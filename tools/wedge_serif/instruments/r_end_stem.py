# The r's terminal thickness: the largest inscribed circle (distance transform) in the
# terminal region -- right of the stem's right edge + 0.45 of the letter's width, above
# 0.55 xh -- and the stem's (below 0.45 xh), both in units of THIS font's x-height x 1000.
import sys, numpy as np, freetype
from scipy import ndimage as ndi
from fontTools.ttLib import TTFont
def measure(path, ch='r'):
    f = TTFont(path); upm = f['head'].unitsPerEm
    face = freetype.Face(path); face.set_char_size(upm * 64)
    face.load_char('x', freetype.FT_LOAD_NO_HINTING); xh = face.glyph.metrics.height / 64
    face.load_char(ch, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING)
    b = face.glyph.bitmap; a = (np.array(b.buffer, np.uint8).reshape(b.rows, b.pitch)[:, :b.width] > 127)
    top = face.glyph.bitmap_top; H, W = a.shape
    Y = top - np.arange(H)[:, None]; X = np.arange(W)[None, :]
    dt = ndi.distance_transform_edt(a)
    term = (Y > 0.55 * xh) & (X > 0.55 * W)
    stem = (Y < 0.45 * xh) & (Y > 0.1 * xh) & (X >= 0)
    ft = 2 * dt[term].max(); st = 2 * dt[stem].max()
    return xh, ft, st
for p in sys.argv[1:]:
    xh, ft, st = measure(p)
    print(f"{p.split('/')[-2][-12:]+'/'+p.split('/')[-1][:24]:40} xh {xh:5.0f}  finial {ft:5.1f} ({1000*ft/xh:5.1f}/k xh)  stem {st:5.1f} ({1000*st/xh:5.1f}/k xh)  finial/stem {ft/st:.2f}")
