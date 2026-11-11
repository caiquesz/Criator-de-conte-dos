import json, sys
import numpy as np
S = sys.argv[1]; sys.path.insert(0, S + "/scripts")
import edl
F = json.load(open(S + "/work/face.json"))["track"]
res = {}
for s in edl.build():
    allpts = [r for r in F if s["src_in"] <= r["t"] <= s["src_out"]]
    pts = [r for r in allpts if r["chin"]]
    cover = len(pts) / max(1, len(allpts))
    if cover < 0.6:
        res[s["label"]] = dict(face=False, cover=cover, anchor=[540.0, 900.0], out_start=s["out_start"], out_end=s["out_end"])
        continue
    ax, ay = np.median([r["nose"] for r in pts], axis=0)
    co, cx, top, xl, xr = [], [], [], [], []
    for r in pts:
        j = (r["t"] - s["src_in"]) / max(1e-6, (s["src_out"] - s["src_in"]))
        z = s["z0"] + (s["z1"] - s["z0"]) * j
        co.append(ay + (r["chin"][1] - ay) * z); cx.append(ax + (r["chin"][0] - ax) * z)
        top.append(ay + (r["top"][1] - ay) * z)
        xl.append(ax + (r["xmin"] - ax) * z); xr.append(ax + (r["xmax"] - ax) * z)
    res[s["label"]] = dict(face=True, cover=cover, anchor=[float(ax), float(ay)], chin_p90=float(np.percentile(co, 90)),
                           chin_med=float(np.median(co)), cx=float(np.median(cx)), top_p10=float(np.percentile(top, 10)),
                           face_x0=float(np.percentile(xl, 5)), face_x1=float(np.percentile(xr, 95)),
                           out_start=s["out_start"], out_end=s["out_end"])
json.dump(res, open(S + "/work/anchors2.json", "w"), indent=1)
for k, v in res.items():
    print(f'{k:18s} face={v["face"]} cover={v["cover"]:.2f} anchor={[round(x) for x in v["anchor"]]}' + (f' chin_p90={v["chin_p90"]:.0f} cx={v["cx"]:.0f} headtop={v["top_p10"]:.0f} facex={v["face_x0"]:.0f}-{v["face_x1"]:.0f}' if v["face"] else ""))
