"""Iguala o timbre da frase que foi gravada à parte ("a depressão lateral que chamamos de hip dips") ao resto do vídeo.

Uso: python3 igualar_voz.py   (na pasta do projeto; escreve assets/video/voz-igualada.wav, que o plano usa como
     "video_original": a mixagem lê a voz dali)

7ª versão, 17/11: "dá uma alteração no tom de voz da Nádia: a gente gravou o vídeo, e nessa parte gravou uma
gravação de áudio dela; por isso o tom ficou diferente". A frase em cima da foto da paciente (31,0–33,66 s) é de
outra gravação, de celular perto da boca. Medido só nas vogais, contra trechos de 2,6 s da fala normal:
  - agudos bem mais fortes: +6 dB em 3–5 kHz e +15 a +22 dB em 6–8 kHz (z de 3 a 12, fora da variação normal);
  - um pouco mais de grave em 160–200 Hz (+5 a +7 dB);
  - 2,3 dB mais alta que as frases vizinhas;
  - a altura da voz é a mesma (F0 ~200 Hz, como "havia algo pedindo atenção" logo antes, 198 Hz): nada de mudar o
    tom, que é o que soaria artificial.
A correção é um EQ de fase linear (~90% da diferença medida; com 65% a frase ainda ficava mais brilhante que o resto)
e o volume igualado ao das frases vizinhas, só dentro da frase, com transições de 20 ms nas pausas das emendas. O
resto do áudio sai idêntico ao original (amostra por amostra).
"""
import subprocess
import sys
from pathlib import Path

import numpy as np

AQUI = Path(__file__).parent
sys.path.insert(0, str(AQUI.parent.parent.parent / "reels-imobiliaria" / "scripts"))
from mixar import TAXA, pcm  # noqa: E402

TRECHO = (31.01, 33.66)          # as emendas da gravação à parte (pausas medidas no áudio)
RAMPA = 0.020
# correção em dB (centro da banda em Hz: ganho), ~90% da diferença medida nas vogais
CURVA = [(60, 0), (120, 0), (160, -3.5), (200, -4.5), (260, -1.0), (400, -2.0), (600, 0), (1200, +1.5), (2400, 0),
         (3000, -3.5), (3800, -5.5), (4800, -6.0), (6000, -10.0), (7600, -13.0), (9500, -12.0), (12000, -10.0),
         (16000, -10.0), (24000, -10.0)]
VIZINHOS = [(28.0, 31.0), (33.70, 36.6)]


def fir(curva, n=8192):
    """FIR de fase linear com a resposta da curva (interpolada no log da frequência)."""
    f = np.fft.rfftfreq(n, 1 / TAXA)
    fc, g = np.array([c for c, _ in curva], float), np.array([v for _, v in curva], float)
    ganho = 10 ** (np.interp(np.log(np.maximum(f, 1)), np.log(fc), g) / 20)
    h = np.fft.irfft(ganho, n)
    h = np.roll(h, n // 2) * np.hanning(n)
    return h


def nivel(x, a, b):
    J = int(0.05 * TAXA)
    r = np.array([np.sqrt((x[i:i + J] ** 2).mean()) for i in range(int(a * TAXA), int(b * TAXA) - J, J)])
    return 20 * np.log10(np.percentile(r, 80))


def main():
    orig = pcm(AQUI / "assets" / "video" / "original.mov")           # (amostras, 2), 48 kHz
    h = fir(CURVA)
    atraso = len(h) // 2
    filt = np.empty_like(orig)
    nfft = 1 << int(np.ceil(np.log2(len(orig) + len(h))))
    H = np.fft.rfft(h, nfft)
    for c in range(2):
        y = np.fft.irfft(np.fft.rfft(orig[:, c], nfft) * H, nfft)
        filt[:, c] = y[atraso:atraso + len(orig)]
    mono_o, mono_f = orig.mean(1), filt.mean(1)
    viz = np.mean([nivel(mono_o, a, b) for a, b in VIZINHOS])
    ganho_db = float(np.clip(viz - nivel(mono_f, *TRECHO), -4, 2))
    filt *= 10 ** (ganho_db / 20)
    # máscara: 1 dentro da frase, 0 fora, com rampas de cosseno de 20 ms centradas nas emendas
    t = np.arange(len(orig)) / TAXA
    def rampa(c):
        return np.clip((t - (c - RAMPA / 2)) / RAMPA, 0, 1)
    m = (0.5 - 0.5 * np.cos(np.pi * rampa(TRECHO[0]))) * (0.5 + 0.5 * np.cos(np.pi * rampa(TRECHO[1])))
    saida = orig * (1 - m[:, None]) + filt * m[:, None]
    fora = m == 0
    assert np.array_equal(saida[fora], orig[fora]), "fora da frase o áudio tem que ficar idêntico"
    arq = AQUI / "assets" / "video" / "voz-igualada.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(TAXA), "-ac", "2", "-i", "-", "-c:a", "pcm_f32le",
                    str(arq)], input=saida.astype(np.float32).tobytes(), check=True)
    print(f"ok: {arq.name}: frase {TRECHO[0]}–{TRECHO[1]} s com EQ e {ganho_db:+.1f} dB "
          f"(vizinhas {viz:.1f} dB, frase depois do EQ {nivel(mono_f, *TRECHO):.1f} dB); o resto idêntico ao original")


if __name__ == "__main__":
    main()
