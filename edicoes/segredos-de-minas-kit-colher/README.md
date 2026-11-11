# Segredos de Minas — "kit colher" (Sara)

Vídeo bruto (Drive): 1080x1920, 37,2 s. A Sara fala no começo, no meio e no fim; entre as falas há b-roll dos kits (pano de prato + colher de pau).
O vídeo final (`segredos_de_minas_kit_colher_editado.mp4`, 31,3 s, H.264 1080x1920 30 fps, bt709) foi entregue na conversa. Não está no git porque tem 46 MB.

## O que foi pedido e como ficou

| Pedido | Como |
|---|---|
| Legenda padrão sem tanto dinamismo, sempre no mesmo lugar | Coolvetica branca, 1 a 3 palavras, **sempre centralizada em y=1330**, com entrada e saída por fade suave. |
| Palavras de destaque em outra fonte, no centro | **DM Serif Display Itálico** (Google Fonts, licença OFL), branca, centralizada em y=960: "amigos secretos", "Natal", "kit de colher", "custo-benefício", "pano de prato + colher de pau", "R$ 15,00", "Segredos de Minas", "estampas natalinas", "todo o Brasil", "link abaixo". Enquanto o destaque está na tela, a legenda padrão dessas mesmas palavras não aparece. |
| Sem tampar o rosto da Sara | A posição do rosto foi conferida frame a frame com o face track: o cartão de destaque fica sempre ≥ 209 px abaixo do queixo. |
| Legível sobre os panos brancos, sem contorno nem sombra | **Cartão de vidro fosco** atrás do texto: o vídeo sob o cartão é desfocado e levemente escurecido (fator 0,62). O efeito é aplicado em YUV no `render.py`, a partir da camada `hyperframes/vidro`, que contém só o formato dos cartões e usa a mesma timeline do texto. |
| Espaço para postar | `scripts/check_safe.py` dá 0 violações nos 940 frames, tanto no texto quanto nos cartões. |

## Edição

- **Cortes:** 10 segmentos (`scripts/edl.py`), 37,2 s → 31,3 s. Saem as pausas e respirações e um trecho de 4,6 s sem fala. Desse trecho fica 1,1 s de close das estampas natalinas como respiro visual, com "estampas natalinas" ainda na tela.
- **Transições e zoom:** dissolve de 6 frames nas trocas entre fala e b-roll. Zoom in lento, punch-in nos jump cuts e um leve zoom out no final.
- **SFX:** 5, de 5 a 13 dB abaixo da voz:
  - whoosh em "amigos secretos";
  - pop em "kit de colher" e em "R$ 15,00";
  - brilho no corte para as estampas natalinas;
  - clique em "link abaixo".
- **Áudio:** voz original, sem EQ, compressão ou normalização. Fora dos fades de corte, as amostras são idênticas ao bruto.
- **Cor:** nenhuma correção. As médias Y/U/V da saída batem com o bruto, com diferença de ~0,04.

## Renderizar de novo

Mesmos passos de `../segredos-de-minas-kit-lavabo`. As diferenças:

```bash
# fontes: hyperframes/{texto,vidro}/assets/fonts/ com Coolvetica-Rg.otf e DMSerifDisplay-Italic.ttf
#   (DM Serif Display: fonts.google.com/specimen/DM+Serif+Display, OFL)
python scripts/gen_overlay.py $S hyperframes/texto hyperframes/vidro
(cd hyperframes/texto && npx hyperframes@0.9.30 render . --format png-sequence -o $S/work/ovl)
(cd hyperframes/vidro && npx hyperframes@0.9.30 render . --format png-sequence -o $S/work/mask)
python scripts/check_safe.py $S/work/ovl 1 && python scripts/check_safe.py $S/work/mask 1
python scripts/render.py $S out/segredos_de_minas_kit_colher_editado.mp4 \
    --overlay $S/work/ovl --mask $S/work/mask --audio $S/work/mix.wav --crf 19
```
