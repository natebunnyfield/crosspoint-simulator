"""glyph_zoom.py -- the c at high zoom over a box in FINAL (sheared) units, every outline vertex dotted,
and any construction points the glyph prints under a debug env (lines like `name (x,y)`) marked in red,
mapped through IT_LC_SCALE x IT_LC_SETW and the shear.

    env "${ALBO_BIT_ENV[@]}" ALBO_ALD_C_TOPDRAW_700=1 ALBO_ALD_C_TOPDEBUG=1 CQ_SCALE=4 \
        PYTHON_GIL=0 python3 instruments/glyph_zoom.py z.png 240,300,470,460

Found the two defects no gate sees on the drawn c top: a corner where a drawn edge met the crown
(junction right of the apex) and an S-curve underside (second control point right of the first).
Edit `build.draw('c')` for another glyph.
"""
import sys, os, math, re, io, contextlib
sys.path.insert(0, os.getcwd())
from outlines import build, pen
from PIL import Image, ImageDraw
out=sys.argv[1]; box=[float(v) for v in sys.argv[2].split(',')]  # x0,y0,x1,y1 in final (sheared) units
buf=io.StringIO()
with contextlib.redirect_stdout(buf): g=build.draw('c')
dbg=buf.getvalue()
SC=float(os.environ.get("CQ_SCALE","4")); x0,y0,x1,y1=box
W=int((x1-x0)*SC); H=int((y1-y0)*SC)
im=Image.new("RGB",(W,H),(250,249,246)); d=ImageDraw.Draw(im)
def P(x,y): return ((x-x0)*SC, (y1-y)*SC)
polys=[g] if g.geom_type=='Polygon' else list(g.geoms)
for Pg in polys:
    d.polygon([P(x,y) for x,y in Pg.exterior.coords], fill=(40,40,40))
    for h in Pg.interiors: d.polygon([P(x,y) for x,y in h.coords], fill=(250,249,246))
    pts=list(Pg.exterior.coords)
    for x,y in pts: 
        if x0<=x<=x1 and y0<=y<=y1: d.ellipse([P(x,y)[0]-2,P(x,y)[1]-2,P(x,y)[0]+2,P(x,y)[1]+2], fill=(0,200,255))
s=build.IT_LC_SCALE; sw=build.IT_LC_SETW; t=math.tan(math.radians(pen.SLANT))
for name,(ux,uy) in re.findall(r'(\w+) \((-?\d+),(-?\d+)\)', dbg) and [(n,(float(a),float(b))) for n,a,b in re.findall(r'(\w+) \((-?\d+),(-?\d+)\)', dbg)]:
    X=ux*s*sw; Y=uy*s; X+=Y*t
    q=P(X,Y); d.ellipse([q[0]-6,q[1]-6,q[0]+6,q[1]+6], outline=(220,30,30), width=3); d.text((q[0]+8,q[1]-8), name, fill=(220,30,30))
im.save(out); print(out, dbg.strip()[:300])
