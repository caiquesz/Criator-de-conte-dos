"""Abertura do quadro (caso Virgínia): gera compositions/abertura.html e os sons dela.

Uso: python3 abertura.py   (na pasta do projeto; depois rode o gerar.py)

É a única animação do vídeo: uma tela cheia que abre o quadro, logo depois de ela dizer "mas eu
vou te contar agora". O vídeo tem uma pausa nesse ponto ("pausas" no plano.json, aberta pelo
reenquadrar.py), então a abertura não cobre a fala.

Delicada e feminina, na estética das referências (a 1 principalmente: bege, nude, luz quente,
letra fina): ao fundo o vídeo da famosa em tom quente e suave, com o glúteo à mostra; um véu nude
no alto; manchas de luz pêssego e brilhos pequenos subindo devagar; "CASO" fino e espaçado, o nome
e a frase do gancho entrando em fade com desfoque; som de brilho. A primeira versão (preto e
branco, letras pesadas, tremor e som de impacto) a cliente achou pesada.

Para o próximo caso, troque NOME, FRASE, VIDEO e o ponto da pausa.
"""

import json
import random
from pathlib import Path

AQUI = Path(__file__).parent
plano = json.loads((AQUI / "plano.json").read_text())
A = plano["pausas"][0]["em"]          # a pausa começa aqui (tempo do vídeo novo = do original até ela)
DUR = plano["pausas"][0]["dur"]
NOME, FRASE = "Virgínia", "o que ninguém vê"
VIDEO, VIDEO_INICIO, FOCO_Y = "assets/fotos/virginia-tela.mp4", 7.0, 68   # % da altura: o glúteo


def n(x):
    return f"{x:.3f}".rstrip("0").rstrip(".")


rnd = random.Random(11)
brilhos = []
for i in range(18):
    x, y = rnd.uniform(90, 990), rnd.uniform(380, 1500)
    tam = rnd.choice([5, 6, 7, 8, 10, 12])
    brilhos.append((f"bx{i}", x, y, tam, rnd.uniform(0.05, 0.7), rnd.uniform(1.3, 1.9), rnd.uniform(90, 210), rnd.uniform(0.55, 0.95)))

html = f"""<div id="ab">
      <div class="ab-fundo" id="ab-fundo"><video id="ab-v" class="clip" src="{VIDEO}" data-start="{n(A)}" data-duration="{n(DUR)}"
        data-media-start="{n(VIDEO_INICIO)}" muted playsinline></video></div>
      <div class="ab-veu"></div>
      <div class="ab-luz" id="ab-l1" style="left:-320px;top:-260px"></div>
      <div class="ab-luz suave" id="ab-l2" style="left:420px;top:1080px"></div>
      {"".join(f'<i class="ab-brilho" id="{b[0]}" style="left:{b[1]:.0f}px;top:{b[2]:.0f}px;width:{b[3]}px;height:{b[3]}px"></i>' for b in brilhos)}
      <div class="ab-titulo" id="ab-t">
        <div class="ab-caso" id="ab-k">{"".join(f'<span class="le" id="le{i}">{c}</span>' for i, c in enumerate("CASO"))}</div>
        <div class="ab-nome" id="ab-n">{NOME}</div>
        <div class="ab-linha" id="ab-r"></div>
        <div class="ab-frase" id="ab-f">{FRASE}</div>
      </div>
    </div>"""

# o vídeo do fundo tem o próprio tempo; a tela em volta aparece e some pela timeline (nunca os dois com data-start)
js = [
    'tl.set("#ab", {opacity:0}, 0);',
    f'tl.set("#ab", {{opacity:1}}, {n(A)});',
    f'tl.set("#ab", {{opacity:0}}, {n(A + DUR)});',
    # fundo: aproxima devagar, sem pressa
    f'tl.fromTo("#ab-fundo", {{scale:1.04, y:0}}, {{scale:1.12, y:-18, duration:{n(DUR)}, ease:"sine.inOut"}}, {n(A)});',
    # luz pêssego atravessando de leve
    f'tl.fromTo("#ab-l1", {{opacity:0, x:-40, y:-20}}, {{opacity:0.7, x:60, y:30, duration:{n(DUR * 0.6)}, ease:"sine.out"}}, {n(A)});',
    f'tl.to("#ab-l1", {{opacity:0.35, x:110, duration:{n(DUR * 0.4)}, ease:"sine.in"}}, {n(A + DUR * 0.6)});',
    f'tl.fromTo("#ab-l2", {{opacity:0, x:40}}, {{opacity:0.55, x:-60, duration:{n(DUR)}, ease:"sine.inOut"}}, {n(A)});',
    # "CASO": fino, as letras se aproximando (cada letra anda até o lugar; transform, não letter-spacing)
    f'tl.fromTo("#ab-k", {{opacity:0, filter:"blur(8px)"}}, {{opacity:0.96, filter:"blur(0px)", duration:1.0, ease:"power2.out"}}, {n(A + 0.22)});',
    *[f'tl.fromTo("#le{i}", {{x:{(i - 1.5) * 30:.0f}}}, {{x:0, duration:1.1, ease:"power2.out"}}, {n(A + 0.22)});' for i in range(4)],
    # o nome sobe em fade, desfocado até ficar nítido
    f'tl.fromTo("#ab-n", {{opacity:0, y:26, scale:0.97, filter:"blur(14px)"}}, '
    f'{{opacity:1, y:0, scale:1, filter:"blur(0px)", duration:1.0, ease:"power2.out"}}, {n(A + 0.42)});',
    f'tl.fromTo("#ab-r", {{scaleX:0, opacity:0}}, {{scaleX:1, opacity:0.9, duration:0.8, ease:"sine.inOut"}}, {n(A + 0.95)});',
    f'tl.fromTo("#ab-f", {{opacity:0, y:14, filter:"blur(6px)"}}, {{opacity:0.96, y:0, filter:"blur(0px)", duration:0.7, ease:"power2.out"}}, {n(A + 1.1)});',
    # saída: o título se desfaz para cima, a luz da transição leva de volta para ela
    f'tl.to("#ab-t", {{opacity:0, y:-16, filter:"blur(8px)", duration:0.45, ease:"power1.in"}}, {n(A + DUR - 0.5)});',
]
for bid, x, y, tam, atraso, dur, sobe, opa in brilhos:
    js.append(f'tl.fromTo("#{bid}", {{opacity:0, y:0, scale:0.6}}, {{keyframes:{{opacity:[0, {opa:.2f}, {opa:.2f}, 0]}}, '
              f'y:-{sobe:.0f}, scale:1, duration:{min(dur, DUR - atraso):.2f}, ease:"sine.out"}}, {n(A + atraso)});')

sons = [{"t": round(A + 0.5, 3), "som": "brilho", "vol": 0.5}]

FONTES = "".join(f'@font-face {{ font-family: "Poppins Reels"; font-weight: {p}; font-style: normal; src: url("assets/fonts/Poppins-{p}.ttf"); }}\n'
                 for p in (400, 600))
saida = f"""<template>
  <style>
{FONTES}
    #root {{ position: absolute; inset: 0; overflow: hidden; font-family: "Poppins Reels"; color: #FFFFFF; }}
    #ab {{ position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; overflow: hidden; opacity: 0; background: #C2B29E; }}
    .ab-fundo {{ position: absolute; inset: 0; transform-origin: 50% {FOCO_Y}%; }}
    .ab-fundo video {{ position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; object-fit: cover;
                       object-position: 50% {FOCO_Y}%; filter: sepia(0.55) saturate(0.78) contrast(0.94) brightness(0.98); }}
    /* véu nude no alto (onde fica o título) que some antes do corpo dela */
    .ab-veu {{ position: absolute; inset: 0;
      background: linear-gradient(180deg, rgba(132, 108, 92, 0.72) 0%, rgba(140, 116, 98, 0.62) 34%,
                                  rgba(176, 156, 136, 0.2) 52%, rgba(194, 178, 158, 0) 64%, rgba(120, 100, 86, 0.18) 100%); }}
    .ab-luz {{ position: absolute; width: 1000px; height: 1000px; border-radius: 50%; mix-blend-mode: screen;
      background: radial-gradient(circle, rgba(255, 190, 156, 0.85) 0%, rgba(255, 196, 166, 0.35) 38%, rgba(255, 200, 170, 0) 70%); }}
    .ab-luz.suave {{ background: radial-gradient(circle, rgba(255, 226, 200, 0.7) 0%, rgba(255, 226, 200, 0.25) 40%, rgba(255, 226, 200, 0) 70%); }}
    .ab-brilho {{ position: absolute; border-radius: 50%; background: #FFFFFF; opacity: 0;
                  box-shadow: 0 0 10px 3px rgba(255, 244, 232, 0.85), 0 0 22px 6px rgba(255, 214, 190, 0.45); }}
    .ab-titulo {{ position: absolute; left: 0; top: 470px; width: 1080px; text-align: center;
                  text-shadow: 0 2px 8px rgba(80, 54, 40, 0.35), 0 8px 34px rgba(80, 54, 40, 0.45); }}
    .ab-caso {{ font-weight: 400; font-size: 40px; letter-spacing: 0.55em; padding-left: 0.55em; line-height: 1; }}
    .le {{ display: inline-block; }}
    .ab-nome {{ font-weight: 600; font-size: 132px; letter-spacing: -0.025em; line-height: 1.05; margin-top: 22px; }}
    .ab-linha {{ width: 260px; height: 2px; margin: 30px auto 0; background: rgba(255, 255, 255, 0.9); border-radius: 2px;
                 box-shadow: 0 0 12px rgba(255, 236, 220, 0.8); }}
    .ab-frase {{ font-weight: 400; font-size: 46px; letter-spacing: 0.01em; line-height: 1; margin-top: 30px; }}
  </style>
  <div id="root" data-composition-id="abertura" data-width="1080" data-height="1920">
    {html}
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
    tl.to({{}}, {{ duration: {n(plano["duracao"])} }}, 0);
    {(chr(10) + "    ").join(js)}
    window.__timelines["abertura"] = tl;
  </script>
</template>
"""
(AQUI / "compositions" / "abertura.html").write_text(saida)
(AQUI / "abertura-sons.json").write_text(json.dumps(sons, ensure_ascii=False, indent=1))
print(f"ok: compositions/abertura.html ({n(A)}–{n(A + DUR)} s), {len(sons)} som")
