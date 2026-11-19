"""Rastreia uma superfície plana do vídeo (parede, fachada, chão) para o texto em perspectiva.

Uso:
  python3 scripts/rastrear.py PASTA SAIDA.json --de T0 --ate T1 --ref T --quad "x,y x,y x,y x,y"
  python3 scripts/rastrear.py PASTA SAIDA.json --de T0 --ate T1 --ref T --quad-de OUTRO.json

O quad são os quatro cantos (superior esquerdo, superior direito, inferior direito,
inferior esquerdo, em px de 1080×1920) de um retângulo da superfície no quadro --ref;
o texto em perspectiva é desenhado dentro dele. Com --quad-de, o quad vem de outro
rastreio da mesma superfície (outra tomada): a superfície é reconhecida nas duas
tomadas por pontos em comum e o quad é levado para o quadro --ref desta.

Os pontos da superfície são seguidos quadro a quadro (fluxo óptico) a partir do
quadro de referência, para frente e para trás; a cada quadro, a homografia
referência → quadro vem de todos os pontos ainda vivos (RANSAC), então o erro
não se acumula. A pessoa recortada (alfa de recorte.webm) não entra no rastreio.

Grava, para cada quadro do vídeo entre T0 e T1, onde caem os quatro cantos do quad.
"""

import argparse
import json
import subprocess
from pathlib import Path

import cv2
import numpy as np

W, H = 540, 960          # resolução do rastreio
ESCALA = 1080 / W


def taxa(video):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries", "stream=r_frame_rate",
                        "-of", "csv=p=0", str(video)], capture_output=True, text=True, check=True).stdout.strip()
    num, den = (int(x) for x in r.split("/"))
    return num, den


def quadros(video, k0, n, alfa=False):
    """n quadros a partir do quadro k0, em cinza (ou o alfa, para o recorte)."""
    num, den = taxa(video)
    entrada = ["-c:v", "libvpx-vp9"] if alfa else []
    filtro = ("alphaextract," if alfa else "") + f"select='between(n\\,{k0}\\,{k0 + n - 1})',scale={W}:{H},format=gray"
    raw = subprocess.run(["ffmpeg", "-v", "error", *entrada, "-i", str(video), "-vf", filtro, "-fps_mode", "passthrough",
                          "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True, check=True).stdout
    q = np.frombuffer(raw, np.uint8).reshape(-1, H, W)
    if len(q) != n:
        raise SystemExit(f"esperava {n} quadros de {video.name}, vieram {len(q)}")
    return q


def mascara_roi(poligono, pessoa):
    m = np.zeros((H, W), np.uint8)
    cv2.fillPoly(m, [np.round(np.array(poligono) / ESCALA).astype(np.int32)], 255)
    pessoa = cv2.dilate((pessoa > 60).astype(np.uint8) * 255, np.ones((25, 25), np.uint8))
    m[pessoa > 0] = 0
    return m


def detectar(img, mascara, n=500):
    p = cv2.goodFeaturesToTrack(img, maxCorners=n, qualityLevel=0.008, minDistance=6, mask=mascara, blockSize=7)
    return np.zeros((0, 2), np.float32) if p is None else p.reshape(-1, 2)


def aplicar(Hm, pts):
    p = cv2.perspectiveTransform(np.asarray(pts, np.float64).reshape(-1, 1, 2), Hm)
    return p.reshape(-1, 2)


def seguir(qs, ps, ir, ordem, roi_ref):
    """Homografia referência → quadro para cada quadro, andando a partir de ir na ordem dada."""
    lk = dict(winSize=(25, 25), maxLevel=4, criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 40, 0.01))
    ref = detectar(qs[ir], mascara_roi(roi_ref, ps[ir]))
    cur, Hk = ref.copy(), np.eye(3)
    saida = {ir: np.eye(3)}
    anterior = ir
    for k in ordem:
        nxt, st, _ = cv2.calcOpticalFlowPyrLK(qs[anterior], qs[k], cur.astype(np.float32), None, **lk)
        volta, st2, _ = cv2.calcOpticalFlowPyrLK(qs[k], qs[anterior], nxt, None, **lk)
        ok = (st.ravel() == 1) & (st2.ravel() == 1) & (np.linalg.norm(volta - cur, axis=1) < 0.8)
        # fora da pessoa (com folga) e dentro do quadro
        pessoa = cv2.dilate((ps[k] > 60).astype(np.uint8), np.ones((21, 21), np.uint8))
        xi, yi = np.clip(nxt[:, 0], 0, W - 1).astype(int), np.clip(nxt[:, 1], 0, H - 1).astype(int)
        ok &= (pessoa[yi, xi] == 0) & (nxt[:, 0] > 2) & (nxt[:, 0] < W - 3) & (nxt[:, 1] > 2) & (nxt[:, 1] < H - 3)
        ref, cur = ref[ok], nxt[ok]
        if len(ref) < 12:
            raise SystemExit(f"rastreio perdido no quadro {k} ({len(ref)} pontos)")
        Hk, inl = cv2.findHomography(ref, cur, cv2.RANSAC, 1.5, maxIters=4000, confidence=0.999)
        inl = inl.ravel() == 1
        ref, cur = ref[inl], cur[inl]
        saida[k] = Hk
        # repõe pontos quando sobram poucos: detecta no quadro atual e leva para a referência
        if len(ref) < 220:
            roi_k = aplicar(Hk, np.array(roi_ref) / ESCALA) * ESCALA
            novos = detectar(qs[k], mascara_roi(roi_k, ps[k]), 500)
            if len(novos):
                longe = np.min(np.linalg.norm(novos[:, None] - cur[None], axis=2), axis=1) > 6 if len(cur) else np.ones(len(novos), bool)
                novos = novos[longe]
                ref = np.vstack([ref, aplicar(np.linalg.inv(Hk), novos).astype(np.float32)])
                cur = np.vstack([cur, novos])
        anterior = k
    return saida


def transferir_quad(origem, qs_ref, roi):
    """Leva o quad de outro rastreio (outra tomada) para este quadro de referência."""
    o = json.loads(Path(origem).read_text())
    video = Path(o["video"])
    img_o = quadros(video, o["k_ref"], 1)[0]
    sift = cv2.SIFT_create(4000)
    m_o = np.zeros((H, W), np.uint8)
    cv2.fillPoly(m_o, [np.round(np.array(o["roi"]) / ESCALA).astype(np.int32)], 255)
    m_d = np.zeros((H, W), np.uint8)
    cv2.fillPoly(m_d, [np.round(np.array(roi) / ESCALA).astype(np.int32)], 255)
    ko, do = sift.detectAndCompute(img_o, m_o)
    kd, dd = sift.detectAndCompute(qs_ref, m_d)
    pares = cv2.BFMatcher().knnMatch(do, dd, k=2)
    bons = [a for a, b in pares if a.distance < 0.72 * b.distance]
    po = np.float32([ko[m.queryIdx].pt for m in bons])
    pd = np.float32([kd[m.trainIdx].pt for m in bons])
    Hm, inl = cv2.findHomography(po, pd, cv2.RANSAC, 3.0)
    print(f"tomadas ligadas por {int(inl.sum())} de {len(bons)} pontos em comum")
    if inl.sum() < 25:
        raise SystemExit("poucos pontos em comum entre as tomadas; marque o quad à mão (--quad)")
    return (aplicar(Hm, np.array(o["quad"]) / ESCALA) * ESCALA).round(1).tolist()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pasta")
    ap.add_argument("saida")
    ap.add_argument("--de", type=float, required=True)
    ap.add_argument("--ate", type=float, required=True)
    ap.add_argument("--ref", type=float, required=True)
    ap.add_argument("--quad")
    ap.add_argument("--quad-de")
    ap.add_argument("--roi", help="polígono da superfície no quadro --ref (padrão: o próprio quad)")
    a = ap.parse_args()

    pasta = Path(a.pasta).resolve()
    plano = json.loads((pasta / "plano.json").read_text())
    video, recorte = pasta / plano["video"], pasta / plano["recorte"]
    num, den = taxa(video)
    fps = num / den
    k0, k1 = int(np.ceil(a.de * fps - 1e-6)), int(np.floor(a.ate * fps + 1e-6))
    kr = int(round(a.ref * fps))
    n = k1 - k0 + 1
    qs, ps = quadros(video, k0, n), quadros(recorte, k0, n, alfa=True)
    par = lambda s: [[float(v) for v in p.split(",")] for p in s.split()]
    roi = par(a.roi) if a.roi else None
    if a.quad_de:
        quad = transferir_quad(a.quad_de, qs[kr - k0], roi)
        print("quad levado para esta tomada:", " ".join(f"{x:.0f},{y:.0f}" for x, y in quad))
    else:
        quad = par(a.quad)
    roi = roi or quad

    i = kr - k0
    hs = seguir(qs, ps, i, list(range(i + 1, n)), roi)
    hs.update(seguir(qs, ps, i, list(range(i - 1, -1, -1)), roi))
    cantos = {k0 + j: (aplicar(hs[j], np.array(quad) / ESCALA) * ESCALA).round(2).tolist() for j in range(n)}
    Path(a.saida).write_text(json.dumps({
        "video": str(video), "fps": [num, den], "k0": k0, "k1": k1, "k_ref": kr,
        "quad": quad, "roi": roi, "cantos": cantos}))
    desloc = [np.abs(np.array(cantos[k]) - np.array(quad)).max() for k in cantos]
    print(f"ok: {n} quadros ({k0}–{k1}), maior deslocamento do quad {max(desloc):.0f} px -> {a.saida}")


if __name__ == "__main__":
    main()
