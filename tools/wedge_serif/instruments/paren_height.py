#!/usr/bin/env python3
"""paren_height.py -- where do the parentheses sit against the text? Owner todo
2026-10-02: *"italic parentheses seem low or text is too high"*.

    $VENV/bin/python instruments/paren_height.py DIR      (DIR holds the four Albo-*.ttf)

Outline ink boxes, unhinted, font units, in X-HEIGHTS (0 = baseline, 1 = the x's top):
  ( top / bottom   the parenthesis's extremes
  asc / desc       the l's top and the p's bottom -- the text's own extremes
  cap              the H's top
  ctr off          the parenthesis's center minus the center of [desc, asc]; + = sits high
  top-asc          how far the parenthesis rises past the ascender
  desc-bot         how far it hangs below the descender
"""
import os, sys
import numpy as np, freetype
SUP = "/System/Library/Fonts/Supplemental/"; LIB = os.path.expanduser("~/Library/Fonts/")
REFS_I = [("Flanker I", LIB + "flanker-griffo.italic.otf", 0), ("Poetica", LIB + "Poetica Std Regular.otf", 0),
          ("Pagella I", LIB + "texgyrepagella-italic.otf", 0), ("Palatino I", "/System/Library/Fonts/Palatino.ttc", 1),
          ("Georgia I", SUP + "Georgia Italic.ttf", 0), ("Charter I", SUP + "Charter.ttc", 1),
          ("Times I", SUP + "Times New Roman Italic.ttf", 0), ("Baskerville I", SUP + "Baskerville.ttc", 2)]
REFS_R = [("Flanker R", LIB + "flanker-griffo.regular.otf", 0), ("Pagella R", LIB + "texgyrepagella-regular.otf", 0),
          ("Palatino R", "/System/Library/Fonts/Palatino.ttc", 0), ("Georgia R", SUP + "Georgia.ttf", 0),
          ("Charter R", SUP + "Charter.ttc", 0), ("Times R", SUP + "Times New Roman.ttf", 0),
          ("Baskerville R", SUP + "Baskerville.ttc", 0)]


def box(face, ch):
    face.load_char(ch, freetype.FT_LOAD_NO_SCALE | freetype.FT_LOAD_NO_HINTING); b = face.glyph.outline.get_bbox()
    return b.yMin, b.yMax


def row(path, idx):
    f = freetype.Face(path, idx); xh = box(f, "x")[1]
    pl, pr = box(f, "("), box(f, ")"); asc = box(f, "l")[1]; desc = box(f, "p")[0]; cap = box(f, "H")[1]
    bot, top = (pl[0] + pr[0]) / 2 / xh, (pl[1] + pr[1]) / 2 / xh; a, d = asc / xh, desc / xh
    return dict(top=top, bot=bot, asc=a, desc=d, cap=cap / xh, off=(top + bot) / 2 - (a + d) / 2, tasc=top - a, dbot=d - bot)


def table(rows):
    print(f"{'':15s} {'( top':>6s} {'( bot':>6s} {'asc':>6s} {'desc':>6s} {'cap':>6s} {'ctr off':>8s} {'top-asc':>8s} {'desc-bot':>9s}")
    for l, r in rows:
        print(f"{l:15s} {r['top']:6.3f} {r['bot']:6.3f} {r['asc']:6.3f} {r['desc']:6.3f} {r['cap']:6.3f} {r['off']:8.3f} {r['tasc']:8.3f} {r['dbot']:9.3f}")


if __name__ == "__main__":
    d = sys.argv[1]
    for title, cuts, refs in (("ITALIC", ["Italic", "BoldItalic"], REFS_I), ("ROMAN", ["Regular", "Bold"], REFS_R)):
        rows = [(f"Albo {c}", row(os.path.join(d, f"Albo-{c}.ttf"), 0)) for c in cuts]
        rr = [(l, row(p, i)) for l, p, i in refs if os.path.exists(p)]
        print(f"== {title}"); table(rows + rr)
        m = {k: np.median([r[k] for _, r in rr]) for k in rr[0][1]}
        table([("refs median", m)]); print()
