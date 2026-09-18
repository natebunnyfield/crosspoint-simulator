"""Curves as sampled point lists, and the union of polygons (shapely).

Everything is in font units, y up. Curves are sampled at SPACING units of
arc length -- the same density the round-17 pen used (one sample per ~11
units, one vertex in four kept by the cut, facets of ~45 units), so the
cut's texture matches the record."""
import math
import numpy as np
import shapely
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union

SPACING = 11.0

def _n(length, spacing): return max(3, int(math.ceil(length / spacing)))

def cubic(p0, c1, c2, p3, spacing=SPACING):
    L = math.dist(p0, c1) + math.dist(c1, c2) + math.dist(c2, p3)
    n = _n(L, spacing); out = []
    for i in range(n + 1):
        t = i / n; m = 1 - t
        out.append((m*m*m*p0[0] + 3*m*m*t*c1[0] + 3*m*t*t*c2[0] + t*t*t*p3[0],
                    m*m*m*p0[1] + 3*m*m*t*c1[1] + 3*m*t*t*c2[1] + t*t*t*p3[1]))
    return out

def quad(p0, c, p1, spacing=SPACING):
    L = math.dist(p0, c) + math.dist(c, p1); n = _n(L, spacing); out = []
    for i in range(n + 1):
        t = i / n; m = 1 - t
        out.append((m*m*p0[0] + 2*m*t*c[0] + t*t*p1[0], m*m*p0[1] + 2*m*t*c[1] + t*t*p1[1]))
    return out

def line(p0, p1, spacing=SPACING):
    n = _n(math.dist(p0, p1), spacing)
    return [(p0[0] + (p1[0] - p0[0]) * i / n, p0[1] + (p1[1] - p0[1]) * i / n) for i in range(n + 1)]

def superellipse(cx, cy, rx, ry, a0, a1, k=2.0, spacing=SPACING, rot=0.0):
    """Points on a superellipse (k=2 a true ellipse, higher = squarer
    shoulders) from angle a0 to a1 (radians, 0 = right, ccw positive). rot
    tilts the whole figure. Angle steps are uniform; the arc is resampled
    to SPACING afterwards."""
    L = abs(a1 - a0) * max(rx, ry); n = max(8, _n(L, spacing / 2)); out = []
    cr, sr = math.cos(rot), math.sin(rot)
    for i in range(n + 1):
        a = a0 + (a1 - a0) * i / n; c, s = math.cos(a), math.sin(a)
        x = rx * math.copysign(abs(c) ** (2 / k), c); y = ry * math.copysign(abs(s) ** (2 / k), s)
        out.append((cx + x * cr - y * sr, cy + x * sr + y * cr))
    return resample(out, spacing)

def catmull(points, spacing=SPACING, tension=0.5, closed=False):
    """A smooth spline through the points (tangent continuous)."""
    P = list(points)
    if closed: P = [P[-1]] + P + [P[0], P[1]]
    else: P = [P[0]] + P + [P[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i-1], P[i], P[i+1], P[i+2]
        c1 = (p1[0] + (p2[0]-p0[0]) * tension / 3, p1[1] + (p2[1]-p0[1]) * tension / 3)
        c2 = (p2[0] - (p3[0]-p1[0]) * tension / 3, p2[1] - (p3[1]-p1[1]) * tension / 3)
        seg = cubic(p1, c1, c2, p2, spacing)
        out.extend(seg if i == 1 else seg[1:])
    return out

def join(*parts):
    """Concatenate sampled pieces, dropping a repeated joint point."""
    out = []
    for p in parts:
        if out and math.dist(out[-1], p[0]) < 1e-6: out.extend(p[1:])
        else: out.extend(p)
    return out

def resample(pts, spacing=SPACING):
    """Uniform arc-length resampling, both ends kept."""
    if len(pts) < 2: return list(pts)
    d = [0.0]
    for a, b in zip(pts, pts[1:]): d.append(d[-1] + math.dist(a, b))
    L = d[-1]
    if L < 1e-9: return [pts[0]]
    n = _n(L, spacing); out = []; j = 0
    for i in range(n + 1):
        s = L * i / n
        while j < len(d) - 2 and d[j + 1] < s: j += 1
        seg = d[j + 1] - d[j]; t = (s - d[j]) / seg if seg > 1e-12 else 0
        out.append((pts[j][0] + (pts[j+1][0] - pts[j][0]) * t, pts[j][1] + (pts[j+1][1] - pts[j][1]) * t))
    return out

def tangents(pts, closed=False):
    t = []; n = len(pts)
    for i in range(n):
        if closed: a = pts[(i - 1) % n]; b = pts[(i + 1) % n]
        else: a = pts[max(0, i - 1)]; b = pts[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy) or 1.0
        t.append((dx / L, dy / L))
    return t

def signed_area(poly):
    a = 0.0
    for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]): a += x0 * y1 - x1 * y0
    return a / 2

def translate(pts, dx, dy): return [(x + dx, y + dy) for x, y in pts]
def mirror_x(pts, axis): return [(2 * axis - x, y) for x, y in pts]
def mirror_y(pts, axis): return [(x, 2 * axis - y) for x, y in pts]
def rotate(pts, cx, cy, deg):
    a = math.radians(deg); c, s = math.cos(a), math.sin(a)
    return [(cx + (x - cx) * c - (y - cy) * s, cy + (x - cx) * s + (y - cy) * c) for x, y in pts]
def scale(pts, cx, cy, sx, sy=None):
    sy = sx if sy is None else sy
    return [(cx + (x - cx) * sx, cy + (y - cy) * sy) for x, y in pts]

def smooth(pts, passes=1, closed=False):
    """Chaikin corner cutting -- for a derived edge (an offset) that must
    read as a drawn curve."""
    for _ in range(passes):
        out = []; n = len(pts)
        rng = range(n) if closed else range(n - 1)
        for i in rng:
            a, b = pts[i], pts[(i + 1) % n]
            out.append((0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1]))
            out.append((0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1]))
        if not closed: out = [pts[0]] + out + [pts[-1]]
        pts = out
    return pts

# ---------------------------------------------------------------- shapely
def poly(outer, holes=()):
    """A valid polygon from a possibly self-crossing outline: folds and
    crossings are resolved by make_valid and EVERY piece is kept (a stroke
    that crosses itself -- the &, the @'s ring -- is the union of its
    pieces; the first version kept only the largest and the & lost its
    loop, seen on the e-ink proof)."""
    g = Polygon(outer, [list(h) for h in holes])
    if not g.is_valid: g = shapely.make_valid(g)
    if g.geom_type == 'Polygon': return g
    parts = [p for p in getattr(g, 'geoms', []) if p.geom_type == 'Polygon' and p.area > 2.0]
    if not parts: return Polygon()
    return unary_union(parts)

def _largest(g):
    if g.geom_type == 'Polygon': return g
    parts = [p for p in getattr(g, 'geoms', []) if p.geom_type == 'Polygon']
    if not parts: return Polygon()
    return max(parts, key=lambda p: p.area)

def union(geoms):
    gs = [g for g in geoms if g is not None and not g.is_empty]
    if not gs: return Polygon()
    return unary_union(gs)

def ink(solids, cutouts=()):
    """The glyph: union of its solids minus its cutouts (counters drawn as
    their own shapes, ink traps)."""
    g = union(solids)
    if cutouts:
        g = g.difference(union(cutouts))
    return g

def close_corners(g, r, segs=24):
    """ROUND 205b -- FILL THE CONCAVE CORNERS A UNION LEAVES.

    `ink` adds shapes, and where a band meets a ring at an angle the result is
    a notch on one side and a knuckle on the other, however well the two are
    aimed. A morphological CLOSING -- dilate by r, erode by r -- fills exactly
    those: a concave corner is rounded to radius r, a convex one comes back
    where it was, and no edge moves in between. Owner 2026-09-17: *"make sure
    the connector blends perfectly so it appears to be continuous strokes"*.

    r must stay well under half the narrowest white the letter is meant to
    keep, because a closing also bridges any channel narrower than 2r.
    """
    if not r or r <= 0:
        return g
    return _largest(g.buffer(r, join_style=1, quad_segs=segs)
                     .buffer(-r, join_style=1, quad_segs=segs))


def contours(g, min_area=40.0):
    """[(points, is_hole)] with exteriors wound CCW (positive area) and holes
    CW -- the nonzero winding TrueType wants. Tiny slivers are dropped."""
    out = []
    polys = [g] if g.geom_type == 'Polygon' else [p for p in getattr(g, 'geoms', []) if p.geom_type == 'Polygon']
    for p in polys:
        if p.area < min_area: continue
        ext = list(p.exterior.coords)[:-1]
        if signed_area(ext) < 0: ext = ext[::-1]
        out.append((ext, False))
        for r in p.interiors:
            h = list(r.coords)[:-1]
            if abs(signed_area(h)) < min_area: continue
            if signed_area(h) > 0: h = h[::-1]
            out.append((h, True))
    return out

def bbox(g):
    return g.bounds if not g.is_empty else (0, 0, 0, 0)
