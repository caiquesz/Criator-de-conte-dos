#!/usr/bin/env bash
# Normaliza o áudio do render para Reels (-14 LUFS, pico -1.5 dBTP) sem reencodar o vídeo.
#   tools/finish.sh renders/render.mp4 renders/final.mp4
set -euo pipefail
in="$1"
out="$2"

stats=$(ffmpeg -hide_banner -nostats -i "$in" -vn -af loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p')
get() { echo "$stats" | python3 -c "import sys,json; print(json.load(sys.stdin)['$1'])"; }

ffmpeg -v error -y -i "$in" -c:v copy \
  -af "loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=$(get input_i):measured_TP=$(get input_tp):measured_LRA=$(get input_lra):measured_thresh=$(get input_thresh):offset=$(get target_offset):linear=true" \
  -c:a aac -b:a 256k -ar 48000 -movflags +faststart "$out"

echo "$out: $(ffmpeg -hide_banner -nostats -i "$out" -vn -af ebur128=peak=true -f null - 2>&1 | grep -E '^\s+(I|Peak):' | tr -s ' ' | tr '\n' ' ')"
