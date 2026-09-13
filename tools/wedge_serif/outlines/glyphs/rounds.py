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
from ..pen import S, XH, OVER, TH_V, TH_H, HAIR, CUT, BOWL_K

O_RX = 227; C_RX = 210; E_RX = 186   # centerline radii of the record (x wf); the outer adds half the pen's vertical

def o_ring(c, rx_center, ry_center=None, cy=None, k=BOWL_K, w_scale=1.0):
    """A full round on the o's construction: outer superellipse whose x
    radius is the centerline's plus half the vertical pen, y radius the
    x-height half plus the overshoot at the INK's edge (ruling: 14)."""
    xh = c["xh"]; wf = c["wf"]
    rx = rx_center * wf + TH_V / 2 * w_scale; ry = (xh / 2 + OVER) if ry_center is None else ry_center
    cy = xh / 2 if cy is None else cy
    return ring(rx, cy, rx, ry, k=k, w_scale=w_scale)

@glyph('o')
def g_o(c):
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
        solid, center = open_arc(c, C_RX, 40, 318, prof, cut0=CUT, cut1=CUT); return solid
    prof = widths([(0.0, 1.30), (0.13, 1.0), (0.82, 1.0), (1.0, 0.70)])
    solid, center = open_arc(c, C_RX, 40, 318, prof, cut0=math.radians(-28), cut1=CUT)
    lip = beak(center, PR.bowl_th(geom.tangents(center)[0]) * 1.30, True, -28.0, lip=(0.35, 0.6))
    return geom.ink([solid, lip])

E_DEG, E_BAR, E_TH, E_END = 5.0, 0.62, 0.72, 330   # the e's dials (rulings, rounds 39 + 46)

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
ARM_START_DEG, ARM_END_DEG = 270.0, E_END
ARM_TAPER = 0.25
E_ARM_THIN = float(os.environ.get("FJORD_E_ARM_THIN", 0.90))
E_ARM_OUT = float(os.environ.get("FJORD_E_ARM_OUT", 8.0))

def _e_ring(c, rx_center, thin=1.0, out_shift=0.0, k=BOWL_K, taper_frac=ARM_TAPER):
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
    solid, outer, inner = _e_ring(c, E_RX, E_ARM_THIN, E_ARM_OUT)
    rx = E_RX * wf + TH_V / 2; cx = rx; cy = xh / 2
    tilt = math.radians(E_DEG); slope = math.tan(tilt)
    th = max(pen.th(E_DEG) * E_TH, S * 0.35)
    bar_top = lambda x: xh * E_BAR + (x - cx) * slope
    under = lambda x: bar_top(x) - th
    # the bar: from inside the left stroke to inside the right stroke
    b = stroke([(cx - rx + 8, bar_top(cx - rx + 8) - th / 2), (cx + rx - 42, bar_top(cx + rx - 42) - th / 2)], th)
    # the aperture: between the arm's end face (radial at E_END) and the bar's underside
    a = math.radians(E_END); far = 3 * rx
    aperture = geom.poly([(cx, cy), (cx + far * math.cos(a), cy + far * math.sin(a)), (cx + far, under(cx + far)), (cx, under(cx))])
    return geom.ink([solid.difference(aperture), b])
