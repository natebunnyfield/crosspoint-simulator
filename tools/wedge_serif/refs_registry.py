"""The reference italics, and the ONE fact about them every instrument gets wrong.

Owner 2026-09-16: *"add coelacanth italic as reference font"*.

**A FONT'S DECLARED ITALIC ANGLE IS NOT ITS SLANT, and one of these declares
nothing at all.** Every measuring script here unshears a reference by
`post.italicAngle` before comparing it with Albo, because Albo's glyph code is
unsheared design space and the build applies FJORD_SLANT=13 at the end. Measured
off each face's own `l`, against what its `post` table claims:

    Coelacanth Italic    declared  -0.0     measured 14.5     <-- declares NOTHING
    Cancelleresca        declared  -0.0     measured 10.3     <-- declares NOTHING
    Flanker Griffo It    declared  12.0     measured 11.7
    Pagella Italic       declared  10.0     measured 11.7
    Poetica Std          declared  11.0     measured  9.2

TWO of the five declare zero. Coelacanth is the trap: it is plainly an italic
and its `post.italicAngle` is zero, so an instrument that trusts the field measures it **sheared by 14.5
degrees** and every width, counter and axis that comes out is wrong -- silently,
with no error and a plausible-looking number. Pagella is off by 1.7 the other
way and Poetica by 1.8, which is small enough to pass unnoticed and large enough
to move a stress axis.

So `slant()` returns the MEASURED value, and `check()` is the gate: it re-measures
every reference and fails if one has drifted from the table, which is what
happens when a font file is replaced by a different cut under the same name.

    PYTHON_GIL=0 python3 refs_registry.py          # print the table, verify it
"""
import math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REFS = os.path.join(HERE, "refs")

# name -> (filename, TRUE slant in degrees, what it is good for)
REFERENCES = {
    "Flanker Griffo": ("flanker-griffo-italic.otf", 11.7,
                       "the primary reference: Griffo's own letter, digitised"),
    "Coelacanth":     ("coelacanth-italic.otf", 14.5,
                       "Centaur/Bruce Rogers lineage; the face Albo's IT_SERIF 0.50 "
                       "and the g's brush-stroke analysis were measured off "
                       "(docs/italic-g-strokes.md). x-height 425/1000, the closest "
                       "of any reference to Albo's own 429"),
    "Pagella":        ("texgyrepagella-italic.otf", 11.7,
                       "proportion fallback where no scan crop exists"),
    "Poetica":        ("poetica-std-regular.otf", 9.2,
                       "the owner's preferred shape fallback, 2026-09-16"),
    "Cancelleresca":  ("cancelleresca-bastarda-beta12.otf", 10.3,
                       "a chancery hand, 28 glyphs, lowercase only. Its post table "
                       "also says 0 and it plainly slants -- this was called "
                       "'upright' in an earlier measurement on the strength of "
                       "that field, and it is not"),
}


def path(name):
    return os.path.join(REFS, REFERENCES[name][0])


def slant(name):
    """The MEASURED slant, never `post.italicAngle`. See the module docstring."""
    return REFERENCES[name][1]


def measure_slant(ttf, chars="l", px=900):
    """Re-measure a face's slant as the MEDIAN over bare-stem letters.

    ONLY BARE-STEM LETTERS ARE VALID, and getting that wrong is not subtle. The
    axis is read between the stem's centre at 30% and 70% of the glyph's own
    height, so on a letter whose middle is a BOWL the reading is the bowl's
    widest point against the stem and it is nonsense. Measured on Cancelleresca
    Bastarda, one face, one instrument, per glyph:

        l  10.3                              <-- ONE bare stem: valid
        n  10.6    m  10.7                    <-- agree here BY LUCK, see below
        b  -8.9    h  -7.7    d  26.4         <-- the band crosses a bowl
        k  -0.5                               <-- the band crosses the leg

    Only a SINGLE bare stem is valid, and n and m are not it even though they
    looked right on this face. A row's midpoint is `(min + max) / 2` across the
    whole row, so on an n it spans BOTH stems and the arch between them -- it
    reports the letter's centre rather than a stem's, and whether that tracks
    the slant depends on how the arch is drawn. Adding n and m to the median
    flipped Coelacanth from +14.5 to -14.0 and Poetica from +9.2 to -10.7,
    which is how this was caught: a sign reversal is too big to be a slant
    measurement and too plausible to ignore.

    So: `l` alone, and any face without one has to state its slant by hand.
    """
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
    from fontTools.ttLib import TTFont
    f = TTFont(ttf); upm = f["head"].unitsPerEm
    try: sx = f["OS/2"].sxHeight or upm * 0.5
    except Exception: sx = upm * 0.5
    size = int(round(px * upm / sx)); W = H = size * 3
    out = []
    for ch in chars:
        im = Image.new("L", (W, H), 255)
        ImageDraw.Draw(im).text((W * .35, H * .62), ch,
                                font=ImageFont.truetype(ttf, size), fill=0, anchor="ls")
        a = np.asarray(im) < 128
        if not a.any(): continue
        ys = np.nonzero(a.any(1))[0]; y0, y1 = ys.min(), ys.max(); span = y1 - y0
        cs = []
        for fr in (0.30, 0.70):
            y = int(y0 + span * fr); r = np.nonzero(a[y])[0]
            if not len(r): break
            cs.append(((r.min() + r.max()) / 2.0, y))
        if len(cs) < 2: continue
        out.append(math.degrees(math.atan2(cs[0][0] - cs[1][0], cs[1][1] - cs[0][1])))
    if not out: return float("nan")
    out.sort(); return out[len(out) // 2]


def check(tol=1.0):
    """Gate: every reference still slants what the table says. Non-zero on drift."""
    bad = 0
    print(f"\n  {'reference':16}{'table':>8}{'measured':>10}")
    for n in REFERENCES:
        p = path(n)
        if not os.path.exists(p):
            print(f"  {n:16}{'':>8}{'MISSING':>10}   {p}"); bad += 1; continue
        m = measure_slant(p)
        off = abs(m - slant(n))
        print(f"  {n:16}{slant(n):8.1f}{m:10.1f}" + ("   <-- DRIFTED" if off > tol else ""))
        if off > tol: bad += 1
    print(f"\n  {bad} reference(s) missing or drifted.\n")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(check())
