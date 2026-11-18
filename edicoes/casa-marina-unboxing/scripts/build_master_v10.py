"""Casa Marina v10 - clean master (with colour grade, scripts/grade.py) from the re-recorded clips (wooden deck) + the old
sousplat-on-the-wooden-table shots.

Each segment: (name, source file, start seconds, duration seconds).
iPhone clips: HEVC 2160x3840 (rotated), full-range yuvj420p BT.709, 30 or 29.97 fps.
They are scaled to 1080x1920 (exact 1/2), full->limited range handled by the scaler, and
laid frame by frame on a 30 fps timeline (29.97 clips play 0.1% faster: invisible).
No colour grading.

Usage: python3 build_master_v8.py OUT.mp4  [--plan]
"""
import json
import os
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from grade import grade  # noqa: E402

W, H, FPS = 1080, 1920, 30
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NEW = os.path.join(ROOT, "raw2")
OLD = os.path.join(ROOT, "raw", "video.MOV")
FX = os.path.join(ROOT, "out", "v10", "menores_live.mp4")


def c(n):
    return os.path.join(NEW, f"IMG_{n}.MOV")


# (name, file, start_s, dur_s)
EDL = [
    # abertura (logo rapida por cima do deck, a caixa chegando)
    ("caixa_chega",       c(6847), 0.30, 2.60),
    ("adesivo",           c(6849), 1.10, 1.30),
    ("abre_caixa",        c(6850), 1.40, 1.20),
    ("papel_seda",        c(6851), 1.40, 1.50),
    # sousplat (so o momento em que ela passa a mao) -> mesa
    ("tira_sousplat_cru", c(6852), 3.40, 1.10),
    ("tira_sousplat_verm", c(6853), 3.50, 1.10),
    ("mesa_prato",        OLD, 32.6667, 1.10),
    ("mesa_vermelho",     OLD, 36.2333, 1.90),
    # tapete redondo
    ("tira_redondo_teal", c(6854), 5.30, 1.30),
    ("tira_redondo_cru",  c(6855), 4.00, 1.20),
    ("deck_redondo_cru",  c(6872), 0.50, 2.00),
    # tapete retangular
    ("tira_retang_marinho", c(6861), 4.20, 1.60),
    ("deck_retang_vermelho", c(6875), 1.40, 1.30),
    ("deck_retang_marinho", c(6876), 0.20, 2.00),
    # tapete geometrico
    ("tira_geometrico",   c(6857), 5.40, 1.60),
    ("deck_geometrico",   c(6868), 2.30, 2.20),
    # jogo de passadeira (3 pecas)
    ("tira_passadeira",   c(6859), 4.30, 1.30),
    ("deck_passadeira_jogo", c(6862), 1.40, 2.30),
    # tapete para sala
    ("deck_tapete_sala",  c(6890), 2.50, 2.00),
    # tapetes redondos menores aparecendo (stop motion com o video real estabilizado)
    ("menores_aparecem",  FX, 0.00, 3.60),
    # fecho (ovais, com a mao arrumando)
    ("oval_verde",        c(6883), 0.00, 1.30),
    ("oval_cru",          c(6883), 3.60, 1.40),
    ("oval_teal",         c(6883), 6.40, 2.20),
]


def segments():
    out, o = [], 0
    for name, f, s, d in EDL:
        n = int(round(d * FPS))
        out.append(dict(name=name, file=f, start=s, frames=n, out0=o))
        o += n
    return out, o


def decode_cmd(seg):
    f = seg["file"]
    if f in (OLD, FX):
        vf = "scale=in_color_matrix=bt709:in_range=tv:flags=accurate_rnd+full_chroma_int"
    else:
        vf = (f"scale={W}:{H}:in_color_matrix=bt709:in_range=pc:"
              "flags=lanczos+accurate_rnd+full_chroma_int")
    return ["ffmpeg", "-v", "error", "-ss", f"{seg['start']:.4f}", "-i", f, "-vf", vf,
            "-frames:v", str(seg["frames"]), "-vsync", "passthrough",
            "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]


def main():
    segs, total = segments()
    if "--plan" in sys.argv:
        for i, s in enumerate(segs):
            print(f"{i:2d} {s['name']:22s} {os.path.basename(s['file']):14s} {s['start']:6.2f}+{s['frames'] / FPS:4.2f}s"
                  f"  out {s['out0'] / FPS:6.2f}-{(s['out0'] + s['frames']) / FPS:6.2f}")
        print(f"total {total} frames = {total / FPS:.2f}s")
        json.dump(segs, open(os.path.join(ROOT, "out", "v10_segs.json"), "w"), indent=1)
        return
    out = sys.argv[1]
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-vf", "scale=out_color_matrix=bt709:out_range=tv:flags=accurate_rnd+full_chroma_int",
                            "-c:v", "libx264", "-preset", "medium", "-crf", "12", "-pix_fmt", "yuv420p",
                            "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
                            "-color_range", "tv", "-an", out], stdin=subprocess.PIPE)
    fs = W * H * 3
    for s in segs:
        p = subprocess.run(decode_cmd(s), capture_output=True, check=True)
        data = p.stdout
        got = len(data) // fs
        if got < s["frames"]:   # pad with the last frame if the clip ended early
            data += data[(got - 1) * fs: got * fs] * (s["frames"] - got)
            print("padded", s["name"], s["frames"] - got, file=sys.stderr)
        arr = np.frombuffer(data[: s["frames"] * fs], np.uint8).reshape(s["frames"], H, W, 3)
        for fr in arr:
            enc.stdin.write(grade(fr).tobytes())
        print("seg", s["name"], s["frames"], file=sys.stderr, flush=True)
    enc.stdin.close()
    enc.wait()
    print("master", out, total, "frames")


if __name__ == "__main__":
    main()
