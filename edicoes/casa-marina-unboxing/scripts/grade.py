"""Casa Marina colour grade: soft, warm, minimal (keeps product colours honest).

- tone curve: slightly lifted blacks, gentle mid contrast, rolled-off highlights
  (the deck footage is shot in hard sun);
- warmth: a touch of red/yellow in mids and highlights, a little less blue;
- saturation: -6 % overall, greens/cyans pulled a bit more than reds (deck/railing grass),
  so the crochet colours stay true.
grade(rgb_uint8) -> rgb_uint8
"""
import cv2
import numpy as np

_x = np.arange(256, dtype=np.float32) / 255.0


def _curve():
    # monotone cubic through control points (input, output) in 0..1
    pts = np.array([[0.00, 0.035], [0.12, 0.13], [0.30, 0.305], [0.50, 0.505],
                    [0.70, 0.695], [0.85, 0.82], [0.95, 0.905], [1.00, 0.935]])
    return np.interp(_x, pts[:, 0], pts[:, 1])


_TONE = _curve()
_hi = np.clip((_x - 0.35) / 0.65, 0, 1)            # mids/highlights weight
LUT_R = np.clip(_TONE * (1 + 0.025 * _hi) + 0.004, 0, 1)
LUT_G = np.clip(_TONE * (1 + 0.008 * _hi), 0, 1)
LUT_B = np.clip(_TONE * (1 - 0.030 * _hi) - 0.002, 0, 1)
LUT = np.stack([LUT_R, LUT_G, LUT_B], -1)          # 256 x 3
LUT8 = np.clip(LUT * 255 + 0.5, 0, 255).astype(np.uint8)


def grade(rgb):
    out = np.empty_like(rgb)
    for c in range(3):
        out[..., c] = cv2.LUT(rgb[..., c], LUT8[:, c])
    hsv = cv2.cvtColor(out, cv2.COLOR_RGB2HSV_FULL).astype(np.float32)
    h = hsv[..., 0] * (360.0 / 256.0)
    # hue-dependent desaturation: greens/cyans (70..200 deg) -12 %, everything else -5 %
    w = np.clip(1 - np.abs(h - 135) / 65, 0, 1)
    hsv[..., 1] *= 0.95 - 0.07 * w
    out = cv2.cvtColor(np.clip(hsv, 0, 255).astype(np.uint8), cv2.COLOR_HSV2RGB_FULL)
    return out


if __name__ == "__main__":
    import sys
    from PIL import Image
    ims = []
    for p in sys.argv[2:]:
        a = np.asarray(Image.open(p).convert("RGB"))
        b = grade(a)
        ims.append(np.vstack([a, b]))
    Image.fromarray(np.hstack(ims)).save(sys.argv[1], quality=90)
