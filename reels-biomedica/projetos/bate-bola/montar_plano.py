"""Monta o plano.json do Bate-bola com a Dra. Nádia (rode na pasta do projeto; depois o abertura.py, o
reenquadrar.py, o sincronizar.py e o gerar.py).

Segunda versão, nos dois modelos que a cliente mandou (a primeira ela achou básica):
- abertura como a do bate-bola da doutora: o cursor clica nela duas vezes (e cada clique fecha o plano,
  cortado do 4K), estrelas douradas, o título digitado e barras de TV no fim. Ela diz o título de 0 a
  2,93 s; depois vem uma pausa de 1,6 s ("pausas") para a abertura respirar;
- o resto como o bate-bola da Nina Secrets: cada pergunta vira um texto em duas linhas (o tema em
  negrito, o resto regular), as respostas têm legenda no mesmo tipo (as palavras que pesam em
  negrito), cortes secos e as reações em preto e branco.

Tempos: "enquadramentos" e "pausas" no tempo do vídeo original; o resto no tempo do vídeo com a pausa.
"""
import json
from pathlib import Path

AQUI = Path(__file__).parent
ws = [w for s in json.loads((AQUI / "transcricao.json").read_text()) for w in s["palavras"]]
PAUSA_EM, PAUSA = 2.9333, 1.6
desloca = lambda t: round(t + PAUSA, 4) if t >= PAUSA_EM - 1e-6 else t
q = lambda t: round(round(t * 30) / 30, 4)

i = 6                                   # as 6 primeiras palavras são o título, dito na abertura


def fala(k, negrito=(), textos=None, so=None):
    """k palavras da fala, com os tempos já no vídeo novo; negrito = índices em negrito; textos corrige."""
    global i
    grupo = ws[i:i + k]
    i += k
    out = [{"t": w["t"], "s": desloca(w["s"]), "e": desloca(w["e"])} for w in grupo]
    if textos:
        for w, t in zip(out, textos):
            w["t"] = t
    for j in negrito:
        out[j]["b"] = True
    if so is not None:
        out = [out[j] for j in so]
    return out


def pergunta(k, linha1, linha2):
    """A pergunta inteira (k palavras) vira um texto em duas linhas, como no modelo: "**tema** resto"."""
    global i
    grupo = ws[i:i + k]
    i += k
    t0, t1 = desloca(grupo[0]["s"]), desloca(grupo[-1]["e"])
    toks = lambda linha: [{"t": t.strip("*"), "s": t0, "e": t1, **({"b": True} if t.startswith("*") else {})}
                          for t in linha.split()]
    return [toks(linha1), toks(linha2)]


T = "texto"
G = [  # cada item: lista de linhas (cada linha, lista de palavras)
    pergunta(12, "*O *verão está chegando:", "ainda dá tempo de cuidar do corpo?"),
    [fala(4, negrito=[0])],                         # Calma, vamos por partes.
    [fala(2)], [fala(2, negrito=[1])],              # Depende muito / do procedimento.
    pergunta(8, "*Preenchimento *glúteo:", "quanto tempo pra perceber o resultado?"),
    [fala(4, negrito=[1, 3])], [fala(3, negrito=[1])], [fala(3)], [fala(3)], [fala(3, negrito=[2])],
    [fala(4, negrito=[0, 1, 2, 3])], [fala(3)], [fala(2, negrito=[1])], [fala(4, negrito=[1])],
    pergunta(5, "*Bioestimulador *de *colágeno", "é rápido?"),
    [fala(4, negrito=[1, 2, 3])], [fala(3, negrito=[0])], [fala(3, negrito=[2])], [fala(2)],
    [fala(4, negrito=[0, 1, 2, 3])], [fala(3, negrito=[1, 2])],
    pergunta(5, "*Subcisão *pra *celulite:", "dá tempo?"),
    [fala(4, negrito=[1])], [fala(3, negrito=[2])], [fala(3, textos=["como", "pós-imediato,", ""], negrito=[1], so=[0, 1])],
    [fala(3)], [fala(3)], [fala(4, negrito=[3])], [fala(3)], [fala(4, negrito=[2, 3])],
    pergunta(8, "*Toxina *botulínica *pra *suor *excessivo:", "quanto tempo demora?"),
    [fala(3, negrito=[1])], [fala(2, negrito=[1])], [fala(4, negrito=[3])], [fala(1, negrito=[0])], [fala(3)],
    [fala(4, negrito=[0, 1, 2, 3])], [fala(3, negrito=[1, 2])],
    pergunta(11, "*Ainda *dá *tempo", "de fazer alguma coisa antes do verão?"),
    [fala(5, textos=["começando", "", "", "", "agora,"], negrito=[0, 4], so=[0, 4])], [fala(4, negrito=[3])], [fala(1, negrito=[0])],
    [fala(3)], [fala(5, negrito=[3, 4])],
    # o fim em preto e branco, com a citação em cima, como o "e o que é isso, ein?" do modelo
    [[{"t": "“", "s": desloca(ws[i]["s"]), "e": desloca(ws[i]["e"]), "b": True}], fala(5, negrito=[4])],
]
assert i == len(ws), (i, len(ws))
CENTRO = 1230          # no top escuro dela (aberto e médio) e no colo no fechado, a mesma altura sempre
legendas = []
for k, linhas in enumerate(G, 1):
    alt = sum(110 if ln[0]["t"] == "“" else 44 for ln in linhas) * 0.98
    ultima = max(w["e"] for ln in linhas for w in ln)
    legendas.append({"id": f"g{k}", "y": round(CENTRO - alt / 2),
                     "linhas": [dict({"estilo": T, "palavras": [{kk: v for kk, v in w.items() if kk != "e"} for w in ln]},
                                     **({"tam": 110} if ln[0]["t"] == "“" else {})) for ln in linhas],
                     "fim": round(ultima + 0.3, 3), "sombra_forte": True})

ABERTO, MEDIO, FECHADO, FECHADO2 = (1.0, [0.5, 0.5]), (1.15, [0.55, 0.42]), (1.45, [0.55, 0.40]), (1.25, [0.55, 0.42])
CLIQUE1, CLIQUE2 = (1.25, [0.55, 0.42]), (1.6, [0.55, 0.455])   # os dois cliques do cursor na abertura
cortes = [  # (tempo no original, plano, transição)
    (0, ABERTO, None),
    (0.4333, CLIQUE1, "clique"), (0.7667, CLIQUE2, "clique"),
    (2.9333, MEDIO, "barras"),     # P0 (depois da pausa e das barras de TV)
    (6.5, FECHADO, "pb"),          # R0: "Calma, vamos por partes." em preto e branco
    (8.1333, FECHADO2, "corte"),
    (9.9333, ABERTO, "pergunta"),  # P1
    (12.7667, FECHADO, "corte"), (16.1, FECHADO2, "corte"), (19.9667, FECHADO, "corte"),
    (23.8, MEDIO, "pergunta"),     # P2
    (25.9, FECHADO, "corte"), (30.2667, FECHADO2, "corte"),
    (34.0333, ABERTO, "pergunta"), # P3
    (36.2, FECHADO, "corte"), (40.0, FECHADO2, "corte"),
    (45.1667, MEDIO, "pergunta"),  # P4
    (48.6333, FECHADO, "corte"), (53.5, FECHADO2, "corte"),
    (56.4, ABERTO, "pergunta"),    # P5
    (59.3333, FECHADO, "corte"), (62.7333, FECHADO2, "corte"),
    (66.0333, FECHADO, "pb"),      # o fim em preto e branco
]
fim_video = round(67.5 + PAUSA, 4)
transicoes, pb, sfx, remover = [], [], [], []
for j, (t, _, tipo) in enumerate(cortes):
    if not tipo:
        continue
    tn = desloca(q(t))
    if tipo == "clique":           # o clique já tem som (o do cursor): sem whoosh
        transicoes.append({"t": tn, "tipo": "corte", "escala": 1.06})
        remover.append({"t": tn})
    elif tipo == "barras":         # o corte das barras de TV para a primeira pergunta: o bipe é o som
        transicoes.append({"t": tn, "tipo": "corte"})
        remover.append({"t": tn})
    else:
        transicoes.append({"t": tn, "tipo": "corte"})
    if tipo == "pb":
        ate = desloca(q(cortes[j + 1][0])) if j + 1 < len(cortes) else fim_video
        pb.append({"de": tn, "ate": ate})
        sfx.append({"t": round(tn + 0.02, 3), "som": "whoosh", "vol": 0.4})
# os trancos de câmera da abertura, na imagem parada da pausa (no modelo a câmera dá zoom aos solavancos)
for tn, esc in ((3.3, 1.09), (3.85, 1.07)):
    transicoes.append({"t": tn, "tipo": "corte", "escala": esc})
    remover.append({"t": tn})
transicoes.sort(key=lambda x: x["t"])
for g in legendas:                 # cada pergunta entra com um pop, como os textos do modelo
    if len(g["linhas"]) == 2 and g["linhas"][0]["palavras"][0].get("b") and g["linhas"][0]["palavras"][0]["t"] != "“":
        sfx.append({"t": g["linhas"][0]["palavras"][0]["s"], "som": "pop", "vol": 0.5})

plano = {
    "video": "assets/video/video.mp4",
    "video_original": "assets/video/voz.wav",
    "video_tem_audio": True,
    "duracao": round(67.5 + PAUSA, 4),
    "pausas": [{"em": PAUSA_EM, "dur": PAUSA}],
    "enquadramentos": [{"de": q(t), "escala": e, "centro": c} for t, (e, c), _ in cortes],
    "legendas_na_frente": True,
    "foco_fotos": "corpo",
    "cores": {"texto": "#FFFFFF", "destaque": "#FFFFFF", "destaque_escuro": "#FFFFFF", "brilho": False},
    "legendas": legendas,
    "legendas_modo": "corte",
    "tracking": {"texto": -0.03},
    "entrelinha": -0.02,
    "transicoes": transicoes,
    "pb": pb,
    "zoom_lento": 0.03,
    "som_cortes": {"som": "whoosh-rapido", "vol": 0.25},
    "extras": [{"id": "abertura", "src": "compositions/abertura.html", "z": 6}],
    "sfx_extra": sfx,
    "sfx_remover": remover,
}
sons = AQUI / "abertura-sons.json"
if sons.exists():
    plano["sfx_extra"] = json.loads(sons.read_text()) + sfx
(AQUI / "plano.json").write_text(json.dumps(plano, ensure_ascii=False, indent=1))
print(f"ok: {len(legendas)} textos e legendas, {len(transicoes)} cortes, {len(pb)} trechos em P&B, duração {plano['duracao']} s")
