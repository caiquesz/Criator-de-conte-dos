# Reels da biomédica

Antes de editar, leia `README.md` (o que as referências mostram, os formatos de foto, o fluxo) e
`../reels-imobiliaria/CLAUDE.md` (regras do mesmo cliente, que valem aqui também) e carregue a
skill `/hyperframes`. Os scripts ficam em `../reels-imobiliaria/scripts/`; a composição sai do
`plano.json` via `gerar.py`: ajuste o plano ou o gerador, não o HTML gerado.

## Como os vídeos chegam

Pela página "Envio da Biomédica" (https://claude.ai/artifact/Dm5w3uprQVKwq9PZGXGTBk, slug
`67556ddf-776c-4945-bc27-0dda6e5e0baf`, fonte em `envio/envio-biomedica.html`, armazenamento
próprio). Cada envio é um documento da coleção `envios` (ler com `db_get`/`db_list`):

- `arquivos: [{nome, tamanho, duracao, largura, altura, partes: [ids]}]`: o vídeo, em um ou mais
  arquivos na ordem escolhida. Baixe as partes de cada arquivo na ordem com `read_asset`
  (`max_bytes: 4194304`; o arquivo fica salvo em `tool-results/` e o resultado traz o sha256 para
  conferir) e junte com `cat`. Um arquivo a mais pode ser material para o vídeo, não uma
  continuação: leia as `observacoes` antes de emendar (a gravação de tela da Virgínia era para a
  tela dividida).
- **Pedaços de 4 MiB:** o `read_asset` só baixa até 4 MiB. A página guarda tudo em pedaços de até
  4 MiB; envios antigos, de pedaços de 19 MiB, ela mesma refaz quando o cliente abre a página
  (`pequenas: true` no documento quando termina; os ids antigos ficam em `partesGrandes`, para
  apagar com `delete_asset` depois de baixar e conferir).
- `fotos: [{nome, tamanho, tipo, largura, altura, categoria, grupo, quando, layout, partes}]`:
  `categoria` é `antes`, `depois`, `famosa` ou `outra`; `grupo` junta o antes e o depois da mesma
  pessoa (ou dá o nome da famosa); `quando` diz em que fala a foto entra; `layout` é `auto`
  (eu escolho), `cards`, `dividida`, `atras` ou `cheia`. Quase sempre `partes` tem um id só (a
  foto inteira); `emPedacos: true` significa juntar com `cat`; `convertida: true`, que a página
  já mandou em JPEG. Salve em `projetos/NOME/fotos-originais/`.
- `briefing: {tema, destaques, observacoes, musica}`, `status`, `nota` e `entrega` como nas
  páginas da imobiliária (mesmo formato de entrega, partes de até 19 MiB).

**Entrega com as ferramentas novas:** corte o .mp4 em partes de até 19 MiB (nenhuma começando com
`<`) e suba com `upload_asset`, no máximo 3 partes por chamada (o limite é uns 60 MB por envio); o
resultado traz o sha256 de cada parte, confira contra o local. Grave `entrega` com `db_write`
(`ifVersion` da última leitura). Pelo chat vai a versão leve (~45 MB, 5,5 Mbit/s).

**Limpeza do armazenamento:** depois de baixar e conferir, apague com `delete_asset` os ids de
`partesGrandes` e grave `partesGrandes: []`. Se a página foi fechada no meio da preparação, ficam
pedaços soltos de uma primeira tentativa, que nenhum documento cita: compare `list_assets` com os
ids de **todos** os documentos (`db_list` da coleção inteira) antes de apagar, nunca pela hora em que
foram criados. Em 12/11 isso apagou os pedaços de um segundo envio (a mesma gravação de tela, mandada
de novo) que eu tomei por sobra; o conteúdo já estava baixado, mas a regra é conferir antes.

## Regras

- **Ela trabalha com glúteo**, não com rosto: harmonização corporal (glúteo, gordura localizada,
  celulite, flacidez de coxa). As fotos de antes e depois e das famosas são de corpo; enquadre pelo
  corpo (`"foco_fotos": "corpo"`, o padrão) e confira no snapshot que o glúteo aparece, nunca só o
  rosto.
- **Voz intacta**, legenda só quando ela fala, sombra nas letras: como no CLAUDE.md da imobiliária.
- **Legenda na frente dela** (`"legendas_na_frente": true`): nas referências o texto nunca passa
  atrás da pessoa.
- **Cada foto só enquanto ela fala daquilo**, como os cards de preço da imobiliária: entra na
  palavra que a chama e sai antes do assunto seguinte.
- **Antes e depois lado a lado, na mesma escala:** o antes à esquerda; o corpo do mesmo tamanho e
  na mesma altura nas duas fotos (o gerador alinha pela silhueta; confira e acerte `foco`/`zoom`). Sem `layout` pedido: par de antes e
  depois em `cards` na primeira vez e `dividida` quando ela comenta os detalhes; várias famosas em
  `dividida` (carrossel); uma famosa ou um resultado em `atras`; um resultado para impressionar em
  `cheia`, curto (2 a 4 s).
- **Siga as referências à risca.** Nada de cards, listas, selos ou etiquetas animadas (na v2 da
  Virgínia eu enchi o vídeo de motion e a cliente recusou: "não quero esses cards"). O que entra é
  o que as referências têm: legenda, tela dividida, foto no fundo ou em tela cheia, troca de plano,
  luz e flash nas transições, e som em cada evento.
- **Abertura do quadro:** a única animação. Os vídeos de famosas são um quadro ("Caso <famosa>"),
  e cada um abre com uma tela cheia, como a vinheta de um quadro, logo depois do gancho (na
  Virgínia, depois de "mas eu vou te contar agora"). Para não cobrir a fala, o vídeo ganha uma
  pausa de 2,4 s ali (`"pausas"` no plano, aberta pelo `reenquadrar.py`; a voz não muda, a mixagem
  lê de `assets/video/voz.wav`). **Delicada e feminina**, na estética da referência 1: o vídeo da
  famosa ao fundo em tom quente (ela gostou da famosa atrás), véu nude no alto, luz pêssego,
  brilhos pequenos, Poppins fina ("CASO" espaçado, o nome, a frase do gancho) entrando em fade com
  desfoque, som `brilho`, luz com whoosh leve na entrada e na saída. A primeira (preto e branco,
  letra pesada, tremor, som de impacto) ela achou pesada. Modelo:
  `projetos/gluteo-virginia/abertura.py`, montado com `"extras"`.
- **Quadro "Bate-bola com Dra. Nádia"** (perguntas rápidas, pergunta fora da câmera e ela
  responde): ela mesma diz o título no começo, então a abertura delicada fica por cima do vídeo dela
  (desfocado atrás do véu nude) nesses 3 s, sem pausa, e sai numa luz. Cada pergunta abre num flash
  branco e no plano aberto ou médio; cada resposta corta para o fechado, com outro corte no meio das
  longas; a palavra-chave da pergunta e os prazos em `legenda-forte`. Modelo:
  `projetos/bate-bola/montar_plano.py` e `abertura.py`. O vídeo veio com música (opção "já tem
  música"): o áudio fica como está, só entram os efeitos.
- **Celular em 31,58 quadros/s:** o Bate-bola chegou em 600/19 fps. O `novo_projeto.sh` e o
  `reenquadrar.py` passam tudo para 30 (os da composição) antes de contar quadros.
- **Legendas:** como nas referências, pequenas (Poppins 700, 46 px; `legenda-forte` 800, 64 px
  para a palavra que pesa), letras juntas (`tracking.legenda` -0.04), numa linha, na altura do
  peito dela (meio do bloco em y 1040, no top), a mesma em todo o vídeo, inclusive na tela
  dividida e na foto em tela cheia (na v1 a da foto ficou baixa demais). A frase entra inteira e
  troca seca (`"legendas_modo": "corte"`): uma nunca aparece com a anterior ainda na tela (na v1,
  "ter feito" ainda saía quando "harmonização glútea" entrou). **Nada de letra cursiva.**
- **Tela dividida meio a meio e esfumada** (`corte` 960, `"esfumado": true`, `"dissolve": 0.32`, a divisão bem esfumada na parte da famosa, como ela pediu no envio da Virgínia, referência 1):
  a famosa em cima, com o glúteo no meio da metade dela (`foco` no glúteo e `zoom` ~1.25), a
  biomédica embaixo; só enquanto ela fala do vídeo da famosa.
- **Dinâmica:** planos alternando a cada 2 a 5 s (`enquadramentos` 1.22/1.5 do 4K), `zoom_lento`
  0.035, luz quente nas mudanças de assunto, corte com whoosh nos outros (`som_cortes`).
- **Fotos de pacientes são sensíveis:** ficam só no projeto local (`fotos-originais/` e
  `assets/fotos/` estão fora do git) e na página de envio; nunca em artefato publicado.
