#!/usr/bin/env python3
"""bold_s_proof.py -- the Bold S width arms, measured and drawn (docs/albo-bold-s-2026-10-02.md).

    $VENV/bin/python instruments/bold_s_proof.py --measure LABEL=DIR ...   (DIR holds Albo-Bold.ttf)
    $VENV/bin/python instruments/bold_s_proof.py OUT LABEL=DIR ...

  --measure   S against H, E and O by outline ink box (unhinted, font units), every arm and
              the bold references: S/H and S/E width, S/O height
  words.png   "Step  Sense  Sister  Says" at 60 pt through the reader's renderer, 1x, one row per arm
  read.png    a Bold line at 10 pt on the X3 (150 dpi), 4x NEAREST
  phone.png   the same line at the phone's 2x tier, 2x NEAREST
  sheet.png   H, O and S of each arm and each reference at one cap height (120 px), S/H in the label
"""
import os, sys
import numpy as np, freetype
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); WS = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(WS, "fit_audit")); sys.path.insert(0, HERE)
from legib import Renderer
import poor_proof as P
PAPER = tuple(int(v) for v in P.PAPER); LAB = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 22)
SUP = "/System/Library/Fonts/Supplemental/"
REFS = [("Georgia B", SUP + "Georgia Bold.ttf", 0), ("Charter B", SUP + "Charter.ttc", 3),
        ("Palatino B", "/System/Library/Fonts/Palatino.ttc", 2),
        ("Pagella B", os.path.expanduser("~/Library/Fonts/texgyrepagella-bold.otf"), 0),
        ("Times B", SUP + "Times New Roman Bold.ttf", 0), ("Baskerville B", SUP + "Baskerville.ttc", 1)]
LINE = "Step by Step: She Saw Seven Ships Sailing South."


def ink(path, idx, ch):
    f = freetype.Face(path, idx); f.load_char(ch, freetype.FT_LOAD_NO_SCALE | freetype.FT_LOAD_NO_HINTING)
    b = f.glyph.outline.get_bbox(); return b.xMax - b.xMin, b.yMax - b.yMin


def ratios(path, idx=0):
    (sw, sh), (hw, _), (ew, _), (_, oh) = (ink(path, idx, c) for c in "SHEO")
    return sw / hw, sw / ew, sh / oh


def text_img(path, line, pt, mag, tier=1):
    ppem = 150 / 72 * pt * tier; R = Renderer(path, 0, ppem)
    c = np.zeros((int(ppem * 1.6), int(ppem * 40)), np.uint8); R.line(line, c, 4, int(ppem * 1.2))
    c = c[:, :np.nonzero(c.any(0))[0][-1] + 4]
    return P.rgb(np.kron(c, np.ones((mag, mag), np.uint8)))


def lab(text, h, w=110):
    li = Image.new("RGB", (w, h), PAPER); ImageDraw.Draw(li).text((12, h // 2 - 12), text, fill=(30, 30, 30), font=LAB)
    return np.array(li)


def stack(bs, gap=12):
    W = max(b.shape[1] for b in bs); out = []
    for i, b in enumerate(bs):
        out.append(np.concatenate([b, np.full((b.shape[0], W - b.shape[1], 3), PAPER, np.uint8)], 1))
        if i < len(bs) - 1: out.append(np.full((gap, W, 3), 255, np.uint8))
    return np.concatenate(out, 0)


def hcat(cs, gap=10):
    Hh = max(c.shape[0] for c in cs); parts = []
    for c in cs: parts += [np.concatenate([c, np.full((Hh - c.shape[0], c.shape[1], 3), PAPER, np.uint8)], 0), np.full((Hh, gap, 3), 255, np.uint8)]
    return np.concatenate(parts[:-1], 1)


def cell(path, idx, label, CH=120):
    f = freetype.Face(path, idx); hh = ink(path, idx, "H")[1]
    f.set_char_size(int(round(CH * f.units_per_EM / hh * 64)), 0, 72, 72)
    glyphs = []
    for ch in "HOS":
        f.load_char(ch, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING); b = f.glyph.bitmap
        a = np.array(b.buffer, np.uint8).reshape(b.rows, b.pitch)[:, :b.width].copy()
        glyphs.append((a, f.glyph.bitmap_left, f.glyph.bitmap_top, f.glyph.advance.x // 64))
    W = 24 + sum(g[3] for g in glyphs) + 16; H = int(CH * 1.75); base = int(CH * 1.5)
    im = Image.new("L", (W, H), 250); d = ImageDraw.Draw(im)
    d.line([(0, base), (W, base)], fill=190); d.line([(0, base - CH), (W, base - CH)], fill=215)
    x = 24
    for a, l, t, adv in glyphs:
        im.paste(Image.fromarray(255 - a), (x + l, base - t), Image.fromarray(a)); x += adv
    d.text((8, 6), f"{label}   S/H {ratios(path, idx)[0]:.2f}", fill=0, font=LAB)
    return np.array(im.convert("RGB"))


if __name__ == "__main__":
    if sys.argv[1] == "--measure":
        rows = [(l, os.path.join(d, "Albo-Bold.ttf"), 0) for l, d in (a.split("=", 1) for a in sys.argv[2:])] + REFS
        print(f"{'':16s} {'S/H w':>6s} {'S/E w':>6s} {'S/O h':>6s}")
        for l, p, i in rows: print(f"{l:16s} " + " ".join(f"{v:6.3f}" for v in ratios(p, i)))
        r = np.array([ratios(p, i) for _, p, i in REFS])
        print(f"{'refs median':16s} " + " ".join(f"{v:6.3f}" for v in np.median(r, 0)))
        print(f"{'refs range':16s} " + "  ".join(f"{a:.2f}-{b:.2f}" for a, b in zip(r.min(0), r.max(0))))
        sys.exit(0)
    out = sys.argv[1]; arms = [a.split("=", 1) for a in sys.argv[2:]]; os.makedirs(out, exist_ok=True)
    fonts = [(l, os.path.join(d, "Albo-Bold.ttf")) for l, d in arms]
    def rows_of(line, pt, mag, tier=1):
        rs = []
        for l, p in fonts:
            img = text_img(p, line, pt, mag, tier); rs.append(np.concatenate([lab(l, img.shape[0]), img], 1))
        return stack(rs)
    Image.fromarray(rows_of("Step  Sense  Sister  Says", 60, 1)).save(os.path.join(out, "words.png"))
    Image.fromarray(rows_of(LINE, 10, 4)).save(os.path.join(out, "read.png"))
    Image.fromarray(rows_of(LINE, 10, 2, 2)).save(os.path.join(out, "phone.png"))
    albo = [cell(p, 0, f"Albo {l}") for l, p in fonts]
    refs = [cell(p, i, l) for l, p, i in REFS if os.path.exists(p)]
    Image.fromarray(stack([hcat(albo), hcat(refs[:3]), hcat(refs[3:])])).save(os.path.join(out, "sheet.png"))
    for f in sorted(os.listdir(out)):
        if f.endswith(".png"): print(f, Image.open(os.path.join(out, f)).size)
