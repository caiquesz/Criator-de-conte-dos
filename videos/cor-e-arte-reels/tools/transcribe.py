"""Transcreve o vídeo em português com timestamps por palavra (formato HyperFrames).

Uso: python tools/transcribe.py assets/video/main.mp4 assets/transcript.json [modelo]
Requer: pip install faster-whisper  (modelo padrão: large-v3-turbo, int8 na CPU)
"""
import json
import subprocess
import sys

import numpy as np
from faster_whisper import WhisperModel

src, out = sys.argv[1], sys.argv[2]
model_name = sys.argv[3] if len(sys.argv) > 3 else "large-v3-turbo"

# decodifica com o ffmpeg do sistema (16 kHz mono) em vez do PyAV
pcm = subprocess.run(
    ["ffmpeg", "-v", "error", "-i", src, "-vn", "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
    check=True, capture_output=True,
).stdout
audio = np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768.0

model = WhisperModel(model_name, device="cpu", compute_type="int8", cpu_threads=4)
segments, info = model.transcribe(
    audio,
    language="pt",
    word_timestamps=True,
    vad_filter=True,
    beam_size=5,
    condition_on_previous_text=False,
)

words = []
for seg in segments:
    for w in seg.words or []:
        text = w.word.strip()
        if not text:
            continue
        words.append({
            "id": f"w{len(words)}",
            "text": text,
            "start": round(w.start, 3),
            "end": round(w.end, 3),
        })

with open(out, "w", encoding="utf-8") as f:
    json.dump(words, f, ensure_ascii=False, indent=1)

print(f"{len(words)} palavras -> {out} ({info.duration:.1f}s de áudio)")
