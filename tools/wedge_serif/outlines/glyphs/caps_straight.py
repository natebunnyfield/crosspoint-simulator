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
# ROUND 272 -- THE DIAGONALS ABOVE STEM 84. Owner 2026-09-19: *"for roman
# 700 and 900, 'w' 'v' and possibly others are too heavy compared to
# others."* Round 51's rule makes a down-right diagonal the PEN's broad,
# about 1.10 of the stem at every weight, and at the heavy ends that tenth
# is what reads: measured on the ridge, the v's thick ran 1.12 x the n's
# stem at the 700 and 1.23 at the 900, the w's 1.17 and 1.22, the k's 1.14
# and 1.21, the K's 1.18 and 1.31. Above 84 the pen's width is capped at
# DIAG_CAP x S -- 0.93, which is where the n's stem itself measures at
# those weights (0.95 S at the 700, 0.91 S at the 900, the stem's own
# entasis) -- so the thick diagonal lands on the stem. At and under 84 the
# rule is round 51's and the 400 is byte-identical.
DIAG_CAP = float(os.environ.get("ALBO_DIAG_CAP", 0.93))
def pw(p0, p1, mult=1.0):
    """Round 51's `latin.diag`: a capital's diagonal is `mult` x the PEN's
    width at its own angle (the cap factor cancelled out of it); the thin
    strokes 0.72 x that."""
    tn = tangents(line(p0, p1))[0]; th = pen.th_t(tn)
    if S > 84.0 and DIAG_CAP: th = min(th, S * DIAG_CAP)   # round 272, see DIAG_CAP
    return th * mult
BEAK_CUT = -28.0

# ---------------------------------------------------------------------------
# THE 2026-09-18 BUMP FIXES (owner's write-up on the hi-res bump sheets,
# docs/albo-bump-markup-2026-09-18.md, rows R01-R16). Every fix below is
# gated on FIX_ROM: the italic draws its capitals through these same
# functions, and the caller's brief for this round (not an owner ruling)
# required the italic byte-identical, so the roman alone takes them. Each glyph's own comment carries his words, what was
# wrong in units, what moved and what did not.
FIX_ROM = not pen.ITALIC
A_APEX_CLIP = os.environ.get("ALBO_ROM_A_APEX_CLIP", "0") == "1"
L_CORNER_CLIP = os.environ.get("ALBO_ROM_L_CORNER_CLIP", "0") == "1"
M_SPURS = os.environ.get("ALBO_ROM_M_SPURS", "1") == "1"
M_RIGHT_CROWN = os.environ.get("ALBO_ROM_M_RIGHT_CROWN", "1") == "1"   # round 243: the right top takes the left crown, mirrored
# ROUND 271 -- THE RIGHT TOP IS THE LEFT TOP, MIRRORED. Owner 2026-09-19,
# verbatim: "M needs to have symmetrical stem tops, based on left top."
# Round 243 rebuilt the right crown from the left's RECIPE (the family's
# wedge, seated at the thick stem's outer corner), and the two still did not
# match, because the recipes are seated on strokes of different widths: the
# left crown sits 0.35 of the THIN stroke's width inside its top and the
# right one on the THICK stem's outer corner, so the right serif projected
# 7 units further at the 400, 28 at the 700 and 46 at the 900, and only the
# left top carried the 17-unit peak over the cap line (the thick inner
# stroke's square-cut corner). Measured on the built letter, row by row
# (docs/albo-family-2026-09-19.md, round 271). So the right top is now the
# left top's INK, reflected about the letter's axis -- the outer strokes are
# placed symmetrically, x0 + 0.25 s and x1 - 0.25 s -- and shifted outward
# by half the difference of the two outer strokes' widths, so the two
# silhouettes align on the stems' OUTER edges, which is what the eye reads.
# The band taken is the left top down to 130 under the cap line, and no
# further in than the peak, so nothing of the thick inner stroke's body
# travels. The round-243 right crown is off under this dial (it is what the
# mirror replaces); the spike trim and the vertex stay.
M_TOP_MIRROR = float(os.environ.get("ALBO_ROM_M_MIRROR", 1.0))
# (A "come to a point" ladder was drawn the same hour and withdrawn by the
# owner before it was shown: "left was okay before, just need to match
# right to left." The left top is round 243's, untouched.)
M_VERTEX_V = os.environ.get("ALBO_ROM_M_VERTEX_V", "1") == "1"         # round 243: the vertex one point, as the V   # round 240: strokes as round 232, errant spurs cut; 0 is round 232 exactly   # round 239: off, the flare tucks in like the E's   # round 236: the R01 clip is off, owner: "restore apex"

def _left_of(p, tn, ylo, yhi, reach=1500.0):
    """The half-plane LEFT of the line through p with direction tn, cut to
    the band ylo..yhi -- the clip that keeps a thick stroke's flat corner from
    standing out past the thin stroke that makes the letter's silhouette (the
    A's apex, the M's and the W's)."""
    xat = lambda y: p[0] + tn[0] / tn[1] * (y - p[1])
    return geom.poly([(xat(ylo), ylo), (xat(yhi), yhi), (xat(yhi) - reach, yhi), (xat(ylo) - reach, ylo)])

def _half_bowl_flat(edge, y_top, y_bot, rx, k=pen.BOWL_K * 1.12, open_bottom=0.0, w_scale=1.0, into=22.0, taper=0.7, taper_span=0.08):
    """`primitives.half_bowl` with its end TAPER taken from the counter side
    only (R02/R03, owner: "straighten, no fracture"). The primitive eases each
    end to `taper` of the hairline symmetrically about the centreline, so the
    OUTER edge -- the bowl's flat run on the baseline or the cap line -- rose
    2.3 units (B) and 3 (D) over the last ~30 units before the stem, and at
    the stem it met the stem's own square corner with a 2-unit step. Here
    the centreline is shifted toward the outer edge by half of what the
    taper takes, so that edge holds y_bot / y_top from the arc's tangent
    point all the way into the stem and the taper shows only on the counter
    side, buried where the bowl runs `into` the stem. Widths are read off
    the UNSHIFTED centreline's tangents, so every width is the primitive's
    own to the unit; the arc, the flats, the shoulders and open_bottom are
    untouched. Local to this file rather than a primitive change: the same
    primitive draws the P, the R and every lowercase bowl, and none of those
    was named."""
    from ..geom import resample
    hair = S * (PR.BOWL['hair'] if PR.BOWL else PR.BOWL_HAIR); mx = S * (PR.BOWL['max'] if PR.BOWL else PR.BOWL_MAX)
    if PR.BOWL: taper = PR.BOWL['taper']
    ry_c = (y_top - y_bot) / 2 - hair / 2; rx_c = rx - mx / 2
    cy = (y_top + y_bot) / 2; cx = edge + rx * 0.05
    arc_rx = min(rx_c, ry_c * PR.BOWL_ARC); flat = rx_c - arc_rx; ax = cx + flat
    arc = superellipse(ax, cy, arc_rx, ry_c, -math.pi / 2, math.pi / 2, PR.BOWL['k'] if PR.BOWL else PR.BOWL_ARC_K)
    center = [(edge - into, cy - ry_c)] + arc + [(edge - into, cy + ry_c)]
    center = resample(center)
    n = len(center) - 1
    if open_bottom:
        def win(t): return max(0.0, math.sin(math.pi * (t - 0.04) / 0.46)) if 0.04 <= t <= 0.50 else 0.0
        center = [(px, py + 0.5 * open_bottom * TH_H * win(i / n)) for i, (px, py) in enumerate(center)]
    tans = tangents(center)
    def ease(t):
        if t < taper_span: u = t / taper_span
        elif t > 1 - taper_span: u = (1 - t) / taper_span
        else: return 1.0
        return taper + (1 - taper) * (3 * u * u - 2 * u ** 3)
    def wfull(t):
        i = min(n, int(round(t * n)))
        w = PR.bowl_profile(tans[i]) * w_scale
        if open_bottom: w += open_bottom * TH_H * win(t)
        return w
    def wfn(t): return wfull(t) * ease(t)
    # Only the OUTER edge moves. The primitive's taper took dw off the width
    # symmetrically -- dw/2 off each edge. Here the counter edge keeps exactly
    # that dw/2 (so the counter is the primitive's to the unit) and the outer
    # edge gives up its half: width wfull - dw/2, centreline shifted dw/4
    # toward the outer edge. The end face is then 0.925 of the hairline,
    # vertical, 22 units inside the stem.
    def wfn(t): return wfull(t) * (1.0 - (1.0 - ease(t)) / 2)
    shifted = []
    for i, (px, py) in enumerate(center):
        t = i / n; dw = wfull(t) * (1 - ease(t))
        shifted.append((px, py + (-1.0 if t < 0.5 else 1.0) * dw / 4))   # bottom run: the outer edge is below; top run: above
    solid, L, R = stroke(shifted, wfn, raw=True, sides=True)
    return solid, cx, cy, rx_c, ry_c, L, R

def _flat_diag(p0, p1, w, flat0=False, flat1=False, serif0=None, serif1=None):
    """`primitives.diagonal` with either end cut HORIZONTAL -- the M's and
    W's apexes and the M's middle vertex, where two strokes meet at one point
    and each square face tilts its own way. `flat_face` was written for
    `stroke`'s cut0/cut1, and its algebra is right, but the shear it asks
    for is tan(cut) x w/2 = 15-20 units on these strokes and `stroke`'s
    `_unfold` drops any side point moved back past the previous 11-unit
    sample: the M's vertex face came out tilted with its corner 9 units
    UNDER the baseline. So the stroke is drawn one width past the point and
    clipped at the line through it -- exact, and nothing to unfold. The end
    wedges are seated from the ORIGINAL ends, as `diagonal` seats them."""
    from shapely.geometry import box as _box
    tn = tangents(line(p0, p1))[0]
    q0 = (p0[0] - tn[0] * w, p0[1] - tn[1] * w) if flat0 else p0
    q1 = (p1[0] + tn[0] * w, p1[1] + tn[1] * w) if flat1 else p1
    body = stroke(line(q0, q1), w)
    far = 5000.0
    if flat0: body = body.difference(_box(-far, -far, far, p0[1]) if p1[1] > p0[1] else _box(-far, p0[1], far, far))
    if flat1: body = body.difference(_box(-far, p1[1], far, far) if p1[1] > p0[1] else _box(-far, -far, far, p1[1]))
    pts = line(p0, p1); parts = [body]
    if serif0: parts.append(end_wedge(pts, w, True, serif0))
    if serif1: parts.append(end_wedge(pts, w, False, serif1))
    return geom.union(parts)

def _beak_lip(pts, L, w, cut_deg=BEAK_CUT, lip=(0.4, 0.7), inset=6.0, fillet=0.40):
    """The C/G/S beak's lip, drawn as ONE terminal with the cut face (R04,
    R14; owner: "make it one cohesive serif, not overlapping", "make cohesive
    and without any kink"). Three things `primitives.beak` did wrong, each
    measured on the built G:
      * its polygon closed from the inner corner A straight into the stroke
        along the unsheared normal, and with the face sheared 28 degrees that
        segment stands 6 sin 28 = 2.8 units BEHIND the face -- the 2-unit jog
        at (548,519) -> (543,514);
      * its bracket was built on the TANGENT line at A (`wedge`'s default
        edge), and the arc's real inner edge leaves that line by the sagitta
        -- 14 units in 92 on the G's radius, far more on the S's crown -- so
        the bracket crossed the real edge at an angle: the overlap on the G
        and the 6-unit Z-kink on the S at (329,566) -> (335,559);
      * its top edge left A perpendicular to the stroke while the face left A
        at 28 degrees, a kink at the corner between two pieces of one
        terminal.
    So: the polygon starts AT A (nothing behind the face); the bracket's
    seat and its samples are the stroke's own L side, walked by arc length,
    with the quadratic's control on the real edge's tangent at C so it
    leaves the edge tangent; and B sits on the cut face's own line (drop =
    -length tan cut), so outer corner, A and B are one straight cut. The
    lip's size is the family's 0.4 x 0.7, unchanged.

    THE APEX. Measured with a morphological opening at r 6 (what a 12-unit
    disc cannot reach): every wedge tip in the family gives up 40-50 units^2
    in a 13 x 11 box, and its apex is ~38 degrees. The lip is 3.5 times as
    deep as it is long where the family's wedge is 2, so with the family's
    fillet (control 0.65 of the depth from C) and B on the face line its
    bracket leaves B at 30 degrees and the opening took 78 units^2 in an
    11 x 21 box off the G -- the needle. `fillet` 0.40 puts the control
    further down the edge, the bracket leaves B at 41 degrees, and the tip
    goes back to a foot wedge's size. It is the lip's own number; every
    other wedge keeps 0.65."""
    tn = tangents(pts); d = (-tn[0][0], -tn[0][1]); nl = (-tn[0][1], tn[0][0])
    A = L[0]
    length = WL * lip[0]; depth = WD * lip[1]; drop = -length * math.tan(math.radians(abs(cut_deg)))
    B = (A[0] + nl[0] * length - d[0] * drop, A[1] + nl[1] * length - d[1] * drop)
    cum = [0.0]
    for a, b in zip(L, L[1:]): cum.append(cum[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    def edge_at(dist):
        for i in range(1, len(L)):
            if cum[i] >= dist:
                u = (dist - cum[i - 1]) / max(cum[i] - cum[i - 1], 1e-9)
                return (L[i - 1][0] + (L[i][0] - L[i - 1][0]) * u, L[i - 1][1] + (L[i][1] - L[i - 1][1]) * u)
        return L[-1]
    C = edge_at(depth); Cb = edge_at(max(depth - 4.0, 0.0))
    tC = (Cb[0] - C[0], Cb[1] - C[1]); Lt = math.hypot(*tC) or 1.0; tC = (tC[0] / Lt, tC[1] / Lt)   # back toward A, along the real edge
    ctrl = (C[0] + tC[0] * fillet * depth, C[1] + tC[1] * fillet * depth)   # as `wedge`: ctrl = A*fillet + C*(1-fillet), `fillet` of the depth from C
    fil = geom.quad(C, ctrl, B)
    edge = [edge_at(depth * i / 12) for i in range(13)]
    # round 237: `fil` whole, C included -- skipping fil[0] jumped from the
    # inset edge to the first fillet sample past C and left a 1-2 unit step
    # at the seat (the S, after round 235: "S beak was not fully corrected").
    outline = [A] + [(p[0] - nl[0] * inset, p[1] - nl[1] * inset) for p in edge[1:]] + fil + [B]
    return geom.poly(outline)

def _blunt_tip(A, B, back):
    """Round 237, the S: the terminal's point B cut off `back` units up the
    face A->B by a face perpendicular to it -- the half-plane beyond that line,
    to subtract. The lip's own apex is 41 degrees and still reads as a needle
    on the S's long, shallow terminal; a short flat end is what the family's
    pen leaves."""
    d = (B[0] - A[0], B[1] - A[1]); L = math.hypot(*d) or 1.0; d = (d[0] / L, d[1] / L)
    P = (B[0] - d[0] * back, B[1] - d[1] * back); n = (-d[1], d[0]); far = 40.0   # a box round the tip only: a half-plane cut the S's lower bowl (2 islands)
    return geom.poly([(P[0] + n[0] * far, P[1] + n[1] * far), (P[0] - n[0] * far, P[1] - n[1] * far),
                      (P[0] - n[0] * far + d[0] * far, P[1] - n[1] * far + d[1] * far),
                      (P[0] + n[0] * far + d[0] * far, P[1] + n[1] * far + d[1] * far)])

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
    if FIX_ROM:
        # R01, owner 2026-09-18: "the outside edge is slightly funky and
        # distracting." Measured on the built roman: the thin leg's outer
        # edge is one line (slope 0.368, every vertex within rounding) from
        # the foot bracket's top at y 102 up to y 617 -- and there it STOPS,
        # because the thin stroke ends 30 units under the cap line buried in
        # the thick leg, and the thick leg's own left edge, which leans the
        # other way, takes over the silhouette for the last 57 units: a
        # 41-degree bend in the A's left profile, then the thick leg's tilted
        # square face. The thick leg is clipped to the thin leg's outer line
        # here, so the outside edge is one straight line from the bracket to
        # the apex face. Nothing else moves: both legs' widths, angles and
        # ends, the foot, the bar and the apex face are as they were.
        # ROUND 236 -- RESTORED. Owner 2026-09-18, on the round-235 page: "R01
        # restore apex." The clip took the thick leg's overhang off the apex,
        # and that overhang is the apex he wants; the A is round 232's again,
        # byte for byte. R01's "funky outside edge" stays open for his word.
        if A_APEX_CLIP:
            right = right.difference(_left_of(Apt, tn, C * 0.6, C + 40.0))
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
    # R02, owner 2026-09-18: "straighten, no fracture" -- the lower bowl's
    # bottom edge rose 2.3 units over its last 30 before the stem and met the
    # stem's corner with a 2-unit step (the primitive's symmetric end
    # taper); the top of the upper bowl dropped 2 the same way, and at the
    # waist both bowls tapered toward each other so the shared bar pinched
    # from 50 to 45 units at the stem. `_half_bowl_flat` holds every outer
    # edge on its line; see it for what moved.
    hb = _half_bowl_flat if FIX_ROM else half_bowl
    up, *_ = hb(edge, C, waist - h / 2, w * 0.86 * 0.72 + TH_V / 2, open_bottom=0.0)
    lo, *_ = hb(edge, waist + h / 2, 0, w * 0.72 + TH_V / 2, open_bottom=0.06)
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
    # ROUND 267 -- at a 148 stem the lip's underside and the arc's end face
    # leave a 2.9-unit sliver of paper between them (CRACK, area 208). A
    # morphological close of 2 units seals any sliver under 4 wide and is
    # gated to stems above the 84 the letter was drawn at, so nothing under
    # that -- the shipped 400 included -- is touched.
    g = geom.ink([body, lip])
    if pen.S > 84.0:
        g = g.buffer(4.0, join_style=2).buffer(-4.0, join_style=2)   # 2.0 left the 2.8-unit crack untouched; a hole's MAX width is what a close has to span
    return g

@glyph('D')
def g_D(c):
    C = c["cap"]; x = CS / 2; rx = W_(c, 'D', 330); edge = x + CW / 2
    st = cstem(x, 0, C, top='left', foot='left')
    # R03, owner 2026-09-18: "straighten" -- the same end taper as the B's,
    # 3 units at the baseline and 3 at the cap line. `_half_bowl_flat`.
    bowl, *_ = (_half_bowl_flat if FIX_ROM else half_bowl)(edge, C, 0, rx + TH_V / 2, open_bottom=0.06)
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
    if not FIX_ROM:
        body = stroke(pts, wfn, cut0=math.radians(BEAK_CUT))
        lip = beak(pts, wfn(0.0), True, BEAK_CUT)
        b = bar(xg - s * 1.1, xg + s * 0.6, yb, bar_th, cut0=CUT, cut1=CUT)
        return geom.ink([body, lip, b])
    # R04, owner 2026-09-18: "make it one cohesive serif, not overlapping" --
    # the lip on the stroke's real inner edge, its top edge on the cut face's
    # line, nothing behind the face. `_beak_lip` carries the measurements.
    body, Lside, _ = stroke(pts, wfn, cut0=math.radians(BEAK_CUT), sides=True)
    lip = _beak_lip(pts, Lside, wfn(0.0), BEAK_CUT)
    # R05, owner 2026-09-18: "give me other options with more calligraphic
    # treatment" for the bar. ALBO_ROM_G_BAR picks; `a` is today's drawing
    # byte for byte. Today: both ends pen-cut the same way, so the bar is a
    # keystone -- 180 wide underneath, 145 on top -- overhanging the spur 69
    # left and 22 right, its underside sitting on the spur's run with the run
    # ending 8 units inside it. The bar's height (0.42 C) and thickness
    # (0.8 x the capitals' bar unit) are kept in every option.
    #   a  today: the keystone, cut0 = cut1 = CUT.
    #   b  a PEN-DRAWN bar: both end faces sheared the SAME way (cut0 = CUT,
    #      cut1 = -CUT), so the ends are parallel as a nib leaves them, and
    #      the family's bar modulation (`bar(prof=)`, round 219): the top
    #      edge straight, the underside rising to 0.85 of the thickness at
    #      the free left end, full by 0.7 of the run into the spur.
    #   c  a SMALL WEDGE: the left end square with the I's small rising
    #      wedge on its top corner (0.5 x 0.6 of the family, drop 0 -- the
    #      wedge's face IS the terminal, as on the E's and T's arms), the
    #      right end the pen cut as today.
    #   d  the bar FLOWS OUT OF THE SPUR as one written stroke: a single
    #      centreline down the spur, turning left through a round inner
    #      corner into the bar and running out to the same left end under
    #      the pen's cut, on the pen's own widths scaled so the level run is
    #      the bar's thickness; no right overhang, and the spur's run comes
    #      down flush with the bar's underside so the bottom is one line.
    x0b, x1b = xg - s * 1.1, xg + s * 0.6
    if G_BAR == 'b':
        # ROUND 238. Owner 2026-09-18: "ALBO_ROM_G_BAR b but extend the bar
        # tastefully." b ships, and the bar's free left end runs G_BAR_EXT_L
        # units further into the counter (G_BAR_EXT_R the spur side); 30 / 0
        # is the shipped reading of "tastefully", the ladder 0 / 30 / 60 and
        # 30+15 is on the round-238 page for his correction.
        x0b -= G_BAR_EXT_L; x1b += G_BAR_EXT_R
        b = bar(x0b, x1b, yb + bar_th / 2, bar_th, align='top', cut0=CUT, cut1=-CUT, prof=widths([(0.0, 0.85), (0.7, 1.0), (1.0, 1.0)]))
    elif G_BAR == 'c':
        b = geom.union([bar(x0b, x1b, yb, bar_th, cut1=CUT),
                        wedge((x0b, yb + bar_th / 2), (-1, 0), (0, 1), WL * 0.5, WD * 0.6, 0.0)])
    elif G_BAR == 'd':
        # The spur RISES: the arc ends at 312 degrees on the bowl's underside
        # and the bend climbs to p1, 55 units under the bar's centre, at the
        # cap stem's width. The written stroke takes over exactly there -- the
        # spur's straight run is dropped, the path starts at p1 going up,
        # turns left through a round corner and runs out to the bar's left
        # end -- so the top-right of the junction is the pen's own rounded
        # turn rather than the square corner a bar laid on a spur makes. The
        # width is the pen's, scaled so the vertical run is the cap stem (the
        # spur's own 88) and the level run the bar's 45.
        turn = bar_th * 1.1
        # the path starts 12 units under p1, inside the bend's last 2% of
        # ramp (its width is within 0.3 of the cap stem there): two square
        # faces meeting exactly at p1 left a hairline crack in the union
        path = cubic((xg, p1[1] - 12.0), (xg, yb - turn * 0.45), (xg - turn * 0.45, yb), (xg - turn * 1.6, yb)) + line((xg - turn * 1.6, yb), (x0b, yb))[1:]
        base_b = pen_widths(path); tans_b = tangents(path); nb = len(path) - 1
        def wfn_b(t):
            tn_ = tans_b[min(nb, int(round(t * nb)))]; a = abs(tn_[1]) / (abs(tn_[0]) + abs(tn_[1]))
            return base_b(t) * ((CW / TH_V) * a + (bar_th / TH_H) * (1 - a))
        b = stroke(path, wfn_b, cut1=CUT)
        pts = arc + bend; N = len(pts) - 1; t0 = (len(arc) - 1) / N; t1 = 1.0
        base = bowl_widths(pts)
        body, Lside, _ = stroke(pts, wfn, cut0=math.radians(BEAK_CUT), sides=True)
        lip = _beak_lip(pts, Lside, wfn(0.0), BEAK_CUT)
    else:
        b = bar(x0b, x1b, yb, bar_th, cut0=CUT, cut1=CUT)
    return geom.ink([body, lip, b])

G_BAR = os.environ.get("ALBO_ROM_G_BAR", "b")   # a | b | c | d, see g_G; a is round 232 byte for byte; b ships since round 238 (owner's pick)
G_BAR_EXT_L = float(os.environ.get("ALBO_ROM_G_BAR_EXT_L", 30.0))   # round 238: the bar's left end, units further into the counter
G_BAR_EXT_R = float(os.environ.get("ALBO_ROM_G_BAR_EXT_R", 0.0))

@glyph('H')
def g_H(c):
    C = c["cap"]; x0 = CS / 2; x1 = x0 + W_(c, 'H', 520)
    return geom.ink([cstem(x0, 0, C), cstem(x1, 0, C, top='right'), bar(x0, x1, C * 0.52, CAP_BAR * 0.95)])   # round 94

# ---------------------------------------------------------------- THE I's TOP
# Owner, verbatim: "reduce I top left serif to be more optically symmetrically
# matched to top right."
#
# WHAT THE LETTER IS. `g_I` is one `cstem` with `top='left+'`, and that single
# string is the whole asymmetry: `primitives.stem` reads 'left+' as MAIN on the
# left plus the family's SMALL wedge on the right, and the small one is hard-
# coded at (0.4 length, 0.6 depth, 0.4 drop) of the family's wedge against the
# main one's (1.0, 1.0, 1.0) -- `primitives.stem`, the `small` branch. At the
# shipping stem 66.9 that is 52.32 units of reach on the left against 20.93 on
# the right, a ratio of 2.500 in the drawing before the ink spread rounds
# either apex.  So the two serifs are not near each other and then drifted:
# they are 2.5x apart BY CONSTRUCTION and always have been.
#
# THE DIAL. `ALBO_CAP_I_LSERIF` is the LEFT wedge's length as a fraction of the
# family's wedge -- 1.0 is the drawing as it stands, byte for byte, and 0.4 is
# the RIGHT serif's own number, at which the two wedges are the same wedge and
# the top is symmetric. Depth and drop are carried with it, LINEARLY IN THE
# DIAL, from the main wedge's (1.0, 1.0) at 1.0 to the small wedge's (0.6, 0.4)
# at 0.4 -- so the two ends of the ladder are the two wedges the letter already
# owns and nothing in between is invented. Scaling the length alone was tried
# first and is wrong: the bracket's depth is what seats a wedge on the stem, so
# a 0.4-length wedge still running 104.6 units down the stem is a ramp, not a
# serif of this family.
#
# `ALBO_CAP_I_LSERIF_DEPTH` overrides the depth arm alone (a fraction of the
# family's wedge depth); < 0 means follow the coupling, which is the default.
# It is here because the depth and the reach are what an eye trades off at this
# junction and a one-armed ladder cannot separate them.
#
# SCOPE: this is `g_I`, so it moves the ROMAN I and -- through
# `aldine.a_I` -> `_thin_stem(_CS.g_I, ...)` -- the Aldine italic's I as well.
# Both are inert at the default.
CAP_I_LSERIF = float(os.environ.get("ALBO_CAP_I_LSERIF", 0.55))   # round 373, owner: 0.55
CAP_I_LSERIF_DEPTH = float(os.environ.get("ALBO_CAP_I_LSERIF_DEPTH", -1.0))

# ROUND 373 -- THE RULING, and the RIGHT serif gets a dial too. Owner
# 2026-09-23, on round 370's ladder: *"for I: .55 on left, .45 on right."* So
# the two top wedges are no longer 2.5x apart (1.0 / 0.4) but nearly matched
# (0.55 / 0.45), the left still a shade the larger -- which round 370 measured
# is what clears `VI` (touching at -0.0052 em in the shipped font, +0.0134 at
# 0.55). The right serif was the primitive's hard-coded small wedge; it is
# `stem(small_top=...)` now, and CAP_I_RSERIF is its length on the SAME scale
# and the SAME coupling as the left dial -- so 0.4 is the old small wedge
# exactly and the two dials describe one family of wedges, not two.
CAP_I_RSERIF = float(os.environ.get("ALBO_CAP_I_RSERIF", 0.45))

def _i_wedge_for(L, depth_override=-1.0):
    """(len, depth, drop) for an I top wedge of length L on the family scale:
    linear from the main wedge (1.0, 1.0, 1.0) at 1.0 to the small wedge
    (0.4, 0.6, 0.4) at 0.4."""
    t = (1.0 - L) / 0.6
    depth = depth_override if depth_override >= 0 else 1.0 - 0.4 * t
    return L, depth, 1.0 - 0.6 * t

def _i_right_wedge():
    if CAP_I_RSERIF == 0.4:
        return (0.4, 0.6, 0.4)          # the primitive's own literals: bit-identical
    return _i_wedge_for(CAP_I_RSERIF)

def _i_left_wedge():
    """(top_len, top_depth, top_drop) for the I's LEFT top wedge, keyed on the
    dial. t = 0 at the dial's 1.0 (the main wedge) and 1 at its 0.4 (the small
    wedge the right side already carries)."""
    L = CAP_I_LSERIF
    t = (1.0 - L) / 0.6
    depth = CAP_I_LSERIF_DEPTH if CAP_I_LSERIF_DEPTH >= 0 else 1.0 - 0.4 * t
    return L, depth, 1.0 - 0.6 * t

@glyph('I')
def g_I(c):
    L_, D_, dr_ = _i_left_wedge()
    return geom.ink([cstem(CS / 2, 0, c["cap"], top='left+', top_len=L_, top_depth=D_, top_drop=dr_,
                           small_top=_i_right_wedge())])

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
    blend = lambda t: (CW if t < 0.1 else (base(t) if t > 0.45 else CW + (base(t) - CW) * (3 * ((t - 0.1) / 0.35) ** 2 - 2 * ((t - 0.1) / 0.35) ** 3)))
    # ROUND 275 -- THE HOOK'S END IS THE c's TOP FINIAL. Owner 2026-09-19:
    # "change out round finials (like c top serif)." The hook flared 1.3 over
    # its last 35% into the 20-degree cut -- 84.8 wide at the 400, a teardrop
    # at the lower left. Now the family's finial (PR.finial_widths /
    # PR.finial_cut): the swell to 1.10 over the last 13% (71.8) and the face
    # sheared 28 degrees toward the vertical, the inner corner forward. The
    # top is the I's wedge and is not a finial.
    # ROUND 276: the ITALIC too (owner, on the italic cent page: "that italic
    # has round finials that needs to replaced along with others") -- its
    # branch kept the 1.3 flare into the cut for one round (86.7 wide at the
    # Italic 400, the last teardrop in the family) and is gone.
    return geom.ink([st, stroke(tail, PR.finial_widths(blend, False), cut1=PR.finial_cut(tail, False))])

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
L_TOP = os.environ.get("ALBO_ROM_L_TOP", "a")   # round 241: a | b | c | d | e, see g_L; a is today byte for byte
if L_TOP not in ('a', 'b', 'c', 'd', 'e'): L_TOP = 'a'

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
        # ROUND 241 -- OPTIONS. Owner 2026-09-18: "give me options for
        # lightening L top serif". ALBO_ROM_L_TOP picks; a is today. The left
        # wedge's length (x L_TOP_LEFT), its depth and drop, and the small
        # right wedge scale together or apart:
        #   a  today: left 0.96 x WL, depth 1.0, drop 1.0; right 0.45 / 0.66 / 0.45
        #   b  both a shade lighter: left 0.85, depth 0.85; right 0.38 / 0.56
        #   c  lighter still: left 0.75, depth 0.75, drop 0.8; right 0.32 / 0.50
        #   d  the left wedge only, lightened to c; the right micro-serif as today
        #   e  the right micro-serif dropped, the left wedge as today (the I's own top, one-sided)
        lt = {'a': (L_TOP_LEFT, 1.0, 1.0), 'b': (0.85, 0.85, 1.0), 'c': (0.75, 0.75, 0.8), 'd': (0.75, 0.75, 0.8), 'e': (L_TOP_LEFT, 1.0, 1.0)}[L_TOP]
        rt = {'a': (L_TOP_RIGHT, L_TOP_RIGHT_DEPTH), 'b': (0.38, 0.56), 'c': (0.32, 0.50), 'd': (L_TOP_RIGHT, L_TOP_RIGHT_DEPTH), 'e': (0.0, 0.0)}[L_TOP]
        st = cstem(x, 0, C, top='left', foot='left', top_len=lt[0], top_depth=lt[1], top_drop=lt[2])
        cap_w = TH_V * CAP_STEM
        def _wid(y): return cap_w * (1.0 + ENT * (2 * y / C - 1) ** 4)
        top_right = wedge((x + _wid(C) / 2, C), (0, 1), (1, 0), WL * rt[0], WD * rt[1], DROP * L_TOP_RIGHT_DROP,
                           edge_at=lambda d: (x + _wid(C - d) / 2, C - d)) if rt[0] > 0 else geom.poly([(x, 0), (x, 1), (x + 1, 0)])
        parts = [st, top_right]
    else:
        parts = [cstem(x, 0, C, top='left+', foot='left')]
    if FIX_ROM:
        # R07, owner 2026-09-18: "use the same treatment as B D and other
        # similar joints" at the inside corner. The stem's right side carries
        # the family's foot entasis although there is no foot wedge on that
        # side (`foot='left'`), so its edge flared 2.3 units outward over the
        # last 100 units above the arm and met the arm's flat top as a
        # 1.7-degree angle. The flare is clipped back to the stem's mid width
        # between the arm's top (y = CAP_BAR, the bar's own top edge) and the
        # stem's waist at C/2, where the entasis is exactly zero, so the edge
        # runs straight down into the arm's top and the corner is square. The
        # flare below the arm's top is inside the bar and stays; the left
        # side, the foot, the top wedges and the bar are untouched.
        # ROUND 239 -- THE FLARE COMES BACK. Owner 2026-09-18, on the round-235
        # page: "R07 should tuck inside slightly like other interior corners
        # do." The E's bottom inside corner carries exactly this flare (the
        # stem's edge running 2 units toward the arm over its last 40, seen at
        # 6 px/unit), so the square clip was the odd one out. L_CORNER_CLIP
        # keeps round 235's cut for the record; the L is round 232's again.
        if L_CORNER_CLIP:
            from shapely.geometry import box as _box
            parts[0] = parts[0].difference(_box(x + CW / 2, CAP_BAR, x + CW / 2 + 40.0, C / 2))
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
    if not FIX_ROM or not M_SPURS:
        return geom.ink([a, b, d, e, apex])
    # ROUND 240. Owner 2026-09-18, on round 235's M: "the topmost vertices
    # should stay where they are, extend serif from those. keep the strokes as
    # they are but address errant spurs." So round 232's four strokes and crown
    # are drawn exactly as they were, and three things are done to the union:
    #  * LEFT APEX: the crown's top edge is carried in ONE line from its tip to
    #    the thick stroke's topmost face corner (the peak that stays), which
    #    fills the 4.5-unit step where the wedge's top met the thin stroke's
    #    flat -- a triangle tip/peak/seat added.
    #  * RIGHT TOP: the thin diagonal's cut corner stood 10 units above the
    #    thick stem's top face (the spike); everything above that face's line
    #    across the face's own span is cut away. The face, its corners and the
    #    wedge on its right are untouched.
    #  * MIDDLE VERTEX: the thin stroke's lower corner stands 13 units right of
    #    the thick stroke's right edge ("small overlapping triangle on right");
    #    the part of it beyond that edge, below where the two edges cross, is
    #    cut away. The two prongs and the notch between them at the baseline
    #    are the strokes as they are, and stay.
    from shapely.geometry import Polygon as _Poly
    def _corners(p0, p1, wgt, at_end):
        tn = tangents(line(p0, p1))[0]; n = (-tn[1], tn[0]); P_ = p1 if at_end else p0
        return (P_[0] + n[0] * wgt / 2, P_[1] + n[1] * wgt / 2), (P_[0] - n[0] * wgt / 2, P_[1] - n[1] * wgt / 2)
    def _side(p, dvec, sign, span=1500.0):
        """The half-plane on `sign` side (+1 left of travel) of the line through p along dvec."""
        n = (-dvec[1] * sign, dvec[0] * sign)
        return _Poly([(p[0] - dvec[0] * span, p[1] - dvec[1] * span), (p[0] + dvec[0] * span, p[1] + dvec[1] * span),
                      (p[0] + dvec[0] * span + n[0] * span, p[1] + dvec[1] * span + n[1] * span),
                      (p[0] - dvec[0] * span + n[0] * span, p[1] - dvec[1] * span + n[1] * span)])
    from shapely.geometry import box as _box
    wa, wb, wd, we = [pw(p0, p1, m) for p0, p1, m, _, _ in P]
    # LEFT APEX: the crown's tip to the thick stroke's peak in one line -- fill under it, trim over it
    peak = max(_corners(P[1][0], P[1][1], wb, False), key=lambda q: q[1])
    seat = (x0 + s * 0.45 - wa * 0.35, C); tip = (seat[0] - WL * 0.9, C - DROP)
    fill = _Poly([tip, peak, (seat[0], seat[1] - 40.0)])
    ldir = (peak[0] - tip[0], peak[1] - tip[1]); Ll = math.hypot(*ldir); ldir = (ldir[0] / Ll, ldir[1] / Ll)
    lip = geom.union([a, apex]).intersection(_side(tip, ldir, +1)).intersection(_box(tip[0], C - 60.0, peak[0], C + 80.0))   # round 243: the crown's own corner at (seat, C) stood a unit over the line too
    if M_TOP_MIRROR:
        # ROUND 272 -- the trim overshoots its line by a third of a unit: a cut
        # whose boundary is exactly the fill's top edge left a zero-width strip
        # that the build's ink spread inflated into a 26 x 2.4 sliver on the
        # cap line at the 700 (owner: "shards and glitches").
        lip = lip.buffer(0.34, join_style=2)
    # RIGHT TOP: what the thin stroke d stands above the thick stem e's end face
    eA, eB = _corners(P[3][0], P[3][1], we, True)
    lo, hi = (eA, eB) if eA[0] < eB[0] else (eB, eA)
    fdir = (hi[0] - lo[0], hi[1] - lo[1]); Lf = math.hypot(*fdir); fdir = (fdir[0] / Lf, fdir[1] / Lf)
    spike = d.intersection(_side(lo, fdir, +1)).intersection(_box(lo[0] - 60.0, C - 60.0, hi[0], C + 80.0))
    # ROUND 243. Owner: "make the right top serif of M match the left better".
    # The right top carried the diagonal-end wedge (0.9 x 0.9, hanging off the
    # square face's corner); it takes the LEFT crown's construction now,
    # mirrored: the family's wedge (WL 0.9, WD, DROP) seated at the thick
    # stem's top-right corner pointing right, its top edge carried in one line
    # from the wedge's tip to the face's high corner, the same fill.
    if M_RIGHT_CROWN:
        e = diagonal(P[3][0], P[3][1], we, serif0=1)                        # the foot wedge only
        rseat = hi; rtip = (rseat[0] + WL * 0.9, C - DROP)
        rcrown = wedge(rseat, (0, 1), (1, 0), WL * 0.9, WD, DROP)
        rpeak = max((lo, hi), key=lambda q: q[1])
        rfill = _Poly([rtip, rpeak, (rseat[0], rseat[1] - 40.0)])
        rdir = (rpeak[0] - rtip[0], rpeak[1] - rtip[1]); Lr = math.hypot(*rdir); rdir = (rdir[0] / Lr, rdir[1] / Lr)
        rlip = geom.union([e, rcrown]).intersection(_side(rtip, rdir, -1)).intersection(_box(rpeak[0], C - 60.0, rtip[0], C + 80.0))
    else:
        rcrown = rfill = rlip = geom.poly([(0, 0), (0, 1), (1, 0)])
    # MIDDLE VERTEX: the thin stroke d's lower corner past the thick stroke b's right edge, below their crossing
    # the poking corner is the piece of d OUTSIDE b that touches the baseline
    # region -- d minus b falls into d's body above the crossing and this
    # small corner below it; taking the component by position (its top under
    # y 60) needs no analytic crossing, which the resampled edges miss by a
    # unit or two (an 8-unit box left a 3-unit tooth).
    # ... and it is the THICK stroke's corner standing past the thin one's
    # right edge (13 units), not the thin stroke's: b minus d, the small
    # piece near the baseline. The thin stroke's own prong stays.
    rest = b.difference(d); pieces = list(rest.geoms) if hasattr(rest, 'geoms') else [rest]
    tri = geom.union([q for q in pieces if q.bounds[3] < 60.0 and q.area < 800.0])
    # ROUND 243. Owner: "remove the odd corners sticking out of middle bottom
    # join (match V better)". The V's vertex is one point -- the thick
    # stroke's cut tip, the thin stroke's face running into its edge. So the
    # thin stroke's own prong (d outside b, near the baseline) goes too.
    if M_VERTEX_V:
        rest2 = d.difference(b); p2 = list(rest2.geoms) if hasattr(rest2, 'geoms') else [rest2]
        tri = geom.union([tri] + [q for q in p2 if q.bounds[3] < 60.0 and q.area < 800.0])
    if M_TOP_MIRROR:
        # THE LEFT'S RECIPE ON THE RIGHT'S OWN STROKES. The wedge projects
        # past the thick stem's outer edge by exactly what the left wedge
        # projects past the thin stroke's; the point stands on the thin inner
        # stroke's inner edge carried up, as the left's stands on the thick
        # one's; the fill and the trim are the same shapes. (Mirroring the
        # left's ink was tried first and dragged a chunk of the thick inner
        # stroke onto the thin one -- a shelf on the inside of the junction.)
        a_out = min(_corners(P[0][0], P[0][1], wa, True), key=lambda q: q[0])   # the thin outer stroke's outer top corner
        proj = a_out[0] - tip[0]
        e_out = max(_corners(P[3][0], P[3][1], we, True), key=lambda q: q[0])   # the thick outer stem's outer top corner
        rtip = (e_out[0] + proj, C - DROP); rseat = (rtip[0] - WL * 0.9, C)
        rcrown = wedge(rseat, (0, 1), (1, 0), WL * 0.9, WD, DROP)
        e = diagonal(P[3][0], P[3][1], we, serif0=1)                          # the foot wedge only; the crown is the one above
        d_in = min(_corners(P[2][0], P[2][1], wd, False), key=lambda q: q[0])  # the thin inner stroke's inner (higher) top corner -- the right's peak, as b's inner corner is the left's
        # round 272: the right peak at the LEFT peak's height (adversarial
        # review: the thin stroke's corner stood 5-10 units under the thick
        # stroke's), carried up the thin stroke's inner edge
        _tdu = tangents(line(P[2][1], P[2][0]))[0]                            # d's axis, pointing up
        rpoint = (d_in[0] + _tdu[0] * (peak[1] - d_in[1]) / _tdu[1], peak[1]) if peak[1] > d_in[1] else d_in
        rfill = _Poly([rtip, rpoint, d_in, (rseat[0], rseat[1] - 40.0)])
        rdir = (rpoint[0] - rtip[0], rpoint[1] - rtip[1]); Lr = math.hypot(*rdir); rdir = (rdir[0] / Lr, rdir[1] / Lr)
        rlip = geom.union([e, d, rcrown]).intersection(_side(rtip, rdir, -1)).intersection(_box(rpoint[0] - 60.0, C - 60.0, rtip[0] + 10.0, C + 200.0)).buffer(0.34, join_style=2)
        # THE THICK STEM'S INNER SHOULDER. Both strokes' tops are centred on
        # the same point, so the thick outer stem's inner top corner stands
        # out past the thin inner stroke's edge -- 30 units at the 900 -- on
        # the INSIDE of the junction, where on the left it is the thick
        # stroke's own edge that runs up to the peak and nothing shoulders
        # it. So the inside of the right junction is the thin stroke's inner
        # edge, carried up to the peak: the stem's ink left of that edge line,
        # above where the two edges cross, is cut.
        # ROUND 272 -- the line is the stroke's AXIS direction through the
        # corner, which is its inner edge. The first cut ran from the corner
        # to the axis's own end at the vertex, a line that converges into the
        # stroke, so it shaved a wedge off the diagonal's inside down to the
        # box's floor at C - 200 and left a step there at every weight
        # (owner: "the inside of the diagonal right stroke of M has a
        # fracture").
        _td = tangents(line(P[2][0], P[2][1]))[0]                             # d's axis, pointing down
        # the cut is the half-plane and a box, NOT intersected with the stem
        # first: a cut whose boundary is the stem's own face leaves a
        # zero-area loop in the difference, which the build's ink spread then
        # inflates into a 2.4-unit sliver along the face (seen at the 900).
        # The line is set half a unit into the cut side so the thin stroke's
        # own edge, which it runs along, is never on the boundary.
        _nl = (_td[1] * 0.5, -_td[0] * 0.5)                                   # half a unit to the left of the line
        shoulder = _side((rpoint[0] + _nl[0], rpoint[1] + _nl[1]), _td, -1).intersection(
            _box(rpoint[0] - 80.0, C - 300.0, rpoint[0] + 1.0, C + 200.0))
        g = geom.ink([a, b, d, e, apex, fill, rcrown, rfill])
        return g.difference(geom.union([lip, tri, rlip, shoulder]))          # no spike trim: the thin stroke's corner is the peak
    g = geom.ink([a, b, d, e, apex, fill, rcrown, rfill])
    return g.difference(geom.union([lip, spike, tri, rlip]))

@glyph('N')
def g_N(c):
    C = c["cap"]; s = CS; w = W_(c, 'N', 560); x0 = s / 2; x1 = x0 + w
    d0, d1 = (x0 + s * 0.1, C - s * 0.3), (x1 - s * 0.1, s * 0.3)
    # R11, owner 2026-09-18: "add a microserif on left inside of top right
    # stem" -- the stem primitive's 'right+' top, the same small inward wedge
    # (0.4 x 0.6 of the family at 0.4 drop) the I and the U's right stem
    # carry. The diagonal arrives at that stem 0.3 stems above the baseline,
    # nowhere near the top; nothing else on the letter moves.
    return geom.ink([cstem(x0, 0, C, top='left', foot='both', w=THIN), diagonal(d0, d1, pw(d0, d1)),
                     cstem(x1, 0, C, top='right+' if FIX_ROM else 'right', foot=None, w=THIN)])

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

# ROUND 281 -- THE TAIL SWEEPS UNDER THE MARKS. Owner 2026-09-19, choosing
# among three readings of what the Q and a following , ; . need: "Tail under
# the marks" -- the marks sit on the baseline right after the bowl and the
# tail passes BELOW them; nothing is spaced apart. (A kern was tried the same
# day as round 280 and withdrawn: "you misunderstood the need entirely".)
#
# What the built fonts measured before this: the tail already dips under the
# marks at every weight, and the CLEARANCE between its upper edge and the
# comma's lowest point, over the comma's own footprint, was 136 units at the
# 400, 59 at the 700 and 10 at the 900 -- the comma descends with the weight
# (-81 / -139 / -176) and the tail thickens, so at 13 px on the reader (77
# units to the pixel) the comma and the tail merge into one blob at the 700
# and the 900 while the 400 keeps two pixel rows of white. Q_CLEAR is the
# least clearance, in units, above stem 84; the tail's control points are
# scaled in y about the baseline until the clearance is met, so the tail
# leaves the ring where it always did and reaches the same x, and only
# deepens. The 400 and the 200 are untouched (deep = 1.0 exactly).
Q_CLEAR = float(os.environ.get("ALBO_ROM_Q_CLEAR", 0.0))   # least clearance under the marks above stem 84, design units; 0 = the tail as drawn
Q_MARK_GAP = 114.0   # the ring's right edge to the following comma's first ink: the Q's rsb (36-37) + the comma's lsb (78), measured off the built 400 / 700 / 900, 2026-09-19

def q_tail_deep(c, solid, tail_for):
    """The y-scale for the Q's tail control points (see Q_CLEAR): 1.0 unless
    above stem 84 with a clearance asked for, else the least scale in [1, 2]
    that puts the tail's upper edge Q_CLEAR under the comma's lowest point
    over the comma's footprint after the Q. Measured on the raw stroke; both
    inks take the build's 1.2 spread, so 2.4 is added to the ask."""
    if not (S > 84.0 and Q_CLEAR > 0.0): return 1.0
    from shapely.geometry import box
    from . import GLYPHS
    cb = GLYPHS[','](c).bounds
    x0 = solid.bounds[2] + Q_MARK_GAP; x1 = x0 + (cb[2] - cb[0]); ymin = cb[1]
    need = Q_CLEAR + 2 * 1.2
    def clear(deep):
        tail_, wfn_ = tail_for(deep); under = stroke(tail_, wfn_, cut1=CUT).intersection(box(x0, -2000, x1, -1.0))
        return (ymin - under.bounds[3]) if not under.is_empty else 1e9
    if clear(1.0) >= need: return 1.0
    lo, hi = 1.0, 2.0
    if clear(hi) < need: return hi
    for _ in range(14):
        mid = (lo + hi) / 2
        if clear(mid) >= need: hi = mid
        else: lo = mid
    return hi

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
    def _tail_for(deep):
        # ROUND 281 (q_tail_deep below): the control points' y scaled about
        # the baseline by `deep` -- p0 stays on the ring, the tip's x stays --
        # 1.0 at and below the 400 (byte-identical), the solved number above.
        tp_ = tp if deep == 1.0 else [(x, y * deep) for x, y in tp]
        tail_ = cubic(p0, *tp_)
        base_ = pen_widths(tail_)
        def wfn_(t):
            # THE BELLY SCALES WITH THE TAIL. It is an ABSOLUTE -- 1.05 stems, 100
            # units -- and the header note above already records what an absolute
            # did to this letter once: the solved Q (width x 0.70) got the bulge at
            # full size on a smaller ring, which is the bulge the owner asked to
            # lose. A shortened tail carrying the same 100 units is the same fault
            # again, so the floor travels with the reach; at Q_TAIL 1.0 the
            # expression is the original one multiplied by exactly 1.0.
            belly = max(0.0, 1 - abs(t - 0.45) / 0.4)
            return max(base_(t), s * 1.05 * Q_TAIL * (3 * belly * belly - 2 * belly ** 3)) * widths([(0.0, 0.6), (0.12, 1.0), (0.8, 1.0), (1.0, 0.7)])(t)
        if FIX_ROM and Q_TAIL_OPT != 'a':
            # R12, owner 2026-09-18: "give me more options that are less
            # distracting with the bulge placement and size." The tail's path,
            # its ruled reach (Q_TAIL, "tail long") and the end profile are the
            # same in every option; only the belly -- the `max(pen, belly)` floor
            # that a smoothstep hump lays over the pen's own widths -- moves.
            # Measured on today's tail (option a): the pen alone runs 74 at the
            # root, 66 at 0.4, 54 at 0.6, 28 at 0.8; the belly lifts that to 100
            # at t 0.45 (peak 1.05 stems, half-width 0.4 of the run).
            #   a  today: peak 1.05 CS at t 0.45, half-width 0.40.
            #   b  belly SMALLER: peak 0.85 CS (81 units) at the same place.
            #   c  belly NEARER THE BOWL: peak 1.05 CS at t 0.30, half-width 0.30,
            #      so the swell sits under the ring and the run out is the pen's.
            #   d  an EVEN TAPER, no belly: the pen at its own angle with the
            #      family's tail floor (0.55 S, the 6's and 9's) -- 74 at the root
            #      thinning to the floor and the cut, which is what the header
            #      note above this glyph describes.
            #   e  belly LATER: peak 1.05 CS at t 0.60, half-width 0.35.
            peak, at, hw = {'b': (0.85, 0.45, 0.40), 'c': (1.05, 0.30, 0.30), 'd': (0.0, 0.45, 0.40), 'e': (1.05, 0.60, 0.35)}[Q_TAIL_OPT]
            endp = widths([(0.0, 0.6), (0.12, 1.0), (0.8, 1.0), (1.0, 0.7)])
            def wfn_(t):
                belly = max(0.0, 1 - abs(t - at) / hw)
                floor = s * peak * Q_TAIL * (3 * belly * belly - 2 * belly ** 3) if peak else S * Q_TAIL_FLOOR
                return max(base_(t), floor) * endp(t)
        return tail_, wfn_
    tail, wfn = _tail_for(q_tail_deep(c, solid, _tail_for))
    return geom.ink([solid, stroke(tail, wfn, cut1=CUT)])

Q_TAIL_OPT = os.environ.get("ALBO_ROM_Q_TAIL_OPT", "d")   # a | b | c | d | e, see g_Q; a is round 232 byte for byte; d ships since round 240 (owner's pick)
if Q_TAIL_OPT not in ("a", "b", "c", "d", "e"): Q_TAIL_OPT = "a"   # review 2026-09-18: unknown letters fall back to a

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
    cutouts = []
    if FIX_ROM:
        # R13, owner 2026-09-18: "remove tooth from counter." The leg's
        # start is `CS * 0.15` up its own line from J, and its start face --
        # 37.6 units wide, square to a 60-degree run -- has its upper corner
        # at (240.2, 370.6): 7.6 units above the counter floor (363), an
        # 18-unit-wide tooth standing up from the bowl's inner edge. The
        # leg is clipped by the counter's air (the polygon of the bowl's own
        # inner side, `L`), so the floor is the bowl's one edge again. The
        # leg's path, widths, spring and tip do not move; the alternative --
        # burying the start 14 units lower on its line -- would have moved
        # the whole cubic by a unit or two.
        cutouts.append(leg.intersection(geom.poly(L)))
    return geom.ink(parts, cutouts)

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
S_SPINE = float(os.environ.get("ALBO_ROM_S_SPINE", 0.87))   # the waist's declared weight, x CS; 0.92 is round 223
S_BOT = float(os.environ.get("ALBO_ROM_S_BOT", 0.16))       # the lower curve's extra, x itself; 0.20 is round 223

# ...AND ITS CROWN AND FOOT STAND OUTSIDE THE ROUND FAMILY'S LINE. Ink top 699
# and bottom -25 against O 690/-15, G 691/-17, C 691/-17: ten units proud at
# each end. Both references put the S's extremes ON the O's -- Times 677.2 for
# both, Georgia 708.5 against 709.5. It is not the beak: the topmost ink sits
# at x 280-314, the crown of the arc, where the beak is away at the top-right
# terminal. The catmull OVERSHOOTS its own second point, so the crown is an
# artefact of the curve rather than a declared overshoot, and the honest lever
# is to pull the two extreme points inside the band by the measured amount.
S_CROWN = float(os.environ.get("ALBO_ROM_S_CROWN", 1.5))    # units the crown and foot come inside the cap band; 0 is round 223

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
S_BOWL = float(os.environ.get("ALBO_ROM_S_BOWL", 0.5))
S_BEAK_TIP = float(os.environ.get("ALBO_ROM_S_BEAK_TIP", 12.0))
S_BAL = os.environ.get("ALBO_ROM_S_BAL", "a")   # round 242: a | b | c | d | e, see g_S; a is today byte for byte
if S_BAL not in ("a", "b", "c", "d", "e"): S_BAL = "a"   # round 237: units of the terminal's point cut off square; 0 is round 235      # 0 = the raw pen (round 223), 1 = the round family's own bowl profile

@glyph('S')
def g_S(c):
    C = c["cap"]; w = W_(c, 'S', 440); o = OVER - TH_H / 2; st = CS
    # ROUND 242 -- OPTIONS. Owner 2026-09-18: "rebalance S so the bottom is
    # optically balanced [with] the top (give me options)". Measured on the
    # spine: the top bowl spans 0.18-0.93 of the width and 0.40 of the cap,
    # the bottom 0.04-0.84 and 0.42, and the bottom stroke carries S_BOT 0.16
    # extra and a 1.30 flare at its end. ALBO_ROM_S_BAL picks; a is today.
    #   b  the bottom bowl narrower: its right extreme 0.84 -> 0.80, the end 0.04 -> 0.07
    #   c  the bottom stroke lighter: S_BOT 0.16 -> 0.08, the end flare 1.30 -> 1.15
    #   d  b and c together
    #   e  the TOP bowl bigger instead: start 0.93 -> 0.96, crown 0.62 -> 0.60, left 0.18 -> 0.15, waist 0.60 -> 0.58
    sb = {'a': (0.84, 0.04, 0.16, S_BOTTOM_END, 0.93, 0.62, 0.18, 0.60), 'b': (0.80, 0.07, 0.16, S_BOTTOM_END, 0.93, 0.62, 0.18, 0.60),
          'c': (0.84, 0.04, 0.08, 1.15, 0.93, 0.62, 0.18, 0.60), 'd': (0.80, 0.07, 0.08, 1.15, 0.93, 0.62, 0.18, 0.60),
          'e': (0.84, 0.04, 0.16, S_BOTTOM_END, 0.96, 0.60, 0.15, 0.58)}[S_BAL]
    bx, ex, s_bot, s_end, tx0, cx_, lx, wy = sb
    spine = catmull([(w * tx0, C * 0.80), (w * cx_, C + o * 0.9 - S_CROWN), (w * lx, C * 0.86), (w * 0.2, C * wy),
                     (w * 0.8, C * 0.42), (w * bx, C * 0.16), (w * 0.42, -o * 0.9 + S_CROWN), (w * ex, C * 0.22)], tension=0.55)
    base = pen_widths(spine)
    if S_BOWL != 0.0:
        _pen, _bowl = base, bowl_widths(spine)
        base = lambda t: _pen(t) * (1.0 - S_BOWL) + _bowl(t) * S_BOWL
    def wfn(t):
        mid = 1.0 - min(1.0, abs(t - 0.5) / 0.28); want = base(t) * (1 - mid) + st * S_SPINE * mid
        bot = max(0.0, 1 - abs(t - 0.74) / 0.22); want *= 1 + s_bot * (3 * bot * bot - 2 * bot ** 3)
        return want * widths([(0.0, 1.3), (0.10, 1.0), (0.86, 1.0), (1.0, s_end)])(t)
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
    if not FIX_ROM:
        body = stroke(spine, wfn, cut0=math.radians(BEAK_CUT))
        return geom.ink([body, beak(spine, wfn(0.0), True, BEAK_CUT)])
    # R14, owner 2026-09-18: "make cohesive and without any kink" -- the
    # same lip as the G's, on the spine's real inner edge (`_beak_lip`): the
    # 6-unit Z-kink two thirds down the terminal was the lip's bracket,
    # built on the tangent line, crossing the spine's real edge where the
    # crown's curve had already left that line; the 3-unit zig on the face
    # was the lip polygon standing 6 sin 28 units behind the sheared face.
    body, Lside, _ = stroke(spine, wfn, cut0=math.radians(BEAK_CUT), sides=True)
    lip = _beak_lip(spine, Lside, wfn(0.0), BEAK_CUT)
    # ROUND 237. Owner 2026-09-18, on the round-235 page: "S beak was not
    # fully corrected." Two things were left: the seat step (fixed in
    # `_beak_lip`) and the tip, a 41-degree needle at the end of a 100-unit
    # face. S_BEAK_TIP units of the point are cut off square to the face.
    if S_BEAK_TIP > 0:
        tn = tangents(spine); d = (-tn[0][0], -tn[0][1]); nl = (-tn[0][1], tn[0][0])
        A = Lside[0]; length = WL * 0.4; drop = -length * math.tan(math.radians(abs(BEAK_CUT)))
        B = (A[0] + nl[0] * length - d[0] * drop, A[1] + nl[1] * length - d[1] * drop)
        return geom.ink([body, lip], [_blunt_tip(A, B, S_BEAK_TIP)])
    return geom.ink([body, lip])

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
    # R15 (see below): the stems ran 30 units down INTO the bowl, and the
    # bowl's cubic has already drifted 1.2 units sideways by the end of that
    # overlap, so a stem at its own width and the bowl at the same width
    # could not both be flush -- the stem's square bottom stood a unit out.
    # The stems now end 2 units into the bowl (drift 0.006), where the
    # bowl's start face, the same width, is flat on the same line.
    yover = 2 if FIX_ROM else 30
    left = cstem(x0, y0 - yover, C, top='left', foot=None, ent_span=(0, C))
    right = cstem(x1, y0 - yover, C, top='right+', foot=None, w=CW * 0.78, ent_span=(0, C))
    yb = -OVER + TH_H / 2; cy = (8 * yb - 2 * y0) / 6
    pts = cubic((x0, y0), (x0, cy), (x1, cy), (x1, y0))
    # round 51: the pen's widths x CAP_STEM(1 - 0.22 t), swelling by the
    # entasis over the first and last 15% to meet the stems' ends
    amt = ENT; base = pen_widths(pts)
    bump = lambda t: 1.0 + amt * (max(0.0, 1 - t / 0.15) + max(0.0, 1 - (1 - t) / 0.15))
    wfn = lambda t: base(t) * CAP_STEM * (1 - 0.22 * t) * bump(t) * widths([(0.0, 0.9), (0.05, 1.0), (0.88, 1.0), (1.0, 0.8)])(t)
    if FIX_ROM:
        # R15, owner 2026-09-18: "correct shitty joins." The bowl's width was
        # to swell "by the entasis over the first and last 15% to meet the
        # stems' ends" -- but both stems are drawn with `ent_span=(0, C)`, a
        # piece of a full-height stem, so at y0 they are at MID width (88.1
        # and 68.7) with no swell to meet. The bump then made the bowl 3.5
        # units wider than the left stem on each side just below the join
        # (the outer edge bulged to x 115 against the stem's 118: the knee)
        # and, with the 0.8 end factor, 6 units NARROWER than the right stem
        # where it arrives, so the right stem's square bottom stood out 3
        # units on both sides at y 253. The bowl now holds each stem's own
        # width across the overlap and eases onto the pen from there: the
        # pen's vertical x CAP_STEM(1 - 0.22 t), which IS 88.1 at t 0 and
        # 68.7 at t 1, so every edge runs straight out of its stem and
        # curves away tangent. The path, the middle of the bowl's weight and
        # both stems are untouched; what moved is the bowl's first and last
        # 15%, which lose the swell that never met anything.
        nat = lambda t: base(t) * CAP_STEM * (1 - 0.22 * t)
        def _ease(u): return 3 * u * u - 2 * u ** 3
        def wfn(t):
            if t < 0.06: k = _ease(max(0.0, (t - 0.03) / 0.03)); return CW * (1 - k) + nat(0.06) * k
            if t > 0.94: k = _ease(max(0.0, (0.97 - t) / 0.03)); return CW * 0.78 * (1 - k) + nat(0.94) * k
            return nat(t)
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
    if not FIX_ROM:
        a, b, d, e = [diagonal(p0, p1, pw(p0, p1, m), serif0=sf) for p0, p1, m, sf in P]
        # owner 2026-09-13: "lower and reduce the protuberance of the top middle
        # connector in W" -- the crown at W_CROWN of the family's wedge, seated
        # W_CROWN_DROP x the family's drop lower
        crown = wedge((apex[0] - pw(P[1][0], P[1][1], 0.72) * 0.35, C - DROP * (W_CROWN_DROP - 1.0)), (0, 1), (-1, 0), WL * W_CROWN, WD * W_CROWN, DROP)
        return geom.ink([a, b, d, e, crown])
    # R16, owner 2026-09-18: "despur entirely." Measured on the built roman:
    # the thin inner stroke's square start face stood 7 units over the cap
    # line and the thick one's 13, with a dip to the line between them (the
    # two peaks and the dip); and the crown was a 20 x 11 SPUR, because its
    # seat was 0.35 of the thin stroke's width in from the apex -- which at
    # this apex is the stroke's CENTRE -- so all but the tip of a 39 x 79
    # wedge was buried in the stroke and a thorn was what came out. The
    # documented fix, applied: both inner strokes cut flat on the cap line
    # (`flat_face`), and the crown seated ON the thin stroke's real left edge
    # at its ruled height (W_CROWN_DROP x the family's drop under the line,
    # round 84) with its bracket following that edge, so the whole of the
    # ruled 0.6 wedge shows and nothing is left standing. Plus what the
    # M taught: the thick stroke's flat face is 24 units wider on the left
    # than the thin stroke's, so its corner is clipped back to the thin
    # stroke's edge line. `crotch_blunt` is NOT applied: the crotch below,
    # measured on the same build, is one clean V at (448.8, 564.8) with a
    # 1.2-unit facet -- the zigzag the comment above describes is gone, and
    # a cut that narrows a clean crotch to 9 degrees would be a change with
    # no fault under it. Widths, angles, the crown's ruled size and drop, the
    # splay and the advance are untouched.
    wa, wb, wd, we = [pw(p0, p1, m) for p0, p1, m, _ in P]
    a = diagonal(P[0][0], P[0][1], wa, serif0=1)
    b = _flat_diag(P[1][0], P[1][1], wb, flat0=True)
    d = _flat_diag(P[2][0], P[2][1], wd, flat0=True)
    e = diagonal(P[3][0], P[3][1], we, serif0=-1)
    tb = tangents(line(P[1][0], P[1][1]))[0]
    bL = flat_corner(P[1][0], P[1][1], wb, -1, False)
    d = d.difference(_left_of(bL, tb, C - 150.0, C + 10.0))
    seat_y = C - DROP * (W_CROWN_DROP - 1.0)
    A = (bL[0] + tb[0] * (seat_y - C) / tb[1], seat_y)          # the thin stroke's left edge at the crown's ruled height
    crown = wedge(A, (0, 1), (-1, 0), WL * W_CROWN, WD * W_CROWN, DROP, edge_at=lambda t: (A[0] + tb[0] * t, A[1] + tb[1] * t))
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
