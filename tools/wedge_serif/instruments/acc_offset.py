"""acc_offset.py -- each accent's centre against its base letter's ink centroid carried along the slant to the
accent's height, units. python3 instruments/acc_offset.py FONT.ttf SLANT_DEG. Round 440 (2026-09-29): the
italics read 37-108 units LEFT before the marks followed the slope, within ~15 after."""
import sys, math, numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import DecomposingRecordingPen
import freetype
path=sys.argv[1]; slant=float(sys.argv[2]); t=math.tan(math.radians(slant))
f=TTFont(path); cm=f.getBestCmap(); gs=f.getGlyphSet(); upm=f['head'].unitsPerEm
face=freetype.Face(path); face.set_char_size(upm*64)  # 1 px = 1 unit
def raster(ch):
    face.load_char(ch, freetype.FT_LOAD_RENDER|freetype.FT_LOAD_NO_HINTING|freetype.FT_LOAD_NO_BITMAP)
    b=face.glyph.bitmap; a=np.array(b.buffer,np.float32).reshape(b.rows,b.pitch)[:, :b.width]/255.
    return a, face.glyph.bitmap_left, face.glyph.bitmap_top
def centroid(a,l,top, ymin=None, ymax=None):
    ys,xs=np.mgrid[0:a.shape[0],0:a.shape[1]]; Y=top-ys; X=xs+l
    m=a.copy()
    if ymin is not None: m[(Y<ymin)|(Y>ymax)]=0
    w=m.sum(); return (X*m).sum()/w, (Y*m).sum()/w
res=[]
for base,acc in [('a','á'),('e','é'),('i','í'),('o','ó'),('u','ú'),('n','ñ'),('c','ç'),('y','ý'),('a','à'),('o','ô'),('u','ü'),('e','ë')]:
    if ord(acc) not in cm: continue
    ab,lb,tb=raster(base); aa,la,ta=raster(acc)
    # mark = accented minus base (same origin): subtract base raster
    H=max(ta,tb)-min(ta-aa.shape[0], tb-ab.shape[0]); 
    bx,by=centroid(ab,lb,tb)
    # accent ink = pixels of accented glyph above base top+2
    top=tb
    mx,my=centroid(aa,la,ta, ymin=top+2, ymax=10000)
    target=bx+t*(my-by)
    res.append((acc, round(mx-target,1)))
print(path.split('/')[-2]+'/'+path.split('/')[-1], ' '.join(f"{a}{d:+.0f}" for a,d in res), ' mean %+.1f'%(sum(d for _,d in res)/len(res)))
