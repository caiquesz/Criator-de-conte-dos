# Reels da imobiliária

Antes de editar um vídeo, leia `README.md` (guia de estilo e fluxo) e carregue a skill
`/hyperframes`. O vídeo chega cortado: só se adicionam legendas, destaques, cards, transições
e sons, nunca logo. A composição sai de `plano.json` via `scripts/gerar.py`; ajuste o plano
ou o gerador, não o HTML gerado. Depois de gerar: `npx hyperframes check`, olhar os
`snapshot`, renderizar.
