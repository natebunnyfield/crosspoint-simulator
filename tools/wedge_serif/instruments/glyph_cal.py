"""glyph_cal.py -- the LIVE builder's letter measured as word_parts.py / thin_measure.py measure a font (1 px = 1 unit, 429 x-height).

    cd tools/wedge_serif && source build_env.sh && env "${ALBO_ROM_ENV[@]}" ALBO_O_FLOOR=0.40 PYTHON_GIL=0 python3 instruments/glyph_cal.py o

Prints, per letter: ink width, advance-free band ink over the n's, and the letter's own parts --
o: top/bottom thins and sides over the n stem; a: hood, bowl-top hairline, bowl-left over the stem,
width; f: hook overhang and bar's right end past the stem's right edge, in units; c: as c_cal.py.
Round 486 (the a, o and f; 2026-10-09)."""
import sys, os, numpy as np
sys.path.insert(0, os.getcwd())
from outlines import build
from PIL import Image, ImageDraw
XH=429.0
def raster(g, off=150):
    polys=[g] if g.geom_type=='Polygon' else list(g.geoms)
    im=Image.new('L',(1100,1100),0); d=ImageDraw.Draw(im)
    for P in polys:
        d.polygon([(x+off, 750-y) for x,y in P.exterior.coords], fill=255)
        for h in P.interiors: d.polygon([(x+off, 750-y) for x,y in h.coords], fill=0)
    return np.array(im)>127
def runs(col):
    xs=np.nonzero(col)[0]; out=[]
    if not len(xs): return out
    s=xs[0]
    for k in range(1,len(xs)):
        if xs[k]!=xs[k-1]+1: out.append((s,xs[k-1])); s=xs[k]
    out.append((s,xs[-1])); return out
def rl(r): return r[1]-r[0]+1
n=raster(build.draw('n')); y=750-np.arange(n.shape[0])-0.5; band=(y>=0)&(y<=XH)
mid=int(np.argmin(np.abs(y-XH*0.5))); stem=rl(runs(n[mid])[0]); nband=n[band].sum()
for ch in sys.argv[1:]:
    m=raster(build.draw(ch)); cols=np.nonzero(m.any(0))[0]; x0,x1=cols[0],cols[-1]+1
    out="%s: width %d band/n %.3f" % (ch, x1-x0, m[band].sum()/nband)
    if ch=='o':
        cx=(x0+x1)//2; rr=runs(m[:,cx]); rs=runs(m[mid])
        out+=" | top %.2f bot %.2f sides %.2f" % (rl(rr[0])/stem, rl(rr[-1])/stem, rl(rs[0])/stem)
    if ch=='a':
        c55=int(x0+0.55*(x1-x0)); rr=runs(m[:,c55]); r30=int(np.argmin(np.abs(y-XH*0.3))); rs=runs(m[r30])
        out+=" | hood %.2f bowl-top %.2f bowl-left %.2f" % (rl(rr[0])/stem, (rl(rr[1])/stem if len(rr)>1 else -1), rl(rs[0])/stem)
    if ch=='f':
        sr=runs(m[mid])[0]; stem_right=sr[1]+1
        above=y>XH*1.05; ca=np.nonzero(m[above].any(0))[0]; barrows=band&(y>=0.80*XH); cb=np.nonzero(m[barrows].any(0))[0]
        out+=" | hook right of stem %d, bar right of stem %d" % (ca[-1]+1-stem_right, cb[-1]+1-stem_right)
    print(out)
