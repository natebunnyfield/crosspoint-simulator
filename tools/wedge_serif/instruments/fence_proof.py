#!/usr/bin/env python3
"""fence_proof.py -- the fence-span arms as proof pictures (docs/albo-fences-2026-10-03.md).

    $VENV/bin/python instruments/fence_proof.py OUT LABEL=DIR ...     (DIR holds the four Albo-*.ttf)

  sheet_r.png "(hp) [bq] {dj} |ly|" at a 70 px x-height with the ascender (tallest of b d h k l),
              x-height, baseline and descender (deepest of g j p q y) lines, one row per arm;
              sheet_i.png the same in the Italic
  words.png   a Regular and an Italic phrase with every fence at 32 pt, 1x
  read_r.png  a Regular line at 10 pt on the X3 (150 dpi), 4x NEAREST;  read_i.png the Italic
  phone.png   the Regular line at the phone's 2x tier, 2x NEAREST
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
LAB = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 22)
WORD = "(hp) [bq] {dj} |ly|"
LINE = "A ferry (slow, high) left [as planned] from the {quay}."


def text_img(path, line, pt, mag, tier=1):
    ppem = 150 / 72 * pt * tier; R = Renderer(path, 0, ppem); m = int(ppem * 0.8)
    c = np.zeros((int(ppem * 1.8), int(ppem * 44) + m), np.uint8); R.line(line, c, m, int(ppem * 1.3))
    cols = np.nonzero(c.any(0))[0]; c = c[:, max(0, cols[0] - 4):cols[-1] + 4]
    return P.rgb(np.kron(c, np.ones((mag, mag), np.uint8)))


def cell(path, label, XHPX=70):
    f = freetype.Face(path); xh = box(f, "x")[1]
    asc = max(box(f, ch)[1] for ch in "bdhkl"); desc = min(box(f, ch)[0] for ch in "gjpqy")
    k = XHPX / xh; f.set_char_size(int(round(f.units_per_EM * k * 64)), 0, 72, 72)
    gl = []
    for ch in WORD:
        f.load_char(ch, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING); b = f.glyph.bitmap
        a = np.array(b.buffer, np.uint8).reshape(b.rows, b.pitch)[:, :b.width].copy()
        gl.append((a, f.glyph.bitmap_left, f.glyph.bitmap_top, f.glyph.advance.x / 64))
    W = int(36 + sum(g[3] for g in gl) + 24); base = int(XHPX * 2.75); H = int(base + XHPX * 1.25)
    im = Image.new("L", (W, H), 250); d = ImageDraw.Draw(im)
    for y, col in ((base, 175), (base - XHPX, 210), (base - asc * k, 140), (base - desc * k, 140)):
        d.line([(0, int(round(y))), (W, int(round(y)))], fill=col)
    x = 36.0
    for a, l, t, adv in gl:
        if a.size: im.paste(Image.fromarray(255 - a), (int(round(x)) + l, base - t), Image.fromarray(a))
        x += adv
    d.text((6, 4), label, fill=0, font=LAB)
    return np.array(im.convert("RGB"))


if __name__ == "__main__":
    out = sys.argv[1]; arms = [a.split("=", 1) for a in sys.argv[2:]]; os.makedirs(out, exist_ok=True)
    def rows_of(cut, line, pt, mag, tier=1):
        rs = []
        for l, d in arms:
            img = text_img(os.path.join(d, f"Albo-{cut}.ttf"), line, pt, mag, tier); rs.append(np.concatenate([lab(l, img.shape[0]), img], 1))
        return stack(rs)
    for c, name in (("Regular", "sheet_r.png"), ("Italic", "sheet_i.png")):
        Image.fromarray(stack([cell(os.path.join(d, f"Albo-{c}.ttf"), f"{l} {c[0]}") for l, d in arms])).save(os.path.join(out, name))
    rs = []
    for l, d in arms:
        img = hcat([text_img(os.path.join(d, f"Albo-{c}.ttf"), "(high) [deep] {jump} |bold|", 32, 1) for c in ("Regular", "Italic")], gap=40)
        rs.append(np.concatenate([lab(l, img.shape[0]), img], 1))
    Image.fromarray(stack(rs)).save(os.path.join(out, "words.png"))
    Image.fromarray(rows_of("Regular", LINE, 10, 4)).save(os.path.join(out, "read_r.png"))
    Image.fromarray(rows_of("Italic", LINE, 10, 4)).save(os.path.join(out, "read_i.png"))
    Image.fromarray(rows_of("Regular", LINE, 10, 2, 2)).save(os.path.join(out, "phone.png"))
    for f in sorted(os.listdir(out)):
        if f.endswith(".png"): print(f, Image.open(os.path.join(out, f)).size)
