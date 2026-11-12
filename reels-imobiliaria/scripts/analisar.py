"""Prepara um vídeo já cortado para a edição: transcrição palavra a palavra,
pontos de corte entre cenas e paleta de cores.

Uso: python3 scripts/analisar.py PASTA_DO_PROJETO [--modelo medium]

Lê PASTA/assets/video/video.mp4 e escreve na pasta:
  transcricao.json  frases e palavras com início/fim (s)
  transcricao.txt   o texto com tempos, para montar o plano
  cortes.json       instantes de troca de cena (onde entram as transições)
  paleta.json       paleta e cor de destaque sugerida
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import paleta  # noqa: E402


def transcrever(video, modelo):
    from faster_whisper import WhisperModel
    bruto = subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-ac", "1", "-ar", "16000",
                            "-f", "f32le", "-"], capture_output=True, check=True).stdout
    audio = np.frombuffer(bruto, dtype=np.float32)
    m = WhisperModel(modelo, device="cpu", compute_type="int8")
    frases, _ = m.transcribe(audio, language="pt", word_timestamps=True, vad_filter=True)
    saida = []
    for f in frases:
        saida.append({"inicio": round(f.start, 3), "fim": round(f.end, 3), "texto": f.text.strip(),
                      "palavras": [{"t": w.word.strip(), "s": round(w.start, 3), "e": round(w.end, 3),
                                    "conf": round(w.probability, 2)} for w in f.words]})
    return saida


def cortes(video, limiar=10):
    log = subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-vf",
                          f"scdet=threshold={limiar},metadata=print:file=-", "-an", "-f", "null", "-"],
                         capture_output=True, text=True).stdout
    tempos = [float(t) for t in re.findall(r"lavfi\.scd\.time=([0-9.]+)", log)]
    # trocas a menos de 0,3 s umas das outras são a mesma transição
    unicos = []
    for t in tempos:
        if not unicos or t - unicos[-1] > 0.3:
            unicos.append(round(t, 3))
    return unicos


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pasta")
    ap.add_argument("--modelo", default="medium")
    a = ap.parse_args()
    pasta = Path(a.pasta)
    video = pasta / "assets" / "video" / "video.mp4"

    trans = transcrever(video, a.modelo)
    (pasta / "transcricao.json").write_text(json.dumps(trans, ensure_ascii=False, indent=1))
    linhas = []
    for f in trans:
        linhas.append(f"[{f['inicio']:6.2f} – {f['fim']:6.2f}] {f['texto']}")
        linhas.append("    " + "  ".join(f"{w['t']}@{w['s']:.2f}" for w in f["palavras"]))
    (pasta / "transcricao.txt").write_text("\n".join(linhas) + "\n")

    c = cortes(video)
    (pasta / "cortes.json").write_text(json.dumps(c))

    sys.argv = ["paleta.py", str(video), "--saida", str(pasta / "paleta.json")]
    paleta.main()
    print("\n".join(linhas))
    print("cortes:", c)


if __name__ == "__main__":
    main()
