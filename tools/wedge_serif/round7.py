"""Round 7: DIVERGE. Twenty-four 'fjord' word images on the second drawing
model, each pushed toward one installed family's character -- proportions,
weight, stress, serif logic -- and each tuned to stand on its own. The
families are inspiration, never rendered. Owner 2026-09-12: 'make the wedge
serif into variations that I can pick from... an evolutionary approach.'"""
import html, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import round5, round6, alphabet2 as A

BASE = dict(round5.MATCHED)
BASE.update(xh=495, asc=730, desc=200, stem=88, contrast=0.45, stress=20, flare=0.18, width=0.85,
            n_width=340, fit=0.8, wedge_len=0.75, wedge_depth=1.5, serif_drop=0.22, bowl_k=2.15,
            power=1.15, serif_style="wedge", arch_start=0.58, fillet=0.55, cut_deg=12)

def v(**kw):
    p = dict(BASE); p.update(kw); return p

POP = [
 # --- Coelacanth (Bruce Rogers' Centaur lineage): light, low x-height, long ascenders, Venetian stress
 ("C1", "Coelacanth lineage · light Venetian", v(xh=440, asc=760, desc=250, stem=76, contrast=0.55, stress=28, power=1.0, wedge_len=0.8, wedge_depth=1.7, serif_drop=0.3, arch_start=0.5)),
 ("C2", "Coelacanth lineage · same bones, firmer", v(xh=450, asc=755, desc=240, stem=90, contrast=0.5, stress=26, power=1.05, wedge_len=0.7, wedge_depth=1.5, fillet=0.7)),
 # --- TeXGyreSchola (Century Schoolbook): round, sturdy, big counters, low contrast
 ("S1", "Schola lineage · round and sturdy", v(xh=500, asc=720, desc=205, stem=100, contrast=0.35, stress=14, width=0.95, bowl_k=2.05, wedge_len=0.6, wedge_depth=1.2, serif_drop=0.15, fillet=0.45)),
 ("S2", "Schola lineage · with a deeper bracket", v(xh=505, asc=715, desc=200, stem=104, contrast=0.4, stress=12, width=0.97, bowl_k=2.0, wedge_len=0.7, wedge_depth=1.9, serif_drop=0.1, fillet=0.75)),
 # --- LibreFranklin (grotesque): near-mono, tall x-height, wedges kept minimal
 ("F1", "Franklin lineage · grotesque bones, wedge feet", v(xh=530, asc=720, desc=175, stem=92, contrast=0.2, stress=6, power=1.4, width=0.9, wedge_len=0.5, wedge_depth=1.0, serif_drop=0.1, arch_start=0.62)),
 ("F2", "Franklin lineage · flared, no wedge", v(xh=530, asc=720, desc=175, stem=92, contrast=0.18, stress=4, power=1.4, width=0.9, serif_style="flare", wedge_len=0.35, flare=0.3)),
 # --- LibrisADF: compact, dark, narrow set
 ("L1", "Libris lineage · compact and dark", v(xh=485, asc=730, desc=195, stem=100, contrast=0.45, stress=18, width=0.78, n_width=320, wedge_len=0.65, wedge_depth=1.4, serif_drop=0.25)),
 ("L2", "Libris lineage · compact, sharper cuts", v(xh=485, asc=735, desc=195, stem=96, contrast=0.5, stress=22, width=0.8, n_width=325, wedge_len=0.8, wedge_depth=1.3, serif_drop=0.35, cut_deg=20, fillet=0.4)),
 # --- InknutJunicode: heavy old-style, big serifs, dark color
 ("I1", "Inknut lineage · heavy old style", v(xh=470, asc=745, desc=230, stem=125, contrast=0.4, stress=24, width=0.9, wedge_len=0.9, wedge_depth=1.8, serif_drop=0.3, fillet=0.65, bowl_k=2.25)),
 ("I2", "Inknut lineage · heavy, Albertus flare", v(xh=470, asc=745, desc=230, stem=125, contrast=0.35, stress=20, width=0.9, serif_style="flare", wedge_len=0.5, flare=0.28)),
 # --- TeXGyreHeros (Helvetica): neutral proportions, tight apertures, even color
 ("H1", "Heros lineage · neutral, even color", v(xh=520, asc=725, desc=210, stem=94, contrast=0.25, stress=8, power=1.3, width=0.92, bowl_k=2.3, wedge_len=0.55, wedge_depth=1.1, serif_drop=0.12, arch_start=0.6)),
 ("H2", "Heros lineage · squarer, wider", v(xh=520, asc=725, desc=210, stem=94, contrast=0.22, stress=6, power=1.3, width=1.0, bowl_k=2.6, wedge_len=0.6, wedge_depth=1.2, serif_drop=0.1, fillet=0.35)),
 # --- Almendra: calligraphic, high contrast, strong stress, pointed wedges
 ("A1", "Almendra lineage · calligraphic", v(xh=480, asc=740, desc=220, stem=104, contrast=0.68, stress=32, power=0.9, wedge_len=0.9, wedge_depth=1.4, serif_drop=0.4, cut_deg=22, fillet=0.5)),
 ("A2", "Almendra lineage · calligraphic, lighter", v(xh=480, asc=740, desc=220, stem=90, contrast=0.72, stress=34, power=0.85, wedge_len=1.0, wedge_depth=1.6, serif_drop=0.45, cut_deg=24)),
 # --- Atkinson Next: open, generous counters, humanist sans bones
 ("N1", "Atkinson lineage · open humanist, wedge feet", v(xh=500, asc=710, desc=165, stem=90, contrast=0.3, stress=10, power=1.25, width=0.98, n_width=350, bowl_k=2.1, wedge_len=0.55, wedge_depth=1.1, arch_start=0.62)),
 ("N2", "Atkinson lineage · open, flared", v(xh=500, asc=710, desc=165, stem=90, contrast=0.28, stress=10, power=1.25, width=0.98, n_width=350, serif_style="flare", wedge_len=0.4, flare=0.26)),
 # --- Doves (Jenson): the Venetian model with a warm, even rhythm
 ("D1", "Doves lineage · Jenson rhythm", v(xh=460, asc=750, desc=230, stem=92, contrast=0.5, stress=30, power=1.0, width=0.92, wedge_len=0.75, wedge_depth=1.6, serif_drop=0.32, fillet=0.6, arch_start=0.52)),
 ("D2", "Doves lineage · Jenson, darker", v(xh=460, asc=750, desc=230, stem=108, contrast=0.45, stress=28, power=1.0, width=0.94, wedge_len=0.7, wedge_depth=1.5, serif_drop=0.3, fillet=0.6)),
 # --- VandenKeere (Dutch old style): sturdy, large x-height for its age, crisp
 ("V1", "Van den Keere lineage · Dutch sturdy", v(xh=505, asc=725, desc=200, stem=106, contrast=0.5, stress=18, width=0.9, wedge_len=0.7, wedge_depth=1.5, serif_drop=0.2, cut_deg=16, fillet=0.5, bowl_k=2.2)),
 ("V2", "Van den Keere lineage · crisper, more contrast", v(xh=505, asc=725, desc=200, stem=100, contrast=0.6, stress=20, width=0.9, wedge_len=0.8, wedge_depth=1.4, serif_drop=0.28, cut_deg=18, fillet=0.4)),
 # --- Edgar (a display humanist): more personality in the wedges
 ("E1", "Edgar lineage · pronounced wedges", v(xh=490, asc=735, desc=210, stem=96, contrast=0.45, stress=20, wedge_len=1.1, wedge_depth=2.0, serif_drop=0.4, fillet=0.7, cut_deg=14)),
 ("E2", "Edgar lineage · pronounced wedges, squarer bowls", v(xh=490, asc=735, desc=210, stem=96, contrast=0.4, stress=16, wedge_len=1.0, wedge_depth=2.2, serif_drop=0.35, fillet=0.7, bowl_k=2.5)),
 # --- two wild cards
 ("W1", "Wild · Icone entasis, long shallow wedges", v(xh=495, asc=730, desc=200, stem=92, contrast=0.3, stress=10, flare=0.4, wedge_len=1.3, wedge_depth=1.0, serif_drop=0.0, fillet=0.3, power=1.3)),
 ("W2", "Wild · reverse-leaning nib, pointed serifs", v(xh=495, asc=730, desc=200, stem=96, contrast=0.5, stress=-12, power=1.0, wedge_len=0.9, wedge_depth=1.8, serif_drop=0.5, cut_deg=-10, fillet=0.5)),
]

def page():
    tiles = []
    for key, blurb, p in POP:
        svg = round6.svg_lines(p, ["fjord"], 0.3)
        tiles.append(f'<figure class="opt"><div class="word">{svg}</div><figcaption><span class="num">{key}</span> <b>{html.escape(blurb)}</b><span class="blurb">stem {p["stem"]} · contrast {p["contrast"]} · stress {p["stress"]}° · x-height {p["xh"]} · {p["serif_style"]} serifs</span></figcaption></figure>')
    return f'''<title>Fjord Twenty-Four</title>
<style>
:root{{--paper:#F9F3E9;--ink:#5C332B;--soft:#8A6A62;--rule:#E4D8C8}}
@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{--paper:#171B1B;--ink:#CFD4CC;--soft:#93A09B;--rule:#2B3331}}}}
:root[data-theme="dark"]{{--paper:#171B1B;--ink:#CFD4CC;--soft:#93A09B;--rule:#2B3331}}
body{{background:var(--paper);color:var(--ink);margin:0;padding:20px 14px 60px;font:15px/1.45 -apple-system,"Helvetica Neue",Arial,sans-serif}}
main{{max-width:1180px;margin:0 auto}} h1{{font-size:24px;margin:0 0 4px}}
.lede{{color:var(--soft);max-width:64ch;margin:0 0 22px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:22px 26px}}
.opt{{margin:0;border-top:1px solid var(--rule);padding-top:12px}}
.word{{color:var(--ink);overflow-x:auto}} .word svg{{display:block;max-width:100%;height:auto}}
figcaption{{margin-top:6px;font-size:13px}} .num{{display:inline-block;min-width:3ch;color:var(--soft);margin-right:6px}}
.blurb{{display:block;color:var(--soft);font-variant-numeric:tabular-nums}}
</style>
<main>
<h1>Fjord Twenty-Four</h1>
<p class="lede">Round 7, divergent. Twenty-four word images on the second drawing model, two per installed family plus two wild cards. Each takes one family's character as the brief (its proportions, weight, stress, how it ends a stem) and is tuned on its own; none is that font. Vectors: pinch in.</p>
<div class="grid">{''.join(tiles)}</div>
</main>'''

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
    open(os.path.join(out, "fjord-24.html"), "w").write(page())
    from PIL import Image, ImageDraw
    tiles = []
    for key, blurb, p in POP:
        polys, adv = A.layout(p, "fjord"); scale = 0.24; ss = 3
        top = p["asc"] + 60; H = int((top + p["desc"] + 80) * scale); W = int((adv + 60) * scale)
        im = Image.new("L", (W * ss, H * ss), 255); d = ImageDraw.Draw(im)
        for poly in polys: d.polygon([((x + 30) * scale * ss, (top - y) * scale * ss) for x, y in poly], fill=0)
        tiles.append(im.resize((W, H), Image.LANCZOS))
    Wm = max(t.width for t in tiles); Hm = max(t.height for t in tiles)
    sheet = Image.new("L", (Wm * 4, Hm * 6), 255)
    for i, t in enumerate(tiles): sheet.paste(t, ((i % 4) * Wm, (i // 4) * Hm))
    sheet.save(os.path.join(out, "sheet24.png")); print("ok", sheet.size)
