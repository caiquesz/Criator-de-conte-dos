"""Acerta o tempo das legendas pela voz real, para nenhuma palavra entrar antes da fala.

Uso: python3 scripts/sincronizar.py PASTA_DO_PROJETO

O Whisper costuma adiantar a primeira palavra depois de uma pausa (em até meio
segundo). Aqui um detector de voz (Silero, o mesmo do faster-whisper) marca os
trechos em que a pessoa está falando, e cada palavra que começaria antes do seu
trecho de fala passa para o começo dele. Os grupos de legenda que estavam
encadeados continuam encadeados. Grava o plano.json corrigido e guarda o
anterior em plano.antes-sync.json.
"""

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from faster_whisper.vad import VadOptions, get_speech_timestamps


def trechos_de_fala(video):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-ac", "1", "-ar", "16000",
                          "-f", "f32le", "-"], capture_output=True, check=True).stdout
    audio = np.frombuffer(raw, np.float32)
    opts = VadOptions(threshold=0.65, min_speech_duration_ms=120, min_silence_duration_ms=120, speech_pad_ms=0)
    return [(s["start"] / 16000, s["end"] / 16000) for s in get_speech_timestamps(audio, opts)]


def inicio_corrigido(s, trechos):
    """Se a palavra cai num silêncio (ou começa antes do trecho dela), vai para o começo do trecho seguinte."""
    for k, (ini, fim) in enumerate(trechos):
        if ini <= s < fim:
            # nos últimos 150 ms de um trecho, a palavra quase sempre abre o trecho seguinte
            prox = trechos[k + 1][0] if k + 1 < len(trechos) else None
            if fim - s < 0.15 and prox is not None and prox - s < 0.8:
                return prox
            return s
        if s < ini:
            return ini if ini - s < 0.8 else s  # longe demais: deixa como está
    return s


def main():
    pasta = Path(sys.argv[1]).resolve()
    plano = json.loads((pasta / "plano.json").read_text())
    (pasta / "plano.antes-sync.json").write_text(json.dumps(plano, ensure_ascii=False, indent=1))
    video = pasta / plano.get("video_original", plano["video"])
    trechos = trechos_de_fala(video)

    grupos = plano["legendas"]
    primeiras = [min(p["s"] for l in g["linhas"] for p in l["palavras"]) for g in grupos]
    encadeado = [i + 1 < len(grupos) and abs(g["fim"] - (primeiras[i + 1] - 0.08)) < 0.06
                 for i, g in enumerate(grupos)]

    mudou = []
    anterior = -1.0
    for g in grupos:
        for l in g["linhas"]:
            for p in l["palavras"]:
                novo = round(max(inicio_corrigido(p["s"], trechos), anterior + 0.06), 3)
                if novo - p["s"] > 0.05:
                    mudou.append(f'{p["t"]} {p["s"]:.2f}→{novo:.2f}')
                p["s"] = novo
                anterior = novo
    for i, g in enumerate(grupos):
        if encadeado[i]:
            g["fim"] = round(min(p["s"] for l in grupos[i + 1]["linhas"] for p in l["palavras"]) - 0.08, 3)
    (pasta / "plano.json").write_text(json.dumps(plano, ensure_ascii=False, indent=1))
    print("trechos de fala:", " ".join(f"[{a:.2f}-{b:.2f}]" for a, b in trechos))
    print(f"{len(mudou)} palavras atrasadas:", "; ".join(mudou))


if __name__ == "__main__":
    main()
