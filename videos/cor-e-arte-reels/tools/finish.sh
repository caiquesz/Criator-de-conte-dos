#!/usr/bin/env bash
# Normaliza o áudio do render para Reels (-14 LUFS) e limita os picos (cliques) com folga para o AAC,
# sem reencodar o vídeo. Confere o pico depois de codificar: o AAC pode exagerar um clique bem rápido
# (na Black Friday, uma única amostra a +1,2 dBFS em 256 kbps), então refaz com mais folga se passar de -1 dBFS.
#   tools/finish.sh renders/render.mp4 renders/final.mp4
set -euo pipefail
in="$1"
out="$2"

stats=$(ffmpeg -hide_banner -nostats -i "$in" -vn -af loudnorm=I=-14:TP=-2.5:LRA=11:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p')
get() { echo "$stats" | python3 -c "import sys,json; print(json.load(sys.stdin)['$1'])"; }
norm="loudnorm=I=-14:TP=-2.5:LRA=11:measured_I=$(get input_i):measured_TP=$(get input_tp):measured_LRA=$(get input_lra):measured_thresh=$(get input_thresh):offset=$(get target_offset):linear=true,aresample=48000"
peak() { ffmpeg -hide_banner -nostats -i "$1" -vn -af astats=measure_perchannel=none -f null - 2>&1 | grep -oE "Peak level dB: [-0-9.]+" | awk '{print $4}'; }

for limit in 0.7 0.6 0.5; do
  ffmpeg -v error -y -i "$in" -c:v copy -af "$norm,alimiter=limit=$limit:attack=2:release=60:level=disabled" \
    -c:a aac -b:a 320k -ar 48000 -movflags +faststart "$out"
  p=$(peak "$out")
  if python3 -c "import sys; sys.exit(0 if float('$p') <= -1.0 else 1)"; then break; fi
  echo "pico $p dBFS com limite $limit; refazendo com mais folga"
done

echo "$out: $(ffmpeg -hide_banner -nostats -i "$out" -vn -af ebur128=peak=true -f null - 2>&1 | grep -E '^\s+(I|Peak):' | tr -s ' ' | tr '\n' ' ')"
