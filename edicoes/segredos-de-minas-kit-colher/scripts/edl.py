# EDL - Segredos de Minas "kit colher" (video 3, Sara). SOURCE seconds, 30 fps grid.
FPS = 30
SRC_FRAMES = 1115
SRC_END = SRC_FRAMES / 30
# first frame of each shot (raw hard cuts at 8.6, 15.933, 17.5, 21.7, 27.667, 31.633)
TAKE_STARTS = {0: 0.0, 1: 258/30, 2: 478/30, 3: 651/30, 4: 830/30, 5: 949/30}
def fr(t): return round(t*FPS)/FPS
SEGMENTS = [
 # src_in, src_out, take, z0, z1, label, vlead
 (0.000, 3.933, 0, 1.00, 1.05, "hook", 0),
 (4.200, 8.167, 0, 1.12, 1.14, "e se voce", 0),
 (8.933, 11.067, 1, 1.00, 1.03, "esse e o nosso kit", 0),
 (11.400, 15.733, 1, 1.06, 1.09, "uma opcao linda", 0),
 (15.967, 19.333, 2, 1.00, 1.04, "o kit vem com", 0),
 (19.567, 21.433, 2, 1.08, 1.10, "por apenas", 0),
 (21.700, 27.000, 3, 1.00, 1.05, "aqui na segredos", 0),
 (27.700, 28.800, 4, 1.00, 1.03, "broll natalinas", 0),
 (31.600, 33.767, 5, 1.00, 1.04, "nos enviamos", 0),
 (34.000, SRC_END, 5, 1.10, 1.05, "e so clicar", 0),
]
XFADE = 6
NO_XFADE = set()
FADE_OUT = {"uma opcao linda": 0.03, "por apenas": 0.03, "e se voce": 0.02}

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
        print(f'{s["i"]:2d} {s["label"]:20s} src {s["src_in"]:6.3f}-{s["src_out"]:6.3f} out {s["out_start"]:6.3f}-{s["out_end"]:6.3f} ({s["nframes"]}f) z {s["z0"]}->{s["z1"]} {"XFADE" if s["take_change"] else ""}')
    print("total", round(segs[-1]["out_end"],3), "frames", sum(s["nframes"] for s in segs))
