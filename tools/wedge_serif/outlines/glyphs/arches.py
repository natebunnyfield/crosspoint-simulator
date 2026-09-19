"""n m h u r: the arch family. The arch is drawn from its OUTER edge (the
silhouette) with declared widths toward the counter, read against the pen:
a hairline where it leaves the stem, the pen's horizontal (55) over the
top thinned a little (the garaldes' arch tops run under the o's), the full
stem where it turns down into the right stem. Rulings: the outer edge peaks
at xh + 12; the inner edge leaves the stem at 0.52 xh with a trap notch."""
import math, os
from . import glyph
from .. import geom, pen
from ..geom import cubic, line, join
from ..primitives import stem, stem_edge_x, edge_stroke, widths, stroke, trap, wedge, pen_widths
from .. import primitives as PR
from ..pen import S, XH, ASC, TH_V, TH_H, HAIR, WL, WD, DROP, ENT, CUT, FOOT, adj
from ..primitives import end_wedge

# round 92 (adj 'n'): the shoulder was square -- the arch left the stem high
# (0.52 xh) and its second control point sat ON the right stem, so the
# curve reached full height and dropped vertically; and the join was a
# knot (+6% Albertus). Now it leaves lower, the shoulder's control point
# is pulled in by N_SHOULDER_IN x S so the turn is round, the taper in is a
# little thinner. n h m share this by construction.
N_START_ADJ, N_SHOULDER_IN, N_TAPER_ADJ = 0.46, 0.35, 0.26
# THE JOIN, 2026-09-18 (the owner's roman bump markup, R27 / R29): "I did not
# highlight this, I wanted to slightly reduce the weight of the joins." The
# join is the sliver of arch OUTSIDE the stem between the arch's start and the
# shoulder: measured on the h, the arch's underside left the stem at y 195
# (its own start face) and its outer edge at y 332, and everything between
# those two heights right of the stem's edge was join ink -- 18 units wide at
# y 250, 52 at 332. Two dials, both on the taper the arch is drawn with
# (round 51's taper_in): the start width and how far along the arch it reaches
# full. Thinner and longer keeps the underside against the stem for longer,
# which is where the ink comes out; the shoulder above the taper is untouched.
N_JOIN_TAPER = float(os.environ.get("ALBO_ROM_N_JOIN_TAPER", 0.22))   # the arch's start, x the pen (N_TAPER_ADJ 0.26 until round 232)
N_JOIN_SPAN = float(os.environ.get("ALBO_ROM_N_JOIN_SPAN", 0.38))     # ... reaching full width this far along (0.32 until round 232)
# The arch's START FACE used to POKE OUT of the stem, and the trap sealed it
# into a speck. Measured on the h before this: the centerline began 6 units
# inside the stem's edge with a 19.4-unit start width, so the face's lower
# corner stood 3.7 units OUTSIDE the edge at y 196; the trap (apex ON the
# edge, opening at 65 degrees) cut a V around that corner, and build.py's
# 1.2-unit ink spread then closed the V's mouth -- the outline came back with
# a five-vertex ENCLOSED HOLE of about 3 x 4 units inside the stem's ink at
# (80..84, 197..201), on n, h and m alike. N_START_IN is how far INSIDE the
# edge the face's near corner now sits; the trap is aimed at the real crotch
# instead (below), so nothing is cut where the arch is still buried.
N_START_IN = 2.0

def smooth_widths(center, th, profile=None, floor=0.0):
    """R23, owner 2026-09-18 on the h's arch inner edge: "correct weird thin
    bending." `pen_widths(center)` (and `bowl_widths`) look the tangent up at
    `round(t * (len(center) - 1))` on the centerline's OWN points, while
    `stroke` resamples that centerline to arc-length spacing and asks for
    widths at i / (resampled n): on the arch that is 69 points against 49,
    so the lookup advanced one index, then two, then one, and the width
    stepped 1.3, 2.6, 1.3 units along the edge -- measured on the underside
    as alternating turns of +16 / -5 degrees per 9-unit segment.

    This reads the tangent at the FRACTIONAL index, interpolated between the
    two neighbours, and nothing else changes: the width at a stroke point is
    still the pen at the centerline's parameter-fraction point, which is the
    width the face has shipped with. That matters, and was measured before
    this helper existed: the first fix resampled the centerline so the pen
    was read at the stroke point's own tangent, and through the arch's rise
    -- where the cubic's parameter runs ahead of its arc length and the
    shipped lookup was reading a flatter, thinner pen -- the stroke came out
    58 units wide at y 360..380 against the shipped 38..46, +8% of ink in the
    shoulder, the opposite of R27's ask. `th` is `pen.PEN.th` for a pen stroke
    or `PR.bowl_th` for a bowl one."""
    tans = geom.tangents(center); n = len(center) - 1
    def f(t):
        u = max(0.0, min(1.0, t)) * n; i = min(n - 1, int(u)); fr = u - i
        tx = tans[i][0] * (1 - fr) + tans[i + 1][0] * fr; ty = tans[i][1] * (1 - fr) + tans[i + 1][1] * fr
        m = math.hypot(tx, ty) or 1.0
        w = th((tx / m, ty / m))
        if profile: w *= profile(t)
        return max(w, floor)
    return f

N_TRAP_GAP = 3.0   # the trap's apex sits where the air between the stem's edge and the arch's underside is this wide
# THE ARCH TRAP IS OFF, 2026-09-18 -- a departure from the round-30 ruling
# ("the inner edge leaves the stem ... with a trap notch"), flagged for the
# owner. Three placements were built and looked at on the h, m and n at 3
# px/unit: at the old apex it was the sealed speck above; at the underside's
# first crossing of the edge (y 208 on the h) it was a lone nick 130 units
# below the visible crotch; and at the crotch's own tip (N_TRAP_GAP) it read
# as a small hook on the stem's edge -- the same thing the owner called a
# burr on the r (R31) and asked removed. The crotch these arches now make is
# a 20-degree sliver, not the 65-degree corner the ruling's notch was cut
# for, and the caller's brief for this round (not the owner) ruled a notch
# a defect. THE OWNER HAS NOT RULED ON THIS: a departure to put to him. N_TRAP_DEPTH x S
# restores it (0.05 was round 78's), at the crotch's tip.
N_TRAP_DEPTH = float(os.environ.get("ALBO_ROM_N_TRAP", 0.0))
def arch_geom(x0, x1, xh, ent_span=None, start=0.52, taper=0.30, taper_span=0.32, end_y=0.60):
    if adj('n'): start, taper, taper_span = N_START_ADJ, N_JOIN_TAPER, N_JOIN_SPAN
    sh_in = S * N_SHOULDER_IN if adj('n') else 0.0
    """The arch as the NIB writes it (owner 2026-09-13): a designed
    CENTERLINE -- leaves the left stem's inner edge at `start` x xh
    (ruling 0.52) climbing steeply, peaks so its outer edge lands at
    xh + 12 (ruling), and comes down vertical into the right stem at
    end_y -- offset by pen.th(tangent)/2 at every point: a hairline where
    it runs up along the stress, the pen's horizontal (55) over the top,
    the full stem where it turns down. It thins into the left stem
    (taper_in 0.30 over 32%, round 51's), so its start face lies inside
    the stem's ink. Returns (solid, cutouts, L, R)."""
    w = TH_V; lo, hi = ent_span or (0, xh)
    xl = stem_edge_x(x0, w, ENT, start * xh, lo, hi, +1)
    over_c = pen.ARCH_OVER - TH_H / 2
    yc = (8 * (xh + over_c) - xh * start - xh * end_y) / 6
    c1 = (xl + S * 0.2, yc + xh * 0.005)
    # the start, buried: the face's lower corner sits N_START_IN inside the
    # edge. The start width is the pen at the start tangent x taper, and the
    # tangent depends (weakly) on where the start is, so two passes.
    xs = xl - 6.0
    for _ in range(2):
        dx, dy = c1[0] - xs, c1[1] - xh * start; m = math.hypot(dx, dy); tx, ty = dx / m, dy / m
        w0 = taper * pen.PEN.th((tx, ty))
        xs = xl - N_START_IN - ty * w0 / 2   # the corner is start + (ty, -tx) * w0/2
    center = cubic((xs, xh * start), c1, (x1 - sh_in, yc - xh * 0.005), (x1, xh * end_y))
    base = smooth_widths(center, pen.PEN.th)   # R23: the shipped widths without the sawtooth (see smooth_widths); the u carries the old lookup and is not in the round
    floor = S * PR.BOWL['arch_floor'] if (PR.BOWL and PR.BOWL.get('arch_floor')) else 0.0   # variant D: the arch never thins below the stem (Albertus, measured)
    def wfn(t):
        u = min(1.0, t / taper_span); return max(base(t) * (taper + (1 - taper) * (3 * u * u - 2 * u ** 3)), floor)
    solid, L, R = stroke(center, wfn, sides=True)
    # The join trap (ruling: arches leave the stem with a trap notch). Its
    # apex used to be the raw stem-edge point at `start` -- which is where the
    # arch's centerline begins, not where its underside LEAVES the stem. And
    # "leaves" needs a number: the underside runs up nearly PARALLEL to the
    # edge (the arch sets off at 85 degrees and its width grows by a
    # smoothstep), so it is a fraction of a unit outside the edge for a long
    # way -- on the h it first crosses at y 208 and is only 3 units out by
    # y 300 -- and a notch at the first crossing is a nick in a straight edge
    # again (built and seen, 2026-09-18). The apex is where the sliver of air
    # between edge and underside is N_TRAP_GAP wide, which is where the eye
    # sees the crotch begin; the V opens along the bisector of that air --
    # between straight down the stem's edge and the underside's direction --
    # and the depth stays at 0.05 stem (round 78's re-scaling).
    apex, direction = None, None
    for i in range(1, len(R)):
        px, py = R[i]; ex = stem_edge_x(x0, w, ENT, py, lo, hi, +1)
        if px - ex >= N_TRAP_GAP:
            qx, qy = R[i - 1]; eq = stem_edge_x(x0, w, ENT, qy, lo, hi, +1)
            g0, g1 = qx - eq, px - ex
            u = (N_TRAP_GAP - g0) / (g1 - g0) if g1 != g0 else 0.0
            u = max(0.0, min(1.0, u))
            apex = (eq + (ex - eq) * u, qy + (py - qy) * u)
            ux, uy = px - qx, py - qy; m = math.hypot(ux, uy) or 1.0
            bx, by = ux / m + 0.0, uy / m - 1.0; mb = math.hypot(bx, by) or 1.0
            direction = (bx / mb, by / mb)
            break
    if apex is None:   # the underside never leaves the stem (cannot happen on these arches; keep the old aim rather than crash)
        apex, direction = (xl, start * xh), (math.cos(math.radians(65)), math.sin(math.radians(65)))
    cuts = [trap(apex, direction, 18, S * N_TRAP_DEPTH)] if N_TRAP_DEPTH > 0 else []
    return solid, cuts, L, R

def arch(x0, x1, xh, **kw):
    solid, cuts, L, R = arch_geom(x0, x1, xh, **kw)
    return solid, cuts

@glyph('n')
def g_n(c):
    xh = c["xh"]; x0 = S / 2; x1 = x0 + pen.NW
    left = stem(x0, 0, xh, top='left', foot='both')
    right = stem(x1, 0, 0.66 * xh, top=None, foot='both', ent_span=(0, xh))
    a, cuts = arch(x0, x1, xh)
    return geom.ink([left, right, a], cuts)

@glyph('h')
def g_h(c):
    xh = c["xh"]; x0 = S / 2; x1 = x0 + pen.NW
    left = stem(x0, 0, c["asc"], top='left', foot='both')
    right = stem(x1, 0, 0.66 * xh, top=None, foot='both', ent_span=(0, xh))
    a, cuts = arch(x0, x1, xh, ent_span=(0, xh))
    return geom.ink([left, right, a], cuts)

# R28, owner 2026-09-18, on the feet of the m's 2nd and 3rd stems: "reduce
# the interior serifs slightly and give me options for the middle stem." The
# interior feet are the wedges that point INTO a counter -- both of the middle
# stem's and the right stem's left one; the right stem's right foot faces out
# and is the family's. `stem()` has one foot length for both sides, so a stem
# with unequal feet is built as its body plus one one-footed stem per side.
M_INNER_FOOT = 0.85   # the interior feet, length AND depth x this (the wedge keeps its shape)
# ALBO_ROM_M_MID -- the middle stem's foot, for the owner to pick from:
#   a  both feet, as today (interior, so both reduced by M_INNER_FOOT)
#   b  one foot only, the LEFT (the side the reading eye reaches first)
#   c  no foot: the stem ends square on the baseline
#   d  both feet, shorter still: 0.60 of the family's
M_MID = os.environ.get("ALBO_ROM_M_MID", "d")   # round 247: d ships -- owner 2026-09-18, "ALBO_ROM_M_MID d wins" (both middle feet at 0.60)
if M_MID not in ("a", "b", "c", "d"): M_MID = "a"   # review 2026-09-18: an unknown letter drew a KeyError, not today's m
def _footed(x, top, xh, left_k, right_k):
    """A 0.66-xh stem under an arch with feet of two different sizes (None = no
    foot on that side; 1.0 = the family's foot, FOOT x WL long and WD deep;
    k = that foot scaled by k in both). Its body is stem()'s; the feet are
    stem()'s wedges. Note stem()'s own foot_len default IS FOOT (0.85), so
    the factor multiplies it -- a plain 1.0 there is a 15% LONGER foot (built
    once by mistake: the m's advance grew 857 -> 868)."""
    parts = [stem(x, 0, top, top=None, foot=None, ent_span=(0, xh))]
    if left_k: parts.append(stem(x, 0, top, top=None, foot='left', ent_span=(0, xh), foot_len=FOOT * left_k, foot_depth=left_k))
    if right_k: parts.append(stem(x, 0, top, top=None, foot='right', ent_span=(0, xh), foot_len=FOOT * right_k, foot_depth=right_k))
    return geom.union(parts)

@glyph('m')
def g_m(c):
    xh = c["xh"]; x0 = S / 2; d = pen.NW * 0.88; x1 = x0 + d; x2 = x1 + d
    left = stem(x0, 0, xh, top='left', foot='both')
    k = M_INNER_FOOT
    mid_feet = {'a': (k, k), 'b': (k, None), 'c': (None, None), 'd': (0.60, 0.60)}[M_MID]
    mid = _footed(x1, 0.66 * xh, xh, *mid_feet)   # the references all foot the middle stem; R28 asks for the alternatives
    right = _footed(x2, 0.66 * xh, xh, k, 1.0)
    a1, c1 = arch(x0, x1, xh); a2, c2 = arch(x1, x2, xh)
    return geom.ink([left, mid, right, a1, a2], c1 + c2)

@glyph('u')
def g_u(c):
    """Round 51's u on the nib: the left stem runs into a bowl whose
    centerline is a cubic solved to bottom out at the rounds' overshoot,
    the pen's widths along it thinning (taper_out 0.42 over 30%) into the
    right stem; left stem top wedge, right stem top wedge and right foot."""
    xh = c["xh"]; x0 = S / 2; x1 = x0 + pen.NW
    over_c = pen.OVER - TH_H / 2
    left = stem(x0, 0.40 * xh - 30, xh, top='left', foot=None, ent_span=(0, xh))
    cy = (8 * (-over_c) - xh * 0.4 - xh * 0.42) / 6
    center = cubic((x0, xh * 0.4), (x0, cy), (x1, cy), (x1 + 4, xh * 0.42))
    base = pen_widths(center)
    floor = S * PR.BOWL['arch_floor'] if (PR.BOWL and PR.BOWL.get('arch_floor')) else 0.0
    u_end = 0.70 if adj('u') else 0.58   # round 92 (adj 'u'): light (band -11%) -- the bowl holds more weight into the right stem, the right top wedge a little shorter
    wfn = lambda t: max(base(t) * (1.0 if t < 0.7 else (u_end + (1 - u_end) * (1 - (3 * ((t - 0.7) / 0.3) ** 2 - 2 * ((t - 0.7) / 0.3) ** 3)))), floor)
    bowl = stroke(center, wfn)
    right = stem(x1, 0, xh, top='left', foot='right', top_len=(0.85 if adj('u') else 1.0))
    return geom.ink([left, right, bowl])

@glyph('r')
def g_r(c):
    """Round 51's r on the nib: the arm leaves the stem at 0.6 xh and
    climbs to the arch overshoot, the pen's widths with a floor of 0.78
    stem (round 36: the nib alone makes a 33-unit hairline of a stroke at
    the arm's angle), thinning into the stem (taper 0.5 over 35%) and
    flaring 0.5 into the family's pen cut."""
    xh = c["xh"]; x0 = S / 2; wf = c["wf"]
    # round 92 (adj 'r'): the arm was a knob on a short stem -- it flared 1.5
    # into the cut (a swell, not a serif) and sat high; the join trap still
    # carried the old 0.22 depth that nicks the crotch (the arches went to
    # 0.05 in round 78). Now: the arm leaves a hair lower, ends at 1.05 with
    # a plain pen cut (no wedge: tried, a horn), trap 0.05, feet 0.85.
    r_on = adj('r')
    st = stem(x0, 0, xh, top='left', foot='both', foot_len=(FOOT_R if r_on else 1.0))
    over_c = pen.ARCH_OVER - TH_H / 2
    # round 94 (owner: "reduce 'r' slightly so it fits with the rest of the chars"): the arm's reach 205 -> R_REACH wf, its floor 0.78 -> R_FLOOR S, its flare 1.5 -> R_FLARE
    # round 101: an italic BRANCHES -- the arm leaves the stem low and climbs,
    # instead of turning off a roman shoulder near the top. IT_BRANCH slides
    # between the two; at 1 the arm starts at 0.22 xh, which is what the
    # reference italics do and what a sheared roman cannot.
    # GATED at round 111 with the o's IT_OVAL, and for the same reason: written
    # ungated at round 101, it slid the ROMAN r's arm from 0.56 of the x-height
    # down to 0.509 and moved its control point with it.
    _b = pen.IT_BRANCH if pen.ITALIC else 0.0
    _start = xh * ((0.56 if r_on else 0.6) * (1 - _b) + 0.22 * _b)
    center = cubic((x0, _start), (x0, xh * (1.0 - 0.10 * _b)), (x0 + 120 * wf * R_REACH / 205, xh + over_c + 6), (x0 + R_REACH * wf, xh * 0.9))
    r_floor, r_flare = R_FLOOR, R_FLARE
    if not pen.ITALIC: r_floor, r_flare = R_THIN_OPTS[R_THIN]   # R31's options; 'a' is these same numbers
    base = (smooth_widths(center, pen.PEN.th, floor=S * r_floor) if not pen.ITALIC   # the arch's sawtooth fix (smooth_widths, R23), the same lookup on this arm
            else pen_widths(center, floor=S * r_floor))
    prof = widths([(0.0, 0.5), (0.35, 1.0), (0.55, 1.0), (1.0, 1.05)]) if r_on else widths([(0.0, 0.5), (0.35, 1.0), (0.55, 1.0), (1.0, r_flare)])
    wfn = lambda t: base(t) * prof(t)
    arm = stroke(center, wfn, cut1=CUT)
    # (a family end wedge was tried on the arm's tip and stood up like a horn -- the plain cut it is)
    if pen.ITALIC:
        xl = stem_edge_x(x0, TH_V, ENT, 0.52 * xh, 0, xh, +1)
        cut = trap((xl, 0.52 * xh), (math.cos(math.radians(65)), math.sin(math.radians(65))), 18, S * (0.05 if r_on else 0.22))
        return geom.ink([st, arm], [cut])
    # R31, owner 2026-09-18: "THIS IS NOT WHAT I HIGHLIGHTED. remove burr on
    # right side of stem." The burr was the join trap. It was aimed at (stem
    # edge, 0.52 xh) as if the arm left the stem there; but the arm starts
    # 30 units wide ON the stem's centerline, entirely inside a 78-unit stem,
    # and its underside only clears the stem's right edge at y 331 (0.77 xh)
    # -- measured -- so the 0.22-stem trap (the roman r is not in ADJ, so it
    # never took round 92's 0.05) cut a 7.4-unit-deep, 40-unit-tall nick into
    # plain stem edge between y 206 and 249, eighty units below the real
    # crotch, with nothing on either side of it. Removed rather than re-aimed:
    # the arm's underside meets the stem in a smooth 25-degree crotch and
    # there is no ruling asking the r for a notch there.
    return geom.ink([st, arm])
FOOT_R = 0.85   # round 92: the r's feet, x the family's foot length
R_REACH, R_FLOOR, R_FLARE = 190, 0.72, 1.35   # round 94: was 205, 0.78, 1.5
# ALBO_ROM_R_THIN -- R31, owner 2026-09-18: "give me options for thinning out
# the right side for word image legibility." The right side is the arm: its
# floor (round 36: the nib alone makes a 33-unit hairline at the arm's angle,
# so the arm rides a floor x the stem) and its flare into the cut.
#   a  today: floor 0.72, flare 1.35
#   b  the arm thinner: floor 0.60, the flare as today
#   c  thinner and less swell at the tip: floor 0.60, flare 1.15
R_THIN = os.environ.get("ALBO_ROM_R_THIN", "a")
if R_THIN not in ("a", "b", "c"): R_THIN = "a"   # review 2026-09-18: unknown letters fall back to today's r
R_THIN_OPTS = {'a': (R_FLOOR, R_FLARE), 'b': (0.60, R_FLARE), 'c': (0.60, 1.15)}
