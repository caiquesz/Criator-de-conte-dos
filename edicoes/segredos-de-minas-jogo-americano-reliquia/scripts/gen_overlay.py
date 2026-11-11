"""Overlay for video 6 (jogo americano Relíquia, Sara) - same style as videos 3-5.

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
DUR = 978 / 30
CAP_Y = 1330      # fixed caption centre (inside the Reels safe area)
HL_Y = 960        # highlight centre (chin reaches y~716 in the talking shots)
EV = []


def cap(text, t0, t1):
    EV.append(dict(kind="cap", t0=t0, t1=t1, y=CAP_Y, lines=[dict(text=text, size=60, font="cool", t=t0)]))


def hl(lines, t1, y=None):
    """lines: (text, size, font, t) ; font 'serif' or 'cool' (small label).
    y: optional centre height for b-roll shots (no face), picked where the footage is darkest."""
    EV.append(dict(kind="hl", t0=lines[0][3], t1=t1, y=y or HL_Y,
                   lines=[dict(text=a, size=b, font=c, t=d) for a, b, c, d in lines]))


def measure(a, b, ta, tb, t_label, t1):
    """size highlight: first number, then ' x <length> m', then a small 'de comprimento' label."""
    EV.append(dict(kind="hl", t0=ta, t1=t1, y=HL_Y, lines=[
        dict(text=a + b, size=116, font="serif", t=ta, parts=[dict(text=a, t=ta), dict(text=b, t=tb)]),
        dict(text="de comprimento", size=56, font="cool", t=t_label)]))


# ---------------- hook (0 - 5.933) ----------------
cap("hoje eu vou", 0.08, 0.64)
cap("te mostrar um", 0.64, 1.22)
hl([("detalhe", 160, "serif", 1.22)], 1.92)
cap("que vai fazer", 1.93, 2.63)
hl([("toda a diferença", 100, "serif", 2.63)], 3.75)
cap("na hora de montar", 3.75, 4.77)
cap("a sua", 4.77, 5.13)
hl([("mesa posta", 146, "serif", 5.13)], 5.92)
# ---------------- esse é o nosso (5.933 - 8.867) ----------------
cap("esse é o nosso", 6.00, 7.22)
hl([("jogo americano", 104, "serif", 7.22), ("Relíquia", 150, "serif", 8.10)], 8.85)
# ---------------- vendido avulsa (8.867 - 12.367) ----------------
cap("ele é vendido a", 8.94, 9.98)
hl([("peça avulsa", 138, "serif", 9.98)], 10.96, y=1100)
hl([("produzida em", 56, "cool", 10.98), ("tear", 176, "serif", 11.74)], 12.40, y=1160)
# ---------------- 100% algodão (12.367 - 14.033) ----------------
hl([("e", 56, "cool", 12.42), ("100% algodão", 112, "serif", 12.60)], 14.02, y=1040)
# ---------------- aqui na segredos (14.033 - 17.8) ----------------
cap("e aqui na", 14.07, 14.57)
cap("Segredos de Minas", 14.57, 15.77)
cap("temos essa opção", 15.77, 16.89)
cap("que está", 16.89, 17.31)
hl([("linda", 176, "serif", 17.31)], 17.85)
# ---------------- outros modelos (17.8 - 23.067) ----------------
hl([("outros modelos", 106, "serif", 17.99), ("e cores", 106, "serif", 19.25)], 19.93, y=1100)
cap("para você escolher", 19.93, 20.89)
cap("aquele que mais", 20.89, 21.75)
cap("combina com", 21.75, 22.41)
cap("a sua casa.", 22.41, 23.05)
# ---------------- você quer conhecer (23.067 - 27.4) ----------------
cap("você quer conhecer", 23.10, 24.46)
cap("todas as opções", 24.46, 25.44)
cap("que nós temos", 25.44, 26.00)
cap("aqui na", 26.00, 26.34)
cap("Segredos de Minas?", 26.34, 27.38)
# ---------------- então clique (27.4 - 30.4) ----------------
cap("então clique no", 27.40, 28.06)
hl([("link abaixo", 144, "serif", 28.06)], 28.86)
cap("e mande uma mensagem", 28.86, 29.90)
cap("para a gente.", 29.90, 30.40)
# ---------------- nós enviamos (30.4 - 32.6) ----------------
cap("nós enviamos para", 30.42, 31.40)
hl([("todo o Brasil", 128, "serif", 31.40)], DUR + 1)

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
