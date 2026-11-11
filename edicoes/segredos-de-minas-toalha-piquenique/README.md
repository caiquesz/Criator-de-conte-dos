# Segredos de Minas — "toalha piquenique" (Sara)

Vídeo bruto (Drive): 1080x1920, 30,0 s. A Sara fala sentada à mesa nos primeiros 13,6 s; o resto é b-roll da toalha xadrez, com a voz dela por cima.
O vídeo final (`segredos_de_minas_toalha_piquenique_editado.mp4`, 27,0 s, H.264 1080x1920 30 fps, bt709) foi entregue na conversa.

Mesmo estilo dos vídeos anteriores da Sara:

| Item | Como |
|---|---|
| Legenda padrão | Coolvetica branca, 1 a 3 palavras, sempre centralizada em y=1330, fade suave. |
| Destaques | DM Serif Display Itálico branca, no centro (y=1010 nas falas): mesa bonita, boa toalha, procurando, toalha piquenique, bonita / alegre e / aconchegante, família, valorizar a decoração, garanta já, cores e tamanhos disponíveis. |
| Altura | O bloco de 3 linhas da fala desce para y=1080 para não encostar no queixo. No b-roll, cada destaque usa a altura menos clara da toalha (y=900 a 1140). |
| Sem caixa | Texto branco puro, sem caixa, contorno ou sombra. A toalha xadrez é clara (40 a 58% de pixels claros), então no b-roll o contraste é menor que nos outros vídeos. |
| Rosto | Rastreado num recorte ampliado (`FACE_CROP=240,100,840,900`). O texto central fica sempre ≥ 59 px abaixo do queixo. |
| Área segura | `scripts/check_safe.py` dá 0 violações nos 811 frames. |
| SFX | Só clique: em "toalha piquenique", "garanta já" e "cores e tamanhos". |
| Cortes | 10 segmentos, 30,0 s → 27,0 s (9 pausas e respirações removidas). Tem dissolve entre os dois takes da fala. O corte do bruto para o b-roll ficou seco, porque cai dentro da pausa removida e não tem sobra de imagem. |
| Áudio e cor | Voz original, sem EQ, compressão ou normalização (amostras idênticas ao bruto fora dos fades). Nenhuma correção de cor: as médias Y/U/V batem com o bruto (diferença de ~0,02). |
