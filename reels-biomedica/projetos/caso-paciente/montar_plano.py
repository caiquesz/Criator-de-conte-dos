"""Monta a edição do Caso de paciente, 2ª versão, nas referências (veja roteiro.py): escreve as camadas
compositions/legendas-ref.html (legendas da referência B) e compositions/fotos-ref.html (antes e depois da
referência A), o plano.json e roda o gerar.py.

Uso: python3 cortar_fotos.py; python3 montar_video.py; python3 montar_plano.py   (na pasta do projeto)

A 1ª versão (legendas Poppins no top dela, o antes atrás dela com recorte, cards inclinados, tela dividida e
flash branco) a cliente recusou: "até agora você não fez nenhum vídeo com base nas referências". Nesta, tudo
sai das duas referências que ela mandou; a voz e a música do vídeo continuam as do original.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

from roteiro import (ALTURA, ALTURA_COM_FOTO, FOTO_CHEIA, FOTO_FAIXA, FOTO_PAR, FOTO_UNICA, FRASES, GRANDES, PLANOS,
                     TOTAL, TRANSICOES)

AQUI = Path(__file__).parent
SCRIPTS = AQUI.parent.parent.parent / "reels-imobiliaria" / "scripts"
sys.path.insert(0, str(SCRIPTS))
from sincronizar import inicio_corrigido, trechos_de_fala  # noqa: E402

DUR = round(TOTAL / 30, 4)
ws = [w for s in json.loads((AQUI / "transcricao.json").read_text()) for w in s["palavras"]]
# a palavra entra quando ela fala de verdade (o Whisper adianta depois das pausas)
trechos = trechos_de_fala(AQUI / "assets" / "video" / "original.mov")
ant = -1.0
for w in ws:
    w["s"] = round(max(inicio_corrigido(w["s"], trechos), ant + 0.06), 3)
    ant = w["s"]


def texto(w):
    """Como na referência B: minúsculas, sem pontuação; "hipdips" do Whisper vira "hip dips"."""
    t = re.sub(r"[.,:;!?]", "", w["t"]).lower()
    return "hip dips" if t == "hipdips" else t


def n(x):
    return f"{x:.3f}".rstrip("0").rstrip(".")


def plano_em(t):
    return next(p for a, b, p, _ in PLANOS if a <= t < b)


# ── legendas (referência B) ───────────────────────────────────────────────────────────────────────
assert [f[0][0] for f in FRASES[1:]] == [f[-1][1] + 1 for f in FRASES[:-1]] and FRASES[-1][-1][1] == len(ws) - 1
grupos = []
for k, linhas in enumerate(FRASES):
    ini = ws[linhas[0][0]]["s"]
    ult = ws[linhas[-1][1]]
    prox = ws[FRASES[k + 1][0][0]]["s"] if k + 1 < len(FRASES) else DUR
    fim = prox if prox - ult["e"] < 0.7 else round(ult["e"] + 0.35, 3)
    com_foto = FOTO_PAR[0] - 0.05 <= ini < FOTO_PAR[1] or FOTO_UNICA[0] - 0.05 <= ini < FOTO_UNICA[1]
    y = ALTURA_COM_FOTO if com_foto else ALTURA[plano_em(ini)]
    # as linhas finas seguidas ficam na mesma linha; um estilo grande vai numa linha própria, embaixo
    blocos = []
    for a, b, est in linhas:
        pal = [{"t": texto(ws[i]), "s": ws[i]["s"]} for i in range(a, b + 1)]
        if est in GRANDES or not blocos or blocos[-1]["grande"]:
            blocos.append({"grande": est in GRANDES, "trechos": []})
        blocos[-1]["trechos"].append({"estilo": est, "palavras": pal})
    grupos.append({"id": f"l{k + 1}", "ini": ini, "fim": round(min(fim, DUR), 3), "y": y, "blocos": blocos})
(AQUI / "legendas-ref.json").write_text(json.dumps(grupos, ensure_ascii=False, indent=1))

html_l, js_l = [], []
cont = 0                        # id de cada palavra (um contador próprio: pelo tamanho da lista de animações,
for g in grupos:                # as palavras das linhas grandes, que não têm animação própria, repetiam id)
    linhas_html = []
    for bi, bl in enumerate(g["blocos"]):
        spans = []
        for tr in bl["trechos"]:
            for j, p in enumerate(tr["palavras"]):
                cont += 1
                pid = f'{g["id"]}w{cont}'
                spans.append(f'<span class="w {tr["estilo"]}" id="{pid}">{p["t"]}</span>')
                if bl["grande"]:
                    if j == 0:     # a linha grande entra inteira, do desfoque, na primeira palavra dela
                        js_l.append(f'tl.fromTo("#{g["id"]}b{bi}", {{opacity:0, scale:0.94, filter:"blur(14px)"}}, '
                                    f'{{opacity:1, scale:1, filter:"blur(0px)", duration:0.32, ease:"power2.out"}}, {n(p["s"])});')
                else:              # as finas entram palavra por palavra, do desfoque
                    js_l.append(f'tl.fromTo("#{pid}", {{opacity:0, y:8, filter:"blur(10px)"}}, '
                                f'{{opacity:1, y:0, filter:"blur(0px)", duration:0.28, ease:"power2.out"}}, {n(p["s"])});')
        cls = "linha grande-l" if bl["grande"] else "linha"
        linhas_html.append(f'<div class="{cls}" id="{g["id"]}b{bi}">{" ".join(spans)}</div>')
    html_l.append(f'<div class="g" id="{g["id"]}" style="top:{g["y"]}px">{"".join(linhas_html)}</div>')
    js_l += [f'tl.set("#{g["id"]}", {{opacity:1}}, {n(g["ini"])});', f'tl.set("#{g["id"]}", {{opacity:0}}, {n(g["fim"])});']

FONTES = """
    @font-face { font-family: "Montserrat Ref"; font-weight: 100 900; font-style: normal; src: url("assets/fonts/Montserrat-VF.ttf"); }
    @font-face { font-family: "Playfair Ref"; font-weight: 400 900; font-style: italic; src: url("assets/fonts/PlayfairDisplay-Italic-VF.ttf"); }"""


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


css_l = """    .g { position: absolute; left: 60px; width: 960px; opacity: 0; transform: translateY(-50%); text-align: center;
         color: #FFFFFF; text-shadow: 0 1px 2px rgba(20, 12, 8, 0.45), 0 2px 18px rgba(20, 12, 8, 0.5); }
    .linha { font-family: "Montserrat Ref"; font-size: 42px; line-height: 1.15; letter-spacing: -0.005em; }
    .grande-l { margin-top: -2px; line-height: 1.05; }
    .w { display: inline-block; }
    .fina { font-weight: 300; }
    .negrito { font-weight: 700; }
    .grande { font-family: "Montserrat Ref"; font-weight: 800; font-size: 62px; letter-spacing: -0.02em; }
    .creme { font-family: "Montserrat Ref"; font-weight: 800; font-size: 62px; letter-spacing: -0.02em; color: #EED6A4; }
    .serifa { font-family: "Playfair Ref"; font-style: italic; font-weight: 500; font-size: 72px; color: #F1DDB2; letter-spacing: 0; }"""
(AQUI / "compositions" / "legendas-ref.html").write_text(
    composicao("legendas-ref", css_l, "    " + "\n    ".join(html_l), js_l))

# ── fotos (referência A) ──────────────────────────────────────────────────────────────────────────
F = "assets/fotos/faixas/"
fotos_html = f"""    <img id="faixa" class="foto" src="{F}banda-antes.jpg" alt="">
    <div id="par" class="par"><img src="{F}par-antes.jpg" alt=""><i></i><img src="{F}par-depois.jpg" alt=""></div>
    <img id="unica" class="foto unica" src="{F}unica-antes2.jpg" alt="">
    <div id="cheia" class="cheia"><img id="cheia-img" src="{F}cheia-depois2.jpg" alt=""></div>"""
css_f = """    .foto, .par, .cheia { position: absolute; opacity: 0; }
    #faixa { left: 0; top: 0; width: 1080px; height: 560px; object-fit: cover; }
    .par { left: 100px; top: 1185px; width: 880px; height: 373px; display: flex; background: #FFFFFF; }
    .par img { width: 438px; height: 373px; object-fit: cover; display: block; }
    .par i { width: 4px; flex: none; }
    .unica { left: 150px; top: 1160px; width: 780px; height: 503px; object-fit: cover; border-radius: 26px; }
    .cheia { left: 0; top: 0; width: 1080px; height: 1920px; overflow: hidden; }
    .cheia img { width: 1080px; height: 1920px; object-fit: cover; transform-origin: 50% 50%; }"""
js_f = [
    # a faixa do antes no alto já está lá desde o primeiro quadro, como na referência A, e sai seca
    f'tl.set("#faixa", {{opacity:1}}, 0);', f'tl.set("#faixa", {{opacity:0}}, {n(FOTO_FAIXA[1])});',
    # o par cresce de leve ao entrar e sai seco
    f'tl.fromTo("#par", {{opacity:0, scale:0.84}}, {{opacity:1, scale:1, duration:0.4, ease:"power2.out"}}, {n(FOTO_PAR[0])});',
    f'tl.set("#par", {{opacity:0}}, {n(FOTO_PAR[1])});',
    # a foto única entra saindo do desfoque
    f'tl.fromTo("#unica", {{opacity:0, scale:1.05, filter:"blur(16px)"}}, {{opacity:1, scale:1, filter:"blur(0px)", '
    f'duration:0.5, ease:"power2.out"}}, {n(FOTO_UNICA[0])});',
    f'tl.set("#unica", {{opacity:0}}, {n(FOTO_UNICA[1] + 0.45)});',
    # o resultado em tela cheia esmaece por cima da foto única e se aproxima devagar
    f'tl.fromTo("#cheia", {{opacity:0, filter:"blur(12px)"}}, {{opacity:1, filter:"blur(0px)", duration:0.45, ease:"sine.inOut"}}, '
    f'{n(FOTO_CHEIA[0])});',
    f'tl.fromTo("#cheia-img", {{scale:1}}, {{scale:1.06, duration:{FOTO_CHEIA[1] - FOTO_CHEIA[0]:.2f}, ease:"none"}}, {n(FOTO_CHEIA[0])});',
    f'tl.set("#cheia", {{opacity:0}}, {n(FOTO_CHEIA[1])});',
]
(AQUI / "compositions" / "fotos-ref.html").write_text(composicao("fotos-ref", css_f, fotos_html, js_f))

# ── sons ──────────────────────────────────────────────────────────────────────────────────────────
sons = [{"t": a, "som": "impacto", "vol": 0.22} for a, b, p, ef in PLANOS if ef == "pb"]     # o drama entra com um grave
sons += [{"t": FOTO_PAR[0], "som": "whoosh-rapido", "vol": 0.2}, {"t": FOTO_UNICA[0], "som": "whoosh-rapido", "vol": 0.2},
         {"t": FOTO_CHEIA[0], "som": "brilho", "vol": 0.18}]

plano = {
    "video": "assets/video/video.mp4",
    "video_original": "assets/video/original.mov",
    "video_tem_audio": True,
    "duracao": DUR,
    "cores": {"texto": "#FFFFFF", "destaque": "#FFFFFF", "destaque_escuro": "#FFFFFF", "brilho": False, "vazamento": "#FF8A3D"},
    "legendas": [],
    "fotos": [],
    "transicoes": TRANSICOES,
    "extras": [{"id": "fotos-ref", "src": "compositions/fotos-ref.html", "z": 5},
               {"id": "legendas-ref", "src": "compositions/legendas-ref.html", "z": 7}],
    "sfx_extra": sons,
}
(AQUI / "plano.json").write_text(json.dumps(plano, ensure_ascii=False, indent=1))
subprocess.run(["python3", str(SCRIPTS / "gerar.py"), str(AQUI)], check=True)
print(f"ok: {len(grupos)} frases, {len(PLANOS)} planos, {len(sons)} sons")
