"""Every glyph against the FOUR shape references (guide §0): EB Garamond
400, Van den Keere, Dante MT, Edgar -- cmp_garamond's metrics (matched
x-height; flags at width +-20%, height +-15%, mean stroke +-25%, top/bottom
+-0.12 xh), one flag count per reference, and an HTML of overlay cells.
    python3 -m outlines.cmp.overlay4 <ttf> [<out.html>]"""
import sys, os, math, html, statistics
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.areaPen import AreaPen
from fontTools.pens.perimeterPen import PerimeterPen
from fontTools.pens.transformPen import TransformPen
R = os.path.expanduser('~/src/crosspoint-reader/lib/EpdFont/local_fonts')
REFS = [('Garamond', '/private/tmp/claude-501/-Users-natebunnyfield-src-crosspoint-simulator/414829eb-ff28-4317-bac9-e346395042d3/scratchpad/wedge/ref/EBGaramond-400.ttf', '#c0392b'),
        ('Van den Keere', f'{R}/VandenKeere-Regular.otf', '#6c3483'), ('Dante', f'{R}/DanteMT-Regular.ttf', '#1e8449'), ('Edgar', f'{R}/Edgar-Regular.ttf', '#b7950b')]
OSF = {c: n + '.osf' for c, n in zip('0123456789', ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine'])}

def info(path, fjord=False):
    f = TTFont(path); gs = f.getGlyphSet(); cm = f.getBestCmap()
    bp = BoundsPen(gs); gs[cm[ord('x')]].draw(bp); xh = 415 if fjord else bp.bounds[3]
    return dict(xh=xh, gs=gs, cmap=cm, hmtx=f['hmtx'], fjord=fjord)

def measure(I, ch):
    gn = I['cmap'].get(ord(ch))
    if not I['fjord'] and ch in OSF and OSF[ch] in I['gs']: gn = OSF[ch]
    if gn is None: return None
    g = I['gs'][gn]; s = 1.0 / I['xh']
    bp = BoundsPen(I['gs']); g.draw(bp); ap = AreaPen(I['gs']); g.draw(ap); pp = PerimeterPen(I['gs']); g.draw(pp)
    sp = SVGPathPen(I['gs']); g.draw(TransformPen(sp, (s, 0, 0, -s, 0, 0)))
    if bp.bounds is None: return None
    x0, y0, x1, y1 = [v * s for v in bp.bounds]; A = abs(ap.value) * s * s; P = pp.value * s
    return dict(x0=x0, y0=y0, x1=x1, y1=y1, w=x1 - x0, h=y1 - y0, top=y1, bot=y0, thick=(2 * A / P if P else 0), path=sp.getCommands())

def flags(f, g):
    out = []
    lr = lambda a, b: math.log(a / b) if a > 0 and b > 0 else 0
    if abs(lr(f['w'], g['w'])) > 0.20: out.append('width %+.0f%%' % (100 * (f['w'] / g['w'] - 1)))
    if abs(lr(f['h'], g['h'])) > 0.15: out.append('height %+.0f%%' % (100 * (f['h'] / g['h'] - 1)))
    if abs(lr(f['thick'], g['thick'])) > 0.25: out.append('stroke %+.0f%%' % (100 * (f['thick'] / g['thick'] - 1)))
    if abs(f['top'] - g['top']) > 0.12: out.append('top %+.2f' % (f['top'] - g['top']))
    if abs(f['bot'] - g['bot']) > 0.12: out.append('bottom %+.2f' % (f['bot'] - g['bot']))
    return out

def compare(ttf):
    F = info(ttf, True); refs = [(n, info(p), col) for n, p, col in REFS]
    chars = [chr(c) for c in sorted(F['cmap']) if chr(c).strip()]
    table = {}; counts = {n: 0 for n, _, _ in refs}; per = {n: [] for n, _, _ in refs}
    for ch in chars:
        f = measure(F, ch)
        if f is None: continue
        table[ch] = dict(f=f, refs={})
        for n, I, col in refs:
            g = measure(I, ch)
            if g is None: continue
            fl = flags(f, g); table[ch]['refs'][n] = (g, fl, col)
            if fl: counts[n] += 1; per[n].append((ch, fl))
    return table, counts, per, [n for n, _, _ in refs]

def cells_html(table, names, XH=48):
    out = []
    for ch, r in table.items():
        f = r['f']; gs = [(n, g, fl, col) for n, (g, fl, col) in r['refs'].items()]
        allg = [f] + [g for _, g, _, _ in gs]
        top = max(max(g['top'] for g in allg), 1.0); bot = min(min(g['bot'] for g in allg), 0.0)
        W = max(g['w'] for g in allg) * XH + 12; H = (top - bot) * XH + 12; base = top * XH + 6
        pane = lambda g, col, op: f'<path d="{g["path"]}" fill="{col}" fill-opacity="{op}" transform="translate({6 - g["x0"] * XH:.1f},{base:.1f}) scale({XH})"/>'
        svg = (f'<svg width="{W:.0f}" height="{H:.0f}" viewBox="0 0 {W:.0f} {H:.0f}"><line x1="0" x2="{W:.0f}" y1="{base:.1f}" y2="{base:.1f}" stroke="#c9c2b6" stroke-width="0.5"/>'
               f'<line x1="0" x2="{W:.0f}" y1="{base - XH:.1f}" y2="{base - XH:.1f}" stroke="#e2dcd0" stroke-width="0.5" stroke-dasharray="3 3"/>'
               + ''.join(pane(g, col, 0.26) for _, g, _, col in gs) + pane(f, '#000', 0.72) + '</svg>')
        fl = ''.join(f'<span class="flag" style="border-color:{col}">{html.escape(n[:3])}: {html.escape(", ".join(x))}</span>' for n, g, x, col in gs if x)
        out.append(f'<div class="cell"><div class="ch">{html.escape(ch)}</div>{svg}<div class="fl">{fl}</div></div>')
    return ''.join(out)

if __name__ == '__main__':
    table, counts, per, names = compare(sys.argv[1])
    print(os.path.basename(sys.argv[1]), 'flagged per reference:', counts, 'of', len(table))
    for n in names: print(' ', n, ' '.join(f"{ch}[{len(fl)}]" for ch, fl in per[n]))
    if len(sys.argv) > 2:
        page = f'<title>Fjord over four references</title><style>body{{font:13px -apple-system,Arial;background:#f6f3ec;padding:16px}}.grid{{display:flex;flex-wrap:wrap;gap:8px}}.cell{{background:#fff;border:1px solid #d9d2c4;padding:5px 7px;border-radius:4px;max-width:200px}}.ch{{font:600 14px Georgia;color:#6f6a60}}.flag{{display:inline-block;font-size:10px;border-left:3px solid;padding:0 4px;margin:2px 2px 0 0;background:#f7efe9}}</style><div class="grid">{cells_html(table, names)}</div>'
        open(sys.argv[2], 'w').write(page)
