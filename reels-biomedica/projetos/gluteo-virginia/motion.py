"""Animações do quadro (caso Virgínia): gera compositions/motion.html e os sons delas.

Uso: python3 motion.py   (na pasta do projeto; depois rode o gerar.py)

Tudo em Poppins com letras juntas, branco sobre vidro escuro (o fundo do vídeo é claro), no
alto da tela, acima da cabeça dela; as legendas ficam embaixo. Os tempos são os da fala
(transcricao.json, já sincronizada).
"""

import json
from pathlib import Path

AQUI = Path(__file__).parent
D = 63.9


def n(x):
    return f"{x:.3f}".rstrip("0").rstrip(".")


html, js, sons = [], [], []


def clip(cid, a, b, corpo, extra=""):
    html.append(f'<div id="{cid}" class="clip" data-start="{n(a)}" data-duration="{n(b - a)}"{extra}>{corpo}</div>')


def entra(sel, t, de, dur=0.5, ease="expo.out"):
    js.append(f'tl.fromTo("{sel}", {json.dumps(de)}, {{opacity:1, x:0, y:0, scale:1, duration:{dur}, ease:"{ease}"}}, {n(t)});')


def sai(sel, t, para=None, dur=0.3):
    para = para or {"opacity": 0, "y": -24}
    js.append(f'tl.to("{sel}", {{...{json.dumps(para)}, duration:{dur}, ease:"power2.in"}}, {n(t)});')


def som(t, nome, vol=0.45):
    sons.append({"t": round(t, 3), "som": nome, "vol": vol})


CHECK = ('<svg class="chk" viewBox="0 0 44 44"><circle cx="22" cy="22" r="20"/>'
         '<path id="{id}" d="M12.5 22.5 L19 29 L31.5 15.5"/></svg>')

# ── selo do quadro ────────────────────────────────────────────────────────────
clip("selo", 0.3, 7.95, '<div class="pilula" id="selo-p" style="left:48px;top:64px"><span class="ponto" id="selo-d"></span>'
     '<span class="pil-a">CASO</span><span class="pil-b">VIRGÍNIA</span></div>')
entra("#selo-p", 0.35, {"opacity": 0, "x": -40})
js.append('tl.fromTo("#selo-d", {scale:1}, {scale:1.4, duration:0.5, ease:"sine.inOut", yoyo:true, repeat:9}, 0.9);')
sai("#selo-p", 7.6, {"opacity": 0, "x": -24})
som(0.4, "pop", 0.4)

# ── índice: os três pontos que ela vai contar ("mas eu vou te contar agora") ──────
IND = [("01", "rotina", 6.60), ("02", "genética", 6.85), ("03", "construção", 7.10)]
pills = "".join(f'<div class="pilula" id="ind{i}"><span class="pil-num">{k}</span><span class="pil-b">{t}</span></div>'
                for i, (k, t, _) in enumerate(IND))
clip("indice", 6.55, 8.13, f'<div class="indice">{pills}</div>')
for i, (_, _, t) in enumerate(IND):
    entra(f"#ind{i}", t, {"opacity": 0, "y": 30, "scale": 0.85}, 0.4, "back.out(1.8)")
    som(t, "click", 0.4)
js.append('tl.to(["#ind0", "#ind1", "#ind2"], {opacity:0, y:-20, duration:0.22, ease:"power2.in", stagger:0.04}, 7.9);')

# ── capítulos: cartão grande e, depois, etiqueta no canto até o fim da parte ───────
CAPS = [("1", "01", "a rotina", "ROTINA", 8.20, 10.0, 18.95),
        ("2", "02", "a genética", "GENÉTICA", 19.12, 20.85, 27.62),
        ("3", "03", "a construção", "CONSTRUÇÃO", 27.78, 28.95, 46.80)]
for k, num, tit, rot, a, b, fim_tag in CAPS:
    clip(f"cap{k}", a, b, f'<div class="vidro capitulo" id="cap{k}-v"><div class="mascara"><div class="cap-num" id="cap{k}-n">{num}</div></div>'
         f'<div class="mascara"><div class="cap-tit" id="cap{k}-t">{tit}</div></div></div>')
    entra(f"#cap{k}-v", a, {"opacity": 0, "scale": 0.9}, 0.45)
    js.append(f'tl.fromTo("#cap{k}-n", {{yPercent:105}}, {{yPercent:0, duration:0.55, ease:"expo.out"}}, {n(a + 0.08)});')
    js.append(f'tl.fromTo("#cap{k}-t", {{yPercent:110}}, {{yPercent:0, duration:0.5, ease:"expo.out"}}, {n(a + 0.2)});')
    sai(f"#cap{k}-v", b - 0.32, {"opacity": 0, "scale": 0.92, "y": -30})
    som(a + 0.1, "pop", 0.45)
    clip(f"tag{k}", b - 0.1, fim_tag, f'<div class="pilula" id="tag{k}-p" style="left:48px;top:64px"><span class="pil-num">{num}</span>'
         f'<span class="pil-b">{rot}</span></div>')
    entra(f"#tag{k}-p", b - 0.1, {"opacity": 0, "x": -30}, 0.45)
    sai(f"#tag{k}-p", fim_tag - 0.32, {"opacity": 0, "x": -20})
    som(b - 0.05, "click", 0.35)

# ── parte 1: a lista da rotina, e o procedimento entra sobre essa base ────────
ITENS = [("treina todos os dias", 10.38), ("academia em casa", 11.88), ("alimentação", 13.00), ("descanso", 14.36)]
# cada item é uma pílula própria, empilhada à esquerda: a lista cresce na fala, sem caixa vazia
corpo = "".join(f'<div class="vidro item" id="it{i}" style="left:100px;top:{140 + 88 * i}px">' + CHECK.format(id=f"it{i}-c") +
                f'<span>{t}</span></div>' for i, (t, _) in enumerate(ITENS))
corpo += ('<div class="vidro item base" id="proc" style="left:100px;top:492px">'
          '<span class="seta">+</span><b>procedimento</b><span class="leve">sobre essa base</span></div>')
clip("lista", 10.3, 18.95, corpo)
for i, (_, t) in enumerate(ITENS):
    entra(f"#it{i}", t, {"opacity": 0, "x": -50, "scale": 0.92}, 0.42, "back.out(1.5)")
    js.append(f'tl.fromTo("#it{i}-c", {{strokeDashoffset:40}}, {{strokeDashoffset:0, duration:0.3, ease:"power2.out"}}, {n(t + 0.14)});')
    som(t + 0.14, "click-agudo", 0.5)
entra("#proc", 15.62, {"opacity": 0, "y": 40, "scale": 0.9}, 0.5, "back.out(1.6)")
som(15.62, "pop", 0.5)
js.append('tl.to(["#it0", "#it1", "#it2", "#it3", "#proc"], {opacity:0, x:-30, duration:0.26, ease:"power2.in", stagger:0.04}, 18.55);')

# ── parte 2: não é mérito, nem culpa; é o ponto de partida ─────────────────────
clip("merito", 24.78, 26.38, '<div class="vidro chip" id="mer" style="left:150px;top:250px;width:360px;height:116px"><span>mérito</span>'
     '<i class="risco" id="mer-r"></i></div><div class="vidro chip" id="cul" style="left:570px;top:250px;width:360px;height:116px">'
     '<span>culpa</span><i class="risco" id="cul-r"></i></div>')
for cid, t in (("mer", 24.86), ("cul", 25.72)):
    entra(f"#{cid}", t, {"opacity": 0, "y": 24, "scale": 0.9}, 0.4, "back.out(1.5)")
    js.append(f'tl.fromTo("#{cid}-r", {{scaleX:0}}, {{scaleX:1, duration:0.28, ease:"power2.inOut"}}, {n(t + 0.3)});')
    som(t, "click", 0.4)
    som(t + 0.32, "click-tecla", 0.4)
sai("#mer", 26.08)
sai("#cul", 26.08)

clip("partida", 26.44, 27.6, '<div class="vidro" id="par-v" style="left:90px;top:240px;width:900px;height:170px">'
     '<div class="par-txt">ponto de partida</div><i class="no" id="par-no" style="left:56px;top:112px"></i>'
     '<i class="trilho" id="par-l" style="left:80px;top:122px;width:770px"></i></div>')
entra("#par-v", 26.44, {"opacity": 0, "y": 26}, 0.4)
js.append('tl.fromTo("#par-no", {scale:0}, {scale:1, duration:0.35, ease:"back.out(2)"}, 26.56);')
js.append('tl.fromTo("#par-l", {scaleX:0}, {scaleX:1, duration:0.8, ease:"power2.out"}, 26.7);')
som(26.5, "whoosh-rapido", 0.35)

# ── parte 3: ela mesma contou (o vídeo dela), a linha do tempo da construção ──
html.append('<div id="post" class="post" style="left:620px;top:40px"><video id="post-v" class="clip" src="assets/fotos/virginia-tela.mp4" '
            'data-start="28.95" data-duration="3.05" data-media-start="3" muted playsinline></video></div>')
js.append('tl.fromTo("#post", {opacity:0, y:-60, rotation:12, scale:0.85}, {opacity:1, y:0, rotation:5, scale:1, duration:0.6, ease:"back.out(1.4)"}, 28.95);')
js.append('tl.to("#post", {y:-10, rotation:6, duration:2.0, ease:"sine.inOut"}, 29.55);')
js.append('tl.to("#post", {opacity:0, y:-80, scale:0.9, duration:0.35, ease:"power2.in"}, 31.62);')
som(28.98, "whoosh-rapido", 0.45)
som(31.65, "whoosh", 0.3)

clip("linha", 33.55, 37.42, '<div class="vidro" id="lin-v" style="left:70px;top:170px;width:940px;height:300px">'
     '<div class="rotulo">a construção</div>'
     '<i class="trilho fraco" style="left:80px;top:128px;width:780px"></i>'
     '<i class="trilho" id="lin-a" style="left:80px;top:128px;width:390px"></i>'
     '<i class="trilho" id="lin-b" style="left:470px;top:128px;width:390px"></i>'
     '<i class="no fraco" style="left:56px;top:104px"></i><i class="no" id="lin-n2" style="left:446px;top:104px"></i>'
     '<i class="no" id="lin-n3" style="left:836px;top:104px"></i>'
     '<div class="no-txt fraco" style="left:10px;top:170px;width:160px;text-align:left">partida</div>'
     '<div class="no-txt" id="lin-t2" style="left:300px;top:170px;width:340px">harmonização<br>glútea</div>'
     '<div class="no-txt" id="lin-t3" style="left:600px;top:170px;width:320px;text-align:right">bioestimulador<br>de colágeno</div></div>')
entra("#lin-v", 33.55, {"opacity": 0, "y": 26}, 0.4)
for lin, no, txt, t in (("#lin-a", "#lin-n2", "#lin-t2", 33.90), ("#lin-b", "#lin-n3", "#lin-t3", 36.24)):
    js.append(f'tl.fromTo("{lin}", {{scaleX:0}}, {{scaleX:1, duration:0.45, ease:"power2.out"}}, {n(t - 0.3)});')
    js.append(f'tl.fromTo("{no}", {{scale:0}}, {{scale:1, duration:0.35, ease:"back.out(2)"}}, {n(t + 0.1)});')
    entra(txt, t + 0.12, {"opacity": 0, "y": 16}, 0.35)
    som(t + 0.1, "click-agudo", 0.45)
som(33.6, "whoosh-rapido", 0.3)
sai("#lin-v", 37.1)

clip("versus", 37.55, 41.85, '<div class="vidro chip" id="vs-a" style="left:70px;top:250px;width:420px;height:120px"><span>preenchedor</span></div>'
     '<div class="vidro chip" id="vs-b" style="left:590px;top:250px;width:420px;height:120px"><span>bioestimulador</span></div>'
     '<div class="vidro diferente" id="vs-x" style="left:488px;top:258px;width:104px;height:104px"><span>≠</span></div>')
entra("#vs-a", 37.64, {"opacity": 0, "x": -60}, 0.45)
entra("#vs-b", 38.54, {"opacity": 0, "x": 60}, 0.45)
entra("#vs-x", 39.88, {"opacity": 0, "scale": 0.4}, 0.4, "back.out(2.2)")
som(37.66, "pop", 0.45)
som(38.56, "pop", 0.45)
som(39.9, "click-agudo", 0.5)
for cid in ("#vs-a", "#vs-b", "#vs-x"):
    sai(cid, 41.52)

clip("anos", 44.4, 46.55, '<div class="vidro" id="anos-v" style="left:120px;top:240px;width:840px;height:156px">'
     '<div class="anos-txt">anos de acompanhamento</div><i class="barra"></i><i class="barra cheia" id="anos-b"></i></div>')
entra("#anos-v", 44.42, {"opacity": 0, "y": 26}, 0.4)
js.append('tl.fromTo("#anos-b", {scaleX:0}, {scaleX:1, duration:1.5, ease:"power1.inOut"}, 45.1);')
som(44.45, "whoosh-rapido", 0.35)
som(45.14, "click", 0.35)
sai("#anos-v", 46.22)

# ── a série de cuidados que ela tem com ela mesma ─────────────────────────────────
CUID = [("treino", 0), ("alimentação", 0), ("descanso", 0), ("procedimentos", 1), ("acompanhamento", 1)]
pills = "".join(f'<span class="cuid" id="cu{i}">{t}</span>' + ("<br>" if i == 2 else "") for i, (t, _) in enumerate(CUID))
clip("serie", 54.3, 56.78, f'<div class="vidro" id="ser-v" style="left:90px;top:170px;width:900px;height:300px">'
     f'<div class="rotulo">a série de cuidados</div><div class="cuids">{pills}</div></div>')
entra("#ser-v", 54.3, {"opacity": 0, "y": 26}, 0.4)
som(54.33, "whoosh-rapido", 0.35)
for i in range(len(CUID)):
    t = 54.56 + 0.24 * i
    entra(f"#cu{i}", t, {"opacity": 0, "scale": 0.7, "y": 12}, 0.35, "back.out(2)")
    som(t, "click", 0.32)
sai("#ser-v", 56.45)

# ── fecho do quadro: o selo de caso analisado ──────────────────────────────────
clip("fecho", 60.05, D, '<div class="vidro fecho" id="fe-v"><svg class="chk grande" viewBox="0 0 44 44"><circle cx="22" cy="22" r="20"/>'
     '<path id="fe-c" d="M12.5 22.5 L19 29 L31.5 15.5"/></svg><div><div class="fe-a">CASO VIRGÍNIA</div>'
     '<div class="fe-b">analisado</div></div></div>')
js.append('tl.fromTo("#fe-v", {opacity:0, scale:1.35, rotation:-4}, {opacity:1, scale:1, rotation:-2, duration:0.45, ease:"back.out(1.6)"}, 60.08);')
js.append('tl.fromTo("#fe-c", {strokeDashoffset:40}, {strokeDashoffset:0, duration:0.35, ease:"power2.out"}, 60.4);')
js.append('tl.to("#fe-v", {scale:1.03, duration:3.2, ease:"sine.inOut"}, 60.6);')
som(60.1, "pop", 0.5)
som(60.45, "click-agudo", 0.45)

FONTES = "".join(f'@font-face {{ font-family: "Poppins Reels"; font-weight: {p}; font-style: normal; src: url("assets/fonts/Poppins-{p}.ttf"); }}\n'
                 for p in (600, 700, 800))
saida = f"""<template>
  <style>
{FONTES}
    #root {{ position: absolute; inset: 0; overflow: hidden; font-family: "Poppins Reels"; color: #FFFFFF; }}
    .clip, .post {{ position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; }}
    .post {{ width: 300px; height: 518px; padding: 10px; background: #FFFFFF; border-radius: 28px;
             box-shadow: 0 30px 70px rgba(0, 0, 0, 0.35); overflow: hidden; }}
    .post video {{ position: absolute; left: 10px; top: 10px; width: 280px; height: 498px; border-radius: 20px; object-fit: cover; }}
    .vidro {{ position: absolute; border-radius: 34px; overflow: hidden;
      background: linear-gradient(140deg, rgba(255,255,255,0.16), rgba(255,255,255,0.04) 50%, rgba(255,255,255,0.08)), rgba(22, 15, 17, 0.56);
      -webkit-backdrop-filter: blur(22px) saturate(160%); backdrop-filter: blur(22px) saturate(160%);
      border: 1.5px solid rgba(255, 255, 255, 0.32);
      box-shadow: inset 0 1.5px 0 rgba(255, 255, 255, 0.45), 0 24px 60px rgba(0, 0, 0, 0.26); }}
    .pilula {{ position: absolute; display: flex; align-items: center; gap: 12px; padding: 14px 26px 14px 20px; border-radius: 999px;
      background: rgba(18, 13, 15, 0.5); -webkit-backdrop-filter: blur(18px); backdrop-filter: blur(18px);
      border: 1.5px solid rgba(255, 255, 255, 0.34); font-size: 30px; line-height: 1; }}
    .ponto {{ width: 14px; height: 14px; border-radius: 50%; background: #FFFFFF; box-shadow: 0 0 14px rgba(255,255,255,0.8); }}
    .pil-a {{ font-weight: 600; letter-spacing: 0.16em; opacity: 0.85; }}
    .pil-b {{ font-weight: 800; letter-spacing: 0.06em; }}
    .pil-num {{ font-weight: 800; letter-spacing: -0.02em; padding-right: 12px; border-right: 1.5px solid rgba(255,255,255,0.45); }}
    .capitulo {{ left: 230px; top: 150px; width: 620px; height: 330px; display: flex; flex-direction: column; align-items: center; justify-content: center; }}
    .mascara {{ overflow: hidden; }}
    .cap-num {{ font-weight: 800; font-size: 190px; line-height: 0.86; letter-spacing: -0.05em; }}
    .cap-tit {{ font-weight: 800; font-size: 68px; line-height: 1.05; letter-spacing: -0.04em; padding-bottom: 6px; }}
    .item {{ display: flex; align-items: center; gap: 18px; padding: 12px 30px 12px 14px; border-radius: 999px; font-weight: 700; font-size: 44px;
             letter-spacing: -0.035em; line-height: 1; }}
    .chk {{ width: 44px; height: 44px; flex: none; }}
    .chk circle {{ fill: rgba(255,255,255,0.16); stroke: rgba(255,255,255,0.75); stroke-width: 2.5; }}
    .chk path {{ fill: none; stroke: #FFFFFF; stroke-width: 4; stroke-linecap: round; stroke-linejoin: round; stroke-dasharray: 40; }}
    .item.base {{ padding: 12px 30px 12px 24px; border-color: rgba(255,255,255,0.75); box-shadow: inset 0 1.5px 0 rgba(255,255,255,0.5), 0 0 26px rgba(255,255,255,0.28), 0 24px 60px rgba(0,0,0,0.26); }}
    .item .seta {{ font-weight: 800; width: 44px; text-align: center; }}
    .item b {{ font-weight: 800; }}
    .leve {{ font-weight: 600; font-size: 32px; opacity: 0.85; margin-left: 6px; letter-spacing: -0.02em; }}
    .chip {{ display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 52px; letter-spacing: -0.04em; }}
    .risco {{ position: absolute; left: 44px; right: 44px; top: 56px; height: 7px; border-radius: 4px; background: #FFFFFF;
              transform-origin: 0 50%; box-shadow: 0 2px 8px rgba(0,0,0,0.3); }}
    .par-txt {{ position: absolute; left: 44px; top: 26px; font-weight: 800; font-size: 50px; letter-spacing: -0.04em; }}
    .no {{ position: absolute; width: 48px; height: 48px; border-radius: 50%; background: #FFFFFF; box-shadow: 0 0 22px rgba(255,255,255,0.7); }}
    .no.fraco {{ background: rgba(255,255,255,0.55); box-shadow: none; }}
    .trilho {{ position: absolute; height: 6px; border-radius: 3px; background: #FFFFFF; transform-origin: 0 50%; }}
    .trilho.fraco {{ background: rgba(255,255,255,0.25); }}
    .rotulo {{ position: absolute; left: 44px; top: 28px; font-weight: 700; font-size: 28px; letter-spacing: 0.14em; text-transform: uppercase; opacity: 0.85; }}
    .no-txt {{ position: absolute; text-align: center; font-weight: 700; font-size: 36px; line-height: 1.08; letter-spacing: -0.035em; }}
    .no-txt.fraco {{ opacity: 0.7; font-weight: 600; }}
    .diferente {{ display: flex; align-items: center; justify-content: center; border-radius: 50%; font-weight: 800; font-size: 60px; }}
    .anos-txt {{ position: absolute; left: 44px; top: 30px; font-weight: 800; font-size: 46px; letter-spacing: -0.04em; }}
    .barra {{ position: absolute; left: 44px; right: 44px; top: 108px; height: 12px; border-radius: 6px; background: rgba(255,255,255,0.22); }}
    .barra.cheia {{ background: #FFFFFF; transform-origin: 0 50%; }}
    .cuids {{ position: absolute; left: 40px; right: 40px; top: 90px; text-align: center; line-height: 1; }}
    .cuid {{ display: inline-block; margin: 10px 8px; padding: 16px 28px; border-radius: 999px; background: rgba(255,255,255,0.16);
             border: 1.5px solid rgba(255,255,255,0.45); font-weight: 700; font-size: 40px; letter-spacing: -0.035em; }}
    .indice {{ position: absolute; left: 0; width: 1080px; top: 400px; display: flex; justify-content: center; gap: 16px; }}
    .indice .pilula {{ position: relative; font-size: 32px; padding: 16px 28px 16px 22px; }}
    .fecho {{ left: 230px; top: 250px; width: 620px; justify-content: center; height: 190px; display: flex; align-items: center; gap: 30px; padding: 0 44px; }}
    .chk.grande {{ width: 104px; height: 104px; }}
    .chk.grande path {{ stroke-width: 3.4; }}
    .fe-a {{ font-weight: 800; font-size: 50px; letter-spacing: -0.03em; line-height: 1; }}
    .fe-b {{ font-weight: 600; font-size: 38px; letter-spacing: -0.02em; line-height: 1.1; opacity: 0.85; margin-top: 8px; }}
  </style>
  <div id="root" data-composition-id="motion" data-width="1080" data-height="1920">
    {chr(10).join("    " + h for h in html).strip()}
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
    tl.to({{}}, {{ duration: {n(D)} }}, 0);
    {(chr(10) + "    ").join(js)}
    window.__timelines["motion"] = tl;
  </script>
</template>
"""
(AQUI / "compositions").mkdir(exist_ok=True)
(AQUI / "compositions" / "motion.html").write_text(saida)
(AQUI / "motion-sons.json").write_text(json.dumps(sons, ensure_ascii=False, indent=1))
print(f"ok: compositions/motion.html, {len(sons)} sons")
