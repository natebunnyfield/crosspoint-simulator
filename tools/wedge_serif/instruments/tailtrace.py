import sys, math, numpy as np; sys.path.insert(0,'.')
from PIL import Image, ImageFont, ImageDraw
from collections import deque
from alt051 import thin
from sansg import raster, holes

def tail_trace(path, index=0, xh_px=620):
    """The g's descender centreline: skeletonise, keep the skeleton at or below
    the baseline, order it from the pixel nearest the bowl down to the tip."""
    m, base, u = raster(path, "g", xh_px=xh_px, index=index)
    if m is None: return None
    hs = holes(m)
    if not hs: return None
    c = hs[0]; bcx = sum(x for _,x in c)/len(c); bcy = sum(y for y,_ in c)/len(c)
    sk = thin(m.astype(np.uint8))
    ys, xs = np.nonzero(sk)
    P = {(int(y),int(x)) for y,x in zip(ys,xs) if y >= base-2}
    if len(P) < 12: return None
    def nb(p):
        y,x=p
        return [(y+dy,x+dx) for dy in(-1,0,1) for dx in(-1,0,1)
                if (dy or dx) and (y+dy,x+dx) in P]
    # largest connected run
    seen=set(); best=[]
    for p in P:
        if p in seen: continue
        q=deque([p]); seen.add(p); comp=[p]
        while q:
            cur=q.popleft()
            for n in nb(cur):
                if n not in seen: seen.add(n); q.append(n); comp.append(n)
        if len(comp)>len(best): best=comp
    B=set(best)
    def nb2(p):
        y,x=p
        return [(y+dy,x+dx) for dy in(-1,0,1) for dx in(-1,0,1)
                if (dy or dx) and (y+dy,x+dx) in B]
    ends=[p for p in best if len(nb2(p))==1]
    start = min(ends, key=lambda p: p[0]) if ends else min(best, key=lambda p: p[0])
    order=[start]; seen2={start}
    while True:
        nxt=[n for n in nb2(order[-1]) if n not in seen2]
        if not nxt: break
        nxt.sort(key=lambda n: abs(n[0]-order[-1][0])+abs(n[1]-order[-1][1]))
        order.append(nxt[0]); seen2.add(nxt[0])
    pts=[(((x-bcx)*u), ((base-y)*u)) for y,x in order]   # Albo units, +y up, origin bowl centre-x / baseline
    return dict(pts=pts, u=u, base=base, bcx=bcx, m=m, order=order)

def summarise(pts):
    if len(pts)<6: return None
    ys=[p[1] for p in pts]; xs=[p[0] for p in pts]
    lo=min(range(len(pts)), key=lambda i: ys[i])          # deepest
    rise=ys[-1]-ys[lo]                                     # how far it comes back UP
    return dict(depth=-ys[lo], tip=(xs[-1],ys[-1]), deep_x=xs[lo],
                rise=rise, leftmost=min(xs), after=len(pts)-lo)
