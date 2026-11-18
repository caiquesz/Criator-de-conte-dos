"""Vídeo-base do "Posso pesar o clima?": o vídeo como veio (cor original, sem color grade), mais perto, com o trecho de
drama em preto e branco, sem os 2 quadros pretos do fim e com o último quadro parado por CAUDA quadros para a assinatura.

Uso: python3 montar_video.py   (na pasta do projeto; lê o 4K de assets/video/original.mov)
Escreve assets/video/base.mp4 com QUADROS + CAUDA quadros e o som do original junto (o HyperFrames pede som no vídeo)
e assets/video/voz.wav: o som do original amostra por amostra, mais silêncio na cauda (a mixagem lê a voz dali).

Zoom só na abertura (3ª versão, 18/11: "o zoom é só na introdução, na hora que ela fala posso pesar o clima, com a
fonte na lateral, igual na referência"). Na 2ª eu tinha fechado o vídeo inteiro (1,6x) e ela recusou. Na referência,
durante o título, o rosto fica à direita (centro a 69% da largura e 31% da altura, 28% da largura de tamanho) e o
título ocupa a esquerda; depois da luz quente volta o plano normal. Aqui: um recorte fixo do 4K só nos quadros da
abertura (até o corte do próprio vídeo em 1,667 s, que a luz cobre), com o rosto nesse tamanho e nesse lugar; o resto
do vídeo fica com o enquadramento original.

Cauda (3ª versão): na referência a assinatura entra quando a última legenda sai, sozinha na tela, e fica 1,1 s até o
fim. Aqui o vídeo acaba 0,4 s depois da última palavra; ela já está parada (menos de 0,5 de diferença média por
quadro no último segundo), então o último quadro fica parado mais 26 quadros (0,87 s). A voz não muda.

P&B: na referência ele entra e sai por uma luz quente e cobre uma frase de peso; aqui é "E nem sempre o exercício
consegue mudar esses aspectos." (33,10–36,17 s): começa num corte do próprio vídeo e termina no corte para o outro take.
"""
import subprocess
import sys
from pathlib import Path

import numpy as np

AQUI = Path(__file__).parent
V = AQUI / "assets" / "video"
sys.path.insert(0, str(AQUI.parent.parent.parent / "reels-imobiliaria" / "scripts"))
from mixar import TAXA, pcm  # noqa: E402
FPS = 30
QUADROS = 1739                       # 57,967 s: o vídeo tem 2 quadros pretos depois disso
CAUDA = 26                           # o último quadro parado, para a assinatura (total 1765 quadros, 58,833 s)
PB = (993, 1085)                     # quadros do P&B (33,10 a 36,167 s)
FILTRO_PB = "hue=s=0,eq=contrast=1.06"
W4, H4 = 2160, 3840
ABERTURA = 50                        # quadros 0–49: até o corte do próprio vídeo em 1,667 s
ROSTO = (0.560, 0.416, 0.183)        # rosto da Nádia na abertura (centro x, y e largura, fração), YuNet a 2 quadros/s
ALVO = (0.69, 0.31, 0.28)            # o da referência durante o título


def janela_abertura():
    fx, fy, fw = ROSTO
    ax, ay, aw = ALVO
    z = aw / fw
    cw, ch = round(W4 / z / 2) * 2, round(H4 / z / 2) * 2
    x = min(max(fx * W4 - ax * cw, 0), W4 - cw)
    y = min(max(fy * H4 - ay * ch, 0), H4 - ch)
    return z, cw, ch, round(x / 2) * 2, round(y / 2) * 2


def quadros(arq):
    return int(subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries",
                               "stream=nb_read_frames", "-of", "csv=p=0", str(arq)], capture_output=True, text=True).stdout)


def main():
    z, cw, ch, x, y = janela_abertura()
    print(f"  abertura (quadros 0–{ABERTURA - 1}): zoom {z:.2f}x, recorte {cw}×{ch} em ({x}, {y}) do 4K")
    a, b = PB
    vf = (f"fps={FPS},split[f][z];[f]scale=1080:1920:flags=lanczos,setsar=1[base];"
          f"[z]crop={cw}:{ch}:{x}:{y},scale=1080:1920:flags=lanczos,setsar=1[zoom];"
          f"[base][zoom]overlay=enable='lt(n,{ABERTURA})',trim=end_frame={QUADROS},setpts=PTS-STARTPTS,"
          f"split[c][p];[p]{FILTRO_PB}[pb];[c][pb]overlay=enable='between(n,{a},{b - 1})',"
          f"tpad=stop_mode=clone:stop={CAUDA},format=yuv420p")
    total = QUADROS + CAUDA
    saida = V / "base.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(V / "original.mov"),
                    "-filter_complex", f"[0:v]{vf}[v]", "-map", "[v]", "-map", "0:a", "-c:v", "libx264", "-crf", "14",
                    "-preset", "slow", "-g", "30", "-pix_fmt", "yuv420p", "-color_primaries", "bt709", "-color_trc", "bt709",
                    "-colorspace", "bt709", "-color_range", "tv", "-af", "apad", "-c:a", "aac", "-b:a", "256k", "-t", f"{total / FPS:.4f}",
                    "-movflags", "+faststart", str(saida)], check=True)
    n = quadros(saida)
    if n != total:
        raise SystemExit(f"o vídeo saiu com {n} quadros, esperava {total}")
    # a voz: o som do original sem tocar em nada, com silêncio depois do fim dele até o fim do vídeo
    orig = pcm(V / "original.mov")
    voz = np.zeros((max(len(orig), round(total / FPS * TAXA)), 2), np.float32)
    voz[:len(orig)] = orig
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(TAXA), "-ac", "2", "-i", "-", "-c:a", "pcm_f32le",
                    str(V / "voz.wav")], input=voz.tobytes(), check=True)
    assert np.array_equal(pcm(V / "voz.wav")[:len(orig)], orig), "a voz tem que sair idêntica ao original"
    print(f"ok: {saida} ({n} quadros; zoom só na abertura; P&B nos quadros {a}–{b - 1}; "
          f"último quadro parado nos {CAUDA} do fim) e voz.wav ({len(orig) / TAXA:.3f} s do original + silêncio)")


if __name__ == "__main__":
    main()
