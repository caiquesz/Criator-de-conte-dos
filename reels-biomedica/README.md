# Reels da biomédica

Vídeos de uma biomédica falando para a câmera, editados no HyperFrames no estilo das cinco
referências em `referencias/` (fora do git), com fotos de antes e depois, de famosas e de
resultados no momento em que ela fala delas. Os scripts são os mesmos dos Reels da imobiliária
(`../reels-imobiliaria/scripts/`); este README cobre só o que muda aqui.

## O que as referências mostram

| Ref. | O que pegar |
| --- | --- |
| 1 (depoimento de paciente) | Foto de perfil (antes) no fundo, no alto, com a pessoa recortada na frente; depois a foto do resultado; trechos em tela cheia com flash branco. Legenda pequena em duas linhas, a segunda em negrito. |
| 2 (toxina) | Legenda palavra a palavra, curta, e uma expressão escrita à mão ("pézinho de galinha"). |
| 3 (ciência da beleza) | Tela dividida: famosas passando em carrossel na metade de cima, ela embaixo, legenda na emenda. Flash branco para tela cheia. |
| 4 (visagismo) | Antes e depois em dois cards inclinados no alto; depois tela dividida com o antes e o depois lado a lado, separados por uma linha branca, e a legenda logo abaixo. |
| 5 (enxerto) | Foto da famosa no fundo, atrás dela; legenda com tamanhos misturados ("o resultado do / bumbum / **da Virgínia?**"); cena em preto e branco. |

**Legenda:** frases curtas (2 a 4 palavras), brancas, com sombra nas letras, no meio da tela ou
na emenda da tela dividida, sempre **na frente** da pessoa (`"legendas_na_frente": true`).
Estilos: `frase` (Poppins 600, 54 px), `frase-fina` (400, 46 px) para a linha de cima de duas,
`frase-forte` (800, 86 px) para a palavra que pesa, e `manuscrita` (Caveat, à mão) para uma
expressão de destaque, de vez em quando. As palavras entram no tempo da voz, como nos outros
Reels (`scripts/sincronizar.py`).

## Fotos no vídeo

As fotos chegam pela página de envio com o que são (antes, depois, famosa, outra), de quem são
(o mesmo nome junta o antes e o depois), quando entram e como mostrar. Cada uma vira uma entrada
de `fotos` no `plano.json`, presa à fala:

```jsonc
"legendas_na_frente": true,
"fotos": [
  // antes e depois em dois cards inclinados no alto, ela embaixo
  { "id": "f1", "layout": "cards", "inicio": 3.2, "fim": 8.6,
    "imagens": ["assets/fotos/ana-antes.jpg", "assets/fotos/ana-depois.jpg"], "rotulos": true },
  // metade de cima com as fotos, o vídeo desce para a metade de baixo; 3 ou mais fotos = carrossel
  { "id": "f2", "layout": "dividida", "inicio": 10, "fim": 18, "corte": 880,
    "imagens": ["assets/fotos/famosa1.jpg", "assets/fotos/famosa2.jpg", "assets/fotos/famosa3.jpg"] },
  // a foto no fundo, no alto, e ela recortada na frente (precisa do recorte da pessoa)
  { "id": "f3", "layout": "atras", "inicio": 0.2, "fim": 5.4, "altura": 1150,
    "imagens": ["assets/fotos/virginia.jpg"] },
  // a foto na tela inteira, com zoom lento e flash branco na entrada e na saída
  { "id": "f4", "layout": "cheia", "inicio": 20.1, "fim": 23.0, "imagens": ["assets/fotos/resultado.jpg"] }
]
```

- **Enquadramento pelo rosto:** `scripts/preparar_fotos.py` acha o rosto de cada foto; o gerador
  põe o rosto no lugar certo de cada caixa e, num par de antes e depois, com o mesmo tamanho nas
  duas fotos. Para outra parte da foto (um corpo, um lábio): `{"src": "...", "foco": [0.5, 0.7],
  "zoom": 1.3}`, com o foco em fração da foto; `"rosto": false` desliga o enquadramento pelo rosto.
- **Rótulos:** `"rotulos": true` escreve ANTES e DEPOIS nos cards; uma lista troca os nomes
  (`["antes", "30 dias depois"]`). As referências não usam: ligue quando ajudar a entender.
- **Tela dividida:** `corte` é onde a metade de cima termina (padrão 880 px); o vídeo desce sozinho
  para os olhos dela ficarem a 30% da metade de baixo (medido pelo `preparar_fotos.py`; `desce`
  força um valor). A legenda desse trecho vai logo abaixo da linha branca (y ≈ corte + 40).
- **Atrás dela:** precisa do recorte da pessoa (`scripts/recorte.sh`) e de `recorte` no plano
  (com `recorte_janelas` só nesses trechos); a foto desce até `altura` e some num degradê para o
  fundo do vídeo. O rosto da foto fica à direita e no alto (`"centro": [0.7, 0.24]`, fração da
  caixa), ao lado da cabeça dela e não escondido atrás; mude o `centro` se a foto pedir.
- Cada formato tem som de entrada (whoosh, clique); `"sons": false` tira.

## Como editar um vídeo dela

```bash
cd ../reels-imobiliaria
scripts/novo_projeto.sh NOME video.mp4 ../reels-biomedica/projetos
# as fotos baixadas da página vão para ../reels-biomedica/projetos/NOME/fotos-originais/
python3 scripts/analisar.py ../reels-biomedica/projetos/NOME        # transcrição e cortes
bash scripts/recorte.sh ../reels-biomedica/projetos/NOME            # se tiver foto "atras"
# monte o plano.json (legendas + fotos) e acerte os tempos pela voz
python3 scripts/sincronizar.py ../reels-biomedica/projetos/NOME
python3 scripts/preparar_fotos.py ../reels-biomedica/projetos/NOME  # fotos convertidas + rostos
python3 scripts/gerar.py ../reels-biomedica/projetos/NOME
# check, snapshot, render e mixar.py como nos outros Reels
```
