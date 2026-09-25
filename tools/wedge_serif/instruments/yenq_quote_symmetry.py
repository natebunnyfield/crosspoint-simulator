"""Quote asymmetry, measured on the built TTF (italics unsheared).
  mirror IoU  the mark against its own mirror image about its vertical axis
  lean        principal-axis angle from vertical, degrees (+ = top to the right)
  edges       left / right edge angle from vertical over 20-80% of the height;
              mirror symmetry means L = -R, so L+R is the edge asymmetry
  pair        " : IoU of mark 2 onto mark 1 (translated);  ‘ vs mirrored ’ : IoU
"""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from yenq_probe import glyph_poly, runs, mirror_iou, SP
import shapely.affinity as aff


def parts(g):
    return sorted(list(g.geoms) if g.geom_type == 'MultiPolygon' else [g], key=lambda p: p.bounds[0])


def lean(p):
    xs, ys = p.exterior.coords.xy
    # area moments via triangulation-free approximation: sample interior grid
    import numpy as np, shapely
    x0, y0, x1, y1 = p.bounds
    X, Y = np.meshgrid(np.linspace(x0, x1, 80), np.linspace(y0, y1, 160))
    m = shapely.contains_xy(p, X.ravel(), Y.ravel())
    X, Y = X.ravel()[m], Y.ravel()[m]
    X = X - X.mean(); Y = Y - Y.mean()
    sxx, syy, sxy = (X * X).mean(), (Y * Y).mean(), (X * Y).mean()
    ang = 0.5 * math.atan2(2 * sxy, sxx - syy)          # major axis from +x
    deg = 90 - math.degrees(ang)                        # from vertical
    if deg > 90: deg -= 180
    return -deg                                          # + = top leans right


def edges(p):
    x0, y0, x1, y1 = p.bounds; h = y1 - y0
    L, R = [], []
    for k in range(13):
        y = y0 + h * (0.2 + 0.6 * k / 12)
        rs = runs(p, y)
        if rs: L.append((y, rs[0][0])); R.append((y, rs[-1][1]))
    def slope(pts):
        n = len(pts); my = sum(y for y, _ in pts) / n; mx = sum(x for _, x in pts) / n
        num = sum((y - my) * (x - mx) for y, x in pts); den = sum((y - my) ** 2 for y, _ in pts)
        return math.degrees(math.atan(num / den))
    return slope(L), slope(R)      # dx/dy of each edge, degrees; mirror symmetry means L = -R


def iou(a, b):
    return a.intersection(b).area / a.union(b).area


def align(a, b):
    return aff.translate(b, a.bounds[0] - b.bounds[0], a.bounds[3] - b.bounds[3])


def row(d, cut):
    f = f'{SP}/{d}/Albo-{cut}.ttf'
    out = []
    for ch in "'’‘":
        g, _ = glyph_poly(f, ch)
        el, er = edges(g)
        ax = mirror_iou(aff.rotate(g, -lean(g), origin="centroid"))
        out.append(f"{ch} iou {mirror_iou(g):.3f} axis-iou {ax:.3f} lean {lean(g):+5.1f} edges {el:+5.1f}/{er:+5.1f} sum {el + er:+5.1f}")
    g, _ = glyph_poly(f, '"'); a, b = parts(g)[:2]
    out.append(f'" marks {iou(a, align(a, b)):.3f}')
    r, _ = glyph_poly(f, '’'); l, _ = glyph_poly(f, '‘')
    rm = aff.scale(r, -1, 1, origin=(0, 0))
    out.append(f"‘~mirror’ {iou(l, align(l, rm)):.3f}")
    return out


if __name__ == '__main__':
    for d in sys.argv[1:]:
        for cut in ('Regular', 'Italic', 'Bold', 'BoldItalic'):
            print(f"{d:6s} {cut:10s} | " + ' | '.join(row(d, cut)))
