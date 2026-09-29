"""live_view.py -- glyph_view.py with the vertical range chosen: glyphs from the LIVE builder, filled.

    env "${ALBO_ROM_ENV[@]}" [dials] PYTHON_GIL=0 python3 instruments/live_view.py out.png "{(x)}"
    env: CQ_SCALE (px per unit, default 0.5), CQ_TOP / CQ_BOT (units, default 800 / -320), CQ_XH (the
         x-line guide, default 444)

glyph_view.py fixes the frame at 700 units with the baseline at 560, which cuts off anything that
reaches the ascender and the descender at once (the fences, the braces). Written 2026-09-28 for
the issue sweep's braces.
"""
import sys, os, time
sys.path.insert(0, os.getcwd())
from outlines import build
from PIL import Image, ImageDraw
out = sys.argv[1]; chars = sys.argv[2] if len(sys.argv) > 2 else "{"
SC = float(os.environ.get("CQ_SCALE", "0.5")); TOP = float(os.environ.get("CQ_TOP", "800")); BOT = float(os.environ.get("CQ_BOT", "-320"))
geoms = [build.draw(ch) for ch in chars]
Wtot = int(sum((g.bounds[2] - min(0, g.bounds[0]) + 60) * SC for g in geoms)) + 40
H = int((TOP - BOT) * SC) + 20
im = Image.new("L", (Wtot, H), 250); d = ImageDraw.Draw(im)
base = int(TOP * SC) + 10; x0 = 20
xh = float(os.environ.get("CQ_XH", "444"))
d.line([(0, base), (Wtot, base)], fill=200); d.line([(0, base - xh * SC), (Wtot, base - xh * SC)], fill=200)
for g in geoms:
    polys = [g] if g.geom_type == 'Polygon' else list(g.geoms)
    ox = x0 - min(0, g.bounds[0]) * SC
    for P in polys:
        d.polygon([(ox + x * SC, base - y * SC) for x, y in P.exterior.coords], fill=0)
        for h in P.interiors: d.polygon([(ox + x * SC, base - y * SC) for x, y in h.coords], fill=250)
    x0 += int((g.bounds[2] - min(0, g.bounds[0]) + 60) * SC)
im.save(out); print(out, [tuple(round(v) for v in g.bounds) for g in geoms])
