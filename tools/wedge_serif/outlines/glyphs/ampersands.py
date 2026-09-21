"""Ten florid ampersands for Albo (owner, 2026-09-13: "make ten more florid
and poetic ampersands"), each drawn as an Albo glyph: the same pen for the
diagonals, spurs and arms (`pen_widths`, floored at the hair), the ruled
bowl profile `PR.BOWL` for every loop and bowl (`bowl_widths`), the stem S
and the cap height, the wedge family on every free terminal (the diagonal
wedge on a spur's foot and an arm's tip, the stem wedge on a stem or an arm
that stands up, the foot wedge on a terminal that runs down, the C/c beak
on an epsilon's upper terminal), and every join a real union.
Every dimension is a multiple of a `pen.py` name (S, C, XH, ASC, DESC, WL,
WD, OVER, the pen's widths) so the drawings move with the variable axes.

Registered as VARIANTS = [(name, fn), ...]; each fn has the signature and
return of `marks.g_ampersand` (c -> shapely geometry) and NONE of them is
registered as '&' -- the shipping & stays `marks.g_ampersand` until the
owner picks. `outlines.cmp.ampersands` builds each into its own TTF.

Two construction rules learned on the first pass, kept here because they
are silent: a bracket wedge's polygon runs `depth` back along a STRAIGHT
edge, so any wedge on a curving stroke gets a straight run of that depth
first (`straight_tail` / `straight_head`), or a sliver floats in the air
beside the terminal; and a closed loop drawn by `ring_from` folds its
counter wherever the outer's radius is under the stroke's width, so the
teardrops take a superellipse top whose radius clears it.
"""
import math, os
import shapely.affinity as aff
from .. import geom, pen
from .. import primitives as PR
from ..geom import line, catmull, superellipse, cubic
from ..primitives import stroke, pen_widths, bowl_widths, widths, wedge, end_wedge, diagonal, bar, beak, ring, stem, dot
from ..pen import S, XH, ASC, DESC, OVER, TH_V, TH_H, HAIR, CUT, BOWL_K, WL, WD, DROP

def CAP(c): return c["cap"]

# ---------------------------------------------------------------- helpers
def ob():
    """Centerline overshoot for a bowl-profile top or bottom: the INK's edge
    lands OVER past the line (negative: the centerline sits inside)."""
    return OVER - PR.bowl_hair() / 2

def spine(pts, tension=0.5):
    """A resampled Catmull-Rom spine, so the width function's index and the
    stroke's sample agree (the half_bowl trap in NOTES.md)."""
    return geom.resample(catmull(pts, tension=tension))

def norm(pts, w, H, o):
    """(a, b) fractions of the width and height -> units; b of 1.0 lands the
    centerline at H + o, b of 0.0 at -o, so the ink's edge overshoots the
    line by OVER."""
    out = []
    for a, b in pts:
        y = H + o if b >= 0.999 else (-o if b <= 0.001 else H * b)
        out.append((w * a, y))
    return out

def mixw(center, blend, profile=None, floor=HAIR):
    """The width along a spine that is part bowl, part pen stroke: blend(t)
    0 = the bowl profile (PR.BOWL), 1 = the pen at that tangent; times the
    declared profile, never under the hair."""
    tans = geom.tangents(center); n = len(center) - 1
    bf = blend if callable(blend) else (lambda t: blend)
    def f(t):
        i = min(n, int(round(t * n))); tn = tans[i]; b = bf(t)
        w = PR.bowl_th(tn) * (1 - b) + pen.PEN.th(tn) * b
        if profile: w *= profile(t)
        return max(w, floor)
    return f

def pw(p0, p1, mult=1.0):
    """The pen's width for a straight stroke p0 -> p1 (the diagonals' rule)."""
    tn = geom.tangents(line(p0, p1))[0]; th = pen.th_t(tn)
    if S > 84.0: th = min(th, S * 0.93)   # round 272: the diagonals' cap, see diagonals.DIAG_CAP
    return th * mult

def spur(foot, top, taper=0.35, mult=1.0):
    """The garalde &'s thick down-right spur, drawn FOOT-FIRST as the A's
    right leg is: the pen's width at its angle, the diagonal wedge on the
    outer (right) side of the foot, thinning into `top`, which the caller
    buries inside the loop's stroke."""
    w = pw(foot, top, mult)
    return diagonal(foot, top, widths([(0.0, w), (0.72, w), (1.0, w * (1 - taper))]), serif0=1)

def straight_tail(pts, length):
    """Append a straight run of `length` along the spine's final tangent, so
    a wedge's bracket sits on a real edge."""
    tn = geom.tangents(pts)[-1]; P = pts[-1]
    return pts + line(P, (P[0] + tn[0] * length, P[1] + tn[1] * length))[1:]

def straight_head(pts, length):
    """Prepend a straight run of `length` back along the spine's first tangent."""
    tn = geom.tangents(pts)[0]; P = pts[0]
    return line((P[0] - tn[0] * length, P[1] - tn[1] * length), P)[:-1] + pts

def stand_up(pts, rise, lean=0.06):
    """The arm's end: bend the last stretch to vertical and run `rise` up
    (the last WD units straight), for a stem-top wedge."""
    P = pts[-1]; tn = geom.tangents(pts)[-1]; xe = P[0] + rise * lean * 4
    mid = cubic(P, (P[0] + tn[0] * rise * 0.3, P[1] + tn[1] * rise * 0.3), (xe, P[1] + rise * 0.30), (xe, P[1] + rise * 0.4))
    top = line(mid[-1], (xe, mid[-1][1] + rise * 0.6))
    return geom.resample(pts + mid[1:] + top[1:])

def top_wedge(center, w_end, side=-1, scale=1.0):
    """A stem-top wedge on a spine that ENDS VERTICAL (its last WD x scale
    units run straight up): side -1 points left (the l's), +1 right."""
    P = center[-1]; A = (P[0] + side * w_end / 2, P[1])
    return wedge(A, (0, 1), (side, 0), WL * scale, WD * scale, DROP * scale)

def foot_wedge(P, w_end, side=-1, scale=0.85):
    """A stem-foot wedge at a spine's START, which runs straight UP from P
    for WD x scale: side -1 points left."""
    A = (P[0] + side * w_end / 2, P[1])
    return wedge(A, (0, -1), (side, 0), WL * scale, WD * scale, DROP * 0.6 * scale)

def teardrop_outer(cx, cy, rx, ry, Pt, flare=0.06):
    """A closed teardrop outline, ccw: a superellipse top (radius rx above
    the stroke's width, so `ring_from` does not fold), two sides bowing
    down to the point Pt."""
    top = superellipse(cx, cy, rx, ry, 0.0, math.pi, 2.0)
    L = (cx - rx, cy); R = (cx + rx, cy); dy = (cy - Pt[1])
    left = cubic(L, (L[0] - rx * flare, cy - dy * 0.45), (Pt[0] - rx * 0.45, Pt[1] + dy * 0.30), Pt)
    right = cubic(Pt, (Pt[0] + rx * 0.55, Pt[1] + dy * 0.30), (R[0] + rx * flare, cy - dy * 0.45), R)
    return geom.resample(top + left[1:] + right[1:])[:-1]

def teardrop_loop(outer):
    """`ring_from` on the BOWL profile: it offsets by the 26-degree pen when
    given no widths, which thins a loop's upper left to the pen's hair."""
    o2 = geom.resample(outer + [outer[0]])[:-1]; tans = geom.tangents(o2, closed=True); n = len(o2)
    wf = lambda t: max(PR.bowl_th(tans[min(n - 1, int(round(t * n)))]), HAIR)
    return PR.ring_from(o2, widths_fn=wf, smooth_w=3)

def arm_flag(center, w_end, scale=0.9):
    """Van den Keere's arm terminal, on a straight run: the family's wedge
    with its apex straight RIGHT of the arm's end corner and its bracket
    down the arm's own right edge."""
    P = center[-1]; d = geom.tangents(center)[-1]; A = (P[0] + d[1] * w_end / 2, P[1] - d[0] * w_end / 2)
    return wedge(A, d, (1, 0), WL * scale, WD * scale, 0.0)

def garalde(pts, w, H, o, blend, arm='flag', arm_scale=0.9):
    """The closed-loop garalde body: one spine starting on the spur's line
    (its start buried in the spur), up-left through the crossing, round the
    top loop, back down through the crossing as the thin diagonal, round
    the lower bowl and up into the arm. arm = 'flag' ends the arm on a
    straight run with the right-pointing flag; 'stand' bends the arm up to
    vertical under a right stem wedge.
    Returns (body, tip, spine)."""
    sp = spine(norm(pts, w, H, o))
    if arm == 'stand': sp = stand_up(sp, WD * 1.5)
    else: sp = geom.resample(straight_tail(sp, WD * arm_scale))
    wf = mixw(sp, blend); body = stroke(sp, wf, pieces=True)
    tip = top_wedge(sp, wf(1.0), +1, 0.9) if arm == 'stand' else arm_flag(sp, wf(1.0), arm_scale)
    return body, tip, sp

# the garalde spine's width plan: pen on the spur stub, bowl round the top
# loop, pen down the thin diagonal, bowl round the lower bowl, pen up the arm
GARALDE_BLEND = widths([(0.0, 1.0), (0.12, 0.0), (0.36, 0.0), (0.42, 1.0), (0.50, 1.0), (0.56, 0.0), (0.80, 0.0), (0.88, 1.0)])

# ---------------------------------------------------------------- 1. E-t, Caslon italic
def amp_et_caslon(c):
    """The classical E-t ligature of the italic Caslon kind: a lowercase-
    sized epsilon (two bowls joined at the waist, the 3's construction
    mirrored, the upper terminal the c's beak) whose bottom sweeps right and
    rises into a TALL italic t -- a sheared stem to the cap height with the
    family's top wedge -- crossed by the t's bar just under the epsilon's
    top."""
    C = CAP(c); o = ob(); hb = PR.bowl_hair()
    ew = 3.4 * S; Eh = XH + 0.4 * S; yw = 0.50 * Eh          # the epsilon: width, height, waist
    xs = ew + 0.8 * S; slant = math.tan(math.radians(11))     # the t's stem base and its lean
    xst = lambda y: xs + y * slant
    top = spine([(0.90 * ew, 0.84 * Eh), (0.68 * ew, Eh - hb / 2), (0.34 * ew, Eh - hb / 2 - 3), (0.09 * ew, 0.78 * Eh),
                 (0.06 * ew, 0.64 * Eh), (0.24 * ew, yw + 3), (0.54 * ew, yw - 2), (0.68 * ew, yw - 6)])
    tw = bowl_widths(top, widths([(0.0, 1.25), (0.12, 1.0), (0.9, 1.0), (1.0, 0.8)]), floor=HAIR)
    t_body = stroke(top, tw, cut0=math.radians(-28))
    lip = beak(top, tw(0.0), True, -28.0, lip=(0.35, 0.6))
    low = spine([(0.62 * ew, yw + 4), (0.30 * ew, yw - 0.04 * Eh), (0.07 * ew, 0.34 * Eh), (0.05 * ew, 0.16 * Eh),
                 (0.30 * ew, -o), (0.62 * ew, 2), (0.86 * ew, 0.06 * Eh), (ew + 0.2 * S, 0.12 * Eh), (xst(0.32 * Eh), 0.32 * Eh)])
    lw = mixw(low, widths([(0.72, 0.0), (0.86, 1.0)]), widths([(0.0, 0.8), (0.1, 1.0)]))
    l_body = stroke(low, lw)
    st = stem(xs, 0.12 * Eh, C, top='left', foot=None, ent_span=(0, C))
    st = aff.skew(st, xs=11, origin=(xs, 0))
    yb = 0.86 * Eh
    b = bar(xst(yb) - 1.1 * S, xst(yb) + 1.5 * S, yb, TH_H)
    return geom.ink([t_body, lip, l_body, st, b])

# ---------------------------------------------------------------- 2. Garamond roman
def amp_garamond(c):
    """The Garamond roman &: the top loop OPEN -- its stroke starts free at
    the left as a short upright with the foot wedge, rises, rounds the top,
    and runs down-left as the pen's thin diagonal into the lower bowl, which
    sweeps up into the arm; the arm stands up into the stem's right wedge;
    the spur a separate thick diagonal, foot-first, with the A's outer
    wedge."""
    C = CAP(c); w = 7.7 * S; o = ob()
    head = 0.85 * WD; P0 = (0.21 * w, 0.66 * C)
    pts = [(P0[0], P0[1] + head), (0.14 * w, 0.86 * C), (0.28 * w, C + o), (0.45 * w, 0.90 * C), (0.48 * w, 0.75 * C), (0.37 * w, 0.60 * C),
           (0.21 * w, 0.47 * C), (0.07 * w, 0.34 * C), (0.05 * w, 0.17 * C), (0.21 * w, -o), (0.42 * w, 0.02 * C), (0.60 * w, 0.20 * C),
           (0.70 * w, 0.36 * C), (0.76 * w, 0.50 * C)]
    sp = spine(pts); sp = geom.resample(line(P0, sp[0])[:-1] + sp)    # the straight upright under the foot wedge
    sp = stand_up(sp, WD * 1.5)
    blend = widths([(0.28, 0.0), (0.35, 1.0), (0.45, 1.0), (0.53, 0.0), (0.74, 0.0), (0.82, 1.0)])
    wf = mixw(sp, blend); body = stroke(sp, wf, pieces=True)
    start = foot_wedge(sp[0], wf(0.0), -1, 0.85)
    tip = top_wedge(sp, wf(1.0), +1, 0.9)
    X = (0.46 * w, 0.72 * C)
    leg = spur((0.95 * w, 0.0), (X[0] - 0.06 * w, X[1] + 0.06 * C))
    return geom.ink([body, start, tip, leg])

# ---------------------------------------------------------------- 3. full ring below, small open loop above
def amp_ringed(c):
    """A looped &: the lower bowl is a FULL RING on the o's construction
    (the bowl profile, the family's k), the top loop small and open -- it
    leaves the ring's upper right, rounds the top, comes down the left and
    curls back toward the ring, ending in the diagonal wedge; the arm and
    the spur both spring from the ring's right side and cross outside it."""
    C = CAP(c); w = 7.4 * S
    ry = 0.26 * C + OVER; cy = ry - OVER; rx = 0.29 * w; cx = rx + 0.02 * w
    bowl, outer, inner = ring(cx, cy, rx, ry, k=BOWL_K)
    hook = spine([(cx + 0.58 * rx, cy + 0.78 * ry), (cx + 0.72 * rx, cy + 1.45 * ry), (cx + 0.40 * rx, C + ob() - 0.02 * C), (cx - 0.20 * rx, C + ob()),
                  (cx - 0.68 * rx, 0.88 * C), (cx - 0.62 * rx, 0.78 * C)])
    hook = geom.resample(straight_tail(hook, 0.6 * WD))
    hw = bowl_widths(hook, widths([(0.0, 0.85), (0.15, 1.0), (1.0, 0.95)]), floor=HAIR)
    hk = stroke(hook, hw); hk_tip = end_wedge(hook, hw(1.0), False, -1, 0.6)
    arm = spine([(cx + 0.78 * rx, cy), (cx + 1.25 * rx, cy + 0.42 * ry), (cx + 1.55 * rx, cy + 1.15 * ry)])   # routed right of the hook's rise: 0.6 S of air between them
    arm = geom.resample(straight_tail(arm, 0.9 * WD))
    aw = pen_widths(arm, widths([(0.0, 0.9), (0.25, 1.0)]), floor=HAIR)
    am = stroke(arm, aw); am_tip = arm_flag(arm, aw(1.0))
    leg = spur((0.97 * w, 0.0), (cx + 0.60 * rx, cy + 1.08 * ry))   # springs from the hook's rise, clear of the ring's crotch
    return geom.ink([bowl, hk, hk_tip, am, am_tip, leg])

# ---------------------------------------------------------------- 4. swash tail under the baseline
def amp_swash(c):
    """A garalde & whose spur does not stop at the baseline: it dives to
    three quarters of the descender and sweeps back LEFT under the whole
    glyph as a long flourish, ending in the diagonal wedge; the top loop
    closed, the arm on the outer diagonal wedge."""
    C = CAP(c); w = 7.6 * S; o = ob()
    X = (0.43, 0.62)
    body, tip, sp = garalde([(0.50, 0.53), X, (0.25, 0.75), (0.11, 0.86), (0.27, 1.0), (0.48, 0.90), (0.50, 0.74), (0.40, 0.60),
                             (0.22, 0.46), (0.07, 0.32), (0.06, 0.15), (0.24, 0.0), (0.46, 0.02), (0.62, 0.20), (0.72, 0.38)], w, C, o, GARALDE_BLEND)
    tail = spine([(X[0] * w - 0.03 * w, X[1] * C + 0.05 * C), (0.62 * w, 0.36 * C), (0.84 * w, 0.06 * C), (0.92 * w, -0.34 * DESC),
                  (0.80 * w, -0.68 * DESC), (0.52 * w, -0.80 * DESC), (0.28 * w, -0.76 * DESC), (0.14 * w, -0.68 * DESC)])
    tail = geom.resample(straight_tail(tail, 0.6 * WD))
    tw = pen_widths(tail, widths([(0.0, 0.7), (0.10, 1.0), (0.55, 1.0), (1.0, 0.85)]), floor=0.5 * S)   # the K arm's kind of floor: the sweep crosses the pen's thinnest direction
    tl = stroke(tail, tw); tl_tip = end_wedge(tail, tw(1.0), False, -1, 0.6)
    return geom.ink([body, tip, tl, tl_tip])

# ---------------------------------------------------------------- 5. cursive E with a crossing t-bar
def amp_cursive_et(c):
    """The Garamond-italic Et: a cap-height cursive E in two bowls, the
    upper bowl's tongue running straight on as the E's middle arm -- which
    IS the t's crossbar, crossing a short upright t stem at the right and
    ending in the bar wedge; the lower bowl sweeps under and rises into that
    stem, whose top takes the t's pen cut."""
    C = CAP(c); o = ob()
    ew = 3.6 * S; yw = 0.52 * C; xs = ew + 0.9 * S
    up = spine([(0.88 * ew, 0.86 * C), (0.62 * ew, C + o), (0.30 * ew, C + o - 2), (0.08 * ew, 0.84 * C), (0.05 * ew, 0.70 * C),
                (0.18 * ew, yw + 4), (0.44 * ew, yw)])
    uw = bowl_widths(up, widths([(0.0, 1.25), (0.12, 1.0), (1.0, 1.0)]), floor=HAIR)
    u_body = stroke(up, uw, cut0=math.radians(-28)); lip = beak(up, uw(0.0), True, -28.0, lip=(0.4, 0.7))
    b = bar(0.36 * ew, xs + 1.5 * S, yw, TH_H, wedges=[('right', 1)])
    low = spine([(0.50 * ew, yw - 2), (0.22 * ew, 0.44 * C), (0.06 * ew, 0.32 * C), (0.05 * ew, 0.15 * C), (0.30 * ew, -o),
                 (0.62 * ew, 2), (0.86 * ew, 0.05 * C), (xs - 0.55 * S, 0.13 * C), (xs, 0.30 * C)])
    lw = mixw(low, widths([(0.74, 0.0), (0.88, 1.0)]), widths([(0.0, 0.8), (0.1, 1.0)]))
    l_body = stroke(low, lw)
    st = stem(xs, 0.12 * C, 0.76 * C, top=None, foot=None, ent_span=(0, 0.76 * C), cut_top=CUT)
    return geom.ink([u_body, lip, b, l_body, st])

# ---------------------------------------------------------------- 6. teardrop top loop
def amp_teardrop(c):
    """The top loop as a TEARDROP, its counter closed and round at the top
    and pointed at the crossing: the loop is a designed closed outer on the
    bowl profile (`ring_from`), and the thin diagonal, the lower bowl, the
    arm and the spur all leave from its point."""
    C = CAP(c); w = 7.6 * S; o = ob()
    Pt = (0.38 * w, 0.54 * C)
    outer = teardrop_outer(0.29 * w, 0.80 * C, 0.215 * w, C + OVER - 0.80 * C, Pt)
    loop, lo, li = teardrop_loop(outer)
    body_pts = spine([(Pt[0] + 0.02 * w, Pt[1] + 0.04 * C), (0.24 * w, 0.44 * C), (0.09 * w, 0.31 * C), (0.05 * w, 0.15 * C), (0.22 * w, -o),
                      (0.45 * w, 0.02 * C), (0.62 * w, 0.20 * C), (0.72 * w, 0.38 * C)])
    body_pts = geom.resample(straight_tail(body_pts, 0.9 * WD))
    blend = widths([(0.0, 1.0), (0.18, 1.0), (0.28, 0.0), (0.72, 0.0), (0.82, 1.0)])
    wf = mixw(body_pts, blend); body = stroke(body_pts, wf)
    tip = arm_flag(body_pts, wf(1.0))
    leg = spur((0.95 * w, 0.0), (Pt[0] + 0.01 * w, Pt[1] + 0.05 * C))
    return geom.ink([loop, body, tip, leg])

# ---------------------------------------------------------------- 7. tall and narrow
def amp_narrow(c):
    """A condensed garalde &, 0.7 of the shipping width at the full cap
    height: the loops drawn tall so both counters keep 0.6 S, the spur
    foot-first with the outer wedge, the arm standing up into the right
    stem wedge so the aperture beside the spur stays open."""
    C = CAP(c); w = 5.4 * S; o = ob()
    X = (0.40, 0.60)
    body, tip, sp = garalde([(0.52, 0.49), X, (0.22, 0.74), (0.10, 0.86), (0.26, 1.0), (0.50, 0.89), (0.54, 0.73), (0.42, 0.58),
                             (0.22, 0.44), (0.07, 0.30), (0.06, 0.14), (0.24, 0.0), (0.48, 0.02), (0.64, 0.20), (0.72, 0.34)], w, C, o, GARALDE_BLEND, arm='stand')
    leg = spur((0.96 * w, 0.0), (X[0] * w - 0.05 * w, X[1] * C + 0.05 * C))
    return geom.ink([body, tip, leg])

# ---------------------------------------------------------------- 8. wide and low
def amp_wide_low(c):
    """A lowercase-sized &: x-height plus a little, wide, the top loop
    drawn big enough for its counter at this height, the arm standing up
    into the right stem wedge, the spur foot-first with the outer wedge."""
    H = XH * 1.12; w = 8.0 * S; o = ob()
    X = (0.40, 0.50)
    body, tip, sp = garalde([(0.50, 0.38), X, (0.22, 0.70), (0.09, 0.86), (0.25, 1.0), (0.46, 0.90), (0.50, 0.72), (0.38, 0.52),
                             (0.20, 0.38), (0.06, 0.26), (0.07, 0.12), (0.28, 0.0), (0.54, 0.02), (0.70, 0.16), (0.78, 0.28)], w, H, o, GARALDE_BLEND, arm='stand')
    leg = spur((0.97 * w, 0.0), (X[0] * w - 0.05 * w, X[1] * H + 0.06 * H))
    return geom.ink([body, tip, leg])

# ---------------------------------------------------------------- 9. spur ending in an upward wedge flick
def amp_flick(c):
    """A garalde & whose spur, instead of a foot, turns UP at the baseline
    into a short flick that ends in the family's wedge -- no ball. The turn
    is routed round enough for the pen's width through it."""
    C = CAP(c); w = 7.7 * S; o = ob()
    X = (0.42, 0.62)
    body, tip, sp = garalde([(0.50, 0.53), X, (0.24, 0.75), (0.10, 0.86), (0.26, 1.0), (0.47, 0.90), (0.49, 0.74), (0.39, 0.60),
                             (0.21, 0.46), (0.06, 0.32), (0.06, 0.15), (0.24, 0.0), (0.46, 0.02), (0.62, 0.20), (0.72, 0.38)], w, C, o, GARALDE_BLEND)
    fl = spine([(X[0] * w - 0.04 * w, X[1] * C + 0.05 * C), (0.60 * w, 0.40 * C), (0.80 * w, 0.14 * C), (0.88 * w, 0.02 * C),
                (0.95 * w, 0.03 * C), (0.98 * w, 0.12 * C)])
    fl = geom.resample(fl + line(fl[-1], (fl[-1][0], fl[-1][1] + 0.16 * C))[1:])
    fw = pen_widths(fl, widths([(0.0, 0.7), (0.10, 1.0), (0.80, 1.0), (1.0, 0.95)]), floor=HAIR)
    f_body = stroke(fl, fw); f_tip = top_wedge(fl, fw(1.0), +1, 0.8)
    return geom.ink([body, tip, f_body, f_tip])

# ---------------------------------------------------------------- 10. poetic: the arm aspires to the ascender
def amp_aspiring(c):
    """My own: the & as a written figure whose arm does not stop at the cap
    line -- it rises in one long curve to the ASCENDER, straightens to a
    stem and takes the l's top wedge; the top loop a teardrop, the lower
    bowl round, the spur foot-first with the outer wedge."""
    C = CAP(c); w = 7.5 * S; o = ob()
    Pt = (0.37 * w, 0.55 * C)
    outer = teardrop_outer(0.28 * w, 0.80 * C, 0.21 * w, C + OVER - 0.80 * C, Pt)
    loop, lo, li = teardrop_loop(outer)
    body_pts = spine([(Pt[0] + 0.02 * w, Pt[1] + 0.04 * C), (0.23 * w, 0.44 * C), (0.08 * w, 0.31 * C), (0.05 * w, 0.15 * C), (0.22 * w, -o),
                      (0.46 * w, 0.02 * C), (0.64 * w, 0.20 * C), (0.74 * w, 0.44 * C), (0.79 * w, 0.68 * C), (0.81 * w, ASC - 0.26 * C)])
    body_pts = geom.resample(body_pts + line(body_pts[-1], (body_pts[-1][0], ASC))[1:])
    blend = widths([(0.0, 1.0), (0.16, 1.0), (0.26, 0.0), (0.62, 0.0), (0.72, 1.0)])
    wf = mixw(body_pts, blend); body = stroke(body_pts, wf)
    tip = top_wedge(body_pts, wf(1.0), -1)
    leg = spur((0.94 * w, 0.0), (Pt[0] + 0.01 * w, Pt[1] + 0.05 * C))
    return geom.ink([loop, body, tip, leg])

VARIANTS = [
    ('et_caslon', amp_et_caslon),
    ('garamond', amp_garamond),
    ('ringed', amp_ringed),
    ('swash', amp_swash),
    ('cursive_et', amp_cursive_et),
    ('teardrop', amp_teardrop),
    ('narrow', amp_narrow),
    ('wide_low', amp_wide_low),
    ('flick', amp_flick),
    ('aspiring', amp_aspiring),
]

# ================================================================ generation II
# Owner, on round 67's ten (2026-09-13): "make variants inspired by current
# and teardrop." So one parametric drawing, `bred`, whose dials span the two
# parents -- the shipping & (`marks.g_ampersand`: the spur running on as the
# loop's thin left side, the arm's right-pointing flag, the hooked foot) and
# round 67's `amp_teardrop` (a designed closed loop, round at the top,
# pointed at the crossing, a straight spur with the A's foot wedge) -- and
# ten settings of it. The midpoint of every dial is the default; each
# variant names only the dials it moved off it.
#
# Two rules of this drawing, kept because they are silent. The spur and the
# loop's left side are COLLINEAR in both parents (the ring's left side runs
# at 42 degrees from the point, the spur at 45), so "the loop stops short"
# cannot open the loop -- it breaks the spur's line -- and the half-closed
# top is instead a HOOK: the loop's left side, coming down from the top,
# curls inward and stops above the crossing, the aperture between its end
# and the spur. And the thin diagonal is the pen at its own angle (0.31 S at
# 41 degrees) with `THIN` as its floor: at a crossing steeper than 35
# degrees the pen runs into its stress angle and would vanish (4 units at
# the owner's 0.95 contrast).

# ROUND 272 -- THE AMPERSAND'S WIDTH ABOVE STEM 84. Owner 2026-09-19, on the
# roman 700 and 900: *"ampersand is way too wide."* The letter's whole
# skeleton is drawn in CUR_W, which is 8.76 stems, so it grew with the
# weight like a stroke: 629 units of ink at the 400, 1,004 at the 700, 1,245
# at the 900, against an H that grew from 744 to 780. Above 84 the skeleton's
# stem is 66.9 x (S / 66.9) ^ 0.17 -- the 400's skeleton widened a tenth at
# the 700 and a seventh at the 900, which is what a bold ampersand does --
# and the strokes stay on S. At and under 84 the 400 is byte-identical.
_SW = S if S <= 84.0 else 66.9 * (S / 66.9) ** 0.17
CUR_W = 8.76 * _SW * pen.WIDTH   # the shipping &'s 736, in the pen's units, on the width axis
THIN = 0.30 * S                # the thin diagonal's floor: what the pen gives at 41 degrees

def t_of(sp, P):
    """The t (0..1) of the resampled spine's sample nearest P: how the width
    plan's keys are placed on a spine whose lengths move with the dials."""
    n = len(sp) - 1; i = min(range(len(sp)), key=lambda k: math.dist(sp[k], P)); return i / n

def loop_path(cx, cy, rx, ry, Pt, flare=0.06):
    """The loop's CENTERLINE as an open path from the point, ccw: up the
    left side, over the top, down the right side, back to the point --
    `teardrop_outer` rotated to start at Pt and reversed."""
    o = teardrop_outer(cx, cy, rx, ry, Pt, flare)
    i = min(range(len(o)), key=lambda k: math.dist(o[k], Pt))
    rot = o[i:] + o[:i] + [o[i]]
    return rot[::-1]

def lerp_pts(a, b, t):
    return [(p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t) for p, q in zip(a, b)]

def egg_loop_path(cx, top_y, Pt, rx, pinch=0.85, power=3.0):
    """ROUND 233 -- THE LOOP AS AN EGG, for the options the owner asked for on
    2026-09-18 (R54 upper loop, R55 right side / terminal, R56 lower-left:
    *"give me options that fix the unattractive lumpy and droopiness"*).

    `loop_path` is `teardrop_outer` turned: a superellipse over the top and
    two CUBICS down to the point, each leaving the equator with its first
    handle pulled OUTWARD by `flare` -- so the loop's sides bulge below the
    equator before they turn in, and the lower left (R56) droops where the
    cubic and the spur's width blend meet. This is one smooth closed curve
    instead: an ellipse whose half-width shrinks smoothly from `rx` at the
    top to `rx x (1 - pinch)` at the bottom -- by `((1 - cos) / 2) ** power`,
    so at power 3 the equator still has 0.9 of the width and the narrowing
    happens in the last third (power 1 gave straight sides from above the
    equator down, a triangle with a round cap) -- and whose bottom is sheared
    onto the point `Pt`. The curvature changes continuously all the way
    round and the only sharp place is the crossing itself. Same direction as
    `loop_path` (from the point up the LEFT side, over the top, down the
    right, back to the point) and the same top (`top_y`), so it drops into
    `bred` where `loop_path` was."""
    ry = (top_y - Pt[1]) / 2.0; cy = Pt[1] + ry; N = 240; pts = []
    for i in range(N + 1):
        th = math.pi + 2 * math.pi * i / N                    # bottom -> left -> top -> right -> bottom
        c, s = math.cos(th), math.sin(th)
        f = 1.0 - pinch * ((1.0 - c) / 2.0) ** power          # 1 at the top, 1 - pinch at the bottom
        pts.append((cx + rx * f * s + (Pt[0] - cx) * (1.0 - c) / 2.0, cy + ry * c))
    pts[0] = Pt; pts[-1] = Pt
    return geom.resample(pts)

def arm_beak(center, w_end):
    """The C's beak transposed to a RISING arm: the end face sheared to the
    vertical (stroke's cut1 = minus the arm's angle: the upper-left corner
    advances, the lower-right retreats) and a short lip, 0.35 x 0.6 of the
    family, hanging from the face's lower corner into the air under the
    arm. `primitives.beak` assumes the C's end convention (its lip sits on
    the corner stroke() ADVANCES at a start), which on an arm's end leaves
    the lip floating off the face -- so the corner is computed here from
    the same shear stroke() applies. Returns (cut1, lip)."""
    d = geom.tangents(center)[-1]; P = center[-1]; alpha = math.atan2(d[1], d[0])
    cut1 = -alpha; nr = (d[1], -d[0])                       # the arm's lower (right-of-travel) normal
    shift = math.tan(cut1) * w_end / 2                      # stroke() moves R[-1] by +tn * shift at the end
    A = (P[0] + nr[0] * w_end / 2 + d[0] * shift, P[1] + nr[1] * w_end / 2 + d[1] * shift)
    return cut1, wedge(A, d, nr, WL * 0.35, WD * 0.6, 0.0)

# the lower bowl between the two constructions: the current's (a straight
# left side, a flat bottom, the right side rising steeply into the arm) and
# the o's (round, wider, its right side a real curve the arm leaves from)
BOWL_CUR = [(0.06, 0.17), (0.18, 0.03), (0.38, 0.0), (0.53, 0.10), (0.60, 0.26)]
BOWL_O = [(0.05, 0.12), (0.15, 0.01), (0.35, 0.0), (0.55, 0.04), (0.65, 0.17)]

def bred(c, top='half', loop=1.0, point=(0.36, 0.555), cross=41.0, arm=0.58, arm_end='flag',
         spur_w=1.0, spur_x=0.97, spur_foot='hook', bowl=0.5, width=1.0, opening=0.58, hook_end='cut',
         loop_shape='tear', egg_pinch=0.85, egg_power=3.0, bowl_shape='points', bowl_k=(1.0, 1.0), bowl_bottom=0.35):
    """One & from the dials.
    loop_shape (round 233): 'tear' = `loop_path`, the teardrop every entry
         in VARIANTS2 was built on; 'egg' = `egg_loop_path`, one smooth
         curve pinched to the point by `egg_pinch` -- for the 'open' and the
         'closed' tops.
    arm_end 'pencut' (round 233): the arm ends in the family's pen cut and
         nothing hangs from it -- 'cut' in the 'open' branch was a plain
         square face and is left as it was, since VARIANTS2 was built on it.
    top: 'open' = the current's spiral (the spur runs on as the loop's left
         side, one stroke, the pen's width there); 'half' = the loop's left
         side comes down from the top as its own stroke and stops above the
         crossing, curling in (a hook, `opening` of the side removed, its
         end a diagonal wedge or a pen cut); 'closed' = the teardrop's ring.
    loop: the loop's width, x the parents' 0.22 w.  point: the crossing, in
         (w, C) fractions.  cross: the thin diagonal's angle below horizontal.
    arm: the arm's end height in C; arm_end: 'flag' (the current's
         right-pointing wedge), 'beak' (the C's), 'cut' (the pen cut), 'up'
         (a small upturn into the right stem wedge).
    spur_w: x the pen; spur_x: the foot's x in w (its angle); spur_foot:
         'hook' (the current's curled foot, tapered in), 'wedge' (the
         teardrop's straight spur with the A's foot wedge), 'plain' (straight,
         the pen cut).  bowl: 0 = the current's lower bowl, 1 = the o's.
    width: x the current's advance-width proportion."""
    C = CAP(c); w = CUR_W * width; o = ob(); hb = PR.bowl_hair()
    # ROUND 272 -- THE STROKES ABOVE STEM 84. With the skeleton held to the
    # 400's width (CUR_W above) and the strokes on the bold's pen, the upper
    # loop closed to a slit at the 900 and the crossing became a mass; the
    # strokes lighten by sqrt(84/S) -- 0.85 at the 700, 0.75 at the 900 -- as
    # the eszett's do (round 267). At and under 84 the factor is 1.
    _lt = (84.0 / S) ** 0.5 if S > 84.0 else 1.0
    _L = lambda f: (lambda t, _f=f: _f(t) * _lt)
    X = (point[0] * w, point[1] * C)
    # ---- the loop: outer top on C + OVER, widest rx, centre a little left of the point
    rx = 0.22 * w * loop; ry = 0.20 * C + OVER; cy = C + OVER - ry; cx = X[0] - 0.06 * w
    # ---- the thin diagonal and the lower bowl, then the arm
    xD = 0.065 * w; yD = X[1] - (X[0] - xD) * math.tan(math.radians(cross))
    D = (xD, yD); M = ((X[0] + xD) / 2, (X[1] + yD) / 2)
    bp = [(a * w, (b * C if b > 0.001 else -o)) for a, b in lerp_pts(BOWL_CUR, BOWL_O, bowl)]
    B5 = bp[-1]; ang = math.radians(53.0)
    yE = arm * C; xE = B5[0] + (yE - B5[1]) / math.tan(ang); E = (xE, yE)
    tail = 0.9 * WD if arm_end in ('flag', 'beak') else 0.35 * WD   # the flag's and the beak's brackets run down a STRAIGHT edge
    A1 = (E[0] - tail * math.cos(ang), E[1] - tail * math.sin(ang))
    # ROUND 256, owner 2026-09-19: *"smooth out lower loop of ampersand to be
    # use fewer and more graceful curves."* 'points' is the lower bowl as it
    # was: a Catmull-Rom through the five BOWL_* points between the diagonal's
    # end D and the arm's foot A1. 'cubic' replaces the five with ONE cubic
    # from D to A1: its first handle continues the diagonal's direction, its
    # last arrives along the arm's, so the bowl is tangent-continuous with
    # both and has no interior knots; the two handle lengths are bowl_k x the
    # chord, scaled together until the curve's lowest point is on -o (the
    # overshoot the points reached). 'three' keeps the spline but through
    # three points only -- D, the bottom (bowl_bottom x w, -o) and A1.
    if bowl_shape in ('cubic', 'three'):
        head = catmull([X, M, D], tension=0.5)
        if bowl_shape == 'three':
            bowl_path = catmull([M, D, (bowl_bottom * w, -o), A1, E], tension=0.5)
            i0 = min(range(len(bowl_path)), key=lambda k: math.dist(bowl_path[k], D)); i1 = min(range(len(bowl_path)), key=lambda k: math.dist(bowl_path[k], A1))
            bowl_path = bowl_path[i0:i1 + 1]
        else:
            # the bowl DEPARTS D heading down (the five points went straight
            # down from D before turning right: D (48, 201) -> (44, 115) on the
            # shipped &), not along the diagonal's 41 degrees -- a handle on
            # the diagonal's own direction points back out to the left and the
            # solver then has nothing to pull the curve down with.
            d_in = (-0.05, -1.0); Ld = math.hypot(*d_in); d_in = (d_in[0] / Ld, d_in[1] / Ld)
            d_out = (math.cos(ang), math.sin(ang)); chord = math.dist(D, A1)
            def _bowl(scale):
                L1, L2 = bowl_k[0] * chord * scale * 0.5, bowl_k[1] * chord * scale * 0.5
                return cubic(D, (D[0] + d_in[0] * L1, D[1] + d_in[1] * L1), (A1[0] - d_out[0] * L2, A1[1] - d_out[1] * L2), A1)
            lo_, hi_ = 0.05, 6.0           # bisect on the handle scale: longer handles, lower curve
            for _ in range(30):
                scale = (lo_ + hi_) / 2; ymin = min(q[1] for q in _bowl(scale))
                if abs(ymin + o) < 0.25: break
                if ymin > -o: lo_ = scale
                else: hi_ = scale
            bowl_path = _bowl(scale)
        body = geom.resample(head + bowl_path[1:] + line(A1, E)[1:])
        B5 = bowl_path[int(len(bowl_path) * 0.82)]   # the width plan's "arm from here" key sits on the curve where the fifth point used to
    else:
        body_pts = [X, M, D] + bp + [A1]
        body = geom.resample(catmull(body_pts, tension=0.5) + line(A1, E)[1:])
    if arm_end == 'up': body = stand_up(body, WD * 1.2)   # a SMALL upturn: the last WD x 1.2 bent up (0.6 of it straight, past the 0.7 wedge's depth) under the stem wedge
    tD, tB5 = t_of(body, D), t_of(body, B5)
    beak_cut, beak_lip = arm_beak(body, 0.0)[0], None       # the shear alone here; the lip needs the arm's final width
    # ---- the spur: from the foot up-left through the crossing, buried past it
    if spur_foot == 'hook':
        sp_pts = [((spur_x - d) * w, b * C) for d, b in ((0.0, 0.10), (0.13, 0.02), (0.27, 0.07), (0.34, 0.17))]
    else:
        sp_pts = [(spur_x * w, 0.0)]
    parts = []; spur_end = (X[0] - 0.02 * w, X[1] + 0.03 * C)    # buried in the loop's point / the diagonal's start
    end_cut = beak_cut if arm_end == 'beak' else (CUT if arm_end == 'pencut' else None)
    if top == 'open':
        # ONE spine: spur -> X -> up the loop's left -> top -> down its right -> X -> diagonal -> bowl -> arm
        if loop_shape == 'egg': lp = egg_loop_path(cx, cy + ry - hb / 2, X, rx - 0.45 * S, egg_pinch, egg_power)
        else: lp = loop_path(cx, cy, rx - 0.45 * S, ry - hb / 2, X)
        spur_sp = catmull(sp_pts + [X], tension=0.5) if spur_foot == 'hook' else line(sp_pts[0], X)
        sp = geom.resample(spur_sp[:-1] + lp + body[1:])
        tX1 = t_of(sp, X); tL = t_of(sp, lp[len(lp) // 4]); tR = t_of(sp, lp[3 * len(lp) // 4]); tX2 = t_of(sp, lp[-1])
        tD2 = t_of(sp, D); tB = t_of(sp, B5)
        blend = widths([(0.0, 1.0), (tX1 - 0.02, 1.0), (tL, 0.0), (tR, 0.0), (tX2 + 0.02, 1.0), (tD2 - 0.02, 1.0), (tD2 + 0.03, 0.0),
                        (tB - 0.02, 0.0), (tB + 0.04, 1.0)])
        prof = widths([(0.0, 0.3 if spur_foot == 'hook' else 1.0), (0.05, 1.0)])
        sw = widths([(0.0, spur_w), (tX1 - 0.03, spur_w), (tX1 + 0.02, 1.0)])
        # the loop's left side (spiral): the pen at its angle, floored at THIN -- the current's thin
        wf = mixw(sp, blend, lambda t: prof(t) * sw(t), floor=THIN * _lt)
        parts.append(stroke(sp, _L(wf), pieces=True, cut0=CUT if spur_foot == 'plain' else None, cut1=end_cut))
        if spur_foot == 'wedge': parts.append(end_wedge(sp, wf(0.0) * _lt, True, +1, 0.9))   # round 272: the wedge seats on the stroke as lightened
        arm_sp, arm_w = sp, wf(1.0)
    else:
        # the spur, its own stroke, thinning into the crossing
        spur_sp = geom.resample(catmull(sp_pts + [spur_end], tension=0.5) if spur_foot == 'hook' else line(sp_pts[0], spur_end))
        prof = widths([(0.0, 0.3 if spur_foot == 'hook' else 1.0), (0.05, 1.0), (0.72, 1.0), (1.0, 0.65)])
        sw = pen_widths(spur_sp, prof, floor=THIN * _lt, scale=spur_w)
        parts.append(stroke(spur_sp, _L(sw), cut0=CUT if spur_foot == 'plain' else None))
        if spur_foot == 'wedge': parts.append(end_wedge(spur_sp, sw(0.0) * _lt, True, +1, 0.9))   # round 272: the wedge seats on the stroke as lightened
        if top == 'closed':
            # the egg runs clockwise like `loop_path`; `ring_from` offsets inward from a ccw outline, so reverse it
            if loop_shape == 'egg': outer = egg_loop_path(cx, cy + ry, X, rx, egg_pinch, egg_power)[:-1][::-1]
            else: outer = teardrop_outer(cx, cy, rx, ry, X)
            lo, _, _ = teardrop_loop(outer); parts.append(lo)
            sp = body
            blend = widths([(0.0, 1.0), (tD - 0.02, 1.0), (tD + 0.03, 0.0), (tB5 - 0.02, 0.0), (tB5 + 0.04, 1.0)])
            wf = mixw(sp, blend, floor=THIN * _lt)
            parts.append(stroke(sp, _L(wf), cut1=end_cut))
        else:   # 'half': the hook + the body as one spine
            # the loop's sides bow out a little more than the ring's, so the
            # hook's free end sits LEFT of the spur's line rather than on it
            lp = loop_path(cx, cy, rx - 0.45 * S, ry - hb / 2, X, flare=0.14)
            # the left side is lp[0 .. iL] (Pt up to L); drop `opening` of it from the point; the free
            # end runs straight for the wedge's bracket (the garamond's foot) or takes the pen cut
            iL = min(range(len(lp)), key=lambda k: lp[k][0]); k = int(round(iL * opening))
            hook = lp[k:]; H = hook[0]
            if hook_end == 'wedge': hook = straight_head(hook, 0.3 * WD)
            sp = geom.resample(hook + body[1:])
            tH = t_of(sp, H); tX2 = t_of(sp, lp[-1]); tD2 = t_of(sp, D); tB = t_of(sp, B5)
            blend = widths([(0.0, 0.0), (tX2 + 0.02, 0.0), (tD2 - 0.02, 1.0), (tD2 + 0.03, 0.0), (tB - 0.02, 0.0), (tB + 0.04, 1.0)])
            wf = mixw(sp, blend, widths([(0.0, 0.92), (tH + 0.03, 1.0)]), floor=THIN * _lt)
            parts.append(stroke(sp, _L(wf), pieces=True, cut0=CUT if hook_end == 'cut' else None, cut1=end_cut))
            if hook_end == 'wedge': parts.append(end_wedge(sp, wf(0.0), True, -1, 0.6))
        arm_sp, arm_w = sp, wf(1.0)
    # ---- the arm's end
    if arm_end == 'flag': parts.append(arm_flag(arm_sp, arm_w, 0.9))
    elif arm_end == 'up': parts.append(top_wedge(arm_sp, arm_w, +1, 0.7))
    elif arm_end == 'beak': parts.append(arm_beak(arm_sp, arm_w)[1])
    return geom.ink(parts)

def _v(**d):
    """A VARIANTS2 entry: `bred` at these dials, the dials kept on the
    function (`fn.dials`) so the proof page prints what moved rather than a
    hand-written list that drifts."""
    fn = lambda c: bred(c, **d); fn.dials = dict(d); return fn

VARIANTS2 = [
    ('teardrop_top', _v(top='closed', point=(0.35, 0.56), cross=39.0, arm=0.64, spur_foot='hook', bowl=0.0)),
    ('current_arm', _v(top='closed', point=(0.38, 0.54), cross=40.0, arm=0.64, spur_x=0.95, spur_foot='wedge', bowl=0.35)),
    ('midpoint', _v()),
    ('mid_light', _v(spur_w=0.8)),
    ('mid_heavy', _v(spur_w=1.2, spur_foot='wedge')),
    ('mid_narrow', _v(width=0.9)),
    ('mid_wide', _v(width=1.1)),
    ('beak', _v(arm=0.50, arm_end='beak', cross=47.0)),
    ('upturn', _v(top='closed', loop=0.88, point=(0.37, 0.60), arm=0.56, arm_end='up', spur_x=0.93, spur_foot='plain')),
    ('round_bowl', _v(top='open', loop=1.1, bowl=1.0, arm_end='cut', arm=0.54)),
]

# ROUND 233 -- THE OWNER'S OPTIONS ON THE SHIPPING &. 2026-09-18, three lines
# on the bump markup (R54 the upper loop, R55 its right side down to the
# crossing, R56 its lower left): *"give me options that fix the unattractive
# lumpy and droopiness."* Read on the outline at 3 px/unit: the loop is
# `teardrop_outer` turned -- a superellipse over the top and two cubics to
# the point, each leaving the equator with a handle pulled OUTWARD (flare
# 0.06) -- so the sides swell below the equator and the lower left sags into
# the crossing, and the width there is `mixw`'s blend from the pen (at the
# spur) to the bowl profile (on the left side), which crosses the THIN floor
# as it goes. `marks.g_ampersand` picks one of these by ALBO_AMP_OPT; 'a' is
# today's drawing, unchanged.
#   b  the SAME & with the loop redrawn as an egg (`egg_loop_path`): one
#      smooth curve, no flare, pinched 0.80 to the point; loop 1.1 -> 1.0
#      (Georgia's loop is 0.48 of the &'s width; this is 0.44)
#   c  as b, tighter and cleaner: loop 0.92, pinch 0.90 (the sides come into
#      the crossing steeper, so nothing hangs at the lower left), and the
#      arm ends in the family's pen cut with no lip (the beak's lip is the
#      notch numbered 212 on his sheet)
#   d  redrawn from GEORGIA in the family's pen: its & measured at 1000 px
#      against its E -- 1.05 cap tall, 0.97 cap wide (Albo's is 1.09), the
#      loop 0.48 of the width and 0.40 cap tall, the crossing at 0.58 cap,
#      the arm rising at ~51 degrees to a flat terminal at 0.63 cap, a
#      straight thick leg from the crossing to a flat foot at the lower
#      right, the bowl round. That is `bred`'s closed teardrop with the
#      egg for its ring, the wedge foot (the A's) on a straight leg, the
#      o's bowl, and the arm on a pen cut.
AMP_OPTIONS = {
    'b': dict(top='open', loop=1.1, bowl=1.0, arm_end='beak', arm=0.54, cross=41.2, loop_shape='egg', egg_pinch=0.85, egg_power=3.0),
    'c': dict(top='open', loop=1.0, bowl=1.0, arm_end='pencut', arm=0.54, cross=41.2, loop_shape='egg', egg_pinch=0.92, egg_power=3.0),
    'd': dict(top='closed', loop=1.1, point=(0.36, 0.58), cross=41.2, arm=0.63, arm_end='pencut', spur_x=0.97,
              spur_foot='wedge', bowl=1.0, loop_shape='egg', egg_pinch=0.6, egg_power=2.0),
    # ROUND 252, owner 2026-09-18: *"ALBO_AMP_OPT d with a b top."* d's body --
    # the crossing, the arm on its pen cut, the straight leg to the wedge foot,
    # the round bowl -- under b's OPEN top: the spur runs on as the loop's left
    # side in one stroke. e takes b's loop whole (its egg, 0.85 / 3.0); f keeps
    # d's own egg (0.6 / 2.0) and opens it only.
    'e': dict(top='open', loop=1.1, point=(0.36, 0.58), cross=41.2, arm=0.63, arm_end='pencut', spur_x=0.97,
              spur_foot='wedge', bowl=1.0, loop_shape='egg', egg_pinch=0.85, egg_power=3.0),
    'f': dict(top='open', loop=1.1, point=(0.36, 0.58), cross=41.2, arm=0.63, arm_end='pencut', spur_x=0.97,
              spur_foot='wedge', bowl=1.0, loop_shape='egg', egg_pinch=0.6, egg_power=2.0),
    # ROUND 256 (owner: "smooth out lower loop of ampersand to be use fewer and
    # more graceful curves. give me options to choose from."): e with its lower
    # bowl redrawn, see `bred` bowl_shape.
    'g': dict(top='open', loop=1.1, point=(0.36, 0.58), cross=41.2, arm=0.63, arm_end='pencut', spur_x=0.97,
              spur_foot='wedge', bowl=1.0, loop_shape='egg', egg_pinch=0.85, egg_power=3.0, bowl_shape='cubic', bowl_k=(1.0, 1.0)),   # ONE cubic, even handles
    'h': dict(top='open', loop=1.1, point=(0.36, 0.58), cross=41.2, arm=0.63, arm_end='pencut', spur_x=0.97,
              spur_foot='wedge', bowl=1.0, loop_shape='egg', egg_pinch=0.85, egg_power=3.0, bowl_shape='cubic', bowl_k=(1.4, 0.8)),   # one cubic, the diagonal's direction carried further: fuller lower left, tighter into the arm
    'i': dict(top='open', loop=1.1, point=(0.36, 0.58), cross=41.2, arm=0.63, arm_end='pencut', spur_x=0.97,
              spur_foot='wedge', bowl=1.0, loop_shape='egg', egg_pinch=0.85, egg_power=3.0, bowl_shape='cubic', bowl_k=(0.8, 1.4)),   # one cubic, the arm's direction carried further: tight under the diagonal, a long sweep up into the arm
    'j': dict(top='open', loop=1.1, point=(0.36, 0.58), cross=41.2, arm=0.63, arm_end='pencut', spur_x=0.97,
              spur_foot='wedge', bowl=1.0, loop_shape='egg', egg_pinch=0.85, egg_power=3.0, bowl_shape='three', bowl_bottom=0.35),     # the spline through three points instead of five
    'k': dict(top='open', loop=1.1, point=(0.36, 0.58), cross=41.2, arm=0.63, arm_end='pencut', spur_x=0.97,
              spur_foot='wedge', bowl=1.0, loop_shape='egg', egg_pinch=0.85, egg_power=3.0, bowl_shape='three', bowl_bottom=0.42),     # three points, the bottom further right: a rounder underside
}



# ============================================================ THE ITALIC et
# OWNER'S BRIEF, queued since 2026-09-15 and recorded at
# docs/wedge-serif-exploration.md:4239 under "Queued, not yet investigated":
#
#     "use a flowing and adorned curved E ampersand for italics."
#
# restated at docs/albo-italic-capitals.md:123 -- *"the owner asked for a
# flowing adorned curved E form for the italic, which is the chancery et, and
# that is a construction question rather than a width one."*
#
# WHAT WAS WRONG. The italic has no ampersand of its own: `marks.AMP_OPT`
# defaults to 'a' under `pen.ITALIC`, which is round 68's `round_bowl` --
# THE ROMAN LETTER, sheared 13 degrees by `build.draw` and nothing else. Set
# beside the Aldine lowercase it is the one roman thing left in the line: a
# ruled diagonal, a teardrop loop and a bowl on `PR.BOWL`, in a word whose
# e t o are drawn from Griffo's 1501 page on a broad nib. A sheared roman is
# what round 115 was written to stop being, one letter at a time.
#
# A "curved E" is the *et* ligature as a chancery hand writes it: the two
# arcs of an E bulging LEFT and meeting at a waist right of centre, with the
# t crossing that waist. It is not a variant of the garalde & -- it is the
# other construction entirely, which is why none of these is a `bred` dial
# set and why `AMP_OPTIONS` was the wrong place to put them.
#
# DRAWN FROM THE REFERENCE SHELF, not invented. `refs/poetica-std-regular.otf`
# (Slimbach's chancery, banked round 116c for exactly this work -- "the
# reference for the queued italic ampersand, the k and r loops, and the swash
# g") carries SIXTY-ONE ampersands, and they fall into four families. Each arm
# below is one of them, measured off Poetica at upm 1000 against its own
# x-height of 394 and read as multiples of it:
#
#   family                      Poetica           height      ink width
#   E + rising t-stroke         alt002 alt003     1.04-1.35   1.13-1.52 xh
#   E + long flat swash         alt012 alt052     1.54        2.26 xh
#   e + upright t ("et")        alt004 alt005     1.62        1.63 xh
#   E + short arm and curl      alt027 alt028     1.04        1.29 xh
#
# EVERY ONE OF THEM IS WIDER THAN IT IS TALL (w/h 1.01 to 1.47), where the
# sheared roman & is 0.89. That is not decoration: the E's two arcs stack
# vertically and everything else in the letter -- the t's rise, the swash, the
# arm -- travels right. An arm here that came out taller than wide would be
# the roman's proportion wearing the chancery's shapes.
#
# HOW THEY ARE DRAWN. On the Aldine nib, not on `pen.PEN` and not on
# `PR.BOWL`: width = thin + (thick - thin) * |sin(direction - phi)| with phi
# 35, which is `aldine.nib` and the pen the o, the c and the e are built on
# (aldine.py: "the o's own"). The formula is repeated here rather than
# imported because `glyphs/__init__` imports `marks` BEFORE `aldine`, and a
# top-level import would invert that order for a two-line function. thick is
# declared at the e's own 0.86 S and the contrast at its arm B's 5:1, so a
# stroke of this & running in a given direction is the same weight as the e's
# running in that direction -- which is the whole point of drawing it on the
# same pen.
#
# ...WITH ONE FLOOR, and it is the measurement that earned this round its
# second cut. At phi 35 every member that travels UP AND RIGHT runs along the
# nib's own edge, so the t's rise, the swash's flat and the arm are all near
# the pen's thin -- 0.86 S / 5 = 11.5 units at the shipping stem. Measured on
# the shipped Italic as horizontal ink runs (5th percentile): o 29, x 22,
# t 26, n 24, s 24, c 18. ELEVEN IS THINNER THAN ANYTHING THE FACE DRAWS, and
# the first cut of these arms duly rendered the crossing stroke as a stray
# hairline that disappears at reading size. ET_FLOOR holds every member at
# 0.30 S, which lands the thin members at 20-26 units measured the same way --
# inside the face's own range and above the italic X's 15-unit hairline, the
# thinnest thing in the family that has to survive printing
# (docs/albo-weight-survey-2026-09-17.md).
#
# Ends TAPER (0.62 of the body over the last 12%) instead of taking a wedge.
# That is the Aldine lowercase's rule and the reason it reads as written --
# "a brush leaves and arrives". A wedge serif on a chancery et would let the
# roman back in by another door.
#
# Everything is a multiple of S, XH or the cap, so these move with the axes
# exactly as the `bred` drawings do. Nothing here is registered as '&':
# `marks.g_ampersand` picks one by ALBO_IT_AMP, and 'a' -- an unset build,
# which is every build that has ever been made -- is today's drawing.
ET_PHI   = float(os.environ.get("ALBO_IT_AMP_PHI", 35.0))     # the nib's angle: the o's, the c's and the e's
ET_THICK = float(os.environ.get("ALBO_IT_AMP_THICK", 0.86))   # x S, across the nib -- ALBO_ALD_E_THICK
ET_CON   = float(os.environ.get("ALBO_IT_AMP_CON", 5.00))     # thick:thin -- ALBO_ALD_CON, arm B
ET_FLOOR = float(os.environ.get("ALBO_IT_AMP_FLOOR", 0.30))   # x S: no member thinner than the face draws
ET_TIP   = float(os.environ.get("ALBO_IT_AMP_TIP", 0.62))     # ALBO_ALD_TIP
ET_TIP_RUN = float(os.environ.get("ALBO_IT_AMP_TIP_RUN", 0.12))
ET_WT    = float(os.environ.get("ALBO_IT_AMP_WT", 1.00))      # one dial over every arm's colour


def et_nib(deg, thick=None, thin=None, phi=None):
    """`aldine.nib`, repeated (see the import note above). A broad pen is
    fullest ACROSS its edge and thinnest ALONG it."""
    thick = (ET_THICK * S) if thick is None else thick
    thin = (thick / ET_CON) if thin is None else thin
    phi = ET_PHI if phi is None else phi
    return thin + (thick - thin) * abs(math.sin(math.radians(deg - phi)))


def et_w(pts, scale=1.0, phi=None, smooth=9, taper=(True, True), tip=None,
         boost=None, thick=None, floor=None):
    """Nib widths along a spine -> a width function of t for `stroke`.

    `boost` is f(t) -> multiplier for a member that wants weight the pen's
    own angle does not give it; `taper` says which ends leave the paper. The
    moving average is `aldine.nib_widths`'s: a stepped width makes a faceted
    counter, and a narrow counter shows every facet. The floor is applied
    BEFORE the taper, so a tip is still a tip."""
    n = len(pts); ws = []
    fl = (ET_FLOOR if floor is None else floor) * S
    for i in range(n):
        a_ = pts[max(0, i - 1)]; b_ = pts[min(n - 1, i + 1)]
        d = math.degrees(math.atan2(b_[1] - a_[1], b_[0] - a_[0]))
        w = et_nib(d, thick=(thick * S if thick else None), phi=phi)
        if boost: w *= boost(i / max(1, n - 1))
        ws.append(max(w, fl) * scale * ET_WT)
    if smooth:
        ws = [sum(ws[max(0, i - smooth):i + smooth + 1]) /
              len(ws[max(0, i - smooth):i + smooth + 1]) for i in range(n)]
    tp = ET_TIP if tip is None else tip
    if tp < 1.0 and ET_TIP_RUN > 0:
        run = ET_TIP_RUN
        for i in range(n):
            t = i / max(1, n - 1); m = 1.0
            if taper[0] and t < run:
                m = min(m, tp + (1 - tp) * (0.5 - 0.5 * math.cos(math.pi * t / run)))
            if taper[1] and t > 1 - run:
                u = (1 - t) / run
                m = min(m, tp + (1 - tp) * (0.5 - 0.5 * math.cos(math.pi * u)))
            ws[i] *= m
    m = n - 1
    return widths([(i / m, w) for i, w in enumerate(ws)])


def et_stroke(keys, scale=1.0, tension=0.5, **kw):
    """A catmull spine through `keys` (absolute units), stroked on the nib."""
    p = catmull(keys, tension=tension)
    return stroke(p, et_w(p, scale=scale, **kw)), p


def _et_frame(H):
    """f=0 is the bottom centerline and f=1 the crown's, so a flat top or
    bottom overshoots the line by OVER exactly as every bowl in the face
    does. `o` is half the nib's width in the horizontal direction."""
    o = 0.5 * et_nib(0.0) - OVER
    return (lambda f: o + f * (H - 2 * o)), o


def _et_curved_E(H, WE, pre=(), waist=(0.42, 0.50), crown_x=0.36,
                 entry=((0.74, 0.75), (0.68, 0.93)), upper=(0.04, 0.74),
                 low=(0.00, 0.25), bot=(0.36, 0.00),
                 exit_=((0.74, 0.10), (0.86, 0.24)),
                 scale=1.0, tension=0.5, **kw):
    """THE CURVED E -- the owner's own words for it -- as ONE pen movement:
    in at the upper right, left over the crown, down the upper flank, right
    through the waist, down the LOWER and fuller flank, round the bottom and
    out to the right. Shared by arms b and c, which differ in what crosses
    it; that is the construction question and this is the part that is not in
    question.

    TWO THINGS MEASURED OFF THE REFERENCE AND NOT GUESSED, both of which the
    first cut of this round got wrong by drawing the shape from the idea of
    an epsilon instead of from the page:

    THE LOWER ARC IS FULLER THAN THE UPPER. It reaches further left (0.00 of
    the width against the upper flank's 0.04) and its bottom carries further
    right than the crown does. An E whose two arcs are the same size reads as
    a 3, and every ampersand on the shelf avoids it the same way.

    AND IT IS WIDE. `WE` runs 0.70-0.75 of the height here. Poetica's chancery
    ampersands are ALL wider than they are tall -- w/h 1.01 to 1.47 over the
    four families -- where the sheared roman & is 0.89, and the first cut of
    this arm came out at 0.60 of the height with counters the pen could very
    nearly close. The width is not decoration: the E's two arcs stack
    vertically while the t, the swash and the arm all travel right, so the
    proportion follows from the construction."""
    Y, _o = _et_frame(H)
    X = lambda f: f * WE
    P = lambda q: (X(q[0]), Y(q[1]))
    keys = [P(q) for q in pre] + [P(entry[0]), P(entry[1]),
            (X(crown_x), Y(1.00)), P(upper), P(waist),
            P(low), P(bot), P(exit_[0]), P(exit_[1])]
    return et_stroke(keys, scale=scale, tension=tension, **kw)


def et_b(c):
    """b -- THE CHANCERY et, COMPACT (Poetica alt002/alt003, ink 1.13-1.52
    x-heights wide over 1.04-1.35 tall). The curved E with the t crossing its
    waist and rising to a flicked tip past the crown's shoulder.

    THE READING-SIZE ARM. It is the narrowest of the four and its only member
    outside the E's own box is the t's rise, so at 13 px it stays one mark
    instead of breaking into two."""
    H = CAP(c) * 0.94; WE = H * 0.70
    Y, _o = _et_frame(H); X = lambda f: f * WE
    # THE TERMINAL'S DIRECTION IS ITS WEIGHT, and that is why two cuts of
    # this loop came out as a blunt stub shutting its own counter. An entry
    # that arrives travelling straight UP is at 86 degrees, which on this nib
    # is 0.78 of the thick; entering at 57, along the pen's own edge, is 0.37
    # of it. The terminal is fine because of where it points, and `tip` only
    # lifts the pen at the very end of it.
    E, _p = _et_curved_E(H, WE, entry=((0.60, 0.79), (0.73, 0.92)), tip=0.42)
    # The t. It starts steep, where the nib is full, and flattens as it rises,
    # so it thins on the way out because of where it is GOING rather than
    # because a taper was declared on it -- and the hand presses through the
    # crossing and lifts, which is `boost`. Without that pressure the member
    # came out at the pen's thin for its whole length and read as a stray
    # flourish laid over an epsilon rather than as the t of an et; that is
    # what the first cut of this arm did.
    # It LEAVES THE BOTTOM ARC, on that stroke's own centreline, rather than
    # clipping the lower-left flank on its way past. Started at the flank the
    # two strokes met at about 20 degrees and the t's entry terminal stood
    # 2.2 units proud of the E's edge -- a HAIR by `cmp_contour_hairs.py`
    # (turn 151.1 deg, arms 2.2/19.4), which is the one thing in this glyph
    # that gate found. Buried on the centreline there is no crotch to leave.
    T, _q = et_stroke([(X(0.26), Y(0.04)), (X(0.44), Y(0.30)),
                       (X(0.74), Y(0.52)), (X(1.06), Y(0.70)),
                       (X(1.26), Y(0.84)), (X(1.34), Y(0.98))],
                      scale=1.04, tension=0.58,
                      boost=lambda t: 1.0 + 0.55 * math.sin(math.pi * min(1.0, t / 0.66)) ** 1.4)
    # A BALL ON THE t's TIP. The rise ends near the pen's thin whatever is
    # done to it, so without a terminal it runs off the page as a hairline --
    # which is what it did for three cuts. Poetica finishes this member with a
    # ball (alt002), and so does Albo's own Aldine r (`aldine.d_ball`), so it
    # is the family's answer and not an import.
    return geom.ink([E, T, dot(X(1.33), Y(0.97), S * 0.27)])


def et_c(c):
    """c -- THE ADORNED et, WITH THE LONG FLAT SWASH (Poetica alt012/alt052,
    ink 2.26 x-heights wide). The same E, drawn a little smaller, with the t's
    exit running out FLAT to the right, dipping, and rising into a curl that
    closes above the x-height; a lifted entry curl over the crown answers it
    at the other end.

    This is "flowing and adorned" taken at its word, and it is the arm for a
    title page or a colophon rather than for running text: at 2.3 x-heights it
    is nearly twice arm b's width, and the swash reaches into whatever follows
    it. The curl is part of the SAME movement as the E -- a chancery hand does
    not lift the pen to add an adornment -- which is why it is `pre` on the E's
    own key list and not a mark drawn beside it."""
    H = CAP(c) * 0.89; WE = H * 0.66
    Y, _o = _et_frame(H); X = lambda f: f * WE
    # THE SWASH IS WHERE THIS ARM'S ORNAMENT LIVES, and two other places
    # were tried first and are recorded because both look plausible written
    # down. A rolled curl over the crown KINKED: a catmull asked to double
    # back inside a stroke's own width has nowhere to put the turn. A lifted
    # entry coming in above the crown line from the upper right read as a
    # SLAB across the top, because it arrives travelling nearly horizontally
    # and adds its length to the crown's. The E keeps arm b's fine inward
    # curl, and everything this arm has to say it says to the right.
    E, _p = _et_curved_E(H, WE, entry=((0.60, 0.79), (0.73, 0.92)),
                         crown_x=0.36, upper=(0.05, 0.74), waist=(0.44, 0.50),
                         low=(0.00, 0.24), bot=(0.38, 0.00),
                         exit_=((0.70, 0.07), (0.80, 0.18)), tip=0.42)
    # The swash leaves from INSIDE the E's lower flank, so the union has no
    # seam to show, crosses the waist, and runs away right.
    SW, _ = et_stroke([(X(0.26), Y(0.34)), (X(0.56), Y(0.50)),
                       (X(0.96), Y(0.55)), (X(1.34), Y(0.44)),
                       (X(1.72), Y(0.51)), (X(1.95), Y(0.75)),
                       (X(1.82), Y(0.92)), (X(1.62), Y(0.83))],
                      scale=1.02, tension=0.5,
                      boost=lambda t: 1.0 + 0.40 * math.sin(math.pi * min(1.0, t / 0.55)) ** 1.4)
    return geom.ink([E, SW])


def et_d(c):
    """d -- THE et WRITTEN OUT (Poetica alt004/alt005/alt026): a round e on
    the left and an upright t on the right, tied by ONE horizontal that is the
    e's bar and the t's crossbar at the same time. The only arm a reader can
    actually spell, and the tallest -- the t stands to the ascender the way
    the Aldine t does.

    The shared bar IS the ligature. An earlier cut drew the e's bar, the t's
    crossbar and a joining stroke as three members, and the letter read as two
    letters with a scratch between them; the references all merge them, and
    merging is also what makes this one glyph rather than a kerned pair."""
    H = CAP(c) * 0.99
    Y, _o = _et_frame(H); U = H
    xh = U * 0.585                       # the e's band, x the whole height
    Ye = lambda f: _o + f * (xh - 2 * _o)
    ew = U * 0.46; Xe = lambda f: f * ew
    # the e: the Aldine e's own movement at this scale -- out of the bar, over
    # the crown, down the left, round the flat wide bottom, and up into a
    # narrow aperture.
    # The arc starts ABOVE the bar, not on it. At Ye(0.64) its terminal ran
    # nearly collinear with the bar for its whole first segment and the pair
    # closed a 169-degree crotch -- a REVERSAL by `cmp_contour_hairs.py`, the
    # only finding in this arm. It is the same trap round 172c solved on the
    # Aldine e itself, where the answer was to let the stub follow the arc's
    # own points; here the members are a bar and an e, so the answer is to
    # give them an angle to cross at.
    EA, _ = et_stroke([(Xe(0.86), Ye(0.76)), (Xe(0.56), Ye(1.00)),
                       (Xe(0.08), Ye(0.72)), (Xe(0.05), Ye(0.28)),
                       (Xe(0.44), Ye(0.00)), (Xe(0.92), Ye(0.22))],
                      tension=0.5)
    # the t's stem: the Aldine head leans in from the left at the top, and the
    # foot kicks right along the baseline (`aldine.hm_exit`'s gesture).
    TS, _ = et_stroke([(U * 0.845, Y(0.99)), (U * 0.745, Y(0.62)),
                       (U * 0.70, Y(0.20)), (U * 0.76, Y(0.02)),
                       (U * 0.94, Y(0.09))], scale=1.06, tension=0.5,
                      tip=0.88)   # the Aldine ascender ends in a flat angled HEAD, not a point
    # the one bar.
    TB, _ = et_stroke([(Xe(0.02), Ye(0.47)), (Xe(0.95), Ye(0.58)),
                       (U * 1.02, Y(0.60))], scale=1.02, tension=0.5,
                      taper=(False, True))
    return geom.ink([EA, TB, TS])


def et_e(c):
    """e -- THE TWO-BOWL E WITH A t OF ITS OWN (Poetica alt027/alt028, ink
    1.29 x-heights wide over 1.04 tall). The other half of the chancery
    family, and the one the first cuts of this round missed entirely: the E's
    lower arc CLOSES INTO A ROUND BOWL and its upper arc closes over it, so
    the left of the letter is two bowls stacked -- and the t on the right is
    not one crossing stroke but TWO members, a crossbar running out nearly
    flat and a stem sweeping down to a kicked foot.

    That is the difference between alt002/alt027 and alt003/alt051, and it is
    what makes this arm read as an ampersand where an open epsilon reads as a
    Greek letter with a flourish on it. It is also the arm that spells `Et`
    most plainly of the three E-forms: the two bowls are the E, the crossbar
    and the stem are the t.

    The bowl is `PR.ring` on the round-305 nib -- the same law as every other
    member here, stated as (thick, thin, phi) -- so the ring's thin falls
    where the pen's does and not where the family's bowl profile would put it.

    Three things cost a cut each. A bowl at 0.30 of the width read as a
    leaning oval with a K beside it rather than as the body of a letter, so
    it is 0.40 and it dominates. The loop's lower end must be BURIED in the
    ring and not butted onto it -- a terminal that stops on a curve's edge
    leaves a notch. And the crossbar has to run FLAT: drawn as a second rising
    diagonal it made an X with the stem and the whole right side collapsed
    into a saltire."""
    H = XH * 1.36; WE = H * 0.80
    Y, _o = _et_frame(H); X = lambda f: f * WE
    BW, _out, _in = ring(X(0.38), Y(0.32), X(0.38), Y(0.32) - _o,
                         k=1.78, nib=(ET_THICK, ET_FLOOR, ET_PHI))
    # the upper bowl: up out of the big bowl's left flank, over the crown,
    # down the right and back in, so the two counters sit one over the other
    # SEVEN keys, not five: at five the crown came to a POINT at the upper
    # left, because a catmull through a wide-spaced turn puts all of the
    # curvature at one sample. An arc wants points round it.
    LP, _ = et_stroke([(X(0.12), Y(0.52)), (X(0.05), Y(0.76)),
                       (X(0.19), Y(0.96)), (X(0.44), Y(1.00)),
                       (X(0.62), Y(0.88)), (X(0.59), Y(0.68)),
                       (X(0.44), Y(0.57))], tension=0.5, taper=(False, False))
    # the t's crossbar and stem -- both STARTED ON THE LOOP'S RIGHT FLANK,
    # at its centreline. "Bury it deeper" is the wrong instinct on a closed
    # member and cost this arm a cut: moving the start further LEFT puts it
    # in the loop's COUNTER, not in its ink, and the square end face then
    # stands in open white as a nub. Inside a bowl means within half a
    # stroke of the centreline, which here is x 0.60, not x 0.42.
    CB, _ = et_stroke([(X(0.60), Y(0.75)), (X(0.90), Y(0.76)),
                       (X(1.22), Y(0.71)), (X(1.34), Y(0.80))],
                      scale=1.0, tension=0.5, taper=(False, True), tip=0.45)
    # THE STEM IS GIVEN REAL AIR PAST THE BOWL, and that is the third thing
    # this arm cost a cut. Run close alongside a round bowl, a straight-ish
    # stroke leaves a white wedge that tapers to a point -- a HAIR by
    # `cmp_contour_hairs.py` (158.2 deg, arms 24.1/2.2) even though both
    # strokes are full weight, because the DEFECT is in the white and not in
    # the ink. There is no near miss available here: at the bowl's equator
    # the two half-widths are 53 units together, so the stem either merges
    # solidly or it clears by enough to read as counterspace. The reference
    # clears it, with a wide counter between, so this does too.
    ST, _ = et_stroke([(X(0.62), Y(0.86)), (X(0.82), Y(0.62)),
                       (X(0.97), Y(0.32)), (X(1.02), Y(0.08)),
                       (X(1.20), Y(0.01)), (X(1.38), Y(0.12))],
                      scale=1.02, tension=0.5, taper=(False, True))
    return geom.ink([BW, LP, CB, ST])


# ALBO_IT_AMP picks one; 'a' is what the italic has always drawn (the sheared
# roman, `marks.g_ampersand`'s own path), so an unset build is byte-identical.
# ROUND 314 -- 'b', THE COMPACT CHANCERY et, IS DROPPED. Owner 2026-09-21:
# *"drop the compact chancery et"*. Its drawing (`et_b`) stays in this file --
# c is built from it and deleting it would take c with it -- but it is no
# longer selectable, and `ALBO_IT_AMP=b` now falls through to the shipped
# ampersand rather than silently choosing a letter he rejected.
ET_OPTIONS = {'c': et_c, 'd': et_d, 'e': et_e,
              'f': lambda c: alt051_traced(c),     # round 312: alt051, traced
              'g': lambda c: alt051_nib(c)}        # round 313: alt051 on the nib



# ===================== ROUND 312 -- alt051 TRACED ==========================
# Owner 2026-09-21: *"trace alt051 in the albo style"*.
#
# WHAT THIS IS, said plainly: the reference's own CONTOUR, brought into Albo's
# metrics -- scaled to this build's x-height, counter-sheared so `build.draw`'s
# 13-degree slant lands it at the reference's own slope rather than adding to
# it, and finished through `geom.ink` so it takes the face's ink spread and
# hand cut like every other glyph.
#
# WHAT IT IS NOT: re-drawn on Albo's nib. The honest method for that is the
# round-182 one -- take the reference's SKELETON and run the face's pen along
# it -- and it was attempted first: the glyph rasters and thins cleanly (1,861
# skeleton pixels off 66,848 of ink), but the skeleton breaks at every junction
# and five passes at chaining the fragments by direction would not reassemble
# them into the two or three strokes a hand actually made. That is recorded in
# `docs/albo-family-2026-09-19.md` as a negative result with the numbers, so
# the next attempt starts from hand-placed control points rather than repeating
# the automation.
#
# So this arm is a TRACE and reads as one: the reference's contrast, which is
# steeper than Albo's, and its terminals, which are Poetica's. Judge it as the
# shape, not as the finish.
ALT051_NAME = "ampersand.alt051"
ALT051_REF = os.path.join(os.path.dirname(__file__), "..", "..", "refs",
                           "poetica-std-regular.otf")

def alt051_traced(c, counter_shear=True):
    from fontTools.ttLib import TTFont
    from fontTools.pens.recordingPen import DecomposingRecordingPen
    import shapely.geometry as _sg, shapely.ops as _ops, math as _m
    f = TTFont(ALT051_REF); gs = f.getGlyphSet()
    pen = DecomposingRecordingPen(gs); gs[ALT051_NAME].draw(pen)
    rings = []; cur = []
    def flush():
        if len(cur) > 2: rings.append(list(cur))
    for op, args in pen.value:
        if op == 'moveTo': flush(); cur.clear(); cur.append(args[0])
        elif op == 'lineTo': cur.append(args[0])
        elif op == 'curveTo':
            p0 = cur[-1]; c1, c2, p3 = args
            for i in range(1, 25):
                t = i / 24; m = 1 - t
                cur.append((m**3*p0[0] + 3*m*m*t*c1[0] + 3*m*t*t*c2[0] + t**3*p3[0],
                            m**3*p0[1] + 3*m*m*t*c1[1] + 3*m*t*t*c2[1] + t**3*p3[1]))
        elif op == 'qCurveTo':
            pts = list(args); p0 = cur[-1]
            for i in range(len(pts)-1):
                cq = pts[i]
                e = pts[i+1] if i == len(pts)-2 else ((pts[i][0]+pts[i+1][0])/2, (pts[i][1]+pts[i+1][1])/2)
                for k in range(1, 17):
                    t = k/16; m = 1-t
                    cur.append((m*m*p0[0] + 2*m*t*cq[0] + t*t*e[0],
                                m*m*p0[1] + 2*m*t*cq[1] + t*t*e[1]))
                p0 = e
        elif op == 'closePath': flush(); cur.clear()
    flush()
    polys = [_sg.Polygon(r).buffer(0) for r in rings if len(r) > 2]
    g = polys[0]
    for q in polys[1:]:                      # even-odd: a ring inside another is a counter
        g = g.symmetric_difference(q)
    # pen.SLANT IS IN DEGREES (13.0), not a slope. Both counter-shears here first
    # ran it through atan(), which asks for a shear of 85.6 degrees and turns a
    # letter into a diagonal streak -- visible instantly on arm g, and present
    # but less obvious on arm f.
    # the reference is drawn on a 1000 upm with its x-height at 429 of ours
    x0, y0, x1, y1 = g.bounds
    k = (c["xh"] * ALT051_H) / (y1 - y0)
    g = aff.scale(g, k, k, origin=(x0, y0))
    if counter_shear:                        # build.draw will shear by pen.SLANT
        g = aff.skew(g, xs=-float(getattr(pen, 'SLANT', 0.0) or 0.0), ys=0.0,
                     origin=(0, 0), use_radians=False)   # SLANT IS DEGREES ALREADY
    return geom.ink([aff.translate(g, -geom.bbox(g)[0], -geom.bbox(g)[1])])

ALT051_H = float(os.environ.get("ALBO_ALT051_H", 1.62))   # its ink height, x the x-height


# ============ ROUND 313 -- alt051 ON THE ALBO NIB ==========================
# Owner 2026-09-21: *"make that letter form with the albo nib"*.
#
# Round 312 traced the reference's CONTOUR and said plainly that it was not the
# letter drawn with this face's pen. This is that letter: the reference's own
# SPINE, with Albo's nib run along it.
#
# HOW THE SPINE WAS GOT, after five passes of automation failed in round 312.
# The glyph is rastered and thinned (Zhang-Suen) to a one-pixel skeleton; the
# WAYPOINTS below were read by hand off a labelled plot of the skeleton's
# fragments, and the route between two waypoints is the skeleton's own SHORTEST
# PATH, found by breadth-first search on the pixel graph. That is what makes it
# reliable where direction-chaining was not: BFS cannot wander -- if two
# waypoints are joined through ink it finds the route, and if they are not it
# fails loudly instead of guessing. Every waypoint is a fragment ENDPOINT, so
# each is guaranteed to be a skeleton pixel; the first cut invented
# intermediate points and one landed 19 px off the ink.
#
# ROUND 314 -- THE SPUR WAS A STUB. Both of its waypoints sat on the ARM's own
# line (y ~ 260 in pixel space), so the BFS route between them was the arm, not
# the inner hook, and the coverage map against the source showed the whole arc
# missing. Its far end is in the bowl's interior at (334, 260); the route from
# there is 162 px where the stub was 80.
#
# 1,356 skeleton pixels became the 59 points of the main stroke (RDP at 1.2
# units) and 80 became the spur's 5. Those points are frozen here: they are a
# measurement of the reference, not a dial, and re-deriving them on every build
# would make the letter depend on a raster.
ALT051_SPINE = [
    (283.7,458), (285.9,465.7), (285.9,479.1), (277,486.8),
    (267,491.3), (254.8,491.3), (209.2,481.3), (194.8,472.4),
    (178.1,455.7), (168.1,438), (161.4,421.3), (150.3,363.5),
    (150.3,354.6), (155.9,335.7), (168.1,313.5), (159.2,304.6),
    (150.3,288), (137,276.8), (113.7,252.4), (101.4,234.6),
    (95.9,224.6), (88.1,202.4), (79.2,156.8), (79.2,136.8),
    (81.4,132.4), (82.6,121.3), (95.9,89.1), (109.2,69.1),
    (128.1,50.2), (141.4,40.2), (151.4,33.5), (173.7,23.5),
    (195.9,16.8), (219.2,12.4), (235.9,12.4), (277,16.8),
    (318.1,24.6), (339.2,33.5), (361.4,45.7), (398.1,76.8),
    (424.8,112.4), (441.4,146.8), (452.6,186.8), (459.2,246.8),
    (454.8,269.1), (453.7,290.2), (449.2,308), (457,315.7),
    (509.2,313.5), (560.3,304.6), (610.3,300.2), (645.9,301.3),
    (685.9,305.7), (717,314.6), (741.4,326.8), (754.8,336.8),
    (774.8,358), (787,378), (795.9,399.1), (800.3,415.7),
    (808.1,466.8), (802.6,491.3), (790.3,512.4), (777,525.7),
    (765.9,532.4), (734.8,533.5), (712.6,528),
]
ALT051_SPUR = [
    (291.4,225.7), (305.9,254.6), (320.3,274.6), (341.4,294.6),
    (361.4,306.8), (382.6,312.4), (413.7,316.8), (432.6,314.6),
    (445.9,310.2), (450.3,306.8),
]
ALT051_NIB_H = float(os.environ.get("ALBO_ALT051_NIB_H", 1.62))   # ink height, x the x-height
ALT051_THICK = float(os.environ.get("ALBO_ALT051_THICK", 0.86))   # x the stem -- the Aldine o's own pen
ALT051_THIN = float(os.environ.get("ALBO_ALT051_THIN", 0.20))     # x the thick
ALT051_PHI = float(os.environ.get("ALBO_ALT051_PHI", 35.0))       # the nib's angle, degrees
ALT051_WAIST = [
    (168.1,313.5), (179.2,309.1), (203.7,305.7), (227,305.7),
    (242.6,310.2),
]

# ROUND 315 -- THE STROKE'S OWN WIDTH, MEASURED OFF THE SOURCE.
#
# Owner: *"trace more of the line to get the red covered"*. Tracing more LINE
# closed the features (the waist, the spur, both tips); what stayed red was a
# rim down the outside of the bowl, and that is not a missing stroke -- it is
# weight. The reference's width along the main stroke runs **12 to 77 design
# units**, a 6:1 range, and a nib's width goes as |sin(direction - phi)|, which
# cannot be both the arm's hairline and the bowl's heaviest place.
#
# So the width comes from the SOURCE and the nib MODULATES it: at every sample
# the width is the reference's own half-width (its distance transform, doubled)
# times the nib's own factor raised to ALT051_NIB_MIX. At mix 0 the stroke is
# the reference's weight exactly; at 1 it is all nib. The letter keeps the
# face's direction-dependence without pretending a broad pen produced a
# 6:1 taper.
ALT051_WIDTHS = {
  "main": [
    (0,34.2), (0.0435,33.6), (0.087,24.8), (0.1304,49.1), (0.1739,52.1), (0.2174,32.9),
    (0.2609,53.9), (0.3043,76.8), (0.3478,71.5), (0.3913,55.6), (0.4348,36.4), (0.4783,24.5),
    (0.5217,25.8), (0.5652,38.9), (0.6087,55.2), (0.6522,58.3), (0.6957,46.4), (0.7391,43.9),
    (0.7826,34.6), (0.8261,21.7), (0.8696,27.6), (0.913,46.9), (0.9565,57.7), (1,11.9),
  ],
  "waist": [
    (0,56.2), (0.0435,54.7), (0.087,52.8), (0.1304,50.3), (0.1739,47.6), (0.2174,45.3),
    (0.2609,43.6), (0.3043,42.1), (0.3478,40.9), (0.3913,40.1), (0.4348,38.8), (0.4783,37.8),
    (0.5217,37.1), (0.5652,36.1), (0.6087,35.3), (0.6522,34.7), (0.6957,34.1), (0.7391,32.7),
    (0.7826,30.5), (0.8261,28.3), (0.8696,25.3), (0.913,22.6), (0.9565,21.4), (1,20.1),
  ],
  "spur": [
    (0,14.8), (0.0435,15.3), (0.087,16.1), (0.1304,16.8), (0.1739,17.7), (0.2174,18.4),
    (0.2609,19.5), (0.3043,20.9), (0.3478,21.8), (0.3913,22.4), (0.4348,23.7), (0.4783,25.4),
    (0.5217,25.8), (0.5652,25.5), (0.6087,25.9), (0.6522,27.5), (0.6957,30.3), (0.7391,35.4),
    (0.7826,40.4), (0.8261,43.7), (0.8696,48.2), (0.913,53.5), (0.9565,58.8), (1,62.2),
  ],
}
ALT051_NIB_MIX = float(os.environ.get("ALBO_ALT051_NIB_MIX", 0.45))
ALT051_BALL = float(os.environ.get("ALBO_ALT051_BALL", 0.62))     # round 314: the terminal discs, x the stroke's width there

def alt051_nib(c):
    """The reference's spine, drawn with this face's nib: the width at every
    sample is a function of the DIRECTION the stroke is running, which is what
    makes it Albo's letter rather than Poetica's outline."""
    import math as _m
    from .aldine import nib_widths
    from ..primitives import stroke as _stroke
    xs = [p[0] for p in ALT051_SPINE]; ys = [p[1] for p in ALT051_SPINE]
    k = (c["xh"] * ALT051_NIB_H) / (max(ys) - min(ys))
    S_ = pen.S
    th = S_ * ALT051_THICK
    def draw(pts, taper, ball_ends=(), key=None):
        p = [( (x - min(xs)) * k, (y - min(ys)) * k ) for x, y in pts]
        p = geom.catmull(p, tension=0.5)
        w = nib_widths(p, th, th * ALT051_THIN, target=None, smooth=9,
                       taper=taper, boost=None)
        if key in ALT051_WIDTHS:                      # round 315, above
            tab = ALT051_WIDTHS[key]; n = len(w)
            mean = sum(w) / n
            for i in range(n):
                t = i / (n - 1)
                # the source's width at t, linear between its 24 stops
                for j in range(len(tab) - 1):
                    if tab[j][0] <= t <= tab[j+1][0]:
                        f = (t - tab[j][0]) / max(1e-9, tab[j+1][0] - tab[j][0])
                        src = tab[j][1] + (tab[j+1][1] - tab[j][1]) * f
                        break
                else:
                    src = tab[-1][1]
                w[i] = src * k * ((w[i] / mean) ** ALT051_NIB_MIX)
        parts = [_stroke(p, widths(list(zip([i/(len(w)-1) for i in range(len(w))], w))))]
        # ROUND 314 -- THE TERMINALS SWELL, they do not run out. The coverage
        # map against the source (59.1% covered, 1.7% extra -- the drawing was
        # thin, not wrong) shows the two misses that are FEATURES rather than
        # weight: the top hook's tip and the right curl's tip, where the
        # reference's stroke thickens into a ball and `taper=True` ran mine to
        # nothing. Each is a disc at the stroke's own end, sized on the width
        # there, which is what a broad nib leaves when it stops without lifting.
        for idx in ball_ends:
            parts.append(dot(p[idx][0], p[idx][1], w[idx] * ALT051_BALL))
        return geom.ink(parts)
    # ROUND 315 -- THE WAIST IS ITS OWN STROKE, because it is a DEAD END.
    # Owner: *"trace more of the line to get the red covered"*. Measured on the
    # skeleton rather than by eye: the routes covered 81.5% of its pixels, and
    # the largest thing missing was the E's middle bar -- 67 pixels that no
    # route between two waypoints can ever include, because the bar terminates
    # instead of leading anywhere. A branch that ends has to be asked for.
    g = geom.ink([draw(ALT051_SPINE, True, ball_ends=(0, -1), key="main"),
                  draw(ALT051_WAIST, True, key="waist"),
                  draw(ALT051_SPUR, True, key="spur")])
    if pen.SLANT:                      # build.draw will shear; hold the reference's own slope
        g = aff.skew(g, xs=-float(getattr(pen, 'SLANT', 0.0) or 0.0), ys=0.0,
                     origin=(0, 0), use_radians=False)   # SLANT IS DEGREES ALREADY
    return geom.ink([aff.translate(g, -geom.bbox(g)[0], -geom.bbox(g)[1])])
