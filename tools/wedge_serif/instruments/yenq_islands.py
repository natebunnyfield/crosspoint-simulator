"""Islands of a glyph and the white between every pair: the minimum distance
and the length of the stretch where the white stays within 1.5 units of it
(the gap's 'run'), measured unsheared. usage: islands.py TTF CH"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from yenq_probe import glyph_poly, CAP
import shapely.geometry as sg
from shapely.ops import nearest_points


def islands(g):
    return sorted(list(g.geoms) if g.geom_type == 'MultiPolygon' else [g], key=lambda p: -p.area)


def gap_profile(a, b, tol=1.5):
    """Sample a's boundary; the points whose distance to b is within tol of
    the minimum give the gap's run (their extent along the boundary)."""
    d = a.distance(b)
    ring = a.exterior
    L = ring.length; n = int(L / 1.0)
    near = [ring.interpolate(i / n * L) for i in range(n)]
    close = [p for p in near if p.distance(b) <= d + tol]
    if not close: return d, 0.0, None
    ys = [p.y for p in close]
    pa, pb = nearest_points(a, b)
    span = max(((p.x - q.x) ** 2 + (p.y - q.y) ** 2) ** 0.5 for p in close for q in close)
    return d, span, ((pa.x + pb.x) / 2, (pa.y + pb.y) / 2)


def report(ttf, ch, unshear=None):
    g, n = glyph_poly(ttf, ch, unshear)
    isl = islands(g)
    rows = []
    for i in range(len(isl)):
        for j in range(i + 1, len(isl)):
            d, span, mid = gap_profile(isl[i], isl[j])
            if d < 40:
                rows.append((i, j, d, span, mid))
    return n, len(isl), [round(p.area) for p in isl], rows


if __name__ == '__main__':
    from yenq_probe import SP
    d = sys.argv[1]
    for cut in ('Regular', 'Italic', 'Bold', 'BoldItalic'):
        for ch in sys.argv[2]:
            n, k, areas, rows = report(f'{SP}/{d}/Albo-{cut}.ttf', ch)
            print(f"{cut:10s} {ch}  contours {n}, islands {k}, areas {areas}")
            for i, j, dd, span, mid in rows:
                print(f"      islands {i}-{j}: white {dd:.1f} u, run {span:.0f} u, at y/cap {mid[1] / CAP:.3f} x {mid[0]:.0f}")
