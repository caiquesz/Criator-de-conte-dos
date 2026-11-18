"""Casa Marina v12 - overlays on the v12 clean master (new colour grade).

Labels: option B chosen by the client - no leader line, text block centred in the frame;
where the middle of the frame is busy/bright (light crochet, checks, stripes) the block
moves up to a calmer, darker area (scored with a luminance + texture measure on the
graded master: scripts/label_spots_v12.py). Same Westwing-style type and soft fade as v11.
Usage: python3 render_v12.py CLEAN_MASTER.mp4 OUT.mp4 [--preview t1,t2,...] [--tag name]
                                [--y seg=top,...]   (override block top for tests)
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render as R          # noqa: E402
import render_v4 as V4      # noqa: E402
import render_v10 as V10    # noqa: E402  (quick white logo intro)
import render_v11 as V11    # noqa: E402  (SerifLabel: Cormorant Garamond caps + Allura)

FPS = 30
ROOT = R.ROOT
SEGS = {s["name"]: s for s in json.load(open(os.path.join(ROOT, "out", "v12_segs.json")))}

# (segment, (d0, d1), caps, script, block top y or None = centred in the frame)
PLAN = [
    ("mesa_vermelho", (0.05, 0.03), "SOUSPLAT", "em fio de malha", None),
    ("deck_retang_marinho", (0.05, 0.03), "TAPETE RETANGULAR", "de crochê em fio de malha", None),
    ("deck_geometrico", (0.10, 0.03), "TAPETE GEOMÉTRICO", "em crochê e em fio de malha", 480),
    ("deck_passadeira_jogo", (0.55, 0.03), "JOGO DE PASSADEIRA", "feito em tear manual", 260),
    ("deck_tapete_sala", (0.05, 0.03), "TAPETE PARA SALA", "", 420),
    ("menores_aparecem", (0.35, 0.05), "TAPETE REDONDO MENOR", "de crochê", 250),
    ("redondos_final", (0.10, 0.03), "TAPETE REDONDO", "de crochê", None),
]
LABEL_END_CAP = {"redondos_final": 1.95}      # gone before the outro haze


def rng(name, d0, d1):
    s = SEGS[name]
    return s["out0"] / FPS + d0, (s["out0"] + s["frames"]) / FPS - d1


def build_labels(overrides=None):
    overrides = overrides or {}
    labels = []
    for seg, (d0, d1), caps, script, y in PLAN:
        y = overrides.get(seg, y)
        t0, t1 = rng(seg, d0, d1)
        if seg in LABEL_END_CAP:
            t1 = min(t1, t0 + LABEL_END_CAP[seg])
        labels.append(V11.SerifLabel(t0, t1, caps, script, "center", 540, y))
    return labels


def setup(master, overrides=None):
    n = int(subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v", "-show_entries",
                            "stream=nb_read_frames", "-of", "csv=p=0", master], capture_output=True, text=True).stdout)
    R.SRC = master
    V4.SEGS = [("all", 0, n, 0)]
    V4.N_OUT = n
    V4.T_END = n / FPS
    V4.OUTRO_START, V4.OUTRO_FULL = V4.T_END - 1.70, V4.T_END - 0.75
    V4.INTRO_CLEAR = V10.LOGO_OUT
    if not hasattr(V4, "_orig_intro_outro"):
        V4._orig_intro_outro = V4.intro_outro
    V4.intro_outro = V10.intro_outro
    R.ZOOM_F0, R.ZOOM_F1 = -1, -1
    V4.LABELS = build_labels(overrides)


def main():
    master, out = sys.argv[1], sys.argv[2]
    tag = sys.argv[sys.argv.index("--tag") + 1] if "--tag" in sys.argv else "v12"
    ov = {}
    if "--y" in sys.argv:
        for kv in sys.argv[sys.argv.index("--y") + 1].split(","):
            k, v = kv.split("=")
            ov[k] = None if v == "c" else int(v)
    setup(master, ov)
    if "--preview" in sys.argv:
        ts = sys.argv[sys.argv.index("--preview") + 1].split(",")
        od = os.path.join(ROOT, "out", "v12", "preview")
        os.makedirs(od, exist_ok=True)
        for tstr in ts:
            k = min(round(float(tstr) * FPS), V4.N_OUT - 1)
            img = V4.process(R.decode_frame(k), k, k)
            p = os.path.join(od, f"{tag}_{float(tstr):06.2f}.png")
            img.save(p)
            print(p)
        return
    V4.render(out)


if __name__ == "__main__":
    main()
