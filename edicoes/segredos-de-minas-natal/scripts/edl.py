# Edit decision list for "Segredos de Minas - 3 presentes de Natal"
# Times in SOURCE seconds. Frame grid 30 fps. Each segment: (src_in, src_out, take, zoom_from, zoom_to, video_in_override)
FPS = 30
TAKE_STARTS = [0.0, 263/30, 519/30, 748/30, 972/30, 1119/30]   # first frame of each take
SRC_END = 1332/30
def fr(t): return round(t*FPS)/FPS
SEGMENTS = [
 # src_in, src_out, take, z0, z1, label
 (0.000, 4.433, 0, 1.00, 1.045, "hook"),
 (4.867, 8.367, 0, 1.12, 1.14, "e olha"),
 (262/30, 11.567, 1, 1.00, 1.035, "primeira opcao"),
 (11.967, 15.233, 1, 1.08, 1.10, "ele vem"),
 (15.400, 16.867, 1, 1.16, 1.175, "preco 22"),
 (17.500, 22.600, 2, 1.00, 1.035, "segunda opcao"),
 (22.900, 24.433, 2, 1.14, 1.155, "preco 17,50"),
 (25.067, 30.567, 3, 1.00, 1.035, "terceira opcao"),
 (30.833, 31.900, 3, 1.14, 1.155, "preco 15"),
 (970/30, 33.000, 4, 1.00, 1.01, "viu so"),
 (33.267, 36.900, 4, 1.10, 1.125, "da pra presentear"),
 (37.233, SRC_END, 5, 1.06, 1.00, "cta"),
]
XFADE = 6  # frames of dissolve at take changes (video only)

def build():
    """Return list of dicts with output start/end and mapping."""
    out=[]; t=0.0
    for i,(a,b,take,z0,z1,label) in enumerate(SEGMENTS):
        a=fr(a); b=fr(b)
        nf=round((b-a)*FPS)
        prev_take = SEGMENTS[i-1][2] if i>0 else None
        out.append(dict(i=i,src_in=a,src_out=b,take=take,z0=z0,z1=z1,label=label,
                        out_start=t, nframes=nf, out_end=t+nf/FPS,
                        take_change=(prev_take is not None and prev_take!=take),
                        vmin=TAKE_STARTS[take]))
        t+=nf/FPS
    return out

def src_to_out(ts, segs=None):
    segs=segs or build()
    for s in segs:
        if s["src_in"]-1e-6 <= ts <= s["src_out"]+1e-6:
            return s["out_start"]+(ts-s["src_in"])
    return None

if __name__=="__main__":
    segs=build()
    for s in segs:
        print(f'{s["i"]:2d} {s["label"]:18s} src {s["src_in"]:6.3f}-{s["src_out"]:6.3f}  out {s["out_start"]:6.3f}-{s["out_end"]:6.3f} ({s["nframes"]}f) z {s["z0"]}->{s["z1"]} {"XFADE" if s["take_change"] else ""}')
    print("total", segs[-1]["out_end"], "frames", sum(s["nframes"] for s in segs))
