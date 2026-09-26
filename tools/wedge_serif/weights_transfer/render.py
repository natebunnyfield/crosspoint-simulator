#!/usr/bin/env python3
"""The proof for the weight-transfer study: every cut x every arm, the same
English, plus his most-corrected pairs as a grid.

Rasterized with FreeType (freetype-py), FORCE_AUTOHINT and grayscale, then cut
to FOUR levels -- the reader's 2-bit autohinted pipeline -- and laid out with
HarfBuzz positions (kern on, ligatures on, as the reader shapes), each glyph
placed at its rounded pixel pen position. PNG at native pixels; the 27 px rows
are magnified x2 NEAREST.

    $VENV/bin/python render.py FONTS_DIR OUT_DIR
"""
import html, json, os, sys
import numpy as np
import freetype
import uharfbuzz as hb
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from transfer import CUTS, BASE  # noqa: E402

ARMS = [("today", "a. today (units)"), ("b-stem", "b. stem-scaled"), ("c-rhythm", "c. rhythm (counter)"), ("d-b2", "d. B2 on each cut")]
PARA = ("The printer set the page twice, once for the proof and once for the run, and in between "
        "he changed his mind about the spacing of the lowercase. Nobody who reads the book will know "
        "it; they will only find that it asks less of them.")
WORDS = "subjective objections, adjacent ejecta; drums, asks, swim, whether, aspens, thumbs, kiosks, swallowed"
LEVELS = np.array([0, 85, 170, 255])


class Face:
    def __init__(self, path, px):
        self.ft = freetype.Face(path); self.ft.set_pixel_sizes(0, px); self.px = px
        blob = hb.Blob.from_file_path(path); self.hbf = hb.Font(hb.Face(blob))
        self.upm = self.hbf.face.upem
        self.cache = {}

    def glyph(self, gid):
        if gid not in self.cache:
            self.ft.load_glyph(gid, freetype.FT_LOAD_FORCE_AUTOHINT | freetype.FT_LOAD_TARGET_NORMAL)
            self.ft.glyph.render(freetype.FT_RENDER_MODE_NORMAL)
            b = self.ft.glyph.bitmap
            a = np.array(b.buffer, dtype=np.uint8).reshape(b.rows, b.pitch)[:, :b.width] if b.rows else np.zeros((0, 0), np.uint8)
            self.cache[gid] = (a, self.ft.glyph.bitmap_left, self.ft.glyph.bitmap_top)
        return self.cache[gid]

    def shape(self, s):
        buf = hb.Buffer(); buf.add_str(s); buf.guess_segment_properties()
        hb.shape(self.hbf, buf, {"kern": True, "liga": True})
        sc = self.px / self.upm
        return [(i.codepoint, p.x_advance * sc, p.x_offset * sc) for i, p in zip(buf.glyph_infos, buf.glyph_positions)]

    def width(self, s):
        return sum(a for _, a, _ in self.shape(s))


def wrap(F, text, W):
    lines, cur = [], ""
    for w in text.split(" "):
        t = (cur + " " + w).strip()
        if cur and F.width(t) > W:
            lines.append(cur); cur = w
        else:
            cur = t
    lines.append(cur)
    return lines


def draw_lines(F, lines, W, lead=1.45):
    lh = int(round(F.px * lead)); H = lh * len(lines) + int(F.px * 0.5)
    img = np.zeros((H, W), np.float32)
    for li, line in enumerate(lines):
        x = 0.0; base = int(F.px * 1.0) + li * lh
        for gid, adv, xo in F.shape(line):
            a, l, t = F.glyph(gid)
            if a.size:
                x0 = int(round(x + xo)) + l; y0 = base - t
                ys, xs = slice(max(0, y0), min(H, y0 + a.shape[0])), slice(max(0, x0), min(W, x0 + a.shape[1]))
                sub = a[ys.start - y0:ys.stop - y0, xs.start - x0:xs.stop - x0]
                img[ys, xs] = np.maximum(img[ys, xs], sub)
            x += adv
    q = LEVELS[np.clip(np.round(img / 255 * 3), 0, 3).astype(int)]
    return Image.fromarray((255 - q).astype(np.uint8), "L")


def text_block(path, px, W, text):
    F = Face(path, px)
    return draw_lines(F, wrap(F, text, W - 8), W)


def label(img, s, h=22):
    out = Image.new("L", (img.width, img.height + h), 255)
    ImageDraw.Draw(out).text((2, 3), s, fill=90, font=ImageFont.load_default(size=15))
    out.paste(img, (0, h)); return out


def stack(imgs, gap=10):
    W = max(i.width for i in imgs); H = sum(i.height for i in imgs) + gap * (len(imgs) - 1)
    out = Image.new("L", (W, H), 255); y = 0
    for i in imgs:
        out.paste(i, (0, y)); y += i.height + gap
    return out


def hcat(imgs, gap=24):
    H = max(i.height for i in imgs); W = sum(i.width for i in imgs) + gap * (len(imgs) - 1)
    out = Image.new("L", (W, H), 255); x = 0
    for i in imgs:
        out.paste(i, (x, 0)); x += i.width + gap
    return out


def carrier(pair, cars):
    ws = cars.get(pair) or []
    best = sorted((tuple(x) for x in ws), key=lambda kv: (-kv[1], len(kv[0])))
    for w, _ in best:
        if w.isalpha() and w.islower() and 4 <= len(w) <= 9:
            return w
    return best[0][0] if best else pair


def main():
    fonts, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    meas = json.load(open(os.path.join(fonts, "measure.json")))
    cars = json.load(open(os.path.join(HERE, "census-bigrams.json")))["carriers"]
    figs = []
    for style, cuts in CUTS.items():
        for cut, wt in cuts:
            for px, mag, W, tag in ((27, 2, 520, "27px-x2"), (54, 1, 1040, "54px")):
                rows = []
                for arm, name in (ARMS[:1] if cut == BASE[style] else ARMS):
                    p = os.path.join(fonts, arm, f"Albo-{cut}.ttf")
                    b = stack([text_block(p, px, W, PARA), text_block(p, px, W, WORDS)], gap=int(px * 0.4))
                    if mag > 1:
                        b = b.resize((b.width * mag, b.height * mag), Image.NEAREST)
                    rows.append(label(b, f"{cut} {wt} -- {name}" if cut != BASE[style] else
                                      f"{cut} {wt} -- the anchor: every arm leaves it unchanged (measured 0.00)"))
                fn = f"text-{cut}-{tag}.png"
                stack(rows, gap=26).save(os.path.join(out, fn))
                figs.append((style, cut, wt, tag, fn))
    grids = []
    for style, cuts in CUTS.items():
        blocks = []
        for pair in meas["grid"][style]:
            word = carrier(pair, cars)
            his = meas["his"][style][pair]
            cols = []
            for cut, wt in cuts:
                cells = []
                for arm, name in ARMS:
                    p = os.path.join(fonts, arm, f"Albo-{cut}.ttf")
                    w = meas["white"][arm][cut][pair]
                    img = text_block(p, 40, 300, word)
                    cells.append(label(img, f"{arm.split('-')[0]}  white {w:.0f}" if w is not None else arm, h=18))
                cols.append(label(stack(cells, gap=4), f"{cut} {wt}"))
            hs = f"his answers n={his['n']} mean {his['mean']:+.0f}" if his["n"] else "not answered in this style"
            blocks.append(label(hcat(cols), f"'{pair}' in '{word}'   ({hs})", h=24))
        fn = f"grid-{style}.png"
        stack(blocks, gap=30).save(os.path.join(out, fn))
        grids.append((style, fn))
    json.dump({"text": figs, "grids": grids}, open(os.path.join(out, "figs.json"), "w"), indent=1)
    print("wrote", len(figs), "text figures and", len(grids), "grids to", out)


if __name__ == "__main__":
    main()
