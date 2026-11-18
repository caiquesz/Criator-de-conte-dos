"""Put the AI wood-laminate floor under the ORIGINAL 1080p footage.

The FLUX 3 Video Edit output is 704x1248 @ 24 fps. Instead of using it as is (soft
products), we keep every original pixel except the floor:
  mask = original pixel looks like the white tile floor (low saturation, not dark)
       AND the AI pixel looks like wood (warm hue, some saturation)
       AND the two differ clearly
cleaned with a small morphological close/open and feathered, then
  out = original * (1 - mask) + ai_upscaled * mask
AI frames are aligned in time exactly (AI frame k = time k/24 s) and blended linearly.

Usage: python3 floor_composite.py clean_master.mp4 plan.json out.mp4
plan.json: list of {"ai": path, "map": [[ai_chunk_start_frame30, master_start, n_frames], ...]}
           (chunk frame numbers are in the 30 fps chunk that was sent to the AI)
"""
import json
import subprocess
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

W, H, FPS, AI_FPS = 1080, 1920, 30, 24
DEC = "scale=in_color_matrix=bt709:in_range=tv:flags=accurate_rnd+full_chroma_int"
ENC_VF = "scale=out_color_matrix=bt709:out_range=tv:flags=accurate_rnd+full_chroma_int"

def read_all(path, w=None, h=None):
    vf = DEC if w is None else f"scale={w}:{h}:flags=lanczos,{DEC}"
    p = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vf", vf, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                       capture_output=True, check=True)
    ww, hh = (W, H) if w is None else (w, h)
    return np.frombuffer(p.stdout, np.uint8).reshape(-1, hh, ww, 3)

def hsv_parts(img):
    f = img.astype(np.float32)
    mx = f.max(-1)
    mn = f.min(-1)
    sat = (mx - mn) / np.maximum(mx, 1)
    lum = f.mean(-1)
    r, g, b = f[..., 0], f[..., 1], f[..., 2]
    # hue in degrees (only need a coarse warm-hue test)
    hue = np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) % 360
    return sat, lum, hue

PAD = 12

def _pad(a):
    return np.pad(a, PAD, mode="edge")

def _crop(a):
    return a[PAD:-PAD, PAD:-PAD]

def closing(m, k):
    return _crop(ndi.binary_closing(_pad(m), structure=np.ones((k, k))))

def opening(m, k):
    return _crop(ndi.binary_opening(_pad(m), structure=np.ones((k, k))))

def fill_small_holes(m, max_area, lum=None, max_lum=None):
    holes = ndi.binary_fill_holes(m) & ~m
    lab, n = ndi.label(holes)
    if not n:
        return m
    idx = np.arange(1, n + 1)
    areas = ndi.sum(holes, lab, index=idx)
    keep = np.zeros(n + 1, bool)
    ok = areas <= max_area
    if lum is not None:
        ok &= ndi.mean(lum, lab, index=idx) < max_lum      # grout is darker than skin/yarn highlights
    keep[1:] = ok
    return m | keep[lab]

def floor_mask(orig_s, ai_s):
    """Both inputs at half resolution (540x960).
    Returns (m, h): m = floor mask (use the AI pixel), h = crochet-hole mask (use a wood colour)."""
    so, lo, _ = hsv_parts(orig_s)
    sa, la, ha = hsv_parts(ai_s)
    # local texture of the ORIGINAL: tiles are smooth, crochet yarn is not
    m3 = ndi.uniform_filter(lo, 3)
    std3 = np.sqrt(np.maximum(ndi.uniform_filter(lo * lo, 3) - m3 * m3, 0))
    m5 = ndi.uniform_filter(lo, 5)
    std5 = np.sqrt(np.maximum(ndi.uniform_filter(lo * lo, 5) - m5 * m5, 0))
    m9 = ndi.uniform_filter(lo, 9)
    std9 = np.sqrt(np.maximum(ndi.uniform_filter(lo * lo, 9) - m9 * m9, 0))
    lowsat = so < 0.22
    notblown = lo < 242                                # over-exposed white yarn/paper is not floor
    warmth = orig_s[..., 0].astype(np.float32) - orig_s[..., 2].astype(np.float32)
    diffval = np.abs(orig_s.astype(np.float32) - ai_s.astype(np.float32)).mean(-1)
    # tile is neutral/cool; cream yarn and paper are warm. Warm-lit tile still counts when the AI
    # changed it a lot (tile -> wood), while the AI keeps cream yarn cream (small difference).
    cool = (warmth < 13) | (so < 0.05) | (diffval > 42)
    seed = lowsat & notblown & cool & (lo > 185) & (std3 < 14) & (std9 < 11)      # bright, smooth tile
    smooth = lowsat & notblown & cool & (lo > 85) & (std5 < 18) & (std9 < 17)     # tile in shadow / veins
    tile = ndi.binary_propagation(seed, mask=seed | smooth)
    tile = closing(tile, 15)                                  # grout lines
    tile = fill_small_holes(tile, 220)                        # grout crossings, small specks
    wood = (ha > 8) & (ha < 55) & (sa > 0.07) & (la > 55)
    diff = np.abs(orig_s.astype(np.float32) - ai_s.astype(np.float32)).mean(-1) > 12
    m = tile & wood & diff
    m = closing(m, 5)
    m = opening(m, 5)
    m = fill_small_holes(m, 220)
    m = fill_small_holes(m, 900, lo, 160)                     # grout crossings left by the AI
    lab, n = ndi.label(m)
    if n:
        areas = ndi.sum(m, lab, index=np.arange(1, n + 1))
        keep = np.zeros(n + 1, bool)
        keep[1:] = areas >= 200
        m = keep[lab]
    # crochet holes: small bright low-saturation blobs (tile seen through the yarn) where the
    # AI frame shows wood-ish colour (the AI keeps cream/white yarn cream, so those are excluded)
    bright = (so < 0.38) & (lo > 175) & ~m
    lab, n = ndi.label(bright)
    h = np.zeros_like(m)
    if n:
        idx = np.arange(1, n + 1)
        areas = ndi.sum(bright, lab, index=idx)
        woodfrac = ndi.mean(wood.astype(np.float32), lab, index=idx)
        surround = ndi.uniform_filter(lo, 17)              # mostly yarn around a hole
        contrast = ndi.mean(lo - surround, lab, index=idx)
        keep = np.zeros(n + 1, bool)
        keep[1:] = (areas <= 250) & ((woodfrac > 0.5) | (contrast > 60)) & (contrast > 38)
        h = keep[lab]
        h = ndi.binary_dilation(h, iterations=1)
    # grow the floor into neighbouring tile-ish pixels the strict test missed (shadowed tile next to
    # the rugs, grout lines, AI seams): low saturation in the original, warm in the AI, not yarn-textured
    grow_ok = (so < 0.34) & (lo > 70) & notblown & (std9 < 20) & (ha > 5) & (ha < 60) & (la > 45) & diff & ((warmth < 14) | (so < 0.05) | (diffval > 42))
    near = _crop(ndi.binary_dilation(_pad(m), iterations=14))
    m = ndi.binary_propagation(m, mask=m | (grow_ok & near))
    m = closing(m, 9)
    m = fill_small_holes(m, 900, lo, 170)
    rim = _crop(ndi.binary_dilation(_pad(m), iterations=3)) & ~m & (so < 0.30) & (lo > 110) & wood
    m = m | rim
    mf = ndi.gaussian_filter(m.astype(np.float32), 1.2, mode="nearest")
    hf = ndi.gaussian_filter(h.astype(np.float32), 0.8)
    hf = np.minimum(hf, 1.0 - mf)
    return mf, hf, m

def clean_ai_floor(ai_full, floor):
    """Remove small dark compact marks (grout crossings the AI kept) inside the floor area."""
    small = ai_full[::4, ::4]
    fl = floor[::4, ::4]
    lum = small.mean(-1)
    med = ndi.median_filter(lum, size=9)
    dark = fl & (lum < med - 28)
    lab, n = ndi.label(dark)
    if not n:
        return ai_full
    idx = np.arange(1, n + 1)
    areas = ndi.sum(dark, lab, index=idx)
    keep = np.zeros(n + 1, bool)
    keep[1:] = areas <= 40
    spots = ndi.binary_dilation(keep[lab], iterations=2)
    if not spots.any():
        return ai_full
    blur = np.stack([ndi.median_filter(small[..., c], size=11) for c in range(3)], -1)
    spots_full = np.asarray(Image.fromarray((spots * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR),
                            np.float32)[..., None] / 255.0
    blur_full = np.asarray(Image.fromarray(np.clip(blur, 0, 255).astype(np.uint8)).resize((W, H), Image.BILINEAR),
                           np.float32)
    return ai_full * (1 - spots_full) + blur_full * spots_full

def main():
    master, plan_path, out = sys.argv[1:4]
    plan = json.load(open(plan_path))
    # master frame -> (ai_index_in_plan, chunk_frame)
    assign = {}
    for pi, item in enumerate(plan):
        for c0, m0, n in item["map"]:
            for k in range(n):
                assign[m0 + k] = (pi, c0 + k)
    ai_cache = {}

    def ai_frames(pi):
        if pi not in ai_cache:
            ai_cache[pi] = read_all(plan[pi]["ai"], W // 2, H // 2)
        return ai_cache[pi]

    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", master, "-vf", DEC, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                           stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-vf", ENC_VF, "-c:v", "libx264", "-preset", "medium", "-crf", "13",
                            "-pix_fmt", "yuv420p", "-colorspace", "bt709", "-color_primaries", "bt709",
                            "-color_trc", "bt709", "-color_range", "tv", "-an", out], stdin=subprocess.PIPE)
    fs = W * H * 3
    j = 0
    replaced = 0
    last_wood = [np.array([196.0, 156.0, 112.0])]
    order = sorted(set(pi for pi, _ in assign.values()))
    # process in master order; AI files are loaded on demand (cache of one)
    while True:
        buf = dec.stdout.read(fs)
        if len(buf) < fs:
            break
        if j in assign:
            pi, cf = assign[j]
            A = ai_frames(pi)
            t = cf / FPS * AI_FPS
            k0 = int(np.floor(t))
            w1 = t - k0
            k0 = min(k0, len(A) - 1)
            k1 = min(k0 + 1, len(A) - 1)
            ai_s = A[k0].astype(np.float32) * (1 - w1) + A[k1].astype(np.float32) * w1
            O = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
            O_s = np.asarray(Image.fromarray(O).resize((W // 2, H // 2), Image.BILINEAR))
            m, hmask, mbin = floor_mask(O_s, ai_s.astype(np.uint8))
            if m.max() > 0.01 or hmask.max() > 0.01:
                if mbin.sum() > 500:
                    wood_rgb = np.median(ai_s[mbin], axis=0)
                    last_wood[0] = wood_rgb
                else:
                    wood_rgb = last_wood[0]
                up = lambda a: np.asarray(Image.fromarray((a * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR),
                                          np.float32)[..., None] / 255.0
                m_full, h_full = up(m), up(hmask)
                ai_full = np.asarray(Image.fromarray(np.clip(ai_s, 0, 255).astype(np.uint8)).resize((W, H), Image.BICUBIC),
                                     np.float32)
                ai_full = clean_ai_floor(ai_full, m_full[..., 0] > 0.5)
                comp = (O.astype(np.float32) * (1 - m_full - h_full) + ai_full * m_full
                        + wood_rgb.astype(np.float32)[None, None, :] * h_full)
                buf = np.clip(comp + 0.5, 0, 255).astype(np.uint8).tobytes()
                replaced += 1
        enc.stdin.write(buf)
        j += 1
        if j % 150 == 0:
            print("frame", j, file=sys.stderr, flush=True)
    enc.stdin.close()
    enc.wait()
    dec.wait()
    print("frames", j, "with floor replaced", replaced)

if __name__ == "__main__":
    main()
