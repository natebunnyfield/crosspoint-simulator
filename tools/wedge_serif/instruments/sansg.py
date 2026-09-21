import sys, math, numpy as np; sys.path.insert(0,'.')
from PIL import Image, ImageFont, ImageDraw
from collections import deque
def raster(path, ch, xh_px=520, pad=90, index=0):
    f0=ImageFont.truetype(path,100,index=index); b=f0.getbbox("x")
    if b[3]-b[1]<=0: return None,None,None
    px=int(round(100*xh_px/(b[3]-b[1])))
    f=ImageFont.truetype(path,px,index=index)
    a,d=f.getmetrics()
    W=int(f.getlength(ch))+2*pad; H=a+d+2*pad
    im=Image.new("L",(W,H),255); dr=ImageDraw.Draw(im)
    base=pad+a
    dr.text((pad,base),ch,font=f,fill=0,anchor="ls")
    return (np.asarray(im)<128), base, 1000.0/px
def holes(m,minsz=150):
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
def measure(path, index=0):
    m,base,u = raster(path,"g",index=index)
    if m is None: return None
    hs = holes(m)
    ys,xs = np.nonzero(m)
    top, bot = ys.min(), ys.max()
    depth = (bot-base)*u                       # below the baseline
    xh    = (base-top)*u
    res = dict(counters=len(hs), depth=depth, xh=xh, dep_xh=depth/xh if xh else 0)
    if hs:
        c=hs[0]; cy=[p[0] for p in c]; cx=[p[1] for p in c]
        res["bowl_w"]=(max(cx)-min(cx))*u; res["bowl_h"]=(max(cy)-min(cy))*u
        res["bowl_ratio"]=res["bowl_w"]/res["bowl_h"] if res["bowl_h"] else 0
        # the tail's horizontal reach: ink below the baseline, left and right of the bowl centre
        bcx=sum(cx)/len(cx)
        below=[(y,x) for y,x in zip(ys,xs) if y>base+2]
        if below:
            res["tail_left"]=(bcx-min(x for _,x in below))*u
            res["tail_right"]=(max(x for _,x in below)-bcx)*u
            # where the ink sits at the deepest row
            deep=[x for y,x in below if y>bot-max(3,int(0.06*(bot-base)))]
            res["tip_x"]=((sum(deep)/len(deep))-bcx)*u if deep else 0
    return res
