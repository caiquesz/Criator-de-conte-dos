"""Per-segment face anchors in OUTPUT space (zoom applied).

anchor  = median nose position (zoom pivot used by render.py)
chin_p90 = 90th percentile of the chin's output y -> product/price cards hang just below it
cx       = median chin x -> cards are centred under the chin

usage: anchors.py SCRATCH   (reads work/face.json, writes work/anchors2.json)
"""
import json, sys
import numpy as np

S = sys.argv[1]
sys.path.insert(0, S + "/scripts")
import edl

F = json.load(open(S + "/work/face.json"))["track"]
res = {}
for s in edl.build():
    pts = [r for r in F if r["chin"] and s["src_in"] <= r["t"] <= s["src_out"]]
    ax, ay = np.median([r["nose"] for r in pts], axis=0)
    co, cx = [], []
    for r in pts:
        j = (r["t"] - s["src_in"]) / max(1e-6, (s["src_out"] - s["src_in"]))
        z = s["z0"] + (s["z1"] - s["z0"]) * j
        co.append(ay + (r["chin"][1] - ay) * z)
        cx.append(ax + (r["chin"][0] - ax) * z)
    res[s["label"]] = dict(anchor=[float(ax), float(ay)], chin_p90=float(np.percentile(co, 90)),
                           chin_med=float(np.median(co)), cx=float(np.median(cx)),
                           out_start=s["out_start"], out_end=s["out_end"])
json.dump(res, open(S + "/work/anchors2.json", "w"), indent=1)
print(json.dumps(res, indent=1))
