"""Overlay for video 3 (kit colher, Sara).

- Standard caption: always the same spot (centre, y=1330), Coolvetica, white, short chunks,
  simple soft fade (no position changes).
- Highlight words: DM Serif Display Italic, white, centred at y=960, below Sara's face.
- All text plain white: no box, no outline, no shadow (client's call).

Writes OUTDIR/index.html.
Times are OUTPUT-timeline seconds.
"""
import json, sys, os

V = sys.argv[1]
OUTDIR = sys.argv[2]
DUR = 940 / 30
CAP_Y = 1330      # fixed caption centre (inside the Reels safe area)
HL_Y = 960        # highlight centre (face ends ~y 650 in every talking shot)
EV = []


def cap(text, t0, t1):
    EV.append(dict(kind="cap", t0=t0, t1=t1, y=CAP_Y, lines=[dict(text=text, size=60, font="cool", t=t0)]))


def hl(lines, t1):
    """lines: (text, size, font, t) ; font 'serif' or 'cool' (small label)."""
    EV.append(dict(kind="hl", t0=lines[0][3], t1=t1, y=HL_Y,
                   lines=[dict(text=a, size=b, font=c, t=d) for a, b, c, d in lines]))


# ---------------- hook (0 - 3.933) ----------------
cap("está chegando", 0.04, 0.82)
cap("a época dos", 0.82, 1.24)
hl([("amigos secretos", 104, "serif", 1.24)], 2.38)
cap("e das brincadeiras", 2.38, 3.32)
hl([("de", 56, "cool", 3.32), ("Natal", 176, "serif", 3.42)], 3.90)
# ---------------- e se você (3.933 - 7.9) ----------------
cap("e se você", 3.97, 4.50)
cap("ainda não sabe", 4.50, 5.27)
cap("o que comprar,", 5.27, 6.18)
cap("olha essa ideia", 6.18, 6.92)
cap("que eu tenho", 6.92, 7.32)
cap("para vocês.", 7.32, 7.88)
# ---------------- esse é o nosso kit (7.9 - 10.033) ----------------
cap("esse é o nosso", 8.00, 9.10)
hl([("kit de colher", 132, "serif", 9.10)], 10.06)
# ---------------- uma opção linda (10.033 - 14.367) ----------------
cap("uma opção", 10.08, 10.62)
cap("linda, útil", 10.62, 11.68)
cap("e com ótimo", 11.68, 12.42)
hl([("custo-benefício", 106, "serif", 12.42)], 13.40)
cap("para presentear.", 13.40, 14.34)
# ---------------- o kit vem com (14.367 - 17.733) ----------------
cap("o kit vem com", 14.40, 15.42)
hl([("pano de prato", 116, "serif", 15.42), ("+ colher de pau", 96, "serif", 16.62)], 17.70)
# ---------------- por apenas (17.733 - 19.6) ----------------
hl([("por apenas", 56, "cool", 17.74), ("R$ 15,00", 176, "serif", 18.44)], 19.58)
# ---------------- aqui na segredos (19.6 - 24.9) ----------------
cap("aqui na", 19.62, 19.94)
hl([("Segredos", 116, "serif", 19.94), ("de Minas", 116, "serif", 19.94)], 20.93)
cap("vocês encontram", 20.94, 21.89)
cap("várias estampas,", 21.89, 22.97)
cap("inclusive", 22.97, 23.64)
# held through the silent b-roll of the Christmas prints (24.9 - 26.0)
hl([("estampas", 120, "serif", 23.64), ("natalinas", 120, "serif", 24.08)], 25.96)
# ---------------- nós enviamos (26.0 - 28.167) ----------------
cap("e aqui nós", 26.03, 26.55)
cap("enviamos para", 26.55, 27.26)
hl([("todo o Brasil", 128, "serif", 27.26)], 28.15)
# ---------------- é só clicar (28.167 - 31.333) ----------------
cap("é só clicar aí", 28.20, 29.07)
hl([("link abaixo", 144, "serif", 29.07)], 30.12)
cap("para garantir o seu.", 30.12, DUR + 1)

json.dump(EV, open(os.path.join(V, "work/events.json"), "w"), ensure_ascii=False, indent=1)

HTML = r"""<!doctype html>
<html lang="pt-BR" data-resolution="portrait">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1080, height=1920" />
<script src="assets/js/gsap.min.js"></script>
<style>
@font-face { font-family: "Coolvetica"; src: url("assets/fonts/Coolvetica-Rg.otf") format("opentype"); font-display: block; }
@font-face { font-family: "DM Serif Display"; font-style: italic; src: url("assets/fonts/DMSerifDisplay-Italic.ttf") format("truetype"); font-display: block; }
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body { width: 1080px; height: 1920px; overflow: hidden; background: transparent; }
#root { position: relative; width: 1080px; height: 1920px; color: #fff; -webkit-font-smoothing: antialiased; }
.ev { position: absolute; left: 0; width: 1080px; display: flex; justify-content: center; opacity: 0; }
.card { position: relative; border-radius: 28px; text-align: center; white-space: nowrap; }
.cap .card { padding: 12px 26px 16px; border-radius: 22px; }
.hl .card { padding: 18px 44px 30px; border-radius: 36px; }
.line { display: block; line-height: 0.92; }
.cool { font-family: "Coolvetica", sans-serif; letter-spacing: -0.012em; font-feature-settings: "liga" 1, "kern" 1; }
.serif { font-family: "DM Serif Display", serif; font-style: italic; letter-spacing: -0.005em; line-height: 1.0; }
/* MODE */
__MODECSS__
</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="__DUR__" data-width="1080" data-height="1920"></div>
<script>
const EV = __EVENTS__;
const root = document.getElementById("root");
const tl = gsap.timeline({ paused: true });
EV.forEach((e, idx) => {
  const box = document.createElement("div");
  box.className = "ev " + e.kind;
  const card = document.createElement("div");
  card.className = "card";
  const lines = e.lines.map(L => {
    const el = document.createElement("div");
    el.className = "line txt " + L.font; el.style.fontSize = L.size + "px";
    el.textContent = L.text;
    card.appendChild(el);
    return el;
  });
  box.appendChild(card);
  root.appendChild(box);
  // vertical centring from known line metrics (fonts may not be measured yet)
  const lh = e.lines.reduce((a, L) => a + L.size * (L.font === "serif" ? 1.0 : 0.92), 0);
  const pad = e.kind === "cap" ? 28 : 48;
  box.style.top = (e.y - (lh + pad) / 2) + "px";
  if (e.kind === "cap") {
    // standard caption: same place every time, plain soft fade
    tl.fromTo(box, { opacity: 0, y: 6 }, { opacity: 1, y: 0, duration: 0.14, ease: "power2.out" }, e.t0);
    if (e.t1 < __DUR__) tl.to(box, { opacity: 0, duration: 0.1, ease: "power1.in" }, e.t1 - 0.08);
  } else {
    // highlight: card + first line together, later lines join when they are spoken
    tl.fromTo(box, { opacity: 0, scale: 0.96 }, { opacity: 1, scale: 1, duration: 0.24, ease: "power3.out" }, e.t0);
    lines.forEach((el, li) => {
      if (li === 0) {
        tl.fromTo(el, { opacity: 0, y: 10, filter: "blur(8px)" }, { opacity: 1, y: 0, filter: "blur(0px)", duration: 0.3, ease: "power3.out" }, e.lines[li].t);
      } else {
        tl.set(el, { opacity: 0 }, 0);
        tl.fromTo(el, { opacity: 0, y: 12, filter: "blur(8px)" }, { opacity: 1, y: 0, filter: "blur(0px)", duration: 0.3, ease: "power3.out" }, e.lines[li].t);
      }
    });
    if (e.t1 < __DUR__) tl.to(box, { opacity: 0, scale: 0.98, duration: 0.18, ease: "power1.in" }, e.t1 - 0.16);
  }
});
tl.set({}, {}, __DUR__);
window.__timelines = window.__timelines || {};
window.__timelines["main"] = tl;
tl.seek(0);
</script>
</body>
</html>
"""
TEXT_CSS = ".card { background: transparent; }"
base = HTML.replace("__EVENTS__", json.dumps(EV, ensure_ascii=False)).replace("__DUR__", f"{DUR:.4f}")
os.makedirs(OUTDIR, exist_ok=True)
open(os.path.join(OUTDIR, "index.html"), "w").write(base.replace("__MODECSS__", TEXT_CSS))
print("events", len(EV), "duration", DUR)
