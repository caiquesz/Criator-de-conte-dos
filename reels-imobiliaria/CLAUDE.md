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
(`Artifact` action `read` com `path` = id) e concatenados com `cat`, refazem o vídeo original.
Atualize `status` (`editando`, `pronto`) e `nota` do documento para o cliente acompanhar.

Espaçamento confirmado pelo cliente: A, letras juntas como nas referências (padrão do gerador).
