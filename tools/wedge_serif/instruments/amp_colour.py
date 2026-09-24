"""The '&''s COLOUR in running text against the lowercase beside it -- round 381.

Owner 2026-09-24, on round 377's ampersand: *"italic ampersand is too thin."*
What thin means to a reader is how dark the mark sits in a line next to the
letters around it, so this measures exactly that, at the size he reads.

Each glyph is set ALONE at `px` (FreeType antialiasing, as PIL renders it) and
its darkness is summed: sum(255 - v) / 255 is its ink in pixels. Its COLOUR is
that ink over its own advance -- how much darkness it puts into each pixel of
line it occupies -- so a wide glyph is not counted dark for being wide. The
row reports the '&''s colour over the median colour of the lowercase in
`--text` (default: the proof line's own letters), at 13 px and at 60 px (the
13 px number is the reading-size truth but moves with pixel grid; 60 px is
the same measure with the grid noise gone).

    PYTHON_GIL=0 python3 instruments/amp_colour.py FONT.ttf [...]
"""
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

TEXT = "Smith Sons Black White rock roll bread butter"


def colour(ttf, ch, px):
    f = ImageFont.truetype(ttf, px)
    adv = f.getlength(ch)
    W, H = int(px * 4), int(px * 3); base = int(px * 2)
    ink = 0.0
    # average over four sub-pixel phases so one grid position does not decide it
    for dx in (0.0, 0.25, 0.5, 0.75):
        im = Image.new("L", (W, H), 255)
        ImageDraw.Draw(im).text((px + dx, base), ch, font=f, fill=0, anchor="ls")
        ink += (255 - np.asarray(im, float)).sum() / 255.0
    return (ink / 4) / adv


def row(ttf, px):
    lc = sorted({c for c in TEXT if c.islower()})
    med = float(np.median([colour(ttf, c, px) for c in lc]))
    return colour(ttf, "&", px) / med, med


def main():
    print(f"{'font':70s} {'&/lc 13px':>9s} {'&/lc 60px':>9s}")
    for p in sys.argv[1:]:
        a, _ = row(p, 13); b, _ = row(p, 60)
        print(f"{p[-70:]:70s} {a:9.3f} {b:9.3f}")


if __name__ == "__main__":
    main()
