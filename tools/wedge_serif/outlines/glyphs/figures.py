"""0-9, old-style, drawn at the height of their reference box (c['figH'];
the builder shifts each into its box, latin.FIG_BOX). The 8 on two rings in
the 6's proportion (round 49), the 3's bottom after the 5's (round 44), the
6 and 9 with one thinning stroke (round 42)."""
import math
from . import glyph
from .. import geom, pen
from ..geom import cubic, line, superellipse
from ..primitives import stem, ring, stroke, pen_widths, widths, diagonal, bar, wedge, end_wedge
from ..pen import S, OVER, TH_V, TH_H, HAIR, CUT, BOWL_K, WL, WD, DROP
from .caps_straight import W_, pw

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
    return geom.ink([arc, d, bar(0, w, 0, max(TH_H, S * 0.5), align='bottom', cut1=CUT, wedges=[('right', 1)])])

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
    top = bar(S * 0.3, w * 0.95, D, max(TH_H, S * 0.5), align='center', cut0=CUT, wedges=[('right', -1)])   # round 51: centred ON D, its top at D + 28
    st = stem(S * 0.3 + S / 2, D * 0.5, D + 10, w=TH_V * 0.85 * pen.CAP_STEM, top=None, foot=None, ent=0.0)   # round 51: vstem at 0.85 x the cap stem
    bowl = superellipse(w * 0.5, r, w * 0.55, r + OVER - TH_H / 2, math.radians(125), math.radians(-160), BOWL_K)
    bw = stroke(bowl, pen_widths(bowl, widths([(0.0, 0.45), (0.12, 1.0), (0.85, 1.0), (1.0, 1.25)])), cut1=CUT)
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
    D = c["figH"]
    def ring_for(h): ry = (h - TH_H) / 2; rx = (0.98 * h - TH_V) / 2; return rx, ry
    rx2, ry2 = ring_for(D * 0.60); rx1, ry1 = ring_for(D * 0.50)
    cx = rx2 + TH_V / 2 + 4
    up, *_ = fig_ring(cx, D - ry1 - TH_H / 2, rx1, ry1)
    lo, *_ = fig_ring(cx, ry2 + TH_H / 2 - OVER, rx2, ry2 + OVER)
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
