#!/usr/bin/env python3
"""spacing_arms.py -- italic SPACING arms as proof pictures: the same outlines, different tables.

    $VENV/bin/python instruments/spacing_arms.py OUT LABEL=DIR ...

Writes, at native pixels (the reader's own renderer, fit_audit/legib.Renderer: unhinted, 2-bit,
glyphs placed by HarfBuzz so every kern is in):
  lead.png          two lines of italic at 10 pt on the X3 (150 dpi), 4x NEAREST, one row per arm
  lead_bold.png     the same in the Bold Italic
  phone.png         the phone's 2x tier, 3x NEAREST, Italic
  pairs.png         the pairs the arms move most, at 72 pt, 1x
Written for docs/albo-round-463-2026-10-02.md (round 463's refit on the refreshed re-basing pair).
"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); WS = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(WS, "fit_audit")); sys.path.insert(0, HERE)
from legib import Renderer
import poor_proof as P

LINES = ["Each chapter can reach a quiet, careful rhythm across the page;",
         "characters rarely crowd, and every scene has a clear arc."]
PAIRS = "co ch ca ce ra re ri an al ay My"
PAPER = tuple(int(v) for v in P.PAPER)
LAB = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 26)


def text_img(path, line, pt, mag, tier=1):
    ppem = 150 / 72 * pt * tier
    R = Renderer(path, 0, ppem)
    c = np.zeros((int(ppem * 1.75), int(ppem * 42)), np.uint8); R.line(line, c, 4, int(ppem * 1.28))
    c = c[:, :np.nonzero(c.any(0))[0][-1] + 4]
    return P.rgb(np.kron(c, np.ones((mag, mag), np.uint8)))


def label_col(text, h, w=150):
    li = Image.new("RGB", (w, h), PAPER)
    ImageDraw.Draw(li).text((12, h // 2 - 15), text, fill=(30, 30, 30), font=LAB)
    return np.array(li)


def stack(blocks, gap=10):
    W = max(b.shape[1] for b in blocks)
    out = []
    for i, b in enumerate(blocks):
        out.append(np.concatenate([b, np.full((b.shape[0], W - b.shape[1], 3), PAPER, np.uint8)], 1))
        if i < len(blocks) - 1: out.append(np.full((gap, W, 3), 255, np.uint8))
    return np.concatenate(out, 0)


def rows(arms, fn, lines, pt, mag, tier=1):
    rs = []
    for lab, d in arms:
        segs = [text_img(os.path.join(d, fn), ln, pt, mag, tier) for ln in lines]
        body = stack(segs, 4)
        rs.append(np.concatenate([label_col(lab, body.shape[0]), body], 1))
    return stack(rs, 14)


if __name__ == "__main__":
    out = sys.argv[1]; arms = [a.split("=", 1) for a in sys.argv[2:]]
    os.makedirs(out, exist_ok=True)
    Image.fromarray(rows(arms, "Albo-Italic.ttf", LINES, 10, 4)).save(os.path.join(out, "lead.png"))
    Image.fromarray(rows(arms, "Albo-BoldItalic.ttf", LINES, 10, 4)).save(os.path.join(out, "lead_bold.png"))
    Image.fromarray(rows(arms, "Albo-Italic.ttf", LINES, 10, 3, tier=2)).save(os.path.join(out, "phone.png"))
    Image.fromarray(rows(arms, "Albo-Italic.ttf", [PAIRS], 72, 1)).save(os.path.join(out, "pairs.png"))
    for f in sorted(os.listdir(out)):
        if f.endswith(".png"): print(os.path.join(out, f), Image.open(os.path.join(out, f)).size)
