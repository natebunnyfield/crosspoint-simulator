#!/usr/bin/env python3
"""THE BOLD PROOF -- Medium beside Bold and Italic beside BoldItalic, in words.

Owner 2026-09-19: *"continue autonomously on all commonly needed roman, italic,
bold and bold italic characters."* A weight is judged in RUNNING TEXT and not on
a letter sheet, so the sheet is the last thing here and the paragraphs are the
first.

THE PROOF-FIGURE RULES this obeys (CLAUDE.md, owner rulings 2026-08-22), because
every one of them has been broken here before:

  * PNG at native pixels, NEVER JPEG, nothing resampled after drawing.
  * Magnification is an INTEGER factor with NEAREST resampling, and the factor
    is written on the image.
  * No image wider than MAXW (1400 px): he reads these on a phone, and a
    browser that has to shrink an image to fit has undone the whole proof. The
    text is WRAPPED to a measure that fits the magnified width, which is why the
    13 px lines are short -- 1400/8 is 175 native pixels of line.
  * Labels are ASCII only. PIL's default font draws an en-dash as a tofu box and
    one shipped that way.

    python3 albo_bold_proof.py OUTDIR Medium=M.ttf Bold=B.ttf Italic=I.ttf BoldItalic=BI.ttf
    python3 albo_bold_proof.py OUTDIR --ladder Medium=M.ttf s107=a.ttf s116=b.ttf
"""
import os, sys
from PIL import Image, ImageDraw, ImageFont

MAXW = 1400
SIZES = [(13, 8), (17, 6), (40, 2)]

PARA1 = ("It is a truth universally acknowledged, that a single man in "
         "possession of a good fortune must be in want of a wife. However "
         "little known the views of such a man may be on his first entering a "
         "neighbourhood, this truth is so well fixed in the minds of the "
         "surrounding families.")
PARA2 = ("The more I study the more dissatisfied I am with variation of "
         "species. When I finished your chapter I turned about and began "
         "again, and the fresh eye reading it through found the argument "
         "whole. We have to consider what any part now does.")
MIXED = [("regular", "The quick brown fox jumps over the lazy dog, and "),
         ("bold", "THIS PART IS SET IN THE BOLD"),
         ("regular", " while the rest of the line returns to the text weight.")]


def wrap(font, text, native_w):
    words = text.split(); lines = []; cur = ""
    for w in words:
        t = (cur + " " + w).strip()
        if font.getlength(t) > native_w and cur:
            lines.append(cur); cur = w
        else:
            cur = t
    if cur: lines.append(cur)
    return lines


def block(rows, px, Z, label):
    """rows: list of (font, text). One image, magnified by Z with NEAREST."""
    lead = int(round(px * 1.42))
    w = max(int(f.getlength(t)) for f, t in rows) + 8
    h = lead * len(rows) + int(px * 0.6)
    im = Image.new("L", (w, h), 255)
    d = ImageDraw.Draw(im)
    y = int(px * 1.05)
    for f, t in rows:
        d.text((4, y), t, font=f, fill=0, anchor="ls"); y += lead
    im = im.resize((im.width * Z, im.height * Z), Image.NEAREST).convert("RGB")
    cap = Image.new("RGB", (im.width, im.height + 15), (255, 255, 255))
    cap.paste(im, (0, 0))
    ImageDraw.Draw(cap).text((3, im.height + 2), f"{label} -- {px} px at x{Z}, nearest",
                             fill=(0, 0, 190))
    return cap


def save(im, path):
    im.save(path)
    print(f"  {os.path.basename(path):<44} {im.width}x{im.height}"
          + ("   WIDE" if im.width > MAXW else ""))


def main():
    out = sys.argv[1]
    args = [a for a in sys.argv[2:] if not a.startswith("--")]
    ladder = "--ladder" in sys.argv
    arms = [a.split("=", 1) for a in args]
    os.makedirs(out, exist_ok=True)
    fonts = {k: v for k, v in arms}

    for px, Z in SIZES:
        native = MAXW // Z - 10
        # THE DECISION IMAGE: the same sentence in every arm, one line each, so
        # the weight jump is read in words rather than in letters.
        rows = []
        for k, v in arms:
            f = ImageFont.truetype(v, px)
            rows.append((f, wrap(f, PARA1, native)[0]))
        save(block(rows, px, Z, "one sentence per arm: " + ", ".join(k for k, _ in arms)),
             os.path.join(out, f"ladder-{px}px-x{Z}.png"))

        if ladder: continue

        # MIXED: the text weight and the bold in ONE line, which is how a book
        # actually uses a bold and the only way the pairing can be judged.
        for tag, a, b in (("roman", "Medium", "Bold"), ("italic", "Italic", "BoldItalic")):
            if a not in fonts or b not in fonts: continue
            fa = ImageFont.truetype(fonts[a], px); fb = ImageFont.truetype(fonts[b], px)
            # WRAP WITHIN a run, not only between runs. The first cut wrapped
            # only at a weight change, so a single run longer than the measure
            # ran off the right edge and the proof was a picture of a cropped
            # line -- caught by looking at the render, which is the only thing
            # that catches it.
            W = MAXW // Z
            lead = int(round(px * 1.42))
            placed = []; x = 4.0; row = 0
            for kind, t in MIXED:
                f = fb if kind == "bold" else fa
                for word in t.split(" "):
                    if not word: continue
                    seg = word + " "
                    wlen = f.getlength(seg)
                    if x + f.getlength(word) > W - 6 and x > 4.0:
                        row += 1; x = 4.0
                    placed.append((f, seg, x, row)); x += wlen
            im = Image.new("L", (W, lead * (row + 1) + int(px * 0.8)), 255)
            d = ImageDraw.Draw(im)
            for f, t, xx, rr in placed:
                d.text((xx, int(px * 1.05) + rr * lead), t, font=f, fill=0, anchor="ls")
            im = im.resize((im.width * Z, im.height * Z), Image.NEAREST).convert("RGB")
            cap = Image.new("RGB", (im.width, im.height + 15), (255, 255, 255))
            cap.paste(im, (0, 0))
            ImageDraw.Draw(cap).text((3, im.height + 2),
                                     f"{a} with {b} inline -- {px} px at x{Z}, nearest",
                                     fill=(0, 0, 190))
            save(cap, os.path.join(out, f"mixed-{tag}-{px}px-x{Z}.png"))

        # PARAGRAPHS and the ALPHABET, per style.
        for k, v in arms:
            f = ImageFont.truetype(v, px)
            for i, para in enumerate((PARA1, PARA2), 1):
                rows = [(f, l) for l in wrap(f, para, native)]
                save(block(rows, px, Z, f"{k}, paragraph {i}"),
                     os.path.join(out, f"para{i}-{k}-{px}px-x{Z}.png"))
            sheet = ["ABCDEFGHIJKLM", "NOPQRSTUVWXYZ", "abcdefghijklm",
                     "nopqrstuvwxyz", "0123456789 &@ .,;:!? ()"]
            save(block([(f, s) for s in sheet], px, Z, f"{k}, alphabet and figures"),
                 os.path.join(out, f"alpha-{k}-{px}px-x{Z}.png"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
