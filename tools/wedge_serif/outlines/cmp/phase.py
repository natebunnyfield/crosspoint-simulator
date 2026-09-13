"""A per-family before/after proof page (mobile-friendly, guide §4): each
glyph at 230 px x-height -- Van den Keere, the previous build, this build
-- in one 750 px block; then words at 13 pt through the four-level
pipeline, before and after.
    python3 -m outlines.cmp.phase <glyphs> <before.ttf> <after.ttf> <out.html> <title> <words...>"""
import sys, os, html
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen
from .proof import b64, eink, W
from .overlay4 import REFS

VDK = REFS[1][1]
def xh_of(path):
    f = TTFont(path); gs = f.getGlyphSet(); cm = f.getBestCmap(); bp = BoundsPen(gs); gs[cm[ord('x')]].draw(bp)
    return (415 if 'Fjord' in path else bp.bounds[3]) / f['head'].unitsPerEm

def trio(ch, before, after, xh_px=230, width=W):
    cells = []
    for label, path in (('Van den Keere', VDK), ('before', before), ('after', after)):
        em = int(round(xh_px / xh_of(path))); font = ImageFont.truetype(path, em); asc, desc = font.getmetrics()
        w = int(font.getlength(ch)) + 16; im = Image.new('L', (w, asc + desc + 18), 255); d = ImageDraw.Draw(im)
        base = asc + 14; d.line([(0, base), (w, base)], fill=215); d.line([(0, base - xh_px), (w, base - xh_px)], fill=228)
        d.text((8, base), ch, font=font, fill=0, anchor='ls'); d.text((4, 2), label, fill=140); cells.append(im)
    H = max(c.size[1] for c in cells); tot = sum(c.size[0] for c in cells)
    sc = min(1.0, (width - 20) / tot)
    out = Image.new('L', (width, int(H * sc) + 4), 255); x = 10
    for c in cells:
        cc = c if sc == 1.0 else c.resize((int(c.size[0] * sc), int(c.size[1] * sc)), Image.NEAREST)
        out.paste(cc, (x, 2)); x += cc.size[0]
    return out, sc

def page(glyphs, before, after, out, title, words):
    figs = []
    def img(im, cap): figs.append(f'<figure><img src="{b64(im)}" width="{im.size[0]}" height="{im.size[1]}"><figcaption>{html.escape(cap)}</figcaption></figure>')
    figs.append('<h2>230 px x-height: Van den Keere, before, after</h2>')
    for ch in glyphs:
        im, sc = trio(ch, before, after); img(im, ch + ('' if sc == 1.0 else f'  (scaled {sc:.2f} to fit; NEAREST)'))
    figs.append('<h2>13 pt on the 2x reader, four-level pipeline: before, then after</h2>')
    for wtxt in words:
        img(eink(before, wtxt), 'before: ' + wtxt); img(eink(after, wtxt), 'after: ' + wtxt)
    doc = f'''<title>{html.escape(title)}</title>
<style>:root{{--paper:#F9F3E9;--ink:#5C332B;--soft:#8A6A62;--rule:#E4D8C8}}@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{--paper:#171B1B;--ink:#CFD4CC;--soft:#93A09B;--rule:#2B3331}}}}:root[data-theme="dark"]{{--paper:#171B1B;--ink:#CFD4CC;--soft:#93A09B;--rule:#2B3331}}
body{{background:var(--paper);color:var(--ink);margin:0;padding:16px 10px 60px;font:15px/1.45 -apple-system,Arial,sans-serif}}main{{max-width:900px;margin:0 auto}}h1{{font-size:22px;margin:0 0 6px}}h2{{font-size:13px;letter-spacing:.04em;text-transform:uppercase;color:var(--soft);margin:22px 0 8px;border-top:1px solid var(--rule);padding-top:10px}}
figure{{margin:0 0 10px}}figure img{{width:100%;max-width:375px;height:auto;image-rendering:pixelated;display:block;background:#fff}}figcaption{{font-size:11px;color:var(--soft);margin-top:2px}}p{{max-width:64ch;color:var(--soft);font-size:13px}}</style>
<main><h1>{html.escape(title)}</h1><p>PNG at native pixels; 750 px blocks shown at 375 CSS px (one image pixel per screen pixel on a 2x phone).</p>{''.join(figs)}</main>'''
    open(out, 'w').write(doc); print(out, len(doc) // 1024, 'KB')

if __name__ == '__main__':
    page(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6:])
