import sys, math, numpy as np; sys.path.insert(0,'.')
from PIL import Image, ImageFont, ImageDraw
from render import line
from alt051 import thin
from collections import deque

def raster_g(path, xh=900, pad=70):
    f=ImageFont.truetype(path,100); b=f.getbbox("x")
    px=int(round(100*xh/(b[3]-b[1])))
    im,_=line(path,"g",px,pad=pad)
    return (np.asarray(im)<128).astype(np.uint8), 1000.0/px, im

def counters(m, minsz=400):
    h,w=m.shape; bg=(m==0); seen=np.zeros_like(bg); q=deque()
    for x in range(w):
        for y in (0,h-1):
            if bg[y,x] and not seen[y,x]: seen[y,x]=True; q.append((y,x))
    for y in range(h):
        for x in (0,w-1):
            if bg[y,x] and not seen[y,x]: seen[y,x]=True; q.append((y,x))
    while q:
        y,x=q.popleft()
        for dy,dx in ((1,0),(-1,0),(0,1),(0,-1)):
            ny,nx=y+dy,x+dx
            if 0<=ny<h and 0<=nx<w and bg[ny,nx] and not seen[ny,nx]: seen[ny,nx]=True; q.append((ny,nx))
    hl=bg&~seen; lab=np.zeros(hl.shape,int); out=[]; n=0
    ys,xs=np.nonzero(hl)
    for y,x in zip(ys,xs):
        if lab[y,x]: continue
        n+=1; q=deque([(y,x)]); lab[y,x]=n; cells=[(y,x)]
        while q:
            cy,cx=q.popleft()
            for dy,dx in ((1,0),(-1,0),(0,1),(0,-1)):
                ny,nx=cy+dy,cx+dx
                if 0<=ny<hl.shape[0] and 0<=nx<hl.shape[1] and hl[ny,nx] and not lab[ny,nx]:
                    lab[ny,nx]=n; q.append((ny,nx)); cells.append((ny,nx))
        if len(cells)>minsz: out.append(cells)
    return sorted(out,key=lambda c:min(p[0] for p in c))

def connector(path, xh=900):
    """The skeleton run that lies between the two counters -- the connector."""
    m,u,im = raster_g(path, xh)
    cs = counters(m)
    assert len(cs)>=2, "need two counters"
    bowl, loop = cs[0], cs[1]
    lo = max(y for y,_ in bowl); hi = min(y for y,_ in loop)
    sk = thin(m)
    ys,xs = np.nonzero(sk)
    pts = [(int(y),int(x)) for y,x in zip(ys,xs) if lo <= y <= hi]
    if not pts: return None
    # keep the largest 8-connected run in that band
    S=set(pts); seen=set(); best=[]
    for p in pts:
        if p in seen: continue
        q=deque([p]); seen.add(p); comp=[p]
        while q:
            cy,cx=q.popleft()
            for dy in(-1,0,1):
                for dx in(-1,0,1):
                    n=(cy+dy,cx+dx)
                    if (dy or dx) and n in S and n not in seen:
                        seen.add(n); q.append(n); comp.append(n)
        if len(comp)>len(best): best=comp
    # order it: walk from the endpoint with the fewest neighbours
    B=set(best)
    def nb(p):
        y,x=p
        return [(y+dy,x+dx) for dy in(-1,0,1) for dx in(-1,0,1)
                if (dy or dx) and (y+dy,x+dx) in B]
    ends=[p for p in best if len(nb(p))==1] or [max(best)]
    start=min(ends)
    order=[start]; seen2={start}
    while True:
        nxt=[n for n in nb(order[-1]) if n not in seen2]
        if not nxt: break
        nxt.sort(key=lambda n: (abs(n[0]-order[-1][0])+abs(n[1]-order[-1][1])))
        order.append(nxt[0]); seen2.add(nxt[0])
    return dict(order=order, u=u, im=im, m=m, band=(lo,hi), bowl=bowl, loop=loop)

def curvature(order, smooth=9):
    """Signed turn per sample along a smoothed centreline."""
    P=[(x,y) for y,x in order]
    n=len(P)
    if n<3*smooth: smooth=max(1,n//6)
    S=[]
    for i in range(n):
        a=max(0,i-smooth); b=min(n,i+smooth+1)
        S.append((sum(p[0] for p in P[a:b])/(b-a), sum(p[1] for p in P[a:b])/(b-a)))
    turns=[]
    for i in range(smooth, n-smooth):
        p0,p1,p2 = S[i-smooth], S[i], S[i+smooth]
        v1=(p1[0]-p0[0], p1[1]-p0[1]); v2=(p2[0]-p1[0], p2[1]-p1[1])
        cross=v1[0]*v2[1]-v1[1]*v2[0]
        dot=v1[0]*v2[0]+v1[1]*v2[1]
        turns.append((i, math.degrees(math.atan2(cross,dot))))
    return S, turns

def runs(row):
    out=[]; s=None
    for i,v in enumerate(row):
        if v and s is None: s=i
        elif not v and s is not None: out.append((s,i-1)); s=None
    if s is not None: out.append((s,len(row)-1))
    return out

def neck_connect(path, xh=900):
    """The connector alone, by CONNECTIVITY: start at the row under the bowl
    counter's floor, take the ink run beneath that counter's centre, then step
    down taking the run that OVERLAPS the previous one. Isolates the connector
    and nothing else, by construction (the method the aldine g uses)."""
    m,u,im = raster_g(path, xh)
    cs = counters(m)
    bowl, loop = cs[0], cs[1]
    bcx = sum(x for _,x in bowl)/len(bowl)
    y0 = max(y for y,_ in bowl)+1
    y1 = min(y for y,_ in loop)-1
    cur=None; mids=[]; spans=[]
    for y in range(y0, y1+1):
        rs = runs(m[y])
        if not rs: continue
        if cur is None:
            cand=[r for r in rs if r[0]-2 <= bcx <= r[1]+2] or \
                 [min(rs, key=lambda r: abs((r[0]+r[1])/2 - bcx))]
            cur = cand[0]
        else:
            ov=[r for r in rs if not (r[1] < cur[0] or r[0] > cur[1])]
            if not ov: break
            cur = max(ov, key=lambda r: min(r[1],cur[1])-max(r[0],cur[0]))
        mids.append(((cur[0]+cur[1])/2.0, y)); spans.append(cur[1]-cur[0]+1)
    return dict(mids=mids, spans=spans, u=u, im=im, m=m, y0=y0, y1=y1,
                bowl=bowl, loop=loop)
