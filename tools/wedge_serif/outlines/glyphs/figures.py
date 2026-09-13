"""0-9, old-style, drawn at the height of their reference box (c['figH'];
the builder shifts each into its box, latin.FIG_BOX). The 8 on two rings
whose counters are both the o's optical circle, the lower sized to a
neighbour's bowl counter, as tall as the stack makes it (round 64; round 49
had the rings in the 6's proportion, round 63 bottom-heavy at the 6's
height), the 3's bottom after the 5's (round 44), the 6 and 9 with one
thinning stroke (round 42), the 2's base running past its body by the 9's
tail overhang (2026-09-13) and the 5's top ending FIVE_TOP_INSET from its
bowl (round 64).

Round 75 (2026-09-13), one owner instruction per figure: the 1's flag ends
buried in the stem and takes the family's diagonal end wedge; the 2's neck
tapers into its diagonal and its base's wedged end loses the pen cut; the 3's
lower bowl opens halfway to the 5's; the 4 has an OPEN counter (FOUR_OPEN);
the 7's top right is one mitred corner; the 9's tail leaves the ring tangent
to it (NINE_JOIN_SINK). Each constant carries its measurement and its
rejected alternatives above it."""
import math
from . import glyph
from .. import geom, pen
from .. import primitives as PR
from ..geom import cubic, line, superellipse, tangents, resample, join
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

# Owner 2026-09-13 (round 75): "clean up stray marks and mismatch of '1' and
# '2'." The 1's flag ends this far INSIDE the stem, in stem widths, so its
# square face and both of that face's corners sit under the stem's own ink
# and the top face is the stem's alone (it ran 2 units past the top and
# printed a nub); and it takes the family's diagonal end wedge at its tip,
# which is the treatment the 2's base already had and the 1 had not.
ONE_FLAG_BURY = 0.35
ONE_FLAG_WEDGE = True
ONE_FLAG_WEDGE_SCALE = 0.32   # owner 2026-09-13: "1 needs a much smaller tip serif at top" -- a third of the family's 0.9 diagonal end

# Owner 2026-09-13 (round 75), the 2's half of the same ruling. Its base's
# free (right) end was CUT and WEDGED at once, and `bar` plants the wedge at
# the UNCUT corner: the pen cut pulls a bar's top-right corner back by
# tan(20) x half the bar (7.6 units) and pushes the bottom-right corner
# forward by the same, so the wedge's bracket stood past the real top corner
# and the cut's lower corner spiked out under it -- a notch and a spur, both
# visible at 600 px. The wedge IS the terminal there, so the cut goes.
#
# NOT changed, and checked rather than assumed: the base's LEFT end stays a
# square face with no wedge. That is the Z's own construction
# (`caps_straight.g_Z`: the bottom bar is `wedges=[('right', 1)]` and nothing
# at the left, because the diagonal lands there), and a left wedge was built
# and rejected on the render -- its rise met the diagonal's foot and opened a
# fresh V-notch between them, trading one stray for another.
TWO_BASE_CUT = False
# How far the diagonal's start is buried back into the arc's end, x the stem
# (the guide's join rule is a fifth to a third; the diagonal used to start ON
# the arc's centerline end and covered only half its end face, leaving a
# white nick in the outer corner of the join).
TWO_NECK_BURY = 0.44
# ...and the fraction of the arc's run over which it eases from full width to
# the diagonal's, so the bowl hands over instead of stopping.
TWO_NECK_TAPER = 0.18

# The 7's diagonal starts this far below the bar's top edge, in bar depths,
# so both corners of its square end face lie inside the bar's band (round 75).
SEVEN_DIAG_BURY = 0.45

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

# Owner 2026-09-13 (round 75): "give more of space at bottom curve of '3',
# halfway to 5." Measured on the built outlines (the ENCLOSED white of the
# lower bowl -- a white pixel with ink to its left and right on its row and
# above and below in its column, which is what an opened bottom curve
# changes) the 3's lower counter was 161 x 131 units and the 5's is
# 215 x 143; the mouths' narrowest necks were 43.2 and 45.0. Halfway is
# 188 x 137 with a 44-unit aperture, and these three numbers are the lower
# bowl solved onto it: its x radius as a fraction of the figure's width, its
# y radius as a fraction of the height, and where its sweep ends. The 3's
# bottom keeps the 5's sweep and terminal (the round-44 ruling) -- the width
# profile and the cut terminal are untouched, only the bowl they run on.
# Was 0.52 / 0.30; the sweep's end is unchanged at -156, which is the round-44
# ruling's terminal, and only the bowl it runs on grew. Solved: 187 x 137
# units, area 19,328 against the halfway target 188 x 137 / 19,448.
#
# The MOUTH came with it and could not be held back: the width solver pins the
# figure's total width, so the centre of the lower bowl is not an independent
# knob (0.44 / 0.52 / 0.60 all render byte for byte) and the only lever on the
# counter is the bowl's own radius, which opens the neck as it opens the
# counter. The neck goes 46.4 -> 55.1 units against the 5's 45.6. That is
# further than halfway, and it is the right direction anyway: 46.4 was BELOW
# the standing 0.6 S floor (50.4) and 55.1 is above it, so the 3's aperture was
# the one figure in breach and now is not.
THREE_BOT_RX = 0.62
THREE_BOT_R = 0.315
THREE_BOT_END = -156.0
THREE_BOT_CX = 0.52
THREE_W = 330.0   # the 3's nominal drawn width, before the builder's solved multiplier

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
    """Owner 2026-09-13: "clean up stray marks and mismatch of '1' and '2'."
    Two strays and one mismatch, all at the flag. (a) The flag's centerline
    ran to (x + 6, D + 2) -- 2 units ABOVE the stem's top face and 6 past
    its centre -- and its end face is square across a stroke climbing at
    ~40 degrees, so the face's upper corner rose ~25 units past the top and
    printed a pointed NUB out of the top-right of the stem (visible at 600
    px). The flag now ends BURIED inside the stem, on its axis at
    D - ONE_FLAG_BURY x the stem's width, so the union closes flush with a
    top face the stem alone draws. (b) The flag's tip was a bald sheared
    face -- the only free terminal in the figures with no serif of any
    kind, against the family's rule that a diagonal's end takes the
    0.9 x 0.9 wedge (A V W X Y, and the 9's own flag-diag). It takes that
    wedge now, on the UPPER side, which is (c) the mismatch with the 2: the
    2's base carries the family's bar-end wedge and the 1 carried nothing."""
    D = c["figH"]; x = 200 * c["wf"] + S / 2
    st = stem(x, 0, D, top=None, foot='both')
    path = line((x - 150, D * 0.72), (x, D - TH_V * ONE_FLAG_BURY))
    wf = pen_widths(path, lambda t: 0.85)
    parts = [st, stroke(path, wf, cut0=None if ONE_FLAG_WEDGE else CUT)]
    if ONE_FLAG_WEDGE:   # the 9's flag-diag construction: a square face across the stroke, the wedge off its UPPER corner
        parts.append(end_wedge(path, wf(0.0), True, 1, scale=ONE_FLAG_WEDGE_SCALE))
    return geom.ink(parts)

@glyph('2')
def g_two(c):
    """Owner 2026-09-13: "2 needs another pass to tidy up stray marks and
    flow the top right into the slash into the bottom." So the 2 is ONE
    stroke from the arc's start, round the top, down the slash and into
    the base's left end -- no separate diagonal, no neck join, nothing to
    leave a stray mark. The centerline: the round-49 superellipse arc,
    continued by a cubic that leaves the arc on its own tangent, bows down
    to the left and arrives at the base's left end running horizontally
    into it. Widths on the bowl profile (the pen's thin is the 6-unit
    floor at this contrast): heavy on the arc's right, easing to the
    slash's weight, easing back up into the base. The base is the family's
    bar with its right-end wedge (round 77: wedge alone, no cut), the
    stroke's end buried in it."""
    D = c["figH"]; w = W_(c, '2', 440); rx = w * 0.46
    top = superellipse(rx, D - rx * 0.95, rx, rx * 0.95, math.radians(190), math.radians(TWO_ARC_END_DEG), BOWL_K)
    barw = max(TH_H, S * 0.5)
    tipd = top[-1]; at = tangents(top)[-1]
    foot = (S * 0.55, barw * 0.5)                       # the base's centerline, a little in from its left end
    seg = math.hypot(tipd[0] - foot[0], tipd[1] - foot[1])
    c1 = (tipd[0] + at[0] * seg * TWO_SLASH_LEAVE, tipd[1] + at[1] * seg * TWO_SLASH_LEAVE)
    c2 = (foot[0] - seg * TWO_SLASH_LAND, foot[1] + barw * 0.1)   # arrive running right along the base
    slash = cubic(tipd, c1, c2, foot)
    center = join(top, slash)
    # where along the whole stroke the arc ends (by arc length), for the widths
    def _len(pts): return sum(math.hypot(q[0] - p_[0], q[1] - p_[1]) for p_, q in zip(pts, pts[1:]))
    f_arc = _len(top) / max(_len(center), 1e-6)
    prof = widths([(0.0, 1.15), (0.15, 1.0), (max(0.0, f_arc - 0.08), 1.0), (min(1.0, f_arc + 0.12), TWO_SLASH_W),
                   (0.90, TWO_SLASH_W), (1.0, 1.0)])
    body = stroke(center, PR.bowl_widths(center, prof, floor=S * 0.5), cut0=CUT)
    x1 = geom.bbox(body)[2] + NINE_OVERHANG
    return geom.ink([body, bar(0, x1, 0, barw, align='bottom', wedges=[('right', 1)])])

# the 2 as one stroke (2026-09-13): where the arc hands over to the slash
# (degrees on the superellipse, -25 was round 49's), how far the slash
# keeps the arc's tangent (x the slash's chord) and how far before the foot
# it is already horizontal, and the slash's weight (x the bowl profile).
TWO_ARC_END_DEG = -20
TWO_SLASH_LEAVE = 0.30
TWO_SLASH_LAND = 0.42
TWO_SLASH_W = 0.72

@glyph('3')
def g_three(c):
    D = c["figH"]; w = W_(c, '3', THREE_W); r1 = D * 0.20; r2 = D * THREE_BOT_R
    top = superellipse(w * 0.52, D - r1, w * 0.46, r1, math.radians(165), math.radians(-105), BOWL_K)
    bot = superellipse(w * THREE_BOT_CX, r2, w * THREE_BOT_RX, r2 + OVER - TH_H / 2,
                       math.radians(100), math.radians(THREE_BOT_END), BOWL_K)
    t = stroke(top, pen_widths(top, widths([(0.0, 1.1), (0.1, 1.0), (0.88, 1.0), (1.0, 0.4)])), cut0=CUT)
    b = stroke(bot, pen_widths(bot, widths([(0.0, 0.4), (0.1, 1.0), (0.85, 1.0), (1.0, 1.25)])), cut1=CUT)
    return geom.ink([t, b])

# Owner 2026-09-13 (round 75): "make a slightly altered 'open' version of
# '4'." The closed 4 runs its diagonal from the stem's own top corner, so the
# bar and the two strokes shut the triangle at every corner. The OPEN 4 lifts
# the diagonal's TOP END clear of the vertical: the counter's top-left corner
# is left ajar by FOUR_OPEN_GAP x the stem, measured as the shortest distance
# from the diagonal's end face to the stem's ink (0.6 S = 50.4 units, 2.7 px
# at 13 pt -- an aperture, so it is held at or above the standing 0.6 S floor
# and not below it). Nothing else moves: the diagonal keeps its angle, its
# width and its foot on the bar, and the bar and the stem are untouched.
# FOUR_OPEN = False restores the closed construction byte for byte.
FOUR_OPEN = True
FOUR_OPEN_GAP = 0.62       # x the stem, the gap at the top-left corner: 0.6 S is the standing aperture floor (50.4) and the cut's facets shave ~0.4 off the built gap, so the drawn number is a shade over


@glyph('4')
def g_four(c):
    """Owner 2026-09-13: "research how open 4 numerals can be done with
    curved top left stroke." Measured on the references on disk: Berkeley
    Oldstyle, Miju Goudy (Goudy Oldstyle) and Cheltenham draw the open 4's
    top-left as ONE stroke that leaves the top thin, bows down and to the
    left, and rounds into the bar with no corner, standing clear of the
    stem; Dante, EB Garamond, Doves and Van den Keere keep a straight thin
    diagonal, also clear of the stem. This is the Goudy way
    (`FOUR_CURVED`): a cubic from a start clear of the stem's left edge by
    FOUR_OPEN_GAP x S, bowing left (FOUR_BOW), arriving at the bar's left
    end running right along it; widths on the bowl profile, thin at the
    start (a pen cut), full by a quarter of the run, merging into the bar.
    FOUR_CURVED False keeps round 77's straight open diagonal; FOUR_OPEN
    False the closed 4."""
    D = c["figH"]; w = W_(c, '4', 480); xs = w * 0.7
    barw = max(TH_H, S * 0.5); bar_y = D * 0.3
    st = stem(xs, 0, D, top=None, foot='both')
    b = bar(0, w, bar_y, barw)
    if FOUR_OPEN and FOUR_CURVED:
        x_edge = xs - TH_V / 2
        p0 = (x_edge - S * FOUR_OPEN_GAP - S * 0.28, D - 4)     # the start's centre, its half width past the gap
        p3 = (S * 0.45, bar_y)                                  # the bar's left end, on its centerline
        c1 = (p0[0] - S * FOUR_BOW, D * 0.66)
        c2 = (p3[0] - S * 0.35, bar_y + barw * 0.1)
        curve = cubic(p0, c1, c2, p3)
        prof = widths([(0.0, 0.5), (0.25, 1.0), (0.88, 1.0), (1.0, 0.95)])
        dg = stroke(curve, PR.bowl_widths(curve, prof, floor=S * 0.5), cut0=CUT)
        return geom.ink([dg, b, st])
    p1 = (S * 0.1, bar_y); p0 = (xs - S * 0.2, D)
    wd = pw(p0, p1, 0.75)
    dg = diagonal(p0, p1, wd)
    if FOUR_OPEN:
        from .. import build as _build     # lazy: build imports this module
        ux, uy = p0[0] - p1[0], p0[1] - p1[1]; L = math.hypot(ux, uy) or 1.0
        ux, uy = ux / L, uy / L
        want = S * FOUR_OPEN_GAP + 2 * _build.INK_SPREAD; back = want
        for _ in range(8):
            q = (p0[0] - ux * back, p0[1] - uy * back)
            dg = diagonal(q, p1, wd); got = dg.distance(st)
            if abs(got - want) < 0.05: break
            back += (want - got) / max(ux, 0.25)
    return geom.ink([dg, b, st])

FOUR_CURVED = True      # the Goudy open 4: a bowed stroke rounding into the bar (owner 2026-09-13)
FOUR_BOW = 0.22         # how far left of the start the bow's upper control sits, x S

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
    """Owner 2026-09-13 (round 75): "clean up top right of '7'." The corner
    was three separate faces fighting: the bar's right end sheared by the pen
    cut (which, at the END of a stroke, pulls the TOP corner back and pushes
    the BOTTOM one forward), the diagonal's square start face at its own
    ~68-degree angle, and the diagonal's right edge, which is wider than the
    bar is long and stood ~23 units past the bar's end. The silhouette went
    out, in, out and in again -- a spur with two re-entrant notches, plainly
    visible at 600 px and present before the cut, so it is construction and
    not a facet.

    The guide's wedge table gives the 7 a hanging wedge at the bar's LEFT end
    and nothing at the right, so the right is a MITRE: the bar's end face is
    cut parallel to the diagonal and laid exactly ON the diagonal's right
    edge, and the bar's length is solved so the two coincide. One corner,
    where the bar's top edge meets the diagonal's right edge. The diagonal
    starts inside the bar's band (SEVEN_DIAG_BURY of the bar's depth below
    its top edge) so both corners of its square face are buried."""
    D = c["figH"]; w = W_(c, '7', 440); barw = max(TH_H, S * 0.5)
    p1 = (w * 0.3, 0); p0 = (w - S * 0.2, D - barw * SEVEN_DIAG_BURY)
    wd = pw(p0, p1)
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]; L = math.hypot(dx, dy) or 1.0
    ux, uy = dx / L, dy / L; nx, ny = -uy, ux          # the up-right side of a stroke running down-left
    ex, ey = p0[0] + nx * wd / 2, p0[1] + ny * wd / 2  # a point on the diagonal's right edge
    yc = D - barw / 2                                  # the bar's centerline (align='top')
    x1 = ex + ux * (yc - ey) / uy                      # where that edge crosses it: the bar's end
    mitre = -math.atan2(abs(dx), abs(dy))              # the end face parallel to the diagonal
    return geom.ink([bar(0, x1, D, barw, align='top', cut1=mitre, wedges=[('left', -1)]),
                     diagonal(p0, p1, wd)])

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
# Owner 2026-09-13 (round 75): "attach '9' on the right better." Measured on
# the built outline, scanning the right silhouette every 2 units of y: the
# ring's outer edge falls monotonically to x 381.56 at y 162.6 and the tail's
# outer edge then picks it up at 385.58 -- a 4.0-unit RE-ENTRANT NOTCH,
# the tail leaving the loop 4 units OUTSIDE the ring's own silhouette instead
# of tangent to it, with a nick in the corner where the two edges cross. The
# tail's start (its centerline point on the ring, at -20 degrees) is sunk this
# far along both of the ring's radii, which moves the whole departure inward
# until the two edges leave as one. Nothing else about the tail moves: the
# ruled constants below are untouched, `_fit_left_bottom` puts the tip back on
# its ruled leftmost and lowest, and the width under the bowl is what round
# 72-74 ruled. 0 = the round-71 attachment.
NINE_JOIN_SINK = 8.0

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
    p0 = (cx + (rx - NINE_JOIN_SINK) * math.cos(math.radians(-20)),
          D - r + (r - NINE_JOIN_SINK) * math.sin(math.radians(-20)))
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
