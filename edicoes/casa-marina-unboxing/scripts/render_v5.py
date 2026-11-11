"""Casa Marina reel - v5.

Same cut, white haze intro/outro and soft sticker zoom as v4. Label changes:
  * type pairing from the reference "Sequel + CC-Doodly" (combination 2), using free
    look-alikes: Unbounded ExtraBold (caps, product) + Coming Soon (handwritten, material);
  * text centred, white, soft diffuse shadow only (no outline);
  * leader line is a straight VERTICAL stroke that stays still (no motion tracking):
    it grows from the product towards the text, then the text fades in.
Positions were chosen with scripts/place_search.py / bg_luma.py so the white text sits
on a dark part of the product for the whole time it is on screen.

Usage:
  python3 render_v5.py --plan | --preview 13.3,18.8 | --render out/v5/master.mp4
"""
import argparse
import os
import sys

from PIL import ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render as R      # noqa: E402
import render_v4 as V4  # noqa: E402

FONT_CAPS = os.path.join(R.ROOT, "fonts", "Unbounded.ttf")
FONT_HAND = os.path.join(R.ROOT, "fonts", "ComingSoon.ttf")

def _font(path, size, weight=None):
    f = ImageFont.truetype(path, size)
    if weight is not None:
        f.set_variation_by_axes([weight])
    return f

F_CAPS = _font(FONT_CAPS, 46, 800)
F_HAND = _font(FONT_HAND, 40)
GAP = 10
LINE_GAP_TEXT = 18      # space between the stroke end and the text block
R.LINE_W = 3.0

class CenteredLabel:
    def __init__(self, t0, t1, caps, hand, cx, y, line, length, shadow_alpha=0.38, shadow_blur=10,
                 fast=False):
        self.t0, self.t1 = t0, t1
        self.cx, self.y = cx, y
        self.line, self.length = line, length          # "up" or "down"
        self.fast = fast
        self.sh = (shadow_blur, shadow_alpha)
        a1, p1 = R.text_layer(caps, F_CAPS, R.LIGHT)
        a2, p2 = R.text_layer(hand, F_HAND, R.LIGHT)
        bb1 = a1.getchannel("A").getbbox()
        bb2 = a2.getchannel("A").getbbox()
        w1, w2 = bb1[2] - bb1[0], bb2[2] - bb2[0]
        self.l1 = (a1, round(cx - w1 / 2 - bb1[0]), y - bb1[1])
        y2 = y + (bb1[3] - bb1[1]) + GAP
        self.l2 = (a2, round(cx - w2 / 2 - bb2[0]), y2 - bb2[1])
        self.bottom = y2 + (bb2[3] - bb2[1])
        self.sh1 = R.Label._shadow(a1, blur=shadow_blur, alpha=shadow_alpha)
        self.sh2 = R.Label._shadow(a2, blur=shadow_blur, alpha=shadow_alpha)
        self.width = max(w1, w2)

    def stroke(self):
        if self.line == "up":
            q = (self.cx, self.y - LINE_GAP_TEXT)
            p = (self.cx, q[1] - self.length)
        else:
            q = (self.cx, self.bottom + LINE_GAP_TEXT)
            p = (self.cx, q[1] + self.length)
        return p, q                                    # grows from product (p) to text (q)

    def timings(self):
        if self.fast:
            return dict(line=(0.0, 0.28), t1=(0.14, 0.44), t2=(0.20, 0.50), out=0.26)
        return dict(line=(0.0, 0.42), t1=(0.22, 0.62), t2=(0.30, 0.70), out=0.32)

    def draw(self, frame, t):
        if not (self.t0 <= t < self.t1):
            return frame
        tm = self.timings()
        lt = t - self.t0
        out_k = 1.0 - R.ease_in_out_sine((t - (self.t1 - tm["out"])) / tm["out"])
        lk = R.ease_out_cubic((lt - tm["line"][0]) / (tm["line"][1] - tm["line"][0]))
        p, q = self.stroke()
        if lk > 0:
            e = (p[0], p[1] + (q[1] - p[1]) * lk)
            R.draw_line(frame, p, e, R.LIGHT, out_k, True)
        rise = -1 if self.line == "down" else 1
        for (layer, x, y), (a0, a1), (s_img, pad) in ((self.l1, tm["t1"], self.sh1),
                                                       (self.l2, tm["t2"], self.sh2)):
            k = R.ease_out_cubic((lt - a0) / (a1 - a0))
            if k <= 0:
                continue
            alpha = k * out_k
            dy = round(10 * (1 - k)) * rise
            frame.alpha_composite(R.fade(s_img, alpha), (x - pad, y - pad + dy + 2))
            frame.alpha_composite(R.fade(layer, alpha), (x, y + dy))
        return frame

def build_labels():
    w = V4.within
    so = V4.seg_out
    L = []
    t0, t1 = w("mesa_vermelho")
    L.append(CenteredLabel(t0, t1, "SOUSPLAT", "em fio de malha", 650, 1240, "up", 120))
    t0, t1 = w("chao_redondo_marrom", 0.10)
    L.append(CenteredLabel(t0, t1, "TAPETE REDONDO", "de crochê", 580, 1160, "up", 120))
    t0, t1 = so("chao_retang_marinho")[0] + 0.05, so("chao_retang_marrom")[1] - 0.03
    L.append(CenteredLabel(t0, t1, "TAPETE RETANGULAR", "de crochê em fio de malha", 500, 940, "up", 110))
    t0, t1 = w("chao_geo_aberto")
    L.append(CenteredLabel(t0, t1, "TAPETE GEOMÉTRICO", "em crochê e em fio de malha", 500, 340, "down", 200,
                           shadow_alpha=0.62, shadow_blur=12, fast=True))
    t0, t1 = w("chao_passadeira", 0.45)
    L.append(CenteredLabel(t0, t1, "JOGO DE PASSADEIRA", "feito em tear manual", 500, 985, "up", 75))
    s, _ = so("menores_1")
    L.append(CenteredLabel(s + 0.19, s + 1.99, "TAPETE REDONDO MENOR", "de crochê", 480, 1110, "up", 120))
    return L

V4.LABELS = build_labels()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--preview")
    ap.add_argument("--render")
    args = ap.parse_args()
    if args.plan:
        V4.plan()
        for lb in V4.LABELS:
            print(f"  w={lb.width}px  cx={lb.cx}  x {lb.cx - lb.width / 2:.0f}-{lb.cx + lb.width / 2:.0f}  y {lb.y}-{lb.bottom}")
    if args.preview:
        od = os.path.join(R.ROOT, "out", "preview_v5")
        os.makedirs(od, exist_ok=True)
        for tstr in args.preview.split(","):
            k = min(round(float(tstr) * V4.FPS), V4.N_OUT - 1)
            s = V4.out_frame_to_src(k)
            img = V4.process(R.decode_frame(s), k, s)
            p = os.path.join(od, f"v5_{float(tstr):06.2f}.png")
            img.save(p)
            print(p)
    if args.render:
        V4.render(args.render)

if __name__ == "__main__":
    main()
