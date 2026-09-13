"""i l j f t a s and the bowl-and-stem letters b d p q, and the g."""
import math
import shapely.affinity as aff
from . import glyph
from .. import geom, pen
from ..geom import cubic, line, join, superellipse, catmull
from ..primitives import stem, stem_edge_x, ring, ring_from, stroke, pen_widths, widths, dot, wedge, trap, diagonal, beak
from ..pen import S, XH, ASC, DESC, OVER, TH_V, TH_H, HAIR, CUT, BOWL_K, ENT, WL, WD, DROP
from .rounds import o_ring, open_arc

DOT_R = 0.62 * S   # round 36: a dot 1.24 stems across reads as the stem's weight
def dot_y(xh): return xh + 118 + S * 0.3

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
    hd = stroke(hood, pen_widths(hood, widths([(0.0, 0.5), (0.3, 1.0), (0.7, 1.0), (1.0, 1.10)])), cut1=CUT)
    L = (x - 330 * wf, xh * 0.27); B = (x - 150 * wf, -OVER); xe = x - TH_V / 2
    top = (xe + 82, xh * 0.62)   # closes 82 inside the stem, so the counter's offset lands ON the stem's edge
    outer = join(cubic(top, (top[0] - 110 * wf, top[1] - 40), (L[0], L[1] + 70), L),
                 cubic(L, (L[0], L[1] - 95), (B[0] - 95 * wf, B[1]), B),
                 cubic(B, (B[0] + 80 * wf, B[1]), (xe + 82, 20), (xe + 82, 60)))
    solid, o, i = ring_from(outer, floor=HAIR * 0.85)
    return geom.ink([st, hd, solid])

@glyph('s')
def g_s(c):
    """One smooth spine; the middle runs near the nib's angle, so the
    weight is DECLARED: 0.92 stem at the middle, the pen's own at the ends,
    a flared face at the top (steep cut), a thinner pen-cut end below."""
    xh = c["xh"]; wf = c["wf"]; w = 370 * wf; o = OVER - TH_H / 2
    pts = [(w * 0.93, xh * 0.80), (w * 0.62, xh + o * 0.9), (w * 0.20, xh * 0.86), (w * 0.22, xh * 0.60),
           (w * 0.78, xh * 0.42), (w * 0.82, xh * 0.16), (w * 0.42, -o * 0.9), (w * 0.06, xh * 0.19)]
    spine = catmull(pts, tension=0.55)
    base = pen_widths(spine)
    def wfn(t):
        mid = 1.0 - min(1.0, abs(t - 0.5) / 0.28)
        want = base(t) * (1 - mid) + S * 0.92 * mid
        return want * widths([(0.0, 1.15), (0.12, 1.0), (0.86, 1.0), (1.0, 0.72)])(t)
    body = stroke(spine, wfn, cut0=math.radians(-22), cut1=CUT)
    lip = beak(spine, wfn(0.0), True, -22.0, lip=(0.35, 0.6))
    return geom.ink([body, lip])

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
        cx = rx; x = cx + rx_c + S * 0.5; into = -1
    else:                 # b p
        x = S / 2; cx = x - S * 0.5 + rx_c; into = 1
    solid, outer, inner = ring(cx, xh / 2, rx, ry)
    edge = x + into * TH_V / 2
    clip = box(edge - 5, -1000, 3000, 2000) if into == 1 else box(-2000, -1000, edge + 5, 2000)
    solid = solid.intersection(clip)
    foot = ('right' if side == 'right' else 'left') if bottom == 0 else 'both'
    st = stem(x, bottom, top, top='left', foot=foot, ent_span=(bottom, top))
    cuts = []
    for y, sgn in ((xh * 0.80, 1), (xh * 0.20, -1)):
        cuts.append(trap((edge, y), (into * 0.7, sgn * 0.7), 18, S * 0.18))
    return geom.ink([solid, st], cuts)

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
    neck = cubic(p0, (p0[0] - gap * 0.02, p0[1] - gap * 0.60), (p3[0] - tl[0] * gap * 0.55, p3[1] - tl[1] * gap * 0.55), p3)
    nk = stroke(neck, pen_widths(neck))
    ex, ey = on(cx, cy, crx, cry, 48); L = 118 * wf
    ear = stroke([(ex - S * 0.15, ey - 4), (ex + L, ey + L * math.tan(math.radians(5)))], pen_widths([(ex, ey), (ex + L, ey + 8)]), cut1=CUT)
    return geom.ink([bowl, loop, nk, ear])
