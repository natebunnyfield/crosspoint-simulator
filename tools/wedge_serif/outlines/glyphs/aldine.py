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
    HM_DOT_LEN = _hm("DOT_LEN", 84.0)   # its long axis, units
    HM_DOT_TH = _hm("DOT_TH", 44.0)     # its short axis, units
    HM_DOT_CY = _hm("DOT_CY", 1.400)    # its center, x xh above the baseline

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

    def hm_head(c, xc, ytop):
        """The entry stroke: up from the lower left, across the stem's top.
        Tapered at the tip -- Flanker's detached tip reads 34 units across a
        stroke running at 53 degrees, so 34*sin53 = 27 perpendicular -- and
        bowed, so its underside is hollow the way the reference's is."""
        u = hm_u(c); xh = c["xh"]; sw = HM_STEMW * u
        # the END is the CENTERLINE's end: a stroke this thick running at ~53
        # degrees puts its upper edge 0.30 of its width above the centerline,
        # and the references' ink top is exactly the x-line (Flanker's n and i
        # both bbox at 429) -- the head does not rise above it.
        tip = (xc - sw / 2 - HM_HEAD_L * u, ytop - HM_HEAD_D * xh)
        end = (xc + HM_HEAD_R * sw, ytop - 0.30 * HM_HEAD_W * u)
        mid = ((tip[0] + end[0]) / 2, (tip[1] + end[1]) / 2 + HM_HEAD_BOW * xh)
        p = catmull([tip, mid, end], tension=0.5)
        return stroke(p, widths([(0.0, HM_HEAD_T * u), (0.55, HM_HEAD_W * u),
                                 (1.0, HM_HEAD_W * 0.86 * u)]), cut0=CUT, cut1=CUT)

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

    def hm_arch(c, x0, x1):
        """ONE movement: out of the stem low, up as a hairline, over the top,
        down into the next stem. Not a shoulder turned near the top."""
        u = hm_u(c); xh = c["xh"]; P = x1 - x0; sw = HM_STEMW * u
        # the landing runs BELOW the stem's own top (0.86 xh) so the arch's
        # blunt end face is buried inside it; ending them level left a hairline
        # white slit across the junction on the m's second and third stems.
        K = [(0.0, HM_SPRING)] + HM_ARCH_K + [(0.930, HM_ARCH_TOP), (1.0, 0.780)]
        p = catmull([(x0 + fx * P, fy * xh) for fx, fy in K], tension=0.5)
        t = HM_ARCH_T * u
        return stroke(p, widths([(0.00, sw * 0.94), (0.14, t * 1.15), (0.36, t),
                                 (0.60, t * 1.30), (0.80, t * 2.00), (1.00, sw)]))

    @glyph('i')
    def a_i(c):
        """Stem, head, exit, dot. The scan's i is the family's cleanest single
        stroke, and the dot is one touch of the nib: 89 x 64 units on the scan
        (rows 1.35-1.45), 98 x 98 in Flanker, centered 1.40 x xh above the
        baseline in both. Drawn 92 x 70 on the pen's own angle."""
        xh = c["xh"]; u = hm_u(c); x = S * 1.0
        parts = [hm_stem(c, x, 0, xh), hm_head(c, x, xh), hm_exit(c, x)]
        parts.append(geom.poly(superellipse(x, HM_DOT_CY * xh, HM_DOT_LEN * u / 2,
                                            HM_DOT_TH * u / 2, 0.0, 2 * math.pi, 2.1,
                                            rot=math.radians(HEAD_DEG))))
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

    @glyph('m')
    def a_m(c):
        """Three stems at one pitch -- the doc's "three stems at 70/70/70".
        One head, on the first; one exit, on the last."""
        xh = c["xh"]; x0 = S * 1.0; d = HM_PITCH * xh; x1 = x0 + d; x2 = x1 + d
        return geom.ink([hm_stem(c, x0, 0, xh), hm_head(c, x0, xh),
                         hm_arch(c, x0, x1), hm_arch(c, x1, x2),
                         hm_stem(c, x1, 0, xh * 0.86, cut=False),
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
        E = lambda f: mid + (f - mid) * E_EYE   # the eye's flanks, about its center
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
    A_STEM_X = float(os.environ.get("ALBO_ALD_A_STEM_X", 317.0))   # stem center, units
    A_STEM_W = float(os.environ.get("ALBO_ALD_A_STEMW", 70.0))     # units
    A_STEM_TOP = float(os.environ.get("ALBO_ALD_A_TOP", 0.97))     # x xh
    A_RX = float(os.environ.get("ALBO_ALD_A_RX", 155.0))            # bowl outer half-width, units
    A_CY = float(os.environ.get("ALBO_ALD_A_CY", 215.0))            # bowl center height, units
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
