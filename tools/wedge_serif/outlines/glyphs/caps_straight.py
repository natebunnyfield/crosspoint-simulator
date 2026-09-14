"""A-Z on the same hand: cap stems at 1.137 x the lowercase (the wedge
family at ONE size, round 22), the D's ring for D B P R (rulings), beaks
on C G S, the kicks at their ruled angles (A 65, R 60, K 37), the two-sided
tops on the I and the U's right stem, no bar on the J. Widths are solved
by the builder against the garalde references' medians (c['W'])."""
import math
from . import glyph
from .. import geom, pen
from ..geom import cubic, line, join, superellipse, catmull, tangents
from ..primitives import (stem, stem_edge_x, ring, ring_from, half_bowl, stroke, pen_widths, widths, dot, wedge,
                          diag_wedge, end_wedge, diagonal, bar, beak, trap)
from ..pen import S, CS, XH, OVER, TH_V, TH_H, HAIR, CUT, WL, WD, DROP, ENT, BOWL_K, CAP_STEM, CAP_BAR
from .. import primitives as PR
from ..primitives import bowl_widths, widen_terminal

def W_(c, ch, default): return default * c["W"].get(ch, 1.0)
CW = TH_V * CAP_STEM          # the drawn cap stem, 87.9
THIN = CW * 0.72              # the capitals' thin STEM (N's stems: round 51's _cstem thin=0.72)
def pw(p0, p1, mult=1.0):
    """Round 51's `latin.diag`: a capital's diagonal is `mult` x the PEN's
    width at its own angle (the cap factor cancelled out of it); the thin
    strokes 0.72 x that."""
    tn = tangents(line(p0, p1))[0]; return pen.th_t(tn) * mult
BEAK_CUT = -28.0

def cstem(x, y0, y1, top='left', foot='both', **kw):
    return stem(x, y0, y1, cap=True, top=top, foot=foot, **kw)

def flat_face(p0, p1, at_end=True):
    """The shear (`stroke`'s cut0/cut1) that makes a diagonal's end face
    HORIZONTAL instead of perpendicular to its own axis.

    Two strokes that meet at ONE point -- the M's and the W's apexes, the
    M's middle vertex -- each cut their end square to their own axis, and
    the two faces tilt opposite ways: their union is a pair of prongs with
    a notch between, not a vertex. Cut both to the same horizontal line and
    the union is one flat face on the cap line (or the baseline).
    Derivation: `stroke` shifts the L edge by tn x d and the R edge by
    -tn x d with d = -tan(cut) w/2 at the end and +tan(cut) w/2 at the
    start; setting L's y equal to the centre's gives tan(cut) = tnx/tny at
    the end and -tnx/tny at the start."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    return math.atan2(dx if at_end else -dx, dy)

def _stroke_edge(p0, p1, w, toward):
    """The straight edge of a straight stroke, on the side facing `toward`."""
    tn = tangents(line(p0, p1))[0]; n = (-tn[1], tn[0])
    s = 1.0 if ((toward[0] - p1[0]) * n[0] + (toward[1] - p1[1]) * n[1]) > 0 else -1.0
    ox, oy = n[0] * s * w / 2, n[1] * s * w / 2
    return (p0[0] + ox, p0[1] + oy), (p1[0] + ox, p1[1] + oy)

def _cross(a0, a1, b0, b1):
    (x1, y1), (x2, y2), (x3, y3), (x4, y4) = a0, a1, b0, b1
    den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den
    return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))

def _at_y(a0, a1, y):
    t = (y - a0[1]) / (a1[1] - a0[1]); return (a0[0] + t * (a1[0] - a0[0]), y)

def crotch_blunt(pa0, pa1, wa, pb0, pb1, wb, lift, drop):
    """The cutout that blunts the crotch where two STRAIGHT strokes leave a
    common point (the W's middle apex). Their facing edges close at only
    ~18 degrees a side, so the wedge between them runs on as a hair and the
    union's last dozen units of it come out as a zigzag. Returns a triangle:
    apex `lift` above the two edges' crossing, base ON those edges `drop`
    below it -- so the cut meets each edge at a ~9-degree kink, takes at
    most a couple of units out of either stroke, and leaves a mouth of
    drop x (tan18 + tan19) that the ink spread cannot seal."""
    ea = _stroke_edge(pa0, pa1, wa, pb1); eb = _stroke_edge(pb0, pb1, wb, pa1)
    X = _cross(ea[0], ea[1], eb[0], eb[1])
    return geom.poly([(X[0], X[1] + lift), _at_y(ea[0], ea[1], X[1] - drop), _at_y(eb[0], eb[1], X[1] - drop)])

def flat_corner(p0, p1, w, side, at_end=True):
    """The corner of that horizontal face: the stroke's real edge where the
    face lies (side -1 the left corner, +1 the right). Falls straight out
    of the same algebra -- the face's half width is w / 2 sin(inclination).
    A wedge crowning such an apex is seated HERE and nowhere else; seated a
    fraction of the stroke's width in from it, as the M's and the W's
    crowns were, it leaves a step where its bracket misses the edge."""
    tn = tangents(line(p0, p1))[0]
    P = p1 if at_end else p0
    return (P[0] + side * w / (2 * abs(tn[1])), P[1])

@glyph('A')
def g_A(c):
    """Thin left leg with a FLAT foot (round 36: the wedge's tip on the
    baseline, the face pen-cut level), thick right leg with the outer
    wedge, the thin stroke ending inside the thick one under the apex, the
    bar low at 0.28 C."""
    C = c["cap"]; w = W_(c, 'A', 600); s = CS
    p0, p1 = (s * 0.3, 0), (w / 2 - s * 0.06, C - s * 0.32)
    tn = geom.tangents(line(p0, p1))[0]
    lw = pw(p0, p1, 0.72)   # round 51: 0.72 x the pen at the leg's angle (47)
    left = stroke(line(p0, p1), lw, cut0=-math.atan2(tn[0], tn[1]))
    # the flat foot: a bracket up the leg's left edge, tip ON the baseline
    nrm = (-tn[1], tn[0]); Apt = (p0[0] - lw / 2 / tn[1], 0.0)
    edge_at = lambda d: (Apt[0] + tn[0] * d, tn[1] * d)
    foot = wedge(Apt, (0, -1), (-1, 0), WL * 0.9, WD * 0.9, 0.0, edge_at=edge_at)
    r0, r1 = (w - s * 0.3, 0), (w / 2 - s * 0.18, C)
    right = diagonal(r0, r1, pw(r0, r1), serif0=1)
    b = stroke(line((w * 0.19, C * 0.28), (w * 0.81, C * 0.28)), CAP_BAR * 0.9)   # round 94: the capitals' bar unit
    return geom.ink([left, foot, right, b])

@glyph('B')
def g_B(c):
    C = c["cap"]; x = CS / 2; w = W_(c, 'B', 380); edge = x + CW / 2
    st = cstem(x, 0, C, top='left', foot='left')
    # upper bowl 0.86 of the lower's width (ruling); both bowls' thin ends
    # taper into the stem at the waist (0.55 C), so the waist is the pen's
    # horizontal thinning to a hairline at the stem
    # owner (round 58): "the cross bar in B needs to be like R or P, not
    # doubled" -- the two bowls SHARE one bar at the waist: the upper bowl's
    # bottom stroke and the lower bowl's top stroke have the same centerline
    # (waist 0.55 C), so the waist is one horizontal at the bowl's thin, the
    # stroke the P's bowl makes where it returns to the stem
    waist = C * 0.55; h = PR.bowl_hair()
    up, *_ = half_bowl(edge, C, waist - h / 2, w * 0.86 * 0.72 + TH_V / 2, open_bottom=0.0)
    lo, *_ = half_bowl(edge, waist + h / 2, 0, w * 0.72 + TH_V / 2, open_bottom=0.06)
    return geom.ink([st, up, lo])

def cap_arc(c, rx_c, a0, a1, profile, cut0=None, cut1=None, k=BOWL_K, ry_c=None, cy=None):
    C = c["cap"]; ry = (C / 2 + OVER - TH_H / 2) if ry_c is None else ry_c; cy = C / 2 if cy is None else cy
    center = superellipse(rx_c + TH_V / 2, cy, rx_c, ry, math.radians(a0), math.radians(a1), k)
    return stroke(center, bowl_widths(center, profile), cut0=cut0, cut1=cut1), center

@glyph('C')
def g_C(c):
    rx = W_(c, 'C', 330)
    if PR.BOWL and PR.BOWL.get('widen'):   # variant C: both ends widen into the family's cut, no beak, no taper to a point
        body, center = cap_arc(c, rx, 43, 334, widen_terminal(widen_terminal(None, True), False), cut0=CUT, cut1=CUT); return body
    prof = widths([(0.0, 1.3), (0.12, 1.0), (0.78, 1.0), (1.0, 0.3)])
    body, center = cap_arc(c, rx, 43, 334, prof, cut0=math.radians(BEAK_CUT))
    lip = beak(center, PR.bowl_th(tangents(center)[0]) * 1.3, True, BEAK_CUT)
    return geom.ink([body, lip])

@glyph('D')
def g_D(c):
    C = c["cap"]; x = CS / 2; rx = W_(c, 'D', 330); edge = x + CW / 2
    st = cstem(x, 0, C, top='left', foot='left')
    bowl, *_ = half_bowl(edge, C, 0, rx + TH_V / 2, open_bottom=0.06)
    return geom.ink([st, bowl])

# owner, verbatim: "the top right serif of E and F need cleanup." The top
# arm carried BOTH the family's bar-end wedge (0.85 x 0.9, hanging) and the
# 20-degree pen cut, and the two do not meet. `bar` seats the wedge at the
# UNSHEARED corner (x1, yc - th/2) with drop 0, so its outer face is the
# vertical x = x1; `cut1` then shears the bar's own end face so its
# UNDERSIDE runs tan(20) x th/2 = 7.6 units PAST that -- measured on the E's
# designed outline, the end went ... (444.2, 675.6) -> (460.3, 631.2) ->
# (452.2, 631.2) -> (452.2, 573.1): a double facet with an 8-unit
# horizontal ledge between two right edges, the wedge hanging from the
# inner one. The wedge's face IS the terminal -- the T's arms carry the
# same wedge and have never taken a cut -- so the cut goes from the wedged
# end and the arm ends in one clean vertical face from the cap line down to
# the wedge's apex. The middle bar keeps its pen cut (it carries no wedge),
# and E and F now draw the same end.
# NOT changed, and not asked for: E's BOTTOM-right and L's bottom bar carry
# the identical pair and have the same ledge, mirrored; the Z's bars, whose
# cut ends are at the corners the owner did not name.
@glyph('E')
def g_E(c):
    C = c["cap"]; x = CS / 2; w = W_(c, 'E', 420)
    st = cstem(x, 0, C, top='left', foot='left')
    th = CAP_BAR   # round 94
    return geom.ink([st, bar(x, x + w * 0.96, C, th, align='top', wedges=[('right', -1)]),
                     bar(x, x + w * 0.74, C * 0.54, th * 0.9, cut1=CUT),
                     bar(x, x + w, 0, th, align='bottom', cut1=CUT, wedges=[('right', 1)])])

@glyph('F')
def g_F(c):
    C = c["cap"]; x = CS / 2; w = W_(c, 'F', 400)
    st = cstem(x, 0, C, top='left', foot='both')
    th = CAP_BAR   # round 94
    return geom.ink([st, bar(x, x + w, C, th, align='top', wedges=[('right', -1)]),
                     bar(x, x + w * 0.72, C * 0.54, th * 0.9, cut1=CUT)])

@glyph('G')
def g_G(c):
    """The C's arc to 312 degrees bending into a vertical spur whose right
    edge is the bowl's outermost (one outline), the weight ramping to the
    cap stem over the bend; a short bar at 0.42 C, half a stem thick."""
    C = c["cap"]; rx = W_(c, 'G', 340); ry = C / 2 + OVER - TH_H / 2; s = CS
    # the bar is the record's (round 42): half the pen's horizontal, never
    # under half a stem (41 at stem 82) -- the port had halved AFTER the floor
    # and drawn it 24, and the spur's run ended 0.05 of a pen BELOW its
    # underside, so the two touched only through the 1.2-unit ink spread:
    # joined at 84/0.80, a hair apart at 94/0.60, apart at every heavier or
    # lower-contrast weight (round 62). The run now ends 8 units inside it.
    bar_th = CAP_BAR * 0.8; yb = C * 0.42   # round 94
    cx = rx + TH_V / 2
    arc = superellipse(cx, C / 2, rx, ry, math.radians(43), math.radians(312), BOWL_K)
    xg = cx + rx + TH_V / 2 - CW / 2                   # the spur's centerline: its right edge = the bowl's
    p0 = arc[-1]; d = (arc[-1][0] - arc[-3][0], arc[-1][1] - arc[-3][1]); L = math.hypot(*d); d = (d[0] / L, d[1] / L)
    ctrl = (xg, p0[1] + d[1] * (xg - p0[0]) / d[0]); p1 = (xg, ctrl[1] + (ctrl[1] - p0[1]) * 0.7)
    bend = cubic(p0, (p0[0] + (ctrl[0] - p0[0]) * 2 / 3, p0[1] + (ctrl[1] - p0[1]) * 2 / 3), (p1[0] + (ctrl[0] - p1[0]) * 2 / 3, p1[1] + (ctrl[1] - p1[1]) * 2 / 3), p1)[1:]
    run = line(p1, (xg, yb - bar_th * 0.5 + 8))[1:]
    pts = arc + bend + run; N = len(pts) - 1; t0 = (len(arc) - 1) / N; t1 = (len(arc) + len(bend) - 1) / N
    base = bowl_widths(pts)
    def wfn(t):
        w = base(t) * widths([(0.0, 1.3), (0.12, 1.0)])(t)
        if t >= t1: return CW
        if t > t0: u = (t - t0) / (t1 - t0); return w + (CW - w) * (3 * u * u - 2 * u ** 3)
        return w
    body = stroke(pts, wfn, cut0=math.radians(BEAK_CUT))
    lip = beak(pts, wfn(0.0), True, BEAK_CUT)
    b = bar(xg - s * 1.1, xg + s * 0.6, yb, bar_th, cut0=CUT, cut1=CUT)
    return geom.ink([body, lip, b])

@glyph('H')
def g_H(c):
    C = c["cap"]; x0 = CS / 2; x1 = x0 + W_(c, 'H', 520)
    return geom.ink([cstem(x0, 0, C), cstem(x1, 0, C, top='right'), bar(x0, x1, C * 0.52, CAP_BAR * 0.95)])   # round 94

@glyph('I')
def g_I(c):
    return geom.ink([cstem(CS / 2, 0, c["cap"], top='left+')])

@glyph('J')
def g_J(c):
    """No bar (round 36); the I's top wedge; the hook starts at the stem's
    weight and eases to the pen's by its turn, flaring into the pen cut."""
    C = c["cap"]; r = W_(c, 'J', 190); x = r * 1.05 + CS / 2; desc = c["desc"]
    st = cstem(x, r * 0.25 - 20, C, top='left', foot=None, ent_span=(r * 0.25 - 60, C))
    tail = cubic((x, r * 0.25), (x, -desc * 0.42), (x - r * 0.55, -desc * 0.55), (x - r * 1.1, -desc * 0.1))
    base = pen_widths(tail)
    wfn = lambda t: (CW if t < 0.1 else (base(t) if t > 0.45 else CW + (base(t) - CW) * (3 * ((t - 0.1) / 0.35) ** 2 - 2 * ((t - 0.1) / 0.35) ** 3))) * widths([(0.65, 1.0), (1.0, 1.3)])(t)
    return geom.ink([st, stroke(tail, wfn, cut1=CUT)])

# owner, verbatim: "the kick on K and R needs to taper (give me options to
# choose from)." Both kicks are drawn FOOT-FIRST, so the pair reads
# (fraction at the FOOT, fraction at the JUNCTION) of the leg's ruled
# width. Everything ruled is untouched: the angles (K 37, R 60), the base
# width the fractions are taken OF (K 1.1 x the pen at the leg's angle,
# R 1.05 x it -- round 51 / round 42), the K arm's 0.47-stem floor, the
# end wedge at the foot (which follows the tapered width, so it stays
# seated) and where each leg springs. Only the profile between the two
# ends moves.
#   A  (0.70, 1.00)  taper toward the foot: full width at the junction,
#                    0.7 of it at the end before the end wedge  -- DEFAULT
#   B  (1.00, 0.70)  taper toward the junction: the classic "leg thin
#                    where it springs"
#   C  (0.85, 0.85)  a spindle: 0.85 at both ends, full in the middle
K_KICK_TAPER = (1.00, 1.00)   # owner 2026-09-13, on round 81: "leave K R Q M W as is, before agent was better" -- unused now; the round-51 K is the K   # owner 2026-09-13: "K before is best for inktraps, but adopt some of C kick thickness" -- C was the 0.85/0.85 spindle; a little of it
R_KICK_TAPER = (1.00, 1.00)   # unused now (owner: "leave K R Q M W as is, before agent was better")

def kick_widths(w, pair, t_join, buried):
    """The leg's width keypoints: `pair` x the ruled width w over the
    VISIBLE run (foot .. junction at t_join), the middle held full when
    both ends are thinned (option C's spindle), then the family's bury
    taper to `buried` x the junction's width at the end inside the arm or
    the bowl. t_join is the junction's own t, so the whole of the taper the
    owner asked for is the part that can be seen and the bury stays buried."""
    f0, f1 = pair
    keys = [(0.0, w * f0)]
    if f0 < 1.0 and f1 < 1.0: keys.append((t_join / 2, w))
    keys += [(t_join, w * f1), (1.0, w * f1 * buried)]
    return widths(keys)

def kick(J, angle_deg, w, bury=0.2, serif=1, taper=0.45, pair=(1.0, 1.0)):
    """A K/R leg drawn as the A's right leg: foot-first from the baseline
    at `angle`, the wedge foot on the outer side, thinning into J."""
    a = math.radians(angle_deg); foot = (J[0] + J[1] / math.tan(a), 0)
    d = (J[0] - foot[0], J[1] - foot[1]); L = math.hypot(*d); d = (d[0] / L, d[1] / L)
    top = (J[0] + d[0] * CS * bury, J[1] + d[1] * CS * bury)
    return diagonal(foot, top, kick_widths(w, pair, L / (L + CS * bury), 1 - taper), serif0=serif)

@glyph('K')
def g_K(c):
    """Arm with a 0.47-stem floor from the cap line (a third of a stem
    under it) to the stem's centre at 0.45 C; the leg springs from the arm
    0.16 of the way out, its angle solved so the foot lands half a stem past
    the arm's tip (round 36 / 42: ~37 degrees)."""
    C = c["cap"]; x = CS / 2; w = W_(c, 'K', 500); s = CS
    st = cstem(x, 0, C)
    A0, B0 = (x + w, C - s * 0.36), (x, C * 0.45)
    arm_w = max(pw(B0, A0, 0.72), 0.47 * S)   # round 51: the pen's hairline at the arm's angle, floored at 0.47 stem (38.5)
    arm = diagonal(A0, B0, arm_w, serif0=1)
    u = 0.16; J = (B0[0] + (A0[0] - B0[0]) * u, B0[1] + (A0[1] - B0[1]) * u)
    angle = math.degrees(math.atan2(J[1], A0[0] + s * 0.5 - J[0]))
    foot = (J[0] + J[1] / math.tan(math.radians(angle)), 0)
    return geom.ink([st, arm, kick(J, angle, pw(foot, J, 1.1), bury=0.1)])   # round 51: 1.1 x the pen at the leg's angle

# owner, verbatim: "add more top right serif to 'L'" -- the stem top's wedge
# (today `top='left'` only) extended to the right as the H/N/U right-stem tops
# do, so the top reads as a proper two-sided serif rather than a bare stem
# with the wedge on one side. In units of a full stem-top wedge's length (WL);
# depth stays the family's WD, drop the family's DROP. The arm (there is
# none), foot and bar-end wedge are untouched.

L_TOP_RIGHT = float(__import__("os").environ.get("FJORD_L_TOP", 0.45))   # owner: "yes to with life, but halfway between the two" (I: 0.4, life: 0.5)
L_TOP_RIGHT_DEPTH = 0.66   # the I's small wedge is 0.4 x 0.6 x 0.4 drop; the L's 0.5 x 0.72 x 0.5 (owner: "give it life")
L_TOP_RIGHT_DROP = 0.45
L_TOP_LEFT = 0.96          # the left wedge a touch shorter than the family's 1.0   # FJORD_L_TOP: ladder override

@glyph('L')
def g_L(c):
    C = c["cap"]; x = CS / 2; w = W_(c, 'L', 420)
    # Owner 2026-09-13, on the L_TOP_RIGHT ladder 0.1-1.4: "none of the
    # options are an improvement. try one similar to other letters like 'I'".
    # So the L's top is the I's: the stem primitive's own two-sided top
    # ('left+'), the small right-pointing wedge at the primitive's factor.
    # L_TOP_RIGHT > 0 keeps the ladder's separate wedge for the record.
    # Then, on that: "yes to that I, but make it not an exact match. adjust
    # it slightly give it life." The I's small wedge is 0.4 x 0.6 of the
    # family at 0.4 drop; the L's is a touch bigger (L_TOP_RIGHT x
    # L_TOP_RIGHT_DEPTH at L_TOP_RIGHT_DROP) and its left wedge a touch
    # shorter (L_TOP_LEFT), so the two crowns are kin, not twins.
    if L_TOP_RIGHT > 0:
        st = cstem(x, 0, C, top='left', foot='left', top_len=L_TOP_LEFT)
        cap_w = TH_V * CAP_STEM
        def _wid(y): return cap_w * (1.0 + ENT * (2 * y / C - 1) ** 4)
        top_right = wedge((x + _wid(C) / 2, C), (0, 1), (1, 0), WL * L_TOP_RIGHT, WD * L_TOP_RIGHT_DEPTH, DROP * L_TOP_RIGHT_DROP,
                           edge_at=lambda d: (x + _wid(C - d) / 2, C - d))
        parts = [st, top_right]
    else:
        parts = [cstem(x, 0, C, top='left+', foot='left')]
    return geom.ink(parts + [bar(x, x + w, 0, CAP_BAR, align='bottom', cut1=CUT, wedges=[('right', 1)])])   # round 94

# owner, verbatim: "slightly cleanup the top and middle serifs of 'M'."
# Three faults, all one cause -- two strokes meeting at one point, each cut
# square to its OWN axis, so the faces tilt opposite ways:
#  * the left apex went (62.3, 672.2) -> (62.5, 676.4) -> (90.5, 675.6) ->
#    (129.3, 693.8): a 4-unit sliver, a short flat, then a spike 19 units
#    ABOVE the cap line -- and the M was the only flat-topped capital that
#    overshot at all (H N I B D P E F L T all stop at the line);
#  * the right apex the same, a 10-unit spike at (706.1, 684.5);
#  * the middle vertex two prongs (-19.5 and -10.1) with a notch between
#    them, plus a 10-unit ledge poking right of the thick stroke where the
#    thin one's end face came out at (447.4, 17.3).
# Every one is cured by cutting the meeting faces HORIZONTAL (`flat_face`)
# so each apex is one face on the cap line and the vertex one face on the
# baseline. The crown was also seated 0.35 of the thin stroke's width in
# from the apex instead of ON its edge, which is where the 4-unit sliver
# came from; it is seated by `flat_corner` now. Widths, angles, the wedge
# family's sizes, the splay and the advance are untouched.
@glyph('M')
def g_M(c):
    """Splayed: the outer strokes lean out a little, the apex on the
    baseline, a wedge crowning the left apex."""
    C = c["cap"]; s = CS; w = W_(c, 'M', 720); x0 = s / 2; x1 = x0 + w
    P = [((x0 + s * 0.25, 0), (x0 + s * 0.45, C), 0.72, -1, None), ((x0 + s * 0.45, C), (x0 + w / 2, 0), 1.0, None, None),
         ((x1 - s * 0.45, C), (x0 + w / 2, 0), 0.72, None, None), ((x1 - s * 0.25, 0), (x1 - s * 0.45, C), 1.0, 1, -1)]
    a, b, d, e = [diagonal(p0, p1, pw(p0, p1, m), serif0=s0, serif1=s1) for p0, p1, m, s0, s1 in P]
    apex = wedge((x0 + s * 0.45 - pw(P[0][0], P[0][1], 0.72) * 0.35, C), (0, 1), (-1, 0), WL * 0.9, WD, DROP)
    return geom.ink([a, b, d, e, apex])

@glyph('N')
def g_N(c):
    C = c["cap"]; s = CS; w = W_(c, 'N', 560); x0 = s / 2; x1 = x0 + w
    d0, d1 = (x0 + s * 0.1, C - s * 0.3), (x1 - s * 0.1, s * 0.3)
    return geom.ink([cstem(x0, 0, C, top='left', foot='both', w=THIN), diagonal(d0, d1, pw(d0, d1)),
                     cstem(x1, 0, C, top='right', foot=None, w=THIN)])

def cap_ring(c, rx_c):
    C = c["cap"]; rx = rx_c + TH_V / 2; ry = C / 2 + OVER
    return ring(rx, C / 2, rx, ry)

@glyph('O')
def g_O(c):
    solid, o, i = cap_ring(c, W_(c, 'O', 350)); return solid

@glyph('P')
def g_P(c):
    C = c["cap"]; x = CS / 2; w = W_(c, 'P', 400); edge = x + CW / 2
    bowl, *_ = half_bowl(edge, C, C * 0.44, w * 0.72 + TH_V / 2, open_bottom=0.06)
    return geom.ink([cstem(x, 0, C), bowl])

# owner, verbatim: "the tail on Q needs to lose its bulge." The bulge was
# DECLARED, not an accident of the union: round 42's profile forced
# `max(pen, 1.05 stems)` over a smoothstep belly centred at t 0.45, so the
# tail ran 100 units wide -- wider than the cap stem (95.5) and wider than
# the ring's own heaviest stroke (84) -- exactly where it crosses out from
# under the ring, and the 1.05 stems is an ABSOLUTE that does not scale
# with the letter, so the solved Q (width x 0.70) got the bulge at full
# size on a smaller ring. The tail is now the pen at its own angle, with
# the family's tail floor, so it leaves the ring at the ring's weight and
# thins along its sweep; the ring is untouched and unbroken.
Q_TAIL_FLOOR = 0.55   # x the stem: the family's tail floor, the 6's and the 9's (rounds 70, 71)

@glyph('Q')
def g_Q(c):
    """The O with Van den Keere's swash tail (round 42): from the ring's
    centerline at 250 degrees, heaviest at its belly (1.05 stems), thinning
    to a pen-cut tip at 1.8 O-widths, 0.2 C down."""
    C = c["cap"]; rx_c = W_(c, 'O', 350); solid, o, i = cap_ring(c, rx_c); s = CS
    rx = rx_c + TH_V / 2; ry_c = C / 2 + OVER - TH_H / 2; W = 2 * rx
    p0 = superellipse(rx, C / 2, rx_c, ry_c, math.radians(250), math.radians(250.5), BOWL_K)[0]
    tail = cubic(p0, (W * 0.85, -C * 0.30), (W * 1.40, -C * 0.56), (W * 1.80, -C * 0.20))
    base = pen_widths(tail)
    def wfn(t):
        belly = max(0.0, 1 - abs(t - 0.45) / 0.4)
        return max(base(t), s * 1.05 * (3 * belly * belly - 2 * belly ** 3)) * widths([(0.0, 0.6), (0.12, 1.0), (0.8, 1.0), (1.0, 0.7)])(t)
    return geom.ink([solid, stroke(tail, wfn, cut1=CUT)])

Q_BELLY = 0.15

@glyph('R')
def g_R(c):
    C = c["cap"]; x = CS / 2; w = W_(c, 'R', 400); edge = x + CW / 2
    bowl, cx, cy, rx, ry, L, R = half_bowl(edge, C, C * 0.46, w * 0.95 * 0.72 + TH_V / 2, open_bottom=0.06)
    ang = math.radians(-52); J = (cx + rx * math.cos(ang), cy + ry * math.sin(ang))
    # the leg as the nib writes it: thin where it leaves the bowl, the
    # pen's width at 60 degrees x 1.05 (64, round 42) by the foot, on a
    # slight outward bow; drawn foot-first so the foot wedge is the A's
    foot = (J[0] + J[1] / math.tan(math.radians(60)), 0)
    d = (J[0] - foot[0], J[1] - foot[1]); Ld = math.hypot(*d); d = (d[0] / Ld, d[1] / Ld); nrm = (-d[1], d[0])
    end = (J[0] + d[0] * CS * 0.15, J[1] + d[1] * CS * 0.15)
    c1 = (foot[0] + d[0] * Ld * 0.35 - nrm[0] * 9, foot[1] + d[1] * Ld * 0.35 - nrm[1] * 9)
    c2 = (foot[0] + d[0] * Ld * 0.70 - nrm[0] * 9, foot[1] + d[1] * Ld * 0.70 - nrm[1] * 9)
    leg_c = cubic(foot, c1, c2, end)
    w_foot = pw(foot, J, 1.05)
    leg = stroke(leg_c, lambda t: w_foot * widths([(0.0, 1.0), (0.45, 1.0), (1.0, 0.42)])(t))
    return geom.ink([cstem(x, 0, C), bowl, leg, end_wedge(leg_c, w_foot, True, 1)])

R_LEG_BURY = 0.28
S_BOTTOM_END = 1.30

@glyph('S')
def g_S(c):
    C = c["cap"]; w = W_(c, 'S', 440); o = OVER - TH_H / 2; st = CS
    spine = catmull([(w * 0.93, C * 0.80), (w * 0.62, C + o * 0.9), (w * 0.18, C * 0.86), (w * 0.2, C * 0.6),
                     (w * 0.8, C * 0.42), (w * 0.84, C * 0.16), (w * 0.42, -o * 0.9), (w * 0.04, C * 0.22)], tension=0.55)
    base = pen_widths(spine)
    def wfn(t):
        mid = 1.0 - min(1.0, abs(t - 0.5) / 0.28); want = base(t) * (1 - mid) + st * 0.92 * mid
        bot = max(0.0, 1 - abs(t - 0.74) / 0.22); want *= 1 + 0.2 * (3 * bot * bot - 2 * bot ** 3)
        return want * widths([(0.0, 1.3), (0.10, 1.0), (0.86, 1.0), (1.0, S_BOTTOM_END)])(t)
    if PR.BOWL and PR.BOWL.get('widen'):
        wid = widen_terminal(widen_terminal(None, True), False)
        base2 = pen_widths(spine)
        def wfn2(t):
            mid = 1.0 - min(1.0, abs(t - 0.5) / 0.28); want = base2(t) * (1 - mid) + st * 0.92 * mid
            bot = max(0.0, 1 - abs(t - 0.74) / 0.22); want *= 1 + 0.2 * (3 * bot * bot - 2 * bot ** 3)
            return want * wid(t)
        return geom.ink([stroke(spine, wfn2, cut0=CUT, cut1=CUT)])
    body = stroke(spine, wfn, cut0=math.radians(BEAK_CUT))
    return geom.ink([body, beak(spine, wfn(0.0), True, BEAK_CUT)])

@glyph('T')
def g_T(c):
    C = c["cap"]; w = W_(c, 'T', 520); x = w / 2
    th = CAP_BAR * 0.85; yb = C - th / 2   # round 94: was 0.62 of the pen's horizontal, a light line at 13 pt
    b = bar(0, w, C, th, align='top', wedges=[('left', -1), ('right', -1)])
    return geom.ink([b, cstem(x, 0, yb + th * 0.5 - 4, top=None, foot='both', ent_span=(0, C))])

@glyph('U')
def g_U(c):
    """Left stem at cap weight, the bowl reaching the overshoot and thinning
    to the thin right stem (0.78), whose top wedge is two-sided (ruling)."""
    C = c["cap"]; s = CS; w = W_(c, 'U', 520); x0 = s / 2; x1 = x0 + w; y0 = C * 0.42
    left = cstem(x0, y0 - 30, C, top='left', foot=None, ent_span=(0, C))
    right = cstem(x1, y0 - 30, C, top='right+', foot=None, w=CW * 0.78, ent_span=(0, C))
    yb = -OVER + TH_H / 2; cy = (8 * yb - 2 * y0) / 6
    pts = cubic((x0, y0), (x0, cy), (x1, cy), (x1, y0))
    # round 51: the pen's widths x CAP_STEM(1 - 0.22 t), swelling by the
    # entasis over the first and last 15% to meet the stems' ends
    amt = ENT; base = pen_widths(pts)
    bump = lambda t: 1.0 + amt * (max(0.0, 1 - t / 0.15) + max(0.0, 1 - (1 - t) / 0.15))
    wfn = lambda t: base(t) * CAP_STEM * (1 - 0.22 * t) * bump(t) * widths([(0.0, 0.9), (0.05, 1.0), (0.88, 1.0), (1.0, 0.8)])(t)
    return geom.ink([left, right, stroke(pts, wfn)])

@glyph('V')
def g_V(c):
    C = c["cap"]; s = CS; w = W_(c, 'V', 560)
    p0, p1 = (s * 0.3, C), (w / 2, 0); q0, q1 = (w - s * 0.3, C), (w / 2 + s * 0.15, 0)
    return geom.ink([diagonal(p0, p1, pw(p0, p1), serif0=1), diagonal(q0, q1, pw(q0, q1, 0.72), serif0=-1)])

# owner, verbatim: "clean up the top middle of W (stray marks below and
# some overlap above)." Both halves of that sentence are one construction:
# the two inner strokes START at the same point and each was cut square to
# its own axis.
#  * ABOVE -- the two faces tilt opposite ways and cross past the apex
#    wedge: the designed outline peaked at (386.5, 682.0) and (450.6,
#    687.5) with a notch down to (410.0, 675.6) between them. `flat_face`
#    cuts both on the cap line, so the apex is one face; and the crown,
#    seated 0.35 of the thin stroke's width in from the apex, is seated on
#    the real edge by `flat_corner`, which is what left a step beside it.
#  * BELOW -- the strokes' inner edges converge at only ~18 degrees each,
#    so the crotch closes over 136 units and its last dozen came out as a
#    zigzag hanging into the counter (399.4, 540.8) -> (400.8, 538.2) ->
#    (400.8, 545.9) -> (401.9, 550.0) -> (402.9, 546.5): the stray marks.
#    `crotch_blunt` lifts the crotch onto two straight edges.
#    Two shapes were built for that cut and looked at before this one, and
#    both fail at this half-angle. Subtracting the two strokes' OVERLAP
#    leaves a slot between them closing to a point at the old crotch, which
#    build.py's 1.2-unit ink spread seals into a 13 x 20 COUNTER (the W
#    came back with two contours). A `trap`, the arches' primitive, needs a
#    half-angle wider than the edges' own or it seals the same way -- and
#    wider means its rays leave the crotch's air and shear a ~12-unit ledge
#    off the inside of both strokes, which is a new stray mark for an old
#    one.
W_CROTCH_LIFT = 0.22   # x the stem: how far the crotch's point rises
W_CROTCH_DROP = 0.22   # x the stem: where the cut rejoins the two edges

@glyph('W')
def g_W(c):
    C = c["cap"]; s = CS; w = W_(c, 'W', 820)
    f1, f2, apex = (w * 0.26, 0), (w * 0.74, 0), (w * 0.5, C)
    P = [((s * 0.3, C), f1, 1.0, 1), (apex, (f1[0] + s * 0.15, 0), 0.72, None), (apex, f2, 1.0, None), ((w - s * 0.3, C), (f2[0] + s * 0.15, 0), 0.72, -1)]
    a, b, d, e = [diagonal(p0, p1, pw(p0, p1, m), serif0=sf) for p0, p1, m, sf in P]
    # owner 2026-09-13: "lower and reduce the protuberance of the top middle
    # connector in W" -- the crown at W_CROWN of the family's wedge, seated
    # W_CROWN_DROP x the family's drop lower
    crown = wedge((apex[0] - pw(P[1][0], P[1][1], 0.72) * 0.35, C - DROP * (W_CROWN_DROP - 1.0)), (0, 1), (-1, 0), WL * W_CROWN, WD * W_CROWN, DROP)
    return geom.ink([a, b, d, e, crown])

@glyph('X')
def g_X(c):
    C = c["cap"]; s = CS; w = W_(c, 'X', 540)
    p0, p1 = (s * 0.3, C), (w - s * 0.3, 0); q0, q1 = (w - s * 0.3, C), (s * 0.3, 0)
    return geom.ink([diagonal(p0, p1, pw(p0, p1), serif0=1, serif1=1), diagonal(q0, q1, pw(q0, q1, 0.72), serif0=-1, serif1=-1)])

@glyph('Y')
def g_Y(c):
    C = c["cap"]; s = CS; w = W_(c, 'Y', 540)
    p0, p1 = (s * 0.3, C), (w / 2 + 6, C * 0.45 - 10); q0, q1 = (w - s * 0.3, C), (w / 2 - 6, C * 0.45 - 10)
    return geom.ink([diagonal(p0, p1, pw(p0, p1), serif0=1), diagonal(q0, q1, pw(q0, q1, 0.72), serif0=-1),
                     cstem(w / 2, 0, C * 0.45 + s * 0.3, top=None, foot='both', ent_span=(0, C))])

# owner, verbatim: "cleanup 'Z' ... bottom left and top right." Those are
# the two corners where a bar meets the diagonal, and the diagonal was
# drawn straight past both of them. Its square end faces are 95.5 units
# long across a 51-degree axis, so each one reached well outside the bars'
# own box: at the top right the outline went (441.2, 675.6) -> a spur to
# (447.1, 683.6) 8 units above the cap line -> (501.2, 675.6) -> down the
# bar's end -> (525.6, 625.1), the diagonal's corner 24 units RIGHT of the
# bar; at the bottom left the mirror, a corner at (-25.6, 49.3) 24 units
# left of the bar's end and a spur to (52.9, -9.2) under the baseline.
# The bars ARE the Z's box, so the diagonal is kept to it: each corner is
# now one flush face, the bar's end above and the diagonal's edge below.
# The bars themselves -- their pen cuts and their two bar-end wedges, at
# the top LEFT and the bottom RIGHT -- are untouched, those being the two
# corners the owner did not name.
@glyph('Z')
def g_Z(c):
    """Owner 2026-09-13: "give Z a blunt edge and other similar more fitting
    connectors than a right angle." The corners where the diagonal meets
    the bars (top right, bottom left) were right angles. Z_CORNER picks:
    'blunt' -- the corner bevelled parallel to the diagonal by Z_BEVEL x S;
    'mitre' -- the bar's end cut along the diagonal's outer edge, a sharp
    corner on the diagonal's line; 'wedge' -- the diagonal's ends carry
    the family's 0.9 x 0.9 diagonal end wedge past the bars. The other two
    corners keep their pen cut and their bar-end wedge."""
    from shapely.geometry import Polygon
    C = c["cap"]; s = CS; w = W_(c, 'Z', 500); th = CAP_BAR   # round 94
    p_top, p_bot = (w - s * 0.15, C - th / 2), (s * 0.15, th / 2)
    dg = diagonal(p_top, p_bot, CS)
    parts = [bar(0, w, C, th, align='top', cut0=CUT, wedges=[('left', -1)]), dg, bar(0, w, 0, th, align='bottom', cut1=CUT, wedges=[('right', 1)])]
    g = geom.ink(parts)
    dx, dy = p_top[0] - p_bot[0], p_top[1] - p_bot[1]; L = math.hypot(dx, dy); dx, dy = dx / L, dy / L
    far = 4000.0
    if Z_CORNER == 'blunt':
        b = S * Z_BEVEL
        tr = Polygon([(w - b, C + 2), (w + 2, C + 2), (w + 2, C + 2 - (b + 2) * dy / dx)])
        bl = Polygon([(b, -2), (-2, -2), (-2, -2 + (b + 2) * dy / dx)])
        g = g.difference(tr).difference(bl)
    elif Z_CORNER == 'mitre':
        # the diagonal's outer edge, extended to the bar's outer face: the
        # bar runs out to that corner and everything beyond the edge's line
        # is cut away -- a sharp corner on the diagonal's own line
        nx, ny = dy, -dx                                     # the diagonal's right/lower normal
        def half(corner, sign):
            u = (dx * far, dy * far); n = (nx * far * sign, ny * far * sign)
            return Polygon([(corner[0] + u[0], corner[1] + u[1]), (corner[0] - u[0], corner[1] - u[1]),
                            (corner[0] - u[0] + n[0], corner[1] - u[1] + n[1]), (corner[0] + u[0] + n[0], corner[1] + u[1] + n[1])])
        ox, oy = p_top[0] + nx * CS / 2, p_top[1] + ny * CS / 2
        corner = (ox + dx * (C - oy) / dy, C)
        ox2, oy2 = p_bot[0] - nx * CS / 2, p_bot[1] - ny * CS / 2
        corner2 = (ox2 + dx * (0.0 - oy2) / dy, 0.0)
        # owner 2026-09-13: "Z mitre wins but extend the bottom right out to
        # optically match the top's right edge" -- the bottom bar runs out to
        # the top corner's x, so both right edges share one line
        parts = [bar(0, max(w, corner[0] + 2), C, th, align='top', cut0=CUT, wedges=[('left', -1)]), dg,
                 bar(min(0, corner2[0] - 2), corner[0], 0, th, align='bottom', cut1=CUT, wedges=[('right', 1)])]
        from shapely.geometry import box as _box
        cut_tr = half(corner, +1).intersection(_box(corner[0] - CS * 2, C - th - 2, corner[0] + far, C + far))   # beyond the edge, within the top bar's band
        cut_bl = half(corner2, -1).intersection(_box(corner2[0] - far, -far, corner2[0] + CS * 2, th + 2))    # beyond the edge, within the bottom bar's band
        g = geom.ink(parts).difference(cut_tr).difference(cut_bl)
    elif Z_CORNER == 'wedge':
        g = geom.ink(parts + [end_wedge([p_bot, p_top], CS, False, 1, scale=0.9), end_wedge([p_bot, p_top], CS, True, 1, scale=0.9)])
    return g
W_CROWN = 0.6
W_CROWN_DROP = 2.2
Z_CORNER = __import__("os").environ.get("FJORD_Z_CORNER", "mitre")   # owner 2026-09-13: "Z mitre wins"
Z_BEVEL = 0.45
