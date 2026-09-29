"""reading_rows.py -- a word at the reader's sizes and levels (unhinted, 2-bit), per arm, magnified NEAREST.

    python3 instruments/reading_rows.py BASE_DIR arm1 arm2 ...      (arms are dirs under BASE_DIR holding Albo-*.ttf)
    env: TEXT (default "once, cocoa, ice"), CUTS (default "BoldItalic"; comma list)

Rows per arm per cut: 10 pt X3 x5 | 12 pt X3 x4 | 8 pt phone x3 | 10 pt phone x3. Writes BASE_DIR/csmall.png.
"""
import os
import sys, os, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fit_audit"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from legib import Renderer
from PIL import Image, ImageDraw, ImageFont
import poor_proof as P
S=sys.argv[1]; arms=sys.argv[2:]
LAB=ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc",20); PAPER=tuple(int(v) for v in P.PAPER)
parts=[]
for a in arms:
  for cut in os.environ.get("CUTS","BoldItalic").split(","):
    row=[]
    for ppem,mag in ((150/72*10,5),(150/72*12,4),(150/72*8*2,3),(150/72*10*2,3)):
        R=Renderer(f"{S}/{a}/Albo-{cut}.ttf",0,ppem)
        c=np.zeros((int(ppem*1.4),int(ppem*8)),np.uint8); R.line(os.environ.get("TEXT","once, cocoa, ice"),c,6,int(ppem*1.05))
        xs=np.nonzero(c.any(0))[0]; c=c[:,:xs[-1]+6]
        row.append(P.rgb(np.kron(c,np.ones((mag,mag),np.uint8)))); row.append(np.full((row[-1].shape[0],20,3),PAPER,np.uint8))
    H=max(r.shape[0] for r in row); row=[np.concatenate([r,np.full((H-r.shape[0],r.shape[1],3),PAPER,np.uint8)],0) for r in row]
    img=np.concatenate(row,1); h=Image.new("RGB",(img.shape[1],28),PAPER); ImageDraw.Draw(h).text((6,4),f"{a} {cut}   (10pt X3 x5 | 12pt X3 x4 | 8pt phone x3 | 10pt phone x3)",fill=(30,30,30),font=LAB)
    parts+= [np.array(h), img]
W=max(p.shape[1] for p in parts)
out=np.concatenate([np.concatenate([p,np.full((p.shape[0],W-p.shape[1],3),PAPER,np.uint8)],1) for p in parts],0)
Image.fromarray(out).save(f"{S}/csmall.png"); print(out.shape)
