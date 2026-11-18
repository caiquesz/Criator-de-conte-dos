"""Gera assets/fonts/FreeSans-LightRef.ttf: a FreeSans (o clone livre da Helvetica do GNU FreeFont) afinada até o peso
da Helvetica Neue Light das legendas da referência.

Uso: /usr/bin/python3.12 fonte_legenda.py   (precisa do python3-fontforge do apt, que só existe para o Python 3.12,
     e da FreeSans do apt, fonts-freefont-ttf)

4ª versão, 18/11: a cliente não gostou da fonte das legendas normais (Roboto 300): "não achei que tá igual da
referência". O peso já era o mesmo (traço de 3,2 px na referência e na Roboto); o que muda é o desenho: a Roboto tem
as letras redondas mais estreitas e outro "a", "e", "g" e "t". A FreeSans tem o desenho da Helvetica, mas é a Regular
(traço de 5,3 px). Afinada em 30 unidades (de 1000) com a largura de cada letra mantida (contraformas "squish"), o
traço fica em 3,3 px e as letras continuam largas. Na legenda: 56 px e −0,012em (altura-x de 31 px e "precisa de
complemento" com 570 px, contra 30 e 573 na referência). Comparação no scratchpad (fontes-leg/cmp5.png). Licença: GPLv3 com exceção de fonte, como a
FreeSans (assets/fonts/LICENSE-FreeFont.txt).
"""
import subprocess
from pathlib import Path

import fontforge

AQUI = Path(__file__).parent
ORIGEM = "/usr/share/fonts/truetype/freefont/FreeSans.ttf"
AFINAR = -30
DESTINO = AQUI / "assets" / "fonts" / "FreeSans-LightRef.ttf"


def main():
    f = fontforge.open(ORIGEM)
    f.selection.none()
    for g in f.glyphs():
        if 0x20 <= g.unicode <= 0x24F or 0x2000 <= g.unicode <= 0x206F:
            f.selection.select(("more",), g.glyphname)
    f.changeWeight(AFINAR, "LCG", 0, 0, "squish")
    f.fontname, f.familyname, f.fullname = "FreeSans-LightRef", "FreeSans Light Ref", "FreeSans Light Ref"
    tmp = DESTINO.with_suffix(".tmp.ttf")
    f.generate(str(tmp))
    # só o latino (a fonte inteira tem 1,5 MB)
    subprocess.run(["pyftsubset", str(tmp), "--unicodes=U+0020-024F,U+2000-206F", f"--output-file={DESTINO}"], check=True)
    tmp.unlink()
    print(f"ok: {DESTINO} ({DESTINO.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
