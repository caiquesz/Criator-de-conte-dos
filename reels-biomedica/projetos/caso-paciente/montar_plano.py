"""Monta o plano.json do Caso de paciente (rode na pasta do projeto; depois sincronizar.py, preparar_fotos.py e
gerar.py, da pasta ../reels-imobiliaria/scripts).

O vídeo chegou montado, em 14 takes com luz, cor e enquadramento diferentes. A cliente pediu: igualar a
luz e os tons, padronizar o enquadramento e editar nas referências. O enquadrar.py já deixou os takes
iguais (assets/video/video.mp4; o vídeo como chegou fica em video-sem-ajuste.mp4); a voz vem do original,
intacto (o vídeo já tem música: o som fica como está).

As fotos, como ela pediu na página de envio:
- o antes atrás dela quando ela diz "essa paciente" (o começo);
- antes e depois da 1ª sessão em cards (sem "quando": na fala da 1ª sessão);
- o antes da 2ª etapa na tela dividida (na fala da 2ª sessão), meio a meio e esfumada;
- o resultado da 2ª etapa, como ela está hoje, em tela cheia (logo depois, "que foi a queixa dela desde o
  início").
O take 6 (31,2–33,6 s) é uma foto da paciente que a própria cliente pôs no vídeo: fica como veio.
"""
import json
from pathlib import Path

AQUI = Path(__file__).parent
ws = [w for s in json.loads((AQUI / "transcricao.json").read_text()) for w in s["palavras"]]
L, F = "legenda", "legenda-forte"
CORRIGE = {"preciso.": "preciso:", "atenção,": "atenção:", "hipdips.": "hip dips.", "hipdips": "hip dips",
           "Melhorar": "melhorar"}

# (primeira palavra, última palavra, estilo): frases curtas numa linha, a que pesa em legenda-forte
GRUPOS = [
    (0, 1, L), (2, 4, L), (5, 6, L), (7, 9, F), (10, 13, L), (14, 17, L), (18, 19, F), (20, 21, L),
    (22, 23, L), (24, 27, L),
    (28, 32, L), (33, 36, L), (37, 39, L), (40, 44, L), (45, 47, F), (48, 50, L), (51, 52, L), (53, 55, F),
    (56, 58, L), (59, 61, L), (62, 65, L), (66, 68, L), (69, 71, F),
    (72, 74, L), (75, 77, L), (78, 81, L), (82, 84, F), (85, 88, L),
    (89, 91, L), (92, 93, L), (94, 95, F),
    (96, 98, F), (99, 100, L), (101, 103, L), (104, 105, L), (106, 108, L), (109, 110, L), (111, 113, L),
    (114, 115, F), (116, 120, L), (121, 123, F),
    (124, 127, F), (128, 131, L), (132, 134, L), (135, 137, L), (138, 142, L), (143, 145, L),
    (146, 149, F),
    (150, 151, L), (152, 154, L), (155, 156, L), (157, 160, L), (161, 164, L),
    (165, 167, L), (168, 171, L), (172, 174, F),
    (175, 179, L), (180, 182, F), (183, 186, L), (187, 188, L), (189, 190, L), (191, 193, F),
    (194, 196, L), (197, 200, L), (201, 203, L), (204, 206, F), (207, 209, L), (210, 213, L),
]
assert [g[0] for g in GRUPOS[1:]] == [g[1] + 1 for g in GRUPOS[:-1]] and GRUPOS[0][0] == 0 and GRUPOS[-1][1] == len(ws) - 1
CENTRO = 1290                # meio do bloco, no top jeans escuro dela (o colo é claro como a parede), a mesma altura no vídeo inteiro
legendas = []
for k, (a, b, est) in enumerate(GRUPOS, 1):
    pal = [{"t": CORRIGE.get(w["t"], w["t"]), "s": w["s"]} for w in ws[a:b + 1]]
    alt = 64 if est == F else 46
    legendas.append({"id": f"g{k}", "y": round(CENTRO - alt / 2), "linhas": [{"estilo": est, "palavras": pal}],
                     "fim": round(ws[b]["e"] + 0.25, 3), "sombra_forte": True})
# "hip dips" virou duas palavras no texto: os tempos são os da palavra que o Whisper juntou
for g in legendas:
    for ln in g["linhas"]:
        novo = []
        for p in ln["palavras"]:
            if p["t"].startswith("hip dips"):
                novo += [{"t": "hip", "s": p["s"]}, {"t": p["t"].replace("hip ", "", 1), "s": p["s"]}]
            else:
                novo.append(p)
        ln["palavras"] = novo

t = lambda i: ws[i]["s"]
fotos = [
    # o antes no fundo, atrás dela, enquanto ela diz "essa paciente chegou até mim me pedindo projeção no glúteo"
    {"id": "f1", "layout": "atras", "inicio": 0.0, "fim": round(t(10) - 0.05, 3),
     "imagens": ["assets/fotos/antes-1a-etapa.jpg"]},
    # antes e depois da 1ª sessão, lado a lado (o antes à esquerda), na fala da 1ª sessão
    {"id": "f2", "layout": "cards", "inicio": round(t(96), 3), "fim": round(t(104) - 0.05, 3),
     # o foco no glúteo (no meio da foto ficava a lombar e o glúteo saía cortado embaixo)
     "imagens": [{"src": "assets/fotos/antes-1a-etapa.jpg", "foco": [0.5, 0.6]},
                 {"src": "assets/fotos/depois-1a-etapa.jpg", "foco": [0.5, 0.56]}]},
    # o antes da 2ª etapa na metade de cima, esfumado, na fala da 2ª sessão
    {"id": "f3", "layout": "dividida", "inicio": round(t(124), 3), "fim": round(t(138) - 0.05, 3), "corte": 960,
     "esfumado": True, "dissolve": 0.32,
     # o glúteo um pouco acima do meio do painel: a parte de baixo se dissolve no vídeo
     "imagens": [{"src": "assets/fotos/antes-2a-etapa.jpg", "foco": [0.5, 0.66], "zoom": 1.1}]},
    # o resultado da 2ª etapa, como ela está hoje, em tela cheia: "que foi a queixa dela desde o início"
    {"id": "f4", "layout": "cheia", "inicio": round(t(138), 3), "fim": round(t(149) + 0.35, 3),
     "imagens": ["assets/fotos/depois-2a-etapa.jpg"]},
]
# na tela dividida o vídeo desce para a metade de baixo e o rosto dela fica onde está a legenda: nesse trecho a
# legenda sobe para logo abaixo da emenda (como na referência 4)
for g in legendas:
    if fotos[2]["inicio"] - 0.05 <= g["linhas"][0]["palavras"][0]["s"] < fotos[2]["fim"]:
        g["y"] = round(1010 - (64 if g["linhas"][0]["estilo"] == F else 46) / 2)
duracao = round(2385 / 30, 4)
plano = {
    "video": "assets/video/video.mp4",
    "video_original": "assets/video/original.mov",
    "video_tem_audio": True,
    "duracao": duracao,
    "legendas_na_frente": True,
    "foco_fotos": "corpo",
    "cores": {"texto": "#FFFFFF", "destaque": "#FFFFFF", "destaque_escuro": "#FFFFFF", "brilho": False},
    "legendas": legendas,
    "legendas_modo": "corte",
    "tracking": {"legenda": -0.04},
    "entrelinha": -0.02,
    "fotos": fotos,
    "recorte": "assets/video/recorte.webm",
    "recorte_janelas": [[0.0, round(t(10) + 0.3, 3)]],
    "transicoes": [],
}
(AQUI / "plano.json").write_text(json.dumps(plano, ensure_ascii=False, indent=1))
print(f"ok: {len(legendas)} legendas, {len(fotos)} fotos, {duracao} s")
