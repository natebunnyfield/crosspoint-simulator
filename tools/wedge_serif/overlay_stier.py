import math, html, os, glob
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.transformPen import TransformPen
R = os.path.expanduser('~/src/crosspoint-reader/lib/EpdFont')
REFS = [  # (name, path, color)  the humanist S-tier faces on disk
 ('Coelacanth', f'{R}/scripts/downloaded_fonts/Coelacanth/Coelacanth.otf', '#c0392b'),
 ('Libris ADF', f'{R}/scripts/downloaded_fonts/LibrisADF/LibrisADFStd-Regular.otf', '#d35400'),
 ('Almendra', f'{R}/scripts/downloaded_fonts/Almendra/H4ckBXKAlMnTn0CskyY6.ttf', '#b7950b'),   # the one whose name table says "Almendra Regular" (the four files have hashed names)
 ('Atkinson Next 365', glob.glob(f'{R}/scripts/instanced_fonts/AtkinsonHyperlegibleNext/regular_wght365_*.ttf')[0], '#1e8449'),
 ('Inknut Antiqua', f'{R}/scripts/downloaded_fonts/InknutAntiqua62/InknutAntiqua-Regular.ttf', '#148f77'),
 ('Doves Type', f'{R}/local_fonts/DovesType-Text.ttf', '#2471a3'),
 ('Van den Keere', f'{R}/local_fonts/VandenKeere-Regular.otf', '#6c3483'),
 ('Dante MT', f'{R}/local_fonts/DanteMT-Regular.ttf', '#a93226'),
 ('Edgar', f'{R}/local_fonts/Edgar-Regular.ttf', '#7d6608'),
]
def load(path):
    f = TTFont(path); gs = f.getGlyphSet(); cm = f.getBestCmap()
    # measure the x-height from the x's own outline: one face's OS/2 field is
    # wrong (it rendered giant), so the table value is not trusted for any
    bp = BoundsPen(gs); gs[cm[ord('x')]].draw(bp); xh = bp.bounds[3]
    if 'Fjord' in path: xh = 415   # the design's x-height; Fjord's x carries wedge tips 26 units above it
    return dict(gs=gs, cm=cm, xh=xh, upm=f['head'].unitsPerEm)
def glyph(I, ch):
    gn = I['cm'].get(ord(ch))
    if gn is None: return None
    g = I['gs'][gn]; s = 1.0 / I['xh']
    bp = BoundsPen(I['gs']); g.draw(bp)
    if bp.bounds is None: return None
    sp = SVGPathPen(I['gs']); g.draw(TransformPen(sp, (s, 0, 0, -s, 0, 0)))
    x0, y0, x1, y1 = [v * s for v in bp.bounds]
    return dict(path=sp.getCommands(), x0=x0, y0=y0, x1=x1, y1=y1)
FJ = load('fonts/Fjord-Regular.ttf'); refs = [(n, load(p), col) for n, p, col in REFS]
chars = [chr(c) for c in sorted(FJ['cm']) if chr(c).strip()]
XH = 64
cells = []
for ch in chars:
    f = glyph(FJ, ch)
    if f is None: continue
    rs = [(n, glyph(I, ch), col) for n, I, col in refs]; rs = [(n, g, col) for n, g, col in rs if g]
    allg = [f] + [g for _, g, _ in rs]
    top = max(max(g['y1'] for g in allg), 1.0); bot = min(min(g['y0'] for g in allg), 0.0)
    W = (max(g['x1'] - g['x0'] for g in allg)) * XH + 16; H = (top - bot) * XH + 16; base = top * XH + 8
    def pane(g, color, op, cls):
        return f'<path class="{cls}" d="{g["path"]}" fill="{color}" fill-opacity="{op}" transform="translate({8 - g["x0"] * XH:.1f},{base:.1f}) scale({XH})"/>'
    svg = (f'<svg width="{W:.0f}" height="{H:.0f}" viewBox="0 0 {W:.0f} {H:.0f}">'
           f'<line x1="0" x2="{W:.0f}" y1="{base:.1f}" y2="{base:.1f}" stroke="#c9c2b6" stroke-width="0.5"/>'
           f'<line x1="0" x2="{W:.0f}" y1="{base - XH:.1f}" y2="{base - XH:.1f}" stroke="#e2dcd0" stroke-width="0.5" stroke-dasharray="3 3"/>'
           + ''.join(pane(g, col, 0.28, 'r' + str(i)) for i, (n, g, col) in enumerate(rs))
           + pane(f, '#000', 0.7, 'fj') + '</svg>')
    cells.append(f'<div class="cell"><div class="ch">{html.escape(ch)}</div>{svg}</div>')
legend = ''.join(f'<label><input type="checkbox" checked data-cls="r{i}"><i style="background:{col}"></i>{html.escape(n)}</label>' for i, (n, _, col) in enumerate(refs))
legend += '<label><input type="checkbox" checked data-cls="fj"><i style="background:#000"></i>Fjord-Regular</label>'
# word rows, each face on its own line at matched x-height
def wordrow(I, text, color, name):
    x = 0; parts = []; s = 1.0 / I['xh']
    for ch in text:
        gn = I['cm'].get(ord(ch))
        if gn is None: x += 0.5; continue
        g = I['gs'][gn]; sp = SVGPathPen(I['gs']); g.draw(TransformPen(sp, (s, 0, 0, -s, 0, 0)))
        parts.append(f'<path d="{sp.getCommands()}" fill="{color}" transform="translate({x:.4f},0)"/>'); x += g.width * s
    return x, f'<g>{"".join(parts)}</g>', name
WXH = 26; rows = []
for n, I, col in [('Fjord-Regular', FJ, '#000')] + [(n, I, col) for n, I, col in refs]:
    w, g, name = wordrow(I, 'Hamburgefonstiv quick fjord zephyrs', col, n)
    rows.append(f'<div class="wrow"><span class="wn">{html.escape(name)}</span><svg width="{w * WXH + 10:.0f}" height="{3.2 * WXH:.0f}" viewBox="0 0 {w * WXH + 10:.0f} {3.2 * WXH:.0f}"><g transform="translate(5,{2.1 * WXH:.1f}) scale({WXH})">{g}</g></svg></div>')
page = f'''<title>Fjord over the Humanist S Tier</title>
<style>
body{{background:#f6f3ec;color:#1a1814;font:14px/1.45 -apple-system,Helvetica,Arial,sans-serif;margin:0;padding:22px}}
h1{{font-weight:600;font-size:22px;margin:0 0 6px}} h2{{font-weight:600;font-size:16px;margin:18px 0 6px}} p{{max-width:72ch;color:#6f6a60;margin:0 0 12px}}
.legend{{display:flex;flex-wrap:wrap;gap:8px 18px;background:#fff;border:1px solid #d9d2c4;padding:10px 12px;border-radius:4px;margin-bottom:14px;position:sticky;top:0;z-index:2}}
.legend label{{display:flex;align-items:center;gap:6px}} .legend i{{display:inline-block;width:12px;height:12px;border-radius:2px}}
.grid{{display:flex;flex-wrap:wrap;gap:10px}} .cell{{background:#fff;border:1px solid #d9d2c4;padding:6px 8px;border-radius:4px}}
.ch{{font:600 15px Georgia,serif;color:#6f6a60;margin-bottom:2px}}
.wrow{{display:flex;align-items:center;gap:10px;background:#fff;border:1px solid #d9d2c4;padding:2px 8px;margin-bottom:4px;overflow-x:auto}} .wn{{min-width:150px;color:#6f6a60;font-size:12px}}
svg path.off{{display:none}}
</style>
<h1>Fjord over the humanist S tier</h1>
<p>Every Fjord-Regular glyph (black, 70%) overlaid on the same glyph from the nine humanist faces of the S tier that are on disk (each 28%, its own color), scaled so all x-heights match; aligned on the baseline and on the left edge of each glyph's ink. Baseline solid, x-height dashed. Untick a face to hide it. Left out as not humanist: TeX Gyre Schola, Libre Franklin, TeX Gyre Heros. Fjord here is the round-33 build.</p>
<div class="legend">{legend}</div>
<div class="grid">{''.join(cells)}</div>
<h2>Rhythm, one face per line, x-heights matched</h2>
{''.join(rows)}
<script>document.querySelectorAll('.legend input').forEach(cb=>cb.addEventListener('change',()=>{{document.querySelectorAll('svg path.'+cb.dataset.cls).forEach(p=>p.classList.toggle('off',!cb.checked))}}));</script>'''
open('fonts/fjord-stier-overlay.html', 'w').write(page); print(len(cells), 'cells', len(page)//1024, 'KB')
