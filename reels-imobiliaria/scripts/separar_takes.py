"""Separa um vídeo já montado (vários takes emendados) em takes soltos, para o enquadrar.py.

Uso: python3 scripts/separar_takes.py PASTA_DO_PROJETO

Lê os cortes de PASTA/cortes.json (o analisar.py: tempos no video.mp4, a 30 quadros/s) e escreve
PASTA/takes/01.mov, 02.mov... do original em 4K (assets/video/original.*). O original do celular
pode vir com quadros por segundo variáveis: ele passa antes para 30 constantes, como o video.mp4
(mesmo filtro fps=30), e cada take sai cortado no quadro exato do corte. O áudio de cada take
vai junto, cortado nos mesmos instantes (a mixagem final lê a voz do original, sem emendas).
Confere que a soma dos quadros dos takes é a do video.mp4.
"""

import json
import subprocess
import sys
from pathlib import Path

FPS = 30


def quadros(arq):
    r = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries",
                        "stream=nb_read_frames", "-of", "csv=p=0", str(arq)], capture_output=True, text=True, check=True)
    return int(r.stdout.strip().split()[0])


def main():
    pasta = Path(sys.argv[1]).resolve()
    v = pasta / "assets" / "video"
    original = next(v.glob("original.*"))
    total = quadros(v / "video.mp4")
    cortes = [round(t * FPS) for t in json.loads((pasta / "cortes.json").read_text())]
    bordas = [0] + cortes + [total]
    # um intermediário em 30 quadros/s constantes, com um quadro-chave por segundo: cada take começa a ser
    # lido do quadro-chave anterior (busca exata, sem decodificar o vídeo inteiro catorze vezes)
    inter = pasta / "takes" / "_30fps.mp4"
    inter.parent.mkdir(exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(original), "-vf", f"fps={FPS}", "-c:v", "libx264", "-crf", "10",
                    "-preset", "medium", "-g", str(FPS), "-keyint_min", str(FPS), "-sc_threshold", "0", "-pix_fmt", "yuv420p",
                    "-c:a", "pcm_s16le", str(inter).replace(".mp4", ".mov")], check=True)
    inter = inter.with_suffix(".mov")
    if quadros(inter) != total:
        raise SystemExit(f"o intermediário tem {quadros(inter)} quadros, o video.mp4 {total}")
    soma = 0
    for k, (a, b) in enumerate(zip(bordas, bordas[1:]), 1):
        s0 = a // FPS                                   # o quadro-chave (segundo inteiro) antes do take
        saida = pasta / "takes" / f"{k:02d}.mov"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(s0), "-i", str(inter),
                        "-vf", f"trim=start_frame={a - s0 * FPS}:end_frame={b - s0 * FPS},setpts=PTS-STARTPTS",
                        "-af", f"atrim=start={a / FPS - s0:.6f}:end={b / FPS - s0:.6f},asetpts=PTS-STARTPTS",
                        "-c:v", "libx264", "-crf", "10", "-preset", "medium", "-g", str(FPS), "-pix_fmt", "yuv420p",
                        "-c:a", "pcm_s16le", str(saida)], check=True)
        n = quadros(saida)
        if n != b - a:
            raise SystemExit(f"{saida.name}: {n} quadros, esperava {b - a}")
        soma += n
        print(f"{saida.name}: quadros {a}–{b - 1} ({a / FPS:.3f}–{b / FPS:.3f} s), {n} quadros")
    inter.unlink()
    if soma != total:
        raise SystemExit(f"os takes somam {soma} quadros, o video.mp4 tem {total}")
    print(f"ok: {len(bordas) - 1} takes, {soma} quadros")


if __name__ == "__main__":
    main()
