#!/usr/bin/env bash
# Efeitos sonoros (Mixkit, licença livre; não redistribuídos no repositório).
# Os pops/cliques/whoosh/marcador vêm de ../../edicao_video (rode antes edicao_video/baixar_assets.sh).
set -euo pipefail
cd "$(dirname "$0")"; mkdir -p sfx _tmp
for id in 719 1566; do curl -sSL -o "_tmp/$id.mp3" "https://assets.mixkit.co/active_storage/sfx/$id/$id-preview.mp3"; done
ffmpeg -v error -y -i _tmp/719.mp3 -af "atrim=0.08:0.8,afade=t=out:st=0.55:d=0.15,aresample=48000" -ac 2 sfx/buzina.wav
ffmpeg -v error -y -i _tmp/1566.mp3 -af "atrim=0.15:1.6,afade=t=out:st=1.0:d=0.45,aresample=48000" -ac 2 sfx/partida.wav
cp ../../edicao_video/sfx/{pop,pop_soft,click,tick,swish,whoosh}.wav sfx/
cp ../../edicao_video/prova_detran/sfx/marcador.wav sfx/
rm -rf _tmp; echo "sfx ok"
