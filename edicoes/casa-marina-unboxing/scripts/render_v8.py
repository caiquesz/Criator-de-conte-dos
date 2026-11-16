"""Casa Marina v8 - overlays on the re-recorded (wooden deck) clean master.

Same proposal as v5: white-haze logo intro/outro, soft sticker push-in (1.3x), product
labels (Unbounded ExtraBold caps + Coming Soon) in white with a straight, static vertical
leader line. No audio, no colour grading.
Usage: python3 render_v8.py CLEAN_MASTER.mp4 OUT.mp4 [--preview t1,t2,...]
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render as R          # noqa: E402
import render_v5 as V5      # noqa: E402  (fonts + CenteredLabel; also configures render_v4)
import render_v4 as V4      # noqa: E402

FPS = 30
ROOT = R.ROOT
SEGS = {s["name"]: s for s in json.load(open(os.path.join(ROOT, "out", "v8_segs.json")))}


def rng(name, d0=0.05, d1=0.03, f0=0.0, f1=1.0):
    s = SEGS[name]
    a = s["out0"] + s["frames"] * f0
    b = s["out0"] + s["frames"] * f1
    return a / FPS + d0, b / FPS - d1


def setup(master):
    n = int(subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v", "-show_entries",
                            "stream=nb_read_frames", "-of", "csv=p=0", master], capture_output=True, text=True).stdout)
    R.SRC = master
    V4.SEGS = [("all", 0, n, 0)]
    V4.N_OUT = n
    V4.T_END = n / FPS
    V4.OUTRO_START, V4.OUTRO_FULL = V4.T_END - 1.70, V4.T_END - 0.75
    # sticker push-in on the "adesivo" shot, following the tracked sticker
    a = SEGS["adesivo"]
    R.ZOOM_F0, R.ZOOM_F1 = a["out0"], a["out0"] + a["frames"]
    R.ZOOM_T0 = R.ZOOM_F0 / FPS
    R.ZOOM_MAX, R.ZOOM_END, R.ZOOM_RAMP = 1.30, 1.34, 1.10
    R.TRACK = os.path.join(ROOT, "out", "v8", "track_adesivo.json")
    R._track = None
    L = V5.CenteredLabel
    deck = dict(shadow_alpha=0.55, shadow_blur=12)
    labels = []
    t0, t1 = rng("mesa_vermelho")
    labels.append(L(t0, t1, "SOUSPLAT", "em fio de malha", 650, 1240, "up", 120))
    t0, t1 = rng("deck_redondo_cru", 0.10, 0.0, 0.0, 0.74)
    labels.append(L(t0, t1, "TAPETE REDONDO", "de crochê", 700, 290, "down", 105, **deck))
    t0, t1 = rng("deck_retang_marinho")
    labels.append(L(t0, t1, "TAPETE RETANGULAR", "de crochê em fio de malha", 600, 740, "up", 110, **deck))
    t0, t1 = rng("deck_geometrico")
    labels.append(L(t0, t1, "TAPETE GEOMÉTRICO", "em crochê e em fio de malha", 470, 500, "down", 110, **deck))
    t0, t1 = rng("deck_passadeira_3")
    labels.append(L(t0, t1, "JOGO DE PASSADEIRA", "feito em tear manual", 600, 330, "down", 110, **deck))
    t0 = SEGS["menor_pink"]["out0"] / FPS + 0.05
    t1 = (SEGS["menor_azul"]["out0"] + SEGS["menor_azul"]["frames"]) / FPS - 0.03
    labels.append(L(t0, t1, "TAPETE REDONDO MENOR", "de crochê", 520, 500, "down", 120, **deck))
    V4.LABELS = labels


def main():
    master, out = sys.argv[1], sys.argv[2]
    setup(master)
    if "--preview" in sys.argv:
        ts = sys.argv[sys.argv.index("--preview") + 1].split(",")
        od = os.path.join(ROOT, "out", "v8", "preview")
        os.makedirs(od, exist_ok=True)
        for tstr in ts:
            k = min(round(float(tstr) * FPS), V4.N_OUT - 1)
            fr = R.decode_frame(k)
            img = V4.process(fr, k, k)
            p = os.path.join(od, f"p_{float(tstr):06.2f}.png")
            img.save(p)
            print(p)
        return
    V4.render(out)


if __name__ == "__main__":
    main()
