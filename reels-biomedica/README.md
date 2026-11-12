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

**Legenda:** como nas referências, pequena, branca, numa linha (2 a 5 palavras), na altura do
peito (meio do bloco em y ≈ 1040, no top dela), a mesma em todo o vídeo, sempre **na frente** da
pessoa (`"legendas_na_frente": true`). A frase entra inteira e troca seca (`"legendas_modo":
"corte"`), sem fade: uma nunca por cima da outra. Estilos: `legenda` (Poppins 700, 46 px) e
`legenda-forte` (800, 64 px) para a palavra que pesa, às vezes numa segunda linha (como "bumbum /
da Virgínia?" da referência 5); letras juntas (`"tracking": {"legenda": -0.04}`, `"entrelinha":
-0.02`). A cliente pediu Poppins e não gostou da cursiva (`manuscrita`): não use. Os tempos vêm da
voz (`scripts/sincronizar.py`).

**Abertura do quadro "Caso <famosa>":** a única animação (sem cards, listas ou selos: a cliente
recusou). Uma tela cheia logo depois do gancho, numa pausa aberta no vídeo (`"pausas": [{"em":
8.1333, "dur": 2.4}]`, tempo do original; o `reenquadrar.py` congela a imagem e põe silêncio, e
grava a voz exata em `assets/video/voz.wav` para o `mixar.py`, via `"video_original"`). Todos os
tempos do plano depois da pausa andam 2,4 s, menos `enquadramentos` e `pausas`. A tela vem de
`abertura.py` no projeto (`compositions/abertura.html`, montada com `"extras"`; sons em
`abertura-sons.json` → `sfx_extra`) e é delicada, como a referência 1: o vídeo da famosa ao fundo
em tom quente, véu nude, luz pêssego, brilhos subindo, "CASO" / nome / frase do gancho em Poppins
fina entrando em fade, som `brilho` (`scripts/sfx_sintetizar.py`); a transição `luz` de entrada e
saída leva `"som": "whoosh"` (cada transição aceita `som` e `vol`).

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

- **Enquadramento pelo corpo:** ela trabalha com glúteo (harmonização corporal: glúteo, gordura
  localizada, celulite, flacidez de coxa), então as fotos são de corpo, quase sempre de costas ou
  de lado. `scripts/preparar_fotos.py` acha a silhueta de cada foto e o ponto do quadril (com a
  cabeça na foto, uns 3,8 rostos abaixo do rosto), e o gerador põe esse ponto no centro de cada
  caixa (`"foco_fotos": "corpo"`, o padrão). Num par de antes e depois em que as duas fotos mostram
  o corpo inteiro, os dois corpos ficam na mesma escala; com fotos já cortadas pela clínica, as duas
  cobrem a caixa do mesmo jeito. Confira cada foto no snapshot e, quando o ponto não for o certo,
  force: `{"src": "...", "foco": [0.5, 0.7], "zoom": 1.3}` (foco em fração da foto).
  `"foco_fotos": "rosto"` enquadra pelo rosto, para um vídeo que fale de rosto.
- **Rótulos:** `"rotulos": true` escreve ANTES e DEPOIS nos cards; uma lista troca os nomes
  (`["antes", "30 dias depois"]`). As referências não usam: ligue quando ajudar a entender.
- **Tela dividida:** meio a meio nos vídeos dela (`"corte": 960`, esfumada com `"dissolve": 0.32`; ou `"linha": false` para o corte seco da
  referência 3; com uma imagem só e `"saida": "corte"`, ela já abre dividida e sai num corte seco).
  `corte` é onde a metade de cima termina (padrão 880 px); o vídeo desce sozinho
  para os olhos dela ficarem a 30% da metade de baixo (medido pelo `preparar_fotos.py`; `desce`
  força um valor). A legenda desse trecho vai logo abaixo da linha branca (y ≈ corte + 40).
- **Atrás dela:** precisa do recorte da pessoa (`scripts/recorte.sh`) e de `recorte` no plano
  (com `recorte_janelas` só nesses trechos); a foto desce até `altura` e some num degradê para o
  fundo do vídeo. O quadril da foto fica à direita (`"centro": [0.72, 0.5]`, fração da caixa), ao
  lado dela e não escondido atrás; mude o `centro` se a foto pedir.
- **Vídeo no lugar da foto:** uma imagem pode ser um vídeo (`assets/fotos/x.mp4`, ex.: a gravação de
  tela de um post da famosa, convertida para 1080×1920 a 30 fps com `-g 30`); entra sem som, a voz
  dela continua. Dê o `foco` à mão (`{"src": "assets/fotos/x.mp4", "foco": [0.5, 0.73]}`).
- **Tela dividida esfumada** (`"esfumado": true`, referência 1): sem linha branca, a parte de cima
  se dissolve no vídeo dela (`"dissolve": 0.3` da altura do painel). No começo do vídeo já abre
  dividida; `"saida": "corte"` faz sair no mesmo quadro de um corte de enquadramento (sem a faixa
  preta que aparece quando o vídeo sobe enquanto o painel some).
- **Planos aberto, médio e fechado** numa tomada só: `"enquadramentos"` no plano e
  `scripts/reenquadrar.py` (corta do 4K original, nas pausas da fala; ponha as transições `corte`
  nos mesmos quadros, `quadro/30`).
- **Legenda em cenário claro** (poltrona e almofada brancas): meça a faixa mais escura de cada plano
  e ponha a legenda nela (na Virgínia, a calça jeans), com `sombra_forte`; numa foto em tela cheia,
  fora do que a foto mostra.
- Cada formato tem som de entrada (whoosh, clique); `"sons": false` tira. O `mixar.py` baixa os
  efeitos na mesma proporção quando a voz foi gravada mais baixa que a do André (a dela veio uns
  24 dB mais baixa), sem tocar na voz.

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
