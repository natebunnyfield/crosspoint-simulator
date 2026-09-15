"""o c e: the rounds. The o is the designed superellipse (the family's k)
with its counter the pen's inward offset -- the o's stress -- sized so the
counter is 1.036 wide over tall (ruling). The c and the e's eye are the
o's ring opened; their terminals are the family's: a flared face at the
top, a thinner pen-cut end below (c), a blunt end (e, ruling)."""
import math, os
from . import glyph
from .. import geom, pen
from ..geom import superellipse, line, join, cubic
from ..primitives import ring, stroke, pen_widths, widths, bar, beak, bowl_widths, widen_terminal
from .. import primitives as PR
from ..pen import S, XH, OVER, TH_V, TH_H, HAIR, CUT, BOWL_K, adj

O_RX = 227; C_RX = 210; E_RX = 186   # centerline radii of the record (x wf); the outer adds half the pen's vertical
_IO = pen.IT_OVAL if pen.ITALIC else 1.0   # round 108: in the italic the c and the e narrow with the o (they were 25% wider than it)

def o_ring(c, rx_center, ry_center=None, cy=None, k=BOWL_K, w_scale=1.0):
    """A full round on the o's construction: outer superellipse whose x
    radius is the centerline's plus half the vertical pen, y radius the
    x-height half plus the overshoot at the INK's edge (ruling: 14)."""
    xh = c["xh"]; wf = c["wf"] * pen.IT_OVAL   # round 101: the italic narrows the o (measured on five real italics)
    rx = rx_center * wf + TH_V / 2 * w_scale; ry = (xh / 2 + OVER) if ry_center is None else ry_center
    cy = xh / 2 if cy is None else cy
    return ring(rx, cy, rx, ry, k=k, w_scale=w_scale)

O_FLOOR_ADJ = 0.55   # round 92 (adj 'o'): the o read hollow -- its knot the lowest of any letter (-11%), the hairs dropping to gray at 13 pt; floored like the 6's tail
@glyph('o')
def g_o(c):
    if adj('o'):
        xh = c["xh"]; wf = c["wf"] * pen.IT_OVAL; rx = O_RX * wf + TH_V / 2
        solid, outer, inner = ring(rx, xh / 2, rx, xh / 2 + OVER, floor=S * O_FLOOR_ADJ); return solid
    solid, outer, inner = o_ring(c, O_RX)
    return solid

def open_arc(c, rx_center, a0_deg, a1_deg, profile, cut0=None, cut1=None, k=BOWL_K, cx=None, cy=None, ry_center=None):
    """An open round stroke on the o's centerline (rx_center x wf, the
    centerline overshoot), the pen's widths times a declared profile."""
    xh = c["xh"]; wf = c["wf"]; rx = rx_center * wf
    ry = (xh / 2 + OVER - TH_H / 2) if ry_center is None else ry_center
    cx = rx + TH_V / 2 if cx is None else cx; cy = xh / 2 if cy is None else cy
    center = superellipse(cx, cy, rx, ry, math.radians(a0_deg), math.radians(a1_deg), k)
    return stroke(center, bowl_widths(center, profile), cut0=cut0, cut1=cut1), center

@glyph('c')
def g_c(c):
    """The o's ring from 42 to 318 degrees. Upper terminal: a swell into a
    near-vertical face (the family's beak face, no lip on the lowercase);
    lower terminal: thins to 0.7 of the pen and takes the pen cut."""
    if PR.BOWL and PR.BOWL.get('widen'):   # variant C: both free ends widen into the family's cut, no beak
        prof = widen_terminal(widen_terminal(None, True), False)
        solid, center = open_arc(c, C_RX * _IO, 40, 318, prof, cut0=CUT, cut1=CUT); return solid
    top = 1.10 if adj('c') else 1.30   # round 92 (adj 'c'): both terminals heavy (band +15% Albertus) -- the top's swell 1.30 -> 1.10
    prof = widths([(0.0, top), (0.13, 1.0), (0.82, 1.0), (1.0, 0.70)])
    solid, center = open_arc(c, C_RX * _IO, 40, 318, prof, cut0=math.radians(-28), cut1=CUT)
    lip = beak(center, PR.bowl_th(geom.tangents(center)[0]) * top, True, -28.0, lip=(0.35, 0.6))
    return geom.ink([solid, lip])

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
E_TIPDEG_R = float(os.environ.get("ALBO_E_TIPDEG_R", 50.0))# the direction the tail is travelling when it ends

E_BAR_ADJ, E_TH_ADJ = 0.58, 0.66   # round 92 (adj 'e'): the eye small for its bar -- bar top 0.62 -> 0.58 xh (eye taller), bar 0.72 -> 0.66 of the pen

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
    solid, outer, inner = _e_ring(c, E_RX * _IO, E_ARM_THIN, E_ARM_OUT)
    rx = E_RX * _IO * wf + TH_V / 2; cx = rx; cy = xh / 2
    tilt = math.radians(E_DEG_IT if pen.ITALIC else E_DEG); slope = math.tan(tilt)
    e_bar, e_th = (E_BAR_ADJ, E_TH_ADJ) if adj('e') else (E_BAR, E_TH)
    th = max(pen.th(E_DEG_IT if pen.ITALIC else E_DEG) * e_th, S * 0.35)
    bar_top = lambda x: xh * e_bar + (x - cx) * slope
    under = lambda x: bar_top(x) - th
    # the bar: from inside the left stroke to inside the right stroke
    b = stroke([(cx - rx + 8, bar_top(cx - rx + 8) - th / 2), (cx + rx - 42, bar_top(cx + rx - 42) - th / 2)], th)
    # the aperture: between the arm's end face (radial at E_END) and the bar's underside
    a = math.radians(E_END_IT if pen.ITALIC else E_END_R); far = 3 * rx
    aperture = geom.poly([(cx, cy), (cx + far * math.cos(a), cy + far * math.sin(a)), (cx + far, under(cx + far)), (cx, under(cx))])
    parts = [solid.difference(aperture), b, _e_tail(outer, inner, cx, cy, rx, xh, a)]
    return geom.ink(parts)


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


def _e_tail(outer, inner, cx, cy, rx, xh, a_cut):
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
    Po, To = _ray_hit(outer, cx, cy, R)
    Pi, _ = _ray_hit(inner, cx, cy, R)
    if Po is None or Pi is None:
        return geom.poly([(0, 0), (0, 0), (0, 0)])
    tail_end, tipx, tipy, tipdeg = ((E_TAIL_IT, E_TIP_X, E_TIP_Y, E_TIP_DEG) if pen.ITALIC
                                    else (E_TAIL_R, E_TIPX_R, E_TIPY_R, E_TIPDEG_R))
    w0 = math.hypot(Po[0] - Pi[0], Po[1] - Pi[1])   # the ring's width on the cut
    if To[0] < 0:            # travel counterclockwise, up the bowl's right
        To = (-To[0], -To[1])
    tip = (cx + tipx * rx, tipy * xh)
    L = math.hypot(tip[0] - Po[0], tip[1] - Po[1])
    d2 = math.radians(tipdeg); D2 = (math.cos(d2), math.sin(d2))
    edge = cubic(Po,
                 (Po[0] + To[0] * L * 0.30, Po[1] + To[1] * L * 0.30),
                 (tip[0] - D2[0] * L * 0.55, tip[1] - D2[1] * L * 0.55),
                 tip)
    wf = lambda t: w0 * (1.0 - (1.0 - tail_end) * (3 * t * t - 2 * t ** 3))
    return PR.edge_stroke(edge, wf, side=1)[0]
