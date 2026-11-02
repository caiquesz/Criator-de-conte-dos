#!/usr/bin/env python3
"""
🎬 PÓS-PRODUÇÃO — legendas estilo Reels SEM alterar a montagem.

Regra absoluta: o vídeo de entrada é tratado como montagem finalizada.
Nada é cortado, acelerado, reordenado ou encurtado. O áudio é copiado
byte a byte (-c:a copy). Só a camada visual (legendas + ajuste sutil de
cor opcional) é adicionada por cima.

Uso básico:
    python pos_producao/legendar.py entrada.mp4
    python pos_producao/legendar.py entrada.mp4 --preset reels_destaque
    python pos_producao/legendar.py entrada.mp4 --texto roteiro.txt
    python pos_producao/legendar.py entrada.mp4 --legendas-json saida/entrada.legendas.json

Pipeline:
    1. Registra duração, frames, fps, resolução e hash do áudio original.
    2. Detecta trechos de fala (Silero VAD) e transcreve cada trecho (Whisper).
    3. Distribui o tempo das palavras dentro de cada trecho.
    4. Agrupa em "cards" curtos (2–4 palavras) e gera um .ass com o estilo do preset.
    5. Queima a legenda com ffmpeg (vídeo re-encodado, áudio copiado, frames preservados).
    6. Confere duração, nº de frames e hash do áudio e grava um relatório.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import shutil
import subprocess
import sys
import unicodedata
from dataclasses import dataclass, field, asdict
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
FONTS_DIR = AQUI / "fonts"
PRESETS_DIR = AQUI / "presets"
MODELOS_DIR = AQUI / "modelos"
SR = 16000


# ──────────────────────────────────────────────────────────────────
# ffprobe / registro do original
# ──────────────────────────────────────────────────────────────────
def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, check=True, **kw)


def probe(path: Path) -> dict:
    """Duração, frames (pacotes), fps, resolução (já considerando rotação) e codecs."""
    out = run([
        "ffprobe", "-v", "error", "-count_packets",
        "-show_entries",
        "stream=index,codec_type,codec_name,width,height,r_frame_rate,avg_frame_rate,"
        "nb_read_packets,duration,sample_rate,channels:stream_side_data=rotation:format=duration",
        "-of", "json", str(path),
    ]).stdout
    info = json.loads(out)
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    a = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)

    rot = 0
    for sd in v.get("side_data_list", []) or []:
        if "rotation" in sd:
            rot = int(float(sd["rotation"]))
    w, h = int(v["width"]), int(v["height"])
    if rot % 180 != 0:
        w, h = h, w

    def fps(s):
        n, d = s.split("/")
        return float(n) / float(d) if float(d) else 0.0

    return {
        "arquivo": str(path),
        "duracao_s": float(info["format"]["duration"]),
        "video": {
            "codec": v["codec_name"], "largura": w, "altura": h,
            "fps": round(fps(v.get("avg_frame_rate", v["r_frame_rate"])), 3),
            "frames": int(v.get("nb_read_packets", 0)),
            "duracao_s": float(v.get("duration", info["format"]["duration"])),
            "rotacao": rot,
        },
        "audio": None if a is None else {
            "codec": a["codec_name"], "sample_rate": int(a.get("sample_rate", 0)),
            "canais": int(a.get("channels", 0)),
            "duracao_s": float(a.get("duration", info["format"]["duration"])),
            "pacotes": int(a.get("nb_read_packets", 0)),
        },
    }


def hash_audio(path: Path) -> str | None:
    """MD5 dos pacotes do stream de áudio, sem decodificar — prova que a fala não mudou."""
    try:
        out = run(["ffmpeg", "-v", "error", "-i", str(path), "-map", "0:a:0", "-c", "copy",
                   "-f", "md5", "-"]).stdout.strip()
        return out.replace("MD5=", "")
    except subprocess.CalledProcessError:
        return None


def carregar_audio_16k(path: Path) -> np.ndarray:
    out = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-vn", "-ac", "1", "-ar", str(SR),
         "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(out, dtype=np.float32).copy()


# ──────────────────────────────────────────────────────────────────
# Transcrição: VAD + Whisper (sherpa-onnx, offline)
# ──────────────────────────────────────────────────────────────────
@dataclass
class Palavra:
    texto: str
    inicio: float
    fim: float
    destaque: bool = False


@dataclass
class Trecho:
    inicio: float
    fim: float
    texto: str
    palavras: list[Palavra] = field(default_factory=list)


def _modelo_whisper(nome: str) -> Path:
    d = MODELOS_DIR / f"sherpa-onnx-whisper-{nome}"
    if not d.exists():
        sys.exit(f"Modelo não encontrado: {d}\nRode: python pos_producao/baixar_modelos.py --modelo {nome}")
    return d


def detectar_fala(samples: np.ndarray, max_trecho_s: float = 7.0) -> list[tuple[float, float]]:
    import sherpa_onnx

    vad_path = MODELOS_DIR / "silero_vad.onnx"
    if not vad_path.exists():
        sys.exit(f"VAD não encontrado: {vad_path}\nRode: python pos_producao/baixar_modelos.py")
    cfg = sherpa_onnx.VadModelConfig()
    cfg.silero_vad.model = str(vad_path)
    cfg.silero_vad.threshold = 0.5
    cfg.silero_vad.min_silence_duration = 0.22
    cfg.silero_vad.min_speech_duration = 0.20
    cfg.silero_vad.max_speech_duration = max_trecho_s
    cfg.sample_rate = SR
    win = cfg.silero_vad.window_size
    vad = sherpa_onnx.VoiceActivityDetector(cfg, buffer_size_in_seconds=600)

    segs: list[tuple[float, float]] = []
    i = 0
    while i + win <= len(samples):
        vad.accept_waveform(samples[i:i + win])
        i += win
        while not vad.empty():
            s = vad.front
            segs.append((s.start / SR, (s.start + len(s.samples)) / SR))
            vad.pop()
    vad.flush()
    while not vad.empty():
        s = vad.front
        segs.append((s.start / SR, (s.start + len(s.samples)) / SR))
        vad.pop()
    return segs


def transcrever(samples: np.ndarray, modelo: str, idioma: str, verbose=True) -> list[Trecho]:
    import sherpa_onnx

    M = _modelo_whisper(modelo)
    rec = sherpa_onnx.OfflineRecognizer.from_whisper(
        encoder=str(M / f"{modelo}-encoder.int8.onnx"),
        decoder=str(M / f"{modelo}-decoder.int8.onnx"),
        tokens=str(M / f"{modelo}-tokens.txt"),
        language=idioma, task="transcribe", num_threads=4,
    )
    segs = detectar_fala(samples)
    trechos: list[Trecho] = []
    for (ini, fim) in segs:
        # margem pequena para não cortar consoantes iniciais/finais
        a = max(0, int((ini - 0.10) * SR))
        b = min(len(samples), int((fim + 0.10) * SR))
        st = rec.create_stream()
        st.accept_waveform(SR, samples[a:b])
        rec.decode_stream(st)
        txt = _limpar_alucinacao(st.result.text.strip())
        if not txt:
            continue
        t = Trecho(ini, fim, txt)
        t.palavras = _distribuir_palavras(txt, ini, fim)
        trechos.append(t)
        if verbose:
            print(f"  [{ini:6.2f}s → {fim:6.2f}s] {txt}")
    return trechos


def _limpar_alucinacao(txt: str) -> str:
    """Whisper às vezes repete a mesma palavra em loop em trechos ruidosos."""
    pal = txt.split()
    out: list[str] = []
    for p in pal:
        if len(out) >= 3 and out[-1] == out[-2] == out[-3] == p:
            continue
        out.append(p)
    return " ".join(out)


def _peso(p: str) -> float:
    base = re.sub(r"[^\w]", "", p)
    vog = len(re.findall(r"[aeiouáéíóúâêôãõàü]", base.lower()))
    w = max(1.0, vog * 0.9 + len(base) * 0.25)
    if re.search(r"[.!?…]$", p):
        w += 2.2  # pausa de fim de frase
    elif re.search(r"[,;:]$", p):
        w += 1.0
    return w


def _distribuir_palavras(txt: str, ini: float, fim: float) -> list[Palavra]:
    pal = txt.split()
    pesos = [_peso(p) for p in pal]
    total = sum(pesos)
    t = ini
    out: list[Palavra] = []
    for p, w in zip(pal, pesos):
        d = (fim - ini) * w / total
        out.append(Palavra(p, round(t, 3), round(t + d, 3)))
        t += d
    return out


# ──────────────────────────────────────────────────────────────────
# Texto corrigido pelo editor (alinha o roteiro ao tempo do ASR)
# ──────────────────────────────────────────────────────────────────
def _norm(p: str) -> str:
    p = unicodedata.normalize("NFD", p.lower())
    p = "".join(c for c in p if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]", "", p)


def alinhar_texto(trechos: list[Trecho], texto: str) -> list[Trecho]:
    """Substitui as palavras do ASR pelas do roteiro, herdando os tempos.

    Palavras que casam ancoram o tempo; as demais são interpoladas entre âncoras.
    """
    asr = [p for t in trechos for p in t.palavras]
    ref = texto.split()
    if not asr or not ref:
        return trechos
    sm = difflib.SequenceMatcher(a=[_norm(p.texto) for p in asr], b=[_norm(p) for p in ref], autojunk=False)
    anc: dict[int, Palavra] = {}
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                anc[j1 + k] = asr[i1 + k]
    # interpola os não ancorados
    novas: list[Palavra] = [None] * len(ref)  # type: ignore
    for j, p in anc.items():
        novas[j] = Palavra(ref[j], p.inicio, p.fim)
    j = 0
    while j < len(ref):
        if novas[j] is not None:
            j += 1
            continue
        k = j
        while k < len(ref) and novas[k] is None:
            k += 1
        t0 = novas[j - 1].fim if j > 0 else asr[0].inicio
        t1 = novas[k].inicio if k < len(ref) else asr[-1].fim
        if t1 <= t0:  # sem espaço: rouba um pouco dos vizinhos
            t1 = t0 + 0.12 * (k - j)
        pesos = [_peso(ref[x]) for x in range(j, k)]
        tot = sum(pesos)
        t = t0
        for x, w in zip(range(j, k), pesos):
            d = (t1 - t0) * w / tot
            novas[x] = Palavra(ref[x], round(t, 3), round(t + d, 3))
            t += d
        j = k
    # reagrupa em trechos pelos limites de frase do roteiro / pausas
    out: list[Trecho] = []
    atual: list[Palavra] = []
    for p in novas:
        if atual and (p.inicio - atual[-1].fim > 0.6):
            out.append(Trecho(atual[0].inicio, atual[-1].fim, " ".join(x.texto for x in atual), atual))
            atual = []
        atual.append(p)
    if atual:
        out.append(Trecho(atual[0].inicio, atual[-1].fim, " ".join(x.texto for x in atual), atual))
    return out


# ──────────────────────────────────────────────────────────────────
# Cards (grupos de 2–4 palavras)
# ──────────────────────────────────────────────────────────────────
@dataclass
class Card:
    inicio: float
    fim: float
    palavras: list[Palavra]

    @property
    def texto(self) -> str:
        return " ".join(p.texto for p in self.palavras)


PALAVRAS_FUNCAO = {"o", "a", "os", "as", "um", "uma", "de", "do", "da", "dos", "das", "e", "é", "em", "no", "na",
                   "nos", "nas", "que", "se", "por", "com", "ao", "à", "pra", "pro", "para", "ou", "mas", "nem",
                   "meu", "minha", "seu", "sua", "esse", "essa", "este", "esta", "isso", "num", "numa"}


def _dividir_balanceado(pal: list[Palavra], max_pal: int, max_chars: int) -> list[list[Palavra]]:
    """Divide uma frase em cards de tamanho parecido (evita card órfão de 1 palavra no fim)."""
    n = len(pal)
    if n <= max_pal and len(" ".join(p.texto for p in pal)) <= max_chars:
        return [pal]
    k = max(1, -(-n // max_pal))
    ideal = n / k
    INF = float("inf")
    melhor = [INF] * (n + 1); prev = [-1] * (n + 1); melhor[0] = 0.0
    for fim in range(1, n + 1):
        for tam in range(1, max_pal + 1):
            ini = fim - tam
            if ini < 0 or melhor[ini] == INF:
                continue
            grupo = pal[ini:fim]
            custo = (tam - ideal) ** 2
            if tam == 1 and n > 1:
                custo += 2.5
            if fim < n and _norm(grupo[-1].texto) in PALAVRAS_FUNCAO and not re.search(r"[,;:]$", grupo[-1].texto):
                custo += 3.0
            if ini > 0 and re.search(r"[,;:]$", pal[ini - 1].texto):
                custo -= 0.8  # quebrar depois de vírgula é bom
            if any(re.search(r"[,;:]$", g.texto) for g in grupo[:-1]):
                custo += 1.5  # vírgula no meio do card lê mal
            if len(" ".join(p.texto for p in grupo)) > max_chars:
                custo += 10.0
            if melhor[ini] + custo < melhor[fim]:
                melhor[fim] = melhor[ini] + custo; prev[fim] = ini
    grupos: list[list[Palavra]] = []
    f = n
    while f > 0:
        grupos.append(pal[prev[f]:f]); f = prev[f]
    return grupos[::-1]


def montar_cards(trechos: list[Trecho], max_pal: int, max_chars: int, pausa_corte: float = 0.45) -> list[Card]:
    cards: list[Card] = []
    for t in trechos:
        # 1) frases: fim de sentença ou pausa longa
        frase: list[Palavra] = []
        frases: list[list[Palavra]] = []
        for p in t.palavras:
            if frase and (p.inicio - frase[-1].fim > pausa_corte or re.search(r"[.!?…]$", frase[-1].texto)):
                frases.append(frase); frase = []
            frase.append(p)
        if frase:
            frases.append(frase)
        # 2) cada frase vira 1+ cards balanceados
        for fr in frases:
            for g in _dividir_balanceado(fr, max_pal, max_chars):
                cards.append(Card(g[0].inicio, g[-1].fim, g))
    # segura o card até o próximo começar (sem piscar), com teto
    for i, c in enumerate(cards):
        prox = cards[i + 1].inicio if i + 1 < len(cards) else c.fim + 0.3
        c.fim = min(prox, c.fim + 0.35) if prox - c.fim < 1.2 else c.fim + 0.35
    return cards


# ──────────────────────────────────────────────────────────────────
# ASS
# ──────────────────────────────────────────────────────────────────
def _ass_cor(hex_: str, alpha: int = 0) -> str:
    h = hex_.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"&H{alpha:02X}{b:02X}{g:02X}{r:02X}"


def _ts(t: float) -> str:
    t = max(0.0, t)
    h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def _quebrar_linhas(palavras: list[str], max_chars: int, max_linhas: int) -> list[list[int]]:
    """Índices das palavras por linha, equilibrando o comprimento."""
    if max_linhas <= 1 or len(" ".join(palavras)) <= max_chars:
        return [list(range(len(palavras)))]
    n = len(palavras)
    melhor, melhor_custo = None, 1e9
    for corte in range(1, n):
        l1 = " ".join(palavras[:corte]); l2 = " ".join(palavras[corte:])
        custo = abs(len(l1) - len(l2)) + (50 if len(l2) > max_chars or len(l1) > max_chars else 0)
        if custo < melhor_custo:
            melhor, melhor_custo = corte, custo
    return [list(range(melhor)), list(range(melhor, n))]


def gerar_ass(cards: list[Card], preset: dict, largura: int, altura: int,
              palavras_chave: set[str]) -> str:
    esc = altura / 1920.0  # preset é pensado para 1080x1920
    tam = int(preset["tamanho"] * esc)
    contorno = round(preset.get("contorno", 4) * esc, 2)
    sombra = round(preset.get("sombra", 2) * esc, 2)
    cor_txt = _ass_cor(preset["cor_texto"])
    cor_dst = _ass_cor(preset["cor_destaque"])
    cor_ctn = _ass_cor(preset.get("cor_contorno", "#000000"))
    cor_smb = _ass_cor(preset.get("cor_sombra", "#000000"), alpha=int(255 * (1 - preset.get("opacidade_sombra", 0.7))))
    fundo = preset.get("fundo")
    border_style = 1
    if fundo:
        border_style = 4  # caixa só atrás do texto, por linha
        cor_ctn = _ass_cor(fundo["cor"], alpha=int(255 * (1 - fundo.get("opacidade", 0.65))))
        contorno = round(fundo.get("padding", 18) * esc, 2)
        sombra = 0
    y = int(altura * preset.get("posicao_y", 0.72))
    x = largura // 2
    espaco = preset.get("espacamento", 0)
    anim = preset.get("animacao", {"tipo": "pop", "duracao_ms": 110, "escala_inicial": 80})
    modo = preset.get("modo", "destaque")
    maius = preset.get("maiusculas", True)
    max_chars = preset.get("max_chars_linha", 18)
    max_linhas = preset.get("max_linhas", 2)
    cor_dst_fundo = preset.get("fundo_destaque")  # ex: caixinha colorida na palavra atual

    linhas = [
        "[Script Info]",
        "ScriptType: v4.00+",
        f"PlayResX: {largura}",
        f"PlayResY: {altura}",
        "WrapStyle: 2",
        "ScaledBorderAndShadow: yes",
        "YCbCr Matrix: TV.709",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
        "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
        "Alignment, MarginL, MarginR, MarginV, Encoding",
        f"Style: Legenda,{preset['fonte']},{tam},{cor_txt},{cor_dst},{cor_ctn},{cor_smb},"
        f"{-1 if preset.get('negrito', True) else 0},0,0,0,100,100,{espaco},0,{border_style},{contorno},{sombra},"
        f"5,{int(preset.get('margem_lateral', 80) * esc)},{int(preset.get('margem_lateral', 80) * esc)},0,1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]

    def fmt(p: Palavra) -> str:
        t = p.texto.upper() if maius else p.texto
        if preset.get("remover_pontuacao", True):
            t = re.sub(r"[.,;:!?…]+$", "", t)
        return t.replace("{", "(").replace("}", ")")

    def pop_inline() -> str:
        e0 = anim.get("escala_inicial", 80); d = anim.get("duracao_ms", 110)
        return f"\\fscx{e0}\\fscy{e0}\\t(0,{d},\\fscx100\\fscy100)"

    def render(card: Card, atual: int | None, acumulado: bool, anima_atual: bool = False) -> str:
        pal = card.palavras if not acumulado else card.palavras[: (atual or 0) + 1]
        textos = [fmt(p) for p in pal]
        grupos = _quebrar_linhas([fmt(p) for p in card.palavras], max_chars, max_linhas)
        partes = []
        for g in grupos:
            seg = []
            for i in g:
                if i >= len(textos):
                    continue
                p = card.palavras[i]
                chave = _norm(p.texto) in palavras_chave or p.destaque
                e_atual = atual is not None and i == atual and modo in ("destaque", "palavra")
                extra = pop_inline() if (anima_atual and e_atual) else ""
                if chave or e_atual:
                    tag = f"{{\\c{cor_dst}&{extra}}}"
                    if cor_dst_fundo and e_atual:
                        tag = f"{{\\c{_ass_cor(cor_dst_fundo['cor_texto'])}&\\3c{_ass_cor(cor_dst_fundo['cor'])}&\\bord{int(cor_dst_fundo.get('padding', 14) * esc)}\\shad0{extra}}}"
                    seg.append(f"{tag}{textos[i]}{{\\r}}")
                elif extra:
                    seg.append(f"{{{extra}}}{textos[i]}{{\\r}}")
                else:
                    seg.append(textos[i])
            if seg:
                partes.append(" ".join(seg))
        return "\\N".join(partes)

    def pop_tag(card: Card) -> str:
        if anim.get("tipo") == "pop":
            e0 = anim.get("escala_inicial", 80); d = anim.get("duracao_ms", 110)
            return f"{{\\fscx{e0}\\fscy{e0}\\t(0,{d},\\fscx100\\fscy100)}}"
        if anim.get("tipo") == "fade":
            return f"{{\\fad({anim.get('duracao_ms', 120)},0)}}"
        if anim.get("tipo") == "sobe":
            d = anim.get("duracao_ms", 140); dy = int(anim.get("deslocamento", 40) * esc)
            return f"{{\\move({x},{y + dy},{x},{y},0,{d})\\fad({d},0)}}"
        return ""

    for c in cards:
        pos = f"{{\\an5\\pos({x},{y})}}"
        if modo == "card":
            linhas.append(f"Dialogue: 0,{_ts(c.inicio)},{_ts(c.fim)},Legenda,,0,0,0,,{pos}{pop_tag(c)}{render(c, None, False)}")
            continue
        n = len(c.palavras)
        for i, p in enumerate(c.palavras):
            ini = c.inicio if i == 0 else p.inicio
            fim = c.fim if i == n - 1 else c.palavras[i + 1].inicio
            if fim - ini < 0.04:
                continue
            tag = pop_tag(c) if i == 0 else ""
            por_palavra = anim.get("por_palavra", modo == "palavra") and anim.get("tipo") == "pop" and i > 0
            linhas.append(f"Dialogue: 0,{_ts(ini)},{_ts(fim)},Legenda,,0,0,0,,{pos}{tag}{render(c, i, modo == 'palavra', por_palavra)}")
    return "\n".join(linhas) + "\n"


# ──────────────────────────────────────────────────────────────────
# Render final
# ──────────────────────────────────────────────────────────────────
def queimar(entrada: Path, ass: Path, saida: Path, cor_sutil: bool, crf: int, largura: int, altura: int):
    filtros = []
    if cor_sutil:
        filtros.append("eq=contrast=1.04:saturation=1.06")
        filtros.append("unsharp=5:5:0.35:5:5:0.0")
    ass_esc = str(ass).replace("\\", "/").replace(":", "\\:").replace("'", "\\'")
    fd = str(FONTS_DIR).replace("\\", "/").replace(":", "\\:")
    filtros.append(f"ass='{ass_esc}':fontsdir='{fd}'")
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-stats",
        "-i", str(entrada),
        "-map", "0:v:0", "-map", "0:a:0?",
        "-vf", ",".join(filtros),
        "-fps_mode", "passthrough",          # mantém cada frame e seus timestamps
        "-c:v", "libx264", "-preset", "medium", "-crf", str(crf),
        "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "4.1",
        "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
        "-c:a", "copy",                      # fala original intocada
        "-movflags", "+faststart",
        str(saida),
    ]
    subprocess.run(cmd, check=True)


def verificar(orig: dict, novo: dict, hash_o: str | None, hash_n: str | None) -> tuple[bool, list[str]]:
    msgs = []
    ok = True
    fps = orig["video"]["fps"] or 30
    tol = 1.0 / fps + 0.02
    dd = abs(orig["duracao_s"] - novo["duracao_s"])
    msgs.append(f"duração: {orig['duracao_s']:.3f}s → {novo['duracao_s']:.3f}s (Δ {dd*1000:.0f} ms)")
    if dd > tol:
        ok = False; msgs[-1] += "  ❌"
    fo, fn = orig["video"]["frames"], novo["video"]["frames"]
    msgs.append(f"frames de vídeo: {fo} → {fn}")
    if fo != fn:
        ok = False; msgs[-1] += "  ❌"
    msgs.append(f"resolução: {orig['video']['largura']}x{orig['video']['altura']} → {novo['video']['largura']}x{novo['video']['altura']}")
    if (orig['video']['largura'], orig['video']['altura']) != (novo['video']['largura'], novo['video']['altura']):
        ok = False; msgs[-1] += "  ❌"
    if orig["audio"]:
        msgs.append(f"áudio: {orig['audio']['codec']} {orig['audio']['pacotes']} pacotes → {novo['audio']['codec'] if novo['audio'] else '—'} {novo['audio']['pacotes'] if novo['audio'] else 0} pacotes")
        if not novo["audio"] or orig["audio"]["pacotes"] != novo["audio"]["pacotes"]:
            ok = False; msgs[-1] += "  ❌"
        msgs.append(f"hash do áudio: {'idêntico ✅' if hash_o and hash_o == hash_n else 'DIFERENTE ❌'} ({hash_o})")
        if not (hash_o and hash_o == hash_n):
            ok = False
    return ok, msgs


# ──────────────────────────────────────────────────────────────────
def carregar_preset(nome: str) -> dict:
    p = Path(nome)
    if not p.exists():
        p = PRESETS_DIR / f"{nome}.json"
    if not p.exists():
        sys.exit(f"Preset não encontrado: {nome}. Disponíveis: {[x.stem for x in PRESETS_DIR.glob('*.json')]}")
    return json.loads(p.read_text(encoding="utf-8"))


def cards_para_json(cards: list[Card]) -> list[dict]:
    return [{"inicio": c.inicio, "fim": c.fim,
             "palavras": [asdict(p) for p in c.palavras]} for c in cards]


def cards_de_json(data: list[dict]) -> list[Card]:
    return [Card(c["inicio"], c["fim"], [Palavra(**p) for p in c["palavras"]]) for c in data]


def main():
    ap = argparse.ArgumentParser(description="Legendas estilo Reels sem alterar a montagem.")
    ap.add_argument("entrada", type=Path)
    ap.add_argument("--saida", type=Path, help="padrão: pos_producao/saida/<nome>_legendado.mp4")
    ap.add_argument("--preset", default="reels_destaque")
    ap.add_argument("--modelo", default="small", help="whisper: tiny/base/small/medium")
    ap.add_argument("--idioma", default="pt")
    ap.add_argument("--texto", type=Path, help="roteiro/transcrição correta (txt) para substituir o texto do ASR")
    ap.add_argument("--legendas-json", type=Path, help="reaproveita cards já revisados (pula transcrição)")
    ap.add_argument("--destaque", default="", help="palavras-chave sempre coloridas, separadas por vírgula")
    ap.add_argument("--max-palavras", type=int)
    ap.add_argument("--max-chars", type=int)
    ap.add_argument("--cor-sutil", action="store_true", help="contraste/saturação/nitidez leves")
    ap.add_argument("--crf", type=int, default=17)
    ap.add_argument("--so-ass", action="store_true", help="gera só o .ass/.json, não renderiza")
    args = ap.parse_args()

    entrada: Path = args.entrada
    if not entrada.exists():
        sys.exit(f"Arquivo não encontrado: {entrada}")
    saida_dir = (args.saida.parent if args.saida else AQUI / "saida")
    saida_dir.mkdir(parents=True, exist_ok=True)
    saida: Path = args.saida or saida_dir / f"{entrada.stem}_legendado.mp4"
    base = saida_dir / saida.stem  # arquivos auxiliares acompanham o nome da saída

    preset = carregar_preset(args.preset)
    if args.max_palavras: preset["max_palavras"] = args.max_palavras
    if args.max_chars: preset["max_chars_linha"] = args.max_chars
    chaves = {_norm(x) for x in (args.destaque.split(",") if args.destaque else []) if x.strip()}
    chaves |= {_norm(x) for x in preset.get("palavras_chave", [])}

    print("1) Registrando o original…")
    orig = probe(entrada)
    hash_o = hash_audio(entrada)
    W, H = orig["video"]["largura"], orig["video"]["altura"]
    print(f"   {W}x{H} @ {orig['video']['fps']} fps · {orig['duracao_s']:.3f}s · {orig['video']['frames']} frames · áudio {orig['audio']['codec'] if orig['audio'] else '—'}")
    (base.with_suffix(".original.json")).write_text(json.dumps({**orig, "hash_audio": hash_o}, indent=2, ensure_ascii=False), encoding="utf-8")

    if args.legendas_json:
        print("2) Usando legendas revisadas:", args.legendas_json)
        cards = cards_de_json(json.loads(args.legendas_json.read_text(encoding="utf-8"))["cards"])
    else:
        print(f"2) Transcrevendo (whisper-{args.modelo}, VAD)…")
        samples = carregar_audio_16k(entrada)
        trechos = transcrever(samples, args.modelo, args.idioma)
        if args.texto:
            print("   Alinhando ao texto fornecido…")
            trechos = alinhar_texto(trechos, args.texto.read_text(encoding="utf-8"))
        print("3) Montando cards…")
        cards = montar_cards(trechos, preset.get("max_palavras", 3), preset.get("max_chars_linha", 18) * preset.get("max_linhas", 2))
    leg_json = base.with_suffix(".legendas.json")
    leg_json.write_text(json.dumps({"preset": args.preset, "cards": cards_para_json(cards)}, indent=2, ensure_ascii=False), encoding="utf-8")
    txt = base.with_suffix(".transcricao.txt")
    txt.write_text("\n".join(f"{_ts(c.inicio)} → {_ts(c.fim)}  {c.texto}" for c in cards), encoding="utf-8")
    print(f"   {len(cards)} cards · texto em {txt.name} · timings em {leg_json.name}")

    print("4) Gerando .ass…")
    ass = base.with_suffix(".ass")
    ass.write_text(gerar_ass(cards, preset, W, H, chaves), encoding="utf-8")
    if args.so_ass:
        print("   (--so-ass) pronto:", ass); return

    print("5) Queimando legenda (vídeo re-encodado, áudio copiado)…")
    queimar(entrada, ass, saida, args.cor_sutil, args.crf, W, H)

    print("6) Conferindo…")
    novo = probe(saida)
    ok, msgs = verificar(orig, novo, hash_o, hash_audio(saida))
    rel = ["# Relatório de pós-produção", f"- entrada: `{entrada}`", f"- saída: `{saida}`", f"- preset: `{args.preset}`", ""]
    rel += [f"- {m}" for m in msgs]
    rel.append("")
    rel.append("✅ MONTAGEM PRESERVADA" if ok else "❌ ALGO MUDOU — NÃO PUBLICAR")
    base.with_suffix(".relatorio.md").write_text("\n".join(rel), encoding="utf-8")
    for m in msgs: print("   " + m)
    print("   " + rel[-1])
    print("→", saida)
    sys.exit(0 if ok else 2)


if __name__ == "__main__":
    main()
