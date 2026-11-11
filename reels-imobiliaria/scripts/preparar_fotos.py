"""Prepara as fotos de um projeto (antes e depois, famosas, resultados) para o gerar.py.

Uso: python3 scripts/preparar_fotos.py PASTA_DO_PROJETO

1. Cada foto de PASTA/fotos-originais/ (JPG, PNG, WEBP ou HEIC, como chegou da página de envio)
   vira PASTA/assets/fotos/<nome>.jpg: girada como foi tirada (EXIF), em RGB, com no máximo
   2400 px no lado maior. Fotos já em assets/fotos/ também entram.
2. Em cada foto, o rosto (YuNet): o gerar.py enquadra pelo rosto e, no antes e depois, deixa
   o rosto do mesmo tamanho nas duas fotos.
3. Em cada tela dividida do plano.json, a altura dos olhos da pessoa no vídeo durante aquele
   trecho: o vídeo desce o quanto precisa para o rosto ficar na metade de baixo.

Escreve PASTA/fotos.json.
"""

import json
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps

try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except ImportError:  # sem HEIC: as outras fotos seguem
    pillow_heif = None

MODELO = Path(__file__).parent / "modelos" / "face_detection_yunet_2023mar.onnx"
LADO_MAX = 2400
EXTENSOES = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"}


def converter(origem, destino):
    with Image.open(origem) as im:
        im = ImageOps.exif_transpose(im).convert("RGB")
        if max(im.size) > LADO_MAX:
            im.thumbnail((LADO_MAX, LADO_MAX), Image.LANCZOS)
        im.save(destino, "JPEG", quality=92)


def rosto(detector, caminho):
    """Maior rosto da foto, [x, y, w, h] em px da foto, ou None."""
    img = cv2.imread(str(caminho))
    h, w = img.shape[:2]
    e = min(1.0, 1280 / max(w, h))
    peq = cv2.resize(img, (round(w * e), round(h * e)), interpolation=cv2.INTER_AREA) if e < 1 else img
    detector.setInputSize((peq.shape[1], peq.shape[0]))
    _, faces = detector.detect(peq)
    if faces is None or not len(faces):
        return None
    f = faces[np.argmax(faces[:, 2] * faces[:, 3])]
    return [round(float(v) / e, 1) for v in f[:4]]


def olhos_no_video(detector, video, inicio, fim):
    """Altura mediana dos olhos (px em 1080×1920) entre inicio e fim, ou None."""
    w, h = 540, 960
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{inicio:.3f}", "-t", f"{max(0.5, fim - inicio):.3f}", "-i", str(video),
                          "-vf", f"fps=3,scale={w}:{h}", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
                         capture_output=True, check=True).stdout
    quadros = np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3)
    detector.setInputSize((w, h))
    ys = []
    for q in quadros:
        _, faces = detector.detect(np.ascontiguousarray(q))
        if faces is not None and len(faces):
            f = faces[np.argmax(faces[:, -1])]
            ys.append((f[5] + f[7]) / 2 * (1920 / h))
    return float(np.median(ys)) if ys else None


def main():
    pasta = Path(sys.argv[1]).resolve()
    originais, saida = pasta / "fotos-originais", pasta / "assets" / "fotos"
    saida.mkdir(parents=True, exist_ok=True)
    if originais.exists():
        for arq in sorted(originais.iterdir()):
            if arq.suffix.lower() not in EXTENSOES:
                continue
            if arq.suffix.lower() in (".heic", ".heif") and pillow_heif is None:
                print(f"{arq.name}: HEIC precisa do pillow-heif (pip install pillow-heif)")
                continue
            destino = saida / (arq.stem + ".jpg")
            if not destino.exists() or destino.stat().st_mtime < arq.stat().st_mtime:
                converter(arq, destino)

    detector = cv2.FaceDetectorYN.create(str(MODELO), "", (320, 320), 0.6, 0.3, 50)
    fotos = {}
    for arq in sorted(saida.iterdir()):
        if arq.suffix.lower() not in (".jpg", ".jpeg", ".png", ".webp"):
            continue
        with Image.open(arq) as im:
            largura, altura = im.size
        r = rosto(detector, arq)
        chave = f"assets/fotos/{arq.name}"
        fotos[chave] = {"largura": largura, "altura": altura, "rosto": r}
        print(f"{chave}: {largura}×{altura}, " + (f"rosto {r[2]:.0f}×{r[3]:.0f} px em ({r[0]:.0f}, {r[1]:.0f})" if r else "sem rosto (enquadra pelo centro)"))

    divididas = {}
    plano_arq = pasta / "plano.json"
    if plano_arq.exists():
        plano = json.loads(plano_arq.read_text())
        video = pasta / plano["video"]
        for f in plano.get("fotos", []):
            if f["layout"] != "dividida":
                continue
            y = olhos_no_video(detector, video, f["inicio"], f["fim"])
            if y is not None:
                divididas[f["id"]] = {"olhos_y": round(y)}
                print(f"tela dividida {f['id']}: olhos a {y:.0f} px")
        for f in plano.get("fotos", []):
            for im in f["imagens"]:
                src = im if isinstance(im, str) else im["src"]
                if src not in fotos:
                    print(f"aviso: {f['id']} usa {src}, que não está em assets/fotos/")
    (pasta / "fotos.json").write_text(json.dumps({"fotos": fotos, "divididas": divididas}, ensure_ascii=False, indent=1))
    print("ok:", pasta / "fotos.json")


if __name__ == "__main__":
    main()
