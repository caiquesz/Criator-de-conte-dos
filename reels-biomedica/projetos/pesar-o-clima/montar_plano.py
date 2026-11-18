"""Edição do "Posso pesar o clima?" na estética da referência que a cliente mandou (referencias/ref-pesar-o-clima.mp4,
a Dra. de blazer branco, 18/11): "pegue as fontes, as transições, como cada palavra entra, como cada palavra sai, tudo;
só não o color grade". Escreve compositions/abertura-pesar.html e compositions/legendas-pesar.html, o plano.json e roda o gerar.py.

Uso: python3 montar_video.py; python3 montar_plano.py   (na pasta do projeto)

Medido na referência, quadro a quadro (720×1280, aqui ×1,5):
  - abertura: o título "POSSO / PESAR / O CLIMA?" em três linhas centralizadas, as duas primeiras em grotesca
    finíssima e a última em negrito, com o nome da doutora pequeno embaixo ("DRA." fino, o nome em negrito), o bloco
    centrado a 38% da largura; entra descendo e aparecendo em 0,3 s enquanto o vídeo sai de um zoom; some numa luz
    quente (laranja, clarão branco) que leva ao plano seguinte;
  - legendas: grotesca leve (Helvetica Neue Light na referência; aqui Roboto 300, 59 px), branca, com maiúsculas e pontuação
    normais (vírgula, ponto, interrogação), 1 a 4 palavras por vez, centralizada a ~57% da altura; a frase inteira de
    uma vez e troca em corte seco;
  - as palavras de impacto: maiúsculas finíssimas grandes (Roboto 100, 98 px, letras coladas), uma a três linhas coladas, centralizadas;
    entram subindo e aparecendo em 0,2 s e saem em corte seco;
  - P&B numa frase de peso, entrando e saindo por uma luz quente;
  - no fim, a assinatura em letra de pincel inclinada ("Dra Nádia / Resende", Mr Dafoe), aparecendo da esquerda.
  - sons: whoosh na luz e nas palavras de impacto, grave na entrada do P&B, brilho na assinatura (a 0,5, o volume que
    a cliente aprovou no Caso de paciente).
"""
import json
import re
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).parent
SCRIPTS = AQUI.parent.parent.parent / "reels-imobiliaria" / "scripts"
sys.path.insert(0, str(SCRIPTS))
from sincronizar import inicio_corrigido, trechos_de_fala  # noqa: E402

FPS = 30
QUADROS = 1739
DUR = round(QUADROS / FPS, 4)
ws = [w for s in json.loads((AQUI / "transcricao.json").read_text()) for w in s["palavras"]]
trechos = trechos_de_fala(AQUI / "assets" / "video" / "original.mov")
ant = -1.0
for w in ws:
    w["s"] = round(max(inicio_corrigido(w["s"], trechos), ant + 0.06), 3)
    ant = w["s"]
# o Whisper (small e medium) escreve "devolve"; pela duração (3 sílabas) e pela frase de antes ("desenvolver a
# musculatura") é "desenvolve"
TEXTO = {121: "desenvolve"}


def palavra(i, caixa_alta=False):
    t = TEXTO.get(i, ws[i]["t"])
    if caixa_alta:
        return re.sub(r"[.,:;]+$", "", t).upper()
    return t


def n(x):
    return f"{x:.3f}".rstrip("0").rstrip(".")


# ── legendas: (primeira palavra, última palavra) ou ("M", [(a, b), ...]) para as maiúsculas (uma tupla por linha) ──
L = [
    (4, 4), (5, 7), ("M", [(8, 8), (9, 9)]), (10, 12), (13, 15), ("M", [(16, 16), (17, 18)]), (19, 20),
    (21, 22), (23, 26), (27, 29), (30, 31), (32, 35),
    (36, 38), ("M", [(39, 39)]), (40, 42), (43, 44), (45, 45), (46, 48), (49, 50), (51, 52),
    (53, 55), ("M", [(56, 56), (57, 58)]), (59, 60), (61, 62), (63, 64), ("M", [(65, 66)]),
    (67, 68), (69, 71), (72, 75), ("M", [(76, 77)]), ("M", [(78, 78), (79, 80)]), (81, 82), (83, 85), (86, 87), (88, 90),
    (91, 93), (94, 96), (97, 99),
    (100, 103), (104, 105), ("M", [(106, 106), (107, 107)]), (108, 110), (111, 112), (113, 114), (115, 118),
    (119, 120), (121, 122), (123, 125), (126, 128),
    (129, 131), (132, 134), (135, 136), (137, 139), (140, 141), (142, 143), (144, 145), ("M", [(146, 146), (147, 147)]),
    (148, 150), (151, 152), (153, 154), (155, 158),
]
primeira = lambda e: e[0] if e[0] != "M" else e[1][0][0]
ultima = lambda e: e[1] if e[0] != "M" else e[1][-1][1]
assert primeira(L[0]) == 4 and ultima(L[-1]) == len(ws) - 1
assert all(primeira(b) == ultima(a) + 1 for a, b in zip(L, L[1:])), "as legendas têm que cobrir todas as palavras"

Y_LEGENDA = 1089                 # meio da linha da legenda (referência: 726 de 1280)
Y_MAIUSC = 1105                  # meio do bloco de maiúsculas (referência: ~737 de 1280)
html_l, js_l, entradas_maiusc = [], [], []
for k, e in enumerate(L):
    ini = ws[primeira(e)]["s"]
    ult = ws[ultima(e)]
    prox = ws[primeira(L[k + 1])]["s"] if k + 1 < len(L) else DUR
    fim = prox if prox - ult["e"] < 0.7 else round(ult["e"] + 0.3, 3)
    fim = min(fim, DUR)
    gid = f"g{k + 1}"
    if e[0] == "M":
        linhas = "".join(f'<div class="ml">{" ".join(palavra(i, True) for i in range(a, b + 1))}</div>' for a, b in e[1])
        html_l.append(f'<div class="m" id="{gid}" style="top:{Y_MAIUSC}px">{linhas}</div>')
        # entra subindo e aparecendo em 0,2 s (5,13–5,33 s na referência), sai seca
        js_l += [f'tl.fromTo("#{gid}", {{opacity:0, y:60}}, {{opacity:1, y:0, duration:0.2, ease:"power2.out"}}, {n(ini)});',
                 f'tl.set("#{gid}", {{opacity:0}}, {n(fim)});']
        seguida = k > 0 and L[k - 1][0] == "M"
        entradas_maiusc.append((ini, seguida))
    else:
        texto = " ".join(palavra(i) for i in range(e[0], e[1] + 1))
        html_l.append(f'<div class="c" id="{gid}" style="top:{Y_LEGENDA}px">{texto}</div>')
        js_l += [f'tl.set("#{gid}", {{opacity:1}}, {n(ini)});', f'tl.set("#{gid}", {{opacity:0}}, {n(fim)});']

# ── assinatura no fim (referência: "Dra Enyla / Cerqueira" em pincel, aparecendo da esquerda depois da fala) ──
ASSIN_T = ws[154]["s"]           # em "possibilidades": o vídeo acaba 0,4 s depois da última palavra
html_l.append('''<div id="assin"><div id="assin-in">
      <span class="dra">Dra</span><span class="nome1">Nádia</span><br><span class="nome2">Resende</span>
    </div></div>''')
js_l += [f'tl.set("#assin", {{opacity:1}}, {n(ASSIN_T)});',
         f'tl.fromTo("#assin-in", {{clipPath:"inset(0 100% 0 0)", opacity:0.2}}, '
         f'{{clipPath:"inset(0 0% 0 0)", opacity:1, duration:0.6, ease:"power2.out"}}, {n(ASSIN_T)});']

# 2ª versão (18/11: "as fontes não estão nada iguais"): a referência é Helvetica Neue (o R de perna reta, o G com
# esporão, o "a" com rabinho, letras coladas): UltraLight nas maiúsculas e nas duas linhas finas do título, Light
# nas legendas, Bold no "O CLIMA?". A Inter da 1ª versão é mais larga e tem outro "a" e outro G. Entre as livres,
# comparadas na mesma escala da referência (scratchpad, comparar2/3): Roboto Thin e Light, com as letras coladas,
# ficaram as mais parecidas; o negrito é a FreeSans Bold (o clone da Helvetica Bold do GNU FreeFont).
FONTES = "".join(
    f'\n    @font-face {{ font-family: "Roboto Ref"; font-weight: {p}; src: url("assets/fonts/Roboto-{p}.woff2") format("woff2"); }}'
    for p in (100, 300)) + \
    '\n    @font-face { font-family: "Helvetica Ref"; font-weight: 700; src: url("assets/fonts/FreeSansBold.ttf"); }' + \
    '\n    @font-face { font-family: "Assinatura"; src: url("assets/fonts/MrDafoe-400.woff2") format("woff2"); }'
SOMBRA = "0 1px 3px rgba(20, 14, 10, 0.5), 0 2px 16px rgba(20, 14, 10, 0.45)"


def composicao(cid, css, corpo, js):
    return f"""<template>
  <style>{FONTES}
    #root {{ position: absolute; inset: 0; overflow: hidden; }}
{css}
  </style>
  <div id="root" data-composition-id="{cid}" data-width="1080" data-height="1920">
{corpo}
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
    tl.to({{}}, {{ duration: {n(DUR)} }}, 0);
    {(chr(10) + "    ").join(js)}
    window.__timelines["{cid}"] = tl;
  </script>
</template>
"""


css_l = f"""    .c {{ position: absolute; left: 60px; width: 960px; transform: translateY(-50%); text-align: center; opacity: 0;
         font-family: "Roboto Ref"; font-weight: 300; font-size: 59px; line-height: 1.1; letter-spacing: -0.055em;
         color: #FFFFFF; text-shadow: {SOMBRA}; white-space: nowrap; }}
    .m {{ position: absolute; left: 20px; width: 1040px; transform: translateY(-50%); text-align: center; opacity: 0;
         font-family: "Roboto Ref"; font-weight: 100; font-size: 98px; line-height: 0.84; letter-spacing: -0.06em;
         color: #FFFFFF; text-shadow: {SOMBRA}; }}
    .ml {{ white-space: nowrap; }}
    #assin {{ position: absolute; left: 0; top: 1330px; width: 1080px; opacity: 0; }}
    #assin-in {{ position: absolute; left: 300px; top: 0; transform: rotate(-9deg); transform-origin: 0 50%;
                font-family: "Assinatura"; color: #FFFFFF; line-height: 0.92; text-shadow: {SOMBRA}; }}
    .dra {{ font-size: 58px; margin-right: 14px; }}
    .nome1 {{ font-size: 118px; }}
    .nome2 {{ font-size: 118px; margin-left: 70px; }}"""
(AQUI / "compositions").mkdir(exist_ok=True)
(AQUI / "compositions" / "legendas-pesar.html").write_text(composicao("legendas-pesar", css_l, "    " + "\n    ".join(html_l), js_l))

# ── abertura: o título enquanto ela diz "Posso pesar o clima?" (0–1,67 s) ─────────────────────────────────────
TITULO_FIM = 1.667               # o corte do próprio vídeo; a luz quente cobre a troca
abertura = """    <div id="tit">
      <div class="t1">POSSO</div><div class="t1">PESAR</div><div class="t2">O CLIMA?</div>
      <div class="dr"><span class="drf">DRA.</span> <b>NÁDIA</b><br><b>RESENDE</b></div>
    </div>"""
css_a = f"""    #tit {{ position: absolute; left: 412px; top: 862px; transform: translateX(-50%); text-align: center; opacity: 0;
           color: #FFFFFF; text-shadow: {SOMBRA}; white-space: nowrap; }}
    .t1 {{ font-family: "Roboto Ref"; font-weight: 100; font-size: 92px; line-height: 0.88; letter-spacing: -0.065em; }}
    .t2 {{ font-family: "Helvetica Ref"; font-weight: 700; font-size: 98px; line-height: 0.92; letter-spacing: -0.025em; }}
    .dr {{ margin-top: 70px; font-size: 30px; line-height: 1.05; letter-spacing: -0.02em; text-align: left;
          display: inline-block; }}
    .drf {{ font-family: "Roboto Ref"; font-weight: 300; }}
    .dr b {{ font-family: "Helvetica Ref"; font-weight: 700; }}"""
js_a = ['tl.fromTo("#tit", {opacity:0, y:-70}, {opacity:1, y:0, duration:0.32, ease:"power2.out"}, 0.02);',
        f'tl.to("#tit", {{opacity:0, duration:0.18, ease:"power1.in"}}, {n(TITULO_FIM - 0.12)});']
(AQUI / "compositions" / "abertura-pesar.html").write_text(composicao("abertura-pesar", css_a, abertura, js_a))

# ── transições e sons ───────────────────────────────────────────────────────────────────────────────────────
PB_INI, PB_FIM = 993 / FPS, 1085 / FPS
transicoes = [
    {"t": 0.0, "tipo": "corte", "escala": 1.1},                                        # o vídeo sai de um zoom na abertura
    {"t": TITULO_FIM, "tipo": "luz", "zoom": False, "som": "whoosh-transicao", "vol": 0.6},
    {"t": PB_INI, "tipo": "luz", "zoom": False, "som": "whoosh-transicao", "vol": 0.6},
    {"t": PB_FIM, "tipo": "luz", "zoom": False, "som": "whoosh-grave", "vol": 0.5},
]
sons = [{"t": 0.04, "som": "whoosh-rapido", "vol": 0.5},                               # o título descendo
        {"t": PB_INI + 0.02, "som": "impacto", "vol": 0.6},                             # o grave da entrada do P&B
        {"t": ASSIN_T, "som": "brilho", "vol": 0.6}, {"t": ASSIN_T + 0.02, "som": "impacto", "vol": 0.35}]
for t, seguida in entradas_maiusc:                                                     # as palavras de impacto
    if not seguida:
        sons.append({"t": t, "som": "whoosh-rapido", "vol": 0.55})
sons.sort(key=lambda s: s["t"])

plano = {
    "video": "assets/video/base.mp4",
    "video_original": "assets/video/original.mov",
    "video_tem_audio": True,
    "duracao": DUR,
    "cores": {"texto": "#FFFFFF", "destaque": "#FFFFFF", "destaque_escuro": "#FFFFFF", "brilho": False, "vazamento": "#FF7A2E"},
    "legendas": [],
    "fotos": [],
    "transicoes": transicoes,
    "extras": [{"id": "abertura-pesar", "src": "compositions/abertura-pesar.html", "z": 6},
               {"id": "legendas-pesar", "src": "compositions/legendas-pesar.html", "z": 7}],
    "sfx_extra": sons,
    "volume_efeitos": 0.5,
}
(AQUI / "plano.json").write_text(json.dumps(plano, ensure_ascii=False, indent=1))
subprocess.run(["python3", str(SCRIPTS / "gerar.py"), str(AQUI)], check=True)
print(f"ok: {len(L)} legendas ({sum(1 for e in L if e[0] == 'M')} em maiúsculas), {len(sons)} sons extras")
