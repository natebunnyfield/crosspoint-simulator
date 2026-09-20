"""Build Albo-Medium.ttf (Albo-Regular until round 83; Fjord until round 58) from the designed outlines: draw, extract the
contours (exteriors ccw, counters cw), apply the linear cut, fit with the
round-20 rule, write the TrueType and the round-19 specimen.

    cd tools/wedge_serif && PYTHON_GIL=0 python3 -m outlines.build <out_dir> [--nocut]
"""
import os, sys, math
# round 202: the owner's own word space, from the phone bench
WORD_SPACE_ADJ = float(os.environ.get('ALBO_ALD_WORD_SPACE', 27.0))
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

ACC_GAP_LC = 0.10 * pen.XH      # the mark's foot over the x-height
ACC_GAP_CAP = 0.055 * pen.XH
S_GAP_RIGHT = 0.10 * pen.S     # the apostrophe-caron's gap off the letter's right ink    # tighter over a capital: the eye reads the cap line as the ceiling

LIGS = list("\ufb00\ufb01\ufb02\ufb03\ufb04") if os.environ.get("ALBO_LIGS") == "1" else []   # round 96: drawn; round 96b (owner): "no to ligatures for now" -- opt-in only
# Every character any glyph module registers and the record does not already
# name -- so a new module (round 99's symbols, the next round's chess) is in
# the font by existing, with no second list to keep in step.
EXTRA = sorted(set(GLYPHS) - set(round19.CHARS) - set(LIGS) - set(MARKS), key=ord)
CHARS = round19.CHARS + LIGS + MARKS + EXTRA; gname = round19.gname
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


def solve_widths(passes=3):
    """Capitals and figures: scale each glyph's width multiplier so its ink
    width lands on the references' median (round 20's rule, same clamps)."""
    W = {}
    for _ in range(passes):
        for ch in CHARS:
            if not (ch.isupper() or isfig(ch)) or ch in ('I', '1') or ch not in REF or ch not in GLYPHS: continue
            g = draw(ch, W); x0, y0, x1, y1 = geom.bbox(g); drawn = x1 - x0
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
            if drawn > 1: W[ch] = max(0.7, min(1.45, W.get(ch, 1.0) * (target / drawn) ** 0.85))
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
BEARING_ADJ = {'a': (-13, 3), 'b': (-4, 0), 'c': (2, 15), 'd': (3, 1), 'e': (2, -1), 'f': (5, 25), 'g': (-11, -19), 'h': (0, -2), 'i': (0, -1), 'j': (0, 14), 'k': (0, 18), 'l': (-3, 2), 'm': (0, -2), 'n': (4, 0), 'o': (0, -2), 'p': (-11, -1), 'q': (0, 37), 'r': (2, 13), 's': (17, 19), 't': (-11, 0), 'u': (-9, 3), 'v': (-1, -4), 'w': (6, 4), 'x': (42, 0), 'y': (0, 13), 'z': (0, -23), 'ﬀ': (0, 16)}
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
    if ALD is not None and ALD.ON and ch in PUNCT_QUOTES:
        rsb += ALD_QUOTE_RSB; lsb += ALD_QUOTE_LSB
    if ch in BEARING_ADJ: lsb += BEARING_ADJ[ch][0]; rsb += BEARING_ADJ[ch][1]
    # ROUND 137: the owner's own capital spacing, set live on the bench and
    # applied as a delta on the rule above -- aldine italic only.
    if ALD is not None and ALD.ON and ch in getattr(ALD, 'CAP_BEARING_ADJ', {}):
        lsb += ALD.CAP_BEARING_ADJ[ch][0]; rsb += ALD.CAP_BEARING_ADJ[ch][1]   # round 97: the lowercase solve
    adv = lsb + (r - l) + rsb; dx = lsb - l
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

def build(out_dir, name="Albo", style="Medium", do_cut=True, only=None, dump=None):   # owner 2026-09-13, round 83: today's cut is the 500, "Rename to Medium"; the calibrated 400 is Albo-Regular
    os.makedirs(out_dir, exist_ok=True)
    W = solve_widths()
    cutter = cut.Cutter(73, 4)
    fb = FontBuilder(1000, isTTF=True); fb.setupGlyphOrder(GLYPH_ORDER)
    fb.setupCharacterMap({ord(ch): gname(ch) for ch in CHARS} | {ord(ch): gname(ch) for ch in ACC_CHARS} | {ord(ch): gname(ch) for ch in COMB_CHARS} | {32: 'space'})
    glyphs, metrics, report = {}, {}, {}
    ink, advances = {}, {}      # round 99: per-char ink bbox and advance, for the accent composites
    for ch in CHARS:
        c = ctx(ch, W)
        if ch in GLYPHS and (only is None or ch in only):
            g = draw(ch, W); dense = geom.contours(g)
            # round 62: the cut is an amount on the DENSE point set (cut.blend):
            # every point kept, the dropped ones moved onto their chords -- the
            # same construction the variable font's masters use
            phases = [cutter.phase() for _ in dense]
            amount = pen.CUT_AMOUNT if do_cut else 0.0
            lines = (0.0, pen.XH, pen.CAP) if not isfig(ch) else (0.0, pen.XH, pen.CAP, (latin.FIG_BOX[ch][0] - latin.FIG_BOX[ch][1]) * C)   # round 93: the baseline, x-height and cap line are pinned through the cut
            conts = [(cut.blend(pts, ph, amount, lines=lines), hole) for (pts, hole), ph in zip(dense, phases)]
        else:
            conts = []; dense = []; phases = []
        pen_ = TTGlyphPen(None)
        if conts:
            adv, dx, lsb_ink = fit(ch, conts, c)
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
        advances[ch] = adv
        glyphs[gname(ch)] = pen_.glyph(); metrics[gname(ch)] = (int(round(adv)), int(round(lsb_ink)))
    # ------------------------------------------------ round 99: the composites
    # An accented letter is its base plus its mark, both as components: the
    # letter is never redrawn, so a later round that changes the e changes
    # every e-acute with it, and the file pays for one outline instead of 161.
    for ch in ACC_CHARS:
        base, mark, kind = ACCENTED[ch]
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
            top = max(by1, C if isCap else pen.XH)
            dy = top + (ACC_GAP_CAP if isCap else ACC_GAP_LC) - my0
        elif kind == 'below':
            dx = (bx0 + bx1) / 2 - (mx0 + mx1) / 2
            dy = -my1            # the mark's own top to the baseline (it is drawn hanging from 0)
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
        space_adv = 205.0 * (pen.XH / 429.0) + WORD_SPACE_ADJ
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
