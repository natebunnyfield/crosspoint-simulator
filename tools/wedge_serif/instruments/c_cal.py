"""c_cal.py -- the LIVE roman c (outlines.build.draw) measured as word_parts.py measures a font: width, mouth, left side, band/n, terminals. Round 485.

    cd tools/wedge_serif && source build_env.sh && env "${ALBO_ROM_ENV[@]}" ALBO_ROM_C_RX=182 PYTHON_GIL=0 python3 instruments/c_cal.py
"""
import sys, os, numpy as np
sys.path.insert(0, os.getcwd())
from outlines import build
from PIL import Image, ImageDraw
def raster(g):
    polys=[g] if g.geom_type=='Polygon' else list(g.geoms)
    W=900; H=900; im=Image.new('L',(W,H),0); d=ImageDraw.Draw(im); off=100
    for P in polys:
        d.polygon([(x+off, 700-y) for x,y in P.exterior.coords], fill=255)
        for h in P.interiors: d.polygon([(x+off, 700-y) for x,y in h.coords], fill=0)
    return np.array(im)>127
XH=429.0
def meas(ch):
    g=build.draw(ch); m=raster(g); y=700-np.arange(m.shape[0])-0.5
    cols=np.nonzero(m.any(0))[0]; x0,x1=cols[0],cols[-1]+1
    band=(y>=0)&(y<=XH); out=dict(width=x1-x0, band=m[band].sum())
    cx=int(x0+0.80*(x1-x0)); col=m[:,cx]&band; rows=np.nonzero(col)[0]
    if len(rows):
        gaps=np.diff(rows); k=int(np.argmax(gaps)); out['mouth']=int(gaps[k]-1) if gaps[k]>1 else 0
    mid=int(np.argmin(np.abs(y-XH*0.5))); xs=np.nonzero(m[mid])[0]
    run=0
    for i in range(len(xs)):
        if i==0 or xs[i]==xs[i-1]+1: run+=1
        else: break
    out['bowl_left']=run
    # terminals: largest vertical ink run in the right 38% of cols, top/bottom 45% of rows of the band, over the n's stem
    r0=int(x0+0.62*(x1-x0)); sub=m[:, r0:x1]
    def biggest(rows_mask):
        best=0
        for c in range(sub.shape[1]):
            colm=sub[:,c]&rows_mask; r=0; b=0
            for v in colm:
                r=r+1 if v else 0; b=max(b,r)
            best=max(best,b)
        return best
    top=biggest(band&(y>=0.55*XH)); bot=biggest(band&(y<=0.45*XH))
    out['term_top']=top; out['term_bot']=bot
    return out
c=meas('c'); n=meas('n')
stem=n['bowl_left']
print("width %d mouth %d bowl_left %d band/n %.3f top %.2f bot %.2f" % (c['width'], c.get('mouth',-1), c['bowl_left'], c['band']/n['band'], c['term_top']/stem, c['term_bot']/stem))
