"""glyph_view.py -- draw glyphs straight from the LIVE builder and render them large. 0.1 s a glyph.

Run from tools/wedge_serif with the cut's environment (build_env.sh arrays) plus any dials:

    source build_env.sh
    env "${ALBO_BIT_ENV[@]}" ALBO_ALD_C_TOPDRAW_700=1 PYTHON_GIL=0 python3 instruments/glyph_view.py out.png ocecoa

This is the fast loop for drawing: outlines.build.draw(ch) is the shipped geometry (shear, IT_LC
scale, ink spread) without a font build (~2 min a cut). Use it to iterate, then build the cut once
for the gates. CQ_SCALE (default 0.8) sets px per unit; CQ_XH draws the x-line guide (default 444).
Added 2026-09-28 (the Bold Italic c's drawn top, docs/albo-round-433-2026-09-28.md).
"""
import sys, os, time
t0=time.time()
sys.path.insert(0, os.getcwd())
from outlines import build
from PIL import Image, ImageDraw
out=sys.argv[1]; chars=sys.argv[2] if len(sys.argv)>2 else "c"
SC=float(os.environ.get("CQ_SCALE","0.8")); H=int(700*SC)+40
geoms=[build.draw(ch) for ch in chars]
Wtot=int(sum((g.bounds[2]-min(0,g.bounds[0])+60)*SC for g in geoms))+40
im=Image.new("L",(Wtot,H),250); d=ImageDraw.Draw(im)
base=int(560*SC)+20; x0=20
xh=float(os.environ.get("CQ_XH","444"))
d.line([(0,base),(Wtot,base)],fill=200); d.line([(0,base-xh*SC),(Wtot,base-xh*SC)],fill=200)
for g in geoms:
    polys=[g] if g.geom_type=='Polygon' else list(g.geoms)
    for P in polys:
        ext=[(x0+x*SC, base-y*SC) for x,y in P.exterior.coords]; d.polygon(ext,fill=0)
        for h in P.interiors: d.polygon([(x0+x*SC, base-y*SC) for x,y in h.coords],fill=250)
    x0+=int((g.bounds[2]+60)*SC)
im.save(out); print(f"{out} {time.time()-t0:.1f}s bounds={[tuple(round(v) for v in g.bounds) for g in geoms]}")
