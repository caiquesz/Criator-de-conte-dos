"""Build the final audio: original voice spliced per the EDL (no EQ, no compression,
no loudness change; only 5 ms fades at cut points to avoid clicks) + a few subtle
synthesized SFX.

usage: audio.py SCRATCH OUT.wav [--no-sfx]
"""
import sys, os, json, subprocess
import numpy as np
from scipy.signal import butter, sosfilt

S = sys.argv[1]; OUT = sys.argv[2]; NOSFX = "--no-sfx" in sys.argv
sys.path.insert(0, S + "/scripts")
import edl

SR = 44100
raw = S + "/work/voice_stereo.f32"
if not os.path.exists(raw):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", S + "/src/raw.mov", "-vn", "-f", "f32le",
                    "-acodec", "pcm_f32le", "-ar", str(SR), "-ac", "2", raw], check=True)
src = np.fromfile(raw, dtype=np.float32).reshape(-1, 2)

segs = edl.build()
total = int(round(segs[-1]["out_end"] * SR))
out = np.zeros((total, 2), np.float32)
FADE = int(0.005 * SR)
for s in segs:
    a = int(round(s["src_in"] * SR)); b = int(round(s["src_out"] * SR))
    chunk = src[a:b].copy()
    n = len(chunk)
    ramp = np.linspace(0, 1, FADE, dtype=np.float32)[:, None]
    chunk[:FADE] *= ramp
    fo = int(s.get("fade_out", 0.005) * SR)
    chunk[n - fo:] *= np.linspace(1, 0, fo, dtype=np.float32)[:, None]
    o = int(round(s["out_start"] * SR))
    m = min(n, total - o)
    out[o:o + m] += chunk[:m]

voice_peak = float(np.abs(out).max())

# ------------------------------------------------------------------ SFX
rng = np.random.default_rng(7)


def db(x):
    return 10 ** (x / 20)


def norm(x, peak_db):
    return x / (np.abs(x).max() + 1e-12) * db(peak_db)


def whoosh(dur=0.42):
    n = int(dur * SR); t = np.arange(n) / SR
    noise = rng.standard_normal((n, 2)).astype(np.float32)
    y = np.zeros_like(noise)
    # time-varying band-pass: process in short blocks with a sweeping centre
    blk = 256
    for i in range(0, n, blk):
        x = i / n
        fc = 350 + 2600 * np.sin(np.pi * min(1, x * 1.15)) ** 2
        sos = butter(2, [max(80, fc * 0.6), min(16000, fc * 1.6)], btype="band", fs=SR, output="sos")
        y[i:i + blk] = sosfilt(sos, noise[i:i + blk], axis=0)
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 2.2
    env = env * (t / dur < 0.62) + env * (t / dur >= 0.62) * np.exp(-(t / dur - 0.62) * 4)
    y *= env[:, None]
    # gentle stereo movement L->R
    pan = np.clip(t / dur, 0, 1)
    y[:, 0] *= np.cos(pan * np.pi / 2) * 0.6 + 0.4
    y[:, 1] *= np.sin(pan * np.pi / 2) * 0.6 + 0.4
    return y


def pop(dur=0.13):
    n = int(dur * SR); t = np.arange(n) / SR
    f = 330 + 950 * np.exp(-t / 0.011)
    ph = 2 * np.pi * np.cumsum(f) / SR
    tone = np.sin(ph) * np.exp(-t / 0.032) * np.minimum(1, t / 0.0012)
    click = rng.standard_normal(n) * np.exp(-t / 0.0015) * 0.25
    sos = butter(2, 5200, btype="low", fs=SR, output="sos")
    y = sosfilt(sos, tone + click)
    return np.stack([y, y], 1).astype(np.float32)


def click(dur=0.11):
    n = int(dur * SR); t = np.arange(n) / SR
    def tick(t0, amp, fc):
        tt = np.clip(t - t0, 0, None)
        burst = rng.standard_normal(n) * np.exp(-tt / 0.0022) * (t >= t0)
        sos = butter(2, [fc * 0.7, fc * 1.4], btype="band", fs=SR, output="sos")
        return sosfilt(sos, burst) * amp
    y = tick(0.0, 1.0, 2600) + tick(0.055, 0.55, 3200)
    return np.stack([y, y], 1).astype(np.float32)


def sparkle(dur=1.1):
    n = int(dur * SR); t = np.arange(n) / SR
    y = np.zeros((n, 2), np.float32)
    notes = [2093.0, 2637.0, 3136.0, 4186.0]
    for i, f0 in enumerate(notes):
        t0 = i * 0.045
        tt = np.clip(t - t0, 0, None); on = (t >= t0)
        s = (np.sin(2 * np.pi * f0 * tt) + 0.35 * np.sin(2 * np.pi * f0 * 2.76 * tt) * np.exp(-tt / 0.08)
             + 0.12 * np.sin(2 * np.pi * f0 * 5.4 * tt) * np.exp(-tt / 0.04))
        s = s * np.exp(-tt / (0.32 - i * 0.04)) * np.minimum(1, tt / 0.002) * on
        p = 0.25 + 0.5 * (i / (len(notes) - 1))
        y[:, 0] += s * np.cos(p * np.pi / 2); y[:, 1] += s * np.sin(p * np.pi / 2)
    return y


# (time in OUTPUT seconds, generator, peak dBFS)  -- kept deliberately sparse
SFX = [  # client: click only
    (6.63, click, -19.5),                  # "toalha piquenique"
    (20.60, click, -19.5),                 # "garanta já"
    (24.45, click, -19.5),                 # "cores e tamanhos"
]
if not NOSFX:
    for t, gen, pk in SFX:
        x = norm(gen(), pk)
        o = int(round(t * SR))
        m = min(len(x), total - o)
        out[o:o + m] += x[:m]

peak = float(np.abs(out).max())
assert peak < 0.98, peak
pcm = np.clip(out, -1, 1)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
                "-c:a", "pcm_s24le", OUT], input=pcm.astype(np.float32).tobytes(), check=True)
json.dump(dict(voice_peak_db=20 * np.log10(voice_peak), mix_peak_db=20 * np.log10(peak),
               sfx=[(t, pk) for t, _, pk in SFX]), open(S + "/work/audio_report.json", "w"), indent=1)
print("written", OUT, "duration", total / SR, "voice peak dBFS %.1f" % (20 * np.log10(voice_peak)),
      "mix peak dBFS %.1f" % (20 * np.log10(peak)))
