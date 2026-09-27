"""Stroke widths of a glyph from its ridge: 2 x the distance transform at the
ridge (3x3 local maxima), unhinted at 1000 ppem, reported as p10 (the light
strokes) and p90 (the heavy). Needs scipy (the session venv).

    python instruments/stroke_ridge.py FONT.ttf A V W
"""
import sys, numpy as np, freetype
from scipy.ndimage import distance_transform_edt as edt, maximum_filter
f = freetype.Face(sys.argv[1]); f.set_pixel_sizes(0, 1000)
for ch in sys.argv[2:]:
    f.load_char(ch, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING); b = f.glyph.bitmap
    a = np.array(b.buffer, np.uint8).reshape(b.rows, b.pitch)[:, :b.width] > 127
    d = edt(np.pad(a, 2)); ridge = (d == maximum_filter(d, 3)) & (d > 3)
    w = 2 * d[ridge]
    print(f"{ch}  light(p10) {np.percentile(w, 10):6.1f}  p25 {np.percentile(w, 25):6.1f}  median {np.median(w):6.1f}  heavy(p90) {np.percentile(w, 90):6.1f}")
