"""Abertura do Bate-bola: gera compositions/abertura.html e os sons dela (abertura-sons.json, que o
montar_plano.py junta no plano).

Uso: python3 broll.py; python3 abertura.py [ESTILO [PASTA]]   (na pasta do projeto; depois montar_plano.py
e gerar.py). PASTA (padrão: a do projeto) serve para as prévias: lê o plano.json dela e escreve nela.

O que fica de todas as versões: ela diz o título ("Bate bola com doutora Nádia Resende", 0 a 2,8 s) no vídeo
normal, sem nada por cima; a abertura vem na pausa logo depois (4,4 s), com trechos dela falando mais de
perto (broll.py, olhos abertos), a música, "Bate Bola com" em Poppins e o nome à mão em Pinyon Script.

O que a cliente já recusou (não repetir):
- o modelo da doutora (cursor em pixel, estrelas chapadas, barras coloridas de TV com bipe): recusou as
  estrelas, a entrada e a "tela falhada" (16/11);
- quatro estilos (pinceladas, luz dourada com bolinhas de luz, moldura em arco, clique abrindo um círculo):
  achou infantil (16/11). Gostou mais do arco, mas ele "bugou" (dentro do arco o trecho de perto se misturava
  com o quadro parado nas trocas: imagem dupla), e da moldura de papel em que ficou o título nas pinceladas;
  não gostou das pinceladas.

Agora, abertura de programa de TV: painéis retos (caramelo e marrom, com o creme por cima) sobem e revelam o
cenário; o título na moldura de papel que ela gostou, as palavras subindo de uma máscara e um brilho passando
nela; na saída os painéis voltam e revelam a primeira pergunta. Nenhuma troca por esmaecimento: toda troca de
imagem acontece embaixo dos painéis.
- tv-arco: cenário nude com o trecho de perto num arco, contornos finos e uma luz passando no fundo;
- tv-cheia: o trecho de perto em tela cheia e a moldura com o título por cima.
"""

import json
import sys
from pathlib import Path

ESTILOS = ("tv-arco", "tv-cheia")
AQUI = Path(__file__).parent
ESTILO = sys.argv[1] if len(sys.argv) > 1 else "tv-arco"
if ESTILO not in ESTILOS:
    raise SystemExit(f"estilo {ESTILO!r}: use um de {', '.join(ESTILOS)}")
ARCO = ESTILO == "tv-arco"
SAIDA = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else AQUI
_plano = json.loads((SAIDA / "plano.json").read_text())
DURACAO = _plano["duracao"]
ENTRA = _plano["pausas"][0]["em"]                     # a pausa (montar_plano.py), num silêncio depois do título
FIM = round(ENTRA + _plano["pausas"][0]["dur"], 4)    # fim da pausa: a primeira pergunta
BROLL_TOTAL = 128 / 30                                # broll.py: trechos de 1,9 + 1,2 + 1,1667 s
FALA_FIM = 2.56                                       # ela termina de dizer o título (medido no som; o Whisper diz 2,9)
TITULO1, TITULO2 = "Bate Bola com", "Dra Nádia Resende"


def n(x):
    return f"{x:.3f}".rstrip("0").rstrip(".")


# ── painéis ───────────────────────────────────────────────────────────────────────────────────────
# três colunas; em cada uma sobe primeiro um painel de cor e logo atrás um creme por cima dele (a borda fica em
# duas cores); a tela fica coberta uns 2 quadros, a imagem troca embaixo, e os painéis seguem subindo
COLUNAS, LARG = 3, 1080 / 3
CORES = ["#B68660", "#6E4A33", "#C9A27E"]
CREME = "#F3E9DE"
paineis = ("".join(f'<div id="pl{k}" class="painel" style="left:{k * LARG:.0f}px;background:{c}"></div>' for k, c in enumerate(CORES))
           + "".join(f'<div id="pc{k}" class="painel creme" style="left:{k * LARG:.0f}px"></div>' for k in range(COLUNAS)))


def passar_paineis(ini):
    """Os painéis cobrem a tela a partir de ini e seguem subindo; devolve (js, hora da troca, fim)."""
    js = []
    for k in range(COLUNAS):
        t0 = ini + 0.04 * k
        js += [
            f'tl.fromTo("#pl{k}", {{y:1940}}, {{y:0, duration:0.32, ease:"power3.inOut", immediateRender:false}}, {n(t0)});',
            f'tl.fromTo("#pc{k}", {{y:1940}}, {{y:0, duration:0.32, ease:"power3.inOut", immediateRender:false}}, {n(t0 + 0.05)});',
            f'tl.fromTo("#pc{k}", {{y:0}}, {{y:-1940, duration:0.34, ease:"power3.inOut", immediateRender:false}}, {n(t0 + 0.37)});',
            f'tl.fromTo("#pl{k}", {{y:0}}, {{y:-1940, duration:0.34, ease:"power3.inOut", immediateRender:false}}, {n(t0 + 0.47)});',
        ]
    # coberta de ini+0,40 (a última coluna chega) a ini+0,47 (a primeira começa a sair)
    return js, round(ini + 0.42, 4), round(ini + 0.04 * (COLUNAS - 1) + 0.47 + 0.34, 4)


# nenhum quadro parado à vista (a cliente viu "o rosto dela parado"): na pausa o vídeo fica parado de ENTRA a FIM,
# então os painéis começam a subir 1/3 s antes, ainda com ela se mexendo, e cobrem o rosto antes de a imagem parar
# (o rosto, no alto, é o último a ser coberto); na volta só começam a descobrir no fim da pausa, de baixo para cima:
# a mesa (parada de todo jeito) aparece um instante antes, as mãos e o rosto já com o vídeo andando
ENTRA_PAINEIS = round(ENTRA - 1 / 3, 4)
js_in, TROCA_IN, _ = passar_paineis(ENTRA_PAINEIS)
SAI = round(FIM - 0.62, 4)
js_out, TROCA_OUT, FIM_AB = passar_paineis(SAI)

# ── trechos de perto ──────────────────────────────────────────────────────────────────────────────
BROLL_INI = TROCA_IN
BROLL_FIM = round(min(FIM, BROLL_INI + BROLL_TOTAL), 4)
TROCAS = [round(BROLL_INI + d, 4) for d in (1.9, 3.1) if BROLL_INI + d < TROCA_OUT - 0.3]
broll = (f'<div class="broll" id="broll"><div class="zoom" id="zoom">'
         f'<video id="br" class="clip" src="assets/video/broll.mp4" data-start="{n(BROLL_INI)}" '
         f'data-duration="{n(BROLL_FIM - BROLL_INI)}" data-media-start="0" muted playsinline></video></div></div>')
js_broll = [f'tl.fromTo("#zoom", {{scale:1.05}}, {{scale:1, duration:0.7, ease:"expo.out"}}, {n(BROLL_INI)});']
marcos = [BROLL_INI] + TROCAS + [TROCA_OUT]
for k, (a, b) in enumerate(zip(marcos, marcos[1:])):
    if k > 0:   # corte seco entre os trechos, com um assentar de zoom leve
        js_broll.append(f'tl.fromTo("#zoom", {{scale:1.05}}, {{scale:1, duration:0.6, ease:"expo.out", immediateRender:false}}, {n(a)});')
    js_broll.append(f'tl.fromTo("#zoom", {{scale:1}}, {{scale:1.03, duration:{b - a - 0.6:.2f}, ease:"none", immediateRender:false}}, {n(a + 0.6)});')

# ── cenário ───────────────────────────────────────────────────────────────────────────────────────
if ARCO:
    ESC, DY = 0.57, -270                                # o arco: o quadro inteiro em 0,57, no alto da tela
    xa, xb = 540 - 540 * ESC, 540 + 540 * ESC
    ya, yb = 960 + DY - 960 * ESC, 960 + DY + 960 * ESC

    def contorno(id_, m, larg, alfa):
        r = (xb - xa) / 2 + m
        return (f'<path id="{id_}" d="M{xa - m:.0f},{yb + m:.0f} L{xa - m:.0f},{ya - m + r:.0f} A{r:.0f},{r:.0f} 0 0 1 '
                f'{xb + m:.0f},{ya - m + r:.0f} L{xb + m:.0f},{yb + m:.0f}" fill="none" stroke="#A97E5A" stroke-width="{larg}" '
                f'opacity="{alfa}" pathLength="100" stroke-dasharray="100" stroke-dashoffset="100"/>')
    cena = ('<div id="cena" class="camada" style="opacity:0">'
            '<div class="camada fundo"><div class="grao"></div><div id="luzfundo" class="luzfundo"></div></div>'
            f'<svg class="camada" viewBox="0 0 1080 1920" width="1080" height="1920">{contorno("ct1", 22, 2.4, 1)}'
            f'{contorno("ct2", 50, 1.3, 0.55)}</svg>'
            f'<div id="sombra-arco" class="sombra-arco"></div><div id="arco" class="arco">{broll}</div></div>')
    js_cena = [
        f'tl.set(["#arco", "#sombra-arco"], {{scale:{ESC}, y:{DY}, transformOrigin:"540px 960px"}}, 0);',
        f'tl.fromTo(["#arco", "#sombra-arco"], {{scale:{ESC * 1.06:.4f}}}, {{scale:{ESC}, duration:0.9, ease:"expo.out", immediateRender:false}}, {n(TROCA_IN)});',
        f'tl.to("#ct1", {{strokeDashoffset:0, duration:0.9, ease:"power2.inOut"}}, {n(TROCA_IN + 0.15)});',
        f'tl.to("#ct2", {{strokeDashoffset:0, duration:1.0, ease:"power2.inOut"}}, {n(TROCA_IN + 0.3)});',
        'tl.set("#luzfundo", {rotation:18, x:-900}, 0);',
        f'tl.to("#luzfundo", {{x:1300, duration:3.0, ease:"sine.inOut"}}, {n(TROCA_IN + 0.2)});',
    ]
    CARTAO_Y, CARTAO_X, CARTAO_COR, CARTAO_LARG = 1365, (70, 1010), "#FBF6F0", 280
    TIT_TOPO, TAM1, TAM2 = 1262, 62, 108
else:
    cena = f'<div id="cena" class="camada" style="opacity:0">{broll}</div>'
    js_cena = []
    # (a moldura um pouco abaixo da das pinceladas: lá ela encostava na boca dela no trecho de perto)
    CARTAO_Y, CARTAO_X, CARTAO_COR, CARTAO_LARG = 1094, (40, 1040), "#F4E7DB", 290
    TIT_TOPO, TAM1, TAM2 = 980, 74, 124
js_cena.append(f'tl.fromTo("#cena", {{scale:1}}, {{scale:1.03, duration:{TROCA_OUT - TROCA_IN:.2f}, ease:"none"}}, {n(TROCA_IN)});')

# ── a moldura do título (a de papel que ela gostou nas pinceladas), com o brilho passando ─────────────────
x0, x1 = CARTAO_X
Y = CARTAO_Y
d = f"M{x0},{Y + 18} C{x0 + (x1 - x0) * 0.3:.0f},{Y - 4} {x0 + (x1 - x0) * 0.66:.0f},{Y + 8} {x1},{Y - 18}"
PAPEL = ('<filter id="papel" filterUnits="userSpaceOnUse" x="-200" y="-200" width="1480" height="2320">'
         '<feTurbulence type="fractalNoise" baseFrequency="0.011 0.05" numOctaves="3" seed="11" result="r"/>'
         '<feDisplacementMap in="SourceGraphic" in2="r" scale="38" xChannelSelector="R" yChannelSelector="G"/></filter>')
cartao = (f'<svg id="cartao" class="camada" viewBox="0 0 1080 1920" width="1080" height="1920" style="opacity:0">'
          f'<defs>{PAPEL}<filter id="sombra" filterUnits="userSpaceOnUse" x="-200" y="-200" width="1480" height="2320">'
          '<feDropShadow dx="0" dy="10" stdDeviation="14" flood-color="#4A2E1F" flood-opacity="0.24"/></filter>'
          '<linearGradient id="brilho-g" x1="0" x2="1" y1="0" y2="0"><stop offset="0" stop-color="#FFFFFF" stop-opacity="0"/>'
          '<stop offset="0.5" stop-color="#FFFFFF" stop-opacity="0.75"/><stop offset="1" stop-color="#FFFFFF" stop-opacity="0"/></linearGradient>'
          f'<mask id="m-cartao" maskUnits="userSpaceOnUse" x="0" y="0" width="1080" height="1920"><path d="{d}" fill="none" stroke="#FFFFFF" '
          f'stroke-width="{CARTAO_LARG}" filter="url(#papel)"/></mask></defs>'
          f'<g filter="url(#sombra)"><path id="cartao-p" d="{d}" fill="none" stroke="{CARTAO_COR}" stroke-width="{CARTAO_LARG}" '
          f'stroke-linecap="butt" pathLength="100" stroke-dasharray="100" stroke-dashoffset="100" filter="url(#papel)"/></g>'
          f'<g mask="url(#m-cartao)"><g transform="skewX(-22)"><rect id="brilho-r" x="0" y="{Y - 260}" width="200" height="520" '
          f'fill="url(#brilho-g)"/></g></g></svg>')
palavras = TITULO1.split()
t1 = " ".join(f'<span class="masc"><span class="pal" id="w{k}">{p}</span></span>' for k, p in enumerate(palavras))
esp = lambda c: "&nbsp;" if c == " " else c
t2 = "".join(f'<span class="ch" id="b{k}">{esp(c)}</span>' for k, c in enumerate(TITULO2))
traco = ('<svg id="traco" class="traco" viewBox="0 0 240 40" width="240" height="40"><path id="traco-p" '
         'd="M4,30 C60,12 130,10 236,16 M36,36 C90,24 150,22 200,26" fill="none" stroke="#86522E" stroke-width="3" '
         'stroke-linecap="round" pathLength="100" stroke-dasharray="100" stroke-dashoffset="100"/></svg>')
titulo = f'<div class="titulo" id="tit"><div class="l1">{t1}</div><div class="l2">{t2}{traco}</div></div>'
TC = round(TROCA_IN + 0.32, 4)                       # a moldura se desenha logo que o cenário aparece
T1 = round(TC + 0.3, 4)
T2 = round(T1 + 0.45, 4)
js_titulo = [
    f'tl.set("#cartao", {{opacity:1}}, {n(TC)});',
    'tl.set("#tit", {opacity:0}, 0);',               # as palavras esperam escondidas na máscara; o bloco só aparece com elas
    f'tl.set("#tit", {{opacity:1}}, {n(T1)});',
    f'tl.to("#cartao-p", {{strokeDashoffset:0, duration:0.45, ease:"power2.out"}}, {n(TC)});',
    'tl.set("#brilho-r", {x:-420}, 0);',
]
js_titulo += [f'tl.fromTo("#w{k}", {{yPercent:110}}, {{yPercent:0, duration:0.6, ease:"expo.out"}}, {n(T1 + 0.09 * k)});'
              for k in range(len(palavras))]
js_titulo += [f'tl.fromTo("#b{k}", {{opacity:0}}, {{opacity:1, duration:0.12, ease:"none"}}, {n(T2 + 0.04 * k)});'
              for k in range(len(TITULO2))]
FIM_NOME = round(T2 + 0.04 * len(TITULO2) + 0.1, 4)
BRILHO = round(FIM_NOME + 0.3, 4)
js_titulo += [f'tl.set("#traco", {{opacity:1}}, {n(FIM_NOME)});',
              f'tl.to("#traco-p", {{strokeDashoffset:0, duration:0.35, ease:"power2.out"}}, {n(FIM_NOME)});',
              f'tl.to("#brilho-r", {{x:1500, duration:0.85, ease:"power2.inOut"}}, {n(BRILHO)});']

js = (['tl.set("#ab", {opacity:1}, 0);', f'tl.set("#ab", {{opacity:0}}, {n(FIM_AB)});']
      + [f'tl.set(["#pl{k}", "#pc{k}"], {{y:1940}}, 0);' for k in range(COLUNAS)]
      + js_in + js_out
      + [f'tl.set("#cena", {{opacity:1}}, {n(TROCA_IN)});', f'tl.set("#broll", {{opacity:1}}, {n(TROCA_IN)});',
         f'tl.set(["#cena", "#cartao", "#tit"], {{opacity:0}}, {n(TROCA_OUT)});']
      + js_cena + js_broll + js_titulo)

GRAO = ("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='300' height='300'><filter id='f'>"
        "<feTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/><feColorMatrix type='saturate' values='0'/></filter>"
        "<rect width='300' height='300' filter='url(%23f)' opacity='0.5'/></svg>")
FONTES = ('@font-face { font-family: "Poppins Reels"; font-weight: 600; font-style: normal; src: url("assets/fonts/Poppins-600.ttf"); }\n'
          '@font-face { font-family: "Pinyon Script"; font-weight: 400; font-style: normal; src: url("assets/fonts/PinyonScript-Regular.ttf"); }\n')
saida = f"""<template>
  <style>
{FONTES}
    #root {{ position: absolute; inset: 0; overflow: hidden; }}
    #ab {{ position: absolute; inset: 0; }}
    .camada {{ position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; }}
    #cena {{ transform-origin: 50% 40%; }}
    .broll {{ position: absolute; inset: 0; overflow: hidden; opacity: 0; background: #2A1E16; }}
    .zoom {{ position: absolute; inset: 0; transform-origin: 52% 40%; }}
    .zoom video {{ position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; object-fit: cover; }}
    .grao {{ position: absolute; left: 0; top: 0; width: 1200px; height: 2040px; mix-blend-mode: overlay; opacity: 0.45;
             background-image: url("{GRAO}"); background-size: 300px 300px; }}
    .fundo {{ background: radial-gradient(ellipse 120% 80% at 50% 36%, #F6EEE6 0%, #ECDDCF 58%, #DEC8B4 100%); overflow: hidden; }}
    .fundo .grao {{ opacity: 0.3; }}   /* só no fundo nude, nunca no vídeo dela */
    .luzfundo {{ position: absolute; left: 0; top: -340px; width: 640px; height: 2600px;
                 background: linear-gradient(90deg, rgba(255, 255, 255, 0) 0%, rgba(255, 252, 246, 0.42) 50%, rgba(255, 255, 255, 0) 100%); }}
    .arco {{ position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; clip-path: inset(0 round 540px 540px 40px 40px); }}
    .sombra-arco {{ position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; border-radius: 540px 540px 40px 40px;
                    background: rgba(74, 46, 31, 0.38); filter: blur(46px); margin-top: 40px; }}
    .titulo {{ position: absolute; left: 0; top: {TIT_TOPO}px; width: 1080px; text-align: center; }}
    .l1 {{ font-family: "Poppins Reels"; font-weight: 600; font-size: {TAM1}px; letter-spacing: -0.02em; line-height: 1; color: #5A3722; }}
    .masc {{ display: inline-block; overflow: hidden; vertical-align: top; padding: 0 0.03em 0.12em; margin-bottom: -0.12em; }}
    .pal {{ display: inline-block; }}
    .l2 {{ position: relative; display: inline-block; font-family: "Pinyon Script"; font-size: {TAM2}px; line-height: 1;
           color: #86522E; margin-top: -2px; -webkit-text-stroke: 0.6px #86522E; }}
    .traco {{ position: absolute; left: 10px; top: {TAM2}px; opacity: 0; }}
    .ch {{ opacity: 0; display: inline-block; }}
    .painel {{ position: absolute; top: 0; width: {LARG + 1:.0f}px; height: 1920px; }}
    .painel.creme {{ background: {CREME}; box-shadow: 0 -20px 30px -12px rgba(60, 36, 22, 0.3); }}
  </style>
  <div id="root" data-composition-id="abertura" data-width="1080" data-height="1920">
    <div id="ab">{cena}{cartao}{titulo}{paineis}</div>
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
    tl.to({{}}, {{ duration: {n(DURACAO)} }}, 0);
    {(chr(10) + "    ").join(js)}
    window.__timelines["abertura"] = tl;
  </script>
</template>
"""
sons = [
    # a batida forte da música cai quando ela termina o título (o arquivo sobe do silêncio 0,33 s antes: PICO_SFX do
    # gerar.py) e a cauda vai até depois do fim da pausa, sumindo por baixo da pergunta: sem buraco de silêncio antes
    # nem depois (a cliente achou que "a música demora a começar")
    {"t": FALA_FIM, "som": "musica-abertura", "vol": 0.65},
    {"t": round(ENTRA_PAINEIS + 0.3, 3), "som": "whoosh", "vol": 0.32},
    {"t": round(BRILHO + 0.3, 3), "som": "brilho", "vol": 0.16},
    {"t": round(SAI + 0.3, 3), "som": "whoosh", "vol": 0.3},
]
(SAIDA / "compositions").mkdir(exist_ok=True)
(SAIDA / "compositions" / "abertura.html").write_text(saida)
(SAIDA / "abertura-sons.json").write_text(json.dumps(sons, ensure_ascii=False, indent=1))
print(f"ok: {ESTILO}: compositions/abertura.html (abertura {n(ENTRA)}–{n(FIM)} s, cenário {n(TROCA_IN)}–{n(TROCA_OUT)} s, "
      f"painéis até {n(FIM_AB)} s), {len(sons)} sons")
