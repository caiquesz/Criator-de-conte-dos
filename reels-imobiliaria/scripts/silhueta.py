"""Mede a silhueta da pessoa nos instantes pedidos, em coordenadas de 1080×1920.

Uso: python3 scripts/silhueta.py MASCARA.webm T1 T2 ... | --janelas plano.json

Para cada instante: topo da cabeça (y), faixa horizontal da cabeça (x),
linha dos ombros (y) e a caixa do corpo inteiro. Com --janelas, mede cada
grupo de legenda do plano no início, meio e fim e calcula quanto de cada
linha fica escondido atrás da pessoa (o ideal para uma palavra grande atrás
da cabeça é 30–55%).
"""

import json
import subprocess
import sys

import numpy as np

W, H = 135, 240          # resolução da análise
ESCALA = 1080 / W


def alfa(mascara, t):
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-c:v", "libvpx-vp9", "-ss", f"{t:.3f}", "-i", mascara,
         "-frames:v", "1", "-vf", f"alphaextract,scale={W}:{H}", "-f", "rawvideo",
         "-pix_fmt", "gray", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(H, W) > 128


def medir(m):
    linhas = np.where(m.any(1))[0]
    if len(linhas) < 3:
        return None
    topo = linhas[0]
    larguras = m.sum(1)
    # cabeça: do topo até onde a largura salta (ombros)
    ref = np.median(larguras[topo:topo + 6]) if larguras[topo:topo + 6].any() else 1
    ombro = next((y for y in range(topo + 3, linhas[-1]) if larguras[y] > 2.1 * max(ref, 1)), topo + 12)
    cab = m[topo:ombro]
    xs = np.where(cab.any(0))[0]
    corpo_x = np.where(m.any(0))[0]
    return {
        "cabeca_topo": int(topo * ESCALA), "ombros": int(ombro * ESCALA),
        "cabeca_x": [int(xs[0] * ESCALA), int((xs[-1] + 1) * ESCALA)] if len(xs) else None,
        "corpo": [int(corpo_x[0] * ESCALA), int(topo * ESCALA), int((corpo_x[-1] + 1) * ESCALA), int((linhas[-1] + 1) * ESCALA)],
    }


def cobertura(m, caixa):
    """Fração da caixa (x0, y0, x1, y1 em 1080×1920) coberta pela pessoa."""
    x0, y0, x1, y1 = (int(round(v / ESCALA)) for v in caixa)
    reg = m[max(0, y0):max(0, y1), max(0, x0):max(0, x1)]
    return float(reg.mean()) if reg.size else 0.0


def main():
    mascara = sys.argv[1]
    if sys.argv[2] == "--janelas":
        sys.path.insert(0, __file__.rsplit("/", 1)[0])
        from gerar import ESTILOS, tamanho_linha, largura_linha  # noqa: E402
        plano = json.load(open(sys.argv[3]))
        for g in plano["legendas"]:
            ini = min(p["s"] for l in g["linhas"] for p in l["palavras"])
            y = g["y"]
            caixas = []
            for li, l in enumerate(g["linhas"]):
                est = l.get("estilo", "fina")
                tam = tamanho_linha(l, plano)
                larg = largura_linha(" ".join(p["t"] for p in l["palavras"]), est, tam, plano)
                x0 = (1080 - larg) / 2 + l.get("dx", 0)
                caixas.append((li, est, (x0, y + 0.18 * tam, x0 + larg, y + 0.86 * tam)))
                y += tam * (1 + plano.get("entrelinha", -0.16))
            res = []
            for t in (ini, (ini + g["fim"]) / 2, g["fim"] - 0.1):
                m = alfa(mascara, t)
                res.append([round(cobertura(m, c), 2) for _, _, c in caixas])
            print(g["id"], f"{ini:.2f}-{g['fim']:.2f}", "cobertura por linha (início/meio/fim):", res)
        return
    for t in map(float, sys.argv[2:]):
        print(f"{t:7.2f}", json.dumps(medir(alfa(mascara, t))))


if __name__ == "__main__":
    main()
