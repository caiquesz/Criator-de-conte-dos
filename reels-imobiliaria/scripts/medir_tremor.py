"""Mede o tremor de um trecho: escala e deslocamento quadro a quadro (ECC afim), e quanto eles vão e voltam.

Uso: python3 medir_tremor.py VIDEO INICIO FIM X Y LARGURA ALTURA [-v]  (a região: de preferência algo parado, como
     uma foto ou o fundo; o rosto mexendo entra na conta)
Um zoom lento suave dá escala quase constante e "trocas" perto de 0; o zoompan do ffmpeg dava dy indo e voltando
±2 px a cada quadro (Caso de paciente v2, 17/11).
"""
import subprocess, sys
import cv2, numpy as np
arq, a, b, x0, y0, w, h = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), *map(int, sys.argv[4:8])
cmd = ["ffmpeg", "-v", "error", "-ss", str(a), "-i", arq, "-t", str(b - a), "-vf", f"crop={w}:{h}:{x0}:{y0},format=gray",
       "-f", "rawvideo", "-"]
raw = subprocess.run(cmd, capture_output=True).stdout
fr = np.frombuffer(raw, np.uint8).reshape(-1, h, w).astype(np.float32)
esc, dx, dy = [], [], []
for i in range(1, len(fr)):
    M = np.eye(2, 3, dtype=np.float32)
    try:
        _, M = cv2.findTransformECC(fr[i - 1], fr[i], M, cv2.MOTION_AFFINE,
                                    (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 200, 1e-6), None, 5)
    except cv2.error:
        M = np.full((2, 3), np.nan, np.float32)
    esc.append((M[0, 0] + M[1, 1]) / 2 - 1); dx.append(M[0, 2]); dy.append(M[1, 2])
esc, dx, dy = map(np.array, (esc, dx, dy))
def ida_volta(v):
    s = np.sign(v[np.abs(v) > 1e-4]); return int(np.sum(s[1:] != s[:-1]))
print(f"{len(fr)} quadros; escala/quadro média {np.nanmean(esc)*1e4:.2f}e-4 dp {np.nanstd(esc)*1e4:.2f}e-4 trocas {ida_volta(esc)};"
      f" dx dp {np.nanstd(dx):.3f}px trocas {ida_volta(dx)}; dy dp {np.nanstd(dy):.3f}px trocas {ida_volta(dy)}")
if "-v" in sys.argv:
    print("escala e-4:", " ".join(f"{e*1e4:.1f}" for e in esc[:40]))
    print("dy:", " ".join(f"{e:.2f}" for e in dy[:40]))
