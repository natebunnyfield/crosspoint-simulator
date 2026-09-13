"""The 30 marks, on the record's geometry (round 41: fitted on their full
extent), the & and @ real glyphs (round 42)."""
import math
import shapely.affinity as aff
from . import glyph
from .. import geom, pen
from ..geom import cubic, line, superellipse, catmull
from ..primitives import stem, ring, stroke, pen_widths, widths, dot, wedge, diagonal, bar
from ..pen import S, XH, DESC, OVER, TH_V, TH_H, HAIR, CUT, BOWL_K, WL, WD, DROP
from .rounds import o_ring
from .stems import g_a, DOT_R

def CAP(c): return c["cap"]

# Owner 2026-09-13: "line up punctuation vertically (including the quotes
# being misaligned)." The rule applied, after checking the guide and NOTES
# for an existing ruling and finding none for the marks (round 36 rules only
# the i/j dot, "a dot 1.24 stems across reads as the stem's weight"): every
# ROUND dot in the punctuation set -- period, comma's head, both colon dots,
# both semicolon dots, the exclamation dot, the question dot, and the three
# ellipsis dots -- is the SAME size, and that size is the family's own
# established dot (`stems.DOT_R`, 0.62 stem), not a one-off per glyph as
# before (period at 0.08 cap, everything else at 0.55 stem -- two different
# sizes on the same baseline). Every BASELINE dot (. , : ; ! ? and the
# ellipsis) sits with its bottom exactly on the baseline (y=0). The colon's
# and semicolon's upper dot sits with its TOP exactly on the x-height (the
# current code's placement, kept as the rule since nothing else names one).
# The comma's body is the period's dot exactly (bottom at 0), its tail below.
# The quotes (straight and curly, single and double) all share the same TOP
# (the cap height) and the same body height: the curly ones are the comma's
# own dot+tail construction turned to sit at the top instead of the
# baseline (same DOT_R body), and the straight quotes' stroke is shortened to
# the SAME body height (2 x DOT_R) so nothing about a quote's size depends on
# whether it is straight or curly. The double marks stay 1.3 stem apart
# (unchanged; already equal between the straight and curly pairs).
@glyph('.')
def g_period(c): return dot(DOT_R, DOT_R, DOT_R)
def comma_tail(x, y, up=True, w0=0.9, w1=0.3):
    if up: tail = cubic((x + S * 0.1, y - S * 0.35), (x + S * 0.1, y - S * 1.05), (x - S * 0.3, y - S * 1.45), (x - S * 0.6, y - S * 1.75))
    # mirrored in x only (round 51 flipped y too, sending the left quote's
    # tail UP past the cap height instead of down like a real turned comma --
    # the defect behind the misaligned "‘"/"“"): the tail still descends,
    # it just curls to the right instead of the left.
    else:  tail = cubic((x - S * 0.1, y - S * 0.35), (x - S * 0.1, y - S * 1.05), (x + S * 0.3, y - S * 1.45), (x + S * 0.55, y - S * 1.75))
    return stroke(tail, pen_widths(tail, lambda t: w0 - (w0 - w1) * t))   # round 51: the pen x (0.9 - 0.6 t)
@glyph(',')
def g_comma(c): return geom.ink([dot(DOT_R, DOT_R, DOT_R), comma_tail(DOT_R, DOT_R)])
@glyph(':')
def g_colon(c): return geom.ink([dot(DOT_R, DOT_R, DOT_R), dot(DOT_R, XH - DOT_R, DOT_R)])
@glyph(';')
def g_semicolon(c): return geom.ink([dot(DOT_R, DOT_R, DOT_R), comma_tail(DOT_R, DOT_R), dot(DOT_R, XH - DOT_R, DOT_R)])
@glyph('!')
def g_exclam(c):
    C = CAP(c); x = DOT_R; y0 = 2 * DOT_R + 0.8 * S   # same gap above the dot as round 51's (0.8 stem)
    return geom.ink([dot(x, DOT_R, DOT_R), stroke(line((x, y0), (x, C)), pen_widths(line((x, y0), (x, C)), lambda t: 0.55 + 0.5 * t), cut1=CUT)])
@glyph('?')
def g_question(c):
    """Owner 2026-09-13: 'both ? and & need to be made flowing and elegant
    while still clean counterspace.' The old hook was a 7-point catmull
    spline with two collinear-ish points stacked on the same x right above
    the tail's end -- a redundant vertex catmull could not smooth through,
    which is exactly where a visible kink/nub showed at 600 px. Redrawn on
    6 points, none redundant, a single flowing gesture from the terminal
    (beak-like, the family's pen cut) up through the top, wide down the
    right shoulder for an open counter, and back in a gentler curve to the
    tail; the width profile ramps smoothly (no plateau-then-jump) and
    THINS into the tail instead of flaring, so the stroke reads as one
    calligraphic pull, not stacked pieces. Dot aligned by the mark rule
    (DOT_R, bottom at 0)."""
    C = CAP(c); w = 380
    end_y = C * 0.2 + max(0.0, (S - 94) * 2.2)   # above the shipping weight the hook stops higher, clear of the dot (identical at 94)
    hook = catmull([(w * 0.14, C * 0.60), (w * 0.00, C * 0.86), (w * 0.32, C * 1.00), (w * 0.70, C * 0.92), (w * 0.60, C * 0.52), (w * 0.5, end_y)], tension=0.62)
    return geom.ink([dot(w * 0.5, DOT_R, DOT_R), stroke(hook, pen_widths(hook, widths([(0.0, 0.40), (0.30, 1.0), (0.58, 0.95), (1.0, 0.55)])), cut0=CUT, cut1=CUT)])
QUOTE_BODY = 2 * DOT_R   # straight and curly quotes share this body height, top-aligned to CAP
@glyph("'")
def g_quotesingle(c): C = CAP(c); return stroke(line((S * 0.5, C - QUOTE_BODY), (S * 0.5, C)), TH_V * 0.8, cut0=CUT)
@glyph('"')
def g_quotedbl(c):
    C = CAP(c); return geom.ink([stroke(line((S * 0.5 + i * S * 1.3, C - QUOTE_BODY), (S * 0.5 + i * S * 1.3, C)), TH_V * 0.8, cut0=CUT) for i in (0, 1)])
def quote(c, x, up):
    """The curly quotes: the comma's own dot+tail (same DOT_R body as every
    other mark), turned to hang from the top instead of sitting on the
    baseline -- top of the dot flush with CAP, matching the straight
    quotes' top and body height exactly."""
    C = CAP(c); y = C - DOT_R
    return geom.ink([dot(x, y, DOT_R), comma_tail(x, y, up, 0.85, 0.3)])
@glyph('’')
def g_quoteright(c): return quote(c, S * 0.7, True)
@glyph('‘')
def g_quoteleft(c): return quote(c, S * 0.7, False)
@glyph('”')
def g_quotedblright(c): return geom.ink([quote(c, S * 0.7, True), quote(c, S * 2.0, True)])
@glyph('“')
def g_quotedblleft(c): return geom.ink([quote(c, S * 0.7, False), quote(c, S * 2.0, False)])
def dash(c, length): C = CAP(c); return stroke(line((0, C * 0.34), (length * C, C * 0.34)), TH_H)
@glyph('-')
def g_hyphen(c): return dash(c, 0.37)
@glyph('–')
def g_endash(c): return dash(c, 0.72)
@glyph('—')
def g_emdash(c): return dash(c, 1.41)
def paren(c, left):
    C = CAP(c); d = DESC; r = 150
    if left: pts = superellipse(r, (C - d) / 2, r, (C + d) / 2 + 16, math.radians(105), math.radians(255), 2.2)
    else: pts = superellipse(0, (C - d) / 2, r, (C + d) / 2 + 16, math.radians(75), math.radians(-75), 2.2)
    return stroke(pts, pen_widths(pts, lambda t: 0.6 + 0.4 * math.sin(math.pi * t)), cut0=CUT, cut1=CUT)
@glyph('(')
def g_parenleft(c): return paren(c, True)
@glyph(')')
def g_parenright(c): return paren(c, False)
def bracket(c, left):
    C = CAP(c); d = DESC; w = 180; x = S * 0.4 if left else w - S * 0.4
    x0, x1 = (x, w) if left else (0, x)
    return geom.ink([stroke(line((x, -d), (x, C)), TH_V * 0.85), stroke(line((x0, C - TH_H / 2), (x1, C - TH_H / 2)), TH_H), stroke(line((x0, -d + TH_H / 2), (x1, -d + TH_H / 2)), TH_H)])
@glyph('[')
def g_bracketleft(c): return bracket(c, True)
@glyph(']')
def g_bracketright(c): return bracket(c, False)
@glyph('/')
def g_slash(c): C = CAP(c); p = line((0, -DESC * 0.4), (330, C)); return stroke(p, pen_widths(p, lambda t: 0.8), cut0=CUT, cut1=CUT)
@glyph('\\')
def g_backslash(c): C = CAP(c); p = line((0, C), (330, -DESC * 0.4)); return stroke(p, pen_widths(p, lambda t: 0.8), cut0=CUT, cut1=CUT)
@glyph('*')
def g_asterisk(c):
    C = CAP(c); cx, cy = 200, C * 0.78; r = 150; parts = []
    for k in range(5):
        a = math.pi / 2 + k * 2 * math.pi / 5; p = line((cx, cy), (cx + r * math.cos(a), cy + r * math.sin(a)))
        parts.append(stroke(p, pen_widths(p, lambda t: 0.75), cut1=CUT))
    return geom.ink(parts)
@glyph('+')
def g_plus(c):
    y = XH * 0.55; w = 420
    return geom.ink([stroke(line((0, y), (w, y)), TH_H * 0.9), stroke(line((w / 2, y - w / 2), (w / 2, y + w / 2)), TH_V * 0.9)])
@glyph('=')
def g_equal(c):
    y = XH * 0.55; w = 420; g = S * 1.1
    return geom.ink([stroke(line((0, y - g / 2), (w, y - g / 2)), TH_H), stroke(line((0, y + g / 2), (w, y + g / 2)), TH_H)])
@glyph('&')
def g_ampersand(c):
    """Round 68's #10 `round_bowl` (owner 2026-09-13, round 72: "round_bowl
    wins"): the open spiral -- the spur running on as the loop's left side,
    one stroke -- on the o's bowl, the loop 1.1 wide, ending at 0.54 C.
    Drawn by ampersands.bred, whose round_bowl dials from VARIANTS2 are the
    base (so the shipping & and the variant page cannot drift on those);
    two dials are nudged from here per the owner's 2026-09-13 ask ("both ?
    and & need to be made flowing and elegant while still clean
    counterspace") WITHOUT touching ampersands.py:
    - `cross` 41 -> 41.2: `bred`'s width-blend pinches the stroke toward
      zero right where the diagonal meets the loop, and at exactly 41 that
      pinch coincided with a tight turn in the catmull spine -- together
      they cut a visible V-notch into the crossing at 600 px (never at
      41.2, checked across 41.0-44.0; the notch is gone as soon as the
      pinch and the turn stop lining up, and a bigger nudge only bends the
      diagonal's angle for no further gain). This is the one point in the
      glyph two strokes visually cross, so "continuous curvature at the
      crossing" reads as no notch there, not a literal shared tangent.
    - `arm_end` 'cut' -> 'beak': the old value named a plain square end
      (the `bred` code only shears 'beak' and 'up'; nothing in the 'open'
      branch ever gave 'cut' a cut), which is what "abrupt" meant here. The
      family's own C/G/S beak on the arm's rising exit reads as a lifted
      pen, not a chop -- the one construction bred() offers that isn't a
      plain wedge or a flat face on a stroke this thin.
    Measured at 54 px on the four-level render (`outlines.cmp.proof.eink`,
    flood-filled for enclosed white): loop 183, bowl 86 px, both above the
    shipping 182 / 83 (the render is unchanged by 'cross'/'arm_end' at any
    other size checked). `spur_foot`, `point`, `bowl`, `loop`, `arm`,
    `top` -- the lower bowl's own construction and the spur's hooked foot
    -- are untouched; the join there already reads as one gesture."""
    from .ampersands import bred, VARIANTS2
    dials = dict(dict(VARIANTS2)['round_bowl'].dials)
    dials.update(cross=41.2, arm_end='beak')
    return bred(c, **dials)
@glyph('%')
def g_percent(c):
    C = CAP(c); r = 120; p = line((60, 0), (440, C))
    parts = [stroke(p, pen_widths(p, lambda t: 0.75), cut0=CUT, cut1=CUT)]
    for cx, cy in ((r + 10, C - r), (620 - r, r)):
        parts.append(ring(cx, cy, r + TH_V / 2, r + TH_H / 2, k=2.0)[0])   # r is the CENTERLINE radius (round 51): counter 163 of 317
    return geom.ink(parts)
@glyph('#')
def g_numbersign(c):
    C = CAP(c); w = 480; parts = []
    for x in (w * 0.32, w * 0.68): parts.append(stroke(line((x - w * 0.06, 0), (x + w * 0.06, C)), TH_V * 0.75))
    for y in (C * 0.35, C * 0.65): parts.append(stroke(line((0, y), (w, y)), TH_H))
    return geom.ink(parts)
AT_A_SCALE = 0.80   # owner 2026-09-13: "simple a within the usual at symbol spiral" -- the family's
                    # own lowercase a (stems.g_a), scaled down to clear the spiral on every side
@glyph('@')
def g_at(c):
    """Owner 2026-09-13: 'redo @ to not have a top stroke over, just simple
    a within the usual at symbol spiral. Today's @ has a stroke running
    over the top of the inner a.' That stroke was the old single-storey
    a's hood, drawn as its own cubic from the stem's top back over toward
    the bowl -- a face independent of the ring, crossing above the inner
    shape. Redrawn: the inner glyph is the family's real two-storey a
    (stems.g_a, unmodified), scaled down and centred so nothing but the
    spiral surrounds it. The spiral itself is Van den Keere's sweep (round
    42, kept): it starts at -62 deg (the a's lower right, where its stem
    foot sits), sweeps down, around the left, over the top, and ends open
    at -400 deg (back on the right, above the start) with the family's pen
    cut as its terminal -- no stroke crosses the a."""
    C = CAP(c); rx = C * 0.52; ry = C / 2 + OVER - TH_H / 2; cx = rx + S / 2; cy = C / 2
    a_raw = g_a(dict(xh=XH, wf=1.0))
    ax0, ay0, ax1, ay1 = a_raw.bounds
    acx, acy = (ax0 + ax1) / 2, (ay0 + ay1) / 2
    a_glyph = aff.translate(aff.scale(a_raw, xfact=AT_A_SCALE, yfact=AT_A_SCALE, origin=(acx, acy)), cx - acx, cy - acy)
    ringc = superellipse(cx, cy, rx, ry, math.radians(-62), math.radians(-62 - 338), BOWL_K)
    rg = stroke(ringc, pen_widths(ringc, widths([(0.0, 0.1), (0.08, 0.85), (0.86, 0.85), (1.0, 0.42)])), cut1=CUT, pieces=True)
    return geom.ink([a_glyph, rg])
@glyph('_')
def g_underscore(c): return stroke(line((0, -DESC * 0.5), (500, -DESC * 0.5)), TH_H)
@glyph('…')
def g_ellipsis(c): return geom.ink([dot(DOT_R + i * S * 2.4, DOT_R, DOT_R) for i in range(3)])
