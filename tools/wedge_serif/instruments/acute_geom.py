"""acute_geom.py -- the ACUTE measured on its letters, any font. Round 453 (2026-09-30), owner on
the italic "aquí?": "reduce the accent length and/or make angle of stroke to avoid near collision".

    venv/bin/python instruments/acute_geom.py FONT ...

The acute = the accented raster minus its base (dilated 2 px), above the base's top. Printed: length along its principal axis, lean from vertical,
mean width -- per x-height, in each font's own units, on í é á ó ú (median)."""
import sys, math, statistics, freetype, numpy as np, unicodedata
from scipy import ndimage as ndi
from fontTools.ttLib import TTFont

def raster(f, ch):
    f.load_char(ch, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING)
    b = f.glyph.bitmap
    return np.array(b.buffer, np.uint8).reshape(b.rows, b.pitch)[:, :b.width] >= 128, f.glyph.bitmap_left, f.glyph.bitmap_top

def place(parts, pad=40):
    L = min(l for a, l, t in parts) - pad; R = max(l + a.shape[1] for a, l, t in parts) + pad
    T = max(t for a, l, t in parts) + pad; B = min(t - a.shape[0] for a, l, t in parts) - pad
    out = []
    for a, l, t in parts:
        c = np.zeros((T - B, R - L), bool); c[T - t:T - t + a.shape[0], l - L:l - L + a.shape[1]] = a; out.append(c)
    return out

for p in sys.argv[1:]:
    f = freetype.Face(p); upm = f.units_per_EM; f.set_pixel_sizes(0, upm)
    f.load_char('x', freetype.FT_LOAD_NO_HINTING); xh = f.glyph.metrics.horiBearingY / 64
    try:
        sx = TTFont(p)['OS/2'].sxHeight
        if p.split('/')[-1].startswith('Albo') and sx: xh = float(sx)
    except Exception: pass
    rows = []
    for ch in "íéáóú":
        b = unicodedata.normalize('NFD', ch)[0]; b = 'ı' if b == 'i' else b
        try: ca, cb = place([raster(f, ch), raster(f, b)])
        except Exception: continue
        m = ca & ~ndi.binary_dilation(cb, iterations=2)
        ys, xs = np.nonzero(cb); m[ys.min() - 1:, :] = False
        my, mx = np.nonzero(m)
        if my.size < 50: continue
        P = np.stack([mx.astype(float), -my.astype(float)], 1); P -= P.mean(0)
        w, v = np.linalg.eigh(np.cov(P.T)); ax = v[:, 1]
        proj = P @ ax; length = proj.max() - proj.min()
        lean = math.degrees(math.atan2(abs(ax[0]), abs(ax[1])))
        width = m.sum() / length
        rows.append((ch, length / xh, lean, width / xh))
    if not rows: print(p.split('/')[-1], 'n/a'); continue
    med = lambda i: statistics.median(r[i] for r in rows)
    print(f"{p.split('/')[-1][:32]:32s} length {med(1):.3f} xh  lean {med(2):4.1f} deg  width {med(3):.3f} xh   í: len {rows[0][1]:.3f} lean {rows[0][2]:.1f}")
