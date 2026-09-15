"""n m h u r: the arch family. The arch is drawn from its OUTER edge (the
silhouette) with declared widths toward the counter, read against the pen:
a hairline where it leaves the stem, the pen's horizontal (55) over the
top thinned a little (the garaldes' arch tops run under the o's), the full
stem where it turns down into the right stem. Rulings: the outer edge peaks
at xh + 12; the inner edge leaves the stem at 0.52 xh with a trap notch."""
import math
from . import glyph
from .. import geom, pen
from ..geom import cubic, line, join
from ..primitives import stem, stem_edge_x, edge_stroke, widths, stroke, trap, wedge, pen_widths
from .. import primitives as PR
from ..pen import S, XH, ASC, TH_V, TH_H, HAIR, WL, WD, DROP, ENT, CUT, adj
from ..primitives import end_wedge

# round 92 (adj 'n'): the shoulder was square -- the arch left the stem high
# (0.52 xh) and its second control point sat ON the right stem, so the
# curve reached full height and dropped vertically; and the join was a
# knot (+6% Albertus). Now it leaves lower, the shoulder's control point
# is pulled in by N_SHOULDER_IN x S so the turn is round, the taper in is a
# little thinner. n h m share this by construction.
N_START_ADJ, N_SHOULDER_IN, N_TAPER_ADJ = 0.46, 0.35, 0.26
def arch_geom(x0, x1, xh, ent_span=None, start=0.52, taper=0.30, taper_span=0.32, end_y=0.60):
    if adj('n'): start, taper = N_START_ADJ, N_TAPER_ADJ
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
    center = cubic((xl - 6, xh * start), (xl + S * 0.2, yc + xh * 0.005), (x1 - sh_in, yc - xh * 0.005), (x1, xh * end_y))
    base = pen_widths(center)
    floor = S * PR.BOWL['arch_floor'] if (PR.BOWL and PR.BOWL.get('arch_floor')) else 0.0   # variant D: the arch never thins below the stem (Albertus, measured)
    def wfn(t):
        u = min(1.0, t / taper_span); return max(base(t) * (taper + (1 - taper) * (3 * u * u - 2 * u ** 3)), floor)
    solid, L, R = stroke(center, wfn, sides=True)
    # The join trap (ruling: arches leave the stem with a trap notch,
    # 0.22 stem deep) was cutting from the RAW stem-edge point down into
    # plain stem ink -- at 65 deg its tip lands 0.20 xh below the join, well
    # under the actual (buried, tapered) corner where the arch's near edge
    # departs the stem, so it sliced a deep gouge through the thin taper
    # region instead of nicking the crotch (visible as a lightning-bolt nick
    # at 600 px in n m h, found 2026-09-13). The real corner the union forms
    # here is a ~5-unit step, so the trap is re-scaled to match it: same
    # apex and 65 deg direction (still the crotch's ruled corner), depth cut
    # to 0.05 stem so its tip stays inside the join's own solid overlap
    # rather than reaching into the stem below it.
    cut = trap((xl, start * xh), (math.cos(math.radians(65)), math.sin(math.radians(65))), 18, S * 0.05)
    return solid, [cut], L, R

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

@glyph('m')
def g_m(c):
    xh = c["xh"]; x0 = S / 2; d = pen.NW * 0.88; x1 = x0 + d; x2 = x1 + d
    left = stem(x0, 0, xh, top='left', foot='both')
    mid = stem(x1, 0, 0.66 * xh, top=None, foot='both', ent_span=(0, xh))   # the references all foot the middle stem
    right = stem(x2, 0, 0.66 * xh, top=None, foot='both', ent_span=(0, xh))
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
    _b = pen.IT_BRANCH
    _start = xh * ((0.56 if r_on else 0.6) * (1 - _b) + 0.22 * _b)
    center = cubic((x0, _start), (x0, xh * (1.0 - 0.10 * _b)), (x0 + 120 * wf * R_REACH / 205, xh + over_c + 6), (x0 + R_REACH * wf, xh * 0.9))
    base = pen_widths(center, floor=S * R_FLOOR)
    prof = widths([(0.0, 0.5), (0.35, 1.0), (0.55, 1.0), (1.0, 1.05)]) if r_on else widths([(0.0, 0.5), (0.35, 1.0), (0.55, 1.0), (1.0, R_FLARE)])
    wfn = lambda t: base(t) * prof(t)
    arm = stroke(center, wfn, cut1=CUT)
    # (a family end wedge was tried on the arm's tip and stood up like a horn -- the plain cut it is)
    xl = stem_edge_x(x0, TH_V, ENT, 0.52 * xh, 0, xh, +1)
    cut = trap((xl, 0.52 * xh), (math.cos(math.radians(65)), math.sin(math.radians(65))), 18, S * (0.05 if r_on else 0.22))
    return geom.ink([st, arm], [cut])
FOOT_R = 0.85   # round 92: the r's feet, x the family's foot length
R_REACH, R_FLOOR, R_FLARE = 190, 0.72, 1.35   # round 94: was 205, 0.78, 1.5
