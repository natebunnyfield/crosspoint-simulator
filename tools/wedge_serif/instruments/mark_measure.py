"""mark_measure.py -- an accent's weight: its ink area, its length (the box diagonal) and its mean
stroke width (2 x area / outline length, the FIT table's measure), against the font's own lowercase
stem, in any font. Unhinted, 1000 px/em, the spacing mark itself (U+00B4 etc.).

    venv/bin/python instruments/mark_measure.py "´`˜¨" FONT[@deg] ...

Written 2026-09-28 for the issue sweep (docs/albo-issue-sweep-2026-09-28.md): Albo's acute had zero
dark pixels at 8-12 pt on the X3 where every reference's had 1-10.
"""
import sys, math, freetype, numpy as np
from scipy import ndimage as ndi
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
        try: f.load_char(ch, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING)
        except Exception: out.append(f"{ch} n/a"); continue
        b = f.glyph.bitmap
        if not b.rows: out.append(f"{ch} empty"); continue
        a = np.array(b.buffer, np.uint8).reshape(b.rows, b.pitch)[:, :b.width] >= 128
        area = a.sum(); edge = (a & ~ndi.binary_erosion(a)).sum()
        mw = 2.0 * area / max(edge, 1)
        d = ndi.distance_transform_edt(np.pad(a, 1))
        out.append(f"{ch} {a.shape[1] * sc:.0f}x{a.shape[0] * sc:.0f} area {area * sc * sc / 1000:.1f}k w {mw * sc:.0f} ({mw / stem:.2f}) max {2 * d.max() * sc:.0f}")
    print(f"{p.split('/')[-1][:30]:30s} stem {stem * sc:5.1f} | " + "  ".join(out))
