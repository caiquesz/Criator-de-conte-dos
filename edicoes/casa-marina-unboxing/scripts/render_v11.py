"""Casa Marina v11 - overlays on the v11 clean master.

Typography after the Westwing unboxing reference (thin serif caps, wide tracking + an
elegant hand-written script line just under it):
  * product name: Cormorant Garamond (upright, ~SemiBold for video legibility), caps,
    letter-spacing ~0.16 em;
  * material: Allura (script), sitting close under the caps, as in "WESTWING / Unboxing";
  * white, no outline, only a very soft diffuse shadow (wide + medium blur) so it reads on
    the sunny deck without looking like a box or an outline.
Animation: everything fades in together (caps, then script 0.12 s later, small 8 px rise);
no element appears alone first (v10 showed the leader line for ~5 frames before the text,
which read as a flicker on the geometric rug).

Layout styles (--style):
  center  - no line, text block centred in the frame (default, the user's suggestion);
  line    - straight vertical leader line from the product to the text (grows together
            with the text fade, never alone);
  top     - no line, block centred horizontally in the upper part of the frame (on the
            deck / a calm area, so it never covers the piece);
  divider - like top, plus a short thin horizontal rule between the caps and the script.

Usage: python3 render_v11.py CLEAN_MASTER.mp4 OUT.mp4 [--style center|line|divider]
                                [--preview t1,t2,...] [--tag name]
"""
import json
import os
import subprocess
import sys

from PIL import Image, ImageChops, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render as R          # noqa: E402
import render_v4 as V4      # noqa: E402
import render_v10 as V10    # noqa: E402  (quick white logo intro)

FPS = 30
ROOT = R.ROOT
SEGS = {s["name"]: s for s in json.load(open(os.path.join(ROOT, "out", "v11_segs.json")))}

F_CAPS_PATH = os.path.join(ROOT, "fonts", "CormorantGaramond.ttf")
F_SCRIPT_PATH = os.path.join(ROOT, "fonts", "Allura.ttf")
CAPS_SIZE, CAPS_WEIGHT, CAPS_TRACK = 60, 600, 0.15
MAX_W = 840                 # keep every line inside the safe width
SCRIPT_SIZE = 80
SCRIPT_OVERLAP = 2          # script line tucks slightly under the caps (px)
WHITE = (255, 252, 247)
SHADOW_RGB = (28, 18, 10)


def _caps_font(size=CAPS_SIZE):
    f = ImageFont.truetype(F_CAPS_PATH, size)
    f.set_variation_by_axes([CAPS_WEIGHT])
    return f


F_CAPS = _caps_font()


def caps_layer(text):
    """Caps line at the standard size; long names are scaled down to fit MAX_W."""
    size = CAPS_SIZE
    while True:
        lay = ink_layer(text, _caps_font(size), size * CAPS_TRACK)
        if lay.width <= MAX_W or size <= 40:
            return lay
        size -= 1
F_SCRIPT = ImageFont.truetype(F_SCRIPT_PATH, SCRIPT_SIZE)


def ink_layer(text, fnt, tracking=0.0):
    """Text as a tight white RGBA layer (cropped to the ink)."""
    a, _ = R.text_layer(text, fnt, WHITE, tracking)
    bb = a.getchannel("A").getbbox()
    return a.crop(bb)


def soft_shadow(layer, strength=1.0):
    """Two-scale diffuse shadow (no hard edge, never reads as an outline)."""
    pad = 60
    a = layer.getchannel("A")
    base = Image.new("L", (layer.width + 2 * pad, layer.height + 2 * pad), 0)
    base.paste(a, (pad, pad))
    wide = base.filter(ImageFilter.GaussianBlur(22)).point(lambda v: round(min(255, v * 0.55 * strength)))
    mid = base.filter(ImageFilter.GaussianBlur(5)).point(lambda v: round(min(255, v * 0.30 * strength)))
    sh = Image.new("RGBA", base.size, SHADOW_RGB + (0,))
    sh.putalpha(ImageChops.screen(wide, mid))
    return sh, pad


class SerifLabel:
    """Caps (serif, tracked) + script line. style: center | line | divider."""

    def __init__(self, t0, t1, caps, script, style="center", cx=540, y=None, line_dir="down", line_len=90,
                 shadow=1.0):
        self.t0, self.t1 = t0, t1
        self.style, self.cx, self.line_dir, self.line_len = style, cx, line_dir, line_len
        self.caps = caps_layer(caps)
        self.script = ink_layer(script, F_SCRIPT) if script else None
        gap = -SCRIPT_OVERLAP
        if style == "divider":
            gap = 46
        h = self.caps.height + ((gap + self.script.height) if self.script else 0)
        if y is None:                                   # centred block
            y = round(960 - h / 2)
        self.y = y
        self.caps_xy = (round(cx - self.caps.width / 2), y)
        if self.script:
            self.script_xy = (round(cx - self.script.width / 2), y + self.caps.height + gap)
        self.bottom = y + h
        self.div_y = y + self.caps.height + gap // 2
        self.sh_caps = soft_shadow(self.caps, shadow)
        self.sh_script = soft_shadow(self.script, shadow) if self.script else None
        self.width = max(self.caps.width, self.script.width if self.script else 0)

    def draw(self, frame, t):
        if not (self.t0 <= t < self.t1):
            return frame
        lt = t - self.t0
        dur_in, dur_out = 0.55, 0.38
        out_k = 1.0 - R.ease_in_out_sine((t - (self.t1 - dur_out)) / dur_out)
        k1 = R.ease_out_cubic(lt / dur_in)
        k2 = R.ease_out_cubic((lt - 0.12) / dur_in)
        if self.style == "line":
            if self.line_dir == "up":
                q = (self.cx, self.y - 22)
                p = (self.cx, q[1] - self.line_len)
            else:
                q = (self.cx, self.bottom + 22)
                p = (self.cx, q[1] + self.line_len)
            if k1 > 0:
                e = (p[0], p[1] + (q[1] - p[1]) * k1)
                R.draw_line(frame, p, e, WHITE, k1 * out_k, True)
        if self.style == "divider" and self.script and k1 > 0:
            half = 0.5 * 110 * k1
            R.draw_line(frame, (self.cx - half, self.div_y), (self.cx + half, self.div_y), WHITE, k1 * out_k, True)
        parts = [(self.caps, self.caps_xy, self.sh_caps, k1)]
        if self.script:
            parts.append((self.script, self.script_xy, self.sh_script, k2))
        for layer, (x, y), (sh, pad), k in parts:
            if k <= 0:
                continue
            alpha = k * out_k
            dy = round(8 * (1 - k))
            frame.alpha_composite(R.fade(sh, alpha), (x - pad, y - pad + dy + 2))
            frame.alpha_composite(R.fade(layer, alpha), (x, y + dy))
        return frame


def rng(name, d0=0.05, d1=0.03, f0=0.0, f1=1.0):
    s = SEGS[name]
    return (s["out0"] + s["frames"] * f0) / FPS + d0, (s["out0"] + s["frames"] * f1) / FPS - d1


# per-label placements: (segment, (d0, d1), caps, script, line-style placement)
#   line placement: (cx, y, dir, len) - text block top y, line from product towards text
#   divider placement: y (block top), centred horizontally
PLAN = [
    ("mesa_vermelho", (0.05, 0.03), "SOUSPLAT", "em fio de malha",
     dict(line=(650, 1240, "up", 120), divider=330)),
    ("deck_retang_marinho", (0.05, 0.03), "TAPETE RETANGULAR", "de crochê em fio de malha",
     dict(line=(560, 720, "up", 110), divider=330)),
    ("deck_geometrico", (0.10, 0.03), "TAPETE GEOMÉTRICO", "em crochê e em fio de malha",
     dict(line=(600, 330, "down", 90), divider=330)),
    ("deck_passadeira_jogo", (0.55, 0.03), "JOGO DE PASSADEIRA", "feito em tear manual",
     dict(line=(540, 230, "down", 70), divider=300)),
    ("deck_tapete_sala", (0.05, 0.03), "TAPETE PARA SALA", "",
     dict(line=(700, 360, "down", 140), divider=330)),
    ("menores_aparecem", (0.35, 0.05), "TAPETE REDONDO MENOR", "de crochê",
     dict(line=(520, 250, "down", 80), divider=235)),
    ("redondos_final", (0.10, 0.03), "TAPETE REDONDO", "de crochê",
     dict(line=(560, 300, "down", 90), divider=330)),
]
# the closing shot: label must be gone before the outro haze
LABEL_END_CAP = {"redondos_final": 1.95}


def build_labels(style):
    labels = []
    for seg, (d0, d1), caps, script, pl in PLAN:
        t0, t1 = rng(seg, d0, d1)
        if seg in LABEL_END_CAP:
            t1 = min(t1, t0 + LABEL_END_CAP[seg])
        if style == "line":
            cx, y, dr, ln = pl["line"]
            labels.append(SerifLabel(t0, t1, caps, script, "line", cx, y, dr, ln))
        elif style in ("divider", "top"):
            labels.append(SerifLabel(t0, t1, caps, script, style, 540, pl["divider"] + (8 if style == "top" else 0)))
        else:
            labels.append(SerifLabel(t0, t1, caps, script, "center", 540, None))
    return labels


def setup(master, style):
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
    R.ZOOM_F0, R.ZOOM_F1 = -1, -1          # no push-in on the sticker shot
    V4.LABELS = build_labels(style)


def main():
    master, out = sys.argv[1], sys.argv[2]
    style = sys.argv[sys.argv.index("--style") + 1] if "--style" in sys.argv else "center"
    tag = sys.argv[sys.argv.index("--tag") + 1] if "--tag" in sys.argv else style
    setup(master, style)
    if "--preview" in sys.argv:
        ts = sys.argv[sys.argv.index("--preview") + 1].split(",")
        od = os.path.join(ROOT, "out", "v11", "preview")
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
