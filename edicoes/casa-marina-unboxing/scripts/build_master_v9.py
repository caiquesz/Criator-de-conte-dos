"""Casa Marina v9 - clean master from the re-recorded clips (wooden deck) + the old
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

W, H, FPS = 1080, 1920, 30
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NEW = os.path.join(ROOT, "raw2")
OLD = os.path.join(ROOT, "raw", "video.MOV")
FX = os.path.join(ROOT, "out", "v8", "menores_fx.mp4")


def c(n):
    return os.path.join(NEW, f"IMG_{n}.MOV")


# (name, file, start_s, dur_s)
EDL = [
    # abertura (logo rapida por cima da caixa chegando)
    ("caixa_chega",       c(6847), 0.30, 2.60),
    ("adesivo",           c(6849), 1.10, 1.60),
    ("abre_caixa",        c(6850), 1.40, 1.20),
    ("papel_seda",        c(6851), 1.40, 1.50),
    # sousplat (tirada da caixa curta; destaque na mesa)
    ("tira_sousplat_cru", c(6852), 2.10, 0.90),
    ("tira_sousplat_verm", c(6853), 2.60, 0.90),
    ("mesa_prato",        OLD, 32.6667, 1.10),
    ("mesa_vermelho",     OLD, 36.2333, 1.90),
    # tapete redondo
    ("tira_redondo_teal", c(6854), 2.60, 1.20),
    ("tira_redondo_cru",  c(6855), 2.40, 1.20),
    ("deck_redondo_cru",  c(6872), 0.50, 2.00),
    # tapete retangular
    ("tira_retang_marinho", c(6861), 1.60, 1.60),
    ("deck_retang_vermelho", c(6875), 1.20, 1.30),
    ("deck_retang_marinho", c(6876), 0.20, 2.00),
    # tapete geometrico
    ("tira_geometrico",   c(6857), 2.60, 1.80),
    ("deck_geometrico",   c(6868), 0.00, 2.00),
    # jogo de passadeira (3 pecas)
    ("tira_passadeira",   c(6859), 3.00, 1.50),
    ("deck_passadeira_jogo", c(6862), 1.40, 2.30),
    # tapete para sala
    ("deck_tapete_sala",  c(6890), 2.50, 2.00),
    # tapetes redondos menores aparecendo um a um (efeito pre-renderizado)
    ("menores_aparecem",  FX, 0.00, 4.7333),
    # fecho (ovais)
    ("oval_verde",        c(6883), 0.00, 1.10),
    ("oval_cru",          c(6883), 2.50, 1.50),
    ("oval_teal",         c(6883), 6.00, 2.20),
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
        json.dump(segs, open(os.path.join(ROOT, "out", "v9_segs.json"), "w"), indent=1)
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
        enc.stdin.write(data[: s["frames"] * fs])
        print("seg", s["name"], s["frames"], file=sys.stderr, flush=True)
    enc.stdin.close()
    enc.wait()
    print("master", out, total, "frames")


if __name__ == "__main__":
    main()
