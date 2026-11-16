"""Incremental template tracking of the sticker (OpenCV matchTemplate), forward and backward
from a reference frame. Output JSON {frame: [cx, cy]} in 1080x1920 coords."""
import json, subprocess, sys
import cv2, numpy as np
src, out, F0, F1, ref, cx, cy = sys.argv[1], sys.argv[2], *map(int, sys.argv[3:8])
W, H, S = 1080, 1920, 2
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-vf", f"select='between(n\\,{F0}\\,{F1-1})',scale={W//S}:{H//S}",
                      "-vsync", "0", "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True, check=True).stdout
fr = np.frombuffer(raw, np.uint8).reshape(-1, H // S, W // S)
r = 90
pos = {ref: (cx / S, cy / S)}
def step(a, b):
    x, y = pos[a]
    t = fr[a - F0][int(y) - r:int(y) + r, int(x) - r:int(x) + r]
    sx0, sy0 = int(x) - r - 40, int(y) - r - 40
    win = fr[b - F0][max(sy0, 0):int(y) + r + 40, max(sx0, 0):int(x) + r + 40]
    res = cv2.matchTemplate(win, t, cv2.TM_CCOEFF_NORMED)
    _, mv, _, ml = cv2.minMaxLoc(res)
    pos[b] = (max(sx0, 0) + ml[0] + r, max(sy0, 0) + ml[1] + r)
    return mv
for k in range(ref, F1 - 1):
    step(k, k + 1)
for k in range(ref, F0, -1):
    step(k, k - 1)
res = {k: [pos[k][0] * S, pos[k][1] * S] for k in sorted(pos)}
json.dump(res, open(out, "w"), indent=0)
for k in list(res)[::8]:
    print(k, [round(v) for v in res[k]])
