# Segredos de Minas — "kit lavabo" (edição do reels)

Vídeo bruto (Drive): 1080x1920, 39,7 s. A cliente fala no começo e no fim, e o meio é b-roll dos produtos.
O vídeo final (`segredos_de_minas_kit_lavabo_editado.mp4`, 36,2 s, H.264 1080x1920 30 fps, bt709) foi entregue na conversa. Ele não fica no git porque tem cerca de 60 MB.

Segue o mesmo pipeline de `../segredos-de-minas-natal`, com estas mudanças pedidas:

- **Todas as letras brancas.** Nenhuma cor de destaque; a hierarquia vem só do tamanho (Coolvetica).
- **Legenda dinâmica.** Cada frase ou bloco aparece num lugar diferente do quadro, em 12 zonas (topo, meio e base × esquerda, centro e direita) com alinhamento à esquerda, ao centro ou à direita. A entrada desliza levemente a partir do lado em que o texto está ancorado.
  - A zona de cada trecho foi escolhida por `scripts/zones.py`, que mede no vídeo já cortado a área clara e a luminância média de cada zona. O texto vai para onde o branco fica legível e, nas falas, longe do rosto.
  - Na toalha creme (12,8 a 14,9 s), o texto fica sobre a faixa laranja, que é a região mais escura.

## O que foi feito

| Item | Como |
|---|---|
| Cortes | 10 segmentos (`scripts/edl.py`). Saem 6 pausas/respirações longas e o vídeo vai de 39,7 s para 36,2 s. Os cortes de b-roll que já existiam no bruto foram mantidos. |
| Sincronia das palavras | Alinhamento forçado CTC (`scripts/align.py`, torchaudio MMS_FA) sobre a transcrição. Os timestamps do Whisper divergiam até 0,5 s. |
| Transições | Dissolve de 6 frames só onde o corte de pausa coincide com troca de take (5 lugares). Em 13,7 s, o corte do bruto caía no meio de um corte de pausa. Ali o vídeo entra 2 frames antes do áudio (`vlead`), para não piscar. |
| Zoom | Push-in lento em cada trecho, punch-in no jump cut de "olha esse kit" e no meio do b-roll, e zoom out lento no CTA. |
| Produto | "olha esse / kit de lavabo" abaixo do queixo. A palavra **tapete** fica na tela do momento em que é dita até o fim da medida. Logo embaixo, em fonte menor, a medida vai entrando conforme a fala: "0,65" e depois "x 0,40 m" (65 cm × 40 cm). |
| SFX | 6 efeitos: whoosh no início, pop em "kit de lavabo", em "0,65" e em "0,40 m", click em "link abaixo" e brilho em "o seu". Ficam 3 a 6 dB abaixo da voz. |
| Áudio | Voz original, sem EQ, compressão ou normalização. Fades de 5 ms nos cortes (30 ms no "s" longo de "peças"). Fora dos fades, as amostras são idênticas ao bruto. |
| Cor | Nenhuma correção. O processamento é feito direto em YUV bt709, e as médias Y/U/V da saída batem com o bruto (diferença de ~0,1). |

## Área segura para postar

 verifica todos os frames da camada de texto. Os limites são:
- margem de 60 px nas laterais;
- nada acima de y=290 (é a parte que o corte 4:5 do feed remove);
- nada abaixo de y=1440 (área do nome, da legenda e do áudio no Reels);
- texto à direita termina em x≤950 abaixo de y=1000 (coluna de curtir/comentar/compartilhar).

O resultado atual é 0 violações nos 1085 frames.

## Renderizar de novo

Mesmos passos do README de `../segredos-de-minas-natal`, mais:

```bash
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
python scripts/align.py $S              # work/transcript.json -> work/aligned.json
# mapear aligned.json para a timeline final (dados/words_out.json) e ajustar gen_overlay.py
python scripts/render.py $S work/base_preview.mp4 --preset ultrafast
ffmpeg -i work/base_preview.mp4 -vf "fps=10,scale=108:192" work/lum/f_%04d.png
python scripts/zones.py $S 12.8 13.9    # nota de legibilidade de cada zona numa janela
```
