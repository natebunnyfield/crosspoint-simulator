"""Round 8: the population from round 7 set in the evaluation sentence.
Owner 2026-09-12: 'I cannot judge this by a single word. It needs to be a
sentence with meaning behind it. Look at the most common words and
combinations of letters, digraphs, trigraphs.' The sentence was chosen from
six candidates by coverage of Norvig's top-50 bigrams (39), top-50 trigrams
(16) and the 200 commonest words (28 of its 34)."""
import html, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import round3, round6, round7, alphabet2 as A
from PIL import Image, ImageDraw

SENTENCE = ("what we make of the time we have is the only thing that was ever ours to make, "
            "and the people we made it for are the ones who will remember how it went.")
EM_PX = round3.EM_PX; MEASURE_PX = round3.MEASURE_PX; LINE_GAP = 1.42

def eink(p, text, ss=8):
    scale = EM_PX * ss / 1000.0
    lines = A.wrap(p, text, MEASURE_PX / EM_PX * 1000.0)
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

def page():
    tiles = []
    for key, blurb, p in round7.POP:
        svg = round6.svg_lines(p, A.wrap(p, SENTENCE, 15500), 0.056)
        ek, n = eink(p, SENTENCE)
        tiles.append(f'''<section class="cut">
  <h2><span class="num">{key}</span>{html.escape(blurb)} <span class="blurb">stem {p["stem"]} · contrast {p["contrast"]} · stress {p["stress"]}° · x-height {p["xh"]} · {p["serif_style"]}</span></h2>
  <div class="word">{svg}</div>
  <figure><div class="scroll"><img src="data:image/png;base64,{round3.b64(ek)}" width="{ek.width}" height="{ek.height}" alt=""></div>
  <figcaption>EVIDENCE · 13 pt at the reader's 2x, 936 px measure, four levels, {n} lines, native pixels</figcaption></figure>
</section>''')
    return f'''<title>Fjord, the Sentence</title>
<style>
:root{{--paper:#F9F3E9;--ink:#5C332B;--soft:#8A6A62;--rule:#E4D8C8}}
@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{--paper:#171B1B;--ink:#CFD4CC;--soft:#93A09B;--rule:#2B3331}}}}
:root[data-theme="dark"]{{--paper:#171B1B;--ink:#CFD4CC;--soft:#93A09B;--rule:#2B3331}}
body{{background:var(--paper);color:var(--ink);margin:0;padding:20px 14px 60px;font:15px/1.45 -apple-system,"Helvetica Neue",Arial,sans-serif}}
main{{max-width:980px;margin:0 auto}} h1{{font-size:24px;margin:0 0 4px}}
.lede{{color:var(--soft);max-width:64ch;margin:0 0 6px}}
.sentence{{font-size:17px;max-width:60ch;margin:0 0 26px}}
.cut{{border-top:1px solid var(--rule);padding:16px 0 10px}} h2{{font-size:16px;margin:0 0 10px}}
.num{{color:var(--soft);font-variant-numeric:tabular-nums;margin-right:8px}}
.blurb{{display:block;font-weight:normal;color:var(--soft);font-size:13px;font-variant-numeric:tabular-nums}}
.word{{color:var(--ink);overflow-x:auto;margin-bottom:8px}} .word svg{{display:block;max-width:100%;height:auto}}
figure{{margin:8px 0 0}} .scroll{{overflow-x:auto}}
.scroll img{{display:block;image-rendering:pixelated;image-rendering:crisp-edges;background:#F9F3E9;max-width:none}}
figcaption{{font-size:12px;letter-spacing:.02em;color:var(--soft);margin-top:5px}}
</style>
<main>
<h1>Fjord, the Sentence</h1>
<p class="lede">Round 8. The twenty-four from round 7, each setting the same sentence, chosen for coverage of the commonest English words, bigrams and trigraphs and for meaning. Lowercase only: the face has no capitals yet. Vectors first, then the 13 pt four-level e-ink block at the X3's measure.</p>
<p class="sentence">{html.escape(SENTENCE)}</p>
{''.join(tiles)}
</main>'''

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
    open(os.path.join(out, "fjord-sentence.html"), "w").write(page())
    ek, n = eink(round7.POP[16][2], SENTENCE); ek.save(os.path.join(out, "eink_D1.png"))
    print("ok", n)
