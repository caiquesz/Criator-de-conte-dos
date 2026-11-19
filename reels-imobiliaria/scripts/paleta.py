"""Extrai a paleta de cores de um vídeo e sugere a cor de destaque das legendas.

Uso: python3 scripts/paleta.py VIDEO [--saida paleta.json] [--amostra amostra.png]

Amostra 1 quadro por segundo, agrupa as cores (k-means) e escolhe como destaque
a cor mais presente entre as que têm saturação de verdade (madeira, céu, piscina,
LED...). O destaque é clareado/saturado para ficar legível como texto sobre o vídeo.
"""

import argparse
import colorsys
import json
import subprocess

import numpy as np
from PIL import Image, ImageDraw


def quadros(video, w=96, h=170):
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", video, "-vf", f"fps=1,scale={w}:{h}",
         "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
        capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, 3).astype(np.float32)


def kmeans(px, k=10, iters=25, seed=7):
    rng = np.random.default_rng(seed)
    centros = px[rng.choice(len(px), k, replace=False)]
    for _ in range(iters):
        d = ((px[:, None, :] - centros[None]) ** 2).sum(-1)
        rotulo = d.argmin(1)
        for i in range(k):
            sel = px[rotulo == i]
            if len(sel):
                centros[i] = sel.mean(0)
    contagem = np.bincount(rotulo, minlength=k) / len(px)
    return centros, contagem


def hexa(rgb):
    return "#%02X%02X%02X" % tuple(int(round(c)) for c in rgb)


def legivel(rgb):
    """Leva a cor para uma faixa que lê bem como texto sobre vídeo."""
    h, l, s = colorsys.rgb_to_hls(*(c / 255 for c in rgb))
    l = min(max(l, 0.62), 0.74)
    s = min(max(s, 0.55), 0.85)
    return [c * 255 for c in colorsys.hls_to_rgb(h, l, s)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--saida", default="paleta.json")
    ap.add_argument("--amostra", default=None)
    a = ap.parse_args()

    px = quadros(a.video)
    centros, peso = kmeans(px)
    cores = []
    for c, p in sorted(zip(centros, peso), key=lambda t: -t[1]):
        h, l, s = colorsys.rgb_to_hls(*(float(v) / 255 for v in c))
        cores.append({"hex": hexa(c), "peso": round(float(p), 3),
                      "matiz": round(h * 360), "sat": round(s, 2), "luz": round(l, 2)})

    # agrupa as cores com alguma saturação em famílias de matiz (30°) e soma a
    # presença de cada família: a que domina o vídeo dá a cor de destaque
    familias = {}
    for c in cores:
        if c["sat"] < 0.10 or not 0.12 <= c["luz"] <= 0.9:
            continue
        familias.setdefault(c["matiz"] // 30, []).append(c)
    ordem = sorted(familias.values(),
                   key=lambda fam: -sum(c["peso"] * (0.4 + c["sat"]) for c in fam))
    destaques = []
    for fam in ordem:
        # representante: a mais viva da família (saturação x luz)
        c = max(fam, key=lambda c: c["sat"] * (0.3 + c["luz"]))
        rgb = [int(c["hex"][i:i + 2], 16) for i in (1, 3, 5)]
        destaques.append({"hex": hexa(legivel(rgb)), "origem": c["hex"], "matiz": c["matiz"],
                          "presenca": round(sum(x["peso"] for x in fam), 3)})

    resultado = {"paleta": cores, "destaques_sugeridos": destaques[:3],
                 "destaque": destaques[0]["hex"] if destaques else "#E8B07A",
                 "texto": "#FFFFFF"}
    json.dump(resultado, open(a.saida, "w"), ensure_ascii=False, indent=2)
    print(json.dumps(resultado, ensure_ascii=False, indent=2))

    if a.amostra:
        img = Image.new("RGB", (100 * len(cores), 220), "white")
        dr = ImageDraw.Draw(img)
        for i, c in enumerate(cores):
            dr.rectangle([i * 100, 0, i * 100 + 99, 120], fill=c["hex"])
            dr.text((i * 100 + 6, 125), f'{c["hex"]}\n{c["peso"]:.0%}', fill="black")
        for i, d in enumerate(destaques[:3]):
            dr.rectangle([i * 160, 165, i * 160 + 150, 215], fill=d["hex"])
        img.save(a.amostra)


if __name__ == "__main__":
    main()
