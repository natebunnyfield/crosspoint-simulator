"""The rest of the Latin set on the same pen: capitals A-Z, lining figures
0-9, and the punctuation an epub needs. Same primitives as alphabet2 (stem,
curve, bracket_wedge), counterpunched bowls from round17 (ring, Hole) where
a closed counter exists. Cap height 0.94 of the ascender (humanist caps sit
under the ascenders); figures 0.92 of the cap height, lining.
"""
import math
import alphabet2 as A
from alphabet2 import line, bez, ellipse, tangents, compose, taper_in, taper_out, flare_end, bracket_wedge, blob, catmull

def _round17():
    import round17
    return round17

# ---------------------------------------------------------------- helpers
# Per-glyph width multipliers, solved by the builder against the garalde
# references' measured ink widths (round 20). 1.0 = the drawn default.
W = {}
def _w(c, key, default):
    return default * W.get(key, 1.0) * c["wf"]

def capH(c): return c["xh"] * 1.625    # Garamond's cap over x-height (round 26; was 0.941 asc = 1.73 xh, every capital 0.11 xh tall)
CAP_STEM = 1.137                        # cap stem over lowercase stem, same references
# Old-style figures (three of the four references): 0 1 2 sit on the
# x-height, 6 and 8 rise, 3 4 5 7 9 descend. The boxes are the references'
# medians as fractions of the cap height; the builder draws each figure
# with height top - bot and shifts it to bot.
FIG_BOX = {'0': (0.66, -0.02), '1': (0.64, 0.0), '2': (0.66, 0.0), '3': (0.66, -0.31), '4': (0.66, -0.31),
           '5': (0.64, -0.31), '6': (0.98, -0.02), '7': (0.64, -0.31), '8': (0.98, -0.02), '9': (0.66, -0.31)}
_FIG = [None]
def figH(c):
    return _FIG[0] if _FIG[0] else capH(c) * 0.92

def vstem(c, P, x, y0, y1, top_sides=(1, -1), foot_sides=(-1, 1), thin=1.0, flare=True):
    """A capital's stem: bracketed wedges BOTH sides top and foot, at the
    cap stem weight (1.137 x the lowercase, the references' median)."""
    pts = line((x, y0), (x, y1), 36)
    thin = thin * CAP_STEM
    prof = c["ent"] if flare else (lambda t: 1.0)
    prof2 = (lambda t: prof(t) * thin)
    P.append(A.outline(pts, c["pen"], prof2))
    th = c["pen"].th((0, 1)) * thin
    if c["wl"] <= 0 or c["serif"] != "wedge": return
    for sd in top_sides:
        P.append(bracket_wedge((x, y1), (0, 1), (-1, 0), th * prof(1.0), c["wl"] * 0.8, c["wd"], sd, drop=c["drop"], fillet=c["fillet"]))
    for sd in foot_sides:
        P.append(bracket_wedge((x, y0), (0, -1), (1, 0), th * prof(0.0), c["wl"] * 0.8, c["wd"], sd, drop=c["drop"] * 0.6, fillet=c["fillet"]))

def bar(c, P, x0, x1, y, serif_ends=(), thick=1.0, align="center"):
    """align: 'center' puts the bar's centerline on y; 'top' puts its top
    edge there (a bar on the cap line), 'bottom' its bottom edge (a bar on
    the baseline). Round 26: E F L Z bars were centered on the cap line and
    the baseline and overshot both by half a bar."""
    th = max(c["pen"].th((1, 0)) * thick, c["s"] * 0.5)
    y = y - th / 2 if align == "top" else (y + th / 2 if align == "bottom" else y)
    pts = line((x0, y), (x1, y), 12)
    P.append(A.outline(pts, c["pen"], lambda t: thick, cut0=c["cut"], cut1=c["cut"]))
    for end, side in serif_ends:   # ('left'|'right', +1 up | -1 down)
        if c["wl"] <= 0: continue
        P_ = (x0, y) if end == 'left' else (x1, y)
        d = (-1, 0) if end == 'left' else (1, 0); nrm = (0, -1) if end == 'left' else (0, 1)
        sd = side if end == 'right' else -side
        P.append(bracket_wedge(P_, d, nrm, th, c["wl"] * 0.85, c["wd"] * 0.9, sd, drop=0, fillet=c["fillet"]))

def diag(c, P, p0, p1, thin=1.0, serif0=None, serif1=None, taper0=0.0, taper1=0.0):
    pts = line(p0, p1, 30)
    thin = thin * CAP_STEM
    prof = lambda t: thin
    if taper0: prof = compose(prof, taper_in(taper0, 0.22))    # round 30: a leg thins into its junction
    if taper1: prof = compose(prof, taper_out(taper1, 0.22))   # round 31: same, for a leg drawn foot-first
    P.append(A.outline(pts, c["pen"], prof))
    if c["wl"] <= 0: return
    tn = tangents(pts)
    if serif0:
        d = (-tn[0][0], -tn[0][1]); nrm = (-d[1], d[0]); th = c["pen"].th(tn[0]) * thin
        P.append(bracket_wedge(pts[0], d, nrm, th, c["wl"] * 0.9, c["wd"] * 0.9, serif0, drop=c["drop"], fillet=c["fillet"]))
    if serif1:
        d = tn[-1]; nrm = (-d[1], d[0]); th = c["pen"].th(tn[-1]) * thin
        P.append(bracket_wedge(pts[-1], d, nrm, th, c["wl"] * 0.9, c["wd"] * 0.9, serif1, drop=c["drop"], fillet=c["fillet"]))

KICK_ANGLE = math.radians(65)   # the A's right leg: (w - 0.3 s, 0) -> (w/2 - 0.18 s, C), about 65 degrees
def kick(c, P, J, s, thin=1.0 / CAP_STEM, angle=KICK_ANGLE, bury=0.2):
    """A K/R leg drawn exactly as the A's right leg (owner 2026-09-12: 'match
    the flow of the lower right of A'): foot-first from the baseline, full
    weight, the wedge foot on the outer side as the A's, straight, at the
    A's angle; it thins into the junction J (round 31)."""
    foot = (J[0] + J[1] / math.tan(angle), 0)
    d = ((J[0] - foot[0]), (J[1] - foot[1])); L = math.hypot(*d); d = (d[0] / L, d[1] / L)
    top = (J[0] + d[0] * s * bury, J[1] + d[1] * s * bury)   # buried past the junction
    diag(c, P, foot, top, thin=thin, serif0=1, taper1=0.45)

def cp_ring(c, P, cx, cy, rx, ry, a0=0.0, a1=2 * math.pi, close_x=None):
    """Counterpunched ring (outer cut, counter clean). close_x: for a D-like
    half ring, both contours are closed along the vertical x=close_x."""
    R = _round17()
    cut = c.get("_cut")
    outer, inner = R.ring(c, cx, cy, rx, ry, a0, a1, 110, cut=cut)
    if close_x is not None:
        outer = [(close_x, outer[0][1])] + outer + [(close_x, outer[-1][1])]
        inner = [(close_x, inner[0][1])] + inner + [(close_x, inner[-1][1])]
    P.append(outer); P.append(R.Hole(inner))

# ---------------------------------------------------------------- capitals
# Redrawn (round 21) on the lowercase's own primitives so the two cases are
# one hand: A.stem for every stem (entasis, bracketed wedges, the same
# fillet), counterpunched bowls (B D O P Q R and the figures), diagonals
# thin at 0.72, joins tapered, the J's line across always. Skeletons follow
# the garalde model: low bar on the A, small upper bowl on the B, the E's
# middle arm short and high, splayed M with its apex on the baseline, thin
# verticals on the N, the R's leg straight to the line, the U's bottom ON
# the baseline (it floated), pointed V W, the Y's arms meeting at 0.45.

def _cstem(c, P, x, y0, y1, top="left", foot="both", thin=1.0):
    """A capital stem at cap weight with the LOWERCASE's serifs exactly (owner
    2026-09-12): one wedge at the top, pointing left, and a foot both sides,
    at the sizes alphabet2.stem uses. top: 'left'|'right'|None ('both' is
    mapped to left; 'right' points OUT on a right-hand stem, round 32;
    'right+' is 'right' plus a small left wedge, round 34, the U only);
    foot: 'both'|'left'|'right'|None."""
    pts = line((x, y0), (x, y1), 36)
    prof = lambda t: c["ent"](t) * CAP_STEM * thin
    P.append(A.outline(pts, c["pen"], prof))
    th = c["pen"].th((0, 1)) * CAP_STEM * thin
    if c["wl"] <= 0 or c["serif"] != "wedge": return
    if top:
        # round 32 (owner: "the top right serif of caps needs to flare out, not
        # inward"): a RIGHT stem's top wedge points right; 'left'/'both' point left.
        side = -1 if top in ("right", "right+") else 1
        P.append(bracket_wedge((x, y1), (0, 1), (-1, 0), th * c["ent"](1.0), c["wl"], c["wd"], side, drop=c["drop"], fillet=c["fillet"]))
        if top == "right+":
            # round 34 (owner: the U's top right serif should "go slightly to
            # the left too"): a second, small wedge to the left beside the
            # full right one -- 0.4 of its length, 0.6 of its depth, 0.4 of
            # its drop. Only the U's right stem asks for it; 'left', 'right'
            # and 'both' draw exactly what they did.
            P.append(bracket_wedge((x, y1), (0, 1), (-1, 0), th * c["ent"](1.0), c["wl"] * 0.4, c["wd"] * 0.6, 1, drop=c["drop"] * 0.4, fillet=c["fillet"]))
    fsides = {"both": (-1, 1), "left": (-1,), "right": (1,), None: ()}
    for sd in fsides[foot]:
        P.append(bracket_wedge((x, y0), (0, -1), (1, 0), th * c["ent"](0.0), c["wl"] * 0.85, c["wd"], sd, drop=c["drop"] * 0.6, fillet=c["fillet"]))

def _bowl_ctrl(x, y_top, y_bot, w, s=0.0):
    """Control points of a B/P/R bowl: both ends a quarter of a cap stem INSIDE
    the stem (round 33: the tapered ends used to land on the stem's center and
    nick it top and bottom)."""
    return (x - s * 0.25, y_top), (x + w * 1.05, y_top), (x + w * 1.05, y_bot), (x - s * 0.25, y_bot)

def _bowl_point(x, y_top, y_bot, w, t, s=0.0):
    """The point at t on the bowl bezier _bowl_stroke draws (round 30)."""
    p0, p1, p2, p3 = _bowl_ctrl(x, y_top, y_bot, w, s)
    u = 1 - t
    return (u*u*u*p0[0] + 3*u*u*t*p1[0] + 3*u*t*t*p2[0] + t*t*t*p3[0], u*u*u*p0[1] + 3*u*u*t*p1[1] + 3*u*t*t*p2[1] + t*t*t*p3[1])

def _bowl_stroke(c, P, x, y_top, y_bot, w, taper=0.5):
    """A B/P/R bowl: leaves the stem tapered at the top, swings out to w and
    rejoins tapered at the bottom. Stroked (the counter is what the stroke
    leaves), so its weight follows the pen like the lowercase b's."""
    p0, p1, p2, p3 = _bowl_ctrl(x, y_top, y_bot, w, c["s"] * CAP_STEM)
    pts = bez(p0, p1, p2, p3, 48)
    A.curve(c, P, pts, compose(taper_in(taper * 0.6, 0.14), taper_out(taper, 0.14)))   # round 33: the top join keeps more weight

def g_A(c):
    P = []; C = capH(c); w = _w(c, "A", 600); s = c["s"] * CAP_STEM
    # round 33: the thin stroke ends INSIDE the thick one under the apex (its
    # square end poked out past it)
    # round 34 (owner: "flatten the bottom left kick of A"): the thin leg's
    # foot was diag()'s -- an end face square to the leg and a wedge square
    # to that, so the serif rose off the baseline like a kick (its tip 45
    # units up). Now the end face is pen-cut FLAT onto the baseline (cut0 =
    # the leg's lean) and the wedge is built by hand: bracket up the leg's
    # own left edge, tip ON the baseline, no drop -- the garalde A's flat
    # left foot. The right foot is untouched.
    p0, p1 = (s * 0.3, 0), (w / 2 - s * 0.06, C - s * 0.32)
    pts = line(p0, p1, 30); tn = tangents(pts)[0]; th = c["pen"].th(tn) * 0.72
    P.append(A.outline(pts, c["pen"], lambda t: 0.72, cut0=-math.atan2(tn[0], tn[1])))
    if c["wl"] > 0:
        nrm = (-tn[1], tn[0])                                     # the leg's left-hand normal
        Apt = (p0[0] - th / 2 / tn[1], 0.0)                       # the flat face's left corner
        Cpt = (Apt[0] + tn[0] * c["wd"] * 0.9, tn[1] * c["wd"] * 0.9)   # up the leg's left edge
        B = (Apt[0] - c["wl"] * 0.9, 0.0); f = c["fillet"]
        ctrl = (Apt[0] * f + Cpt[0] * (1 - f), Apt[1] * f + Cpt[1] * (1 - f))
        fil = [((1-t)**2*Cpt[0] + 2*(1-t)*t*ctrl[0] + t*t*B[0], (1-t)**2*Cpt[1] + 2*(1-t)*t*ctrl[1] + t*t*B[1]) for t in [i / 10 for i in range(11)]]
        P.append([(Cpt[0] - nrm[0] * th / 2, Cpt[1] - nrm[1] * th / 2)] + fil + [Apt, (p0[0], 0.0)])
    diag(c, P, (w - s * 0.3, 0), (w / 2 - s * 0.18, C), thin=1.0 / CAP_STEM, serif0=1)
    A.curve(c, P, line((w * 0.19, C * 0.28), (w * 0.81, C * 0.28), 10)); return P

def g_B(c):
    P = []; C = capH(c); s = c["s"] * CAP_STEM; x = s / 2; w = _w(c, "B", 380)
    _cstem(c, P, x, 0, C, top="left", foot="left")
    th = c["pen"].th((1, 0))   # round 33: bowls' outer edges ON the cap line and baseline (they were centered on them)
    _bowl_stroke(c, P, x, C - th / 2, C * 0.55, w * 0.86)
    _bowl_stroke(c, P, x, C * 0.55, th / 2, w); return P

def g_C(c):
    P = []; C = capH(c); rx = _w(c, "C", 330); ry = C / 2 + c["over"]
    pts = ellipse(rx, C / 2, rx, ry, math.radians(38), math.radians(322), 100, c["k"])
    A.curve(c, P, pts, compose(flare_end(0.3, 0.14), lambda t: flare_end(0.22, 0.12)(1 - t)))   # round 33: no pen cuts (the lower terminal was a thorn)
    # the beak: a wedge on the UPPER terminal, as the garalde C has. The ellipse
    # runs 38 -> 322 degrees, so the upper terminal is pts[0] (round 33: the
    # beak had been on pts[-1], the lower one); same construction as the G's.
    if c["wl"] > 0:
        tn = tangents(pts)[0]; d = (-tn[0], -tn[1]); nrm = (-d[1], d[0])
        P.append(bracket_wedge(pts[0], d, nrm, c["pen"].th(tn) * 1.15, c["wl"] * 0.85, c["wd"] * 0.85, 1, drop=0, fillet=c["fillet"]))
    return P

def g_D(c):
    """Stem plus a counterpunched bowl that starts at the stem's inner edge
    and is trimmed to the cap height, so nothing of the ring shows past the
    stem (the first D closed its contours at the stem's center and its ring
    top and bottom poked out to the left: 'a mess on the left side')."""
    P = []; C = capH(c); s = c["s"] * CAP_STEM; x = s / 2; rx = _w(c, "D", 330)
    _cstem(c, P, x, 0, C, top="left", foot="left")
    edge = x + s * 0.5
    th_h = c["pen"].th((1, 0)); ry = C / 2 - th_h / 2       # outer top lands ON the cap height
    R = _round17()
    outer, inner = R.ring(c, edge + rx * 0.05, C / 2, rx, ry, -math.pi / 2, math.pi / 2, 110, cut=c.get("_cut"))
    # round 34 (owner: "make D slightly more weighted by opening the bottom"):
    # the ring's pen is symmetric top to bottom, so the D's bottom stroke was
    # as thin as its top (55). The counter's lower half is lifted toward the
    # baseline -- by 0.3 of the pen's horizontal at the very bottom, nothing
    # at the sides -- so the bottom stroke runs 72 into the stem and the
    # counter's lower curve opens; the outer contour, width and height stay.
    cy = C / 2
    inner = [(px, py + th_h * 0.3 * max(0.0, (cy - py) / ry) ** 1.5) for px, py in inner]
    outer = [(edge - s * 0.06, outer[0][1])] + outer + [(edge - s * 0.06, outer[-1][1])]
    inner = [(edge + 1, inner[0][1])] + inner + [(edge + 1, inner[-1][1])]
    P.append(outer); P.append(R.Hole(inner)); return P

def g_E(c):
    P = []; C = capH(c); s = c["s"] * CAP_STEM; x = s / 2; w = _w(c, "E", 420)
    _cstem(c, P, x, 0, C, top="left", foot="left")
    bar(c, P, x, x + w * 0.96, C, serif_ends=[('right', -1)], align="top")
    bar(c, P, x, x + w * 0.74, C * 0.54, thick=0.9)
    bar(c, P, x, x + w, 0, serif_ends=[('right', 1)], align="bottom"); return P

def g_F(c):
    P = []; C = capH(c); s = c["s"] * CAP_STEM; x = s / 2; w = _w(c, "F", 400)
    _cstem(c, P, x, 0, C, top="left", foot="both")
    bar(c, P, x, x + w, C, serif_ends=[('right', -1)], align="top")
    bar(c, P, x, x + w * 0.72, C * 0.54, thick=0.9); return P

def _ramp(v0, v1, t0, t1):
    """A profile that holds v0 up to t0, eases to v1 by t1 and holds it: the
    weight hand-over where one stroke becomes another (G's bowl into its
    spur, J's stem into its hook)."""
    def f(t):
        if t <= t0: return v0
        if t >= t1: return v1
        u = (t - t0) / (t1 - t0); return v0 + (v1 - v0) * (3*u*u - 2*u*u*u)
    return f

def g_G(c):
    P = []; C = capH(c); rx = _w(c, "G", 340); ry = C / 2 + c["over"]; s = c["s"] * CAP_STEM
    th_v = c["pen"].th((0, 1)); th_h = max(c["pen"].th((1, 0)), c["s"] * 0.5); yb = C * 0.46
    # round 34 ("the multiple overlap issue"): the spur was three pieces --
    # the bowl's flared lower terminal, a separate stem and the bar -- and
    # every square end showed: the terminal's corner past the stem's right
    # edge, the stem's foot below the bowl, the stem's top beside the bar.
    # The spur is now the bowl's OWN stroke: the arc stops at 312 degrees,
    # a quadratic bend carries it into a vertical run whose right edge is
    # the bowl's rightmost outer edge (so the outer contour is one line),
    # the weight ramps to the cap stem's over the bend, and the run ends
    # buried at the bar's centerline. The bar then crosses OVER the spur
    # and its pen-cut end hangs a little past it, as the garalde bar does.
    xg = 2 * rx + th_v / 2 - s / 2
    arc = ellipse(rx, C / 2, rx, ry, math.radians(38), math.radians(312), 100, c["k"])
    p0 = arc[-1]; d = (arc[-1][0] - arc[-3][0], arc[-1][1] - arc[-3][1]); L = math.hypot(*d); d = (d[0] / L, d[1] / L)
    ctrl = (xg, p0[1] + d[1] * (xg - p0[0]) / d[0])           # where the arc's end tangent meets the spur's line
    p1 = (xg, ctrl[1] + (ctrl[1] - p0[1]) * 0.7)             # the vertical run begins here
    q1 = (p0[0] + (ctrl[0] - p0[0]) * 2 / 3, p0[1] + (ctrl[1] - p0[1]) * 2 / 3)
    q2 = (p1[0] + (ctrl[0] - p1[0]) * 2 / 3, p1[1] + (ctrl[1] - p1[1]) * 2 / 3)
    bend = bez(p0, q1, q2, p1, 14)[1:]
    run = line(p1, (xg, yb - th_h * 0.3), 6)[1:]                # buried in the bar, 10 units above its underside
    pts = arc + bend + run; N = len(pts) - 1
    t0 = (len(arc) - 1) / N; t1 = (len(arc) + len(bend) - 1) / N
    A.curve(c, P, pts, _ramp(1.0, CAP_STEM, t0, t1), cut0=c["cut"])
    if c["wl"] > 0:
        tn = tangents(pts)[0]; d = (-tn[0], -tn[1]); nrm = (-d[1], d[0])
        P.append(bracket_wedge(pts[0], d, nrm, c["pen"].th(tn) * 1.15, c["wl"] * 0.85, c["wd"] * 0.85, 1, drop=0, fillet=c["fillet"]))
    # the bar's cut end: its top corner 12 inside the spur's right edge, its
    # bottom corner 8 past it -- the run's top corner stays 4 inside the
    # sheared face under the pen's 3-unit jitter
    bar(c, P, 2 * rx - s * 0.55 - rx * 0.55, xg + s * 0.45, yb); return P

def g_H(c):
    P = []; C = capH(c); s = c["s"] * CAP_STEM; x0 = s / 2; x1 = x0 + _w(c, "H", 520)
    _cstem(c, P, x0, 0, C); _cstem(c, P, x1, 0, C, top="right")
    bar(c, P, x0, x1, C * 0.52, thick=0.95); return P

def g_I(c):
    P = []; _cstem(c, P, c["s"] * CAP_STEM / 2, 0, capH(c)); return P

def g_J(c):
    """Round 34 (owner: "remove top bar of J"): the line across the top is
    gone -- this reverses the 2026-09-12 ruling that kept it -- and the stem
    ends in the I's top wedge. Descends a little, as the garalde J does, and
    hooks left. Same round: the stem (cap weight, 1.14 x at its swollen
    foot) used to run half a stem into a hook drawn at the bare pen weight
    and poke 12 units out of it on both sides; the hook now STARTS at the
    stem's foot weight and eases to the pen's by its turn, and the stem's
    last 6% thins to 0.55 so its end face is buried in the hook."""
    P = []; C = capH(c); s = c["s"] * CAP_STEM; r = _w(c, "J", 190); x = r * 1.05 + s / 2
    pts = line((x, r * 0.25 - s * 0.5), (x, C), 36)
    P.append(A.outline(pts, c["pen"], compose(lambda t: c["ent"](t) * CAP_STEM, taper_in(0.55, 0.06))))
    if c["wl"] > 0 and c["serif"] == "wedge":
        th = c["pen"].th((0, 1)) * CAP_STEM
        P.append(bracket_wedge((x, C), (0, 1), (-1, 0), th * c["ent"](1.0), c["wl"], c["wd"], 1, drop=c["drop"], fillet=c["fillet"]))
    tail = bez((x, r * 0.25), (x, -c["desc"] * 0.42), (x - r * 0.55, -c["desc"] * 0.55), (x - r * 1.1, -c["desc"] * 0.1), 40)
    A.curve(c, P, tail, compose(_ramp(CAP_STEM * c["ent"](0.0), 1.0, 0.1, 0.45), flare_end(0.3, 0.35)), cut1=c["cut"]); return P

def g_K(c):
    P = []; C = capH(c); s = c["s"] * CAP_STEM; x = s / 2; w = _w(c, "K", 500)
    _cstem(c, P, x, 0, C, top="left", foot="both")
    # round 26: the arm stopped short of the stem and its serif spiked 0.19 xh
    # above the cap line; it now runs to the stem's center and starts a
    # third of a stem under the cap line, so the wedge's tip lands on it.
    A0, B0 = (x + w, C - s * 0.36), (x, C * 0.45)
    diag(c, P, A0, B0, thin=0.72 / CAP_STEM, serif0=1)
    # round 30: the leg springs from the arm's centerline, its start buried a
    # third of a stem back along the leg (it started 0.1 C under the arm)
    # round 32 ("extend kick of K to match to arm better"): the leg springs
    # from the arm a quarter of the way out from the stem (was 0.42) and is
    # buried a third of a stem into it, so it runs along the arm to the stem.
    # round 34 (owner: "fix the arm vs kick unbalance of K"): the arm ran 30
    # degrees to x + w while the leg fell at 52 degrees and stopped 130 units
    # short of it, a long thin arm over a short thick leg. Now the junction
    # is 0.18 of the way out (0.54 C, 60 units off the stem, Garamond's) and
    # the leg's angle is SOLVED so its foot lands 0.1 stem past the arm's
    # tip -- about 38 degrees, Garamond's leg, still apart from the A's 65
    # and the R's 60. The burial is 0.1 stem: at 0.35 (and still at 0.2)
    # the leg's tapered start face poked out ABOVE the arm, because a leg
    # buried along its own line leaves the arm's band at 0.93 per unit and
    # the arm at 30 degrees is only ~23 units to a side.
    u = 0.18; J = (B0[0] + (A0[0] - B0[0]) * u, B0[1] + (A0[1] - B0[1]) * u)
    angle = math.atan2(J[1], A0[0] + s * 0.1 - J[0])
    kick(c, P, J, s, bury=0.1, angle=angle); return P

def g_L(c):
    P = []; C = capH(c); s = c["s"] * CAP_STEM; x = s / 2; w = _w(c, "L", 420)
    _cstem(c, P, x, 0, C, top="both", foot="left")
    bar(c, P, x, x + w, 0, serif_ends=[('right', 1)], align="bottom"); return P

def g_M(c):
    P = []; C = capH(c); s = c["s"] * CAP_STEM; w = _w(c, "M", 720); x0 = s / 2; x1 = x0 + w
    # splayed: the outer strokes lean out a little; apex on the baseline
    diag(c, P, (x0 + s * 0.25, 0), (x0 + s * 0.45, C), thin=0.72 / CAP_STEM, serif0=-1)
    diag(c, P, (x0 + s * 0.45, C), (x0 + w / 2, 0), thin=1.0 / CAP_STEM)
    diag(c, P, (x1 - s * 0.45, C), (x0 + w / 2, 0), thin=0.72 / CAP_STEM)
    diag(c, P, (x1 - s * 0.25, 0), (x1 - s * 0.45, C), thin=1.0 / CAP_STEM, serif0=1, serif1=-1)
    if c["wl"] > 0:
        P.append(bracket_wedge((x0 + s * 0.45, C), (0, 1), (-1, 0), c["pen"].th((0, 1)) * 0.72, c["wl"] * 0.9, c["wd"], 1, drop=c["drop"], fillet=c["fillet"]))
    return P

def g_N(c):
    P = []; C = capH(c); s = c["s"] * CAP_STEM; w = _w(c, "N", 560); x0 = s / 2; x1 = x0 + w
    _cstem(c, P, x0, 0, C, top="left", foot="both", thin=0.72)
    diag(c, P, (x0 + s * 0.1, C - s * 0.3), (x1 - s * 0.1, s * 0.3), thin=1.0 / CAP_STEM)   # round 33: ends inside both stems
    _cstem(c, P, x1, 0, C, top="right", foot=None, thin=0.72); return P

def g_O(c):
    P = []; C = capH(c); rx = _w(c, "O", 350); cp_ring(c, P, rx, C / 2, rx, C / 2 + c["over"]); return P

def g_P(c):
    P = []; C = capH(c); s = c["s"] * CAP_STEM; x = s / 2; w = _w(c, "P", 400)
    _cstem(c, P, x, 0, C, top="left", foot="both")
    _bowl_stroke(c, P, x, C - c["pen"].th((1, 0)) / 2, C * 0.44, w); return P   # round 33: top edge on the cap line

def g_Q(c):
    P = g_O(c); C = capH(c); rx = _w(c, "O", 350)
    tail = bez((rx * 0.95, C * 0.12), (rx * 1.3, -C * 0.05), (rx * 1.7, -C * 0.28), (rx * 2.1, -C * 0.24), 30)
    A.curve(c, P, tail, compose(taper_in(0.6, 0.2), flare_end(0.25, 0.4)), cut1=c["cut"]); return P

def g_R(c):
    P = []; C = capH(c); s = c["s"] * CAP_STEM; x = s / 2; w = _w(c, "R", 400)
    _cstem(c, P, x, 0, C, top="left", foot="both")
    _bowl_stroke(c, P, x, C - c["pen"].th((1, 0)) / 2, C * 0.46, w * 0.95)   # round 33: top edge on the cap line
    # round 30: the leg springs from the bowl's lower curve (it started under
    # it): its start is the bowl bezier's point at t = 0.8, buried a third of
    # a stem back along the leg.
    J = _bowl_point(x, C - c["pen"].th((1, 0)) / 2, C * 0.46, w * 0.95, 0.8, s)
    kick(c, P, J, s, angle=math.radians(60)); return P   # round 32: the A's leg, a little more upright than the K's (A 65, R 60, K 52)

def g_S(c):
    P = []; C = capH(c); w = _w(c, "S", 440); o = c["over"]; st = c["s"] * CAP_STEM
    spine = catmull([(w * 0.93, C * 0.80), (w * 0.62, C + o * 0.9), (w * 0.18, C * 0.86), (w * 0.2, C * 0.6),
                     (w * 0.8, C * 0.42), (w * 0.84, C * 0.16), (w * 0.42, -o * 0.9), (w * 0.05, C * 0.2)], 16, 0.55)
    tn = tangents(spine); n = len(spine) - 1
    def prof(t):
        i = min(n, int(round(t * n))); th = c["pen"].th(tn[i]); mid = 1.0 - min(1.0, abs(t - 0.5) / 0.28)
        want = th * (1 - mid) + st * 0.92 * mid   # the spine carries the weight
        # round 34 (owner: "make the S bottom heavier"): the lower bowl, t in
        # 0.52..0.96, gains up to 20% at t = 0.74; the top half is untouched
        bot = max(0.0, 1 - abs(t - 0.74) / 0.22); want *= 1 + 0.2 * (3 * bot * bot - 2 * bot ** 3)
        return want / th * flare_end(0.25, 0.1)(t) * flare_end(0.25, 0.1)(1 - t)
    A.curve(c, P, spine, prof)   # round 33: no pen cuts (both terminals were thorns)
    if c["wl"] > 0:   # the C's beak on the top terminal
        d = (-tn[0][0], -tn[0][1]); nrm = (-d[1], d[0])
        P.append(bracket_wedge(spine[0], d, nrm, c["pen"].th(tn[0]) * 1.15, c["wl"] * 0.85, c["wd"] * 0.85, 1, drop=0, fillet=c["fillet"]))
    return P

def g_T(c):
    """Round 25: the bar was stem-heavy, centered on the cap height (so it
    overshot), and pen-cut at the ends under small wedges. Now a thin bar
    whose top IS the cap height, square ends, and a wedge hanging down from
    each arm the size of a stem's foot, the garalde T."""
    P = []; C = capH(c); s = c["s"] * CAP_STEM; w = _w(c, "T", 520); x = w / 2
    th = max(c["pen"].th((1, 0)) * 0.62, c["s"] * 0.45); yb = C - th / 2
    pts = line((0, yb), (w, yb), 12)
    P.append(A.outline(pts, c["pen"], lambda t: th / c["pen"].th((1, 0))))
    if c["wl"] > 0:
        P.append(bracket_wedge((0, yb), (-1, 0), (0, -1), th, c["wl"] * 0.9, c["wd"], 1, drop=0, fillet=c["fillet"]))
        P.append(bracket_wedge((w, yb), (1, 0), (0, 1), th, c["wl"] * 0.9, c["wd"], -1, drop=0, fillet=c["fillet"]))
    _cstem(c, P, x, 0, yb + th * 0.5 - s * 0.05, top=None, foot="both"); return P

def g_U(c):
    """Two stems joined by a bowl that reaches the baseline. The right stem
    is the thin one (the pen's second stroke) and has no foot."""
    P = []; C = capH(c); s = c["s"] * CAP_STEM; w = _w(c, "U", 520); x0 = s / 2; x1 = x0 + w
    y0 = C * 0.42
    _cstem(c, P, x0, y0 - s * 0.5, C, top="both", foot=None)
    # round 26: the bowl sat 0.18 xh under the baseline; the controls are now
    # solved so the curve's centerline bottom is half a stroke above -overshoot.
    yb = -c["over"]; cy = (8 * yb - 2 * y0) / 6   # centerline bottom; over is already the centerline's (round 27)
    pts = bez((x0, y0), (x0, cy), (x1, cy), (x1, y0), 48)
    # round 33: the bowl runs at the LEFT stem's weight and thins to the thin
    # right stem's (0.78) by the time it meets it, so there is no jog
    amt = c["ent"](0.0) - 1.0   # the stems swell at their ends (entasis); the bowl matches where they meet
    bump = lambda t: 1.0 + amt * (max(0.0, 1 - t / 0.15) + max(0.0, 1 - (1 - t) / 0.15))
    A.curve(c, P, pts, compose(lambda t: CAP_STEM * (1 - 0.22 * t), bump, taper_in(0.9, 0.05), taper_out(0.8, 0.12)))
    _cstem(c, P, x1, y0 - s * 0.5, C, top="right+", foot=None, thin=0.78); return P   # round 34: a small left wedge beside the right one

def g_V(c):
    P = []; C = capH(c); s = c["s"] * CAP_STEM; w = _w(c, "V", 560)
    diag(c, P, (s * 0.3, C), (w / 2, 0), thin=1.0 / CAP_STEM, serif0=1)
    diag(c, P, (w - s * 0.3, C), (w / 2 + s * 0.2, 0), thin=0.72 / CAP_STEM, serif0=-1); return P

def g_W(c):
    P = []; C = capH(c); s = c["s"] * CAP_STEM; w = _w(c, "W", 820)
    f1, f2, apex = (w * 0.26, 0), (w * 0.74, 0), (w * 0.5, C)
    # round 34: the four strokes met at the feet and the middle apex with
    # their square ends crossing -- a notch under each foot where the thin
    # stroke's end face crossed the thick one's, and a bumpy top where both
    # inner strokes' faces and a wedge built for a VERTICAL stem stacked at
    # the apex. Now each thin stroke ends 0.35 stem INSIDE the thick stroke
    # it meets (as the A's does under its apex), so the feet are the thick
    # strokes' end faces alone; the middle apex is the inner thick stroke's
    # top face, and the thin stroke's top-left corner sits ON that face's
    # left corner (2.5 units down the edge) so the thin's own left wedge
    # crowns the apex and its bracket flows into the thin's left edge, as
    # the garalde W's does.
    def into(p, q, k=0.35):   # the point k stems from q toward p, inside the stroke p -> q
        dx, dy = p[0] - q[0], p[1] - q[1]; L = math.hypot(dx, dy)
        return (q[0] + dx / L * k * s, q[1] + dy / L * k * s)
    def unit(p, q): dx, dy = q[0] - p[0], q[1] - p[1]; L = math.hypot(dx, dy); return (dx / L, dy / L)
    def stroke(p0, p1, thin, serif0=None):
        # diag() with 40 samples instead of 30. The Cut post-op ROUNDS every
        # polygon under 20 vertices (its serif rule), and a 30-sample line
        # decimated one-in-four keeps 18 or 20 depending on the phase, so two
        # of the four strokes had their end corners cut 25% and the joins
        # built on those corners could not close. 40 samples keep 22-24.
        pts = line(p0, p1, 40)
        P.append(A.outline(pts, c["pen"], lambda t: thin))
        if serif0 and c["wl"] > 0:
            tn = tangents(pts)[0]; d = (-tn[0], -tn[1]); nrm = (-d[1], d[0])
            P.append(bracket_wedge(pts[0], d, nrm, c["pen"].th(tn) * thin, c["wl"] * 0.9, c["wd"] * 0.9, serif0, drop=c["drop"], fillet=c["fillet"]))
    stroke((s * 0.3, C), f1, 1.0, serif0=1)
    d3 = unit(apex, f2); n3 = (-d3[1], d3[0]); th3 = c["pen"].th(d3)
    corner = (apex[0] - n3[0] * th3 / 2 + d3[0] * 2.5, apex[1] - n3[1] * th3 / 2 + d3[1] * 2.5)
    foot1 = into((s * 0.3, C), f1)
    d2 = unit(apex, foot1); n2 = (-d2[1], d2[0]); th2 = c["pen"].th(d2) * 0.72
    stroke((corner[0] + n2[0] * th2 / 2, corner[1] + n2[1] * th2 / 2), foot1, 0.72, serif0=1)
    stroke(apex, f2, 1.0)
    stroke((w - s * 0.3, C), into(apex, f2), 0.72, serif0=-1)
    return P

def g_X(c):
    P = []; C = capH(c); s = c["s"] * CAP_STEM; w = _w(c, "X", 540)
    diag(c, P, (s * 0.3, C), (w - s * 0.3, 0), thin=1.0 / CAP_STEM, serif0=1, serif1=1)
    diag(c, P, (w - s * 0.3, C), (s * 0.3, 0), thin=0.72 / CAP_STEM, serif0=-1, serif1=-1); return P

def g_Y(c):
    P = []; C = capH(c); s = c["s"] * CAP_STEM; w = _w(c, "Y", 540)
    diag(c, P, (s * 0.3, C), (w / 2, C * 0.45), thin=1.0 / CAP_STEM, serif0=1)
    diag(c, P, (w - s * 0.3, C), (w / 2, C * 0.45), thin=0.72 / CAP_STEM, serif0=-1)
    _cstem(c, P, w / 2, 0, C * 0.45 + s * 0.35, top=None, foot="both"); return P

def g_Z(c):
    P = []; C = capH(c); s = c["s"] * CAP_STEM; w = _w(c, "Z", 500)
    th = max(c["pen"].th((1, 0)), c["s"] * 0.5)
    bar(c, P, 0, w, C, serif_ends=[('left', -1)], align="top")
    zd = line((w - s * 0.15, C - th / 2), (s * 0.15, th / 2), 30); tz = tangents(zd)[0]
    A.curve(c, P, zd, lambda t: s / c["pen"].th(tz))
    bar(c, P, 0, w, 0, serif_ends=[('right', 1)], align="bottom"); return P

# ---------------------------------------------------------------- figures (lining)
def g_zero(c):
    P = []; D = figH(c); rx = _w(c, "0", 230); cp_ring(c, P, rx, D / 2, rx, D / 2 + c["over"]); return P

def g_one(c):
    P = []; D = figH(c); s = c["s"]; x = 200 * c["wf"] + s / 2
    vstem(c, P, x, 0, D, top_sides=(), foot_sides=(-1, 1))
    A.curve(c, P, line((x - 150 * c["wf"], D * 0.72), (x, D), 12), lambda t: 0.85, cut0=c["cut"]); return P

def g_two(c):
    P = []; D = figH(c); s = c["s"]; w = _w(c, "2", 440); rx = w * 0.46
    top = ellipse(rx, D - rx * 0.95, rx, rx * 0.95, math.radians(190), math.radians(-25), 60, c["k"])
    A.curve(c, P, top, flare_end(0.2, 0.15), cut0=c["cut"])
    diag(c, P, top[-1], (s * 0.2, 0))
    bar(c, P, 0, w, 0, serif_ends=[('right', 1)]); return P

def g_three(c):
    P = []; D = figH(c); w = _w(c, "3", 400); r1 = D * 0.24; r2 = D * 0.28
    top = ellipse(w * 0.5, D - r1, w * 0.48, r1, math.radians(175), math.radians(-60), 50, c["k"])
    bot = ellipse(w * 0.5, r2, w * 0.54, r2 + c["over"], math.radians(60), math.radians(-175), 60, c["k"])
    A.curve(c, P, top, flare_end(0.2, 0.15), cut0=c["cut"])
    A.curve(c, P, bot, compose(taper_in(0.6, 0.1), flare_end(0.25, 0.15)), cut1=c["cut"]); return P

def g_four(c):
    P = []; D = figH(c); s = c["s"]; w = _w(c, "4", 480); xs = w * 0.7
    diag(c, P, (xs - s * 0.2, D), (s * 0.1, D * 0.3), thin=0.75)
    bar(c, P, 0, w, D * 0.3)
    vstem(c, P, xs, 0, D, top_sides=(), foot_sides=(-1, 1)); return P

def g_five(c):
    P = []; D = figH(c); s = c["s"]; w = _w(c, "5", 400); r = D * 0.31
    bar(c, P, s * 0.3, w * 0.95, D, serif_ends=[('right', -1)])
    vstem(c, P, s * 0.3 + s / 2, D * 0.5, D, top_sides=(), foot_sides=(), thin=0.85, flare=False)
    bowl = ellipse(w * 0.5, r, w * 0.55, r + c["over"], math.radians(125), math.radians(-160), 70, c["k"])
    A.curve(c, P, bowl, compose(taper_in(0.55, 0.12), flare_end(0.25, 0.15)), cut1=c["cut"]); return P

def g_six(c):
    P = []; D = figH(c); rx = _w(c, "6", 230); r = D * 0.29
    top = ellipse(rx, D - rx * 1.0, rx * 0.95, rx * 1.0, math.radians(70), math.radians(180), 40, c["k"])
    A.curve(c, P, top, flare_end(0.25, 0.2), cut0=c["cut"])
    left = line(top[-1], (rx * 0.05, r), 16); A.curve(c, P, left)
    cp_ring(c, P, rx, r, rx, r + c["over"]); return P

def g_seven(c):
    P = []; D = figH(c); s = c["s"]; w = _w(c, "7", 440)
    bar(c, P, 0, w, D, serif_ends=[('left', -1)])
    diag(c, P, (w - s * 0.2, D), (w * 0.3, 0)); return P

def g_eight(c):
    P = []; D = figH(c); rx = _w(c, "8", 215); r1 = D * 0.235; r2 = D * 0.265
    cp_ring(c, P, rx, D - r1, rx * 0.86, r1); cp_ring(c, P, rx, r2, rx, r2 + c["over"]); return P

def g_nine(c):
    """A six turned over: counterpunched bowl at the top, the tail runs down
    the right side and curls to the bottom-left (the first draft ran the
    curl the other way and read as a mirrored e)."""
    P = []; D = figH(c); rx = _w(c, "9", 230); r = D * 0.29; s = c["s"]
    cp_ring(c, P, rx, D - r, rx, r)
    bot = ellipse(rx, rx * 1.0, rx * 0.95, rx * 1.0, math.radians(0), math.radians(-110), 40, c["k"])
    right = line((rx * 2 - s * 0.5, D - r), bot[0], 16); A.curve(c, P, right)
    A.curve(c, P, bot, flare_end(0.25, 0.2), cut1=c["cut"]); return P

# ---------------------------------------------------------------- punctuation
def dot(c, x, y, r=0.55): return blob((x, c["s"] * r + 0 if False else y), c["s"] * r)

def g_period(c): r = capH(c) * 0.08; return [blob((r, r), r)]
def g_comma(c):
    s = c["s"]; x = s * 0.55; P = [blob((x, s * 0.55), s * 0.55)]
    tail = bez((x + s * 0.1, s * 0.2), (x + s * 0.1, -s * 0.5), (x - s * 0.3, -s * 0.9), (x - s * 0.6, -s * 1.2), 20)
    P.append(A.outline(tail, c["pen"], lambda t: 0.9 - 0.6 * t)); return P
def g_colon(c): s = c["s"]; return [blob((s * 0.55, s * 0.55), s * 0.55), blob((s * 0.55, c["xh"] - s * 0.55), s * 0.55)]
def g_semicolon(c):
    P = g_comma(c); P.append(blob((c["s"] * 0.55, c["xh"] - c["s"] * 0.55), c["s"] * 0.55)); return P
def g_exclam(c):
    s = c["s"]; C = capH(c); P = [blob((s * 0.55, s * 0.55), s * 0.55)]
    P.append(A.outline(line((s * 0.55, s * 1.9), (s * 0.55, C), 20), c["pen"], lambda t: 0.55 + 0.5 * t, cut1=c["cut"])); return P
def g_question(c):
    s = c["s"]; C = capH(c); w = 380 * c["wf"]; P = [blob((w * 0.5, s * 0.55), s * 0.55)]
    hook = catmull([(w * 0.08, C * 0.74), (w * 0.28, C * 0.97), (w * 0.62, C * 0.98), (w * 0.88, C * 0.74),
                    (w * 0.74, C * 0.5), (w * 0.5, C * 0.38), (w * 0.5, C * 0.2)], 14, 0.5)
    A.curve(c, P, hook, compose(taper_in(0.55, 0.15), flare_end(0.1, 0.2)), cut0=c["cut"], cut1=c["cut"]); return P
def g_quotesingle(c):
    s = c["s"]; C = capH(c); return [A.outline(line((s * 0.5, C * 0.72), (s * 0.5, C), 8), c["pen"], lambda t: 0.8, cut0=c["cut"])]
def g_quotedbl(c):
    P = g_quotesingle(c); P.extend([[(x + c["s"] * 1.3, y) for x, y in p] for p in g_quotesingle(c)]); return P
def _quote(c, x, up):
    s = c["s"]; C = capH(c); y = C - s * 0.55
    P = [blob((x, y), s * 0.5)]
    if up: tail = bez((x + s * 0.1, y - s * 0.3), (x + s * 0.1, y - s * 1.0), (x - s * 0.3, y - s * 1.3), (x - s * 0.55, y - s * 1.6), 16)
    else:  tail = bez((x - s * 0.1, y + s * 0.3), (x - s * 0.1, y + s * 1.0), (x + s * 0.3, y + s * 1.3), (x + s * 0.55, y + s * 1.6), 16)
    P.append(A.outline(tail, c["pen"], lambda t: 0.85 - 0.55 * t)); return P
def g_quoteright(c): return _quote(c, c["s"] * 0.7, True)
def g_quoteleft(c): return [[(x, capH(c) - (y - capH(c) * 0.0) + capH(c) * 0.0) for x, y in p] for p in []] or _quote(c, c["s"] * 0.7, False)
def g_quotedblright(c): P = _quote(c, c["s"] * 0.7, True); P.extend(_quote(c, c["s"] * 2.0, True)); return P
def g_quotedblleft(c): P = _quote(c, c["s"] * 0.7, False); P.extend(_quote(c, c["s"] * 2.0, False)); return P
def g_hyphen(c): return [A.outline(line((0, capH(c) * 0.34), (0.37 * capH(c), capH(c) * 0.34), 8), c["pen"])]
def g_endash(c): return [A.outline(line((0, capH(c) * 0.34), (0.72 * capH(c), capH(c) * 0.34), 8), c["pen"])]
def g_emdash(c): return [A.outline(line((0, capH(c) * 0.34), (1.41 * capH(c), capH(c) * 0.34), 8), c["pen"])]
def g_parenleft(c):
    C = capH(c); d = c["desc"]; r = 150 * c["wf"]
    pts = ellipse(r, (C - d) / 2, r, (C + d) / 2 + 30, math.radians(105), math.radians(255), 50, 2.2)
    return [A.outline(pts, c["pen"], lambda t: 0.6 + 0.4 * math.sin(math.pi * t), cut0=c["cut"], cut1=c["cut"])]
def g_parenright(c):
    C = capH(c); d = c["desc"]; r = 150 * c["wf"]
    pts = ellipse(0, (C - d) / 2, r, (C + d) / 2 + 30, math.radians(75), math.radians(-75), 50, 2.2)
    return [A.outline(pts, c["pen"], lambda t: 0.6 + 0.4 * math.sin(math.pi * t), cut0=c["cut"], cut1=c["cut"])]
def g_bracketleft(c):
    C = capH(c); d = c["desc"]; s = c["s"]; w = 180 * c["wf"]
    return [A.outline(line((s * 0.4, -d), (s * 0.4, C), 20), c["pen"], lambda t: 0.85), A.outline(line((s * 0.4, C), (w, C), 6), c["pen"]), A.outline(line((s * 0.4, -d), (w, -d), 6), c["pen"])]
def g_bracketright(c):
    C = capH(c); d = c["desc"]; s = c["s"]; w = 180 * c["wf"]
    return [A.outline(line((w - s * 0.4, -d), (w - s * 0.4, C), 20), c["pen"], lambda t: 0.85), A.outline(line((0, C), (w - s * 0.4, C), 6), c["pen"]), A.outline(line((0, -d), (w - s * 0.4, -d), 6), c["pen"])]
def g_slash(c): C = capH(c); return [A.outline(line((0, -c["desc"] * 0.4), (330 * c["wf"], C), 20), c["pen"], lambda t: 0.8, cut0=c["cut"], cut1=c["cut"])]
def g_backslash(c): C = capH(c); return [A.outline(line((0, C), (330 * c["wf"], -c["desc"] * 0.4), 20), c["pen"], lambda t: 0.8, cut0=c["cut"], cut1=c["cut"])]
def g_asterisk(c):
    C = capH(c); cx, cy = 200 * c["wf"], C * 0.78; r = 150 * c["wf"]; P = []
    for k in range(5):
        a = math.pi / 2 + k * 2 * math.pi / 5
        P.append(A.outline(line((cx, cy), (cx + r * math.cos(a), cy + r * math.sin(a)), 8), c["pen"], lambda t: 0.75, cut1=c["cut"]))
    return P
def g_plus(c):
    y = c["xh"] * 0.55; w = 420 * c["wf"]
    return [A.outline(line((0, y), (w, y), 8), c["pen"], lambda t: 0.9), A.outline(line((w / 2, y - w / 2), (w / 2, y + w / 2), 8), c["pen"], lambda t: 0.9)]
def g_equal(c):
    y = c["xh"] * 0.55; w = 420 * c["wf"]; g = c["s"] * 1.1
    return [A.outline(line((0, y - g / 2), (w, y - g / 2), 8), c["pen"]), A.outline(line((0, y + g / 2), (w, y + g / 2), 8), c["pen"])]
def g_ampersand(c):
    C = capH(c); w = 760 * c["wf"]; o = c["over"]
    spine = catmull([(w * 0.95, C * 0.36), (w * 0.62, 0.0 - o * 0.4), (w * 0.15, C * 0.18), (w * 0.3, C * 0.5), (w * 0.62, C * 0.8),
                     (w * 0.6, C + o * 0.5), (w * 0.35, C * 0.92), (w * 0.34, C * 0.62), (w * 0.62, C * 0.32), (w * 0.98, C * 0.02)], 14, 0.5)
    return [A.outline(spine, c["pen"], compose(flare_end(0.2, 0.1), lambda t: flare_end(0.2, 0.12)(1 - t)), cut0=c["cut"], cut1=c["cut"])]
def g_percent(c):
    C = capH(c); P = []; r = 120 * c["wf"]
    P.extend(g_slash_at(c, 60 * c["wf"], 0, 60 * c["wf"] + 380 * c["wf"], C))
    R = _round17()
    for cx, cy in ((r + 10, C - r), (620 * c["wf"] - r, r)):
        outer, inner = R.ring(c, cx, cy, r, r, 0, 2 * math.pi, 60); P.append(outer); P.append(R.Hole(inner))
    return P
def g_slash_at(c, x0, y0, x1, y1): return [A.outline(line((x0, y0), (x1, y1), 20), c["pen"], lambda t: 0.75, cut0=c["cut"], cut1=c["cut"])]
def g_numbersign(c):
    C = capH(c); w = 480 * c["wf"]; P = []
    for x in (w * 0.32, w * 0.68): P.append(A.outline(line((x - w * 0.06, 0), (x + w * 0.06, C), 10), c["pen"], lambda t: 0.75))
    for y in (C * 0.35, C * 0.65): P.append(A.outline(line((0, y), (w, y), 8), c["pen"]))
    return P
def g_at(c):
    xh = c["xh"]; C = capH(c); w = 860 * c["wf"]; cx, cy = w * 0.5, xh * 0.5; P = []
    R = _round17()
    outer, inner = R.ring(c, cx + 20, cy, 170 * c["wf"], xh * 0.5, 0, 2 * math.pi, 70); P.append(outer); P.append(R.Hole(inner))
    P.append(A.outline(line((cx + 190 * c["wf"], xh * 0.95), (cx + 190 * c["wf"], 0.0), 16), c["pen"], lambda t: 0.8))
    big = ellipse(cx, cy, w * 0.5, xh * 0.55 + c["desc"] * 0.6, math.radians(-20), math.radians(300), 90, 2.2)
    P.append(A.outline(big, c["pen"], compose(flare_end(0.2, 0.1), lambda t: flare_end(0.2, 0.1)(1 - t)), cut0=c["cut"], cut1=c["cut"])); return P
def g_underscore(c): return [A.outline(line((0, -c["desc"] * 0.5), (500 * c["wf"], -c["desc"] * 0.5), 8), c["pen"])]
def g_ellipsis(c):
    s = c["s"]; return [blob((s * 0.55 + i * s * 2.4, s * 0.55), s * 0.55) for i in range(3)]

CAPS = {chr(k): globals()["g_" + chr(k)] for k in range(ord('A'), ord('Z') + 1)}
FIGS = {'0': g_zero, '1': g_one, '2': g_two, '3': g_three, '4': g_four, '5': g_five, '6': g_six, '7': g_seven, '8': g_eight, '9': g_nine}
PUNCT = {'.': g_period, ',': g_comma, ':': g_colon, ';': g_semicolon, '!': g_exclam, '?': g_question, "'": g_quotesingle, '"': g_quotedbl,
         '‘': g_quoteleft, '’': g_quoteright, '“': g_quotedblleft, '”': g_quotedblright,
         '-': g_hyphen, '–': g_endash, '—': g_emdash, '(': g_parenleft, ')': g_parenright, '[': g_bracketleft, ']': g_bracketright,
         '/': g_slash, '\\': g_backslash, '*': g_asterisk, '+': g_plus, '=': g_equal, '&': g_ampersand, '%': g_percent, '#': g_numbersign,
         '@': g_at, '_': g_underscore, '…': g_ellipsis}

SIDES = {
 'A': ('diag', 'diag'), 'B': ('straight', 'round'), 'C': ('round', 'open'), 'D': ('straight', 'round'), 'E': ('straight', 'open'),
 'F': ('straight', 'open'), 'G': ('round', 'straight'), 'H': ('straight', 'straight'), 'I': ('straight', 'straight'), 'J': ('open', 'straight'),
 'K': ('straight', 'diag'), 'L': ('straight', 'open'), 'M': ('straight', 'straight'), 'N': ('straight', 'straight'), 'O': ('round', 'round'),
 'P': ('straight', 'round'), 'Q': ('round', 'round'), 'R': ('straight', 'diag'), 'S': ('round', 'round'), 'T': ('open', 'open'),
 'U': ('straight', 'straight'), 'V': ('diag', 'diag'), 'W': ('diag', 'diag'), 'X': ('diag', 'diag'), 'Y': ('diag', 'diag'), 'Z': ('straight', 'straight'),
 '0': ('round', 'round'), '1': ('open', 'straight'), '2': ('round', 'straight'), '3': ('open', 'round'), '4': ('diag', 'straight'),
 '5': ('straight', 'round'), '6': ('round', 'round'), '7': ('straight', 'diag'), '8': ('round', 'round'), '9': ('round', 'round'),
}
for k in PUNCT: SIDES.setdefault(k, ('punct', 'punct'))
