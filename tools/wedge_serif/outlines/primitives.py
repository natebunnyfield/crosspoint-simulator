"""The designed parts every glyph is built from. Each returns a shapely
geometry (already a valid solid) or, for the edge helpers, point lists; a
glyph composes them with geom.ink(solids, cutouts), whose union IS the
join -- one outline per solid, counters as holes, nothing buried.

Widths are DECLARED here and in the glyph code, read against pen.th()
(the reference), not generated from it: `widths(keys)` interpolates the
designer's keypoints along a stroke."""
import math
from . import geom, pen
from .geom import cubic, quad, line, superellipse, join, resample, tangents, smooth
from .pen import S, CS, XH, WL, WD, DROP, FILLET, FOOT, ENT, TH_V, TH_H, HAIR, CUT

# ---------------------------------------------------------------- widths
def widths(keys):
    """keys: [(t, width), ...] with t in 0..1 ascending. Smoothstep between
    keys, held flat outside. Returns f(t)."""
    keys = sorted(keys)
    def f(t):
        if t <= keys[0][0]: return keys[0][1]
        if t >= keys[-1][0]: return keys[-1][1]
        for (t0, w0), (t1, w1) in zip(keys, keys[1:]):
            if t0 <= t <= t1:
                u = (t - t0) / (t1 - t0) if t1 > t0 else 1.0
                return w0 + (w1 - w0) * (3 * u * u - 2 * u * u * u)
        return keys[-1][1]
    return f

def pen_widths(center, profile=None, floor=0.0, scale=1.0):
    """The pen's own width along a centerline, as a width function of t --
    the reference, for reading off what to declare (and for the strokes
    that simply ARE the pen: dots, bars)."""
    tans = tangents(center); n = len(center) - 1
    def f(t):
        i = min(n, int(round(t * n))); w = pen.PEN.th(tans[i]) * scale
        if profile: w *= profile(t)
        return max(w, floor)
    return f

# ---------------------------------------------------------------- strokes
def _unfold(side, tans):
    out = [side[0]]
    for i in range(1, len(side)):
        dx, dy = side[i][0] - out[-1][0], side[i][1] - out[-1][1]
        if dx * tans[i][0] + dy * tans[i][1] >= -1e-9: out.append(side[i])
    return out

def stroke(center, width, cut0=None, cut1=None, raw=False, pieces=False, sides=False):
    """A stroke along a centerline: `width` a number or f(t). Ends are
    square faces, or sheared by cut0/cut1 (radians; the family's pen cut is
    pen.CUT). Returns a shapely solid."""
    pts = resample(center) if not raw else list(center)
    tans = tangents(pts); n = len(pts) - 1; L, R = [], []
    wf = width if callable(width) else (lambda t: width)
    for i, (p, tn) in enumerate(zip(pts, tans)):
        w = wf(i / n); nx, ny = -tn[1], tn[0]
        L.append((p[0] + nx * w / 2, p[1] + ny * w / 2)); R.append((p[0] - nx * w / 2, p[1] - ny * w / 2))
    for cut, idx, sgn in ((cut0, 0, 1), (cut1, -1, -1)):
        if cut is None: continue
        tn = tans[idx]; w = wf(0.0 if idx == 0 else 1.0); d = math.tan(cut) * w / 2 * sgn
        L[idx] = (L[idx][0] + tn[0] * d, L[idx][1] + tn[1] * d); R[idx] = (R[idx][0] - tn[0] * d, R[idx][1] - tn[1] * d)
    L = _unfold(L, tans); R = _unfold(R, tans)
    if pieces:
        # a centerline that CROSSES ITSELF (the &, the @'s ring): one polygon
        # would make holes of its crossings, so the stroke is the union of
        # short overlapping pieces, each a simple polygon
        parts = []; step = 6; n2 = min(len(L), len(R))
        for i in range(0, n2 - 1, step):
            j = min(n2, i + step + 2)
            q = L[i:j] + R[i:j][::-1]
            if len(q) >= 3: parts.append(geom.poly(q))
        return geom.union(parts)
    solid = geom.poly(L + R[::-1])
    return (solid, L, R) if sides else solid

def edge_stroke(outer, width, side=1, cut0=None, cut1=None):
    """A stroke drawn from its OUTER edge (the silhouette the designer
    draws) and a declared width toward `side` (+1 = left of travel, -1 =
    right). Returns (solid, inner_edge_points)."""
    pts = resample(outer); tans = tangents(pts); n = len(pts) - 1; inner = []
    wf = width if callable(width) else (lambda t: width)
    for i, (p, tn) in enumerate(zip(pts, tans)):
        w = wf(i / n); nx, ny = -tn[1] * side, tn[0] * side
        inner.append((p[0] + nx * w, p[1] + ny * w))
    inner = _unfold(inner, tans)
    return geom.poly(pts + inner[::-1]), inner

def offset(pts, width, side=1, closed=False):
    """Offset a curve by `width` (number or f(t)) toward `side`."""
    tans = tangents(pts, closed); n = max(1, len(pts) - 1); out = []
    wf = width if callable(width) else (lambda t: width)
    for i, (p, tn) in enumerate(zip(pts, tans)):
        w = wf(i / n); out.append((p[0] - tn[1] * side * w, p[1] + tn[0] * side * w))
    return out

# ---------------------------------------------------------------- serifs
def wedge(A, d, sd, length, depth, drop, edge_at=None, into=None, fillet=FILLET):
    """The family's bracketed wedge, as one polygon that overlaps its stem.
    A: the stem's corner at the end; d: unit direction OUT of the stem's
    end; sd: unit normal pointing out of the stem on the wedge's side.
    The apex sits `length` out along sd and `drop` back along d; the
    bracket is a concave quadratic from the apex to the stem's edge
    `depth` back, tangent to the edge there (control 0.65 of the way up
    the edge). edge_at(dist) gives the stem edge's real point `dist` back
    from A (entasis); default straight."""
    if edge_at is None: edge_at = lambda t: (A[0] - d[0] * t, A[1] - d[1] * t)
    B = (A[0] + sd[0] * length - d[0] * drop, A[1] + sd[1] * length - d[1] * drop)
    C = edge_at(depth)
    ctrl = (A[0] * fillet + C[0] * (1 - fillet), A[1] * fillet + C[1] * (1 - fillet))
    fil = quad(C, ctrl, B)
    # the polygon: down the stem's edge from A to C (real edge), then the
    # bracket out to the apex, the top edge back to A, and a strip inside
    # the stem so the union has no seam.
    inset = into if into is not None else 6.0
    edge = [edge_at(depth * i / 12) for i in range(13)]            # A .. C along the real edge
    inner = [(p[0] - sd[0] * inset, p[1] - sd[1] * inset) for p in edge]
    outline = inner + fil[1:] + [B, A]   # A'..C' inside the stem, C .. bracket .. B, the top edge back to A
    return geom.poly(outline)

# ---------------------------------------------------------------- stems
def stem_width(w0, ent, t):
    """Entasis: the ends swell by `ent` (14%), the waist stays straight --
    a quartic, so the middle 60% of the stem is within 1% of w0 and the
    swell lives in the last fifth at each end, where the brackets are. (The
    record's quadratic waisted the whole stem, visibly at 300 px.)"""
    return w0 * (1.0 + ent * (2 * t - 1) ** 4)

def stem(x, y0, y1, w=None, top=None, foot=None, ent=ENT, ent_span=None, cap=False,
         top_len=1.0, top_depth=1.0, foot_len=FOOT, foot_depth=1.0, top_drop=1.0, foot_drop=0.6,
         top_scale=1.0, cut_top=None):
    """A vertical stem from y0 to y1 with entasis, its wedges as part of the
    same solid. w: mid width (default the pen's vertical, x1.137 for cap).
    top: None | 'left' | 'right' | 'both' | 'left+' | 'right+' ('+' adds the
    small 0.4 x 0.6 wedge the other way: the I, the U's right stem).
    foot: None | 'both' | 'left' | 'right'. ent_span: (ylo, yhi) the entasis
    is computed over when the drawn stem is a piece of a longer one (the
    n's right stem ends inside its arch). cut_top: shear the top face by
    this angle (radians) instead of a square end."""
    if w is None: w = TH_V * (pen.CAP_STEM if cap else 1.0)
    lo, hi = ent_span or (y0, y1)
    def wid(y): return stem_width(w, ent, (y - lo) / (hi - lo) if hi > lo else 0.5)
    ys = [y0 + (y1 - y0) * i / geom._n(abs(y1 - y0), geom.SPACING) for i in range(geom._n(abs(y1 - y0), geom.SPACING) + 1)]
    left = [(x - wid(y) / 2, y) for y in ys]; right = [(x + wid(y) / 2, y) for y in ys]
    if cut_top is not None:
        d = math.tan(cut_top) * wid(y1) / 2
        left[-1] = (left[-1][0], y1 + d); right[-1] = (right[-1][0], y1 - d)
    body = geom.poly(left + right[::-1])
    parts = [body]
    wl = WL * (pen.CAP_STEM if False else 1.0)   # the family's wedge is one size in both cases (round 22)
    wd = WD
    def edge_fn(side, at_top):
        # the real stem edge, `dist` back from the end on `side` (-1 left, +1 right)
        def f(dist):
            y = y1 - dist if at_top else y0 + dist
            return (x + side * wid(y) / 2, y)
        return f
    if top:
        main = -1 if top in ("left", "left+", "both") else +1
        sides = [main] + ([-main] if top in ("both", "left+", "right+") else [])
        for i, sd in enumerate(sides):
            small = (top in ("left+", "right+")) and i == 1
            L_ = wl * (0.4 if small else top_len) * top_scale; D_ = wd * (0.6 if small else top_depth); dr = DROP * (0.4 if small else top_drop)
            A = (x + sd * wid(y1) / 2, y1)
            parts.append(wedge(A, (0, 1), (sd, 0), L_, D_, dr, edge_at=edge_fn(sd, True)))
    if foot:
        sides = {"both": (-1, 1), "left": (-1,), "right": (1,)}[foot]
        for sd in sides:
            A = (x + sd * wid(y0) / 2, y0)
            parts.append(wedge(A, (0, -1), (sd, 0), wl * foot_len, wd * foot_depth, DROP * foot_drop, edge_at=edge_fn(sd, False)))
    return geom.union(parts)

def stem_edge_x(x, w, ent, y, lo, hi, side):
    """x of a stem's edge at height y (entasis over lo..hi)."""
    return x + side * stem_width(w, ent, (y - lo) / (hi - lo)) / 2

def diag_wedge(p_end, d_out, sd, scale=0.9, drop=DROP):
    """The wedge at a diagonal's end (A V W X Y K k v w x y): 0.9 x 0.9 of
    the family's, on the outer side. p_end is the stroke's end CORNER on
    that side, d_out the unit direction out of the stroke's end."""
    return wedge(p_end, d_out, sd, WL * scale, WD * scale, drop)

def end_wedge(pts, w, at_start, side, scale=0.9):
    """The diagonal wedge at one end of a stroke: side +1/-1 is taken on
    the normal of the direction OUT of that end (the record's convention:
    +1 on a diagonal's top-left end points up-left)."""
    tn = tangents(pts)
    d = (-tn[0][0], -tn[0][1]) if at_start else tn[-1]
    nrm = (-d[1], d[0]); sd = (nrm[0] * side, nrm[1] * side)
    P = pts[0] if at_start else pts[-1]
    A = (P[0] + sd[0] * w / 2, P[1] + sd[1] * w / 2)
    return diag_wedge(A, d, sd, scale)

def diagonal(p0, p1, w, serif0=None, serif1=None, cut0=None, cut1=None):
    """A straight stroke p0 -> p1 of width w (number or f(t)); serif0/serif1:
    +1/-1 = a diagonal wedge at that end, on the side named as end_wedge does."""
    pts = line(p0, p1)
    wf = w if callable(w) else (lambda t: w)
    parts = [stroke(pts, wf, cut0=cut0, cut1=cut1)]
    if serif0: parts.append(end_wedge(pts, wf(0.0), True, serif0))
    if serif1: parts.append(end_wedge(pts, wf(1.0), False, serif1))
    return geom.union(parts)

def bar(x0, x1, y, w, align="center", cut0=None, cut1=None, wedges=()):
    """A horizontal bar. align: 'center' | 'top' | 'bottom' (which edge sits
    on y). wedges: [(end, side)] with end 'left'|'right' and side +1 (rising)
    or -1 (hanging) -- the bar-end wedge, 0.85 x 0.9 of the family."""
    yc = y - w / 2 if align == "top" else (y + w / 2 if align == "bottom" else y)
    pts = line((x0, yc), (x1, yc)); parts = [stroke(pts, w, cut0=cut0, cut1=cut1)]
    for end, side in wedges:
        if end == 'left': A = (x0, yc + side * w / 2); d = (-1, 0)
        else: A = (x1, yc + side * w / 2); d = (1, 0)
        parts.append(wedge(A, d, (0, side), WL * 0.85, WD * 0.9, 0.0))
    return geom.union(parts)

# ---------------------------------------------------------------- rounds
def ring(cx, cy, rx, ry, k=pen.BOWL_K, w_scale=1.0, floor=0.0, rot=0.0, counter_smooth=2, a0=0.0, a1=2 * math.pi):
    """A full bowl: the OUTER is the designed superellipse (k = squareness);
    the COUNTER is its inward offset by the pen's width at each tangent
    (x w_scale, never under `floor`), smoothed so it reads as a drawn
    curve. Carries the pen's stress: sides at the vertical width, top and
    bottom at the horizontal, thinnest at 11 and 5 o'clock. Returns
    (solid, outer_pts, inner_pts)."""
    outer = superellipse(cx, cy, rx, ry, a0, a1, k, rot=rot)[:-1]
    tans = tangents(outer, closed=True)
    inner = []
    for p, tn in zip(outer, tans):
        w = max(pen.PEN.th(tn) * w_scale, floor)
        inner.append((p[0] - tn[1] * w, p[1] + tn[0] * w))   # inward: the LEFT normal of a ccw outer
    inner = _unfold(inner, tans)
    inner = smooth(inner, counter_smooth, closed=True)
    inner = resample(inner + [inner[0]])[:-1]
    solid = geom.poly(outer, [inner[::-1]])
    return solid, outer, inner

def ring_from(outer, w_scale=1.0, floor=0.0, widths_fn=None, counter_smooth=2, post_inner=None, smooth_w=0):
    """A bowl from a DESIGNED closed outer path (ccw): the counter is the
    inward offset by the pen's width at each tangent (or widths_fn(t)),
    smoothed. Returns (solid, outer, inner)."""
    outer = resample(outer + [outer[0]])[:-1]
    tans = tangents(outer, closed=True); n = len(outer); inner = []
    ws = [widths_fn(i / n) if widths_fn else max(pen.PEN.th(tn) * w_scale, floor) for i, tn in enumerate(tans)]
    if smooth_w:   # the pen's width sequence, moving-averaged over +-smooth_w samples (a tight turn steps it)
        ws = [sum(ws[(i + k) % n] for k in range(-smooth_w, smooth_w + 1)) / (2 * smooth_w + 1) for i in range(n)]
    for i, (p, tn) in enumerate(zip(outer, tans)):
        w = ws[i]
        inner.append((p[0] - tn[1] * w, p[1] + tn[0] * w))
    inner = _unfold(inner, tans)
    if post_inner: inner = [post_inner(p) for p in inner]
    inner = smooth(inner, counter_smooth, closed=True)
    inner = resample(inner + [inner[0]])[:-1]
    return geom.poly(outer, [inner[::-1]]), outer, inner

def half_bowl(edge, y_top, y_bot, rx, k=pen.BOWL_K * 1.12, open_bottom=0.0, w_scale=1.0, into=22.0, taper=0.42, taper_span=0.10):
    """The D's bowl (rulings, rounds 36/47) as the NIB writes it (owner,
    2026-09-13: "brush stroke revision"): the CENTERLINE is the designed
    half superellipse from the stem's inner edge -- squared shoulders (k x
    1.12), outer edges ON y_top and y_bot -- and the outer and inner
    contours are its offsets by pen.th(tangent)/2 at every point: a thin
    horizontal (55) leaving the stem at the top, the full stem on the
    right with the maximum at the stress angle, thin again returning at
    the bottom. Both ends run `into` the stem and TAPER there (to `taper`
    of the pen over `taper_span`), so the end faces lie inside the stem's
    ink: no slit, no square end. The opened bottom lifts the counter's
    lower half by open_bottom x the horizontal stroke (centerline up by
    half, width up by the whole, so the outer edge holds). Returns (solid,
    cx, cy, rx_c, ry_c, L, R) with the centerline radii and the two edges."""
    ry_c = (y_top - y_bot) / 2 - TH_H / 2; rx_c = rx - TH_V / 2
    cy = (y_top + y_bot) / 2; cx = edge + rx * 0.05
    arc = superellipse(cx, cy, rx_c, ry_c, -math.pi / 2, math.pi / 2, k)
    center = [(edge - into, cy - ry_c)] + arc + [(edge - into, cy + ry_c)]
    center = resample(center)
    n = len(center) - 1
    if open_bottom:
        # the lower half is the FIRST half of this centerline (bottom -> right -> top)
        def win(t): return max(0.0, math.sin(math.pi * (t - 0.04) / 0.46)) if 0.04 <= t <= 0.50 else 0.0
        center = [(px, py + 0.5 * open_bottom * TH_H * win(i / n)) for i, (px, py) in enumerate(center)]
    tans = tangents(center)
    def wfn(t):
        i = min(n, int(round(t * n))); w = pen.PEN.th(tans[i]) * w_scale
        if open_bottom: w += open_bottom * TH_H * win(t)
        # taper into the stem at both ends
        if t < taper_span: u = t / taper_span; w *= taper + (1 - taper) * (3 * u * u - 2 * u ** 3)
        elif t > 1 - taper_span: u = (1 - t) / taper_span; w *= taper + (1 - taper) * (3 * u * u - 2 * u ** 3)
        return w
    solid, L, R = stroke(center, wfn, raw=True, sides=True)
    return solid, cx, cy, rx_c, ry_c, L, R

def beak(pts, w, at_start=True, cut_deg=-28.0, lip=(0.4, 0.7)):
    """The C/G/S beak (round 42, Van den Keere): the terminal's face is
    sheared toward the vertical and a SHORT lip hangs from the face's inner
    corner into the aperture -- a bracket wedge at 0.4 x 0.7 of the family.
    Returns the lip polygon; the caller shears the face with the same cut."""
    tn = tangents(pts)
    d = (-tn[0][0], -tn[0][1]) if at_start else tn[-1]
    nrm = (-d[1], d[0]); P = pts[0] if at_start else pts[-1]
    dd = math.tan(math.radians(cut_deg)) * w / 2
    # the face's inner corner after the cut (stroke() moves L forward, R back at the start)
    P0 = (P[0] - d[0] * dd, P[1] - d[1] * dd)
    A = (P0[0] - nrm[0] * w / 2, P0[1] - nrm[1] * w / 2)
    return wedge(A, d, (-nrm[0], -nrm[1]), WL * lip[0], WD * lip[1], 0.0)

def dot(cx, cy, r, k=2.0):
    return geom.poly(superellipse(cx, cy, r, r, 0, 2 * math.pi, k)[:-1])

# ---------------------------------------------------------------- traps
def trap(apex, direction, half_deg, depth):
    """An ink trap: a V cut into the ink with its apex at `apex`, opening
    along `direction` (unit, pointing OUT of the ink into the crotch's
    air), `depth` deep. Subtract it (geom.ink cutouts)."""
    dx, dy = direction; a = math.radians(half_deg)
    tip = (apex[0] - dx * depth, apex[1] - dy * depth)
    far = depth * 2.2 / math.cos(a)   # the V reaches only a little past the apex into the air
    e1 = (dx * math.cos(a) - dy * math.sin(a), dx * math.sin(a) + dy * math.cos(a))
    e2 = (dx * math.cos(a) + dy * math.sin(a), -dx * math.sin(a) + dy * math.cos(a))
    return geom.poly([tip, (tip[0] + e1[0] * far, tip[1] + e1[1] * far), (tip[0] + e2[0] * far, tip[1] + e2[1] * far)])
