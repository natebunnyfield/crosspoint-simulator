"""band_extent.py -- what the italic fit will read for a glyph, from the LIVE builder: its unsheared
ink extent inside the x-height band (the only ink the italic bearings are measured from), its full
extent, and its ink top and bottom.

    env "${ALBO_ITA_ENV[@]}" [dials] PYTHON_GIL=0 python3 instruments/band_extent.py rnij

build.fit_aldine reads min/max of x - SHEAR*y over the outline points whose ROUNDED y lies in
[-OVER, XH + OVER]; the advance is lsb + (r - l) + rsb from the bearings table. So a redrawn part
that moves `band r` moves the advance, and every pair after the letter, by exactly that much --
this is the check that a drawing fix did not quietly respace the letter. Written 2026-09-28 for
the r's drawn arm (docs/albo-issue-sweep-2026-09-28.md).
"""
import sys, os
sys.path.insert(0, os.getcwd())
from outlines import build, pen

for ch in sys.argv[1] if len(sys.argv) > 1 else "r":
    g = build.draw(ch)
    polys = [g] if g.geom_type == 'Polygon' else list(g.geoms)
    pts = [p for P in polys for ring in [P.exterior] + list(P.interiors) for p in ring.coords]
    sh = pen.SHEAR; lo, hi = -pen.OVER, pen.XH + pen.OVER
    band = [x - sh * y for x, y in pts if lo <= round(y) <= hi]
    allx = [x - sh * y for x, y in pts]
    ys = [y for _, y in pts]
    print(f"{ch}: band l {min(band):7.1f} r {max(band):7.1f} w {max(band) - min(band):6.1f} | full l {min(allx):7.1f} r {max(allx):7.1f} | ink y {min(ys):6.1f}..{max(ys):6.1f}  (band {lo}..{hi})")
