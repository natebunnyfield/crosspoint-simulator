#!/usr/bin/env python3
"""a_arms.py -- the ROMAN a's top-stroke ARMS (stems.py ALBO_ROM_A_RISE / _LIFT / _BOWL_TOP) as proof
pictures; the italic x's x_arms.py with the letter, the cuts and the references swapped.
docs/albo-roman-a-top-2026-10-02.md quotes every number from here and from a_roman_top.py.

  proof OUT LABEL=DIR ...   PNGs at native pixels, from each build's Albo-Regular.ttf and
                            Albo-Bold.ttf:
                              lead.png         the compact options image: one row per arm, today
                                               first -- the Regular and Bold a at one 150 px
                                               x-height, then "and that was" at 10 pt on the X3
                                               (150 dpi), 4x NEAREST
                              glyphs_<cut>.png every arm's a and the references at one x-height
                              words_<cut>.png  the corpus line at 10 pt on the X3, 5x NEAREST
                              words2x_<cut>.png the phone's 2x tier, 3x NEAREST
                              pairs_<cut>.png  "an at ha ra" at 100 pt, 1x

    $VENV/bin/python instruments/a_arms.py proof OUT today=$T T1=$A1 T2=$A2 ...

The line is built from the owner's own 41 books: the commonest a-words (a 18,342, and 16,113,
that 4,953, as 3,815, what 2,938, are 2,499, at 2,423, was 2,336, an 2,159, than, have, has, all)
and the commonest a pairs (an 47,165, at 31,913, ar 30,265, ha 24,717, al 22,369, ra 19,652).
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.dirname(HERE)
CUTS = ("Regular", "Bold")
CHAR = "a"
LINE = "And that was all a man can have: what he has at last, after all the years."


def cmd_proof(out, arms):
    import numpy as np, freetype
    from PIL import Image, ImageDraw, ImageFont
    sys.path.insert(0, os.path.join(WS, "fit_audit")); sys.path.insert(0, HERE)
    from legib import Renderer
    import poor_proof as P
    os.makedirs(out, exist_ok=True)
    arms = [a.split("=", 1) for a in arms]
    SUP = "/System/Library/Fonts/Supplemental/"; RF = os.path.join(WS, "refs") + "/"
    PG = os.path.expanduser("~/Library/Fonts/")
    DL = os.path.expanduser("~/Downloads/")
    REFS = {
        "Regular": [("Georgia", SUP + "Georgia.ttf", 0), ("Charter", SUP + "Charter.ttc", 0),
                    ("Palatino", "/System/Library/Fonts/Palatino.ttc", 0), ("Hoefler", SUP + "Hoefler Text.ttc", 0),
                    ("Baskerville", SUP + "Baskerville.ttc", 0), ("Albertus", DL + "Albertus Medium Regular.ttf", 0)],
        "Bold": [("Georgia B", SUP + "Georgia Bold.ttf", 0), ("Charter B", SUP + "Charter.ttc", 3),
                 ("Palatino B", "/System/Library/Fonts/Palatino.ttc", 2), ("Pagella B", PG + "texgyrepagella-bold.otf", 0)],
    }
    PAPER = tuple(int(v) for v in P.PAPER); INK = (20, 20, 20)
    LAB = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 22)

    def cell(path, idx, label, XH=150, W=270):
        f = freetype.Face(path, idx)
        f.set_char_size(f.units_per_EM * 64, 0, 72, 72)
        # scaled on the o's top, not the x's: Albo's roman x carries ~22 units of wedge over the line
        f.load_char("o", freetype.FT_LOAD_NO_SCALE | freetype.FT_LOAD_NO_HINTING)
        f.set_char_size(int(round(XH * f.units_per_EM / f.glyph.outline.get_bbox().yMax * 64)), 0, 72, 72)
        f.load_char(CHAR, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING)
        b = f.glyph.bitmap
        a = np.array(b.buffer, np.uint8).reshape(b.rows, b.pitch)[:, :b.width] if b.rows else np.zeros((1, 1), np.uint8)
        H = int(XH * 1.75) + 30; base = int(XH * 1.45) + 10
        cl = np.full((H, W, 3), PAPER, np.uint8); cl[base, :] = (175, 175, 175); cl[base - XH, :] = (210, 210, 210)
        x0, y0 = (W - a.shape[1]) // 2, base - f.glyph.bitmap_top; h, w = a.shape
        ys, xs = slice(max(0, y0), min(H, y0 + h)), slice(max(0, x0), min(W, x0 + w))
        sub = a[ys.start - y0:ys.stop - y0, xs.start - x0:xs.stop - x0].astype(float)[..., None] / 255.0
        cl[ys, xs] = (cl[ys, xs] * (1 - sub) + np.array(INK) * sub).astype(np.uint8)
        im = Image.fromarray(cl)
        if label: ImageDraw.Draw(im).text((8, 6), label, fill=(0, 0, 0), font=LAB)
        return np.array(im)

    def hcat(cs, gap=6):
        H = max(c.shape[0] for c in cs); parts = []
        for c in cs:
            parts += [np.concatenate([c, np.full((H - c.shape[0], c.shape[1], 3), PAPER, np.uint8)], 0),
                      np.full((H, gap, 3), 255, np.uint8)]
        return np.concatenate(parts[:-1], 1)

    def vcat(blocks, sep_h=16):
        W = max(b.shape[1] for b in blocks)
        padded = [np.concatenate([b, np.full((b.shape[0], W - b.shape[1], 3), PAPER, np.uint8)], 1) for b in blocks]
        out_ = [padded[0]]
        for p in padded[1:]: out_ += [np.full((sep_h, W, 3), 255, np.uint8), p]
        return np.concatenate(out_, 0)

    def text_img(path, line, pt, mag, tier=1):
        ppem = 150 / 72 * pt * tier
        R = Renderer(path, 0, ppem)
        c = np.zeros((int(ppem * 1.75), int(ppem * 40)), np.uint8); R.line(line, c, 4, int(ppem * 1.28))
        c = c[:, :np.nonzero(c.any(0))[0][-1] + 4]
        return P.rgb(np.kron(c, np.ones((mag, mag), np.uint8)))

    def label_col(text, h, w=120):
        li = Image.new("RGB", (w, h), PAPER)
        ImageDraw.Draw(li).text((12, h // 2 - 14), text, fill=(30, 30, 30), font=ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 28))
        return np.array(li)

    def rows(cut, line, pt, mag, tier=1):
        rs = []
        for lab, d in arms:
            img = text_img(os.path.join(d, f"Albo-{cut}.ttf"), line, pt, mag, tier)
            rs.append(np.concatenate([label_col(lab, img.shape[0]), img], 1))
        return vcat(rs, 8)

    # the lead image: one row per arm, today first
    lead = []
    for lab, d in arms:
        gi = cell(os.path.join(d, "Albo-Regular.ttf"), 0, None)
        gz = cell(os.path.join(d, "Albo-Bold.ttf"), 0, None)
        words = text_img(os.path.join(d, "Albo-Regular.ttf"), "and that was", 10, 4)
        pad = np.full((gi.shape[0], words.shape[1], 3), PAPER, np.uint8)
        y = (gi.shape[0] - words.shape[0]) // 2; pad[y:y + words.shape[0]] = words
        lead.append(hcat([label_col(lab, gi.shape[0]), gi, gz, pad]))
        widths_ = [120, gi.shape[1], gz.shape[1], pad.shape[1]]
    hd = Image.new("RGB", (sum(widths_) + 6 * 3, 40), PAPER); dh = ImageDraw.Draw(hd); x_ = 0
    for w_, t_ in zip(widths_, ["", "Regular", "Bold", "Regular, 10 pt on the X3, 4x"]):
        dh.text((x_ + 10, 8), t_, fill=(30, 30, 30), font=LAB); x_ += w_ + 6
    Image.fromarray(vcat([np.array(hd)] + lead, 6)).save(os.path.join(out, "lead.png"))
    for cut in CUTS:
        cs = [cell(os.path.join(d, f"Albo-{cut}.ttf"), 0, f"Albo {lab}") for lab, d in arms]
        cs += [cell(p, i, lab) for lab, p, i in REFS[cut] if os.path.exists(p)]
        half = (len(cs) + 1) // 2
        Image.fromarray(vcat([hcat(cs[:half]), hcat(cs[half:])], 6)).save(os.path.join(out, f"glyphs_{cut}.png"))
        Image.fromarray(rows(cut, LINE, 10, 5)).save(os.path.join(out, f"words_{cut}.png"))
        Image.fromarray(rows(cut, "and that was what an area", 10, 3, tier=2)).save(os.path.join(out, f"words2x_{cut}.png"))
        # the commonest a pairs in his books, large: 100 pt through the same renderer
        Image.fromarray(rows(cut, "an at ha ra", 100, 1)).save(os.path.join(out, f"pairs_{cut}.png"))
    for fn in sorted(os.listdir(out)):
        if fn.endswith(".png"): print(os.path.join(out, fn))


if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] != "proof":
        print(__doc__); sys.exit(2)
    cmd_proof(sys.argv[2], sys.argv[3:])
