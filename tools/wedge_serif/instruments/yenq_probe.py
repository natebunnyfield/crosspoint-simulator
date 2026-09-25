"""Glyph geometry from a built TTF, unsheared for the italics, as shapely."""
import math, os, sys
WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, WS)
import shapely.geometry as sg
from shapely.ops import unary_union
import shapely.affinity as aff
SP = os.environ.get("ALBO_OPT_DIR", ".")   # holds head/ opt_b/ ... opt_e/, each an albo_build_all OUTDIR
SHEAR = math.tan(math.radians(13))
CAP = 674.0


def glyph_poly(ttf, ch, unshear=None):
    import cmp_aldine_glitch as G
    if unshear is None:
        unshear = 'Italic' in os.path.basename(ttf)
    (c, conts, note), = list(G.from_ttf(ttf, ch))
    ext = [sg.Polygon(p) for p, h in conts if not h]
    holes = [sg.Polygon(p) for p, h in conts if h]
    g = unary_union([e.buffer(0) for e in ext])
    for h in holes:
        g = g.difference(h.buffer(0))
    if unshear:
        g = aff.affine_transform(g, (1, -SHEAR, 0, 1, 0, 0))
    return g, len(conts)


def runs(g, y):
    x0, _, x1, _ = g.bounds
    r = g.intersection(sg.LineString([(x0 - 5, y), (x1 + 5, y)]))
    segs = list(r.geoms) if hasattr(r, 'geoms') else ([r] if not r.is_empty else [])
    return sorted((s.bounds[0], s.bounds[2]) for s in segs if s.length > 0)


def scan(g, lo, hi, step, cap=CAP):
    out = []
    y = lo
    while y <= hi + 1e-9:
        rs = runs(g, y * cap)
        gaps = [rs[i + 1][0] - rs[i][1] for i in range(len(rs) - 1)]
        out.append((y, rs, gaps))
        y = round(y + step, 4)
    return out


def mirror_iou(g):
    """IoU of the glyph with its own mirror about the vertical line through
    its area centroid, and about its bbox centre; the max of the two."""
    best = 0
    for cx in (g.centroid.x, (g.bounds[0] + g.bounds[2]) / 2):
        m = aff.scale(g, -1, 1, origin=(cx, 0))
        best = max(best, g.intersection(m).area / g.union(m).area)
    return best


if __name__ == '__main__':
    ttf, ch = sys.argv[1], sys.argv[2]
    lo, hi, st = (float(v) for v in sys.argv[3:6]) if len(sys.argv) > 5 else (0.30, 0.60, 0.01)
    g, n = glyph_poly(ttf, ch)
    print(ch, 'contours', n, 'bounds', [round(v) for v in g.bounds])
    for y, rs, gaps in scan(g, lo, hi, st):
        print(f"{y:.3f}  " + ' | '.join(f"{a:.0f}-{b:.0f}" for a, b in rs) + ("   gaps " + ', '.join(f"{q:.1f}" for q in gaps) if gaps else ''))
