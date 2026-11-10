# EDL - Segredos de Minas "kit lavabo" (video 2). Times in SOURCE seconds, 30 fps grid.
FPS = 30
SRC_FRAMES = 1192
SRC_END = SRC_FRAMES / 30
# first frame of each shot where my cuts meet a camera change (raw hard cuts)
TAKE_STARTS = {0: 0.0, 1: 256/30, 2: 256/30, 3: 496/30, 4: 623/30, 5: 930/30, 6: 1030/30}
def fr(t): return round(t*FPS)/FPS
SEGMENTS = [
 # src_in, src_out, take, z0, z1, label, vlead(frames of next segment's pre-roll shown at the end)
 (0.000, 6.033, 0, 1.00, 1.05, "hook", 0),
 (6.367, 8.067, 0, 1.12, 1.14, "olha esse kit", 0),
 (8.667, 13.767, 1, 1.00, 1.04, "ele vem", 2),
 (14.133, 16.167, 2, 1.00, 1.03, "toalhinha", 0),
 (16.567, 20.400, 3, 1.00, 1.04, "capricho", 0),
 (20.900, 22.633, 4, 1.00, 1.03, "aqui na segredos", 0),
 (22.867, 28.200, 4, 1.06, 1.09, "temos varias", 0),
 (28.433, 30.600, 4, 1.00, 1.03, "com a pessoa", 0),
 (30.967, 33.967, 5, 1.00, 1.04, "nos enviamos", 0),
 (34.500, SRC_END, 6, 1.08, 1.00, "cta", 0),
]
XFADE = 6
NO_XFADE = {(1, 2)}   # same shot continues (handled with vlead)
FADE_OUT = {"capricho": 0.03}   # long sibilant tail: softer fade

def build():
    out=[]; t=0.0
    for i,(a,b,take,z0,z1,label,vlead) in enumerate(SEGMENTS):
        a=fr(a); b=fr(b); nf=round((b-a)*FPS)
        prev_take = SEGMENTS[i-1][2] if i>0 else None
        tc = prev_take is not None and prev_take!=take and (prev_take,take) not in NO_XFADE
        out.append(dict(i=i,src_in=a,src_out=b,take=take,z0=z0,z1=z1,label=label,vlead=vlead,
                        out_start=t,nframes=nf,fade_out=FADE_OUT.get(label,0.005),out_end=t+nf/FPS,take_change=tc,vmin=TAKE_STARTS[take]))
        t+=nf/FPS
    return out

if __name__=="__main__":
    segs=build()
    for s in segs:
        print(f'{s["i"]:2d} {s["label"]:18s} src {s["src_in"]:6.3f}-{s["src_out"]:6.3f} out {s["out_start"]:6.3f}-{s["out_end"]:6.3f} ({s["nframes"]}f) z {s["z0"]}->{s["z1"]} {"XFADE" if s["take_change"] else ""} vlead={s["vlead"]}')
    print("total", round(segs[-1]["out_end"],3), "frames", sum(s["nframes"] for s in segs))
