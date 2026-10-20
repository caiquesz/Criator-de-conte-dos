# 🎬 Pós-produção — legendas estilo Reels sem mexer na montagem

Ferramenta que recebe um vídeo **já cortado e montado** e devolve o mesmo vídeo
com legendas sincronizadas no estilo dos presets (ou de um preset novo copiado
das referências). Nada é cortado, acelerado ou reordenado:

- o vídeo é re-encodado frame a frame (`-fps_mode passthrough`), mesmo nº de frames;
- o **áudio é copiado byte a byte** (`-c:a copy`) — a fala nunca é tocada;
- no fim, duração, nº de frames, resolução e **hash do áudio** são comparados
  com o original; se algo mudou o script sai com erro e marca "NÃO PUBLICAR".

## Instalação (uma vez)

```bash
pip install -r pos_producao/requirements.txt     # sherpa-onnx + numpy (ffmpeg precisa estar no PATH)
python pos_producao/baixar_modelos.py --modelo small   # Whisper ONNX + Silero VAD (GitHub, ~600 MB)
```

## Uso

```bash
# 1) primeira passada: transcreve e renderiza
python pos_producao/legendar.py meu_video.mp4 --preset reels_destaque

# 2) texto 100% correto: passe o roteiro/transcrição que o ASR só dá o tempo
python pos_producao/legendar.py meu_video.mp4 --texto roteiro.txt --destaque "tráfego,escalar"

# 3) revisou os cards no .legendas.json? Re-renderiza sem transcrever de novo
python pos_producao/legendar.py meu_video.mp4 --legendas-json pos_producao/saida/meu_video_legendado.legendas.json

# só gerar o .ass (para abrir no CapCut/Premiere/DaVinci) sem renderizar
python pos_producao/legendar.py meu_video.mp4 --so-ass
```

Saída em `pos_producao/saida/<nome>_legendado.mp4` + arquivos auxiliares:

| arquivo | o que é |
|---|---|
| `*.original.json` | registro do original (duração, frames, fps, hash do áudio) |
| `*.transcricao.txt` | texto por card com tempos — revise aqui |
| `*.legendas.json` | palavras + tempos; edite e reaproveite com `--legendas-json` |
| `*.ass` | legenda final (abre em qualquer editor) |
| `*.relatorio.md` | conferência: duração/frames/áudio ✅ ou ❌ |

Opções: `--max-palavras 3`, `--max-chars 18`, `--cor-sutil` (contraste +4 %, saturação +6 %, nitidez leve),
`--crf 17` (qualidade), `--modelo tiny|base|small|medium`.

## Presets (`pos_producao/presets/*.json`)

| preset | estilo |
|---|---|
| `reels_destaque` | Montserrat ExtraBold, caixa alta, branco com contorno preto, palavra falada em amarelo, pop na entrada |
| `reels_palavra` | Anton, palavra por palavra acumulando, palavra atual verde com pop |
| `reels_caixa` | Poppins ExtraBold sobre caixa preta translúcida, frase inteira, fade |

Para copiar uma referência, duplique um preset e ajuste: `fonte`, `tamanho` (base 1080×1920,
escala automática para outras resoluções), `cor_texto`, `cor_destaque`, `contorno`, `sombra`,
`posicao_y` (0–1, fração da altura), `max_palavras`, `max_chars_linha`, `modo`
(`destaque` | `palavra` | `card`), `animacao` (`pop` | `fade` | `sobe`), `fundo` (caixa),
`fundo_destaque` (caixinha colorida atrás da palavra atual), `palavras_chave`.

Fontes incluídas em `pos_producao/fonts/` (Google Fonts, licença OFL): Montserrat, Poppins, Anton, Bebas Neue.
Inter já vem no sistema. Para outra fonte, coloque o `.ttf` na pasta e use o nome da família no preset.

## Limitações conhecidas

- O Whisper ONNX usado aqui não dá tempo por palavra; o tempo é ancorado nos trechos de fala
  (VAD) e distribuído por palavra proporcionalmente às sílabas. Em frases longas pode haver
  desvio de ~100–200 ms; ajuste no `.legendas.json` se precisar.
- Transições entre takes e efeitos sonoros **não** são adicionados automaticamente — só com a
  referência em mãos e por decisão explícita, para não alterar o ritmo da montagem.
