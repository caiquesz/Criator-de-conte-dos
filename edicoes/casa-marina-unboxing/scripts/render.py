"""Casa Marina unboxing reel - edit renderer.

Pipeline (frame-exact, 1080x1920 @ 30fps):
  1. Logo intro (0-2s): transparent logo appears and dissolves away.
  2. Take 2 (2.000-3.766s): smooth push-in that tracks the Casa Marina sticker.
  3. Product labels: thin leader line + product name (Noto Serif / Montserrat).
No colour grading: frames are decoded/encoded with the same BT.709 matrix.

Usage:
  python3 render.py --preview 0.3,2.9,34.0     -> PNG stills in out/preview/
  python3 render.py --render out/video_noaudio.mp4
"""
import argparse
import json
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "raw", "video.MOV")
LOGO = os.path.join(ROOT, "logo", "logo_casa_marina.png")
TRACK = os.path.join(ROOT, "t2", "track.json")
FONT_SERIF = os.path.join(ROOT, "fonts", "NotoSerif.ttf")
FONT_SANS = os.path.join(ROOT, "fonts", "Montserrat.ttf")

W, H, FPS = 1080, 1920, 30
N_FRAMES = 2156

DARK = (58, 36, 28)        # Casa Marina brown (from the logo)
LIGHT = (255, 252, 247)    # warm white

# --------------------------------------------------------------------------
# easing helpers
def clamp01(x):
    return 0.0 if x < 0 else 1.0 if x > 1 else x

def ease_out_cubic(x):
    x = clamp01(x)
    return 1 - (1 - x) ** 3

def ease_in_cubic(x):
    x = clamp01(x)
    return x ** 3

def ease_in_out_cubic(x):
    x = clamp01(x)
    return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2

def ease_in_out_sine(x):
    x = clamp01(x)
    return -(math.cos(math.pi * x) - 1) / 2

# --------------------------------------------------------------------------
# 1. Logo intro
LOGO_T_IN, LOGO_HOLD_END, LOGO_T_OUT = 0.35, 1.40, 1.95
LOGO_W = 640
LOGO_CENTER = (540, 900)

_logo_cache = {}

def logo_img():
    if "img" not in _logo_cache:
        lg = Image.open(LOGO).convert("RGBA")
        h = round(lg.height * LOGO_W / lg.width)
        _logo_cache["img"] = lg.resize((LOGO_W, h), Image.LANCZOS)
    return _logo_cache["img"]

def apply_logo(frame, t):
    if t >= LOGO_T_OUT:
        return frame
    if t < LOGO_T_IN:
        k = ease_out_cubic(t / LOGO_T_IN)
        alpha, scale, blur = k, 0.97 + 0.03 * k, 0.0
    elif t < LOGO_HOLD_END:
        k = (t - LOGO_T_IN) / (LOGO_HOLD_END - LOGO_T_IN)
        alpha, scale, blur = 1.0, 1.0 + 0.012 * k, 0.0
    else:
        k = ease_in_cubic((t - LOGO_HOLD_END) / (LOGO_T_OUT - LOGO_HOLD_END))
        k2 = ease_in_out_sine((t - LOGO_HOLD_END) / (LOGO_T_OUT - LOGO_HOLD_END))
        alpha, scale, blur = 1.0 - k2, 1.012 + 0.05 * k, 7.0 * k
    lg = logo_img()
    sw, sh = round(lg.width * scale), round(lg.height * scale)
    lg = lg.resize((sw, sh), Image.LANCZOS)
    if blur > 0.05:
        pad = 24
        canvas = Image.new("RGBA", (sw + 2 * pad, sh + 2 * pad), (0, 0, 0, 0))
        canvas.paste(lg, (pad, pad))
        lg = canvas.filter(ImageFilter.GaussianBlur(blur))
        sw, sh = lg.size
    if alpha < 1:
        a = lg.getchannel("A").point(lambda v: round(v * alpha))
        lg.putalpha(a)
    x = round(LOGO_CENTER[0] - sw / 2)
    y = round(LOGO_CENTER[1] - sh / 2)
    frame.alpha_composite(lg, (x, y))
    return frame

# --------------------------------------------------------------------------
# 2. Sticker push-in (take 2)
ZOOM_F0, ZOOM_F1 = 60, 113          # frames [2.000, 3.767)
ZOOM_T0 = ZOOM_F0 / FPS
ZOOM_RAMP = 0.95                    # seconds of eased push
ZOOM_MAX, ZOOM_END = 1.70, 1.78     # then a gentle drift until the cut

_track = None

def sticker_center(fi):
    global _track
    if _track is None:
        d = json.load(open(TRACK))
        idx = sorted(int(k) for k in d)
        xs = np.array([d[str(i)][0] for i in idx], float)
        ys = np.array([d[str(i)][1] for i in idx], float)
        k = 9
        ker = np.ones(k) / k
        xs = np.convolve(np.pad(xs, k // 2, mode="edge"), ker, "valid")
        ys = np.convolve(np.pad(ys, k // 2, mode="edge"), ker, "valid")
        _track = {i: (x, y) for i, x, y in zip(idx, xs, ys)}
    return _track[min(max(fi, ZOOM_F0), ZOOM_F1 - 1)]

def apply_zoom(frame, fi):
    if not (ZOOM_F0 <= fi < ZOOM_F1):
        return frame
    t = fi / FPS - ZOOM_T0
    e = ease_in_out_cubic(t / ZOOM_RAMP)
    z = 1 + (ZOOM_MAX - 1) * e
    if t > ZOOM_RAMP:
        z = ZOOM_MAX + (ZOOM_END - ZOOM_MAX) * clamp01((t - ZOOM_RAMP) / ((ZOOM_F1 - ZOOM_F0) / FPS - ZOOM_RAMP))
    sx, sy = sticker_center(fi)
    cx = 540 + (sx - 540) * e
    cy = 960 + (sy - 960) * e
    hw, hh = W / (2 * z), H / (2 * z)
    cx = min(max(cx, hw), W - hw)
    cy = min(max(cy, hh), H - hh)
    # output (u,v) -> source (cx + (u-540)/z, cy + (v-960)/z)
    a, b, c = 1 / z, 0, cx - 540 / z
    d, e2, f = 0, 1 / z, cy - 960 / z
    return frame.transform((W, H), Image.AFFINE, (a, b, c, d, e2, f), resample=Image.BICUBIC)

# --------------------------------------------------------------------------
# 3. Product labels
def font(path, size, weight, width=None):
    f = ImageFont.truetype(path, size)
    axes = [weight] if width is None else [weight, width]
    f.set_variation_by_axes(axes)
    return f

F_L1 = font(FONT_SERIF, 54, 400, 100)
F_L2 = font(FONT_SANS, 31, 400)
L2_TRACK = 1.4
LINE_GAP = 14          # px between line-1 bottom and line-2 top

def text_layer(text, fnt, color, tracking=0.0):
    """Render a single line of text into a tight RGBA layer.

    Returns (img, ascent_offset): img top corresponds to the font ascender.
    """
    asc, desc = fnt.getmetrics()
    if tracking:
        widths = [fnt.getlength(text[:i]) for i in range(len(text) + 1)]
        total = widths[-1] + tracking * (len(text) - 1)
    else:
        total = fnt.getlength(text)
    pad = 4
    img = Image.new("L", (math.ceil(total) + 2 * pad, asc + desc + 2 * pad), 0)
    d = ImageDraw.Draw(img)
    if tracking:
        for i, ch in enumerate(text):
            d.text((pad + widths[i] + tracking * i, pad), ch, font=fnt, fill=255)
    else:
        d.text((pad, pad), text, font=fnt, fill=255)
    rgba = Image.new("RGBA", img.size, color + (0,))
    rgba.putalpha(img)
    return rgba, pad

class Label:
    def __init__(self, t0, t1, l1, l2, tx, ty, color, style, anchors=None,
                 line_len=70, fast=False):
        self.t0, self.t1 = t0, t1
        self.color = DARK if color == "dark" else LIGHT
        self.shadow = color == "light"
        self.style = style            # "drop" (line from product up to text) or "side"
        self.anchors = anchors or []  # list of (t, (x, y)) keyframes for product point
        self.line_len = line_len
        self.tx, self.ty = tx, ty
        self.fast = fast
        a1, p1 = text_layer(l1, F_L1, self.color)
        a2, p2 = text_layer(l2, F_L2, self.color, L2_TRACK)
        asc1, desc1 = F_L1.getmetrics()
        # tight vertical metrics using real ink bbox of line 1
        bb1 = a1.getchannel("A").getbbox()
        bb2 = a2.getchannel("A").getbbox()
        self.l1 = (a1, tx - p1, ty - bb1[1])                       # place ink top at ty
        l1_bottom = ty + (bb1[3] - bb1[1])
        self.l2 = (a2, tx - p2 + 1, l1_bottom + LINE_GAP - bb2[1])
        self.block_bottom = l1_bottom + LINE_GAP + (bb2[3] - bb2[1])
        self.block_right = max(tx + a1.width, tx + a2.width)
        self.l1_mid = ty + (bb1[3] - bb1[1]) / 2
        if self.shadow:
            self.sh1 = self._shadow(a1)
            self.sh2 = self._shadow(a2)

    @staticmethod
    def _shadow(layer, blur=9, alpha=0.42):
        pad = 30
        a = layer.getchannel("A")
        canvas = Image.new("L", (layer.width + 2 * pad, layer.height + 2 * pad), 0)
        canvas.paste(a, (pad, pad))
        canvas = canvas.filter(ImageFilter.GaussianBlur(blur)).point(lambda v: round(v * alpha))
        sh = Image.new("RGBA", canvas.size, (25, 14, 8, 0))
        sh.putalpha(canvas)
        return sh, pad

    def product_point(self, t):
        if not self.anchors:
            return None
        if t <= self.anchors[0][0]:
            return self.anchors[0][1]
        for (ta, pa), (tb, pb) in zip(self.anchors, self.anchors[1:]):
            if ta <= t <= tb:
                if tb - ta < 1e-6:
                    return pb
                k = (t - ta) / (tb - ta)
                return (pa[0] + (pb[0] - pa[0]) * k, pa[1] + (pb[1] - pa[1]) * k)
        return self.anchors[-1][1]

    def line_points(self, t):
        if self.style == "drop":
            q = (self.tx + 3, self.block_bottom + 24)
            p = self.product_point(t)
            return p, q                       # draws from product (p) towards text (q)
        y = self.l1_mid
        q = (self.tx - 22, y)
        p = (self.tx - 22 - self.line_len, y)
        return p, q

    def timings(self):
        if self.fast:
            return dict(line=(0.0, 0.28), t1=(0.14, 0.44), t2=(0.20, 0.50), out=0.26)
        return dict(line=(0.0, 0.42), t1=(0.22, 0.62), t2=(0.30, 0.70), out=0.32)

    @property
    def sfx_time(self):
        tm = self.timings()
        return self.t0 + tm["t1"][0] + 0.02

    def draw(self, frame, t):
        if not (self.t0 <= t < self.t1):
            return frame
        tm = self.timings()
        lt = t - self.t0
        out_k = 1.0 - ease_in_out_sine((t - (self.t1 - tm["out"])) / tm["out"])
        # leader line
        lk = ease_out_cubic((lt - tm["line"][0]) / (tm["line"][1] - tm["line"][0]))
        p, q = self.line_points(t)
        if lk > 0:
            e = (p[0] + (q[0] - p[0]) * lk, p[1] + (q[1] - p[1]) * lk)
            draw_line(frame, p, e, self.color, out_k, self.shadow)
        # text lines
        for (layer, x, y), (a0, a1), sh in ((self.l1, tm["t1"], getattr(self, "sh1", None)),
                                             (self.l2, tm["t2"], getattr(self, "sh2", None))):
            k = ease_out_cubic((lt - a0) / (a1 - a0))
            if k <= 0:
                continue
            alpha = k * out_k
            dy = round(12 * (1 - k))
            if sh is not None:
                s_img, pad = sh
                frame.alpha_composite(fade(s_img, alpha), (x - pad, y - pad + dy + 2))
            frame.alpha_composite(fade(layer, alpha), (x, y + dy))
        return frame

def fade(img, alpha):
    if alpha >= 0.999:
        return img
    out = img.copy()
    out.putalpha(img.getchannel("A").point(lambda v: round(v * alpha)))
    return out

LINE_W = 2.6
SS = 4

def draw_line(frame, p, q, color, alpha, shadow):
    if alpha <= 0:
        return
    m = 30
    x0, y0 = math.floor(min(p[0], q[0])) - m, math.floor(min(p[1], q[1])) - m
    x1, y1 = math.ceil(max(p[0], q[0])) + m, math.ceil(max(p[1], q[1])) + m
    w, h = x1 - x0, y1 - y0
    mask = Image.new("L", (w * SS, h * SS), 0)
    d = ImageDraw.Draw(mask)
    a = ((p[0] - x0) * SS, (p[1] - y0) * SS)
    b = ((q[0] - x0) * SS, (q[1] - y0) * SS)
    lw = LINE_W * SS
    d.line([a, b], fill=255, width=round(lw))
    r = lw / 2
    for c in (a, b):
        d.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], fill=255)
    mask = mask.resize((w, h), Image.LANCZOS)
    if shadow:
        sm = mask.filter(ImageFilter.GaussianBlur(7)).point(lambda v: round(v * 0.45 * alpha))
        sl = Image.new("RGBA", (w, h), (25, 14, 8, 0))
        sl.putalpha(sm)
        frame.alpha_composite(sl, (x0, y0 + 2))
    layer = Image.new("RGBA", (w, h), color + (0,))
    layer.putalpha(mask.point(lambda v: round(v * alpha)))
    frame.alpha_composite(layer, (x0, y0))

LABELS = [
    # Sousplat on the table (two takes: plate placed / glass placed), text on the white wall
    Label(32.45, 36.12, "Sousplat", "em fio de malha", 90, 292, "dark", "drop",
          anchors=[(32.45, (210, 800))]),
    # Brown round rug on the tiles, text on the tiles (camera tilts, anchor follows)
    Label(40.80, 42.56, "Tapete redondo", "de crochê", 90, 268, "dark", "drop",
          anchors=[(40.80, (340, 770)), (42.56, (340, 650))]),
    # Hand-loomed runners - text sits on the wide burgundy stripe
    Label(43.05, 45.22, "Jogo de passadeira", "feito em tear manual", 250, 948, "light", "side",
          line_len=72),
    # Geometric rug, wide take: text on the tiles above it
    Label(47.82, 49.26, "Tapete geométrico em crochê", "e em fio de malha", 90, 276, "dark", "drop",
          anchors=[(47.82, (240, 650)), (48.50, (330, 650)), (49.26, (500, 640))], fast=True),
    # Rectangular rugs (navy / brown / navy): white text on the rug
    Label(50.00, 55.26, "Tapete retangular de crochê", "em fio de malha", 250, 930, "light", "side",
          line_len=72),
    # Smaller round rugs falling on the floor
    Label(55.56, 57.36, "Tapete redondo menor", "de crochê", 90, 612, "dark", "drop",
          anchors=[(55.56, (270, 990))]),
]

# extra SFX cues (time, kind)
EXTRA_SFX = [(0.06, "pop"), (2.05, "click")]

def sfx_cues():
    cues = list(EXTRA_SFX)
    for lb in LABELS:
        cues.append((round(lb.sfx_time, 3), "pop"))
    return sorted(cues)

# --------------------------------------------------------------------------
def process(rgb, fi):
    t = fi / FPS
    img = Image.fromarray(rgb, "RGB")
    img = apply_zoom(img, fi)
    active = t < LOGO_T_OUT or any(lb.t0 <= t < lb.t1 for lb in LABELS)
    if not active:
        return img
    img = img.convert("RGBA")
    img = apply_logo(img, t)
    for lb in LABELS:
        img = lb.draw(img, t)
    return img.convert("RGB")

DEC_VF = "scale=in_color_matrix=bt709:in_range=tv:flags=accurate_rnd+full_chroma_int"

def decode_frame(fi):
    t = fi / FPS
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{max(t - 1, 0):.4f}", "-i", SRC,
           "-ss", f"{t - max(t - 1, 0):.4f}", "-frames:v", "1", "-vf", DEC_VF,
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(raw[: W * H * 3], np.uint8).reshape(H, W, 3)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview")
    ap.add_argument("--render")
    ap.add_argument("--cues", action="store_true")
    args = ap.parse_args()
    if args.cues:
        print(json.dumps(sfx_cues()))
        return
    if args.preview:
        od = os.path.join(ROOT, "out", "preview")
        os.makedirs(od, exist_ok=True)
        for ts in args.preview.split(","):
            fi = round(float(ts) * FPS)
            img = process(decode_frame(fi), fi)
            p = os.path.join(od, f"p_{float(ts):06.2f}.png")
            img.save(p)
            print(p)
        return
    if args.render:
        dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", SRC, "-vf", DEC_VF, "-vsync", "passthrough",
                                "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
        enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                                "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                                "-vf", "scale=out_color_matrix=bt709:out_range=tv:flags=accurate_rnd+full_chroma_int",
                                "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-profile:v", "high",
                                "-pix_fmt", "yuv420p", "-colorspace", "bt709", "-color_primaries", "bt709",
                                "-color_trc", "bt709", "-color_range", "tv", "-movflags", "+faststart",
                                args.render], stdin=subprocess.PIPE)
        fs = W * H * 3
        fi = 0
        while True:
            buf = dec.stdout.read(fs)
            if len(buf) < fs:
                break
            rgb = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
            t = fi / FPS
            if (ZOOM_F0 <= fi < ZOOM_F1) or t < LOGO_T_OUT or any(lb.t0 <= t < lb.t1 for lb in LABELS):
                out = process(rgb, fi).tobytes()
            else:
                out = buf
            enc.stdin.write(out)
            fi += 1
            if fi % 300 == 0:
                print("frame", fi, file=sys.stderr, flush=True)
        enc.stdin.close()
        enc.wait()
        dec.wait()
        print("frames written", fi)

if __name__ == "__main__":
    main()
