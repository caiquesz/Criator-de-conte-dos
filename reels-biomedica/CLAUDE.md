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
  páginas da imobiliária (mesmo formato de entrega, partes de até 19 MiB). Para mandar mais de uma
  versão para a cliente escolher, grave `entregas: [{rotulo, arquivo, tamanho, sha256, descricao, partes}]`
  (um botão "Baixar <rotulo>" para cada; com `entregas`, apague `entrega`). Foi assim no Bate-bola, em 16/11:
  opção A (arco) e opção B (tela cheia).

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

- **Siga as referências que ela manda, à risca, e estude cada uma antes de editar** (17/11: "até agora você não
  fez nenhum vídeo com base nas referências"). Grade a 2 quadros/s, tiras a 10–15 quadros/s nas transições,
  letras de perto. As duas de 17/11 valem daqui para a frente:
  - `referencias/ref-blazer-marrom.mp4` (a moça sentada de blazer marrom): **a estética de tudo** — planos
    aberto e fechado alternando em corte seco (zoom in, zoom out), P&B nas falas de drama (entra seco; sai num
    clarão ou esmaecendo escurecido para a cor), luz quente nas transições, as legendas dela (abaixo) e um som
    em cada evento. **Sem color grade:** a cor da moça de blazer (pele dourada, vinheta) ela recusou na 3ª versão;
    vale a regra do Bate-bola, a cor do vídeo dela nunca muda.
  - **legendas = o formato da referência, em Poppins, com o gosto dela** (4ª e 5ª versões, 17/11). Na 4ª: "as
    legendas que você fez não têm nada a ver com as que eu pedi; a única coisa que eu falei foi para usar a
    Poppins" (na 2ª eu fiz palavra por palavra do desfoque; na 3ª, sem vírgula nenhuma). Medido na referência,
    quadro a quadro, e é o formato: **uma frase curta por vez** (2 a 6 palavras, cortadas nas pausas), numa linha,
    centralizada, com o meio da linha fina a ~78% da altura (y ≈ 1500); **a frase inteira de uma vez e troca em
    corte seco**; fina **itálica Light minúscula** (Poppins 300 itálica, 45 px); a palavra que pesa em **ExtraBold
    itálica do mesmo tamanho**, dentro da frase; de vez em quando a frase sozinha em ExtraBold itálica maior (58 px)
    entrando com borrão de lado; a palavra de impacto em **ExtraBold reta grande** (~1,75x, até 65% da largura) com
    a fina pequena em cima, entrando seca na palavra dela; duas linhas só no fim; **com as vírgulas da fala** e sem
    ponto final; só a primeira palavra do vídeo com maiúscula. **O gosto dela, por cima da referência (5ª versão):**
    (a) **letras juntinhas** ("gosto muito da estética quando elas ficam mais juntinhas": −0,045em na fina, −0,04em
    no negrito, −0,05em na grande) e **linhas próximas** (entrelinha 1,08; a grande 0,98). Na 3ª ela já tinha pedido
    "espaçamento entre linhas bem diminuído" e eu li como reclamação e abri para 1,45 na 4ª: era pedido; (b) **um
    padrão só de cor**: a fala **sempre branca** e tudo o que pesa **sempre bege #EED6A4** (o negrito dentro da
    frase, a frase forte e a palavra grande), com a sombra no tom escuro do bege ("uma hora a fonte tá bege, na outra
    tá branca, não tem um padrão": na 4ª o negrito e a frase forte eram brancos e a grande, bege); sem serifada (a
    "harmonioso" em Playfair branca saiu). Modelo: `LEGENDAS` no `roteiro.py` e o CSS do `montar_plano.py` do Caso
    de paciente. Poppins ExtraBold itálica vem do npm (`@fontsource/poppins`; o GitHub dá 403);
  - **cor do vídeo e das fotos igual à que ela mandou:** o vídeo dela vem em **faixa limitada (16–235) e Display P3**,
    e as fotos do iPhone em P3. O `enquadrar.py` lia como faixa cheia e sem converter o P3, e o `preparar_fotos.py`
    jogava fora o perfil: tudo saía lavado ("você tirou a saturação do vídeo"). Agora os dois leem a etiqueta e
    convertem para BT.709/sRGB. Na padronização de takes, **só a luz** (`--cor-pela luz`: um ganho por take, igual
    nos três canais; "alterando apenas a iluminação"): nada de balanço de branco nem saturação. Confira a saturação
    (média de máx−mín do RGB) contra o original lido certo antes de entregar;
  - **efeitos sonoros que se ouçam:** a voz dela é gravada ~14 dB abaixo da do André e o `mixar.py` baixa os
    efeitos junto; na 2ª versão, a 0,2–0,3, quase não se ouviam ("senti falta de efeitos sonoros"). Um som em
    cada evento (grave no P&B a 0,9, whoosh nas trocas de plano a 0,4–0,5, whoosh e clique nas fotos a 0,6–0,7,
    clique agudo nas palavras que pesam a 0,7, brilho no resultado, transições a 0,8), nunca dois a menos de 0,4 s;
  - **zoom sem tremor:** nunca `zoompan` do ffmpeg num zoom lento (arredonda a posição e a imagem treme ~2 px a
    cada quadro; ela viu na foto). Use o `empurrar()` do `montar_video.py` (warpAffine fracionário no YUV) ou a
    escala do GSAP, e meça com `scripts/medir_tremor.py` (ECC quadro a quadro);
  - `referencias/ref-dentista-antes-depois.mp4`: **o antes e depois**, minimalista e delicado — a foto numa
    faixa no alto com ela embaixo; o par lado a lado, encostado, com um fio branco no meio, atravessando o peito
    dela e crescendo de leve; uma foto só em faixa de cantos arredondados, entrando do desfoque; a foto em tela
    cheia esmaecendo. Nada de cards inclinados, molduras ou sombras, e **nada de recorte da pessoa** (o antes
    atrás dela, recortado, ficou feio na borda).
  Modelo: `projetos/caso-paciente/roteiro.py`, `montar_video.py` e `montar_plano.py` (5ª versão).
- **Marcação com lápis na foto** (Caso de paciente, 6ª versão: "um lapisinho passando, como se fosse uma marcação,
  marcando o hip dips"): um lápis branco pequeno (como o dermográfico da clínica) contorna a região numa linha branca
  com textura de traço e sombra marrom leve, um lado de cada vez, ~0,8 s por lado, com som de lápis (`lapis.mp3`,
  sintetizado). A posição sai do contorno do corpo na foto (onde a borda fica reta logo abaixo do quadril) e a
  marcação acompanha o empurrão do plano. Modelo: `MARCACAO` no `roteiro.py` e `compositions/marcacao.html`.
- **Foto que a cliente retocou** (6ª versão: tirou uma manchinha que a paciente não quer mostrar): troque a original
  em `fotos-originais/` pela retocada (mesmo nome), rode `preparar_fotos.converter` e o `cortar_fotos.py`, e não
  guarde a versão sem retoque em lugar nenhum.
- **Trecho de voz gravado à parte** (Caso de paciente, 7ª versão: "nessa parte a gente gravou uma gravação de áudio
  dela, por isso o tom ficou diferente"): a voz continua intocada, **só aquele trecho** é igualado ao resto, e só
  porque ela pediu. Ache as emendas pelas pausas, meça o timbre **só nas vogais** contra trechos de 2,6 s da fala
  normal (com tudo, o "s" e o "ch" da frase enganam a medida) e confira a altura da voz (F0): lá era a mesma, a
  diferença era o microfone do celular (agudos +6 a +22 dB, um pouco de grave) e 2 dB a mais de volume. Corrija
  com EQ de fase linear (~90% da diferença) e o volume das frases vizinhas, transições de 20 ms nas pausas, e
  **nunca mude a altura da voz** (é o que soaria artificial). O resto sai idêntico ao original, amostra por
  amostra; o plano lê a voz de `assets/video/voz-igualada.wav`. Modelo: `projetos/caso-paciente/igualar_voz.py`.
- **Som do lápis baixo:** a 0,75 ela achou alto; 0,3 (uns 17 dB abaixo da voz) ficou o volume.
- **Efeitos sonoros mais baixos** (8ª versão: "tô achando eles muito altos"): depois de pedir mais efeitos na 3ª, ela
  achou altos os volumes que eu pus (P&B 0,9, whoosh 0,4–0,7, cliques 0,6–0,7). Ficou `"volume_efeitos": 0.5` no
  plano (todos 6 dB abaixo, o equilíbrio entre eles igual; o `gerar.py` aplica o fator em todos os efeitos). Comece
  os próximos vídeos dela já nesse nível.
- **Referência da Dra. de blazer branco** (`referencias/ref-pesar-o-clima.mp4`, 18/11, para o "Posso pesar o clima?": "pegue
  as fontes, as transições, como cada palavra entra e sai, tudo; só não o color grade"). Medido quadro a quadro: título
  em três linhas centralizadas a 38% da largura ("POSSO / PESAR" ultrafinas, "O CLIMA?" em negrito, o nome pequeno
  embaixo: "DRA." fino, o nome em negrito), entrando descendo em 0,3 s enquanto o vídeo sai de um zoom, e saindo numa
  luz quente (laranja e clarão branco); legendas finas com maiúsculas e pontuação normais, 1 a 4 palavras, a ~57% da
  altura, troca seca; palavras de impacto em maiúsculas ultrafinas grandes, linhas coladas, entrando de baixo em 0,2 s
  e saindo secas; P&B na frase de peso com luz quente na entrada e na saída; a assinatura em pincel no fim.
  (Os tempos e distâncias dessa 1ª leitura estavam errados: valem os da 3ª versão, abaixo.)
  **2ª versão ("tá com um zoom na pessoa"; "as fontes não estão nada iguais"):**
  - **o enquadramento faz parte da referência:** lá o rosto ocupa 30% da largura e fica a 30% da altura; no vídeo da
    Nádia, 18–19% e a 40%. Recorte fixo de 1,6x por take, do 4K (sem perder nitidez), deslizando junto nos zooms do
    próprio vídeo (`montar_video.py`). Meça o rosto (YuNet) nos dois vídeos antes de editar;
  - **a fonte é Helvetica Neue** (R de perna reta, G com esporão, "a" com rabinho, letras coladas), e a Inter da 1ª
    versão não parecia. Entre as livres, comparando na mesma escala: Roboto 100 nas maiúsculas e nas linhas finas do
    título (98 px, −0,06em), Roboto 300 nas legendas (**59 px**, −0,055em: a altura-x da referência é ~31 px; eu tinha
    posto 46) e FreeSans Bold (o clone da Helvetica Bold do GNU FreeFont, −0,025em) no "O CLIMA?" e no nome.
  **3ª versão ("o zoom é só na introdução, com a fonte na lateral"; "não quero nenhum contorno, nenhuma sombra";
  "até a posição das palavras eu quero idêntico"; "você não tá seguindo as referências"):**
  - **o zoom da 2ª era um erro de leitura:** na referência só a abertura (enquanto ela fala o título) é fechada, com o
    rosto à direita (centro a 69% da largura e 31% da altura, 28% da largura) e o título à esquerda; depois da luz
    volta o plano normal. Zoom fixo só nos quadros da abertura, o resto com o enquadramento original;
  - **sem sombra nenhuma** em texto nenhum (`SOMBRA = "none"`): a regra da imobiliária ("sombra nas letras") não
    vale quando a referência não tem;
  - **"idêntico" = medido em pixels, não a olho.** Para cada texto: caixa da letra na referência (1080×1920) contra
    a nossa no snapshot, e ajuste até ficar a 1–3 px. Medidas: título POSSO 882–947 / PESAR 960–1032 (as duas linhas
    finas com a mesma largura, x 277–550: o PESAR é maior) / O CLIMA? 1049–1120 (x 190–627), nome em maiúscula de
    25 px a 1216 e 1247 (x 319); legendas com a faixa do x em 1077–1106; maiúsculas com o bloco centrado em ~1107
    (letra de 68–70 px, linha a cada 82 px), o HARMONIZAÇÃO GLÚTEA à esquerda (x 208) com letra de 58 px;
    assinatura em x 280–840 / y 1067–1350;
  - **o movimento também se mede**, por correlação com o quadro parado (`reels-imobiliaria/scripts/movimento_texto.py`), não pelo
    olho em quadros soltos: na 1ª/2ª eu tinha posto o título descendo 70 px em 0,32 s e as maiúsculas subindo 60 px
    em 0,2 s, e o certo era: título descendo de 400 px em 0,5 s (power1.out) aparecendo em 0,47 s, e o nome
    separado, subindo 45 px em 0,18 s; maiúsculas com deslocamento e duração próprios por bloco (descendo de 360 px
    em 0,47 s no AGACHAMENTO, de 170 px em 0,38 s no NÃO É ISSO, de 235 px em 0,12 s no A PROJEÇÃO, subindo de 200 px
    em 0,22 s no HARMONIZAÇÃO) e as que vêm logo depois de outra trocam seco; assinatura aparecendo em 0,45 s,
    subindo 16 px, de 105% para 100%, com cortina suave da esquerda;
  - **o GSAP sobrescreve o `transform` do CSS:** um `y` animado apaga o `translateY(-50%)` (as maiúsculas da 2ª
    ficaram 80 px baixas). Use `yPercent` no próprio tween;
  - **a assinatura entra sozinha**, quando a última legenda sai, e fica 1,1 s; o vídeo dela acaba 0,4 s depois da
    última palavra, então o último quadro fica parado 26 quadros (`CAUDA` no `montar_video.py`; a voz vai para
    `assets/video/voz.wav`, amostra por amostra, mais silêncio). A letra de pincel agora é a Satisfy inclinada mais
    10° (o traço médio e os laços da referência); a Mr Dafoe era pesada demais.
  **4ª versão ("gostei muito, ficou muito igual"; "desce a legenda um pouco mais"; "não gostei da fonte da legenda
  tradicional, não achei igual à referência"; as maiúsculas ela aprovou):**
  - **legenda normal mais baixa que na referência:** centro da altura-x em 1159 (lá, 1091), uns 70 px abaixo. As
    maiúsculas continuam em 1107. Nos próximos vídeos dela, comece já com a legenda nessa altura;
  - **a legenda normal fica na Roboto 300 (59 px, −0,055em), a da 3ª versão.** Na 4ª eu troquei pela FreeSans
    (o desenho da Helvetica) afinada no FontForge até o peso da Light e ela achou "horrível": afinada, a FreeSans
    ficou com as letras estreitas, altas e espaçadas, nada da Helvetica Neue larga e colada da referência. Ela
    preferiu voltar à Roboto (5ª versão). Não tente de novo afinar uma fonte Regular para imitar uma Light; se ela
    pedir outra fonte, mande antes uma imagem com a frase da referência e as candidatas (na mesma altura-x e na
    mesma largura de frase) para ela escolher, sem renderizar o vídeo.
  **6ª versão ("dá para remover o barulho da xícara batendo?"; "tá entre o segundo 14 e o 20, depois disso é a
  batida da música"):**
  - **os vídeos dela já vêm com música** (aqui, batida de 120 por minuto do começo ao fim, com chimbal a cada
    0,25/0,5 s a partir dos 16 s). O chimbal parece estalo de objeto no detector de estalos: não é a xícara e fica;
  - **pergunte o trecho antes de caçar um ruído no vídeo todo.** Eu procurei sozinho e marquei 7,45, 15,47 e
    33,25 s; ao conferir, duas das janelas tinham voz (periodicidade alta na faixa de 80–1000 Hz, com a altura da
    voz dela, 210–260 Hz) e a limpeza ia comer o começo de palavras. Sempre meça a periodicidade da voz dentro de uma
    janela antes de mexer nela;
  - **a xícara (de metal, dourada) não é só o estalo:** cada batida deixa notas finas soando por até ~0,5 s (4,55 kHz
    a principal; ~3,6–4,1, ~6,9, ~7,2–7,5, ~10,6–11,4 kHz) e, quando ela segura, a xícara chacoalha no pires (série de
    estalinhos). Confira no vídeo quadro a quadro quando a mão está na xícara;
  - **como tirar sem mexer na voz** (`projetos/pesar-o-clima/limpar_xicara.py`): só nas janelas, (1) as notas da
    xícara e os picos estreitos de 3–13 kHz descem ao nível do espectro em volta e (2) nos estalos, acima de 2 kHz,
    cada faixa fica limitada à mediana dos 30 ms em volta. Abaixo de 2 kHz nada muda (a voz ficou idêntica, 0,0 dB) e
    fora das janelas o áudio sai igual ao original, amostra por amostra. O plano lê a voz de
    `assets/video/voz-sem-xicara.wav` (ordem: `montar_video.py`, `limpar_xicara.py`, `montar_plano.py`). Mudar só o
    áudio não pede render: `mixar.py` sobre o vídeo final anterior (ele copia a imagem e troca o som).
  Fontes: Roboto e Satisfy do npm (`@fontsource/...`), FreeSans do apt (`fonts-freefont-ttf`), copiadas para
  `assets/fonts/`. Modelo: `projetos/pesar-o-clima/montar_plano.py` e `montar_video.py`. Os nomes das camadas
  próprias não podem ser `legendas.html` nem `cards.html` (o `gerar.py` escreve por cima).
- **O nome é Dra. Nádia Resende, com S** (o Whisper escreve "Rezende"/"Rezegues": corrija sempre).

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
  responde). A primeira versão (abertura com véu nude, flash branco, legenda palavra a palavra) ela
  achou básica e mandou dois modelos para seguir o mais perto possível:
  - **abertura como a do bate-bola de uma doutora:** cursor de mouse em pixel clica nela duas vezes
    (cada clique fecha o plano, do 4K), estrelas douradas estouram e ficam girando, imagem quente com
    grão, "★ Bate Bola com" digitado em Poppins creme e o nome à mão em **Pinyon Script** (ali a
    letra cursiva é o modelo: ela só não quer cursiva nas legendas), trancos de zoom, barras
    coloridas de TV com bipe e corte. Música de abertura (CC BY, crédito no post) e pausa de 1,6 s
    depois do título;
  - **textos e legendas como os da Nina Secrets:** cada pergunta vira um texto em duas linhas, o tema
    em negrito e o resto regular (estilo `texto`, Poppins 400 44 px, palavras com `"b": true` em
    negrito); as respostas com a mesma tipografia, a palavra que pesa em negrito; cortes secos (sem
    flash) e as reações em preto e branco (`"pb"`), com um whoosh.
  Na terceira versão ela corrigiu: (1) a abertura só começa **depois** de ela dizer o título, como no
  modelo (pausa de 4,4 s logo depois da fala); (2) no fundo, **trechos dela falando**, nunca a imagem
  parada (pegou ela de olho fechado): `broll.py`, com a piscada medida quadro a quadro pelo mediapipe
  (blendshape `eyeBlink` < 0,35 em todos os quadros; precisa de `apt-get install libegl1`; medir pelo
  escuro do olho falha, os cílios e o delineado dela ficam escuros de olho fechado) e só onde ela fala;
  (3) **estrelas chapadas como as do modelo** (sem contorno, sem degradê: amarelo #DCAB55 e algumas
  caramelo #7C4D27, poucas e espalhadas), não douradas com brilho; (4) no fim, **nem aspas nem emoji**: só a
  frase, maior e em negrito (aspas abertas sem fechar ela notou na hora, e pediu para tirar o ✨ que pus no
  lugar); (5) Resende com S; (6) **um clique só**: o cursor clica e no mesmo instante entra a abertura
  inteira (com dois cliques o vídeo pulava para o trecho de perto sem nada e ela achou que bugou).
  (7) **emenda sem tranco:** depois ela notou um pico no som na entrada do quadro: a pausa caía no começo do
  "Nádia" da pergunta seguinte (a palavra partia ao meio) e o corte seco estalava. A pausa vai num silêncio
  medido (a frase acaba em 2,56 s, a pergunta começa em 2,90: pausa em 2,83, último quadro de olho aberto),
  com rampas de 25 ms (`reenquadrar.py`, só no fundo, nunca na voz); a música sobe do silêncio meio segundo
  antes do clique e a batida forte cai nele (`PICO_SFX` 0,5333); e a troca para o trecho de perto é uma
  transição de zoom (o quadro dela mergulha com desfoque e o trecho chega focando), sem esmaecer duplo.
  (8) **Sem estrelas e sem barras de TV:** em 16/11 a cliente recusou as estrelas, a entrada do quadro e a
  "tela falhada" (as barras coloridas com bipe), mesmo sendo do modelo. Quatro opções que mandei (pinceladas,
  luz dourada com bolinhas, moldura em arco, clique abrindo um círculo) ela achou **infantis**: quer algo
  **profissional, como a abertura de um programa de TV**. Gostou mais do arco (mas "bugou": dentro dele o trecho
  de perto se misturava com a imagem parada, imagem dupla) e da moldura de papel do título nas pinceladas. Agora
  o `abertura.py` tem `tv-arco` e `tv-cheia` (`python3 abertura.py ESTILO`): painéis retos caramelo/marrom com
  creme por cima sobem e revelam, o título na moldura de papel com as palavras subindo de uma máscara e um
  brilho, e os painéis voltam para a pergunta; toda troca de imagem fica escondida atrás dos painéis (nada de
  esmaecer uma imagem sobre a outra). Use o que ela escolher como padrão do script. Fica de todos: o título
  dito antes, os trechos de perto, a música, o nome em Pinyon.
  (9) **Sem bug nenhum:** ela notou o rosto parado, a música demorando a começar e a pele "muito branca, sem
  saturação" no quadro. Regras: **nunca uma imagem parada à vista** (na pausa o vídeo para: os painéis cobrem o
  rosto antes de ela parar e só descobrem com o vídeo andando; confira com `freezedetect` no render final);
  **a música entra quando ela termina a fala** (2,56 s; a batida forte do arquivo em 0,33 s) e a cauda some
  por baixo da pergunta, sem buraco de silêncio; **a cor do vídeo dela nunca muda** (nada de sépia, filtro
  quente, vinheta ou grão nos trechos de perto: eles têm que ficar iguais ao vídeo; grão só no fundo nude).
  Modelo: `projetos/bate-bola/montar_plano.py`, `broll.py` e `abertura.py`. O vídeo veio com música: o áudio
  fica como está, só entram a música da abertura e os efeitos.
- **Vídeo já montado, em vários takes, com luz e enquadramento diferentes** (Caso de paciente, 16/11: "uniformize a
  iluminação e os tons... e o enquadramento"): `scripts/separar_takes.py` corta o original 4K nos cortes do
  `analisar.py` (no quadro exato, passando antes para 30 quadros/s) e o `enquadrar.py` iguala os takes. Opções que
  esse vídeo pediu: `--passar 06` (a foto da paciente que a própria cliente pôs no meio entra como veio),
  `--sem-tripe 01,03,10,11` (câmera andando de propósito atrás dela: o tripé desfaria o movimento),
  `--tamanho mediana` (um take bem mais perto puxaria todos para um zoom forte) e `--cor-pela luz` (só o brilho;
  a 1ª versão usou `--cor-pela pele`, que mexia no balanço de branco, e ela pediu "alterando apenas a iluminação";
  pela parede, três takes na frente da madeira e um com a sala inteira saíam azulados). Confira
  numa grade antes/depois com um quadro de cada take. O vídeo sem ajuste fica em `video-sem-ajuste.mp4`; a voz
  vem do original (`"video_original": "assets/video/original.mov"`). Modelo: `projetos/caso-paciente/montar_plano.py`.
- **Legenda no top escuro dela** quando o colo e a parede são claros (y ≈ 1290 no Caso de paciente); na tela
  dividida o vídeo desce e o rosto dela fica nessa altura: ali a legenda sobe para logo abaixo da emenda (y ≈ 1010).
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
- **Não corte nem reenquadre o vídeo dela.** No Bate-bola ela pediu o vídeo "do jeito que ele tá":
  as trocas de plano aberto/fechado (`enquadramentos`), os trancos e o zoom lento pareceram cortes.
  Deixe um enquadramento só, escala 1, sem `zoom_lento`; o movimento fica nas animações por cima
  (abertura, textos) e nos efeitos que o modelo usa (preto e branco nas reações).
- **Fotos de pacientes são sensíveis:** ficam só no projeto local (`fotos-originais/` e
  `assets/fotos/` estão fora do git) e na página de envio; nunca em artefato publicado.
