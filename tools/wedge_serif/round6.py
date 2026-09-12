"""Round 6: the second drawing model (alphabet2) on the matched cut 3, as a
regular and a bold: the word, the alphabet, the pangram in vectors and at
13 pt on four-level e-ink, with LibrisADF and Atkinson Next on the same
pipeline beside it."""
import base64, html, io, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import round3, round4, round5, alphabet2 as A
from PIL import Image, ImageDraw

PANGRAM = round3.PANGRAM; EM_PX = round3.EM_PX; MEASURE_PX = round3.MEASURE_PX; LINE_GAP = 1.42

def svg_lines(p, lines, scale):
    lh = (p["asc"] + p["desc"]) * LINE_GAP; top = p["asc"] + 40
    out = []; W = 0
    for i, ln in enumerate(lines):
        polys, adv = A.layout(p, ln); W = max(W, adv); oy = i * lh
        for poly in polys:
            out.append('<polygon points="' + " ".join(f"{(x+20)*scale:.1f},{(top - y + oy)*scale:.1f}" for x, y in poly) + '"/>')
    w = (W + 40) * scale; h = (top + p["desc"] + 60 + (len(lines) - 1) * lh) * scale
    return f'<svg viewBox="0 0 {w:.0f} {h:.0f}" width="{w:.0f}" height="{h:.0f}" fill="currentColor">{"".join(out)}</svg>'

def eink(p, ss=8):
    scale = EM_PX * ss / 1000.0
    lines = A.wrap(p, PANGRAM, MEASURE_PX / EM_PX * 1000.0)
    lh = (p["asc"] + p["desc"]) * LINE_GAP; top = p["asc"] + 40
    Hu = top + p["desc"] + 40 + (len(lines) - 1) * lh
    W, H = MEASURE_PX * ss, int(Hu * scale)
    im = Image.new("L", (W, H), 0); dr = ImageDraw.Draw(im)
    for i, ln in enumerate(lines):
        polys, adv = A.layout(p, ln); oy = i * lh
        for poly in polys:
            dr.polygon([((x + 10) * scale, (top - y + oy) * scale) for x, y in poly], fill=255)
    small = im.resize((W // ss, H // ss), Image.BOX); px = small.load()
    out = Image.new("L", small.size, 255); po = out.load()
    for y in range(small.size[1]):
        for x in range(small.size[0]):
            c = px[x, y] / 255.0
            po[x, y] = 255 if c < 0.108 else 200 if c < 0.42 else 96 if c < 0.812 else 0
    return out, len(lines)

def fig(ek, cap):
    return f'<figure><div class="scroll"><img src="data:image/png;base64,{round3.b64(ek)}" width="{ek.width}" height="{ek.height}" alt=""></div><figcaption>{cap}</figcaption></figure>'

def block(title, sub, p):
    ek, n = eink(p)
    lh_px = int((p["asc"] + p["desc"]) * LINE_GAP * EM_PX / 1000)
    crop = ek.crop((0, 0, min(ek.width, 468), min(ek.height, 2 * lh_px + 8)))
    mag = crop.resize((crop.width * 2, crop.height * 2), Image.NEAREST)
    return f'''<section class="cut">
  <h2>{html.escape(title)} <span class="blurb">{html.escape(sub)}</span></h2>
  <div class="word big">{svg_lines(p, ["fjord"], 0.5)}</div>
  <div class="word">{svg_lines(p, ["abcdefghijklm", "nopqrstuvwxyz.,-"], 0.19)}</div>
  <div class="word">{svg_lines(p, A.wrap(p, PANGRAM, 13000), 0.062)}</div>
  {fig(ek, f"EVIDENCE · 13 pt at 2x, 936 px measure, four levels, {n} lines, native pixels")}
  {fig(mag, "EVIDENCE · first two lines, left half, 2x NEAREST")}
</section>'''

def page():
    p = dict(round5.MATCHED)
    tiles = [block("3, second drawing, Regular", f"stem {p['stem']}, contrast {p['contrast']}, stress {p['stress']}, x-height {p['xh']}, width {p['width']}, fit {p['fit']}", p),
             block("3, second drawing, Bold", "stem x1.6, contrast −0.12, width x1.05", round4.bold_of(p))]
    for title, path in round5.REAL[1:]:
        if os.path.exists(path):
            ek, n = round5.eink_real(path)
            tiles.append(f'<section class="cut"><h2>{html.escape(title)} <span class="blurb">the real outlines, same pipeline</span></h2>{fig(ek, f"EVIDENCE · 13 pt at 2x, four levels, {n} lines, native pixels")}</section>')
    return f'''<title>Fjord, Second Drawing</title>
<style>
:root{{--paper:#F9F3E9;--ink:#5C332B;--soft:#8A6A62;--rule:#E4D8C8}}
@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{--paper:#171B1B;--ink:#CFD4CC;--soft:#93A09B;--rule:#2B3331}}}}
:root[data-theme="dark"]{{--paper:#171B1B;--ink:#CFD4CC;--soft:#93A09B;--rule:#2B3331}}
body{{background:var(--paper);color:var(--ink);margin:0;padding:20px 14px 60px;font:15px/1.45 -apple-system,"Helvetica Neue",Arial,sans-serif}}
main{{max-width:980px;margin:0 auto}} h1{{font-size:24px;margin:0 0 4px}}
.lede{{color:var(--soft);max-width:64ch;margin:0 0 26px}}
.cut{{border-top:1px solid var(--rule);padding:16px 0 10px}} h2{{font-size:17px;margin:0 0 10px}}
.blurb{{display:block;font-weight:normal;color:var(--soft);font-size:13px;font-variant-numeric:tabular-nums}}
.word{{color:var(--ink);overflow-x:auto;margin-bottom:10px}} .word svg{{display:block;max-width:100%;height:auto}}
figure{{margin:12px 0 0}} .scroll{{overflow-x:auto}}
.scroll img{{display:block;image-rendering:pixelated;image-rendering:crisp-edges;background:#F9F3E9;max-width:none}}
figcaption{{font-size:12px;letter-spacing:.02em;color:var(--soft);margin-top:5px}}
</style>
<main>
<h1>Fjord, Second Drawing</h1>
<p class="lede">After "try harder": a second drawing model. Continuous thick-thin along every curve, arches and bowls that taper into their stems, bracketed wedge serifs with a concave fillet, pen-angle cuts instead of square ends, overshoots, one smooth spine for the s, the z's diagonal at stem weight. Cut 3 at the S-tier proportions, regular and bold; LibrisADF and Atkinson Next 365 below on the same 13 pt four-level pipeline.</p>
{''.join(tiles)}
</main>'''

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
    open(os.path.join(out, "fjord-second.html"), "w").write(page())
    ek, n = eink(dict(round5.MATCHED)); ek.save(os.path.join(out, "eink_v2.png")); print("ok", n)
