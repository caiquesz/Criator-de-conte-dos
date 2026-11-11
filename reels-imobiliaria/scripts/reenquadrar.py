"""Alterna o enquadramento de um vídeo de uma tomada só (aberto, médio, fechado) a partir do original.

Uso: python3 scripts/reenquadrar.py PASTA_DO_PROJETO

No plano.json:
  "enquadramentos": [
    {"de": 0,    "escala": 1.0},
    {"de": 8.5,  "escala": 1.5,  "centro": [0.53, 0.5]},
    {"de": 19.1, "escala": 1.22, "centro": [0.53, 0.5]}
  ]
Cada trecho vale do seu "de" até o "de" do seguinte (corte seco, como nas referências da
biomédica, que mudam de plano a cada parte da fala). "escala" 1 é o quadro inteiro; "centro" é o
ponto do quadro original (fração da largura e da altura) que vai para o meio da tela, preso às
bordas. O corte sai do original (4K do celular), então o plano fechado não perde nitidez em
1080×1920. Ponha os cortes nas pausas da fala.

Escreve assets/video/video.mp4 (o vídeo sem reenquadrar fica em video-aberto.mp4), com o áudio
original copiado sem mexer, e confere que o resultado tem os mesmos quadros do original.
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

L, A = 1080, 1920


def sonda(arq, campos):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", f"stream={campos}",
                        "-of", "json", str(arq)], capture_output=True, text=True, check=True).stdout
    return json.loads(r)["streams"][0]


def quadros(arq):
    r = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries",
                        "stream=nb_read_frames", "-of", "csv=p=0", str(arq)], capture_output=True, text=True, check=True).stdout
    return int(r.strip().split()[0])


def main():
    pasta = Path(sys.argv[1]).resolve()
    plano = json.loads((pasta / "plano.json").read_text())
    v = pasta / "assets" / "video"
    original = next(v.glob("original.*"))
    aberto = v / "video-aberto.mp4"
    if not aberto.exists():
        shutil.copy2(v / "video.mp4", aberto)
    s = sonda(original, "width,height,r_frame_rate")
    w, h = int(s["width"]), int(s["height"])
    num, den = (int(x) for x in s["r_frame_rate"].split("/"))
    fps = num / den
    total = quadros(aberto)
    if w > h:  # o celular grava de lado e marca a rotação: o ffmpeg já entrega em pé
        w, h = h, w

    trechos = sorted(plano["enquadramentos"], key=lambda e: e["de"])
    bordas = [round(e["de"] * fps) for e in trechos] + [total]
    bordas[0] = 0
    ramos, filtros = [], []
    for i, e in enumerate(trechos):
        a, b = bordas[i], bordas[i + 1]
        if b <= a:
            continue
        esc = float(e.get("escala", 1.0))
        cw, ch = round(w / esc / 2) * 2, round(h / esc / 2) * 2
        cx, cy = e.get("centro", [0.5, 0.5])
        x0 = int(min(max(cx * w - cw / 2, 0), w - cw)) // 2 * 2
        y0 = int(min(max(cy * h - ch / 2, 0), h - ch)) // 2 * 2
        filtros.append(f"[s{i}]trim=start_frame={a}:end_frame={b},setpts=PTS-STARTPTS,"
                       f"crop={cw}:{ch}:{x0}:{y0},scale={L}:{A}:flags=lanczos,setsar=1[v{i}]")
        ramos.append(i)
        print(f"{a / fps:6.2f}–{b / fps:6.2f} s: escala {esc:.2f}, corte {cw}×{ch} em ({x0}, {y0})")
    grafo = (f"[0:v]split={len(ramos)}" + "".join(f"[s{i}]" for i in ramos) + ";" + ";".join(filtros) + ";"
             + "".join(f"[v{i}]" for i in ramos) + f"concat=n={len(ramos)}:v=1:a=0,setpts=N/({num}/{den})/TB[o]")
    saida = v / "video.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(original), "-filter_complex", grafo, "-map", "[o]",
                    "-map", "0:a:0", "-fps_mode", "passthrough", "-c:v", "libx264", "-crf", "14", "-preset", "slow",
                    "-g", "30", "-pix_fmt", "yuv420p", "-c:a", "copy", str(saida)], check=True)
    n = quadros(saida)
    if n != total:
        raise SystemExit(f"o reenquadrado tem {n} quadros, o original {total}: imagem sairia da voz")
    print(f"ok ({n} quadros, mesmos do original): {saida}")


if __name__ == "__main__":
    main()
