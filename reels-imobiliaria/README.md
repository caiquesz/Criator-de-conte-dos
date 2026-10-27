# Reels da imobiliária: edição no HyperFrames

Pipeline para editar Reels de imóveis (1080×1920, 30 fps). O vídeo chega **já cortado**.
Aqui entram as legendas cinéticas sincronizadas com a fala, os destaques, os cards em
liquid glass, as transições e os efeitos sonoros. Nada de logo.

## Guia de estilo (tirado das duas referências)

| Elemento | Como é |
| --- | --- |
| Legenda | Palavra por palavra, no tempo da fala. Grupos de 2 a 3 linhas empilhadas. Frase de apoio em Poppins Light (300) e palavra-chave em Poppins Bold/ExtraBold (700/800), bem maior. |
| Espaçamento | Entrelinha bem curta (as linhas quase se encostam, `-0.16em`). Letras justas nas palavras grandes (`-0.035em`), como nas referências. Rótulos pequenos em caixa alta com letras bem abertas (`0.32em`). |
| Cor | O que não é destaque fica branco. O destaque usa a cor que predomina no vídeo (`scripts/paleta.py`). Sobre um fundo da mesma cor, o destaque fica branco em serifada. |
| Serifada | Instrument Serif Italic, para a palavra que fecha a ideia ("duplo.") e os números dos cards. |
| Liquid glass | Cards de informação (m², suítes, vagas, preço): vidro com desfoque do fundo, borda clara e reflexo, número em serifada e rótulo espaçado. |
| Entrada | Cada palavra entra saindo do desfoque (blur 12–16 px → 0) com um leve deslize: a fina sobe, a forte vem da esquerda, a serifada encolhe até o lugar. 0,34 s, `power3.out`. |
| Saída | O grupo sai linha a linha, subindo e desfocando (0,26 s, 0,05 s entre linhas). |
| Texto atrás da pessoa | Nos trechos em que a pessoa fala para a câmera, a legenda fica entre o fundo e a pessoa recortada (como na referência 1). |
| Transições | Nos cortes de cena: vazamento de luz quente com clarão (padrão), mergulho no preto ou flash branco, sempre com um leve zoom de entrada no plano novo. |
| Sons | Clique na entrada de cada grupo e nos destaques. Whoosh nas transições e na entrada dos cards. As tomadas se alternam para não repetir o mesmo som. |
| Área segura | Texto entre y=168 e y=1330 px (abaixo disso ficam a legenda e os botões do Instagram), dentro de 880 px de largura. |

Medida certa: um grupo de legenda por frase, um card só quando há um número que vale
mostrar, uma transição por troca de cena.

## Como editar um vídeo novo

```bash
# uma vez por máquina
npx hyperframes skills            # skills e biblioteca de sons do HyperFrames
npx hyperframes browser ensure    # Chrome usado na renderização
pip install faster-whisper pillow numpy

scripts/novo_projeto.sh casa-x ~/Downloads/casa-x.mp4   # cria projetos/casa-x
python3 scripts/analisar.py projetos/casa-x               # transcrição, cortes e paleta
# monte projetos/casa-x/plano.json (formato abaixo) a partir de transcricao.txt
npx hyperframes remove-background projetos/casa-x/assets/video/video.mp4 \
  -o projetos/casa-x/assets/video/recorte.webm --quality best   # só se houver texto atrás da pessoa
python3 scripts/gerar.py projetos/casa-x
cd projetos/casa-x && npx hyperframes check && npx hyperframes render -o renders/final.mp4 --quality delivery
```

## Formato do `plano.json`

```jsonc
{
  "video": "assets/video/video.mp4",
  "video_tem_audio": true,
  "recorte": "assets/video/recorte.webm",     // opcional: pessoa recortada por cima das legendas
  "duracao": 42.5,
  "cores": { "texto": "#FFFFFF", "destaque": "#E8B880", "vazamento": "#FF9A4D" },
  "tracking": { "forte": -0.035, "fina": -0.01, "serifa": -0.01 },
  "entrelinha": -0.16,
  "legendas": [
    {
      "id": "g1", "y": 560, "fim": 3.3,           // topo do bloco (px) e fim do grupo (s)
      "alinhar": "centro",                         // centro | esquerda | direita
      "linhas": [
        { "estilo": "fina", "dx": -60, "palavras": [ {"t": "uma", "s": 0.30}, {"t": "sala", "s": 0.42} ] },
        { "estilo": "forte", "palavras": [ {"t": "pé-direito", "s": 1.18} ] },
        { "estilo": "serifa", "cor": "texto", "palavras": [ {"t": "duplo.", "s": 1.75} ] }
      ]
    }
  ],
  "cards": [ { "id": "c1", "inicio": 5.0, "fim": 7.5, "y": 1060, "grande": "256", "unidade": "m²", "rotulo": "área construída" } ],
  "transicoes": [ { "t": 3.6, "tipo": "luz" } ],   // luz | preto | flash; "zoom": false desliga o zoom
  "sfx_extra": [ { "t": 9.2, "som": "pop", "vol": 0.4 } ],
  "sfx_remover": [ { "t": 0.30 } ]
}
```

Estilos de linha: `fina`, `fina-it`, `media`, `forte`, `pesada`, `destaque` (ExtraBold na cor de
destaque) e `serifa`. `s` é o instante em que a palavra é dita (vem de `transcricao.txt`). Uma
linha mais larga que a área segura tem a fonte reduzida automaticamente.

## Pastas

- `template/`: fontes (Poppins e Instrument Serif, licença OFL) e configuração do HyperFrames.
- `scripts/`: `analisar.py`, `paleta.py`, `gerar.py`, `novo_projeto.sh`, `preparar_sfx.sh`.
- `teste-estilo/`: o teste de estilo feito sobre trechos de B-roll da referência (o vídeo não vai
  para o git).
- `projetos/`: um projeto por vídeo. Os vídeos e renders ficam fora do git.

Os efeitos sonoros vêm da biblioteca do HyperFrames (Pixabay, uso comercial sem crédito) e são
gerados por `scripts/preparar_sfx.sh`.
