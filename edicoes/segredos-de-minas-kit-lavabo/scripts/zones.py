"""Score candidate caption zones (readability of white text) over output-time windows."""
import sys, json, numpy as np
from PIL import Image
V = sys.argv[1] if len(sys.argv) > 1 else "."
N = 362
L = np.stack([np.asarray(Image.open(f"{V}/work/lum/f_{k+1:04d}.png").convert("L"), dtype=np.float32) for k in range(N)])  # 10 fps, 108x192
ZONES = {  # x0,y0,x1,y1 in 1080x1920
    "TL": (80, 280, 620, 520), "TR": (460, 280, 1000, 520), "TC": (200, 280, 880, 520),
    "ML": (80, 620, 620, 900), "MR": (460, 620, 1000, 900), "C": (180, 820, 900, 1100),
    "LL": (80, 1100, 620, 1360), "LR": (420, 1100, 940, 1360), "LC": (200, 1100, 880, 1360),
    "BL": (80, 1360, 620, 1580), "BR": (420, 1360, 940, 1580), "BC": (200, 1360, 880, 1580),
}
def score(t0, t1, z):
    x0, y0, x1, y1 = [v // 10 for v in ZONES[z]]
    a = int(t0 * 10); b = max(a + 1, int(t1 * 10))
    r = L[a:b, y0:y1, x0:x1]
    bright = (r > 170).mean(); mean = r.mean(); tex = r.std()
    return bright, mean, tex
if __name__ == "__main__":
    t0, t1 = float(sys.argv[2]), float(sys.argv[3])
    for z in ZONES:
        b, m, s = score(t0, t1, z)
        print(f"{z:3s} bright={b:.2f} mean={m:5.1f} std={s:4.1f}")
