"""Abertura do quadro Bate-bola: gera compositions/abertura.html e os sons dela.

Uso: python3 abertura.py   (na pasta do projeto, depois do montar_plano.py; depois rode o gerar.py)

A mesma abertura delicada do quadro "Caso Virgínia" (projetos/gluteo-virginia/abertura.py), só que
aqui ela mesma diz o título ("Bate bola com doutora Nádia Rezende", de 0 a 2,97 s), então não há
pausa: a tela cheia fica por cima do vídeo dela, que aparece desfocado atrás de um véu nude, com luz
pêssego, brilhos subindo e "Bate-bola" / "com Dra. Nádia Rezende" entrando em fade. Sai numa luz
(a transição do plano.json em FIM).
"""

import json
import random
from pathlib import Path

AQUI = Path(__file__).parent
plano = json.loads((AQUI / "plano.json").read_text())
A, FIM = 0.0, 2.9667
NOME, FRASE = "Bate-bola", "com Dra. Nádia Rezende"


def n(x):
    return f"{x:.3f}".rstrip("0").rstrip(".")


rnd = random.Random(5)
brilhos = []
for i in range(18):
    x, y = rnd.uniform(90, 990), rnd.uniform(380, 1500)
    brilhos.append((f"bx{i}", x, y, rnd.choice([5, 6, 7, 8, 10, 12]), rnd.uniform(0.0, 0.9), rnd.uniform(1.3, 1.9),
                    rnd.uniform(90, 210), rnd.uniform(0.55, 0.95)))

letras = "".join(f'<span class="le" id="le{i}">{c}</span>' for i, c in enumerate(NOME))
html = f"""<div id="ab">
      <div class="ab-desfoque"></div>
      <div class="ab-veu"></div>
      <div class="ab-luz" id="ab-l1" style="left:-320px;top:-260px"></div>
      <div class="ab-luz suave" id="ab-l2" style="left:420px;top:1080px"></div>
      {"".join(f'<i class="ab-brilho" id="{b[0]}" style="left:{b[1]:.0f}px;top:{b[2]:.0f}px;width:{b[3]}px;height:{b[3]}px"></i>' for b in brilhos)}
      <div class="ab-titulo" id="ab-t">
        <div class="ab-nome" id="ab-n">{letras}</div>
        <div class="ab-linha" id="ab-r"></div>
        <div class="ab-frase" id="ab-f">{FRASE}</div>
      </div>
    </div>"""

D = FIM - A
js = [
    f'tl.set("#ab", {{opacity:1}}, {n(A)});',
    f'tl.set("#ab", {{opacity:0}}, {n(FIM)});',
    # luz pêssego atravessando de leve
    f'tl.fromTo("#ab-l1", {{opacity:0, x:-40, y:-20}}, {{opacity:0.7, x:60, y:30, duration:{n(D * 0.6)}, ease:"sine.out"}}, {n(A)});',
    f'tl.to("#ab-l1", {{opacity:0.35, x:110, duration:{n(D * 0.4)}, ease:"sine.in"}}, {n(A + D * 0.6)});',
    f'tl.fromTo("#ab-l2", {{opacity:0, x:40}}, {{opacity:0.55, x:-60, duration:{n(D)}, ease:"sine.inOut"}}, {n(A)});',
    # o título: cada letra sobe em fade, desfocada até ficar nítida
    f'tl.fromTo(".le", {{opacity:0, y:30, filter:"blur(12px)"}}, {{opacity:1, y:0, filter:"blur(0px)", duration:0.8, ease:"power2.out", stagger:0.05}}, {n(A + 0.15)});',
    f'tl.fromTo("#ab-r", {{scaleX:0, opacity:0}}, {{scaleX:1, opacity:0.9, duration:0.7, ease:"sine.inOut"}}, {n(A + 0.6)});',
    f'tl.fromTo("#ab-f", {{opacity:0, y:14, filter:"blur(6px)"}}, {{opacity:0.96, y:0, filter:"blur(0px)", duration:0.6, ease:"power2.out"}}, {n(A + 0.8)});',
    # saída: o título se desfaz para cima, a luz da transição leva para a primeira pergunta
    f'tl.to("#ab-t", {{opacity:0, y:-16, filter:"blur(8px)", duration:0.38, ease:"power1.in"}}, {n(FIM - 0.4)});',
]
for bid, x, y, tam, atraso, dur, sobe, opa in brilhos:
    js.append(f'tl.fromTo("#{bid}", {{opacity:0, y:0, scale:0.6}}, {{keyframes:{{opacity:[0, {opa:.2f}, {opa:.2f}, 0]}}, '
              f'y:-{sobe:.0f}, scale:1, duration:{min(dur, D - atraso):.2f}, ease:"sine.out"}}, {n(A + atraso)});')

sons = [{"t": round(A + 0.3, 3), "som": "brilho", "vol": 0.5}]

FONTES = "".join(f'@font-face {{ font-family: "Poppins Reels"; font-weight: {p}; font-style: normal; src: url("assets/fonts/Poppins-{p}.ttf"); }}\n'
                 for p in (400, 600))
saida = f"""<template>
  <style>
{FONTES}
    #root {{ position: absolute; inset: 0; overflow: hidden; font-family: "Poppins Reels"; color: #FFFFFF; }}
    #ab {{ position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; overflow: hidden; opacity: 0; }}
    /* o vídeo dela continua por baixo: aqui só desfoca e aquece */
    .ab-desfoque {{ position: absolute; inset: 0; -webkit-backdrop-filter: blur(10px) sepia(0.35) saturate(0.85);
                    backdrop-filter: blur(10px) sepia(0.35) saturate(0.85); }}
    .ab-veu {{ position: absolute; inset: 0;
      background: linear-gradient(180deg, rgba(132, 108, 92, 0.62) 0%, rgba(140, 116, 98, 0.52) 34%,
                                  rgba(160, 138, 118, 0.42) 60%, rgba(120, 100, 86, 0.5) 100%); }}
    .ab-luz {{ position: absolute; width: 1000px; height: 1000px; border-radius: 50%; mix-blend-mode: screen;
      background: radial-gradient(circle, rgba(255, 190, 156, 0.85) 0%, rgba(255, 196, 166, 0.35) 38%, rgba(255, 200, 170, 0) 70%); }}
    .ab-luz.suave {{ background: radial-gradient(circle, rgba(255, 226, 200, 0.7) 0%, rgba(255, 226, 200, 0.25) 40%, rgba(255, 226, 200, 0) 70%); }}
    .ab-brilho {{ position: absolute; border-radius: 50%; background: #FFFFFF; opacity: 0;
                  box-shadow: 0 0 10px 3px rgba(255, 244, 232, 0.85), 0 0 22px 6px rgba(255, 214, 190, 0.45); }}
    .ab-titulo {{ position: absolute; left: 0; top: 760px; width: 1080px; text-align: center;
                  text-shadow: 0 2px 8px rgba(80, 54, 40, 0.35), 0 8px 34px rgba(80, 54, 40, 0.45); }}
    .ab-nome {{ font-weight: 600; font-size: 150px; letter-spacing: -0.03em; line-height: 1.05; }}
    .le {{ display: inline-block; }}
    .ab-linha {{ width: 280px; height: 2px; margin: 34px auto 0; background: rgba(255, 255, 255, 0.9); border-radius: 2px;
                 box-shadow: 0 0 12px rgba(255, 236, 220, 0.8); }}
    .ab-frase {{ font-weight: 400; font-size: 50px; letter-spacing: 0.01em; line-height: 1; margin-top: 32px; }}
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
(AQUI / "compositions").mkdir(exist_ok=True)
(AQUI / "compositions" / "abertura.html").write_text(saida)
(AQUI / "abertura-sons.json").write_text(json.dumps(sons, ensure_ascii=False, indent=1))
print(f"ok: compositions/abertura.html ({n(A)}–{n(FIM)} s), {len(sons)} som")
