"""
Gera o PDF do briefing da Isabele Ribeiro com a identidade visual da Nux.

Fonte das perguntas: ../nutricionista-consulta-online.md (blocos "## Bloco N | ...",
perguntas "**N. ...**" e a linha "→ ..." logo abaixo). Editou o .md, rode de novo.

Uso:
    python3 briefings/pdf/build_briefing_pdf.py

Requer: playwright (Chromium), pypdf e as fontes DM Sans, Playfair Display e
Bebas Neue instaladas no sistema (Google Fonts).
"""

import html
import os
import re
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright
from pypdf import PdfReader, PdfWriter

AQUI = Path(__file__).resolve().parent
MD = AQUI.parent / "nutricionista-consulta-online.md"
SAIDA = AQUI.parent / "briefing-isabele-ribeiro-nux.pdf"

# Tempo sugerido por bloco (minutos). Abertura 5 + blocos 60 + fechamento 5 = 70.
TEMPOS = {1: 10, 2: 10, 3: 5, 4: 8, 5: 7, 6: 5, 7: 12, 8: 3}

TRI = ('<svg class="tri" viewBox="0 0 10 8.66" aria-hidden="true">'
       '<polygon points="0,0 10,0 5,8.66"/></svg>')
LOGO = f'<span class="logo">{TRI}<span>nux</span></span>'


# ── LEITURA DO MARKDOWN ─────────────────────────────────────────
def inline(md: str) -> str:
    txt = html.escape(md.strip(), quote=False)
    txt = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", txt)
    return txt


def ler_blocos(md_path: Path):
    blocos, atual, pergunta = [], None, None
    for linha in md_path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^## Bloco (\d+) \| (.+)$", linha)
        if m:
            atual = {"n": int(m.group(1)), "titulo": m.group(2).strip(), "perguntas": []}
            blocos.append(atual)
            pergunta = None
            continue
        if linha.startswith("## "):
            atual, pergunta = None, None
            continue
        if atual is None:
            continue
        m = re.match(r"^\*\*(\d+)\. (⭐ )?(.*)$", linha)
        if m:
            pergunta = {
                "n": int(m.group(1)),
                "essencial": bool(m.group(2)),
                "texto": inline("**" + m.group(3)),
                "uso": "",
            }
            atual["perguntas"].append(pergunta)
            continue
        if linha.startswith("→") and pergunta is not None:
            pergunta["uso"] = inline(linha.lstrip("→ "))
    return blocos


# ── HTML ────────────────────────────────────────────────────────
CSS_BASE = """
:root{
  --navy:#000814; --blue:#2979FF; --blue2:#1565C0;
  --ink:#0B1324; --ink2:#36425B; --muted:#66728A; --line:#E2E7F0;
  --tint:#EEF4FF; --gray:#9AA6BD;
}
*{margin:0;padding:0;box-sizing:border-box}
html{-webkit-print-color-adjust:exact;print-color-adjust:exact}
body{font-family:'DM Sans',sans-serif;color:var(--ink2);font-size:9.6pt;line-height:1.5;background:#fff}
strong{color:var(--ink);font-weight:600}
.tri{width:.62em;height:.54em;fill:var(--blue);display:inline-block}
.logo{display:inline-flex;align-items:center;gap:.18em;font-weight:700;letter-spacing:.04em}
.kicker{font-family:'Bebas Neue',sans-serif;letter-spacing:.2em;color:var(--blue);font-size:10pt}
.glow{background:
  radial-gradient(ellipse 65% 55% at 12% 70%, rgba(41,121,255,.38) 0%, transparent 65%),
  radial-gradient(ellipse 60% 55% at 92% 25%, rgba(21,101,192,.30) 0%, transparent 65%),
  var(--navy)}
"""

CSS_CAPA = """
@page{size:A4;margin:0}
body{width:210mm;height:296.8mm;overflow:hidden;color:#fff;position:relative}
.capa{position:absolute;inset:0}
.bar{position:absolute;left:0;top:0;bottom:0;width:2.2mm;background:linear-gradient(to bottom,var(--blue),var(--blue2))}
.topo{position:absolute;top:18mm;left:22mm;right:18mm;display:flex;justify-content:space-between;align-items:center}
.topo .logo{font-size:17pt;color:rgba(255,255,255,.85)}
.topo .data{font-family:'Bebas Neue';letter-spacing:.25em;font-size:10pt;color:rgba(255,255,255,.45)}
.miolo{position:absolute;left:22mm;right:22mm;bottom:58mm}
.miolo .kicker{font-size:12pt;margin-bottom:7mm}
.aspas{font-family:'Playfair Display';font-size:80pt;line-height:.5;color:var(--blue);opacity:.85;height:12mm}
h1{font-family:'Playfair Display';font-style:italic;font-weight:700;font-size:50pt;line-height:1.02;letter-spacing:-.01em;margin-bottom:5mm}
.sub{font-family:'Playfair Display';font-weight:600;font-size:20pt;line-height:1.25;color:rgba(255,255,255,.86);max-width:150mm}
.div{width:22mm;height:1mm;border-radius:1mm;background:linear-gradient(90deg,var(--blue),var(--blue2));margin:9mm 0 0}
.meta{position:absolute;left:22mm;right:22mm;bottom:20mm;display:grid;grid-template-columns:repeat(4,1fr);gap:6mm;
  border-top:1px solid rgba(255,255,255,.14);padding-top:6mm}
.meta .k{font-family:'Bebas Neue';letter-spacing:.2em;color:var(--blue);font-size:9pt;margin-bottom:1.2mm}
.meta .v{font-size:9pt;line-height:1.4;color:rgba(255,255,255,.82)}
"""

CSS_MIOLO = """
@page{size:A4;margin:15mm 16mm 17mm 16mm}
h2.titulo{font-family:'Playfair Display';font-weight:700;font-size:21pt;line-height:1.1;color:var(--ink);margin:1mm 0 2mm}
h3{font-family:'Playfair Display';font-weight:700;font-size:12.5pt;color:var(--ink);margin:0 0 2mm}
.lead{font-size:10.5pt;color:var(--ink2);max-width:170mm}
.quebra{break-before:page}
.secao{margin-top:7mm}
.rule{width:12mm;height:.8mm;border-radius:1mm;background:linear-gradient(90deg,var(--blue),var(--blue2));margin:3mm 0 4mm}

/* faixa de bloco */
.band{color:#fff;border-radius:3mm;padding:4.2mm 5.5mm;display:flex;justify-content:space-between;align-items:flex-end;
  margin:7mm 0 1mm;break-inside:avoid;break-after:avoid}
.band.first{margin-top:0}
.band .kicker{font-size:10pt;margin-bottom:1mm}
.band h2{font-family:'Playfair Display';font-style:italic;font-weight:700;font-size:16.5pt;line-height:1.15;max-width:135mm}
.band .tempo{font-family:'Bebas Neue';letter-spacing:.18em;font-size:10pt;color:rgba(255,255,255,.8);
  border:1px solid rgba(255,255,255,.28);border-radius:20mm;padding:.6mm 3.2mm .3mm;white-space:nowrap}

/* perguntas */
.q{display:grid;grid-template-columns:11mm 1fr;column-gap:2.5mm;padding:3.4mm 0 3.2mm;border-bottom:1px solid var(--line);break-inside:avoid}
.q:last-child{border-bottom:none}
.qn{font-family:'Bebas Neue';font-size:21pt;line-height:.95;color:var(--gray);letter-spacing:.02em}
.q.ess .qn{color:var(--blue)}
.qt{font-size:10pt;line-height:1.45;color:var(--ink2)}
.qt strong{color:var(--ink);font-weight:600}
.pill{display:inline-block;font-family:'Bebas Neue';letter-spacing:.14em;font-size:7.6pt;line-height:1;color:#fff;background:var(--blue);
  border-radius:10mm;padding:.9mm 2mm .6mm;margin-right:1.6mm;vertical-align:1.2pt}
.uso{margin-top:1.6mm;font-size:8.7pt;line-height:1.45;color:var(--muted);padding-left:3mm;border-left:.6mm solid var(--tint)}
.uso b{font-family:'Bebas Neue';font-weight:400;letter-spacing:.14em;color:var(--blue);font-size:8.6pt;margin-right:1.2mm}

/* listas e cartões */
ul.lista{list-style:none}
ul.lista li{position:relative;padding-left:5mm;margin:1.4mm 0}
ul.lista li:before{content:"";position:absolute;left:0;top:.55em;width:2mm;height:2mm;border-radius:50%;background:var(--blue)}
.card{border:1px solid var(--line);border-radius:3mm;padding:4.5mm 5mm;break-inside:avoid;background:#fff}
.card.tint{background:var(--tint);border-color:#D6E4FF}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:4mm}
.grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:3.5mm}

/* pauta */
table.pauta{width:100%;border-collapse:collapse;font-size:9.3pt}
table.pauta td{padding:1.9mm 0;border-bottom:1px solid var(--line);vertical-align:top}
table.pauta td.t{font-family:'Bebas Neue';letter-spacing:.12em;color:var(--blue);font-size:11pt;width:20mm}
table.pauta td.m{text-align:right;color:var(--muted);font-size:8.6pt;width:26mm}
table.pauta tr.total td{border-bottom:none;font-weight:600;color:var(--ink)}

/* raio-x */
.tiles{display:grid;grid-template-columns:repeat(4,1fr);gap:3mm;margin:4mm 0 5mm}
.tile{border-radius:3mm;padding:4mm 4mm 3.6mm;color:#fff;break-inside:avoid}
.tile .v{font-family:'Bebas Neue';font-size:27pt;line-height:1;letter-spacing:.02em}
.tile .l{font-size:8.4pt;font-weight:600;margin-top:1.4mm;color:#fff}
.tile .s{font-size:7.6pt;line-height:1.35;color:rgba(255,255,255,.62);margin-top:1mm}
.chart .row{display:grid;grid-template-columns:44mm 1fr;align-items:center;gap:2.5mm;margin:1.9mm 0}
.chart .lab{font-size:8.6pt;color:var(--ink2);line-height:1.25}
.chart .track{display:flex;align-items:center;gap:2mm}
.chart .bar{height:4.2mm;border-radius:0 1.1mm 1.1mm 0;background:var(--gray)}
.chart .bar.hi{background:var(--blue)}
.chart .val{font-size:8.6pt;font-weight:600;color:var(--ink)}
.legenda{display:flex;gap:5mm;font-size:8pt;color:var(--muted);margin-top:2.5mm}
.legenda i{display:inline-block;width:2.6mm;height:2.6mm;border-radius:.6mm;margin-right:1.4mm;vertical-align:-.3mm}
.top{width:100%;border-collapse:collapse;font-size:8.6pt}
.top td{padding:1.7mm 0;border-bottom:1px solid var(--line);vertical-align:top}
.top td.n{text-align:right;font-weight:600;color:var(--ink);white-space:nowrap;padding-left:2mm}
.top td.x{text-align:right;color:var(--muted);white-space:nowrap;padding-left:2mm;width:9mm}
.nota{font-size:8pt;color:var(--muted);margin-top:2mm}
.bio{font-family:'Playfair Display';font-style:italic;font-size:11pt;color:var(--ink);line-height:1.4;margin:1mm 0 2.5mm}
.tags{display:flex;flex-wrap:wrap;gap:1.6mm}
.tag{font-family:'Bebas Neue';letter-spacing:.12em;font-size:8.4pt;color:var(--blue2);border:1px solid #C9DAFF;background:#fff;border-radius:10mm;padding:.7mm 2.6mm .4mm}
.destaque{color:#fff;border-radius:3mm;padding:5mm 6mm;margin-top:4mm;break-inside:avoid}
.destaque .kicker{margin-bottom:1.4mm}
.destaque p{font-size:9.8pt;line-height:1.5;color:rgba(255,255,255,.88)}
.destaque p strong{color:#fff}

/* linha editorial */
.funil .card{border-top:1.2mm solid var(--blue)}
.funil .card:nth-child(1){border-top-color:#9CC0FF}
.funil .card:nth-child(2){border-top-color:#2979FF}
.funil .card:nth-child(3){border-top-color:#1565C0}
.funil .obj{font-size:8.6pt;color:var(--muted);margin-bottom:2mm}
.funil ul.lista li{font-size:8.8pt;margin:1.1mm 0}

/* checklists */
.checks{list-style:none;display:grid;grid-template-columns:1fr 1fr;column-gap:6mm}
.checks li{display:flex;gap:2.6mm;align-items:flex-start;padding:2.3mm 0;border-bottom:1px solid var(--line);font-size:9.3pt;break-inside:avoid}
.box{flex:none;width:3.6mm;height:3.6mm;border:1.4px solid var(--blue);border-radius:.8mm;margin-top:.5mm}
.ok{flex:none;width:3.6mm;height:3.6mm;border-radius:50%;background:var(--blue);margin-top:.6mm;position:relative}
.ok:after{content:"";position:absolute;left:1.15mm;top:.65mm;width:.9mm;height:1.6mm;border:solid #fff;border-width:0 .45mm .45mm 0;transform:rotate(45deg)}
.linhas div{height:8.5mm;border-bottom:1px solid var(--line)}
"""


def capa_html() -> str:
    return f"""<!DOCTYPE html><html lang="pt-BR"><head><meta charset="utf-8">
<style>{CSS_BASE}{CSS_CAPA}</style></head><body>
<div class="capa glow"></div>
<div class="bar"></div>
<div class="topo">{LOGO}<span class="data">Briefing · 03.11.2026</span></div>
<div class="miolo">
  <div class="kicker">Briefing estratégico de social media</div>
  <div class="aspas">“</div>
  <h1>Isabele Ribeiro</h1>
  <div class="sub">Expansão para consulta online no Brasil, com foco em saúde intestinal</div>
  <div class="div"></div>
</div>
<div class="meta">
  <div><div class="k">Cliente</div><div class="v">@isabeleribeironutri<br>Nutricionista</div></div>
  <div><div class="k">Reunião</div><div class="v">03/11/2026<br>60 a 75 minutos</div></div>
  <div><div class="k">Escopo Nux</div><div class="v">Roteiro, captação<br>e edição</div></div>
  <div><div class="k">Objetivo</div><div class="v">Pacientes de consulta<br>online no Brasil todo</div></div>
</div>
</body></html>"""


def pergunta_html(q) -> str:
    pill = '<span class="pill">Essencial</span>' if q["essencial"] else ""
    uso = f'<div class="uso"><b>Para o roteiro</b>{q["uso"]}</div>' if q["uso"] else ""
    cls = "q ess" if q["essencial"] else "q"
    return f"""<div class="{cls}"><div class="qn">{q["n"]:02d}</div>
<div><div class="qt">{pill}{q["texto"]}</div>{uso}</div></div>"""


def blocos_html(blocos) -> str:
    partes = []
    for i, b in enumerate(blocos):
        primeira = " first" if i == 0 else ""
        tempo = TEMPOS.get(b["n"])
        tempo_html = f'<span class="tempo">{tempo} min</span>' if tempo else ""
        perguntas = "\n".join(pergunta_html(q) for q in b["perguntas"])
        partes.append(f"""<div class="band glow{primeira}"><div>
  <div class="kicker">Bloco {b["n"]:02d} · {len(b["perguntas"])} perguntas</div>
  <h2>{html.escape(b["titulo"])}</h2></div>{tempo_html}</div>
<div class="perguntas">{perguntas}</div>""")
    return "\n".join(partes)


def miolo_html(blocos) -> str:
    total_q = sum(len(b["perguntas"]) for b in blocos)
    total_ess = sum(q["essencial"] for b in blocos for q in b["perguntas"])
    pauta = "\n".join(
        f'<tr><td class="t">{TEMPOS.get(b["n"], "")} min</td><td>Bloco {b["n"]:02d} · '
        f'{html.escape(b["titulo"])}</td><td class="m">{len(b["perguntas"])} perguntas</td></tr>'
        for b in blocos)

    mix = [("Parceiros e publis locais", 8, False), ("Diário de obra do consultório", 7, False),
           ("Motivacional e #teamisanutri", 7, False), ("Jornada SIBO (intestino)", 5, True),
           ("Educativo (Mounjaro)", 1, True)]
    barras = "\n".join(
        f'<div class="row"><div class="lab">{nome}</div><div class="track">'
        f'<div class="bar{" hi" if hi else ""}" style="width:{n / 8 * 100 * 0.82:.1f}%"></div>'
        f'<span class="val">{n}</span></div></div>' for nome, n, hi in mix)

    return f"""<!DOCTYPE html><html lang="pt-BR"><head><meta charset="utf-8">
<style>{CSS_BASE}{CSS_MIOLO}</style></head><body>

<!-- ANTES DE COMEÇAR -->
<div class="kicker">Antes de começar</div>
<h2 class="titulo">O que precisamos sair da reunião sabendo</h2>
<div class="rule"></div>
<p class="lead">Tudo o que precisamos para escrever roteiros que cheguem em pessoas de fora da cidade e virem
<strong>agendamento de consulta online</strong>. E a operação combinada: agenda de publis, envio de pautas,
gravação, edição e aprovação. A Nux cuida do processo completo: roteiro, captação e edição.</p>

<div class="grid2 secao">
  <div class="card">
    <h3>Como usar este roteiro</h3>
    <ul class="lista">
      <li><strong>{total_q} perguntas</strong> em {len(blocos)} blocos. As <strong>{total_ess} marcadas como essenciais</strong> são as que não podem ficar de fora se o tempo apertar.</li>
      <li>O trecho <strong>Para o roteiro</strong> é só para você: diz para que a resposta serve na hora de escrever.</li>
      <li>Resposta genérica ("atendo todo mundo", "consulta humanizada")? Peça um exemplo real: "me conta a última vez que isso aconteceu".</li>
      <li>Grave a reunião, com permissão. As frases dela viram gancho e mostram o tom de voz.</li>
    </ul>
  </div>
  <div class="card tint">
    <h3>Peça para ela abrir na hora</h3>
    <ul class="lista">
      <li><strong>Insights do Instagram:</strong> público por cidade e estado, idade, gênero e alcance de não seguidores nos últimos 90 dias. Peça print.</li>
      <li><strong>Os 3 vídeos que ela sente que mais trouxeram pacientes.</strong> Compare com os mais vistos do Raio-X: quase sempre são diferentes.</li>
      <li><strong>A agenda de publis</strong> dos próximos 30 a 60 dias.</li>
    </ul>
  </div>
</div>

<div class="secao">
  <h3>Pauta sugerida · 70 minutos</h3>
  <table class="pauta">
    <tr><td class="t">5 min</td><td>Abertura e Raio-X do perfil</td><td class="m"></td></tr>
    {pauta}
    <tr><td class="t">5 min</td><td>Fechamento: checklist de combinados</td><td class="m"></td></tr>
  </table>
</div>

<!-- RAIO-X -->
<div class="quebra"></div>
<div class="kicker">Raio-X do perfil</div>
<h2 class="titulo">O ponto de partida</h2>
<div class="rule"></div>
<p class="lead">Dados públicos dos <strong>30 reels mais recentes</strong> (19/07 a 02/11/2026), coletados em 03/11/2026.</p>

<div class="tiles">
  <div class="tile glow"><div class="v">15.783</div><div class="l">seguidores</div><div class="s">550 posts e 27 destaques</div></div>
  <div class="tile glow"><div class="v">8,1 mil</div><div class="l">views por reel (mediana)</div><div class="s">cerca de metade dos seguidores; 24 de 30 entre 5 e 9,6 mil</div></div>
  <div class="tile glow"><div class="v">6 de 30</div><div class="l">reels falam de nutrição</div><div class="s">5 da jornada SIBO e 1 educativo</div></div>
  <div class="tile glow"><div class="v">78 s</div><div class="l">duração (mediana)</div><div class="s">17 de 30 passam de 1 min; só 5 entre 15 e 45 s</div></div>
</div>

<div class="grid2">
  <div class="card chart">
    <h3>Mix de conteúdo nos últimos 30 reels</h3>
    {barras}
    <div class="legenda"><span><i style="background:var(--blue)"></i>Nutrição</span><span><i style="background:var(--gray)"></i>Outros temas</span></div>
  </div>
  <div class="card">
    <h3>Os 4 que mais foram vistos</h3>
    <table class="top">
      <tr><td>Diário de Obra EP1 (consultório)</td><td class="n">16,7 mil</td><td class="x">2,1x</td></tr>
      <tr><td>Expo Resende Costa (último dia)</td><td class="n">16,2 mil</td><td class="x">2,0x</td></tr>
      <tr><td>Expo Resende Costa (show)</td><td class="n">14,0 mil</td><td class="x">1,7x</td></tr>
      <tr><td>Harmonização (vídeo de 4 s, replay infla a contagem)</td><td class="n">13,3 mil</td><td class="x">1,6x</td></tr>
    </table>
    <p class="nota">Múltiplo = visualizações divididas pela mediana do perfil. <strong>Nenhum é de nutrição; todos são de comunidade local.</strong></p>
  </div>
</div>

<div class="grid2" style="margin-top:4mm">
  <div class="card">
    <h3>Bio atual</h3>
    <p class="bio">“Emagrecimento saudável e sem terrorismo. Acompanhamento personalizado para resultados duradouros. Agende seu horário.”</p>
    <div class="tags"><span class="tag">Não fala em online</span><span class="tag">Não fala em intestino</span><span class="tag">Não fala em Brasil</span></div>
  </div>
  <div class="card">
    <h3>O que isso indica</h3>
    <ul class="lista">
      <li>Audiência fiel e estável, mas o alcance parece concentrado em quem já segue e na região. <strong>Confirmar com os Insights.</strong></li>
      <li>Nenhum vídeo de nutrição furou a bolha ainda. O trabalho: gancho mais forte, vídeo mais curto, tema que interessa ao Brasil todo.</li>
      <li>Bio e link precisam dizer "consulta online" antes de mandarmos gente de fora para o perfil.</li>
    </ul>
  </div>
</div>

<div class="destaque glow">
  <div class="kicker">O maior ativo para a especialização em intestino</div>
  <p>Ela já documentou o <strong>próprio tratamento de SIBO</strong>: preparação e teste respiratório, dia 1 da dieta low FODMAP,
  "o que eu comi em um domingo tratando SIBO" e "tratamento SIBO e emagrecimento". Ela não está só estudando o assunto, ela viveu.
  Dá para contar essa história <strong>sem se dizer especialista e sem usar resultado de paciente</strong>.</p>
</div>

<!-- PERGUNTAS -->
<div class="quebra"></div>
{blocos_html(blocos)}

<!-- PROPOSTAS -->
<div class="quebra"></div>
<div class="kicker">Propostas para validar com ela</div>
<h2 class="titulo">Como vamos trabalhar</h2>
<div class="rule"></div>

<div class="grid3">
  <div class="card">
    <div class="kicker">A · Fluxo de pautas</div>
    <ul class="lista">
      <li><strong>Um canal só:</strong> grupo de WhatsApp só para pautas, separado do dia a dia.</li>
      <li><strong>Ela manda:</strong> o tema, um áudio de até 1 min com a opinião dela e o link, se tiver.</li>
      <li><strong>Prazo:</strong> até o dia combinado entra no próximo bloco. Tema quente: roteiro em até 24h.</li>
      <li><strong>Volume:</strong> 2 a 3 pautas dela por semana. O resto vem do nosso monitoramento.</li>
    </ul>
  </div>
  <div class="card">
    <div class="kicker">B · Rotina de gravação</div>
    <ul class="lista">
      <li>Um bloco no consultório <strong>a cada 15 dias</strong>, de 2 a 3 horas.</li>
      <li><strong>6 a 8 vídeos</strong> por bloco, com 2 ou 3 trocas de roupa.</li>
      <li>Roteiros enviados <strong>2 dias antes</strong> do bloco.</li>
      <li>Entre blocos: bastidor real (atendimento, material, mercado) e temas quentes.</li>
    </ul>
  </div>
  <div class="card">
    <div class="kicker">C · Calendário</div>
    <ul class="lista">
      <li>Calendário compartilhado (Google Agenda ou Notion) com 3 cores: <strong>publi</strong>, <strong>nutrição</strong> e <strong>gravação</strong>.</li>
      <li>Ela lança a publi assim que fechar com a marca.</li>
      <li>Evitar vídeo de captação no mesmo dia de publi no feed: os dois disputam o mesmo seguidor.</li>
    </ul>
  </div>
</div>

<div class="secao">
  <div class="kicker">D · Linha editorial para alcance nacional</div>
  <h3 style="margin-top:1mm">Do primeiro play até a consulta</h3>
  <div class="grid3 funil">
    <div class="card"><h3>Alcance</h3><div class="obj">Chegar em quem não a conhece</div>
      <ul class="lista"><li>Mitos e verdades sobre intestino e emagrecimento</li><li>Reagir a tendências virais de nutrição</li>
      <li>Rótulos e produtos vendidos no Brasil todo</li><li>"Sinais de que seu intestino não está bem"</li>
      <li>"O que uma nutricionista come em um dia"</li><li>Temas em alta enviados por ela</li></ul></div>
    <div class="card"><h3>Confiança</h3><div class="obj">Fazer quem chegou ficar</div>
      <ul class="lista"><li>A jornada dela com SIBO (série)</li><li>Bastidores do atendimento</li><li>A jornada do curso de intestino</li>
      <li>O método dela</li><li>Respostas às perguntas mais frequentes</li></ul></div>
    <div class="card"><h3>Agendamento</h3><div class="obj">Virar consulta</div>
      <ul class="lista"><li>Como funciona a consulta online</li><li>Quebra de objeções</li><li>"Atendo você em qualquer cidade do Brasil"</li>
      <li>Chamada com palavra-chave para o direct</li></ul></div>
  </div>
</div>

<div class="secao" style="break-inside:avoid">
  <h3>Regras para os roteiros que precisam viajar para fora da cidade</h3>
  <ul class="checks">
    <li><span class="ok"></span><span>Nada que só faça sentido para quem é daqui. O sotaque e o jeito dela continuam: é charme, não barreira.</span></li>
    <li><span class="ok"></span><span>Gancho nos 2 primeiros segundos, sem "oi, gente" e sem apresentação.</span></li>
    <li><span class="ok"></span><span>Entre 15 e 45 segundos (hoje a mediana é 78).</span></li>
    <li><span class="ok"></span><span>Uma ideia por vídeo.</span></li>
    <li><span class="ok"></span><span>Texto na tela: a maioria assiste sem som.</span></li>
    <li><span class="ok"></span><span>Uma chamada só, no final.</span></li>
    <li><span class="ok"></span><span>Nada de afirmar especialização antes do certificado.</span></li>
  </ul>
</div>

<!-- COMBINADOS -->
<div class="secao" style="margin-top:11mm"></div>
<div class="kicker">Fechamento</div>
<h2 class="titulo">Combinados antes de sair da reunião</h2>
<div class="rule"></div>
<ul class="checks">
  <li><span class="box"></span><span>Posicionamento: emagrecimento + intestino, ou só intestino</span></li>
  <li><span class="box"></span><span>Como ela se apresenta até terminar o curso (e data prevista)</span></li>
  <li><span class="box"></span><span>Se a série da jornada com SIBO continua</span></li>
  <li><span class="box"></span><span>Meta de pacientes online por mês</span></li>
  <li><span class="box"></span><span>Quem responde o direct e em quanto tempo</span></li>
  <li><span class="box"></span><span>Regras do CRN: o que pode e o que não pode aparecer</span></li>
  <li><span class="box"></span><span>Canal de pautas criado</span></li>
  <li><span class="box"></span><span>Calendário compartilhado com as publis do próximo mês</span></li>
  <li><span class="box"></span><span>Data do primeiro bloco de gravação no consultório</span></li>
  <li><span class="box"></span><span>Formato do roteiro: decorado, teleprompter ou tópicos</span></li>
  <li><span class="box"></span><span>Fluxo e prazo de aprovação (roteiro e vídeo editado)</span></li>
  <li><span class="box"></span><span>Acessos: Instagram, Meta Business e Drive</span></li>
</ul>

<div class="secao">
  <h3>Anotações</h3>
  <div class="linhas">{"<div></div>" * 9}</div>
</div>
</body></html>"""


RODAPE = """<div style="width:100%;padding:0 16mm;display:flex;justify-content:space-between;align-items:center;
font-family:'DM Sans';font-size:7.5pt;color:#7A869E;-webkit-print-color-adjust:exact">
<span style="display:flex;align-items:center;gap:6px"><span style="display:inline-flex;align-items:center;gap:2px;font-weight:700;color:#000814">
<svg viewBox="0 0 10 8.66" style="width:6px;height:5.2px;fill:#2979FF"><polygon points="0,0 10,0 5,8.66"/></svg>nux</span>
<span>Briefing estratégico · Isabele Ribeiro · 03/11/2026</span></span>
<span style="font-family:'Bebas Neue';letter-spacing:2px;font-size:9pt;color:#2979FF"><span class="pageNumber"></span>
<span style="color:#9AA6BD">/ <span class="totalPages"></span></span></span></div>"""


def main():
    blocos = ler_blocos(MD)
    assert blocos and all(b["perguntas"] for b in blocos), "Não encontrei os blocos no markdown"

    with tempfile.TemporaryDirectory() as tmp, sync_playwright() as p:
        tmp = Path(tmp)
        # CHROMIUM_PATH aponta para um Chromium já instalado, se o do Playwright não estiver baixado
        exe = os.environ.get("CHROMIUM_PATH")
        browser = p.chromium.launch(executable_path=exe) if exe else p.chromium.launch()
        page = browser.new_page()

        page.set_content(capa_html(), wait_until="load")
        page.evaluate("document.fonts.ready")
        page.pdf(path=str(tmp / "capa.pdf"), format="A4", print_background=True,
                 margin={"top": "0", "right": "0", "bottom": "0", "left": "0"})

        page.set_content(miolo_html(blocos), wait_until="load")
        page.evaluate("document.fonts.ready")
        page.pdf(path=str(tmp / "miolo.pdf"), format="A4", print_background=True,
                 display_header_footer=True, header_template="<div></div>", footer_template=RODAPE,
                 margin={"top": "15mm", "right": "16mm", "bottom": "17mm", "left": "16mm"})
        browser.close()

        out = PdfWriter()
        for nome in ("capa.pdf", "miolo.pdf"):
            for pg in PdfReader(str(tmp / nome)).pages:
                out.add_page(pg)
        out.add_metadata({"/Title": "Briefing estratégico · Isabele Ribeiro", "/Author": "Nux"})
        with open(SAIDA, "wb") as f:
            out.write(f)
    print(f"PDF gerado: {SAIDA}")


if __name__ == "__main__":
    main()
