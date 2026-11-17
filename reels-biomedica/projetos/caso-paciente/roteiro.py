"""Roteiro do Caso de paciente, 2ª versão, nas duas referências que a cliente mandou em 17/11:

- antes e depois como no vídeo da dentista (referência A): a foto do antes numa faixa no alto com ela
  embaixo (sem recorte da pessoa: na 1ª versão o recorte ficou feio na borda); o par lado a lado, encostado,
  com um fio branco no meio, atravessando o peito dela e crescendo de leve ao entrar; uma foto só numa faixa
  de cantos arredondados que entra saindo do desfoque; o resultado em tela cheia, esmaecendo;
- todo o resto como o vídeo da moça de blazer marrom (referência B): planos aberto e fechado alternando em
  corte seco (o "zoom in, zoom out"), preto e branco nas falas de drama (entra seco, sai num clarão ou num
  esmaecer escurecido para a cor), luz quente nas transições e as legendas da referência (veja LEGENDAS).
  Na 3ª versão (17/11) a cliente tirou a cor da referência B (fica a cor original) e pediu Poppins e mais
  efeitos sonoros; na 4ª, a cor igual à que ela mandou (só a luz igualada entre os takes) e as legendas iguais
  às da referência, só que em Poppins.

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
# ── legendas: como as da referência B (a moça de blazer marrom), só que em Poppins ──────────────────
# 4ª versão (17/11): "as legendas que você fez não têm nada a ver com as das referências; a única coisa que eu
# falei foi para usar a fonte Poppins", "espaçamento entre linhas bem diminuído", "não colocou vírgulas".
# Medido na referência, quadro a quadro: uma frase curta por vez (2 a 6 palavras, entre as pausas), numa linha,
# centralizada, perto da altura das mãos (~78% da tela); troca em corte seco, a frase inteira de uma vez (nada de
# palavra por palavra); letra fina itálica minúscula (~45 px em 1080); a palavra que pesa em negrito itálico do
# mesmo tamanho; de vez em quando uma frase curta sozinha em negrito itálico maior, entrando com um borrão de lado;
# a palavra de impacto grande, em negrito reto bege, com a palavra fina pequena em cima; uma serifada itálica
# ("leve e harmonioso" lá, "harmonioso" aqui). Duas linhas só no fim, com entrelinha normal (~1,45).
# Cada legenda é uma lista de linhas; cada linha, de trechos (primeira palavra, última palavra, estilo):
#   f fina (Poppins Light itálica, branca) · n negrito (Poppins ExtraBold itálica, branca, mesmo tamanho)
#   F forte (a frase sozinha, ExtraBold itálica maior, com borrão de lado) · b bege (ExtraBold reta #EED6A4, grande,
#   entra seca na palavra dela) · s serifa (Playfair Display itálica; fora desde a 5ª versão)
# 5ª versão (17/11): um padrão só de cor, a fala branca e tudo o que pesa bege (n, F e b; a serifada branca saiu,
# "harmonioso" virou bege como as outras palavras grandes), e letras e linhas mais juntas (montar_plano.py).
f, n, F, b, s = "f", "n", "F", "b", "s"
LEGENDAS = [
    [[(0, 4, f)]],                              # Essa paciente chegou até mim
    [[(5, 6, f), (7, 9, n)]],                   # me pedindo projeção no glúteo
    [[(10, 13, f)]],                            # e a primeira coisa
    [[(14, 17, f)]],                            # que eu fiz foi
    [[(18, 21, F)]],                            # não colocar a projeção (P&B)
    [[(22, 27, f)]],                            # e hoje eu vou te explicar
    [[(28, 30, f), (31, 32, n)]],               # essa paciente tem 29 anos,
    [[(33, 36, f)]],                            # treina, se alimenta bem,
    [[(37, 39, f)]],                            # cuida do corpo
    [[(40, 44, f)]],                            # e o pedido era preciso
    [[(45, 47, f)]],                            # melhorar o contorno
    [[(48, 50, f)]],                            # e ganhar projeção
    [[(51, 52, f)], [(53, 55, b)]],             # na parte / superior do glúteo
    [[(56, 59, f)]],                            # mas antes de definir
    [[(60, 61, f)]],                            # qualquer procedimento
    [[(62, 65, f)]],                            # eu avaliei as características
    [[(66, 69, f), (70, 71, n)]],               # e as proporções de cada corpo
    [[(72, 74, f)]],                            # e nesse caso,
    [[(75, 77, f)]],                            # antes da proporção
    [[(78, 80, f), (81, 81, n)]],               # havia algo pedindo atenção,
    [[(82, 84, f)]],                            # a depressão lateral
    [[(85, 87, f)], [(88, 88, b)]],             # que chamamos de / hip dips
    [[(89, 91, f)]],                            # então o planejamento
    [[(92, 93, f), (94, 95, n)]],               # foi construído em etapas
    [[(96, 98, f)]],                            # na primeira sessão,
    [[(99, 100, f)]],                           # nós trabalhamos
    [[(101, 101, f), (102, 103, n)]],           # o contorno lateral,
    [[(104, 105, f)]],                          # porque projetar
    [[(106, 110, f)]],                          # essa região superior do glúteo
    [[(111, 114, f), (115, 115, n)]],           # sem antes tratar o hip dips
    [[(116, 120, f)]],                          # faz com que o resultado
    [[(121, 122, f)], [(123, 123, b)]],         # não fique / harmonioso
    [[(124, 127, f)]],                          # já na segunda sessão,
    [[(128, 131, f)]],                          # com a base pronta,
    [[(132, 134, f)]],                          # nós conseguimos trabalhar
    [[(135, 137, f)]],                          # essa região superior
    [[(138, 142, f)]],                          # que foi a queixa dela
    [[(143, 145, f)]],                          # desde o início
    [[(146, 149, F)]],                          # e não termina aí
    [[(150, 152, f)]],                          # essa paciente segue
    [[(153, 154, f)]],                          # em tratamento
    [[(155, 158, f)]],                          # e manutenções de acordo
    [[(159, 164, f)]],                          # com o que o corpo responde
    [[(165, 167, f)]],                          # a harmonização glútea (P&B)
    [[(168, 171, F)]],                          # não é um evento,
    [[(172, 173, f)], [(174, 174, b)]],         # é um / processo
    [[(175, 179, f)]],                          # o que ela me pediu
    [[(180, 181, f), (182, 182, n)]],           # era o destino,
    [[(183, 188, f)]],                          # o que o corpo dela precisava (P&B)
    [[(189, 190, f)], [(191, 193, b)]],         # era o / ponto de partida
    [[(194, 196, f)]],                          # um bom resultado
    [[(197, 200, f)]],                          # não começa na aplicação,
    [[(201, 203, f)], [(204, 204, f), (205, 206, n)]],   # começa com uma / avaliação bem feita
    [[(207, 210, f)]],                          # e um planejamento pensado
    [[(211, 211, f)], [(212, 213, b)]],         # para / cada paciente
]
# o texto: minúsculo (só a primeira palavra do vídeo com maiúscula, como o "Deixa" da referência), com as vírgulas
# da fala e sem ponto final; correções do Whisper e vírgulas que faltavam:
TEXTO = {88: "hip dips", 115: "hip dips", 98: "sessão,"}
# a base da legenda (a borda de baixo da última linha), em px: a linha fina fica com o meio em ~1500, como na
# referência; com o par e a foto única na tela, logo acima da foto, como na referência A
BASE_LEGENDA = 1530
BASE_COM_FOTO = 1105

# as fotos (estilo da referência A), presas à fala
FOTO_FAIXA = (0.000, 3.933)          # o antes no alto, enquanto ela diz "essa paciente... projeção no glúteo"
FOTO_PAR = (36.800, 40.433)          # antes e depois da 1ª sessão, na fala da 1ª sessão
FOTO_UNICA = (48.200, 53.500)        # o antes da 2ª etapa, na fala da 2ª sessão
FOTO_CHEIA = (53.500, 56.967)        # o resultado de hoje: "que foi a queixa dela desde o início. e não termina aí"
