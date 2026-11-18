"""Report background luminance inside candidate text boxes over a time window (for white text)."""
import subprocess, sys, json, numpy as np
SRC='raw/video.MOV'; S=4  # downscale factor
def frames(t0,t1):
    raw=subprocess.run(['ffmpeg','-v','error','-ss',f'{t0}','-i',SRC,'-t',f'{t1-t0}','-vf',f'scale={1080//S}:{1920//S}','-f','rawvideo','-pix_fmt','gray','-'],capture_output=True,check=True).stdout
    n=len(raw)//((1080//S)*(1920//S)); return np.frombuffer(raw,np.uint8).reshape(n,1920//S,1080//S)
for spec in json.loads(sys.argv[1]):
    name,t0,t1,(x0,y0,x1,y1)=spec
    fr=frames(t0,t1)[:, y0//S:y1//S, x0//S:x1//S].astype(float)
    p80=np.percentile(fr.reshape(len(fr),-1),80,axis=1); p50=np.median(fr.reshape(len(fr),-1),axis=1)
    print(f"{name:28s} box{(x0,y0,x1,y1)} median luma: min {p50.min():5.1f} max {p50.max():5.1f} | p80 max {p80.max():5.1f} (white text wants < ~140)")
