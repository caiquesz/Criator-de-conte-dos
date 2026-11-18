# Edição: "Questão comum na prova do Detran" (Alexandre)

Reels final: 1080x1920, 30 fps, ~47 s (bruto de 63 s), -14 LUFS.

- **Cortes**: ~15,6 s de pausas mortas removidos (lista `CUTS_RAW` em `timeline.py`), inclusive a falsa
  largada antes de "remoção" e o trecho ininteligível perto do fim. Cada corte com câmera coincide com uma troca
  de zoom (1.0x / 1.12x) para parecer corte de ângulo.
- **Tempo das palavras**: texto conferido com Whisper large-v3 + medium e tempo exato por alinhamento forçado
  (wav2vec2 MMS_FA, `../alinhar.py`). O Whisper adiantava até 0,5 s algumas palavras depois de pausas.
- **Legenda constante**: mesmo estilo do vídeo da CNH, com os destaques em Oblisk **laranja**.
- **Cena 1 (ele sai do quadro, 1,2 s–11 s)**: o primeiro fundo vira a folha da prova. Selo "MUITO COMUM",
  a pergunta escrita palavra por palavra (som de lápis), marcador de combustível descendo até o E durante a pausa
  "sem... combustível", adesivo "LEMBRE!" preso debaixo do clipe (o clipe é redesenhado por cima: `assets/clipe.png`).
- **Papel amassando** (`crumple.html`): a folha inteira, com tudo que está escrito, vira uma bola de papel 3D
  (malha WebGL com vincos Worley e sombreamento facetado) e é arremessada pra fora, revelando o vídeo
  bem na hora em que ele volta pelo outro lado.
- **Cena 2 (ele sai de novo, ~25,7 s–37,2 s)**: fundo gradiente laranja com os 4 cartões de alternativa;
  dois riscados e descartados, os outros dois "parecidos", anzol "feito pra pegar", lupa na "atenção",
  cronômetro no "use o tempo". No gradiente os destaques ficam em branco, porque laranja sumiria no fundo laranja.
- **SFX**: pops e cliques, papel deslizando, lápis, papel amassando, whoosh do arremesso, marcador, tique-taque.

## Como re-renderizar

```bash
cd edicao_video && ./baixar_assets.sh && cd prova_detran
ffmpeg -i bruto2.mov -map 0:a:0 -ac 1 -ar 16000 audio16k.wav
python3 ../alinhar.py audio16k.wav dados/texto.txt dados/palavras.json   # opcional, já está salvo
python3 timeline.py dados/palavras.json timeline.json
node render_overlay.js /tmp/ov 4           # legendas + cenas (PNG com alpha)
node render_crumple.js /tmp/cr             # print da folha + bola de papel 3D
python3 audio.py bruto2.mov /tmp/audio.wav
python3 composite.py bruto2.mov /tmp/cr,/tmp/ov /tmp/audio.wav final.mp4
```

O `.MOV` do iPhone tem taxa de quadros variável: o `composite.py` converte para 30 fps constantes (`fps=30`)
antes de aplicar os cortes, para o vídeo bater com o áudio.

### Onde ajustar
- Cortes: `CUTS_RAW` em `timeline.py` (tempo do bruto). Frases/destaques: `PH`.
- Texto da legenda e o que o alinhador procura: `dados/texto.txt` (`R|erre` = mostra "R", fala "erre").
- Cenas: `buildA()` (folha) e `buildB()` (gradiente) em `overlay.html`. Amassado: `crumple.html`.
