"""The designed parts every glyph is built from. Each returns a shapely
geometry (already a valid solid) or, for the edge helpers, point lists; a
glyph composes them with geom.ink(solids, cutouts), whose union IS the
join -- one outline per solid, counters as holes, nothing buried.

Widths are DECLARED here and in the glyph code, read against pen.th()
(the reference), not generated from it: `widths(keys)` interpolates the
designer's keypoints along a stroke."""
import os, math
from . import geom, pen
from .geom import cubic, quad, line, superellipse, join, resample, tangents, smooth
from .pen import S, CS, XH, WL, WD, DROP, FILLET, FOOT, ENT, TH_V, TH_H, HAIR, CUT

# ---------------------------------------------------------------- life
# Owner 2026-09-13, on the variety audit (129 of 144 serifs byte-identical
# twins): "alter anything identical very slightly so they render the same
# at small scale, but are full of life at large scale." Every wedge and
# every ring takes a small deterministic perturbation keyed on the glyph
# being drawn and the order of the call within it -- never on geometry, so
# the variable font's masters get the same perturbation and stay
# compatible. LIFE is the amplitude: 0.06 = +-6% on a wedge's length and
# depth, +-10% on its drop and fillet, +-0.06 on a ring's superellipse
# exponent and +-0.6 deg of rotation. At 54 px a wedge is 3.5 x 7 px, so
# 6% is a fifth of a pixel: the four-level render does not move; at 400 px
# it is 4 units, a visible difference of hand. FJORD_LIFE=0 switches it off.
LIFE = float(os.environ.get("FJORD_LIFE", 0.06))
_life = {"glyph": None, "n": 0}
def begin_glyph(name):
    """build.draw calls this before drawing a glyph; resets the call count."""
    _life["glyph"] = name; _life["n"] = 0
def life(k=3):
    """k deterministic values in [-1, 1] for the next serif/counter of the
    current glyph (a small LCG over a hash of (glyph, index))."""
    if not LIFE or _life["glyph"] is None: return [0.0] * k
    _life["n"] += 1
    x = 0
    for ch in "%s#%d" % (_life["glyph"], _life["n"]): x = (x * 131 + ord(ch)) & 0xFFFFFFFF
    out = []
    for _ in range(k):
        x = (x * 1103515245 + 12345) & 0x7FFFFFFF
        out.append((x >> 8) / float(1 << 23) * 2 - 1)
    return out

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
    u1, u2, u3, u4 = life(4)
    length *= 1 + LIFE * u1; depth *= 1 + LIFE * u2; drop *= 1 + 1.7 * LIFE * u3; fillet *= 1 + 1.7 * LIFE * u4
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
        # the bar's end face is sheared by cut0/cut1 (stroke() moves the
        # top corner back and the bottom corner forward by tan(cut) x w/2),
        # so the wedge must start at the SHEARED corner -- at the plain
        # corner its flat top overran the face and left a notch (owner,
        # 2026-09-13, "fix these weird glitches", on the variety audit's
        # bar-end blocks of E F L Z 2).
        if end == 'left':
            sh = math.tan(cut0) * w / 2 if cut0 is not None else 0.0
            A = (x0 + side * sh, yc + side * w / 2); d = (-1, 0)
        else:
            sh = math.tan(cut1) * w / 2 if cut1 is not None else 0.0
            A = (x1 - side * sh, yc + side * w / 2); d = (1, 0)
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
    u1, u2 = life(2)
    k = k * (1 + LIFE * u1); rot = rot + math.radians(10 * LIFE * u2)
    outer = superellipse(cx, cy, rx, ry, a0, a1, k, rot=rot)[:-1]
    tans = tangents(outer, closed=True)
    inner = []
    for p, tn in zip(outer, tans):
        w = max(bowl_th(tn) * w_scale, floor)
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

BOWL_HAIR, BOWL_MAX, BOWL_POW = 0.42, 1.18, 1.7    # round 57's D-family profile, fitted to Van den Keere's rays (kept for the record; the shipping font)
# Round 58 (owner: "a wedge serif like Albertus, but more readable" -- not
# Van den Keere): the bowl profile is a SWITCH. None = the pen (the 26-degree
# nib, round 56's bowls); a dict = a vertically stressed profile applied to
# EVERY bowl (D B P R, O Q C G, o c e b d p q g): hair and max over the stem,
# the exponent, the taper of a bowl's ends into its stem (x the hair), the
# round end's superellipse exponent, and for variant C the free terminals'
# widening (fraction, span) into the family's cut.
DEFAULT_BOWL = 'B'   # owner's pick, round 58 (2026-09-13): 'Albertus-like firm'; the family is Albo from this round
BOWL_OPTIONS = {
    'A': dict(name='Albertus-like moderate', hair=0.62, max=1.02, pow=1.4, taper=0.75, k=2.0, widen=None),
    'B': dict(name='Albertus-like firm', hair=0.70, max=1.00, pow=1.6, taper=0.85, k=1.9, widen=None),
    'C': dict(name='Glyphic near-monoline', hair=0.78, max=0.98, pow=2.0, taper=0.90, k=2.0, widen=(0.15, 0.12)),
    'D': dict(name='Albertus-measured', hair=0.75, max=1.05, pow=1.5, taper=0.85, k=2.0, widen=None, stress=20.0, arch_floor=1.0),
    'VDK': dict(name='round 57, Van den Keere fit', hair=0.42, max=1.18, pow=1.7, taper=0.7, k=2.0, widen=None),
}
# 'stress': degrees the profile's maximum sits above 3 o'clock (Albertus's O
# peaks at +20); 'arch_floor': the n m h u arches never thin below this x stem.

def bowl_hair():
    """The current bowl profile's thin, in units (the waist bar of the B)."""
    return S * (BOWL['hair'] if BOWL else BOWL_HAIR)
def set_bowl(key):
    """None = the ruled default (B); 'pen' = the 26-degree nib at each tangent (round 56)."""
    global BOWL
    BOWL = None if key == 'pen' else dict(BOWL_OPTIONS[DEFAULT_BOWL if key is None else key])
BOWL = dict(BOWL_OPTIONS[DEFAULT_BOWL])
if os.environ.get('FJORD_ARCH_FLOOR'): BOWL['arch_floor'] = float(os.environ['FJORD_ARCH_FLOOR'])   # round 60 ladder override: the n m h u arches never thin below this x stem
# The bowl hair follows the contrast (round 61's rule, applied at the
# default too since round 63): hair fraction 1 - 0.5 c -- B's own 0.70 at
# the 0.60 it was picked at, 0.60 at 0.80, 0.525 at 0.95, 0.50 at 1.00; the
# max unchanged.
BOWL['hair'] = 1.0 - 0.5 * pen.CONTRAST

def bowl_th(tn):
    """Width of a bowl stroke at tangent tn: the switched profile, or the pen."""
    if BOWL is None: return pen.PEN.th(tn)
    phi = math.atan2(tn[1], tn[0]) - math.radians(BOWL.get('stress', 0.0))
    return S * (BOWL['hair'] + (BOWL['max'] - BOWL['hair']) * abs(math.sin(phi)) ** BOWL['pow'])

def bowl_widths(center, profile=None, floor=0.0):
    """Like pen_widths, on the bowl profile (the pen when none is set)."""
    tans = tangents(center); n = len(center) - 1
    def f(t):
        i = min(n, int(round(t * n))); w = bowl_th(tans[i])
        if profile: w *= profile(t)
        return max(w, floor)
    return f

def widen_terminal(profile_fn, at_start=False):
    """Variant C: a free terminal widens 15% over its last 12% (first 12% if
    at_start) into the family's cut. Returns the composed profile."""
    if BOWL is None or not BOWL.get('widen'): return profile_fn
    amt, span = BOWL['widen']
    def f(t):
        u = (t if not at_start else 1 - t)
        w = profile_fn(t) if profile_fn else 1.0
        if u > 1 - span: v = (u - (1 - span)) / span; w *= 1 + amt * (3 * v * v - 2 * v ** 3)
        return w
    return f
BOWL_ARC = 1.0     # the round end's x radius over the bowl's half height (a semicircle); a 12-cell grid over 0.65-1.0 x exponent 1.28-2.2 against VdK's D P R rays put 1.0 / 1.7 best (sum |delta| 141 of 27 cells)
BOWL_ARC_K = 2.0   # the end is a true round; the "squared shoulders" are the flat runs

def bowl_profile(tan):
    """Stroke width of a D-family bowl by its TANGENT: measured on Van den
    Keere's D P B (ray-cast at 1000 px from the bowl's centre), the bowl is
    VERTICALLY stressed -- the maximum where the stroke runs vertical (3
    o'clock), symmetric above and below, heavier than the stem (97 against
    82), falling steeply to a true thin wherever it runs horizontal (34,
    0.42 of the stem -- the whole top and bottom, from the stem to the
    shoulder): w = hair + (max - hair) |sin phi|^1.28, phi the tangent's
    angle. Not the 26-degree nib's profile, which peaks at 2 o'clock and
    only falls to ~60. (A first version took the angle from the half
    superellipse's own centre, which sits at the stem, so the top stroke
    thickened from the stem outward and the rays read ~100 everywhere.)"""
    if BOWL is not None: return bowl_th(tan)
    phi = math.atan2(tan[1], tan[0])
    return S * (BOWL_HAIR + (BOWL_MAX - BOWL_HAIR) * abs(math.sin(phi)) ** BOWL_POW)

def half_bowl(edge, y_top, y_bot, rx, k=pen.BOWL_K * 1.12, open_bottom=0.0, w_scale=1.0, into=22.0, taper=0.7, taper_span=0.08):
    """The D's bowl (rulings, rounds 36/47) on the measured profile (owner,
    2026-09-13, "take another pass at B and related characters"): the
    CENTERLINE is the designed half superellipse from the stem's inner
    edge -- squared shoulders (k x 1.12), outer edges ON y_top and y_bot --
    and the width at every point is bowl_profile(angle from the bowl's
    centre): a hairline leaving the stem at the top, the maximum at 3
    o'clock, a hairline returning at the bottom. Both ends run `into` the
    stem and ease to `taper` of the hairline there, so the end faces lie
    inside the stem's ink. The opened bottom (ruling) is a modest
    asymmetry now: the counter's lower half lifted by open_bottom x the
    horizontal stroke (Van den Keere's own bottom is 38 against a top of
    46). Returns (solid, cx, cy, rx_c, ry_c, L, R)."""
    hair = S * (BOWL['hair'] if BOWL else BOWL_HAIR); mx = S * (BOWL['max'] if BOWL else BOWL_MAX)
    if BOWL: taper = BOWL['taper']
    ry_c = (y_top - y_bot) / 2 - hair / 2; rx_c = rx - mx / 2
    cy = (y_top + y_bot) / 2; cx = edge + rx * 0.05
    # Van den Keere's bowl, measured (2026-09-13): a FLAT run from the stem
    # along the top, a round end, a flat run back along the bottom -- so the
    # thin holds all the way to the shoulder and the weight sits on the
    # belly. The arc's x radius is the bowl's half height (a round end),
    # the flat runs take up the rest of the fixed width.
    arc_rx = min(rx_c, ry_c * BOWL_ARC); flat = rx_c - arc_rx; ax = cx + flat
    arc = superellipse(ax, cy, arc_rx, ry_c, -math.pi / 2, math.pi / 2, BOWL['k'] if BOWL else BOWL_ARC_K)
    center = [(edge - into, cy - ry_c)] + arc + [(edge - into, cy + ry_c)]
    center = resample(center)
    n = len(center) - 1
    if open_bottom:
        def win(t): return max(0.0, math.sin(math.pi * (t - 0.04) / 0.46)) if 0.04 <= t <= 0.50 else 0.0
        center = [(px, py + 0.5 * open_bottom * TH_H * win(i / n)) for i, (px, py) in enumerate(center)]
    tans = tangents(center)
    def wfn(t):
        i = min(n, int(round(t * n)))
        w = bowl_profile(tans[i]) * w_scale
        if open_bottom: w += open_bottom * TH_H * win(t)
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

DOT_STYLE = int(os.environ.get("FJORD_DOT_STYLE", 1))   # owner 2026-09-14: "dot style 1 wins"
def dot(cx, cy, r, k=2.0):
    """The dot of i j and the marks. DOT_STYLE 0-9 (owner 2026-09-14: "make
    ten increasingly handcut versions of dots"): 0 the round superellipse;
    the exponent falls toward a squarer form, the outline becomes a polygon
    of fewer sides, and each vertex takes a deterministic radial jitter
    from life() -- 9 is a rough-cut five-sided lump."""
    st = DOT_STYLE
    if st <= 0:
        return geom.poly(superellipse(cx, cy, r, r, 0, 2 * math.pi, k)[:-1])
    n = max(5, 12 - st)
    jit = 0.035 * st
    ks = k - 0.06 * st
    js = life(n + 1)
    rot = js[0] * math.pi / n
    pts = []
    for i in range(n):
        a = rot + 2 * math.pi * i / n
        rr = r * (1 + jit * js[i + 1])
        # a superellipse radius at this angle, so the squaring shows in the polygon too
        ca, sa = math.cos(a), math.sin(a)
        se = 1.0 / ((abs(ca) ** ks + abs(sa) ** ks) ** (1.0 / ks)) if ks > 0.5 else 1.0
        pts.append((cx + rr * se * ca, cy + rr * se * sa))
    return geom.poly(pts)

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
