"""ref_row.py -- ONE glyph across many fonts at ONE x-height, baseline and x-line drawn. Char is an argument.

    python3 instruments/ref_row.py out.png CHARS "path[@deg]::label" ...
    env: XH (x-height in px, default 220), COLS (default 6), UNSHEAR (1 = unshear each font by its
         italic angle, or @deg, so the letters are compared upright; default 0)

The same picture as ref_sheet.py (which is hard-wired to the c) with the character on the command
line; several characters in CHARS give one row block per character. Written for the 2026-09-28
issue sweep: every italic terminal built on the family's finial machinery was checked against all
the references at one x-height before anything was concluded about it (the c's lesson, round 433).
"""
import sys, os, math, freetype, numpy as np
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont
F = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 15)
out_path = sys.argv[1]; chars = sys.argv[2]; items = sys.argv[3:]
XH = int(os.environ.get("XH", "220")); COLS = int(os.environ.get("COLS", "6")); UNSHEAR = os.environ.get("UNSHEAR", "0") == "1"
CW, CH = int(XH * 1.55), int(XH * 2.6)


def angle(p):
    try: return abs(TTFont(p)['post'].italicAngle)
    except Exception: return 0.0


cells = []
for ch in chars:
    for it in items:
        p, lab = it.split("::")
        p, deg = (p.split('@') + [None])[:2]
        deg = float(deg) if deg else angle(p)
        f = freetype.Face(p)
        f.set_pixel_sizes(0, 200)
        try:
            _v = TTFont(p)['OS/2'].sxHeight if os.path.basename(p).startswith('Albo') else 0   # Albo's 'x' has flags over its 429 x-height (review 2026-09-28); refs' sxHeight is unreliable
        except Exception:
            _v = 0
        if _v and _v > 0:
            xh = _v * 200.0 / f.units_per_EM
        else:
            f.load_char('x', freetype.FT_LOAD_NO_HINTING); xh = f.glyph.metrics.horiBearingY / 64
        f.set_pixel_sizes(0, int(round(200 * XH / xh)))
        f.load_char(ch, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING); b = f.glyph.bitmap
        im = Image.new("L", (CW, CH), 250); d = ImageDraw.Draw(im)
        base = int(XH * 1.95); d.line([(0, base), (CW, base)], fill=200); d.line([(0, base - XH), (CW, base - XH)], fill=200)
        if b.rows:
            a = np.array(b.buffer, np.uint8).reshape(b.rows, b.pitch)[:, :b.width]
            g = Image.fromarray(a)
            top = f.glyph.bitmap_top; left = f.glyph.bitmap_left
            if UNSHEAR and deg:
                t = math.tan(math.radians(deg)); pad = int(abs(t) * b.rows) + 2
                gg = Image.new("L", (b.width + 2 * pad, b.rows), 0); gg.paste(g, (pad, 0))
                # row y stands (top - y) above the baseline; unshearing moves it LEFT by t x that height:
                # x_src = x_dst + t * (top - y_dst)
                gg = gg.transform(gg.size, Image.AFFINE, (1, -t, t * top, 0, 1, 0), Image.BILINEAR)
                g = gg; left = left - pad
            im.paste(Image.new("L", g.size, 0), (int(XH * 0.25) + left, base - top), g)
        d.text((4, 4), f"{lab} '{ch}'", fill=0, font=F); cells.append(im)
rows = (len(cells) + COLS - 1) // COLS
out = Image.new("L", (CW * min(COLS, len(cells)), CH * rows), 250)
for i, c in enumerate(cells): out.paste(c, ((i % COLS) * CW, (i // COLS) * CH))
out.save(out_path); print(out_path, out.size)
