# Reels da imobiliária: edição no HyperFrames

Pipeline para editar Reels de imóveis (1080×1920, 30 fps). O vídeo chega **já cortado**.
Aqui entram as legendas cinéticas sincronizadas com a fala, os destaques, os cards em
liquid glass, as transições e os efeitos sonoros. Nada de logo.

## Guia de estilo (tirado das duas referências)

| Elemento | Como é |
| --- | --- |
| Legenda | Palavra por palavra, no tempo da fala. Grupos de 2 a 3 linhas empilhadas. Frase de apoio em Poppins Light (300) e palavra-chave em Poppins Bold/ExtraBold (700/800), bem maior. |
| Espaçamento | Entrelinha bem curta (as linhas quase se encostam, `-0.16em`). Letras justas nas palavras grandes (`-0.035em`), como nas referências. Rótulos pequenos em caixa alta com letras bem abertas (`0.32em`). |
| Cor | O que não é destaque fica branco. O destaque usa a cor que predomina no vídeo (`scripts/paleta.py`): o tom claro sobre fundos escuros ou neutros, um tom mais escuro da mesma família (`destaque-escuro`) sobre paredes e pisos claros e branco sobre fundos da mesma cor do destaque. |
| Serifada | Instrument Serif Italic, para a palavra que fecha a ideia ("duplo.") e os números dos cards. |
| Liquid glass | Cards de informação (m², suítes, vagas, preço): vidro com desfoque do fundo, borda clara e reflexo, número em serifada e rótulo espaçado. |
| Entrada | Cada palavra entra saindo do desfoque (blur 12–16 px → 0) com um leve deslize: a fina sobe, a forte vem da esquerda, a serifada encolhe até o lugar. 0,34 s, `power3.out`. |
| Saída | O grupo sai linha a linha, subindo e desfocando (0,26 s, 0,05 s entre linhas). |
| Texto atrás da pessoa | Nos trechos em que a pessoa fala para a câmera, a legenda fica entre o fundo e a pessoa recortada (como na referência 1). |
| Texto em perspectiva | Quando o cliente pede, uma palavra de destaque do começo fica presa a uma superfície da cena (fachada, parede), na perspectiva dela e acompanhando a câmera quadro a quadro, atrás da pessoa. Mesmas fontes e estilos das legendas. |
| Transições | Nas mudanças de ambiente: vazamento de luz quente com clarão, mergulho no preto ou flash branco, com um zoom de entrada no plano novo. Nos cortes rápidos dentro do mesmo ambiente, só um empurrão de câmera discreto (`corte`). |
| Ambiente muito claro | Sombra mais firme nas próprias letras brancas (`"sombra_forte": true`), nunca um bloco de sombra atrás do texto. |
| Sombra da cor de destaque | Nunca preta: palavra colorida leva só uma sombra suave no tom escuro da própria cor (mesmo matiz). |
| Sons | Clique quando o texto volta depois de uma pausa e nos destaques. Whoosh nas transições e na entrada dos cards. As tomadas se alternam para não repetir o mesmo som. |
| Voz | Intocada: sem normalizar, comprimir ou tirar ruído. O áudio final é o original com ganho 1,0 mais os efeitos (`scripts/mixar.py`). |
| Música | Quando o vídeo vem sem trilha: leve e animada (referência: ~120 BPM, violão), cerca de 12 dB abaixo da fala e +4 dB nas pausas longas. Só a música é ajustada, nunca a voz. Licença livre (CC0 ou CC BY com crédito na legenda do post). |
| Tempo | Cada palavra entra no instante em que é dita, nunca antes (`scripts/sincronizar.py` corrige o adiantamento do Whisper). |
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
# monte projetos/casa-x/plano.json e acerte os tempos pela voz real
python3 scripts/sincronizar.py projetos/casa-x
scripts/recorte.sh projetos/casa-x                         # máscara da pessoa (texto atrás dela)
python3 scripts/estabilizar.py projetos/casa-x             # estabiliza por cena, vídeo e máscara juntos
python3 scripts/silhueta.py projetos/casa-x/assets/video/recorte.webm --janelas projetos/casa-x/plano.json
# texto em perspectiva (opcional): rastreia a superfície no vídeo já estabilizado
python3 scripts/rastrear.py projetos/casa-x projetos/casa-x/rastreios/fachada-a.json \
  --de 0 --ate 5.3 --ref 2.0 --quad "140,800 1060,800 1060,1160 140,1160" --roi "0,250 1080,250 1080,1300 0,1300"
python3 scripts/gerar.py projetos/casa-x
cd projetos/casa-x && npx hyperframes check && npx hyperframes render -o renders/render.mp4 --quality delivery
cd ../.. && python3 scripts/mixar.py projetos/casa-x projetos/casa-x/renders/render.mp4 projetos/casa-x/renders/final.mp4
```

## Formato do `plano.json`

```jsonc
{
  "video": "assets/video/video.mp4",
  "video_tem_audio": true,
  "recorte": "assets/video/recorte.webm",     // opcional: pessoa recortada por cima das legendas
  "recorte_janelas": [[0, 5.8], [35.7, 55.7]],  // opcional: só nas tomadas com a pessoa (drone e paisagem dão falso recorte)
  "duracao": 42.5,
  "cores": { "texto": "#FFFFFF", "destaque": "#E8B880", "destaque_escuro": "#B5653C", "vazamento": "#FF9A4D" },
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
      ],
      "sombra_forte": false                        // sombra mais firme nas letras, para fundo claro
    }
  ],
  "cards": [ { "id": "c1", "inicio": 5.0, "fim": 7.5, "y": 1060, "grande": "256", "unidade": "m²", "rotulo": "área construída" } ],
  // "grande": "Nossa Senhora|da Penha" quebra a linha no "|"; "tam": 118 troca o tamanho do texto grande
  "transicoes": [ { "t": 3.6, "tipo": "luz" } ],   // luz | preto | flash | corte; "zoom": false desliga o zoom
  "perspectivas": [ {                         // opcional: texto preso a uma superfície da cena
    "id": "pv1", "inicio": 0.13, "fim": 6.3, "tela": [920, 360],    // a tela (px) vai para o quad rastreado
    "ancoras": ["rastreios/fachada-a.json", "rastreios/fachada-b.json"],  // uma por tomada
    "linhas": [ { "estilo": "fina", "palavras": [ {"t": "Casa", "s": 0.13} ] } ]  // como nas legendas
  } ],
  "trilha": { "src": "assets/musica/x.mp3", "inicio_trilha": 97.6,   // opcional: música por baixo da voz
              "abaixo_da_voz_db": 12, "sobe_nas_pausas_db": 4, "fade_in": 0.3, "fade_out": 1.6 },
  "sfx_extra": [ { "t": 9.2, "som": "pop", "vol": 0.4 } ],
  "sfx_remover": [ { "t": 0.30 } ]
}
```

Estilos de linha: `fina`, `fina-it`, `media`, `forte`, `pesada`, `destaque` (ExtraBold na cor de
destaque), `serifa` e `rotulo` (caixa alta pequena, letras bem abertas). `s` é o instante em que a palavra é dita (vem de `transcricao.txt`). Uma
linha mais larga que a área segura tem a fonte reduzida automaticamente.

## Pastas

- `template/`: fontes (Poppins e Instrument Serif, licença OFL) e configuração do HyperFrames.
- `scripts/`: `analisar.py`, `sincronizar.py`, `paleta.py`, `gerar.py`, `recorte.sh`, `estabilizar.py`, `rastrear.py`, `silhueta.py`, `mixar.py`, `novo_projeto.sh`, `preparar_sfx.sh`.
- `teste-estilo/`: o teste de estilo feito sobre trechos de B-roll da referência (o vídeo não vai
  para o git).
- `projetos/`: um projeto por vídeo. Os vídeos e renders ficam fora do git.

Os efeitos sonoros vêm da biblioteca do HyperFrames (Pixabay, uso comercial sem crédito) e são
gerados por `scripts/preparar_sfx.sh`.
