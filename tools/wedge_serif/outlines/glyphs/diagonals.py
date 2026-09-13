"""v w x y z k: the diagonals, wedges on the outer side (0.9 x 0.9); the
thin strokes at 0.72 of the thick; the k's leg the A's kick at 56 degrees."""
import math
from . import glyph
from .. import geom, pen
from ..geom import cubic, line
from ..primitives import stem, diagonal, stroke, pen_widths, widths, wedge, diag_wedge, end_wedge, bar
from ..pen import S, XH, OVER, TH_V, TH_H, HAIR, CUT, WL, WD, DROP, ENT

THICK = TH_V * 1.02   # a down-right diagonal on the pen is ~79-82; the thin 0.72 of that
THIN = THICK * 0.72

@glyph('v')
def g_v(c):
    xh = c["xh"]; wf = c["wf"]; w = 440 * wf
    a = diagonal((S * 0.4, xh), (w / 2, 0), THICK, serif0=1)
    b = diagonal((w - S * 0.4, xh), (w / 2 + S * 0.12, 0), THIN, serif0=-1)
    return geom.ink([a, b])

@glyph('w')
def g_w(c):
    xh = c["xh"]; wf = c["wf"]; w = 680 * wf
    a = diagonal((S * 0.4, xh), (w * 0.27, 0), THICK, serif0=1)
    b = diagonal((w * 0.5, xh * 0.96), (w * 0.27 + S * 0.12, 0), THIN)
    d = diagonal((w * 0.5, xh * 0.96), (w * 0.73, 0), THICK)
    e = diagonal((w - S * 0.4, xh), (w * 0.73 + S * 0.12, 0), THIN, serif0=-1)
    apex = wedge((w * 0.5 - THIN * 0.36, xh * 0.96), (0, 1), (-1, 0), WL * 0.9, WD * 0.9, DROP)
    return geom.ink([a, b, d, e, apex])

@glyph('x')
def g_x(c):
    xh = c["xh"]; wf = c["wf"]; w = 430 * wf
    a = diagonal((S * 0.4, xh), (w - S * 0.4, 0), THICK, serif0=1, serif1=1)
    b = diagonal((w - S * 0.4, xh), (S * 0.4, 0), THIN, serif0=-1, serif1=-1)
    return geom.ink([a, b])

@glyph('y')
def g_y(c):
    xh = c["xh"]; wf = c["wf"]; desc = c["desc"]; w = 440 * wf
    a = diagonal((S * 0.4, xh), (w / 2 + S * 0.1, -S * 0.4), THICK, serif0=1)
    tail = cubic((w - S * 0.4, xh), (w * 0.52, -desc * 0.55), (w * 0.44, -desc * 1.08), (w * 0.02, -desc * 0.95))
    wfn = widths([(0.0, THIN), (0.5, THICK * 0.9), (0.85, THICK * 0.95), (1.0, S * 0.75)])
    t = stroke(tail, wfn, cut1=CUT)
    return geom.ink([a, t, end_wedge(tail, THIN, True, -1)])

@glyph('z')
def g_z(c):
    xh = c["xh"]; wf = c["wf"]; w = 400 * wf
    th = max(TH_H, S * 0.55)
    yt = xh - th / 2; yb = th / 2
    t = bar(0, w, xh, th, align='top', cut1=CUT, wedges=[('left', -1)])
    b = bar(0, w, 0, th, align='bottom', cut0=CUT, wedges=[('right', 1)])
    d = diagonal((w - S * 0.15, yt), (S * 0.15, yb), S)
    return geom.ink([t, b, d])

@glyph('k')
def g_k(c):
    """Stem, an arm from the stem at 0.42 xh to the x-height, and the leg
    springing from the arm at the A's kick, 56 degrees (ruling)."""
    xh = c["xh"]; wf = c["wf"]; x = S / 2
    st = stem(x, 0, c["asc"], top='left', foot='both')
    A0, B0 = (x + 360 * wf, xh * 0.97), (x + S * 0.2, xh * 0.42)
    arm = diagonal(A0, B0, THIN, serif0=1)
    u = (150 * wf - (B0[0] - x)) / (A0[0] - B0[0]); J = (B0[0] + (A0[0] - B0[0]) * u, B0[1] + (A0[1] - B0[1]) * u)
    foot = (J[0] + J[1] / math.tan(math.radians(56)), 0)
    d = (J[0] - foot[0], J[1] - foot[1]); L = math.hypot(*d); d = (d[0] / L, d[1] / L)
    leg = diagonal(foot, (J[0] + d[0] * S * 0.25, J[1] + d[1] * S * 0.25), widths([(0.0, THICK), (0.78, THICK), (1.0, THICK * 0.55)]), serif0=1)
    return geom.ink([st, arm, leg])
