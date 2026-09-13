"""v w x y z k: the diagonals, wedges on the outer side (0.9 x 0.9); the
thin strokes at 0.72 of the thick; the k's leg the A's kick at 56 degrees."""
import math
from . import glyph
from .. import geom, pen
from ..geom import cubic, line
from ..primitives import stem, diagonal, stroke, pen_widths, widths, wedge, diag_wedge, end_wedge, bar
from ..pen import S, XH, OVER, TH_V, TH_H, HAIR, CUT, WL, WD, DROP, ENT

def pw(p0, p1, mult=1.0):
    """Round 51's rule for every diagonal (`_diag`): the width is `mult` x
    the PEN's width at the stroke's own angle -- a down-right stroke is the
    pen's broad ~82, a down-left one its thin ~50, and 0.72 of THAT is the
    thin stroke of v w x y (36-40), not 0.72 of the stem."""
    tn = geom.tangents(line(p0, p1))[0]; return pen.th_t(tn) * mult

@glyph('v')
def g_v(c):
    xh = c["xh"]; wf = c["wf"]; w = 440 * wf
    p0, p1 = (S * 0.4, xh), (w / 2, 0); q0, q1 = (w - S * 0.4, xh), (w / 2 + S * 0.12, 0)
    return geom.ink([diagonal(p0, p1, pw(p0, p1), serif0=1), diagonal(q0, q1, pw(q0, q1, 0.72), serif0=-1)])

@glyph('w')
def g_w(c):
    xh = c["xh"]; wf = c["wf"]; w = 680 * wf
    P = [((S * 0.4, xh), (w * 0.27, 0), 1.0, 1), ((w * 0.5, xh * 0.96), (w * 0.27 + S * 0.12, 0), 0.72, None),
         ((w * 0.5, xh * 0.96), (w * 0.73, 0), 1.0, None), ((w - S * 0.4, xh), (w * 0.73 + S * 0.12, 0), 0.72, -1)]
    a, b, d, e = [diagonal(p0, p1, pw(p0, p1, m), serif0=sf) for p0, p1, m, sf in P]
    apex = wedge((w * 0.5 - pw(P[1][0], P[1][1], 0.72) * 0.36, xh * 0.96), (0, 1), (-1, 0), WL * 0.9, WD * 0.9, DROP)
    return geom.ink([a, b, d, e, apex])

@glyph('x')
def g_x(c):
    xh = c["xh"]; wf = c["wf"]; w = 430 * wf
    p0, p1 = (S * 0.4, xh), (w - S * 0.4, 0); q0, q1 = (w - S * 0.4, xh), (S * 0.4, 0)
    return geom.ink([diagonal(p0, p1, pw(p0, p1), serif0=1, serif1=1), diagonal(q0, q1, pw(q0, q1, 0.72), serif0=-1, serif1=-1)])

@glyph('y')
def g_y(c):
    xh = c["xh"]; wf = c["wf"]; desc = c["desc"]; w = 440 * wf
    p0, p1 = (S * 0.4, xh), (w / 2 + S * 0.1, -S * 0.4)
    a = diagonal(p0, p1, pw(p0, p1), serif0=1)
    tail = cubic((w - S * 0.4, xh), (w * 0.52, -desc * 0.55), (w * 0.44, -desc * 1.08), (w * 0.02, -desc * 0.95))
    # round 51: the pen's width along the tail x (0.72 rising to 1.0 by the middle), flaring 0.3 into the cut
    wfn = pen_widths(tail, lambda t: (0.72 + 0.28 * min(1.0, t * 2)) * widths([(0.7, 1.0), (1.0, 1.3)])(t))
    t = stroke(tail, wfn, cut1=CUT)
    return geom.ink([a, t, end_wedge(tail, wfn(0.0), True, -1)])

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
    arm = diagonal(A0, B0, pw(A0, B0, 0.78), serif0=1)   # round 51: 0.78 x the pen at the arm's angle
    u = (150 * wf - (B0[0] - x)) / (A0[0] - B0[0]); J = (B0[0] + (A0[0] - B0[0]) * u, B0[1] + (A0[1] - B0[1]) * u)
    foot = (J[0] + J[1] / math.tan(math.radians(56)), 0)
    d = (J[0] - foot[0], J[1] - foot[1]); L = math.hypot(*d); d = (d[0] / L, d[1] / L)
    lw = pw(foot, J)   # round 51: the pen at the leg's angle (58 at 56 degrees)
    leg = diagonal(foot, (J[0] + d[0] * S * 0.25, J[1] + d[1] * S * 0.25), widths([(0.0, lw), (0.78, lw), (1.0, lw * 0.55)]), serif0=1)
    return geom.ink([st, arm, leg])
