"""Trilha de efeitos do motion (sincronizada com a timeline do index.html).
uso: python3 audio.py <saida.wav>"""
import os, subprocess, sys, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SR, DUR = 48000, 12.0


ev = []
def add(name, t, vol, align=0.0):
    ev.append((name, t - align, vol))

add("partida", 0.02, 0.55)     # motor ligando enquanto a foto do volante sobe
add("swish", 0.40, 0.3, align=0.41)
add("pop", 0.38, 0.7)          # ícone da CNH
add("click", 0.62, 0.5); add("click", 0.79, 0.5)
add("pop_soft", 0.96, 0.6)     # Dia da
add("pop", 1.13, 0.8)          # Autoescola!
add("swish", 1.15, 0.18, align=0.41)   # pontinhos
add("click", 1.72, 0.55)       # tarja com o logo
add("swish", 5.92, 0.25, align=0.41)
add("click", 6.27, 0.5); add("click", 6.44, 0.5)
add("pop_soft", 6.61, 0.6)     # sonhos com a
add("pop", 6.78, 0.8)          # gente!
add("buzina", 10.90, 0.75)     # bi-bi!
add("pop", 10.92, 0.5)

N = int(SR * DUR)
mix = np.zeros((N, 2), np.float32)
cache = {}
for name, t, vol in ev:
    if name not in cache:
        b = subprocess.run(["ffmpeg", "-v", "error", "-i", os.path.join(HERE, "sfx", name + ".wav"), "-ac", "2", "-ar", str(SR),
                            "-f", "f32le", "-"], capture_output=True, check=True).stdout
        cache[name] = np.frombuffer(b, np.float32).reshape(-1, 2)
    s = cache[name]; i0 = int(round(t * SR)); a0 = max(0, -i0); i0 = max(0, i0)
    n = min(len(s) - a0, N - i0)
    if n > 0:
        mix[i0:i0 + n] += s[a0:a0 + n] * vol * 0.6
peak = np.abs(mix).max()
if peak > 0.89:
    mix *= 0.89 / peak
fo = int(0.15 * SR); mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
with wave.open(sys.argv[1], "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())
print("ok", sys.argv[1], f"{len(ev)} efeitos, pico {peak:.2f}")
