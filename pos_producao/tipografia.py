#!/usr/bin/env python3
"""
🎬 TIPOGRAFIA CINÉTICA — texto gigante ATRÁS da pessoa, estilo das referências.

O que reproduz:
  • palavras em tamanhos misturados (pequeno / médio / gigante) compostas por frase;
  • o texto fica ATRÁS do sujeito (segmentação da pessoa frame a frame, u2net_human_seg);
  • palavra-chave com preenchimento de textura (cena invertida, como o "faz") ou foto
    (como o "P" da praia) ou em cor de destaque (como o "rotina" laranja);
  • entrada por palavra sincronizada com a fala (pop/escala + fade curtos);
  • montagem intocada: mesmo nº de frames, áudio copiado byte a byte, conferência no fim.

Uso:
    python pos_producao/tipografia.py video.mp4 [--texto roteiro.txt] [--destaque "casa,rotina"]
    python pos_producao/tipografia.py video.mp4 --cenas pos_producao/saida/video_tipografia.cenas.json
    python pos_producao/tipografia.py video.mp4 --so-cenas    # só gera o .cenas.json para revisar o layout

O arquivo *.cenas.json é o "projeto": cada cena tem blocos de texto com fonte, tamanho,
cor/textura, posição, camada (atras|frente) e tempo de entrada. Edite e re-renderize.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
import legendar as L  # noqa: E402  (reaproveita probe, transcrição, cards, verificação)

AQUI = Path(__file__).resolve().parent
FONTS = AQUI / "fonts"
MODELOS = AQUI / "modelos"
PRESETS = AQUI / "presets"

PALAVRAS_FUNCAO = L.PALAVRAS_FUNCAO | {"você", "voce", "vai", "tem", "ter", "ser", "está", "esta", "são", "foi",
                                        "mais", "muito", "bem", "já", "ja", "aí", "ai", "não", "nao", "sim",
                                        "ele", "ela", "eles", "elas", "nós", "nos", "eu", "tu", "lá", "la", "aqui"}


# ──────────────────────────────────────────────────────────────────
# Segmentação da pessoa (u2net_human_seg via onnxruntime)
# ──────────────────────────────────────────────────────────────────
class Segmentador:
    def __init__(self, modelo: str = "u2net_human_seg"):
        import onnxruntime as ort
        p = MODELOS / f"{modelo}.onnx"
        if not p.exists():
            sys.exit(f"Modelo de segmentação não encontrado: {p}\nRode: python pos_producao/baixar_modelos.py --segmentacao")
        so = ort.SessionOptions(); so.intra_op_num_threads = 4
        self.s = ort.InferenceSession(str(p), so, providers=["CPUExecutionProvider"])
        self.inp = self.s.get_inputs()[0].name
        self.tam = 320 if "u2net" in modelo else 1024
        self.anterior: np.ndarray | None = None

    def mascara(self, frame_rgb: np.ndarray, suavizar: float = 0.35, t: float | None = None) -> np.ndarray:
        """Retorna máscara float32 [0..1] (1 = pessoa) no tamanho do frame.

        Em vídeos a 60 fps reaproveita a máscara anterior se passaram < 25 ms (metade do custo).
        """
        if t is not None and getattr(self, "_t_ultimo", None) is not None and getattr(self, "_ultima", None) is not None \
                and 0 <= (t - self._t_ultimo) < 0.025:
            return self._ultima
        h, w = frame_rgb.shape[:2]
        x = cv2.resize(frame_rgb, (self.tam, self.tam), interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0
        x = (x - np.array([0.485, 0.456, 0.406], np.float32)) / np.array([0.229, 0.224, 0.225], np.float32)
        x = x.transpose(2, 0, 1)[None]
        y = self.s.run(None, {self.inp: x})[0][0, 0]
        y = (y - y.min()) / max(1e-6, (y.max() - y.min()))
        m = cv2.resize(y, (w, h), interpolation=cv2.INTER_LINEAR)
        # contraste na borda + leve suavização temporal (evita tremer)
        m = np.clip((m - 0.35) / 0.3, 0, 1)
        if self.anterior is not None and suavizar > 0:
            m = (1 - suavizar) * m + suavizar * self.anterior
        self.anterior = m
        self._ultima = cv2.GaussianBlur(m, (0, 0), 2.0)
        self._t_ultimo = t
        return self._ultima


# ──────────────────────────────────────────────────────────────────
# Modelo de cena
# ──────────────────────────────────────────────────────────────────
@dataclass
class Bloco:
    texto: str
    fonte: str            # arquivo em pos_producao/fonts (ex.: Quicksand-700.ttf)
    tamanho: int          # px para altura 1920 (escala automática)
    inicio: float         # s (entrada)
    fim: float            # s (saída)
    pos: tuple[float, float]       # fração (x, y) do centro/âncora
    ancora: str = "centro"         # centro | esquerda | direita
    cor: str = "#FFFFFF"
    textura: str | None = None     # "inverter" | caminho de imagem | None
    camada: str = "atras"          # atras | frente
    anim: str = "pop"              # pop | fade | sobe | nenhuma
    tracking: float = 0.0          # em (negativo aperta)
    opacidade: float = 1.0
    maiusculas: bool = False


def _fonte(nome: str, tam: int) -> ImageFont.FreeTypeFont:
    p = FONTS / nome
    if not p.exists():
        p = FONTS / f"{nome}.ttf"
    return ImageFont.truetype(str(p), tam)


def _largura_texto(fonte: ImageFont.FreeTypeFont, txt: str, tracking_px: float) -> float:
    if not txt:
        return 0.0
    return sum(fonte.getlength(c) for c in txt) + tracking_px * (len(txt) - 1)


def desenhar_texto(txt: str, fonte: ImageFont.FreeTypeFont, tracking_px: float) -> np.ndarray:
    """Máscara alfa (uint8) do texto com tracking manual. Retorna array HxW."""
    asc, desc = fonte.getmetrics()
    w = int(math.ceil(_largura_texto(fonte, txt, tracking_px))) + 8
    h = asc + desc + 8
    img = Image.new("L", (max(1, w), h), 0)
    d = ImageDraw.Draw(img)
    x = 4.0
    for c in txt:
        d.text((x, 4), c, font=fonte, fill=255)
        x += fonte.getlength(c) + tracking_px
    return np.array(img)


# ──────────────────────────────────────────────────────────────────
# Composição por frame
# ──────────────────────────────────────────────────────────────────
def _ease_out(t: float) -> float:
    return 1 - (1 - t) ** 3


class Renderizador:
    def __init__(self, W: int, H: int, fps: float, cenas: list[dict], texturas_dir: Path):
        self.W, self.H, self.fps = W, H, fps
        self.esc = H / 1920.0
        self.cenas = cenas
        self.cache_fontes: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}
        self.cache_texto: dict[tuple, np.ndarray] = {}
        self.cache_img: dict[str, np.ndarray] = {}
        self.texturas_dir = texturas_dir

    def fonte(self, nome: str, tam: int):
        k = (nome, tam)
        if k not in self.cache_fontes:
            self.cache_fontes[k] = _fonte(nome, tam)
        return self.cache_fontes[k]

    def alfa_texto(self, b: Bloco) -> np.ndarray:
        tam = max(8, int(b.tamanho * self.esc))
        txt = b.texto.upper() if b.maiusculas else b.texto
        k = (txt, b.fonte, tam, round(b.tracking, 3))
        if k not in self.cache_texto:
            f = self.fonte(b.fonte, tam)
            self.cache_texto[k] = desenhar_texto(txt, f, b.tracking * tam)
        return self.cache_texto[k]

    def textura(self, b: Bloco, frame: np.ndarray, x0: int, y0: int, w: int, h: int) -> np.ndarray:
        if b.textura == "inverter":
            reg = frame[y0:y0 + h, x0:x0 + w].astype(np.float32)
            inv = 255.0 - reg
            # leve clareada, como no "faz" da referência
            return np.clip(inv * 0.85 + 255 * 0.15, 0, 255).astype(np.uint8)
        if b.textura:
            if b.textura not in self.cache_img:
                p = Path(b.textura)
                if not p.exists():
                    p = self.texturas_dir / b.textura
                im = cv2.cvtColor(cv2.imread(str(p)), cv2.COLOR_BGR2RGB)
                self.cache_img[b.textura] = im
            im = self.cache_img[b.textura]
            # cover: escala para cobrir o retângulo do texto e corta no centro
            s = max(w / im.shape[1], h / im.shape[0])
            im2 = cv2.resize(im, (max(w, int(im.shape[1] * s)), max(h, int(im.shape[0] * s))))
            cy, cx = (im2.shape[0] - h) // 2, (im2.shape[1] - w) // 2
            return im2[cy:cy + h, cx:cx + w]
        c = b.cor.lstrip("#")
        cor = np.array([int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)], np.uint8)
        return np.broadcast_to(cor, (h, w, 3)).copy()

    def aplicar_bloco(self, base: np.ndarray, frame: np.ndarray, b: Bloco, t: float):
        if t < b.inicio or t > b.fim:
            return
        alfa = self.alfa_texto(b)
        th, tw = alfa.shape
        # animação de entrada
        d_in = 0.16
        k = min(1.0, (t - b.inicio) / d_in)
        e = _ease_out(k)
        escala, op, dy = 1.0, 1.0, 0
        if b.anim == "pop":
            escala = 0.90 + 0.10 * e; op = e
        elif b.anim == "fade":
            op = e
        elif b.anim == "sobe":
            op = e; dy = int((1 - e) * 40 * self.esc)
        # saída: fade curto
        d_out = 0.10
        if b.fim - t < d_out:
            op *= max(0.0, (b.fim - t) / d_out)
        op *= b.opacidade
        if op <= 0.005:
            return
        if abs(escala - 1.0) > 1e-3:
            alfa = cv2.resize(alfa, (max(1, int(tw * escala)), max(1, int(th * escala))), interpolation=cv2.INTER_AREA)
            th, tw = alfa.shape
        cx, cy = int(b.pos[0] * self.W), int(b.pos[1] * self.H) + dy
        if b.ancora == "esquerda":
            x0 = cx
        elif b.ancora == "direita":
            x0 = cx - tw
        else:
            x0 = cx - tw // 2
        y0 = cy - th // 2
        # recorte no frame
        xa, ya = max(0, x0), max(0, y0)
        xb, yb = min(self.W, x0 + tw), min(self.H, y0 + th)
        if xb <= xa or yb <= ya:
            return
        a = alfa[ya - y0:yb - y0, xa - x0:xb - x0].astype(np.float32) / 255.0 * op
        tex = self.textura(b, frame, xa, ya, xb - xa, yb - ya).astype(np.float32)
        reg = base[ya:yb, xa:xb].astype(np.float32)
        base[ya:yb, xa:xb] = (reg * (1 - a[..., None]) + tex * a[..., None]).astype(np.uint8)

    def blocos_em(self, t: float) -> list[Bloco]:
        out = []
        for c in self.cenas:
            if c["inicio"] - 0.05 <= t <= c["fim"] + 0.05:
                for b in c["blocos"]:
                    bb = Bloco(**{**b, "pos": tuple(b["pos"])})
                    if bb.inicio <= t <= bb.fim:
                        out.append(bb)
        return out

    def frame(self, frame: np.ndarray, t: float, seg: Segmentador | None) -> np.ndarray:
        blocos = self.blocos_em(t)
        if not blocos:
            return frame
        base = frame.copy()
        atras = [b for b in blocos if b.camada == "atras"]
        frente = [b for b in blocos if b.camada == "frente"]
        for b in atras:
            self.aplicar_bloco(base, frame, b, t)
        if atras and seg is not None:
            m = seg.mascara(frame, t=t)[..., None]
            base = (base.astype(np.float32) * (1 - m) + frame.astype(np.float32) * m).astype(np.uint8)
        for b in frente:
            self.aplicar_bloco(base, frame, b, t)
        return base


# ──────────────────────────────────────────────────────────────────
# Layout automático a partir dos cards (frases de 2–4 palavras)
# ──────────────────────────────────────────────────────────────────
def _escolher_chave(palavras: list[L.Palavra], chaves: set[str]) -> int:
    for i, p in enumerate(palavras):
        if L._norm(p.texto) in chaves:
            return i
    cand = [(len(L._norm(p.texto)), i) for i, p in enumerate(palavras) if L._norm(p.texto) not in PALAVRAS_FUNCAO]
    if not cand:
        cand = [(len(p.texto), i) for i, p in enumerate(palavras)]
    return max(cand)[1]


def _ajustar_tamanho(fonte: str, txt: str, tam: int, max_w: int, tracking: float, esc: float, maius=False) -> int:
    """Reduz o tamanho até o texto caber em max_w (px reais)."""
    txt = txt.upper() if maius else txt
    while tam > 40:
        f = _fonte(fonte, int(tam * esc))
        if _largura_texto(f, txt, tracking * tam * esc) <= max_w:
            return tam
        tam = int(tam * 0.92)
    return tam


def _limpo(txt: str) -> str:
    """Sem vírgulas/pontos finais, como nas referências (mantém ? e !)."""
    return re.sub(r"[.,;:…]+$", "", txt.replace(",", ""))


def layout_automatico(cards: list[L.Card], preset: dict, W: int, H: int, chaves: set[str],
                      textura_img: str | None) -> list[dict]:
    esc = H / 1920.0
    cenas = []
    modelos = preset["modelos"]
    # frases curtas demais (< 1.3 s) não dão tempo de ler a composição: junta com a próxima
    cards = [L.Card(c.inicio, c.fim, list(c.palavras)) for c in cards]
    i = 0
    while i < len(cards) - 1:
        c, n = cards[i], cards[i + 1]
        if (n.inicio - c.inicio) < 1.3 and len(c.palavras) + len(n.palavras) <= 6 and n.inicio - c.fim < 0.6:
            c.palavras += n.palavras; c.fim = n.fim; del cards[i + 1]
        else:
            i += 1
    for i, c in enumerate(cards):
        fim = (cards[i + 1].inicio if i + 1 < len(cards) else c.fim + 0.6)
        fim = min(fim, c.fim + 1.2)
        tpl = modelos[i % len(modelos)]
        k = _escolher_chave(c.palavras, chaves)
        antes = c.palavras[:k]
        chave = c.palavras[k]
        depois = c.palavras[k + 1:]
        blocos = []
        f_med, f_leve, f_gig = preset["fonte_media"], preset["fonte_leve"], preset["fonte_gigante"]
        tr = preset.get("tracking", 0.0)
        maius = preset.get("maiusculas", False)
        largura_max = int(W * 0.94)
        # textura/cor da palavra-chave segundo o modelo
        estilo_chave = tpl.get("chave", "inverter")
        if estilo_chave == "foto" and textura_img:
            textura, cor = textura_img, "#FFFFFF"
        elif estilo_chave == "cor":
            textura, cor = None, preset.get("cor_destaque", "#F5A21B")
        else:
            textura, cor = "inverter", "#FFFFFF"

        if tpl["nome"] == "faz":           # ref. 1: linha curta no alto à direita, gigante no centro, linha leve abaixo
            if antes:
                t1 = _limpo(" ".join(p.texto for p in antes))
                if len(antes) <= 2:   # curta: no alto à direita, como "o que"
                    tam = _ajustar_tamanho(f_med, t1, 160, int(W * 0.60), tr, esc, maius)
                    blocos.append(dict(texto=t1, fonte=f_med, tamanho=tam, inicio=antes[0].inicio, fim=fim,
                                       pos=[0.93, 0.24], ancora="direita", cor="#FFFFFF", camada="atras", anim="pop", tracking=tr, maiusculas=maius))
                else:                 # longa: linha inteira centralizada acima da gigante
                    tam = _ajustar_tamanho(f_med, t1, 150, largura_max, tr, esc, maius)
                    blocos.append(dict(texto=t1, fonte=f_med, tamanho=tam, inicio=antes[0].inicio, fim=fim,
                                       pos=[0.5, 0.22], ancora="centro", cor="#FFFFFF", camada="atras", anim="pop", tracking=tr, maiusculas=maius))
            tam = _ajustar_tamanho(f_gig, _limpo(chave.texto), 640, largura_max, tr, esc, maius)
            blocos.append(dict(texto=_limpo(chave.texto), fonte=f_gig, tamanho=tam, inicio=chave.inicio, fim=fim,
                               pos=[0.5, 0.34], ancora="centro", cor=cor, textura=textura, camada="atras", anim="pop", tracking=tr, maiusculas=maius))
            if depois:
                t2 = _limpo(" ".join(p.texto for p in depois))
                tam = _ajustar_tamanho(f_leve, t2, 160, largura_max, tr, esc, maius)
                blocos.append(dict(texto=t2, fonte=f_leve, tamanho=tam, inicio=depois[0].inicio, fim=fim,
                                   pos=[0.5, 0.53], ancora="centro", cor="#FFFFFF", camada="atras", anim="pop", tracking=tr, maiusculas=maius))
        elif tpl["nome"] == "rotina":      # ref. 2: "Literalmente / na sua / ROTINA" — empilhado à esquerda, ordem de leitura
            y = 0.40
            x_esq = 0.06
            texto_chave = _limpo(chave.texto)
            if len(antes) == 1 and L._norm(antes[0].texto) in PALAVRAS_FUNCAO:
                texto_chave = _limpo(antes[0].texto) + " " + texto_chave   # "A propriedade" em vez de "A" solto
                antes = []
            if antes:
                grande, resto = antes[:1] if len(antes) > 1 else antes, antes[1:]
                t1 = _limpo(" ".join(p.texto for p in grande))
                tam = _ajustar_tamanho(f_med, t1, 230 if len(t1) > 3 else 170, int(W * (0.96 - x_esq)), tr, esc, maius)
                blocos.append(dict(texto=t1, fonte=f_med, tamanho=tam, inicio=grande[0].inicio, fim=fim,
                                   pos=[x_esq, y], ancora="esquerda", cor="#FFFFFF", camada="atras", anim="pop", tracking=tr, maiusculas=maius))
                y += tam * 0.80 / 1920
                if resto:
                    t2 = _limpo(" ".join(p.texto for p in resto))
                    tam2 = _ajustar_tamanho(f_med, t2, 130, int(W * (0.96 - x_esq - 0.06)), tr, esc, maius)
                    blocos.append(dict(texto=t2, fonte=f_med, tamanho=tam2, inicio=resto[0].inicio, fim=fim,
                                       pos=[x_esq + 0.06, y], ancora="esquerda", cor="#FFFFFF", camada="atras", anim="pop", tracking=tr, maiusculas=maius))
                    y += tam2 * 0.55 / 1920
            tam = _ajustar_tamanho(f_gig, texto_chave, 300, int(W * 0.90), tr, esc, maius)
            blocos.append(dict(texto=texto_chave, fonte=f_gig, tamanho=tam, inicio=chave.inicio, fim=fim,
                               pos=[0.95, y + tam * 0.45 / 1920], ancora="direita", cor=cor, textura=textura,
                               camada=tpl.get("camada_chave", "frente"), anim="pop", tracking=tr, maiusculas=maius))
            y += tam * 0.95 / 1920
            if depois:
                t3 = _limpo(" ".join(p.texto for p in depois))
                tam3 = _ajustar_tamanho(f_leve, t3, 140, int(W * 0.88), tr, esc, maius)
                blocos.append(dict(texto=t3, fonte=f_leve, tamanho=tam3, inicio=depois[0].inicio, fim=fim,
                                   pos=[0.95, y + tam3 * 0.3 / 1920], ancora="direita", cor="#FFFFFF", camada="atras", anim="pop", tracking=tr, maiusculas=maius))
        else:                              # ref. 3: linha grande branca + gigante com foto/textura abaixo
            texto_chave = _limpo(chave.texto)
            if len(antes) == 1 and L._norm(antes[0].texto) in PALAVRAS_FUNCAO:
                texto_chave = _limpo(antes[0].texto) + " " + texto_chave
                antes = []
            if antes:
                t1 = _limpo(" ".join(p.texto for p in antes))
                tam = _ajustar_tamanho(f_med, t1, 230 if len(t1) > 3 else 170, largura_max, tr, esc, maius)
                blocos.append(dict(texto=t1, fonte=f_med, tamanho=tam, inicio=antes[0].inicio, fim=fim,
                                   pos=[0.5, 0.40], ancora="centro", cor="#FFFFFF", camada="atras", anim="pop", tracking=tr, maiusculas=maius))
            tam = _ajustar_tamanho(f_gig, texto_chave, 420, largura_max, tr, esc, maius)
            blocos.append(dict(texto=texto_chave, fonte=f_gig, tamanho=tam, inicio=chave.inicio, fim=fim,
                               pos=[0.5, 0.52], ancora="centro", cor=cor, textura=textura, camada="atras", anim="pop", tracking=tr, maiusculas=maius))
            if depois:
                t2 = _limpo(" ".join(p.texto for p in depois))
                tam = _ajustar_tamanho(f_leve, t2, 150, largura_max, tr, esc, maius)
                blocos.append(dict(texto=t2, fonte=f_leve, tamanho=tam, inicio=depois[0].inicio, fim=fim,
                                   pos=[0.5, 0.64], ancora="centro", cor="#FFFFFF", camada="atras", anim="pop", tracking=tr, maiusculas=maius))
        cenas.append({"inicio": c.inicio, "fim": fim, "frase": c.texto, "modelo": tpl["nome"], "blocos": blocos})
    return cenas


# ──────────────────────────────────────────────────────────────────
# Render completo (frames via pipe, áudio copiado do original)
# ──────────────────────────────────────────────────────────────────
def renderizar(entrada: Path, saida: Path, cenas: list[dict], orig: dict, texturas_dir: Path,
               cor_sutil: bool, crf: int, sem_mascara: bool):
    W, H, fps = orig["video"]["largura"], orig["video"]["altura"], orig["video"]["fps"]
    n = orig["video"]["frames"]
    dec = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-i", str(entrada), "-map", "0:v:0", "-fps_mode", "passthrough",
         "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE, bufsize=W * H * 3 * 4)
    filtros = "eq=contrast=1.04:saturation=1.06,unsharp=5:5:0.35:5:5:0.0" if cor_sutil else "null"
    enc = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-stats",
         "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-framerate", f"{fps:.6f}", "-i", "-",
         "-i", str(entrada),
         "-map", "0:v:0", "-map", "1:a:0?",
         "-vf", filtros,
         "-c:v", "libx264", "-preset", "medium", "-crf", str(crf), "-pix_fmt", "yuv420p",
         "-profile:v", "high", "-level", "4.1",
         "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
         "-c:a", "copy", "-movflags", "+faststart", str(saida)], stdin=subprocess.PIPE)
    seg = None if sem_mascara else Segmentador()
    R = Renderizador(W, H, fps, cenas, texturas_dir)
    tam = W * H * 3
    i = 0
    while True:
        buf = dec.stdout.read(tam)
        if len(buf) < tam:
            break
        fr = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
        t = i / fps
        out = R.frame(fr, t, seg)
        enc.stdin.write(out.tobytes())
        i += 1
        if i % 60 == 0:
            print(f"   frame {i}/{n} ({100 * i / max(1, n):.0f}%)", end="\r", flush=True)
    enc.stdin.close(); enc.wait(); dec.wait()
    print(f"   {i} frames renderizados" + " " * 20)


def renderizar_av(entrada: Path, saida: Path, cenas: list[dict], orig: dict, texturas_dir: Path,
                  crf: int, sem_mascara: bool):
    """Render frame a frame com PyAV: cada frame sai com o MESMO pts do original (VFR preservado),
    áudio copiado sem decodificar."""
    import av
    W, H = orig["video"]["largura"], orig["video"]["altura"]
    n = orig["video"]["frames"]
    inp = av.open(str(entrada))
    vin = inp.streams.video[0]
    vin.thread_type = "AUTO"
    ain = inp.streams.audio[0] if inp.streams.audio else None
    out = av.open(str(saida), "w", options={"movflags": "faststart"})
    vout = out.add_stream("libx264", rate=None)
    vout.width, vout.height = W, H
    vout.pix_fmt = "yuv420p"
    vout.time_base = vin.time_base
    vout.codec_context.time_base = vin.time_base   # sem isso o x264 rescala os pts e o mux falha
    vout.options = {"crf": str(crf), "preset": "medium", "profile": "high", "level": "4.1"}
    aout = out.add_stream_from_template(ain) if ain is not None else None
    seg = None if sem_mascara else Segmentador()
    R = Renderizador(W, H, orig["video"]["fps"], cenas, texturas_dir)
    i = 0
    streams = [vin] + ([ain] if ain is not None else [])
    for packet in inp.demux(streams):
        if ain is not None and packet.stream is ain:
            if packet.dts is None:      # pacote de flush do áudio: nada a copiar
                continue
            packet.stream = aout
            out.mux(packet)
            continue
        # no vídeo o pacote de flush (dts None) precisa ser decodificado: ele libera os últimos
        # frames que o decoder segura (B-frames); sem isso faltam ~6 frames no fim
        for frame in packet.decode():
            t = float(frame.pts * vin.time_base)
            img = frame.to_ndarray(format="rgb24")
            comp = R.frame(img, t, seg)
            nf = av.VideoFrame.from_ndarray(np.ascontiguousarray(comp), format="rgb24").reformat(format="yuv420p")
            nf.pts = frame.pts
            nf.time_base = vin.time_base
            for p in vout.encode(nf):
                out.mux(p)
            i += 1
            if i % 60 == 0:
                print(f"   frame {i}/{n} ({100 * i / max(1, n):.0f}%)  t={t:6.2f}s", end="\r", flush=True)
    for p in vout.encode():
        out.mux(p)
    out.close(); inp.close()
    print(f"   {i} frames renderizados" + " " * 30)


def main():
    ap = argparse.ArgumentParser(description="Tipografia cinética atrás do sujeito, sem alterar a montagem.")
    ap.add_argument("entrada", type=Path)
    ap.add_argument("--saida", type=Path)
    ap.add_argument("--preset", default="tipografia_cinetica")
    ap.add_argument("--texto", type=Path, help="roteiro/transcrição correta")
    ap.add_argument("--destaque", default="", help="palavras-chave (vírgula) que viram a palavra gigante")
    ap.add_argument("--cenas", type=Path, help="projeto .cenas.json revisado (pula transcrição e layout)")
    ap.add_argument("--textura", type=str, help="imagem para preencher a palavra-chave nos modelos 'foto'")
    ap.add_argument("--modelo", default="small")
    ap.add_argument("--max-palavras", type=int, default=4)
    ap.add_argument("--cor-sutil", action="store_true")
    ap.add_argument("--crf", type=int, default=17)
    ap.add_argument("--so-cenas", action="store_true", help="gera só o .cenas.json")
    ap.add_argument("--sem-mascara", action="store_true", help="não segmenta a pessoa (texto na frente)")
    ap.add_argument("--preview", type=str, help="renderiza só frames nesses tempos (ex. '0.5,2,4') em PNG")
    ap.add_argument("--motor", default="av", choices=["av", "ffmpeg"], help="av = PyAV (preserva VFR); ffmpeg = pipe CFR")
    a = ap.parse_args()

    entrada = a.entrada
    if not entrada.exists():
        sys.exit(f"Arquivo não encontrado: {entrada}")
    saida_dir = a.saida.parent if a.saida else AQUI / "saida"
    saida_dir.mkdir(parents=True, exist_ok=True)
    saida = a.saida or saida_dir / f"{entrada.stem}_tipografia.mp4"
    base = saida_dir / saida.stem
    preset = L.carregar_preset(a.preset)

    print("1) Registrando o original…")
    orig = L.probe(entrada); hash_o = L.hash_audio(entrada)
    W, H = orig["video"]["largura"], orig["video"]["altura"]
    print(f"   {W}x{H} @ {orig['video']['fps']} fps · {orig['duracao_s']:.3f}s · {orig['video']['frames']} frames")
    base.with_suffix(".original.json").write_text(json.dumps({**orig, "hash_audio": hash_o}, indent=2, ensure_ascii=False), encoding="utf-8")

    if a.cenas:
        print("2) Usando projeto revisado:", a.cenas)
        cenas = json.loads(a.cenas.read_text(encoding="utf-8"))["cenas"]
    else:
        print(f"2) Transcrevendo (whisper-{a.modelo})…")
        samples = L.carregar_audio_16k(entrada)
        trechos = L.transcrever(samples, a.modelo, "pt")
        if a.texto:
            trechos = L.alinhar_texto(trechos, a.texto.read_text(encoding="utf-8"))
        cards = L.montar_cards(trechos, a.max_palavras, 40)
        chaves = {L._norm(x) for x in a.destaque.split(",") if x.strip()}
        print("3) Layout automático…")
        cenas = layout_automatico(cards, preset, W, H, chaves, a.textura)
        base.with_suffix(".transcricao.txt").write_text(
            "\n".join(f"{L._ts(c['inicio'])} → {L._ts(c['fim'])}  [{c['modelo']}] {c['frase']}" for c in cenas), encoding="utf-8")
    proj = base.with_suffix(".cenas.json")
    proj.write_text(json.dumps({"preset": a.preset, "cenas": cenas}, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"   {len(cenas)} cenas · projeto em {proj}")
    if a.so_cenas:
        return

    if a.preview:
        print("4) Preview de frames…")
        R = Renderizador(W, H, orig["video"]["fps"], cenas, saida_dir)
        seg = None if a.sem_mascara else Segmentador()
        for ts in [float(x) for x in a.preview.split(",")]:
            raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(ts), "-i", str(entrada), "-frames:v", "1",
                                  "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
            fr = np.frombuffer(raw, np.uint8).reshape(H, W, 3)
            seg and setattr(seg, "anterior", None)
            out = R.frame(fr, ts, seg)
            p = saida_dir / f"{saida.stem}_preview_{ts:.2f}.png"
            Image.fromarray(out).save(p); print("   ", p)
        return

    print("4) Renderizando (segmentação + composição, timestamps originais)…")
    if a.cor_sutil:
        print("   aviso: --cor-sutil só está disponível no render por ffmpeg (--motor ffmpeg)")
    if a.motor == "ffmpeg":
        renderizar(entrada, saida, cenas, orig, saida_dir, a.cor_sutil, a.crf, a.sem_mascara)
    else:
        renderizar_av(entrada, saida, cenas, orig, saida_dir, a.crf, a.sem_mascara)

    print("5) Conferindo…")
    novo = L.probe(saida)
    ok, msgs = L.verificar(orig, novo, hash_o, L.hash_audio(saida))
    rel = ["# Relatório de pós-produção (tipografia)", f"- entrada: `{entrada}`", f"- saída: `{saida}`", ""] + [f"- {m}" for m in msgs]
    rel += ["", "✅ MONTAGEM PRESERVADA" if ok else "❌ ALGO MUDOU — NÃO PUBLICAR"]
    base.with_suffix(".relatorio.md").write_text("\n".join(rel), encoding="utf-8")
    for m in msgs: print("   " + m)
    print("   " + rel[-1]); print("→", saida)
    sys.exit(0 if ok else 2)


if __name__ == "__main__":
    main()
