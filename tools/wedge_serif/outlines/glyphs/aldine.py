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
    'h': (0.938, 1.100),
    'l': (0.550, 1.100),
    'm': (1.131, 0.850),
    'p': (0.550, 0.725),
    'r': (0.938, 1.100),
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
    'Q': (0.492, 1.225),
    'V': (1.000, 1.350),
    'S': (1.218, 0.975),
    'N': (1.000, 1.100),
    'H': (0.950, 1.100),
    'G': (1.175, 1.100),
    'U': (0.950, 1.225),
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
    O_PEN = float(os.environ.get("ALBO_ALD_O_PEN", 25.0))      # the nib's angle, degrees
    O_THICK = float(os.environ.get("ALBO_ALD_O_THICK", 1.44))  # x S, at the pen's fullest
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
    E_W = float(os.environ.get("ALBO_ALD_E_W", 0.70))       # 38/58 measured
    # The bar's ends, off the macro: its TOP edge (the eye's floor) is at row
    # 371 where it leaves the left flank and row 364 at x620 -- 0.54 and 0.67
    # of the band. The eye itself is x608-622 by rows 353-369: 0.37 of the
    # letter's width and 0.28 of the x-height. The first cut had the bar's left
    # end at 0.40 and the upper loop's flanks at 0.18/0.92, which made an eye
    # 0.55 W wide -- half again Griffo's -- and THAT, not the stroke weight,
    # was the counterspace. The macro's stroke is 0.79 x the stem: a LIGHT
    # letter with a small eye, not a heavy one.
    E_BAR = float(os.environ.get("ALBO_ALD_E_BAR", 0.50))   # the bar's LEFT end, x xh
    E_BAR_R = float(os.environ.get("ALBO_ALD_E_BAR_R", 0.61))  # its RIGHT end -- the rise
    E_EYE = float(os.environ.get("ALBO_ALD_E_EYE", 0.54))   # scales the upper loop's flanks
    E_WT = float(os.environ.get("ALBO_ALD_E_WT", 1.00))
    E_CON = float(os.environ.get("ALBO_ALD_E_CON", 1.00))   # contrast, x the measured 3.4:1
    E_THICK = float(os.environ.get("ALBO_ALD_E_THICK", 1.24))  # x S, across the nib
    E_THIN = float(os.environ.get("ALBO_ALD_E_THIN", 0.26))    # x S, along it
    E_CTR = float(os.environ.get("ALBO_ALD_E_CTR", 1.14))   # >1 eats counterspace
    E_END = float(os.environ.get("ALBO_ALD_E_END", 0.54))   # where the bottom stops. It STOPS.
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
             (E(0.84), E_SHOULDER), (E(0.52), E_TOP),   # up the eye's right, over the crown
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
    A_STEM_X = float(os.environ.get("ALBO_ALD_A_STEM_X", 317.0))   # stem centre, units
    A_STEM_W = float(os.environ.get("ALBO_ALD_A_STEMW", 70.0))     # units
    A_STEM_TOP = float(os.environ.get("ALBO_ALD_A_TOP", 0.97))     # x xh
    A_RX = float(os.environ.get("ALBO_ALD_A_RX", 155.0))            # bowl outer half-width, units
    A_CY = float(os.environ.get("ALBO_ALD_A_CY", 215.0))            # bowl centre height, units
    A_SKEW = float(os.environ.get("ALBO_ALD_A_SKEW", 0.06))         # the egg's lean, dx per dy
    A_K = float(os.environ.get("ALBO_ALD_A_K", 1.90))               # squareness
    A_TAIL_X = float(os.environ.get("ALBO_ALD_A_TAIL_X", 434.0))    # tip, units from the left edge
    A_TAIL_Y = float(os.environ.get("ALBO_ALD_A_TAIL_Y", 0.15))     # x xh
    A_HEAD_R = float(os.environ.get("ALBO_ALD_A_HEAD_R", 22.0))     # the head's reach right of the stem, units
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

    @glyph('a')
    def a_a(c):
        """The Aldine single-storey a: a ring filling the x-height, a straight
        stem the height of the x-line, and a short thick tail along the
        baseline. See the block above for where every number comes from."""
        xh = c["xh"]; u = xh / A_UNIT; x0 = S * 0.6
        xs = x0 + A_STEM_X * u; sw = A_STEM_W * u
        # the stem: straight, its top cut on the pen's angle. The owner's scan
        # crop and the Petrarch page both put a small blunt HEAD on the
        # stem's top right -- the nib set down and pushed right before the
        # downstroke -- so the top face reaches a little past the stem on
        # that side and slopes down to the left. Flanker has the same corner,
        # smaller; the scan is the target.
        stem = stroke([(xs, S * 0.10), (xs, xh * A_STEM_TOP)], sw, cut1=CUT)
        hr = A_HEAD_R * u
        head = geom.poly([(xs - sw / 2, xh * A_STEM_TOP - 26 * u), (xs + sw / 2 + hr, xh * A_STEM_TOP + 4 * u),
                          (xs + sw / 2 + hr * 0.7, xh * A_STEM_TOP + 12 * u), (xs - sw / 2 + 10 * u, xh * A_STEM_TOP - 8 * u)])
        # the bowl
        ry = (xh + OVER * 0.6) / 2.0 + 0.0
        bowl_ = keyed_ring(x0 + A_RX * u, A_CY * u, A_RX * u, ry, A_RING,
                           k=A_K, skew=A_SKEW, unit=u)
        # the tail: down the stem, out along the baseline, lifting to a point
        tip = (x0 + A_TAIL_X * u, xh * A_TAIL_Y)
        tp = catmull([(xs, xh * 0.30), (xs + 4 * u, xh * 0.10), (xs + 30 * u, 26 * u),
                      (xs + 70 * u, 30 * u), (tip[0] - 30 * u, tip[1] - 14 * u), tip], tension=0.5)
        tail = stroke(tp, widths([(0.0, sw), (0.30, sw * 0.90), (0.62, sw * 0.62), (1.0, sw * 0.30)]),
                      cut1=CUT)
        return geom.ink([bowl_, stem, head, tail])

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
    S_W = float(os.environ.get("ALBO_ALD_S_W", 176.0))      # the letter's width, units
    S_WT = float(os.environ.get("ALBO_ALD_S_WT", 0.90))     # scales every key
    S_APEX = float(os.environ.get("ALBO_ALD_S_APEX", 0.46))   # the top arc's apex, x w
    S_TAIL_X = float(os.environ.get("ALBO_ALD_S_TAILX", 0.03))  # the bottom terminal, x w
    S_TAIL_Y = float(os.environ.get("ALBO_ALD_S_TAILY", 0.06))  # x xh
    S_HEAD_Y = float(os.environ.get("ALBO_ALD_S_HEADY", 0.86))  # the top terminal, x xh
    S_UL = float(os.environ.get("ALBO_ALD_S_UL", 0.22))       # the upper-left flank, x w
    S_LR = float(os.environ.get("ALBO_ALD_S_LR", 0.91))       # the lower-right turn, x w
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
    S_KEYS = [(0, 0.00, 62.0), (0, 0.32, 56.0), (0, 0.70, 26.0), (1, 0.00, 34.0),
              (2, 0.00, 52.0), (2, 0.50, 75.0), (3, 0.00, 55.0), (3, 0.60, 30.0),
              (4, 0.00, 34.0), (4, 0.60, 24.0), (4, 0.88, 50.0), (5, 0.00, 60.0)]
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


    # ------------------------------------------------------------------ CAPS
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
    CAP_BOW = float(os.environ.get("ALBO_ALD_CAP_BOW", -0.45))   # inward, as the a's
    # 2.00, MEASURED against the capitals this module does NOT redraw. CAP_W
    # is the NIB's thick and the nib takes most of it back on a near-vertical
    # stem, so the dial sits well above the width it produces: at 1.10 the H's
    # stem rendered 11 px against the untouched I and L at 22 -- half the
    # weight, and eight hairline capitals in an otherwise solid alphabet. The
    # same trap as the a's stem in round 127, and the same cure: measure the
    # rendered stroke, not the dial.
    CAP_W = float(os.environ.get("ALBO_ALD_CAP_W", 1.36))        # the nib's thick, x CS
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

    def cstem_i(x, y0, y1, bow=None, w=None):
        """A capital's stem, bowed inward and drawn on the nib -- the italic
        stem of round 127 at cap height."""
        bow = CAP_BOW if bow is None else bow
        w = CAP_W if w is None else w
        p_ = catmull([(x, y0), (x + S * bow * 0.72, y0 + (y1 - y0) * 0.30),
                      (x + S * bow, y0 + (y1 - y0) * 0.55),
                      (x + S * bow * 0.55, y0 + (y1 - y0) * 0.82), (x, y1)],
                     tension=0.5)
        ws = nib_widths(p_, CS * w / S, CS * w * 0.34 / S, CAP_CON)
        return stroke(p_, widths([(i / (len(ws) - 1), S * v) for i, v in enumerate(ws)]))

    def cdiag(a, b, w=None):
        """A capital's diagonal, on the nib: its width follows its direction,
        so the two diagonals of an A or a V are NOT the same weight."""
        w = CAP_W if w is None else w
        p_ = catmull([a, ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2), b], tension=0.5)
        ws = nib_widths(p_, CS * w / S, CS * w * 0.30 / S, CAP_CON)
        return stroke(p_, widths([(i / (len(ws) - 1), S * v) for i, v in enumerate(ws)]),
                      cut0=CUT, cut1=CUT)

    @glyph('H')
    def a_H(c):
        C = c["cap"]; x0 = CS * 0.6; x1 = x0 + 0.62 * C
        bar = stroke([(x0, C * 0.54), (x1, C * 0.58)], TH_H * 1.25)
        return geom.ink([cstem_i(x0, 0, C), cstem_i(x1, 0, C), bar])

    @glyph('N')
    def a_N(c):
        C = c["cap"]; x0 = CS * 0.6; x1 = x0 + 0.66 * C
        return geom.ink([cstem_i(x0, 0, C, w=CAP_W * N_SC), cstem_i(x1, 0, C, w=CAP_W * N_SC),
                         cdiag((x0 + CS * 0.2, C * 0.96), (x1 - CS * 0.2, C * 0.06), N_SC)])

    @glyph('U')
    def a_U(c):
        C = c["cap"]; x0 = CS * 0.6; x1 = x0 + 0.62 * C
        p_ = catmull([(x0, C), (x0 - S * 0.10, C * 0.42), (x0 + (x1 - x0) * 0.16, C * 0.10),
                      (x0 + (x1 - x0) * 0.52, -OVER * 0.4),
                      (x1 - (x1 - x0) * 0.12, C * 0.12), (x1, C * 0.46), (x1, C)],
                     tension=0.5)
        ws = nib_widths(p_, CS * CAP_W_ROUND / S, CS * CAP_W_ROUND * 0.28 / S, CAP_CON)
        return geom.ink([stroke(p_, widths([(i / (len(ws) - 1), S * v)
                                            for i, v in enumerate(ws)]), cut0=CUT, cut1=CUT)])

    @glyph('V')
    def a_V(c):
        C = c["cap"]; x0 = CS * 0.5; w = 0.66 * C
        apex = (x0 + w * 0.52, -OVER * 0.3)
        return geom.ink([cdiag((x0, C), apex, V_DIAG), cdiag(apex, (x0 + w, C), V_DIAG)])

    @glyph('A')
    def a_A(c):
        C = c["cap"]; x0 = CS * 0.4; w = 0.68 * C
        apex = (x0 + w * 0.56, C)
        left = cdiag((x0, 0), apex, A_DIAG)
        right = cdiag(apex, (x0 + w, 0), A_DIAG)
        bar = stroke([(x0 + w * 0.16, C * 0.32), (x0 + w * 0.84, C * 0.35)], TH_H * 1.20)
        # the apex flag: a real italic A carries an entry reaching LEFT
        flag = stroke([(apex[0] - CS * 1.05, C * 1.02), (apex[0] + CS * 0.18, C)],
                      widths([(0.0, S * 0.30), (0.55, S * 0.72), (1.0, S * 0.50)]), cut0=CUT)
        return geom.ink([left, right, bar, flag])

    @glyph('S')
    def a_S(c):
        C = c["cap"]; x0 = CS * 0.5; w = 0.50 * C
        p_ = catmull([(x0 + w * 0.92, C * 0.86), (x0 + w * 0.46, C * 1.00),
                      (x0 + w * 0.04, C * 0.80), (x0 + w * 0.34, C * 0.55),
                      (x0 + w * 0.70, C * 0.44), (x0 + w * 0.94, C * 0.20),
                      (x0 + w * 0.50, -OVER * 0.3), (x0, C * 0.16)], tension=0.5)
        ws = nib_widths(p_, CS * CAP_W_ROUND / S, CS * CAP_W_ROUND * 0.26 / S, CAP_CON)
        return geom.ink([stroke(p_, widths([(i / (len(ws) - 1), S * v)
                                            for i, v in enumerate(ws)]), cut0=CUT, cut1=CUT)])

    @glyph('G')
    def a_G(c):
        """A G opens on the RIGHT, between about one and four o'clock; its bar
        comes INWARD from the right terminal, and a short stem joins the two.

        The first cut ran its arc from -34 to 250 degrees, which covers the
        right side and leaves the gap at the BOTTOM -- so the letter read as a
        broken O with a spur stuck on its flank. Compared against Pagella and
        Poetica: both open at the right, both turn their bar in toward the
        counter, and neither lets it project past the bowl.
        """
        C = c["cap"]; rx = 0.34 * C; ry = C / 2 + OVER * 0.4; cx = CS * 0.6 + rx
        A0, A1 = math.radians(G_OPEN0), math.radians(G_OPEN1)
        p_ = superellipse(cx, C / 2, rx, ry, A0, A1, BOWL_K)
        ws = nib_widths(p_, CS * CAP_W_ROUND / S, CS * CAP_W_ROUND * 0.30 / S,
                        CAP_CON, smooth=7)
        arc = stroke(p_, widths([(i / (len(ws) - 1), S * v) for i, v in enumerate(ws)]),
                     cut0=CUT, cut1=CUT)
        # the terminal the arc ends on, and the bar turning in from it
        ex = cx + rx * math.cos(A1); ey = C / 2 + ry * math.sin(A1)
        by = C * G_BAR
        stem_ = stroke([(ex, ey), (ex + (cx + rx * 0.92 - ex) * 0.5, by)],
                       widths([(0.0, CS * 0.52), (1.0, CS * 0.86)]))
        bar = stroke([(cx + rx * 0.96, by), (cx + rx * G_BAR_IN, by + C * 0.012)],
                     widths([(0.0, TH_H * 1.30), (1.0, TH_H * 0.70)]), cut1=CUT)
        return geom.ink([arc, stem_, bar])

    @glyph('Q')
    def a_Q(c):
        C = c["cap"]; rx = 0.35 * C; cx = CS * 0.6 + rx
        ring_ = ring(cx, C / 2, rx, C / 2 + OVER * 0.4, floor=S * FLOOR)[0]
        tail = catmull([(cx + rx * 0.12, C * 0.30), (cx + rx * 0.62, C * 0.10),
                        (cx + rx * 1.12, -C * 0.10), (cx + rx * 1.46, -C * 0.22)],
                       tension=0.5)
        wt = pen_widths(tail, floor=S * FLOOR)
        return geom.ink([ring_, stroke(tail, lambda t: wt(t) * (1.15 - 0.80 * t), cut1=CUT)])


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
