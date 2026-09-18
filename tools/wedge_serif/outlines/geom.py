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

def smooth_corners(pts, turn=28.0, window=2, passes=2):
    """ROUND 226 -- THE WOBBLE WAS THE POLYGON. Owner 2026-09-18: *"reduce
    most of the wobble effect on letters"*, then *"I don't see a wobble
    difference"* after every deliberate irregularity had been cut to a third.
    Measured, the imperfection tables move the italic lowercase by ZERO units
    -- what he sees is the export itself: every contour leaves here as a
    dense polyline at ~11-unit spacing, unioned facet by facet and rounded to
    the integer grid, and its curvature noise (the second difference of the
    edge's angle, per 10 units of contour) reads 6-21 on Albo's n m e o
    against Flanker's 0.7-1.4 and Georgia's 1.6-4. This smooths each contour
    BEFORE it is rounded: points whose turn exceeds `turn` degrees are
    corners and stay put; every run between corners is averaged over
    `window` neighbours on each side, `passes` times. A wedge's tip, a
    stem's foot and a bar's end are corners and survive; a bowl's facets do
    not. ALBO_SMOOTH=0 in build.py is the old polygon, byte for byte."""
    n = len(pts)
    if n < 8: return pts
    P = [(float(x), float(y)) for x, y in pts]
    def ang(i):
        ax, ay = P[i - 1]; bx, by = P[i]; cx, cy = P[(i + 1) % n]
        v1 = (bx - ax, by - ay); v2 = (cx - bx, cy - by)
        l1 = math.hypot(*v1); l2 = math.hypot(*v2)
        if l1 < 1e-9 or l2 < 1e-9: return 0.0
        d = max(-1.0, min(1.0, (v1[0] * v2[0] + v1[1] * v2[1]) / (l1 * l2)))
        return math.degrees(math.acos(d))
    corner = [ang(i) > turn for i in range(n)]
    for _ in range(passes):
        out = []
        for i in range(n):
            if corner[i]: out.append(P[i]); continue
            xs = []; ys = []; ws = []
            for k in range(-window, window + 1):
                j = (i + k) % n
                if k != 0 and corner[j]:      # do not pull a run through a corner
                    break_ = True
                w = 1.0 / (1 + abs(k))
                xs.append(P[j][0] * w); ys.append(P[j][1] * w); ws.append(w)
            out.append((sum(xs) / sum(ws), sum(ys) / sum(ws)))
        P = out
    return P

# ---------------------------------------------------------------- round 226
def _corners(P, turn):
    n = len(P); out = []
    for i in range(n):
        ax, ay = P[i - 1]; bx, by = P[i]; cx, cy = P[(i + 1) % n]
        v1 = (bx - ax, by - ay); v2 = (cx - bx, cy - by)
        l1 = math.hypot(*v1); l2 = math.hypot(*v2)
        if l1 < 1e-9 or l2 < 1e-9: out.append(False); continue
        d = max(-1.0, min(1.0, (v1[0] * v2[0] + v1[1] * v2[1]) / (l1 * l2)))
        out.append(math.degrees(math.acos(d)) > turn)
    return out

def _catmull_run(run, step):
    """Cubic Beziers THROUGH every `step`-th point of one run (ends always
    kept), with Catmull-Rom tangents -- C1 between the kept points, one-sided
    at the run's ends so a corner stays a corner. Interpolation, not
    least-squares: the curve is ON the dense polygon at every kept point, so
    it cannot drift, loop or pinch the way a fitted cubic can (the first cut
    put the roman e's tail 2 units from itself and blew a heart's inner
    contour 144 units out)."""
    n = len(run)
    idx = list(range(0, n - 1, step)) + [n - 1]
    if len(idx) < 2: return [('line', run[-1])]
    K = [run[i] for i in idx]
    m = len(K)
    def tan(i):
        if i == 0: a, b = K[0], K[1]
        elif i == m - 1: a, b = K[m - 2], K[m - 1]
        else: a, b = K[i - 1], K[i + 1]
        return ((b[0] - a[0]) * 0.5, (b[1] - a[1]) * 0.5)
    segs = []
    for i in range(m - 1):
        p0, p3 = K[i], K[i + 1]; t0, t1 = tan(i), tan(i + 1)
        chord = math.hypot(p3[0] - p0[0], p3[1] - p0[1]) or 1.0
        # uniform Catmull-Rom: Bezier handles at a third of the tangent, and
        # each handle CLAMPED to 0.35 of the chord -- a run's overshoot into
        # the stroke's other side is what pinched the italic F T g r s v w
        # (0.6-2.9 units) on the unclamped cut
        def clamp(v):
            L = math.hypot(*v) / 3.0
            if L <= 1e-9: return (0.0, 0.0)
            k = (0.30 * chord / (3.0 * L)) if L > 0.30 * chord else 1.0 / 3.0
            return (v[0] * k, v[1] * k)
        h0 = clamp(t0); h1 = clamp(t1)
        c1 = (p0[0] + h0[0], p0[1] + h0[1]); c2 = (p3[0] - h1[0], p3[1] - h1[1])
        segs.append(('cubic', c1, c2, p3))
    return segs


def _flatten(start, segs, n=8):
    pts = [start]; cur = start
    for sg in segs:
        if sg[0] == 'line': pts.append(sg[1]); cur = sg[1]
        else:
            c1, c2, p3 = sg[1], sg[2], sg[3]
            for i in range(1, n + 1):
                t = i / n
                pts.append(((1 - t) ** 3 * cur[0] + 3 * (1 - t) ** 2 * t * c1[0] + 3 * (1 - t) * t * t * c2[0] + t ** 3 * p3[0],
                            (1 - t) ** 3 * cur[1] + 3 * (1 - t) ** 2 * t * c1[1] + 3 * (1 - t) * t * t * c2[1] + t ** 3 * p3[1]))
            cur = p3
    return pts


def _dev_to_polyline(F, P):
    """Max distance from points F to the OPEN polyline P (point-to-segment)."""
    import numpy as _np
    A = _np.array(P[:-1], float); B = _np.array(P[1:], float); Q = _np.array(F, float)
    AB = B - A; L2 = (AB ** 2).sum(axis=1); L2[L2 == 0] = 1e-12
    worst = 0.0
    for q in Q:
        t = ((q - A) * AB).sum(axis=1) / L2; t = _np.clip(t, 0, 1)
        proj = A + AB * t[:, None]; d = _np.sqrt(((proj - q) ** 2).sum(axis=1)).min()
        if d > worst: worst = float(d)
    return worst

def fit_curves(pts, turn=28.0, step=3, max_dev=2.0, min_len=40.0, gentle_turn=12.0):
    """ROUND 226 -- THE WOBBLE WAS THE POLYGON, and averaging it made it worse.
    Every contour left the builder as a dense polyline at ~11-unit spacing,
    rounded to the integer grid: half a unit of rounding on an 11-unit segment
    is 2.6 degrees of angle noise per segment, and the edge's curvature noise
    read 6-21 (deg per 10 units) on Albo's n m e o against Flanker's 0.7-1.4
    and Georgia's 1.6-4. Corner-preserving averaging (the first cut) took it to
    20-26 and shrank the small marks by up to 24% -- fewer, better points are
    the answer, not moved ones. This fits each run between CORNERS (a turn over
    `turn` degrees) with least-squares cubics within `tol` units of the dense
    polygon, for the exporter to write as TrueType quadratics. Returns a list of
    segments: ('line', p) or ('cubic', c1, c2, p), starting at the run's first
    corner."""
    n = len(pts)
    if n < 6: return None
    P = [(float(x), float(y)) for x, y in pts]
    corner = _corners(P, turn)
    if not any(corner):                     # a closed smooth curve with no corner: cut it at its first point
        corner[0] = True
    # rotate so we start at a corner
    k = corner.index(True); P = P[k:] + P[:k]; corner = corner[k:] + corner[:k]
    runs = []; cur = [P[0]]
    for i in range(1, n):
        cur.append(P[i])
        if corner[i]: runs.append(cur); cur = [P[i]]
    cur.append(P[0]); runs.append(cur)
    segs = []; fitted_runs = 0; kept_runs = 0
    for run in runs:
        if len(run) <= 2: segs.append(('line', run[-1])); continue
        # ONLY A LONG, GENTLE RUN IS FITTED -- a bowl's or an arch's side, a
        # stem's flank -- which is where the facets show. A short or tightly
        # turning run (a serif, a terminal, a hairline tip) stays a polygon:
        # that is where a curve's overshoot pinched the e's tail, the g's
        # descender and the F's and T's bar ends on the earlier cuts.
        length = sum(math.hypot(run[i + 1][0] - run[i][0], run[i + 1][1] - run[i][1]) for i in range(len(run) - 1))
        turns = [_turn(run[i - 1], run[i], run[i + 1]) for i in range(1, len(run) - 1)]
        gentle = length >= min_len and (not turns or max(turns) < gentle_turn)
        if gentle:
            cand = _catmull_run(run, step)
            if _dev_to_polyline(_flatten(run[0], cand), run) <= max_dev:
                segs += cand; fitted_runs += 1; continue
        for q in run[1:]: segs.append(('line', q))
        kept_runs += 1
    return P[0], segs, fitted_runs, kept_runs


def _turn(a, b, c):
    v1 = (b[0] - a[0], b[1] - a[1]); v2 = (c[0] - b[0], c[1] - b[1])
    l1 = math.hypot(*v1); l2 = math.hypot(*v2)
    if l1 < 1e-9 or l2 < 1e-9: return 0.0
    d = max(-1.0, min(1.0, (v1[0] * v2[0] + v1[1] * v2[1]) / (l1 * l2)))
    return math.degrees(math.acos(d))
