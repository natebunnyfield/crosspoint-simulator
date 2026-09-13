"""Render a TTF at a size with baseline and x-height rules: the LOOK step.
    python3 -m outlines.cmp.look <ttf> <text> <px_em> <out.png> [ref.ttf ...]"""
import sys, os
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont

def render_line(path, text, px, pad=24, rules=True):
    f = TTFont(path); upm = f['head'].unitsPerEm; xh = f['OS/2'].sxHeight * px / upm
    font = ImageFont.truetype(path, px); asc, desc = font.getmetrics()
    w = int(font.getlength(text)) + 2 * pad; h = asc + desc + 8
    im = Image.new('L', (w, h), 255); d = ImageDraw.Draw(im); base = asc + 4
    if rules:
        d.line([(0, base), (w, base)], fill=200); d.line([(0, base - xh), (w, base - xh)], fill=215)
    d.text((pad, base), text, font=font, fill=0, anchor='ls')
    return im

def stack(ims, gap=6):
    W = max(i.size[0] for i in ims); H = sum(i.size[1] for i in ims) + gap * (len(ims) - 1)
    out = Image.new('L', (W, H), 255); y = 0
    for i in ims: out.paste(i, (0, y)); y += i.size[1] + gap
    return out

if __name__ == '__main__':
    ttf, text, px, out = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
    ims = [render_line(ttf, text, px)]
    for r in sys.argv[5:]: ims.append(render_line(r, text, px))
    stack(ims).save(out); print(out)
