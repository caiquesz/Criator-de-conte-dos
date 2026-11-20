"""Alinhamento forçado (wav2vec2 MMS_FA) do texto da legenda com o áudio -> tempo exato de cada palavra.
O Whisper acerta o texto mas costuma adiantar palavras depois de pausas; aqui o tempo vem do áudio.

uso: python3 alinhar.py <audio16k.wav> <texto.txt> <saida.json>
texto.txt: uma frase por linha. Cada palavra pode ser "exibida|falada" (ex.: "R|erre") quando a grafia
da legenda é diferente do som. "*" sozinho marca um trecho de fala ininteligível que não vai pra legenda.
"""
import json, re, sys, unicodedata, wave
import numpy as np
import torch, torchaudio
from torchaudio.pipelines import MMS_FA as bundle

wav_path, txt_path, out_path = sys.argv[1:4]
wf = wave.open(wav_path)
assert wf.getframerate() == 16000
audio = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
wave_t = torch.from_numpy(audio).unsqueeze(0)

def norm(s):
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z']", "", s)

display, spoken = [], []
for line in open(txt_path, encoding="utf-8"):
    line = line.strip()
    if not line:
        continue
    for tok in line.split():
        if tok == "*":
            display.append(None); spoken.append("*")
            continue
        shown, _, said = tok.partition("|")
        display.append(shown)
        spoken.append(norm(said or shown))

model = bundle.get_model(with_star=True)
tokenizer, aligner = bundle.get_tokenizer(), bundle.get_aligner()
with torch.inference_mode():
    emission, _ = model(wave_t)
spans = aligner(emission[0], tokenizer(spoken))
ratio = wave_t.size(1) / emission.size(1) / 16000  # segundos por frame de emissão

words = []
for shown, said, sp in zip(display, spoken, spans):
    if shown is None:
        continue
    s, e = sp[0].start * ratio, sp[-1].end * ratio
    score = float(np.mean([x.score for x in sp]))
    words.append({"w": shown, "s": round(s, 3), "e": round(e, 3), "p": round(score, 3)})
json.dump(words, open(out_path, "w"), ensure_ascii=False, indent=1)
for i, w in enumerate(words):
    print(i, w["w"], w["s"], w["e"], w["p"])
