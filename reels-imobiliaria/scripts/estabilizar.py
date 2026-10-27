"""Estabiliza o vídeo cena por cena e aplica a mesma correção à máscara do recorte.

Uso: python3 scripts/estabilizar.py PASTA_DO_PROJETO [--zoom-max 1.2]

O movimento da câmera é medido quadro a quadro (fluxo óptico nos pontos do fundo,
sem a pessoa recortada) e, em cada cena (os cortes vêm das transições do plano),
a trajetória é suavizada: o que sobra é o balanço, e cada quadro é deslocado,
girado e escalado para tirá-lo. Para não aparecer borda, a cena ganha um zoom fixo;
a suavização mais forte cujo zoom cabe em --zoom-max é a escolhida, então cenas com
movimento grande e intencional (uma panorâmica rápida) recebem menos correção.

Nos trechos em que a correção pediria zoom demais (uma panorâmica rápida, uma
virada no corredor), ela é reduzida só ali, com transição suave, e o resto da cena
continua bem estabilizado.

A imagem sai do envio original (4K, quando houver): o corte do zoom é feito em 4K e
só depois o quadro desce para 1080×1920, sem perder nitidez. A máscara da pessoa
recebe exatamente a mesma transformação, então a legenda continua passando atrás
dela no lugar certo.

Escreve assets/video/video_estab.mp4 (com o áudio original copiado, sem mexer)
e assets/video/recorte.webm (pessoa recortada, já estabilizada), com os mesmos
quadros do original, cada um no mesmo instante.
"""

import argparse
import json
import subprocess
from pathlib import Path

import cv2
import numpy as np

W, H = 1080, 1920          # saída
AW, AH = 540, 960          # análise do movimento
SUAVIDADES = [1.0, 0.75, 0.55, 0.4, 0.28, 0.18]   # sigma da suavização (s), da mais forte à mais fraca


def ff(*args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args], check=True)


def contar(video):
    """Número de quadros decodificados de um arquivo."""
    saida = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v", "-show_entries",
                            "stream=nb_read_frames", "-of", "csv=p=0", str(video)],
                           capture_output=True, text=True, check=True).stdout
    return int(saida.strip().split()[0])


def ler(cmd, w, h, canais):
    """Gerador de quadros (uint8) de um comando ffmpeg que escreve rawvideo na saída."""
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    tam = w * h * canais
    while True:
        b = p.stdout.read(tam)
        if len(b) < tam:
            break
        yield np.frombuffer(b, np.uint8).reshape(h, w, canais) if canais > 1 else np.frombuffer(b, np.uint8).reshape(h, w)
    p.wait()


def mascaras(v, w, h):
    return ler(["ffmpeg", "-v", "error", "-c:v", "libvpx-vp9", "-i", str(v / "mascara540.webm"), "-vf",
                f"alphaextract,scale={w}:{h}:flags=bicubic,erosion,gblur=sigma=1.2,format=gray",
                "-f", "rawvideo", "-pix_fmt", "gray", "-"], w, h, 1)


def movimento(v):
    """Movimento do fundo de cada quadro em relação ao anterior: deslocamento do centro (px em 1080),
    giro (rad) e log da escala."""
    quadros = ler(["ffmpeg", "-v", "error", "-i", str(v / "video.mp4"), "-vf", f"scale={AW}:{AH},format=gray",
                   "-f", "rawvideo", "-pix_fmt", "gray", "-"], AW, AH, 1)
    lk = dict(winSize=(31, 31), maxLevel=4, criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01))
    c = np.array([AW / 2, AH / 2])
    mov, ant = [np.zeros(4)], None
    for q, m in zip(quadros, mascaras(v, AW, AH)):
        if ant is not None:
            fundo = (cv2.dilate((ant[1] > 60).astype(np.uint8), np.ones((15, 15), np.uint8)) == 0).astype(np.uint8) * 255
            p0 = cv2.goodFeaturesToTrack(ant[0], 500, 0.01, 7, mask=fundo, blockSize=7)
            d = np.zeros(4)
            if p0 is not None and len(p0) >= 12:
                p1, st, _ = cv2.calcOpticalFlowPyrLK(ant[0], q, p0, None, **lk)
                pv, st2, _ = cv2.calcOpticalFlowPyrLK(q, ant[0], p1, None, **lk)
                ok = (st.ravel() == 1) & (st2.ravel() == 1) & (np.linalg.norm((pv - p0).reshape(-1, 2), axis=1) < 1.0)
                if ok.sum() >= 12:
                    M, _ = cv2.estimateAffinePartial2D(p0[ok], p1[ok], method=cv2.RANSAC, ransacReprojThreshold=1.2)
                    if M is not None:
                        dc = M[:, :2] @ c + M[:, 2] - c
                        d = np.array([dc[0] * W / AW, dc[1] * W / AW, np.arctan2(M[1, 0], M[0, 0]),
                                      np.log(np.hypot(M[0, 0], M[1, 0]))])
            mov.append(d)
        ant = (q, m)
    return np.array(mov)


def suavizar(x, sigma):
    if sigma < 0.5:
        return x.copy()
    r = int(3 * sigma) + 1
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2)
    k /= k.sum()
    return np.stack([np.convolve(np.pad(x[:, i], r, mode="edge"), k, "valid") for i in range(x.shape[1])], 1)


def zoom_necessario(corr):
    """Menor zoom (por quadro) que esconde a borda depois da correção (tx, ty, giro, log escala)."""
    tx, ty, th, ls = corr.T
    s = np.exp(ls)
    cantos = np.array([[-W / 2, -H / 2], [W / 2, -H / 2], [W / 2, H / 2], [-W / 2, H / 2]])
    lo, hi = np.ones(len(corr)), np.full(len(corr), 3.0)
    for _ in range(40):
        z = (lo + hi) / 2
        ok = np.ones(len(corr), bool)
        for u in cantos:
            vx, vy = u[0] / z - tx, u[1] / z - ty
            px = (np.cos(th) * vx + np.sin(th) * vy) / s
            py = (-np.sin(th) * vx + np.cos(th) * vy) / s
            ok &= (np.abs(px) <= W / 2) & (np.abs(py) <= H / 2)
        hi = np.where(ok, z, hi)
        lo = np.where(ok, lo, z)
    return hi


def fator(c, zoom_max, fps):
    """Quanto da correção cabe (0–1) em cada quadro sem passar do zoom máximo, variando suave."""
    f = np.ones(len(c))
    excede = zoom_necessario(c) > zoom_max
    if excede.any():
        lo, hi = np.zeros(excede.sum()), np.ones(excede.sum())
        for _ in range(25):
            m = (lo + hi) / 2
            ok = zoom_necessario(c[excede] * m[:, None]) <= zoom_max
            lo, hi = np.where(ok, m, lo), np.where(ok, hi, m)
        f[excede] = lo
        # mínimo numa janela de ~0,5 s e média curta: a correção volta aos poucos, nunca de repente
        w = int(0.5 * fps) | 1
        f = np.lib.stride_tricks.sliding_window_view(np.pad(f, w // 2, mode="edge"), w).min(1)
        f = suavizar(f[:, None], w / 6)[:, 0]
    return f


def balanco(traj, fps):
    """Balanço médio (px): o que a trajetória foge da sua versão suavizada em 0,35 s."""
    return np.hypot(*(traj - suavizar(traj, 0.35 * fps))[:, :2].T).mean()


def matriz(corr, z, escala):
    """2×3: q = c + z·(s·R(θ)·(p − c) + t), em px da resolução `escala`× a de 1080."""
    tx, ty, th, ls = corr
    a = z * np.exp(ls)
    R = a * np.array([[np.cos(th), -np.sin(th)], [np.sin(th), np.cos(th)]])
    c = np.array([W / 2, H / 2]) * escala
    t = z * np.array([tx, ty]) * escala
    return np.hstack([R, (c + t - R @ c)[:, None]])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pasta")
    ap.add_argument("--zoom-max", type=float, default=1.2, help="zoom máximo para esconder a borda")
    a = ap.parse_args()

    pasta = Path(a.pasta).resolve()
    v = pasta / "assets" / "video"
    plano = json.loads((pasta / "plano.json").read_text())
    total = contar(v / "video.mp4")
    taxa = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries", "stream=r_frame_rate",
                           "-of", "csv=p=0", str(v / "video.mp4")], capture_output=True, text=True, check=True).stdout.strip()
    num, den = (int(x) for x in taxa.split("/"))
    fps = num / den  # a taxa do próprio vídeo (o celular nem sempre grava a 30)
    cortes = sorted({round(t["t"] * fps) for t in plano.get("transicoes", [])})
    bordas = [0] + [c for c in cortes if 0 < c < total] + [total]
    print(f"{total} quadros, {len(bordas) - 1} cenas", flush=True)

    cache = v / "movimento.npy"
    mov = np.load(cache) if cache.exists() else movimento(v)
    np.save(cache, mov)
    if len(mov) != total:
        raise SystemExit(f"movimento de {len(mov)} quadros, o vídeo tem {total}")
    corr, zoom = np.zeros((total, 4)), np.ones(total)
    for i, (k0, k1) in enumerate(zip(bordas[:-1], bordas[1:])):
        m = mov[k0:k1].copy()
        m[0] = 0                                  # o corte não é movimento
        traj = np.cumsum(m, 0)
        # a suavização que deixa menos balanço depois de limitar a correção ao zoom máximo
        opcoes = []
        for sigma in SUAVIDADES:
            c = suavizar(traj, sigma * fps) - traj
            c *= fator(c, a.zoom_max, fps)[:, None]
            opcoes.append((round(balanco(traj + c, fps), 1), -sigma, c))
        resto, sigma, c = min(opcoes, key=lambda o: o[:2])
        z = max(1.0, zoom_necessario(c).max())
        corr[k0:k1], zoom[k0:k1] = c, z
        print(f"cena {i + 1}/{len(bordas) - 1} ({k0 / fps:.1f}–{k1 / fps:.1f}s): balanço {balanco(traj, fps):.1f}px "
              f"→ {resto:.1f}px, suavização {-sigma:.2f}s, zoom {z:.3f}", flush=True)

    # imagem: do original em alta, corrigida e reduzida para 1080×1920; máscara corrigida em 1080
    original = v / plano.get("video_original", "original.mov").split("/")[-1]
    ow, oh = (int(x) for x in subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries", "stream=width,height", "-of", "csv=p=0",
         str(original)], capture_output=True, text=True, check=True).stdout.strip().split(","))
    escala = ow / W
    quadros = ler(["ffmpeg", "-v", "error", "-i", str(original), "-vf",
                   "scale=in_color_matrix=bt709:in_range=tv:flags=bicubic,format=rgb24", "-fps_mode", "passthrough",
                   "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], ow, oh, 3)
    saida_v = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-framerate",
         f"{num}/{den}", "-i", "-", "-i", str(v / "video.mp4"), "-map", "0:v", "-map", "1:a",
         "-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p", "-c:v", "libx264", "-crf", "14",
         "-preset", "slow", "-g", "30", "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
         "-c:a", "copy", str(v / "video_estab.mp4")], stdin=subprocess.PIPE)
    tmp_m = v / "mascara_estab.mkv"
    saida_m = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "gray", "-s", f"{W}x{H}", "-framerate",
         f"{num}/{den}", "-i", "-", "-c:v", "libx264", "-crf", "0", "-preset", "ultrafast", "-pix_fmt", "gray",
         str(tmp_m)], stdin=subprocess.PIPE)
    n = 0
    for k, (q, m) in enumerate(zip(quadros, mascaras(v, W, H))):
        grande = cv2.warpAffine(q, matriz(corr[k], zoom[k], escala), (ow, oh), flags=cv2.INTER_CUBIC,
                                borderMode=cv2.BORDER_REPLICATE)
        saida_v.stdin.write(cv2.resize(grande, (W, H), interpolation=cv2.INTER_AREA).tobytes())
        saida_m.stdin.write(cv2.warpAffine(m, matriz(corr[k], zoom[k], 1), (W, H), flags=cv2.INTER_LINEAR,
                                           borderMode=cv2.BORDER_CONSTANT, borderValue=0).tobytes())
        n += 1
    for p in (saida_v, saida_m):
        p.stdin.close()
        p.wait()
    if n != total:
        raise SystemExit(f"{n} quadros processados, o original tem {total}")

    ff("-i", str(v / "video_estab.mp4"), "-i", str(tmp_m), "-filter_complex",
       "[1:v]format=gray[m];[0:v][m]alphamerge,format=yuva420p[o]", "-map", "[o]", "-an",
       "-fps_mode", "passthrough", "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-b:v", "0", "-crf", "22",
       "-deadline", "realtime", "-cpu-used", "8", "-row-mt", "1", "-auto-alt-ref", "0", "-g", "30",
       str(v / "recorte.webm"))
    tmp_m.unlink()
    for arq in (v / "video_estab.mp4", v / "recorte.webm"):
        n = contar(arq)
        if n != total:
            raise SystemExit(f"{arq.name}: {n} quadros, o original tem {total}")
    print(f"ok ({total} quadros, alinhado ao original):", v / "video_estab.mp4", v / "recorte.webm")


if __name__ == "__main__":
    main()
