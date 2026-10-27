"""Estabiliza o vídeo cena por cena e aplica a mesma correção à máscara do recorte.

Uso: python3 scripts/estabilizar.py PASTA_DO_PROJETO [--suavidade 20] [--max-desvio 40]

Lê assets/video/video.mp4, assets/video/mascara540.webm e os cortes de plano.json
(os instantes das transições). Cada cena é estabilizada sozinha (vid.stab em duas
passadas), para o tremor de um plano não vazar para o outro através do corte. A
máscara da pessoa recebe exatamente as mesmas transformações, então a legenda
continua passando atrás dela no lugar certo.

Cada cena só fica estabilizada se o tremor cair pelo menos 25%; nas outras o que
sobra é movimento intencional da câmera e a correção só traria zoom, então a cena
fica como veio.

Escreve assets/video/video_estab.mp4 (com o áudio original copiado, sem mexer)
e assets/video/recorte.webm (pessoa recortada, já estabilizada).
"""

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path

import numpy as np

FPS = 30


def ff(*args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args], check=True)


def tremor(trf, escala=2.0):
    """Tremor da câmera (px, em 1080): o quanto a trajetória global foge da sua média móvel."""
    g = []
    for linha in open(trf):
        if not linha.startswith("Frame"):
            continue
        lm = re.findall(r"\(LM (-?\d+) (-?\d+) -?\d+ -?\d+ \d+ [\d.]+ [\d.]+\)", linha)
        g.append(np.median(np.array(lm, float), 0) if lm else (0.0, 0.0))
    if len(g) < 17:
        return 0.0
    t = np.cumsum(np.array(g[1:]) * escala, 0)
    k = np.ones(15) / 15
    media = np.stack([np.convolve(np.pad(t[:, i], 7, mode="edge"), k, "valid") for i in range(2)], 1)
    return float(np.sqrt(((t - media) ** 2).sum(1)).mean())


def medir(video, trf):
    ff("-i", str(video), "-vf", f"scale=540:960,vidstabdetect=shakiness=8:accuracy=15:result={trf}", "-f", "null", "-")
    return tremor(trf)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pasta")
    ap.add_argument("--suavidade", type=int, default=20, help="janela de suavização (quadros de cada lado)")
    ap.add_argument("--max-desvio", type=int, default=40, help="correção máxima em px (limita o zoom)")
    a = ap.parse_args()

    pasta = Path(a.pasta).resolve()
    v = pasta / "assets" / "video"
    tmp = v / "estab_tmp"
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir()

    plano = json.loads((pasta / "plano.json").read_text())
    total = int(subprocess.run(
        ["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v", "-show_entries",
         "stream=nb_read_frames", "-of", "csv=p=0", str(v / "video.mp4")],
        capture_output=True, text=True, check=True).stdout.strip())
    cortes = sorted({round(t["t"] * FPS) for t in plano.get("transicoes", [])})
    bordas = [0] + [c for c in cortes if 0 < c < total] + [total]
    print(f"{total} quadros, {len(bordas) - 1} cenas")

    # 1. corta vídeo e máscara (já ampliada) nos mesmos quadros, sem perdas
    chave = "+".join(f"eq(n,{c})" for c in bordas[1:-1])
    lista = ",".join(map(str, bordas[1:-1]))
    ff("-i", str(v / "video.mp4"), "-an", "-c:v", "libx264", "-crf", "6", "-preset", "veryfast",
       "-force_key_frames", f"expr:{chave}", "-f", "segment", "-segment_frames", lista,
       "-reset_timestamps", "1", str(tmp / "v%03d.mkv"))
    ff("-c:v", "libvpx-vp9", "-i", str(v / "mascara540.webm"), "-vf",
       "alphaextract,scale=1080:1920:flags=bicubic,erosion,gblur=sigma=1.2,format=gray",
       "-c:v", "libx264", "-crf", "0", "-preset", "ultrafast", "-pix_fmt", "gray",
       "-force_key_frames", f"expr:{chave}", "-f", "segment", "-segment_frames", lista,
       "-reset_timestamps", "1", str(tmp / "m%03d.mkv"))

    # 2. estabiliza cada cena e aplica a mesma transformação à máscara
    transf = (f"smoothing={a.suavidade}:optzoom=1:zoomspeed=0.2:maxshift={a.max_desvio}:"
              f"maxangle=0.04:crop=black")
    lista_v, lista_m = [], []
    for i in range(len(bordas) - 1):
        trf = tmp / f"c{i:03d}.trf"
        cena_v, cena_m = tmp / f"v{i:03d}.mkv", tmp / f"m{i:03d}.mkv"
        ff("-i", str(cena_v), "-vf", f"vidstabdetect=shakiness=6:accuracy=15:result={trf}", "-f", "null", "-")
        ff("-i", str(cena_v), "-vf", f"vidstabtransform=input={trf}:{transf}:interpol=bicubic,unsharp=5:5:0.35:3:3:0",
           "-c:v", "libx264", "-crf", "8", "-preset", "fast", str(tmp / f"ev{i:03d}.mkv"))
        # só fica estabilizada a cena em que o tremor cai de verdade; nas outras o que
        # sobra é movimento da própria câmera e a estabilização só traria zoom
        antes = medir(cena_v, tmp / f"a{i:03d}.trf")
        depois = medir(tmp / f"ev{i:03d}.mkv", tmp / f"d{i:03d}.trf")
        usa = antes >= 1.4 and depois <= 0.75 * antes
        if usa:
            ff("-i", str(cena_m), "-vf", f"vidstabtransform=input={trf}:{transf}:interpol=bilinear,format=gray",
               "-c:v", "libx264", "-crf", "0", "-preset", "ultrafast", "-pix_fmt", "gray", str(tmp / f"em{i:03d}.mkv"))
            lista_v.append(f"file 'ev{i:03d}.mkv'")
            lista_m.append(f"file 'em{i:03d}.mkv'")
        else:
            lista_v.append(f"file 'v{i:03d}.mkv'")
            lista_m.append(f"file 'm{i:03d}.mkv'")
        print(f"cena {i + 1}/{len(bordas) - 1} ({bordas[i] / FPS:.1f}–{bordas[i + 1] / FPS:.1f}s): "
              f"tremor {antes:.2f}px → {depois:.2f}px, {'estabilizada' if usa else 'original'}", flush=True)
    (tmp / "v.txt").write_text("\n".join(lista_v) + "\n")
    (tmp / "m.txt").write_text("\n".join(lista_m) + "\n")

    # 3. junta as cenas; o áudio é o original, copiado sem reprocessar
    ff("-f", "concat", "-safe", "0", "-i", str(tmp / "v.txt"), "-i", str(v / "video.mp4"),
       "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-crf", "14", "-preset", "slow", "-g", "30",
       "-pix_fmt", "yuv420p", "-c:a", "copy", "-shortest", str(v / "video_estab.mp4"))
    ff("-i", str(v / "video_estab.mp4"), "-f", "concat", "-safe", "0", "-i", str(tmp / "m.txt"),
       "-filter_complex", "[1:v]format=gray[m];[0:v][m]alphamerge,format=yuva420p[o]",
       "-map", "[o]", "-an", "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-b:v", "0", "-crf", "22",
       "-deadline", "realtime", "-cpu-used", "8", "-row-mt", "1", "-auto-alt-ref", "0", "-g", "30",
       str(v / "recorte.webm"))
    shutil.rmtree(tmp)
    print("ok:", v / "video_estab.mp4", v / "recorte.webm")


if __name__ == "__main__":
    main()
