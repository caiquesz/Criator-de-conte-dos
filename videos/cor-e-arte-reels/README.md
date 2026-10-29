# Reels Cor e Arte Artesanato — edição em HyperFrames

O vídeo chega já cortado. Esta pasta só adiciona as camadas de edição — legendas, títulos/destaques,
zooms, transições e efeitos sonoros — no estilo medido nas referências (ver [STYLE.md](STYLE.md)).

## Fluxo

```bash
# 1. padroniza o vídeo, lista os cortes, transcreve e recorta a pessoa no gancho
tools/prepare.sh ~/Downloads/video-cortado.mp4 3.5      # 3.5 = fim do gancho em segundos

# 2. plano de edição: copie edit.example.json para edit.json e preencha
#    (palavras pelo id da transcrição: w0, w1, …; transições nos tempos de assets/cuts.txt)

# 3. gera a composição
node tools/build.mjs

# 4. confere
npx hyperframes check
npx hyperframes snapshot --at 0.5,1.5,8

# 5. renderiza e normaliza o áudio para Reels
npx hyperframes render --quality delivery --output renders/render.mp4
tools/finish.sh renders/render.mp4 renders/final.mp4
```

A transcrição usa `faster-whisper` (`pip install faster-whisper`, modelo `large-v3-turbo`).

## edit.json

| Campo | O que faz |
| --- | --- |
| `video.src`, `video.focus` | vídeo base e ponto de foco do zoom (rosto) |
| `fix` | correções de palavras da transcrição: `{ "w12": "Cor e Arte" }` |
| `captions.y`, `captions.size` | altura e tamanho das legendas |
| `cutout` | recorte da pessoa (`tools/prepare.sh`) e até quando ele cobre o título |
| `titles[]` | gancho, destaques e seções: `from`/`to` (palavras que saem da legenda), `y`, `enter` (`blur-rise`, `blur`, `type`, `cut`), `exit` (`blur`, `cut`), `end` ou `hold`, `sfx` (`each`, `first`, `whoosh`, `none`) e `lines[].tokens[]` com `w` (palavra que dispara), `t` (texto), `s` (`sans`, `sans-sm`, `serif`, `serif-up`), `size` |
| `zooms[]` | `{ t, scale }` punch-in seco; com `dur` vira zoom suave |
| `transitions[]` | `{ t, type }` com `flash`, `silhouette` ou `leak`, no instante do corte |
| `sfx[]` | efeitos extras `{ t, name: "click" \| "whoosh" \| "pop", vol }` |
| `sfxVolume` | muda o volume padrão (`click` 1, `whoosh` 0,6, `pop` 0,5) |

`node tools/build.mjs` reescreve `index.html` e `compositions/` — edite o `edit.json`, não o HTML gerado.

## Efeitos sonoros

`assets/sfx/click-*.mp3`: "Mouse click sounds" por Masgame, CC0 (Openverse/Freesound).
`assets/sfx/whoosh-*.mp3` e `pop.mp3`: biblioteca do HyperFrames (licença Pixabay).
