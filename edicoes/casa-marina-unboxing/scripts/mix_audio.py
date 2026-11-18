"""Build the reel's audio: original camera sound (optional) + pop/click SFX at cue times.

Usage: python3 mix_audio.py cues.json pop.ogg click.ogg out_with_ambience.wav out_sfx_only.wav
"""
import json
import subprocess
import sys

import numpy as np

SR = 44100
SRC = sys.argv[6] if len(sys.argv) > 6 else None

def load(path, channels=2):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", str(channels), "-ar", str(SR),
                          "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, channels).copy()

def save(path, x):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
                          "-c:a", "pcm_s24le", path], stdin=subprocess.PIPE)
    p.stdin.write(np.ascontiguousarray(x, np.float32).tobytes())
    p.stdin.close()
    p.wait()

def prep(x, peak_db):
    x = x - x.mean(0)                    # remove DC
    # trim leading silence so the transient lands exactly on the cue
    env = np.abs(x).max(1)
    start = int(np.argmax(env > env.max() * 0.02))
    x = x[max(start - 20, 0):]
    # short fade-out to avoid clicks at the tail
    n = min(len(x), int(0.01 * SR))
    x[-n:] *= np.linspace(1, 0, n)[:, None]
    return x / np.abs(x).max() * 10 ** (peak_db / 20)

cues = json.load(open(sys.argv[1]))
pop = prep(load(sys.argv[2]), -9.0)
click = prep(load(sys.argv[3]), -8.0)
orig = load(SRC)
n = len(orig)
sfx = np.zeros_like(orig)
for t, kind in cues:
    s = pop if kind == "pop" else click
    i = int(round(t * SR))
    j = min(i + len(s), n)
    sfx[i:j] += s[: j - i]

mix = orig + sfx
for name, x in ((sys.argv[4], mix), (sys.argv[5], sfx)):
    pk = np.abs(x).max()
    if pk > 0.98:
        x = x / pk * 0.98
    save(name, x)
    print(name, "peak dBFS", round(20 * np.log10(np.abs(x).max() + 1e-12), 2), "len s", round(len(x) / SR, 3))
