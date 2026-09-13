"""i l j f t a s and the bowl-and-stem letters b d p q, and the g."""
import math, os
import shapely.affinity as aff
from . import glyph
from .. import geom, pen
from ..geom import cubic, line, join, superellipse, catmull
from ..primitives import stem, stem_edge_x, ring, ring_from, stroke, pen_widths, widths, dot, wedge, trap, diagonal, beak, widen_terminal
from .. import primitives as PR
from ..pen import S, XH, ASC, DESC, OVER, TH_V, TH_H, HAIR, CUT, BOWL_K, ENT, WL, WD, DROP
from .rounds import o_ring, open_arc

DOT_R = 0.62 * S   # round 36: a dot 1.24 stems across reads as the stem's weight
def dot_y(xh): return xh + 118 + S * 0.3

# owner, 2026-09-13: "slightly extend the top right serif of g" -- the ear's
# LENGTH only (the wedge family's L, WL, scaled), its DEPTH (the stroke's own
# cross-section) unchanged. Built at +15% and +30% for the page; +15% ships
# here by default. ALBO_G_EAR_EXTEND overrides for the page's other variant.
G_EAR_EXTEND = 0.15
def g_ear_scale(): return 1.0 + float(os.environ.get('ALBO_G_EAR_EXTEND', G_EAR_EXTEND))

# owner, 2026-09-13: "make a version of 't' that is a triangle on the right
# side, but keep it optically even to what is there now." Default True so
# both the old and new t ship; the page shows both.
T_RIGHT_TRIANGLE = os.environ.get('ALBO_T_TRIANGLE', '1') != '0'
T_TRI_SCALE = 0.55   # tunes the triangle's apex height so its ink area matches the old bar's within 2% (measured: old 53927 sq units at 1000 upm, triangle at 1.0 overshot to 56690 (+5.1%), 0.55 lands at 54552 (+1.2%))

@glyph('i')
def g_i(c):
    xh = c["xh"]; x = S / 2
    return geom.ink([stem(x, 0, xh, top='left', foot='both'), dot(x, dot_y(xh), DOT_R)])

@glyph('l')
def g_l(c):
    return geom.ink([stem(S / 2, 0, c["asc"], top='left', foot='both')])

@glyph('j')
def g_j(c):
    """No top flag; the tail one round arc holding the stem's weight through
    the turn and thinning to a point past the bottom (rounds 22, 25)."""
    xh = c["xh"]; wf = c["wf"]; desc = c["desc"]; r = 125 * wf; x = 120 * wf + S / 2
    B = -desc * 0.97; y0 = B + r
    st = stem(x, y0 - 30, xh, top=None, foot=None, ent_span=(y0 - 260, xh))
    a0, a1 = 0.0, math.radians(-118)
    tail = [(x - r + r * math.cos(a0 + (a1 - a0) * i / 48), y0 + r * math.sin(a0 + (a1 - a0) * i / 48)) for i in range(49)]
    wfn = widths([(0.0, TH_V), (0.45, S), (1.0, S * 0.10)])
    return geom.ink([st, stroke(tail, wfn), dot(x, dot_y(xh), DOT_R)])

@glyph('f')
def g_f(c):
    """VdK's f (round 42): hook radius 200, reaching 0.65 xh past the stem,
    flaring into the pen cut; the bar 0.8 of the pen with its top on the
    x-height, 45 left / 120 right."""
    xh = c["xh"]; asc = c["asc"]; wf = c["wf"]; r = 200 * wf; x = 110 * wf + S / 2
    st = stem(x, 0, asc - r + 30, top=None, foot='both', ent_span=(0, asc))
    hook = cubic((x, asc - r), (x, asc + 8), (x + r * 0.9, asc + 8), (x + r * 1.25, asc - r * 0.55))
    hk = stroke(hook, pen_widths(hook, widths([(0.0, 1.0), (0.7, 1.0), (1.0, 1.2)])), cut1=CUT)
    th = TH_H * 0.8
    b = stroke([(x - S * 0.5 - 45 * wf, xh - th / 2), (x + S * 0.5 + 120 * wf, xh - th / 2)], th)
    return geom.ink([st, hk, b])

@glyph('t')
def g_t(c):
    xh = c["xh"]; wf = c["wf"]; r = 135 * wf; x = 100 * wf + S / 2
    st = stem(x, r * 0.85 - 10, xh + 95, top=None, foot=None, ent_span=(0, xh + 95), cut_top=CUT)
    tail = cubic((x, r * 0.85), (x, -OVER * 0.5), (x + r * 0.8, -OVER * 0.5), (x + r * 1.45, r * 0.6))
    tl = stroke(tail, pen_widths(tail, widths([(0.0, 1.0), (0.65, 1.0), (1.0, 1.3)])), cut1=CUT)
    if T_RIGHT_TRIANGLE:
        # owner, 2026-09-13: "make a version of 't' that is a triangle on
        # the right side, but keep it optically even to what is there now."
        # The bar's LEFT arm is untouched (same stroke as always, stopping
        # at the stem's own right edge at the top of the entasis swell);
        # from there to the bar's old right end the crossbar and the stem's
        # top are read as ONE triangular wedge -- the bar's top edge rises
        # from the crossbar's height to the stem's own top-right corner,
        # its bottom edge stays on the crossbar's underside, its right edge
        # is the family's own pen cut (the stem top is already sheared by
        # CUT, so the triangle's outer edge continues that same face rather
        # than adding a second, different-angled cut). T_TRI_SCALE tunes the
        # apex height so the triangle's own area plus the shortened bar
        # matches the old bar's ink within 2% (measured, not eyeballed --
        # see the proof page for the before/after area).
        stem_r_top = x + TH_V * (1.0 + ENT) / 2   # the stem's own right edge at its top corner (full entasis swell)
        bar_y = xh - TH_H / 2; bar_bot = xh - TH_H; right_tip = x + 150 * wf
        apex = (stem_r_top, xh + 95 * T_TRI_SCALE)
        tri = geom.poly([apex, (right_tip, bar_bot), (stem_r_top, bar_bot)])
        b_left = stroke([(x - 100 * wf, bar_y), (stem_r_top, bar_y)], TH_H)
        b = geom.union([b_left, tri])
    else:
        b = stroke([(x - 100 * wf, xh - TH_H / 2), (x + 150 * wf, xh - TH_H / 2)], TH_H)
    return geom.ink([st, tl, b])

@glyph('a')
def g_a(c):
    """Stem, hood and bowl. The hood leaves the stem thin, thickens over the
    top and ends in the family's flag. The bowl is DRAWN: its upper edge a
    diagonal from the stem down-left to the bowl's left extreme at 0.27 xh,
    a round bottom back into the stem at the foot; the counter is the pen's
    offset (a hairline along the diagonal, the stem's weight at the lower
    left, the horizontal at the bottom). Hood peaks at the rounds'
    overshoot, bowl bottoms at it."""
    xh = c["xh"]; wf = c["wf"]; x = 360 * wf
    st = stem(x, 0, xh * 0.95, top=None, foot='both', ent_span=(0, xh))
    yc = (8 * (xh + OVER - TH_H / 2) - xh * 0.66 - xh * 0.78) / 6
    hood = cubic((x, xh * 0.66), (x, yc), (x - 250 * wf, yc), (x - 300 * wf, xh * 0.78))
    hd = stroke(hood, pen_widths(hood, widen_terminal(widths([(0.0, 0.5), (0.3, 1.0), (0.7, 1.0), (1.0, 1.10)])) if (PR.BOWL and PR.BOWL.get('widen')) else widths([(0.0, 0.5), (0.3, 1.0), (0.7, 1.0), (1.0, 1.10)])), cut1=CUT)
    L = (x - 330 * wf, xh * 0.27); B = (x - 150 * wf, -OVER); xe = x - TH_V / 2
    # the corner where the bowl's outer path closes near the stem must land
    # BURIED inside the stem's own ink (the guide's join rule: a fifth to a
    # third of a stem), not at a fixed offset from xe -- a fixed "+82" was
    # tuned for a thinner pen and, at the current stem/contrast, landed 82
    # units from the stem's LEFT edge while the stem's RIGHT edge (with
    # entasis) sits only ~76-83 units in: the corner poked 2-6 units PAST
    # the stem's own edge, and because it is a sharp reversal (the outer
    # path's closing straight run meeting the curve toward L), that overshoot
    # showed as a step/notch at the top right instead of hiding inside the
    # stem's ink (found by probing the union's rightmost x by height: it
    # spiked to xe+82 for two samples right at xh*0.67 and nowhere else).
    xin = x + TH_V / 2 - TH_V * 0.35   # a third of a stem inside the stem's right edge, so it clears entasis at both the top and bottom corners
    top = (xin, xh * 0.67)   # buried well inside the stem; a shallow crotch under the hood, as round 51's
    outer = join(cubic(top, (top[0] - 120 * wf, top[1] - 55), (L[0], L[1] + 105), L),
                 cubic(L, (L[0], L[1] - 115), (B[0] - 100 * wf, B[1]), B),
                 cubic(B, (B[0] + 80 * wf, B[1]), (xin, 20), (xin, 60)))
    # the counter is the pen's offset at each tangent (a hairline along the
    # diagonal, the stem's weight at the lower left, the horizontal along
    # the bottom), the width sequence averaged over +-4 samples so the
    # tight lower-left turn does not step it; near the stem the width is
    # held at 40 so the counter lands on the stem's edge. The two regimes
    # used to switch on a hard x-threshold (p[0] > xe + 30), which stepped
    # the width from ~40 straight down to a near-hairline in one or two
    # samples right where the curve is turning fastest (just past the top
    # corner) -- steep enough that the inward offset crossed the outer
    # path and left an island for shapely's make_valid to carve out (the
    # top-right blob). Blended over a span instead of switched: a clean
    # taper, no discontinuity for the offset to trip on.
    n_o = len(geom.resample(outer + [outer[0]])) - 1
    tans_o = geom.tangents(geom.resample(outer + [outer[0]])[:-1], closed=True)
    outer_closed = geom.resample(outer + [outer[0]])[:-1]
    NEAR_STEM_W = 40.0
    def wfn2(t):
        i = min(n_o - 1, int(round(t * n_o))); p = outer_closed[i]
        pen_w = pen.PEN.th(tans_o[i])
        u = max(0.0, min(1.0, (p[0] - (xin - 90.0)) / 90.0)); u = u * u * (3 - 2 * u)
        return pen_w * (1 - u) + NEAR_STEM_W * u
    solid, o, i = ring_from(outer, widths_fn=wfn2, counter_smooth=3, smooth_w=8)
    return geom.ink([st, hd, solid])

@glyph('s')
def g_s(c):
    """One smooth spine on the pen's own widths (round 51's s: no spine
    boost -- that is the capital's rule), flaring 1.25 into a 20-degree pen
    cut at both ends."""
    xh = c["xh"]; wf = c["wf"]; w = 370 * wf; o = OVER - TH_H / 2
    pts = [(w * 0.93, xh * 0.80), (w * 0.62, xh + o * 0.9), (w * 0.20, xh * 0.86), (w * 0.22, xh * 0.60),
           (w * 0.78, xh * 0.42), (w * 0.82, xh * 0.16), (w * 0.42, -o * 0.9), (w * 0.06, xh * 0.19)]
    spine = catmull(pts, tension=0.55)
    prof = widths([(0.0, 1.25), (0.12, 1.0), (0.88, 1.0), (1.0, 1.25)])
    if PR.BOWL and PR.BOWL.get('widen'): prof = widen_terminal(widen_terminal(None, True), False)
    wfn = pen_widths(spine, prof)
    return geom.ink([stroke(spine, wfn, cut0=CUT, cut1=CUT)])

def bowl_stem(c, side, top, bottom):
    """b d p q: the o's ring at the b's radius, KEPT TO THE STEM (ruling,
    round 18): the ring's far stroke is centred half a stem outside the
    stem's centre, as the record placed it, and the ring is clipped a hair
    inside the stem's inner edge -- the union with the stem is the join,
    the counter's edge is the stem's inner edge, nothing pokes past the
    stem. A trap notch at each crotch."""
    from shapely.geometry import box
    xh = c["xh"]; wf = c["wf"]
    rx_c = 214 * wf; rx = rx_c + TH_V / 2; ry = xh / 2 + OVER
    if side == 'right':   # d q: stem on the right
        cx = rx; x = cx + rx_c - S * 0.5; into = -1   # the record: the stem's centre half a stem INSIDE the ring's far centerline
    else:                 # b p
        x = S / 2; cx = x - S * 0.5 + rx_c; into = 1
    solid, outer, inner = ring(cx, xh / 2, rx, ry)
    edge = x + into * TH_V / 2
    clip = box(edge - 5, -1000, 3000, 2000) if into == 1 else box(-2000, -1000, edge + 5, 2000)
    solid = solid.intersection(clip)
    foot = ('right' if side == 'right' else 'left') if bottom == 0 else 'both'
    st = stem(x, bottom, top, top='left', foot=foot, ent_span=(bottom, top))
    # no trap cutouts here: the first version's pointed INTO the strokes
    # (a nick on the outside at each crotch, seen at 500 px); no ruling asks
    # for traps on the bowl letters
    return geom.ink([solid, st])

@glyph('b')
def g_b(c): return bowl_stem(c, 'left', c["asc"], 0)
@glyph('d')
def g_d(c): return bowl_stem(c, 'right', c["asc"], 0)
@glyph('p')
def g_p(c): return bowl_stem(c, 'left', c["xh"], -c["desc"])
@glyph('q')
def g_q(c): return bowl_stem(c, 'right', c["xh"], -c["desc"])

@glyph('g')
def g_g(c):
    """G3 on the nib (rulings, rounds 40/42): bowl rx 185, 0.70 xh tall;
    loop rx 215 x 0.45 desc, 30 right of the bowl; the neck from 242 deg
    dropping near-vertically into the loop at 150 deg, no floor; the ear a
    pen stroke off the shoulder at 48 deg, rising 5."""
    xh = c["xh"]; wf = c["wf"]; desc = c["desc"]
    rx = 185 * wf + TH_V / 2; ry = (xh * 0.70 + OVER * 2) / 2; cy = xh + OVER - ry; cx = rx + S * 0.35
    bowl, bo, bi = ring(cx, cy, rx, ry)
    lrx = 215 * wf + TH_V / 2; lry = desc * 0.45 + TH_H / 2; lcx = cx + 30 * wf; lcy = -desc * 0.47
    loop, lo, li = ring(lcx, lcy, lrx, lry)
    # centerline rings for the neck's ends
    crx, cry = rx - TH_V / 2, ry - TH_H / 2; clrx, clry = lrx - TH_V / 2, lry - TH_H / 2
    def on(cx_, cy_, rx_, ry_, deg):
        a = math.radians(deg); return (cx_ + rx_ * math.cos(a), cy_ + ry_ * math.sin(a))
    p0 = on(cx, cy, crx, cry, 242); a1 = math.radians(150); p3 = on(lcx, lcy, clrx, clry, 150)
    tl = (-math.sin(a1), math.cos(a1)); gap = p0[1] - p3[1]
    # the neck starts 22 units up INSIDE the bowl's stroke (its square face
    # straddled the centerline and one corner broke the ring's edge -- a
    # nick at 500 px); the ear the same, from the ring's centerline
    p0 = (p0[0] + 4, p0[1] + 22)
    neck = cubic(p0, (p0[0] - gap * 0.02, p0[1] - gap * 0.60), (p3[0] - tl[0] * gap * 0.55, p3[1] - tl[1] * gap * 0.55), p3)
    # the start's square face used to be drawn at FULL pen width right where
    # it enters the ring: the bowl's own curve widens gradually there, but
    # the neck's flat full-width face does not follow it, so the union held
    # a few rows of constant width (a shelf) wherever the neck's straight
    # edge stuck out past the ring's own curving edge, before the ring's
    # curve caught up and grew past it -- a stray mark right at the join
    # (found by comparing the ring drawn alone against the union row by row:
    # the ring's own width increases every row, the union's held flat for
    # six). Tapered in over the same span the far end tapers out, so the
    # face that lands inside the ring is thin and the ring's own curve
    # decides the join's outline, not the neck's square corner.
    nk = stroke(neck, pen_widths(neck, widths([(0.0, 0.35), (0.14, 1.0), (0.90, 1.0), (1.0, 0.25)])))   # the end thins so its corners stay inside the loop's stroke (round 51: taper_out 0.85 over 8%)
    ex, ey = on(cx, cy, crx, cry, 48); L = 118 * wf * g_ear_scale()   # the ear's length only, scaled by g_ear_scale(); its cross-section (the widths keypoints below) is untouched, so the depth is unchanged
    ear = stroke([(ex - S * 0.30, ey - 24), (ex + L, ey + L * math.tan(math.radians(5)))], pen_widths([(ex, ey), (ex + L, ey + 8)], widths([(0.0, 0.45), (0.28, 1.0)])), cut1=CUT)   # starts inside the ring, thin, so no corner reaches the counter
    return geom.ink([bowl, loop, nk, ear])
