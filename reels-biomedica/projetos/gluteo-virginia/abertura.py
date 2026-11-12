"""Abertura do quadro (caso Virgínia): gera compositions/abertura.html e os sons dela.

Uso: python3 abertura.py   (na pasta do projeto; depois rode o gerar.py)

É a única animação do vídeo: uma tela cheia que abre o quadro, logo depois de ela dizer "mas eu
vou te contar agora". O vídeo tem uma pausa nesse ponto ("pausas" no plano.json, aberta pelo
reenquadrar.py), então a abertura não cobre a fala. Ao fundo, o vídeo da famosa em preto e branco,
com o glúteo à mostra; por cima, "CASO" / nome / a frase do gancho, em Poppins branca. Para o
próximo caso, troque NOME, FRASE, VIDEO e o ponto da pausa.
"""

import json
from pathlib import Path

AQUI = Path(__file__).parent
plano = json.loads((AQUI / "plano.json").read_text())
A = plano["pausas"][0]["em"]          # a pausa começa aqui (tempo do vídeo novo = do original até ela)
DUR = plano["pausas"][0]["dur"]
NOME, FRASE = "VIRGÍNIA", "o que ninguém vê"
VIDEO, VIDEO_INICIO, FOCO_Y = "assets/fotos/virginia-tela.mp4", 7.0, 68   # % da altura: o glúteo


def n(x):
    return f"{x:.3f}".rstrip("0").rstrip(".")


letras = "".join(f'<span class="le" id="le{i}">{c}</span>' for i, c in enumerate("CASO"))
# o vídeo do fundo tem o próprio tempo; a tela em volta aparece e some pela timeline (nunca os dois com data-start)
html = f"""<div id="ab">
      <div class="ab-fundo" id="ab-fundo"><video id="ab-v" class="clip" src="{VIDEO}" data-start="{n(A)}" data-duration="{n(DUR)}"
        data-media-start="{n(VIDEO_INICIO)}" muted playsinline></video></div>
      <div class="ab-veu"></div>
      <div class="ab-canto" id="c1" style="left:64px;top:64px;border-width:5px 0 0 5px"></div>
      <div class="ab-canto" id="c2" style="right:64px;top:64px;border-width:5px 5px 0 0"></div>
      <div class="ab-canto" id="c3" style="left:64px;bottom:64px;border-width:0 0 5px 5px"></div>
      <div class="ab-canto" id="c4" style="right:64px;bottom:64px;border-width:0 5px 5px 0"></div>
      <div class="ab-titulo" id="ab-t">
        <div class="ab-caso">{letras}</div>
        <div class="ab-nome" id="ab-n">{NOME}</div>
        <div class="ab-linha" id="ab-l"></div>
        <div class="ab-frase" id="ab-f">{FRASE}</div>
      </div>
      <div class="ab-clarao" id="ab-c"></div>
    </div>"""

js = [
    f'tl.set("#ab", {{opacity:0}}, 0);',
    f'tl.set("#ab", {{opacity:1}}, {n(A)});',
    f'tl.set("#ab", {{opacity:0}}, {n(A + DUR)});',
    # fundo: preto e branco, empurrando devagar para o glúteo
    f'tl.fromTo("#ab-fundo", {{scale:1.1}}, {{scale:1.24, duration:{n(DUR)}, ease:"none"}}, {n(A)});',
    # cantos de enquadramento entram de fora
    *[f'tl.fromTo("#{c}", {{opacity:0, x:{dx}, y:{dy}}}, {{opacity:1, x:0, y:0, duration:0.4, ease:"expo.out"}}, {n(A + 0.08)});'
      for c, dx, dy in (("c1", -40, -40), ("c2", 40, -40), ("c3", -40, 40), ("c4", 40, 40))],
    # CASO, letra a letra
    f'tl.fromTo(".le", {{opacity:0, y:28}}, {{opacity:1, y:0, duration:0.3, ease:"power3.out", stagger:0.05}}, {n(A + 0.12)});',
    # o nome cai com peso (o impacto do som), com um tremor curto e um clarão no fundo
    f'tl.fromTo("#ab-n", {{opacity:0, scale:1.7, filter:"blur(18px)"}}, {{opacity:1, scale:1, filter:"blur(0px)", duration:0.3, ease:"expo.out"}}, {n(A + 0.36)});',
    f'tl.fromTo("#ab-t", {{x:0}}, {{keyframes:{{x:[0, -9, 7, -4, 2, 0]}}, duration:0.22, ease:"none"}}, {n(A + 0.44)});',
    f'tl.fromTo("#ab-c", {{opacity:0}}, {{opacity:0.5, duration:0.05, ease:"none"}}, {n(A + 0.42)});',
    f'tl.to("#ab-c", {{opacity:0, duration:0.3, ease:"power2.out"}}, {n(A + 0.47)});',
    # linha e a frase do gancho
    f'tl.fromTo("#ab-l", {{scaleX:0}}, {{scaleX:1, duration:0.42, ease:"expo.out"}}, {n(A + 0.62)});',
    f'tl.fromTo("#ab-f", {{opacity:0, y:22}}, {{opacity:1, y:0, duration:0.36, ease:"power3.out"}}, {n(A + 0.72)});',
    # saída: o título cresce e desfoca para dentro da luz da transição
    f'tl.to("#ab-t", {{scale:1.08, opacity:0, filter:"blur(10px)", duration:0.32, ease:"power2.in"}}, {n(A + DUR - 0.36)});',
]
sons = [{"t": round(A + 0.42, 3), "som": "impacto", "vol": 0.8},
        {"t": round(A + 0.74, 3), "som": "click", "vol": 0.35}]

FONTES = "".join(f'@font-face {{ font-family: "Poppins Reels"; font-weight: {p}; font-style: normal; src: url("assets/fonts/Poppins-{p}.ttf"); }}\n'
                 for p in (600, 700, 800))
saida = f"""<template>
  <style>
{FONTES}
    #root {{ position: absolute; inset: 0; overflow: hidden; font-family: "Poppins Reels"; color: #FFFFFF; }}
    #ab {{ position: absolute; left: 0; top: 0; opacity: 0; width: 1080px; height: 1920px; overflow: hidden; background: #111; }}
    .ab-fundo {{ position: absolute; inset: 0; transform-origin: 50% {FOCO_Y}%; }}
    .ab-fundo video {{ position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; object-fit: cover;
                       object-position: 50% {FOCO_Y}%; filter: grayscale(1) contrast(1.12) brightness(0.82); }}
    .ab-veu {{ position: absolute; inset: 0;
      background: radial-gradient(ellipse 85% 60% at 50% 46%, rgba(0,0,0,0.08) 0%, rgba(0,0,0,0.5) 100%),
                  linear-gradient(180deg, rgba(0,0,0,0.4) 0%, rgba(0,0,0,0.12) 40%, rgba(0,0,0,0) 60%, rgba(0,0,0,0.2) 100%); }}
    .ab-canto {{ position: absolute; width: 96px; height: 96px; border-style: solid; border-color: rgba(255,255,255,0.92); }}
    .ab-titulo {{ position: absolute; left: 0; top: 500px; width: 1080px; text-align: center; transform-origin: 50% 40%; }}
    .ab-caso {{ font-weight: 700; font-size: 46px; letter-spacing: 0.42em; padding-left: 0.42em; line-height: 1; }}
    .le {{ display: inline-block; }}
    .ab-nome {{ font-weight: 800; font-size: 176px; letter-spacing: -0.045em; line-height: 1; margin-top: 18px;
                text-shadow: 0 6px 40px rgba(0,0,0,0.45); }}
    .ab-linha {{ width: 560px; height: 5px; margin: 34px auto 0; background: #FFFFFF; border-radius: 3px; }}
    .ab-frase {{ font-weight: 600; font-size: 46px; letter-spacing: -0.02em; line-height: 1; margin-top: 30px; }}
    .ab-clarao {{ position: absolute; inset: 0; background: #FFFFFF; opacity: 0; }}
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
print(f"ok: compositions/abertura.html ({n(A)}–{n(A + DUR)} s), {len(sons)} sons")
