"""CTC forced alignment (torchaudio MMS_FA) of the known transcript -> precise word times (SOURCE seconds)."""
import sys, json, re, unicodedata, wave
import numpy as np, torch, torchaudio
S = sys.argv[1]
T = json.load(open(S + "/work/transcript.json"))
words = [w["w"].strip() for s in T for w in s["words"]]
# merge whisper's split tokens ("R", "$", "22" / "-benefício")
disp = []
i = 0
while i < len(words):
    w = words[i]
    # whisper splits prices as "R" "$" "15" ",00." -> one display token "R$ 15,00"
    if w == "R" and i + 2 < len(words) and words[i + 1] == "$":
        num = words[i + 2]; j = i + 3
        if j < len(words) and re.fullmatch(r",\d\d\.?", words[j]): num += words[j].rstrip("."); j += 1
        disp.append("R$ " + num); i = j; continue
    if w.startswith("-") and disp: disp[-1] += w; i += 1; continue
    disp.append(w); i += 1
NUM = {"65": "sessenta e cinco", "40": "quarenta"}
PRICE = {"15": "quinze reais", "15,00": "quinze reais", "22,00": "vinte e dois reais", "17,50": "dezessete e cinquenta"}
def norm(w):
    if w.startswith("R$ "):
        return PRICE[w[3:].strip()]
    w = w.lower()
    w = NUM.get(re.sub(r"[^0-9]", "", w), w) if re.fullmatch(r"[0-9]+[.,]?", w) else w
    w = "centimetros" if w in ("cm", "cm.") else w
    w = unicodedata.normalize("NFKD", w)
    w = "".join(c for c in w if not unicodedata.combining(c))
    return re.sub(r"[^a-z ]", "", w).strip()
toks = [norm(w) for w in disp]
bundle = torchaudio.pipelines.MMS_FA
model = bundle.get_model(with_star=False); model.eval()
dic = bundle.get_dict(star=None)
wf = wave.open(S + "/work/voice16k.wav"); sr = wf.getframerate()
a = torch.from_numpy(np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float32) / 32768).unsqueeze(0)
with torch.inference_mode():
    em, _ = model(a)
# each display word may expand to several spoken words (numbers); align on the flattened list
flat = []; owner = []
for i, t in enumerate(toks):
    for part in t.split():
        flat.append(part); owner.append(i)
targets = torch.tensor([[dic[c] for wd in flat for c in wd]], dtype=torch.int32)
ali, scores = torchaudio.functional.forced_align(em, targets, blank=0)
ali = ali[0]; scores = scores[0].exp()
spans = torchaudio.functional.merge_tokens(ali, scores)
ratio = a.shape[1] / em.shape[1] / sr
out = []; k = 0
per_word = []
for wd in flat:
    n = len(wd); sp = spans[k:k + n]; k += n
    per_word.append((sp[0].start * ratio, sp[-1].end * ratio, float(np.mean([x.score for x in sp]))))
res = []
for i, w in enumerate(disp):
    idx = [j for j, o in enumerate(owner) if o == i]
    res.append(dict(w=w, s=round(per_word[idx[0]][0], 3), e=round(per_word[idx[-1]][1], 3), p=round(min(per_word[j][2] for j in idx), 3)))
json.dump(res, open(S + "/work/aligned.json", "w"), ensure_ascii=False, indent=0)
print(" ".join(f'{r["w"]}[{r["s"]:.2f}-{r["e"]:.2f}]' for r in res))
