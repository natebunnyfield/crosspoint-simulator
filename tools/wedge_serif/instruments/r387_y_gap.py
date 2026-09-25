"""ROUND 387 (2026-09-25): the Y's join gap, unsheared -- horizontal ink runs
and the white between them at 0.30-0.50 cap, and the nearest approach between
the arm island and the spine. `python3 r387_y_gap.py A.ttf [B.ttf ...]`.
Decided ALBO_ALD_Y_GAP_BOLD = 0.040 (docs/albo-round-387-2026-09-25.md)."""
import sys
import r387_eth_measure as ethmeas
from shapely.geometry import box
def gap(f, ch='Y', slant=13, lo=0.30, hi=0.50, step=0.01):
    g,upm,xh = ethmeas.glyph_poly(f, ch, slant)
    cap = 674.0
    out=[]
    y=lo
    while y<=hi+1e-9:
        ln=g.intersection(box(-1e4,y*cap-0.25,1e4,y*cap+0.25))
        gs=sorted([q for q in getattr(ln,'geoms',[ln]) if not q.is_empty], key=lambda q:q.bounds[0])
        runs=[(round(q.bounds[0]),round(q.bounds[2])) for q in gs]
        whites=[round(gs[i+1].bounds[0]-gs[i].bounds[2],1) for i in range(len(gs)-1)]
        out.append((round(y,2),runs,whites)); y+=step
    return out
if __name__=='__main__':
    for f in sys.argv[1:]:
        g,_,_=ethmeas.glyph_poly(f,'Y',13)
        print(f, 'islands', len(getattr(g,'geoms',[g])))
        for r in gap(f): print('  ',r)
        # nearest approach between islands
        gs=list(getattr(g,'geoms',[g]))
        if len(gs)>1:
            gs.sort(key=lambda q:-q.area); print('   nearest', round(gs[0].distance(gs[1]),2))
