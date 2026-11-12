"""Sintetiza o som de impacto da abertura do quadro da biomédica (assets/sfx/impacto.mp3).

Uso: python3 scripts/sfx_impacto.py PASTA/assets/sfx/impacto.mp3

Um "tum" grave de cinema: uma senoide que desce de ~130 Hz para 38 Hz, um estalo de ruído
filtrado e uma cauda curta. Feito aqui, sem direitos de terceiros (os mp3 de efeitos ficam fora
do git; este se refaz com este script).
"""

import subprocess
import sys

import numpy as np

R = 48000


def passa_baixa(x, fc):
    a = np.exp(-2 * np.pi * fc / R)
    y, acc = np.empty_like(x), 0.0
    for i, v in enumerate(x):
        acc = (1 - a) * v + a * acc
        y[i] = acc
    return y


def main():
    t = np.arange(int(1.4 * R)) / R
    ruido = np.random.default_rng(7).standard_normal(len(t))
    ataque = np.clip(t / 0.003, 0, 1)
    sub = np.sin(2 * np.pi * np.cumsum(38 + 95 * np.exp(-t / 0.07)) / R) * np.exp(-t / 0.42) * ataque
    x = sub + passa_baixa(ruido, 1800) * np.exp(-t / 0.05) * ataque * 2.2 + passa_baixa(ruido, 600) * np.exp(-t / 0.55) * 0.5
    x = x / np.abs(x).max() * 10 ** (-4 / 20)
    st = np.stack([x, x], 1).astype(np.float32)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(R), "-ac", "2", "-i", "-",
                    "-c:a", "libmp3lame", "-q:a", "2", sys.argv[1]], input=st.tobytes(), check=True)
    print("ok:", sys.argv[1])


if __name__ == "__main__":
    main()
