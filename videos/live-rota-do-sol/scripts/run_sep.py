"""Separa duas vozes com SepFormer (speechbrain). Uso: python run_sep.py <entrada_16k.wav> <pasta_saida> speechbrain/sepformer-whamr16k

Requer torch, torchaudio, speechbrain e soundfile (ver README)."""
import sys, os, numpy as np, torch, soundfile as sf
from speechbrain.inference.separation import SepformerSeparation
src, outdir, model = sys.argv[1], sys.argv[2], sys.argv[3]
m = SepformerSeparation.from_hparams(source=model, savedir=os.path.join(outdir, "pretrained_"+model.split("/")[-1]))
x, sr = sf.read(src, dtype="float32")
with torch.no_grad():
    est = m.separate_batch(torch.from_numpy(x)[None])  # [1, T, n_src]
est = est[0].numpy()
for k in range(est.shape[1]):
    sf.write(os.path.join(outdir, f"src{k}.wav"), est[:, k], sr)
print("ok", est.shape, sr)
