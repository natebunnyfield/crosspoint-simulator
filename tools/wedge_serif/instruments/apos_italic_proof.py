#!/usr/bin/env python3
"""ONE compact image of the italic straight ' arms (2026-09-26): italic words
with ' at 54 px, unhinted FreeType + HarfBuzz, today on top, each arm
labeled, and the curly ’ row (round 403) for comparison.

    uv run --python 3.13 --with uharfbuzz --with freetype-py --with shapely \\
        --with fonttools --with pillow --with numpy \\
        python instruments/apos_italic_proof.py OUT.png today.ttf b.ttf c.ttf d.ttf e.ttf
    or, labeled:  ... OUT.png "a  today=today.ttf" "b  pen wedge=b.ttf" ...
"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from apos_slider_frames import set_block

WORDS = "don't it's I'm they're o'clock"
LAB = ["a  today (parallel)", "b  pen wedge", "c  short wedge", "d  teardrop", "e  reference median"]
UI = "/System/Library/Fonts/Supplemental/Arial.ttf"


def main():
    out, fonts = sys.argv[1], sys.argv[2:]
    specs = [a.rsplit("=", 1) if "=" in a else (LAB[i], a) for i, a in enumerate(fonts)]
    rows = [(lab, set_block(p, WORDS, 54, 700)) for lab, p in specs]
    rows.append(("curly ’ (round 403)", set_block(specs[0][1], WORDS.replace("'", "’"), 54, 700)))
    LW = max(190, 20 + max(int(ImageFont.truetype(UI, 17).getlength(l)) for l, _ in rows)); h = rows[0][1].shape[0]
    im = Image.new("RGB", (LW + 700, h * len(rows)), "white"); d = ImageDraw.Draw(im)
    f = ImageFont.truetype(UI, 17)
    for i, (lab, cov) in enumerate(rows):
        g = Image.fromarray((255 - cov * 255).clip(0, 255).astype(np.uint8)).convert("RGB")
        im.paste(g, (LW, i * h)); d.text((8, i * h + h // 2), lab, font=f, fill=(40, 40, 40), anchor="lm")
        if i: d.line([(0, i * h), (im.width, i * h)], fill=(225, 222, 215))
    im.save(out, optimize=True); print(out, im.size)


if __name__ == "__main__":
    main()
