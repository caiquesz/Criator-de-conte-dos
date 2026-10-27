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

**Entrega:** o vídeo final vai para o cliente pela mesma página. Corte o .mp4 em partes de até
19 MiB (nenhuma começando com `<`), suba com `Artifact` publish `asset: true` + `file_paths` e
grave no documento `entrega: {arquivo, tamanho, sha256, descricao, partes: [ids]}`; a página
mostra o botão "Baixar vídeo editado", junta as partes e salva um único .mp4. Pelo chat, arquivos
grandes (>100 MB) não baixam no app: mande também uma versão leve (~50 MB).

**Armazenamento da página:** 1 GB para tudo. Quando o cliente avisar que acabou, apague as partes
brutas (`partes`) dos vídeos já entregues, depois de conferir que o original está em
`assets/video/original.*` do projeto, e grave `partes: []` no documento. Ao reentregar uma versão,
suba a nova, confira o sha256 das partes baixadas e só então apague as partes da anterior.

Espaçamento confirmado pelo cliente: A, letras juntas como nas referências (padrão do gerador).

## Regras do cliente

- **Nunca alterar a voz.** Nada de normalizar, comprimir, limitar, tirar ruído ou mudar o tom do
  áudio que vem no vídeo. O áudio final sai de `scripts/mixar.py`: o original com ganho 1,0 mais os
  efeitos; a imagem do render é só copiada.
- **Legenda só quando a pessoa fala.** Depois de montar o plano, rode `scripts/sincronizar.py`
  (o Whisper adianta a primeira palavra depois de pausas).
- **Sombra nas letras, nunca em bloco** atrás do texto (`sombra_forte` para fundos claros).
  Palavra na cor de destaque nunca leva sombra preta, só o tom escuro da própria cor.
- **Estabilizar** o vídeo por cena com `scripts/estabilizar.py` antes do render (vid.stab,
  correção moderada). Na Casa no Centro testamos uma estabilização bem mais forte (suavização de
  1 s e até 20% de zoom a partir do 4K) e o cliente achou pior: pareceu balançar mais. Fique com a
  moderada. O script confere que o resultado tem os mesmos quadros do original; confira também com
  `scripts/conferir_sincronia.py` (tudo em +0 quadros), porque imagem fora da voz não volta.
  Depois de estabilizar de novo, refaça os rastreios.
- **Cores:** quando o cliente pedir (ex.: casa rosa), destaques só em branco:
  `"cores": {"destaque": "#FFFFFF", "destaque_escuro": "#FFFFFF", "brilho": false}`.
  O cliente acha o tom escuro do destaque (bege/terracota) escuro demais: deixe a maioria dos
  destaques em branco e use a cor só às vezes, num tom claro e sobre fundo mais escuro.
- **Música:** leve e animada, mas adulta: nada de ukulele, glockenspiel ou assobio ("Carefree"
  ficou infantil). Na dúvida, mande 2 ou 3 amostras de 20 s já por baixo da voz para o cliente
  escolher; trocar a música só refaz a mixagem. Licença sem NC (CC BY ou CC0) e crédito no post.
- **Texto em perspectiva** (`perspectivas` no plano, `scripts/rastrear.py`): só na tomada em que o
  André aparece; na troca para outra tomada ele sai antes do corte.

## Espaço em disco

Cada render enche `/tmp/hyperframes-extract-cache-0` (dá 5–17 GB). Depois de renderizar e mixar,
apague esse cache e os renders que já foram substituídos; o disco da sessão é limitado.

