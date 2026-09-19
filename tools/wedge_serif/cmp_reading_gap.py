"""The gap the READER gets, at the size he reads at: blank COLUMNS at 13 px.

Owner's device sets this face at 13 pt on a 2x panel, and at that size one
design unit is 1/77 of a pixel: a bearing moved by 20 units changes nothing a
reader can see, while a pair that lands one pixel wider than its neighbours
breaks a word in half. Every other instrument here measures the OUTLINE, which
is the right place to fit a face and the wrong place to ask "does *about* read
as *a bout*".

WHAT IT COUNTS. Both letters are rendered as one string, so the shaped advance
and the kern table are in it, and the x-height band's columns are reduced to
ink / not-ink at a coverage threshold. The number reported is the widest run of
BLANK columns between the two letters. At 13 px the whole lowercase of Albo
sits at 1 blank column -- that IS the rhythm -- so a pair at 2 is a hole and a
pair at 0 is two letters touching.

THIS IS A GATE AND NOT A LADDER. It is quantised to whole pixels on purpose:
it answers what the reader sees, and it cannot answer by how much, which is
what the outline instruments are for. Fit on those; confirm here.

Found with it, 2026-09-19: `t` before any tall letter (`th tb tk tl tf`) and
before `w` was the only lowercase family at 2 blank columns, which is the
coordinator's *"'the' reads as 't he'"* and *"'between' reads as 'bet ween'"*.
The same pass cleared `ab` and `al` -- reported as breaking, measured at 1
column exactly like their `nb` / `nl` controls, and the render agrees.

    PYTHON_GIL=0 python3 cmp_reading_gap.py <ttf>
    PYTHON_GIL=0 python3 cmp_reading_gap.py <ttf> --px 13 --px 17 --px 40
    PYTHON_GIL=0 python3 cmp_reading_gap.py <ttf> --words "about the between"
"""
import argparse, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

LOWER = "abcdefghijklmnopqrstuvwxyz"


def blanks(fnt, px, a, b, thr=40, xh_frac=0.46):
    """The widest run of blank columns between two letters' ink, in the
    x-height band, at `px`. None where either glyph puts no ink in the band."""
    W, H = px * 8, px * 3
    im = Image.new("L", (W, H), 255)
    ImageDraw.Draw(im).text((px, px * 2), a + b, font=fnt, fill=0, anchor="ls")
    v = 255 - np.asarray(im).astype(np.int16)
    band = v[px * 2 - max(2, int(px * xh_frac)): px * 2, :]
    ink = band.max(0) > thr
    xs = np.nonzero(ink)[0]
    if len(xs) < 2: return None
    runs, cur = [], 0
    for x in range(xs.min(), xs.max() + 1):
        if not ink[x]: cur += 1
        elif cur: runs.append(cur); cur = 0
    return max(runs) if runs else 0


def sweep(ttf, px, chars=LOWER):
    fnt = ImageFont.truetype(ttf, px)
    out = {}
    for a in chars:
        for b in chars:
            g = blanks(fnt, px, a, b)
            if g is not None: out[(a, b)] = g
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ttf")
    ap.add_argument("--px", type=int, action="append")
    ap.add_argument("--words")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    sizes = a.px or [13, 17]
    worst_total = 0
    for px in sizes:
        g = sweep(a.ttf, px)
        vals = np.array(list(g.values()))
        mode = int(np.bincount(vals).argmax())
        hole = sorted([p for p, v in g.items() if v > mode])
        shut = sorted([p for p, v in g.items() if v < mode])
        print("\n  %s at %d px -- %d lowercase pairs" % (os.path.basename(a.ttf), px, len(g)))
        print("    blank columns: " + "  ".join("%d:%d" % (k, int((vals == k).sum()))
                                                for k in range(vals.max() + 1)) + "   (rhythm = %d)" % mode)
        print("    %d pair(s) WIDER than the rhythm%s" % (len(hole), ":" if hole else "."))
        if hole and not a.quiet:
            for i in range(0, len(hole), 18):
                print("      " + " ".join(x + y for x, y in hole[i:i + 18]))
        print("    %d pair(s) TIGHTER (the rounds, mostly, and they are meant to be)" % len(shut))
        if shut and not a.quiet:
            for i in range(0, len(shut), 18):
                print("      " + " ".join(x + y for x, y in shut[i:i + 18]))
        # per-letter: which side of which letter owns the holes
        if hole:
            from collections import Counter
            L = Counter(x for x, _ in hole); R = Counter(y for _, y in hole)
            print("    by first letter (its RIGHT side): " + " ".join("%s:%d" % kv for kv in L.most_common(8)))
            print("    by second letter (its LEFT side): " + " ".join("%s:%d" % kv for kv in R.most_common(8)))
        worst_total += len(hole)
    if a.words:
        print()
        for px in sizes:
            fnt = ImageFont.truetype(a.ttf, px)
            for w in a.words.split():
                print("    %-14s %2dpx  " % (w, px) + " ".join(
                    "%s%s:%s" % (w[i], w[i + 1], blanks(fnt, px, w[i], w[i + 1])) for i in range(len(w) - 1)))
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
