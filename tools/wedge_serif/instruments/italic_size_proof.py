#!/usr/bin/env python3
"""The compact roman-then-italic proof of docs/albo-italic-size-nib-2026-09-26.md: one line per
arm at 14 and 18 pt on the phone (2x), FreeType unhinted, 2 bits, the frozen dark page.
    uv run --python 3.13 --with uharfbuzz --with freetype-py --with numpy --with pillow \
        python instruments/italic_size_proof.py DIR   (DIR holds today/ and opt_c e h m/)
"""
import sys, numpy as np, freetype, uharfbuzz as hb
from PIL import Image, ImageDraw, ImageFont
N=sys.argv[1]
ROM="The rain had stopped."; ITA="Nobody came out to see."
OPTS=[("a  today (round 404)", f"{N}/today/Albo-Italic.ttf"),
      ("c  x-height +5%  (IT_LC_SCALE 1.05)", f"{N}/opt_c/Albo-Italic.ttf"),
      ("e  nib +6%  (ALD_NIB 1.06)", f"{N}/opt_e/Albo-Italic.ttf"),
      ("h  set width +15%  (IT_LC_SETW 1.15)", f"{N}/opt_h/Albo-Italic.ttf"),
      ("m  reference match  (1.015 / 1.15 / nib 0.92)", f"{N}/opt_m/Albo-Italic.ttf")]
ROMF=f"{N}/today/Albo-Regular.ttf"
BG=np.array([0x17,0x1B,0x1B],float); INK=np.array([0xCF,0xD4,0xCC],float)
class S:
    def __init__(s,path,ppem):
        s.f=freetype.Face(path); s.f.set_char_size(int(round(ppem*64)),0,72,72); s.ppem=ppem
        s.h=hb.Font(hb.Face(hb.Blob(open(path,'rb').read()))); s.up=s.h.face.upem; s.h.scale=(s.up,s.up)
    def run(s,text,out,x,base):
        buf=hb.Buffer(); buf.add_str(text); buf.guess_segment_properties(); hb.shape(s.h,buf,{"kern":True,"liga":True})
        k=s.ppem/s.up
        for i,p in zip(buf.glyph_infos,buf.glyph_positions):
            s.f.load_glyph(i.codepoint, freetype.FT_LOAD_RENDER|freetype.FT_LOAD_NO_HINTING); b=s.f.glyph.bitmap
            if b.rows and b.width:
                a=np.frombuffer(bytes(b.buffer),np.uint8).reshape(b.rows,abs(b.pitch))[:,:b.width]
                x0=int(round(x+p.x_offset*k))+s.f.glyph.bitmap_left; y0=base-s.f.glyph.bitmap_top
                reg=out[y0:y0+a.shape[0], x0:x0+a.shape[1]]; np.maximum(reg,a[:reg.shape[0],:reg.shape[1]],out=reg)
            x+=p.x_advance*k
        return x
UI=ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf",22)
blocks=[]
for pt in (14,18):
    ppem=pt*300/72
    lh=int(ppem*1.25); labh=30
    W=1560
    rows=[]
    for lab,it in OPTS:
        cov=np.zeros((lh,W),np.uint8); base=int(ppem*0.95)
        x=S(ROMF,ppem).run(ROM+" ",cov,16,base); S(it,ppem).run(ITA,cov,x,base)
        q=np.round(cov/255*3)/3   # the converter's 2 bits
        rgb=(BG+(INK-BG)*q[...,None]).clip(0,255).astype(np.uint8)
        im=Image.new("RGB",(W,lh+labh),tuple(BG.astype(int))); d=ImageDraw.Draw(im)
        d.text((16,labh-6),lab,font=UI,fill=(150,156,150),anchor="ls"); im.paste(Image.fromarray(rgb),(0,labh)); rows.append(im)
    head=Image.new("RGB",(W,40),(40,46,46)); ImageDraw.Draw(head).text((16,28),f"{pt} pt  ({ppem:.1f} ppem, the phone's 2x)  unhinted, 2-bit",font=UI,fill=(220,224,218),anchor="ls")
    blocks.append([head]+rows)
Wm=max(r.width for b in blocks for r in b); H=sum(r.height for b in blocks for r in b)
out=Image.new("RGB",(Wm,H),tuple(BG.astype(int))); y=0
for b in blocks:
    for r in b: out.paste(r,(0,y)); y+=r.height
out.save(f"{N}/italic-size-nib.png",optimize=True); print(out.size)
