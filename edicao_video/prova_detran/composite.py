"""Composição: vídeo bruto (com cortes, zoom, push) + camadas PNG (papel amassando, overlay) + áudio.
uso:
  python3 composite.py <bruto.mov> <camada1_dir,camada2_dir,...> <audio.wav> <saida.mp4>
  python3 composite.py <bruto.mov> <camadas> --preview <dir> <f1,f2,...>
As camadas são aplicadas na ordem dada (a última fica por cima). Quadro sem PNG numa camada = nada.
"""
import json, os, subprocess, sys
import numpy as np
import cv2

HERE = os.path.dirname(os.path.abspath(__file__))
TL = json.load(open(os.path.join(HERE, "timeline.json")))
W, H, FPS = 1080, 1920, TL["fps"]
CX, CY = 540, 1000


def decoder(src):
    sel = "+".join(f"between(n\\,{a}\\,{b - 1})" for a, b in TL["keep"])
    vf = f"fps={FPS},select='{sel}',setpts=N/{FPS}/TB,eq=contrast=1.05:saturation=1.08:gamma=0.98"
    cmd = ["ffmpeg", "-v", "error", "-i", src, "-map", "0:v:0", "-vf", vf, "-f", "rawvideo", "-pix_fmt", "bgr24", "-"]
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=W * H * 3 * 4)


def blend(img, ov):
    if ov is None:
        return img
    if ov.ndim == 3 and ov.shape[2] == 3:
        return ov
    a = ov[:, :, 3:4].astype(np.float32) / 255.0
    if a.max() == 0:
        return img
    return (img.astype(np.float32) * (1 - a) + ov[:, :, :3].astype(np.float32) * a + 0.5).astype(np.uint8)


def process(frame, f, layers):
    z, vx, sp = TL["zoom"][f], TL["videoX"][f], TL["speed"][f]
    img = frame
    if abs(vx) >= 1079.5:
        img = np.zeros_like(frame)
    elif abs(z - 1) > 1e-4 or abs(vx) > 0.01:
        M = np.float32([[z, 0, (1 - z) * CX + vx], [0, z, (1 - z) * CY]])
        img = cv2.warpAffine(frame, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
    if sp > 1 and abs(vx) < 1079.5:
        k = int(sp * 0.7) | 1
        img = cv2.blur(img, (k, 1))
    for d in layers:
        p = os.path.join(d, f"{f:05d}.png")
        if os.path.exists(p):
            img = blend(img, cv2.imread(p, cv2.IMREAD_UNCHANGED))
    return img


def main():
    src, layers = sys.argv[1], [d for d in sys.argv[2].split(",") if d]
    dec = decoder(src)
    n = TL["nframes"]
    if sys.argv[3] == "--preview":
        pdir = sys.argv[4]; os.makedirs(pdir, exist_ok=True)
        want = set(int(x) for x in sys.argv[5].split(","))
        for f in range(n):
            buf = dec.stdout.read(W * H * 3)
            if not buf:
                break
            if f in want:
                fr = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
                cv2.imwrite(os.path.join(pdir, f"p{f:05d}.jpg"), process(fr, f, layers), [cv2.IMWRITE_JPEG_QUALITY, 92])
            if f >= max(want):
                break
        dec.kill(); return
    audio, out = sys.argv[3], sys.argv[4]
    enc = subprocess.Popen([
        "ffmpeg", "-v", "error", "-y",
        "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-i", audio, "-map", "0:v", "-map", "1:a",
        "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p",
        "-profile:v", "high", "-level", "4.2", "-r", str(FPS),
        "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
        "-c:a", "aac", "-b:a", "256k", "-ar", "48000",
        "-shortest", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    for f in range(n):
        buf = dec.stdout.read(W * H * 3)
        if not buf:
            print("fim antecipado no frame", f); break
        fr = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
        enc.stdin.write(process(fr, f, layers).tobytes())
        if f % 150 == 0:
            print("frame", f, "/", n, flush=True)
    enc.stdin.close(); enc.wait(); dec.wait()
    print("ok", out)


if __name__ == "__main__":
    main()
