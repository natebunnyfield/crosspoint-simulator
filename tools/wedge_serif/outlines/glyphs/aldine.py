"""THE ALDINE LOWERCASE, drawn again from nothing (round 115).

Owner, three times, the last plainly: *"remake lowercase italic from scratch to
match the scan. I cannot be clearer, stop ignoring this instruction."* Rounds
114 and 114b answered by turning dials on the existing italic -- width,
contrast, serif size, the flick's tip, where the arch branches -- and a dial
cannot change what a letter IS. This module draws the lowercase from Griffo's
1501 shapes instead of adjusting a sheared roman toward them.

Registered ONLY under ALBO_ALDINE=1, so the shipping italic is untouched while
this is judged, and both can be built for the same page.

WHAT THE SCAN SHOWS, and what each of these is built from:

  THE HEAD    an ascender does not end in a flick. It ends in a flat angled
              head that sits ACROSS the stem, entered from the left. That one
              shape is most of the page's texture, because b d h k l are
              everywhere in Latin.
  THE ARCH    branches LOW -- around a third of the way up the stem -- climbs,
              and arches over. It is one movement, not a shoulder turned near
              the top.
  THE FOOT    a short blunt outstroke to the right, with weight in it.
  THE BOWLS   small, round and sitting LOW in the x-height band, not filling
              it. The a is single-storey with its bowl low against a nearly
              straight stem.
  THE e       a small eye under a bar that slants up hard.

Everything is drawn on the pen, so the contrast is the pen's own; no widths
are declared except where a stroke has to thin against its neighbour.
"""
import math, os
from . import glyph, GLYPHS
from .. import geom, pen
from ..geom import cubic, line, catmull, superellipse
from ..primitives import stroke, pen_widths, widths, ring
from .. import primitives as PR
from ..pen import S, XH, ASC, DESC, OVER, TH_V, TH_H, CUT, BOWL_K

# WHICH ITALIC. Two complete italic lowercases now exist and BOTH are kept
# (owner 2026-09-15: "be sure to make an alternative of the prior italic, then
# we can make this griffo scans one the new, default Albo Italic"):
#
#   classic  glyphs/italic.py -- the branching-arch italic built off the roman,
#            rounds 101-114b. Today's default.
#   aldine   this module -- drawn from the Griffo scans, rounds 114-117c.
#
# Flipping the default is the one word in _DEFAULT below; nothing is deleted
# either way, and the loser stays reachable by name. This module only defines
# the lowercase, so the capitals, figures and marks come from italic.py under
# both settings.
_DEFAULT = "classic"
_WHICH = os.environ.get("ALBO_ITALIC", _DEFAULT).lower()
ON = _WHICH == "aldine" or os.environ.get("ALBO_ALDINE") == "1"

# ---------------------------------------------------------------- CONTRAST
# Owner 2026-09-15: *"needs to have more line contrast. give me options that
# match prior approved contrasts."*
#
# WHY THIS MODULE HAD LESS CONTRAST THAN THE REST OF ALBO, which is the part
# worth understanding: every width in here is DECLARED from a measurement off
# the scan, so these letters bypass `FJORD_CONTRAST` -- the family's own dial --
# completely. Albo's shipping Regular and Italic build at contrast 0.892, and
# `hair = stem x (1 - contrast)` makes that a **9.26:1** pen. The Aldine letters
# as measured are 2.8:1 (the o) and 3.4:1 (the e): a far flatter face sitting
# inside a family that is not flat. Griffo's page really is that low-contrast
# at this size -- but matching the source's contrast and matching Albo are two
# different goals, and this is Albo.
#
# The prior APPROVED contrasts, from the family's own rulings, converted:
#
#   FJORD_CONTRAST 0.60  ->  2.50:1   round 53
#   FJORD_CONTRAST 0.80  ->  5.00:1   round 62's sliders; Bold ships here
#   FJORD_CONTRAST 0.892 ->  9.26:1   the SHIPPING Regular and Italic
#   FJORD_CONTRAST 0.95  -> 11.15:1   round 65, "set default to .95 contrast"
#
# ALBO_ALD_CON names a target thick:thin ratio, and the transform ANCHORS ON
# THE THICK -- the family's own model, `hair = stem x (1 - contrast)`: the stem
# is held and the hair thins.
#
#     w' = hi * (w / hi) ** gamma,   gamma = ln(target) / ln(hi / lo)
#
# so w'=hi at the thick and hi/target at the thin, with the order of every
# stroke between them preserved. A first version anchored on the MEAN instead,
# which fattened the thicks as much as it thinned the thins: by the 0.892 arm
# the o was a black blob with a lens-shaped slit for a counter. More contrast
# should not mean more ink -- it means less, in the thins only.
# 0 leaves every letter exactly as measured off the page.
# CONTRAST IS PER LETTER, not one number for the module. Owner 2026-09-15,
# after a global switch to C moved the o off the arm he had already set it to:
# *"o was set to D contrast. you are confusing things."* He is right -- "use C"
# was said about the a, and "e needs C too" about the e, and neither was a
# ruling on the o. The ledger of what is set where is docs/albo-aldine-metrics.md.
ALD_CON = float(os.environ.get("ALBO_ALD_CON", 9.26))      # the module default: arm D
CON_A = float(os.environ.get("ALBO_ALD_CON_A", 5.00))      # the a: arm C
CON_E = float(os.environ.get("ALBO_ALD_CON_E", 5.00))      # the e: arm C
CON_O = float(os.environ.get("ALBO_ALD_CON_O", 9.26))      # the o: arm D


def nib(direction_deg, thick, thin, phi=50.0):
    """The measured 50-degree nib, as a width for a stroke running in
    `direction_deg`. A broad pen is fullest across its edge and thinnest along
    it, so the width goes as |sin(direction - phi)|. The o was built on this
    from the start; the e was carrying a HAND LIST instead, near-uniform all
    the way round the loop, which is why it read flat beside the others even
    once the contrast arm had stretched its ratio."""
    import math as _m
    return thin + (thick - thin) * abs(_m.sin(_m.radians(direction_deg - phi)))


def nib_widths(pts, thick, thin, target=None, smooth=9, boost=None):
    """Widths along a path FROM THE NIB, sampled at every point.

    A five-stop list makes a five-sided counter: the inner offset of a stroke
    whose width changes in steps develops flats and corners, and a narrow
    counter shows every one of them. The nib varies continuously, so the
    counter's edge is a curve. `boost` is an optional smooth multiplier
    f(t) -> x, for a letter that wants extra weight somewhere without a step.
    """
    import math as _m
    n = len(pts)
    ws = []
    for i in range(n):
        a_ = pts[max(0, i - 1)]; b_ = pts[min(n - 1, i + 1)]
        d = _m.degrees(_m.atan2(b_[1] - a_[1], b_[0] - a_[0]))
        w = nib(d, thick, thin)
        if boost: w *= boost(i / max(1, n - 1))
        ws.append(w)
    ws = con(ws, target)
    if smooth:                      # a moving average: no step survives it
        ws = [sum(ws[max(0, i - smooth):i + smooth + 1]) /
              len(ws[max(0, i - smooth):i + smooth + 1]) for i in range(n)]
    return ws


def con(ws, target=None):
    """Re-spread a letter's declared widths to ITS OWN target contrast."""
    target = ALD_CON if target is None else target
    if not target or len(ws) < 2:
        return list(ws)
    lo, hi = min(ws), max(ws)
    if lo <= 0 or hi / lo <= 1.0001:
        return list(ws)
    import math as _m
    gamma = _m.log(target) / _m.log(hi / lo)
    return [hi * (w / hi) ** gamma for w in ws]

HEAD_DEG = float(os.environ.get("ALBO_ALD_HEAD_DEG", 24.0))   # the head's slant
HEAD_LEN = float(os.environ.get("ALBO_ALD_HEAD_LEN", 1.15))   # its length, x the stem
HEAD_W = float(os.environ.get("ALBO_ALD_HEAD_W", 0.58))       # its weight, x the stem
FOOT_LEN = float(os.environ.get("ALBO_ALD_FOOT", 0.80))       # the foot's outstroke
BRANCH = float(os.environ.get("ALBO_ALD_BRANCH", 0.34))       # where an arch leaves the stem, x xh
BOWL_TOP = float(os.environ.get("ALBO_ALD_BOWL_TOP", 0.98))   # a bowl's top, x xh -- they sit LOW
FLOOR = float(os.environ.get("ALBO_ALD_FLOOR", 0.30))         # the pen's floor, x the stem


def _w(c):
    return c["wf"]


def st(x, y0, y1, head=False, foot=True, w=1.0, foot_len=None, foot_w=None):
    """A stem. `head` puts the Aldine angled head across its top; `foot` the
    blunt outstroke to the right at the baseline. `foot_len` overrides the
    outstroke's length (x the stem) for a letter whose exit runs longer."""
    parts = [stroke([(x, y0), (x, y1)], S * w)]
    if head:
        a = math.radians(HEAD_DEG); L = S * HEAD_LEN
        dx, dy = math.cos(a) * L, math.sin(a) * L
        p0 = (x - dx * 0.74, y1 - dy * 0.74 - S * 0.06)
        p1 = (x + dx * 0.36, y1 + dy * 0.36 - S * 0.02)
        parts.append(stroke([p0, p1], S * HEAD_W, cut0=CUT))
    if foot:
        L = S * (FOOT_LEN if foot_len is None else foot_len)
        parts.append(stroke(cubic((x - S * w * 0.42, y0 + S * 0.30),
                                  (x - S * w * 0.10, y0 + S * 0.02),
                                  (x + L * 0.42, y0 + S * 0.02),
                                  (x + L, y0 + L * 0.46)),
                            widths([(0.0, S * w * 0.92), (0.5, S * (0.42 if foot_w is None else foot_w * 1.40)),
                                    (1.0, S * (0.30 if foot_w is None else foot_w))])))
    return parts


def arch(c, x0, x1, land=0.74):
    """Branches low off the left stem, climbs, arches over, lands on the right
    one. ONE movement -- the thing a sheared roman cannot do."""
    xh = c["xh"]; ov = pen.ARCH_OVER
    p = cubic((x0, xh * BRANCH),
              (x0 + (x1 - x0) * 0.06, xh * 0.88),
              (x0 + (x1 - x0) * 0.52, xh + ov),
              (x1, xh * land))
    wf = pen_widths(p, floor=S * FLOOR)
    return stroke(p, lambda t: wf(t) * (0.62 + 0.38 * min(1.0, t / 0.34)))


def bowl(c, cx, rx, top=None, ry=None):
    """A small round bowl sitting LOW in the x-height band."""
    xh = c["xh"]; top = (top if top is not None else BOWL_TOP) * xh
    ry = ry if ry is not None else top / 2
    return ring(cx, top - ry, rx, ry + OVER * 0.5, floor=S * FLOOR)[0]


if ON:
    # MEASURED off the i of "rodigium" in griffo-macro.png (the 54 px macro):
    # dot x192-203 rows 471-479, stem and head x187-205 rows 497-553.
    # x-height 56 px, baseline row 553.
    #
    #   THE STEM   6-8 px, call it 7 = 0.125 x xh = **0.64 x Albo's stem**.
    #              The Aldine lowercase is LIGHTER than this family, which is
    #              the same thing the e said (its flanks 0.79 x). Only the i is
    #              changed here -- l m n u carry the module's old 1.0 and
    #              should follow, but that is a separate pass.
    #   THE HEAD   a straight diagonal rising ~22 deg to the right, from
    #              (188,507) to (205,500): 17 px long = 2.5 stems = 1.6 x S,
    #              about 6 px thick away from the stem = 0.55 x S. It crosses
    #              the stem at 0.875 of the band, and reaches FURTHER RIGHT of
    #              the stem than left. The module's generic head has the angle
    #              and the weight about right and is too SHORT (1.15).
    #   THE EXIT   sweeps right to x203 from a stem at x187-194 -- about 1.4
    #              stem widths, so the module's 0.80 x S foot is close.
    #   THE DOT    x192-203 by rows 471-479: 12 x 9 px, WIDER THAN TALL, and
    #              its centre sits 0.39 of the band above the x-line (the old
    #              code had 0.265). A round dot is the wrong shape -- it is a
    #              single touch of a broad nib, so it is drawn as a short
    #              stroke on the pen's own angle.
    I_STEM = float(os.environ.get("ALBO_ALD_I_STEM", 0.64))   # x S
    I_HEAD_LEN = float(os.environ.get("ALBO_ALD_I_HEAD", 1.60))  # x S
    I_FOOT = float(os.environ.get("ALBO_ALD_I_FOOT", 1.30))      # the exit, x S
    I_DOT_Y = float(os.environ.get("ALBO_ALD_I_DOT_Y", 0.39))    # x xh, above the x-line
    I_DOT_W = float(os.environ.get("ALBO_ALD_I_DOT_W", 1.09))    # its long axis, x S
    I_DOT_T = float(os.environ.get("ALBO_ALD_I_DOT_T", 0.83))    # its thickness, x S

    def wedge_head(x, y, length=None, w=None, deg=None):
        """The Aldine head: a diagonal rising to the right ACROSS the stem,
        THICK where it meets the stem and tapering to its right tip, reaching
        much further right than left.

        The first cut drew it at a constant 0.55 x S, taken from the head's
        thickness at its right END (6 px at x204). That is its thinnest point.
        Beside the stem it is 13 rows -- 0.23 x xh, about 1.2 x S -- so the
        letter's top is a WEDGE with real mass in it, and a constant-width
        diagonal rendered as a sliver. Measured on the i of "rodigium"; the
        a, l, m, n and u wear the same shape."""
        a = math.radians(HEAD_DEG if deg is None else deg)
        L = S * (I_HEAD_LEN if length is None else length)
        dx, dy = math.cos(a) * L, math.sin(a) * L
        hw = (HEAD_W if w is None else w)
        hp = con([0.80, 2.05, 1.35, 0.82])
        return stroke([(x - dx * 0.30, y - dy * 0.30), (x + dx * 0.70, y + dy * 0.70)],
                      widths([(0.0, S * hw * hp[0]), (0.30, S * hw * hp[1]),
                              (0.62, S * hw * hp[2]), (1.0, S * hw * hp[3])]),
                      cut0=CUT, cut1=CUT)

    @glyph('i')
    def a_i(c):
        xh = c["xh"]; x = S * 1.0
        parts = list(st(x, 0, xh, head=False, foot=True, w=I_STEM,
                        foot_len=I_FOOT, foot_w=0.46))
        parts.append(wedge_head(x, xh * 0.875))
        # the dot: one touch of the nib, so an oval lying on the pen's angle
        a = math.radians(HEAD_DEG); L = S * I_DOT_W
        dx, dy = math.cos(a) * L, math.sin(a) * L
        cy = xh + I_DOT_Y * xh
        parts.append(stroke([(x - dx * 0.5, cy - dy * 0.5), (x + dx * 0.5, cy + dy * 0.5)],
                            S * I_DOT_T, cut0=CUT, cut1=CUT))
        return geom.ink(parts)

    @glyph('l')
    def a_l(c):
        return geom.ink(st(S * 1.0, 0, c["asc"], head=True))

    @glyph('n')
    def a_n(c):
        xh = c["xh"]; x0 = S * 1.0; x1 = x0 + 268 * _w(c)
        return geom.ink(st(x0, 0, xh, head=False) + [arch(c, x0, x1)] + st(x1, 0, xh * 0.74, foot=True))

    @glyph('m')
    def a_m(c):
        xh = c["xh"]; x0 = S * 1.0; d = 250 * _w(c); x1 = x0 + d; x2 = x1 + d
        return geom.ink(st(x0, 0, xh, head=False) + [arch(c, x0, x1), arch(c, x1, x2)]
                        + st(x1, 0, xh * 0.74, foot=False) + st(x2, 0, xh * 0.74))

    @glyph('h')
    def a_h(c):
        xh = c["xh"]; x0 = S * 1.0; x1 = x0 + 268 * _w(c)
        return geom.ink(st(x0, 0, c["asc"], head=True) + [arch(c, x0, x1)] + st(x1, 0, xh * 0.74))

    # THE STEM PITCH, measured three ways on griffo-macro.png and agreeing:
    # the m of "tumulum" puts its stems near x505/532/560, and the l and the
    # following u sit at 680 and 709 -- about 28 px on a 54 px x-height, so
    # **0.52 x xh between stem centres**. Everything else in the u is already
    # measured on the i: the stem at 0.64 x S, the wedge head, the exit.
    U_PITCH = float(os.environ.get("ALBO_ALD_U_PITCH", 0.52))   # stem centres, x xh
    U_JOIN = float(os.environ.get("ALBO_ALD_U_JOIN", 0.30))     # where the bottom curve meets, x xh

    @glyph('u')
    def a_u(c):
        """Written, not assembled. ONE movement makes the left stem, the bottom
        turn and the rise to the right stem -- down, around, up -- and a second
        stroke brings the right stem down to the baseline and out.

        The first cut butted three pieces together: two stems and a bottom
        curve drawn separately. It measured correctly and read as construction,
        because the joins were seams rather than the places a stroke changes
        direction. The pen's own widths along one path do the work instead:
        thick down the left, thinning through the turn, thin on the rise --
        which is what an upstroke is."""
        xh = c["xh"]; x0 = S * 1.0; x1 = x0 + U_PITCH * xh
        w = x1 - x0
        # down, around, up -- one path
        p = catmull([(x0, xh * 0.94), (x0 - w * 0.02, xh * 0.52),
                     (x0 + w * 0.06, xh * 0.16), (x0 + w * 0.34, -OVER * 0.5),
                     (x0 + w * 0.72, xh * 0.14), (x1, xh * 0.52), (x1, xh * 0.94)],
                    tension=0.5)
        # thick down the left, thinning through the turn, thin on the rise
        up = con([1.00, 0.98, 0.74, 0.52, 0.46, 0.60, 0.78])
        prof = widths([(i / (len(up) - 1), S * I_STEM * 1.34 * v) for i, v in enumerate(up)])
        parts = [stroke(p, prof, cut0=CUT)]
        # the second stroke: the right stem down to the baseline, and out
        parts += list(st(x1, 0, xh * 0.94, head=False, foot=True, w=I_STEM,
                         foot_len=I_FOOT, foot_w=0.46))
        parts.append(wedge_head(x0, xh * 0.875))
        parts.append(wedge_head(x1, xh * 0.875))
        return geom.ink(parts)

    # MEASURED off the o of "udos" in griffo-macro.png: x145-185, y61-114 --
    # 41 wide by 54 tall, w/h 0.759, counter/ink 0.617.
    #
    # THE STRESS was read properly rather than guessed: walking a ray out from
    # the letter's centre every 10 degrees and taking the FIRST contiguous band
    # of ink. The naive "last ink out" walks into the neighbouring s and
    # reports 30 px of stroke, which is how a stress measurement goes wrong
    # without anyone noticing. Thickness peaks at 50 deg (13.8 px) and bottoms
    # near 110 and 290 (about 5) -- so the PEN ANGLE is ~50 deg, a conventional
    # steep italic nib, and the contrast is ~2.8:1. Mean 8.7 px = 0.161 x xh =
    # 0.82 x the stem, which sits with the e's flanks at 0.79.
    O_W = float(os.environ.get("ALBO_ALD_O_W", 0.76))          # width, x xh
    O_PEN = float(os.environ.get("ALBO_ALD_O_PEN", 50.0))      # the nib's angle, degrees
    O_THICK = float(os.environ.get("ALBO_ALD_O_THICK", 1.63))  # x S, at the pen's fullest
    O_THIN = float(os.environ.get("ALBO_ALD_O_THIN", 0.590))    # x S, across the nib

    @glyph('o')
    def a_o(c):
        xh = c["xh"]; rx = O_W * xh / 2; ry = xh / 2 + OVER * 0.5
        cx = S * 0.6 + rx
        outer = superellipse(cx, ry - OVER * 0.5, rx, ry, 0.0, 2 * math.pi, BOWL_K)[:-1]
        phi = math.radians(O_PEN)
        _thick, _thin = (con([O_THIN, O_THICK], CON_O)[::-1] if CON_O else (O_THICK, O_THIN))
        def wf(t):
            th = t * 2 * math.pi
            return S * (_thin + (_thick - _thin) * abs(math.cos(th - phi)))
        return geom.ink([PR.ring_from(outer, widths_fn=wf, smooth_w=3)[0]])

    @glyph('c')
    def a_c(c):
        xh = c["xh"]; rx = 140 * _w(c); cx = S * 0.6 + rx
        p = superellipse(cx, xh / 2, rx, xh / 2 + OVER * 0.5, math.radians(38), math.radians(322), BOWL_K)
        wf = pen_widths(p, floor=S * FLOOR)
        return geom.ink([stroke(p, wf, cut0=CUT, cut1=CUT)])

    # RE-MEASURED off griffo-dante-1502.jpg -- the Stagnino Dante, the same
    # cutter at THREE TIMES the linear resolution of aldine.png (a 35 px
    # x-height against 13). The e in "Che" runs x191-212, y965-999.
    #
    # It corrects round 117 on two counts, and the owner called both before
    # the measurement did:
    #
    #   THE BAR IS ANGLED, not flat -- from (191,985) up to (209,977), a rise
    #   of 8 over a run of 14, about 30 degrees. At a 13 px x-height the bar
    #   is one row of ink and CANNOT show a slant; round 117 read that
    #   absence as evidence and wrote "no measurable rise". It was the
    #   resolution, not the letter.
    #
    #   THE LOWER RIGHT IS CLOSED. Rows 987-991 carry a second run at
    #   x205-210 -- the lower bowl's right flank -- so the letter has TWO
    #   counters, the small eye above the bar (x200-204, rows 973-976) and a
    #   larger one below it (x198-204, rows 987-991). On the 13 px scan that
    #   flank is a pixel wide and fell under the threshold.
    #
    # And it is ONE STROKE, not an arc with a bar laid across it: the pen
    # starts at the bar's left, rises right along the bar, carries up over the
    # crown, comes down the left -- passing its own start -- rounds the
    # bottom, and climbs the right to stop under the bar's right end. The bar
    # is where the loop closes on itself.
    #
    # Weights, off the same rows: left flank 6 px (0.17 x xh, ~0.87 x the
    # stem), crown 8 px (~1.15 x), the bar 5 px vertical at 30 degrees, so
    # ~4.3 px perpendicular (~0.63 x) -- the pen's thin.
    # RE-MEASURED a third time, off griffo-macro.png -- the macro detail of the
    # 1501 Virgil, a **54 px x-height**, four times aldine.png and half again
    # the Dante. The e of "naues" runs x594-631, y345-402. This is the best
    # evidence available and it settles all three readings:
    #
    #   THE BAR IS ANGLED, ~30 deg -- confirmed. Its TOP edge (the eye's
    #     floor) runs (610,370) -> (615,368) -> (620,364): 6 rows of rise over
    #     10 of run. Rows 370-372 look flat only because that is BELOW the
    #     slope, where the bar has merged with the left flank.
    #   THE LOWER RIGHT IS OPEN -- rows 373-391 carry ONE run. The bottom
    #     sweeps right to x619 and stops; nothing climbs the right side. Round
    #     117b closed it on a 35 px Dante reading where the bar's own right end
    #     and the bottom's return are four rows apart and cannot be told
    #     apart. The 13 px reading was right by luck; this one is right by
    #     resolution.
    #   CONTRAST IS ~3.4:1, much higher than drawn. Thick (left flank, right
    #     flank, crown) 8-9 px = 0.155 x xh = 0.79 x the stem; the bar 3 rows
    #     vertical at 30 deg, so 2.6 px perpendicular = 0.23 x the stem.
    #
    # So the letter has ONE enclosed counter, the eye, and it measures
    # 191 px against 941 px of ink -- a counter/ink ratio of 0.203, which is
    # what E_CTR is tuned against rather than a guess at a percentage.
    E_W = float(os.environ.get("ALBO_ALD_E_W", 0.65))       # 38/58 measured
    # The bar's ends, off the macro: its TOP edge (the eye's floor) is at row
    # 371 where it leaves the left flank and row 364 at x620 -- 0.54 and 0.67
    # of the band. The eye itself is x608-622 by rows 353-369: 0.37 of the
    # letter's width and 0.28 of the x-height. The first cut had the bar's left
    # end at 0.40 and the upper loop's flanks at 0.18/0.92, which made an eye
    # 0.55 W wide -- half again Griffo's -- and THAT, not the stroke weight,
    # was the counterspace. The macro's stroke is 0.79 x the stem: a LIGHT
    # letter with a small eye, not a heavy one.
    E_BAR = float(os.environ.get("ALBO_ALD_E_BAR", 0.54))   # the bar's LEFT end, x xh
    E_BAR_R = float(os.environ.get("ALBO_ALD_E_BAR_R", 0.67))  # its RIGHT end -- the rise
    E_EYE = float(os.environ.get("ALBO_ALD_E_EYE", 0.62))   # scales the upper loop's flanks
    E_WT = float(os.environ.get("ALBO_ALD_E_WT", 1.00))
    E_CON = float(os.environ.get("ALBO_ALD_E_CON", 1.00))   # contrast, x the measured 3.4:1
    E_THICK = float(os.environ.get("ALBO_ALD_E_THICK", 1.12))  # x S, across the nib
    E_THIN = float(os.environ.get("ALBO_ALD_E_THIN", 0.26))    # x S, along it
    E_CTR = float(os.environ.get("ALBO_ALD_E_CTR", 1.00))   # >1 eats counterspace
    E_END = float(os.environ.get("ALBO_ALD_E_END", 0.66))   # where the bottom stops. It STOPS.

    # THE PAGE'S OWN SLANT. Whole-stem fits scatter badly -- chancery stems
    # curve, so one stroke gives 13 deg and its neighbour 4.7 -- but 52 sliding
    # windows across the macro's first line have a median of 8.2, and the
    # Dante's l fits 8.8 over 41 clean rows. Call it 8.8. Glyph code here is
    # UNSHEARED design space (build.py shears at the end), so the slant has to
    # be taken OUT of points read off the page or the letter is slanted twice.
    # NOTE: the shipping italic builds at 13, which this says is 4-5 deg
    # steeper than Griffo. Not changed here -- that is a family ruling.
    # 13.0, not 8.8. The 8.8 came from fitting whole stems across a line, and
    # that method was already known to scatter 5-16 degrees because chancery
    # stems CURVE -- an entry and an exit at opposite ends drag a least-squares
    # line off the stem's own angle. The owner's target crop of a single a
    # gives 13.7 on 16 clean stem rows, and the family has shipped
    # FJORD_SLANT=13 all along. Build the Aldine italic at 13 so this unshear
    # cancels the build's shear exactly.
    E_PAGE_SLANT = float(os.environ.get("ALBO_ALD_PAGE_SLANT", 13.0))

    @glyph('e')
    def a_e(c):
        xh = c["xh"]; W = E_W * xh
        unshear = math.tan(math.radians(E_PAGE_SLANT)) * xh
        X = lambda f, fy: S * 0.55 + f * W - unshear * fy
        Y = lambda f: f * xh
        mid = 0.50
        E = lambda f: mid + (f - mid) * E_EYE   # the eye's flanks, about its centre
        P = [(0.00, E_BAR),  (E(0.78), E_BAR_R),  # the bar, rising ~30 degrees
             (E(0.84), 0.82), (E(0.52), 0.96),   # up the eye's right, over the crown
             (E(0.22), 0.86), (0.10, 0.66),      # down the left
             (0.02, 0.34),   (0.08, 0.14),      # past its own start
             (0.34, 0.02),   (E_END, 0.12)]     # round the bottom, and STOP
        p = catmull([(X(fx, fy), Y(fy)) for fx, fy in P], tension=0.5)
        # Measured off the macro: thick 0.79 x the stem, the bar 0.23 -- 3.4:1.
        # The width at each point comes from the NIB and the direction the
        # stroke is travelling there, not from a hand-tuned list.
        dirs = []
        for i in range(len(P)):
            a_ = P[max(0, i - 1)]; b_ = P[min(len(P) - 1, i + 1)]
            dirs.append(math.degrees(math.atan2((b_[1] - a_[1]) * xh,
                                                (b_[0] - a_[0]) * W)))
        base = con([nib(d, E_THICK, E_THIN) for d in dirs], CON_E)
        mean = sum(base) / len(base)
        wf = widths([(i / (len(base) - 1),
                      S * (mean + (w - mean) * E_CON) * E_WT * E_CTR)
                     for i, w in enumerate(base)])
        # pieces=True: the centerline CROSSES ITSELF where the loop closes on
        # the bar. As one polygon that crossing becomes a HOLE -- the outline
        # self-intersects and the fill cancels -- which was the bite in the
        # letter's left side.
        return geom.ink([stroke(p, wf, cut0=CUT, cut1=CUT, pieces=True)])

    # MEASURED off aldine.png, row by row, on two separate a's -- the one in
    # "resonaram" at x223-234 and the one at x326-338. Both give the same
    # letter and it is not the one drawn before this: the bowl's top joins the
    # stem AT the x-line in a tight arc (not a long diagonal arm reaching down
    # from a tall stem), the counter is a SMALL rounded triangle pointing up,
    # and -- the part that makes it an a rather than a d -- the bowl's bottom
    # rejoins the stem about a fifth of the way UP, leaving a notch above the
    # foot. Every earlier cut ran it into the stem at the baseline, which is a
    # d, which is what the ladders kept rendering.
    A_W = float(os.environ.get("ALBO_ALD_A_W", 1.00))       # letter width, x xh (12/12 measured)
    A_STEM = float(os.environ.get("ALBO_ALD_A_STEM", 0.67)) # the stem's center, x the width
    # The rise is the whole a/d question. The scan puts 2-3 px of ink above a
    # 13 px x-line -- but as a BLUNT wedge jutting right, not a spike, and a
    # thin spike at the same height reads as a d however right the bowl is.
    A_RISE = float(os.environ.get("ALBO_ALD_A_RISE", 0.12)) # the head above the x-line, x xh
    A_HEAD = float(os.environ.get("ALBO_ALD_A_HEAD", 1.15))
    A_HEAD_W = float(os.environ.get("ALBO_ALD_A_HEAD_W", 1.55))  # its weight, x HEAD_W
    A_JOIN = float(os.environ.get("ALBO_ALD_A_JOIN", 0.22)) # where the bowl's bottom meets the stem
    A_FLANK = float(os.environ.get("ALBO_ALD_A_FLANK", 2.03))  # the bowl's left flank, x the stem
    # The exit. Owner 2026-09-15, choosing arm C: *"it needs more of an
    # extended tail to match the scan."* Palatino's italic a (TeX Gyre Pagella,
    # refs/texgyrepagella-italic.otf, his reference) runs the stem past the
    # bowl and kicks it right along the baseline; the scan does the same. The
    # ordinary FOOT_LEN is the arch letters' blunt outstroke and is too short
    # to read as that exit.
    A_TAIL = float(os.environ.get("ALBO_ALD_A_TAIL", 1.65))  # the exit's length, x the stem
    A_TAIL_W = float(os.environ.get("ALBO_ALD_A_TAIL_W", 0.48))  # its weight where it ends
    # THE BOWL'S SIZE, against the owner's target crop (2026-09-15). Measured
    # on it: lean 13.7 deg over 16 clean stem rows, pen angle 50 deg (the same
    # axis the o gave), w/h 0.891 and **counter/ink 0.344**. The proportion was
    # already right at 0.920; the counter was not, at 0.652 -- nearly twice the
    # target. As with the e, the lever is the bowl's GEOMETRY and not its
    # weight: thickening to close a counter moves the page's colour to fix a
    # ratio. A_BOWL scales the bowl's path about its own centroid.
    # A_BOWL back to 1.00. Squeezing the bowl toward the stem was the wrong way
    # to close the counter: it ran the bowl's inner edge PARALLEL to the stem
    # for most of its length, which is a sliver, and no amount of smoothing the
    # width profile fixes a counter whose two sides are parallel. The area
    # comes from the bowl's WEIGHT instead, and the counter stays round --
    # measured, the same counter/ink at 26% more inscribed radius.
    A_BOWL = float(os.environ.get("ALBO_ALD_A_BOWL", 1.00))
    # THE TOP RIGHT CARRIES A THICK TOO (owner 2026-09-15). It is not a taste
    # call -- it is what the measured 50 degree pen MUST do. A nib at 50 is
    # fullest on the 50/230 axis, so the upper-right and the lower-left are
    # both thick and the upper-left and lower-right are both thin. The bowl
    # had its thick only at the bottom left, which is half a pen.
    A_TOPR = float(os.environ.get("ALBO_ALD_A_TOPR", 1.55))   # the bowl where it leaves the stem
    # Where the arm STARTS. Springing it from the stem's top corner
    # (A_STEM-0.01, 1.00) makes the counter's ceiling and the stem's left edge
    # meet at an acute angle, and that sharp apex is what reads as ungraceful
    # however round the rest of the counter is. Starting it to the RIGHT of the
    # stem's centre and a little below the top makes the arm CROSS the stem, so
    # the junction is blunt and the counter's top is a curve.
    A_CROSS = float(os.environ.get("ALBO_ALD_A_CROSS", 0.08))   # x past the stem's centre
    A_TOP_Y = float(os.environ.get("ALBO_ALD_A_TOP_Y", 0.92))   # and how far below the top
    A_ARM_X = float(os.environ.get("ALBO_ALD_A_ARM_X", 0.34))  # how far left the arm dives
    A_ARM_Y = float(os.environ.get("ALBO_ALD_A_ARM_Y", 0.78))  # and how steeply

    @glyph('a')
    def a_a(c):
        """One stem with an angled head, and one bowl stroke that leaves the
        stem at the x-line, swings left and down, round the bottom, and comes
        back UP to the stem a fifth of the way above the baseline."""
        xh = c["xh"]; W = A_W * xh
        X = lambda f: S * 0.55 + f * W
        Y = lambda f: f * xh
        xs_ = X(A_STEM)
        top = xh + A_RISE * xh
        parts = list(st(xs_, 0, top, head=False, foot=True, foot_len=A_TAIL, foot_w=A_TAIL_W))
        if A_HEAD:
            L = S * A_HEAD; a = math.radians(HEAD_DEG)
            dx, dy = math.cos(a) * L, math.sin(a) * L
            parts.append(stroke([(xs_ - dx * 0.70, top - dy * 0.70 - S * 0.05),
                                 (xs_ + dx * 0.34, top + dy * 0.34)], S * HEAD_W * A_HEAD_W, cut0=CUT))
        # THE ARM DIVES. The counter is bounded above by this entry and on the
        # right by the stem, so a shallow entry leaves the two running parallel
        # for most of the letter -- a sliver, whatever the widths do. A steep
        # dive gives the counter a diagonal ceiling and compacts it.
        BP = [(A_STEM + A_CROSS, A_TOP_Y), (A_ARM_X, A_ARM_Y), (0.20, 0.66),
              (0.11, 0.44), (0.12, 0.24), (0.26, 0.06),
              (0.46, 0.09), (A_STEM - 0.09, A_JOIN)]
        # Narrow the bowl TOWARD THE STEM, leaving its two ends where they
        # are: they sit ON the stem, and a first version scaled every point
        # about the bowl's centroid, which walked those ends inward and SEALED
        # the counter -- counter/ink went to 0.000 at the first step down.
        BP = [(A_STEM + (fx - A_STEM) * A_BOWL, fy) for fx, fy in BP]
        p_ = catmull([(X(fx), Y(fy)) for fx, fy in BP], tension=0.5)
        # Weight read off the same rows: thin where the arc leaves the stem,
        # the flank at three quarters of the stem, the bottom heaviest.
        # The bowl's width comes from the nib at every sample, not from five
        # stops -- a stepped profile offsets into a five-sided counter, and
        # this counter is narrow enough to show every flat. The top-right
        # boost the owner approved rides on top as a smooth cosine ramp, so it
        # adds weight without adding a corner.
        def _boost(t):
            return 1.0 + (A_TOPR - 1.0) * (0.5 + 0.5 * math.cos(math.pi * min(1.0, t / 0.34)))
        aw = nib_widths(p_, A_FLANK, A_FLANK * 0.33, CON_A, smooth=11, boost=_boost)
        parts.append(stroke(p_, widths([(i / (len(aw) - 1), S * w_)
                                        for i, w_ in enumerate(aw)]), cut0=CUT))
        return geom.ink(parts)

    @glyph('b')
    def a_b(c):
        xh = c["xh"]; x0 = S * 1.0; rx = 142 * _w(c)
        return geom.ink(st(x0, 0, c["asc"], head=True, foot=False)
                        + [bowl(c, x0 + rx * 0.86, rx, top=BOWL_TOP)])

    @glyph('d')
    def a_d(c):
        xh = c["xh"]; rx = 142 * _w(c); x1 = S * 0.6 + rx * 1.78
        return geom.ink([bowl(c, S * 0.6 + rx, rx, top=BOWL_TOP)] + st(x1, 0, c["asc"], head=True))

    @glyph('p')
    def a_p(c):
        x0 = S * 1.0; rx = 142 * _w(c)
        return geom.ink(st(x0, -c["desc"], c["xh"], head=False, foot=False)
                        + [bowl(c, x0 + rx * 0.86, rx, top=BOWL_TOP)])

    @glyph('q')
    def a_q(c):
        rx = 142 * _w(c); x1 = S * 0.6 + rx * 1.78
        return geom.ink([bowl(c, S * 0.6 + rx, rx, top=BOWL_TOP)]
                        + st(x1, -c["desc"], c["xh"], head=False))

    @glyph('r')
    def a_r(c):
        xh = c["xh"]; x0 = S * 1.0
        p = cubic((x0, xh * BRANCH), (x0 + 26 * _w(c), xh * 0.90),
                  (x0 + 96 * _w(c), xh + pen.ARCH_OVER), (x0 + 182 * _w(c), xh * 0.86))
        wf = pen_widths(p, floor=S * FLOOR)
        return geom.ink(st(x0, 0, xh, head=False)
                        + [stroke(p, lambda t: wf(t) * (0.60 + 0.40 * min(1.0, t / 0.35)), cut1=CUT)])

    @glyph('f')
    def a_f(c):
        """Tall, hooked head, and it descends -- as it does on the page."""
        xh = c["xh"]; asc = c["asc"]; x = S * 1.4
        p = cubic((x - S * 0.10, -c["desc"] * 0.52), (x - S * 0.02, xh * 0.5),
                  (x + S * 0.06, asc * 0.94), (x + S * 1.15, asc * 1.02))
        wf = pen_widths(p, floor=S * FLOOR)
        bar = stroke([(x - S * 0.95, xh * 0.94), (x + S * 1.00, xh * 0.94)], TH_H * 0.90)
        return geom.ink([stroke(p, lambda t: wf(t) * (1.0 - 0.42 * max(0.0, (t - 0.72) / 0.28)), cut1=CUT), bar])

    @glyph('t')
    def a_t(c):
        xh = c["xh"]; x = S * 1.0
        p = cubic((x, xh * 1.30), (x, xh * 0.34), (x + S * 0.30, S * 0.08), (x + S * 1.20, S * 0.62))
        wf = pen_widths(p, floor=S * FLOOR)
        bar = stroke([(x - S * 0.80, xh * 0.92), (x + S * 0.86, xh * 0.92)], TH_H * 0.88)
        return geom.ink([stroke(p, wf, cut1=CUT), bar])

    @glyph('j')
    def a_j(c):
        x = S * 1.0
        p = cubic((x, c["xh"]), (x, -c["desc"] * 0.36), (x - S * 0.55, -c["desc"] * 0.92), (x - S * 1.50, -c["desc"] * 0.70))
        wf = pen_widths(p, floor=S * FLOOR)
        return geom.ink([stroke(p, lambda t: wf(t) * (1.0 - 0.45 * max(0.0, (t - 0.6) / 0.4)), cut1=CUT),
                         PR.dot(x + S * 0.30, c["xh"] + S * 1.35, S * 0.52)])

    @glyph('s')
    def a_s(c):
        xh = c["xh"]; x = S * 0.7; w = 182 * _w(c)
        p = catmull([(x + w * 0.92, xh * 0.86), (x + w * 0.20, xh * 0.98), (x + w * 0.10, xh * 0.62),
                     (x + w * 0.86, xh * 0.40), (x + w * 0.94, xh * 0.08), (x + w * 0.16, xh * 0.14)], tension=0.5)
        wf = pen_widths(p, floor=S * FLOOR)
        return geom.ink([stroke(p, wf, cut0=CUT, cut1=CUT)])

    @glyph('g')
    def a_g(c):
        """Two storeys, both small -- the page's g is a quiet letter."""
        xh = c["xh"]; rx = 138 * _w(c); cx = S * 0.6 + rx
        up = bowl(c, cx, rx, top=BOWL_TOP)
        lo = ring(cx - rx * 0.16, -c["desc"] * 0.48, rx * 0.96, c["desc"] * 0.40, floor=S * FLOOR)[0]
        nk = stroke(cubic((cx + rx * 0.78, xh * 0.20), (cx + rx * 0.58, -c["desc"] * 0.04),
                          (cx + rx * 0.30, -c["desc"] * 0.10), (cx + rx * 0.72, -c["desc"] * 0.08)),
                    widths([(0.0, S * 0.66), (0.5, S * 0.34), (1.0, S * 0.60)]))
        return geom.ink([up, lo, nk])

    def _diag(p0, p1, w0, w1):
        return stroke([p0, p1], widths([(0.0, S * w0), (1.0, S * w1)]), cut0=CUT, cut1=CUT)

    @glyph('v')
    def a_v(c):
        xh = c["xh"]; x = S * 0.7; w = 200 * _w(c)
        return geom.ink([_diag((x, xh), (x + w * 0.52, 0), 0.96, 0.34),
                         _diag((x + w * 0.52, 0), (x + w, xh), 0.34, 0.52)])

    @glyph('w')
    def a_w(c):
        xh = c["xh"]; x = S * 0.7; w = 182 * _w(c)
        P = []
        for k in (0, 1):
            o = x + k * w * 1.06
            P += [_diag((o, xh), (o + w * 0.52, 0), 0.94, 0.34),
                  _diag((o + w * 0.52, 0), (o + w * 1.04, xh), 0.34, 0.50)]
        return geom.ink(P)

    @glyph('x')
    def a_x(c):
        xh = c["xh"]; x = S * 0.7; w = 190 * _w(c)
        return geom.ink([_diag((x, xh), (x + w, 0), 0.92, 0.40),
                         _diag((x, 0), (x + w, xh), 0.40, 0.40)])

    # THE y IS DERIVED, NOT MEASURED, and that is worth saying plainly: there
    # is no y anywhere in griffo-macro.png, in the Dante, or in the Virgil page
    # -- Latin and Italian barely use it. So it is built from parts that ARE
    # measured elsewhere in this module (the 0.64 stem, the wedge head, the
    # 50-degree pen, the u's pitch) rather than read off a page, and it should
    # be the first letter re-cut if a specimen carrying one ever turns up.
    Y_PITCH = float(os.environ.get("ALBO_ALD_Y_PITCH", 0.52))   # as the u
    Y_TAIL = float(os.environ.get("ALBO_ALD_Y_TAIL", 0.88))     # how far left the tail reaches, x desc

    @glyph('y')
    def a_y(c):
        """DERIVED. The u's left half, then a right stroke carrying on past the
        baseline into a tail that sweeps left -- the descender drawn on the same
        pen as the o."""
        xh = c["xh"]; dsc = c["desc"]; x0 = S * 1.0; x1 = x0 + Y_PITCH * xh
        parts = list(st(x0, xh * U_JOIN, xh, head=False, foot=False, w=I_STEM))
        parts.append(wedge_head(x0, xh * 0.875))
        parts.append(wedge_head(x1, xh * 0.875))
        p = catmull([(x0, xh * U_JOIN), (x0 + (x1 - x0) * 0.12, xh * 0.10),
                     (x0 + (x1 - x0) * 0.52, -OVER * 0.4),
                     (x1 - (x1 - x0) * 0.08, xh * 0.16), (x1, xh * 0.88)], tension=0.5)
        wf = pen_widths(p, floor=S * FLOOR)
        parts.append(stroke(p, lambda t: wf(t) * I_STEM * 1.30))
        tail = catmull([(x1, xh * 0.88), (x1 - S * 0.10, xh * 0.10),
                        (x1 - S * 0.55, -dsc * 0.46),
                        (x1 - S * 1.60, -dsc * 0.86),
                        (x0 - Y_TAIL * S, -dsc * 0.66)], tension=0.5)
        wt = pen_widths(tail, floor=S * FLOOR)
        parts.append(stroke(tail, lambda t: wt(t) * I_STEM
                            * (1.30 - 0.85 * max(0.0, (t - 0.50) / 0.50)), cut1=CUT))
        return geom.ink(parts)

    @glyph('z')
    def a_z(c):
        xh = c["xh"]; x = S * 0.7; w = 182 * _w(c)
        return geom.ink([stroke([(x, xh * 0.94), (x + w, xh * 0.94)], TH_H * 0.95, cut0=CUT, cut1=CUT),
                         _diag((x + w * 0.94, xh * 0.94), (x + S * 0.10, TH_H * 0.5), 0.86, 0.86),
                         stroke([(x, 0), (x + w, 0)], TH_H * 0.95, cut0=CUT, cut1=CUT)])

    @glyph('k')
    def a_k(c):
        xh = c["xh"]; x0 = S * 1.0; r = 182 * _w(c)
        arm = _diag((x0 + r, xh), (x0 + S * 0.16, xh * 0.42), 0.40, 0.64)
        leg = _diag((x0 + S * 0.22, xh * 0.46), (x0 + r * 0.98, 0), 0.62, 0.86)
        return geom.ink(st(x0, 0, c["asc"], head=True) + [arm, leg])


# ---------------------------------------------------------------- THE GATE
# Round 117b deleted a, b, d, p and q from this module and round 119 took r,
# and NOTHING SAID SO for four rounds. The edits sliced the file between
# `@glyph(...)` markers, one slice ran from the e's comment block to
# `@glyph('f')`, and everything in between went with it. The letters then fell
# through to glyphs/italic.py -- so the builds still worked, the specimens
# still rendered, and the pages published for three rounds showed the CLASSIC
# a, b, d, p, q and r under an "aldine" label. The owner caught it by eye:
# "why am I seeing the wrong a?"
#
# A comment asking the next editor to be careful would not have caught it.
# This does: the module declares what it is FOR -- the complete lowercase --
# and refuses to load quietly without it.
# NOTE the check is on OWNERSHIP, not on presence. A first version asked
# whether GLYPHS held each letter -- and it always does, because italic.py
# registers the whole lowercase before this module is imported. It passed
# happily with the a deleted, which is the very bug it was written for. A gate
# has to be shown FAILING before it is worth anything.
if ON:
    _MINE = {ch for ch, fn in GLYPHS.items()
             if getattr(fn, "__module__", None) == __name__}
    _MISSING = sorted(set("abcdefghijklmnopqrstuvwxyz") - _MINE)
    if _MISSING:
        raise RuntimeError(
            "ALBO_ITALIC=aldine is missing " + "".join(_MISSING) +
            " -- the Aldine module must define the whole lowercase. Without "
            "this check those letters silently fall through to the classic "
            "italic and the build still succeeds.")
