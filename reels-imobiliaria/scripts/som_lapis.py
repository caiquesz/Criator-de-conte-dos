"""Gera o som de lápis riscando (lapis.mp3) para a marcação com lápis na foto (Caso de paciente, 6ª versão).

Uso: python3 scripts/som_lapis.py PASTA_DO_PROJETO [DURACAO=0.8]
Escreve PASTA/assets/sfx/lapis.mp3 (os .mp3 de efeitos ficam fora do git: rode de novo num checkout novo).

Ruído numa faixa de ~1,8 a 7,5 kHz (o chiado do grafite), com a amplitude oscilando devagar e irregular e uns
grãos curtos, como o lápis prendendo no papel; entrada de 30 ms e saída de 90 ms. Sintetizado aqui, sem licença
de terceiros. O gerar.py já conhece "lapis" (duração 0,8 s, pico no começo).
"""
import subprocess
import sys
from pathlib import Path

import numpy as np

TAXA = 48000


def main():
    pasta = Path(sys.argv[1])
    dur = float(sys.argv[2]) if len(sys.argv) > 2 else 0.80
    rng = np.random.default_rng(11)
    n = int(TAXA * dur)
    F = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / TAXA)
    F *= np.exp(-0.5 * ((np.log(np.maximum(f, 1)) - np.log(3800)) / 0.55) ** 2)
    x = np.fft.irfft(F, n)
    k = np.exp(-0.5 * (np.arange(-1600, 1601) / 550.0) ** 2)
    k /= k.sum()
    lento = np.convolve(rng.standard_normal(n), k, "same")
    lento = (lento - lento.min()) / (lento.max() - lento.min())
    env = 0.45 + 0.55 * lento
    graos = np.convolve((rng.random(n) < 0.0009).astype(float), np.exp(-np.arange(240) / 40), "same")
    y = x * env * (1 + 0.8 * graos)
    a, r = int(0.03 * TAXA), int(0.09 * TAXA)
    y[:a] *= np.linspace(0, 1, a) ** 2
    y[-r:] *= np.linspace(1, 0, r) ** 2
    y = y / np.abs(y).max() * 10 ** (-3 / 20)
    est = np.stack([y, np.roll(y, 24) * 0.95], 1).astype(np.float32)
    saida = pasta / "assets" / "sfx" / "lapis.mp3"
    saida.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(TAXA), "-ac", "2", "-i", "-", "-c:a", "libmp3lame",
                    "-b:a", "192k", str(saida)], input=est.tobytes(), check=True)
    print(f"ok: {saida} ({dur:.2f} s)")


if __name__ == "__main__":
    main()
