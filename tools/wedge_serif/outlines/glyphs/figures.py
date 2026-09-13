"""0-9, old-style, drawn at the height of their reference box (c['figH'];
the builder shifts each into its box, latin.FIG_BOX). The 8 on two rings
whose counters are both the o's optical circle, the lower sized to a
neighbour's bowl counter, as tall as the stack makes it (round 64; round 49
had the rings in the 6's proportion, round 63 bottom-heavy at the 6's
height), the 3's bottom after the 5's (round 44), the 6 and 9 with one
thinning stroke (round 42), the 2's base running past its body by the 9's
tail overhang (2026-09-13) and the 5's top ending FIVE_TOP_INSET from its
bowl (round 64)."""
import math
from . import glyph
from .. import geom, pen
from ..geom import cubic, line, superellipse, tangents, resample
from ..primitives import stem, ring, stroke, pen_widths, widths, diagonal, bar, wedge, end_wedge, bowl_hair, bowl_th
from ..pen import S, OVER, TH_V, TH_H, HAIR, CUT, BOWL_K, WL, WD, DROP
from .caps_straight import W_, pw
import latin   # the figure boxes: the 8 sizes its counters to the 6's or the 0's, drawn at THEIR heights

# Owner 2026-09-13: "extend the bottom of 2 and top of 5 to the right
# (visually the same overhang as 9's tail goes to the left)". The 9's tail
# tip sits 11 units left of its bowl's leftmost ink, measured on the built
# outline (raster at a 1000 px em reads 10: the cut corner's tip pixel falls
# under the threshold). The 2's base ends that far past its body's rightmost
# ink. The 5's top did too, for one round (63); see FIVE_TOP_INSET.
NINE_OVERHANG = 11.0

# Owner 2026-09-13, on round 63: "5 top was extended much too far, match the
# visual of 2's bottom." On the 2 the diagonal meets the base at its END, so
# 11 units of base past the neck reads as the stroke's own extent; on the 5
# the bar leaves the stem and hangs over the bowl, so the same 11 read as too
# far. Where the bar's rightmost ink ends, relative to the bowl's rightmost
# ink (units; negative = inside the bowl's extent, 0 = flush). Round 64 built
# the ladder -36 / -24 / -12 / 0; owner ruling 2026-09-13, round 64: "5 at
# -24 is best."
FIVE_TOP_INSET = -24.0

# Owner 2026-09-13, on round 64's first 8 (round 63's upper loop widened to
# a 1.036 counter at round 63's height came out WIDER than the lower loop):
# "remake 8 again but make it shorter so counters can match other numerals
# or optical circles." So the 8 is no longer sized to the 6's outer bowl or
# held to the ascending figures' height: BOTH counters are the o's optical
# circle (1.036 wide over tall, guide §3), the lower one the WIDTH of a
# neighbour's bowl counter, the upper a linear fraction of the lower, and
# the figure is as tall as the two stacked make it. Measured on the built
# outlines under the owner's pen (stem 84, contrast 0.95, spread included):
# the 0's counter 256.4 x 395.6, the 6's bowl 239.4 x 328.2, the 9's bowl
# 227.8 x 329.0. "The size of" a tall oval, for a circle, is taken as its
# WIDTH, so the 8 keeps its neighbour's width (410 against the 6's 412); an
# equal AREA would make the 8 456 wide and 654 tall, nearly the 6 again.
# The round-64 ladder: (A) the 6's counter, upper 0.85; (B) the 0's, upper
# 0.85; (C) the 6's, upper 0.75. Owner ruling 2026-09-13: "for 8, C wins but
# the bottom counter needs to be slightly taller. possibly matching the
# top's." So the LOWER counter keeps its width and grows taller than the
# circle by EIGHT_LOWER_TALL (1.0 = the 1.036 circle; the ladder built 1.04
# / 1.08 / 1.12, w/h 0.996 / 0.959 / 0.925), the figure taller by the same
# units, the upper counter unchanged at 1.036. Owner ruling 2026-09-13, on
# that ladder: "1.08 wins."
EIGHT_COUNTER_OF = '6'     # whose bowl counter the lower counter is sized to: '6' or '0'
EIGHT_LOWER = 1.0          # the lower counter's width, x that counter's width
EIGHT_UPPER = 0.75         # the upper counter, x the lower's WIDTH, linearly (width and height alike); ruled: C
EIGHT_LOWER_TALL = 1.08    # the lower counter's height, x the circle's (1.0 = 1.036 wide over tall)
EIGHT_COUNTER_WH = 1.036   # the counters wide over tall: the o's ruling (round 35); the lower then x EIGHT_LOWER_TALL

# Owner 2026-09-13 (round 64): "give me options for thickening 6 tail." The
# tail is the 6's one thinning stroke (round 42): the 26-degree nib's width
# at each tangent, and the run above the bowl heads up-right at ~40 degrees,
# close to the nib's angle, so it thins from 58 units where it leaves the
# bowl to 25 (0.30 S) at t 0.64 before the terminal's own taper (to 5 at
# the tip). A FLOOR on the pen's width, x the stem, applied before the
# profile as the 9's tail does it, so the buried start and the terminal
# taper are kept: 0 = the pen alone (today), 0.55 / 0.70 / 0.85 / 1.00 the
# round-64 ladder (from 0.70 up the whole run above the bowl sits on the
# floor). Owner ruling 2026-09-13: "floor 0.55 S = 46.2 units wins."
SIX_TAIL_FLOOR = 0.55

def fig_ring(cx, cy, rx_c, ry_c):
    return ring(cx, cy, rx_c + TH_V / 2, ry_c + TH_H / 2)

def zero_bowl(c, D):
    """The 0's ring at figure height D: (solid, outer, inner). Also the 8's
    reference counter when EIGHT_COUNTER_OF is '0'."""
    rx = W_(c, '0', 230)
    return fig_ring(rx + TH_V / 2, D / 2, rx, D / 2 + OVER - TH_H / 2)

def six_bowl(c, D):
    """The 6's bowl at figure height D: (solid, outer, inner), rx, r, ry.
    Also the 8's reference counter when EIGHT_COUNTER_OF is '6'."""
    rx = W_(c, '6', 230); r = D * 0.29; ry = r + OVER - TH_H / 2
    return fig_ring(rx + TH_V / 2, r, rx, ry), rx, r, ry

def counter_box(solid):
    """Bounds of a ring's counter (its one interior)."""
    p = solid if solid.geom_type == 'Polygon' else max(solid.geoms, key=lambda q: q.area)
    return list(p.interiors)[0].bounds

def ring_for_counter(cx, cy, cw, ch, w_scale=1.0):
    """The outer radii (rx, ry) of a ring whose COUNTER measures cw x ch,
    found by iteration: the counter is the pen's inward offset, unfolded and
    smoothed, and has no closed form. Six half-error steps; the response is
    near 1:1, so it settles in two."""
    rx = cw / 2 + bowl_th((0, 1)) * w_scale; ry = ch / 2 + bowl_th((1, 0)) * w_scale
    for _ in range(6):
        solid, o, i = ring(cx, cy, rx, ry, w_scale=w_scale)
        x0, y0, x1, y1 = counter_box(solid)
        rx += (cw - (x1 - x0)) / 2; ry += (ch - (y1 - y0)) / 2
    return rx, ry

@glyph('0')
def g_zero(c):
    D = c["figH"]
    solid, o, i = zero_bowl(c, D); return solid

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
    # the top ends FIVE_TOP_INSET from the bowl's rightmost ink (round 63 ran
    # it NINE_OVERHANG past; before that it ended 0.95 w, 72 units inside);
    # the square end and the hanging wedge's apex both sit at x1, so x1 is
    # the bar's rightmost ink
    x1 = geom.bbox(bw)[2] + FIVE_TOP_INSET
    top = bar(S * 0.3, x1, D, max(TH_H, S * 0.5), align='center', cut0=CUT, wedges=[('right', -1)])   # round 51: centred ON D, its top at D + 28
    return geom.ink([top, st, bw])

@glyph('6')
def g_six(c):
    D = c["figH"]
    (solid, o, i), rx, r, ry = six_bowl(c, D); cx = rx + TH_V / 2
    p0 = (cx - rx, r); tip = (cx + rx * 0.85, D - 10)
    top = cubic(p0, (p0[0], p0[1] + ry * 1.5), (tip[0] - rx * 0.55, tip[1] - rx * 0.75), tip)
    base = pen_widths(top); prof = widths([(0.0, 0.15), (0.06, 1.0), (0.65, 1.0), (1.0, 0.12)])
    t = stroke(top, lambda u: max(base(u), SIX_TAIL_FLOOR * S) * prof(u))   # the floor under the pen, the profile over both
    return geom.ink([solid, t])

@glyph('7')
def g_seven(c):
    D = c["figH"]; w = W_(c, '7', 440)
    return geom.ink([bar(0, w, D, max(TH_H, S * 0.5), align='top', cut1=CUT, wedges=[('left', -1)]), diagonal((w - S * 0.2, D - 10), (w * 0.3, 0), pw((w - S * 0.2, D - 10), (w * 0.3, 0)))])

@glyph('8')
def g_eight(c):
    """Two rings whose COUNTERS are both the o's optical circle
    (EIGHT_COUNTER_WH), the lower sized to a neighbour's bowl counter
    (EIGHT_COUNTER_OF, EIGHT_LOWER), the upper EIGHT_UPPER of it, the figure
    as tall as the stack makes it. Owner 2026-09-13, round 64: "remake 8
    again but make it shorter so counters can match other numerals or
    optical circles." (Round 49 had the rings in the 6's proportion and the
    8 read top heavy; round 63 made it bottom-heavy at the ascending
    figures' height with a 0.63 upper counter; round 64's first pass widened
    that counter to 1.036 at the same height and the upper loop came out
    wider than the lower.) Then, on C: "the bottom counter needs to be
    slightly taller. possibly matching the top's" -- EIGHT_LOWER_TALL
    stretches the lower counter's height at its width, the figure growing
    by the same units. Sides on the bowl profile as the 0's, no 0.9
    scaling. The two rings overlap by exactly the bowl's horizontal stroke,
    so the waist is ONE band and not two stacked strokes. The lower ring's
    bottom sits at -OVER as the 0's and the 6's do (the box shift then puts
    all three 28 under the baseline in the font); the top is wherever the
    stack puts it. The counters are sized as the BUILT outline has them, ink
    spread included, which is why build.INK_SPREAD is read here; the
    reference bowl is drawn by the 6's or the 0's own helper at that
    figure's own height, so it cannot drift from the neighbour."""
    from .. import build as _build     # lazy: build imports this module
    sp = _build.INK_SPREAD
    Dr = (latin.FIG_BOX[EIGHT_COUNTER_OF][0] - latin.FIG_BOX[EIGHT_COUNTER_OF][1]) * pen.CAP
    ref = six_bowl(c, Dr)[0][0] if EIGHT_COUNTER_OF == '6' else zero_bowl(c, Dr)[0]
    x0, y0, x1, y1 = counter_box(ref)
    bw2 = (x1 - x0 - 2 * sp) * EIGHT_LOWER              # the lower counter's width, as built
    bw1 = bw2 * EIGHT_UPPER
    cw2, ch2 = bw2 + 2 * sp, bw2 / EIGHT_COUNTER_WH * EIGHT_LOWER_TALL + 2 * sp     # drawn (pre-spread) targets
    cw1, ch1 = bw1 + 2 * sp, bw1 / EIGHT_COUNTER_WH + 2 * sp
    rx2, ry2 = ring_for_counter(0.0, 0.0, cw2, ch2)
    rx1, ry1 = ring_for_counter(0.0, 0.0, cw1, ch1)
    cx = rx2
    y2 = -OVER + ry2                                     # the lower ring's bottom at -OVER
    y1 = -OVER + 2 * ry2 - bowl_hair() + ry1             # over the lower by one bowl stroke
    lo, *_ = ring(cx, y2, rx2, ry2); up, *_ = ring(cx, y1, rx1, ry1)
    return geom.ink([up, lo])

# Owner 2026-09-13 (round 72), on round 71's ten serifed tails: "flag-diag
# wins but it needs to be have more space to the left like foot-left."
# Measured on the built outlines, owner's pen: foot-left and flag-diag both
# reach 12.4 units past the bowl's left ink (the tail-tip rule, "11" on the
# pen it was measured on) -- but foot-left reaches it ON THE BOTTOM LINE
# (its foot's tip), while flag-diag's leftmost is the wedge's apex 100-150
# units up, and at the bottom line its ink sits 35.6 RIGHT of the bowl's
# left: 48 units short of foot-left's foot. That is the space he saw. So the
# round-72 page built the tail 48 and 56 further left on that reading, and
# the owner, verbatim: "'flag-diag as built in round 71' wins but it needs
# to thin out on top of tail to give more space. my earlier instruction
# was increase that space above tail and it was misinterpreted." So the
# apex stays where round 71 put it (NINE_FLAG_REACH = the tail-tip rule)
# and the space is opened ABOVE the tail: the pocket between the tail's
# upper edge and the bowl. NINE_TAIL_TOP scales the tail's width under the
# bowl (from where it leaves the ring to the wedge; the buried taper inside
# the ring untouched), and ALL of the thinning is taken from the TOP edge:
# the centerline drops by half the thinning, so the bottom edge, the bottom
# line and the wedge's size and angle are round 71's. The 6's ruled floor
# (0.55 S = 46.2) holds for a step meant to sit above it -- 0.60 x 75.6 is
# 45.4, so that step sits ON the floor -- and is released for a step meant
# to go under it (0.45: 34). Round 72's ladder: 0.75 / 0.60 / 0.45. Owner
# ruling 2026-09-13: ".6 wins but the stroke needs to be thicker towards
# the loop." So the thinning is not uniform: the tail leaves the ring at
# round 71's full width and eases (smoothstep) down to NINE_TAIL_TOP over
# the first NINE_TAIL_EASE of the run from the ring exit to the wedge,
# the rest of the run at 0.60 -- heavier where it leaves the loop, lighter
# toward the tip, still all off the top edge, bottom line and wedge kept.
# 0 = the uniform 0.60 (a short ramp at the exit only). Round 72's ladder:
# 0.35 / 0.55 / 0.75; 0.55 until he picks.
NINE_FLAG_REACH = 12.4    # the wedge apex past the bowl's left ink: round 71's, the tail-tip rule as this pen draws it
NINE_TAIL_TOP = 0.60      # the tail's width at the wedge end, x round 71's, thinned from the top edge (1.0 = round 71); ruled
NINE_TAIL_EASE = 0.70   # ruled 2026-09-13, round 74: "eased over ~70% wins"     # fraction of the run (ring exit -> wedge) over which the width eases from 1.0 to NINE_TAIL_TOP
NINE_TAIL_MIN = 0.55      # the 6's ruled floor, x stem: holds while NINE_TAIL_TOP >= 0.5, released under it
NINE_BOTTOM = -7.3        # the round-42 tail's lowest spread ink, drawing coords (built -216.4 on the owner's pen); kept
NINE_FLOOR = 0.9          # the record's weight floor on the tail, x stem
NINE_TAPER = [(0.0, 0.15), (0.06, 1.0)]   # the tail's taper into the ring

def _walk_back(side):
    """edge_at for wedge(): the point `dist` back along a stroke's REAL side
    polyline from its end, so the bracket lands on the drawn edge."""
    pts = list(side)
    def f(dist):
        rem = dist; p = pts[-1]
        for q in reversed(pts[:-1]):
            seg = math.dist(p, q)
            if seg >= rem:
                u = rem / seg if seg else 0.0; return (p[0] + (q[0] - p[0]) * u, p[1] + (q[1] - p[1]) * u)
            rem -= seg; p = q
        return pts[0]
    return f

def _fit_left_bottom(make, target_left, bot, spread, iters=6):
    """Slide a tail's free tip until the glyph's leftmost SPREAD ink is at
    target_left and its lowest at bot, each within 0.05 unit (nines._fit)."""
    dx = dy = 0.0; g = None
    for _ in range(iters):
        g = make(dx, dy); x0, y0, _, _ = g.buffer(spread, join_style=2).bounds
        ex, ey = x0 - target_left, y0 - bot
        if abs(ex) < 0.05 and abs(ey) < 0.05: return g
        dx -= ex; dy -= ey
    return make(dx, dy)

@glyph('9')
def g_nine(c):
    """Round 71's flag-diag (owner, round 72: "flag-diag wins"): the round-42
    ring and tail -- the pen's width with the record's 0.9-stem floor,
    tapering into the ring -- the end face SQUARE across the tail at its
    own angle, and the family's diagonal end wedge (0.9 x 0.9, drop DROP;
    the A's, the V's) on the upper side, rising from the face's upper
    corner, its bracket back along the tail's real edge. The tip is fitted
    so the wedge's apex ends NINE_FLAG_REACH past the bowl's left ink on
    the BUILT outline (spread included; a sharp apex mitres out further
    than a blunt corner) and the lowest ink stays at NINE_BOTTOM. Round 72:
    the run under the bowl is NINE_TAIL_TOP of that width, thinned from the
    TOP edge (the centerline dropped by half the thinning; see the
    constants), so the pocket above the tail opens while the bottom edge,
    the bottom line and the wedge stay."""
    from .. import build as _build     # lazy: build imports this module
    from shapely.geometry import Point
    sp = _build.INK_SPREAD
    D = c["figH"]; rx = W_(c, '9', 230); r = D * 0.29; cx = rx + TH_V / 2
    solid, o, i = fig_ring(cx, D - r, rx, r)
    p0 = (cx + rx * math.cos(math.radians(-20)), D - r + r * math.sin(math.radians(-20)))
    target_left = (cx - rx - TH_V / 2 - sp) - NINE_FLAG_REACH
    tap = widths(NINE_TAPER)
    floor = S * NINE_TAIL_MIN if NINE_TAIL_TOP >= 0.5 else 0.0
    def make(dx, dy):
        tip = (cx - rx * 1.12 + dx, 22 + dy)
        tail = cubic(p0, (p0[0] - rx * 0.15, p0[1] - r * 1.5), (tip[0] + rx * 1.15, tip[1] + r * 0.55), tip)
        base = pen_widths(tail)
        wf = lambda u: max(base(u), S * NINE_FLOOR) * tap(u)            # round 71's width
        pts = resample(tail); tans = tangents(pts); n = len(pts) - 1
        t_exit = next((k / n for k in range(len(pts)) if k / n > 0.05 and not solid.contains(Point(pts[k]))), 0.3)
        if NINE_TAIL_EASE > 0: k_of = widths([(t_exit, 1.0), (t_exit + NINE_TAIL_EASE * (1.0 - t_exit), NINE_TAIL_TOP)])   # full at the exit, easing to the step's factor
        else: k_of = widths([(t_exit - 0.04, 1.0), (t_exit + 0.10, NINE_TAIL_TOP)])   # the uniform thinning: 1.0 inside the ring, the factor under the bowl
        def wf2(u):
            w = wf(u); return max(w * k_of(u), min(floor, w))
        center = []
        for k, (p, tn) in enumerate(zip(pts, tans)):                    # the thinning off the TOP edge: drop the centerline by half of it
            u = k / n; d = (wf(u) - wf2(u)) / 2
            ux, uy = -tn[1], tn[0]
            if uy < 0: ux, uy = -ux, -uy                                 # the upward normal
            center.append((p[0] - ux * d, p[1] - uy * d))
        t, A, B = stroke(center, wf2, raw=True, sides=True)
        up, lo = (A, B) if A[-1][1] >= B[-1][1] else (B, A)
        d = tangents(resample(tail))[-1]
        v = (up[-1][0] - lo[-1][0], up[-1][1] - lo[-1][1]); n = math.hypot(*v) or 1.0; sd = (v[0] / n, v[1] / n)
        flag = wedge(up[-1], d, sd, WL * 0.9, WD * 0.9, DROP, edge_at=_walk_back(up))
        return geom.ink([solid, t, flag])
    return _fit_left_bottom(make, target_left, NINE_BOTTOM, sp)
