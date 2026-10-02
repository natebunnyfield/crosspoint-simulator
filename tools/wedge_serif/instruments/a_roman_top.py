"""a_roman_top.py -- the roman a's top stroke against the letters around it: height and interior white.

    $VENV/bin/python instruments/a_roman_top.py DIR [DIR ...]      (DIR holds Albo-Regular.ttf / Albo-Bold.ttf)
    $VENV/bin/python instruments/a_roman_top.py --refs              (the same numbers on the reference romans)

Owner todo 2026-10-01: *"raise just the top stroke of roman 'a' so it matches the same x height
and interior spacing of others"*; 2026-10-02 *"show me improved roman 'a'"*. Per face, in units at
the face's own o-height scaled to Albo's 444:

  tops      ink top of a, o, c, e, n
  a eye     the white between the a's top stroke and its bowl: the vertical run of white at the
            bowl's own center column, from the bowl's top edge up to the hood's underside
  e eye     the same white in the e: from the bar's top edge up to the top arc's underside, at
            the e's center column
  a counter the bowl's own counter, vertical at its center column
  o counter the o's counter height at its center column
  a gap     the narrowest white between the top stroke and the bowl (2-D: the least distance from
            any white pixel of the eye to... measured as twice the max inscribed radius of the eye
            region, i.e. the widest disc that fits between hood and bowl)

Written for docs/albo-roman-a-top-2026-10-02.md.
"""
import os, sys
import numpy as np, freetype
from scipy.ndimage import distance_transform_edt as edt, label

SUP = "/System/Library/Fonts/Supplemental/"
REFS = [("Georgia", SUP + "Georgia.ttf", 0), ("Charter", SUP + "Charter.ttc", 0),
        ("Palatino", "/System/Library/Fonts/Palatino.ttc", 0), ("Hoefler", SUP + "Hoefler Text.ttc", 0),
        ("Baskerville", SUP + "Baskerville.ttc", 0), ("Big Caslon", SUP + "BigCaslon.ttf", 0),
        ("Iowan", SUP + "Iowan Old Style.ttc", 0), ("Pagella", os.path.expanduser("~/Library/Fonts/texgyrepagella-regular.otf"), 0),
        ("Albertus", os.path.expanduser("~/Downloads/Albertus Medium Regular.ttf"), 0)]
OH = 444.0   # Albo's o top (Regular), the common scale


def glyph(path, idx, ch, px):
    f = freetype.Face(path, idx); f.set_pixel_sizes(0, px)
    f.load_char(ch, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING)
    b = f.glyph.bitmap
    a = np.array(b.buffer, np.uint8).reshape(b.rows, b.pitch)[:, :b.width] if b.rows else np.zeros((1, 1), np.uint8)
    return a > 127, f.glyph.bitmap_top, f.glyph.bitmap_left


def vruns(col):
    r = []; on = False
    for i, v in enumerate(col):
        if v and not on: s = i; on = True
        elif not v and on: r.append((s, i - 1)); on = False
    if on: r.append((s, len(col) - 1))
    return r


def measure(path, idx=0):
    # scale so the o's ink top is ~1000 px: everything is read at that resolution, reported in units of OH
    ink, top, _ = glyph(path, idx, "o", 1000)
    px = int(round(1000 * 1000.0 / top))
    k = OH / glyph(path, idx, "o", px)[1]       # px -> units on Albo's scale
    out = {}
    for ch in "aocen":
        g, t, l = glyph(path, idx, ch, px)
        out["top_" + ch] = t * k
    # the a: find the stem (rightmost long vertical run) and the bowl/eye regions
    a, t, l = glyph(path, idx, "a", px)
    H, W = a.shape
    white = ~a
    # label the white inside the glyph's bbox that does not touch the border: the counter (bowl) is enclosed;
    # the eye (between hood and bowl) is open to the left. Measure along columns instead.
    cols = [c for c in range(W) if a[:, c].any()]
    x0, x1 = cols[0], cols[-1]
    # bowl center column: the column where the bowl is widest is hard; use 40% of the ink width from the left
    best = None
    for frac in [0.30, 0.35, 0.40, 0.45, 0.50]:
        c = int(x0 + frac * (x1 - x0))
        rr = vruns(a[:, c])   # top to bottom: hood, bowl top, bowl bottom
        if len(rr) >= 3:
            best = (frac, c, rr); break
    if best:
        frac, c, rr = best
        # rr[0] hood, rr[1] bowl top stroke, rr[-1] bowl bottom stroke (row 0 is the top)
        out["a_eye"] = (rr[1][0] - rr[0][1] - 1) * k
        out["a_counter"] = (rr[-1][0] - rr[1][1] - 1) * k if len(rr) >= 3 else float("nan")
        out["a_col"] = frac
    # e eye: center column, runs top arc, bar, bottom
    e, t, l = glyph(path, idx, "e", px)
    ecols = [c for c in range(e.shape[1]) if e[:, c].any()]
    c = int((ecols[0] + ecols[-1]) / 2)
    rr = vruns(e[:, c])
    if len(rr) >= 3:
        out["e_eye"] = (rr[1][0] - rr[0][1] - 1) * k
    o, t, l = glyph(path, idx, "o", px)
    ocols = [c for c in range(o.shape[1]) if o[:, c].any()]
    c = int((ocols[0] + ocols[-1]) / 2)
    rr = vruns(o[:, c])
    if len(rr) >= 2:
        out["o_counter"] = (rr[1][0] - rr[0][1] - 1) * k
    # a gap: the widest disc in the white between hood and bowl, left of the stem
    # (the white region right above the bowl's top and below the hood, bounded left at the hood's terminal)
    if best:
        d = edt(white)
        frac, c, rr = best
        r0, r1 = rr[0][1] + 1, rr[1][0] - 1
        if r1 > r0:
            out["a_gap"] = 2 * d[r0:r1 + 1, max(0, c - 40):c + 40].max() * k
    return out


def row(lab, m):
    g = lambda kk: m.get(kk, float("nan"))
    return (f"{lab:20s} a {g('top_a'):5.0f} o {g('top_o'):5.0f} c {g('top_c'):5.0f} e {g('top_e'):5.0f} n {g('top_n'):5.0f}"
            f" | a eye {g('a_eye'):5.1f}  e eye {g('e_eye'):5.1f}  a/e {g('a_eye')/g('e_eye'):.2f}"
            f" | a counter {g('a_counter'):5.1f}  o counter {g('o_counter'):5.1f}  a/o {g('a_counter')/g('o_counter'):.2f}  (col {g('a_col'):.2f})")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "--refs":
        for lab, p, i in REFS:
            if os.path.exists(p): print(row(lab, measure(p, i)))
        sys.exit(0)
    for d in args:
        for st in ("Regular", "Bold"):
            p = os.path.join(d, f"Albo-{st}.ttf")
            if os.path.exists(p): print(row(f"{os.path.basename(d.rstrip('/'))} {st}", measure(p)))
