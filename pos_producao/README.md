# 🎬 Pós-produção — texto no vídeo sem mexer na montagem

Duas ferramentas, mesma regra: o vídeo recebido é montagem final. Nada é cortado,
acelerado ou reordenado. O áudio é copiado byte a byte e, no fim, duração, nº de frames,
resolução e hash do áudio são conferidos contra o original.

| ferramenta | estilo | quando usar |
|---|---|---|
| `tipografia.py` | **tipografia cinética atrás da pessoa** (referências enviadas: "o que **faz** uma casa de", "Literalmente na sua **rotina**", "Morar na **P**") | padrão para os Reels do Caique |
| `legendar.py` | legenda clássica de 2–4 palavras com palavra destacada | quando o vídeo pede legenda convencional |

## tipografia.py — estilo das referências

```bash
pip install -r pos_producao/requirements.txt
python pos_producao/baixar_modelos.py --modelo small --segmentacao

# 1ª passada: transcreve, monta o layout automático e renderiza
python pos_producao/tipografia.py video.mp4 --texto roteiro.txt --destaque "casa,rotina" --textura praia.jpg

# só o projeto (.cenas.json) para revisar posições/tamanhos antes de renderizar
python pos_producao/tipografia.py video.mp4 --texto roteiro.txt --so-cenas
# frames de prova em PNG nos tempos indicados (rápido, sem render completo)
python pos_producao/tipografia.py video.mp4 --cenas pos_producao/saida/video_tipografia.cenas.json --preview "1.2,4.5,9"
# render final a partir do projeto revisado
python pos_producao/tipografia.py video.mp4 --cenas pos_producao/saida/video_tipografia.cenas.json
```

O que ele faz, frame a frame:

1. segmenta a pessoa (u2net_human_seg, CPU, ~0,3 s/frame em 1080×1920);
2. desenha os blocos de texto da cena (camada `atras`), recoloca a pessoa por cima, desenha a camada `frente`;
3. cada palavra entra no instante em que é falada (pop 90→100 % + fade de 160 ms) e a composição sai em fade de 100 ms.

Três modelos de composição se alternam, um por frase (editáveis no preset):

| modelo | referência | composição |
|---|---|---|
| `faz` | "o que **faz** uma casa de" | linha curta no alto à direita · palavra gigante no centro com a **cena invertida** dentro das letras · linha leve abaixo |
| `rotina` | "Literalmente na sua **rotina**" | empilhado à esquerda · palavra-chave gigante **laranja** sobrepondo, na frente da pessoa |
| `morar` | "Morar na **P**" | linha grande branca · palavra gigante preenchida com **foto** (`--textura`) |

A palavra-chave de cada frase vem de `--destaque` ou, sem ela, da palavra de conteúdo mais longa.
Fontes: Quicksand 700/300 (geométrica arredondada da ref. 1); preset `tipografia_grotesca` usa
Inter Black com tracking apertado (refs. 2 e 3).

O `.cenas.json` é o projeto: por bloco, `texto`, `fonte`, `tamanho` (px a 1920 de altura),
`cor` ou `textura` (`inverter` | imagem), `pos` [x, y] em fração, `ancora`, `camada`, `inicio`/`fim`,
`anim` (`pop` | `fade` | `sobe` | `nenhuma`), `tracking`. Ajuste e renderize de novo.

---

# legendar.py — legendas clássicas

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
