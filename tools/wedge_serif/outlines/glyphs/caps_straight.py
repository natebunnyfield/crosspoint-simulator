"""A-Z on the same hand: cap stems at 1.137 x the lowercase (the wedge
family at ONE size, round 22), the D's ring for D B P R (rulings), beaks
on C G S, the kicks at their ruled angles (A 65, R 60, K 37), the two-sided
tops on the I and the U's right stem, no bar on the J. Widths are solved
by the builder against the garalde references' medians (c['W'])."""
import math
from . import glyph
from .. import geom, pen
from ..geom import cubic, line, join, superellipse, catmull, tangents
from ..primitives import (stem, stem_edge_x, ring, ring_from, half_bowl, stroke, pen_widths, widths, dot, wedge,
                          diag_wedge, end_wedge, diagonal, bar, beak, trap)
from ..pen import S, CS, XH, OVER, TH_V, TH_H, HAIR, CUT, WL, WD, DROP, ENT, BOWL_K, CAP_STEM

def W_(c, ch, default): return default * c["W"].get(ch, 1.0)
CW = TH_V * CAP_STEM          # the drawn cap stem, 87.9
THIN = CW * 0.72              # the capitals' thin diagonal
BEAK_CUT = -28.0

def cstem(x, y0, y1, top='left', foot='both', **kw):
    return stem(x, y0, y1, cap=True, top=top, foot=foot, **kw)

@glyph('A')
def g_A(c):
    """Thin left leg with a FLAT foot (round 36: the wedge's tip on the
    baseline, the face pen-cut level), thick right leg with the outer
    wedge, the thin stroke ending inside the thick one under the apex, the
    bar low at 0.28 C."""
    C = c["cap"]; w = W_(c, 'A', 600); s = CS
    p0, p1 = (s * 0.3, 0), (w / 2 - s * 0.06, C - s * 0.32)
    tn = geom.tangents(line(p0, p1))[0]
    left = stroke(line(p0, p1), THIN, cut0=-math.atan2(tn[0], tn[1]))
    # the flat foot: a bracket up the leg's left edge, tip ON the baseline
    nrm = (-tn[1], tn[0]); Apt = (p0[0] - THIN / 2 / tn[1], 0.0)
    edge_at = lambda d: (Apt[0] + tn[0] * d, tn[1] * d)
    foot = wedge(Apt, (0, -1), (-1, 0), WL * 0.9, WD * 0.9, 0.0, edge_at=edge_at)
    right = diagonal((w - s * 0.3, 0), (w / 2 - s * 0.18, C), CW, serif0=1)
    b = stroke(line((w * 0.19, C * 0.28), (w * 0.81, C * 0.28)), TH_H)
    return geom.ink([left, foot, right, b])

@glyph('B')
def g_B(c):
    C = c["cap"]; x = CS / 2; w = W_(c, 'B', 380); edge = x + CW / 2
    st = cstem(x, 0, C, top='left', foot='left')
    up, *_ = half_bowl(edge, C, C * 0.55 - TH_H * 0.3, w * 0.86 * 0.72 + TH_V / 2, open_bottom=0.0)
    lo, *_ = half_bowl(edge, C * 0.55 + TH_H * 0.3, 0, w * 0.72 + TH_V / 2, open_bottom=0.3)
    return geom.ink([st, up, lo])

def cap_arc(c, rx_c, a0, a1, profile, cut0=None, cut1=None, k=BOWL_K, ry_c=None, cy=None):
    C = c["cap"]; ry = (C / 2 + OVER - TH_H / 2) if ry_c is None else ry_c; cy = C / 2 if cy is None else cy
    center = superellipse(rx_c + TH_V / 2, cy, rx_c, ry, math.radians(a0), math.radians(a1), k)
    return stroke(center, pen_widths(center, profile), cut0=cut0, cut1=cut1), center

@glyph('C')
def g_C(c):
    rx = W_(c, 'C', 330)
    prof = widths([(0.0, 1.3), (0.12, 1.0), (0.78, 1.0), (1.0, 0.3)])
    body, center = cap_arc(c, rx, 43, 334, prof, cut0=math.radians(BEAK_CUT))
    lip = beak(center, pen.th_t(tangents(center)[0]) * 1.3, True, BEAK_CUT)
    return geom.ink([body, lip])

@glyph('D')
def g_D(c):
    C = c["cap"]; x = CS / 2; rx = W_(c, 'D', 330); edge = x + CW / 2
    st = cstem(x, 0, C, top='left', foot='left')
    bowl, *_ = half_bowl(edge, C, 0, rx + TH_V / 2, open_bottom=0.3)
    return geom.ink([st, bowl])

@glyph('E')
def g_E(c):
    C = c["cap"]; x = CS / 2; w = W_(c, 'E', 420)
    st = cstem(x, 0, C, top='left', foot='left')
    th = max(TH_H, S * 0.5)
    return geom.ink([st, bar(x, x + w * 0.96, C, th, align='top', cut1=CUT, wedges=[('right', -1)]),
                     bar(x, x + w * 0.74, C * 0.54, th * 0.9, cut1=CUT),
                     bar(x, x + w, 0, th, align='bottom', cut1=CUT, wedges=[('right', 1)])])

@glyph('F')
def g_F(c):
    C = c["cap"]; x = CS / 2; w = W_(c, 'F', 400)
    st = cstem(x, 0, C, top='left', foot='both')
    th = max(TH_H, S * 0.5)
    return geom.ink([st, bar(x, x + w, C, th, align='top', cut1=CUT, wedges=[('right', -1)]),
                     bar(x, x + w * 0.72, C * 0.54, th * 0.9, cut1=CUT)])

@glyph('G')
def g_G(c):
    """The C's arc to 312 degrees bending into a vertical spur whose right
    edge is the bowl's outermost (one outline), the weight ramping to the
    cap stem over the bend; a short bar at 0.42 C, half a stem thick."""
    C = c["cap"]; rx = W_(c, 'G', 340); ry = C / 2 + OVER - TH_H / 2; s = CS
    th_h = max(TH_H, S * 0.5); yb = C * 0.42
    cx = rx + TH_V / 2
    arc = superellipse(cx, C / 2, rx, ry, math.radians(43), math.radians(312), BOWL_K)
    xg = cx + rx + TH_V / 2 - CW / 2                   # the spur's centerline: its right edge = the bowl's
    p0 = arc[-1]; d = (arc[-1][0] - arc[-3][0], arc[-1][1] - arc[-3][1]); L = math.hypot(*d); d = (d[0] / L, d[1] / L)
    ctrl = (xg, p0[1] + d[1] * (xg - p0[0]) / d[0]); p1 = (xg, ctrl[1] + (ctrl[1] - p0[1]) * 0.7)
    bend = cubic(p0, (p0[0] + (ctrl[0] - p0[0]) * 2 / 3, p0[1] + (ctrl[1] - p0[1]) * 2 / 3), (p1[0] + (ctrl[0] - p1[0]) * 2 / 3, p1[1] + (ctrl[1] - p1[1]) * 2 / 3), p1)[1:]
    run = line(p1, (xg, yb - th_h * 0.3))[1:]
    pts = arc + bend + run; N = len(pts) - 1; t0 = (len(arc) - 1) / N; t1 = (len(arc) + len(bend) - 1) / N
    base = pen_widths(pts)
    def wfn(t):
        w = base(t) * widths([(0.0, 1.3), (0.12, 1.0)])(t)
        if t >= t1: return CW
        if t > t0: u = (t - t0) / (t1 - t0); return w + (CW - w) * (3 * u * u - 2 * u ** 3)
        return w
    body = stroke(pts, wfn, cut0=math.radians(BEAK_CUT))
    lip = beak(pts, wfn(0.0), True, BEAK_CUT)
    b = bar(xg - s * 1.1, xg + s * 0.6, yb, th_h * 0.5, cut0=CUT, cut1=CUT)
    return geom.ink([body, lip, b])

@glyph('H')
def g_H(c):
    C = c["cap"]; x0 = CS / 2; x1 = x0 + W_(c, 'H', 520)
    return geom.ink([cstem(x0, 0, C), cstem(x1, 0, C, top='right'), bar(x0, x1, C * 0.52, max(TH_H, S * 0.5) * 0.95)])

@glyph('I')
def g_I(c):
    return geom.ink([cstem(CS / 2, 0, c["cap"], top='left+')])

@glyph('J')
def g_J(c):
    """No bar (round 36); the I's top wedge; the hook starts at the stem's
    weight and eases to the pen's by its turn, flaring into the pen cut."""
    C = c["cap"]; r = W_(c, 'J', 190); x = r * 1.05 + CS / 2; desc = c["desc"]
    st = cstem(x, r * 0.25 - 20, C, top='left', foot=None, ent_span=(r * 0.25 - 60, C))
    tail = cubic((x, r * 0.25), (x, -desc * 0.42), (x - r * 0.55, -desc * 0.55), (x - r * 1.1, -desc * 0.1))
    base = pen_widths(tail)
    wfn = lambda t: (CW if t < 0.1 else (base(t) if t > 0.45 else CW + (base(t) - CW) * (3 * ((t - 0.1) / 0.35) ** 2 - 2 * ((t - 0.1) / 0.35) ** 3))) * widths([(0.65, 1.0), (1.0, 1.3)])(t)
    return geom.ink([st, stroke(tail, wfn, cut1=CUT)])

def kick(J, angle_deg, w, bury=0.2, serif=1, taper=0.45):
    """A K/R leg drawn as the A's right leg: foot-first from the baseline
    at `angle`, the wedge foot on the outer side, thinning into J."""
    a = math.radians(angle_deg); foot = (J[0] + J[1] / math.tan(a), 0)
    d = (J[0] - foot[0], J[1] - foot[1]); L = math.hypot(*d); d = (d[0] / L, d[1] / L)
    top = (J[0] + d[0] * CS * bury, J[1] + d[1] * CS * bury)
    return diagonal(foot, top, widths([(0.0, w), (0.78, w), (1.0, w * (1 - taper))]), serif0=serif)

@glyph('K')
def g_K(c):
    """Arm with a 0.47-stem floor from the cap line (a third of a stem
    under it) to the stem's centre at 0.45 C; the leg springs from the arm
    0.16 of the way out, its angle solved so the foot lands half a stem past
    the arm's tip (round 36 / 42: ~37 degrees)."""
    C = c["cap"]; x = CS / 2; w = W_(c, 'K', 500); s = CS
    st = cstem(x, 0, C)
    A0, B0 = (x + w, C - s * 0.36), (x, C * 0.45)
    tn = tangents(line(B0, A0))[0]
    arm_w = max(THIN, 0.47 * S, pen.th_t(tn) * 0.72)
    arm = diagonal(A0, B0, arm_w, serif0=1)
    u = 0.16; J = (B0[0] + (A0[0] - B0[0]) * u, B0[1] + (A0[1] - B0[1]) * u)
    angle = math.degrees(math.atan2(J[1], A0[0] + s * 0.5 - J[0]))
    return geom.ink([st, arm, kick(J, angle, CW * 1.1, bury=0.1)])

@glyph('L')
def g_L(c):
    C = c["cap"]; x = CS / 2; w = W_(c, 'L', 420)
    return geom.ink([cstem(x, 0, C, top='left', foot='left'), bar(x, x + w, 0, max(TH_H, S * 0.5), align='bottom', cut1=CUT, wedges=[('right', 1)])])

@glyph('M')
def g_M(c):
    """Splayed: the outer strokes lean out a little, the apex on the
    baseline, a wedge crowning the left apex."""
    C = c["cap"]; s = CS; w = W_(c, 'M', 720); x0 = s / 2; x1 = x0 + w
    a = diagonal((x0 + s * 0.25, 0), (x0 + s * 0.45, C), THIN, serif0=-1)
    b = diagonal((x0 + s * 0.45, C), (x0 + w / 2, 0), CW)
    d = diagonal((x1 - s * 0.45, C), (x0 + w / 2, 0), THIN)
    e = diagonal((x1 - s * 0.25, 0), (x1 - s * 0.45, C), CW, serif0=1, serif1=-1)
    apex = wedge((x0 + s * 0.45 - THIN * 0.35, C), (0, 1), (-1, 0), WL * 0.9, WD, DROP)
    return geom.ink([a, b, d, e, apex])

@glyph('N')
def g_N(c):
    C = c["cap"]; s = CS; w = W_(c, 'N', 560); x0 = s / 2; x1 = x0 + w
    return geom.ink([cstem(x0, 0, C, top='left', foot='both', w=THIN), diagonal((x0 + s * 0.1, C - s * 0.3), (x1 - s * 0.1, s * 0.3), CW),
                     cstem(x1, 0, C, top='right', foot=None, w=THIN)])

def cap_ring(c, rx_c):
    C = c["cap"]; rx = rx_c + TH_V / 2; ry = C / 2 + OVER
    return ring(rx, C / 2, rx, ry)

@glyph('O')
def g_O(c):
    solid, o, i = cap_ring(c, W_(c, 'O', 350)); return solid

@glyph('P')
def g_P(c):
    C = c["cap"]; x = CS / 2; w = W_(c, 'P', 400); edge = x + CW / 2
    bowl, *_ = half_bowl(edge, C, C * 0.44, w * 0.72 + TH_V / 2, open_bottom=0.3)
    return geom.ink([cstem(x, 0, C), bowl])

@glyph('Q')
def g_Q(c):
    """The O with Van den Keere's swash tail (round 42): from the ring's
    centerline at 250 degrees, heaviest at its belly (1.05 stems), thinning
    to a pen-cut tip at 1.8 O-widths, 0.2 C down."""
    C = c["cap"]; rx_c = W_(c, 'O', 350); solid, o, i = cap_ring(c, rx_c); s = CS
    rx = rx_c + TH_V / 2; ry_c = C / 2 + OVER - TH_H / 2; W = 2 * rx
    p0 = superellipse(rx, C / 2, rx_c, ry_c, math.radians(250), math.radians(250.5), BOWL_K)[0]
    tail = cubic(p0, (W * 0.85, -C * 0.30), (W * 1.40, -C * 0.56), (W * 1.80, -C * 0.20))
    base = pen_widths(tail)
    def wfn(t):
        belly = max(0.0, 1 - abs(t - 0.45) / 0.4)
        return max(base(t), s * 1.05 * (3 * belly * belly - 2 * belly ** 3)) * widths([(0.0, 0.6), (0.12, 1.0), (0.8, 1.0), (1.0, 0.7)])(t)
    return geom.ink([solid, stroke(tail, wfn, cut1=CUT)])

@glyph('R')
def g_R(c):
    C = c["cap"]; x = CS / 2; w = W_(c, 'R', 400); edge = x + CW / 2
    bowl, cx, cy, rx, ry = half_bowl(edge, C, C * 0.46, w * 0.95 * 0.72 + TH_V / 2, open_bottom=0.3)
    ang = math.radians(-52); J = (cx + rx * math.cos(ang), cy + ry * math.sin(ang))
    return geom.ink([cstem(x, 0, C), bowl, kick(J, 60, CW * 1.05)])

@glyph('S')
def g_S(c):
    C = c["cap"]; w = W_(c, 'S', 440); o = OVER - TH_H / 2; st = CS
    spine = catmull([(w * 0.93, C * 0.80), (w * 0.62, C + o * 0.9), (w * 0.18, C * 0.86), (w * 0.2, C * 0.6),
                     (w * 0.8, C * 0.42), (w * 0.84, C * 0.16), (w * 0.42, -o * 0.9), (w * 0.04, C * 0.22)], tension=0.55)
    base = pen_widths(spine)
    def wfn(t):
        mid = 1.0 - min(1.0, abs(t - 0.5) / 0.28); want = base(t) * (1 - mid) + st * 0.92 * mid
        bot = max(0.0, 1 - abs(t - 0.74) / 0.22); want *= 1 + 0.2 * (3 * bot * bot - 2 * bot ** 3)
        return want * widths([(0.0, 1.3), (0.10, 1.0), (0.86, 1.0), (1.0, 0.3)])(t)
    body = stroke(spine, wfn, cut0=math.radians(BEAK_CUT))
    return geom.ink([body, beak(spine, wfn(0.0), True, BEAK_CUT)])

@glyph('T')
def g_T(c):
    C = c["cap"]; w = W_(c, 'T', 520); x = w / 2
    th = max(TH_H * 0.62, S * 0.45); yb = C - th / 2
    b = bar(0, w, C, th, align='top', wedges=[('left', -1), ('right', -1)])
    return geom.ink([b, cstem(x, 0, yb + th * 0.5 - 4, top=None, foot='both', ent_span=(0, C))])

@glyph('U')
def g_U(c):
    """Left stem at cap weight, the bowl reaching the overshoot and thinning
    to the thin right stem (0.78), whose top wedge is two-sided (ruling)."""
    C = c["cap"]; s = CS; w = W_(c, 'U', 520); x0 = s / 2; x1 = x0 + w; y0 = C * 0.42
    left = cstem(x0, y0 - 30, C, top='left', foot=None, ent_span=(0, C))
    right = cstem(x1, y0 - 30, C, top='right+', foot=None, w=CW * 0.78, ent_span=(0, C))
    yb = -OVER + TH_H / 2; cy = (8 * yb - 2 * y0) / 6
    pts = cubic((x0, y0), (x0, cy), (x1, cy), (x1, y0))
    return geom.ink([left, right, stroke(pts, widths([(0.0, CW), (0.5, TH_H * 1.05), (1.0, CW * 0.78)]))])

@glyph('V')
def g_V(c):
    C = c["cap"]; s = CS; w = W_(c, 'V', 560)
    return geom.ink([diagonal((s * 0.3, C), (w / 2, 0), CW, serif0=1), diagonal((w - s * 0.3, C), (w / 2 + s * 0.15, 0), THIN, serif0=-1)])

@glyph('W')
def g_W(c):
    C = c["cap"]; s = CS; w = W_(c, 'W', 820)
    f1, f2, apex = (w * 0.26, 0), (w * 0.74, 0), (w * 0.5, C)
    a = diagonal((s * 0.3, C), f1, CW, serif0=1)
    b = diagonal(apex, (f1[0] + s * 0.15, 0), THIN)
    d = diagonal(apex, f2, CW)
    e = diagonal((w - s * 0.3, C), (f2[0] + s * 0.15, 0), THIN, serif0=-1)
    crown = wedge((apex[0] - THIN * 0.35, C), (0, 1), (-1, 0), WL * 0.9, WD, DROP)
    return geom.ink([a, b, d, e, crown])

@glyph('X')
def g_X(c):
    C = c["cap"]; s = CS; w = W_(c, 'X', 540)
    return geom.ink([diagonal((s * 0.3, C), (w - s * 0.3, 0), CW, serif0=1, serif1=1), diagonal((w - s * 0.3, C), (s * 0.3, 0), THIN, serif0=-1, serif1=-1)])

@glyph('Y')
def g_Y(c):
    C = c["cap"]; s = CS; w = W_(c, 'Y', 540)
    return geom.ink([diagonal((s * 0.3, C), (w / 2 + 6, C * 0.45 - 10), CW, serif0=1), diagonal((w - s * 0.3, C), (w / 2 - 6, C * 0.45 - 10), THIN, serif0=-1),
                     cstem(w / 2, 0, C * 0.45 + s * 0.3, top=None, foot='both', ent_span=(0, C))])

@glyph('Z')
def g_Z(c):
    C = c["cap"]; s = CS; w = W_(c, 'Z', 500); th = max(TH_H, S * 0.5)
    return geom.ink([bar(0, w, C, th, align='top', cut0=CUT, wedges=[('left', -1)]), diagonal((w - s * 0.15, C - th / 2), (s * 0.15, th / 2), CS),
                     bar(0, w, 0, th, align='bottom', cut1=CUT, wedges=[('right', 1)])])
