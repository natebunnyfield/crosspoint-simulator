#!/usr/bin/env python3
"""Set width split into INK (mid x-height row extent) and WHITE (advance - ink), italic/roman,
for the references and one Albo pair (2026-09-26, docs/albo-italic-size-nib-2026-09-26.md).
    uv run --python 3.13 --with uharfbuzz --with freetype-py --with fonttools --with numpy \
        python instruments/italic_ink_white.py ROMAN.ttf ITALIC.ttf
"""
import os
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from italic_size_nib import REFS, F, TEXT
import numpy as np, freetype, statistics as st
def iw(spec):
    f=F(spec); xh=f.top('x'); ink=0; n=0
    for ch in TEXT:
        if not ch.isalpha() or not ch.islower(): continue
        a,l,t=f.raster(ch); r=t-int(xh*0.5)
        row=np.nonzero(a[r]>0.5)[0] if 0<=r<a.shape[0] else []
        if len(row): ink+=row[-1]-row[0]+1; n+=1
    adv=sum(f.shape_len(c) for c in TEXT if c.isalpha() and c.islower())
    return ink/n, (adv-ink)/n, adv/n
if __name__=="__main__":
  rows=REFS+[('Albo',(sys.argv[1],0),(sys.argv[2],0))]
  print('face            ink-mid  white   adv  (italic/roman)')
  for nm,r,i in rows:
    R=iw(r); I=iw(i); print(f'{nm:15s}', ' '.join(f'{I[k]/R[k]:.3f}' for k in range(3)), f'   R white/adv {R[1]/R[2]:.2f} I {I[1]/I[2]:.2f}')
