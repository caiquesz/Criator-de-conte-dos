"""Monta o áudio final sem mexer na voz: áudio original (ganho 1,0) + efeitos sonoros.

Uso: python3 scripts/mixar.py PASTA_DO_PROJETO VIDEO_RENDERIZADO SAIDA.mp4

Nada de normalização, compressão, limitador ou mudança de tom: o áudio que veio no
vídeo entra exatamente como está e os efeitos são somados por cima, nos mesmos
instantes e volumes que o gerador usa. A imagem do vídeo renderizado é copiada
sem recompressão. No fim, compara o resultado com o original nos trechos sem
efeito, para provar que a voz não mudou.
"""

import json
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from gerar import DURACAO_SFX, FPS, PICO_SFX, eventos_sfx  # noqa: E402

TAXA = 48000


def pcm(arquivo):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(arquivo), "-vn", "-ac", "2", "-ar", str(TAXA),
                          "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).copy()


def main():
    pasta, renderizado, saida = Path(sys.argv[1]).resolve(), Path(sys.argv[2]), Path(sys.argv[3])
    plano = json.loads((pasta / "plano.json").read_text())
    original = pcm(pasta / plano.get("video_original", plano["video"]))
    mix = original.copy()
    tem_efeito = np.zeros(len(mix), bool)

    for t, som, vol in eventos_sfx(plano):
        ini = max(0.0, t - PICO_SFX.get(som, 0.08) + 1 / FPS)
        efeito = pcm(pasta / "assets" / "sfx" / f"{som}.mp3")[: int(DURACAO_SFX.get(som, 1.0) * TAXA)] * vol
        a = int(round(ini * TAXA))
        b = min(len(mix), a + len(efeito))
        mix[a:b] += efeito[: b - a]
        tem_efeito[a:b] = True

    pico = float(np.abs(mix).max())
    if pico > 0.97:
        print(f"atenção: pico {20 * np.log10(pico):.1f} dBFS; baixe o volume de algum efeito em vez de comprimir")
    wav = saida.with_suffix(".mix.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(TAXA), "-ac", "2", "-i", "-",
                    "-c:a", "pcm_f32le", str(wav)], input=mix.astype(np.float32).tobytes(), check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(renderizado), "-i", str(wav),
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "320k",
                    "-ar", str(TAXA), "-movflags", "+faststart", "-shortest", str(saida)], check=True)
    wav.unlink()

    # prova: fora dos efeitos, o áudio final é o original (só a diferença do codificador AAC)
    final = pcm(saida)
    n = min(len(final), len(original))
    livre = ~tem_efeito[:n]
    dif = final[:n][livre] - original[:n][livre]
    sinal = np.sqrt(np.mean(original[:n][livre] ** 2))
    resto = np.sqrt(np.mean(dif ** 2))
    print(f"pico do mix: {20 * np.log10(pico):.1f} dBFS")
    print(f"diferença para o original fora dos efeitos: {20 * np.log10(resto / sinal):.1f} dB abaixo da voz")
    print("ok:", saida)


if __name__ == "__main__":
    main()
