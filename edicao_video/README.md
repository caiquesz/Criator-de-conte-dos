# Edição de vídeo: "Quando a CNH pode ser recolhida" (Alexandre)

Pipeline que gerou o Reels final (1080x1920, 30 fps, ~35 s, -14 LUFS):

- **Título de abertura**: a 1ª frase ("quando que ela pode ser recolhida?") vira o título
  "quando a sua **CNH** / **PODE SER RECOLHIDA?**" no centro, com o vídeo escurecido atrás; em 1,4 s ele
  encolhe e voa para o topo, virando um cabeçalho fixo (tarja preta) até o motion entrar.
- **Legenda constante** no estilo da referência (@adorozaya): Poppins Medium, minúscula, palavras entrando
  uma a uma com blur e subida, sincronizadas com a fala (Whisper large-v3, timestamps por palavra).
- **Palavras de destaque** em **Oblisk**, caixa alta, entrando com "pop" (escala com overshoot e blur).
- **Motion** no trecho em que o Alexandre sai do quadro (~8,3 s a ~18,6 s): fundo texturizado enviado,
  transição *push* com motion blur, texto explicativo sincronizado com a fala, card de CNH animado,
  carimbo "VENCIDA", contador 1→10 anos e barra "dia 1 → dia 30".
- **SFX**: pop e clique (pedido), whoosh nas transições e swish suave na saída dos textos.
- Corte de ~0,93 s de silêncio morto entre "10 anos" e "e venceu" (fica escondido debaixo do motion).
- Zoom alternado 1.0x / 1.12x entre frases e push-in final no "REMOVIDO".
- Voz: passa-alta, redução de ruído leve, EQ de presença, compressor e loudnorm em -14 LUFS.

## Como re-renderizar

Requisitos: `ffmpeg`, Python 3 com `numpy`, `opencv-python-headless` e `faster-whisper`, Node com `playwright`.

```bash
cd edicao_video
./baixar_assets.sh                                   # Oblisk + SFX (não versionados por licença)
python3 transcrever.py audio16k.wav large-v3 dados/transcricao.json   # opcional, já está salva
python3 timeline.py dados/transcricao.json timeline.json
node render_overlay.js /tmp/ov 4                     # legendas + motion em PNG com alpha
python3 audio.py bruto.mov sfx /tmp/audio_final.wav
python3 composite.py bruto.mov /tmp/ov /tmp/audio_final.wav final.mp4
```

`audio16k.wav` sai de `ffmpeg -i bruto.mov -ac 1 -ar 16000 audio16k.wav`. O bruto está no Drive (não versionado).

### Onde ajustar
- Texto, quebras e destaques da legenda: lista `PH` em `timeline.py`.
- Tempos/volumes dos SFX: bloco `# ---- SFX ----` em `timeline.py`.
- Visual do motion (cenas 1–4) e da legenda: `overlay.html` (`buildScenes`, CSS `.phrase`).
- Prévia de quadros soltos: `node render_overlay.js /tmp/ov 2 36,360,456` e
  `python3 composite.py bruto.mov /tmp/ov --preview /tmp/prev 36,360,456`.

## Licenças
- **Oblisk** (Maikohatta): grátis **apenas para uso pessoal**. Para post de cliente/comercial, compre a
  licença (MyFonts / Creative Market). Por isso a fonte não está no repositório.
- **Poppins**: SIL Open Font License (incluída em `assets/`).
- **SFX**: Mixkit Free License (uso em vídeo liberado; arquivos não redistribuídos aqui).
