# Segredos de Minas — "jogo americano Relíquia" (Sara)

Vídeo bruto (Drive): 1080x1920, 36,2 s. A Sara fala na mesa posta no começo e no fim; o meio é close dos jogos americanos e dos guardanapos com anel de crochê.
O vídeo final (`segredos_de_minas_jogo_americano_reliquia_editado.mp4`, 32,6 s, H.264 1080x1920 30 fps, bt709) foi entregue na conversa.

Mesmo estilo dos vídeos do kit colher, da cortina e do jogo americano de Natal:

| Item | Como |
|---|---|
| Legenda padrão | Coolvetica branca, 1 a 3 palavras, sempre centralizada em y=1330, fade suave. |
| Destaques | DM Serif Display Itálico branca, centralizada (y=960 nas falas): detalhe, toda a diferença, mesa posta, jogo americano Relíquia, peça avulsa, produzida em tear, 100% algodão, linda, outros modelos e cores, link abaixo, todo o Brasil. |
| Altura no b-roll | Onde não há rosto, alguns destaques descem um pouco (y=1040 a 1160) para o ponto mais escuro do quadro. Assim "peça avulsa", "tear", "100% algodão" e "outros modelos" ficam sobre o guardanapo vermelho e não sobre o branco do tecido e do anel de crochê. |
| Sem caixa | Texto branco puro, sem caixa, contorno ou sombra. |
| Rosto | Rastreado num recorte ampliado (`FACE_CROP=240,100,840,900`). O texto central fica sempre ≥ 210 px abaixo do queixo. |
| Área segura | `scripts/check_safe.py` dá 0 violações nos 978 frames. |
| SFX | Só clique: em "Relíquia", "100% algodão" e "link abaixo". |
| Cortes | 11 segmentos, 36,2 s → 32,6 s (10 pausas removidas, uma delas de 0,9 s). Tem dissolves nas trocas fala ↔ b-roll e entre os dois blocos de b-roll. |
| Áudio e cor | Voz original, sem EQ, compressão ou normalização (amostras idênticas ao bruto fora dos fades). Nenhuma correção de cor: as médias Y/U/V batem com o bruto (diferença de ~0,01). |
