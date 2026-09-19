"""The reference faces, grouped by POSTURE AND WEIGHT -- one registry, four sets.

WHY THIS FILE EXISTS. Every gap instrument here (`cmp_space_2d.py`,
`cmp_figure_space.py`, `cmp_cap_space.py`) carried its own list of seven
references and all seven were ITALICS. That was right while Albo was a roman
plus an Aldine italic being fitted against Aldine italics, and
`docs/albo-misfit-audit-2026-09-18.md` (§d, *"What could NOT be measured"*)
names the consequence: the roman's class medians were being judged against the
wrong posture, which OVERSTATES how loose the roman is, since a roman is
normally fitted a little wider than its italic. With a Bold and a Bold Italic
in the family the same hole opens twice more.

So the sets are:

    roman        8 upright text romans at 400
    italic       the SAME seven this project has always used, in the same
                 order -- so every number in docs/albo-spacing-method.md
                 stays comparable. Do not re-order or add to this one
                 without saying so in that doc
    bold         the 700 of the roman families
    bolditalic   the 700 italics, plus Flanker Griffo Bold Italic

TWO THINGS TO KNOW BEFORE USING A BAND.

1. **Albo's "Bold" is not the references' Bold.** Measured by this file's own
   `report()` (stem thickness over x-height, from the rendered `n`): Albo's
   Bold is 0.249 against its Medium's 0.191, a ratio of **1.30**, where the
   eight reference families run **1.37 - 1.71** (median 1.45). By stem-over-xh
   Albo's Bold sits with the SemiBolds, so `bold` carries Baskerville SemiBold
   and its italic beside the 700s ON PURPOSE, and a "tight" verdict against
   this band on a 1.30 weight is expected rather than a fault.

2. **A gap in EM is not a gap at one apparent size.** These faces' x-heights
   run 0.395 - 0.481 em, so two faces set at the same em are not set at the
   same reading size. Every number in this project is in em, and it stays that
   way for continuity; `--unit xh` on `cmp_space_2d.py` divides by the measured
   x-height instead, which is the perceptually honest unit, and the two agree
   on every verdict in the 2026-09-19 pass (recorded in
   docs/albo-spacing-method.md). Within ONE family regular-to-bold the choice
   cannot matter -- Times 0.4473 -> 0.4565, Georgia 0.4814 -> 0.4844 -- which
   is why the weight rule in that round is derived from within-family deltas.

AND ONE INSTRUMENT BUG THIS FILE CARRIES THE FIX FOR. The x-height used to be
read from `OS/2.sxHeight`, which is **absent in Charter and Iowan Old Style,
zero in New York, and wrong by 34% in Poetica** (declared 0.600 em, its
rendered `x` is 0.395). It only sized the raster -- the reported numbers are
per-em and were never biased by it -- but a Poetica rendered 52% larger than
asked for was quantising its gaps on a different grid from everything it was
being compared with, and `--unit xh` cannot exist on a declared value at all.
`measure_xh()` renders an `x` and measures it; validated against the eleven
faces whose sxHeight is present and right, where it agrees to under 1% on
seven and 2.9% on the rest (the difference is the x's own overshoot).

    PYTHON_GIL=0 python3 refsets.py            # the whole basis, all four sets
    PYTHON_GIL=0 python3 refsets.py --set bold
"""
import os

SYS = "/System/Library/Fonts"
SUP = SYS + "/Supplemental"
HERE = os.path.dirname(os.path.abspath(__file__))
_R = lambda n: os.path.join(HERE, "refs", n)

# (label, path, face index within a .ttc)
SETS = {
    "italic": [                        # UNCHANGED, and in the original order
        ("Flanker Griffo it", _R("flanker-griffo-italic.otf"), 0),
        ("Pagella it",        _R("texgyrepagella-italic.otf"), 0),
        ("Poetica",           _R("poetica-std-regular.otf"), 0),
        ("Coelacanth it",     _R("coelacanth-italic.otf"), 0),
        ("Times it",          SUP + "/Times New Roman Italic.ttf", 0),
        ("Georgia it",        SUP + "/Georgia Italic.ttf", 0),
        ("New York it",       SYS + "/NewYorkItalic.ttf", 0),
    ],
    "roman": [
        ("Times",             SUP + "/Times New Roman.ttf", 0),
        ("Georgia",           SUP + "/Georgia.ttf", 0),
        ("New York",          SYS + "/NewYork.ttf", 0),
        ("Palatino",          SYS + "/Palatino.ttc", 0),
        ("Baskerville",       SUP + "/Baskerville.ttc", 0),
        ("Charter",           SUP + "/Charter.ttc", 0),
        ("Iowan Old Style",   SUP + "/Iowan Old Style.ttc", 0),
        ("Hoefler Text",      SUP + "/Hoefler Text.ttc", 0),
    ],
    "bold": [
        ("Times B",           SUP + "/Times New Roman Bold.ttf", 0),
        ("Georgia B",         SUP + "/Georgia Bold.ttf", 0),
        ("Palatino B",        SYS + "/Palatino.ttc", 2),
        ("Baskerville B",     SUP + "/Baskerville.ttc", 1),
        ("Baskerville SB",    SUP + "/Baskerville.ttc", 4),   # 600: Albo's Bold is a 1.30 weight ratio
        ("Charter B",         SUP + "/Charter.ttc", 3),
        ("Iowan B",           SUP + "/Iowan Old Style.ttc", 1),
        ("Hoefler Black",     SUP + "/Hoefler Text.ttc", 1),
    ],
    "bolditalic": [
        ("Flanker Griffo BI", _R("flanker-griffo-bold-italic.otf"), 0),
        ("Times BI",          SUP + "/Times New Roman Bold Italic.ttf", 0),
        ("Georgia BI",        SUP + "/Georgia Bold Italic.ttf", 0),
        ("Palatino BI",       SYS + "/Palatino.ttc", 3),
        ("Baskerville BI",    SUP + "/Baskerville.ttc", 3),
        ("Baskerville SBI",   SUP + "/Baskerville.ttc", 5),
        ("Charter BI",        SUP + "/Charter.ttc", 2),
        ("Iowan BI",          SUP + "/Iowan Old Style.ttc", 3),
        ("Hoefler Black It",  SUP + "/Hoefler Text.ttc", 3),
    ],
}
# regular -> bold, within one family: the only comparison a weight rule may be
# derived from, because posture and design are held fixed across it.
FAMILY_PAIRS = [
    ("Times",        ("Times", 0), ("Times B", 0)),
    ("Georgia",      ("Georgia", 0), ("Georgia B", 0)),
    ("Palatino",     ("Palatino", 0), ("Palatino B", 0)),
    ("Baskerville",  ("Baskerville", 0), ("Baskerville B", 0)),
    ("Baskerville/SB", ("Baskerville", 0), ("Baskerville SB", 0)),
    ("Charter",      ("Charter", 0), ("Charter B", 0)),
    ("Iowan",        ("Iowan Old Style", 0), ("Iowan B", 0)),
    ("Hoefler",      ("Hoefler Text", 0), ("Hoefler Black", 0)),
    ("Times it",     ("Times it", 0), ("Times BI", 0)),
    ("Georgia it",   ("Georgia it", 0), ("Georgia BI", 0)),
    ("Flanker it",   ("Flanker Griffo it", 0), ("Flanker Griffo BI", 0)),
]


def pick(path):
    """Which set a built Albo belongs to, from its file name. `Albo-BoldItalic`
    must be tested before `Albo-Italic` and before `Albo-Bold`."""
    n = os.path.basename(path)
    if "BoldItalic" in n: return "bolditalic"
    if "Italic" in n:     return "italic"
    if "Bold" in n:       return "bold"
    return "roman"


def entries(name):
    """The set's (label, path, index) rows that actually exist on this machine."""
    return [(l, p, i) for l, p, i in SETS[name] if os.path.exists(p)]


def lookup(label):
    for rows in SETS.values():
        for l, p, i in rows:
            if l == label: return (l, p, i)
    raise KeyError(label)


# ------------------------------------------------------------------ measuring
def measure_xh(path, index=0, px=400):
    """The x-height as RENDERED, in em -- see the header. The `x` is chosen
    because it is flat-topped in every face here, so its ink height is the
    x-height plus at most a hairline of rounding."""
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
    fnt = ImageFont.truetype(path, px, index=index)
    im = Image.new("L", (px * 3, px * 3), 255)
    ImageDraw.Draw(im).text((px, px * 2), "x", font=fnt, fill=0, anchor="ls")
    a = np.asarray(im) < 128
    rows = np.nonzero(a.any(1))[0]
    return (px * 2 - int(rows.min())) / float(px)


def _n_parts(fnt, px):
    """(stem thickness, counter width) in px, read off the `n`'s own middle row
    -- below the arch and above the feet, so neither is in the runs."""
    import numpy as np
    from PIL import Image, ImageDraw
    im = Image.new("L", (px * 4, px * 3), 255)
    ImageDraw.Draw(im).text((px, px * 2), "n", font=fnt, fill=0, anchor="ls")
    a = np.asarray(im) < 128
    rows = np.nonzero(a.any(1))[0]
    y = int(rows.min() + (rows.max() - rows.min()) * 0.55)
    xs = np.nonzero(a[y])[0]
    if not len(xs): return None, None
    runs, start = [], xs[0]
    for i in range(1, len(xs)):
        if xs[i] != xs[i - 1] + 1:
            runs.append((start, xs[i - 1])); start = xs[i]
    runs.append((start, xs[-1]))
    if len(runs) < 2: return None, None
    return min(b - a0 + 1 for a0, b in runs), runs[1][0] - runs[0][1] - 1


def basis(path, index=0, px=400):
    """One face's spacing basis, everything over its MEASURED x-height so faces
    compare at a reading size rather than at an em: the `n`'s stem (weight), the
    `n`'s counter (the space WITHIN, which is what the space BETWEEN is judged
    against, round 3's ruling), and the word space."""
    from PIL import ImageFont
    xh = measure_xh(path, index, px)
    fnt = ImageFont.truetype(path, px, index=index)
    stem, ctr = _n_parts(fnt, px)
    sp = fnt.getlength(" ")
    xpx = xh * px
    return dict(xh=xh, stem=(stem / xpx if stem else None), ctr=(ctr / xpx if ctr else None),
                space=sp / xpx, spctr=(sp / ctr if ctr else None), stem_px=stem, ctr_px=ctr)


def report(sets=None, px=400):
    out = {}
    for name in (sets or list(SETS)):
        print("\n  %s" % name.upper())
        print("    %-19s%8s%8s%8s%8s%8s" % ("face", "xh/em", "stem", "ctr", "space", "sp/ctr"))
        for label, path, idx in entries(name):
            row = basis(path, idx, px)
            out[label] = row
            print("    %-19s%8.4f%8.3f%8.3f%8.3f%8.2f" % (
                label, row["xh"], row["stem"] or 0, row["ctr"] or 0, row["space"], row["spctr"] or 0))
    return out


if __name__ == "__main__":
    import sys
    sel = None
    if "--set" in sys.argv: sel = [sys.argv[sys.argv.index("--set") + 1]]
    r = report(sel)
    if "--albo" in sys.argv:            # the four built styles, same instrument
        d = sys.argv[sys.argv.index("--albo") + 1]
        print("\n  ALBO")
        print("    %-19s%8s%8s%8s%8s%8s" % ("face", "xh/em", "stem", "ctr", "space", "sp/ctr"))
        for st in ("Medium", "Italic", "Bold", "BoldItalic"):
            p = os.path.join(d, "Albo-%s.ttf" % st)
            if not os.path.exists(p): continue
            b = basis(p)
            print("    %-19s%8.4f%8.3f%8.3f%8.3f%8.2f" % (
                "Albo " + st, b["xh"], b["stem"] or 0, b["ctr"] or 0, b["space"], b["spctr"] or 0))
    print("\n  REGULAR -> BOLD, within one family (stem, counter and word space over x-height)")
    print("    %-16s%9s%9s%9s%9s" % ("family", "stem x", "ctr x", "space x", "sp/ctr"))
    for fam, (la, _), (lb, _) in FAMILY_PAIRS:
        if la not in r or lb not in r: continue
        a, b = r[la], r[lb]
        if not (a["stem"] and b["stem"] and a["ctr"] and b["ctr"]): continue
        print("    %-16s%9.3f%9.3f%9.3f%9s" % (
            fam, b["stem"] / a["stem"], b["ctr"] / a["ctr"], b["space"] / a["space"],
            "%.2f/%.2f" % (a["spctr"], b["spctr"])))
    print()
