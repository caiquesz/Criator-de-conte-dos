#!/usr/bin/env bash
# Prepara um vídeo já cortado para a edição:
#   tools/prepare.sh <video> <nome> [fim-do-gancho-em-segundos] [eq]
# 1. padroniza em 1080x1920 / 30 fps com keyframe a cada 1 s (o render busca quadro a quadro)
# 2. trata a voz (tools/voz.sh): nivela em -16 LUFS; com "eq", corrige voz estridente/fina sem mudar o timbre
# 3. lista os cortes do vídeo em assets/cuts/<nome>.txt (candidatos às transições)
# 4. transcreve em português com tempo por palavra → assets/transcripts/<nome>.json
# 5. se o fim do gancho for informado (e não for 0), recorta a pessoa nesse trecho → assets/cutout/<nome>.webm
set -euo pipefail
src="$1"
name="$2"
hook="${3:-0}"
eq="${4:-}"
PY="${PYTHON:-python3}"
cd "$(dirname "$0")/.."
mkdir -p assets/video assets/cutout assets/cuts assets/transcripts
tmp="$(mktemp -d)"

tools/voz.sh "$src" "$tmp/voz.wav" "$eq"
ffmpeg -v error -y -i "$src" -i "$tmp/voz.wav" -map 0:v:0 -map 1:a:0 \
  -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30" \
  -c:v libx264 -preset medium -crf 16 -g 30 -keyint_min 30 -pix_fmt yuv420p \
  -c:a aac -b:a 256k -ar 48000 -shortest "assets/video/$name.mp4"
echo "vídeo: assets/video/$name.mp4 ($(ffprobe -v error -show_entries format=duration -of csv=p=0 "assets/video/$name.mp4")s)"

ffmpeg -hide_banner -i "assets/video/$name.mp4" -an -vf "scale=270:-2,select='gt(scene,0.25)',showinfo" -f null - 2>&1 \
  | grep -o "pts_time:[0-9.]*" | sed 's/pts_time://' > "assets/cuts/$name.txt"
echo "cortes: $(tr '\n' ' ' < "assets/cuts/$name.txt")"

"$PY" tools/transcribe.py "assets/video/$name.mp4" "assets/transcripts/$name.json"

if [ "$hook" != "0" ]; then
  ffmpeg -v error -y -i "assets/video/$name.mp4" -t "$hook" -an -c:v libx264 -crf 12 -g 30 -pix_fmt yuv420p "$tmp/hook.mp4"
  npx --yes hyperframes@0.8.214 remove-background "$tmp/hook.mp4" -o "assets/cutout/$name.webm" --quality best
fi
rm -rf "$tmp"
