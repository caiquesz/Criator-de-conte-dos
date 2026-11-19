# Motion "Dia da Autoescola" (19/11) — Auto Escola Lara

Post animado de 12 s em dois formatos: **feed 4:5 (1080x1350)** e **Reels/Stories 9:16 (1080x1920)**.

- Layout igual à referência: ícone (mão segurando a CNH), título em Montserrat (2 linhas finas + 2 em negrito),
  três fileiras de bolinhas em escada, foto realista da mão no volante embaixo e tarja com o logo.
- Fundo na paleta da Lara (pêssego do logo). Cores tiradas do logo: azul `#30318A`, verde `#34774C`,
  pêssego `#EDAF8A`, laranja `#D2683A`. Com `?bg=areia` (ou `BG=areia` no render) o fundo vira areia clara.
- Texto 1: "Hoje, **19 de novembro**, é o **Dia da Autoescola!**" (data em verde, em destaque).
  Texto 2: "Obrigado a todos que dirigem seus **sonhos com a gente!**"
- `assets/volante_foto.png`: foto gerada por IA (Higgsfield, GPT Image) e recortada; não é a foto da referência.
- `assets/logo_lara.png`, `lara_verde.png`, `autoescola_azul.png`: logo recortado do arquivo enviado.
- Data: o Dia da Autoescola em 19/11 vem da Lei estadual 16.208/2016 (SP) e é comemorado pelo setor no país.
- `versao_ilustrada.html`: primeira versão (volante ilustrado + velocímetro marcando 19), guardada como alternativa.

## Render

```bash
./baixar_sfx.sh
python3 audio.py /tmp/sfx.wav
node render.js feed /tmp/feed 4        # ou: node render.js reels /tmp/reels 4
ffmpeg -framerate 30 -i /tmp/feed/%05d.png -i /tmp/sfx.wav -c:v libx264 -crf 15 -pix_fmt yuv420p \
  -c:a aac -b:a 256k -shortest -movflags +faststart dia_da_autoescola_feed_4x5.mp4
```
