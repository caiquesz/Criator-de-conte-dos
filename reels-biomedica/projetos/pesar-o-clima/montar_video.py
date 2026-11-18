"""Vídeo-base do "Posso pesar o clima?": o vídeo como veio (cor original, sem color grade), mais perto, com o trecho de
drama em preto e branco e sem os 2 quadros pretos do fim.

Uso: python3 montar_video.py   (na pasta do projeto; lê o 4K de assets/video/original.mov)
Escreve assets/video/base.mp4 com QUADROS quadros e o som do original junto (o HyperFrames pede som no vídeo; a
mixagem lê a voz do original, intacta).

Zoom (2ª versão, 18/11: "no vídeo que eu te mandei de referência tá com um zoom na pessoa"): na referência o rosto
ocupa 30% da largura e fica a 30% da altura (mediana, medido com o YuNet); no vídeo da Nádia, 18–19% e a 40%. Cada
take ganha um recorte fixo de 1,6x tirado do 4K (1350×2400 de 2160×3840, então não perde nitidez), com o rosto no
meio da largura e a 30,5% da altura. Fixo por take, sem acompanhar: a câmera não anda. As trocas de recorte caem nos
cortes do próprio vídeo (no meio do quadro antes do corte, para não pegar o take vizinho).

P&B: na referência ele entra e sai por uma luz quente e cobre uma frase de peso; aqui é "E nem sempre o exercício
consegue mudar esses aspectos." (33,10–36,17 s): começa num corte do próprio vídeo e termina no corte para o outro take.
"""
import subprocess
from pathlib import Path

AQUI = Path(__file__).parent
V = AQUI / "assets" / "video"
FPS = 30
QUADROS = 1739                       # 57,967 s: o vídeo tem 2 quadros pretos depois disso
PB = (993, 1085)                     # quadros do P&B (33,10 a 36,167 s)
FILTRO_PB = "hue=s=0,eq=contrast=1.06"
W4, H4 = 2160, 3840
ZOOM = 1.6
CW, CH = round(W4 / ZOOM / 2) * 2, round(H4 / ZOOM / 2) * 2      # 1350 × 2400
ROSTO_Y = 0.305                      # altura do meio do rosto na referência
# takes: (primeiro quadro, centro do rosto x, y) no vídeo inteiro (fração), medidos com o YuNet a 2 quadros/s; "rampa"
# = o recorte desliza do take anterior até este ao longo do zoom do próprio vídeo (quadros 235–244 e 410–419), em vez
# de pular no primeiro quadro do zoom
TAKES = [(0, 0.566, 0.420, None),            # mesa, plano médio
         (235, 0.550, 0.455, 244),           # 7,83–8,13 s: o zoom do próprio vídeo para a sala inteira
         (410, 0.613, 0.401, 419),           # 13,67–13,97 s: o zoom de volta ao plano médio
         (1085, 0.586, 0.421, None),         # 36,17 s: o outro ângulo (corte seco)
         (1346, 0.555, 0.400, None)]         # 44,87 s (corte seco)


def janela(fx, fy):
    """Canto do recorte (px do 4K) para o rosto ficar no meio e a ROSTO_Y da altura, sem sair do quadro."""
    x = min(max(fx * W4 - CW / 2, 0), W4 - CW)
    y = min(max(fy * H4 - ROSTO_Y * CH, 0), H4 - CH)
    return round(x / 2) * 2, round(y / 2) * 2


def por_tempo(chaves):
    """Expressão do ffmpeg com o valor de cada take pelo tempo do quadro de entrada: salto no corte, ou rampa linear
    quando o take tem um quadro de fim de rampa."""
    expr = str(chaves[0][1])
    for (q0, v0, _), (q, v, fim) in zip(chaves, chaves[1:]):
        t0 = (q - 0.5) / FPS
        if fim is None:
            expr = f"if(gte(t,{t0:.4f}),{v},{expr})"
        else:
            t1 = (fim - 0.5) / FPS
            expr = f"if(gte(t,{t1:.4f}),{v},if(gte(t,{t0:.4f}),{v0}+({v}-{v0})*(t-{t0:.4f})/{t1 - t0:.4f},{expr}))"
    return expr


def quadros(arq):
    return int(subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries",
                               "stream=nb_read_frames", "-of", "csv=p=0", str(arq)], capture_output=True, text=True).stdout)


def main():
    js = [(q, *janela(fx, fy), fim) for q, fx, fy, fim in TAKES]
    for q, x, y, fim in js:
        print(f"  take a partir do quadro {q}: recorte {CW}×{CH} em ({x}, {y})" + (f", deslizando até o quadro {fim}" if fim else ""))
    ex, ey = por_tempo([(q, x, fim) for q, x, _, fim in js]), por_tempo([(q, y, fim) for q, _, y, fim in js])
    a, b = PB
    vf = (f"crop={CW}:{CH}:'{ex}':'{ey}',scale=1080:1920:flags=lanczos,setsar=1,fps={FPS},"
          f"trim=end_frame={QUADROS},setpts=PTS-STARTPTS,"
          f"split[c][p];[p]{FILTRO_PB}[pb];[c][pb]overlay=enable='between(n,{a},{b - 1})',format=yuv420p")
    saida = V / "base.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(V / "original.mov"),
                    "-filter_complex", f"[0:v]{vf}[v]", "-map", "[v]", "-map", "0:a", "-c:v", "libx264", "-crf", "14",
                    "-preset", "slow", "-g", "30", "-pix_fmt", "yuv420p", "-color_primaries", "bt709", "-color_trc", "bt709",
                    "-colorspace", "bt709", "-color_range", "tv", "-c:a", "aac", "-b:a", "256k", "-t", f"{QUADROS / FPS:.4f}",
                    "-movflags", "+faststart", str(saida)], check=True)
    n = quadros(saida)
    if n != QUADROS:
        raise SystemExit(f"o vídeo saiu com {n} quadros, esperava {QUADROS}")
    print(f"ok: {saida} ({n} quadros; zoom {ZOOM}x do 4K; P&B nos quadros {a}–{b - 1})")


if __name__ == "__main__":
    main()
