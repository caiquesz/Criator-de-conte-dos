# Reels da imobiliária

Antes de editar um vídeo, leia `README.md` (guia de estilo e fluxo) e carregue a skill
`/hyperframes`. O vídeo chega cortado: só se adicionam legendas, destaques, cards, transições
e sons, nunca logo. A composição sai de `plano.json` via `scripts/gerar.py`; ajuste o plano
ou o gerador, não o HTML gerado. Depois de gerar: `npx hyperframes check`, olhar os
`snapshot`, renderizar.

## Como os vídeos chegam

Pela página "Envio de Reels" (https://claude.ai/artifact/5q94sQub5Nb3pA9opnRcfR, fonte em
`envio/envio-reels.html`). Cada envio é um documento da coleção `envios` (ler com ArtifactData)
com o briefing e a lista `partes`: ids de arquivos de até 19 MiB que, baixados na ordem
(`Artifact` action `read` com `path` = id, um por chamada: `paths` não acha ids de arquivo) e concatenados com `cat`, refazem o vídeo original.
Atualize `status` (`editando`, `pronto`) e `nota` do documento para o cliente acompanhar.

Espaçamento confirmado pelo cliente: A, letras juntas como nas referências (padrão do gerador).

## Regras do cliente

- **Nunca alterar a voz.** Nada de normalizar, comprimir, limitar, tirar ruído ou mudar o tom do
  áudio que vem no vídeo. O áudio final sai de `scripts/mixar.py`: o original com ganho 1,0 mais os
  efeitos; a imagem do render é só copiada.
- **Legenda só quando a pessoa fala.** Depois de montar o plano, rode `scripts/sincronizar.py`
  (o Whisper adianta a primeira palavra depois de pausas).
- **Sombra nas letras, nunca em bloco** atrás do texto (`sombra_forte` para fundos claros).
- **Estabilizar** o vídeo por cena com `scripts/estabilizar.py` antes do recorte e do render.

