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

"pausas": [{"em": 8.1333, "dur": 1.8}] (tempo do original) abre um respiro no vídeo para uma
abertura em tela cheia (a abertura do quadro da biomédica): a imagem fica parada e o som em
silêncio nesse trecho, e o resto anda para a frente. A voz não muda: o áudio do vídeo é
recodificado para caber o silêncio, então a mixagem lê a voz de assets/video/voz.wav (o original
decodificado, com zeros exatos na pausa; ponha "video_original": "assets/video/voz.wav" no plano).
Todos os outros tempos do plano (legendas, fotos, transições) ficam no tempo novo; só os
"enquadramentos" e as "pausas" ficam no tempo do original.
"""

import numpy as np

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
    s = sonda(original, "width,height")
    w, h = int(s["width"]), int(s["height"])
    # sempre 30 quadros por segundo, como a composição e o video.mp4 do novo_projeto.sh (o original pode vir
    # em 31,58 ou 60): o filtro fps=30 vem antes dos cortes, então os quadros contados são os do vídeo final
    num, den = 30, 1
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
    pausas = sorted((round(p["em"] * fps), round(p["dur"] * fps)) for p in plano.get("pausas", []))
    grafo = (f"[0:v]fps={num}/{den},split={len(ramos)}" + "".join(f"[s{i}]" for i in ramos) + ";" + ";".join(filtros) + ";"
             + "".join(f"[v{i}]" for i in ramos) + f"concat=n={len(ramos)}:v=1:a=0,setpts=N/({num}/{den})/TB"
             + ("[o]" if not pausas else "[r]"))
    audio = ["-map", "0:a:0", "-c:a", "copy"]
    if pausas:
        # cada pedaço entre pausas; a imagem do último quadro antes da pausa fica parada nela
        taxa = int(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=sample_rate",
                                   "-of", "csv=p=0", str(original)], capture_output=True, text=True, check=True).stdout.strip())
        cortes = [0] + [q for q, _ in pausas] + [total]
        k = len(cortes) - 1
        grafo += f";[r]split={k}" + "".join(f"[r{j}]" for j in range(k)) + f";[0:a:0]asplit={k}" + "".join(f"[a{j}]" for j in range(k))
        for j in range(k):
            a, b = cortes[j], cortes[j + 1]
            para = f",tpad=stop_mode=clone:stop={pausas[j][1]}" if j < len(pausas) else ""
            grafo += f";[r{j}]trim=start_frame={a}:end_frame={b},setpts=PTS-STARTPTS{para}[w{j}]"
            sa, sb = round(a / fps * taxa), round(b / fps * taxa)
            fim_a = f":end_sample={sb}" if j < k - 1 else ""
            silencio = f",apad=pad_len={round(pausas[j][1] / fps * taxa)}" if j < len(pausas) else ""
            grafo += f";[a{j}]atrim=start_sample={sa}{fim_a},asetpts=PTS-STARTPTS{silencio}[x{j}]"
        grafo += ";" + "".join(f"[w{j}][x{j}]" for j in range(k)) + f"concat=n={k}:v=1:a=1[o0][oa]"
        grafo += f";[o0]setpts=N/({num}/{den})/TB[o]"
        audio = ["-map", "[oa]", "-c:a", "aac", "-b:a", "320k"]
        for q, d in pausas:
            print(f"pausa de {d / fps:.2f} s em {q / fps:.2f} s (imagem parada, silêncio)")
    saida = v / "video.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(original), "-filter_complex", grafo, "-map", "[o]",
                    *audio, "-fps_mode", "passthrough", "-c:v", "libx264", "-crf", "14", "-preset", "slow",
                    "-g", "30", "-pix_fmt", "yuv420p", str(saida)], check=True)
    esperado = total + sum(d for _, d in pausas)
    n = quadros(saida)
    if n != esperado:
        raise SystemExit(f"o reenquadrado tem {n} quadros, esperava {esperado}: imagem sairia da voz")
    if pausas:
        # a voz para a mixagem: o original decodificado como o mixar.py faz, com zeros exatos nas pausas
        TAXA = 48000
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(original), "-vn", "-ac", "2", "-ar", str(TAXA),
                              "-f", "f32le", "-"], capture_output=True, check=True).stdout
        voz = np.frombuffer(raw, np.float32).reshape(-1, 2)
        partes, ini = [], 0
        for q, d in pausas:
            corte = round(q / fps * TAXA)
            partes += [voz[ini:corte], np.zeros((round(d / fps * TAXA), 2), np.float32)]
            ini = corte
        partes.append(voz[ini:])
        wav = v / "voz.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(TAXA), "-ac", "2", "-i", "-",
                        "-c:a", "pcm_f32le", str(wav)], input=np.concatenate(partes).tobytes(), check=True)
        print(f"voz para a mixagem (original com as pausas): {wav}")
    print(f"ok ({n} quadros{', os do original mais as pausas' if pausas else ', mesmos do original'}): {saida}")


if __name__ == "__main__":
    main()
