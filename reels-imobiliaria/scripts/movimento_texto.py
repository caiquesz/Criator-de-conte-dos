"""Mede como um texto branco entra num vídeo de referência: deslocamento vertical e opacidade aparente, quadro a quadro.

Uso: python3 scripts/movimento_texto.py VIDEO T_PARADO INI DUR [Y0 Y1 [X0 X1]]
  T_PARADO   um instante em que o texto já está parado e opaco (vira o molde)
  INI, DUR   o trecho a medir (s), normalmente a entrada ou a saída
  Y0 Y1 X0 X1  a região do texto no quadro 1080×1920 (padrão: y 950–1300, x 120–960)

Para cada quadro imprime o deslocamento (dy, em px; negativo = acima do lugar final) que melhor encaixa o molde e o
"sinal" (1 = tão visível quanto no quadro parado; serve de opacidade aproximada). Funciona com o texto ainda
semitransparente e sobre fundo claro, porque compara o detalhe fino (o quadro menos o borrado) e não o brilho.

Como ler a curva: se a raiz quadrada do dy cai a mesma quantidade a cada quadro, é power1.out do GSAP (quadrática);
a duração é o número de quadros até zero. Criado no "Posso pesar o clima?" (biomédica, 3ª versão), quando a leitura a
olho de quadros soltos tinha dado o título "descendo 70 px em 0,32 s" e a medida deu 400 px em 0,5 s.
"""
import subprocess
import sys

import numpy as np


def quadros(video, t, d=None):
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{t}", "-i", video] + (["-t", f"{d}"] if d else ["-frames:v", "1"]) + \
          ["-vf", "scale=1080:1920", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    saida = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(saida, np.uint8).reshape(-1, 1920, 1080, 3).astype(np.float32)


def borrado(img, k=6):
    c = np.cumsum(np.cumsum(np.pad(img, ((k + 1, k), (k + 1, k)), mode="edge"), 0), 1)
    return (c[2 * k + 1:, 2 * k + 1:] - c[:-2 * k - 1, 2 * k + 1:] - c[2 * k + 1:, :-2 * k - 1]
            + c[:-2 * k - 1, :-2 * k - 1]) / (2 * k + 1) ** 2


def detalhe(a):
    y = a.mean(2)
    return y - borrado(y)


def main():
    video, t_parado, ini, dur = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4])
    y0, y1 = (int(sys.argv[5]), int(sys.argv[6])) if len(sys.argv) > 6 else (950, 1300)
    x0, x1 = (int(sys.argv[7]), int(sys.argv[8])) if len(sys.argv) > 8 else (120, 960)
    parado = quadros(video, t_parado)[0]
    molde = (parado.min(2) > 236) & ((parado.max(2) - parado.min(2)) < 12)     # branco puro: o texto
    molde[:y0] = False
    molde[y1:] = False
    molde[:, :x0] = False
    molde[:, x1:] = False
    ys, xs = np.nonzero(molde)
    if len(ys) < 50:
        raise SystemExit("o molde saiu com poucos pixels: ajuste a região ou o instante parado")
    print(f"molde: {len(ys)} px, y {ys.min()}-{ys.max()}")
    base = detalhe(parado)[ys, xs].mean()
    for i, a in enumerate(quadros(video, ini, dur)):
        h = detalhe(a)
        sinal, dy = max((h[np.clip(ys + d, 0, 1919), xs].mean(), d) for d in range(-520, 300))
        print(f"{ini + i / 30:7.3f}  dy {dy:+5d}  sinal {sinal / base:5.2f}")


if __name__ == "__main__":
    main()
