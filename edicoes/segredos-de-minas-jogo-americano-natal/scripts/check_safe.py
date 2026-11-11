"""Check every overlay frame against an Instagram Reels safe area (1080x1920).

- sides: 60 px margin (phones with rounded corners / slight zoom)
- top: y >= 290 (4:5 feed crop removes the top 285 px; profile/back UI)
- bottom: y <= 1440 (username, caption and audio row sit below ~1450; 4:5 crop ends at 1635)
- right icon column (like/comment/share): x <= 950 wherever y > 1000
usage: check_safe.py OVERLAY_DIR [step]
"""
import sys, glob, os
import numpy as np, cv2
d = sys.argv[1]; step = int(sys.argv[2]) if len(sys.argv) > 2 else 2
files = sorted(glob.glob(os.path.join(d, "frame_*.png")))
bad = []
for i in range(0, len(files), step):
    a = cv2.imread(files[i], cv2.IMREAD_UNCHANGED)[..., 3]
    m = a > 40
    if not m.any():
        continue
    ys, xs = np.where(m)
    probs = []
    if xs.min() < 60: probs.append(f"left x={xs.min()}")
    if xs.max() > 1020: probs.append(f"right x={xs.max()}")
    if ys.min() < 290: probs.append(f"top y={ys.min()}")
    if ys.max() > 1440: probs.append(f"bottom y={ys.max()}")
    low = m[1000:, 951:]
    if low.any(): probs.append("icon column")
    if probs:
        bad.append((i / 30.0, ", ".join(probs)))
print(f"frames checked: {len(range(0, len(files), step))}, violations: {len(bad)}")
last = None
for t, p in bad:
    if last is None or p != last[1] or t - last[0] > 0.2:
        print(f"  t={t:6.2f}s  {p}")
    last = (t, p)
