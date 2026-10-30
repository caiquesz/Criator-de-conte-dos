# Reels Cor e Arte Artesanato — edição em HyperFrames

O vídeo chega já cortado. Esta pasta só adiciona as camadas de edição — legendas, títulos/destaques,
zooms, transições e efeitos sonoros — no estilo medido nas referências (ver [STYLE.md](STYLE.md)).
Cada vídeo tem o seu plano em `edits/<nome>.json`; os vídeos e renders ficam fora do git.

| Vídeo | Plano |
| --- | --- |
| Mantas natalinas | `edits/mantas-natalinas.json` |
| Live de Black Friday | `edits/black-friday.json` (voz tratada com `eq`) |

## Fluxo

```bash
# 1. padroniza o vídeo, trata a voz, lista os cortes, transcreve e recorta a pessoa no gancho
tools/prepare.sh ~/Downloads/video-cortado.mp4 black-friday 4.5 eq
#                                               nome         fim do gancho (0 = sem recorte)
#                                                                eq = corrige voz estridente/fina

# 2. plano de edição: copie edits/exemplo.json para edits/<nome>.json e preencha
#    (palavras pelo id da transcrição: w0, w1, …; transições nos tempos de assets/cuts/<nome>.txt)

# 3. gera a composição (index.html + compositions/)
node tools/build.mjs edits/black-friday.json

# 4. confere
npx hyperframes check
npx hyperframes snapshot --at 0.5,1.5,8

# 5. renderiza e normaliza o áudio para Reels
npx hyperframes render --quality delivery --output renders/black-friday-render.mp4
tools/finish.sh renders/black-friday-render.mp4 renders/black-friday-final.mp4
```

A transcrição usa `faster-whisper` (`pip install faster-whisper`, modelo `large-v3-turbo`).

## Voz (`tools/voz.sh`)

Só equalização, compressão leve e volume: a voz continua a mesma (a altura medida antes e depois não muda).
Sem `eq`, a voz é só nivelada em −16 LUFS, para os cliques ficarem na mesma proporção das referências.
Com `eq`: corte de ronco abaixo de 105 Hz, +3 dB de corpo em 300 Hz, −4 a −4,5 dB na faixa estridente
de 2,4–4,3 kHz e compressão 2,2:1. É cerca de metade da diferença medida contra as vozes das referências.

## edits/<nome>.json

| Campo | O que faz |
| --- | --- |
| `video.src`, `video.focus` | vídeo base e ponto de foco do zoom (rosto) |
| `fix` | correções de palavras da transcrição: `{ "w4": "Cor e Arte" }`; `""` apaga a palavra |
| `captions` | `y`, `size`, `maxWords`, `maxChars`; `yAt` muda a altura por trecho; `emph` põe palavras em serifada |
| `breakBefore` | força quebra de legenda antes dessas palavras |
| `cutout` | recorte da pessoa: `src`, `dur` e `windows` (trechos em que ela fica na frente do texto; para o vídeo inteiro, `prepare.sh` com o fim do gancho igual à duração) |
| `motionBlur` | `true` liga o desfoque de movimento do HyperFrames (chicotes e zooms) |
| `titles[]` | gancho, destaques e tópicos: `from`/`to` (palavras que saem da legenda), `y`, `align`, `padX`, `enter` (`blur-rise`, `blur`, `type`, `cut`, `pop`), `exit` (`blur`, `cut`), `end` ou `hold`, `sfx` (`each`, `first`, `whoosh`, `none`), `captions: "after-speech"` (legenda volta logo depois da fala), `dim` (escurece o fundo; não usar, o cliente não gosta) e `lines[]` com `gap`, `justify` e `tokens[]` (`w` palavra que dispara, `t` texto, `s` estilo `sans`/`sans-sm`/`serif`/`serif-up`/`badge`, `size`, `enter` próprio) |
| `cards[]` | trecho do vídeo num retângulo (não usado: o cliente não quer cards de B-roll) |
| `zooms[]` | `{ t, scale, origin }` punch-in seco; com `dur` vira zoom suave |
| `transitions[]` | `{ t, type }` com `flash`, `silhouette`, `leak`, `whip` (com `dir`: `left`/`right`) ou `zoom`, no instante do corte |
| `sfx[]` | efeitos extras `{ t, name: "click" \| "whoosh" \| "pop", vol }` |
| `sfxVolume` | muda o volume padrão (`click` 1, `whoosh` 0,6, `pop` 0,5) |

`node tools/build.mjs` reescreve `index.html` e `compositions/`: edite o plano, não o HTML gerado.

## Efeitos sonoros

`assets/sfx/click-*.mp3`: "Mouse click sounds" por Masgame, CC0 (Openverse/Freesound).
`assets/sfx/whoosh-*.mp3` e `pop.mp3`: biblioteca do HyperFrames (licença Pixabay).
