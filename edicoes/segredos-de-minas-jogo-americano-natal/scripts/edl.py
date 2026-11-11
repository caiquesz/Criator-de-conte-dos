# EDL - Segredos de Minas "jogo americano de Natal" (video 5). SOURCE seconds, 30 fps grid.
FPS = 30
SRC_FRAMES = 1234
SRC_END = SRC_FRAMES / 30
# raw hard cuts: 4.633 (talk take 2), 12.633 (b-roll), 16.767/21.367/25.333 (inside b-roll), 27.433 (talk)
TAKE_STARTS = {0: 0.0, 1: 139/30, 2: 379/30, 3: 823/30}
def fr(t): return round(t*FPS)/FPS
SEGMENTS = [
 # src_in, src_out, take, z0, z1, label, vlead
 (0.000, 4.233, 0, 1.00, 1.05, "hook", 0),
 (4.667, 8.100, 1, 1.00, 1.04, "as vezes", 0),
 (8.100, 12.367, 1, 1.10, 1.13, "olha so", 0),          # punch-in on a continuous take (no time removed)
 (13.033, 18.867, 2, 1.00, 1.04, "ele contem", 0),
 (19.400, 23.033, 2, 1.06, 1.09, "otima opcao", 0),
 (23.367, 27.033, 2, 1.00, 1.03, "deixar tudo", 0),
 (27.400, 32.533, 3, 1.00, 1.05, "aqui na segredos", 0),
 (32.800, 35.367, 3, 1.10, 1.12, "entao se voce", 0),
 (35.633, 39.067, 3, 1.02, 1.05, "nao deixe", 0),
 (39.267, SRC_END, 3, 1.09, 1.04, "enviamos", 0),
]
XFADE = 6
NO_XFADE = set()
FADE_OUT = {"deixar tudo": 0.02, "nao deixe": 0.02}

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
