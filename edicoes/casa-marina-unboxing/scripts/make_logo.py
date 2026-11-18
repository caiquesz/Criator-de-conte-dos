"""Extract the Casa Marina logo (letters + symbol) from the paper background.

Produces a transparent PNG with:
  - dark-brown strokes keyed by luminance against the local paper colour
  - the small yellow accent keyed by blue-channel deficit
Small specks from the paper texture are removed by connected-component size.
"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

src, out = sys.argv[1], sys.argv[2]
im = np.asarray(Image.open(src).convert("RGB")).astype(np.float32)
H, W, _ = im.shape
lum = im @ np.array([0.299, 0.587, 0.114], np.float32)

# Local paper estimate: replace ink-ish pixels by global bg, then blur heavily.
bg_rgb = np.array([240.0, 232.4, 221.2], np.float32)
ink_guess = (lum < 200) | (im[..., 2] < 185)
paper = im.copy()
paper[ink_guess] = bg_rgb
paper = np.stack([ndi.gaussian_filter(paper[..., c], 25) for c in range(3)], -1)
paper_lum = paper @ np.array([0.299, 0.587, 0.114], np.float32)

ink_rgb = np.array([39.0, 19.0, 13.0], np.float32)
ink_lum = float(ink_rgb @ np.array([0.299, 0.587, 0.114], np.float32))

# Dark strokes alpha (paper texture noise ~ +-8 lum => small dead-zone)
a_dark = (paper_lum - lum - 10.0) / (paper_lum - ink_lum - 10.0)
a_dark = np.clip(a_dark, 0, 1)

# Yellow accent: blue drops much more than red does.
blue_def = (paper[..., 2] - im[..., 2]) - 0.6 * np.clip(paper[..., 0] - im[..., 0], 0, None)
a_yel = np.clip((blue_def - 14.0) / (85.0 - 14.0), 0, 1)
a_yel[a_dark > 0.35] = 0  # dark strokes win

# Remove specks: keep components with enough area (computed on a binarised mask)
def clean(alpha, min_area):
    lab, n = ndi.label(alpha > 0.25)
    if n == 0:
        return alpha
    areas = ndi.sum(np.ones_like(alpha), lab, index=np.arange(1, n + 1))
    keep = np.zeros(n + 1, bool)
    keep[1:] = areas >= min_area
    mask = keep[lab]
    mask = ndi.binary_dilation(mask, iterations=3)  # keep soft AA edges
    return alpha * mask

a_dark = clean(a_dark, 400)
a_yel = clean(a_yel, 150)
# Restrict yellow to the area right of the knot symbol (where the accent lives)
ys, xs = np.nonzero(a_dark > 0.5)
alpha = np.maximum(a_dark, a_yel)

# Colours: flat brand brown for strokes, flat accent yellow for the dot
brown = np.array([52, 30, 24], np.float32)
yellow = np.array([238, 214, 128], np.float32)
w_y = np.where(alpha > 0, a_yel / np.maximum(alpha, 1e-6), 0)[..., None]
rgb = brown * (1 - w_y) + yellow * w_y

rgba = np.dstack([rgb, alpha * 255]).astype(np.uint8)
img = Image.fromarray(rgba, "RGBA")
bbox = img.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()
pad = 20
bbox = (max(bbox[0] - pad, 0), max(bbox[1] - pad, 0), min(bbox[2] + pad, W), min(bbox[3] + pad, H))
img = img.crop(bbox)
img.save(out)
print("saved", out, img.size, "bbox", bbox)
