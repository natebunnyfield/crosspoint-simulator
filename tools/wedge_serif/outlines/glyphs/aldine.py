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
from . import glyph as _register, GLYPHS

# PER-LETTER WEIGHT, so the fitter can reach a letter without a dial of its
# own. Every glyph here is wrapped to record which letter is being drawn, and
# the shared width paths multiply by ALBO_ALD_LW_<ch>. It is one hook rather
# than twenty-six dials, and it is what lets aldine_autofit solve a letter that
# nobody has hand-tuned.
_CUR = [None]

# SOLVED BY aldine_autofit.py against the scan crops, not by hand. Only the
# letters whose fit actually CONVERGED are here -- d (err 0.106), q (0.108) and
# u (0.151) are left at 1.0 because their solver pinned at a dial's rail, which
# is the fitter saying the lever is wrong rather than the value. Re-run:
#   python3 aldine_autofit.py --letters <chars>
FIT = {            # ch: (weight, width)
    'b': (0.550, 1.100),
    # h l m r LEFT THIS TABLE in round 132: they are drawn to the reference in
    # units now, so a weight buffer and a horizontal scale on top of the
    # drawing can only take them away from it -- and the three different widths
    # this table gave h, m and r were a large part of why they did not read as
    # one hand.
    'p': (0.550, 0.725),
    's': (1.325, 1.100),
    # the eight re-cut capitals, fitted against Pagella Italic -- DERIVED, not
    # measured: the macro carries only an A and a B, and the Dante's lines
    # would not segment. They are the reference half of the brief, and the
    # ledger says so rather than letting them pass as scan-measured.
    # WIDTHS are kept from the fit; WEIGHTS are not, except where the target
    # actually constrained ink. G H N U all solved at the weight dial's 2.10
    # rail and rendered as black blobs, because their only reference target is
    # w/h and a letter can double its stroke without moving its bounding box.
    # The fitter no longer offers a weight dial to a letter nothing holds it
    # against; these four sit at the measured CAP_W instead.
    # WEIGHTS SOLVED AGAINST THE ROMAN CAPITALS this module does not redraw,
    # letter BY letter: each italic capital is driven to the ratio its OWN
    # roman carries against the roman's controls. So the target for the A is
    # the roman A's 0.89, not 1.00 -- a diagonal letter is lighter than a
    # stemmed one and always was, and a metric that does not know it will
    # fatten every A in the alphabet.
    #
    # THE MEASURE IS 2 x AREA / OUTLINE LENGTH -- the mean width of the ink,
    # taken off the OUTLINE with an area pen and a flattened-curve perimeter.
    # Two earlier instruments both lied, in opposite directions, on the same
    # letters: the MEDIAN of a row's horizontal runs read the A 1.81x too
    # HEAVY (a crossbar is one run per row and hundreds of pixels long, so it
    # drags the median off the strokes), and the 30th PERCENTILE read it 0.71x
    # too LIGHT (it catches each letter's hairline, and a high-contrast letter
    # has more hairline than stem). Area over length asks neither question.
    # It also counts the WIDTH dial, which is right: a ring scaled 1.225x
    # horizontally IS heavier on the page, and the Q's 1.18 came from nowhere
    # else.
    'A': (1.000, 1.350),
    # ROUND 135 re-solved the Q's weight, 0.492 -> 1.000, because the letter
    # changed under it: the ring widened by 17% to Pagella's and the tail left
    # the counter, and both take ink out of a measure that is ink AREA over
    # outline LENGTH. At the old 0.492 the re-cut Q measured 0.79 of its roman
    # against a 0.05 tolerance. 1.000 means the buffer is off entirely and the
    # drawn letter stands as drawn.
    'Q': (0.880, 1.225),
    'V': (1.000, 1.350),
    'S': (1.218, 0.975),
    'N': (1.000, 1.100),
    'H': (0.950, 1.100),
    'G': (1.175, 1.100),
    'U': (0.950, 1.225),
    # ROUND 135, Y and O -- SHAPE from Pagella, WEIGHT from Albo's own roman,
    # which is round 131c's rule and not a compromise between the two: the
    # reference says what the letter IS and the roman says how black it may be.
    # Both widths stay at 1.000 because these two are drawn to a measured w/h
    # in units (0.875 and 0.943), so a horizontal scale on top could only take
    # them off it. The weights are solved by cmp_cap_weight.py --tol 0.05.
    'Y': (1.000, 1.000),
    'O': (1.000, 1.000),
}


def _lw():
    ch = _CUR[0]
    if not ch: return 1.0
    v = os.environ.get(f"ALBO_ALD_LW_{ch}")
    return float(v) if v is not None else FIT.get(ch, (1.0, 1.0))[0]


def _wd():
    ch = _CUR[0]
    if not ch: return 1.0
    v = os.environ.get(f"ALBO_ALD_WD_{ch}")
    return float(v) if v is not None else FIT.get(ch, (1.0, 1.0))[1]


def glyph(*chars):
    """Registers a glyph AND gives it two dials nobody has to write by hand:
    `ALBO_ALD_LW_<ch>` scales its stroke weight through the shared width paths,
    and `ALBO_ALD_WD_<ch>` scales the finished outline horizontally.

    The width one exists because the fitter kept pinning at the weight dial's
    rail -- b p q u all solved to the low or high bound with an error still
    over 0.09, which is a solver saying "this is not the lever". A letter whose
    w/h is wrong cannot be fixed by making its strokes thinner."""
    def deco(fn):
        def wrapped(c, _ch=chars[0], _fn=fn):
            prev = _CUR[0]; _CUR[0] = _ch
            try:
                g = _fn(c)
                # WEIGHT AT THE ONE CHOKE POINT. Hooking `nib_widths` and
                # `st` reached only the letters built that way -- c f j v x z
                # g o q come from ring/pen_widths/_diag and ignored the dial
                # completely, so the colour fitter moved it, saw nothing
                # change, and recorded values that did nothing. A buffer on
                # the finished outline reaches every letter however it was
                # drawn: positive thickens, negative thins, and the shape is
                # untouched. The nib-path multiplier is gone.
                lw = _lw()
                if abs(lw - 1.0) > 1e-6:
                    g = g.buffer(S * 0.16 * (lw - 1.0), join_style=2)
                wd = _wd()
                if abs(wd - 1.0) > 1e-6:
                    from shapely import affinity
                    g = affinity.scale(g, xfact=wd, yfact=1.0, origin=(0, 0))
                return g
            finally:
                _CUR[0] = prev
        wrapped.__name__ = getattr(fn, "__name__", "glyph")
        return _register(*chars)(wrapped)
    return deco
from .. import geom, pen
from ..geom import cubic, line, catmull, superellipse
from ..primitives import stroke, pen_widths, widths, ring
from .. import primitives as PR
from ..pen import S, XH, ASC, DESC, OVER, TH_V, TH_H, CUT, BOWL_K, CS

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
ALD_CON = float(os.environ.get("ALBO_ALD_CON", 5.00))      # the module default: arm B (owner, spacing bench 2026-09-16)
CON_A = float(os.environ.get("ALBO_ALD_CON_A", 5.00))      # the a: arm C
CON_E = float(os.environ.get("ALBO_ALD_CON_E", 5.00))      # the e: arm C
CON_O = float(os.environ.get("ALBO_ALD_CON_O", 5.00))      # the o: arm B (the whole line moved to B, 2026-09-16)


def nib(direction_deg, thick, thin, phi=50.0):
    """The measured 50-degree nib, as a width for a stroke running in
    `direction_deg`. A broad pen is fullest across its edge and thinnest along
    it, so the width goes as |sin(direction - phi)|. The o was built on this
    from the start; the e was carrying a HAND LIST instead, near-uniform all
    the way round the loop, which is why it read flat beside the others even
    once the contrast arm had stretched its ratio."""
    import math as _m
    return thin + (thick - thin) * abs(_m.sin(_m.radians(direction_deg - phi)))


# A BRUSH LEAVES AND ARRIVES. Every stroke in the scans starts and ends
# narrower than its body: the nib is not at full width the instant it touches
# the paper, and it lifts before it stops. Albo's strokes were full width to a
# flat cut at both ends, which is what makes a drawn letter look assembled
# rather than written. TIP is the fraction of the body's width a stroke has at
# its very ends, and TIP_RUN how much of the stroke's length it takes to get
# there -- both small, because this is the pen's entry, not a taper.
ALD_TIP = float(os.environ.get("ALBO_ALD_TIP", 0.62))
ALD_TIP_RUN = float(os.environ.get("ALBO_ALD_TIP_RUN", 0.12))


def _taper(n, tip=None, run=None, ends=(True, True)):
    """A multiplier per sample: `tip` at the ends, 1.0 across the body."""
    tip = ALD_TIP if tip is None else tip
    run = ALD_TIP_RUN if run is None else run
    if tip >= 1.0 or run <= 0: return [1.0] * n
    out = []
    for i in range(n):
        t = i / max(1, n - 1)
        m = 1.0
        if ends[0] and t < run:
            m = min(m, tip + (1 - tip) * (0.5 - 0.5 * math.cos(math.pi * t / run)))
        if ends[1] and t > 1 - run:
            u = (1 - t) / run
            m = min(m, tip + (1 - tip) * (0.5 - 0.5 * math.cos(math.pi * u)))
        out.append(m)
    return out


def nib_widths_closed(pts, thick, thin, target=None, phi=50.0):
    """Nib widths round a CLOSED contour -- the tangent wraps, so there is no
    seam where the first and last samples meet, and no taper either: a closed
    curve has no ends to leave from."""
    n = len(pts); out = []
    for i in range(n):
        a_ = pts[(i - 1) % n]; b_ = pts[(i + 1) % n]
        out.append(nib(math.degrees(math.atan2(b_[1] - a_[1], b_[0] - a_[0])),
                       thick, thin, phi))
    return con(out, target)


def nib_widths(pts, thick, thin, target=None, smooth=9, boost=None, taper=True):
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
    if taper:
        ws = [w * m for w, m in zip(ws, _taper(n))]
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
    # THESE THREE ARE RETIRED AND DRAW NOTHING (round 135). They were the
    # j's copy of the dot; the j calls `ij_dot` now, so the live dials are
    # HM_DOT_LEN / HM_DOT_TH / HM_DOT_CY. Kept named rather than deleted only
    # because the prose above and in the j cites them -- setting one moves no
    # ink, which is worth saying out loud where the next pass will look.
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

    # ------------------------------------------- THE STEM-AND-ARCH FAMILY, round 132
    # h m n r u i l DRAWN AGAINST THE REFERENCE, one construction, one hand.
    # Owner 2026-09-15: "examine a then each subsequent letter, take multiple
    # passes at each until the shape and strokes and serifs match what they
    # should based on a referenced vector or bitmap", and 2026-09-16: "poetica
    # is my preferred fallback". So the shapes below come from the scan crops
    # (`aldine_autofit.SOURCES`) and from Poetica Std, and the WEIGHT from
    # Flanker Griffo Italic, which is the face that matches the 1501 page's
    # darkness. Everything is in units of xh/429 -- the a's convention
    # (`u = xh / A_UNIT`), so a number here is directly the number in
    # docs/albo-aldine-targets.md.
    #
    # WHAT THE SEVEN LETTERS SHARE, and where each number is from. Every
    # position below is a fraction of the STEM PITCH P measured from the left
    # stem's CENTER, or a fraction of the x-height -- so the arch is the same
    # curve however wide the letter is set, which is what makes h m n r u one
    # hand instead of five letters that happen to have stems.
    #
    #   THE STEM   70 units. Flanker holds exactly 70 on 19 of its 26 lowercase
    #              (targets doc, section 2: "h m n r u -- every stem 70"), dead
    #              constant from .25 to 1.40. The module's I_STEM (0.64 x S =
    #              43 units, and it measured 45) is what made the paragraph
    #              proof read spindly; the a already draws 70.
    #              Its top is CUT down to the right: Flanker's i runs 9-79 at
    #              .88 and 6-46 at .99, so the top face falls ~45 degrees.
    #   THE HEAD   NOT a flick, and not "further right than left" -- that older
    #              reading of the macro took the stem's position at the
    #              BASELINE and compared it with the head 50 rows higher, which
    #              on a 13-degree page is 12 px of shear. Corrected here: at
    #              the head's own height the scan i's ink runs 55 units LEFT of
    #              the stem and 17 right (rows .80-.95), Flanker's i 83 left,
    #              Poetica's n 69 left. It is an ENTRY -- the nib set down
    #              below and left, pushed up and right across the stem's top.
    #              Its tip sits 0.155 x xh below the stroke's top in BOTH
    #              Flanker's i (x-height) and its l (ascender), so one helper
    #              serves the x-height letters and the ascenders.
    #              Its underside is HOLLOW: Flanker's i at .85 shows the tip
    #              detached (-74..-40) with 21 units of white before the stem,
    #              which a straight stroke cannot do -- hence HM_HEAD_BOW.
    #   THE ARCH   springs off the stem's center at ~0.36 xh, is inside the
    #              stem until ~.55 (the doc's "the arch springs at HALF the
    #              x-height and the spring is 84-100 wide -- a junction, not a
    #              stroke"), climbs as the page's HAIRLINE and arches over with
    #              its apex just short of the right stem.
    #              Normalized, Flanker and Poetica are the SAME curve: at .70
    #              the arch's center is 0.381 P along in Flanker and 0.373 in
    #              Poetica; at .80, 0.521 and 0.527; the apex 0.930 and 0.933.
    #              That agreement is why the arch is written in P at all.
    #              Its thickness is 22 units (the doc's hairline, 22-24),
    #              measured TWICE on the same stroke: Flanker's n gives a
    #              32-unit horizontal run and a 33-unit vertical run where the
    #              arch climbs at 48 degrees, and 32*sin48 = 23.4 against
    #              33*cos48 = 22.0. Two cuts agreeing is what makes it a
    #              stroke width rather than a run.
    #   THE EXIT   the last stem of h m n u, and i and l, finishes with an
    #              outstroke that rises: Flanker's i has a DETACHED tip at .15
    #              (149-162) 76 units right of the stem, Poetica's at .25
    #              (159-175) 63 right, the scan m's at .30 about 85 right. The
    #              left stems of h m n have none -- Flanker's n reads exactly
    #              70 at .02, and only the LAST stem of the m reads 88.
    #              The tip's HEIGHT is the reference median and a sweep agrees:
    #              0.11 to 0.27 scored on all seven letters against Poetica and
    #              the scans moves the u .571 -> .597, the i .527 -> .545 and
    #              the i against its own scan .400 -> .449, costing the h .007.
    #              0.25 is Poetica's own and one step under the printed m's.
    #   THE PITCH  0.470 x xh. The three sources split: the scan m's three stem
    #              centers are 184 units apart (a horizontal distance at one
    #              height, so shear-invariant and trustworthy), Poetica's n is
    #              194, and Flanker's n 286 with its m at 249. Poetica and the
    #              printed page are close and Flanker is a much wider face, so
    #              the wide reading is dropped; the module meanwhile had three
    #              different pitches -- h 263, n 239, m 190 -- which is the
    #              opposite of one hand.
    #              The final 0.470 is a SWEEP, not either reading: 0.425 to
    #              0.500 in six steps, scored on h m n r u against Poetica and
    #              against the four scans at once. It trades -- the h wants it
    #              narrow against Poetica (.507 at 0.425, .394 at 0.500) and the
    #              u wants it wide (.483 -> .596) -- and 0.470 is the joint
    #              best against Poetica (sum 3.110, against 3.083 at 0.455 and
    #              3.008 at 0.485) and within .05 of the best against the scans.
    #              A dial this shared cannot be fitted on one letter.
    #
    # WHAT WAS FITTED AND WHAT WAS NOT. HEAD_L/D/R/W/T, HEAD_BOW, EXIT_R/Y/T
    # and TOPCUT below were coordinate-descended by `aldine_fit_shape.py i
    # --ref flanker` (IoU .707 -> .726) and then moved back to the measured
    # value where a sweep across all seven letters disagreed with the single-
    # letter fit; PITCH and EXIT_Y are sweeps, not fits.
    #
    # DO NOT FIT THESE AGAINST POETICA. Its lowercase stem is 57 units against
    # the 70 this family is ruled to, so an overlap score charges Albo for ink
    # it is required to have, and the cheapest way for a solver to buy that
    # back is to AMPUTATE the thin parts: a full run against Poetica's n drove
    # HEAD_L 80 -> 50, HEAD_BOW to 0, EXIT_R 74 -> 53 and EXIT_Y 0.185 ->
    # 0.105, deleting most of the entry and the outstroke for +0.04 of IoU.
    # Flanker's stem IS 70, so its i -- stem, head, exit and nothing else --
    # is the honest target for these dials.
    #
    # AND THE SCORE HAS A CEILING THIS ROUND MAY NOT REACH. Rebuilding this
    # same drawing with the REFERENCE's own family settings measures it:
    # at Poetica's rendered slant (9.1 degrees against the family's 13) the l
    # goes .228 -> .512 and the h .452 -> .697 while the x-height letters
    # barely move; at its 57-unit stem the l gains another .080 and the n, m
    # and r LOSE .02-.08; at its 723 ascender the l gains .066. With all three
    # forced the best any of the seven reaches is .706. So a target of .80
    # against Poetica is not a shape target at all -- it is FJORD_SLANT,
    # FJORD_ASC and the stem ruling, none of which is this round's to move.
    HM_UNIT = 429.0

    def _hm(name, default):
        return float(os.environ.get("ALBO_ALD_HM_" + name, default))

    HM_STEMW = _hm("STEMW", 70.0)       # units
    HM_PITCH = _hm("PITCH", 0.470)      # stem center to stem center, x xh
    HM_TOPCUT = _hm("TOPCUT", 45.0)     # the stem's top face, degrees down to the right
    HM_HEAD_L = _hm("HEAD_L", 70.0)     # the head's tip CENTER, units LEFT of the stem's left edge
    HM_HEAD_D = _hm("HEAD_D", 0.157)    # the tip, x xh BELOW the stroke's top
    HM_HEAD_R = _hm("HEAD_R", 0.04)     # where it ends, x the stem RIGHT of its center
    HM_HEAD_W = _hm("HEAD_W", 50.0)     # the head's body, units
    HM_HEAD_T = _hm("HEAD_T", 29.0)     # its tip, units
    HM_HEAD_BOW = _hm("HEAD_BOW", 0.014)   # the hollow under it, x xh
    HM_EXIT_R = _hm("EXIT_R", 84.0)     # the exit's tip, units RIGHT of the stem's right edge
    HM_EXIT_Y = _hm("EXIT_Y", 0.250)    # the tip's height, x xh
    HM_EXIT_T = _hm("EXIT_T", 19.0)     # the tip, units
    HM_ARCH_T = _hm("ARCH_T", 22.0)     # the climb's hairline, units
    HM_ARCH_TOP = _hm("ARCH_TOP", 0.935)   # the apex's centerline, x xh
    HM_SPRING = _hm("SPRING", 0.355)    # where the arch leaves the stem's center, x xh
    # the i's dot: the scan's is 89 x 64 units at 1.40 x xh, Flanker's 98 x 98
    # at 1.41, Poetica's 79 wide at 1.36. One touch of the nib, so it is an
    # OVAL LYING ON THE PEN'S ANGLE, not a disc -- and not a `stroke` either:
    # a 22-unit stroke 70 wide with the family's 20-degree cut on both ends has
    # its two end faces CROSS, `_unfold` drops the folded points, and what
    # rendered was a 45-unit triangle. Drawn as a rotated superellipse instead,
    # which at 84 x 44 on the 24-degree pen gives a 95 x 74 bounding box.
    # ---------------------------------------------------------- ROUND 135
    # THE DOT IS TWICE AS DEEP, AND IT IS CANCELLERESCA'S. Owner 2026-09-16:
    # *"double the height of the dot on i and j to match the relative size of
    # cancell."* Both halves of that sentence are true at one number, which is
    # why this is the change rather than a compromise between them:
    #
    #   MEASURED, Cancelleresca Bastarda's i rendered at a 400 px x-height --
    #   its dot is 76 x 81 px, so **0.190 xh wide by 0.203 xh tall**, aspect
    #   0.94, and it is a DISC: the row runs grow 18 -> 76 -> 13 with the
    #   widest rows in the middle and the center drifting only 6 px left over
    #   81 rows. Not a teardrop, not a sliver -- one full touch of a round nib.
    #   Albo's rendered 79 x 50 px, **0.125 xh tall**: a flat lozenge.
    #   Doubling the SHORT AXIS (44 -> 88 units) turns the lozenge into that
    #   disc and lands the rendered height on 0.204 xh against the reference's
    #   0.203. The long axis is left at the 84 the scan measured, because the
    #   owner asked about the dot's height and not its width; at 84 x 88 on the
    #   24-degree pen, through the build's 13-degree shear, the rendered box is
    #   86 x 87 units -- within 6% of Cancelleresca's on both axes.
    #
    # ITS HEIGHT ABOVE THE X-LINE IS THE REFERENCE'S TOO. Cancelleresca's dot
    # floor stands 0.242 xh clear of the x-line and its center 1.343 xh above
    # the baseline; at the old 1.400 center a dot this deep would have stood
    # 0.298 clear, which is a dot drifting off its own stem. 1.343 puts the
    # floor at 0.241.
    HM_DOT_LEN = _hm("DOT_LEN", 84.0)   # its long axis, units
    HM_DOT_TH = _hm("DOT_TH", 88.0)     # its short axis, units -- 2 x the 44 drawn to round 134
    HM_DOT_CY = _hm("DOT_CY", 1.343)    # its center, x xh above the baseline (Cancelleresca's)

    def hm_u(c):
        return c["xh"] / HM_UNIT

    def hm_stem(c, xc, y0, y1, w=None, cut=True):
        """A stem: straight, 70 units, its top face cut down to the right so
        the head can lie across it (Flanker's i, 9-79 at .88 -> 6-46 at .99).
        `y1` is where the top-LEFT corner lands. `cut=False` for a stem an ARCH
        lands on -- there the crown is the top, and a cut corner under it only
        pokes a spike through the shoulder."""
        u = hm_u(c); sw = (HM_STEMW if w is None else w) * u
        if not cut:
            return stroke([(xc, y0), (xc, y1)], sw)
        drop = math.tan(math.radians(HM_TOPCUT)) * sw / 2
        return stroke([(xc, y0), (xc, y1 - drop)], sw, cut1=-math.radians(HM_TOPCUT))

    def hm_head(c, xc, ytop, cap=0.0):
        """The entry stroke: up from the lower left, across the stem's top.
        Tapered at the tip -- Flanker's detached tip reads 34 units across a
        stroke running at 53 degrees, so 34*sin53 = 27 perpendicular -- and
        bowed, so its underside is hollow the way the reference's is.

        `cap` ROUNDS THE END the head stops on, x its own half width -- round
        143, the m only (0.0 is the cut face h l b d k and the m drew before,
        so those letters are byte-identical with the parameter absent). The
        end face is where the m's FIRST top peaks: on the dense outline that
        corner turns 71.5 degrees, the same knife-stop the two arch crowns
        have, and it is the only one of the m's three tops that is not an
        arch. It is rounded HERE rather than by laying a bead over the corner,
        which was tried first and is the wrong tool: the corner is CONVEX and
        its right flank falls at about 70 degrees, so every dome wide enough
        to round the apex jutted out past the stem as a slab."""
        u = hm_u(c); xh = c["xh"]; sw = HM_STEMW * u
        # the END is the CENTERLINE's end: a stroke this thick running at ~53
        # degrees puts its upper edge 0.30 of its width above the centerline,
        # and the references' ink top is exactly the x-line (Flanker's n and i
        # both bbox at 429) -- the head does not rise above it.
        tip = (xc - sw / 2 - HM_HEAD_L * u, ytop - HM_HEAD_D * xh)
        end = (xc + HM_HEAD_R * sw, ytop - 0.30 * HM_HEAD_W * u)
        mid = ((tip[0] + end[0]) / 2, (tip[1] + end[1]) / 2 + HM_HEAD_BOW * xh)
        p = catmull([tip, mid, end], tension=0.5)
        body = stroke(p, widths([(0.0, HM_HEAD_T * u), (0.55, HM_HEAD_W * u),
                                 (1.0, HM_HEAD_W * 0.86 * u)]), cut0=CUT, cut1=CUT)
        if cap <= 0.0:
            return body
        # AN ELLIPSE ON THE END FACE, not a disc. The face is `hw` half-wide,
        # so a disc of any radius under hw pokes out of the middle of it as a
        # LUMP instead of rounding it -- measured at cap 0.5, which drew a bead
        # on the shoulder. Matching the ellipse's minor axis to hw and scaling
        # only its major axis along the direction of travel makes the dial
        # continuous: 0 is the cut face, 1 a true half-round.
        hw = HM_HEAD_W * 0.86 * u / 2
        ang = math.atan2(end[1] - mid[1], end[0] - mid[0])
        return geom.union([body, geom.poly(superellipse(end[0], end[1],
                                                        cap * hw, hw,
                                                        0.0, 2 * math.pi, 2.0,
                                                        rot=ang))])

    def hm_exit(c, xc):
        """The outstroke: down the stem, round the baseline, out RIGHT and UP
        to a hairline tip. One stroke, started inside the stem so there is no
        seam where it leaves."""
        u = hm_u(c); xh = c["xh"]; sw = HM_STEMW * u
        tip = (xc + sw / 2 + HM_EXIT_R * u, HM_EXIT_Y * xh)
        # IT IS SHORT AND IT CLIMBS: a hook round the baseline, then a
        # straight run at about 45 degrees. Measured off Flanker's i as the
        # ink's right edge against the stem's -- 27 units past it at .02, 45 at
        # .05, 75 at .10, 83 at the tip -- so the outer edge rises at about 54
        # degrees and it is ONE CONTINUOUS RUN from the stem the whole way
        # (14-154 at .10). The knee therefore sits at the stem's own right
        # edge, not out in the margin. The first cut drew a long low flick that
        # left the stem at the baseline and had pinched off into a detached
        # curl by .05.
        #
        # THE UNDERSIDE lands on the overshoot, not the centerline: the stroke
        # is ~0.94 x the stem where it rounds the baseline, so a centerline at
        # -5 hangs its lower edge 38 units under the line. Flanker's i and n
        # bottom out at exactly -9 and this module's own a at -4; the first cut
        # of these seven sat at -34, which is a sunk letter.
        botY = sw * 0.47 - 9 * u
        knee = (xc + sw * 0.56, botY + 9 * u)
        d = (tip[0] - knee[0], tip[1] - knee[1])
        p = catmull([(xc, xh * 0.26), (xc + sw * 0.05, botY + 22 * u), (xc + sw * 0.30, botY),
                     knee,
                     (knee[0] + d[0] * 0.42, knee[1] + d[1] * 0.42),
                     (knee[0] + d[0] * 0.76, knee[1] + d[1] * 0.76), tip],
                    tension=0.5)
        return stroke(p, widths([(0.0, sw), (0.36, sw * 0.94), (0.66, sw * 0.78),
                                 (0.88, sw * 0.48), (1.0, HM_EXIT_T * u)]), cut1=CUT)

    # The arch's centerline, as (fraction of the pitch from the left stem's
    # CENTER, fraction of the x-height). The middle five come straight off
    # Flanker's n -- vertical cuts at x 120/160/200/240/270 put the stroke's
    # center at .575/.694/.796/.875/.907 of the x-height, which normalize to
    # .234/.374/.514/.654/.759 of that letter's 286-unit pitch -- and Poetica
    # lands within .01 of every one of them.
    HM_ARCH_K = [(0.234, 0.575), (0.374, 0.694), (0.514, 0.796),
                 (0.654, 0.875), (0.800, 0.925)]

    def hm_arch(c, x0, x1, drop=0.0, crown=0.0):
        """ONE movement: out of the stem low, up as a hairline, over the top,
        down into the next stem. Not a shoulder turned near the top.

        `drop`  LOWERS THE WHOLE SHOULDER by this much, x xh -- round 143, the
                m only, and 0.0 is what h n r and both of the m's arches drew
                to round 142. It is weighted in from 0.45 P and taken back to
                0.45 of itself at the landing, so the climb and the junction
                are left where they were and only the top of the arch moves.

                IT IS NOT A DIAL ON HM_ARCH_TOP, and that is measured rather
                than assumed: HM_ARCH_TOP is the CENTERLINE's height at 0.930
                P, but the ink's top there is centerline + half the width, and
                the width is ramping 2t -> sw across exactly that span -- so
                the outline's crest sits at a different t and moving the
                centerline knot alone transmits only about a SIXTH of itself.
                Measured: a 0.020 xh cut to HM_ARCH_TOP for the right arch
                moved its rendered apex 0.0034 xh, and reaching 0.020 that way
                would need a knot below HM_ARCH_K's own last point (0.925),
                which inverts the crest and makes the letter worse.
        `crown` HAND-CUT ROUNDING on the crown, x xh -- round 143, the m only
                (owner 2026-09-16, *"make all three slightly rounded by
                handcuts"*). 0.0 is the turn every other letter in the family
                draws, so h n r are byte-identical with the parameter absent.

        WHY THE CROWN IS ANGULAR AT crown=0, measured on the dense outline
        (`FJORD_CUT=0`, m, contour 0): the apex is TWO corners 26 units apart
        -- (360.1, 412.8) turning 37.4 degrees and (339.5, 428.3) turning 49.6
        -- with one flat facet between them. That is a knife stopping, not a
        pen turning. It comes from the tail of the centerline, which crests at
        0.930 P and then falls 0.155 xh in the remaining 0.070 P (a slope of
        -4.7) while the width ramps 2t -> sw over the same run: the outer edge
        folds, `_unfold` drops the folded points, and the crease is what is
        left. Rounding it therefore means easing the TAIL, not adding a fillet
        to the finished polygon -- crest a little earlier, come off the crest
        in two steps rather than one, and start the width's climb to the stem
        sooner so it is not doing all its growing inside the turn."""
        u = hm_u(c); xh = c["xh"]; P = x1 - x0; sw = HM_STEMW * u
        tp = HM_ARCH_TOP

        def lower(fx, fy):
            """`drop`, weighted: nothing below 0.45 P, smoothstepped in to its
            full value by 0.90, and held at 0.45 of itself at the landing so
            the arch still finishes inside the next stem's top."""
            if drop <= 0.0 or fx <= 0.45: return fy
            if fx >= 1.0: return fy - drop * 0.45
            t = min(1.0, (fx - 0.45) / 0.45)
            return fy - drop * (t * t * (3 - 2 * t))

        # the landing runs BELOW the stem's own top (0.86 xh) so the arch's
        # blunt end face is buried inside it; ending them level left a hairline
        # white slit across the junction on the m's second and third stems.
        t = HM_ARCH_T * u
        prof = [(0.00, sw * 0.94), (0.14, t * 1.15), (0.36, t),
                (0.60, t * 1.30), (0.80, t * 2.00), (1.00, sw)]
        if crown <= 0.0:
            K = [(0.0, HM_SPRING)] + HM_ARCH_K + [(0.930, tp), (1.0, 0.780)]
        else:
            # THE CREST, AS AN ARC RATHER THAN A VERTEX. Measured on the
            # centerline itself: it runs (0.800 P, 0.925 xh) -> (0.930, tp) ->
            # (1.000, 0.780), which in units at this pitch is a turn from +9.3
            # degrees to -78.0 -- an 87-degree corner taken in 14 units. The
            # width profile is NOT touched here; moving it was tried first
            # (four arms, `prof` reaching sw by 0.86-0.92) and every one of
            # them stepped the landing: the stroke arrived at the next stem
            # already stem-wide and left a nick above the junction.
            #
            # Instead two knots are added, one each side of the apex, each
            # pushed OUTWARD off the straight line it would otherwise sit on
            # -- which is what turns a vertex into an arc. `crown` is the
            # outward push in xh, so 0 is the vertex and larger is rounder.
            # the crest's own geometry, swept once (five arms at crown 0,
            # .015, .030, .050, .080 rendered at a 600 px x-height) and then
            # fixed: the apex stays at 0.930 P, a knot goes 0.055 P before it
            # and 0.040 P after, and the two are pushed out by 0.55 and 0.85 of
            # `crown`. The asymmetry is the descent's -- the tail falls nearly
            # five times as fast as the climb rises, so the knot on that side
            # has to come further off its chord to turn the same amount.
            fa, ga, gb = 0.930, 0.055, 0.040
            wa, wb = 0.55, 0.85
            fb = fa - ga; fc = fa + gb
            # where each inserted knot would sit on the straight chords
            yb = 0.925 + (fb - 0.800) / (fa - 0.800) * (tp - 0.925)
            yc = tp + (fc - fa) / (1.0 - fa) * (0.780 - tp)
            K = ([(0.0, HM_SPRING)] + HM_ARCH_K
                 + [(fb, yb + crown * wa), (fa, tp), (fc, yc + crown * wb),
                    (1.0, 0.780)])
        p = catmull([(x0 + fx * P, lower(fx, fy) * xh) for fx, fy in K], tension=0.5)
        return stroke(p, widths(prof))

    def ij_dot(c, xc):
        """THE DOT OF THE i AND THE j, drawn ONCE and called by both.

        It was two drawings until round 135, and they had already drifted: the
        i's was this rotated superellipse (rendered 79 x 50 px at a 400 px
        x-height) while the j's was a `stroke` on I_DOT_W / I_DOT_T (88 x 76).
        An i and a j on the same page have to wear the same dot -- the module
        said so in the j's own comment and then drew a second one anyway -- so
        the construction is a function now and the j calls it."""
        xh = c["xh"]; u = hm_u(c)
        return geom.poly(superellipse(xc, HM_DOT_CY * xh, HM_DOT_LEN * u / 2,
                                      HM_DOT_TH * u / 2, 0.0, 2 * math.pi, 2.1,
                                      rot=math.radians(HEAD_DEG)))

    @glyph('i')
    def a_i(c):
        """Stem, head, exit, dot. The scan's i is the family's cleanest single
        stroke, and the dot is one touch of the nib: 89 x 64 units on the scan
        (rows 1.35-1.45), 98 x 98 in Flanker, centered 1.40 x xh above the
        baseline in both. Drawn 84 x 88 on the pen's own angle since round 135
        -- Cancelleresca's disc, by the owner's ruling; see the dial block."""
        xh = c["xh"]; u = hm_u(c); x = S * 1.0
        parts = [hm_stem(c, x, 0, xh), hm_head(c, x, xh), hm_exit(c, x)]
        parts.append(ij_dot(c, x))
        return geom.ink(parts)

    @glyph('l')
    def a_l(c):
        """The i's stem carried to the ascender. Flanker puts the head's tip
        0.15 x xh below the ascender's top (l: -62 at 1.60, top 1.75) and
        0.155 below the x-line on the i -- the same shape at the same drop,
        which is why hm_head takes the top as an argument."""
        return geom.ink([hm_stem(c, S * 1.0, 0, c["asc"]),
                         hm_head(c, S * 1.0, c["asc"]), hm_exit(c, S * 1.0)])

    @glyph('n')
    def a_n(c):
        """Two stems one pitch apart, one arch, one head, one exit. The left
        stem has NO foot: Flanker's n reads exactly 70 at .02, and the foot the
        module used to put there was a roman's, not a chancery hand's."""
        xh = c["xh"]; x0 = S * 1.0; x1 = x0 + HM_PITCH * xh
        return geom.ink([hm_stem(c, x0, 0, xh), hm_head(c, x0, xh), hm_arch(c, x0, x1),
                         hm_stem(c, x1, 0, xh * 0.86, cut=False), hm_exit(c, x1)])

    # ------------------------------------------------ ROUND 143, THE m ALONE
    # Owner 2026-09-16, verbatim: *"the arches of 'm' need to be slightly
    # different. the right one can be slightly wider and shorter. and the
    # middle brush stroke should be rounded and not reach the baseline. make
    # all three slightly rounded by handcuts"*.
    #
    # WHICH THREE. An m has TWO arch SPANS and THREE tops along the x-line --
    # the left stem under its head, then the two arches. "The right one" is
    # the right span; "all three" is read as the three TOPS, so the first one
    # is rounded too, at the head's end face (`hm_head(cap=)`) rather than at
    # a crown. The sentence can also be read as the three BRUSH STROKES, in
    # which case "all three slightly rounded" would mean the other two FEET as
    # well; that reading is not taken, because the first foot is the letter's
    # baseline junction and the third is already the outstroke's turn, and
    # because rounding either was not asked for in the sentence that names the
    # arches. It is worth a ruling if he meant the feet.
    #
    # EVERY DIAL HERE IS THE m's OWN. h n r u i l b d k are drawn by the same
    # hm_* helpers and must not move: the three parameters added (`hm_arch`'s
    # `drop` and `crown`, `hm_head`'s `cap`) all default to 0.0, which is
    # exactly what those letters drew to round 142, and `m_midstem` is new and
    # called from nowhere else. PROVEN, NOT ASSERTED -- two FJORD_CUT=0 builds
    # diffed outline by outline (289 designed glyphs, 288 identical) and the
    # two shipped TTFs diffed by glyf coordinates, hmtx and components (470
    # glyphs, 469 identical). The m is the only thing in the font that moves.
    #
    # WHAT THE REFERENCES DO WITH AN m's TWO ARCHES, measured 2026-09-16 by
    # rendering each face's m at a 600 px x-height, de-shearing on the stems'
    # own fitted slant, and reading the stems off least-squares lines in the
    # band 0.27-0.40 xh -- the only band where all three stems stand alone. A
    # band reaching the baseline reads the outstroke as part of the third stem
    # and reports the right arch 20% wider than it is, which is the first
    # wrong answer this measurement gave.
    #
    #   face                    pitch R/L   apex R-L    crown R-L   counter R/L
    #   Flanker Griffo Italic     1.0125    +0.0000     +0.0050       0.9991
    #   Poetica Std               1.0085    +0.0000     -0.0033       1.0043
    #   TeX Gyre Pagella Italic   1.0248    +0.0000     -0.0317       1.0141
    #   Cancelleresca Bastarda    0.9850    +0.0000     +0.0000       0.9850
    #   Albo, round 142           0.9998    +0.0000     +0.0017       1.0296
    #
    # APEX is the arch's own top; CROWN is how high the arch stands over the
    # CENTRE of its counter. They are different questions and they give
    # different answers, which is why both are here:
    #
    #   * ON HEIGHT, NOT ONE REFERENCE DIFFERENTIATES. All four top BOTH
    #     arches at 0.9997-0.9999 xh -- dead on the x-line, zero difference to
    #     the pixel. "Shorter" therefore has no period precedent at all and is
    #     purely the owner's drawing decision.
    #   * ON WIDTH AND ON THE SHOULDER OVER THE COUNTER, PAGELLA ALONE DOES:
    #     right arch 2.5% wider, shoulder 0.032 xh lower. The other three are
    #     within 1.5% and 0.005 xh, which is this measurement's own floor.
    #     Albo was the flattest twin of the lot -- 0.02% and 1 px -- because
    #     a_m called one `hm_arch` twice with the same numbers.
    #
    # So Pagella sets the CEILING on the width and "slightly" sets the value.
    # Drawn: +2.000% on the pitch (exact, off the designed outline: the stem
    # centres go 86.26 / 287.89 / 493.55, pitches 201.630 and 205.663) and a
    # rendered apex 0.0183 xh lower on the right, against 0.0000 for every
    # reference.
    #
    # AND NO REFERENCE LIFTS THE MIDDLE FOOT EITHER. Measured the same way,
    # the m's three feet in all four sit level within 2 px at a 600 px
    # x-height (mid-vs-left +0.000, +0.000, -0.003, +0.000 xh). The lift below
    # is the owner's drawing decision too, so it was laddered on the PAGE at
    # 27 px rather than fitted to anything: see M_MID_LIFT.
    def _m(name, default):
        return float(os.environ.get("ALBO_ALD_M_" + name, default))

    # the RIGHT arch's pitch, x the left's. 1.020 = +2.0%, under Pagella's
    # +2.5% and above the 1.5% floor the other three references sit inside.
    # It widens the m's advance by 4 units of 634, which is +0.64%.
    M_A2_W = _m("A2_W", 1.020)
    # the RIGHT arch's shoulder, LOWERED by this much x xh. It transmits at
    # about 0.63 to the rendered apex (laddered 0.020 / 0.025 / 0.029 / 0.031 /
    # 0.035 / 0.045, giving -0.0117 / -0.0167 / -0.0183 / -0.0233 / -0.0283 /
    # -0.0383 xh), so 0.029 is the value nearest a 0.020 xh drop that the
    # raster can actually resolve -- it renders -0.0183, and its neighbour
    # 0.030 jumps to -0.0233.
    M_A2_DROP = _m("A2_DROP", 0.029)
    # the hand cut on a crown, x xh. Laddered 0 / .015 / .030 / .050 / .080 at
    # a 600 px x-height: .015 is still a vertex, .080 flattens the crest into
    # a wide table, and .035 turns the corner over three facets, which is a
    # knife rounding a corner in two or three cuts. It moves the apex 1 px in
    # 600, so "slightly rounded" costs the arch no height.
    M_CROWN = _m("CROWN", 0.035)
    # the middle stem's foot, x xh above the baseline. NOT fitted -- no
    # reference lifts it -- so it was laddered on the page: at 27 px the
    # x-height is 11.6 px, so 0.030 xh is 0.35 px and invisible, 0.120 xh is
    # 1.39 px and reads as a broken stem, and 0.060 xh is 0.70 px, which
    # renders as a lightened foot rather than a gap. Rendered lift 0.0617 xh.
    M_MID_LIFT = _m("MID_LIFT", 0.060)
    # its rounding, x the stem's width (0.5 = a full half-round)
    M_MID_FOOT = _m("MID_FOOT", 0.50)
    # the FIRST top's round, x the head's half width. 0.30 is WORSE than 0
    # (the hand cut decimates a shallow ellipse into a horn on the shoulder)
    # and 1.00 is a bulb; 0.60 rounds the 71.5-degree corner and nothing else.
    M_HEAD_CAP = _m("HEAD_CAP", 0.60)

    def m_midstem(c, xc, lift, top):
        """THE m's MIDDLE BRUSH STROKE -- owner 2026-09-16: *"the middle brush
        stroke should be rounded and not reach the baseline"*. It is the only
        one of the m's three verticals that is neither entered (the first
        carries the head) nor left (the third carries the outstroke), so it is
        the one a written hand lifts off early, and the only one whose foot is
        a free end rather than a junction.

        Two changes from `hm_stem`, and they belong together: the stroke stops
        `lift` x xh ABOVE the baseline, and the foot it stops on is ROUND
        instead of the square face a `stroke` ends in. A square face floating
        clear of the line reads as a broken stem; the round one reads as a pen
        lifting. The cap is a half-superellipse on the stem's own width, so
        the foot is exactly as wide as the stroke and the build's shear turns
        it into the leaning oval a slanted pen actually leaves."""
        u = hm_u(c); sw = HM_STEMW * u
        r = M_MID_FOOT * sw                  # the cap's depth below the shaft
        y0 = lift + r
        cap = geom.poly(superellipse(xc, y0, sw / 2, r, math.pi, 2 * math.pi, 2.0))
        return [stroke([(xc, y0), (xc, top)], sw), cap]

    @glyph('m')
    def a_m(c):
        """Three stems -- the doc's "three stems at 70/70/70" -- but since
        round 143 NOT at one pitch and NOT under one arch drawn twice. The
        right arch spans M_A2_W of the left's and its shoulder is M_A2_DROP
        lower; all three tops are hand-cut, the two crowns by M_CROWN and the
        first by the round on the head's end; and the middle brush stroke
        lifts M_MID_LIFT clear of the baseline onto a round foot. The dial
        block above says what each number was measured against -- including
        that three of the four references draw the two arches as one arch, and
        that none of the four lifts the middle foot at all."""
        xh = c["xh"]; x0 = S * 1.0; d = HM_PITCH * xh
        x1 = x0 + d; x2 = x1 + d * M_A2_W
        return geom.ink([hm_stem(c, x0, 0, xh), hm_head(c, x0, xh, cap=M_HEAD_CAP),
                         hm_arch(c, x0, x1, crown=M_CROWN),
                         hm_arch(c, x1, x2, drop=M_A2_DROP, crown=M_CROWN),
                         *m_midstem(c, x1, M_MID_LIFT * xh, xh * 0.86),
                         hm_stem(c, x2, 0, xh * 0.86, cut=False),
                         hm_exit(c, x2)])

    @glyph('h')
    def a_h(c):
        """The n with its left stem carried to the ascender. The macro's h
        finishes its right leg with an INWARD hook (its .05 row sits 60 units
        left of its .20 row) -- a real feature of that printing and not taken,
        because both digital references and the m's own last stem exit to the
        RIGHT, and one letter cannot leave the family to follow one page."""
        xh = c["xh"]; x0 = S * 1.0; x1 = x0 + HM_PITCH * xh
        return geom.ink([hm_stem(c, x0, 0, c["asc"]), hm_head(c, x0, c["asc"]),
                         hm_arch(c, x0, x1), hm_stem(c, x1, 0, xh * 0.86, cut=False), hm_exit(c, x1)])

    # THE STEM PITCH, measured three ways on griffo-macro.png and agreeing:
    # the m of "tumulum" puts its stems near x505/532/560, and the l and the
    # following u sit at 680 and 709 -- about 28 px on a 54 px x-height, so
    # **0.52 x xh between stem centers**. Everything else in the u is already
    # measured on the i: the stem at 0.64 x S, the wedge head, the exit.
    U_PITCH = float(os.environ.get("ALBO_ALD_U_PITCH", 0.52))   # stem centers, x xh
    U_JOIN = float(os.environ.get("ALBO_ALD_U_JOIN", 0.30))     # where the bottom curve meets, x xh

    # THE u, round 132 -- redrawn on the family's own stem, head and exit.
    # The old cut is corrected on three counts, each measured:
    #   ITS LEFT STEM IS STRAIGHT. Flanker reads 29-99 at .25 AND at .75, and
    #     Poetica 47-104 at .40 and .60 -- a dead-constant 70. The one-path
    #     catmull bowed it (a control point 0.02 P left of the stem), and a
    #     bowed stem beside the h's straight one is two hands.
    #   ONE HEAD, NOT TWO. Flanker's u widens to 132 at .90 on the LEFT run
    #     only, its right run staying 70 and tapering to 63 at .97; Poetica's
    #     right stem goes 56 -> 53 -> 31 with no widening anywhere. The right
    #     stem's top is where an upstroke ARRIVES, and an arrival is not an
    #     entry.
    #   THE RISE MEETS THE RIGHT STEM AT HALF THE X-HEIGHT. Flanker's rise is
    #     a detached 32-unit run at .25, centered 0.577 of the pitch along, and
    #     is absorbed into the stem by .55; Poetica's is at 0.605 P at .25.
    # The bottom turn's own low point sits 0.22 P along, a touch under the
    # baseline -- Flanker's ink bottom is -9 and its .03 row runs 45-142.
    U_RISE_X = float(os.environ.get("ALBO_ALD_U_RISE_X", 0.590))  # the rise at .25 xh, x the pitch
    U_BOT_X = float(os.environ.get("ALBO_ALD_U_BOT_X", 0.15))     # the turn's low point, x the pitch

    @glyph('u')
    def a_u(c):
        """Written, not assembled: ONE movement makes the left stem, the bottom
        turn and the rise -- down, around, up -- and a second stroke brings the
        right stem down to the baseline and out. The pen's widths along that
        one path do the work: full down the left, thinning through the turn,
        hairline on the rise, which is what an upstroke is."""
        xh = c["xh"]; u = hm_u(c); x0 = S * 1.0; P = HM_PITCH * xh
        x1 = x0 + P; sw = HM_STEMW * u
        # down (dead straight), around, up -- one path
        # The stem stays DEAD STRAIGHT to .24 and the turn happens under it:
        # Poetica reads 47-104 at .50, 48-106 at .35 and 49-110 at .25, and only
        # at .20 does the run run away (50-115). And THE TURN IS FULL WIDTH --
        # Poetica's bottom run at .02 is 72, exactly its stem, and Flanker's 97
        # -- so the thinning belongs on the RISE, which is the upstroke. The
        # first cut thinned through the turn itself and the bottom pinched in
        # two at .05, where both references show one continuous mass.
        p = catmull([(x0, xh * 0.95), (x0, xh * 0.58), (x0, xh * 0.24),
                     (x0 + P * 0.05, sw * 0.48 + 22 * u), (x0 + P * U_BOT_X, sw * 0.48 - 9 * u),
                     (x0 + P * 0.38, sw * 0.48 - 3 * u), (x0 + P * U_RISE_X, xh * 0.25),
                     (x0 + P * 0.84, xh * 0.50), (x0 + P * 0.97, xh * 0.66)],
                    tension=0.5)
        prof = widths([(0.00, sw), (0.42, sw), (0.55, sw * 0.96), (0.66, sw * 0.72),
                       (0.76, HM_ARCH_T * u * 1.25), (0.90, HM_ARCH_T * u * 1.45),
                       (1.00, sw * 0.70)])
        parts = [stroke(p, prof, cut0=-math.radians(HM_TOPCUT))]
        # the second stroke: the right stem down to the baseline, and out
        parts += [hm_stem(c, x1, 0, xh * 0.985), hm_exit(c, x1), hm_head(c, x0, xh)]
        return geom.ink(parts)

    # MEASURED off the o of "udos" in griffo-macro.png: x145-185, y61-114 --
    # 41 wide by 54 tall, w/h 0.759, counter/ink 0.617.
    #
    # THE STRESS was read properly rather than guessed: walking a ray out from
    # the letter's center every 10 degrees and taking the FIRST contiguous band
    # of ink. The naive "last ink out" walks into the neighbouring s and
    # reports 30 px of stroke, which is how a stress measurement goes wrong
    # without anyone noticing. Thickness peaks at 50 deg (13.8 px) and bottoms
    # near 110 and 290 (about 5) -- so the PEN ANGLE is ~50 deg, a conventional
    # steep italic nib, and the contrast is ~2.8:1. Mean 8.7 px = 0.161 x xh =
    # 0.82 x the stem, which sits with the e's flanks at 0.79.
    # ROUND 132, DRAWN AGAINST THE REFERENCE. Two of the three numbers above
    # were wrong, and both were wrong for the same reason: a RAY out of the
    # centre measures a RADIAL run, which over-reads wherever the ring's own
    # normal is not radial -- worst at 45 degrees, which is exactly where the
    # 50-degree reading landed. The distance transform does not have that
    # error (at the stroke's medial axis the distance to the background IS
    # half the perpendicular width, whatever direction the stroke runs), and
    # re-measured that way the scan, Flanker and Poetica all agree:
    #
    #   THE THIN SITS AT ~105 AND ~285 DEGREES, not 135/315. Perpendicular
    #     thickness by angle, geometric, in Albo's units: scan 90:33 105:29,
    #     Flanker 90:30 105:23, Poetica 105:21 285:23. The thick is a broad
    #     plateau (Flanker 0-30 at 66-71, the scan 15-60 at 69-93) whose peak
    #     the three references put in different places, so the THIN is the
    #     feature to key on -- it is sharp and all three agree on it. As drawn,
    #     Albo's thin was at 135/315: a ring rotated 30 degrees off its
    #     reference, which no dial in this block could say.
    #   THE RING IS ROUNDER THAN THE FAMILY'S 2.1. Run width is
    #     shear-invariant, so a scan row width compares directly with an
    #     outline's. At .90 the scan is 154 wide and the drawn o 212; at .03,
    #     90 against 145; at .25, 260 against 291. Solving the superellipse
    #     for each gives k 1.6 at .90 and 1.7 at .25, against 2.15 as drawn --
    #     the o's top and bottom were too FLAT, and that is where the extra
    #     width was.
    #
    # THE WEIGHT IS ONLY PARTLY CORRECTED, and the limit is a ledger row
    # rather than a judgment. Flanker's ring is 66-71 at the thick where this
    # one was 104, so matching it outright would be right for the colour -- but
    # `cmp_aldine_metrics` holds the o at counter/ink 0.617, measured off the
    # scan, and a Flanker-weight o measures **1.322** there: twice the target,
    # a failed row. The scan itself measures 0.559, so that target is a
    # property of the printed page's INK SPREAD and not of the letter, and the
    # two instructions cannot both be met. The ledger wins, the conflict is
    # reported rather than silently split, and the thick came down as far as
    # the row allows -- 1.63 to 1.44 x S, which lands counter/ink at 0.626
    # (+2%) and w/h at 0.761 against the ledger's 0.759. The two shape moves
    # above are free of all of it: rotating the stress and rounding the
    # shoulders spend no ink at all.
    O_W = float(os.environ.get("ALBO_ALD_O_W", 0.76))          # width, x xh
    O_K = float(os.environ.get("ALBO_ALD_O_K", 1.72))          # squareness; 1.6-1.7 off the scan's row widths
    # 25 -> 35 in round 134 (the bulge pass): at 25 the ring's thick sat
    # square on the flank's middle, 1.27 by cmp_aldine_bulge.py against
    # Flanker's 1.15; at 35 it slides toward the lower left, 1.11, and the
    # bow reads 1.15 against 1.17. 45 overshoots (1.07 / 0.72).
    O_PEN = float(os.environ.get("ALBO_ALD_O_PEN", 35.0))      # the nib's angle, degrees
    # RULED 2026-09-16: the o takes the REFERENCE's ring weight, and the
    # ledger row moves with it. The scan's counter/ink of 0.617 is the printed
    # page's INK SPREAD, not the punch -- holding it put 104 units of ring on
    # a letter whose reference draws 66-71, and the o was the darkest thing in
    # any line. At 1.08 the o's mean ink width is 0.91 of the n's, against
    # Flanker's own 0.90 -- the letter now sits with its neighbours instead of
    # anchoring the page.
    O_THICK = float(os.environ.get("ALBO_ALD_O_THICK", 1.08))  # x S, at the pen's fullest
    O_THIN = float(os.environ.get("ALBO_ALD_O_THIN", 0.590))    # x S, across the nib

    @glyph('o')
    def a_o(c):
        xh = c["xh"]; rx = O_W * xh / 2; ry = xh / 2 + OVER * 0.5
        cx = S * 0.6 + rx
        outer = superellipse(cx, ry - OVER * 0.5, rx, ry, 0.0, 2 * math.pi, O_K)[:-1]
        phi = math.radians(O_PEN)
        _thick, _thin = (con([O_THIN, O_THICK], CON_O)[::-1] if CON_O else (O_THICK, O_THIN))
        def wf(t):
            th = t * 2 * math.pi
            return S * (_thin + (_thick - _thin) * abs(math.cos(th - phi)))
        return geom.ink([PR.ring_from(outer, widths_fn=wf, smooth_w=3)[0]])

    # ------------------------------------------------------------ THE c, round 132
    # DRAWN AGAINST POETICA for its shape -- owner 2026-09-16, *"poetica is my
    # preferred fallback"* -- because the c is one of the twelve lowercase
    # letters with NO scan crop at all (docs/albo-aldine-targets.md section 6),
    # and against FLANKER for its weight, which is the other half of the same
    # brief: flank 70 units, hairline 22-26.
    #
    # WHAT WAS WRONG, measured and not guessed:
    #   TOO TALL BY A TENTH OF AN X-HEIGHT. y -28..452 = 480 units, against
    #     Flanker's 438 and Poetica's 444. The semi-axis already carried the
    #     overshoot and then half a stroke was laid outside it at each end, so
    #     the letter grew by its own stroke. Everything downstream read as a
    #     narrow c, because w/h was being measured against that inflated h.
    #   THE BOTTOM ARC WAS A HAIRLINE. At mid-width Flanker's c is 62 units
    #     thick along the bottom and Poetica's 61; this one was 42, and its
    #     crown 32 where Flanker's is 26. It had the weight the wrong way up.
    #   IT WAS CARRYING THE FAMILY'S PEN. `pen_widths` is Albo's own nib, not
    #     the Aldine one; the c and the s were the last two letters in this
    #     module still drawn from it, and both leave it in this round. Its
    #     stress disagreed with the o standing next to it in every word.
    #
    # Measured after: IoU against Poetica 0.484 -> 0.643 and against Flanker
    # 0.512 -> 0.566; bbox 294 x 480 -> 241 x 443, against Poetica's 250 x 444.
    # The weight lands on Flanker almost exactly -- vertical median 71 units
    # against its 70, thickest 75 at 0.27 of the band against its 73 at 0.29,
    # and the .50 row 70 wide against its 70.
    #   NO TERMINALS. Both references end the top in a blunt BEAK -- Flanker 59
    #     units thick at 60 degrees where its crown is 24, Poetica 57 at 75
    #     against a 50 crown -- and the bottom in a fine taper (Flanker 27 at
    #     315 degrees, Poetica 19-22). This had one flat pen-cut at each end and
    #     the same width running into both.
    #
    # THE WIDTHS ARE KEYED BY ANGLE, the a's method, rather than left to a pen
    # model: the table below IS Flanker's perpendicular thickness round its own
    # c, measured with a distance transform (a ray from the centre measures a
    # RADIAL run and over-reads every place the stroke's normal is not radial),
    # converted from the geometric angle it was read at to the superellipse's
    # PARAMETRIC angle, which is what a point on the arc can be asked for.
    # NO `con()` re-spread: the c carries no contrast-arm ruling, and the table
    # is already the reference's own 74:24 -- whose hairline is the 22-26 the
    # brief names. Re-spreading it to the module's 9.26 would put the crown at
    # 8 units, which at 27 px is a broken letter.
    C_W = float(os.environ.get("ALBO_ALD_C_W", 0.675))      # outer width, x xh
    C_K = float(os.environ.get("ALBO_ALD_C_K", 1.88))      # squareness, as the o's
    C_A0 = float(os.environ.get("ALBO_ALD_C_A0", 50.0))    # the top terminal's end, parametric deg
    C_A1 = float(os.environ.get("ALBO_ALD_C_A1", 322.0))   # the bottom terminal's end
    C_WT = float(os.environ.get("ALBO_ALD_C_WT", 1.00))    # scales every key
    # THE TERMINALS ARE ROUNDED, and that is drawn rather than left to the
    # stroke's end face. Both references end this letter in a lobe: Poetica's
    # top terminal spans 59 units at its 0.75 column and is gone by 0.90, and
    # its bottom one tapers to a rounded point that has curled up to a quarter
    # of the x-height by the time it reaches the letter's right edge (row .25,
    # x 235-254). A `stroke` can only end in a flat or sheared face, and on a
    # 57-unit terminal that face reads as a cut corner.
    #
    # A STRAIGHT BEAK STROKE WAS TRIED FIRST AND IS NOT WHAT THIS IS. Butting a
    # second stroke onto the arc's end scored BETTER against Poetica (0.644
    # against 0.628) and looked worse: the two strokes meet at an angle, so the
    # underside gains a V-notch and the top a spike. It is the case the brief
    # names -- the number says a pass moved toward the reference and the
    # picture says what it did. A semicircular cap is the same lobe with no
    # join in it, and it costs nothing in width.
    C_CAP0 = float(os.environ.get("ALBO_ALD_C_CAP0", 1.00))   # top terminal, x half its width
    C_CAP1 = float(os.environ.get("ALBO_ALD_C_CAP1", 0.85))   # bottom terminal
    C_RING = [(40, 52), (47, 59), (66, 32), (90, 24), (113, 34), (133, 47),
              (160, 60), (171, 65), (180, 66), (189, 70), (200, 72), (212, 74),
              (227, 73), (246, 68), (270, 60), (293, 51), (313, 38), (328, 27)]
    if os.environ.get("ALBO_ALD_C_RING"):   # "40:52,47:59,..." -- for the fitter
        C_RING = [(float(a), float(w)) for a, w in
                  (kv.split(":") for kv in os.environ["ALBO_ALD_C_RING"].split(","))]

    def cs_round_end(pts, ws, at_start, amount):
        """Trim a stroke back and report the disc that caps it, so a ROUND
        terminal does not grow the letter.

        A disc simply dropped on the path's end is not a cap. At less than the
        stroke's half-width it sits inside the end face and shows as a bump; at
        exactly the half-width it is a true semicircular cap but it adds its
        whole radius to the letter's extent, which on the s -- whose terminals
        ARE its top-right and bottom-left corners -- grew the bounding box by a
        third and cost 0.27 of IoU. Trimming the path back by that radius first
        puts the finished ball's outer edge where the flat cut had it.

        THE RADIUS IS THE ORIGINAL END'S HALF-WIDTH, not the trimmed point's.
        Both references end these two strokes in a ball WIDER than the stroke
        running into it; measuring at the trimmed point instead made a letter
        that shrank -- the s lost a tenth of its width and 0.19 of IoU. Returns
        the new index and the cap's radius; `amount` 0 leaves the end alone and
        keeps the pen's flat cut. Serves the c and the s, the two letters here
        with free terminals."""
        n = len(pts) - 1
        if amount <= 0: return (0 if at_start else n), 0.0
        j = 0 if at_start else n
        r = ws[j] * 0.5
        k = j
        while 0 <= k <= n and math.hypot(pts[k][0] - pts[j][0], pts[k][1] - pts[j][1]) < r * amount:
            k += 1 if at_start else -1
        k = max(0, min(n, k))
        return k, r

    def c_key_widths(pts, cx, cy, rx, ry, keys, unit):
        """Widths for an OPEN arc, read off a table keyed by the parametric
        angle at each point. `keyed_ring` cannot serve here -- it builds a
        closed ring and returns a solid -- and an open arc has ends, which is
        the whole point of the c."""
        ks = sorted((a % 360.0, w) for a, w in keys)
        def wat(a):
            a %= 360.0
            for (a0, w0), (a1, w1) in zip(ks, ks[1:] + [(ks[0][0] + 360.0, ks[0][1])]):
                if a0 <= a <= a1 or (a1 > 360.0 and a < a1 - 360.0):
                    if a1 > 360.0 and a < a0: a += 360.0
                    t = (a - a0) / (a1 - a0) if a1 > a0 else 0.0
                    t = 0.5 - 0.5 * math.cos(math.pi * t)     # smooth, so no corner in the counter
                    return w0 + (w1 - w0) * t
            return ks[0][1]
        return [wat(math.degrees(math.atan2((y - cy) / ry, (x - cx) / rx))) * unit
                for x, y in pts]

    @glyph('c')
    def a_c(c):
        xh = c["xh"]; u = xh / 429.0      # the reference's own units
        def key(a):
            return c_key_widths([(math.cos(math.radians(a)), math.sin(math.radians(a)))],
                                0.0, 0.0, 1.0, 1.0, C_RING, u)[0] * C_WT
        wt, wb, wl = key(90), key(270), key(180)
        # THE OUTER EDGE lands on the overshoot, not the centerline -- and the
        # top and the bottom are inset by DIFFERENT amounts, because the crown
        # is 24 units and the bottom arc 60. Same outer band as the o
        # (-OVER/2 .. xh+OVER/2), so the two round letters sit on one line.
        y0, y1 = -OVER * 0.5 + wb / 2, xh + OVER * 0.5 - wt / 2
        cy = (y0 + y1) / 2; ry = (y1 - y0) / 2
        half = C_W * xh / 2
        cx = S * 0.6 + half; rx = half - wl / 2
        # CCW from the top terminal, over the crown, down the left, round the
        # bottom: a0 < a1 is the LONG way round, and the short way is the
        # aperture.
        p = superellipse(cx, cy, rx, ry, math.radians(C_A0), math.radians(C_A1), C_K)
        ws = c_key_widths(p, cx, cy, rx, ry, C_RING, u * C_WT)
        n = len(ws) - 1
        i0, r0 = cs_round_end(p, ws, True, C_CAP0)
        i1, r1 = cs_round_end(p, ws, False, C_CAP1)
        q, qw = p[i0:i1 + 1], ws[i0:i1 + 1]; m = len(q) - 1
        parts = [stroke(q, lambda t: qw[min(m, int(round(t * m)))],
                        cut0=None if r0 else CUT, cut1=None if r1 else CUT, raw=True)]
        if r0: parts.append(PR.dot(q[0][0], q[0][1], r0))
        if r1: parts.append(PR.dot(q[-1][0], q[-1][1], r1))
        return geom.ink(parts)

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
    # ------------------------------------------------------------ ROUND 132
    # THE BAR WAS HALF A STROKE TOO HIGH, and it is the same misreading twice:
    # the macro numbers above give the bar's TOP EDGE at 0.54 rising to 0.67
    # (that is what "the eye's floor" means), and both were written straight
    # into E_BAR / E_BAR_R, which are CENTERLINE fractions. With the bar 0.075
    # xh thick its centerline belongs at 0.50 rising to ~0.63. Drawn from the
    # top edge, the whole bar -- and the eye standing on it -- sat a half
    # stroke up. A blind coordinate descent against the scan crop asked for
    # 0.48 and 0.61 on its own, which is the measurement and the fit agreeing
    # from opposite directions; 0.50 is taken because it is the measured one
    # and it costs 0.002, and 0.61 because the rise it gives (0.11 of the band
    # against the 0.13 read off the top edge) is inside one printed row at 54
    # px and scores 0.028 better.
    #
    # THE REST OF THIS LETTER IS FITTED AGAINST THE SCAN CROP UNDER THE LEDGER
    # AS A HARD CONSTRAINT, which is the part not to drop. A free descent
    # reached IoU 0.719 by growing the eye to 0.71 -- and counter/ink with it,
    # to 0.264 against a target of 0.203. That is a FAILED ledger row wearing
    # a better number, and the eye it wanted is the one the macro block above
    # already rejected ("half again Griffo's"). Constrained, the same descent
    # reaches 0.720 legally: wider (0.65 -> 0.70), heavier (E_CTR 1.00 -> 1.14,
    # E_THICK 1.12 -> 1.24, toward Flanker's 69 median against this letter's
    # 53), a SMALLER eye (0.62 -> 0.54) and a bottom that stops earlier.
    # Measured after: scan IoU 0.563 -> 0.718, counter/ink 0.200 against 0.203,
    # w/h 0.65 against the crop's 0.65.
    E_W = float(os.environ.get("ALBO_ALD_E_W", 0.73))       # 38/58 measured
    # The bar's ends, off the macro: its TOP edge (the eye's floor) is at row
    # 371 where it leaves the left flank and row 364 at x620 -- 0.54 and 0.67
    # of the band. The eye itself is x608-622 by rows 353-369: 0.37 of the
    # letter's width and 0.28 of the x-height. The first cut had the bar's left
    # end at 0.40 and the upper loop's flanks at 0.18/0.92, which made an eye
    # 0.55 W wide -- half again Griffo's -- and THAT, not the stroke weight,
    # was the counterspace. The macro's stroke is 0.79 x the stem: a LIGHT
    # letter with a small eye, not a heavy one.
    E_BAR = float(os.environ.get("ALBO_ALD_E_BAR", 0.47))   # the bar's LEFT end, x xh
    E_BAR_R = float(os.environ.get("ALBO_ALD_E_BAR_R", 0.64))  # its RIGHT end -- the rise
    E_EYE = float(os.environ.get("ALBO_ALD_E_EYE", 0.49))   # scales the upper loop's flanks
    E_WT = float(os.environ.get("ALBO_ALD_E_WT", 1.00))
    E_CON = float(os.environ.get("ALBO_ALD_E_CON", 1.00))   # contrast, x the measured 3.4:1
    E_THICK = float(os.environ.get("ALBO_ALD_E_THICK", 1.24))  # x S, across the nib
    E_THIN = float(os.environ.get("ALBO_ALD_E_THIN", 0.26))    # x S, along it
    E_CTR = float(os.environ.get("ALBO_ALD_E_CTR", 1.08))   # >1 eats counterspace
    E_END = float(os.environ.get("ALBO_ALD_E_END", 0.80))   # where the terminal stops, x the width
    E_END_Y = float(os.environ.get("ALBO_ALD_E_END_Y", 0.24))  # and how high it has risen, x xh
    # CHECKED AND LEFT ALONE, round 132, and worth saying so rather than
    # leaving the next pass to re-derive it. The mid-width column says the eye
    # sits high -- the scan's spans y 0.59-0.83 of the band and this letter's
    # 0.66-0.87 -- so the crown's apex and the eye's right shoulder were made
    # dials and swept. BOTH ARE ALREADY AT THEIR BEST: lowering the crown to
    # 0.93 costs 0.018 of IoU and 0.90 costs 0.043, and the shoulder falls off
    # in both directions from 0.82. The reason is that the crown's outer edge
    # is also the letter's TOP, so shortening it rescales the whole letter
    # against a height-normalized reference and moves everything else with it.
    # The eye's height is not reachable from here; it would need the loop's
    # floor, which is the bar. They stay as dials because the sweep was worth
    # having and will be worth having again.
    E_TOP = float(os.environ.get("ALBO_ALD_E_TOP", 0.96))      # the crown's apex, x xh
    E_SHOULDER = float(os.environ.get("ALBO_ALD_E_SHOULDER", 0.82))  # the eye's right shoulder, x xh
    # ---------------------------------------------------------------- ROUND 135
    # THE LETTER IS DRAWN IN A BAND, NOT FROM THE BASELINE. Owner 2026-09-16:
    # *"bring e up above baseline."* Measured on the shipped font at a 400 px
    # x-height, ink bottoms: **e -0.0925 xh** against the o's -0.0125, the c's
    # -0.0150 and the n's -0.0175 -- the e hung seven times the round letters'
    # overshoot below the line, and it was 1.10 xh of ink tall where the o is
    # 1.008 and all three references' e's are 1.02-1.03 (Flanker -8 units,
    # Poetica -14, Cancelleresca -13, every one of them topping at exactly
    # 429). So the e was not sitting low, it was OVERSIZE, and translating it
    # up would only move the fault to the crown -- 1.086 xh, a tenth of the
    # band proud of the o on the same line.
    #
    # `f` is remapped into E_FLOOR..1.0 instead of 0..1.0. The bottom arc's
    # centerline stands at E_FLOOR and its underside -- 40 units of half-width
    # -- lands on the o's own overshoot; the crown is pinned, so nothing above
    # the bar moves more than a thousandth of the band. The unshear reads the
    # SAME remapped height, or the page's 13 degrees would be taken out at the
    # wrong altitude, and `dirs` scales its dy by the band, or the nib would be
    # asked for the width of a direction the stroke no longer travels in.
    #
    # MEASURED AFTER: ink bottom **-0.015 xh**, the c's own and within 0.003 of
    # the o's, from -0.093; ink height 1.023 xh against the references' 1.02 to
    # 1.03; IoU against the scan crop 0.663 -> 0.698 and against Poetica 0.510
    # -> 0.553. IT COSTS COUNTER: the ledger row goes 0.194 -> 0.187 against a
    # target of 0.203, so -4% becomes -8% inside a 10% gate. That is the
    # compression, not a defect -- the eye's height is 7.8% of the band shorter
    # because the letter is. E_EYE 0.49 -> 0.53 buys it all back (0.195) and is
    # deliberately NOT taken: the ask was the baseline and the terminal, and
    # E_EYE is a fitted shape dial. Whoever needs the margin knows where it is.
    E_FLOOR = float(os.environ.get("ALBO_ALD_E_FLOOR", 0.078))   # the f=0 line, x xh
    # THE LOWER TERMINAL IS BLUNT, NOT ANGULAR (the same ruling's second half).
    # It ended in a 20-degree pen shear (`cut1=CUT`) laid across a stroke the
    # nib was giving its THINNEST width -- the terminal runs at 49.6 degrees
    # and the nib's own angle is 50, so `nib()` returned 0.27 x S there, the
    # hair, and a sheared face on a hairline is a spike. Measured, the topmost
    # row of each e's terminal: Albo 6 units, Poetica 17, Cancelleresca 23,
    # Flanker 33. It was the finest of the four by a factor of three.
    # Two changes: the end face is SQUARE rather than sheared (`cut1=None`),
    # and the width is floored at E_END_W over the last E_END_T0 of the path so
    # the face has something to be -- Poetica's 17 units is 0.25 x S, Flanker's
    # 33 is 0.49, and 0.40 sits between them. Measured after, the terminal's
    # top four rows: **15 / 26 / 37 / 43** units against Poetica's 17 / 26 / 32
    # / 41 and the 6 / 14 / 23 / 32 this letter shipped with.
    #
    # A `PR.dot` CAP, the c's own round end, WAS TRIED AND IS NOT THIS. It
    # rendered as a bead hung off a neck: `_unfold` drops the folded inner
    # offset where a widening stroke turns, so the drawn ink stops ~12 units
    # short of the path's last point, and a disc placed AT that point stands
    # clear of it. `cs_round_end` exists for exactly that trap but wants a
    # raw per-point width array, which this letter does not have -- it is
    # drawn `pieces=True` because its centerline crosses itself. A square face
    # on a 26-unit stroke is blunt, which is what was asked for.
    E_END_W = float(os.environ.get("ALBO_ALD_E_END_W", 0.40))    # the terminal's width, x S
    E_END_T0 = float(os.environ.get("ALBO_ALD_E_END_T0", 0.82))  # where the blunting starts, x the path

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
        band = 1.0 - E_FLOOR                     # round 135: the e's own band
        YF = lambda f: E_FLOOR + f * band        # a y fraction -> its real height
        X = lambda f, fy: S * 0.55 + f * W - unshear * YF(fy)
        Y = lambda f: YF(f) * xh
        mid = 0.50
        E = lambda f: mid + (f - mid) * E_EYE   # the eye's flanks, about its center
        # ROUND 133, against the macro's "naues" (owner: "match a and e to
        # scans better. take multiple passes"). Two things the printed e does
        # that this path did not, both obvious once the scan and the render
        # are cropped to one height and set side by side:
        #   THE LOWER BOWL CLOSES. Its terminal comes round the bottom and
        #     rises to about 0.80 of the width at a quarter of the x-height,
        #     so the aperture is a narrow slot. Stopping at 0.54 and 0.12 left
        #     the stroke under the bar's middle, and the letter read as a c
        #     with a bar laid across it.
        #   THE BOTTOM IS FLAT AND WIDE, running from 0.26 to 0.52 of the
        #     width before it turns up, where this path turned at 0.34.
        P = [(0.00, E_BAR),  (E(0.78), E_BAR_R),  # the bar, rising ~30 degrees
             (E(0.86), E_SHOULDER), (E(0.54), E_TOP),   # up the eye's right, over the crown
             (E(0.20), 0.87), (0.08, 0.68),      # down the left
             (0.00, 0.38),   (0.06, 0.16),       # past its own start
             (0.26, 0.01),   (0.52, 0.00),       # the flat wide bottom
             (E_END, E_END_Y)]                   # and up into the aperture
        # ROUND 135 -- THE MOVEMENT IS DRAWN FROM THE TERMINAL BACK TO THE BAR,
        # and that one line is what makes the terminal blunt at all.
        #
        # WHY: `_unfold` DROPS the folded points of an offset, and this
        # letter's inner offset folds twice -- measured, the eye's right
        # shoulder has a curvature radius of 30 units under a 76-unit stroke
        # and the crown's left 22 under 47, so (w/2)/R is 1.29 and 1.21 where
        # 1.0 is the fold. Five of the 96 samples on the LEFT side are dropped,
        # which leaves L five samples AHEAD of R for the whole rest of the
        # path; `pieces=True` unions overlapping quads so the body heals
        # itself, but the LAST quad has no successor to cover it and closes as
        # a WEDGE. That wedge is the angular point the owner reported -- it is
        # not the pen cut (it survived `cut1=None`) and it is not the width
        # (it survived the E_END_W floor).
        #
        # Reversed, the geometry is identical -- `nib()` reads |sin(d - 50)|,
        # so a direction and its opposite give the same width, and a catmull
        # through reversed points is the same curve -- but the unhealed end is
        # now the BAR'S LEFT END, which is buried under the descending left
        # flank where the loop closes on itself. The terminal becomes sample 0,
        # where L and R cannot be out of step. The cuts and the blunt floor
        # swap ends to follow.
        P = P[::-1]
        p = catmull([(X(fx, fy), Y(fy)) for fx, fy in P], tension=0.5)
        # Measured off the macro: thick 0.79 x the stem, the bar 0.23 -- 3.4:1.
        # The width at each point comes from the NIB and the direction the
        # stroke is travelling there, not from a hand-tuned list.
        dirs = []
        for i in range(len(P)):
            a_ = P[max(0, i - 1)]; b_ = P[min(len(P) - 1, i + 1)]
            dirs.append(math.degrees(math.atan2((b_[1] - a_[1]) * band * xh,
                                                (b_[0] - a_[0]) * W)))
        base = con([nib(d, E_THICK, E_THIN) for d in dirs], CON_E)
        mean = sum(base) / len(base)
        ws = [S * (mean + (w - mean) * E_CON) * E_WT * E_CTR for w in base]
        # THE BLUNT LOWER TERMINAL, round 135 -- see the dial block. The width
        # is raised to E_END_W over the last stretch on a cosine, so there is
        # no step in the counter's edge where the floor takes over.
        m = len(ws) - 1
        run = 1.0 - E_END_T0                 # the terminal is the path's START now
        for i in range(m + 1):
            t = i / m
            if t < run:
                k = 0.5 - 0.5 * math.cos(math.pi * (1.0 - t / run))
                ws[i] += (S * E_END_W - ws[i]) * k
        wf = widths([(i / m, w) for i, w in enumerate(ws)])
        # pieces=True: the centerline CROSSES ITSELF where the loop closes on
        # the bar. As one polygon that crossing becomes a HOLE -- the outline
        # self-intersects and the fill cancels -- which was the bite in the
        # letter's left side.
        return geom.ink([stroke(p, wf, cut0=None, cut1=CUT, pieces=True)])

    # ------------------------------------------------------------ THE a, round 132
    # DRAWN AGAINST THE REFERENCE, NOT TUNED. Owner 2026-09-15: "examine a
    # then each subsequent letter, take multiple passes at each until the
    # shape and strokes and serifs match what they should based on a
    # referenced vector or bitmap." The reference is Flanker Griffo Italic
    # (refs/, his 2026-09-15 upload; the closest digital face to the 1501
    # scans) measured UNSHEARED in Albo's design units by aldine_targets.py --
    # docs/albo-aldine-targets.md, section 1 -- and the owner's scan crop of
    # the a, which agrees on every point below. Every earlier a-dial (rise,
    # head, bow, teardrop counter, arm dive) is retired by this: they were
    # tuning a construction the reference does not have.
    #
    # WHAT THE NUMBERS SAY (x from the letter's left ink edge, xh = 429):
    #   the letter is SQUARE: 437 x 438, the bowl filling the x-height (-9..429)
    #   the stem is 70 wide (0.83 S) at x 282-352, straight, top at ~0.95 xh
    #   the bowl is a RING: left extreme x=0 at ~0.45 xh, top at x~205, bottom
    #     at x~140 -- an egg skewed right; it merges into the stem at the top
    #     and rises into it at ~0.25 xh (a 14-unit gap at .25, merged by .50)
    #   the ring's width by position: left flank 70, lower-left 78, bottom 58,
    #     the rise into the stem 34, top 28, upper-left 52
    #   the tail: underside ON the baseline from x 300 to 385, tip at (436, 0.15)
    # Everything is written as a fraction of xh or S, so it rides the axes.
    A_UNIT = 429.0
    A_STEM_X = float(os.environ.get("ALBO_ALD_A_STEM_X", 302))   # stem center, units
    A_STEM_W = float(os.environ.get("ALBO_ALD_A_STEMW", 77))     # units
    A_STEM_TOP = float(os.environ.get("ALBO_ALD_A_TOP", 0.97))     # x xh
    A_RX = float(os.environ.get("ALBO_ALD_A_RX", 155.0))            # bowl outer half-width, units
    A_CY = float(os.environ.get("ALBO_ALD_A_CY", 215.0))            # bowl center height, units
    A_SKEW = float(os.environ.get("ALBO_ALD_A_SKEW", 0.06))         # the egg's lean, dx per dy
    A_K = float(os.environ.get("ALBO_ALD_A_K", 1.90))               # squareness
    A_TAIL_X = float(os.environ.get("ALBO_ALD_A_TAIL_X", 424))    # tip, units from the left edge
    A_TAIL_Y = float(os.environ.get("ALBO_ALD_A_TAIL_Y", 0.15))     # x xh
    # (the old right-reaching nib mark's dial lived here and was shadowed by
    # the A_HEAD_R below from round 137 on -- the same name twice, the second
    # winning silently. Removed; the head reaches LEFT and its dial is there.)
    # THE a IS A d WITH A SHORT ASCENDER (owner 2026-09-16, from the scan).
    # The Petrarch page and the owner's crop both carry the a's stem past the
    # x-line and finish it with the SAME head the b d p wear -- the wedge
    # reaching left -- not the little right-hand nib mark the first cut gave
    # it. A_ASC is how far above the x-line that stem goes, in units; the d's
    # own ascender clears the x-line by 341, so this is a short one.
    # 8, not 96 (owner 2026-09-16, after seeing 96 on the page): the stem
    # clears the x-line by a hair -- enough that the a is the same gesture as
    # the d and not enough to read as an ascender. The 150 that made the a and
    # the d one letter, and the 96 this replaces, are both in the round 133 log.
    # ROUND 137: THE OWNER DREW THIS ONE. He set the a in the editor
    # (https://claude.ai/artifact/81j24wds45Lfp31aCPatDB) and pasted its state
    # back, which is a different letter from the one round 135 shipped: the
    # stem's top stops 54 units BELOW the x-line and a long head -- 210 units
    # of reach against the b's 58 -- sweeps left across it and becomes the
    # letter's top. So the a's arch is the HEAD, not the bowl's crown, and the
    # bowl hangs under it. The a carries its own head dials for that reason;
    # the b d p head stays where he put it two rounds ago ("reduce visual
    # weight of top serif on b and d").
    A_ASC = float(os.environ.get("ALBO_ALD_A_ASC", -27))             # units, NEGATIVE = below the x-line
    A_HEAD_R = float(os.environ.get("ALBO_ALD_A_HEAD_R", 220))       # the head's reach left
    A_HEAD_D = float(os.environ.get("ALBO_ALD_A_HEAD_D", 109))       # its tip below the stem's top
    A_TAIL_W1 = float(os.environ.get("ALBO_ALD_A_TAIL_W1", 21.0))  # the tail's tip width, units
    A_HEAD_F = float(os.environ.get("ALBO_ALD_A_HEAD_F", 120))       # where its underside rejoins the stem
    # THE COUNTER IS DRAWN, NOT OFFSET, AND ITS SHAPE IS THE SCAN'S.
    # Owner 2026-09-16: "a needs a smaller counterspace that is rounded
    # teardrop and 24 units above", then "match the counterspace for a to the
    # griffo scans".
    #
    # Until round 133 the counter was whatever `ring_from` left after
    # offsetting the bowl's outer edge inward by eight width keys, so it could
    # not be asked for a shape at all. The bowl is a filled superellipse now
    # and the counter is its own closed curve, subtracted.
    #
    # MEASURED, on two a's that agree: the macro's "ad" (griffo-macro.png,
    # 54 px x-height) and the owner's own crop, both binarized with Otsu on an
    # 8x upscale and flooded from the border, so the counter is whatever white
    # survives inside the ink (tools/wedge_serif, the round 133 log):
    #
    #                        macro "ad"    owner crop      the d, for scale
    #   counter / ink            0.42          0.32              0.25
    #   counter w/h              0.84          0.83              0.60
    #   counter h / ink h        0.51          0.47              0.35
    #   widest at                0.45          0.45              0.45
    #   area / (w x h)           0.60          0.59              0.70
    #
    # An ellipse fills 0.79 of its box and a triangle 0.50, so at 0.60 this is
    # neither: it is narrow at BOTH ends -- 0.15 of its width at the floor,
    # 0.25 at the tip -- and widest across the middle. And it LEANS: its left
    # edge starts 0.20 in at the floor, reaches the far left at 0.35 of the
    # height, and has walked to 0.71 by the tip. That lean is the letter's own
    # stress seen from the inside, and it is what a symmetric teardrop (the
    # first cut of this) could not show.
    # ROUND 139: FEWER POINTS (owner: "simplify a to much fewer polygons").
    # The a carried 217 outline points against the n's 116 and the o's 190 --
    # the counter's twelve rows were interpolated six ways each, then
    # catmulled, smoothed four times and resampled twice at the module's
    # default spacing, and the bowl was offset from that dense curve. The
    # The curve is built FINE (eight points per row gap, five smoothing
    # passes) and thinned ONCE at the end -- smoothing a coarse polygon
    # corner-cuts it, which is a different and worse letter.
    #
    # THE TRADE IS REAL AND IT IS MEASURED. 217 points -> 167 at spacing 16,
    # in family with the o's 190 and the b's 201 where it used to be the
    # densest glyph in the font. Below that the outline FACETS at display
    # size: at 420 px the ladder reads smooth at 217, visibly flat-sided at
    # 137 (spacing 22) and a polygon at 115 (spacing 30). At reading size
    # none of it is visible. 16 is the rung that keeps the curve.
    A_CTR_FINE = int(os.environ.get("ALBO_ALD_A_FINE", 8))
    A_SPACING = float(os.environ.get("ALBO_ALD_A_SPACING", 16.0))
    A_CTR_BOT = float(os.environ.get("ALBO_ALD_A_CTR_BOT", 22.0))   # the counter's floor, units above the baseline
    # ROUND 142 -- FITTED TO THE REST OF THE LOWERCASE (owner: "reshape and
    # resize a to fit the rest of the lowercase letters and make a legible
    # word image"). Measured against its own alphabet, the a was the outlier
    # three ways: 468 units of ink where the n is 392 and the o 336, its top
    # +26 over the x-line where n o e sit at +4 +7 +13, and a mean ink width
    # of 66 against 46-57 for everything else -- a fifth heavier than the
    # heaviest of its neighbours.
    #
    # THE TARGETS ARE THE REFERENCES' OWN RATIOS, not a taste: all three make
    # the a 0.82-0.92 of the n's ink (mean 0.88 -> 345 here), and all three
    # put its top EXACTLY on the x-line -- +0.000 xh, because an a's top is a
    # flat head and takes no overshoot where a round letter does. Solved by
    # coordinate descent over the eight dials that move width, height and
    # weight: 386 wide (0.98 of the n), +1 over the line, mean ink 54.1
    # against the lowercase's 46-57, counter fill 0.65 -- his shape.
    #
    # ROUND 139: TALL ENOUGH TO OVERLAP THE X-LINE (owner 2026-09-16: "it
    # needs to be tall enough to slightly overlap x height. keep lean and
    # counter shape and lack of fractures ... the same"). His a topped at 376
    # -- 53 units BELOW the x-line, where every other lowercase reaches +4 to
    # +16 above it (n +4, o +7, c +8, x +10, e and s +13, u +16). It was the
    # one short letter in the line.
    # The counter and its bowl are scaled UNIFORMLY (278 -> 339, and the width
    # follows through A_CTR_WH), not stretched: a uniform scale is a similar
    # figure, so the counter's shape is untouched -- measured, its fill is
    # 0.65 against his 0.66, where stretching the height alone reads 0.63. The
    # head rides up with it (A_ASC -54 -> +7) so the two still meet, and the
    # bowl's weight comes back to 0.86 because a bigger bowl at the same
    # stroke reads lighter: a/n 0.89 at 0.70, 1.01 at 0.86.
    A_CTR_H = float(os.environ.get("ALBO_ALD_A_CTR_H", 332))      # its height, units -- 0.51 x the ink, as the macro
    A_CTR_WH = float(os.environ.get("ALBO_ALD_A_CTR_WH", 0.84))     # its width over its height, as both scans
    A_CTR_X = float(os.environ.get("ALBO_ALD_A_CTR_X", 77))       # its left extreme, units from the letter's left
    # height fraction (0 = floor) -> (left edge, right edge), both x the
    # counter's width. The mean of the two a's, which differ by under 0.03
    # everywhere except the floor.
    A_CTR_PROFILE = [
        (0.117, 0.357, 0.472), (0.143, 0.247, 0.579), (0.187, 0.140, 0.683),
        (0.257, 0.064, 0.778), (0.370, 0.019, 0.870), (0.453, 0.024, 0.917),
        (0.533, 0.040, 0.966), (0.661, 0.103, 0.995), (0.762, 0.178, 1.006),
        (0.865, 0.313, 1.010), (0.958, 0.530, 0.936), (0.995, 0.736, 0.870),
    ]
    # ring widths keyed by angle (degrees ccw from the right), in units
    A_RING = [(0, 26), (45, 22), (90, 20), (135, 40), (180, 66), (225, 74), (270, 54), (315, 38)]
    if os.environ.get("ALBO_ALD_A_RING"):   # "0:34,45:30,..." -- for the fitter
        A_RING = [(float(a), float(w)) for a, w in
                  (kv.split(":") for kv in os.environ["ALBO_ALD_A_RING"].split(","))]

    def keyed_ring(cx, cy, rx, ry, keys, k=None, skew=0.0, unit=1.0, smooth_w=4):
        """A bowl whose OUTER is the designed superellipse (optionally skewed
        into an egg) and whose stroke width is read off a table keyed by the
        angle round the ring -- the width the reference shows at each side,
        not a pen model's guess. `keys` are (degrees, units); interpolation
        is periodic and smooth."""
        k = BOWL_K if k is None else k
        outer = superellipse(cx, cy, rx, ry, 0.0, 2 * math.pi, k)[:-1]
        if skew:
            outer = [(x + (y - cy) * skew, y) for x, y in outer]
        # replicate ring_from's resampling so the widths line up with its points
        pts = geom.resample(outer + [outer[0]])[:-1]; n = len(pts)
        ks = sorted((math.radians(d) % (2 * math.pi), w) for d, w in keys)
        def wat(ang):
            ang %= 2 * math.pi
            for (a0, w0), (a1, w1) in zip(ks, ks[1:] + [(ks[0][0] + 2 * math.pi, ks[0][1])]):
                if a0 <= ang <= a1 or (a1 > 2 * math.pi and ang < a1 - 2 * math.pi):
                    if a1 > 2 * math.pi and ang < a0: ang += 2 * math.pi
                    u = (ang - a0) / (a1 - a0) if a1 > a0 else 0.0
                    u = 0.5 - 0.5 * math.cos(math.pi * u)
                    return w0 + (w1 - w0) * u
            return ks[0][1]
        ws = []
        for x, y in pts:
            ang = math.atan2((y - cy) / ry, (x - (y - cy) * skew - cx) / rx)
            ws.append(wat(ang) * unit)
        return PR.ring_from(outer, widths_fn=lambda t: ws[min(n - 1, int(round(t * n))) % n],
                            smooth_w=smooth_w)[0]

    # ---------------------------------------------------------------- nib_ring
    # OWNER 2026-09-16: *"O and Q need match the line contrast and axis tilt of
    # G"*. The G's arc is the only one of the three round capitals drawn ON THE
    # PEN -- `nib_widths(p_, CS*CAP_W_ROUND, x0.30, CAP_CON)` -- and the other
    # two were each on something else, which is exactly what the instruction
    # says you can see:
    #
    #             axis (thick at)   axis (thin at)   contrast   drawn on
    #   G           50 / 230 deg     140 / 320        2.20:1     the 50-deg nib
    #   O (was)    180 / 195         105 / 285        2.25:1     Pagella's keyed table
    #   Q (was)     15 /  30          90 / 270        1.43:1     bowl_th, the family profile
    #
    # -- measured on the built font, unsheared, as radial ink at 15-degree
    # steps about each ring's own centre. So the O's stress axis sat about 40
    # degrees off the G's and the Q's about 35 the other way, and the Q was
    # barely modulated at all beside either. One pen for all three is the fix.
    #
    # The width goes as |sin(direction - 50)| round the closed contour, so a
    # ring's thick lands where its TANGENT runs at 50 degrees -- geometric 50
    # and 230 on a ccw superellipse -- and `con()` then re-spreads the whole
    # sequence to CAP_CON exactly as the G's does. `nib_widths_closed` is used
    # rather than `nib_widths` because a ring has no ends: the open version
    # clamps its neighbour lookup at the first and last sample and leaves a
    # seam in the width where the contour closes.
    def _hand_at(keys, ang, idx):
        """One column of a HAND table, interpolated periodically and smoothly
        round the ring. `keys` are (degrees, dr, dw) in units; `idx` 1 picks
        the radial column and 2 the width's."""
        if not keys:
            return 0.0
        ks = sorted((math.radians(d) % (2 * math.pi), row[idx - 1])
                    for d, *row in keys)
        ang %= 2 * math.pi
        for (a0, v0), (a1, v1) in zip(ks, ks[1:] + [(ks[0][0] + 2 * math.pi, ks[0][1])]):
            if a0 <= ang <= a1:
                u = (ang - a0) / (a1 - a0) if a1 > a0 else 0.0
                return v0 + (v1 - v0) * (0.5 - 0.5 * math.cos(math.pi * u))
        a0, v0 = ks[-1]; a1, v1 = ks[0][0] + 2 * math.pi, ks[0][1]
        if ang < ks[0][0]: ang += 2 * math.pi
        u = (ang - a0) / (a1 - a0) if a1 > a0 else 0.0
        return v0 + (v1 - v0) * (0.5 - 0.5 * math.cos(math.pi * u))

    def nib_ring(cx, cy, rx, ry, k=None, unit=1.0, smooth_w=2, floor=0.0,
                 thick=None, thin_f=0.30, target=None, phi=50.0, hand=None):
        """A closed bowl carrying the G's own pen. Returns (solid, outer, inner).

        `hand` is an optional HAND-CUT table: (degrees, dr, dw) in design
        units, interpolated smoothly round the ring, `dr` pushing the OUTER
        contour out or in and `dw` thickening or thinning the stroke there. It
        is a table and not a random jitter on purpose -- `life()` re-rolls per
        build and a defect that moves is not a cut, it is noise."""
        k = BOWL_K if k is None else k
        thick = CS * CAP_W_ROUND if thick is None else thick
        target = CAP_CON if target is None else target
        outer = superellipse(cx, cy, rx, ry, 0.0, 2 * math.pi, k)[:-1]
        if hand:
            warped = []
            for x, y in outer:
                ang = math.atan2((y - cy) / ry, (x - cx) / rx)
                dr = _hand_at(hand, ang, 1)
                nx, ny = (x - cx), (y - cy)
                L = math.hypot(nx, ny) or 1.0
                warped.append((x + nx / L * dr, y + ny / L * dr))
            outer = geom.smooth(warped, 2, closed=True)
        # replicate ring_from's resampling so the widths line up with its points
        pts = geom.resample(outer + [outer[0]])[:-1]; n = len(pts)
        ws = nib_widths_closed(pts, thick, thick * thin_f, target, phi)
        out = []
        for (x, y), w in zip(pts, ws):
            v = w * unit
            if hand:
                v += _hand_at(hand, math.atan2((y - cy) / ry, (x - cx) / rx), 2)
            out.append(max(v, floor))
        ws = out
        return PR.ring_from(outer, widths_fn=lambda t: ws[min(n - 1, int(round(t * n))) % n],
                            smooth_w=smooth_w)

    # The bowl's width round the counter, keyed by angle (degrees ccw from
    # the right, 180 = the left flank), in units. Flanker's a, measured
    # unsheared (docs/albo-aldine-targets.md): the left flank 68-73, the
    # lower left 80, the bottom 58, the rise into the stem 34, the top 28.
    # Scaled 1.12 from Flanker's numbers after the first build measured the
    # counter at 0.49 of the ink against the scan's 0.42: the print is heavier
    # than the revival, and the scan is the target.
    # 0.70 -- ROUND 137'S IMPROVING PASS, and it moves his drawing's WEIGHT
    # and not its shape. Measured against the n, the way the o was in round
    # 134: his a's mean ink width was 1.22 of the n's where Flanker's a is
    # 0.98 of its own n, so the a was 24% heavier than everything beside it
    # and read as the dark blob in every word it appears in. His long head
    # adds ink at the top that the old bowl's weight was never carrying. At
    # 0.70 the ratio is 1.00 and the counter opens from 0.48 to 0.57 -- the
    # shape, the counter's profile and the head are all exactly as he drew
    # them.
    A_FLANK_S = float(os.environ.get("ALBO_ALD_A_FLANK_S", 0.66))   # scales every bowl width
    A_FLANK = [(0, 38), (45, 29), (90, 33), (135, 54), (180, 78), (225, 90), (270, 65), (315, 40)]

    def _a_flank(deg):
        """Periodic cosine interpolation of A_FLANK."""
        ks = sorted((d % 360, w) for d, w in A_FLANK); deg %= 360
        for (a0, w0), (a1, w1) in zip(ks, ks[1:] + [(ks[0][0] + 360, ks[0][1])]):
            if a0 <= deg <= a1 or (a1 > 360 and deg < a1 - 360):
                if a1 > 360 and deg < a0: deg += 360
                t = (deg - a0) / (a1 - a0) if a1 > a0 else 0.0
                t = 0.5 - 0.5 * math.cos(math.pi * t)
                return w0 + (w1 - w0) * t
        return ks[0][1]

    def a_counter(u, x0):
        """The a's counter, drawn from the SCAN'S OWN PROFILE.

        `A_CTR_PROFILE` is a measured table of left and right edges by height,
        so the curve is the scan's silhouette rather than an idea of a
        teardrop: narrow at the floor, widest across the middle, narrowing to
        a small tip, and leaning right the whole way up. Closed with a catmull
        so the corners the sampling leaves become curves again."""
        bot = A_CTR_BOT * u; h = A_CTR_H * u; w = A_CTR_H * A_CTR_WH * u
        x = x0 + A_CTR_X * u
        # The table is twelve rows; a catmull through twelve points at this
        # size leaves visible facets on the counter's left flank, where the
        # curve is flattest. Interpolate it to three points per gap first --
        # the measurement cannot see a facet and the eye finds it immediately.
        rows = []
        for (f0, l0, r0), (f1, l1, r1) in zip(A_CTR_PROFILE, A_CTR_PROFILE[1:]):
            for i in range(A_CTR_FINE):
                t = i / float(A_CTR_FINE)
                rows.append((f0 + (f1 - f0) * t, l0 + (l1 - l0) * t, r0 + (r1 - r0) * t))
        rows.append(A_CTR_PROFILE[-1])
        left = [(x + l * w, bot + f * h) for f, l, r in rows]
        right = [(x + r * w, bot + f * h) for f, l, r in rows]
        pts = catmull(left + right[::-1], tension=0.5, closed=True)
        pts = geom.smooth(pts, 5, closed=True)
        return geom.poly(geom.resample(pts + [pts[0]], A_SPACING)[:-1])

    # ------------------------------------------------------------ THE a's SILHOUETTE, TRACED
    # Owner 2026-09-16: "make a brand new a tracing the scans and using the
    # counter of the existing a." So the letter's OUTSIDE is the 1501 page's
    # and its INSIDE is his.
    #
    # Traced off griffo-macro.png, the a of "ad" (crop 263,42..308,112 at a
    # 54 px x-height), binarized with Otsu on an 8x upscale, largest ink blob
    # only, then the LEFT edge read at 41 heights and converted to design
    # units. The left edge is the half of that print that is clean: the a's
    # right side touches the d, which is why round 132's crop measured the
    # pair and why this traces one edge rather than a silhouette.
    #
    # height above the ink's bottom (units)  ->  left edge (units)
    #     0 214 | 49 0 | 99 0 | 148 0 | 198 0 | 247 35 | 297 52
    #   346 139 | 396 210 | 445 258 | 495 309
    # The whole ink is 495 units tall = 1.15 xh: the bowl's left extreme is a
    # FLAT RUN from 0.10 to 0.40 of that height -- the pen's own side, not a
    # curve -- and above it the silhouette walks right at a near-constant
    # rate into the head.
    A_TRACE = [(0.000, 214), (0.099, 0), (0.200, 0), (0.299, 0), (0.400, 0),
               (0.499, 35), (0.600, 52), (0.699, 139), (0.800, 210),
               (0.899, 258), (1.000, 309)]
    A_TRACE_H = float(os.environ.get("ALBO_ALD_A_TRACE_H", 495.0))   # the traced ink's height, units
    A_TRACE_BOT = float(os.environ.get("ALBO_ALD_A_TRACE_BOT", -24.0))  # where it sits, units off the baseline
    # SHIPPED AT 0, AND THE REASON IS THE FINDING. Driving the left flank
    # onto this trace puts a SPUR on the bowl's lower left, at every band and
    # every clamp tried, because the two halves of the instruction fight:
    # the scan's left edge runs dead straight from 0.10 to 0.40 of the ink's
    # height, while the owner's counter is an egg whose lower left curves
    # away from it -- so the width between them swells to 2-3x the flank as
    # the counter turns. A page's a and his counter are not the same letter's
    # inside and outside. The trace is kept because it is measured and
    # correct; `ALBO_ALD_A_TRACE_S=1` renders it.
    A_TRACE_S = float(os.environ.get("ALBO_ALD_A_TRACE_S", 0.0))     # 1 = drive the left flank from the scan

    def a_traced_left(u, x0):
        """The scan's left edge as a list of (x, y) in design units."""
        h = A_TRACE_H * A_TRACE_S * u; bot = A_TRACE_BOT * u
        return [(x0 + lx * A_TRACE_S * u, bot + f * h) for f, lx in A_TRACE]

    # ------------------------------------------------------------ THE a, round 147
    # TRACED. Owner 2026-09-16: "forget about the tear drop counter. just
    # match the shape of the letter 'a' from the scans." So both contours are
    # the page's -- outer AND counter -- and no part of this letter is a
    # construction any more.
    #
    # Off griffo-macro.png, the a of "ad" (crop 263,42..302,112 at a 54 px
    # x-height), upscaled 10x, Otsu, largest ink blob, and the d cut away at
    # 0.78 of the crop's width -- the two letters touch in this print, which
    # is what defeated every earlier attempt to measure this a. The outer and
    # the counter are then walked with a Moore-neighbour boundary trace,
    # converted to design units at xh = 429, and UNSHEARED by 13 degrees,
    # because build.draw() shears the finished ink and a traced italic is
    # already sheared -- tracing without that step doubles the slant.
    #
    # 65 outer points and 42 counter points, resampled off 1751 and 780.
    A_TRACE_OUTER = [
        (144.1, 418.7), (149, 397.2), (154, 375.8), (158.9, 354.3),
        (163.9, 332.9), (168.8, 311.4), (173.8, 290), (178.7, 268.5),
        (183.7, 247.1), (188.6, 225.6), (193.6, 204.2), (198.5, 182.7),
        (203.5, 161.3), (208.4, 139.8), (213.4, 118.4), (218.3, 96.9),
        (223.3, 75.5), (228.2, 54), (233.2, 32.6), (238.1, 11.1),
        (224.1, 3.2), (202.3, 4.8), (179.8, 12.7), (163.7, 34.2),
        (159.6, 55.6), (156.2, 77.1), (157.6, 98.5), (144.3, 118.4),
        (130.5, 102.5), (123.9, 82.6), (130.8, 66.7), (151.2, 46.9),
        (143, 31), (122.9, 49.3), (110.1, 66.7), (92.2, 51.6),
        (73.8, 38.1), (55.9, 26.2), (35.6, 21.4), (15.8, 17.5),
        (-4, 17.5), (-9, 38.9), (-13.9, 60.4), (-18.9, 81.8),
        (-23.8, 103.3), (-28.8, 124.7), (-33.7, 146.2), (-38.7, 167.6),
        (-43.7, 189.1), (-48.6, 210.5), (-39.7, 227.2), (-27.1, 244.7),
        (-17.8, 263), (-10.8, 277.3), (-15.7, 298.7), (6.6, 294.7),
        (23.4, 311.4), (37.9, 328.1), (56.1, 335.3), (63.4, 355.1),
        (83.4, 361.5), (98.8, 377.4), (118.8, 383.7), (124.4, 400.4),
        (145.5, 402),
    ]
    A_TRACE_COUNTER = [
        (91.1, 307.4), (107.5, 301.9), (122.7, 301.1), (139.4, 287.6),
        (142.1, 272.5), (140, 257.4), (130.1, 248.7), (135.2, 233.6),
        (148, 219.3), (143.6, 207.4), (146.3, 192.3), (135.6, 183.5),
        (122.4, 178.8), (125.9, 163.7), (122.2, 148.6), (117, 133.5),
        (105.6, 120.8), (91.8, 115.2), (78.7, 106.5), (69.2, 96.1),
        (57.9, 86.6), (46.1, 85.8), (29.2, 93.7), (14.2, 107.2),
        (-2.8, 122.3), (-11.9, 137.4), (-20.1, 152.5), (-25.2, 167.6),
        (-19.9, 182.7), (-18.7, 197.8), (-12.6, 212.9), (-13.7, 228),
        (-2.3, 233.6), (8.4, 242.3), (16.8, 257.4), (25.4, 268.5),
        (30, 279.6), (44.5, 282), (57.2, 292.4), (72, 293.9),
        (82, 298.7), (91.1, 307.4),
    ]
    A_TRACE_SMOOTH = int(os.environ.get("ALBO_ALD_A_TSMOOTH", 2))
    A_TRACE_SCALE = float(os.environ.get("ALBO_ALD_A_TSCALE", 1.0))

    @glyph('a')
    def a_a(c):
        """The scan's own a: its outer contour and its counter, traced,
        unsheared and set on Albo's x-height. See the block above."""
        xh = c["xh"]; u = xh / 429.0 * A_TRACE_SCALE; x0 = S * 0.6
        def path(tbl):
            pts = [(x0 + px * u, py * u) for px, py in tbl]
            pts = geom.smooth(pts, A_TRACE_SMOOTH, closed=True)
            return geom.poly(geom.resample(pts + [pts[0]], 14.0)[:-1])
        return geom.ink([path(A_TRACE_OUTER)], [path(A_TRACE_COUNTER)])

    # ------------------------------------------------------------ THE b, round 132
    # DRAWN AGAINST THE REFERENCE, by the a's method and in the a's units.
    # Measured UNSHEARED in Albo's design space off Flanker Griffo Italic
    # (docs/albo-aldine-targets.md section 1) and read back at 0.08 xh
    # intervals, and checked against the owner's scan crop of "habitum"
    # (aldine_autofit.SOURCES['b'], the one b crop that passes its own
    # self-check -- 1.56 xh of ink where 1.45-1.85 is expected).
    #
    # WHICH REFERENCE THE NUMBERS COME FROM, and why it is not the scan or
    # Poetica -- measured before a line was drawn, because the brief for this
    # round asked for IoU 0.80 against the scan where one exists and Poetica
    # otherwise, and NOTHING can reach that. Run `cmp_aldine_shape.py` with a
    # reference IN PLACE of the candidate and it scores the two references
    # against each other:
    #
    #        against          a      b      d      p      q      g
    #     Flanker vs scan    0.254  0.415  0.288  0.198  0.155   --
    #     Poetica vs scan    0.342  0.524  0.511  0.308  0.121   --
    #     Flanker vs Poetica 0.282  0.352  0.227  0.315  0.220  0.221
    #
    # The two best digital revivals of this hand do not reach 0.36 against each
    # other, and neither reaches 0.53 against the printed page -- Otsu over a
    # 66 px photograph of 1501 metal leaves a mask with holes in it, and the
    # scan comparison is bbox-normalized, which is the one scan quantity
    # docs/albo-aldine-targets.md section 6 rules INVALID (a shear leaves
    # horizontal run widths alone and inflates the bounding box). So 0.80 is
    # not a bar these instruments can clear against those two, and the only
    # reference where it demonstrably can be cleared is Flanker: the a, drawn
    # against Flanker in the round above this one, scores 0.842 there and 0.296
    # against Poetica.
    #
    # Flanker is therefore what every number below is measured from -- it is
    # also the face docs/albo-aldine-targets.md section 1 is entirely built out
    # of, and the b d p q bowls have to be the a's bowl, which is Flanker's.
    # The scan and Poetica overlays are still rendered and looked at every
    # pass. Where they can be scored the result is that these five now sit at
    # or above what FLANKER ITSELF scores against them: against Poetica, b
    # 0.341 (Flanker 0.352), d 0.226 (0.227), p 0.358 (0.315), q 0.253 (0.220),
    # g 0.298 (0.221); against the scans, b 0.401 (0.415), d 0.315 (0.288),
    # q 0.243 (0.155).
    #
    # ONE SCAN CROP IS BAD AND IT IS THE p's. `SOURCES['p']` is 61 x 112 px at
    # 70 px of x-height -- 0.87 xh WIDE, where a p with a bowl is 1.2-1.4 --
    # and the overlay shows the bowl's right side cut off at the crop's edge.
    # The self-check in the targets doc only tests a crop's HEIGHT, which this
    # one passes. Reported, not fixed: aldine_autofit.py is out of this round's
    # scope, and a re-crop wants the owner's eye on it the way the others had.
    #
    # WHY THE OLD b HAD TO GO rather than be tuned: it measured 310 units wide
    # unsheared against the reference's 439, on a page whose a is 443. A letter
    # 30% narrow than the letter it must sit beside is not a dial's worth of
    # wrong, and `bowl()` cannot make the shape anyway -- it draws a ring on
    # the pen, and the reference's bowl is a ring whose width is different at
    # every side.
    #
    # WHAT THE NUMBERS SAY (x measured from the head's left tip, xh = 429):
    #   the letter is 439 WIDE -- the same width as the a, which is what the
    #     reference also says (a 437, b 439)
    #   the stem is 70 wide at x 64-134 and DEAD STRAIGHT: the reference reads
    #     exactly 70 at every row from .19 xh to 1.47 xh, and leans 4 units
    #     over that whole run
    #   the head is a WEDGE REACHING LEFT, which is the single biggest
    #     correction in this round. rows 1.47/1.55/1.63/1.71 read
    #     -13..57 / -35..56 / -76..56 / -1..56 against an ascender top of
    #     1.75 xh: the right edge never moves off the stem, the LEFT edge
    #     swings out 63 units and comes back. The module's generic
    #     st(head=True) flick reaches RIGHT and overshoots the ascender,
    #     which is the i's head (measured off the scan, correctly, for the i)
    #     put on a letter that does not wear it.
    #   the bowl is the a's ring MOVED TO THE RIGHT OF THE STEM: its left
    #     extreme sits on the stem's right edge, its right extreme at 444, it
    #     springs off the stem at .90 xh and is merged into it from .55 down
    #     (rows .59 and .67 show a 28-wide wall standing clear; .51 shows one
    #     97-wide mass)
    #   the ring's width by position, taken perpendicular (a horizontal cut
    #     across a curve is corrected by the sine of its tangent, and the top
    #     and bottom come from vertical cuts at x 170/210/286): right 68,
    #     upper-right 61, top 34, upper-left 28, left 25, lower-left 26,
    #     bottom 26, lower-right 42. This is NOT the a's ring rotated 180 --
    #     the a's bottom is 52 and the b's is 26 -- so it gets its own table.
    #
    # WHAT SHIPPED, against what was measured. The geometry below was seeded
    # from those numbers and then run through `aldine_fit_shape.py b` against
    # Flanker, which raised the overlay IoU 0.615 -> 0.708 -> 0.721 over two
    # descents. Four dials moved off their measured value and each is worth
    # knowing: the bowl's centre came in 10 units (289 -> 279) and its radius
    # out 4 (155 -> 159); the squareness went 1.90 -> 2.44, a squarer bowl
    # than the a's; the head's reach went 63 -> 74 and its tip 54 -> 60 below
    # the ascender. The skew went 0.06 -> 0.13, which is a third of the 0.35
    # the reference's own top-to-bottom lean implies -- the reference's bowl
    # is NOT a skewed superellipse (its left boundary runs nearly straight
    # from (201,386) to (70,245)), so the skew that best fits the whole shape
    # is not the one that reproduces its lean. Pushing it to 0.34 by hand cost
    # 0.06 of IoU and was reverted.
    # FIT's b and p rows (0.550 weight, 1.100 / 0.725 width) are RETIRED here.
    # They were solved by aldine_autofit against the OLD construction, and the
    # wrapper applies them as a -4.8 unit buffer and an x-scale on the finished
    # outline: on a letter whose every width is now the reference's own
    # measurement they do not correct anything, they undo it. The a carries no
    # FIT row for the same reason.
    FIT.pop('b', None); FIT.pop('p', None)
    B_STEM_X = float(os.environ.get("ALBO_ALD_B_STEM_X", 114.0))    # stem centre, units from the head's tip
    B_STEM_W = float(os.environ.get("ALBO_ALD_B_STEMW", 70.0))     # units
    # LIGHTER (owner 2026-09-16: "reduce visual weight of top serif on b and
    # d"): reach 74 -> 58, drop 60 -> 44, and the underside rejoins the stem
    # 96 below the top instead of 143 -- the wedge loses a third of its area
    # and stops reading as a flag on the ascender. The a's head rides these
    # same dials, so it follows.
    B_HEAD_R = float(os.environ.get("ALBO_ALD_B_HEAD_R", 58.0))    # the head's reach LEFT of the stem
    B_HEAD_DROP = float(os.environ.get("ALBO_ALD_B_HEAD_D", 44.0))  # its tip, below the stem's top
    B_HEAD_FOOT = float(os.environ.get("ALBO_ALD_B_HEAD_F", 96.0))  # where its underside rejoins the stem
    B_CX = float(os.environ.get("ALBO_ALD_B_CX", 279.0))           # bowl centre, units
    B_RX = float(os.environ.get("ALBO_ALD_B_RX", 159.0))           # the a's A_RX
    B_CY = float(os.environ.get("ALBO_ALD_B_CY", 207.0))
    # ---------------------------------------------------------------- ROUND 135
    # THE MIDDLE STROKE IS PAGELLA'S. Owner 2026-09-16: *"match the middle
    # stroke curve of pagella"* -- the arm that leaves the stem and carries the
    # bowl over. Measured on one row at a time, so the page's shear cancels:
    # the arm's horizontal run, and its center's offset from the STEM's center
    # at that same row.
    #
    #   height   Pagella          Poetica          Albo (round 134)   now
    #   .85      off 102 t 45 gap 51   96 / 34 / 51   90 / 46 / 33   106 / 44 / 50
    #   .80       79 / 31 / 35        73 / 27 / 32   68 / 38 / 15    81 / 32 / 31
    #   .75       61 / 26 / 20        57 / 26 / 16   53 / 33 /  2    64 / 28 / 16
    #   .72       53 / 25 / 13        48 / 25 /  8   merged          55 / 24 /  9
    #   spring        .67                 .71            .75             .69
    #
    # TWO REFERENCES AGREE HERE AND THE THIRD DOES NOT, which is what makes
    # this safe to move: Pagella and Poetica are within 5 units of each other
    # on every row, while FLANKER -- the face this letter was fitted against in
    # round 132 -- opens a **119-unit** gap at .85 against their 51, because
    # its b is a far wider, more open letter. Albo was drawn to Flanker's
    # thickness and Flanker's spring and came out with neither: an arm 27%
    # thicker than Pagella's leaving the stem with a 2-unit slit where the
    # references leave 16-20.
    #
    # WHAT MOVED. The skew 0.13 -> 0.25, which is the lever because the arm has
    # to come RIGHT while the bowl's bottom goes LEFT -- a translation does the
    # first and the wrong thing to the second (Albo's bowl bottom already sits
    # 39 units right of Pagella's at .15). The module's own note records 0.34
    # being tried by hand in round 132 and costing 0.06 of IoU against Flanker;
    # 0.25 is not that, it is the value the two agreeing references ask for,
    # and it is still well under the 0.35 the reference's own top-to-bottom
    # lean implies. The IoU it costs against Flanker is 0.706 -> 0.687 and it
    # BUYS 0.462 -> 0.468 against Pagella; both numbers are small because this
    # comparison is dominated by the ascender, which is 1.76 xh here against
    # Pagella's 1.52 and is a family metric, not this letter's.
    B_SKEW = float(os.environ.get("ALBO_ALD_B_SKEW", 0.25))
    B_K = float(os.environ.get("ALBO_ALD_B_K", 2.44))
    B_EXIT = float(os.environ.get("ALBO_ALD_B_EXIT", 78.0))   # how far right the stem's turned bottom runs
    # B_RING IS NOT THE b's TABLE ANY MORE, AND THAT IS DELIBERATE: `a_p` reads
    # it too ("the p takes B_RING and its own centre"), and the p is not in
    # this round. Left byte-for-byte as round 132 cut it, so the p is
    # unchanged; the b takes B_BOWL_RING below. Whoever brings the p to a
    # reference next should decide whether the two letters share one table
    # again -- the reference says their flanks agree, so they probably should.
    B_RING = [(0, 68), (45, 61), (90, 34), (135, 28), (180, 25), (225, 26), (270, 26), (315, 42)]
    if os.environ.get("ALBO_ALD_B_RING"):
        B_RING = [(float(a), float(w)) for a, w in
                  (kv.split(":") for kv in os.environ["ALBO_ALD_B_RING"].split(","))]
    # THE ARM IS A HAIRLINE FOR LONGER, three keys of it. 135 (0.87 xh) is the
    # top of the arm and was already right; 150 and 165 (0.79 and 0.70 xh) are
    # new, and they are what takes the run from 33 to 28 units at .75 against
    # Pagella's 26. 180 -- the bowl's left flank, where it merges into the stem
    # -- comes 25 -> 23 with them so the interpolation does not bulge back out
    # below the arm. `keyed_ring` smooths the table over 4 samples, so a single
    # narrow key moves the ink about a third as far as it reads.
    B_BOWL_RING = [(0, 68), (45, 61), (90, 34), (135, 26), (150, 17), (165, 18),
                   (180, 23), (225, 26), (270, 26), (315, 42)]
    if os.environ.get("ALBO_ALD_B_BOWL_RING"):
        B_BOWL_RING = [(float(a), float(w)) for a, w in
                       (kv.split(":") for kv in os.environ["ALBO_ALD_B_BOWL_RING"].split(","))]

    def bd_head(xl, xr, yt, u=1.0, reach=None, drop=None, foot=None):
        """The Aldine ascender head, reaching LEFT across the stem's top.

        Drawn as a polygon rather than through `wedge_head`, because that one
        is the i's head measured off the scan -- a diagonal crossing the stem
        and reaching FURTHER RIGHT than left -- and the reference's b, d and p
        wear the opposite shape: the right edge stays on the stem and only the
        left swings out. The top edge bows (the 1.71 row reads -1 where a
        straight line from the corner to the tip would give -14), so both
        edges are cubics rather than straight cuts.

        The first cut of this was a straight-sided polygon and it rendered as
        a plain triangular wedge with a kink in its underside -- cropped and
        set beside the reference's own b and d heads it read as a different
        letter's serif. The curved edges cost 0.010 of IoU on the b and 0.014
        on the d and were kept anyway: the number cannot see a kink, and the
        head is most of the page's texture (b d h k l)."""
        r = (B_HEAD_R if reach is None else reach) * u
        dp = (B_HEAD_DROP if drop is None else drop) * u
        ft = (B_HEAD_FOOT if foot is None else foot) * u
        tip = xl - r
        # the tip hangs in a small BEAK: the reference's left end drops below
        # the line of the top edge and turns back, which is the nib being set
        # down and dragged up-right rather than a wedge cut to a point.
        top = cubic((tip, yt - dp * 0.66), (tip + r * 0.50, yt - dp * 0.26),
                    (xl - r * 0.10, yt - dp * 0.05), (xr, yt))
        und = cubic((xl, yt - ft), (tip + r * 0.74, yt - dp - (ft - dp) * 0.64),
                    (tip + r * 0.04, yt - dp - (ft - dp) * 0.22), (tip - r * 0.06, yt - dp * 1.04))
        return geom.poly(list(top) + [(xr, yt - ft)] + list(und))

    @glyph('b')
    def a_b(c):
        """The Aldine b: a straight ascender under a left-reaching wedge head,
        with the a's ring hung on its right. See the block above for where
        every number comes from."""
        xh = c["xh"]; u = xh / A_UNIT; x0 = S * 0.6
        xs = x0 + B_STEM_X * u; sw = B_STEM_W * u
        # THE STEM'S BOTTOM IS CUT AND TURNED, not squared on the baseline.
        # The reference's rows go -2..67 at .19 xh, 12..90 at .11 and 48..241
        # at .03 against a stem at -12..58: below a fifth of the x-height the
        # stroke leaves the stem's line and runs right into the bowl's bottom
        # arc, and by the baseline there is no ink at the stem's left edge at
        # all. It is also what ALIGNS the letter -- the comparison puts the
        # leftmost ink of both letters together, and a stem squared on the
        # baseline puts that point 23 units further left than the reference's,
        # which shifted the whole ascender and cost 0.18 of IoU on its own.
        sp = catmull([(xs, c["asc"]), (xs, xh * 0.62), (xs, xh * 0.28),
                      (xs + 18 * u, 46 * u), (xs + 64 * u, 14 * u),
                      (xs + B_EXIT * u, 22 * u)], tension=0.5)
        stem = stroke(sp, widths([(0.0, sw), (0.78, sw), (0.90, sw * 0.84), (1.0, 46 * u)]))
        head = bd_head(xs - sw / 2, xs + sw / 2, c["asc"], u)
        ry = (xh + OVER * 0.6) / 2.0
        bowl_ = keyed_ring(x0 + B_CX * u, B_CY * u, B_RX * u, ry, B_BOWL_RING,
                           k=B_K, skew=B_SKEW, unit=u)
        return geom.ink([bowl_, stem, head])

    # ------------------------------------------------------------ THE d, round 132
    # THE d IS THE a's BOWL ON AN ASCENDER, and the reference says so in
    # numbers rather than in prose. Its rows and the a's are the same letter:
    #
    #        row .25/.27      left flank   bowl's right wall   stem
    #   a    -11-68(79)       79           213-244(32)         258-328(70)
    #   d    -19-58(77)       77           212-244(32)         250-322(72)
    #
    # -- the bowl's right wall is at the SAME x in both, and the stem is 8
    # units apart. So the d reuses A_RING, A_RX, A_CY, A_SKEW, A_K and the a's
    # tail unchanged, and differs only in what stands on the right: an
    # ascender to 770 with the left-reaching wedge head, in place of the a's
    # short stem and its blunt right-hand head.
    #
    # THE d KEEPS THE a's TAIL, which is not an assumption: the reference's
    # row .11 reads 255-404 against a stem at 250-320, so 84 units of ink
    # stand right of the stem at a tenth of the x-height, and the bbox reaches
    # 406. The a's tail reaches 82 past its own stem. Same stroke.
    # The head's reach is 64 units here against the b's 63 (row 1.63 reads
    # 186-319 against a stem at 250-320), so one number serves both.
    #
    # WHAT SHIPPED: 0.567 against Poetica and 0.235 against Flanker before this
    # round; drawn from the numbers it came out at 0.829 against Flanker, and
    # `aldine_fit_shape.py d` took it to 0.846 by moving four dials a little --
    # the stem in 5 (317 -> 312), the bowl's radius out 4, its centre down 4,
    # and the tail's tip out 16 (434 -> 450). It is the best-matching of the
    # five, which is what you would expect of the letter the reference draws as
    # the a with an ascender on it.
    D_STEM_X = float(os.environ.get("ALBO_ALD_D_STEM_X", 312.0))   # = the a's A_STEM_X
    D_STEM_W = float(os.environ.get("ALBO_ALD_D_STEMW", 70.0))
    D_RX = float(os.environ.get("ALBO_ALD_D_RX", 159.0))
    D_CY = float(os.environ.get("ALBO_ALD_D_CY", 211.0))
    D_SKEW = float(os.environ.get("ALBO_ALD_D_SKEW", 0.06))
    D_TAIL_X = float(os.environ.get("ALBO_ALD_D_TAIL_X", 450.0))
    D_TAIL_Y = float(os.environ.get("ALBO_ALD_D_TAIL_Y", 0.15))
    D_RING = list(A_RING)
    if os.environ.get("ALBO_ALD_D_RING"):
        D_RING = [(float(a), float(w)) for a, w in
                  (kv.split(":") for kv in os.environ["ALBO_ALD_D_RING"].split(","))]

    @glyph('d')
    def a_d(c):
        xh = c["xh"]; u = xh / A_UNIT; x0 = S * 0.6
        xs = x0 + D_STEM_X * u; sw = D_STEM_W * u
        stem = stroke([(xs, S * 0.10), (xs, c["asc"])], sw)
        head = bd_head(xs - sw / 2, xs + sw / 2, c["asc"], u)
        ry = (xh + OVER * 0.6) / 2.0
        bowl_ = keyed_ring(x0 + D_RX * u, D_CY * u, D_RX * u, ry, D_RING,
                           k=A_K, skew=D_SKEW, unit=u)
        tip = (x0 + D_TAIL_X * u, xh * D_TAIL_Y)
        tp = catmull([(xs, xh * 0.30), (xs + 4 * u, xh * 0.10), (xs + 30 * u, 26 * u),
                      (xs + 70 * u, 30 * u), (tip[0] - 30 * u, tip[1] - 14 * u), tip], tension=0.5)
        tail = stroke(tp, widths([(0.0, sw), (0.30, sw * 0.90), (0.62, sw * 0.62), (1.0, sw * 0.30)]),
                      cut1=CUT)
        return geom.ink([bowl_, stem, head, tail])

    # ------------------------------------------------------------ THE p, round 132
    # THE p IS THE b WITH THE ASCENDER TURNED INTO A DESCENDER, and its head
    # moved down to the x-line. The reference's p and b agree wall for wall --
    # the bowl's right wall reads 68 at the flank in both, the stem 70 -- so
    # the p takes B_RING and its own centre.
    #
    # TWO THINGS THE p HAS THAT THE b DOES NOT:
    #   the HEAD SITS AT THE X-LINE. Rows .80/.88/.96 read -5..66 / -77..61 /
    #     -29..47 against a stem at -1..68: the same wedge as the ascender's,
    #     reaching 76 left, peaking at 0.88 of the way up rather than 0.93,
    #     because there is less stroke above it to lean on.
    #   the DESCENDER ENDS IN A SPREAD FOOT, and this one is confirmed by the
    #     printed page and not only by the outline. Flanker's row -0.72 reads
    #     -65..150 -- 216 units against a 70 stem -- and the owner's scan crop
    #     of "pater" reads 143 at -0.55 against a stem of 63, which is 2.3x
    #     the stem at 0.05 xh above ITS own descender depth (the crop's ink is
    #     1.60 xh, so its baseline-to-foot is 0.60 xh). Two independent
    #     sources, one shape. Albo's descender is 280 rather than the
    #     reference's 326, so the foot is placed on Albo's own depth.
    #
    # WHAT SHIPPED: 0.077 against Flanker before this round -- the old p was
    # 190 units wide unsheared against the reference's 436, less than half a
    # letter. Drawn from the numbers and fitted twice it is 0.710. The bowl
    # came out 6 units tighter than the b's (the reference's p bowl is 280
    # across where its b's is 295) and the head's tip 15 units shallower.
    P_STEM_X = float(os.environ.get("ALBO_ALD_P_STEM_X", 114.0))
    P_STEM_W = float(os.environ.get("ALBO_ALD_P_STEMW", 70.0))
    P_CX = float(os.environ.get("ALBO_ALD_P_CX", 273.0))    # 6 tighter than the b: the reference's p bowl is 280 across, the b's 295
    P_RX = float(os.environ.get("ALBO_ALD_P_RX", 145.0))
    P_CY = float(os.environ.get("ALBO_ALD_P_CY", 203.0))
    P_SKEW = float(os.environ.get("ALBO_ALD_P_SKEW", 0.13))
    P_HEAD_R = float(os.environ.get("ALBO_ALD_P_HEAD_R", 79.0))   # row .88 reads -77 against a stem at -1
    P_HEAD_D = float(os.environ.get("ALBO_ALD_P_HEAD_D", 45.0))
    P_HEAD_F = float(os.environ.get("ALBO_ALD_P_HEAD_F", 98.0))
    # THE FOOT'S THICKNESS IS MEASURED AT ITS TIPS, NOT AT THE STEM, and the
    # first cut had the profile INVERTED. Vertical cuts through the reference's
    # p read 20 at x -60 and 140, 26 at -40 and 110, 43 at -10, and 70 under
    # the stem -- and every one of them bottoms at exactly -326, so the bar's
    # UNDERSIDE is a straight line on the descender depth and all the thickening
    # happens on its top edge. The q's foot reads the same numbers (20/26/43/68)
    # at the mirrored positions, which is why one helper serves both.
    # The fitter pinned this dial at its low rail twice; measuring it says the
    # rail was right and the profile was wrong.
    #
    # DO NOT LET THE FITTER SIZE THIS FOOT. It reached for 105 left and 75
    # right, and the second of those is an artifact with a mechanism: Albo's
    # descender is 280 where the reference's is 326, the comparison is
    # baseline-aligned, so NONE of this foot can ever overlap the reference's
    # -- every pixel of it counts as excess and the only way to score better
    # is to delete it. The left reach is the opposite case and is real: the
    # foot's left tip is the letter's leftmost ink, which is what the two
    # masks are aligned on, so it sets where the whole letter sits. Both are
    # shipped at the measured value (98 / 116, against the reference's -65 and
    # 150 either side of a stem centred on 33), which costs 0.03 of IoU on the
    # p and 0.02 on the q against the fitter's answer.
    PQ_FOOT_L = float(os.environ.get("ALBO_ALD_PQ_FOOT_L", 98.0))   # reach left of the stem centre; ref -65 against a centre of 33
    PQ_FOOT_R = float(os.environ.get("ALBO_ALD_PQ_FOOT_R", 116.0))  # and right; ref 150
    PQ_FOOT_T = float(os.environ.get("ALBO_ALD_PQ_FOOT_T", 21.0))   # AT THE TIPS

    def pq_foot(xc, ybot, u=1.0):
        """The descender's spread foot: a flat-bottomed two-sided bar, 21 units
        at the tips and 3.2x that where the stem lands. The centerline RISES
        toward the middle, because the underside is straight and the stroke
        thickens upward from it."""
        l = PQ_FOOT_L * u; r = PQ_FOOT_R * u; t = PQ_FOOT_T * u
        p = catmull([(xc - l, ybot + t * 0.50), (xc - l * 0.46, ybot + t * 0.68),
                     (xc, ybot + t * 1.60), (xc + r * 0.46, ybot + t * 0.68),
                     (xc + r, ybot + t * 0.50)], tension=0.5)
        return stroke(p, widths([(0.0, t), (0.24, t * 1.32), (0.50, t * 3.20),
                                 (0.76, t * 1.32), (1.0, t)]), cut0=CUT, cut1=CUT)

    @glyph('p')
    def a_p(c):
        xh = c["xh"]; u = xh / A_UNIT; x0 = S * 0.6
        xs = x0 + P_STEM_X * u; sw = P_STEM_W * u; ybot = -c["desc"]
        stem = stroke([(xs, ybot + PQ_FOOT_T * u * 1.30), (xs, xh)], sw)
        head = bd_head(xs - sw / 2, xs + sw / 2, xh, u,
                       reach=P_HEAD_R, drop=P_HEAD_D, foot=P_HEAD_F)
        ry = (xh + OVER * 0.6) / 2.0
        bowl_ = keyed_ring(x0 + P_CX * u, P_CY * u, P_RX * u, ry, B_RING,
                           k=B_K, skew=P_SKEW, unit=u)
        return geom.ink([bowl_, stem, head, pq_foot(xs, ybot, u)])

    # ------------------------------------------------------------ THE q, round 132
    # THE q IS THE d's BOWL WITH THE STEM RUNNING DOWN INSTEAD OF UP, and the
    # reference's rows make that literal too: its .24 row reads
    # 1-80(79) 220-252(31) 268-338(69) against the a's .25
    # -11-68(79) 213-244(32) 258-328(70) -- the same three runs, the same
    # widths, shifted 10 units. So it carries A_RING and the a's geometry.
    #
    # NO HEAD AND NO TAIL. The stem's top is inside the bowl's join (row .88
    # reads one 86-wide mass where the bowl's top arc comes in, row .96 one
    # 222-wide run), so there is nothing for a head to sit on; and the .00 row
    # shows no ink right of the stem at the baseline, where the a and the d
    # both carry 80-odd units of tail. The descender ends in the p's foot.
    #
    # THE SCAN CANNOT CHECK THE BOTTOM HALF OF THIS LETTER. The "qu" crop is
    # 1.13 xh of ink where 1.45-1.85 is expected -- it cuts the descender off
    # entirely (docs/albo-aldine-targets.md section 6). Its bowl rows are
    # usable and agree (band 69 / 70 against a stem of 70); nothing below the
    # baseline is in the crop at all, so the foot here rests on the p's two
    # sources and on this letter being the p's mirror, not on the q's own scan.
    #
    # WHAT SHIPPED: seeded from the a and then fitted, 0.759 -> 0.781 -> 0.758
    # (the last step is the foot being put back to its MEASURED size, below).
    # Only the stem's centre moved, 317 -> 322. The fitter also offered a 66
    # stem for +0.001 and it was refused: every stroke in this letter is the
    # reference's own measurement and 70 is what the reference reads at every
    # row from -0.64 xh to .24.
    Q_STEM_X = float(os.environ.get("ALBO_ALD_Q_STEM_X", 322.0))
    Q_STEM_W = float(os.environ.get("ALBO_ALD_Q_STEMW", 70.0))
    Q_RX = float(os.environ.get("ALBO_ALD_Q_RX", 155.0))
    Q_CY = float(os.environ.get("ALBO_ALD_Q_CY", 215.0))
    Q_SKEW = float(os.environ.get("ALBO_ALD_Q_SKEW", 0.06))

    @glyph('q')
    def a_q(c):
        xh = c["xh"]; u = xh / A_UNIT; x0 = S * 0.6
        xs = x0 + Q_STEM_X * u; sw = Q_STEM_W * u; ybot = -c["desc"]
        stem = stroke([(xs, ybot + PQ_FOOT_T * u * 1.30), (xs, xh)], sw, cut1=CUT)
        ry = (xh + OVER * 0.6) / 2.0
        bowl_ = keyed_ring(x0 + Q_RX * u, Q_CY * u, Q_RX * u, ry, A_RING,
                           k=A_K, skew=Q_SKEW, unit=u)
        return geom.ink([bowl_, stem, pq_foot(xs, ybot, u)])

    # THE r, round 132 -- the family's stem and head, then an arm that is the
    # arch's first half made STEEPER, stopped in a ball.
    #   THE ARM springs off the stem exactly where the arch does and climbs
    #     harder: normalized on the pitch, Flanker's arm is 0.55 xh high at
    #     0.22 P, 0.76 at 0.36, 0.88 at 0.50, and Poetica's 0.55 / 0.74 / 0.85
    #     at 0.165 / 0.32 / 0.47 -- the same curve, and above the arch's
    #     0.575 / 0.694 / 0.796 at those same distances.
    #   IT IS THE HAIRLINE. Flanker's vertical cut at x140 gives 47 units on a
    #     stroke rising at 63 degrees: 47*cos63 = 21.
    #   THE TERMINAL IS A BALL, not a flick, and it is heavy: 99 x 103 units
    #     in Flanker (vertical cuts x220/250/280 -> 77/103/91) and 84 x 106 in
    #     Poetica -- an OVAL taller than wide, not a disc -- and the macro's r
    #     shows the same blob at .75. Its center sits 0.66 of the pitch right
    #     of the stem's center in Poetica and 0.76 in Flanker, both at 0.876
    #     xh; Poetica's is taken, with the arm RUNNING INTO it rather than
    #     stopping short (the first cut left a one-unit gap at .80).
    #   THE r HAS NO EXIT. Flanker reads a flat 70 from .02 to .15 and Poetica
    #     49-57; the stroke stops at the baseline. The module gave it the
    #     shared foot, which is a letter the references do not print.
    R_ARM_X = float(os.environ.get("ALBO_ALD_R_ARM_X", 0.660))   # the ball's center, x the pitch
    R_ARM_Y = float(os.environ.get("ALBO_ALD_R_ARM_Y", 0.876))   # its center, x xh
    R_ARM_W = float(os.environ.get("ALBO_ALD_R_ARM_W", 84.0))    # its width, units
    R_ARM_H = float(os.environ.get("ALBO_ALD_R_ARM_H", 106.0))   # its height, units

    @glyph('r')
    def a_r(c):
        xh = c["xh"]; u = hm_u(c); x0 = S * 1.0; P = HM_PITCH * xh; sw = HM_STEMW * u
        t = HM_ARCH_T * u
        arm = catmull([(x0, xh * HM_SPRING), (x0 + P * 0.17, xh * 0.55),
                       (x0 + P * 0.32, xh * 0.745), (x0 + P * 0.47, xh * 0.850),
                       (x0 + P * R_ARM_X, xh * 0.876)], tension=0.5)
        ball = geom.poly(superellipse(x0 + P * R_ARM_X, R_ARM_Y * xh,
                                      R_ARM_W * u / 2, R_ARM_H * u / 2,
                                      0.0, 2 * math.pi, 2.2))
        return geom.ink([hm_stem(c, x0, 0, xh), hm_head(c, x0, xh),
                         stroke(arm, widths([(0.00, sw * 0.94), (0.16, t * 1.15),
                                             (0.42, t), (0.72, t * 1.25), (1.00, t * 2.1)])),
                         ball])

    # ------------------------------------- THE NINE DIAGONALS AND ODD ONES
    # v w x y z k f t j, round 132: drawn against a reference rather than
    # tuned. Owner 2026-09-15, "examine a then each subsequent letter, take
    # multiple passes at each until the shape and strokes and serifs match what
    # they should based on a referenced vector or bitmap", and 2026-09-16,
    # "poetica is my preferred fallback."
    #
    # NONE OF THESE NINE HAS A SCAN CROP -- docs/albo-aldine-targets.md section
    # 6 names c f g j k n t v w x y z as the twelve without one -- so the SHAPE
    # reference for every one of them is refs/poetica-std-regular.otf, measured
    # UNSHEARED in Albo's own units by
    #     aldine_targets.py --font refs/poetica-std-regular.otf --md <chars>
    # The WEIGHT reference stays Flanker Griffo Italic, the face that carries
    # the 1501 page's colour: lowercase stem 70 units (0.83 S), hairline 22-24.
    # Each letter's block below says which it followed for each terminal.
    #
    # WHERE THE TWO DISAGREE the owner's standing brief decides: the chancery
    # references "describe what a flourish may do but don't move the text
    # lowercase", and the target is the metal. So the y's swash tail is drawn
    # back inside Flanker's extent (that one costs IoU and the cost is
    # recorded at the letter), while the f's and j's leftward tails are kept
    # because BOTH references sweep them. Flanker's own looped k is not
    # adopted either: Poetica's open arm is the simpler letter and it is the
    # shape reference.
    #
    # THICK AND THIN FOLLOW THE PEN. This is the one thing a diagonal letter
    # gets wrong when it is drawn as two lines of declared weight, which is
    # what `_diag` above was doing: the stroke running upper-left to
    # lower-right is the DOWNSTROKE and carries the pen's full width, the one
    # running lower-left to upper-right is the hairline. So the v w y are
    # thick-then-thin left to right, the x crosses thick over thin, and the z
    # -- whose diagonal runs the other way, down to the LEFT, along the pen's
    # own edge -- has a thin diagonal between thick bars (targets section 2:
    # "the z's thick strokes are the horizontal bars (70) and its diagonal is
    # the thin one at 25"). The old v w x z read `vert med` off the targets
    # table as if it were a stem; section 6 says plainly that x y z have no
    # vertical stem and that median falls on the THIN stroke.
    #
    # WHERE EACH ONE LANDED, by cmp_aldine_shape against Poetica (IoU, start ->
    # end), with the stroke width the built font actually measures beside it
    # (aldine_targets --font on the TTF; Flanker's lowercase is 70):
    #
    #     v 0.088 -> 0.756  67    w 0.096 -> 0.765  68    x 0.131 -> 0.691  60
    #     y 0.155 -> 0.075  68    z 0.275 -> 0.709  67    k 0.267 -> 0.399  68
    #     f 0.000 -> 0.649  65    t 0.316 -> 0.718  65    j 0.022 -> 0.649  67
    #
    # THE BRIEF'S 0.80 GATE IS NOT REACHABLE IN THIS INSTRUMENT, and the number
    # that says so is FLANKER'S OWN: scoring refs/flanker-griffo-italic.otf
    # against Poetica the same way gives v 0.220, w 0.250, x 0.259, y 0.034,
    # z 0.340, k 0.448, f 0.213, t 0.661, j 0.210 -- mean 0.29. Two real faces
    # of the same tradition do not reach 0.8 of each other, so 0.8 would mean
    # "be Poetica", which the weight half of the brief forbids. Eight of these
    # nine beat that ceiling; the k does not, for a reason it carries below.
    #
    # THE APEX RULE, and it cost every letter in this module a wrong reading
    # before it was found: a stroke whose CENTRELINE ends on the x-line puts
    # its INK half a width above it. The first cut of these letters did that
    # at every apex and the x came out 459 units tall against the family's
    # 430-436 -- and `cmp_aldine_shape` scales both fonts by the bbox top of
    # their OWN `x`, so a tall x quietly shrank every other Albo letter by 6%
    # in the comparison, including letters nobody here is drawing. Every apex
    # is now placed so the ink tops at 434-446 (`pen.OVER` is 14), which alone
    # moved v 0.732 -> 0.762 and x 0.531 -> 0.664 and unpinned two fitters that
    # had been railing. Check the bbox, not the coordinate, after moving a top.
    #
    # EVERY `<L>_W` AND `<L>_TW` BELOW IS BAKED FROM `aldine_fit_shape.py`
    # (coordinate descent on the overlay IoU, --ref poetica), with ONE
    # exception that is deliberate and worth knowing: the COLOUR dials were
    # NOT taken from the fitter. It wanted 0.84-0.96 on the v w x z f -- which
    # is Poetica's own lighter stroke -- and the brief's weight reference is
    # Flanker at 70. They are set instead so the BUILT font measures 60-68
    # (the table above), which is Flanker's 70 less the bite `cut.blend` takes
    # out of a curved stroke, and which is where Albo's own redrawn a (72) and
    # n (69) already sit. Two letters also kept a measured value over a fitted
    # one: the w's apex (its fitter wanted 1.00, but Poetica's `.97` row has
    # NO middle run, so there is no ink there) and the f's top (its fitter
    # railed at 1.74 xh, which would put the f's hook below b d h l on the
    # same page; Flanker's f is ABOVE its b).
    D_UNIT = 429.0          # the reference's x-height, and Albo's

    def d_frame(c, wide=1.0, x0=None):
        """The frame all nine are drawn in. `P(x, y)` maps a REFERENCE
        coordinate -- x in units from the letter's own left ink edge, y as a
        fraction of the x-height -- into design space, and `u` converts a
        reference WIDTH into design units. `wide` is the letter's width dial,
        so a fitter can stretch the drawing without touching a coordinate.

        Everything here is UNSHEARED, like the rest of the module: build.py
        shears by FJORD_SLANT afterwards, and the references were unsheared by
        their own declared italic angle before being measured."""
        xh = c["xh"]; u = xh / D_UNIT
        x0 = S * 0.6 if x0 is None else x0
        return (lambda px, py: (x0 + px * wide * u, py * xh)), u

    def d_pen(pts, keys, u, cut0=None, cut1=None, tension=0.5, tw=1.0):
        """One movement of the pen: a catmull through `pts` (design space)
        carrying the width table `keys` -- (t, REFERENCE units) pairs read off
        the reference's own runs and converted here by `u`. `tw` scales every
        width, so a letter's colour is one dial.

        A catmull and not a pair of straight lines, because a chancery stroke's
        entry, body and terminal are a single movement. Drawing the entry as a
        separate bar is what made the old letters' heads sit ON the letter
        instead of in it, and a straight `_diag` cannot bow at all -- Poetica's
        v leans 0.27 dx/dy at .75 and 0.20 at .10, which is a curve."""
        p = catmull(list(pts), tension=tension) if len(pts) > 2 else list(pts)
        return stroke(p, widths([(t, w * u * tw) for t, w in keys]),
                      cut0=cut0, cut1=cut1)

    def d_dial(name, default):
        return float(os.environ.get("ALBO_ALD_" + name, default))

    def d_ball(P, u, x, y, r, squash=1.10, deg=None):
        """The round terminal the chancery references hang on a rising
        hairline -- the v w y's right stroke, the x's top right. It is a
        separate blob rather than more width on the stroke because `stroke`
        ends in a FLAT face: widening the last samples gives an angular flag,
        which is what the first cut of these letters drew, and Poetica's is a
        round bulb that reaches back over the stroke it sits on. Same reason
        the i's dot is a nib touch and not a circle: it lies on the PEN'S
        angle, so it is an oval leaning HEAD_DEG, not a disc."""
        cx, cy = P(x, y)
        a = math.radians(HEAD_DEG if deg is None else deg)
        pts = superellipse(0.0, 0.0, r * u * squash, r * u, 0.0, 2 * math.pi, 2.0)[:-1]
        ca, sa = math.cos(a), math.sin(a)
        return geom.poly([(cx + px * ca - py * sa, cy + px * sa + py * ca)
                          for px, py in pts])

    # ---------------------------------------------------------------- THE f
    # POETICA for the shape (there is no scan crop of an f -- targets section
    # 6 lists it among the twelve without one), FLANKER for the extent of the
    # two ends. Measured unsheared by aldine_targets.py, x in units from the
    # letter's own left ink edge, y as a fraction of the x-height:
    #   the f is ONE movement -- hook, stem, tail -- and not three pieces.
    #   its stem is a long shallow S: centre 231 at 1.40, 215 at 1.15, 226 at
    #   .75, 238 at .10, 233 at -0.12, 218 at -0.30, then hard left.
    #   the width along it runs 40 at 1.40, 66 at .97 (the belly), 58 at .25,
    #   43 at -0.12, 32 at -0.30 -- it tapers BOTH ways off a belly at the
    #   x-line, which is most of why an f reads as written rather than built.
    #   the hook leaves the stem at ~1.42 and ends in a ball. Poetica tops out
    #   at 1.69 xh and Flanker at 1.82; Albo's own l draws 1.84, so the hook
    #   is taken to Albo's ascender and not to Poetica's shorter one.
    #   the bar spans 117-350 at .90 (Flanker 253 wide, Poetica 233) and is 42
    #   thick in Poetica, 61 in Flanker -- drawn at 48, between them.
    #   the tail: BOTH references sweep it left to the letter's own left edge
    #   (Poetica reaches x 6 at -0.55, Flanker x 32 at the same height), so
    #   unlike the y's tail this one is NOT a Poetica-only flourish and it is
    #   drawn swept.
    F_W = d_dial("F_W", 0.98)          # the letter's width, x the reference
    F_TW = d_dial("F_TW", 1.12)        # its colour: every declared width x this
    F_BAR = d_dial("F_BAR", 0.92)     # the crossbar's height, x xh
    F_TOP = d_dial("F_TOP", 1.78)     # the hook's top, x xh (Albo's ascender)
    F_TAIL = d_dial("F_TAIL", -0.62)  # the tail's floor, x xh

    @glyph('f')
    def a_f(c):
        """One movement: the hook's ball, over the ascender, down the stem's
        long S, out to the left below the baseline into the tail's ball. The
        bar is the only stroke drawn separately."""
        P, u = d_frame(c, F_W); T = F_TOP; B = F_TAIL
        body = d_pen([P(356, T - 0.235), P(372, T - 0.145), P(360, T - 0.04),
                      P(324, T), P(283, T - 0.025),
                      P(250, T - 0.12), P(231, 1.45), P(215, 1.15), P(220, 0.95),
                      P(233, 0.50), P(238, 0.10), P(233, -0.14), P(216, -0.34),
                      P(170, B + 0.08), P(100, B), P(40, B + 0.02), P(12, B + 0.10)],
                     [(0.00, 32), (0.04, 54), (0.09, 60), (0.17, 44), (0.26, 42),
                      (0.35, 60), (0.47, 66), (0.54, 64), (0.66, 60), (0.74, 52),
                      (0.81, 43), (0.87, 34), (0.93, 46), (0.97, 50), (1.00, 22)],
                     u, tw=F_TW)
        bar = d_pen([P(117, F_BAR - 0.045), P(230, F_BAR), P(350, F_BAR + 0.045)],
                    [(0.0, 22), (0.18, 48), (0.80, 48), (1.0, 24)], u, tw=F_TW)
        return geom.ink([body, bar])

    # ---------------------------------------------------------------- THE t
    # POETICA for the shape, FLANKER for the height above the x-line.
    #   the stem is a STEM -- centre 103 at .50 and .75, 108 at .25, so it is
    #   vertical in design space and not a diagonal -- 57-58 wide (Flanker 70).
    #   it rises to a POINT above the x-line: Poetica 1.224 xh, Flanker 1.184
    #   ("top at 508 -- 79 units above the x-line", targets section 2).
    #   the bar at .90 spans 11-221 (Flanker 253 wide) and is 41 thick.
    #   the exit is what makes the letter: the stem turns right at the
    #   baseline and sweeps UP, and Poetica's .25 row catches its tip as a
    #   17-unit run standing clear of the stem at x 204-221. The old t ended in
    #   a cubic that stopped at 0.62 S with no lift in it at all.
    T_W = d_dial("T_W", 0.97)
    T_TW = d_dial("T_TW", 1.12)
    T_TOP = d_dial("T_TOP", 1.23)     # x xh; between Poetica 1.224 and Flanker 1.184
    T_BAR = d_dial("T_BAR", 0.93)     # x xh

    @glyph('t')
    def a_t(c):
        """The stem and its exit are one movement; the bar crosses it."""
        P, u = d_frame(c, T_W); B = T_BAR
        body = d_pen([P(122, T_TOP), P(110, 0.95), P(103, 0.60), P(105, 0.25),
                      P(112, 0.085), P(140, 0.012), P(178, 0.055), P(205, 0.155),
                      P(215, 0.26)],
                     [(0.00, 18), (0.10, 46), (0.17, 56), (0.60, 58), (0.72, 56),
                      (0.80, 50), (0.88, 38), (0.95, 26), (1.00, 13)], u, tw=T_TW)
        bar = d_pen([P(11, B - 0.035), P(115, B), P(221, B + 0.035)],
                    [(0.0, 20), (0.18, 46), (0.80, 46), (1.0, 22)], u, tw=T_TW)
        return geom.ink([body, bar])

    # ---------------------------------------------------------------- THE j
    # POETICA for the shape; the DOT is the i's, by the owner's instruction, so
    # it is the FUNCTION a_i calls -- `ij_dot`, a disc lying on the pen's own
    # angle, centered HM_DOT_CY (1.343 xh) above the baseline -- and NOT
    # Poetica's, which sits at 1.35 xh and is a much steeper oval. An i and a j
    # on the same page have to wear the same dot, and until round 135 this
    # paragraph said so while the code below drew a second one.
    #   the stem: centre 214 at .97, 227 at .50, 233 at .10, 229 at -0.12,
    #   217 at -0.30, then hard left into the tail, exactly as the f's does.
    #   62 wide (Poetica 57-62, Flanker 70).
    #   the head is the module's wedge_head at .875 xh. Poetica draws its own
    #   entry as a 26-unit tip at (127, .75) rising into the stem's top, which
    #   is the shape the i already wears, so the j takes the i's rather than a
    #   second drawing of the same thing.
    #   the tail reaches x 4 at -0.55 in Poetica and x 32 in Flanker: both
    #   sweep left, so it is drawn swept. The old j stopped at -0.70 desc and
    #   wore a round PR.dot the i does not have.
    J_W = d_dial("J_W", 0.97)
    J_TW = d_dial("J_TW", 1.10)
    J_TAIL = d_dial("J_TAIL", -0.62)  # the tail's floor, x xh

    @glyph('j')
    def a_j(c):
        xh = c["xh"]; P, u = d_frame(c, J_W); B = J_TAIL
        body = d_pen([P(216, 1.00), P(224, 0.72), P(229, 0.40), P(233, 0.05),
                      P(229, -0.16), P(214, -0.36), P(168, B + 0.07), P(98, B),
                      P(38, B + 0.02), P(10, B + 0.09)],
                     [(0.00, 42), (0.08, 58), (0.30, 62), (0.50, 61), (0.60, 56),
                      (0.70, 46), (0.79, 36), (0.88, 44), (0.95, 48), (1.00, 20)],
                     u, cut0=CUT, tw=J_TW)
        xs = P(218, 0.0)[0]
        # THE i's DOT, not a second drawing of one (round 135). This was a
        # `stroke` on I_DOT_W / I_DOT_T and rendered 88 x 76 px where the i's
        # rendered 79 x 50 -- two different dots on two letters the module's
        # own comment says must wear the same one. `ij_dot` is that one.
        return geom.ink([body, wedge_head(xs, xh * 0.875), ij_dot(c, xs)])

    # ------------------------------------------------------------ THE s, round 132
    # THE SCAN CROP IS OVERRULED FOR THIS LETTER, and that has to be said out
    # loud because the brief names the scan as the reference wherever one
    # exists. Three things say this one cannot carry it, and section 6 of
    # docs/albo-aldine-targets.md already flagged the first:
    #   its ink is 0.94 xh, so either the crop clips or the declared x-height
    #     is high -- the s is the crop the doc calls borderline;
    #   the CEILING it sets is the lowest of the four letters by a wide
    #     margin. Two professional revivals of the same source score 0.303
    #     (Poetica) and 0.181 (Flanker) against it, where the o's crop lets
    #     Poetica reach 0.617;
    #   and the s as drawn scored 0.524 against it -- 1.7x better than Poetica
    #     manages. That is not a better Griffo s than Poetica's. It is a fat
    #     near-monoline letter matching a fat blob's MASS, and it scored 0.344
    #     and 0.159 against the two real faces, the worst pair in the set.
    # So this letter is drawn against Poetica for shape and Flanker for weight,
    # as the c is. Afterwards it scores 0.755 / 0.340 / 0.334 against
    # Poetica / Flanker / the scan -- the scan figure being, within noise,
    # exactly the ceiling a Poetica-shaped s can reach against that crop.
    #
    # THE PATH WAS WRONG AND THE WEIGHT WAS WRONG, both:
    #
    #   THE ARCS WERE THREE TIMES TOO THICK. At mid-width Flanker's s cuts
    #     three runs -- bottom arc 23, spine 89 (a diagonal, so ~67
    #     perpendicular), top arc 23. This letter cut 61 / 75 / 72: an almost
    #     monoline snake where the reference is a hairline-and-spine. It is why
    #     the s read heavier than every letter beside it.
    #   THE TERMINALS ARE BLOBS AND WERE FLAT SLABS. This is the one the first
    #     cut got backwards. "Thinnest 22 at .97" names the top ARC, not the
    #     end of the stroke: at its 0.90 column Flanker's top terminal is 68
    #     units tall and its row .90 carries an 89-wide run, and Poetica ends
    #     both strokes in a visible ball. A first pass read that 22 as the
    #     terminal, drew two hairlines, and every IoU fell -- scan 0.524 ->
    #     0.422, Poetica 0.344 -> 0.293. The overlay said why in one look.
    #   IT DID NOT LEAN, BY 11 DEGREES. Measured by SEARCH and not by a fitted
    #     axis, because a row-midpoint fit is meaningless on an s -- at a given
    #     height the ink can be the top arc or the bottom arc, and under that
    #     fit every real face's s reads -22 to -34 degrees, Poetica's and
    #     Flanker's included. Shear the candidate through a range and take the
    #     angle that best overlaps the reference: this s wanted **+11 degrees**
    #     of extra lean to sit on Poetica's and +12 on Flanker's, where the o
    #     wanted +2 and the c +1. It is not the build's shear (every letter
    #     here is drawn upright and sheared at the end); it is the path.
    #     Poetica's apex sits near the middle of the letter and its bottom
    #     terminal reaches down to the baseline and far left, so the top of
    #     the s is carried right of the bottom. This one had the apex at 0.20
    #     of the width and the bottom terminal 14% of the x-height off the
    #     ground. After: **+0** against Poetica. Flanker still asks +10, and
    #     that is Flanker's own s -- it leans 5 degrees further than its o
    #     where Poetica's leans like its o.
    #   IT WAS ON THE FAMILY'S PEN. `pen_widths` floored at 0.30 S, so the
    #     hairline could not go below 20 units and the pen decided the rest.
    #
    # So both the path and the width are keyed to the reference AT EACH PLACE
    # ON THE STROKE, the a's method. The key positions are found by LOCATING
    # each control point on the resampled path rather than by guessing a t for
    # it: the six segments are nothing like equal in length, and a hand-written
    # t puts the spine's weight somewhere the spine is not.
    S_W = float(os.environ.get("ALBO_ALD_S_W", 183.0))      # the letter's width, units
    S_WT = float(os.environ.get("ALBO_ALD_S_WT", 0.95))     # scales every key
    S_APEX = float(os.environ.get("ALBO_ALD_S_APEX", 0.46))   # the top arc's apex, x w
    S_TAIL_X = float(os.environ.get("ALBO_ALD_S_TAILX", 0.03))  # the bottom terminal, x w
    S_TAIL_Y = float(os.environ.get("ALBO_ALD_S_TAILY", 0.06))  # x xh
    S_HEAD_Y = float(os.environ.get("ALBO_ALD_S_HEADY", 0.86))  # the top terminal, x xh
    S_UL = float(os.environ.get("ALBO_ALD_S_UL", 0.22))       # the upper-left flank, x w
    S_LR = float(os.environ.get("ALBO_ALD_S_LR", 0.87))       # the lower-right turn, x w
    # ROUNDED, like the c's -- both references end this stroke in a ball and a
    # `stroke` can only end in a flat or sheared face, which on a 60-unit
    # terminal reads as a cut corner.
    S_CAP0 = float(os.environ.get("ALBO_ALD_S_CAP0", 1.00))   # top terminal, x half its width
    S_CAP1 = float(os.environ.get("ALBO_ALD_S_CAP1", 0.50))   # bottom terminal
    # WIDTH AT EACH PLACE, as (control point, fraction toward the next one,
    # units). The two terminals and the spine are the thicks; the two arcs
    # between them are the hairlines. Flanker at its 0.50 column: bottom arc
    # 23, spine 89 (a diagonal, ~67 perpendicular), top arc 23.
    # The terminal's width is HELD across the length the round cap trims away
    # (0.32 of the first segment, 0.12 of the last), so the ball is a swelling
    # of the stroke and not a lollipop on the end of it. Without that hold the
    # width has already fallen to the arc's hairline by the time the cap is
    # placed, and both terminals read as discs stuck on -- visible in the
    # overlay long before the number moved.
    # ROUND 133, owner: "match the s to poetica so the word image reads
    # better". Fitted key by key against the Poetica overlay -- IoU 0.724 ->
    # 0.806, which is well past the ceiling two references reach against each
    # other (0.22-0.46). What moved: the SPINE came down (75 -> 51 at its
    # middle) and the LOWER ARC came up (24 -> 42, and 50 -> 74 into the
    # bottom terminal), so the letter's weight sits lower and its diagonal is
    # no longer the heaviest thing in it. That is the difference the word
    # image was showing: a top-heavy s pulls the eye up out of the line.
    S_KEYS = [(0, 0.00, 56.0), (0, 0.32, 56.0), (0, 0.70, 44.0), (1, 0.00, 22.0),
              (2, 0.00, 52.0), (2, 0.50, 51.0), (3, 0.00, 61.0), (3, 0.60, 30.0),
              (4, 0.00, 16.0), (4, 0.60, 42.0), (4, 0.88, 74.0), (5, 0.00, 60.0)]
    if os.environ.get("ALBO_ALD_S_KEYS"):   # "0:0:62|0:0.5:26|..." -- for the fitter
        S_KEYS = [tuple(float(v) for v in kv.split(":"))
                  for kv in os.environ["ALBO_ALD_S_KEYS"].split("|")]

    @glyph('s')
    def a_s(c):
        xh = c["xh"]; u = xh / 429.0; x = S * 0.7; w = S_W * _w(c)
        P = [(x + w * 0.92, xh * S_HEAD_Y), (x + w * S_APEX, xh * 0.98), (x + w * S_UL, xh * 0.62),
             (x + w * 0.86, xh * 0.40), (x + w * S_LR, xh * 0.08),
             (x + w * S_TAIL_X, xh * S_TAIL_Y)]
        p = geom.resample(catmull(P, tension=0.5))
        n = len(p) - 1
        def at(q):
            return min(range(n + 1), key=lambda j: (p[j][0] - q[0]) ** 2 + (p[j][1] - q[1]) ** 2) / n
        ts = [at(q) for q in P]
        keys = []
        for i, f, wv in S_KEYS:
            i = int(i); t0 = ts[i]; t1 = ts[i + 1] if i + 1 < len(ts) else 1.0
            keys.append((t0 + (t1 - t0) * f, wv * u * S_WT))
        wf = widths(keys); ws = [wf(i / n) for i in range(n + 1)]
        i0, r0 = cs_round_end(p, ws, True, S_CAP0)
        i1, r1 = cs_round_end(p, ws, False, S_CAP1)
        q, qw = p[i0:i1 + 1], ws[i0:i1 + 1]; m = len(q) - 1
        parts = [stroke(q, lambda t: qw[min(m, int(round(t * m)))],
                        cut0=None if r0 else CUT, cut1=None if r1 else CUT, raw=True)]
        if r0: parts.append(PR.dot(q[0][0], q[0][1], r0))
        if r1: parts.append(PR.dot(q[-1][0], q[-1][1], r1))
        return geom.ink(parts)

    # ------------------------------------------------------------ THE g, round 132
    # IT STAYS DOUBLE-STOREY, and that is a finding rather than an assumption.
    # The brief for this round said to draw a single-storey g -- a bowl like
    # the a's, a stem, a hooked tail -- and to read the references first. Read:
    # BOTH of them are binocular, an upper bowl over a large lower loop with an
    # ear reaching right at the x-line, and they agree on it closely (Flanker's
    # rows show the two counters separated by a neck that narrows to 65 at .10
    # xh; Poetica's .03 row reads one 128-wide link between two loops). Nothing
    # in either reference, or in the 1501 page, carries a single-storey g. So
    # the structure is kept and the EXECUTION is what gets redrawn.
    #
    # WHAT WAS ACTUALLY BROKEN, which is worth naming because "two loops" was
    # not it: the upper bowl was a tall narrow oval standing off the x-line,
    # the lower loop was a small faceted ring 0.40 of the descender deep, the
    # neck was a stub that did not reach either of them (the overlay shows
    # clear white between all three pieces), there was no ear at all, and the
    # letter measured 263 units wide against the reference's 397.
    #
    # WHAT THE NUMBERS SAY (Flanker, unsheared, read at 0.06 xh intervals):
    #   UPPER BOWL  x -8..296, y 86..429 -- 304 x 343, so it is an o sitting on
    #     the x-line, not a small bowl. Its widths are an o's: flanks 70 left
    #     and 66 right (rows .58, .64), top 25 and bottom 27 (column x=144).
    #     Compare the module's own o at 69/70 and 26/25 -- the same ring.
    #   LOWER LOOP  x -46..324, y -336..-43 -- 370 x 293, WIDER THAN TALL, and
    #     that ratio is the loop's character. Thick along the upper left (left
    #     flank 70-76 at -0.44 to -0.62, top arc 68-73 by column) and thin
    #     along the lower right (right flank 34-42 at -0.56 to -0.68, bottom
    #     arc 22-26). Albo's descender is 280 against the reference's 336, so
    #     the loop is scaled to Albo's depth and keeps the 1.26 width ratio.
    #   NECK  one run from .16 xh down to -0.14, narrowest at .10 (17-83, 65
    #     wide horizontally, ~46 perpendicular) and widening as it turns: it
    #     leaves the bowl's bottom near x 97, dives LEFT to x 44 at the
    #     baseline, then swings right into the loop's top.
    #   EAR  column x=300 reads 354..415, so 61 units of ink stand 60 past the
    #     bowl's right extreme just under the x-line. Row .88 reaches 347 where
    #     the bowl reaches 296.
    #
    # WHAT SHIPPED: 0.189 against Flanker before this round, 0.658 after. It is
    # the weakest of the five and the reason is Albo's own descender: rebuilt
    # with the reference's 336 instead of Albo's 280 the same outlines score
    # 0.716, and the bottom twelfth of the comparison is 1,472 reference pixels
    # against zero of ours -- ink at a depth this family does not have. The p
    # and the q lose 0.02-0.05 the same way. Nothing here can recover it, and
    # changing `desc` to chase it would be a family decision, not a g one.
    # ROUND 135, to the owner's Griffo detail of the g (2026-09-16, a crop
    # he pasted: the upper bowl is a small near-round oval, the lower loop
    # is WIDER than the bowl and flat along its floor, the neck is short and
    # does not dive far left, the ear a short flat stroke at the x-line).
    # Bowl 187 -> 158 tall and raised; loop 182 -> 205 half-width and its
    # top lifted -43 -> -26 so it hangs off the neck rather than under it;
    # the neck's leftmost 52 -> 78 (a shallower dive) and its waist 52 -> 44.
    G_CX = float(os.environ.get("ALBO_ALD_G_CX", 144.0))      # upper bowl centre
    G_CY = float(os.environ.get("ALBO_ALD_G_CY", 268.0))
    G_RX = float(os.environ.get("ALBO_ALD_G_RX", 150.0))
    G_RY = float(os.environ.get("ALBO_ALD_G_RY", 158.0))
    G_SKEW = float(os.environ.get("ALBO_ALD_G_SKEW", -0.01))
    G_LCX = float(os.environ.get("ALBO_ALD_G_LCX", 150.0))    # lower loop centre
    G_LRX = float(os.environ.get("ALBO_ALD_G_LRX", 205.0))    # 185 at the reference's depth, scaled to Albo's 280
    G_LTOP = float(os.environ.get("ALBO_ALD_G_LTOP", -20.0))  # the loop's top
    G_SKEW_L = float(os.environ.get("ALBO_ALD_G_SKEW_L", 0.07))
    G_EAR_X = float(os.environ.get("ALBO_ALD_G_EAR_X", 350.0))  # the ear's right tip
    G_EAR_T = float(os.environ.get("ALBO_ALD_G_EAR_T", 52.0))   # its thickness
    G_EAR_Y = float(os.environ.get("ALBO_ALD_G_EAR_Y", 0.84))   # the tip's height, x xh
    G_NECK_L = float(os.environ.get("ALBO_ALD_G_NECK_L", 78.0))  # how far LEFT the neck dives
    G_NECK_R = float(os.environ.get("ALBO_ALD_G_NECK_R", 208.0))  # where it enters the loop
    G_NECK_W = float(os.environ.get("ALBO_ALD_G_NECK_W", 50.0))   # its waist
    G_RING = [(0, 66), (45, 46), (90, 25), (135, 50), (180, 70), (225, 35), (270, 27), (315, 38)]
    G_LRING = [(0, 50), (45, 62), (90, 70), (135, 74), (180, 72), (225, 58), (270, 24), (315, 34)]
    if os.environ.get("ALBO_ALD_G_RING"):
        G_RING = [(float(a), float(w)) for a, w in
                  (kv.split(":") for kv in os.environ["ALBO_ALD_G_RING"].split(","))]
    if os.environ.get("ALBO_ALD_G_LRING"):
        G_LRING = [(float(a), float(w)) for a, w in
                   (kv.split(":") for kv in os.environ["ALBO_ALD_G_LRING"].split(","))]

    @glyph('g')
    def a_g(c):
        """The Aldine binocular g: an o on the x-line, a neck that dives left
        through the baseline, a wide shallow loop under it, and an ear. See
        the block above for where every number comes from."""
        xh = c["xh"]; u = xh / A_UNIT; x0 = S * 0.6; dsc = c["desc"]
        up = keyed_ring(x0 + G_CX * u, G_CY * u, G_RX * u, G_RY * u, G_RING,
                        k=A_K, skew=G_SKEW, unit=u)
        lt = G_LTOP * u; lb = -dsc - OVER * 0.4
        lo = keyed_ring(x0 + G_LCX * u, (lt + lb) / 2.0, G_LRX * u, (lt - lb) / 2.0,
                        G_LRING, k=A_K, skew=G_SKEW_L, unit=u)
        # the neck: out of the bowl's bottom at x 97, left to x 44 on the
        # baseline, then right into the loop's top. Widths are the run widths
        # taken perpendicular -- 46 at the waist, 58 where it enters the loop.
        nk = stroke(catmull([(x0 + (G_CX + G_SKEW * -G_RY - 8) * u, (G_CY - G_RY) * u + 10 * u),
                             (x0 + G_NECK_L * u, 46 * u), (x0 + (G_NECK_L - 6) * u, 4 * u),
                             (x0 + (G_NECK_L + 56) * u, -40 * u), (x0 + G_NECK_R * u, lt - 43 * u)], tension=0.5),
                    widths([(0.0, 56 * u), (0.42, G_NECK_W * u), (1.0, 64 * u)]))
        # the ear: a short flat stroke off the bowl's top right, at the x-line
        ear = stroke([(x0 + (G_CX + G_RX * 0.55) * u, xh * 0.96),
                      (x0 + G_EAR_X * u, xh * G_EAR_Y)],
                     widths([(0.0, G_EAR_T * u * 1.10), (1.0, G_EAR_T * u * 0.80)]), cut1=CUT)
        return geom.ink([up, lo, nk, ear])

    def _diag(p0, p1, w0, w1):
        """UNUSED since round 132 -- v w x z k were its only callers and all
        five are drawn on the pen now (`d_pen` below). Left in place rather
        than deleted: it is a straight two-point stroke with a declared width
        at each end, which is the right primitive for a letter that really is
        two straight lines, and deleting it while another letter is being
        re-cut in this file is a collision for no gain."""
        return stroke([p0, p1], widths([(0.0, S * w0), (1.0, S * w1)]), cut0=CUT, cut1=CUT)

    # ---------------------------------------------------------------- THE v
    # POETICA for the shape and the proportion, FLANKER for the weight.
    #   322 x 446 (w/h 0.72). Flanker's v is 449 wide (w/h 1.03) -- half again
    #   as wide -- and Poetica's is taken, because the shape reference is
    #   Poetica and because Albo's own n u o e currently measure 348 353 327
    #   229, so a 449-wide v would be wider than this alphabet's n.
    #   the ENTRY and the thick downstroke are ONE stroke: the pen lands at
    #   (5, .755), sweeps up-right to the top at (76, 1.0), turns and comes
    #   down. Poetica's .75 row catches the entry's tip as an 11-unit run at
    #   x 0-11, clear of the body.
    #   the downstroke's centre: 109 at .75, 138 at .50, 161 at .25, 174 at
    #   .10 -- so it STEEPENS as it falls (0.27 dx/dy, then 0.22, then 0.20),
    #   and its width is 64/57/58 horizontal = 62/55/56 perpendicular. Drawn
    #   at 68 in the body, which is Flanker's 70 less the sliver a 13-degree
    #   lean takes back.
    #   the thin rise: 227 at .25, 276 at .50, 294 at .75, 22-28 wide.
    #   the TERMINAL is a ball that bulges LEFT: .75 is 268-320, .90 is
    #   236-315 (79 wide) and .97 is 246-298, so the stroke reaches its
    #   rightmost below the ball and the ball turns back over it. Flanker does
    #   the same thing (its .90 is 228-354 at 126 wide, .97 75 wide), so this
    #   is not a Poetica flourish and it is drawn.
    V_W = d_dial("V_W", 1.00)
    V_TW = d_dial("V_TW", 1.12)
    V_VX = d_dial("V_VX", 176.0)      # the vertex, units from the left ink edge

    @glyph('v')
    def a_v(c):
        P, u = d_frame(c, V_W); X = V_VX
        thick = d_pen([P(5, 0.755), P(32, 0.90), P(76, 0.95), P(109, 0.75),
                       P(138, 0.50), P(161, 0.25), P(X - 4, 0.07), P(X, -0.018)],
                      [(0.00, 22), (0.10, 48), (0.24, 68), (0.70, 66),
                       (0.90, 52), (1.00, 30)], u, tw=V_TW)
        thin = d_pen([P(X, -0.018), P(205, 0.12), P(232, 0.27), P(272, 0.50),
                      P(296, 0.68), P(302, 0.795), P(290, 0.885)],
                     [(0.00, 30), (0.15, 24), (0.55, 25), (0.72, 32),
                      (0.88, 44), (1.00, 48)], u, tw=V_TW)
        ball = d_ball(P, u, 274, 0.895, 32 * V_TW)
        return geom.ink([thick, thin, ball])

    # ---------------------------------------------------------------- THE w
    # The v twice, with the middle apex SHORT of the x-line and the two inner
    # strokes merging well below it -- which is what Poetica's rows say and
    # what no pair of straight diagonals can produce:
    #   513 x 446 (Flanker 655). At .50 there are FOUR runs -- 108-165 (57),
    #   227-249 (22), 297-357 (60), 454-484 (30) -- alternating thick, thin,
    #   thick, thin exactly as targets section 2 records for Flanker
    #   ("at .10 the w shows four strokes alternating 68, 50, 69, 50").
    #   at .75 only THREE runs survive (0-11, 78-142, 255-327, 458-512): the
    #   inner thin and the second thick have already merged, because the
    #   second thick is 60 wide and closes the gap long before the apex. The
    #   apex itself falls between .90 (one 37-unit run at 275-312) and .97
    #   (no middle run at all), so it is drawn at 0.95.
    #   vertex 1 at 166, vertex 2 at 368, both at -0.04.
    W_W = d_dial("W_W", 1.02)
    W_TW = d_dial("W_TW", 1.10)
    W_APEX = d_dial("W_APEX", 0.96)   # the middle apex's height, x xh

    @glyph('w')
    def a_w(c):
        P, u = d_frame(c, W_W); A = W_APEX
        thick = [(0.00, 22), (0.10, 48), (0.24, 68), (0.70, 64), (0.90, 50), (1.00, 30)]
        thin = [(0.00, 30), (0.15, 24), (0.55, 25), (0.72, 32),
                (0.88, 44), (1.00, 48)]
        return geom.ink([
            d_pen([P(5, 0.755), P(32, 0.90), P(77, 0.95), P(110, 0.75), P(136, 0.50),
                   P(156, 0.25), P(164, 0.07), P(166, -0.022)], thick, u, tw=W_TW),
            # the inner rise stops at the apex, so it keeps the hairline all
            # the way up and never grows the v's terminal
            d_pen([P(166, -0.022), P(190, 0.12), P(205, 0.25), P(240, 0.50),
                   P(268, 0.75), P(286, A)],
                  [(0.0, 32), (0.20, 24), (0.75, 26), (1.0, 32)], u, tw=W_TW),
            d_pen([P(288, A), P(300, 0.75), P(327, 0.50), P(356, 0.25),
                   P(366, 0.07), P(368, -0.022)],
                  [(0.00, 30), (0.12, 52), (0.30, 64), (0.75, 62),
                   (0.92, 48), (1.00, 30)], u, tw=W_TW),
            d_pen([P(368, -0.022), P(396, 0.12), P(421, 0.25), P(455, 0.48),
                   P(478, 0.655), P(484, 0.775), P(472, 0.865)],
                  thin, u, tw=W_TW),
            d_ball(P, u, 456, 0.875, 32 * W_TW)])

    # ---------------------------------------------------------------- THE x
    # The letter with NO vertical stem (targets section 6), so its `vert med`
    # of 23 is the HAIRLINE and not a stem -- read `rng`.
    #   390 x 446 in Poetica, 434 in Flanker: the one letter of these nine
    #   where the two references nearly agree on width, so there is nothing to
    #   choose between them.
    #   the THICK runs upper-left to lower-right, which is the pen's
    #   downstroke: its centre is 140 at .75, 193 at .50, 246 at .25 -- 0.49
    #   dx/dy -- and it is 68 horizontal = 61 perpendicular, exactly the
    #   figure targets section 2 quotes for Flanker ("the x's thick diagonal
    #   runs 70 horizontally but is 61 perpendicular").
    #   the THIN runs the other way: 136 at .25, 233 at .75, 30 wide.
    #   FOUR terminals, all flared, and both references have all four: an
    #   entry sweeping up from (8, .755) into the thick's top, a ball on the
    #   thin's top at (305, .93), a hook under the thin's start that turns
    #   left and down (Poetica .10 19-122, .03 18-103), and a hook off the
    #   thick's foot that turns right and UP to (385, .15).
    X_W = d_dial("X_W", 1.00)
    X_TW = d_dial("X_TW", 1.00)

    @glyph('x')
    def a_x(c):
        P, u = d_frame(c, X_W)
        thick = d_pen([P(8, 0.755), P(34, 0.89), P(70, 0.95), P(105, 0.83),
                       P(140, 0.75), P(193, 0.50), P(246, 0.25), P(282, 0.09),
                       P(318, 0.018), P(356, 0.058), P(378, 0.135), P(368, 0.185)],
                      [(0.00, 24), (0.08, 52), (0.20, 66), (0.60, 62),
                       (0.80, 54), (0.90, 48), (1.00, 38)], u, tw=X_TW)
        thin = d_pen([P(80, -0.008), P(44, 0.045), P(34, 0.112), P(58, 0.172),
                      P(112, 0.235), P(184, 0.50), P(233, 0.75), P(272, 0.855),
                      P(298, 0.925), P(289, 0.965)],
                     [(0.00, 30), (0.08, 44), (0.20, 34), (0.35, 27), (0.62, 27),
                      (0.78, 40), (0.92, 64), (1.00, 54)], u, tw=X_TW)
        return geom.ink([thin, thick])

    # ---------------------------------------------------------------- THE y
    # POETICA for the shape, and FLANKER for the TAIL'S EXTENT -- the one place
    # in these nine where the two references had to be split, so it is written
    # out. Poetica's tail sweeps down and LEFT clear past the letter's own left
    # edge (its -0.55 row is 6-122, and the bbox's left edge IS the tail).
    # Flanker's does not travel at all: 202-227 at -0.12, 196-217 at -0.30,
    # 187-210 at -0.55, a straight hairline descender with a flat foot. The
    # owner's brief calls "a swash tail on the y" a chancery flourish the 1501
    # metal does not have, and says to keep the Poetica SHAPE inside Flanker's
    # EXTENT: so the tail curves left as Poetica's does and stops at x ~118 of
    # a 370-wide letter -- under the letter's own body, not under its
    # neighbour. IT COSTS IoU against Poetica, whose tail covers a large area
    # this one leaves empty, and that is the ruling working rather than a miss.
    #   the rest is Poetica: entry tip (48, .755), thick top (110, 1.0),
    #   centres 165/206/234 at .75/.50/.25 and 57-68 wide (Flanker's y thick is
    #   63); the thin right stroke 307 at .25, 334 at .50, 341 at .75 with a
    #   ball at (321, .95) that turns left over it, as the v's does.
    #   the tail is a HAIRLINE the whole way -- 34 units at -0.12 in Poetica,
    #   and targets section 2 for Flanker: "the tail is a hairline 21-25 all
    #   the way down to -326."
    #   cmp_aldine_metrics.py holds NO w/h target for the y (its row is
    #   `(None, None, ...)`, "DERIVED - no y in any scan we hold"), so the
    #   0.725 it used to print was the old drawing's own measurement and not a
    #   target. This one measures 0.451, between Poetica's 0.515 and Flanker's
    #   0.561 once Albo's shorter descender (280 against 287 and 336) is
    #   allowed for. The ledger's exit status is unchanged by these nine.
    #
    # THE COST OF THE RULING, MEASURED, because it is large and the owner
    # should be the one to spend it. Sweeping Y_TAIL_X alone:
    #
    #     Y_TAIL_X    8     40     70    118(ships)  170    230
    #     IoU      0.645  0.414  0.156    0.075     0.073  0.072
    #
    # That is not a shape score falling off; it is an ALIGNMENT FLIP.
    # `compare_xh` aligns the two letters on their LEFT INK EDGE, and in
    # Poetica the y's leftmost ink IS the tail. While the tail reaches out
    # past the entry head the two letters align on the same feature and the
    # number means something; once it stops short, Albo's leftmost becomes the
    # head and the whole letter shifts ~40 units against the reference, so
    # every stroke decorrelates at once. The shipped y's THICK STROKE, THIN
    # STROKE AND BALL match Poetica as well as the v's do (which scores 0.756
    # on the same construction) -- the 0.075 is the tail's reach and nothing
    # else, and `ALBO_ALD_Y_TAIL_X=8` is the whole change if the swash is
    # wanted.
    Y_W = d_dial("Y_W", 1.00)
    Y_TW = d_dial("Y_TW", 1.02)
    # RULED 2026-09-16: the owner took **Poetica's full swash**, shown both
    # arms in running text. So the tail runs out to 8 -- the letter's own left
    # edge -- and passes under whatever precedes it. This is the one place the
    # chancery reference is allowed to move the text lowercase, by his call;
    # the f and j descenders keep the metal's extent.
    Y_TAIL_X = d_dial("Y_TAIL_X", 8.0)     # the tail's leftmost, units
    Y_TAIL_Y = d_dial("Y_TAIL_Y", -0.62)   # its floor, x xh
    # ---------------------------------------------------------------- ROUND 135
    # THE SWOOP IS CANCELLERESCA'S. Owner 2026-09-16: *"match y lowest brush
    # stroke to the swoop of cancell."* The REACH is not in question -- his own
    # 2026-09-16 ruling above put the tail out at unit 8 and it stays there.
    # What changes is the CURVE and the TERMINAL.
    #
    # WHAT THE REFERENCE DOES, read off Cancelleresca Bastarda's y rendered at
    # a 429-unit x-height (its tail runs from the junction at -0.15 xh to ink
    # bottom at -0.99, reaching its leftmost x=1 at -0.90):
    #
    #   IT HOLDS ITS x AND WHIPS AT THE END. Normalize both axes between the
    #   junction and the leftmost point -- 94% of the DESCENT spends only 53%
    #   of the leftward travel, and the last 6% spends the other 47%. Albo's
    #   tail did the opposite: at the same normalized depths it had already
    #   travelled 0.766 / 0.600 / 0.340 of the way left where the reference is
    #   at 0.836 / 0.725 / 0.596. That is what makes Albo's read as a long flat
    #   run with a knee in it and the reference's as a plunge.
    #   IT IS A HAIRLINE UNTIL THE VERY END -- a dead-constant 26 units from
    #   -0.50 to -0.82, where Albo's ran 31 / 35 / 43 / 52 / 58 and thickened
    #   the whole way down.
    #   IT ENDS IN A ROUND DROP, not a cut. The stroke swells to about 56 units
    #   -- 2.2 x the hairline -- over the last stretch and closes as a rounded
    #   lobe roughly 110 x 56. Albo's ended in a squared face with an upward
    #   flick, which is the shape the old last point (TX, TY+0.055) drew.
    Y_TAIL_W = d_dial("Y_TAIL_W", 26.0)    # the hairline, units -- the reference's
    Y_TAIL_DROP = d_dial("Y_TAIL_DROP", 27.0)   # the terminal drop's radius, units

    @glyph('y')
    def a_y(c):
        """The v's two strokes, with the RIGHT one carrying on past the
        baseline into the tail -- which is the construction both references
        show, and why the tail is a hairline: it is the thin stroke."""
        P, u = d_frame(c, Y_W); TX = Y_TAIL_X; TY = Y_TAIL_Y
        thick = d_pen([P(48, 0.755), P(72, 0.89), P(110, 0.95), P(140, 0.86),
                       P(165, 0.75), P(206, 0.50), P(234, 0.25), P(250, 0.10),
                       P(256, 0.02)],
                      [(0.00, 22), (0.10, 48), (0.22, 66), (0.70, 62),
                       (0.90, 50), (1.00, 36)], u, tw=Y_TW)
        W = Y_TAIL_W
        # ONE CURVE, NOT A SERPENTINE (owner 2026-09-16: "make both Y and y
        # have a single curve on their strokes, not serpentine ones"). The
        # round-135 path held x through the baseline and then whipped left
        # -- an inflection at -0.05, which read as an S. The tail is now one
        # arc of one sign of curvature from the ball to the drop.
        tail = d_pen([P(322, 0.885), P(336, 0.825), P(341, 0.74),
                      P(331, 0.50), P(306, 0.25), P(276, 0.05), P(244, -0.15),
                      P(210, -0.32), P(172, -0.46), P(128, -0.55),
                      P(TX + 26, TY)],
                     [(0.00, 48), (0.05, 44), (0.13, 34), (0.35, 30),
                      (0.55, W), (0.76, W), (0.86, W * 1.40), (1.00, W * 2.1)],
                     u, tw=Y_TW)
        ball = d_ball(P, u, 308, 0.895, 32 * Y_TW)
        # THE DROP AT THE TAIL'S END. A `stroke` closes on a FLAT face, which
        # on a 55-unit terminal reads as an angular flag -- the same reason the
        # v w y's rising hairline carries `d_ball` rather than more width.
        # It is an OVAL LYING ALONG THE STROKE, not the pen's own disc: the
        # tail's last design segment runs 7.7 degrees below horizontal, so a
        # blob at the pen's 24 degrees stands across it and leaves a shelf on
        # the top edge -- which is exactly what the first cut of this rendered.
        drop = d_ball(P, u, TX + 14.0, TY - 0.004, Y_TAIL_DROP * Y_TW,
                      squash=1.55, deg=-8.0)
        return geom.ink([thick, tail, ball, drop])

    # ---------------------------------------------------------------- THE z
    # The x's mirror image, and the letter whose thick and thin are the way
    # round a reader does not expect: the BARS are the thick strokes and the
    # DIAGONAL is the hairline, because the z's diagonal runs down to the LEFT,
    # along the pen's own edge (targets section 2, and section 6 again: the z
    # has no vertical stem, so its `vert med` of 25 is the diagonal).
    #   343 x 442 (Flanker 371).
    #   the top bar: 33-264 at .90, rising to the right -- its right end is at
    #   .97 and its left is not, so the bar climbs about 0.06 xh across the
    #   letter. Its left end drops into a curved entry reaching (0, .755).
    #   the diagonal: centre 212 at .75, 152 at .50, 89 at .25, so 0.57 dx/dy,
    #   37 horizontal = 32 perpendicular.
    #   the bottom bar: one run 16-310 at .03, and a flick lifting off its
    #   right end to (343, .115) -- Poetica's .10 row catches that flick alone
    #   at 317-343.
    # ---------------------------------------------------------------- ROUND 135
    # THE BARS RIBBON. Owner 2026-09-16: *"match z to poetica, specifically the
    # slight ribboning of the horizontal strokes."* A ribbon is two things at
    # once and both were measured, column by column at a 429-unit x-height --
    # the vertical extent at each x, which for a near-horizontal stroke is its
    # thickness, and the two EDGES separately, which is where the undulation
    # lives.
    #
    #   THE WIDTH SWELLS AND EASES. Poetica's top bar, normalized over its own
    #   run (peak = 1.00): 0.05 at the tip, 0.37 / 0.48 / 0.63 / 0.77 / 0.90
    #   climbing, 1.00 held from 0.56 to 0.66, then 0.98 / 0.95 / 0.88 to the
    #   junction. Albo's was 0.24 / 0.69 / 0.82 / 0.90 / 0.96 / 0.97 / 1.00 /
    #   1.00 / 0.99 / 0.97 / 0.96 -- at full weight within a twentieth of its
    #   length and flat from there. A slab, not a ribbon. Its bottom bar was
    #   the same: a dead 67 units from x80 to x200 where Poetica tapers 62 ->
    #   15 over its right half.
    #   THE EDGES ARE NOT PARALLEL. Poetica's top bar CRESTS -- its centerline
    #   runs 0.855 / 0.899 / 0.908 / 0.902 / 0.892 / 0.889 across the letter,
    #   up to a crest at 0.56 of its length and then DOWN. Albo's rose
    #   monotonically, 0.840 / 0.877 / 0.889 / 0.898 / 0.907 / 0.912. And
    #   Poetica's bottom bar SAGS -- 0.050 / 0.034 / 0.0245 / 0.0305 / 0.0525 /
    #   0.1025, a dip at 0.55 of its length before the flick -- where Albo's
    #   climbed 0.035 / 0.042 / 0.049 / 0.063 / 0.086 / 0.1235 all the way.
    #
    # THE PEAK IS NOT TOUCHED. Poetica's bar is 12% lighter than Albo's at its
    # thickest (60 units against 68) and the whole letter is lighter with it,
    # but the ask was the ribboning and this family's color is set against
    # Flanker, not Poetica. Only the SHAPE of the profile is taken.
    #
    # MEASURED AFTER, top bar by column against Poetica's: 30/36/36/44/51/55/
    # 59/62/60/59/56 against 22/29/38/46/54/58/60/60/59/56/53 at x 70..270 --
    # the swell and the ease, within about 3 units through the body. Its top
    # edge crests at 0.979 at x210 and falls to 0.944 at x310, where Poetica
    # crests 0.977 at x190 and falls to the same 0.944. The bottom bar's
    # center sags 0.046 -> 0.026 -> 0.101 against Poetica's 0.050 -> 0.025 ->
    # 0.103, and its thickness tracks within 2 units from x130 to x340. IoU
    # against Poetica **0.710 -> 0.834**, the largest single gain in the round.
    Z_W = d_dial("Z_W", 1.03)
    Z_TW = d_dial("Z_TW", 1.12)
    Z_DIAG = d_dial("Z_DIAG", 27.0)   # the diagonal's width, units

    @glyph('z')
    def a_z(c):
        P, u = d_frame(c, Z_W); D = Z_DIAG
        top = d_pen([P(8, 0.755), P(26, 0.855), P(64, 0.902), P(126, 0.928),
                     P(196, 0.910), P(234, 0.922), P(268, 0.972)],
                    [(0.00, 14), (0.05, 20), (0.17, 26), (0.23, 34),
                     (0.30, 41), (0.36, 48), (0.43, 52), (0.50, 54),
                     (0.56, 54), (0.61, 53), (0.67, 50), (0.76, 45),
                     (0.90, 35), (1.00, 26)], u, tw=Z_TW)
        diag = d_pen([P(258, 0.95), P(212, 0.75), P(152, 0.50), P(89, 0.25),
                      P(48, 0.09), P(32, 0.012)],
                     [(0.00, D * 1.45), (0.12, D * 1.09), (0.50, D),
                      (0.88, D * 1.15), (1.00, D * 1.52)], u, tw=Z_TW)
        # the bottom bar's left end HOOKS UP FROM UNDER THE LINE -- Poetica's
        # tip centers at -0.022 xh and is at +0.019 twenty units later. Without
        # that entry the raised left end of the sag leaves a step where the
        # diagonal's foot arrives, which is what the first cut of this drew.
        # ITS x IS PINNED BY THE LETTER'S WIDTH, not by the reference's tip:
        # at design 4 the entry reached 11 units left of the diagonal's foot
        # and made the whole z 373 units wide against Poetica's 353 and this
        # letter's own 356, which `compare_xh` aligns on -- IoU 0.633. At 18
        # the foot is still the leftmost ink, the letter measures 359, and the
        # same comparison reads 0.834. Dropping the tip to -0.022 to close the
        # last 4 units of notch under the foot puts it proud on the left again
        # and costs 0.03; the notch stays, and at 27 px it is a quarter pixel.
        bot = d_pen([P(18, -0.010), P(46, 0.046), P(90, 0.058), P(180, 0.034),
                     P(262, 0.022), P(312, 0.054), P(340, 0.112)],
                    [(0.00, 14), (0.17, 40), (0.28, 50), (0.42, 55),
                     (0.56, 55), (0.64, 53), (0.72, 48), (0.81, 38),
                     (0.88, 27), (0.97, 16), (1.00, 13)], u, tw=Z_TW)
        return geom.ink([top, diag, bot])

    # ---------------------------------------------------------------- THE k
    # POETICA for the shape, and this is the letter where that choice is a
    # choice: FLANKER'S k IS THE LOOPED ONE -- its arm leaves the stem at .95,
    # curves right and comes BACK to the stem at .45, closing a bowl (its .90
    # row shows three runs, its .50 one merged run 199 wide). Poetica's arm is
    # open: it rises from the stem at ~.53 and ends in a ball at (292, .99),
    # with the leg leaving the same junction. The owner's brief names "a looped
    # k" as the kind of chancery mannerism not to move the text lowercase, and
    # Poetica is the shape reference, so the open arm is drawn.
    #   428 x 746 in Poetica, 441 x 760 in Flanker -- the two agree.
    #   the stem takes `st(head=True)`, the same call b d h l take, so the four
    #   ascenders of this module cannot drift apart. Poetica's is 59 wide and
    #   Flanker's 70; the shared call draws S = the weight axis.
    #   the arm: 201 at .75, 222 at .90, ball 81 wide at .90 (247-328).
    #   the leg: 270 at .25, 317 at .10, then a flick turning right and UP to
    #   (428, .08) -- Poetica's .03 run is 299-416, 117 wide, because the
    #   stroke is nearly horizontal there.
    #
    # THE k's SCORE IS CAPPED BY TWO SHARED THINGS, neither of them this
    # letter's to change, and it is the only one of the nine that does not
    # clear Flanker's own 0.448 against Poetica. Clip every row ABOVE the
    # x-line out of the comparison and the same drawing scores 0.519 against
    # 0.386 for the whole glyph -- so a third of the shortfall is the
    # ascender region alone. Both causes are `st(x, 0, c["asc"], head=True)`,
    # the call b d h l also make:
    #   * ALBO'S ASCENDER IS THE TALLEST of the three. The k's ink tops at 781
    #     (1.82 xh) where Poetica's is 724 (1.69) and Flanker's 751 (1.75).
    #   * THE GENERIC HEAD IS SHORT. `st`'s reaches 52 units left of the stem
    #     centre; Poetica's k head reaches 125, and it is the letter's leftmost
    #     ink, so left-edge alignment puts Albo's whole right side ~70 units
    #     inboard of the reference's. (`wedge_head`, the measured Aldine head
    #     the i and u wear, reaches LESS far left, not more -- it is -30%/+70%
    #     about the stem -- so it is not the fix either.)
    # Reported rather than worked around: drawing the k its own head would
    # make one ascender disagree with the other four on the same page, which
    # is worse than the number.
    K_W = d_dial("K_W", 1.03)
    K_TW = d_dial("K_TW", 1.08)
    K_STEM_X = d_dial("K_STEM_X", 137.0)   # the stem's centre, units
    K_JOIN = d_dial("K_JOIN", 0.52)        # where the arm and leg leave it, x xh

    @glyph('k')
    def a_k(c):
        P, u = d_frame(c, K_W); J = K_JOIN
        arm = d_pen([P(150, J + 0.02), P(196, 0.60), P(238, 0.70), P(270, 0.79),
                     P(286, 0.885), P(292, 0.955)],
                    [(0.00, 60), (0.18, 44), (0.45, 40), (0.70, 48),
                     (0.88, 64), (1.00, 52)], u, tw=K_TW)
        leg = d_pen([P(152, J), P(212, 0.40), P(250, 0.28), P(290, 0.15),
                     P(322, 0.05), P(360, 0.01), P(398, 0.05), P(414, 0.115)],
                    [(0.00, 62), (0.15, 58), (0.55, 58), (0.75, 52),
                     (0.88, 40), (0.96, 30), (1.00, 22)], u, tw=K_TW)
        return geom.ink(st(P(K_STEM_X, 0.0)[0], 0, c["asc"], head=True) + [arm, leg])


    # ------------------------------------------------------------------ CAPS
    # A CAPITAL'S DIAL MAY NOT SHARE A NAME WITH A LOWERCASE ONE, and there is
    # a gate for it at the foot of this section rather than a rule in a comment.
    # Round 135 shipped five collisions in one edit -- S_W, Z_W, Z_DIAG,
    # K_JOIN and Q_RX were already the lowercase s, z, k and q's own dials, and
    # every letter here is registered AFTER those, so the capital's assignment
    # silently re-pointed the lowercase letter. The `s` went from 245 units wide
    # to 137 and rendered as a stem with two blobs -- a different glyph, in a
    # round whose brief said "no lowercase". Nothing failed: the build
    # succeeded, the capitals were correct, `cmp_cap_weight.py` stayed green
    # (it measures capitals), and the only thing that said so was a word
    # rendered at 54 px where "Verso" read "Verio". A comment asking the next
    # editor to check would not have caught it; this does. Capital dials
    # therefore carry a CAP_ prefix, and the gate proves it rather than trusting
    # it.
    _PRE_CAPS = {k: v for k, v in list(globals().items()) if k[:1].isupper()}

    # THE EIGHT THAT A REAL ITALIC RE-CUTS.
    #
    # docs/albo-italic-capitals.md measured 17 roman/italic pairs and ranked
    # every capital by how far its italic departs from a sheared roman
    # (round 104's IoU test). Eighteen of the twenty-six want nothing but the
    # 5% narrowing, which build.py now applies to all of them. These eight are
    # the ones the measurement says are genuinely DRAWN AGAIN:
    #
    #     N 0.439   H 0.475   Q 0.552   G 0.577
    #     V 0.590   A 0.591   S 0.597   U 0.618
    #
    # (For scale: a pure oblique scores 1.00 and real italic LOWERCASE scores
    # 0.31-0.43. So these sit between -- re-cut, but nothing like as far as the
    # lowercase goes.)
    #
    # They are built on the same nib, the same brush entry and the same bowed
    # stem as the lowercase, because the point of re-cutting a capital for an
    # italic is that it should look written by the hand beside it. Their widths
    # are solved by aldine_autofit against the reference italics, the same way
    # every lowercase letter was.
    # ROUND 134: STRAIGHT. Owner: "there is a pervasive issue of bulging with
    # a and H and other letters." The H's and N's stems were bowed inward by
    # 0.45 x S at mid-height -- both edges curving, which the eye reads as a
    # belly whatever the width does. The metal does not do it: Flanker's H
    # stem is 116 px wide a fifth of the way up and 116 px at the slab, its
    # centre on one line; the macro's i is 6-8 px the whole way down. The bow
    # was round 127's idea for the a's stem, carried to the capitals in
    # round 131, and the a lost it in round 132. Now the capitals do.
    CAP_BOW = float(os.environ.get("ALBO_ALD_CAP_BOW", 0.0))
    # 2.00, MEASURED against the capitals this module does NOT redraw. CAP_W
    # is the NIB's thick and the nib takes most of it back on a near-vertical
    # stem, so the dial sits well above the width it produces: at 1.10 the H's
    # stem rendered 11 px against the untouched I and L at 22 -- half the
    # weight, and eight hairline capitals in an otherwise solid alphabet. The
    # same trap as the a's stem in round 127, and the same cure: measure the
    # rendered stroke, not the dial.
    # 1.36 -> 1.16 in round 134, when the stems went straight: a bowed stem
    # runs off the vertical for most of its length and the nib thins it
    # there, so straightening it made the H and N 18% and 15% heavier by
    # cmp_cap_weight.py. The thick comes down by the same ratio and both
    # land on their roman again.
    CAP_W = float(os.environ.get("ALBO_ALD_CAP_W", 1.16))        # the nib's thick, x CS
    # A SEPARATE WEIGHT FOR THE ROUND CAPITALS. CAP_W was solved on a
    # near-vertical STEM, where the nib gives back only a fraction of its thick
    # -- 2.00 renders 22 px there. A curve turns through every direction, so it
    # takes the nib's FULL thick somewhere, and 2.00 on the G's bowl is twice
    # the cap stem: the letter filled solid. One dial cannot serve strokes of
    # different directions, which is the same thing the a's stem taught in
    # round 127 arriving from the other side.
    CAP_W_ROUND = float(os.environ.get("ALBO_ALD_CAP_WR", 0.79))  # x CS, for G Q S U
    # CAPITALS ARE NOT AS HIGH-CONTRAST AS THE LOWERCASE. They were drawn on
    # CON_O -- arm D, 9.26:1, the o's contrast -- and it made the A's two
    # diagonals a hairline and a slab beside near-monoline roman capitals. The
    # owner saw it as weight ("AHNV are all off on weight"), and it is weight,
    # but the cause is spread rather than level: the thicks were too thick and
    # the thins too thin for the company they keep.
    CAP_CON = float(os.environ.get("ALBO_ALD_CAP_CON", 2.20))
    # THE TWO DIAGONALS OF AN A, A V OR AN N TAKE THE SAME MULTIPLIER. The
    # nib is what makes one of them thick and the other a hairline -- its width
    # follows the stroke's direction -- so a per-stroke multiplier that differs
    # between them is the pen's own contrast being overwritten by hand. Round
    # 131c had the A at 0.46 left and 0.80 right and the N's diagonal at 0.92
    # against stems at 1.00, which INVERTED the N: its diagonal came out
    # lighter than its stems, where a pen makes that stroke the heaviest in the
    # letter. One number per letter now, scaling both, and the nib keeps the
    # relation.
    A_DIAG = float(os.environ.get("ALBO_ALD_A_DIAG", 0.743))
    V_DIAG = float(os.environ.get("ALBO_ALD_V_DIAG", 0.715))
    # The N takes ONE number for both its parts, for the same reason: its
    # stems and its diagonal are the same pen at different angles, and a
    # multiplier on only one of them is a hand overriding the nib. At 0.46 on
    # the diagonal against 1.00 on the stems the letter's heaviest stroke was
    # its lightest.
    N_SC = float(os.environ.get("ALBO_ALD_N_SC", 0.776))
    G_OPEN0 = float(os.environ.get("ALBO_ALD_G_A0", 36.0))   # the arc's start, degrees
    G_OPEN1 = float(os.environ.get("ALBO_ALD_G_A1", 312.0))  # and its end -- the gap is between
    G_BAR = float(os.environ.get("ALBO_ALD_G_BAR", 0.46))    # the bar's height, x C
    G_BAR_IN = float(os.environ.get("ALBO_ALD_G_IN", 0.16))  # how far in it reaches, x rx

    # ------------------------------------------------- THE SERIFS, round 134
    # Owner 2026-09-16, looking at these eight: *"some capitals need serifs as
    # they are missing them."* He is right, and the cause is structural rather
    # than an oversight in any one letter. These eight are drawn on the nib and
    # stopped with the pen's own cut; the EIGHTEEN capitals this module does
    # not redraw come from glyphs/caps_straight.py and wear the family's
    # bracketed wedge. In NAVE, Hugh or SUGAR the two kinds stand side by side
    # and the re-cut ones read unfinished.
    #
    # WHICH CORNER GETS ONE IS THE ROMAN'S DECISION, letter by letter, and not
    # a new one taken here. Read off caps_straight.py and confirmed on a 700 px
    # render of Albo-Medium:
    #
    #   H  both stems: an OUTWARD top wedge only (left stem left, right stem
    #      right) and a two-sided foot                     g_H
    #   N  the left stem the same; the right stem keeps its outward top and
    #      has NO foot, the diagonal landing there          g_N's foot=None
    #   U  the left stem's top, the right stem's two-sided top ('right+');
    #      the bowl's foot takes none                       g_U
    #   V  a diagonal end wedge on each top terminal, outward; the baseline
    #      vertex bare                                      g_V's serif0=1/-1
    #   A  the left leg's FLAT foot (tip on the baseline, drop 0) and the
    #      right leg's outward diagonal wedge; the apex bare g_A
    #   S  the family's beak at the top terminal             g_S
    #   G  the beak at the top terminal                      g_G
    #   Q  the ring takes none and the tail ends in the pen's cut and nothing
    #      else                                             g_Q
    #
    # SO THE Q IS UNTOUCHED, deliberately: its tail already ends in `cut1=CUT`,
    # which is the whole of what the roman Q's tail does. Nothing was added to
    # it and nothing should be.
    #
    # WHERE THE REFERENCE ITALICS DISAGREE WITH THE ROMAN, the roman wins and
    # the disagreement is recorded rather than split. Rendered at 700 px and
    # looked at: Flanker Griffo Italic gives the H, N and U TWO-SIDED tops --
    # four horns on an H, not two -- and the A two-sided feet; Poetica the
    # same, in a much finer chancery hairline. Following them would make these
    # eight the odd ones out a second time, in the other direction, beside the
    # B D E I J L M T of the same font whose tops are one-sided. The two places
    # the reference IS followed are the S's lower terminal and the G's bar end,
    # and both say so where they are drawn.
    #
    # AN ITALIC SERIF IS NOT THE ROMAN'S ROTATED -- and the asymmetry is in the
    # BRACKET, not in the reach, which is the opposite of what I expected to
    # find. Measured on Flanker Griffo Italic at 1200 px (cap height 878),
    # column by column out of the slab, against the stem's own edges carried up
    # the slope:
    #
    #                reach L   reach R   bracket depth 15-20 px outside the stem
    #     H foot       113       144       LEFT 0.082 cap    RIGHT 0.047 cap
    #     H top        113       144       LEFT 0.087        RIGHT 0.076
    #     U top L      113       125       (its thin right stem: 113 / 116)
    #
    # The REACH is the same either side to within a few per cent, and the same
    # 113 px on a 117 px stem as on a 43 px one: a slab serif is a fixed length,
    # not a multiple of the stem, and the slant does not lengthen it. What the
    # slant costs is the BRACKET. At the FOOT the left horn climbs 1.7x further
    # up the stem than the right, because a right-leaning stem's left edge
    # leans AWAY from the wedge's tip and the concave bracket has further to
    # travel before it can lie along it; at the TOP the same effect is nearly
    # spent (1.15x). That is what CAP_SERIF_TRAIL carries, and it is the only
    # number here that is not the roman's.
    #
    # WHAT IT COST IN WIDTH, measured rather than assumed, as advance over the
    # letter's OWN roman (the eighteen capitals the build only shears and
    # narrows sit at 0.96-0.99 of theirs):
    #
    #        before  after        before  after
    #     A   0.985  1.118     N   0.916  1.000
    #     G   0.893  0.886     Q   0.901  0.901
    #     H   0.910  0.992     S   1.106  1.104
    #     U   0.973  1.030     V   0.941  1.043
    #
    # The H and N were the two NARROW ones and the serifs put them on their
    # roman exactly, which is the change earning itself. The A at 1.118 is the
    # one letter now visibly wider than its roman, and the cause is its own
    # FIT width dial (1.350) multiplying the wedges with everything else -- so
    # re-solving that dial is a real proposal and NOT something this round
    # takes on its own: the weights it sits beside were solved against the
    # roman capitals and hold (cmp_cap_weight, --tol 0.05, 0 off, before and
    # after). Checked and ruled out as the cause: keeping the brush taper on
    # the served ends only moves the A from 1.118 to 1.100 and the V from
    # 1.043 to 1.016, so the width is the serifs and not the un-taper.
    CAP_SERIF_TRAIL = float(os.environ.get("ALBO_ALD_CAP_TRAIL", 1.60))
    CAP_SERIF_TRAIL_TOP = float(os.environ.get("ALBO_ALD_CAP_TRAIL_TOP", 1.15))

    # ------------------------------------------------ DOUBLED, round 135
    # Owner 2026-09-16: *"for capitals, double the recently added serifs so
    # they are visible and not microserifs."* One factor on all three of a
    # wedge's dimensions -- length (its reach out of the stroke), depth (how
    # far back down the stroke's own edge the concave bracket runs) and drop
    # (how far back along the stroke the apex sits, which is the blade's
    # THICKNESS). Scaling only the length gives a longer sliver, which is the
    # fault rather than the fix.
    #
    # WHERE THE MICROSERIFS ACTUALLY WERE, measured before turning the dial
    # rather than assumed -- and the answer is NOT the one the round-134 note
    # would lead you to expect. Rendered at cap height 1000 px, the top-left
    # blade's reach LEFT of the bare stem edge with the 13-degree shear taken
    # out (a shear maps a horizontal run to a horizontal run of the same
    # length, so nothing has to be unsheared but the x of one edge):
    #
    #     depth below cap line      2    6   12   20   30   45   65   90
    #     H  re-cut                -7   15   47   31   25   13    3    1
    #     N  re-cut                 2   19   45   35   25    9    3    1
    #     I  roman-derived         -1   21   46   31   20   13    5    4
    #     K  roman-derived         -6   12   39   41   31   16    6    4
    #     L  roman-derived         -4   16   46   39   29   13    5    3
    #
    # The re-cut STEM tops were already the roman's blade to within the
    # measurement -- 45-47 px of peak reach against 39-46. What made them read
    # unfinished beside I K L is the stem they sit on: a roman cap stem carries
    # 14% entasis, so its crown widens INTO the wedge and the two read as one
    # flare, while `cstem_i` draws a parallel-sided nib stem and the same wedge
    # is a blade stuck on a post. The genuinely micro ones are the 0.4-unit
    # pieces: the S's and G's beak lips and the U's small right-stem wedge, all
    # at WL x 0.4 x WD x 0.7-ish, which is a third of the family's blade.
    #
    # So this factor lands the 0.4-unit pieces at 0.8 -- still inside the
    # family's own 1.0 unit, which is the "not bigger than the roman-derived
    # capitals" half of the brief -- and it takes the full-unit stem blades
    # past the roman's. That second half is the part the gate refuses, and the
    # gate is the owner's own: the doubled ones must read as the same family at
    # 27 px, NOT bigger. CAP_SERIF_FULL is therefore what the pieces already at
    # the family's unit get, and it is 1.0: doubling a blade that already
    # matches I K L exactly would make these eight the odd ones out a second
    # time, in the other direction, which is the trap round 134's own serif
    # note records itself falling into over Flanker's two-sided tops.
    # Both are dials, so the whole-alphabet doubling is one env var away
    # (ALBO_ALD_CAP_SFULL=2) and was built and looked at before this was set.
    CAP_SERIF_LEN = float(os.environ.get("ALBO_ALD_CAP_SLEN", 2.0))
    # RULED 2026-09-16: "yes to SFULL 2" -- every capital serif doubled, not
    # only the micro pieces. Round 135 measured the re-cut stem blades at the
    # roman's own reach (47 units against the I's 46 at depth 12) and left
    # them, shipping 1.0 and offering 2.0 as the arm he could see. He has seen
    # it: the brackets now run to a peak of 81 at depth 30 against the
    # roman-derived capitals' 46, about 1.75x, and that IS the serif family
    # now -- the eighteen letters that come from the roman are the ones that
    # will look light beside these until they follow.
    CAP_SERIF_FULL = float(os.environ.get("ALBO_ALD_CAP_SFULL", 2.0))

    def _sk(small):
        """The scale a round-134 serif takes: the doubling for the 0.4-unit
        pieces, CAP_SERIF_FULL for the ones already at the family's unit."""
        return CAP_SERIF_LEN if small else CAP_SERIF_FULL

    from ..primitives import wedge as _wedge, beak as _beak, end_wedge as _end_wedge
    from ..pen import WL, WD, DROP, FOOT as SERIF_FOOT
    from .caps_straight import BEAK_CUT as CAP_BEAK_CUT   # -28 deg: the C/G/S terminal, imported so it cannot drift from the roman's

    def _edge_back(side):
        """edge_at for wedge(): the point `dist` back along a stroke's REAL
        side polyline from its LAST point.

        wedge()'s default walks a STRAIGHT line back from the corner, which is
        right for the roman's stems and wrong for every stroke in this module:
        these stems are bowed (CAP_BOW) and the nib changes their width along
        their length, so the drawn edge is neither straight nor parallel to the
        centerline. With the default the bracket's foot lands beside the edge
        instead of on it and each serif seats with a nick. Same helper the
        figures reach for (glyphs/nines.py `_walk_back`)."""
        pts = list(side)

        def f(dist):
            rem = dist; p = pts[-1]
            for q in reversed(pts[:-1]):
                seg = math.dist(p, q)
                if seg >= rem:
                    u = rem / seg if seg else 0.0
                    return (p[0] + (q[0] - p[0]) * u, p[1] + (q[1] - p[1]) * u)
                rem -= seg; p = q
            return pts[0]
        return f

    def _stem_serifs(Lz, Rz, where, at_top):
        """The family's wedges at one end of a drawn stem. `where` is the
        ROMAN'S OWN vocabulary (primitives.stem): 'left' | 'right' | 'both' |
        'left+' | 'right+', the '+' being the small 0.4 x 0.6 wedge the other
        way that the I and the U's right stem carry -- so a call site here
        reads against g_H, g_N and g_U word for word. Sizes are the roman's
        too: a top is the family's full unit, a foot 0.85 of its length at 0.6
        of its drop (primitives.stem's own defaults)."""
        d = (0, 1) if at_top else (0, -1)
        # the stems here are drawn UPWARD, so `stroke`'s left-of-travel edge is
        # the left side; at the foot each polyline has to be walked from its
        # other end.
        edges = {-1: (Lz if at_top else Lz[::-1]), +1: (Rz if at_top else Rz[::-1])}
        main = -1 if where in ("left", "left+", "both") else +1
        sides = [main] + ([-main] if where in ("both", "left+", "right+") else [])
        out = []
        for i, sx in enumerate(sides):
            small = (where in ("left+", "right+")) and i == 1
            k = _sk(small)
            ln = WL * (0.4 if small else (1.0 if at_top else SERIF_FOOT)) * k
            dp = WD * (0.6 if small else 1.0) * k
            dr = DROP * (0.4 if small else (1.0 if at_top else 0.6)) * k
            if sx < 0: dp *= CAP_SERIF_TRAIL_TOP if at_top else CAP_SERIF_TRAIL
            e = edges[sx]
            out.append(_wedge(e[-1], d, (sx, 0), ln, dp, dr, edge_at=_edge_back(e)))
        return out

    def _cap_end_wedge(pts, w, at_start, side, scale=0.9, k=None, edge_at=None):
        """primitives.end_wedge with round 135's factor on ALL THREE of the
        wedge's dimensions.

        It cannot go through `end_wedge`: that hands `diag_wedge` the family's
        DROP as a fixed argument and offers no way to move it, so a scale
        passed down it lengthens and deepens the blade while leaving its apex
        at the old thickness -- a longer sliver. Same body otherwise, so the
        +1/-1 side convention is the roman's unchanged."""
        k = CAP_SERIF_FULL if k is None else k
        tn = geom.tangents(pts)
        d = (-tn[0][0], -tn[0][1]) if at_start else tn[-1]
        nrm = (-d[1], d[0]); sd = (nrm[0] * side, nrm[1] * side)
        P = pts[0] if at_start else pts[-1]
        A = (P[0] + sd[0] * w / 2, P[1] + sd[1] * w / 2)
        return _wedge(A, d, sd, WL * scale * k, WD * scale * k, DROP * k,
                      **({} if edge_at is None else {'edge_at': edge_at}))

    def cstem_i(x, y0, y1, bow=None, w=None, top=None, foot=None):
        """A capital's stem, bowed inward and drawn on the nib -- the italic
        stem of round 127 at cap height -- with the family's bracketed wedges
        at whichever ends carry them.

        A SERVED END DOES NOT ALSO TAPER. `nib_widths`' brush entry (ALD_TIP,
        0.62 of the body over its last 12%) is what a stroke the pen LIFTS off
        does; a stroke the pen finishes with a serif is full width into its
        bracket. Measured on Flanker Griffo Italic's H: the stem is 116 px wide
        a fifth of the way up and still 116 px where the slab meets it. Seating
        a wedge on a needle gives the bracket nothing to land on, and the
        serif reads as a crossbar stuck on a point. Built both ways and looked
        at, A V beside the untouched X at 420 px: with the taper kept the V's
        top wedges are slivers hanging off two points and the X's beside them
        are slabs; with it dropped the three terminals are the same terminal,
        which is the whole object of the round."""
        bow = CAP_BOW if bow is None else bow
        w = CAP_W if w is None else w
        p_ = catmull([(x, y0), (x + S * bow * 0.72, y0 + (y1 - y0) * 0.30),
                      (x + S * bow, y0 + (y1 - y0) * 0.55),
                      (x + S * bow * 0.55, y0 + (y1 - y0) * 0.82), (x, y1)],
                     tension=0.5)
        ws = nib_widths(p_, CS * w / S, CS * w * 0.34 / S, CAP_CON, taper=False)
        ws = [v * m for v, m in zip(ws, _taper(len(ws), ends=(foot is None, top is None)))]
        wf = widths([(i / (len(ws) - 1), S * v) for i, v in enumerate(ws)])
        solid, Lz, Rz = stroke(p_, wf, sides=True)
        parts = [solid]
        if top: parts += _stem_serifs(Lz, Rz, top, True)
        if foot: parts += _stem_serifs(Lz, Rz, foot, False)
        return geom.union(parts)

    def _flat_foot_diag(a, b, w=None):
        """The A's left leg: a nib diagonal from the baseline at `a` up to `b`,
        its bottom face cut LEVEL and the family's wedge growing horizontally
        out of the leg's left edge with its tip ON the baseline (drop 0).

        This is g_A's foot, reproduced rather than invented -- `flat_face`'s
        shear so the face lies on the baseline instead of square across a
        47-degree axis, then `wedge(Apt, (0,-1), (-1,0), WL*0.9, WD*0.9, 0)`.
        The one difference is the edge the bracket walks: the roman's leg is a
        straight line and takes wedge()'s default, while this one is a bowed
        catmull on a changing nib, so it walks the drawn edge (`_edge_back`)."""
        w = CAP_W if w is None else w
        p_ = catmull([a, ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2), b], tension=0.5)
        ws = nib_widths(p_, CS * w / S, CS * w * 0.30 / S, CAP_CON, taper=False)
        ws = [v * m for v, m in zip(ws, _taper(len(ws), ends=(False, True)))]
        wf = widths([(i / (len(ws) - 1), S * v) for i, v in enumerate(ws)])
        tn = geom.tangents(p_)[0]
        solid, Lz, Rz = stroke(p_, wf, cut0=math.atan2(-tn[0], tn[1]), sides=True)
        return geom.union([solid,
                           _wedge(Lz[0], (0, -1), (-1, 0),
                                  WL * 0.9 * CAP_SERIF_FULL,
                                  WD * 0.9 * CAP_SERIF_TRAIL * CAP_SERIF_FULL,
                                  0.0, edge_at=_edge_back(Lz[::-1]))])

    def cdiag(a, b, w=None, serif0=None, serif1=None):
        """A capital's diagonal, on the nib: its width follows its direction,
        so the two diagonals of an A or a V are NOT the same weight.

        serif0/serif1 are the roman's (primitives.diagonal): +1/-1 names the
        side taken on the normal of the direction OUT of that end. A SERVED END
        DROPS ITS PEN CUT -- the wedge's face IS the terminal, and a cut behind
        it leaves the double facet with a ledge between two faces that the
        owner had cleaned off the roman E and F (caps_straight.py's note on
        `bar`). It does not taper either, for the reason cstem_i gives."""
        w = CAP_W if w is None else w
        p_ = catmull([a, ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2), b], tension=0.5)
        ws = nib_widths(p_, CS * w / S, CS * w * 0.30 / S, CAP_CON, taper=False)
        ws = [v * m for v, m in zip(ws, _taper(len(ws), ends=(serif0 is None, serif1 is None)))]
        wf = widths([(i / (len(ws) - 1), S * v) for i, v in enumerate(ws)])
        parts = [stroke(p_, wf, cut0=None if serif0 else CUT, cut1=None if serif1 else CUT)]
        if serif0: parts.append(_cap_end_wedge(p_, wf(0.0), True, serif0))
        if serif1: parts.append(_cap_end_wedge(p_, wf(1.0), False, serif1))
        return geom.union(parts)

    @glyph('H')
    def a_H(c):
        """Serifs as g_H's: each stem's top wedge points OUTWARD only (the
        inner top corners are bare, which is the roman's cut and not Flanker's)
        and each foot is two-sided. Six in all, where a roman H has six."""
        C = c["cap"]; x0 = CS * 0.6; x1 = x0 + 0.62 * C
        bar = stroke([(x0, C * 0.54), (x1, C * 0.58)], TH_H * 1.25)
        return geom.ink([cstem_i(x0, 0, C, top='left', foot='both'),
                         cstem_i(x1, 0, C, top='right', foot='both'), bar])

    @glyph('N')
    def a_N(c):
        """Serifs as g_N's, which is the H's minus one: the RIGHT stem has no
        foot, because the diagonal arrives there and a wedge under it would be
        a serif on a junction. Flanker's italic N leaves the same corner bare,
        so roman and reference agree here."""
        C = c["cap"]; x0 = CS * 0.6; x1 = x0 + 0.66 * C
        return geom.ink([cstem_i(x0, 0, C, w=CAP_W * N_SC, top='left', foot='both'),
                         cstem_i(x1, 0, C, w=CAP_W * N_SC, top='right', foot=None),
                         cdiag((x0 + CS * 0.2, C * 0.96), (x1 - CS * 0.2, C * 0.06), N_SC)])

    @glyph('U')
    def a_U(c):
        """Serifs as g_U's: the left stem's top wedge reaching LEFT, the right
        stem's two-sided top ('right+' -- a full right wedge and the small
        0.4 x 0.6 one back the other way), and NOTHING on the bowl, which is
        one continuous stroke through the baseline and has no foot to serve.
        Flanker's italic U agrees on all three.

        This letter is drawn as ONE stroke rather than two stems and a bowl, so
        its serifs are seated on the stroke's two ENDS off `stroke(sides=True)`
        -- and the pen cuts that used to close those ends are gone, because the
        wedge's face is the terminal."""
        C = c["cap"]; x0 = CS * 0.6; x1 = x0 + 0.62 * C
        p_ = catmull([(x0, C), (x0 - S * 0.10, C * 0.42), (x0 + (x1 - x0) * 0.16, C * 0.10),
                      (x0 + (x1 - x0) * 0.52, -OVER * 0.4),
                      (x1 - (x1 - x0) * 0.12, C * 0.12), (x1, C * 0.46), (x1, C)],
                     tension=0.5)
        ws = nib_widths(p_, CS * CAP_W_ROUND / S, CS * CAP_W_ROUND * 0.28 / S, CAP_CON,
                        taper=False)
        wf = widths([(i / (len(ws) - 1), S * v) for i, v in enumerate(ws)])
        solid, Lz, Rz = stroke(p_, wf, sides=True)
        # the stroke starts DOWNWARD at the left stem, so `stroke`'s left-of-
        # travel edge is the one facing INTO the letter there and the outer
        # (left) edge is Rz; by the right stem it is travelling up and the two
        # have swapped back.
        return geom.ink([solid,
                         _wedge(Rz[0], (0, 1), (-1, 0), WL * CAP_SERIF_FULL,
                                WD * CAP_SERIF_TRAIL_TOP * CAP_SERIF_FULL,
                                DROP * CAP_SERIF_FULL,
                                edge_at=_edge_back(Rz[::-1])),
                         _wedge(Rz[-1], (0, 1), (1, 0), WL * CAP_SERIF_FULL,
                                WD * CAP_SERIF_FULL, DROP * CAP_SERIF_FULL,
                                edge_at=_edge_back(Rz)),
                         _wedge(Lz[-1], (0, 1), (-1, 0), WL * 0.4 * CAP_SERIF_LEN,
                                WD * 0.6 * CAP_SERIF_TRAIL_TOP * CAP_SERIF_LEN,
                                DROP * 0.4 * CAP_SERIF_LEN, edge_at=_edge_back(Lz))])

    @glyph('V')
    def a_V(c):
        """Serifs as g_V's: the family's diagonal end wedge (0.9 x 0.9, the
        A's and the X's) on each top terminal, reaching OUTWARD, and nothing at
        the baseline vertex -- where Flanker's and Poetica's italic V's are
        also bare, the two strokes simply closing on each other. The left
        stroke is drawn top-down so its serif is at t=0; the right is drawn UP
        from the vertex, so its serif is at t=1 and the side flips."""
        C = c["cap"]; x0 = CS * 0.5; w = 0.66 * C
        apex = (x0 + w * 0.52, -OVER * 0.3)
        return geom.ink([cdiag((x0, C), apex, V_DIAG, serif0=1),
                         cdiag(apex, (x0 + w, C), V_DIAG, serif1=-1)])

    # ROUND 135, TO POETICA. Three measured differences, at a 300 px cap with
    # the ink runs read at fixed heights and each letter shifted to its own
    # 0.50-cap left edge (so the shear, which both faces have at about the same
    # angle, cancels):
    #
    #                        0.75 cap                0.50 cap        0.08 cap
    #     Poetica     0.130-0.196  0.229-0.348   0.000-0.062 0.281-0.395   span 0.766
    #     Albo r134   0.185-0.253  0.394-0.503   0.000-0.067 0.439-0.545   span 0.933
    #
    # The A was 38% WIDER at mid-height and its legs opened faster: at 0.90 cap
    # Poetica's two legs are still one run and Albo's had already parted. That
    # is round 134's own open question -- it recorded the A at 1.118 of its
    # roman's advance, "the one letter now visibly wider than its roman",
    # named its FIT width dial of 1.350 as the cause, and left re-solving it as
    # a proposal rather than taking it. This round takes it: the drawn width
    # comes down instead, which is the same correction made where the letter is
    # rather than on a scale applied over the top of it.
    #
    # The BAR drops from 0.32 to 0.29 of the cap (Poetica's sits just under
    # three tenths) and the apex FLAG is cut to 0.45 of its reach. The flag is
    # NOT removed: Poetica's A has no entry at all, but round 134 put it there
    # because a written italic A carries one, and taking a stroke out of the
    # letter is a bigger change than the owner asked for -- "match to poetica"
    # is about what the letter DOES, and what this one does at its apex now is
    # a short entry rather than a bar reaching a full cap-stem left.
    CAP_A_W = float(os.environ.get("ALBO_ALD_CAP_A_W", 0.57))     # the letter's drawn width, x C (was 0.68)
    CAP_A_APEX = float(os.environ.get("ALBO_ALD_CAP_A_AP", 0.56))  # where the apex sits, x w
    CAP_A_BAR = float(os.environ.get("ALBO_ALD_CAP_A_BAR", 0.31))  # the crossbar's height, x C
    CAP_A_FLAG = float(os.environ.get("ALBO_ALD_CAP_A_FLAG", 0.45))  # the apex entry's reach, x round 134's

    @glyph('A')
    def a_A(c):
        """Serifs as g_A's, which serves the two BASELINE feet and leaves the
        apex to the flag. The left leg is the hairline and takes the roman's
        FLAT foot -- a wedge growing horizontally out of the leg's left edge
        with its tip ON the baseline (drop 0), off a level end face rather than
        the pen's, so a thin diagonal does not finish in a spike. The right leg
        is the stem and takes the ordinary outward diagonal wedge. Flanker
        makes both feet two-sided; the roman does not, and the roman wins."""
        C = c["cap"]; x0 = CS * 0.4; w = CAP_A_W * C
        apex = (x0 + w * CAP_A_APEX, C)
        left = _flat_foot_diag((x0, 0), apex, A_DIAG)
        right = cdiag(apex, (x0 + w, 0), A_DIAG, serif1=1)
        bar = stroke([(x0 + w * 0.16, C * CAP_A_BAR), (x0 + w * 0.84, C * (CAP_A_BAR + 0.03))],
                     TH_H * 1.20)
        # the apex flag: a real italic A carries an entry reaching LEFT
        flag = stroke([(apex[0] - CS * 1.05 * CAP_A_FLAG, C * 1.02),
                       (apex[0] + CS * 0.18, C)],
                      widths([(0.0, S * 0.30), (0.55, S * 0.72), (1.0, S * 0.50)]), cut0=CUT)
        return geom.ink([left, right, bar, flag])

    CAP_S_W = float(os.environ.get("ALBO_ALD_CAP_S_W", 0.50))   # the letter's drawn width, x C

    @glyph('S')
    def a_S(c):
        """BOTH terminals take the family's beak -- the face sheared toward the
        vertical at CAP_BEAK_CUT and a short lip hanging from its inner corner
        into the aperture (primitives.beak, 0.4 x 0.7 of the family).

        The top one is the roman's: g_S carries exactly this at its start. The
        BOTTOM one is the one place this letter follows the reference over the
        roman -- g_S finishes its lower terminal with a widening (S_BOTTOM_END
        1.30) and no beak at all, while Flanker Griffo Italic's S and Poetica's
        both hook the lower left terminal up into the mouth, and the owner's
        report is that these letters are missing serifs rather than that they
        carry the wrong ones. Rendered at 700 px beside the roman S before
        choosing."""
        C = c["cap"]; x0 = CS * 0.5; w = CAP_S_W * C
        # ROUND 135: THE LOWER BOWL IS FULLER. Poetica's S reaches 0.199 of the
        # cap left of its own 0.50-cap edge at a quarter height and round 134's
        # reached nothing at all there -- the lower bowl simply stopped short
        # and the letter finished on a flatter curve. The last three control
        # points carry the whole of that: the bowl swings wider right before it
        # turns, comes down further, and the terminal reaches back further left.
        p_ = catmull([(x0 + w * 0.92, C * 0.86), (x0 + w * 0.46, C * 1.00),
                      (x0 + w * 0.04, C * 0.80), (x0 + w * 0.34, C * 0.55),
                      (x0 + w * 0.72, C * 0.42), (x0 + w * 1.00, C * 0.18),
                      (x0 + w * 0.46, -OVER * 0.5), (x0 - w * 0.10, C * 0.17)],
                     tension=0.5)
        ws = nib_widths(p_, CS * CAP_W_ROUND / S, CS * CAP_W_ROUND * 0.26 / S, CAP_CON,
                        taper=False)
        wf = widths([(i / (len(ws) - 1), S * v) for i, v in enumerate(ws)])
        bc = math.radians(CAP_BEAK_CUT)
        # The upper terminal is primitives.beak's own case and takes it.
        # THE LOWER ONE CANNOT USE IT, and the reason is a sign: beak() seats
        # its lip on the corner `stroke` would have made with cut = -cut_deg at
        # the END (it moves P FORWARD along the tangent while stroke's cut1
        # moves that same corner BACK), so the pair leave a V notch between the
        # lip and the body -- visible at 3x on the first cut of this letter. The
        # lip is therefore built here from the corner `stroke` actually drew,
        # which is also what lets its bracket walk the real edge; the cut is
        # -bc so the aperture side of the face runs forward and the outer
        # corner is the one taken back, which is what a beak is.
        solid, Lz, Rz = stroke(p_, wf, cut0=bc, cut1=-bc, sides=True)
        tl = geom.tangents(p_)[-1]; nl = (-tl[1], tl[0])
        return geom.ink([solid,
                         _beak(p_, wf(0.0), True, CAP_BEAK_CUT,
                               lip=(0.4 * CAP_SERIF_LEN, 0.7 * CAP_SERIF_LEN)),
                         _wedge(Rz[-1], tl, (-nl[0], -nl[1]),
                                WL * 0.4 * CAP_SERIF_LEN, WD * 0.7 * CAP_SERIF_LEN,
                                0.0, edge_at=_edge_back(Rz))])

    @glyph('G')
    def a_G(c):
        """A G opens on the RIGHT, between about one and four o'clock; its bar
        comes INWARD from the right terminal, and a short stem joins the two.

        The first cut ran its arc from -34 to 250 degrees, which covers the
        right side and leaves the gap at the BOTTOM -- so the letter read as a
        broken O with a spur stuck on its flank. Compared against Pagella and
        Poetica: both open at the right, both turn their bar in toward the
        counter, and neither lets it project past the bowl.

        SERIFS, round 134: the arc's upper terminal takes the family's beak,
        which is g_G's own ending, and THE BAR'S INNER END TAKES NOTHING.

        That second half was built first and thrown away, which is worth
        recording so it is not re-proposed. At a glance Flanker Griffo Italic's
        G looks as though it finishes its bar with a two-sided slab; cropped
        and magnified 3x it is nothing of the kind -- the whole bar IS one flat
        slab of even thickness, bracketed down into the spur on both sides,
        and its ends are simply blunt. g_G's bar is the same idea with the
        family's pen cut at each end and no wedge anywhere. Built with the
        family's bar-end wedge (0.85 x 0.9, drop 0) both ways it came out a
        trumpet: this bar tapers to TH_H x 0.70 at the inner end, so a
        full-size wedge is 2.5x the thing it is finishing and its bracket eats
        a third of the bar's visible length. Roman and reference agree, so the
        pen cut stays.
        """
        C = c["cap"]; rx = 0.34 * C; ry = C / 2 + OVER * 0.4; cx = CS * 0.6 + rx
        A0, A1 = math.radians(G_OPEN0), math.radians(G_OPEN1)
        p_ = superellipse(cx, C / 2, rx, ry, A0, A1, BOWL_K)
        ws = nib_widths(p_, CS * CAP_W_ROUND / S, CS * CAP_W_ROUND * 0.30 / S,
                        CAP_CON, smooth=7)
        af = widths([(i / (len(ws) - 1), S * v) for i, v in enumerate(ws)])
        arc = stroke(p_, af, cut0=math.radians(CAP_BEAK_CUT), cut1=CUT)
        lip = _beak(p_, af(0.0), True, CAP_BEAK_CUT,
                    lip=(0.4 * CAP_SERIF_LEN, 0.7 * CAP_SERIF_LEN))
        # the terminal the arc ends on, and the bar turning in from it
        ex = cx + rx * math.cos(A1); ey = C / 2 + ry * math.sin(A1)
        by = C * G_BAR
        stem_ = stroke([(ex, ey), (ex + (cx + rx * 0.92 - ex) * 0.5, by)],
                       widths([(0.0, CS * 0.52), (1.0, CS * 0.86)]))
        bar = stroke([(cx + rx * 0.96, by), (cx + rx * G_BAR_IN, by + C * 0.012)],
                     widths([(0.0, TH_H * 1.30), (1.0, TH_H * 0.70)]), cut1=CUT)
        return geom.ink([arc, lip, stem_, bar])

    # ROUND 135: THE Q IS THE ONE THAT GOES TO PAGELLA. The owner's first list
    # put it with the Poetica eight and his second message the same day
    # (2026-09-16) moved it: the Q matches TeX Gyre Pagella Italic. Both arms
    # are drawn and the dial ships `pagella`; the Poetica arm is kept because
    # the first ruling was real and reversing this is one env var.
    CAP_Q_REF = os.environ.get("ALBO_ALD_CAP_Q_REF", "pagella").lower()
    # AND THE RING IS WIDER. Pagella's ring spans 0.986 of the cap against round
    # 134's 0.839, measured the same way -- 17% -- so the letter read narrow
    # beside its own reference whatever the tail did.
    # The FIT weight moved with it, 0.492 -> 0.880: a wider ring and a tail that
    # has left the counter both take ink out of area-over-length, and then the
    # tail's join back onto the ring puts some of it back -- the first cut of
    # this letter started the tail BELOW the ring and the glyph was two pieces.
    # Each of those three is worth more than the 0.05 tolerance on its own.
    CAP_Q_RX = float(os.environ.get("ALBO_ALD_CAP_Q_RX", 0.41))   # the ring's x radius, x C (was 0.35)
    Q_AXIS = os.environ.get("ALBO_ALD_Q_AXIS", "nib").lower()   # 'bowl' = the pre-150 family profile
    Q_INK = float(os.environ.get("ALBO_ALD_Q_INK", 1.13))       # x the nib's widths
    Q_DROP = float(os.environ.get("ALBO_ALD_Q_DROP", 0.045))    # how far the ring bottoms BELOW the baseline, x C
    # ROUND 151 -- THE Q IS HAND CUT. Owner 2026-09-16: *"make Q more
    # handcut"*. A superellipse on a nib is a machine's O with a tail on it:
    # every quadrant is the same quadrant and the only thing that varies round
    # the ring is the pen's own angle. A punchcutter's Q is not that.
    #
    # SIX DELIBERATE CUTS, as (degrees ccw from the right, radial push in
    # units, stroke thickening in units). They are a TABLE and not `life()`'s
    # jitter, and the difference is the point: `life` re-rolls per build, and a
    # defect that moves from one build to the next is noise rather than a cut.
    # Read them as the tool's own history round the bowl --
    #
    #    60   the upper right is where the graver lifts: the ring pulls in 5
    #         and the stroke thins 4, so the letter's lightest quarter is
    #         lighter than the pen alone would make it.
    #   105   and immediately past it the top is a little full, +4 -- the
    #         over-correction that follows a lift.
    #   150   a FLAT on the upper left, -6: the longest straight the cutter
    #         took, and the one deviation big enough to read at text size.
    #   225   the lower left flank is the heaviest press, +4 radial and +5 on
    #         the stroke; this is the quarter the nib's own thick already
    #         falls in, so the two agree rather than fight.
    #   285   the bottom pulls in 3, which is what keeps the ring from
    #         reading as a circle once 225 has been pushed out.
    #   340   a second, shorter flat at the lower right, -4, where the tail
    #         will leave -- the cutter squaring the ground for the join.
    #
    # Everything is 3 to 6 units on a ring whose stroke runs 62 to 115, so the
    # biggest is a twentieth of the letter's own width. At 13 pt none of it is
    # a feature; what it does is stop the four quadrants being the same
    # quadrant, which is the whole complaint.
    Q_HAND = [(60, -5.0, -4.0), (105, 4.0, 0.0), (150, -6.0, 2.0),
              (225, 4.0, 5.0), (285, -3.0, 0.0), (340, -4.0, -2.0)]
    if os.environ.get("ALBO_ALD_Q_HAND") == "0":
        Q_HAND = None

    @glyph('Q')
    def a_Q(c):
        """NO SERIF ANYWHERE, and that is the answer rather than an omission.
        The ring is a closed curve with no terminal to serve, and g_Q's tail
        ends in the pen's cut (`cut1=CUT`) and nothing else -- which is what
        this tail already did, so round 134 changed the Q by not one unit.
        Flanker Griffo Italic and Poetica both finish the tail the same way, a
        swash thinning to a cut. Recorded so the next pass does not re-propose
        it."""
        # ROUND 152 -- THE RING IS SCALED UP OFF ITS OWN TOP. Owner 2026-09-16:
        # *"scale up Q so oval shape is just slightly below baseline, but same
        # height on top"*. So the TOP IS PINNED and the bottom is the free end:
        # the ring's top stays at C + OVER*0.4 exactly where round 151 left it,
        # the bottom goes to -Q_DROP*C, and ry and the centre follow from those
        # two. `rx` is scaled by the SAME factor so the oval keeps its shape --
        # a Q that dropped without widening would be a different letter, not a
        # bigger one -- which means the letter grows to the RIGHT, cx being
        # anchored on the left sidebearing.
        #
        # Round 151's ring bottomed at -5.6 units, 0.008 cap: an overshoot and
        # not a descent. At Q_DROP it bottoms 30 units under, 0.045 cap, for a
        # scale of 1.036 on both radii.
        #
        # The pen does NOT scale with it. `nib_ring`'s thick is CS*CAP_W_ROUND,
        # an absolute, so a bigger ring is the same stroke round a longer path
        # -- which is why cmp_cap_weight barely moves and why the counter opens
        # rather than the letter fattening.
        C = c["cap"]
        top = C + OVER * 0.4                 # round 151's own top, pinned
        bot = -C * Q_DROP
        ry = (top - bot) / 2
        cy = (top + bot) / 2
        kq = ry / (C / 2 + OVER * 0.4)       # what the drop scaled the ring by
        rx = CAP_Q_RX * C * kq; cx = CS * 0.6 + rx
        dy = cy - C / 2                      # the tail rides down with the ring
        # ROUND 150: the ring is on the G's pen too -- same owner instruction as
        # the O's. `ring()` carried `bowl_th`, the family's vertically stressed
        # bowl profile, which measured 1.43:1 with its thick at 15/195: beside
        # a G at 2.20:1 on 50/230 the Q read as a different letter's O.
        ring_ = (ring(cx, cy, rx, ry, floor=S * FLOOR)[0] if Q_AXIS == 'bowl'
                 else nib_ring(cx, cy, rx, ry, unit=Q_INK, floor=S * FLOOR,
                                    hand=Q_HAND)[0])
        if CAP_Q_REF == 'poetica':
            # Poetica leaves the ring at five o'clock and runs out and down in
            # one shortening sweep.
            tail = catmull([(cx + rx * 0.62, -C * 0.02 + dy), (cx + rx * 1.00, -C * 0.10 + dy),
                            (cx + rx * 1.34, -C * 0.19 + dy)], tension=0.5)
            prof = lambda t: 1.10 - 0.72 * t
        else:
            # PAGELLA runs the tail UNDER the letter: it leaves the ring near
            # seven o'clock, dips below the baseline, crosses beneath the bowl
            # almost level, and lifts at its right end. Measured at a 300 px cap
            # with the ink runs read at fixed heights, Pagella's Q shows nothing
            # at all inside the counter at 0.25 of the cap -- 0.008-0.137 and
            # 0.790-0.891, the two sides of the ring and no third run -- while
            # round 134's tail put 0.390-0.537 right through the middle of it.
            # A tail that crosses its own bowl is the shape being changed.
            # THE FIRST POINT SITS ON THE RING, not under it. At 250 degrees
            # the ring's own outline is at about +0.03 C, so a tail that starts
            # below the baseline starts in mid-air: the first cut left a visible
            # gap between bowl and tail and the glyph was two pieces.
            tail = catmull([(cx - rx * 0.30, C * 0.045 + dy),
                            (cx + rx * 0.10, -C * 0.17 + dy),
                            (cx + rx * 0.80, -C * 0.16 + dy),
                            (cx + rx * 1.08, -C * 0.03 + dy)], tension=0.5)
            prof = lambda t: 0.62 + 0.80 * t - 0.82 * t * t
        wt = pen_widths(tail, floor=S * FLOOR)
        return geom.ink([ring_, stroke(tail, lambda t: wt(t) * prof(t), cut1=CUT)])

    # ================================================ ROUND 135: NINE TO POETICA
    # Owner 2026-09-16: *"match R P S Z Q L K M A to poetica."* R P Z L K M came
    # from the roman through italic.py (sheared and narrowed 5%); A S Q were
    # already re-cut here. Each is drawn again below against what the reference
    # letter DOES, not against its proportions -- a proportion is not a
    # construction, and the w/h of the two R's already agreed to 0.09 while the
    # legs were different animals.
    #
    # THE Q IS THE EXCEPTION AND IT IS PAGELLA. Owner's call the same day, in a
    # second message: the Q matches TeX Gyre Pagella Italic rather than Poetica.
    # `ALBO_ALD_Q_REF` keeps both arms reachable and ships `pagella`.
    #
    # HOW THE MATCH IS MEASURED, and the trap in the instrument. `cmp_aldine_shape.py`
    # scales both faces to one X-HEIGHT, which is right for the lowercase it was
    # written for and misleading for a capital: Poetica's cap/x is 1.29 and
    # Albo's 1.54, so every Albo capital arrives 19% TALLER than its reference
    # before a single stroke is compared, and the IoU is then mostly a report of
    # that ratio. Measured on the round-134 tree, x-height-scaled against
    # cap-scaled: A 0.141 / 0.126, M 0.361 / 0.090, S 0.275 / 0.630. The cap
    # height is a family-wide proportion nobody asked to move, so what these
    # letters were drawn against is the CONSTRUCTION -- the swash leg, the arm,
    # the splay, the foot's turn, the ribbon, the bowl's depth, the spine, the
    # tail, the apex -- and both numbers are reported rather than one being
    # quietly preferred.
    #
    # WHAT A RE-CUT COSTS THE REST OF THE FONT, measured rather than assumed,
    # because "no lowercase" is one of the round's own constraints and a naive
    # check says it was broken. Comparing the shipped build against round 134's,
    # 247 of 469 glyphs differ, 23 of them plain lowercase. NONE of that is a
    # lowercase edit. `build.build` draws with ONE `cut.Cutter`, whose `phase()`
    # consumes a running counter once PER CONTOUR in CHARS order, so changing
    # any glyph's contour count re-phases the hand-cut decimation of every glyph
    # drawn after it -- a deliberate one-to-two-unit wobble, landing on a
    # different point of each later outline. Build both trees with FJORD_CUT=0
    # and the count falls to zero plain lowercase: the only non-capital glyphs
    # that then differ are the accented composites of the nine, plus $ § (R) (M)
    # and the U and G that instruction 1's beak touched. Round 134 did the same
    # thing on a smaller scale (26 glyphs, 2 lowercase). It is a property of the
    # cut, not a change to a letter, and there is nothing to fix -- but the
    # naive diff will say otherwise every time, so it is written down here.
    #
    # EVERY ONE OF THEM KEEPS ALBO'S WEDGE. The reference is the shape's
    # authority and never the terminal's: Poetica finishes on a chancery
    # hairline and these are Albo capitals standing beside B C D E F I J T W X Y,
    # so the stems take `cstem_i`'s bracketed wedges and the diagonals take
    # `cdiag`'s, exactly as the round-134 eight do.

    # ---------------------------------------------------------------- R
    # ROUND 140 -- TRACED FROM POETICA, NOT FITTED TOWARD IT. Owner 2026-09-16,
    # the whole instruction: *"copy 'R' from poetica"*. Round 135 cut this
    # letter against Poetica BY EYE and round 138 moved its kick's tip; this
    # round throws both drawings away and rebuilds the letter from Poetica's
    # own outline, sampled.
    #
    # HOW THE TRACE WAS TAKEN, because the scale is the one decision that is
    # not mechanical. `aldine_targets.py` flattens a reference glyph, scales it
    # so its X-HEIGHT lands on Albo's 429, and unshears it -- and for a COPY
    # that scale is wrong. Poetica's cap is 509 on a 1000 em against an x-height
    # of 394 (xh/cap 0.774); Albo's is 674 against 429 (0.636). Scaled by the
    # x-height the letter comes out 553 tall in a 674 alphabet, which is not an
    # R, it is a small capital. So the trace is scaled by CAP HEIGHT instead --
    # uniformly, k = 674/509.2 = 1.3236 -- which reproduces Poetica's
    # proportions exactly at Albo's height, and the width follows from them.
    # It also unshears by 7.88 degrees and NOT by the declared 11: measured on
    # this letter's own stem over 0.55-0.90 cap, Poetica's R leans 7.88, and
    # unshearing by the `post.italicAngle` would have left the "upright" trace
    # leaning 3 degrees the other way before Albo's 13-degree build shear ever
    # touched it. (Its l measures 8.44, so the gap is the font's, not the R's.)
    #
    # WHAT THE TRACE SAYS THE LETTER IS. Three strokes, and the middle one was
    # NOT what round 135's comment claimed: Poetica's bowl is a CLOSED ring that
    # comes back to the stem along a thin bottom arm at 0.454 cap, and the leg
    # springs from the bowl's lower RIGHT, not from the stem. The old drawing
    # sprang the leg out of the stem at 0.46 and closed the bowl on the stem
    # with a superellipse centered ON the stem's midline; the reference's bowl is
    # centered 0.07 cap to the RIGHT of it and its counter's floor is a separate
    # arm. That is why the two letters' whites never agreed.
    #
    # THE LETTER, cut by horizontal lines. Edges in design units from the STEM'S
    # MIDLINE at a cap of 674, unsheared -- this is the table to check a future
    # R against without re-tracing, and the numbers the tables below were taken
    # from:
    #
    #   y/cap    stem l  stem r    bowl/leg l  r
    #   0.00     -145  +128   +365  +500      <- foot serif, and the kick's tip
    #   0.05      -82   +68   +304  +430
    #   0.10      -54   +45   +271  +387
    #   0.15      -47   +39   +245  +355
    #   0.20      -43   +37   +223  +327
    #   0.25      -41   +37   +204  +302
    #   0.30      -40   +37   +186  +279
    #   0.35      -39   +37   +169  +258
    #   0.40      -39   +39   +151  +239
    #   0.45      -39  +221                   <- the bowl's bottom arm, merged
    #   0.50      -38   +39   +157  +223
    #   0.55      -38   +38   +202  +267
    #   0.60      -38   +39   +218  +292
    #   0.65      -38   +39   +223  +306
    #   0.70      -38   +39   +221  +310      <- the bowl's widest, +310
    #   0.75      -39   +40   +215  +308
    #   0.80      -40   +41   +203  +300
    #   0.85      -41   +42   +182  +286
    #   0.90      -43   +45   +144  +262
    #   0.95     -130  +219                   <- crown and top serif, merged
    #   0.99      -14  +139
    #
    # THE STEM IS LEFT EXACTLY AS IT WAS, and that is a finding rather than a
    # convenience. Traced width by height: 79.5 at 0.22, 77.7 at 0.26, 76.8 at
    # 0.30-0.34, 76.4 at 0.58-0.66, 78.2 at 0.74, 81.5 at 0.82, 88.2 at 0.90.
    # The waist moves by ONE UNIT across the middle two thirds -- Poetica's R
    # stem has no entasis worth drawing -- and everything above 0.74 and below
    # 0.22 is its serif brackets, which are Poetica's serifs and not ours. Its
    # midline drifts right by 4.5 units from 0.14 to 0.50 and is then flat: a
    # 0.7% lean, under the hand-cut wobble. `cstem_i` at CAP_BOW 0 is already
    # that stem, so it is untouched and keeps the family's bracketed wedges.
    #
    # WHAT STAYS ALBO'S, deliberately, and none of it is negotiable here:
    #   THE SERIFS   `cstem_i(top='left', foot='both')` -- the CAP_SERIF_* wedge
    #                family. Poetica finishes on a chancery hairline; this R
    #                stands beside B D E F I J L and takes their terminal, which
    #                is the standing rule for all the re-cut capitals.
    #   THE WEIGHT   CAP_R_W scales every traced width to Albo's color, and the
    #                value it lands on is a finding rather than a conversion.
    #                The obvious number is the stem ratio -- the trace's own
    #                stem is 76.4 units (0.113 cap) against Albo's cap stem of
    #                68 (0.101), so 0.89 -- and at 0.89 the letter FAILS
    #                cmp_cap_weight at +0.06 against the roman R's 1.07. It
    #                solves at **0.81**, because Poetica's R carries more of its
    #                weight in the bowl and the leg than Albo's roman R does:
    #                its bowl's thickest is 1.19x its own stem, and 0.81 puts
    #                ours at 1.08x of Albo's. So the copy is 19% lighter than
    #                the reference and NOT 11%, and where that shows is the
    #                kick, which is why the kick needed its own placement rule.
    #                Swept and built: 0.84 +0.02, 0.82 +0.01, 0.81 -0.00,
    #                0.80 -0.01; the gate is --tol 0.05.
    #   THE SLANT    13 degrees, applied by the build to an upright drawing.
    #                Poetica's R leans 7.88, so 4.1 degrees of the residual in
    #                any overlay is this and cannot be taken out.
    #   THE ADVANCE  CAP_BEARING_ADJ['R'] = (0, -56) is the owner's own number
    #                from the round-137 bench and is not touched, and neither is
    #                BEARINGS.
    #
    # AND THE ADVANCE DID NOT BALLOON, which is worth recording because it is
    # the opposite of what a wider-looking reference predicts. Poetica's R is
    # 1.015 cap of ink to Albo's 0.855 before this round, so a copy "should"
    # have widened the letter by 19%. It did not: ink 0.855 -> 0.828 cap and
    # advance 0.895 -> 0.846, i.e. the letter got NARROWER. Cut by horizontal
    # lines at the baseline, from each letter's own stem midline, Poetica reads
    # -146/+127 and +365/+500 and ours -38/+34 and +386/+493 -- the kick's right
    # extreme agrees to 7 units and the ENTIRE width difference is on the left,
    # where Poetica's foot serif reaches 147 units out of the stem and Albo's
    # wedge reaches 61. The extra width was never the letter; it was the serif,
    # and the serif is the part that stays ours. Against the family, Albo's
    # capitals are 0.75-0.91 of Poetica's ink width at a given cap height
    # (B 0.79, D 0.85, E 0.75, H 0.79, K 0.77, L 0.90, N 0.83, P 0.78, U 0.91)
    # and this R moves from 0.86 to 0.82 -- into the middle of that band rather
    # than out of it. An earlier draft of this comment predicted the reverse and
    # was wrong; the measurement is why it says this instead.
    #
    # WHAT IT DID TO THE SPACING, minimum white between the R's ink and the next
    # letter's, in em, measured on 600 px renders (Poetica's own in brackets):
    #
    #            round 139   round 140   [poetica]
    #   Rather     +0.008      +0.042      +0.062
    #   Robert     +0.038      +0.057      +0.062
    #   REMARK     -0.057      +0.002      +0.025
    #   Re         +0.052      +0.063      +0.065
    #   RA         -0.142      -0.145      +0.027
    #
    # REMARK was OVERLAPPING before this round and is not now, and Rather's gap
    # is five times what it was; both come from the kick ending shorter and
    # lower rather than from any bearing. RA is unchanged and is not the R's:
    # the A reaches 0.179 cap LEFT of its own origin at the baseline
    # (CAP_BEARING_ADJ['A'] is -151), so it collides with everything before it,
    # and that is an owner number too.
    #
    # WHAT COULD NOT BE REPRODUCED, measured rather than guessed:
    #   1. THE SERIFS and the slant and the weight, by the rulings above. The
    #      weight is the one that shows: the reference's kick and bowl are
    #      visibly fuller at a 400 px cap, and they are meant to be.
    #   2. THE BOWL'S WEIGHT DISTRIBUTION, as a consequence. Holding the gate
    #      means the bowl's thick lands at 1.08x our stem where the reference's
    #      is 1.19x of its own, so the flank reads a little lighter against the
    #      stem than Poetica's does. Trading it the other way would have to come
    #      out of the roman R.
    #   3. THE IoU AGAINST POETICA CANNOT SEE ANY OF THIS, and must not be used
    #      to judge the round. `cmp_aldine_shape.py --ref poetica` scales both
    #      faces to one X-HEIGHT, and Poetica's cap is 0.774 of its x-height
    #      where Albo's is 0.636 -- so a letter drawn at Albo's cap stands 22%
    #      taller than the reference it is scored against. An EXACT copy of
    #      Poetica's R, scaled to Albo's cap, scores **0.214** in that
    #      instrument -- lower than the drawing this round replaces. Measured by
    #      scaling Poetica's own mask about its baseline: k=1.00 1.000,
    #      k=1.05 0.657, k=1.10 0.440, k=1.15 0.320, k=1.219 0.214, k=1.25
    #      0.190. So that number is reported for the record only. The one that
    #      means something scales both to the same CAP height and aligns on the
    #      baseline and the STEM'S LEFT EDGE AT MID-CAP -- not on the ink bbox,
    #      because our wedge serif reaches further left than Poetica's chancery
    #      one and a bbox alignment slides the whole letter sideways by the
    #      overhang (it cost 0.05 of IoU and scored the traced letter WORSE than
    #      the one it replaced, which is how the bad alignment was caught).
    #      On that measure: round 139 0.526, round 140 0.694.
    CAP_R_W = float(os.environ.get("ALBO_ALD_CAP_R_W", 0.81))   # every traced width x this: see THE WEIGHT below
    # THE BOWL, traced: (x from the stem's midline, height, width), all x cap.
    # One stroke, from the bottom arm's end buried in the stem, right, up the
    # flank and over the crown, back into the stem. The first and last rows are
    # the burial (0.020 cap inside the stem, where the union swallows the join);
    # every other row is a sample of the reference's own centerline, taken as
    # the midpoint between its counter and its outer contour along the counter's
    # outward normal. Thickest 0.1347 cap on the flank at 0.76, thinnest 0.0537
    # at the lower terminal -- a 2.51:1 pen, which is CAP_CON's 2.20 measured
    # rather than assumed.
    CAP_R_BOWL = [
        (0.0200, 0.4540, 0.0695), (0.0814, 0.4548, 0.0695), (0.1044, 0.4547, 0.0661),
        (0.1473, 0.4563, 0.0616), (0.1866, 0.4585, 0.0610), (0.2049, 0.4543, 0.0746),
        (0.2963, 0.5037, 0.0579), (0.3285, 0.5342, 0.0649), (0.3550, 0.5638, 0.0837),
        (0.3756, 0.5980, 0.1028), (0.3900, 0.6414, 0.1200), (0.3946, 0.6786, 0.1288),
        (0.3931, 0.7204, 0.1337), (0.3856, 0.7630, 0.1347), (0.3719, 0.8050, 0.1336),
        (0.3547, 0.8394, 0.1303), (0.3277, 0.8760, 0.1228), (0.2993, 0.9025, 0.1129),
        (0.2611, 0.9269, 0.0983), (0.2265, 0.9427, 0.0871), (0.1855, 0.9552, 0.0762),
        (0.1443, 0.9624, 0.0686), (0.1034, 0.9651, 0.0650), (0.0914, 0.9652, 0.0648),
        (0.0200, 0.9659, 0.0648),
    ]
    # THE LEG, traced the same way: true perpendicular thickness from the paired
    # horizontal and vertical cuts (t = w*h/sqrt(w^2+h^2)), so a diagonal is not
    # reported as the width of the row it crosses. It leaves the bowl's lower
    # right -- the first row is buried inside the bowl, as `a_G`'s spur is at
    # its own junction -- swells to 0.1264 cap at 0.16, which is THICKER than
    # the stem, and runs out to 0.736 cap in a long fine taper whose last three
    # rows sit on and just under the baseline. The tip's final rise is real: the
    # reference's lower edge bottoms at -13 units at 0.65 cap and comes back to
    # -10 by 0.72. Its rightmost ink is 0.745 cap from the stem's midline.
    CAP_R_LEG = [
        (0.2470, 0.4640, 0.1152), (0.2759, 0.4200, 0.1152), (0.3003, 0.3800, 0.1191),
        (0.3112, 0.3600, 0.1224), (0.3337, 0.3200, 0.1184), (0.3453, 0.3000, 0.1196),
        (0.3693, 0.2600, 0.1223), (0.3949, 0.2200, 0.1247), (0.4084, 0.2000, 0.1256),
        (0.4373, 0.1600, 0.1264), (0.4531, 0.1400, 0.1261), (0.4883, 0.1000, 0.1221),
        (0.5089, 0.0800, 0.1180), (0.5349, 0.0716, 0.1113), (0.5705, 0.0478, 0.0965),
        (0.6061, 0.0288, 0.0805), (0.6417, 0.0138, 0.0624), (0.6773, 0.0031, 0.0433),
        (0.7129, -0.0033, 0.0261), (0.7360, -0.0062, 0.0090),
    ]

    # THE KICK IS PLACED BY ITS UNDERSIDE, NOT BY ITS CENTERLINE. Owner
    # 2026-09-16, added to the brief after the first cut: *"the kick off the R
    # needs go below the baseline and copy Poetica."* Measured on the trace:
    # Poetica's kick bottoms at -13.24 units, **-0.0196 cap**, at 0.634 cap
    # right of its own stem midline -- and it IS the kick, not the foot serif,
    # which reaches only -2 before it stops. Round 138 had deliberately put this
    # tip ON the baseline (to spend its overhang in the row a following a or o
    # leaves empty); that ruling is superseded by this one.
    #
    # WHY A TRACED CENTERLINE DOES NOT CARRY A DEPTH THROUGH A WEIGHT CHANGE,
    # which is the whole reason this helper exists. CAP_R_W thins every traced
    # stroke to Albo's color, and a stroke thinned on a fixed centerline lifts
    # its own underside by half of what it lost: the traced centerline built at
    # 0.81 bottomed at -0.0148 cap, three units shy of the reference, with the
    # tip's position and the kick's length both already correct. So the tail's
    # control points are lowered by exactly the half-width the gate took away,
    # along each row's own direction -- which is the same statement as "the tail
    # is placed by the reference's UNDERSIDE and the centerline is what moves".
    #
    # IT RAMPS OFF FAST, AND THAT IS NOT TIDINESS. Sinking the whole leg would
    # drop its TOP edge by w*(1 - CAP_R_W) -- 16 units at the leg's thickest --
    # and the leg's top edge is what the bowl's lower terminal lands on. The
    # ramp is full below CAP_R_KICK_FULL and gone by CAP_R_KICK_FADE, so the
    # junction does not move at all and only the last sixth of the stroke is
    # placed by its underside.
    #
    # SHIPPED: **-0.0192 cap**, lowest at 0.644 cap right of our stem's midline,
    # against the reference's -0.0196 at 0.634 -- a quarter of a unit of depth
    # and seven of position. Round 139's R bottomed at -0.0133. Nothing collides:
    # the minimum white in Rather / Robert / REMARK / Re all GREW (table above),
    # and REMARK stopped overlapping.
    _R_WSAMP = 240      # width samples along a traced stroke (see _R_traced)
    _R_WSMOOTH = 7      # and the moving-average half-window over them
    CAP_R_KICK_FULL = float(os.environ.get("ALBO_ALD_CAP_R_KFULL", 0.030))  # x cap: fully placed by the underside below this
    CAP_R_KICK_FADE = float(os.environ.get("ALBO_ALD_CAP_R_KFADE", 0.120))  # and not at all above it

    def _R_kick_sunk(tab):
        """The leg's traced table with its tail lowered onto the reference's
        underside. Returns a new table; the trace above is left as traced."""
        out = []; n = len(tab)
        for i, (dx, y, w) in enumerate(tab):
            a_ = tab[max(0, i - 1)]; b_ = tab[min(n - 1, i + 1)]
            th = math.atan2(b_[1] - a_[1], b_[0] - a_[0])
            if y <= CAP_R_KICK_FULL: m = 1.0
            elif y >= CAP_R_KICK_FADE: m = 0.0
            else:
                u = (CAP_R_KICK_FADE - y) / (CAP_R_KICK_FADE - CAP_R_KICK_FULL)
                m = 3 * u * u - 2 * u * u * u
            out.append((dx, y - m * (1.0 - CAP_R_W) * w / 2 * abs(math.cos(th)), w))
        return out

    def _R_traced(tab, x0, C, wscale=None):
        """A stroke from a traced table of (dx, y, width), all x cap and dx from
        the stem's midline: the centerline through EVERY traced point, and the
        widths keyed at those points' own arc-length fractions along the drawn
        curve.

        The keying is the part that is easy to get wrong. `stroke` resamples its
        centerline to uniform arc length and asks the width function for
        `i / n`, so a width declared at the index of its control point lands
        wherever the spacing happens to put it -- and this trace is deliberately
        NOT evenly spaced (the flank's samples crowd where the curvature is).
        Measuring each control point's own arc-length position along the catmull
        puts every measured width back where it was measured."""
        pts = [(x0 + dx * C, y * C) for dx, y, _ in tab]
        p_ = catmull(pts, tension=0.5)
        d = [0.0]
        for a_, b_ in zip(p_, p_[1:]):
            d.append(d[-1] + math.hypot(b_[0] - a_[0], b_[1] - a_[1]))
        keys = []
        for (px, py), row in zip(pts, tab):
            j = min(range(len(p_)), key=lambda i: (p_[i][0] - px) ** 2 + (p_[i][1] - py) ** 2)
            keys.append((d[j] / d[-1], row[2] * C * (CAP_R_W if wscale is None else wscale)))
        # AND THEN DENSIFIED AND SMOOTHED, which is not tidying. `widths`
        # smoothsteps between its keys and a smoothstep is C1: its curvature
        # JUMPS at every key, and a stroke's edge is centerline + w/2, so one
        # key per control point put a curvature break every 4% of the bowl.
        # Rendered at a 400 px cap it read as a faceted outer edge with a
        # visible flat at 1 o'clock, against the reference's continuous curve.
        # A moving average of a C1 function is C2, which is the same device
        # `nib_widths` uses (`smooth=9`) and for the same reason. The window
        # shrinks at the ends so the terminal widths are not blunted.
        base = widths(keys); n = _R_WSAMP; k = _R_WSMOOTH
        v = [base(i / n) for i in range(n + 1)]
        v = [sum(v[max(0, i - k):i + k + 1]) / len(v[max(0, i - k):i + k + 1])
             for i in range(len(v))]
        return p_, widths([(i / n, v[i]) for i in range(n + 1)])

    @glyph('R')
    def a_R(c):
        """Stem, a closed ring bowl whose bottom arm returns to the stem, and a
        swash leg out of the bowl's lower right -- Poetica's R, traced. The leg
        is ONE stroke to the tip rather than a strut plus a foot wedge, because
        what separates this R from a roman one is that the leg never stops: it
        thins all the way out and finishes in the pen's own cut, which is what
        `g_Q`'s tail and this module's other tails do. A foot wedge out there
        would be a serif on a swash."""
        C = c["cap"]; x0 = CS * 0.6
        bp, bw = _R_traced(CAP_R_BOWL, x0, C)
        lp, lw = _R_traced(_R_kick_sunk(CAP_R_LEG), x0, C)
        return geom.ink([cstem_i(x0, 0, C, top='left', foot='both'),
                         stroke(bp, bw), stroke(lp, lw, cut1=CUT)])

    # ---------------------------------------------------------------- P
    # POETICA'S P HAS A DEEP BOWL THAT DOES NOT CLOSE. Measured at a 300 px cap:
    # its bowl's lower terminal reaches 0.38 of the cap and stops about a fifth
    # of a stem short of the stem itself, while the roman's closes at 0.44 --
    # so ours read as a small high loop and the reference as a full one. The
    # terminal is left OPEN and cut with the pen, which is `half_bowl`'s
    # `open_bottom` in the roman said in this module's vocabulary.
    CAP_P_BOWL_Y = float(os.environ.get("ALBO_ALD_CAP_P_BY", 0.38))
    CAP_P_BOWL_W = float(os.environ.get("ALBO_ALD_CAP_P_BW", 0.43))
    # THE ARC MUST REACH THE STEM. The first cut stopped at -72 degrees on the
    # reading that Poetica's P leaves its lower terminal free -- it does not,
    # and the count says so before the eye does: a P has TWO contours, an outer
    # and a counter, and the -72 cut built ONE. The counter was open at the
    # bottom and the white ran out of the letter into the sidebearing. -88 is
    # where the arc's own width carries it onto the stem; -99 closes the counter
    # too, and pushes a spur out past the stem's left edge. Both were rendered
    # at 260 px and looked at.
    CAP_P_BOWL_END = float(os.environ.get("ALBO_ALD_CAP_P_END", -88.0))
    # 1.15 -> 1.06 when the serifs doubled (2026-09-16): the P was the one
    # capital the doubling pushed past the gate (+0.05 against its roman),
    # because its bowl already carried the extra weight round 138 gave it.
    CAP_P_W = float(os.environ.get("ALBO_ALD_CAP_P_W", 1.06))   # the bowl's weight, x CAP_W_ROUND
    # ROUND 138 -- UNIFY THE TOP SERIF. Owner 2026-09-16: *"unify the top serif
    # of P."* The wedge itself was never the odd one: this letter's stem is
    # `cstem_i(top='left')`, the same call B D E F I J L H N reach, and measured
    # in UNSHEARED space on a 900 px render its blade reaches 0.0394 of the cap
    # out of the stem against 0.0394 (L), 0.0443 (D), 0.0460 (F I H N) and
    # 0.0476 (B J E) -- inside the hand-cut's own one-to-two-unit wobble.
    #
    # WHAT MADE IT LOOK DIFFERENT WAS THE BOWL LANDING ON TOP OF IT. The arc
    # started at 90 degrees of a superellipse whose crown sits exactly on the
    # cap line, so the STROKE around it put half its own width ABOVE the cap
    # line, and the letter's top read as three levels: the wedge's tip, the
    # stem's flat top, then a step UP into the bowl. In font units off the
    # shipped tree, yMax: B D E F I J L N Z all 676 (the cap line exactly),
    # O 689 (a round letter's honest overshoot), and P **707** -- 31 units, more
    # than twice the O's, on a letter whose crown nobody would call round.
    # Every other capital's top is one continuous edge out of the wedge; this
    # one had a riser in it.
    #
    # So the arc is lowered by exactly the half-width it was hanging above the
    # line, and its LOWER terminal is held: cy and ry each drop by half the
    # overshoot, which moves the crown down by `over` and leaves cy - ry where
    # it was, so CAP_P_BOWL_Y still means what it says. The measurement has to
    # be taken from the drawn stroke rather than declared, because the crown's
    # width is `nib_widths` output and moves with CAP_P_W, CAP_CON and the nib
    # -- a number typed in here would be right today and silently wrong after
    # the next weight change. Set ALBO_ALD_CAP_P_FLUSH=0 for the old top.
    CAP_P_TOP_FLUSH = float(os.environ.get("ALBO_ALD_CAP_P_FLUSH", 1.0))

    @glyph('P')
    def a_P(c):
        """Stem plus one deep arc. The arc stops at CAP_P_BOWL_END rather than -90,
        which is what leaves the lower terminal hanging free of the stem the way
        the reference's does. Its crown is seated ON the cap line rather than
        half a stroke above it, so the top edge leaving the stem's wedge is the
        one continuous line every other capital's is."""
        C = c["cap"]; x0 = CS * 0.6
        rx = CAP_P_BOWL_W * C
        jy = C * CAP_P_BOWL_Y
        ry = (C - jy) / 2 + OVER * 0.2
        cy = C - ry

        def _arc(cy_, ry_):
            p = superellipse(x0, cy_, rx, ry_, math.radians(90),
                             math.radians(CAP_P_BOWL_END), BOWL_K)
            w = nib_widths(p, CS * CAP_W_ROUND * CAP_P_W / S,
                           CS * CAP_W_ROUND * CAP_P_W * 0.30 / S,
                           CAP_CON, smooth=7, taper=False)
            return p, w

        p_, ws = _arc(cy, ry)
        # the crown's own half width is what was standing above the cap line
        over = S * ws[0] / 2 * CAP_P_TOP_FLUSH
        if over:
            p_, ws = _arc(cy - over / 2, ry - over / 2)
        bf = widths([(i / (len(ws) - 1), S * v) for i, v in enumerate(ws)])
        return geom.ink([cstem_i(x0, 0, C, top='left', foot='both'),
                         stroke(p_, bf, cut0=CUT, cut1=CUT)])

    # ---------------------------------------------------------------- Z
    # THE Z WAS ALREADY THE CLOSEST OF THE NINE (cap-aligned IoU 0.665 at round
    # 134) and the whole difference is in its two TERMINALS, which is what the
    # overlay shows: every pixel of disagreement is at the top-left and the
    # bottom-right and none of it is on the diagonal. Poetica RIBBONS both bars
    # -- the top bar's left end drops into a hook that descends about a sixth of
    # the cap below the bar, and the bottom bar's right end lifts into a tail
    # that rises about as far. The roman gives the first a bar-end wedge and the
    # second a modest upturn, so ours read as cut where the reference reads as
    # written.
    CAP_Z_HOOK = float(os.environ.get("ALBO_ALD_CAP_Z_HOOK", 0.22))   # how far the top-left hook descends, x C
    CAP_Z_TAIL = float(os.environ.get("ALBO_ALD_CAP_Z_TAIL", 0.20))   # how far the bottom-right tail rises, x C
    CAP_Z_W = float(os.environ.get("ALBO_ALD_CAP_Z_W", 0.62))         # the letter's width, x C
    # THE Z'S DIAGONAL IS A DECLARED THICK, not a nib stroke, and this is the
    # one place in the nine where the nib had to be overruled. A Z's diagonal
    # runs top-right to bottom-left, which for a right-handed pen at this
    # module's 50-degree nib is very nearly the THIN direction -- so `cdiag`
    # drew it as a hairline and the letter came out at 0.64 of its roman's mean
    # ink width against a 0.05 tolerance, the worst miss of the nine. Sweeping
    # the nib's thick does not rescue it: 1.16 -> 2.60 moved the letter only
    # from -0.400 to -0.158, so reaching the roman would have taken a nib thick
    # of about 3.5 cap stems to make one diagonal, which is a dial being used to
    # say the model is wrong. `g_Z` already says it plainly by declaring CS, and
    # Poetica's own Z has its diagonal as the heaviest stroke in the letter.
    # So it is `primitives.diagonal` at a declared width, as the roman's is.
    # ROUND 138: 1.14 -> 1.09, and the reason is the join below, not the stroke.
    # Burying the diagonal in both bars fills two notches that were paper, so the
    # letter honestly gained ink: `cmp_cap_weight.py` (2 x area / outline length)
    # took the Z from +0.02 against its roman to +0.05, which is the gate's whole
    # tolerance and it FAILED. The junction is not negotiable, so the weight
    # comes back out of the stroke that put it there. At 1.09 the Z reads +0.02
    # again -- the round-137 number exactly -- and every other re-cut capital is
    # unmoved.
    CAP_Z_DIAG = float(os.environ.get("ALBO_ALD_CAP_Z_D", 1.09))     # x CS; the roman declares 1.00 and this letter's bars are lighter, so it carries a touch more
    CAP_Z_BAR = float(os.environ.get("ALBO_ALD_CAP_Z_BAR", 1.28))     # the bars' thickness, x TH_H
    # ROUND 138 -- THE TWO FRACTURES. Owner 2026-09-16: *"correct the fractures
    # of Z in top right and bottom left connections."* Rendered at 900 px and
    # cropped 8x NEAREST at both junctions, each one is a WEDGE OF PAPER driven
    # into the letter -- at the top right it reaches about a third of the way
    # back along the bar's underside, at the bottom left about a quarter of the
    # way in above the bar. They are not a fold and not a width falling to zero:
    # the cause is the third of the three, TWO STROKES BUTTING INSTEAD OF
    # OVERLAPPING, and it is visible in the old call line without rendering
    # anything. The diagonal ran from (.., C - th) to (.., th) -- that is, from
    # the top bar's INNER edge to the bottom bar's INNER edge -- so each of its
    # cut end faces lay exactly ON the joint rather than inside the bar, and its
    # own half width then carried the outer corner of that face PAST the bar's
    # end. Two end faces meeting at an angle with nothing behind either one is a
    # notch, every time; the union has no material there to swallow.
    #
    # The fix is `a_R`'s and `a_G`'s, applied at both ends: bury the end. The
    # diagonal now runs the FULL cap height, from y = C to y = 0, so each end
    # face sits a whole bar's thickness inside its bar and the joint is solid
    # material. Burying it also swings each end outward along the diagonal's own
    # slope -- up-right at the top, down-left at the bottom, which is the exact
    # direction that would push the corner past the bar's end again -- so the
    # horizontal inset is re-solved with it rather than left at the old 0.14.
    # Both were then rendered and re-cropped at 8x; the numbers below are what
    # closed the paper at both junctions without the diagonal's corner breaking
    # the line of the bar's end.
    # THE BURY HAS A CEILING, and it is the cap line. At JOIN 1.0 each end face
    # sits on its bar's OUTER edge, and the end cap's own corner then stands
    # about 20 units proud of it: the Z measured yMax 695 against the cap's 676
    # and yMin -21, a spur above the cap line and another below the baseline,
    # where every other flat capital here reads 676 / -1. 0.60 of the bar
    # (about 31 of its 52 units) is the most that can be spent: measured
    # yMax 677, yMin -3, against the round-137 Z's 676 / -1.
    CAP_Z_JOIN = float(os.environ.get("ALBO_ALD_CAP_Z_JOIN", 0.60))   # how far each end of the diagonal runs INTO its bar, x the bar's thickness
    # The two insets are NOT the same number, and they were swept rather than
    # reasoned. At the TOP the bar's own end is at x 628 and the diagonal's
    # corner reaches 631 at 0.36 and is inside the bar by 0.50, so 0.50 is where
    # the letter's right side becomes one line. At the BOTTOM the diagonal's end
    # face crosses the bar's end cut, and the nick that leaves shrank 12 units
    # (0.36) -> 5 units (0.50) as the inset grew, so it is carried on to 0.62.
    CAP_Z_IN_T = float(os.environ.get("ALBO_ALD_CAP_Z_IN_T", 0.50))   # the top end's inset from the bar's right end, x CS
    CAP_Z_IN_B = float(os.environ.get("ALBO_ALD_CAP_Z_IN_B", 0.62))   # the bottom end's inset from the bar's left end, x CS

    @glyph('Z')
    def a_Z(c):
        """Two bars, a diagonal, and the two ribbon terminals that are the
        letter's whole argument with the roman. The hook and the tail are drawn
        as continuations of their bars -- one stroke each, on the nib -- rather
        than as wedges, because a ribbon is the pen turning and a wedge is a
        cut."""
        C = c["cap"]; x0 = CS * 0.5; w = CAP_Z_W * C
        th = TH_H * CAP_Z_BAR
        top = stroke([(x0, C - th / 2), (x0 + w, C - th / 2)], th, cut1=CUT)
        bot = stroke([(x0, th / 2), (x0 + w, th / 2)], th, cut0=CUT)
        hook_p = catmull([(x0 + w * 0.16, C - th / 2),
                          (x0 + w * 0.01, C - th * 0.8),
                          (x0 - CS * 0.30, C - C * CAP_Z_HOOK)], tension=0.5)
        hook = stroke(hook_p, widths([(0.0, th), (0.55, th * 1.00),
                                      (1.0, th * 1.00)]), cut1=CUT)
        tail_p = catmull([(x0 + w * 0.84, th / 2),
                          (x0 + w * 0.99, th * 0.8),
                          (x0 + w + CS * 0.30, C * CAP_Z_TAIL)], tension=0.5)
        tail = stroke(tail_p, widths([(0.0, th), (0.55, th * 1.00),
                                      (1.0, th * 1.00)]), cut1=CUT)
        # the diagonal is BURIED in both bars -- see the note above the dials
        bury = th * CAP_Z_JOIN
        dg = PR.diagonal((x0 + w - CS * CAP_Z_IN_T, C - th + bury),
                         (x0 + CS * CAP_Z_IN_B, th - bury),
                         CS * CAP_Z_DIAG)
        return geom.ink([top, bot, hook, tail, dg])

    # ---------------------------------------------------------------- L
    # POETICA'S L TURNS ITS FOOT UP. The bar leaves the stem, runs right, and
    # its last fifth lifts into a small rising tail -- 0.11 of the cap above the
    # baseline at a 300 px render -- so the letter finishes with a flick rather
    # than with the roman's bar-end wedge sitting flat on the line. Its stem
    # also bows very slightly left, which this module cannot give it: round 134
    # took the bow out of every capital stem on the owner's bulging report and
    # CAP_BOW is 0. The bow is therefore NOT restored here; the turn is the
    # change, and the straight stem is the standing ruling.
    CAP_L_W = float(os.environ.get("ALBO_ALD_CAP_L_W", 0.54))     # the bar's reach, x C
    CAP_L_TURN = float(os.environ.get("ALBO_ALD_CAP_L_TURN", 0.11))   # how far the tail rises, x C
    CAP_L_BAR = float(os.environ.get("ALBO_ALD_CAP_L_BAR", 1.35))     # the bar's thickness, x TH_H

    @glyph('L')
    def a_L(c):
        """Stem with the family's top wedge, and a bar whose right end turns
        up. The stem takes NO foot wedge on the right, because the bar arrives
        there -- the same rule `a_N` follows at its right stem, and the same one
        `g_L` follows by drawing `foot='left'`."""
        C = c["cap"]; x0 = CS * 0.6; w = CAP_L_W * C
        th = TH_H * CAP_L_BAR
        bar_p = catmull([(x0, th / 2), (x0 + w * 0.62, th / 2),
                         (x0 + w * 0.92, th * 0.9), (x0 + w, C * CAP_L_TURN)],
                        tension=0.5)
        bar = stroke(bar_p, widths([(0.0, th), (0.62, th * 0.94),
                                    (1.0, th * 0.62)]), cut1=CUT)
        return geom.ink([cstem_i(x0, 0, C, top='left', foot='left'), bar])

    # ---------------------------------------------------------------- K
    # ROUND 148 -- TRACED FROM FLANKER GRIFFO ITALIC, NOT FROM POETICA. Owner
    # 2026-09-16, the whole instruction: *"copy the K from franklin griffo"*.
    # Rounds 135 and 138 cut this letter against POETICA, whose K is a stem, a
    # hairline arm and a SWASH leg that thins all the way out and finishes on
    # the pen. Flanker Griffo's K is a different animal and this round throws
    # the Poetica drawing away for it.
    #
    # THE ONE STRUCTURAL DIFFERENCE, and it is the reason the round is worth
    # its cost: **the leg ends in a FOOT SERIF ON THE BASELINE, not in a swash
    # tip.** Cut at the baseline, Flanker's leg reads +236/+583 from its own
    # stem midline -- 347 units of flare, both sides -- against +315/+476 (161)
    # one twentieth of the cap higher. Poetica's leg at the same cut is a point.
    # So the letter stops instead of trailing, which is what a following a or e
    # has to live beside, and rounds 135-138's whole "swash that never stops"
    # reading does not describe this reference at all.
    #
    # HOW THE TRACE WAS TAKEN, same recipe as the R's (round 140) so the two
    # copies are comparable. Flanker Griffo Italic is 2048 upem, cap 1500,
    # x-height 900; scaled by CAP HEIGHT (k = 674/1500 = 0.4493) and NOT by the
    # x-height, because an x-height scale turns a capital into a small capital
    # -- Flanker's xh/cap is 0.600 against Albo's 0.636, closer than Poetica's
    # 0.774 but still wrong for a copy. Unsheared by **12.00 degrees**, which
    # here IS the declared `post.italicAngle`: measured on this letter's own
    # stem over 0.55-0.90 cap it leans 12.003, so unlike Poetica (declared 11,
    # measured 7.88 on its R) the font's own number is the letter's.
    #
    # THE LETTER, cut by horizontal lines, design units from the STEM'S MIDLINE
    # at a cap of 674, unsheared -- the table to check a future K against
    # without re-tracing:
    #
    #   y/cap   stem l/r      arm or leg l/r
    #   1.00    -132/+132     +200/+504   <- the arm's flag terminal, 304 wide
    #   0.95     -68/+68      +281/+411
    #   0.90     -47/+47      +292/+360
    #   0.85     -44/+44      +284/+335
    #   0.75     -44/+44      +248/+294
    #   0.65     -44/+44      +193/+244
    #   0.55     -44/+44      +119/+181
    #   0.50     -44/+201                 <- arm, leg and stem all one mass
    #   0.45     -44/+47      +106/+240
    #   0.35     -44/+44      +189/+304
    #   0.25     -44/+44      +251/+358
    #   0.15     -44/+44      +301/+406
    #   0.05     -68/+68      +315/+476
    #   0.00    -125/+125     +236/+583   <- the leg's FOOT SERIF, 347 wide
    #
    # THE ARM IS A HAIRLINE AND THE LEG IS A STEM, and the split is wider than
    # the drawing it replaces. True perpendicular thickness (the horizontal cut
    # corrected by the local slope, t = w*|dy|/hypot(dx,dy), so a diagonal is
    # not reported as the width of the row it crosses): the arm's body runs
    # 0.055-0.060 cap over its middle two thirds, the leg's 0.1245-0.1250, and
    # Flanker's own stem is 0.1332. So arm/stem = 0.41 and leg/stem = 0.94 --
    # the leg is a second stem, and the arm is a quarter of it. Round 138 had
    # the arm at 1.30 x CS and the leg at 1.62, a ratio of 0.80.
    #
    # BOTH BRANCHES CURVE, and in opposite senses, which is what makes them
    # read as one swept stroke through the junction rather than as a chevron.
    # The arm's horizontal travel per 0.05 cap GROWS going down (16.5, 17.5, 21,
    # 24.5, 28, 31.5, 37 units) -- it leaves the cap line steeply and flattens
    # into the joint. The leg's SHRINKS going down (41, 32.5, 30, 28, 25.5,
    # 23.5, 20.5) -- it leaves the joint flat and steepens onto the foot. Drawn
    # as two straight lines this letter loses the thing that identifies it.
    #
    # WHAT STAYS ALBO'S, by the standing rule for every re-cut capital:
    #   THE SERIFS   `cstem_i(top='left', foot='both')` on the stem, and the
    #                CAP_SERIF_* wedge family at the arm's top and the leg's
    #                foot. Flanker's arm terminal is a 304-unit flag and its
    #                leg's foot a 347-unit slab; ours are wedges, and this K
    #                stands beside B D E F H I J L N.
    #   THE WEIGHT   CAP_K_W scales every traced width. The stem ratio predicts
    #                it: Flanker's cap stem is 0.1332 cap against Albo's 0.101,
    #                so 0.757 -- see the value below for what the gate said.
    #   THE SLANT    13 degrees, applied by the build to an upright drawing;
    #                Flanker leans 12, so 1 degree of any overlay residual is
    #                this and cannot be taken out.
    #   THE ADVANCE  CAP_BEARING_ADJ['K'] is the owner's own bench number.
    K_ARM_EDGE = int(os.environ.get("ALBO_ALD_K_AEDGE", 0))
    CAP_K_W = float(os.environ.get("ALBO_ALD_CAP_K_W", 0.76))   # every traced width x this
    # ROUND 151 -- THE ARM'S CAP TERMINAL. Owner 2026-09-16: *"top right serif
    # of K needs to be visually heavier and reinforce top line"*. Two separate
    # things, and the second is the one the family's wedge cannot do on its own:
    # `_cap_end_wedge` lays its blade along the stroke's OWN direction, so on an
    # arm arriving at 47 degrees the serif runs diagonally up-right and adds
    # nothing to the cap line. The reference's arm finishes in a FLAG lying flat
    # on the cap line -- 304 units of it, measured -- which is what defines the
    # top of the word.
    #   HEAVIER is the wedge scaled (all three of its dimensions, through `k`,
    #   for the reason `_cap_end_wedge`'s own docstring gives: a `scale` passed
    #   down `end_wedge` lengthens and deepens the blade and leaves its apex at
    #   the old thickness, which is a longer sliver rather than a heavier serif).
    #   REINFORCING THE TOP LINE is the flag: a short stroke running LEFT from
    #   the arm's tip along the cap line, thickest where it meets the arm and
    #   thinning to the pen's cut at its free end, which is the same shape the
    #   A's apex flag already carries in this module.
    CAP_K_ASER_L = float(os.environ.get("ALBO_ALD_CAP_K_ASER_L", 0.135))  # the slab's reach LEFT of the arm's tip, x C
    CAP_K_ASER_R = float(os.environ.get("ALBO_ALD_CAP_K_ASER_R", 0.035))  # and right
    CAP_K_ASER_T = float(os.environ.get("ALBO_ALD_CAP_K_ASER_T", 0.62))   # its thickness at the thickest, x S
    # THE ARM, traced, drawn from the CAP LINE DOWN INTO THE STEM:
    # (x from the stem's midline, height, perpendicular width), all x cap. The
    # first row carries the centerline to the cap line holding the width it had
    # at 0.86 (everything above that in the reference is its flag serif and ours
    # is a wedge); the last two rows BURY the stroke in the stem, thickened, so
    # the union swallows the join and the arm's underside and the leg's topside
    # do not leave a white V where they part -- which the first cut of this
    # round did, at 0.47 cap.
    CAP_K_ARM = [
        (0.5400, 1.0000, 0.1068), (0.4957, 0.9200, 0.1068), (0.4846, 0.9000, 0.0896),
        (0.4746, 0.8800, 0.0789), (0.4650, 0.8600, 0.0713),
        (0.4555, 0.8400, 0.0661), (0.4453, 0.8200, 0.0621), (0.4343, 0.8000, 0.0591),
        (0.4223, 0.7800, 0.0571), (0.4096, 0.7600, 0.0558), (0.3961, 0.7400, 0.0551),
        (0.3817, 0.7200, 0.0550), (0.3666, 0.7000, 0.0553), (0.3507, 0.6800, 0.0558),
        (0.3339, 0.6600, 0.0565), (0.3163, 0.6400, 0.0573), (0.2977, 0.6200, 0.0580),
        (0.2781, 0.6000, 0.0585), (0.2573, 0.5800, 0.0587), (0.2352, 0.5600, 0.0604),
        (0.2000, 0.5350, 0.0620), (0.1350, 0.4820, 0.0600),
    ]
    # THE LEG, traced, drawn from the BASELINE UP INTO THE STEM so the family's
    # `_stem_serifs` foot can be seated on it: that helper walks a stroke drawn
    # upward, and this leg arrives at the line 17 degrees off vertical, which is
    # inside what a stem foot handles. Same burial at the top; the first row
    # carries the centerline to the baseline holding the width it had at 0.12,
    # everything below that in the reference being its foot slab.
    CAP_K_LEG = [
        (0.5800, 0.0000, 0.1357), (0.5620, 0.0600, 0.1357), (0.5436, 0.1200, 0.1357),
        (0.5313, 0.1400, 0.1320), (0.5183, 0.1600, 0.1291), (0.5047, 0.1800, 0.1270),
        (0.4904, 0.2000, 0.1257), (0.4756, 0.2200, 0.1250), (0.4603, 0.2400, 0.1246),
        (0.4445, 0.2600, 0.1245), (0.4282, 0.2800, 0.1245), (0.4114, 0.3000, 0.1247),
        (0.3940, 0.3200, 0.1248), (0.3761, 0.3400, 0.1249), (0.3576, 0.3600, 0.1247),
        (0.3383, 0.3800, 0.1243), (0.3181, 0.4000, 0.1231), (0.2966, 0.4200, 0.1197),
        (0.2723, 0.4400, 0.1092), (0.2050, 0.4460, 0.1010), (0.1150, 0.4560, 0.0880),
        (-0.0200, 0.4720, 0.0700),
    ]

    @glyph('K')
    def a_K(c):
        """Stem, a hairline arm off the cap line and a stem-weight leg onto the
        baseline -- Flanker Griffo's K, traced. The arm takes ONE outward wedge
        at the cap, which is the terminal every other capital in this family
        finishes on; the leg takes the family's TWO-SIDED STEM FOOT, because the
        reference's leg stops on the line instead of trailing off, and a foot is
        what a stroke that stops takes here."""
        C = c["cap"]; x0 = CS * 0.6
        ap, aw = _R_traced(CAP_K_ARM, x0, C, CAP_K_W)
        lp, lw = _R_traced(CAP_K_LEG, x0, C, CAP_K_W)
        asolid = stroke(ap, aw)
        # THE ARM'S CAP TERMINAL IS A SLAB, NOT A STACK OF WEDGES. See the note
        # above CAP_K_ASER: both wedge arms left a hairline crack down the
        # arm's left edge, because `_wedge` drops its root back along the
        # stroke by DROP x k and a 36-unit arm has nothing there for a blade
        # scaled past the family's unit to land on. A slab laid along the cap
        # line is one polygon, unions with no seam, and is the thing the
        # instruction actually asks for.
        tx, ty = ap[0]
        slab = stroke([(tx - C * CAP_K_ASER_L, ty - S * CAP_K_ASER_T * 0.5 - C * 0.004),
                       (tx + C * CAP_K_ASER_R, ty - S * CAP_K_ASER_T * 0.5 + C * 0.006)],
                      widths([(0.0, S * CAP_K_ASER_T * 0.74),
                              (0.58, S * CAP_K_ASER_T),
                              (1.0, S * CAP_K_ASER_T * 0.86)]), cut0=CUT, cut1=CUT)
        arm = geom.union([asolid, slab])
        lsolid, Lz, Rz = stroke(lp, lw, sides=True)
        leg = geom.union([lsolid] + _stem_serifs(Lz, Rz, 'both', False))
        return geom.ink([cstem_i(x0, 0, C, top='left', foot='both'), arm, leg])

    # ---------------------------------------------------------------- M
    # POETICA'S M IS SPLAYED AND IT IS WIDE. Cap-aligned, its w/h is 1.39
    # against the sheared roman's 1.15 -- the largest proportional gap of the
    # nine by a factor of three, and the reason its cap-aligned IoU was 0.090,
    # the lowest number in the set. The outer strokes LEAN OUT: the left one's
    # foot sits further left than its apex and the right one's foot further
    # right, so the letter stands like an A beside an inverted V rather than
    # like two rules with a V between them. The middle vertex reaches the
    # BASELINE (Poetica's does; some romans stop it short).
    CAP_M_W = float(os.environ.get("ALBO_ALD_CAP_M_W", 0.83))      # the letter's width, x C
    CAP_M_SPLAY = float(os.environ.get("ALBO_ALD_CAP_M_SP", 0.20))  # how far each outer foot leans out, x CS
    CAP_M_DIAG = float(os.environ.get("ALBO_ALD_CAP_M_D", 0.81))    # the inner diagonals' weight, x CAP_W
    CAP_M_OUT = float(os.environ.get("ALBO_ALD_CAP_M_O", 1.17))     # the outer strokes', x CAP_W
    # THE VERTEX IS LEFT OF CENTRE. Poetica's M brings its two inner strokes
    # down to about 0.42 of the letter's width rather than to the middle, which
    # is what makes its right counter the wider of the two and gives the letter
    # its lean; a centred vertex reads as a symmetrical W upside down.
    CAP_M_VTX = float(os.environ.get("ALBO_ALD_CAP_M_V", 0.52))     # the vertex, x the width

    # ROUND 145 -- ALL FOUR OF THE M'S OWN TERMINALS ARE SERVED, AND TWO OF
    # THEM WERE NOT. Owner 2026-09-16: *"these capitals need serifs: X heavy on
    # light strokes, M, W."* Round 135's M claimed in its own docstring that
    # "the two OUTER ones take the family's diagonal end wedge at the cap line
    # and a flat foot on the baseline". Measured on the shipped build at a
    # 1000-unit cap, with the 13-degree shear taken out (a shear maps a
    # horizontal run to a horizontal run of the same length, so the runs below
    # need no unshearing at all):
    #
    #                       run at the terminal   bare stroke   reach, and which way
    #     left  cap line      77 and falling         138        NONE -- a bare point
    #     left  baseline     164                     101        the A's flat foot
    #     right cap line     167                     119        50 INWARD -- wrong side
    #     right baseline      52 and falling         104        NONE -- a bare point
    #
    # So two of the four ended in a taper, and the one wedge that was there
    # pointed the wrong way. `serif0=1` on a stroke drawn rt->rb puts the blade
    # on the same side as `a_V`'s `serif0=1` does on ITS down-right stroke --
    # which is outward for a V's left arm and INWARD for an M's right stem,
    # where it lands on top of the inner diagonal arriving at the same point.
    #
    # WHAT THE REFERENCES DO AT THESE FOUR PLACES, measured the same way (units
    # of a 1000-unit cap; "reach" is past the bare stroke's own edge):
    #
    #                    cap line, left   cap line, right   baseline feet
    #     Poetica        142 out, 0 in    136 out, 0 in     two-sided slabs
    #     Pagella        149 out, 0 in    112 out, 0 in     two-sided slabs
    #     Flanker        130 out, 0 in    130 out, 0 in     two-sided slabs
    #
    # All three agree on the cap line and they agree with the roman: ONE-SIDED,
    # OUTWARD. The inner diagonal owns the inward side of that junction and a
    # wedge there is a serif on a join. At the FEET all three go two-sided,
    # and the family does not -- `a_A`'s right leg finishes its baseline with
    # one outward blade and nothing inward, and round 134's ruling is that
    # where the reference italics disagree with the roman the roman wins. So
    # the right foot takes `serif1=1`, which is `a_A`'s right leg word for
    # word, and the left foot keeps the flat foot it already had.
    #
    # The inner vertex stays bare, which is not an omission: Poetica's middle
    # run measures 18.6 units at 0.02 cap and nothing at 0.005, Pagella's 70.3
    # falling to 58.2, Flanker's 74.4 falling to 55.6 -- all three taper it to
    # a point, and so does this one (68.4 falling to 53.8).
    @glyph('M')
    def a_M(c):
        """Four strokes, and all four of the letter's own terminals served:
        the two OUTER strokes take the family's diagonal end wedge OUTWARD at
        the cap line, the left one the A's flat foot on the baseline and the
        right one the A's outward blade there. The two inner strokes meet at
        the vertex bare, which is what `a_V` does at the same junction and for
        the same reason -- two strokes closing on each other need no terminal
        between them.

        THE LEFT STROKE IS DRAWN HERE rather than through `_flat_foot_diag`,
        and that is the one structural change. The helper serves the foot and
        TAPERS the other end (`ends=(False, True)`), which is right for the A,
        whose apex is a join; round 134's rule is that a served end does not
        also taper, because a bracket seated on a needle reads as a crossbar
        stuck on a point. Everything else is the helper's body unchanged, so
        the foot is still a level end face with the family's wedge growing
        horizontally out of the leg's left edge and its tip ON the baseline."""
        C = c["cap"]; x0 = CS * 0.5; w = CAP_M_W * C
        sp = CS * CAP_M_SPLAY
        lt = (x0 + sp, C); lb = (x0, 0)
        rt = (x0 + w - sp, C); rb = (x0 + w, 0)
        vtx = (x0 + w * CAP_M_VTX, 0)
        lp = catmull([lb, ((lb[0] + lt[0]) / 2, (lb[1] + lt[1]) / 2), lt], tension=0.5)
        lws = nib_widths(lp, CS * CAP_M_OUT / S, CS * CAP_M_OUT * 0.30 / S,
                         CAP_CON, taper=False)
        lwf = widths([(i / (len(lws) - 1), S * v) for i, v in enumerate(lws)])
        ltn = geom.tangents(lp)[0]
        lsolid, lLz, lRz = stroke(lp, lwf, cut0=math.atan2(-ltn[0], ltn[1]), sides=True)
        left = geom.union([lsolid,
                           _wedge(lLz[0], (0, -1), (-1, 0),
                                  WL * 0.9 * CAP_SERIF_FULL,
                                  WD * 0.9 * CAP_SERIF_TRAIL * CAP_SERIF_FULL,
                                  0.0, edge_at=_edge_back(lLz[::-1])),
                           _cap_end_wedge(lp, lwf(1.0), False, 1)])
        right = cdiag(rt, rb, CAP_M_OUT, serif0=-1, serif1=1)
        d1 = cdiag(lt, vtx, CAP_M_DIAG)
        d2 = cdiag(rt, vtx, CAP_M_DIAG)
        return geom.ink([left, d1, d2, right])


    # ------------------------------------------- THE CAPS' OWN GATE, round 135
    # Every module-level name that existed before the capitals were defined must
    # still hold the object it held. See the note at the head of this section
    # for the five that did not.
    _CLOBBERED = sorted(k for k, v in _PRE_CAPS.items() if globals().get(k) is not v)
    if _CLOBBERED:
        raise RuntimeError(
            "the Aldine CAPS block re-points " + ", ".join(_CLOBBERED) +
            " -- those names belong to letters defined above it, and rebinding "
            "one silently redraws that letter. Give the capital's dial a CAP_ "
            "prefix.")


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
# ------------------------------------------------------------ THE FITTING
# ROUND 133: THE LOWERCASE'S SIDEBEARINGS, in the same UNSHEARED design space
# the shapes were measured in, over the x-height band. Owner 2026-09-16: "fit
# the whole lowercase in one pass."
#
# WHY A TABLE AND NOT THE ROMAN'S MACHINERY. Until this round these letters
# inherited `build.SIDE_FRACTION` x `capbear` + 17 plus `build.BEARING_ADJ`,
# and every one of those inputs was solved in round 96b/97 against a drawing
# that no longer exists -- round 132 redrew all 26 against the reference. The
# machinery's own terms say why it cannot be re-pointed cheaply: it fits a
# letter from its SIDE CATEGORY (straight/round/open/diag) times a capital's
# bearing, which is a rule for a family whose letters were never measured. The
# Aldine letters are drawn in units against a named reference, so their
# bearings are stated in units too, and nothing about the roman moves.
#
# HOW THE NUMBERS WERE GOT -- `outlines/cmp/aldine_space.py`, which re-solves
# them and is the record; re-run it after ANY outline change here.
#
#   A sidebearing is only meaningful against the edge it is measured from.
#   Flanker's `r` carries a right bearing of 64 units because its arm reaches
#   387 across; Albo's r reaches 285, so the same 64 leaves a visibly bigger
#   hole. Copying the reference's numbers transfers its bookkeeping, not its
#   page. What transfers is the WHITE -- and the white between two letters at
#   a given height is a horizontal distance at a fixed y, which a shear leaves
#   alone, so Flanker's white and Albo's are directly comparable with no
#   unshearing at all.
#
#   Writing glyph X's band ink from its own left extreme -- left(y) =
#   lsb + pL(y), right(y) = lsb + pR(y), advance = lsb + W + rsb -- the pair
#   A B has
#
#       gap(y) = rsb_A + lsb_B + [W_A - pR_A(y)] + pL_B(y)
#
#   in which lsb_A cancels: the white is an affine function of rsb_A + lsb_B
#   over a pure-shape term. So all 676 ordered pairs give a linear least
#   squares in these 52 numbers, with exactly one gauge freedom (add c to
#   every lsb, take c off every rsb) pinned by splitting the mean shift evenly
#   between the two sides -- the capitals, figures and punctuation still come
#   from the round-20 fitter, and a one-sided gauge would silently re-space
#   every lowercase-beside-capital pair in the font.
#
#   White is the mean over band rows of min(gap, counter): no gap between two
#   letters counts as more white than the white INSIDE the letter. Without
#   that clip the c's mouth and the r's shoulder spend their whole depth as
#   inter-letter space and the letter is fitted far too tight.
#
#   THEN A RELIEF PASS, because a mean cannot see a collision. The least
#   squares fits the average white and is blind to the minimum, so a pair can
#   average correctly while an exit stroke and an entry stroke cross at one
#   height. Rasterizing each glyph of a pair separately and intersecting the
#   ink, the un-relieved table put 81 of 676 pairs in contact INSIDE the
#   x-height band against Flanker's 7 -- ks, vp, wp, wv, zp, vv, zs -- about
#   1.2 px of overlap at the 27 px reading size. Nothing downstream would have
#   opened them: the lowercase is deliberately unkerned (`outlines/kern.py`,
#   round 95). The floor is the REFERENCE'S OWN worst band minimum, -22 units,
#   which Flanker spends on `rp` -- an italic may interlock, it may not
#   interlock worse than the face it is drawn against. Twelve letters were
#   opened, at most 11 units (g, p), and it cost 2 units of mean white:
#   0.74 -> 0.75 x counter, which is still Flanker's 0.74 to within the
#   measurement.
#
# THE SCALE, which is the one judgment in the round. Even color means the
# white BETWEEN letters tracks the white INSIDE them, so what transfers from
# the reference is a RATIO and not a number of units. Measured over all 676
# pairs, as a multiple of each face's own mean counter (n and o):
#
#     Flanker Griffo Italic   0.74        Albo Medium, the roman      0.75
#     Pagella Italic          0.82        Albo Italic, classic        0.87
#     Poetica                 0.86        Albo Italic, aldine BEFORE  0.96
#     Cancelleresca           0.92
#
# 0.74 is the target: the face round 132 drew against, with Albo's OWN roman
# landing on 0.75 independently -- two unrelated anchors 0.01 apart. The
# aldine italic was at 0.96, the loosest thing in the table bar a chancery
# display face, which is what the page looked like: narrow letters adrift in
# roman-sized gaps. Its counters are 153 against the roman's 272, so most of
# that gap is the drawing being narrow and the fitting never having been told.
#
# The solve's own check that it is recovering the reference rather than
# inventing: the LEFT bearings land on Flanker's almost exactly where the two
# faces draw the same letter -- n -68 against Flanker's -67, i -73 / -74,
# m -66 / -63, r -79 / -83, p -92 / -87, c -37 / -33, s -37 / -31. The right
# bearings come out about 35 units tighter throughout, which is k = 0.678
# doing its job on a narrower letter.
#
# NEGATIVE NUMBERS ARE NOT ERRORS, on either side.
#   * A negative LSB is what an unsheared italic measurement looks like: the
#     unshear pivots on the baseline, so a letter's leftmost band ink is its
#     TOP-left and sits left of the origin. Flanker reads -67 on its own n.
#   * z (-7) takes a negative RSB -- its tail crosses the advance by a tenth
#     of a stem. Flanker allows the same thing outright, fitting its own f at
#     -39. Checked as a MINIMUM and not as a mean (`aldine_space.py --gaps`):
#     no pair in the font closes past -22, which is Flanker's own worst.
#   * THE f KEEPS ITS OVERHANGS, which is a deliberate answer and not a
#     leftover. Flanker's f reaches 211 units left of its origin and 39 past
#     its advance; fitted on its band ink (the stem and the bar, which is what
#     the neighbours actually meet) Albo's reaches 189 left and stays 31
#     inside on the right. The head and the tail are allowed to pass over the
#     neighbours exactly as the reference's do -- that IS the Aldine f -- and
#     the band rule is what lets them, because fitting the f on its full
#     extent would price the overhang as if it were spacing and drive the
#     letter apart.
#   * THE y IS FITTED ON ITS BAND INK, tail excluded, because Y_TAIL_X 8 (the
#     owner's full swash, round 132) is MEANT to pass under the preceding
#     letter. Its band bearings are -48/63 against Flanker's -62/82; the swash
#     reaches 85 left of the origin, below the baseline, where only a
#     descender can meet it.
#
# ch -> (lsb, rsb), design units, UNSHEARED, measured over the x-height band.
# ROUND 136 -- THE OWNER'S OWN FITTING, from the spacing bench (2026-09-16).
# He set the italic live at 64 px on arm B and dialed tracking +26, word space
# 166 and sixteen letters' bearings by hand; the table below is round 133's
# solve plus his deltas, the tracking split 13 / 13 onto every letter so the
# white between any pair is what he saw. His deltas, for the record:
#   a -13/-6 c +0/+17 e +4/-7 f +32/-1 i +15/+16 l +6/-2 n +10/+0 p +6/+0 r +9/+8 s -3/+0 t +0/-9 u +3/-6 v -7/+24 w -4/+12 x -23/+0 y -17/+42
# Letters he did not reach (b d g h j k m o q z) carry the tracking only.
BEARINGS = {
    'a': ( -36,   44), 'b': (  -9,   87), 'c': ( -24,   87), 'd': ( -27,   32),
    'e': ( -19,   72), 'f': ( -32,   81), 'g': ( -13,   72), 'h': (   4,   58),
    'i': ( -44,   57), 'j': (   2,   84), 'k': ( -11,   14), 'l': (  14,   58),
    'm': ( -53,   44), 'n': ( -45,   48), 'o': ( -34,   81), 'p': ( -62,   84),
    'q': ( -16,  128), 'r': ( -53,   85), 's': ( -18,   84), 't': ( -36,   99),
    'u': ( -38,   38), 'v': ( -61,   88), 'w': ( -57,   74), 'x': ( -17,   37),
    'y': ( -52,  118), 'z': ( -22,    6),
}

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


# ================================================================ round 135
# THE Y AND THE O, round 135 -- to Pagella
#
# Owner 2026-09-16: *"for Y Q O, match to pagella."* (The Q is another pass's;
# nothing here touches it.) Both letters came through as the eighteen the
# build only shears and narrows, so what they were is a sheared roman, and
# what the reference does is not a sheared roman in either case.
#
# EVERY NUMBER BELOW IS MEASURED, on Tex Gyre Pagella Italic
# (refs/texgyrepagella-italic.otf) rendered at 600 px and UNSHEARED by its own
# post.italicAngle of -10 degrees, which is the space this module draws in.
# The unshear was proved before it was trusted: Pagella's I leans 28 px over
# 40% of its cap height as drawn (9.6 degrees, its declared angle), and 2 px
# after the transform. It matters because the first cut had the sign the wrong
# way, which DOUBLES the slant instead of removing it -- and a doubly-sheared
# O measures as a ring elongated along the up-right diagonal (outer radius 262
# px at 45 degrees against 179 at 135), which reads as a discovery about the
# reference's axis and is nothing but the bug.
#
# READ THIS BEFORE TRUSTING cmp_aldine_shape ON A CAPITAL. Its font-against-font
# path (`compare_xh`) scales both faces to a common X-HEIGHT and aligns on the
# baseline, which is exactly right for the lowercase it was written for and
# WRONG for a capital, because it then measures the two faces' cap-to-x-height
# ratios as if they were a drawing difference. Albo's is 1.5353 and Pagella's
# 1.4627, so at a common x-height every Albo capital is 5.0% taller before any
# question about its shape: at XH_PX 240 Pagella's O renders 346 x 361 and
# Albo's 376 x 385. On a thin RING a 5% scale moves the stroke by more than half
# its own width at the flanks, and the overlap collapses. The control that
# settles it: Albo's ROMAN O has w/h 0.943 to three places, the same number as
# Pagella's unsheared O, and still scores only 0.429 there.
#
# So this round's numbers are reported on both, and the second is the one that
# answers the question asked:
#
#                        cmp_aldine_shape      ink-height, both upright
#     O   before               0.567                    0.524
#         after                0.441                    0.884
#     Y   before               0.464                    0.436
#         after                0.319                    0.378  (0.709 on the stem)
#
# The first column falls for both letters and the second rises, and the O is
# the proof of which is which: after this round it matches Pagella's unsheared
# w/h, its counter w/h, its 2.25:1 contrast, its 15-degree stress axis and all
# twenty-four of its measured ring widths to within 0.002 of cap height. A
# letter cannot be that and be further from the reference than it was.
#
# The Y's second column is held down by one thing this pass may not touch --
# the family's italic wedge at half size, which puts the ink box's left and
# right extremes in different places from Pagella's and so slides the whole
# letter under a left-edge alignment. Registered on the STEM instead, where the
# serifs cannot move the origin, it is 0.548 before and 0.709 after.
#
# A DIFF OF THIS ROUND TOUCHES 131 GLYPHS, AND 115 OF THEM ARE THE BUILD'S OWN
# COUPLING, NOT A CHANGE TO ANY DRAWING. Worth reading before anyone reverts it
# on the size of the diff, and worth knowing for the Q and the other capitals,
# which will do the same thing.
#
#   * 12 are the O and what is built from it -- O, OE, Oslash and the eight
#     accented O's. 5 are the Y, yen and the three accented Y's. Those are the
#     round.
#   * The other 115 are glyphs whose DRAWN geometry is byte-identical (checked:
#     alpha's bbox and area agree to six decimals across the two trees) and
#     whose assembled outline still moves by a unit or two.
#
# The cause is `cut.Cutter`, and its own docstring says so: "Contours are cut in
# glyph order with one running phase counter." Each contour of each glyph
# consumes one phase, so anything that changes the NUMBER of contours drawn
# before a glyph shifts which vertex in four its hand-cut keeps. Traced to the
# exact record: `yen` is `GLYPHS['Y'](c)` plus two bars (glyphs/symbols.py), and
# with this Y the upper bar crosses the two ARMS instead of the merged stem, so
# the ¥ encloses a small triangle and draws 2 contours where it drew 1. Every
# glyph after ¥ in CHARS then takes the next phase along. Rendered and looked
# at: the ¥ is right, and better -- a ¥'s bar is supposed to cross the arms.
#
# It is NOT floating-point noise and it is NOT the `life()` jitter: the build is
# deterministic (two builds of this tree are identical glyph for glyph), the
# baseline reproduces from HEAD exactly, and the same 131 appear with
# FJORD_LIFE=0. The only way to avoid it would be to raise the Y's join until
# the ¥ stops enclosing a counter, which is damaging the letter to protect a
# decimation phase.
#
# The block sits at the end of the file, after the gate, in its own `if ON:`,
# so three concurrent passes at the capitals do not meet in one hunk. It
# defines no helper anything else uses and redefines no dial: the serifs come
# off `_stem_serifs`, `_end_wedge`, WL/WD/DROP and CAP_SERIF_TRAIL* exactly as
# the H's and the V's do, so when those dials move these two letters move with
# them.
if ON:
    # ------------------------------------------------------------------ THE O
    #
    # WHAT PAGELLA'S O DOES THAT OURS DID NOT -- four things, in the order
    # they cost IoU. Widths are the PERPENDICULAR ring thickness (the distance
    # from a point on the outer contour to the nearest point of the counter),
    # which is the same quantity `ring_from` offsets by, so the table below can
    # be handed to it unconverted.
    #
    #                                   Pagella     Albo italic    Albo ROMAN
    #     ink w/h, unsheared              0.943        0.863          0.943
    #     counter w/h                     0.800        0.757          0.841
    #     thick : thin                  2.25:1       1.72:1         1.80:1
    #     thick at                     15 / 195 deg  165 / 345      180 / 0
    #     thin at                     105 / 285 deg   90 / 270       90 / 270
    #
    #   1. THE PROPORTION. 0.943 against 0.863 -- and 0.943 is ALSO Albo's own
    #      roman O to three places, which is the strongest evidence in this
    #      round that the target is right: two unrelated faces agree, and the
    #      italic was the odd one out because CAP_NARROW's 5% is applied to a
    #      SHEARED bounding box, so an upright-measured italic O comes out 8%
    #      narrower than the roman rather than 5%. Nothing here undoes
    #      CAP_NARROW -- these capitals never consumed `c["W"]` and so never
    #      saw it; the letter is simply drawn at the width the reference has.
    #   2. THE AXIS. Pagella's thins sit at 105 and 285 degrees and its thicks
    #      at 15 and 195 -- one stress axis rotated 15 degrees, the humanist
    #      inclined axis. Albo's italic O had no inclination at all: thin at
    #      exactly 90/270, thick at 180/0, which is the roman's upright axis
    #      carried through the shear unchanged. A sheared upright O is the one
    #      thing a written O cannot be.
    #   3. THE CONTRAST. 2.25:1 against 1.72:1. Pagella's flanks are 18%
    #      heavier than Albo's roman and its thins 5% lighter, so the letter is
    #      not heavier overall -- the ink is moved from the arches into the
    #      flanks.
    #   4. THE DISTRIBUTION IS NOT A SINE. Round the ring the width falls off
    #      steeply from the thick toward the thin on one side and gently on the
    #      other (0.962 of max at 0 degrees, 0.854 at 45, 0.490 at 90), which
    #      is why this is a keyed table and not a pen model with an angle dial.
    #      Same answer, and the same reason, as the a's bowl in round 133: the
    #      width the reference shows at each side, not a guess.
    #
    # THE TABLE IS ALL TWENTY-FOUR MEASURED ANGLES, not a sparse key set, and
    # that is a correction to this round's own first cut. Twelve keys at the
    # extremes (15 / 105 / 195 / 285) left the interpolation to the cosine, and
    # the reference's curve is convex where the cosine is not: the built O came
    # out 0.0040 of cap HEAVY at 120 degrees and 0.0056 at 300, both of them
    # midpoints between two keys, while every angle that had a key of its own
    # landed within 0.0013. A table this cheap should not be asked to guess.
    # `smooth_w` came down from 4 with it -- the +-sample moving average was
    # shaving 2 units off the peaks, which is affordable on a bowl with a tight
    # turn in it and not on a ring that has none.
    #
    # UNITS, and the 2 taken off each: the measurement is of rendered ink, and
    # build.draw() grows every outline by INK_SPREAD (1.2 units a side, so 2.4
    # on a ring's stroke) after this function returns. Keying the measured
    # numbers raw would ship an O 2.4 units heavier than the thing measured.
    O_WH = float(os.environ.get("ALBO_ALD_O_WH", 0.943))     # ink w/h, unsheared
    # 0.89 SOLVED, not chosen: Pagella's O is genuinely heavier than Albo's.
    # Keyed raw, the ring's mean ink width comes out 1.11 x the untouched
    # capitals' median against the roman O's 0.99 (cmp_cap_weight.py), because
    # Pagella's flanks run 0.1195 of cap where Albo's roman runs 0.0991. Round
    # 131c's rule is that an italic capital carries its OWN ROMAN's weight, so
    # the reference sets the distribution and the roman sets the level. A SCALE
    # is the right lever and FIT's weight buffer is not: the buffer moves every
    # edge by a constant, which would take 6.6 units off a 35-unit hairline and
    # the same 6.6 off an 82-unit flank, pushing the contrast from the
    # measured 2.25:1 to 2.65:1 on the way to the weight. Scaling holds the
    # ratio exactly. Cost, recorded: the counter opens a little, 0.807 w/h
    # against the reference's 0.800, which is arithmetic and not a slip --
    # a lighter ring inside the same outer contour has a bigger hole.
    O_INK = float(os.environ.get("ALBO_ALD_O_INK", 0.89))    # x the measured ring widths
    # ROUND 150 -- THE O GOES ON THE G'S PEN. Owner 2026-09-16: *"O and Q need
    # match the line contrast and axis tilt of G"*. The Pagella table above is
    # NOT deleted -- it is a measured reference and the round-136 ruling behind
    # it was real -- it is one env var away at `ALBO_ALD_O_AXIS=pagella`, and
    # everything the comment above says about the proportion, the counter and
    # the 24 measured angles still holds for that arm. What changes on the
    # shipping arm is only the width round the ring: the axis moves from
    # Pagella's 15/195 to the nib's 50/230, and the contrast from the table's
    # measured 2.25:1 to the G's CAP_CON of 2.20:1. The PROPORTION (O_WH) is
    # untouched, because the instruction was about contrast and axis.
    O_AXIS = os.environ.get("ALBO_ALD_O_AXIS", "nib").lower()
    # And its own weight dial, because the distribution moved: the Pagella
    # table's 0.89 is calibrated against that table's own peaks and means
    # nothing to a nib. Solved on cmp_cap_weight against the roman O.
    O_NIB_INK = float(os.environ.get("ALBO_ALD_O_NIB_INK", 1.13))
    O_RING = [(0, 79), (15, 82), (30, 79), (45, 70), (60, 58), (75, 48),
              (90, 39), (105, 35), (120, 39), (135, 52), (150, 67), (165, 77),
              (180, 82), (195, 81), (210, 78), (225, 72), (240, 60), (255, 48),
              (270, 38), (285, 35), (300, 37), (315, 47), (330, 62), (345, 73)]
    if os.environ.get("ALBO_ALD_O_RING"):    # "15:82,45:70,..." -- for the fitter
        O_RING = [(float(a), float(w)) for a, w in
                  (kv.split(":") for kv in os.environ["ALBO_ALD_O_RING"].split(","))]

    @glyph('O')
    def a_O(c):
        """A ring, keyed to Pagella's own widths by angle.

        NO SERIF, and that is the answer rather than an omission -- the same
        one the Q's note gives: a closed curve has no terminal to serve, and
        neither Pagella's O nor Albo's roman puts anything on one.

        `keyed_ring` reads its angle off the superellipse's PARAMETRIC
        coordinate and the table above was measured on the GEOMETRIC angle
        from the counter's centroid. At rx/ry 0.943 the two differ by at most
        1.7 degrees, a ninth of the key spacing, so no correction is applied;
        at a squarer ring it would have to be."""
        C = c["cap"]
        ry = C / 2 + OVER
        rx = O_WH * ry
        cx = CS * 0.6 + rx
        if O_AXIS == 'pagella':
            return geom.ink([keyed_ring(cx, C / 2, rx, ry, O_RING,
                                        k=BOWL_K, unit=O_INK, smooth_w=2)])
        return geom.ink([nib_ring(cx, C / 2, rx, ry, k=BOWL_K, unit=O_NIB_INK,
                                  smooth_w=2)[0]])

    # ------------------------------------------------------------------ THE Y
    #
    # WHAT PAGELLA'S Y DOES THAT OURS DID NOT.
    #
    #   1. IT IS TWO STROKES, NOT THREE, AND THE LEFT ARM IS THE STEM. Ours is
    #      the roman's assembly -- two straight diagonals meeting a separate
    #      vertical stem (`g_Y`: two `diagonal`s and a `cstem`). Pagella's left
    #      edge runs 0.444 of the ink width at 46% of cap height, 0.473 at 40%,
    #      0.484 at 38%, 0.487 at 36%, 0.489 at 34% and then 0.489 all the way
    #      to the foot: one edge, decelerating into the vertical. There is no
    #      junction on that side of the letter, and the arm is the same weight
    #      as the stem it becomes.
    #   2. BOTH ARMS CURVE. Ours are dead straight -- the left arm's center
    #      moves 0.83 of a width per unit height at every height measured, the
    #      right arm's 0.83 likewise. Pagella's left arm runs at 0.93 near the
    #      head and 0.50 at the join, its right arm 1.05 near the head and 0.31
    #      at the join. Both bend toward the vertical as they descend, which is
    #      what makes the letter look written rather than ruled.
    #   3. THE JOIN IS LOWER: 0.45 of cap height against our 0.49.
    #   4. THE FOOT IS A REAL TWO-SIDED SLAB. Ours barely exists -- 0.158 of
    #      the ink width across at 2% of cap height against a 0.108 stem, so
    #      25 units of serif in all. Pagella's is 0.369 across: 67 units either
    #      side of the stem. THIS IS THE LARGEST SINGLE DIFFERENCE IN THE
    #      LETTER and it is NOT fixed here by hand, deliberately. The family's
    #      italic wedge is half its roman one (`pen._ITS` = IT_SERIF 0.50), so
    #      `_stem_serifs` reaches 22 units where the roman reaches 44 and
    #      Pagella reaches 67. The Y now calls the family's foot through the
    #      same `_stem_serifs(..., 'both', False)` the H's stem calls, so
    #      doubling the italic serif doubles this one; inventing a 67-unit
    #      wedge for one letter would leave the Y the odd one out in NAVE the
    #      moment that dial moves.
    #
    # WIDTHS ARE MEASURED, NOT TAKEN FROM THE NIB, and this is the one place
    # the letter departs from `cstem_i`'s model on purpose. Converted to
    # PERPENDICULAR thickness (a horizontal run across a stroke leaning alpha
    # from the vertical is w / cos alpha, and these strokes lean up to 46
    # degrees, so the raw runs overstate the arms by up to 45%):
    #
    #                              Pagella, x cap       the 50-degree nib says
    #     main stroke, head            0.105             thickest here (0.98)
    #     main stroke, join            0.093             ...
    #     main stroke, stem            0.108             THINNEST here (0.64)
    #     right arm, head              0.075             THINNEST here (0.11)
    #     right arm, join              0.052             thickest here (0.39)
    #
    # Both strokes run the OPPOSITE way to the pen: Pagella's stem is the
    # heaviest part of its main stroke and its right arm is heaviest at the
    # terminal it was started from. That is a stroke drawn with the pressure
    # lifting, not a broad nib held at 50 degrees, and no value of CAP_CON
    # produces it -- `con` only rescales the spread, it cannot invert the
    # order. Declaring the widths is the same answer round 133 reached for the
    # a's bowl, for the same reason.
    #
    # THE SKELETON IS PAGELLA'S; THE SPREAD IS NOT, AND THE DIFFERENCE IS THE
    # SERIF. Drawn to the reference's centerlines exactly, this Y measures
    # 0.822 ink w/h against Pagella's 0.875 -- and the skeleton is NOT the
    # reason: the distance from the head's centerline to the right arm's,
    # measured at 70% of cap height, is 0.303 x cap here against Pagella's
    # 0.299. The whole 0.053 is the ink BOX, whose left and right extremes are
    # serif tips at both ends, and the family's italic wedge is half its roman
    # one (`pen._ITS` = IT_SERIF 0.50). So Pagella's serifs reach 0.07 x cap
    # further out than ours at each end and its box is wider round the same
    # letter.
    #
    # A 6% narrow Y beside twenty-five capitals fitted to the family's width is
    # a defect a reader sees, and the family's own rule for the eighteen it
    # only shears is to SPREAD the skeleton until the ink box hits the target
    # (build.solve_widths). This dial does that here, scaling both arms about
    # the stem. It is the one number in this block that is not the reference's,
    # and IT IS TIED TO A DIAL OUTSIDE THIS FILE -- measured, both arms built:
    #
    #     IT_SERIF 0.50 (today)   spread 1.088 -> ink w/h 0.875   upright IoU 0.378
    #     IT_SERIF 1.00 (doubled) spread 1.088 -> ink w/h 0.906   upright IoU 0.533
    #
    # So if the italic wedge is doubled this must come down to about 1.045 or
    # the Y goes 3.5% WIDE instead of 6% narrow. (Note the IoU rises anyway on
    # that arm, because the reference's own serifs are bigger than either.)
    # The target either way is 0.875 -- which is also the family's own answer,
    # since Albo's roman Y is 0.924 and CAP_NARROW's 0.953 puts the italic at
    # 0.881, six thousandths from the reference.
    Y_SPREAD = float(os.environ.get("ALBO_ALD_Y_SPREAD", 1.088))
    Y_PIVOT = 0.4830        # the stem's center, x C -- what the spread scales about
    # x of the main stroke's centerline at a height, both x cap height, foot
    # first -- read off the run table with the arm's half width added to the
    # left edge where the right arm's ink is in the way.
    # ONE CURVE (owner 2026-09-16: "make both Y and y have a single curve on
    # their strokes, not serpentine ones"). Pagella's centerline, keyed raw,
    # carried a wobble where the stem turns into the arm (0.4839 -> 0.4821 ->
    # 0.4681 across 0.20-0.40 of the cap: a lean right, then left, then the
    # arc) and the right arm had a kink at its join. Both are one arc of one
    # curvature now: the spine straight to 0.30 and then a power curve
    # (exponent 1.6) into the top-left, the arm a power curve (0.85) from the
    # join to the top-right. The end points are Pagella's; the wobble is not.
    Y_SPINE = [(0.4816, 0.000), (0.4816, 0.200), (0.4816, 0.300)] + [
        (round(0.4816 - 0.3516 * (((y - 0.30) / 0.675) ** 1.6), 4), y)
        for y in (0.40, 0.50, 0.60, 0.70, 0.80, 0.88, 0.975)]
    # Widths are the MEASURED perpendicular thickness less INK_SPREAD's 2.4
    # units (0.00356 x cap), for the same reason the O's ring table has 2 taken
    # off each key: build.draw() grows the outline after this returns, and the
    # first cut of this round keyed the measurements raw and shipped a Y 4.6%
    # heavy at every height -- stem, left arm and right arm all by the same
    # 4.6%, which is what a constant added to every stroke looks like.
    Y_SPINE_W = [(0.00, 0.1044), (0.31, 0.1044), (0.44, 0.0904), (0.58, 0.0934),
                 (0.68, 0.0964), (0.79, 0.1004), (1.00, 0.1014)]
    # the right arm, join first
    # THE RIGHT BRANCH STEMS UP VERTICALLY (owner 2026-09-16). It ran as one
    # diagonal from the join to the cap line, which is what makes this a V on
    # a stick rather than a Y: both references turn their right arm upright
    # well before the top -- Pagella's is vertical from about 0.72 of the cap,
    # Poetica's from 0.60. So the arm carries its whole horizontal travel in
    # the first third and is a STEM above Y_ARM_VERT, parallel to the left
    # one, which is also what lets its foot serif sit square.
    Y_ARM_VERT = float(os.environ.get("ALBO_ALD_Y_ARM_VERT", 0.80))
    # The curve that turns upright must arrive at the vertical with ZERO
    # horizontal slope, or the join is an elbow: `t ** 0.70` reaches the
    # vertical at full tilt and rendered as a visible corner at 380 px on
    # every turn height tried. `1 - (1 - t) ** p` lands tangent to it.
    Y_ARM_P = float(os.environ.get("ALBO_ALD_Y_ARM_P", 2.0))
    # 0.368 -> 0.28 (owner 2026-09-16: "shorten the right branch of Y until
    # fits the horizontal rhythm of common english words"). Laddered in
    # Yes / Yellow / Yorkshire / ONLY / SYZYGY at 54 and 27 px against both
    # references: at 0.368 the arm hangs over whatever follows it, at 0.24 the
    # letter reads narrow beside O N L, and 0.28 is where the word evens out.
    #
    # WHAT THE LADDER ALSO SHOWED, and it is not what the instruction assumed:
    # shortening the arm cannot change the gap to the next letter. The fitter
    # measures ink, so the advance shrinks with the arm and the right overhang
    # stays +0.129 cap at every rung -- that number is his own -116 right
    # bearing (CAP_BEARING_ADJ['Y']) and nothing in the drawing moves it. The
    # Y's advance is 0.76 of the H's where Pagella sets 0.86 and Poetica 0.88,
    # so the letter is narrow in its box before the arm is touched at all.
    Y_ARM_DX = float(os.environ.get("ALBO_ALD_Y_ARM_DX", 0.28))  # the arm's horizontal travel, x cap
    Y_ARM = [(round(0.4850 + Y_ARM_DX * (1.0 - (1.0 - min(1.0, (y - 0.40) / (Y_ARM_VERT - 0.40))) ** Y_ARM_P), 4), y)
             for y in (0.400, 0.460, 0.500, 0.560, 0.620, 0.680, 0.740, 0.800, 0.890, 0.980)]
    Y_ARM_W = [(0.00, 0.0484), (0.18, 0.0514), (0.38, 0.0574), (0.58, 0.0634),
               (0.78, 0.0684), (1.00, 0.0714)]
    # THE WEIGHT IS ALBO'S, THE DISTRIBUTION IS PAGELLA'S -- round 131c's rule,
    # and this is the dial that carries it. A multiplier on the declared widths
    # rather than a value in FIT's weight column, because FIT's weight is an
    # OUTLINE BUFFER: it moves every edge by a constant, which takes the same
    # number of units off a hairline as off a stem and so drags the letter's
    # contrast up on the way to its weight. The A, V, N and H already do it
    # this way (A_DIAG, V_DIAG, N_SC against a FIT weight of 1.000); this is
    # the same dial for the same reason.
    # 0.94 solved the same way: keyed raw the Y came out 1.01 against its
    # roman's 0.92, and 0.95 / 0.93 bracket the answer at +0.01 / -0.01.
    Y_INK = float(os.environ.get("ALBO_ALD_Y_INK", 0.94))

    @glyph('Y')
    def a_Y(c):
        """Two strokes. The main one is drawn UPWARD -- out of the foot,
        through the stem, into the curve, out to the head at the top left --
        and that direction is load-bearing rather than a preference:
        `_stem_serifs` reads `stroke`'s left-of-travel edge as the letter's
        left, and walks each side polyline from its far end for a foot. Drawn
        downward the same call seats the family's two-sided foot on the HEAD.

        The head takes the family's diagonal end wedge reaching DOWN-LEFT and
        the right arm's terminal one reaching DOWN-RIGHT, which is `g_Y`'s own
        `serif0=1` / `serif0=-1` read through `end_wedge`'s convention for a
        stroke whose served end is its last point instead of its first.
        Pagella agrees with the roman on both: its head's underside carries a
        horn far enough below the arm to break into a separate run for one
        scanline at 90% of cap height, and its right terminal reaches to the
        letter's own right extreme. Neither the roman nor the reference puts
        anything at the join, so nothing is put there.

        A SERVED END DOES NOT TAPER, for the reason `cstem_i` gives: the
        bracket has to land on full width or the serif reads as a crossbar on
        a point. Both ends of both strokes here are either served or buried in
        the other stroke, so `_taper` is off throughout."""
        C = c["cap"]
        x0 = CS * 0.5

        def pt(fx, fy):
            return (x0 + (Y_PIVOT + (fx - Y_PIVOT) * Y_SPREAD) * C, fy * C)

        sp = [pt(fx, fy) for fx, fy in Y_SPINE]
        p_ = catmull(sp, tension=0.5)
        wf = widths([(t, C * v * Y_INK) for t, v in Y_SPINE_W])
        solid, Lz, Rz = stroke(p_, wf, sides=True)
        parts = [solid]
        parts += _stem_serifs(Lz, Rz, 'both', False)
        parts.append(_end_wedge(p_, wf(1.0), False, 1))
        ap = [pt(fx, fy) for fx, fy in Y_ARM]
        q_ = catmull(ap, tension=0.5)
        af = widths([(t, C * v * Y_INK) for t, v in Y_ARM_W])
        parts.append(stroke(q_, af))
        parts.append(_end_wedge(q_, af(1.0), False, -1))
        return geom.ink(parts)


# ============================================ ROUND 145: THE X AND THE W
# Owner 2026-09-16: *"these capitals need serifs: X heavy on light strokes,
# M, W."* The M is re-cut above and its half of the round is there. These two
# were not re-cut at all -- they came from `caps_straight.g_X` / `g_W` through
# the build's shear and 5% narrowing -- so they wore the ROMAN's undoubled
# blade while A G H K L M N O P Q R S U V Y Z wore the doubled one that
# `CAP_SERIF_FULL` 2 shipped on 2026-09-16. This block is its own `if ON:` at
# the foot of the file for the reason the O/Y block gives: two passes at the
# capitals should not meet in one hunk. It defines no helper and redefines no
# dial.
#
# HOW BIG THE GAP WAS, measured rather than asserted. Rendered at a 1000-unit
# cap and read as horizontal ink runs with the 13-degree shear taken out (a
# shear maps a horizontal run to a horizontal run of the same length, so the
# numbers need no unshearing), "reach" being the widest run over the terminal
# minus the bare stroke's own run well clear of the bracket:
#
#                       bare   before   reach      after   reach
#     X thick top      122.2    154.1     30.5     195.2    73.0
#     X thin  top       54.4     95.1     38.7     149.7    95.3
#     X thin  foot      56.4     93.9     37.5     148.2    91.8
#     X thick foot     121.5    149.1     25.5     188.4    66.9
#     W down-stroke    108.4    140.2     33.4     164.6    56.2
#     W up-stroke       64.4     85.9     23.5     122.4    58.0
#
# THE FAMILY'S OWN BLADE IS 74.9, AND THE 101.1 IT LOOKS LIKE IS AN ARTEFACT.
# `a_V`'s top terminal measures 208.3 over a bare 107.2 -- but FIT gives the V
# a WIDTH of 1.350, which scales the finished outline horizontally, blades and
# all, so 101.1 / 1.35 = 74.9 is the blade this family actually cuts. The X's
# thick top now measures 73.0 and its foot 66.9, which is that blade to within
# the hand cut's own wobble. This is worth writing down because the naive
# comparison says the X is 28% short of the V and it is not short at all; the
# same trap is waiting for anyone who measures the A (width 1.350 too).
#
# IT IS STILL HALF THE REFERENCES', AND THAT IS A FAMILY QUESTION AND NOT
# THIS ROUND'S. Poetica's X reaches 222.9-272.3, Pagella's 241.7-263.5,
# Flanker's 224.2-258.5 -- three times what Albo cuts -- and all three are
# TWO-SIDED where Albo's are one-sided outward. `a_V` is exactly as far off
# them on both counts, and so are `a_A`'s feet: it is the size and sidedness of
# the whole doubled family, decided by the owner on 2026-09-16 ("yes to SFULL
# 2") after seeing it, and moving it for three letters would make these three
# the odd ones out instead. Recorded so the next pass does not re-measure it.
#
# "HEAVY ON LIGHT STROKES" -- WHAT THE REFERENCES ACTUALLY SAY, because the
# instruction is checkable and the check does not simply confirm it. Each
# reference X's serif reach on the THIN diagonal against the same reach on the
# THICK one:
#
#                    top     foot
#     Poetica        1.22    1.03
#     Pagella        0.94    1.03
#     Flanker        1.00    1.00
#
# The absolute reach is the SAME on both diagonals to within a few per cent in
# five of those six pairs. A slab serif is a fixed length, which is round 135's
# own finding arriving from the other side ("a slab serif is a fixed length,
# not a multiple of the stem") -- and Albo's wedge is already fixed, since
# `_cap_end_wedge` takes WL/WD/DROP and never the stroke's width. So the naive
# reading of the instruction -- make the light stroke's blade absolutely bigger
# -- is supported by exactly one measurement out of six, Poetica's top pair.
#
# WHAT IS SUPPORTED, by all three and by a wide margin, is the instruction's
# EFFECT. A fixed blade on a stroke half the width is twice the event:
#
#                    reach / its own stroke      thick      thin
#     Poetica                                     1.66      3.25
#     Pagella                                     2.05      2.71
#     Flanker                                     1.50      2.96
#
# 1.4x to 2.0x more serif per unit of stroke on the light diagonal, in every
# reference. That is what "heavy on light strokes" looks like on a page, and
# the mechanism is the fixed length rather than a bigger blade. `CAP_X_THIN`
# is therefore SMALL -- 1.25 -- and not the 2x that reading the instruction
# literally and skipping the measurement would have produced. It is a dial, so
# the literal reading is one env var away.
#
# WHAT IT RENDERS, which is not the dial: reach on the thin over reach on the
# thick comes out 1.30 at the cap line and 1.37 at the baseline, against the
# dial's 1.25, because the two diagonals meet a horizontal scanline at
# different angles and the geometry adds to the dial. Poetica, the one
# reference that puts more blade on the light stroke, reads 1.22 and 1.03. So
# this sits a little past the only measurement that supports it and a long way
# short of a literal doubling. The relation the eye actually reads -- blade
# against its OWN stroke -- comes out 0.60 on the thick and 1.75 on the thin,
# both below the references (1.50-2.05 and 2.71-3.25) by the same factor of
# about two-and-a-half, which is the family's half-size blade and not this
# dial. What the instruction asked for is the RATIO between those two, and it
# comes out 2.9 against the references' 1.3 to 2.0 -- past all three, because
# the X's own contrast is steeper than theirs (0.454 against 0.508-0.708) and
# a fixed blade on a thinner hairline is a bigger event for free. Reported
# rather than tuned back: the instruction was "heavy on light strokes", the
# arm that obeys it least is `ALBO_ALD_CAP_X_THIN=1.0`, and the owner has the
# render.
#
# THE SIDES. All three references give the X two-sided slabs at all four
# terminals (Flanker: 140 out, 84 in). The family does not, and the roman does
# not: `a_V`'s tops and `a_A`'s feet are one-sided outward blades, and round
# 134's ruling is that where the reference italics disagree with the roman on a
# terminal the roman wins, because following them would make these letters the
# odd ones out a second time in the other direction. One-sided outward, as the
# roman's own `serif0=1 / serif1=1` and `serif0=-1 / serif1=-1` already said.
#
# THE W'S FEET AND THE W'S APEX TAKE NOTHING, and both are measurements rather
# than omissions. Every reference W tapers its two baseline vertices to a point
# -- Poetica 140.5 units of run at 0.10 cap falling to 58.2 at 0.005, Pagella
# 125.0 to 79.3, Flanker 145.0 to 157.9 through a merge and then down -- and
# none of them puts a terminal there. The apex keeps the roman's CROWN at
# `W_CROWN` exactly, imported rather than copied so it cannot drift: it is the
# owner's own 2026-09-13 ruling ("lower and reduce the protuberance of the top
# middle connector in W"), and doubling it with the serifs would reverse that
# ruling by the back door. Poetica's and Flanker's W's have four separate cap
# terminals where this one has a pointed apex, so their middle pair has no
# counterpart here at all; Pagella's W is built as this one is and its apex
# carries nothing.
#
# WHAT IT COSTS BESIDES THE SERIFS, stated because it is not nothing. A re-cut
# leaves `build.solve_widths` behind -- these capitals never consume `c["W"]`,
# so the 5% italic narrowing that shaped the sheared X and W no longer reaches
# them and the drawn width has to carry it. `CAP_X_W` and `CAP_VV_W` are
# therefore solved off the SHIPPED letters: the stroke centres of the build
# this round started from, read at 0.20 and 0.80 cap and extrapolated to the
# cap line and the baseline, give the X 0.688 C of horizontal travel per
# diagonal and the W a width of 1.375 C (its apex at 0.5 w and its feet at
# 0.26 / 0.74 w reproduce to within a unit). The letters therefore stand where
# they stood -- but their ADVANCES do not, because the bearing solver measures
# ink and a blade is ink: X 710 -> 738, M 856 -> 898, W 941 -> 982, about 4%
# each. Round 134's eight moved by the same kind of step when they were served
# (its own table: H 0.910 -> 0.992 of its roman, N 0.916 -> 1.000), so this is
# the serifs earning their width and not a spacing slip. The round-137 bearing
# deltas (`CAP_BEARING_ADJ`, the owner's own hand on the bench) are untouched
# and still apply on top of it.
#
# THE CONTRAST DOES NOT MOVE, AND THAT COST A BUILD TO ESTABLISH. The roman
# gives the X's second diagonal and the W's two up-strokes an extra 0.72 by
# hand (`caps_straight.pw`'s `mult`) on top of the pen's own angle-dependent
# width. Round 131c's ruling forbids that in this module -- "a per-stroke
# multiplier that differs between them is the pen's own contrast being
# overwritten by hand" -- so the first cut of these two letters took ONE
# multiplier each and let the nib make the relation, exactly as `a_V` does.
# Built and measured, thin over thick as horizontal ink runs:
#
#                      shipped   one multiplier   Flanker  Poetica  Pagella
#     X                 0.456        0.406         0.508    0.622    0.708
#     W                 0.585        0.643         0.499    0.519    0.600
#
# The X came out LIGHTER in its hairline, not heavier, and further outside the
# references' range than the letter it replaced. The reason is that round 131c
# was solved on a V, and a V is not an X: `a_V`'s two strokes leave its apex at
# about 18 degrees off vertical, while an X's cross at 34.5, and the nib's
# ratio at those two pairs of angles is 0.64 and 0.41. The ruling's own
# argument -- that the nib knows the relation -- therefore does not carry from
# one letter to the other, and applying it here would have thinned the hairline
# in a round whose whole subject is making these letters' terminals visible.
#
# So both letters keep the weights they ship with, to the unit, and each has a
# second dial for its light arms. That is a departure from round 131c and it is
# recorded as one: it is NOT the inversion that ruling was written against (a
# hand making the pen's heaviest stroke its lightest), it is the roman's own
# convention preserved, and it keeps this round to the terminals the owner
# named. `CAP_X_THIN_W` 1.0 and `CAP_VV_THIN_W` 1.0 are the single-multiplier
# arm, one env var away.
if ON:
    # The crown's two numbers are IMPORTED, not copied, for the same reason
    # `CAP_BEAK_CUT` is: they are the owner's 2026-09-13 ruling on the roman W
    # and a second copy here would drift the moment that ruling moves again.
    from .caps_straight import (W_CROWN as CAP_VV_CROWN,
                                W_CROWN_DROP as CAP_VV_CROWN_DROP)

    # The W's dials cannot take a `CAP_W_` prefix -- `CAP_W` and `CAP_W_ROUND`
    # are the PEN's thicks and have been since round 131 -- so the letter's own
    # dials are `CAP_VV_`, the W being a double V.
    CAP_X_W = float(os.environ.get("ALBO_ALD_CAP_X_W", 0.688))    # each diagonal's horizontal travel, x C
    # 0.879 and 1.153 are SOLVED, not chosen, and they answer to the GATE
    # rather than to a ruler. A build at 0.700 flat rendered the thick at 98.7
    # units of a 1000-cap horizontal run and the thin at 40.4, and `nib_widths`
    # is linear in this dial, so 0.877 / 1.115 put the pair on the shipped
    # letter's 123.6 and 56.4 -- and cmp_cap_weight then read +0.012 against
    # the roman X where the letter this replaced read +0.015. 0.891 lands the
    # thick dead on 123.6 and costs +0.033. These two split it: the thick
    # renders 1.4% under the shipped stroke, which is inside the hand cut's own
    # wobble, and the gate reads what the shipped letter read. What it renders:
    # 121.9 and 55.4, ratio 0.454 against the shipped letter's 0.456.
    # It is a SCALE and not a FIT weight, for the reason `O_INK` and `Y_INK`
    # give: FIT's weight column is an outline BUFFER that moves every edge by
    # a constant, so it takes the same units off a hairline as off a stem and
    # drags the letter's contrast up on the way to its weight. Scaling the
    # stroke holds the ratio exactly.
    CAP_X_DIAG = float(os.environ.get("ALBO_ALD_CAP_X_D", 0.879))  # the heavy diagonal's weight, x CS
    CAP_X_THIN_W = float(os.environ.get("ALBO_ALD_CAP_X_TW", 1.153))  # the light diagonal's, x CAP_X_DIAG
    CAP_X_THIN = float(os.environ.get("ALBO_ALD_CAP_X_THIN", 1.25))  # the light diagonal's blades, x the family's

    @glyph('X')
    def a_X(c):
        """Two diagonals crossing, the roman's own construction: the THICK one
        from the cap line at the left down to the baseline at the right, the
        THIN one the other way. Four terminals, four one-sided outward blades,
        and the thin diagonal's two at `CAP_X_THIN` of the family's.

        The thin stroke is drawn here instead of through `cdiag` for one
        reason: `cdiag` seats `_cap_end_wedge` at the family's own
        `CAP_SERIF_FULL` and offers no way past it, and this round's whole
        instruction is that these two blades are not that size. Everything
        else is `cdiag`'s body word for word, so the `+1/-1` side convention
        is the roman's unchanged and a served end neither tapers nor keeps a
        pen cut behind the wedge's face."""
        C = c["cap"]; x0 = CS * 0.5; dx = CAP_X_W * C
        p0, p1 = (x0, C), (x0 + dx, 0)
        q0, q1 = (x0 + dx, C), (x0, 0)
        qp = catmull([q0, ((q0[0] + q1[0]) / 2, (q0[1] + q1[1]) / 2), q1], tension=0.5)
        qw = CAP_X_DIAG * CAP_X_THIN_W
        qws = nib_widths(qp, CS * qw / S, CS * qw * 0.30 / S,
                         CAP_CON, taper=False)
        qwf = widths([(i / (len(qws) - 1), S * v) for i, v in enumerate(qws)])
        k = CAP_SERIF_FULL * CAP_X_THIN
        return geom.ink([cdiag(p0, p1, CAP_X_DIAG, serif0=1, serif1=1),
                         stroke(qp, qwf),
                         _cap_end_wedge(qp, qwf(0.0), True, -1, k=k),
                         _cap_end_wedge(qp, qwf(1.0), False, -1, k=k)])

    CAP_VV_W = float(os.environ.get("ALBO_ALD_CAP_VV_W", 1.375))   # the letter's width, x C
    # 0.985 and 0.909 solved the same way and from the same build: at 0.640
    # flat the down-strokes rendered 71.8 units of a 1000-cap horizontal run
    # and the up-strokes 46.2, against the shipped letter's 107.35 and 62.75,
    # which is 0.957 / 0.909. The extra 2.9% on top of that is the SERIFS
    # being paid for: 2 x area / outline length is what the gate measures, a
    # blade adds more outline than it adds area, and at 0.957 the re-cut W read
    # -0.040 against its roman where the sheared W it replaces read -0.015.
    # 0.985 puts it back on -0.013. Both arms are scaled together so the
    # letter's own contrast does not move; see the X's note for why this is a
    # scale and not a FIT weight. What it renders: 108.6 and 64.5, which is
    # +1.2% and +2.8% on the shipped letter, ratio 0.594 against its 0.585.
    CAP_VV_DIAG = float(os.environ.get("ALBO_ALD_CAP_VV_D", 0.985))  # the down-strokes' weight, x CS
    CAP_VV_THIN_W = float(os.environ.get("ALBO_ALD_CAP_VV_TW", 0.909))  # the up-strokes', x CAP_VV_DIAG

    @glyph('W')
    def a_W(c):
        """Four arms and a crown, `g_W`'s own construction: two down-strokes
        landing at 0.26 and 0.74 of the width, two up-strokes leaving a
        sixth of a cap stem to their right, and the crown hanging under the
        apex where the middle pair meet.

        ONLY THE TWO OUTER TOPS ARE SERVED. The inner pair end at the apex,
        which the crown finishes; the two baseline vertices are junctions where
        two strokes close on each other, and all three references taper theirs
        to a point. `serif0=1` on the left arm and `serif0=-1` on the right are
        `g_W`'s own, and they reach outward."""
        C = c["cap"]; w = CAP_VV_W * C; s = CS; ox = CS * 0.2
        f1, f2 = (ox + w * 0.26, 0), (ox + w * 0.74, 0)
        apex = (ox + w * 0.5, C)
        up = CAP_VV_DIAG * CAP_VV_THIN_W
        a = cdiag((ox + s * 0.3, C), f1, CAP_VV_DIAG, serif0=1)
        b = cdiag(apex, (f1[0] + s * 0.15, 0), up)
        d = cdiag(apex, f2, CAP_VV_DIAG)
        e = cdiag((ox + w - s * 0.3, C), (f2[0] + s * 0.15, 0), up, serif0=-1)
        # the crown, `g_W`'s to the unit. `pw` cannot be used for its offset
        # here -- these arms are drawn on the nib and `pw` is the roman's pen
        # width for a straight line -- so the b arm's own width at the apex
        # stands in for it, which is the quantity the roman was asking for.
        bw = nib_widths(catmull([apex, ((apex[0] + f1[0] + s * 0.15) / 2, C / 2),
                                 (f1[0] + s * 0.15, 0)], tension=0.5),
                        CS * up / S, CS * up * 0.30 / S,
                        CAP_CON, taper=False)[0] * S
        crown = _wedge((apex[0] - bw * 0.35, C - DROP * (CAP_VV_CROWN_DROP - 1.0)),
                       (0, 1), (-1, 0), WL * CAP_VV_CROWN, WD * CAP_VV_CROWN, DROP)
        return geom.ink([a, b, d, e, crown])


# ROUND 137 -- THE CAPITALS' SPACING, HIS. Set live on the bench
# (https://claude.ai/artifact/9RUVYkit1Vdk9foVUTFz46) at 58 px on arm B, every
# capital dialed by hand. These are DELTAS in design units on whatever the
# round-20 rule computes, because a capital's bearings are solved from its own
# ink and the reference widths rather than read from a table -- so the letter
# stays fitted to its drawing and this is the hand on top of it.
# The big ones say what the fitter had wrong: H N Y -86 to -116 on the right
# (far too loose after a flat-sided capital), A -151 on the left (its apex
# overhangs and the fitter was paying for air), W -132 right, T +87 left.
CAP_BEARING_ADJ = {
    'A': (-151,    0), 'B': (   1,   -2), 'C': (  -7,  -54), 'D': (  -4,   14),
    'E': ( -77,  -50), 'F': (   0,  -37), 'G': (   0,  -28), 'H': (   0,  -86),
    'I': (  33,  -61), 'J': ( -84,    0), 'K': (   0,  -32), 'L': (  -3,  -24),
    'M': (   0,  -48), 'N': (   0,  -86), 'O': (   9,  -16), 'P': (   0,    3),
    'Q': (   0,  -30), 'R': (   0,  -56), 'S': (   0,   36), 'T': (  87,  -56),
    'U': (   0,   12), 'V': (   0,  -48), 'W': (  35, -132), 'X': (   0,  -11),
    'Y': (   0, -116), 'Z': (   0,  -78),
}
