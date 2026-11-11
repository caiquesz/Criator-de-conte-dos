# EDL - Segredos de Minas "cortina corta-luz" (video 4). SOURCE seconds, 30 fps grid.
FPS = 30
SRC_FRAMES = 1438
SRC_END = SRC_FRAMES / 30
# shot 0 = talking intro; shot 1 = everything after the first raw cut at 7.867 (b-roll + outro;
# the raw hard cuts inside it fall on continuous speech and are kept as they are)
TAKE_STARTS = {0: 0.0, 1: 236/30}
def fr(t): return round(t*FPS)/FPS
SEGMENTS = [
 # src_in, src_out, take, z0, z1, label, vlead
 (0.000, 3.467, 0, 1.00, 1.04, "hook", 0),
 (3.667, 7.533, 0, 1.12, 1.14, "eu vou te mostrar", 0),
 (7.967, 10.133, 1, 1.00, 1.03, "essa e a nossa", 0),
 (10.533, 16.167, 1, 1.06, 1.09, "ideal para quem", 0),
 (16.733, 17.867, 1, 1.00, 1.02, "ela e produzida", 0),
 (18.100, 19.267, 1, 1.06, 1.07, "em tecido duplo", 0),
 (19.767, 23.567, 1, 1.00, 1.04, "na frente o voal", 0),
 (23.933, 25.667, 1, 1.07, 1.09, "e nos fazemos", 0),
 (26.000, 27.300, 1, 1.00, 1.02, "em tres tamanhos", 0),
 (27.567, 30.600, 1, 1.06, 1.09, "3 x 1,80", 0),
 (30.967, 33.400, 1, 1.00, 1.03, "3 x 2,20", 0),
 (33.733, 36.567, 1, 1.06, 1.09, "4 x 2,60", 0),
 (36.767, 42.333, 1, 1.00, 1.04, "tres cores", 0),
 (42.600, 45.400, 1, 1.10, 1.12, "clique no link", 0),
 (45.867, SRC_END, 1, 1.04, 1.00, "nos enviamos", 0),
]
XFADE = 6
NO_XFADE = set()
FADE_OUT = {"em tres tamanhos": 0.02}

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
        print(f'{s["i"]:2d} {s["label"]:18s} src {s["src_in"]:6.3f}-{s["src_out"]:6.3f} out {s["out_start"]:6.3f}-{s["out_end"]:6.3f} ({s["nframes"]}f) z {s["z0"]}->{s["z1"]} {"XFADE" if s["take_change"] else ""}')
    print("total", round(segs[-1]["out_end"],3), "frames", sum(s["nframes"] for s in segs))
