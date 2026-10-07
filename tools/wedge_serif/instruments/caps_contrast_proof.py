#!/usr/bin/env python3
"""caps_contrast_proof.py -- the Bold capitals' light-stroke arms, drawn
(docs/albo-capitals-contrast-options-2026-10-06.md).

    $VENV/bin/python instruments/caps_contrast_proof.py OUT LABEL=DIR ...   (DIR holds Albo-Bold.ttf, Albo-BoldItalic.ttf)

  compare.png      one compact image: "WAVE MAGNA HELLO" per arm, B left, Z right, 1x through the reader's renderer
  para-B.png       a paragraph of REAL bold runs from his books (headings and <strong>), X3 10 pt
  para-Z.png       (150 dpi) through the reader's renderer, one block per arm, 3x NEAREST
  sheet-B.png      the 26 capitals per arm at a 72 px em, 1x
  sheet-Z.png
Everything is PNG at native pixels or an integer NEAREST magnification.
"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); WS = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(WS, "fit_audit")); sys.path.insert(0, HERE)
from legib import Renderer
import poor_proof as P
PAPER = tuple(int(v) for v in P.PAPER)
LAB = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)
CUTS = {"B": "Bold", "Z": "BoldItalic"}

# Every string is a bold run (a heading or <strong>) from the owner's own epubs:
# eighth-atlas, trivia-aimed-v2, ai-engineering-essentials (claude-tools).
PARA = ["The Mythical Man-Month. The Montreal Protocol.",
        "Training Within Industry. The Computer Journal.",
        "Art Questions Are Crime Questions. TRIZ deep",
        "strata. A Murder of Crows, a Parliament of Owls.",
        "The Royal Box and Other Arbitrary Numbers. Quiz",
        "answers: Empire in a Glass. The Man Who Is Half",
        "the Canon. Quiz answers: The Gaps in the Table."]
WORDS = "WAVE MAGNA HELLO"


def render(path, s, ppem):
    R = Renderer(path, 0, ppem)
    c = np.zeros((int(ppem * 1.5), int(ppem * len(s) + 40)), np.uint8)
    R.line(s, c, 4, int(ppem * 1.15))
    cols = np.nonzero(c.any(0))[0]
    return c[:, :cols[-1] + 6] if len(cols) else c


def lab(text, h, w=70):
    li = Image.new("RGB", (w, h), PAPER); ImageDraw.Draw(li).text((10, h // 2 - 11), text, fill=(30, 30, 30), font=LAB)
    return np.array(li)


def pad_w(b, W):
    return np.concatenate([b, np.full((b.shape[0], W - b.shape[1], 3), PAPER, np.uint8)], 1)


def stack(bs, gap=10):
    W = max(b.shape[1] for b in bs); out = []
    for i, b in enumerate(bs):
        out.append(pad_w(b, W))
        if i < len(bs) - 1: out.append(np.full((gap, W, 3), 255, np.uint8))
    return np.concatenate(out, 0)


def hcat(cs, gap=16):
    H = max(c.shape[0] for c in cs); parts = []
    for c in cs:
        parts += [np.concatenate([c, np.full((H - c.shape[0], c.shape[1], 3), PAPER, np.uint8)], 0),
                  np.full((H, gap, 3), 255, np.uint8)]
    return np.concatenate(parts[:-1], 1)


def main():
    out = sys.argv[1]; arms = [a.split("=", 1) for a in sys.argv[2:]]
    os.makedirs(out, exist_ok=True)
    rows = []
    for name, d in arms:
        cells = [P.rgb(render(os.path.join(d, f"Albo-{CUTS[k]}.ttf"), WORDS, 56)) for k in ("B", "Z")]
        r = hcat(cells); rows.append(hcat([lab(name, r.shape[0]), r], 0))
    Image.fromarray(stack(rows)).save(os.path.join(out, "compare.png"))
    ppem = 150 / 72 * 10
    for k, cut in CUTS.items():
        blocks = []
        for name, d in arms:
            path = os.path.join(d, f"Albo-{cut}.ttf")
            lines = [render(path, s, ppem) for s in PARA]
            W = max(l.shape[1] for l in lines)
            para = np.concatenate([np.pad(l, ((0, 0), (0, W - l.shape[1]))) for l in lines], 0)
            img = P.rgb(np.kron(para, np.ones((3, 3), np.uint8)))
            blocks.append(hcat([lab(name, 60), img], 0))
        Image.fromarray(stack(blocks, 18)).save(os.path.join(out, f"para-{k}.png"))
        rows = []
        for name, d in arms:
            path = os.path.join(d, f"Albo-{cut}.ttf")
            a = render(path, "ABCDEFGHIJKLM", 72); b = render(path, "NOPQRSTUVWXYZ", 72)
            r = stack([P.rgb(a), P.rgb(b)], 0); rows.append(hcat([lab(name, r.shape[0]), r], 0))
        Image.fromarray(stack(rows)).save(os.path.join(out, f"sheet-{k}.png"))


if __name__ == "__main__":
    main()
