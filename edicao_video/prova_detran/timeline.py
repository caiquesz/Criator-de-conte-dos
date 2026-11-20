"""Timeline do vídeo "prova do Detran": cortes de silêncio, palavras (tempo final), frases da legenda,
cenas de motion (papel + gradiente), transições, zoom e SFX.
uso: python3 timeline.py dados/palavras.json timeline.json"""
import copy, json, sys

FPS = 30
RAW_FRAMES = 1892   # 63,085 s convertido para 30 fps constantes (o .MOV do iPhone é VFR)

# trechos REMOVIDOS (tempo do bruto). Silêncios mortos, falsa largada e a parte ininteligível.
CUTS_RAW = [
    (6.85, 8.08),    # hesitação entre "carro" e "parado" (debaixo do motion)
    (10.10, 10.95),  # pausa longa "sem ... combustível" (debaixo do motion)
    (13.15, 13.50),
    (16.15, 17.05),  # encurta a pausa antes do "R" (fica ~0,5 s de suspense)
    (19.95, 21.80),
    (24.15, 26.00),  # pausa + falsa largada antes de "remoção" (fica ~0,5 s de suspense)
    (27.90, 28.85),
    (29.25, 29.90),
    (33.15, 34.00),
    (39.65, 40.50),  # debaixo do motion
    (41.85, 43.30),  # debaixo do motion
    (48.60, 49.30),  # debaixo do motion
    (55.85, 58.25),  # trecho ininteligível + pausa
    (60.35, 61.05),
]
# GANCHO de abertura: "essas provas de múltipla escolha são danadas" (o trecho também fica no lugar original)
HOOK_RAW = (29.95, 33.15)
# o conteúdo principal começa aqui; a aparição dele no começo fica escondida atrás da folha
START_RAW = 0.35

# em frames: [a, b) removidos
CUTS = [(round(a * FPS), round(b * FPS)) for a, b in CUTS_RAW]
MAIN = []
prev = round(START_RAW * FPS)
for a, b in CUTS:
    MAIN.append((prev, a)); prev = b
MAIN.append((prev, RAW_FRAMES))
HOOK = (round(HOOK_RAW[0] * FPS), round(HOOK_RAW[1] * FPS))
SEGS = [HOOK] + MAIN                      # trechos do bruto, na ordem em que aparecem no vídeo final
NFRAMES = sum(b - a for a, b in SEGS)
HOOK_LEN = (HOOK[1] - HOOK[0]) / FPS


def m(t):
    """tempo do bruto -> tempo final no conteúdo principal (se cair num corte, gruda no ponto do corte)"""
    f = t * FPS
    out = HOOK[1] - HOOK[0]
    for a, b in MAIN:
        if f < a:
            return out / FPS
        if f < b:
            return (out + f - a) / FPS
        out += b - a
    return out / FPS


def mh(t):
    """tempo do bruto -> tempo final dentro do gancho"""
    return (t * FPS - HOOK[0]) / FPS


words = json.load(open(sys.argv[1]))
for w in words:
    # palavra muito longa e com score baixo = o alinhador esticou por cima de um silêncio
    if w["e"] - w["s"] > 0.6 and w["p"] < 0.3:
        w["s"] = round(w["e"] - 0.38, 3)
fixes = {62: (28.88, 29.20), 92: (43.40, 43.70)}   # "agora", "é"
for i, (s, e) in fixes.items():
    words[i]["s"], words[i]["e"] = s, e
raw_words = copy.deepcopy(words)
for w in words:
    w["s"] = round(m(w["s"]), 3)
    w["e"] = round(m(w["e"]), 3)
W = lambda i: words[i]["s"]
E = lambda i: words[i]["e"]

# ---- legenda constante: (palavras pequenas, palavras destaque) por índice ----
PH = [
    (range(0, 2), [2]),          # quando na PROVA,
    # 3..30 -> cena do papel
    (range(31, 33), [33]),       # toda medida ADMINISTRATIVA
    (range(34, 38), [38]),       # começa com a letra R
    (range(39, 43), [43]),       # então, tudo que tiver R,
    (range(44, 46), [46]),       # você já DESCARTA
    (range(47, 50), [50]),       # ter um veículo IMOBILIZADO
    (range(51, 53), [53, 54]),   # vai gerar O QUÊ?
    (range(0, 0), [55]),         # REMOÇÃO
    (range(56, 61), [61]),       # do veículo, leva o carro EMBORA
    (range(62, 66), [66, 67]),   # agora, essas provas de MÚLTIPLA ESCOLHA
    (range(68, 69), [69]),       # são DANADAS,
    (range(70, 74), [74, 75]),   # porque você tem lá QUATRO OPÇÕES
    # 76..105 -> cena do gradiente
    (range(106, 111), [111, 112]),  # não vai querer fazer nada CORRENDO, NÃO
    (range(113, 116), []),          # tá lá, né?
    (range(116, 120), [120, 121]),  # às vezes uma leitura MAL FEITA,
    (range(122, 124), [124]),       # uma leitura RÁPIDA,
    (range(125, 128), [128, 129, 130]),  # aí voltar, remarcar TUDO DE NOVO
    (range(131, 132), [132, 133]),  # fazer OUTRA PROVA
    (range(134, 136), [136, 137]),  # não é BOM, NÉ?
]
import re
def small_txt(t):
    return t.lower().rstrip(".") if t != "R" else "R"
def hl_txt(t):
    return re.sub(r"[.,]+$", "", t).upper()

phrases = []
# gancho (mesmas palavras 63..69, no tempo do gancho)
for sm, hl in [(range(63, 66), [66, 67]), (range(68, 69), [69])]:
    ws = [{"t": small_txt(raw_words[i]["w"]), "s": round(mh(raw_words[i]["s"]), 3), "hl": False} for i in sm]
    ws += [{"t": hl_txt(raw_words[i]["w"]), "s": round(mh(raw_words[i]["s"]), 3), "hl": True} for i in hl]
    idx = list(sm) + hl
    phrases.append({"start": round(max(0, ws[0]["s"] - 0.06), 3), "lastEnd": round(mh(raw_words[idx[-1]]["e"]), 3),
                    "words": ws, "hook": True})
for sm, hl in PH:
    ws = [{"t": small_txt(words[i]["w"]), "s": W(i), "hl": False} for i in sm]
    ws += [{"t": hl_txt(words[i]["w"]), "s": W(i), "hl": True} for i in hl]
    idx = list(sm) + hl
    phrases.append({"start": round(ws[0]["s"] - 0.06, 3), "lastEnd": E(idx[-1]), "words": ws})
for k, p in enumerate(phrases):
    nxt = phrases[k + 1]["start"] if k + 1 < len(phrases) else 999
    p["end"] = round(min(nxt - 0.10, p["lastEnd"] + 0.6), 3)
phrases[-1]["end"] = NFRAMES / FPS + 1
def find(*hl):
    return [p for p in phrases if [w["t"] for w in p["words"] if w["hl"]] == list(hl)]
for p in find("R") + find("REMOÇÃO") + [q for q in find("DANADAS") if q.get("hook")]:
    p["big"] = True                       # destaque gigante
find("PROVA")[0]["ink"] = True            # "quando na PROVA," fica escrito na folha (ele não aparece mais)

# ---- cenas de motion (tempo final) ----
A_IN = (HOOK_LEN - 0.35, HOOK_LEN)  # folha entra pela esquerda empurrando o fim do gancho
CR_START = m(13.02)               # papel amassa depois de "lembrar,"
CR_DUR, TOSS_DUR = 0.62, 0.36     # amassar + arremesso
B_IN = (m(35.28), m(35.62))       # gradiente entra pela direita (ele sai pela esquerda)
B_OUT = (m(49.32), m(49.66))      # gradiente sai pela direita, ele volta pela esquerda
find("DANADAS")[0]["end"] = round(A_IN[0] + 0.08, 3)
find("QUATRO", "OPÇÕES")[0]["end"] = round(B_IN[0] + 0.02, 3)   # "quatro opções" sai quando o gradiente entra


def ease_io(p):
    p = max(0.0, min(1.0, p))
    return 4 * p ** 3 if p < 0.5 else 1 - (-2 * p + 2) ** 3 / 2


panelA, panelB, videoX, speed = [], [], [], []
for f in range(NFRAMES):
    t = f / FPS
    # cena A (papel): x do painel; None = escondido
    if t < A_IN[0]:
        a = None
    elif t < A_IN[1]:
        a = -1080 * (1 - ease_io((t - A_IN[0]) / (A_IN[1] - A_IN[0])))
    elif t < CR_START:
        a = 0.0
    else:
        a = None
    # cena B (gradiente)
    if t < B_IN[0] or t >= B_OUT[1]:
        b = None
    elif t < B_IN[1]:
        b = 1080 * (1 - ease_io((t - B_IN[0]) / (B_IN[1] - B_IN[0])))
    elif t < B_OUT[0]:
        b = 0.0
    else:
        b = 1080 * ease_io((t - B_OUT[0]) / (B_OUT[1] - B_OUT[0]))
    # vídeo empurrado junto
    if a is not None and t < A_IN[1]:
        vx = a + 1080
    elif a is not None:
        vx = 1080.0          # coberto pelo papel
    elif b is not None and t < B_IN[1]:
        vx = b - 1080
    elif b is not None and t >= B_OUT[0]:
        vx = b - 1080
    elif b is not None:
        vx = -1080.0
    else:
        vx = 0.0
    panelA.append(None if a is None else round(a, 2))
    panelB.append(None if b is None else round(b, 2))
    videoX.append(round(vx, 2))
for f in range(NFRAMES):
    a = videoX[max(0, f - 1)]; b = videoX[min(NFRAMES - 1, f + 1)]
    speed.append(round(abs(b - a) / 2, 2))

# ---- zoom: troca a cada frase (e em todo corte), push leve dentro da frase ----
cut_times = [m(a) for a, b in CUTS_RAW]
zoom = []
for f in range(NFRAMES):
    t = f / FPS
    k = max([i for i, p in enumerate(phrases) if t >= p["start"]] or [0])
    p = phrases[k]
    base = 1.12 if k % 2 == 0 else 1.0
    nxt = phrases[k + 1]["start"] if k + 1 < len(phrases) else NFRAMES / FPS
    prog = max(0, min(1, (t - p["start"]) / max(0.5, nxt - p["start"])))
    z = base * (1 + 0.03 * prog)
    if p.get("big"):
        z = 1.18 * (1 + 0.03 * prog)
    if k == len(phrases) - 1:
        z = 1.0 + 0.12 * (1 - (1 - prog) ** 2)
    if (A_IN[1] <= t < CR_START + CR_DUR + TOSS_DUR + 0.2) or (B_IN[0] - 0.3 < t < B_OUT[1]):
        z = 1.0
    zoom.append(round(z, 4))

# ---- SFX ----
sfx = []
def add(name, t, vol, align=0.0):
    sfx.append({"name": name, "t": round(t - align, 3), "vol": vol})

SOFT = {"R": ("pop", .7), "DESCARTA": ("pop_soft", .5), "IMOBILIZADO": ("pop_soft", .45), "QUÊ?": ("click", .6),
        "REMOÇÃO": ("pop", .75), "MÚLTIPLA": ("pop_soft", .45), "DANADAS": ("pop_soft", .45),
        "QUATRO": ("pop_soft", .45), "CORRENDO": ("pop_soft", .45), "MAL": ("pop_soft", .45),
        "TUDO": ("pop_soft", .45), "OUTRA": ("pop", .65)}
for p in phrases:
    for w in p["words"]:
        if w["hl"] and p.get("hook"):
            add("pop" if w["t"] == "DANADAS" else "pop_soft", w["s"] - 0.02, 0.8 if w["t"] == "DANADAS" else 0.45)
        elif w["hl"] and w["t"] in SOFT:
            n, v = SOFT[w["t"]]
            add(n, w["s"] - 0.02, v)

# cena A (papel)
add("papel_desliza", A_IN[0] + 0.02, 0.8, align=0.10)
add("swish", A_IN[0] + 0.12, 0.2, align=0.41)
add("pop", W(5) - 0.02, 0.8)                     # selo MUITO COMUM
for t0, t1 in [(W(10), E(13)), (W(14), E(20)), (W(21), E(25))]:   # lápis escrevendo a pergunta
    t = t0
    while t < t1 - 0.2:
        add("lapis", t, 0.55); t += 0.8
add("click", W(25) - 0.05, 0.7)                  # marcador de combustível aparece
for k in range(4):
    add("tick", W(25) + 0.25 + k * 0.16, 0.45)   # ponteiro descendo
add("pop", W(26) - 0.02, 0.9)                    # COMBUSTÍVEL (E)
add("click", W(30) - 0.03, 0.75)                 # LEMBRE!
add("amassar", CR_START - 0.04, 1.0, align=0.06)
add("amassar2", CR_START + 0.05, 0.6, align=0.11)
add("whoosh_curto", CR_START + CR_DUR + 0.02, 0.6, align=0.29)

# cena B (gradiente)
add("whoosh", (B_IN[0] + B_IN[1]) / 2, 0.5, align=1.07)
for k in range(4):
    add("pop", B_IN[1] + 0.02 + k * 0.11, 0.7)    # 4 cartões
add("marcador", W(80) + 0.0, 0.8)                # risca C
add("marcador", W(80) + 0.22, 0.8)               # risca D
add("swish", W(81) - 0.05, 0.22, align=0.41)     # cartões se reorganizam
add("pop_soft", W(85) - 0.02, 0.5)               # PARECIDAS
add("click", W(89) - 0.02, 0.7)                  # FEITO PRA PEGAR (anzol desce)
add("pop", W(91) - 0.02, 0.8)
add("click", W(94) - 0.02, 0.7)                  # PORTUGUÊS
add("swish", W(95) - 0.05, 0.2, align=0.41)      # lupa
add("pop", W(99) - 0.02, 0.8)                    # ATENÇÃO
add("relogio", W(100) + 0.05, 0.55)              # TEMPO (tique-taque)
add("pop", W(102) - 0.02, 0.8)
add("whoosh", (B_OUT[0] + B_OUT[1]) / 2, 0.5, align=1.07)

out = {
    "fps": FPS, "nframes": NFRAMES, "segs": SEGS, "hookLen": HOOK_LEN,
    "words": words, "phrases": phrases,
    "A_in": A_IN, "crStart": CR_START, "crDur": CR_DUR, "tossDur": TOSS_DUR,
    "B_in": B_IN, "B_out": B_OUT,
    "panelA": panelA, "panelB": panelB, "videoX": videoX, "speed": speed, "zoom": zoom, "sfx": sfx,
}
json.dump(out, open(sys.argv[2], "w"), ensure_ascii=False)
print(f"frames {NFRAMES} ({NFRAMES / FPS:.2f}s), cortado {(RAW_FRAMES - NFRAMES) / FPS:.2f}s")
for i, w in enumerate(words):
    print(i, w["w"], w["s"], w["e"], end=" | ")
print("\nfrases:")
for p in phrases:
    print(round(p["start"], 2), p["end"], " ".join(("*" + w["t"] if w["hl"] else w["t"]) for w in p["words"]))
print("A_in", A_IN, "crumple", CR_START, "B", B_IN, B_OUT, "sfx", len(sfx))
