"""Rasterize a glyph (as in the TTF, NOT unsheared) at `ppu` px per unit over a
units window, nearest-neighbour exact: each pixel is ink if its centre is in the
outline. usage: crop.py TTF CH x0 y0 x1 y1 ppu out.png"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
import numpy as np
import shapely


def render(g, x0, y0, x1, y1, ppu):
    W = int(round((x1 - x0) * ppu)); H = int(round((y1 - y0) * ppu))
    xs = x0 + (np.arange(W) + 0.5) / ppu
    ys = y1 - (np.arange(H) + 0.5) / ppu
    X, Y = np.meshgrid(xs, ys)
    inside = shapely.contains_xy(g, X.ravel(), Y.ravel()).reshape(H, W)
    return Image.fromarray(np.where(inside, 0, 255).astype('uint8'))


if __name__ == '__main__':
    from yenq_probe import glyph_poly
    ttf, ch = sys.argv[1], sys.argv[2]
    x0, y0, x1, y1 = (float(v) for v in sys.argv[3:7]); ppu = float(sys.argv[7]); out = sys.argv[8]
    g, _ = glyph_poly(ttf, ch, unshear=False)
    render(g, x0, y0, x1, y1, ppu).save(out)
