"""v w x y z k: the diagonals, wedges on the outer side (0.9 x 0.9); the
thin strokes at 0.72 of the thick; the k's leg the A's kick at 56 degrees."""
import math
from . import glyph
from .. import geom, pen
from ..geom import cubic, line
from ..primitives import stem, diagonal, stroke, pen_widths, widths, wedge, diag_wedge, end_wedge, bar
from ..pen import S, XH, OVER, TH_V, TH_H, HAIR, CUT, WL, WD, DROP, ENT

def pw(p0, p1, mult=1.0):
    """Round 51's rule for every diagonal (`_diag`): the width is `mult` x
    the PEN's width at the stroke's own angle -- a down-right stroke is the
    pen's broad ~82, a down-left one its thin ~50, and 0.72 of THAT is the
    thin stroke of v w x y (36-40), not 0.72 of the stem."""
    tn = geom.tangents(line(p0, p1))[0]; return pen.th_t(tn) * mult

@glyph('v')
def g_v(c):
    xh = c["xh"]; wf = c["wf"]; w = 440 * wf
    p0, p1 = (S * 0.4, xh), (w / 2, 0); q0, q1 = (w - S * 0.4, xh), (w / 2 + S * 0.12, 0)
    return geom.ink([diagonal(p0, p1, pw(p0, p1), serif0=1), diagonal(q0, q1, pw(q0, q1, 0.72), serif0=-1)])

def _clean_apex_notch(b, d, apex, apex_x, apex_y, band=110):
    """Owner 2026-09-13: "clean up top middle of 'w'." Two defects at the
    vertex where b and d (different angles, different widths) share one
    start point:
    1. Their own square end faces aren't collinear, so the apex `wedge()`
       (built for a near-VERTICAL stem's edge, per its docstring) only
       closes part of the gap between them, leaving a second, smaller peak
       and a notch beside the crown. Fixed by taking the convex hull of the
       three shapes near the apex and adding back only the sliver the hull
       found and the ink didn't -- i.e. the actual notch, not the legs'
       intentional counter below it (`band` keeps the patch to the region
       right at the vertex).
    2. Below that, the two strokes' INNER edges cross a second time (the
       thin b and the thick d meet the shared point at different widths, so
       their near edges don't meet at one clean point either) and leave a
       thin ink spike stabbing down into the counter -- present even before
       fix 1, at 600 px. A morphological opening (erode then dilate) removes
       a spike thinner than 2 x its radius while leaving a straight stroke
       of ordinary width alone; applied only inside a local window at the
       vertex so neither leg is touched anywhere else (checked: leg cross-
       section width off-window is bit-for-bit unchanged)."""
    core = geom.union([b, d, apex])
    missing = core.convex_hull.difference(core)
    pieces = missing.geoms if hasattr(missing, 'geoms') else [missing]
    cands = [g for g in pieces if g.area > 5 and g.bounds[1] >= apex_y - 10 and g.bounds[3] <= apex_y + band]
    patched = core if not cands else geom.union([core, min(cands, key=lambda g: g.area).buffer(0.5, join_style=2)])
    from shapely.geometry import box
    r = 0.24 * S   # > half the thin stroke's width (so the spike, thinner still, is eroded away) and < half the thin stroke's own width margin at this window's edge
    win = box(apex_x - 110, apex_y - 160, apex_x + 110, apex_y + 20)
    inside, outside = patched.intersection(win), patched.difference(win)
    opened = inside.buffer(-r, join_style=2).buffer(r, join_style=2)
    return geom.union([outside, opened])

@glyph('w')
def g_w(c):
    xh = c["xh"]; wf = c["wf"]; w = 680 * wf
    P = [((S * 0.4, xh), (w * 0.27, 0), 1.0, 1), ((w * 0.5, xh * 0.96), (w * 0.27 + S * 0.12, 0), 0.72, None),
         ((w * 0.5, xh * 0.96), (w * 0.73, 0), 1.0, None), ((w - S * 0.4, xh), (w * 0.73 + S * 0.12, 0), 0.72, -1)]
    a, b, d, e = [diagonal(p0, p1, pw(p0, p1, m), serif0=sf) for p0, p1, m, sf in P]
    apex_y = xh * 0.96
    # the depth was 0.9 x WD (only this glyph); the family's apex wedge
    # (M, W) is 0.9 x 1.0 -- matched here too, so the bracket reaches as
    # far into the strokes as it does everywhere else it's used
    apex_x = w * 0.5 - pw(P[1][0], P[1][1], 0.72) * 0.36
    apex = wedge((apex_x, apex_y), (0, 1), (-1, 0), WL * 0.9, WD, DROP)
    mid = _clean_apex_notch(b, d, apex, apex_x, apex_y)
    return geom.ink([a, e, mid])

@glyph('x')
def g_x(c):
    xh = c["xh"]; wf = c["wf"]; w = 430 * wf
    p0, p1 = (S * 0.4, xh), (w - S * 0.4, 0); q0, q1 = (w - S * 0.4, xh), (S * 0.4, 0)
    return geom.ink([diagonal(p0, p1, pw(p0, p1), serif0=1, serif1=1), diagonal(q0, q1, pw(q0, q1, 0.72), serif0=-1, serif1=-1)])

@glyph('y')
def g_y(c):
    xh = c["xh"]; wf = c["wf"]; desc = c["desc"]; w = 440 * wf
    p0, p1 = (S * 0.4, xh), (w / 2 + S * 0.1, -S * 0.4)
    a = diagonal(p0, p1, pw(p0, p1), serif0=1)
    tail = cubic((w - S * 0.4, xh), (w * 0.52, -desc * 0.55), (w * 0.44, -desc * 1.08), (w * 0.02, -desc * 0.95))
    # round 51: the pen's width along the tail x (0.72 rising to 1.0 by the middle), flaring 0.3 into the cut
    wfn = pen_widths(tail, lambda t: (0.72 + 0.28 * min(1.0, t * 2)) * widths([(0.7, 1.0), (1.0, 1.3)])(t))
    t = stroke(tail, wfn, cut1=CUT)
    return geom.ink([a, t, end_wedge(tail, wfn(0.0), True, -1)])

@glyph('z')
def g_z(c):
    """Owner 2026-09-13, verbatim: "cleanup 'Z' and 'z' bottom left and top
    right." The pen cut was on the wrong end of each bar: it sat on the end
    the DIAGONAL crosses (top bar's right, bottom bar's left), a square
    stroke end sheared against the diagonal's own square end, which is what
    put a stray sliver spike at the top-right and bottom-left corners. The
    capital Z (`g_Z`, caps_straight.py) puts the cut on the WEDGE end
    instead, where the wedge polygon covers it -- the diagonal-facing end
    stays square and the diagonal's own square end closes it cleanly. Same
    fix here: cut0 on the top bar (under its left wedge), cut1 on the
    bottom bar (under its right wedge), neither on the end the diagonal
    meets."""
    xh = c["xh"]; wf = c["wf"]; w = 400 * wf
    th = max(TH_H, S * 0.55)
    yt = xh - th / 2; yb = th / 2
    t = bar(0, w, xh, th, align='top', cut0=CUT, wedges=[('left', -1)])
    b = bar(0, w, 0, th, align='bottom', cut1=CUT, wedges=[('right', 1)])
    d = diagonal((w - S * 0.15, yt), (S * 0.15, yb), S)
    return geom.ink([t, b, d])

@glyph('k')
def g_k(c):
    """Stem, an arm from the stem at 0.42 xh to the x-height, and the leg
    springing from the arm at the A's kick, 56 degrees (ruling).

    Owner 2026-09-13, verbatim: "add some weight to the top right kick of
    'k' to balance it out visually and reduce overlap of bottom right
    stroke." ARM_WEIGHT is the ladder's default (x1.30 of round 51's 0.78
    pen-mult; the page also builds 1.15 and 1.45). The leg used to spring
    from a point ON THE ARM'S CENTERLINE and bury straight through it,
    crossing both edges and knotting; it now springs from the arm's LOWER
    edge (LEG_EDGE) and buries only LEG_BURY (a fifth of a stem, the
    join-rule minimum) past that edge, thinning sooner (LEG_TAPER) so the
    join reads as one clean fork instead of an X."""
    ARM_WEIGHT = 1.30
    LEG_EDGE = 1.0            # spring the leg from the arm's lower edge (1.0), not its centerline (0.0)
    LEG_BURY = 0.20           # x stem, past that edge (join rule: a fifth to a third of a stem)
    LEG_TAPER = (0.55, 0.35)  # thin from t=0.55 (was 0.78) to 0.35 x lw (was 0.55) at the buried tip
    xh = c["xh"]; wf = c["wf"]; x = S / 2
    st = stem(x, 0, c["asc"], top='left', foot='both')
    A0, B0 = (x + 360 * wf, xh * 0.97), (x + S * 0.2, xh * 0.42)
    arm_w = pw(A0, B0, 0.78 * ARM_WEIGHT)   # round 51's 0.78 x the pen at the arm's angle, x the ladder weight
    arm = diagonal(A0, B0, arm_w, serif0=1)
    u = (150 * wf - (B0[0] - x)) / (A0[0] - B0[0]); J = (B0[0] + (A0[0] - B0[0]) * u, B0[1] + (A0[1] - B0[1]) * u)
    # the arm's own direction and its outward normal, to find the arm's
    # lower edge at J instead of J's centerline point
    ad = (A0[0] - B0[0], A0[1] - B0[1]); aL = math.hypot(*ad); ad = (ad[0] / aL, ad[1] / aL)
    an = (-ad[1], ad[0])
    if an[0] < 0: an = (-an[0], -an[1])
    J_edge = (J[0] + an[0] * arm_w / 2 * LEG_EDGE, J[1] + an[1] * arm_w / 2 * LEG_EDGE)
    foot = (J[0] + J[1] / math.tan(math.radians(56)), 0)
    d = (J[0] - foot[0], J[1] - foot[1]); L = math.hypot(*d); d = (d[0] / L, d[1] / L)
    lw = pw(foot, J)   # round 51: the pen at the leg's angle (58 at 56 degrees)
    tip = (J_edge[0] + d[0] * S * LEG_BURY, J_edge[1] + d[1] * S * LEG_BURY)
    leg = diagonal(foot, tip, widths([(0.0, lw), (LEG_TAPER[0], lw), (1.0, lw * LEG_TAPER[1])]), serif0=1)
    return geom.ink([st, arm, leg])
