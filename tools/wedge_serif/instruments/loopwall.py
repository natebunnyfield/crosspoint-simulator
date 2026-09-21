import sys, math, numpy as np; sys.path.insert(0,'.')
from PIL import ImageFont
from render import line
from collections import deque
def mask(p, xh=520):
    f=ImageFont.truetype(p,100); b=f.getbbox("x")
    px=int(round(100*xh/(b[3]-b[1])))
    im,_=line(p,"g",px,pad=60)
    return (np.asarray(im)<128), 1000.0/px
def holes(m,minsz=200):
    h,w=m.shape; bg=~m; seen=np.zeros_like(bg); q=deque()
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
def wall_by_angle(path, step=15):
    m,u=mask(path); hs=holes(m)
    if len(hs)<2: return None,None
    loop=hs[1]                                   # lower counter
    cy=sum(y for y,_ in loop)/len(loop); cx=sum(x for _,x in loop)/len(loop)
    H,W=m.shape; out={}
    for deg in range(0,360,step):
        a=math.radians(deg); dx,dy=math.cos(a),-math.sin(a)   # screen y is down
        # walk out of the counter to the first ink, then measure the run
        r=0.0
        while r<max(H,W):
            x,y=int(round(cx+dx*r)), int(round(cy+dy*r))
            if not (0<=x<W and 0<=y<H): break
            if m[y,x]: break
            r+=0.5
        t=0.0
        while r+t<max(H,W):
            x,y=int(round(cx+dx*(r+t))), int(round(cy+dy*(r+t)))
            if not (0<=x<W and 0<=y<H) or not m[y,x]: break
            t+=0.5
        out[deg]=t*u
    return out,u
