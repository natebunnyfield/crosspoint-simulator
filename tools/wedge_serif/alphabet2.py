"""Second drawing model, after the owner's "try harder. there is no elegance."

What was crude in the first, and what replaces it:
  - thickness jumped: max(|sin|, hairline) has a corner. Now a smooth blend
    hair + (stem - hair) * |sin(phi - stress)|^1.15 -- continuous everywhere.
  - joins were butted: an arch or bowl met its stem at full weight. Now every
    curve that departs a stem TAPERS into it (a real pen thins on the turn),
    so the n's shoulder, the a's bowl and the d's bowl grow out of the stem.
  - serifs were triangles: flat top, straight hypotenuse. Now a bracketed
    wedge: a concave fillet from the stem's edge out to a short flat, the
    apex a little below the stem end so the wedge reads as a foot, not a flag.
  - stem ends were square. Humanist ends are cut on the pen angle, so an
    unseriffed end is sheared ~12 degrees.
  - curves had no overshoot and the s was three cubics with kinks. Now round
    letters overshoot 12 units top and bottom, and the s is one smooth spline
    through six points with tangent continuity.
  - fitting stays by the n (the ruling), at the S-tier's 0.8.
Coordinates: 1000 upm, y up, baseline 0.
"""
import math

# ---------------------------------------------------------------- curves
def bez(p0, p1, p2, p3, n=40):
    out = []
    for i in range(n + 1):
        t = i / n; m = 1 - t
        out.append((m*m*m*p0[0] + 3*m*m*t*p1[0] + 3*m*t*t*p2[0] + t*t*t*p3[0],
                    m*m*m*p0[1] + 3*m*m*t*p1[1] + 3*m*t*t*p2[1] + t*t*t*p3[1]))
    return out

def line(p0, p1, n=32):
    return [(p0[0] + (p1[0]-p0[0])*i/n, p0[1] + (p1[1]-p0[1])*i/n) for i in range(n+1)]

def catmull(points, n=18, tension=0.5):
    """A smooth spline through points (tangent-continuous), sampled."""
    pts = []
    P = [points[0]] + list(points) + [points[-1]]
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i-1], P[i], P[i+1], P[i+2]
        c1 = (p1[0] + (p2[0]-p0[0]) * tension / 3, p1[1] + (p2[1]-p0[1]) * tension / 3)
        c2 = (p2[0] - (p3[0]-p1[0]) * tension / 3, p2[1] - (p3[1]-p1[1]) * tension / 3)
        seg = bez(p1, c1, c2, p2, n)
        pts.extend(seg if i == 1 else seg[1:])
    return pts

def ellipse(cx, cy, rx, ry, a0, a1, n=90, k=2.15):
    out = []
    for i in range(n + 1):
        a = a0 + (a1 - a0) * i / n
        c, s = math.cos(a), math.sin(a)
        out.append((cx + rx * math.copysign(abs(c) ** (2/k), c), cy + ry * math.copysign(abs(s) ** (2/k), s)))
    return out

def tangents(pts):
    t = []
    for i in range(len(pts)):
        a = pts[max(0, i-1)]; b = pts[min(len(pts)-1, i+1)]
        dx, dy = b[0]-a[0], b[1]-a[1]; L = math.hypot(dx, dy) or 1.0
        t.append((dx/L, dy/L))
    return t

# ---------------------------------------------------------------- the pen
class Pen:
    def __init__(self, stem, contrast, stress_deg, power=1.15):
        self.stem = stem; self.hair = stem * (1 - contrast)
        self.stress = math.radians(stress_deg); self.power = power
    def th(self, tan):
        phi = math.atan2(tan[1], tan[0])
        m = abs(math.sin(phi - self.stress)) ** self.power
        return self.hair + (self.stem - self.hair) * m

def outline(pts, pen, profile=None, cut0=None, cut1=None):
    """Offset a centerline by the pen's thickness. profile(t) multiplies.
    cut0/cut1: shear the end faces (radians from the normal) for a pen-angle
    cut instead of a square end."""
    tans = tangents(pts); n = len(pts) - 1
    L, R = [], []
    for i, (p, tn) in enumerate(zip(pts, tans)):
        th = pen.th(tn) * (profile(i / n) if profile else 1.0)
        nx, ny = -tn[1], tn[0]
        L.append((p[0] + nx*th/2, p[1] + ny*th/2)); R.append((p[0] - nx*th/2, p[1] - ny*th/2))
    if cut0 is not None:  # shift the start face: left side forward, right side back
        tn = tans[0]; th = pen.th(tn) * (profile(0.0) if profile else 1.0)
        d = math.tan(cut0) * th / 2
        L[0] = (L[0][0] + tn[0]*d, L[0][1] + tn[1]*d); R[0] = (R[0][0] - tn[0]*d, R[0][1] - tn[1]*d)
    if cut1 is not None:
        tn = tans[-1]; th = pen.th(tn) * (profile(1.0) if profile else 1.0)
        d = math.tan(cut1) * th / 2
        L[-1] = (L[-1][0] - tn[0]*d, L[-1][1] - tn[1]*d); R[-1] = (R[-1][0] + tn[0]*d, R[-1][1] + tn[1]*d)
    return L + R[::-1]

def taper_in(amount=0.45, span=0.35):
    """Thin at t=0 (the join), full by t=span."""
    def f(t):
        if t >= span: return 1.0
        u = t / span
        return amount + (1 - amount) * (3*u*u - 2*u*u*u)
    return f

def taper_out(amount=0.45, span=0.35):
    g = taper_in(amount, span)
    return lambda t: g(1 - t)

def entasis(amount):
    return lambda t: 1.0 + amount * (2*t - 1) ** 2

def flare_end(amount=0.3, span=0.25):
    """Swell toward t=1: the humanist terminal thickens before the cut."""
    def f(t):
        if t <= 1 - span: return 1.0
        u = (t - (1 - span)) / span
        return 1.0 + amount * (3*u*u - 2*u*u*u)
    return f

def compose(*fs):
    return lambda t: math.prod(f(t) for f in fs)

# ---------------------------------------------------------------- serifs
def bracket_wedge(P, d, nrm, th, length, depth, side, drop=0.0, n=10, fillet=0.55):
    """Bracketed wedge at a stem end P (d = outward unit direction, nrm = unit
    normal). The serif sticks out on `side` (+/-1 along nrm). The outer edge
    runs from the apex B (a little below the end, `drop`) back to the stem
    along a concave fillet, so the serif grows out of the stem instead of
    being pinned to it."""
    A = (P[0] + side*nrm[0]*th/2, P[1] + side*nrm[1]*th/2)          # stem corner at the end
    B = (A[0] + side*nrm[0]*length - d[0]*drop, A[1] + side*nrm[1]*length - d[1]*drop)  # apex
    C = (A[0] - d[0]*depth, A[1] - d[1]*depth)                        # down the stem edge
    # fillet from C to B, concave (control point pulled toward A)
    ctrl = (A[0]*fillet + C[0]*(1-fillet) - d[0]*depth*0.05, A[1]*fillet + C[1]*(1-fillet))
    fil = [((1-t)**2*C[0] + 2*(1-t)*t*ctrl[0] + t*t*B[0], (1-t)**2*C[1] + 2*(1-t)*t*ctrl[1] + t*t*B[1]) for t in [i/n for i in range(n+1)]]
    inner = (C[0] - side*nrm[0]*th*0.5, C[1] - side*nrm[1]*th*0.5)
    innerA = (A[0] - side*nrm[0]*th*0.5, A[1] - side*nrm[1]*th*0.5)
    return [inner] + fil + [A, innerA]

def blob(P, r, n=32):
    return [(P[0] + r*math.cos(2*math.pi*i/n), P[1] + r*math.sin(2*math.pi*i/n)) for i in range(n)]

# ---------------------------------------------------------------- context
def ctx(p):
    s = p["stem"]
    c = dict(xh=p["xh"], asc=p["asc"], desc=p["desc"], s=s, wf=p["width"],
             pen=Pen(s, p["contrast"], p["stress"], p.get("power", 1.15)),
             ent=entasis(p["flare"]), wl=p["wedge_len"] * s, wd=p["wedge_depth"] * s,
             over=12, cut=math.radians(p.get("cut_deg", 12)), k=p["bowl_k"],
             fit=p.get("fit", 1.0), nw=p.get("n_width", 400) * p["width"] + (s - 110) * 0.9,
             drop=p.get("serif_drop", 0.18) * s, serif=p.get("serif_style", "wedge"),
             arch=p.get("arch_start", 0.58), fillet=p.get("fillet", 0.55),
             naive_o=p.get("naive_o", False), raw=p.get("raw_joins", False),
             s_spine=p.get("s_spine", 0.0), s_floor=p.get("s_floor", 0.0), s_two=p.get("s_two", False),
             e_bar_overlap=p.get("e_bar_overlap", 0.45), e_join_fill=p.get("e_join_fill", False),
             trap_depth=p.get("trap_depth", 0.55))
    c["over"] = p.get("overshoot", 12)
    return c

def stem(c, P, x, y0, y1, top="wedge", foot="both", top_side=1, flare=True):
    """A vertical stem from y0 up to y1. top: 'wedge' | 'cut' | None.
    foot: 'both' | 'left' | 'right' | None."""
    pts = line((x, y0), (x, y1), 36)
    prof = c["ent"] if flare else (lambda t: 1.0)
    if c["serif"] == "flare" and flare:
        # Albertus-style: the stem itself trumpets at the ends it would have
        # seriffed, and no wedge polygon is drawn.
        amt = c["wl"] / max(c["s"], 1) * 1.6
        top_f = flare_end(amt, 0.3) if top == "wedge" else (lambda t: 1.0)
        foot_f = (lambda t: flare_end(amt * 0.8, 0.3)(1 - t)) if foot else (lambda t: 1.0)
        prof = compose(prof, top_f, foot_f)
    P.append(outline(pts, c["pen"], prof, cut1=(c["cut"] if top == "cut" else None)))
    th = c["pen"].th((0, 1))
    if c["serif"] == "flare":
        return
    # top serif: normal (-1,0) points LEFT, so side +1 is the left of the stem
    if top == "wedge" and c["wl"] > 0:
        P.append(bracket_wedge((x, y1), (0, 1), (-1, 0), th * prof(1.0), c["wl"], c["wd"], top_side, drop=c["drop"], fillet=c["fillet"]))
    # foot: normal (1,0) points RIGHT, so side -1 is left, +1 right
    if foot and c["wl"] > 0:
        sides = {"both": (-1, 1), "left": (-1,), "right": (1,)}[foot]
        for sd in sides:
            P.append(bracket_wedge((x, y0), (0, -1), (1, 0), th * prof(0.0), c["wl"] * 0.85, c["wd"], sd, drop=c["drop"] * 0.6, fillet=c["fillet"]))

def curve(c, P, pts, profile=None, cut1=None, cut0=None):
    P.append(outline(pts, c["pen"], profile, cut0=cut0, cut1=cut1))

def terminal(c, P, pts, kind):
    """Ends of hooks and arms: 'cut' (pen-angle shear, done in outline),
    'drop' (a small teardrop that the stroke swells into)."""
    # 'drop' is retired: a ball terminal belongs to a different face. Ends
    # flare (see flare_end) and take the pen-angle cut in outline().
    return

# ---------------------------------------------------------------- glyphs
def _bowl(c, P, cx, rx, taper_at=None):
    """A full bowl centered at cx, x-height tall with overshoot. Two arcs that
    overlap by 20 degrees at each end, each a simple polygon: one closed loop
    self-crosses at its seam and an even-odd fill leaves a notch there."""
    ry = c["xh"] / 2 + c["over"]
    if c["naive_o"]:
        # the first model's o: one loop that crosses itself at the seam and,
        # filled even-odd, leaves the small gap the owner liked. Kept as a
        # choice, not a bug.
        pts = ellipse(cx, c["xh"] / 2, rx, ry, math.radians(80), math.radians(80 + 370), 124, c["k"])
        curve(c, P, pts); return
    for a0 in (80, 260):
        pts = ellipse(cx, c["xh"] / 2, rx, ry, math.radians(a0 - 10), math.radians(a0 + 200), 70, c["k"])
        curve(c, P, pts)

def g_o(c):
    P = []; rx = 226 * c["wf"]; cx = rx
    _bowl(c, P, cx, rx); return P

def g_d(c):
    P = []; rx = 214 * c["wf"]; cx = rx; x = cx + rx - c["s"] * 0.5
    # the bowl departs the stem thin at top and bottom: draw as an arc from the
    # stem's top junction around to its bottom junction with tapers both ends
    a0, a1 = math.radians(24), math.radians(24 + 312)
    pts = ellipse(cx, c["xh"] / 2, rx, c["xh"] / 2 + c["over"], a0, a1, 110, c["k"])
    curve(c, P, pts, compose(taper_in(0.5, 0.18), taper_out(0.5, 0.18)))
    stem(c, P, x, 0, c["asc"], top="wedge", foot="right"); return P

def g_b(c):
    P = []; x = c["s"] * 0.5; rx = 214 * c["wf"]; cx = x + rx - c["s"] * 0.5
    stem(c, P, x, 0, c["asc"], top="wedge", foot="left")
    a0, a1 = math.radians(156), math.radians(156 - 312)
    pts = ellipse(cx, c["xh"] / 2, rx, c["xh"] / 2 + c["over"], a0, a1, 110, c["k"])
    curve(c, P, pts, compose(taper_in(0.5, 0.18), taper_out(0.5, 0.18))); return P

def g_p(c):
    P = []; x = c["s"] * 0.5; rx = 214 * c["wf"]; cx = x + rx - c["s"] * 0.5
    stem(c, P, x, -c["desc"], c["xh"], top="wedge", foot="both")
    a0, a1 = math.radians(156), math.radians(156 - 312)
    pts = ellipse(cx, c["xh"] / 2, rx, c["xh"] / 2 + c["over"], a0, a1, 110, c["k"])
    curve(c, P, pts, compose(taper_in(0.5, 0.18), taper_out(0.5, 0.18))); return P

def g_q(c):
    P = []; rx = 214 * c["wf"]; cx = rx; x = cx + rx - c["s"] * 0.5
    a0, a1 = math.radians(24), math.radians(24 + 312)
    pts = ellipse(cx, c["xh"] / 2, rx, c["xh"] / 2 + c["over"], a0, a1, 110, c["k"])
    curve(c, P, pts, compose(taper_in(0.5, 0.18), taper_out(0.5, 0.18)))
    stem(c, P, x, -c["desc"], c["xh"], top="wedge", foot="right"); return P

def g_c(c):
    P = []; rx = 214 * c["wf"]; cx = rx
    pts = ellipse(cx, c["xh"] / 2, rx, c["xh"] / 2 + c["over"], math.radians(42), math.radians(318), 100, c["k"])
    curve(c, P, pts, compose(flare_end(0.25, 0.12), lambda t: flare_end(0.25, 0.12)(1 - t)), cut1=c["cut"], cut0=c["cut"]); return P

def g_e(c):
    # narrower than the o by 9% and the bar at 0.58: an e drawn on the o's
    # full width reads too big in a word, because its aperture is air that
    # adds to the letter space on its right. The bar OVERLAPS both strokes
    # (owner 2026-09-12: "the crossbar of the e needs to connect more"); the
    # bowl starts at the bar's own height so the two meet in one join.
    P = []; rx = 195 * c["wf"]; cx = rx; ry = c["xh"] / 2 + c["over"]; s = c["s"]
    bar_y = c["xh"] * 0.58
    a_start = math.degrees(math.asin(min(1.0, (bar_y - c["xh"] / 2) / ry)))
    pts = ellipse(cx, c["xh"] / 2, rx, ry, math.radians(a_start), math.radians(318), 100, c["k"])
    curve(c, P, pts, flare_end(0.25, 0.12), cut1=c["cut"])
    ov = c.get("e_bar_overlap", 0.45) * s
    bar = line((cx - rx + s * 0.1, bar_y), (cx + rx + ov, bar_y), 12)
    curve(c, P, bar)
    if c.get("e_join_fill", False):
        # a small pool of ink in each join, the way a pen leaves it
        for jx in (cx - rx + s * 0.35, cx + rx - s * 0.2):
            P.append(blob((jx, bar_y), s * 0.42))
    return P

def g_a(c):
    P = []; xh = c["xh"]; wf = c["wf"]; s = c["s"]; x = 360 * wf
    stem(c, P, x, 0, xh * 0.95, top=None, foot="both")
    # the hood: leaves the stem thin, thickens over the top, ends in a drop
    hood = bez((x, xh * 0.66), (x, xh * 1.06), (x - 250 * wf, xh * 1.12), (x - 300 * wf, xh * 0.78), 40)
    curve(c, P, hood, compose(taper_in(0.45, 0.3), flare_end(0.15, 0.3)), cut1=c["cut"]); terminal(c, P, hood, "drop")
    # the bowl: a tilted loop that leaves the stem at ~0.55 xh and rejoins at the foot
    rx = 165 * wf; ry = xh * 0.29
    bowl = ellipse(x - rx, ry, rx, ry + 4, math.radians(28), math.radians(28 + 320), 90, c["k"])
    curve(c, P, bowl, compose(taper_in(0.55, 0.15), taper_out(0.6, 0.12))); return P

def g_g(c):
    """Single-storey g. The stem starts at 0.42 of the x-height, where the
    bowl's right side is already vertical, so the two do not double up over
    the bowl's upper half (owner 2026-09-12: a less distracting overlap
    area, counterpunch-inspired). A short ear instead of a top wedge."""
    P = []; xh = c["xh"]; wf = c["wf"]; s = c["s"]; desc = c["desc"]
    rx = 205 * wf; cx = rx; x = cx + rx - s * 0.5
    _bowl(c, P, cx, rx)
    stem(c, P, x, -desc * 0.3 - s * 0.5, xh * 0.42, top=None, foot=None, flare=False)
    # no ear: the bowl carries nothing over it (owner 2026-09-12)
    tail = bez((x, -desc * 0.3), (x, -desc * 1.1), (cx - rx * 0.6, -desc * 1.15), (cx - rx * 1.05, -desc * 0.6), 44)
    curve(c, P, tail, compose(taper_in(0.7, 0.15), flare_end(0.3, 0.3)), cut1=c["cut"]); return P

def _arch(c, P, x0, x1, xh, start=None):
    start = c["arch"] if start is None else start
    pts = bez((x0, xh * start), (x0, xh * 1.05), (x1, xh * 1.04), (x1, xh * 0.60), 44)
    curve(c, P, pts, None if c["raw"] else taper_in(0.42, 0.32))

def g_n(c):
    P = []; xh = c["xh"]; x0 = c["s"] / 2; x1 = x0 + c["nw"]
    stem(c, P, x0, 0, xh, top="wedge", foot="both"); _arch(c, P, x0, x1, xh)
    stem(c, P, x1, 0, xh * 0.62, top=None, foot="both"); return P

def g_h(c):
    P = []; xh = c["xh"]; x0 = c["s"] / 2; x1 = x0 + c["nw"]
    stem(c, P, x0, 0, c["asc"], top="wedge", foot="both"); _arch(c, P, x0, x1, xh)
    stem(c, P, x1, 0, xh * 0.62, top=None, foot="both"); return P

def g_m(c):
    P = []; xh = c["xh"]; x0 = c["s"] / 2; x1 = x0 + c["nw"] * 0.88; x2 = x1 + c["nw"] * 0.88
    stem(c, P, x0, 0, xh, top="wedge", foot="both")
    _arch(c, P, x0, x1, xh); stem(c, P, x1, 0, xh * 0.62, top=None, foot=None)
    _arch(c, P, x1, x2, xh); stem(c, P, x2, 0, xh * 0.62, top=None, foot="both"); return P

def g_u(c):
    P = []; xh = c["xh"]; x0 = c["s"] / 2; x1 = x0 + c["nw"]
    stem(c, P, x0, xh * 0.4 - c["s"] * 0.5, xh, top="wedge", foot=None, flare=False)
    # control points below the baseline by 0.55 of the start height, or a
    # cubic between two stems bottoms out a tenth of the way up (it floated 40 units)
    pts = bez((x0, xh * 0.4), (x0, -xh * 0.4 * 0.55 - c["over"]), (x1, -xh * 0.42 * 0.55 - c["over"]), (x1, xh * 0.42), 44)
    curve(c, P, pts, taper_out(0.42, 0.3))
    stem(c, P, x1, 0, xh, top="wedge", foot="right"); return P

def g_i(c):
    P = []; x = c["s"] / 2; stem(c, P, x, 0, c["xh"], top="wedge", foot="both")
    P.append(blob((x, c["xh"] + 118 + c["s"] * 0.3), c["s"] * 0.5)); return P

def g_l(c):
    P = []; x = c["s"] / 2; stem(c, P, x, 0, c["asc"], top="wedge", foot="both"); return P

def g_j(c):
    P = []; xh = c["xh"]; s = c["s"]; desc = c["desc"]; wf = c["wf"]; r = 165 * wf; x = 120 * wf + s / 2
    stem(c, P, x, -desc + r * 0.2 - s * 0.5, xh, top="wedge", foot=None, flare=False)
    tail = bez((x, -desc + r * 0.2), (x, -desc - r * 0.5), (x - r * 0.55, -desc - r * 0.7), (x - r * 1.05, -desc - r * 0.25), 40)
    curve(c, P, tail, flare_end(0.3, 0.35), cut1=c["cut"])
    P.append(blob((x, xh + 118 + s * 0.3), s * 0.5)); return P

def g_f(c):
    P = []; xh = c["xh"]; s = c["s"]; asc = c["asc"]; wf = c["wf"]; r = 150 * wf; x = 110 * wf + s / 2
    stem(c, P, x, 0, asc - r + s * 0.5, top=None, foot="both", flare=False)
    hook = bez((x, asc - r), (x, asc + 10), (x + r * 0.9, asc + 10), (x + r * 1.25, asc - r * 0.5), 40)
    curve(c, P, hook, flare_end(0.15, 0.3), cut1=c["cut"])
    curve(c, P, line((x - 105 * wf, xh), (x + 150 * wf, xh), 12)); return P

def g_t(c):
    P = []; xh = c["xh"]; s = c["s"]; wf = c["wf"]; r = 135 * wf; x = 100 * wf + s / 2
    stem(c, P, x, r * 0.85 - s * 0.5, xh + 120, top="cut", foot=None, flare=False)
    tail = bez((x, r * 0.85), (x, -c["over"] * 0.5), (x + r * 0.8, -c["over"] * 0.5), (x + r * 1.45, r * 0.6), 36)
    curve(c, P, tail, flare_end(0.3, 0.35), cut1=c["cut"])
    curve(c, P, line((x - 100 * wf, xh), (x + 150 * wf, xh), 12)); return P

def g_r(c):
    P = []; xh = c["xh"]; wf = c["wf"]; x = c["s"] / 2
    stem(c, P, x, 0, xh, top="wedge", foot="both")
    arm = bez((x, xh * 0.6), (x, xh * 1.0), (x + 120 * wf, xh * 1.05), (x + 205 * wf, xh * 0.9), 36)
    curve(c, P, arm, compose(taper_in(0.42, 0.35), flare_end(0.18, 0.3)), cut1=c["cut"]); return P

def _diag(c, P, p0, p1, serif0=None, serif1=None, thin=1.0):
    pts = line(p0, p1, 30)
    prof = lambda t: thin
    curve(c, P, pts, prof)
    tn = tangents(pts)
    if c["wl"] <= 0: return
    if serif0:
        d = (-tn[0][0], -tn[0][1]); nrm = (-d[1], d[0]); th = c["pen"].th(tn[0]) * thin
        P.append(bracket_wedge(pts[0], d, nrm, th, c["wl"] * 0.9, c["wd"] * 0.9, serif0, drop=c["drop"]))
    if serif1:
        d = tn[-1]; nrm = (-d[1], d[0]); th = c["pen"].th(tn[-1]) * thin
        P.append(bracket_wedge(pts[-1], d, nrm, th, c["wl"] * 0.9, c["wd"] * 0.9, serif1, drop=c["drop"]))

def g_k(c):
    P = []; xh = c["xh"]; wf = c["wf"]; s = c["s"]; x = s / 2
    stem(c, P, x, 0, c["asc"], top="wedge", foot="both")
    _diag(c, P, (x + 360 * wf, xh * 0.97), (x + s * 0.2, xh * 0.42), serif0=1, thin=0.78)
    _diag(c, P, (x + 150 * wf, xh * 0.56), (x + 380 * wf, 0), serif1=-1); return P

def g_v(c):
    P = []; xh = c["xh"]; wf = c["wf"]; s = c["s"]; w = 440 * wf
    _diag(c, P, (s * 0.4, xh), (w / 2, 0), serif0=1)
    _diag(c, P, (w - s * 0.4, xh), (w / 2, 0), serif0=-1, thin=0.72); return P

def g_w(c):
    P = []; xh = c["xh"]; wf = c["wf"]; s = c["s"]; w = 680 * wf
    _diag(c, P, (s * 0.4, xh), (w * 0.27, 0), serif0=1)
    _diag(c, P, (w * 0.5, xh * 0.96), (w * 0.27, 0), thin=0.72)
    _diag(c, P, (w * 0.5, xh * 0.96), (w * 0.73, 0))
    _diag(c, P, (w - s * 0.4, xh), (w * 0.73, 0), serif0=-1, thin=0.72); return P

def g_x(c):
    P = []; xh = c["xh"]; wf = c["wf"]; s = c["s"]; w = 430 * wf
    _diag(c, P, (s * 0.4, xh), (w - s * 0.4, 0), serif0=1, serif1=1)
    _diag(c, P, (w - s * 0.4, xh), (s * 0.4, 0), serif0=-1, serif1=-1, thin=0.72); return P

def g_y(c):
    P = []; xh = c["xh"]; wf = c["wf"]; s = c["s"]; desc = c["desc"]; w = 440 * wf
    _diag(c, P, (s * 0.4, xh), (w / 2, 0), serif0=1)
    tail = bez((w - s * 0.4, xh), (w * 0.52, -desc * 0.55), (w * 0.44, -desc * 1.08), (w * 0.02, -desc * 0.95), 44)
    curve(c, P, tail, compose(lambda t: 0.72 + 0.28 * min(1, t * 2), flare_end(0.3, 0.3)), cut1=c["cut"])
    if c["wl"] > 0:
        tn = tangents(tail)[0]; d = (-tn[0], -tn[1]); nrm = (-d[1], d[0])
        P.append(bracket_wedge(tail[0], d, nrm, c["pen"].th(tn) * 0.72, c["wl"] * 0.9, c["wd"] * 0.9, -1, drop=c["drop"]))
    return P

def g_z(c):
    P = []; xh = c["xh"]; wf = c["wf"]; s = c["s"]; w = 400 * wf
    curve(c, P, line((0, xh), (w, xh), 12), cut1=c["cut"])
    zd = line((w - s * 0.15, xh), (s * 0.15, 0), 30)
    tz = tangents(zd)[0]
    curve(c, P, zd, lambda t: c["s"] / c["pen"].th(tz))  # thick, whatever the nib says
    curve(c, P, line((0, 0), (w, 0), 12), cut1=c["cut"])
    th = max(c["pen"].th((1, 0)), s * 0.55)
    if c["wl"] > 0:
        P.append(bracket_wedge((0, xh), (-1, 0), (0, -1), th, c["wl"] * 0.9, c["wd"] * 0.9, -1, drop=0))
        P.append(bracket_wedge((w, 0), (1, 0), (0, -1), th, c["wl"] * 0.9, c["wd"] * 0.9, -1, drop=0))
    return P

def g_s(c):
    """One smooth spine. The middle of it runs near the nib angle, so the
    pen alone makes it the thinnest stroke of the letter and any cut breaks
    it; a humanist s carries its weight IN the spine, so the middle is
    forced toward stem weight (`s_spine`, 0 = the pen's own, 1 = full stem),
    the way the z's diagonal is. `s_floor` keeps the whole letter above a
    fraction of the stem. `s_two` draws it as two overlapping strokes."""
    P = []; xh = c["xh"]; wf = c["wf"]; w = 370 * wf; o = c["over"]; st = c["s"]
    spine_w = c.get("s_spine", 0.0); floor = c.get("s_floor", 0.0)
    pts_ctrl = [(w * 0.93, xh * 0.80), (w * 0.62, xh + o * 0.9), (w * 0.20, xh * 0.86), (w * 0.22, xh * 0.60),
                (w * 0.78, xh * 0.42), (w * 0.82, xh * 0.16), (w * 0.42, -o * 0.9), (w * 0.06, xh * 0.19)]
    if c.get("s_two", False):
        top = catmull(pts_ctrl[:5], 16, 0.55); bot = catmull(pts_ctrl[3:], 16, 0.55)
        for seg, first in ((top, True), (bot, False)):
            tn = tangents(seg); n = len(seg) - 1
            def prof(t, tn=tn, n=n, first=first):
                i = min(n, int(round(t * n))); th = c["pen"].th(tn[i])
                mid = 1.0 - min(1.0, abs((t if first else 1 - t) - 0.85) / 0.3)
                want = th * (1 - mid) + st * spine_w * mid
                return max(want, floor * st) / th
            curve(c, P, seg, compose(prof, flare_end(0.25, 0.12) if first else (lambda t: 1.0)), cut1=c["cut"] if first else None, cut0=None if first else c["cut"])
        return P
    spine = catmull(pts_ctrl, 16, 0.55)
    tn = tangents(spine); n = len(spine) - 1
    def prof(t):
        i = min(n, int(round(t * n))); th = c["pen"].th(tn[i])
        mid = 1.0 - min(1.0, abs(t - 0.5) / 0.28)      # 1 at the middle, 0 by the ends
        want = th if spine_w <= 0 else th * (1 - mid) + st * spine_w * mid
        want = max(want, floor * st)
        return want / th * flare_end(0.25, 0.12)(t) * flare_end(0.25, 0.12)(1 - t)
    curve(c, P, spine, prof, cut1=c["cut"], cut0=c["cut"]); return P

def g_H(c):
    """The one capital the test string needs. Cap height 0.94 of the
    ascender (humanist caps sit under the ascenders); bracketed wedges both
    sides at top and foot; the bar a hair above center."""
    P = []; s = c["s"]; capH = c["asc"] * 0.94; x0 = s / 2; x1 = x0 + c["nw"] * 1.25
    for x in (x0, x1):
        pts = line((x, 0), (x, capH), 36)
        P.append(outline(pts, c["pen"], c["ent"]))
        th = c["pen"].th((0, 1))
        if c["wl"] > 0 and c["serif"] == "wedge":
            for sd in (1, -1):
                P.append(bracket_wedge((x, capH), (0, 1), (-1, 0), th * c["ent"](1.0), c["wl"] * 0.8, c["wd"], sd, drop=c["drop"], fillet=c["fillet"]))
                P.append(bracket_wedge((x, 0), (0, -1), (1, 0), th * c["ent"](0.0), c["wl"] * 0.8, c["wd"], sd, drop=c["drop"] * 0.6, fillet=c["fillet"]))
    curve(c, P, line((x0, capH * 0.52), (x1, capH * 0.52), 12))
    return P

def g_period(c):
    return [blob((c["s"] * 0.55, c["s"] * 0.55), c["s"] * 0.55)]

def g_comma(c):
    s = c["s"]; x = s * 0.55
    P = [blob((x, s * 0.55), s * 0.55)]
    tail = bez((x + s * 0.1, s * 0.2), (x + s * 0.1, -s * 0.5), (x - s * 0.3, -s * 0.9), (x - s * 0.6, -s * 1.2), 20)
    P.append(outline(tail, c["pen"], lambda t: 0.9 - 0.6 * t)); return P

def g_hyphen(c):
    return [outline(line((0, c["xh"] * 0.48), (240 * c["wf"], c["xh"] * 0.48), 8), c["pen"])]

GLYPHS = {'H': g_H, 'a': g_a, 'b': g_b, 'c': g_c, 'd': g_d, 'e': g_e, 'f': g_f, 'g': g_g, 'h': g_h, 'i': g_i,
          'j': g_j, 'k': g_k, 'l': g_l, 'm': g_m, 'n': g_n, 'o': g_o, 'p': g_p, 'q': g_q, 'r': g_r,
          's': g_s, 't': g_t, 'u': g_u, 'v': g_v, 'w': g_w, 'x': g_x, 'y': g_y, 'z': g_z,
          '.': g_period, ',': g_comma, '-': g_hyphen}

SIDES = {
    'H': ('straight', 'straight'), 'a': ('round', 'straight'), 'b': ('straight', 'round'), 'c': ('round', 'open'),
    'd': ('round', 'straight'), 'e': ('round', 'open'), 'f': ('straight', 'open'),
    'g': ('round', 'straight'), 'h': ('straight', 'straight'), 'i': ('straight', 'straight'),
    'j': ('straight', 'straight'), 'k': ('straight', 'diag'), 'l': ('straight', 'straight'),
    'm': ('straight', 'straight'), 'n': ('straight', 'straight'), 'o': ('round', 'round'),
    'p': ('straight', 'round'), 'q': ('round', 'straight'), 'r': ('straight', 'open'),
    's': ('round', 'round'), 't': ('straight', 'open'), 'u': ('straight', 'straight'),
    'v': ('diag', 'diag'), 'w': ('diag', 'diag'), 'x': ('diag', 'diag'), 'y': ('diag', 'diag'),
    'z': ('straight', 'straight'), '.': ('punct', 'punct'), ',': ('punct', 'punct'), '-': ('punct', 'punct'),
}
SIDE_FRACTION = {'straight': 1.0, 'round': 0.72, 'open': 0.6, 'diag': 0.45, 'punct': 0.5}

def n_counter(c): return c["nw"] - c["s"]
def bearing(c, side): return n_counter(c) / 2.0 * SIDE_FRACTION[side] * c["fit"]

def layout(p, text):
    c = ctx(p); polys = []; x = 0.0; prev = None
    for ch in text:
        if ch == ' ':
            x += n_counter(c) * 2.2; prev = None; continue
        fn = GLYPHS.get(ch) or GLYPHS.get(ch.lower())
        if not fn: continue
        gp = fn(c)
        # Fit on the x-height band: a j's tail or an f's hook must not set the
        # bearing of the stem the eye actually spaces against.
        band = [px for poly in gp for (px, py) in poly if -c["over"] <= py <= c["xh"] + c["over"]]
        xs = band or [px for poly in gp for (px, _) in poly]
        l, r = min(xs), max(xs)
        allx = [px for poly in gp for (px, _) in poly]
        # ...but the glyph's own ink still starts where it starts
        ink_l = min(allx)
        lt, rt = SIDES.get(ch) or SIDES[ch.lower()]
        if prev is not None: x += bearing(c, prev) + bearing(c, lt)
        polys.extend([[(px - l + x, py) for (px, py) in poly] for poly in gp])
        x += r - l; prev = rt
    if p.get("slant"):
        sh = math.tan(math.radians(p["slant"]))
        polys = [[(px + py * sh, py) for (px, py) in poly] for poly in polys]
    return polys, x

def wrap(p, text, max_units):
    words = text.split(' '); lines, cur = [], ''
    for w in words:
        t = (cur + ' ' + w).strip()
        if layout(p, t)[1] <= max_units or not cur: cur = t
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines
