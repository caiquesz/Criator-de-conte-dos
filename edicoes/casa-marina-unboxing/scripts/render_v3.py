"""Casa Marina reel - v3 (v2 re-cut + new type pairing + single text colour, no audio).

Structure: each product is pulled out of the box and the very next shot shows it in
its room ("unboxing -> in situ"), in the order of the product list:
  intro (logo + sticker zoom + opening) -> sousplat -> tapete redondo -> tapete
  retangular -> tapete geométrico -> passadeira -> tapetes redondos menores -> close.

v3 changes: the white round rug pulled from the box belongs to the smaller round rugs;
labels use Cormorant Garamond Italic (product) + Lexend Mega Light (material), all in
the Casa Marina brown; passadeira text sits on the cream stripe, rectangular text on
the tiles of the wide take (shown first).
Reuses the v1 effects from render.py (logo intro, sticker push-in, labels).
EDL is in *source frame* numbers [a, b). Overlays: zoom keyed to source frames,
logo/labels animated in output time, label anchor points keyed to source time.

Usage:
  python3 render_v3.py --plan                       # print the EDL / label timings
  python3 render_v3.py --preview 3.2,10.5           # output-time stills
  python3 render_v3.py --render out/v3/master.mp4   # segments + concat (no audio)
"""
import argparse
import os
import subprocess
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render as R  # noqa: E402

FPS = R.FPS

# (name, a, b) source frames, in OUTPUT order
EDL = [
    ("intro_logo",        0,   60),
    ("adesivo_zoom",     60,  113),
    ("abre_caixa",      141,  171),
    ("papel_seda",      171,  195),
    ("revela",          222,  258),
    # Sousplat
    ("tira_sousplat_bege",  303,  352),
    ("tira_sousplat_verm",  368,  407),
    ("mesa_prato",          969, 1019),
    ("mesa_copo",          1019, 1062),
    ("mesa_vermelho",      1092, 1125),
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
    ("textura_final",      2050, 2110),
]

SEGS = []
_o = 0
for name, a, b in EDL:
    SEGS.append((name, a, b, _o))
    _o += b - a
N_OUT = _o

def src_to_out_time(ts):
    f = ts * FPS
    for _, a, b, o in SEGS:
        if a - 1e-6 <= f <= b + 1e-6:
            return (o + (f - a)) / FPS
    raise ValueError(f"source time {ts} not in EDL")

def out_frame_to_src(k):
    for _, a, b, o in SEGS:
        if o <= k < o + (b - a):
            return a + (k - o)
    raise ValueError(k)

FONT_TOP = os.path.join(R.ROOT, "fonts", "CormorantGaramond-Italic.ttf")
FONT_BOTTOM = os.path.join(R.ROOT, "fonts", "LexendMega.ttf")
R.F_L1 = R.font(FONT_TOP, 70, 600)
R.F_L2 = R.font(FONT_BOTTOM, 24, 300)
R.L2_TRACK = 0.0
R.LINE_GAP = 12

class LabelV2(R.Label):
    """Label animated in output time, product anchor keyed to source time."""

    def __init__(self, src_t0, src_t1, *args, **kw):
        super().__init__(src_to_out_time(src_t0), src_to_out_time(src_t1), *args, **kw)
        self._src0, self._src1 = src_t0, src_t1
        self._ts = src_t0

    def line_points(self, t):
        if self.style == "side":  # leave room for the italic swash of the first letter
            q = (self.tx - 36, self.l1_mid)
            return (q[0] - self.line_len, q[1]), q
        return super().line_points(self._ts)

    def draw_v2(self, frame, t_out, t_src):
        self._ts = t_src
        return self.draw(frame, t_out)

# same layouts as v1 (validated on these source ranges)
LABELS = [
    LabelV2(32.45, 35.36, "Sousplat", "em fio de malha", 90, 292, "dark", "drop",
            anchors=[(32.45, (210, 800))]),
    LabelV2(40.80, 42.56, "Tapete redondo", "de crochê", 90, 268, "dark", "drop",
            anchors=[(40.80, (340, 770)), (42.56, (340, 650))]),
    LabelV2(53.27, 55.14, "Tapete retangular", "de crochê em fio de malha", 90, 276, "dark", "drop",
            anchors=[(53.27, (250, 860))]),
    LabelV2(47.82, 49.26, "Tapete geométrico", "em crochê e em fio de malha", 90, 276, "dark", "drop",
            anchors=[(47.82, (240, 650)), (48.50, (330, 650)), (49.26, (500, 640))], fast=True),
    LabelV2(43.05, 45.22, "Jogo de passadeira", "feito em tear manual", 250, 760, "dark", "side",
            line_len=72),
    LabelV2(55.56, 57.36, "Tapete redondo menor", "de crochê", 90, 548, "dark", "drop",
            anchors=[(55.56, (270, 990))]),
]

def needs_processing(k, s):
    t = k / FPS
    return (R.ZOOM_F0 <= s < R.ZOOM_F1) or t < R.LOGO_T_OUT or any(lb.t0 <= t < lb.t1 for lb in LABELS)

def process(rgb, k, s):
    t, ts = k / FPS, s / FPS
    img = Image.fromarray(rgb, "RGB")
    img = R.apply_zoom(img, s)
    if not (t < R.LOGO_T_OUT or any(lb.t0 <= t < lb.t1 for lb in LABELS)):
        return img
    img = img.convert("RGBA")
    img = R.apply_logo(img, t)
    for lb in LABELS:
        img = lb.draw_v2(img, t, ts)
    return img.convert("RGB")

def plan():
    print(f"{'#':>2} {'trecho':22s} {'src':>15s} {'out':>15s} {'dur':>5s}")
    for i, (name, a, b, o) in enumerate(SEGS):
        print(f"{i:2d} {name:22s} {a / FPS:6.2f}-{b / FPS:6.2f}  {o / FPS:6.2f}-{(o + b - a) / FPS:6.2f} {(b - a) / FPS:5.2f}")
    print(f"total {N_OUT} frames = {N_OUT / FPS:.2f}s")
    for lb in LABELS:
        print(f"label {lb.t0:6.2f}-{lb.t1:6.2f}s ({lb.t1 - lb.t0:.2f}s)  src {lb._src0}-{lb._src1}")

ENC = ["-c:v", "libx264", "-preset", "medium", "-crf", "14", "-profile:v", "high",
       "-pix_fmt", "yuv420p", "-colorspace", "bt709", "-color_primaries", "bt709",
       "-color_trc", "bt709", "-color_range", "tv", "-g", "30", "-bf", "2"]
ENC_VF = "scale=out_color_matrix=bt709:out_range=tv:flags=accurate_rnd+full_chroma_int"

def render(out_path):
    work = os.path.join(os.path.dirname(os.path.abspath(out_path)), "segs")
    os.makedirs(work, exist_ok=True)
    W, H = R.W, R.H
    fs = W * H * 3
    by_src = sorted(range(len(SEGS)), key=lambda i: SEGS[i][1])
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", R.SRC, "-vf", R.DEC_VF, "-vsync", "passthrough",
                            "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    s = 0
    for i in by_src:
        name, a, b, o = SEGS[i]
        while s < a:  # skip unused source frames
            if len(dec.stdout.read(fs)) < fs:
                raise RuntimeError("source ended early")
            s += 1
        seg_path = os.path.join(work, f"seg_{i:02d}.mp4")
        enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                                "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-vf", ENC_VF, *ENC, "-an",
                                seg_path], stdin=subprocess.PIPE)
        while s < b:
            buf = dec.stdout.read(fs)
            if len(buf) < fs:
                raise RuntimeError("source ended early")
            k = o + (s - a)
            if needs_processing(k, s):
                rgb = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
                buf = process(rgb, k, s).tobytes()
            enc.stdin.write(buf)
            s += 1
        enc.stdin.close()
        enc.wait()
        print(f"seg {i:02d} {name} done ({b - a} frames)", file=sys.stderr, flush=True)
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
        od = os.path.join(R.ROOT, "out", "preview_v3")
        os.makedirs(od, exist_ok=True)
        for tstr in args.preview.split(","):
            k = round(float(tstr) * FPS)
            s = out_frame_to_src(k)
            img = process(R.decode_frame(s), k, s)
            p = os.path.join(od, f"v3_{float(tstr):06.2f}.png")
            img.save(p)
            print(p)
    if args.render:
        render(args.render)

if __name__ == "__main__":
    main()
