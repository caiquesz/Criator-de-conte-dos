# Live Roda do Sol (11/11): vídeo de divulgação

Edição feita com [HyperFrames](https://hyperframes.heygen.com) (HTML → MP4).

- **Vídeo final:** `renders/live-roda-do-sol-final.mp4` (1080×1920, 30 fps, 21,6 s, áudio em −16 LUFS)
- **Vídeo bruto:** [Google Drive](https://drive.google.com/file/d/1B2fN3IEbHdzI5JAFZrMgOTDsp_xJlt5P/view)
- **Referências:** legenda e efeito, [reel @giubeckers](https://www.instagram.com/reel/DfcgCGiBxCQ/); efeitos sonoros, [reel @majusoarees](https://www.instagram.com/reel/Db1JEipPpeY/)

## O que foi feito

| Elemento | Decisão |
| --- | --- |
| **Texto atrás da pessoa** | Usado **uma vez só**, no gancho (0–3,6 s). "Estamos preparando mais uma" em branco e **LIVE DE SUCESSO** em amarelo bem clarinho (`#fff4c8`, League Gothic). Ela entra andando na frente do título e a cabeça cobre a parte de baixo do "SU". Fica menor e mais discreto que na referência, com um leve escurecimento do fundo só atrás do texto. |
| **Por que no gancho** | O primeiro frame do vídeo não tem ninguém (ela entra depois), então o título é o que segura quem passa o feed e funciona como capa. É também o plano com cabeça pequena e fundo mais limpo, onde o texto continua legível com ela na frente. No plano final, com a data, a cabeça grande taparia o "11 de novembro". |
| **Legenda contínua** | Uma palavra por vez, branca, Inter Bold, centralizada na altura do quadril (fora da área da interface do Reels). As palavras de destaque aparecem agrupadas e um pouco maiores: *11 de novembro*, *Roda do Sol*, *tapetes de sala*, *capas de almofada*, *mantas de sofá*, *jogos de passadeira*, *7 horas*. |
| **Efeitos sonoros** | Poucos, só na data e nos produtos (veja a tabela abaixo). |
| **Voz** | O áudio original veio baixo (−27 LUFS); a voz foi subida em +11 dB (`data-volume="3.5"`). |

### Efeitos sonoros

| Tempo | Fala | Som (tipo da referência) |
| --- | --- | --- |
| 4,0 s | "No dia **11 de novembro**" | hit (impacto grave, baixo) |
| 10,4 s | "**tapetes** de sala" | click |
| 12,0 s | "**capas** de almofada" | pop (som de interface) |
| 13,3 s | "**mantas** de sofá" | click |
| 14,6 s | "**jogos** de passadeira" | pop (som de interface) |
| 14,9 → 17,5 s | "e muito mais… Então no dia" | riser (cria a tensão antes da data) |
| 17,5 s | "**11 de novembro** às 7 horas" | hit |

Os sons vêm da biblioteca do HyperFrames (Pixabay, uso comercial liberado; ver `assets/sfx/CREDITS.md`).

## Estrutura

```
index.html                  vídeo + cenas + sons (volumes e tempos editáveis aqui)
compositions/hook-title.html  título do gancho (texto, cor, posição, animação)
compositions/captions.html    legenda contínua (gerada pelo script)
assets/video/hook-cutout.webm recorte da pessoa (0–3,6 s) com transparência
assets/transcript-words.json  transcrição palavra por palavra (faster-whisper medium, pt)
scripts/build_captions.py     gera compositions/captions.html a partir da transcrição
scripts/clean_matte.py        limpa a máscara do recorte (deixa só a pessoa)
```

## Como editar e renderizar de novo

Requer Node 22+ e FFmpeg.

```bash
cd videos/live-roda-do-sol

# 1. Vídeo-fonte (não versionado, 39 MB): baixe o .mov do Drive e converta para H.264
ffmpeg -i live.mov -c:v libx264 -crf 16 -pix_fmt yuv420p -c:a aac assets/video/live.mp4

# 2. Mudou a transcrição ou os destaques? Gere a legenda de novo
python3 scripts/build_captions.py

# 3. Prévia no navegador e render
npx hyperframes@0.9.23 preview
npx hyperframes@0.9.23 check
npx hyperframes@0.9.23 render -o renders/live-roda-do-sol-final.mp4 -q delivery --crf 18
```

Para refazer o recorte da pessoa: `npx hyperframes remove-background` no trecho 0–3,6 s e depois
`scripts/clean_matte.py`. O modelo confundia a almofada branca do fundo com a pessoa entre 0,4 e
0,7 s, por isso o script zera a máscara antes de ela entrar (0,75 s) e mantém só o maior recorte.
