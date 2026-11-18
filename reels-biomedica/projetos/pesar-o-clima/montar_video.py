"""Vídeo-base do "Posso pesar o clima?": o vídeo como veio (cor original, sem color grade), só com o trecho de drama
em preto e branco e sem os 2 quadros pretos do fim.

Uso: python3 montar_video.py   (na pasta do projeto; lê assets/video/video.mp4 do novo_projeto.sh)
Escreve assets/video/base.mp4 com QUADROS quadros e o som do original junto (o HyperFrames pede som no vídeo; a
mixagem lê a voz do original, intacta).

Na referência (referencias/ref-pesar-o-clima.mp4) o P&B entra e sai por uma luz quente e cobre uma frase de
peso; aqui é "E nem sempre o exercício consegue mudar esses aspectos." (33,10–36,17 s): começa num corte do
próprio vídeo (33,1) e termina no corte para o outro take (36,167), e as duas pontas ficam atrás da luz.
"""
import subprocess
from pathlib import Path

AQUI = Path(__file__).parent
V = AQUI / "assets" / "video"
FPS = 30
QUADROS = 1739                       # 57,967 s: o vídeo tem 2 quadros pretos depois disso
PB = (993, 1085)                     # quadros do P&B (33,10 a 36,167 s)
# P&B como o da referência: cinza limpo, um pouco mais de contraste
FILTRO_PB = "hue=s=0,eq=contrast=1.06"


def quadros(arq):
    return int(subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries",
                               "stream=nb_read_frames", "-of", "csv=p=0", str(arq)], capture_output=True, text=True).stdout)


def main():
    a, b = PB
    vf = (f"trim=end_frame={QUADROS},setpts=PTS-STARTPTS,"
          f"split[c][p];[p]{FILTRO_PB}[pb];[c][pb]overlay=enable='between(n,{a},{b - 1})',format=yuv420p")
    saida = V / "base.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(V / "video.mp4"), "-i", str(V / "original.mov"),
                    "-filter_complex", f"[0:v]{vf}[v]", "-map", "[v]", "-map", "1:a", "-c:v", "libx264", "-crf", "14",
                    "-preset", "slow", "-g", "30", "-pix_fmt", "yuv420p", "-color_primaries", "bt709", "-color_trc", "bt709",
                    "-colorspace", "bt709", "-color_range", "tv", "-c:a", "aac", "-b:a", "256k", "-t", f"{QUADROS / FPS:.4f}",
                    "-movflags", "+faststart", str(saida)], check=True)
    n = quadros(saida)
    if n != QUADROS:
        raise SystemExit(f"o vídeo saiu com {n} quadros, esperava {QUADROS}")
    print(f"ok: {saida} ({n} quadros; P&B nos quadros {a}–{b - 1})")


if __name__ == "__main__":
    main()
