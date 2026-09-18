"""A-Z on the same hand: cap stems at 1.137 x the lowercase (the wedge
family at ONE size, round 22), the D's ring for D B P R (rulings), beaks
on C G S, the kicks at their ruled angles (A 65, R 60, K 37), the two-sided
tops on the I and the U's right stem, no bar on the J. Widths are solved
by the builder against the garalde references' medians (c['W'])."""
import math, os
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

J_DROP = float(os.environ.get("ALBO_J_DROP", 120.0))


@glyph('J')
def g_J(c):
    """No bar (round 36); the I's top wedge; the hook starts at the stem's
    weight and eases to the pen's by its turn, flaring into the pen cut."""
    C = c["cap"]; r = W_(c, 'J', 190); x = r * 1.05 + CS / 2; desc = c["desc"]
    st = cstem(x, r * 0.25 - 20 - J_DROP, C, top='left', foot=None, ent_span=(r * 0.25 - 60 - J_DROP, C))
    # Owner 2026-09-15: "lower the descender on J." J_DROP is how far FURTHER
    # below the baseline the hook sits, in units; 0 is the shipped cut, whose
    # ink stops at -119 where p, y, g and j all reach -281 to -298.
    #
    # It TRANSLATES the hook and grows the stem down to meet it, and that is
    # the whole trick. Scaling the tail's descent instead -- which is the
    # obvious thing and what I tried first -- turns a shallow swing left into a
    # hook that plunges and doubles back on itself, because the two control
    # points move down while their x stays put. A wide stroke round a 180
    # degree turn balloons: at twice the depth the ink ran to x -115 and the
    # fitting rule collapsed the advance from 410 to 217. A deeper J is the
    # same hook, lower.
    _j = J_DROP
    tail = cubic((x, r * 0.25 - _j), (x, -desc * 0.42 - _j),
                 (x - r * 0.55, -desc * 0.55 - _j), (x - r * 1.1, -desc * 0.1 - _j))
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

# ROUND 224 -- THE TAIL'S LENGTH IS THE DRAWING'S, AND THIS IS ITS DIAL.
# Fourteen of the roman's nineteen touching pairs are this one letter --
# Q( Q) Q3 Q4 Q5 Q7 Q9 Qg Qj QJ Qp Qq QQ Qy, the worst Q3 at -0.489 em -- and
# a kern was tried first and removed the same round (see the note in
# outlines/kern.py: the pairs want +270 to +522 units, a third to a half of
# the Q's own advance, and three still touch afterwards because the tail meets
# a following descender at a different row).
#
# WHAT THE NUMBER IS, measured off the built fonts rather than asserted. The
# tip lands at 1.80 ring-widths, so the ink box runs 36..1250 against an
# advance of 741: **509 units of tail hang past the letter's own advance**,
# and the ink is 1.80 cap heights wide where the rest of the round family is
# 0.89-0.99. Both reference romans keep the tail INSIDE the advance and take
# it DOWN rather than right -- Times ends its Q's ink 38 units short of the
# advance and drops to -196, Georgia 39 short and -188 -- and the owner's own
# italic Q, whose tail he ruled at Q_TAIL_SCALE 1.2 in round 178, ends 32
# units PAST its advance. So the family's character is a tail that reaches
# about as far as the letter does, and this one reaches two thirds again.
#
# The tail is scaled about its JOIN and not re-drawn. That holds round 156's
# requirement that the tail's first point sit ON the ring, and a uniform scale
# about a fixed point leaves every tangent direction unchanged -- including
# the departure tangent, so the join cannot open the step under the bowl that
# round 179 spent a round closing.
Q_TAIL = float(os.environ.get("ALBO_ROM_Q_TAIL", 1.0))   # x the tail's reach, about the join; 1.0 is round 223 byte for byte

@glyph('Q')
def g_Q(c):
    """The O with Van den Keere's swash tail (round 42): from the ring's
    centerline at 250 degrees, heaviest at its belly (1.05 stems), thinning
    to a pen-cut tip at 1.8 O-widths, 0.2 C down -- Q_TAIL of that reach."""
    C = c["cap"]; rx_c = W_(c, 'O', 350); solid, o, i = cap_ring(c, rx_c); s = CS
    rx = rx_c + TH_V / 2; ry_c = C / 2 + OVER - TH_H / 2; W = 2 * rx
    p0 = superellipse(rx, C / 2, rx_c, ry_c, math.radians(250), math.radians(250.5), BOWL_K)[0]
    tp = [(W * 0.85, -C * 0.30), (W * 1.40, -C * 0.56), (W * 1.80, -C * 0.20)]
    if Q_TAIL != 1.0:
        tp = [(p0[0] + (x - p0[0]) * Q_TAIL, p0[1] + (y - p0[1]) * Q_TAIL) for x, y in tp]
    tail = cubic(p0, *tp)
    base = pen_widths(tail)
    def wfn(t):
        # THE BELLY SCALES WITH THE TAIL. It is an ABSOLUTE -- 1.05 stems, 100
        # units -- and the header note above already records what an absolute
        # did to this letter once: the solved Q (width x 0.70) got the bulge at
        # full size on a smaller ring, which is the bulge the owner asked to
        # lose. A shortened tail carrying the same 100 units is the same fault
        # again, so the floor travels with the reach; at Q_TAIL 1.0 the
        # expression is the original one multiplied by exactly 1.0.
        belly = max(0.0, 1 - abs(t - 0.45) / 0.4)
        return max(base(t), s * 1.05 * Q_TAIL * (3 * belly * belly - 2 * belly ** 3)) * widths([(0.0, 0.6), (0.12, 1.0), (0.8, 1.0), (1.0, 0.7)])(t)
    return geom.ink([solid, stroke(tail, wfn, cut1=CUT)])

Q_BELLY = 0.15

# ROUND 226 -- THE ROMAN R's LEG KICKS. Owner 2026-09-18, verbatim: *"make the
# roman R kick like the italic one (make other changes to it as needed)"*.
#
# WHAT THE KICK IS ON THE ITALIC, and then what this R does -- both measured the
# SAME WAY on the BUILT fonts (the italic unsheared by 13 degrees), taking the
# rightmost ink run at each height, its centre as x from that letter's OWN stem
# midline, the travel direction of that centre, and the run's perpendicular
# thickness. Cap 674 both sides:
#
#            ------- the italic -------      ---- this R, as it ships ----
#     y      centre       travel  thick      centre       travel  thick
#    270    0.283 cap      -59     67        0.345 cap      -63     80
#    200    0.342          -59     68        0.395          -62     91
#    150    0.388          -56     71        0.437          -61     93
#    120    0.418          -54     72        0.463          -57     91
#     90    0.452          -52     72        0.490          -58     93
#     60    0.498          -47     75        0.526          -46     80
#     40    0.528          -42     70        0.560          -37     71
#     30    0.547          -36     64        0.583          -30     61
#     20    0.571          -25     45        0.612          -25     51
#     10    0.607          -23     41        0.644          -28     55
#      0    0.645          -23     45        0.670          -25     35
#    -10    0.676          -40     51        0.707          -23     14
#
# (the roman's thickness above y 90 reads the bowl and the leg as one run, where
# they overlap; the leg alone is the ruled 88 plus the build's 1.2 of spread.)
#
# Read down the italic's travel column and the kick is NOT a bow along the whole
# leg, which is what it looks like at a glance and what a first cut here would
# draw. For its upper two thirds that leg is STRAIGHT and at the roman's own
# ruled angle -- -59 degrees against R_LEG_ANG's 60 -- and the whole kick lives
# in the last 0.15 of the cap: the travel rotates from -59 to -23 over 90 units
# of height, the stroke swells about a tenth where it turns (67 -> 75 at y 60,
# the elbow), and then it tapers hard, 75 -> 45, running out to 0.735 cap of ink
# and finishing a few units under the baseline on the pen's cut.
#
# So the roman keeps everything above the knee -- the junction on the bowl, the
# 60-degree run, the ruled width (1.05 x the pen at that angle, round 42) -- and
# gains the turn and the run-out. The stroke is drawn JUNCTION-FIRST now rather
# than foot-first, because the width has to key to the RUN (thin where it
# springs, full down the straight, a swell at the elbow, a taper out to the tip)
# and a foot-first table would state all four of those backwards.
#
# WHAT IS ROMAN ABOUT IT, and none of it is negotiable:
#   THE PEN     the widths are `pen_widths(leg_c, scale=1.05)` -- the same pen
#               and the same 1.05 the straight leg was drawn at, so the run's
#               thinning as it flattens is the nib's own (83.8 units at -60
#               degrees of travel, 65.9 at -20, 47.5 at 0) and not a declared
#               taper laid over it. At the junction that reproduces round 42's
#               88.0 to the unit, which is why the letter's colour barely moves.
#   THE FOOT    THE PEN'S OWN CUT, and this is the one place the letter gives
#               up a family serif -- so it is a negative result rather than a
#               preference. The straight strut ended in `end_wedge`, the A's
#               foot, and the wedge was the first thing tried out here. It
#               cannot work at a shallow exit and the reason is mechanical:
#               `diag_wedge` seats its apex `WL` along the OUTWARD NORMAL of the
#               stroke's end, and at -17 degrees of travel that normal points
#               up and to the right. Rendered at 520 px and looked at, four
#               ways: full wedge on the outer side is a 59-unit barb standing
#               up off the tail (`B` in the ladder -- a spearhead); at 0.35 of
#               the family it is a smaller spearhead; hung under the tail
#               (FOOT_SIDE -1) at 0.35 and at 0.60 it is a downward claw. A
#               wedge is a serif for a stroke that STOPS, and this one runs out.
#               So the tail is cut with `CUT`, which is what the italic does and
#               what `g_Q`'s tail already did in this module. R_KICK_FOOT > 0
#               brings the wedge back for anyone who wants to re-argue it.
#   THE UPRIGHT nothing is sheared: this is drawn upright and the kick's
#               geometry is stated in the roman's own frame.
#
# WHAT ELSE MOVED, AND IT IS ONE THING: THE JUNCTION ON THE BOWL, -52 -> -66
# degrees. That is the "other changes as needed", and it is not a taste call --
# it is what gives the run-out somewhere to go. In DESIGN units, from each
# letter's stem midline: at -52 this leg springs at 0.333 cap and 0.547 high,
# where the italic's table (`CAP_R_LEG`, row 0) springs at 0.247 and 0.464. So
# the roman started 0.086 cap further out, and a run-out of the italic's own
# length would have finished 0.09 cap past the italic's tip -- which the fitter
# then bills for (see THE REACH). At -66 the spring lands at 0.250 and 0.517:
# the same distance out as the italic's, a little higher up the bowl, which is
# what an upright letter's bowl puts there. On the built letters the two legs
# then run within 0.03 cap of one another all the way down (the table above).
#
# Laddered -52 / -60 / -66 / -72 at the shipped tail and rendered at 500 px.
# All four pass the glitch sweep; the render is what separates them. -52 leaves
# a visible step where the leg's upper edge crosses the bowl's outer edge, and
# the crotch between the bowl's lower arm and the leg is a sharp V. -72 pulls
# the spring under the bowl and pinches the counter's lower right into a narrow
# wedge. -66 is the one where the bowl's underside and the leg read as one
# continuous shape.
#
# Nothing else moved: the bowl's size and profile, the stem, the serifs, the
# straight run's 60 degrees and its ruled width are all untouched.
#
# THE REACH IS SET BY THE FITTER'S BILL, NOT BY THE DRAWING, and the number that
# decides it is the RIGHTMOST INK rather than the tip's centre. `build.fit`
# measures a capital over the CAP BAND, so every unit the tail gains inside that
# band is a unit on the advance: at R_KICK_REACH 0.780 the R's widest in-band
# ink went 650 -> 689 and its advance went 680 -> 718, +5.6%. Measured, all four
# from the stem's own midline:
#
#                 rightmost ink    at y      R's advance   RY min white
#   round 225        0.723 cap    +0.099 cap     680         0.130 em
#   reach 0.730      0.733        -0.028         684         0.170
#   reach 0.780      0.784        -0.028         718         0.245
#   the italic       0.735        -0.016          --           --
#
# 0.730 puts the roman's tail within two units of the italic's own reach AND
# leaves the letter's fitting where it was; 0.780 overshoots the italic by 0.05
# cap and buys nothing but a longer run-out. The tip's HEIGHT is the lever that
# actually pays -- round 138's finding, and it holds here: the overhang used to
# sit a tenth of a cap UP (the wedge's apex) where a following a, o or e is
# already at its widest, and it now sits below the baseline where they are open.
# Minimum white on the shaped pair, round 225 -> this: **Ra 0.067 -> 0.102 em,
# Re 0.097 -> 0.152, Ro 0.100 -> 0.162**. Two pairs move the other way and both
# are reported rather than fixed. **Rn 0.139 -> 0.089**, the n's flat left stem
# meeting the tail where the old leg had already stopped -- still seven times
# `cmp_touch`'s 0.012 em floor. And **RY 0.126 -> 0.167** (`cmp_cap_space`
# 0.130 -> 0.170, which flags it WIDE beside the AY, LY, OY, VY and NY it
# already flagged): the leg no longer reaches UP toward the Y's arm, so the
# closest approach moved. That is a kern pair, not a shorter leg, and the kern
# table is not touched here.
#
# R_KICK = 0 is round 225's letter BYTE FOR BYTE -- the branch below is the old
# code verbatim, not a special case of the new one, and it was proved by
# building both from one tree state and diffing all 470 glyphs with a
# RecordingPen.
R_JOIN = float(os.environ.get("ALBO_ROM_R_JOIN", -66.0))        # degrees round the bowl where the leg springs; -52 is round 42's
R_LEG_ANG = float(os.environ.get("ALBO_ROM_R_LEG_ANG", 60.0))   # the straight run's angle; 60 is the ruling of round 32
R_KICK = float(os.environ.get("ALBO_ROM_R_KICK", 1.0))          # 0 = the straight strut of round 225, byte for byte
R_KICK_EXIT = float(os.environ.get("ALBO_ROM_R_KICK_EXIT", 17.0))    # degrees below horizontal the tail leaves at (the italic's last run measures -23)
R_KICK_REACH = float(os.environ.get("ALBO_ROM_R_KICK_REACH", 0.730))  # x cap: the tip's CENTRE, right of the stem's midline; see THE REACH
R_KICK_DROP = float(os.environ.get("ALBO_ROM_R_KICK_DROP", 0.004))   # x cap: the tip's centre below the baseline (the italic's is 0.006)
R_KICK_BEND = float(os.environ.get("ALBO_ROM_R_KICK_BEND", 0.70))    # the departure handle, x the chord: how LOW the turn sits
R_KICK_FLARE = float(os.environ.get("ALBO_ROM_R_KICK_FLARE", 0.38))  # the arrival handle, x the chord: how long the run-out is
R_KICK_ELBOW = float(os.environ.get("ALBO_ROM_R_KICK_ELBOW", 0.62))  # t of the swell at the turn
R_KICK_SWELL = float(os.environ.get("ALBO_ROM_R_KICK_SWELL", 0.06))  # the elbow's extra, x itself (the italic's is 0.10)
R_KICK_TIP = float(os.environ.get("ALBO_ROM_R_KICK_TIP", 0.42))      # the tip's width, x the pen's own there
R_KICK_SPRING = float(os.environ.get("ALBO_ROM_R_KICK_SPRING", 0.42))  # and at the junction, x the pen's -- round 225's own 0.42
R_KICK_FOOT = float(os.environ.get("ALBO_ROM_R_KICK_FOOT", 0.0))     # 0 = the pen's cut (see THE FOOT above); >0 = the family's wedge at x 0.9 of it
R_KICK_FOOT_SIDE = float(os.environ.get("ALBO_ROM_R_KICK_FOOT_SIDE", 1.0))  # +1 the outer (upper) side, as the A's foot; -1 hangs it below

@glyph('R')
def g_R(c):
    C = c["cap"]; x = CS / 2; w = W_(c, 'R', 400); edge = x + CW / 2
    bowl, cx, cy, rx, ry, L, R = half_bowl(edge, C, C * 0.46, w * 0.95 * 0.72 + TH_V / 2, open_bottom=0.06)
    ang = math.radians(R_JOIN); J = (cx + rx * math.cos(ang), cy + ry * math.sin(ang))
    # `foot` is where the straight 60-degree run would MEET the baseline, and it
    # is still computed in both branches: round 225 drew the leg from it, and
    # the kick still takes its ruled width from it (`pw(foot, J, 1.05)`, the
    # pen at the leg's own angle -- round 42/51).
    foot = (J[0] + J[1] / math.tan(math.radians(R_LEG_ANG)), 0)
    d = (J[0] - foot[0], J[1] - foot[1]); Ld = math.hypot(*d); d = (d[0] / Ld, d[1] / Ld); nrm = (-d[1], d[0])
    w_foot = pw(foot, J, 1.05)
    if not R_KICK:
        end = (J[0] + d[0] * CS * 0.15, J[1] + d[1] * CS * 0.15)
        c1 = (foot[0] + d[0] * Ld * 0.35 - nrm[0] * 9, foot[1] + d[1] * Ld * 0.35 - nrm[1] * 9)
        c2 = (foot[0] + d[0] * Ld * 0.70 - nrm[0] * 9, foot[1] + d[1] * Ld * 0.70 - nrm[1] * 9)
        leg_c = cubic(foot, c1, c2, end)
        leg = stroke(leg_c, lambda t: w_foot * widths([(0.0, 1.0), (0.45, 1.0), (1.0, 0.42)])(t))
        return geom.ink([cstem(x, 0, C), bowl, leg, end_wedge(leg_c, w_foot, True, 1)])
    # THE KICK. ONE cubic from inside the bowl to the tip, with the departure
    # tangent pinned to the straight run's own angle and the arrival tangent to
    # R_KICK_EXIT. One curve and not a line plus an arc, because a straight
    # segment joined to a curve is tangent-continuous but NOT curvature-
    # continuous, and a stroke's edge is centreline +/- w/2: the curvature step
    # lands on both edges at once and shows as a flat, which is the fault
    # `_R_traced` records on the italic's bowl at a 400 px cap. A cubic whose
    # first handle is the longer holds its departure direction over most of its
    # length, so the upper two thirds stay the straight 60-degree leg the letter
    # already had and the turn collects in the last fifth of the cap -- the
    # travel column of the table at the head of this block, measured on the
    # shipped build, is the check on that.
    start = (J[0] + d[0] * CS * 0.15, J[1] + d[1] * CS * 0.15)   # buried in the bowl, as the strut was
    u0 = (-d[0], -d[1])
    e = math.radians(R_KICK_EXIT); u1 = (math.cos(e), -math.sin(e))
    tip = (x + R_KICK_REACH * C, -R_KICK_DROP * C)
    chd = math.hypot(tip[0] - start[0], tip[1] - start[1])
    k1 = (start[0] + u0[0] * chd * R_KICK_BEND, start[1] + u0[1] * chd * R_KICK_BEND)
    k2 = (tip[0] - u1[0] * chd * R_KICK_FLARE, tip[1] - u1[1] * chd * R_KICK_FLARE)
    leg_c = cubic(start, k1, k2, tip)
    base = pen_widths(leg_c, scale=1.05)
    prof = widths([(0.0, R_KICK_SPRING), (0.30, 1.0), (R_KICK_ELBOW, 1.0 + R_KICK_SWELL), (1.0, R_KICK_TIP)])
    leg = stroke(leg_c, lambda t: base(t) * prof(t), cut1=(None if R_KICK_FOOT else CUT))
    parts = [cstem(x, 0, C), bowl, leg]
    if R_KICK_FOOT:
        parts.append(end_wedge(leg_c, base(1.0) * R_KICK_TIP, False,
                               1 if R_KICK_FOOT_SIDE >= 0 else -1, scale=0.9 * R_KICK_FOOT))
    return geom.ink(parts)

R_LEG_BURY = 0.28
S_BOTTOM_END = 1.30

# ROUND 224 -- THE S IS THE ROUND FAMILY'S ONE HEAVY LETTER, AND IT SITS PROUD.
# Measured on the built roman with a PADDED chamfer mask (see the note under
# S_CROWN): stroke 84.3 against a round-family median of 66.2, +27%, and 22%
# over its own O at 69.2. Both references run the S LIGHTER than the O, not
# heavier -- Times S 48.2 against O 66.2 (-27%), Georgia 54.2 against 68.5
# (-21%) -- so the sign is wrong here, not just the size. The lever is the
# DECLARED middle weight: `st * 0.92` overrides the pen with 0.92 cap stems
# (87.9 units, the cap stem itself) through the whole waist, and the `bot`
# bump adds a further fifth on the way out of it. The pen at the ends is
# untouched, so the letter's contrast is set by what the nib does at the S's
# own shallow angles and not by a second declared number.
S_SPINE = float(os.environ.get("ALBO_ROM_S_SPINE", 0.92))   # the waist's declared weight, x CS; 0.92 is round 223
S_BOT = float(os.environ.get("ALBO_ROM_S_BOT", 0.20))       # the lower curve's extra, x itself; 0.20 is round 223

# ...AND ITS CROWN AND FOOT STAND OUTSIDE THE ROUND FAMILY'S LINE. Ink top 699
# and bottom -25 against O 690/-15, G 691/-17, C 691/-17: ten units proud at
# each end. Both references put the S's extremes ON the O's -- Times 677.2 for
# both, Georgia 708.5 against 709.5. It is not the beak: the topmost ink sits
# at x 280-314, the crown of the arc, where the beak is away at the top-right
# terminal. The catmull OVERSHOOTS its own second point, so the crown is an
# artefact of the curve rather than a declared overshoot, and the honest lever
# is to pull the two extreme points inside the band by the measured amount.
S_CROWN = float(os.environ.get("ALBO_ROM_S_CROWN", 0))    # units the crown and foot come inside the cap band; 0 is round 223

# ...AND THE REASON THE WAIST HAD TO BE DECLARED AT ALL: THE S IS THE ONE
# ROUND CAPITAL DRAWN ON THE RAW PEN. C, G, O, Q and the B/D/P/R bowls all
# take their widths from `primitives.bowl_th` -- the family's switched bowl
# profile, whose hair is `1 - 0.5 CONTRAST` of the stem, 50.4 units at the
# shipped contrast -- while `g_S` calls `pen_widths`, whose floor is the nib's
# own minimum of 22.2 at the 18-degree run the S makes over its shoulders. So
# the letter arrives with hairline ends the family does not have, and the 0.92
# cap stems through its waist is what was put in to stop it reading as wire.
# The two together are the measurement: cut 2.95 against the O's 1.60, +84%,
# where Times holds S/O at 1.27 and Georgia at 0.94. Blending the S's own
# widths onto the family's profile fixes the ratio at both ends at once and
# needs no new number -- `bowl_th` IS the round family's definition, imported
# rather than restated.
S_BOWL = float(os.environ.get("ALBO_ROM_S_BOWL", 0))      # 0 = the raw pen (round 223), 1 = the round family's own bowl profile

@glyph('S')
def g_S(c):
    C = c["cap"]; w = W_(c, 'S', 440); o = OVER - TH_H / 2; st = CS
    spine = catmull([(w * 0.93, C * 0.80), (w * 0.62, C + o * 0.9 - S_CROWN), (w * 0.18, C * 0.86), (w * 0.2, C * 0.6),
                     (w * 0.8, C * 0.42), (w * 0.84, C * 0.16), (w * 0.42, -o * 0.9 + S_CROWN), (w * 0.04, C * 0.22)], tension=0.55)
    base = pen_widths(spine)
    if S_BOWL != 0.0:
        _pen, _bowl = base, bowl_widths(spine)
        base = lambda t: _pen(t) * (1.0 - S_BOWL) + _bowl(t) * S_BOWL
    def wfn(t):
        mid = 1.0 - min(1.0, abs(t - 0.5) / 0.28); want = base(t) * (1 - mid) + st * S_SPINE * mid
        bot = max(0.0, 1 - abs(t - 0.74) / 0.22); want *= 1 + S_BOT * (3 * bot * bot - 2 * bot ** 3)
        return want * widths([(0.0, 1.3), (0.10, 1.0), (0.86, 1.0), (1.0, S_BOTTOM_END)])(t)
    if PR.BOWL and PR.BOWL.get('widen'):
        wid = widen_terminal(widen_terminal(None, True), False)
        # `base`, not a second `pen_widths(spine)`: this branch kept its own
        # copy, which was identical until S_BOWL existed and would now be the
        # one place in the letter still on the raw pen. Unreachable at the
        # ruled bowl ('B' declares widen=None) and the built font is
        # unchanged, but a second definition is how the next dial drifts.
        base2 = base
        def wfn2(t):
            mid = 1.0 - min(1.0, abs(t - 0.5) / 0.28); want = base2(t) * (1 - mid) + st * S_SPINE * mid
            bot = max(0.0, 1 - abs(t - 0.74) / 0.22); want *= 1 + S_BOT * (3 * bot * bot - 2 * bot ** 3)
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

# ROUND 224 -- THE W's +43% IS THE INSTRUMENT, AND IT SHIPS AT ITS NO-OP.
# `cmp_weight_survey` reads the W's stroke at 89.6 against a diagonal-family
# median of 62.8 and flags it as the family's heaviest. It is not. The survey
# reports the MEDIAN thickness along a letter's ridge, and a W is two thicks
# and two thins where a V is one of each -- so the V's median falls on its
# thin (59.5) and the W's on its thick (89.6) while the two letters' THICKS
# are 89.6 and 90.3, within a raster step of each other, because both are the
# same `pw(p0, p1, 1.0)` on strokes within two degrees of the pen's thick
# axis. Both references order the three the same way and by more: Times W 93.3
# > V 90.3 > X 86.6, Georgia 96.3 > 95.6 > 88.8. By COLOUR -- ink over the
# reading band, which no stroke count can skew -- the W is 0.256 against its
# family's 0.272, slightly LIGHT, and the references agree in sign (-3%, -10%).
# So the dial exists for a future ruling and is shipped at 1.0, which is round
# 223 byte for byte. What the W IS wide: 1.52 cap heights of ink against Times
# 1.39 and Georgia 1.43. That is `W_(c, 'W', 820)` and the builder's solve, it
# is a proportion rather than a weight, and it is not changed here.
W_THICK = float(os.environ.get("ALBO_ROM_W_THICK", 1.0))   # the two down-strokes, x the pen at their angle

@glyph('W')
def g_W(c):
    C = c["cap"]; s = CS; w = W_(c, 'W', 820)
    f1, f2, apex = (w * 0.26, 0), (w * 0.74, 0), (w * 0.5, C)
    P = [((s * 0.3, C), f1, W_THICK, 1), (apex, (f1[0] + s * 0.15, 0), 0.72, None), (apex, f2, W_THICK, None), ((w - s * 0.3, C), (f2[0] + s * 0.15, 0), 0.72, -1)]
    a, b, d, e = [diagonal(p0, p1, pw(p0, p1, m), serif0=sf) for p0, p1, m, sf in P]
    # owner 2026-09-13: "lower and reduce the protuberance of the top middle
    # connector in W" -- the crown at W_CROWN of the family's wedge, seated
    # W_CROWN_DROP x the family's drop lower
    crown = wedge((apex[0] - pw(P[1][0], P[1][1], 0.72) * 0.35, C - DROP * (W_CROWN_DROP - 1.0)), (0, 1), (-1, 0), WL * W_CROWN, WD * W_CROWN, DROP)
    return geom.ink([a, b, d, e, crown])

# ROUND 224 -- THE X's LIGHT DIAGONAL IS THE PEN'S THIN TWICE OVER.
# THE ONE RULE FIRST (docs/albo-method.md): check the DIRECTION before the
# width. The X's two strokes run at 49 and 131 degrees; the pen's own thin
# axis is 30 and its thick 120, so at those angles the nib already gives 44.9
# and 81.5 where the V's steeper pair get 61.2 and 83.7. The thick is
# therefore right and is not touched. What is NOT the pen is the 0.72 the
# light stroke is then multiplied by: it is the family's declared thin factor,
# uniform across A V W X Y, and at the X's angle it lands on a nib width that
# is already near its minimum, so the two thinnings COMPOUND. The result, on
# the built roman, is 33.1 units -- with the S's 32.4 the thinnest capital
# stroke in the face, 0.66 of the V's thin where both references run their X's
# thin at 0.89 (Times) and 0.93 (Georgia) of their V's, and where the X's own
# contrast is 2.45 against the V's 1.78 where the references hold the two
# within 8% of each other. At a 13 px em that stroke is 0.43 device pixels and
# the backslash of SWIX reads as a wire. docs/albo-imperfections.md's fourth
# rule: an imperfection that costs legibility is a defect.
X_THIN = float(os.environ.get("ALBO_ROM_X_THIN", 0.90))   # the light diagonal, x the pen at its own angle; 0.72 is round 223

@glyph('X')
def g_X(c):
    C = c["cap"]; s = CS; w = W_(c, 'X', 540)
    p0, p1 = (s * 0.3, C), (w - s * 0.3, 0); q0, q1 = (w - s * 0.3, C), (s * 0.3, 0)
    return geom.ink([diagonal(p0, p1, pw(p0, p1), serif0=1, serif1=1), diagonal(q0, q1, pw(q0, q1, X_THIN), serif0=-1, serif1=-1)])

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
