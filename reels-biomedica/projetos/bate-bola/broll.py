"""Fundo da abertura do Bate-bola: três trechos dela falando, sem som, cortados do 4K um pouco mais perto.

Uso: python3 broll.py   (na pasta do projeto; escreve assets/video/broll.mp4, fora do git)

No modelo da doutora, a abertura passa por cima de imagens das duas se mexendo, mais de perto. Aqui
são três trechos em que ela está falando e não pisca nenhuma vez (a segunda versão parou a
imagem com ela de olho fechado). A voz não entra: na abertura só toca a música.
"""
import subprocess
from pathlib import Path

AQUI = Path(__file__).parent
# (início no original, duração) = 4,2667 s. Escolhidos medindo a piscada quadro a quadro com o modelo de rosto
# do mediapipe (eyeBlink abaixo de 0,35 em todos os quadros; medir pelo escuro do olho não serve, os cílios e o
# delineado dela ficam escuros com o olho fechado) e só onde ela está falando (nas perguntas fica de boca fechada)
TRECHOS = [(61.80, 1.9), (16.30, 1.2), (14.75, 1.1667)]
ESCALA, CENTRO = 1.3, (0.55, 0.42)
W, H = 2160, 3840
cw, ch = round(W / ESCALA / 2) * 2, round(H / ESCALA / 2) * 2
x0 = int(min(max(CENTRO[0] * W - cw / 2, 0), W - cw)) // 2 * 2
y0 = int(min(max(CENTRO[1] * H - ch / 2, 0), H - ch)) // 2 * 2
# uma entrada por trecho, cada uma já buscada no seu início (com uma entrada só e os trechos fora de ordem o
# ffmpeg guarda quadros 4K na memória e estoura); o -ss antes do -i cai no quadro-chave e o trim acerta o resto
entradas = []
for a, d in TRECHOS:
    entradas += ["-ss", f"{max(0.0, a - 1.0):.3f}", "-t", f"{d + 1.5:.3f}", "-i", str(AQUI / "assets" / "video" / "original.mov")]
partes = "".join(f"[{k}:v]fps=30,trim=start={min(a, 1.0):.3f}:duration={d},setpts=PTS-STARTPTS,crop={cw}:{ch}:{x0}:{y0},"
                 f"scale=1080:1920:flags=lanczos,setsar=1[v{k}];" for k, (a, d) in enumerate(TRECHOS))
grafo = partes + "".join(f"[v{k}]" for k in range(len(TRECHOS))) + f"concat=n={len(TRECHOS)}:v=1:a=0[o]"
saida = AQUI / "assets" / "video" / "broll.mp4"
subprocess.run(["ffmpeg", "-v", "error", "-y", *entradas, "-filter_complex", grafo,
                "-map", "[o]", "-an", "-c:v", "libx264", "-crf", "14", "-preset", "slow", "-g", "30", "-pix_fmt", "yuv420p", str(saida)], check=True)
n = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries", "stream=nb_read_frames",
                    "-of", "csv=p=0", str(saida)], capture_output=True, text=True).stdout.strip()
print(f"ok: {saida} ({n} quadros)")
