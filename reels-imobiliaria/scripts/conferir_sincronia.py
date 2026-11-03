"""Confere se o vídeo estabilizado continua alinhado ao original (e, portanto, à voz).

Uso: python3 scripts/conferir_sincronia.py ORIGINAL.mp4 ESTABILIZADO.mp4 FPS

A cada 5 s, acha o deslocamento (em quadros) que melhor encaixa o ritmo de mudança
de imagem do estabilizado no original. Tudo em +0 quadros = imagem e voz juntas.
"""
import subprocess, sys, numpy as np
W, H = 48, 86
def frames(f):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", f, "-vf", f"scale={W}:{H},format=gray", "-f", "rawvideo", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, H, W).astype(np.float32)
a, b = frames(sys.argv[1]), frames(sys.argv[2])
fps = float(sys.argv[3])
print("quadros", len(a), len(b))
da = np.abs(np.diff(a, axis=0)).mean((1, 2)); db = np.abs(np.diff(b, axis=0)).mean((1, 2))
n = min(len(da), len(db))
for ini in range(0, n - 60, int(fps * 5)):
    seg = da[ini:ini + 60]
    melhor = min(range(-4, 5), key=lambda k: np.inf if ini + k < 0 or ini + k + 60 > len(db) else
                 np.abs(db[ini + k:ini + k + 60] - seg).mean())
    print(f"{ini / fps:6.1f}s: estabilizado {melhor:+d} quadros")
