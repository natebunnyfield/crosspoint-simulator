"""The 30 marks, on the record's geometry (round 41: fitted on their full
extent), the & and @ real glyphs (round 42)."""
import math
from . import glyph
from .. import geom, pen
from ..geom import cubic, line, superellipse, catmull
from ..primitives import stem, ring, stroke, pen_widths, widths, dot, wedge, diagonal, bar
from ..pen import S, XH, DESC, OVER, TH_V, TH_H, HAIR, CUT, BOWL_K, WL, WD, DROP
from .rounds import o_ring

def CAP(c): return c["cap"]

@glyph('.')
def g_period(c): r = CAP(c) * 0.08; return dot(r, r, r)
def comma_tail(x, y, up=True, w0=0.9, w1=0.3):
    if up: tail = cubic((x + S * 0.1, y - S * 0.35), (x + S * 0.1, y - S * 1.05), (x - S * 0.3, y - S * 1.45), (x - S * 0.6, y - S * 1.75))
    else:  tail = cubic((x - S * 0.1, y + S * 0.35), (x - S * 0.1, y + S * 1.05), (x + S * 0.3, y + S * 1.45), (x + S * 0.55, y + S * 1.75))
    return stroke(tail, pen_widths(tail, lambda t: w0 - (w0 - w1) * t))   # round 51: the pen x (0.9 - 0.6 t)
@glyph(',')
def g_comma(c): x = S * 0.55; return geom.ink([dot(x, S * 0.55, S * 0.55), comma_tail(x, S * 0.55)])
@glyph(':')
def g_colon(c): return geom.ink([dot(S * 0.55, S * 0.55, S * 0.55), dot(S * 0.55, XH - S * 0.55, S * 0.55)])
@glyph(';')
def g_semicolon(c): x = S * 0.55; return geom.ink([dot(x, S * 0.55, S * 0.55), comma_tail(x, S * 0.55), dot(x, XH - S * 0.55, S * 0.55)])
@glyph('!')
def g_exclam(c):
    C = CAP(c); x = S * 0.55
    return geom.ink([dot(x, S * 0.55, S * 0.55), stroke(line((x, S * 1.9), (x, C)), pen_widths(line((x, S * 1.9), (x, C)), lambda t: 0.55 + 0.5 * t), cut1=CUT)])
@glyph('?')
def g_question(c):
    C = CAP(c); w = 380
    end_y = C * 0.2 + max(0.0, (S - 94) * 2.2)   # above the shipping weight the hook stops higher, clear of the dot (identical at 94)
    hook = catmull([(w * 0.08, C * 0.74), (w * 0.28, C * 0.97), (w * 0.62, C * 0.98), (w * 0.88, C * 0.74), (w * 0.74, C * 0.5), (w * 0.5, C * 0.38 + max(0.0, (S - 94) * 1.2)), (w * 0.5, end_y)], tension=0.5)
    return geom.ink([dot(w * 0.5, S * 0.55, S * 0.55), stroke(hook, pen_widths(hook, widths([(0.0, 0.45), (0.15, 1.0), (0.8, 1.0), (1.0, 1.1)])), cut0=CUT, cut1=CUT)])
@glyph("'")
def g_quotesingle(c): C = CAP(c); return stroke(line((S * 0.5, C * 0.72), (S * 0.5, C)), TH_V * 0.8, cut0=CUT)
@glyph('"')
def g_quotedbl(c):
    C = CAP(c); return geom.ink([stroke(line((S * 0.5 + i * S * 1.3, C * 0.72), (S * 0.5 + i * S * 1.3, C)), TH_V * 0.8, cut0=CUT) for i in (0, 1)])
def quote(c, x, up):
    C = CAP(c); y = C - S * 0.55
    return geom.ink([dot(x, y, S * 0.5), comma_tail(x, y, up, 0.85, 0.3)])
@glyph('’')
def g_quoteright(c): return quote(c, S * 0.7, True)
@glyph('‘')
def g_quoteleft(c): return quote(c, S * 0.7, False)
@glyph('”')
def g_quotedblright(c): return geom.ink([quote(c, S * 0.7, True), quote(c, S * 2.0, True)])
@glyph('“')
def g_quotedblleft(c): return geom.ink([quote(c, S * 0.7, False), quote(c, S * 2.0, False)])
def dash(c, length): C = CAP(c); return stroke(line((0, C * 0.34), (length * C, C * 0.34)), TH_H)
@glyph('-')
def g_hyphen(c): return dash(c, 0.37)
@glyph('–')
def g_endash(c): return dash(c, 0.72)
@glyph('—')
def g_emdash(c): return dash(c, 1.41)
def paren(c, left):
    C = CAP(c); d = DESC; r = 150
    if left: pts = superellipse(r, (C - d) / 2, r, (C + d) / 2 + 16, math.radians(105), math.radians(255), 2.2)
    else: pts = superellipse(0, (C - d) / 2, r, (C + d) / 2 + 16, math.radians(75), math.radians(-75), 2.2)
    return stroke(pts, pen_widths(pts, lambda t: 0.6 + 0.4 * math.sin(math.pi * t)), cut0=CUT, cut1=CUT)
@glyph('(')
def g_parenleft(c): return paren(c, True)
@glyph(')')
def g_parenright(c): return paren(c, False)
def bracket(c, left):
    C = CAP(c); d = DESC; w = 180; x = S * 0.4 if left else w - S * 0.4
    x0, x1 = (x, w) if left else (0, x)
    return geom.ink([stroke(line((x, -d), (x, C)), TH_V * 0.85), stroke(line((x0, C - TH_H / 2), (x1, C - TH_H / 2)), TH_H), stroke(line((x0, -d + TH_H / 2), (x1, -d + TH_H / 2)), TH_H)])
@glyph('[')
def g_bracketleft(c): return bracket(c, True)
@glyph(']')
def g_bracketright(c): return bracket(c, False)
@glyph('/')
def g_slash(c): C = CAP(c); p = line((0, -DESC * 0.4), (330, C)); return stroke(p, pen_widths(p, lambda t: 0.8), cut0=CUT, cut1=CUT)
@glyph('\\')
def g_backslash(c): C = CAP(c); p = line((0, C), (330, -DESC * 0.4)); return stroke(p, pen_widths(p, lambda t: 0.8), cut0=CUT, cut1=CUT)
@glyph('*')
def g_asterisk(c):
    C = CAP(c); cx, cy = 200, C * 0.78; r = 150; parts = []
    for k in range(5):
        a = math.pi / 2 + k * 2 * math.pi / 5; p = line((cx, cy), (cx + r * math.cos(a), cy + r * math.sin(a)))
        parts.append(stroke(p, pen_widths(p, lambda t: 0.75), cut1=CUT))
    return geom.ink(parts)
@glyph('+')
def g_plus(c):
    y = XH * 0.55; w = 420
    return geom.ink([stroke(line((0, y), (w, y)), TH_H * 0.9), stroke(line((w / 2, y - w / 2), (w / 2, y + w / 2)), TH_V * 0.9)])
@glyph('=')
def g_equal(c):
    y = XH * 0.55; w = 420; g = S * 1.1
    return geom.ink([stroke(line((0, y - g / 2), (w, y - g / 2)), TH_H), stroke(line((0, y + g / 2), (w, y + g / 2)), TH_H)])
@glyph('&')
def g_ampersand(c):
    """Van den Keere's garalde ampersand (round 42): one stroke through 24
    measured points on the pen, the foot's hook tapered, the arm ending in
    the family's wedge pointing right."""
    C = CAP(c); w = 736; o = OVER - TH_H / 2
    pts = [(0.99, 0.10), (0.86, 0.02), (0.72, 0.07), (0.65, 0.17), (0.53, 0.37), (0.36, 0.56), (0.16, 0.68), (0.07, 0.80),
           (0.15, 0.94), (0.31, 0.98), (0.48, 0.90), (0.52, 0.76), (0.44, 0.63), (0.28, 0.53), (0.14, 0.44), (0.06, 0.32),
           (0.06, 0.16), (0.19, 0.03), (0.38, 0.0), (0.53, 0.11), (0.60, 0.27), (0.70, 0.41), (0.78, 0.53), (0.85, 0.64)]
    spine = catmull([(w * a, C * b + (o if b > 0.9 else (-o if b < 0.01 else 0))) for a, b in pts], tension=0.5)
    body = stroke(spine, pen_widths(spine, widths([(0.0, 0.3), (0.05, 1.0)])), cut0=CUT, pieces=True)   # the spine crosses itself twice
    arm = wedge(spine[-1], (0, 1), (1, 0), WL * 0.9, WD, 0.0)
    return geom.ink([body, arm])
@glyph('%')
def g_percent(c):
    C = CAP(c); r = 120; p = line((60, 0), (440, C))
    parts = [stroke(p, pen_widths(p, lambda t: 0.75), cut0=CUT, cut1=CUT)]
    for cx, cy in ((r + 10, C - r), (620 - r, r)):
        parts.append(ring(cx, cy, r + TH_V / 2, r + TH_H / 2, k=2.0)[0])   # r is the CENTERLINE radius (round 51): counter 163 of 317
    return geom.ink(parts)
@glyph('#')
def g_numbersign(c):
    C = CAP(c); w = 480; parts = []
    for x in (w * 0.32, w * 0.68): parts.append(stroke(line((x - w * 0.06, 0), (x + w * 0.06, C)), TH_V * 0.75))
    for y in (C * 0.35, C * 0.65): parts.append(stroke(line((0, y), (w, y)), TH_H))
    return geom.ink(parts)
@glyph('@')
def g_at(c):
    """Van den Keere's @ (round 42): cap height on the baseline, a
    single-storey a inside whose foot becomes the ring, the ring at 0.85 of
    the pen ending thinned at the lower right."""
    C = CAP(c); rx = C * 0.52; ry = C / 2 + OVER - TH_H / 2; cx = rx + S / 2; cy = C / 2
    ax = cx + rx * 0.24; a_bot = C * 0.19; a_top = C * 0.78
    brx = rx * 0.31; bry = C * 0.20; bcx = ax - brx - S * 0.28; bcy = C * 0.41
    bowl, o, i = ring(bcx, bcy, brx + TH_V / 2, bry + TH_H / 2)
    st = stroke(line((ax, a_bot), (ax, a_top)), TH_V * 0.9)
    hood = cubic((ax, a_top - S * 0.3), (ax, a_top + C * 0.08), (ax - brx * 1.2, a_top + C * 0.1), (ax - brx * 2.2, a_top - C * 0.08))
    hd = stroke(hood, pen_widths(hood, widths([(0.0, 0.45), (0.3, 1.0), (0.7, 1.0), (1.0, 1.1)])), cut1=CUT)
    ringc = superellipse(cx, cy, rx, ry, math.radians(-62), math.radians(-62 - 338), BOWL_K)
    link = cubic((ax, a_bot + S * 0.4), (ax, a_bot - C * 0.06), (ringc[0][0] - rx * 0.12, ringc[0][1] + ry * 0.12), ringc[0])
    lk = stroke(link, pen_widths(link, widths([(0.0, 0.15), (0.2, 0.62), (1.0, 0.62)])))
    rg = stroke(ringc, pen_widths(ringc, widths([(0.0, 0.1), (0.08, 0.85), (0.86, 0.85), (1.0, 0.42)])), cut1=CUT, pieces=True)
    return geom.ink([bowl, st, hd, lk, rg])
@glyph('_')
def g_underscore(c): return stroke(line((0, -DESC * 0.5), (500, -DESC * 0.5)), TH_H)
@glyph('…')
def g_ellipsis(c): return geom.ink([dot(S * 0.55 + i * S * 2.4, S * 0.55, S * 0.55) for i in range(3)])
