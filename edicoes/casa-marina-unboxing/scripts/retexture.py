"""Planar re-texturing of the tile floor with a real CC0 laminate texture (Poly Haven
"Laminate Floor 02"), for the shots where the AI edit failed or looked wrong.

Per shot:
  1. floor mask per frame from the ORIGINAL footage (white/grey tile: low saturation,
     cool, smooth; grout lines and the tile seen through crochet holes included);
  2. camera tracking: corners on the floor+rugs (all planar) tracked with LK optical flow,
     frame-to-frame homographies (RANSAC) chained to a reference frame;
  3. plank layout in the reference frame aligned with the tile grout direction, plank
     width = tile pitch / PLANKS_PER_TILE;
  4. texture colour-matched (Lab mean/std) to the AI wood used in the other shots, shaded
     by the original low-frequency floor luminance (keeps soft shadows of rugs/people);
  5. composited with a feathered mask; everything that is not floor keeps original pixels.

Library use: python3 retexture.py analyse FRAME   (prints grout angle / pitch, writes debug)
             python3 retexture.py run plan.json IN.mp4 OUT.mp4
"""
import json
import math
import subprocess
import sys

import cv2
import numpy as np
from scipy import ndimage as ndi

W, H = 1080, 1920
DEC = "scale=in_color_matrix=bt709:in_range=tv:flags=accurate_rnd+full_chroma_int"
ENC_VF = "scale=out_color_matrix=bt709:out_range=tv:flags=accurate_rnd+full_chroma_int"
TEX = None


def read_frames(path, k0, k1):
    p = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vf",
                        f"select='between(n\\,{k0}\\,{k1 - 1})',{DEC}", "-vsync", "0",
                        "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True)
    return np.frombuffer(p.stdout, np.uint8).reshape(-1, H, W, 3)


# ----------------------------------------------------------------------------- floor mask
def _fill_holes(m, max_area, lum, max_lum):
    holes = ndi.binary_fill_holes(m) & ~m
    n, lab, stats, _ = cv2.connectedComponentsWithStats(holes.astype(np.uint8), 8)
    if n <= 1:
        return m
    ml = ndi.mean(lum, lab, index=np.arange(1, n))
    keep = np.zeros(n, bool)
    keep[1:] = (stats[1:, cv2.CC_STAT_AREA] <= max_area) & (np.asarray(ml) < max_lum)
    return m | keep[lab]


def tile_mask(rgb, warm_max=13.0, roi=None, loose=False, loose_lum=95, loose_s9=18, rim_px=5):
    """Half-resolution boolean tile mask (960x540) from an original RGB frame.
    roi: optional half-res boolean region where the floor can be; loose: inside roi accept
    smooth low-saturation pixels without needing to touch a bright seed (shadowed tile)."""
    s = cv2.resize(rgb, (W // 2, H // 2), interpolation=cv2.INTER_AREA).astype(np.float32)
    mx, mn = s.max(-1), s.min(-1)
    sat = (mx - mn) / np.maximum(mx, 1)
    lum = s.mean(-1)
    warm = s[..., 0] - s[..., 2]

    def sd(k):
        m = cv2.blur(lum, (k, k))
        return np.sqrt(np.maximum(cv2.blur(lum * lum, (k, k)) - m * m, 0))

    s3, s5, s9 = sd(3), sd(5), sd(9)
    low = (sat < 0.24) & (lum < 246) & ((warm < warm_max) | (sat < 0.05))
    seed = low & (lum > 170) & (s3 < 14) & (s9 < 12)
    smooth = low & (lum > 80) & (s5 < 20) & (s9 < 18)
    if roi is not None:
        seed &= roi
        smooth &= roi
    m = ndi.binary_propagation(seed, mask=seed | smooth)
    if loose:
        lsm = (sat < 0.24) & ((warm < warm_max) | (sat < 0.05)) & (lum < 246) & (lum > loose_lum) & (s5 < 20) & (s9 < loose_s9)
        if roi is not None:
            lsm &= roi
        m |= lsm
    # over-exposed glare on the tile, attached to the floor
    blown = (lum >= 246) & (sat < 0.12)
    if roi is not None:
        blown &= roi
    n, lab, stats, _ = cv2.connectedComponentsWithStats(blown.astype(np.uint8), 8)
    if n > 1:
        touch = ndi.maximum(cv2.dilate(m.astype(np.uint8), np.ones((5, 5), np.uint8)), lab, index=np.arange(1, n))
        keep = np.zeros(n, bool)
        keep[1:] = np.asarray(touch) > 0
        m |= keep[lab]
    m = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8),
                         borderType=cv2.BORDER_REPLICATE).astype(bool)
    m = _fill_holes(m, 900, lum, 175)                  # grout crossings / thin grout left inside
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m.astype(np.uint8), 8)
    keep = np.zeros(n, bool)
    keep[1:] = stats[1:, cv2.CC_STAT_AREA] >= 150
    m = keep[lab]
    # holes of the crochet: bright blobs much brighter than the surrounding yarn
    bright = (sat < 0.40) & (lum > 140) & ~m
    if roi is not None:
        bright &= roi
    n, lab, stats, _ = cv2.connectedComponentsWithStats(bright.astype(np.uint8), 8)
    if n > 1:
        surround = cv2.blur(lum, (41, 41))
        contrast = np.asarray(ndi.mean(lum - surround, lab, index=np.arange(1, n)))
        area = stats[1:, cv2.CC_STAT_AREA]
        ok = ((area <= 260) & (contrast > 38)) | ((area <= 900) & (contrast > 65))
        keep = np.zeros(n, bool)
        keep[1:] = ok
        m = m | cv2.dilate(keep[lab].astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
    # rim: the light fringe between rug edge and tile
    rim = cv2.dilate(m.astype(np.uint8), np.ones((rim_px, rim_px), np.uint8)).astype(bool) & ~m \
        & (lum > 95) & (sat < 0.35) & ((warm < warm_max + 2) | (sat < 0.06))
    m = m | rim
    return m, lum


# ----------------------------------------------------------------------------- grid analysis
def grout_angle_pitch(rgb, mask):
    """Dominant grout direction (deg, image coords) and tile pitch (px, full res)."""
    g = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    bh = cv2.morphologyEx(g, cv2.MORPH_BLACKHAT, cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15)))
    big = cv2.resize(mask.astype(np.uint8), (W, H), interpolation=cv2.INTER_NEAREST)
    big = cv2.erode(big, np.ones((9, 9), np.uint8)) | 0
    bh = np.where(cv2.dilate(big, np.ones((31, 31), np.uint8)) > 0, bh, 0)
    edges = (bh > 18).astype(np.uint8) * 255
    lines = cv2.HoughLinesP(edges, 1, np.pi / 360, threshold=120, minLineLength=160, maxLineGap=12)
    if lines is None:
        return None, None, edges
    ang, wts = [], []
    for x1, y1, x2, y2 in lines.reshape(-1, 4):
        a = math.degrees(math.atan2(y2 - y1, x2 - x1)) % 180
        ang.append(a)
        wts.append(math.hypot(x2 - x1, y2 - y1))
    ang, wts = np.array(ang), np.array(wts)
    # fold to [0,90) to merge the two perpendicular families, take weighted circular mode
    f = ang % 90
    hist, b = np.histogram(f, bins=90, range=(0, 90), weights=wts)
    hist = ndi.gaussian_filter1d(hist, 1.5, mode="wrap")
    theta = (np.argmax(hist) + 0.5)
    # pitch: project grout pixels onto the normal of theta and autocorrelate
    ys, xs = np.nonzero(edges)
    if len(xs) < 200:
        return theta, None, edges
    t = math.radians(theta)
    d = -xs * math.sin(t) + ys * math.cos(t)
    h1, _ = np.histogram(d, bins=np.arange(d.min(), d.max() + 1, 1.0))
    h1 = h1 - h1.mean()
    ac = np.correlate(h1, h1, "full")[len(h1) - 1:]
    lo = 120
    pitch = lo + int(np.argmax(ac[lo:900])) if len(ac) > 900 else None
    return theta, pitch, edges


# ----------------------------------------------------------------------------- texture
def load_texture(path, target_lab):
    t = cv2.cvtColor(cv2.imread(path), cv2.COLOR_BGR2RGB)
    lab = cv2.cvtColor(t, cv2.COLOR_RGB2LAB).astype(np.float32)
    mu, sd = lab.reshape(-1, 3).mean(0), lab.reshape(-1, 3).std(0)
    tmu, tsd = np.array(target_lab[0], np.float32), np.array(target_lab[1], np.float32)
    lab = (lab - mu) / np.maximum(sd, 1e-3) * tsd + tmu
    return cv2.cvtColor(np.clip(lab, 0, 255).astype(np.uint8), cv2.COLOR_LAB2RGB)


def texture_canvas(tex, theta_deg, plank_px, tex_plank_px, cw, ch):
    """Canvas (ch x cw) of laminate with planks running along theta, plank width plank_px."""
    s = plank_px / tex_plank_px
    reps = int(math.ceil(max(cw, ch) * 1.6 / (tex.shape[0] * s))) + 1
    big = np.tile(tex, (reps, reps, 1))
    c = (big.shape[1] / 2, big.shape[0] / 2)
    M = cv2.getRotationMatrix2D(c, -theta_deg, s)          # texture planks are horizontal
    M[0, 2] += cw / 2 - c[0]
    M[1, 2] += ch / 2 - c[1]
    return cv2.warpAffine(big, M, (cw, ch), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_WRAP)


# ----------------------------------------------------------------------------- tracking
def track_homographies(frames, masks, ref, mode="all"):
    """H[k] maps reference-frame pixels -> frame k pixels."""
    n = len(frames)
    gray = [cv2.cvtColor(cv2.resize(f, (W // 2, H // 2), interpolation=cv2.INTER_AREA), cv2.COLOR_RGB2GRAY)
            for f in frames]
    step = {}
    for a, b in [(k, k + 1) for k in range(n - 1)]:
        fm = None
        if mode == "floor":
            fm = cv2.dilate(masks[a].astype(np.uint8) * 255, np.ones((7, 7), np.uint8))
        pts = cv2.goodFeaturesToTrack(gray[a], 1500, 0.005, 6, mask=fm)
        nxt, st, _ = cv2.calcOpticalFlowPyrLK(gray[a], gray[b], pts, None, winSize=(21, 21), maxLevel=4)
        back, st2, _ = cv2.calcOpticalFlowPyrLK(gray[b], gray[a], nxt, None, winSize=(21, 21), maxLevel=4)
        ok = (st[:, 0] == 1) & (st2[:, 0] == 1) & (np.linalg.norm(back - pts, axis=2)[:, 0] < 0.8)
        p0, p1 = pts[ok, 0] * 2, nxt[ok, 0] * 2
        Hab = None
        if len(p0) >= 25:
            Hab, inl = cv2.findHomography(p0, p1, cv2.RANSAC, 3.0)
            if Hab is not None and inl.sum() < 15:
                Hab = None
        step[(a, b)] = Hab if Hab is not None else np.eye(3)
    Hs = [None] * n
    Hs[ref] = np.eye(3)
    for k in range(ref + 1, n):
        Hs[k] = step[(k - 1, k)] @ Hs[k - 1]
    for k in range(ref - 1, -1, -1):
        Hs[k] = np.linalg.inv(step[(k, k + 1)]) @ Hs[k + 1]
    return Hs


# ----------------------------------------------------------------------------- shading
def shading(lum_half, mask_half, ref_lum):
    m = mask_half.astype(np.float32)
    num = cv2.GaussianBlur(lum_half * m, (0, 0), 18)
    den = cv2.GaussianBlur(m, (0, 0), 18)
    low = num / np.maximum(den, 1e-3)
    sh = np.clip(low / ref_lum, 0.45, 1.22)
    return sh


def grid_homography(spec):
    """Homography tile-grid (u,v) -> reference-frame pixels."""
    if "quad" in spec:                               # 4 corners of one tile, (0,0),(1,0),(1,1),(0,1)
        src = np.array([[0, 0], [1, 0], [1, 1], [0, 1]], np.float64)
        return cv2.getPerspectiveTransform(src.astype(np.float32), np.array(spec["quad"], np.float32)).astype(np.float64)
    t = math.radians(spec["theta"])
    p = spec["pitch"]
    cx, cy = spec.get("origin", (W / 2, H / 2))
    return np.array([[p * math.cos(t), -p * math.sin(t), cx],
                     [p * math.sin(t), p * math.cos(t), cy],
                     [0, 0, 1]], np.float64)


def process_shot(orig, wood, spec, tex, tex_plank_px):
    n = len(orig)
    ref = spec.get("ref", n // 2)
    masks, lums = [], []
    roi_list = [None] * n
    if "roi" in spec:
        rough = [tile_mask(o, spec.get("warm_max", 13.0))[0] for o in orig]
        Hs0 = track_homographies(orig, rough, ref, spec.get("track", "all"))
        roi_ref = np.zeros((H, W), np.uint8)
        for poly in spec["roi"]:
            cv2.fillPoly(roi_ref, [np.array(poly, np.int32)], 1)
        for k in range(n):
            r = cv2.warpPerspective(roi_ref, Hs0[k], (W, H), flags=cv2.INTER_NEAREST)
            roi_list[k] = cv2.resize(r, (W // 2, H // 2), interpolation=cv2.INTER_NEAREST).astype(bool)
    for k, (o, w) in enumerate(zip(orig, wood)):
        m, lum = tile_mask(o, spec.get("warm_max", 13.0), roi_list[k], spec.get("loose", False),
                           spec.get("loose_lum", 95), spec.get("loose_s9", 18), spec.get("rim_px", 5))
        if w is not None:   # also cover what the AI pass already replaced
            d = np.abs(cv2.resize(w, (W // 2, H // 2), interpolation=cv2.INTER_AREA).astype(np.int16)
                       - cv2.resize(o, (W // 2, H // 2), interpolation=cv2.INTER_AREA).astype(np.int16)).mean(-1)
            m = m | cv2.morphologyEx((d > 25).astype(np.uint8), cv2.MORPH_OPEN, np.ones((5, 5), np.uint8)).astype(bool)
        masks.append(m)
        lums.append(lum)
    Hs = track_homographies(orig, masks, ref, spec.get("track", "all"))
    Hg = grid_homography(spec)
    tex_per_tile = tex_plank_px * spec.get("planks_per_tile", 3.0)
    S_inv = np.diag([1.0 / tex_per_tile, 1.0 / tex_per_tile, 1.0])
    rot = spec.get("plank_axis", 0)                  # 0: planks along grid u, 1: along v
    if rot:
        S_inv = np.array([[0, 1.0 / tex_per_tile, 0], [1.0 / tex_per_tile, 0, 0], [0, 0, 1]])
    ref_lum = np.median(np.concatenate([l[m] for l, m in zip(lums, masks) if m.any()]))
    out = []
    for k in range(n):
        M = Hs[k] @ Hg @ S_inv                       # texture px -> frame k px
        t = cv2.warpPerspective(tex, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
        sh = cv2.resize(shading(lums[k], masks[k], ref_lum), (W, H), interpolation=cv2.INTER_LINEAR)
        t = np.clip(t.astype(np.float32) * sh[..., None], 0, 255)
        mf = cv2.GaussianBlur(masks[k].astype(np.float32), (0, 0), 1.2)
        mf = cv2.resize(mf, (W, H), interpolation=cv2.INTER_LINEAR)[..., None]
        comp = orig[k].astype(np.float32) * (1 - mf) + t * mf
        out.append(np.clip(comp + 0.5, 0, 255).astype(np.uint8))
    return out, dict(ref=int(ref))


def main():
    if sys.argv[1] == "analyse":
        path, k = sys.argv[2], int(sys.argv[3])
        f = read_frames(path, k, k + 1)[0]
        m, _ = tile_mask(f)
        th, pt, edges = grout_angle_pitch(f, m)
        print("theta", th, "pitch", pt, "mask", m.mean())
        dbg = f.copy()
        dbg[cv2.resize(m.astype(np.uint8), (W, H)) > 0] = (dbg[cv2.resize(m.astype(np.uint8), (W, H)) > 0] * 0.5
                                                           + np.array([255, 120, 0]) * 0.5).astype(np.uint8)
        dbg[edges > 0] = (0, 255, 255)
        cv2.imwrite(sys.argv[4], cv2.cvtColor(cv2.resize(dbg, (540, 960)), cv2.COLOR_RGB2BGR))
        return
    if sys.argv[1] == "run":
        plan = json.load(open(sys.argv[2]))
        src, dst = sys.argv[3], sys.argv[4]
        tex = load_texture(plan["texture"], plan["target_lab"])
        shots = {}
        orig_path = plan["orig"]
        for spec in plan["shots"]:
            fo = read_frames(orig_path, spec["k0"], spec["k1"])
            fw = read_frames(src, spec["k0"], spec["k1"]) if spec.get("use_wood_mask", True) else [None] * len(fo)
            res, info = process_shot(fo, fw, spec, tex, plan["tex_plank_px"])
            shots[spec["k0"]] = res
            print("shot", spec["name"], info, file=sys.stderr, flush=True)
        dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", src, "-vf", DEC, "-f", "rawvideo",
                                "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
        enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                                "-s", f"{W}x{H}", "-r", "30", "-i", "-", "-vf", ENC_VF, "-c:v", "libx264",
                                "-preset", "medium", "-crf", "13", "-pix_fmt", "yuv420p", "-colorspace", "bt709",
                                "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv", "-an", dst],
                               stdin=subprocess.PIPE)
        ranges = [(s["k0"], s["k1"]) for s in plan["shots"]]
        fs = W * H * 3
        j = 0
        while True:
            buf = dec.stdout.read(fs)
            if len(buf) < fs:
                break
            for k0, k1 in ranges:
                if k0 <= j < k1:
                    buf = shots[k0][j - k0].tobytes()
            enc.stdin.write(buf)
            j += 1
        enc.stdin.close()
        enc.wait()
        dec.wait()
        print("frames", j)


if __name__ == "__main__":
    main()


# ----------------------------------------------------------------------------- grid homography
def fit_grid_homography(rgb, mask, debug_path=None):
    """Fit a homography from tile-grid coordinates (u,v in tiles) to image pixels using the
    grout lines of one frame. Returns (Hg, err_px, n_points) or (None, ...)."""
    g = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    bh = cv2.morphologyEx(g, cv2.MORPH_BLACKHAT, cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15)))
    big = cv2.resize(mask.astype(np.uint8), (W, H), interpolation=cv2.INTER_NEAREST)
    bh = np.where(cv2.dilate(big, np.ones((31, 31), np.uint8)) > 0, bh, 0)
    edges = (bh > 18).astype(np.uint8) * 255
    segs = cv2.HoughLinesP(edges, 1, np.pi / 720, threshold=90, minLineLength=110, maxLineGap=14)
    if segs is None or len(segs) < 6:
        return None, None, 0
    segs = segs.reshape(-1, 4).astype(np.float64)
    ang = np.degrees(np.arctan2(segs[:, 3] - segs[:, 1], segs[:, 2] - segs[:, 0])) % 180
    ln = np.hypot(segs[:, 2] - segs[:, 0], segs[:, 3] - segs[:, 1])
    hist, _ = np.histogram(ang % 90, bins=180, range=(0, 90), weights=ln)
    hist = ndi.gaussian_filter1d(hist, 2, mode="wrap")
    a0 = (np.argmax(hist) + 0.5) / 2.0
    fams = []
    for base in (a0, a0 + 90):
        d = np.abs(((ang - base + 90) % 180) - 90)
        fams.append(np.nonzero(d < 18)[0])
    ys, xs = np.nonzero(edges)
    epts = np.stack([xs, ys], 1).astype(np.float64)
    fam_lines = []
    for fi, idx in enumerate(fams):
        base = math.radians(a0 + 90 * fi)
        nrm = np.array([-math.sin(base), math.cos(base)])
        mids = np.stack([(segs[idx, 0] + segs[idx, 2]) / 2, (segs[idx, 1] + segs[idx, 3]) / 2], 1)
        rho = mids @ nrm
        order = np.argsort(rho)
        clusters = []
        for i in order:
            if clusters and abs(rho[i] - np.mean([rho[j] for j in clusters[-1]])) < 28:
                clusters[-1].append(i)
            else:
                clusters.append([i])
        lines = []
        for cl in clusters:
            r = np.average(rho[cl], weights=ln[idx][cl])
            # refine: total least squares on edge pixels close to this line
            dist = np.abs(epts @ nrm - r)
            sel = epts[dist < 12]
            if len(sel) < 60:
                continue
            c = sel.mean(0)
            u, s, vt = np.linalg.svd(sel - c, full_matrices=False)
            dirv = vt[0]
            n2 = np.array([-dirv[1], dirv[0]])
            lines.append((n2, float(n2 @ c), float(r), len(sel)))
        fam_lines.append(sorted(lines, key=lambda t: t[2]))
    if len(fam_lines[0]) < 2 or len(fam_lines[1]) < 2:
        return None, None, 0
    # integer indices from spacing (robust to missing lines)
    def index(lines):
        r = np.array([l[2] for l in lines])
        dif = np.diff(r)
        sp = np.median(dif[dif > 60]) if np.any(dif > 60) else None
        if sp is None:
            return None
        return np.round((r - r[0]) / sp).astype(int)
    ia, ib = index(fam_lines[0]), index(fam_lines[1])
    if ia is None or ib is None:
        return None, None, 0
    src, dst = [], []
    for (na, ca, _, _), i in zip(fam_lines[0], ia):
        for (nb, cb, _, _), j in zip(fam_lines[1], ib):
            A = np.array([na, nb])
            if abs(np.linalg.det(A)) < 0.3:
                continue
            p = np.linalg.solve(A, np.array([ca, cb]))
            if -200 < p[0] < W + 200 and -200 < p[1] < H + 200:
                src.append((j, i))
                dst.append(p)
    if len(src) < 4:
        return None, None, len(src)
    src, dst = np.array(src, np.float64), np.array(dst, np.float64)
    Hg, inl = cv2.findHomography(src, dst, cv2.RANSAC, 25.0)
    if Hg is None:
        return None, None, len(src)
    proj = cv2.perspectiveTransform(src.reshape(-1, 1, 2), Hg).reshape(-1, 2)
    err = float(np.median(np.linalg.norm(proj - dst, axis=1)))
    if debug_path:
        dbg = rgb.copy()
        for u in range(-6, 12):
            pts = cv2.perspectiveTransform(np.array([[[u, v] for v in np.linspace(-6, 12, 60)]], np.float64), Hg)
            cv2.polylines(dbg, [pts.astype(np.int32)], False, (255, 0, 0), 3)
        for v in range(-6, 12):
            pts = cv2.perspectiveTransform(np.array([[[u, v] for u in np.linspace(-6, 12, 60)]], np.float64), Hg)
            cv2.polylines(dbg, [pts.astype(np.int32)], False, (0, 90, 255), 3)
        for p in dst:
            cv2.circle(dbg, tuple(int(x) for x in p), 9, (255, 255, 0), -1)
        cv2.imwrite(debug_path, cv2.cvtColor(cv2.resize(dbg, (540, 960)), cv2.COLOR_RGB2BGR))
    return Hg, err, int(inl.sum())


if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "grid":
    pass
