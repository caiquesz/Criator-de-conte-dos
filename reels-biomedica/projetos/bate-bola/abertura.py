"""Abertura do Bate-bola, no modelo do bate-bola da doutora que a cliente mandou: gera
compositions/abertura.html e os sons dela (abertura-sons.json, que o montar_plano.py junta no plano).

Uso: python3 abertura.py   (na pasta do projeto; depois rode o montar_plano.py e o gerar.py)

Como no modelo, quadro a quadro:
- um cursor de mouse em pixel (a mãozinha branca) sobe e clica nela duas vezes; cada clique fecha o
  plano (os cortes do 4K estão nos "enquadramentos", em 0,43 e 0,77 s) com um tranco de câmera;
- no segundo clique a imagem esquenta, ganha grão, explodem estrelas douradas que ficam girando e
  entra a música da abertura;
- o título é digitado: a estrelinha rosa, "Bate Bola com" (Poppins creme) e o nome à mão (Pinyon
  Script rosado), letra por letra;
- na pausa de 1,6 s depois do título a câmera dá trancos de zoom (no plano.json) e as estrelas
  continuam; no fim, as barras coloridas de TV com o bipe e o corte para a primeira pergunta.
"""

import json
import random
from pathlib import Path

AQUI = Path(__file__).parent
CLIQUE1, CLIQUE2 = 0.4333, 0.7667
BARRAS, FIM = 4.40, 4.5333          # as barras ficam 4 quadros, até o corte da primeira pergunta
TITULO1, TITULO2 = "Bate Bola com", "Dra Nádia Rezende"


def n(x):
    return f"{x:.3f}".rstrip("0").rstrip(".")


# ── o cursor: a mãozinha clássica em pixel (B = contorno preto, W = branco), cada pixel com 6 px ──
MAO = """\
.....BB..........
....BWWB.........
....BWWB.........
....BWWB.........
....BWWB.........
....BWWBBB.......
....BWWBWWBBB....
....BWWBWWBWWBB..
BBB.BWWBWWBWWBWB.
BWWBBWWWWWWWWBWWB
BWWWBWWWWWWWWWWWB
.BWWWWWWWWWWWWWWB
..BWWWWWWWWWWWWWB
..BWWWWWWWWWWWWWB
...BWWWWWWWWWWWWB
...BWWWWWWWWWWWB.
....BWWWWWWWWWWB.
....BWWWWWWWWWB..
.....BWWWWWWWWB..
.....BWWWWWWWWB..
.....BBBBBBBBBB.."""
PX = 6
rects = []
for y, linha in enumerate(MAO.splitlines()):
    for x, c in enumerate(linha):
        if c in "BW":
            rects.append(f'<rect x="{x}" y="{y}" width="1" height="1" fill="{"#111" if c == "B" else "#FFF"}"/>')
largura_mao, altura_mao = 17, len(MAO.splitlines())
cursor = (f'<svg id="cur" class="cursor" viewBox="0 0 {largura_mao} {altura_mao}" width="{largura_mao * PX}" height="{altura_mao * PX}" '
          f'shape-rendering="crispEdges">{"".join(rects)}</svg>')
PONTA = (5.5 * PX, 0.5 * PX)        # a ponta do dedo, que é onde o clique acontece


def em(x, y):
    """Posição do canto do cursor para a ponta do dedo ficar em (x, y)."""
    return x - PONTA[0], y - PONTA[1]


# ── estrelas douradas: estouram do meio no segundo clique e ficam girando até as barras ──────────
rnd = random.Random(23)
CORES = [("#F7D57A", "#D59A34", "#7A4A12"), ("#F2C35A", "#B9782A", "#6B3E10"), ("#E9A94F", "#9C5F22", "#5C3410")]
estrela = "M0,-50 L14.7,-20.2 L47.6,-15.5 L23.8,7.7 L29.4,40.5 L0,25 L-29.4,40.5 L-23.8,7.7 L-47.6,-15.5 L-14.7,-20.2 Z"
grads, stars, js_estrelas = [], [], []
for k, (c1, c2, borda) in enumerate(CORES):
    grads.append(f'<radialGradient id="g{k}" cx="40%" cy="35%" r="70%"><stop offset="0" stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/></radialGradient>')
for k in range(20):
    tam = rnd.choice([56, 64, 72, 84, 96, 110, 124])
    ang = rnd.uniform(0, 6.283)
    import math
    dist = rnd.uniform(260, 760)
    tx, ty = 540 + math.cos(ang) * dist * 0.95, 900 + math.sin(ang) * dist * 1.35
    tx, ty = min(max(tx, 30), 1050), min(max(ty, 60), 1860)
    cor = k % len(CORES)
    desf = ' style="filter:blur(1.6px)"' if k % 5 == 0 else ""
    stars.append(f'<svg id="st{k}" class="estrela" viewBox="-56 -56 112 112" width="{tam}" height="{tam}"{desf}>'
                 f'<path d="{estrela}" fill="url(#g{cor})" stroke="{CORES[cor][2]}" stroke-width="5" stroke-linejoin="round"/></svg>')
    r0, r1 = rnd.uniform(-200, 200), rnd.uniform(-60, 60)
    deriva = (rnd.uniform(-90, 90), rnd.uniform(-140, 40))
    js_estrelas += [
        f'tl.fromTo("#st{k}", {{x:{540 - tam / 2:.0f}, y:{900 - tam / 2:.0f}, scale:0.2, rotation:{r0:.0f}, opacity:0}}, '
        f'{{x:{tx - tam / 2:.0f}, y:{ty - tam / 2:.0f}, scale:1, rotation:{r1:.0f}, opacity:1, duration:{rnd.uniform(0.55, 0.8):.2f}, ease:"expo.out"}}, {n(CLIQUE2 + rnd.uniform(0, 0.12))});',
        f'tl.to("#st{k}", {{x:"+={deriva[0]:.0f}", y:"+={deriva[1]:.0f}", rotation:"+={rnd.choice([-1, 1]) * rnd.uniform(90, 260):.0f}", '
        f'duration:{BARRAS - CLIQUE2 - 0.9:.2f}, ease:"sine.inOut"}}, {n(CLIQUE2 + 0.9)});',
    ]

# ── título digitado ────────────────────────────────────────────────────────────────────────────
t1 = "".join(f'<span class="ch" id="a{k}">{"&nbsp;" if c == " " else c}</span>' for k, c in enumerate(TITULO1))
t2 = "".join(f'<span class="ch" id="b{k}">{"&nbsp;" if c == " " else c}</span>' for k, c in enumerate(TITULO2))
estrela_rosa = (f'<svg id="rosa" class="rosa" viewBox="-56 -56 112 112" width="58" height="58"><path d="{estrela}" fill="#F7B3CF" '
                f'stroke="#5A2440" stroke-width="7" stroke-linejoin="round"/></svg>')
T1, T2 = 1.0, 1.75
js_titulo = [f'tl.fromTo("#rosa", {{scale:0, rotation:-40}}, {{scale:1, rotation:0, duration:0.35, ease:"back.out(2.4)"}}, {n(T1 - 0.08)});']
js_titulo += [f'tl.set("#a{k}", {{opacity:1}}, {n(T1 + 0.05 * k)});' for k in range(len(TITULO1))]
js_titulo += [f'tl.fromTo("#b{k}", {{opacity:0, y:6}}, {{opacity:1, y:0, duration:0.09, ease:"power1.out"}}, {n(T2 + 0.055 * k)});'
              for k in range(len(TITULO2))]

# ── barras de TV ───────────────────────────────────────────────────────────────────────────────
cima = ["#C0C0C0", "#C0C000", "#00C0C0", "#00C000", "#C000C0", "#C00000", "#0000C0"]
meio = ["#0000C0", "#131313", "#C000C0", "#131313", "#00C0C0", "#131313", "#C0C0C0"]
baixo = [("#00214C", 1.25), ("#FFFFFF", 1.25), ("#32006A", 1.25), ("#131313", 1.25), ("#090909", 0.33), ("#131313", 0.33), ("#1D1D1D", 0.34), ("#131313", 1)]
w7 = 1080 / 7
barras = "".join(f'<rect x="{k * w7:.1f}" y="0" width="{w7 + 0.5:.1f}" height="1290" fill="{c}"/>' for k, c in enumerate(cima))
barras += "".join(f'<rect x="{k * w7:.1f}" y="1290" width="{w7 + 0.5:.1f}" height="150" fill="{c}"/>' for k, c in enumerate(meio))
x = 0.0
for c, frac in baixo:
    barras += f'<rect x="{x:.1f}" y="1440" width="{frac * w7 + 0.5:.1f}" height="480" fill="{c}"/>'
    x += frac * w7

html = f"""<div id="ab">
      <div class="quente" id="quente"></div>
      <div class="grao" id="grao"></div>
      <svg width="0" height="0" style="position:absolute"><defs>{"".join(grads)}</defs></svg>
      {"".join(stars)}
      <div class="titulo" id="tit">
        <div class="l1">{estrela_rosa}<span class="t1">{t1}</span></div>
        <div class="l2">{t2}</div>
      </div>
      {cursor}
      <svg id="barras" class="barras" viewBox="0 0 1080 1920" width="1080" height="1920" shape-rendering="crispEdges">{barras}</svg>
    </div>"""

x0, y0 = em(930, 1820)
x1, y1 = em(600, 1160)
x2, y2 = em(560, 830)
x3, y3 = em(1000, 1540)
js = [
    'tl.set("#ab", {opacity:1}, 0);',
    f'tl.set("#ab", {{opacity:0}}, {n(FIM)});',
    # o cursor sobe, clica no corpo dela, sobe para o rosto, clica de novo e sai
    f'tl.fromTo("#cur", {{x:{x0:.0f}, y:{y0:.0f}, opacity:0}}, {{x:{x1:.0f}, y:{y1:.0f}, opacity:1, duration:0.33, ease:"power2.out"}}, 0.05);',
    f'tl.to("#cur", {{scale:0.84, duration:0.05, ease:"power1.in", transformOrigin:"32% 3%"}}, {n(CLIQUE1 - 0.05)});',
    f'tl.to("#cur", {{scale:1, duration:0.08, ease:"power1.out"}}, {n(CLIQUE1)});',
    f'tl.to("#cur", {{x:{x2:.0f}, y:{y2:.0f}, duration:0.22, ease:"power2.inOut"}}, {n(CLIQUE1 + 0.1)});',
    f'tl.to("#cur", {{scale:0.84, duration:0.05, ease:"power1.in"}}, {n(CLIQUE2 - 0.05)});',
    f'tl.to("#cur", {{scale:1, duration:0.08, ease:"power1.out"}}, {n(CLIQUE2)});',
    f'tl.to("#cur", {{x:{x3:.0f}, y:{y3:.0f}, opacity:0, duration:0.28, ease:"power2.in"}}, {n(CLIQUE2 + 0.12)});',
    # a imagem esquenta e ganha grão no segundo clique
    f'tl.fromTo(["#quente", "#grao"], {{opacity:0}}, {{opacity:1, duration:0.12, ease:"none"}}, {n(CLIQUE2)});',
    # o grão pula de lugar a cada quadro (filme)
    *[f'tl.set("#grao", {{x:{rnd.randint(-60, 0)}, y:{rnd.randint(-60, 0)}}}, {n(CLIQUE2 + k / 30)});'
      for k in range(0, int((BARRAS - CLIQUE2) * 30), 2)],
    *js_estrelas,
    *js_titulo,
    # barras de TV: entram secas, 4 quadros, e o vídeo corta para a primeira pergunta
    f'tl.set("#barras", {{opacity:1}}, {n(BARRAS)});',
]

FONTES = ('@font-face { font-family: "Poppins Reels"; font-weight: 600; font-style: normal; src: url("assets/fonts/Poppins-600.ttf"); }\n'
          '@font-face { font-family: "Pinyon Script"; font-weight: 400; font-style: normal; src: url("assets/fonts/PinyonScript-Regular.ttf"); }\n')
# grão de filme: ruído fractal em SVG, repetido, por cima da imagem
GRAO = ("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='300' height='300'><filter id='f'>"
        "<feTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/><feColorMatrix type='saturate' values='0'/></filter>"
        "<rect width='300' height='300' filter='url(%23f)' opacity='0.55'/></svg>")
saida = f"""<template>
  <style>
{FONTES}
    #root {{ position: absolute; inset: 0; overflow: hidden; }}
    #ab {{ position: absolute; inset: 0; opacity: 0; }}
    .quente {{ position: absolute; inset: 0; opacity: 0;
      background: radial-gradient(ellipse 80% 70% at 50% 45%, rgba(255, 196, 140, 0.10) 0%, rgba(110, 60, 20, 0.30) 100%);
      mix-blend-mode: multiply; }}
    .grao {{ position: absolute; left: 0; top: 0; width: 1200px; height: 2040px; opacity: 0; mix-blend-mode: overlay;
             background-image: url("{GRAO}"); background-size: 300px 300px; }}
    .estrela {{ position: absolute; left: 0; top: 0; opacity: 0; filter: drop-shadow(0 3px 6px rgba(60, 30, 5, 0.35)); }}
    .titulo {{ position: absolute; left: 0; top: 840px; width: 1080px; text-align: center;
               text-shadow: 0 2px 4px rgba(40, 20, 10, 0.35), 0 6px 22px rgba(40, 20, 10, 0.35); }}
    .l1 {{ font-family: "Poppins Reels"; font-weight: 600; font-size: 80px; letter-spacing: -0.035em; line-height: 1; color: #FBF2CF;
           display: inline-flex; align-items: center; gap: 14px; }}
    .rosa {{ flex: none; filter: drop-shadow(0 2px 4px rgba(40, 20, 10, 0.35)); }}
    .l2 {{ font-family: "Pinyon Script"; font-size: 128px; line-height: 1; color: #FFEAF1; margin-top: -8px;
           -webkit-text-stroke: 0.8px #FFEAF1;
           text-shadow: 0 2px 3px rgba(40, 18, 10, 0.55), 0 4px 18px rgba(40, 18, 10, 0.45), 0 0 26px rgba(255, 205, 222, 0.4); }}
    .ch {{ opacity: 0; display: inline-block; }}
    .cursor {{ position: absolute; left: 0; top: 0; opacity: 0; filter: drop-shadow(2px 3px 0 rgba(0, 0, 0, 0.25)); }}
    .barras {{ position: absolute; left: 0; top: 0; opacity: 0; }}
  </style>
  <div id="root" data-composition-id="abertura" data-width="1080" data-height="1920">
    {html}
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
    tl.to({{}}, {{ duration: 69.1 }}, 0);
    {(chr(10) + "    ").join(js)}
    window.__timelines["abertura"] = tl;
  </script>
</template>
"""
sons = [
    {"t": CLIQUE1, "som": "click", "vol": 0.6},
    {"t": CLIQUE2, "som": "click", "vol": 0.6},
    {"t": CLIQUE2 + 0.01, "som": "musica-abertura", "vol": 0.85},
    {"t": round(CLIQUE2 + 0.03, 3), "som": "brilho", "vol": 0.4},
    {"t": round(T1 - 0.06, 3), "som": "pop", "vol": 0.3},
    {"t": BARRAS, "som": "bipe", "vol": 0.5},
]
(AQUI / "compositions").mkdir(exist_ok=True)
(AQUI / "compositions" / "abertura.html").write_text(saida)
(AQUI / "abertura-sons.json").write_text(json.dumps(sons, ensure_ascii=False, indent=1))
print(f"ok: compositions/abertura.html (0–{n(FIM)} s), {len(sons)} sons")
