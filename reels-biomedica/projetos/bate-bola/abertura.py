"""Abertura do Bate-bola, no modelo do bate-bola da doutora: gera compositions/abertura.html e os sons
dela (abertura-sons.json, que o montar_plano.py junta no plano).

Uso: python3 broll.py; python3 abertura.py   (na pasta do projeto; depois montar_plano.py e gerar.py)

Como no modelo (conferido quadro a quadro e com a transcrição dele):
- primeiro ela diz o título ("Bate bola com doutora Nádia Resende", 0 a 2,93 s) no vídeo normal, sem
  nada por cima: a abertura só vem depois da fala (na primeira versão as estrelas entravam no meio);
- no fim da fala o cursor em pixel (a mãozinha branca) sobe e clica nela uma vez, e no clique entra
  tudo junto: trechos dela falando, mais de perto (broll.py, olhos abertos; na pausa a imagem parada
  pegou ela de olho fechado), as estrelas, a música e a imagem quente com grão;
- as estrelas são como as do modelo: chapadas, sem contorno nem brilho, amarelo-ouro e algumas
  caramelo, poucas e espalhadas, girando e flutuando devagar;
- "★ Bate Bola com" digitado (Poppins creme, estrelinha rosa com contorno), o nome à mão em Pinyon
  Script, letra por letra, com o traço embaixo do "Dra"; imagem quente com grão; troca de trecho com
  tranco de zoom; barras coloridas de TV com bipe e corte para a primeira pergunta.
"""

import json
import math
import random
import subprocess
from pathlib import Path

AQUI = Path(__file__).parent
_plano = json.loads((AQUI / "plano.json").read_text())
FALA_FIM = _plano["pausas"][0]["em"]    # a pausa da abertura (montar_plano.py), num silêncio depois do título
CLIQUE = FALA_FIM                     # um clique só: no clique entra a abertura inteira (estrelas, trecho de perto, música)
TROCA_ZOOM = 4 / 30                   # a transição de zoom: 4 quadros mergulhando no quadro dela, e o trecho de perto chega

FIM = round(FALA_FIM + _plano["pausas"][0]["dur"], 4)   # fim da pausa: a primeira pergunta
BARRAS = round(FIM - 4 / 30, 4)       # as barras ficam 4 quadros
TROCAS = [round(CLIQUE + 1.9, 4), round(CLIQUE + 3.1, 4)]   # os trechos do broll.py: 1,9 + 1,2 + 1,1667 s
TITULO1, TITULO2 = "Bate Bola com", "Dra Nádia Resende"
AMARELO, CARAMELO = "#DCAB55", "#7C4D27"   # medidos nas estrelas do modelo


def n(x):
    return f"{x:.3f}".rstrip("0").rstrip(".")


# ── cursor: a mãozinha clássica em pixel (B = contorno preto, W = branco) ───────────────────────────
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
PX = 8                                # no modelo o cursor é grande (uns 140 px de largura)
rects = [f'<rect x="{x}" y="{y}" width="1" height="1" fill="{"#111" if c == "B" else "#FFF"}"/>'
         for y, linha in enumerate(MAO.splitlines()) for x, c in enumerate(linha) if c in "BW"]
cursor = (f'<svg id="cur" class="cursor" viewBox="0 0 17 {len(MAO.splitlines())}" width="{17 * PX}" '
          f'height="{len(MAO.splitlines()) * PX}" shape-rendering="crispEdges">{"".join(rects)}</svg>')
em = lambda x, y: (x - 5.5 * PX, y - 0.5 * PX)     # canto do cursor para a ponta do dedo cair em (x, y)

# ── estrelas chapadas ─────────────────────────────────────────────────────────────────────────────
ESTRELA = "M0,-50 L14.7,-20.2 L47.6,-15.5 L23.8,7.7 L29.4,40.5 L0,25 L-29.4,40.5 L-23.8,7.7 L-47.6,-15.5 L-14.7,-20.2 Z"
rnd = random.Random(8)
# lugares espalhados como no modelo: alto, laterais e baixo, longe do título (y 900–1160)
LUGARES = [(130, 210), (820, 150), (540, 90), (980, 470), (90, 640), (300, 380), (760, 560),
           (60, 1290), (1010, 1210), (250, 1520), (840, 1460), (560, 1760), (990, 1830), (120, 1840)]
stars, js_estrelas = [], []
for k, (x, y) in enumerate(LUGARES):
    tam = rnd.choice([62, 70, 78, 88, 100, 112])
    cor = CARAMELO if k in (2, 8, 11) else AMARELO
    desf = ' style="filter:blur(2.2px)"' if k in (4, 12) else ""
    # contorno da mesma cor e cantos redondos: as pontas ficam levemente arredondadas, como recortadas
    stars.append(f'<svg id="st{k}" class="estrela" viewBox="-58 -58 116 116" width="{tam}" height="{tam}"{desf}>'
                 f'<path d="{ESTRELA}" fill="{cor}" stroke="{cor}" stroke-width="7" stroke-linejoin="round"/></svg>')
    rot = rnd.uniform(-35, 35)
    t_in = CLIQUE + TROCA_ZOOM + 0.012 * k   # todas estouram logo depois do clique, quase juntas, quando o trecho de perto chega
    js_estrelas += [
        f'tl.fromTo("#st{k}", {{x:{x - tam / 2:.0f}, y:{y - tam / 2:.0f}, scale:0, rotation:{rot - 40:.0f}, opacity:1}}, '
        f'{{scale:1, rotation:{rot:.0f}, duration:0.22, ease:"back.out(2.2)"}}, {n(t_in)});',
        # deriva em valores absolutos (relativos "+=" pegam a base errada quando o tween anterior ainda corre)
        f'tl.to("#st{k}", {{x:{x - tam / 2 + rnd.uniform(-45, 45):.0f}, y:{y - tam / 2 + rnd.uniform(-60, 30):.0f}, '
        f'rotation:{rot + rnd.choice([-1, 1]) * rnd.uniform(25, 70):.0f}, duration:{BARRAS - t_in - 0.23:.2f}, ease:"sine.inOut"}}, {n(t_in + 0.23)});',
    ]

# ── título ────────────────────────────────────────────────────────────────────────────────────────
esp = lambda c: "&nbsp;" if c == " " else c
t1 = "".join(f'<span class="ch" id="a{k}">{esp(c)}</span>' for k, c in enumerate(TITULO1))
t2 = "".join(f'<span class="ch" id="b{k}">{esp(c)}</span>' for k, c in enumerate(TITULO2))
rosa = (f'<svg id="rosa" class="rosa" viewBox="-60 -60 120 120" width="56" height="56"><path d="{ESTRELA}" fill="#F4B6D2" '
        f'stroke="#9E5577" stroke-width="6" stroke-linejoin="round"/></svg>')
traco = ('<svg id="traco" class="traco" viewBox="0 0 240 40" width="240" height="40"><path id="traco-p" '
         'd="M4,30 C60,12 130,10 236,16 M36,36 C90,24 150,22 200,26" fill="none" stroke="#FBE3EC" stroke-width="3.2" '
         'stroke-linecap="round" pathLength="100" stroke-dasharray="100" stroke-dashoffset="100"/></svg>')
T1, T2 = round(CLIQUE + 0.37, 4), round(CLIQUE + 1.17, 4)
js_titulo = [f'tl.fromTo("#rosa", {{scale:0, rotation:-50}}, {{scale:1, rotation:-12, duration:0.32, ease:"back.out(2.4)"}}, {n(T1 - 0.07)});']
js_titulo += [f'tl.set("#a{k}", {{opacity:1}}, {n(T1 + 0.05 * k)});' for k in range(len(TITULO1))]
js_titulo += [f'tl.fromTo("#b{k}", {{opacity:0}}, {{opacity:1, duration:0.07, ease:"none"}}, {n(T2 + 0.065 * k)});' for k in range(len(TITULO2))]
fim_nome = T2 + 0.065 * len(TITULO2)
js_titulo.append(f'tl.to("#traco-p", {{strokeDashoffset:0, duration:0.32, ease:"power2.out"}}, {n(fim_nome)});')

# ── barras de TV ─────────────────────────────────────────────────────────────────────────────────
cima = ["#C0C0C0", "#C0C000", "#00C0C0", "#00C000", "#C000C0", "#C00000", "#0000C0"]
meio = ["#0000C0", "#131313", "#C000C0", "#131313", "#00C0C0", "#131313", "#C0C0C0"]
baixo = [("#00214C", 1.25), ("#FFFFFF", 1.25), ("#32006A", 1.25), ("#131313", 1.25), ("#090909", 0.33), ("#131313", 0.33), ("#1D1D1D", 0.34), ("#131313", 1)]
w7 = 1080 / 7
barras = "".join(f'<rect x="{k * w7:.1f}" y="0" width="{w7 + 0.5:.1f}" height="1290" fill="{c}"/>' for k, c in enumerate(cima))
barras += "".join(f'<rect x="{k * w7:.1f}" y="1290" width="{w7 + 0.5:.1f}" height="150" fill="{c}"/>' for k, c in enumerate(meio))
xb = 0.0
for c, frac in baixo:
    barras += f'<rect x="{xb:.1f}" y="1440" width="{frac * w7 + 0.5:.1f}" height="480" fill="{c}"/>'
    xb += frac * w7

html = f"""<div id="ab">
      <div class="broll" id="broll"><div class="balanco" id="bal"><div class="zoom" id="zoom">
        <video id="br" class="clip" src="assets/video/broll.mp4" data-start="{n(CLIQUE)}" data-duration="{n(BARRAS - CLIQUE)}"
          data-media-start="0" muted playsinline></video></div></div>
        <div class="quente"></div><div class="grao" id="grao"></div>
      </div>
      <img id="congela" class="congela" src="assets/video/abertura-quadro.jpg" alt="">
      {"".join(stars)}
      <div class="titulo" id="tit">
        <div class="l1">{rosa}<span class="t1">{t1}</span></div>
        <div class="l2">{t2}{traco}</div>
      </div>
      {cursor}
      <svg id="barras" class="barras" viewBox="0 0 1080 1920" width="1080" height="1920" shape-rendering="crispEdges">{barras}</svg>
    </div>"""

x0, y0 = em(960, 1880)
x1, y1 = em(600, 1180)                # o peito dela no vídeo normal
js = [
    'tl.set("#ab", {opacity:1}, 0);',
    f'tl.set("#ab", {{opacity:0}}, {n(FIM)});',
    # transição de zoom no clique: o quadro dela (o mesmo que fica parado na pausa) mergulha num zoom com
    # desfoque e o trecho de perto chega saindo desse zoom, focando (no esmaecer simples ficava imagem dupla)
    'tl.set("#congela", {opacity:0}, 0);',
    f'tl.set("#congela", {{opacity:1}}, {n(CLIQUE)});',
    # (a troca é seca no auge do desfoque, 4 quadros depois do clique: as duas nunca aparecem juntas)
    f'tl.fromTo("#congela", {{scale:1, filter:"blur(0px)"}}, {{scale:1.45, filter:"blur(16px)", duration:{TROCA_ZOOM:.4f}, ease:"power2.in"}}, {n(CLIQUE)});',
    f'tl.set("#congela", {{opacity:0}}, {n(CLIQUE + TROCA_ZOOM)});',
    'tl.set("#broll", {opacity:0}, 0);',
    f'tl.set("#broll", {{opacity:1}}, {n(CLIQUE + TROCA_ZOOM)});',
    f'tl.fromTo("#broll", {{filter:"blur(16px)"}}, {{filter:"blur(0px)", duration:0.28, ease:"power2.out"}}, {n(CLIQUE + TROCA_ZOOM)});',
    # cursor: sobe enquanto ela termina o título, clica uma vez e some (a abertura entra no clique;
    # na versão anterior havia dois cliques e o vídeo pulava para o trecho de perto sem nada, o que parecia um erro)
    f'tl.fromTo("#cur", {{x:{x0:.0f}, y:{y0:.0f}, opacity:0}}, {{x:{x1:.0f}, y:{y1:.0f}, opacity:1, duration:0.5, ease:"power2.out"}}, {n(CLIQUE - 0.68)});',
    f'tl.to("#cur", {{scale:0.84, duration:0.05, ease:"power1.in", transformOrigin:"32% 3%"}}, {n(CLIQUE - 0.05)});',
    f'tl.to("#cur", {{scale:1, duration:0.06, ease:"power1.out"}}, {n(CLIQUE)});',
    f'tl.to("#cur", {{opacity:0, duration:0.12, ease:"power1.in"}}, {n(CLIQUE + 0.06)});',
    # trechos de perto: salto de zoom em cada clique e em cada troca, e um empurrão lento dentro de cada um
    f'tl.fromTo("#zoom", {{scale:1.45}}, {{scale:1.14, duration:0.4, ease:"expo.out"}}, {n(CLIQUE + TROCA_ZOOM)});',
    f'tl.to("#zoom", {{scale:1.2, duration:{TROCAS[0] - CLIQUE - 0.5:.2f}, ease:"none"}}, {n(CLIQUE + 0.5)});',
]
for a, b in zip(TROCAS, TROCAS[1:] + [BARRAS]):
    js += [f'tl.fromTo("#zoom", {{scale:1.26}}, {{scale:1.14, duration:0.3, ease:"expo.out", immediateRender:false}}, {n(a)});',
           f'tl.to("#zoom", {{scale:1.21, duration:{b - a - 0.3:.2f}, ease:"none"}}, {n(a + 0.3)});']
# balanço de câmera na mão, devagar
js.append(f'tl.fromTo("#bal", {{x:0, y:0, rotation:0}}, {{keyframes:{{x:[0, 10, -6, 8, -4, 0], y:[0, -8, 6, -4, 8, 0], '
          f'rotation:[0, 0.6, -0.5, 0.4, -0.6, 0]}}, duration:{BARRAS - CLIQUE:.2f}, ease:"none"}}, {n(CLIQUE)});')
# grão pulando a cada dois quadros
js += [f'tl.set("#grao", {{x:{rnd.randint(-60, 0)}, y:{rnd.randint(-60, 0)}}}, {n(CLIQUE + k / 30)});'
       for k in range(0, int((BARRAS - CLIQUE) * 30), 2)]
js += js_estrelas + js_titulo
js.append(f'tl.set("#barras", {{opacity:1}}, {n(BARRAS)});')

GRAO = ("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='300' height='300'><filter id='f'>"
        "<feTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/><feColorMatrix type='saturate' values='0'/></filter>"
        "<rect width='300' height='300' filter='url(%23f)' opacity='0.5'/></svg>")
FONTES = ('@font-face { font-family: "Poppins Reels"; font-weight: 600; font-style: normal; src: url("assets/fonts/Poppins-600.ttf"); }\n'
          '@font-face { font-family: "Pinyon Script"; font-weight: 400; font-style: normal; src: url("assets/fonts/PinyonScript-Regular.ttf"); }\n')
saida = f"""<template>
  <style>
{FONTES}
    #root {{ position: absolute; inset: 0; overflow: hidden; }}
    #ab {{ position: absolute; inset: 0; opacity: 0; }}
    .broll {{ position: absolute; inset: 0; overflow: hidden; background: #2A1E16; }}
    .balanco, .zoom {{ position: absolute; inset: 0; transform-origin: 52% 40%; }}
    .zoom video {{ position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; object-fit: cover;
                   filter: sepia(0.18) saturate(1.05) contrast(1.04) brightness(1.02); }}
    .quente {{ position: absolute; inset: 0; mix-blend-mode: multiply;
      background: radial-gradient(ellipse 80% 70% at 50% 45%, rgba(255, 200, 150, 0.06) 0%, rgba(110, 64, 26, 0.26) 100%); }}
    .grao {{ position: absolute; left: 0; top: 0; width: 1200px; height: 2040px; mix-blend-mode: overlay;
             background-image: url("{GRAO}"); background-size: 300px 300px; }}
    .estrela {{ position: absolute; left: 0; top: 0; opacity: 0; }}
    .congela {{ position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; opacity: 0; transform-origin: 52% 40%; }}
    .titulo {{ position: absolute; left: 0; top: 930px; width: 1080px; text-align: center;
               text-shadow: 0 2px 4px rgba(40, 20, 10, 0.35), 0 6px 22px rgba(40, 20, 10, 0.35); }}
    .l1 {{ font-family: "Poppins Reels"; font-weight: 600; font-size: 80px; letter-spacing: -0.035em; line-height: 1; color: #FDF3CB;
           display: inline-flex; align-items: center; gap: 14px; }}
    .rosa {{ flex: none; }}
    .l2 {{ position: relative; display: inline-block; font-family: "Pinyon Script"; font-size: 128px; line-height: 1; color: #FBE3EC;
           margin-top: -6px; -webkit-text-stroke: 0.6px #FBE3EC;
           text-shadow: 0 2px 3px rgba(40, 18, 10, 0.5), 0 4px 18px rgba(40, 18, 10, 0.4); }}
    .traco {{ position: absolute; left: 10px; top: 128px; filter: drop-shadow(0 2px 3px rgba(40, 18, 10, 0.45)); }}
    .ch {{ opacity: 0; display: inline-block; }}
    .cursor {{ position: absolute; left: 0; top: 0; opacity: 0; filter: drop-shadow(3px 4px 0 rgba(0, 0, 0, 0.22)); }}
    .barras {{ position: absolute; left: 0; top: 0; opacity: 0; }}
  </style>
  <div id="root" data-composition-id="abertura" data-width="1080" data-height="1920">
    {html}
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
    tl.to({{}}, {{ duration: 71.9 }}, 0);
    {(chr(10) + "    ").join(js)}
    window.__timelines["abertura"] = tl;
  </script>
</template>
"""
sons = [
    {"t": CLIQUE, "som": "click", "vol": 0.6},
    # a música já vem subindo do silêncio meio segundo antes (o arquivo começa 0,5 s antes da batida forte,
    # que cai no clique: PICO_SFX do gerar.py), para a fala dela emendar na abertura sem tranco
    {"t": CLIQUE, "som": "musica-abertura", "vol": 0.8},
    {"t": round(T1 - 0.05, 3), "som": "pop", "vol": 0.3},
    {"t": BARRAS, "som": "bipe", "vol": 0.35},
]
# o quadro parado da pausa (o último antes da emenda), para a transição de zoom no clique
subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{FALA_FIM + 0.5:.3f}", "-i", str(AQUI / "assets" / "video" / "video.mp4"),
                "-frames:v", "1", "-q:v", "2", str(AQUI / "assets" / "video" / "abertura-quadro.jpg")], check=True)
(AQUI / "compositions").mkdir(exist_ok=True)
(AQUI / "compositions" / "abertura.html").write_text(saida)
(AQUI / "abertura-sons.json").write_text(json.dumps(sons, ensure_ascii=False, indent=1))
print(f"ok: compositions/abertura.html (cursor {n(CLIQUE - 0.68)} s, clique e abertura {n(CLIQUE)}–{n(FIM)} s), {len(sons)} sons")
