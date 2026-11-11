# Segredos de Minas — "kit colher" (Sara)

Vídeo bruto (Drive): 1080x1920, 37,2 s. A Sara fala no começo, no meio e no fim; entre as falas há b-roll dos kits (pano de prato + colher de pau).
O vídeo final (`segredos_de_minas_kit_colher_editado.mp4`, 31,3 s, H.264 1080x1920 30 fps, bt709) foi entregue na conversa. Não está no git porque tem 46 MB.

## O que foi pedido e como ficou

| Pedido | Como |
|---|---|
| Legenda padrão sem tanto dinamismo, sempre no mesmo lugar | Coolvetica branca, 1 a 3 palavras, **sempre centralizada em y=1330**, com entrada e saída por fade suave. |
| Palavras de destaque em outra fonte, no centro | **DM Serif Display Itálico** (Google Fonts, licença OFL), branca, centralizada em y=960: "amigos secretos", "Natal", "kit de colher", "custo-benefício", "pano de prato + colher de pau", "R$ 15,00", "Segredos de Minas", "estampas natalinas", "todo o Brasil", "link abaixo". Enquanto o destaque está na tela, a legenda padrão dessas mesmas palavras não aparece. |
| Sem tampar o rosto da Sara | A posição do rosto foi conferida frame a frame com o face track: o destaque fica sempre pelo menos 209 px abaixo do queixo. |
| Tudo branco, sem caixa de texto | A primeira versão tinha um cartão de vidro fosco atrás do texto. A pedido, ele foi removido: legenda e destaques são texto branco puro, sem caixa, contorno ou sombra. |
| Espaço para postar | `scripts/check_safe.py` dá 0 violações nos 940 frames. |

## Edição

- **Cortes:** 10 segmentos (`scripts/edl.py`), 37,2 s → 31,3 s. Saem as pausas e respirações e um trecho de 4,6 s sem fala. Desse trecho fica 1,1 s de close das estampas natalinas como respiro visual, com "estampas natalinas" ainda na tela.
- **Transições e zoom:** dissolve de 6 frames nas trocas entre fala e b-roll. Zoom in lento, punch-in nos jump cuts e um leve zoom out no final.
- **SFX:** só pop e clique, conforme pedido:
  - pop em "kit de colher", em "R$ 15,00" e em "natalinas";
  - clique em "link abaixo".
- **Áudio:** voz original, sem EQ, compressão ou normalização. Fora dos fades de corte, as amostras são idênticas ao bruto.
- **Cor:** nenhuma correção. As médias Y/U/V da saída batem com o bruto, com diferença de ~0,04.

## Renderizar de novo

Mesmos passos de `../segredos-de-minas-kit-lavabo`. A diferença é a fonte dos destaques:

```bash
# fontes em hyperframes/texto/assets/fonts/: Coolvetica-Rg.otf e DMSerifDisplay-Italic.ttf
#   (DM Serif Display: fonts.google.com/specimen/DM+Serif+Display, OFL)
python scripts/gen_overlay.py $S hyperframes/texto
(cd hyperframes/texto && npx hyperframes@0.9.30 render . --format png-sequence -o $S/work/ovl)
python scripts/check_safe.py $S/work/ovl 1
python scripts/audio.py $S $S/work/mix.wav
python scripts/render.py $S out/segredos_de_minas_kit_colher_editado.mp4 \
    --overlay $S/work/ovl --audio $S/work/mix.wav --crf 19
```
