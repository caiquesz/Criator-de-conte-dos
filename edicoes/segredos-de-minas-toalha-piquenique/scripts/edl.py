# EDL - Segredos de Minas "toalha piquenique" (video 7). SOURCE seconds, 30 fps grid.
FPS = 30
SRC_FRAMES = 900
SRC_END = SRC_FRAMES / 30
# raw hard cuts: 6.233 (talk take 2), 13.633 (b-roll), 16.833/18.567/19.667/23.967/27.167 (inside b-roll)
TAKE_STARTS = {0: 0.0, 1: 187/30, 2: 409/30}
def fr(t): return round(t*FPS)/FPS
SEGMENTS = [
 # src_in, src_out, take, z0, z1, label, vlead
 (0.000, 2.833, 0, 1.00, 1.04, "uma mesa bonita", 0),
 (3.100, 5.967, 0, 1.10, 1.13, "e essa aqui", 0),
 (6.400, 8.433, 1, 1.00, 1.03, "essa e a nossa", 0),
 (8.767, 13.567, 1, 1.07, 1.10, "e uma toalha", 0),
 (13.933, 16.733, 2, 1.00, 1.03, "ela e perfeita", 0),
 (17.067, 19.100, 2, 1.05, 1.07, "cafes da tarde", 0),
 (19.400, 22.633, 2, 1.00, 1.03, "e tambem", 0),
 (23.033, 24.433, 2, 1.05, 1.07, "garanta ja", 0),
 (24.767, 26.333, 2, 1.00, 1.02, "entre em contato", 0),
 (26.533, SRC_END, 2, 1.05, 1.08, "consulte as cores", 0),
]
XFADE = 6
NO_XFADE = {(1, 2)}   # the raw cut to b-roll sits inside the removed pause: no handle, keep it a hard cut
FADE_OUT = {"e uma toalha": 0.02, "e tambem": 0.02, "cafes da tarde": 0.02, "garanta ja": 0.02}

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
