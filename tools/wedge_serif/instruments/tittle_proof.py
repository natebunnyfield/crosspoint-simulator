#!/usr/bin/env python3
"""tittle_proof.py -- the tittle arms as proof pictures (docs/albo-tittles-2026-10-02.md).

    $VENV/bin/python instruments/tittle_proof.py OUT LABEL=DIR ...     (DIR holds the four Albo-*.ttf)

  words.png   a Regular line full of i and j at 40 pt through the reader's renderer, 1x
  read_r.png  the Regular at 10 pt on the X3 (150 dpi), 4x NEAREST;  read_b.png the Bold;  read_i.png the Italic
  small_r.png "jilt in Fiji" at 8, 10 and 12 pt on the X3, 6x NEAREST -- where a dot can be lost;
              small_i.png the same in the Italic
  phone.png   the Regular at the phone's 2x tier, 2x NEAREST
  sheet.png   "ij" in the four cuts at a 120 px x-height, two arms to a row
"""
import os, sys
import numpy as np, freetype
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); WS = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(WS, "fit_audit")); sys.path.insert(0, HERE)
from legib import Renderer
import poor_proof as P
from bold_s_proof import lab, stack, hcat
from paren_height import box
PAPER = tuple(int(v) for v in P.PAPER); LAB = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 22)
LINE = "Jill insisted it is just inside, in plain sight, by the jib."


def text_img(path, line, pt, mag, tier=1):
    ppem = 150 / 72 * pt * tier; R = Renderer(path, 0, ppem)
    m = int(ppem * 0.8)   # the italic j's tail swings left of its origin; at x 4 the renderer dropped it
    c = np.zeros((int(ppem * 1.7), int(ppem * 40) + m), np.uint8); R.line(line, c, m, int(ppem * 1.25))
    cols = np.nonzero(c.any(0))[0]; c = c[:, max(0, cols[0] - 4):cols[-1] + 4]
    return P.rgb(np.kron(c, np.ones((mag, mag), np.uint8)))


def cell(path, label, XHPX=120):
    f = freetype.Face(path); xh = box(f, "x")[1]; k = XHPX / xh
    f.set_char_size(int(round(f.units_per_EM * k * 64)), 0, 72, 72)
    gl = []
    for ch in "ij":
        f.load_char(ch, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING); b = f.glyph.bitmap
        a = np.array(b.buffer, np.uint8).reshape(b.rows, b.pitch)[:, :b.width].copy()
        gl.append((a, f.glyph.bitmap_left, f.glyph.bitmap_top, f.glyph.advance.x / 64))
    W = int(24 + sum(g[3] for g in gl) + 24); base = int(XHPX * 2.0); H = int(base + XHPX * 0.75)
    im = Image.new("L", (W, H), 250); d = ImageDraw.Draw(im)
    d.line([(0, base), (W, base)], fill=180); d.line([(0, base - XHPX), (W, base - XHPX)], fill=205)
    x = 24.0
    for a, l, t, adv in gl:
        im.paste(Image.fromarray(255 - a), (int(round(x)) + l, base - t), Image.fromarray(a)); x += adv
    d.text((6, 4), label, fill=0, font=LAB)
    return np.array(im.convert("RGB"))


if __name__ == "__main__":
    out = sys.argv[1]; arms = [a.split("=", 1) for a in sys.argv[2:]]; os.makedirs(out, exist_ok=True)
    def rows_of(cut, line, pt, mag, tier=1):
        rs = []
        for l, d in arms:
            img = text_img(os.path.join(d, f"Albo-{cut}.ttf"), line, pt, mag, tier); rs.append(np.concatenate([lab(l, img.shape[0]), img], 1))
        return stack(rs)
    Image.fromarray(rows_of("Regular", "Jill insisted it is just inside", 40, 1)).save(os.path.join(out, "words.png"))
    Image.fromarray(rows_of("Regular", LINE, 10, 4)).save(os.path.join(out, "read_r.png"))
    Image.fromarray(rows_of("Bold", LINE, 10, 4)).save(os.path.join(out, "read_b.png"))
    Image.fromarray(rows_of("Italic", LINE, 10, 4)).save(os.path.join(out, "read_i.png"))
    Image.fromarray(rows_of("Regular", LINE, 10, 2, 2)).save(os.path.join(out, "phone.png"))
    for cut, name in (("Regular", "small_r.png"), ("Italic", "small_i.png")):
        rs = []
        for l, d in arms:
            parts = [text_img(os.path.join(d, f"Albo-{cut}.ttf"), "jilt in Fiji", pt, 6) for pt in (8, 10, 12)]
            img = hcat(parts, gap=24); rs.append(np.concatenate([lab(l, img.shape[0]), img], 1))
        Image.fromarray(stack(rs)).save(os.path.join(out, name))
    rows = [hcat([cell(os.path.join(d, f"Albo-{c}.ttf"), f"{l} {c[0] if c != 'BoldItalic' else 'Z'}") for c in ("Regular", "Italic", "Bold", "BoldItalic")]) for l, d in arms]
    Image.fromarray(stack([hcat(rows[i:i + 2], gap=28) for i in range(0, len(rows), 2)])).save(os.path.join(out, "sheet.png"))
    for f in sorted(os.listdir(out)):
        if f.endswith(".png"): print(f, Image.open(os.path.join(out, f)).size)
