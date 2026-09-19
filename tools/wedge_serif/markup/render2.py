import sys, json, html
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from PIL import Image, ImageDraw
SP='/private/tmp/claude-501/-Users-natebunnyfield-src-crosspoint-simulator/06bd1159-4703-424c-abda-64842a60926b/scratchpad'
R=json.load(open(f'{SP}/ledger2/regions.json')); SC=300/674.0
def contours(gs,name):
    pen=RecordingPen(); gs[name].draw(pen); cs=[]; cur=[]
    for op,a in pen.value:
        if op=='moveTo': cur=[a[0]]
        elif op=='lineTo': cur.append(a[0])
        elif op in ('closePath','endPath'): cs.append(cur); cur=[]
    if cur: cs.append(cur)
    return cs
idx={}
for style, ttf, js in (('roman',f'{SP}/r232_rom/Albo-Medium.ttf',f'{SP}/bumps/bumps-roman.json'),('italic',f'{SP}/r231f_it/Albo-Italic.ttf',f'{SP}/bumps/bumps-italic.json')):
    f=TTFont(ttf); gs=f.getGlyphSet(); cmap=f.getBestCmap(); J=json.load(open(js))
    for r in R[style]:
        ch=r['glyph']; ux0,uy0,ux1,uy1=r['box']; cx,cy=(ux0+ux1)/2,(uy0+uy1)/2
        half=max(110.0,(ux1-ux0)/2+60,(uy1-uy0)/2+60); Z=min(3.0,900/(2*half))
        bx0,by0,bx1,by1=cx-half,cy-half,cx+half,cy+half; W=H=int(2*half*Z)
        im=Image.new('RGB',(W,H),(255,255,255)); d=ImageDraw.Draw(im,'RGBA'); P=lambda x,y:((x-bx0)*Z,(by1-y)*Z)
        cs=contours(gs,cmap[ord(ch)])
        for c in cs: d.polygon([P(*p) for p in c],fill=(0,0,0,45))
        for c in cs:
            pts=[P(*p) for p in c]; d.line(pts+[pts[0]],fill=(0,0,0,255),width=1)
            for p in pts: d.ellipse([p[0]-1.6,p[1]-1.6,p[0]+1.6,p[1]+1.6],fill=(200,0,0,255))
        for gy in (0,429,674):
            if by0<=gy<=by1: d.line([P(bx0,gy),P(bx1,gy)],fill=(0,0,255,70))
        d.rectangle([P(ux0,uy1),P(ux1,uy0)],fill=(255,230,0,55),outline=(200,170,0,255),width=2)
        for e in J:
            if e['glyph']==ch and bx0<=e['x']<=bx1 and by0<=e['y']<=by1:
                p=P(e['x'],e['y']); rr=22*Z/SC*0.45; d.ellipse([p[0]-rr,p[1]-rr,p[0]+rr,p[1]+rr],outline=(220,0,0,255),width=2); d.text((p[0]+rr+2,p[1]-rr),str(e['n']),fill=(220,0,0,255))
        d.text((6,4),f"{r['id']}  {style} {ch}  [{int(bx0)},{int(by0)} - {int(bx1)},{int(by1)}] units, {Z:.2f} px/unit",fill=(0,0,200,255))
        gn=cmap[ord(ch)]; k=sum(1 for q in R[style] if q['glyph']==ch and q['id']<=r['id'])
        fn=f"{style[0]}_{'cap' if ch.isupper() else ''}{gn}_{r['id'][len(ch)+1:]}.png"; im.save(f'{SP}/ledger2/{fn}')
        idx[r['id']]=dict(style=style,glyph=ch,file=fn,box=r['box'],size=[W,H])
json.dump(idx,open(f'{SP}/ledger2/index.json','w'),indent=1); print(len(idx),'crops')
