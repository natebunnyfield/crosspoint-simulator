import os, glob, html, json
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.transformPen import TransformPen
R = os.path.expanduser('~/src/crosspoint-reader/lib/EpdFont')
FACES = [('EB Garamond 400', 'ref/EBGaramond-400.ttf', '#c0392b'),
 ('Coelacanth', f'{R}/scripts/downloaded_fonts/Coelacanth/Coelacanth.otf', '#d35400'),
 ('Libris ADF', f'{R}/scripts/downloaded_fonts/LibrisADF/LibrisADFStd-Regular.otf', '#b7950b'),
 ('Almendra', f'{R}/scripts/downloaded_fonts/Almendra/H4ckBXKAlMnTn0CskyY6.ttf', '#7d6608'),
 ('Atkinson Next 365', glob.glob(f'{R}/scripts/instanced_fonts/AtkinsonHyperlegibleNext/regular_wght365_*.ttf')[0], '#1e8449'),
 ('Inknut Antiqua', f'{R}/scripts/downloaded_fonts/InknutAntiqua62/InknutAntiqua-Regular.ttf', '#148f77'),
 ('Doves Type', f'{R}/local_fonts/DovesType-Text.ttf', '#2471a3'),
 ('Van den Keere', f'{R}/local_fonts/VandenKeere-Regular.otf', '#6c3483'),
 ('Dante MT', f'{R}/local_fonts/DanteMT-Regular.ttf', '#a93226'),
 ('Edgar', f'{R}/local_fonts/Edgar-Regular.ttf', '#5d6d7e')]
NAMES = ['zero','one','two','three','four','five','six','seven','eight','nine']
def onum_map(f):
    if 'GSUB' not in f: return {}
    g = f['GSUB'].table; m = {}
    for fr in g.FeatureList.FeatureRecord:
        if fr.FeatureTag != 'onum': continue
        for li in fr.Feature.LookupListIndex:
            for st in g.LookupList.Lookup[li].SubTable:
                st = getattr(st, 'ExtSubTable', st); mp = getattr(st, 'mapping', None)
                if mp: m.update(mp)
    return m
def load(path):
    f = TTFont(path); gs = f.getGlyphSet(); cm = f.getBestCmap()
    bp = BoundsPen(gs); gs[cm[ord('x')]].draw(bp); xh = bp.bounds[3]
    if 'Fjord' in path: xh = 415
    om = onum_map(f); figs = {}
    for d, n in enumerate(NAMES):
        gn = cm.get(ord(str(d)))
        if gn is None: continue
        gn2 = om.get(gn, gn)
        # prefer a proportional old-style set when the onum target is tabular
        for alt in (gn2.replace('.tosf', '.osf'), gn2):
            if alt in gs: gn2 = alt; break
        figs[str(d)] = gn2
    # old-style test: the 3 descends, or the 8 rises above the x-height by more than the 0 does
    def top(gn): bp = BoundsPen(gs); gs[gn].draw(bp); return bp.bounds
    b3 = top(figs['3']); b0 = top(figs['0']); b8 = top(figs['8'])
    oldstyle = (b3[1] < -0.15 * xh) or (b8[3] - b0[3] > 0.25 * xh)
    return dict(gs=gs, xh=xh, figs=figs, oldstyle=oldstyle, onum=bool(om))
def path(I, gn):
    s = 1 / I['xh']; g = I['gs'][gn]; bp = BoundsPen(I['gs']); g.draw(bp)
    sp = SVGPathPen(I['gs']); g.draw(TransformPen(sp, (s, 0, 0, -s, 0, 0)))
    x0, y0, x1, y1 = [v * s for v in bp.bounds]; return dict(path=sp.getCommands(), x0=x0, y0=y0, x1=x1, y1=y1, adv=g.width * s)
FJ = load('fonts/Fjord-Regular.ttf'); refs = []; excluded = []
for n, p, col in FACES:
    I = load(p); (refs if I['oldstyle'] else excluded).append((n, I, col)); print(n, 'oldstyle' if I['oldstyle'] else 'LINING only', 'onum' if I['onum'] else '')
XH = 90; cells = []
for d in '0123456789':
    f = path(FJ, FJ['figs'][d]); rs = [(n, path(I, I['figs'][d]), col) for n, I, col in refs]
    allg = [f] + [g for _, g, _ in rs]; top = max(max(g['y1'] for g in allg), 1.0); bot = min(min(g['y0'] for g in allg), 0.0)
    W = max(g['x1'] - g['x0'] for g in allg) * XH + 16; H = (top - bot) * XH + 16; base = top * XH + 8
    pane = lambda g, color, op, cls: f'<path class="{cls}" d="{g["path"]}" fill="{color}" fill-opacity="{op}" transform="translate({8 - g["x0"] * XH:.1f},{base:.1f}) scale({XH})"/>'
    svg = (f'<svg width="{W:.0f}" height="{H:.0f}" viewBox="0 0 {W:.0f} {H:.0f}"><line x1="0" x2="{W:.0f}" y1="{base:.1f}" y2="{base:.1f}" stroke="#c9c2b6" stroke-width="0.5"/><line x1="0" x2="{W:.0f}" y1="{base - XH:.1f}" y2="{base - XH:.1f}" stroke="#e2dcd0" stroke-width="0.5" stroke-dasharray="3 3"/>'
           + ''.join(pane(g, col, 0.28, 'r' + str(i)) for i, (n, g, col) in enumerate(rs)) + pane(f, '#000', 0.7, 'fj') + '</svg>')
    cells.append(f'<div class="cell{" eight" if d == "8" else ""}"><div class="ch">{d}</div>{svg}</div>')
legend = ''.join(f'<label><input type="checkbox" checked data-cls="r{i}"><i style="background:{col}"></i>{html.escape(n)}</label>' for i, (n, _, col) in enumerate(refs)) + '<label><input type="checkbox" checked data-cls="fj"><i style="background:#000"></i>Fjord-Regular</label>'
def row(I, name, color, text='0123456789  1868 380 3.5% 1953'):
    x = 0; parts = []; s = 1 / I['xh']
    for ch in text:
        if ch == ' ': x += 0.5; continue
        gn = I['figs'].get(ch) or I['gs'].font.getBestCmap().get(ord(ch)) if hasattr(I['gs'], 'font') else I['figs'].get(ch)
        if gn is None:
            cm = TTFont if False else None
        if ch not in I['figs']:
            # non-figure characters from the face's cmap
            cm = I.setdefault('cm', None)
        g = None
        if ch in I['figs']: g = I['gs'][I['figs'][ch]]
        else:
            if I.get('cmx') is None: I['cmx'] = {}
            g = None
        if g is None: x += 0.4; continue
        sp = SVGPathPen(I['gs']); g.draw(TransformPen(sp, (s, 0, 0, -s, 0, 0))); parts.append(f'<path d="{sp.getCommands()}" fill="{color}" transform="translate({x:.4f},0)"/>'); x += g.width * s
    return f'<div class="wrow"><span class="wn">{html.escape(name)}</span><svg width="{x * 30 + 10:.0f}" height="{3.0 * 30:.0f}" viewBox="0 0 {x * 30 + 10:.0f} {3.0 * 30:.0f}"><g transform="translate(5,{2.0 * 30:.1f}) scale(30)">{"".join(parts)}</g></svg></div>'
rows = row(FJ, 'Fjord-Regular', '#000') + ''.join(row(I, n, col) for n, I, col in refs)
page = f'''<title>Fjord Figures over the Humanist Old Style</title>
<style>body{{background:#f6f3ec;color:#1a1814;font:14px/1.45 -apple-system,Helvetica,Arial,sans-serif;margin:0;padding:22px}}
h1{{font-weight:600;font-size:22px;margin:0 0 6px}} h2{{font-weight:600;font-size:16px;margin:18px 0 6px}} p{{max-width:72ch;color:#6f6a60;margin:0 0 12px}}
.legend{{display:flex;flex-wrap:wrap;gap:8px 18px;background:#fff;border:1px solid #d9d2c4;padding:10px 12px;border-radius:4px;margin-bottom:14px;position:sticky;top:0}}
.legend label{{display:flex;align-items:center;gap:6px}} .legend i{{display:inline-block;width:12px;height:12px;border-radius:2px}}
.grid{{display:flex;flex-wrap:wrap;gap:10px}} .cell{{background:#fff;border:1px solid #d9d2c4;padding:6px 8px;border-radius:4px}} .cell.eight{{border:2px solid #1a1814}}
.ch{{font:600 15px Georgia,serif;color:#6f6a60;margin-bottom:2px}}
.wrow{{display:flex;align-items:center;gap:10px;background:#fff;border:1px solid #d9d2c4;padding:2px 8px;margin-bottom:4px;overflow-x:auto}} .wn{{min-width:150px;color:#6f6a60;font-size:12px}}
svg path.off{{display:none}}</style>
<h1>Fjord's figures over the humanist old style</h1>
<p>Fjord-Regular's 0 to 9 (black, 70%) over the OLD-STYLE figures of the humanist faces on disk that have them (each 28%, its own color), scaled to one x-height, aligned on the baseline and the left edge of each figure's ink. The 8 is boxed. Faces with only lining figures are left out: {html.escape(', '.join(n for n, _, _ in excluded)) or 'none'}. Untick a face to hide it.</p>
<div class="legend">{legend}</div><div class="grid">{''.join(cells)}</div>
<h2>Figures in a row, one face per line, x-heights matched</h2>{rows}
<script>document.querySelectorAll('.legend input').forEach(cb=>cb.addEventListener('change',()=>{{document.querySelectorAll('svg path.'+cb.dataset.cls).forEach(p=>p.classList.toggle('off',!cb.checked))}}));</script>'''
open('fonts/fjord-figures-overlay.html', 'w').write(page); print('excluded:', [n for n, _, _ in excluded], len(page) // 1024, 'KB')
