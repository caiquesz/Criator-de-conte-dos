"""Monta o plano.json do Bate-bola com a Dra. Nádia (rode na pasta do projeto; depois o abertura.py, o
reenquadrar.py, o sincronizar.py e o gerar.py).

Segunda versão, nos dois modelos que a cliente mandou (a primeira ela achou básica):
- abertura como a do bate-bola da doutora (abertura.py), que só começa depois de ela dizer o título
  (0 a 2,93 s): uma pausa de 4,4 s ("pausas") em que passam trechos dela falando (broll.py), o
  cursor, as estrelas, o título digitado e as barras de TV;
- o resto como o bate-bola da Nina Secrets: cada pergunta vira um texto em duas linhas (o tema em
  negrito, o resto regular), as respostas têm legenda no mesmo tipo (as palavras que pesam em
  negrito) e as reações em preto e branco. Sem cortes nem troca de plano no vídeo dela (3ª versão:
  a cliente quer o vídeo como veio).

Tempos: "enquadramentos" e "pausas" no tempo do vídeo original; o resto no tempo do vídeo com a pausa.
"""
import json
from pathlib import Path

AQUI = Path(__file__).parent
ws = [w for s in json.loads((AQUI / "transcricao.json").read_text()) for w in s["palavras"]]
PAUSA_EM, PAUSA = 2.9333, 4.4            # a abertura vem depois de ela dizer o título (como no modelo)
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
    # o fim em preto e branco como o "👀 / e o que é isso, ein?" do modelo: emoji em cima, frase maior e em negrito
    [[{"t": "✨", "s": desloca(ws[i]["s"]), "e": desloca(ws[i]["e"])}], fala(5, negrito=[0, 1, 2, 3, 4])],
]
assert i == len(ws), (i, len(ws))
CENTRO = 1230          # no top escuro dela (aberto e médio) e no colo no fechado, a mesma altura sempre
legendas = []
for k, linhas in enumerate(G, 1):
    fim_ = linhas[0][0]["t"] == "✨"
    alt = (84 + 56) * 0.98 if fim_ else sum(44 for ln in linhas) * 0.98
    ultima = max(w["e"] for ln in linhas for w in ln)
    legendas.append({"id": f"g{k}", "y": round(CENTRO - alt / 2),
                     "linhas": [dict({"estilo": T, "palavras": [{kk: v for kk, v in w.items() if kk != "e"} for w in ln]},
                                     **({"tam": 84 if ln[0]["t"] == "✨" else 56} if fim_ else {})) for ln in linhas],
                     "fim": round(ultima + 0.3, 3), "sombra_forte": True})

# o vídeo dela fica como veio: sem cortes, sem trocar de plano e sem zoom (pedido da cliente na 2ª
# versão). Só as reações em preto e branco, como no modelo, nas pausas entre as frases (tempo do original)
PB = [(6.5, 8.1333),        # "Calma, vamos por partes."
      (66.0333, 67.5)]      # o fim: "que é algo muito individual."
fim_video = round(67.5 + PAUSA, 4)
transicoes, sfx, remover = [], [], []
pb = [{"de": desloca(q(a)), "ate": desloca(q(b)) if b < 67.5 else fim_video} for a, b in PB]
for t in pb:
    sfx.append({"t": round(t["de"] + 0.02, 3), "som": "whoosh", "vol": 0.4})
for g in legendas:                 # cada pergunta entra com um pop, como os textos do modelo
    if len(g["linhas"]) == 2 and g["linhas"][0]["palavras"][0].get("b") and g["linhas"][0]["palavras"][0]["t"] != "✨":
        sfx.append({"t": g["linhas"][0]["palavras"][0]["s"], "som": "pop", "vol": 0.5})

plano = {
    "video": "assets/video/video.mp4",
    "video_original": "assets/video/voz.wav",
    "video_tem_audio": True,
    "duracao": round(67.5 + PAUSA, 4),
    "pausas": [{"em": PAUSA_EM, "dur": PAUSA}],
    "enquadramentos": [{"de": 0, "escala": 1.0, "centro": [0.5, 0.5]}],
    "legendas_na_frente": True,
    "foco_fotos": "corpo",
    "cores": {"texto": "#FFFFFF", "destaque": "#FFFFFF", "destaque_escuro": "#FFFFFF", "brilho": False},
    "legendas": legendas,
    "legendas_modo": "corte",
    "tracking": {"texto": -0.03},
    "entrelinha": -0.02,
    "transicoes": transicoes,
    "pb": pb,
    "extras": [{"id": "abertura", "src": "compositions/abertura.html", "z": 6}],
    "sfx_extra": sfx,
    "sfx_remover": remover,
}
sons = AQUI / "abertura-sons.json"
if sons.exists():
    plano["sfx_extra"] = json.loads(sons.read_text()) + sfx
(AQUI / "plano.json").write_text(json.dumps(plano, ensure_ascii=False, indent=1))
print(f"ok: {len(legendas)} textos e legendas, {len(pb)} trechos em P&B, sem cortes, duração {plano['duracao']} s")
