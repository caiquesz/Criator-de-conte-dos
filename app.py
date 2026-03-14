"""
🎨 AGÊNCIA DE CONTEÚDO — Frontend Streamlit
Interface minimalista para geração de carrosséis com Claude AI
"""

import streamlit as st
import json
import os
import re
import io
import zipfile
import urllib.request
import urllib.parse
from datetime import datetime
from pathlib import Path
import anthropic

# ── CONFIG ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="Agência de Conteúdo · Claude AI",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ── CSS ──────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }

.stApp { background: #ffffff; }

header[data-testid="stHeader"],
footer, #MainMenu { display: none !important; }

/* Tipografia */
h1 { color: #0f172a !important; font-weight: 700 !important; font-size: 28px !important; margin-bottom: 4px !important; }
h2 { color: #0f172a !important; font-weight: 600 !important; font-size: 20px !important; }
p { color: #475569; }

/* Inputs */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    border: 1.5px solid #e2e8f0 !important;
    border-radius: 12px !important;
    padding: 14px 16px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 15px !important;
    color: #0f172a !important;
    background: #f8fafc !important;
    box-shadow: none !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #2563eb !important;
    background: #fff !important;
    box-shadow: 0 0 0 3px rgba(37,99,235,0.08) !important;
}

/* Labels */
.stTextInput label, .stTextArea label,
.stSelectbox label, .stRadio > label {
    font-size: 11px !important;
    font-weight: 600 !important;
    letter-spacing: 0.8px !important;
    text-transform: uppercase !important;
    color: #94a3b8 !important;
    margin-bottom: 6px !important;
}

/* Botão principal */
div[data-testid="stButton"] > button {
    background: #2563eb !important;
    color: #fff !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 16px 32px !important;
    font-size: 15px !important;
    font-weight: 600 !important;
    width: 100% !important;
    letter-spacing: 0.3px !important;
    transition: all 0.15s !important;
    box-shadow: 0 2px 12px rgba(37,99,235,0.25) !important;
}
div[data-testid="stButton"] > button:hover {
    background: #1d4ed8 !important;
    box-shadow: 0 4px 20px rgba(37,99,235,0.35) !important;
    transform: translateY(-1px) !important;
}

/* Botão download */
div[data-testid="stDownloadButton"] > button {
    background: #fff !important;
    color: #2563eb !important;
    border: 1.5px solid #dbeafe !important;
    border-radius: 10px !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    padding: 10px 16px !important;
    width: 100% !important;
    transition: all 0.15s !important;
}
div[data-testid="stDownloadButton"] > button:hover {
    background: #eff6ff !important;
    border-color: #2563eb !important;
}

/* Radio */
.stRadio > div {
    flex-direction: row !important;
    gap: 10px !important;
}
.stRadio > div > label {
    background: #f8fafc !important;
    border: 1.5px solid #e2e8f0 !important;
    border-radius: 10px !important;
    padding: 10px 24px !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    color: #475569 !important;
    text-transform: none !important;
    letter-spacing: 0 !important;
    cursor: pointer !important;
    transition: all 0.15s !important;
}
.stRadio > div > label:has(input:checked) {
    border-color: #2563eb !important;
    background: #eff6ff !important;
    color: #2563eb !important;
}

/* Progress */
.stProgress > div > div > div > div {
    background: linear-gradient(90deg, #2563eb, #60a5fa) !important;
    border-radius: 4px !important;
}

/* Alertas limpos */
div[data-testid="stAlert"] {
    border-radius: 12px !important;
    border: none !important;
    font-size: 14px !important;
}

/* Expander */
.streamlit-expanderHeader {
    font-size: 14px !important;
    font-weight: 500 !important;
    color: #64748b !important;
    background: #f8fafc !important;
    border-radius: 10px !important;
    border: 1.5px solid #e2e8f0 !important;
}

/* Métricas */
div[data-testid="metric-container"] {
    background: #f8fafc;
    border: 1.5px solid #f1f5f9;
    border-radius: 12px;
    padding: 16px !important;
    text-align: center;
}
div[data-testid="metric-container"] label {
    font-size: 11px !important;
    color: #94a3b8 !important;
    font-weight: 600 !important;
    letter-spacing: 0.8px !important;
    text-transform: uppercase !important;
}
div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
    font-size: 22px !important;
    font-weight: 700 !important;
    color: #0f172a !important;
}

/* Imagens */
img { border-radius: 12px !important; }

/* Divider */
hr { border: none !important; border-top: 1px solid #f1f5f9 !important; margin: 28px 0 !important; }
</style>
""", unsafe_allow_html=True)


# ── BACKEND ──────────────────────────────────────────────────────
def baixar_imagem(query: str, destino: Path, pexels_key: str = "") -> str:
    headers = {"User-Agent": "Mozilla/5.0 Chrome/120.0.0.0 Safari/537.36"}
    if pexels_key:
        try:
            q = urllib.parse.quote(query)
            req = urllib.request.Request(
                f"https://api.pexels.com/v1/search?query={q}&per_page=5&orientation=square",
                headers={**headers, "Authorization": pexels_key}
            )
            with urllib.request.urlopen(req, timeout=10) as r:
                fotos = json.loads(r.read()).get("photos", [])
                if fotos:
                    req2 = urllib.request.Request(fotos[0]["src"]["large2x"], headers=headers)
                    with urllib.request.urlopen(req2, timeout=15) as r2:
                        destino.write_bytes(r2.read())
                    return str(destino.absolute())
        except Exception:
            pass
    seed = abs(hash(query)) % 1000
    req = urllib.request.Request(f"https://picsum.photos/seed/{seed}/1080/1080", headers=headers)
    with urllib.request.urlopen(req, timeout=15) as r:
        destino.write_bytes(r.read())
    return str(destino.absolute())


def gerar_html_slide(slide: dict, total: int, tema: str, paleta: dict, img_local: str = "") -> str:
    num = slide.get("numero", 1)
    titulo = slide.get("titulo", "")
    texto = slide.get("texto", "")
    emoji = slide.get("emoji", "✦")
    img_url = f"file:///{img_local.replace(chr(92), '/')}" if img_local else ""
    a, a2 = paleta["accent"], paleta["accent2"]
    ov = paleta["overlay"]

    if num == 1:
        corpo = f"""<div class="slide-inner capa">
  <div class="num-badge">01 / {total:02d}</div>
  <div class="emoji-big">{emoji}</div>
  <h1 class="titulo-capa">{titulo}</h1>
  <div class="subtema">{tema.upper()}</div>
  <div class="bar-accent"></div>
</div>"""
    elif num == total:
        corpo = f"""<div class="slide-inner cta">
  <div class="num-badge">{num:02d} / {total:02d}</div>
  <div class="emoji-big">{emoji}</div>
  <h2 class="titulo-cta">{titulo}</h2>
  <p class="texto-cta">{texto}</p>
  <div class="cta-pill">SALVA ✦ COMPARTILHA ✦ SEGUE</div>
</div>"""
    else:
        corpo = f"""<div class="slide-inner conteudo">
  <div class="num-badge">{num:02d} / {total:02d}</div>
  <div class="tag-topo">{emoji} {tema.upper()}</div>
  <h2 class="titulo-slide">{titulo}</h2>
  <div class="divider-line"></div>
  <p class="texto-slide">{texto}</p>
</div>"""

    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@300;400;500;600&display=swap');
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1080px;height:1080px;overflow:hidden;font-family:'DM Sans',sans-serif;background:{paleta["bg"]};position:relative}}
.bg-img{{position:absolute;inset:0;background:url('{img_url}') center/cover no-repeat;filter:saturate(1.1) brightness(0.85)}}
.overlay{{position:absolute;inset:0;background:{ov};opacity:0.65}}
.side-bar{{position:absolute;left:0;top:0;bottom:0;width:8px;background:linear-gradient(to bottom,{a},{a2})}}
.marca{{position:absolute;bottom:40px;right:48px;font-family:'Bebas Neue',sans-serif;font-size:18px;color:rgba(255,255,255,0.3);letter-spacing:3px}}
.slide-inner{{position:absolute;inset:0;padding:72px 72px 72px 88px;display:flex;flex-direction:column;justify-content:center;color:{paleta["text"]}}}
.num-badge{{position:absolute;top:44px;right:52px;font-family:'Bebas Neue',sans-serif;font-size:16px;letter-spacing:3px;color:rgba(255,255,255,0.45)}}
.capa{{justify-content:flex-end;padding-bottom:100px}}
.emoji-big{{font-size:64px;margin-bottom:24px}}
.titulo-capa{{font-family:'Bebas Neue',sans-serif;font-size:96px;line-height:.95;color:#fff;text-shadow:0 4px 24px rgba(0,0,0,.5);margin-bottom:20px;max-width:800px}}
.subtema{{font-size:14px;letter-spacing:5px;color:{a};font-weight:600;margin-bottom:24px}}
.bar-accent{{width:80px;height:4px;background:linear-gradient(90deg,{a},{a2});border-radius:2px}}
.tag-topo{{font-size:13px;letter-spacing:4px;color:{a};font-weight:600;text-transform:uppercase;margin-bottom:28px}}
.titulo-slide{{font-family:'Bebas Neue',sans-serif;font-size:72px;line-height:1;color:#fff;text-shadow:0 2px 20px rgba(0,0,0,.6);margin-bottom:24px;max-width:820px}}
.divider-line{{width:56px;height:3px;background:linear-gradient(90deg,{a},{a2});border-radius:2px;margin-bottom:28px}}
.texto-slide{{font-size:26px;line-height:1.65;color:rgba(255,255,255,.92);max-width:820px;font-weight:400;text-shadow:0 2px 12px rgba(0,0,0,.7)}}
.cta{{align-items:center;text-align:center;padding:80px}}
.titulo-cta{{font-family:'Bebas Neue',sans-serif;font-size:80px;color:#fff;line-height:1;margin-bottom:24px;text-shadow:0 4px 24px rgba(0,0,0,.5)}}
.texto-cta{{font-size:26px;color:rgba(255,255,255,.8);max-width:700px;line-height:1.6;margin-bottom:40px;font-weight:300}}
.cta-pill{{background:linear-gradient(135deg,{a},{a2});color:#fff;font-family:'Bebas Neue',sans-serif;font-size:22px;letter-spacing:4px;padding:18px 48px;border-radius:100px}}
</style></head><body>
<div class="bg-img"></div>
<div class="overlay"></div>
<div class="side-bar"></div>
{corpo}
<div class="marca">@[SEU_USERNAME]</div>
</body></html>"""


def renderizar_png(html_path: str, png_path: str):
    import subprocess
    import sys
    render_script = Path(__file__).parent / "render_slide.py"
    result = subprocess.run(
        [sys.executable, str(render_script), html_path, png_path],
        capture_output=True, text=True, timeout=40
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout or "Erro desconhecido no Playwright")


def pesquisar_tendencias(tema: str, plataforma: str, api_key: str) -> str:
    """Passo 1: Claude pesquisa o que está funcionando no tema antes de criar."""
    client = anthropic.Anthropic(api_key=api_key)

    prompt = f"""Você é um analista de conteúdo digital especializado em {plataforma}.

Analise o tema "{tema}" e responda de forma direta:

1. PADRÕES VIRAIS: Quais formatos de carrossel funcionam melhor para esse tema? (ex: listas, antes/depois, mitos vs verdades, passo a passo)
2. ÂNGULO VENCEDOR: Qual ângulo/perspectiva gera mais engajamento? (ex: polêmica, revelação, erro comum, segredo)
3. LINGUAGEM: Como o público que consome esse conteúdo fala? Gírias, expressões, tom?
4. GANCHO: Qual tipo de frase de abertura para esse tema faz as pessoas pararem o scroll?
5. SEQUÊNCIA LÓGICA: Como deve ser a jornada emocional do leitor slide a slide? (ex: dor → esperança → solução → prova → ação)
6. OBJEÇÕES: Quais são as maiores dúvidas/resistências do público sobre esse tema?

Seja específico e prático. Máximo 300 palavras."""

    resposta = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}]
    )
    return resposta.content[0].text


def gerar_conteudo_claude(tema: str, plataforma: str, api_key: str, tendencias: str = "") -> dict:
    client = anthropic.Anthropic(api_key=api_key)

    contexto_tendencias = f"""
PESQUISA PRÉVIA SOBRE O TEMA (use isso para criar conteúdo mais preciso e viral):
{tendencias}
""" if tendencias else ""

    prompt = f"""Você é um estrategista de conteúdo viral com 10 anos de experiência em {plataforma}.
{contexto_tendencias}
Crie um carrossel de 7 slides sobre: "{tema}"

━━ ESTRUTURA OBRIGATÓRIA DE STORYTELLING ━━

Slide 1 — GANCHO (para o scroll)
- Começa com número, dado chocante ou pergunta que dói
- Promete uma transformação específica
- Ex: "X pessoas perdem dinheiro com isso todo dia (e você pode ser uma delas)"

Slide 2 — DOR / PROBLEMA
- Aprofunda o problema que o leitor já sente
- Usa linguagem empática, não julgadora
- Faz o leitor pensar "isso sou eu"

Slide 3 — REVELAÇÃO / VIRADA
- O insight que muda tudo
- Algo que vai contra o senso comum
- Começa com "O que ninguém te conta é..."

Slide 4 — COMO FUNCIONA (mecanismo)
- Explica o porquê de forma simples
- Usa analogia ou exemplo concreto
- Dá credibilidade ao conteúdo

Slide 5 — PROVA / EXEMPLO REAL
- Caso concreto, dado, estatística ou exemplo prático
- Torna o abstrato em real
- "Na prática, isso significa..."

Slide 6 — APLICAÇÃO PRÁTICA
- O que o leitor pode fazer AGORA
- Passo a passo simples (2-3 ações)
- Remove a desculpa de "não sei por onde começar"

Slide 7 — CTA COM URGÊNCIA
- Por que agir agora e não depois
- Consequência de não agir
- Chamada clara para salvar/seguir/comentar

━━ REGRAS DE ESCRITA ━━
- Linguagem brasileira direta, sem enrolação
- Cada slide: 3 a 5 linhas densas de conteúdo
- Sem bullet points no texto — parágrafos corridos
- Títulos curtos e impactantes (máx 6 palavras)
- Nunca use "aprenda", "descubra", "veja" — seja direto

Para cada slide, "query_imagem" em INGLÊS específico para o contexto visual.

Responda APENAS JSON válido:
{{
  "titulo_serie": "...",
  "angulo": "...",
  "paleta": {{
    "nome": "dark-orange",
    "bg": "#0a0a0a",
    "accent": "#FF4D00",
    "accent2": "#FF8C42",
    "text": "#ffffff",
    "overlay": "linear-gradient(160deg, rgba(0,0,0,0.75) 0%, rgba(10,10,10,0.92) 100%)"
  }},
  "hashtags": ["...", "..."],
  "melhor_horario": "19:00",
  "slides": [
    {{"numero": 1, "emoji": "🔥", "titulo": "...", "texto": "...", "query_imagem": "..."}}
  ]
}}

Paletas por tom:
- Urgente/impacto: accent #FF4D00, bg #0a0a0a
- Premium/luxo: accent #C9A84C, bg #0d0d0d
- Tech/futuro: accent #00E5FF, bg #050510
- Growth/verde: accent #00E676, bg #071a0e
- Confiança/azul: accent #2563eb, bg #050a1a"""

    resposta = ""
    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=3500,
        messages=[{"role": "user", "content": prompt}]
    ) as stream:
        for text in stream.text_stream:
            resposta += text

    json_str = re.sub(r'```(?:json)?', '', resposta.strip()).strip()
    try:
        return json.loads(json_str)
    except Exception:
        match = re.search(r'\{.*\}', json_str, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise ValueError("Erro ao parsear resposta do Claude.")


# ── INTERFACE ────────────────────────────────────────────────────
def main():
    # ── Header ───────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style='margin-bottom: 8px;'>
        <span style='font-size:32px; font-weight:700; color:#0f172a;'>Agência de Conteúdo</span>
        <span style='font-size:28px; margin-left:10px;'>🤖</span>
    </div>
    <p style='color:#94a3b8; font-size:14px; margin-bottom:32px; font-weight:400;'>
        Carrosséis visuais prontos para postar · Powered by Claude AI
    </p>
    """, unsafe_allow_html=True)

    st.divider()

    # ── API Keys ─────────────────────────────────────────────────
    api_key = st.session_state.get("anthropic_key", os.environ.get("ANTHROPIC_API_KEY", ""))
    px_key = st.session_state.get("pexels_key", os.environ.get("PEXELS_API_KEY", ""))

    with st.expander("🔑  Configurar API Keys", expanded=not bool(api_key)):
        c1, c2 = st.columns(2)
        with c1:
            new_key = st.text_input("Anthropic API Key", type="password",
                                    placeholder="sk-ant-...", value=api_key)
        with c2:
            new_px = st.text_input("Pexels API Key (opcional)", type="password",
                                   placeholder="Leave empty para usar Picsum", value=px_key)
        if st.button("Salvar"):
            if new_key:
                st.session_state["anthropic_key"] = new_key
                st.session_state["pexels_key"] = new_px
                st.success("Configurações salvas!")
                st.rerun()
            else:
                st.error("Insira a Anthropic API Key")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Formulário ───────────────────────────────────────────────
    tema = st.text_area(
        "Tema do carrossel",
        placeholder="Ex: Por que investir em tráfego pago em 2026?",
        height=90
    )

    plataforma = st.radio("Plataforma", ["Instagram", "LinkedIn"], horizontal=True)

    st.markdown("<br>", unsafe_allow_html=True)
    gerar = st.button("✦  Gerar Carrossel")

    # ── Geração ──────────────────────────────────────────────────
    if gerar:
        if not api_key:
            st.error("Configure sua Anthropic API Key primeiro.")
            return
        if not tema.strip():
            st.error("Digite o tema do carrossel.")
            return

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        pasta = Path(f"carrossel_{ts}")
        pasta.mkdir(exist_ok=True)
        (pasta / "html").mkdir(exist_ok=True)

        st.divider()

        # Status container limpo
        status_box = st.empty()
        progress = st.progress(0)

        arquivos_png = []
        dados = {}

        try:
            # Passo 1 — Pesquisa de tendências
            status_box.markdown("""
            <div style='background:#eff6ff;border-radius:12px;padding:16px 20px;color:#1d4ed8;font-size:14px;font-weight:500;'>
                🔍 &nbsp; Analisando o que está viralizando sobre esse tema...
            </div>""", unsafe_allow_html=True)
            progress.progress(8)
            tendencias = pesquisar_tendencias(tema.strip(), plataforma, api_key)

            # Passo 2 — Gera conteúdo com contexto
            status_box.markdown("""
            <div style='background:#eff6ff;border-radius:12px;padding:16px 20px;color:#1d4ed8;font-size:14px;font-weight:500;'>
                🧠 &nbsp; Claude criando carrossel com storytelling otimizado...
            </div>""", unsafe_allow_html=True)
            progress.progress(18)

            dados = gerar_conteudo_claude(tema.strip(), plataforma, api_key, tendencias)
            slides = dados.get("slides", [])
            paleta = dados.get("paleta", {
                "bg": "#0a0a0a", "accent": "#FF4D00", "accent2": "#FF8C42",
                "text": "#ffffff",
                "overlay": "linear-gradient(160deg,rgba(0,0,0,0.75) 0%,rgba(10,10,10,0.92) 100%)"
            })
            hashtags = dados.get("hashtags", [])
            horario = dados.get("melhor_horario", "19:00")
            progress.progress(25)

            for i, slide in enumerate(slides):
                num = slide.get("numero", 1)
                query = slide.get("query_imagem", tema)
                pct = 25 + int((i / len(slides)) * 65)

                status_box.markdown(f"""
                <div style='background:#eff6ff;border-radius:12px;padding:16px 20px;color:#1d4ed8;font-size:14px;font-weight:500;'>
                    🖼️ &nbsp; Slide {num}/{len(slides)} — baixando imagem e renderizando...
                </div>""", unsafe_allow_html=True)
                progress.progress(pct)

                img_path = pasta / f"img_{num:02d}.jpg"
                img_local = ""
                try:
                    img_local = baixar_imagem(query, img_path, px_key)
                except Exception:
                    pass

                html_content = gerar_html_slide(slide, len(slides), tema.strip(), paleta, img_local)
                html_path = pasta / "html" / f"slide_{num:02d}.html"
                html_path.write_text(html_content, encoding="utf-8")

                png_path = pasta / f"slide_{num:02d}.png"
                try:
                    renderizar_png(str(html_path.absolute()), str(png_path))
                    if png_path.exists():
                        arquivos_png.append(png_path)
                except Exception as e:
                    import traceback
                    st.error(f"Erro no slide {num}: {type(e).__name__}: {e}\n\n{traceback.format_exc()}")

            progress.progress(100)
            status_box.markdown("""
            <div style='background:#f0fdf4;border-radius:12px;padding:16px 20px;color:#166534;font-size:14px;font-weight:500;'>
                ✅ &nbsp; Carrossel gerado com sucesso!
            </div>""", unsafe_allow_html=True)

        except Exception as e:
            progress.empty()
            status_box.error(f"Erro: {str(e)}")
            return

        # ── Resultado ────────────────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        st.divider()
        st.markdown("### Seu carrossel")
        st.markdown("<br>", unsafe_allow_html=True)

        # Métricas
        hashtags = dados.get("hashtags", [])
        horario = dados.get("melhor_horario", "19:00")
        angulo = dados.get("angulo", "")
        c1, c2, c3 = st.columns(3)
        c1.metric("Slides gerados", len(arquivos_png))
        c2.metric("Melhor horário", horario)
        c3.metric("Plataforma", plataforma)

        # Ângulo escolhido
        if angulo:
            st.markdown(f"""
            <div style='background:#f8fafc;border-left:3px solid #2563eb;border-radius:0 10px 10px 0;
                        padding:14px 18px;margin:16px 0;color:#334155;font-size:14px;'>
                <strong style='color:#2563eb;'>Ângulo escolhido:</strong> {angulo}
            </div>""", unsafe_allow_html=True)

        # Análise de tendências (expansível)
        if tendencias:
            with st.expander("🔍  Ver análise de tendências usada"):
                st.markdown(f"<div style='color:#475569;font-size:14px;line-height:1.7;'>{tendencias}</div>",
                           unsafe_allow_html=True)

        # Hashtags
        if hashtags:
            st.markdown("<br>", unsafe_allow_html=True)
            chips = "".join(
                f"<span style='display:inline-block;background:#eff6ff;color:#2563eb;border-radius:20px;"
                f"padding:5px 14px;font-size:13px;font-weight:500;margin:3px;'>#{h}</span>"
                for h in hashtags
            )
            st.markdown(f"<div style='margin-bottom:8px;'>{chips}</div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Grid de slides
        if arquivos_png:
            cols = st.columns(2)
            for i, png in enumerate(arquivos_png):
                if png.exists():
                    with cols[i % 2]:
                        st.image(png.read_bytes(), use_container_width=True)
                        st.download_button(
                            f"⬇  Baixar slide {i+1}",
                            data=png.read_bytes(),
                            file_name=png.name,
                            mime="image/png",
                            key=f"dl_{i}"
                        )
                        st.markdown("<br>", unsafe_allow_html=True)

            # ZIP
            st.divider()
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w") as zf:
                for p in arquivos_png:
                    if p.exists():
                        zf.write(p, p.name)
            buf.seek(0)
            st.download_button(
                "⬇  Baixar todos os slides (ZIP)",
                data=buf.getvalue(),
                file_name=f"carrossel_{ts}.zip",
                mime="application/zip",
                use_container_width=True
            )
        else:
            st.warning("Nenhum PNG foi gerado. Verifique se o Playwright está instalado corretamente.")
            st.code("python -m playwright install chromium")


if __name__ == "__main__":
    main()
