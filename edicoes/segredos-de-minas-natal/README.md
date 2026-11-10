# Segredos de Minas — "3 presentes de Natal" (edição do reels)

Projeto de edição do vídeo bruto (`copy_428CED46-….mov`, 1080x1920, 44,4 s, 6 takes) seguindo:

- **Referência de edição** (`@anoomaker`, reel `DdtgYv0ye3O`): fonte, hierarquia de tamanhos, entrada dos textos, legenda curta.
- **Referência de SFX** (`@alinebahz`, reel `Dfhrdcfx1Kv`): o estilo dos efeitos (pop, whoosh, click, brilho), usados com moderação.

O vídeo final (`segredos_de_minas_natal_editado.mp4`, 40,2 s, H.264 1080x1920 30 fps, bt709) foi entregue direto na conversa. Ele não fica no git porque tem cerca de 60 MB.

## O que foi feito

| Item | Como |
|---|---|
| Cortes de pausa e respiração | 12 segmentos (`scripts/edl.py`). Os pontos de corte foram conferidos no envelope de áudio (−40 dB), deixando cerca de 40 ms de respiro. O vídeo passou de 44,4 s para 40,2 s. |
| Transição entre takes | Dissolve curto de 6 frames (0,2 s), só no vídeo. Usa a "sobra" silenciosa do take anterior, então o áudio entra no tempo certo. |
| Zoom in / zoom out | Push-ins lentos (1,00 → 1,035) no começo de cada take, punch-in (1,10 a 1,16) nos jump cuts e nos preços, e um zoom out lento no CTA (1,06 → 1,00). O pivô do zoom é o rosto. |
| Fonte | **Coolvetica** (a mesma da referência, com a ligadura "qu" e o "t" curvo). É a única família usada, em vários tamanhos. |
| Legenda | Curta (1 a 3 palavras), minúscula, branca, com entrada letra a letra com blur, igual à referência. Fica no peito quando ela não segura produto e logo abaixo do queixo quando segura. |
| Produto + preço | Card abaixo do queixo (no colo), centralizado no queixo: nome em branco e preço grande em laranja (`#f2920c`, cor tirada da referência). **Sem contorno e sem sombra.** |
| Títulos | Blocos empilhados com tamanhos diferentes, como na referência ("três opções de / presente / de natal", "por menos de / R$ 22", "sem precisar / gastar muito", "clique no / link abaixo", "presentear / nesse natal"). |
| SFX | Só 6: whoosh no título, pop em cada um dos 3 preços, click em "link abaixo" e um brilho em "nesse natal". Todos foram sintetizados (sem licença de terceiros) e ficam de 5 a 10 dB abaixo da voz. |
| Áudio | A voz é a original, sem EQ, sem compressão e sem normalização. Só há fades de 5 ms nos cortes. Fora dos fades, as amostras são idênticas ao bruto. |
| Cor | Nenhuma correção de cor. O vídeo é processado direto nos planos YUV 4:2:0 bt709 do original. As médias Y/U/V da saída batem com o bruto (diferença de ~0,04). |
| Sem música | Conforme pedido. |

## Estrutura

```
scripts/
  transcribe.py   # transcrição com timestamps por palavra (faster-whisper)
  words.py        # junta 2 modelos, ajusta os onsets pela energia e mapeia para a timeline final
  face_track.py   # rastreia queixo e nariz (MediaPipe Face Landmarker)
  edl.py          # lista de cortes, zooms e dissolves (a "timeline")
  anchors.py      # posição do queixo/rosto em cada segmento, já com o zoom aplicado
  gen_overlay.py  # gera a composição HyperFrames (todos os textos e as animações GSAP)
  audio.py        # emenda a voz e adiciona os SFX
  render.py       # cortes, zoom e dissolve em YUV + aplica os textos + encode
hyperframes/      # composição HyperFrames (camada de texto com fundo transparente)
dados/            # transcrição, eventos de texto, âncoras e relatório de áudio
```

## Como renderizar de novo

Use uma pasta de trabalho `$S` com `src/raw.mov`, `work/`, `scripts/` (copie os scripts para lá) e `models/face_landmarker.task`.

```bash
pip install faster-whisper opencv-python-headless mediapipe scipy numpy pillow
python scripts/transcribe.py work/voice16k.wav work/transcript.json large-v3
python scripts/transcribe.py work/voice16k.wav work/transcript_medium.json medium
python scripts/face_track.py $S src/raw.mov work/face.json
python scripts/anchors.py $S
python scripts/words.py $S

# camada de texto (HyperFrames)
cd hyperframes
mkdir -p assets/fonts assets/js
#  - assets/fonts/Coolvetica-Rg.otf  (baixar em typodermicfonts.com, licença Typodermic Desktop EULA)
#  - assets/js/gsap.min.js           (npm i gsap && cp node_modules/gsap/dist/gsap.min.js assets/js/)
python ../scripts/gen_overlay.py $S index.html
npx hyperframes@0.9.30 lint .
npx hyperframes@0.9.30 render . --format png-sequence -o $S/work/ovl --fps 30

# áudio + vídeo final
python scripts/audio.py $S work/mix.wav
python scripts/render.py $S out/segredos_de_minas_natal_editado.mp4 --overlay work/ovl --audio work/mix.wav --crf 19
```

Para mudar um texto ou um horário, edite as chamadas `cap(...)`, `stack(...)`, `name_card(...)` e `price_card(...)` em `gen_overlay.py` (os tempos são da timeline final) e renderize de novo a camada de texto e o `render.py`.
