# Créditos da música

A abertura do quadro usa 3,85 s de "Movement Proposition", de Kevin MacLeod (incompetech.com),
licença Creative Commons Atribuição 4.0 (CC BY 4.0), a partir de 10,9 s da faixa
(`assets/sfx/musica-abertura.mp3`, fora do git; refaça com
`ffmpeg -ss 10.90 -t 3.85 -i "Movement Proposition.mp3" -af "volume='if(lt(t,2.05),0.2,if(lt(t,2.25),0.2+(t-2.05)*3.0,0.8))':eval=frame,afade=t=in:d=0.02,afade=t=out:st=3.45:d=0.4" musica-abertura.mp3`).
A música fica baixa enquanto ela diz o título e sobe na pausa. O resto do vídeo já veio com a música dele, que fica como está.

Ao publicar, inclua na legenda do post:
Música da abertura: "Movement Proposition" – Kevin MacLeod (incompetech.com), CC BY 4.0
