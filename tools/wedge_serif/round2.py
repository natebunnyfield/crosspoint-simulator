"""Round 2: nine lanes x two variations + two blends = twenty, each rendered
large (SVG) and at 13 pt on four-level e-ink at the shipped 2x (54 px em)."""
import base64, io, html, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wedge
from PIL import Image, ImageDraw

def lane(n): return wedge.option_params(n - 1)[2]
def var(n, **kw):
    p = dict(lane(n)); p.update(kw); return p

R2 = [
 ("3a", "Text cut, longer sharper wedges", var(3, wedge_len=0.7, wedge_depth=1.1)),
 ("3b", "Text cut, heavier, lower contrast", var(3, stem=120, contrast=0.4)),
 ("5a", "Calligraphic, tamed toward text", var(5, contrast=0.6, stress=25, stem=110)),
 ("5b", "Calligraphic, wedge terminals for teardrops", var(5, terminal="wedge")),
 ("8a", "Wide, a little narrower and taller", var(8, width=1.15, xh=470)),
 ("8b", "Wide, squarer bowls", var(8, bowl_k=2.4)),
 ("10a", "Classical, taller x-height", var(10, xh=455, stem=100)),
 ("10b", "Classical, flared ends and small wedges", var(10, flare=0.3, flare_shape="ends", wedge_len=0.3, wedge_depth=0.6)),
 ("11a", "Modern tall, rounder bowls", var(11, bowl_k=2.2)),
 ("11b", "Modern tall, heavier and flatter", var(11, stem=120, contrast=0.3)),
 ("13a", "Light, up to book weight", var(13, stem=82)),
 ("13b", "Light, shorter wedges, less contrast", var(13, wedge_len=0.5, wedge_depth=0.9, contrast=0.35)),
 ("14a", "Squared humanist, a touch of stress", var(14, bowl_k=2.8, stress=14)),
 ("14b", "Squared humanist, lighter with contrast", var(14, stem=105, contrast=0.45)),
 ("15a", "Reverse stress, softened", var(15, stress=100, contrast=0.4)),
 ("15b", "Reverse stress, wedge terminals", var(15, stress=110, terminal="wedge")),
 ("19a", "Sturdy text, crisper wedges", var(19, xh=500, wedge_len=0.5, wedge_depth=1.0)),
 ("19b", "Sturdy text, more contrast and flare", var(19, stem=112, contrast=0.38, flare=0.25)),
 ("A", "Blend: 3's skeleton, 5's teardrops and stress", var(3, terminal="teardrop", stress=26, contrast=0.6)),
 ("B", "Blend: 19 with a mild reverse stress from 15", var(19, stress=75, contrast=0.35)),
]

def eink(p, em_px=54, levels=(255, 200, 96, 0), ss=8):
    """Rasterize at em_px pixels per em with ss x supersampling, then quantize
    coverage to the reader's four levels the way the firmware's 2-bit page
    would carry it. Returns a PIL 'L' image at 1:1."""
    scale = em_px * ss / 1000.0
    polys, adv = wedge.glyphs(p)
    top, bot = p["asc"] + 40, -p["desc"] - 60
    W, H = int((adv + 40) * scale), int((top - bot) * scale)
    im = Image.new("L", (W, H), 0)
    dr = ImageDraw.Draw(im)
    for poly in polys:
        dr.polygon([((x + 20) * scale, (top - y) * scale) for x, y in poly], fill=255)
    small = im.resize((W // ss, H // ss), Image.BOX)  # coverage 0..255
    px = small.load()
    out = Image.new("L", small.size, 255)
    po = out.load()
    for y in range(small.size[1]):
        for x in range(small.size[0]):
            c = px[x, y] / 255.0
            # nearest of the four levels by coverage (ink fraction)
            lv = 255 if c < 0.108 else 200 if c < 0.42 else 96 if c < 0.812 else 0
            po[x, y] = lv
    return out

def b64(im):
    buf = io.BytesIO(); im.save(buf, format="PNG"); return base64.b64encode(buf.getvalue()).decode()

def page():
    tiles = []
    for key, blurb, p in R2:
        svg, adv = wedge.svg_for(p, 0.26)
        small = eink(p)
        mag = small.resize((small.width * 3, small.height * 3), Image.NEAREST)
        tiles.append(f'''<figure class="opt">
  <div class="word">{svg}</div>
  <div class="eink"><img src="data:image/png;base64,{b64(small)}" width="{small.width}" height="{small.height}" alt=""> <img class="mag" src="data:image/png;base64,{b64(mag)}" width="{mag.width}" height="{mag.height}" alt=""></div>
  <figcaption><span class="num">{key}</span> <b>{html.escape(blurb)}</b><span class="blurb">13 pt at the reader's 2x (54 px em), four levels, shown 1:1 then 3x NEAREST</span></figcaption>
</figure>''')
    return f'''<title>Fjord Twenty, Round Two</title>
<style>
:root{{--paper:#F9F3E9;--ink:#5C332B;--soft:#8A6A62;--rule:#E4D8C8}}
@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{--paper:#171B1B;--ink:#CFD4CC;--soft:#93A09B;--rule:#2B3331}}}}
:root[data-theme="dark"]{{--paper:#171B1B;--ink:#CFD4CC;--soft:#93A09B;--rule:#2B3331}}
body{{background:var(--paper);color:var(--ink);margin:0;padding:20px 14px 60px;font:15px/1.45 -apple-system,"Helvetica Neue",Arial,sans-serif}}
main{{max-width:1180px;margin:0 auto}}
h1{{font-size:24px;margin:0 0 4px}}
.lede{{color:var(--soft);max-width:64ch;margin:0 0 22px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:22px 26px}}
.opt{{margin:0;border-top:1px solid var(--rule);padding-top:12px}}
.word{{color:var(--ink);overflow-x:auto}}
.word svg{{display:block;max-width:100%;height:auto}}
.eink{{display:flex;align-items:flex-end;gap:14px;margin-top:8px;overflow-x:auto}}
.eink img{{image-rendering:pixelated;image-rendering:crisp-edges;display:block;background:#F9F3E9}}
figcaption{{margin-top:6px;font-size:13px}}
.num{{display:inline-block;min-width:3ch;color:var(--soft);font-variant-numeric:tabular-nums;margin-right:6px}}
.blurb{{display:block;color:var(--soft)}}
</style>
<main>
<h1>Fjord Twenty, Round Two</h1>
<p class="lede">All nine kept cuts, two variations each, plus two blends. Each is shown as vectors and then as the reader would actually carry it: 13 pt at the shipped 2x render scale, coverage quantized to the page's four levels, at 1:1 and magnified 3x with NEAREST. The e-ink strips are the evidence; the vectors are the shape.</p>
<div class="grid">{''.join(tiles)}</div>
</main>'''

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
    open(os.path.join(out, "fjord-round2.html"), "w").write(page())
    print("ok")
