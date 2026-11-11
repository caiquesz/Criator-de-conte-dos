#!/usr/bin/env bash
# Baixa os assets que NÃO ficam no repositório por causa da licença:
#  - fonte Oblisk (Maikohatta) — grátis só para uso pessoal; uso comercial exige licença
#  - efeitos sonoros Mixkit (licença livre, mas não pode redistribuir os arquivos soltos)
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p assets sfx _tmp

# fonte Oblisk (1001fonts)
curl -sSL -o _tmp/oblisk.zip https://www.1001fonts.com/download/oblisk.zip
unzip -o -q _tmp/oblisk.zip -d _tmp/oblisk
cp _tmp/oblisk/OBLISK.otf assets/OBLISK.otf

# SFX Mixkit: pops, cliques e whoosh
mk() { curl -sSL -o "_tmp/$1.mp3" "https://assets.mixkit.co/active_storage/sfx/$1/$1-preview.mp3"; }
for id in 3005 2925 1119 2858 1492 1489; do mk $id; done
ff() { ffmpeg -v error -y "$@"; }
ff -i _tmp/3005.mp3 -af "atrim=0:0.18,afade=t=out:st=0.14:d=0.04,aresample=48000" -ac 2 sfx/pop.wav
ff -i _tmp/2925.mp3 -af "atrim=0:0.15,afade=t=out:st=0.11:d=0.04,aresample=48000" -ac 2 sfx/pop_soft.wav
ff -i _tmp/1119.mp3 -af "atrim=0.125:0.33,afade=t=in:d=0.003,afade=t=out:st=0.16:d=0.04,aresample=48000" -ac 2 sfx/click.wav
ff -i _tmp/2858.mp3 -af "atrim=0.025:0.16,afade=t=in:d=0.003,afade=t=out:st=0.1:d=0.035,aresample=48000" -ac 2 sfx/tick.wav
ff -i _tmp/1492.mp3 -af "aresample=48000" -ac 2 sfx/whoosh.wav
ff -i _tmp/1489.mp3 -af "atrim=0.3:1.3,afade=t=in:d=0.1,afade=t=out:st=0.7:d=0.3,aresample=48000" -ac 2 sfx/swish.wav
rm -rf _tmp
echo "assets ok"
