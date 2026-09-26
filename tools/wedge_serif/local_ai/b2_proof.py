#!/usr/bin/env python3
"""Proof page: round 395 over the B2 spacing arm, set the way the reader sets.

    $VENV/bin/python b2_proof.py BASE_DIR B2_DIR MOVED_JSON OUT_DIR

RENDERING (as the reader does, fontconvert_sdcard.py): FreeType, FT_LOAD_RENDER
with default flags (the auto-hinter on these unhinted TTFs), coverage cut to
the reader's four levels (2-bit), pen advanced by the glyph's LINEAR advance
(fractional) plus the GPOS kern quantized to 1/16 px (the reader's 4.4 fixed
point), each bitmap placed at the pen rounded to a whole pixel. Kerns and
ligatures come from HarfBuzz; the italic has no ligatures (owner 2026-09-21).

Writes lossless PNGs and index.html (no image is ever sized by CSS; the 2x
figures are enlarged with NEAREST here, at generation).
"""
import html, json, os, sys
import numpy as np
import freetype
import uharfbuzz as hb
from PIL import Image, ImageDraw, ImageFont

PARA = [
    "It is a truth universally acknowledged, that a single man in possession of a good "
    "fortune, must be in want of a wife. However little known the feelings or views of "
    "such a man may be on his first entering a neighbourhood, this truth is so well fixed "
    "in the minds of the surrounding families, that he is considered the rightful property "
    "of some one or other of their daughters.",
    "The rhythm of the argument was wrongly named: You and John found every agreement in "
    "the software, first things first, because the community had checked it. Yesterday "
    "they said that it appears the English have their own views, and which of them are "
    "rather more difficult than others is a question for another day.",
]
LONG = ("responsibility approximately understanding characteristically appearances "
        "institutionalization extraordinary acknowledgement simultaneously "
        "Wednesday Philadelphia Mediterranean Dostoevsky Everybody's")
FILES = {"roman": "Albo-Regular.ttf", "italic": "Albo-Italic.ttf"}
WIDTH54 = 1100


class Setter:
    def __init__(self, path, px, liga):
        self.face = freetype.Face(path)
        self.face.set_pixel_sizes(0, px)
        self.px = px
        self.upm = self.face.units_per_EM
        self.hb = hb.Font(hb.Face(hb.Blob.from_file_path(path)))
        self.feats = {"liga": liga, "kern": True}
        self.cache = {}

    def glyph(self, gid):
        if gid not in self.cache:
            self.face.load_glyph(gid, freetype.FT_LOAD_RENDER)
            g = self.face.glyph
            bm = g.bitmap
            a = np.array(bm.buffer, np.uint8).reshape(bm.rows, bm.width) if bm.rows else np.zeros((0, 0), np.uint8)
            a = (np.round(a / 255 * 3) / 3 * 255).astype(np.uint8)      # 2-bit, as the reader stores
            self.cache[gid] = (a, g.bitmap_left, g.bitmap_top, g.linearHoriAdvance / 65536.0)
        return self.cache[gid]

    def line(self, text):
        buf = hb.Buffer(); buf.add_str(text); buf.guess_segment_properties()
        hb.shape(self.hb, buf, self.feats)
        s = self.px / self.upm
        pen, out = 0.0, []
        for inf, pos in zip(buf.glyph_infos, buf.glyph_positions):
            a, l, t, lin = self.glyph(inf.codepoint)
            natural = self.hb.get_glyph_h_advance(inf.codepoint)
            kern = round((pos.x_advance - natural) * s * 16) / 16
            out.append((int(np.floor(pen + 0.5)) + l, t, a))
            pen += lin + kern
        return out, pen

    def words(self, text, width):
        lines, cur = [], ""
        for w in text.split():
            t = (cur + " " + w).strip()
            if self.line(t)[1] > width and cur:
                lines.append(cur); cur = w
            else:
                cur = t
        return lines + ([cur] if cur else [])

    def block(self, paras, width, lead=1.45, rows=None):
        """rows: reuse another arm's line breaks, so both arms set the SAME lines
        and a difference view compares words, not a rewrap."""
        if rows is None:
            rows = []
            for p in paras:
                rows += self.words(p, width) + [""]
        lh = int(round(self.px * lead)); asc = int(round(self.px * 0.95))
        img = np.zeros((lh * len(rows) + self.px // 2, width + self.px), np.uint8)
        for i, r in enumerate(rows):
            if not r:
                continue
            gl, _ = self.line(r)
            base = i * lh + asc
            for x, t, a in gl:
                y = base - t
                if a.size == 0:
                    continue
                y0, x0 = max(0, y), max(0, x)
                sub = a[y0 - y:, x0 - x:]
                h, w = min(sub.shape[0], img.shape[0] - y0), min(sub.shape[1], img.shape[1] - x0)
                img[y0:y0 + h, x0:x0 + w] = np.maximum(img[y0:y0 + h, x0:x0 + w], sub[:h, :w])
        self.rows = rows
        return img

    def word(self, text, pad=16):
        img = self.block([text], 4000, 1.3, rows=[text])
        ys, xs = np.nonzero(img)
        return img[max(0, ys.min() - pad):ys.max() + pad, max(0, xs.min() - pad):xs.max() + pad]


def to_png(cov, path, scale=1):
    im = Image.fromarray(255 - cov)
    if scale > 1:
        im = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
    im.save(path)
    return os.path.basename(path)


def diff_png(a, b, path):
    h, w = max(a.shape[0], b.shape[0]), max(a.shape[1], b.shape[1])
    A = np.zeros((h, w)); B = np.zeros((h, w))
    A[:a.shape[0], :a.shape[1]] = a / 255; B[:b.shape[0], :b.shape[1]] = b / 255
    both = np.minimum(A, B); onlyA = A - both; onlyB = B - both
    rgb = np.ones((h, w, 3))
    rgb -= both[..., None] * 0.55                              # gray: ink in both
    rgb -= onlyA[..., None] * np.array([1.0, 0.45, 0.0])       # blue: round 395 only
    rgb -= onlyB[..., None] * np.array([0.0, 0.85, 0.85])      # red: B2 only
    Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8)).save(path)
    return os.path.basename(path)


LABEL = None


def label(text, w, h=28):
    global LABEL
    if LABEL is None:
        LABEL = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 18)
    im = Image.new("L", (w, h), 255)
    ImageDraw.Draw(im).text((4, 4), text, font=LABEL, fill=90)
    return 255 - np.asarray(im)


def pair_strip(base, b2, moved, style, out, px=108):
    sA, sB = Setter(base, px, style == "roman"), Setter(b2, px, style == "roman")
    rows = [r for r in moved if r["style"] == style][:15]
    # the ranked list is sorted by |d| x count already
    cells = []
    for r in rows:
        a, b = sA.word(r["word"]), sB.word(r["word"])
        wd = max(a.shape[1], b.shape[1], 520)
        pad = lambda m: np.pad(m, ((0, 0), (0, wd - m.shape[1])))
        txt = f"{r['pair']}  ({r['word']})   white {r['before']} -> {r['after']}  ({r['d']:+d})   {r['n']:,} in his books"
        cells.append(np.vstack([label(txt, wd), label("round 395", wd, 22), pad(a),
                                label("B2", wd, 22), pad(b), np.zeros((30, wd), np.uint8)]))
    W = max(c.shape[1] for c in cells)
    img = np.vstack([np.pad(c, ((0, 0), (0, W - c.shape[1]))) for c in cells])
    return to_png(img, os.path.join(out, f"pairs-{style}.png"))


def main():
    base_dir, b2_dir, moved_json, out = sys.argv[1:5]
    os.makedirs(out, exist_ok=True)
    moved = json.load(open(moved_json))
    figs = {}
    for style, fn in FILES.items():
        base, b2 = os.path.join(base_dir, fn), os.path.join(b2_dir, fn)
        liga = style == "roman"
        f = {}
        for px, width, scale in ((27, WIDTH54 // 2, 2), (54, WIDTH54, 1)):
            sa = Setter(base, px, liga)
            A = sa.block(PARA + [LONG], width)
            B = Setter(b2, px, liga).block(PARA + [LONG], width + px * 2, rows=sa.rows)
            f[px] = (to_png(A, os.path.join(out, f"{style}-{px}-r395.png"), scale),
                     to_png(B, os.path.join(out, f"{style}-{px}-b2.png"), scale))
            if px == 54:
                f["diff"] = diff_png(A, B, os.path.join(out, f"{style}-54-diff.png"))
        f["pairs"] = pair_strip(base, b2, moved["all"], style, out)
        figs[style] = f
    s = moved["summary"]
    rows = "".join(
        f"<tr><td>{r['style']}</td><td><code>{html.escape(r['pair'])}</code></td><td>{r['n']:,}</td>"
        f"<td>{r['before']}</td><td>{r['after']}</td><td>{r['d']:+d}</td><td>{html.escape(r['word'])}</td></tr>"
        for r in moved["top"])
    sec = ""
    for style in ("roman", "italic"):
        f = figs[style]; t = style.capitalize()
        sec += f"""
<h2>{t}</h2>
<p class="cap">27 px, enlarged 2&times; with nearest-neighbor at generation. Top: round 395. Bottom: B2. Both arms set the same line breaks (round 395's).</p>
<div class="strip"><img src="{f[27][0]}" alt="{t} round 395 at 27 px"></div>
<div class="strip"><img src="{f[27][1]}" alt="{t} B2 at 27 px"></div>
<p class="cap">54 px (the phone's em), native pixels, 1:1. Top: round 395. Bottom: B2.</p>
<div class="strip"><img src="{f[54][0]}" alt="{t} round 395 at 54 px"></div>
<div class="strip"><img src="{f[54][1]}" alt="{t} B2 at 54 px"></div>
<p class="cap">Difference at 54 px: <span class="k g">gray</span> ink in both, <span class="k b">blue</span> round 395 only, <span class="k r">red</span> B2 only.</p>
<div class="strip"><img src="{f['diff']}" alt="{t} difference"></div>
<p class="cap">The {t.lower()} pairs B2 moves most (by |&Delta;white| &times; frequency in his books), each in its commonest word at 108 px, native. Upper: round 395; lower: B2.</p>
<div class="strip"><img src="{f['pairs']}" alt="{t} most-moved pairs"></div>
"""
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>B2 Spacing Proof</title>
<style>
:root {{ --bg:#fbfbf9; --fg:#1d1d1b; --mut:#6b6b66; --line:#dcdcd6; --panel:#ffffff; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ --bg:#161614; --fg:#e8e8e3; --mut:#a3a39c; --line:#3a3a36; --panel:#fbfbf9; }} }}
:root[data-theme="dark"] {{ --bg:#161614; --fg:#e8e8e3; --mut:#a3a39c; --line:#3a3a36; --panel:#fbfbf9; }}
body {{ background:var(--bg); color:var(--fg); font:16px/1.5 -apple-system, system-ui, sans-serif; margin:0; padding:16px; }}
main {{ max-width:1200px; margin:0 auto; }}
.cap {{ color:var(--mut); font-size:14px; margin:18px 0 6px; }}
.strip {{ display:block; overflow-x:auto; background:var(--panel); border:1px solid var(--line); margin:4px 0; }}
.strip img {{ display:block; image-rendering:pixelated; }}
table {{ border-collapse:collapse; font-size:14px; display:block; overflow-x:auto; }}
td, th {{ border-bottom:1px solid var(--line); padding:3px 10px; text-align:left; }}
.k {{ padding:0 4px; border-radius:3px; color:#fff; }} .g {{ background:#737373; }} .b {{ background:#0073ff; }} .r {{ background:#ff2626; }}
</style></head><body><main>
<h1>B2 Spacing Proof</h1>
<p>Round 395 as shipped, over the B2 arm (<code>ALBO_SPACING_FIT=b2</code>): the per-glyph ridge plus measured shape
features, held out at 10.73 units against the shipped fit's 11.66 and his repeatability of 10.83. Rendered as the reader
renders: FreeType, 2-bit coverage, fractional advances, kerns in 1/16 px.</p>
<p>Frequency-weighted over his books: roman moves {s['roman']['wabs']:.1f} units per pair on average (mean {s['roman']['wmean']:+.2f}),
italic {s['italic']['wabs']:.1f} (mean {s['italic']['wmean']:+.2f}). The pairs he set by hand after the bench (rounds 384&ndash;390) are held at round 395's white.</p>
{sec}
<h2>The 30 pairs that move most</h2>
<p class="cap">White = right bearing + kern + left bearing, in design units (1000 per em); ranked by |&Delta;| &times; count in his books.</p>
<table><tr><th>style</th><th>pair</th><th>count</th><th>r395</th><th>B2</th><th>&Delta;</th><th>word</th></tr>{rows}</table>
</main></body></html>"""
    open(os.path.join(out, "index.html"), "w").write(page)
    print("wrote", out)


if __name__ == "__main__":
    main()
