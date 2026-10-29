#!/usr/bin/env bash
# Prepara o vídeo já cortado para a edição:
#   tools/prepare.sh <video.mp4> [fim-do-gancho-em-segundos]
# 1. padroniza em 1080x1920 / 30 fps com keyframe a cada 1 s (o render busca quadro a quadro)
# 2. lista os cortes do vídeo em assets/cuts.txt (candidatos às transições)
# 3. transcreve em português com tempo por palavra → assets/transcript.json
# 4. se o fim do gancho for informado, recorta a pessoa nesse trecho (texto atrás dela)
set -euo pipefail
src="$1"
hook="${2:-}"
PY="${PYTHON:-python3}"
cd "$(dirname "$0")/.."
mkdir -p assets/video assets/cutout

ffmpeg -v error -y -i "$src" \
  -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30" \
  -c:v libx264 -preset medium -crf 16 -g 30 -keyint_min 30 -pix_fmt yuv420p \
  -c:a aac -b:a 256k -ar 48000 assets/video/main.mp4
echo "vídeo: assets/video/main.mp4 ($(ffprobe -v error -show_entries format=duration -of csv=p=0 assets/video/main.mp4)s)"

ffmpeg -hide_banner -i assets/video/main.mp4 -an -vf "scale=270:-2,select='gt(scene,0.25)',showinfo" -f null - 2>&1 \
  | grep -o "pts_time:[0-9.]*" | sed 's/pts_time://' > assets/cuts.txt
echo "cortes: $(tr '\n' ' ' < assets/cuts.txt)"

"$PY" tools/transcribe.py assets/video/main.mp4 assets/transcript.json

if [ -n "$hook" ]; then
  tmp="$(mktemp -d)"
  ffmpeg -v error -y -i assets/video/main.mp4 -t "$hook" -an -c:v libx264 -crf 12 -g 30 -pix_fmt yuv420p "$tmp/hook.mp4"
  npx --yes hyperframes@0.8.214 remove-background "$tmp/hook.mp4" -o assets/cutout/hook.webm --quality best
  rm -rf "$tmp"
fi
