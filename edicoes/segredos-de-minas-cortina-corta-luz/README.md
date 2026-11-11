# Segredos de Minas — "cortina corta-luz" (Sara)

Vídeo bruto (Drive): 1080x1920, 47,9 s. A Sara aparece de corpo inteiro no começo e no fim; o meio é b-roll das cortinas.
O vídeo final (`segredos_de_minas_cortina_corta_luz_editado.mp4`, 43,0 s, H.264 1080x1920 30 fps, bt709) foi entregue na conversa.

Mesmo estilo do `../segredos-de-minas-kit-colher`:

| Item | Como |
|---|---|
| Legenda padrão | Coolvetica branca, 1 a 3 palavras, **sempre centralizada em y=1330**, fade suave. |
| Destaques | **DM Serif Display Itálico** branca, centralizada em y=1060. Fica mais baixo que no kit colher porque a Sara aparece pequena no quadro e o queixo chega a y≈907. Destaques: cortinas, praticidade e beleza, cortina corta-luz, conforto, claridade, tecido duplo, voal, três tamanhos, as 3 medidas, três opções de cores, link abaixo e todo o Brasil. |
| Medidas | Cada tamanho entra conforme a fala: primeiro "3,00", depois " x 1,80 m", e embaixo, em fonte menor, "de comprimento". O mesmo vale para 3,00 x 2,20 m e 4,00 x 2,60 m. |
| Sem caixa | Texto branco puro, sem caixa, contorno ou sombra. |
| Rosto | O rosto é rastreado num recorte ampliado (`scripts/face_track_crop.py`), porque a Sara é pequena no quadro. O texto central fica sempre ≥ 61 px abaixo do queixo. |
| Área segura | `scripts/check_safe.py` dá 0 violações nos 1290 frames. |
| SFX | Só pop e clique: pop em "cortinas", "cortina corta-luz", "três tamanhos" e "três opções"; clique em "link abaixo". Ficam ~4 dB abaixo da voz. |
| Cortes | 15 segmentos, 47,9 s → 43,0 s (14 pausas e respirações removidas). Tem dissolve na passagem da fala para o b-roll; os cortes de b-roll do bruto ficam como estavam. |
| Áudio e cor | Voz original, sem EQ, compressão ou normalização (amostras idênticas ao bruto fora dos fades). Nenhuma correção de cor: as médias Y/U/V batem com o bruto (diferença de ~0,02). |

O alinhamento (`scripts/align.py`) agora entende medidas faladas: "1,80" é lido como "um e oitenta".

Para renderizar de novo, siga os mesmos passos do `../segredos-de-minas-kit-colher`, usando `scripts/face_track_crop.py` no lugar de `face_track.py`.
