"""word_rows.py -- labeled rows of text from several fonts at one x-height (the compact options image).

    python3 instruments/word_rows.py out.png 90 "A  today::Albo-BoldItalic.ttf::ocecoa" "D1::other.ttf::ocecoa"

The owner rules fastest from ONE small labeled image with today on top (memory: compact option images).
"""
import sys, freetype, numpy as np
from PIL import Image, ImageDraw, ImageFont
F=ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc",26)
XHPX=int(sys.argv[2]); out=sys.argv[1]; specs=sys.argv[3:]
rows=[]
for spec in specs:
    lab, path, text = spec.split("::")
    f=freetype.Face(path); f.set_pixel_sizes(0,200); f.load_char('x', freetype.FT_LOAD_NO_HINTING); xh=f.glyph.metrics.height/64
    size=int(200*XHPX/xh); f.set_pixel_sizes(0,size)
    H=int(XHPX*2.0); base=int(XHPX*1.55); W=260+int(size*0.75*len(text))+40
    im=Image.new("L",(W,H),250); d=ImageDraw.Draw(im); d.text((14,base-XHPX//2-16),lab,fill=40,font=F)
    x=260; prev=None
    for ch in text:
        gi=f.get_char_index(ch)
        if prev is not None:
            k=f.get_kerning(prev, gi); x+=k.x//64
        f.load_char(ch, freetype.FT_LOAD_RENDER|freetype.FT_LOAD_NO_HINTING); b=f.glyph.bitmap
        if b.rows:
            a=np.array(b.buffer,np.uint8).reshape(b.rows,b.pitch)[:, :b.width]
            im.paste(Image.fromarray(255-a),(x+f.glyph.bitmap_left,base-f.glyph.bitmap_top),Image.fromarray(a))
        x+=f.glyph.advance.x//64; prev=gi
    rows.append(im.crop((0,0,min(W,x+40),H)))
W=max(r.width for r in rows); out_im=Image.new("L",(W,sum(r.height for r in rows)),250); y=0
for r in rows: out_im.paste(r,(0,y)); y+=r.height
out_im.save(out); print(out, out_im.size)
