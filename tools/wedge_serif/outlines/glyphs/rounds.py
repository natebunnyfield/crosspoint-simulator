"""o c e: the rounds. The o is the designed superellipse (the family's k)
with its counter the pen's inward offset -- the o's stress -- sized so the
counter is 1.036 wide over tall (ruling). The c and the e's eye are the
o's ring opened; their terminals are the family's: a flared face at the
top, a thinner pen-cut end below (c), a blunt end (e, ruling)."""
import math
from . import glyph
from .. import geom, pen
from ..geom import superellipse, line, join, cubic
from ..primitives import ring, stroke, pen_widths, widths, bar, beak
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
    return stroke(center, pen_widths(center, profile), cut0=cut0, cut1=cut1), center

@glyph('c')
def g_c(c):
    """The o's ring from 42 to 318 degrees. Upper terminal: a swell into a
    near-vertical face (the family's beak face, no lip on the lowercase);
    lower terminal: thins to 0.7 of the pen and takes the pen cut."""
    prof = widths([(0.0, 1.30), (0.13, 1.0), (0.82, 1.0), (1.0, 0.70)])
    solid, center = open_arc(c, C_RX, 40, 318, prof, cut0=math.radians(-28), cut1=CUT)
    lip = beak(center, pen.th_t(geom.tangents(center)[0]) * 1.30, True, -28.0, lip=(0.35, 0.6))
    return geom.ink([solid, lip])

E_DEG, E_BAR, E_TH, E_END = 5.0, 0.62, 0.72, 330   # the e's dials (rulings, rounds 39 + 46)

@glyph('e')
def g_e(c):
    """Ring on the o's construction at the e's radius; the aperture is cut
    from the bar's underside down to the arm's blunt end at 330 degrees;
    the bar rises 5 degrees, 0.72 of the pen's width at that angle, its top
    at 0.62 xh at the letter's middle (rulings)."""
    xh = c["xh"]; wf = c["wf"]
    solid, outer, inner = o_ring(c, E_RX)
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
