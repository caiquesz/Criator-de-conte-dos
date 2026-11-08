"""Remove a voz de fundo (criança) que aparece por cima de "capas de almofada" (~12,0–13,1 s).

Passos:
1. SepFormer (speechbrain/sepformer-whamr16k) separa o trecho 9,4–17,4 s em duas fontes
   a 16 kHz: a voz da apresentadora e a voz de fundo. Rodar antes, num venv com torch:
       python run_sep.py broll16k.wav <pasta> speechbrain/sepformer-whamr16k
2. Este script usa as duas fontes como máscara (Wiener) sobre o áudio ORIGINAL a 44,1 kHz,
   então a voz dela mantém a qualidade cheia, e aplica só na janela onde a voz de fundo aparece,
   com transição suave nas bordas.

Uso:
    python3 clean_voice.py <original_44k.wav> <src0.wav> <src1.wav> <saida.wav>
"""
import sys
import wave

import numpy as np
from scipy.signal import istft, resample_poly, stft
from scipy.ndimage import uniform_filter

SEG_START = 9.4        # início do trecho enviado ao SepFormer (s)
WIN = (11.85, 13.30)   # janela onde a voz de fundo aparece (s)
FADE = 0.06            # transição nas bordas da janela (s)
MASK_FLOOR = 0.04


def read_wav(path):
    w = wave.open(path)
    sr, ch, sw = w.getframerate(), w.getnchannels(), w.getsampwidth()
    raw = w.readframes(w.getnframes())
    dt = {2: np.int16, 4: np.int32}[sw]
    x = np.frombuffer(raw, dtype=dt).astype(np.float64) / (2 ** (8 * sw - 1))
    return x.reshape(-1, ch), sr


def write_wav(path, x, sr):
    y = np.clip(x, -1, 1)
    y = (y * 32767).astype(np.int16)
    w = wave.open(path, "wb")
    w.setnchannels(y.shape[1])
    w.setsampwidth(2)
    w.setframerate(sr)
    w.writeframes(y.tobytes())
    w.close()


orig, sr = read_wav(sys.argv[1])
s0, sr0 = read_wav(sys.argv[2])
s1, _ = read_wav(sys.argv[3])
mono = orig.mean(axis=1)

# Escala de cada fonte por mínimos quadrados contra a mistura (o SepFormer devolve escala arbitrária).
mix16 = resample_poly(mono, 160, 441)[int(SEG_START * sr0):][: len(s0)]
n = min(len(mix16), len(s0), len(s1))
A = np.stack([s0[:n, 0], s1[:n, 0]], 1)
coef = np.linalg.lstsq(A, mix16[:n], rcond=None)[0]
s0u = resample_poly(s0[:, 0] * coef[0], 441, 160)
s1u = resample_poly(s1[:, 0] * coef[1], 441, 160)

# Trecho de trabalho (com folga) no áudio original.
a0 = int((WIN[0] - 0.3) * sr)
a1 = int((WIN[1] + 0.3) * sr)
seg = mono[a0:a1]
o = a0 - int(SEG_START * sr)
v = s0u[o : o + len(seg)]
b = s1u[o : o + len(seg)]

nper, hop = 2048, 512
f, _, X = stft(seg, sr, nperseg=nper, noverlap=nper - hop)
_, _, V = stft(v, sr, nperseg=nper, noverlap=nper - hop)
_, _, B = stft(b, sr, nperseg=nper, noverlap=nper - hop)
pv, pb = np.abs(V) ** 2, np.abs(B) ** 2
pv = uniform_filter(pv, size=(3, 3))
pb = uniform_filter(pb, size=(3, 3))
M = pv / (pv + pb + 1e-12)
# Acima de 7,5 kHz o SepFormer (16 kHz) não tem informação: usa a média da faixa 4–7,5 kHz.
hi = f >= 7500
band = (f >= 4000) & (f < 7500)
M[hi, :] = M[band, :].mean(axis=0, keepdims=True)
M = np.clip(M, MASK_FLOOR, 1.0)
_, y = istft(X * M, sr, nperseg=nper, noverlap=nper - hop)
y = y[: len(seg)]

# Crossfade: original fora da janela, versão limpa dentro.
t = (np.arange(len(seg)) + a0) / sr
w = np.clip(np.minimum((t - WIN[0]) / FADE, (WIN[1] - t) / FADE), 0, 1)
w = 0.5 - 0.5 * np.cos(np.pi * w)
clean = mono.copy()
clean[a0:a1] = seg * (1 - w) + y * w

out = np.stack([clean, clean], 1)
write_wav(sys.argv[4], out, sr)
removed = mono[a0:a1] - clean[a0:a1]
db = lambda z: 20 * np.log10(np.sqrt(np.mean(z ** 2)) + 1e-12)
print(f"coef={coef}, janela {WIN}, removido {db(removed):.1f} dB vs trecho {db(mono[a0:a1]):.1f} dB")
