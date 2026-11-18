"""Áudio final: voz (com os cortes da timeline + tratamento + loudnorm -14 LUFS) + SFX.
uso: python3 audio.py <bruto.mov> <saida.wav>
SFX: procura primeiro em ./sfx (papel, lápis, relógio...) e depois em ../sfx (pop, clique, whoosh)."""
import json, os, re, subprocess, sys, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
TL = json.load(open(os.path.join(HERE, "timeline.json")))
SR, FPS = 48000, TL["fps"]
src, out = sys.argv[1], sys.argv[2]
dur = TL["nframes"] / FPS

# 1) voz: junta os trechos mantidos, com micro-fades em cada emenda
parts, labels = [], []
for k, (a, b) in enumerate(TL["keep"]):
    ta, tb = a / FPS, b / FPS
    parts.append(f"[0:a:0]atrim={ta:.4f}:{tb:.4f},asetpts=PTS-STARTPTS,"
                 f"afade=t=in:st=0:d=0.012,afade=t=out:st={tb - ta - 0.012:.4f}:d=0.012[s{k}]")
    labels.append(f"[s{k}]")
chain = (";".join(parts) + ";" + "".join(labels) + f"concat=n={len(labels)}:v=0:a=1,aresample=48000,"
         "highpass=f=75,lowpass=f=15000,afftdn=nr=8:nf=-44,"
         "equalizer=f=220:t=q:w=1.2:g=-2,equalizer=f=3200:t=q:w=1.5:g=2.5,"
         "acompressor=threshold=-24dB:ratio=3:attack=8:release=120:makeup=3dB[v]")
tmp = os.path.join(os.path.dirname(os.path.abspath(out)), "voz_tratada.wav")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-filter_complex", chain, "-map", "[v]",
                "-ac", "2", "-ar", str(SR), tmp], check=True)
r = subprocess.run(["ffmpeg", "-hide_banner", "-i", tmp, "-af", "loudnorm=I=-14:TP=-1.5:LRA=9:print_format=json",
                    "-f", "null", "-"], capture_output=True, text=True)
js = json.loads(re.findall(r"\{[^{}]*\}", r.stderr)[-1])
ln = (f"loudnorm=I=-14:TP=-1.5:LRA=9:measured_I={js['input_i']}:measured_TP={js['input_tp']}:"
      f"measured_LRA={js['input_lra']}:measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true")
voz = subprocess.run(["ffmpeg", "-v", "error", "-i", tmp, "-af", ln + ",aresample=48000", "-ac", "2",
                      "-f", "f32le", "-"], capture_output=True, check=True).stdout
voz = np.frombuffer(voz, np.float32).reshape(-1, 2).copy()
N = int(round(dur * SR))
mix = np.zeros((N, 2), np.float32)
mix[:min(N, len(voz))] = voz[:N]
print(f"voz: {js['input_i']} LUFS -> -14 | {len(voz) / SR:.3f}s de voz para {dur:.3f}s de vídeo")

# 2) SFX
def load(name):
    for d in (os.path.join(HERE, "sfx"), os.path.join(HERE, "..", "sfx")):
        p = os.path.join(d, name + ".wav")
        if os.path.exists(p):
            b = subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
                               capture_output=True, check=True).stdout
            return np.frombuffer(b, np.float32).reshape(-1, 2)
    raise FileNotFoundError(name)
cache, SFX_GAIN = {}, 0.45
for ev in TL["sfx"]:
    s = cache.setdefault(ev["name"], load(ev["name"]))
    i0 = int(round(ev["t"] * SR)); a0 = max(0, -i0); i0 = max(0, i0)
    seg = s[a0:]; n = min(len(seg), N - i0)
    if n > 0:
        mix[i0:i0 + n] += seg[:n] * ev["vol"] * SFX_GAIN

# 3) limitador suave + fade final
lim = 10 ** (-1 / 20)
if np.abs(mix).max() > lim:
    k = lim * 0.8
    mix = np.where(np.abs(mix) > k, np.sign(mix) * (k + (lim - k) * np.tanh((np.abs(mix) - k) / (lim - k))), mix)
fo = int(0.25 * SR)
mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
pcm = (np.clip(mix, -1, 1) * 32767).astype(np.int16)
with wave.open(out, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print("ok", out)
