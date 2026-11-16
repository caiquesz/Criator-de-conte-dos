"""Abertura do Bate-bola: gera compositions/abertura.html e os sons dela (abertura-sons.json, que o
montar_plano.py junta no plano).

Uso: python3 broll.py; python3 abertura.py [ESTILO [PASTA]]   (na pasta do projeto; depois montar_plano.py
e gerar.py). PASTA (padrão: a do projeto) serve para as prévias: lê o plano.json dela e escreve nela.

O que fica de todas as versões: ela diz o título ("Bate bola com doutora Nádia Resende", 0 a 2,8 s) no vídeo
normal, sem nada por cima; a abertura vem na pausa logo depois (4,4 s), com trechos dela falando mais de
perto (broll.py, olhos abertos), a música, imagem quente com grão leve, "Bate Bola com" em Poppins e o nome à
mão em Pinyon Script, letra por letra, com o traço embaixo.

Em 16/11 a cliente recusou as estrelas, a entrada do quadro e as barras coloridas de TV (a "tela falhada")
da versão no modelo da doutora. Para ela escolher, quatro estilos (ESTILOS), todos sem estrelas nem barras:
"""

import json
import random
import subprocess
import sys
from pathlib import Path

ESTILOS = {
    "pincel": "pinceladas nude e rosé pintam a tela e revelam os trechos dela; o título numa pincelada clara, "
              "como o marca-texto da matéria; sai com as mesmas pinceladas",
    "luz": "uma luz dourada acende e revela os trechos dela; bolinhas de luz desfocadas subindo devagar e "
           "brilhos redondos; sai na mesma luz",
    "arco": "o vídeo dela encolhe para uma moldura em arco sobre um fundo nude, o título em marrom embaixo; "
            "no fim o arco abre de volta para a pergunta",
    "clique": "o clique do modelo, mas a abertura nasce num círculo que abre da ponta do dedo; sem enfeites; "
              "no fim o círculo fecha de volta no dedo",
}
__doc__ += "".join(f"- {k}: {v};\n" for k, v in ESTILOS.items())

AQUI = Path(__file__).parent
ESTILO = sys.argv[1] if len(sys.argv) > 1 else "pincel"
if ESTILO not in ESTILOS:
    raise SystemExit(f"estilo {ESTILO!r}: use um de {', '.join(ESTILOS)}")
SAIDA = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else AQUI
_plano = json.loads((SAIDA / "plano.json").read_text())
DURACAO = _plano["duracao"]
ENTRA = _plano["pausas"][0]["em"]                     # a pausa (montar_plano.py), num silêncio depois do título
FIM = round(ENTRA + _plano["pausas"][0]["dur"], 4)    # fim da pausa: a primeira pergunta
BROLL_TOTAL = 128 / 30                                # broll.py: trechos de 1,9 + 1,2 + 1,1667 s
TITULO1, TITULO2 = "Bate Bola com", "Dra Nádia Resende"
rnd = random.Random(8)


def n(x):
    return f"{x:.3f}".rstrip("0").rstrip(".")


# quando o trecho de perto entra (escondido pela transição de cada estilo) e quando o título começa
BROLL_INI = round({"pincel": ENTRA + 0.5, "luz": ENTRA + 0.18, "arco": ENTRA + 0.8, "clique": ENTRA}[ESTILO], 4)
BROLL_FIM = round(min(FIM, BROLL_INI + BROLL_TOTAL), 4)
TROCAS = [round(BROLL_INI + d, 4) for d in (1.9, 3.1) if BROLL_INI + d < BROLL_FIM - 0.3]
T1 = round({"pincel": ENTRA + 0.75, "luz": ENTRA + 0.55, "arco": ENTRA + 0.95, "clique": ENTRA + 0.5}[ESTILO], 4)
T2 = round(T1 + 0.62, 4)

# ── trechos de perto ──────────────────────────────────────────────────────────────────────────────
broll = (f'<div class="broll" id="broll"><div class="balanco" id="bal"><div class="zoom" id="zoom">'
         f'<video id="br" class="clip" src="assets/video/broll.mp4" data-start="{n(BROLL_INI)}" '
         f'data-duration="{n(BROLL_FIM - BROLL_INI)}" data-media-start="0" muted playsinline></video></div></div>'
         f'<div class="quente"></div><div class="grao" id="grao"></div></div>')
js_broll = [
    # um assentar de zoom leve em cada trecho e um empurrão lento dentro dele (sem os trancos da versão anterior)
    f'tl.fromTo("#zoom", {{scale:1.06}}, {{scale:1, duration:0.6, ease:"power2.out"}}, {n(BROLL_INI)});',
]
marcos = [BROLL_INI] + TROCAS + [BROLL_FIM]
for k, (a, b) in enumerate(zip(marcos, marcos[1:])):
    if k > 0:
        js_broll.append(f'tl.fromTo("#zoom", {{scale:1.06}}, {{scale:1, duration:0.5, ease:"power2.out", immediateRender:false}}, {n(a)});')
    js_broll.append(f'tl.fromTo("#zoom", {{scale:1}}, {{scale:1.035, duration:{b - a - 0.6:.2f}, ease:"none", immediateRender:false}}, {n(a + 0.6)});')
js_broll.append(f'tl.fromTo("#bal", {{x:0, y:0, rotation:0}}, {{keyframes:{{x:[0, 6, -4, 5, -3, 0], y:[0, -5, 4, -3, 5, 0], '
                f'rotation:[0, 0.35, -0.3, 0.25, -0.35, 0]}}, duration:{BROLL_FIM - BROLL_INI:.2f}, ease:"none"}}, {n(BROLL_INI)});')
js_broll += [f'tl.set("#grao", {{x:{rnd.randint(-60, 0)}, y:{rnd.randint(-60, 0)}}}, {n(BROLL_INI + k / 30)});'
             for k in range(0, int((BROLL_FIM - BROLL_INI) * 30), 2)]

# ── título ────────────────────────────────────────────────────────────────────────────────────────
# (cor da linha 1, cor do nome, sombra, alto do bloco)
CLARO = "0 2px 4px rgba(40, 20, 10, 0.35), 0 6px 22px rgba(40, 20, 10, 0.35)"
TITULO = {
    "pincel": ("#5A3722", "#86522E", "none", 930),
    "luz": ("#FFF6EC", "#FDE7EC", "0 0 18px rgba(255, 214, 170, 0.55), " + CLARO, 930),
    "arco": ("#6A4329", "#8A5531", "none", 1318),
    "clique": ("#FDF3E7", "#FBE3EC", CLARO, 930),
}[ESTILO]
esp = lambda c: "&nbsp;" if c == " " else c
t1 = "".join(f'<span class="ch" id="a{k}">{esp(c)}</span>' for k, c in enumerate(TITULO1))
t2 = "".join(f'<span class="ch" id="b{k}">{esp(c)}</span>' for k, c in enumerate(TITULO2))
traco = (f'<svg id="traco" class="traco" viewBox="0 0 240 40" width="240" height="40"><path id="traco-p" '
         f'd="M4,30 C60,12 130,10 236,16 M36,36 C90,24 150,22 200,26" fill="none" stroke="{TITULO[1]}" stroke-width="3.2" '
         'stroke-linecap="round" pathLength="100" stroke-dasharray="100" stroke-dashoffset="100"/></svg>')
titulo = f'<div class="titulo" id="tit"><div class="l1">{t1}</div><div class="l2">{t2}{traco}</div></div>'
# "Bate Bola com" sobe de leve saindo do desfoque, letra por letra; o nome é escrito letra por letra
js_titulo = [f'tl.fromTo("#a{k}", {{opacity:0, y:16, filter:"blur(8px)"}}, {{opacity:1, y:0, filter:"blur(0px)", '
             f'duration:0.4, ease:"power2.out"}}, {n(T1 + 0.035 * k)});' for k in range(len(TITULO1))]
js_titulo += [f'tl.fromTo("#b{k}", {{opacity:0}}, {{opacity:1, duration:0.09, ease:"none"}}, {n(T2 + 0.045 * k)});'
              for k in range(len(TITULO2))]
FIM_NOME = round(T2 + 0.045 * len(TITULO2), 4)
js_titulo += [f'tl.set("#traco", {{opacity:1}}, {n(FIM_NOME)});',
              f'tl.to("#traco-p", {{strokeDashoffset:0, duration:0.35, ease:"power2.out"}}, {n(FIM_NOME)});']

GRAO = ("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='300' height='300'><filter id='f'>"
        "<feTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/><feColorMatrix type='saturate' values='0'/></filter>"
        "<rect width='300' height='300' filter='url(%23f)' opacity='0.5'/></svg>")
css = [f"""
    #ab {{ position: absolute; inset: 0; }}
    .camada {{ position: absolute; inset: 0; }}
    .broll {{ position: absolute; inset: 0; overflow: hidden; opacity: 0; background: #2A1E16; }}
    .balanco, .zoom {{ position: absolute; inset: 0; transform-origin: 52% 40%; }}
    .zoom video {{ position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; object-fit: cover;
                   filter: sepia(0.16) saturate(1.04) contrast(1.03) brightness(1.03); }}
    .quente {{ position: absolute; inset: 0; mix-blend-mode: multiply;
      background: radial-gradient(ellipse 80% 70% at 50% 45%, rgba(255, 205, 160, 0.05) 0%, rgba(120, 72, 34, 0.22) 100%); }}
    .grao {{ position: absolute; left: 0; top: 0; width: 1200px; height: 2040px; mix-blend-mode: overlay; opacity: 0.6;
             background-image: url("{GRAO}"); background-size: 300px 300px; }}
    .congela {{ position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; }}
    .titulo {{ position: absolute; left: 0; top: {TITULO[3]}px; width: 1080px; text-align: center; text-shadow: {TITULO[2]}; }}
    .l1 {{ font-family: "Poppins Reels"; font-weight: 600; font-size: 74px; letter-spacing: -0.02em; line-height: 1; color: {TITULO[0]}; }}
    .l2 {{ position: relative; display: inline-block; font-family: "Pinyon Script"; font-size: 124px; line-height: 1;
           color: {TITULO[1]}; margin-top: -2px; -webkit-text-stroke: 0.6px {TITULO[1]}; }}
    .traco {{ position: absolute; left: 10px; top: 124px; opacity: 0; }}
    .ch {{ opacity: 0; display: inline-block; }}
"""]
js = []
sons = [
    # a música sobe do silêncio meio segundo antes da entrada (PICO_SFX do gerar.py), para a fala dela emendar
    # na abertura sem tranco
    {"t": ENTRA, "som": "musica-abertura", "vol": 0.65},
]

# ── estilos ───────────────────────────────────────────────────────────────────────────────────────
if ESTILO == "pincel":
    # quatro pinceladas largas na diagonal, indo e voltando, cobrem a tela; debaixo delas o vídeo troca
    # para o trecho de perto e as pinceladas se desfazem na mesma direção, revelando
    CORES = [("#EBD5C3", "#F6EADF"), ("#E3BFB5", "#F1DAD3"), ("#D3A985", "#E6C9AE"), ("#EEDCCD", "#F8EEE6")]
    ALTURAS = [200, 740, 1280, 1820]
    pinceladas = []
    for k, (y, (cor, luz)) in enumerate(zip(ALTURAS, CORES)):
        a, b = (-330, y + 120), (1410, y - 120)
        if k % 2:
            a, b = b, a
        d = (f"M{a[0]},{a[1]} C{a[0] + (b[0] - a[0]) * 0.35:.0f},{a[1] + (b[1] - a[1]) * 0.25:.0f} "
             f"{a[0] + (b[0] - a[0]) * 0.65:.0f},{a[1] + (b[1] - a[1]) * 0.8:.0f} {b[0]},{b[1]}")
        comum = 'fill="none" stroke-linecap="butt" pathLength="100" stroke-dasharray="100" stroke-dashoffset="100"'
        pinceladas.append(f'<g id="pc{k}"><path class="pc" d="{d}" stroke="{cor}" stroke-width="700" {comum}/>'
                          f'<path class="pc" d="{d}" transform="translate(0,{-150 if k % 2 else 130})" stroke="{luz}" '
                          f'stroke-width="200" opacity="0.6" {comum}/>'
                          f'<path class="pc" d="{d}" transform="translate(0,{200 if k % 2 else -210})" stroke="{luz}" '
                          f'stroke-width="70" opacity="0.45" {comum}/></g>')
    # a área do filtro em pixels da tela: em fração da caixa do traço (o padrão) ela corta a largura da pincelada
    FILTRO = ('<filter id="{id}" filterUnits="userSpaceOnUse" x="-400" y="-400" width="1880" height="2720">'
              '<feTurbulence type="fractalNoise" baseFrequency="0.011 0.05" numOctaves="3" seed="{s}" result="r"/>'
              '<feDisplacementMap in="SourceGraphic" in2="r" scale="{d}" xChannelSelector="R" yChannelSelector="G"/></filter>')
    tinta = (f'<svg id="tinta" class="camada" viewBox="0 0 1080 1920" width="1080" height="1920">'
             f'<defs>{FILTRO.format(id="pincel", s=3, d=70)}</defs>'
             f'<rect id="tampa" x="0" y="0" width="1080" height="1920" fill="#E8CFBD" opacity="0"/>'
             f'<g filter="url(#pincel)">{"".join(pinceladas)}</g></svg>')
    faixa = (f'<svg id="faixa" class="camada" viewBox="0 0 1080 1920" width="1080" height="1920">'
             f'<defs>{FILTRO.format(id="pincel2", s=11, d=38)}</defs>'
             '<path id="faixa-p" d="M40,1062 C330,1040 700,1052 1040,1026" fill="none" stroke="#F2E2D4" stroke-width="290" '
             'opacity="0.94" stroke-linecap="butt" pathLength="100" stroke-dasharray="100" stroke-dashoffset="100" filter="url(#pincel2)"/></svg>')
    html = (f'<div id="conteudo" class="camada" style="opacity:0">{broll}{faixa}{titulo}</div>{tinta}')
    TROCA_IN, TROCA_OUT = round(ENTRA + 0.5, 4), round(FIM - 0.54, 4)

    def pincelar(ini, cobre):
        out = []
        for k in range(len(ALTURAS)):
            de, para = (100, 0) if cobre else (0, -100)
            out.append(f'tl.fromTo("#pc{k} .pc", {{strokeDashoffset:{de}}}, {{strokeDashoffset:{para}, duration:0.32, '
                       f'ease:"{"power2.out" if cobre else "power1.inOut"}", immediateRender:false}}, {n(ini + 0.06 * k)});')
        return out
    js += pincelar(ENTRA, True) + pincelar(TROCA_IN + 0.02, False)
    js += pincelar(FIM - 1.05, True) + pincelar(TROCA_OUT + 0.02, False)
    for t in (TROCA_IN, TROCA_OUT):   # uma tampa lisa nos 2 quadros da troca, para nenhuma fresta mostrar a emenda
        js += [f'tl.set("#tampa", {{opacity:1}}, {n(t - 0.03)});', f'tl.set("#tampa", {{opacity:0}}, {n(t + 0.04)});']
    js += [f'tl.set("#conteudo", {{opacity:1}}, {n(TROCA_IN)});', f'tl.set("#broll", {{opacity:1}}, {n(TROCA_IN)});',
           f'tl.set("#conteudo", {{opacity:0}}, {n(TROCA_OUT)});',
           f'tl.to("#faixa-p", {{strokeDashoffset:0, duration:0.42, ease:"power2.out"}}, {n(T1 - 0.22)});']
    FIM_AB = FIM + 0.12
    sons += [{"t": round(ENTRA + 0.1, 3), "som": "whoosh", "vol": 0.32},
             {"t": round(T1 - 0.12, 3), "som": "whoosh-rapido", "vol": 0.16},
             {"t": round(FIM - 0.95, 3), "som": "whoosh", "vol": 0.3}]

elif ESTILO == "luz":
    # a luz acende sobre o quadro dela e, no auge, o vídeo troca para o trecho de perto; bolinhas de luz
    # desfocadas sobem devagar e uns brilhos redondos piscam (nada de estrela); sai na mesma luz
    BOKEH = ["#FFD7A8", "#F7C1A6", "#FFCF94", "#F9D2D6"]
    bolas, js_bolas = [], []
    for k in range(28):
        tam = rnd.choice([24, 32, 42, 54, 66, 84, 104])
        x, y = rnd.uniform(40, 1040), rnd.uniform(160, 1860)
        if 860 < y < 1200:                       # longe do título
            y += rnd.choice([-1, 1]) * 340
        cor = rnd.choice(BOKEH)
        desf = rnd.choice([0, 1.5, 3, 6])
        alfa = rnd.uniform(0.55, 0.9) if tam < 60 else rnd.uniform(0.35, 0.55)
        bolas.append(f'<div id="bk{k}" class="bola" style="width:{tam}px;height:{tam}px;filter:blur({desf}px);'
                     f'background:radial-gradient(circle, {cor} 0%, {cor}CC 45%, {cor}00 72%)"></div>')
        t_in = BROLL_INI + 0.1 + rnd.uniform(0, 0.7)
        sobe = rnd.uniform(110, 260)
        js_bolas += [
            f'tl.fromTo("#bk{k}", {{x:{x - tam / 2:.0f}, y:{y - tam / 2:.0f}, opacity:0, scale:0.6}}, '
            f'{{opacity:{alfa:.2f}, scale:1, duration:0.6, ease:"sine.out"}}, {n(t_in)});',
            f'tl.to("#bk{k}", {{x:{x - tam / 2 + rnd.uniform(-50, 50):.0f}, y:{y - tam / 2 - sobe:.0f}, duration:{FIM - t_in:.2f}, '
            f'ease:"sine.inOut"}}, {n(t_in)});',
        ]
    for k in range(10):                          # brilhos: pontinhos de luz que acendem e apagam
        x, y = rnd.uniform(80, 1000), rnd.uniform(200, 1800)
        if 860 < y < 1200:
            y += rnd.choice([-1, 1]) * 360
        bolas.append(f'<div id="gl{k}" class="glint" style="left:{x:.0f}px;top:{y:.0f}px"></div>')
        for t in (BROLL_INI + rnd.uniform(0.3, 1.6), BROLL_INI + rnd.uniform(1.9, 3.4)):
            js_bolas += [f'tl.fromTo("#gl{k}", {{opacity:0, scale:0.3}}, {{keyframes:{{opacity:[0, 1, 0], scale:[0.3, 1, 0.3]}}, '
                         f'duration:0.6, ease:"sine.inOut", immediateRender:false}}, {n(t)});']
    html = (f'<div id="conteudo" class="camada" style="opacity:0">{broll}<div class="camada">{"".join(bolas)}</div>{titulo}</div>'
            '<div class="camada luz"><div id="vz1" class="vaz v1"></div><div id="vz2" class="vaz v2"></div>'
            '<div id="queima" class="queima"></div></div>')
    css.append("""
    .bola { position: absolute; left: 0; top: 0; border-radius: 50%; opacity: 0; mix-blend-mode: screen; }
    .glint { position: absolute; width: 10px; height: 10px; margin: -5px 0 0 -5px; border-radius: 50%; background: #FFFDF8; opacity: 0;
             box-shadow: 0 0 8px 3px rgba(255, 236, 205, 0.9), 0 0 22px 8px rgba(255, 210, 160, 0.45); }
    .luz { mix-blend-mode: screen; pointer-events: none; }
    .vaz { position: absolute; width: 1400px; height: 2400px; left: -160px; top: -240px; opacity: 0; filter: blur(50px); }
    .v1 { background: radial-gradient(ellipse 34% 48% at 50% 46%, rgba(255, 246, 226, 0.95), rgba(255, 178, 112, 0.7) 45%, transparent 75%); }
    .v2 { background: radial-gradient(ellipse 30% 40% at 50% 50%, rgba(255, 170, 170, 0.75), rgba(255, 140, 150, 0.3) 50%, transparent 76%); }
    .queima { position: absolute; inset: 0; opacity: 0;
              background: radial-gradient(ellipse 90% 80% at 55% 42%, #FFF9F0 0%, #FFE6CC 50%, #F8C9AC 100%); }
""")
    TROCA_IN, TROCA_OUT = BROLL_INI, round(FIM - 0.06, 4)

    def acender(pico, sai):
        return [
            f'tl.fromTo("#vz1", {{x:520, y:-120, opacity:0}}, {{x:-80, y:40, opacity:1, duration:0.42, ease:"sine.out", immediateRender:false}}, {n(pico - 0.34)});',
            f'tl.to("#vz1", {{x:-560, y:140, opacity:0, duration:{sai:.2f}, ease:"sine.in"}}, {n(pico + 0.04)});',
            f'tl.fromTo("#vz2", {{x:-420, y:260, opacity:0}}, {{x:60, y:120, opacity:0.9, duration:0.4, ease:"sine.out", immediateRender:false}}, {n(pico - 0.28)});',
            f'tl.to("#vz2", {{x:480, y:0, opacity:0, duration:{sai:.2f}, ease:"sine.in"}}, {n(pico + 0.06)});',
            f'tl.fromTo("#queima", {{opacity:0}}, {{opacity:1, duration:0.2, ease:"power2.in", immediateRender:false}}, {n(pico - 0.2)});',
            f'tl.to("#queima", {{opacity:0, duration:{sai:.2f}, ease:"power2.out"}}, {n(pico + 0.02)});',
        ]
    js += acender(TROCA_IN, 0.5) + acender(TROCA_OUT, 0.24)
    js += [f'tl.set("#conteudo", {{opacity:1}}, {n(TROCA_IN)});', f'tl.set("#broll", {{opacity:1}}, {n(TROCA_IN)});',
           f'tl.set("#conteudo", {{opacity:0}}, {n(TROCA_OUT)});'] + js_bolas
    FIM_AB = FIM + 0.26
    sons += [{"t": round(TROCA_IN - 0.02, 3), "som": "brilho", "vol": 0.3},
             {"t": round(TROCA_OUT - 0.05, 3), "som": "whoosh", "vol": 0.26}]

elif ESTILO == "arco":
    # o quadro dela encolhe para dentro de um arco (a moldura cresce de 1,4x, com os cantos fora da tela, e o
    # conteúdo dentro dela é contraescalado: no começo a imagem é exatamente a do vídeo, sem salto) sobre um
    # fundo nude; no arco entram os trechos de perto; no fim o arco volta ao quadro dela e abre para a pergunta
    ESC, DY = 0.57, -230
    xa, xb = 540 - 540 * ESC, 540 + 540 * ESC
    ya = 960 + DY - 960 * ESC
    yb = 960 + DY + 960 * ESC
    m = 24                                       # o contorno fino, um pouco fora do arco
    r = (xb - xa) / 2 + m
    contorno = (f'<svg id="contorno" class="camada" viewBox="0 0 1080 1920" width="1080" height="1920">'
                f'<path id="contorno-p" d="M{xa - m:.0f},{yb + m:.0f} L{xa - m:.0f},{ya - m + r:.0f} A{r:.0f},{r:.0f} 0 0 1 {xb + m:.0f},{ya - m + r:.0f} '
                f'L{xb + m:.0f},{yb + m:.0f} Z" fill="none" stroke="#B08460" stroke-width="2.6" pathLength="100" '
                f'stroke-dasharray="100" stroke-dashoffset="100"/></svg>')
    html = (f'<div id="fundo" class="camada fundo" style="opacity:0"><div class="grao"></div></div>{contorno}'
            f'<div id="arco" class="arco" style="opacity:0"><div id="arco-in" class="arco-in">'
            f'<img id="congela" class="congela" src="assets/video/abertura-quadro.jpg" alt="">{broll}</div></div>{titulo}')
    css.append("""
    .fundo { background: radial-gradient(ellipse 120% 80% at 50% 38%, #F5ECE3 0%, #ECDDCF 58%, #E0CBB8 100%); overflow: hidden; }
    .fundo .grao { opacity: 0.35; }
    .arco { position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; transform-origin: 540px 960px;
            clip-path: inset(0 round 540px 540px 40px 40px); }
    .arco-in { position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; transform-origin: 540px 960px; }
""")
    SAI = round(FIM - 0.75, 4)                   # o arco abre de volta em 0,75 s e termina na pergunta
    js += [
        f'tl.set(["#fundo", "#arco"], {{opacity:1}}, {n(ENTRA)});',
        f'tl.fromTo("#arco", {{scale:1.4, y:0}}, {{scale:{ESC}, y:{DY}, duration:0.8, ease:"power3.inOut"}}, {n(ENTRA)});',
        f'tl.fromTo("#arco-in", {{scale:{1 / 1.4:.5f}}}, {{scale:1, duration:0.8, ease:"power3.inOut"}}, {n(ENTRA)});',
        f'tl.to("#contorno-p", {{strokeDashoffset:0, duration:0.7, ease:"power2.inOut"}}, {n(ENTRA + 0.72)});',
        f'tl.fromTo("#broll", {{opacity:0}}, {{opacity:1, duration:0.3, ease:"sine.inOut"}}, {n(BROLL_INI)});',
        # a volta: o trecho de perto dá lugar ao quadro dela (o mesmo em que o vídeo continua), o título e o
        # contorno somem, e o arco cresce até a tela inteira
        f'tl.to("#broll", {{opacity:0, duration:0.25, ease:"sine.inOut"}}, {n(SAI - 0.3)});',
        f'tl.to("#tit", {{opacity:0, y:14, duration:0.3, ease:"power2.in"}}, {n(SAI - 0.35)});',
        f'tl.to("#contorno", {{opacity:0, duration:0.3, ease:"power2.in"}}, {n(SAI - 0.3)});',
        f'tl.fromTo("#arco", {{scale:{ESC}, y:{DY}}}, {{scale:1.4, y:0, duration:0.75, ease:"power3.inOut", immediateRender:false}}, {n(SAI)});',
        f'tl.fromTo("#arco-in", {{scale:1}}, {{scale:{1 / 1.4:.5f}, duration:0.75, ease:"power3.inOut", immediateRender:false}}, {n(SAI)});',
    ]
    FIM_AB = FIM
    sons += [{"t": round(ENTRA + 0.3, 3), "som": "whoosh", "vol": 0.3},
             {"t": round(ENTRA + 0.78, 3), "som": "brilho", "vol": 0.18},
             {"t": round(SAI + 0.35, 3), "som": "whoosh", "vol": 0.28}]

else:  # clique
    # o cursor em pixel do modelo clica nela uma vez e do dedo abre um círculo com o trecho de perto, com um
    # aro claro e um brilho suave no ponto do clique; sem enfeites; sai esmaecendo com desfoque
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
    PX = 8
    linhas = MAO.splitlines()
    rects = [f'<rect x="{x}" y="{y}" width="1" height="1" fill="{"#111" if c == "B" else "#FFF"}"/>'
             for y, linha in enumerate(linhas) for x, c in enumerate(linha) if c in "BW"]
    cursor = (f'<svg id="cur" class="cursor" viewBox="0 0 17 {len(linhas)}" width="{17 * PX}" '
              f'height="{len(linhas) * PX}" shape-rendering="crispEdges">{"".join(rects)}</svg>')
    em = lambda x, y: (x - 5.5 * PX, y - 0.5 * PX)     # canto do cursor para a ponta do dedo cair em (x, y)
    CX, CY = 600, 1180                                 # o peito dela, onde o dedo clica
    R = 1420                                           # raio que cobre a tela a partir do clique
    html = (f'<div id="conteudo" class="camada">{broll}{titulo}</div>'
            f'<svg id="aro" class="camada" viewBox="0 0 1080 1920" width="1080" height="1920" style="opacity:0">'
            f'<circle id="aro-c" cx="{CX}" cy="{CY}" r="1" fill="none" stroke="#FFF4E8" stroke-width="6"/></svg>'
            f'<div id="clarao" class="clarao"></div>{cursor}')
    css.append(f"""
    .cursor {{ position: absolute; left: 0; top: 0; opacity: 0; filter: drop-shadow(3px 4px 0 rgba(0, 0, 0, 0.22)); }}
    #aro {{ filter: drop-shadow(0 0 10px rgba(255, 228, 200, 0.85)); }}
    .clarao {{ position: absolute; left: {CX - 300}px; top: {CY - 300}px; width: 600px; height: 600px; border-radius: 50%; opacity: 0;
               mix-blend-mode: screen; background: radial-gradient(circle, rgba(255, 248, 236, 0.95) 0%, rgba(255, 224, 196, 0.5) 40%, transparent 70%); }}
""")
    x0, y0 = em(960, 1880)
    x1, y1 = em(CX, CY)
    ABRE = 0.62
    FECHA = round(BROLL_FIM - ABRE - 0.02, 4)          # o círculo termina de fechar antes do fim do trecho de perto
    js += [
        f'tl.fromTo("#cur", {{x:{x0:.0f}, y:{y0:.0f}, opacity:0}}, {{x:{x1:.0f}, y:{y1:.0f}, opacity:1, duration:0.5, ease:"power2.out"}}, {n(ENTRA - 0.68)});',
        f'tl.to("#cur", {{scale:0.84, duration:0.05, ease:"power1.in", transformOrigin:"32% 3%"}}, {n(ENTRA - 0.05)});',
        f'tl.to("#cur", {{scale:1, duration:0.06, ease:"power1.out"}}, {n(ENTRA)});',
        f'tl.to("#cur", {{opacity:0, duration:0.14, ease:"power1.in"}}, {n(ENTRA + 0.08)});',
        f'tl.set("#broll", {{opacity:1}}, {n(ENTRA)});',
        f'tl.fromTo("#broll", {{clipPath:"circle(0px at {CX}px {CY}px)"}}, {{clipPath:"circle({R}px at {CX}px {CY}px)", '
        f'duration:{ABRE}, ease:"power2.inOut"}}, {n(ENTRA)});',
        f'tl.set("#aro", {{opacity:1}}, {n(ENTRA)});',
        f'tl.fromTo("#aro-c", {{attr:{{r:1}}}}, {{attr:{{r:{R}}}, duration:{ABRE}, ease:"power2.inOut"}}, {n(ENTRA)});',
        f'tl.to("#aro", {{opacity:0, duration:0.2, ease:"power1.in"}}, {n(ENTRA + ABRE - 0.22)});',
        f'tl.fromTo("#clarao", {{scale:0.2, opacity:0.95}}, {{scale:1.8, opacity:0, duration:0.6, ease:"power2.out", immediateRender:false}}, {n(ENTRA)});',
        # a saída: o título some e o círculo fecha de volta no ponto do clique, deixando o quadro dela, onde o
        # vídeo continua (esmaecer o trecho de perto sobre ele dava imagem dupla)
        f'tl.to("#tit", {{opacity:0, duration:0.22, ease:"power1.in"}}, {n(FECHA - 0.2)});',
        f'tl.fromTo("#broll", {{clipPath:"circle({R}px at {CX}px {CY}px)"}}, {{clipPath:"circle(0px at {CX}px {CY}px)", '
        f'duration:{ABRE}, ease:"power2.inOut", immediateRender:false}}, {n(FECHA)});',
        f'tl.fromTo("#aro", {{opacity:0}}, {{opacity:1, duration:0.15, ease:"power1.out", immediateRender:false}}, {n(FECHA)});',
        f'tl.fromTo("#aro-c", {{attr:{{r:{R}}}}}, {{attr:{{r:1}}, duration:{ABRE}, ease:"power2.inOut", immediateRender:false}}, {n(FECHA)});',
        f'tl.to("#aro", {{opacity:0, duration:0.12, ease:"power1.in"}}, {n(FECHA + ABRE - 0.12)});',
    ]
    FIM_AB = FIM
    sons = [{"t": ENTRA, "som": "click", "vol": 0.45}] + sons + [
        {"t": round(ENTRA + 0.03, 3), "som": "brilho", "vol": 0.22},
        {"t": round(FECHA + 0.3, 3), "som": "whoosh", "vol": 0.24}]

js = (['tl.set("#ab", {opacity:1}, 0);', f'tl.set("#ab", {{opacity:0}}, {n(FIM_AB)});']
      + js + js_broll + js_titulo)
FONTES = ('@font-face { font-family: "Poppins Reels"; font-weight: 600; font-style: normal; src: url("assets/fonts/Poppins-600.ttf"); }\n'
          '@font-face { font-family: "Pinyon Script"; font-weight: 400; font-style: normal; src: url("assets/fonts/PinyonScript-Regular.ttf"); }\n')
saida = f"""<template>
  <style>
{FONTES}
    #root {{ position: absolute; inset: 0; overflow: hidden; }}
{"".join(css)}
  </style>
  <div id="root" data-composition-id="abertura" data-width="1080" data-height="1920">
    <div id="ab">{html}</div>
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
    tl.to({{}}, {{ duration: {n(DURACAO)} }}, 0);
    {(chr(10) + "    ").join(js)}
    window.__timelines["abertura"] = tl;
  </script>
</template>
"""
# o quadro parado da pausa (o último antes da emenda): o estilo arco encolhe e abre com ele
subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{ENTRA + 0.5:.3f}", "-i", str(AQUI / "assets" / "video" / "video.mp4"),
                "-frames:v", "1", "-q:v", "2", str(AQUI / "assets" / "video" / "abertura-quadro.jpg")], check=True)
(SAIDA / "compositions").mkdir(exist_ok=True)
(SAIDA / "compositions" / "abertura.html").write_text(saida)
(SAIDA / "abertura-sons.json").write_text(json.dumps(sons, ensure_ascii=False, indent=1))
print(f"ok: {ESTILO}: compositions/abertura.html (abertura {n(ENTRA)}–{n(FIM)} s, trechos de perto {n(BROLL_INI)}–{n(BROLL_FIM)} s), {len(sons)} sons")
