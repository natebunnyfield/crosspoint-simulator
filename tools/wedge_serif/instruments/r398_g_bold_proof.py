#!/usr/bin/env python3
"""Round 398 proof: the Bold Italic g before/after going onto the weight axis.

    $VENV/bin/python r398_g_bold_proof.py BEFORE_DIR AFTER_DIR OUT_DIR

Rendered as the reader renders (local_ai/b2_proof.py's Setter: FreeType, 2-bit
coverage, linear advances, kerns in 1/16 px). Lossless PNG; the 27 px rows are
enlarged 2x with NEAREST here, never by CSS.
"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "local_ai"))
from b2_proof import Setter, to_png  # noqa: E402

WORDS = "going again bigger straight"
LAB = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)


def label(text, w, h=30):
    im = Image.new("L", (w, h), 255)
    ImageDraw.Draw(im).text((6, 5), text, font=LAB, fill=90)
    return 255 - np.asarray(im)


def row(cells, gap=40):
    H = max(c.shape[0] for c in cells)
    out = []
    for c in cells:
        out += [np.pad(c, ((H - c.shape[0], 0), (0, 0))), np.zeros((H, gap), np.uint8)]
    return np.hstack(out)


def cell(setter, text, cap):
    # full-height canvas, columns cropped only: every cell shares one baseline
    img = setter.block([text], 2000, 1.3, rows=["  " + text + "  "])   # spaces: an italic overhangs its origin
    xs = np.nonzero(img.any(0))[0]
    img = img[:, max(0, xs[0] - 10):xs[-1] + 10]
    w = max(img.shape[1], 215)
    img = np.pad(img, ((0, 0), (0, w - img.shape[1])))
    return np.vstack([img, label(cap, w)])


def main():
    before, after, out = sys.argv[1:4]
    os.makedirs(out, exist_ok=True)
    bi = lambda d, px: Setter(os.path.join(d, "Albo-BoldItalic.ttf"), px, False)
    it = lambda d, px: Setter(os.path.join(d, "Albo-Italic.ttf"), px, False)
    B, A, I = bi(before, 220), bi(after, 220), it(after, 220)
    top = row([cell(I, "g", "Italic g (approved)"), cell(B, "g", "BI g, round 397"),
               cell(A, "g", "BI g, round 398")] + [cell(A, ch, "BI " + ch) for ch in "aoqd"])
    ys = np.nonzero(top[:-30].any(1))[0]
    top = np.vstack([top[max(0, ys[0] - 10):ys[-1] + 10], top[-30:]])
    to_png(top, os.path.join(out, "g-220.png"))
    for px, sc in ((27, 2), (54, 1)):
        rows = []
        for name, d in (("round 397", before), ("round 398", after)):
            s = bi(d, px)
            img = s.block([WORDS], 2000, 1.4, rows=[WORDS])
            ys, xs = np.nonzero(img)
            img = img[max(0, ys.min() - 6):ys.max() + 8, :xs.max() + 12]
            rows.append((name, img))
        W = max(r[1].shape[1] for r in rows)
        stack = []
        for name, img in rows:
            stack += [label(name, W, 22), np.pad(img, ((0, 0), (0, W - img.shape[1])))]
        to_png(np.vstack(stack), os.path.join(out, f"words-{px}.png"), sc)
    html = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Bold Italic g</title>
<style>
:root { --bg:#fbfbf9; --fg:#1d1d1b; --mut:#6b6b66; --line:#dcdcd6; --panel:#ffffff; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { --bg:#161614; --fg:#e8e8e3; --mut:#a3a39c; --line:#3a3a36; } }
:root[data-theme="dark"] { --bg:#161614; --fg:#e8e8e3; --mut:#a3a39c; --line:#3a3a36; }
body { background:var(--bg); color:var(--fg); font:16px/1.5 -apple-system, system-ui, sans-serif; margin:0; padding:16px; }
main { max-width:1200px; margin:0 auto; } .cap { color:var(--mut); font-size:14px; margin:18px 0 6px; }
.strip { display:block; overflow-x:auto; background:var(--panel); border:1px solid var(--line); margin:4px 0; }
.strip img { display:block; image-rendering:pixelated; }
</style></head><body><main>
<h1>Bold Italic g</h1>
<p>The cursive g's widths were never on the weight axis, so the Bold Italic drew the 400's g. Round 398 scales every
width of that letter by 1.65 above the Medium (the measured Bold Italic / Italic ratio of the bowl letters); the Italic g
is untouched (approved.py). Rendered as the reader renders.</p>
<p class="cap">220 px, native: the approved Italic g, the Bold Italic g before and after, and the Bold Italic a o q d.</p>
<div class="strip"><img src="g-220.png" alt="g comparison at 220 px"></div>
<p class="cap">Bold Italic words at 27 px, enlarged 2&times; with nearest-neighbor. Top: round 397. Bottom: round 398.</p>
<div class="strip"><img src="words-27.png" alt="words at 27 px"></div>
<p class="cap">The same at 54 px, native pixels, 1:1.</p>
<div class="strip"><img src="words-54.png" alt="words at 54 px"></div>
</main></body></html>"""
    open(os.path.join(out, "index.html"), "w").write(html)
    print("wrote", out)


if __name__ == "__main__":
    main()
