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
G_NECK = 0.42        # the neck's floor, x the stem (0.55 before; owner: thin the connector)
G_NECK_MID = 0.72    # the neck's middle, x its profile
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
    """Round 51's t, restored (owner 2026-09-13: "revert 't' before the
    triangle"): the stem sheared at the top by the pen cut, a plain bar,
    the hooked tail."""
    xh = c["xh"]; wf = c["wf"]; r = 135 * wf; x = 100 * wf + S / 2
    st = stem(x, r * 0.85 - 10, xh + 95, top=None, foot=None, ent_span=(0, xh + 95), cut_top=CUT)
    tail = cubic((x, r * 0.85), (x, -OVER * 0.5), (x + r * 0.8, -OVER * 0.5), (x + r * 1.45, r * 0.6))
    tl = stroke(tail, pen_widths(tail, widths([(0.0, 1.0), (0.65, 1.0), (1.0, 1.3)])), cut1=CUT)
    b = stroke([(x - 100 * wf, xh - TH_H / 2), (x + 150 * wf, xh - TH_H / 2)], TH_H)
    return geom.ink([st, tl, b])

T_TOP_RISE = 96
T_TOP_SHEAR_DEG = 46

# owner 2026-09-14: "make five versions for me to pick from that gives a curve
# instead of a corner in the upper right of 'a'": (stem top x xh, hood
# start x xh, lean right in wf units, the lean's height x xh)
A_CURVES = [(0.66, 0.54, 22, 0.93),   # 0: round 84's
            (0.62, 0.50, 34, 0.94),   # 1: a little rounder
            (0.58, 0.46, 46, 0.95),   # 2: rounder still
            (0.54, 0.42, 60, 0.96),   # 3: a full shoulder
            (0.70, 0.58, 14, 0.90)]   # 4: barely a curve, the stem nearly to the top
A_CURVE = int(__import__('os').environ.get('FJORD_A_CURVE', 0))

@glyph('a')
def g_a(c):
    """Stem, hood and bowl -- redrawn 2026-09-13 (owner: the first cleanup
    "sucks"). What was wrong: the hood and the bowl's upper edge were PEN
    strokes, and at contrast 0.95 the pen's thin is the 6-unit floor, so the
    hood read as a bar with a flag and the bowl as a shallow lens. Now the
    hood and the bowl are on the BOWL profile (hair 0.525 S at this
    contrast), the bowl is taller -- it leaves the stem at 0.60 xh with a
    round upper-left shoulder instead of a straight diagonal -- and the
    hood curls: it climbs from the stem, crosses the top at the rounds'
    overshoot and comes DOWN to its terminal, which swells and ends in the
    pen cut, a teardrop not a flag. Counter and aperture are the whites
    the standing rule watches: reported on the page."""
    xh = c["xh"]; wf = c["wf"]; x = 360 * wf
    # owner 2026-09-13: "the top right of 'a' needs to be more of a curve
    # than a rectangular corner" -- the stem stops at A_STEM_TOP x xh and the
    # hood takes over from lower on the stem, leaning out to the right as it
    # climbs, so the outer contour at the top right is the hood's own curve
    top_f, start_f, lean, up = A_CURVES[A_CURVE]
    st = stem(x, 0, xh * top_f, top=None, foot='both', ent_span=(0, xh))
    peak = xh + OVER - PR.bowl_hair() / 2
    hood = cubic((x, xh * start_f), (x + lean * wf, xh * up), (x - 236 * wf, peak + 44), (x - 286 * wf, xh * 0.72))
    hd = stroke(hood, PR.bowl_widths(hood, widths([(0.0, 0.85), (0.22, 1.0), (0.75, 1.0), (1.0, 1.12)]), floor=S * 0.5), cut1=CUT)
    # the bowl's OUTER path (ccw): from inside the stem at 0.60 xh, a round
    # shoulder out to the left extreme at 0.30 xh, a round bottom, back
    # into the stem near the foot
    L = (x - 335 * wf, xh * 0.30); B = (x - 150 * wf, -OVER)
    xin = x + TH_V / 2 - TH_V * 0.35
    top = (xin, xh * 0.60)
    outer = join(cubic(top, (top[0] - 70 * wf, top[1] + 62), (L[0] + 6 * wf, L[1] + 150), L),
                 cubic(L, (L[0], L[1] - 120), (B[0] - 105 * wf, B[1]), B),
                 cubic(B, (B[0] + 85 * wf, B[1]), (xin, 15), (xin, 60)))
    outer_closed = geom.resample(outer + [outer[0]])[:-1]
    tans_o = geom.tangents(outer_closed, closed=True); n_o = len(outer_closed)
    NEAR_STEM_W = 40.0
    def wfn2(t):
        i = min(n_o - 1, int(round(t * n_o))); p = outer_closed[i]
        w = max(PR.bowl_th(tans_o[i]), S * 0.5)
        u = max(0.0, min(1.0, (p[0] - (xin - 90.0)) / 90.0)); u = u * u * (3 - 2 * u)
        return w * (1 - u) + NEAR_STEM_W * u
    solid, o, i = ring_from(outer, widths_fn=wfn2, counter_smooth=3, smooth_w=6)
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
    """G3 (rulings, rounds 40/42) -- redrawn 2026-09-13 (owner: the first
    cleanup "sucks"). What was wrong: the neck and the ear were PEN strokes,
    sticks at contrast 0.95; the loop was a flat ellipse much wider than the
    bowl; the ear a long thin bar. Now: the bowl a little smaller and
    rounder (rx 172 wf, 0.66 xh tall); the loop less flat (rx 200 wf, half
    height 0.50 desc) and closer under the bowl; the neck on the bowl
    profile with a 0.55 S floor, leaving the bowl at 240 deg and entering
    the loop at 150 deg; the ear a short heavy stroke off the shoulder at
    the bowl profile, floored at 0.72 S, rising 8 deg, ending in the pen
    cut -- the top-right serif of the round-30 ruling, with weight."""
    xh = c["xh"]; wf = c["wf"]; desc = c["desc"]
    rx = 172 * wf + TH_V / 2; ry = (xh * 0.66 + OVER * 2) / 2; cy = xh + OVER - ry; cx = rx + S * 0.35
    bowl, bo, bi = ring(cx, cy, rx, ry)
    lrx = 190 * wf + TH_V / 2; lry = desc * 0.50 + TH_H / 2; lcx = cx + 18 * wf; lcy = -desc * 0.50
    loop, lo, li = ring(lcx, lcy, lrx, lry)
    crx, cry = rx - TH_V / 2, ry - TH_H / 2; clrx, clry = lrx - TH_V / 2, lry - TH_H / 2
    def on(cx_, cy_, rx_, ry_, deg):
        a = math.radians(deg); return (cx_ + rx_ * math.cos(a), cy_ + ry_ * math.sin(a))
    p0 = on(cx, cy, crx, cry, 240); a1 = math.radians(150); p3 = on(lcx, lcy, clrx, clry, 150)
    tl = (-math.sin(a1), math.cos(a1)); gap = p0[1] - p3[1]
    # owner 2026-09-14: "clear out the inside counter of 'g' so it is an
    # uninterrupted oval" -- the neck and the ear used to START inside the
    # ring's centerline (22 up, 25 in), and their square start faces landed
    # in the counter. Both now begin ON the ring's centerline and taper in,
    # so nothing reaches the counter. And: "thin out the connector stroke
    # between ovals in g to match the calligraphic style" -- the neck on the
    # bowl profile with a G_NECK floor and a light middle.
    neck = cubic(p0, (p0[0] - gap * 0.05, p0[1] - gap * 0.58), (p3[0] - tl[0] * gap * 0.55, p3[1] - tl[1] * gap * 0.55), p3)
    nk = stroke(neck, PR.bowl_widths(neck, widths([(0.0, 0.30), (0.16, 0.9), (0.45, G_NECK_MID), (0.85, 0.9), (1.0, 0.30)]), floor=S * G_NECK))
    ex, ey = on(cx, cy, crx, cry, 44); L = 96 * wf * g_ear_scale()
    ear_c = [(ex, ey), (ex + L, ey + L * math.tan(math.radians(8)))]
    ear = stroke(ear_c, PR.bowl_widths(ear_c, widths([(0.0, 0.4), (0.35, 1.0), (1.0, 1.05)]), floor=S * 0.72), cut1=CUT)
    return geom.ink([bowl, loop, nk, ear])
