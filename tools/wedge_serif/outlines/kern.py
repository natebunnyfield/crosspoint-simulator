"""Albo's kerning: hand class kerning, written into the TTF as a GPOS `kern`
feature (round 95, owner ruling 2026-09-14: "A. Hand class kerning").

Why classes and not pairs: the reader's `.cpfont` stores kerning as a class
matrix (`EpdKernClassEntry` x2 + an int8 matrix in 4.4 px), extracted from
the GPOS `kern` feature by `fontconvert_sdcard.py`; a class feature is the
native shape. Why these values: set by eye on the round-95 page, in steps of
18 units -- one sixteenth of a pixel at 13 pt on the 2x app (54 px em), the
reader's kern quantum there; the X3 at 1x quantizes at 37. Anything under
~36 is a no-op on the phone and everything under ~72 rounds to one or two
sixteenths on the device, so the table is coarse on purpose.

The lowercase is NOT kerned. Measured (exploration doc, round 95): the
firmware's counter-calibrated autokerner wants nothing from n+n, o+o, n+o,
o+n and a median of -24 from the 69 lowercase pairs it touches at all --
below the quantum. The fitting rule as ruled (round 3, "the distance
between characters should be the same as within") is right for the
lowercase; kerning here is the capitals with an overhang or a diagonal, and
the punctuation that tucks under one.

    cd tools/wedge_serif && python3 -m outlines.kern <font.ttf> [<out.ttf>]
    (in place when no out; outlines.build calls apply() on every build)
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(HERE))
import json
from fontTools.ttLib import TTFont
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString

STEP = 18   # the phone's kern quantum in design units at 13 pt (1/16 px at 54 px em)

# ---------------------------------------------------------------- classes
# LEFT classes describe the RIGHT side of the first glyph; RIGHT classes the
# LEFT side of the second. Glyph names are AGL (round19.gname).
LEFT = {
    'T':       ['T'],
    'VW':      ['V', 'W'],
    'Y':       ['Y'],
    'A':       ['A'],
    'L':       ['L'],
    'FP':      ['F', 'P'],
    'K':       ['K', 'k'],                      # arm and leg: the top-right is open
    'R':       ['R'],
    'Oleft':   ['C', 'G', 'O', 'Q'],            # round 177: a round capital BEFORE a V W Y -- see the note on that cell
    'r':       ['r'],
    'f':       ['f'],
    'vwy':     ['v', 'w', 'y'],
    'oround':  ['b', 'o', 'p'],                 # a round right side into a quote or a period tucks a little
    'quote':   ['quoteleft', 'quotedblleft', 'quoteright', 'quotedblright', 'quotesingle', 'quotedbl'],
    'period':  ['period', 'comma'],
    'e':       ['e'],
    'a':       ['a'],
    'cg':      ['c', 'g'],
    't':       ['t'],
    's':       ['s'],
}
RIGHT = {
    'round':   ['a', 'c', 'd', 'e', 'g', 'o', 'q', 's'],
    'flat':    ['n', 'm', 'r', 'u', 'p', 'i', 'j', 'z', 'x'],   # x: its left arm is low, so it takes the flat value
    'diag':    ['v', 'w', 'y'],
    'asc':     ['i', 'j', 'f', 't'],                            # tall on the left: a T's bar clears them less
    'ascwedge':['b', 'h', 'k', 'l'],                            # tall with a top-left wedge: the f's hook lands on it (round 96b)
    'a':       ['a'],
    'A':       ['A'],
    'T':       ['T'],
    'VWY':     ['V', 'W', 'Y'],
    'J':       ['J'],
    'O':       ['C', 'G', 'O', 'Q'],
    'period':  ['period', 'comma', 'ellipsis'],
    'hyphen':  ['hyphen', 'endash', 'emdash'],
    'quote':   ['quoteleft', 'quotedblleft', 'quoteright', 'quotedblright', 'quotesingle', 'quotedbl'],
    'colon':   ['colon', 'semicolon'],
}
# The `asc` and `flat` right classes overlap on i j; feaLib refuses a glyph in
# two classes of one PairPos, so asc is the class and i j leave flat:
RIGHT['flat'] = [g for g in RIGHT['flat'] if g not in RIGHT['asc'] + RIGHT['ascwedge'] + RIGHT['a']]
RIGHT['round'] = [g for g in RIGHT['round'] if g != 'a']

# ---------------------------------------------------------------- values
# (left class, right class) -> units. Multiples of STEP. Negative tightens.
# Round 96: the marks' bearings grew 31 -> 59, so the period and quote cells
# judged in round 95 moved one step deeper to keep the same tuck. Round 97b
# (owner: punctuation "needs to breathe"): marks 60 -> 80 and the period
# cells back that step.
CLASS_PAIRS = {
    # T: the bar overhangs; every lowercase tucks under it, rounds most
    ('T', 'round'): -126, ('T', 'a'): -126, ('T', 'flat'): -90, ('T', 'diag'): -90, ('T', 'asc'): -18, ('T', 'ascwedge'): -18,
    ('T', 'A'): -216, ('T', 'O'): -36, ('T', 'J'): -72,
    ('T', 'period'): -126, ('T', 'hyphen'): -108, ('T', 'colon'): -72,
    # V W: a diagonal right side; the rounds and the a tuck, the flats less
    ('VW', 'round'): -90, ('VW', 'a'): -90, ('VW', 'flat'): -54, ('VW', 'diag'): -36, ('VW', 'asc'): -18, ('VW', 'ascwedge'): -18,
    ('VW', 'A'): -216, ('VW', 'O'): -36, ('VW', 'J'): -54,
    ('VW', 'period'): -126, ('VW', 'hyphen'): -72, ('VW', 'colon'): -54,
    # Y: the deepest overhang after the T
    ('Y', 'round'): -108, ('Y', 'a'): -108, ('Y', 'flat'): -72, ('Y', 'diag'): -54, ('Y', 'asc'): -18, ('Y', 'ascwedge'): -18,
    ('Y', 'A'): -162, ('Y', 'O'): 0, ('Y', 'J'): -72,   # round 177: ('Y','O') -54 -> 0, the same re-solve as the Oleft cell
    ('Y', 'period'): -126, ('Y', 'hyphen'): -90, ('Y', 'colon'): -72,
    # A: its right side slopes away at the top, so the tall overhangs fall into it
    ('A', 'T'): -90, ('A', 'VWY'): -90, ('A', 'O'): -18, ('A', 'quote'): -126,
    ('A', 'diag'): -36,
    # L: open above its arm
    ('L', 'T'): -108, ('L', 'VWY'): -36, ('L', 'quote'): -144, ('L', 'O'): -18,
    ('L', 'diag'): -36, ('L', 'hyphen'): -54,
    # ROUND 177 -- THE Y AGAINST A ROUND. Owner 2026-09-16: *"adjust the letter
    # spacing of capitals especially after U and with Y"*. Re-solving the Y's
    # own bearings (aldine.CAP_Y_LSB / CAP_Y_RSB) fixed the letter against
    # flats and diagonals and left one family behind: Y beside a ROUND capital
    # stayed about 0.08 em tighter than the face's own rhythm -- LY, OY, YO, RY
    # -- because these cells were fitted to the Y of before round 163, which was
    # a wider letter with more of its own white to give away. ('L','VWY') goes
    # -108 -> -36 above; the rest are here.
    #
    # `Oleft` is a NEW left class, and it exists because OY was the worst pair
    # in the whole measurement (-0.175 em against target) and had no cell at
    # all: C G O Q were a RIGHT class only, so nothing could be said about a
    # round capital FOLLOWED by a diagonal one. Its value is POSITIVE, which is
    # rare here and correct: the two letters' closest approach is the O's belly
    # against the Y's left arm, and the arm came in with round 163.
    ('Oleft', 'VWY'): 36,
    ('R', 'VWY'): 0,
    # F P: open below the bowl / the bar, so a period or comma tucks in
    ('FP', 'period'): -126, ('FP', 'A'): -198, ('FP', 'round'): -36, ('FP', 'a'): -36, ('FP', 'colon'): -36,
    # K k, R: an open top-right corner takes a round or a diagonal a little
    ('K', 'round'): -36, ('K', 'a'): -36, ('K', 'diag'): -36, ('K', 'O'): -36,
    ('R', 'T'): -36, ('R', 'round'): -18, ('R', 'a'): -18,   # ('R','VWY') moved up to round 177's block
    # lowercase overhangs before punctuation
    ('r', 'period'): -72, ('r', 'hyphen'): -18, ('r', 'quote'): -18,
    ('f', 'period'): -36, ('f', 'hyphen'): -18,
    ('vwy', 'period'): -72, ('vwy', 'hyphen'): -18,
    ('oround', 'quote'): -18,
    # quotes and periods
    ('quote', 'A'): -126, ('quote', 'J'): -36, ('quote', 'T'): -54, ('quote', 'VWY'): -36,   # an opening quote before a T: the bar is at the quote's height, so only a little
    ('T', 'quote'): -36, ('VW', 'quote'): -18, ('Y', 'quote'): -36,
    ('quote', 'round'): -18, ('quote', 'a'): -18,
    # round 96b's a-by-neighbour cells were retired in round 97: the lowercase solve (rhythm.solve) put every common bigram within +-9 of the rhythm on bearings alone
    # round 96b: the f's hook stood 5-10 units off the ascender wedges (fl fb fh fk), connected at 13 pt
    ('f', 'ascwedge'): 54,
    ('period', 'quote'): -36,
    ('period', 'T'): -72, ('period', 'VWY'): -72,
}
# Single-glyph exceptions (written first, so the reader's first-wins overlay
# takes them over the class value; format-1 subtable before the format-2).
PAIRS = {
    # ROUND 340 -- the g's one remaining pair. With its bearings refitted
    # (build.py's tables) every neighbour tested came within a unit of what the
    # same pair gets with an o in the g's place -- except `gr`, which reads 36
    # units tight in the roman and 18 in the italic: the r's left side is cut
    # back for the round letters and the g's tail swings left under it. A pair
    # fault, so it belongs here.
    #
    # NOT in BENCH_DELTAS, which is where it was first written. That table is
    # gated on ALBO_KERN_BENCH and the variable is EMPTY in a shipped build, so
    # `_apply_bench` returns before reading it -- a kern put there does nothing
    # and the pair measures exactly as it did before. Third time today that a
    # value was written to a table the shipping path does not consult.
    ('g', 'r'): 36,
    # ROUND 202 -- the owner's second bench pass, from the phone. His W at -43
    # puts it where the U and the Y already were against the quotes.
    ('U', 'quotedbl'): 36,
    ('U', 'quotesingle'): 36,
    ('Y', 'quotedbl'): 18,
    ('Y', 'quotesingle'): 18,
    ('W', 'quotedbl'): 36,
    ('W', 'quotesingle'): 36,
    ('J', 'U'): 54,
    ('R', 'Y'): -18,
    ('V', 'a'): -126,
    ('k', 'e'): -54,
    ('o', 'c'): 36,     # round 211 halves both of these, ITALIC ONLY -- see below
    ('o', 'r'): 36,
    # ROUND 199 -- um, OPENED. The lowercase bearings are the owner's own
    # round-136 fitting, so the pair carries it rather than moving m.
    # (A `Vi` kern of -126 stood here and is WITHDRAWN: see round 200 in
    # docs/albo-spacing-method.md. It was fitted on a measure that counted the
    # V's own splay as space between the letters.)
    ('u', 'm'): 30,

    # ROUND 202 NOTE: eleven of these are GONE, not lost -- the owner's +31/+15
    # tracking opened them past the floor on its own, and leaving them would have
    # loosened those pairs twice. Removed: Op Ov RR Ri Rj Rn Rx.
    # (The four quote pairs were removed too and PUT BACK: the redundancy test
    # split "Uquotedbl" by character and measured U against a lowercase q, which
    # is not the pair. The touch gate caught it at 0.0001 em.)
    # ROUND 198b -- WHAT THE OWNER'S TIGHTENING COSTS, paid in exceptions.
    # His R at -55, U at -148 and O at -55 are rulings on those letters, and
    # each collides with a specific set of partners: R against every ascender
    # and round lowercase (19 of these 24), U and Y against the quotes, O
    # against p and v. Opening them here keeps his letters where he put them --
    # a pair exception is exactly the mechanism for "this letter, except when
    # it meets that one". Solved to 0.022 em, a step clear of the 0.012 floor.
    ('R', 'four'): 18,
    ('R', 'A'): 54,
    ('R', 'E'): 54,
    ('R', 'M'): 36,
    ('R', 'g'): 54,
    ('R', 'h'): 54,
    ('R', 'k'): 72,
    ('R', 'l'): 36,
    ('R', 'm'): 36,
    ('R', 'p'): 36,
    ('R', 'r'): 36,
    ('R', 's'): 54,
    ('R', 'z'): 72,

    # ROUND 198 -- THE OWNER'S OWN SPACING BENCH, 2026-09-17. Sixteen pairs he
    # set by hand against words, capitals, title case and sentences; the values
    # are his, snapped to the 18-unit STEP the table is quantised to.
    ('A', 'P'): -36,
    ('G', 'N'): -54,
    ('I', 'A'): -72,
    ('I', 'G'): 18,
    ('J', 'o'): 36,
    ('O', 'G'): 72,
    ('P', 'H'): -72,
    ('Q', 'U'): 36,
    ('U', 'A'): -90,
    ('U', 'R'): 36,
    ('U', 'V'): 90,
    ('V', 'I'): -108,
    ('V', 'u'): -126,
    ('X', 'I'): -72,
    ('X', 'Y'): -54,
    ('Y', 'v'): -36,
    # NOTE Rg and Rs were listed here in round 197 and are now solved above by
    # round 198b; a duplicate key is silent -- the LATER one wins -- so they are
    # removed rather than left to shadow the new values. This is the second time
    # a duplicate key has cost a build in this file.
    # ROUND 197 -- BOTH of the g's neighbours moved as the letter was re-cut,
    # and which pair fails moved with them: the leftward connector broke Rg,
    # the rightward descender broke gg, and lifting the loop onto the baseline
    # brought Rg back. Both are kerned. (gg was ALREADY in this table further
    # down at 18; a second entry here changed nothing, because the later key
    # wins in a dict literal -- it is raised at its own entry instead.)
    ('T', 'i'): -36,          # the i's dot clears the bar; a full asc value is too little, a flat too much
    ('T', 'j'): -36,
    ('f', 'quoteright'): 36,  # the arm already reaches; push the quote off it
    ('f', 'quotedblright'): 36,
    ('f', 'question'): -18,
    ('r', 'quoteright'): -36, # 'r' before an apostrophe: "Mr's"
    ('quotesingle', 'quotesingle'): 0, ('quotedbl', 'quotedbl'): 0,
    # Round 177, the two capitals the re-solved U bearing could not serve from
    # one number. U's right went -72 units to cure a letter that stood about
    # 0.13 em too far from everything after it; these two are what that left.
    ('U', 'U'): 72,    # two identical stems, so both bearings are the tight one
    ('U', 'I'): -54,   # the I carries a +33 left bearing of its own, being a bare stem
    # ROUND 178 -- THE DESCENDER-BAND COLLISIONS, and why they are PAIRS.
    #
    # `outlines/build.py` fits a glyph from the ink inside its x-height (or cap)
    # BAND -- `band = [x for ... if -OVER <= y <= top + OVER]` -- so a stroke
    # that leaves the band is invisible to the letter's own bearings. The g and
    # the J are already excepted there by name; the q, the Q, the f and the y
    # are not, and their tails and hooks are what the sweep found still
    # touching after every bearing above was re-solved.
    #
    # Fitting those letters on their FULL EXTENT instead would be the tidier
    # fix and it is the wrong one: q's tail reaches far to the right BELOW the
    # baseline, so a full-extent fit spaces `qu` -- which is very nearly every q
    # in English -- by ink that is nowhere near the u. The clash is genuinely
    # pair-dependent: it happens only when the SECOND letter also has ink down
    # there. That is what a kern pair is for.
    #
    # Values are per-pair rather than a class cell because the depths differ by
    # an order of magnitude across the family: qj was -0.110 em and Qf -0.004,
    # and one number that fixes qj opens qp to 0.127.
    ('q', 'j'): 126, ('q', 'f'): 108, ('q', 'y'): 90, ('q', 'p'): 18,
    ('j', 'f'): 36,  # round 189: the j's head now leans LEFT, so its own right
                     # side gained nothing while the f's hook still reaches back
    ('j', 'j'): 72,  # round 190: and a LEFT-leaning head runs back into the
                     # previous j's descender -- the one pair where the same
                     # letter's new left reach meets its own old right one.
                     # Measured -0.0087 em, i.e. actually touching.
    ('g', 'j'): 72,  ('g', 'f'): 54,  ('g', 'g'): 36, ('g', 'v'): 18,
    ('g', 'p'): 18,  # round 186: the g's loop grew where its neck now lands
    # Round 179: the Q's tail thickened downward (Q_TAIL_BOT) and its root was
    # trimmed (Q_TAIL_LIFT), which put more ink lower and re-tightened every
    # pair whose second letter also goes below the baseline. Re-solved, not
    # nudged: Qg had fallen to 0.002 em.
    ('Q', 'g'): 126, ('Q', 'j'): 72,  ('Q', 'p'): 72, ('Q', 'f'): 36,
    ('Q', 'parenleft'): 36, ('Q', 'y'): 36, ('Q', 'q'): 36,
    ('f', 'U'): 36,  ('f', 'V'): 18,
    ('f', 'quotedbl'): 36, ('f', 'quotesingle'): 36,
    ('Z', 'V'): 18,  ('k', 's'): 18, ('z', 's'): 18,   # R,s solved in 198b
    ('w', 'v'): 18,  ('W', 'V'): 18,
}

# ---------------------------------------------------------- round 211, italic
# THE ITALIC o's RIGHT BEARING GAINED 28 UNITS this round (owner 2026-09-18,
# *"adjust oo spacing until 'good' looks correct (it currently touches)"*; the
# measurement and the reasoning are at ALD_BEARING_ADJ in outlines/build.py).
# Both `oc` and `or` are round-202 bench values of HIS, and they have not been
# overruled -- but the letter now supplies most of the opening they were set to
# make, and the full 36 on top of it would carry both pairs far past where he
# put them: oc 0.086 -> 0.114 em and or 0.108 -> 0.136, against reference
# medians of 0.074 and 0.075. Halved, they land 0.096 and 0.118: ten units off
# his own figures, which is half a STEP and about half a pixel at 13 pt on the
# 2x app -- as close as the quantum allows.
#
# GATED, because this table is shared and the ROMAN o was not touched and does
# not need to be (its oo measures 0.073 em against a 0.071 reference median).
# An ungated halving would have moved two roman pairs nobody asked about. The
# gate reads ALD.ON rather than re-deriving it from the environment, so it
# cannot disagree with the predicate `fit` uses to choose fit_aldine.
try:
    from .glyphs import aldine as _ALD
except ImportError:
    _ALD = None
# ROUND 340 -- and the g's pair is STYLE-SPECIFIC. PAIRS is shared by both
# faces and is built above, before this module knows which one it is
# drawing; the roman needs 36 on `gr` and the italic 18, and shipping the
# roman's number to both left the italic pair 18 units LOOSER than the
# same pair with an o. Corrected here, where _ALD.ON answers.
if _ALD is not None and _ALD.ON:
    PAIRS[('g', 'r')] = 18

if _ALD is not None and _ALD.ON:
    PAIRS[('o', 'c')] = 18
    PAIRS[('o', 'r')] = 18
    # ROUND 268 -- THE BOLD ITALIC q's FOOT, eight pairs, gated to the bold.
    # The italic q ships the p's foot, a flat bar reaching a MEASURED 116
    # units right of the stem (PQ_FOOT_R, aldine.py -- "do not let the fitter
    # size this foot"). That reach does not move with weight; what moves is
    # the next letter's descending stroke, which widens with ALD_WF, and the
    # foot's own thickness. At the 400 the eight pairs clear; at the 700 they
    # were the ONLY touching pairs in the style (qf -0.0571 em, qy -0.0322,
    # qp -0.0298, qj -0.0205, q1 -0.0163, q2 -0.0135, qv -0.0063, qw -0.0034).
    # A descender clash is a kern pair, not a wider fitting band
    # (docs/albo-capital-spacing.md), and these are 3-14% of the q's advance
    # -- nothing like the roman Q's half-em, which round 225 ruled out of the
    # kern table. Each value is the measured overlap, the 0.012 em floor, and
    # a few units of clearance, ADDED to whatever the pair already carries:
    # qj, qf, qy and qp were kerned above (126, 108, 90, 18) and those
    # overlaps were measured WITH that kern in the pair. The first cut of
    # this block assigned instead of adding and made three of the four worse
    # (qj -0.0205 -> -0.1125 em: exactly the 92 units it took away). Five
    # more pairs sat UNDER the floor without touching -- qm and qr at
    # 0.0008 em, qn 0.0080, qi 0.0094 (the foot against a baseline serif)
    # and R1 at 0.0048 (the bold R's leg, the one figure pair round 216 did
    # not reach) -- and take the same treatment. Under stem 84 the block is
    # skipped and the Italic's kern table is exactly as it was.
    from . import pen as _pen
    if _pen.S > 84.0:
        for _k, _v in (('f', 72), ('y', 46), ('p', 44), ('j', 34), ('one', 30), ('two', 26), ('v', 20), ('w', 16),
                       ('m', 14), ('r', 14), ('n', 6), ('i', 5)):
            PAIRS[('q', _k)] = PAIRS.get(('q', _k), 0) + _v
        PAIRS[('R', 'one')] = PAIRS.get(('R', 'one'), 0) + 10
        # ROUND 270 -- round 269 put the y's, f's and j's strokes on the
        # weight axis (they had been the 400's widths at the 700), so their
        # tails and hook came back down against the q's foot: qy 0.0009 em,
        # qf and qj 0.0049, qp 0.0114, and the f's hook against the question
        # mark 0.0111 -- under the floor, none touching. The same rule, the
        # same block, added to what the pairs carry.
        for _k, _v in (('y', 14), ('f', 10), ('j', 10), ('p', 3)):
            PAIRS[('q', _k)] = PAIRS.get(('q', _k), 0) + _v
        PAIRS[('f', 'question')] = PAIRS.get(('f', 'question'), 0) + 3
    # ------------------------------------------------------ round 216, italic
    # THE ITALIC FIGURES ARE NOW FITTED ON THEIR BODY rather than their reach
    # (FIG_BODY in outlines/build.py), which took roughly three quarters of
    # every digit's overhang out of its bearings -- and the R's leg and the Q's
    # tail were already the tightest ink in the font, at 0.023-0.031 em against
    # letters. Three pairs went under the floor with the digits' left bearings:
    # R4 0.031 -> -0.012 and R2 0.024 -> -0.004 (both TOUCHING) and Q3
    # 0.035 -> 0.011.
    #
    # PAIRS and not a looser fit, for round 178's reason exactly: the clash is
    # pair-dependent. The R's leg reaches right BELOW the figures' own band, so
    # it only meets a digit that has ink down there -- R4 and R2 do, R8 and R0
    # do not, and widening the 4's left bearing to clear one R would open every
    # other pair the 4 is in. Only the three pairs that fail the gate are
    # kerned; O1, R1 and Q5 tightened too and all three still clear it.
    #
    # Values are STEP multiples, so they survive the phone's kern quantum.
    PAIRS[('R', 'four')] = 72
    PAIRS[('R', 'two')] = 54
    PAIRS[('Q', 'three')] = 36
    # ------------------------------------------------------ round 220, italic
    # The stops' bearings came in (ALD_STOP_BEAR, outlines/build.py) and the Q's
    # tail found the comma the way it found the 3: Q, fell to 0.008 em. Same
    # shape, same reason -- the tail runs right BELOW the comma's own band, so
    # it is a pair and not the comma's bearing, which is now measured against
    # seven faces and should not move for one capital.
    PAIRS[('Q', 'comma')] = 36
    # ------------------------------------------------------ round 222, italic
    # The quotes came DOWN 50 units and IN 20 / 120 (QUOTE_DROP in marks.py,
    # ALD_QUOTE_LSB/RSB in build.py) and the V's splayed left arm -- its own
    # white, by the spacing doc's first rule -- is the one thing at that height
    # the straight quotes now meet: 'V -0.014 em, "V -0.013, 'W 0.012. The
    # curly quotes clear (their tail hangs inward). Pairs, for round 178's
    # reason: the class is measured against seven faces and should not move
    # for one capital.
    PAIRS[('quotesingle', 'V')] = 36
    PAIRS[('quotedbl', 'V')] = 36
    PAIRS[('quotesingle', 'W')] = 18
    PAIRS[('quotedbl', 'W')] = 18   # round 233: the W's diagonals lost their 4-unit sway and "W fell to 0.0110 em, under the 0.012 floor
    # ------------------------------------------------------ round 276, italic
    # THE ITALIC'S ROUND FINIALS BECAME THE c's TOP (owner 2026-09-19: "that
    # italic has round finials that needs to replaced along with others"),
    # and two of the converted ends reach where a ball did not. The f's HOOK
    # now ends on a 65.6-unit face lying across a stroke that heads down-left,
    # so its right corner sits ~15 units further right and 15 lower than the
    # old bulb's -- at the height of the capitals' top-left serifs; and the f's
    # and j's TAILS end on the same face across a stroke heading up-left, so
    # their left corner reaches 16 units further left at the 400 (20 / 24 at
    # the 700), under the 4's foot and the q's. Measured on the built fonts,
    # baseline 0 touching / 0 under the floor at both weights; after the
    # finials, at the 400: 4j -0.0167 em, fV -0.0150, fW -0.0073, 4f -0.0038
    # (touching), fU 0.0116, qf 0.0119 (under the 0.012 floor). A descender
    # clash is a kern pair and not a wider fitting band (round 178's reason),
    # and the hook's is the same shape -- it meets only a capital with a
    # serif at that height. Each value is the measured overlap, the floor,
    # and a few units of clearance, ADDED to what the pair carries (fV 18 and
    # fU 36 above, qf 108 + the bold's 82; 4f 4j fW carried nothing).
    for _k, _v in ((('four', 'j'), 32), (('f', 'V'), 30), (('f', 'W'), 22), (('four', 'f'), 18),
                   (('f', 'U'), 4), (('q', 'f'), 4)):
        PAIRS[_k] = PAIRS.get(_k, 0) + _v
    # ...and the 700's, over those: the same faces on strokes 1.38x wider.
    # Measured with the base additions in the pair: fV 0.0041, 4f -0.0065,
    # fW 0.0053, qf 0.0003, fU 0.0118; and three pairs that clear at the 400
    # and not here -- f? -0.0117, qj -0.0080, fE 0.0048.
    if _pen.S > 84.0:
        for _k, _v in ((('f', 'question'), 27), (('q', 'j'), 23), (('four', 'f'), 21), (('q', 'f'), 15),
                       (('f', 'V'), 11), (('f', 'W'), 10), (('f', 'E'), 10), (('f', 'U'), 4)):
            PAIRS[_k] = PAIRS.get(_k, 0) + _v


# ---------------------------------------------------------- round 223, ROMAN
# The roman's figures took round 216's body fit (ROM_FIG_BODY 0.45 / TRACK 8 in
# outlines/build.py) and, as in the italic, two overhangs meet themselves
# first: the 7's bar over a 7 (77 0.009 em) and the 4's crossbar over a 4 (44
# 0.024). Pairs, for round 178's reason. Gated to the ROMAN -- the italic's 77
# reads 0.048 at ship and does not want them.
if _ALD is None or not _ALD.ON:
    # ROUND 277 -- the wedge serif is the 400's at every weight above it (owner,
    # "b wins"), and the fitter, which measures the ink in the band, drew the V
    # and the I closer once their wedges shrank: VI went from 0.0108 em under
    # the floor to -0.0026 em, touching, at the 700. The pair carries -108 at
    # the 400 (the capitals' pairing); above stem 84 it gives back 8.
    from . import pen as _penr
    if _penr.S > 84.0:
        PAIRS[('V', 'I')] = PAIRS.get(('V', 'I'), 0) + 8
    PAIRS[('seven', 'seven')] = 36
    PAIRS[('four', 'four')] = 18
    # ROUND 225 -- THE ROMAN Q KEEPS ITS LONG TAIL. Owner 2026-09-18: *"leave
    # the Q tail on roman long, it only needs to pair with other capitals and
    # 'u'."* Round 224's shortened tail (ALBO_ROM_Q_TAIL 0.50) is reverted to
    # 1.0 and the letter is judged on those pairs alone. Measured on the long
    # tail: Qu +0.079 em and every capital clears except QQ -0.042 and QJ
    # -0.452. QQ is kerned here. QJ is NOT: the J's hook runs back under the
    # tail by nearly half an em, no kern short of a word space clears it, and
    # no English word contains QJ -- it is exempted by name in cmp_touch.py
    # with the rest of the Q pairs the ruling accepts.
    PAIRS[('Q', 'Q')] = 72
    # THE Q's TAIL IS NOT A KERNING PROBLEM. Fourteen of the roman's nineteen
    # touching pairs are one letter (Q( Q) Q3 Q4 Q5 Q7 Q9 Qg Qj QJ Qp Qq QQ Qy),
    # and a kern was tried here first: the pairs measure -0.25 to -0.49 em --
    # the tail runs half an em under the next glyph -- so the smallest pairs
    # that clear the floor are +270 to +522 units, a third to a half of the
    # Q's own advance, and three still touch afterwards because the tail meets
    # a following descender at a different row (Qg -0.086, Qj -0.045, Qp
    # -0.038). A rule that wants to move that much is the wrong rule
    # (docs/albo-spacing-method.md). Removed the same round; the tail's length
    # is the drawing's, in caps_straight.py g_Q, and that is where it is fixed.


# ======================= ROUND 299 -- THE OWNER'S BENCH VALUES ==============
# Owner 2026-09-20, from the interactive bench
# (claude.ai/artifact/VCbkYNuYmZgV2m5Udd6ruy): eighteen real English words,
# each opened at ONE pair, judged at reading size, roman and italic set
# SEPARATELY -- his own ruling, *"roman and italic need different settings"*.
# The numbers are DELTAS on what the pair already carries, because that is
# what the bench rendered: its slider's zero re-applied the shipped GPOS value
# for that pair, so a number he left is a correction and not a replacement.
#
# THE QUANTUM PARAGRAPH AT THE TOP OF THIS FILE IS WRONG BY 16x, and it is
# the reason the lowercase was left unkerned. `fontconvert_sdcard.py` encodes
# `raw = round(du * (ppem/upm) * 16)` into a 4.4 signed fixed-point int8 --
# 1/16 PX resolution, not one pixel. The quantum is therefore **1.16 design
# units on the phone** (54 ppem) and **2.31 on the X3** (27 ppem), not the 18.5
# and 37 this file and CLAUDE.md both claim. Every value below survives to the
# device: the smallest, the italic's +2 on `wi`, is 2/16 px on the phone and
# 1/16 on the X3. So "a median of -24 from the lowercase pairs, below the
# quantum" was never below it -- it is 20/16 px on the phone.
#
# (Found the same way: ('T','A') and ('VW','A') at -216 are -11.66 px at 54
# ppem, outside the 4.4 range of -8.0..+7.94, so the PHONE clamps them to -8
# and the desktop does not. Recorded, not changed -- it is a separate fault.)
#
# OFF by default: `ALBO_KERN_BENCH` is "" (unset) and neither table moves, so
# a build is byte-identical to build 205's kerning. "pairs" writes exactly the
# eighteen pairs he judged; "classes" generalises each to the class cell it
# belongs to, averaging where two of his words land in one cell and rounding
# to STEP.
#
# ONE ROW OF THE BENCH WAS MISLABELLED AND THE AUDIT IS WHY IT IS HERE. The
# `away` row said `w a` and opened the word at the wrong index: what it
# actually rendered, and what he judged, is **a y** -- the round into the
# descending diagonal at the end of the word. His -4 / +17 is that pair and it
# is recorded as that pair. `w a` was never shown and carries no value; a new
# `wander` row was added to the bench for it. Every one of the nineteen rows
# was then checked by rebuilding its label from its own index, which is the
# check that found this one: one mislabel of eighteen, and it would have
# shipped a kern on a pair nobody looked at.
BENCH_DELTAS = {
    'roman': {
        ('v','e'): 17, ('a','y'): -4, ('y','e'): -5, ('r','e'): -1, ('r','o'): 12,
        ('f','t'): 4, ('s','s'): 12, ('s','y'): 6, ('s','e'): 18, ('w','i'): 2,
        ('V','i'): 13, ('W','a'): 41, ('Y','e'): 12, ('T','o'): 24, ('Q','u'): 37,
        ('A','v'): 12, ('y','comma'): -22, ('y','quoteright'): -50, ('y','quotesingle'): -50,
    },
    'italic': {
        ('v','e'): 13, ('a','y'): 17, ('y','e'): 4, ('r','e'): 3, ('r','o'): 13,
        ('f','t'): -6, ('s','s'): 3, ('s','y'): 18, ('s','e'): 5, ('w','i'): 21,
        ('V','i'): -9, ('W','a'): 12, ('Y','e'): 42, ('T','o'): 16, ('Q','u'): 11,
        ('A','v'): 16, ('y','comma'): -1,
        # ('y','quoteright') / ('y','quotesingle') were never set in the italic
        # pass -- 17 of 18. Left
        # absent rather than carried over from the roman's -50: the roman's is
        # the largest correction in the whole bench and the italic's apostrophe
        # sits over a sheared descender, which is a different meeting.
    },
}
#
# BOTH APOSTROPHES CARRY THE ROMAN'S -50. The bench renders `story's` with the
# ASCII apostrophe (U+0027 quotesingle) and the first table keyed only
# `quoteright` (U+2019), so the pair he actually judged took no value at all
# while the class arm -- whose `quote` class holds both -- moved. It is the
# same meeting either way: a descender under a raised mark.
BENCH_MODE = os.environ.get("ALBO_KERN_BENCH", "").strip().lower()

# ROUND 302 -- the bench grew to 396 rows (every common pair in his own books,
# `pair_census.py`) and he judged 189 of them. `bench_values.json` carries two
# readings of that, per style, as pair -> delta:
#
#   "literal"  only the pairs he actually moved.
#   "model"    his answers generalised to the pairs he did not reach, by the
#              structure IN the answers: marks by which mark, the roman's
#              lowercase by the LEFT letter's class (round +11 against flat
#              +2 -- a bearing signal, not 66 kerns), the italic's lowercase
#              by one number (+8, sd 7.9: it really is uniform), and the
#              roman's capitals by one (+23, all six positive).
#              The italic's CAPITALS are deliberately NOT generalised: mean
#              +2 with sd 20 and a -41..+57 range is not one number.
BENCH_FILE = os.path.join(HERE, "..", "bench_values.json")

def _apply_bench_file(which):
    with open(BENCH_FILE) as fh: table = json.load(fh)[which]
    style = 'italic' if (_ALD is not None and _ALD.ON) else 'roman'
    cmap_names = {}
    for pair, d in table[style].items():
        if not d: continue
        l, r = _gname(pair[0]), _gname(pair[1])
        if l and r: PAIRS[(l, r)] = _shipped(l, r) + d

_AGL = {'.': 'period', ',': 'comma', ':': 'colon', ';': 'semicolon',
        "'": 'quotesingle', '"': 'quotedbl', '-': 'hyphen', '!': 'exclam', '?': 'question'}
def _gname(ch):
    return ch if ch.isalpha() else _AGL.get(ch)

def _class_cell(l, r):
    """The (left class, right class) cell a glyph pair falls in, or None."""
    lc = next((k for k, gs in LEFT.items() if l in gs), None)
    rc = next((k for k, gs in RIGHT.items() if r in gs), None)
    return (lc, rc) if lc and rc else None

def _shipped(l, r):
    if (l, r) in PAIRS: return PAIRS[(l, r)]
    cell = _class_cell(l, r)
    return CLASS_PAIRS.get(cell, 0) if cell else 0

def _apply_bench():
    if BENCH_MODE in ('literal', 'model'):
        _apply_bench_file(BENCH_MODE); return
    if BENCH_MODE not in ('pairs', 'classes'): return
    style = 'italic' if (_ALD is not None and _ALD.ON) else 'roman'
    deltas = BENCH_DELTAS[style]
    if BENCH_MODE == 'pairs':
        for (l, r), d in deltas.items():
            PAIRS[(l, r)] = _shipped(l, r) + d
        return
    by_cell = {}
    for (l, r), d in deltas.items():
        cell = _class_cell(l, r)
        if cell is None:                      # no class covers it: keep the pair
            PAIRS[(l, r)] = _shipped(l, r) + d
            continue
        by_cell.setdefault(cell, []).append(d)
    for cell, ds in by_cell.items():
        mean = sum(ds) / len(ds)
        step = int(round(mean / STEP)) * STEP          # cells must be multiples of STEP
        if step: CLASS_PAIRS[cell] = CLASS_PAIRS.get(cell, 0) + step

# ROUND 308: each value is his judgment MINUS what the following letter's new
# left bearing now contributes, for the same reason the marks are re-solved --
# the letter table moves these pairs too, and a capital corrected against the
# old letters lands wrong once the letters move.
# ROUND 303 -- THE PAIRS HIS BENCH LEAVES BEHIND, once the bearings have taken
# what they can (build.py's marks and round lowercase, aldine's capitals). The
# roman's six capital judgments are one reading each, so none of them can be a
# letter's bearing; the italic's G Q R V are singles too, and its T's two pairs
# disagree by 25 units (Th -9, To +16), which is what a kern table is for.
# Values are his, ADDED to what the pair already carried.
_BENCH_PAIRS_ROM = ((('A','v'), 12), (('Q','u'), 29), (('T','o'), 17), (('V','i'), 13), (('W','a'), 23), (('Y','e'), 5))
# ROUND 304: raw again -- round 303's minus-4 was compensation for the italic
# lowercase tracking, which the fuller data withdrew.
_BENCH_PAIRS_ITA = ((('A','n'), 2), (('A','v'), 16), (('C','a'), -1), (('C','h'), 2), (('C','o'), 3),
                    (('F','i'), -36), (('F','o'), -47), (('G','r'), -2), (('P','a'), -27), (('P','o'), -32),
                    (('P','r'), -19), (('Q','u'), 16), (('R','e'), 8), (('S','a'), -9), (('S','e'), -7),
                    (('S','h'), 7), (('S','o'), -8), (('S','p'), 10), (('S','t'), 4), (('T','h'), -13),
                    (('T','o'), 9), (('V','i'), -4), (('W','a'), 12), (('W','h'), 7), (('W','i'), 20),
                    (('Y','e'), 42), (('Y','o'), 50))
for _p, _d in (_BENCH_PAIRS_ITA if (_ALD is not None and _ALD.ON) else _BENCH_PAIRS_ROM):
    PAIRS[_p] = _shipped(*_p) + _d

# ROUND 373 -- HOLD THE OWNER'S XI AND XY WHERE HE SET THEM, ROMAN ONLY. The
# roman X's right bearing came in 18 units (build.ROM_CAP_ADJ, "adjust spacing
# around x"), and his round-198 bench kerns XI -72 / XY -54 were set against
# the old bearing: left alone they would have closed XI 0.033 -> 0.018 em and
# XY 0.029 -> 0.011, under the 0.012 floor. +18 returns both to exactly the
# gap he chose (measured 0.033 and 0.029 after). The italic X's bearing did not
# move, so the italic keeps -72 / -54 untouched -- this table is shared by every
# style, which is why the adjustment is gated here rather than written into it.
if not (_ALD is not None and _ALD.ON):
    for _p in (('X', 'I'), ('X', 'Y')):
        PAIRS[_p] = PAIRS[_p] + 18

# ROUND 348 -- THE ROMAN Q'S TAIL, KERNED RATHER THAN SHORTENED.
# Owner 2026-09-21, choosing between a shorter tail and kern pairs: *"kern
# Q"*. So the letter is untouched and these thirteen pairs carry the white
# instead.
#
# WHAT WAS ACTUALLY WRONG. The Q's ink runs to x=1312 on a 777-unit advance --
# the tail overhangs 535 units past its own body and dips to y=-272 -- so any
# following DESCENDER crosses it. Not a fitting error: `Quiet`, `QU` and `Qu`
# all read correctly, because u, i, e and t have nothing below the baseline.
# Round 225 exempted the thirteen collisions on the ground that the roman Q
# "pairs only with capitals and u", which is true of English and was never a
# repair.
#
# EACH VALUE IS MEASURED, NOT CHOSEN: the smallest kern, swept over
# -400..+900 in steps of 20 and ordered by absolute size, at which the two
# glyphs' INK is 0.012 em apart -- `cmp_touch.py`'s own floor, but taken as a
# 2-D distance between rasterised outlines rather than row by row.
#
# THE GATE'S OWN MEASURE CANNOT SETTLE THIS, and that is worth knowing before
# anyone re-tunes these. `cmp_touch` compares, per raster ROW, the left edge
# of the second glyph with the right edge of the first; the Q's tail reaches
# x=1312 on rows the following glyph also occupies, so the row-wise number
# stays at -0.25 to -0.49 em however far the pair is kerned, short of pushing
# it clean past the tail's end. Measured 2-D, ten of the thirteen pairs really
# do INTERSECT at kern 0 (Q7 does not, and clears by 0.0125 em, which is why
# it takes no kern here); Q5 and Q3 pass within 0.007 em. So the gate was
# right that these are faults and wrong about their size, and the pairs stay
# EXEMPT there with a corrected reason rather than being declared fixed by a
# measure that cannot see the fix.
#
# THE COST IS NOT UNIFORM AND THE OWNER SHOULD SEE IT. Four are ordinary
# kerns; the other nine buy clearance at a third to a half of an em, which is
# a visible hole. They are shipped because every one of those nine is a
# sequence that does not occur in English -- which is round 225's own
# argument, now used to license the repair instead of to excuse the defect.
# Pulling any of them back is one number here.
_Q_KERNS = {
    '4': -60, '9': 60, 'q': 140,          # the cheap three; Q7 needs none
    'y': 360, '(': 440, ')': 440,         # and the expensive nine
    'p': 460, 'g': 480, 'j': 500, 'J': 500, '5': 500, '3': 520,
}
for _ch, _k in _Q_KERNS.items():
    _g = _gname(_ch) or {'4': 'four', '7': 'seven', '9': 'nine', '5': 'five',
                         '3': 'three', '(': 'parenleft', ')': 'parenright'}.get(_ch)
    if _g and not (_ALD is not None and _ALD.ON):
        PAIRS[('Q', _g)] = _k

# ROUND 369 -- THE RAISED ? AGAINST AN OPEN CAPITAL. Taking the ? up to the
# ascender scales its hook uniformly about its own lowest point, so the
# upper-left arm -- the part that overhangs backwards -- travelled 25 units
# LEFT. In the italic, where the slant already carries that arm over whatever
# precedes it, `U?` closed to 0.0093 em against the sweep's 0.012 floor.
#
# A KERN AND NOT A WIDER FITTING BAND, which is this face's standing rule for
# a clash that only some neighbours can have (docs/albo-capital-spacing.md):
# widening the ?'s left bearing would loosen it after every one of the 26
# lowercase letters to fix five capitals with open right sides. Swept: U? is
# the only pair under the floor; V? W? Y? T? all sit at 0.03 em or better.
_QUESTION_KERNS = {'U': 30}
for _ch, _k in _QUESTION_KERNS.items():
    _g = _gname(_ch)
    if _g: PAIRS[(_g, 'question')] = _k

# ROUND 357 -- THE BOLD ITALIC'S `q` PAIRS, and why they are weight-gated.
#
# The bench's bearings are fitted on the 400 and applied at every weight, so a
# bearing that is right there can be wrong at stem 116 where the same absolute
# units eat a smaller gap. Found by gating the FOUR CUTS before a deploy rather
# than the two: the BoldItalic went from 0 pairs under `cmp_touch`'s floor to
# three -- `qg` 0.0023, `qi` 0.0101, `qu` 0.0109 em -- while the Regular
# IMPROVED (2 touching -> 1) and the Italic stayed clean.
#
# Measured 2-D as well as row-wise, and the two disagree on `qi` (0.0050
# against 0.0101), so each value is the larger of the two requirements: the
# smallest kern at which BOTH measures clear 0.013 em.
#
# Gated on the weight because the 400 italic does not need them and a kern
# applied there would loosen three pairs that currently read correctly.
if (_ALD is not None and _ALD.ON):
    from . import pen as _pen_q
    if _pen_q.S > 84.0:
        for _r, _k in (('g', 12), ('i', 12), ('u', 4)):
            PAIRS[('q', _r)] = _shipped('q', _r) + _k

_apply_bench()


def feature_text():
    lines = ['languagesystem DFLT dflt;', 'languagesystem latn dflt;']
    for k, gs in LEFT.items(): lines.append(f"@L_{k} = [{' '.join(gs)}];")
    for k, gs in RIGHT.items(): lines.append(f"@R_{k} = [{' '.join(gs)}];")
    lines.append('feature kern {')
    for (l, r), v in PAIRS.items(): lines.append(f'    pos {l} {r} {v};')
    for (l, r), v in CLASS_PAIRS.items():
        assert v % STEP == 0, (l, r, v)
        lines.append(f'    pos @L_{l} @R_{r} {v};')
    lines.append('} kern;')
    # round 96: the five standard ligatures; feaLib orders the longer sequences first
    # ROUND 309 -- THE ITALIC HAS NO LIGATURES, and the roman has five more.
    # Owner 2026-09-21: *"remove italic ligatures. take pass at adding other
    # ligatures to roman"*. The italic's FB00-FB04 GLYPHS stay drawn and
    # encoded -- a text that literally contains U+FB01 still sets in Albo
    # rather than falling back to Noto mid-word -- but nothing SUBSTITUTES
    # into them any more, so `fi` in an italic word is an f and an i.
    if _ALD is not None and _ALD.ON:
        lines.append('feature liga {\n    sub f i by uniFB01;\n} liga;'.replace(
            '    sub f i by uniFB01;\n', ''))          # an empty feature: no rule at all
    else:
        lines.append('feature liga {\n'
                     '    sub f f i by uniFB03;\n'
                     '    sub f f l by uniFB04;\n'
                     '    sub f f by uniFB00;\n'
                     '    sub f i by uniFB01;\n'
                     '    sub f l by uniFB02;\n'
                     # ROUND 309b -- fb fh fj fk are DRAWN and NOT substituted:
                     # counted over his own books they appear 13 times in two
                     # million pairs (six of them in `Kafka`), where `st` alone
                     # appears 23,470 times. The glyphs stay at E000-E003 so
                     # the work is not lost; the feature carries what the
                     # corpus justifies.
                     # ...and st/ct are DRAWN but not substituted either, for
                     # the opposite reason to the f-family: the corpus wants
                     # them badly (st is the commonest pair in his books) and
                     # the DRAWING is not right yet. Their arc reads as a spur
                     # off the s rather than a span to the t at every height
                     # and weight tried in round 309. Reaching them is
                     # U+FB06 / U+E004; switching them on is one line here,
                     # once the join is drawn properly.
                     # ROUND 310 -- THE Th IS WITHDRAWN. Owner 2026-09-21,
                     # having seen it set: *"Th ligature is worse"*. It went in
                     # on the corpus count (8,589) and it comes straight back
                     # out on his eye, which outranks the count: the tuck buys
                     # a tighter pair and costs the T its own air, and `The` at
                     # the head of a sentence is the most-looked-at word in a
                     # book. The glyph stays drawn at U+E005 and NOTHING
                     # substitutes into it. Do not re-propose it; a gentler
                     # TH_TUCK is a different proposal and needs its own ask.

                     '} liga;')
    return '\n'.join(lines) + '\n'

def apply(path, out=None):
    """Write the kern feature into the TTF at `path` (a fresh GPOS; any
    previous one is replaced). Returns the output path."""
    font = TTFont(path)
    for t in ('GPOS', 'GDEF', 'GSUB'):
        if t in font: del font[t]
    names = set(font.getGlyphOrder())
    for cls in list(LEFT.values()) + list(RIGHT.values()):
        missing = [g for g in cls if g not in names]
        assert not missing, f"kern classes name glyphs the font lacks: {missing}"
    if 'uniFB01' not in names:   # a file built before round 96: kern only
        addOpenTypeFeaturesFromString(font, feature_text().split('feature liga')[0]); out = out or path; font.save(out); return out
    addOpenTypeFeaturesFromString(font, feature_text())
    out = out or path; font.save(out); return out

def reader_view(path, ppem=54):
    """What the reader would get: the firmware's own extractor at `ppem`,
    returned as {(leftCp, rightCp): 4.4 px}. Needs the firmware checkout."""
    fw = os.path.expanduser(os.environ.get('CROSSPOINT_FIRMWARE_DIR', '~/src/crosspoint-reader'))
    sys.path.insert(0, os.path.join(fw, 'lib', 'EpdFont', 'scripts'))
    import fontconvert_sdcard as fc
    cps = sorted(TTFont(path).getBestCmap().keys())
    return fc.extract_kerning_fonttools(path, cps, ppem)

if __name__ == '__main__':
    src = sys.argv[1]; dst = sys.argv[2] if len(sys.argv) > 2 else None
    out = apply(src, dst); print('kern written', out)
    try:
        rv = reader_view(out); print(f'reader at 54 px: {len(rv)} pairs; T+o {rv.get((ord("T"), ord("o")))} /16 px, A+V {rv.get((ord("A"), ord("V")))}, P+. {rv.get((ord("P"), ord(".")))}')
    except Exception as e:
        print('reader view unavailable:', e)
