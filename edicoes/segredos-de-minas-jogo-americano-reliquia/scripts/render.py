"""Render the edited video.

Works directly on the source's YUV 4:2:0 planes (bt709, limited range) so the
original colour grade is untouched: cuts, sub-pixel zooms and short dissolves are
applied per plane, and the transparent HyperFrames text layer is converted to
bt709 YUV and alpha-blended on top. Frames where nothing changes (zoom 1.0, no
dissolve, no text) are passed through bit-exact before encoding.

usage: render.py SCRATCH OUT.mp4 [--overlay DIR] [--audio FILE.wav] [--frames a:b] [--crf N]
"""
import sys, os, json, subprocess, argparse, math
import numpy as np, cv2

ap = argparse.ArgumentParser()
ap.add_argument("S"); ap.add_argument("out")
ap.add_argument("--overlay"); ap.add_argument("--audio")
ap.add_argument("--frames"); ap.add_argument("--crf", default="15")
ap.add_argument("--preset", default="slow")
ap.add_argument("--mask", help="PNG sequence whose alpha marks frosted-glass cards (blur + darken under the text)")
ap.add_argument("--glass-dark", type=float, default=0.62); ap.add_argument("--glass-blur", type=float, default=18.0)
args = ap.parse_args()
S = args.S
sys.path.insert(0, S + "/scripts")
import edl

W, H = 1080, 1920
FS = W * H * 3 // 2
SRC = S + "/src/raw.mov"
CACHE = S + "/work/frames.yuv"
NSRC = edl.SRC_FRAMES

# ---------- decode source once into a raw yuv420p cache ----------
if not os.path.exists(CACHE) or os.path.getsize(CACHE) != FS * NSRC:
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", SRC, "-f", "rawvideo", "-pix_fmt", "yuv420p", CACHE], check=True)
src = np.memmap(CACHE, dtype=np.uint8, mode="r", shape=(NSRC, FS))


def planes(buf):
    y = buf[:W * H].reshape(H, W)
    u = buf[W * H:W * H + W * H // 4].reshape(H // 2, W // 2)
    v = buf[W * H + W * H // 4:].reshape(H // 2, W // 2)
    return y, u, v


A = json.load(open(S + "/work/anchors2.json"))
segs = edl.build()


def ease(x):  # smooth in-out for slow pushes
    return 0.5 - 0.5 * math.cos(math.pi * max(0.0, min(1.0, x)))


def zoom_planes(buf, z, ax, ay):
    y, u, v = planes(buf)
    if abs(z - 1.0) < 1e-6:
        return y, u, v
    # out = (src - a) * z + a   (anchor stays fixed)
    My = np.float32([[z, 0, ax * (1 - z)], [0, z, ay * (1 - z)]])
    # chroma planes: half resolution, chroma sited left (horizontal) / centre (vertical)
    axc, ayc = ax / 2.0, (ay - 0.5) / 2.0
    Mc = np.float32([[z, 0, axc * (1 - z)], [0, z, ayc * (1 - z)]])
    yo = cv2.warpAffine(y, My, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    uo = cv2.warpAffine(u, Mc, (W // 2, H // 2), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    vo = cv2.warpAffine(v, Mc, (W // 2, H // 2), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return yo, uo, vo


def seg_frame(s, j):
    """planes for local frame j of segment s (j may run past the end for dissolve tails)."""
    fi = round(s["src_in"] * 30) + j
    fi = max(fi, round(s["vmin"] * 30))
    fi = min(fi, NSRC - 1)
    nf = s["nframes"]
    z = s["z0"] + (s["z1"] - s["z0"]) * ease(max(0, j) / max(1, nf - 1))
    ax, ay = A[s["label"]]["anchor"]
    return zoom_planes(src[fi], z, ax, ay)


def rgba_to_yuv(png):
    """BGRA uint8 -> (Y, U, V) float32 limited-range bt709 + alpha (full and chroma res)."""
    b, g, r, a = [png[..., i].astype(np.float32) / 255.0 for i in range(4)]
    Y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    Cb = (b - Y) / 1.8556
    Cr = (r - Y) / 1.5748
    Y8 = 16 + 219 * Y
    U8 = 128 + 224 * Cb
    V8 = 128 + 224 * Cr
    # chroma: 2x2 box of premultiplied values
    def down(x):
        return cv2.resize(x, (W // 2, H // 2), interpolation=cv2.INTER_AREA)
    ac = down(a)
    Uc = down(U8 * a) / np.maximum(ac, 1e-6)
    Vc = down(V8 * a) / np.maximum(ac, 1e-6)
    return Y8, Uc, Vc, a, ac


def blend(p, o, a):
    return np.clip(p.astype(np.float32) * (1 - a) + o * a + 0.5, 0, 255).astype(np.uint8)


# ---------- output frame list ----------
plan = []
for k, s in enumerate(segs):
    for j in range(s["nframes"]):
        plan.append((k, j))
TOTAL = len(plan)
f0, f1 = 0, TOTAL
if args.frames:
    f0, f1 = [int(x) for x in args.frames.split(":")]

enc = ["ffmpeg", "-v", "error", "-y",
       "-f", "rawvideo", "-pix_fmt", "yuv420p", "-s", f"{W}x{H}", "-r", "30",
       "-color_range", "tv", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
       "-i", "-"]
if args.audio:
    enc += ["-ss", f"{f0/30:.6f}", "-t", f"{(f1-f0)/30:.6f}", "-i", args.audio]
enc += ["-map", "0:v"] + (["-map", "1:a"] if args.audio else [])
enc += ["-c:v", "libx264", "-preset", args.preset, "-crf", args.crf, "-profile:v", "high", "-pix_fmt", "yuv420p",
        "-x264-params", "colorprim=bt709:transfer=bt709:colormatrix=bt709:range=tv:chromaloc=0",
        "-color_range", "tv", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
        "-movflags", "+faststart"]
if args.audio:
    enc += ["-c:a", "aac", "-b:a", "320k", "-ar", "44100", "-shortest"]
enc += [args.out]
p = subprocess.Popen(enc, stdin=subprocess.PIPE)

XF = edl.XFADE
for n in range(f0, f1):
    k, j = plan[n]
    s = segs[k]
    if s.get("vlead") and j >= s["nframes"] - s["vlead"] and k + 1 < len(segs):
        nxt = segs[k + 1]
        y, u, v = seg_frame(nxt, j - s["nframes"])
    else:
        y, u, v = seg_frame(s, j)
    # dissolve: blend the previous take's tail under the head of a new take
    if s["take_change"] and j < XF:
        prev = segs[k - 1]
        py, pu, pv = seg_frame(prev, prev["nframes"] + j)
        t = (j + 1) / (XF + 1)
        a = 0.5 - 0.5 * math.cos(math.pi * t)
        y = blend(py, y.astype(np.float32), a)
        u = blend(pu, u.astype(np.float32), a)
        v = blend(pv, v.astype(np.float32), a)
    if args.mask:
        mpath = os.path.join(args.mask, f"frame_{n+1:06d}.png")
        mk = cv2.imread(mpath, cv2.IMREAD_UNCHANGED) if os.path.exists(mpath) else None
        if mk is not None and mk[..., 3].max() > 0:
            m = mk[..., 3].astype(np.float32) / 255.0
            mc = cv2.resize(m, (W // 2, H // 2), interpolation=cv2.INTER_AREA)
            k = args.glass_dark; sg = args.glass_blur
            def glass(p, mm, sig, mid):
                b = cv2.GaussianBlur(p.astype(np.float32), (0, 0), sig)
                g = mid + (b - mid) * k          # multiplicative darkening of RGB == scale Y-16 and C-128
                return np.clip(p.astype(np.float32) * (1 - mm) + g * mm + 0.5, 0, 255).astype(np.uint8)
            y = glass(y, m, sg, 16.0)
            u = glass(u, mc, sg / 2, 128.0)
            v = glass(v, mc, sg / 2, 128.0)
    if args.overlay:
        fpath = os.path.join(args.overlay, f"frame_{n+1:06d}.png")
        if not os.path.exists(fpath):
            fpath = os.path.join(args.overlay, f"frame_{n:06d}.png")
        png = cv2.imread(fpath, cv2.IMREAD_UNCHANGED) if os.path.exists(fpath) else None
        if png is not None and png.shape[2] == 4 and png[..., 3].max() > 0:
            Yo, Uo, Vo, a, ac = rgba_to_yuv(png)
            y = blend(y, Yo, a)
            u = blend(u, Uo, ac)
            v = blend(v, Vo, ac)
    p.stdin.write(np.ascontiguousarray(y).tobytes())
    p.stdin.write(np.ascontiguousarray(u).tobytes())
    p.stdin.write(np.ascontiguousarray(v).tobytes())
    if n % 100 == 0:
        print("frame", n, "/", f1, flush=True)
p.stdin.close()
p.wait()
print("done", args.out, "frames", f1 - f0)
