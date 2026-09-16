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
    # it is the construction a_i already uses -- an oval lying on the pen's own
    # angle, centre I_DOT_Y (0.39 xh) above the x-line -- and NOT Poetica's,
    # which sits at 1.35 xh and is a much steeper oval. An i and a j on the
    # same page have to wear the same dot.
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
        parts = [body, wedge_head(xs, xh * 0.875)]
        a = math.radians(HEAD_DEG); L = S * I_DOT_W
        dx, dy = math.cos(a) * L, math.sin(a) * L
        cy = xh + I_DOT_Y * xh
        parts.append(stroke([(xs - dx * 0.5, cy - dy * 0.5), (xs + dx * 0.5, cy + dy * 0.5)],
                            S * I_DOT_T, cut0=CUT, cut1=CUT))
        return geom.ink(parts)

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
    Y_TAIL_X = d_dial("Y_TAIL_X", 118.0)   # the tail's leftmost, units
    Y_TAIL_Y = d_dial("Y_TAIL_Y", -0.62)   # its floor, x xh

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
        tail = d_pen([P(322, 0.885), P(336, 0.825), P(341, 0.74),
                      P(334, 0.50), P(307, 0.25), P(274, 0.10), P(252, -0.05),
                      P(230, -0.22), P(190, -0.40), P(TX + 34, TY),
                      P(TX, TY + 0.055)],
                     [(0.00, 48), (0.05, 44), (0.13, 34),
                      (0.35, 29), (0.70, 26), (0.92, 30), (1.00, 16)], u, tw=Y_TW)
        ball = d_ball(P, u, 308, 0.895, 32 * Y_TW)
        return geom.ink([thick, tail, ball])

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
    Z_W = d_dial("Z_W", 1.03)
    Z_TW = d_dial("Z_TW", 1.12)
    Z_DIAG = d_dial("Z_DIAG", 27.0)   # the diagonal's width, units

    @glyph('z')
    def a_z(c):
        P, u = d_frame(c, Z_W); D = Z_DIAG
        top = d_pen([P(8, 0.755), P(26, 0.855), P(64, 0.895), P(150, 0.918),
                     P(240, 0.940), P(266, 0.962)],
                    [(0.00, 20), (0.12, 44), (0.30, 60), (0.75, 60),
                     (0.92, 52), (1.00, 40)], u, tw=Z_TW)
        diag = d_pen([P(258, 0.95), P(212, 0.75), P(152, 0.50), P(89, 0.25),
                      P(48, 0.09), P(32, 0.012)],
                     [(0.00, D * 1.45), (0.12, D * 1.09), (0.50, D),
                      (0.88, D * 1.15), (1.00, D * 1.52)], u, tw=Z_TW)
        bot = d_pen([P(24, 0.025), P(90, 0.028), P(180, 0.038), P(262, 0.058),
                     P(312, 0.092), P(340, 0.145)],
                    [(0.00, 52), (0.12, 60), (0.55, 60), (0.80, 46),
                     (0.92, 32), (1.00, 22)], u, tw=Z_TW)
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
