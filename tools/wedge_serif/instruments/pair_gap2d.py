"""pair_gap2d.py -- the CLOSEST APPROACH between two shaped glyphs, in font units, plus the mean
row white over 0.15-0.85 xh (pair_white.py's measure), for a list of pairs, several fonts side by side.

    venv/bin/python instruments/pair_gap2d.py "rn ra re ro" A.ttf B.ttf ...

HarfBuzz-shaped (kern on), unhinted at 1000 ppem (1 px = 1 unit). The closest approach is the
minimum Euclidean distance from any ink pixel of the first glyph to any of the second (a distance
transform of the second's complement read under the first's ink): the diagonal gap the eye sees
between a terminal and the next letter's head, which a row-based white cannot see. Written
2026-09-28 for the r's drawn arm (docs/albo-issue-sweep-2026-09-28.md).
"""
import sys, numpy as np, freetype, uharfbuzz as hb
from scipy import ndimage as ndi
pairs = sys.argv[1].split(); fonts = sys.argv[2:]
XH = 429


def measure(path, pair):
    face = freetype.Face(path); face.set_pixel_sizes(0, 1000)
    blob = hb.Blob.from_file_path(path); hf = hb.Face(blob); font = hb.Font(hf); upm = hf.upem
    buf = hb.Buffer(); buf.add_str(pair); buf.guess_segment_properties(); hb.shape(font, buf, {"kern": True})
    x = 0; masks = []
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        face.load_glyph(info.codepoint, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING); b = face.glyph.bitmap
        a = np.array(b.buffer, np.uint8).reshape(b.rows, b.pitch)[:, :b.width] > 127
        masks.append((a, int(round(x + pos.x_offset * 1000 / upm)) + face.glyph.bitmap_left, face.glyph.bitmap_top))
        x += pos.x_advance * 1000 / upm
    W = int(x) + 800; top = 1100; H = 1700
    canv = []
    for a, l, t in masks:
        c = np.zeros((H, W), bool); y0 = top - t; x0 = l + 300
        c[y0:y0 + a.shape[0], x0:x0 + a.shape[1]] |= a
        canv.append(c)
    d = ndi.distance_transform_edt(~canv[1])
    gap = float(d[canv[0]].min()) if canv[0].any() else float('nan')
    rows = []
    for yy in range(H):
        y = top - yy
        if not (0.15 * XH <= y <= 0.85 * XH): continue
        a0 = np.nonzero(canv[0][yy])[0]; a1 = np.nonzero(canv[1][yy])[0]
        if len(a0) and len(a1): rows.append(a1.min() - a0.max())
    return gap, (np.mean(rows) if rows else float('nan'))


print(f"{'pair':6s}" + "".join(f"{f.split('/')[-2][-10:] + '/' + f.split('/')[-1][5:-4]:>26s}" for f in fonts))
for p in pairs:
    cells = []
    for f in fonts:
        g, w = measure(f, p); cells.append(f"{g:7.1f} / {w:6.1f}".rjust(26))
    print(f"{p:6s}" + "".join(cells))
