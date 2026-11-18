"""Per shot: how much white-tile floor is left in the AI output vs the original."""
import subprocess, sys, json, numpy as np
sys.path.insert(0,'scripts')
import render_v4 as V
def load(path, w=90, h=160):
    raw=subprocess.run(['ffmpeg','-v','error','-i',path,'-vf',f'scale={w}:{h}','-f','rawvideo','-pix_fmt','rgb24','-'],capture_output=True,check=True).stdout
    return np.frombuffer(raw,np.uint8).reshape(-1,h,w,3).astype(np.float32)
def tile(img):
    mx=img.max(-1); mn=img.min(-1); s=(mx-mn)/np.maximum(mx,1); l=img.mean(-1)
    return ((s<0.22)&(l>78)).mean(axis=(1,2))
names={o:(n,a,b) for n,a,b,o in V.SEGS}
chunks=json.loads(sys.argv[1])
for orig, ai, segs in chunks:   # segs: list of [master_start, n]
    O=load(orig); A=load(ai)
    c=0
    for m0,n in segs:
        # which shots
        for name,a,b,o in V.SEGS:
            lo=max(o,m0); hi=min(o+b-a,m0+n)
            if lo>=hi: continue
            c0=c+(lo-m0); c1=c+(hi-m0)
            to=tile(O[c0:c1]).mean(); ta=tile(A[int(c0*0.8):max(int(c1*0.8),int(c0*0.8)+1)]).mean()
            flag='FALHOU' if to>0.08 and ta>0.5*to else ('ok' if to>0.08 else 'sem piso')
            print(f"{ai.split('/')[-1]:22s} {name:22s} tile orig {to:.2f} -> ai {ta:.2f}  {flag}")
        c+=n
