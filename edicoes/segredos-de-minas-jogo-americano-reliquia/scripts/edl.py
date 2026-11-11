# EDL - Segredos de Minas "jogo americano Relíquia" (video 6). SOURCE seconds, 30 fps grid.
FPS = 30
SRC_FRAMES = 1086
SRC_END = 36.000          # trims 0.2 s of silence after the last word
# raw hard cuts: 6.467 (b-roll), 10.367/12.933 (inside), 15.633 (b-roll), 17.033/24.367 (inside), 25.767 (talk)
TAKE_STARTS = {0: 0.0, 1: 194/30, 2: 469/30, 3: 773/30}
def fr(t): return round(t*FPS)/FPS
SEGMENTS = [
 # src_in, src_out, take, z0, z1, label, vlead
 (0.000, 1.933, 0, 1.00, 1.03, "hoje eu vou", 0),
 (2.067, 6.067, 0, 1.08, 1.11, "que vai fazer", 0),
 (6.433, 9.367, 1, 1.00, 1.03, "esse e o nosso", 0),
 (9.633, 11.767, 1, 1.06, 1.08, "vendido avulsa", 0),
 (12.167, 13.533, 1, 1.00, 1.02, "produzida em tear", 0),
 (13.733, 15.400, 1, 1.06, 1.08, "100% algodao", 0),
 (16.133, 19.900, 2, 1.00, 1.04, "aqui na segredos", 0),
 (20.300, 25.567, 2, 1.06, 1.09, "outros modelos", 0),
 (25.800, 30.133, 3, 1.00, 1.04, "voce quer conhecer", 0),
 (30.533, 33.533, 3, 1.10, 1.12, "entao clique", 0),
 (33.800, SRC_END, 3, 1.04, 1.00, "nos enviamos", 0),
]
XFADE = 6
NO_XFADE = set()
FADE_OUT = {"outros modelos": 0.02, "esse e o nosso": 0.02, "aqui na segredos": 0.02, "voce quer conhecer": 0.02}

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
