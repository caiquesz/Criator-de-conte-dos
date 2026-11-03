"""Corrige o enquadramento de takes gravados sem tripé e emenda tudo, como se a câmera estivesse parada.

Uso: python3 scripts/enquadrar.py PASTA [--olhos-y 0.38] [--zoom-max 1.6] [--modelo yunet.onnx]

Lê PASTA/takes/*.mov (na ordem do nome) e escreve PASTA/renders/enquadrado.mp4.

Para cada take:
  1. a posição da câmera é medida em cada quadro contra um quadro de referência do take
     (alinhamento ECC do fundo, fora da pessoa) e o movimento é removido por inteiro: o fundo fica parado, como num tripé; o movimento da própria
     pessoa continua natural;
  2. o rosto é achado em todos os quadros (YuNet) e, já no quadro estabilizado, vale a
     mediana do ponto entre os olhos e da distância entre os olhos.
Depois, um enquadramento só para todos os takes: o ponto entre os olhos no centro da
largura e a --olhos-y da altura, e a mesma distância entre os olhos em todos (o mesmo
tamanho de rosto). Só se aproxima (nunca se afasta), com o menor zoom que cobre todos os
takes sem borda; a imagem vem do original em 4K, então zoom até 2× não perde resolução em
1080×1920. Sem distorção: só escala uniforme, giro e deslocamento.

O áudio de cada take entra como está (só 4 ms de rampa nas emendas, para não estalar) e
cada take mantém a duração, a velocidade e a ordem.
"""

import argparse
import json
import subprocess
from pathlib import Path

import cv2
import numpy as np

W, H = 1080, 1920          # saída
AW, AH = 540, 960          # análise
FPS = 30
TAXA = 48000


def ler(cmd, w, h, canais):
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    tam = w * h * canais
    while True:
        b = p.stdout.read(tam)
        if len(b) < tam:
            break
        yield np.frombuffer(b, np.uint8).reshape(h, w, canais)
    p.wait()


def quadros(take, w, h):
    """Quadros do take já girados, a 30 fps constantes, em RGB (faixa cheia do iPhone)."""
    return ler(["ffmpeg", "-v", "error", "-i", str(take), "-vf",
                f"fps={FPS},scale={w}:{h}:flags=bicubic:in_range=pc:in_color_matrix=bt709,format=rgb24",
                "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], w, h, 3)


def mascara_fundo(caixa, k, w_img=AW, h_img=AH):
    """Tudo menos a pessoa, estimada a partir do rosto: cabeça com cabelo (estreita) e, do
    pescoço para baixo, tronco e braços (larga)."""
    m = np.full((h_img, w_img), 255, np.uint8)
    if caixa is not None and not np.isnan(caixa[0]):
        e = w_img / W
        x, y, w, h = caixa * e
        cx = x + w / 2
        topo, queixo = int(max(0, y - 0.55 * h)), int(min(h_img, y + 1.1 * h))
        m[topo:queixo, int(max(0, cx - 1.05 * w)):int(min(w_img, cx + 1.05 * w))] = 0
        m[queixo:, int(max(0, cx - 1.75 * w)):int(min(w_img, cx + 1.75 * w))] = 0
    return m


def analisar(take, detector):
    """Rosto (olhos) em cada quadro e posição da câmera em cada quadro em relação a um quadro de
    referência do take (o do meio), medida direto contra ele (o erro não se acumula) por
    alinhamento ECC do fundo: usa todo degrau de luz do fundo, não só cantos, então funciona
    mesmo com parede lisa."""
    k = W / AW
    olhos, dist, caixas, cinzas = [], [], [], []
    for rgb in quadros(take, AW, AH):
        bgr = np.ascontiguousarray(rgb[:, :, ::-1])
        cinzas.append(cv2.resize(cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY), (AW // 2, AH // 2), interpolation=cv2.INTER_AREA))
        _, faces = detector.detect(bgr)
        if faces is not None and len(faces):
            f = faces[np.argmax(faces[:, -1])]
            re, le = f[4:6], f[6:8]
            olhos.append(((re + le) / 2) * k)
            dist.append(np.linalg.norm(le - re) * k)
            caixas.append(f[:4] * k)
        else:
            olhos.append([np.nan, np.nan]); dist.append(np.nan); caixas.append(np.array([np.nan] * 4))
    n = len(cinzas)
    r = n // 2
    sw, sh = AW // 2, AH // 2
    ks = W / sw
    ref = cinzas[r].astype(np.float32)
    # fundo do quadro de referência, sem a pessoa em nenhum quadro do take (ela se mexe)
    mask = mascara_fundo(caixas[r], k, sw, sh)
    for cx in caixas[::5]:
        mask &= mascara_fundo(cx, k, sw, sh)
    crit = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 80, 1e-6)
    c = np.array([sw / 2, sh / 2])
    pos, qual = [np.zeros(4) for _ in range(n)], [1.0] * n
    for ordem in (range(r + 1, n), range(r - 1, -1, -1)):
        warp = np.eye(2, 3, dtype=np.float32)
        for j in ordem:
            try:
                cc, warp = cv2.findTransformECC(ref, cinzas[j].astype(np.float32), warp, cv2.MOTION_EUCLIDEAN, crit, mask, 5)
            except cv2.error:
                cc = 0.0
            qual[j] = float(cc)
            dc = warp[:, :2] @ c + warp[:, 2] - c
            pos[j] = np.array([dc[0] * ks, dc[1] * ks, np.arctan2(warp[1, 0], warp[0, 0]), 0.0])
    return np.array(olhos), np.array(dist), np.array(caixas), np.array(pos), float(np.median(qual)), int((mask > 0).mean() * 100)


def suavizar(x, sigma):
    r = int(3 * sigma) + 1
    kern = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2)
    kern /= kern.sum()
    return np.stack([np.convolve(np.pad(x[:, i], r, mode="edge"), kern, "valid") for i in range(x.shape[1])], 1)


def rot(th):
    return np.array([[np.cos(th), -np.sin(th)], [np.sin(th), np.cos(th)]])


def estab(corr):
    """2×3 da estabilização: p' = c + s·R(θ)·(p − c) + t, com corr = (tx, ty, θ, log s)."""
    tx, ty, th, ls = corr
    A = np.exp(ls) * rot(th)
    c = np.array([W / 2, H / 2])
    return np.hstack([A, (c + np.array([tx, ty]) - A @ c)[:, None]])


def compor(F, S):
    return np.vstack([F, [0, 0, 1]]) @ np.vstack([S, [0, 0, 1]])


def enquadra(z, E, alvo):
    """2×3 do enquadramento: q = alvo + z·(p − E)."""
    return np.hstack([z * np.eye(2), (np.array(alvo) - z * np.array(E))[:, None]])


def cabe(M):
    """True se a saída inteira vem de dentro do quadro de origem (sem borda)."""
    Mi = np.linalg.inv(np.vstack([np.asarray(M)[:2], [0, 0, 1]]))[:2]
    cantos = np.array([[0, 0, 1], [W, 0, 1], [W, H, 1], [0, H, 1]], float).T
    p = Mi @ cantos
    return bool((p[0] >= -0.5).all() and (p[0] <= W + 0.5).all() and (p[1] >= -0.5).all() and (p[1] <= H + 0.5).all())


def zoom_minimo(Ss, E, alvo):
    lo, hi = 1.0, 4.0
    for _ in range(40):
        z = (lo + hi) / 2
        if all(cabe(compor(enquadra(z, E, alvo), S)) for S in Ss):
            hi = z
        else:
            lo = z
    return hi


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pasta")
    ap.add_argument("--olhos-y", type=float, default=0.38, help="altura dos olhos na tela (fração da altura)")
    ap.add_argument("--zoom-max", type=float, default=1.6)
    ap.add_argument("--analise", action="store_true", help="só mede e mostra o zoom de cada take, sem renderizar")
    ap.add_argument("--modelo", default=str(Path(__file__).parent / "modelos" / "face_detection_yunet_2023mar.onnx"))
    a = ap.parse_args()

    pasta = Path(a.pasta).resolve()
    takes = sorted((pasta / "takes").glob("*.mov"))
    detector = cv2.FaceDetectorYN.create(a.modelo, "", (AW, AH), 0.6, 0.3, 50)
    alvo = (W / 2, a.olhos_y * H)

    dados = []
    for t in takes:
        olhos, dist, caixas, pos, qualidade, area = analisar(t, detector)
        n = len(pos)
        traj = suavizar(pos, 1.5)                                # posição da câmera (sem o ruído da medida)
        corr = np.median(traj, 0) - traj                         # tripé: devolve cada quadro à posição mediana
        Ss = [estab(c) for c in corr]
        ok = ~np.isnan(dist)
        if ok.sum() < n * 0.5:
            raise SystemExit(f"{t.name}: rosto achado em só {ok.sum()} de {n} quadros")
        # olhos no quadro estabilizado
        E = np.array([S[:, :2] @ o + S[:, 2] for S, o, v in zip(Ss, olhos, ok) if v])
        D = np.array([d * np.exp(c[3]) for d, c, v in zip(dist, corr, ok) if v])
        Em, Dm = np.median(E, 0), np.median(D)
        zmin = zoom_minimo(Ss, Em, alvo)
        bal = np.hypot(*(pos - suavizar(pos, 8))[:, :2].T).mean()
        dados.append(dict(take=t, n=n, Ss=Ss, E=Em, D=Dm, zmin=zmin, deriva=float(np.abs(corr[:, :2]).max()),
                          tremor=float(bal), rosto=float(ok.mean())))
        print(f"{t.name}: {n} quadros, rosto em {ok.mean() * 100:.0f}%, olhos em ({Em[0]:.0f}, {Em[1]:.0f}), "
              f"entre os olhos {Dm:.0f}px, câmera mexe até {dados[-1]['deriva']:.0f}px (tremor {bal:.1f}px), "
              f"zoom mínimo {zmin:.3f} (alinhamento {qualidade:.3f}, fundo {area}% do quadro)", flush=True)

    # um tamanho de rosto para todos: o menor que todos os takes alcançam sem borda
    Dalvo = max(d["D"] * d["zmin"] for d in dados)
    zs = [Dalvo / d["D"] for d in dados]
    if max(zs) > a.zoom_max:
        # um take muito longe puxaria todos para perto demais: limita e deixa esse um pouco menor
        Dalvo = max(d["D"] * d["zmin"] for d in dados if d["D"] * a.zoom_max >= d["D"] * d["zmin"])
        zs = [min(max(Dalvo / d["D"], d["zmin"]), a.zoom_max) for d in dados]
    print(f"rosto padrão: {Dalvo:.0f}px entre os olhos; olhos em ({alvo[0]:.0f}, {alvo[1]:.0f})")
    print("zoom por take:", " ".join(f"{z:.3f}" for z in zs))
    if a.analise:
        return

    renders = pasta / "renders"
    renders.mkdir(exist_ok=True)
    partes, audios, relatorio = [], [], []
    for d, z in zip(dados, zs):
        F = enquadra(z, d["E"], alvo)
        saida = renders / f"take-{d['take'].stem}.mp4"
        enc = subprocess.Popen(
            ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-framerate", str(FPS),
             "-i", "-", "-vf", "scale=out_range=tv:out_color_matrix=bt709,format=yuv420p", "-c:v", "libx264",
             "-crf", "15", "-preset", "slow", "-g", "30", "-color_primaries", "bt709", "-color_trc", "bt709",
             "-colorspace", "bt709", "-color_range", "tv", "-video_track_timescale", "15360", str(saida)],
            stdin=subprocess.PIPE)
        n = 0
        for rgb, S in zip(quadros(d["take"], 2 * W, 2 * H), d["Ss"]):
            M = compor(F, S)[:2].copy()
            M[:, 2] *= 2                                   # em 4K: mesma transformação, coordenadas ×2
            grande = cv2.warpAffine(rgb, M, (2 * W, 2 * H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
            enc.stdin.write(cv2.resize(grande, (W, H), interpolation=cv2.INTER_AREA).tobytes())
            n += 1
        enc.stdin.close(); enc.wait()
        if n != d["n"]:
            raise SystemExit(f"{d['take'].name}: {n} quadros no 4K, {d['n']} na análise")
        partes.append(saida)
        # áudio do take, do começo, com a duração exata dos quadros
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(d["take"]), "-map", "0:a:0", "-ac", "1", "-ar", str(TAXA),
                              "-f", "f32le", "-"], capture_output=True, check=True).stdout
        x = np.frombuffer(raw, np.float32).copy()
        alvo_n = round(n / FPS * TAXA)
        x = x[:alvo_n] if len(x) >= alvo_n else np.pad(x, (0, alvo_n - len(x)))
        r = int(0.004 * TAXA)
        x[:r] *= np.linspace(0, 1, r); x[-r:] *= np.linspace(1, 0, r)
        audios.append(x)
        relatorio.append({"take": d["take"].name, "quadros": n, "zoom": round(z, 3), "zoom_minimo": round(d["zmin"], 3),
                          "olhos_antes": [round(v) for v in d["E"]], "entre_olhos_antes": round(d["D"]),
                          "camera_mexia_px": round(d["deriva"]), "tremor_px": round(d["tremor"], 1)})
        print(f"{d['take'].name}: zoom {z:.3f}, {n} quadros", flush=True)

    lista = renders / "takes.txt"
    lista.write_text("".join(f"file '{p.name}'\n" for p in partes))
    wav = renders / "audio.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(TAXA), "-ac", "1", "-i", "-",
                    "-c:a", "pcm_f32le", str(wav)], input=np.concatenate(audios).astype(np.float32).tobytes(), check=True)
    final = renders / "enquadrado.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lista), "-i", str(wav),
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart",
                    "-shortest", str(final)], check=True)
    wav.unlink(); lista.unlink()
    for p in partes:
        p.unlink()
    (pasta / "enquadramento.json").write_text(json.dumps({"olhos_alvo": alvo, "entre_olhos_alvo": round(Dalvo, 1),
                                                          "takes": relatorio}, ensure_ascii=False, indent=1))
    print("ok:", final)


if __name__ == "__main__":
    main()
