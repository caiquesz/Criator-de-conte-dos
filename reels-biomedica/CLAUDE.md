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
  arquivos na ordem escolhida. Baixe as partes de cada arquivo na ordem (`read_asset` ou o
  `/_blob/<id>`), junte com `cat` e, se forem vários arquivos, emende-os nessa ordem.
- `fotos: [{nome, tamanho, tipo, largura, altura, categoria, grupo, quando, layout, partes}]`:
  `categoria` é `antes`, `depois`, `famosa` ou `outra`; `grupo` junta o antes e o depois da mesma
  pessoa (ou dá o nome da famosa); `quando` diz em que fala a foto entra; `layout` é `auto`
  (eu escolho), `cards`, `dividida`, `atras` ou `cheia`. Quase sempre `partes` tem um id só (a
  foto inteira); `emPedacos: true` significa juntar com `cat`; `convertida: true`, que a página
  já mandou em JPEG. Salve em `projetos/NOME/fotos-originais/`.
- `briefing: {tema, destaques, observacoes, musica}`, `status`, `nota` e `entrega` como nas
  páginas da imobiliária (mesmo formato de entrega, partes de até 19 MiB).

## Regras

- **Voz intacta**, legenda só quando ela fala, sombra nas letras: como no CLAUDE.md da imobiliária.
- **Legenda na frente dela** (`"legendas_na_frente": true`): nas referências o texto nunca passa
  atrás da pessoa.
- **Cada foto só enquanto ela fala daquilo**, como os cards de preço da imobiliária: entra na
  palavra que a chama e sai antes do assunto seguinte.
- **Antes e depois lado a lado, do mesmo tamanho:** o antes à esquerda; o rosto com o mesmo
  tamanho nas duas fotos (o gerador já faz pelo rosto). Sem `layout` pedido: par de antes e
  depois em `cards` na primeira vez e `dividida` quando ela comenta os detalhes; várias famosas em
  `dividida` (carrossel); uma famosa ou um resultado em `atras`; um resultado para impressionar em
  `cheia`, curto (2 a 4 s).
- **Fotos de pacientes são sensíveis:** ficam só no projeto local (`fotos-originais/` e
  `assets/fotos/` estão fora do git) e na página de envio; nunca em artefato publicado.
