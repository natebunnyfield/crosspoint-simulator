"""Curves as sampled point lists, and the union of polygons (shapely).

Everything is in font units, y up. Curves are sampled at SPACING units of
arc length -- the same density the round-17 pen used (one sample per ~11
units, one vertex in four kept by the cut, facets of ~45 units), so the
cut's texture matches the record."""
import math
import os
import numpy as np
import shapely
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union

SPACING = 11.0

# ROUND 291 -- the Douglas-Peucker tolerance `close_corners` puts its result
# back through, in font units. See that function: a round buffer triples the
# point count of a polyline it is handed, and the sub-unit segments it leaves
# are what the em grid turns into stair-steps and hairs. A tenth of a unit is
# a ten-thousandth of the em and rather better than the 0.076 units of sagitta
# an 11-unit chord already carries across a 200-unit bowl, so the simplify
# cannot be the largest error in the outline.
CLOSE_TOL = float(os.environ.get("ALBO_CLOSE_TOL", 0.10))

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

    ROUND 291 -- AND THEN PUT THE POINT TEXTURE BACK. Owner 2026-09-19:
    *"bold italic 700 has errors and glitches and fractures and hairs"*, then
    *"italic has some hairs and stray lines."* The closing was the mechanism
    for the two worst letters. A round buffer lays a fan of `segs` points per
    quadrant against EVERY vertex of its input, and the input here is already
    a dense polyline at `SPACING`, so the dilate-erode pair came back with
    three times the points it was handed, nearly all of them a fraction of a
    unit apart: the `s` left with 338 points of which 222 sat under two units
    and 52 were exact duplicates, the `g` with 841 of which 527 and 236. The
    shape was right to a fifth of a percent of its area and the POINT STREAM
    was ruined, which costs twice over --

      the exporter rounds to the integer em grid, and a run of 0.3-unit
      segments rounds into duplicate points and one-unit stair-steps, which
      is the faceting and the fractures he can see; and

      `fit_curves` reads the turn between consecutive segments to find a
      contour's corners, and on a 0.3-unit segment that angle is noise -- so
      every vertex read as a corner, no run was ever fitted, and these two
      letters exported as raw polygons while the rest of the face got curves.

    Douglas-Peucker at `CLOSE_TOL` restores the texture. It is the right tool
    rather than a resample because it cannot cut a corner: the recursion
    always keeps the point of greatest deviation, so a wedge tip and a finial
    cut survive exactly while a fan of near-collinear points collapses. The
    tolerance is the whole guarantee -- every point of the result lies within
    CLOSE_TOL units of the closed outline, a ten-thousandth of the em, which
    is a thousandth of a pixel at the 13 px the face is read at. Measured on
    the built italics: the `s` 338 points -> 131 with no segment under two
    units, the `g` 841 -> 354 with 27, and the area moved by 0.02%.

    ALBO_CLOSE_TOL=0 is the old dense polygon, byte for byte.
    """
    if not r or r <= 0:
        return g
    out = _largest(g.buffer(r, join_style=1, quad_segs=segs)
                    .buffer(-r, join_style=1, quad_segs=segs))
    if CLOSE_TOL > 0 and not out.is_empty:
        out = _largest(out.simplify(CLOSE_TOL, preserve_topology=True))
    return out


WELD_WIDTH = float(os.environ.get("ALBO_WELD_WIDTH", 8.0))
WELD_MIN_LEN = float(os.environ.get("ALBO_WELD_MIN_LEN", 12.0))
WELD_MAX_AREA = float(os.environ.get("ALBO_WELD_MAX_AREA", 120.0))
WELD_SKIP = int(os.environ.get("ALBO_WELD_SKIP", 2))
WELD_TURN = float(os.environ.get("ALBO_WELD_TURN", 140.0))


def weld_slivers(pts, width=None, min_len=None, max_area=None, skip=None):
    """ROUND 291 -- WELD THE CRACKS A UNION LEAVES AT A SHALLOW JUNCTION.

    Owner 2026-09-19: *"bold italic 700 has errors and glitches and fractures
    and hairs"*, and then of the 400, *"italic has some hairs and stray
    lines."* Two of the three words are this. `ink` ADDS strokes, and where
    two of them meet at a shallow angle the boolean's boundary runs out along
    one stroke's edge and straight back along the other's, leaving a tapering
    hairline of WHITE driven into solid ink. Measured on the built italic:
    the `x`'s upper join carries a slit 18 units long closing to 1.0, the
    `y`'s tail join one 18 long and 4.7 wide. Both show plainly in FreeType at
    a large size, which is where he found them; at 13 px they are a quarter of
    a pixel of gray and invisible, which is why sixteen rounds of reading-size
    proofs never caught one.

    This splices across such an excursion. A crack qualifies only when ALL of

      * it is at most `skip` vertices long -- one or two points, a tip;
      * its two ends close to within `width` units;
      * the path being removed is at least `min_len` units, so an ordinary
        corner between two 11-unit facets can never qualify; and
      * the area recovered is under `max_area`, so nothing with a shape in it
        can be welded away by accident.

    THE DESIGNED HAIRLINE GAP IS SAFE, and that is the reason for the vertex
    count rather than a width alone. The Y's and the P's gap
    (`docs/albo-hairline-gap.md`) is about EIGHT units wide -- the same order
    as these cracks -- but it is held within a unit of that width over 0.04 to
    0.10 of the cap, 27 to 67 units, which at this project's 11-unit sampling
    is three to six vertices down each flank. A crack is one or two. A
    parallel-sided gap the owner named and made a feature of cannot be reached
    by a two-vertex splice; a taper that closes to nothing can.

    It does NOT touch the one-unit jogs the integer grid leaves on a shallow
    edge -- the `e`'s and the `m`'s, whose removed path is 6 units against the
    12 required. Those are the honest resolution of an 11-unit polygon rounded
    to a 1000-unit em (`ALBO_CURVES` has been 0 since round 231), they are on
    every letter in the face, and chasing them would be chasing the grid.

    ALBO_WELD_WIDTH=0 turns the whole pass off.
    """
    width = WELD_WIDTH if width is None else width
    min_len = WELD_MIN_LEN if min_len is None else min_len
    max_area = WELD_MAX_AREA if max_area is None else max_area
    skip = WELD_SKIP if skip is None else skip
    if width <= 0 or len(pts) < 6:
        return list(pts), 0
    P = [(float(x), float(y)) for x, y in pts]
    welds = 0
    changed = True
    while changed and len(P) >= 8:
        changed = False
        n = len(P)
        for i in range(n):
            for k in range(1, skip + 1):
                if n - k < 6:
                    continue
                run = [P[(i + t) % n] for t in range(k + 2)]     # i, the k tip points, and j
                if math.dist(run[0], run[-1]) > width:
                    continue
                L = sum(math.dist(run[t], run[t + 1]) for t in range(len(run) - 1))
                sa = signed_area(run)
                if L < min_len or abs(sa) > max_area:
                    continue
                # IT MAY ONLY ADD INK. A ring's area changes by -signed_area
                # of the spliced run, and a ring's area IS its contribution to
                # the ink whichever way it is wound, so sa < 0 is exactly "this
                # weld fills something". The other sign is a SHAVE -- ink the
                # drawing put there -- and shaving is a drawing decision, not a
                # repair: with it allowed, the pass took eight units off the
                # italic 6's entry terminal and nicked the 9's tail, which are
                # the two places in the face where a stroke deliberately runs
                # out to a point. Measured, every weld that survives this test
                # adds between 0.005% and 0.2% of its glyph's area.
                if sa >= 0:
                    continue
                # ...AND THE ARMS MUST DOUBLE BACK. This is the condition that
                # separates a crack from a corner, and without it the pass
                # shaved serif tips: the `l`'s foot and its ascender top both
                # qualified on width, length and area, because a wedge tip
                # between two 11-unit facets is narrow and long too. A crack
                # leaves along one edge and returns along the other, so its
                # first and last segments are nearly antiparallel; a tip's
                # are not.
                v1 = (run[1][0] - run[0][0], run[1][1] - run[0][1])
                v2 = (run[-1][0] - run[-2][0], run[-1][1] - run[-2][1])
                l1 = math.hypot(*v1); l2 = math.hypot(*v2)
                if l1 < 1e-9 or l2 < 1e-9:
                    continue
                d = max(-1.0, min(1.0, (v1[0] * v2[0] + v1[1] * v2[1]) / (l1 * l2)))
                if math.degrees(math.acos(d)) < WELD_TURN:
                    continue
                drop = {(i + t) % n for t in range(1, k + 1)}
                P = [p for t, p in enumerate(P) if t not in drop]
                welds += 1
                changed = True
                break
            if changed:
                break
    return P, welds


WELDS = [0]        # how many cracks the last build spliced -- printed by build.py


DESPIKE_ARM = float(os.environ.get("ALBO_DESPIKE_ARM", 6.0))    # the longest arm a spike may have, units
DESPIKE_TURN = float(os.environ.get("ALBO_DESPIKE_TURN", 150.0))  # the turn that makes one, degrees
DESPIKE_DEV = float(os.environ.get("ALBO_DESPIKE_DEV", 0.0))      # the shallow-spur pass, OFF by measurement -- see pass 2; 1.8 was the tolerance the letters wanted
# ROUND 297 -- 2.5 -> 3.0. Round 295 picked 2.5 without a case at the boundary
# to test it against; round 297's v/w/y terminals produced one. The BoldItalic
# w exports ... (412,107) (410,103) (410,105) ... -- a two-unit spur the grid
# left, whose neighbors are 2.83 apart, so the 2.5 limit skipped it by a third
# of a unit and the hair gate read 153.4 degrees. The SAME spur is in the
# shipped drawing at (413,107), where the arm is 5.0 rather than 4.47 and the
# turn falls just under the gate's 150: latent grid noise, not a new fault, and
# a one-unit shift anywhere would have tripped it.
#
# MEASURED BEFORE CHANGING IT, because round 295 records three tolerance rules
# that each ate the arrows. Across all six shipped fonts, 2.5 -> 3.0 removes
# SEVENTEEN points -- 2 to 4 per font, 2 to 4 glyphs touched -- total ink moves
# by +0.0000%, NO arrow moves at all, and the only glyph whose area moves by
# more than a hundredth of a percent is the ExtraLight's currency sign, by 3
# units of 29,099 (+0.010%). Hair findings: the BoldItalic 2 -> 1, every other
# font unchanged. It touches all six point streams and is taken under the
# owner's standing "Chase them to zero first" (2026-09-20).
DESPIKE_CHORD = float(os.environ.get("ALBO_DESPIKE_CHORD", 3.0)) # or: the neighbors this close together mean the contour doubled back


def despike(q, arm=None, turn=None, dev=None, chord_lim=None):
    """ROUND 295 -- the spikes the INTEGER GRID leaves, removed at export.

    Owner 2026-09-20, having ruled that the contour-hair gate is to go green
    rather than carry an exemption table: *"Chase them to zero first."* The 33
    findings across the six fonts share one shape -- a turn past 150 degrees
    with one arm of a single unit or a few, very often an exact 180 -- and
    they are not drawing faults. `build` writes each contour by ROUNDING a
    dense polyline to the em grid, and rounding a run of points that are a
    fraction of a unit apart lands two of them on the same integer, or lands
    one a unit to the wrong side of its neighbours. That is a spike with
    1-unit arms, in a letter whose drawing is clean.

    So it is cured where it is made. Consecutive duplicates go first (a
    zero-length segment has no direction, which is what made the earlier
    detector report 9 reversals in the italic s that did not exist), then any
    vertex whose turn exceeds `turn` with its shorter arm under `arm` -- but
    only while the vertex sits within `dev` of the chord between its two
    neighbours, which is what keeps a real corner.

    THE TWO GUARDS ARE ALTERNATIVES, and getting them right took three cuts.

    Bounding the DEVIATION alone lets through the pure spike, where a vertex's
    two neighbours land on the SAME integer: the chord is then zero, the
    deviation infinite, and the Regular e's 1-unit 180-degree spur survives.
    So the second guard asks whether the contour has doubled back -- whether
    the neighbours sit within `chord_lim` of each other -- which is what a
    spike is.

    Bounding the INK instead, which was the first cut, is what must NOT be
    done, and the ExtraLight's arrows are why: at that weight an arrow's tip
    is a real corner holding only a few square units, so an area guard eats
    it. Measured, `arrowboth` lost 4.1% of itself under a 12-unit area bound
    while the letters it was meant to help barely moved. A corner is thin, not
    small.

    A wedge tip fails both tests -- its neighbours are tens of units apart and
    it stands tens of units off their chord -- and the Y's and P's designed
    hairline gap is between two contours, which is not reachable from inside
    one.
    """
    arm = DESPIKE_ARM if arm is None else arm
    turn = DESPIKE_TURN if turn is None else turn
    dev = DESPIKE_DEV if dev is None else dev
    chord_lim = DESPIKE_CHORD if chord_lim is None else chord_lim
    cos_lim = math.cos(math.radians(180.0 - turn))
    pts = [p for i, p in enumerate(q) if p != q[i - 1]]      # duplicates, wrap included
    if len(pts) < 4: return pts

    def geom_at(seq, i):
        a, b, c = seq[i - 1], seq[i], seq[(i + 1) % len(seq)]
        ax, ay = a[0] - b[0], a[1] - b[1]
        cx, cy = c[0] - b[0], c[1] - b[1]
        la = math.hypot(ax, ay); lc = math.hypot(cx, cy)
        if la < 1e-9 or lc < 1e-9: return None
        if min(la, lc) > arm: return None
        if (ax * cx + ay * cy) / (la * lc) < cos_lim: return None
        return abs(ax * cy - ay * cx), math.hypot(a[0] - c[0], a[1] - c[1])

    # PASS 1 -- the pure spikes, iterated. The contour has doubled back on
    # itself, so removing one can expose the next, and none of this moves the
    # drawing: the two neighbours are within `chord_lim` of each other.
    changed = True
    while changed and len(pts) > 3:
        changed = False
        for i in range(len(pts)):
            g = geom_at(pts, i)
            if g is None: continue
            if g[1] > chord_lim: continue
            del pts[i]; changed = True; break

    # PASS 2 -- the shallow spurs, ONE sweep and never two in a row.
    # ITERATING THIS IS THE TRAP: each removal is within `dev` of its own
    # local chord, but the chords move with it, so a long edge drifts a little
    # further every pass. Measured, that is what ate the ExtraLight's arrows
    # -- `arrowboth` GAINED 4.1% of its area, its concave notches flattened
    # out, while the guard looked innocent at 1.8 units a step. One sweep over
    # fixed geometry, skipping the neighbour of anything removed, cannot drift.
    if len(pts) > 3:
        drop = set(); i = 0
        while i < len(pts):
            g = geom_at(pts, i)
            if g is not None and g[1] > 1e-9 and g[0] / g[1] <= dev:
                drop.add(i); i += 2           # never the vertex next door
            else:
                i += 1
        if drop and len(pts) - len(drop) >= 3:
            pts = [p for i, p in enumerate(pts) if i not in drop]
    return pts


def contours(g, min_area=40.0, weld=True):
    """[(points, is_hole)] with exteriors wound CCW (positive area) and holes
    CW -- the nonzero winding TrueType wants. Tiny slivers are dropped, and
    since round 291 the cracks a shallow union leaves are welded shut (see
    `weld_slivers`)."""
    out = []
    polys = [g] if g.geom_type == 'Polygon' else [p for p in getattr(g, 'geoms', []) if p.geom_type == 'Polygon']
    for p in polys:
        if p.area < min_area: continue
        ext = list(p.exterior.coords)[:-1]
        if signed_area(ext) < 0: ext = ext[::-1]
        if weld:
            ext, w = weld_slivers(ext); WELDS[0] += w
        out.append((ext, False))
        for r in p.interiors:
            h = list(r.coords)[:-1]
            if abs(signed_area(h)) < min_area: continue
            if signed_area(h) > 0: h = h[::-1]
            if weld:
                h, w = weld_slivers(h); WELDS[0] += w
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
    `window` neighbors on each side, `passes` times. A wedge's tip, a
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

def fit_curves(pts, turn=28.0, step=3, max_dev=2.0, min_len=30.0, gentle_turn=28.0, clearance=28.0, obstacles=None):
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
        # ROUND 231 -- THE CLEARANCE GUARD. The pinches of the earlier cuts
        # were all at hairline tips, where a run's overshoot met the contour's
        # other side. A run whose points come within `clearance` units of any
        # OTHER part of its contour is left as the polygon; a bowl's or an
        # arch's side has hundreds of units of counter beside it and is fitted.
        if gentle and clearance > 0:
            # the two ADJACENT runs meet this one at a shared corner and are
            # 11 units away there by construction -- that is not a pinch, so
            # they are left out; every other run of the contour is checked
            ri = runs.index(run); nr = len(runs)
            others = [q for j, r2 in enumerate(runs) if j not in (ri, (ri - 1) % nr, (ri + 1) % nr) for q in r2[1:-1]]
            # ...and the glyph's OTHER contours: a counter is its own contour,
            # and the roman 4's closed to 1.9 units when the guard saw only
            # the run's own ring
            if obstacles: others = others + list(obstacles)
            if others:
                import numpy as _np
                O = _np.array(others, float); R = _np.array(run[1:-1] if len(run) > 3 else run, float)
                d2 = ((R[:, None, 0] - O[None, :, 0]) ** 2 + (R[:, None, 1] - O[None, :, 1]) ** 2).min(axis=1)
                if float(_np.sqrt(d2.min())) < clearance: gentle = False
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


# ROUND 296 -- THE MICRO-EDGES THE INK SPREAD IS HANDED AND THE ONES IT MAKES.
# `build.draw` finishes every glyph with a 1.2-unit MITRE dilation, and that one
# call is where most of the contour-hair gate's surviving letter findings are
# born. See `collapse_micro`.
MICRO_TOL = float(os.environ.get("ALBO_MICRO_TOL", 1.0))     # one unit of the em: the grid the exporter rounds to
COLLINEAR_TOL = float(os.environ.get("ALBO_COLLINEAR_TOL", 0.02))


def collapse_micro(g, tol=None):
    """Drop every vertex that sits within `tol` of the last vertex KEPT before
    it, on every ring of a polygonal geometry.

    ROUND 296. `build.draw` ends with `g.buffer(1.2, join_style=2)` -- the
    record's ink spread -- and an offsetter cannot say anything true about a
    feature finer than the distance it is offsetting by. Two things go wrong
    there and between them they account for most of the contour-hair gate's
    letter findings:

      * ITS INPUT carries exact duplicates and sub-unit edges. `wedge()` ends
        its outline `fil[1:] + [B, A]`, and `fil` already ends at B, so every
        wedge in the face repeats its apex; a union of two parts that share a
        corner exactly repeats that corner as well. A zero-length edge has no
        direction, so the offset normal at it is arbitrary, and the ExtraLight
        v's top-left serif came back with a 2.8-unit horizontal spur standing
        off a face that is one straight line in the drawing.

      * ITS OUTPUT carries them at a shallow CONCAVE corner, where the two
        offset edges are near-antiparallel and their intersection is a pair of
        vertices a fraction of a unit apart rather than one. That is the w's
        and the W's crotch, and the M's.

    So the ink spread is cleaned on both sides. THE RULE MOVES NO POINT: a
    vertex is either kept exactly where it is or removed, and a removed vertex
    lies within `tol` of a vertex that was kept, so no excursion larger than a
    `tol` disk can be taken out. That is the property round 295's shallow-spur
    pass could not have -- it compared each vertex to a chord that MOVED as its
    neighbors were removed, which is how an iterated sweep drifted and
    flattened the arrows' notches. Here the comparison is always against a
    retained point, so there is nothing to drift along.

    It is NOT a simplifier and must not become one. ONE UNIT is the whole
    argument for the number: it is the grid the exporter rounds to, so nothing
    it can reach survives into the font anyway, and it is under the 1.2 units
    the very next operation offsets by. A wedge tip, an arrow's point and the
    designed hairline gap are all tens of units across and are not reachable
    -- measured, `arrowboth` moves 0.511% of its area and `arrowright` 0.181%,
    against the 4.1% and 2.9% the three rules round 295 rejected cost them.
    ALBO_MICRO_TOL=0 turns it off.
    """
    tol = MICRO_TOL if tol is None else tol
    if tol <= 0 or g.is_empty: return g

    def clean(ring):
        out = []
        for p in ring:
            if not out or math.dist(out[-1], p) > tol: out.append(p)
        while len(out) > 2 and math.dist(out[0], out[-1]) <= tol: out.pop()
        # A RING THAT COLLAPSES IS KEPT, NOT DROPPED. Adversarial review
        # 2026-09-20: a ring every one of whose vertices is within tol of the
        # last is not a micro-EDGE, it is a whole sliver -- and it can be 100
        # units long and still qualify, because the rule chains. Returning it
        # short would have the caller drop the polygon or the hole outright,
        # which is a valid result, so `res.is_valid` below cannot see it. On
        # the six fonts it fires on three holes (the a, the feminine ordinal
        # and the ae), each 0.08 x 0.33 units and 0.02 of area, which
        # `contours(min_area=40)` drops anyway -- but latent and ungated is
        # not the same as absent.
        return out if len(out) >= 3 else list(ring)

    polys = [g] if g.geom_type == 'Polygon' else [p for p in getattr(g, 'geoms', []) if p.geom_type == 'Polygon']
    out = []
    for p in polys:
        ext = clean(list(p.exterior.coords)[:-1])
        if len(ext) < 3: continue                      # cannot happen: clean() keeps the ring
        holes = [h for h in (clean(list(r.coords)[:-1]) for r in p.interiors) if len(h) >= 3]
        out.append(Polygon(ext, holes))
    if not out: return g
    res = out[0] if len(out) == 1 else MultiPolygon(out)
    # the POLYGON-level guard: a hole brought against its exterior would make an
    # invalid shape. Nothing in the six fonts does. It cannot see a ring that
    # vanished, which is why `clean` refuses to let one -- see there.
    return res if res.is_valid else g


def drop_collinear(pts, tol=None):
    """A forward sweep at a fiftieth of a unit: the vertices that lie ON the
    line they are in the middle of, and nothing else.

    ROUND 296, and the other half of the CROTCH fault. Where two diagonals
    meet -- the w's and the W's inner vertex, the m's arch against its stem --
    the union's boundary arrives at the crotch along one straight run and
    leaves along another, and the ink spread's offset lands its intersection a
    few units short of the nearest vertex on each run. The corner is then a
    real 150-degree crotch with a 3-unit arm on it, which is exactly the
    signature `cmp_contour_hairs` calls a HAIR: "a drawn corner has two long
    arms, a spike has one arm a unit or two long." Here both are true at once
    -- the corner is drawn AND its arms are short -- because the vertex NEXT
    to the crotch is redundant. Measured on the Black w's crotch, that
    neighbor stands 0.0006 units off the chord through it: it is ON the line
    it is in the middle of, and dropping it merges the stub into the 11-unit
    facet beyond, so the crotch reads with the arms it actually has.

    THE TOLERANCE IS THE WHOLE ARGUMENT AND IT IS NOT A SIMPLIFIER'S. A
    fiftieth of a unit is two hundred-thousandths of the em, and a quarter of
    the 0.076 units of sagitta an 11-unit chord already carries across a
    200-unit bowl -- so no sampled curve is reachable: at the Regular the roman
    o and 0 keep all 230 and 231 of their points, the s loses 3 of 180 and the
    8 one of 300, while the M goes from 466 to 59 and the W from 470 to 48,
    because those letters are straight lines that were being written as
    11-unit facets and rounded into a staircase. The ExtraLight em
    dash shipped as 148 points along two straight edges, stepping 207, 208,
    208, 208, 209; it is four points now.

    IT CARRIES DOUGLAS-PEUCKER'S BOUND WITHOUT ITS ANCHORS, and that is why it
    is written out rather than handed to `shapely.simplify`. Every point
    dropped is re-checked against the chord that will replace it, so a run of
    them cannot bow away from the line a little at a time -- the drift round
    295's iterated pass could not rule out. But DP picks the point FARTHEST
    from a chord as a split and keeps it whatever it is, and at a crotch the
    vertex beside the corner is exactly that point: measured on the Black w,
    DP at this tolerance merged the run on one side of the crotch into 265
    units and kept a 2.0-unit stub on the other, because its recursion had
    made that stub an anchor.

    A local rule -- walk out from each sharp corner, drop the neighbor within
    a hundredth of its own chord -- was built and measured and is WORSE: 20
    findings against this pass's 6, because the crotch it is aimed at turns
    149.9 degrees and sits under any threshold that does not also admit half
    the letter. Recorded so it is not built again.

    IT RUNS AT EXPORT, after `fit` and never inside `draw`. The Aldine fitter
    reads its bearings off the vertices whose ROUNDED y falls in the x-height
    band (`fit_aldine`, and the q's tail is why), so dropping a vertex that
    happens to sit on the band's edge moves a bearing by whatever that vertex
    was holding. Measured with this pass inside draw(): the ExtraLight four
    came out 349 wide against 444 and the seven 470 against 402, which put 35
    more pairs on cmp_touch's TOUCHING list and took cmp_figure_space's roman
    spread to 2.57x, over its 2.50x. The fitter now sees every vertex it
    always saw and only the written outline is decimated.

    ALBO_COLLINEAR_TOL=0 turns it off.
    """
    tol = COLLINEAR_TOL if tol is None else tol
    if tol <= 0 or len(pts) < 6: return list(pts)

    def dev(a, b, c):
        """How far b lies off the chord a -> c."""
        L = math.hypot(c[0] - a[0], c[1] - a[1])
        if L < 1e-12: return math.dist(a, b)
        return abs((c[0] - a[0]) * (a[1] - b[1]) - (a[0] - b[0]) * (c[1] - a[1])) / L

    P = list(pts)
    out = [P[0]]
    run = []            # the points already dropped since out[-1]
    first_run = None    # ... and the ones dropped between out[0] and out[1]
    hold = None         # the point being held, which the next one may drop
    for p in P[1:] + [P[0]]:
        if hold is None: hold = p; continue
        if all(dev(out[-1], q, p) <= tol for q in run + [hold]):
            run.append(hold)                      # every dropped point is within tol of the NEW chord
        else:
            if len(out) == 1: first_run = list(run)
            out.append(hold); run = []
        hold = p
    # THE SEAM. pts[0] is wherever the ring happened to start and it is kept by
    # construction, so it is tested last -- but the points already dropped on
    # either side of it were measured against chords that ENDED or BEGAN at it,
    # and popping it moves their chord. Adversarial review 2026-09-20 measured
    # the version that popped without re-checking: 0.0289 units off the final
    # chord against a tol of 0.02, on the yen sign. So they are re-checked, and
    # the bound is tol everywhere on the ring rather than tol and 2 tol.
    if len(out) > 2 and first_run is not None:
        seam = run + [out[0]] + first_run
        if all(dev(out[-1], q, out[1]) <= tol for q in seam): out.pop(0)
    return out if len(out) >= 3 else list(pts)
