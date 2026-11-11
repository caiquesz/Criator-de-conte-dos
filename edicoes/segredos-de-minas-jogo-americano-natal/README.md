# Segredos de Minas — "jogo americano de Natal" (Sara)

Vídeo bruto (Drive): 1080x1920, 41,1 s. São dois takes da Sara na mesa, depois o b-roll dos jogos americanos e um take final segurando o kit.
O vídeo final (`segredos_de_minas_jogo_americano_natal_editado.mp4`, 38,1 s, H.264 1080x1920 30 fps, bt709) foi entregue na conversa.

Mesmo estilo do `../segredos-de-minas-kit-colher` e do `../segredos-de-minas-cortina-corta-luz`:

| Item | Como |
|---|---|
| Legenda padrão | Coolvetica branca, 1 a 3 palavras, sempre centralizada em y=1330, fade suave. |
| Destaques | DM Serif Display Itálico branca, centralizada em y=980: gastar muito, mesa linda, pequenos detalhes, jogo americano de Natal, Segredos de Minas, 6 americanos + 6 guardanapos, 100% algodão, toque natalino, família, outras opções de cores natalinas, Natal, link abaixo, todo o Brasil. |
| Sem caixa | Texto branco puro, sem caixa, contorno ou sombra. |
| Rosto | Rastreado num recorte ampliado (`FACE_CROP=240,120,840,920 scripts/face_track_crop.py`). O texto central fica sempre ≥ 69 px abaixo do queixo. |
| Área segura | `scripts/check_safe.py` dá 0 violações nos 1142 frames. |
| SFX | Só clique, conforme pedido: em "jogo americano de Natal", "100% algodão" e "link abaixo". |
| Cortes | 10 segmentos, 41,1 s → 38,1 s (pausas removidas). Tem dissolve nas trocas de take e um punch-in (zoom seco, sem cortar o áudio) em "Olha só esse jogo americano". |
| Áudio e cor | Voz original, sem EQ, compressão ou normalização (amostras idênticas ao bruto fora dos fades). Nenhuma correção de cor: as médias Y/U/V batem com o bruto (diferença de ~0,01). |

O `align.py` agora também lê porcentagem ("100%" → "cem por cento").
