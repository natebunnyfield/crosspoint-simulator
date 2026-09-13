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
from ..primitives import stem, stem_edge_x, edge_stroke, widths, stroke, trap, wedge
from ..pen import S, XH, ASC, TH_V, TH_H, HAIR, WL, WD, DROP, ENT, CUT

def arch_geom(x0, x1, xh, ent_span=None, peak_frac=0.58, leave_y=0.52, outer_leave=0.80, top_w=None,
              lean=50.0, lean_in=74.0, yr_frac=0.50, yri_frac=0.58, inner_peak_dx=-36.0, w=None):
    """The arch between a left stem centered at x0 and a right stem at x1.
    BOTH edges are designed: the outer (the silhouette) leaves the stem at
    outer_leave x xh at `lean` degrees, peaks at xh + 12 (ruling) right of
    centre, and comes down vertical into the right stem's right edge; the
    inner peels off the stem at leave_y x xh (ruling: 0.52) at `lean_in`
    degrees -- nearly along the stem, which is what makes the join a
    hairline -- peaks top_w under the outer (the pen's horizontal, 55,
    thinned to 50 as the garaldes' arch tops run under their o's), and comes
    down vertical into the right stem's left edge. Returns (solid, cutouts,
    outer, inner)."""
    w = w or TH_V; lo, hi = ent_span or (0, xh)
    xl = stem_edge_x(x0, w, ENT, outer_leave * xh, lo, hi, +1)
    yr = yr_frac * xh; yri = yri_frac * xh
    xr = stem_edge_x(x1, w, ENT, yr, lo, hi, +1); xri = stem_edge_x(x1, w, ENT, yri, lo, hi, -1)
    top = xh + pen.ARCH_OVER; top_w = top_w or TH_H * 0.95
    xp = xl + (xr - xl) * peak_frac; xpi = xp + inner_peak_dx
    a = math.radians(lean); P0 = (xl - 8, outer_leave * xh); d0 = math.dist(P0, (xp, top))
    outer = join(cubic(P0, (P0[0] + math.cos(a) * d0 * 0.40, P0[1] + math.sin(a) * d0 * 0.40), (xp - (xp - P0[0]) * 0.42, top), (xp, top)),
                 cubic((xp, top), (xp + (xr - xp) * 0.60, top), (xr, top - (top - yr) * 0.42), (xr, yr)))
    b = math.radians(lean_in); Q0 = (xl - 3, leave_y * xh); topi = top - top_w; d1 = math.dist(Q0, (xpi, topi))
    inner = join(cubic(Q0, (Q0[0] + math.cos(b) * d1 * 0.36, Q0[1] + math.sin(b) * d1 * 0.36), (xpi - (xpi - Q0[0]) * 0.40, topi), (xpi, topi)),
                 cubic((xpi, topi), (xpi + (xri - xpi) * 0.55, topi), (xri, topi - (topi - yri) * 0.52), (xri, yri)))
    # close the solid through the stems: outer .. down the right stem's right edge .. across .. up the inner .. back inside the left stem
    body = outer + [(xr, yr - 20), (xri, yri - 20)] + inner[::-1] + [(xl - 3, leave_y * xh - 20), (xl - 8, outer_leave * xh - 20)]
    solid = geom.poly(body)
    cut = trap((xl, leave_y * xh), (math.cos(math.radians(65)), math.sin(math.radians(65))), 18, S * 0.22)
    return solid, [cut], outer, inner

def arch(x0, x1, xh, **kw):
    solid, cuts, outer, inner = arch_geom(x0, x1, xh, **kw)
    return solid, cuts

@glyph('n')
def g_n(c):
    xh = c["xh"]; x0 = S / 2; x1 = x0 + pen.NW
    left = stem(x0, 0, xh, top='left', foot='both')
    right = stem(x1, 0, 0.60 * xh, top=None, foot='both', ent_span=(0, xh))
    a, cuts = arch(x0, x1, xh)
    return geom.ink([left, right, a], cuts)

@glyph('h')
def g_h(c):
    xh = c["xh"]; x0 = S / 2; x1 = x0 + pen.NW
    left = stem(x0, 0, c["asc"], top='left', foot='both')
    right = stem(x1, 0, 0.60 * xh, top=None, foot='both', ent_span=(0, xh))
    a, cuts = arch(x0, x1, xh, ent_span=(0, xh))
    return geom.ink([left, right, a], cuts)

@glyph('m')
def g_m(c):
    xh = c["xh"]; x0 = S / 2; d = pen.NW * 0.88; x1 = x0 + d; x2 = x1 + d
    left = stem(x0, 0, xh, top='left', foot='both')
    mid = stem(x1, 0, 0.60 * xh, top=None, foot='both', ent_span=(0, xh))   # the references all foot the middle stem
    right = stem(x2, 0, 0.60 * xh, top=None, foot='both', ent_span=(0, xh))
    a1, c1 = arch(x0, x1, xh); a2, c2 = arch(x1, x2, xh)
    return geom.ink([left, mid, right, a1, a2], c1 + c2)

@glyph('u')
def g_u(c):
    """The n turned over: the bowl is the arch's geometry mirrored through
    the x-height's middle and through the letter's middle, so the u's bottom
    is the n's shoulder. Left stem: top wedge, no foot (the bowl is its
    foot); right stem: top wedge, right foot (round 46: three wedges)."""
    xh = c["xh"]; x0 = S / 2; x1 = x0 + pen.NW
    import shapely.affinity as aff
    solid, cuts, outer, inner = arch_geom(x0, x1, xh)
    mid_x = (x0 + x1) / 2
    flip = lambda g: aff.scale(g, xfact=-1, yfact=-1, origin=(mid_x, xh / 2))
    bowl = flip(solid); cuts = [flip(q) for q in cuts]
    # the arch peaked at xh + 12 (arches); the u's bottom is a round and takes 14
    bowl = aff.translate(bowl, 0, -(pen.OVER - pen.ARCH_OVER))
    left = stem(x0, 0.40 * xh, xh, top='left', foot=None, ent_span=(0, xh))
    right = stem(x1, 0, xh, top='left', foot='right')
    return geom.ink([left, right, bowl], cuts)

@glyph('r')
def g_r(c):
    """Stem plus an arm: leaves the stem as the arch does (a hairline at
    0.52-0.72 xh), climbs to the arch overshoot and ends in the family's
    flag -- the stroke swells and is cut on the pen's angle. The arm holds
    0.78 stem through its length (round 36: the arm is the r's ink; the
    nib alone would make a 33-unit hairline of a stroke at its angle)."""
    xh = c["xh"]; x0 = S / 2; wf = c["wf"]
    st = stem(x0, 0, xh, top='left', foot='both')
    xl = stem_edge_x(x0, TH_V, ENT, 0.66 * xh, 0, xh, +1)
    top = xh + pen.ARCH_OVER; reach = 172 * wf
    P0 = (xl - 12, 0.62 * xh); peak = (xl + reach * 0.50, top - S * 0.36); end = (xl + reach, xh * 0.84)
    center = join(cubic(P0, (P0[0] + 40, P0[1] + 70), (peak[0] - 55, peak[1]), peak),
                  cubic(peak, (peak[0] + 45, peak[1]), (end[0] - 10, end[1] + 45), end))
    wfn = widths([(0.0, HAIR * 0.9), (0.10, HAIR), (0.42, S * 0.78), (0.78, S * 0.80), (1.0, S * 0.95)])
    arm = stroke(center, wfn, cut1=CUT)
    cut = trap((xl, 0.50 * xh), (math.cos(math.radians(65)), math.sin(math.radians(65))), 18, S * 0.22)
    return geom.ink([st, arm], [cut])
