"""numbered_sheet.py -- one glyph (or a few) per OPTION, side by side, large, the option's NUMBER big above it.

    python3 instruments/numbered_sheet.py out.png CHARS "NUM::FONT.ttf" ["NUM::FONT.ttf" ...]
    env: PX (em size in px, default 900), NUMPX (number size, default 110)

For the owner's rulings by number (2026-09-28, "give them numbers"): each option is a column headed
by its number in type he can read on a phone, the glyphs unhinted at PX on a baseline and x-line
(the font's OS/2 x-height for Albo), lossless 8-bit gray, native pixels. Row 0 is today by
convention -- pass it first. Written for round 2 of the issue sweep
(docs/albo-issue-sweep-2026-09-28.md).
"""
import sys, os, freetype, numpy as np
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont

out = sys.argv[1]; chars = sys.argv[2]; specs = [s.split("::") for s in sys.argv[3:]]
PX = int(os.environ.get("PX", "900")); NUMPX = int(os.environ.get("NUMPX", "110"))
NF = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", NUMPX)
PAPER = 250


def column(num, path):
    f = freetype.Face(path); f.set_pixel_sizes(0, PX)
    xh = TTFont(path)['OS/2'].sxHeight * PX / f.units_per_EM
    cells = []
    for ch in chars:
        f.load_char(ch, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING); g = f.glyph; b = g.bitmap
        a = np.array(b.buffer, np.uint8).reshape(b.rows, b.pitch)[:, :b.width] if b.rows else np.zeros((1, 1), np.uint8)
        adv = g.advance.x / 64
        W = int(max(adv, b.width + max(0, g.bitmap_left)) + PX * 0.12); H = int(PX * 1.30)
        im = Image.new("L", (W, H), PAPER); d = ImageDraw.Draw(im)
        base = int(PX * 1.02); x0 = int(PX * 0.06)
        d.line([(0, base), (W, base)], fill=205); d.line([(0, base - xh), (W, base - xh)], fill=205)
        if b.rows:
            im.paste(Image.fromarray(255 - a), (x0 + g.bitmap_left, base - g.bitmap_top), Image.fromarray(a))
        cells.append(im)
    W = sum(c.width for c in cells); H = max(c.height for c in cells) + int(NUMPX * 1.3)
    col = Image.new("L", (max(W, int(NUMPX * 1.2)), H), PAPER)
    ImageDraw.Draw(col).text((int(PX * 0.06), int(NUMPX * 0.1)), num, fill=20, font=NF)
    x = 0
    for c in cells:
        col.paste(c, (x, int(NUMPX * 1.3))); x += c.width
    return col


cols = [column(n, p) for n, p in specs]
sep = 24
sheet = Image.new("L", (sum(c.width for c in cols) + sep * (len(cols) - 1), max(c.height for c in cols)), PAPER)
x = 0
for i, c in enumerate(cols):
    sheet.paste(c, (x, 0)); x += c.width
    if i < len(cols) - 1:
        ImageDraw.Draw(sheet).line([(x + sep // 2, 0), (x + sep // 2, sheet.height)], fill=215, width=2)
        x += sep
sheet.save(out); print(out, sheet.size)
