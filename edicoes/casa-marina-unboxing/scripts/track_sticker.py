"""Track the Casa Marina sticker through take 2 with patch cross-correlation.

Outputs JSON {frame_index: [cx, cy]} in source pixel coords (1080x1920).
"""
import json
import subprocess
import sys

import numpy as np

src, out = sys.argv[1], sys.argv[2]
W, H = 1080, 1920
F0, F1 = 60, 113  # take 2 frames [2.000s, 3.766s)
ref_frame = 75     # 2.5s, sticker centre measured by eye
ref_c = np.array([687.0, 1003.0])
S = 2  # work at half resolution

cmd = ["ffmpeg", "-v", "error", "-i", src, "-vf",
       f"select='between(n\\,{F0}\\,{F1 - 1})',scale={W // S}:{H // S}",
       "-vsync", "0", "-f", "rawvideo", "-pix_fmt", "gray", "-"]
raw = subprocess.run(cmd, capture_output=True, check=True).stdout
n = len(raw) // ((W // S) * (H // S))
frames = np.frombuffer(raw, np.uint8).reshape(n, H // S, W // S).astype(np.float32)
print("frames", n)

def patch(img, c, r):
    x, y = int(round(c[0])), int(round(c[1]))
    return img[y - r:y + r, x - r:x + r]

r = 110  # half-size of template at half res (sticker ~200px wide at half res)
tmpl = patch(frames[ref_frame - F0], ref_c / S, r)
tmpl = (tmpl - tmpl.mean()) / (tmpl.std() + 1e-6)

res = {}
search = 60
for i in range(n):
    img = frames[i]
    best = None
    cx0, cy0 = ref_c / S
    # coarse exhaustive search over a window, step 2 then refine step 1
    for step, rad, centre in [(3, search, (cx0, cy0)), (1, 4, None)]:
        if centre is None:
            centre = best[1]
        cands = []
        for dy in range(-rad, rad + 1, step):
            for dx in range(-rad, rad + 1, step):
                c = (centre[0] + dx, centre[1] + dy)
                p = patch(img, c, r)
                if p.shape != tmpl.shape:
                    continue
                p = (p - p.mean()) / (p.std() + 1e-6)
                score = float((p * tmpl).mean())
                cands.append((score, c))
        best = max(cands, key=lambda s: s[0])
    res[F0 + i] = [best[1][0] * S, best[1][1] * S, round(best[0], 3)]
    print(F0 + i, res[F0 + i])

json.dump(res, open(out, "w"), indent=1)
