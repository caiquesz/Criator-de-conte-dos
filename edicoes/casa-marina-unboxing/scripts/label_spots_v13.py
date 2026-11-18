"""Legibility of each v13 name over every shot it spans, at the centre and at higher spots.
Prints, per shot, p75 luminance and stitch texture inside the text box (white text reads
well when both are low). Usage: python3 -I scripts/label_spots_v13.py MASTER.mp4
"""
import os
import subprocess
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render_v13 as V  # noqa: E402

master = sys.argv[1]
order = list(V.SEGS)


def grab(k):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{k / 30:.3f}", "-i", master, "-frames:v", "1", "-vf",
                          "scale=in_range=tv:in_color_matrix=bt709", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(1920, 1080, 3).astype(np.float32) / 255


for first, last, (d0, d1), caps, script, y in V.PLAN:
    lb = V.V11.SerifLabel(0, 1, caps, script, "center", 540, None)
    h, w = lb.bottom - lb.y, lb.width
    segs = order[order.index(first): order.index(last) + 1]
    tops = [round(960 - h / 2)] + list(range(820, 200, -60))
    print(caps, "h", h, "w", w, "plan y", y)
    for sg in segs:
        s = V.SEGS[sg]
        frs = [grab(s["out0"] + int(s["frames"] * f)) for f in (0.2, 0.5, 0.8)]
        row = []
        for top in tops:
            x0, x1, y0, y1 = 540 - w // 2 - 10, 540 + w // 2 + 10, top - 10, top + h + 10
            L = [f[y0:y1, x0:x1] @ np.array([0.2126, 0.7152, 0.0722], np.float32) for f in frs]
            p75 = max(np.percentile(l, 75) for l in L)
            tex = max(np.abs(cv2.Laplacian(cv2.GaussianBlur(l, (0, 0), 1.2), cv2.CV_32F)).mean() for l in L) * 100
            row.append(f"{top}:{p75:.2f}/{tex:.1f}")
        print(f"   {sg:22s}", " ".join(row))
