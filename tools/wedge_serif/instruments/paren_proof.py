#!/usr/bin/env python3
"""paren_proof.py -- the italic parens' height arms as proof pictures
(docs/albo-italic-parens-2026-10-02.md).

    $VENV/bin/python instruments/paren_proof.py OUT LABEL=DIR ...     (DIR holds Albo-Italic.ttf, Albo-BoldItalic.ttf)

  words.png   an italic line with parens at 40 pt through the reader's renderer, 1x, one row per arm
  read.png    the line at 10 pt on the X3 (150 dpi), 4x NEAREST -- Italic
  read_z.png  the same, Bold Italic
  phone.png   the Italic line at the phone's 2x tier, 2x NEAREST
  sheet.png   "(hold up)" at one x-height (90 px) with the ascender, x-height, baseline and
              descender lines, every arm, two by two
  refs.png    the same at 60 px in eight reference italics
"""
import os, sys
import numpy as np, freetype
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); WS = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(WS, "fit_audit")); sys.path.insert(0, HERE)
from legib import Renderer
import poor_proof as P
from paren_height import REFS_I, box
from bold_s_proof import lab, stack, hcat
PAPER = tuple(int(v) for v in P.PAPER); LAB = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 22)
LINE = "She left (quietly, by the gate) before the dog woke."
WORD = "(hold up)"


def text_img(path, line, pt, mag, tier=1):
    ppem = 150 / 72 * pt * tier; R = Renderer(path, 0, ppem)
    c = np.zeros((int(ppem * 1.7), int(ppem * 40)), np.uint8); R.line(line, c, 4, int(ppem * 1.25))
    c = c[:, :np.nonzero(c.any(0))[0][-1] + 4]
    return P.rgb(np.kron(c, np.ones((mag, mag), np.uint8)))


def cell(path, idx, label, XHPX=90):
    f = freetype.Face(path, idx); xh = box(f, "x")[1]; asc = box(f, "l")[1]; desc = box(f, "p")[0]
    k = XHPX / xh; f.set_char_size(int(round(f.units_per_EM * k * 64)), 0, 72, 72)
    gl = []
    for ch in WORD:
        f.load_char(ch, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING); b = f.glyph.bitmap
        a = np.array(b.buffer, np.uint8).reshape(b.rows, b.pitch)[:, :b.width].copy()
        gl.append((a, f.glyph.bitmap_left, f.glyph.bitmap_top, f.glyph.advance.x / 64))
    W = int(30 + sum(g[3] for g in gl) + 30); base = int(XHPX * 2.55); H = int(base + XHPX * 1.15)
    im = Image.new("L", (W, H), 250); d = ImageDraw.Draw(im)
    for y, col in ((base, 170), (base - XHPX, 205), (base - asc * k, 150), (base - desc * k, 150)):
        d.line([(0, int(round(y))), (W, int(round(y)))], fill=col)
    x = 30.0
    for a, l, t, adv in gl:
        im.paste(Image.fromarray(255 - a), (int(round(x)) + l, base - t), Image.fromarray(a)); x += adv
    d.text((8, 6), label, fill=0, font=LAB)
    return np.array(im.convert("RGB"))


if __name__ == "__main__":
    out = sys.argv[1]; arms = [a.split("=", 1) for a in sys.argv[2:]]; os.makedirs(out, exist_ok=True)
    def rows_of(cut, line, pt, mag, tier=1):
        rs = []
        for l, d in arms:
            img = text_img(os.path.join(d, f"Albo-{cut}.ttf"), line, pt, mag, tier); rs.append(np.concatenate([lab(l, img.shape[0]), img], 1))
        return stack(rs)
    Image.fromarray(rows_of("Italic", "before the lights (and the dog) woke", 40, 1)).save(os.path.join(out, "words.png"))
    Image.fromarray(rows_of("Italic", LINE, 10, 4)).save(os.path.join(out, "read.png"))
    Image.fromarray(rows_of("BoldItalic", LINE, 10, 4)).save(os.path.join(out, "read_z.png"))
    Image.fromarray(rows_of("Italic", LINE, 10, 2, 2)).save(os.path.join(out, "phone.png"))
    albo = [cell(os.path.join(d, "Albo-Italic.ttf"), 0, f"Albo {l}") for l, d in arms]
    refs = [cell(p, i, l, 60) for l, p, i in REFS_I if os.path.exists(p)]
    Image.fromarray(stack([hcat(albo[i:i + 2]) for i in range(0, len(albo), 2)])).save(os.path.join(out, "sheet.png"))
    Image.fromarray(stack([hcat(refs[:4]), hcat(refs[4:])])).save(os.path.join(out, "refs.png"))
    for f in sorted(os.listdir(out)):
        if f.endswith(".png"): print(f, Image.open(os.path.join(out, f)).size)
