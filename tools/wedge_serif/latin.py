"""The rest of the Latin set on the same pen: capitals A-Z, lining figures
0-9, and the punctuation an epub needs. Same primitives as alphabet2 (stem,
curve, bracket_wedge), counterpunched bowls from round17 (ring, Hole) where
a closed counter exists. Cap height 0.94 of the ascender (humanist caps sit
under the ascenders); figures 0.92 of the cap height, lining.
"""
import math
import alphabet2 as A
from alphabet2 import line, bez, ellipse, tangents, compose, taper_in, taper_out, flare_end, bracket_wedge, blob, catmull

def _round17():
    import round17
    return round17

# ---------------------------------------------------------------- helpers
# Per-glyph width multipliers, solved by the builder against the garalde
# references' measured ink widths (round 20). 1.0 = the drawn default.
W = {}
def _w(c, key, default):
    return default * W.get(key, 1.0) * c["wf"]

def capH(c): return c["asc"] * 0.941   # median of Dante, Van den Keere, Hoefler, Doves
CAP_STEM = 1.137                        # cap stem over lowercase stem, same references
# Old-style figures (three of the four references): 0 1 2 sit on the
# x-height, 6 and 8 rise, 3 4 5 7 9 descend. The boxes are the references'
# medians as fractions of the cap height; the builder draws each figure
# with height top - bot and shifts it to bot.
FIG_BOX = {'0': (0.66, -0.02), '1': (0.64, 0.0), '2': (0.66, 0.0), '3': (0.66, -0.31), '4': (0.66, -0.31),
           '5': (0.64, -0.31), '6': (0.98, -0.02), '7': (0.64, -0.31), '8': (0.98, -0.02), '9': (0.66, -0.31)}
_FIG = [None]
def figH(c):
    return _FIG[0] if _FIG[0] else capH(c) * 0.92

def vstem(c, P, x, y0, y1, top_sides=(1, -1), foot_sides=(-1, 1), thin=1.0, flare=True):
    """A capital's stem: bracketed wedges BOTH sides top and foot, at the
    cap stem weight (1.137 x the lowercase, the references' median)."""
    pts = line((x, y0), (x, y1), 36)
    thin = thin * CAP_STEM
    prof = c["ent"] if flare else (lambda t: 1.0)
    prof2 = (lambda t: prof(t) * thin)
    P.append(A.outline(pts, c["pen"], prof2))
    th = c["pen"].th((0, 1)) * thin
    if c["wl"] <= 0 or c["serif"] != "wedge": return
    for sd in top_sides:
        P.append(bracket_wedge((x, y1), (0, 1), (-1, 0), th * prof(1.0), c["wl"] * 0.8, c["wd"], sd, drop=c["drop"], fillet=c["fillet"]))
    for sd in foot_sides:
        P.append(bracket_wedge((x, y0), (0, -1), (1, 0), th * prof(0.0), c["wl"] * 0.8, c["wd"], sd, drop=c["drop"] * 0.6, fillet=c["fillet"]))

def bar(c, P, x0, x1, y, serif_ends=(), thick=1.0):
    pts = line((x0, y), (x1, y), 12)
    P.append(A.outline(pts, c["pen"], lambda t: thick, cut0=c["cut"], cut1=c["cut"]))
    th = max(c["pen"].th((1, 0)) * thick, c["s"] * 0.5)
    for end, side in serif_ends:   # ('left'|'right', +1 up | -1 down)
        if c["wl"] <= 0: continue
        P_ = (x0, y) if end == 'left' else (x1, y)
        d = (-1, 0) if end == 'left' else (1, 0); nrm = (0, -1) if end == 'left' else (0, 1)
        sd = side if end == 'right' else -side
        P.append(bracket_wedge(P_, d, nrm, th, c["wl"] * 0.7, c["wd"] * 0.8, sd, drop=0, fillet=c["fillet"]))

def diag(c, P, p0, p1, thin=1.0, serif0=None, serif1=None):
    pts = line(p0, p1, 30)
    thin = thin * CAP_STEM
    P.append(A.outline(pts, c["pen"], lambda t: thin))
    if c["wl"] <= 0: return
    tn = tangents(pts)
    if serif0:
        d = (-tn[0][0], -tn[0][1]); nrm = (-d[1], d[0]); th = c["pen"].th(tn[0]) * thin
        P.append(bracket_wedge(pts[0], d, nrm, th, c["wl"] * 0.8, c["wd"] * 0.8, serif0, drop=c["drop"], fillet=c["fillet"]))
    if serif1:
        d = tn[-1]; nrm = (-d[1], d[0]); th = c["pen"].th(tn[-1]) * thin
        P.append(bracket_wedge(pts[-1], d, nrm, th, c["wl"] * 0.8, c["wd"] * 0.8, serif1, drop=c["drop"], fillet=c["fillet"]))

def cp_ring(c, P, cx, cy, rx, ry, a0=0.0, a1=2 * math.pi, close_x=None):
    """Counterpunched ring (outer cut, counter clean). close_x: for a D-like
    half ring, both contours are closed along the vertical x=close_x."""
    R = _round17()
    cut = c.get("_cut")
    outer, inner = R.ring(c, cx, cy, rx, ry, a0, a1, 110, cut=cut)
    if close_x is not None:
        outer = [(close_x, outer[0][1])] + outer + [(close_x, outer[-1][1])]
        inner = [(close_x, inner[0][1])] + inner + [(close_x, inner[-1][1])]
    P.append(outer); P.append(R.Hole(inner))

# ---------------------------------------------------------------- capitals
def g_A(c):
    P = []; C = capH(c); w = _w(c, "A", 560); s = c["s"]
    diag(c, P, (s * 0.35, 0), (w / 2, C), thin=0.72, serif0=-1)
    diag(c, P, (w - s * 0.35, 0), (w / 2, C), serif0=1)
    A.curve(c, P, line((w * 0.2, C * 0.34), (w * 0.8, C * 0.34), 10)); return P

def g_B(c):
    P = []; C = capH(c); s = c["s"]; x = s / 2; w = _w(c, "B", 470)
    vstem(c, P, x, 0, C, top_sides=(1,), foot_sides=(-1,))
    up = bez((x, C), (x + w * 0.85, C), (x + w * 0.85, C * 0.54), (x, C * 0.54), 40)
    lo = bez((x, C * 0.54), (x + w * 1.05, C * 0.54), (x + w * 1.05, 0), (x, 0), 40)
    A.curve(c, P, up, compose(taper_in(0.5, 0.15), taper_out(0.5, 0.15)))
    A.curve(c, P, lo, compose(taper_in(0.5, 0.15), taper_out(0.5, 0.15))); return P

def g_C(c):
    P = []; C = capH(c); rx = _w(c, "C", 300); ry = C / 2 + c["over"]
    pts = ellipse(rx, C / 2, rx, ry, math.radians(40), math.radians(318), 100, c["k"])
    A.curve(c, P, pts, compose(flare_end(0.25, 0.12), lambda t: flare_end(0.25, 0.12)(1 - t)), cut0=c["cut"], cut1=c["cut"]); return P

def g_D(c):
    P = []; C = capH(c); s = c["s"]; x = s / 2; rx = _w(c, "D", 330)
    vstem(c, P, x, 0, C, top_sides=(1,), foot_sides=(-1,))
    cp_ring(c, P, x + rx - 300 * c["wf"], C / 2, rx, C / 2 + c["over"], -math.pi / 2, math.pi / 2, close_x=x)
    return P

def g_E(c):
    P = []; C = capH(c); s = c["s"]; x = s / 2; w = _w(c, "E", 440)
    vstem(c, P, x, 0, C, top_sides=(1,), foot_sides=(-1,))
    bar(c, P, x, x + w, C, serif_ends=[('right', -1)]); bar(c, P, x, x + w * 0.82, C * 0.52, thick=0.9)
    bar(c, P, x, x + w * 1.04, 0, serif_ends=[('right', 1)]); return P

def g_F(c):
    P = []; C = capH(c); s = c["s"]; x = s / 2; w = _w(c, "F", 420)
    vstem(c, P, x, 0, C, top_sides=(1,), foot_sides=(-1, 1))
    bar(c, P, x, x + w, C, serif_ends=[('right', -1)]); bar(c, P, x, x + w * 0.8, C * 0.52, thick=0.9); return P

def g_G(c):
    P = []; C = capH(c); rx = _w(c, "G", 310); ry = C / 2 + c["over"]; s = c["s"]
    pts = ellipse(rx, C / 2, rx, ry, math.radians(40), math.radians(345), 110, c["k"])
    A.curve(c, P, pts, flare_end(0.25, 0.12), cut0=c["cut"])
    xg = rx + rx * 0.98
    vstem(c, P, xg - s * 0.5, C * 0.06, C * 0.46, top_sides=(), foot_sides=(), flare=False)
    bar(c, P, rx + rx * 0.35, xg, C * 0.46, serif_ends=[]); return P

def g_H(c): return A.g_H(c)

def g_I(c):
    P = []; vstem(c, P, c["s"] / 2, 0, capH(c)); return P

def g_J(c):
    P = []; C = capH(c); s = c["s"]; r = 190 * c["wf"]; x = 200 * c["wf"] + s / 2
    vstem(c, P, x, r * 0.2 - s * 0.5, C, foot_sides=())
    tail = bez((x, r * 0.2), (x, -c["over"] * 0.6), (x - r * 0.6, -c["over"] * 0.8), (x - r * 1.15, r * 0.35), 40)
    A.curve(c, P, tail, flare_end(0.3, 0.35), cut1=c["cut"]); return P

def g_K(c):
    P = []; C = capH(c); s = c["s"]; x = s / 2; w = _w(c, "K", 520)
    vstem(c, P, x, 0, C, top_sides=(1,), foot_sides=(-1, 1))
    diag(c, P, (x + w, C), (x + s * 0.2, C * 0.42), thin=0.74, serif0=1)
    diag(c, P, (x + w * 0.4, C * 0.55), (x + w * 1.05, 0), serif1=-1); return P

def g_L(c):
    P = []; C = capH(c); s = c["s"]; x = s / 2; w = _w(c, "L", 430)
    vstem(c, P, x, 0, C, top_sides=(1, -1), foot_sides=(-1,))
    bar(c, P, x, x + w, 0, serif_ends=[('right', 1)]); return P

def g_M(c):
    P = []; C = capH(c); s = c["s"]; x0 = s / 2; w = _w(c, "M", 700); x1 = x0 + w
    vstem(c, P, x0, 0, C, top_sides=(1,), foot_sides=(-1, 1), thin=0.78)
    diag(c, P, (x0, C), (x0 + w / 2, C * 0.08))
    diag(c, P, (x1, C), (x0 + w / 2, C * 0.08), thin=0.72)
    vstem(c, P, x1, 0, C, top_sides=(-1,), foot_sides=(-1, 1), thin=0.78); return P

def g_N(c):
    P = []; C = capH(c); s = c["s"]; x0 = s / 2; w = _w(c, "N", 560); x1 = x0 + w
    vstem(c, P, x0, 0, C, top_sides=(1,), foot_sides=(-1, 1), thin=0.72)
    diag(c, P, (x0, C), (x1, 0))
    vstem(c, P, x1, 0, C, top_sides=(-1, 1), foot_sides=(), thin=0.72); return P

def g_O(c):
    P = []; C = capH(c); rx = _w(c, "O", 330); cp_ring(c, P, rx, C / 2, rx, C / 2 + c["over"]); return P

def g_P(c):
    P = []; C = capH(c); s = c["s"]; x = s / 2; w = _w(c, "P", 450)
    vstem(c, P, x, 0, C, top_sides=(1,), foot_sides=(-1, 1))
    bowl = bez((x, C), (x + w * 1.0, C), (x + w * 1.0, C * 0.46), (x, C * 0.46), 44)
    A.curve(c, P, bowl, compose(taper_in(0.5, 0.15), taper_out(0.5, 0.15))); return P

def g_Q(c):
    P = g_O(c); C = capH(c); rx = 330 * c["wf"]
    tail = line((rx * 1.05, C * 0.16), (rx * 1.9, -C * 0.22), 20)
    A.curve(c, P, tail, flare_end(0.3, 0.4), cut1=c["cut"]); return P

def g_R(c):
    P = g_P(c); C = capH(c); s = c["s"]; x = s / 2; w = 450 * c["wf"]
    diag(c, P, (x + w * 0.45, C * 0.47), (x + w * 1.12, 0), serif1=-1); return P

def g_S(c):
    P = []; C = capH(c); w = _w(c, "S", 480); o = c["over"]
    spine = catmull([(w * 0.94, C * 0.80), (w * 0.62, C + o * 0.9), (w * 0.18, C * 0.86), (w * 0.2, C * 0.6),
                     (w * 0.8, C * 0.42), (w * 0.84, C * 0.16), (w * 0.42, -o * 0.9), (w * 0.05, C * 0.2)], 16, 0.55)
    A.curve(c, P, spine, compose(flare_end(0.25, 0.1), lambda t: flare_end(0.25, 0.1)(1 - t)), cut0=c["cut"], cut1=c["cut"]); return P

def g_T(c):
    P = []; C = capH(c); s = c["s"]; w = _w(c, "T", 500); x = w / 2
    bar(c, P, 0, w, C, serif_ends=[('left', -1), ('right', -1)])
    vstem(c, P, x, 0, C - s * 0.2, top_sides=(), foot_sides=(-1, 1)); return P

def g_U(c):
    P = []; C = capH(c); s = c["s"]; x0 = s / 2; w = _w(c, "U", 540); x1 = x0 + w
    vstem(c, P, x0, C * 0.38 - s * 0.5, C, top_sides=(1, -1), foot_sides=())
    A.curve(c, P, bez((x0, C * 0.38), (x0, -c["over"] * 0.6), (x1, -c["over"] * 0.6), (x1, C * 0.38), 44))
    vstem(c, P, x1, C * 0.38 - s * 0.5, C, top_sides=(1, -1), foot_sides=(), thin=0.78); return P

def g_V(c):
    P = []; C = capH(c); s = c["s"]; w = _w(c, "V", 560)
    diag(c, P, (s * 0.35, C), (w / 2, 0), serif0=1)
    diag(c, P, (w - s * 0.35, C), (w / 2, 0), thin=0.72, serif0=-1); return P

def g_W(c):
    P = []; C = capH(c); s = c["s"]; w = _w(c, "W", 790)
    diag(c, P, (s * 0.35, C), (w * 0.27, 0), serif0=1)
    diag(c, P, (w * 0.5, C * 0.96), (w * 0.27, 0), thin=0.72)
    diag(c, P, (w * 0.5, C * 0.96), (w * 0.73, 0))
    diag(c, P, (w - s * 0.35, C), (w * 0.73, 0), thin=0.72, serif0=-1); return P

def g_X(c):
    P = []; C = capH(c); s = c["s"]; w = _w(c, "X", 540)
    diag(c, P, (s * 0.35, C), (w - s * 0.35, 0), serif0=1, serif1=1)
    diag(c, P, (w - s * 0.35, C), (s * 0.35, 0), thin=0.72, serif0=-1, serif1=-1); return P

def g_Y(c):
    P = []; C = capH(c); s = c["s"]; w = _w(c, "Y", 540)
    diag(c, P, (s * 0.35, C), (w / 2, C * 0.45), serif0=1)
    diag(c, P, (w - s * 0.35, C), (w / 2, C * 0.45), thin=0.72, serif0=-1)
    vstem(c, P, w / 2, 0, C * 0.45 + s * 0.3, top_sides=(), foot_sides=(-1, 1)); return P

def g_Z(c):
    P = []; C = capH(c); s = c["s"]; w = _w(c, "Z", 500)
    bar(c, P, 0, w, C, serif_ends=[('left', -1)])
    zd = line((w - s * 0.15, C), (s * 0.15, 0), 30); tz = tangents(zd)[0]
    A.curve(c, P, zd, lambda t: c["s"] / c["pen"].th(tz))
    bar(c, P, 0, w, 0, serif_ends=[('right', 1)]); return P

# ---------------------------------------------------------------- figures (lining)
def g_zero(c):
    P = []; D = figH(c); rx = _w(c, "0", 230); cp_ring(c, P, rx, D / 2, rx, D / 2 + c["over"]); return P

def g_one(c):
    P = []; D = figH(c); s = c["s"]; x = 200 * c["wf"] + s / 2
    vstem(c, P, x, 0, D, top_sides=(), foot_sides=(-1, 1))
    A.curve(c, P, line((x - 150 * c["wf"], D * 0.72), (x, D), 12), lambda t: 0.85, cut0=c["cut"]); return P

def g_two(c):
    P = []; D = figH(c); s = c["s"]; w = _w(c, "2", 440); rx = w * 0.46
    top = ellipse(rx, D - rx * 0.95, rx, rx * 0.95, math.radians(190), math.radians(-25), 60, c["k"])
    A.curve(c, P, top, flare_end(0.2, 0.15), cut0=c["cut"])
    diag(c, P, top[-1], (s * 0.2, 0))
    bar(c, P, 0, w, 0, serif_ends=[('right', 1)]); return P

def g_three(c):
    P = []; D = figH(c); w = _w(c, "3", 400); r1 = D * 0.24; r2 = D * 0.28
    top = ellipse(w * 0.5, D - r1, w * 0.48, r1, math.radians(175), math.radians(-60), 50, c["k"])
    bot = ellipse(w * 0.5, r2, w * 0.54, r2 + c["over"], math.radians(60), math.radians(-175), 60, c["k"])
    A.curve(c, P, top, flare_end(0.2, 0.15), cut0=c["cut"])
    A.curve(c, P, bot, compose(taper_in(0.6, 0.1), flare_end(0.25, 0.15)), cut1=c["cut"]); return P

def g_four(c):
    P = []; D = figH(c); s = c["s"]; w = _w(c, "4", 480); xs = w * 0.7
    diag(c, P, (xs - s * 0.2, D), (s * 0.1, D * 0.3), thin=0.75)
    bar(c, P, 0, w, D * 0.3)
    vstem(c, P, xs, 0, D, top_sides=(), foot_sides=(-1, 1)); return P

def g_five(c):
    P = []; D = figH(c); s = c["s"]; w = _w(c, "5", 400); r = D * 0.31
    bar(c, P, s * 0.3, w * 0.95, D, serif_ends=[('right', -1)])
    vstem(c, P, s * 0.3 + s / 2, D * 0.5, D, top_sides=(), foot_sides=(), thin=0.85, flare=False)
    bowl = ellipse(w * 0.5, r, w * 0.55, r + c["over"], math.radians(125), math.radians(-160), 70, c["k"])
    A.curve(c, P, bowl, compose(taper_in(0.55, 0.12), flare_end(0.25, 0.15)), cut1=c["cut"]); return P

def g_six(c):
    P = []; D = figH(c); rx = _w(c, "6", 230); r = D * 0.29
    top = ellipse(rx, D - rx * 1.0, rx * 0.95, rx * 1.0, math.radians(70), math.radians(180), 40, c["k"])
    A.curve(c, P, top, flare_end(0.25, 0.2), cut0=c["cut"])
    left = line(top[-1], (rx * 0.05, r), 16); A.curve(c, P, left)
    cp_ring(c, P, rx, r, rx, r + c["over"]); return P

def g_seven(c):
    P = []; D = figH(c); s = c["s"]; w = _w(c, "7", 440)
    bar(c, P, 0, w, D, serif_ends=[('left', -1)])
    diag(c, P, (w - s * 0.2, D), (w * 0.3, 0)); return P

def g_eight(c):
    P = []; D = figH(c); rx = _w(c, "8", 215); r1 = D * 0.235; r2 = D * 0.265
    cp_ring(c, P, rx, D - r1, rx * 0.86, r1); cp_ring(c, P, rx, r2, rx, r2 + c["over"]); return P

def g_nine(c):
    """A six turned over: counterpunched bowl at the top, the tail runs down
    the right side and curls to the bottom-left (the first draft ran the
    curl the other way and read as a mirrored e)."""
    P = []; D = figH(c); rx = _w(c, "9", 230); r = D * 0.29; s = c["s"]
    cp_ring(c, P, rx, D - r, rx, r)
    bot = ellipse(rx, rx * 1.0, rx * 0.95, rx * 1.0, math.radians(0), math.radians(-110), 40, c["k"])
    right = line((rx * 2 - s * 0.5, D - r), bot[0], 16); A.curve(c, P, right)
    A.curve(c, P, bot, flare_end(0.25, 0.2), cut1=c["cut"]); return P

# ---------------------------------------------------------------- punctuation
def dot(c, x, y, r=0.55): return blob((x, c["s"] * r + 0 if False else y), c["s"] * r)

def g_period(c): r = capH(c) * 0.08; return [blob((r, r), r)]
def g_comma(c):
    s = c["s"]; x = s * 0.55; P = [blob((x, s * 0.55), s * 0.55)]
    tail = bez((x + s * 0.1, s * 0.2), (x + s * 0.1, -s * 0.5), (x - s * 0.3, -s * 0.9), (x - s * 0.6, -s * 1.2), 20)
    P.append(A.outline(tail, c["pen"], lambda t: 0.9 - 0.6 * t)); return P
def g_colon(c): s = c["s"]; return [blob((s * 0.55, s * 0.55), s * 0.55), blob((s * 0.55, c["xh"] - s * 0.55), s * 0.55)]
def g_semicolon(c):
    P = g_comma(c); P.append(blob((c["s"] * 0.55, c["xh"] - c["s"] * 0.55), c["s"] * 0.55)); return P
def g_exclam(c):
    s = c["s"]; C = capH(c); P = [blob((s * 0.55, s * 0.55), s * 0.55)]
    P.append(A.outline(line((s * 0.55, s * 1.9), (s * 0.55, C), 20), c["pen"], lambda t: 0.55 + 0.5 * t, cut1=c["cut"])); return P
def g_question(c):
    s = c["s"]; C = capH(c); w = 380 * c["wf"]; P = [blob((w * 0.5, s * 0.55), s * 0.55)]
    hook = catmull([(w * 0.08, C * 0.74), (w * 0.28, C * 0.97), (w * 0.62, C * 0.98), (w * 0.88, C * 0.74),
                    (w * 0.74, C * 0.5), (w * 0.5, C * 0.38), (w * 0.5, C * 0.2)], 14, 0.5)
    A.curve(c, P, hook, compose(taper_in(0.55, 0.15), flare_end(0.1, 0.2)), cut0=c["cut"], cut1=c["cut"]); return P
def g_quotesingle(c):
    s = c["s"]; C = capH(c); return [A.outline(line((s * 0.5, C * 0.72), (s * 0.5, C), 8), c["pen"], lambda t: 0.8, cut0=c["cut"])]
def g_quotedbl(c):
    P = g_quotesingle(c); P.extend([[(x + c["s"] * 1.3, y) for x, y in p] for p in g_quotesingle(c)]); return P
def _quote(c, x, up):
    s = c["s"]; C = capH(c); y = C - s * 0.55
    P = [blob((x, y), s * 0.5)]
    if up: tail = bez((x + s * 0.1, y - s * 0.3), (x + s * 0.1, y - s * 1.0), (x - s * 0.3, y - s * 1.3), (x - s * 0.55, y - s * 1.6), 16)
    else:  tail = bez((x - s * 0.1, y + s * 0.3), (x - s * 0.1, y + s * 1.0), (x + s * 0.3, y + s * 1.3), (x + s * 0.55, y + s * 1.6), 16)
    P.append(A.outline(tail, c["pen"], lambda t: 0.85 - 0.55 * t)); return P
def g_quoteright(c): return _quote(c, c["s"] * 0.7, True)
def g_quoteleft(c): return [[(x, capH(c) - (y - capH(c) * 0.0) + capH(c) * 0.0) for x, y in p] for p in []] or _quote(c, c["s"] * 0.7, False)
def g_quotedblright(c): P = _quote(c, c["s"] * 0.7, True); P.extend(_quote(c, c["s"] * 2.0, True)); return P
def g_quotedblleft(c): P = _quote(c, c["s"] * 0.7, False); P.extend(_quote(c, c["s"] * 2.0, False)); return P
def g_hyphen(c): return [A.outline(line((0, capH(c) * 0.34), (0.37 * capH(c), capH(c) * 0.34), 8), c["pen"])]
def g_endash(c): return [A.outline(line((0, capH(c) * 0.34), (0.72 * capH(c), capH(c) * 0.34), 8), c["pen"])]
def g_emdash(c): return [A.outline(line((0, capH(c) * 0.34), (1.41 * capH(c), capH(c) * 0.34), 8), c["pen"])]
def g_parenleft(c):
    C = capH(c); d = c["desc"]; r = 150 * c["wf"]
    pts = ellipse(r, (C - d) / 2, r, (C + d) / 2 + 30, math.radians(105), math.radians(255), 50, 2.2)
    return [A.outline(pts, c["pen"], lambda t: 0.6 + 0.4 * math.sin(math.pi * t), cut0=c["cut"], cut1=c["cut"])]
def g_parenright(c):
    C = capH(c); d = c["desc"]; r = 150 * c["wf"]
    pts = ellipse(0, (C - d) / 2, r, (C + d) / 2 + 30, math.radians(75), math.radians(-75), 50, 2.2)
    return [A.outline(pts, c["pen"], lambda t: 0.6 + 0.4 * math.sin(math.pi * t), cut0=c["cut"], cut1=c["cut"])]
def g_bracketleft(c):
    C = capH(c); d = c["desc"]; s = c["s"]; w = 180 * c["wf"]
    return [A.outline(line((s * 0.4, -d), (s * 0.4, C), 20), c["pen"], lambda t: 0.85), A.outline(line((s * 0.4, C), (w, C), 6), c["pen"]), A.outline(line((s * 0.4, -d), (w, -d), 6), c["pen"])]
def g_bracketright(c):
    C = capH(c); d = c["desc"]; s = c["s"]; w = 180 * c["wf"]
    return [A.outline(line((w - s * 0.4, -d), (w - s * 0.4, C), 20), c["pen"], lambda t: 0.85), A.outline(line((0, C), (w - s * 0.4, C), 6), c["pen"]), A.outline(line((0, -d), (w - s * 0.4, -d), 6), c["pen"])]
def g_slash(c): C = capH(c); return [A.outline(line((0, -c["desc"] * 0.4), (330 * c["wf"], C), 20), c["pen"], lambda t: 0.8, cut0=c["cut"], cut1=c["cut"])]
def g_backslash(c): C = capH(c); return [A.outline(line((0, C), (330 * c["wf"], -c["desc"] * 0.4), 20), c["pen"], lambda t: 0.8, cut0=c["cut"], cut1=c["cut"])]
def g_asterisk(c):
    C = capH(c); cx, cy = 200 * c["wf"], C * 0.78; r = 150 * c["wf"]; P = []
    for k in range(5):
        a = math.pi / 2 + k * 2 * math.pi / 5
        P.append(A.outline(line((cx, cy), (cx + r * math.cos(a), cy + r * math.sin(a)), 8), c["pen"], lambda t: 0.75, cut1=c["cut"]))
    return P
def g_plus(c):
    y = c["xh"] * 0.55; w = 420 * c["wf"]
    return [A.outline(line((0, y), (w, y), 8), c["pen"], lambda t: 0.9), A.outline(line((w / 2, y - w / 2), (w / 2, y + w / 2), 8), c["pen"], lambda t: 0.9)]
def g_equal(c):
    y = c["xh"] * 0.55; w = 420 * c["wf"]; g = c["s"] * 1.1
    return [A.outline(line((0, y - g / 2), (w, y - g / 2), 8), c["pen"]), A.outline(line((0, y + g / 2), (w, y + g / 2), 8), c["pen"])]
def g_ampersand(c):
    C = capH(c); w = 760 * c["wf"]; o = c["over"]
    spine = catmull([(w * 0.95, C * 0.36), (w * 0.62, 0.0 - o * 0.4), (w * 0.15, C * 0.18), (w * 0.3, C * 0.5), (w * 0.62, C * 0.8),
                     (w * 0.6, C + o * 0.5), (w * 0.35, C * 0.92), (w * 0.34, C * 0.62), (w * 0.62, C * 0.32), (w * 0.98, C * 0.02)], 14, 0.5)
    return [A.outline(spine, c["pen"], compose(flare_end(0.2, 0.1), lambda t: flare_end(0.2, 0.12)(1 - t)), cut0=c["cut"], cut1=c["cut"])]
def g_percent(c):
    C = capH(c); P = []; r = 120 * c["wf"]
    P.extend(g_slash_at(c, 60 * c["wf"], 0, 60 * c["wf"] + 380 * c["wf"], C))
    R = _round17()
    for cx, cy in ((r + 10, C - r), (620 * c["wf"] - r, r)):
        outer, inner = R.ring(c, cx, cy, r, r, 0, 2 * math.pi, 60); P.append(outer); P.append(R.Hole(inner))
    return P
def g_slash_at(c, x0, y0, x1, y1): return [A.outline(line((x0, y0), (x1, y1), 20), c["pen"], lambda t: 0.75, cut0=c["cut"], cut1=c["cut"])]
def g_numbersign(c):
    C = capH(c); w = 480 * c["wf"]; P = []
    for x in (w * 0.32, w * 0.68): P.append(A.outline(line((x - w * 0.06, 0), (x + w * 0.06, C), 10), c["pen"], lambda t: 0.75))
    for y in (C * 0.35, C * 0.65): P.append(A.outline(line((0, y), (w, y), 8), c["pen"]))
    return P
def g_at(c):
    xh = c["xh"]; C = capH(c); w = 860 * c["wf"]; cx, cy = w * 0.5, xh * 0.5; P = []
    R = _round17()
    outer, inner = R.ring(c, cx + 20, cy, 170 * c["wf"], xh * 0.5, 0, 2 * math.pi, 70); P.append(outer); P.append(R.Hole(inner))
    P.append(A.outline(line((cx + 190 * c["wf"], xh * 0.95), (cx + 190 * c["wf"], 0.0), 16), c["pen"], lambda t: 0.8))
    big = ellipse(cx, cy, w * 0.5, xh * 0.55 + c["desc"] * 0.6, math.radians(-20), math.radians(300), 90, 2.2)
    P.append(A.outline(big, c["pen"], compose(flare_end(0.2, 0.1), lambda t: flare_end(0.2, 0.1)(1 - t)), cut0=c["cut"], cut1=c["cut"])); return P
def g_underscore(c): return [A.outline(line((0, -c["desc"] * 0.5), (500 * c["wf"], -c["desc"] * 0.5), 8), c["pen"])]
def g_ellipsis(c):
    s = c["s"]; return [blob((s * 0.55 + i * s * 2.4, s * 0.55), s * 0.55) for i in range(3)]

CAPS = {chr(k): globals()["g_" + chr(k)] for k in range(ord('A'), ord('Z') + 1)}
FIGS = {'0': g_zero, '1': g_one, '2': g_two, '3': g_three, '4': g_four, '5': g_five, '6': g_six, '7': g_seven, '8': g_eight, '9': g_nine}
PUNCT = {'.': g_period, ',': g_comma, ':': g_colon, ';': g_semicolon, '!': g_exclam, '?': g_question, "'": g_quotesingle, '"': g_quotedbl,
         '‘': g_quoteleft, '’': g_quoteright, '“': g_quotedblleft, '”': g_quotedblright,
         '-': g_hyphen, '–': g_endash, '—': g_emdash, '(': g_parenleft, ')': g_parenright, '[': g_bracketleft, ']': g_bracketright,
         '/': g_slash, '\\': g_backslash, '*': g_asterisk, '+': g_plus, '=': g_equal, '&': g_ampersand, '%': g_percent, '#': g_numbersign,
         '@': g_at, '_': g_underscore, '…': g_ellipsis}

SIDES = {
 'A': ('diag', 'diag'), 'B': ('straight', 'round'), 'C': ('round', 'open'), 'D': ('straight', 'round'), 'E': ('straight', 'open'),
 'F': ('straight', 'open'), 'G': ('round', 'straight'), 'H': ('straight', 'straight'), 'I': ('straight', 'straight'), 'J': ('open', 'straight'),
 'K': ('straight', 'diag'), 'L': ('straight', 'open'), 'M': ('straight', 'straight'), 'N': ('straight', 'straight'), 'O': ('round', 'round'),
 'P': ('straight', 'round'), 'Q': ('round', 'round'), 'R': ('straight', 'diag'), 'S': ('round', 'round'), 'T': ('open', 'open'),
 'U': ('straight', 'straight'), 'V': ('diag', 'diag'), 'W': ('diag', 'diag'), 'X': ('diag', 'diag'), 'Y': ('diag', 'diag'), 'Z': ('straight', 'straight'),
 '0': ('round', 'round'), '1': ('open', 'straight'), '2': ('round', 'straight'), '3': ('open', 'round'), '4': ('diag', 'straight'),
 '5': ('straight', 'round'), '6': ('round', 'round'), '7': ('straight', 'diag'), '8': ('round', 'round'), '9': ('round', 'round'),
}
for k in PUNCT: SIDES.setdefault(k, ('punct', 'punct'))
