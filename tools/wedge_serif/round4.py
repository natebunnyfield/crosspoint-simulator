"""Round 4: the four kept cuts (3, 5, 13, 19), each as a regular and a bold,
setting the pangram large and at 13 pt on four-level e-ink."""
import base64, html, io, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wedge, alphabet, round3
from PIL import Image

KEPT = [3, 5, 13, 19]

def bold_of(p):
    """Owner 2026-09-12: 'we need a regular and a bold'. Stem x1.6, contrast
    eased a fifth so the hairlines keep up, 5% wider so the counters survive;
    the wedges scale with the stem on their own."""
    b = dict(p)
    b["stem"] = int(round(p["stem"] * 1.6))
    b["contrast"] = max(0.0, p["contrast"] - 0.12)
    b["width"] = p["width"] * 1.05
    return b

def page():
    tiles = []
    for n in KEPT:
        name, blurb, reg = wedge.option_params(n - 1)
        num, title = name.split(maxsplit=1)
        for weight, p in (("Regular", reg), ("Bold", bold_of(reg))):
            svg = round3.svg_block(p)
            ek, nlines = round3.eink_block(p)
            lh_px = int((p["asc"] + p["desc"]) * round3.LINE_GAP * round3.EM_PX / 1000)
            crop = ek.crop((0, 0, min(ek.width, 468), min(ek.height, 2 * lh_px + 8)))
            mag = crop.resize((crop.width * 2, crop.height * 2), Image.NEAREST)
            tiles.append(f'''<section class="cut">
  <h2><span class="num">{num}</span>{html.escape(title)} <span class="wt">{weight}</span> <span class="blurb">stem {p["stem"]}, contrast {p["contrast"]:.2f}, stress {p["stress"]}, x-height {p["xh"]}</span></h2>
  <div class="word">{svg}</div>
  <figure>
    <div class="scroll"><img src="data:image/png;base64,{round3.b64(ek)}" width="{ek.width}" height="{ek.height}" alt=""></div>
    <figcaption>EVIDENCE · 13 pt at the reader's 2x, the X3's 936 px measure, four levels, {nlines} lines, native pixels (scrolls sideways)</figcaption>
  </figure>
  <figure>
    <div class="scroll"><img src="data:image/png;base64,{round3.b64(mag)}" width="{mag.width}" height="{mag.height}" alt=""></div>
    <figcaption>EVIDENCE · first two lines, left half, 2x NEAREST</figcaption>
  </figure>
</section>''')
    return f'''<title>Fjord Regular and Bold</title>
<style>
:root{{--paper:#F9F3E9;--ink:#5C332B;--soft:#8A6A62;--rule:#E4D8C8}}
@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{--paper:#171B1B;--ink:#CFD4CC;--soft:#93A09B;--rule:#2B3331}}}}
:root[data-theme="dark"]{{--paper:#171B1B;--ink:#CFD4CC;--soft:#93A09B;--rule:#2B3331}}
body{{background:var(--paper);color:var(--ink);margin:0;padding:20px 14px 60px;font:15px/1.45 -apple-system,"Helvetica Neue",Arial,sans-serif}}
main{{max-width:980px;margin:0 auto}}
h1{{font-size:24px;margin:0 0 4px}}
.lede{{color:var(--soft);max-width:64ch;margin:0 0 26px}}
.cut{{border-top:1px solid var(--rule);padding:16px 0 10px}}
h2{{font-size:17px;margin:0 0 10px}}
.num{{color:var(--soft);font-variant-numeric:tabular-nums;margin-right:8px}}
.wt{{font-weight:normal;color:var(--soft);margin-left:6px}}
.blurb{{display:block;font-weight:normal;color:var(--soft);font-size:13px;font-variant-numeric:tabular-nums}}
.word{{color:var(--ink);overflow-x:auto}}
.word svg{{display:block;max-width:100%;height:auto}}
figure{{margin:12px 0 0}}
.scroll{{overflow-x:auto}}
.scroll img{{display:block;image-rendering:pixelated;image-rendering:crisp-edges;background:#F9F3E9;max-width:none}}
figcaption{{font-size:12px;letter-spacing:.02em;color:var(--soft);margin-top:5px}}
</style>
<main>
<h1>Fjord Regular and Bold</h1>
<p class="lede">Round 4. Four cuts kept (3, 5, 13, 19), each now a regular and a bold. Three rulings applied since round 3: wedge serifs on z, v, w, x, y and k; fitting by the n (the air between letters equals the air inside the n); and the bold, at 1.6x the stem. Vectors first, then the e-ink evidence at 13 pt on the X3's measure.</p>
{''.join(tiles)}
</main>'''

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
    open(os.path.join(out, "fjord-weights.html"), "w").write(page())
    b = bold_of(wedge.option_params(18)[2])
    ek, n = round3.eink_block(b); ek.save(os.path.join(out, "eink19_bold.png"))
    print("ok")
