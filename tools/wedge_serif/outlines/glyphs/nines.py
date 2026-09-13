"""Ten variants of the 9 whose tail ENDS IN A SERIF from the wedge family
(owner 2026-09-13: "give me ten variants on a 9 serifed tail to choose
from"). Every variant keeps g_nine's ring and counter byte for byte and its
tail construction -- the pen's width with the record's 0.9-stem floor, the
taper into the ring -- and changes only how the tail ends: the family's
flat foot (two-sided, left-only, longer), a rising diagonal end wedge, a
beak turned down (two lengths), a curl under the bowl, a straight diagonal
with the diagonal end wedge, a vertical stub with the stem foot, and the
2's base mirrored. Every serif is a real join by union, grown from the
stroke's REAL side polyline; level, vertical and pen-cut faces are made by
clipping rather than stroke()'s cut1, because a cut that moves the end
corner back more than one sample spacing (11 units) has that corner
dropped by _unfold and the face lands at the wrong angle. Nothing here
touches the @glyph('9') registration; cmp/nines.py rebinds it per build.

VARIANTS = [(name, fn), ...]; each fn has g_nine's signature and return."""
import math
from .. import geom, pen
from ..geom import cubic, line, superellipse, join, tangents, resample
from ..primitives import stroke, pen_widths, widths, wedge, stem_width as PR_stem_width
from ..pen import S, OVER, TH_V, TH_H, HAIR, CUT, WL, WD, DROP, FOOT, ENT
from .caps_straight import W_
from .figures import fig_ring, g_nine as g_nine_current, NINE_OVERHANG

FLOOR = 0.9                              # the record's weight floor on the 9's tail, x stem (NOTES: "the 9's 0.9")
TAPER_IN = [(0.0, 0.15), (0.06, 1.0)]    # g_nine's taper into the ring
FOOT_DEG = 55.0                          # the flat-foot tails meet their foot at this angle below horizontal
FOOT_C1 = 1.3                            # their first control's drop, x r: at 1.0 the sweep ran so close under the bowl that the pocket between them closed at 54 px (0 px of paper against the current 9's 2)
BEAK_SWELL, BEAK_SPAN = 1.15, 0.13       # the beak's swell into its face (guide section 2: 1.15 pen) over the tail's last 13%
BEAK_LIP = (0.85, 0.85)                  # the beak's lip, x the family's wedge (guide section 2's table)
SMALL = (0.4, 0.6, 0.4)                  # the family's small wedge: length, depth, drop (the I's second wedge in stem())

# ---------------------------------------------------------------- the shared 9
INK_SPREAD = 1.2   # build.INK_SPREAD: the builder grows every glyph this much (mitre joins), which is where a sharp apex gains up to 6 units

def _spread(g): return g.buffer(INK_SPREAD, join_style=2)

def _base(c):
    """g_nine's ring, its tail's start, and where the current tail bottoms
    and reaches ON THE BUILT OUTLINE (after the builder's ink spread --
    a sharp apex mitres out further than a blunt corner, so the design
    outline is not where an overhang can be matched): every variant
    bottoms at `bot` and is fitted to its overhang against `cur_left`."""
    D = c["figH"]; rx = W_(c, '9', 230); r = D * 0.29; cx = rx + TH_V / 2
    ring, _, _ = fig_ring(cx, D - r, rx, r)
    p0 = (cx + rx * math.cos(math.radians(-20)), D - r + r * math.sin(math.radians(-20)))
    x0, y0, _, _ = geom.bbox(_spread(g_nine_current(c)))
    return dict(D=D, rx=rx, r=r, cx=cx, ring=ring, p0=p0, bot=y0, cur_left=x0)

def _target_left(b, overhang):
    """x of the leftmost spread ink for a requested overhang past the
    bowl's left ink. NINE_OVERHANG (11) names the CURRENT tail as the
    record measured it on the built outline, so `overhang` 11 IS the
    current tail's reach and the others are offsets from it."""
    return b['cur_left'] - (overhang - NINE_OVERHANG)

def _tail(b, tip, end_deg=None, pull=0.55, c1_pull=1.5, c2_y_max=None):
    """g_nine's tail cubic with the tip free. end_deg None: g_nine's own
    second control (1.15 rx, 0.55 r back from the tip). Otherwise the tail
    arrives at the tip heading LEFT and `end_deg` below horizontal (90 =
    straight down, 0 = level), the second control `pull` x r back along
    that heading; c1_pull is the first control's drop below p0, x r.
    c2_y_max caps the second control's height, so a tip raised for its
    serif does not lift the whole sweep into the bowl's pocket."""
    p0, rx, r = b['p0'], b['rx'], b['r']
    c1 = (p0[0] - rx * 0.15, p0[1] - r * c1_pull)
    if end_deg is None: c2 = (tip[0] + rx * 1.15, tip[1] + r * 0.55)
    else:
        a = math.radians(end_deg); c2 = (tip[0] + math.cos(a) * r * pull, tip[1] + math.sin(a) * r * pull)
    if c2_y_max is not None: c2 = (c2[0], min(c2[1], c2_y_max))
    return cubic(p0, c1, c2, tip)

def _width(path, floor=FLOOR, profile=None):
    """g_nine's tail width: the pen along the path, never under floor x
    stem, tapering in at the ring; x profile(t) when given."""
    base = pen_widths(path); tap = widths(TAPER_IN)
    def f(t):
        w = max(base(t), S * floor) * tap(t)
        return w * profile(t) if profile else w
    return f

def _length(pts): return sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))

def _extend(path, length):
    """The path continued straight along its end tangent (to be clipped)."""
    tn = tangents(path)[-1]; P = path[-1]
    return join(path, line(P, (P[0] + tn[0] * length, P[1] + tn[1] * length)))

def _walk_back(side):
    """edge_at for wedge(): the point `dist` back along a stroke's REAL side
    polyline from its end -- so the bracket lands on the drawn edge, curved
    or not, and the join has no nick."""
    pts = list(side)
    def f(dist):
        rem = dist; p = pts[-1]
        for q in reversed(pts[:-1]):
            seg = math.dist(p, q)
            if seg >= rem:
                u = rem / seg if seg else 0.0; return (p[0] + (q[0] - p[0]) * u, p[1] + (q[1] - p[1]) * u)
            rem -= seg; p = q
        return pts[0]
    return f

def _clip(path, wf, origin, inward):
    """Stroke `path` and keep the half-plane {p : (p - origin) . inward >= 0}
    -- the face is the clip line. Returns (solid, sideA, sideB) with each
    side polyline truncated at its crossing, whose last point is that
    side's corner ON the face."""
    solid, L, R = stroke(path, wf, sides=True)
    nx, ny = inward; tx, ty = -ny, nx; o = origin; big = 6000.0
    half = geom.poly([(o[0] + tx * big, o[1] + ty * big), (o[0] - tx * big, o[1] - ty * big),
                      (o[0] - tx * big + nx * big, o[1] - ty * big + ny * big), (o[0] + tx * big + nx * big, o[1] + ty * big + ny * big)])
    clipped = geom._largest(solid.intersection(half))
    def cut_side(side):
        out = []
        for a, q in zip(side, side[1:]):
            da = (a[0] - o[0]) * nx + (a[1] - o[1]) * ny; db = (q[0] - o[0]) * nx + (q[1] - o[1]) * ny
            out.append(a)
            if da >= 0 > db:
                u = da / (da - db); out.append((a[0] + (q[0] - a[0]) * u, a[1] + (q[1] - a[1]) * u)); return out
        return out
    return clipped, cut_side(L), cut_side(R), half

def _upper_lower(A, B):
    """The two side polylines by their END corners: (upper, lower)."""
    return (A, B) if A[-1][1] >= B[-1][1] else (B, A)

def _unit(v):
    n = math.hypot(*v) or 1.0; return (v[0] / n, v[1] / n)

def _fit(make, target_left, bot, fit_x=True, fit_y=True, iters=6):
    """Slide a variant's free point until the glyph's leftmost SPREAD ink
    is at target_left and its lowest at bot (the current tail's, spread),
    each within 0.05 unit. make(dx, dy) -> the glyph's ink (unspread)."""
    dx = dy = 0.0; g = None
    for _ in range(iters):
        g = make(dx, dy); x0, y0, _, _ = geom.bbox(_spread(g))
        ex = (x0 - target_left) if fit_x else 0.0; ey = (y0 - bot) if fit_y else 0.0
        if abs(ex) < 0.05 and abs(ey) < 0.05: return g
        dx -= ex; dy -= ey
    return make(dx, dy)

# ---------------------------------------------------------------- 1, 2, 8: the flat foot
def _foot(c, overhang, sides):
    """The tail bends into a STRAIGHT leg at FOOT_DEG (one bracket depth
    and a little more long, so both brackets land on a straight edge as
    they do on the 1's stem) and lands on a LEVEL face at the figure's
    bottom; the family's stem foot (0.85 x 1.0, drop 0.6) grows
    horizontally from the face's corner(s), its bracket up the leg's real
    edge -- the 1's foot on a slanted leg, as the A's left foot is."""
    b = _base(c); tgt = _target_left(b, overhang); y_face = b['bot']
    a = math.radians(FOOT_DEG); half_face = S * FLOOR / (2 * math.sin(a)); leg = WD + 20
    def make(dx, dy):
        tip = (tgt + WL * FOOT + half_face + dx, y_face)
        J = (tip[0] + math.cos(a) * leg, tip[1] + math.sin(a) * leg)
        ext = _extend(join(_tail(b, J, end_deg=FOOT_DEG, pull=0.9, c1_pull=FOOT_C1), line(J, tip)), 90)
        solid, A, B, _ = _clip(ext, _width(ext), (0.0, y_face), (0.0, 1.0))
        left, right = (A, B) if A[-1][0] <= B[-1][0] else (B, A)
        parts = [b['ring'], solid]
        if 'left' in sides: parts.append(wedge(left[-1], (0, -1), (-1, 0), WL * FOOT, WD, DROP * 0.6, edge_at=_walk_back(left)))
        if 'right' in sides: parts.append(wedge(right[-1], (0, -1), (1, 0), WL * FOOT, WD, DROP * 0.6, edge_at=_walk_back(right)))
        return geom.ink(parts)
    return _fit(make, tgt, y_face, fit_y=False)

def v01_foot_flat(c): return _foot(c, NINE_OVERHANG, ('left', 'right'))
def v02_foot_left(c): return _foot(c, NINE_OVERHANG, ('left',))
def v08_foot_long(c): return _foot(c, 20.0, ('left', 'right'))

# ---------------------------------------------------------------- 3: the diagonal end wedge, rising
def v03_flag(c):
    """g_nine's tail and path, the end face SQUARE across the tail at its
    own angle (29 below horizontal), and the family's diagonal end wedge
    (0.9 x 0.9, drop DROP -- the A's, V's) on the upper side, rising from
    the face's upper corner: the 2's base wedge mirrored onto a sloping
    end. The lower side would twin the beak and drop under the bottom."""
    b = _base(c); tgt = _target_left(b, NINE_OVERHANG)
    def make(dx, dy):
        tip = (b['cx'] - b['rx'] * 1.12 + dx, 22 + dy)
        path = _tail(b, tip); wf = _width(path)
        solid, A, B = stroke(path, wf, sides=True); up, lo = _upper_lower(A, B)
        d = tangents(resample(path))[-1]; sd = _unit((up[-1][0] - lo[-1][0], up[-1][1] - lo[-1][1]))
        flag = wedge(up[-1], d, sd, WL * 0.9, WD * 0.9, DROP, edge_at=_walk_back(up))
        return geom.ink([b['ring'], solid, flag])
    return _fit(make, tgt, b['bot'])

# ---------------------------------------------------------------- 4, 9: the beak, turned down
def _beak(c, overhang, floor):
    """The C's and S's terminal turned to the tail's end: the stroke swells
    to 1.15 over its last 13%, the face is VERTICAL (clipped at the
    overhang), and the lip -- 0.85 x 0.85 of the family, drop 0 -- hangs
    from the face's lower corner perpendicular to the tail, its bracket
    back along the tail's lower edge. The tail's END is raised so the
    lip's tip is the figure's bottom, with the second control held where
    g_nine's is: raising the whole tip lifted the sweep into the bowl's
    pocket, which closed at 54 px (0 px of paper against the current's 3)."""
    b = _base(c); tgt = _target_left(b, overhang); x_face = tgt + INK_SPREAD   # the spread lands the face's ink at tgt
    c2_cap = 22.0 + b['r'] * 0.55
    def make(dx, dy):
        path = _tail(b, (x_face + 30.0, 22.0 + dy), c2_y_max=c2_cap); ext = _extend(path, 100)
        Lv = _length(path); Lt = _length(ext); span = BEAK_SPAN * Lv
        def swell(t):
            s = t * Lt
            if s <= Lv - span: return 1.0
            u = min(1.0, (s - (Lv - span)) / span); return 1.0 + (BEAK_SWELL - 1.0) * (3 * u * u - 2 * u ** 3)
        solid, A, B, half = _clip(ext, _width(ext, floor, swell), (x_face, 0.0), (1.0, 0.0))
        up, lo = _upper_lower(A, B)
        d = tangents(resample(path))[-1]; sd = _unit((lo[-1][0] - up[-1][0], lo[-1][1] - up[-1][1]))
        sd = (-d[1], d[0]) if (-d[1]) * sd[0] + d[0] * sd[1] > 0 else (d[1], -d[0])   # the tail's normal, on the lower side
        # the lip, clipped to the face too: wedge()'s 6-unit strip inside the
        # stroke is laid along the tail's normal, which the vertical face cuts
        lip = wedge(lo[-1], d, sd, WL * BEAK_LIP[0], WD * BEAK_LIP[1], 0.0, edge_at=_walk_back(lo)).intersection(half)
        return geom.ink([b['ring'], solid, lip])
    return _fit(make, tgt, b['bot'], fit_x=False)

def v04_beak_down(c): return _beak(c, NINE_OVERHANG, FLOOR)
def v09_beak_short(c): return _beak(c, 4.0, 1.0)

# ---------------------------------------------------------------- 5: the curl under the bowl
CURL_R = 0.38     # the curl's centerline radius, x r (0.42 put the arc's top so high that the sweep closed the pocket under the bowl at 54 px)
CURL_THIN = 0.6   # the curl thins to this over the arc, as the 6's stroke thins toward its end
CURL_SAG = 4.5    # units: the curl's leftmost point is on a curve, not a corner, so the one-in-four cut drops it and the built outline reads that much short; the fit targets that much further

def v05_curl(c):
    """The tail steepens to 60 below horizontal and runs into a round curl
    (radius 0.42 r) that turns back under the bowl through the figure's
    bottom, thinning to 0.6 over the arc as the 6's stroke thins, then a
    short level run to the right (a bracket depth long, at the thinned
    width) ending SQUARE with the family's SMALL wedge (0.4 x 0.6, drop
    0.4 -- the I's second wedge) standing straight up from the end's upper
    corner. A first draft ended the arc heading up-right and put the wedge
    there: it pointed back into the hook, and its bracket sat on the arc's
    tightly curved inner edge, which reads as a bump."""
    b = _base(c); tgt = _target_left(b, NINE_OVERHANG) - CURL_SAG; R_ = CURL_R * b['r']
    a0, a1 = math.radians(150), math.radians(270); run = WD * SMALL[1] + 12
    def make(dx, dy):
        C = (tgt + R_ + S * FLOOR / 2 + dx, b['bot'] + R_ + S * FLOOR * CURL_THIN / 2 + dy)
        T = (C[0] + R_ * math.cos(a0), C[1] + R_ * math.sin(a0)); Bm = (C[0], C[1] - R_)
        path = _tail(b, T, end_deg=60, pull=0.5)
        arc = superellipse(C[0], C[1], R_, R_, a0, a1, 2.0)
        full = join(path, arc, line(Bm, (Bm[0] + run, Bm[1])))
        Lv = _length(path); La = Lv + _length(arc); Lt = _length(full)
        def thin(t):
            s = t * Lt
            if s <= Lv: return 1.0
            if s >= La: return CURL_THIN
            u = (s - Lv) / (La - Lv); return 1.0 - (1.0 - CURL_THIN) * (3 * u * u - 2 * u ** 3)
        solid, A, B = stroke(full, _width(full, FLOOR, thin), sides=True); up, lo = _upper_lower(A, B)
        tip = wedge(up[-1], (1, 0), (0, 1), WL * SMALL[0], WD * SMALL[1], DROP * SMALL[2], edge_at=_walk_back(up))
        return geom.ink([b['ring'], solid, tip])
    return _fit(make, tgt, b['bot'])

# ---------------------------------------------------------------- 6: the straight diagonal
DIAG_OFF = 12.0   # the straight tail is tangent to an ellipse this far OUTSIDE the ring's centerline: on the centerline itself its upper edge crossed the counter by a few units

def _tangent_angle(cx, cy, rx, ry, E):
    """The angle on an ellipse (lower right quadrant) whose tangent line
    passes through E: bisection on the cross product."""
    def f(th):
        P = (cx + rx * math.cos(th), cy + ry * math.sin(th)); T = (-rx * math.sin(th), ry * math.cos(th))
        return T[0] * (E[1] - P[1]) - T[1] * (E[0] - P[0])
    lo, hi = math.radians(-89.0), math.radians(-1.0); flo = f(lo)
    for _ in range(60):
        mid = (lo + hi) / 2; fm = f(mid)
        if (fm < 0) == (flo < 0): lo, flo = mid, fm
        else: hi = mid
    return (lo + hi) / 2

def v06_diag(c):
    """The 7's stroke reversed: one straight stroke leaving the ring where
    the ring's tangent points at the tail's end, on the tail's own width
    rule, tapering into the ring as g_nine's does, ending SQUARE with the
    family's diagonal end wedge (0.9 x 0.9, drop DROP) on the outer, lower
    side -- the A's right foot -- whose apex is the figure's bottom."""
    b = _base(c); tgt = _target_left(b, NINE_OVERHANG); cx, cy = b['cx'], b['D'] - b['r']
    rx, r = b['rx'] + DIAG_OFF, b['r'] + DIAG_OFF
    def make(dx, dy):
        E = (tgt + 60 + dx, b['bot'] + 70 + dy)
        th = _tangent_angle(cx, cy, rx, r, E); P = (cx + rx * math.cos(th), cy + r * math.sin(th))
        path = line(P, E); wf = _width(path)
        solid, A, B = stroke(path, wf, sides=True); up, lo = _upper_lower(A, B)
        d = _unit((E[0] - P[0], E[1] - P[1])); sd = _unit((lo[-1][0] - up[-1][0], lo[-1][1] - up[-1][1]))
        foot = wedge(lo[-1], d, sd, WL * 0.9, WD * 0.9, DROP, edge_at=_walk_back(lo))
        return geom.ink([b['ring'], solid, foot])
    return _fit(make, tgt, b['bot'])

# ---------------------------------------------------------------- 7: the vertical stub with the stem foot
STUB_RUN = 0.6    # the vertical run, x WD: a full bracket depth would push the tail's sweep up into the ring's bottom stroke, and 0.72 still closed the pocket under the bowl at 54 px

def v07_stub(c):
    """The tail sweeps left under the bowl, turns down and runs VERTICAL to
    the figure's bottom, where the two-sided stem foot (0.85 x 1.0, drop
    0.6) sits exactly as under the 4 and the l. Tail and run are ONE stroke
    on the tail's width rule, with the stem's entasis (stem_width, the
    bottom half of its quartic) swelling the run into the foot; the feet
    grow from the stroke's real edges, so the brackets climb the run and
    on up the bend without a seam. The run is STUB_RUN of a bracket depth
    -- a full one pushes the sweep into the ring's bottom stroke."""
    b = _base(c); tgt = _target_left(b, NINE_OVERHANG); w0 = S * FLOOR; bot = b['bot']
    run = WD * STUB_RUN; y_top = bot + run
    def make(dx, dy):
        xs = tgt + WL * FOOT + w0 * (1 + ENT) / 2 + dx
        path = _tail(b, (xs, y_top), end_deg=90, pull=0.3, c1_pull=1.3)   # the sweep held low: at 1.0 / 0.4 it closed the pocket under the bowl at 54 px
        full = join(path, line((xs, y_top), (xs, bot)))
        Lv = _length(path); Lt = _length(full)
        def swell(t):   # the stem's bottom-half entasis over the run: 1.0 at its top, 1 + ENT at the bottom
            s = t * Lt
            if s <= Lv: return 1.0
            u = 0.5 * (1.0 - (s - Lv) / (Lt - Lv)); return PR_stem_width(1.0, ENT, u)
        solid, A, B = stroke(full, _width(full, FLOOR, swell), sides=True)
        left, right = (A, B) if A[-1][0] <= B[-1][0] else (B, A)
        feet = [wedge(left[-1], (0, -1), (-1, 0), WL * FOOT, WD, DROP * 0.6, edge_at=_walk_back(left)),
                wedge(right[-1], (0, -1), (1, 0), WL * FOOT, WD, DROP * 0.6, edge_at=_walk_back(right))]
        return geom.ink([b['ring'], solid] + feet)
    return _fit(make, tgt, bot, fit_y=False)

# ---------------------------------------------------------------- 10: the 2's base, mirrored
def v10_base_two(c):
    """The tail flattens onto the figure's bottom and runs LEFT as a base,
    the floor released so the run is the pen's horizontal (the 2's base
    weight), the end pen-cut as the z's bottom bar's left end, and the
    bar-end wedge (0.85 x 0.9, drop 0) rising from the cut's upper corner:
    the 2's base mirrored, the ruling that ties the 2's base to the 9's
    overhang read the other way."""
    b = _base(c); tgt = _target_left(b, NINE_OVERHANG); bot = b['bot']
    w_end = TH_H; fl = S * FLOOR; y_c = bot + w_end / 2
    x_j = tgt + WD * 0.9 + w_end * math.tan(CUT) + 12
    face_n = (math.cos(CUT), -math.sin(CUT))          # inward normal of a face leaning tan(CUT) rightward as it rises
    def make(dx, dy):
        J = (x_j + dx, y_c + dy)
        path = _tail(b, J, end_deg=0, pull=0.75)
        full = join(path, line(J, (tgt - 40.0, J[1])))
        corner = (J[0] - x_j + tgt, J[1] - w_end / 2)  # the face's bottom corner rides with the fit
        Lv = _length(path); Lt = _length(full); s0 = 0.6 * Lv
        def release(t):
            s = t * Lt
            if s <= s0: return 1.0
            u = min(1.0, (s - s0) / (Lv - s0)); return 1.0 + (w_end / fl - 1.0) * (3 * u * u - 2 * u ** 3)
        base = pen_widths(full); tap = widths(TAPER_IN)
        wf = lambda t: max(base(t), fl) * tap(t) * release(t)
        solid, A, B, half = _clip(full, wf, corner, face_n); up, lo = _upper_lower(A, B)
        wdg = wedge(up[-1], (-1, 0), (0, 1), WL * 0.85, WD * 0.9, 0.0, edge_at=_walk_back(up)).intersection(half)
        return geom.ink([b['ring'], solid, wdg])
    return _fit(make, tgt, bot)

VARIANTS = [
    ('foot-flat', v01_foot_flat),
    ('foot-left', v02_foot_left),
    ('flag-diag', v03_flag),
    ('beak-down', v04_beak_down),
    ('curl-up', v05_curl),
    ('diag-straight', v06_diag),
    ('stub-foot', v07_stub),
    ('foot-long', v08_foot_long),
    ('beak-short', v09_beak_short),
    ('base-two', v10_base_two),
]

INFO = {   # one line on the idea, and the serif's size in the family's units
    'foot-flat': ("the tail steepens to 55 and lands on a level face; the 1's two-sided foot on the bottom line", "foot 0.85 x 1.0 (WL x WD), both sides, drop 0.6"),
    'foot-left': ("the same footed tail, the half serif: only the left wedge, as the L's and E's feet", "foot 0.85 x 1.0, left only, drop 0.6"),
    'flag-diag': ("the current tail, square-ended, with the diagonal end wedge rising from the face's upper corner at the tail's own angle", "diagonal end wedge 0.9 x 0.9, drop DROP, upper side"),
    'beak-down': ("the C's terminal turned down: swell to 1.15, a vertical face, the lip hanging from the lower corner", "beak lip 0.85 x 0.85 at 1.15 pen, drop 0"),
    'curl-up': ("the tail turns under the bowl in a round curl, thins to 0.6, runs level to the right and ends with a small wedge standing up", "small wedge 0.4 x 0.6, drop 0.4 (the I's second)"),
    'diag-straight': ("the 7's stroke reversed: one straight diagonal off the ring's tangent, the diagonal end wedge beneath its end", "diagonal end wedge 0.9 x 0.9, drop DROP, lower side"),
    'stub-foot': ("the tail drops vertically into a short stub carrying the stem foot, as the 4's and the l's", f"stem foot 0.85 x 1.0, both sides, drop 0.6, on a vertical run {STUB_RUN:.2g} WD ({WD * STUB_RUN:.0f} units) tall"),
    'foot-long': ("the two-sided flat foot with the tail reaching 9 units further left", "foot 0.85 x 1.0, both sides, drop 0.6; overhang 20"),
    'beak-short': ("the beak on a shorter, heavier tail: floor 1.0 stem, overhang 4", "beak lip 0.85 x 0.85 at 1.15 pen, drop 0; floor 1.0 S"),
    'base-two': ("the 2's base mirrored: the tail flattens onto the bottom line, released to the pen's horizontal, pen-cut, the bar-end wedge rising", "bar-end wedge 0.85 x 0.9, drop 0; run TH_H wide"),
}
