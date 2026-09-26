#!/usr/bin/env python3
"""The e->o proof page: lossless PNGs + index.html.

Rendering is FreeType FT_LOAD_RENDER (the autohinter, because Albo carries
no bytecode) -- what the firmware's converter and the Kept Legibility Index
both ask for. "reader" views are quantized to the converter's 2 bits; the
"index" view is the index's own 9 px, 8-bit, clean and after its
GaussianBlur(0.6). Every magnified image is NEAREST by an integer factor.

    python3 e_proof.py CONFIG.json OUTDIR

CONFIG: {"fonts": [[label, path, note], ...], "words_fonts": [labels],
         "counts": {label: {"vision": n, "tess": n, "gate": "ok 0.078"}}}
"""
import json, os, sys, html
import numpy as np
import freetype
import uharfbuzz as hb
from PIL import Image, ImageDraw, ImageFont, ImageFilter

INK = np.array([24, 24, 24], float); PAPER = np.array([250, 250, 246], float)
W = 700
WORDS = "the needle, seventeen, recede, excellent, between, reference, eleventh"
PARA = ("Seventeen elderly members met here between the trees; the eleventh never "
        "needed the reference, yet everyone else deferred, reread the sentence, "
        "and kept the excellent needle beneath the lever.")


def label_font(sz=13):
    for p in ("/System/Library/Fonts/SFNSMono.ttf", "/System/Library/Fonts/Menlo.ttc"):
        try:
            return ImageFont.truetype(p, sz)
        except Exception:
            pass
    return ImageFont.load_default()


def shape(path, text):
    blob = hb.Blob(open(path, "rb").read()); face = hb.Face(blob); font = hb.Font(face)
    font.scale = (face.upem, face.upem)
    buf = hb.Buffer(); buf.add_str(text); buf.guess_segment_properties()
    hb.shape(font, buf, {"kern": True, "liga": True})
    return face.upem, buf.glyph_infos, buf.glyph_positions


def render_line(path, text, ppem, twobit=False):
    """Coverage 0..1 of one shaped line; returns (array, baseline_row)."""
    upem, infos, poss = shape(path, text)
    ft = freetype.Face(path); ft.set_char_size(int(ppem * 64))
    s = ppem / upem
    wpx = int(sum(p.x_advance for p in poss) * s) + 8
    asc, desc = int(ppem * 1.05) + 2, int(ppem * 0.35) + 2
    cov = np.zeros((asc + desc, wpx))
    x = 2.0
    for inf, pos in zip(infos, poss):
        ft.load_glyph(inf.codepoint, freetype.FT_LOAD_RENDER)
        g = ft.glyph; b = g.bitmap
        if b.width and b.rows:
            a = np.frombuffer(bytes(b.buffer), dtype=np.uint8).reshape(b.rows, b.pitch)[:, :b.width] / 255.0
            ox = int(round(x + pos.x_offset * s + g.bitmap_left)); oy = asc - g.bitmap_top
            y0, x0 = max(0, oy), max(0, ox)
            sub = a[y0 - oy:, x0 - ox:]
            h_, w_ = min(sub.shape[0], cov.shape[0] - y0), min(sub.shape[1], cov.shape[1] - x0)
            cov[y0:y0 + h_, x0:x0 + w_] = np.maximum(cov[y0:y0 + h_, x0:x0 + w_], sub[:h_, :w_])
        x += pos.x_advance * s
    if twobit:
        q = (cov * 255).astype(int) >> 4
        cov = np.select([q >= 12, q >= 8, q >= 4], [3, 2, 1], 0) / 3.0
    return cov


def wrap(path, text, ppem, maxw):
    upem, infos, poss = shape(path, text)
    words, lines, cur = text.split(" "), [], ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        _, _, p = shape(path, t)
        if sum(q.x_advance for q in p) * ppem / upem > maxw and cur:
            lines.append(cur); cur = w_
        else:
            cur = t
    lines.append(cur)
    return lines


def block(path, text, ppem, maxw, twobit=False, blur=0.0, lead=1.45):
    lines = wrap(path, text, ppem, maxw - 6)
    rows = [render_line(path, ln, ppem, twobit) for ln in lines]
    lh = int(round(ppem * lead)); h = lh * (len(rows) - 1) + rows[0].shape[0]
    cov = np.zeros((h, maxw))
    for i, r in enumerate(rows):
        w_ = min(r.shape[1], maxw)
        cov[i * lh:i * lh + r.shape[0], :w_] = np.maximum(cov[i * lh:i * lh + r.shape[0], :w_], r[:, :w_])
    if blur:
        im = Image.fromarray((cov * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(blur))
        cov = np.asarray(im, float) / 255.0
    return cov


def to_img(cov, mag=1):
    rgb = PAPER[None, None, :] * (1 - cov[..., None]) + INK[None, None, :] * cov[..., None]
    im = Image.fromarray(rgb.clip(0, 255).astype(np.uint8), "RGB")
    if mag > 1:
        im = im.resize((im.width * mag, im.height * mag), Image.NEAREST)
    return im


def glyph_e(path, ppem, hinted=True):
    f = freetype.Face(path); f.set_char_size(int(ppem * 64))
    f.load_char("e", freetype.FT_LOAD_RENDER | (0 if hinted else freetype.FT_LOAD_NO_HINTING))
    b = f.glyph.bitmap
    a = np.frombuffer(bytes(b.buffer), dtype=np.uint8).reshape(b.rows, b.pitch)[:, :b.width] / 255.0
    return a, f.glyph.bitmap_top, f.glyph.bitmap_left


def cells_row(cells, cell_w, cell_h, lab_h=34):
    """cells: [(PIL image, label)] -> one row image W wide (no scaling of the cells)."""
    per = max(1, W // cell_w)
    out = []
    lf = label_font(12)
    for i in range(0, len(cells), per):
        chunk = cells[i:i + per]
        row = Image.new("RGB", (W, cell_h + lab_h), tuple(int(v) for v in PAPER))
        d = ImageDraw.Draw(row)
        for j, (im, lab) in enumerate(chunk):
            x = j * cell_w + (cell_w - im.width) // 2
            row.paste(im, (x, cell_h - im.height))
            for k, ln in enumerate(lab.split("\n")[:2]):
                tw = d.textlength(ln, font=lf)
                d.text((j * cell_w + (cell_w - tw) / 2, cell_h + 4 + 14 * k), ln, fill=(90, 90, 90), font=lf)
        out.append(row)
    return out


def main():
    cfg = json.load(open(sys.argv[1])); out = sys.argv[2]
    os.makedirs(out, exist_ok=True)
    fonts = cfg["fonts"]; figs = []

    def save(im, name, cap, kind="evidence"):
        im.save(os.path.join(out, name), optimize=True)
        figs.append((name, cap, kind))

    # 1. the e alone, 220 px em, unhinted outline (the drawing itself)
    cells = []
    for lab, path, note in fonts:
        a, _, _ = glyph_e(path, 220, hinted=False)
        cells.append((to_img(np.pad(a, 4)), lab))
    for k, im in enumerate(cells_row(cells, 140, 150)):
        save(im, f"e220-{k}.png", "The e alone at 220 px em, native pixels (the drawn outline).", "context")

    # 2. the mechanism: the e as the index's 9 px renderer draws it (autohinted), x16 nearest
    for ppem in (9.0, 9.5):
        cells = []
        for lab, path, note in fonts:
            a, top, left = glyph_e(path, ppem)
            pad = np.zeros((7, 7))          # rows: 6 px above the baseline down to 1 below
            r0 = 6 - top
            for r in range(a.shape[0]):
                if 0 <= r0 + r < 7:
                    pad[r0 + r, 1:1 + min(6, a.shape[1])] = a[r, :6]
            cells.append((to_img(pad, 16), lab))
        for k, im in enumerate(cells_row(cells, 116, 7 * 16 + 4)):
            save(im, f"e{ppem}-{k}.png",
                 f"The e at {ppem} ppem exactly as FreeType's autohinter renders it for the index (8-bit), "
                 f"each pixel shown 16x nearest; each cell spans 6 px above the baseline to 1 below. The mouth is "
                 f"the right end of the row under the bar -- clear where the e reads as e, inked where it reads as o.")

    # 3. words and paragraph
    for lab, path, note in fonts:
        if lab not in cfg["words_fonts"]:
            continue
        slug = "".join(ch if ch.isalnum() else "-" for ch in lab)[:40]
        txt = WORDS + ". " + PARA
        save(to_img(block(path, txt, 27, W // 2, twobit=True), 2), f"w27-{slug}.png",
             f"{lab}: 27 px em as the reader draws it (autohinted, 2-bit), 2x nearest.")
        save(to_img(block(path, txt, 27, W // 2, twobit=True, blur=1.8), 2), f"w27b-{slug}.png",
             f"{lab}: the same 27 px, blurred 1.8 px (the index's 0.6 px at 9 px, scaled to this em), 2x nearest.")
        save(to_img(block(path, txt, 54, W, twobit=True)), f"w54-{slug}.png",
             f"{lab}: 54 px em (the 2x app), autohinted 2-bit, native pixels.")
        save(to_img(block(path, txt, 54, W, twobit=True, blur=3.6)), f"w54b-{slug}.png",
             f"{lab}: 54 px, blurred 3.6 px (the index's blur scaled to this em), native pixels.")
        save(to_img(block(path, txt, 9, W // 4), 4), f"w9-{slug}.png",
             f"{lab}: 9 px em, the index's body-9px condition as its reader sees it (8-bit), 4x nearest.")
        save(to_img(block(path, txt, 9, W // 4, blur=0.6), 4), f"w9b-{slug}.png",
             f"{lab}: 9 px after the index's GaussianBlur(0.6) -- body-9px-blur -- 4x nearest.")

    # page
    counts = cfg.get("counts", {})
    trs = "".join(
        f"<tr><td>{html.escape(l)}</td><td>{html.escape(n)}</td><td class=n>{counts.get(l, {}).get('vision', '')}</td>"
        f"<td class=n>{counts.get(l, {}).get('tess', '')}</td><td>{html.escape(str(counts.get(l, {}).get('gate', '')))}</td></tr>"
        for l, _, n in fonts)
    body = []
    for name, cap, kind in figs:
        body.append(f'<figure><img src="{name}" alt=""><figcaption>{"CONTEXT. " if kind == "context" else ""}{html.escape(cap)}</figcaption></figure>')
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Albo e legibility</title>
<style>
:root{{--bg:#fafaf6;--fg:#1b1b1b;--mute:#5a5a5a;--rule:#d9d9d2;--card:#ffffff}}
@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{--bg:#151515;--fg:#e8e8e3;--mute:#a4a4a0;--rule:#333;--card:#1d1d1d}}}}
:root[data-theme="dark"]{{--bg:#151515;--fg:#e8e8e3;--mute:#a4a4a0;--rule:#333;--card:#1d1d1d}}
body{{background:var(--bg);color:var(--fg);font:15px/1.5 -apple-system,system-ui,sans-serif;margin:0;padding:16px}}
main{{max-width:700px;margin:0 auto}}
figure{{margin:18px 0}}
img{{display:block;width:100%;height:auto;image-rendering:pixelated}}
figcaption{{color:var(--mute);font-size:13px;margin-top:4px}}
table{{border-collapse:collapse;width:100%;font-size:13px}}td,th{{border-bottom:1px solid var(--rule);padding:4px 6px;text-align:left}}
.n{{text-align:right;font-variant-numeric:tabular-nums}}
.wrap{{overflow-x:auto}}
</style></head><body><main>
<h1>Albo e legibility</h1>
<p>{html.escape(cfg.get("intro", ""))}</p>
<div class="wrap"><table><tr><th>font</th><th>what it is</th><th>Vision e&gt;o</th><th>Tesseract e&gt;o</th><th>hint gate</th></tr>{trs}</table></div>
<p style="color:var(--mute);font-size:13px">Images are PNG at native pixels composed to 700 px rows; magnified views are integer NEAREST, as each caption says. On a screen narrower than 700 px the whole row is scaled by the browser.</p>
{''.join(body)}
</main></body></html>"""
    open(os.path.join(out, "index.html"), "w").write(page)
    print(len(figs), "figures ->", out)


if __name__ == "__main__":
    main()
