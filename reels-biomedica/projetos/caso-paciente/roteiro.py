"""Roteiro do Caso de paciente, 2ª versão, nas duas referências que a cliente mandou em 17/11:

- antes e depois como no vídeo da dentista (referência A): a foto do antes numa faixa no alto com ela
  embaixo (sem recorte da pessoa: na 1ª versão o recorte ficou feio na borda); o par lado a lado, encostado,
  com um fio branco no meio, atravessando o peito dela e crescendo de leve ao entrar; uma foto só numa faixa
  de cantos arredondados que entra saindo do desfoque; o resultado em tela cheia, esmaecendo;
- todo o resto como o vídeo da moça de blazer marrom (referência B): planos aberto e fechado alternando em
  corte seco (o "zoom in, zoom out"), preto e branco nas falas de drama (entra seco, sai num clarão ou num
  esmaecer escurecido para a cor), luz quente nas transições, legendas minúsculas entrando palavra por
  palavra do desfoque, as que pesam em negrito ou maiores em creme, uma ou outra em itálico.
  Na 3ª versão (17/11) a cliente tirou a cor da referência B (fica a cor original) e pediu Poppins com as
  letras juntas, mantendo o bege, e mais efeitos sonoros.

Tempos em segundos no vídeo (30 quadros/s); os cortes caem nos silêncios entre palavras (VAD do sincronizar.py).
"""

FPS = 30
TOTAL = 2385                    # quadros

# planos: (início, fim, plano "a" aberto / "f" fechado / "foto" a foto que a cliente pôs, efeito)
# efeitos: "pb" preto e branco (com empurrão lento), "volta" sai do P&B para a cor em 0,5 s, "zoom" empurrão lento
PLANOS = [
    (0.000, 3.967, "a", None),          # essa paciente chegou até mim me pedindo projeção no glúteo (faixa do antes)
    (3.967, 7.400, "f", "pb"),          # e a primeira coisa que eu fiz foi não colocar a projeção
    (7.400, 8.800, "a", None),          # e hoje eu vou te explicar (sai do P&B num clarão)
    (8.800, 13.767, "f", None),         # essa paciente tem 29 anos, treina, se alimenta bem, cuida do corpo
    (13.767, 15.467, "a", None),        # e o pedido era preciso:
    (15.467, 20.033, "f", None),        # melhorar o contorno e ganhar projeção na parte superior do glúteo
    (20.033, 22.967, "a", None),        # mas antes de definir qualquer procedimento
    (22.967, 26.833, "f", None),        # eu avaliei as características e as proporções de cada corpo
    (26.833, 31.200, "a", None),        # e nesse caso, antes da proporção havia algo pedindo atenção (luz quente)
    (31.200, 33.633, "foto", "zoom"),   # a depressão lateral que chamamos de hip dips (a foto que ela pôs)
    (33.633, 36.600, "f", None),        # então o planejamento foi construído em etapas
    (36.600, 43.467, "a", None),        # na primeira sessão... (o par) porque projetar essa região superior do glúteo
    (43.467, 47.867, "f", None),        # sem antes tratar o hip dips faz com que o resultado não fique harmonioso
    (47.867, 61.933, "a", None),        # já na segunda sessão... (foto e resultado) e não termina aí... (luz quente)
    (61.933, 65.767, "f", "pb"),        # a harmonização glútea não é um evento, é um processo
    (65.767, 68.567, "a", "volta"),     # o que ela me pediu era o destino
    (68.567, 71.800, "f", "pb"),        # o que o corpo dela precisava era o ponto de partida
    (71.800, 74.433, "a", "volta"),     # um bom resultado não começa na aplicação
    (74.433, 76.833, "a", None),        # começa com uma avaliação bem feita e
    (76.833, 79.500, "f", None),        # um planejamento pensado para cada paciente
]
# transições por cima (gerar.py): luz quente nas trocas de take sem fala cortada, clarão na saída do 1º P&B
TRANSICOES = [
    {"t": 7.400, "tipo": "flash", "zoom": False, "som": "brilho", "vol": 0.25},
    {"t": 26.833, "tipo": "luz", "zoom": False, "som": "whoosh-transicao", "vol": 0.8},
    {"t": 47.867, "tipo": "luz", "zoom": False, "som": "whoosh-transicao", "vol": 0.8},
]
# legenda: altura do meio do bloco em cada plano (no top jeans dela; no fechado ele desce)
ALTURA = {"a": 1340, "f": 1500, "foto": 1340}

# frases (primeira palavra, última palavra, linhas): cada linha é (primeira, última, estilo); estilos:
# fina (Poppins 400, branca), negrito (700 bege, a palavra que pesa, no mesmo tamanho), grande e creme (800 bege,
# 1,43x), serifa (Poppins 400 itálica bege, 1,48x; era a Playfair na 2ª versão)
F, N, G, C, S = "fina", "negrito", "grande", "creme", "serifa"
FRASES = [
    [(0, 1, F)], [(2, 6, F)], [(7, 9, C)],
    [(10, 13, F)], [(14, 17, F)], [(18, 19, G), (20, 21, F)],
    [(22, 26, F), (27, 27, N)],
    [(28, 30, F), (31, 32, N)], [(33, 36, F)], [(37, 39, F)], [(40, 43, F), (44, 44, N)],
    [(45, 47, F)], [(48, 49, F), (50, 50, N)], [(51, 52, F), (53, 55, C)],
    [(56, 58, F)], [(59, 61, F)], [(62, 64, F), (65, 65, N)], [(66, 68, F), (69, 71, N)],
    [(72, 74, F)], [(75, 77, F)], [(78, 80, F), (81, 81, N)], [(82, 82, F), (83, 84, C)], [(85, 87, F), (88, 88, S)],
    [(89, 91, F)], [(92, 93, F), (94, 95, C)],
    [(96, 98, N)], [(99, 101, F), (102, 103, N)],
    [(104, 106, F)], [(107, 110, F)], [(111, 114, F), (115, 115, N)], [(116, 120, F)], [(121, 122, F), (123, 123, S)],
    [(124, 125, F), (126, 127, G)], [(128, 131, F)], [(132, 134, F)], [(135, 137, F)],
    [(138, 140, F), (141, 141, N), (142, 142, F)], [(143, 145, F)],
    [(146, 149, C)],
    [(150, 153, F), (154, 154, N)], [(155, 156, F)], [(157, 160, F)], [(161, 162, F), (163, 164, N)],
    [(165, 167, F)], [(168, 171, G)], [(172, 174, S)],
    [(175, 179, F)], [(180, 181, F), (182, 182, N)],
    [(183, 188, F)], [(189, 190, F), (191, 193, C)],
    [(194, 196, F)], [(197, 199, F), (200, 200, N)], [(201, 203, F), (204, 206, G)],
    [(207, 209, F)], [(210, 211, F), (212, 213, C)],
]
GRANDES = {G, C, S}             # estilos que vão numa linha própria, embaixo da fina

# as fotos (estilo da referência A), presas à fala
FOTO_FAIXA = (0.000, 3.933)          # o antes no alto, enquanto ela diz "essa paciente... projeção no glúteo"
FOTO_PAR = (36.800, 40.433)          # antes e depois da 1ª sessão, na fala da 1ª sessão
FOTO_UNICA = (48.200, 53.500)        # o antes da 2ª etapa, na fala da 2ª sessão
FOTO_CHEIA = (53.500, 56.967)        # o resultado de hoje: "que foi a queixa dela desde o início. e não termina aí"
# durante o par e a foto única a legenda sobe para logo acima da foto, como na referência A
ALTURA_COM_FOTO = 1075
