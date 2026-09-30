"""cr_grid.py -- CHARS of each font at one x-height, a grid of labelled cells (round 448).

    python3 instruments/cr_grid.py OUT.png COLS XHPX cr "Coelacanth::refs/coelacanth-italic.otf" "Albo::Albo-Italic.ttf" ...

The picture that found the r's rule: laid c-beside-r, every reference ends its r with the same
terminal as the top of its c (Coelacanth, Pagella, Poetica, Flanker), and Albo's r did not.
An empty font ("LABEL::") leaves a blank cell. docs/albo-round-448-2026-09-30.md.
"""
import sys, freetype, numpy as np
from PIL import Image, ImageDraw, ImageFont
out, cols, XH, chars = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
items = [s.split("::") for s in sys.argv[5:]]
F = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", int(XH * 0.16))
cells = []
for lab, p in items:
    if not p:
        cells.append(None); continue
    f = freetype.Face(p); f.set_pixel_sizes(0, 200); f.load_char('x', freetype.FT_LOAD_NO_HINTING)
    xh = f.glyph.metrics.height / 64; f.set_pixel_sizes(0, int(round(200 * XH / xh)))
    gl = []
    for ch in chars:
        f.load_char(ch, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING); b = f.glyph.bitmap
        a = np.array(b.buffer, np.uint8).reshape(b.rows, b.pitch)[:, :b.width]
        gl.append((a, f.glyph.bitmap_left, f.glyph.bitmap_top, f.glyph.advance.x / 64))
    cells.append((lab, gl))
def cw(gl): 
    x = XH * 0.3
    for a, l, t, adv in gl: x += max(adv, a.shape[1] + l) + XH * 0.08
    return x
CW = int(max(cw(c[1]) for c in cells if c) + XH * 0.25); CH = int(XH * 1.75)
rows = (len(cells) + cols - 1) // cols
o = Image.new("L", (CW * cols, CH * rows), 250); d = ImageDraw.Draw(o)
for i, c in enumerate(cells):
    ox, oy = (i % cols) * CW, (i // cols) * CH
    if c is None: continue
    lab, gl = c
    base = oy + int(XH * 1.45)
    d.line([(ox, base), (ox + CW - 8, base)], fill=205); d.line([(ox, base - XH), (ox + CW - 8, base - XH)], fill=205)
    d.text((ox + 8, oy + 6), lab, fill=0, font=F)
    x = ox + int(XH * 0.3)
    for a, l, t, adv in gl:
        o.paste(Image.fromarray(255 - a), (int(x) + l, base - t), Image.fromarray(a)); x += max(adv, a.shape[1] + l) + XH * 0.08
    if i % cols: d.line([(ox, oy), (ox, oy + CH)], fill=225)
o.save(out); print(out, o.size)
