"""bar_measure.py -- the vertical thickness of a horizontal bar glyph (hyphen, dashes, equals, the e's
bar) at its middle column, against the font's own lowercase stem (the l's horizontal run at 0.5 xh x
cos(italic angle)) and its x-height. Unhinted, 1000 px/em.

    venv/bin/python instruments/bar_measure.py "-–—=" FONT[@deg] ...

Every dark run crossing the glyph's middle column is listed (the = has two), in units and as a
fraction of the stem. Written 2026-09-28 for the italic dashes (docs/albo-parts-audit-2026-09-28.md:
"faint stroke > 25%" at 9 of 12 reader sizes).
"""
import sys, math, freetype, numpy as np
from fontTools.ttLib import TTFont
chars = sys.argv[1]; fonts = sys.argv[2:]
for arg in fonts:
    p, deg = (arg.split('@') + [None])[:2]
    if deg is None:
        try: deg = abs(TTFont(p)['post'].italicAngle)
        except Exception: deg = 0.0
    deg = float(deg); f = freetype.Face(p); upm = f.units_per_EM; f.set_pixel_sizes(0, upm); sc = 1000.0 / upm
    try:
        _v = TTFont(p)['OS/2'].sxHeight if p.split('/')[-1].startswith('Albo') else 0   # Albo only: refs' sxHeight is unreliable
    except Exception:
        _v = 0
    if _v and _v > 0:
        xh = float(_v)   # OS/2 sxHeight at 1 px per unit: Albo's 'x' has flags over its 429 (review 2026-09-28)
    else:
        f.load_char('x', freetype.FT_LOAD_NO_HINTING); xh = f.glyph.metrics.horiBearingY / 64
    f.load_char('l', freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING); b = f.glyph.bitmap
    a = np.array(b.buffer, np.uint8).reshape(b.rows, b.pitch)[:, :b.width] >= 128
    row = int(f.glyph.bitmap_top - 0.5 * xh); xs = np.nonzero(a[row])[0]
    stem = (xs.max() - xs.min() + 1) * math.cos(math.radians(deg))
    out = []
    for ch in chars:
        f.load_char(ch, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING); b = f.glyph.bitmap
        a = np.array(b.buffer, np.uint8).reshape(b.rows, b.pitch)[:, :b.width] >= 128
        col = a[:, a.shape[1] // 2]; runs = []; y = 0
        while y < len(col):
            if col[y]:
                y0 = y
                while y < len(col) and col[y]: y += 1
                runs.append(y - y0)
            y += 1
        out.append(f"{ch} " + "/".join(f"{r * sc:.0f}" for r in runs) + f" ({'/'.join(f'{r / stem:.2f}' for r in runs)})")
    print(f"{p.split('/')[-1][:34]:34s} stem {stem * sc:5.1f} xh {xh * sc:4.0f} | " + "  ".join(out))
