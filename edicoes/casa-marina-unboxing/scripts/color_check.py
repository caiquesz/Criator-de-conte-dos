"""Compare a passthrough frame between raw and rendered video in native YUV (no conversions)."""
import subprocess, sys, numpy as np
W,H=1080,1920
def yuv(path, n):
    raw=subprocess.run(['ffmpeg','-v','error','-i',path,'-vf',f"select=eq(n\\,{n})",'-vsync','0','-frames:v','1','-f','rawvideo','-pix_fmt','yuv420p','-'],capture_output=True,check=True).stdout
    y=np.frombuffer(raw[:W*H],np.uint8).astype(float); u=np.frombuffer(raw[W*H:W*H*5//4],np.uint8).astype(float); v=np.frombuffer(raw[W*H*5//4:],np.uint8).astype(float)
    return y,u,v
for n in map(int, sys.argv[3:]):
    a=yuv(sys.argv[1],n); b=yuv(sys.argv[2],n)
    print(n, 'mean Y/U/V raw', [round(x.mean(),2) for x in a], 'out', [round(x.mean(),2) for x in b], 'MAE', [round(np.abs(x-y).mean(),2) for x,y in zip(a,b)])
