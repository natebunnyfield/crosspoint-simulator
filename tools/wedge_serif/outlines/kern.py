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
# judged in round 95 moved one step deeper to keep the same tuck.
CLASS_PAIRS = {
    # T: the bar overhangs; every lowercase tucks under it, rounds most
    ('T', 'round'): -126, ('T', 'a'): -126, ('T', 'flat'): -90, ('T', 'diag'): -90, ('T', 'asc'): -18, ('T', 'ascwedge'): -18,
    ('T', 'A'): -90, ('T', 'O'): -36, ('T', 'J'): -72,
    ('T', 'period'): -144, ('T', 'hyphen'): -108, ('T', 'colon'): -72,
    # V W: a diagonal right side; the rounds and the a tuck, the flats less
    ('VW', 'round'): -90, ('VW', 'a'): -90, ('VW', 'flat'): -54, ('VW', 'diag'): -36, ('VW', 'asc'): -18, ('VW', 'ascwedge'): -18,
    ('VW', 'A'): -90, ('VW', 'O'): -36, ('VW', 'J'): -54,
    ('VW', 'period'): -144, ('VW', 'hyphen'): -72, ('VW', 'colon'): -54,
    # Y: the deepest overhang after the T
    ('Y', 'round'): -108, ('Y', 'a'): -108, ('Y', 'flat'): -72, ('Y', 'diag'): -54, ('Y', 'asc'): -18, ('Y', 'ascwedge'): -18,
    ('Y', 'A'): -108, ('Y', 'O'): -54, ('Y', 'J'): -72,
    ('Y', 'period'): -144, ('Y', 'hyphen'): -90, ('Y', 'colon'): -72,
    # A: its right side slopes away at the top, so the tall overhangs fall into it
    ('A', 'T'): -90, ('A', 'VWY'): -90, ('A', 'O'): -18, ('A', 'quote'): -126,
    ('A', 'diag'): -36,
    # L: open above its arm
    ('L', 'T'): -108, ('L', 'VWY'): -108, ('L', 'quote'): -144, ('L', 'O'): -18,
    ('L', 'diag'): -36, ('L', 'hyphen'): -54,
    # F P: open below the bowl / the bar, so a period or comma tucks in
    ('FP', 'period'): -144, ('FP', 'A'): -72, ('FP', 'round'): -36, ('FP', 'a'): -36, ('FP', 'colon'): -36,
    # K k, R: an open top-right corner takes a round or a diagonal a little
    ('K', 'round'): -36, ('K', 'a'): -36, ('K', 'diag'): -36, ('K', 'O'): -36,
    ('R', 'T'): -36, ('R', 'VWY'): -54, ('R', 'round'): -18, ('R', 'a'): -18,
    # lowercase overhangs before punctuation
    ('r', 'period'): -90, ('r', 'hyphen'): -18, ('r', 'quote'): -18,
    ('f', 'period'): -54, ('f', 'hyphen'): -18,
    ('vwy', 'period'): -90, ('vwy', 'hyphen'): -18,
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
    ('T', 'i'): -36,          # the i's dot clears the bar; a full asc value is too little, a flat too much
    ('T', 'j'): -36,
    ('f', 'quoteright'): 36,  # the arm already reaches; push the quote off it
    ('f', 'quotedblright'): 36,
    ('f', 'question'): -18,
    ('r', 'quoteright'): -36, # 'r' before an apostrophe: "Mr's"
    ('quotesingle', 'quotesingle'): 0, ('quotedbl', 'quotedbl'): 0,
}

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
    lines.append('feature liga {\n    sub f f i by uniFB03;\n    sub f f l by uniFB04;\n    sub f f by uniFB00;\n    sub f i by uniFB01;\n    sub f l by uniFB02;\n} liga;')
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
