"""Monta a edição do Caso de paciente, 2ª versão, nas referências (veja roteiro.py): escreve as camadas
compositions/legendas-ref.html (legendas da referência B) e compositions/fotos-ref.html (antes e depois da
referência A), o plano.json e roda o gerar.py.

Uso: python3 cortar_fotos.py; python3 montar_video.py; python3 montar_plano.py   (na pasta do projeto)

A 1ª versão (legendas Poppins no top dela, o antes atrás dela com recorte, cards inclinados, tela dividida e
flash branco) a cliente recusou: "até agora você não fez nenhum vídeo com base nas referências". Na 2ª, tudo
saiu das duas referências que ela mandou. Na 3ª (17/11) ela tirou o color grade (cor original), trocou a letra
por Poppins com as letras juntas (o bege das palavras que pesam ela gostou), pediu mais efeitos sonoros e
notou a foto tremendo (o zoompan; veja montar_video.py). Na 4ª, as legendas iguais às da referência B, só que
em Poppins (veja LEGENDAS no roteiro.py), e a cor igual à que ela mandou. A voz e a música do vídeo continuam as
do original.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

from PIL import ImageFont

from roteiro import (BASE_COM_FOTO, BASE_LEGENDA, FOTO_CHEIA, FOTO_FAIXA, FOTO_PAR, FOTO_UNICA, LEGENDAS, PLANOS,
                     TEXTO, TOTAL, TRANSICOES)

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


def texto(i):
    """Como na referência B: minúsculas (só a primeira palavra do vídeo com maiúscula), sem ponto final; as vírgulas
    da fala ficam (4ª versão: "você não colocou vírgulas em alguns lugares")."""
    if i in TEXTO:
        return TEXTO[i]
    t = re.sub(r"[.;:!?]+$", "", ws[i]["t"])
    return t if i == 0 else t.lower()


def n(x):
    return f"{x:.3f}".rstrip("0").rstrip(".")


def plano_em(t):
    return next(p for a, b, p, _ in PLANOS if a <= t < b)


# ── legendas (referência B, em Poppins; veja LEGENDAS no roteiro.py) ─────────────────────────────────
TAM_FINA, TAM_FORTE, TAM_SERIFA, BEGE_MAX, LARGURA = 45, 58, 84, 78, 700   # bege: ~1,75x a fina e até 65% da largura, como na referência
# 5ª versão (17/11): "eu gosto muito da estética quando as letras ficam mais juntinhas" e "o espaçamento entre linhas
# pode diminuir também": letras juntas como na 3ª versão e entrelinha apertada (na 3ª ela já tinha pedido isso: li
# "espaçamento entre linhas bem diminuído" como reclamação e abri para 1,45 na 4ª)
TRACK_FINA, TRACK_NEGRITO, TRACK_BEGE = -0.045, -0.04, -0.05
ENTRELINHA = 1.08
FONTE_BEGE = ImageFont.truetype(str(AQUI / "assets" / "fonts" / "Poppins-800.ttf"), 100)


def tamanho_bege(txt):
    """A palavra bege o maior possível (até BEGE_MAX px) sem passar da largura."""
    larg100 = FONTE_BEGE.getlength(txt) + TRACK_BEGE * 100 * (len(txt) - 1)
    return min(BEGE_MAX, int(LARGURA * 100 / larg100))


assert [l[0][0][0] for l in LEGENDAS[1:]] == [l[-1][-1][1] + 1 for l in LEGENDAS[:-1]] and LEGENDAS[-1][-1][-1][1] == len(ws) - 1
grupos = []
for k, linhas in enumerate(LEGENDAS):
    pri, ult = linhas[0][0][0], linhas[-1][-1][1]
    ini = ws[pri]["s"]
    prox = ws[LEGENDAS[k + 1][0][0][0]]["s"] if k + 1 < len(LEGENDAS) else DUR
    fim = prox if prox - ws[ult]["e"] < 0.7 else round(ws[ult]["e"] + 0.35, 3)
    com_foto = FOTO_PAR[0] - 0.05 <= ini < FOTO_PAR[1] or FOTO_UNICA[0] - 0.05 <= ini < FOTO_UNICA[1]
    lins = []
    for trechos_l in linhas:
        est = trechos_l[0][2] if len(trechos_l) == 1 and trechos_l[0][2] in "Fbs" else "f"
        lins.append({"estilo": est, "s": ws[trechos_l[0][0]]["s"],
                     "trechos": [{"estilo": e, "texto": " ".join(texto(i) for i in range(a, b + 1))} for a, b, e in trechos_l]})
    grupos.append({"id": f"l{k + 1}", "ini": ini, "fim": round(min(fim, DUR), 3),
                   "base": BASE_COM_FOTO if com_foto else BASE_LEGENDA, "linhas": lins})
(AQUI / "legendas-ref.json").write_text(json.dumps(grupos, ensure_ascii=False, indent=1))

html_l, js_l = [], []
for g in grupos:
    linhas_html = []
    for li, l in enumerate(g["linhas"]):
        lid = f'{g["id"]}x{li}'
        if l["estilo"] == "b":
            txt = l["trechos"][0]["texto"]
            linhas_html.append(f'<div class="ln bege" id="{lid}" style="font-size:{tamanho_bege(txt)}px">{txt}</div>')
        elif l["estilo"] in "Fs":
            cls = {"F": "forte", "s": "serifa"}[l["estilo"]]
            linhas_html.append(f'<div class="ln {cls}" id="{lid}">{l["trechos"][0]["texto"]}</div>')
        else:
            spans = " ".join(f'<span class="{"n" if t["estilo"] == "n" else "f"}">{t["texto"]}</span>' for t in l["trechos"])
            linhas_html.append(f'<div class="ln" id="{lid}">{spans}</div>')
        atraso = l["s"] - g["ini"] > 0.08
        if l["estilo"] == "F":       # a frase forte entra com um borrão de lado, como "prevenção" na referência
            js_l.append(f'tl.fromTo("#{lid}", {{opacity:0, x:-40, filter:"blur(10px)"}}, '
                        f'{{opacity:1, x:0, filter:"blur(0px)", duration:0.2, ease:"power2.out"}}, {n(l["s"])});')
        elif atraso:                 # a palavra grande entra seca quando ela fala, como "complexos" na referência
            js_l += [f'tl.set("#{lid}", {{opacity:0}}, {n(g["ini"])});', f'tl.set("#{lid}", {{opacity:1}}, {n(l["s"])});']
    html_l.append(f'<div class="g" id="{g["id"]}" style="top:{g["base"]}px">{"".join(linhas_html)}</div>')
    js_l += [f'tl.set("#{g["id"]}", {{opacity:1}}, {n(g["ini"])});', f'tl.set("#{g["id"]}", {{opacity:0}}, {n(g["fim"])});']

FONTES = """
    @font-face { font-family: "Poppins Ref"; font-weight: 300; font-style: italic; src: url("assets/fonts/Poppins-300i.ttf"); }
    @font-face { font-family: "Poppins Ref"; font-weight: 800; font-style: italic; src: url("assets/fonts/Poppins-800i.woff2") format("woff2"); }
    @font-face { font-family: "Poppins Ref"; font-weight: 800; font-style: normal; src: url("assets/fonts/Poppins-800.ttf"); }
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


# um padrão só de cor (5ª versão: "uma hora a fonte tá bege, na outra tá branca, não tem um padrão"): a fala
# sempre branca; tudo o que pesa sempre bege (o negrito dentro da frase, a frase forte e a palavra grande), com a
# sombra no tom escuro do próprio bege (regra do cliente: palavra colorida nunca leva sombra preta)
BEGE = "#EED6A4"


def sombra_da_cor(hexa, alfa):
    import colorsys
    r, g, b = (int(hexa[i:i + 2], 16) / 255 for i in (1, 3, 5))
    h, l, s_ = colorsys.rgb_to_hls(r, g, b)
    r, g, b = colorsys.hls_to_rgb(h, 0.2, min(1.0, s_ + 0.1))
    return f"rgba({round(r * 255)}, {round(g * 255)}, {round(b * 255)}, {alfa})"


SOMBRA_BEGE = f"0 1px 3px {sombra_da_cor(BEGE, 0.55)}, 0 2px 16px {sombra_da_cor(BEGE, 0.45)}"
css_l = f"""    .g {{ position: absolute; left: 40px; width: 1000px; opacity: 0; transform: translateY(-100%); text-align: center;
         color: #FFFFFF; text-shadow: 0 1px 3px rgba(20, 12, 8, 0.4), 0 2px 16px rgba(20, 12, 8, 0.4); }}
    .ln {{ font-family: "Poppins Ref"; font-style: italic; font-weight: 300; font-size: {TAM_FINA}px; line-height: {ENTRELINHA};
          letter-spacing: {TRACK_FINA}em; white-space: nowrap; }}
    .ln .n {{ font-weight: 800; letter-spacing: {TRACK_NEGRITO}em; color: {BEGE}; text-shadow: {SOMBRA_BEGE}; }}
    .ln.forte {{ font-weight: 800; font-size: {TAM_FORTE}px; line-height: {ENTRELINHA}; letter-spacing: {TRACK_NEGRITO}em;
                color: {BEGE}; text-shadow: {SOMBRA_BEGE}; }}
    .ln.bege {{ font-style: normal; font-weight: 800; line-height: 0.98; letter-spacing: {TRACK_BEGE}em; color: {BEGE};
               text-shadow: {SOMBRA_BEGE}; }}
    .ln.serifa {{ font-family: "Playfair Ref"; font-weight: 400; font-size: {TAM_SERIFA}px; line-height: 1.1; letter-spacing: 0; }}"""
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
# 3ª versão (17/11: "senti falta de efeitos sonoros"): na 2ª eram poucos e a 0,2–0,3, e o mixar.py ainda baixa os
# efeitos 14 dB, porque a voz dela foi gravada 14 dB abaixo da do André (os efeitos acompanham a voz): quase não se
# ouviam. Agora há um som em cada evento, como na referência B, num volume que aparece por baixo da voz. Ordem de
# prioridade: transições, P&B, fotos, trocas de plano, palavras que pesam; dois sons nunca a menos de 0,4 s.
candidatos = [(t["t"], "transicao", None) for t in TRANSICOES]          # o gerar.py põe o whoosh delas
candidatos.append((TRANSICOES[0]["t"], "brilho", 0.55))                  # o clarão que tira do 1º P&B
for k in range(1, len(PLANOS)):
    a, _, p, ef = PLANOS[k]
    if ef == "pb":
        candidatos.append((a, "impacto", 0.9))                           # o drama entra com um grave
    elif ef == "volta":
        candidatos.append((a, "whoosh-grave", 0.6))                      # e a cor volta com um sopro grave
for t, som, vol in [(FOTO_PAR[0], "whoosh-rapido", 0.7), (FOTO_PAR[0] + 0.4, "click", 0.6),
                    (FOTO_UNICA[0] + 0.3, "click", 0.6), (FOTO_CHEIA[0], "brilho", 0.7)]:
    candidatos.append((t, som, vol))
for k in range(1, len(PLANOS)):
    a, _, p, ef = PLANOS[k]
    if ef in ("pb", "volta") or p == PLANOS[k - 1][2]:
        continue
    if p == "foto":
        candidatos.append((a, "whoosh-rapido", 0.7))                     # a foto que a cliente pôs
    elif p == "f":
        candidatos.append((a, "whoosh-rapido", 0.5))                     # zoom in
    else:
        candidatos.append((a, "whoosh", 0.4))                            # zoom out
entradas = [l["s"] for g in grupos for l in g["linhas"] if l["estilo"] in "Fbs"]
for t in entradas[:-1]:
    candidatos.append((t, "click-agudo", 0.7))                           # a palavra que pesa
candidatos.append((entradas[-1], "brilho", 0.6))                         # "cada paciente", no fim
aceitos = []
for t, som, vol in candidatos:
    if all(abs(t - x[0]) >= 0.4 or (som == "click" and x[1] == "whoosh-rapido" and t - x[0] >= 0.39)
           or (som == "brilho" and x[1] == "transicao") for x in aceitos):
        aceitos.append((t, som, vol))
sons = [{"t": round(t, 3), "som": som, "vol": vol} for t, som, vol in sorted(aceitos) if som != "transicao"]

plano = {
    "video": "assets/video/video.mp4",
    "video_original": "assets/video/original.mov",
    "video_tem_audio": True,          # o som do original vai junto no vídeo-base (o HyperFrames pede); a mixagem lê a voz do original
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
