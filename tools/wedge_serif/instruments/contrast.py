"""Stroke contrast off the raster, with a two-pass chamfer instead of scipy.

The distance from an ink pixel to the nearest paper, doubled, is the local
stroke width. The ridge (the top of the distance map) carries the real widths;
its high over its low is the contrast. Same shape of measure round 195 used to
call the 8 nearly monolinear at 1.69:1.
"""
from PIL import Image, ImageDraw, ImageFont
import numpy as np

def chamfer(mask):
    INF = 1e9
    d = np.where(mask, INF, 0.0)
    h, w = d.shape
    for y in range(h):
        for x in range(w):
            if d[y, x] == 0: continue
            best = d[y, x]
            if y: best = min(best, d[y-1, x] + 1.0)
            if x: best = min(best, d[y, x-1] + 1.0)
            if y and x: best = min(best, d[y-1, x-1] + 1.41421)
            if y and x + 1 < w: best = min(best, d[y-1, x+1] + 1.41421)
            d[y, x] = best
    for y in range(h - 1, -1, -1):
        for x in range(w - 1, -1, -1):
            if d[y, x] == 0: continue
            best = d[y, x]
            if y + 1 < h: best = min(best, d[y+1, x] + 1.0)
            if x + 1 < w: best = min(best, d[y, x+1] + 1.0)
            if y + 1 < h and x + 1 < w: best = min(best, d[y+1, x+1] + 1.41421)
            if y + 1 < h and x: best = min(best, d[y+1, x-1] + 1.41421)
            d[y, x] = best
    return d

def raster(path, ch, px):
    f = ImageFont.truetype(path, px); asc, desc = f.getmetrics(); pad = 24
    im = Image.new("L", (int(f.getlength(ch)) + 2*pad, asc + desc + 2*pad), 255)
    ImageDraw.Draw(im).text((pad, pad + asc), ch, font=f, fill=0, anchor="ls")
    return np.array(im) < 128

def contrast(path, ch, px=220):
    m = raster(path, ch, px)
    d = chamfer(m)
    v = d[d > 0]
    if v.size == 0: return None
    ridge = v[v >= np.percentile(v, 80)]      # the stroke centres, not the edges
    lo, hi = 2*np.percentile(ridge, 5), 2*np.percentile(ridge, 95)
    return lo, hi, hi/lo

if __name__ == "__main__":
    import sys
    for arm in "abcdef":
        p = f"r305/{arm}/Albo-Regular.ttf"
        r8 = contrast(p, "8"); ro = contrast(p, "o"); r0 = contrast(p, "0")
        print(f"{arm}: 8 thin {r8[0]:5.1f} thick {r8[1]:5.1f} contrast {r8[2]:4.2f}"
              f"   | o {ro[2]:4.2f}   0 {r0[2]:4.2f}")
