"""Limpa a máscara do recorte (remove-background) e monta PNGs RGBA com as cores originais.

Uso:
    python3 clean_matte.py <pasta_rgb> <pasta_alpha> <pasta_saida> <fps> <t_entrada>

- zera a máscara antes de t_entrada (a pessoa ainda não entrou; o modelo pegava a almofada branca)
- depois disso mantém só o maior componente conectado (a pessoa)
- usa o RGB do vídeo original para o recorte casar 100% com o fundo

Depois: ffmpeg -framerate 30 -i <saida>/f_%04d.png -c:v libvpx-vp9 -pix_fmt yuva420p -crf 14 -b:v 0 hook-cutout.webm
"""
import sys, glob, os, numpy as np
from PIL import Image
from scipy import ndimage
rgb_dir, a_dir, out_dir, fps, t_enter = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4]), float(sys.argv[5])
rgbs=sorted(glob.glob(rgb_dir+'/*.png')); als=sorted(glob.glob(a_dir+'/*.png'))
assert len(rgbs)==len(als), (len(rgbs),len(als))
for i,(r,a) in enumerate(zip(rgbs,als)):
    t=i/fps
    A=np.array(Image.open(a).convert('L')).astype(np.float32)
    if t < t_enter:
        A[:]=0
    else:
        lab,n=ndimage.label(A>40)
        if n>1:
            sizes=ndimage.sum(np.ones_like(A),lab,range(1,n+1))
            keep=np.argmax(sizes)+1
            mask=ndimage.binary_dilation(lab==keep,iterations=6)
            A=A*mask
    R=np.array(Image.open(r).convert('RGB'))
    out=np.dstack([R,A.clip(0,255).astype(np.uint8)])
    Image.fromarray(out,'RGBA').save(os.path.join(out_dir,f'f_{i:04d}.png'))
print('ok',len(rgbs))
