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
import subprocess
import sys
import urllib.request
import urllib.parse
from datetime import datetime
from pathlib import Path
import anthropic

@st.cache_resource(show_spinner=False)
def instalar_playwright():
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"],
                   capture_output=True)

instalar_playwright()

# ── CONFIG ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="Agência de Conteúdo · Claude AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CSS ──────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Bebas+Neue&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }

.stApp { background: #f8fafc; }
.stMain { background: #f8fafc; }

header[data-testid="stHeader"], footer, #MainMenu { display: none !important; }

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {
    background: #ffffff !important;
    border-right: 1px solid #e2e8f0 !important;
}
[data-testid="stSidebar"] > div { padding: 32px 24px !important; }

/* ── MAIN CONTENT ── */
.block-container {
    padding: 40px 48px !important;
    max-width: 1000px !important;
}

/* ── HERO ── */
.hero-badge {
    display: inline-flex; align-items: center; gap: 6px;
    background: #eff6ff; color: #2563eb;
    font-size: 12px; font-weight: 600; letter-spacing: 1px;
    text-transform: uppercase; padding: 6px 14px;
    border-radius: 100px; margin-bottom: 20px;
    border: 1px solid #dbeafe;
}
.hero-title {
    font-size: 48px; font-weight: 800; color: #0f172a;
    line-height: 1.1; margin-bottom: 12px; letter-spacing: -1px;
}
.hero-title span {
    background: linear-gradient(135deg, #2563eb, #60a5fa);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.hero-sub {
    font-size: 16px; color: #64748b; margin-bottom: 8px;
    font-weight: 400; line-height: 1.6;
}
.hero-stats {
    display: flex; gap: 24px; margin-top: 20px; flex-wrap: wrap;
}
.stat-item {
    display: flex; align-items: center; gap: 8px;
    font-size: 13px; color: #64748b; font-weight: 500;
}
.stat-dot {
    width: 6px; height: 6px; border-radius: 50%;
    background: #2563eb;
}

/* ── CARD FORM ── */
.form-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 20px;
    padding: 32px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 4px 16px rgba(0,0,0,0.04);
    margin-top: 32px;
}

/* ── INPUTS ── */
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
    transition: all 0.15s !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #2563eb !important;
    background: #fff !important;
    box-shadow: 0 0 0 3px rgba(37,99,235,0.08) !important;
}

/* ── LABELS ── */
.stTextInput label, .stTextArea label,
.stSelectbox label, .stRadio > label {
    font-size: 11px !important; font-weight: 700 !important;
    letter-spacing: 1px !important; text-transform: uppercase !important;
    color: #94a3b8 !important; margin-bottom: 8px !important;
}

/* ── BOTÃO PRINCIPAL ── */
div[data-testid="stButton"] > button {
    background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
    color: #fff !important; border: none !important;
    border-radius: 14px !important; padding: 18px 32px !important;
    font-size: 15px !important; font-weight: 700 !important;
    width: 100% !important; letter-spacing: 0.5px !important;
    transition: all 0.2s !important;
    box-shadow: 0 4px 16px rgba(37,99,235,0.3) !important;
}
div[data-testid="stButton"] > button:hover {
    background: linear-gradient(135deg, #1d4ed8, #1e40af) !important;
    box-shadow: 0 8px 24px rgba(37,99,235,0.4) !important;
    transform: translateY(-2px) !important;
}

/* ── BOTÃO DOWNLOAD ── */
div[data-testid="stDownloadButton"] > button {
    background: #fff !important; color: #2563eb !important;
    border: 1.5px solid #dbeafe !important; border-radius: 10px !important;
    font-size: 13px !important; font-weight: 600 !important;
    padding: 10px 16px !important; width: 100% !important;
    transition: all 0.15s !important;
}
div[data-testid="stDownloadButton"] > button:hover {
    background: #eff6ff !important; border-color: #2563eb !important;
}

/* ── RADIO ── */
.stRadio > div { flex-direction: row !important; gap: 10px !important; }
.stRadio > div > label {
    background: #f8fafc !important; border: 1.5px solid #e2e8f0 !important;
    border-radius: 12px !important; padding: 12px 28px !important;
    font-size: 14px !important; font-weight: 600 !important;
    color: #475569 !important; text-transform: none !important;
    letter-spacing: 0 !important; cursor: pointer !important;
    transition: all 0.15s !important;
}
.stRadio > div > label:has(input:checked) {
    border-color: #2563eb !important;
    background: #eff6ff !important; color: #2563eb !important;
    box-shadow: 0 0 0 3px rgba(37,99,235,0.1) !important;
}

/* ── PROGRESS ── */
.stProgress > div > div > div > div {
    background: linear-gradient(90deg, #2563eb, #60a5fa) !important;
    border-radius: 4px !important;
}
.stProgress > div > div {
    background: #e2e8f0 !important; border-radius: 4px !important;
}

/* ── MÉTRICAS ── */
div[data-testid="metric-container"] {
    background: #fff; border: 1px solid #e2e8f0;
    border-radius: 16px; padding: 20px !important;
    text-align: center;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}
div[data-testid="metric-container"] label {
    font-size: 10px !important; color: #94a3b8 !important;
    font-weight: 700 !important; letter-spacing: 1px !important;
    text-transform: uppercase !important;
}
div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
    font-size: 24px !important; font-weight: 800 !important; color: #0f172a !important;
}

/* ── CARDS DE SLIDE ── */
.slide-card {
    background: #fff;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    transition: all 0.2s;
    margin-bottom: 16px;
}
.slide-card:hover {
    box-shadow: 0 8px 24px rgba(0,0,0,0.1);
    transform: translateY(-2px);
}

/* ── SIDEBAR ITEMS ── */
[data-testid="stSidebar"] .stTextInput > div > div > input {
    background: #f8fafc !important;
}

/* ── EXPANDER ── */
details { border: 1px solid #e2e8f0 !important; border-radius: 12px !important; }
summary {
    font-size: 13px !important; font-weight: 600 !important;
    color: #475569 !important; padding: 12px 16px !important;
}

/* ── DIVIDER ── */
hr { border: none !important; border-top: 1px solid #f1f5f9 !important; margin: 32px 0 !important; }

/* ── IMAGENS ── */
img { border-radius: 12px !important; }

/* ── STEPPER ── */
.stepper {
    display: flex; align-items: center; gap: 0;
    margin: 24px 0; padding: 20px 24px;
    background: #fff; border: 1px solid #e2e8f0;
    border-radius: 16px;
}
.step {
    display: flex; align-items: center; gap: 10px;
    flex: 1; position: relative;
}
.step-num {
    width: 32px; height: 32px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 13px; font-weight: 700; flex-shrink: 0;
}
.step-num.active { background: #2563eb; color: #fff; }
.step-num.done { background: #dcfce7; color: #16a34a; }
.step-num.pending { background: #f1f5f9; color: #94a3b8; }
.step-label { font-size: 13px; font-weight: 500; color: #475569; }
.step-label.active { color: #2563eb; font-weight: 600; }
.step-label.done { color: #16a34a; }
.step-line { flex: 1; height: 1px; background: #e2e8f0; margin: 0 12px; }
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


def pesquisar_tendencias(tema: str, plataforma: str, api_key: str, insights: str = "") -> str:
    """Passo 1: Claude pesquisa o que está funcionando no tema antes de criar."""
    client = anthropic.Anthropic(api_key=api_key)

    contexto_insights = f"\nCONTEXTO FORNECIDO PELO CRIADOR:\n{insights}\n" if insights.strip() else ""

    prompt = f"""Você é um analista de conteúdo digital com experiência em {plataforma}.
{contexto_insights}
Estude o tema "{tema}" considerando múltiplas perspectivas e responda:

1. ESTRUTURA IDEAL: Qual sequência narrativa funciona melhor? Considere: problema > solução, antes > depois, mito > realidade, pergunta > resposta progressiva. Qual gera mais salvamentos e comentários reflexivos?

2. GANCHO SEM CLICKBAIT: Que tipo de abertura prende genuinamente? O gancho deve contextualizar uma situação real que o leitor reconhece, não criar ansiedade ou usar estatísticas alarmistas.

3. PERSPECTIVAS E NUANCES: Quais os diferentes pontos de vista legítimos sobre esse assunto? Quem discorda e por quê? Quais exceções existem? Como abordar sem excluir leitores com contextos diferentes?

4. IMAGENS POR ETAPA: Para cada momento da narrativa, que cena concreta representa bem o conteúdo visualmente? Descreva ambiente, ação da pessoa, iluminação e tom emocional. Evite sugerir conceitos abstratos como imagem.

Seja equilibrado e analítico. Máximo 300 palavras."""

    resposta = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=700,
        messages=[{"role": "user", "content": prompt}]
    )
    return resposta.content[0].text


def gerar_conteudo_claude(tema: str, plataforma: str, api_key: str, tendencias: str = "", insights: str = "") -> dict:
    client = anthropic.Anthropic(api_key=api_key)

    bloco_tendencias = f"\nANÁLISE PRÉVIA DO TEMA:\n{tendencias}\n" if tendencias else ""
    bloco_insights = f"\nINSIGHTS E CONTEXTO DO CRIADOR (use com prioridade):\n{insights}\n" if insights.strip() else ""

    prompt = f"""Você é um criador de conteúdo experiente em {plataforma}, com foco em conteúdo que gera reflexão genuína.
{bloco_tendencias}{bloco_insights}
Crie um carrossel de 7 slides sobre: "{tema}"

FILOSOFIA DO CONTEÚDO

Escreva como alguém que viveu o assunto e quer compartilhar o que aprendeu. Não como um copywriter tentando vender algo.
Reconheça que o tema tem nuances. Evite posições absolutas quando a realidade é mais complexa.
O leitor deve terminar sentindo que aprendeu algo real, não que foi provocado a reagir.

ESTRUTURA NARRATIVA

Slide 1 — GANCHO COM CONTEXTO REAL
Descreva uma situação concreta que o leitor reconhece na própria vida. Abra uma pergunta ou tensão que ele vai querer ver resolvida. Não use estatísticas alarmistas nem frases como "X pessoas estão errando isso". O título deve ser algo que o leitor concorda ou que o deixa genuinamente curioso.

Slide 2 — O CONTEXTO
Explique por que o tema importa no momento atual. Apresente a complexidade sem simplificar demais. Reconheça que existem diferentes situações e perfis de pessoas. Conecte ao cotidiano do leitor sem generalizar.

Slide 3 — A TENSÃO
Mostre onde a maioria das pessoas trava nesse assunto e por que é natural travar ali. Não culpe o leitor. Formule a pergunta central que o carrossel vai responder.

Slide 4 — A VIRADA
O ponto de vista que reorganiza como o leitor enxerga o problema. Pode contrariar o senso comum, mas com argumento sólido. Reconheça exceções. Use uma analogia do cotidiano para tornar o conceito concreto.

Slide 5 — NA PRÁTICA
Mostre como funciona de verdade com um exemplo realista, não o caso extremo de sucesso. Inclua o processo, não só o resultado. Mencione o que pode dar errado e como lidar.

ATENÇÃO SLIDE 5: Se o criador forneceu um case real nos insights, use-o aqui com os detalhes exatos que ele forneceu. Se não forneceu nenhum case, descreva uma situação genérica e realista SEM inventar nomes, números ou atribuir resultados a pessoas reais. Nunca invente estatísticas. Se quiser citar dado, use linguagem como "segundo estudos da área" sem fabricar números específicos.

Slide 6 — O PRÓXIMO PASSO
Uma ação específica que qualquer pessoa pode fazer hoje. Considere que diferentes leitores estão em momentos diferentes. Remova a pressão, não aumente.

Slide 7 — FECHAMENTO COM CONVITE
Sintetize a ideia central em uma frase memorável. Faça uma pergunta genuína para o leitor refletir. O CTA deve ser natural, sem urgência artificial.

REGRAS DE ESCRITA

Tom: voz ativa, presente, como se estivesse conversando com alguém. Não como lista de instruções.
Estrutura do texto: parágrafos corridos. Proibido bullet points no campo "texto".
Pontuação: use vírgulas e pontos. Não use traço longo (—) como separador de ideias. Use ponto e vírgula ou nova frase quando necessário.
Comprimento: 3 a 5 frases por slide. Densas mas respiráveis.
Títulos: até 6 palavras, diretos, sem clickbait.
Proibido: "descubra", "aprenda", "simples assim", "todo mundo sabe", afirmações absolutas sem contexto, asteriscos para negrito no texto, hífens como marcadores de lista.
Permitido: "pode ser que", "dependendo do contexto", "na minha visão", "uma das formas".
Se o tema tiver dois lados legítimos, apresente os dois. O leitor é inteligente.

REGRAS PARA IMAGEM (query_imagem)

O campo query_imagem deve estar em INGLÊS e descrever uma cena concreta que ILUSTRA visualmente o que o texto do slide está dizendo, não o título nem palavras-chave abstratas.

Formato obrigatório: [ação ou emoção da pessoa] [tipo de pessoa] [ambiente específico] [luz e tom emocional]

Exemplos corretos:
- Para slide sobre posicionamento de marca: "confident woman presenting brand strategy on whiteboard to small team modern studio natural light"
- Para slide sobre travamento em decisões: "person staring at blank notebook at desk late afternoon dim light indecisive"
- Para slide sobre resultado real: "small shop owner smiling while checking phone behind counter warm morning light"

Exemplos errados: "success", "branding", "business strategy", "people working", "marketing".

Se o conceito for abstrato, use uma metáfora visual concreta: posicionamento pode ser representado por alguém escolhendo onde colocar uma placa na porta de um negócio.

Responda APENAS JSON válido:
{{
  "titulo_serie": "...",
  "angulo": "...",
  "paleta": {{
    "nome": "amber",
    "bg": "#0c0a00",
    "accent": "#F59E0B",
    "accent2": "#FCD34D",
    "text": "#ffffff",
    "overlay": "linear-gradient(160deg, rgba(0,0,0,0.72) 0%, rgba(12,10,0,0.90) 100%)"
  }},
  "hashtags": ["...", "..."],
  "melhor_horario": "19:00",
  "slides": [
    {{"numero": 1, "emoji": "💡", "titulo": "...", "texto": "...", "query_imagem": "..."}}
  ]
}}

Paletas por tom emocional:
- Reflexivo/humano: accent #F59E0B, bg #0c0a00 (ambar)
- Confianca/clareza: accent #2563eb, bg #050a1a (azul)
- Crescimento/esperanca: accent #10b981, bg #071a0e (verde)
- Premium/autoridade: accent #C9A84C, bg #0d0d0d (dourado)
- Tech/inovacao: accent #00E5FF, bg #050510 (ciano)
- Urgente/transformacao: accent #FF4D00, bg #0a0a0a (laranja)"""

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
    # ── SIDEBAR — API Keys ───────────────────────────────────────
    with st.sidebar:
        st.markdown("""
        <div style='margin-bottom:28px;'>
            <div style='font-size:22px; font-weight:800; color:#0f172a; letter-spacing:-0.5px;'>🤖 Agência</div>
            <div style='font-size:12px; color:#94a3b8; font-weight:500; margin-top:2px;'>Powered by Claude AI</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='font-size:11px;font-weight:700;color:#94a3b8;letter-spacing:1px;text-transform:uppercase;margin-bottom:12px;'>Configurações</div>", unsafe_allow_html=True)

        api_key_env = os.environ.get("ANTHROPIC_API_KEY", "")
        px_key_env = os.environ.get("PEXELS_API_KEY", "")

        new_key = st.text_input("Anthropic API Key", type="password",
                                placeholder="sk-ant-...",
                                value=st.session_state.get("anthropic_key", api_key_env))
        new_px = st.text_input("Pexels API Key", type="password",
                               placeholder="Opcional — usa Picsum sem ela",
                               value=st.session_state.get("pexels_key", px_key_env))

        if st.button("Salvar configurações"):
            if new_key:
                st.session_state["anthropic_key"] = new_key
                st.session_state["pexels_key"] = new_px
                st.success("Salvo!")
            else:
                st.error("Insira a Anthropic API Key")

        st.markdown("<br>", unsafe_allow_html=True)
        st.divider()
        st.markdown("""
        <div style='font-size:12px;color:#94a3b8;line-height:1.7;'>
            <strong style='color:#475569;'>Como funciona:</strong><br>
            1. Cole seu tema<br>
            2. Escolha a plataforma<br>
            3. Claude analisa tendências<br>
            4. Gera 7 slides com storytelling<br>
            5. Renderiza PNGs 1080×1080px<br>
            6. Baixe e poste!
        </div>
        """, unsafe_allow_html=True)

    api_key = st.session_state.get("anthropic_key", os.environ.get("ANTHROPIC_API_KEY", ""))
    px_key = st.session_state.get("pexels_key", os.environ.get("PEXELS_API_KEY", ""))

    # ── HERO ─────────────────────────────────────────────────────
    st.markdown("""
    <div style='padding: 8px 0 0 0;'>
        <div class='hero-badge'>✦ Carrosséis com IA</div>
        <div class='hero-title'>Crie conteúdo que<br><span>para o scroll.</span></div>
        <div class='hero-sub'>Cole seu tema, escolha a plataforma e o Claude cria 7 slides otimizados,<br>com storytelling, imagens e paleta profissional. Pronto para postar.</div>
        <div class='hero-stats'>
            <div class='stat-item'><div class='stat-dot'></div>7 slides por carrossel</div>
            <div class='stat-item'><div class='stat-dot'></div>1080 × 1080px</div>
            <div class='stat-item'><div class='stat-dot'></div>Instagram & LinkedIn</div>
            <div class='stat-item'><div class='stat-dot'></div>Download em PNG + ZIP</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── FORM CARD ────────────────────────────────────────────────
    st.markdown("<div class='form-card'>", unsafe_allow_html=True)

    entrada = st.text_area(
        "Tema e contexto",
        placeholder=(
            'Coloque o tema entre aspas e, abaixo, seus insights.\n\n'
            '"Posicionamento de marca no Instagram"\n\n'
            'Minha agência atendeu uma loja de roupas que dobrou o engajamento mudando '
            'só a forma como falava nos posts. Quero mostrar que não é sobre anunciar, '
            'é sobre como você se posiciona. Público: donos de pequenos negócios.'
        ),
        height=180
    )

    plataforma = st.radio("Plataforma", ["📸  Instagram", "💼  LinkedIn"], horizontal=True)
    plataforma = "Instagram" if "Instagram" in plataforma else "LinkedIn"

    st.markdown("<br>", unsafe_allow_html=True)
    gerar = st.button("✦  Gerar Carrossel")
    st.markdown("</div>", unsafe_allow_html=True)

    # ── Geração ──────────────────────────────────────────────────
    if gerar:
        if not api_key:
            st.error("Configure sua Anthropic API Key na barra lateral.")
            return
        if not entrada.strip():
            st.error("Digite o tema do carrossel.")
            return

        # Extrai tema (entre aspas) e insights (o resto)
        import re as _re
        match_tema = _re.search(r'["\u201c\u201d\u2018\u2019](.+?)["\u201c\u201d\u2018\u2019]', entrada, _re.DOTALL)
        if match_tema:
            tema = match_tema.group(1).strip()
            insights = entrada.replace(match_tema.group(0), "").strip()
        else:
            tema = entrada.strip()
            insights = ""

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        pasta = Path(f"carrossel_{ts}")
        pasta.mkdir(exist_ok=True)
        (pasta / "html").mkdir(exist_ok=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Stepper visual
        stepper = st.empty()
        status_box = st.empty()
        progress = st.progress(0)

        def render_stepper(etapa):
            steps = ["Pesquisando", "Criando", "Renderizando", "Pronto"]
            items = ""
            for i, s in enumerate(steps):
                if i < etapa:
                    cls = "done"; num = "✓"
                elif i == etapa:
                    cls = "active"; num = str(i+1)
                else:
                    cls = "pending"; num = str(i+1)
                sep = "<div class='step-line'></div>" if i < len(steps)-1 else ""
                items += f"<div class='step'><div class='step-num {cls}'>{num}</div><div class='step-label {cls}'>{s}</div></div>{sep}"
            stepper.markdown(f"<div class='stepper'>{items}</div>", unsafe_allow_html=True)

        arquivos_png = []
        dados = {}
        tendencias = ""

        try:
            render_stepper(0)
            status_box.markdown("""<div style='background:#eff6ff;border-radius:12px;padding:14px 18px;
                color:#1d4ed8;font-size:14px;font-weight:500;'>
                🔍 &nbsp; Analisando tendências e padrões virais para esse tema...</div>""",
                unsafe_allow_html=True)
            progress.progress(8)
            tendencias = pesquisar_tendencias(tema, plataforma, api_key, insights)

            render_stepper(1)
            status_box.markdown("""<div style='background:#eff6ff;border-radius:12px;padding:14px 18px;
                color:#1d4ed8;font-size:14px;font-weight:500;'>
                🧠 &nbsp; Claude criando storytelling otimizado para máximo engajamento...</div>""",
                unsafe_allow_html=True)
            progress.progress(18)

            dados = gerar_conteudo_claude(tema, plataforma, api_key, tendencias, insights)
            slides = dados.get("slides", [])
            paleta = dados.get("paleta", {
                "bg": "#0a0a0a", "accent": "#FF4D00", "accent2": "#FF8C42",
                "text": "#ffffff",
                "overlay": "linear-gradient(160deg,rgba(0,0,0,0.75) 0%,rgba(10,10,10,0.92) 100%)"
            })
            progress.progress(25)

            render_stepper(2)
            for i, slide in enumerate(slides):
                num = slide.get("numero", 1)
                query = slide.get("query_imagem", tema)
                pct = 25 + int((i / len(slides)) * 65)
                status_box.markdown(f"""<div style='background:#eff6ff;border-radius:12px;padding:14px 18px;
                    color:#1d4ed8;font-size:14px;font-weight:500;'>
                    🖼️ &nbsp; Slide {num} de {len(slides)} — baixando imagem e renderizando...</div>""",
                    unsafe_allow_html=True)
                progress.progress(pct)

                img_path = pasta / f"img_{num:02d}.jpg"
                img_local = ""
                try:
                    img_local = baixar_imagem(query, img_path, px_key)
                except Exception:
                    pass

                html_content = gerar_html_slide(slide, len(slides), tema, paleta, img_local)
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

            render_stepper(3)
            progress.progress(100)
            status_box.markdown("""<div style='background:#f0fdf4;border-radius:12px;padding:14px 18px;
                color:#166534;font-size:14px;font-weight:600;'>
                ✅ &nbsp; Carrossel gerado com sucesso!</div>""", unsafe_allow_html=True)

        except Exception as e:
            progress.empty()
            stepper.empty()
            status_box.error(f"Erro: {str(e)}")
            return

        # ── RESULTADO ────────────────────────────────────────────
        hashtags = dados.get("hashtags", [])
        horario = dados.get("melhor_horario", "19:00")
        angulo = dados.get("angulo", "")
        serie = dados.get("titulo_serie", tema.strip())

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style='margin-bottom:8px;'>
            <div style='font-size:11px;font-weight:700;color:#94a3b8;letter-spacing:1px;text-transform:uppercase;margin-bottom:8px;'>Resultado</div>
            <div style='font-size:24px;font-weight:800;color:#0f172a;letter-spacing:-0.5px;'>{serie}</div>
        </div>""", unsafe_allow_html=True)

        # Métricas
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Slides", len(arquivos_png))
        c2.metric("Postar às", horario)
        c3.metric("Plataforma", plataforma)
        c4.metric("Formato", "1080px")

        # Ângulo + tendências
        if angulo:
            st.markdown(f"""<div style='background:#fff;border:1px solid #dbeafe;border-left:4px solid #2563eb;
                border-radius:12px;padding:16px 20px;margin:16px 0;color:#334155;font-size:14px;'>
                <strong style='color:#2563eb;font-size:11px;text-transform:uppercase;letter-spacing:1px;'>
                Ângulo estratégico</strong><br><span style='font-size:15px;font-weight:500;color:#0f172a;'>
                {angulo}</span></div>""", unsafe_allow_html=True)

        if tendencias:
            with st.expander("🔍  Ver análise de tendências completa"):
                st.markdown(f"<div style='color:#475569;font-size:14px;line-height:1.8;white-space:pre-wrap;'>{tendencias}</div>",
                           unsafe_allow_html=True)

        # Hashtags
        if hashtags:
            chips = "".join(
                f"<span style='display:inline-block;background:#eff6ff;color:#2563eb;border-radius:20px;"
                f"padding:5px 14px;font-size:13px;font-weight:500;margin:3px 3px 3px 0;border:1px solid #dbeafe;'>#{h}</span>"
                for h in hashtags
            )
            st.markdown(f"<div style='margin:16px 0;'>{chips}</div>", unsafe_allow_html=True)

        st.divider()

        # Grid de slides 3 colunas
        if arquivos_png:
            st.markdown("<div style='font-size:11px;font-weight:700;color:#94a3b8;letter-spacing:1px;text-transform:uppercase;margin-bottom:16px;'>Slides gerados</div>", unsafe_allow_html=True)
            cols = st.columns(3)
            for i, png in enumerate(arquivos_png):
                if png.exists():
                    with cols[i % 3]:
                        img_bytes = png.read_bytes()
                        st.markdown(f"""<div style='background:#fff;border:1px solid #e2e8f0;border-radius:14px;
                            overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.06);margin-bottom:4px;'>""",
                            unsafe_allow_html=True)
                        st.image(img_bytes, use_container_width=True)
                        st.markdown("</div>", unsafe_allow_html=True)
                        st.download_button(
                            f"⬇  Slide {i+1}",
                            data=img_bytes,
                            file_name=png.name,
                            mime="image/png",
                            key=f"dl_{i}"
                        )
                        st.markdown("<br>", unsafe_allow_html=True)

            # ZIP
            st.markdown("<br>", unsafe_allow_html=True)
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
