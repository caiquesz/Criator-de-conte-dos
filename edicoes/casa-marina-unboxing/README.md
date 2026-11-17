# Casa Marina: edição do reel de unboxing

Vídeo bruto: `copy_61C673C5-00F2-4F88-ACCF-1E32521DE24E.MOV` (Drive), 71,9 s, 1080x1920, 30 fps.

**Entrega atual: `casa-marina-unboxing-v14.mp4`.** O vídeo tem 38,9 s, gravado no deck de madeira, com color grading. É H.264 Main@4.0, 1080x1920 a 30 fps, com faixa de áudio em silêncio.
As versões anteriores ficaram no histórico do git (v13 `aac6a06`, v12 `f3abec4`, v11 `ef70f53`, v10 `9b82e24`, v9 `2120ca6`). A versão com o piso original continua em `casa-marina-unboxing-editado-v5.mp4`.

## v14: ajustes sobre a v13
- **Adesivo mais curto:** continua em câmera lenta (0,6x), mas agora fica 1,6 s na tela em vez de 2,6 s. É o trecho 0,6 a 2,2 s do `adesivo_slow.mp4`, em que o adesivo aparece inteiro.
- **Saiu o tapete branco tirado da caixa** (6855) na parte do tapete redondo. A sequência agora é: tira o teal da caixa → ela folheando os 3 redondos maiores (6882).
- O master limpo da v14 é cortado direto do master graduado da v13, com o mesmo grading (quadros 0 a 77, 90 a 137, 156 a 1042 e 1079 a 1231). As legendas são as mesmas da v13 (`scripts/render_v14.py`).

## v13: ajustes sobre a v12
- **Vermelho estourado corrigido** (`scripts/grade_v13.py`):
  - o celular já grava o canal vermelho dos tapetes vermelhos no limite quando estão no sol (25 a 37% da peça);
  - na v12, o tone mapping empurrava esse canal ainda mais e o vermelho ficava chapado, com cara de neon e puxando para o laranja;
  - agora nenhuma etapa que clareia passa um canal de 0,95, o split tone age só nos tons neutros, os vermelhos saturados têm uma leve rolagem que devolve a textura do crochê, o brilho nas altas luzes ficou menor e há um soft clip que preserva a luminância;
  - o resto do look da v12 continua igual.
- **Tapete vermelho com o azul:** saiu o 6875 e entrou o **6877** (0,5 a 2,0 s). Ele tem o vermelho mais profundo e menos estourado, com a câmera passando devagar pelos dois tapetes.
- **Nomes por mais tempo:**
  - cada nome entra assim que ela tira a peça da caixa e fica até o fim do take da peça no ambiente. O sousplat, por exemplo, passou de ~2 s para ~5 s;
  - o texto fica parado na mesma posição ao longo dos cortes;
  - a posição de cada nome foi escolhida para ficar legível em todos os takes que ele atravessa (`scripts/label_spots_v13.py`). Fica no centro o retangular; sobem um pouco o sousplat, o geométrico, a passadeira, a sala, o redondo menor e o redondo.
- **Tapete para sala:** agora com a medida, **"medida 1,50 x 2,00 m"**, na linha manuscrita.

## v12: ajustes sobre a v11
- **Color grading profissional** (`scripts/grade_v12.py`), em duas etapas, como uma árvore de nós de colorista. O antes/depois está em `assets/antes_depois_grading_v12.jpg`.
  - **Primária, por take (casamento dos planos):**
    - balanço de branco: as áreas neutras de cada take (deck, caixa, parede) são puxadas 60% em direção a um mesmo branco levemente quente, com limite de ±6%, para as cores das peças não mudarem. Os takes do retangular na sombra (mais azulados) passam a combinar com os de sol;
    - exposição: o meio-tom das áreas neutras é igualado entre os takes, para não haver saltos de brilho nos cortes.
  - **Look (todos os quadros), editorial suave, na linha da referência da Westwing:**
    - tone mapping local com filtro guiado (respeita bordas, sem halo): suaviza o contraste do sol forte, abre as sombras e mantém a textura dos pontos de crochê;
    - curva fílmica: pretos levemente levantados e altas luzes com rolagem longa;
    - split tone: sombras neutras-quentes e altas luzes cremosas;
    - "de-vibrance": o fundo de baixa saturação (madeira, grama, pele) fica mais contido e as cores fortes das peças ficam fiéis;
    - leve brilho nas altas luzes e uma vinheta bem sutil.
- **Take com falha (geométrico saindo da caixa):** no trecho usado antes (6857, 5,4 s), a dobra do tapete com a sombra do braço parecia uma dupla exposição. Isso está no próprio vídeo e não tem como consertar. Agora o take usa o final limpo do mesmo vídeo (7,0 a 8,25 s), com o tapete esticado e a mão na borda.
- **Textos na opção B:** sem risquinho e centralizados no meio do vídeo. Nos takes em que o meio é claro ou muito estampado, o texto sobe para uma área mais calma.
  - A posição foi escolhida medindo brilho e textura no master graduado.
  - Ficam no centro: sousplat, retangular e redondo.
  - Sobem: geométrico, passadeira, sala e redondo menor.

## v11: ajustes sobre a v10
- **Adesivo em câmera lenta:** o trecho 1,0 a 2,75 s do 6849 roda a 0,6x, com interpolação de movimento (`minterpolate`, sem fantasmas no adesivo). Ficam 2,6 s na tela, então dá para ler "Casa Marina" com calma.
- **"Piscar" antes do TAPETE GEOMÉTRICO:** na v10 o risquinho aparecia sozinho por ~5 quadros antes do texto, junto com uma sombra escura forte, e isso parecia uma falha. Agora o texto entra num único fade suave (nome, e a linha de baixo 0,12 s depois), sem nenhum elemento aparecendo sozinho, e com a sombra bem mais difusa.
- **Saiu o take do tapete branco** (6872), que era o mesmo tapete dos redondos menores.
- **Tapetes redondos maiores no fecho:** a tirada da caixa do verde/teal (6854) e do cru (6855) foi para o fim, logo antes do vídeo novo **6882** (ela folheando os 3 redondos maiores: verde, cru e teal). O 6882 substitui os ovais (6883) e leva o nome **TAPETE REDONDO / de crochê**.
- **Débora abrindo o tapete para sala** (vídeo novo **6884**, 1,9 a 4,5 s) entra antes do 6890.
- **Fonte nova, no estilo da referência Westwing:**
  - nome do produto em **Cormorant Garamond** (serifada fina, caixa alta, letras espaçadas);
  - material em **Allura** (manuscrita elegante), logo abaixo;
  - branco, sem contorno, só uma sombra bem difusa.
- **Sem risquinho:** o texto fica centralizado, no alto do quadro, sobre o deck (opção C). Assim não cobre a peça.
  - As outras opções estão em `assets/opcoes_risquinho_v11.jpg`: A com risquinho reto, B no centro do vídeo, C centralizado no alto, D no alto com um fio fino entre as linhas.
  - Qualquer uma sai com `python3 scripts/render_v11.py CLEAN.mp4 OUT.mp4 --style line|center|top|divider`.

| Saída | Trecho |
|---|---|
| 0,0 a 2,6 s | Deck + logo → caixa chegando |
| 2,6 a 5,2 s | Adesivo em câmera lenta |
| 5,2 a 7,9 s | Abre a caixa → papel de seda |
| 7,9 a 13,1 s | Sousplat: tira o cru e o vermelho → mesinha de madeira (nome) |
| 13,1 a 18,0 s | Tapete retangular: tira o marinho → vermelho e marinho no deck (nome) |
| 18,0 a 21,8 s | Tapete geométrico: tira da caixa → aberto no deck (nome) |
| 21,8 a 25,4 s | Jogo de passadeira: tira da caixa → as 3 peças no deck (nome) |
| 25,4 a 30,0 s | Tapete para sala: a Débora abre o tapete (6884) → tapete estendido (6890, nome) |
| 30,0 a 33,6 s | Tapete redondo menor: os tapetes vão aparecendo um a um (nome) |
| 33,6 a 41,2 s | Tapete redondo: tira o teal e o cru → ela folheando os 3 redondos maiores (6882, nome) → véu branco com a logo |

## v10: ajustes sobre a v9
- **Tapetes redondos menores mais naturais** (`scripts/menores_live.py`):
  - saiu o efeito de pop com escala; agora é stop motion com o **vídeo real**;
  - para cada tapete já parado no deck entra um trechinho ao vivo (~0,4 s), com a câmera estabilizada (SIFT + homografia) e recortada na área comum;
  - os trechos são ligados por corte seco: o deck fica parado e o tapete novo simplesmente está lá.
- **Sem zoom no adesivo.**
- **Inícios cortados:** cada take começa no momento em que ela **passa a mão** nos tapetes. Isso vale para o sousplat cru e o vermelho, o redondo teal e o cru, o retangular marinho e o vermelho, o geométrico, a passadeira e os ovais.
- **Color grading** (`scripts/grade.py`), suave e quente, sem mudar a cor das peças:
  - pretos levemente levantados e altas luzes mais suaves, porque o sol no deck estava forte;
  - um toque de calor nos meios-tons e nas altas luzes;
  - saturação -5% no geral e um pouco menos nos verdes e cianos (grama e grade), para manter as cores do crochê fiéis.
- O take da Débora abrindo o tapete para sala ainda não estava no Drive (entrou na v11).

## v9: ajustes sobre a v8
- **Abertura:** saiu o véu branco. Agora aparece só a logo, branca e com sombra difusa, por cima do deck vazio. Ela some rápido (até 1,6 s) enquanto a caixa é colocada no chão.
- **Jogo de passadeira:** o nome agora está no **conjunto de 3 peças** vinho e branco (6862). O tapete cinza e vermelho (6890) entrou como produto separado: **TAPETE PARA SALA** (nome em uma linha).
- **Mais curto:** de 54,7 s para 40,1 s.
  - A tirada do sousplat da caixa caiu para 0,9 s em cada cor, porque ele já aparece em destaque na mesa.
  - Todos os outros takes também foram enxugados.
- **Tapetes redondos menores aparecendo um a um** (`scripts/menores_fx.py`): em vez de mostrar ela jogando, os tapetes surgem no deck um de cada vez.
  - Foram escolhidos 7 momentos do vídeo 6871 com os tapetes já parados, sem mão nem tapete no ar.
  - A câmera foi alinhada entre esses momentos (SIFT + homografia), e o enquadramento é a área que todos têm em comum, renderizada direto do 4K.
  - Cada tapete novo "surge": entra com fade e uma leve escala de 0,9 para 1. Um push-in suave dá movimento ao trecho.
- O final continua igual: véu branco com a logo.

| Saída | Trecho |
|---|---|
| 0,0 a 4,2 s | Deck vazio + logo → caixa chegando → zoom no adesivo |
| 4,2 a 6,9 s | Abre a caixa → papel de seda |
| 6,9 a 11,7 s | Sousplat: tira o cru e o vermelho (rápido) → mesinha de madeira (nome) |
| 11,7 a 16,1 s | Tapete redondo: tira o teal e o cru → cru no deck (nome) |
| 16,1 a 21,0 s | Tapete retangular: tira o marinho → vermelho e marinho no deck (nome) |
| 21,0 a 24,8 s | Tapete geométrico: tira da caixa → aberto no deck (nome) |
| 24,8 a 28,6 s | Jogo de passadeira: tira da caixa → as 3 peças no deck (nome) |
| 28,6 a 30,6 s | Tapete para sala (nome) |
| 30,6 a 35,3 s | Tapete redondo menor: os tapetes vão aparecendo um a um (nome) |
| 35,3 a 40,1 s | Fecho: ovais verde, cru e teal → véu branco com a logo |

## v8: regravação no deck de madeira
Os vídeos novos (pasta do Drive, 30 clipes, 4K, iPhone) foram gravados direto no fundo de madeira. Por isso **não teve troca de piso nem IA**. O único take reaproveitado do vídeo antigo é o do **sousplat na mesinha de madeira** (prato e close do vermelho).

Montagem (mesma proposta "tira da caixa → peça no ambiente"):
| Saída | Trecho | Clipes |
|---|---|---|
| 0,0 a 8,0 s | Caixa chegando no tapete de fibra (com a logo e o véu branco) → zoom suave no adesivo → abre a caixa → papel de seda | 6847, 6849, 6850, 6851 |
| 8,0 a 14,5 s | **Sousplat**: tira o cru → tira o vermelho → mesinha de madeira (prato e close do vermelho). Nome no close | 6852, 6853, vídeo antigo |
| 14,5 a 20,4 s | **Tapete redondo**: tira o teal → tira o cru → cru no deck. Nome no deck | 6854, 6855, 6872 |
| 20,4 a 26,8 s | **Tapete retangular**: tira o marinho → vermelho e marinho no deck. Nome no marinho | 6861, 6875, 6876 |
| 26,8 a 31,6 s | **Tapete geométrico**: tira da caixa → aberto no deck. Nome no deck | 6857, 6868 |
| 31,6 a 39,3 s | **Jogo de passadeira**: tira da caixa → vinho e branco no deck → cinza e vermelho. Nome no último | 6859, 6862, 6866, 6890 |
| 39,3 a 48,9 s | **Tapete redondo menor**: o cru cai no deck → laranja, taupe, pink e azul vão caindo → pilha | 6870, 6871 |
| 48,9 a 54,7 s | Fecho: ovais verde, cru e teal sendo arrumados → véu branco com a logo | 6883 |

- `scripts/build_master_v8.py` monta a base limpa a partir dos clipes. A lista de cortes está em `EDL` e as cores são as originais, sem color grading.
- `scripts/render_v8.py` aplica por cima os mesmos efeitos da v5:
  - logo e véu branco na abertura e no final;
  - zoom suave de 1,3x no adesivo, seguindo o adesivo (`track_sticker_v8.py`);
  - nomes em Unbounded + Coming Soon, brancos, com risquinho reto e parado, e sombra difusa mais forte por causa do sol no deck. As posições foram escolhidas com `place_search_v8.py`.

## v7: piso de laminado de madeira em todos os takes
Mesma edição da v5. O piso de cerâmica branca virou laminado de carvalho claro em todos os takes em que o chão aparece. A troca é feita em duas camadas:

1. **IA (Higgsfield, FLUX 3 Video Edit)**, que é a base dos takes em que a IA trocou bem o piso: caixa, sousplat, tapete redondo cinza, geométrico, passadeira e redondos menores (branco e pilha).
   - `scripts/floor_composite.py` usa a madeira da IA **só nos pixels do piso**. Tapetes, mãos e caixa continuam com os pixels originais em 1080p.
2. **Laminado real com rastreamento de câmera (`scripts/retexture.py`)**, usado nos takes em que a IA falhou ou deixou cerâmica: tapete redondo marrom, tapete retangular (aberto, close e marrom), passadeira saindo da caixa, primeiro take dos redondos menores, oval verde e close final.
   - A textura é uma foto de laminado em alta resolução: *Laminate Floor 02*, da Poly Haven, licença CC0 (`assets/textura/`).
   - A cor foi ajustada para bater com a madeira da IA dos outros takes (média e desvio no espaço Lab).
   - A câmera é rastreada (optical flow + homografia por take), então as tábuas acompanham o movimento e a perspectiva do chão.
   - A orientação e o tamanho das tábuas seguem a grade dos rejuntes da cerâmica.
   - A sombra original do chão (pés, pessoa, tapetes) é mantida: a luminância de baixa frequência do piso original multiplica a textura.
   - A máscara cobre a cerâmica clara, a cerâmica na sombra, o reflexo de luz, os rejuntes e o piso que aparece pelos furinhos do crochê.
   - Os parâmetros de cada take ficam em `assets/plano_textura_piso.json`.
3. Por cima entram a logo, o véu branco, o zoom e os textos da v5 (`scripts/render_v6.py`).

O `scripts/residual_tile.py` mede quanto de cerâmica sobra em cada take. Em todos os takes com chão, o resultado é ~0%. O que a métrica ainda marca nos takes da caixa e da passadeira é o papel de seda branco e as listras creme. Nos takes da mesa, é a parede.

## v5: fontes da combinação "Sequel + CC-Doodly" e risquinho reto
- **Fontes:** a 2ª combinação do reel de referência. A Sequel é paga e a CC-Doodly é exclusiva do CapCut, então usei as equivalentes livres mais parecidas:
  - **Unbounded ExtraBold, 46 px, caixa-alta** (como a Sequel), com o nome da peça;
  - **Coming Soon, 40 px, manuscrita** (como a CC-Doodly), com o material.
- Texto **centralizado e branco**, sem contorno, só com uma sombra difusa.
- **Risquinho reto (vertical) e parado:** ele não acompanha mais o movimento do vídeo. Nasce na peça e cresce até o texto, e depois o texto aparece.
  - O sousplat tem o texto embaixo e o risquinho sobe até o sousplat vermelho, longe do prato.
  - O geométrico tem o texto em cima, no piso, e o risquinho desce até o tapete.
  - Nos outros, o texto fica sobre a peça e o risquinho sobe até ela.
- As posições foram escolhidas com `scripts/place_search.py` e `scripts/bg_luma.py`, para o fundo do texto branco ficar escuro durante todo o tempo do nome.
- O resto é igual à v4: véu branco com logo na abertura e no final, e zoom suave no adesivo.
- Ver `scripts/render_v5.py`.

## v4 (teste com texto branco)
- **Abertura com véu branco:** o vídeo começa desfocado sob um véu branco e a logo marrom aparece junto. Depois a logo some com fade e desfoque, o véu se dissolve e o vídeo começa nítido (0 a 1,9 s).
- **Final com fade out:** o último take vai desfocando sob o véu branco e a logo volta a aparecer, espelhando a abertura (últimos ~1,7 s).
- **Zoom no adesivo mais suave:** foi de 1,7x para 1,3x.
- **Textos brancos e maiores:** Cormorant Garamond Italic 84 px + Lexend Mega Light 28 px (na v3 eram 70/24). Não há contorno, só uma sombra bem difusa.
  - Cada nome fica sobre uma parte escura da peça. Medi o brilho do fundo quadro a quadro com o `scripts/bg_luma.py`.
  - Exceção: o geométrico ficou no mesmo layout da v3, sobre o piso, com a sombra difusa um pouco mais forte.
- **Sousplat:** o nome foi para o close do sousplat vermelho, e o risquinho aponta para o sousplat, não mais para o prato.
- Ver `scripts/render_v4.py` (`--plan` mostra cortes e tempos).

Fora desta versão: color grading e música. As cores do bruto foram mantidas: o vídeo é decodificado e recodificado na mesma matriz BT.709, e conferi que o brilho médio de cada corte é igual ao do bruto.

## Montagem "tira da caixa → peça no ambiente"
Cada peça sai da caixa e, logo no take seguinte, aparece no ambiente com o nome.

| Saída | Trecho |
|---|---|
| 0,00 a 6,77 s | Abertura: caixa + logo (0 a 1,95 s) → zoom no adesivo → abre a caixa → papel de seda → revela as peças |
| 6,77 a 13,90 s | **Sousplat**: tira o bege → tira o vermelho → bege na mesa (prato, copo) → close do vermelho. Nome de 9,85 a 12,76 s |
| 13,90 a 19,00 s | **Tapete redondo**: tira o taupe → cinza no chão → marrom no chão. Nome de 17,20 a 18,96 s |
| 19,00 a 26,20 s | **Tapete retangular**: tira o marinho → tira o vermelho → marinho aberto no chão → close → marrom. Nome de 22,30 a 24,17 s |
| 26,20 a 31,00 s | **Tapete geométrico**: tira da caixa → close → aberto no chão. Nome de 29,52 a 30,96 s |
| 31,00 a 35,73 s | **Jogo de passadeira**: tira da caixa → arrumando no chão. Nome de 33,48 a 35,65 s |
| 35,73 a 41,73 s | **Tapete redondo menor**: tira o branco da caixa → os menores caindo no chão (inclusive o branco) → pilha. Nome de 37,13 a 38,93 s |
| 41,73 a 44,93 s | Fecho: oval verde → close da textura (teal e cru) |

A lista completa de cortes, em quadros do bruto, está em `EDL` no `scripts/render_v3.py` (`python3 scripts/render_v3.py --plan`).

## Efeitos visuais
- **Logo sem o fundo de papel** (só letras e símbolo, no marrom da marca). Entra com um fade de 0,35 s e some com fade, um leve desfoque e uma leve ampliação, até 1,95 s.
- **Zoom suave no adesivo** (take 2, até 1,7x, com curva ease-in-out). O zoom segue o adesivo quadro a quadro (`assets/track_adesivo.json`).
- **Nome dos produtos** com um **risquinho fino** (sem ponta de seta), que se desenha a partir da peça. Depois o texto entra com fade e uma pequena subida, e some com fade antes do corte.

### Tipografia (v3)
A combinação é a 1ª do reel de referência (Anafogue + LexendMega). A Anafogue é exclusiva do CapCut e não tem download nem licença públicos, então usei a itálica livre mais parecida com ela:
- **Em cima (destaque):** Cormorant Garamond Italic, peso 600, 70 px, com o tipo da peça
- **Embaixo (ainda mais minimalista):** Lexend Mega Light, 24 px (a mesma da referência), com o material e a técnica

Os nomes foram divididos em tipo da peça (em cima) e material (embaixo):
Sousplat / em fio de malha · Tapete redondo / de crochê · Tapete retangular / de crochê em fio de malha · Tapete geométrico / em crochê e em fio de malha · Jogo de passadeira / feito em tear manual · Tapete redondo menor / de crochê

### Cor única
Todos os nomes e risquinhos usam o **marrom da logo** (`#3A241C`), sem contorno e sem sombra. Para ficar legível em todos os takes, o texto sempre fica sobre uma área clara:
- parede, no sousplat
- piso, no redondo, no geométrico e no redondo menor
- piso do take aberto, no retangular. Por isso esse take foi para o começo da sequência.
- faixa creme da passadeira

### Área segura (Instagram Reels)
Todos os textos ficam entre y = 260 e y = 900 px e entre x = 90 e x = 900 px. Assim eles passam longe do topo, da faixa da legenda e da coluna de botões da direita.

## Como renderizar de novo
```bash
# estrutura esperada (pasta de trabalho):
#   raw/video.MOV, logo/logo_casa_marina.png, t2/track.json,
#   fonts/{CormorantGaramond-Italic,LexendMega}.ttf (+ as fontes da v1 para o render.py)
python3 scripts/make_logo.py logo/logo_src.jpg logo/logo_casa_marina.png
python3 scripts/track_sticker.py raw/video.MOV t2/track.json
python3 scripts/render_v3.py --plan                        # lista de cortes e tempos dos nomes
python3 scripts/render_v3.py --preview 3.3,11.0,34.2       # stills para conferir
python3 scripts/render_v3.py --render out/v3/master.mp4    # vídeo sem áudio
```

## Histórico
- **v3**: o tapete branco que sai da caixa foi para o bloco do tapete redondo menor. Entraram as fontes novas (Cormorant + Lexend Mega) e todos os textos ficaram em marrom.
- **v2** (commit `f1ea05a`): primeira remontagem "caixa → ambiente", 44,8 s, sem áudio, com Noto Serif + Montserrat e texto em marrom e branco.
- **v1** (commit `a6061e1`): ordem original do bruto, 71,9 s, com o som ambiente e SFX de pop e clique (CC0, Kenney, em `assets/sfx`).
