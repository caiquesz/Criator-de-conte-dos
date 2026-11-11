import sys, json, numpy as np
S=sys.argv[1]; sys.path.insert(0,S+"/scripts")
import edl
segs=edl.build()
db=np.load(S+"/work/db10ms.npy")
L=[w for s in json.load(open(S+"/work/transcript.json")) for w in s["words"]]
M=[w for s in json.load(open(S+"/work/transcript_medium.json")) for w in s["words"]]
def onset_after(t, maxlook=0.5, thr=-38):
    # first 10ms frame >= t whose level crosses thr after being below
    i=int(t*100)
    for k in range(i, min(len(db), i+int(maxlook*100))):
        if db[k]>thr and db[k-1]<=thr: return k/100
    return None
def m(t):
    for s in segs:
        if s["src_in"]-1e-6<=t<=s["src_out"]+1e-6: return s["out_start"]+t-s["src_in"]
    for s in segs:
        if t<s["src_in"]: return s["out_start"]
    return segs[-1]["out_end"]
out=[]
for a,b in zip(L,M):
    st=0.5*(a["s"]+b["s"]); en=0.5*(a["e"]+b["e"])
    # if this start is within/after a silence (level low just before), snap to real onset
    i=int(st*100)
    if i>8 and (db[i-8:i].max()<-38 or db[i]< -40):
        o=onset_after(st-0.25,0.6)
        if o is not None: st=o
    out.append(dict(w=a["w"].strip(), src=round(st,3), s=round(m(st),3), e=round(m(en),3)))
json.dump(out,open(S+"/work/words_out.json","w"),ensure_ascii=False,indent=0)
print(" ".join(f'{w["w"]}[{w["s"]:.2f}]' for w in out))
