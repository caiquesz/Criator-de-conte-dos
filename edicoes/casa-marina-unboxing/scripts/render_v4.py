"""Casa Marina reel - v4 (white-text test, white haze intro/outro, softer sticker zoom).

Same "pulled from the box -> shown in the room" structure as v3, plus:
  * intro: footage starts under a blurred white haze, the brown logo appears with it,
    then logo + haze dissolve and the video starts clean (0 - ~1.9 s);
  * outro: the last shot blurs into the white haze again and the logo comes back (fade out);
  * sticker push-in reduced from 1.7x to 1.3x;
  * labels in white, bigger (Cormorant Garamond Italic 84 px + Lexend Mega Light 28 px),
    always placed on a dark part of the product (checked with scripts/bg_luma.py), with a
    soft diffuse shadow only (no outline);
  * sousplat label moved to the red sousplat close-up, leader line on the sousplat itself.
Label timing and anchor keyframes are in OUTPUT time; zoom is keyed to source frames.

Usage:
  python3 render_v4.py --plan
  python3 render_v4.py --preview 0.5,1.5,13.0
  python3 render_v4.py --render out/v4/master.mp4
"""
import argparse
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render as R  # noqa: E402

FPS = R.FPS
W, H = R.W, R.H

EDL = [
    ("intro_logo",        0,   60),
    ("adesivo_zoom",     60,  113),
    ("abre_caixa",      141,  171),
    ("papel_seda",      171,  195),
    ("revela",          222,  258),
    # Sousplat
    ("tira_sousplat_bege",  303,  352),
    ("tira_sousplat_verm",  368,  407),
    ("mesa_prato",          980, 1019),
    ("mesa_copo",          1019, 1055),
    ("mesa_vermelho",      1087, 1153),
    # Tapete redondo
    ("tira_redondo_taupe",  456,  516),
    ("chao_redondo_cinza", 1177, 1213),
    ("chao_redondo_marrom",1221, 1278),
    # Tapete retangular
    ("tira_retang_marinho", 528,  588),
    ("tira_retang_verm",    799,  837),
    ("chao_retang_marinho",1597, 1655),
    ("chao_retang_close",  1505, 1535),
    ("chao_retang_marrom", 1557, 1587),
    # Tapete geométrico
    ("tira_geometrico",     645,  706),
    ("chao_geo_close",     1396, 1433),
    ("chao_geo_aberto",    1433, 1479),
    # Passadeira
    ("tira_passadeira",     858,  919),
    ("chao_passadeira",    1278, 1359),
    # Tapetes redondos menores
    ("tira_redondo_branco", 753,  789),
    ("menores_1",          1661, 1725),
    ("menores_branco",     1800, 1835),
    ("menores_pilha",      1930, 1975),
    # Fecho
    ("oval_verde",         2000, 2036),
    ("textura_final",      2050, 2140),
]

SEGS = []
_o = 0
for name, a, b in EDL:
    SEGS.append((name, a, b, _o))
    _o += b - a
N_OUT = _o
T_END = N_OUT / FPS
SEG = {name: (a, b, o) for name, a, b, o in SEGS}

def seg_out(name):
    a, b, o = SEG[name]
    return o / FPS, (o + b - a) / FPS

def out_frame_to_src(k):
    for _, a, b, o in SEGS:
        if o <= k < o + (b - a):
            return a + (k - o)
    raise ValueError(k)

# ---------------------------------------------------------------- effects config
R.ZOOM_MAX, R.ZOOM_END, R.ZOOM_RAMP = 1.30, 1.34, 1.10

FONT_TOP = os.path.join(R.ROOT, "fonts", "CormorantGaramond-Italic.ttf")
FONT_BOTTOM = os.path.join(R.ROOT, "fonts", "LexendMega.ttf")
R.F_L1 = R.font(FONT_TOP, 84, 600)
R.F_L2 = R.font(FONT_BOTTOM, 28, 300)
R.L2_TRACK = 0.0
R.LINE_GAP = 13
R.LINE_W = 3.0

class LabelV4(R.Label):
    """Label with output-time window and output-time anchor keyframes."""

    def __init__(self, t0, t1, *args, shadow_alpha=0.38, shadow_blur=10, **kw):
        self._sh_alpha, self._sh_blur = shadow_alpha, shadow_blur
        super().__init__(t0, t1, *args, **kw)

    def line_points(self, t):
        if self.style == "side":
            q = (self.tx - 36, self.l1_mid)
            return (q[0] - self.line_len, q[1]), q
        q = (self.tx + 4, self.block_bottom + 26)
        return self.product_point(t), q

    def _shadow(self, layer):
        return R.Label._shadow(layer, blur=self._sh_blur, alpha=self._sh_alpha)

def src_out(name, ts):
    a, b, o = SEG[name]
    return (o + ts * FPS - a) / FPS

def within(name, d0=0.05, d1=0.03):
    s, e = seg_out(name)
    return s + d0, e - d1

def build_labels():
    L = []
    t0, t1 = within("mesa_vermelho")
    L.append(LabelV4(t0, t1, "Sousplat", "em fio de malha", 345, 605, "light", "drop",
                     anchors=[(t0, (300, 930)), (t1, (650, 930))]))
    t0, t1 = within("chao_redondo_marrom", 0.10)
    L.append(LabelV4(t0, t1, "Tapete redondo", "de crochê", 390, 905, "light", "drop",
                     anchors=[(t0, (330, 1240))]))
    t0 = seg_out("chao_retang_marinho")[0] + 0.05
    t1 = seg_out("chao_retang_marrom")[1] - 0.03
    L.append(LabelV4(t0, t1, "Tapete retangular", "de crochê em fio de malha", 260, 930, "light", "drop",
                     anchors=[(t0, (200, 1200))]))
    # geométrico: same layout as v3 (text on the tiles above the rug, line down to the rug)
    t0, t1 = within("chao_geo_aberto")
    L.append(LabelV4(t0, t1, "Tapete geométrico", "em crochê e em fio de malha", 90, 276, "light", "drop",
                     anchors=[(src_out("chao_geo_aberto", 47.82), (240, 650)),
                              (src_out("chao_geo_aberto", 48.50), (330, 650)),
                              (src_out("chao_geo_aberto", 49.26), (500, 640))], fast=True,
                     shadow_alpha=0.62, shadow_blur=12))
    t0, t1 = within("chao_passadeira", 0.45)
    L.append(LabelV4(t0, t1, "Jogo de passadeira", "feito em tear manual", 240, 940, "light", "drop",
                     anchors=[(t0, (180, 1180))]))
    s, _ = seg_out("menores_1")
    t0, t1 = s + 0.19, s + 1.99
    L.append(LabelV4(t0, t1, "Tapete redondo menor", "de crochê", 105, 1062, "light", "drop",
                     anchors=[(t0, (300, 1320))]))
    return L

LABELS = build_labels()

# ---------------------------------------------------------------- white haze intro/outro
HAZE_VEIL = 0.80        # white veil opacity at full haze (footage still faintly visible)
HAZE_BLUR = 30          # px, at full haze
INTRO_HOLD, INTRO_CLEAR = 1.05, 1.90
OUTRO_START, OUTRO_FULL = T_END - 1.70, T_END - 0.75
LOGO_OUT_VEIL = 0.90

def haze(img, h, veil):
    if h <= 0.001:
        return img
    small = img.resize((W // 4, H // 4), Image.BILINEAR)
    small = small.filter(ImageFilter.GaussianBlur(HAZE_BLUR * h / 4))
    blurred = small.resize((W, H), Image.BILINEAR)
    a = np.asarray(img, np.float32)
    b = np.asarray(blurred, np.float32)
    mix = min(1.0, h * 1.25)
    out = a + (b - a) * mix
    out = out + (255.0 - out) * (veil * h)
    return Image.fromarray(np.clip(out + 0.5, 0, 255).astype(np.uint8), img.mode)

def logo_layer(alpha, scale, blur):
    lg = R.logo_img()
    sw, sh = round(lg.width * scale), round(lg.height * scale)
    lg = lg.resize((sw, sh), Image.LANCZOS)
    if blur > 0.05:
        pad = 24
        c = Image.new("RGBA", (sw + 2 * pad, sh + 2 * pad), (0, 0, 0, 0))
        c.paste(lg, (pad, pad))
        lg = c.filter(ImageFilter.GaussianBlur(blur))
    return R.fade(lg, alpha)

def put_logo(frame, alpha, scale, blur):
    if alpha <= 0.002:
        return frame
    lg = logo_layer(alpha, scale, blur)
    frame.alpha_composite(lg, (round(R.LOGO_CENTER[0] - lg.width / 2), round(R.LOGO_CENTER[1] - lg.height / 2)))
    return frame

def intro_outro(frame, t):
    """frame: RGB image. Returns RGBA image."""
    e = R.ease_in_out_sine
    if t < INTRO_CLEAR:
        h = 1.0 if t < INTRO_HOLD else 1.0 - e((t - INTRO_HOLD) / (INTRO_CLEAR - INTRO_HOLD))
        img = haze(frame, h, HAZE_VEIL).convert("RGBA")
        # logo: in 0.12-0.55, hold, out 1.00-1.60 (slight blur + growth)
        if t < 0.55:
            k = R.ease_out_cubic((t - 0.12) / 0.43)
            return put_logo(img, k, 0.97 + 0.03 * k, 0)
        if t < 1.00:
            return put_logo(img, 1.0, 1.0 + 0.01 * (t - 0.55) / 0.45, 0)
        k = e((t - 1.00) / 0.60)
        return put_logo(img, 1 - k, 1.01 + 0.04 * k, 6 * k)
    if t >= OUTRO_START:
        h = e((t - OUTRO_START) / (OUTRO_FULL - OUTRO_START))
        img = haze(frame, h, LOGO_OUT_VEIL).convert("RGBA")
        k = R.ease_out_cubic((t - (OUTRO_FULL - 0.25)) / 0.55)
        return put_logo(img, k, 0.97 + 0.03 * k, 0)
    return frame.convert("RGBA")

# ---------------------------------------------------------------- frame processing
def active_overlay(t):
    return t < INTRO_CLEAR or t >= OUTRO_START or any(lb.t0 <= t < lb.t1 for lb in LABELS)

def needs_processing(k, s):
    return (R.ZOOM_F0 <= s < R.ZOOM_F1) or active_overlay(k / FPS)

def process(rgb, k, s):
    t = k / FPS
    img = Image.fromarray(rgb, "RGB")
    img = R.apply_zoom(img, s)
    if not active_overlay(t):
        return img
    img = intro_outro(img, t)
    for lb in LABELS:
        img = lb.draw(img, t)
    return img.convert("RGB")

def plan():
    print(f"{'#':>2} {'trecho':22s} {'src':>15s} {'out':>15s} {'dur':>5s}")
    for i, (name, a, b, o) in enumerate(SEGS):
        print(f"{i:2d} {name:22s} {a / FPS:6.2f}-{b / FPS:6.2f}  {o / FPS:6.2f}-{(o + b - a) / FPS:6.2f} {(b - a) / FPS:5.2f}")
    print(f"total {N_OUT} frames = {T_END:.2f}s | intro haze clears at {INTRO_CLEAR}s | outro from {OUTRO_START:.2f}s")
    for lb in LABELS:
        print(f"label {lb.t0:6.2f}-{lb.t1:6.2f}s ({lb.t1 - lb.t0:.2f}s)")

ENC = ["-c:v", "libx264", "-preset", "medium", "-crf", "14", "-profile:v", "high",
       "-pix_fmt", "yuv420p", "-colorspace", "bt709", "-color_primaries", "bt709",
       "-color_trc", "bt709", "-color_range", "tv", "-g", "30", "-bf", "2"]
ENC_VF = "scale=out_color_matrix=bt709:out_range=tv:flags=accurate_rnd+full_chroma_int"

def render(out_path):
    work = os.path.join(os.path.dirname(os.path.abspath(out_path)), "segs")
    os.makedirs(work, exist_ok=True)
    fs = W * H * 3
    by_src = sorted(range(len(SEGS)), key=lambda i: SEGS[i][1])
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", R.SRC, "-vf", R.DEC_VF, "-vsync", "passthrough",
                            "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    s = 0
    for i in by_src:
        name, a, b, o = SEGS[i]
        while s < a:
            if len(dec.stdout.read(fs)) < fs:
                raise RuntimeError("source ended early")
            s += 1
        enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                                "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-vf", ENC_VF, *ENC, "-an",
                                os.path.join(work, f"seg_{i:02d}.mp4")], stdin=subprocess.PIPE)
        while s < b:
            buf = dec.stdout.read(fs)
            if len(buf) < fs:
                raise RuntimeError("source ended early")
            k = o + (s - a)
            if needs_processing(k, s):
                buf = process(np.frombuffer(buf, np.uint8).reshape(H, W, 3), k, s).tobytes()
            enc.stdin.write(buf)
            s += 1
        enc.stdin.close()
        enc.wait()
        print(f"seg {i:02d} {name} done", file=sys.stderr, flush=True)
    dec.stdout.close()
    dec.kill()
    lst = os.path.join(work, "list.txt")
    with open(lst, "w") as f:
        for i in range(len(SEGS)):
            f.write(f"file 'seg_{i:02d}.mp4'\n")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst,
                    "-c", "copy", "-an", "-movflags", "+faststart", out_path], check=True)
    print("master written", out_path, N_OUT, "frames")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--preview")
    ap.add_argument("--render")
    args = ap.parse_args()
    if args.plan:
        plan()
    if args.preview:
        od = os.path.join(R.ROOT, "out", "preview_v4")
        os.makedirs(od, exist_ok=True)
        for tstr in args.preview.split(","):
            k = min(round(float(tstr) * FPS), N_OUT - 1)
            s = out_frame_to_src(k)
            img = process(R.decode_frame(s), k, s)
            p = os.path.join(od, f"v4_{float(tstr):06.2f}.png")
            img.save(p)
            print(p)
    if args.render:
        render(args.render)

if __name__ == "__main__":
    main()
