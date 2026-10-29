# Estilo de edição — Cor e Arte Artesanato (Reels)

Medido quadro a quadro (30 fps) e no áudio separado das três referências enviadas
(INID "sala de jantar", Ramos Casa "árvore de Natal" e Ramos Casa "novidades Le Creuset").
O vídeo chega já cortado: nada aqui altera tempo, só adiciona camadas por cima.

## Legendas (todo o vídeo)

| | Valor | De onde vem |
| --- | --- | --- |
| Fonte | Poppins SemiBold (600), 46 px em 1080×1920 | Poppins por preferência |
| Espaçamento | letras −0,045 em, entrelinha 1,04 | pedido: letras bem juntas, mas legíveis |
| Cor | branco, **sem sombra** | pedido |
| Posição | centralizada, altura do peito da pessoa (y ≈ 1010–1210, por plano) | refs 1, 2 e 3 |
| Tamanho do bloco | 2–5 palavras, até 26 caracteres, 1 linha, nunca terminando em palavra fraca (de, a, com…) | refs |
| Quebra | pontuação, pausa ≥ 250 ms | refs |
| Animação | **nenhuma**: entra e sai no corte seco | as três refs |
| Texto | como foi falado, com vírgula e ponto | refs |

Quando um título ou destaque está na tela, não há legenda: as palavras dele não viram legenda e o que for
dito enquanto ele está na tela entra na legenda seguinte. Nos tópicos ("1. Algodão"), a frase que anuncia
o tópico ("A de algodão") sai da legenda, e a legenda volta logo depois dela.

Palavras-chave dentro da legenda (o adjetivo ou o substantivo que vende: "leve", "relevo", "diferença")
aparecem em Playfair Display Italic, 1,3× maior. No máximo uma por bloco e só onde ajuda.

## Títulos e destaques

- **Sans**: Poppins Bold (700), letras −0,055 em, entrelinha 0,86 — "Novidades", "Pergunta", "Como eu".
- **Serifada**: Playfair Display Italic, ~1,3× maior que o sans, 94% de opacidade, letras −0,035 em,
  entrelinha 0,82 e linhas encostando (margem negativa) — "do ano", "compro", "Le Creuset".
- **Serifada reta** (`serif-up`): Playfair Display normal — "Se eu estivesse" (ref 1).
- Cada palavra entra **no instante em que é falada** (40 ms antes):
  - `blur-rise` (ref 3): sobe 32% do tamanho da fonte, desfoque 16 px → 0, 0,24 s, `power3.out`;
  - `blur` (ref 2): desfoque 14 px → 0 e escala 1,06 → 1, 0,2 s, sem deslocamento;
  - `type` (ref 1): letra a letra, 45 ms por letra;
  - `cut`: aparece seco (títulos de seção da ref 1, "1. Buffet").
- Saída: desfoque 10 px + fade em 0,16 s, ou corte seco junto com a transição.
- **Gancho** (primeiros 2–4 s): o título fica **atrás da pessoa** (recorte do vídeo por cima), 30–55% coberto.

## Tópicos

"1. Algodão", "2. Lurex", "3. Escama": Playfair Display Italic sozinho, à direita, acima do produto,
no corte seco com um clique. **Sem cards de B-roll** (pedido do cliente).

## Zoom

Punch-in seco (sem animação) de 1,0 → 1,08–1,12 junto com a entrada do título, voltando a 1,0 no próximo
corte (ref 3). Ponto de foco no rosto. Nos B-rolls, aproximação lenta e contínua (1,0 → 1,09 durante o plano).

## Transições (só nos cortes que já existem no vídeo)

| Tipo | Como é | Ref |
| --- | --- | --- |
| `flash` | 1 frame branco cheio antes do corte, 1 frame a 45% depois | 2 |
| `silhouette` | a pessoa vira silhueta branca por 1 frame, depois o flash | 3 (fim do gancho) |
| `leak` | estouro de luz quente (~0,4 s) atravessando o corte | 1 |

Os demais cortes ficam secos, como nas referências.

## Som

- **Clique duplo de mouse** (3 variações, CC0) em cada palavra de título que entra e em cada flash —
  é o efeito que as refs 2 e 3 usam. Nível: pico do clique ≈ −6 dBFS com a voz em −18 dB RMS (igual às refs).
- **Whoosh** (3 variações) nas transições.
- O pico de cada efeito cai 1 frame depois da imagem.
- Mix final normalizado para −14 LUFS, pico −1,5 dBTP (`tools/finish.sh`).

## Medida certa

- Gancho nos primeiros segundos, sempre.
- Um destaque (sans + serifada) a cada ~8–12 s, nas frases que carregam a mensagem
  (benefício, número, nome do produto, chamada final). Nunca dois seguidos.
- Seções numeradas ("1. …", "2. …") quando a fala enumera itens.
- Sem logo.
