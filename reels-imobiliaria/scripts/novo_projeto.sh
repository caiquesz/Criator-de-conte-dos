#!/usr/bin/env bash
# Cria um projeto de Reels a partir do template.
# Uso: scripts/novo_projeto.sh NOME caminho/do/video.mp4 [PASTA_DOS_PROJETOS]
#      (sem a pasta, o projeto vai para reels-imobiliaria/projetos; a biomédica usa reels-biomedica/projetos)
set -euo pipefail

RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
NOME="$1"
VIDEO="$2"
DEST="${3:-$RAIZ/projetos}/$NOME"

mkdir -p "$DEST/assets/video"
cp -r "$RAIZ/template/." "$DEST/"
"$RAIZ/scripts/preparar_sfx.sh" "$DEST/assets/sfx"

# o envio original fica guardado: o áudio final sai dele, sem nenhuma alteração
cp "$VIDEO" "$DEST/assets/video/original.${VIDEO##*.}"
# H.264 com um quadro-chave por segundo (o HyperFrames busca quadro a quadro); áudio copiado
# (vídeos 4K do celular descem para 1080×1920, a resolução do Reels e da composição; e para 30 quadros
# por segundo, os da composição: o celular às vezes grava em 31,58 ou 60, e os cortes contam quadros)
# cor: o iPhone às vezes grava em Display P3 (smpte432); sem converter, o vídeo sai lavado no celular (Caso de
# paciente, 17/11). A faixa (limitada/cheia) segue a etiqueta do arquivo; a saída é sempre BT.709.
PRIM=$(ffprobe -v error -select_streams v:0 -show_entries stream=color_primaries -of csv=p=0 "$VIDEO")
FAIXA=$(ffprobe -v error -select_streams v:0 -show_entries stream=color_range -of csv=p=0 "$VIDEO")
COR=""
if [ "$PRIM" = "smpte432" ] || [ "$PRIM" = "bt2020" ]; then
  R=$([ "$FAIXA" = "pc" ] && echo full || echo limited)
  ZP=$([ "$PRIM" = "bt2020" ] && echo 2020 || echo smpte432)
  COR="zscale=primariesin=$ZP:primaries=709:transferin=709:transfer=709:matrixin=709:matrix=709:rangein=$R:range=limited,"
  echo "cor: $PRIM convertido para BT.709"
fi
ffmpeg -v error -y -i "$VIDEO" -vf "${COR}scale=1080:1920:flags=lanczos,setsar=1,fps=30" -c:v libx264 -crf 14 \
  -preset slow -g 30 -pix_fmt yuv420p -color_primaries bt709 -color_trc bt709 -colorspace bt709 -color_range tv \
  -c:a copy "$DEST/assets/video/video.mp4"

echo "projeto criado em $DEST"
echo "próximo passo: python3 scripts/analisar.py $DEST"
