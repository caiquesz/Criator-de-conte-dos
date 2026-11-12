"""Sintetiza os efeitos sonoros da abertura do quadro da biomédica (assets/sfx/).

Uso: python3 scripts/sfx_sintetizar.py brilho|impacto PASTA/assets/sfx/NOME.mp3

- brilho: um brilho delicado, de caixinha de música (quatro notas agudas em arpejo rápido, com
  um sopro de ar por baixo). É o som da abertura delicada que a cliente pediu.
- impacto: um "tum" grave de cinema (a primeira abertura, que ela achou pesada).

Feitos aqui, sem direitos de terceiros (os mp3 de efeitos ficam fora do git; estes se refazem
com este script).
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


def impacto():
    t = np.arange(int(1.4 * R)) / R
    ruido = np.random.default_rng(7).standard_normal(len(t))
    ataque = np.clip(t / 0.003, 0, 1)
    sub = np.sin(2 * np.pi * np.cumsum(38 + 95 * np.exp(-t / 0.07)) / R) * np.exp(-t / 0.42) * ataque
    x = sub + passa_baixa(ruido, 1800) * np.exp(-t / 0.05) * ataque * 2.2 + passa_baixa(ruido, 600) * np.exp(-t / 0.55) * 0.5
    return np.stack([x, x], 1), -4


def brilho():
    t = np.arange(int(1.8 * R)) / R
    esq, dir_ = np.zeros(len(t)), np.zeros(len(t))
    notas = [1567.98, 2093.0, 2637.02, 3135.96]           # sol, dó, mi, sol: um acorde claro, sem tensão
    for k, f in enumerate(notas):
        t0 = 0.055 * k
        u = np.clip(t - t0, 0, None)
        env = np.where(t >= t0, np.clip(u / 0.004, 0, 1) * np.exp(-u / 0.55), 0)
        som = (np.sin(2 * np.pi * f * u) + 0.18 * np.sin(2 * np.pi * f * 2.76 * u) * np.exp(-u / 0.12)) * env
        pan = 0.35 + 0.1 * k                              # as notas abrem da esquerda para a direita
        esq += som * (1 - pan)
        dir_ += som * pan
    ruido = np.random.default_rng(3).standard_normal(len(t))
    ar = (ruido - passa_baixa(ruido, 5000)) * np.sin(np.pi * np.clip(t / 0.9, 0, 1)) ** 2 * 0.05
    return np.stack([esq + ar, dir_ + ar], 1), -7


def main():
    nome, destino = sys.argv[1], sys.argv[2]
    x, pico_db = {"brilho": brilho, "impacto": impacto}[nome]()
    x = x / np.abs(x).max() * 10 ** (pico_db / 20)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(R), "-ac", "2", "-i", "-",
                    "-c:a", "libmp3lame", "-q:a", "2", destino], input=x.astype(np.float32).tobytes(), check=True)
    print("ok:", destino)


if __name__ == "__main__":
    main()
