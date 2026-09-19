"""v w x y z k: the diagonals, wedges on the outer side (0.9 x 0.9); the
thin strokes at 0.72 of the thick; the k's leg the A's kick at 56 degrees."""
import math, os
from . import glyph
from .. import geom, pen
from ..geom import cubic, line
from ..primitives import stem, diagonal, stroke, pen_widths, widths, wedge, diag_wedge, end_wedge, bar
from ..pen import S, XH, OVER, TH_V, TH_H, HAIR, CUT, WL, WD, DROP, ENT, adj

# ROUND 272 -- THE DIAGONALS ABOVE STEM 84. Owner 2026-09-19: *"for roman
# 700 and 900, 'w' 'v' and possibly others are too heavy compared to
# others."* Round 51's rule makes a down-right diagonal the PEN's broad,
# about 1.10 of the stem at every weight, and at the heavy ends that tenth
# is what reads: measured on the ridge, the v's thick ran 1.12 x the n's
# stem at the 700 and 1.23 at the 900, the w's 1.17 and 1.22, the k's 1.14
# and 1.21, the K's 1.18 and 1.31. Above 84 the pen's width is capped at
# DIAG_CAP x S -- 0.93, which is where the n's stem itself measures at
# those weights (0.95 S at the 700, 0.91 S at the 900, the stem's own
# entasis) -- so the thick diagonal lands on the stem. At and under 84 the
# rule is round 51's and the 400 is byte-identical.
DIAG_CAP = float(os.environ.get("ALBO_DIAG_CAP", 0.93))
def pw(p0, p1, mult=1.0):
    """Round 51's rule for every diagonal (`_diag`): the width is `mult` x
    the PEN's width at the stroke's own angle -- a down-right stroke is the
    pen's broad ~82, a down-left one its thin ~50, and 0.72 of THAT is the
    thin stroke of v w x y (36-40), not 0.72 of the stem."""
    tn = geom.tangents(line(p0, p1))[0]; th = pen.th_t(tn)
    if S > 84.0 and DIAG_CAP: th = min(th, S * DIAG_CAP)   # round 272, see DIAG_CAP
    return th * mult

# THE VERTEX, 2026-09-18 (the owner's roman bump markup, R32 on the v, R33
# on the w). The thick and the thin stroke of a v both ran to the baseline
# and each was cut square to its own axis, so the letter's bottom was two
# prongs with a notch between: measured on the built v, corners at y -16.4
# (the thick's) and -9.3 (the thin's) with the notch up to +0.6 -- the
# thin's face standing beside the thick's, which is the heavy join. Owner,
# R32: "THIS IS NOT WHAT I HIGHLIGHTED. improve the heavy join."
#
# The guide's rule -- bury the thin a fifth to a third of a stem inside the
# thick, thinning into the junction -- was built first and does not fit
# here: a 47-unit face at 70 degrees cannot sit inside the thick stroke's
# last 15 units without a corner poking out of its right edge or under its
# chisel face (the two conditions on the bury depth contradict: >= 27.4 and
# <= 25.9 units), and tapering it to fit left a 5-unit concave kink on the
# outer edge where the narrowed thin met the thick's edge. So the thin
# stroke ends ON the thick's own end face instead: both strokes are drawn as
# before and the union is cut along the thick stroke's square face, locally
# (V_CLIP_HALF either side of the vertex, V_CLIP_DEEP beyond it). The bottom
# is then one chisel face, the thick's, from its outer corner to where the
# thin's outer edge runs straight into it; nothing is buried, nothing
# tapers, and the inner crotch is exactly where it was.
W_APEX = os.environ.get("ALBO_ROM_W_APEX", "a")   # round 248: a = the thick stroke's face tops the middle apex (ships), b = the thin's
if W_APEX not in ("a", "b"): W_APEX = "a"
W_APEX_HALF = 70.0    # the apex face's reach either side of the apex point; the outer serifs are 200+ away
V_CLIP_HALF = 140.0   # the clip's reach along the face, either side of the vertex (the other vertex of a w is 313 away)
V_CLIP_DEEP = 200.0   # and beyond the face

def _flat_face(p0, p1, at_end=True):
    """caps_straight.flat_face, copied rather than imported (that module
    registers glyphs at import): the shear that makes a diagonal's end face
    HORIZONTAL instead of perpendicular to its own axis."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    return math.atan2(dx if at_end else -dx, dy)

def _flat_corner(p0, p1, w, side, at_end=True):
    """caps_straight.flat_corner: the corner of that horizontal face on the
    stroke's real edge (side -1 left, +1 right)."""
    tn = geom.tangents(line(p0, p1))[0]
    P = p1 if at_end else p0
    return (P[0] + side * w / (2 * abs(tn[1])), P[1])

def _vertex_clip(p0, p1, half=None):
    """The region beyond the thick stroke p0 -> p1's square end face, near
    the vertex: subtract it from the union so the thin stroke ends on that
    face. The face passes through p1 perpendicular to the stroke. `half`
    is the reach along the face either side of p1 (V_CLIP_HALF)."""
    tn = geom.tangents(line(p0, p1))[0]; f = (-tn[1], tn[0])
    H, D = (V_CLIP_HALF if half is None else half), V_CLIP_DEEP
    return geom.poly([(p1[0] + f[0] * H, p1[1] + f[1] * H), (p1[0] - f[0] * H, p1[1] - f[1] * H),
                      (p1[0] - f[0] * H + tn[0] * D, p1[1] - f[1] * H + tn[1] * D),
                      (p1[0] + f[0] * H + tn[0] * D, p1[1] + f[1] * H + tn[1] * D)])

@glyph('v')
def g_v(c):
    xh = c["xh"]; wf = c["wf"]; w = 440 * wf
    p0, p1 = (S * 0.4, xh), (w / 2, 0); q0, q1 = (w - S * 0.4, xh), (w / 2 + S * 0.12, 0)
    # ROUND 248. Owner 2026-09-18: "restore v and w". The round-235 vertex
    # clip (R32) is off this letter; the v is round 232's again, both styles.
    return geom.ink([diagonal(p0, p1, pw(p0, p1), serif0=1), diagonal(q0, q1, pw(q0, q1, 0.72), serif0=-1)])

def _clean_apex_notch(b, d, apex, apex_x, apex_y, band=110):
    """Owner 2026-09-13: "clean up top middle of 'w'." Two defects at the
    vertex where b and d (different angles, different widths) share one
    start point:
    1. Their own square end faces aren't collinear, so the apex `wedge()`
       (built for a near-VERTICAL stem's edge, per its docstring) only
       closes part of the gap between them, leaving a second, smaller peak
       and a notch beside the crown. Fixed by taking the convex hull of the
       three shapes near the apex and adding back only the sliver the hull
       found and the ink didn't -- i.e. the actual notch, not the legs'
       intentional counter below it (`band` keeps the patch to the region
       right at the vertex).
    2. Below that, the two strokes' INNER edges cross a second time (the
       thin b and the thick d meet the shared point at different widths, so
       their near edges don't meet at one clean point either) and leave a
       thin ink spike stabbing down into the counter -- present even before
       fix 1, at 600 px. A morphological opening (erode then dilate) removes
       a spike thinner than 2 x its radius while leaving a straight stroke
       of ordinary width alone; applied only inside a local window at the
       vertex so neither leg is touched anywhere else (checked: leg cross-
       section width off-window is bit-for-bit unchanged)."""
    core = geom.union([b, d, apex])
    missing = core.convex_hull.difference(core)
    pieces = missing.geoms if hasattr(missing, 'geoms') else [missing]
    cands = [g for g in pieces if g.area > 5 and g.bounds[1] >= apex_y - 10 and g.bounds[3] <= apex_y + band]
    patched = core if not cands else geom.union([core, min(cands, key=lambda g: g.area).buffer(0.5, join_style=2)])
    from shapely.geometry import box
    r = 0.24 * S   # > half the thin stroke's width (so the spike, thinner still, is eroded away) and < half the thin stroke's own width margin at this window's edge
    win = box(apex_x - 110, apex_y - 160, apex_x + 110, apex_y + 20)
    inside, outside = patched.intersection(win), patched.difference(win)
    opened = inside.buffer(-r, join_style=2).buffer(r, join_style=2)
    return geom.union([outside, opened])

@glyph('w')
def g_w(c):
    xh = c["xh"]; wf = c["wf"]; w = 680 * wf
    tm = 0.68 if adj('w') else 0.72   # round 92 (adj 'w'): the darkest wide letter, its thins 0.72 -> 0.68 of the pen
    P = [((S * 0.4, xh), (w * 0.27, 0), 1.0, 1), ((w * 0.5, xh * 0.96), (w * 0.27 + S * 0.12, 0), tm, None),
         ((w * 0.5, xh * 0.96), (w * 0.73, 0), 1.0, None), ((w - S * 0.4, xh), (w * 0.73 + S * 0.12, 0), tm, -1)]
    apex_y = xh * 0.96
    if pen.ITALIC:
        a, b, d, e = [diagonal(p0, p1, pw(p0, p1, m), serif0=sf) for p0, p1, m, sf in P]
        # the depth was 0.9 x WD (only this glyph); the family's apex wedge
        # (M, W) is 0.9 x 1.0 -- matched here too, so the bracket reaches as
        # far into the strokes as it does everywhere else it's used
        apex_x = w * 0.5 - pw(P[1][0], P[1][1], tm) * 0.36
        apex = wedge((apex_x, apex_y), (0, 1), (-1, 0), WL * 0.9, WD, DROP)
        mid = _clean_apex_notch(b, d, apex, apex_x, apex_y)
        return geom.ink([a, e, mid])
    # ROUND 248. Owner 2026-09-18: "restore v and w, except give top middle
    # of w a simple tall diagonal top edge without corners". The round-235
    # drawing (R33: both strokes cut flat, a crown wedge seated on the thick
    # stroke's corner, the vertex clips) is gone; the four strokes are round
    # 232's, the outer two with their serifs, and the middle apex carries
    # NO wedge. Its top is one straight face: the thick stroke d's own
    # square end face (perpendicular to d, so it rises to the right -- d's
    # right corner is the apex's highest point), extended across the thin
    # stroke b, whose opposite-tilted corner is cut off by it. That is the
    # V's vertex rule turned upside down: one face, the thick stroke's, from
    # where b's outer edge runs into it up to d's outer corner. W_APEX b is
    # the same with the thin stroke's face (falls to the right) for the
    # comparison; a ships.
    a, b, d, e = [diagonal(p0, p1, pw(p0, p1, m), serif0=sf) for p0, p1, m, sf in P]
    (b0, b1), (d0, d1) = P[1][:2], P[2][:2]
    if W_APEX == 'b':
        top = _vertex_clip(b1, b0, half=W_APEX_HALF)   # beyond b's start face
    else:
        top = _vertex_clip(d1, d0, half=W_APEX_HALF)   # beyond d's start face
    # d's top-left corner stands 6 units west of b's outer edge (d is twice
    # as wide and its face is cut the other way), a spur under the face's
    # left end; cut everything west of b's outer edge in a box around the
    # apex, so the face runs straight into that edge. The box stays clear
    # of the a stroke's material at the first vertex.
    wb = pw(b0, b1, P[1][2]); tb = geom.tangents(line(b0, b1))[0]
    E = (b0[0] + tb[1] * wb / 2, b0[1] - tb[0] * wb / 2)   # b's western edge at the apex (right hand of its down-left travel)
    far = 600.0
    west = geom.poly([(E[0] - tb[0] * far, E[1] - tb[1] * far), (E[0] + tb[0] * far, E[1] + tb[1] * far),
                      (E[0] + tb[0] * far - far, E[1] + tb[1] * far), (E[0] - tb[0] * far - far, E[1] - tb[1] * far)])
    west = west.intersection(geom.poly([(b0[0] - 150, apex_y - 60), (b0[0] + 10, apex_y - 60), (b0[0] + 10, apex_y + 80), (b0[0] - 150, apex_y + 80)]))
    return geom.ink([a, b, d, e], [top, west])

X_BL_WEDGE = 1.15   # the x's bottom-left wedge, x the family's diagonal end (0.9 is the family's own)
X_BL_WIDTH = 1.0    # the width the wedge is sized on: the THICK diagonal's (1.0), not the thin's
X_BL_THIN = 0.72    # ... and the width the stroke it lands on actually has

# THE WEDGE'S OVERHANG IS A KNIFE-CUT, NOT A WEIGHT (2026-09-19, the bold
# masters). `end_wedge` anchors a wedge half of the width it is GIVEN off the
# stroke's centreline, and the x's bottom-left wedge is deliberately given the
# THICK diagonal's width (X_BL_WIDTH 1.0, owner 2026-09-14: "increase the visual
# weight of the bottom left serif in 'x'") while the stroke it sits on is drawn
# at X_BL_THIN of that. So its root stands (1.0 - 0.72)/2 = 0.14 of the pen's
# width OUTSIDE the thin stroke's edge, and that overhang is a FRACTION of the
# stem -- it grows with the weight axis. At the Medium's 84 the wedge's own body
# still bridges it; by FJORD_STEM 107 it does not, and the glitch gate reads the
# x as a SPLIT: two ink islands, 87,873 and 6,961 square units, the second being
# the whole serif lying detached at the bottom left (x 71..256, y 13..176).
#
# The cure is to hold that overhang at the number of UNITS it has at the Medium
# instead of at a fraction of the stem: a serif's reach past its own stroke is a
# detail of the cut, and nothing about a heavier pen says the gap between the two
# should open. `84.0 / S` is exactly 1.0 at the shipping Medium, so the anchor
# width is `pw(q0, q1)` there to the bit and the roman is unchanged; above it the
# wedge walks back in toward the stroke as fast as the stroke thickens.
# Measured: 0 glitch findings at stems 107, 116, 122 and 140.
def x_bl_anchor(q0, q1):
    thin = pw(q0, q1, X_BL_THIN)
    return thin + (pw(q0, q1, X_BL_WIDTH) - thin) * min(1.0, 84.0 / pen.S)

@glyph('x')
def g_x(c):
    xh = c["xh"]; wf = c["wf"]; w = 430 * wf
    p0, p1 = (S * 0.4, xh), (w - S * 0.4, 0); q0, q1 = (w - S * 0.4, xh), (S * 0.4, 0)
    # owner 2026-09-14: "increase the visual weight of the bottom left serif
    # in 'x'" -- that serif ends the THIN diagonal, so the family's wedge
    # scaled on the thin stroke's width is small; it is drawn on the thick
    # diagonal's width instead, at X_BL_WEDGE of the family's diagonal end
    thin = diagonal(q0, q1, pw(q0, q1, X_BL_THIN), serif0=-1)
    bl = end_wedge([q0, q1], x_bl_anchor(q0, q1), False, -1, scale=X_BL_WEDGE)
    return geom.ink([diagonal(p0, p1, pw(p0, p1), serif0=1, serif1=1), thin, bl])

# owner 2026-09-14 ("Beyond", "Tuesday"): "the 'y' is too dark in a word
# currently. thin out the left stroke of 'y' by decreasing its width, but
# leave the left side of the character as is." Y_LEFT_W x the pen's width
# for the left diagonal; the stroke's centerline moves toward its inner
# (upper-right) edge by half the width lost, so the outer (lower-left) edge
# and the serif on it stay where they were. Chosen on the in-word
# measurement (outlines/cmp/balance.py) and the eye, round 88.
Y_LEFT_W = float(__import__('os').environ.get('FJORD_Y_LEFT_W', 0.97))   # owner 2026-09-14, round 90: "0.9 is slightly too thin for 500", then ".97" from the 0.92-0.98 ladder

@glyph('y')
def g_y(c):
    xh = c["xh"]; wf = c["wf"]; desc = c["desc"]; w = 440 * wf
    # ROUND 267 -- THE DIAGONAL MUST REACH THE TAIL AT ANY WEIGHT. Its end was
    # -S x 0.4 below the line: an overlap sized in the stem, crossing a tail
    # whose path sits on the descender grid. At the 200's stem of 43.8 that is
    # 17.5 units and the tail's ink no longer covers it -- the y shipped as TWO
    # islands (25568 and 22308 units^2). The end is now the deeper of the two,
    # S x 0.4 or 0.16 of the descender (41 units): at 66.9 the extension sits
    # entirely inside the tail's ink, so the shipped 400 is unchanged.
    # Gated to stems under the 400's 66.9: at 66.9 the deeper end poked out of
    # the tail's ink by a few units and moved a ruled letter, so the shipped
    # weight keeps -S x 0.4 exactly and only the lighter cuts take the floor.
    _yend = -max(S * 0.4, desc * 0.16) if S < 66.0 else -S * 0.4
    p0, p1 = (S * 0.4, xh), (w / 2 + S * 0.1, _yend)
    w_full = pw(p0, p1); w_left = w_full * Y_LEFT_W
    if Y_LEFT_W != 1.0:
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]; L = math.hypot(dx, dy)
        nx, ny = -dy / L, dx / L            # the left normal of a down-right stroke points up-right: the inner edge
        sh = (w_full - w_left) / 2
        # the centerline moves TOWARD the edge that stays (outer = center - n w/2 is fixed when center moves by -n sh)
        p0 = (p0[0] - nx * sh, p0[1] - ny * sh); p1 = (p1[0] - nx * sh, p1[1] - ny * sh)
    a = diagonal(p0, p1, w_left, serif0=1)
    tail = cubic((w - S * 0.4, xh), (w * 0.52, -desc * 0.55), (w * 0.44, -desc * 1.08), (w * 0.02, -desc * 0.95))
    # round 51: the pen's width along the tail x (0.72 rising to 1.0 by the middle), flaring 0.3 into the cut
    wfn = pen_widths(tail, lambda t: (0.72 + 0.28 * min(1.0, t * 2)) * widths([(0.7, 1.0), (1.0, 1.3)])(t))
    t = stroke(tail, wfn, cut1=CUT)
    return geom.ink([a, t, end_wedge(tail, wfn(0.0), True, -1)])

@glyph('z')
def g_z(c):
    """Owner 2026-09-13, on the cleanup: "'z' is much worse, you are
    half-assing it and I need better." Read against Albertus and Berkeley:
    in both the z's DIAGONAL is the heavy stroke and the bars are light,
    and the corners where the diagonal meets the bars are mitred on the
    diagonal's own line -- the ruled Z construction (round 82: mitre, the
    bottom bar run out to the top corner's x). So the z is the Z at
    x-height: bars at Z_BAR of the stem with the top's hanging wedge at the
    left and the bottom's rising wedge at the right, the diagonal at
    Z_DIAG x S, each bar's end at the diagonal cut along the diagonal's
    outer edge, the bottom bar run out so both right edges share one x."""
    from shapely.geometry import Polygon, box as _box
    xh = c["xh"]; wf = c["wf"]; w = 400 * wf * Z_W
    th = S * (Z_BAR_ADJ if adj('z') else Z_BAR); dw = S * (Z_DIAG_ADJ if adj('z') else Z_DIAG)
    p_top, p_bot = (w - S * 0.12, xh - th / 2), (S * 0.12, th / 2)
    dg = diagonal(p_top, p_bot, dw)
    dx, dy = p_top[0] - p_bot[0], p_top[1] - p_bot[1]; L = math.hypot(dx, dy); dx, dy = dx / L, dy / L
    nx, ny = dy, -dx
    ox, oy = p_top[0] + nx * dw / 2, p_top[1] + ny * dw / 2
    corner = (ox + dx * (xh - oy) / dy, xh)
    ox2, oy2 = p_bot[0] - nx * dw / 2, p_bot[1] - ny * dw / 2
    corner2 = (ox2 + dx * (0.0 - oy2) / dy, 0.0)
    far = 4000.0
    def half(cn, sign):
        u = (dx * far, dy * far); n = (nx * far * sign, ny * far * sign)
        return Polygon([(cn[0] + u[0], cn[1] + u[1]), (cn[0] - u[0], cn[1] - u[1]), (cn[0] - u[0] + n[0], cn[1] - u[1] + n[1]), (cn[0] + u[0] + n[0], cn[1] + u[1] + n[1])])
    t = bar(0, max(w, corner[0] + 2), xh, th, align='top', cut0=CUT, wedges=[('left', -1)])
    bt = bar(min(0, corner2[0] - 2), corner[0], 0, th, align='bottom', cut1=CUT, wedges=[('right', 1)])
    g = geom.ink([t, bt, dg])
    cut_tr = half(corner, +1).intersection(_box(corner[0] - S * 2, xh - th - 2, corner[0] + far, xh + far))
    cut_bl = half(corner2, -1).intersection(_box(corner2[0] - far, -far, corner2[0] + S * 2, th + 2))
    return g.difference(cut_tr).difference(cut_bl)
# ROUND 207 -- THE Z'S TWO STROKES ARE DIALS. Owner 2026-09-17: *"give me
# options for a roman z that has thicker crossbar and thinner diagonal"*, after
# the weight survey measured this letter as the heaviest lowercase in the face
# (stroke 99.3 against the roman lowercase median of 79.0) while its italic is
# the lightest glyph in the face at 27.1 -- 73% apart, and not recognisable as
# one typeface's z.
#
# Note what this reverses: the construction above was read off Albertus and
# Berkeley, where the z's DIAGONAL is the heavy stroke and the bars are light.
# His ask inverts that relationship, which is his to make -- and the survey is
# the argument for it, since the diagonal is what makes this z the darkest thing
# on its line.
#
# REWORKED 2026-09-18, and the round-207 ruling below is superseded on the
# numbers while its PRINCIPLE stands: the bars still carry this letter, the
# diagonal still gives way. Owner: *"z is too wide and heavy in roman. rework
# so razzmatazz is balanced."* Both faults measured -- ink 1.05 of the o where
# Georgia sets 0.83 and Times 0.95, and colour +12% over the lowercase median.
# Shipped: width 0.84, bars 0.73, diagonal 0.605 -- ink 0.85 of the o, colour
# +3%, the bar/diagonal ratio kept at round 207's 1.48. In razzmatazz the z's
# now sit with the a and the m instead of stamping through them; one notch
# lighter again (0.70 / 0.58) and they go paler than the r, which is the other
# fault.
#
# ROUND 207, 2026-09-17: B -- bars 0.85, diagonal 0.70. Measured off the
# raster, that is a bar of 90.9 units against a diagonal of 61.4 (bar/diag
# 1.48, from 1.00), with the bars now clearly the heavy stroke and the diagonal
# at the weight of a round letter's curve. Colour goes 0.337 -> 0.368 against a
# lowercase median of 0.330: thickening two full-width bars adds more ink than
# thinning one 45-degree run removes, so this letter gets DARKER by making its
# heaviest stroke lighter. Glitch gate clean; the mitres hold.
# ROUND 210 -- THE Z'S WIDTH. Owner 2026-09-18: *"z is too wide and heavy in
# roman. rework so razzmatazz is balanced."* Measured, the z's ink runs 1.05 of
# the o's where Georgia sets 0.83 and Times New Roman 0.95 -- a lowercase z is
# narrower than its o in every text roman to hand, and Albo's was wider. Z_W
# scales the drawn width; the fitter takes the sidebearings from the ink, so
# the advance follows it down.
Z_W = float(os.environ.get("ALBO_Z_W", 0.84))
Z_BAR = float(os.environ.get("ALBO_Z_BAR", 0.52))    # the z's bars, x the stem (owner 2026-09-14: "slightly reduce the line thickness ... of the horizontal strokes in 'z'"; 0.62 before). The bars stay ON the x-height and the baseline (align top / bottom), so the vertical grid holds
Z_DIAG = float(os.environ.get("ALBO_Z_DIAG", 1.05))  # the z's diagonal, x the stem (the heavy stroke, as Albertus and Berkeley)
Z_BAR_ADJ = float(os.environ.get("ALBO_Z_BAR_ADJ", 0.73))    # round 92 (adj 'z'): the darkest thing on any line it was in -- diagonal down, bars up, one color
Z_DIAG_ADJ = float(os.environ.get("ALBO_Z_DIAG_ADJ", 0.605))

@glyph('k')
def g_k(c):
    """Stem, an arm from the stem at 0.42 xh to the x-height, and the leg
    springing from the arm at the A's kick, 56 degrees (ruling).

    Owner 2026-09-13, verbatim: "add some weight to the top right kick of
    'k' to balance it out visually and reduce overlap of bottom right
    stroke." ARM_WEIGHT is the ladder's default (x1.30 of round 51's 0.78
    pen-mult; the page also builds 1.15 and 1.45). The leg used to spring
    from a point ON THE ARM'S CENTERLINE and bury straight through it,
    crossing both edges and knotting; it now springs from the arm's LOWER
    edge (LEG_EDGE) and buries only LEG_BURY (a fifth of a stem, the
    join-rule minimum) past that edge, thinning sooner (LEG_TAPER) so the
    join reads as one clean fork instead of an X."""
    ARM_WEIGHT = 1.40 if adj('k') else 1.30   # round 92 (adj 'k'): light beside the stem, band -14% Albertus
    K_ARM_WEDGE = 1.35 if adj('k') else 1.15   # round 93 (owner): "the top right serif of 'k' needs more visual weight"
    LEG_EDGE = 1.0            # spring the leg from the arm's lower edge (1.0), not its centerline (0.0)
    LEG_BURY = 0.20           # x stem, past that edge (join rule: a fifth to a third of a stem)
    LEG_TAPER = (0.55, 0.35)  # thin from t=0.55 (was 0.78) to 0.35 x lw (was 0.55) at the buried tip
    xh = c["xh"]; wf = c["wf"]; x = S / 2
    st = stem(x, 0, c["asc"], top='left', foot='both')
    A0, B0 = (x + 360 * wf, xh * 0.97), (x + S * 0.2, xh * 0.42)
    arm_w = pw(A0, B0, 0.78 * ARM_WEIGHT)   # round 51's 0.78 x the pen at the arm's angle, x the ladder weight
    # owner 2026-09-13: "the top right serif needs to be slightly larger so
    # visually balances and reads well" -- the arm's end wedge at K_ARM_WEDGE
    # of the family's diagonal end (0.9 is the family's own)
    arm = geom.union([diagonal(A0, B0, arm_w), end_wedge([B0, A0], arm_w, False, 1, scale=K_ARM_WEDGE)])
    u = (150 * wf - (B0[0] - x)) / (A0[0] - B0[0]); J = (B0[0] + (A0[0] - B0[0]) * u, B0[1] + (A0[1] - B0[1]) * u)
    # the arm's own direction and its outward normal, to find the arm's
    # lower edge at J instead of J's centerline point
    ad = (A0[0] - B0[0], A0[1] - B0[1]); aL = math.hypot(*ad); ad = (ad[0] / aL, ad[1] / aL)
    an = (-ad[1], ad[0])
    if an[0] < 0: an = (-an[0], -an[1])
    J_edge = (J[0] + an[0] * arm_w / 2 * LEG_EDGE, J[1] + an[1] * arm_w / 2 * LEG_EDGE)
    foot = (J[0] + J[1] / math.tan(math.radians(56)), 0)
    d = (J[0] - foot[0], J[1] - foot[1]); L = math.hypot(*d); d = (d[0] / L, d[1] / L)
    lw = pw(foot, J) * (1.10 if adj('k') else 1.0)   # round 51: the pen at the leg's angle (58 at 56 degrees); round 92 leg x1.10
    tip = (J_edge[0] + d[0] * S * LEG_BURY, J_edge[1] + d[1] * S * LEG_BURY)
    leg = diagonal(foot, tip, widths([(0.0, lw), (LEG_TAPER[0], lw), (1.0, lw * LEG_TAPER[1])]), serif0=1)
    return geom.ink([st, arm, leg])
