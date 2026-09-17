"""The binocular g's LOWER LOOP: does its stroke taper the way a brush does?

Owner 2026-09-16, with a fresh scan crop: *"compare scan to italic g. does the
bottom loop taper as a brush stroke would?"*

HOW IT MEASURES. The loop's counter is found as the lower of the two enclosed
white regions, and from that counter's centroid a ray is walked outward at every
5 degrees: the ink run it crosses IS the stroke's width there. Widths are
normalised by the counter's own mean radius, so a photograph of a printed page
and a rendered outline are directly comparable.

THE ONE SECTOR THAT MUST BE EXCLUDED is 70-120 degrees, where the NECK crosses
the ring -- a ray there leaves through the neck rather than through the loop's
own wall and reports the two strokes as one. Left in, the scan reads 1.02 at 80
degrees and 0.24 at 100, a jump that is not in the letter.

WHAT THE TWO NUMBERS MEAN. `contrast` is thickest/thinnest round the ring, which
says how much the stroke tapers at all. `change` is the mean absolute step in
width per 5 degrees x100, which says how GRADUAL it is -- a brush taper changes
smoothly and continuously, a compass-drawn ring hardly changes. A high contrast
with a low change is a stroke thick on one side and thin on the other that never
tapers between them.
"""
import sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont

def otsu(a):
    h=np.bincount(a.ravel(),minlength=256).astype(float); t=h.sum()
    w=np.cumsum(h); m=np.cumsum(h*np.arange(256))
    with np.errstate(invalid='ignore',divide='ignore'):
        b=(m[-1]*w/t-m)**2/(w*(t-w))
    b[~np.isfinite(b)]=-1; return int(np.argmax(b))

def comps(mask):
    seen=np.zeros(mask.shape,bool); out=[]; H,W=mask.shape
    for sy in range(H):
        for sx in range(W):
            if not mask[sy,sx] or seen[sy,sx]: continue
            st=[(sy,sx)]; seen[sy,sx]=True; pix=[]
            while st:
                y,x=st.pop(); pix.append((y,x))
                for dy,dx in ((1,0),(-1,0),(0,1),(0,-1)):
                    ny,nx=y+dy,x+dx
                    if 0<=ny<H and 0<=nx<W and mask[ny,nx] and not seen[ny,nx]:
                        seen[ny,nx]=True; st.append((ny,nx))
            out.append(pix)
    out.sort(key=len,reverse=True); return out

def ink_from_scan(path):
    im=Image.open(path).convert("L")
    a=np.asarray(im)
    return a<otsu(a)

def ink_from_font(ttf, px=900):
    from fontTools.ttLib import TTFont
    f=TTFont(ttf); upm=f["head"].unitsPerEm
    try: sx=f["OS/2"].sxHeight or upm*0.5
    except Exception: sx=upm*0.5
    ang=-getattr(f["post"],"italicAngle",0.0)
    size=int(round(px*upm/sx)); W=H=size*3
    im=Image.new("L",(W,H),255)
    ImageDraw.Draw(im).text((W*0.35,H*0.62),"g",font=ImageFont.truetype(ttf,size),fill=0,anchor="ls")
    base=H*0.62
    if abs(ang)>0.05:
        k=math.tan(math.radians(ang))
        im=im.transform((W,H),Image.AFFINE,(1,k,-k*base,0,1,0),resample=Image.BICUBIC,fillcolor=255)
    a=np.asarray(im); return a<128

def loop_widths(mask, label, nang=72):
    ys,xs=np.nonzero(mask)
    sub=mask[ys.min():ys.max()+1, xs.min():xs.max()+1]
    H,W=sub.shape
    white=~sub
    bg=np.zeros_like(white); st=[]
    for x in range(W):
        for y in (0,H-1):
            if white[y,x] and not bg[y,x]: bg[y,x]=True; st.append((y,x))
    for y in range(H):
        for x in (0,W-1):
            if white[y,x] and not bg[y,x]: bg[y,x]=True; st.append((y,x))
    while st:
        y,x=st.pop()
        for dy,dx in ((1,0),(-1,0),(0,1),(0,-1)):
            ny,nx=y+dy,x+dx
            if 0<=ny<H and 0<=nx<W and white[ny,nx] and not bg[ny,nx]:
                bg[ny,nx]=True; st.append((ny,nx))
    holes=[h for h in comps(white&~bg) if len(h)>(min(H,W)*0.04)**2]
    if len(holes)<2: print(f"{label}: found {len(holes)} counters"); return None
    boxes=[]
    for h in holes[:2]:
        hy=np.array([p[0] for p in h]); hx=np.array([p[1] for p in h])
        boxes.append((hy.mean(),hx.mean(),hy.min(),hy.max(),hx.min(),hx.max()))
    boxes.sort()                      # topmost first = the bowl
    cy,cx = boxes[1][0], boxes[1][1]  # the LOOP's counter centroid
    # ring outward from the centroid; width = ink run along the ray
    out=[]
    for i in range(nang):
        th=2*math.pi*i/nang
        dy,dx=-math.sin(th),math.cos(th)
        # walk out to the counter edge, then measure the ink run
        r=0.0; step=0.25
        while r<max(H,W):
            y,x=int(round(cy+dy*r)), int(round(cx+dx*r))
            if not (0<=y<H and 0<=x<W): break
            if sub[y,x]: break
            r+=step
        r0=r; 
        while r<max(H,W):
            y,x=int(round(cy+dy*r)), int(round(cx+dx*r))
            if not (0<=y<H and 0<=x<W) or not sub[y,x]: break
            r+=step
        out.append((math.degrees(th), r-r0))
    # normalise to the loop counter's own mean radius so two images compare
    rad=((boxes[1][3]-boxes[1][2])+(boxes[1][5]-boxes[1][4]))/4
    return [(a,w/rad) for a,w in out]

if __name__=="__main__":
    pass
