"""'Small rugs appear one by one' - natural version (real footage, stop-motion cuts).

For each settled state (no hand / rug in the air) a short LIVE window of the original
clip is used. Every frame is stabilised onto the last state's view (SIFT + MAGSAC
homography frame -> state key frame, state key frames chained to the last one), cropped
to the area all windows share and rendered straight from 4K. Windows are joined with
plain cuts: the deck stays put and a new rug is simply there - no fades, no scaling.
Usage: python3 menores_live.py OUT.mp4 [SRC]
"""
import subprocess
import sys

import cv2
import numpy as np

OUT = sys.argv[1]
SRC = sys.argv[2] if len(sys.argv) > 2 else "raw2/IMG_6871.MOV"
W, H, FPS = 1080, 1920, 30
CLIP_FPS = 30000 / 1001
# (key time, window start, window length) in seconds of the source clip
WINDOWS = [(0.45, 0.15, 0.55), (2.85, 2.60, 0.42), (7.85, 7.60, 0.42), (13.05, 12.80, 0.42),
           (17.55, 17.30, 0.42), (22.55, 22.30, 0.42), (25.90, 25.50, 0.90)]


def read_range(k0, n, full):
    if full:
        vf = "scale=in_color_matrix=bt709:in_range=pc:flags=accurate_rnd+full_chroma_int"
        w, h = 2160, 3840
    else:
        vf = f"scale={W}:{H}:in_color_matrix=bt709:in_range=pc:flags=area+accurate_rnd+full_chroma_int"
        w, h = W, H
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", SRC, "-vf",
                          f"select='between(n\\,{k0}\\,{k0 + n - 1})'," + vf, "-vsync", "0",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3)


sift = cv2.SIFT_create(5000)
flann = cv2.FlannBasedMatcher(dict(algorithm=1, trees=5), dict(checks=64))


def homog(g1, g2):
    k1, d1 = sift.detectAndCompute(g1, None)
    k2, d2 = sift.detectAndCompute(g2, None)
    mm = flann.knnMatch(d1, d2, k=2)
    good = [m for m, n2 in mm if m.distance < 0.72 * n2.distance]
    p1 = np.float32([k1[m.queryIdx].pt for m in good])
    p2 = np.float32([k2[m.trainIdx].pt for m in good])
    Hm, inl = cv2.findHomography(p1, p2, cv2.USAC_MAGSAC, 2.5, maxIters=20000, confidence=0.9999)
    return Hm, int(inl.sum())


def main():
    keys, wins = [], []
    for kt, ws, wl in WINDOWS:
        k0 = int(round(ws * CLIP_FPS))
        n = int(round(wl * FPS))
        small = read_range(k0, n, False)
        kk = min(max(int(round(kt * CLIP_FPS)) - k0, 0), len(small) - 1)
        wins.append((k0, n, small))
        keys.append(kk)
    gk = [cv2.cvtColor(w[2][kk], cv2.COLOR_RGB2GRAY) for w, kk in zip(wins, keys)]
    # key i -> key i+1, chained to the last key
    toref = [None] * len(wins)
    toref[-1] = np.eye(3)
    for i in range(len(wins) - 2, -1, -1):
        Hm, ni = homog(gk[i], gk[i + 1])
        print("key", i, "->", i + 1, "inliers", ni, file=sys.stderr)
        toref[i] = toref[i + 1] @ Hm
    # every frame -> its key
    per = []
    for i, (k0, n, small) in enumerate(wins):
        hs = []
        for j in range(len(small)):
            if j == keys[i]:
                hs.append(np.eye(3))
            else:
                Hm, _ = homog(cv2.cvtColor(small[j], cv2.COLOR_RGB2GRAY), gk[i])
                hs.append(Hm)
        per.append([toref[i] @ h for h in hs])
    # common window (9:16) over all frames
    inter = np.ones((H, W), bool)
    for hs in per:
        for Hm in hs:
            inter &= cv2.warpPerspective(np.full((H, W), 255, np.uint8), Hm, (W, H), flags=cv2.INTER_NEAREST) > 0
    inter = cv2.erode(inter.astype(np.uint8), np.ones((15, 15), np.uint8)).astype(bool)
    ii = np.pad(inter.astype(np.int64), ((1, 0), (1, 0))).cumsum(0).cumsum(1)
    best = None
    for w in range(W, 400, -6):
        h = int(round(w * 16 / 9))
        cands = [(x0, y0) for y0 in range(0, H - h + 1, 6) for x0 in range(0, W - w + 1, 6)]
        cands.sort(key=lambda p: (p[0] + w / 2 - W / 2) ** 2 + (p[1] + h / 2 - H / 2) ** 2)
        for x0, y0 in cands:
            if ii[y0 + h, x0 + w] - ii[y0, x0 + w] - ii[y0 + h, x0] + ii[y0, x0] == w * h:
                best = (x0, y0, w, h)
                break
        if best:
            break
    x0, y0, ww, hh = best
    sc = W / ww
    C = np.array([[sc, 0, -x0 * sc], [0, sc, -y0 * sc], [0, 0, 1]])
    D = np.diag([0.5, 0.5, 1.0])
    print("window", best, "zoom", round(sc, 3), file=sys.stderr)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-vf",
                            "scale=out_color_matrix=bt709:out_range=tv:flags=accurate_rnd+full_chroma_int",
                            "-c:v", "libx264", "-preset", "medium", "-crf", "12", "-pix_fmt", "yuv420p",
                            "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
                            "-color_range", "tv", "-an", OUT], stdin=subprocess.PIPE)
    total = 0
    for i, (k0, n, small) in enumerate(wins):
        full = read_range(k0, n, True)
        for j in range(len(full)):
            M = C @ per[i][j] @ D
            out = cv2.warpPerspective(full[j], M, (W, H), flags=cv2.INTER_AREA, borderMode=cv2.BORDER_REFLECT)
            enc.stdin.write(out.tobytes())
            total += 1
    enc.stdin.close()
    enc.wait()
    print("frames", total, "seconds", round(total / FPS, 2))


if __name__ == "__main__":
    main()
