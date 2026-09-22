"""One text line, rendered to a grayscale raster.

WHY IT IS HERE. `instruments/loopwall.py` and `instruments/gtrace.py` both
open with `from render import line`, and on 2026-09-21 neither could run: the
instruments were moved into the repo (so the numbers in the docs could be
re-derived) and this, their one dependency, was left in a session scratchpad
that no longer exists. That is the failure `instruments/README.md` was written
to prevent, one layer down. If you add an instrument, check what it imports.

    im, px = line(font_path, "g", px=600)     # im is 'L', ink dark on white
"""
from PIL import Image, ImageDraw, ImageFont


def line(path, text, px, pad=60):
    """Render `text` at `px` pixels per em. Returns (image, px)."""
    f = ImageFont.truetype(path, px)
    asc, desc = f.getmetrics()
    w = int(f.getlength(text)) + 2 * pad
    h = asc + desc + 2 * pad
    im = Image.new('L', (max(1, w), max(1, h)), 255)
    ImageDraw.Draw(im).text((pad, pad + asc), text, font=f, fill=0, anchor='ls')
    return im, px
