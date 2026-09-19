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
import math
import shapely.affinity as aff
from .. import geom, pen
from .. import primitives as PR
from ..geom import line, catmull, superellipse, cubic
from ..primitives import stroke, pen_widths, bowl_widths, widths, wedge, end_wedge, diagonal, bar, beak, ring, stem
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
    tn = geom.tangents(line(p0, p1))[0]; return pen.th_t(tn) * mult

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

CUR_W = 8.76 * S * pen.WIDTH   # the shipping &'s 736, in the pen's units, on the width axis
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
            d_in = (D[0] - M[0], D[1] - M[1]); Ld = math.hypot(*d_in) or 1.0; d_in = (d_in[0] / Ld, d_in[1] / Ld)
            d_out = (math.cos(ang), math.sin(ang)); chord = math.dist(D, A1)
            def _bowl(scale):
                L1, L2 = bowl_k[0] * chord * scale * 0.5, bowl_k[1] * chord * scale * 0.5
                return cubic(D, (D[0] + d_in[0] * L1, D[1] + d_in[1] * L1), (A1[0] - d_out[0] * L2, A1[1] - d_out[1] * L2), A1)
            scale = 1.0
            for _ in range(12):   # bring the lowest point onto -o
                bowl_path = _bowl(scale); ymin = min(q[1] for q in bowl_path)
                if abs(ymin + o) < 0.5: break
                scale *= 1.0 + (-o - ymin) / max(chord, 1.0) * 1.5
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
        wf = mixw(sp, blend, lambda t: prof(t) * sw(t), floor=THIN)
        parts.append(stroke(sp, wf, pieces=True, cut0=CUT if spur_foot == 'plain' else None, cut1=end_cut))
        if spur_foot == 'wedge': parts.append(end_wedge(sp, wf(0.0), True, +1, 0.9))
        arm_sp, arm_w = sp, wf(1.0)
    else:
        # the spur, its own stroke, thinning into the crossing
        spur_sp = geom.resample(catmull(sp_pts + [spur_end], tension=0.5) if spur_foot == 'hook' else line(sp_pts[0], spur_end))
        prof = widths([(0.0, 0.3 if spur_foot == 'hook' else 1.0), (0.05, 1.0), (0.72, 1.0), (1.0, 0.65)])
        sw = pen_widths(spur_sp, prof, floor=THIN, scale=spur_w)
        parts.append(stroke(spur_sp, sw, cut0=CUT if spur_foot == 'plain' else None))
        if spur_foot == 'wedge': parts.append(end_wedge(spur_sp, sw(0.0), True, +1, 0.9))
        if top == 'closed':
            # the egg runs clockwise like `loop_path`; `ring_from` offsets inward from a ccw outline, so reverse it
            if loop_shape == 'egg': outer = egg_loop_path(cx, cy + ry, X, rx, egg_pinch, egg_power)[:-1][::-1]
            else: outer = teardrop_outer(cx, cy, rx, ry, X)
            lo, _, _ = teardrop_loop(outer); parts.append(lo)
            sp = body
            blend = widths([(0.0, 1.0), (tD - 0.02, 1.0), (tD + 0.03, 0.0), (tB5 - 0.02, 0.0), (tB5 + 0.04, 1.0)])
            wf = mixw(sp, blend, floor=THIN)
            parts.append(stroke(sp, wf, cut1=end_cut))
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
            wf = mixw(sp, blend, widths([(0.0, 0.92), (tH + 0.03, 1.0)]), floor=THIN)
            parts.append(stroke(sp, wf, pieces=True, cut0=CUT if hook_end == 'cut' else None, cut1=end_cut))
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
