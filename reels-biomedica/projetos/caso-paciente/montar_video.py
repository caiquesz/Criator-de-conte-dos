"""Monta o vídeo-base do Caso de paciente (2ª versão): planos aberto e fechado alternando em corte seco,
P&B nas falas de drama, a cor da referência B e um empurrão lento na foto que a cliente pôs.

Uso: python3 montar_video.py   (na pasta do projeto, depois do enquadrar.py nas duas versões:
  renders/enquadrado.mp4 → assets/video/video-aberto.mp4 e renders/enquadrado-fechado.mp4 → video-fechado.mp4)
Escreve assets/video/video.mp4 com os mesmos 2385 quadros (a voz continua a do original, intacta).

A cor (referência B, a moça de blazer marrom): fundo frio e neutro, pele e roupa douradas, sombras mais fundas
e uma vinheta leve. Não entra na foto da paciente que a cliente pôs no vídeo (as fotos ficam como são).
"""
import subprocess
from pathlib import Path

from roteiro import FPS, PLANOS, TOTAL

AQUI = Path(__file__).parent
V = AQUI / "assets" / "video"
COR = ("curves=m='0/0.02 0.25/0.21 0.5/0.49 0.75/0.79 1/0.98',"
       "colorbalance=rs=0.07:gs=0.015:bs=-0.055:rm=0.045:gm=0.005:bm=-0.045:rh=-0.035:gh=0:bh=0.035,"
       "eq=saturation=1.15,vignette=angle=PI/5")
# P&B como o da referência B: limpo, claro e com contraste
PB = "hue=s=0,eq=contrast=1.12:brightness=0.01"
# a volta do P&B para a cor: a saturação sobe e o escurecido some em 0,5 s
VOLTA = "hue=s='min(1,t/0.5)':b='-1.6*max(0,1-t/0.5)'"


def empurrao(n, z=0.06, y=0.40):
    """Empurrão lento (zoom de 1 a 1+z ao longo do plano), em volta de um ponto um pouco acima do meio."""
    return (f"zoompan=z='1+{z}*on/{max(n - 1, 1)}':x='iw/2-(iw/zoom/2)':y='ih*{y}-(ih/zoom*{y})':d=1:"
            f"s=1080x1920:fps={FPS}")


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
        cadeia = [f"trim=start_frame={qa - s0 * FPS}:end_frame={qb - s0 * FPS}", "setpts=PTS-STARTPTS"]
        if efeito in ("pb", "zoom"):
            cadeia.append(empurrao(qb - qa, 0.05 if efeito == "pb" else 0.08))
        if plano != "foto":
            cadeia.append(COR)
        if efeito == "pb":
            cadeia.append(PB)
        elif efeito == "volta":
            cadeia.append(VOLTA)
        cadeia.append("format=yuv420p")
        parte = tmp / f"{k:02d}.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(s0), "-i", str(fontes[plano]), "-vf", ",".join(cadeia),
                        "-an", "-c:v", "libx264", "-crf", "14", "-preset", "slow", "-g", "30", "-pix_fmt", "yuv420p",
                        "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
                        "-video_track_timescale", "15360", str(parte)], check=True)
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
