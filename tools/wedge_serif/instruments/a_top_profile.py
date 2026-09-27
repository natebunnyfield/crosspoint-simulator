"""Where is an italic a TALLEST, unsheared -- owner 2026-09-27: "make italic a
droopier from the left top being the tallest point and matching historical
references for handwritten and aldine a".

Each a is rasterised, unsheared by its OWN stem's slant (a line fitted to the
stem's left edge between 0.25 and 0.70 of the ink height), and its top contour
read column by column. Reported, in x-heights above the baseline and as a
fraction of the unsheared ink width from the left:
  crown   the bowl's highest point LEFT of the stem
  valley  the lowest point of the top contour between crown and stem (the join)
  stem    the stem's top
  left30  the top at 30% of the width -- how high the upper left rides
"""
import sys, numpy as np, freetype
from PIL import Image

def unshear(ink):
    h, w = ink.shape; ys, xs = [], []
    for y in range(int(h * 0.30), int(h * 0.75)):
        row = np.where(ink[y])[0]
        if len(row) == 0: continue
        runs = np.split(row, np.where(np.diff(row) > 1)[0] + 1)
        if len(runs) >= 2: ys.append(y); xs.append(runs[-1][0])   # the stem: the rightmost run's left edge
    k = np.polyfit(ys, xs, 1)[0] if len(ys) > 8 else 0.0
    sh = [-k * y for y in range(h)]; off = -min(sh)   # new x = x - k y: the stem's edge becomes one column
    out = np.zeros((h, w + int(abs(k) * h) + 4), bool)
    for y in range(h):
        d = int(round(sh[y] + off)); out[y, d:d + w] = ink[y]
    cols = np.where(out.any(0))[0]
    return out[:, cols[0]:cols[-1] + 1], k

def profile(ink, xh_px, base_row, straighten=True):
    if straighten:
        u, k = unshear(ink)
    else:
        cols = np.where(ink.any(0))[0]; u, k = ink[:, cols[0]:cols[-1] + 1], 0.0
    h, w = u.shape
    top = np.array([(base_row - np.where(u[:, x])[0][0]) / xh_px if u[:, x].any() else np.nan for x in range(w)])
    # the stem: the rightmost column block whose ink reaches below 0.3 xh
    # the stem: in the right half, the columns carrying the most vertical ink
    # between 0.25 and 0.75 xh (a bowl's side only crosses that band twice)
    y0, y1 = int(base_row - 0.75 * xh_px), int(base_row - 0.25 * xh_px)
    cov = u[max(0, y0):max(1, y1), :].mean(0); half = int(w * 0.5)
    right = cov[half:]; sc = np.where(right > 0.9 * right.max())[0]
    sx = half + int(sc[0])
    left = top[: sx]; ci = int(np.nanargmax(left)); crown = left[ci]
    seg = top[ci: sx + 1]; vi = ci + int(np.nanargmin(seg)); valley = top[vi]
    stem = np.nanmax(top[sx:])
    return dict(stem_x=sx / w, crown=crown, crown_x=ci / w, valley=valley, valley_x=vi / w, stem=stem, left30=top[int(w * 0.30)], slant=k, img=u)

def face_a(path, px=600):
    f = freetype.Face(path); f.set_pixel_sizes(0, px)
    def bm(ch):
        f.load_char(ch, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING); b = f.glyph.bitmap
        return np.array(b.buffer, np.uint8).reshape(b.rows, b.pitch)[:, :b.width] > 127, f.glyph.bitmap_top
    a, top = bm('a'); _, xt = bm('x')
    return profile(a, xt, top)

if __name__ == "__main__":
    for arg in sys.argv[1:]:
        name, path = arg.split("=", 1)
        d = face_a(path)
        print(f"{name:30s} crown {d['crown']:.3f} @ {d['crown_x']:.2f}   valley {d['valley']:.3f} @ {d['valley_x']:.2f}   "
              f"droop {d['crown'] - d['valley']:.3f}   stem {d['stem']:.3f}   left30 {d['left30']:.3f}")
