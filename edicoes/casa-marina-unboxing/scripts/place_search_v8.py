"""Search a centred text box that stays dark over a master frame window (white text)."""
import subprocess, sys, json, numpy as np
SC = 4
def frames(src, k0, k1):
    raw = subprocess.run(['ffmpeg','-v','error','-i',src,'-vf',f"select='between(n\\,{k0}\\,{k1-1})',scale={1080//SC}:{1920//SC}",
                          '-vsync','0','-f','rawvideo','-pix_fmt','gray','-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, 1920//SC, 1080//SC).astype(float)
src = sys.argv[1]
for name, k0, k1, w, h, ymin, ymax in json.loads(sys.argv[2]):
    fr = frames(src, k0, k1); res = []
    for y in range(ymin, ymax + 1, 20):
        for cx in range(int(90 + w/2), int(990 - w/2) + 1, 20):
            x0 = int((cx - w/2)/SC); x1 = int((cx + w/2)/SC)
            box = fr[:, y//SC:(y+h)//SC, x0:x1].reshape(len(fr), -1)
            res.append((np.percentile(box, 80, axis=1).max(), np.median(box), cx, y))
    res.sort()
    print(name, [(round(a), round(m), c, y) for a, m, c, y in res[:6]])
