"""Round 3: the pangram in each of the nine kept cuts, large and at 13 pt on
the reader's four-level e-ink at 2x (54 px em, the X3's measure)."""
import base64, html, io, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wedge, alphabet
from PIL import Image, ImageDraw

PANGRAM = ("Beyond the quiet fjord, a jackdaw skims low over black water, while the "
           "last light of dusk hazes the zinc-gray peaks and a vixen crosses the frozen marsh.")
KEPT = [3, 5, 8, 10, 11, 13, 14, 15, 19]
EM_PX = 54            # 13 pt at the shipped 2x render scale
MEASURE_PX = 936      # the X3 text block at 2x: 1056 - 2 x 60
LINE_GAP = 1.42

def svg_block(p, scale=0.062, max_units=13000):
    lines = alphabet.wrap(p, PANGRAM, max_units)
    lh = (p["asc"] + p["desc"]) * LINE_GAP
    top = p["asc"] + 40
    out = []; W = 0
    for i, ln in enumerate(lines):
        polys, adv = alphabet.layout(p, ln)
        W = max(W, adv)
        oy = i * lh
        for poly in polys:
            pts = " ".join(f"{(x+20)*scale:.1f},{(top - y + oy)*scale:.1f}" for x, y in poly)
            out.append(f'<polygon points="{pts}"/>')
    w = (W + 40) * scale; h = (top + p["desc"] + 60 + (len(lines) - 1) * lh) * scale
    return f'<svg viewBox="0 0 {w:.0f} {h:.0f}" width="{w:.0f}" height="{h:.0f}" fill="currentColor">{"".join(out)}</svg>'

def eink_block(p, ss=8):
    scale = EM_PX * ss / 1000.0
    max_units = MEASURE_PX / EM_PX * 1000.0
    lines = alphabet.wrap(p, PANGRAM, max_units)
    lh = (p["asc"] + p["desc"]) * LINE_GAP
    top = p["asc"] + 40
    Hu = top + p["desc"] + 40 + (len(lines) - 1) * lh
    W, H = int((MEASURE_PX * ss)), int(Hu * scale)
    im = Image.new("L", (W, H), 0); dr = ImageDraw.Draw(im)
    for i, ln in enumerate(lines):
        polys, adv = alphabet.layout(p, ln)
        oy = i * lh
        for poly in polys:
            dr.polygon([((x + 10) * scale, (top - y + oy) * scale) for x, y in poly], fill=255)
    small = im.resize((W // ss, H // ss), Image.BOX)
    px = small.load(); out = Image.new("L", small.size, 255); po = out.load()
    for y in range(small.size[1]):
        for x in range(small.size[0]):
            c = px[x, y] / 255.0
            po[x, y] = 255 if c < 0.108 else 200 if c < 0.42 else 96 if c < 0.812 else 0
    return out, len(lines)

def b64(im):
    buf = io.BytesIO(); im.save(buf, format="PNG"); return base64.b64encode(buf.getvalue()).decode()

def page():
    tiles = []
    for n in KEPT:
        name, blurb, p = wedge.option_params(n - 1)
        num, title = name.split(maxsplit=1)
        svg = svg_block(p)
        ek, nlines = eink_block(p)
        crop = ek.crop((0, 0, min(ek.width, 468), min(ek.height, 2 * int((p["asc"] + p["desc"]) * LINE_GAP * EM_PX / 1000) + 8)))
        mag = crop.resize((crop.width * 2, crop.height * 2), Image.NEAREST)
        tiles.append(f'''<section class="cut">
  <h2><span class="num">{num}</span>{html.escape(title)} <span class="blurb">{html.escape(blurb)}</span></h2>
  <div class="word">{svg}</div>
  <figure>
    <div class="scroll"><img src="data:image/png;base64,{b64(ek)}" width="{ek.width}" height="{ek.height}" alt=""></div>
    <figcaption>EVIDENCE · 13 pt at the reader's 2x, the X3's 936 px measure, four levels, {nlines} lines, native pixels (scrolls sideways)</figcaption>
  </figure>
  <figure>
    <div class="scroll"><img src="data:image/png;base64,{b64(mag)}" width="{mag.width}" height="{mag.height}" alt=""></div>
    <figcaption>EVIDENCE · the first two lines' left half, magnified 2x NEAREST</figcaption>
  </figure>
</section>''')
    return f'''<title>Fjord Pangram</title>
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
.blurb{{display:block;font-weight:normal;color:var(--soft);font-size:13px}}
.word{{color:var(--ink);overflow-x:auto}}
.word svg{{display:block;max-width:100%;height:auto}}
figure{{margin:12px 0 0}}
.scroll{{overflow-x:auto}}
.scroll img{{display:block;image-rendering:pixelated;image-rendering:crisp-edges;background:#F9F3E9;max-width:none}}
figcaption{{font-size:12px;letter-spacing:.02em;color:var(--soft);margin-top:5px}}
</style>
<main>
<h1>Fjord Pangram</h1>
<p class="lede">Round 3: the whole lowercase now exists on the same pen, so each of the nine kept cuts sets the test sentence. The vectors show the shape; the e-ink strips are the evidence: 13 pt at the shipped 2x on the X3's measure, coverage quantized to the page's four levels, native pixels.</p>
{''.join(tiles)}
</main>'''

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
    open(os.path.join(out, "fjord-pangram.html"), "w").write(page())
    ek, n = eink_block(wedge.option_params(18)[2])
    ek.save(os.path.join(out, "eink19_pangram.png"))
    print("ok", n, "lines")
