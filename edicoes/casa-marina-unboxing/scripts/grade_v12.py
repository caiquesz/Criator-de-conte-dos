"""Casa Marina v12 - 'professional' colour grade in two stages, like a colourist's node tree.

1. PRIMARY (per clip) - shot matching
   * white balance: the clip's neutral-ish pixels (low saturation, mid luminance: deck, box,
     wall, paper) are pulled 60 % of the way towards one common warm-neutral target, so shots
     in hard sun and shots in the blue shade (rectangular rugs) sit together. Gains are
     clamped to +-6 % so product colours never drift;
   * exposure: the clip's median luminance is nudged 40 % towards a common mid level
     (gamma, clamped), so cuts don't jump in brightness.

2. LOOK (every frame) - soft editorial daylight, after the Westwing unboxing reference
   * local tone mapping (fast guided filter on the luminance, edge aware -> no halos):
     the large-scale contrast of the hard sun is reduced (shadows opened, sun patches
     calmed) while the fine detail - the crochet stitches - is kept, even slightly enhanced;
   * filmic tone curve: lifted, soft blacks; gentle mid contrast; long highlight shoulder;
   * split tone: warm-neutral shadows (no teal), creamy highlights;
   * colour: 'de-vibrance' - low-saturation background colours (wood deck, grass, skin)
     are muted more than the saturated product colours, which stay true; greens/cyans of
     the background a little more muted;
   * a faint highlight bloom (creamy glow on sunlit whites) and a very light vignette.
grade(rgb_uint8, prim) -> rgb_uint8 ; prim = primary_params(sample_frames)
"""
import cv2
import numpy as np

TARGET_WB = np.array([1.035, 1.0, 0.965], np.float32)   # warm-neutral, normalised to mean 1
WB_STRENGTH, WB_CLAMP = 0.60, 0.06
TARGET_MID, EXP_STRENGTH = 0.58, 0.50
LUMA = np.array([0.2126, 0.7152, 0.0722], np.float32)


# ----------------------------------------------------------------------------- primary
def _neutral_rgb(a):
    hsv = cv2.cvtColor((a * 255).astype(np.uint8), cv2.COLOR_RGB2HSV)
    lum = a @ LUMA
    m = (hsv[..., 1] < 60) & (lum > 0.25) & (lum < 0.90)
    v = a[m] if m.sum() > 2000 else a.reshape(-1, 3)
    return v.mean(0)


def primary_params(frames):
    """frames: list of rgb uint8 samples of one clip (already the size it will be graded at)."""
    small = [cv2.resize(f, (270, 480), interpolation=cv2.INTER_AREA).astype(np.float32) / 255 for f in frames]
    nr = np.mean([_neutral_rgb(a) for a in small], 0)
    nr = nr / nr.mean()
    want = TARGET_WB / TARGET_WB.mean()
    gains = 1 + WB_STRENGTH * (want / nr - 1)
    gains = np.clip(gains, 1 - WB_CLAMP, 1 + WB_CLAMP)
    gains = gains / (gains @ LUMA)                       # keep luminance
    # exposure is judged on the neutral surroundings (deck, box, wall), not on the product:
    # a frame filled by a dark-red sousplat is not under-exposed
    mids = []
    for a in small:
        hsv = cv2.cvtColor((a * 255).astype(np.uint8), cv2.COLOR_RGB2HSV)
        lum = a @ LUMA
        m = (hsv[..., 1] < 90) & (lum > 0.08)
        mids.append(lum[m] if m.sum() > 5000 else lum.ravel())
    mid = float(np.median(np.concatenate(mids)))
    mid = min(max(mid, 0.05), 0.95)
    # gamma that would move mid to target, applied partially and clamped
    g_full = np.log(TARGET_MID) / np.log(mid)
    gamma = float(np.clip(1 + EXP_STRENGTH * (g_full - 1), 0.88, 1.12))
    return dict(gains=gains.astype(np.float32), gamma=gamma, mid=mid, neutral=nr)


# ----------------------------------------------------------------------------- look
def _box(x, r):
    return cv2.boxFilter(x, -1, (2 * r + 1, 2 * r + 1), borderType=cv2.BORDER_REFLECT)


def fast_guided_base(L, scale=4, r=10, eps=0.006):
    """Edge-aware smoothing of L (H x W float32) - fast guided filter, guide = L itself."""
    h, w = L.shape
    Ls = cv2.resize(L, (w // scale, h // scale), interpolation=cv2.INTER_AREA)
    mI = _box(Ls, r)
    vI = _box(Ls * Ls, r) - mI * mI
    a = vI / (vI + eps)
    b = mI - a * mI
    ma = cv2.resize(_box(a, r), (w, h), interpolation=cv2.INTER_LINEAR)
    mb = cv2.resize(_box(b, r), (w, h), interpolation=cv2.INTER_LINEAR)
    return ma * L + mb


def _curve_lut():
    # filmic: soft lifted toe, gentle mids, long shoulder (input -> output, 0..1)
    pts = np.array([[0.00, 0.050], [0.06, 0.082], [0.15, 0.160], [0.30, 0.310], [0.50, 0.520],
                    [0.68, 0.700], [0.80, 0.795], [0.90, 0.865], [0.97, 0.910], [1.00, 0.925]])
    x = np.linspace(0, 1, 1024, dtype=np.float32)
    return x, np.interp(x, pts[:, 0], pts[:, 1]).astype(np.float32)


_CX, _CY = _curve_lut()
_VIG = {}


def _vignette(h, w):
    if (h, w) not in _VIG:
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        d = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2) / np.sqrt(2)
        _VIG[(h, w)] = (1 - 0.10 * np.clip((d - 0.45) / 0.55, 0, 1) ** 2).astype(np.float32)[..., None]
    return _VIG[(h, w)]


def look(a):
    """a: float32 RGB 0..1 (after primary). returns float32 0..1."""
    h, w = a.shape[:2]
    L = np.maximum(a @ LUMA, 1e-4)
    # 1) local tone mapping in log2 space: compress the base, keep (a bit more) detail
    lg = np.log2(L)
    base = fast_guided_base(lg.astype(np.float32), r=12, eps=0.05)
    detail = lg - base
    anchor = np.log2(0.42)
    k = np.where(base > anchor, 0.70, 0.80)        # sun patches calmed more than shadows opened
    base2 = anchor + (base - anchor) * k
    L2 = np.exp2(base2 + 1.06 * detail)
    a = a * (L2 / L)[..., None]
    # 2) filmic curve on luminance (ratio, keeps hue), mild chroma compression in highlights
    L = np.maximum(a @ LUMA, 1e-4)
    Lc = np.interp(np.clip(L, 0, 1), _CX, _CY).astype(np.float32)
    a = a * (Lc / L)[..., None]
    a = Lc[..., None] + (a - Lc[..., None]) * (1 - 0.25 * np.clip((Lc - 0.70) / 0.25, 0, 1))[..., None]
    # 3) split tone (additive, luminance-weighted): warm-neutral shadows, creamy highlights
    sh = np.clip(1 - Lc / 0.40, 0, 1)[..., None]
    hi = np.clip((Lc - 0.55) / 0.40, 0, 1)[..., None]
    a = a + sh * np.array([0.012, 0.006, 0.000], np.float32) + hi * np.array([0.016, 0.008, -0.010], np.float32)
    # 4) colour: de-vibrance (mute low-sat background more than saturated products)
    a8 = (np.clip(a, 0, 1) * 255).astype(np.uint8)
    hsv = cv2.cvtColor(a8, cv2.COLOR_RGB2HSV_FULL).astype(np.float32)
    s = hsv[..., 1] / 255.0
    hue = hsv[..., 0] * (360.0 / 256.0)
    green = np.clip(1 - np.abs(hue - 140) / 60, 0, 1)
    fac = 0.97 - 0.17 * (1 - np.clip(s / 0.55, 0, 1)) - 0.08 * green
    Lm = (a @ LUMA)[..., None]
    a = Lm + (a - Lm) * fac[..., None]
    # 5) highlight bloom: soft glow from bright areas only
    bright = np.clip((Lm - 0.72) / 0.25, 0, 1) * a
    glow = cv2.GaussianBlur(cv2.resize(bright, (w // 4, h // 4), interpolation=cv2.INTER_AREA), (0, 0), 9)
    glow = cv2.resize(glow, (w, h), interpolation=cv2.INTER_LINEAR)
    a = 1 - (1 - a) * (1 - 0.12 * glow)              # screen
    # 6) very light vignette
    a = a * _vignette(h, w)
    return np.clip(a, 0, 1)


def grade(rgb, prim):
    a = rgb.astype(np.float32) / 255.0
    a = np.clip(a * prim["gains"], 0, 1)
    if abs(prim["gamma"] - 1) > 1e-3:
        L = np.maximum(a @ LUMA, 1e-4)
        a = a * (np.power(L, prim["gamma"]) / L)[..., None]
    a = look(np.clip(a, 0, 1))
    return (a * 255 + 0.5).astype(np.uint8)
