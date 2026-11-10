"""Generate the HyperFrames overlay composition (transparent text layer).

All times are OUTPUT-timeline seconds (after cuts). Layout anchors come from the
face track (anchors2.json) so product/price callouts sit just below the chin.
"""
import json, sys, os

S = sys.argv[1]
OUT = sys.argv[2]
A = json.load(open(os.path.join(S, "work/anchors2.json")))
DUR = 1205 / 30

WHITE = "#ffffff"
ORANGE = "#f2920c"   # accent sampled from the reference reel


def clampx(x):
    return max(400, min(680, x))


def seg(label):
    a = A[label]
    return dict(cx=clampx(a["cx"]), chin=a["chin_p90"])


EV = []


def cap(text, t0, t1, label, slot):
    g = seg(label)
    if slot == "chest":
        y = 1122
    else:
        y = g["chin"] + 26 + 34
    EV.append(dict(kind="cap", t0=t0, t1=t1, x=g["cx"], y=y, lines=[dict(text=text, size=58, color=WHITE, t=t0)]))


def stack(lines, t1, label, y_center, x=None):
    g = seg(label)
    EV.append(dict(kind="stack", t0=lines[0][3], t1=t1, x=x or g["cx"], y=y_center,
                   lines=[dict(text=a, size=b, color=c, t=d) for a, b, c, d in lines]))


def name_card(name, t0, t1, label, detail=None, detail_t=None):
    g = seg(label)
    lines = [dict(text=name, size=100, color=WHITE, t=t0)]
    if detail:
        lines.append(dict(text=detail, size=62, color=WHITE, t=detail_t))
    EV.append(dict(kind="name", t0=t0, t1=t1, x=g["cx"], ytop=g["chin"] + 22, lines=lines))


def price_card(name, price, t0, tp, t1, label):
    g = seg(label)
    EV.append(dict(kind="price", t0=t0, t1=t1, x=g["cx"], ytop=g["chin"] + 20,
                   lines=[dict(text=name, size=64, color=WHITE, t=t0),
                          dict(text=price, size=156, color=ORANGE, t=tp, price=True)]))


# ---------------- hook (0 - 4.433) ----------------
stack([("três opções de", 64, WHITE, 0.00), ("presente", 158, WHITE, 1.06), ("de natal", 110, WHITE, 1.42)], 2.40, "hook", 1075)
stack([("por menos de", 64, WHITE, 2.44), ("R$ 22", 176, ORANGE, 3.20)], 4.36, "hook", 1065)
# ---------------- e olha (4.433 - 7.933) ----------------
cap("e olha,", 4.43, 5.02, "e olha", "chest")
cap("são opções", 5.02, 5.74, "e olha", "chest")
cap("que valem", 5.74, 6.50, "e olha", "chest")
cap("a pena", 6.50, 6.90, "e olha", "chest")
cap("vocês conhecerem", 6.90, 7.88, "e olha", "chest")
# ---------------- primeira opção (7.933 - 10.767) ----------------
cap("a primeira opção", 7.94, 8.58, "primeira opcao", "chin")
cap("é esse", 8.58, 8.90, "primeira opcao", "chin")
name_card("jogo americano", 8.90, 10.72, "primeira opcao", detail="7 peças", detail_t=10.08)
# ---------------- ele vem (10.767 - 14.033) ----------------
cap("ele vem", 10.77, 11.14, "ele vem", "chin")
cap("seis americanos", 11.14, 12.46, "ele vem", "chin")
cap("e um caminho", 12.46, 13.18, "ele vem", "chin")
cap("de mesa", 13.18, 13.77, "ele vem", "chin")
cap("por", 13.77, 14.02, "ele vem", "chin")
# ---------------- preço 22 (14.033 - 15.5) ----------------
price_card("jogo americano", "R$ 22,00", 14.04, 14.18, 15.42, "preco 22")
# ---------------- segunda opção (15.5 - 20.6) ----------------
cap("a segunda opção", 15.56, 16.55, "segunda opcao", "chin")
cap("é esse", 16.55, 17.05, "segunda opcao", "chin")
name_card("kit lavabo", 17.05, 18.20, "segunda opcao")
cap("que vem", 18.22, 18.48, "segunda opcao", "chin")
cap("uma toalhinha", 18.48, 19.36, "segunda opcao", "chin")
cap("e um tapetinho", 19.36, 20.58, "segunda opcao", "chin")
# ---------------- preço 17,50 (20.6 - 22.133) ----------------
price_card("kit lavabo", "R$ 17,50", 20.61, 20.80, 22.06, "preco 17,50")
# ---------------- terceira opção (22.133 - 27.633) ----------------
cap("e a terceira", 22.14, 22.84, "terceira opcao", "chin")
cap("opção é esse", 22.84, 24.08, "terceira opcao", "chin")
name_card("kit colher", 24.08, 24.96, "terceira opcao")
cap("que contém", 24.98, 25.50, "terceira opcao", "chin")
cap("um paninho", 25.50, 25.98, "terceira opcao", "chin")
cap("de prato", 25.98, 26.56, "terceira opcao", "chin")
cap("e uma colher", 26.56, 26.98, "terceira opcao", "chin")
cap("de pau,", 26.98, 27.60, "terceira opcao", "chin")
# ---------------- preço 15 (27.633 - 28.7) ----------------
price_card("kit colher", "R$ 15,00", 27.64, 27.82, 28.64, "preco 15")
# ---------------- viu só / dá pra presentear (28.7 - 33.0) ----------------
cap("viu só?", 28.70, 29.40, "viu so", "chest")
cap("dá para", 29.40, 29.82, "da pra presentear", "chest")
cap("presentear", 29.82, 30.58, "da pra presentear", "chest")
cap("com carinho,", 30.58, 31.46, "da pra presentear", "chest")
stack([("sem precisar", 64, WHITE, 31.46), ("gastar muito", 128, WHITE, 32.16)], 32.94, "da pra presentear", 1090)
# ---------------- CTA (33.0 - 40.167) ----------------
cap("então agora", 33.03, 33.56, "cta", "chest")
stack([("clique no", 64, WHITE, 33.56), ("link abaixo", 132, WHITE, 34.26)], 35.14, "cta", 1090)
cap("confira todas", 35.18, 36.05, "cta", "chest")
cap("as opções", 36.05, 36.72, "cta", "chest")
cap("de cores", 36.72, 37.15, "cta", "chest")
cap("que nós temos", 37.15, 37.92, "cta", "chest")
cap("para você", 37.92, 38.30, "cta", "chest")
stack([("presentear", 88, WHITE, 38.30), ("nesse natal", 140, ORANGE, 39.12)], DUR + 1, "cta", 1080)

json.dump(EV, open(os.path.join(S, "work/events.json"), "w"), ensure_ascii=False, indent=1)

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
#root { position: relative; width: 1080px; height: 1920px; font-family: "Coolvetica", sans-serif;
        font-feature-settings: "liga" 1, "kern" 1; -webkit-font-smoothing: antialiased; }
.ev { position: absolute; left: 0; top: 0; width: 1080px; opacity: 0; }
.line { display: block; white-space: nowrap; text-align: center; line-height: 0.86; letter-spacing: -0.012em; }
.ch { display: inline-block; will-change: transform, opacity, filter; }
.sp { display: inline-block; }
.cur { font-size: 0.5em; vertical-align: 0.62em; margin-right: 0.14em; letter-spacing: 0; }
.pl { margin-top: 8px; }
</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="__DUR__" data-width="1080" data-height="1920"></div>
<script>
const EV = __EVENTS__;
const root = document.getElementById("root");
const tl = gsap.timeline({ paused: true });

// split text into animatable glyph groups; keep the "qu" ligature of Coolvetica intact
function glyphs(text) {
  const out = []; let i = 0;
  while (i < text.length) {
    const two = text.slice(i, i + 2).toLowerCase();
    if (two === "qu") { out.push(text.slice(i, i + 2)); i += 2; continue; }
    out.push(text[i]); i += 1;
  }
  return out;
}
function buildLine(L) {
  const el = document.createElement("div");
  el.className = L.price ? "line pl" : "line";
  el.style.fontSize = L.size + "px";
  el.style.color = L.color;
  let text = L.text;
  if (L.price) {
    const cur = document.createElement("span");
    cur.className = "ch cur"; cur.textContent = "R$";
    el.appendChild(cur);
    text = text.replace("R$ ", "");
  }
  for (const g of glyphs(text)) {
    const s = document.createElement("span");
    if (g === " ") { s.className = "sp"; s.innerHTML = "&nbsp;"; }
    else { s.className = "ch"; s.textContent = g; }
    el.appendChild(s);
  }
  return el;
}

EV.forEach((e, idx) => {
  const box = document.createElement("div");
  box.className = "ev"; box.id = "ev" + idx;
  const lines = e.lines.map(buildLine);
  lines.forEach(l => box.appendChild(l));
  root.appendChild(box);
  // horizontal centring on the anchor x
  box.style.width = "1080px";
  box.style.left = (e.x - 540) + "px";
  // vertical placement: caps/stacks centred on y; cards hang from ytop
  const h = e.lines.reduce((a, L) => a + L.size * 0.86, 0);
  const top = (e.ytop !== undefined) ? e.ytop : (e.y - h / 2);
  box.style.top = top + "px";

  tl.set(box, { opacity: 1 }, e.t0);
  // ---- entrances ----
  e.lines.forEach((L, li) => {
    const chars = lines[li].querySelectorAll(".ch");
    if (e.kind === "cap") {
      tl.fromTo(chars, { opacity: 0, y: 9, filter: "blur(6px)" },
        { opacity: 1, y: 0, filter: "blur(0px)", duration: 0.24, stagger: 0.012, ease: "power2.out" }, L.t);
    } else if (L.price) {
      tl.fromTo(chars, { opacity: 0, y: 28, scale: 0.82, filter: "blur(12px)" },
        { opacity: 1, y: 0, scale: 1, filter: "blur(0px)", duration: 0.38, stagger: 0.032, ease: "power3.out" }, L.t);
    } else if (e.kind === "stack" && L.color !== "#ffffff") {
      tl.fromTo(chars, { opacity: 0, x: -10, filter: "blur(10px)" },
        { opacity: 1, x: 0, filter: "blur(0px)", duration: 0.34, stagger: 0.028, ease: "power3.out" }, L.t);
    } else if (e.kind === "name" && li === 0) {
      tl.fromTo(chars, { opacity: 0, y: 14, filter: "blur(8px)" },
        { opacity: 1, y: 0, filter: "blur(0px)", duration: 0.3, stagger: 0.016, ease: "power3.out" }, L.t);
    } else {
      tl.fromTo(lines[li], { opacity: 0, y: 22, scale: 0.97, filter: "blur(10px)" },
        { opacity: 1, y: 0, scale: 1, filter: "blur(0px)", duration: 0.34, ease: "power3.out" }, L.t);
    }
  });
  // ---- exits ----
  if (e.t1 < __DUR__) {
    if (e.kind === "cap") {
      tl.to(box, { opacity: 0, filter: "blur(3px)", duration: 0.1, ease: "power1.in" }, e.t1 - 0.06);
    } else {
      tl.to(lines, { opacity: 0, filter: "blur(6px)", duration: 0.2, stagger: 0.04, ease: "power1.in" }, e.t1 - 0.2);
    }
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
html = HTML.replace("__EVENTS__", json.dumps(EV, ensure_ascii=False)).replace("__DUR__", f"{DUR:.4f}")
open(OUT, "w").write(html)
print("events", len(EV), "duration", DUR)
