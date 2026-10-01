"""acc_sheet.py -- accented letters in fixed cells, one row per font, at one x-height: the marks'
size, gap and centring compared at a glance, with each letter's base drawn faint behind it.
Round 450 (2026-09-30).

    venv/bin/python instruments/acc_sheet.py OUT.png XHPX "CHARS" "LABEL::font.ttf" ...

Each glyph sits at its own origin in a cell as wide as the widest advance in the row set, so a
mark that drifts right or left of its letter shows as drift inside the cell. Unhinted, AA gray,
FreeType -- the rasteriser the reader's font converter uses, so a glyph whose left sidebearing
disagrees with its ink is drawn where the device draws it.
"""
import sys, freetype, numpy as np, unicodedata
from PIL import Image, ImageDraw, ImageFont

out, XH, chars = sys.argv[1], int(sys.argv[2]), sys.argv[3]
specs = [s.split("::") for s in sys.argv[4:]]
LAB = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", int(XH * 0.32))

def face(path):
    f = freetype.Face(path); f.set_pixel_sizes(0, 200); f.load_char('x', freetype.FT_LOAD_NO_HINTING)
    xh = f.glyph.metrics.height / 64
    f.set_pixel_sizes(0, int(round(200 * XH / xh))); return f

def glyph(f, ch):
    f.load_char(ch, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING); g = f.glyph; b = g.bitmap
    a = np.array(b.buffer, np.uint8).reshape(b.rows, b.pitch)[:, :b.width] if b.rows else np.zeros((0, 0), np.uint8)
    return a, g.bitmap_left, g.bitmap_top, g.advance.x / 64

faces = [(lab, face(p)) for lab, p in specs]
cw = int(max(glyph(f, ch)[3] for _, f in faces for ch in chars) * 1.25) + 8
LW = int(XH * 1.7); H = int(XH * 3.4); base = int(XH * 2.45)
rows = []
for lab, f in faces:
    im = Image.new("L", (LW + cw * len(chars), H), 250); d = ImageDraw.Draw(im)
    for y in (base, base - XH): d.line([(LW, y), (im.width, y)], fill=215)
    d.text((8, base - int(XH * 0.8)), lab, fill=40, font=LAB)
    for i, ch in enumerate(chars):
        x0 = LW + i * cw + (cw - glyph(f, ch)[3]) / 2
        b = unicodedata.normalize("NFD", ch)[0]
        b = 'ı' if b == 'i' else b
        if b != ch:
            a, l, t, _ = glyph(f, b)
            if a.size:
                ghost = (a.astype(np.float32) * 0.18).astype(np.uint8)
                im.paste(Image.fromarray(255 - ghost), (int(round(x0)) + l, base - t), Image.fromarray(ghost))
        a, l, t, _ = glyph(f, ch)
        if a.size:
            im.paste(Image.fromarray(255 - a), (int(round(x0)) + l, base - t), Image.fromarray(a))
        if i: d.line([(LW + i * cw, base - int(XH * 2.2)), (LW + i * cw, base + int(XH * 0.7))], fill=232)
    rows.append(im)
W = max(r.width for r in rows); o = Image.new("L", (W, sum(r.height for r in rows)), 250); y = 0
for r in rows: o.paste(r, (0, y)); y += r.height
o.save(out); print(out, o.size)
