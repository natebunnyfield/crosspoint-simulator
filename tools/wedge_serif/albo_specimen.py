"""A complete specimen of both Albo styles, as the owner reviews them.

Owner 2026-09-18: *"show me a complete specimen for my review."* Every figure
here is PNG at native pixels; the reading-size rows are magnified by an
INTEGER with nearest-neighbour and say so in their label (the proof-figure
rules in CLAUDE.md). Nothing is scaled by the page.

    PYTHON_GIL=0 python3 albo_specimen.py --roman R.ttf --italic I.ttf --out DIR

Writes, per style: reading.png (13 px x5 and 17 px x4, the phone's real
sizes), paragraph.png (40 px native), sheet.png (every encoded glyph),
lines.png (capitals, lowercase, figures, marks and quotes, word tests), and an
index.html that lays them out roman first.
"""
import argparse, os, string, unicodedata
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont

PARA = ("The quick brown fox jumps over the lazy dog; it’s 1970, and the 17th of 5 in 1861 "
        "was a Sunday. “Razzmatazz,” said the Quartermaster, “is a jazz word.” "
        "Minimum illumination of a page: seven, forty-seven, 78,703. Don’t quote me — "
        "or do, at o’clock, in Zanzibar, with sixty-six ZOOs and a QUIZ.")
PARA2 = ("In the beginning the printer set a line of type by hand, letter by letter, from a case; "
         "he judged the word image, not the letter, and he spaced by eye until the page read evenly. "
         "That is what this face is for: to be read at thirteen pixels on an ink panel and to look, "
         "at that size, like a page somebody cut and cast and printed.")
WORDS = ["razzmatazz", "QUIZ", "SWIX", "Quarter", "ZOO", "it’s", "s’s", "don’t", "1970", "7,777",
         "49,503", "Vi", "good", "minimum", "Albo", "“so”", "the 9th", "R4 R2 Q3", "fi ffi fl"]


def font(path, px): return ImageFont.truetype(path, px)


def text_img(path, txt, px, pad=10, width=None):
    f = font(path, px)
    if width:                                  # wrap to a pixel width
        words, lines, cur = txt.split(" "), [], ""
        for w in words:
            t = (cur + " " + w).strip()
            if f.getlength(t) > width and cur: lines.append(cur); cur = w
            else: cur = t
        lines.append(cur)
    else:
        lines = [txt]
    lh = int(px * 1.32)
    W = int(max(f.getlength(l) for l in lines)) + pad * 2
    im = Image.new("L", (W, lh * len(lines) + pad * 2), 255)
    d = ImageDraw.Draw(im)
    for i, l in enumerate(lines):
        d.text((pad, pad + i * lh), l, font=f, fill=0)
    return im


def stack(cells, gap=14, label_h=18):
    W = max(i.width for _, i in cells) + 16
    H = sum(i.height + gap + label_h for _, i in cells) + 8
    o = Image.new("L", (W, H), 255); d = ImageDraw.Draw(o); y = 6
    for lab, im in cells:
        d.text((8, y), lab, fill=110); o.paste(im, (8, y + label_h)); y += im.height + gap + label_h
    return o


def reading(path, out):
    cells = []
    for px, mag in ((13, 5), (17, 4)):
        im = text_img(path, PARA, px, width=int(560 * px / 13))
        cells.append((f"{px} px, x{mag} nearest-neighbour", im.resize((im.width * mag, im.height * mag), Image.NEAREST)))
    stack(cells).save(out)


def paragraph(path, out):
    stack([("40 px, native", text_img(path, PARA, 40, width=1500)),
           ("40 px, native", text_img(path, PARA2, 40, width=1500))]).save(out)


def sheet(path, out, px=110, per_row=22):
    f = TTFont(path); cmap = f.getBestCmap()
    chars = [chr(c) for c in sorted(cmap) if 0x20 < c < 0x3000 and unicodedata.category(chr(c))[0] not in "CZM"]
    fnt = font(path, px); rows = [chars[i:i + per_row] for i in range(0, len(chars), per_row)]
    cw = int(px * 1.15); lh = int(px * 1.45)
    im = Image.new("L", (cw * per_row + 20, lh * len(rows) + 20), 255); d = ImageDraw.Draw(im)
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            d.text((10 + c * cw, 10 + r * lh), ch, font=fnt, fill=0)
    im.save(out); return len(chars)


def lines(path, out):
    cells = [("capitals", text_img(path, string.ascii_uppercase, 96)),
             ("lowercase", text_img(path, string.ascii_lowercase, 96)),
             ("figures", text_img(path, "0123456789  ½ ¼  ¹²³", 96)),
             ("marks and quotes", text_img(path, ".,;:!?  ‘’ “”  ' \"  ( ) [ ]  - – —  & @ #", 96)),
             ("word tests, 60 px", text_img(path, "   ".join(WORDS), 60)),
             ("word tests, 13 px x5", (lambda im: im.resize((im.width * 5, im.height * 5), Image.NEAREST))(text_img(path, "   ".join(WORDS), 13)))]
    stack(cells).save(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--roman", required=True); ap.add_argument("--italic", required=True)
    ap.add_argument("--out", required=True); ap.add_argument("--label", default="")
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    counts = {}
    for style, path in (("roman", a.roman), ("italic", a.italic)):
        reading(path, os.path.join(a.out, f"{style}-reading.png"))
        paragraph(path, os.path.join(a.out, f"{style}-paragraph.png"))
        counts[style] = sheet(path, os.path.join(a.out, f"{style}-sheet.png"))
        lines(path, os.path.join(a.out, f"{style}-lines.png"))
    print("specimen written to", a.out, counts)


if __name__ == "__main__":
    main()
