# rmatch.py -- the italic r against its OWN font's letters, measured the same way on Albo and on
# Coelacanth, so "match Coelacanth" is a set of numbers rather than a feeling:
#   term   the end's largest inscribed circle, per-mille of the font's x-height (fin_thick's measure)
#   hang   the end's lowest ink, as a fraction of the x-height (right quarter of the letter, above 0.4 xh)
#   r/n    the r's advance over the n's
#   cut    the r's p90/p10 ridge thickness (cmp_weight_survey's method, at the font's own slant)
#   col    the r's colour over the median colour of n a e o u (same method)
#   gap    closest approach after r over the same after n (r+X / n+X), and the mean row white
#          (0.15-0.85 xh) ratio, for X in a e o n i t -- shaped with kerning, 1000 ppem
# python rmatch.py SLANT FONT [SLANT FONT ...]
import sys, os, numpy as np, freetype, uharfbuzz as hb
from scipy import ndimage as ndi
from fontTools.ttLib import TTFont
sys.path.insert(0, os.path.expanduser("~/src/crosspoint-simulator/tools/wedge_serif"))
import cmp_weight_survey as W

def xheight(path):
    f = freetype.Face(path); upm = TTFont(path)['head'].unitsPerEm; f.set_char_size(upm * 64)
    f.load_char('x', freetype.FT_LOAD_NO_HINTING); return f.glyph.metrics.height / 64, upm

def term(path):
    xh, upm = xheight(path)
    f = freetype.Face(path); f.set_char_size(upm * 64)
    f.load_char('r', freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING)
    b = f.glyph.bitmap; a = np.array(b.buffer, np.uint8).reshape(b.rows, b.pitch)[:, :b.width] > 127
    top = f.glyph.bitmap_top; H, Wd = a.shape
    Y = top - np.arange(H)[:, None]; X = np.arange(Wd)[None, :]
    dt = ndi.distance_transform_edt(a)
    ft = 2 * dt[(Y > 0.55 * xh) & (X > 0.55 * Wd)].max()
    rq = a & (X > 0.75 * Wd) & (Y > 0.4 * xh)
    hang = Y[rq.any(1)].min() / xh if rq.any() else float('nan')
    return 1000 * ft / xh, hang

def gap(path, pair, xh):
    face = freetype.Face(path); face.set_pixel_sizes(0, 1000)
    blob = hb.Blob.from_file_path(path); hf = hb.Face(blob); font = hb.Font(hf); upm = hf.upem
    s = 1000 / upm; XH = xh * s
    buf = hb.Buffer(); buf.add_str(pair); buf.guess_segment_properties(); hb.shape(font, buf, {"kern": True})
    x = 0; masks = []
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        face.load_glyph(info.codepoint, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING); b = face.glyph.bitmap
        a = np.array(b.buffer, np.uint8).reshape(b.rows, b.pitch)[:, :b.width] > 127
        masks.append((a, int(round(x + pos.x_offset * s)) + face.glyph.bitmap_left, face.glyph.bitmap_top))
        x += pos.x_advance * s
    Wc = int(x) + 800; top = 1100; H = 1700; canv = []
    for a, l, t in masks:
        c = np.zeros((H, Wc), bool); y0 = top - t; x0 = l + 300
        c[y0:y0 + a.shape[0], x0:x0 + a.shape[1]] |= a; canv.append(c)
    d = ndi.distance_transform_edt(~canv[1]); g = float(d[canv[0]].min())
    rows = []
    for yy in range(H):
        y = top - yy
        if not (0.15 * XH <= y <= 0.85 * XH): continue
        a0 = np.nonzero(canv[0][yy])[0]; a1 = np.nonzero(canv[1][yy])[0]
        if len(a0) and len(a1): rows.append(a1.min() - a0.max())
    return g / XH, (np.mean(rows) / XH if rows else float('nan'))

args = sys.argv[1:]
for sl, path in zip(args[0::2], args[1::2]):
    sl = float(sl); xh, upm = xheight(path)
    t, hang = term(path)
    tt = TTFont(path); cm = tt.getBestCmap(); hm = tt['hmtx']
    rn = hm[cm[ord('r')]][0] / hm[cm[ord('n')]][0]
    m = {c: W.measure(path, c, sl) for c in "rnaeou"}
    col = m['r']['colour'] / np.median([m[c]['colour'] for c in "naeou"])
    cut = m['r']['thick'] / m['r']['thin']
    gs = []
    for X in "aeonit":
        gr, wr = gap(path, "r" + X, xh); gn, wn = gap(path, "n" + X, xh)
        gs.append((X, gr / gn, wr / wn))
    name = path.split('/')[-2][-8:] + '/' + path.split('/')[-1].replace('Albo-', '').replace('.ttf', '').replace('.otf', '')[:18]
    print(f"{name:28s} term {t:4.0f} hang {hang:.2f} r/n {rn:.2f} cut {cut:.2f} col {col:.2f} | "
          + " ".join(f"{X}:{a:.2f}/{b:.2f}" for X, a, b in gs))
