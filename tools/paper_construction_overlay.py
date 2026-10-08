# Draw the paper construction (8 pt grid, glass-band circles, paper-to-ink
# margin circles, the corner circle) over an iOS Simulator capture, measured
# from the pixels. usage: paper_construction_overlay.py IN.png OUT.png SCALE MARGINS(0|1)
# docs/zen-mode.md, "Construction measured, 2026-10-08".
import sys, json
from PIL import Image, ImageDraw, ImageFont
def run(src, out, scale, margins=True):
    im=Image.open(src).convert('RGB'); W,H=im.size; px=im.load()
    isP=lambda p: sum(p)>600; isInk=lambda p: sum(p)<450
    cx,cy=W//2,H//2
    def run_along(get,n,start):
        a=start
        while a>0 and isP(get(a-1)): a-=1
        b=start
        while b<n-1 and isP(get(b+1)): b+=1
        return a,b
    # page center is paper; find a paper pixel near center
    isP=lambda p: sum(p)>40
    top,bot=run_along(lambda y:px[cx,y],H,cy)
    yr=top+(bot-top)//2
    left,right=run_along(lambda x:px[x,yr],W,cx)
    isP=lambda p: sum(p)>600
    # corner radius: on the top row, first paper x
    x=left
    while sum(px[x,top])<=40 and x<right: x+=1
    rad=x-left
    # ink rows inside paper
    rows=[y for y in range(top+4,bot-3) if any(isInk(px[xx,y]) for xx in range(left+rad+6,right-rad-6,2))]
    inkT,inkB=(rows[0],rows[-1]) if rows else (top,bot)
    cols=[xx for xx in range(left+4,right-3) if any(isInk(px[xx,y]) for y in range(inkT,inkB+1,3))]
    inkL,inkR=(cols[0],cols[-1]) if cols else (left,right)
    g1=inkT-top; g2=bot-inkB; a=top; b=H-1-bot
    ov=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(ov)
    grid=8*scale
    for gx in range(0,W,grid): d.line([(gx,0),(gx,H)],fill=(80,140,255,55),width=1)
    for gy in range(0,H,grid): d.line([(0,gy),(W,gy)],fill=(80,140,255,55),width=1)
    C=(0,190,210,255); M=(230,40,160,255); Y=(240,170,0,255); lw=max(2,scale)
    def circ(cxx,cyy,r,col): d.ellipse([cxx-r,cyy-r,cxx+r,cyy+r],outline=col,width=lw)
    # band circles: one above, stack below
    if a>4:
        u=a; circ(left-u/2-6 if left-u-6>0 else W-u/2-6, a/2, u/2, M)
        n=max(1,round(b/u)); 
        for i in range(n): circ(left-u/2-6 if left-u-6>0 else W-u/2-6, bot+u/2+i*u+1, u/2, M)
    # margin circles inside paper: one above ink, stack below
    if margins and g1>4:
        circ(right-g1/2-rad*0, top+g1/2, g1/2, C)
        n2=max(1,round(g2/g1))
        for i in range(n2): circ(right-g1/2, inkB+g1/2+i*g1+1, g1/2, C)
    # corner circle
    if rad>2: circ(left+rad, top+rad, rad, Y)
    # edges
    d.rectangle([left,top,right,bot],outline=(0,190,210,160),width=1)
    d.line([(left,inkT),(right,inkT)],fill=(0,190,210,160),width=1); d.line([(left,inkB),(right,inkB)],fill=(0,190,210,160),width=1)
    res=Image.alpha_composite(im.convert('RGBA'),ov).convert('RGB')
    font=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',int(13*scale))
    dd=ImageDraw.Draw(res)
    info=dict(paper=[left,top,right,bot],ink=[inkL,inkT,inkR,inkB],corner=rad,band_above=a,band_below=b,band_ratio=round(b/a,2) if a else None,margin_top=g1,margin_bottom=g2,margin_ratio=round(g2/g1,2) if g1 else None)
    mt=f"   paper-to-ink {g1} : {g2} px = 1 : {info['margin_ratio']}" if margins else ""
    bt=f"glass bands {a} : {b} px = 1 : {info['band_ratio']}" if b>0 else f"glass band above {a} px, none below"
    txt=bt+mt+f"   corner inset {rad} px   grid 8 pt"
    dd.rectangle([0,H-int(30*scale),W,H],fill=(0,0,0)); dd.text((int(6*scale),H-int(24*scale)),txt,fill=(255,255,255),font=font)
    res.save(out); return info
if __name__=='__main__':
    print(json.dumps(run(sys.argv[1],sys.argv[2],int(sys.argv[3]),sys.argv[4]=='1')))
