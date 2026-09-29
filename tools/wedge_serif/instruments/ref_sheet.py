"""ref_sheet.py -- one glyph from several fonts at ONE x-height (260 px), baseline and x-line drawn.

    python3 instruments/ref_sheet.py out.png "refs/poetica-std-regular.otf::Poetica" "Albo-BoldItalic.ttf::Albo BI" ...

The picture that diagnosed the italic c (round 433): every reference c has a round crown arching
over with the terminal hanging off it; Albo's was a ramp ending in a horn. Look at ALL the references
side by side before tuning a dial on one letter. Edit the "c" in load_char for another glyph.
"""
import sys, freetype, numpy as np
from PIL import Image, ImageDraw, ImageFont
F=ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc",15)
out_path=sys.argv[1]; items=sys.argv[2:]; cells=[]
for it in items:
    p,lab=it.split("::")
    f=freetype.Face(p)
    f.set_pixel_sizes(0,200); f.load_char('x', freetype.FT_LOAD_NO_HINTING); xh=f.glyph.metrics.height/64
    f.set_pixel_sizes(0,int(200*260/xh))
    f.load_char("c", freetype.FT_LOAD_RENDER|freetype.FT_LOAD_NO_HINTING); b=f.glyph.bitmap
    a=np.array(b.buffer,np.uint8).reshape(b.rows,b.pitch)[:, :b.width]
    top=f.glyph.bitmap_top
    im=Image.new("L",(300,380),250); d=ImageDraw.Draw(im)
    base=320; d.line([(0,base),(300,base)],fill=200); d.line([(0,base-260),(300,base-260)],fill=200)
    im.paste(Image.fromarray(255-a),(30+f.glyph.bitmap_left,base-top),Image.fromarray(a))
    d.text((4,4),lab,fill=0,font=F); cells.append(im)
cols=5; rows=(len(cells)+cols-1)//cols
out=Image.new("L",(300*cols,380*rows),250)
for i,c in enumerate(cells): out.paste(c,((i%cols)*300,(i//cols)*380))
out.save(out_path); print(out.size)
