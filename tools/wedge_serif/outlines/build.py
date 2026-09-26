"""Build Albo-Medium.ttf (Albo-Regular until round 83; Fjord until round 58) from the designed outlines: draw, extract the
contours (exteriors ccw, counters cw), apply the linear cut, fit with the
round-20 rule, write the TrueType and the round-19 specimen.

    cd tools/wedge_serif && PYTHON_GIL=0 python3 -m outlines.build <out_dir> [--nocut]
"""
import os, sys, math
# round 202: the owner's own word space, from the phone bench
# ROUND 359 -- 27 -> 16. Owner 2026-09-22, shown four narrower rungs and
# answering in the RATIO rather than the em: *"2.55 or something around there
# wins"*. His +27 from the round-202 phone bench is therefore SUPERSEDED by his
# own later eye, not overruled by a measurement: round 358's research was
# published, he replied "word space for roman is too much still", and this is
# where he put it. 2.55 x the roman's 0.118 em letterfit is 301 units, which
# 285 + 16 gives exactly.
WORD_SPACE_ADJ = float(os.environ.get('ALBO_ALD_WORD_SPACE', 16.0))
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(HERE))
import round19, round20, latin, alphabet2 as A
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont
from . import geom, pen, cut
from . import primitives as PR
from .glyphs import GLYPHS

# ---------------------------------------------------------------- round 99
# The diacritics and the accented letters. Every codepoint Albo does not draw
# is supplied by NOTO at .cpfont build time (the fallback chain), so an
# un-drawn accent is not a missing glyph on the page -- it is one letter of a
# different typeface inside a word. `reading` asks for U+0020-024F, so the
# whole of Latin-1 and Latin Extended-A is in scope.
#
# The marks are drawn once (`glyphs/accents.py`) and the accented letters are
# TrueType COMPOSITES of a base and a mark: an accented letter then IS its
# letter, and a later round that redraws the e redraws every e-acute for free.
MARKS = list("\u00b4\u0060\u02c6\u02c7\u02dc\u00af\u02d8\u00a8\u02d9\u02da\u02dd\u00b8\u02db\u02b9\u0131\u0237")

# char -> (base, mark, placement). 'above' centres on the base's ink and
# lifts to the x-height or the cap line; 'below' hangs from the baseline;
# 'right' is the Czech apostrophe-caron of d t l.
ACCENTED = {}
_A = {   # mark -> [(accented char, base char), ...]
 "\u00b4": [('\u00c1','A'),('\u00c9','E'),('\u00cd','I'),('\u00d3','O'),('\u00da','U'),('\u00dd','Y'),
             ('\u00e1','a'),('\u00e9','e'),('\u00ed','\u0131'),('\u00f3','o'),('\u00fa','u'),('\u00fd','y'),
             ('\u0106','C'),('\u0107','c'),('\u0139','L'),('\u013a','l'),('\u0143','N'),('\u0144','n'),
             ('\u0154','R'),('\u0155','r'),('\u015a','S'),('\u015b','s'),('\u0179','Z'),('\u017a','z')],
 "\u0060": [('\u00c0','A'),('\u00c8','E'),('\u00cc','I'),('\u00d2','O'),('\u00d9','U'),
             ('\u00e0','a'),('\u00e8','e'),('\u00ec','\u0131'),('\u00f2','o'),('\u00f9','u')],
 "\u02c6": [('\u00c2','A'),('\u00ca','E'),('\u00ce','I'),('\u00d4','O'),('\u00db','U'),
             ('\u00e2','a'),('\u00ea','e'),('\u00ee','\u0131'),('\u00f4','o'),('\u00fb','u'),
             ('\u0108','C'),('\u0109','c'),('\u011c','G'),('\u011d','g'),('\u0124','H'),('\u0125','h'),
             ('\u0134','J'),('\u0135','\u0237'),('\u015c','S'),('\u015d','s'),('\u0174','W'),('\u0175','w'),
             ('\u0176','Y'),('\u0177','y')],
 "\u02dc": [('\u00c3','A'),('\u00d1','N'),('\u00d5','O'),('\u00e3','a'),('\u00f1','n'),('\u00f5','o'),
             ('\u0128','I'),('\u0129','\u0131'),('\u0168','U'),('\u0169','u')],
 "\u00a8": [('\u00c4','A'),('\u00cb','E'),('\u00cf','I'),('\u00d6','O'),('\u00dc','U'),
             ('\u00e4','a'),('\u00eb','e'),('\u00ef','\u0131'),('\u00f6','o'),('\u00fc','u'),
             ('\u00ff','y'),('\u0178','Y')],
 "\u02da": [('\u00c5','A'),('\u00e5','a'),('\u016e','U'),('\u016f','u')],
 "\u02c7": [('\u010c','C'),('\u010d','c'),('\u010e','D'),('\u011a','E'),('\u011b','e'),
             ('\u0147','N'),('\u0148','n'),('\u0158','R'),('\u0159','r'),('\u0160','S'),('\u0161','s'),
             ('\u0164','T'),('\u017d','Z'),('\u017e','z'),('\u013d','L')],
 "\u00af": [('\u0100','A'),('\u0101','a'),('\u0112','E'),('\u0113','e'),('\u012a','I'),('\u012b','\u0131'),
             ('\u014c','O'),('\u014d','o'),('\u016a','U'),('\u016b','u')],
 "\u02d8": [('\u0102','A'),('\u0103','a'),('\u0114','E'),('\u0115','e'),('\u012c','I'),('\u012d','\u0131'),
             ('\u011e','G'),('\u011f','g'),('\u014e','O'),('\u014f','o'),('\u016c','U'),('\u016d','u')],
 "\u02d9": [('\u010a','C'),('\u010b','c'),('\u0116','E'),('\u0117','e'),('\u0120','G'),('\u0121','g'),
             ('\u0130','I'),('\u017b','Z'),('\u017c','z')],
 "\u02dd": [('\u0150','O'),('\u0151','o'),('\u0170','U'),('\u0171','u')],
}
for _m, _rows in _A.items():
    for _ch, _b in _rows: ACCENTED[_ch] = (_b, _m, 'above')
for _ch, _b in [('\u00c7','C'),('\u00e7','c'),('\u0122','G'),('\u0123','g'),('\u0136','K'),('\u0137','k'),
                ('\u013b','L'),('\u013c','l'),('\u0145','N'),('\u0146','n'),('\u0156','R'),('\u0157','r'),
                ('\u015e','S'),('\u015f','s'),('\u0162','T'),('\u0163','t')]:
    ACCENTED[_ch] = (_b, "\u00b8", 'below')
for _ch, _b in [('\u0104','A'),('\u0105','a'),('\u0118','E'),('\u0119','e'),('\u012e','I'),('\u012f','i'),
                ('\u0172','U'),('\u0173','u')]:
    ACCENTED[_ch] = (_b, "\u02db", 'below')
for _ch, _b in [('\u010f','d'),('\u0165','t'),('\u013e','l')]:
    ACCENTED[_ch] = (_b, "\u02b9", 'right')
# Romanian and Latvian set a COMMA below, not a cedilla (the corpus has one
# t-comma; Unicode separates them and a reader that renders s-cedilla for
# s-comma is setting the wrong language's letter).
for _ch, _b in [('\u0219','s'),('\u021b','t'),('\u0218','S'),('\u021a','T')]:
    ACCENTED[_ch] = (_b, "\u0326", 'below')

# ROUND 379 -- THE GREEK THAT IS THE LATIN LETTER. Owner 2026-09-24 ("yes to
# all", round 374's item a): fourteen Greek capitals and the omicron ARE the
# Latin letter, and the reference Greek fonts build them as the Latin glyph.
# A 'copy' is a composite of the base alone, at the base's own advance and
# side bearings, so a round on the A reaches the Alpha for free and the two can
# never disagree. In the italic the component is the italic's own capital.
GREEK_COPY = {'\u0391': 'A', '\u0392': 'B', '\u0395': 'E', '\u0396': 'Z', '\u0397': 'H', '\u0399': 'I', '\u039a': 'K', '\u039c': 'M',
              '\u039d': 'N', '\u039f': 'O', '\u03a1': 'P', '\u03a4': 'T', '\u03a5': 'Y', '\u03a7': 'X', '\u03bf': 'o'}
for _ch, _b in GREEK_COPY.items():
    ACCENTED[_ch] = (_b, None, 'copy')
# ... and the monotonic TONOS on the seven lowercase vowels, as composites of
# the letter and the acute (Unicode decomposes U+03AC..U+03CE to the letter
# plus U+0301, the acute). The omicron's is placed on the o it copies.
for _ch, _b in [('\u03ac', '\u03b1'), ('\u03ad', '\u03b5'), ('\u03ae', '\u03b7'), ('\u03af', '\u03b9'), ('\u03cc', 'o'), ('\u03cd', '\u03c5'), ('\u03ce', '\u03c9')]:
    ACCENTED[_ch] = (_b, "\u00b4", 'above')

# The COMBINING marks (U+0300-0328): the same drawings at ZERO advance, so a
# decomposed string -- which is what a badly-made epub hands the reader --
# still sets in Albo rather than falling to Noto one mark at a time.
COMBINING = {'\u0300': '\u0060', '\u0301': '\u00b4', '\u0302': '\u02c6', '\u0303': '\u02dc',
             '\u0304': '\u00af', '\u0306': '\u02d8', '\u0307': '\u02d9', '\u0308': '\u00a8',
             '\u030a': '\u02da', '\u030b': '\u02dd', '\u030c': '\u02c7',
             '\u0327': '\u00b8', '\u0328': '\u02db'}
# U+0326 is itself a combining mark and is DRAWN (glyphs/symbols2.py), so it
# is not in this table: a row mapping it to itself makes a glyph whose one
# component is the glyph, which fontTools rejects as recursive.

# ROUND 369 -- WHERE AN ACCENT ACTUALLY SITS OVER A LETTER. Owner 2026-09-23:
# *"center dieresis optically."* The composite below centres every above-mark
# on the base letter's INK BOUNDING BOX, and Albo therefore measured a centring
# error of 0.000-0.002 of the x-height on every letter -- dead centre, and
# wrong, because no reference does that.
#
# MEASURED, six roman faces, accent centre minus the base's ink centre, as a
# fraction of the x-height (`cmp_marks.py`):
#
#   letter   Georgia   Times   Baskerville   Charter   Hoefler     verdict
#   o         +0.008  -0.001        +0.018    +0.000    +0.002     centred
#   u         -0.009  -0.001        +0.001    +0.003   -0.013      centred
#   n         -0.007  -0.001        +0.000   -0.036    -0.005      centred
#   a         -0.050  -0.034        -0.087   -0.024    -0.030     LEFT, 5 of 5
#   e         +0.019  +0.034        +0.000   +0.028    +0.034     RIGHT, 4 of 5
#
# So the references' rule is not a formula -- two candidate formulas were
# tested and both failed. Centring on the letter's TOP BAND reproduces the a
# (-0.019) and the o (+0.002) and then invents a shift the references do not
# make on the u (-0.047) and the n (-0.068), and would throw the L's accent
# 0.433 of an x-height to the left. Centring on the ADVANCE is noisier still.
# What the references have is a SHORT HAND-MADE TABLE, and this is it: the
# double-storey a carries its weight low and right, so its mark goes left; the
# e's bar and terminal put its optical centre right of its box.
#
# The keys are LOWERCASE, so the capitals A and E are untouched -- the
# measurement was taken on lowercase and says nothing about them.
ACC_OPTICAL_ON = float(os.environ.get("ALBO_ACC_OPTICAL", 1.0))
ACC_OPTICAL = {'a': -0.030, 'e': +0.030}    # x the x-height; + moves the mark RIGHT
# ROUND 392 -- A MARK OVER THE DOTLESS j SITS OVER ITS STEM, NOT OVER ITS
# TAIL. The mark is centred on the base's whole ink box, and the j's tail
# sweeps a long way LEFT under the baseline, so the ĵ's circumflex stood 135
# units left of the stem's top in the italic (165 once round 392 gave the
# italic ȷ the italic j's longer tail) -- over the white beside the letter. For
# the bases named here the mark is centred on the ink between 0.6 x-height and
# the x-height's overshoot instead: the stem's top, where the j's own dot sits.
ACC_BAND = {'\u0237'}

ACC_GAP_LC = 0.10 * pen.XH      # the mark's foot over the x-height
ACC_GAP_CAP = 0.055 * pen.XH
S_GAP_RIGHT = 0.10 * pen.S     # the apostrophe-caron's gap off the letter's right ink    # tighter over a capital: the eye reads the cap line as the ceiling

LIGS = list("\ufb00\ufb01\ufb02\ufb03\ufb04") if os.environ.get("ALBO_LIGS") == "1" else []   # round 96: drawn; round 96b (owner): "no to ligatures for now" -- opt-in only
# Every character any glyph module registers and the record does not already
# name -- so a new module (round 99's symbols, the next round's chess) is in
# the font by existing, with no second list to keep in step.
# ROUND 379 -- THE GREEK THAT WAS ADDED IS APPENDED, NOT SORTED IN. cut.py's
# decimation phase is one counter advanced per contour in CHARS order, so a
# glyph inserted into the codepoint-sorted EXTRA re-cuts every glyph after it
# (cmp_contours.py's header). Appended at the very end, the new Greek moves
# nothing that already shipped. The glyph ORDER is not the cmap: nothing reads
# a glyph's index for its meaning.
GREEK_APPEND = [ch for ch in "ζηικνξυχψςΓΘΛΞΨ" if ch in GLYPHS]
EXTRA = sorted(set(GLYPHS) - set(round19.CHARS) - set(LIGS) - set(MARKS) - set(GREEK_APPEND), key=ord)
CHARS = round19.CHARS + LIGS + MARKS + EXTRA + GREEK_APPEND; gname = round19.gname
ACC_CHARS = sorted(ACCENTED, key=ord)
COMB_CHARS = sorted(COMBINING, key=ord)
GLYPH_ORDER = ['.notdef', 'space'] + [gname(ch) for ch in CHARS] + [gname(ch) for ch in ACC_CHARS] + [gname(ch) for ch in COMB_CHARS]
SIDES = dict(round19.SIDES); SIDES.update({"\ufb00": ('straight', 'open'), "\ufb01": ('straight', 'straight'), "\ufb02": ('straight', 'straight'), "\ufb03": ('straight', 'straight'), "\ufb04": ('straight', 'straight')})
REF = round20.REF
C = pen.CAP
INK_SPREAD = 1.2

def isfig(ch):
    """An ASCII figure. NOT `str.isdigit()`: round 99 added the superscripts,
    and Python calls U+00B2 a digit, which sent it looking for a figure box."""
    return ch in '0123456789'

def ctx(ch, W=None):
    """Per-glyph context: the fixed proportions, the lowercase width factor
    (baked into every lowercase x radius and width through c['wf']), and
    the capitals' solved width multipliers."""
    return dict(xh=pen.XH, asc=pen.ASC, desc=pen.DESC, s=pen.S, cs=pen.CS, cap=C, over=pen.OVER, arch_over=pen.ARCH_OVER,
                wf=pen.WF if ch.islower() else 1.0, W=W or {}, ch=ch)

def draw(ch, W=None):
    """The glyph's ink as one shapely geometry (figures shifted into their
    old-style box)."""
    c = ctx(ch, W)
    if isfig(ch):
        top, bot = latin.FIG_BOX[ch]; c["figH"] = (top - bot) * C
    PR.begin_glyph(ch)   # the life: deterministic per-glyph perturbation of wedges and rings
    g = GLYPHS[ch](c)
    # the record's Cut post-op grew every polygon 1.2 units (offset_naive,
    # grow 3.0 x 0.4) to re-close the joins it had opened; the joins are
    # real now, but the 1.2 units were part of the shipped weight (the l's
    # stem measured 81, not the pen's 77), so the same ink spread is kept.
    # round 296: the ink spread is a 1.2-unit MITRE dilation, and an offsetter
    # cannot say anything true about a feature finer than that. Its input is
    # cleaned of sub-tolerance edges (wedge() repeats its apex; a union repeats
    # a shared corner) and so is its output (a shallow concave corner offsets to
    # two vertices a fraction of a unit apart). geom.collapse_micro.
    g = geom.collapse_micro(g).buffer(INK_SPREAD, join_style=2)
    g = geom.collapse_micro(g)
    if pen.SHEAR:   # round 100: the italic's slope, about the baseline
        import shapely.affinity as _aff
        # AN ITALIC'S CAPITALS ARE ~5% NARROWER, and that is the ONLY thing
        # that changes for most of them. Measured over 17 roman/italic pairs
        # (docs/albo-italic-capitals.md): median width ratio 0.953, while the
        # cap height ratio is 1.000 and the serif spread 1.005 -- so they are
        # neither shorter nor lighter-serifed, and the folklore that chancery
        # capitals stand uprighter than their lowercase is refuted outright
        # (median lowercase slant 12.97 deg against the capitals' 12.94).
        # Eight letters -- N H Q G V A S U -- are genuinely re-cut in a real
        # italic and are NOT addressed by this; they are drawing work, listed
        # in that doc. The other eighteen want exactly this and nothing else.
        g = _aff.affine_transform(g, (1, pen.SHEAR, 0, 1, 0, 0))
    if isfig(ch):
        import shapely.affinity
        g = shapely.affinity.translate(g, 0, latin.FIG_BOX[ch][1] * C)
    return g

CAP_NARROW = float(os.environ.get("ALBO_IT_CAP_NARROW", 0.953))

# THE CAPITAL X's WIDTH. Owner 2026-09-23: *"make versions of X that are less
# wide by reducing angles but keeping rest of letter stylistically intact."*
#
# IT HAS TO GO ON THE TARGET AND NOT ON THE DRAWING, for the reason the comment
# inside solve_widths already gives about the italic's 5%: the solver re-solves
# every capital's multiplier until its ink hits `target`, so a narrowing applied
# inside `caps_straight.g_X` -- a smaller box, a deeper endpoint inset -- is
# undone on the next pass. Measured rather than assumed: pulling both diagonals'
# endpoints 44 units further in on each side (88 units, 12% of the ink) moved
# the advance 786 -> 787 and the angle 42.99 -> 43.11 degrees. A dead dial that
# builds clean and renders a letter nobody asked for.
#
# The ANGLES follow, because the X's diagonals run corner to corner of that box:
# angle-from-vertical = atan((w - 0.6 CS) / cap), which agrees with a raster fit
# on the built letter to 0.01 degrees. So this IS the angle dial, expressed in
# the one quantity the solver does not overwrite.
#
# And the two STROKES' WIDTHS then follow the angles, which is the pen being
# honest (docs/albo-method.md, THE ONE RULE). Measured on built fonts at 2000
# px/em, 1.00 -> 0.80: the thick diagonal moves 66.9 -> 68.7 units while the
# thin FATTENS 28.9 -> 36.0, so the X's contrast falls 2.32 -> 1.91. The V,
# measured the same way, is 1.90 -- so narrowing the X walks it onto its own
# sibling's footing, which is the direction `X_THIN`'s comment in
# caps_straight.py wanted and could not get from a multiplier. Do NOT
# compensate with X_THIN: that is a table standing in for a pen.
#
# WHY THE X AND NOT THE REST OF THE DIAGONALS -- and the ask's usual measure
# does NOT catch it. By advance over cap the X is not an outlier for this face
# at all: 1.066 of the humanist median against a face median of 1.058, rank 10
# of 26, and four of the six other diagonals are wider FOR THE FACE than it is
# (A 1.105, K 1.118, V 1.092, Y 1.106, against W 1.048 and Z 1.063). By SPLAY
# it is: 42.99 degrees from vertical against a humanist median of 37.06, the
# MOST SPLAYED of the seven reference faces measured (Trajan 32.3, Helvetica
# 35.5, Van den Keere 37.1, Coelacanth 38.3, Doves 40.1). And Albo is the only
# one of the four systems whose X is WIDER THAN ITS OWN O -- X/O 1.013 against
# humanist 0.946, Helvetica 0.858, Trajan 0.758, which is the capital-widths
# doc's round-to-square finding landing on this one letter.
#
# 1.0 is today's drawing, bit-identical (a RecordingPen diff over all 493
# glyphs: 0 differ, hmtx included, and GPOS byte-identical across the whole
# ladder -- the X is the only glyph any arm moves). Landmarks, measured: 0.93
# lands the advance on the humanist median (-0.1%) and X/O on humanist (0.948);
# 0.89 lands the splay INSIDE the humanist spread and is the first rung whose
# contrast comes within 8% of the V's; 0.85 lands the splay on the humanist
# median (36.94); 0.80 lands the advance within 3.5% of Trajan. `W['X']` solves
# to 1.248 against a 0.70 clamp floor, so the dial stays live down to ~0.56 --
# below that a rung renders identically to its neighbour, which is this repo's
# recurring dead-ladder failure.
#
# STYLE-AGNOSTIC ON PURPOSE: `solve_widths` is shared, so a non-default value
# narrows the italic's and the bold's X too. Harmless while it is 1.0. If a
# value is ever ruled for the ROMAN alone, this wants `and not pen.SHEAR`.
CAP_X_WIDTH = float(os.environ.get("ALBO_CAP_X_WIDTH", 0.89))   # round 373, owner: "X .89 wins"


# ROUND 374 -- THE FIGURES' WIDTH SOLVE, two faults, both FIGURE-ONLY (owner
# 2026-09-23, *"yes, address all numeral issues"*; the capitals take exactly
# the old path, proved byte-identical in all four cuts).
#
# 1. THE ITALIC SOLVED AGAINST ITS SHEARED INK. `draw` returns the italic
#    already sheared, so every figure's "drawn" width carried the slant's
#    run -- tan(13) x the figure's height, ~160 units on a 3 or a 9 -- and the
#    solver kept asking for a narrower figure than the one it had. 8 of the 9
#    solved italic figures sat on the floor, and the one that most needed the
#    opposite was hidden: measured unsheared at the shipped W, the 7 was 13.5%
#    UNDER its target while the solver pushed it narrower. The figure is now
#    measured UNSHEARED (about its own baseline, which the box translate moved)
#    and the target is the same one as before. `ALBO_FIG_WIDTH_UNSHEAR=0`
#    restores the old reading.
# 2. THE FLOOR. 0.70 is the capitals' clamp and figures inherited it; it bound
#    the roman 3 (+2.9% over target) and 5 (+7.8%) and the Bold's 2 (+11%).
#    Figures take their own floor. `ALBO_FIG_WIDTH_FLOOR=0.70` restores it.
#    AT THE 400s AND THE MEDIUM ONLY (stem <= 84). The Bold's targets are the
#    400's reference widths x 0.95, which a bold figure cannot reach without
#    its counters closing -- built at 0.55, the Bold 5 went to the floor and
#    still read +8.9% over, visibly pinched, and the 3 +5.3%. That is a bold
#    TARGET problem, not a floor problem, so the bolds keep 0.70.
# The measured before/after per figure is in the round-374 section of
# docs/albo-figures-2026-09-23.md.
FIG_WIDTH_FLOOR = float(os.environ.get("ALBO_FIG_WIDTH_FLOOR", 0.55))
FIG_WIDTH_UNSHEAR = os.environ.get("ALBO_FIG_WIDTH_UNSHEAR", "1") != "0"

# ROUND 376 -- THE FIGURES' TARGET KNOWS THE WEIGHT. Owner 2026-09-24, "yes to
# all" (the open items of round 374). The target was the 400's reference width
# x pen.WIDTH at every weight, so a bold figure's ink -- which carries ~50 more
# units of stem -- could not reach it: measured on round 375's build, the Bold's
# figures ran +6% to +28% over target and the BoldItalic's +12% to +32%, the
# solver pinned at its floor, and the growth from 400 to 700 came out UNEVEN
# (the 5 +70 units, the 3 +54, the 4 -23, the 7 -20).
#
# What bold references do, measured the same way on eleven regular/bold pairs
# on this Mac (Georgia, Times New Roman, Charter, Palatino, Baskerville,
# Hoefler Text; roman and italic; stem = the l's horizontal cut at 40% of its
# height; figure = ink width, old-style where the face has it): the figures
# gain K units of width per unit of stem gained, median 0.61 (range -0.11
# Palatino to 1.20 Georgia Bold Italic); overall they widen x1.03-1.19.
# FIG_BOLD_K is that median. The stem gained is pen.S's gain x Albo's own
# measured l-stem-per-S (0.917 roman, 0.819 italic, from the round-375 build:
# 64.0 -> 109.0 and 57.5 -> 97.7 against S 66.9 -> 116).
#
# At S = 66.9 the term is exactly zero, so the Regular and Italic are
# byte-identical (proved). `ALBO_FIG_BOLD_K=0` restores the old target.
FIG_BOLD_K = float(os.environ.get("ALBO_FIG_BOLD_K", 0.61))
FIG_WIDTH_S0 = 66.9
FIG_BOLD_FLOOR = os.environ.get('ALBO_FIG_BOLD_FLOOR', '1') != '0'   # round 376: with a reachable target the bolds take the figures' floor too (see the note above)
def _fig_weight_gain():
    """Units of figure width a heavier stem earns, per round 376."""
    return FIG_BOLD_K * (pen.S - FIG_WIDTH_S0) * (0.819 if pen.SHEAR else 0.917)

def _fig_width_unsheared(ch, g):
    """A figure's ink width with the italic's shear taken back out. The shear
    is applied about y = 0 and the old-style box translate comes after it, so
    the baseline the shear pivoted on now sits at the box's bottom."""
    import shapely.affinity
    ty = latin.FIG_BOX[ch][1] * C
    u = shapely.affinity.affine_transform(g, (1, -pen.SHEAR, 0, 1, pen.SHEAR * ty, 0))
    x0, _, x1, _ = u.bounds
    return x1 - x0

def solve_widths(passes=3):
    """Capitals and figures: scale each glyph's width multiplier so its ink
    width lands on the references' median (round 20's rule, same clamps)."""
    W = {}
    for _ in range(passes):
        for ch in CHARS:
            if not (ch.isupper() or isfig(ch)) or ch in ('I', '1') or ch not in REF or ch not in GLYPHS: continue
            g = draw(ch, W); x0, y0, x1, y1 = geom.bbox(g); drawn = x1 - x0
            if isfig(ch) and pen.SHEAR and FIG_WIDTH_UNSHEAR:   # round 374, see FIG_WIDTH_UNSHEAR
                drawn = _fig_width_unsheared(ch, g)
            # AN ITALIC'S CAPITALS ARE ~5% NARROWER, and for most of them that
            # is the ONLY change. Measured over 17 roman/italic pairs
            # (docs/albo-italic-capitals.md): median width ratio 0.953, cap
            # height ratio 1.000, serif spread 1.005 -- neither shorter nor
            # lighter-serifed. The folklore that chancery capitals stand
            # uprighter than their lowercase is refuted outright: median
            # lowercase slant 12.97 deg against the capitals' 12.94.
            #
            # It goes on the TARGET and not on the drawn outline, because
            # solve_widths re-solves each capital's multiplier until its ink
            # hits this number -- a scale applied in draw() is simply undone on
            # the next pass, which is what the first attempt did (H moved 752
            # to 749 instead of to 717).
            #
            # Eight letters -- N H Q G V A S U -- are genuinely re-cut in a
            # real italic and this does NOT address them; that is drawing work.
            target = REF[ch]["w"] * C * pen.WIDTH
            if pen.SHEAR: target *= CAP_NARROW
            if ch == 'X': target *= CAP_X_WIDTH          # owner 2026-09-23, see CAP_X_WIDTH
            if isfig(ch) and pen.S > FIG_WIDTH_S0: target += _fig_weight_gain()   # round 376, see FIG_BOLD_K
            _lo = FIG_WIDTH_FLOOR if (isfig(ch) and (pen.S <= 84.0 or FIG_BOLD_FLOOR)) else 0.7   # round 374, see FIG_WIDTH_FLOOR; round 376 FIG_BOLD_FLOOR
            if drawn > 1: W[ch] = max(_lo, min(1.45, W.get(ch, 1.0) * (target / drawn) ** 0.85))
    return W

PUNCT_MARKS = set(".,:;!?'\"\u2018\u2019\u201c\u201d\u2026*"
                  "\u201a\u201e\u02bc\u02bb")   # round 96; round 262 adds the low quotes and the modifier apostrophes, which are QUOTES and must be fitted as the ones they copy -- measured before it, U+201A took the new-symbol fallback (advance 226) where its own drawing, the comma, takes 264, and U+02BC took 197 where the apostrophe it copies takes 264
PUNCT_FENCES = set("()[]/\\-\u2013\u2014+=#@_%&")
# ROUND 220 -- THE STOPS AND THE QUOTES ARE NOT ONE CLASS IN AN ITALIC. Owner
# 2026-09-18 had asked for the italic's punctuation; measured as the 2-D
# closest approach against seven fitted faces (a row-wise measure cannot see
# `s'` at all -- the s and the apostrophe share no scanline), the QUOTES sit in
# the band (s' 0.216 em against Flanker 0.257, Pagella 0.222, a reference
# median of 0.168) while every STOP is the loosest of the eight: s, 0.198
# against 0.048-0.168, e! 0.156 against 0.068-0.140, !a 0.236 against
# 0.100-0.187. Round 97b's 2.25 was set on the roman and is right for the
# quotes; the stops take their own factor, italic only.
PUNCT_STOPS = set(".,:;!?\u2026")
ALD_STOP_BEAR = float(os.environ.get("ALBO_ALD_STOP_BEAR", "1.05"))
# ...and two of the stops still want their own delta after the class factor,
# because the class is symmetric and their shapes are not. Measured at
# STOP_BEAR 1.05: the comma reads s, 0.166 against a 0.129 reference median
# while ,a reads 0.080 against 0.123 -- its ink hangs to the LEFT of where a
# period's sits, so the same pair of bearings lands it wrong on both sides at
# once; and the ! and the ? are still loose on the right alone (!a 0.206 and
# ?o 0.190 against 0.167 and 0.142). Units, (left, right), italic only.
ALD_PUNCT_ADJ = {',': (-37, 43), '!': (0, -39), '?': (0, -48)}
# ROUND 303 -- THE MARKS COME IN, FROM HIS OWN BENCH. Owner 2026-09-20 judged
# 39 roman and 32 italic mark pairs on the 396-row bench; sorted by WHICH mark
# and WHICH SIDE (a letter+mark pair is the mark's LEFT bearing, a mark+letter
# pair its RIGHT), his answers are a ruling on the marks themselves:
#
#     roman   '  lsb -44 (n5, sd 7.1)   rsb -33 (n2)
#             ,  lsb -15 (n12, sd 7.6)
#             .  lsb -12 (n12, sd 10.2)
#             :  lsb  -7 (n5)
#             ;  lsb  -6 (n3)
#     italic  .  lsb  -6 (n11)    :  lsb -6 (n4)
#
# The apostrophe is the most consistent thing in the whole bench -- five words
# carrying one, every value between -32 and -50 -- and it is a BEARING and not
# a kern for the same reason round 211's o was: the fault is the mark's, so a
# kern per preceding letter would fix the letters he happened to judge and
# leave every other one shut.
#
# NOT APPLIED, and the reason is the spread rather than the sign: the italic's
# comma (+1.0, n11) says leave it alone; its apostrophe (-6.7 on [-22,-18,+20])
# and its semicolon (-27 on two values 22 apart) are not evidence yet.
#
# THE CONSTANTS ARE SOLVED AGAINST THE OTHER TWO CHANGES, not copied from the
# table above. His numbers were judged on build 205, and this round also moves
# the letter on the mark's left: in the roman the round lowercase gains +11 on
# its right, and across his own judged pairs for each mark that is worth +4.6
# ('.' and ','), +4.4 (':'), +7.3 (';') and +2.2 ("'") on average -- so a mark
# given his raw number would land short by that much. In the italic every
# lowercase letter gains +4 per side, which reaches a mark pair whatever the
# letter. Both are subtracted here, and `cmp_bench_gaps.py` re-checks the
# built font against his targets rather than against these constants.
# ROUND 308 replaces round 303's hand-solved constants here: the joint fit
# below is a COMPLETE model of his mark judgments, not a delta on them, and
# adding it to those constants double-counted every mark (the apostrophe
# reached -80 and the roman's marks measured worse than doing nothing).
ROM_PUNCT_ADJ = {}
# ROUND 304: his raw numbers, now that the italic lowercase tracking is gone.
# (round 303's italic stop constants removed with the roman's, same reason)

# ROUND 308 -- BOTH SIDES OF EVERY GLYPH, FITTED TOGETHER.
# ROUND 344 -- REFITTED on 384 judgments, and the fit is now a SCRIPT:
#   `bench_fit.py` (its docstring is the method; `--check` gates this file
#   against the bench). Round 308 committed only these numbers, and its input
#   was never written back -- bench_values.json stayed at round 302's 189
#   judgments while the tables were fitted from 330, so nothing here could be
#   re-derived. Do not hand-edit the four tables below; re-run the script.
#   THE g IS EXCLUDED from the fit, all 14 of its rows: owner 2026-09-21,
#   "ignore new 'g' values because it was with old g".
#
# 384 bench judgments (190 roman, 194 italic); 370 after the g is dropped.
# Each says "the white in THIS
# pair should change by d", and a pair's white is the LEFT glyph's right
# bearing plus the RIGHT glyph's left bearing -- so the bench is ONE linear
# system in those two unknowns per glyph, and it is solved as one.
#
# Rounds 303-307 fitted the letters and the marks separately, which is what
# made the marks WORSE as the letter table got richer: each half was absorbing
# the other's error. Mean |error| against his own numbers:
#
#     do nothing        roman 15.20   italic 11.82
#     separate fits     roman 10.7 (letters) / 10.4 (marks)
#     ONE JOINT FIT     roman  9.55   italic  9.03
#
# Round 344, on the 370 non-g judgments (a different, larger set, so these are
# not comparable with the three lines above -- only with each other):
#
#     do nothing        roman 14.82   italic 12.53
#     round 308's tables roman 9.51   italic  9.88
#     REFITTED          roman  9.00   italic  7.66
#
# Ridge-regularised at lambda 1 -- a letter judged twice must not be trusted
# like one judged eleven times -- and a glyph SIDE ships only when he judged it
# at least 4 times and the fit asks for at least 4 units. A MARK's floor is
# different and was never written down: 3 readings and NO magnitude floor,
# which is why the roman's `;` ships at -3 on three readings and the italic's
# `;` does not ship at -20 on two. (Recovered in round 344 by reproducing
# these tables; a floor that lives only in a session is not a rule.) That filter costs
# about a unit against the unfiltered fit (roman 8.50 -> 9.55) and is worth it.
#
# NOT SHIPPED for that reason: the apostrophe's RIGHT side, which his two `'s`
# readings put near -33. Two is under the floor. His five letter+apostrophe
# readings are far stronger and do ship, as that mark's LEFT side.
#
# THE MARKS ARE NOT TAKEN FROM THE JOINT FIT. The ridge shrinks a mark that he
# judged five times toward zero (the apostrophe came back -33 where his five
# readings say -44), and a mark's own readings are the strongest evidence in
# the bench. So each mark is solved DIRECTLY -- his mean for that mark, minus
# what the letters now contribute on its left -- and only the letters come from
# the joint fit. Measured, that is the better of the two on the marks.
#
# (lsb, rsb) deltas in design units. Re-fit from the bench, never hand-tuned.
ROM_LC_ADJ = {'a': (+18, -7), 'd': (+8, -6), 'e': (+7, +0), 'i': (+0, +7), 'l': (+9, +0), 'm': (-5, -5), 'n': (+7, -13), 'o': (+7, +5), 'p': (-8, +14), 's': (-5, +0), 't': (+11, -15), 'u': (+8, +0), 'y': (+0, -8),
               # THE LIGATURES TRACK THE LETTER THEY END IN, which is the trap
               # `BEARING_ADJ['ff']` was given for: cmp_touch reads a pair's
               # white as getlength(ab) - getlength(b), so when the `i` gained
               # 9 units on its right the fi LIGATURE -- whose own advance had
               # not moved -- read newly tight at 0.0093 em while nothing in
               # its drawing had changed. uniFB01 and uniFB03 end in an i,
               # uniFB02 and uniFB04 in an l (which moves 0 here), uniFB00 in
               # an f (unchanged).
               '\ufb01': (0, +7), '\ufb03': (0, +7)}
ROM_PUNCT_FIT = {"'": (-38, +0), ',': (-11, +0), '.': (-8, +0), ':': (-2, +0), ';': (-3, +0)}
# ROUND 340 -- the g's own fitting, after this session redrew both letters.
# MEASURED WITH THE 2D CLOSEST APPROACH, not the bbox gap. The bbox measure
# (rsb + kern + lsb) said this letter was 73 units TIGHT on its left; the
# render said the opposite and the 2D measure agreed with the render -- it was
# already 0.024-0.035 em LOOSE. The bbox is fooled by the italic g's tail,
# which overhangs at DESCENDER level where no neighbour has ink, so the white
# it counts is not white a reader sees. That is the trap
# docs/albo-spacing-method.md exists to name, and I walked into it.
ALD_LC_ADJ = {'g': (-15, -15),   # NOT from the bench: every g row was judged against the
              #                 superseded letter, so round 344 drops them all (owner
              #                 2026-09-21). This pair is round 340's 2-D fit, kept.
              'e': (+0, -14), 'h': (+4, +0), 'i': (-5, +8), 'l': (+0, +5), 'm': (+6, +7), 'o': (+7, +0), 'p': (+0, +9), 'r': (+10, +0), 't': (+0, -10), 'u': (-5, +10), 'w': (+0, +14), 'y': (+10, +16)}
ALD_PUNCT_FIT = {"'": (-6, +0), ',': (+2, +0), '.': (-5, +0), ':': (-1, +0)}

# ROUND 396 (2026-09-26) -- B2 IS THE DEFAULT SPACING. Owner, decided blind:
# *"ship B2"*. The four tables above are round 395's bench fit and stay here as
# the ALBO_SPACING_FIT=bench arm, byte for byte round 395; the default (unset,
# or =b2) replaces them with the identity + shape-feature ridge of
# docs/local-ai-spacing-options-2026-09-26.md, refit on 470 answers (held out
# 10.37 on the bench pairs against these tables' 11.66). The g and the
# ligature riders are handled as before. Tables: spacing_b2.json, written by
# local_ai/b2_fit.py; kern.py swaps _BENCH_PAIRS_* under the same switch.
# docs/albo-round-396-2026-09-26.md.
SPACING_FIT = os.environ.get("ALBO_SPACING_FIT", "b2").strip().lower() or "b2"
if SPACING_FIT == "b2":
    import json as _json
    _B2 = _json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "spacing_b2.json")))
    ROM_LC_ADJ = {c: tuple(v) for c, v in _B2["roman"]["letters"].items() if c != "g"}
    if "i" in ROM_LC_ADJ:
        ROM_LC_ADJ["ﬁ"] = ROM_LC_ADJ["ﬃ"] = (0, ROM_LC_ADJ["i"][1])
    if "l" in ROM_LC_ADJ:
        ROM_LC_ADJ["ﬂ"] = ROM_LC_ADJ["ﬄ"] = (0, ROM_LC_ADJ["l"][1])
    ROM_PUNCT_FIT = {c: tuple(v) for c, v in _B2["roman"]["marks"].items()}
    ALD_LC_ADJ = {"g": ALD_LC_ADJ["g"],
                  **{c: tuple(v) for c, v in _B2["italic"]["letters"].items() if c != "g"}}
    ALD_PUNCT_FIT = {c: tuple(v) for c, v in _B2["italic"]["marks"].items()}
elif SPACING_FIT != "bench":
    raise SystemExit(f"ALBO_SPACING_FIT={SPACING_FIT!r}: the arms are 'b2' (default) and 'bench' (round 395)")

for _c, _lr in ALD_PUNCT_FIT.items():             # round 308's joint fit
    _b = ALD_PUNCT_ADJ.get(_c, (0, 0))
    ALD_PUNCT_ADJ[_c] = (_b[0] + _lr[0], _b[1] + _lr[1])
for _c, _lr in ROM_PUNCT_FIT.items():
    _b = ROM_PUNCT_ADJ.get(_c, (0, 0))
    ROM_PUNCT_ADJ[_c] = (_b[0] + _lr[0], _b[1] + _lr[1])
# ...and the italic COMMA reads +1.0 on eleven pairs, which is "leave it where
# it is" -- and with the tracking withdrawn that is literally nothing to do.
# ROUND 221 -- THE QUOTES' RIGHT SIDE. Owner 2026-09-18: *"take a pass at all
# spacing including 'apostrophe s'."* Round 220 judged the quotes in band on
# `s'` -- the letter BEFORE the mark -- and never measured `'s`, the pair he
# named. On the 2-D closest approach (cmp_space_2d.py) the quote+letter class
# reads 0.244 em against a 0.105-0.217 reference band, and each mark's RIGHT
# side is nearly twice its left (quoteright 0.255 / 0.133): the same flat
# bearing on both sides of a mark that sits at cap height, in a face sheared
# 13 degrees, so its ink already leans toward the next letter. Units off the
# right bearing of every quote, italic only.
PUNCT_QUOTES = set("'\"\u2018\u2019\u201c\u201d")
ALD_QUOTE_RSB = float(os.environ.get("ALBO_ALD_QUOTE_RSB", "-120"))
# ROUND 222 -- AND THE LEFT SIDE TOO. Owner 2026-09-18, on the round-221
# proof: *"too much space between apostrophe and previous and next letters.
# compare with other reference fonts."* Rendered side by side at one x-height,
# the mark NESTS between the letters in Georgia, New York, Coelacanth and
# Poetica and floats in Albo -- and the round-221 band was judged against its
# loose end (Flanker, Pagella), not against the faces that read tight. Units
# off the LEFT bearing of every quote, italic only.
ALD_QUOTE_LSB = float(os.environ.get("ALBO_ALD_QUOTE_LSB", "-20"))
# Round 97 (owner: "go" on the whole-lowercase refit) / 97b (owner: "crosses
# seems way too spaced out", "same for frozen"): per-letter (lsb, rsb) deltas
# from `outlines.cmp.rhythm.solve_cat` on the round-96b file. The first solve
# (round 97) aimed every pair at ONE rhythm and so made a round beside a round
# as open as a stem beside a stem -- 'crosses', 'frozen' -- which is the
# autokerner docstring's own warning. solve_cat aims each pair at the median
# of its SIDE CATEGORY (the fitting rule's straight/round/open/diag, with the
# e's right read as round), so the category ratios the owner had accepted
# stand and only the scatter within a category is solved away: mean
# |deviation| 5.5 -> 0.8, extremes -41..+36 -> -10..+9. Re-solve after any
# outline change; these numbers are the record.
# ROUND 284 (2026-09-19): the s's row is (17, 19), from (1, -15). Round 283
# tucked the head to 0.93 and the letter narrowed 38 units; the band rule then
# stood the old bearings beside a lower bowl instead of a reaching head, and
# cmp_space_2d read the s at 0.072 em on its right and 0.090 on its left
# against the lowercase's 0.106 (owner: "all s need work, mostly spacing").
# +34 / +16 put both sides on the median.
# ROUND 288 (2026-09-19): the f's and the r's right sides, +16 and +15.
# Owner: "fix the spacing around the recently redone characters." Both ends
# were re-cut in round 275 (the finials), which shortened the f's hook and
# the r's arm, and the band rule then priced a shorter reach as spacing:
# cmp_space_2d read the f's right at 0.093 em and the r's at 0.094 against
# the lowercase median of 0.108, the two tightest right flanks in the
# alphabet. The a, the s and the y, redone in the same rounds, measured on
# the median and were left alone.
#
# THE ff LIGATURE TRACKS THE f. uniFB00 is the one f-ligature that ENDS in an
# f, so its right side is the f's; the other four end in an i or an l and take
# those. It is fitted independently, so it did not pick the +16 up, and
# cmp_touch -- whose pair white is `getlength(ab) - getlength(b)`, arithmetic
# that puts the ligature's advance against the plain f's -- read ff as newly
# touching at every roman weight while the ligature's own drawing had not
# moved a unit. The +16 here is the real fix rather than the tool's: after an
# ff the next letter now stands where it stands after a plain f.
# ROUND 303 -- THE ROMAN'S ROUND LOWERCASE, +11 ON THE RIGHT. In his 66 roman
# lowercase judgments the LEFT letter predicts the number and the right one
# does not: a round letter before anything reads +11, a flat one +2, while the
# right-hand letter reads +5 whichever it is. So the fault is the round
# letter's own right side -- about a third of a phone pixel tight -- and it is
# a bearing, applied below to b c d e g o p q s. His per-pair residuals (sd 14)
# are NOT applied: they are the next pass, and only after this one is judged.
ROUND_LC_RSB = 11
# The roman g is a narrower letter since round 335 (advance 512 -> 489) and
# kept the old bearings: measured the same way it ran 11 tight on the left and
# 16 on the right against the o. 'g' goes (-11,-19) -> (0,-3).
BEARING_ADJ = {'a': (-13, 3), 'b': (-4, 0), 'c': (2, 15), 'd': (3, 1), 'e': (2, -1), 'f': (5, 25), 'g': (0, -3), 'h': (0, -2), 'i': (0, -1), 'j': (0, 14), 'k': (0, 18), 'l': (-3, 2), 'm': (0, -2), 'n': (4, 0), 'o': (0, -2), 'p': (-11, -1), 'q': (0, 37), 'r': (2, 13), 's': (17, 19), 't': (-11, 0), 'u': (-9, 3), 'v': (-1, -4), 'w': (6, 4), 'x': (42, 0), 'y': (0, 13), 'z': (0, -23), 'ﬀ': (0, 16)}
# ROUND 373 -- THE ROMAN CAPITALS' OWN BEARING DELTAS, starting with the X.
# Owner 2026-09-23: *"X .89 wins, adjust spacing around x."* Narrowing the X
# did NOT move its gaps -- the solver narrows ink and advance together, so every
# X pair's closest approach stayed within 0.002 em -- but measuring them is what
# showed the X had always sat loose. Measure 4 (cmp_space_2d.py, 2-D closest
# approach, shaped pairs, eight roman references) on the built 0.89 X, each X
# pair's excess over the reference median taken AGAINST the matching H pair's
# excess, so Albo's deliberate +0.03 em capital rhythm cancels out:
#
#   X's LEFT side  (HX OX AX EX TX NX IX YX VX vs the same partners before H):
#       +.015 +.026 +.004 +.021 -.008 +.015 +.024 -.006 -.004   median +0.015 em
#   X's RIGHT side (XH XO XA XE XT XN XV vs H before the same partners):
#       +.023 +.028 +.018 +.026 +.001 +.031 -.013               median +0.023 em
#
# XI and XY are left out of the right-side median deliberately: both carry the
# owner's own hand-set kerns from round 198's bench (XI -72, XY -54), and
# those kerns ARE the spacing he chose for those pairs. The X's shape change
# left their geometry where he set it (XI 0.035 -> 0.033, XY 0.028 -> 0.029),
# so they stand. Applied as whole units: -15 left, -18 right (the right side's
# median is 23; 18 keeps XT, already near-level, from going tight).
#
# Roman only -- the Aldine italic's capitals have their own owner-set table,
# ALD.CAP_BEARING_ADJ, and the italic X takes (1, -16) from it already.
ROM_CAP_ADJ = {'X': (-15, -18)}

# ROUND 376 -- THE ITALIC 1's LEFT SIDE. Round 374 widened the 1 and recorded
# that the italic 1 "needs an O1 kern". Measured on the built italic (Measure 4,
# cmp_space_2d, against eight reference italics) it is not one pair: EVERY pair
# ending in the 1 sits short -- O1 0.016 em (refs 0.133), 01 0.058 (0.157),
# 11 0.087 (0.148), 21 0.077 (0.125), 81 0.091 (0.143) -- while every pair
# STARTING with it is in band (10 12 18 1a). Against the italic figures' own
# rhythm (00 20 80 run ~+0.01 over the refs) the 1's left is ~0.06 em tight.
# A bearing, then, not a kern: its slanted flag leans into whatever precedes
# it. +45 on the left; O1 gets a kern on top (kern.py) because a round
# capital's right curve meets the flag hardest. Italic only.
ALD_FIG_ADJ = {'1': (45, 0)}

A_LEFT = 1.40   # round 96b: 56 units -- measured, not laddered (outlines/cmp/rhythm.py); 2.0 (74) was loose after a stem, 0.72 (37) tight
J_RIGHT = 1.83  # round 96b: the j's right bearing was measured to its bare stem while the n's is measured to a foot tip, so every j-pair sat ~27 tighter; 68 stands the stem where the n's stands

try:                                     # the Aldine lowercase's own fitting table (round 133)
    from .glyphs import aldine as ALD
except ImportError:                      # the module is optional, exactly as in glyphs/__init__
    ALD = None


# ROUND 211 -- THE ITALIC o's RIGHT BEARING, +28. Owner 2026-09-18: *"adjust oo
# spacing until 'good' looks correct (it currently touches)"*.
#
# It is a BEARING and not an `oo` kern because the fault is the letter's, and
# his own word proves it: in `good` the two gaps after the g are o+o at 0.040 em
# and o+d at 0.048, while g+o is 0.118 -- nearly three times either. A kern on
# `oo` alone would have fixed one of the two and left the next one shut.
#
# Measured, min white on the cmp_touch instrument at a 300 px x-height, against
# the median of seven fitted faces (Flanker Griffo, Coelacanth, Pagella,
# Poetica, Times, Georgia, New York): the o's LEFT-side family (x+o) sits +0.012
# em above that median -- healthy -- while its RIGHT-side family (o+x) sits
# -0.020 below it, and `oo`, two identical bowls meeting at the same height, is
# the worst case at -0.030. +28 brings the right side to +0.006, i.e. into
# agreement with the letter's own left, and lands oo at 0.068 em and od at 0.076
# against reference medians of 0.071 and 0.077.
#
# The ROMAN is NOT touched and does not need to be: its oo measures 0.073 em
# against the same 0.071 median. This table is read inside fit_aldine, which
# runs only when the Aldine italic is live.
#
# The arithmetic is exact and needs no ladder: a bearing is added to the advance
# and `dx = lsb - l` is untouched, so rsb += D adds exactly D units of white to
# every `o?` pair and moves nothing else in the font.
#
# It belongs in ALD.BEARINGS['o'] -- (-18, 58) -> (-18, 86) -- and is held here
# only because glyphs/aldine.py was being edited by another hand on the day.
ALD_BEARING_ADJ = {'o': (0, 28)}
for _c, _lr in ALD_LC_ADJ.items():                # round 308's joint fit
    _b = ALD_BEARING_ADJ.get(_c, (0, 0))
    ALD_BEARING_ADJ[_c] = (_b[0] + _lr[0], _b[1] + _lr[1])
# ROUND 304 -- AND THE ITALIC LOWERCASE WANTS NOTHING. WITHDRAWN.
#
# Round 303 gave every italic lowercase letter +4 per side, a uniform +8 per
# pair, on 17 judgments averaging +8.3 with sd 7.9. He judged 37 more the same
# evening and the number did not survive: **n=54, mean +1.4, sd 12.5**. Broken
# out by the left letter it is round -1.5 (n17), flat +1.7 (n33) -- which is
# "leave the italic lowercase alone", and the opposite of a tracking change.
#
# So the +8 is GONE rather than retuned, and the italic's capitals, marks and
# leftover pairs go back to his raw numbers with it: each of those carried his
# target MINUS 4 precisely because this tracking was under them.
#
# The one thing the new data does say is that the italic DIAGONALS want about
# +11 (left-letter diag +10.8 on n=4, right-letter +17.5 on n=2). Four and two
# readings are not a bearing, so nothing is applied; it is the question the
# next bench pass should answer.
#
# The ROMAN's round-lowercase +11 is the opposite story and was CONFIRMED by
# the same 37 rows: round +12.2 (n27) against flat +0.8 (n41), where round 303
# fitted +11 on n=24 against +2 on n=38. It stands.


def fit_aldine(ch, conts):
    """ROUND 133 -- the Aldine lowercase's bearings, read from a table in
    UNSHEARED design units instead of derived from the roman's machinery.

    Owner 2026-09-16: "fit the whole lowercase in one pass." Round 132 redrew
    all 26 letters against a measured reference, which left every input of the
    round-20 rule -- `A.SIDE_FRACTION`, `BEARING_ADJ`, `A_LEFT`, `capbear` --
    solved for a drawing that no longer exists.

    THE SPACE IS THE SHAPES' OWN. `conts` arrives SHEARED (draw() shears last),
    so each point is put back upright by x - SHEAR*y before the band is read:
    the reference was unsheared to be measured, the letters were drawn against
    it upright, and a bearing measured in a third space would describe neither.
    It also takes the two faces' 1.2 degrees of slant difference out of every
    number, which in a sheared frame is a systematic 9 units at the x-line.
    `dx` needs no conversion either way -- a horizontal translation commutes
    with a shear about the baseline, so the same dx moves the sheared ink.

    The band is the x-height band, as for every other letter. Fitting on the
    FULL extent instead would price the f's head, the j's tail and the y's
    swash as if they were spacing, when what a neighbour actually meets is the
    stem. The table's own notes carry the per-letter rulings.
    """
    sh = pen.SHEAR
    lo, hi = -pen.OVER, pen.XH + pen.OVER
    # THE BAND TEST IS ON THE ROUNDED y, because that is the y the glyph ships
    # with -- the TTF stores integers. The q is the letter that proves it: its
    # tail crosses the band's lower edge at about y = -14.4, which rounds INTO
    # the band, so the shipped outline has 73 more units of band ink than the
    # float contour does. Fitted on the float the q came out 373 against the
    # table's 446, and every pair it is in was 73 units tight -- with the table
    # and the font each self-consistent and disagreeing. Round here and the
    # fitter and the shipped glyph cannot drift apart.
    band = [x - sh * y for pts, _ in conts for x, y in pts if lo <= round(y) <= hi]
    xs_u = [x - sh * y for pts, _ in conts for x, y in pts]
    l, r = (min(band), max(band)) if band else (min(xs_u), max(xs_u))
    lsb, rsb = ALD.BEARINGS[ch]
    if ch in ALD_BEARING_ADJ:                      # round 211, above
        lsb += ALD_BEARING_ADJ[ch][0]; rsb += ALD_BEARING_ADJ[ch][1]
    # ROUND 197 -- ONE TRACKING DIAL over the whole lowercase, so the FIT can be
    # judged without disturbing the table. That table is round 133's solve plus
    # the owner's own sixteen hand-set letters (round 136) and a +26 tracking he
    # dialled at his bench; re-solving it would throw his fitting away. This
    # adds or removes tracking uniformly -- half on each side, the way his was
    # applied -- and 0 is exactly what ships.
    _trk = float(os.environ.get("ALBO_ALD_TRACK", "0"))
    if _trk:
        lsb += _trk / 2.0; rsb += _trk / 2.0
    adv = lsb + (r - l) + rsb
    dx = lsb - l
    _FITTED[ch] = (lsb, rsb, 'ald')    # round 379: the Greek's analogues read this
    return adv, dx, min(x for pts, _ in conts for x, y in pts) + dx


# ROUND 379 -- THE GREEK IS SPACED FROM ALBO'S OWN LATIN, SIDE BY SIDE.
# Owner 2026-09-24 ("yes to all", round 374's item b). Every Greek glyph used to
# fall through to SIDES' straight/straight default, so the round letters (alpha,
# delta, theta, omicron, rho, sigma, phi, omega) sat as far from their
# neighbours as an n's stem does. There is no owner bench for the Greek, so each
# SIDE takes the shipped bearing of the Latin letter whose side it IS -- the
# omicron's left is the o's left, the eta's two stems the n's, the rho's bowl
# the o's -- measured in the same band and the same space that letter is fitted
# in (the italic lowercase unsheared, like fit_aldine; everything else as fit()).
# The analogue's bearing is its FINAL one, bench deltas and kerning-free, so a
# later bench refit of the o moves the omicron's side with it. Verified against
# the references' Greek with a closest-approach sweep (docs/albo-greek-2026-09-23.md,
# round 379). The omicron and the Latin-identical capitals are composites and
# take their letter's advance outright.
GREEK_SIDES = {
    'α': ('o', 't'), 'β': ('b', 'b'), 'γ': ('v', 'v'), 'δ': ('o', 'o'), 'ε': ('c', 'c'),
    'ζ': ('c', 'c'), 'η': ('n', 'n'), 'θ': ('o', 'o'), 'ι': ('i', 't'), 'κ': ('k', 'k'),
    'λ': ('x', 'x'), 'μ': ('u', 'u'), 'ν': ('v', 'v'), 'ξ': ('c', 'c'), 'π': ('t', 't'),
    'ρ': ('o', 'o'), 'σ': ('o', 'r'), 'ς': ('c', 'c'), 'τ': ('t', 't'), 'υ': ('u', 'o'),
    'φ': ('o', 'o'), 'χ': ('x', 'x'), 'ψ': ('u', 'o'), 'ω': ('o', 'o'),
    'Γ': ('F', 'F'), 'Δ': ('A', 'A'), 'Θ': ('O', 'O'), 'Λ': ('A', 'A'), 'Ξ': ('Z', 'Z'),
    'Π': ('H', 'H'), 'Σ': ('Z', 'E'), 'Φ': ('O', 'O'), 'Ψ': ('U', 'U'), 'Ω': ('O', 'O'),
}
# ... and the references' own Greek-minus-Latin offset on top, per side, in
# units: where the reference Greek faces space a Greek side looser or tighter
# than its Latin analogue (the eta's feet-less stems sit 0.04 em looser than
# the n's in all four), that offset is carried over. FITTED by
# instruments/greek376_space.py --fit against the four references' median,
# one row per cut family ('rom' the Regular, 'bold' the Bold against the bold
# references, 'ald' both italics -- there is no bold-italic Greek reference set),
# clamped to 30 units a pass. Re-run it after redrawing any Greek letter:
# like the bench tables, a row describes the drawing it was fitted on.
# ONE ROW IS NOT THE FIT'S: the italic Psi's (12, 14). Its two sides sit inside
# the references' spread, but sheared, its arms' two-way top wedges reach over
# the next letter's and PsiPsi TOUCHED (-0.008 em Italic, -0.011 BoldItalic,
# instruments/greek376_touch.py); xiPsi and zetaPsi sat under the 0.012 floor.
# 12 + 14 units clears all three at both weights and keeps Psi's sides in band.
GREEK_SIDE_ADJ = {
    'rom': {'α': (0, 3), 'β': (4, 0), 'γ': (-7, 9), 'δ': (-2, 0), 'ε': (8, 0), 'η': (0, 34), 'θ': (7, 15), 'ι': (2, 0), 'λ': (0, -23), 'π': (0, 24), 'ρ': (9, 1), 'σ': (-4, 0), 'τ': (0, 9), 'Δ': (20, 12), 'Λ': (3, 0), 'Ξ': (27, 8), 'Π': (-13, 1), 'Σ': (18, 0), 'Φ': (3, 0), 'Ω': (0, -17)},
    'ald': {'α': (0, -11), 'ε': (0, 7), 'ζ': (7, 0), 'η': (0, 37), 'θ': (0, 6), 'ι': (45, 0), 'κ': (-33, 23), 'μ': (4, 0), 'ξ': (5, 0), 'π': (0, -16), 'ρ': (32, 0), 'ς': (7, 7), 'υ': (0, 22), 'φ': (13, 21), 'χ': (0, 45), 'ψ': (0, 3), 'ω': (6, 20), 'Δ': (35, 0), 'Θ': (0, 1), 'Ξ': (0, 1), 'Π': (42, 2), 'Σ': (-9, 5), 'Φ': (19, 5), 'Ψ': (12, 14)},
    'bold': {'α': (0, 3), 'β': (4, 0), 'γ': (-7, 9), 'δ': (-2, 0), 'ε': (8, -6), 'ζ': (0, -12), 'η': (0, 34), 'θ': (-4, 11), 'ι': (5, 0), 'λ': (0, -23), 'μ': (1, -3), 'ν': (0, 5), 'π': (-17, 24), 'ρ': (15, 1), 'σ': (-1, 0), 'ς': (1, 0), 'τ': (-13, 12), 'φ': (1, 0), 'ψ': (-3, 0), 'Δ': (20, 12), 'Ξ': (31, 22), 'Π': (-4, 1), 'Σ': (18, 0), 'Φ': (8, 0), 'Ψ': (-2, 0), 'Ω': (0, -17)},
}
GREEK_SPACING = os.environ.get("ALBO_GREEK_SPACING", "1") != "0"   # 0 = the straight/straight default, as before round 379
_FITTED = {}    # ch -> (lsb, rsb, space) of every glyph fitted so far in this build


def _band_extent(ch, conts, space):
    """A glyph's ink extremes in the band its fitter reads: 'ald' is
    fit_aldine's (unsheared, on the ROUNDED y), 'rom' is fit()'s (as drawn,
    the x-height band or the cap band for a capital)."""
    if space == 'ald':
        sh = pen.SHEAR; lo, hi = -pen.OVER, pen.XH + pen.OVER
        band = [x - sh * y for pts, _ in conts for x, y in pts if lo <= round(y) <= hi]
        xs = [x - sh * y for pts, _ in conts for x, y in pts]
    else:
        top = C if ch.isupper() else pen.XH
        band = [x for pts, _ in conts for x, y in pts if -pen.OVER <= y <= top + pen.OVER]
        xs = [x for pts, _ in conts for x, y in pts]
    return (min(band), max(band)) if band else (min(xs), max(xs))


def fit_greek(ch, conts):
    """The Greek letter's two sides from its Latin analogues (GREEK_SIDES), or
    None when an analogue has not been fitted in this build."""
    la, ra = GREEK_SIDES[ch]
    if la not in _FITTED or ra not in _FITTED: return None
    lsb, _, ls = _FITTED[la]; _, rsb, rs = _FITTED[ra]
    _adj = GREEK_SIDE_ADJ['ald' if (ALD is not None and ALD.ON) else ('bold' if pen.S > 84.0 else 'rom')].get(ch)
    if _adj: lsb += _adj[0]; rsb += _adj[1]
    # both analogues of a letter are fitted in one space (a lowercase pair is
    # both 'ald' in the aldine italic, everything else 'rom'); the glyph is read
    # in the LEFT one's, which is where its origin sits.
    l0, r0 = _band_extent(ch, conts, ls)
    adv = lsb + (r0 - l0) + rsb
    dx = lsb - l0
    return adv, dx, min(x for pts, _ in conts for x, y in pts) + dx



FIG_BODY = float(os.environ.get("ALBO_ALD_FIG_BODY", "0.75"))     # round 216, set below
FIG_BODY_Q = float(os.environ.get("ALBO_ALD_FIG_BODY_Q", "80"))
# Absorbing the overhang also TIGHTENS the whole set, because most digits own
# some. FIG_TRACK gives it back uniformly, per side, so the two decisions stay
# separate: FIG_BODY is the evenness and FIG_TRACK is the colour.
FIG_TRACK = float(os.environ.get("ALBO_ALD_FIG_TRACK", "20"))
# ROUND 223 -- THE ROMAN'S FIGURES GET THE SAME FIT. The misfit audit
# (docs/albo-misfit-audit-2026-09-18.md) found round 216's body fit had been
# gated to the italic, so the roman's digits were still fitted on their reach:
# spread 2.10x against the italic's 1.31x, `00` 0.081 em against `47` 0.266.
# Its own two dials, because the roman's overhangs are smaller (no tails swing
# under the baseline) and it wants less absorbed and less given back.
ROM_FIG_BODY = float(os.environ.get("ALBO_ROM_FIG_BODY", "0.45"))
ROM_FIG_TRACK = float(os.environ.get("ALBO_ROM_FIG_TRACK", "8"))
# ROUND 226 -- the export smooths every contour between its corners; see
# geom.smooth_corners for the measurement that found the wobble was the
# polygon and not the imperfection tables. 0 is the old export byte for byte.
CURVES = int(os.environ.get("ALBO_CURVES", "0"))   # OFF (round 231): with the clearance guard it is gate-clean on 119 but adds one finding on the 290 sweep and smooths only bowls; the bumps are being marked for the owner instead -- docs/albo-method.md
CURVE_TURN = float(os.environ.get("ALBO_CURVE_TURN", "28"))
CURVE_STEP = int(os.environ.get("ALBO_CURVE_STEP", "3"))   # every 3rd dense point (~33 units) is interpolated
CURVE_DEV = float(os.environ.get("ALBO_CURVE_DEV", "1.2"))
CURVE_CLEAR = float(os.environ.get("ALBO_CURVE_CLEAR", "44"))   # a run within this of its contour's other side stays a polygon   # a contour whose curve leaves the polygon by more falls back to it
CURVE_FALLBACKS = [0, 0]   # (contours fitted, contours that fell back) -- printed at the end of a build
from fontTools.cu2qu import curve_to_quadratic as _c2q


def _cu2qu(p0, c1, c2, p3, dx):
    """One fitted cubic to TrueType quadratics, translated by the fit's dx and
    rounded; p0 is the pen's current point (fontTools tracks it as the last
    point emitted, so the caller passes it via the qCurveTo chain)."""
    global _LAST
    a = _LAST
    cub = [(a[0], a[1]), (c1[0] + dx, c1[1]), (c2[0] + dx, c2[1]), (p3[0] + dx, p3[1])]
    q = _c2q(cub, 0.75)
    _LAST = (p3[0] + dx, p3[1])
    return [(round(x), round(y)) for x, y in q[1:]]
_LAST = (0.0, 0.0)
def _LAST_SET(p):
    global _LAST
    _LAST = p


def _body_edges(conts, q=80.0):
    """Where a glyph STANDS on each side, as a percentile of its per-row ink
    extremes -- docs/albo-spacing-method.md measure 3. The contours arrive
    SHEARED (see fit_aldine), which is what we want: a gap is judged on the
    shipped shape, and shear moves both glyphs of a pair equally at any one
    row."""
    rows = {}
    for pts, _ in conts:
        for x, y in pts:
            k = int(y // 12)
            lo, hi = rows.get(k, (x, x))
            rows[k] = (min(lo, x), max(hi, x))
    if not rows: return 0.0, 0.0
    los = sorted(v[0] for v in rows.values()); his = sorted(v[1] for v in rows.values())
    def pct(a, p):
        if len(a) == 1: return a[0]
        i = (len(a) - 1) * p / 100.0; f = int(i)
        return a[f] + (a[min(f + 1, len(a) - 1)] - a[f]) * (i - f)
    return pct(los, 100.0 - q), pct(his, q)


# ROUND 388b -- TRACKING OPTIONS FOR THE OWNER, DEFAULT UNCHANGED. The re-ask
# bench (docs/albo-kerning-noise-floor-2026-09-25.md, RESULT) found his answers
# +5.4 units looser than his 09-21 ones on typical rows: lowercase +6.1, marks
# +6.3, capitals +2.7. That is a global preference no pair fit can express. Owner
# 2026-09-25, "show me options first": so ALBO_TRACK=a|b|c. His pick, the same
# day: *"c . +6 (caps +3)"* -- round 393 made **c the shipped default**; a and b
# stay selectable (ALBO_TRACK=a is the pre-393 font, byte for byte).
#
# Each arm is stated as what a bench PAIR gains, and every side is derived from
# that. A lowercase pair is rsb(l) + lsb(l), so the lowercase takes half on each
# side. A mark pair is a lowercase letter's side plus the mark's side, so the
# mark takes the other half. A bench CAPITAL pair is a capital followed by a
# lowercase letter (Fi, Ye, Qu ...), so the lowercase letter's own left half
# already delivers the capital target. The capitals themselves do not move, and
# neither do the figures, the fences or the Greek, because none was judged.
#   a  lowercase +0, marks +0, capital pairs +0    (rounds 388-392)
#   b  lowercase +3, marks +3, capital pairs +1.5
#   c  lowercase +6, marks +6, capital pairs +3    (SHIPPED since round 393)
# Applied after fit(), before anything records the advance or the ink, so the
# accented composites follow their base. The explicit kerns are NOT re-derived:
# his bench answers were read against arm a, and c is a uniform shift he asked
# for on top of them, so every pair's white moves by the same amount and the
# kerns keep their relation to each other (round 393's doc).
# docs/albo-round-388-2026-09-25.md, docs/albo-round-393-2026-09-25.md.
TRACK_ARMS = {'a': 0.0, 'b': 1.5, 'c': 3.0}   # units per SIDE
ALBO_TRACK = (os.environ.get("ALBO_TRACK", "c").strip().lower() or "c")
if ALBO_TRACK not in TRACK_ARMS:
    raise SystemExit(f"ALBO_TRACK={ALBO_TRACK!r}: expected one of {sorted(TRACK_ARMS)}")
TRACK_MARKS = set(".,:;!?'\"‘’“”…-")   # the bench's MARKS (bench_fit.py), with the curly forms and the ellipsis the stops/quotes fit as
def _track_side(ch):
    t = TRACK_ARMS[ALBO_TRACK]
    if not t: return 0.0
    latin_lc = ch.isalpha() and ch.islower() and (ord(ch) < 0x370 or 0xFB00 <= ord(ch) <= 0xFB06)
    return t if (latin_lc or ch in TRACK_MARKS) else 0.0

def fit(ch, conts, c):
    """Round 20's bearing rule: ink measured in the x-height band (cap band
    for capitals and figures); the g and every non-letter on their full
    extent; bearing per side = capbear x SIDE_FRACTION + 17."""
    # The Aldine lowercase only (round 133), and only when that module is the
    # live italic: everything else in the font -- the roman, the classic
    # italic, the capitals, the figures and the punctuation, including under
    # ALBO_ITALIC=aldine -- falls straight through to the rule below.
    if ALD is not None and ALD.ON and ch in ALD.BEARINGS:
        return fit_aldine(ch, conts)
    if GREEK_SPACING and ch in GREEK_SIDES:
        _g = fit_greek(ch, conts)
        if _g is not None: return _g
    isCap = ch.isupper() or isfig(ch); top = C if isCap else pen.XH
    xs_all = [x for pts, _ in conts for x, y in pts]
    band = [x for pts, _ in conts for x, y in pts if -pen.OVER <= y <= top + pen.OVER]
    l, r = (min(band), max(band)) if band else (min(xs_all), max(xs_all))
    # The g is fitted on its FULL extent because its descender IS the letter.
    # The J joins it (2026-09-15) for the same reason and because the band rule
    # fails outright once its hook clears the cap band: with the hook below
    # -OVER the band holds only the stem, so the glyph is fitted as a bare
    # vertical and the hook lands 190 units left of the origin with the advance
    # collapsed from 410 to 217. That is what every rung of the J_DROP ladder
    # hit before this line changed.
    if ch in ('g', 'J') or not ch.isalpha(): l, r = min(xs_all), max(xs_all)
    # ROUND 216 -- THE ITALIC FIGURES ARE FITTED ON THEIR BODY, NOT THEIR REACH.
    # Owner 2026-09-18: *"correct numeral spacing."* Measured
    # (`cmp_figure_space.py`), the italic's figure gaps track, almost exactly,
    # how far each digit REACHES past where it stands: the 9 owns 0.114 em of
    # open white on its left (its tail) and its left flank is the loosest in the
    # set at 0.222, while the 0 owns 0.004 and is the tightest at 0.112. The
    # line above hands the bearing rule the extreme, so every overhang is paid
    # for twice -- once as the glyph's own shape and again as spacing. That is
    # docs/albo-spacing-method.md's measure-1 failure, in the figures, and the
    # cure it names is measure 3: take the edge where the glyph STANDS.
    # FIG_BODY is how much of the overhang is absorbed; 0 is the old rule.
    _ald_on = ALD is not None and ALD.ON
    _fb = FIG_BODY if _ald_on else ROM_FIG_BODY
    if _fb and isfig(ch):
        bl, br = _body_edges(conts, FIG_BODY_Q)
        l += (bl - l) * _fb; r += (br - r) * _fb
    lt, rt = SIDES.get(ch, ('straight', 'straight') if ch.isalnum() else ('punct', 'punct'))
    capbear = REF["Hbear"] / 2 * C * pen.WIDTH   # the fitting follows the width axis
    lsb = capbear * A.SIDE_FRACTION[lt] + 17; rsb = capbear * A.SIDE_FRACTION[rt] + 17
    # Round 96 (owner 2026-09-14): "give punctuation more space, similar to the
    # spacing work that double quotes recently received" and "'a' does not have
    # enough space to its left ... 'ja' should have much more space". The marks
    # were fitted at 0.5 of a straight side (31 units against the n's 45; Albertus
    # 74 / n 49, Garamond 60 / 24, Berkeley 82 / 16), the a's left at the round
    # 0.72 though its hood hangs over open space (Garamond 37 / n 24, Berkeley
    # 33 / 16). Picked on a ladder: marks 1.5 (59), fences and dashes 1.0 (45),
    # the a's left 2.0 (73).
    # Round 97b (owner: "punctuation is still too close. it needs to breathe"): marks 60 -> 80 (Berkeley 82, Albertus 74), fences 45 -> 60
    if ch in PUNCT_MARKS:
        _pf = (ALD_STOP_BEAR if (ALD is not None and ALD.ON and ch in PUNCT_STOPS) else 2.25)
        lsb = capbear * _pf + 17; rsb = capbear * _pf + 17
    elif ch in PUNCT_FENCES or (not ch.isalnum() and ch not in SIDES): lsb = capbear * 1.55 + 17; rsb = capbear * 1.55 + 17   # round 99: every new symbol takes the fences' bearing rather than the tighter default
    if ch == 'a': lsb = capbear * A_LEFT + 17
    if ch == 'j': rsb = capbear * J_RIGHT + 17
    _ft = FIG_TRACK if (ALD is not None and ALD.ON) else ROM_FIG_TRACK
    if _ft and isfig(ch):
        lsb += _ft; rsb += _ft
    if ALD is not None and ALD.ON and ch in ALD_PUNCT_ADJ:
        lsb += ALD_PUNCT_ADJ[ch][0]; rsb += ALD_PUNCT_ADJ[ch][1]
    if not (ALD is not None and ALD.ON):
        _rp = ROM_PUNCT_ADJ.get(ch) or (ROM_PUNCT_ADJ["'"] if ch in PUNCT_QUOTES else None)
        if _rp: lsb += _rp[0]; rsb += _rp[1]
    if ALD is not None and ALD.ON and ch in PUNCT_QUOTES:
        rsb += ALD_QUOTE_RSB; lsb += ALD_QUOTE_LSB
    if ch in BEARING_ADJ: lsb += BEARING_ADJ[ch][0]; rsb += BEARING_ADJ[ch][1]
    if not (ALD is not None and ALD.ON) and ch in ROM_LC_ADJ:
        lsb += ROM_LC_ADJ[ch][0]; rsb += ROM_LC_ADJ[ch][1]      # round 308
    if ALD is not None and ALD.ON and ch in ALD_FIG_ADJ:
        lsb += ALD_FIG_ADJ[ch][0]; rsb += ALD_FIG_ADJ[ch][1]    # round 376
    if not (ALD is not None and ALD.ON) and ch in ROM_CAP_ADJ:
        lsb += ROM_CAP_ADJ[ch][0]; rsb += ROM_CAP_ADJ[ch][1]    # round 373
    # ROUND 137: the owner's own capital spacing, set live on the bench and
    # applied as a delta on the rule above -- aldine italic only.
    if ALD is not None and ALD.ON and ch in getattr(ALD, 'CAP_BEARING_ADJ', {}):
        lsb += ALD.CAP_BEARING_ADJ[ch][0]; rsb += ALD.CAP_BEARING_ADJ[ch][1]   # round 97: the lowercase solve
    adv = lsb + (r - l) + rsb; dx = lsb - l
    _FITTED[ch] = (lsb, rsb, 'rom')    # round 379: the Greek's analogues read this
    return adv, dx, min(xs_all) + dx

WEIGHT_CLASS = {"Thin": 100, "ExtraLight": 200, "Light": 300, "Regular": 400, "Medium": 500, "SemiBold": 600, "Bold": 700,
                "Italic": 400, "MediumItalic": 500, "SemiBoldItalic": 600, "BoldItalic": 700, "ExtraBold": 800, "Black": 900}   # round 272: the Black declared 400 (adversarial review)   # round 268: "Italic" is the REGULAR's italic since the re-anchor (round 266) and declares 400 like it -- round 261 had it at 500 when the Medium was the text weight; the pair must declare ONE weight or the family will not bind   # round 100: an italic style name must still carry its weight, or a Bold Italic ships as a 400

# Round 100, the vertical metrics (they were 900/-300 with no measurement
# behind them). Measured across every style: the ink reaches 971 on the
# Regular and 996 on the Bold (h-circumflex, an accented ascender) and -298
# to -317 (g, y). usWinAscent at 900 was therefore BELOW the ink and clipped
# in any rasteriser that honours it. The line is set to 1.30 em, which is EB
# Garamond's (the references run 1.17 Berkeley, 1.24 Albertus, 1.31
# Garamond) and the only one of the three that clears an accented capital
# over a descender without collision: 1000 + 300 = 1300 against an ink span
# of 1269. The reader can still override per family through `metrics:` in
# sd-fonts.yaml, which is where a per-size reading line belongs.
VM_ASCENT, VM_DESCENT = 1000, -300
VM_WIN_ASCENT, VM_WIN_DESCENT = 1000, 320

# ROUND 384 -- THE CURVE FIT'S SPURS, removed at export. Owner 2026-09-24,
# "take three passes at all albo fonts, find any issues and fix them". Round
# 295's `geom.despike` cures the integer grid's spikes, but only on the
# no-curve FALLBACK path; a contour that goes through `geom.fit_curves` never
# meets it, and the fit leaves its own: the Bold m carried a 2-unit spur at the
# bottom of the notch between its arches, the Bold OE two, the bishop one --
# every one a HAIR to `cmp_contour_hairs.py` (a turn past 150 degrees with an
# arm under 8 units), none in the dense drawing (probed per glyph).
#
# THE TEST IS THE GATE'S OWN DEFINITION, narrowed twice so a real corner cannot
# qualify: an ON-curve vertex between two ON-curve neighbours (a curve's
# junction is never touched), turning past 150 degrees, whose SHORTER arm is
# under 8 units -- and which stands no further off its neighbours' chord than
# that short arm, i.e. it is the tip of a spur a few units long. A wedge's or an
# arrow's tip has two long arms and fails the second clause; a serif's facet is
# not a reversal and fails the first.
# THE CUT'S PHASE COUNTER IS GLOBAL (`cut.Cutter`: one phase per contour, in
# glyph order), so a glyph that gains or loses a contour shifts the cut of
# every glyph drawn after it -- measured on this round's first build, 60 glyphs
# of the 400s moved that no fix touched. The glyphs below changed their contour
# count only because a defect was fixed (round 384), so each goes on consuming
# the count it had before; a contour beyond that draws its phase from a side
# counter. Proof: `cmp_outlines.py` against the previous build moves only the
# glyphs a fix named.
PHASE_LEGACY = {'\u2033': 1, '\u221a': 2, '\u2660': 2, '\u2663': 2, '\u2664': 4, '\u2667': 5}
# ROUND 385: the chess pieces were redrawn as Staunton figurines (owner
# 2026-09-24, "improve the chess, card and other symbols"), which changed nine
# of their contour counts -- the white queen's ten (five hollow balls, crown
# windows) became three. Each keeps consuming what round 99's drawing did.
# The hollow spade and club were already here, and keep their round-384 counts.
# ...and a count that changed in ONE style only is keyed by style: the italic
# fh (U+E001) was two islands and is one (its hook now joins the aldine h),
# while the roman fh was always one -- a global entry would re-cut the roman.
PHASE_LEGACY_STYLE = {('Italic', '\ue001'): 2}
PHASE_LEGACY.update({'\u2654': 2, '\u2655': 10, '\u2656': 2, '\u2657': 4, '\u2658': 2, '\u2659': 2,
                     '\u265b': 4, '\u265d': 2, '\u265e': 1})
# 2026-09-24 -- THE SAME CONTAINMENT FOR AN OPTION. A glyph drawn under an
# option env (docs/albo-yen-quote-options-2026-09-24.md) consumes the phase
# count of its DEFAULT drawing, whatever the option draws: the yen's gap options
# add islands, and without this choosing one would re-cut every glyph after the
# yen. The default is re-drawn with the option forced to `a` to count it; with
# every option unset this returns None and nothing here runs.
OPTION_PHASE = {'ALBO_YEN_GAP': '\u00a5', 'ALBO_QUOTE_SYM': '\'"\u2018\u2019\u201c\u201d\u02bc\u02bb'}
def _option_phase_k(ch, W):
    # ALWAYS count the `a` drawing, not only when an env var picks another:
    # two options now SHIP as code defaults (the italic yen's b, the straight
    # quotes' c, owner 2026-09-24), and a default is as able to add islands as
    # an env var is.
    for var, chars in OPTION_PHASE.items():
        if ch in chars:
            saved = os.environ.get(var); os.environ[var] = 'a'
            try: return len(geom.contours(draw(ch, W)))
            finally:
                if saved is None: del os.environ[var]
                else: os.environ[var] = saved
    return None

SPUR_ARM = 8.0
SPUR_TURN = 150.0
def _despur(glyph):
    if glyph.numberOfContours <= 0: return glyph
    coords = list(glyph.coordinates); flags = list(glyph.flags); ends = list(glyph.endPtsOfContours)
    cos_lim = math.cos(math.radians(180.0 - SPUR_TURN))
    out_c, out_f, out_e, start = [], [], [], 0
    for end in ends:
        pts = list(zip(coords[start:end + 1], flags[start:end + 1])); start = end + 1
        changed = True
        while changed and len(pts) > 3:
            changed = False
            n = len(pts)
            for i in range(n):
                (a, fa), (b, fb), (c, fc) = pts[i - 1], pts[i], pts[(i + 1) % n]
                if not (fa & 1 and fb & 1 and fc & 1): continue
                ax, ay = a[0] - b[0], a[1] - b[1]; cx, cy = c[0] - b[0], c[1] - b[1]
                la, lc = math.hypot(ax, ay), math.hypot(cx, cy)
                if la < 1e-9 or lc < 1e-9:
                    del pts[i]; changed = True; break          # a duplicate point
                if min(la, lc) >= SPUR_ARM: continue
                if (ax * cx + ay * cy) / (la * lc) < cos_lim: continue
                chord = math.hypot(a[0] - c[0], a[1] - c[1])
                dev = abs(ax * cy - ay * cx) / chord if chord > 1e-9 else 0.0
                if dev > min(la, lc): continue
                del pts[i]; changed = True; break
        out_c += [p for p, _ in pts]; out_f += [f for _, f in pts]; out_e.append(len(out_c) - 1)
    from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates
    from array import array
    glyph.coordinates = GlyphCoordinates(out_c); glyph.flags = array('B', out_f); glyph.endPtsOfContours = out_e
    return glyph

def build(out_dir, name="Albo", style="Medium", do_cut=True, only=None, dump=None):   # owner 2026-09-13, round 83: today's cut is the 500, "Rename to Medium"; the calibrated 400 is Albo-Regular
    os.makedirs(out_dir, exist_ok=True)
    W = solve_widths()
    cutter = cut.Cutter(73, 4)
    fb = FontBuilder(1000, isTTF=True); fb.setupGlyphOrder(GLYPH_ORDER)
    fb.setupCharacterMap({ord(ch): gname(ch) for ch in CHARS} | {ord(ch): gname(ch) for ch in ACC_CHARS} | {ord(ch): gname(ch) for ch in COMB_CHARS} | {32: 'space'})
    glyphs, metrics, report = {}, {}, {}
    ink, advances = {}, {}      # round 99: per-char ink bbox and advance, for the accent composites
    inkband = {}                # round 392: ACC_BAND's stem-top extent
    for ch in CHARS:
        c = ctx(ch, W)
        if ch in GLYPHS and (only is None or ch in only):
            g = draw(ch, W); dense = geom.contours(g)
            # round 62: the cut is an amount on the DENSE point set (cut.blend):
            # every point kept, the dropped ones moved onto their chords -- the
            # same construction the variable font's masters use
            # ROUND 384: a glyph whose contour count a fix changed still
            # consumes the phases it used to, so the cut pattern of every
            # glyph AFTER it -- the Greek, the ligatures, the fractions -- does
            # not move. See PHASE_LEGACY.
            _k = (PHASE_LEGACY_STYLE.get((style, ch)) or PHASE_LEGACY.get(ch)
                  or _option_phase_k(ch, W) or len(dense))
            phases = [cutter.phase() for _ in range(_k)]
            if len(dense) > _k:
                phases += [cut.Cutter(911, cutter.every).phase() for _ in range(len(dense) - _k)]
            phases = phases[:len(dense)]
            amount = pen.CUT_AMOUNT if do_cut else 0.0
            lines = (0.0, pen.XH, pen.CAP) if not isfig(ch) else (0.0, pen.XH, pen.CAP, (latin.FIG_BOX[ch][0] - latin.FIG_BOX[ch][1]) * C)   # round 93: the baseline, x-height and cap line are pinned through the cut
            conts = [(cut.blend(pts, ph, amount, lines=lines), hole) for (pts, hole), ph in zip(dense, phases)]
        else:
            conts = []; dense = []; phases = []
        pen_ = TTGlyphPen(None)
        if conts:
            adv, dx, lsb_ink = fit(ch, conts, c)
            _tk = _track_side(ch)          # round 388b; arm c ships (round 393), ALBO_TRACK=a gives 0
            if _tk: adv += 2 * _tk; dx += _tk; lsb_ink += _tk
            for ci, (pts, hole) in enumerate(conts):
                _obst = [q for cj, (p2, _) in enumerate(conts) if cj != ci for q in p2] if CURVES else None
                fitted = geom.fit_curves(pts, turn=CURVE_TURN, step=CURVE_STEP, max_dev=CURVE_DEV, clearance=CURVE_CLEAR, obstacles=_obst) if CURVES else None
                if fitted is not None:
                    CURVE_FALLBACKS[0] += fitted[2]; CURVE_FALLBACKS[1] += fitted[3]; fitted = fitted[:2]
                if fitted is None:
                    # round 296: the vertices that lie ON the line they are in the
                    # middle of, dropped BEFORE the rounding (afterwards the grid has
                    # already moved them off it), then round 295's spikes
                    q = geom.despike([(round(x + dx), round(y)) for x, y in geom.drop_collinear(pts)])
                    if len(q) < 3: continue
                    pen_.moveTo(q[0])
                    for p in q[1:]: pen_.lineTo(p)
                    pen_.closePath(); continue
                # round 226: quadratic curves between the contour's corners
                start, segs = fitted
                _LAST_SET((start[0] + dx, start[1]))
                pen_.moveTo((round(start[0] + dx), round(start[1])))
                for sg in segs:
                    if sg[0] == 'line':
                        _LAST_SET((sg[1][0] + dx, sg[1][1]))
                        pen_.lineTo((round(sg[1][0] + dx), round(sg[1][1])))
                    else:
                        c1, c2, p3 = sg[1], sg[2], sg[3]
                        quads = _cu2qu(None, c1, c2, p3, dx)
                        pen_.qCurveTo(*quads)
                pen_.closePath()
            report[ch] = dict(adv=adv, contours=len(conts), verts=sum(len(p) for p, _ in conts), lsb=lsb_ink, phases=phases,
                              pts=[([(x + dx, y) for x, y in pts], hole) for pts, hole in dense])   # the DENSE contours, translated by the cut's fit: the variable builder's master input
        else:
            adv, lsb_ink = 300, 0
        if conts:
            xs = [x for pts, _ in conts for x, y in pts]; ys = [y for pts, _ in conts for x, y in pts]
            ink[ch] = (min(xs) + dx, min(ys), max(xs) + dx, max(ys))
            if ch in ACC_BAND:
                bxs = [x for pts, _ in conts for x, y in pts if pen.XH * 0.6 <= y <= pen.XH + pen.OVER]
                if bxs: inkband[ch] = (min(bxs) + dx, max(bxs) + dx)
        advances[ch] = adv
        glyphs[gname(ch)] = _despur(pen_.glyph()); metrics[gname(ch)] = (int(round(adv)), int(round(lsb_ink)))
    # ------------------------------------------------ round 99: the composites
    # An accented letter is its base plus its mark, both as components: the
    # letter is never redrawn, so a later round that changes the e changes
    # every e-acute with it, and the file pays for one outline instead of 161.
    for ch in ACC_CHARS:
        base, mark, kind = ACCENTED[ch]
        if kind == 'copy' and base in ink and (only is None or ch in only):   # round 379: the Greek that is the Latin letter
            cp = TTGlyphPen(glyphs); cp.addComponent(gname(base), (1, 0, 0, 1, 0, 0))
            glyphs[gname(ch)] = cp.glyph()
            metrics[gname(ch)] = (int(round(advances[base])), int(round(ink[base][0]))); continue
        if (only is not None and ch not in only) or base not in ink or mark not in ink:
            # round 101: still EMIT the glyph, empty. setupHorizontalMetrics
            # needs a row for every name in the glyph order, so a skipped
            # composite under --only used to fail the whole build with a
            # KeyError on the first accented capital.
            glyphs[gname(ch)] = TTGlyphPen(None).glyph(); metrics[gname(ch)] = (300, 0); continue
        bx0, by0, bx1, by1 = ink[base]; mx0, my0, mx1, my1 = ink[mark]
        isCap = base.isupper()
        if kind == 'above':
            dx = (bx0 + bx1) / 2 - (mx0 + mx1) / 2
            if base in inkband: dx = sum(inkband[base]) / 2 - (mx0 + mx1) / 2
            dx += ACC_OPTICAL.get(base, 0.0) * pen.XH * ACC_OPTICAL_ON
            top = max(by1, C if isCap else pen.XH)
            dy = top + (ACC_GAP_CAP if isCap else ACC_GAP_LC) - my0
        elif kind == 'below':
            dx = (bx0 + bx1) / 2 - (mx0 + mx1) / 2
            dy = -my1            # the mark's own top to the baseline (it is drawn hanging from 0)
            # ROUND 375 -- THE COMMA BELOW STANDS FREE. It hung its top AT the
            # baseline while every round letter dips through it (the s by 15),
            # so s-comma and t-comma fused into one contour with their mark and
            # read as the cedilla forms beside them -- which is the one thing a
            # Romanian reader must be able to tell apart. The cedilla and the
            # ogonek attach by design and are untouched.
            if mark == "\u0326": dy -= pen.OVER + pen.S * 0.30
        else:                    # 'right': the Czech apostrophe-caron at the shoulder
            dx = bx1 + S_GAP_RIGHT - mx0; dy = pen.XH * 0.52 - my0
        cp = TTGlyphPen(glyphs)   # a composite pen needs the glyph set it references
        cp.addComponent(gname(base), (1, 0, 0, 1, 0, 0))
        cp.addComponent(gname(mark), (1, 0, 0, 1, int(round(dx)), int(round(dy))))
        glyphs[gname(ch)] = cp.glyph()
        adv = advances[base]
        if kind == 'right': adv = max(adv, bx1 + S_GAP_RIGHT + (mx1 - mx0) + 20)
        metrics[gname(ch)] = (int(round(adv)), int(round(bx0)))
    # The combining marks: the spacing mark's outline at ZERO advance, placed
    # where it would sit over a lowercase letter. A composite, so it is the
    # same drawing.
    for ch in COMB_CHARS:
        src = COMBINING[ch]
        if src not in ink:
            glyphs[gname(ch)] = TTGlyphPen(None).glyph(); metrics[gname(ch)] = (0, 0); continue
        mx0, my0, mx1, my1 = ink[src]
        below = src in ("\u00b8", "\u02db", "\u0326")
        dy = (-my1 if below else pen.XH + ACC_GAP_LC - my0)
        dx = -(mx0 + mx1) / 2
        cp = TTGlyphPen(glyphs)
        cp.addComponent(gname(src), (1, 0, 0, 1, int(round(dx)), int(round(dy))))
        glyphs[gname(ch)] = cp.glyph(); metrics[gname(ch)] = (0, 0)
    p = TTGlyphPen(None); p.moveTo((50, 0)); p.lineTo((50, 700)); p.lineTo((450, 700)); p.lineTo((450, 0)); p.closePath()
    glyphs['.notdef'] = p.glyph(); metrics['.notdef'] = (500, 50)
    # THE WORD SPACE (round 100, owner: "fix the space being way too wide").
    # It was 1.7 n-counters minus 110 = 356 units, 0.356 em and 0.61 of the n's
    # advance. Measured against the references the same way the LETTER fitting
    # is measured -- mean white across the x-height band, word against letter:
    #
    #   face                 letter   word   ratio   space
    #   Albertus               178     446    2.51     313
    #   EB Garamond            194     370    1.91     200
    #   ITC Berkeley           191     427    2.24     259
    #   Albo, before           232     554    2.39     356
    #
    # The RATIO was never far off; the trouble is that Albo's letters are
    # already the loosest of the four (232 against 178-194), so the same ratio
    # puts its word gap 25-50% past every reference in absolute white. Set to
    # the mean ratio of the two TEXT faces (2.07; Albertus is a display cut and
    # its 2.51 is not a reading target), which lands on 285 -- and confirmed on
    # a five-rung paragraph ladder at 13 pt, where 225 begins to crowd "low
    # over" and 320 still reads as holes.
    #
    # Kept proportional to the n counter so it tracks any later move in weight
    # or width, as the old rule did.
    SPACE_COUNTERS = 1.039
    space_adv = pen.N_COUNTER_FULL * SPACE_COUNTERS + WORD_SPACE_ADJ
    # ROUND 133: THE ALDINE ITALIC GETS ITS OWN WORD SPACE, because its
    # letters are no longer the roman's. That derivation above hangs off
    # `pen.N_COUNTER_FULL` -- the ROMAN's n counter, 272 -- and the Aldine
    # lowercase's counter is 153, so the space did not follow the letters in
    # when they were re-fitted. Measured the same way the letter fitting is
    # (mean white across the x-height band, word against letter):
    #
    #   face        letter white   word/letter   space, Albo units
    #   Flanker          167           2.95            326
    #   Pagella          151           2.47            223
    #   Poetica          124           2.32            163
    #   Albo aldine      115           3.25            259   <- before
    #
    # The ratio was the loosest of the four by 10%, on the tightest letters of
    # the four -- which is the same trap round 100 recorded for the roman,
    # arriving from the other side: there the letters were loose and the ratio
    # fine. At the three references' mean ratio of 2.58 the space is 182.
    from .glyphs import aldine as _ALD
    if _ALD.ON:
        # 182 -> 166 (his own number off the bench) -> 205 in round 137's
        # improving pass. His 166 was chosen at 64 px BEFORE his tracking was
        # baked into the letters; with it in, the word gap measures 2.22 of
        # the letter gap against every text reference's 2.32-2.95 (Poetica
        # 2.32, Pagella 2.47, Flanker 2.95, mean 2.58) -- and at 27 px "It is
        # a truth" set as "It isa truth". 205 puts the ratio at 2.51.
        # ROUND 358 -- 205 -> 240, so the ITALIC'S word space stands in the same
        # relation to its own letters that the ROMAN's does. Owner 2026-09-21,
        # "adjust albo's word spacing based on research from other fonts and
        # optical principles", then "proceed".
        #
        # WHAT THE RESEARCH ACTUALLY SAID, because it did not say "widen":
        # measured against five text romans two ways, the answers point
        # OPPOSITE ways. Absolute, Albo's roman space is the widest of the set
        # (0.312 em against 0.241-0.278). Relative to its own letterfit --
        # Measure 4, the 2-D closest approach -- the romans cluster hard at
        # 3.26-3.47 and Albo reads 2.64, which says widen to 0.40. They
        # disagree because Albo's letters are LOOSE (0.118 em against a
        # 0.072-0.088 band), and the loose fitting is round 258's "leave the
        # tracking alone".
        #
        # THE ROMAN THEREFORE DOES NOT MOVE. Its 312 is 285 from round 100's
        # absolute fit plus the owner's OWN +27 from the round-202 phone bench
        # -- his eye, at reading size, on the device -- and it sits 8 units
        # under the value round 100's own 13 pt ladder called "holes". Two
        # instruments that contradict each other do not outrank that.
        #
        # THE ITALIC IS WHAT MOVES, and on the one comparison that needs no
        # external band: the two styles disagreed with EACH OTHER. Against
        # italic references (measured with italic faces, not the romans -- the
        # first pass used the wrong set) Albo's italic is mid-band on absolute,
        # 0.232 em in a 0.205-0.278 spread, so nothing external asks for a
        # change; but its space-to-letterfit ratio is 2.30 where the roman's is
        # 2.64, so the same word set tighter in italic. 240 + the owner's 27
        # gives 267 units, ratio 2.64 -- the roman's exactly -- and stays
        # inside the italic references' absolute spread.
        # ROUND 359: 240 -> 242, so the italic lands on the same 2.55 the owner
        # ruled for the roman -- 2.55 x its own 0.101 em letterfit is 258, and
        # 242 + his 16 gives it. The pair stays matched, which is what round
        # 358 set out to do; only the number they match AT has moved.
        space_adv = 242.0 * (pen.XH / 429.0) + WORD_SPACE_ADJ
    glyphs['space'] = TTGlyphPen(None).glyph(); metrics['space'] = (int(round(space_adv)), 0)
    fb.setupGlyf(glyphs); fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=VM_ASCENT, descent=VM_DESCENT, lineGap=0)
    if "Italic" in style:   # round 100: the fsSelection ITALIC bit and the post table's angle
        _ital = True
    else:
        _ital = False
    # ROUND 261 -- THE FOUR STYLES HAVE TO BIND AS ONE FAMILY, or the bold is
    # unreachable. Owner 2026-09-19: "all commonly needed roman, italic, bold
    # and bold italic characters." Measured on the built fonts before this:
    # every style declared familyName "Albo" with the STYLE NAME as its
    # subfamily -- "Medium", "Italic", "Bold", "BoldItalic" -- and no
    # typographic names at all. The classic name table groups only the four
    # RIBBI slots (Regular / Italic / Bold / Bold Italic) by subfamily, so a
    # subfamily of "Medium" puts the roman in its own family and pressing the
    # bold button in any application cannot find the Bold. The italic also
    # declared usWeightClass 400 against its roman's 500, which separates the
    # pair again on weight.
    #
    # So: nameID 1/2 carry the RIBBI grouping (Albo + Regular/Italic/Bold/Bold
    # Italic, the Medium being this family's regular weight, which is the
    # owner's round-83 ruling "Rename to Medium"), and nameID 16/17 carry the
    # typographic truth (Albo + Medium / Medium Italic / Bold / Bold Italic)
    # for applications that read them. The full name (4) and the PostScript
    # name (6) keep the identity each style already shipped with, so an
    # installed Albo-Medium or Albo-Italic is not renamed under the owner --
    # except that "Albo BoldItalic" gains the space it was missing.
    _RIBBI = {"Medium": "Regular", "Italic": "Italic", "Bold": "Bold", "BoldItalic": "Bold Italic"}
    _TYPO  = {"Medium": "Medium", "Italic": "Italic", "Bold": "Bold", "BoldItalic": "Bold Italic"}   # round 268: the 400 italic is the REGULAR's italic since the re-anchor (round 266), so its typographic subfamily is "Italic" and its full name "Albo Italic"; "Medium Italic" named the retired 500 pairing
    _sub = _RIBBI.get(style, style); _typo = _TYPO.get(style, style)
    _full = f"{name} {_typo}"
    fb.setupNameTable(dict(familyName=name, styleName=_sub, fullName=_full, psName=f"{name}-{style}",
                           uniqueFontIdentifier=f"{name};{style};2026-09-13",
                           typographicFamily=name, typographicSubfamily=_typo))
    fb.setupOS2(sTypoAscender=VM_ASCENT, sTypoDescender=VM_DESCENT, sTypoLineGap=0, usWinAscent=VM_WIN_ASCENT, usWinDescent=VM_WIN_DESCENT, sxHeight=int(pen.XH), sCapHeight=int(C), usWeightClass=WEIGHT_CLASS.get(style, 400))
    fb.setupPost(italicAngle=-pen.SLANT)
    fb.font['OS/2'].fsSelection = 0x40 if style in ("Regular", "Medium") else 0x00   # REGULAR only on the regular (round 272: the Black and the ExtraLight carried it); cleared below by an italic or a bold
    if _ital:
        fb.font['OS/2'].fsSelection = (fb.font['OS/2'].fsSelection & ~0x40) | 0x01
        fb.font['head'].macStyle |= 0x02
    if 'Bold' in style:
        fb.font['OS/2'].fsSelection = (fb.font['OS/2'].fsSelection & ~0x40) | 0x20
        fb.font['head'].macStyle |= 0x01
    path = os.path.join(out_dir, f"{name}-{style}.ttf"); fb.save(path); TTFont(path)
    from . import kern as K; K.apply(path)   # round 95: the GPOS kern feature rides every build (outlines/kern.py)
    if dump:
        import json
        json.dump(dict(space=metrics['space'][0], W=W, params=dict(stem=pen.S, xh=pen.XH, asc=pen.ASC, desc=pen.DESC, contrast=pen.CONTRAST, width=pen.WIDTH, serif=pen.SERIF, cut=pen.CUT_AMOUNT),
                       glyphs={ch: dict(adv=r['adv'], lsb=r['lsb'], phases=r['phases'], contours=[(pts, hole) for pts, hole in r['pts']]) for ch, r in report.items()}), open(dump, 'w'))
    return path, W, report

if __name__ == "__main__":
    out = sys.argv[1]; do_cut = "--nocut" not in sys.argv
    style = sys.argv[sys.argv.index("--style") + 1] if "--style" in sys.argv else "Medium"
    dump = sys.argv[sys.argv.index("--dump") + 1] if "--dump" in sys.argv else None
    only = set(sys.argv[sys.argv.index("--only") + 1]) if "--only" in sys.argv else None   # round 98: build these chars only (the rest empty), for a variant ladder
    path, W, rep = build(out, style=style, do_cut=do_cut, dump=dump, only=only)
    if CURVES: print(f"curves: {CURVE_FALLBACKS[0]} runs fitted, {CURVE_FALLBACKS[1]} runs kept as polygon")
    if only: print("ok", path); sys.exit(0)
    if style != "Medium": print("ok", path); sys.exit(0)
    open(os.path.join(out, "albo-specimen.html"), "w").write(round19.page(path).replace("Round 19. The complete Latin set in one file, Fjord-Regular.ttf, on the k6 construction: capitals, lowercase, lining figures, text punctuation, quotes and dashes.", "Albo (named 2026-09-13, round 58; Fjord until then): all 93 glyphs as designed outlines under the standing rulings, the bowls on the Albertus-like firm profile he picked, the wedge family kept, the linear cut applied last. Design defaults: weight " + f"{pen.S:g}, contrast {pen.CONTRAST:g}, ascender {pen.ASC:g}, descender {pen.DESC:g}, width {pen.WIDTH * 100:g}, cut {pen.CUT_AMOUNT:g}, x-height {pen.XH:g}, serif {pen.SERIF * 100:g}.").replace("Fjord-Regular.ttf", "Albo-Medium.ttf").replace("Fjord", "Albo"))
    print("ok", path, len(rep), "glyphs drawn of", len(CHARS), "; caps W:", {k: round(v, 2) for k, v in sorted(W.items())})
