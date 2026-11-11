# Casa Marina: edição do reel de unboxing

Vídeo bruto: `copy_61C673C5-00F2-4F88-ACCF-1E32521DE24E.MOV` (Drive), 71,9 s, 1080x1920, 30 fps.

**Entrega atual: `casa-marina-unboxing-editado-v2.mp4`.** O vídeo tem 44,8 s, em H.264 1080x1920 a 30 fps (~7 Mbps), e **não tem áudio** (sem som ambiente, sem efeitos e sem música).

Fora desta versão: color grading e música. As cores do bruto foram mantidas: o vídeo é decodificado e recodificado na mesma matriz BT.709, e conferi que o brilho médio de cada corte é igual ao do bruto.

## v2: remontagem "tira da caixa → peça no ambiente"
Cada peça sai da caixa e, logo no take seguinte, aparece no ambiente com o nome. A ordem segue a lista de produtos. Os takes foram enxugados para ficar só o momento em que a peça aparece bem. Assim o vídeo caiu de 71,9 s para 44,8 s, sem deixar nenhum produto de fora.

| Saída | Trecho |
|---|---|
| 0,00 a 6,77 s | Abertura: caixa + logo (0 a 1,95 s) → zoom no adesivo → abre a caixa → papel de seda → revela as peças |
| 6,77 a 13,90 s | **Sousplat**: tira o bege → tira o vermelho → bege na mesa (prato, copo) → close do vermelho. Nome de 9,85 a 12,76 s |
| 13,90 a 20,20 s | **Tapete redondo**: tira o taupe → tira o cru → cinza no chão → marrom no chão. Nome de 18,40 a 20,16 s |
| 20,20 a 27,40 s | **Tapete retangular**: tira o marinho → tira o vermelho → close do marinho → marrom → marinho no chão. Nome de 23,50 a 27,37 s |
| 27,40 a 32,20 s | **Tapete geométrico**: tira da caixa → close → aberto no chão. Nome de 30,72 a 32,16 s |
| 32,20 a 36,93 s | **Jogo de passadeira**: tira da caixa → arrumando no chão. Nome de 34,68 a 36,85 s |
| 36,93 a 41,60 s | **Tapetes redondos menores** caindo no chão até formar a pilha. Nome de 37,13 a 38,93 s |
| 41,60 a 44,80 s | Fecho: oval verde → close da textura (teal e cru) |

A lista completa de cortes, em quadros do bruto, está em `EDL` no `scripts/render_v2.py` (`python3 scripts/render_v2.py --plan`).

## Efeitos visuais (os mesmos da v1)
- **Logo sem o fundo de papel** (só letras e símbolo, no marrom da marca). Entra com um fade de 0,35 s e some com fade, um leve desfoque e uma leve ampliação, até 1,95 s.
- **Zoom suave no adesivo** (take 2, até 1,7x, com curva ease-in-out). O zoom segue o adesivo quadro a quadro (`assets/track_adesivo.json`).
- **Nome dos produtos** com um **risquinho fino** (sem ponta de seta), que se desenha a partir da peça. Depois o texto entra com fade e uma pequena subida, e some com fade antes do corte.

### Tipografia
A combinação **Noto Serif + Montserrat** foi tirada do reel de referência de combinações de fontes:
- Linha 1: Noto Serif Regular, 54 px (nome do produto)
- Linha 2: Montserrat Regular, 31 px, com um leve espaçamento entre letras (complemento)

Não há contorno na fonte. Sobre fundo claro (parede, piso) o texto sai no marrom da logo (`#3A241C`). Sobre a própria peça (passadeira e tapetes retangulares) sai em branco quente, só com uma sombra bem difusa.

### Área segura (Instagram Reels)
Todos os textos ficam entre y = 260 e y = 1100 px e entre x = 90 e x = 900 px. Assim eles passam longe do topo, da faixa da legenda e da coluna de botões da direita.

## Como renderizar de novo
```bash
# estrutura esperada (pasta de trabalho):
#   raw/video.MOV, logo/logo_casa_marina.png, t2/track.json, fonts/{NotoSerif,Montserrat}.ttf
python3 scripts/make_logo.py logo/logo_src.jpg logo/logo_casa_marina.png
python3 scripts/track_sticker.py raw/video.MOV t2/track.json
python3 scripts/render_v2.py --plan                        # lista de cortes e tempos dos nomes
python3 scripts/render_v2.py --preview 3.3,10.4,31.4       # stills para conferir
python3 scripts/render_v2.py --render out/v2/master.mp4    # vídeo sem áudio
```

## Histórico
- **v1** (commit `a6061e1`): ordem original do bruto, 71,9 s, com o som ambiente e SFX de pop e clique (CC0, Kenney, em `assets/sfx`). Os scripts dela continuam aqui: `render.py` e `mix_audio.py`.
