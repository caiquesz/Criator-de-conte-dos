"""Search a centred text box (w x h) that stays dark over a source time window.
Prints best candidates: (p75 max luminance, cx, y)."""
import subprocess, sys, json, numpy as np
S=4
def frames(t0,t1):
    raw=subprocess.run(['ffmpeg','-v','error','-ss',f'{t0}','-i','raw/video.MOV','-t',f'{t1-t0}','-vf',f'scale={1080//S}:{1920//S}','-f','rawvideo','-pix_fmt','gray','-'],capture_output=True,check=True).stdout
    n=len(raw)//((1080//S)*(1920//S)); return np.frombuffer(raw,np.uint8).reshape(n,1920//S,1080//S).astype(float)
for name,t0,t1,w,h,ymin,ymax in json.loads(sys.argv[1]):
    fr=frames(t0,t1); res=[]
    for y in range(ymin,ymax+1,10):
        for cx in range(int(90+w/2), int(900-w/2)+1, 20):
            x0=int((cx-w/2)/S); x1=int((cx+w/2)/S); yy0=y//S; yy1=(y+h)//S
            box=fr[:,yy0:yy1,x0:x1].reshape(len(fr),-1)
            res.append((np.percentile(box,75,axis=1).max(), cx, y))
    res.sort()
    print(name, [(round(a),b,c) for a,b,c in res[:5]])
