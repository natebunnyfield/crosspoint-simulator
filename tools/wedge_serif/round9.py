"""Round 9: forty humanist variants of 'Hamburgers in a fjord.'

Owner 2026-09-12: restrict the rhythm to the humanist end; keep the charm of
naively assembled shapes and their defects as choices; take risks; stay
legible; a longform text face. So: stress 18-34, contrast 0.38-0.65, pen
power 0.85-1.1 (calligraphic, never grotesque), x-height 440-510, moderate
width, wedge OR flare serifs, and one deliberate "defect" axis per variant
(a naive o with its seam, raw butted joins, no overshoot, square cuts,
straight unbracketed wedges, serifs on one side only). Eight lineages x five.
"""
import html, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import round3, round6, round8, alphabet2 as A
from PIL import Image, ImageDraw

STRING = "Hamburgers in a fjord."
BASE = dict(xh=480, asc=740, desc=215, stem=92, contrast=0.5, stress=24, flare=0.18, width=0.9,
            n_width=340, fit=0.8, wedge_len=0.75, wedge_depth=1.5, serif_drop=0.25, bowl_k=2.15,
            power=1.0, serif_style="wedge", arch_start=0.55, fillet=0.55, cut_deg=14, slant=0,
            wedge_tip=0.0, foot_scale=0.85, terminal="cut")
def v(**kw):
    p = dict(BASE); p.update(kw); return p

LINEAGES = [
 ("V", "Venetian",   dict(xh=450, asc=760, desc=245, stem=84, contrast=0.55, stress=30, power=0.92, arch_start=0.48, serif_drop=0.32, fillet=0.6)),
 ("J", "Jenson-warm", dict(xh=462, asc=750, desc=230, stem=96, contrast=0.48, stress=28, power=0.95, width=0.93, arch_start=0.52, fillet=0.6, wedge_len=0.7)),
 ("D", "Dutch-sturdy", dict(xh=500, asc=730, desc=205, stem=104, contrast=0.52, stress=20, power=1.05, width=0.9, cut_deg=16, bowl_k=2.2)),
 ("C", "Calligraphic", dict(xh=475, asc=745, desc=225, stem=100, contrast=0.64, stress=32, power=0.86, wedge_len=0.9, wedge_depth=1.4, serif_drop=0.4, cut_deg=22)),
 ("A", "Albertus-flare", dict(xh=490, asc=735, desc=210, stem=94, contrast=0.4, stress=20, power=1.05, serif_style="flare", wedge_len=0.45, flare=0.3)),
 ("B", "Book-quiet",  dict(xh=485, asc=740, desc=215, stem=90, contrast=0.45, stress=22, power=1.0, width=0.9, wedge_len=0.65, wedge_depth=1.3, serif_drop=0.2)),
 ("I", "Inscriptional", dict(xh=470, asc=750, desc=220, stem=98, contrast=0.5, stress=24, power=1.0, flare=0.32, wedge_len=1.0, wedge_depth=1.2, serif_drop=0.15, fillet=0.35, cut_deg=18)),
 ("O", "Open-large-x", dict(xh=510, asc=728, desc=200, stem=92, contrast=0.42, stress=22, power=1.05, width=0.95, n_width=350, arch_start=0.6, bowl_k=2.1)),
]
# five mutations per lineage: one defect axis each, plus a weight or width nudge
MUTATIONS = [
 ("1", "clean",                dict()),
 ("2", "naive o, raw joins",   dict(naive_o=True, raw_joins=True)),
 ("3", "no overshoot, square cuts, straight wedges", dict(overshoot=0, cut_deg=0, fillet=0.0)),
 ("4", "heavier, deeper brackets", lambda p: dict(stem=int(p["stem"] * 1.14), contrast=max(0.3, p["contrast"] - 0.06), wedge_depth=p["wedge_depth"] * 1.25, fillet=min(0.8, p["fillet"] + 0.15))),
 ("5", "lighter, wider, longer wedges", lambda p: dict(stem=int(p["stem"] * 0.88), width=p["width"] * 1.05, wedge_len=p["wedge_len"] * 1.3, serif_drop=p["serif_drop"] + 0.1)),
]

def population():
    pop = []
    for lk, lname, lover in LINEAGES:
        base = v(**lover)
        for mk, mname, mover in MUTATIONS:
            p = dict(base); p.update(mover(base) if callable(mover) else mover)
            pop.append((f"{lk}{mk}", f"{lname} · {mname}", p))
    return pop

def eink_line(p, text, ss=8):
    scale = round3.EM_PX * ss / 1000.0
    polys, adv = A.layout(p, text); top = p["asc"] + 40; Hu = top + p["desc"] + 40
    W, H = int((adv + 20) * scale), int(Hu * scale)
    im = Image.new("L", (W, H), 0); dr = ImageDraw.Draw(im)
    for poly in polys: dr.polygon([((x + 10) * scale, (top - y) * scale) for x, y in poly], fill=255)
    small = im.resize((W // ss, H // ss), Image.BOX); px = small.load()
    out = Image.new("L", small.size, 255); po = out.load()
    for y in range(small.size[1]):
        for x in range(small.size[0]):
            c = px[x, y] / 255.0
            po[x, y] = 255 if c < 0.108 else 200 if c < 0.42 else 96 if c < 0.812 else 0
    return out

def svg_word(p, text, scale):
    polys, adv = A.layout(p, text); top = p["asc"] + 40
    out = ['<polygon points="' + " ".join(f"{(x+20)*scale:.1f},{(top - y)*scale:.1f}" for x, y in poly) + '"/>' for poly in polys]
    w = (adv + 40) * scale; h = (top + p["desc"] + 60) * scale
    return f'<svg viewBox="0 0 {w:.0f} {h:.0f}" width="{w:.0f}" height="{h:.0f}" fill="currentColor" fill-rule="evenodd">{"".join(out)}</svg>'

def page():
    tiles = []
    for key, name, p in population():
        ek = eink_line(p, STRING); mag = ek.resize((ek.width * 2, ek.height * 2), Image.NEAREST)
        tiles.append(f'''<figure class="opt">
  <div class="word">{svg_word(p, STRING, 0.16)}</div>
  <div class="eink"><img src="data:image/png;base64,{round3.b64(mag)}" width="{mag.width}" height="{mag.height}" alt=""></div>
  <figcaption><span class="num">{key}</span> <b>{html.escape(name)}</b><span class="blurb">stem {p["stem"]} · contrast {p["contrast"]:.2f} · stress {p["stress"]}° · x-height {p["xh"]} · {p["serif_style"]} · e-ink line is 13 pt at 2x, four levels, shown 2x NEAREST</span></figcaption>
</figure>''')
    return f'''<title>Hamburgers Forty</title>
<style>
:root{{--paper:#F9F3E9;--ink:#5C332B;--soft:#8A6A62;--rule:#E4D8C8}}
@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{--paper:#171B1B;--ink:#CFD4CC;--soft:#93A09B;--rule:#2B3331}}}}
:root[data-theme="dark"]{{--paper:#171B1B;--ink:#CFD4CC;--soft:#93A09B;--rule:#2B3331}}
body{{background:var(--paper);color:var(--ink);margin:0;padding:20px 14px 60px;font:15px/1.45 -apple-system,"Helvetica Neue",Arial,sans-serif}}
main{{max-width:1180px;margin:0 auto}} h1{{font-size:24px;margin:0 0 4px}}
.lede{{color:var(--soft);max-width:64ch;margin:0 0 22px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:22px 26px}}
.opt{{margin:0;border-top:1px solid var(--rule);padding-top:12px}}
.word{{color:var(--ink);overflow-x:auto}} .word svg{{display:block;max-width:100%;height:auto}}
.eink{{overflow-x:auto;margin-top:6px}} .eink img{{display:block;image-rendering:pixelated;image-rendering:crisp-edges;background:#F9F3E9;max-width:none}}
figcaption{{margin-top:6px;font-size:13px}} .num{{display:inline-block;min-width:3ch;color:var(--soft);margin-right:6px}}
.blurb{{display:block;color:var(--soft);font-variant-numeric:tabular-nums}}
</style>
<main>
<h1>Hamburgers Forty</h1>
<p class="lede">Round 9. Eight humanist lineages, five mutations each: a clean cut, a naive cut (the o keeps its seam, joins are butted), a hard cut (no overshoot, square ends, straight wedges), a heavier cut with deeper brackets, a lighter and wider cut with longer wedges. Every one fits by the n at the S-tier's 0.8, the e is narrower than the o with a higher bar, and there is one capital. Vectors, then the same line at 13 pt on four-level e-ink.</p>
<div class="grid">{''.join(tiles)}</div>
</main>'''

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
    open(os.path.join(out, "hamburgers-40.html"), "w").write(page())
    pop = population(); tiles = []
    for key, name, p in pop:
        polys, adv = A.layout(p, STRING); scale = 0.11; ss = 3; top = p["asc"] + 60
        W, H = int((adv + 60) * scale), int((top + p["desc"] + 80) * scale)
        im = Image.new("L", (W * ss, H * ss), 255); d = ImageDraw.Draw(im)
        for poly in polys: d.polygon([((x + 30) * scale * ss, (top - y) * scale * ss) for x, y in poly], fill=0)
        tiles.append(im.resize((W, H), Image.LANCZOS))
    Wm = max(t.width for t in tiles); Hm = max(t.height for t in tiles)
    sheet = Image.new("L", (Wm * 4, Hm * 10), 255)
    for i, t in enumerate(tiles): sheet.paste(t, ((i % 4) * Wm, (i // 4) * Hm))
    sheet.save(os.path.join(out, "sheet40.png")); print("ok", len(pop), sheet.size)
