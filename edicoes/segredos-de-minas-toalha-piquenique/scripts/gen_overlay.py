"""Overlay for video 7 (toalha piquenique, Sara) - same style as videos 3-6.

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
DUR = 811 / 30
CAP_Y = 1330      # fixed caption centre (inside the Reels safe area)
HL_Y = 1010       # highlight centre (chin reaches y~838 in the talking shots)
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


# ---------------- hook (0 - 5.7) ----------------
cap("uma", 0.06, 0.28)
hl([("mesa bonita", 134, "serif", 0.28)], 1.20)
cap("começa com", 1.20, 1.80)
hl([("uma", 56, "cool", 1.80), ("boa toalha", 130, "serif", 1.96)], 2.82)
cap("e essa aqui", 2.86, 3.58)
cap("pode ser a que", 3.58, 4.24)
cap("você estava", 4.24, 4.98)
hl([("procurando", 138, "serif", 4.98)], 5.70)
# ---------------- essa é a nossa (5.7 - 7.733) ----------------
cap("essa é a nossa", 5.76, 6.65)
hl([("toalha", 120, "serif", 6.65), ("piquenique", 140, "serif", 7.15)], 7.74)
# ---------------- é uma toalha (7.733 - 12.533) ----------------
cap("é uma toalha que", 7.76, 8.55)
cap("deixa a mesa", 8.55, 9.23)
cap("muito mais", 9.23, 9.77)
# three lines, so the block sits a little lower to stay clear of the chin
hl([("bonita,", 120, "serif", 9.77), ("alegre e", 120, "serif", 10.59), ("aconchegante", 110, "serif", 11.45)], 12.50, y=1080)
# ---------------- b-roll (12.533 - 27.033) ----------------
cap("ela é perfeita", 12.57, 13.57)
cap("para refeições", 13.57, 14.49)
hl([("em", 56, "cool", 14.49), ("família", 160, "serif", 14.61)], 15.30, y=900)
cap("cafés da tarde,", 15.32, 16.54)
cap("piqueniques", 16.54, 17.38)
cap("e também para", 17.38, 18.18)
hl([("valorizar", 130, "serif", 18.18), ("a decoração", 110, "serif", 19.04)], 19.78, y=1140)
cap("de sua casa.", 19.78, 20.62)
hl([("garanta já", 130, "serif", 20.62)], 21.40, y=900)
cap("a sua,", 21.40, 22.09)
cap("entre em contato", 22.09, 22.85)
cap("conosco", 22.85, 23.63)
cap("e consulte as", 23.63, 24.47)
hl([("cores", 160, "serif", 24.47), ("e tamanhos", 110, "serif", 25.15), ("disponíveis", 96, "serif", 25.75)], DUR + 1, y=980)

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
