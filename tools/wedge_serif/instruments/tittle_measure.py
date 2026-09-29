"""tittle_measure.py -- the i's dot against the i's own stem, in any font, one number per font.

    python3 instruments/tittle_measure.py FONT[@deg] ...     (scipy needed: use the venv python)

Rendered unhinted at 1000 px/em-equivalent (1 px = 1 unit at 1000 upm). The dot is the topmost
connected ink part of 'i'; the stem is the lowest, measured as its horizontal run at 0.5 xh times
cos(italic angle) = the stroke's width across itself. Reports the dot's equivalent-disc diameter
(sqrt of area), its box, dot/stem, dot/xh and the dot floor's clearance above the x-line in xh.
The x-height is Albo's OS/2 sxHeight (429), and the top of 'x' for every other font.
`@deg` forces the angle (Coelacanth declares 0; 12 fits). Written 2026-09-28 for the italic
tittle (docs/albo-parts-audit-2026-09-28.md: the italic dot is under 4 dark px at 1x).
"""
import sys, os, math, freetype, numpy as np
from scipy import ndimage
from fontTools.ttLib import TTFont


def xheight(path, f):
    """Albo: its OS/2 sxHeight (the build writes the design x-height, 429) -- NOT the top of 'x', whose
    flags reach 451-470 and put every Albo "x xh" number 5-7% low in this script's first version
    (review, 2026-09-28). Everything else: the top of 'x', which in the references matches the top of
    'u' within 1%; their sxHeight fields are not trustworthy (Poetica's reads 600 on a 394 x)."""
    if os.path.basename(path).startswith("Albo"):
        try:
            v = TTFont(path)['OS/2'].sxHeight
            if v and v > 0:
                return v * f.size.y_ppem / f.units_per_EM
        except Exception:
            pass
    f.load_char('x', freetype.FT_LOAD_NO_HINTING); return f.glyph.metrics.horiBearingY / 64


def measure(path, ch='i', deg=None):
    if deg is None:
        try: deg = abs(TTFont(path)['post'].italicAngle)
        except Exception: deg = 0.0
    f = freetype.Face(path); upm = f.units_per_EM; f.set_pixel_sizes(0, int(upm))
    xh = xheight(path, f)
    f.load_char(ch, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING); g = f.glyph; b = g.bitmap
    a = np.array(b.buffer, np.uint8).reshape(b.rows, b.pitch)[:, :b.width] >= 128
    lab, n = ndimage.label(a)
    comps = []
    for k in range(1, n + 1):
        ys, xs = np.nonzero(lab == k)
        if len(ys) < 30: continue
        comps.append((ys.min(), ys.max(), xs.min(), xs.max(), len(ys), k))
    comps.sort()
    dot, stem = comps[0], comps[-1]
    top = g.bitmap_top
    row = int(top - 0.5 * xh); xs = np.nonzero(lab[row] == stem[5])[0]
    run = xs.max() - xs.min() + 1
    perp = run * math.cos(math.radians(deg))
    deq = 2 * math.sqrt(dot[4] / math.pi)
    floor = top - dot[1]
    sc = 1000.0 / upm
    return dict(deg=deg, xh=round(xh * sc), dot_deq=round(deq * sc, 1), dot_box=(int((dot[3] - dot[2] + 1) * sc), int((dot[1] - dot[0] + 1) * sc)),
                stem=round(perp * sc, 1), dot_over_stem=round(deq / perp, 2), dot_over_xh=round(deq / xh, 3),
                clear_over_xh=round((floor - xh) / xh, 3))


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        p, deg = (arg.split('@') + [None])[:2]
        m = measure(p, 'i', float(deg) if deg else None)
        print(f"{p.split('/')[-1]:44s} dot {m['dot_deq']:6.1f}  box {m['dot_box']}  stem {m['stem']:6.1f}  dot/stem {m['dot_over_stem']:.2f}  dot/xh {m['dot_over_xh']:.3f}  clear {m['clear_over_xh']:.3f} xh  (xh {m['xh']}, {m['deg']:.0f} deg)")
