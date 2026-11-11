"""Overlay for video 4 (cortina corta-luz, Sara) - same style as video 3 (kit colher).

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
DUR = 1290 / 30
CAP_Y = 1330      # fixed caption centre (inside the Reels safe area)
HL_Y = 1060       # highlight centre (Sara is small in frame: chin reaches y~907)
EV = []


def cap(text, t0, t1):
    EV.append(dict(kind="cap", t0=t0, t1=t1, y=CAP_Y, lines=[dict(text=text, size=60, font="cool", t=t0)]))


def hl(lines, t1):
    """lines: (text, size, font, t) ; font 'serif' or 'cool' (small label)."""
    EV.append(dict(kind="hl", t0=lines[0][3], t1=t1, y=HL_Y,
                   lines=[dict(text=a, size=b, font=c, t=d) for a, b, c, d in lines]))


def measure(a, b, ta, tb, t_label, t1):
    """size highlight: first number, then ' x <length> m', then a small 'de comprimento' label."""
    EV.append(dict(kind="hl", t0=ta, t1=t1, y=HL_Y, lines=[
        dict(text=a + b, size=116, font="serif", t=ta, parts=[dict(text=a, t=ta), dict(text=b, t=tb)]),
        dict(text="de comprimento", size=56, font="cool", t=t_label)]))


# ---------------- hook (0 - 3.467) ----------------
cap("se você está", 0.08, 0.80)
cap("pensando em trocar", 0.80, 1.82)
hl([("as", 56, "cool", 1.82), ("cortinas", 156, "serif", 1.98)], 2.56)
cap("da sua casa,", 2.56, 3.46)
# ---------------- eu vou te mostrar (3.467 - 7.333) ----------------
cap("eu vou te mostrar", 3.48, 4.26)
cap("uma opção", 4.26, 5.00)
cap("que une", 5.00, 5.46)
hl([("praticidade", 118, "serif", 5.46), ("e beleza", 118, "serif", 6.68)], 7.30)
# ---------------- essa é a nossa (7.333 - 9.5) ----------------
cap("essa é a nossa", 7.43, 8.11)
hl([("cortina", 150, "serif", 8.11), ("corta-luz", 130, "serif", 8.71)], 9.48)
# ---------------- ideal para quem (9.5 - 15.133) ----------------
cap("ideal para quem", 9.53, 10.33)
cap("procura mais", 10.33, 11.07)
hl([("conforto", 160, "serif", 11.07)], 11.95)
cap("e quer diminuir", 11.95, 12.97)
cap("a entrada de", 12.97, 13.65)
hl([("claridade", 150, "serif", 13.65)], 14.35)
cap("no ambiente.", 14.35, 15.12)
# ---------------- ela é produzida (15.133 - 17.433) ----------------
cap("ela é produzida", 15.14, 16.29)
hl([("em", 56, "cool", 16.29), ("tecido duplo", 132, "serif", 16.45)], 17.42)
# ---------------- na frente o voal (17.433 - 21.233) ----------------
hl([("na frente, o", 56, "cool", 17.45), ("voal", 160, "serif", 18.15)], 18.85)
cap("e na parte de trás", 18.85, 19.97)
cap("o tecido corta-luz.", 19.97, 21.20)
# ---------------- e nós fazemos (21.233 - 24.267) ----------------
cap("e nós fazemos", 21.26, 22.12)
cap("elas também", 22.12, 22.98)
hl([("em", 56, "cool", 22.99), ("três tamanhos", 114, "serif", 23.15)], 24.24)
# ---------------- medidas (24.267 - 32.567): each size builds as it is spoken ----------------
cap("na medida de", 24.28, 25.09)
measure("3,00", " x 1,80 m", 25.09, 25.68, 26.32, 27.28)
measure("3,00", " x 2,20 m", 27.30, 27.98, 28.74, 29.76)
measure("4,00", " x 2,60 m", 29.98, 30.91, 31.97, 32.55)
# ---------------- três cores (32.567 - 38.133) ----------------
cap("e temos ela", 32.59, 33.57)
hl([("em", 56, "cool", 33.57), ("três opções", 128, "serif", 33.75), ("de cores", 100, "serif", 34.61)], 35.40)
cap("querem conhecer", 35.43, 36.29)
cap("as outras cores", 36.29, 37.21)
cap("disponíveis?", 37.21, 38.11)
# ---------------- clique (38.133 - 40.933) ----------------
cap("clique no", 38.13, 38.60)
hl([("link abaixo", 144, "serif", 38.60)], 39.42)
cap("e entre em contato", 39.42, 40.22)
cap("com a nossa equipe.", 40.22, 40.93)
# ---------------- nós enviamos (40.933 - 43.0) ----------------
cap("nós enviamos para", 40.95, 42.06)
hl([("todo o Brasil", 128, "serif", 42.06)], DUR + 1)

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
    if (L.parts) {
      L.parts.forEach((P, pi) => { const sp = document.createElement("span"); sp.className = "part p" + pi; sp.textContent = P.text; sp.style.display = "inline-block"; sp.style.whiteSpace = "pre"; el.appendChild(sp); });
    } else el.textContent = L.text;
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
      if (e.lines[li].parts) {
        e.lines[li].parts.forEach((P, pi) => {
          const sp = el.querySelector(".p" + pi);
          tl.fromTo(sp, { opacity: 0, y: 10, filter: "blur(8px)" }, { opacity: 1, y: 0, filter: "blur(0px)", duration: 0.3, ease: "power3.out" }, P.t);
        });
        return;
      }
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
