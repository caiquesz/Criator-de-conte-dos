#!/usr/bin/env bash
# Trata a voz sem mudar quem fala: só equalização, compressão leve e volume (nada de IA que recrie a voz).
#   tools/voz.sh entrada.mp4 saida.wav [eq]
# Sem "eq": só nivela a voz em -16 LUFS (base para os efeitos sonoros ficarem na proporção das referências).
# Com "eq": corrige celular estridente / voz fina, chegando perto do timbre das referências.
#   Medido no vídeo da Black Friday contra as vozes das 3 referências (1/3 de oitava, só trechos com voz):
#   +5 a +13 dB sobrando em 1,6–5 kHz, -5 a -9 dB faltando em 150–500 Hz, ronco abaixo de 100 Hz.
#   A correção é parcial (cerca de metade da diferença), para manter o timbre dela.
set -euo pipefail
in="$1"
out="$2"
mode="${3:-}"

chain="highpass=f=105:poles=2"
if [ "$mode" = "eq" ]; then
  chain="$chain,equalizer=f=300:t=q:w=0.9:g=3,equalizer=f=520:t=q:w=1.4:g=2"
  chain="$chain,equalizer=f=2400:t=q:w=0.9:g=-4.5,equalizer=f=4300:t=q:w=1.1:g=-4,treble=g=-2:f=9500:t=s:w=0.7"
  chain="$chain,acompressor=threshold=-24dB:ratio=2.2:attack=12:release=140:knee=6"
fi

tmp="$(mktemp -d)"
ffmpeg -v error -y -i "$in" -vn -ac 2 -ar 48000 -af "$chain" -c:a pcm_f32le "$tmp/eq.wav"
stats=$(ffmpeg -hide_banner -nostats -i "$tmp/eq.wav" -af loudnorm=I=-16:TP=-3:LRA=11:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p')
get() { echo "$stats" | python3 -c "import sys,json; print(json.load(sys.stdin)['$1'])"; }
ffmpeg -v error -y -i "$tmp/eq.wav" \
  -af "loudnorm=I=-16:TP=-3:LRA=11:measured_I=$(get input_i):measured_TP=$(get input_tp):measured_LRA=$(get input_lra):measured_thresh=$(get input_thresh):offset=$(get target_offset):linear=true,aresample=48000,alimiter=limit=0.6:attack=3:release=50:level=disabled" \
  -ar 48000 -c:a pcm_s16le "$out"
rm -rf "$tmp"
echo "$out: $(ffmpeg -hide_banner -nostats -i "$out" -af ebur128=peak=true -f null - 2>&1 | grep -E '^\s+(I|Peak):' | tr -s ' ' | tr '\n' ' ')"
