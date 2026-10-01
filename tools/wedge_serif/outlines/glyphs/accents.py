"""The diacritics, drawn on the pen (round 99, 2026-09-14).

Why they exist: the reader's `reading` interval asks for U+0020-024F, and
every codepoint Albo does not draw is supplied by Noto at build time -- so
"cafe" with an acute, "naive" with a dieresis and every German, French,
Spanish, Polish or Czech word in a book came out with one letter from
another typeface. This module draws the marks; `build.ACCENTED` composes
them onto the bases as TrueType composites, so an accented letter IS its
letter plus its mark, never a redrawn approximation that can drift.

Each mark is drawn with its own ink starting at x = 0 and, for an
ABOVE mark, its bottom on y = 0; a BELOW mark hangs from y = 0. The
composite places it: `build.place_accent` centres it on the base's ink and
lifts it to the x-height or the cap line. So nothing here knows about a
base, and the same mark serves the lowercase and the capitals.

Sizes are the pen's, not invented: the strokes take `pen.th()` at their own
angle exactly as a letter's do, the dots are the family's `DOT_R`, the
macron is the pen's horizontal, and the ring is a bowl.
"""
import math, os
from . import glyph
from .. import geom, pen
from ..geom import cubic, line
from ..primitives import stroke, pen_widths, widths, dot, ring, bar, miter_chevron
from ..pen import S, XH, CAP, ASC, TH_V, TH_H, HAIR, CUT, BOWL_K
from .stems import DOT_R, TIT_R, dot_y

# ROUND 450 -- THE ACCENTS AT THE REFERENCES' SIZE (owner 2026-09-30: "resize
# accents to fit rest and center the marks"). instruments/acc_fit.py reads every
# mark off its own letter (the accented glyph's raster minus its base's), per
# x-height, against Pagella, Flanker, Georgia, Berkeley and Times (Coelacanth in
# the italic), each style against its own. Albo's marks were the references'
# shape at two thirds of their size: circumflex and caron 0.45-0.58 of the
# x-height wide against 0.60-0.72, tilde 0.43-0.48 against 0.70-0.78 and half
# as tall, macron 0.40-0.43 against 0.70-0.78, breve 0.48-0.55 against
# 0.63-0.66, ring 0.33 against 0.44-0.55, double acute 0.48-0.56 against
# 0.68-0.87, cedilla and ogonek 0.28-0.30 deep against 0.43-0.48; the acute half
# the references' weight (0.29-0.33 of the stem against 0.56-0.70); and the
# BOLD dieresis 1.05 x-heights wide against 0.68-0.82, its dots 0.37 against
# 0.28, the one mark too big. ALBO_ACC_FIT=0 restores round 449's marks.
ACC_FIT = int(os.environ.get("ALBO_ACC_FIT", 1))
# The family's accent box. Width and height are the proportions a garalde
# gives an acute: about two fifths of the x-height wide and a little over a
# quarter tall (0.26 until round 450: the acute and grave read 0.29-0.37 of the
# x-height tall on their letters, the references 0.37-0.43).
ACC_H = (float(os.environ.get("ALBO_ACC_H", 0.285)) if ACC_FIT else 0.26) * XH
ACC_W = 0.38 * XH          # 163
_FX = lambda k, v, old: (float(os.environ.get("ALBO_" + k, v)) if ACC_FIT else old)
CIRC_W = _FX("CIRC_W", 0.56, 0.38) * XH      # the circumflex's box (ink ~0.64 of the x-height)
CARON_W = _FX("CARON_W", 0.52, 0.38) * XH    # the caron's (its cut ends spread wider than the circumflex's)
BREVE_W = _FX("BREVE_W", 0.54, 0.38) * XH
RING_K = _FX("RING_K", 0.77, 0.62)           # the ring's radius x ACC_H
CED_D, CED_X = _FX("CED_D", 0.44, 0.30), _FX("CED_X", 1.35, 1.0)    # the cedilla's depth (x xh) and width (x its round-99 drawing)
OGO_D, OGO_X = _FX("OGO_D", 0.42, 0.28), _FX("OGO_X", 1.55, 1.0)    # the ogonek's
# The dieresis and the dot above: the dot a little larger in the 400s (0.212 ->
# 0.225 of the x-height, references 0.21-0.26) and the WHITE between the two
# dots held at a fixed share of the x-height, which is what the references do
# at every weight (their white reads 0.17-0.18 of the x-height in the roman and
# the bold alike, the dots growing with the weight). The dots grow with the
# square root of the stem, not with the stem: the tittle they were made from
# grows linearly, and at the bold that made them 1.3x the references'.
DOT_K = _FX("DOT_K", 1.06, 1.0)
DIE_WHITE = _FX("DIE_WHITE", 0.18, 0.0) * XH
# round 451 (round 450's review): at the square root the bold's dots (0.30 of the
# x-height) fell under parts_audit's 4-dark-pixel floor at 8 pt on the X3 in 18
# cells; laddered 0.50 / 0.40 / 0.30 / 0.25 / 0.20 -> 18 / 15 / 5 / 1 / 1 failing
# cells, no dieresis merged at any size. 0.25 makes the bold dot 0.34 of the
# x-height, the references' largest (0.28-0.34).
DOT_WEXP = float(os.environ.get("ALBO_DOT_WEXP", 0.25))
DOT_W = ((66.9 / S) ** DOT_WEXP if S > 66.9 else 1.0) if ACC_FIT else 1.0
# The acute and grave, lighter: drawn on the pen's thick they read 0.70-0.82 of
# the stem (0.99 for the italic grave, which the shear thickens) against the
# references' 0.56-0.70 -- heavier than Albo's own dieresis relative to the
# references' (their acute is 0.88 of their dieresis's weight). The italic
# grave takes more off than its acute for the shear's sake.
_IT = bool(getattr(pen, "ITALIC", False))
ACUTE_WT = _FX("ACUTE_WT", 0.93 if _IT else 0.86, 1.0)
GRAVE_WT = _FX("GRAVE_WT", 0.76 if _IT else 0.86, 1.0)
DA_TW = _FX("DA_TW", 0.68 + max(0.0, min(1.0, (S - 66.9) / 49.1)) * 0.12, 0.0)   # the double acute's whole width, x xh (references 0.68 / 0.77-0.87 bold)
DIE_GAP = float(os.environ.get("ALBO_DIE_GAP", 3.70))   # the dieresis's centres apart, x a dot RADIUS (round 369)
ACC_LIGHT = 0.86           # the marks' strokes, x the pen (a mark is lighter than a stem)

def _stroke(pts, prof=None, cut0=CUT, cut1=CUT, light=ACC_LIGHT):
    return stroke(pts, pen_widths(pts, (prof or (lambda t: 1.0)), scale=light), cut0=cut0, cut1=cut1)

# 2026-09-28 -- THE ACUTE IS THE GRAVE'S MIRROR (issue sweep; docs/albo-issue-
# sweep-2026-09-28.md; owner's parts-audit follow-up "thin accents"). Drawn on
# the pen, the acute rises along the nib's own angle and comes out the pen's
# THIN: mean width 19 units in the built Regular (0.29 of the stem), 20 in the
# Italic, against the grave's 50 / 56 -- a third of its ink. Every reference
# draws the two as mirror images of one weight: acute / grave mean width over
# the stem Pagella 0.64 / 0.63, Flanker 0.65 / 0.65, Georgia 0.70 / 0.70,
# Berkeley 0.67 / 0.67, their italics 0.62-0.72 (instruments/mark_measure.py).
# On the X3 the acute of e-acute had ZERO dark pixels at 8, 10 and 12 pt in
# both 400s where every reference's had 1-10 (instruments/parts_check.py) --
# the most-used accent in a Spanish or French book, and the Greek tonos with
# it. ACUTE_OPT b draws it as the grave reflected left for right, so the two
# are one weight; the double acute's two strokes follow (each DA_WT of it,
# spread so their white holds DA_WHITE of a stroke). a = today.
ACUTE_OPT = os.environ.get("ALBO_ACUTE_OPT", "b" if ACC_FIT else "a")   # round 450: b ships
DA_WT = float(os.environ.get("ALBO_DA_WT", 0.80))
DA_WHITE = float(os.environ.get("ALBO_DA_WHITE", 0.60))

def _mirror(g):
    import shapely.affinity as aff
    g = aff.scale(g, -1, 1, origin=(0, 0))
    return aff.translate(g, -g.bounds[0], 0)

# ROUND 453 -- THE ITALIC ACUTE, STEEPER AND SHORTER. Owner 2026-09-30, on the italic "aquí?"
# (the collision check had opened its ? to +47 to clear the acute's tip): *"reduce the accent
# length and/or make angle of stroke to avoid near collision"*. Measured on its own letters
# (í é á ó ú, the set acute after the shear), Albo's italic acute leaned 57 degrees from
# vertical and ran 0.580 of the x-height long; the italic references lean 36-52 (median 45:
# Pagella 52, Georgia 45, Flanker 45, Coelacanth 41, Times 36) and run 0.518-0.640 (median
# 0.550). So in the italics the acute is drawn to SET at ACUTE_IT_LEAN from vertical, its
# centerline ACUTE_IT_LEN of today's: the box is solved from the shear, so the lean is the
# one the reader sees. The grave, the roman and every other mark are untouched.
ACUTE_IT_LEAN = float(os.environ.get("ALBO_ACUTE_IT_LEAN", 47.0))   # degrees from vertical, as set; 0 = today's
ACUTE_IT_LEN = float(os.environ.get("ALBO_ACUTE_IT_LEN", 0.95))     # x today's set centerline length
ACUTE_IT_WT = float(os.environ.get("ALBO_ACUTE_IT_WT", 0.96))       # the pen runs ~4% heavier on the steeper
                                                                    # stroke; this holds round 450's measured weight

# ROUND 453 -- THE ITALIC MARKS, SMALLER. Owner 2026-10-01, on the italic Wörter / Töne / Të /
# Těšín proof: *"reduce umlaut and other marks to not be so close to other letters and marks"*.
# Measured on their own letters (instruments/acc_fit.py), the italic marks sat at or above the
# italic references' median width -- the grave wider than all five, the circumflex, caron,
# ring and double acute in their upper half -- and the dieresis 0.636 of the x-height wide
# against Pagella's 0.527. MARK_IT_K scales every ABOVE mark's DRAWING in the italics -- its
# width and height, never its stroke weight (a stroke's width follows its direction, which a
# uniform scale keeps) -- with the tilde's height held (already the references' lowest). The
# dieresis's dots take DOT_IT_K and the white between them DIE_IT_W; the dot above takes the
# same dots. The roman, the marks below and the gaps under the marks are untouched.
# Owner 2026-10-01, on the A/B proof: "A wins" -- drawn 10% smaller (8-10% narrower as set),
# the dieresis 12% (0.636 -> 0.559 of the x-height). B was 0.80 / 0.90 / 0.55. Their spacing is
# instruments/mark_crowd.py --clear's (no mark nearer a neighbor than 0.8 of its own gap), in
# spacing_b2.json's clearance_composite. docs/albo-round-453-2026-09-30.md.
MARK_IT_K = float(os.environ.get("ALBO_MARK_IT_K", 0.90)) if (_IT and ACC_FIT) else 1.0
DOT_IT_K = float(os.environ.get("ALBO_DOT_IT_K", 0.95)) if (_IT and ACC_FIT) else 1.0
DIE_IT_W = float(os.environ.get("ALBO_DIE_IT_W", 0.70)) if (_IT and ACC_FIT) else 1.0
_KH, _KW = ACC_H * MARK_IT_K, ACC_W * MARK_IT_K        # the stroke marks' box, scaled

@glyph('´')      # acute
def g_acute(c):
    if ACUTE_OPT == "b":
        if _IT and ACC_FIT and ACUTE_IT_LEAN > 0:
            k = pen.SHEAR
            L = math.hypot(ACC_W + k * ACC_H, ACC_H) * ACUTE_IT_LEN * MARK_IT_K
            th = math.radians(ACUTE_IT_LEAN)
            H = L * math.cos(th); W = H * (math.tan(th) - k)
            return _mirror(_stroke(line((0, H), (W, 0)), light=ACC_LIGHT * ACUTE_WT * ACUTE_IT_WT))
        return _mirror(_stroke(line((0, ACC_H), (ACC_W, 0)), light=ACC_LIGHT * ACUTE_WT))
    return _stroke(line((0, 0), (ACC_W, ACC_H)))

@glyph('`')      # grave
def g_grave(c):
    return _stroke(line((0, _KH), (_KW, 0)), light=ACC_LIGHT * GRAVE_WT)

def _chev(a, p, b):
    # ROUND 451 (owner: "also fix chevron glitches"): one polygon mitered at the
    # point, each arm at the pen's own width for its direction -- the two square
    # stroke ends that met there left a stepped notch (primitives.miter_chevron)
    w1 = pen_widths(line(a, p), lambda t: 1.0, scale=ACC_LIGHT)(0.5)
    w2 = pen_widths(line(p, b), lambda t: 1.0, scale=ACC_LIGHT)(0.5)
    return miter_chevron(a, p, b, w1, w2, cut_a=CUT, cut_b=CUT)

@glyph('ˆ')      # circumflex
def g_circumflex(c):
    if ACC_FIT:
        w = CIRC_W * MARK_IT_K
        return _chev((0, 0), (w / 2, _KH), (w, 0))
    left = _stroke(line((0, 0), (CIRC_W / 2, ACC_H)), cut1=None)
    right = _stroke(line((CIRC_W / 2, ACC_H), (CIRC_W, 0)), cut0=None)
    return geom.ink([left, right])

@glyph('ˇ')      # caron
def g_caron(c):
    if ACC_FIT:
        w = CARON_W * MARK_IT_K
        return _chev((0, _KH), (w / 2, 0), (w, _KH))
    left = _stroke(line((0, ACC_H), (CARON_W / 2, 0)), cut1=None)
    right = _stroke(line((CARON_W / 2, 0), (CARON_W, ACC_H)), cut0=None)
    return geom.ink([left, right])

# 2026-09-28 -- THE TILDE, AT THE REFERENCES' SIZE (issue sweep; the same
# follow-up). The wave is drawn in the acute's box (ACC_W x ACC_H) and comes
# out 185 x 63 units in the built Regular, 0.41 x 0.14 of the x-height, with a
# mean width 0.41 of the stem; the references run 0.65-0.84 x 0.22-0.30 of
# theirs and 0.58-0.73 of the stem (Pagella, Flanker, Georgia, Berkeley, the
# italics alike). n-tilde had 1-3 dark pixels at 8-12 pt on the X3 against the
# references' 4-17. TILDE_OPT b draws the same wave in a box TILDE_W wide and
# TILDE_H tall (x xh) at TILDE_WT the stroke. A cubic's controls are not on its
# curve, so the ink is shorter than the box: at 0.36 it measured 0.68 x 0.20 xh in
# the 400s, still under the references' 0.22-0.30; 0.44 is the box for ~0.24.
# a = today.
TILDE_OPT = os.environ.get("ALBO_TILDE_OPT", "b" if ACC_FIT else "a")   # round 450: b ships, a touch larger than the sweep's
TILDE_W = float(os.environ.get("ALBO_TILDE_W", 0.64 if ACC_FIT else 0.62))
TILDE_H = float(os.environ.get("ALBO_TILDE_H", 0.54 if ACC_FIT else 0.44))
TILDE_WT = float(os.environ.get("ALBO_TILDE_WT", 1.35))

# ROUND 451 -- THE TILDE AS AN EVEN WAVE (owner: "fix this tildes"; "bold and
# bold italic tilde is too thick. take passes until corrected"). Drawn on the
# pen it took the nib's thick on every falling stretch and its thin on every
# rising one, and the pen-cut ends curled into hooks -- at the bold weights a
# lumpy bird rather than a wave. Every reference draws it smooth: thin at both
# ends, full through the middle, point-symmetric. So the centerline is one
# point-symmetric cubic and the width a sine across it, no pen and no cut, the
# mean width TILDE_MW of the stem at the 400 easing to TILDE_MW7 at the 700.
TILDE_EVEN = int(os.environ.get("ALBO_TILDE_EVEN", 1 if ACC_FIT else 0))
TILDE_MW = float(os.environ.get("ALBO_TILDE_MW", 0.60))
TILDE_MW7 = float(os.environ.get("ALBO_TILDE_MW7", 0.40))   # owner: the bold tildes "too thick"; laddered .30/.36/.42/.48, .42 sits with the bold's own thin strokes, .40 leans lighter as asked
TILDE_EW = float(os.environ.get("ALBO_TILDE_EW", 0.66))      # the even wave's box, x xh
TILDE_EH = float(os.environ.get("ALBO_TILDE_EH", 0.40))
TILDE_ENDS = float(os.environ.get("ALBO_TILDE_ENDS", 0.30))  # the ends' width, x the middle's

@glyph('˜')      # tilde
def g_tilde(c):
    """A wave: up out of the left, over, down into the right. Thin at the
    ends as a pen stroke turning through the horizontal is."""
    if TILDE_EVEN:
        W, H = XH * TILDE_EW * MARK_IT_K, XH * TILDE_EH
        p = cubic((0, H * 0.25), (W * 0.30, H * 1.35), (W * 0.70, -H * 0.35), (W, H * 0.75))
        k = max(0.0, min(1.0, (S - 66.9) / 49.1))
        mean = S * (TILDE_MW + (TILDE_MW7 - TILDE_MW) * k)
        wmax = mean / (TILDE_ENDS + (1 - TILDE_ENDS) * 2 / math.pi)
        return stroke(p, lambda t: wmax * (TILDE_ENDS + (1 - TILDE_ENDS) * math.sin(math.pi * t)))
    if TILDE_OPT == "b":
        W, H = XH * TILDE_W, XH * TILDE_H
        p = cubic((0, H * 0.30), (W * 0.28, H * 1.15), (W * 0.60, -H * 0.18), (W, H * 0.72))
        return _stroke(p, widths([(0.0, 0.62 * TILDE_WT), (0.5, 1.0 * TILDE_WT), (1.0, 0.62 * TILDE_WT)]))
    p = cubic((0, ACC_H * 0.30), (ACC_W * 0.28, ACC_H * 1.15), (ACC_W * 0.60, -ACC_H * 0.18), (ACC_W, ACC_H * 0.72))
    return _stroke(p, widths([(0.0, 0.62), (0.5, 1.0), (1.0, 0.62)]))

# 2026-09-28 -- THE MACRON, AT THE REFERENCES' LENGTH (issue sweep; the same
# follow-up). 172 x 32 units in the built Regular -- 0.38 of the x-height long
# and 0.43 of the stem thick -- against Pagella 0.67 xh / 0.54, Georgia 0.70 /
# 0.58, Flanker 0.72 / 0.46 (their italics alike); a-macron had 0-3 dark
# pixels at 8-10 pt on the X3 against their 4-7. MACRON_OPT b draws it MACRON_W
# of the x-height long at MACRON_TH of today's weight. a = today.
MACRON_OPT = os.environ.get("ALBO_MACRON_OPT", "b" if ACC_FIT else "a")   # round 450: b ships
MACRON_W = float(os.environ.get("ALBO_MACRON_W", 0.68 if ACC_FIT else 0.62))
MACRON_TH = float(os.environ.get("ALBO_MACRON_TH", 1.25))

@glyph('¯')      # macron
def g_macron(c):
    if MACRON_OPT == "b":
        th = TH_H * ACC_LIGHT * MACRON_TH
        return bar(0, XH * MACRON_W * MARK_IT_K, th / 2, th)
    return bar(0, ACC_W * 1.04, TH_H * ACC_LIGHT / 2, TH_H * ACC_LIGHT)

@glyph('˘')      # breve
def g_breve(c):
    """A cup: heavier at the bottom of the turn, the two ends cut."""
    W, H = BREVE_W * MARK_IT_K, _KH
    p = cubic((0, H), (W * 0.12, -H * 0.16), (W * 0.88, -H * 0.16), (W, H))
    return _stroke(p, widths([(0.0, 0.70), (0.5, 1.12), (1.0, 0.70)]))

@glyph('\u00a8')      # dieresis
def g_dieresis(c):
    """Two dots, separated by 1.05 of a dot's DIAMETER. The separation scales
    with the DOT and not with the accent box: ACC_W is a fixed proportion of
    the x-height, so at the Bold's stem the two dots grew into each other and
    the mark merged into a single blob -- every German and Swedish umlaut, in
    the bold. Found by the cross-weight contour count, which is what that
    check exists for."""
    # ROUND 369 -- AND THEY WERE ALL BUT TOUCHING. Owner 2026-09-23: *"center
    # dieresis optically and give them enough space between."* Measured on a
    # real letter against six references (`cmp_marks.py`), the white between
    # Albo's two dots was 0.104 of a dot's own diameter where they run
    # 0.642-1.250 -- not tight, effectively closed, and at 13 px the pair
    # quantised to one bar. DIE_GAP is the centre-to-centre distance in dot
    # RADII, so white/dot is (DIE_GAP - 2) / 2: the shipped 2.1 is 0.05 and
    # the references' middle is 3.7.
    r = TIT_R * 0.92 * DOT_K * DOT_W * DOT_IT_K
    gap = (2 * r + DIE_WHITE * DIE_IT_W) if ACC_FIT else r * DIE_GAP   # centre to centre
    return geom.ink([dot(r, r, r), dot(r + gap, r, r)])

@glyph('˙')      # dot above
def g_dotaccent(c):
    r = TIT_R * 0.92 * DOT_K * DOT_W * DOT_IT_K
    return dot(r, r, r)

@glyph('˚')      # ring above
def g_ring(c):
    """A small bowl, its counter open enough to survive 13 pt: the ring is
    the family's, at a radius that makes the mark ACC_H*1.25 tall."""
    ry = _KH * RING_K; rx = ry * 1.02
    # ROUND 268 -- THE RING'S COUNTER COLLAPSES AT THE HEAVY END, the same
    # class as the theta's and the phi's (round 267): the radius is on the
    # accent grid (ACC_H, which does not move with weight) and the wall is
    # 0.62 of the pen, which does. At the 700 the wall is 72 units on a
    # 93-unit radius and the counter is two slits 7 and 8 units wide (the
    # --all sweep, both styles); at the 900 it would be gone, and the a-ring
    # and u-ring would carry a dot. The wall is scaled by min(1, 84/S) above
    # the stem the mark was drawn at, exactly as the Greek bowls are; at and
    # under 84 it is as drawn, so the 200 and the 400s are byte-identical.
    solid, *_ = ring(rx, ry, rx, ry, k=BOWL_K, w_scale=0.62 * min(1.0, 84.0 / S), floor=HAIR * 0.9)
    return solid

@glyph('˝')      # double acute
def g_hungarumlaut(c):
    if ACUTE_OPT == "b":   # 2026-09-28, see ACUTE_OPT: two of the grave's strokes, reflected
        import shapely.affinity as aff
        one = _mirror(_stroke(line((0, _KH), (_KW * 0.58, 0)), light=ACC_LIGHT * DA_WT))
        w = one.area / max(1.0, math.hypot(_KW * 0.58, _KH))   # the stroke's mean width
        ang = math.atan2(_KH, _KW * 0.58)
        # the two strokes are parallel: their centres a horizontal `dx` apart
        # leave (dx sin(ang) - w) of white between them
        dx = w * (1.0 + DA_WHITE) / math.sin(ang)
        if DA_TW:   # round 450: spread to the references' whole width, never under DA_WHITE of white
            ow = one.bounds[2] - one.bounds[0]
            dx = max(dx, DA_TW * MARK_IT_K * XH - ow)
        return geom.ink([one, aff.translate(one, dx, 0)])
    a = _stroke(line((0, 0), (ACC_W * 0.58, ACC_H)))
    b = _stroke(line((ACC_W * 0.52, 0), (ACC_W * 1.10, ACC_H)))
    return geom.ink([a, b])

@glyph('¸')      # cedilla (hangs below; drawn from y = 0 down)
def g_cedilla(c):
    """A hook leaving the letter's foot, turning left and closing. Its top
    overlaps into the base by a hair so the two read as one stroke."""
    d = CED_D * XH; W = ACC_W * CED_X
    p = cubic((W * 0.46, 8), (W * 0.46, -d * 0.42), (W * 0.86, -d * 0.40), (W * 0.70, -d * 0.78))
    q = cubic((W * 0.70, -d * 0.78), (W * 0.52, -d * 1.10), (W * 0.16, -d * 0.86), (W * 0.10, -d * 0.60))
    return geom.ink([_stroke(p, widths([(0.0, 0.92), (1.0, 0.72)]), cut0=None, cut1=None),
                     _stroke(q, widths([(0.0, 0.72), (1.0, 0.46)]), cut0=None)])

# ROUND 451 -- THE OGONEK AS A HOOK (owner: "improve ąę tails", "ąę need more
# hooky tails"). It was a thin stroke running down and to the RIGHT from the
# foot, a wiggle that read as detached. Every reference (Pagella, Georgia,
# Times, Coelacanth) grows a sturdy hook out of the letter's foot that sweeps
# down and LEFT, turns at the bottom and curls back RIGHT to a fine tip: heavy
# at the root, tapering out. The stroke starts at the mark's local x = 0, the
# ATTACH point build.py hangs it from; it overlaps up into the foot so no
# hairline of white opens at small sizes. OGO_HOOK is how far the tip curls
# back up; OGO_W the root's width x the stem, easing at the 700.
OGO_HOOKED = int(os.environ.get("ALBO_OGO_HOOKED", 1 if ACC_FIT else 0))
OGO_HOOK = float(os.environ.get("ALBO_OGO_HOOK", 0.60))
OGO_W = float(os.environ.get("ALBO_OGO_W", 0.90))
OGO_W7 = float(os.environ.get("ALBO_OGO_W7", 0.66))
OGO_HD = float(os.environ.get("ALBO_OGO_HD", 0.52))          # the hook's depth below the foot, x xh
OGO_BOWL = float(os.environ.get("ALBO_OGO_BOWL", 0.85))      # how far the hook sweeps left of its attach, x the depth
OGO_TIP = float(os.environ.get("ALBO_OGO_TIP", 0.42))        # how far right of the attach its tip ends, x the depth

# ROUND 452 -- THE OGONEK, TRACED. Owner 2026-09-30: *"ogonek needs to be traced and
# redone entirely"*. Round 451's hook was a cubic of five dials with a width table laid
# along it, and it read as constructed. This one is the REFERENCE's own stroke: where the
# pen's center went and how wide it was there, traced off the a-ogonek of TeX Gyre Pagella
# (GUST Font License: a derivative under another name is permitted) by
# `instruments/ogonek_trace.py` into `ogonek_traced.py` -- a skeleton and an inscribed-circle
# width, not a copy of a bezier -- and drawn here by Albo's own stroke(). The path is in
# x-heights and the width in the reference's own stem, so the mark keeps its letter's colour
# at Albo's lighter stem; the 400 and the 700 traces (Pagella Regular/Bold, Italic/Bold
# Italic) blend by the stem as every weight-dependent dial here does. 'mean' is the same
# trace averaged over Pagella, Georgia and Times at equal arc length.
#   ALBO_OGO_TRACE  'pagella' | 'mean' | '' (round 451's constructed hook)
#   ALBO_OGO_TW     width scale on the traced profile;  ALBO_OGO_TS  size scale on the path
#   ALBO_OGO_TTIP   the tip's floor, x the stem
# THE ROOT: the trace starts where the mark leaves the letter, on the baseline, and the mark
# is cut FLAT there: its top IS the baseline, and build.py sets it against the letter's foot
# so that the letter's ink covers the whole of that top edge. A composite is rasterized as
# one outline, so two contours that abut leave no seam. (A plug reaching up into the foot
# poked out beside every foot that is not flat on the line -- the A's oblique leg, the italic
# a's lifting exit; ALBO_OGO_TROOT > 0 restores one, as a trapezoid narrowing upward.)
OGO_TRACE = os.environ.get("ALBO_OGO_TRACE", "pagella" if ACC_FIT else "")
OGO_TW = float(os.environ.get("ALBO_OGO_TW", 1.0))
OGO_TS = float(os.environ.get("ALBO_OGO_TS", 1.0))
OGO_TTIP = float(os.environ.get("ALBO_OGO_TTIP", 0.20))
OGO_TOP = float(os.environ.get("ALBO_OGO_TROOT", 0.0))      # the traced root's cut, x xh above its baseline (build.py reads the same)

def _catmull(P, n=8):
    """centripetal-free uniform Catmull-Rom through P, n points per span, ends held"""
    Q = [P[0]] + list(P) + [P[-1]]; out = []
    for i in range(1, len(Q) - 2):
        p0, p1, p2, p3 = Q[i - 1], Q[i], Q[i + 1], Q[i + 2]
        for j in range(n):
            u = j / n; u2 = u * u; u3 = u2 * u
            out.append(tuple(0.5 * (2 * p1[k] + (-p0[k] + p2[k]) * u + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * u2
                                    + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * u3) for k in (0, 1)))
    out.append(P[-1]); return out

def _cr_fn(keys):
    """f(t) through (t, w) keys: Catmull-Rom on the values, linear in t within a span"""
    T = [k[0] for k in keys]; W = [k[1] for k in keys]; n = len(keys)
    def f(t):
        if t <= T[0]: return W[0]
        if t >= T[-1]: return W[-1]
        i = max(0, min(n - 2, next(j for j in range(n - 1) if T[j + 1] >= t)))
        u = (t - T[i]) / (T[i + 1] - T[i]) if T[i + 1] > T[i] else 0.0
        p0, p1, p2, p3 = W[max(i - 1, 0)], W[i], W[i + 1], W[min(i + 2, n - 1)]
        return 0.5 * (2 * p1 + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u + (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3)
    return f

def _brush(pts, wf):
    import shapely.geometry as _sg
    from shapely.ops import unary_union
    n = len(pts) - 1
    disks = [_sg.Point(p).buffer(max(wf(i / n), 0.5) / 2, quad_segs=12) for i, p in enumerate(pts)]
    g = unary_union([disks[i].union(disks[i + 1]).convex_hull for i in range(n)])
    # the far end CUT SQUARE across the path, as the references' tips are: the last disk's
    # round cap is what lies past the last sample. Only the cap's own neighborhood is cut --
    # a hook curls back, so a whole half-plane past the tip also holds the root (it took the
    # top off the 'mean' italic's mark, 20 units of it)
    (ax, ay), (bx, by) = pts[-2], pts[-1]; L = math.hypot(bx - ax, by - ay); tx, ty = (bx - ax) / L, (by - ay) / L
    r = max(wf(1.0), 0.5) / 2 + 0.25      # the cap: half the tip's width either side, half ahead
    cap = _sg.Polygon([(bx - ty * r, by + tx * r), (bx + ty * r, by - tx * r),
                       (bx + ty * r + tx * r, by - tx * r + ty * r), (bx - ty * r + tx * r, by + tx * r + ty * r)])
    return g.difference(cap)

def _ogo_traced():
    from .ogonek_traced import TABLES
    import shapely.geometry as _sg
    cut = 'I' if pen.ITALIC else 'R'
    lo, hi = TABLES[OGO_TRACE][cut + '400'], TABLES[OGO_TRACE][cut + '700']
    k = max(0.0, min(1.0, (S - 66.9) / 49.1))
    pts = [(XH * OGO_TS * (a[0] + (b[0] - a[0]) * k), XH * OGO_TS * (a[1] + (b[1] - a[1]) * k)) for a, b in zip(lo, hi)]
    ws = [S * OGO_TW * max(OGO_TTIP, a[2] + (b[2] - a[2]) * k) for a, b in zip(lo, hi)]
    # the root runs on up its own tangent, far enough that its square end clears the cut
    (x0, y0), (x1, y1) = pts[0], pts[1]
    ux, uy = x0 - x1, y0 - y1; n = math.hypot(ux, uy); ux, uy = ux / n, uy / n
    up = (OGO_TOP * XH + ws[0]) / max(uy, 0.2)
    head = [(x0 + ux * up * f, y0 + uy * up * f) for f in (1.0, 0.5)]
    path = _catmull(head + pts)       # a smooth curve through the samples, never the polygon between them
    seg = [0.0]
    for (ax, ay), (bx, by) in zip(path, path[1:]): seg.append(seg[-1] + math.hypot(bx - ax, by - ay))
    t = [v / seg[-1] for v in seg]
    # the widths ride the samples' own arc-length positions along the smoothed path
    seg0 = [0.0]
    for (ax, ay), (bx, by) in zip(head + pts, (head + pts)[1:]): seg0.append(seg0[-1] + math.hypot(bx - ax, by - ay))
    t0 = [v / seg0[-1] for v in seg0]
    keys = [(t0[0], ws[0]), (t0[1], ws[0])] + list(zip(t0[2:], ws))
    # a SPLINE through the widths, not widths(): its smoothstep goes flat at every key, so 25
    # keys terraced the stroke's edges into scallops wherever the width changed
    dense = geom.resample(path, 4.0)                                  # 4-unit samples: the hook's inner curve is tight
    # A BRUSH SWEEP: the union of the hulls of consecutive width-circles along the path, which
    # is the stroke's exact envelope on both sides. Where the hook turns tighter than its
    # half-width, ONE offset polygon's inner edge folds back on itself: stroke()'s unfold left
    # a kink there, capping the width pulled a chin out of the outer edge, and stroke(pieces=)
    # pairs the two sides by index after unfolding them separately, so a fold skews every
    # piece after it (the Bold Italic's tip came out a long slanted wedge). The sweep resolves
    # the fold into the clean inner corner the references have; its far end is the round of
    # the tip's own width.
    g = _brush(dense, _cr_fn(keys))
    # ABOVE THE BASELINE the mark is only a plug into the foot: its own baseline section,
    # narrowing upward. The root's extension runs up-right while a leg or a foot it hides in
    # runs up-left, so a plain flat cut left a sliver poking out beside the A's leg and the
    # italic a's exit (instrument: r452 poke check, the mark's ink above y = 0 not under the base)
    top = OGO_TOP * XH
    if top <= 0:
        return g.intersection(_sg.box(-1e5, -1e5, 1e5, 0.0)).buffer(0)
    sec = g.intersection(_sg.box(-1e5, -0.5, 1e5, 0.5)).bounds
    xl, xr = sec[0], sec[2]; ins = 0.5 * top
    plug = _sg.Polygon([(xl, -1.0), (xr, -1.0), (xr - ins, top), (xl + ins, top)])
    below = g.intersection(_sg.box(-1e5, -1e5, 1e5, 0.0))
    return below.union(g.intersection(plug)).buffer(0)

@glyph('˛')      # ogonek (hangs below)
def g_ogonek(c):
    if OGO_TRACE:
        import shapely.affinity as _aff
        g = _ogo_traced()
        return _aff.translate(g, -g.bounds[0], 0)      # ink from x = 0, as every mark is drawn
    if OGO_HOOKED:
        d = OGO_HD * XH
        k = max(0.0, min(1.0, (S - 66.9) / 49.1))
        w0 = S * (OGO_W + (OGO_W7 - OGO_W) * k)
        p = cubic((0, 0), (-d * OGO_BOWL, -d * 0.28), (-d * OGO_BOWL * 0.62, -d * 1.26), (d * OGO_TIP, -d * (1.0 - OGO_HOOK)))
        g = stroke(p, widths([(0.0, w0 * 0.86), (0.30, w0), (0.70, w0 * 0.86), (1.0, w0 * 0.24)]))
        import shapely.affinity as _aff
        return _aff.translate(g, -g.bounds[0], 0)      # ink from x = 0, as every mark is drawn
    d = OGO_D * XH; W = ACC_W * OGO_X
    p = cubic((W * 0.30, 8), (W * 0.30, -d * 0.55), (W * 0.86, -d * 0.55), (W * 0.78, -d * 1.02))
    return _stroke(p, widths([(0.0, 0.88), (1.0, 0.44)]), cut0=None)

# The caron of d t l and L: Czech and Slovak set it as an apostrophe at the
# letter's right shoulder, not as a wedge over the ascender. Drawn as its
# own mark so the composite table can name it.
@glyph('ʹ')      # (spacing modifier prime, borrowed as the caron.alt slot)
def g_caronalt(c):
    w = S * 0.34
    # round 450: held at the round-99 accent box -- the apostrophe-caron was not
    # measured against the references in round 450's resize, so it keeps its size
    p = line((w / 2, 0), (w / 2 - S * 0.12, 0.26 * XH * 1.85))   # round 100: tall enough to read as an apostrophe at 13 pt; at 1.22 it was a tick
    return _stroke(p, widths([(0.0, 0.55), (1.0, 1.10)]), cut0=CUT)

# Dotless bases: í ì î ï and every accented i are the i WITHOUT its dot.
@glyph('ı')      # dotless i
def g_dotlessi(c):
    from ..primitives import stem
    return stem(S / 2, 0, c["xh"], top='left', foot='both')

@glyph('ȷ')      # dotless j
def g_dotlessj(c):
    from .stems import g_j
    from .. import geom as _g, pen as _pen
    from . import GLYPHS as _G
    import shapely.geometry as _sg
    # ROUND 392 -- THE ITALIC's DOTLESS j IS THE ITALIC j. This called the
    # ROMAN j in both styles, so the italic ȷ and ĵ were the roman letter
    # sheared -- a different tail from the italic j beside them, and one that
    # still carried the step R26 fixed on the roman only (5.0 units at the
    # Italic (59, -191), 6.9 at the BoldItalic, `cmp_jogs.py`, round 385's
    # small list). In the italic it is now `GLYPHS['j']` (aldine `a_j`) with
    # its dot taken off, exactly as the roman's is.
    full = _G['j'](c) if _pen.ITALIC else g_j(c)
    # the dot is the small disjoint piece; keep everything else
    parts = list(full.geoms) if hasattr(full, 'geoms') else [full]
    if len(parts) > 1:
        parts = sorted(parts, key=lambda p: -p.area)[:-1]
        return _g.ink(parts)
    return full
