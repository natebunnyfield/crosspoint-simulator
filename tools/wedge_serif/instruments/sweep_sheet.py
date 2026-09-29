"""sweep_sheet.py -- a set of glyphs from one or more built fonts, large, unhinted, one cell each.

    python3 instruments/sweep_sheet.py out.png "abcdef" A.ttf [B.ttf ...]
    env: PX (em size in px, default 600), COLS (default 6), LAB (1 = label each cell)

Each font gets its own row block, so passing a base and an arm gives a before/after pair per glyph
(the rows interleave: glyph 1 base, glyph 1 arm, ...). Baseline and x-line (the font's own 'x'
height) are drawn in light gray. Written for the 2026-09-28 issue sweep: every lowercase of each cut
inspected at ~600-900 px em, which is how lumps, slits and horns no gate sees are found.
"""
import sys, os, freetype, numpy as np
from PIL import Image, ImageDraw, ImageFont
out = sys.argv[1]; chars = sys.argv[2]; fonts = sys.argv[3:]
PX = int(os.environ.get("PX", "600")); COLS = int(os.environ.get("COLS", "6"))
F = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)


def cell(path, ch):
    f = freetype.Face(path); f.set_pixel_sizes(0, PX)
    try:
        from fontTools.ttLib import TTFont
        _v = TTFont(path)['OS/2'].sxHeight if os.path.basename(path).startswith('Albo') else 0   # Albo's 'x' has flags over its 429 x-height (review 2026-09-28); refs' sxHeight is unreliable
    except Exception:
        _v = 0
    if _v and _v > 0:
        xh = _v * PX / f.units_per_EM
    else:
        f.load_char('x', freetype.FT_LOAD_NO_HINTING); xh = f.glyph.metrics.horiBearingY / 64
    f.load_char(ch, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING); g = f.glyph; b = g.bitmap
    a = np.array(b.buffer, np.uint8).reshape(b.rows, b.pitch)[:, :b.width] if b.rows else np.zeros((1, 1), np.uint8)
    adv = g.advance.x / 64
    W = int(max(adv, b.width + max(0, g.bitmap_left)) + PX * 0.25); H = int(PX * 1.25)
    im = Image.new("L", (W, H), 250); d = ImageDraw.Draw(im)
    base = int(PX * 0.95); x0 = int(PX * 0.1)
    d.line([(0, base), (W, base)], fill=205); d.line([(0, base - xh), (W, base - xh)], fill=205)
    d.line([(x0, base - PX * 0.9), (x0, base + PX * 0.2)], fill=225); d.line([(x0 + adv, base - PX * 0.9), (x0 + adv, base + PX * 0.2)], fill=225)
    if b.rows:
        im.paste(Image.fromarray(255 - a), (x0 + g.bitmap_left, base - g.bitmap_top), Image.fromarray(a))
    d.text((4, 4), f"{os.path.basename(path)} '{ch}'", fill=60, font=F)
    return im


cells = []
for ch in chars:
    for p in fonts:
        cells.append(cell(p, ch))
rows = [cells[i:i + COLS] for i in range(0, len(cells), COLS)]
W = max(sum(c.width for c in r) for r in rows); H = sum(max(c.height for c in r) for r in rows)
sheet = Image.new("L", (W, H), 250); y = 0
for r in rows:
    x = 0
    for c in r:
        sheet.paste(c, (x, y)); x += c.width
    y += max(c.height for c in r)
sheet.save(out); print(out, sheet.size)
