"""Monta o plano.json do Bate-bola com a Dra. Nádia (rode na pasta do projeto, depois o reenquadrar.py,
o sincronizar.py, o abertura.py e o gerar.py).

Pergunta e resposta: cada pergunta abre num flash branco e no plano aberto ou médio; cada resposta
corta para o plano fechado, com outro corte no meio das respostas longas. Legenda pequena, na altura
do peito, troca seca; a palavra-chave da pergunta e os prazos em negrito. A abertura do quadro cobre
o "Bate bola com doutora Nádia Rezende" (0 a 2,97 s), então ali não há legenda.
"""
import json
from pathlib import Path

AQUI = Path(__file__).parent
ws = [w for s in json.loads((AQUI / "transcricao.json").read_text()) for w in s["palavras"]]
i = 6                                   # as 6 primeiras palavras são o título, dito na abertura
def pega(k, textos=None, so=None):
    """k palavras da fala; textos troca o que aparece (correções); so escolhe quais mostrar."""
    global i
    grupo = ws[i:i + k]
    i += k
    out = [{"t": w["t"], "s": w["s"]} for w in grupo]
    if textos:
        for w, t in zip(out, textos):
            w["t"] = t
    if so is not None:
        out = [out[j] for j in so]
    return out

L, F = "legenda", "legenda-forte"
G = [  # (estilo, palavras)
    # P0: Nádia, o verão está chegando. Ainda dá tempo de cuidar do corpo?
    (L, pega(3, ["Nádia,", "o", "verão"])), (L, pega(2)), (L, pega(3)), (L, pega(4)),
    # R0
    (L, pega(4)), (L, pega(2)), (L, pega(2)),
    # P1: Preenchimento glúteo. Quanto tempo pra perceber o resultado?
    (F, pega(2, ["Preenchimento", "glúteo."])), (L, pega(4)), (L, pega(2)),
    # R1
    (L, pega(4)), (L, pega(3)), (L, pega(3)), (L, pega(3)), (L, pega(3)),
    (F, pega(4)), (L, pega(3)), (L, pega(2)), (L, pega(4)),
    # P2: Bioestimulador de colágeno é rápido?
    (F, pega(3)), (L, pega(2)),
    # R2
    (L, pega(4)), (L, pega(3)), (L, pega(3)), (L, pega(2)), (F, pega(4)), (L, pega(3)),
    # P3: Subcisão pra celulite. Dá tempo?
    (F, pega(3)), (L, pega(2)),
    # R3
    (L, pega(4)), (L, pega(3)), (L, pega(3, ["como", "pós-imediato,", ""], so=[0, 1])), (L, pega(3)), (L, pega(3)),
    (L, pega(4)), (L, pega(3)), (F, pega(4)),
    # P4: Toxina botulínica pra suor excessivo. Quanto tempo demora?
    (F, pega(2, ["Toxina", "botulínica"])), (L, pega(3, ["pra", "suor", "excessivo."])), (L, pega(3)),
    # R4
    (L, pega(3)), (L, pega(2)), (L, pega(4)), (L, pega(1)), (L, pega(3)), (F, pega(4)), (L, pega(3)),
    # P5: Então ainda dá tempo de fazer alguma coisa antes do verão?
    (L, pega(4)), (L, pega(4)), (F, pega(3)),
    # R5: (Desde que) começando agora, dá pra se planejar sim, ...
    (L, pega(5, ["começando", "", "", "", "agora,"], so=[0, 4])), (L, pega(4)), (F, pega(1)),
    (L, pega(3)), (L, pega(5)), (L, pega(4)), (F, pega(1)),
]
assert i == len(ws), (i, len(ws))
ALT = {L: 46, F: 64}
CENTRO = 1180          # altura do peito dela nos três planos
legendas = []
for k, (est, palavras) in enumerate(G, 1):
    ultima = max(w["s"] for w in palavras)
    fim_fala = next(w["e"] for w in ws if abs(w["s"] - ultima) < 1e-6)
    legendas.append({"id": f"g{k}", "y": round(CENTRO - ALT[est] / 2), "linhas": [{"estilo": est, "palavras": palavras}],
                     "fim": round(fim_fala + 0.25, 3), "sombra_forte": True})

# planos (tempo do original; os cortes caem nas pausas, em quadros inteiros)
ABERTO, MEDIO, FECHADO, FECHADO2 = (1.0, [0.5, 0.5]), (1.15, [0.55, 0.42]), (1.45, [0.55, 0.40]), (1.25, [0.55, 0.42])
q = lambda t: round(round(t * 30) / 30, 4)
cortes = [
    (0, ABERTO, None),
    (2.9667, MEDIO, "luz"),        # sai da abertura: P0
    (6.5, FECHADO, "corte"),       # R0
    (8.1333, FECHADO2, "corte"),
    (9.9333, ABERTO, "flash"),     # P1
    (12.7667, FECHADO, "corte"),   # R1
    (16.1, FECHADO2, "corte"),
    (19.9667, FECHADO, "corte"),
    (23.8, MEDIO, "flash"),        # P2
    (25.9, FECHADO, "corte"),      # R2
    (30.2667, FECHADO2, "corte"),
    (34.0333, ABERTO, "flash"),    # P3
    (36.2, FECHADO, "corte"),      # R3
    (40.0, FECHADO2, "corte"),
    (45.1667, MEDIO, "flash"),     # P4
    (48.6333, FECHADO, "corte"),   # R4
    (53.5, FECHADO2, "corte"),
    (56.4, ABERTO, "flash"),       # P5
    (59.3333, FECHADO, "corte"),   # R5
    (62.7333, FECHADO2, "corte"),
    (66.0333, FECHADO, "corte"),
]
plano = {
    "video": "assets/video/video.mp4",
    "video_tem_audio": True,
    "duracao": 67.5,
    "enquadramentos": [{"de": q(t), "escala": e, "centro": c} for t, (e, c), _ in cortes],
    "legendas_na_frente": True,
    "foco_fotos": "corpo",
    "cores": {"texto": "#FFFFFF", "destaque": "#FFFFFF", "destaque_escuro": "#FFFFFF", "brilho": False},
    "legendas": legendas,
    "legendas_modo": "corte",
    "tracking": {"legenda": -0.04},
    "entrelinha": -0.02,
    "transicoes": [dict({"t": q(t), "tipo": tipo}, **({"som": "whoosh", "vol": 0.45} if tipo == "luz" else {}))
                   for t, _, tipo in cortes if tipo],
    "zoom_lento": 0.035,
    "som_cortes": {"som": "whoosh-rapido", "vol": 0.3},
    "extras": [{"id": "abertura", "src": "compositions/abertura.html", "z": 6}],
    "sfx_extra": [],
}
sons = AQUI / "abertura-sons.json"
if sons.exists():
    plano["sfx_extra"] = json.loads(sons.read_text())
(AQUI / "plano.json").write_text(json.dumps(plano, ensure_ascii=False, indent=1))
print(f"ok: {len(legendas)} legendas, {len(plano['transicoes'])} transições, {len(plano['enquadramentos'])} planos")
for g in legendas:
    print(g["id"], g["linhas"][0]["palavras"][0]["s"], g["fim"], g["linhas"][0]["estilo"][8:] or "-", " ".join(w["t"] for w in g["linhas"][0]["palavras"]))
