"""Round 10: ten iterations from B5 (Book-quiet, lighter/wider/longer
wedges) to a garalde text target: the proportions and stress of Garamond
and Sabon -- small x-height, tall ascenders and deep descenders, moderate-
high oblique contrast, bracketed wedge serifs, high rounded arches -- as a
brief, never a render. Linear on every numeric knob, t = 0 .. 1 in ten."""
import html, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import round3, round9, alphabet2 as A
from PIL import Image

START = {k: p for k, n, p in round9.population()}["B5"]
TARGET = dict(START)
TARGET.update(xh=415, asc=762, desc=250, stem=82, contrast=0.6, stress=26, power=0.95, width=0.9,
              n_width=350, fit=0.8, wedge_len=0.85, wedge_depth=1.7, serif_drop=0.28, fillet=0.65,
              cut_deg=20, arch_start=0.52, bowl_k=2.1, flare=0.14, overshoot=14)

def lerp(a, b, t):
    if isinstance(a, bool) or isinstance(a, str) or a is None: return a if t < 0.5 else b
    v = a + (b - a) * t
    return int(round(v)) if isinstance(a, int) and isinstance(b, int) else round(v, 3)

def steps(n=10):
    out = []
    for i in range(n):
        t = i / (n - 1)
        p = {k: lerp(START[k], TARGET.get(k, START[k]), t) for k in START}
        for k in TARGET:
            if k not in p: p[k] = lerp(START.get(k, TARGET[k]), TARGET[k], t)
        out.append((f"B5.{i}", t, p))
    return out

def page():
    tiles = []
    for key, t, p in steps():
        ek = round9.eink_line(p, round9.STRING); mag = ek.resize((ek.width * 2, ek.height * 2), Image.NEAREST)
        tiles.append(f'''<figure class="opt">
  <div class="word">{round9.svg_word(p, round9.STRING, 0.16)}</div>
  <div class="eink"><img src="data:image/png;base64,{round3.b64(mag)}" width="{mag.width}" height="{mag.height}" alt=""></div>
  <figcaption><span class="num">{key}</span> <b>t = {t:.2f}</b><span class="blurb">x-height {p["xh"]} · asc {p["asc"]} · desc {p["desc"]} · stem {p["stem"]} · contrast {p["contrast"]:.2f} · stress {p["stress"]}° · wedge {p["wedge_len"]:.2f}/{p["wedge_depth"]:.2f} · arch {p["arch_start"]:.2f}</span></figcaption>
</figure>''')
    return f'''<title>B5 to Garalde</title>
<style>
:root{{--paper:#F9F3E9;--ink:#5C332B;--soft:#8A6A62;--rule:#E4D8C8}}
@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{--paper:#171B1B;--ink:#CFD4CC;--soft:#93A09B;--rule:#2B3331}}}}
:root[data-theme="dark"]{{--paper:#171B1B;--ink:#CFD4CC;--soft:#93A09B;--rule:#2B3331}}
body{{background:var(--paper);color:var(--ink);margin:0;padding:20px 14px 60px;font:15px/1.45 -apple-system,"Helvetica Neue",Arial,sans-serif}}
main{{max-width:980px;margin:0 auto}} h1{{font-size:24px;margin:0 0 4px}}
.lede{{color:var(--soft);max-width:64ch;margin:0 0 22px}}
.opt{{margin:0;border-top:1px solid var(--rule);padding-top:12px;margin-bottom:18px}}
.word{{color:var(--ink);overflow-x:auto}} .word svg{{display:block;max-width:100%;height:auto}}
.eink{{overflow-x:auto;margin-top:6px}} .eink img{{display:block;image-rendering:pixelated;image-rendering:crisp-edges;background:#F9F3E9;max-width:none}}
figcaption{{margin-top:6px;font-size:13px}} .num{{display:inline-block;min-width:4ch;color:var(--soft);margin-right:6px}}
.blurb{{display:block;color:var(--soft);font-variant-numeric:tabular-nums}}
</style>
<main>
<h1>B5 to Garalde</h1>
<p class="lede">Round 10. B5.0 is B5 exactly; B5.9 is the garalde brief (x-height 415, ascender 762, descender 250, stem 82, contrast 0.60 at 26°, bracketed wedges 0.85 long and 1.7 deep, arches leaving the stem at 0.52). Every numeric knob moves linearly between them. Vectors, then the same line at 13 pt on four-level e-ink, 2x NEAREST.</p>
{''.join(tiles)}
</main>'''

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
    open(os.path.join(out, "b5-garalde.html"), "w").write(page())
    from PIL import ImageDraw
    rows = []
    for key, t, p in steps():
        polys, adv = A.layout(p, round9.STRING); scale = 0.2; ss = 3; top = p["asc"] + 60
        W, H = int((adv + 60) * scale), int((top + p["desc"] + 80) * scale)
        im = Image.new("L", (W * ss, H * ss), 255); d = ImageDraw.Draw(im)
        for poly in polys: d.polygon([((x + 30) * scale * ss, (top - y) * scale * ss) for x, y in poly], fill=0)
        rows.append(im.resize((W, H), Image.LANCZOS))
    W = max(r.width for r in rows); H = sum(r.height for r in rows)
    sheet = Image.new("L", (W, H), 255); y = 0
    for r in rows: sheet.paste(r, (0, y)); y += r.height
    sheet.save(os.path.join(out, "sheet_b5.png")); print("ok", sheet.size)
