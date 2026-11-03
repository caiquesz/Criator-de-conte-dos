#!/usr/bin/env bash
# Recorte da pessoa em resolução cheia, para a legenda passar por trás dela.
#
# O modelo de recorte usa 320×320 por dentro, então ele roda numa cópia
# 540×960 (muito mais rápido) e só a máscara é ampliada; a cor vem do
# vídeo original, que é o mesmo que está por baixo na composição.
#
# Uso: scripts/recorte.sh PASTA_DO_PROJETO
# Gera assets/video/mascara540.webm (máscara) e assets/video/recorte.webm (pessoa com alfa).
set -euo pipefail

P="$(cd "$1" && pwd)"
V="$P/assets/video"
HF="${HF:-npx hyperframes}"

if [ ! -f "$V/mascara540.webm" ]; then
  ffmpeg -v error -y -i "$V/video.mp4" -an -vf "scale=540:960:flags=bicubic" \
    -c:v libx264 -crf 18 -preset veryfast -g 30 "$V/proxy540.mp4"
  $HF remove-background "$V/proxy540.mp4" -o "$V/mascara540.webm" --device cpu --quality fast
  rm -f "$V/proxy540.mp4"
fi

# máscara ampliada, 1 px mais justa e com borda suave; cor do vídeo original
ffmpeg -v error -y -i "$V/video.mp4" -c:v libvpx-vp9 -i "$V/mascara540.webm" -filter_complex \
  "[1:v]alphaextract,scale=1080:1920:flags=bicubic,erosion,gblur=sigma=1.2[m];[0:v][m]alphamerge,format=yuva420p[o]" \
  -map "[o]" -an -c:v libvpx-vp9 -pix_fmt yuva420p -b:v 0 -crf 22 -deadline realtime -cpu-used 8 \
  -row-mt 1 -auto-alt-ref 0 -g 30 "$V/recorte.webm"
echo "recorte pronto: $V/recorte.webm"
