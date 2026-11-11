# Casa Marina: edição do reel de unboxing

Vídeo bruto: `copy_61C673C5-00F2-4F88-ACCF-1E32521DE24E.MOV` (Drive), 72 s, 1080x1920, 30 fps.
Entrega: `casa-marina-unboxing-editado.mp4` (H.264, 1080x1920, 30 fps, ~6,5 Mbps, AAC 192k).

Fora desta versão: color grading e música de fundo. As cores do bruto foram mantidas: o vídeo é decodificado e recodificado na mesma matriz BT.709.

## O que foi feito

| Tempo | Efeito |
|---|---|
| 0,00 a 1,95 s | Logo da Casa Marina **sem o fundo de papel** (só letras e símbolo, na cor marrom da marca). Entra com um fade de 0,35 s, fica parada e some com fade, um leve desfoque e uma leve ampliação. SFX: pop. |
| 2,00 a 3,77 s (take 2) | **Zoom suave no adesivo** da caixa (até 1,7x, com curva ease-in-out). O zoom segue a posição do adesivo quadro a quadro (`assets/track_adesivo.json`). SFX: clique. |
| 32,45 a 36,12 s | **Sousplat** / em fio de malha |
| 40,80 a 42,56 s | **Tapete redondo** / de crochê |
| 43,05 a 45,22 s | **Jogo de passadeira** / feito em tear manual |
| 47,82 a 49,26 s | **Tapete geométrico em crochê** / e em fio de malha |
| 50,00 a 55,26 s | **Tapete retangular de crochê** / em fio de malha |
| 55,56 a 57,36 s | **Tapete redondo menor** / de crochê |

Cada nome de produto entra com um **risquinho fino** (sem ponta de seta), que se desenha a partir da peça. Depois o texto aparece com fade e uma pequena subida, e no fim tudo some com fade antes do corte. SFX: pop quando o texto aparece.

### Tipografia
A combinação **Noto Serif + Montserrat** foi tirada do reel de referência de combinações de fontes:
- Linha 1: Noto Serif Regular, 54 px (nome do produto)
- Linha 2: Montserrat Regular, 31 px, com um leve espaçamento entre letras (complemento)

Não há contorno na fonte. Sobre fundo claro (parede, piso) o texto sai no marrom da logo (`#3A241C`). Sobre a própria peça (passadeira e tapetes retangulares) sai em branco quente, só com uma sombra bem difusa, sem contorno.

### Área segura (Instagram Reels)
Todos os textos ficam entre y = 260 e y = 1100 px e entre x = 90 e x = 900 px. Assim eles passam longe do topo (interface), da faixa de baixo (legenda e @) e da coluna de botões da direita.

### Efeitos sonoros
Só **pop** e **clique**, com um efeito por informação que aparece (8 no total). Arquivos CC0 do pacote *Interface Sounds* da Kenney (`assets/sfx`).
O áudio original da câmera (ruído ambiente bem baixo, cerca de -40 LUFS) foi mantido por baixo. Também foi gerada uma versão `-so-sfx`, sem o áudio ambiente, para colocar a música direto no Instagram. Ela foi enviada à parte e não está no repositório, para não deixá-lo pesado. Para gerar de novo, use o `audio_so_sfx.wav` do `mix_audio.py`.

## Observação sobre a ordem dos produtos
No vídeo, a ordem é: sousplat, tapete redondo, **passadeira**, geométrico, **retangular**, redondo menor. Os nomes foram aplicados de acordo com a peça que aparece em cada cena. O verde oval (66,4 s) e o close final (teal e cru) não estão na lista e ficaram sem nome.

## Como renderizar de novo
```bash
# estrutura esperada (pasta de trabalho):
#   raw/video.MOV, logo/logo_casa_marina.png, t2/track.json, fonts/{NotoSerif,Montserrat}.ttf
python3 scripts/make_logo.py logo/logo_src.jpg logo/logo_casa_marina.png
python3 scripts/track_sticker.py raw/video.MOV t2/track.json
python3 scripts/render.py --preview 0.5,3.5,44.0          # stills para conferir
python3 scripts/render.py --render out/video_noaudio.mp4  # vídeo sem áudio
python3 scripts/render.py --cues > out/cues.json          # tempos dos SFX
python3 scripts/mix_audio.py out/cues.json assets/sfx/pop.ogg assets/sfx/clique.ogg \
        out/audio_ambiente_sfx.wav out/audio_so_sfx.wav raw/video.MOV
```
Os tempos, as posições e os textos de cada produto ficam na lista `LABELS` em `scripts/render.py`.
