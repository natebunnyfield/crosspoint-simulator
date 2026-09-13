import json, math, html
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.areaPen import AreaPen
from fontTools.pens.perimeterPen import PerimeterPen
from fontTools.pens.transformPen import TransformPen

import sys, os
FJ = TTFont(sys.argv[1] if len(sys.argv) > 1 else 'fonts/vdk/Fjord-Regular.ttf')
GA = TTFont(os.path.expanduser('~/src/crosspoint-reader/lib/EpdFont/local_fonts/VandenKeere-Regular.otf'))
def info(font):
    gs = font.getGlyphSet(); cm = font.getBestCmap()
    bp = BoundsPen(gs); gs[cm[ord('x')]].draw(bp); xh = bp.bounds[3]   # measured x top (VdK's OS/2 says 405, its x tops at 401), as overlay_stier does
    if font is FJ: xh = 415   # Fjord's x carries wedge tips above the design x-height
    return dict(xh=xh, cap=font['OS/2'].sCapHeight, gs=gs, cmap=cm, hmtx=font['hmtx'])
F, G = info(FJ), info(GA)

OSF={c:n+'.osf' for c,n in zip('0123456789',['zero','one','two','three','four','five','six','seven','eight','nine'])}
def measure(I, ch):
    gn = I['cmap'].get(ord(ch))
    if I is G and ch in OSF and OSF[ch] in I['gs']: gn = OSF[ch]
    if gn is None: return None
    g = I['gs'][gn]; s = 1.0 / I['xh']
    bp = BoundsPen(I['gs']); g.draw(bp)
    ap = AreaPen(I['gs']); g.draw(ap)
    pp = PerimeterPen(I['gs']); g.draw(pp)
    sp = SVGPathPen(I['gs']); g.draw(TransformPen(sp, (s, 0, 0, -s, 0, 0)))
    adv = I['hmtx'][gn][0] * s
    b = bp.bounds
    if b is None: return dict(adv=adv, path='', empty=True)
    x0, y0, x1, y1 = [v * s for v in b]
    A = abs(ap.value) * s * s; P = pp.value * s
    return dict(adv=adv, x0=x0, y0=y0, x1=x1, y1=y1, w=x1 - x0, h=y1 - y0, top=y1, bot=y0,
                area=A, thick=(2 * A / P if P else 0), path=sp.getCommands(), empty=False)

chars = ''.join(chr(c) for c in sorted(F['cmap']))
rows = []
for ch in chars:
    f, g = measure(F, ch), measure(G, ch)
    if g is None or f is None: continue
    r = dict(ch=ch, f=f, g=g, flags=[])
    if not f['empty'] and not g['empty']:
        def lr(a, b): return math.log(a / b) if a > 0 and b > 0 else 0
        r['d_adv'] = lr(f['adv'], g['adv']); r['d_w'] = lr(f['w'], g['w'])
        r['d_h'] = lr(f['h'], g['h']); r['d_thick'] = lr(f['thick'], g['thick'])
        r['d_top'] = f['top'] - g['top']; r['d_bot'] = f['bot'] - g['bot']
        r['d_area'] = lr(f['area'], g['area'])
        if abs(r['d_w']) > 0.20: r['flags'].append('width %+.0f%%' % (100 * (math.exp(r['d_w']) - 1)))
        if abs(r['d_h']) > 0.15: r['flags'].append('height %+.0f%%' % (100 * (math.exp(r['d_h']) - 1)))
        if abs(r['d_thick']) > 0.25: r['flags'].append('stroke %+.0f%%' % (100 * (math.exp(r['d_thick']) - 1)))
        if abs(r['d_top']) > 0.12: r['flags'].append('top %+.2f xh' % r['d_top'])
        if abs(r['d_bot']) > 0.12: r['flags'].append('bottom %+.2f xh' % r['d_bot'])
        r['score'] = abs(r['d_w']) + abs(r['d_h']) + abs(r['d_thick']) + abs(r['d_top']) + abs(r['d_bot'])
    else:
        r['score'] = 0
    rows.append(r)

import statistics
low=[r for r in rows if r['ch'].islower() and 'd_thick' in r]; caps=[r for r in rows if r['ch'].isupper() and 'd_thick' in r]
med=lambda rs,k: math.exp(statistics.median(r[k] for r in rs))
GLOBAL=dict(low_thick=med(low,'d_thick'), cap_thick=med(caps,'d_thick'), low_w=med(low,'d_w'), cap_w=med(caps,'d_w'),
  cap_top=statistics.median(r['d_top'] for r in caps), capxh_f=F['cap']/F['xh'], capxh_g=G['cap']/G['xh'])
print('GLOBAL', {k:round(v,3) for k,v in GLOBAL.items()})
# ---- page
XH = 56  # px per x-height
def cell(r):
    f, g = r['f'], r['g']
    if f['empty'] or g['empty']:
        return ''
    top = max(f['top'], g['top'], 1.0); bot = min(f['bot'], g['bot'], 0)
    H = (top - bot) * XH + 16; base = top * XH + 8
    wf = f['w'] * XH + 12; wg = g['w'] * XH + 12; wo = max(wf, wg)
    def pane(path, x, color, op=1, shift=0):
        return f'<path d="{path}" fill="{color}" fill-opacity="{op}" transform="translate({x - shift * XH:.1f},{base:.1f}) scale({XH})"/>'
    W = wg + wf + wo + 24
    lines = f'<line x1="0" x2="{W}" y1="{base:.1f}" y2="{base:.1f}" stroke="#c9c2b6" stroke-width="0.5"/>' \
            f'<line x1="0" x2="{W}" y1="{base - XH:.1f}" y2="{base - XH:.1f}" stroke="#e2dcd0" stroke-width="0.5" stroke-dasharray="3 3"/>'
    svg = (f'<svg width="{W:.0f}" height="{H:.0f}" viewBox="0 0 {W:.0f} {H:.0f}">{lines}'
           + pane(g['path'], 6, '#8a8378', 1, g['x0'])
           + pane(f['path'], wg + 12 + 6, '#111', 1, f['x0'])
           + pane(g['path'], wg + wf + 24 + 6, '#c0392b', 0.55, g['x0'])
           + pane(f['path'], wg + wf + 24 + 6, '#111', 0.55, f['x0'])
           + '</svg>')
    m = ''
    if 'd_adv' in r:
        m = (f'adv {f["adv"]:.2f}/{g["adv"]:.2f} · w {f["w"]:.2f}/{g["w"]:.2f} · h {f["h"]:.2f}/{g["h"]:.2f} · '
             f'stroke {f["thick"]:.3f}/{g["thick"]:.3f}')
    flags = ' '.join(f'<span class="flag">{html.escape(x)}</span>' for x in r['flags'])
    cls = 'cell' + (' off' if len(r['flags']) >= 2 or r['score'] > 0.6 else (' warn' if r['flags'] else ''))
    return f'<div class="{cls}"><div class="hd"><span class="ch">{html.escape(r["ch"])}</span>{flags}</div>{svg}<div class="m">{m}</div></div>'

ranked = sorted([r for r in rows if r['flags']], key=lambda r: -r['score'])
worst = ''.join(f'<li><b>{html.escape(r["ch"])}</b> — {", ".join(r["flags"])}</li>' for r in ranked)
page = f'''<title>Fjord against Van den Keere</title>
<style>
:root{{--bg:#f6f3ec;--ink:#1a1814;--mute:#6f6a60;--line:#d9d2c4;--warn:#b7791f;--off:#b3261e}}
body{{background:var(--bg);color:var(--ink);font:14px/1.45 -apple-system,Helvetica,Arial,sans-serif;margin:0;padding:24px}}
h1{{font-weight:600;font-size:22px;margin:0 0 6px}} p{{max-width:70ch;color:var(--mute);margin:0 0 14px}}
.grid{{display:flex;flex-wrap:wrap;gap:14px}}
.cell{{background:#fff;border:1px solid var(--line);padding:8px 10px;border-radius:4px}}
.cell.warn{{border-color:var(--warn)}} .cell.off{{border-color:var(--off);border-width:2px}}
.hd{{display:flex;gap:8px;align-items:baseline;flex-wrap:wrap;margin-bottom:4px}}
.ch{{font:600 20px Georgia,serif;min-width:1.2em}}
.flag{{font-size:11px;padding:1px 6px;border-radius:9px;background:#f3e6e4;color:var(--off)}}
.m{{font:10.5px ui-monospace,Menlo,monospace;color:var(--mute);margin-top:4px}}
ol{{columns:2;max-width:80ch}} li{{margin:2px 0}}
.key span{{display:inline-block;margin-right:14px}} .sw{{display:inline-block;width:12px;height:12px;vertical-align:-2px;margin-right:4px}}
</style>
<h1>Fjord against Van den Keere, glyph by glyph</h1>
<p>Each cell: <b>Van den Keere</b> (its default figures are old-style) (gray) · <b>Fjord-Regular</b> (black) · both overlaid (Van den Keere red). Both fonts scaled so their x-heights match (Fjord 415, Van den Keere 401 units (its measured x top)); baseline solid, x-height dashed; glyphs aligned on the left edge of their ink. Numbers are in x-heights; stroke = 2·area/perimeter, a mean stroke thickness.</p>
<p class="key"><span><i class="sw" style="background:#fff;border:2px solid var(--off)"></i>wildly off (two flags or more)</span><span><i class="sw" style="background:#fff;border:1px solid var(--warn)"></i>one flag</span> · flags fire at width ±20%, height ±15%, stroke ±25%, top or bottom ±0.12 xh</p>
<h2 style="font-size:16px;margin:10px 0 4px">Whole-font</h2>
<ul style="max-width:80ch"><li>Lowercase mean stroke: Fjord is <b>{100*(GLOBAL['low_thick']-1):+.0f}%</b> against Van den Keere 400 (median over a–z); capitals <b>{100*(GLOBAL['cap_thick']-1):+.0f}%</b>.</li>
<li>Capital height over x-height: Fjord {GLOBAL['capxh_f']:.2f}, Van den Keere {GLOBAL['capxh_g']:.2f} — every capital's top sits about {GLOBAL['cap_top']:+.2f} xh above Van den Keere's, which is why most of A–Z carry a "top" flag.</li>
<li>Lowercase width median {100*(GLOBAL['low_w']-1):+.0f}%, capitals {100*(GLOBAL['cap_w']-1):+.0f}%.</li></ul>
<h2 style="font-size:16px;margin:10px 0 4px">Ranked, worst first ({len(ranked)} of {len(rows)} flagged)</h2>
<ol>{worst}</ol>
<div class="grid">{''.join(cell(r) for r in rows)}</div>
'''
open(sys.argv[2] if len(sys.argv) > 2 else 'vdk-overlay.html', 'w').write(page)
print(len(rows), 'glyphs;', len(ranked), 'flagged')
for r in ranked: print(f'{r["ch"]!r:5} score {r["score"]:.2f}  ' + '; '.join(r['flags']))
print('--- global: Fjord cap/xh', F['cap']/F['xh'], ' Van den Keere', G['cap']/G['xh'])
