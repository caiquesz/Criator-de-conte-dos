"""Casa Marina v15 - overlays on the v14 clean master.

v15: the opening logo sits in the centre of the frame (was at y=600, upper third). Over the
light fibre rug it gets a stronger two-scale diffuse shadow (still no outline).

v14 notes:

v14: sticker shot shorter (still slow motion, 1.6 s instead of 2.6 s) and the white rug pulled
from the box in the round-rug part (IMG_6855) removed. The v14 clean master is cut straight
from the graded v13 master (same grade), see README.

v13 notes:

v13: each name now comes in as soon as she takes the piece out of the box and stays until the
end of the piece's shot on the deck/table (client: "a palavra está desaparecendo muito
rápido"). One fixed position per name, chosen to be readable over every shot it spans
(the text stays still across the cuts). TAPETE PARA SALA gets its size: 1,50 x 2,00 m.

v12 notes:

Labels: option B chosen by the client - no leader line, text block centred in the frame;
where the middle of the frame is busy/bright (light crochet, checks, stripes) the block
moves up to a calmer, darker area (scored with a luminance + texture measure on the
graded master: scripts/label_spots_v12.py). Same Westwing-style type and soft fade as v11.
Usage: python3 render_v15.py CLEAN_MASTER.mp4 OUT.mp4 [--preview t1,t2,...] [--tag name]
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
SEGS = {s["name"]: s for s in json.load(open(os.path.join(ROOT, "out", "v14_segs.json")))}

# (first segment, last segment, (d0, d1), caps, script, block top y or None = centred)
PLAN = [
    ("tira_sousplat_cru", "mesa_vermelho", (0.20, 0.05), "SOUSPLAT", "em fio de malha", 450),
    ("tira_retang_marinho", "deck_retang_marinho", (0.20, 0.05), "TAPETE RETANGULAR",
     "de crochê em fio de malha", None),
    ("tira_geometrico", "deck_geometrico", (0.20, 0.05), "TAPETE GEOMÉTRICO", "em crochê e em fio de malha", 480),
    ("tira_passadeira", "deck_passadeira_jogo", (0.20, 0.05), "JOGO DE PASSADEIRA", "feito em tear manual", 260),
    ("abre_sala", "deck_tapete_sala", (0.20, 0.05), "TAPETE PARA SALA", "medida 1,50 x 2,00 m", 300),
    ("menores_aparecem", "menores_aparecem", (0.30, 0.05), "TAPETE REDONDO MENOR", "de crochê", 250),
    ("tira_redondo_teal", "redondos_final", (0.20, 0.05), "TAPETE REDONDO", "de crochê", 540),
]
LOGO_CENTER = (540, 960)                       # opening logo: centre of the frame
LABEL_END = {"TAPETE REDONDO": -1.80}          # closing shot: gone before the outro haze (s from end)


def centred_logo():
    """White logo + two-scale soft shadow (wide + medium blur, screen-combined)."""
    from PIL import Image, ImageChops, ImageFilter
    lg = Image.open(R.LOGO).convert("RGBA")
    h = round(lg.height * V10.LOGO_W / lg.width)
    lg = lg.resize((V10.LOGO_W, h), Image.LANCZOS)
    a = lg.getchannel("A")
    white = Image.new("RGBA", lg.size, (255, 252, 247, 0))
    white.putalpha(a)
    pad = 50
    base = Image.new("L", (lg.width + 2 * pad, lg.height + 2 * pad), 0)
    base.paste(a, (pad, pad))
    wide = base.filter(ImageFilter.GaussianBlur(18)).point(lambda v: round(min(255, v * 0.95)))
    mid = base.filter(ImageFilter.GaussianBlur(4)).point(lambda v: round(v * 0.38))
    sh = Image.new("RGBA", base.size, (25, 14, 8, 0))
    sh.putalpha(ImageChops.screen(wide, mid))
    V10._logo["img"], V10._logo["shadow"], V10._logo["pad"] = white, sh, pad


def span(first, last, d0, d1):
    a, b = SEGS[first], SEGS[last]
    return a["out0"] / FPS + d0, (b["out0"] + b["frames"]) / FPS - d1


def build_labels(overrides=None):
    overrides = overrides or {}
    labels = []
    t_end = sum(s["frames"] for s in SEGS.values()) / FPS
    for first, last, (d0, d1), caps, script, y in PLAN:
        y = overrides.get(first, y)
        t0, t1 = span(first, last, d0, d1)
        if caps in LABEL_END:
            t1 = min(t1, t_end + LABEL_END[caps])
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
    V10.LOGO_CENTER = LOGO_CENTER
    centred_logo()
    V4.LABELS = build_labels(overrides)


def main():
    master, out = sys.argv[1], sys.argv[2]
    tag = sys.argv[sys.argv.index("--tag") + 1] if "--tag" in sys.argv else "v15"
    ov = {}
    if "--y" in sys.argv:
        for kv in sys.argv[sys.argv.index("--y") + 1].split(","):
            k, v = kv.split("=")
            ov[k] = None if v == "c" else int(v)
    setup(master, ov)
    if "--preview" in sys.argv:
        ts = sys.argv[sys.argv.index("--preview") + 1].split(",")
        od = os.path.join(ROOT, "out", "v15", "preview")
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
