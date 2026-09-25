"""Proof PNGs for the yen-gap and quote-symmetry options. Lossless, native px.
Writes into SP/proof/."""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from yenq_probe import glyph_poly, SP, SHEAR, CAP
from yenq_crop import render
from yenq_islands import islands
from shapely.ops import nearest_points
import shapely.geometry as sg

OUT = f'{SP}/proof'; os.makedirs(OUT, exist_ok=True)
DIRS = [('a', 'head'), ('b', 'opt_b'), ('c', 'opt_c'), ('d', 'opt_d'), ('e', 'opt_e')]
CUTS = ['Regular', 'Italic', 'Bold', 'BoldItalic']
LAB = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 13)


def font(d, cut, px):
    return ImageFont.truetype(f'{SP}/{d}/Albo-{cut}.ttf', px, layout_engine=ImageFont.Layout.RAQM)


def grid(text, out, em=110, cellw=165, rowh=None, names=None):
    rowh = rowh or int(em * 1.25)
    W = 30 + cellw * 4; H = 22 + rowh * len(DIRS)
    im = Image.new('L', (W, H), 255); dr = ImageDraw.Draw(im)
    for j, c in enumerate(CUTS):
        dr.text((30 + j * cellw + 4, 4), c, font=LAB, fill=90)
    for i, (o, d) in enumerate(DIRS):
        y = 22 + i * rowh
        dr.text((8, y + rowh // 2 - 8), o, font=LAB, fill=90)
        dr.line([(0, y), (W, y)], fill=215)
        for j, c in enumerate(CUTS):
            f = font(d, c, em)
            dr.text((30 + j * cellw + 10, y + int(em * 0.10)), text, font=f, fill=0)
    assert W <= 700, W
    im.save(f'{OUT}/{out}')
    return f'{OUT}/{out}'


def lines(texts, out, px=20, mag=2, cuts=CUTS):
    """each option x cut: the line at px, then magnified mag x nearest."""
    rows = []
    for o, d in DIRS:
        for c in cuts:
            for t in texts:
                f = font(d, c, px)
                w = int(f.getlength(t)) + 12
                im = Image.new('L', (w, int(px * 1.6)), 255)
                ImageDraw.Draw(im).text((6, int(px * 0.2)), t, font=f, fill=0)
                rows.append((f'{o} {c}', im.resize((im.width * mag, im.height * mag), Image.NEAREST)))
    W = min(700, 110 + max(r.width for _, r in rows)); H = sum(r.height for _, r in rows)
    canvas = Image.new('L', (W, H), 255); dr = ImageDraw.Draw(canvas); y = 0
    for lab, r in rows:
        dr.text((4, y + r.height // 2 - 8), lab, font=LAB, fill=90)
        canvas.paste(r, (110, y)); y += r.height
    assert W <= 700, W
    canvas.save(f'{OUT}/{out}')
    return f'{OUT}/{out}'


def gap_centre(ttf, ch):
    """The Y's gap (or the yen's trunk/arm white) in TTF coordinates."""
    g, _ = glyph_poly(ttf, ch)          # unsheared
    isl = islands(g)
    if len(isl) >= 2:
        # the pair of islands that are nearest AND whose white sits highest near the arm root
        best = None
        for i in range(len(isl)):
            for j in range(i + 1, len(isl)):
                d = isl[i].distance(isl[j])
                if d < 30:
                    pa, pb = nearest_points(isl[i], isl[j]); y = (pa.y + pb.y) / 2
                    if 0.36 * CAP < y < 0.46 * CAP and (best is None or d < best[0]):
                        best = (d, (pa.x + pb.x) / 2, y)
        if best:
            x, y = best[1], best[2]
            return x + SHEAR * y if 'Italic' in ttf else x, y
    return None


def foot_dx(ttf_y, ttf_yen):
    gy, _ = glyph_poly(ttf_y, 'Y', unshear=False); gv, _ = glyph_poly(ttf_yen, '¥', unshear=False)
    band = sg.box(-1000, -5, 3000, 40)
    return gv.intersection(band).bounds[0] - gy.intersection(band).bounds[0]


def gap_crops(cut, out, half=27, ppu=6, below=35, above=35):
    rows = []
    for o, d in DIRS[1:]:
        ty, tv = f'{SP}/{d}/Albo-{cut}.ttf', f'{SP}/{d}/Albo-{cut}.ttf'
        cy = gap_centre(ty, 'Y')
        # the yen's arm root sits where the Y's does, shifted by the glyph's own fit
        dx = foot_dx(ty, tv)
        cv = gap_centre(tv, '¥') or (cy[0] + dx, cy[1])
        gY, _ = glyph_poly(ty, 'Y', unshear=False); gV, _ = glyph_poly(tv, '¥', unshear=False)
        a = render(gY, cy[0] - half + 12, cy[1] - below, cy[0] + half + 12, cy[1] + above, ppu)
        b = render(gV, cv[0] - half + 12, cv[1] - below, cv[0] + half + 12, cv[1] + above, ppu)
        rows.append((o, a, b))
    S = rows[0][1].width; T = rows[0][1].height; W = 24 + 2 * S + 12; H = 20 + len(rows) * (T + 10)
    im = Image.new('L', (W, H), 255); dr = ImageDraw.Draw(im)
    dr.text((24, 3), f'{cut} Y (its own gap)', font=LAB, fill=90)
    dr.text((24 + S + 12, 3), f'{cut} ¥', font=LAB, fill=90)
    for i, (o, a, b) in enumerate(rows):
        y = 20 + i * (T + 10)
        dr.text((6, y + T // 2 - 8), o, font=LAB, fill=90)
        im.paste(a, (24, y)); im.paste(b, (24 + S + 12, y))
    assert W <= 700, W
    im.save(f'{OUT}/{out}')
    return f'{OUT}/{out}'


if __name__ == '__main__':
    what = sys.argv[1:] or ['yen', 'quotes', 'crops']
    if 'yen' in what:
        print(grid('¥', 'yen-grid.png'))
        print(lines(['Price ¥1,200 · ¥Y'], 'yen-text-2x.png', cuts=['Italic', 'BoldItalic']))
        print(lines(['Price ¥1,200 · ¥Y'], 'yen-text-roman-2x.png', cuts=['Regular', 'Bold']))
    if 'quotes' in what:
        print(grid('\'"', 'quotes-straight-grid.png'))
        print(grid('‘’“”', 'quotes-curly-grid.png', em=84, rowh=110))
        print(lines(['It’s ‘single’ and “double.”'], 'quotes-curly-text-2x.png'))
        print(lines(['it\'s \'single\' and "double"'], 'quotes-straight-text-2x.png'))
    if 'crops' in what:
        print(gap_crops('Italic', 'yen-gap-crop-italic-6x.png'))
        print(gap_crops('BoldItalic', 'yen-gap-crop-bolditalic-6x.png'))
