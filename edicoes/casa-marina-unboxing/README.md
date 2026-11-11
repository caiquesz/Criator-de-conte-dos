# Casa Marina: edição do reel de unboxing

Vídeo bruto: `copy_61C673C5-00F2-4F88-ACCF-1E32521DE24E.MOV` (Drive), 71,9 s, 1080x1920, 30 fps.

**Entregas atuais: `casa-marina-unboxing-editado-v6-madeira.mp4` (piso de madeira) e `casa-marina-unboxing-editado-v5.mp4` (piso original).** Os dois têm 46,4 s, em H.264 1080x1920 a 30 fps (~7 Mbps), e **não tem áudio**.
As versões anteriores ficaram no histórico do git (v4 `c79e0aa`, v3 `ac19ed4`, v2 `f1ea05a`, v1 `a6061e1`).

## v6 (piso de laminado de madeira, com Higgsfield): `casa-marina-unboxing-editado-v6-madeira.mp4`
Mesma edição da v5, mas o piso de cerâmica branca virou laminado de carvalho claro.
- **IA:** usei o FLUX 3 Video Edit do Higgsfield, que sai em 704x1248 a 24 fps. A montagem limpa (sem textos) foi enviada em trechos de até 15 s.
  - O prompt pediu para trocar só o piso.
  - A IA gastou cerca de 1 crédito por segundo de vídeo, uns 46 créditos no total.
- **Composição (`scripts/floor_composite.py`):** o vídeo da IA não substitui o original. Ele só entrega o piso:
  - uma máscara acha o piso no vídeo original: pouca saturação, tom frio, textura lisa, rejuntes e furos do crochê;
  - nesses pixels entra a madeira da IA, alinhada no tempo (24→30 fps);
  - todo o resto (tapetes, mãos, caixa, textos) continua com os pixels originais em 1080p.
- Depois disso, a logo, o véu branco, o zoom e os textos da v5 são aplicados por cima (`scripts/render_v6.py`).
- **O que ainda tem piso de cerâmica:** nos takes em que a IA não trocou o piso, a cerâmica continua aparecendo. São eles:
  - o tapete retangular aberto e os closes dele (~22,8 a 26,7 s);
  - a parte de cima do close final (~43,4 a 46,4 s);
  - algumas manchinhas no tapete taupe saindo da caixa e no papel de seda.
  - Tentei refazer esses takes com um prompt mais forte, mas o Higgsfield bloqueou por limite diário de gerações. Dá para refazer quando o limite renovar (`assets/plano_piso_ia.json` lista os trechos usados).

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
