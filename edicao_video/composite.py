"""Composição final: vídeo bruto (com corte do silêncio, zoom, push) + overlay PNG + áudio.
uso:
  python3 composite.py <bruto.mov> <overlay_dir> <audio.wav> <saida.mp4>
  python3 composite.py <bruto.mov> <overlay_dir> --preview <dir> <f1,f2,...>
"""
import json, os, subprocess, sys
import numpy as np
import cv2

HERE = os.path.dirname(os.path.abspath(__file__))
TL = json.load(open(os.path.join(HERE, "timeline.json")))
W, H, FPS = 1080, 1920, TL["fps"]
CA, CB = TL["cut"]
CX, CY = 540, 980          # centro do zoom (corpo do Alexandre)


def decoder(src):
    vf = (f"select='not(between(n\\,{CA}\\,{CB - 1}))',setpts=N/{FPS}/TB,"
          "eq=contrast=1.05:saturation=1.07:gamma=0.98")
    cmd = ["ffmpeg", "-v", "error", "-i", src, "-vf", vf, "-f", "rawvideo", "-pix_fmt", "bgr24", "-"]
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=W * H * 3 * 4)


def process(frame, f, ov_dir):
    z = TL["zoom"][f]
    vx = TL["videoX"][f]
    sp = TL["speed"][f]
    img = frame
    if vx <= -1079.5:
        img = np.zeros_like(frame)
    elif abs(z - 1) > 1e-4 or abs(vx) > 0.01:
        M = np.float32([[z, 0, (1 - z) * CX + vx], [0, z, (1 - z) * CY]])
        img = cv2.warpAffine(frame, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
    if sp > 1 and vx > -1079.5:
        k = int(sp * 0.7) | 1
        img = cv2.blur(img, (k, 1))
    ov = cv2.imread(os.path.join(ov_dir, f"{f:05d}.png"), cv2.IMREAD_UNCHANGED)
    if ov is not None and ov.ndim == 3 and ov.shape[2] == 3:
        img = ov
    elif ov is not None:
        a = ov[:, :, 3:4].astype(np.float32) / 255.0
        img = (img.astype(np.float32) * (1 - a) + ov[:, :, :3].astype(np.float32) * a + 0.5).astype(np.uint8)
    return img


def main():
    src, ov_dir = sys.argv[1], sys.argv[2]
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
                cv2.imwrite(os.path.join(pdir, f"p{f:05d}.jpg"), process(fr, f, ov_dir), [cv2.IMWRITE_JPEG_QUALITY, 92])
            if f >= max(want):
                break
        dec.kill(); return
    audio, out = sys.argv[3], sys.argv[4]
    enc = subprocess.Popen([
        "ffmpeg", "-v", "error", "-y",
        "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-i", audio,
        "-map", "0:v", "-map", "1:a",
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
        enc.stdin.write(process(fr, f, ov_dir).tobytes())
        if f % 150 == 0:
            print("frame", f, "/", n, flush=True)
    enc.stdin.close(); enc.wait(); dec.wait()
    print("ok", out)


if __name__ == "__main__":
    main()
