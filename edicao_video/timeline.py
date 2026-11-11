"""Gera timeline.json: palavras (tempo de saída), frases de legenda, eventos de SFX,
zoom e transições do motion. Tudo em tempo do vídeo FINAL (após o corte do silêncio)."""
import json, sys, math, re

FPS = 30
RAW_FRAMES = 1077            # 35.9 s
CUT_A = 417                  # 13.900 s  -> primeiro frame removido
CUT_B = 445                  # 14.833 s  -> primeiro frame mantido depois do corte
CUT_LEN = (CUT_B - CUT_A) / FPS
NFRAMES = RAW_FRAMES - (CUT_B - CUT_A)

def m(t):
    """tempo original -> tempo final"""
    if t < CUT_A / FPS:
        return t
    return t - CUT_LEN

tr = json.load(open(sys.argv[1]))
words = []
for s in tr:
    for w in s["words"]:
        words.append({"w": w["w"].strip(), "s": w["s"], "e": w["e"]})

# ajustes finos de início (Whisper adianta a 1a palavra depois de pausa)
fix = {6: 1.50, 14: 5.95, 24: 10.15, 37: 15.15}
for i, t in fix.items():
    words[i]["s"] = t
for w in words:
    w["s"] = round(m(w["s"]), 3)
    w["e"] = round(m(w["e"]), 3)
words[7]["w"] = "desconfiada"

# frases da legenda constante: (palavras pequenas, palavras destaque)
PH = [
    (range(0, 5), [5]),
    (range(6, 7), []),
    (range(7, 9), [9]),
    (range(10, 13), [13]),
    (range(14, 18), [18]),
    # 19..48 -> motion
    (range(49, 53), [53]),
    (range(54, 60), [60, 61]),
    (range(62, 66), [66]),
    (range(67, 72), [72]),
    (range(73, 77), [77]),
    (range(78, 81), [81]),
    (range(82, 87), [87]),
]

def small_txt(t):
    t = t.lower().rstrip(".")
    return t

def hl_txt(t):
    return re.sub(r"[.,]+$", "", t).upper()

phrases = []
for sm, hl in PH:
    ws = [{"t": small_txt(words[i]["w"]), "s": words[i]["s"], "hl": False} for i in sm]
    ws += [{"t": hl_txt(words[i]["w"]), "s": words[i]["s"], "hl": True} for i in hl]
    idx = list(sm) + hl
    phrases.append({"start": ws[0]["s"] - 0.06, "lastEnd": words[idx[-1]]["e"], "words": ws})
for k, p in enumerate(phrases):
    nxt = phrases[k + 1]["start"] if k + 1 < len(phrases) else 99
    p["end"] = round(min(nxt - 0.10, p["lastEnd"] + 0.55), 3)
# P1 vira o título de abertura ("quando a sua CNH pode ser RECOLHIDA?") -> não aparece como legenda
phrases[0]["hidden"] = True
# título de abertura: grande no centro até INTRO_MORPH, depois vira cabeçalho no topo até o motion
INTRO_MORPH = 1.40
INTRO_HDR_OUT = 8.18
# P5 ("ou quando ela tiver VENCIDA") sai quando o painel do motion entra
phrases[4]["end"] = 8.40
# última frase fica até o fim
phrases[-1]["end"] = NFRAMES / FPS + 1

# ---- motion: janela, transições (push) ----
T_IN0, T_IN1 = 8.28, 8.62          # painel entra pela direita empurrando o vídeo
T_OUT0, T_OUT1 = 18.25, 18.60      # painel sai pela direita, vídeo volta pela esquerda

def ease_io(p):
    p = max(0.0, min(1.0, p))
    return 4 * p ** 3 if p < 0.5 else 1 - (-2 * p + 2) ** 3 / 2

panelX, videoX, speed = [], [], []
for f in range(NFRAMES):
    t = f / FPS
    if t < T_IN0:
        px = 1080.0
    elif t < T_IN1:
        px = 1080 * (1 - ease_io((t - T_IN0) / (T_IN1 - T_IN0)))
    elif t < T_OUT0:
        px = 0.0
    elif t < T_OUT1:
        px = 1080 * ease_io((t - T_OUT0) / (T_OUT1 - T_OUT0))
    else:
        px = 1080.0
    if t < (T_IN0 + T_OUT1) / 2 and t < T_OUT0:
        vx = px - 1080          # vídeo sai para a esquerda
    else:
        vx = px - 1080 if t < T_OUT1 else 0.0
    panelX.append(round(px, 2))
    videoX.append(round(vx, 2))
for f in range(NFRAMES):
    a = panelX[max(0, f - 1)]; b = panelX[min(NFRAMES - 1, f + 1)]
    speed.append(round(abs(b - a) / 2, 2))   # px por frame

# ---- zoom do vídeo (corte seco entre frases, leve push dentro da frase) ----
ZOOM = [1.12, 1.0, 1.12, 1.0, 1.12, 1.0, 1.12, 1.0, 1.12, 1.0, 1.12, 1.0]
zoom = []
for f in range(NFRAMES):
    t = f / FPS
    k = 0
    for i, p in enumerate(phrases):
        if t >= p["start"]:
            k = i
    p = phrases[k]
    base = ZOOM[k]
    dur = max(0.5, (phrases[k + 1]["start"] if k + 1 < len(phrases) else NFRAMES / FPS) - p["start"])
    prog = max(0, min(1, (t - p["start"]) / dur))
    z = base * (1 + 0.035 * prog)
    if k == len(phrases) - 1:       # "o carro também vai ser REMOVIDO" -> push mais forte
        z = 1.0 + 0.14 * (1 - (1 - prog) ** 2)
    if T_IN0 - 0.2 < t < T_OUT1:
        z = 1.0
    zoom.append(round(z, 4))

# ---- SFX ----
W = lambda i: words[i]["s"]
sfx = []
def add(name, t, vol, align=0.0):
    sfx.append({"name": name, "t": round(t - align, 3), "vol": vol})

# destaques da legenda normal: pop suave
for p in phrases:
    for w in p["words"]:
        if w["hl"] and not (T_IN0 < w["s"] < T_OUT1):
            add("pop_soft", w["s"] - 0.02, 0.45)
# a parte "DIAS" do "30 DIAS" (2a palavra destaque) -> sem pop extra
sfx = [x for x in sfx if abs(x["t"] - (W(61) - 0.02)) > 0.01]

# título de abertura
add("pop_soft", W(2) - 0.02, 0.5)         # CNH (entra junto com "ela")
add("swish", INTRO_MORPH + 0.05, 0.22, align=0.41)   # título encolhe para o topo

# motion
add("whoosh", (T_IN0 + T_IN1) / 2, 0.55, align=1.07)
add("pop", W(22) - 0.02, 0.85)            # 30
add("click", W(23) - 0.01, 0.8)           # DIAS
add("swish", 9.84, 0.22, align=0.41)      # saída cena 1
add("pop", 10.15, 0.75)                   # card
add("click", W(25), 0.8)                  # A CARTEIRA
add("pop", W(31) - 0.02, 0.85)            # VALIDADE
add("swish", 12.22, 0.22, align=0.41)     # saída cena 2
for k, tt in enumerate([12.80, 12.88, 12.96, 13.04]):
    add("tick", tt, 0.5)                  # contador 1..10
add("pop", 13.10, 0.85)                   # 10
add("click", W(36), 0.8)                  # ANOS
add("swish", 13.98, 0.22, align=0.41)     # saída cena 3
add("click", W(38) - 0.02, 0.8)           # E VENCEU?
add("pop", W(38) + 0.22, 0.9)             # carimbo VENCIDA
add("swish", W(39) - 0.05, 0.22, align=0.41)
add("pop", W(42) - 0.02, 0.85)            # 30
add("click", W(43) - 0.01, 0.8)           # DIAS
add("pop", W(48) - 0.02, 0.8)             # VENCIDA
add("swish", W(49) - 0.06, 0.22, align=0.41)
add("whoosh", (T_OUT0 + T_OUT1) / 2, 0.5, align=1.07)

out = {
    "fps": FPS, "nframes": NFRAMES, "cut": [CUT_A, CUT_B],
    "words": words, "phrases": phrases,
    "intro": {"morph": INTRO_MORPH, "hdrOut": INTRO_HDR_OUT},
    "tin": [T_IN0, T_IN1], "tout": [T_OUT0, T_OUT1],
    "panelX": panelX, "videoX": videoX, "speed": speed, "zoom": zoom, "sfx": sfx,
}
json.dump(out, open(sys.argv[2], "w"), ensure_ascii=False)
for i, w in enumerate(words):
    print(i, w["w"], w["s"], w["e"])
print("frases:")
for p in phrases:
    print(round(p["start"], 2), p["end"], " ".join(("*" + w["t"] if w["hl"] else w["t"]) for w in p["words"]))
print("sfx:", len(sfx))
