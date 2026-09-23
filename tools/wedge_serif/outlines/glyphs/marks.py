"""The 30 marks, on the record's geometry (round 41: fitted on their full
extent), the & and @ real glyphs (round 42)."""
import math, os
import shapely.affinity as aff
from . import glyph, GLYPHS
from .. import geom, pen
from .. import primitives as PR
from ..geom import cubic, line, superellipse, catmull
from ..primitives import stem, ring, stroke, pen_widths, widths, dot, wedge, diagonal, bar, beak
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
# ROUND 362 -- THE MARKS' OWN DOT SIZE, and why it is a multiplier rather
# than a change to DOT_R. Owner 2026-09-23, after the survey: Albo's period
# reads 0.19 of the x-height where Baskerville, Hoefler, Times and Georgia run
# 0.24-0.28, and the comma, colon and semicolon are small with it.
#
# `DOT_R` is 0.62 x S and it is NOT the marks' alone: the i's and j's tittles
# take it (italic.py) and so do the dieresis and the dot accents
# (accents.py). Raising it would re-cut the tittle on every i in the face,
# which is a bigger change than the one that was asked for and is not
# obviously wanted -- a tittle is read at the top of an x-height, a period on
# the baseline between words. So the marks scale their own copy and the
# tittle is untouched. If the two should stay locked together, that is a
# separate ruling and this dial is where it would be made.
MARK_DOT = float(os.environ.get("ALBO_MARK_DOT", 1.0))   # x DOT_R, punctuation only
EXCL_BOT = float(os.environ.get("ALBO_EXCL_BOT", 0.74))  # the !'s profile at the foot, x the pen (round 364: 0.55 before)
EXCL_TOP = float(os.environ.get("ALBO_EXCL_TOP", 1.38))  # ...and at the cap (round 364: 1.05 before). 1.38 puts the ! thick at 1.24 x the face's stem, against the references' 1.10-1.30
EXCL_DOT = float(os.environ.get("ALBO_EXCL_DOT", 1.0))   # the !'s dot, x the marks' dot
EXCL_NIB = int(os.environ.get("ALBO_EXCL_NIB", 1))       # 1 = the dot is a pressed nib; 0 = the old round dot
EXCL_NIB_LEN = float(os.environ.get("ALBO_EXCL_NIB_LEN", 0.62))  # half the press's length along the nib's edge, x the dot radius
EXCL_NIB_W = float(os.environ.get("ALBO_EXCL_NIB_W", 1.15))      # the press's thickness across the edge, x the dot radius
MDOT = DOT_R * MARK_DOT

@glyph('.')
def g_period(c): return dot(MDOT, MDOT, MDOT)
# ROUND 362 -- THE COMMA'S REACH. Measured 0.38 of the x-height tall against
# the references' 0.59-0.70, and 0.20 wide against their 0.33-0.35: it is the
# most undersized mark after the quotes. COMMA_LEN scales how far the tail
# runs below the dot, COMMA_W how far it swings across; 1.0 is the shipped
# tail exactly, so an unset build is bit-identical.
COMMA_LEN = float(os.environ.get("ALBO_COMMA_LEN", 1.0))
COMMA_W = float(os.environ.get("ALBO_COMMA_W", 1.0))

def comma_tail(x, y, up=True, w0=0.9, w1=0.3):
    _L, _W = COMMA_LEN, COMMA_W
    if up: tail = cubic((x + S * 0.1, y - S * 0.35 * _L), (x + S * 0.1, y - S * 1.05 * _L), (x - S * 0.3 * _W, y - S * 1.45 * _L), (x - S * 0.6 * _W, y - S * 1.75 * _L))
    # mirrored in x only (round 51 flipped y too, sending the left quote's
    # tail UP past the cap height instead of down like a real turned comma --
    # the defect behind the misaligned "‘"/"“"): the tail still descends,
    # it just curls to the right instead of the left.
    else:  tail = cubic((x - S * 0.1, y - S * 0.35 * _L), (x - S * 0.1, y - S * 1.05 * _L), (x + S * 0.3 * _W, y - S * 1.45 * _L), (x + S * 0.55 * _W, y - S * 1.75 * _L))
    return stroke(tail, pen_widths(tail, lambda t: w0 - (w0 - w1) * t))   # round 51: the pen x (0.9 - 0.6 t)
@glyph(',')
def g_comma(c): return geom.ink([dot(MDOT, MDOT, MDOT), comma_tail(MDOT, MDOT)])
@glyph(':')
def g_colon(c): return geom.ink([dot(MDOT, MDOT, MDOT), dot(MDOT, XH - MDOT, MDOT)])
@glyph(';')
def g_semicolon(c): return geom.ink([dot(MDOT, MDOT, MDOT), comma_tail(MDOT, MDOT), dot(MDOT, XH - MDOT, MDOT)])
@glyph('!')
def g_exclam(c):
    # ROUND 364 -- THE STEM THICKENED, THEN THE DOT BALANCED AGAINST IT.
    # Owner 2026-09-23: *"thicken exclamation stem to better match letters,
    # then adjust dot to optically balance against it"* -- in that order, and
    # the order matters, because the dot's right size depends on the stem it
    # stands under.
    #
    # MEASURED FIRST, and the obvious reading was wrong. The !'s stroke MEDIAN
    # against the face's own stem reads 0.76 where Baskerville, Hoefler, Times
    # and Georgia run 0.75-0.91 -- in band, at the low end. What is out of band
    # is the TAPER'S TOP: the ! is a wedge, and at its widest Albo reads 0.93
    # of the stem where those four run 1.10-1.30. So the fault is not that the
    # mark is thin everywhere; it is that it never gets thick.
    #
    # EXCL_BOT and EXCL_TOP are the profile's two ends, x the pen. Shipped
    # 0.55 / 1.05 is round 51's original; an unset build is bit-identical.
    # EXCL_DOT scales the dot against MDOT, and is the second half of the ask.
    # ROUND 365 -- THE DOT IS A PRESSED NIB, NEVER A ROUND ONE. Owner
    # 2026-09-23: *"it needs to be done with a nib, never rounded."* So it is
    # not `dot()` at all -- not the superellipse and not DOT_STYLE 1's punched
    # dot, both of which are circles with the corners worked. It is the pen
    # set down once: a short run along the stem's own direction, taking the
    # pen's width there and the family's cut at both ends, which leaves the
    # four-sided mark a broad nib actually makes.
    C = CAP(c); x = MDOT
    _r = MDOT * EXCL_DOT
    if EXCL_NIB:
        # THE FOOTPRINT ITSELF, not a stroke with cuts on it. The first cut ran
        # a short vertical stroke and let the two pen cuts meet, which ate most
        # of the path and left a lopsided wedge -- visible the moment it was
        # rendered. A broad nib set down once leaves a PARALLELOGRAM: its long
        # edge lies along the nib's own angle (the face's stress, 26 degrees
        # here) and its short edge is the nib's thickness.
        _th = pen.PEN.stress
        _ca, _sa = math.cos(_th), math.sin(_th)
        _L = _r * EXCL_NIB_LEN * 2.0        # half the mark's length, along the edge
        _W = _r * EXCL_NIB_W * 0.5          # half its thickness, across
        _dot = geom.poly([(x + _ca * _L - _sa * _W, _r + _sa * _L + _ca * _W),
                          (x + _ca * _L + _sa * _W, _r + _sa * _L - _ca * _W),
                          (x - _ca * _L + _sa * _W, _r - _sa * _L - _ca * _W),
                          (x - _ca * _L - _sa * _W, _r - _sa * _L + _ca * _W)])
        y0 = 2 * _r + 0.8 * S
    else:
        _dot = dot(x, _r, _r)
        y0 = 2 * _r + 0.8 * S
    _p = line((x, y0), (x, C))
    return geom.ink([_dot,
                     stroke(_p, pen_widths(_p, lambda t: EXCL_BOT + (EXCL_TOP - EXCL_BOT) * t), cut1=CUT)])
@glyph('?')
def g_question(c):
    """Owner 2026-09-13: "make more variations of '?' for me to choose
    from." QUESTION_VARIANT picks one of QUESTION_VARIANTS (env
    FJORD_Q_VARIANT for the ladder builds); 0 is the round-77 hook (the
    marks agent's, landed). All on the bowl profile (the pen's thin is the
    floor at this contrast), the dot on the marks' rule (DOT_R, bottom at
    0), the terminal in the family's pen cut unless the variant says a
    beak."""
    return QUESTION_VARIANTS[QUESTION_VARIANT][1](c)

def Q_DOT_CLEAR(r=None, half=None):
    """Where the question mark's descent STOPS, so its dot stays a dot.

    Round 100: it was a fraction of the cap height (C * 0.22), which does not
    move with the weight -- at the Bold's stem the descent's own half-width
    plus the dot's radius closed the gap and the ? merged into one contour,
    losing its dot. The exclamation has always used the family's rule for a
    stroke standing over a dot (`2 * DOT_R + 0.8 * S`, round 51); the
    question mark uses it now too, so the two marks clear identically at
    every weight."""
    r = MDOT if r is None else r
    return 2 * r + (half or 0) + 0.55 * S

def _q_common(c, pts, prof, tension=0.62, cut0=CUT, beak_start=False, floor=0.5, w=380):
    C = CAP(c)
    hook = catmull(pts, tension=tension)
    wf = PR.bowl_widths(hook, widths(prof), floor=S * floor)
    body = stroke(hook, wf, cut0=None if beak_start else cut0, cut1=CUT)
    # round 100: the dot's gap under the hook's terminal must clear at the
    # BOLD too -- at stem 107 the two merged and the ? lost its dot. The
    # hook's own floor is S * `floor`, so the clearance is taken from there.
    parts = [dot(w * 0.5, DOT_R, DOT_R), body]
    if beak_start: parts.append(beak(hook, wf(0.0), at_start=True))
    return geom.ink(parts)

def _q0(c):   # round 77's, the marks agent's hook
    C = CAP(c); w = 380
    end_y = C * 0.2 + max(0.0, (S - 94) * 2.2)
    hook = catmull([(w * 0.14, C * 0.60), (w * 0.00, C * 0.86), (w * 0.32, C * 1.00), (w * 0.70, C * 0.92), (w * 0.60, C * 0.52), (w * 0.5, end_y)], tension=0.62)
    return geom.ink([dot(w * 0.5, DOT_R, DOT_R), stroke(hook, pen_widths(hook, widths([(0.0, 0.40), (0.30, 1.0), (0.58, 0.95), (1.0, 0.55)])), cut0=CUT, cut1=CUT)])
def _q1(c):   # the same gesture on the bowl profile: no hairline anywhere
    C = CAP(c); w = 380; e = Q_DOT_CLEAR()
    return _q_common(c, [(w * 0.14, C * 0.60), (w * 0.00, C * 0.86), (w * 0.32, C * 1.00), (w * 0.70, C * 0.92), (w * 0.60, C * 0.52), (w * 0.5, e)], [(0.0, 0.55), (0.30, 1.0), (0.60, 0.95), (1.0, 0.7)])
def _q2(c):   # garalde: a wide open hook, the terminal low at the left, a short straight stem to the dot
    C = CAP(c); w = 400; e = Q_DOT_CLEAR()
    return _q_common(c, [(w * 0.08, C * 0.66), (w * 0.02, C * 0.84), (w * 0.34, C * 1.00), (w * 0.74, C * 0.90), (w * 0.62, C * 0.58), (w * 0.50, C * 0.40), (w * 0.50, e)], [(0.0, 0.5), (0.28, 1.0), (0.55, 1.0), (0.80, 0.75), (1.0, 0.75)], tension=0.55)
def _q3(c):   # tall and narrow: the hook higher, the descent longer
    C = CAP(c); w = 330; e = Q_DOT_CLEAR()
    return _q_common(c, [(w * 0.12, C * 0.62), (w * 0.02, C * 0.86), (w * 0.36, C * 1.00), (w * 0.78, C * 0.90), (w * 0.62, C * 0.56), (w * 0.52, e)], [(0.0, 0.5), (0.30, 1.0), (0.62, 0.95), (1.0, 0.7)])
def _q4(c):   # the beak: the terminal is the C's beak, the hook squarer at the shoulder
    C = CAP(c); w = 380; e = Q_DOT_CLEAR()
    return _q_common(c, [(w * 0.16, C * 0.60), (w * 0.02, C * 0.84), (w * 0.34, C * 1.00), (w * 0.76, C * 0.94), (w * 0.66, C * 0.54), (w * 0.52, e)], [(0.0, 0.7), (0.30, 1.0), (0.62, 0.95), (1.0, 0.7)], beak_start=True)
def _q5(c):   # Albertus-like: heavier, the shoulder angular, the descent nearly straight, the terminal a heavy cut
    C = CAP(c); w = 380; e = Q_DOT_CLEAR()
    return _q_common(c, [(w * 0.12, C * 0.64), (w * 0.02, C * 0.88), (w * 0.38, C * 1.00), (w * 0.78, C * 0.90), (w * 0.60, C * 0.50), (w * 0.52, e)], [(0.0, 0.85), (0.25, 1.0), (0.60, 1.0), (1.0, 0.85)], tension=0.45, floor=0.65)
def _q6(c):   # the descent as a vertical stem with a wedge foot above the dot, the hook lighter
    C = CAP(c); w = 380; e = Q_DOT_CLEAR()
    g = _q_common(c, [(w * 0.14, C * 0.62), (w * 0.02, C * 0.86), (w * 0.34, C * 1.00), (w * 0.72, C * 0.92), (w * 0.56, C * 0.58), (w * 0.52, e + 20)], [(0.0, 0.5), (0.30, 1.0), (0.58, 0.9), (1.0, 0.6)])
    st = stem(w * 0.52, e, C * 0.45, top=None, foot='both', ent_span=(e, C * 0.45), foot_len=0.55)
    return geom.ink([g, st])
def _q7(c):   # curled: the terminal turns in toward the counter, a teardrop
    C = CAP(c); w = 380; e = Q_DOT_CLEAR()
    return _q_common(c, [(w * 0.24, C * 0.72), (w * 0.10, C * 0.66), (w * 0.02, C * 0.82), (w * 0.34, C * 1.00), (w * 0.74, C * 0.92), (w * 0.62, C * 0.54), (w * 0.50, e)], [(0.0, 0.95), (0.12, 0.6), (0.34, 1.0), (0.62, 0.95), (1.0, 0.7)], tension=0.6)
def _q8(c):   # the original (round-19 to 76) question mark, Albertus heavy and larger
    C = CAP(c); w = 380 * Q8_SCALE
    # round 100: the descent STOPS at the family's dot-clearance rule rather
    # than at a fraction of the cap height. This hook's floor is a heavy
    # 0.78 S, so at the Bold its own half-width plus the dot's radius closed
    # the gap and the ? merged into one contour -- it lost its dot, in the
    # bold only, which no render of the Regular could show.
    end_y = max(C * 0.22, Q_DOT_CLEAR(r=DOT_R * 1.1, half=S * Q8_FLOOR / 2))
    # ROUND 233 -- TWO STRAY CORNERS AND A BULGE. Owner 2026-09-18 (R49): *"fix
    # stray corner in bottom right of stroke, fix bad bulge on left."* Measured
    # on the spine at 4 px/unit:
    # - THE BULGE: the width plan reached 1.0 at t 0.15, where the left arm still
    #   rises at 60 degrees and the bowl profile is near its thick, so the arm
    #   went floor 65.5 -> 76.1 (t 0.136, at (90, 615)) -> floor 65.5 again at
    #   the top: a +16% swell between two equal widths. The plan now holds 0.7
    #   through the left arm and the top (t 0..0.25) and rises to 1.0 by the
    #   right side (t 0.5), so the arm and the top run at the floor and the
    #   weight lives on the right and the descent, where a broad nib puts it.
    # - THE FIRST CORNER, the one in his box: the inner edge kinked at (187, 633)
    #   where that width fell back through the floor (`max(w, floor)` is C0)
    #   while the spine turned at radius 76 against a half-width of 38. The
    #   plan above takes the width change out of the turn; `_smooth_wf` then
    #   rounds every remaining floor crossing over +/-4 samples, because the
    #   right side's rise through the floor at t 0.41 would otherwise kink the
    #   same way (2 units per sample, a 5-degree jog in each edge).
    # - THE SECOND CORNER, at the descent's end above the dot: the spine's last
    #   leg (218, 218) -> (218, 194) was 24 units for a 36-degree swing, radius
    #   7 against a half-width of 42 -- the offset folded and the end face came
    #   out on a tangent of -48 degrees, a spike 40 units below the plan
    #   (bottom at 154, not 179). A catmull cannot arrive vertical there: its
    #   tangent at a point is the chord between the neighbours, and the
    #   neighbour above sits 105 units to the right, so every knee tried (a
    #   longer last leg, a cubic hung off the knee) folded at radius 20-37.
    #   The descent is now ONE cubic from the shoulder point (0.74 w, 0.5 C),
    #   leaving on the catmull's own tangent there and arriving on the
    #   vertical at (0.5 w, end_y): minimum radius 84, end tangent -93
    #   degrees, and at most 8 units off the old spine anywhere on the descent.
    # Nothing else moved: the five upper spine points, Q8_SCALE, Q8_FLOOR, the
    # dot and the clearance rule are as they were.
    upper = catmull([(w * 0.08, C * 0.74), (w * 0.28, C * 0.97), (w * 0.62, C * 0.98), (w * 0.88, C * 0.74), (w * 0.74, C * 0.5)], tension=0.5)
    P = upper[-1]; tn = geom.tangents(upper)[-1]; E = (w * 0.5, end_y); L = math.dist(P, E)
    hook = geom.resample(upper + cubic(P, (P[0] + tn[0] * Q8_TAIL_K1 * L, P[1] + tn[1] * Q8_TAIL_K1 * L), (E[0], E[1] + Q8_TAIL_K2 * L), E)[1:])
    wf = _smooth_wf(PR.bowl_widths(hook, widths([(0.0, 0.7), (0.25, 0.7), (0.5, 1.0), (0.8, 1.0), (1.0, 1.05)]), floor=S * Q8_FLOOR), len(hook) - 1)
    return geom.ink([dot(w * 0.5, DOT_R * 1.1, DOT_R * 1.1), stroke(hook, wf, cut0=CUT, cut1=CUT)])
def _smooth_wf(wf, n, passes=4):
    """A width function sampled at the spine's n+1 points and smoothed by a
    [1 2 1]/4 kernel `passes` times, so a floor's C0 crossing becomes a curve
    over about +/-`passes` samples (44 units at 4 passes) instead of a corner
    in both edges. The ends are held."""
    ws = [wf(i / n) for i in range(n + 1)]
    for _ in range(passes):
        ws = [ws[0]] + [(ws[i - 1] + 2 * ws[i] + ws[i + 1]) / 4 for i in range(1, n)] + [ws[-1]]
    return lambda t: ws[min(n, int(round(t * n)))]
Q8_SCALE = 1.15   # owner 2026-09-13: "make the question mark back into its original question mark shape and albertus heavy, larger to read correctly in a sentence"
Q8_FLOOR = 0.78   # the hook never under 0.78 S: Albertus weight
Q8_TAIL_K1, Q8_TAIL_K2 = 0.35, 0.45   # round 233: the descent cubic's handles, x its chord (swept 0.3-0.6 each; this pair had the largest minimum radius, 84)
QUESTION_VARIANTS = [('original, Albertus heavy', _q8), ('round 77', _q0), ('bowl profile', _q1), ('garalde wide', _q2), ('tall narrow', _q3), ('beak terminal', _q4), ('Albertus heavy', _q5), ('curled terminal', _q7)]   # a stem-foot variant was built and dropped: its foot wedges read as a claw
QUESTION_VARIANT = int(os.environ.get('FJORD_Q_VARIANT', 0))

# ROUND 362 -- THE QUOTES ARE THE WORST OF THE MARKS, by a distance: 0.26 of
# the x-height tall against the references' 0.57-0.71, and 0.13 wide against
# their 0.22-0.25 -- LESS THAN HALF the smallest reference on both. QUOTE_SIZE
# scales the shared body; 1.0 is the shipped mark exactly.
# QUOTE_SIZE ALONE ONLY SOLVES HALF THE GLYPH, which the measurement caught:
# swept 1.0 -> 2.6 the apostrophe's HEIGHT runs 0.259 -> 0.611 of the
# x-height, straight through the references' 0.57-0.71, while its WIDTH sits
# at 0.126 -> 0.131 and never reaches their 0.22-0.25. The straight quote's
# stroke is `TH_V * 0.8`, which no size dial touched, so a taller mark was
# still a hairline. QUOTE_W is that missing half; the two are set together
# per arm because a quote is one mark, not a height and a width.
QUOTE_SIZE = float(os.environ.get("ALBO_QUOTE_SIZE", 1.0))
QUOTE_W = float(os.environ.get("ALBO_QUOTE_W", 1.0))
QUOTE_BODY = 2 * DOT_R * QUOTE_SIZE   # straight and curly quotes share this body height, top-aligned to CAP
# ROUND 222 -- THE ITALIC'S QUOTES SIT LOWER. Owner 2026-09-18, on the round-221
# proof: *"too much space between apostrophe and previous and next letters.
# compare with other reference fonts."* Measured at one x-height, Albo's
# apostrophe hangs from CAP (top 1.57 xh) like Times and New York, while the
# faces whose marks visibly NEST -- Georgia 1.52, Pagella 1.39, Poetica 1.09 --
# sit lower. And the bearings alone cannot get there: at cap height the mark's
# neighbours are capitals and ascenders, which it grazes (14 pairs flagged at
# lsb -40 / rsb -140) while the lowercase it usually stands beside is far
# below. Lowering the mark shortens the diagonal to an x-height letter's top
# without moving it toward a capital's stem. Units below CAP; italic only.
QUOTE_DROP = float(os.environ.get("ALBO_ALD_QUOTE_DROP", "50"))
def _qdrop(): return QUOTE_DROP if pen.ITALIC else 0.0
DQ_GAP = 1.8   # round 94 (owner: "give more space for double quotes so they don't touch"): the two marks' centers, x S (1.3 before: a 48-unit gap, 2.6 px at 13 pt, gray between them)
# ROUND 233 -- CALLIGRAPHIC OPTIONS FOR THE STRAIGHT QUOTES. Owner 2026-09-18
# (R51 ', R52 "): *"give me calligraphic options."* Today's mark is one
# vertical stroke, TH_V x 0.8 wide, QUOTE_BODY tall, one pen cut at its foot.
# ALBO_QUOTE_OPT picks; every option keeps the mark's TOP at the cap (less the
# italic's QUOTE_DROP), the body height where it can, and the x of the stroke:
#   a  today, byte-identical
#   b  a WRITTEN TICK: the nib lands full at the top (pen cut) and lifts away
#      down and to the left, the stroke bowing slightly and thinning to 0.4 --
#      an apostrophe as a pen makes it in one touch
#   c  the family's WEDGE: the top face full width, the two sides falling on
#      the serif's own concave bracket to an apex a little left of centre
#   d  COMMA-SHAPED: the curly quote's own dot-and-tail (the , turned to hang
#      from the top), so the straight and curly marks are one drawing
#   e  PEN-CUT ENDS: today's stroke with the pen cut at both ends
# ROUND 251. Owner 2026-09-18: *"ALBO_QUOTE_OPT b but slightly randomized and
# taller."* b ships on the roman (the italic keeps a). Taller: the written
# tick's body is QUOTE_B_TALL x QUOTE_BODY, the top still at the cap.
# Randomized: NOT a jitter -- a TABLE, per docs/albo-imperfections.md -- one
# row per mark, (body scale, lean scale): the single quote takes row 0, the
# double quote's two marks rows 1 and 2, so the pair differs by a few units
# in height and in how far the stroke leans, and every build is the same.
QUOTE_OPT = os.environ.get("ALBO_QUOTE_OPT", "a" if pen.ITALIC else "b")
QUOTE_B_TALL = float(os.environ.get("ALBO_QUOTE_B_TALL", 1.15))
QUOTE_B_VAR = [(1.00, 1.00), (0.96, 1.12), (1.03, 0.90)]   # (body x, lean x): rows 0, 1, 2 -- about 5 units of height and 3 of lean between the marks of a pair
def straight_quote(c, x, k=0):
    """One straight-quote mark at x, per QUOTE_OPT (see above); k is the
    mark's row in QUOTE_B_VAR (option b only)."""
    C = CAP(c) - _qdrop(); top, bot = C, C - QUOTE_BODY; w = TH_V * 0.8 * QUOTE_W; opt = QUOTE_OPT
    if opt == "b":
        bs, ls = QUOTE_B_VAR[k % len(QUOTE_B_VAR)]
        body = QUOTE_BODY * QUOTE_B_TALL * bs; bot = top - body
        dx = S * 0.16 * ls
        p = cubic((x + dx * 0.5, top), (x + dx * 0.35, top - body * 0.45), (x - dx * 0.2, bot + body * 0.35), (x - dx * 0.6, bot))
        # round 362: option b is what the ROMAN ships and it never touched `w`
        # -- it scales straight off TH_V -- so QUOTE_W was inert here until
        # this line carried it. Caught by laddering the dial rather than by
        # reading the branch.
        return stroke(p, pen_widths(p, widths([(0.0, 0.85), (0.5, 0.8), (1.0, 0.5)]), scale=TH_V * QUOTE_W / pen.PEN.th((0.0, 1.0))), cut0=CUT)
    if opt == "c":
        A = (x - w / 2, top); B = (x + w / 2, top); P = (x - w * 0.18, bot)
        # the bracket: a concave quadratic from each top corner to the apex, its control 0.65 of the way down the straight side and pulled INTO the wedge
        def side(Q):
            cx_, cy_ = Q[0] + (P[0] - Q[0]) * 0.65, Q[1] + (P[1] - Q[1]) * 0.65
            inward = (P[0] - Q[0]) * 0.25
            return geom.quad(Q, (cx_ + inward, cy_), P)
        return geom.poly(side(A) + side(B)[::-1][1:])
    if opt == "d":
        y = C - DOT_R
        return geom.ink([dot(x, y, DOT_R), comma_tail(x, y, True, 0.85, 0.3)])
    if opt == "e":
        return stroke(line((x, bot), (x, top)), w, cut0=CUT, cut1=CUT)
    return stroke(line((x, bot), (x, top)), w, cut0=CUT)
@glyph("'")
def g_quotesingle(c): return straight_quote(c, S * 0.5)
@glyph('"')
def g_quotedbl(c): return geom.ink([straight_quote(c, S * 0.5 + i * S * DQ_GAP, k=i + 1) for i in (0, 1)])
def quote(c, x, up):
    """The curly quotes: the comma's own dot+tail (same DOT_R body as every
    other mark), turned to hang from the top instead of sitting on the
    baseline -- top of the dot flush with CAP, matching the straight
    quotes' top and body height exactly."""
    _r = DOT_R * QUOTE_SIZE          # round 362: the curly pair scales with the straight
    C = CAP(c) - _qdrop(); y = C - _r
    return geom.ink([dot(x, y, _r), comma_tail(x, y, up, 0.85, 0.3)])
@glyph('’')
def g_quoteright(c): return quote(c, S * 0.7, True)
@glyph('‘')
def g_quoteleft(c): return quote(c, S * 0.7, False)
@glyph('”')
def g_quotedblright(c): return geom.ink([quote(c, S * 0.7, True), quote(c, S * (0.7 + DQ_GAP), True)])
@glyph('“')
def g_quotedblleft(c): return geom.ink([quote(c, S * 0.7, False), quote(c, S * (0.7 + DQ_GAP), False)])
# ROUND 233 -- CALLIGRAPHIC OPTIONS FOR THE HYPHEN. Owner 2026-09-18 (R53):
# *"give me calligraphic options."* Today's hyphen is a plain bar, TH_H thick,
# square ends, at 0.34 C. ALBO_HYPHEN_OPT picks; the en and em dashes go
# through the same `dash` so they take the option with it and the three stay
# one drawing. Every option keeps the bar's length and its height:
#   a  today, byte-identical
#   b  PEN-CUT ENDS: both end faces sheared at the family's 20 degrees
#   c  a SLIGHT RISE: the bar climbs HYPHEN_RISE_DEG to the right, as a written
#      dash does, pen-cut ends
#   d  MODULATED: thinner at the ends (0.55) and full in the middle, the
#      pressure of one stroke, square ends
#   e  a SHORT WEDGE: full at the left face (pen cut), tapering to 0.3 at the
#      right -- the family's wedge lying down
# ROUND 251. Owner 2026-09-18: *"ALBO_HYPHEN_OPT c but much less rise, 1 degree
# for longest dash."* c ships on the roman (the italic keeps a). The rise is
# now the SAME NUMBER OF UNITS on every dash -- what the em dash (the longest,
# DASH_LONGEST x C) rises at HYPHEN_RISE_DEG -- so the em dash rises 1 degree,
# the en dash 1.9 and the hyphen 3.8 (16.6 units over 950, 485 and 249).
# ALBO_HYPHEN_RISE=angle gives every dash the 1 degree instead.
HYPHEN_OPT = os.environ.get("ALBO_HYPHEN_OPT", "a" if pen.ITALIC else "c")
HYPHEN_RISE_DEG = float(os.environ.get("ALBO_HYPHEN_RISE_DEG", 1.0))   # 4.0 in round 233's c
HYPHEN_RISE_MODE = os.environ.get("ALBO_HYPHEN_RISE", "units")           # units: one rise for all three dashes; angle: one angle
DASH_LONGEST = 1.41
def dash(c, length):
    C = CAP(c); y = C * 0.34; L = length * C; opt = HYPHEN_OPT
    if opt == "b": return stroke(line((0, y), (L, y)), TH_H, cut0=CUT, cut1=CUT)
    if opt == "c":
        rise = (DASH_LONGEST * C if HYPHEN_RISE_MODE == "units" else L) * math.tan(math.radians(HYPHEN_RISE_DEG))
        return stroke(line((0, y - rise / 2), (L, y + rise / 2)), TH_H, cut0=CUT, cut1=CUT)
    if opt == "d": return stroke(line((0, y), (L, y)), widths([(0.0, TH_H * 0.55), (0.5, TH_H), (1.0, TH_H * 0.55)]))
    if opt == "e": return stroke(line((0, y), (L, y)), widths([(0.0, TH_H), (0.45, TH_H), (1.0, TH_H * 0.3)]), cut0=CUT)
    return stroke(line((0, y), (L, y)), TH_H)
@glyph('-')
def g_hyphen(c): return dash(c, 0.37)
@glyph('–')
def g_endash(c): return dash(c, 0.72)
@glyph('—')
def g_emdash(c): return dash(c, 1.41)
# Round 98 (owner 2026-09-14: "raise parens and brackets and others to be
# optically vertically centered with words"): ( ) [ ] spanned -301..684, centre
# 192-200, against the lowercase body's -280..770, centre 245. Raised 50 on a
# ladder of 0 / +35 / +50 / +70 / stretched-to-the-body: +50 puts the tops on
# the ascender line and the feet a little under the descenders; +70 overshot
# the ascender; the stretched one read heavy. The slash pair sit at 274 already.
FENCE_RAISE = 50
def paren(c, left):
    C = CAP(c); d = DESC; r = 150
    if left: pts = superellipse(r, (C - d) / 2, r, (C + d) / 2 + 16, math.radians(105), math.radians(255), 2.2)
    else: pts = superellipse(0, (C - d) / 2, r, (C + d) / 2 + 16, math.radians(75), math.radians(-75), 2.2)
    return aff.translate(stroke(pts, pen_widths(pts, lambda t: 0.6 + 0.4 * math.sin(math.pi * t)), cut0=CUT, cut1=CUT), 0, FENCE_RAISE)
@glyph('(')
def g_parenleft(c): return paren(c, True)
@glyph(')')
def g_parenright(c): return paren(c, False)
def bracket(c, left):
    C = CAP(c); d = DESC; w = 180; x = S * 0.4 if left else w - S * 0.4
    x0, x1 = (x, w) if left else (0, x)
    return aff.translate(geom.ink([stroke(line((x, -d), (x, C)), TH_V * 0.85), stroke(line((x0, C - TH_H / 2), (x1, C - TH_H / 2)), TH_H), stroke(line((x0, -d + TH_H / 2), (x1, -d + TH_H / 2)), TH_H)]), 0, FENCE_RAISE)
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
    # THE CHANCERY et, round 309. Owner, queued 2026-09-15 and recorded at
    # docs/wedge-serif-exploration.md:4239: *"use a flowing and adorned curved
    # E ampersand for italics."* The italic has never had an ampersand of its
    # own -- AMP_OPT's italic default is round 68's roman `round_bowl`, sheared
    # 13 degrees by build.draw and nothing else. The four arms are a different
    # CONSTRUCTION, not a `bred` dial set, so they are not in AMP_OPTIONS and
    # they are picked by their own name. ALBO_IT_AMP defaults to 'a' -- the
    # drawing below, in either face -- so an unset build is byte-identical.
    from .ampersands import bred, VARIANTS2, AMP_OPTIONS, ET_OPTIONS
    # ROUND 350 -- AND IT IS THE ITALIC'S. There was no `pen.ITALIC` here, so
    # `ALBO_IT_AMP` reached BOTH faces: setting it to the ruled 'g' handed the
    # roman the chancery Et as well, and 169 roman glyphs moved with it (the
    # ampersand itself, then every composite and symbol built after it). It
    # was invisible while the default was 'a', which is not in ET_OPTIONS, so
    # the branch was never taken and the bug shipped dormant from round 309.
    if pen.ITALIC and IT_AMP in ET_OPTIONS:
        return ET_OPTIONS[IT_AMP](c)
    if AMP_OPT in AMP_OPTIONS:   # round 233: the owner's options (R54-R56), see ampersands.AMP_OPTIONS; 'a' is the drawing below
        g = bred(c, **AMP_OPTIONS[AMP_OPT])
        if S > 84.0:
            # round 272: the ruling -- no indentations in a counter at the 700
            # and the 900 -- reaches the ampersand too, once its skeleton is
            # the 400's width and its strokes the bold's: the loops' counters
            # dented 14 and 19 units where the diagonal crosses. Each counter
            # is its own convex hull above 84; at and under 84 the lower
            # loop's drawn concavity stands (the round-256 shape).
            from .. import primitives as _PR
            g = _PR.convex_holes(g)
        return g
    dials = dict(dict(VARIANTS2)['round_bowl'].dials)
    dials.update(cross=41.2, arm_end='beak')
    return bred(c, **dials)
# ROUND 350 -- 'g' SHIPS, AND IT SHOULD HAVE SINCE ROUND 319. Owner
# 2026-09-21, shown the italic ampersand and told it was the outlier:
# *"that is not the italic ampersand that was selected today"* -- correct.
# Rounds 312-321 drew, laddered and RULED alt051 on the Albo nib ("make that
# letter form with the albo nib", "squeeze 0.38 wins", "e wins, but it needs
# to have the italic lean", "c wins") and every one of those commits ends
# "unset build: 0 of 493 glyphs differ", because not one of them moved a
# DEFAULT. The italic went on drawing 'a', the sheared roman. Same failure as
# round 336's g: a letter ruled and not shipped, with every gate green.
IT_AMP = os.environ.get("ALBO_IT_AMP", "g")   # round 309: the chancery et, b-e; 'a' is the drawing above; 'g' is alt051 on the Albo nib
AMP_OPT = os.environ.get("ALBO_AMP_OPT", "a" if pen.ITALIC else "e")   # round 252: e ships on the roman -- owner 2026-09-18, "ALBO_AMP_OPT d with a b top" / "e wins for ampersand"
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
    """Owner 2026-09-13: "for at symbol, use an italic 'a' and connect the
    bottom right to the loop to its right like a conventional"; then,
    after six builds with the sweep the wrong way round: "FIGURE OUT WHAT A
    TYPICAL AT SYMBOL LOOKS LIKE AND TRY AGAIN." Measured on Berkeley,
    Albertus and the system faces: the stroke leaves the a's stem foot,
    hooks RIGHT and UP into the ring at about 4 o'clock, climbs the right
    side, goes over the top, down the left, along the bottom, and ENDS at
    the lower right just under where it began -- counterclockwise, the
    open end at 5 o'clock. The a is a single-storey a (the italic form,
    slanted AT_SLANT) with its stem right of centre; everything on the
    bowl profile."""
    C = CAP(c); rx = C * 0.52; ry = C / 2 + OVER - TH_H / 2; cx = rx + S / 2; cy = C / 2
    ring_w = S * 0.85; ri = rx - ring_w
    brx = ri * AT_A_BOWL; bry = brx * (ry / rx)
    sx_want = cx + rx * AT_STEM_X
    bx, by = sx_want - brx, cy + ri * 0.02
    bowl, bo, bi = ring(bx, by, brx + TH_V * 0.42, bry + TH_H * 0.42, w_scale=0.85)
    # ROUND 233 -- THE INNER a's RIGHT SIDE, THINNED TO THE a's OWN STEM. Owner
    # 2026-09-18 (R57): *"fix overthickness in middle, right of interior
    # strokes."* Measured on the built glyph, horizontal ink from the counter's
    # right edge to the stem's right edge at the bowl's equator: 88 units (90-99
    # a little lower), against the real a's stem of 80 (`stems.g_a`: `stem()` at
    # the pen's vertical TH_V 77.5, plus the 1.2-unit ink spread each side). Two
    # things made it: the stem was on the BOWL's thick (bowl_th vertical, 84)
    # rather than the pen's, and its centre sat 4.9 units RIGHT of the ring's
    # outer edge, so the ring's inner wall stood 4 units clear of the stem's
    # left edge and added itself to the run. The stem is now AT_STEM_W wide
    # (TH_V, the a's) and centred so its left edge lies AT_STEM_BURY inside the
    # counter's right edge (`bi`, the ring's inner contour) -- the a's own rule,
    # the bowl kept to the stem. The width plan's shape (0.75 at the top, full
    # from 30% down), the cut top, the ring, the bowl's size and the hook are
    # unchanged; the stem's outer edge moves about 8 units left.
    cr = max(p[0] for p in bi)                       # the counter's right edge, before the skew
    sx = cr - AT_STEM_BURY + AT_STEM_W / 2
    s_top, s_bot = by + bry + TH_H * 0.35, by - bry - TH_H * 0.25
    stem_c = [(sx, s_top), (sx, s_bot)]
    q = AT_STEM_W / PR.bowl_th((0.0, 1.0))           # the plan is on the bowl's thick; scale it to the pen's
    stm = stroke(stem_c, PR.bowl_widths(stem_c, widths([(0.0, 0.75 * q), (0.3, q), (1.0, q)]), floor=S * 0.62), cut0=CUT)
    tan_s = math.tan(math.radians(AT_SLANT))
    inner = aff.skew(geom.union([bowl, stm]), xs=AT_SLANT, origin=(bx, by))
    p0 = (sx + tan_s * (s_bot - by), s_bot)
    # the ring, COUNTERCLOCKWISE from 4 o'clock (angles increasing), AT_SWEEP
    # degrees, ending at the lower right under the start
    a0 = math.radians(AT_START_DEG)
    ringc = superellipse(cx, cy, rx, ry, a0, math.radians(AT_START_DEG + AT_SWEEP), BOWL_K)
    P = ringc[0]; Q = ringc[3]
    tq = (Q[0] - P[0], Q[1] - P[1]); L = math.hypot(*tq) or 1.0; tq = (tq[0] / L, tq[1] / L)
    gap = math.hypot(P[0] - p0[0], P[1] - p0[1])
    # the hook: down from the foot, round to the right, up into the ring
    tail = cubic(p0, (p0[0], p0[1] - gap * 0.6), (P[0] - tq[0] * gap * 0.55, P[1] - tq[1] * gap * 0.55), P)
    center = geom.join(tail, ringc)
    f_tail = gap / (gap + sum(math.hypot(q[0] - p_[0], q[1] - p_[1]) for p_, q in zip(ringc, ringc[1:])))
    prof = widths([(0.0, 0.95), (f_tail, 0.85), (0.86, 0.85), (1.0, 0.5)])
    rg = stroke(center, PR.bowl_widths(center, prof, floor=S * 0.45), cut1=CUT, pieces=True)
    return geom.ink([inner, rg])
AT_A_BOWL = 0.50       # the inner a's bowl half width, x the interior's half width
AT_STEM_X = 0.40       # the a's stem centre, x rx right of the ring's centre
AT_START_DEG = -38.0   # the ring begins at 4 o'clock, where the a's hook enters it
AT_SWEEP = 296.0       # counterclockwise; the open end lands at about 5 o'clock, under the start
AT_SLANT = 6.0   # degrees, the inner a's italic slant
AT_STEM_W = TH_V       # round 233: the inner a's stem is the a's own (the pen's vertical); was the bowl's thick, 84
AT_STEM_BURY = 1.5     # round 233: the stem's left edge this far inside the counter's right edge -- the composite run is AT_STEM_W + this

@glyph('_')
def g_underscore(c): return stroke(line((0, -DESC * 0.5), (500, -DESC * 0.5)), TH_H)
@glyph('…')
def g_ellipsis(c): return geom.ink([dot(DOT_R + i * S * 2.4, DOT_R, DOT_R) for i in range(3)])

# ============ ROUND 258: THE DASH, LOW-QUOTE AND APOSTROPHE FAMILIES ==========
# Owner 2026-09-19: *"continue autonomously on all commonly needed roman,
# italic, bold and bold italic characters."* Measured against a book face's
# working set, Albo was missing these and nothing else in the dash, quote and
# space families. Each is the drawing the face already has, encoded at the
# codepoint that needs it -- NOT a new shape: a reader that meets U+2010 in an
# epub should get the face's hyphen, not a fallback face's.
@glyph('\u2010')   # HYPHEN -- the real one; '-' is HYPHEN-MINUS and text sources use both
def g_hyphen_true(c): return dash(c, 0.37)
@glyph('\u2011')   # NON-BREAKING HYPHEN
def g_hyphen_nb(c): return dash(c, 0.37)
@glyph('\u00AD')   # SOFT HYPHEN -- invisible until the line breaks on it, and then it is a hyphen. Justified text with hyphenation needs it
def g_softhyphen(c): return dash(c, 0.37)
@glyph('\u2012')   # FIGURE DASH -- as wide as a figure. Albo's figures are
# PROPORTIONAL old-style (advances 288 for the 1 to 494 for the 0, mean 440),
# so there is no tabular width to match and the mean is the honest target:
# 0.45 of the cap gives 442 against the en dash's 624.
def g_figuredash(c): return dash(c, 0.45)
@glyph('\u2015')   # HORIZONTAL BAR -- the quotation dash, the em dash's length
def g_horizbar(c): return dash(c, 1.41)
@glyph('\u201A')   # SINGLE LOW-9 QUOTATION MARK -- the comma, as the opening quote of German and Czech
def g_quotesinglbase(c): return geom.ink([dot(MDOT, MDOT, MDOT), comma_tail(MDOT, MDOT)])
@glyph('\u201E')   # DOUBLE LOW-9 QUOTATION MARK
def g_quotedblbase(c):
    return geom.ink([p_ for i in (0, 1) for p_ in (dot(DOT_R + i * S * DQ_GAP, DOT_R, DOT_R), comma_tail(DOT_R + i * S * DQ_GAP, DOT_R))])
@glyph('\u02BC')   # MODIFIER LETTER APOSTROPHE -- the letter, not the punctuation: Ukrainian, Uzbek, many transliterations
def g_modapostrophe(c): return quote(c, S * 0.7, True)
@glyph('\u02BB')   # MODIFIER LETTER TURNED COMMA -- the Hawaiian okina
def g_modturnedcomma(c): return quote(c, S * 0.7, False)

@glyph('\u00B5')   # MICRO SIGN -- the u with its left stem run on below the
# baseline. Not a borrowed Greek mu: the letter is Albo's own u (so the bowl,
# the taper into the right stem and both top wedges are the face's), and the
# descender is the family's straight stroke on the pen, thinning to 0.62 and
# cut at the family's angle, the way the p's and q's stems end.
def g_micro(c):
    xh = c["xh"]; x0 = S / 2
    tailp = line((x0, xh * 0.55), (x0 - S * 0.06, -pen.DESC * 0.72))
    tail = stroke(tailp, pen_widths(tailp, widths([(0.0, 1.0), (0.62, 1.0), (1.0, 0.62)])), cut1=CUT)
    return geom.ink([GLYPHS['u'](c), tail])
