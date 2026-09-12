"""Round 5: cut 3 matched to the installed S-tier families' medians, shown
beside three of them on the same 13 pt four-level e-ink pipeline."""
import base64, html, io, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wedge, alphabet, round3, round4
from PIL import Image, ImageDraw, ImageFont

# Medians of eight installed regulars measured 2026-09-12 at a 1000 px em
# (Coelacanth, TeXGyreSchola, LibreFranklin, LibrisADF, TeXGyreHeros,
# Almendra, AtkinsonHyperlegibleNext; Inknut's row was a broken read):
# xh 495, asc 730, desc 196, stem 84, n-counter 220, o-width 452, avg
# advance 500, and two n's spaced at ~0.8 of the counter. width and fit
# below were solved numerically so the cut's own average advance and n
# advance land on 500 and 566 (first guess was 0.92 / 0.8 and ran wide).
MATCHED = dict(wedge.option_params(2)[2])
MATCHED.update(xh=495, asc=730, desc=200, stem=88, width=0.85, n_width=340, fit=0.8,
               contrast=0.45, stress=20, flare=0.18, wedge_len=0.75, wedge_depth=1.5, serif_drop=0.22)

SCRIPTS = os.path.expanduser("~/src/crosspoint-reader/lib/EpdFont/scripts/downloaded_fonts")
REAL = [
    ("Coelacanth (S tier)", f"{SCRIPTS}/Coelacanth/Coelacanth.otf"),
    ("LibrisADF (S tier)", f"{SCRIPTS}/LibrisADF/LibrisADFStd-Regular.otf"),
    ("Atkinson Hyperlegible Next 365 (S tier)", (__import__("glob").glob(os.path.expanduser("~/src/crosspoint-reader/lib/EpdFont/scripts/instanced_fonts/AtkinsonHyperlegibleNext/regular_wght365_*.ttf")) or ["missing"])[0]),
]

def eink_real(path, em_px=round3.EM_PX, measure=round3.MEASURE_PX, ss=8):
    font = ImageFont.truetype(path, em_px * ss)
    words = round3.PANGRAM.split(' '); lines = []; cur = ''
    def w(t): return font.getlength(t) / ss
    for wd in words:
        t = (cur + ' ' + wd).strip()
        if w(t) <= measure or not cur: cur = t
        else: lines.append(cur); cur = wd
    lines.append(cur)
    lh = int(em_px * 1.42)
    H = lh * len(lines) + em_px // 2
    im = Image.new('L', (measure * ss, H * ss), 0); d = ImageDraw.Draw(im)
    for i, ln in enumerate(lines):
        d.text((0, (i * lh + em_px * 0.1) * ss), ln, font=font, fill=255)
    small = im.resize((measure, H), Image.BOX); px = small.load()
    out = Image.new('L', small.size, 255); po = out.load()
    for y in range(H):
        for x in range(measure):
            c = px[x, y] / 255.0
            po[x, y] = 255 if c < 0.108 else 200 if c < 0.42 else 96 if c < 0.812 else 0
    return out, len(lines)

def tile(title, sub, ek, nlines, svg=None):
    crop = ek.crop((0, 0, min(ek.width, 468), min(ek.height, 2 * int(round3.EM_PX * 1.42) + 8)))
    mag = crop.resize((crop.width * 2, crop.height * 2), Image.NEAREST)
    return f'''<section class="cut">
  <h2>{html.escape(title)} <span class="blurb">{html.escape(sub)}</span></h2>
  {f'<div class="word">{svg}</div>' if svg else ''}
  <figure><div class="scroll"><img src="data:image/png;base64,{round3.b64(ek)}" width="{ek.width}" height="{ek.height}" alt=""></div>
  <figcaption>EVIDENCE · 13 pt at 2x, 936 px measure, four levels, {nlines} lines, native pixels</figcaption></figure>
  <figure><div class="scroll"><img src="data:image/png;base64,{round3.b64(mag)}" width="{mag.width}" height="{mag.height}" alt=""></div>
  <figcaption>EVIDENCE · first two lines, left half, 2x NEAREST</figcaption></figure>
</section>'''

def page():
    tiles = []
    for weight, p in (("Regular", MATCHED), ("Bold", round4.bold_of(MATCHED))):
        ek, n = round3.eink_block(p)
        tiles.append(tile(f"3 matched, {weight}", f"stem {p['stem']}, x-height {p['xh']}, asc {p['asc']}, desc {p['desc']}, o-width {int(490*p['width'])}, fit 0.8 of the n-counter", ek, n, round3.svg_block(p)))
    for title, path in REAL:
        if not os.path.exists(path):
            tiles.append(f'<section class="cut"><h2>{html.escape(title)} <span class="blurb">not on disk: {html.escape(path)}</span></h2></section>'); continue
        ek, n = eink_real(path)
        tiles.append(tile(title, "the real outlines, same pipeline", ek, n))
    return f'''<title>Fjord Matched</title>
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
.blurb{{display:block;font-weight:normal;color:var(--soft);font-size:13px;font-variant-numeric:tabular-nums}}
.word{{color:var(--ink);overflow-x:auto}} .word svg{{display:block;max-width:100%;height:auto}}
figure{{margin:12px 0 0}} .scroll{{overflow-x:auto}}
.scroll img{{display:block;image-rendering:pixelated;image-rendering:crisp-edges;background:#F9F3E9;max-width:none}}
figcaption{{font-size:12px;letter-spacing:.02em;color:var(--soft);margin-top:5px}}
</style>
<main>
<h1>Fjord Matched</h1>
<p class="lede">Round 5. Cut 3 pulled toward the installed S-tier medians (x-height 495, ascender 730, descender 196, stem 84, n-counter 220, o-width 452, letters fitted at 0.8 of the n-counter as the real faces are), as a regular and a bold, then three S-tier faces set through the same 13 pt four-level pipeline for the comparison.</p>
{''.join(tiles)}
</main>'''

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
    open(os.path.join(out, "fjord-matched.html"), "w").write(page())
    ek, n = round3.eink_block(MATCHED); ek.save(os.path.join(out, "eink3m.png"))
    ek2, n2 = eink_real(REAL[1][1]); ek2.save(os.path.join(out, "eink_libris.png"))
    print("ok", n, n2)
