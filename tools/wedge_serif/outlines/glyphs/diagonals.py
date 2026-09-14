"""v w x y z k: the diagonals, wedges on the outer side (0.9 x 0.9); the
thin strokes at 0.72 of the thick; the k's leg the A's kick at 56 degrees."""
import math
from . import glyph
from .. import geom, pen
from ..geom import cubic, line
from ..primitives import stem, diagonal, stroke, pen_widths, widths, wedge, diag_wedge, end_wedge, bar
from ..pen import S, XH, OVER, TH_V, TH_H, HAIR, CUT, WL, WD, DROP, ENT, adj

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
    tm = 0.68 if adj('w') else 0.72   # round 92 (adj 'w'): the darkest wide letter, its thins 0.72 -> 0.68 of the pen
    P = [((S * 0.4, xh), (w * 0.27, 0), 1.0, 1), ((w * 0.5, xh * 0.96), (w * 0.27 + S * 0.12, 0), tm, None),
         ((w * 0.5, xh * 0.96), (w * 0.73, 0), 1.0, None), ((w - S * 0.4, xh), (w * 0.73 + S * 0.12, 0), tm, -1)]
    a, b, d, e = [diagonal(p0, p1, pw(p0, p1, m), serif0=sf) for p0, p1, m, sf in P]
    apex_y = xh * 0.96
    # the depth was 0.9 x WD (only this glyph); the family's apex wedge
    # (M, W) is 0.9 x 1.0 -- matched here too, so the bracket reaches as
    # far into the strokes as it does everywhere else it's used
    apex_x = w * 0.5 - pw(P[1][0], P[1][1], tm) * 0.36
    apex = wedge((apex_x, apex_y), (0, 1), (-1, 0), WL * 0.9, WD, DROP)
    mid = _clean_apex_notch(b, d, apex, apex_x, apex_y)
    return geom.ink([a, e, mid])

X_BL_WEDGE = 1.15   # the x's bottom-left wedge, x the family's diagonal end (0.9 is the family's own)
X_BL_WIDTH = 1.0    # the width the wedge is sized on: the THICK diagonal's (1.0), not the thin's

@glyph('x')
def g_x(c):
    xh = c["xh"]; wf = c["wf"]; w = 430 * wf
    p0, p1 = (S * 0.4, xh), (w - S * 0.4, 0); q0, q1 = (w - S * 0.4, xh), (S * 0.4, 0)
    # owner 2026-09-14: "increase the visual weight of the bottom left serif
    # in 'x'" -- that serif ends the THIN diagonal, so the family's wedge
    # scaled on the thin stroke's width is small; it is drawn on the thick
    # diagonal's width instead, at X_BL_WEDGE of the family's diagonal end
    thin = diagonal(q0, q1, pw(q0, q1, 0.72), serif0=-1)
    bl = end_wedge([q0, q1], pw(q0, q1) * X_BL_WIDTH, False, -1, scale=X_BL_WEDGE)
    return geom.ink([diagonal(p0, p1, pw(p0, p1), serif0=1, serif1=1), thin, bl])

# owner 2026-09-14 ("Beyond", "Tuesday"): "the 'y' is too dark in a word
# currently. thin out the left stroke of 'y' by decreasing its width, but
# leave the left side of the character as is." Y_LEFT_W x the pen's width
# for the left diagonal; the stroke's centerline moves toward its inner
# (upper-right) edge by half the width lost, so the outer (lower-left) edge
# and the serif on it stay where they were. Chosen on the in-word
# measurement (outlines/cmp/balance.py) and the eye, round 88.
Y_LEFT_W = float(__import__('os').environ.get('FJORD_Y_LEFT_W', 0.97))   # owner 2026-09-14, round 90: "0.9 is slightly too thin for 500", then ".97" from the 0.92-0.98 ladder

@glyph('y')
def g_y(c):
    xh = c["xh"]; wf = c["wf"]; desc = c["desc"]; w = 440 * wf
    p0, p1 = (S * 0.4, xh), (w / 2 + S * 0.1, -S * 0.4)
    w_full = pw(p0, p1); w_left = w_full * Y_LEFT_W
    if Y_LEFT_W != 1.0:
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]; L = math.hypot(dx, dy)
        nx, ny = -dy / L, dx / L            # the left normal of a down-right stroke points up-right: the inner edge
        sh = (w_full - w_left) / 2
        # the centerline moves TOWARD the edge that stays (outer = center - n w/2 is fixed when center moves by -n sh)
        p0 = (p0[0] - nx * sh, p0[1] - ny * sh); p1 = (p1[0] - nx * sh, p1[1] - ny * sh)
    a = diagonal(p0, p1, w_left, serif0=1)
    tail = cubic((w - S * 0.4, xh), (w * 0.52, -desc * 0.55), (w * 0.44, -desc * 1.08), (w * 0.02, -desc * 0.95))
    # round 51: the pen's width along the tail x (0.72 rising to 1.0 by the middle), flaring 0.3 into the cut
    wfn = pen_widths(tail, lambda t: (0.72 + 0.28 * min(1.0, t * 2)) * widths([(0.7, 1.0), (1.0, 1.3)])(t))
    t = stroke(tail, wfn, cut1=CUT)
    return geom.ink([a, t, end_wedge(tail, wfn(0.0), True, -1)])

@glyph('z')
def g_z(c):
    """Owner 2026-09-13, on the cleanup: "'z' is much worse, you are
    half-assing it and I need better." Read against Albertus and Berkeley:
    in both the z's DIAGONAL is the heavy stroke and the bars are light,
    and the corners where the diagonal meets the bars are mitred on the
    diagonal's own line -- the ruled Z construction (round 82: mitre, the
    bottom bar run out to the top corner's x). So the z is the Z at
    x-height: bars at Z_BAR of the stem with the top's hanging wedge at the
    left and the bottom's rising wedge at the right, the diagonal at
    Z_DIAG x S, each bar's end at the diagonal cut along the diagonal's
    outer edge, the bottom bar run out so both right edges share one x."""
    from shapely.geometry import Polygon, box as _box
    xh = c["xh"]; wf = c["wf"]; w = 400 * wf
    th = S * (Z_BAR_ADJ if adj('z') else Z_BAR); dw = S * (Z_DIAG_ADJ if adj('z') else Z_DIAG)
    p_top, p_bot = (w - S * 0.12, xh - th / 2), (S * 0.12, th / 2)
    dg = diagonal(p_top, p_bot, dw)
    dx, dy = p_top[0] - p_bot[0], p_top[1] - p_bot[1]; L = math.hypot(dx, dy); dx, dy = dx / L, dy / L
    nx, ny = dy, -dx
    ox, oy = p_top[0] + nx * dw / 2, p_top[1] + ny * dw / 2
    corner = (ox + dx * (xh - oy) / dy, xh)
    ox2, oy2 = p_bot[0] - nx * dw / 2, p_bot[1] - ny * dw / 2
    corner2 = (ox2 + dx * (0.0 - oy2) / dy, 0.0)
    far = 4000.0
    def half(cn, sign):
        u = (dx * far, dy * far); n = (nx * far * sign, ny * far * sign)
        return Polygon([(cn[0] + u[0], cn[1] + u[1]), (cn[0] - u[0], cn[1] - u[1]), (cn[0] - u[0] + n[0], cn[1] - u[1] + n[1]), (cn[0] + u[0] + n[0], cn[1] + u[1] + n[1])])
    t = bar(0, max(w, corner[0] + 2), xh, th, align='top', cut0=CUT, wedges=[('left', -1)])
    bt = bar(min(0, corner2[0] - 2), corner[0], 0, th, align='bottom', cut1=CUT, wedges=[('right', 1)])
    g = geom.ink([t, bt, dg])
    cut_tr = half(corner, +1).intersection(_box(corner[0] - S * 2, xh - th - 2, corner[0] + far, xh + far))
    cut_bl = half(corner2, -1).intersection(_box(corner2[0] - far, -far, corner2[0] + S * 2, th + 2))
    return g.difference(cut_tr).difference(cut_bl)
Z_BAR = 0.52    # the z's bars, x the stem (owner 2026-09-14: "slightly reduce the line thickness ... of the horizontal strokes in 'z'"; 0.62 before). The bars stay ON the x-height and the baseline (align top / bottom), so the vertical grid holds
Z_DIAG = 1.05   # the z's diagonal, x the stem (the heavy stroke, as Albertus and Berkeley)
Z_BAR_ADJ, Z_DIAG_ADJ = 0.58, 0.90   # round 92 (adj 'z'): the darkest thing on any line it was in -- diagonal down, bars up, one color

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
    ARM_WEIGHT = 1.40 if adj('k') else 1.30   # round 92 (adj 'k'): light beside the stem, band -14% Albertus
    K_ARM_WEDGE = 1.15
    LEG_EDGE = 1.0            # spring the leg from the arm's lower edge (1.0), not its centerline (0.0)
    LEG_BURY = 0.20           # x stem, past that edge (join rule: a fifth to a third of a stem)
    LEG_TAPER = (0.55, 0.35)  # thin from t=0.55 (was 0.78) to 0.35 x lw (was 0.55) at the buried tip
    xh = c["xh"]; wf = c["wf"]; x = S / 2
    st = stem(x, 0, c["asc"], top='left', foot='both')
    A0, B0 = (x + 360 * wf, xh * 0.97), (x + S * 0.2, xh * 0.42)
    arm_w = pw(A0, B0, 0.78 * ARM_WEIGHT)   # round 51's 0.78 x the pen at the arm's angle, x the ladder weight
    # owner 2026-09-13: "the top right serif needs to be slightly larger so
    # visually balances and reads well" -- the arm's end wedge at K_ARM_WEDGE
    # of the family's diagonal end (0.9 is the family's own)
    arm = geom.union([diagonal(A0, B0, arm_w), end_wedge([B0, A0], arm_w, False, 1, scale=K_ARM_WEDGE)])
    u = (150 * wf - (B0[0] - x)) / (A0[0] - B0[0]); J = (B0[0] + (A0[0] - B0[0]) * u, B0[1] + (A0[1] - B0[1]) * u)
    # the arm's own direction and its outward normal, to find the arm's
    # lower edge at J instead of J's centerline point
    ad = (A0[0] - B0[0], A0[1] - B0[1]); aL = math.hypot(*ad); ad = (ad[0] / aL, ad[1] / aL)
    an = (-ad[1], ad[0])
    if an[0] < 0: an = (-an[0], -an[1])
    J_edge = (J[0] + an[0] * arm_w / 2 * LEG_EDGE, J[1] + an[1] * arm_w / 2 * LEG_EDGE)
    foot = (J[0] + J[1] / math.tan(math.radians(56)), 0)
    d = (J[0] - foot[0], J[1] - foot[1]); L = math.hypot(*d); d = (d[0] / L, d[1] / L)
    lw = pw(foot, J) * (1.10 if adj('k') else 1.0)   # round 51: the pen at the leg's angle (58 at 56 degrees); round 92 leg x1.10
    tip = (J_edge[0] + d[0] * S * LEG_BURY, J_edge[1] + d[1] * S * LEG_BURY)
    leg = diagonal(foot, tip, widths([(0.0, lw), (LEG_TAPER[0], lw), (1.0, lw * LEG_TAPER[1])]), serif0=1)
    return geom.ink([st, arm, leg])
