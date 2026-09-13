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
