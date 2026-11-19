"""Corta as fotos da paciente em faixas centradas no glúteo, como a referência A (a dentista) corta o sorriso:
a faixa do alto da abertura, o par de antes e depois da 1ª sessão, a foto única do antes da 2ª etapa e o
resultado em tela cheia. Lê assets/fotos/ (preparar_fotos.py) e escreve assets/fotos/faixas/ (fora do git).

Uso: python3 cortar_fotos.py   (na pasta do projeto)
"""
from pathlib import Path

from PIL import Image

P = Path(__file__).parent / "assets" / "fotos"
# (foto, centro x, centro y, largura em fração da foto, proporção largura/altura): o glúteo inteiro, de lado a lado
CORTES = {
    "banda-antes": ("antes-1a-etapa.jpg", 0.50, 0.57, 1.00, 1080 / 560),    # com o cós e a marca, como no par
    "par-antes": ("antes-1a-etapa.jpg", 0.50, 0.595, 0.86, 438 / 373),
    "par-depois": ("depois-1a-etapa.jpg", 0.47, 0.56, 0.74, 438 / 373),      # mais perto: o corpo é menor na foto
    "unica-antes2": ("antes-2a-etapa.jpg", 0.47, 0.585, 0.76, 780 / 503),
    "cheia-depois2": ("depois-2a-etapa.jpg", 0.50, 0.50, 1.00, 1080 / 1920),
}
(P / "faixas").mkdir(exist_ok=True)
for nome, (arq, cx, cy, fw, prop) in CORTES.items():
    im = Image.open(P / arq).convert("RGB")
    W, H = im.size
    w = fw * W
    h = w / prop
    if h > H:
        h, w = H, H * prop
    x0 = min(max(cx * W - w / 2, 0), W - w)
    y0 = min(max(cy * H - h / 2, 0), H - h)
    c = im.crop((round(x0), round(y0), round(x0 + w), round(y0 + h)))
    c.save(P / "faixas" / f"{nome}.jpg", quality=93)
    print(f"{nome}: {c.size[0]}×{c.size[1]} de {arq}")
