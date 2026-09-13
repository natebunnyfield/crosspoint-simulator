"""0-9, old-style, drawn at the height of their reference box (c['figH'];
the builder shifts each into its box, latin.FIG_BOX). The 8 on two rings,
bottom-heavy (2026-09-13; round 49 had them in the 6's proportion), the 3's
bottom after the 5's (round 44), the 6 and 9 with one thinning stroke
(round 42), the 2's base and the 5's top running past their bodies by the
9's tail overhang (2026-09-13)."""
import math
from . import glyph
from .. import geom, pen
from ..geom import cubic, line, superellipse
from ..primitives import stem, ring, stroke, pen_widths, widths, diagonal, bar, wedge, end_wedge, bowl_hair
from ..pen import S, OVER, TH_V, TH_H, HAIR, CUT, BOWL_K, WL, WD, DROP
from .caps_straight import W_, pw

# Owner 2026-09-13: "extend the bottom of 2 and top of 5 to the right
# (visually the same overhang as 9's tail goes to the left)". The 9's tail
# tip sits 11 units left of its bowl's leftmost ink, measured on the built
# outline (raster at a 1000 px em reads 10: the cut corner's tip pixel falls
# under the threshold). The 2's base and the 5's top end that far past their
# body's rightmost ink.
NINE_OVERHANG = 11.0

def fig_ring(cx, cy, rx_c, ry_c):
    return ring(cx, cy, rx_c + TH_V / 2, ry_c + TH_H / 2)

@glyph('0')
def g_zero(c):
    D = c["figH"]; rx = W_(c, '0', 230)
    solid, o, i = fig_ring(rx + TH_V / 2, D / 2, rx, D / 2 + OVER - TH_H / 2); return solid

@glyph('1')
def g_one(c):
    D = c["figH"]; x = 200 * c["wf"] + S / 2
    st = stem(x, 0, D, top=None, foot='both')
    flag = stroke(line((x - 150, D * 0.72), (x + 6, D + 2)), pen_widths(line((x - 150, D * 0.72), (x, D)), lambda t: 0.85), cut0=CUT)
    return geom.ink([st, flag])

@glyph('2')
def g_two(c):
    D = c["figH"]; w = W_(c, '2', 440); rx = w * 0.46
    top = superellipse(rx, D - rx * 0.95, rx, rx * 0.95, math.radians(190), math.radians(-25), BOWL_K)
    arc = stroke(top, pen_widths(top, widths([(0.0, 1.2), (0.15, 1.0)])), cut0=CUT)
    d = diagonal(top[-1], (S * 0.2, TH_H * 0.5), pw(top[-1], (S * 0.2, TH_H * 0.5)))
    barw = max(TH_H, S * 0.5)
    # the base runs NINE_OVERHANG past the neck's rightmost ink; its rightmost
    # ink is the pen cut's lower corner, tan(CUT) x half the bar past x1
    x1 = max(geom.bbox(arc)[2], geom.bbox(d)[2]) + NINE_OVERHANG - math.tan(CUT) * barw / 2
    return geom.ink([arc, d, bar(0, x1, 0, barw, align='bottom', cut1=CUT, wedges=[('right', 1)])])

@glyph('3')
def g_three(c):
    D = c["figH"]; w = W_(c, '3', 330); r1 = D * 0.20; r2 = D * 0.30
    top = superellipse(w * 0.52, D - r1, w * 0.46, r1, math.radians(165), math.radians(-105), BOWL_K)
    bot = superellipse(w * 0.52, r2, w * 0.52, r2 + OVER - TH_H / 2, math.radians(100), math.radians(-156), BOWL_K)
    t = stroke(top, pen_widths(top, widths([(0.0, 1.1), (0.1, 1.0), (0.88, 1.0), (1.0, 0.4)])), cut0=CUT)
    b = stroke(bot, pen_widths(bot, widths([(0.0, 0.4), (0.1, 1.0), (0.85, 1.0), (1.0, 1.25)])), cut1=CUT)
    return geom.ink([t, b])

@glyph('4')
def g_four(c):
    D = c["figH"]; w = W_(c, '4', 480); xs = w * 0.7
    return geom.ink([diagonal((xs - S * 0.2, D), (S * 0.1, D * 0.3), pw((xs - S * 0.2, D), (S * 0.1, D * 0.3), 0.75)), bar(0, w, D * 0.3, max(TH_H, S * 0.5)),
                     stem(xs, 0, D, top=None, foot='both')])

@glyph('5')
def g_five(c):
    D = c["figH"]; w = W_(c, '5', 400); r = D * 0.31
    st = stem(S * 0.3 + S / 2, D * 0.5, D + 10, w=TH_V * 0.85 * pen.CAP_STEM, top=None, foot=None, ent=0.0)   # round 51: vstem at 0.85 x the cap stem
    bowl = superellipse(w * 0.5, r, w * 0.55, r + OVER - TH_H / 2, math.radians(125), math.radians(-160), BOWL_K)
    bw = stroke(bowl, pen_widths(bowl, widths([(0.0, 0.45), (0.12, 1.0), (0.85, 1.0), (1.0, 1.25)])), cut1=CUT)
    # the top runs NINE_OVERHANG past the bowl's rightmost ink (it ended
    # 0.95 w, 72 units inside it); the square end and the hanging wedge's
    # apex both sit at x1, so x1 is the bar's rightmost ink
    x1 = geom.bbox(bw)[2] + NINE_OVERHANG
    top = bar(S * 0.3, x1, D, max(TH_H, S * 0.5), align='center', cut0=CUT, wedges=[('right', -1)])   # round 51: centred ON D, its top at D + 28
    return geom.ink([top, st, bw])

@glyph('6')
def g_six(c):
    D = c["figH"]; rx = W_(c, '6', 230); r = D * 0.29; ry = r + OVER - TH_H / 2
    solid, o, i = fig_ring(rx + TH_V / 2, r, rx, ry); cx = rx + TH_V / 2
    p0 = (cx - rx, r); tip = (cx + rx * 0.85, D - 10)
    top = cubic(p0, (p0[0], p0[1] + ry * 1.5), (tip[0] - rx * 0.55, tip[1] - rx * 0.75), tip)
    t = stroke(top, pen_widths(top, widths([(0.0, 0.15), (0.06, 1.0), (0.65, 1.0), (1.0, 0.12)])))
    return geom.ink([solid, t])

@glyph('7')
def g_seven(c):
    D = c["figH"]; w = W_(c, '7', 440)
    return geom.ink([bar(0, w, D, max(TH_H, S * 0.5), align='top', cut1=CUT, wedges=[('left', -1)]), diagonal((w - S * 0.2, D - 10), (w * 0.3, 0), pw((w - S * 0.2, D - 10), (w * 0.3, 0)))])

@glyph('8')
def g_eight(c):
    """Bottom-heavy (owner 2026-09-13: the round-49 8 was "top heavy" -- its
    upper loop was 331 wide with the lower's 96-unit sides, a 135-unit
    counter that closed to a dot at 13 pt, and wider than it was tall). The
    lower loop keeps round 49's width, 0.588 D (0.98 x 0.60 D, the 6's
    proportion); the upper is 0.80 of that wide, 0.51 of the figure's height
    tall, and its sides 0.9 of the pen so the counter stays open. The two
    rings overlap by exactly the bowl's horizontal stroke, so the waist is
    ONE band and not two stacked strokes. Both ends overshoot 14 as the 0
    and 6 do (the old 8 put its top ON D and its bottom 28 under, 14 low at
    both ends)."""
    D = c["figH"]; T = D + 2 * OVER
    w2 = 0.588 * D; w1 = 0.80 * w2; h1 = 0.51 * T
    h2 = T + bowl_hair() - h1
    cx = w2 / 2
    up, *_ = ring(cx, D + OVER - h1 / 2, w1 / 2, h1 / 2, w_scale=0.9)
    lo, *_ = ring(cx, -OVER + h2 / 2, w2 / 2, h2 / 2)
    return geom.ink([up, lo])

@glyph('9')
def g_nine(c):
    D = c["figH"]; rx = W_(c, '9', 230); r = D * 0.29
    solid, o, i = fig_ring(rx + TH_V / 2, D - r, rx, r); cx = rx + TH_V / 2
    p0 = (cx + rx * math.cos(math.radians(-20)), D - r + r * math.sin(math.radians(-20))); tip = (cx - rx * 1.12, 22)
    tail = cubic(p0, (p0[0] - rx * 0.15, p0[1] - r * 1.5), (tip[0] + rx * 1.15, tip[1] + r * 0.55), tip)
    base = pen_widths(tail)
    t = stroke(tail, lambda t: max(base(t), S * 0.9) * widths([(0.0, 0.15), (0.06, 1.0)])(t), cut1=CUT)
    return geom.ink([solid, t])
