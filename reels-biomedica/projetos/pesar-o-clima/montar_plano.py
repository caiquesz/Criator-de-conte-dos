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
import os
import re
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).parent
SCRIPTS = AQUI.parent.parent.parent / "reels-imobiliaria" / "scripts"
sys.path.insert(0, str(SCRIPTS))
from sincronizar import inicio_corrigido, trechos_de_fala  # noqa: E402

FPS = 30
QUADROS = 1765                   # o vídeo-base tem o último quadro parado no fim (montar_video.py, CAUDA)
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

# 4ª versão (18/11: "desce a legenda um pouco mais"): a referência tem a legenda a 1089 (726 de 1280); a cliente
# pediu mais baixa que lá. Só a legenda normal desce; as maiúsculas, que ela aprovou, ficam onde estão
Y_LEGENDA = 1159                 # meio da linha da legenda
Y_MAIUSC = 1107                  # meio do bloco de maiúsculas (referência: 736–747 de 1280, centralizado em x)
# na referência o "HARMONIZAÇÃO / GLÚTEA" fica alinhado à esquerda (x 138 de 720) e mais baixo (meio a 758 de 1280):
# o "HARMONIZAÇÃO / CORPORAL" daqui, que é o mesmo momento, vai do mesmo jeito
ESQUERDA = {106: (200, 1145)}
# na referência a última legenda sai e, no mesmo quadro, a assinatura entra, sozinha na tela, e fica 1,1 s até o fim
FIM_FALA = round(ws[-1]["e"] + 0.15, 3)
# como cada bloco de maiúsculas entra (3ª versão, medido quadro a quadro na referência por correlação com o quadro
# parado): o primeiro de uma sequência desliza até o lugar e aparece; o que vem logo depois de outro troca seco
# (O CONTORNO, OU O FORMATO, DO SEU BUMBUM). O movimento é sempre quadrático (power1.out: a raiz da distância que
# falta cai igual a cada quadro); a opacidade sobe linear. (deslocamento inicial em px, duração do movimento, da opacidade)
ENTRADAS_REF = {
    "agachamento": (-360, 0.47, 0.30),   # "SÓ FAZENDO AGACHAMENTO": desce de 360 px em 0,47 s
    "nao_e_isso": (-170, 0.38, 0.30),    # "NÃO É ISSO!": desce de 170 px em 0,38 s
    "projecao": (-235, 0.12, 0.12),      # "A PROJEÇÃO": desce rápido, 0,12 s
    "harmonizacao": (200, 0.22, 0.13),   # "HARMONIZAÇÃO GLÚTEA": sobe de baixo, 0,22 s
}
# bloco daqui (primeira palavra) → o da referência; os outros como o "NÃO É ISSO!"
ENTRADA = {8: "agachamento", 65: "projecao", 76: "projecao", 106: "harmonizacao"}
# o "HARMONIZAÇÃO / GLÚTEA" da referência tem letra menor (maiúscula de 58 px contra 68–70 dos outros blocos), mais
# espaço entre as letras e entre as linhas (linha a cada 85 px)
ESTILO = {106: "font-size:83.5px; line-height:1.02; letter-spacing:0.05em"}
html_l, js_l, entradas_maiusc = [], [], []
for k, e in enumerate(L):
    ini = ws[primeira(e)]["s"]
    ult = ws[ultima(e)]
    prox = ws[primeira(L[k + 1])]["s"] if k + 1 < len(L) else DUR
    fim = prox if prox - ult["e"] < 0.7 else round(ult["e"] + 0.3, 3)
    fim = min(fim, DUR) if k + 1 < len(L) else FIM_FALA
    gid = f"g{k + 1}"
    if e[0] == "M":
        linhas = "".join(f'<div class="ml">{" ".join(palavra(i, True) for i in range(a, b + 1))}</div>' for a, b in e[1])
        extra = "; " + ESTILO[primeira(e)] if primeira(e) in ESTILO else ""
        if primeira(e) in ESQUERDA:
            xe, ye = ESQUERDA[primeira(e)]
            html_l.append(f'<div class="m" id="{gid}" style="top:{ye}px; left:{xe}px; width:auto; text-align:left{extra}">'
                          f'{linhas}</div>')
        else:
            html_l.append(f'<div class="m" id="{gid}" style="top:{Y_MAIUSC}px{extra}">{linhas}</div>')
        # sai seca. O yPercent mantém o bloco centrado no top (o "y" do GSAP sobrescreve o translateY do CSS: na 2ª
        # versão as maiúsculas ficaram 80 px baixas)
        seguida = k > 0 and L[k - 1][0] == "M"
        if seguida:
            js_l.append(f'tl.set("#{gid}", {{opacity:1, yPercent:-50}}, {n(ini)});')
        else:
            dy, dur_m, dur_o = ENTRADAS_REF[ENTRADA.get(primeira(e), "nao_e_isso")]
            js_l += [f'tl.fromTo("#{gid}", {{y:{dy}, yPercent:-50}}, {{y:0, yPercent:-50, duration:{dur_m}, ease:"power1.out"}}, '
                     f'{n(ini)});',
                     f'tl.fromTo("#{gid}", {{opacity:0}}, {{opacity:1, duration:{dur_o}, ease:"none"}}, {n(ini)});']
        js_l.append(f'tl.set("#{gid}", {{opacity:0}}, {n(fim)});')
        entradas_maiusc.append((ini, seguida))
    else:
        texto = " ".join(palavra(i) for i in range(e[0], e[1] + 1))
        html_l.append(f'<div class="c" id="{gid}" style="top:{Y_LEGENDA}px">{texto}</div>')
        js_l += [f'tl.set("#{gid}", {{opacity:1}}, {n(ini)});', f'tl.set("#{gid}", {{opacity:0}}, {n(fim)});']

# ── assinatura no fim (referência: "Dra Enyla / Cerqueira" em pincel, aparecendo da esquerda depois da fala) ──
ASSIN_T = FIM_FALA               # quando a última legenda sai (o vídeo-base tem o último quadro parado até o fim)
# como entra (medido na referência, 71,5–72,0 s): aparece em 0,45 s (opacidade linear), subindo 16 px e passando de
# 105% para 100%, com uma cortina suave da esquerda para a direita ao longo da inclinação (o fim do sobrenome por último)
html_l.append('''<div id="assin"><div id="assin-in"><div id="assin-an" data-layout-allow-overlap>
      <span class="w dra">Dra</span><span class="w nome1">Nádia</span><span class="w nome2">Resende</span>
    </div></div></div>''')
js_l += [f'tl.set("#assin", {{opacity:1}}, {n(ASSIN_T)});',
         f'tl.fromTo("#assin-an", {{opacity:0}}, {{opacity:1, duration:0.45, ease:"none"}}, {n(ASSIN_T)});',
         f'tl.fromTo("#assin-an", {{y:16, scale:1.05}}, {{y:0, scale:1, duration:0.45, ease:"power1.out"}}, {n(ASSIN_T)});',
         f'tl.fromTo("#assin-in", {{"--w":"0%"}}, {{"--w":"135%", duration:0.4, ease:"power1.out"}}, {n(ASSIN_T)});']

# Assinatura (3ª versão): a letra de pincel da referência tem traço de peso médio e quase uniforme (~9 px), o E de
# dois laços, o y com laço e bem inclinada. Comparadas na mesma escala (scratchpad, fontes-assin): a Mr Dafoe das
# outras versões tem traço de ~14 px e contraste forte; a Satisfy (Apache 2.0) tem o peso e os laços da referência,
# e com mais 10° de inclinação fica com a mesma inclinação.
# Legendas (4ª versão, "não gostei da fonte da legenda tradicional, não achei igual à referência"): a Roboto 300 tinha
# o peso certo mas outro desenho (letras redondas mais estreitas, outro "a", "e", "g", "t"); agora é a FreeSans (o
# desenho da Helvetica) afinada até o peso da Light da referência (fonte_legenda.py), 56 px e −0,012em: altura-x de
# 31 px (lá, 30) e "precisa de complemento" com 570 px de largura (lá, 573).
# 2ª versão (18/11: "as fontes não estão nada iguais"): a referência é Helvetica Neue (o R de perna reta, o G com
# esporão, o "a" com rabinho, letras coladas): UltraLight nas maiúsculas e nas duas linhas finas do título, Light
# nas legendas, Bold no "O CLIMA?". A Inter da 1ª versão é mais larga e tem outro "a" e outro G. Entre as livres,
# comparadas na mesma escala da referência (scratchpad, comparar2/3): Roboto Thin e Light, com as letras coladas,
# ficaram as mais parecidas; o negrito é a FreeSans Bold (o clone da Helvetica Bold do GNU FreeFont).
FONTES = "".join(
    f'\n    @font-face {{ font-family: "Roboto Ref"; font-weight: {p}; src: url("assets/fonts/Roboto-{p}.woff2") format("woff2"); }}'
    for p in (100, 300)) + \
    '\n    @font-face { font-family: "Helvetica Ref"; font-weight: 700; src: url("assets/fonts/FreeSansBold.ttf"); }' + \
    '\n    @font-face { font-family: "Legenda Ref"; src: url("assets/fonts/FreeSans-LightRef.ttf"); }' + \
    '\n    @font-face { font-family: "Assinatura"; src: url("assets/fonts/Satisfy-400.woff2") format("woff2"); }'
# 3ª versão (18/11: "não quero nenhum contorno nas fontes, nenhuma sombra, nenhum contorno preto; igualzinho tá no
# vídeo"): como na referência, letra branca pura, sem sombra nenhuma
SOMBRA = "none"


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


# a assinatura da referência ocupa x 280–837 e y 1067–1350 (1080×1920), inclinada uns 9°: "Dra" pequeno à esquerda,
# o nome grande e o sobrenome embaixo começando logo depois do "Dra"
# na referência: "Dra" x 280–405 / y 1165–1235, "Enyla" x 435–765 / y 1075–1215, "Cerqueira" x 315–840 / y 1195–1350
ASSIN_X, ASSIN_Y = 220, 1089
DRA, NOME1, NOME2 = (30, 95, 80), (196, 31, 140), (74, 161, 140)   # (x, y dentro do bloco inclinado, tamanho)
# PESAR_DEPURAR=1 pinta cada palavra de uma cor para medir onde caiu
COR_DEP = ("#FF0000", "#00FF00", "#0000FF") if os.environ.get("PESAR_DEPURAR") else ("#FFFFFF",) * 3
css_l = f"""    .c {{ position: absolute; left: 60px; width: 960px; transform: translateY(-50%); text-align: center; opacity: 0;
         font-family: "Legenda Ref"; font-weight: 400; font-size: 56px; line-height: 1.1; letter-spacing: -0.012em;
         color: #FFFFFF; text-shadow: {SOMBRA}; white-space: nowrap; }}
    .m {{ position: absolute; left: 20px; width: 1040px; transform: translateY(-50%); text-align: center; opacity: 0;
         font-family: "Roboto Ref"; font-weight: 100; font-size: 98px; line-height: 0.84; letter-spacing: -0.052em;
         color: #FFFFFF; text-shadow: {SOMBRA}; }}
    .ml {{ white-space: nowrap; }}
    #assin {{ position: absolute; inset: 0; opacity: 0; }}
    #assin-in {{ position: absolute; left: {ASSIN_X}px; top: {ASSIN_Y}px; width: 760px; height: 380px;
                transform: rotate(-9deg); transform-origin: 0 0; --w: 0%;
                -webkit-mask-image: linear-gradient(90deg, #000 calc(var(--w) - 35%), transparent var(--w));
                mask-image: linear-gradient(90deg, #000 calc(var(--w) - 35%), transparent var(--w)); }}
    #assin-an {{ position: absolute; inset: 0; transform-origin: 50% 50%; opacity: 0; }}
    .w {{ position: absolute; font-family: "Assinatura"; color: #FFFFFF; line-height: 1; text-shadow: {SOMBRA};
          white-space: nowrap; transform: skewX(-10deg); transform-origin: 0 100%; }}
    .dra {{ left: {DRA[0]}px; top: {DRA[1]}px; font-size: {DRA[2]}px; color: {COR_DEP[0]}; }}
    .nome1 {{ left: {NOME1[0]}px; top: {NOME1[1]}px; font-size: {NOME1[2]}px; color: {COR_DEP[1]}; }}
    .nome2 {{ left: {NOME2[0]}px; top: {NOME2[1]}px; font-size: {NOME2[2]}px; color: {COR_DEP[2]}; }}"""
(AQUI / "compositions").mkdir(exist_ok=True)
(AQUI / "compositions" / "legendas-pesar.html").write_text(composicao("legendas-pesar", css_l, "    " + "\n    ".join(html_l), js_l))

# ── abertura: o título enquanto ela diz "Posso pesar o clima?" (0–1,67 s) ─────────────────────────────────────
TITULO_FIM = 1.667               # o corte do próprio vídeo; a luz quente cobre a troca
# 3ª versão ("até a posição que tá as falas, as palavras, eu quero igual, idêntico"): cada linha no lugar e no tamanho
# medidos na referência a 0,8 s (1080×1920). As duas linhas finas têm a mesma largura (x 277–548): o "PESAR" é maior
# que o "POSSO" (letra de 72 px contra 65). Topo das maiúsculas: POSSO 882, PESAR 960, O CLIMA? 1049 (x 190–627);
# o nome em duas linhas de maiúscula de 25 px, topo em 1216 e 1247, alinhado à esquerda em x 319.
# Cada linha: (texto, classe, centro ou esquerda em x, topo da maiúscula, tamanho da letra, espaço entre letras)
TITULO = [("POSSO", "t1", 412, 882, 92, -0.005), ("PESAR", "t1", 413, 957, 102, -0.048),
          ("O CLIMA?", "t2", 409, 1049, 97, -0.025)]
NOME = [('<span class="drf">DRA.</span> NÁDIA', 317, 1216), ("RESENDE", 317, 1249)]
NOME_PX = 35.5
# do topo da caixa (line-height 1) ao topo da maiúscula, em fração do tamanho da letra (medido no render)
TOPO_CAPS = {"t1": 0.103, "t2": 0.061, "dr": 0.09}
abertura = '    <div id="tit"><div id="tit-l">\n' + "".join(
    f'      <div class="tl {c}" style="left:{x}px; top:{y - TOPO_CAPS[c] * px:.1f}px; font-size:{px}px; '
    f'letter-spacing:{ls}em">{t}</div>\n' for t, c, x, y, px, ls in TITULO) + '    </div><div id="tit-n">\n' + "".join(
    f'      <div class="dr" style="left:{x}px; top:{y - TOPO_CAPS["dr"] * NOME_PX:.1f}px">{t}</div>\n'
    for t, x, y in NOME) + "    </div></div>"
css_a = f"""    #tit {{ position: absolute; inset: 0; color: #FFFFFF; text-shadow: {SOMBRA}; white-space: nowrap; }}
    #tit-l, #tit-n {{ position: absolute; inset: 0; opacity: 0; }}
    .tl {{ position: absolute; transform: translateX(-50%); line-height: 1; }}
    .t1 {{ font-family: "Roboto Ref"; font-weight: 100; }}
    .t2 {{ font-family: "Helvetica Ref"; font-weight: 700; }}
    .dr {{ position: absolute; font-family: "Helvetica Ref"; font-weight: 700; font-size: {NOME_PX}px; line-height: 1;
          letter-spacing: -0.02em; }}
    .drf {{ font-family: "Roboto Ref"; font-weight: 300; }}"""
# entrada (medida na referência): as três linhas descem de 400 px até o lugar em 0,5 s (power1.out) aparecendo em
# 0,47 s (sine.out), desde o primeiro quadro; o nome, separado, sobe de 45 px em 0,18 s a partir de 0,05 s e aparece em
# 0,1 s. Saída: tudo some linear (0,23 s até zero) começando 0,15 s antes do corte, que tira o resto
js_a = ['tl.fromTo("#tit-l", {y:-400}, {y:0, duration:0.5, ease:"power1.out"}, 0);',
        'tl.fromTo("#tit-l", {opacity:0}, {opacity:1, duration:0.47, ease:"sine.out"}, 0);',
        'tl.fromTo("#tit-n", {y:45}, {y:0, duration:0.18, ease:"power1.out"}, 0.05);',
        'tl.fromTo("#tit-n", {opacity:0}, {opacity:1, duration:0.1, ease:"none"}, 0.05);',
        f'tl.to("#tit", {{opacity:0, duration:0.23, ease:"none"}}, {n(TITULO_FIM - 0.15)});',
        f'tl.set("#tit", {{opacity:0}}, {n(TITULO_FIM)});']
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
    "video_original": "assets/video/voz.wav",          # o som do original intacto, mais silêncio na cauda
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
