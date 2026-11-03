#!/usr/bin/env bash
# Copia os efeitos sonoros da biblioteca do HyperFrames (Pixabay, uso comercial
# livre) e gera as variações usadas no template. Os arquivos não vão para o git.
# Uso: scripts/preparar_sfx.sh PASTA_DESTINO
set -euo pipefail

DEST="${1:?pasta de destino}"
ORIGEM="${HF_SFX:-$HOME/.claude/skills/media-use/audio/assets/sfx}"
[ -d "$ORIGEM" ] || { echo "rode 'npx hyperframes skills' antes (biblioteca de sons não encontrada)"; exit 1; }
mkdir -p "$DEST"

cp "$ORIGEM/click.mp3" "$ORIGEM/pop.mp3" "$ORIGEM/whoosh.mp3" "$DEST/"
cp "$ORIGEM/key-press.mp3" "$DEST/click-tecla.mp3"
cp "$ORIGEM/CREDITS.md" "$DEST/CREDITS-pixabay.md"
ffmpeg -v error -y -i "$ORIGEM/whoosh.mp3" -af "asetrate=44100*0.82,aresample=44100" "$DEST/whoosh-grave.mp3"
ffmpeg -v error -y -i "$ORIGEM/whoosh.mp3" -af "asetrate=44100*1.15,aresample=44100" "$DEST/whoosh-rapido.mp3"
ffmpeg -v error -y -ss 1.7 -t 1.9 -i "$ORIGEM/whoosh-cinematic.mp3" \
  -af "afade=t=in:d=0.15,afade=t=out:st=1.3:d=0.6,volume=-2dB" "$DEST/whoosh-transicao.mp3"
ffmpeg -v error -y -i "$ORIGEM/click.mp3" -af "asetrate=44100*1.18,aresample=44100" "$DEST/click-agudo.mp3"
echo "sons prontos em $DEST"
