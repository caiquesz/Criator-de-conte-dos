"""Casa Marina v9 - overlays on the v9 clean master (re-recorded on the wooden deck).

Changes vs v8:
  * intro: no white haze - only the logo, quick, over the box being put on the floor
    (white logo, soft diffuse shadow, fade-in 0.25 s, hold, fade-out with slight blur);
  * 'jogo de passadeira' label on the 3-piece set; the red/white rug is 'tapete para sala';
  * shorter cuts; small round rugs 'appear' one by one (menores_fx.py);
  * outro unchanged (white haze + logo).
Usage: python3 render_v9.py CLEAN_MASTER.mp4 OUT.mp4 [--preview t1,t2,...]
"""
import json
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render as R          # noqa: E402
import render_v5 as V5      # noqa: E402
import render_v4 as V4      # noqa: E402

FPS = 30
ROOT = R.ROOT
SEGS = {s["name"]: s for s in json.load(open(os.path.join(ROOT, "out", "v9_segs.json")))}

LOGO_IN, LOGO_HOLD, LOGO_OUT = 0.25, 1.20, 1.60       # seconds
LOGO_W = 520
LOGO_CENTER = (540, 600)
_logo = {}


def white_logo():
    if "img" not in _logo:
        lg = Image.open(R.LOGO).convert("RGBA")
        h = round(lg.height * LOGO_W / lg.width)
        lg = lg.resize((LOGO_W, h), Image.LANCZOS)
        a = lg.getchannel("A")
        white = Image.new("RGBA", lg.size, (255, 252, 247, 0))
        white.putalpha(a)
        pad = 40
        sh = Image.new("L", (lg.width + 2 * pad, lg.height + 2 * pad), 0)
        sh.paste(a, (pad, pad))
        sh = sh.filter(ImageFilter.GaussianBlur(13)).point(lambda v: round(v * 0.70))
        shadow = Image.new("RGBA", sh.size, (25, 14, 8, 0))
        shadow.putalpha(sh)
        _logo["img"], _logo["shadow"], _logo["pad"] = white, shadow, pad
    return _logo["img"], _logo["shadow"], _logo["pad"]


def put_logo_quick(frame, t):
    if t >= LOGO_OUT:
        return frame
    lg, sh, pad = white_logo()
    if t < LOGO_IN:
        k = R.ease_out_cubic(t / LOGO_IN)
        alpha, scale, blur = k, 0.96 + 0.04 * k, 0.0
    elif t < LOGO_HOLD:
        alpha, scale, blur = 1.0, 1.0 + 0.01 * (t - LOGO_IN) / (LOGO_HOLD - LOGO_IN), 0.0
    else:
        k = R.ease_in_out_sine((t - LOGO_HOLD) / (LOGO_OUT - LOGO_HOLD))
        alpha, scale, blur = 1.0 - k, 1.01 + 0.03 * k, 5.0 * k
    for img, off in ((sh, pad), (lg, 0)):
        w, h = round(img.width * scale), round(img.height * scale)
        im = img.resize((w, h), Image.LANCZOS)
        if blur > 0.05:
            im = im.filter(ImageFilter.GaussianBlur(blur))
        im = R.fade(im, alpha)
        frame.alpha_composite(im, (round(LOGO_CENTER[0] - w / 2), round(LOGO_CENTER[1] - h / 2 + 3 * (off > 0))))
    return frame


def intro_outro(frame, t):
    if t < LOGO_OUT:
        return put_logo_quick(frame.convert("RGBA"), t)
    if t >= V4.OUTRO_START:
        return V4._orig_intro_outro(frame, t)
    return frame.convert("RGBA")


def rng(name, d0=0.05, d1=0.03, f0=0.0, f1=1.0):
    s = SEGS[name]
    return (s["out0"] + s["frames"] * f0) / FPS + d0, (s["out0"] + s["frames"] * f1) / FPS - d1


def setup(master):
    n = int(subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v", "-show_entries",
                            "stream=nb_read_frames", "-of", "csv=p=0", master], capture_output=True, text=True).stdout)
    R.SRC = master
    V4.SEGS = [("all", 0, n, 0)]
    V4.N_OUT = n
    V4.T_END = n / FPS
    V4.OUTRO_START, V4.OUTRO_FULL = V4.T_END - 1.70, V4.T_END - 0.75
    V4.INTRO_CLEAR = LOGO_OUT
    if not hasattr(V4, "_orig_intro_outro"):
        V4._orig_intro_outro = V4.intro_outro
    V4.intro_outro = intro_outro
    a = SEGS["adesivo"]
    R.ZOOM_F0, R.ZOOM_F1 = a["out0"], a["out0"] + a["frames"]
    R.ZOOM_T0 = R.ZOOM_F0 / FPS
    R.ZOOM_MAX, R.ZOOM_END, R.ZOOM_RAMP = 1.30, 1.34, 1.00
    R.TRACK = os.path.join(ROOT, "out", "v9", "track_adesivo.json")
    R._track = None
    L = V5.CenteredLabel
    deck = dict(shadow_alpha=0.55, shadow_blur=12)
    strong = dict(shadow_alpha=0.80, shadow_blur=14)
    labels = []
    t0, t1 = rng("mesa_vermelho")
    labels.append(L(t0, t1, "SOUSPLAT", "em fio de malha", 650, 1240, "up", 120))
    t0, t1 = rng("deck_redondo_cru", 0.10)
    labels.append(L(t0, t1, "TAPETE REDONDO", "de crochê", 700, 290, "down", 105, **deck))
    t0, t1 = rng("deck_retang_marinho")
    labels.append(L(t0, t1, "TAPETE RETANGULAR", "de crochê em fio de malha", 600, 740, "up", 110, **deck))
    t0, t1 = rng("deck_geometrico")
    labels.append(L(t0, t1, "TAPETE GEOMÉTRICO", "em crochê e em fio de malha", 430, 470, "down", 110, **deck))
    t0, t1 = rng("deck_passadeira_jogo", 0.65)
    labels.append(L(t0, t1, "JOGO DE PASSADEIRA", "feito em tear manual", 540, 240, "down", 70, fast=True, **strong))
    t0, t1 = rng("deck_tapete_sala")
    labels.append(L(t0, t1, "TAPETE PARA SALA", "", 700, 360, "down", 140, **deck))
    t0, t1 = rng("menores_aparecem", 0.35, 0.05)
    labels.append(L(t0, t1, "TAPETE REDONDO MENOR", "de crochê", 520, 330, "down", 150, **strong))
    V4.LABELS = labels


def main():
    master, out = sys.argv[1], sys.argv[2]
    setup(master)
    if "--preview" in sys.argv:
        ts = sys.argv[sys.argv.index("--preview") + 1].split(",")
        od = os.path.join(ROOT, "out", "v9", "preview")
        os.makedirs(od, exist_ok=True)
        for tstr in ts:
            k = min(round(float(tstr) * FPS), V4.N_OUT - 1)
            img = V4.process(R.decode_frame(k), k, k)
            p = os.path.join(od, f"p_{float(tstr):06.2f}.png")
            img.save(p)
            print(p)
        return
    V4.render(out)


if __name__ == "__main__":
    main()
