"""Overlay for video 5 (jogo americano de Natal, Sara) - same style as videos 3 and 4.

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
DUR = 1142 / 30
CAP_Y = 1330      # fixed caption centre (inside the Reels safe area)
HL_Y = 980        # highlight centre (chin reaches y~791 in the talking shots)
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


# ---------------- hook (0 - 4.233) ----------------
cap("você não precisa", 0.02, 0.96)
hl([("gastar muito", 124, "serif", 0.96)], 1.92)
cap("para montar uma", 1.92, 2.70)
hl([("mesa linda", 146, "serif", 2.70)], 3.48)
cap("nesse Natal.", 3.48, 4.22)
# ---------------- às vezes (4.233 - 7.667) ----------------
cap("às vezes são os", 4.29, 5.13)
hl([("pequenos", 130, "serif", 5.13), ("detalhes", 130, "serif", 5.57)], 6.25)
cap("que fazem a diferença.", 6.25, 7.65)
# ---------------- olha só (7.667 - 11.933) ----------------
cap("olha só esse", 7.75, 8.39)
hl([("jogo americano", 104, "serif", 8.39), ("de Natal", 104, "serif", 9.23)], 9.85)
cap("que nós temos", 9.85, 10.53)
cap("aqui na", 10.53, 10.87)
hl([("Segredos", 116, "serif", 10.87), ("de Minas", 116, "serif", 10.87)], 11.92)
# ---------------- ele contém (11.933 - 17.767) ----------------
cap("ele contém", 11.97, 12.97)
hl([("6 americanos", 118, "serif", 12.97), ("+ 6 guardanapos", 96, "serif", 14.55)], 15.79)
cap("produzidos", 15.79, 16.59)
hl([("100% algodão", 112, "serif", 16.59)], 17.75)
# ---------------- ótima opção (17.767 - 21.4) ----------------
cap("é uma ótima opção", 17.82, 18.84)
cap("para dar aquele", 18.84, 19.64)
hl([("toque natalino", 110, "serif", 19.64)], 20.56)
cap("à sua mesa", 20.56, 21.38)
# ---------------- deixar tudo (21.4 - 25.067) ----------------
cap("e deixar tudo", 21.43, 22.35)
cap("ainda mais bonito", 22.35, 23.45)
cap("para receber", 23.45, 24.17)
hl([("a sua", 56, "cool", 24.17), ("família", 160, "serif", 24.51)], 25.05)
# ---------------- aqui na segredos (25.067 - 30.2) ----------------
cap("e aqui na", 25.08, 25.50)
cap("Segredos de Minas", 25.50, 26.58)
cap("você também encontra", 26.58, 27.94)
hl([("outras opções", 116, "serif", 27.94), ("de cores natalinas", 88, "serif", 28.84)], 30.18)
# ---------------- então se você (30.2 - 32.767) ----------------
cap("então se você quer", 30.22, 31.16)
cap("montar a sua mesa", 31.16, 32.06)
hl([("de", 56, "cool", 32.06), ("Natal", 176, "serif", 32.20)], 32.75)
# ---------------- não deixe (32.767 - 36.2) ----------------
cap("não deixe de entrar", 32.77, 33.59)
cap("em contato com a gente.", 33.59, 34.69)
cap("clique aí no", 34.69, 35.29)
hl([("link abaixo", 144, "serif", 35.29)], 36.19)
# ---------------- enviamos (36.2 - 38.067) ----------------
cap("que enviamos para", 36.20, 37.07)
hl([("todo o Brasil", 128, "serif", 37.07)], DUR + 1)

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
