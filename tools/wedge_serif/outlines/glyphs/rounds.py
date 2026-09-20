"""o c e: the rounds. The o is the designed superellipse (the family's k)
with its counter the pen's inward offset -- the o's stress -- sized so the
counter is 1.036 wide over tall (ruling). The c and the e's eye are the
o's ring opened; their terminals are the family's: a flared face at the
top, a thinner pen-cut end below (c), a blunt end (e, ruling)."""
import math, os
from . import glyph
from .. import geom, pen
from ..geom import superellipse, line, join, cubic
from ..primitives import ring, stroke, pen_widths, widths, bar, beak, bowl_widths, widen_terminal, end_wedge, finial_widths, finial_cut
from .. import primitives as PR
from ..pen import S, XH, OVER, TH_V, TH_H, HAIR, CUT, BOWL_K, adj

# ROUND 225 -- THE ROMAN o, A LITTLE SMALLER AND A LITTLE HEAVIER. Owner
# 2026-09-18: *"'o' roman seems slightly too big and thin, but not by much."*
# Two dials so the two halves of that can be judged apart: O_RX_ADJ scales the
# o's centreline radius (227 is the record's), O_W_ADJ its ring's pen width.
# Applied INSIDE g_o only: O_RX itself is also the roman a's bowl (stems.py)
# and the classic italic's, which are not the ask. Roman only -- the aldine
# italic's o is its own. 1.0 / 1.0 is round 225 exactly.
O_RX_ADJ = float(os.environ.get("ALBO_ROM_O_RX", 0.93))
O_W_ADJ = float(os.environ.get("ALBO_ROM_O_W", 1.10))
O_RX = 227; C_RX = 210; E_RX = 186   # centerline radii of the record (x wf); the outer adds half the pen's vertical
# ROUND 111. _IO is the ONE place IT_OVAL may be read from, and both the o's
# constructions now go through it. Round 101 wrote `pen.IT_OVAL` straight into
# `o_ring` and into the adjusted o with NO `pen.ITALIC` gate, so the ROMAN o
# was narrowed by 0.729 too -- silently, for ten rounds, because every round
# after it was judged on italic pages. Owner 2026-09-15: "the o looks squished
# when it shouldn't have been." It was: the shipping Regular's o measured 374
# wide over 459 tall against the 490 x 459 it was drawn at, its counter 0.621
# wide over tall against 0.918, and its advance 447 against 562.
_IO = pen.IT_OVAL if pen.ITALIC else 1.0   # round 108: in the italic the c and the e narrow with the o (they were 25% wider than it)

def o_ring(c, rx_center, ry_center=None, cy=None, k=BOWL_K, w_scale=1.0):
    """A full round on the o's construction: outer superellipse whose x
    radius is the centerline's plus half the vertical pen, y radius the
    x-height half plus the overshoot at the INK's edge (ruling: 14)."""
    xh = c["xh"]; wf = c["wf"] * _IO   # round 101: the italic narrows the o (measured on five real italics). GATED -- see below.
    rx = rx_center * wf + TH_V / 2 * w_scale; ry = (xh / 2 + OVER) if ry_center is None else ry_center
    cy = xh / 2 if cy is None else cy
    return ring(rx, cy, rx, ry, k=k, w_scale=w_scale)

# ROUND 264 -- THE REAL CONTRAST CLAMP IS THIS LINE, and it is a RULING, not
# an oversight. Owner 2026-09-19 asked for Albo's contrast redrawn toward the
# references. Two ladders located the clamp: FJORD_CONTRAST 0.80 to 0.98 moves
# the built thick:thin only 1.32 to 1.50 (the `1 - 0.5c` mapping bottoms out
# at 0.50 of the stem), and with that mapping bypassed the ratio saturates at
# 1.61 -- because the o's hairline may not go under O_FLOOR_ADJ x the stem.
# That floor is the owner's own round-92 ruling, quoted below: the hairs were
# dropping to gray at 13 pt on the four-level pipeline, which is the size he
# reads at. Lowering it is therefore a LEGIBILITY trade and his to rule, not a
# number to tune. ALBO_O_FLOOR is the ladder's dial; unset, the ruling stands
# and every build is byte-identical.
O_FLOOR_ADJ = float(__import__('os').environ.get('ALBO_O_FLOOR', 0.50))   # round 265: 0.55 -> 0.50, the owner's "around 1.7 wins"; round 92 (adj 'o'): the o read hollow -- its knot the lowest of any letter (-11%), the hairs dropping to gray at 13 pt; floored like the 6's tail
@glyph('o')
def g_o(c):
    if adj('o'):
        xh = c["xh"]; wf = c["wf"] * _IO; rx = O_RX * O_RX_ADJ * wf + TH_V / 2 * O_W_ADJ   # round 225: the o's own size and weight dials
        solid, outer, inner = ring(rx, xh / 2, rx, xh / 2 + OVER, w_scale=O_W_ADJ, floor=S * O_FLOOR_ADJ); return solid
    solid, outer, inner = o_ring(c, O_RX * O_RX_ADJ, w_scale=O_W_ADJ)
    return solid

def open_arc(c, rx_center, a0_deg, a1_deg, profile, cut0=None, cut1=None, k=BOWL_K, cx=None, cy=None, ry_center=None, smooth=False):
    """An open round stroke on the o's centerline (rx_center x wf, the
    centerline overshoot), the pen's widths times a declared profile.

    `smooth` (the roman c, 2026-09-18): the tangent the width is read from
    is interpolated at the fractional index instead of rounded -- the arch's
    sawtooth fix, arches.smooth_widths (R23); `bowl_widths` rounds, and the
    width steps by one and two indices wherever it is changing. Off by
    default: symbols2 draws on this too and is not in the round."""
    xh = c["xh"]; wf = c["wf"]; rx = rx_center * wf
    ry = (xh / 2 + OVER - TH_H / 2) if ry_center is None else ry_center
    cx = rx + TH_V / 2 if cx is None else cx; cy = xh / 2 if cy is None else cy
    center = superellipse(cx, cy, rx, ry, math.radians(a0_deg), math.radians(a1_deg), k)
    if smooth:
        from .arches import smooth_widths
        wfn = smooth_widths(center, PR.bowl_th, profile)
    else:
        wfn = bowl_widths(center, profile)
    return stroke(center, wfn, cut0=cut0, cut1=cut1), center

@glyph('c')
def g_c(c):
    """The o's ring from 42 to 318 degrees. Upper terminal: a swell into a
    near-vertical face (the family's beak face, no lip on the lowercase);
    lower terminal: thins to 0.7 of the pen and takes the pen cut."""
    if PR.BOWL and PR.BOWL.get('widen'):   # variant C: both free ends widen into the family's cut, no beak
        prof = widen_terminal(widen_terminal(None, True), False)
        solid, center = open_arc(c, C_RX * _IO, 40, 318, prof, cut0=CUT, cut1=CUT); return solid
    top = 1.10 if adj('c') else 1.30   # round 92 (adj 'c'): both terminals heavy (band +15% Albertus) -- the top's swell 1.30 -> 1.10
    # ROUND 275: the top's swell and face are the family's finial primitives
    # now (PR.finial_widths / PR.finial_cut, the c's own numbers moved there
    # so the round finials elsewhere could take them); this composes to the
    # same widths as widths([(0.0, 1.10), (0.13, 1.0), ...]) did, and the cut
    # resolves to the -28 degrees the c always carried. Byte-identical.
    prof = finial_widths(1.0, True, widths([(0.0, 1.0), (0.82, 1.0), (1.0, 0.70)]), swell=top)
    c_cut = finial_cut(_c_center(c), True)
    if pen.ITALIC:
        solid, center = open_arc(c, C_RX * _IO, 40, 318, prof, cut0=c_cut, cut1=CUT)
        lip = beak(center, PR.bowl_th(geom.tangents(center)[0]) * top, True, -28.0, lip=(0.35, 0.6))
        return geom.ink([solid, lip])
    # R18, owner 2026-09-18, on the upper terminal: "despur." The spur was
    # the beak's LIP -- the 0.35 x 0.6 bracket wedge `beak()` hangs from the
    # face's inner corner into the aperture. Measured on the built c: the
    # stroke's inner edge ran vertical for its last 12 units (the lip's
    # inner strip) into a point 19 units below and left of the corner (the
    # lip's tip), and the lip's seat missed the face's sheared corner by a
    # unit or two, which was the jog on the cut face. The lip goes; the
    # swelled stroke keeps its -28-degree face, which is the family's beak
    # face without the beak, and the terminal ends on that face and nothing
    # else. (The capital C in caps_straight carries the same `beak()` lip at
    # 0.4 x 0.7; it is not in this round.)
    # ROUND 273 -- THE c's TOP FINIAL AS OPTIONS. Owner 2026-09-19: *"change
    # out round finials (like c top serif)."* The top as drawn is a swell to
    # 1.10 of the pen into a -28-degree face, which reads as a ball. Five
    # ends, one dial, 'a' today's drawing byte for byte:
    #   a  the swell into the -28 face (as drawn)
    #   b  the pen cut and no swell -- the bottom terminal's end, at the top
    #   c  the flared cut: the stroke widens 15% over its last 12% into the
    #      family's cut (variant C's `widen_terminal` rule, on this letter)
    #   d  the wedge: no swell, the pen cut, and the family's diagonal end
    #      wedge on the outer side (the v's and the y's)
    #   e  the beak with its lip: the capital C's terminal (the swell, the
    #      face, the 0.35 x 0.6 bracket wedge hanging into the aperture)
    if C_TOP == 'a':
        solid, center = open_arc(c, C_RX * _IO, 40, 318, prof, cut0=c_cut, cut1=CUT, smooth=True)
        return geom.ink([solid])
    if C_TOP == 'e':
        solid, center = open_arc(c, C_RX * _IO, 40, 318, prof, cut0=c_cut, cut1=CUT, smooth=True)
        lip = beak(center, PR.bowl_th(geom.tangents(center)[0]) * top, True, -28.0, lip=(0.35, 0.6))
        return geom.ink([solid, lip])
    if C_TOP == 'c':
        prof2 = widths([(0.0, 1.15), (0.12, 1.0), (0.82, 1.0), (1.0, 0.70)])
    else:
        prof2 = widths([(0.0, 1.0), (0.82, 1.0), (1.0, 0.70)])
    solid, center = open_arc(c, C_RX * _IO, 40, 318, prof2, cut0=CUT, cut1=CUT, smooth=True)
    if C_TOP == 'd':
        w0 = PR.bowl_th(geom.tangents(center)[0]) * prof2(0.0)
        return geom.ink([solid, end_wedge(center, w0, True, -1, 0.9)])
    return geom.ink([solid])
C_TOP = os.environ.get("ALBO_ROM_C_TOP", "a")   # round 273, see g_c

def _c_center(c):
    """The c's centerline exactly as open_arc builds it for g_c (the roman
    ring from 40 to 318 degrees) -- read for its start tangent only."""
    xh = c["xh"]; wf = c["wf"]; rx = C_RX * _IO * wf
    ry = xh / 2 + OVER - TH_H / 2; cx = rx + TH_V / 2; cy = xh / 2
    return superellipse(cx, cy, rx, ry, math.radians(40), math.radians(318), BOWL_K)
def c_top_width():
    """ROUND 275: the c's top end width -- FINIAL_SWELL x the bowl pen at the
    c's start tangent, from the c's own drawing (60.8 at the 400's stem of
    66.9, 103.4 at the 700's 116; measured on the built c before this existed
    and equal to it). The floor a finial on a thin stroke is held to: the
    y's tail runs out on the pen's thin, and 1.10 of that is 15% under this."""
    return PR.FINIAL_SWELL * PR.bowl_th(geom.tangents(_c_center(dict(xh=pen.XH, wf=pen.WF)))[0])

E_DEG, E_BAR, E_TH, E_END = 5.0, 0.62, 0.72, 330   # the e's dials (rulings, rounds 39 + 46)
# Round 109 (owner: "redo e for a steeper crossbar and less of a tail
# stroke"). ITALIC ONLY -- the roman's 5 degrees and 330 are rulings of rounds
# 39 and 46 and are untouched. Both models' italic e tilts its bar hard and
# stops its arm early; Albo's italic inherited the roman's near-flat bar and
# long lower-right tail. E_DEG_IT is the bar's rise in degrees, E_END_IT the
# radial where the arm's end face is cut (smaller = shorter tail).
E_DEG_IT = float(os.environ.get("ALBO_E_DEG", 16.0))   # rung C of the round-109 ladder
# Round 109c. E_END_IT is now where the ring STOPS and the tail stroke below
# takes over. It is at the BOWL'S BOTTOM, and that position is not a taste
# call: the aperture cuts the ring along a ray from the centre, while the tail
# is built perpendicular to its own travel, so the two faces coincide EXACTLY
# only where the ray and the stroke's normal are parallel -- which is at the
# bottom, where the stroke runs flat. Cut anywhere up the right shoulder and
# the two disagree by the angle between them, which showed as a tooth of ring
# standing proud of the tail. So the tail draws the whole lower-right sweep,
# which is also how Coelacanth's e is built.
E_END_IT = float(os.environ.get("ALBO_E_END", 276.0))
E_TAIL_IT = float(os.environ.get("ALBO_E_TAIL", 0.40))   # the tail stroke's width where it ends, x its width where it leaves the bowl
E_TIP_X = float(os.environ.get("ALBO_E_TIPX", 0.72))     # the tail's tip, x: this many bowl radii right of the bowl's centre
E_TIP_Y = float(os.environ.get("ALBO_E_TIPY", 0.16))     # and this fraction of the x-height above the baseline
E_TIP_DEG = float(os.environ.get("ALBO_E_TIPDEG", 52.0)) # the direction the tail is travelling when it ends (before the italic shear)
# ROUND 110. The same tail, for the UPRIGHT cuts. Owner: "there was an
# improved e that should have made it in this cut." Round 109c rebuilt the
# italic's tail as its own tapering stroke and deliberately left the roman
# byte-identical, because the roman's 330-degree arm end is a ruling of rounds
# 39 and 46. Measured on the specimen's five cuts, the roman carries exactly
# the defect the italic was cured of: its arm's outer edge arrives at the
# terminal at 61.9 degrees in the Regular, 57.5 in the SemiBold and 55.2 in the
# Bold, with an end face of 0.154, 0.200 and 0.232 of the x-height -- against
# the fixed italic's 45.0 degrees and 0.038. A ring turns at a constant rate,
# so the arm steepens all the way and the blunt cut across it reads as a tick;
# the Bold is the worst of the five because its pen is the widest.
E_END_R = float(os.environ.get("ALBO_E_END_R", 276.0))     # the ring stops at the bowl's bottom, as in the italic and for the same reason
E_TAIL_R = float(os.environ.get("ALBO_E_TAIL_R", 0.40))    # the tail's width where it ends, x its width where it leaves the bowl
E_TIPX_R = float(os.environ.get("ALBO_E_TIPX_R", 0.92))    # the tip, this many bowl radii right of the bowl's centre
E_TIPY_R = float(os.environ.get("ALBO_E_TIPY_R", 0.19))    # and this fraction of the x-height above the baseline
# ROUND 290 -- THE TERMINAL RIDES UP WITH THE WEIGHT. Owner 2026-09-19, on a
# sheet of four cuts of the Black: *"d2 wins"* -- the terminal at 0.28 of the
# x-height with the floor's outgoing handle eased 1.6x.
#
# WHY IT HAD TO MOVE AT ALL, measured on the built letters. The floor of the
# bottom stroke leaves the bowl on the counter's own tangent and must arrive
# at the terminal on E_TIPDEG_R's 50 degrees (round 110). Between those two
# fixed ends the room to rise collapses as the stroke thickens, because the
# bowl's counter climbs -- 8.6, 19.3, 41.6, 56.0 at the 200, 400, 700 and 900
# -- while the terminal sat at 0.19 xh for all of them. The chord from the
# handover to the tip therefore flattens from 28.5 degrees to 13.2, and
# against a departure tangent of about 13 that headroom reads +14.7, +13.0,
# +5.0 and -0.8: at the Black the floor has to leave the bowl RISING and
# still arrive BELOW where its own tangent would carry it, so it must dip and
# recover. No choice of handles removes that -- round 287's clamp made the
# dip monotone, which is not the same as simple, and the owner said so.
#
# So the terminal rises with the stem, 0.19 at and below the 400 (which is
# byte-identical, and is the weight he is happy with) to E_TIPY_HEAVY at the
# 900, which restores +10 degrees of headroom there and about +8 at the 700.
E_TIPY_HEAVY = float(os.environ.get("ALBO_E_TIPY_HEAVY", 0.28))
def _e_tipy():
    if not _heavy(): return E_TIPY_R
    t = min(1.0, max(0.0, (pen.S - E_HEAVY_S) / (148.0 - E_HEAVY_S)))
    return E_TIPY_R + (E_TIPY_HEAVY - E_TIPY_R) * t
E_TIPDEG_R = float(os.environ.get("ALBO_E_TIPDEG_R", 50.0))# the direction the tail is travelling when it ends

E_BAR_ADJ, E_TH_ADJ = 0.58, 0.66   # round 92 (adj 'e'): the eye small for its bar -- bar top 0.62 -> 0.58 xh (eye taller), bar 0.72 -> 0.66 of the pen

# ROUND 287 -- THE HEAVY e's BAR. Owner 2026-09-19: *"that e could be
# heavier."* Measured against its own CONSTRUCTION family at the 900 (the
# rounds -- o c a b d g p q s -- not the case group, which flags the alphabet
# rather than the drawing): the e's colour is 0.418 against the family's
# median 0.457, -8.5%, and on the chamfer-ridge stroke median it is 72.3
# against 103.5, -30%, the LIGHTEST of the family. So this is a correction,
# not a departure.
#
# The bar is the lever, and the other two were ruled out rather than passed
# over. The BOWL cannot take it: the e's ring is `ring()`'s pipeline at the
# e's radius, so its pen is the o's pen at the same tangent by construction,
# and widening it here would make the e the one round whose pen is its own.
# The TAIL cannot take it either: it is the "bottom right stroke" the owner
# has twice asked to make LIGHTER (round 94, then 2026-09-14, "slightly
# reduce the visual weight of the bottom right tail stroke of e"), and
# E_ARM_THIN 0.92 is that instruction -- thickening it would quietly reverse
# a standing ruling. The bar is 20% of the letter's ink and is the part that
# reads as the e's colour at text size.
#
# Note what is NOT done: the face's contrast is weight-invariant by design
# (TH_H / S is 0.566 at the 400, the 700 and the 900 alike), and changing
# that is an architectural call for the owner, not a number to tune here. So
# only the e's own bar moves, and only above E_HEAVY_S.
E_BAR_HEAVY = float(os.environ.get("ALBO_E_BAR_HEAVY", "1.22"))
E_TAIL_ARC = os.environ.get("ALBO_E_TAIL_ARC", "1") == "1"    # round 289: the tail's inner edge as one simple arc (see _arc_handles); 0 falls back to round 287's monotone clamp
E_TAIL_LO = float(os.environ.get("ALBO_E_TAIL_LO", "0.04"))   # round 289: the shortest the floor's first handle may be, x its chord
E_TAIL_H2 = float(os.environ.get("ALBO_E_TAIL_H2", "1.6"))    # round 289: the floor's second handle, x the circular arc's -- longer eases the terminal and moves the curvature's peak back toward the middle, which is the shape the 400 has
E_TAIL_G2 = float(os.environ.get("ALBO_E_TAIL_G2", "1.0"))   # round 289: the floor leaves the bowl on this fraction of the bowl counter's own curvature; 0 = tangent only, the round-287 behaviour
E_TAIL_ARC_K = float(os.environ.get("ALBO_E_TAIL_ARC_K", 1.0))   # x the circular-arc handle; 1.0 is the arc itself, lower flattens the floor toward its chord

# The lower-right stroke (the arm, from the bottom -- ARM_START_DEG, 270 --
# sweeping up to the 330-degree terminal, ARM_END_DEG = E_END): owner
# instruction, verbatim, "thin out the bottom right stroke of 'e' slightly
# and give it more interior space by moving the stroke to the right
# slightly (keep word image legible)." E_ARM_THIN multiplies the arm's
# ordinary (bowl-profile) width along that run, tapering back to 1.0 (the
# bowl's own profile) over the first ARM_TAPER of the run off the bottom --
# only at the bottom, so the thinning holds through the terminal, whose
# blunt-cut shape is unchanged. E_ARM_OUT shifts the arm's path to the
# right by up to this many units, a hump zero at the bottom and at the
# terminal and peaking at the run's middle (the widest point) -- so the
# eye above the bar and the lower aperture below both gain the interior
# space, and neither the bottom join nor the terminal's cut moves.
ARM_START_DEG, ARM_END_DEG = 270.0, (E_END_IT if pen.ITALIC else E_END_R)
ARM_TAPER = 0.25
E_ARM_THIN = float(os.environ.get("FJORD_E_ARM_THIN", 0.92))   # owner 2026-09-14: "slightly reduce the visual weight of the bottom right tail stroke of e" (1.0 = as it was; the round-77 0.90 was refused)
E_ARM_OUT = float(os.environ.get("FJORD_E_ARM_OUT", 0.0))    # and the +8 outward shift is off; _e_ring(1.0, 0) reproduces o_ring byte for byte

def _e_ring(c, rx_center, thin=1.0, out_shift=0.0, k=BOWL_K, taper_frac=ARM_TAPER, tail_end=1.0):
    """`o_ring`'s construction (the outer superellipse, the counter the
    pen/bowl's inward offset by tangent), with the arm (ARM_START_DEG to
    ARM_END_DEG) thinned to `thin` x its ordinary width and its path
    shifted right by up to `out_shift` units -- both eased to nothing at
    the bottom (where the arm leaves the bowl) and held through the
    terminal. Mirrors `primitives.ring`'s pipeline exactly (tangents off
    the UNSHIFTED outer, then unfold/smooth/resample the counter) so a
    thin=1.0, out_shift=0.0 call reproduces `o_ring` byte for byte."""
    xh = c["xh"]; wf = c["wf"]
    rx = rx_center * wf + TH_V / 2; ry = xh / 2 + OVER; cy = xh / 2; cx = rx
    outer = superellipse(cx, cy, rx, ry, 0, 2 * math.pi, k)[:-1]
    tans = geom.tangents(outer, closed=True)
    span = ARM_END_DEG - ARM_START_DEG
    outer2, inner = [], []
    for p, tn in zip(outer, tans):
        ang = math.degrees(math.atan2(p[1] - cy, p[0] - cx)) % 360
        tf, shift = 1.0, 0.0
        if ARM_START_DEG <= ang <= ARM_END_DEG:
            t = (ang - ARM_START_DEG) / span
            u = min(1.0, t / taper_frac); su = 3 * u * u - 2 * u ** 3
            tf = 1.0 + (thin - 1.0) * su
            # round 109 (owner: "e is a loop with a tapered tail"): the arm
            # thins toward its end, so the stroke comes to a point rather than
            # stopping at the blunt radial face the aperture cuts.
            if tail_end != 1.0:
                v = max(0.0, (t - 0.45) / 0.55); tf *= 1.0 + (tail_end - 1.0) * (3 * v * v - 2 * v ** 3)
            shift = out_shift * math.sin(math.pi * t)
        op = (p[0] + shift, p[1]); outer2.append(op)
        w = PR.bowl_th(tn) * tf
        inner.append((op[0] - tn[1] * w, op[1] + tn[0] * w))
    inner = PR._unfold(inner, tans)
    inner = geom.smooth(inner, 2, closed=True)
    inner = geom.resample(inner + [inner[0]])[:-1]
    return geom.poly(outer2, [inner[::-1]]), outer2, inner

@glyph('e')
def g_e(c):
    """Ring on the o's construction at the e's radius; the aperture is cut
    from the bar's underside down to the arm's blunt end at 330 degrees;
    the bar rises 5 degrees, 0.72 of the pen's width at that angle, its top
    at 0.62 xh at the letter's middle (rulings). The arm (the lower-right
    stroke) is thinned and shifted right per E_ARM_THIN / E_ARM_OUT (owner
    instruction, 2026-09-13)."""
    xh = c["xh"]; wf = c["wf"]
    # R19, owner 2026-09-18, on the roman's lower stroke: "correct curve."
    # The counter floor stepped up 4 units just past the bowl's bottom, and
    # the step was NOT the handover to the tail: it was E_ARM_THIN. Round 94
    # thinned the arm over ARM_START..ARM_END, easing in over the first
    # quarter of that span -- 15 degrees of ring when the arm ran 270..330.
    # Round 110 moved E_END_R to 276 and gave the lower-right sweep to the
    # tail, which left the ring's thinning squeezed into a 6-degree sliver
    # with its ease-in over 1.5 degrees: the inner edge climbed 4 units in
    # the ten units of path after the bottom (measured: 26.6 degrees where
    # the outer edge runs at 4.8), and the tail then left that point flat.
    # So the ROMAN ring is no longer thinned -- the sliver is gone -- and the
    # tail carries the 0.92 instead, eased in along its own first third
    # (_e_tail). The italic keeps the ring thinning as it was.
    solid, outer, inner = _e_ring(c, E_RX * _IO, E_ARM_THIN if pen.ITALIC else 1.0, E_ARM_OUT)
    rx = E_RX * _IO * wf + TH_V / 2; cx = rx; cy = xh / 2
    tilt = math.radians(E_DEG_IT if pen.ITALIC else E_DEG); slope = math.tan(tilt)
    e_bar, e_th = (E_BAR_ADJ, E_TH_ADJ) if adj('e') else (E_BAR, E_TH)
    if _heavy() and not pen.ITALIC: e_th *= E_BAR_HEAVY   # round 287, see E_BAR_HEAVY
    th = max(pen.th(E_DEG_IT if pen.ITALIC else E_DEG) * e_th, S * 0.35)
    bar_top = lambda x: xh * e_bar + (x - cx) * slope
    under = lambda x: bar_top(x) - th
    # the bar: from inside the left stroke to inside the right stroke
    b = stroke([(cx - rx + 8, bar_top(cx - rx + 8) - th / 2), (cx + rx - 42, bar_top(cx + rx - 42) - th / 2)], th)
    # the aperture: between the arm's end face (radial at E_END) and the bar's underside
    a = math.radians(E_END_IT if pen.ITALIC else E_END_R); far = 3 * rx
    if pen.ITALIC:
        aperture = geom.poly([(cx, cy), (cx + far * math.cos(a), cy + far * math.sin(a)), (cx + far, under(cx + far)), (cx, under(cx))])
        parts = [solid.difference(aperture), b, _e_tail(outer, inner, cx, cy, rx, xh, a)]
        return geom.ink(parts)
    # R19, the other half: the ring's end face is cut along the NORMAL at the
    # handover, not the radial. The tail's inner edge starts at Po + n * w0
    # (edge_stroke offsets along the outer's normal), while the radial face
    # put the ring's inner corner Pi 6 degrees away -- 1.8 units along the
    # floor, with a 0.2-unit step between the two corners, which the curve
    # fitter turned into a 2-unit pimple on the counter floor. With the face
    # on the normal the two corners are one point.
    cut = _normal_cut(outer, inner, cx, cy, a, rx, xh)
    if _heavy() and E_TAIL_INNER:      # round 287: the seam, see _inner_cut
        _ic = _inner_cut(outer, inner, cx, cy, a, rx, xh,
                         math.hypot(cut[0][0] - cut[2][0], cut[0][1] - cut[2][1]))
        if _ic is not None: cut = _ic
    Po, To, Pi, n_in = cut
    C1 = (Po[0] + n_in[0] * far, Po[1] + n_in[1] * far)      # far along the normal, into the counter and out the top
    P_out = (Po[0] - n_in[0] * 20, Po[1] - n_in[1] * 20)     # just outside the ring
    aperture = geom.poly([C1, P_out, (cx + far, P_out[1]), (cx + far, under(cx + far)), (C1[0], under(C1[0]))])
    aperture = aperture.intersection(geom.poly([(cx - 1, -far), (cx + far, -far), (cx + far, under(cx + far)), (cx - 1, under(cx - 1))]))
    parts = [solid.difference(aperture), b, _e_tail(outer, inner, cx, cy, rx, xh, a, cut=cut)]
    return geom.ink(parts)


def _e_tail_edge(Po, To, cx, rx, xh):
    """The tail's OUTER edge: from Po along the ring's tangent To, decelerating
    into a near-straight run to the tip (see _e_tail)."""
    tail_end, tipx, tipy, tipdeg = ((E_TAIL_IT, E_TIP_X, E_TIP_Y, E_TIP_DEG) if pen.ITALIC
                                    else (E_TAIL_R, E_TIPX_R, E_TIPY_R, E_TIPDEG_R))
    tip = (cx + tipx * rx, tipy * xh)
    L = math.hypot(tip[0] - Po[0], tip[1] - Po[1])
    d2 = math.radians(tipdeg); D2 = (math.cos(d2), math.sin(d2))
    return cubic(Po,
                 (Po[0] + To[0] * L * 0.30, Po[1] + To[1] * L * 0.30),
                 (tip[0] - D2[0] * L * 0.55, tip[1] - D2[1] * L * 0.55),
                 tip), tail_end


# ROUND 287 -- THE 900's e. Owner 2026-09-19, on a magnified Black e:
# *"address to wobble wave and bumps of 900 e"*, and *"that e could be
# heavier."* Everything this round changes is gated above E_HEAVY_S, which
# sits between the 400's stem (66.9) and the 700's (116), so the shipped
# Regular, ExtraLight and both italics are byte-identical.
E_HEAVY_S = 84.0
def _heavy():
    return pen.S > E_HEAVY_S


def _line_hit(poly, P, D):
    """Where a closed contour first crosses the ray from P in direction D,
    and the contour's own direction there. Unlike `_ray_hit` the origin need
    not be inside the contour, so the nearest crossing is taken."""
    best = None
    for p, q in zip(poly, poly[1:] + poly[:1]):
        dx, dy = q[0] - p[0], q[1] - p[1]
        den = dx * D[1] - dy * D[0]
        if abs(den) < 1e-9: continue
        ex, ey = p[0] - P[0], p[1] - P[1]
        u = (ey * D[0] - ex * D[1]) / den
        if not (0.0 <= u <= 1.0): continue
        s = (ex + u * dx) * D[0] + (ey + u * dy) * D[1]
        if s <= 1e-9: continue
        if best is None or s < best[0]:
            m = math.hypot(dx, dy) or 1.0
            best = (s, (p[0] + u * dx, p[1] + u * dy), (dx / m, dy / m))
    return (best[1], best[2]) if best else None


def _e_tail_width(w0):
    """The roman tail's width along its run: the ring's width at the handover
    tapering to E_TAIL_R of it, with the round-94 thinning eased in over
    E_ARM_EASE_R (round 245). Extracted unchanged, so that the cut face and
    the drawn tail cannot disagree about how wide the stroke is."""
    def wfn(t):
        v = w0 * (1.0 - (1.0 - E_TAIL_R) * (3 * t * t - 2 * t ** 3))
        u = min(1.0, t / E_ARM_EASE_R); su = 3 * u * u - 2 * u ** 3
        return v * (1.0 + (E_ARM_THIN - 1.0) * su)
    return wfn


def _monotone_handle(P0, C1, P3, D2, s):
    """The longest second handle, at most `s`, for which the cubic's y never
    turns back. y'(t)/3 is a quadratic in Bernstein form with coefficients
    a = C1y - P0y, b = C2y - C1y, c = P3y - C2y; with a and c non-negative it
    is non-negative on [0, 1] exactly when b >= 0, or c > 0 and a*c >= b*b.
    Only the LENGTH is searched -- C2 stays on the ray back from the tip along
    D2 -- so the terminal's angle (E_TIPDEG_R, a ruling of round 110) is
    untouched whatever the clamp does."""
    a = C1[1] - P0[1]
    def ok(ss):
        c2y = P3[1] - D2[1] * ss
        b = c2y - C1[1]; c = P3[1] - c2y
        if a < 0 or c < 0: return False
        if b >= 0: return True
        return c > 0 and a * c >= b * b
    if ok(s): return s
    lo, hi = 0.0, s
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        if ok(mid): lo = mid
        else: hi = mid
    return lo


def _contour_kappa(pts, P, span=4):
    """The signed curvature of a polyline contour near the point P -- the
    bowl's counter where the tail leaves it. Averaged over `span` steps each
    side, because one step of a resampled contour is noise."""
    j = min(range(1, len(pts) - 1),
            key=lambda i: (pts[i][0] - P[0]) ** 2 + (pts[i][1] - P[1]) ** 2)
    ks = []
    for i in range(max(1, j - span), min(len(pts) - 1, j + span + 1)):
        (x0, y0), (x1, y1), (x2, y2) = pts[i - 1], pts[i], pts[i + 1]
        a = math.hypot(x1 - x0, y1 - y0); b = math.hypot(x2 - x1, y2 - y1)
        d = math.hypot(x2 - x0, y2 - y0)
        sp = (a + b + d) / 2.0
        ar = max(1e-12, sp * (sp - a) * (sp - b) * (sp - d)) ** 0.5
        cr = (x1 - x0) * (y2 - y1) - (y1 - y0) * (x2 - x1)
        ks.append(math.copysign(4 * ar / (a * b * d), cr))
    return sum(ks) / len(ks) if ks else 0.0


def _kappa0(P0, C1, C2):
    """A cubic's signed curvature at t = 0."""
    ax, ay = C1[0] - P0[0], C1[1] - P0[1]
    bx, by = C2[0] - C1[0], C2[1] - C1[1]
    h = math.hypot(ax, ay)
    if h < 1e-9: return 0.0
    return (2.0 / 3.0) * (ax * by - ay * bx) / (h ** 3)


def _match_kappa_handle(P0, T0, C2, target, lo_f, hi_f, chord):
    """The first handle's LENGTH that starts the cubic at `target` curvature.

    ROUND 289 -- what the owner is actually pointing at. The floor's curvature
    where it leaves the bowl REVERSES SIGN against the counter it is leaving:
    measured on the built letters, the bowl's counter carries +11.3 (x1000) at
    the handover and the tail's floor started at -3.2 at the 900 and -1.3 at
    the 700, where the 400 -- the weight he is happy with -- starts at +0.6 and
    simply continues. A tangent is shared and a curvature is not, so the eye
    sees a corner however monotone the curve is.

    Curvature at t=0 goes as 1/h^3, so it is monotone in the handle's length
    and a bisection finds it. The handle is only ever SHORTENED toward the
    target, never turned, so the counter's tangent at the handover and
    E_TIPDEG_R at the terminal both stay exact."""
    def k(h):
        return _kappa0(P0, (P0[0] + T0[0] * h, P0[1] + T0[1] * h), C2)
    lo, hi = max(1e-3, lo_f * chord), hi_f * chord
    # UNREACHABLE GOES SHORT, NOT LONG. Curvature at the start goes as 1/h^2,
    # so the shortest handle is the most curved one; returning the longest --
    # which the first cut of this function did -- flattens the floor's first
    # half into a straight and then bends it, which is the opposite of the
    # ask. The owner saw that immediately: "d is closest but still not
    # graceful curve."
    if k(lo) < target: return lo
    for _ in range(48):
        mid = 0.5 * (lo + hi)
        if k(mid) >= target: lo = mid
        else: hi = mid
    return 0.5 * (lo + hi)


def _arc_handles(P0, T0, P3, D3, k=1.0):
    """ROUND 289 -- the tail's floor as one CIRCULAR arc, so it cannot bump.

    Owner 2026-09-19, on the Black: *"the 900 e lowest stroke does not have a
    bumpfree simple curve to it."* Round 287 had stopped the floor SAGGING by
    shortening the second handle until the cubic's y no longer turned back,
    and monotone it duly was -- but monotone is not simple. Shortening one
    handle and leaving the other piles the curvature up near the tip: the
    floor left the bowl, flattened into a run that reads as a straight, and
    then bent up to the terminal. That corner is what he is pointing at.

    The two end tangents here turn only 37.6 degrees apart (12.4 at the
    handover, E_TIPDEG_R's 50 at the tip), so the curve they want is very
    nearly a circular arc -- and the cubic that best approximates one has BOTH
    handles the same length, h = (4/3) tan(turn/4) R, with R the radius the
    chord and the turn imply. Equal handles on a modest turn cannot inflect,
    so the floor is one simple arc by construction at any weight rather than
    by a clamp that has to be re-checked. Both END TANGENTS are exact, so the
    counter's tangent at the handover and E_TIPDEG_R at the terminal (a
    round-110 ruling) both survive untouched.

    The tangent-INTERSECTION construction was tried first and rejected on
    measurement: the triangle is near-degenerate here -- the tangents meet
    4.4 units in front of the tip at the 900 and 25.3 units BEHIND it at the
    700 -- so it built a usable curve at one weight, refused at the other, and
    the one it built hugged the tip's tangent and thinned the tail.

    Returns None if the turn is negligible or reverses, and the caller keeps
    round 287's clamp for that case."""
    turn = math.atan2(T0[0] * D3[1] - T0[1] * D3[0], T0[0] * D3[0] + T0[1] * D3[1])
    if abs(turn) < math.radians(2.0) or abs(turn) > math.radians(160.0): return None
    chord = math.hypot(P3[0] - P0[0], P3[1] - P0[1])
    if chord <= 0.0: return None
    R = chord / (2.0 * math.sin(abs(turn) / 2.0))
    h = (4.0 / 3.0) * math.tan(abs(turn) / 4.0) * R * k
    h = min(h, chord * 0.5)
    return ((P0[0] + T0[0] * h, P0[1] + T0[1] * h),
            (P3[0] - D3[0] * h, P3[1] - D3[1] * h))


def _e_tail_inner(Pi, Ti, w0, cx, rx, xh, k_bowl=None):
    """The roman tail's INNER edge -- the counter floor the reader sees against
    the white -- and its width function. Round 245's construction: one cubic
    from the ring's own inner point along the counter's tangent to one end
    width inside the tip.

    ROUND 287 -- THE SAGGING FLOOR. The second control point is pulled back
    from the tip along the tip's own direction by 0.55 of the chord, which
    leaves it at a nearly FIXED HEIGHT -- measured 18.9, 20.3 and 20.5 units at
    the 400, 700 and 900 -- because the tip's y is 0.19 xh at every weight and
    only the chord grows. The start point Pi, however, CLIMBS with the pen:
    19.3, 41.6, 56.0. At the 400 the two are level and the floor is one curve;
    above it the control sits up to 35 units BELOW the start and the cubic sags
    between them. Measured on the built 900: the floor rose 2.5 units, fell 5.6
    and rose again -- six turning points against the 400's one -- and at its
    lowest it dug 1.5 units under the bowl's own counter floor, which is what
    reads as the wave. The handle is SHORTENED until the floor is monotone;
    never lengthened, and never turned."""
    wfn = _e_tail_width(w0)
    d2 = math.radians(E_TIPDEG_R); D2 = (math.cos(d2), math.sin(d2)); nout = (D2[1], -D2[0])
    tip_o = (cx + E_TIPX_R * rx, _e_tipy() * xh); w1 = wfn(1.0)
    tip_i = (tip_o[0] - nout[0] * w1, tip_o[1] - nout[1] * w1)
    L = math.hypot(tip_i[0] - Pi[0], tip_i[1] - Pi[1])
    c1 = (Pi[0] + Ti[0] * L * 0.30, Pi[1] + Ti[1] * L * 0.30)
    s = L * 0.55
    if _heavy() and E_TAIL_ARC:          # round 289, see _arc_handles
        h = _arc_handles(Pi, Ti, tip_i, D2, E_TAIL_ARC_K)
        if h is not None:
            c1a, c2a = h
            if E_TAIL_H2 != 1.0:          # ease the terminal: lengthen its handle along D2
                _hl2 = math.hypot(tip_i[0] - c2a[0], tip_i[1] - c2a[1]) * E_TAIL_H2
                c2a = (tip_i[0] - D2[0] * _hl2, tip_i[1] - D2[1] * _hl2)
            if k_bowl is not None and E_TAIL_G2:
                # leave the bowl on the bowl's own curvature, E_TAIL_G2 of it
                chord = math.hypot(tip_i[0] - Pi[0], tip_i[1] - Pi[1])
                hl = _match_kappa_handle(Pi, Ti, c2a, k_bowl * E_TAIL_G2, E_TAIL_LO, 0.60, chord)
                c1a = (Pi[0] + Ti[0] * hl, Pi[1] + Ti[1] * hl)
            return cubic(Pi, c1a, c2a, tip_i), wfn
    if _heavy():
        s = _monotone_handle(Pi, c1, tip_i, D2, s)
    c2 = (tip_i[0] - D2[0] * s, tip_i[1] - D2[1] * s)
    return cubic(Pi, c1, c2, tip_i), wfn


def _inner_cut(outer, inner, cx, cy, a_cut, rx, xh, w0_seed):
    """ROUND 287 -- CUT THE RING ON THE FACE THE TAIL ACTUALLY STARTS ON.

    Round 245 gave the roman tail its INNER edge as the drawn curve, starting
    at the ring's own inner point on the ray. The RING, though, went on being
    cut by `_normal_cut`: a face through the ray's point on the OUTER contour,
    along the normal of the OUTER cubic that an inner-edge tail no longer
    draws. Two different lines, so the two pieces do not meet. Measured at the
    bottom of the bowl, the tail's outer edge starts 3.0 units to the right of
    the ring's cut face at the 400 and 9.6 at the 900, and the union leaves the
    difference as a crack -- a reversal of 174 to 177 degrees whose depth runs
    0.5 units at the 400, 8.8 at the 700 and 21.7 at the 900. It is the needle
    standing up out of the letter's underside in the owner's magnified render.

    So the face is taken from the TAIL instead: through the tail's own start
    point, along the normal of its inner edge there, out to the outer contour.
    `edge_stroke(..., side=-1)` offsets by exactly that normal, so the tail's
    outer edge at t=0 lands on the returned Po and the two pieces share an
    edge. w0 feeds the taper, the taper moves the tip, and the tip moves the
    edge's start tangent, so it is iterated; three passes settle it under a
    hundredth of a unit."""
    R = (math.cos(a_cut), math.sin(a_cut))
    Pi, Ti = _ray_hit(inner, cx, cy, R)
    if Pi is None or Ti is None: return None
    if Ti[0] < 0: Ti = (-Ti[0], -Ti[1])
    w0 = w0_seed; out = None
    for _ in range(4):
        edge_i, _wfn = _e_tail_inner(Pi, Ti, w0, cx, rx, xh, _contour_kappa(inner, Pi))
        t0 = geom.tangents(geom.resample(edge_i))[0]
        n_out = (t0[1], -t0[0])                 # edge_stroke's side=-1: right of travel
        hit = _line_hit(outer, Pi, n_out)
        if hit is None: return None
        Po, To = hit
        w_new = math.hypot(Po[0] - Pi[0], Po[1] - Pi[1])
        out = (Po, To, Pi, (-n_out[0], -n_out[1]))
        if abs(w_new - w0) < 0.01:
            w0 = w_new; break
        w0 = w_new
    return out


def _normal_cut(outer, inner, cx, cy, a_cut, rx, xh):
    """The handover on the NORMAL: Po and To off the outer contour on the ray
    at a_cut (as the radial cut found them); then the normal the tail's inner
    edge is actually offset along at its start -- edge_stroke resamples the
    tail's cubic and reads its first tangent off the resampled points, and
    that chord sits ~3 degrees off To, which put the tail's start 2.9 units
    along the floor from a corner cut on To's normal (built and measured);
    then the inner contour's point Pi on the line through Po along it."""
    R = (math.cos(a_cut), math.sin(a_cut))
    Po, To = _ray_hit(outer, cx, cy, R)
    if To[0] < 0: To = (-To[0], -To[1])
    edge, _ = _e_tail_edge(Po, To, cx, rx, xh)
    t0 = geom.tangents(geom.resample(edge))[0]
    n_in = (-t0[1], t0[0])                     # left of travel (counterclockwise up the right side): inward, as edge_stroke's side=1
    best = None
    for p, q in zip(inner, inner[1:] + inner[:1]):
        dx, dy = q[0] - p[0], q[1] - p[1]
        den = dx * n_in[1] - dy * n_in[0]
        if abs(den) < 1e-9: continue
        ex, ey = p[0] - Po[0], p[1] - Po[1]
        u = (ey * n_in[0] - ex * n_in[1]) / den
        if not (0.0 <= u <= 1.0): continue
        s = (ex + u * dx) * n_in[0] + (ey + u * dy) * n_in[1]
        if s <= 0: continue
        if best is None or s < best[0]: best = (s, (p[0] + u * dx, p[1] + u * dy))
    Pi = best[1] if best else _ray_hit(inner, cx, cy, R)[0]
    return Po, To, Pi, n_in


def _ray_hit(poly, cx, cy, R):
    """Where a closed contour crosses the ray from (cx, cy) in direction R,
    and the contour's own direction there. The centre is inside both the ring
    and its counter, so each is crossed exactly once."""
    for p, q in zip(poly, poly[1:] + poly[:1]):
        dx, dy = q[0] - p[0], q[1] - p[1]
        den = dx * R[1] - dy * R[0]
        if abs(den) < 1e-9:
            continue
        ex, ey = p[0] - cx, p[1] - cy
        u = (ey * R[0] - ex * R[1]) / den
        if not (0.0 <= u <= 1.0):
            continue
        if (ex + u * dx) * R[0] + (ey + u * dy) * R[1] <= 0.0:
            continue
        m = math.hypot(dx, dy) or 1.0
        return (p[0] + u * dx, p[1] + u * dy), (dx / m, dy / m)
    return None, None


def _e_tail(outer, inner, cx, cy, rx, xh, a_cut, cut=None):
    """THE TAIL IS ITS OWN STROKE, not the ring carried on round.

    Measured on Coelacanth's italic e: the tail's outer edge leaves the bowl's
    bottom at 1 degree and reaches 45 at the terminal, and the RATE of that
    rise FALLS the whole way -- 2.7 degrees per sample at the start, 0.8 at the
    end. The stroke unwinds OUT of the bowl. A ring cannot do that. Ours left
    the bottom already at 24 degrees and reached 58 with its turn still
    ACCELERATING, so the last of it curled back over the counter and read as a
    tick. Owner, round 109c: "e needs be a simple taper without a change in
    loop direction", then "remove the flick at the e tail end".

    So the ring is cut low (E_END_IT), where it is still running flat, and the
    tail continues from that cut: it starts along the ring's own tangent, turns
    early and then runs almost straight (the short first control arm, the long
    second, which is what makes the turn decelerate), and its width tapers from
    the bowl's to E_TAIL_IT of it.

    It is drawn from its OUTER EDGE rather than from a centerline, and that is
    load-bearing: the aperture cuts the ring with a radial face, so the ring's
    outer corner sits exactly where the tail starts, and a centerline tail
    starting at the chord's midpoint left that corner standing proud as a
    tooth. Built from the edge, the tail's silhouette IS the bowl's carried
    on."""
    R = (math.cos(a_cut), math.sin(a_cut))
    if cut is not None:        # the roman: the ring was cut on the normal (g_e), so Pi is where the tail's inner edge starts
        Po, To, Pi, _ = cut
    else:
        Po, To = _ray_hit(outer, cx, cy, R)
        Pi, Ti = _ray_hit(inner, cx, cy, R)
    if Po is None or Pi is None:
        return geom.poly([(0, 0), (0, 0), (0, 0)])
    w0 = math.hypot(Po[0] - Pi[0], Po[1] - Pi[1])   # the ring's width on the cut
    if To[0] < 0:            # travel counterclockwise, up the bowl's right
        To = (-To[0], -To[1])
    edge, tail_end = _e_tail_edge(Po, To, cx, rx, xh)
    wf = lambda t: w0 * (1.0 - (1.0 - tail_end) * (3 * t * t - 2 * t ** 3))
    if not pen.ITALIC:
        # R19 (see g_e): the round-94 thinning now belongs to the tail, eased
        # in over its first E_ARM_EASE_R so the inner edge leaves the ring's
        # inner edge with no break in slope, and holding from there -- so
        # from E_ARM_EASE_R on, the tail is byte for byte the width it was.
        wf0 = wf
        def wf(t):
            u = min(1.0, t / E_ARM_EASE_R); su = 3 * u * u - 2 * u ** 3
            return wf0(t) * (1.0 + (E_ARM_THIN - 1.0) * su)
        if E_TAIL_INNER:
            # ROUND 245 (owner: "remove the hump on top of bottom stroke,
            # respect the curve better"). The roman tail is drawn from its
            # INNER edge -- the counter floor the reader sees against the
            # white -- as one cubic from the ring's inner cut point along the
            # counter's own tangent, offset OUTWARD by the width; so the
            # floor cannot wave whatever the width does, and the taper shows
            # on the outer, convex edge where it reads as the pen lifting.
            # The tip is the same outer tip: the inner cubic aims one end
            # width inside it.
            _Pi2, Ti = _ray_hit(inner, cx, cy, R)   # the counter's own direction where the ray crosses it
            if Ti is None: Ti = To
            if Ti[0] < 0: Ti = (-Ti[0], -Ti[1])
            Pi = _Pi2 if _Pi2 is not None else Pi   # the ring's own inner point on the ray: the cut's Pi sat 2 units off it (a step at the handover)
            # ROUND 287: the edge and its width come from ONE definition now
            # (`_e_tail_inner` / `_e_tail_width`), which is also what
            # `_inner_cut` cuts the ring against -- the two cannot drift apart.
            # Below E_HEAVY_S it is round 245's cubic and wf byte for byte.
            edge_i, wfn = _e_tail_inner(Pi, Ti, w0, cx, rx, xh, _contour_kappa(inner, Pi))
            return PR.edge_stroke(edge_i, wfn, side=-1)[0]
    return PR.edge_stroke(edge, wf, side=1)[0]
E_TAIL_INNER = __import__('os').environ.get("ALBO_ROM_E_TAIL_INNER", "1") == "1"   # round 245: the roman tail drawn from its inner edge
# ROUND 245. Owner 2026-09-18: "for e and c: remove the hump on top of bottom
# stroke, respect the curve better." Measured on the e's counter floor after
# round 235: 38 38 38 / 40 40 40 / 39 38 38 38 / 40 -- a 2-unit wave, the
# 0.92 thinning easing in over the tail's first 35% while the outer edge is
# still rising, so the inner edge flattened, rose, dipped. Eased over the
# WHOLE tail now (1.0): one monotone width from the ring's own to 0.92 x the
# 0.40 end, and the inner edge follows the outer's curve. The c's floor
# measured clean (37 36 36 37, symmetric) and is untouched.
E_ARM_EASE_R = float(__import__('os').environ.get("ALBO_ROM_E_EASE", 1.0))   # the roman tail reaches the round-94 thinning this far along its length (0.35 was round 235)
