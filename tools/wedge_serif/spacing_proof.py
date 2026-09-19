"""The spacing proof sheets: one text row per image, native pixels, NEAREST.

The proof-figure rules this obeys (CLAUDE.md, owner 2026-08-22): PNG, never
JPEG; rendered at the REAL pixel size and magnified by an INTEGER factor with
NEAREST resampling, never scaled by CSS or by a smooth filter; one row per
image at full width, never a shrunken grid of whole pages; and each image
narrow enough to read on a phone, which caps a row at about 1400 px and so caps
a line of 13 px text magnified 8x at about 29 characters. The lines are wrapped
to that cap rather than shrunk to it.

A BEFORE and an AFTER row share one image, stacked, because the judgement is a
comparison and switching between two files on a phone loses it. Each row is
still one row of text at native pixels; nothing is reduced.

    PYTHON_GIL=0 python3 spacing_proof.py --before DIR --after DIR --out DIR
    PYTHON_GIL=0 python3 spacing_proof.py --after DIR --out DIR --only Medium
"""
import argparse, os, sys
from PIL import Image, ImageDraw, ImageFont

STYLES = ["Medium", "Italic", "Bold", "BoldItalic"]
# Two English paragraphs. The first is the coordinator's own sentence of
# 2026-09-19, which carries the four words that broke apart -- about, capitals,
# the, between -- so the acceptance test is IN the proof rather than beside it.
PARA = [
    "The printer set the page twice, once for the proof and once for the run, "
    "and in between he changed his mind about the spacing of the capitals.",
    "Quietly the old judge in the village held that a word is not a row of "
    "letters but one image, and that a reader who must stop to gather it has "
    "been failed by the fitting and not by his eyes.",
]
# The pairs the 2026-09-19 measurement ranked worst, plus their controls, so a
# tightening can be seen against a letter that did not move.
WORDS = ["about capitals", "the between", "that little wet", "nb ab nl al nh th nw tw",
         "ITALY AVAST Toy Wavy", "1,479 and 3/4", "won't 'stop' “quoted”", "Question quay"]
SIZES = [(13, 8), (17, 6)]
MAXW = 1400
PAD = 8


def wrap(text, fnt, budget):
    out, line = [], ""
    for w in text.split():
        t = (line + " " + w).strip()
        if fnt.getlength(t) > budget and line:
            out.append(line); line = w
        else:
            line = t
    if line: out.append(line)
    return out


def row(text, ttf, px, zoom, label):
    fnt = ImageFont.truetype(ttf, px)
    w = int(fnt.getlength(text)) + 2 * PAD
    h = int(px * 1.8)
    im = Image.new("L", (w, h), 255)
    # the baseline, not the top: anchor "ls" measures from the baseline, and a
    # small y clipped every ascender in the first cut of this file.
    ImageDraw.Draw(im).text((PAD, int(px * 1.3)), text, font=fnt, fill=0, anchor="ls")
    im = im.resize((w * zoom, h * zoom), Image.NEAREST).convert("RGB")
    cap = Image.new("RGB", (im.width, im.height + 14), (255, 255, 255))
    cap.paste(im, (0, 14))
    ImageDraw.Draw(cap).text((2, 1), label, fill=(0, 0, 190))
    return cap


def stack(rows, path):
    W = max(r.width for r in rows); H = sum(r.height for r in rows) + 4 * (len(rows) - 1)
    o = Image.new("RGB", (W, H), (255, 255, 255)); y = 0
    for r in rows:
        o.paste(r, (0, y)); y += r.height + 4
    o.save(path)
    return o.size


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--after", required=True)
    ap.add_argument("--before")
    ap.add_argument("--out", required=True)
    ap.add_argument("--only")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    made = []
    for st in (["" + a.only] if a.only else STYLES):
        A = os.path.join(a.after, "Albo-%s.ttf" % st)
        B = os.path.join(a.before, "Albo-%s.ttf" % st) if a.before else None
        if not os.path.exists(A): continue
        for px, z in SIZES:
            fnt = ImageFont.truetype(A, px)
            budget = MAXW / z - 2 * PAD
            n = 0
            for pi, para in enumerate(PARA):
                for line in wrap(para, fnt, budget):
                    n += 1
                    rows = []
                    if B and os.path.exists(B): rows.append(row(line, B, px, z, "BEFORE  %s %dpx x%d" % (st, px, z)))
                    rows.append(row(line, A, px, z, "AFTER   %s %dpx x%d" % (st, px, z)))
                    p = os.path.join(a.out, "%s-%dpx-x%d-para%d-line%d.png" % (st, px, z, pi + 1, n))
                    made.append((p,) + stack(rows, p))
        # the worst pairs, at 40 px x2
        for wi, wtext in enumerate(WORDS):
            rows = []
            if B and os.path.exists(B): rows.append(row(wtext, B, 40, 2, "BEFORE  %s 40px x2" % st))
            rows.append(row(wtext, A, 40, 2, "AFTER   %s 40px x2" % st))
            p = os.path.join(a.out, "%s-40px-x2-pairs%d.png" % (st, wi + 1))
            made.append((p,) + stack(rows, p))
    for p, w, h in made:
        print("  %-64s %dx%d" % (os.path.relpath(p), w, h))
    print("  %d files" % len(made))


if __name__ == "__main__":
    sys.exit(main())
