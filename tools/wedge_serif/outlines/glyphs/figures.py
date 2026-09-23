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
import math, os, os
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
ONE_FLAG_WEDGE_SCALE = 0.15   # owner 2026-09-13: "1 needs a much smaller tip serif at top", then "reduce the top spur on 1 into a microserif" -- a sixth of the family's 0.9 diagonal end
# ROUND 233 (R34), owner 2026-09-18 on the roman 1's flag: *"remove errant
# flick."* The microserif above IS the flick. `end_wedge(scale=0.15)` scales
# the wedge's length to 9.4 and its depth to 18.8 but NOT its drop -- `wedge`
# takes DROP whole, 23 units -- so the apex lands 23 back along the flag's
# underside and only 9 out from it. Measured on the built outline: from the
# face's lower corner (42, 287) a 30-unit sliver 2-5 units thick runs to
# (72, 291) and back to (56, 296), under the flag. That sliver is gone. What
# did NOT move: the flag's stroke and its square end face are byte-identical
# (the face was the wedge's seat and is what every sheet since round 75 has
# shown); the stem and the feet are untouched. Roman only -- the italic's flag
# is round 217's curve and never carried the wedge -- so `pen.ITALIC` keeps the
# old expression there.
ONE_FLAG_FLICK = False

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
SEVEN_BAR_W = float(os.environ.get("ALBO_ALD_SEVEN_BAR_W", 1.28))    # x the bar's own depth
SEVEN_DIAG_W = float(os.environ.get("ALBO_ALD_SEVEN_DIAG_W", 0.76))  # x the pen's width on the diagonal

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
EIGHT_FLOOR = 0.65         # round 98b (owner 2026-09-14: "yes to c"): the hairs at 11 and 5 o'clock never under 0.65 S, counters untouched, ink +5.6%. (0.55, his first pick, sat under the bowl hair's 0.554 and bound nothing.)
EIGHT_CSM = 2          # unchanged: smoothing does not cure the pinch (see EIGHT_CON)
EIGHT_FLOOR_IT = EIGHT_FLOOR   # unchanged: the floor was measured not to bind (see EIGHT_CON)
# ROUND 195 -- THE 8'S CONTRAST, AND WHY THE EXPONENT DOES NOT SHIP.
# Owner 2026-09-17: *"add line contrast to 8."* Measured against Coelacanth the
# figure is nearly monolinear -- 1.69:1 against its 3.59:1, thins of 52 units
# where the reference's are 23.
#
# TWO THINGS WERE RULED OUT BY MEASUREMENT, in this order:
#   the HAIR FLOOR is not what binds it. EIGHT_FLOOR 0.65 -> 0.50 -> 0.40 ->
#   0.32 moved the contrast 1.63 -> 1.69 and then stopped, because the family's
#   bowl profile never asks for anything thinner than that.
#   the CONTRAST EXPONENT reaches the number and ruins the letter. `ring(con=)`
#   re-spreads the ring's own widths about their geometric mean and gets 2.04,
#   2.22 and 2.55 at 1.6, 1.9 and 2.3 -- and at every one of them the COUNTER
#   necks into a kidney shape at the sides, because `ring` offsets the counter
#   inward by the width at each point and a width swinging twice as far swings
#   the inner contour with it. counter_smooth 2, 7 and 14 all render the same
#   pinch: it is not a sampling artifact, the counter genuinely necks.
#
# WHAT THAT MEANS, and it is this session's own lesson arriving at another
# letter: Coelacanth does not get 3.59:1 from a deeper bowl profile. It gets it
# from the PEN -- thin where the stroke runs along the nib's edge, thick where
# it runs across -- which varies the width without ever pinching a counter,
# because the thin and the thick land where the stroke's DIRECTION puts them
# rather than wherever a profile says. The g's rings were moved onto the pen in
# round 182 for exactly this reason and the 8's want the same treatment.
#
# So EIGHT_CON ships at 1.0 and the letter is unchanged. `ring(con=)` stays --
# it is inert at 1.0, every existing caller is byte-identical, and it is the
# arm that measured all of the above.
EIGHT_CON = 2.1        # the italic 8's contrast exponent. 1.0 until round 211: the ring could not carry one until `oval` made its counter an ellipse
# ROUND 212 -- AND ITS WEIGHT, AGAINST THE 6. Owner 2026-09-18: *"match weight
# of 8 and 7 to 6."* Measured on the built italic: the 6's stroke runs 53.4
# units, the 8's 64.0 (+20%) and the 7's 41.4 (-23%). This scales both of the
# 8's rings; the 7's two dials go the other way. Italic only.
EIGHT_W_IT = 0.70      # x the ring's stroke weight
# the 7's half of the same ruling. SEVEN_BAR_W and SEVEN_DIAG_W are SHARED with
# the roman -- changing their defaults moved the roman's 7, which a build diff
# caught -- so the italic takes its own pair.
# ROUND 215 -- THE 1'S FOOT IS BRUSHED, NOT SLABBED. Owner 2026-09-18:
# *"change big serif on 1 to brushed."* The stem's foot='both' draws the
# family's chiselled bracket, and in the italic the right half is already
# replaced by the calligraphic exit (round 103) -- so what was left was one
# long pointed slab sweeping LEFT, twice the reach of anything else on the
# italic's baseline and the only slab foot among the figures. Brushed is the
# s's and the 7's idiom: the serif IS the stroke, the pen simply pressing as
# it lands. BRUSH is the foot's width over the stem's; BRUSH_H is how far up
# the press reaches, x S. 1.0 restores the wedge.
# ROUND 217 -- THE 1'S FLAG IS A CURVE. Owner 2026-09-18: *"turn top left
# stroke of 1 to simple thick curve."* It was a straight run on the bowl
# profile with the family's diagonal end wedge at a sixth (his round-75
# microserif). CURVE is the bow, as a fraction of the flag's own chord, applied
# perpendicular to it -- positive bows the stroke UP and away from the stem, the
# way a pen arrives; W is the profile multiplier; TIP is the width at the far
# end over the width at the stem, so the thick end can be the one the reader
# sees. "Simple" is the wedge: the italic drops it, because a microserif on the
# end of a curve is the finial he ruled out on the s in round 209. Italic only;
# 0 restores the straight flag exactly.
# ROUND 218 -- AND THE EXIT IS SHORTENED. Owner 2026-09-18: *"reduce length of
# bottom right serif."* The 1's bottom right is the calligraphic exit flick
# round 103 put on every italic stem, at S x pen.IT_EXIT. That dial is the
# FAMILY's -- every i, m, n and u foot is drawn from it -- so this scales the
# 1's alone through stem(it_exit_len=...), which is a new parameter for exactly
# this and defaults to 1.0 everywhere else.
ONE_EXIT_LEN = float(os.environ.get("ALBO_ALD_ONE_EXIT_LEN", 0.70))
ONE_FLAG_CURVE = float(os.environ.get("ALBO_ALD_ONE_FLAG_CURVE", -0.18))
ONE_FLAG_W = float(os.environ.get("ALBO_ALD_ONE_FLAG_W", 1.15))
ONE_FOOT_BRUSH = float(os.environ.get("ALBO_ALD_ONE_FOOT_BRUSH", 1.45))
ONE_FOOT_BRUSH_H = float(os.environ.get("ALBO_ALD_ONE_FOOT_BRUSH_H", 0.20))
SEVEN_BAR_W_IT = float(os.environ.get("ALBO_ALD_SEVEN_BAR_W_IT", 1.65))
SEVEN_DIAG_W_IT = float(os.environ.get("ALBO_ALD_SEVEN_DIAG_W_IT", 1.02))
# ROUND 213 -- WHERE THE FOOT LANDS. Owner 2026-09-18: *"make 7 tail centered
# and taper more like 6."* Measured on the built italic, the foot sits at 0.06
# of the figure's own ink width -- hard against its left edge -- where the 6's
# is 0.25, the 1's 0.28 and the 4's 0.38. Italic only; the roman's 7 keeps its
# 0.30 of w.
SEVEN_FOOT_X = float(os.environ.get("ALBO_ALD_SEVEN_FOOT_X", 0.30))
# ROUND 219 -- THE 7'S STROKES MODULATE. Owner 2026-09-18: *"adjust 7's strokes
# so it varies pleasantly and fitting rest of font."* Measured
# (`cmp_weight_survey.py`), the 7 was the most MONOLINEAR glyph in the italic:
# its thin (the 10th percentile of thickness along the centreline) read 51.2
# against a stroke median of 54.2 -- a ratio of 0.94, where the o is 0.40, the
# 6 0.42 and the a 0.46. It had almost no thin anywhere, because the bar was a
# constant-width slab and the diagonal held one width for 84% of its run.
# BAR_MOD is the bar's width at its RIGHT end over its left, the wedge end
# keeping SEVEN_BAR_W_IT; the LEG is thinned instead by starting its existing
# taper far earlier (SEVEN_TAIL_FROM 0.84 -> 0.55), which is monotone and so
# cannot grow the knee a local waist does. 1.0 is the flat bar.
SEVEN_BAR_MOD = float(os.environ.get("ALBO_ALD_SEVEN_BAR_MOD", 0.55))
# ROUND 215 -- AND THE FOOT TAKES A BRUSHED SERIF. Owner 2026-09-18: *"212
# wins but needs serif on end."* Round 214's answer was the family's chiselled
# end WEDGE stuck on the foot, and it went out with the rest of that round.
# This is the s's idiom instead (round 209, his ruling: *"serif needs to hang
# low off of current brush stroke, not be a weird finial"*): the serif is not
# an object added to the stroke, it IS the stroke -- the pen thins to its
# waist and then presses back out as it lands, so the foot spreads out of the
# taper with no join to see. FLARE is the foot's width over the waist's;
# FLARE_T is where along the run the waist sits, so the spread happens after
# it. 1.0 is the plain tapered end.
SEVEN_FOOT_FLARE = float(os.environ.get("ALBO_ALD_SEVEN_FOOT_FLARE", 1.45))
SEVEN_FOOT_FLARE_T = float(os.environ.get("ALBO_ALD_SEVEN_FOOT_FLARE_T", 0.94))
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
# ROUND 211 -- THE ITALIC'S TAILS ALL END THE WAY THE 6'S DOES. Owner
# 2026-09-18: *"make bottom tail of 7 into a vertical taper like 6, change
# tails of 3 5 9 to match their version of 6's tail."* The 6's tail is a pen
# stroke whose profile runs out to 0.12 at the tip; the 3's and the 5's
# terminals THICKEN to 1.25 and take a cut, the 7's lower stroke is a constant
# width diagonal, and the 9's ends on a sheared face with a wedge flag. Each of
# these is the roman's drawing and each is gated on `pen.ITALIC`, the same
# lever the 9's end cut already uses -- at 0 the roman is untouched.
THREE_TAIL_END = float(os.environ.get("ALBO_ALD_THREE_TAIL_END", 0.45))  # italic: the bottom terminal's width at its tip (0 = the roman's 1.25 and a cut)
FIVE_TAIL_END  = float(os.environ.get("ALBO_ALD_FIVE_TAIL_END",  0.45))  # italic: the same on the 5
SEVEN_TAIL_TAPER = float(os.environ.get("ALBO_ALD_SEVEN_TAIL_TAPER", 0.58))  # italic: the diagonal's width at its foot (0 = the constant-width diagonal)
SEVEN_TAIL_FROM = float(os.environ.get("ALBO_ALD_SEVEN_TAIL_FROM", 0.55))   # where the taper starts, t along the diagonal
# ROUND 212 -- AND IT CURVES INTO THE VERTICAL. Owner 2026-09-18: *"curve 7
# tail to be vertical and less thin so quickly."* The lower stroke was a
# straight run at the diagonal's own angle; this bends it so it ARRIVES
# vertical at the foot -- a cubic whose first handle keeps the diagonal's
# direction and whose second stands straight above the foot, so the top half is
# the diagonal it always was and only the last part turns.
SEVEN_TAIL_CURVE = float(os.environ.get("ALBO_ALD_SEVEN_TAIL_CURVE", 1.00))  # 0 = the straight run; 1 = fully upright at the foot
SEVEN_TAIL_HOLD = float(os.environ.get("ALBO_ALD_SEVEN_TAIL_HOLD", 0.60))   # how long the first handle holds the diagonal's own line before the bend
SEVEN_TAIL_RISE = float(os.environ.get("ALBO_ALD_SEVEN_TAIL_RISE", 0.55))   # the second handle's length straight above the foot, x the chord: this is what actually makes the foot vertical
NINE_TAIL_END = float(os.environ.get("ALBO_ALD_NINE_TAIL_END", 0.35))    # italic: taper the tail out instead of ending it on a flag

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
# THE 3'S OPTIONS.
# (b) NARROWER, onto the face's OWN declared target. `build.solve_widths` aims
# each figure's ink at `round20.REF['3']['w'] x CAP x WIDTH` = 313 units and
# the roman's 3 is built at 362 -- 15.6% over -- because the width multiplier
# is clamped at 0.70 and the 3 sits on that clamp. Only the drawn width can
# take it the rest of the way. At 282 it lands on 313, which is Georgia's
# 0.899 of the 0's advance and Poetica's 0.845 rather than today's 0.826 -- so
# it also OPENS the pair `3` makes with its neighbours, which is the round-216
# measure. (NOTE: an earlier note in this file records the 3's bowl centre as
# a dead knob, "0.44 / 0.52 / 0.60 all render byte for byte". That was true
# while the solver still had room; on the clamp the drawing is what shows.)
# (c) TWO BOWLS MORE ALIKE, which is Georgia's 3 and Big Caslon's: today the
# upper bowl's radius is 0.20 of the figure's height against the lower's
# 0.315, so the 3 reads as a small hook over a big bowl. 0.255 evens them
# without touching the round-75 aperture ruling on the lower one.
THREE_OPT = {
    'b': dict(W=282.0),
    'c': dict(top_rx=0.545, top_cx=0.515),
    # ROUND 233 (R38): the waist's tip, roman only -- 'a' is the fixed flat
    # (below), these are the other two defensible drawings of the same waist
    'd': dict(waist='point'),                   # a POINTED waist: both strokes run out to one point, the pen's reversal
    'e': dict(waist='beak'),                    # the flat face with a small lip hanging from its lower corner, the C's beak idiom
    # ROUND 255 (owner 2026-09-19, "optically balanced with rest of numerals"),
    # roman only, all three on e's beak waist, which ships (round 250). What is
    # measurably off on the 3 is not its weight -- its ridge stroke is 75.3
    # against the shipped 0 1 5 6 9's median 74.5 -- but its UPPER BOWL.
    # Measured on a 1000-unit-x-height raster (`shape.py`, round's scratch):
    #                    upper/lower lobe width   upper counter, of the width
    #   Georgia              0.90                    0.53
    #   Flanker              0.97                    0.53
    #   Pagella              1.02                    0.55
    #   Big Caslon           1.04                    0.59
    #   Poetica              1.14                    0.53
    #   Coelacanth           1.20                    0.56
    #   Albo 3e (today)      0.84                    0.37
    # Every reference's upper counter is 0.53-0.59 of the figure's width;
    # Albo's is 0.37 -- a hook over a bowl, which is what option c was drawn
    # against and e was not. These are c's width lever on e's waist, laddered:
    # the upper bowl's x radius 0.50 / 0.545 / 0.60 of the width (today 0.46),
    # its centre moved right with it so the bowl's right edge stays inside the
    # lower's (0.52 + 0.62 = 1.14 w) and the solved width does not grow. The
    # sweep's end lands 0.375-0.40 w either way, so the round-233 waist joins
    # both strokes at one T as before.
    'f': dict(waist='beak', top_rx=0.50, top_cx=0.51),      # halfway: the upper counter to ~0.45 of the width
    'g': dict(waist='beak', top_rx=0.545, top_cx=0.515),    # option c's bowl on e's waist: the upper within a tenth of the lower (Georgia, Flanker)
    'h': dict(waist='beak', top_rx=0.60, top_cx=0.53),      # the upper AS WIDE as the lower (Pagella, Big Caslon)
}
THREE_OPT_IT = {k: THREE_OPT[k] for k in ('b', 'c')}   # the italic's waist is untouched (its lower terminal is round 211's run-out)
# ROUND 233 (R38), owner 2026-09-18 on the roman 3: *"redo middle stem."* The
# middle stroke -- the arm at the waist -- was two thin square-faced ends lying
# on each other: the upper bowl's end at (90.8, 396.7) heading 166 degrees, 24.3
# wide, and the lower bowl's start at (93.1, 399.5) heading 9.7 degrees, 14.7
# wide, 3.6 units apart, their faces at different angles. The union's tip was
# the upper's face with the lower's smaller face poking 1-2 units out of its
# top corner (a nick at 300 px), and the arm's top edge was the LOWER stroke's
# thickening edge -- so the arm read as a blunt chisel, 26 units at the end.
# NOW the two strokes meet at ONE point T (the midpoint of the two old ends)
# and both run out to 0.04 of the pen there, so the tip is a cusp with no face
# to mismatch; the flat face ('a') is then cut across both at once,
# THREE_WAIST_FLAT right of T, so it is one vertical face -- the lower's rising
# top edge and the upper's falling bottom edge are the only two edges leaving
# it. What did NOT move: both bowls' shapes, the top terminal, the lower
# terminal and its cut, the width profiles away from the last 4.5% of the upper
# stroke and the first 10% of the lower.
THREE_WAIST_FLAT = 14.0    # the flat face stands this far right of T; ~22 units tall there, the old face was 26
# WHY OPTION c WIDENS THE UPPER BOWL RATHER THAN DEEPENING IT, which is what
# it did for two builds. The upper bowl's radius sets where its sweep ENDS,
# and that end has to land on the lower bowl's start (0.41 w, 0.63 D) or the
# two terminals fork and leave a white slit at the waist -- which is exactly
# what a top_r of 0.240 produced, visible at 620 px as two prongs. The ellipse
# cannot be made taller and still reach that point: at r1 = 0.24 D its lowest
# point is 0.52 D, below the junction, and no sweep angle recovers it. r1 is
# therefore pinned by the junction at ~0.20, and the only axis left is WIDTH.
# 0.545 w against today's 0.46 w brings the upper bowl to within a tenth of
# the lower's 0.62 w, which is the proportion Georgia's 3 and Big Caslon's
# have and Albo's has not.

# ROUND 211 -- THE ITALIC'S FIGURES GET A CUT AND AN AXIS. Owner 2026-09-18:
# *"add appropriate line contrast and axis to 8 0 2 9 in italic"*. The italic's
# figures are the ROMAN's drawings sheared at build time, so they carry the
# roman's stress: measured, the 0 reads 1.67 thick-to-thin and the 8 1.68 where
# this italic's round letters run 2.88 and its o 4.61. FIG_CON re-spreads a
# ring's widths about their geometric mean (the ratio goes to the power of it)
# and FIG_STRESS rotates the NIB the widths are read from, which is what moves
# the axis without turning the letter. Both are italic-only and both are 0 for
# the roman.
FIG_CON = float(os.environ.get("ALBO_ALD_FIG_CON", 1.8))       # italic: the rings' contrast exponent
FIG_STRESS = float(os.environ.get("ALBO_ALD_FIG_STRESS", -30.0))  # italic: the nib's angle for them, degrees
FIG_OVAL = float(os.environ.get("ALBO_ALD_FIG_OVAL", 1.0))      # italic: pull the rings' counters onto their own ellipse
# The 9's ring takes its OWN contrast, because its counter is the one a tail
# crosses: at the figures' 1.8 the wall thins where the tail leaves and the
# tail's upper edge bites a notch out of the counter -- visible at 380 px and
# not curable by the ovalise, since the biting ink is the tail's and not the
# ring's. Lower here, and the notch closes without the other three moving.
# ROUND 212 -- THE 2'S BAR DROPS TO THE 4'S. Owner 2026-09-18: *"lower the
# crossbar of 2 from baseline to where the crossbar of 4 is."* Measured on the
# built italic, ink-weighted over the rows each bar occupies: the 2's base bar
# centres at +43 and the 4's crossbar at +7.3, so the drop is 36 units. The
# slash's foot goes down with it, or the stroke stops short of its own bar.
# Italic only; the roman's 2 keeps the baseline.
TWO_BAR_DROP = float(os.environ.get("ALBO_ALD_TWO_BAR_DROP", 42.0))
NINE_RING_CON = float(os.environ.get("ALBO_ALD_NINE_RING_CON", 0.0)) or None
NINE_RING_OVAL = float(os.environ.get("ALBO_ALD_NINE_RING_OVAL", -1.0))
NINE_RING_OVAL = None if NINE_RING_OVAL < 0 else NINE_RING_OVAL

# ============================== THE OPTIONS ==============================
# Owner 2026-09-18: *"improve both 7s"*, *"redo all numerals to fit together
# and read well in long numbers"*, *"subagent to remake numerals based on
# reference fonts that have old style figures and give me multiple options for
# each to choose from."*
#
# ONE DIAL PER DIGIT, `ALBO_FIG_<d>` = a|b|c|d, read once at import.
# `ALBO_FIG_SET` sets all ten at once, which is how the options sheet is built
# (one font per option letter rather than one per digit-option).
#
# **'a' IS TODAY'S DRAWING IN BOTH STYLES AND IS BYTE-IDENTICAL** -- proved on
# a build of every glyph of both fonts against r225, outlines and hmtx.
# `FIG_SHIP_ROM` / `FIG_SHIP_IT` are the per-STYLE defaults, so a winner ships
# by changing one letter in one of those two dicts and nothing else; the owner
# may pick a different option for the roman and the italic of the same digit.
#
# THE OPTION LETTER MEANS A DIFFERENT THING IN EACH STYLE, deliberately: the
# roman's 7 and the italic's 7 are not the same problem (the italic's carries
# five of his own rulings from rounds 211-219 and every option keeps all five;
# the roman's has never been touched and reads -21% of its family). What the
# letters mean, per digit, is in the table at the foot of this block.
#
# THE GATE ON EVERY ITALIC/ROMAN DIFFERENCE IS `pen.ITALIC`, on the WHOLE
# branch and not on the shape alone -- round 213's `SEVEN_BAR_W` and round
# 217's `ONE_FLAG_W` each leaked a weight into the roman while their shape was
# gated, and both were caught by diffing every glyph of both builds rather
# than by reading the code.
#
# AND THE ITALIC'S FIGURES ARE NOT THE LAST WORD HERE. `glyphs/aldine.py`
# re-registers all ten as `_press(figures.g_<name>(c), FIG_HAND[ch])` -- round
# 167's hand-cut, the owner's *"make italic numerals handcut"* -- whose cuts
# are placed as FRACTIONS of the glyph's own bbox. So an option that changes a
# figure's bounds moves where those cuts land: the taller 8 (`8b`/`8d`), the
# shorter tail (`9b`/`9d`) and above all the 6 drawn as the rotated 9 (`6b`),
# which is handed the 6's press over a 9's shape. Every arm was swept with
# `cmp_aldine_glitch --ttf` (0 of 119) and looked at, and nothing has gone
# wrong -- the cuts are 2 to 3.5 units -- but a winner among those three
# wants its `FIG_HAND` row re-checked by eye in `aldine.py`, which was outside
# this round's partition. The ROMAN does not go through `_press` at all.
_FIG_OPT_ALL = (os.environ.get("ALBO_FIG_SET", "") or "").strip().lower()
_FIG_OPT_ENV = {d: (os.environ.get("ALBO_FIG_" + d, "") or _FIG_OPT_ALL).strip().lower()
                for d in "0123456789"}
FIG_SHIP_ROM = dict.fromkeys("0123456789", 'a')
FIG_SHIP_ROM.update({'1': 'h', '2': 'b'})   # round 249, owner 2026-09-18: "ALBO_FIG_1 h", "ALBO_FIG_2 b without the bulge"
# ROUND 361, owner 2026-09-23: *"j wins"*, from six 7s shown in the numeral
# run. j is the bar at the 0's own thick -- the heaviest of the six and the
# closest to the rest of the figures: against their stroke 53.4 / thick 68.9 /
# colour 0.159 it reads -14% / -2% / -3%, where the 7 it replaces read
# -28 / -28 / -24 and was the lightest glyph among the figures.
FIG_SHIP_ROM.update({'7': 'j'})
FIG_SHIP_ROM.update({'3': 'e', '6': 'i', '9': 'u'})   # round 257: the 9's tail joins as the 6's does, tip 5 units past the bowl (owner: "p wins but only got optically just past bowl and switch tail to join the same way that 6's tail does"); round 254: the 9 ships as s (p's short deep wedge, tail flush with the bowl -- owner 2026-09-19: "p wins but shorten the tail until it fits the rest of the 9"); round 253 j; round 250, owner 2026-09-18: "ALBO_FIG_3 e", "ALBO_FIG_6 d and h blunt and short", "ALBO_FIG_9 e wins"
FIG_SHIP_IT = dict.fromkeys("0123456789", 'a')

def OPT(d):
    """Which option this build draws for digit `d`. Env first, then the
    per-style shipped default. Unknown letters fall back to 'a' rather than
    raising, so a typo in a sheet script cannot silently build a third thing.

    a-h. Round 229 gave every digit a-d; round 231 added e-h to the ITALIC 7
    alone (owner: *"give me more options for the italic 7 that match the rest
    of the numerals and font's style"*). A letter with no row in a digit's
    table resolves to an empty override, which IS that digit's option 'a' --
    so `ALBO_FIG_SET=e` draws eight arms of 'e' for the 7 and today's drawing
    for the other nine, and the roman 7 likewise. Proven on a build."""
    o = _FIG_OPT_ENV.get(d) or (FIG_SHIP_IT if pen.ITALIC else FIG_SHIP_ROM)[d]
    return o if o in 'abcdefghijklmnopqrstuvw' and len(o) == 1 else 'a'

# WHAT THE REFERENCES MEASURE, and where each option comes from. Seven faces
# with old-style figures, all measured at ONE x-height (429 units) by
# `refmeas.py` in the round's scratch dir: Flanker Griffo Italic and TeX Gyre
# Pagella Italic through their `onum` feature, Poetica Std and Coelacanth
# Italic (old-style by default), Georgia and Georgia Italic (old-style by
# default), Big Caslon. The full table is in the round's report. The three
# numbers each option is answering:
#
#   CONTRAST  thick/thin on the chamfer ridge. The references' 0 runs 2.33-3.07
#             and their 8 2.05-5.29; Albo's roman 0 is 1.61 and its 8 1.52.
#   HEIGHT    the ascending figures against the x-height. The references' 8
#             tops at 1.31-1.54 x-heights and sits on their 6's line; Albo's
#             roman 8 tops at 1.21 and is 97 units short of its own 6.
#   WIDTH     `build.solve_widths` pins each figure's ink to
#             `round20.REF[ch]['w']`, but the multiplier is CLAMPED at 0.70 and
#             six of the ten figures sit ON that clamp -- so the 5 is built
#             +20.6% over its own target, the 3 +15.6%, the 8 +12.4%, the 9
#             +6.5%. A narrowing option is the only way those four reach the
#             target the face already declares for them.
# ========================================================================

# ROUND 305 -- THE FIGURES' NIB, family-wide. `ALBO_FIG_NIB` = "thin,phi" or
# "thick,thin,phi" (x the stem) puts EVERY figure ring on a true nib instead of
# the family's bowl profile, whose 0.70 hair caps a ring near 1.4:1 however it
# is cut. It exists because the 8 alone on a nib stops matching its own 6 and
# 0: the nib's thick sits on a diagonal axis and the bowl profile's sits on the
# vertical, so one figure moves and the rest do not. Unset, nothing changes.
def _fig_nib():
    v = os.environ.get('ALBO_FIG_NIB')
    if not v: return None
    n = [float(x) for x in v.split(',')]
    return (1.0, n[0], n[1]) if len(n) == 2 else tuple(n)

def fig_ring(cx, cy, rx_c, ry_c, con=None, oval=None, stress=None, k=None):
    """The figures' ring. `con` / `oval` / `stress` / `k` are the OPTION
    levers; with none of them the roman gets the plain ring it always had and
    the italic round 211's cut and axis, byte for byte."""
    kw = {} if k is None else {'k': k}
    _n = _fig_nib()
    if _n is not None: kw['nib'] = _n
    if pen.ITALIC and (FIG_CON != 1.0 or FIG_STRESS or FIG_OVAL):
        return ring(cx, cy, rx_c + TH_V / 2, ry_c + TH_H / 2,
                    con=FIG_CON if con is None else con,
                    stress=math.radians(FIG_STRESS if stress is None else stress),
                    oval=FIG_OVAL if oval is None else oval, **kw)
    if con is None and stress is None and oval is None and not kw:
        return ring(cx, cy, rx_c + TH_V / 2, ry_c + TH_H / 2)
    if _n is not None and oval is None:
        oval = float(os.environ.get('ALBO_FIG_NIB_OVAL', 1.0))
    return ring(cx, cy, rx_c + TH_V / 2, ry_c + TH_H / 2,
                con=1.0 if con is None else con,
                stress=math.radians(stress or 0.0),
                oval=0.0 if oval is None else oval, **kw)

def _okw(d, rom, it=None):
    """The option overrides for digit `d` in the style this build is drawing.
    `it` None means the two styles share the table."""
    return (it if (pen.ITALIC and it is not None) else rom).get(OPT(d), {})

# THE 0. Its width is already on the solver's target (1.007) and its height is
# the box's, so neither is available as an option; what IS available, and what
# the references say is missing, is the CUT and the AXIS. Albo's roman 0 reads
# thick/thin 1.61 and its italic 2.12, where Flanker is 2.91, Georgia 3.07,
# Poetica 2.65, Coelacanth 2.33 and Pagella 2.45. (Big Caslon's 1.23 is the
# one face that draws the 0 as a near-monolinear circle -- which is option d.)
# A NOTE ON `k`, BECAUSE THE FIRST CUT OF OPTION d WAS WRONG AND LOOKED
# DELIBERATE: `k` is the superellipse EXPONENT and 2.0 is a true ellipse.
# BOWL_K 2.1 is therefore already very slightly squared, and going BELOW 2 --
# 1.72, chosen to make the 0 "rounder, like Big Caslon's circle" -- makes the
# ring POINTED at 12 and 6 o'clock, a lens rather than an O. Caught on the
# render, not in the code. There is no rounder available above an ellipse, so
# the fourth arm goes the other way instead: 2.55 is Georgia's squarer ring,
# which is a real and different answer rather than a smaller version of b.
ZERO_OPT = {
    'b': dict(con=1.90),                     # Georgia/Flanker's cut, axis unmoved
    'c': dict(con=1.90, stress=-26.0),       # ...and Poetica's oblique axis with it
    'd': dict(k=2.55),                       # Georgia's squarer ring, cut as today
}
ZERO_OPT_IT = {
    'b': dict(con=2.55),                     # past round 211's 1.8, to Flanker's 2.91
    'c': dict(con=2.55, stress=-46.0),       # ...and the axis further over, Coelacanth's
    'd': dict(k=2.55),
}

# THE 1: (how far left the flag starts, in units; where on the stem, x D).
# HOW FAR THE FLAG MAY REACH IS SET BY THE FITTER, not by taste, and the two
# styles have different room. `_body_edges` in `outlines/build.py` takes a
# glyph's left edge as the 20th percentile of its per-row ink extremes, and the
# flag occupies only the top ~28% of the 1's rows -- so at the percentile the
# 1's left edge is still its STEM, and everything the flag adds is read as pure
# overhang and absorbed (0.75 of it in the italic, 0.45 in the roman). The
# italic therefore runs out of bearing much sooner: at 205 units `cmp_touch`
# reports `O1 w1 o1 p1` TOUCHING and `b1 j1` under the floor, at 250 nine pairs
# touching. Laddered below until every `x1` pair clears the 0.012 em floor with
# the italic's own bearings and no new kern -- kerns live in `kern.py`, which
# is out of this round's partition. The roman shows no `1` pair anywhere near
# the floor at either value, so it keeps the wider reaches.
_E = lambda k, d: float(os.environ.get(k, d))
ONE_OPT = {'b': dict(flag=(_E('ALBO_FIG_1B_X', 195.0), 0.72)),
           'c': dict(flag=(_E('ALBO_FIG_1C_X', 238.0), 0.635)),
           # ROUND 233 (R35), owner 2026-09-18: *"give me options for improved
           # 1."* Roman only (ONE_OPT_IT has no d-h rows, so the italic draws
           # 'a' under any of these letters). Each is ONE change against the
           # fixed 'a' so they can be told apart; the references measured on a
           # raster at a 1000-unit x-height, `mref.py` in the round's scratch:
           # Georgia's flag reaches 1.27 stems left and falls 0.11 of the
           # height, Big Caslon's 0.96 / 0.09, Poetica's 1.44 / 0.09 -- Albo's
           # reaches 1.57 and falls 0.34, a long diagonal where theirs is a
           # short hook; their feet run 2.9-4.1 stems wide against Albo's 2.6.
           'd': dict(foot_len=0.50),                 # shorter feet: each bracket reaches half the family's FOOT
           'e': dict(foot='left'),                   # one-sided: the L's foot, nothing right of the stem
           'f': dict(foot='slab'),                   # a flat slab, square-ended, S x 0.30 deep, the brackets' reach
           'g': dict(flag_tip=0.25),                 # the flag as a plain wedge: 0.25 of the profile at the tip, full into the stem, pen cut
           'h': dict(flag=(95.0, 0.885), flag_tip=0.30, flag_curve=0.16, foot_len=1.20)}   # the references' 1: a short hook bowed UP and over (1.2 stems, 0.115 of the height; -0.16 sagged and its tip barbed upward), feet 3.3 stems wide
ONE_OPT_IT = {'b': dict(flag=(_E('ALBO_FIG_1B_X_IT', 158.0), 0.72)),
              'c': dict(flag=(_E('ALBO_FIG_1C_X_IT', 180.0), 0.635))}
# THE ITALIC LADDER, `O1`'s white in em (the floor is 0.012), and what the
# advance ratio buys: 150 (today) 0.0210 at 0.552 -- 158 0.0167 at 0.562 --
# 162 0.0138 -- 172 0.0052 UNDER -- 182 -0.0019 TOUCHING -- 192/205/250 worse.
# On the lower start: 175 0.0167 at 0.577 -- 180 0.0152 at 0.583 -- 190 0.0095
# UNDER -- 220 TOUCHING. **So the italic 1 cannot be taken past about 0.58 of
# the 0's advance from inside this file.** The references run 0.700 (Georgia),
# 0.736 (Coelacanth), 0.778 (Poetica); reaching those needs the 1's left
# BEARING or a handful of `x1` kerns, and `build.py` and `kern.py` are both
# outside this round's partition. Recorded rather than forced.
# The ROMAN has room and takes it: b reaches 0.692 and c 0.787 with `O1` at
# 0.0429 and 0.0471, four times the floor.

def zero_bowl(c, D, **kw):
    """The 0's ring at figure height D: (solid, outer, inner). Also the 8's
    reference counter when EIGHT_COUNTER_OF is '0'."""
    rx = W_(c, '0', 230)
    return fig_ring(rx + TH_V / 2, D / 2, rx, D / 2 + OVER - TH_H / 2, **kw)

def six_bowl(c, D, r_frac=0.29):
    """The 6's bowl at figure height D: (solid, outer, inner), rx, r, ry.
    Also the 8's reference counter when EIGHT_COUNTER_OF is '6' -- which calls
    it at the default `r_frac`, so an option on the 6 cannot move the 8."""
    rx = W_(c, '6', 230); r = D * r_frac; ry = r + OVER - TH_H / 2
    return fig_ring(rx + TH_V / 2, r, rx, ry), rx, r, ry

def counter_box(solid):
    """Bounds of a ring's counter (its one interior)."""
    p = solid if solid.geom_type == 'Polygon' else max(solid.geoms, key=lambda q: q.area)
    return list(p.interiors)[0].bounds

def ring_for_counter(cx, cy, cw, ch, w_scale=1.0, k=None, floor=0.0, rot=0.0):
    """The outer radii (rx, ry) of a ring whose COUNTER measures cw x ch,
    found by iteration: the counter is the pen's inward offset, unfolded and
    smoothed, and has no closed form. Six half-error steps; the response is
    near 1:1, so it settles in two."""
    rx = cw / 2 + bowl_th((0, 1)) * w_scale; ry = ch / 2 + bowl_th((1, 0)) * w_scale
    kw = dict(w_scale=w_scale, floor=floor, rot=rot); kw.update({'k': k} if k else {})
    for _ in range(6):
        solid, o, i = ring(cx, cy, rx, ry, **kw)
        x0, y0, x1, y1 = counter_box(solid)
        rx += (cw - (x1 - x0)) / 2; ry += (ch - (y1 - y0)) / 2
    return rx, ry

@glyph('0')
def g_zero(c):
    D = c["figH"]
    solid, o, i = zero_bowl(c, D, **_okw('0', ZERO_OPT, ZERO_OPT_IT)); return solid

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
    brushed = pen.ITALIC and ONE_FOOT_BRUSH > 1.0
    _o1 = _okw('1', ONE_OPT, ONE_OPT_IT)
    # round 233 (R35): the foot is an option in the roman -- 'both' (today) |
    # 'left' | 'slab' -- and foot_len scales the brackets' reach. Nothing is
    # passed to stem() unless the option names it, so 'a' is the old call.
    _foot = _o1.get('foot', 'both')
    _fkw = {'foot_len': _o1['foot_len']} if 'foot_len' in _o1 else {}
    st = stem(x, 0, D, top=None, foot=(None if (brushed or _foot == 'slab') else _foot),
              it_exit_len=(ONE_EXIT_LEN if pen.ITALIC else 1.0), **_fkw)
    # THE 1'S OPTIONS ARE WIDTH AND FIT ONLY. Its shape is ruled three times
    # over -- the buried flag and its microserif (round 75, roman), the curve
    # and its bow (rounds 217-218, italic), the brushed foot and the shortened
    # exit (rounds 215, 218) -- and none of that is re-opened here. What is
    # open is how far the flag REACHES, which is what sets the 1's advance and
    # therefore how a run of figures reads: Albo's 1 takes 0.62 of the 0's
    # advance in the roman and 0.55 in the italic, where Georgia is 0.70,
    # Coelacanth 0.74, Poetica 0.78 and Pagella 0.92 (Flanker's figures are
    # tabular, so all ten are 1.00). `11` is the 8th-widest of the roman's 100
    # figure pairs, so the gap is measured as well as seen. The 1 is the one
    # figure `solve_widths` deliberately skips, so its drawn width IS its
    # built width and these numbers move the letter directly.
    _fx, _fy = _o1.get('flag', (150.0, 0.72))
    _p0 = (x - _fx, D * _fy); _p1 = (x, D - TH_V * ONE_FLAG_BURY)
    # round 233: the roman may bow its flag too (option h, the references'
    # short hook); the italic's bow is round 217's and unchanged
    _crv = ONE_FLAG_CURVE if pen.ITALIC else _o1.get('flag_curve', 0.0)
    curved = bool(_crv)
    if curved:
        _dx, _dy = _p1[0] - _p0[0], _p1[1] - _p0[1]
        _L = math.hypot(_dx, _dy) or 1.0
        _nx, _ny = -_dy / _L, _dx / _L          # perpendicular, up-left of the run
        _b = _L * _crv
        path = cubic(_p0,
                     (_p0[0] + _dx * 0.30 + _nx * _b, _p0[1] + _dy * 0.30 + _ny * _b),
                     (_p0[0] + _dx * 0.70 + _nx * _b, _p0[1] + _dy * 0.70 + _ny * _b),
                     _p1)
    else:
        path = line(_p0, _p1)
    _tip = _o1.get('flag_tip')
    if _tip is not None:
        # options g/h: the flag is a WEDGE -- thin at its free end (`flag_tip`
        # of the profile), full by the middle, the family's pen cut on the thin
        # face. The 0.62 S floor below would hold any taper up at 52 units, so
        # it is released here and only here.
        wf0 = PR.bowl_widths(path, widths([(0.0, _tip), (0.55, 0.9), (1.0, 0.9)]), floor=0.0)
    else:
        # the flag on the bowl profile at the stem's weight (a pen-drawn flag
        # is a hairline at this contrast; Albertus's 1 carries a short solid
        # flag) -- reflection of 2026-09-13: chiselled, not calligraphic
        wf0 = PR.bowl_widths(path, widths([(0.0, 0.8), (0.5, 0.9), (1.0, 0.9)]), floor=S * 0.62)
    # ITALIC-GATED, like the curve. Ungated this multiplier moved the ROMAN's
    # 1 as well -- the same leak SEVEN_BAR_W had in round 213, caught the same
    # way, by diffing every glyph of both builds rather than by reading it.
    wf = (lambda u: wf0(u) * ONE_FLAG_W) if (pen.ITALIC and curved and ONE_FLAG_W != 1.0) else wf0
    _square = ONE_FLAG_WEDGE and not curved and _tip is None    # round 75's square face, the microserif's seat
    flick = _square and (ONE_FLAG_FLICK or pen.ITALIC)          # round 233 (R34): the roman drops the microserif, the face stays
    parts = [st, stroke(path, wf, cut0=None if _square else CUT)]
    if brushed:
        # the press: the stem's own width spreading into the baseline. Square
        # end faces (cut0/cut1 None) so the foot sits flat on the line and the
        # top of the press disappears into the stem it is part of.
        w0 = PR.stem_width(TH_V, pen.ENT, 0.0)
        fp = line((x, S * ONE_FOOT_BRUSH_H), (x, 0))
        parts.append(stroke(fp, widths([(0.0, w0), (1.0, w0 * ONE_FOOT_BRUSH)]),
                            cut0=None, cut1=None))
    if _foot == 'slab':
        # option f: a flat slab under the stem, square-ended, reaching exactly
        # where the bracket feet reach (the stem's flared edge + WL x FOOT each
        # side), S x 0.30 deep; the stem's own entasis flares into its top
        _hw = PR.stem_width(TH_V, pen.ENT, 0.0) / 2 + WL * pen.FOOT * _o1.get('foot_len', 1.0)
        parts.append(bar(x - _hw, x + _hw, 0, S * 0.30, align='bottom'))
    if flick:   # the 9's flag-diag construction: a square face across the stroke, the wedge off its UPPER corner
        parts.append(end_wedge(path, wf(0.0), True, 1, scale=ONE_FLAG_WEDGE_SCALE))
    return geom.ink(parts)

@glyph('2')
def g_two(c):
    """Owner 2026-09-13: "2 needs another pass to tidy up stray marks and
    flow the top right into the slash into the bottom"; on the first two
    attempts: "whatever worked on 1 2 4 is lacking the understanding of
    what we're doing with this font. reflect and try again." The font is a
    chiselled wedge serif in Albertus's idiom: one weight, straight where
    it can be, crisp corners. So: the arc, and a STRAIGHT slash that leaves
    the arc on the arc's own tangent (the arc's end angle is solved so its
    tangent points at the base's left end -- that is the flow, and there
    is no neck to leave a mark), the slash at the arc's weight on the bowl
    profile, its end buried in the base; the base the family's bar with
    its right wedge, the corner crisp as Albertus's."""
    D = c["figH"]; w = W_(c, '2', 440); rx = w * 0.46
    barw = max(TH_H, S * 0.5)
    # GLITCH SWEEP 2026-09-16: the slash's end is "buried in the base", and at
    # barw*0.45 it was not quite -- its square face reached 3.55 units under
    # the bar's own bottom edge and printed a 12.6-unit^2 downward spike, 8
    # units wide, on an otherwise straight baseline. Swept: barw*0.45 dips
    # -3.55, barw*0.60 clears by +3.35 and every value above it clears further.
    # Same family as the 1's flag (ONE_FLAG_BURY) and the 4's apex.
    _drop = TWO_BAR_DROP if pen.ITALIC else 0.0
    foot = (S * 0.5, barw * 0.60 - _drop)
    _o2 = _okw('2', TWO_OPT, TWO_OPT_IT)
    _topw = _o2.get('top_w', TWO_TOP_W); _slashw = _o2.get('slash_w', TWO_SLASH_W)
    _basew = _o2.get('base_w', TWO_BASE_W); _over2 = _o2.get('over', NINE_OVERHANG)
    _turn = _o2.get('turn')
    if _turn:
        # ROUND 233 (R36/R37) option f -- THE BASE IS THE SAME STROKE TURNING
        # THE CORNER, Poetica's and Coelacanth's 2. The turn is a circle of
        # centerline radius `turn` x S, tangent to the base's centerline
        # (y = wb/2) and placed so its OUTER edge reaches x 0, where the bar's
        # left end has always stood; the arc's end tangent is solved to point
        # at that circle's outer tangent point instead of at `foot`, so the
        # slash still leaves the arc on the arc's own tangent (the flow the
        # round-75 docstring describes) and arrives on the circle tangent too.
        wb = barw * _basew; R_t = S * _turn
        Ct = (R_t + wb / 2, wb / 2 + R_t)
        def _aim(tipd):
            dx, dy = tipd[0] - Ct[0], tipd[1] - Ct[1]; dd = math.hypot(dx, dy)
            ph = math.atan2(dy, dx); al = math.acos(min(1.0, R_t / dd))
            return (Ct[0] + R_t * math.cos(ph + al), Ct[1] + R_t * math.sin(ph + al))   # the left-hand (outer) tangent point
    else:
        _aim = lambda tipd: foot
    best = None
    for deg in range(-40, -8, 1):
        top = superellipse(rx, D - rx * 0.95, rx, rx * 0.95, math.radians(190), math.radians(deg), BOWL_K)
        tipd = top[-1]; at = tangents(top)[-1]; tgt = _aim(tipd)
        vx, vy = tgt[0] - tipd[0], tgt[1] - tipd[1]; L = math.hypot(vx, vy) or 1.0
        err = 1 - (at[0] * vx + at[1] * vy) / L
        if best is None or err < best[0]: best = (err, deg, top, tipd)
    _, deg, top, tipd = best
    _st = math.radians(FIG_STRESS) if pen.ITALIC else 0.0
    _cn = FIG_CON if pen.ITALIC else 1.0
    import shapely.affinity as _aff
    if _turn:
        T1 = _aim(tipd)
        slash = join(top, line(tipd, T1))
        f_arc = _plen(top) / max(_plen(slash), 1e-6)
        prof = widths([(0.0, _topw * 1.1), (0.15, _topw), (f_arc, _topw), (1.0, 1.0)])
        bw = PR.bowl_widths(slash, prof, floor=S * _slashw * _topw, stress=_st, con=_cn)
        x1 = geom.bbox(stroke(slash, bw, cut0=CUT))[2] + _over2      # the base's right end: where it has always been
        a_T = math.atan2(T1[1] - Ct[1], T1[0] - Ct[0])
        # round the LEFT of the circle: from the tangent point (upper left,
        # ~127 degrees) through 180 to 270, the bottom, where it heads east
        turn_arc = superellipse(Ct[0], Ct[1], R_t, R_t, a_T, 3 * math.pi / 2, 2.0)
        full = join(slash, turn_arc, line((Ct[0], wb / 2), (x1, wb / 2)))
        L_s, L_t, L_f = _plen(slash), _plen(slash) + _plen(turn_arc), _plen(full)
        t_s, t_t = L_s / L_f, L_t / L_f
        w_end = bw(1.0)
        def wfull(t):
            # the arc and the slash on their own (bowl) widths; through the
            # turn the width eases from the slash's to the base's; the base at
            # the bar weight TWO_BASE_W, exactly the bar's depth
            if t <= t_s: return bw(t / t_s)
            if t >= t_t: return wb
            u = (t - t_s) / (t_t - t_s); u = 3 * u * u - 2 * u ** 3
            return w_end + (wb - w_end) * u
        solid, Ls, Rs = stroke(full, wfull, cut0=CUT, sides=True)
        # the family's bar-end wedge rising from the base's top-right corner,
        # its bracket back along the stroke's real top edge (as the bar's was)
        wdg = wedge(Ls[-1], (1, 0), (0, 1), WL * 0.85, WD * 0.9, 0.0, edge_at=_walk_back(Ls))
        return _aff.translate(geom.ink([solid, wdg]), 0, TWO_LIFT)
    center = join(top, line(tipd, foot))
    # owner 2026-09-13: "rebalance 2 to be heavier on the bottom and lighter
    # on the top": the arc at TWO_TOP_W of the profile, the slash growing to
    # full by the base, the base bar TWO_BASE_W heavier
    f_arc = _plen(top) / max(_plen(center), 1e-6)
    _send = _o2.get('slash_end')
    if _send:
        # option e: the slash THINS into the base, so the base carries the
        # figure's weight and the slash reads as the written stroke into it
        prof = widths([(0.0, _topw * 1.1), (0.15, _topw), (f_arc, _topw),
                       (f_arc + 0.35 * (1 - f_arc), 1.0), (1.0, _send)])
    elif _o2.get('slash_k'):
        # round 255 (g-i): the slash HELD at `slash_k` of the profile for its
        # run -- easing down from the arc's weight over the slash's first
        # quarter and flat from there -- instead of easing UP to the full
        # profile by the base. The arc keeps `top_w`; the base is its own bar.
        _sk = _o2['slash_k']
        prof = widths([(0.0, _topw * _o2.get('start_w', 1.1)), (0.15, _topw), (f_arc, _topw),
                       (f_arc + 0.25 * (1 - f_arc), _sk), (1.0, _sk)])
    else:
        # ROUND 276 -- THE ITALIC'S TOP IS THE c's TOP FINIAL (owner 2026-09-19:
        # "that italic has round finials that needs to replaced along with
        # others"): the italic 2 (option a) swelled 1.1 over its first 15%
        # into the 20-degree cut, the 3's top's construction, and takes the
        # same conversion -- the swell in the profile goes and PR.finial_widths
        # / PR.finial_cut put the family's end on it below (same end width,
        # 75.0 at the 400; the span and the face move). The roman is untouched:
        # its shipped option b has start_w 1.0 by round 249's ruling ("without
        # the bulge") and keeps its plain cut.
        prof = widths([(0.0, _topw * (1.0 if pen.ITALIC else _o2.get('start_w', 1.1))), (0.15, _topw), (f_arc, _topw), (1.0, 1.0)])
    wfn = PR.bowl_widths(center, prof, floor=S * _slashw * _topw, stress=_st, con=_cn)
    if _send:
        # ...and its OUTER edge lands ON the base's top-left corner, so the
        # silhouette turns the corner in one point instead of the base
        # standing 24 units proud of the slash (measured: the outer edge met
        # the base's top at x 24, the base's left face at x 0). The
        # centerline's end is the corner pushed in by half the end width along
        # the slash's own normal; two passes, since the width reads the
        # direction.
        corner = (0.0, barw * _basew - _drop)
        for _ in range(2):
            ux, uy = center[-1][0] - tipd[0], center[-1][1] - tipd[1]; Lu = math.hypot(ux, uy) or 1.0
            ux, uy = ux / Lu, uy / Lu; w_f = wfn(1.0)
            foot2 = (corner[0] - uy * w_f / 2, corner[1] + ux * w_f / 2)   # corner - (w/2) x the outer (up-left) normal
            center = join(top, line(tipd, foot2))
            wfn = PR.bowl_widths(center, prof, floor=S * _slashw * _topw, stress=_st, con=_cn)
    if pen.ITALIC:   # round 276: the italic's top is the c's top finial (see the profile above)
        body = stroke(center, PR.finial_widths(wfn, True), cut0=PR.finial_cut(center, True))
    else:
        body = stroke(center, wfn, cut0=CUT)
    x1 = geom.bbox(body)[2] + _over2
    parts = [body, bar(0, x1, -_drop, barw * _basew, align='bottom', wedges=[('right', 1)])]
    if _o2.get('fillet'):
        # option d: the INSIDE join filleted -- the family's concave bracket
        # (the wedge's own quad) laid into the crotch where the slash's inner
        # edge meets the base's top, `fillet` x S along each edge. The slash's
        # inner edge is the stroke's L side (left of a stroke travelling
        # down-left is its south-east edge).
        f = S * _o2['fillet']; ytop = barw * _basew - _drop
        _s, Ls, Rs = stroke(center, wfn, cut0=CUT, sides=True)
        K, upto = _edge_cross_y(Ls, ytop)
        if K is not None:
            A1 = _walk_back(upto)(f); A2 = (K[0] + f, ytop)
            parts.append(geom.poly(geom.quad(A1, K, A2) + [K]))
    g = geom.ink(parts)
    # owner 2026-09-13: "push 2 back up to optical baseline" -- the built 2
    # bottomed at -7 (the cut's facets and the ink spread under a flat base);
    # lifted so the base sits on the line like the 1's feet
    return _aff.translate(g, 0, TWO_LIFT)

def _edge_cross_y(side, y):
    """Where a side polyline (walked from its start) first crosses the line
    y = `y` on its way to its end: (the crossing point, the polyline up to and
    including it). (None, None) if it never does."""
    for a, b in zip(side, side[1:]):
        if (a[1] - y) * (b[1] - y) <= 0 and a[1] != b[1]:
            u = (y - a[1]) / (b[1] - a[1]); K = (a[0] + (b[0] - a[0]) * u, y)
            return K, [p for p in side[:side.index(a) + 1]] + [K]
    return None, None

# the 2 as one stroke (2026-09-13): the slash's weight floor (x S; 0.8 = the
# arc's side, one weight). The arc's end angle is solved per build.
TWO_SLASH_W = 0.80
TWO_TOP_W = 0.82      # the arc's weight, x the profile (lighter on top)
TWO_LIFT = 8.0        # units up, so the base's ink bottoms at the baseline
TWO_BASE_W = 1.22     # the base bar, x the bar weight (heavier on the bottom)
# THE 2'S OPTIONS, and they are two different readings of the same figure.
# (b) is GEORGIA's: a light arc over a long, heavy, flat base -- the base runs
# 26 units past the body instead of 11 (the 9's tail overhang, which is what
# the 2's base was matched to in 2026-09-13) and carries 1.50 of the bar
# weight against today's 1.22, so the figure's mass is unmistakably at the
# bottom. (c) is POETICA's and COELACANTH's: the contrast is put in the STROKE
# rather than in the base -- a thin arc (0.62 of the profile against 0.82)
# running into a diagonal at nearly full width, with the base back at 1.10.
# Both styles share the table; the italic's bar drop (round 212) is untouched.
TWO_OPT = {
    'b': dict(base_w=1.50, top_w=0.74, over=26.0, start_w=1.0),   # round 249: start_w 1.0 -- owner 2026-09-18, "ALBO_FIG_2 b without the bulge": the arc's left terminal no longer swells to 1.1 of the arc
    'c': dict(top_w=0.62, slash_w=0.98, base_w=1.45),
    # ROUND 233 (R36, R37), owner 2026-09-18: *"give me options for improving
    # the diagonal and join in bottom left"* / *"same as R36"*. What is there
    # today, measured on the built outline at 5 px/unit: the slash is a
    # straight line at 41.5 degrees whose outer edge lands on the base's top
    # 24 units RIGHT of the base's left face, so the base stands proud of the
    # slash as a square tab; its inner edge meets the base's top in a bare
    # 41-degree crotch. Three readings of that corner, roman only:
    'd': dict(fillet=0.45),                     # the inside crotch filleted with the family's bracket, 0.45 S along each edge; outer corner as today
    'e': dict(slash_end=0.58, ),                # the slash THINS into the base (to 0.58 of the profile) and its outer edge lands ON the base's corner
    'f': dict(turn=0.55),                       # a WRITTEN TURN: the slash rounds into the base as one stroke, centerline radius 0.55 S, outer edge still reaching x 0
    # ROUND 255, owner 2026-09-19: *"redo 2 3 4 7 8 to be optically balanced
    # with rest of numerals. use other old style figures as inspiration."*
    # Roman only, every arm built on the shipped b (start_w 1.0, the long
    # base) so his round-249 ruling stands under all three. Measured on a
    # raster at a 1000-unit x-height (`shape.py` in the round's scratch), each
    # stroke as a fraction of THAT face's own 0's thick side, so faces of
    # different weight compare -- and Albo's five shipped figures are the
    # yardstick, not the references' absolute weights:
    #                    arc side   base    slash    (of the 0's thick side, all measured on the raster)
    #   Georgia            0.99     0.80    0.40
    #   Flanker            0.98     0.96    0.40
    #   Coelacanth         0.87     0.86    0.39
    #   Pagella            1.23     0.92    0.54
    #   Poetica            1.43     1.20    0.55
    #   Albo 2b (today)    0.72     0.80    0.64
    # (The slash is read perpendicular to its own local edge on rows 0.64-0.80
    # of the height; a first cut read it on rows 0.50-0.72, which on Albo's 2
    # is still the arc's tail, and put it 20% too light. Corrected here.)
    # The 2's ridge stroke reads 57.2 against the shipped 0 1 5 6 9's median
    # 74.5 (-23%), and the table says where that is: the ARC is 0.72 of the
    # 0's side where every reference runs 0.87-1.43, the BASE 0.80 is at the
    # bottom of their 0.80-1.20, and the SLASH, 0.64, is already ABOVE their
    # 0.39-0.55. So the weight goes into the arc and the base and comes OUT of
    # the slash -- `top_w` 1.0 puts the arc's sides on the 0's (measured 0.96),
    # and `slash_k` is a new lever that holds the slash at 0.70 of the profile
    # for its run instead of letting it ease up to the full 1.0 by the base
    # (measured 0.55, Pagella's and Poetica's; Georgia's 0.40 would be a 1 px
    # slash at 13 px on this pen and is deliberately not chased). Without it a
    # heavier arc makes a heavier slash, which is the one stroke that was not
    # light.
    # (`slash_w` is the slash's FLOOR, x S x top_w; at b's 0.80 it would stand
    # at 67 units and hold the slash up over `slash_k`, so it drops under it.)
    'g': dict(top_w=1.0, slash_k=0.70, slash_w=0.55, base_w=1.50, over=26.0, start_w=1.0),  # the ARC to the 0's weight; base as b
    'h': dict(top_w=1.0, slash_k=0.70, slash_w=0.55, base_w=1.90, over=26.0, start_w=1.0),  # ...and the BASE to the references' median (80 units, 0.93 of the 0's thick): heavier on the bottom, as ruled in round 81
    'i': dict(top_w=1.0, slash_k=0.70, slash_w=0.55, base_w=1.90, over=60.0, start_w=1.0),  # ...and the base LONGER: 60 units past the body (0.17 of the width -- Pagella 0.17, Coelacanth 0.18, Big Caslon 0.17; b's 26 is Georgia's 0.06)
}
TWO_OPT_IT = {k: TWO_OPT[k] for k in ('b', 'c')}   # the italic keeps round 229's two and draws 'a' under d-i: its bar sits on the round-212 drop and its press cuts are placed on the bbox
def _plen(pts): return sum(math.hypot(q[0] - p_[0], q[1] - p_[1]) for p_, q in zip(pts, pts[1:]))

@glyph('3')
def g_three(c):
    _o3 = _okw('3', THREE_OPT, THREE_OPT_IT)
    D = c["figH"]; w = W_(c, '3', _o3.get('W', THREE_W))
    r1 = D * _o3.get('top_r', 0.20); r2 = D * THREE_BOT_R
    top = superellipse(w * _o3.get('top_cx', 0.52), D - r1, w * _o3.get('top_rx', 0.46), r1,
                       math.radians(165), math.radians(_o3.get('top_end', -105)), BOWL_K)
    bot = superellipse(w * THREE_BOT_CX, r2, w * THREE_BOT_RX, r2 + OVER - TH_H / 2,
                       math.radians(100), math.radians(THREE_BOT_END), BOWL_K)
    if not pen.ITALIC:
        # round 233 (R38): see THREE_WAIST_FLAT
        mode = _o3.get('waist', 'flat')
        # T sits THREE_WAIST_FLAT left of the two old ends, so the flat face
        # ('a') lands exactly where the old tip stood and the arm keeps its reach
        T = ((top[-1][0] + bot[0][0]) / 2 - THREE_WAIST_FLAT, (top[-1][1] + bot[0][1]) / 2)
        top2 = resample(top + [T]); bot2 = resample([T] + bot)
        # ROUND 275 -- BOTH FREE ENDS ARE THE c's TOP FINIAL (owner 2026-09-19:
        # "change out round finials (like c top serif)"). The top swelled 1.1
        # over its first 10% and the bottom flared 1.25 over its last 15%,
        # both into the 20-degree cut. Now PR.finial_widths / PR.finial_cut:
        # the swell to 1.10 over 13% and the face sheared 28 degrees toward
        # the vertical; the bottom end is held to the c's own end width
        # (rounds.c_top_width) so the lower terminal does not go lighter than
        # the letter it is modelled on. Roman only by construction (the
        # italic's 3 cannot select this waist).
        from .rounds import c_top_width
        t = stroke(top2, PR.finial_widths(pen_widths(top2, widths([(0.0, 1.0), (0.88, 1.0), (0.955, 0.45), (1.0, 0.04)])), True), cut0=PR.finial_cut(top2, True))
        b = stroke(bot2, PR.finial_widths(pen_widths(bot2, widths([(0.0, 0.04), (0.04, 0.45), (0.1, 1.0), (1.0, 1.0)])), False, floor=c_top_width()), cut1=PR.finial_cut(bot2, False))
        g = geom.ink([t, b])
        if mode == 'point': return g
        Xc = T[0] + THREE_WAIST_FLAT
        g = g.difference(geom.poly([(Xc - 400, T[1] - 60), (Xc, T[1] - 60), (Xc, T[1] + 60), (Xc - 400, T[1] + 60)]))
        if mode == 'beak':
            # option e: a lip off the face's LOWER corner, its bracket back along
            # the arm's real underside (the upper stroke's outer edge)
            runs = [rr for rr in _vruns(g, Xc + 0.5) if rr[0] <= T[1] <= rr[1]]
            if runs:
                y_lo = runs[0][0]; A = (Xc, y_lo)
                under = _edge_from(g, A, +1)
                g = geom.ink([g, wedge(A, (-1, 0), (0, -1), WL * 0.35, WD * 0.45, 0.0, edge_at=_walk_back(under))])
        return g
    # round 275: the roman's free ends are the c's top finial (see the beak
    # waist above); round 276: the italic's top too (owner 2026-09-19, "that
    # italic has round finials that needs to replaced along with others") --
    # it kept the 1.1 swell over 10% into the 20-degree cut for one round.
    # Same end width either way (60.7 at the 400): the span and the face move.
    t = stroke(top, PR.finial_widths(pen_widths(top, widths([(0.0, 1.0), (0.88, 1.0), (1.0, 0.4)])), True), cut0=PR.finial_cut(top, True))
    if pen.ITALIC and THREE_TAIL_END:      # runs out like the 6's tail
        b = stroke(bot, pen_widths(bot, widths([(0.0, 0.4), (0.1, 1.0), (0.70, 1.0),
                                                (1.0, THREE_TAIL_END)])))
    elif pen.ITALIC:
        b = stroke(bot, pen_widths(bot, widths([(0.0, 0.4), (0.1, 1.0), (0.85, 1.0), (1.0, 1.25)])), cut1=CUT)
    else:
        from .rounds import c_top_width
        b = stroke(bot, PR.finial_widths(pen_widths(bot, widths([(0.0, 0.4), (0.1, 1.0), (1.0, 1.0)])), False, floor=c_top_width()), cut1=PR.finial_cut(bot, False))
    return geom.ink([t, b])

def _vruns(g, x):
    """The ink runs of g along the vertical line x: [(y0, y1), ...]."""
    from shapely.geometry import LineString
    it = g.intersection(LineString([(x, -3000), (x, 3000)]))
    if it.is_empty: return []
    gs = [it] if it.geom_type == 'LineString' else list(getattr(it, 'geoms', []))
    return sorted((min(p[1] for p in s.coords), max(p[1] for p in s.coords)) for s in gs if s.geom_type == 'LineString')

def _edge_from(g, P, xdir, n=40):
    """The real outline of g leaving the vertex nearest P in the direction that
    moves x by the sign of `xdir`, as a polyline ENDING at that vertex -- the
    shape `_walk_back` wants for a wedge's edge_at."""
    p = g if g.geom_type == 'Polygon' else max(g.geoms, key=lambda q: q.area)
    ext = list(p.exterior.coords)[:-1]; m = len(ext)
    i = min(range(m), key=lambda k: math.dist(ext[k], P))
    fwd = [ext[(i + k) % m] for k in range(n)]; bwd = [ext[(i - k) % m] for k in range(n)]
    # the FIRST step decides: the edge wanted runs off in x, the other
    # neighbour is the face itself, which runs off in y (the first cut took
    # the third vertex, and on a two-vertex face that is already the far edge)
    def score(s): return (s[1][0] - s[0][0]) * xdir - abs(s[1][1] - s[0][1])
    side = fwd if score(fwd) > score(bwd) else bwd
    return list(reversed(side))

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
FOUR_OPEN = False          # owner 2026-09-13: "revert 4 to last closed version" (the curved-open construction stays behind the flag; future todo: reduce the thickness of the 4's top-left stroke)
FOUR_OPEN_GAP = 0.62       # x the stem, the gap at the top-left corner: 0.6 S is the standing aperture floor (50.4) and the cut's facets shave ~0.4 off the built gap, so the drawn number is a shade over
FOUR_DIAG_BURY = 0.25      # glitch sweep 2026-09-16: how far back along its own line the CLOSED diagonal's top end sits, x the stem, so its square end face is under the stem's top face instead of spurring out of it (see g_four)


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
    _o4 = _okw('4', FOUR_OPT, FOUR_OPT_IT)
    D = c["figH"]; w = W_(c, '4', 480); xs = w * 0.7
    barw = max(TH_H, S * 0.5) * _o4.get('bar', 1.0); bar_y = D * _o4.get('bar_y', 0.3)   # round 255: the bar's height is a lever (d-f)
    st = stem(xs, 0, D, top=None, foot='both',
              **({} if 'stem' not in _o4 else dict(w=TH_V * _o4['stem'])))
    b = bar(0, w, bar_y, barw)
    if FOUR_OPEN and FOUR_CURVED:
        x_edge = xs - TH_V / 2
        p0 = (x_edge - S * FOUR_OPEN_GAP - S * 0.28, D - 4)     # the start's centre, its half width past the gap
        p3 = (S * 0.45, bar_y)                                  # the bar's left end, on its centerline
        c1 = (p0[0] - S * FOUR_BOW, D * 0.68)
        c2 = (p3[0] - S * 0.25, bar_y + barw * 0.05)
        curve = cubic(p0, c1, c2, p3)
        # one weight, chiselled: the bowl profile floored at 0.72 S, no
        # thinning at the start, the pen cut as the terminal (the first
        # attempt thinned to a hairline start and bowed 0.55 S -- a hook,
        # not this font)
        prof = widths([(0.0, 1.0), (1.0, 1.0)])
        dg = stroke(curve, PR.bowl_widths(curve, prof, floor=S * 0.72), cut0=CUT)
        return geom.ink([dg, b, st])
    p1 = (S * 0.1, bar_y); p0 = (xs - S * 0.2, D)
    wd = pw(p0, p1, _o4.get('diag', 0.75))
    # GLITCH SWEEP 2026-09-16 -- THE CLOSED 4's APEX. The diagonal's centerline
    # ended exactly ON the figure's top line, and its end face is square across
    # a stroke climbing at ~70 degrees, so the face's upper corner stood 9.95
    # units ABOVE the stem's own top over a 122-unit^2 tab: a pointed spur out
    # of the top-right of the apex, plainly visible at 500 px beside the stem's
    # entry flag. Exactly the 1's flag defect of round 75 (ONE_FLAG_BURY) and
    # the italic entry's of this sweep, in the third place it can happen.
    # The start is slid BACK ALONG ITS OWN LINE, so the diagonal keeps its
    # angle, its width function (`pw` still reads the undisplaced p0->p1) and
    # every part of its silhouette that leaves the stem. Swept: 0 leaves 122
    # units^2 above the top, S*0.10 leaves 7.6, S*0.20 leaves none with 5.0
    # units to spare and S*0.25 with 8.7 -- and from S*0.20 on, the ink OUTSIDE
    # the stem stops changing at all (19786.6 units^2 at both 0.20 and 0.30),
    # which is the proof that only the buried face is moving.
    # The OPEN construction below does not want this: its diagonal deliberately
    # stands clear of the stem, so there is nothing for it to be buried in.
    _ux, _uy = p0[0] - p1[0], p0[1] - p1[1]; _L = math.hypot(_ux, _uy) or 1.0
    p0d = (p0[0] - _ux / _L * S * FOUR_DIAG_BURY, p0[1] - _uy / _L * S * FOUR_DIAG_BURY)
    dg = diagonal(p0d, p1, wd)
    if not pen.ITALIC and not FOUR_OPEN:
        # ROUND 233 (R39, R40), owner 2026-09-18 on the roman 4: *"correct bad
        # join in counter where I highlighted"* (his box: the top-left, where
        # the diagonal's outer edge meets the stem) and *"correct bad join on
        # middle left"* (the bar's left end). Measured on the built outline:
        # at the TOP the diagonal's outer edge crossed the stem's left edge 5.9
        # units below the stem's top corner, so the corner stood as a 6-unit
        # vertical ledge with a 1-unit jog where the buried face's corner met
        # it; at the BAR the centerline ended at (8.4, 196.2) on the bar's
        # centerline, so the square end face -- 41 units across a 59-degree
        # stroke -- reached to (-9.3, 206.7): 9 units LEFT of the bar's left
        # face, a tooth standing out of it, and the bar's own top-left corner
        # was gone under it. Both are one rule now: THE DIAGONAL'S OUTER EDGE
        # RUNS FROM THE BAR'S TOP-LEFT CORNER TO THE STEM'S TOP-LEFT CORNER,
        # and the centerline is that line pushed in by half the width. Each
        # end face then has its outer corner exactly ON the corner it joins
        # and its inner corner inside the stem or the bar (the face at the
        # top spans from the stem's corner to (xs - 9, D - 21), at the bar
        # from the corner to (35, bar_y + 3)). What moved: the diagonal's angle
        # 59.4 -> 59.3 degrees, its top end from (xs - 16.8, D) to (xs - 26.5,
        # D - 10.5), its foot from (8.4, bar_y) to (17.7, bar_y + 13.3); the
        # width is still pw() x diag (41.1), read on the corner-to-corner
        # direction. And the width SOLVER answered: with the 9-unit tooth gone
        # from the left the 4's ink read narrower than its target, so
        # `solve_widths` moved W['4'] 0.88 -> 0.90 (w 422 -> 432, xs 295.7 ->
        # 302.3) -- the bar is 10 units longer and the stem 7 further right,
        # which is the builder's own rule and not a choice made here.
        # FOUR_DIAG_BURY is no longer needed here (the italic and the open 4
        # keep it).
        wtop = PR.stem_width(TH_V * _o4.get('stem', 1.0), pen.ENT, 1.0)
        ctop = (xs - wtop / 2, D); cbar = (0.0, bar_y + barw / 2)
        ux, uy = ctop[0] - cbar[0], ctop[1] - cbar[1]; L = math.hypot(ux, uy) or 1.0
        ux, uy = ux / L, uy / L; nx, ny = -uy, ux                      # the outer (up-left) normal
        wd = pw(cbar, ctop, _o4.get('diag', 0.75))
        p0d = (ctop[0] - nx * wd / 2, ctop[1] - ny * wd / 2)
        p1 = (cbar[0] - nx * wd / 2, cbar[1] - ny * wd / 2)
        dg = diagonal(p0d, p1, wd)
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
FOUR_BOW = 0.10         # how far left of the start the bow's upper control sits, x S
# THE 4'S OPTIONS. The 4 is the second-lightest figure in BOTH styles -- roman
# stroke 49.7 against a figure median of 65.9 (-24.6%), italic 49.7 against
# 65.5 (-24.1%) -- and no reference is anywhere near that: Georgia's 4 is -14%
# of its figures, Coelacanth's -12%, Pagella's -2%, Poetica's +6%. A 4 is
# legitimately a little lighter than its family (it is three thin strokes over
# a big open counter), but not by a quarter.
# (b) simply PUTS THE WEIGHT BACK -- all three strokes up together, so the
# figure keeps the proportions it has and only stops reading as a hole.
# (c) puts the same weight in UNEVENLY, which is the file's own standing todo
# from round 75 (*"reduce the thickness of the 4's top-left stroke"*) and is
# how Poetica and Coelacanth draw it: a thin diagonal against a thick stem and
# a thick bar, so the 4 gains colour without gaining a heavy diagonal.
# The closed construction (his round-75 revert) is kept in every option; the
# open/curved 4 behind `FOUR_OPEN` is NOT re-offered, because he ruled it out.
FOUR_OPT = {
    'b': dict(diag=0.86, bar=1.12, stem=1.10),
    'c': dict(diag=0.62, bar=1.34, stem=1.20),
    # ROUND 255 (owner 2026-09-19, "optically balanced with rest of
    # numerals"), roman only. Two things measured off, and neither is the
    # diagonal. On a 1000-unit-x-height raster (`shape.py`), each stroke as a
    # fraction of that face's own 0's thick side:
    #                    bar     stem    diagonal   bar centre above the baseline (units at xh 429)
    #   Georgia          0.59    0.86     0.42        +68
    #   Flanker          0.96    0.96     0.36        +35
    #   Coelacanth       1.10    0.81     0.41        +37
    #   Pagella          0.82    1.00     0.51        +25
    #   Poetica          0.98    1.26     0.57        +88
    #   Big Caslon       --      --       --          +39
    #   Albo 4a (today)  0.55    0.88     0.48        -13
    # The stem (0.88) and the diagonal (0.48) are inside the references'
    # bands; the BAR is under every one of them (0.55 against 0.59-1.10), and
    # the bar sits 13 units BELOW the baseline where every reference puts it
    # 25-88 ABOVE (median 38) -- so in `1234` the 4's bar runs under the 1's
    # feet. `bar_y` is new: the bar's centre as a fraction of the figure's
    # height, 0.30 today; 0.378 puts the centre at +38. Raising it steepens
    # the diagonal 31 -> ~36 degrees, which is TOWARD the references (29-41,
    # median 38), and leaves 0.34 of the height under the bar (they run
    # 0.27-0.37). The ridge "stroke" of a 4 sits on its longest stroke, the
    # diagonal, so the -33% it reads against the shipped five is what a 4 IS
    # (Georgia's reads -18% of its 0); the colour, 0.76 of the 0's, is inside
    # their 0.69-0.96. Hence no arm here thickens the diagonal.
    'd': dict(bar_y=0.378),                                  # the bar RAISED to the references' line; nothing else
    'e': dict(bar_y=0.378, bar=1.45),                        # ...and the bar at the CAPITALS' bar weight (61 units, 0.94 of pen.CAP_BAR; 0.75 of the 0's thick -- Georgia 0.59, Pagella 0.82)
    'f': dict(bar_y=0.378, bar=1.70, diag=0.80),             # ...the bar at the references' median (71 units, 0.90) and the diagonal at theirs (0.42): Coelacanth's, Flanker's
}
FOUR_OPT_IT = {k: FOUR_OPT[k] for k in ('b', 'c')}   # round 255: the italic keeps round 229's two and draws 'a' under d-f (the table was shared until then; b and c are the same dicts)

# THE 5'S OPTIONS, and they are two independent questions, so there are four
# arms rather than three.
# THE FLAG. `FIVE_TOP_INSET` is where the top bar's right end stops relative
# to the bowl's rightmost ink, and -24 is his own ruling of 2026-09-13 off a
# four-arm ladder (-36 / -24 / -12 / 0). The references cut it much shorter:
# measured as a fraction of the figure's ink width, Georgia's top bar stops
# 0.19 of the width short of the bowl's right edge and Poetica's 0.16, where
# Albo's -24 is 0.07. (b) takes it to -78, which is 0.21.
# THE WIDTH. The 5 is the worst-fitting figure in the face by the solver's own
# reckoning: its target is 321 units of ink and it is built at 387, **+20.6%**,
# because the width multiplier is on its 0.70 clamp. It is also the widest
# figure relative to the references -- 0.911 of the 0's advance in the roman
# and 0.941 in the italic, against Georgia 0.861, Poetica 0.778, Coelacanth
# 0.720 and Pagella 0.899. (c) draws it at 338 instead of 400, which lands the
# ink on 321. (d) is both, and is the arm the set recommendation uses.
FIVE_OPT = {
    'b': dict(inset=-78.0),
    'c': dict(W=338.0),
    'd': dict(W=338.0, inset=-78.0),
}

@glyph('5')
def g_five(c):
    _o5 = _okw('5', FIVE_OPT)
    D = c["figH"]; w = W_(c, '5', _o5.get('W', 400)); r = D * 0.31
    st = stem(S * 0.3 + S / 2, D * 0.5, D + 10, w=TH_V * 0.85 * pen.CAP_STEM, top=None, foot=None, ent=0.0)   # round 51: vstem at 0.85 x the cap stem
    bowl = superellipse(w * 0.5, r, w * 0.55, r + OVER - TH_H / 2, math.radians(125), math.radians(-160), BOWL_K)
    if pen.ITALIC and FIVE_TAIL_END:
        bw = stroke(bowl, pen_widths(bowl, widths([(0.0, 0.45), (0.12, 1.0), (0.70, 1.0),
                                                   (1.0, FIVE_TAIL_END)])))
    elif pen.ITALIC:
        bw = stroke(bowl, pen_widths(bowl, widths([(0.0, 0.45), (0.12, 1.0), (0.85, 1.0), (1.0, 1.25)])), cut1=CUT)
    else:
        # ROUND 275 -- THE BOWL'S END IS THE c's TOP FINIAL (owner 2026-09-19:
        # "change out round finials (like c top serif)"). It flared 1.25 over
        # its last 15% into the 20-degree cut. Now PR.finial_widths /
        # PR.finial_cut, held to the c's own end width (rounds.c_top_width)
        # as the 3's lower end is. The top is a bar with a hanging wedge and
        # is not a finial.
        from .rounds import c_top_width
        bw = stroke(bowl, PR.finial_widths(pen_widths(bowl, widths([(0.0, 0.45), (0.12, 1.0), (1.0, 1.0)])), False, floor=c_top_width()), cut1=PR.finial_cut(bowl, False))
    # the top ends FIVE_TOP_INSET from the bowl's rightmost ink (round 63 ran
    # it NINE_OVERHANG past; before that it ended 0.95 w, 72 units inside);
    # the square end and the hanging wedge's apex both sit at x1, so x1 is
    # the bar's rightmost ink
    x1 = geom.bbox(bw)[2] + _o5.get('inset', FIVE_TOP_INSET)
    top = bar(S * 0.3, x1, D, max(TH_H, S * 0.5), align='center', cut0=CUT, wedges=[('right', -1)])   # round 51: centred ON D, its top at D + 28
    return geom.ink([top, st, bw])

# THE 6'S OPTIONS.
# (b) IS THE ONE OPTION IN THIS ROUND THAT IS A CONSTRUCTION AND NOT A DIAL:
# **the 6 drawn as the 9 turned through 180 degrees**, which is how Georgia and
# Big Caslon draw the pair. Measured: Georgia's 6 and 9 have the SAME ink width
# (423 units at a 429 x-height) and the same advance (504); Big Caslon's are
# 417 and 464. Albo's are 379/462 in the roman and 447/536 in the italic -- two
# separate drawings that have drifted apart, and in a run like `1969` the 6 and
# the 9 do not look like each other. This arm builds `g_nine` at the 6's own
# figure height, turns it about its bbox centre and lands it on the default
# 6's own left and bottom, so the pair is a rotation by construction and
# cannot drift again. Two consequences, both named rather than discovered:
# the 6 then takes the 9's SOLVED WIDTH MULTIPLIER (`W_(c, '9', ...)` inside
# `g_nine`), which is what makes the two equal and leaves `W['6']` inert; and
# the 9's terminal treatment comes with it -- the roman's wedge flag ends up at
# the top right of the 6 and the italic's run-out taper likewise, where today
# the 6's tail simply thins to 0.12.
# (c) is the quieter answer to the same complaint: a BIGGER BOWL and a SHORTER
# tail, so the 6 carries its weight low the way Georgia's does, without
# changing what the terminal is.
SIX_OPT = {
    'b': dict(rotate_nine=True),
    'c': dict(r=0.325, tip=(0.80, -46.0)),
    # ROUND 233 (R41), owner 2026-09-18: *"correct end of tail and give me
    # options to choose from."* 'a' is the corrected run-out (see _six_draw);
    # these end the same tail four other ways, and two move its reach. Roman
    # only (SIX_OPT_IT keeps b and c).
    'd': dict(end='cut', end_w=0.30),           # a blunt PEN CUT: the tail stops at 0.30 of its run width (14 units) on the family's 20-degree face
    'e': dict(end='ball', end_w=0.40, ball=0.22),   # a small BALL: the stroke thins to 0.28 then a round of 0.22 S radius caps it
    'f': dict(end='flag', end_w=0.45, flag=0.55),   # a WEDGE: square face at 0.45 and the family's diagonal end wedge off its upper corner, at 0.55 (the 9's flag is 0.9)
    'g': dict(tip=(1.05, 0.0)),                 # LONGER: the tip 32 units further right and 10 higher, the run-out as 'a'
    'h': dict(tip=(0.62, -40.0)),               # SHORTER: 37 units less reach and 30 lower
    'i': dict(end='cut', end_w=0.30, tip=(0.62, -40.0)),   # ROUND 250, owner 2026-09-18: "d and h blunt and short" -- d's pen cut on h's shorter tail; ships
}
SIX_OPT_IT = {k: SIX_OPT[k] for k in ('b', 'c')}

def _six_draw(c, D, o):
    (solid, oo, i), rx, r, ry = six_bowl(c, D, r_frac=o.get('r', 0.29)); cx = rx + TH_V / 2
    _tx, _ty = o.get('tip', (0.85, -10.0))
    p0 = (cx - rx, r); tip = (cx + rx * _tx, D + _ty)
    top = cubic(p0, (p0[0], p0[1] + ry * 1.5), (tip[0] - rx * 0.55, tip[1] - rx * 0.75), tip)
    base = pen_widths(top); prof = widths([(0.0, 0.15), (0.06, 1.0), (0.65, 1.0), (1.0, 0.12)])
    wfun = lambda u: max(base(u), SIX_TAIL_FLOOR * S) * prof(u)   # the floor under the pen, the profile over both
    if pen.ITALIC:
        return geom.ink([solid, stroke(top, wfun)])
    # ROUND 233 (R41), owner 2026-09-18: *"correct end of tail."* The profile
    # above is a smoothstep from 1.0 at 0.65 to 0.12 at 1.0, and a smoothstep
    # has ZERO slope at its end: measured on the built tail, from t 0.91 (12.8
    # wide) to the tip (5.8) the width falls 7 units over 55 -- the last 50
    # units are a parallel-sided needle ending on a square 5.8-unit face, a
    # stub, and where the needle begins (t ~0.94) is exactly the bend he
    # circled. The fix keeps the tail byte-for-byte to t 0.94 (8.4 wide there,
    # as before) and then runs the width out LINEARLY to a point over the last
    # 6% (36 units, three samples): no stub, no square face. The 0.55 S floor
    # (his round-64 ruling) is untouched.
    end = o.get('end')
    if end is None:
        w94 = wfun(0.94)
        wf2 = lambda u: wfun(u) if u <= 0.94 else max(0.6, w94 * (1.0 - u) / 0.06)
        return geom.ink([solid, stroke(top, wf2)])
    ew = o.get('end_w', 0.30)
    if end == 'cut':
        prof2 = widths([(0.0, 0.15), (0.06, 1.0), (0.65, 1.0), (1.0, ew)])
        return geom.ink([solid, stroke(top, lambda u: max(base(u), SIX_TAIL_FLOOR * S) * prof2(u), cut1=CUT)])
    if end == 'ball':
        prof2 = widths([(0.0, 0.15), (0.06, 1.0), (0.65, 1.0), (0.86, 0.28), (1.0, ew)])
        rb = S * o.get('ball', 0.22); d = tangents(top)[-1]
        ctr = (tip[0] - d[0] * rb * 0.55, tip[1] - d[1] * rb * 0.55)
        ball = geom.poly(superellipse(ctr[0], ctr[1], rb, rb, 0.0, 2 * math.pi, 2.0)[:-1])
        return geom.ink([solid, stroke(top, lambda u: max(base(u), SIX_TAIL_FLOOR * S) * prof2(u)), ball])
    if end == 'flag':
        prof2 = widths([(0.0, 0.15), (0.06, 1.0), (0.65, 1.0), (1.0, ew)])
        wf3 = lambda u: max(base(u), SIX_TAIL_FLOOR * S) * prof2(u)
        return geom.ink([solid, stroke(top, wf3), end_wedge(top, wf3(1.0), False, 1, scale=o.get('flag', 0.55))])
    return geom.ink([solid, stroke(top, wfun)])

@glyph('6')
def g_six(c):
    D = c["figH"]; o = _okw('6', SIX_OPT, SIX_OPT_IT)
    if o.get('rotate_nine'):
        import shapely.affinity as _aff
        ref = _six_draw(c, D, {})                      # today's 6, for its box only
        g = _aff.rotate(g_nine(c), 180, origin='center')
        x0, y0, _, _ = geom.bbox(g); rx0, ry0, _, _ = geom.bbox(ref)
        return _aff.translate(g, rx0 - x0, ry0 - y0)
    return _six_draw(c, D, o)

# ============================== THE 7'S OPTIONS ==========================
# Owner 2026-09-18: *"improve both 7s."* They are two different faults.
#
# THE ROMAN 7 HAS NEVER BEEN TOUCHED and is the worst-fitting figure in the
# style: stroke 51.9 against a figure median of 65.9 (**-21%**), and
# thin/stroke 0.97 -- the FLATTEST glyph in the roman, a constant-width bar
# meeting a constant-width diagonal. Round 219 fixed exactly this in the
# italic (0.94 -> 0.83) and the roman was left where it was; `SEVEN_BAR_W` and
# `SEVEN_DIAG_W` are SHARED between the styles, which is round 213's leak, so
# every roman option here goes through the option table and NOT through those
# two constants. What the references do with the same two strokes, measured at
# one x-height: Georgia's 7 cuts 2.06 thick to thin, Coelacanth's 2.25,
# Poetica's 2.38, Big Caslon's 4.25 -- and Flanker's is 1.28, i.e. flat like
# Albo's, but it pays for that with a leg that descends to -311 where every
# other face stops between -136 and -233.
#   (b) GEORGIA'S: the bar thickened and TAPERED to the mitre, the leg thinned.
#       The whole contrast is in the two strokes' relative weight.
#   (c) FLANKER'S: a heavier bar still, and the leg tapers along its own run
#       as well -- `bar(prof=)` plus the taper branch the italic already uses,
#       with the curve off, because a straight leg is the roman's.
#   (d) WEIGHT FIRST: the least shape change that puts the figure's stroke on
#       its family. Bar and leg both up, a light bar taper, nothing else.
#
# THE ITALIC 7 CARRIES FIVE OF HIS OWN RULINGS and every option keeps all five
# -- the pressed foot that grows out of the taper (round 215, *"212 wins but
# needs serif on end"*), the tapering bar and the thinning leg (round 219,
# *"adjust 7's strokes so it varies pleasantly"*), the leg that curves to
# vertical at the foot (round 212), the foot at 0.30 of the drawn width (round
# 215's revert), and the weight matched to the 6 (round 212). What varies is
# HOW FAR, in one direction or the other:
#   (b) MORE modulation -- the bar tapers to 0.42 instead of 0.55 and the leg
#       starts thinning at 0.45 of its run instead of 0.55.
#   (c) LESS -- 0.72 and 0.68, for a steadier 7 in a column of figures.
#   (d) HEAVIER, modulation as shipped: the 7 is the lightest figure by colour
#       in both styles (0.171 italic, 0.147 roman, against medians of 0.215
#       and 0.223) and round 212 recorded that colour cannot converge by
#       matching strokes. This arm answers the colour instead of the stroke.
#
# AND THE ROMAN BAR HAS A CLIFF AT 1.50, WHICH IS THE FITTER AND NOT THE EYE.
# `_body_edges` reads a glyph's left edge as the 20th percentile of its
# per-row ink extremes. The roman 7's left side is its own open white -- the
# bar's underside -- so while the bar is shallow that percentile lands on the
# LEG and the fitter gives the 7 a wide left bearing; once the bar is deep
# enough, the percentile lands on the BAR and the bearing collapses. Laddered
# on the tightest figure pair (`cmp_figure_space --body`), everything else
# held: 1.28 / 1.36 / 1.42 / 1.45 / **1.48** all read 0.0934 em, and 1.52 /
# 1.56 read **0.0519**, 1.70 reads 0.0491. The pairs that close are every
# `x7`. So (b) stops at 1.48, one step under the cliff, and (c) goes past it
# deliberately -- it is Flanker's 7 and Flanker's bar is that heavy -- with
# the cost recorded rather than hidden. `ALBO_FIG_7_BAR` re-runs the ladder.
SEVEN_OPT = {
    'b': dict(bar_w=1.48, diag_w=0.70, bar_mod=0.74),
    'c': dict(bar_w=1.70, diag_w=0.74, bar_mod=0.60,
              leg_taper=0.62, leg_from=0.55, curve=0.0, flare=1.0),
    'd': dict(bar_w=1.48, diag_w=0.98, bar_mod=0.68,
              leg_taper=0.70, leg_from=0.60, curve=0.0, flare=1.0),
    # ROUND 255 (owner 2026-09-19, "optically balanced with rest of
    # numerals"), roman only -- i-k, because e-h are the ITALIC 7's rows and
    # `ALBO_FIG_7=e` on a roman build was proved to change nothing in round
    # 231; that proof stands. Measured on a 1000-unit-x-height raster
    # (`shape.py`), the bar at mid-span and the leg on its own rows, each as a
    # fraction of that face's own 0's thick side, plus the bar's taper (its
    # thickness at 0.60 of its span over 0.25) and the 7's top against its 0's:
    #                    bar     leg    bar/leg   taper   top vs the 0
    #   Georgia          0.75    0.47    1.58     0.98     -3%
    #   Flanker          0.96    0.86    1.12     0.99     -1%
    #   Coelacanth       0.82    0.44    1.87     0.98     +4%
    #   Pagella          1.10    0.72    1.51     0.98     +1%
    #   Poetica          1.37    0.70    1.92     0.90     +3%
    #   Albo 7a (today)  0.70    0.55    1.29     0.99     -6%
    # Three findings. The bar is under every reference (0.70 against
    # 0.75-1.37, median 0.96) and the leg is at the bottom of their band (0.55
    # against 0.44-0.86, median 0.70); the references' bars are FLAT (taper
    # 0.90-0.99), so b-d's tapered bars are not what they do; and the 7 tops
    # 28 units under the round figures (its box is 0.64 CAP, the 0's 0.66 plus
    # overshoot) where every reference tops within 4% of its 0. `top_up` is
    # new: units added to the figure's height, so the bar's top rises and the
    # leg's foot stays on its line; 14 puts the top on the 0.66 box line, 3%
    # under the 0's overshoot, which is Georgia's 7. The fitter's CLIFF at bar
    # 1.50 (above) is still there: i stops one step under it, j goes past it
    # for the references' bar/leg and pays the `x7` bearing for it -- the
    # `cmp_figure_space --body` number is in the round's report.
    'i': dict(bar_w=1.48, diag_w=0.90, top_up=14.0),                  # a FLAT bar one step under the cliff (measured 0.78 of the 0's thick), the leg to the references' median (measured 0.64), the top on the box line
    'j': dict(bar_w=1.80, diag_w=0.90, top_up=14.0),                  # the bar at the 0's own thick (measured 0.95; bar/leg 1.48, beside Pagella's 1.51) -- past the cliff, cost recorded
    'k': dict(bar_w=1.48, diag_w=0.90, top_up=14.0, foot_x=0.18),     # i with the leg at the references' angle: the foot at 0.18 of the width (Georgia 0.19, Flanker 0.18) puts the leg at ~24 degrees against today's 22 (they run 24-30)
    # ROUND 361 -- two directions i-k do not cover. Owner 2026-09-23 asked
    # again for "five optically balanced version of 7 that fit with the rest
    # of the numerals"; i, j and k were drawn for that same words in round 255
    # and never ruled, so they stand as three of the five and these are the
    # other two. Both take i's leg (0.90) and i's top, and differ only in what
    # they do with the BAR and the FOOT -- the two places the other figures
    # put mass that this one does not.
    'l': dict(bar_w=1.62, diag_w=0.90, top_up=14.0, bar_mod=0.74),    # i's leg under a TAPERED bar: heavier at the stem, thinner at the mitre, so the figure gains colour without gaining a slab. i-k are all flat bars
    # `flare` lives inside the `if _leg:` branch, so a row that sets it without
    # a `leg_taper` is INERT -- caught by measuring, where m read byte-equal to
    # i on all four numbers. It needs the tapered leg to press against.
    'm': dict(bar_w=1.48, diag_w=0.90, top_up=14.0,
              leg_taper=0.72, leg_from=0.58, curve=0.0, flare=1.45),  # i with a FLARED FOOT: the leg tapers and then the pen presses at the baseline, where every other figure has a terminal and this one has a bare cut. The italic 7 has carried one since round 219
}
# ROUND 231 -- FOUR MORE ITALIC 7s, e TO h. Owner 2026-09-18: *"give me more
# options for the italic 7 that match the rest of the numerals and font's
# style."* b, c and d vary HOW FAR the shipped 7's own dials go; these four are
# different GESTURES, each taken from a stroke that already ships elsewhere in
# these ten figures, so the 7 is made out of the family's own parts rather than
# tuned against it.
#
# WHAT THE OTHER NINE ACTUALLY DO, measured on the shipped italic and quoted
# here because that is what "match the rest of the numerals" means:
#   the 6's tail   a pen stroke running out to 0.12 of its width at the tip,
#                  with a floor of 0.55 S under the pen (round 64's ruling)
#   the 2's base   the figure's mass at the bottom, the bar at 1.22 of the
#                  bar weight, and its ARC entering thin at the top left
#   the 9's tail   runs out to 0.35 and ends on a face sheared -34 degrees
#                  (NINE_TAIL_END, NINE_END_CUT -- round 195, the owner's
#                  *"remove bottom side of serif in 9"*)
#   the 1's foot   a brushed PRESS, not a slab: the stroke thins and the pen
#                  spreads as it lands (round 215)
#
#   (e) THE LEG TURNS UPRIGHT EARLIER, AND THE PRESS SITS LOWER. Round 212's
#       curve holds the diagonal's own line for 0.60 of the chord and only
#       then bends; this holds it for 0.34, so the foot is the 6's tail turned
#       over -- a long arc rather than a straight run with a bend at the end --
#       and the press moves from 0.94 to 0.975 of the run so it happens ON the
#       line. Both of the owner's foot rulings are kept: the foot is still
#       vertical (round 212) and it is still a press and not a serif (215).
#   (f) THE BAR TAKES A WRITTEN ENTRY. Its left end starts at 0.42 of its
#       depth and swells to full over the first third, as the 2's arc does,
#       and the family's hanging wedge goes with it -- a bracket on a stroke
#       already tapering to nothing is the finial ruled out on the s (209) and
#       on the 1's flag (217). **This is the one arm that sets aside a ruling**:
#       the guide's wedge table gives the 7 a wedge at the bar's left. Nothing
#       else moves.
#   (g) THE LEG ENDS LIKE THE 9'S TAIL. Runs out to 0.35 instead of 0.58 and
#       ends on a face sheared -34 degrees, which is NINE_END_CUT exactly.
#       **This one sets aside round 215's press** (*"212 wins but needs serif
#       on end"*) and says so: the 9's answer to the same question was to take
#       the serif OFF and shear the face, and the two cannot both be true on
#       one foot. Offered because the 7 and the 9 are the style's two long
#       descending tails and today they end differently.
#   (h) THE BAR IS HEAVIER THAN THE LEG, which is what every reference does
#       and Albo's italic uniquely does not. Measured (`seven_ratio.py`, the
#       ridge median of the top 12% of the glyph against the 45-85% band):
#       Coelacanth it **1.85**, Poetica **1.64**, Georgia it **1.55**, Pagella
#       it **1.38**, Flanker it **1.14** -- and Albo's italic **0.98**, a bar
#       very slightly LIGHTER than its own leg. This arm puts it at **1.30**,
#       inside the Flanker-to-Pagella end of that band.
#       IT STOPS THERE BECAUSE THE RATIO AND ROUND 212'S WEIGHT MATCH CANNOT
#       BOTH BE HAD. Laddered (bar/diag -> bar/leg, and the 7's stroke against
#       its own figure family): 1.65/1.02 -> 0.98 at **+0%**; 2.05/0.86 ->
#       **1.30 at -9%**; 2.05/0.78 -> 1.43 at -17%; 2.20/0.82 -> 1.42 at -13%;
#       2.20/0.74 -> 1.59 at -22%. Coelacanth's 1.85 is not reachable on this
#       skeleton at anything like the family's weight. Same shape of trade as
#       round 215's (the legibility measure preferred E and the contrast
#       ruling won); recorded rather than split the difference silently.
#       **THE BRIEF'S OWN IDEA WAS THE OTHER WAY** (*"a lighter bar with a
#       heavier leg ... checked against Flanker's and Poetica's italic 7s"*)
#       and the check refutes it: no reference italic 7 draws a bar lighter
#       than its leg, and Albo already sits at the parity end of the range.
#       Built as `ALBO_FIG_7_BAR=1.30 ALBO_FIG_7_DIAG=1.45` (ratio 0.72) and
#       rejected on that measurement, not on taste; the number is in the
#       report so nobody re-proposes it.
SEVEN_OPT_IT = {
    'b': dict(bar_w=1.80, diag_w=1.18, bar_mod=0.42, leg_from=0.45, leg_taper=0.52),
    'c': dict(bar_w=1.55, diag_w=1.05, bar_mod=0.72, leg_from=0.68, leg_taper=0.66),
    'd': dict(bar_w=1.95, diag_w=1.18),
    'e': dict(hold=0.34, rise=0.62, flare_t=0.975),
    'f': dict(entry=0.42, entry_t=0.33),
    'g': dict(leg_taper=0.35, flare=1.0, end_cut=-34.0),
    'h': dict(bar_w=2.05, diag_w=0.86),
}

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
    _o7 = _okw('7', SEVEN_OPT, SEVEN_OPT_IT)
    # round 255 (i-k): the bar's top may stand above the 0.64 box; the foot
    # stays on the box's floor, so only the height D grows
    D = c["figH"] + _E('ALBO_FIG_7_TOP', _o7.get('top_up', 0.0)); w = W_(c, '7', 440)
    # ROUND 189 -- the owner, 2026-09-17: *"for 7, thin out diagonal and
    # thicken top bar."* Measured against Coelacanth the 7 was effectively
    # MONOLINEAR -- 1.1:1 where Coelacanth is 2.6:1 -- so the two strokes were
    # carrying the same weight and the figure had no colour. These two dials
    # move them in opposite directions, which is what restores the contrast
    # rather than simply making the whole figure heavier or lighter.
    barw = max(TH_H, S * 0.5) * _E('ALBO_FIG_7_BAR',
                                   _o7.get('bar_w', SEVEN_BAR_W_IT if pen.ITALIC else SEVEN_BAR_W))
    p1 = (w * _o7.get('foot_x', SEVEN_FOOT_X if pen.ITALIC else 0.3), 0)
    p0 = (w - S * 0.2, D - barw * SEVEN_DIAG_BURY)
    wd = pw(p0, p1) * _E('ALBO_FIG_7_DIAG',
                         _o7.get('diag_w', SEVEN_DIAG_W_IT if pen.ITALIC else SEVEN_DIAG_W))
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]; L = math.hypot(dx, dy) or 1.0
    ux, uy = dx / L, dy / L; nx, ny = -uy, ux          # the up-right side of a stroke running down-left
    ex, ey = p0[0] + nx * wd / 2, p0[1] + ny * wd / 2  # a point on the diagonal's right edge
    # A TAPERED BAR ENDS AT A DIFFERENT HEIGHT, so it must be mitred at a
    # different x. The bar's end face is laid ON the diagonal's right edge and
    # `x1` is where that edge crosses the bar's CENTRELINE; with `prof` the
    # bar's depth at the mitre is `barw x _mod`, so its centreline there is
    # `D - barw x _mod / 2` -- higher up, where the leaning edge is further
    # right. Solved at the full depth, the tapered bar stops short of the
    # diagonal and leaves a re-entrant step at the top right, plainly visible
    # at 620 px on every option that tapers.
    # MEASURED, not eyeballed: the largest RISE in the rightmost-ink profile
    # over the top quarter of the glyph, at a 900 px x-height. Roman: **10 px
    # of step** on a tapered bar solved at the full depth, **0** solved at the
    # tapered one. Italic: the shipped 7 already carries **5 px** and every
    # option here reads **3** -- so the italic does not want this correction
    # and is left on the shipped rule, which is why the `pen.ITALIC` guard is
    # in the expression. (A white-gap detector reads ZERO on all eight arms:
    # the fault is a re-entrant STEP in the outline, not a hole, and a gap
    # test cannot see it. That cost a wrong reading first.)
    # OPTION 'a' IS UNTOUCHED IN BOTH STYLES: `_o7` is empty there, so the
    # expression is `barw / 2` exactly as before.
    _mod = _E('ALBO_FIG_7_MOD', _o7.get('bar_mod', SEVEN_BAR_MOD if pen.ITALIC else 1.0))
    yc = D - barw * (_mod if (_o7 and not pen.ITALIC) else 1.0) / 2   # the bar's centerline (align='top')
    x1 = ex + ux * (yc - ey) / uy                      # where that edge crosses it: the bar's end
    mitre = -math.atan2(abs(dx), abs(dy))              # the end face parallel to the diagonal
    _leg = _o7.get('leg_taper', SEVEN_TAIL_TAPER if pen.ITALIC else 0.0)
    _legfrom = _o7.get('leg_from', SEVEN_TAIL_FROM)
    _curve = _o7.get('curve', SEVEN_TAIL_CURVE if pen.ITALIC else 0.0)
    _flare = _o7.get('flare', SEVEN_FOOT_FLARE if pen.ITALIC else 1.0)
    # ROUND 231's new levers, all four defaulting to the shipped constants so
    # options a-d are untouched. `hold` / `rise` are the two handles of the
    # curve that takes the leg upright (round 212), so an arm can turn it
    # EARLIER; `flare_t` is where along the run the press begins, so an arm can
    # put the spread LOWER; `end_cut` shears the leg's end face the way the
    # italic 9's tail is sheared (NINE_END_CUT, round 195).
    _hold = _o7.get('hold', SEVEN_TAIL_HOLD)
    _rise = _o7.get('rise', SEVEN_TAIL_RISE)
    _flare_t = _o7.get('flare_t', SEVEN_FOOT_FLARE_T)
    _endcut = _o7.get('end_cut', 0.0)
    if _leg:
        # the lower stroke runs out downward the way the 6's tail runs out
        # upward: a pen stroke on the same line, held to its width until
        # SEVEN_TAIL_FROM and then tapered to the foot.
        if _flare > 1.0:
            # THE PRESS, AND NOT A WAIST. The first cut forced the taper to
            # reach SEVEN_TAIL_TAPER at FLARE_T and spread from there, which
            # put a pinch in the leg -- at 330 px the 7 grew a knee the 6's
            # tail does not have, and past 1.55 it read as a defect rather
            # than a stroke. The stroke thins MONOTONICALLY as it always did;
            # the serif is only the last few percent, where the pen presses.
            _t = (_flare_t - _legfrom) / max(1e-6, 1.0 - _legfrom)
            _w = 1.0 + (_leg - 1.0) * min(1.0, max(0.0, _t))
            prof = widths([(0.0, 1.0), (_legfrom, 1.0),
                           (_flare_t, _w),
                           (1.0, _w * _flare)])
        else:
            prof = widths([(0.0, 1.0), (_legfrom, 1.0), (1.0, _leg)])
        if _curve:
            _L = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
            c1 = (p0[0] + (p1[0] - p0[0]) * _hold,
                  p0[1] + (p1[1] - p0[1]) * _hold)
            c2 = (p1[0] + (p0[0] - p1[0]) * (1 - _curve) * 0.30,
                  p1[1] + _L * _rise * _curve)   # straight above the foot
            path = cubic(p0, c1, c2, p1)
        else:
            path = [p0, p1]
        diag = stroke(path, lambda u: wd * prof(u),
                      cut1=(math.radians(_endcut) if _endcut else None))
    else:
        diag = diagonal(p0, p1, wd)
    # THE BAR'S LEFT END. `a` plants the family's hanging wedge there (the
    # guide's wedge table gives the 7 a wedge at the left and nothing at the
    # right). An arm may instead give it a WRITTEN ENTRY -- the pen landing
    # light and pressing in, which is what the 2's arc does at its top and
    # what every entry stroke in this italic does -- and then the wedge MUST
    # go: a bracket on the end of a stroke that is already thinning to nothing
    # is the finial the owner ruled out on the s in round 209 and on the 1's
    # flag in round 217. `entry` is the bar's width at its left end over its
    # width at the mitre; `entry_t` is how far along the bar it reaches full.
    _entry = _o7.get('entry', 1.0)
    _entry_t = _o7.get('entry_t', 0.30)
    if _entry != 1.0:
        _bp = widths([(0.0, _entry), (_entry_t, 1.0), (1.0, _mod)])
        _wedges = []
    else:
        _bp = widths([(0.0, 1.0), (1.0, _mod)]) if _mod != 1.0 else None
        _wedges = [('left', -1)]
    return geom.ink([bar(0, x1, D, barw, align='top', cut1=mitre,
                         wedges=_wedges, prof=_bp), diag])

# ============================== THE 8'S OPTIONS ==========================
# TWO FAULTS, AND THE FIRST ONE IS A RULING, so it is offered and not shipped.
#
# HEIGHT. In every reference the 8 tops on the 6's line: Georgia 633/633,
# Flanker 620/644, Coelacanth 657/656, Pagella 622/622, Big Caslon 659/660,
# Poetica 562/562. Albo's roman 8 tops at **520 against its 6's 617** and its
# italic at 561 against 639. Against the x-height the references' 8 stands
# 1.31-1.54 x-heights tall and Albo's roman 1.21. That is the single most
# visible thing about a run of Albo's figures -- in `1889` the two 8s sit in a
# dip. It is ALSO the owner's own ruling of 2026-09-13, round 64: *"remake 8
# again but make it shorter so counters can match other numerals or optical
# circles"*, and then *"for 8, C wins but the bottom counter needs to be
# slightly taller"* -- so `a` stays exactly where he left it and the taller 8
# is an option for him to look at. `tall` multiplies BOTH counters' heights,
# not their widths, so the figure grows upward into the box it already owns
# (FIG_BOX['8'] is the 6's, top 0.98 CAP) and does not get wider: at 1.19 the
# roman 8 tops at about the 6's line with a width/height of 0.62, which is
# Flanker's 0.637 and Coelacanth's 0.649 rather than today's 0.693.
#
# CONTRAST. The roman's 8 cuts **1.52** thick to thin where the references run
# 2.05 (Pagella) to 5.29 (Big Caslon); it is the flattest round shape in the
# style. `con` re-spreads the ring's own widths about their geometric mean, so
# the letter's colour does not move, and `oval` has to come with it.
EIGHT_OPT = {
    'b': dict(tall=1.19),
    'c': dict(con=1.85, oval=1.0),
    'd': dict(tall=1.19, con=1.85, oval=1.0),
    # ROUND 233 (R42), owner 2026-09-18: *"redo entire character to match the
    # rest, give me options."* Three DRAWINGS, roman only, against the same
    # references measured on a raster at a 1000-unit x-height (`mref.py`):
    # every one tops its 8 on its 6's line (8/6: Georgia 1.003, Big Caslon
    # 1.004, Coelacanth 0.997, Poetica 1.000; Albo 0.850); the upper lobe is
    # 0.81-0.96 of the lower by width (Georgia 0.89, Caslon 0.96, Coelacanth
    # 0.81, Poetica 0.82; Albo 0.95) and the upper COUNTER 0.75-0.98 of the
    # lower's width (Albo 0.91); and the waist is a CROSSING -- the two
    # strokes cross, so the waist's total ink is 1.6-2.2 strokes (Georgia
    # 437/199, Caslon 340/176, Coelacanth 239/150, Poetica 234/136) and the
    # outer contour pinches in at it. Albo's rings overlap by exactly one bowl
    # stroke ('waist' 1.0), so there is no crossing and the waist is one band.
    'e': dict(upper=0.82, waist=1.65, to_six=True),                       # Georgia's: two family rings on the 6's line, the upper counter 0.82 of the lower's width, overlapping 1.65 strokes so the waist crosses
    'f': dict(written=True, upper=0.82, stress=-25.0),                   # a WRITTEN figure-8: one pen stroke on the lemniscate of Gerono (two teardrops crossing at the waist, no straights), the nib turned 25 degrees so the down-right arm of the crossing is the thick one
    # ROUND 250, owner 2026-09-18: *"make variants of the existing not creative
    # options."* So: today's two-ring 8 (a) with ONE lever moved a little, the
    # way b, c and d are; e-g stay in the table but are not what he asked for.
    'h': dict(tall=1.10),                                                # a little taller (b is 1.19): the 8 tops 43 units higher, still under the 6's line
    'i': dict(upper=0.88),                                               # the upper counter 0.88 of the lower's width (a is 0.95): a lighter top, same height
    'j': dict(waist=1.25),                                               # the rings overlap 1.25 strokes instead of 1.00: the waist pinches, the figure 6 units shorter
    'k': dict(tall=1.10, upper=0.88),                                    # h and i together
    'l': dict(con=1.40, oval=1.0),                                       # a milder contrast than c's 1.85, the counters ovalised with it
    'm': dict(tall=1.10, upper=0.88, waist=1.25),                        # h, i and j together
    'g': dict(upper=0.92, waist=1.65, to_six=True, con=1.85, oval=1.0),  # Big Caslon's: lobes nearly equal (0.92), crossing waist, on the 6's line, with option c's contrast
    # ROUND 255 (owner 2026-09-19, "optically balanced with rest of
    # numerals"; round 250, "make variants of the existing not creative
    # options"), roman only: today's two rings, the counters as his round-64
    # rulings left them, ONE lever each on top of the exact height solve.
    # Measured on a 1000-unit-x-height raster (`shape.py`, the waist found as
    # the one-run band between the two counters -- an ink-minimum finds the
    # lobes' flanks on a ring pair that does not cross, and read 0.59 first):
    #                 8 top / 6 top   upper/lower counter: width   height   outer pinch, of W
    #   Georgia          1.003              0.84          0.92          0.43
    #   Flanker          0.964              0.91          0.87          0.41
    #   Pagella          1.000              0.89          0.86          0.37
    #   Coelacanth       0.997              0.83          0.83          0.28
    #   Poetica          1.000              0.74          0.80          0.35
    #   Big Caslon       1.004              0.98          0.98          0.42
    #   Albo 8a (today)  0.887              0.75          0.69          0.54
    # The lobe ratio (0.85 of the lower by width; theirs 0.81-0.96) and the
    # counters' WIDTH ratio (0.75; theirs 0.74-0.98) are inside the bands. Off
    # are the HEIGHT (11% under the 6 where the nearest reference is 4%), the
    # upper counter's HEIGHT against the lower's (0.69 where they run
    # 0.80-0.98 -- exactly 0.75 / 1.08, the round-64 rulings compounding), the
    # waist (no pinch at all: 0.54 of the width, theirs 0.28-0.43) and the cut
    # (1.52 against 2.05+). `up_tall` is new: the upper counter's height x
    # this, its width untouched; 1.22 puts the height ratio at 0.85, the
    # references' median. `to_six` (option e's solve) lands the top ON the 6's
    # current line -- the 6 moved in round 250 and b's fixed 1.19 now stands 3
    # units over it.
    'n': dict(to_six='shipped'),                                         # today's 8 solved exactly onto the shipped 6's line (its tail tip); nothing else moves
    'o': dict(to_six='shipped', up_tall=1.22),                           # ...and the upper counter taller, to the references' 0.85 of the lower's height
    'p': dict(to_six='shipped', up_tall=1.22, con=1.40, oval=1.0),       # ...and option l's mild cut (1.40) with it, counters ovalised
    # NEGATIVE RESULT, so nobody offers it again: option j's `waist` 1.25 was
    # built on top of o and measured -- the outer pinch went 0.514 -> 0.556 of
    # the width, WIDER. On two rings that do not cross, a deeper overlap puts
    # the narrowest section into wider parts of each ring; a pinch like the
    # references' needs lobes that narrow toward the waist (option f's
    # teardrops), which round 250 ruled out as "creative". Not offered.
    'q': dict(to_six='shipped', upper=0.84, up_tall=1.09),               # ...o's height ratio (0.84 x 1.09 / 1.08 = 0.85) with the upper counter WIDER: 0.84 of the lower's width, Georgia's (theirs 0.74-0.98; a is 0.75)
}
EIGHT_OPT_IT = {
    'b': dict(tall=1.16),
    'c': dict(con=3.40),
    'd': dict(tall=1.16, con=3.40),
}

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
    _o8 = _okw('8', EIGHT_OPT, EIGHT_OPT_IT)
    _tall = _o8.get('tall', 1.0)
    bw2 = (x1 - x0 - 2 * sp) * EIGHT_LOWER              # the lower counter's width, as built
    bw1 = bw2 * _o8.get('upper', EIGHT_UPPER)
    # round 233: the 6's own top, in this shared box (FIG_BOX['8'] is the
    # 6's), for the options that put the 8 on the 6's line
    if _o8.get('to_six') or _o8.get('written'):
        _c6 = dict(c); _c6['figH'] = Dr
        # round 255 (n-q): `to_six='shipped'` solves onto the 6 THIS BUILD
        # draws -- the shipped i since round 250, whose shorter tail tops 31
        # units under the round-233 6 that e/g (True) still aim at; e and g are
        # left on that older line so they build as they did.
        _o6 = _okw('6', SIX_OPT, SIX_OPT_IT) if _o8.get('to_six') == 'shipped' else {}
        six_top = geom.bbox(_six_draw(_c6, Dr, _o6))[3]
    _uptall = _o8.get('up_tall', 1.0)    # round 255 (o-q): the upper counter's height alone, x this
    cw2, ch2 = bw2 + 2 * sp, bw2 / EIGHT_COUNTER_WH * EIGHT_LOWER_TALL * _tall + 2 * sp     # drawn (pre-spread) targets
    cw1, ch1 = bw1 + 2 * sp, bw1 / EIGHT_COUNTER_WH * _tall * _uptall + 2 * sp
    # Round 98 (owner 2026-09-14: "without reshaping the two counterspaces,
    # give me options for making an 8 that visually fits the rest of the
    # numbers"): the OUTER's levers, each an env override for the options
    # page, the counters re-solved to the same boxes under every one of them.
    E = lambda k, d: float(os.environ.get(k, d))
    _w8 = EIGHT_W_IT if pen.ITALIC else 1.0
    w_up, w_lo = E('ALBO_8_W_UP', _w8), E('ALBO_8_W_LO', _w8)   # stroke weight x, upper / lower ring
    waist = E('ALBO_8_WAIST', _o8.get('waist', 1.0))               # the rings' overlap, x one bowl stroke (round 233: >1 makes the strokes CROSS)
    lean = E('ALBO_8_LEAN', 0.0)                                   # the upper ring's centre, units right of the lower's
    floor_ = E('ALBO_8_FLOOR', EIGHT_FLOOR_IT if pen.ITALIC else EIGHT_FLOOR) * S                    # the hair floor, x the stem (the 6's tail is 0.55)
    kk = E('ALBO_8_K', 0.0) or None                                # the outer's squareness (BOWL_K 2.1 when unset)
    rot_up = math.radians(E('ALBO_8_ROT', 0.0))                    # the upper ring's tilt
    rx2, ry2 = ring_for_counter(0.0, 0.0, cw2, ch2, w_scale=w_lo, k=kk, floor=floor_)
    rx1, ry1 = ring_for_counter(0.0, 0.0, cw1, ch1, w_scale=w_up, k=kk, floor=floor_, rot=rot_up)
    cx = rx2
    y2 = -OVER + ry2                                     # the lower ring's bottom at -OVER
    y1 = -OVER + 2 * ry2 - bowl_hair() * waist + ry1     # over the lower by one bowl stroke (x waist)
    # OWNER 2026-09-17: *"add line contrast to 8."* Measured against Coelacanth
    # the figure was nearly monolinear -- 1.63:1 against its 3.59:1, with thins
    # of 52 units where the reference's are 23. The FLOOR is not what was
    # binding it: lowering EIGHT_FLOOR from 0.65 through 0.50, 0.40 and 0.32
    # moved the contrast 1.63 -> 1.69 and then stopped, because the family's
    # bowl profile never asked for anything thinner. `con` re-spreads the ring's
    # own widths instead. Italic only -- the roman's 8 is not what he is looking
    # at, and `ALBO_8_CON` defaults to 1.0 there.
    con8 = E('ALBO_8_CON', _o8.get('con', EIGHT_CON if pen.ITALIC else 1.0))
    # AND THE COUNTER NEEDS MORE SMOOTHING TO CARRY IT. `ring` offsets the
    # counter inward by the width at each point, so a width that now swings
    # nearly twice as far swings the inner contour with it and the counter
    # developed a visible kidney-shaped pinch at the sides -- the same trap
    # `nib_widths` records, an inner offset cornering where the width changes
    # fast. counter_smooth 2 -> EIGHT_CSM.
    csm = int(E('ALBO_8_CSM', EIGHT_CSM if pen.ITALIC else 2))
    _st = math.radians(FIG_STRESS) if pen.ITALIC else 0.0
    # THE OVALISE IS WHAT LETS A RING CARRY CONTRAST AT ALL (round 204's cure
    # for the g's bowl, round 211's for these). The roman's 8 has never needed
    # it because its `con` is 1.0; an option that raises `con` must switch it
    # on in the same breath, or the counter necks into a kidney -- which this
    # file's own EIGHT_CON note records, measured, at counter_smooth 2, 7 and
    # 14 alike.
    _ov = E('ALBO_8_OVAL', FIG_OVAL if pen.ITALIC else _o8.get('oval', 0.0))
    # ROUND 305 -- the roman 8's contrast levers, which were italic-gated with
    # no way in. `ALBO_8_OVAL` and `ALBO_8_STRESS` now reach both styles (they
    # default to exactly what each style had), and `ALBO_8_NIB` puts the two
    # rings on a true nib: "thin,phi" or "thick,thin,phi", x the stem.
    _st = math.radians(E('ALBO_8_STRESS', math.degrees(_st)))
    _nib = os.environ.get('ALBO_8_NIB')
    if _nib:
        _v = [float(x) for x in _nib.split(',')]
        _nib = (1.0, _v[0], _v[1]) if len(_v) == 2 else tuple(_v)
    else:
        _nib = None
    if _o8.get('written'):
        # ROUND 233 option f -- THE WRITTEN 8. One pen stroke: the upper loop
        # from its lower-right round over the top to its lower-left, a straight
        # crossing down-right to the lower loop's upper-right, the lower loop
        # down its right side round the bottom and up its left, a crossing
        # up-right back to the start. Each loop is an ellipse placed so the two
        # crossings are its tangents (docstring of _fig8_path), so the path is
        # tangent-continuous everywhere and the two crossings meet at the
        # waist's centre -- which is what the references' waists ARE. The pen:
        # the bowl profile with the nib turned `stress` degrees, so the
        # down-right crossing runs across the nib (thick) and the up-right one
        # along it (thin), the way a written 8 comes out. Loop radii from the
        # same counter targets as the rings (outer radius less half the pen);
        # the loops' heights are then scaled together so the figure bottoms at
        # -OVER and tops on the 6's line, as options e and g do.
        a1, b1 = rx1 - TH_V * w_up / 2, ry1 - TH_H * w_up / 2
        a2, b2 = rx2 - TH_V * w_lo / 2, ry2 - TH_H * w_lo / 2
        psi = None; st8 = math.radians(_o8.get('stress', -25.0))
        sc = 1.0; g8 = None
        for _ in range(5):
            path = _fig8_path(cx, 0.0, a1, b1 * sc, a2, b2 * sc, psi)
            wf8 = PR.bowl_widths(path, widths([(0.0, 1.0), (1.0, 1.0)]), floor=S * 0.35, stress=st8)
            g8 = stroke(path, wf8, pieces=True)
            x0_, y0_, x1_, y1_ = geom.bbox(g8)
            import shapely.affinity as _aff
            g8 = _aff.translate(g8, 0, -OVER - y0_)
            got = y1_ - y0_; want = six_top + OVER
            if abs(got - want) < 0.5: break
            sc *= 1 + (want - got) / (b1 + b2) / 2 * 1.0
        return g8
    if _o8.get('to_six'):
        # options e/g: solve `tall` so the stack tops on the 6's line
        for _ in range(6):
            top8 = y1 + ry1
            if abs(top8 - six_top) < 0.3: break
            _tall *= (six_top + OVER) / (top8 + OVER)
            ch2 = bw2 / EIGHT_COUNTER_WH * EIGHT_LOWER_TALL * _tall + 2 * sp
            ch1 = bw1 / EIGHT_COUNTER_WH * _tall * _uptall + 2 * sp
            rx2, ry2 = ring_for_counter(0.0, 0.0, cw2, ch2, w_scale=w_lo, k=kk, floor=floor_)
            rx1, ry1 = ring_for_counter(0.0, 0.0, cw1, ch1, w_scale=w_up, k=kk, floor=floor_, rot=rot_up)
            cx = rx2; y2 = -OVER + ry2; y1 = -OVER + 2 * ry2 - bowl_hair() * waist + ry1
    lo, *_ = ring(cx, y2, rx2, ry2, w_scale=w_lo, k=kk or pen.BOWL_K, floor=floor_, con=con8, counter_smooth=csm, stress=_st, oval=_ov, nib=_nib)
    up, *_ = ring(cx + lean, y1, rx1, ry1, w_scale=w_up, k=kk or pen.BOWL_K, floor=floor_, rot=rot_up, con=con8, counter_smooth=csm, stress=_st, oval=_ov, nib=_nib)
    return geom.ink([up, lo])

def _fig8_path(cx, yX, a1, b1, a2, b2, psi=None):
    """One written figure-8 through the waist centre (cx, yX): the lemniscate
    of Gerono, x = cx + 2a sin t cos t, y = yX + 2b sin t, with the upper lobe's
    (a1, b1) for sin t > 0 and the lower's (a2, b2) below. Each lobe is a
    teardrop: round at its far end, widest 0.7 of the way out, and pointed at
    the waist, where the two arms cross at atan(b/a) -- the two lobes' walls
    cross with NO straight run, which is what the references' waists are.
    (The first cut made each lobe an ellipse tangent to two straight crossing
    lines through the waist; a line steep enough to cross has to be tangent
    at the lobe's SIDE, so the loops sat 330 units above the waist on 195-unit
    straights and the figure read as an hourglass with triangular counters.)
    2a is the lobe's centerline width and 2b its centerline height, so a and b
    are the ring construction's own centerline radii. `psi` is unused and kept
    for the option row. The path is closed and crosses itself once."""
    n = 160; pts = []
    for i in range(n + 1):
        t = 2 * math.pi * i / n; s, c = math.sin(t), math.cos(t)
        a, b = (a1, b1) if s >= 0 else (a2, b2)
        pts.append((cx + 2 * a * s * c, yX + 2 * b * s))
    path = resample(pts)
    # the closed path is stroked in overlapping PIECES (it crosses itself), and
    # the last piece does not overlap the first: run 10 samples past the start
    # so the seam is covered, or a white slit opens where the path closes
    return path + path[1:11]

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
NINE_END_CUT = float(os.environ.get("ALBO_9_END_CUT", -34.0))  # round 195: the tail's end face, degrees; 0 = square (the roman)
NINE_JOIN_SINK = float(os.environ.get('ALBO_ALD_NINE_JOIN_SINK', 8.0))
# ROUND 211 -- ITALIC ONLY, and it is the contrast that makes it necessary. The
# tail leaves the ring from a point sunk into it; with the figures' new cut the
# ring's wall is THIN where that happens, so the tail's inner edge crossed the
# counter and bit a notch out of it (plain at 360 px). Sinking DEEPER makes it
# worse, which is the diagnostic: the join wants to start further OUT, on the
# ring's own edge, where the tail runs along the wall instead of through it.
# The roman's 9 keeps 8.0 and is untouched.
NINE_JOIN_SINK_IT = float(os.environ.get('ALBO_ALD_NINE_JOIN_SINK_IT', 30.0))

NINE_FLAG_REACH = 12.4    # the wedge apex past the bowl's left ink: round 71's, the tail-tip rule as this pen draws it
NINE_TAIL_TOP = 0.60      # the tail's width at the wedge end, x round 71's, thinned from the top edge (1.0 = round 71); ruled
NINE_TAIL_EASE = 0.70   # ruled 2026-09-13, round 74: "eased over ~70% wins"     # fraction of the run (ring exit -> wedge) over which the width eases from 1.0 to NINE_TAIL_TOP
NINE_TAIL_MIN = 0.55      # the 6's ruled floor, x stem: holds while NINE_TAIL_TOP >= 0.5, released under it
NINE_BOTTOM = -7.3        # the round-42 tail's lowest spread ink, drawing coords (built -216.4 on the owner's pen); kept
NINE_FLOOR = 0.9          # the record's weight floor on the tail, x stem
NINE_TAPER = [(0.0, 0.15), (0.06, 1.0)]   # the tail's taper into the ring
# ROUND 212 -- ITALIC ONLY. With the join moved out to the ring's edge (so the
# tail stops biting the counter) its first samples sit OUTSIDE the ring, and at
# the round's width they showed as a step on the 9's right flank. A longer,
# thinner entry hides them inside the ring's own ink.
NINE_TAPER_IT = [(0.0, float(os.environ.get("ALBO_ALD_NINE_ENTRY_W", 0.08))),
                 (float(os.environ.get("ALBO_ALD_NINE_ENTRY_T", 0.28)), 1.0)]
# ...and WHERE on the ring it leaves. The step on the right flank is the tail's
# own start standing proud of the ring's outer contour: at -20 degrees the exit
# is on the flank, where the ring's edge is nearly vertical and any part of the
# stroke outside it shows. Lower down the ring the edge turns under and the same
# stroke is covered.
NINE_EXIT_DEG = float(os.environ.get("ALBO_ALD_NINE_EXIT_DEG", -20.0))

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

# ============================== THE 9'S OPTIONS ==========================
# The 9's fault is not its ink but its FLANK. `NINE_FLAG_REACH` puts the tail's
# tip 12.4 units past the bowl's leftmost ink, and round 216 measured what that
# costs in a run: before the body-edge fit the 9's own left white was 0.114 em
# and its left flank 0.222 -- every overhang paid for twice. The fit absorbs
# 0.75 of it in the italic and 0.45 in the roman, and what is left still makes
# the 9 the widest figure in the italic by advance (1.044 of the 0's, where
# Georgia is 0.922, Coelacanth 0.940, Poetica 0.959 and Pagella 0.957) and the
# second widest in the roman (0.992).
#   (b) SHORTER REACH -- the tip stops 3 units past the bowl instead of 12.4,
#       and its nominal x comes in with it. The wedge flag, the bottom line,
#       the thinning off the top edge and the ring are all round 71-74's and
#       are untouched; only how far the tail flies moves. (It must stay at or
#       past the bowl's left edge: `_fit_left_bottom` slides the tip until the
#       GLYPH's leftmost spread ink lands on the target, and if the ring were
#       the leftmost thing the fit would have nothing to solve.)
#   (c) BIGGER BOWL -- the ring at 0.325 of the figure's height instead of
#       0.29, so the 9 carries its weight in the loop the way Georgia's and
#       Big Caslon's do (both draw the 9 as their 6 turned over, and both have
#       a ring far larger relative to the tail than Albo's).
#   (d) both.
NINE_OPT = {
    'b': dict(reach=3.0, tip_x=1.00),
    'c': dict(r=0.325),
    'd': dict(reach=3.0, tip_x=1.00, r=0.325),
    # ROUND 233 (R43): two more readings of the same loop, roman only. 'a' is
    # the fixed departure and inside join (NINE_TANGENT_EXIT, NINE_JOIN_FILLET).
    'e': dict(k=2.0),                           # a ROUNDER loop: a true ellipse instead of the 2.1 superellipse, whose right flank measures 11 units of sag over the middle 40% of its height
    'f': dict(exit=-32.0),                      # the tail leaves LOWER on the loop (-32 degrees against -20), so the loop's bottom-right opens into the tail
    # ROUND 250, owner 2026-09-18: *"e wins but give me blunt and serif and
    # microserif and other options on tail."* Every one of these is e (the
    # round loop) with a different END on the same tail; the tip is re-fitted
    # to the same reach and bottom line each time.
    'g': dict(k=2.0, end='none'),                        # BLUNT, square: the face across the tail as it is, no wedge
    'h': dict(k=2.0, end='none', end_cut=-34.0),         # BLUNT, sheared: the face pulled back at the lower corner (the italic's -34 degrees), no wedge
    'i': dict(k=2.0, flag=1.0),                          # SERIF: the family's full diagonal wedge (1.0 x 1.0; e's is 0.9 x 0.9)
    'j': dict(k=2.0, flag=0.5),                          # MICROSERIF: the wedge at half size
    'k': dict(k=2.0, end='ball', ball=0.22),             # BALL: the tail thins to 0.72 over its last fifth and a round of 0.22 S caps it
    'l': dict(k=2.0, end='taper', taper=0.35),           # RUN-OUT: the tail thins to 0.35 over its last 28%, no wedge (the italic's ending)
    # ROUND 253, owner 2026-09-18: *"i already picked j i need more microserif
    # options."* j ships; these are the small wedge other ways. `flag` may be
    # (length, depth) x the family's WL, WD; `drop` overrides DROP.
    'm': dict(k=2.0, flag=0.35),                          # smaller still
    'n': dict(k=2.0, flag=0.65),                          # between j and e
    'o': dict(k=2.0, flag=(0.70, 0.35)),                  # long and shallow: j's depth, 0.7 of the length
    'p': dict(k=2.0, flag=(0.35, 0.70)),                  # short and deep
    'q': dict(k=2.0, flag=0.5, end_cut=-34.0),            # j on the sheared face (the lower corner pulled back under it)
    'r': dict(k=2.0, flag=0.5, drop=0.0),                 # j with no drop: the wedge's bracket meets the edge without the family's DROP
    # ROUND 254, owner 2026-09-19: *"p wins but shorten the tail until it fits
    # the rest of the 9."* p's wedge with the tail's reach 0: the fit slides
    # the tip right until the glyph's leftmost ink is the bowl's own (the tip
    # used to fly 12.4 units past it). t tucks it 12 units inside for the
    # comparison.
    's': dict(k=2.0, flag=(0.35, 0.70), reach=0.0, tip_x=1.00),
    't': dict(k=2.0, flag=(0.35, 0.70), reach=-12.0, tip_x=0.94),
    # ROUND 257, owner 2026-09-19: *"p wins but only got optically just past
    # bowl and switch tail to join the same way that 6's tail does."* join
    # 'six' draws the departure exactly as `_six_draw` does, mirrored: the
    # tail leaves the ring's CENTERLINE at its rightmost point (angle 0, no
    # sink, no wall-width match), its first handle straight DOWN at 1.5 r as
    # the 6's is straight up at 1.5 ry, and its width starts at 0.15 of the
    # pen and reaches full by 6% of the run -- NINE_TAPER, which is the 6's
    # own profile. No crotch fillet: the 6 has none. reach 5 puts the wedge's
    # apex 5 units past the bowl's left ink, optically just past it.
    'u': dict(k=2.0, flag=(0.35, 0.70), reach=5.0, tip_x=1.00, join='six'),
    'v': dict(k=2.0, flag=(0.35, 0.70), reach=10.0, tip_x=1.02, join='six'),
    'w': dict(k=2.0, flag=(0.35, 0.70), reach=5.0, tip_x=1.00),
}
NINE_OPT_IT = {k: NINE_OPT[k] for k in ('b', 'c', 'd')}
# ROUND 233 (R43), owner 2026-09-18 on the roman 9: *"redo bottom and middle
# right side of loop. treat the inside join, too."* Measured on the built
# outline: the tail's cubic left the ring with its first handle pointing
# -94.9 degrees (4.9 degrees left of straight down) from a point on the ring's
# flank where the ring's own tangent runs -107.6 degrees -- 12.7 degrees
# apart -- so the outer silhouette turned 17.3 degrees at (377, 360), a
# re-entrant kink where the flank hands over to the tail: the loop read as a
# closed oval with a tail glued onto its side. And on the inside the tail's
# upper edge met the ring's bottom edge in a bare 70-degree crotch. Now the
# first handle lies ALONG the ring's centerline tangent at the exit (its
# length unchanged, 1.51 r), so the flank runs into the tail in one curve,
# and the crotch takes the family's concave bracket, NINE_JOIN_FILLET x S along
# each edge. What did NOT move: the ring, the exit point and its 8-unit sink,
# the tail's width rule and the round 72-74 thinning, the wedge flag, the tip's
# reach and the bottom line (the fit re-lands them).
NINE_TANGENT_EXIT = True
NINE_JOIN_FILLET = 0.45
NINE_HANDLE = 1.51         # the first handle's length, x r (1.51 r is the old handle's length; laddered in the round's report)
# THE TWO DIALS OF THE START, laddered together (`m9d.py` in the round's
# scratch; intrusion = ring-counter white lost to the tail, in units^2; turn =
# the largest single-vertex turn on the outer flank at the exit; the ship's
# 9 reads 0 and 17.3):
#   start 1.00 x wall, shed over 0.15: turn 5.8, intrusion 97 (a 2-unit jog
#       on the counter's edge where the face's inner corner lands 1.4 off the
#       resampled counter, then a 2-unit band for 50 units)
#   0.97 / 0.20: turn 7.6, intrusion 62   <- shipped: the counter reads clean
#       at 5 px/unit and the flank's bend is a third of the ship's
#   0.94 / 0.10: turn 11.1, intrusion 11
#   0.90 / any:  turn 12+, intrusion 0
# There is no arm with both at zero: the wall THINS below the flank (81.5 at
# the exit, ~47 at the bottom) so the counter's edge swings outward faster
# than a 75.6-wide tail can shed width, and a start narrower than the wall
# must emerge from the outer contour somewhere. The handle length does not
# move either number (1.0-3.0 r all within 2 units^2), only the tail's body.
NINE_TAPER_ROM_T = 0.20    # over this fraction of the run the tail sheds the wall's width for its own (see g_nine)
NINE_START_W = 0.97        # the tail's width at its start, x the wall's

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
    _o9 = _okw('9', NINE_OPT, NINE_OPT_IT)
    D = c["figH"]; rx = W_(c, '9', 230); r = D * _o9.get('r', 0.29); cx = rx + TH_V / 2
    _k9 = _o9.get('k')
    solid, o, i = fig_ring(cx, D - r, rx, r, con=NINE_RING_CON, oval=NINE_RING_OVAL, **({'k': _k9} if _k9 else {}))
    _sink = NINE_JOIN_SINK_IT if pen.ITALIC else NINE_JOIN_SINK
    _exit = NINE_EXIT_DEG if pen.ITALIC else _o9.get('exit', -20.0)
    p0 = (cx + (rx - _sink) * math.cos(math.radians(_exit)),
          D - r + (r - _sink) * math.sin(math.radians(_exit)))
    _tap_rom = None
    if _o9.get('join') == 'six':
        # round 257: the 6's own departure, mirrored (see NINE_OPT 'u')
        p0 = (cx + rx, D - r)
        c1 = (p0[0], p0[1] - r * 1.5)
    elif pen.ITALIC or not NINE_TANGENT_EXIT:
        c1 = (p0[0] - rx * 0.15, p0[1] - r * 1.5)
    else:
        # round 233 (R43): the tail starts ON the ring's centerline (no sink),
        # its first handle along the ring's CENTERLINE tangent at the exit (the
        # centerline is the superellipse of radii rx, r -- fig_ring adds half
        # the pen to make the outer), heading down the flank, at the old
        # handle's length -- AND at the WALL'S OWN WIDTH, shed to the tail's
        # width rule over the first NINE_TAPER_ROM_T of the run. Measured why
        # the tangent alone was not enough: the tail's width rule (0.9 S, 75.6)
        # is thinner than the ring's wall at the flank (bowl_th there, ~99), so
        # a tail sunk inside the wall must EMERGE from the outer contour at an
        # angle wherever the straighter stroke leaves the curving ring -- 17.4
        # degrees, the same corner as the ship's 17.3 -- and every sink that
        # hides that pushes the inner edge into the counter instead (sink 8:
        # 121 units^2 of counter lost, 4 deep). Starting at the wall's width on
        # the centerline puts BOTH of the tail's edges on the ring's contours
        # with the ring's tangent, so neither emerges. The 8-unit sink of
        # round 75 stays on the italic and on the non-tangent path.
        # The START is the MIDDLE OF THE WALL, found from the outer contour:
        # fig_ring's outer is the superellipse (rx + TH_V/2, r + TH_H/2) and
        # its counter that outer offset inward by bowl_th along the normal, so
        # the wall's middle at the exit is the outer point pushed in by half of
        # bowl_th -- 10.7 units inside the (rx, r) superellipse at the flank,
        # where the sink of 8 was an eye-measured approximation of exactly
        # this. (On the (rx, r) line itself the face's outer corner stood 10.7
        # outside the ring: a 91-degree tab.)
        _arc = superellipse(cx, D - r, rx, r, math.radians(_exit + 4), math.radians(_exit - 4), _k9 or BOWL_K)
        _tg = tangents(_arc)[len(_arc) // 2]; _L1 = r * NINE_HANDLE
        _wall = bowl_th(_tg)
        _po = (cx + (rx + TH_V / 2) * math.cos(math.radians(_exit)), D - r + (r + TH_H / 2) * math.sin(math.radians(_exit)))
        p0 = (_po[0] + _tg[1] * _wall / 2, _po[1] - _tg[0] * _wall / 2)      # inward = the left normal of the ccw outer
        c1 = (p0[0] + _tg[0] * _L1, p0[1] + _tg[1] * _L1)
        _w0 = max(pen.th_t(_tg), S * NINE_FLOOR)
        _tap_rom = widths([(0.0, _wall * NINE_START_W / _w0), (NINE_TAPER_ROM_T, 1.0)])
    target_left = (cx - rx - TH_V / 2 - sp) - _o9.get('reach', NINE_FLAG_REACH)
    tap = _tap_rom or widths(NINE_TAPER_IT if pen.ITALIC else NINE_TAPER)
    floor = S * NINE_TAIL_MIN if NINE_TAIL_TOP >= 0.5 else 0.0
    def make(dx, dy):
        tip = (cx - rx * _o9.get('tip_x', 1.12) + dx, 22 + dy)
        tail = cubic(p0, c1, (tip[0] + rx * 1.15, tip[1] + r * 0.55), tip)
        base = pen_widths(tail)
        wf = lambda u: max(base(u), S * NINE_FLOOR) * tap(u)            # round 71's width
        pts = resample(tail); tans = tangents(pts); n = len(pts) - 1
        t_exit = next((k / n for k in range(len(pts)) if k / n > 0.05 and not solid.contains(Point(pts[k]))), 0.3)
        if NINE_TAIL_EASE > 0: k_of = widths([(t_exit, 1.0), (t_exit + NINE_TAIL_EASE * (1.0 - t_exit), NINE_TAIL_TOP)])   # full at the exit, easing to the step's factor
        else: k_of = widths([(t_exit - 0.04, 1.0), (t_exit + 0.10, NINE_TAIL_TOP)])   # the uniform thinning: 1.0 inside the ring, the factor under the bowl
        _end = widths([(0.0, 1.0), (0.72, 1.0), (1.0, NINE_TAIL_END)]) if (pen.ITALIC and NINE_TAIL_END) else None
        _o_end = _o9.get('end')                                                   # round 250: the roman tail's endings
        if _o_end == 'taper': _end = widths([(0.0, 1.0), (0.72, 1.0), (1.0, _o9['taper'])])
        elif _o_end == 'ball': _end = widths([(0.0, 1.0), (0.80, 1.0), (1.0, 0.72)])
        def wf2(u):
            w = wf(u); v = max(w * k_of(u), min(floor, w))
            return v * _end(u) if _end else v
        center = []
        for k, (p, tn) in enumerate(zip(pts, tans)):                    # the thinning off the TOP edge: drop the centerline by half of it
            u = k / n; d = (wf(u) - wf2(u)) / 2
            ux, uy = -tn[1], tn[0]
            if uy < 0: ux, uy = -ux, -uy                                 # the upward normal
            center.append((p[0] - ux * d, p[1] - uy * d))
        # ROUND 195 -- THE TAIL'S END FACE IS SHEARED, so its LOWER corner does
        # not stand out as a second prong. Owner 2026-09-17: *"remove bottom
        # side of serif in 9."*
        #
        # The tail ended on a face SQUARE across its own travel, which has two
        # corners. The family's diagonal wedge is added at the UPPER one (the
        # A's, the V's) and the lower one was left standing -- so the terminal
        # read as two points with a notch between them, where Coelacanth's 9
        # simply tapers out. Shearing the face pulls the lower corner back along
        # the tail and leaves the upper one, and therefore the flag, where they
        # are. Italic only; the roman's 9 is untouched at NINE_END_CUT 0.
        _ec = math.radians(NINE_END_CUT if pen.ITALIC else _o9.get('end_cut', 0.0))
        t, A, B = stroke(center, wf2, raw=True, sides=True, cut1=_ec)
        up, lo = (A, B) if A[-1][1] >= B[-1][1] else (B, A)
        d = tangents(resample(tail))[-1]
        v = (up[-1][0] - lo[-1][0], up[-1][1] - lo[-1][1]); n = math.hypot(*v) or 1.0; sd = (v[0] / n, v[1] / n)
        if pen.ITALIC and NINE_TAIL_END:
            return geom.ink([solid, t])       # no flag: the tail runs out instead
        if _o_end in ('none', 'taper'):
            parts = [solid, t]
        elif _o_end == 'ball':
            _ex, _ey = (up[-1][0] + lo[-1][0]) / 2, (up[-1][1] + lo[-1][1]) / 2
            parts = [solid, t, Point(_ex, _ey).buffer(S * _o9['ball'], 24)]
        else:
            _fs = _o9.get('flag', 0.9)
            _fl, _fd = (_fs if isinstance(_fs, tuple) else (_fs, _fs))
            flag = wedge(up[-1], d, sd, WL * _fl, WD * _fd, _o9.get('drop', DROP), edge_at=_walk_back(up))
            parts = [solid, t, flag]
        if not pen.ITALIC and NINE_JOIN_FILLET > 0 and _o9.get('join') != 'six':
            fil = _crotch_fillet(up, o, S * NINE_JOIN_FILLET)     # round 233 (R43): the inside join
            if fil is not None: parts.append(fil)
        return geom.ink(parts)
    return _fit_left_bottom(make, target_left, NINE_BOTTOM, sp)

def _crotch_fillet(side, ring, f):
    """The family's concave bracket laid into the pocket where a tail's INNER
    edge (`side`, walked from the tail's start) leaves a ring's outer contour:
    K is where the edge crosses the contour, A is `f` back along the contour
    on the side that heads left (toward the ring's bottom), B is `f` on down
    the tail; the quad from A to B with K as its control is the bracket, and
    the region between it and K is the ink added. None if they do not cross."""
    from shapely.geometry import LineString, Point
    ls = LineString(side); ro = LineString(list(ring) + [ring[0]])
    x = ls.intersection(ro)
    pts = [x] if x.geom_type == 'Point' else [p for p in getattr(x, 'geoms', []) if p.geom_type == 'Point']
    if not pts: return None
    Kp = min(pts, key=lambda p: p.y); K = (Kp.x, Kp.y)
    dK = ls.project(Kp); Bp = ls.interpolate(min(ls.length, dK + f)); Bt = (Bp.x, Bp.y)
    dR = ro.project(Kp)
    A1 = ro.interpolate((dR + f) % ro.length); A2 = ro.interpolate((dR - f) % ro.length)
    Ap = A1 if A1.x < A2.x else A2; At = (Ap.x, Ap.y)
    # grown 0.6 so its two straight sides -- which lie ON the tail's edge and
    # the ring's contour -- sit inside the ink; flush they left a 0.1-unit
    # numerical sliver as a hole along the tail's edge (area 4.2 on the 9)
    return geom.poly(geom.quad(At, K, Bt) + [K]).buffer(0.6, join_style=2)
