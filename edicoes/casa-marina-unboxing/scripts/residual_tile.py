"""Per shot of the output EDL: share of the frame that still looks like white tile in the wood master."""
import sys, subprocess, numpy as np
sys.path.insert(0, 'scripts')
import render_v4 as V
from scipy import ndimage as ndi
W, H = 135, 240
def load(p):
    raw = subprocess.run(['ffmpeg','-v','error','-i',p,'-vf',f'scale={W}:{H}','-f','rawvideo','-pix_fmt','rgb24','-'],capture_output=True,check=True).stdout
    return np.frombuffer(raw,np.uint8).reshape(-1,H,W,3).astype(np.float32)
def tile(a):
    mx=a.max(-1); mn=a.min(-1); s=(mx-mn)/np.maximum(mx,1); l=a.mean(-1); warm=a[...,0]-a[...,2]
    m=ndi.uniform_filter(l,(1,5,5)); sd=np.sqrt(np.maximum(ndi.uniform_filter(l*l,(1,5,5))-m*m,0))
    return (s<0.10)&(l>165)&(l<245)&(warm<13)&(sd<10)
O=load(sys.argv[1]); Wd=load(sys.argv[2])
to=tile(O).mean((1,2)); tw=tile(Wd).mean((1,2))
for name,a,b,o in V.SEGS:
    k0,k1=o,o+b-a
    print(f"{name:22s} out {k0/30:6.2f}-{k1/30:6.2f}s  tile orig {to[k0:k1].mean():.3f}  left in wood {tw[k0:k1].mean():.3f}  max {tw[k0:k1].max():.3f}")
