"""The mechanical checks on a built font (guide §4): the o's counter aspect
(1.036), bearings >= 20 a side on non-letters, every contour valid and
every counter inside its solid (no contour crosses its own counter), and
no glyph's ink outside its advance except the ruled tucks (f right, j left,
J left, Q's tail) nor outside asc..desc.
    python3 -m outlines.cmp.checks <ttf>"""
import sys, math
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.boundsPen import BoundsPen
from .. import geom, pen, build
from ..glyphs import GLYPHS

def run(path):
    f = TTFont(path); gs = f.getGlyphSet(); cm = f.getBestCmap(); hm = f['hmtx']
    rows = []; bad = []
    for cp, gn in sorted(cm.items()):
        ch = chr(cp)
        if ch == ' ': continue
        bp = BoundsPen(gs); gs[gn].draw(bp)
        if bp.bounds is None: continue
        x0, y0, x1, y1 = bp.bounds; adv, lsb = hm[gn]; rsb = adv - x1
        rows.append((ch, adv, lsb, rsb, y0, y1))
        if not ch.isalpha() and (lsb < 20 or rsb < 20): bad.append(f"{ch!r} bearing {lsb:.0f}/{rsb:.0f}")
        if ch.isalpha() and ch not in 'fjJQ' and (x0 < 0 or x1 > adv): bad.append(f"{ch!r} ink past advance {x0:.0f}..{x1:.0f} of {adv}")
        if y1 > pen.ASC + 40 or y0 < -pen.DESC - 30: bad.append(f"{ch!r} vertical {y0:.0f}..{y1:.0f}")
    # geometry validity from the drawing
    for ch in GLYPHS:
        g = build.draw(ch)
        if not g.is_valid: bad.append(f"{ch!r} invalid geometry")
        polys = [g] if g.geom_type == 'Polygon' else list(g.geoms)
        for p in polys:
            for r in p.interiors:
                from shapely.geometry import Polygon
                h = Polygon(r)
                if not p.exterior.coords or not Polygon(p.exterior).contains(h.representative_point()): bad.append(f"{ch!r} counter outside its solid")
    # the o's counter
    g = build.draw('o'); cs = geom.contours(g)
    for pts, hole in cs:
        if hole:
            xs = [x for x, y in pts]; ys = [y for x, y in pts]
            asp = (max(xs) - min(xs)) / (max(ys) - min(ys)); print(f"o counter {max(xs)-min(xs):.0f} x {max(ys)-min(ys):.0f} = {asp:.3f} (ruling 1.036)")
    print(len(rows), "glyphs;", len(bad), "problems"); [print("  ", b) for b in bad]
    tuck = [(ch, lsb, rsb) for ch, adv, lsb, rsb, y0, y1 in rows if ch.isalpha() and (lsb < 0 or rsb < 0)]
    print("letters with ink past the advance (ruled tucks expected: f right, j left, J left, Q tail):", [(ch, round(l), round(r)) for ch, l, r in tuck])
    return bad

if __name__ == '__main__':
    run(sys.argv[1])
