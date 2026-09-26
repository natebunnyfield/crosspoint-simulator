#!/usr/bin/env python3
"""Proof page for the hinting arms (2026-09-26).

For 9 px and every real Albo size (sd-fonts.yaml 8..18 pt at 150 dpi, and the
2x tier the phone draws, 16..36 pt), the same English paragraph and a line of
long words, set from converter-faithful 2-bit glyphs (compose.py), once per
arm. Native pixels, lossless PNG, each strip in a 1:1 scroller with no CSS
sizing. Then 4x NEAREST crops of a few words with every arm stacked in ONE
image, so the comparison is made in the image, not by the layout.

    python3 proof.py --fonts DIR --out DIR [--measure measure.json --gate gate.json
                     --kli kli-flags0.json,kli-nohint.json,kli-light.json --reader reader.json]
"""
import argparse, html, json, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import raster  # noqa: E402
from compose import Setter, to_gray  # noqa: E402

PARA = ("Here we see the whole of the meaning: every sentence is a thing the eye "
        "must get through before the mind can hold it, and the reader never "
        "notices the letters until one of them fails. Then the e becomes an o, "
        "the line stops being a line, and he reads the word twice.")
LONG = "effervescence benevolence nevertheless indefensible"
ITAL = "effervescence benevolence minimum"
ARMS = ["today", "ttfa-q", "light", "nohint"]
SHORT = {"today": "TODAY", "ttfa-q": "TTFAUTOHINT", "light": "LIGHT", "nohint": "NO HINTING"}
CROP_WORDS = ["effervescence", "minimum", "benevolence"]
CROP_SIZES = ["9px", "8pt", "10pt", "8pt@2x"]
COLUMN = {"1x": 460, "9px": 300, "2x": 920}  # X3 text column, ~528 px panel less margins


def label_font(px):
    for p in ("/System/Library/Fonts/SFNSMono.ttf", "/System/Library/Fonts/Menlo.ttc"):
        try:
            return ImageFont.truetype(p, px)
        except Exception:
            pass
    return ImageFont.load_default()


def block(fonts, arm, key, sz, dpi, tier):
    width = COLUMN[tier]
    rom = Setter(raster.font_path(fonts, arm, "Regular"), sz, dpi, raster.ARMS[arm][1])
    it = Setter(raster.font_path(fonts, arm, "Italic"), sz, dpi, raster.ARMS[arm][1])
    a = rom.set_lines(rom.wrap(PARA, width) + rom.wrap(LONG, width), width)
    b = it.set_lines(it.wrap(ITAL, width), width)
    W = max(a.shape[1], b.shape[1])
    pad = lambda m: np.pad(m, ((0, 0), (0, W - m.shape[1])))
    return np.vstack([pad(a), pad(b)])


def crop_word(fonts, word, key, sz, dpi, scale=4):
    rows, lab = [], label_font(13)
    for arm in ARMS:
        st = Setter(raster.font_path(fonts, arm, "Regular"), sz, dpi, raster.ARMS[arm][1])
        lv = st.set_lines([word], int(st.width(word) + st.ppem * 0.3) + 2, pad=2)
        rows.append((arm, np.kron(to_gray(lv), np.ones((scale, scale), np.uint8))))
    W = max(r.shape[1] for _, r in rows) + 150
    H = sum(r.shape[0] + 8 for _, r in rows)
    im = Image.new("L", (W, H), 255)
    d = ImageDraw.Draw(im)
    y = 0
    for arm, r in rows:
        im.paste(Image.fromarray(r), (150, y))
        d.text((6, y + r.shape[0] // 2 - 7), SHORT[arm], fill=0, font=lab)
        y += r.shape[0] + 8
    return im


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fonts", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--tables", help="HTML fragment with the measured tables, inserted verbatim")
    a = ap.parse_args()
    os.makedirs(os.path.join(a.out, "img"), exist_ok=True)
    secs = []
    # crops first: they carry the finding
    crop_html = []
    for key, sz, dpi, ppem, tier in raster.sizes():
        if key not in CROP_SIZES:
            continue
        for w in CROP_WORDS:
            fn = f"img/crop-{w}-{key.replace('@', '-')}.png"
            crop_word(a.fonts, w, key, sz, dpi).save(os.path.join(a.out, fn), optimize=True)
            crop_html.append(f'<figure><div class="strip"><img src="{fn}" alt="{w} at {key}, four arms"></div>'
                             f'<figcaption><b>{w}</b>, roman, {key} ({ppem:.2f} ppem). 4&times; nearest, '
                             f'top to bottom: TODAY, TTFAUTOHINT, LIGHT, NO HINTING.</figcaption></figure>')
    for key, sz, dpi, ppem, tier in raster.sizes():
        if key == "8pt@2x":
            note = " &mdash; the phone's 8 pt; the same pixels as 16 pt at 1x"
        elif tier == "9px":
            note = " &mdash; the index's body size, not a reader size"
        else:
            note = ""
        figs = []
        for arm in ARMS:
            fn = f"img/para-{key.replace('@', '-')}-{arm}.png"
            Image.fromarray(to_gray(block(a.fonts, arm, key, sz, dpi, tier))).save(
                os.path.join(a.out, fn), optimize=True)
            figs.append(f'<figure><figcaption><b>{SHORT[arm]}</b> &middot; {html.escape(raster.ARMS[arm][2])}'
                        f'</figcaption><div class="strip"><img src="{fn}" alt="{key} {arm}"></div></figure>')
        tier_name = {"1x": "1x (X3)", "2x": "2x tier (phone)", "9px": "9 px"}[tier]
        secs.append(f'<section><h2>{key} &middot; {ppem:.2f} ppem &middot; {tier_name}{note}</h2>'
                    + "".join(figs) + "</section>")
    tables = open(a.tables).read() if a.tables else ""
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Albo Hinting Arms</title>
<style>
:root {{ --bg:#fbfbf9; --fg:#1d1d1b; --mute:#66665f; --rule:#dcdcd6; --card:#ffffff; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ --bg:#141414; --fg:#e6e6e2; --mute:#9a9a94; --rule:#333; --card:#1d1d1d; }} }}
:root[data-theme="dark"] {{ --bg:#141414; --fg:#e6e6e2; --mute:#9a9a94; --rule:#333; --card:#1d1d1d; }}
body {{ background:var(--bg); color:var(--fg); font:16px/1.5 -apple-system, system-ui, sans-serif; margin:0; padding:24px 16px 64px; }}
main {{ max-width:1000px; margin:0 auto; }}
h1 {{ font-size:1.5rem; margin:0 0 .25rem; }} h2 {{ font-size:1.05rem; margin:2rem 0 .5rem; border-top:1px solid var(--rule); padding-top:1rem; }}
p, li {{ color:var(--fg); }} .mute {{ color:var(--mute); font-size:.9rem; }}
figure {{ margin:.5rem 0 1rem; }} figcaption {{ font-size:.85rem; color:var(--mute); margin:.25rem 0; }}
.strip {{ display:block; overflow-x:auto; background:#fff; padding:4px; border:1px solid var(--rule); }}
.strip img {{ display:block; image-rendering:pixelated; }}
table {{ border-collapse:collapse; font-size:.85rem; margin:.5rem 0 1rem; display:block; overflow-x:auto; }}
th, td {{ border-bottom:1px solid var(--rule); padding:3px 8px; text-align:right; white-space:nowrap; }}
th:first-child, td:first-child {{ text-align:left; }}
.bad {{ color:#c0392b; font-weight:600; }}
</style></head><body><main>
<h1>Albo hinting arms</h1>
<p class="mute">Round-399 Regular and Italic. Every glyph is the firmware converter's own 2-bit bitmap
(<code>fontconvert_sdcard.py</code>, reproduced bit for bit: 27,504 glyph renders compared, 0 differ). Layout is HarfBuzz,
shared by every arm. Native pixels, lossless PNG; the strips are never scaled by the page (scroll sideways on a phone).
Four levels drawn on a neutral ramp, not the app's inks.</p>
<p class="mute"><b>TODAY</b>: FreeType default load, no bytecode in the font, so the autohinter at NORMAL target (the shipped path).
<b>TTFAUTOHINT</b>: ttfautohint 1.8.4 bytecode, default settings, same converter.
<b>LIGHT</b>: the autohinter at LIGHT target (vertical only). <b>NO HINTING</b>: FT_LOAD_NO_HINTING.</p>
{tables}
<h2>The words, 4&times;</h2>
{''.join(crop_html)}
{''.join(secs)}
</main></body></html>"""
    open(os.path.join(a.out, "index.html"), "w").write(page)
    print(os.path.join(a.out, "index.html"))


if __name__ == "__main__":
    main()
