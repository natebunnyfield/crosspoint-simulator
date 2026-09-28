"""Visible gap between a fence (bracket) and a letter: render the shaped pair (HarfBuzz, kerned),
and per pixel row inside the letter's band take the white run between the two inks; report
the MINIMUM (closest approach) and the MEAN over the band, in font units."""
import sys, numpy as np, uharfbuzz as hb, freetype
from fontTools.ttLib import TTFont
class G:
    def __init__(s,path,px=1000):
        s.path=path; s.blob=hb.Blob.from_file_path(path); s.face=hb.Face(s.blob); s.font=hb.Font(s.face)
        s.ft=freetype.Face(path); s.upm=s.ft.units_per_EM; s.ft.set_pixel_sizes(0,px); s.k=px/s.upm
        s.tt=TTFont(path); s.cmap=s.tt.getBestCmap()
    def has(s,ch): return ord(ch) in s.cmap
    def masks(s,text):
        buf=hb.Buffer(); buf.add_str(text); buf.guess_segment_properties(); hb.shape(s.font,buf,{"kern":True})
        out=[]; x=0.0
        for inf,pos in zip(buf.glyph_infos,buf.glyph_positions):
            s.ft.load_glyph(inf.codepoint, freetype.FT_LOAD_RENDER|freetype.FT_LOAD_NO_HINTING)
            b=s.ft.glyph.bitmap; a=np.array(b.buffer,np.uint8).reshape(b.rows,b.pitch)[:,:b.width]>127
            out.append((a, x*s.k+s.ft.glyph.bitmap_left, s.ft.glyph.bitmap_top)); x+=pos.x_advance
        return out
    def gap(s,text,y0,y1):
        (a,ax,at),(b,bx,bt)=s.masks(text)
        H=int(1.8*1000); base=1250; Wd=int(max(ax+a.shape[1],bx+b.shape[1]))+900
        ca=np.zeros((H,Wd),bool); cb=np.zeros((H,Wd),bool)
        for m,x,t,c in ((a,ax,at,ca),(b,bx,bt,cb)):
            y=base-t; xi=int(round(x))+450; c[y:y+m.shape[0], xi:xi+m.shape[1]]|=m
        rows=range(base-int(y1*s.k), base-int(y0*s.k))
        g=[]
        for r in rows:
            ra=np.nonzero(ca[r])[0]; rb=np.nonzero(cb[r])[0]
            if len(ra) and len(rb): g.append((rb.min()-ra.max()-1)/s.k)
        return (min(g), float(np.mean(g))) if g else (None,None)
