#!/usr/bin/env python3
"""
🎬 TIPOGRAFIA CINÉTICA v2 — direção de arte tipográfica sobre vídeo montado.

Diferenças para tipografia.py (v1):
  • Poppins ExtraBold/Black, tracking e entrelinha compactos, palavras gigantes que vazam a tela;
  • efeito de VIDRO real (fundo refratado + fosco + brilho + borda) alternado com texto sólido;
  • paleta extraída do próprio vídeo (uma cor de destaque + branco), nunca laranja por padrão;
  • recorte da pessoa combinando dois modelos (humano + alta resolução), borda refinada com
    guided filter, fechamento de buracos, suavização temporal com reset nos cortes;
  • layout ciente da pessoa: nada na frente do rosto; gigantes passam atrás do corpo;
  • animações variadas (impacto, deslize, revelação por letra, pop) com saída;
  • efeitos sonoros sintetizados e sincronizados com as entradas (whoosh, impacto, vidro),
    mixados abaixo da voz — a voz é somada sem alteração de ganho;
  • timestamps de vídeo preservados (PyAV), conferência de frames/duração no fim.

Uso:
    python pos_producao/cinetica.py video.mov --texto roteiro.txt --destaque "a,b,c"
    python pos_producao/cinetica.py video.mov --cenas saida/video_cinetica.cenas.json --preview "1,4,9"
    python pos_producao/cinetica.py video.mov --cenas saida/video_cinetica.cenas.json
"""

from __future__ import annotations

import argparse
import colorsys
import json
import math
import re
import subprocess
import sys
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import legendar as L  # noqa: E402

AQUI = Path(__file__).resolve().parent
FONTS = AQUI / "fonts"
MODELOS = AQUI / "modelos"

FUNCAO = L.PALAVRAS_FUNCAO | {"você", "voce", "vai", "tem", "ter", "ser", "está", "esta", "são", "foi", "mais",
                              "muito", "bem", "já", "ja", "aí", "ai", "não", "nao", "sim", "ele", "ela", "eles",
                              "elas", "nós", "nos", "eu", "lá", "la", "aqui", "esse", "essa", "isso", "este"}


# ══════════════════════════════════════════════════════════════════
# Paleta
# ══════════════════════════════════════════════════════════════════
def extrair_paleta(entrada: Path, duracao: float, passo: float = 2.0) -> dict:
    """k-means nas cores do vídeo; destaque = cor saturada mais presente FORA de laranja/terracota."""
    pix = []
    t = 0.5
    while t < duracao:
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", str(entrada), "-frames:v", "1",
                              "-vf", "scale=96:170", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
        if len(raw) == 96 * 170 * 3:
            pix.append(np.frombuffer(raw, np.uint8).reshape(-1, 3))
        t += passo
    pix = np.concatenate(pix).astype(np.float32)
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 40, 0.5)
    _, lab, cen = cv2.kmeans(pix, 12, None, crit, 3, cv2.KMEANS_PP_CENTERS)
    freq = np.bincount(lab.flatten(), minlength=12) / len(lab)
    cores = []
    for c, f in zip(cen, freq):
        r, g, b = [int(v) for v in c]
        h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        cores.append({"hex": f"#{r:02X}{g:02X}{b:02X}", "freq": round(float(f), 4), "h": int(h * 360), "s": round(s, 2), "v": round(v, 2)})
    cores.sort(key=lambda c: -c["freq"])
    laranja = lambda h: (0 <= h <= 48) or h >= 345
    cand = [c for c in cores if c["s"] >= 0.3 and c["v"] >= 0.35 and not laranja(c["h"])]
    if cand:
        best = max(cand, key=lambda c: c["freq"] * (0.5 + c["s"]))
        h, s, v = best["h"] / 360, best["s"], best["v"]
        # versão para texto: mais clara e um pouco mais saturada, legível sobre a cena
        r, g, b = colorsys.hsv_to_rgb(h, min(1.0, s * 1.15), min(1.0, max(v, 0.78)))
        destaque = f"#{int(r*255):02X}{int(g*255):02X}{int(b*255):02X}"
        origem = best["hex"]
    else:  # cena neutra: azul-acinzentado frio discreto
        destaque, origem = "#9FB8C8", None
    return {"destaque": destaque, "origem_destaque": origem, "dominantes": cores[:8]}


# ══════════════════════════════════════════════════════════════════
# Segmentação (humano + alta resolução, refinada)
# ══════════════════════════════════════════════════════════════════
class Recorte:
    def __init__(self, fino: bool = True):
        import onnxruntime as ort
        so = ort.SessionOptions(); so.intra_op_num_threads = 4
        self.u2 = ort.InferenceSession(str(MODELOS / "u2net_human_seg.onnx"), so, providers=["CPUExecutionProvider"])
        self.u2_in = self.u2.get_inputs()[0].name
        self.isn = None
        if fino and (MODELOS / "isnet-general-use.onnx").exists():
            self.isn = ort.InferenceSession(str(MODELOS / "isnet-general-use.onnx"), so, providers=["CPUExecutionProvider"])
            self.isn_in = self.isn.get_inputs()[0].name
        self.anterior: np.ndarray | None = None
        self.frame_ant: np.ndarray | None = None
        self._ultima = None; self._t_ultimo = None

    def _u2(self, img):
        x = cv2.resize(img, (320, 320), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
        x = ((x - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]).astype(np.float32).transpose(2, 0, 1)[None]
        y = self.u2.run(None, {self.u2_in: x})[0][0, 0]
        return (y - y.min()) / (y.max() - y.min() + 1e-6)

    def _isn(self, img):
        x = cv2.resize(img, (1024, 1024), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
        x = (x - 0.5).astype(np.float32).transpose(2, 0, 1)[None]
        y = self.isn.run(None, {self.isn_in: x})[0][0, 0]
        return (y - y.min()) / (y.max() - y.min() + 1e-6)

    def bbox_rapido(self, img) -> tuple | None:
        """Caixa da pessoa (x0,y0,x1,y1 em fração) só com o modelo humano — para o layout."""
        h, w = img.shape[:2]
        m = cv2.resize(self._u2(img), (w, h)) > 0.5
        if m.sum() < 0.004 * w * h:
            return None
        ys, xs = np.where(m)
        return (xs.min() / w, ys.min() / h, xs.max() / w, ys.max() / h)

    def mascara(self, img: np.ndarray, t: float) -> np.ndarray:
        if self._t_ultimo is not None and self._ultima is not None and 0 <= (t - self._t_ultimo) < 0.025:
            return self._ultima
        h, w = img.shape[:2]
        # corte de take: reseta a suavização temporal (evita fantasma entre cenas)
        peq = cv2.resize(img, (64, 114), interpolation=cv2.INTER_AREA).astype(np.int16)
        if self.frame_ant is not None and np.abs(peq - self.frame_ant).mean() > 28:
            self.anterior = None
        self.frame_ant = peq

        hum = cv2.resize(self._u2(img), (w, h), interpolation=cv2.INTER_LINEAR)
        if self.isn is not None:
            fino = cv2.resize(self._isn(img), (w, h), interpolation=cv2.INTER_LINEAR)
            # fica com o modelo fino só onde o modelo humano (dilatado) diz que há pessoa
            zona = cv2.dilate((hum > 0.25).astype(np.uint8), np.ones((61, 61), np.uint8)) > 0
            m = np.where(zona, np.maximum(fino, hum * 0.35), 0.0).astype(np.float32)
        else:
            m = hum.astype(np.float32)
        # contraste na borda, fecha buracos, remove ilhas pequenas
        m = np.clip((m - 0.30) / 0.40, 0, 1)
        binario = (m > 0.5).astype(np.uint8)
        binario = cv2.morphologyEx(binario, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
        n, lab, stats, _ = cv2.connectedComponentsWithStats(binario)
        if n > 1:
            keep = np.zeros_like(binario)
            maior = stats[1:, cv2.CC_STAT_AREA].max()
            for i in range(1, n):
                if stats[i, cv2.CC_STAT_AREA] >= 0.25 * maior:
                    keep[lab == i] = 1
            m = np.where(cv2.dilate(keep, np.ones((9, 9), np.uint8)) > 0, m, 0)
            m = np.maximum(m, keep.astype(np.float32) * 0.0)
        # borda guiada pela imagem (cola na silhueta, reduz halo) + leve erosão
        try:
            guia = cv2.resize(img, (w // 2, h // 2), interpolation=cv2.INTER_AREA)
            mm = cv2.resize(m, (w // 2, h // 2), interpolation=cv2.INTER_LINEAR)
            mm = cv2.ximgproc.guidedFilter(guia, mm.astype(np.float32), 6, 1e-3)
            m = cv2.resize(mm, (w, h), interpolation=cv2.INTER_LINEAR)
        except Exception:
            pass
        m = np.clip(m, 0, 1)
        m = cv2.erode(m, np.ones((3, 3), np.uint8))
        m = cv2.GaussianBlur(m, (0, 0), 1.2)
        if self.anterior is not None:
            m = 0.7 * m + 0.3 * self.anterior
        self.anterior = m
        self._ultima, self._t_ultimo = m, t
        return m


# ══════════════════════════════════════════════════════════════════
# Modelo de cena
# ══════════════════════════════════════════════════════════════════
@dataclass
class Bloco:
    texto: str
    fonte: str
    tamanho: int
    inicio: float
    fim: float
    pos: tuple[float, float]
    ancora: str = "centro"      # centro | esquerda | direita
    estilo: str = "solido"      # solido | vidro
    cor: str = "#FFFFFF"
    camada: str = "atras"       # atras | frente
    anim: str = "impacto"       # impacto | desliza_esq | desliza_dir | revela | pop | sobe
    saida: str = "fade"         # fade | desliza | escala
    tracking: float = -0.04
    sombra: bool = True
    maiusculas: bool = False
    som: str | None = None      # whoosh | impacto | vidro | None


def _fonte(nome: str, tam: int) -> ImageFont.FreeTypeFont:
    p = FONTS / nome
    return ImageFont.truetype(str(p if p.exists() else FONTS / f"{nome}.ttf"), max(8, tam))


def _largura(f, txt, tr_px):
    return sum(f.getlength(c) for c in txt) + tr_px * (len(txt) - 1) if txt else 0.0


def desenhar_chars(txt: str, f: ImageFont.FreeTypeFont, tr_px: float) -> tuple[np.ndarray, list[tuple[int, int]]]:
    """Alfa do texto inteiro + [(x_ini, x_fim)] de cada caractere (para animar letra a letra)."""
    asc, desc = f.getmetrics()
    w = int(math.ceil(_largura(f, txt, tr_px))) + 16
    h = asc + desc + 16
    img = Image.new("L", (max(1, w), h), 0)
    d = ImageDraw.Draw(img)
    x = 8.0; spans = []
    for c in txt:
        d.text((x, 8), c, font=f, fill=255)
        cw = f.getlength(c)
        spans.append((int(x), int(math.ceil(x + cw))))
        x += cw + tr_px
    return np.array(img), spans


def _hex(c: str) -> np.ndarray:
    c = c.lstrip("#")
    return np.array([int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)], np.float32)


def _ease_out(t): return 1 - (1 - t) ** 3
def _ease_back(t):  # overshoot
    s = 1.70158; t = t - 1
    return 1 + t * t * ((s + 1) * t + s)


# ══════════════════════════════════════════════════════════════════
# Renderizador
# ══════════════════════════════════════════════════════════════════
class Render:
    def __init__(self, W, H, cenas: list[dict], cor_vidro: str = "#9FB8C8"):
        self.W, self.H = W, H
        self.esc = H / 1920.0
        self.cenas = cenas
        self.cor_vidro = _hex(cor_vidro)
        self.cf = {}; self.ct = {}

    def fonte(self, nome, tam):
        k = (nome, tam)
        if k not in self.cf: self.cf[k] = _fonte(nome, tam)
        return self.cf[k]

    def alfa(self, b: Bloco):
        tam = int(b.tamanho * self.esc)
        txt = b.texto.upper() if b.maiusculas else b.texto
        k = (txt, b.fonte, tam, round(b.tracking, 3))
        if k not in self.ct:
            self.ct[k] = desenhar_chars(txt, self.fonte(b.fonte, tam), b.tracking * tam)
        return self.ct[k]

    # ---- texturas -------------------------------------------------
    def vidro(self, frame, x0, y0, w, h, a):
        """Vidro: fundo ampliado (refração) + desfoque fosco + clareada + brilho + borda."""
        H, W = frame.shape[:2]
        # região ampliada 7% em volta do centro (refração), lida com margem
        cx, cy = x0 + w / 2, y0 + h / 2
        s = 1.07
        X0, Y0 = int(cx - w / 2 / s), int(cy - h / 2 / s)
        X1, Y1 = int(cx + w / 2 / s), int(cy + h / 2 / s)
        X0c, Y0c, X1c, Y1c = max(0, X0), max(0, Y0), min(W, X1), min(H, Y1)
        reg = frame[Y0c:Y1c, X0c:X1c]
        if reg.size == 0:
            return np.full((h, w, 3), 255, np.float32)
        reg = cv2.copyMakeBorder(reg, Y0c - Y0, Y1 - Y1c, X0c - X0, X1 - X1c, cv2.BORDER_REPLICATE)
        refr = cv2.resize(reg, (w, h), interpolation=cv2.INTER_LINEAR).astype(np.float32)
        fosco = cv2.GaussianBlur(refr, (0, 0), 6 * self.esc + 1)
        cinza = fosco.mean(axis=2, keepdims=True)
        lum = float(fosco.mean()) / 255.0                         # fundo claro → menos clareada, mais contraste
        lift = 0.18 * (1 - lum) + 0.02
        base = fosco * (0.78 - lift) + cinza * 0.08 + 255 * lift + self.cor_vidro * 0.12   # leve tom da paleta
        if lum > 0.55:
            base = base * (0.84 - 0.30 * (lum - 0.55))             # escurece o vidro sobre céu/paredes claras
        # brilho diagonal (luz vindo de cima/esquerda)
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        g = np.clip(1.0 - (xx / max(1, w) * 0.7 + yy / max(1, h) * 0.9), 0, 1) ** 2
        base = base + 255 * g[..., None] * 0.28
        # faixa de reflexo fina no terço superior
        faixa = np.exp(-((yy / max(1, h) - 0.22) ** 2) / 0.004)[..., None]
        base = base + 255 * faixa * 0.18
        # bordas: borda interna clara (vidro), sombra interna embaixo/direita
        k = max(2, int(3 * self.esc))
        ero = cv2.erode(a, np.ones((k, k), np.uint8))
        rim = np.clip(a - ero, 0, 1)
        rim_claro = np.roll(rim, (-1, -1), axis=(0, 1))
        rim_escuro = np.roll(rim, (2, 2), axis=(0, 1))
        base = base * (1 - rim_claro[..., None] * 0.85) + 255 * rim_claro[..., None] * 0.85
        base = base * (1 - rim_escuro[..., None] * (0.35 + 0.35 * max(0.0, lum - 0.5)))
        return np.clip(base, 0, 255)

    def aplicar(self, base: np.ndarray, frame: np.ndarray, b: Bloco, t: float, fim_cena: float):
        if t < b.inicio or t > fim_cena:
            return
        alfa_full, spans = self.alfa(b)
        th, tw = alfa_full.shape
        d_in = {"impacto": 0.14, "desliza_esq": 0.20, "desliza_dir": 0.20, "revela": 0.26, "pop": 0.16, "sobe": 0.18}.get(b.anim, 0.16)
        k = min(1.0, (t - b.inicio) / d_in)
        e = _ease_out(k)
        escala, op, dx, dy = 1.0, 1.0, 0, 0
        alfa = alfa_full
        if b.anim == "impacto":
            escala = 1.0 + 0.18 * (1 - _ease_out(k)); op = min(1.0, k * 2.5)
        elif b.anim == "pop":
            escala = 0.88 + 0.12 * _ease_back(k) if k < 1 else 1.0; op = e
        elif b.anim == "desliza_esq":
            dx = int(-90 * self.esc * (1 - _ease_back(k))); op = e
        elif b.anim == "desliza_dir":
            dx = int(90 * self.esc * (1 - _ease_back(k))); op = e
        elif b.anim == "sobe":
            dy = int(50 * self.esc * (1 - _ease_out(k))); op = e
        elif b.anim == "revela" and k < 1:
            # letra a letra: cada char sobe e aparece com atraso
            alfa = np.zeros_like(alfa_full)
            n = max(1, len(spans)); por = 0.55 / n
            for i, (xa, xb) in enumerate(spans):
                kk = np.clip((k - i * por) / max(1e-6, 1 - (n - 1) * por), 0, 1)
                if kk <= 0: continue
                ee = _ease_out(kk)
                sh = int(26 * self.esc * (1 - ee))
                col = alfa_full[:, xa:xb].astype(np.float32) * ee
                if sh > 0:
                    col = np.vstack([np.zeros((sh, col.shape[1]), np.float32), col[:-sh]])
                alfa[:, xa:xb] = np.maximum(alfa[:, xa:xb], col.astype(np.uint8))
        # saída
        d_out = 0.13
        resto = fim_cena - t
        if resto < d_out:
            q = max(0.0, resto / d_out)
            if b.saida == "escala":
                escala *= 1.0 + 0.05 * (1 - q); op *= q
            elif b.saida == "desliza":
                dx += int(60 * self.esc * (1 - q)); op *= q
            else:
                op *= q
        if op <= 0.01:
            return
        if abs(escala - 1) > 1e-3:
            alfa = cv2.resize(alfa, (max(1, int(tw * escala)), max(1, int(th * escala))), interpolation=cv2.INTER_AREA)
            th, tw = alfa.shape
        cx = int(b.pos[0] * self.W) + dx; cy = int(b.pos[1] * self.H) + dy
        x0 = cx if b.ancora == "esquerda" else (cx - tw if b.ancora == "direita" else cx - tw // 2)
        y0 = cy - th // 2
        xa, ya, xb, yb = max(0, x0), max(0, y0), min(self.W, x0 + tw), min(self.H, y0 + th)
        if xb <= xa or yb <= ya:
            return
        a = alfa[ya - y0:yb - y0, xa - x0:xb - x0].astype(np.float32) / 255.0
        w, h = xb - xa, yb - ya
        reg = base[ya:yb, xa:xb].astype(np.float32)
        # sombra suave (legibilidade sobre céu claro) — só em texto sólido
        if b.sombra and b.estilo == "solido":
            sh = cv2.GaussianBlur(a, (0, 0), 7 * self.esc + 1)
            oy, ox = int(6 * self.esc), int(2 * self.esc)
            shs = np.zeros_like(sh); shs[oy:, ox:] = sh[:h - oy, :w - ox]
            reg = reg * (1 - shs[..., None] * 0.38 * op)
        if b.estilo == "vidro":
            tex = self.vidro(frame, xa, ya, w, h, a)
            aa = a * op * 0.97
        else:
            tex = np.broadcast_to(_hex(b.cor), (h, w, 3))
            aa = a * op
        base[ya:yb, xa:xb] = np.clip(reg * (1 - aa[..., None]) + tex * aa[..., None], 0, 255).astype(np.uint8)

    def frame(self, frame: np.ndarray, t: float, rec: Recorte | None):
        ativos = []
        for c in self.cenas:
            if c["inicio"] - 0.02 <= t <= c["fim"] + 0.02:
                for b in c["blocos"]:
                    bb = Bloco(**{**b, "pos": tuple(b["pos"])})
                    if bb.inicio <= t <= c["fim"]:
                        ativos.append((bb, c["fim"], c.get("pessoa")))
        if not ativos:
            return frame
        base = frame.copy()
        atras = [(b, f) for b, f, p in ativos if b.camada == "atras"]
        frente = [(b, f) for b, f, p in ativos if b.camada == "frente"]
        precisa_mascara = any(p for _, _, p in ativos) and atras
        for b, f in atras:
            self.aplicar(base, frame, b, t, f)
        if precisa_mascara and rec is not None:
            m = rec.mascara(frame, t)[..., None]
            base = (base.astype(np.float32) * (1 - m) + frame.astype(np.float32) * m).astype(np.uint8)
        for b, f in frente:
            self.aplicar(base, frame, b, t, f)
        return base


# ══════════════════════════════════════════════════════════════════
# Layout (direção de arte)
# ══════════════════════════════════════════════════════════════════
def _limpo(txt: str) -> str:
    return re.sub(r"[.,;:…]+$", "", txt.replace(",", ""))


def _chave(palavras, chaves):
    for i, p in enumerate(palavras):
        if L._norm(p.texto) in chaves:
            return i
    cand = [(len(L._norm(p.texto)), i) for i, p in enumerate(palavras) if L._norm(p.texto) not in FUNCAO]
    return max(cand)[1] if cand else max((len(p.texto), i) for i, p in enumerate(palavras))[1]


def _tam_para_largura(fonte, txt, alvo_px, esc, tracking, teto, piso=90, max_px=None):
    """Tamanho (px a 1920) cujo texto mede ~alvo_px, limitado a [piso, teto];
    nunca ultrapassa max_px (largura disponível), mesmo abaixo do piso."""
    f = _fonte(fonte, int(200 * esc))
    w200 = _largura(f, txt, tracking * 200 * esc)
    if w200 <= 0: return piso
    tam = 200 * alvo_px / w200
    tam = max(piso, min(teto, tam))
    if max_px is not None:
        tam = min(tam, 200 * max_px / w200)
    return int(max(60, tam))


def layout(cards, preset, W, H, chaves, bboxes: list[tuple | None]) -> list[dict]:
    esc = H / 1920.0
    cor = preset["cor_destaque"]
    F_X = preset.get("fonte_extra", "Poppins-ExtraBold.ttf")
    F_B = preset.get("fonte_black", "Poppins-Black.ttf")
    tr = preset.get("tracking", -0.04)
    lead = preset.get("entrelinha", 0.84)
    estilos_gig = preset.get("ciclo_gigante", ["cor", "vidro", "branco", "vidro", "cor", "branco"])
    cenas = []
    # funde frases curtas demais
    cards = [L.Card(c.inicio, c.fim, list(c.palavras)) for c in cards]
    i = 0
    while i < len(cards) - 1:
        c, n = cards[i], cards[i + 1]
        if (n.inicio - c.inicio) < 1.25 and len(c.palavras) + len(n.palavras) <= 6 and n.inicio - c.fim < 0.6:
            c.palavras += n.palavras; c.fim = n.fim; del cards[i + 1]
        else:
            i += 1
    for i, c in enumerate(cards):
        fim = min(cards[i + 1].inicio if i + 1 < len(cards) else c.fim + 0.7, c.fim + 1.1)
        k = _chave(c.palavras, chaves)
        antes, chave, depois = c.palavras[:k], c.palavras[k], c.palavras[k + 1:]
        txt_chave = _limpo(chave.texto)
        if len(antes) == 1 and L._norm(antes[0].texto) in FUNCAO:
            txt_chave = _limpo(antes[0].texto) + " " + txt_chave; antes = []
        if len(depois) == 1 and L._norm(depois[0].texto) in FUNCAO and len(txt_chave) < 9:
            txt_chave = txt_chave + " " + _limpo(depois[0].texto); depois = []
        estilo = estilos_gig[i % len(estilos_gig)]
        gig = dict(fonte=F_B, estilo="vidro" if estilo == "vidro" else "solido",
                   cor=cor if estilo == "cor" else "#FFFFFF")
        pessoa = bboxes[i] if i < len(bboxes) else None
        # região livre do rosto: a cabeça ocupa o topo da caixa da pessoa
        if pessoa:
            px0, py0, px1, py1 = pessoa
            cabeca = (py0 - 0.02, py0 + 0.22 * (py1 - py0) + 0.02)
            torso = py0 + 0.45 * (py1 - py0)
        else:
            cabeca, torso = None, None
        modelo = ["pilha", "centro", "bloco"][i % 3]
        blocos = []
        som_gig = "vidro" if gig["estilo"] == "vidro" else "impacto"
        anim_gig = "revela" if gig["estilo"] == "vidro" else ("impacto" if i % 2 == 0 else "pop")

        if modelo == "pilha":   # ref 2: empilhado à esquerda, gigante vazando pela direita
            x = 0.05; y = 0.30 if not cabeca else max(0.16, cabeca[0] - 0.19)
            if antes:
                grande, resto = antes[:1] if len(antes) > 1 else antes, antes[1:]
                t1 = _limpo(" ".join(p.texto for p in grande))
                tam = _tam_para_largura(F_X, t1, W * 0.72, esc, tr, 260, 150, max_px=W * 0.90)
                blocos.append(dict(texto=t1, fonte=F_X, tamanho=tam, inicio=grande[0].inicio, fim=fim, pos=[x, y],
                                   ancora="esquerda", estilo="solido", cor="#FFFFFF", camada="frente", anim="desliza_esq",
                                   saida="desliza", tracking=tr, som="whoosh"))
                y += tam * lead / 1920
                if resto:
                    t2 = _limpo(" ".join(p.texto for p in resto))
                    tam2 = _tam_para_largura(F_X, t2, W * 0.5, esc, tr, 150, 100, max_px=W * 0.86)
                    blocos.append(dict(texto=t2, fonte=F_X, tamanho=tam2, inicio=resto[0].inicio, fim=fim, pos=[x + 0.04, y],
                                       ancora="esquerda", estilo="solido", cor="#FFFFFF", camada="frente", anim="sobe",
                                       saida="fade", tracking=tr, som=None))
                    y += tam2 * lead / 1920
            tamg = _tam_para_largura(F_B, txt_chave, W * 1.04, esc, tr, 520, 150)
            yg = y + tamg * 0.5 / 1920
            if torso is not None:
                yg = max(yg, torso - 0.02)
            blocos.append(dict(texto=txt_chave, tamanho=tamg, inicio=chave.inicio, fim=fim, pos=[-0.01, yg], ancora="esquerda",
                               camada="atras" if pessoa else "frente", anim=anim_gig, saida="escala", tracking=tr, som=som_gig, **gig))
            y = yg + tamg * 0.5 / 1920
            if depois:
                t3 = _limpo(" ".join(p.texto for p in depois))
                tam3 = _tam_para_largura(F_X, t3, W * 0.6, esc, tr, 140, 96, max_px=W * 0.90)
                blocos.append(dict(texto=t3, fonte=F_X, tamanho=tam3, inicio=depois[0].inicio, fim=fim, pos=[0.95, y + tam3 * 0.45 / 1920],
                                   ancora="direita", estilo="solido", cor="#FFFFFF", camada="atras" if pessoa else "frente",
                                   anim="desliza_dir", saida="fade", tracking=tr, som="whoosh"))
        elif modelo == "centro":  # ref 1: curta no alto à direita, gigante central vazando, linha abaixo
            ytop = 0.20 if not cabeca else max(0.12, cabeca[0] - 0.10)
            if antes:
                t1 = _limpo(" ".join(p.texto for p in antes))
                tam = _tam_para_largura(F_X, t1, W * (0.55 if len(antes) <= 2 else 0.9), esc, tr, 170, 110, max_px=W * 0.92)
                blocos.append(dict(texto=t1, fonte=F_X, tamanho=tam, inicio=antes[0].inicio, fim=fim,
                                   pos=[0.94, ytop] if len(antes) <= 2 else [0.5, ytop], ancora="direita" if len(antes) <= 2 else "centro",
                                   estilo="solido", cor="#FFFFFF", camada="frente", anim="desliza_dir", saida="fade", tracking=tr, som="whoosh"))
            tamg = _tam_para_largura(F_B, txt_chave, W * 1.05, esc, tr, 560, 150)
            yg = ytop + 0.07 + tamg * 0.5 / 1920
            if torso is not None:
                yg = max(yg, torso)
            blocos.append(dict(texto=txt_chave, tamanho=tamg, inicio=chave.inicio, fim=fim, pos=[-0.01, yg], ancora="esquerda",
                               camada="atras" if pessoa else "frente", anim=anim_gig, saida="escala", tracking=tr, som=som_gig, **gig))
            if depois:
                t2 = _limpo(" ".join(p.texto for p in depois))
                tam2 = _tam_para_largura(F_X, t2, W * 0.86, esc, tr, 170, 100, max_px=W * 0.92)
                yl = yg + tamg * 0.5 / 1920 + tam2 * 0.4 / 1920
                blocos.append(dict(texto=t2, fonte=F_X, tamanho=tam2, inicio=depois[0].inicio, fim=fim, pos=[0.5, yl], ancora="centro",
                                   estilo="solido", cor="#FFFFFF", camada="atras" if pessoa else "frente", anim="sobe", saida="fade", tracking=tr, som=None))
        else:                     # ref 3: linha grande branca + gigante vidro/cor abaixo
            ytop = 0.26 if not cabeca else max(0.14, cabeca[0] - 0.12)
            if antes:
                t1 = _limpo(" ".join(p.texto for p in antes))
                tam = _tam_para_largura(F_X, t1, W * 0.9, esc, tr, 230, 120, max_px=W * 0.94)
                blocos.append(dict(texto=t1, fonte=F_X, tamanho=tam, inicio=antes[0].inicio, fim=fim, pos=[0.5, ytop], ancora="centro",
                                   estilo="solido", cor="#FFFFFF", camada="frente", anim="impacto", saida="fade", tracking=tr, som="whoosh"))
                ytop += tam * lead / 1920
            tamg = _tam_para_largura(F_B, txt_chave, W * 1.04, esc, tr, 540, 150)
            yg = ytop + tamg * 0.45 / 1920
            if torso is not None:
                yg = max(yg, torso - 0.03)
            blocos.append(dict(texto=txt_chave, tamanho=tamg, inicio=chave.inicio, fim=fim, pos=[-0.01, yg], ancora="esquerda",
                               camada="atras" if pessoa else "frente", anim=anim_gig, saida="escala", tracking=tr, som=som_gig, **gig))
            if depois:
                t2 = _limpo(" ".join(p.texto for p in depois))
                tam2 = _tam_para_largura(F_X, t2, W * 0.7, esc, tr, 150, 96, max_px=W * 0.92)
                blocos.append(dict(texto=t2, fonte=F_X, tamanho=tam2, inicio=depois[0].inicio, fim=fim,
                                   pos=[0.5, yg + tamg * 0.5 / 1920 + tam2 * 0.45 / 1920], ancora="centro", estilo="solido", cor="#FFFFFF",
                                   camada="atras" if pessoa else "frente", anim="desliza_esq", saida="fade", tracking=tr, som=None))
        # nenhum bloco "frente" sobre o rosto
        if cabeca:
            for b in blocos:
                if b["camada"] == "frente":
                    y0b = b["pos"][1] - b["tamanho"] * 0.5 / 1920; y1b = b["pos"][1] + b["tamanho"] * 0.5 / 1920
                    if y1b > cabeca[0] and y0b < cabeca[1]:
                        b["camada"] = "atras"
        cenas.append({"inicio": c.inicio, "fim": fim, "frase": c.texto, "modelo": modelo, "pessoa": pessoa, "blocos": blocos})
    return cenas


# ══════════════════════════════════════════════════════════════════
# Efeitos sonoros sintetizados
# ══════════════════════════════════════════════════════════════════
SR_SFX = 44100


def _env(n, atk, dec, curva=2.0):
    t = np.arange(n) / SR_SFX
    a = np.clip(t / max(1e-4, atk), 0, 1)
    d = np.exp(-np.clip(t - atk, 0, None) / max(1e-4, dec)) ** curva
    return a * d


def sfx_whoosh(dur=0.22, sentido=1):
    n = int(dur * SR_SFX)
    rng = np.random.default_rng(7)
    ruido = rng.standard_normal(n).astype(np.float32)
    # varredura de passa-banda via filtragem por FFT simples
    t = np.linspace(0, 1, n)
    f0 = 900 + 2600 * (t if sentido > 0 else 1 - t)
    out = np.zeros(n, np.float32)
    bloco = 512
    for i in range(0, n, bloco):
        seg = ruido[i:i + bloco]
        if len(seg) < 32: break
        esp = np.fft.rfft(seg * np.hanning(len(seg)))
        fr = np.fft.rfftfreq(len(seg), 1 / SR_SFX)
        fc = f0[min(i, n - 1)]
        g = np.exp(-((fr - fc) / (fc * 0.45)) ** 2)
        out[i:i + len(seg)] += np.fft.irfft(esp * g, len(seg)).astype(np.float32)
    env = _env(n, 0.05, 0.09, 1.3)
    out = out * env
    return out / (np.abs(out).max() + 1e-6) * 0.55


def sfx_impacto(dur=0.32):
    n = int(dur * SR_SFX); t = np.arange(n) / SR_SFX
    f = 70 * np.exp(-t * 14) + 38
    fase = 2 * np.pi * np.cumsum(f) / SR_SFX
    sub = np.sin(fase) * _env(n, 0.003, 0.12, 1.0)
    rng = np.random.default_rng(3)
    click = rng.standard_normal(n).astype(np.float32) * _env(n, 0.0005, 0.012, 1.0) * 0.5
    click = np.convolve(click, np.ones(6) / 6, mode="same")
    out = (sub * 1.0 + click).astype(np.float32)
    return out / (np.abs(out).max() + 1e-6) * 0.8


def sfx_vidro(dur=0.55):
    n = int(dur * SR_SFX); t = np.arange(n) / SR_SFX
    out = np.zeros(n, np.float32)
    for f, g, d in [(2350, 1.0, 0.22), (3520, 0.55, 0.16), (5230, 0.3, 0.11), (1180, 0.35, 0.3)]:
        out += np.sin(2 * np.pi * f * t + 0.3) * g * _env(n, 0.002, d, 1.0)
    rng = np.random.default_rng(11)
    brilho = rng.standard_normal(n).astype(np.float32)
    esp = np.fft.rfft(brilho); fr = np.fft.rfftfreq(n, 1 / SR_SFX)
    brilho = np.fft.irfft(esp * (fr > 4000) * np.exp(-(fr - 7000) ** 2 / 2.5e7), n).astype(np.float32)
    out += brilho / (np.abs(brilho).max() + 1e-6) * 0.25 * _env(n, 0.01, 0.2, 1.0)
    return out / (np.abs(out).max() + 1e-6) * 0.45


def trilha_sfx(cenas: list[dict], duracao: float, ganho_db: float = -16.0) -> np.ndarray:
    n = int(duracao * SR_SFX) + SR_SFX
    trilha = np.zeros(n, np.float32)
    eventos = []
    for c in cenas:
        for b in c["blocos"]:
            if b.get("som"):
                eventos.append((b["inicio"], b["som"], b.get("anim", "")))
    eventos.sort()
    ultimo = -1.0
    usados = {"whoosh": 0, "impacto": 0, "vidro": 0}
    for t0, tipo, anim in eventos:
        if t0 - ultimo < 0.26 and tipo == "whoosh":
            continue  # não empilha sons de linhas pequenas
        if t0 - ultimo < 0.12:
            continue
        if tipo == "whoosh":
            s = sfx_whoosh(0.2 + 0.05 * (usados["whoosh"] % 2), 1 if "esq" in anim else -1) * 0.6
        elif tipo == "impacto":
            s = sfx_impacto()
        else:
            s = sfx_vidro()
        usados[tipo] += 1
        i = int(t0 * SR_SFX)
        trilha[i:i + len(s)] += s[: max(0, n - i)]
        ultimo = t0
    g = 10 ** (ganho_db / 20)
    return np.clip(trilha * g, -1, 1), usados


def mixar_audio(entrada: Path, trilha: np.ndarray, saida_wav: Path):
    """Decodifica o áudio original (sem mudar ganho), soma os SFX e grava WAV float."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(entrada), "-vn", "-f", "f32le", "-ac", "2", "-ar", str(SR_SFX), "-"],
                         capture_output=True, check=True).stdout
    voz = np.frombuffer(raw, np.float32).reshape(-1, 2).copy()
    n = len(voz)
    tr = trilha[:n]
    if len(tr) < n:
        tr = np.pad(tr, (0, n - len(tr)))
    mix = voz + tr[:, None]
    # ganho da voz intocado. Só os picos acima de 0,95 (que já clipavam no original) passam por
    # um soft-clip suave, para a soma com o SFX não estourar no codec.
    lim = 0.95
    acima = np.abs(mix) > lim
    if acima.any():
        exc = np.abs(mix[acima]) - lim
        mix[acima] = np.sign(mix[acima]) * (lim + (1 - lim) * np.tanh(exc / (1 - lim)))
    import soundfile as sf
    sf.write(str(saida_wav), mix, SR_SFX, subtype="FLOAT")
    return n / SR_SFX


# ══════════════════════════════════════════════════════════════════
# Render (vídeo PyAV, timestamps originais) + mux de áudio
# ══════════════════════════════════════════════════════════════════
def cenas_cor(cenas):
    return cenas[0].get("_cor", "#9FB8C8") if cenas else "#9FB8C8"


def renderizar_video(entrada: Path, saida_video: Path, cenas, orig, crf: int, rec: Recorte | None):
    import av
    W, H = orig["video"]["largura"], orig["video"]["altura"]
    n = orig["video"]["frames"]
    inp = av.open(str(entrada)); vin = inp.streams.video[0]; vin.thread_type = "AUTO"
    out = av.open(str(saida_video), "w")
    vout = out.add_stream("libx264", rate=None)
    vout.width, vout.height, vout.pix_fmt = W, H, "yuv420p"
    vout.time_base = vin.time_base; vout.codec_context.time_base = vin.time_base
    vout.options = {"crf": str(crf), "preset": "medium", "profile": "high", "level": "4.1"}
    R = Render(W, H, cenas, cor_vidro=cenas_cor(cenas))
    i = 0
    for packet in inp.demux([vin]):
        for fr in packet.decode():
            t = float(fr.pts * vin.time_base)
            img = fr.to_ndarray(format="rgb24")
            comp = R.frame(img, t, rec)
            nf = av.VideoFrame.from_ndarray(np.ascontiguousarray(comp), format="rgb24").reformat(format="yuv420p")
            nf.pts = fr.pts; nf.time_base = vin.time_base
            for p in vout.encode(nf): out.mux(p)
            i += 1
            if i % 50 == 0:
                print(f"   frame {i}/{n} ({100 * i / max(1, n):.0f}%) t={t:6.2f}s", end="\r", flush=True)
    for p in vout.encode(): out.mux(p)
    out.close(); inp.close()
    print(f"   {i} frames renderizados" + " " * 30)


def muxar(video_so: Path, wav: Path, saida: Path):
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(video_so), "-i", str(wav), "-map", "0:v:0", "-map", "1:a:0",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", str(saida)], check=True)


def main():
    ap = argparse.ArgumentParser(description="Tipografia cinética v2 (Poppins, vidro, paleta do vídeo, SFX).")
    ap.add_argument("entrada", type=Path)
    ap.add_argument("--saida", type=Path)
    ap.add_argument("--texto", type=Path)
    ap.add_argument("--destaque", default="")
    ap.add_argument("--cenas", type=Path)
    ap.add_argument("--modelo", default="small")
    ap.add_argument("--max-palavras", type=int, default=4)
    ap.add_argument("--crf", type=int, default=17)
    ap.add_argument("--so-cenas", action="store_true")
    ap.add_argument("--preview", type=str)
    ap.add_argument("--sem-sfx", action="store_true")
    ap.add_argument("--cor", type=str, help="força a cor de destaque (hex)")
    ap.add_argument("--remix", type=Path, help="reaproveita o vídeo já renderizado (copia o stream de vídeo) e refaz só o áudio")
    a = ap.parse_args()

    entrada = a.entrada
    saida_dir = a.saida.parent if a.saida else AQUI / "saida"
    saida_dir.mkdir(parents=True, exist_ok=True)
    saida = a.saida or saida_dir / f"{entrada.stem}_cinetica.mp4"
    base = saida_dir / saida.stem

    print("1) Registrando o original…")
    orig = L.probe(entrada); hash_o = L.hash_audio(entrada)
    W, H = orig["video"]["largura"], orig["video"]["altura"]
    print(f"   {W}x{H} · {orig['duracao_s']:.3f}s · {orig['video']['frames']} frames")
    base.with_suffix(".original.json").write_text(json.dumps({**orig, "hash_audio": hash_o}, indent=2, ensure_ascii=False), encoding="utf-8")

    if a.cenas:
        proj = json.loads(a.cenas.read_text(encoding="utf-8")); cenas = proj["cenas"]; preset = proj["preset"]
        print(f"2) Projeto revisado: {len(cenas)} cenas · destaque {preset['cor_destaque']}")
    else:
        print("2) Paleta do vídeo…")
        pal = extrair_paleta(entrada, orig["duracao_s"])
        cor = a.cor or pal["destaque"]
        print(f"   destaque {cor} (origem {pal['origem_destaque']}) · dominantes {[c['hex'] for c in pal['dominantes'][:6]]}")
        preset = {"cor_destaque": cor, "paleta": pal, "fonte_extra": "Poppins-ExtraBold.ttf", "fonte_black": "Poppins-Black.ttf",
                  "tracking": -0.04, "entrelinha": 0.84}
        print(f"3) Transcrevendo (whisper-{a.modelo})…")
        samples = L.carregar_audio_16k(entrada)
        trechos = L.transcrever(samples, a.modelo, "pt", verbose=False)
        if a.texto:
            trechos = L.alinhar_texto(trechos, a.texto.read_text(encoding="utf-8"))
        cards = L.montar_cards(trechos, a.max_palavras, 40)
        chaves = {L._norm(x) for x in a.destaque.split(",") if x.strip()}
        print("4) Posição da pessoa por frase…")
        rec = Recorte(fino=False)
        bboxes = []
        # mesma fusão de frases curtas que o layout fará: calcula bbox no meio de cada frase final
        tmp = layout(cards, preset, W, H, chaves, [None] * len(cards))
        for c in tmp:
            tm = (c["inicio"] + c["fim"]) / 2
            raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{tm:.3f}", "-i", str(entrada), "-frames:v", "1",
                                  "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
            img = np.frombuffer(raw, np.uint8).reshape(H, W, 3)
            bboxes.append(rec.bbox_rapido(img))
        print("5) Layout…")
        cenas = layout(cards, preset, W, H, chaves, bboxes)
        base.with_suffix(".transcricao.txt").write_text(
            "\n".join(f"{L._ts(c['inicio'])} → {L._ts(c['fim'])}  [{c['modelo']}{' 👤' if c['pessoa'] else ''}] {c['frase']}" for c in cenas), encoding="utf-8")
    proj_path = base.with_suffix(".cenas.json")
    proj_path.write_text(json.dumps({"preset": preset, "cenas": cenas}, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"   {len(cenas)} cenas · projeto em {proj_path}")
    if a.so_cenas:
        return

    if a.preview:
        R = Render(W, H, cenas, cor_vidro=preset['cor_destaque']); rec = Recorte(fino=True)
        for ts in [float(x) for x in a.preview.split(",")]:
            raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(ts), "-i", str(entrada), "-frames:v", "1",
                                  "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
            img = np.frombuffer(raw, np.uint8).reshape(H, W, 3)
            rec.anterior = None; rec._t_ultimo = None; rec.frame_ant = None
            p = saida_dir / f"{saida.stem}_preview_{ts:.2f}.png"
            Image.fromarray(R.frame(img, ts, rec)).save(p); print("   ", p)
        return

    for c in cenas: c["_cor"] = preset["cor_destaque"]
    video_so = base.with_suffix(".video.mp4")
    if a.remix:
        print("6) Reaproveitando o vídeo renderizado:", a.remix)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(a.remix), "-map", "0:v:0", "-c:v", "copy", str(video_so)], check=True)
    else:
        print("6) Render de vídeo (recorte fino + composição)…")
        renderizar_video(entrada, video_so, cenas, orig, a.crf, Recorte(fino=True))
    print("7) Áudio: voz original + efeitos sonoros…")
    if a.sem_sfx:
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(video_so), "-i", str(entrada), "-map", "0:v:0", "-map", "1:a:0",
                        "-c", "copy", "-movflags", "+faststart", str(saida)], check=True)
        usados = {}
    else:
        trilha, usados = trilha_sfx(cenas, orig["duracao_s"])
        wav = base.with_suffix(".mix.wav")
        mixar_audio(entrada, trilha, wav)
        muxar(video_so, wav, saida)
        print(f"   efeitos usados: {usados}")
    video_so.unlink(missing_ok=True)

    print("8) Conferindo…")
    novo = L.probe(saida)
    fps = orig["video"]["fps"] or 30
    msgs = []
    ok = True
    dd = abs(orig["duracao_s"] - novo["duracao_s"])
    msgs.append(f"duração: {orig['duracao_s']:.3f}s → {novo['duracao_s']:.3f}s (Δ {dd*1000:.0f} ms)")
    if dd > 1 / fps + 0.03: ok = False; msgs[-1] += " ❌"
    msgs.append(f"frames: {orig['video']['frames']} → {novo['video']['frames']}")
    if orig["video"]["frames"] != novo["video"]["frames"]: ok = False; msgs[-1] += " ❌"
    if orig["audio"] and novo["audio"]:
        da = abs(orig["audio"]["duracao_s"] - novo["audio"]["duracao_s"])
        msgs.append(f"áudio: {orig['audio']['duracao_s']:.3f}s → {novo['audio']['duracao_s']:.3f}s (Δ {da*1000:.0f} ms) · "
                    + ("voz original copiada" if a.sem_sfx else "voz original somada 1:1 + SFX a -16 dB, re-encodado AAC 256k"))
        if da > 0.06: ok = False; msgs[-1] += " ❌"
    rel = ["# Relatório — tipografia cinética v2", f"- entrada: `{entrada}`", f"- saída: `{saida}`",
           f"- destaque: `{preset['cor_destaque']}`", f"- efeitos sonoros: {usados}", ""] + [f"- {m}" for m in msgs]
    rel += ["", "✅ MONTAGEM PRESERVADA" if ok else "❌ ALGO MUDOU — NÃO PUBLICAR"]
    base.with_suffix(".relatorio.md").write_text("\n".join(rel), encoding="utf-8")
    for m in msgs: print("   " + m)
    print("   " + rel[-1]); print("→", saida)
    sys.exit(0 if ok else 2)


if __name__ == "__main__":
    main()
