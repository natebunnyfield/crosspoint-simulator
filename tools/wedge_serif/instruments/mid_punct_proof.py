#!/usr/bin/env python3
"""mid_punct_proof.py -- the mid-punctuation arms as proof pictures (docs/albo-mid-punctuation-2026-10-04.md).

    $VENV/bin/python instruments/mid_punct_proof.py OUT today=DIR Q1=DIR Q2=DIR ...   (DIR holds the four Albo-*.ttf)

Every image is a PNG at native pixels; a magnified one is integer NEAREST and says its factor in
its name and in the caption the doc gives it. Text goes through the reader's own rasterization
(`tittle_proof.text_img`: FreeType unhinted, the 2-bit levels, HarfBuzz placement with the kerns).

  lead.png         ONE small image: a line carrying every class, the Regular at 10 pt on the X3
                   (150 dpi), 4x NEAREST -- today on top, each arm beneath, labeled
  lead44.png       the same line at 44 pt, 1x
  words_<C>.png    the six test lines at 44 pt, 1x; per line a block of rows, today first.
                   C is the cut: R Regular, I Italic, B Bold, Z Bold Italic (never "BI")
  read_<C>.png     the same at 10 pt on the X3, 4x NEAREST
  marks_<C>.png    each mark alone at a 300 px x-height, 8-bit unhinted, against the baseline, the
                   x-height's middle (dotted), the x-line and the cap line; today and each arm
                   side by side, each cell captioned with the mark's ink center in font units
"""
import os, sys
import numpy as np, freetype
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from tittle_proof import text_img          # the reader's rasterization, as the tittle round used it
from bold_s_proof import lab, stack, hcat
import poor_proof as P

PAPER = tuple(int(v) for v in P.PAPER)
LAB = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 22)
SMALL = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 18)
CUTS = (("Regular", "R"), ("Italic", "I"), ("Bold", "B"), ("BoldItalic", "Z"))
LINES = ["co\u00b7operate \u00b7 the \u00b7\u00b7 list", "well-known self-made", "1990\u20132000 pages 3\u20137",
         "word\u2014word", "\u2022 first item", "3 \u00d7 4 = 12 \u2212 2 \u00f7 1 + 0"]
LEAD = "1 \u00b7 Wrap \u2014 well-known 3\u20137 \u00b7 3 \u00d7 4 = 12 \u2212 2 \u2022 list"
MARKS = ["\u00b7", "\u2022", "-", "\u2013", "\u2014", "\u2212", "+", "=", "\u00d7", "\u00f7", "\u00ab"]
NAMES = {"\u00b7": "middle dot", "\u2022": "bullet", "-": "hyphen", "\u2013": "en dash", "\u2014": "em dash",
         "\u2212": "minus", "+": "plus", "=": "equal", "\u00d7": "multiply", "\u00f7": "divide",
         "\u00ab": "guillemet (not moved)"}


def labeled(label, img, w=110):
    return np.concatenate([lab(label, img.shape[0], w), img], 1)


def rows(arms, cut, line, pt, mag):
    return [labeled(l, text_img(os.path.join(d, f"Albo-{cut}.ttf"), line, pt, mag)) for l, d in arms]


def heading(text, W, h=34):
    im = Image.new("RGB", (W, h), PAPER); ImageDraw.Draw(im).text((10, 6), text, fill=(30, 30, 30), font=LAB)
    return np.array(im)


def block_image(arms, cut, pt, mag):
    parts = []
    for line in LINES:
        rs = rows(arms, cut, line, pt, mag); W = max(r.shape[1] for r in rs)
        parts += [heading(" ".join(f"U+{ord(ch):04X}" for ch in dict.fromkeys(line) if ord(ch) > 127 or ch in "-+=")
                          or line, W), stack(rs, gap=4)]
    return stack(parts, gap=18)


def _box(face, ch):
    face.load_char(ch, freetype.FT_LOAD_NO_SCALE | freetype.FT_LOAD_NO_HINTING); b = face.glyph.outline.get_bbox()
    return b.yMin, b.yMax


def mark_cell(path, ch, label, XHPX=300, xh_units=None):
    """One mark at a 300 px x-height with the guides; the caption is its ink center in units."""
    f = freetype.Face(path)
    xh = xh_units or float(np.median([_box(f, c)[1] for c in "zu\u0131nm"] + [sum(_box(f, c)) for c in "oecsa"]))
    cap = _box(f, "H")[1]; k = XHPX / xh
    f.set_char_size(int(round(f.units_per_EM * k * 64)), 0, 72, 72)
    f.load_char(ch, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING); b = f.glyph.bitmap
    a = np.array(b.buffer, np.uint8).reshape(b.rows, b.pitch)[:, :b.width].copy()
    adv = f.glyph.advance.x / 64; left, top = f.glyph.bitmap_left, f.glyph.bitmap_top
    y0, y1 = _box(f, ch); ctr = (y0 + y1) / 2
    base = int(round(cap * k)) + 40; H = base + 90; W = int(max(adv, left + b.width) + 60)
    im = Image.new("L", (W, H), 250); d = ImageDraw.Draw(im)
    for y, shade in ((base, 150), (base - XHPX, 175), (base - int(round(cap * k)), 175)):
        d.line([(0, y), (W, y)], fill=shade, width=2)
    ym = base - XHPX // 2
    for x in range(0, W, 12): d.line([(x, ym), (x + 5, ym)], fill=165, width=2)   # the x-height's middle, dotted
    im.paste(Image.fromarray(255 - a), (30 + left, base - top), Image.fromarray(a))
    yc = base - int(round(ctr * k)); d.line([(W - 22, yc), (W - 6, yc)], fill=60, width=3)   # the ink center, a tick at the right
    d.text((8, base + 10), f"{label}", fill=0, font=LAB)
    d.text((8, base + 42), f"center {ctr:.0f} = {ctr / xh:.3f} xh", fill=60, font=SMALL)
    return np.array(im.convert("RGB"))


def marks_image(arms, cut):
    rs = []
    for ch in MARKS:
        cells = [mark_cell(os.path.join(d, f"Albo-{cut}.ttf"), ch, l) for l, d in arms]
        row = hcat(cells, gap=16)
        rs += [heading(f"U+{ord(ch):04X} {NAMES[ch]}", row.shape[1]), row]
    return stack(rs, gap=10)


if __name__ == "__main__":
    out = sys.argv[1]; arms = [a.split("=", 1) for a in sys.argv[2:]]; os.makedirs(out, exist_ok=True)
    Image.fromarray(stack(rows(arms, "Regular", LEAD, 10, 4), gap=6)).save(os.path.join(out, "lead.png"))
    Image.fromarray(stack(rows(arms, "Regular", LEAD, 44, 1), gap=6)).save(os.path.join(out, "lead44.png"))
    for cut, c in CUTS:
        Image.fromarray(block_image(arms, cut, 44, 1)).save(os.path.join(out, f"words_{c}.png"))
        Image.fromarray(block_image(arms, cut, 10, 4)).save(os.path.join(out, f"read_{c}.png"))
        Image.fromarray(marks_image(arms, cut)).save(os.path.join(out, f"marks_{c}.png"))
    for f in sorted(os.listdir(out)):
        if f.endswith(".png"): print(f, Image.open(os.path.join(out, f)).size)
