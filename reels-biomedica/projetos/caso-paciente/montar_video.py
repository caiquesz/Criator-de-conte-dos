"""Monta o vídeo-base do Caso de paciente: planos aberto e fechado alternando em corte seco, P&B nas falas de
drama e um empurrão lento no P&B e na foto que a cliente pôs.

Uso: python3 montar_video.py   (na pasta do projeto, depois do enquadrar.py nas duas versões:
  renders/enquadrado.mp4 → assets/video/video-aberto.mp4 e renders/enquadrado-fechado.mp4 → video-fechado.mp4)
Escreve assets/video/video.mp4 com os mesmos 2385 quadros (a voz continua a do original, intacta).

Sem color grade (3ª versão, 17/11: "pode tirar o color grade, não gostei dele; deixa original mesmo"): a cor é a
dos takes como ela mandou, só com a luz igualada entre eles pelo enquadrar.py (--cor-pela luz, 4ª versão: "deixe
igual eu te mandei, alterando apenas a iluminação"; o enquadrar.py agora lê a faixa limitada e converte o Display
P3 do iPhone para BT.709, que antes saíam lavados). Na 2ª versão entrava a cor da referência B (pele dourada,
fundo frio, vinheta), que a cliente recusou.

O empurrão é feito aqui, em Python, com posição fracionária (warpAffine em cada plano do YUV, sem passar por
RGB): o zoompan do ffmpeg arredonda a posição do recorte a cada quadro e a imagem tremia ~2 px para cima e para
baixo (a cliente viu na foto: "as fotos estão tremendo").
"""
import subprocess
from pathlib import Path

import cv2
import numpy as np

from roteiro import FPS, PLANOS, TOTAL

AQUI = Path(__file__).parent
V = AQUI / "assets" / "video"
W, H = 1080, 1920
COR_TAGS = ["-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709"]
# P&B como o da referência B: limpo, claro e com contraste
PB = "hue=s=0,eq=contrast=1.12:brightness=0.01"
# a volta do P&B para a cor: a saturação sobe e o escurecido some em 0,5 s
VOLTA = "hue=s='min(1,t/0.5)':b='-1.6*max(0,1-t/0.5)'"


def empurrar(quadros, z, y=0.40):
    """Empurrão lento (zoom de 1 a 1+z ao longo do plano) em volta de um ponto um pouco acima do meio, com posição
    fracionária: cada quadro yuv420p é ampliado plano a plano (luma e as duas cromas) sem arredondar nada."""
    n = len(quadros)
    saida = []
    for k, q in enumerate(quadros):
        s = 1 + z * k / max(n - 1, 1)
        planos = []
        for arr, f in ((q[0], 1), (q[1], 2), (q[2], 2)):
            cx, cy = W / 2 / f, H * y / f
            M = np.float32([[s, 0, cx * (1 - s)], [0, s, cy * (1 - s)]])
            planos.append(cv2.warpAffine(arr, M, (arr.shape[1], arr.shape[0]), flags=cv2.INTER_LANCZOS4,
                                         borderMode=cv2.BORDER_REFLECT))
        saida.append(planos)
    return saida


def ler_yuv(fonte, s0, qa, qb):
    """Quadros qa..qb-1 da fonte em yuv420p (lidos do quadro-chave s0, cortados no quadro exato)."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(s0), "-i", str(fonte), "-vf",
                          f"trim=start_frame={qa - s0 * FPS}:end_frame={qb - s0 * FPS},setpts=PTS-STARTPTS",
                          "-f", "rawvideo", "-pix_fmt", "yuv420p", "-"], capture_output=True, check=True).stdout
    tam = W * H * 3 // 2
    quadros = []
    for i in range(len(raw) // tam):
        b = np.frombuffer(raw, np.uint8, tam, i * tam)
        quadros.append([b[:W * H].reshape(H, W), b[W * H:W * H * 5 // 4].reshape(H // 2, W // 2),
                        b[W * H * 5 // 4:].reshape(H // 2, W // 2)])
    return quadros


def main():
    fontes = {"a": V / "video-aberto.mp4", "f": V / "video-fechado.mp4", "foto": V / "video-aberto.mp4"}
    tmp = V / "_planos"
    tmp.mkdir(exist_ok=True)
    lista, fim_ant = [], 0
    # um plano por vez (os 20 juntos num grafo só estouraram a memória): cada um é lido do quadro-chave
    # anterior (um por segundo) e cortado no quadro exato; depois tudo é emendado sem recodificar
    for k, (a, b, plano, efeito) in enumerate(PLANOS):
        qa, qb = round(a * FPS), round(b * FPS)
        assert qa == fim_ant, (k, qa, fim_ant)
        fim_ant = qb
        s0 = qa // FPS
        cadeia = []
        if efeito == "pb":
            cadeia.append(PB)
        elif efeito == "volta":
            cadeia.append(VOLTA)
        cadeia.append("format=yuv420p")
        parte = tmp / f"{k:02d}.mp4"
        codificar = ["-an", "-c:v", "libx264", "-crf", "14", "-preset", "slow", "-g", "30", "-pix_fmt", "yuv420p",
                     *COR_TAGS, "-video_track_timescale", "15360", str(parte)]
        if efeito in ("pb", "zoom"):
            imgs = empurrar(ler_yuv(fontes[plano], s0, qa, qb), 0.05 if efeito == "pb" else 0.08)
            dados = b"".join(np.concatenate([p.ravel() for p in q]).tobytes() for q in imgs)
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "yuv420p", "-s", f"{W}x{H}",
                            "-r", str(FPS), *COR_TAGS, "-i", "-", "-vf", ",".join(cadeia), *codificar],
                           input=dados, check=True)
        else:
            cadeia = [f"trim=start_frame={qa - s0 * FPS}:end_frame={qb - s0 * FPS}", "setpts=PTS-STARTPTS"] + cadeia
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(s0), "-i", str(fontes[plano]), "-vf",
                            ",".join(cadeia), *codificar], check=True)
        m = quadros(parte)
        if m != qb - qa:
            raise SystemExit(f"plano {k}: {m} quadros, esperava {qb - qa}")
        lista.append(parte)
    assert fim_ant == TOTAL, fim_ant
    (tmp / "lista.txt").write_text("".join(f"file '{p.name}'\n" for p in lista))
    saida = V / "video.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(tmp / "lista.txt"),
                    "-c", "copy", "-movflags", "+faststart", str(saida)], check=True)
    # o som do original vai junto (o HyperFrames pede som no vídeo; a mixagem final lê a voz do original, intacta)
    com_som = V / "_com_som.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(saida), "-i", str(V / "original.mov"), "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-shortest", "-movflags", "+faststart", str(com_som)], check=True)
    com_som.replace(saida)
    n = quadros(saida)
    if n != TOTAL:
        raise SystemExit(f"o vídeo saiu com {n} quadros, esperava {TOTAL}")
    for p in lista:
        p.unlink()
    (tmp / "lista.txt").unlink(); tmp.rmdir()
    print(f"ok: {saida} ({n} quadros, {len(PLANOS)} planos)")


def quadros(arq):
    return int(subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries",
                               "stream=nb_read_frames", "-of", "csv=p=0", str(arq)], capture_output=True, text=True).stdout)


if __name__ == "__main__":
    main()
