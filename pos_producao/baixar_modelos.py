#!/usr/bin/env python3
"""Baixa os modelos offline (Silero VAD + Whisper ONNX) do GitHub para pos_producao/modelos/."""
import argparse, subprocess, sys, tarfile
from pathlib import Path

DEST = Path(__file__).resolve().parent / "modelos"
BASE = "https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/"


def baixar(url: str, destino: Path):
    print("↓", url)
    subprocess.run(["curl", "-sSL", "--fail", "-o", str(destino), url], check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modelo", default="small", help="tiny | base | small | medium")
    a = ap.parse_args()
    DEST.mkdir(parents=True, exist_ok=True)
    vad = DEST / "silero_vad.onnx"
    if not vad.exists():
        baixar(BASE + "silero_vad.onnx", vad)
    pasta = DEST / f"sherpa-onnx-whisper-{a.modelo}"
    if pasta.exists():
        print("já existe:", pasta); return
    tar = DEST / f"{a.modelo}.tar.bz2"
    baixar(BASE + f"sherpa-onnx-whisper-{a.modelo}.tar.bz2", tar)
    with tarfile.open(tar) as t:
        t.extractall(DEST, filter="data")
    tar.unlink()
    print("ok:", pasta)


if __name__ == "__main__":
    main()
