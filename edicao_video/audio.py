"""Áudio final: voz (corte do silêncio + tratamento + loudnorm) + SFX nos tempos da timeline.
uso: python3 audio.py <bruto.mov> <sfx_dir> <saida.wav>"""
import json, os, subprocess, sys, re
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
TL = json.load(open(os.path.join(HERE, "timeline.json")))
SR = 48000
src, sfx_dir, out = sys.argv[1], sys.argv[2], sys.argv[3]
CA, CB = TL["cut"]
ta, tb = CA / TL["fps"], CB / TL["fps"]
dur = TL["nframes"] / TL["fps"]

# 1) voz cortada + tratada
pre = (f"[0:a]atrim=0:{ta},afade=t=out:st={ta - 0.012}:d=0.012,asetpts=PTS-STARTPTS[a];"
       f"[0:a]atrim={tb},afade=t=in:st=0:d=0.012,asetpts=PTS-STARTPTS[b];"
       "[a][b]concat=n=2:v=0:a=1,aresample=48000,"
       "highpass=f=75,lowpass=f=15000,afftdn=nr=8:nf=-44,"
       "equalizer=f=220:t=q:w=1.2:g=-2,equalizer=f=3200:t=q:w=1.5:g=2.5,"
       "acompressor=threshold=-24dB:ratio=3:attack=8:release=120:makeup=3dB")
tmp = os.path.join(os.path.dirname(out), "voz_tratada.wav")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-filter_complex", pre + "[v]", "-map", "[v]",
                "-ac", "2", "-ar", str(SR), tmp], check=True)
# loudnorm 2 passadas
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
print("voz medida:", js["input_i"], "LUFS ->", -14)

# 2) SFX
def load(name):
    b = subprocess.run(["ffmpeg", "-v", "error", "-i", os.path.join(sfx_dir, name + ".wav"), "-ac", "2", "-ar", str(SR),
                        "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(b, np.float32).reshape(-1, 2)
cache = {}
SFX_GAIN = 0.45
for ev in TL["sfx"]:
    s = cache.setdefault(ev["name"], load(ev["name"]))
    i0 = int(round(ev["t"] * SR))
    a0 = max(0, -i0); i0 = max(0, i0)
    seg = s[a0:]
    n = min(len(seg), N - i0)
    if n > 0:
        mix[i0:i0 + n] += seg[:n] * ev["vol"] * SFX_GAIN

# 3) limitador simples (soft clip acima de -1 dBFS) + fade final
peak = np.abs(mix).max()
lim = 10 ** (-1 / 20)
if peak > lim:
    over = np.abs(mix) > lim * 0.8
    mix = np.where(over, np.sign(mix) * (lim * 0.8 + (lim * 0.2) * np.tanh((np.abs(mix) - lim * 0.8) / (lim * 0.2))), mix)
fo = int(0.25 * SR)
mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
pcm = (np.clip(mix, -1, 1) * 32767).astype(np.int16)
import wave
with wave.open(out, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print("ok", out, f"{N / SR:.3f}s pico={peak:.2f}")
