#!/usr/bin/env bash
# Cria um projeto de Reels a partir do template.
# Uso: scripts/novo_projeto.sh NOME caminho/do/video.mp4
set -euo pipefail

RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
NOME="$1"
VIDEO="$2"
DEST="$RAIZ/projetos/$NOME"

mkdir -p "$DEST/assets/video"
cp -r "$RAIZ/template/." "$DEST/"
"$RAIZ/scripts/preparar_sfx.sh" "$DEST/assets/sfx"

# o envio original fica guardado: o áudio final sai dele, sem nenhuma alteração
cp "$VIDEO" "$DEST/assets/video/original.mp4"
# H.264 com um quadro-chave por segundo (o HyperFrames busca quadro a quadro); áudio copiado
ffmpeg -v error -y -i "$VIDEO" -c:v libx264 -crf 14 -preset slow -g 30 -pix_fmt yuv420p \
  -c:a copy "$DEST/assets/video/video.mp4"

echo "projeto criado em $DEST"
echo "próximo passo: python3 scripts/analisar.py $DEST"
