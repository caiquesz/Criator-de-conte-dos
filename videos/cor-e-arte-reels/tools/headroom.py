"""Confere (e corrige) a folga entre cada título e a cabeça da pessoa — regra "nunca texto no rosto".

Uso: python tools/headroom.py edits/<video>.json [--fix]
Lê o recorte da pessoa (cutout.src), acha a cabeça (22% de cima da silhueta) em vários quadros da janela de cada
título e compara com a altura estimada do título (tamanho × entrelinha + espaços). Com --fix, sobe o título para
ficar 40 px acima da cabeça (sem passar do topo seguro de 200 px) e grava o plano.
"""
import json
import subprocess
import sys

import numpy as np

ROOT = __file__.rsplit("/tools/", 1)[0]
plan_path = sys.argv[1]
fix = "--fix" in sys.argv
plan = json.load(open(plan_path))
words = {w["id"]: w for w in json.load(open(f"{ROOT}/{plan['transcript']}"))}
cut = plan.get("cutout")
if not cut:
    sys.exit("o plano não tem recorte (cutout)")

LH = {"sans": 0.86, "sans-sm": 0.86, "serif": 0.82, "serif-up": 0.82, "badge": 1.1}
MARGIN, TOP_SAFE = 40, 200


def head_top(t):
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-c:v", "libvpx-vp9", "-ss", f"{t:.3f}", "-i", f"{ROOT}/{cut['src']}", "-frames:v", "1",
         "-vf", "scale=270:480,format=yuva420p,alphaextract,format=gray", "-f", "rawvideo", "-"],
        capture_output=True).stdout
    if len(raw) != 270 * 480:
        return None, None
    a = np.frombuffer(raw, dtype=np.uint8).reshape(480, 270) > 128
    if a.sum() < 80:
        return None, None
    ys, xs = np.where(a)
    top = ys.min()
    head = a[top: top + max(8, int((ys.max() - top) * 0.22))]
    hy, hx = np.where(head)
    return top * 4, (hx.min() * 4, hx.max() * 4)


def title_window(ti):
    times = [tk["at"] if "at" in tk else words[tk["w"]]["start"] - 0.04 for line in ti["lines"] for tk in line["tokens"]]
    a = ti.get("start", min(times))
    if "end" in ti:
        b = ti["end"]
    else:
        last = words[ti["to"]]["end"] if ti.get("to") else max(times) + 0.4
        b = last + ti.get("hold", 0.45)
    return a, b


CW = {"sans": 0.55, "sans-sm": 0.55, "serif": 0.43, "serif-up": 0.47, "badge": 0.62}  # largura média por letra (em)


def title_x(ti):
    """Faixa horizontal estimada do título (largura da linha mais larga + alinhamento)."""
    pad = ti.get("padX", 80)
    widest = max(sum(len(tk.get("t", "")) * tk["size"] * CW.get(tk.get("s", "sans"), 0.55) for tk in line["tokens"])
                 + 0.24 * line["tokens"][0]["size"] * (len(line["tokens"]) - 1) for line in ti["lines"])
    align = ti.get("align", "center")
    if align == "flex-start":
        return pad, pad + widest
    if align == "flex-end":
        return 1080 - pad - widest, 1080 - pad
    return (1080 - widest) / 2, (1080 + widest) / 2


def title_height(ti):
    h = 0
    for i, line in enumerate(ti["lines"]):
        h += max(tk["size"] * LH.get(tk.get("s", "sans"), 0.86) for tk in line["tokens"])
        if i > 0:
            h += line.get("gap", -18)
    # descendente da serifada itálica (g, p, ç) passa da linha
    last = ti["lines"][-1]["tokens"]
    h += max(tk["size"] * (0.22 if tk.get("s", "").startswith("serif") else 0.08) for tk in last)
    return h


changed = False
for ti in plan["titles"]:
    a, b = title_window(ti)
    x0, x1 = title_x(ti)
    tops = []
    for t in np.linspace(a + 0.05, b - 0.05, 8):
        top, hx = head_top(t)
        # só conta a cabeça que está na mesma faixa horizontal do título
        if top is not None and hx[1] + 20 > x0 and hx[0] - 20 < x1:
            tops.append(top)
    bottom = ti["y"] + title_height(ti)
    if not tops:
        print(f"{ti['id']:14s} {a:6.2f}-{b:6.2f}  título x {x0:4.0f}-{x1:4.0f}  cabeça fora da faixa do título  ok")
        continue
    # o recorte às vezes pega um objeto (pano pendurado, quadro de flash): descarta topos que fogem da mediana
    med = float(np.median(tops))
    head = int(min(t for t in tops if t > med - 220))
    gap = head - bottom
    status = "ok" if gap >= MARGIN else "PERTO DA CABEÇA"
    print(f"{ti['id']:14s} {a:6.2f}-{b:6.2f}  título y {ti['y']:4d}-{bottom:6.0f}  cabeça a partir de y {head:4d}  folga {gap:5.0f} px  {status}")
    if fix and gap < MARGIN:
        new_y = max(TOP_SAFE, int(head - MARGIN - title_height(ti)))
        if new_y != ti["y"]:
            print(f"{'':14s} -> y {ti['y']} passa para {new_y}" + ("  (ainda apertado: reduza o tamanho)" if new_y == TOP_SAFE and head - MARGIN - title_height(ti) < TOP_SAFE else ""))
            ti["y"] = new_y
            changed = True

if fix and changed:
    json.dump(plan, open(plan_path, "w"), ensure_ascii=False, indent=2)
    print("plano atualizado")
