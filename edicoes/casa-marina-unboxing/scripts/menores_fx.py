"""'Rugs appear one by one' sequence from IMG_6871 (rugs thrown onto the deck, handheld).

1. settled states S0..S6 (no hands / rug in flight) are picked from the clip;
2. camera motion is removed: each state is registered to the next one (SIFT + MAGSAC
   homography on the deck and the rugs already on it) and chained to the last state's view;
3. the output window is the largest 9:16 rectangle every state covers, rendered straight
   from the 4K frames (no border fill, no quality loss);
4. a canvas starts with S0; for each new state the mask of what changed (new rug + its
   shadow) 'pops in' (opacity 0->1, scale 0.9->1 around its centroid, ease-out);
5. a slow push-in (1.00 -> 1.05) over the whole sequence keeps it alive.
Output: 1080x1920 @ 30 fps, BT.709 limited range.
Usage: python3 menores_fx.py OUT.mp4 [SRC]
"""
import subprocess
import sys

import cv2
import numpy as np
from scipy import ndimage as ndi

OUT = sys.argv[1]
SRC = sys.argv[2] if len(sys.argv) > 2 else "raw2/IMG_6871.MOV"
W, H, FPS = 1080, 1920, 30
CLIP_FPS = 30000 / 1001
STATES = [0.30, 3.00, 8.00, 13.00, 17.50, 22.50, 26.00]
HOLD0, POP, HOLD, HOLD_END = 0.50, 0.24, 0.42, 0.70
PUSH = 0.03
S4K = 2


def read_frame(k, full=False):
    if full:
        vf = "scale=in_color_matrix=bt709:in_range=pc:flags=accurate_rnd+full_chroma_int"
        w, h = 2160, 3840
    else:
        vf = f"scale={W}:{H}:in_color_matrix=bt709:in_range=pc:flags=lanczos+accurate_rnd+full_chroma_int"
        w, h = W, H
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", SRC, "-vf", f"select=eq(n\\,{k})," + vf, "-vsync", "0",
                          "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(h, w, 3)


def register(states_small):
    gray = [cv2.cvtColor(f, cv2.COLOR_RGB2GRAY) for f in states_small]
    sift = cv2.SIFT_create(6000)
    feats = [sift.detectAndCompute(g, None) for g in gray]
    fl = cv2.FlannBasedMatcher(dict(algorithm=1, trees=5), dict(checks=64))
    pair = []
    for i in range(len(gray) - 1):
        (k1, d1), (k2, d2) = feats[i], feats[i + 1]
        mm = fl.knnMatch(d1, d2, k=2)
        good = [m for m, n2 in mm if m.distance < 0.72 * n2.distance]
        p1 = np.float32([k1[m.queryIdx].pt for m in good])
        p2 = np.float32([k2[m.trainIdx].pt for m in good])
        Hm, inl = cv2.findHomography(p1, p2, cv2.USAC_MAGSAC, 2.5, maxIters=20000, confidence=0.9999)
        print("pair", i, "matches", len(good), "inliers", int(inl.sum()), file=sys.stderr)
        pair.append(Hm)
    toref = [None] * len(gray)
    toref[-1] = np.eye(3)
    for i in range(len(gray) - 2, -1, -1):
        toref[i] = toref[i + 1] @ pair[i]
    return toref


def window(toref):
    inter = np.ones((H, W), bool)
    for Hm in toref:
        inter &= cv2.warpPerspective(np.full((H, W), 255, np.uint8), Hm, (W, H), flags=cv2.INTER_NEAREST) > 0
    inter = cv2.erode(inter.astype(np.uint8), np.ones((15, 15), np.uint8)).astype(bool)
    ii = np.pad(inter.astype(np.int64), ((1, 0), (1, 0))).cumsum(0).cumsum(1)

    def full(x0, y0, w, h):
        if x0 < 0 or y0 < 0 or x0 + w > W or y0 + h > H:
            return False
        return ii[y0 + h, x0 + w] - ii[y0, x0 + w] - ii[y0 + h, x0] + ii[y0, x0] == w * h

    cx, cy = W // 2, H // 2
    for w in range(W, 400, -6):
        h = int(round(w * 16 / 9))
        cands = [(x0, y0) for y0 in range(0, H - h + 1, 6) for x0 in range(0, W - w + 1, 6)]
        cands.sort(key=lambda p: (p[0] + w / 2 - cx) ** 2 + (p[1] + h / 2 - cy) ** 2)
        for x0, y0 in cands:
            if full(x0, y0, w, h):
                return x0, y0, w, h
    raise RuntimeError("no window")


def ease_out(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def main():
    ks = [int(round(t * CLIP_FPS)) for t in STATES]
    toref = register([read_frame(k) for k in ks])
    x0, y0, ww, hh = window(toref)
    sc = W / ww
    C = np.array([[sc, 0, -x0 * sc], [0, sc, -y0 * sc], [0, 0, 1]])
    print("window", (x0, y0, ww, hh), "zoom", round(sc, 3), file=sys.stderr)
    D = np.diag([1.0 / S4K, 1.0 / S4K, 1.0])
    aligned = []
    for i, k in enumerate(ks):
        f4 = read_frame(k, full=True)
        a = cv2.warpPerspective(f4, C @ toref[i] @ D, (W, H), flags=cv2.INTER_AREA, borderMode=cv2.BORDER_REFLECT)
        aligned.append(a.astype(np.float32))
    canvas = aligned[0].copy()
    steps = []
    for i in range(1, len(aligned)):
        a = aligned[i].copy()
        d0 = np.abs(cv2.GaussianBlur(a, (0, 0), 3) - cv2.GaussianBlur(canvas, (0, 0), 3)).mean(-1)
        calm = d0 < 18
        gain = np.median(canvas[calm], 0) / np.maximum(np.median(a[calm], 0), 1)
        a = np.clip(a * gain, 0, 255)
        d = np.abs(cv2.GaussianBlur(a, (0, 0), 4) - cv2.GaussianBlur(canvas, (0, 0), 4)).mean(-1)
        m = (d > 22).astype(np.uint8)
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((9, 9), np.uint8))
        m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((31, 31), np.uint8)).astype(bool)
        lab, n = ndi.label(m)
        if n:
            areas = ndi.sum(m, lab, index=np.arange(1, n + 1))
            keep = np.zeros(n + 1, bool)
            keep[1:] = areas >= max(6000, 0.25 * areas.max())
            m = keep[lab]
        m = ndi.binary_fill_holes(m)
        m = cv2.dilate(m.astype(np.uint8), np.ones((11, 11), np.uint8)).astype(bool)
        mf = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 4)
        ys, xs = np.nonzero(m)
        c = (float(xs.mean()), float(ys.mean())) if len(xs) else (W / 2, H / 2)
        steps.append((mf, a, c))
        canvas = canvas * (1 - mf[..., None]) + a * mf[..., None]
        print("state", i, "mask area", int(m.sum()), "gain", gain.round(3), file=sys.stderr)
        cv2.imwrite(f"out/v8/rev/fx_mask_{i}.jpg", (m * 255).astype(np.uint8)[::4, ::4])

    total = int(round((HOLD0 + len(steps) * (POP + HOLD) - HOLD + HOLD_END) * FPS))
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-vf",
                            "scale=out_color_matrix=bt709:out_range=tv:flags=accurate_rnd+full_chroma_int",
                            "-c:v", "libx264", "-preset", "medium", "-crf", "12", "-pix_fmt", "yuv420p",
                            "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
                            "-color_range", "tv", "-an", OUT], stdin=subprocess.PIPE)
    starts = [HOLD0 + j * (POP + HOLD) for j in range(len(steps))]
    cur = aligned[0].copy()
    done = 0
    for fi in range(total):
        t = fi / FPS
        while done < len(steps) and t >= starts[done] + POP:
            mf, a, c = steps[done]
            cur = cur * (1 - mf[..., None]) + a * mf[..., None]
            done += 1
        img = cur
        if done < len(steps) and t >= starts[done]:
            mf, a, c = steps[done]
            k = ease_out((t - starts[done]) / POP)
            s = 0.90 + 0.10 * k
            M = np.float32([[s, 0, c[0] * (1 - s)], [0, s, c[1] * (1 - s)]])
            mw = cv2.warpAffine(mf, M, (W, H), flags=cv2.INTER_LINEAR) * k
            aw = cv2.warpAffine(a, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
            img = cur * (1 - mw[..., None]) + aw * mw[..., None]
        z = 1.0 + PUSH * (fi / max(total - 1, 1))
        Mz = np.float32([[z, 0, W / 2 * (1 - z)], [0, z, H / 2 * (1 - z)]])
        out = cv2.warpAffine(np.clip(img, 0, 255).astype(np.uint8), Mz, (W, H), flags=cv2.INTER_LINEAR,
                             borderMode=cv2.BORDER_REFLECT)
        enc.stdin.write(out.tobytes())
    enc.stdin.close()
    enc.wait()
    print("frames", total, "seconds", round(total / FPS, 2))


if __name__ == "__main__":
    main()
