"""glyph_overlay.py -- Albo glyph (filled gray, unsheared back to upright) under reference outlines
(colored lines, each unsheared by its italic angle and scaled to Albo's x-height, 429).

    env "${ALBO_BIT_ENV[@]}" PYTHON_GIL=0 python3 instruments/glyph_overlay.py out.png c \
        refs/poetica-std-regular.otf refs/coelacanth-italic.otf@12

`path@deg` forces the unshear angle: **Coelacanth's post table declares italicAngle 0**, so it must be
unsheared by hand (12 deg fits); Poetica declares -11. Glyphs are aligned on their left extreme.
The caption prints Albo's sheared bounds and its c/o width ratio. CQ_LABEL adds a caption.
This is how the c's terminal position, reach and face angle were matched (round 433).
"""
import sys, os, math
sys.path.insert(0, os.getcwd())
from outlines import build, pen
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.basePen import BasePen
out=sys.argv[1]; ch=sys.argv[2]; refs=sys.argv[3:]
SC=1.2; XH=429.0
def unshear_pts(pts, ang):
    t=math.tan(math.radians(ang)); return [(x - y*t, y) for x,y in pts]
g=build.draw(ch)
slant=pen.SLANT if hasattr(pen,'SLANT') else 13.0
polys=[g] if g.geom_type=='Polygon' else list(g.geoms)
A=[]; 
for P in polys:
    A.append(unshear_pts(list(P.exterior.coords), slant)); A += [unshear_pts(list(h.coords), slant) for h in P.interiors]
ax=[x for r in A for x,_ in r]; ay=[y for r in A for _,y in r]
# Albo x-height: the glyph's measured xh for the italic
class Flat(BasePen):
    def __init__(s, gs): super().__init__(gs); s.c=[]; s.cur=[]
    def _moveTo(s,p): s.cur=[p]
    def _lineTo(s,p): s.cur.append(p)
    def _curveToOne(s,a,b,c):
        p0=s.cur[-1]
        for i in range(1,13):
            t=i/12; m=1-t
            s.cur.append((m**3*p0[0]+3*m*m*t*a[0]+3*m*t*t*b[0]+t**3*c[0], m**3*p0[1]+3*m*m*t*a[1]+3*m*t*t*b[1]+t**3*c[1]))
    def _qCurveToOne(s,a,b):
        p0=s.cur[-1]
        for i in range(1,9):
            t=i/8; m=1-t; s.cur.append((m*m*p0[0]+2*m*t*a[0]+t*t*b[0], m*m*p0[1]+2*m*t*a[1]+t*t*b[1]))
    def _closePath(s): s.c.append(s.cur); s.cur=[]
    _endPath=_closePath
def ref_rings(path, ch):
    path, _, force = path.partition("@")
    f=TTFont(path); gs=f.getGlyphSet(); cm=f.getBestCmap(); ang=-float(force) if force else f['post'].italicAngle
    fp=Flat(gs); gs[cm[ord('x')]].draw(fp); xh=max(y for r in fp.c for _,y in r)
    fp=Flat(gs); gs[cm[ord(ch)]].draw(fp)
    k=XH/xh
    return [[(x*k,y*k) for x,y in unshear_pts(r, -ang)] for r in fp.c], ang
W=int(700*SC); H=int(620*SC); im=Image.new("RGB",(W,H),(250,249,246)); d=ImageDraw.Draw(im)
base=int(520*SC)
# align: left extreme of each glyph at x=80
ox=80 - min(ax)
def P(x,y,off): return (int((x+off)*SC), int(base - y*SC))
for r in A: d.polygon([P(x,y,ox) for x,y in r], fill=(170,170,170))
d.line([P(-500,0,0),P(2000,0,0)],fill=(200,200,200)); d.line([P(-500,XH,0),P(2000,XH,0)],fill=(200,200,200))
cols=[(210,40,30),(30,90,200),(30,150,60),(160,60,160)]
F=ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc",16)
for i,rp in enumerate(refs):
    rings,ang=ref_rings(rp, ch)
    rx=[x for r in rings for x,_ in r]; off=80-min(rx)
    for r in rings: d.line([P(x,y,off) for x,y in r]+[P(*r[0],off)], fill=cols[i%4], width=2)
    d.text((10,10+18*i), f"{os.path.basename(rp)} (unsheared {ang:.1f})", fill=cols[i%4], font=F)
o=build.draw('o'); cw=(g.bounds[2]-g.bounds[0])/(o.bounds[2]-o.bounds[0])
d.text((10,10+18*len(refs)), f"Albo gray; sheared bounds {[round(v) for v in g.bounds]}; c/o {cw:.2f}; {os.environ.get('CQ_LABEL','')}", fill=(90,90,90), font=F)
im.save(out); print(out)
