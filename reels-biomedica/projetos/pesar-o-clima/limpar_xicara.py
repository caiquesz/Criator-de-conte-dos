"""Tira o barulho da xícara batendo no pires (14–20 s) do áudio do "Posso pesar o clima?" sem mexer na voz.

Uso: python3 limpar_xicara.py   (na pasta do projeto, depois do montar_video.py; lê assets/video/voz.wav e escreve
     assets/video/voz-sem-xicara.wav, que o plano usa como "video_original": a mixagem lê a voz dali)

6ª versão, 18/11: "dá para remover o barulho da xícara batendo?" e, depois, "tá entre o segundo 14 e o 20; depois
disso é a batida da música". No vídeo, a mão dela está na xícara de 14,0 a 15,4 s e de 17,8 a 19,9 s (pega, levanta
e apoia de novo no pires). No áudio, cada batida é um ataque seco seguido de notas finas soando (a xícara de metal):
~4,5, ~6,9, ~7,3–7,6, ~10,6 e ~11,8 kHz, as mesmas em todas as batidas; em 18,15–18,33 s ela chacoalha (uma série de
estalinhos). Os estalos regulares a cada 0,25/0,5 s a partir dos 16 s são o chimbal da música do vídeo: ficam.

Como tira, só dentro das janelas abaixo:
  1. as notas: com análise fina em frequência (janela de 85 ms), as notas da própria xícara (lista NOTAS, ±45 Hz)
     e qualquer outro pico estreito entre 3 e 13 kHz que fique mais de 6 dB acima do espectro em volta (±260 Hz)
     descem até esse nível. A voz, nessa faixa, é chiado (sem picos estreitos parados), então não muda; abaixo de
     3 kHz nada é tocado;
  2. os estalos: com análise fina no tempo (janela de 5 ms), em cada estalo (ESTALOS) e na série de estalinhos,
     cada faixa acima de 2 kHz fica limitada ao que tinha nos 30 ms em volta (mediana): some o que dura poucos
     milissegundos, fica o que dura mais (as consoantes, o chiado da voz).
Transições de 10 ms nas bordas das janelas; fora delas o áudio sai idêntico ao original, amostra por amostra.
Primeira tentativa (descartada): eu tinha procurado batidas no vídeo todo e marcado 7,45, 15,47 e 33,25 s, mas nas
duas últimas havia voz (com a altura da voz dela, ~210–260 Hz) junto. Ela indicou o trecho certo.
"""
import subprocess
import sys
from pathlib import Path

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

AQUI = Path(__file__).parent
sys.path.insert(0, str(AQUI.parent.parent.parent / "reels-imobiliaria" / "scripts"))
from mixar import TAXA, pcm  # noqa: E402

# janelas das notas (início, fim) e estalos (início, fim), medidos em 14–20,5 s
JANELAS = [(14.895, 15.75), (18.055, 18.65), (18.970, 19.60), (19.845, 20.40)]
ESTALOS = [(14.922, 14.950), (15.128, 15.142), (15.466, 15.512), (18.061, 18.095), (18.977, 19.028), (19.850, 19.902),
           (18.15, 18.34)]                                   # o último: a xícara chacoalhando no pires
# as notas da xícara (média de cada janela, resolução de 6 Hz; as que também aparecem sem a xícara, 16,9–17,8 e
# 20,6–21,4 s, ficaram de fora): 4,55 kHz é a principal (11–16 dB acima do espectro em volta)
NOTAS = [3638, 3714, 4007, 4085, 4420, 4505, 4552, 5583, 6873, 7171, 7488, 7535, 10593, 10634, 10790, 10940, 11040,
         11085, 11390]
RAMPA = 0.010


def stft(y, n, h):
    w = np.hanning(n)
    q = 1 + (len(y) - n) // h
    return np.array([np.fft.rfft(y[i * h:i * h + n] * w) for i in range(q)])


def istft(Z, n, h, tam):
    w = np.hanning(n)
    y, soma = np.zeros(tam), np.zeros(tam)
    for i, z in enumerate(Z):
        y[i * h:i * h + n] += np.fft.irfft(z, n) * w
        soma[i * h:i * h + n] += w ** 2
    return y / np.maximum(soma, 1e-9)


def tirar_notas(y, ini, jan):
    """As notas da xícara (±45 Hz) e qualquer pico estreito entre 3 e 13 kHz descem ao nível do espectro em volta
    (só nas janelas)."""
    n, h = 4096, 512
    Z = stft(y, n, h)
    A = np.abs(Z)
    f = np.fft.rfftfreq(n, 1 / TAXA)
    t = ini + (np.arange(len(Z)) * h + n / 2) / TAXA
    viz = 22                                                   # ±22 bins ≈ ±260 Hz
    Ap = np.pad(A, ((0, 0), (viz, viz)), mode="edge")
    fundo = np.median(sliding_window_view(Ap, 2 * viz + 1, axis=1), axis=2)
    dentro = np.zeros(len(Z), bool)
    for a, b in jan:
        dentro |= (t >= a) & (t <= b)
    banda = (f >= 3000) & (f <= 13000)
    nota = np.zeros(len(f), bool)
    for fq in NOTAS:
        nota |= np.abs(f - fq) <= 45
    pico = ((A > fundo * 10 ** (6 / 20)) & banda[None, :] | (A > fundo) & nota[None, :]) & dentro[:, None]
    nova = np.where(pico, fundo, A)
    return istft(nova * np.exp(1j * np.angle(Z)), n, h, len(y))


def tirar_estalos(y, ini, trechos):
    """Acima de 2 kHz, nos trechos, cada bin fica limitado à mediana dos ±25 ms em volta."""
    n, h = 256, 32
    Z = stft(y, n, h)
    A = np.abs(Z)
    f = np.fft.rfftfreq(n, 1 / TAXA)
    t = ini + (np.arange(len(Z)) * h + n / 2) / TAXA
    m = int(round(0.030 * TAXA / h))
    Ap = np.pad(A, ((m, m), (0, 0)), mode="edge")
    med = np.median(sliding_window_view(Ap, 2 * m + 1, axis=0), axis=2)
    dentro = np.zeros(len(Z), bool)
    for a, b in trechos:
        dentro |= (t >= a) & (t <= b)
    alvo = dentro[:, None] & (f >= 2000)[None, :]
    nova = np.where(alvo, np.minimum(A, med), A)
    return istft(nova * np.exp(1j * np.angle(Z)), n, h, len(y))


def mascara(tt, janelas):
    m = np.zeros(len(tt))
    for a, b in janelas:
        sobe = np.clip((tt - (a - RAMPA)) / RAMPA, 0, 1)
        desce = np.clip(((b + RAMPA) - tt) / RAMPA, 0, 1)
        m = np.maximum(m, (0.5 - 0.5 * np.cos(np.pi * sobe)) * (0.5 - 0.5 * np.cos(np.pi * desce)))
    return m


def main():
    orig = pcm(AQUI / "assets" / "video" / "voz.wav")
    ini, fim = 14.6, 20.7
    a, b = int(ini * TAXA), int(fim * TAXA)
    tt = np.arange(a, b) / TAXA
    estalos = ESTALOS
    m = mascara(tt, JANELAS)
    saida = orig.copy()
    for c in range(orig.shape[1]):
        y = orig[a:b, c].astype(np.float64)
        y = tirar_notas(y, ini, JANELAS)
        y = tirar_estalos(y, ini, estalos)
        saida[a:b, c] = (orig[a:b, c] * (1 - m) + y * m).astype(orig.dtype)
    fora = np.ones(len(orig), bool)
    fora[a:b] = m == 0
    assert np.array_equal(saida[fora], orig[fora]), "fora das janelas o áudio tem que ficar idêntico"
    arq = AQUI / "assets" / "video" / "voz-sem-xicara.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(TAXA), "-ac", str(orig.shape[1]), "-i", "-",
                    "-c:a", "pcm_f32le", str(arq)], input=saida.astype(np.float32).tobytes(), check=True)
    print(f"ok: {arq.name}: janelas {JANELAS}, {len(ESTALOS)} estalos; "
          f"{fora.mean() * 100:.2f}% do áudio idêntico ao original, amostra por amostra")


if __name__ == "__main__":
    main()
