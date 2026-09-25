"""ROUND 387 (2026-09-25): the eth measured unsheared at x-height 429 --
top, bowl width, where the tip sits, and the ink runs at x-height multiples.
Run bare to measure the five reference italics in ../refs; import `meas(ttf,
slant)` to measure a built Albo (slant 13 for the italics, 0 for the romans).
Decided the redrawn eth in docs/albo-round-387-2026-09-25.md."""
import sys, math, numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import DecomposingRecordingPen
from shapely.geometry import Polygon
from fontTools.pens.basePen import BasePen
class P(BasePen):
    def __init__(s,gs): super().__init__(gs); s.c=[]; s.cur=[]
    def _moveTo(s,p): s.cur=[p]
    def _lineTo(s,p): s.cur.append(p)
    def _curveToOne(s,a,b,c):
        p0=s.cur[-1]
        for t in np.linspace(0,1,12)[1:]:
            s.cur.append(tuple((1-t)**3*np.array(p0)+3*(1-t)**2*t*np.array(a)+3*(1-t)*t*t*np.array(b)+t**3*np.array(c)))
    def _qCurveToOne(s,a,b):
        p0=s.cur[-1]
        for t in np.linspace(0,1,10)[1:]:
            s.cur.append(tuple((1-t)**2*np.array(p0)+2*(1-t)*t*np.array(a)+t*t*np.array(b)))
    def _closePath(s): s.c.append(s.cur); s.cur=[]
    _endPath=_closePath
def glyph_poly(f, ch, slant):
    t=TTFont(f); gs=t.getGlyphSet(); name=t.getBestCmap()[ord(ch)]
    p=P(gs); gs[name].draw(p)
    k=math.tan(math.radians(slant))
    from shapely.ops import unary_union
    polys=[Polygon([(x-k*y,y) for x,y in c]).buffer(0) for c in p.c if len(c)>2]
    # even-odd via symmetric difference
    g=polys[0]
    for q in polys[1:]: g=g.symmetric_difference(q)
    upm=t['head'].unitsPerEm; xh=t['OS/2'].sxHeight or 0
    return g, upm, xh
def meas(f, slant, ch='ð'):
    g, upm, xh = glyph_poly(f, ch, slant)
    o,_,_ = glyph_poly(f,'o',slant)
    if not xh: xh=o.bounds[3]
    x0,y0,x1,y1=g.bounds; ox0,oy0,ox1,oy1=o.bounds
    s=429.0/xh
    # top region: rows above bowl top (oy1)
    from shapely.geometry import box
    res=dict(top=y1*s, bowlw=(ox1-ox0)*s, ethw=(x1-x0)*s)
    # tip: leftmost x of ink above 0.9 of top height, relative to bowl left, in bowl widths
    band=g.intersection(box(-1e4, y1-(y1-oy1)*0.12, 1e4, y1+1))
    res['tip_left']=(band.bounds[0]-x0)/(x1-x0); res['tip_right']=(band.bounds[2]-x0)/(x1-x0)
    # rows: runs at several heights
    rows={}
    for fr in (0.55,0.7,0.85,1.0,1.15,1.3,1.45,1.6):
        yy=fr*xh
        if yy>y1: continue
        ln=g.intersection(box(-1e4,yy-0.5,1e4,yy+0.5))
        geoms=getattr(ln,'geoms',[ln])
        rows[fr]=[(round((q.bounds[0]-x0)*s),round((q.bounds[2]-x0)*s)) for q in sorted(geoms,key=lambda q:q.bounds[0]) if not q.is_empty]
    res['rows']=rows
    return res
if __name__=='__main__':
    R=sys.argv[1]
    for n,fn,sl in [('Flanker','flanker-griffo-italic.otf',11.7),('FlankerBI','flanker-griffo-bold-italic.otf',11.7),('Pagella','texgyrepagella-italic.otf',11.7),('Poetica','poetica-std-regular.otf',9.2),('Coelacanth','coelacanth-italic.otf',14.5)]:
        r=meas(R+'/'+fn,sl); print(n, {k:(round(v,2) if isinstance(v,float) else v) for k,v in r.items() if k!='rows'})
        for k,v in r['rows'].items(): print('   xh*%.2f'%k, v)
