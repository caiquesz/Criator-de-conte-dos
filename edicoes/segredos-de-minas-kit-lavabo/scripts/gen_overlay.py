"""Overlay for video 2 (kit lavabo): all-white Coolvetica, dynamic caption placement.

Each caption/stack lands in a different zone of the frame (chosen per window from a
readability scan of the edited base and kept off the face in talking shots).
Times are OUTPUT-timeline seconds.
"""
import json, sys, os

V = sys.argv[1]
OUT = sys.argv[2]
A = json.load(open(os.path.join(V, "work/anchors2.json")))
DUR = 1085 / 30
W = "#ffffff"

# zone -> (x, y_center, align)
Z = {
# kept inside the Reels safe area (see check_safe.py): y 290-1440, 60 px sides,
# and right-aligned text ends at x<=930 below y=1000 (like/comment/share column)
    "TL": (90, 430, "left"), "TR": (990, 430, "right"), "TC": (540, 430, "center"),
    "ML": (90, 760, "left"), "MR": (990, 760, "right"), "C": (540, 960, "center"),
    "LL": (90, 1170, "left"), "LR": (930, 1170, "right"), "LC": (540, 1170, "center"),
    "BL": (90, 1330, "left"), "BR": (930, 1330, "right"), "BC": (540, 1330, "center"),
}
EV = []


def ev(kind, zone, lines, t1, **kw):
    x, y, al = Z[zone] if isinstance(zone, str) else zone
    e = dict(kind=kind, t0=lines[0][2], t1=t1, x=x, y=y, align=al,
             lines=[dict(text=a, size=b, color=W, t=c) for a, b, c in lines])
    e.update(kw)
    EV.append(e)


def cap(text, t0, t1, zone, size=64):
    ev("cap", zone, [(text, size, t0)], t1)


def stack(zone, lines, t1):
    ev("stack", zone, lines, t1)


# ---------------- hook (0 - 6.033) ----------------
stack("MR", [("você está", 60, 0.00), ("procurando", 112, 0.56)], 1.10)
stack("C", [("uma opção de", 60, 1.10), ("presente", 140, 1.68)], 2.44)
cap("bonita,", 2.44, 3.40, "LR", size=104)
cap("útil", 3.40, 4.04, "LL", size=104)
stack("LC", [("e com ótimo", 60, 4.04), ("custo-benefício?", 104, 4.84)], 6.00)
# ---------------- olha esse kit (6.033 - 7.733): name card under the chin ----------------
a = A["olha esse kit"]
stack((90, a["chin_p90"] + 150, "left"), [("olha esse", 60, 6.13), ("kit de lavabo", 112, 6.75)], 7.70)
# ---------------- ele vem (7.733 - 12.833) orange rug close-up ----------------
cap("ele vem com um", 7.77, 8.58, "TL")
# "tapete" stays up until she finishes the size; the size builds underneath in a smaller
# size, part by part as it is spoken (65 cm = 0,65 m; 40 cm = 0,40 m)
ev("stack", "C", [("tapete", 150, 8.58), ("", 78, 10.31)], 12.80)
EV[-1]["lines"][1]["parts"] = [dict(text="0,65", t=10.31), dict(text=" x 0,40 m", t=12.13)]
cap("que tem a medida de", 9.43, 10.31, "BR")
# ---------------- toalhinha (12.833 - 14.867) cream towel ----------------
# both lines ride the orange stripe of the towel (darkest band, y~990-1150)
cap("e uma toalhinha", 12.98, 13.92, (90, 1068, "left"), size=100)
stack((930, 1060, "right"), [("de rosto", 84, 13.92), ("ou de mão", 84, 14.34)], 14.84)
# ---------------- capricho (14.867 - 18.7) ----------------
cap("e olha só", 14.92, 15.60, "LL")
stack("TL", [("o capricho", 120, 15.60), ("no acabamento", 64, 16.40), ("artesanal", 120, 17.14)], 17.82)
cap("dessas peças.", 17.82, 18.68, "BL", size=76)
# ---------------- aqui na segredos (18.7 - 20.433) ----------------
stack("BR", [("aqui na", 60, 18.74), ("segredos de minas", 100, 19.28)], 20.40)
# ---------------- temos várias (20.433 - 25.767) ----------------
cap("temos várias", 20.43, 21.17, "TL")
stack("TR", [("opções de", 60, 21.17), ("cores", 156, 21.79)], 22.47)
cap("para você escolher", 22.47, 23.69, "BR")
cap("a que mais", 23.69, 24.29, "LC")
cap("combina", 24.29, 24.79, "BL", size=112)
cap("com o ambiente", 24.79, 25.76, "TL")
# ---------------- com a pessoa (25.767 - 27.933) ----------------
cap("ou com a pessoa", 25.80, 26.44, "LR")
cap("que vai receber", 26.44, 27.22, "TL")
cap("esse presente.", 27.22, 27.92, "BL", size=80)
# ---------------- nós enviamos (27.933 - 30.933) ----------------
cap("nós enviamos", 27.93, 28.71, "BC")
stack("BR", [("para todo o", 60, 28.71), ("brasil", 156, 28.99)], 29.51)
stack("BL", [("com frete", 60, 29.51), ("acessível", 124, 30.07)], 30.90)
# ---------------- CTA (30.933 - 36.167) ----------------
stack("BC", [("clique no", 60, 30.95), ("link abaixo", 124, 31.36)], 32.24)
cap("conheça todas", 32.26, 33.10, "BL")
stack("BR", [("as cores", 60, 33.10), ("disponíveis", 116, 33.66)], 34.70)
stack("BC", [("e já garanta", 64, 34.70), ("o seu", 168, 35.50)], DUR + 1)

json.dump(EV, open(os.path.join(V, "work/events.json"), "w"), ensure_ascii=False, indent=1)

HTML = r"""<!doctype html>
<html lang="pt-BR" data-resolution="portrait">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1080, height=1920" />
<script src="assets/js/gsap.min.js"></script>
<style>
@font-face { font-family: "Coolvetica"; src: url("assets/fonts/Coolvetica-Rg.otf") format("opentype"); font-display: block; }
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body { width: 1080px; height: 1920px; overflow: hidden; background: transparent; }
#root { position: relative; width: 1080px; height: 1920px; font-family: "Coolvetica", sans-serif; color: #fff;
        font-feature-settings: "liga" 1, "kern" 1; -webkit-font-smoothing: antialiased; }
.ev { position: absolute; top: 0; opacity: 0; white-space: nowrap; }
.line { display: block; white-space: nowrap; line-height: 0.86; letter-spacing: -0.012em; }
.ch { display: inline-block; will-change: transform, opacity, filter; }
.sp { display: inline-block; }
</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="__DUR__" data-width="1080" data-height="1920"></div>
<script>
const EV = __EVENTS__;
const root = document.getElementById("root");
const tl = gsap.timeline({ paused: true });
function glyphs(text) {               // keep Coolvetica's "qu" ligature intact
  const out = []; let i = 0;
  while (i < text.length) {
    if (text.slice(i, i + 2).toLowerCase() === "qu") { out.push(text.slice(i, i + 2)); i += 2; continue; }
    out.push(text[i]); i += 1;
  }
  return out;
}
function buildLine(L, align) {
  const el = document.createElement("div");
  el.className = "line"; el.style.fontSize = L.size + "px"; el.style.textAlign = align;
  const parts = L.parts || [{ text: L.text, t: L.t }];
  parts.forEach((P, pi) => {
    for (const g of glyphs(P.text)) {
      const s = document.createElement("span");
      if (g === " ") { s.className = "sp"; s.innerHTML = "&nbsp;"; } else { s.className = "ch p" + pi; s.textContent = g; }
      el.appendChild(s);
    }
  });
  return el;
}
EV.forEach((e, idx) => {
  const box = document.createElement("div");
  box.className = "ev"; box.id = "ev" + idx;
  const lines = e.lines.map(L => buildLine(L, e.align));
  lines.forEach(l => box.appendChild(l));
  root.appendChild(box);
  if (e.align === "left") { box.style.left = e.x + "px"; box.style.textAlign = "left"; }
  else if (e.align === "right") { box.style.right = (1080 - e.x) + "px"; box.style.textAlign = "right"; }
  else { box.style.left = "0px"; box.style.width = "1080px"; box.style.textAlign = "center"; }
  const h = e.lines.reduce((a, L) => a + L.size * 0.86, 0);
  box.style.top = (e.y - h / 2) + "px";
  // entrance drifts in from the side the text is anchored to
  const dx = e.align === "left" ? -22 : e.align === "right" ? 22 : 0;
  const dy = e.align === "center" ? 14 : 6;
  tl.set(box, { opacity: 1 }, e.t0);
  e.lines.forEach((L, li) => (L.parts || [{ t: L.t }]).forEach((P, pi) => {
    const chars = lines[li].querySelectorAll(L.parts ? ".p" + pi : ".ch");
    const big = L.size >= 110;
    tl.fromTo(chars, { opacity: 0, x: dx, y: dy, filter: big ? "blur(12px)" : "blur(7px)", scale: big ? 0.9 : 1 },
      { opacity: 1, x: 0, y: 0, filter: "blur(0px)", scale: 1, duration: big ? 0.36 : 0.26,
        stagger: big ? 0.028 : 0.013, ease: "power3.out" }, P.t);
  }));
  if (e.t1 < __DUR__) {
    if (e.kind === "cap") tl.to(box, { opacity: 0, filter: "blur(4px)", duration: 0.1, ease: "power1.in" }, e.t1 - 0.06);
    else tl.to(lines, { opacity: 0, filter: "blur(6px)", duration: 0.18, stagger: 0.035, ease: "power1.in" }, e.t1 - 0.18);
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
open(OUT, "w").write(HTML.replace("__EVENTS__", json.dumps(EV, ensure_ascii=False)).replace("__DUR__", f"{DUR:.4f}"))
print("events", len(EV), "duration", DUR)
