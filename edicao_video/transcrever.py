"""Transcrição palavra a palavra com faster-whisper.
uso: python3 transcrever.py <audio16k.wav> <modelo, ex. large-v3> <saida.json>"""
import json, sys, wave
import numpy as np
from faster_whisper import WhisperModel

m = WhisperModel(sys.argv[2], device="cpu", compute_type="int8", cpu_threads=4)
wf = wave.open(sys.argv[1])
a = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
segs, info = m.transcribe(a, language="pt", word_timestamps=True, beam_size=5, vad_filter=False)
out = []
for s in segs:
    out.append({"start": s.start, "end": s.end, "text": s.text,
                "words": [{"w": w.word, "s": w.start, "e": w.end, "p": w.probability} for w in s.words]})
    print(f"[{s.start:6.2f}-{s.end:6.2f}] {s.text}", flush=True)
json.dump(out, open(sys.argv[3], "w"), ensure_ascii=False, indent=1)
