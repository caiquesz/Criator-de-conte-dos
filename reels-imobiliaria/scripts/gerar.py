"""Gera a composição HyperFrames de um Reels a partir do plano de edição.

Uso: python3 scripts/gerar.py PASTA_DO_PROJETO

Lê PASTA/plano.json e escreve:
  index.html                  vídeo, recorte da pessoa, transições, efeitos sonoros
  compositions/legendas.html  legendas palavra a palavra (trilha de legendas)
  compositions/cards.html     cards em liquid glass

Formato do plano.json: veja o README.md da pasta reels-imobiliaria.
"""

import html
import json
import sys
from pathlib import Path

from PIL import ImageFont

RAIZ = Path(__file__).resolve().parent.parent
FONTES = RAIZ / "template" / "assets" / "fonts"

LARGURA, ALTURA = 1080, 1920
LARGURA_MAX = 880  # largura máxima de uma linha de legenda (dentro da área segura)
FPS = 30

# estilos de palavra: fonte, peso, itálico, tamanho base (px em 1080 de largura)
ESTILOS = {
    "fina":     {"familia": "Poppins Reels", "peso": 300, "italico": False, "tam": 62,  "arquivo": "Poppins-300.ttf"},
    "fina-it":  {"familia": "Poppins Reels", "peso": 300, "italico": True,  "tam": 62,  "arquivo": "Poppins-300i.ttf"},
    "media":    {"familia": "Poppins Reels", "peso": 600, "italico": False, "tam": 84,  "arquivo": "Poppins-600.ttf"},
    "forte":    {"familia": "Poppins Reels", "peso": 700, "italico": False, "tam": 112, "arquivo": "Poppins-700.ttf"},
    "pesada":   {"familia": "Poppins Reels", "peso": 800, "italico": False, "tam": 132, "arquivo": "Poppins-800.ttf"},
    "destaque": {"familia": "Poppins Reels", "peso": 800, "italico": False, "tam": 120, "arquivo": "Poppins-800.ttf", "cor": "destaque"},
    "serifa":   {"familia": "Instrument Serif", "peso": 400, "italico": True, "tam": 172, "arquivo": "InstrumentSerif-400i.ttf", "cor": "destaque"},
}

# onde cai o pico de cada efeito sonoro (s), medido com `hyperframes audio`
DURACAO_SFX = {
    "click": 0.366, "click-agudo": 0.34, "click-tecla": 0.432, "pop": 0.72,
    "whoosh": 0.575, "whoosh-grave": 0.731, "whoosh-rapido": 0.549, "whoosh-transicao": 1.944,
}
PICO_SFX = {
    "click": 0.073, "click-agudo": 0.062, "click-tecla": 0.076, "pop": 0.12,
    "whoosh": 0.162, "whoosh-grave": 0.197, "whoosh-rapido": 0.14, "whoosh-transicao": 0.803,
}
CLIQUES = ["click", "click-agudo", "click"]
WHOOSH_TRANSICAO = ["whoosh-transicao", "whoosh-grave"]


def esc(t):
    return html.escape(str(t), quote=True)


def num(x):
    return f"{x:.3f}".rstrip("0").rstrip(".")


def tracking_em(estilo, plano):
    t = plano.get("tracking", {})
    if estilo in ("fina", "fina-it"):
        return t.get("fina", -0.01)
    if estilo == "serifa":
        return t.get("serifa", -0.01)
    return t.get("forte", -0.035)


def largura_linha(texto, estilo, tam, plano):
    e = ESTILOS[estilo]
    fonte = ImageFont.truetype(str(FONTES / e["arquivo"]), tam)
    return fonte.getlength(texto) + tracking_em(estilo, plano) * tam * len(texto)


def tamanho_linha(linha, plano):
    """Tamanho final da linha: o do estilo (ou o pedido), reduzido até caber."""
    estilo = linha.get("estilo", "fina")
    tam = linha.get("tam", ESTILOS[estilo]["tam"])
    texto = " ".join(p["t"] for p in linha["palavras"])
    while tam > 36 and largura_linha(texto, estilo, tam, plano) > LARGURA_MAX:
        tam -= 2
    return tam


def font_faces():
    return """
      @font-face { font-family: "Poppins Reels"; font-weight: 300; font-style: normal; src: url("assets/fonts/Poppins-300.ttf"); }
      @font-face { font-family: "Poppins Reels"; font-weight: 300; font-style: italic; src: url("assets/fonts/Poppins-300i.ttf"); }
      @font-face { font-family: "Poppins Reels"; font-weight: 400; font-style: normal; src: url("assets/fonts/Poppins-400.ttf"); }
      @font-face { font-family: "Poppins Reels"; font-weight: 600; font-style: normal; src: url("assets/fonts/Poppins-600.ttf"); }
      @font-face { font-family: "Poppins Reels"; font-weight: 700; font-style: normal; src: url("assets/fonts/Poppins-700.ttf"); }
      @font-face { font-family: "Poppins Reels"; font-weight: 800; font-style: normal; src: url("assets/fonts/Poppins-800.ttf"); }
      @font-face { font-family: "Instrument Serif"; font-weight: 400; font-style: italic; src: url("assets/fonts/InstrumentSerif-400i.ttf"); }
      @font-face { font-family: "Instrument Serif"; font-weight: 400; font-style: normal; src: url("assets/fonts/InstrumentSerif-400.ttf"); }"""


# ── legendas ────────────────────────────────────────────────────────────────

def entrada_palavra(estilo):
    """De onde cada estilo entra (sempre com desfoque, como nas referências)."""
    if estilo == "serifa":
        return {"opacity": 0, "filter": "blur(16px)", "y": 14, "scale": 1.14}
    if estilo in ("forte", "pesada", "destaque", "media"):
        return {"opacity": 0, "filter": "blur(14px)", "x": -28, "scale": 1.04}
    return {"opacity": 0, "filter": "blur(12px)", "y": 18}


def gerar_legendas(plano, duracao):
    grupos_html, js = [], []
    for g in plano.get("legendas", []):
        gid = g["id"]
        palavras = [p for l in g["linhas"] for p in l["palavras"]]
        inicio = min(p["s"] for p in palavras) - 0.02
        fim = g["fim"]
        alinhar = g.get("alinhar", "centro")
        estilo_bloco = f"top:{g['y']}px;"
        if alinhar == "esquerda":
            estilo_bloco += f"text-align:left;padding-left:{g.get('x', 110)}px;"
        elif alinhar == "direita":
            estilo_bloco += f"text-align:right;padding-right:{g.get('x', 110)}px;"
        linhas_html = []
        for li, linha in enumerate(g["linhas"]):
            estilo = linha.get("estilo", "fina")
            e = ESTILOS[estilo]
            tam = tamanho_linha(linha, plano)
            cor = linha.get("cor", e.get("cor", "texto"))
            css = (f"font-family:'{e['familia']}';font-weight:{e['peso']};"
                   f"font-style:{'italic' if e['italico'] else 'normal'};font-size:{tam}px;"
                   f"letter-spacing:{tracking_em(estilo, plano)}em;color:var(--{cor});")
            if li:
                css += f"margin-top:{plano.get('entrelinha', -0.16)}em;"
            if linha.get("dx"):  # desloca a linha (layout escalonado da referência 1)
                css += f"position:relative;left:{linha['dx']}px;"
            spans = []
            for pi, p in enumerate(linha["palavras"]):
                pid = f"{gid}-l{li}-p{pi}"
                spans.append(f'<span class="p" id="{pid}">{esc(p["t"])}</span>')
                js.append(f'tl.fromTo("#{pid}", {json.dumps(entrada_palavra(estilo))}, '
                          f'{{opacity:1, filter:"blur(0px)", x:0, y:0, scale:1, duration:0.34, ease:"power3.out"}}, {num(p["s"])});')
            classe = "linha brilho" if cor.startswith("destaque") else "linha"
            linhas_html.append(f'<div class="{classe}" id="{gid}-l{li}" style="{css}">{" ".join(spans)}</div>')
        # saída: linha a linha, subindo e desfocando (como na referência 2). Na fala
        # corrida a última palavra fica pelo menos 0,32 s parada antes de sair, mesmo
        # que a saída invada o começo do grupo seguinte (como na referência 2)
        n = len(g["linhas"])
        saida = 0.26
        ultima = max(p["s"] for p in palavras)
        inicio_saida = max(fim - saida - 0.05 * (n - 1) - 0.02, ultima + 0.32)
        fim = max(fim, inicio_saida + saida + 0.05 * (n - 1) + 0.02)
        js.append(f'tl.to([{", ".join(chr(34) + "#" + gid + "-l" + str(i) + chr(34) for i in range(n))}], '
                  f'{{opacity:0, filter:"blur(12px)", y:-26, duration:{saida}, ease:"power2.in", stagger:0.05}}, {num(inicio_saida)});')
        classe_grupo = "clip grupo sombra-forte" if g.get("sombra_forte") else "clip grupo"
        grupos_html.append(
            f'<div id="{gid}" class="{classe_grupo}" data-start="{num(inicio)}" data-duration="{num(fim - inicio)}" '
            f'data-layout-allow-overlap style="{estilo_bloco}">\n        ' + "\n        ".join(linhas_html) + "\n      </div>")

    return f"""<template>
  <style>{font_faces()}
      #root {{ position: absolute; inset: 0; overflow: visible; }}
      .grupo {{ position: absolute; left: 0; width: {LARGURA}px; text-align: center; overflow: visible; isolation: isolate; }}
      .linha {{ position: relative; display: block; white-space: nowrap; line-height: 1.0; color: #fff;
               text-shadow: 0 1px 3px rgba(0, 0, 0, 0.30), 0 3px 18px rgba(0, 0, 0, 0.36); }}
      .linha.brilho {{ text-shadow: 0 1px 3px rgba(0, 0, 0, 0.32), 0 4px 26px rgba(0, 0, 0, 0.40), 0 0 40px var(--destaque-brilho); }}
      /* fundo muito claro: a sombra fica nas próprias letras, mais firme e mais justa */
      .sombra-forte .linha, .sombra-forte .linha.brilho {{
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.55), 0 2px 8px rgba(0, 0, 0, 0.45), 0 4px 22px rgba(0, 0, 0, 0.35); }}
      .p {{ display: inline-block; will-change: transform, filter, opacity; }}
  </style>
  <div id="root" data-composition-id="legendas" data-width="{LARGURA}" data-height="{ALTURA}">
      {chr(10).join("      " + h for h in grupos_html).strip()}
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
    tl.to({{}}, {{ duration: {num(duracao)} }}, 0);
    {(chr(10) + "    ").join(js)}
    window.__timelines["legendas"] = tl;
  </script>
</template>
"""


# ── cards em liquid glass ───────────────────────────────────────────────────

def gerar_cards(plano, duracao):
    cards_html, js = [], []
    for c in plano.get("cards", []):
        cid = c["id"]
        ini, fim = c["inicio"], c["fim"]
        unidade = f'<span class="card-unidade">{esc(c["unidade"])}</span>' if c.get("unidade") else ""
        rotulo = f'<div class="card-rotulo" id="{cid}-r">{esc(c["rotulo"])}</div>' if c.get("rotulo") else ""
        cards_html.append(
            f'<div id="{cid}" class="clip card" data-start="{num(ini)}" data-duration="{num(fim - ini)}" style="top:{c["y"]}px">\n'
            f'        <div class="vidro" id="{cid}-v">\n'
            f'          <div class="vidro-brilho"></div>\n'
            f'          <div class="card-grande" id="{cid}-g">{esc(c["grande"])}{unidade}</div>\n'
            f'          {rotulo}\n'
            f'        </div>\n      </div>')
        # o vidro entra sem filter (filter no ancestral desliga o backdrop-filter)
        js.append(f'tl.fromTo("#{cid}-v", {{opacity:0, y:46, scale:0.88}}, {{opacity:1, y:0, scale:1, duration:0.55, ease:"expo.out"}}, {num(ini)});')
        js.append(f'tl.fromTo("#{cid}-g", {{opacity:0, filter:"blur(14px)", y:12}}, {{opacity:1, filter:"blur(0px)", y:0, duration:0.4, ease:"power3.out"}}, {num(ini + 0.12)});')
        if c.get("rotulo"):
            js.append(f'tl.fromTo("#{cid}-r", {{opacity:0, filter:"blur(8px)", y:10}}, {{opacity:1, filter:"blur(0px)", y:0, duration:0.5, ease:"power3.out"}}, {num(ini + 0.22)});')
        js.append(f'tl.to("#{cid}-v", {{opacity:0, y:-24, scale:0.96, duration:0.3, ease:"power2.in"}}, {num(fim - 0.32)});')

    return f"""<template>
  <style>{font_faces()}
      #root {{ position: absolute; inset: 0; }}
      .card {{ position: absolute; left: 0; width: {LARGURA}px; display: flex; justify-content: center; }}
      .vidro {{
        position: relative; overflow: hidden; text-align: center;
        padding: 30px 64px 36px; border-radius: 48px;
        background: linear-gradient(140deg, rgba(255, 255, 255, 0.26), rgba(255, 255, 255, 0.07) 48%, rgba(255, 255, 255, 0.14)),
                    rgba(18, 18, 22, 0.14);
        -webkit-backdrop-filter: blur(24px) saturate(180%);
        backdrop-filter: blur(24px) saturate(180%);
        border: 1.5px solid rgba(255, 255, 255, 0.42);
        box-shadow: inset 0 2px 0 rgba(255, 255, 255, 0.7), inset 0 -2px 0 rgba(255, 255, 255, 0.14),
                    inset 0 -22px 44px rgba(255, 255, 255, 0.08), 0 26px 70px rgba(0, 0, 0, 0.30);
      }}
      .vidro-brilho {{
        position: absolute; inset: 0; pointer-events: none; border-radius: inherit;
        background: radial-gradient(130% 70% at 18% -10%, rgba(255, 255, 255, 0.42), transparent 58%),
                    radial-gradient(90% 60% at 100% 120%, rgba(255, 255, 255, 0.16), transparent 60%);
      }}
      .card-grande {{
        position: relative; font-family: "Instrument Serif"; font-style: italic; font-weight: 400;
        font-size: 150px; line-height: 0.95; letter-spacing: -0.01em; color: #fff;
        text-shadow: 0 2px 18px rgba(0, 0, 0, 0.18);
      }}
      .card-unidade {{ color: var(--destaque); margin-left: 0.08em; }}
      .card-rotulo {{
        position: relative; margin-top: 6px; font-family: "Poppins Reels"; font-weight: 300;
        font-size: 28px; letter-spacing: 0.32em; text-transform: uppercase; color: rgba(255, 255, 255, 0.92);
        padding-left: 0.32em;
      }}
  </style>
  <div id="root" data-composition-id="cards" data-width="{LARGURA}" data-height="{ALTURA}">
      {chr(10).join("      " + h for h in cards_html).strip()}
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
    tl.to({{}}, {{ duration: {num(duracao)} }}, 0);
    {(chr(10) + "    ").join(js)}
    window.__timelines["cards"] = tl;
  </script>
</template>
"""


# ── raiz: vídeo, recorte, transições, sons ──────────────────────────────────

def eventos_sfx(plano):
    """Efeitos sonoros automáticos (clique nas legendas e cards, whoosh nas transições)."""
    ev = []
    fim_anterior, n_cliques = -10.0, 0
    for g in plano.get("legendas", []):
        primeira = min(p["s"] for l in g["linhas"] for p in l["palavras"])
        destaques = [l["palavras"][0]["s"] for l in g["linhas"]
                     if l.get("estilo", "fina") in ("serifa", "destaque")]
        # clique quando o texto volta depois de uma pausa; na fala corrida, só nos destaques
        if primeira - fim_anterior > 0.3 and not any(abs(d - primeira) < 0.15 for d in destaques):
            ev.append((primeira, CLIQUES[n_cliques % len(CLIQUES)], 0.5))
            n_cliques += 1
        for d in destaques:
            ev.append((d, "click-agudo", 0.6))
        fim_anterior = g["fim"]
    for c in plano.get("cards", []):
        ev.append((c["inicio"] + 0.08, "whoosh-rapido", 0.45))
        ev.append((c["inicio"] + 0.3, "click", 0.55))
    grandes = [t for t in plano.get("transicoes", []) if t.get("tipo", "luz") != "corte"]
    for i, t in enumerate(grandes):
        tipo = t.get("tipo", "luz")
        if tipo == "preto":
            ev.append((t["t"], "whoosh-grave", 0.5))
        elif tipo == "flash":
            ev.append((t["t"], "whoosh-rapido", 0.5))
        else:
            ev.append((t["t"], WHOOSH_TRANSICAO[i % len(WHOOSH_TRANSICAO)], 0.6))
    for s in plano.get("sfx_extra", []):
        ev.append((s["t"], s["som"], s.get("vol", 0.5)))
    remover = {round(s["t"], 2) for s in plano.get("sfx_remover", [])}
    ev = sorted(e for e in ev if round(e[0], 2) not in remover)
    # sem amontoado: logo depois de um whoosh de transição não entra outro whoosh nem
    # um clique colado, e dois cliques a menos de 0,2 s viram um só
    limpo = []
    for t, som, vol in ev:
        ultimo_whoosh = max((x[0] for x in limpo if x[1].startswith("whoosh")), default=-10)
        ultimo_clique = max((x[0] for x in limpo if x[1].startswith("click")), default=-10)
        if som.startswith("whoosh") and t - ultimo_whoosh < 0.5:
            continue
        if som.startswith("click") and (t - ultimo_whoosh < 0.2 or t - ultimo_clique < 0.2):
            continue
        limpo.append((t, som, vol))
    return limpo


def gerar_index(plano, duracao):
    video = plano["video"]
    tem_audio = plano.get("video_tem_audio", True)
    audio_attr = 'data-has-audio="true"' if tem_audio else "muted"
    recorte = plano.get("recorte")

    transicoes_html, js = [], []
    for i, t in enumerate(plano.get("transicoes", [])):
        tid = f"tr{i + 1}"
        tipo = t.get("tipo", "luz")
        corte = t["t"]
        if tipo == "corte":  # corte seco com um empurrão de câmera discreto
            escala = t.get("escala", 1.045)
            js.append(f'tl.fromTo(".cam", {{scale:{escala}}}, {{scale:1, duration:0.45, ease:"expo.out", immediateRender:false}}, {num(corte)});')
            continue
        if tipo == "luz":
            ini, dur = corte - 0.32, 0.8
            transicoes_html.append(
                f'<div id="{tid}" class="clip transicao luz" data-start="{num(ini)}" data-duration="{num(dur)}" '
                f'data-track-index="5" data-layout-ignore>\n'
                f'        <div class="vazamento ambar" id="{tid}-a"></div>\n'
                f'        <div class="vazamento quente" id="{tid}-b"></div>\n'
                f'        <div class="vazamento clarao" id="{tid}-c"></div>\n      </div>')
            js += [
                f'tl.fromTo("#{tid}-a", {{opacity:0, xPercent:-30, rotation:-6}}, {{opacity:1, xPercent:10, rotation:2, duration:0.42, ease:"sine.out"}}, {num(ini)});',
                f'tl.to("#{tid}-a", {{opacity:0, xPercent:30, duration:0.36, ease:"sine.in"}}, {num(ini + 0.42)});',
                f'tl.fromTo("#{tid}-b", {{opacity:0, xPercent:25, yPercent:-8}}, {{opacity:0.9, xPercent:-5, yPercent:4, duration:0.36, ease:"sine.out"}}, {num(ini + 0.06)});',
                f'tl.to("#{tid}-b", {{opacity:0, xPercent:-25, duration:0.38, ease:"sine.in"}}, {num(ini + 0.42)});',
                f'tl.fromTo("#{tid}-c", {{opacity:0}}, {{opacity:0.92, duration:0.1, ease:"power2.in"}}, {num(corte - 0.1)});',
                f'tl.to("#{tid}-c", {{opacity:0, duration:0.3, ease:"power2.out"}}, {num(corte + 0.02)});',
            ]
        elif tipo == "preto":
            ini, dur = corte - 0.2, 0.46
            transicoes_html.append(
                f'<div id="{tid}" class="clip transicao preto" data-start="{num(ini)}" data-duration="{num(dur)}" '
                f'data-track-index="5" data-layout-ignore><div class="cortina" id="{tid}-a"></div></div>')
            js += [
                f'tl.fromTo("#{tid}-a", {{opacity:0}}, {{opacity:1, duration:0.18, ease:"power2.in"}}, {num(ini)});',
                f'tl.to("#{tid}-a", {{opacity:0, duration:0.24, ease:"power2.out"}}, {num(corte + 0.02)});',
            ]
        else:  # flash branco
            ini, dur = corte - 0.08, 0.36
            transicoes_html.append(
                f'<div id="{tid}" class="clip transicao flash" data-start="{num(ini)}" data-duration="{num(dur)}" '
                f'data-track-index="5" data-layout-ignore><div class="cortina branca" id="{tid}-a"></div></div>')
            js += [
                f'tl.fromTo("#{tid}-a", {{opacity:0}}, {{opacity:0.9, duration:0.08, ease:"power2.in"}}, {num(ini)});',
                f'tl.to("#{tid}-a", {{opacity:0, duration:0.24, ease:"power2.out"}}, {num(corte + 0.02)});',
            ]
        if t.get("zoom", True):
            js.append(f'tl.fromTo(".cam", {{scale:1.09}}, {{scale:1, duration:0.6, ease:"expo.out", immediateRender:false}}, {num(corte)});')

    audios, fim_trilha = [], []
    for i, (t, som, vol) in enumerate(eventos_sfx(plano)):
        ini = max(0.0, t - PICO_SFX.get(som, 0.08) + 1 / FPS)
        dur = min(DURACAO_SFX.get(som, 1.0), duracao - ini)
        # primeira trilha livre (efeitos que se sobrepõem vão para trilhas diferentes)
        trilha = next((k for k, f in enumerate(fim_trilha) if f <= ini), len(fim_trilha))
        if trilha == len(fim_trilha):
            fim_trilha.append(0)
        fim_trilha[trilha] = ini + dur
        audios.append(f'<audio id="sfx{i + 1}" src="assets/sfx/{som}.mp3" data-start="{num(ini)}" '
                      f'data-duration="{num(dur)}" data-track-index="{10 + trilha}" data-volume="{vol}"></audio>')
    for i, m in enumerate(plano.get("musica", [])):
        audios.append(f'<audio id="musica{i + 1}" src="{esc(m["src"])}" data-start="{num(m.get("inicio", 0))}" '
                      f'data-media-start="{num(m.get("corte", 0))}" data-duration="{num(m.get("dur", duracao))}" '
                      f'data-track-index="9" data-volume="{m.get("vol", 0.14)}" data-fade-out="1.2"></audio>')

    recorte_html = ""
    if recorte:
        recorte_html = f"""
      <div class="cam" id="cam-recorte" style="z-index: 3">
        <video id="recorte" class="clip" src="{esc(recorte)}" data-start="0" data-media-start="0"
          data-duration="{num(duracao)}" data-track-index="1" muted playsinline data-layout-allow-occlusion></video>
      </div>"""

    cores = plano["cores"]
    return f"""<!doctype html>
<html lang="pt-BR" data-resolution="portrait">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={LARGURA}, height={ALTURA}" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <style>
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ margin: 0; width: {LARGURA}px; height: {ALTURA}px; overflow: hidden; background: #000; }}
      :root {{
        --texto: {cores.get("texto", "#FFFFFF")};
        --destaque: {cores["destaque"]};
        --destaque-brilho: {cores["destaque"]}59;
        --destaque-escuro: {cores.get("destaque_escuro", cores["destaque"])};
        --vazamento: {cores.get("vazamento", "#FF9A4D")};
      }}
      .cam {{ position: absolute; inset: 0; transform-origin: 50% 45%; }}
      .cam video {{ position: absolute; left: 0; top: 0; width: {LARGURA}px; height: {ALTURA}px; object-fit: cover; }}
      .transicao {{ position: absolute; inset: 0; z-index: 5; pointer-events: none; }}
      .transicao.luz {{ mix-blend-mode: screen; }}
      .vazamento {{ position: absolute; inset: -25%; opacity: 0; }}
      .vazamento.ambar {{
        background: radial-gradient(ellipse 50% 95% at 18% 55%, rgba(255, 244, 214, 0.95), transparent 46%),
                    radial-gradient(ellipse 75% 120% at 28% 50%, var(--vazamento), transparent 68%);
        filter: blur(30px);
      }}
      .vazamento.quente {{
        background: radial-gradient(ellipse 60% 100% at 78% 35%, rgba(255, 92, 60, 0.75), rgba(255, 60, 90, 0.25) 50%, transparent 76%);
        filter: blur(40px);
      }}
      .vazamento.clarao {{ background: radial-gradient(ellipse 90% 80% at 50% 45%, rgba(255, 248, 232, 1), rgba(255, 214, 160, 0.85) 55%, rgba(255, 170, 110, 0.6)); }}
      .cortina {{ position: absolute; inset: 0; background: #000; opacity: 0; }}
      .cortina.branca {{ background: #fff8ee; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{num(duracao)}"
      data-width="{LARGURA}" data-height="{ALTURA}">
      <div class="cam" id="cam-video" style="z-index: 1">
        <video id="video" class="clip" src="{esc(video)}" data-start="0" data-duration="{num(duracao)}"
          data-track-index="0" {audio_attr} playsinline></video>
      </div>

      <div id="legendas" data-composition-id="legendas" data-composition-src="compositions/legendas.html"
        data-start="0" data-duration="{num(duracao)}" data-track-index="2" data-track-kind="captions"
        data-width="{LARGURA}" data-height="{ALTURA}" style="z-index: 2"></div>
{recorte_html}
      <div id="cards" data-composition-id="cards" data-composition-src="compositions/cards.html"
        data-start="0" data-duration="{num(duracao)}" data-track-index="3" data-track-kind="graphics"
        data-width="{LARGURA}" data-height="{ALTURA}" style="z-index: 4"></div>

      {(chr(10) + "      ").join(transicoes_html)}

      {(chr(10) + "      ").join(audios)}
    </div>

    <script>
      window.__timelines = window.__timelines || {{}};
      const tl = gsap.timeline({{ paused: true }});
      tl.to({{}}, {{ duration: {num(duracao)} }}, 0);
      {(chr(10) + "      ").join(js)}
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""


def main():
    pasta = Path(sys.argv[1]).resolve()
    plano = json.loads((pasta / "plano.json").read_text())
    duracao = plano["duracao"]
    (pasta / "compositions").mkdir(exist_ok=True)
    (pasta / "index.html").write_text(gerar_index(plano, duracao))
    (pasta / "compositions" / "legendas.html").write_text(gerar_legendas(plano, duracao))
    (pasta / "compositions" / "cards.html").write_text(gerar_cards(plano, duracao))
    print(f"ok: {pasta}/index.html + compositions/legendas.html + compositions/cards.html")


if __name__ == "__main__":
    main()
