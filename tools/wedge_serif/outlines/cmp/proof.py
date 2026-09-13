"""The rebuild's proof page (guide §4, mobile-friendly): every block is
rendered 750 px wide and shown at 375 CSS px with image-rendering:
pixelated (one image pixel per screen pixel on a 2x phone); PNG only.
    python3 -m outlines.cmp.proof <new.ttf> <before.ttf> <out.html>"""
import sys, os, io, base64, html, math
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont
import round19
from . import overlay4 as O

W = 750
LEVELS = (255, 200, 96, 0); THRESH = (0.108, 0.42, 0.812)   # the reader's four-level pipeline (round 53)

def b64(im):
    buf = io.BytesIO(); im.save(buf, format='PNG'); return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()

def wrap(font, text, width):
    words = text.split(' '); lines, cur = [], ''
    for w in words:
        t = (cur + ' ' + w).strip()
        if font.getlength(t) <= width or not cur: cur = t
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines

def block(path, text, px, line=1.3, width=W, pad=10, rules=False):
    font = ImageFont.truetype(path, px); asc, desc = font.getmetrics()
    lines = wrap(font, text, width - 2 * pad); lh = int(round(px * line))
    im = Image.new('L', (width, pad * 2 + lh * len(lines)), 255); d = ImageDraw.Draw(im)
    for i, ln in enumerate(lines):
        y = pad + i * lh + asc
        if rules:
            f = TTFont(path); xh = f['OS/2'].sxHeight * px / f['head'].unitsPerEm
            d.line([(0, y), (width, y)], fill=225); d.line([(0, y - xh), (width, y - xh)], fill=235)
        d.text((pad, y), ln, font=font, fill=0, anchor='ls')
    return im

def eink(path, text, pt=13, scale=2, ss=8, line=1.25, width=W, pad=8):
    """13 pt on the 2x reader = 54 px em, rendered 8x supersampled and
    quantized to the panel's four levels at the reader's thresholds."""
    px = int(round(pt * scale * 96 / 72 * 100)) // 100   # 54
    px = 54
    big = ImageFont.truetype(path, px * ss); small = ImageFont.truetype(path, px)
    lines = wrap(small, text, width - 2 * pad); lh = px * line
    H = int(pad * 2 + lh * len(lines) + px * 0.4)
    im = Image.new('L', (width * ss, H * ss), 255); d = ImageDraw.Draw(im)
    asc = big.getmetrics()[0]
    for i, ln in enumerate(lines):
        d.text((pad * ss, int((pad + i * lh) * ss) + asc), ln, font=big, fill=0, anchor='ls')
    import numpy as np
    a = np.asarray(im, dtype=np.float32) / 255.0
    cov = 1.0 - a.reshape(H, ss, width, ss).mean(axis=(1, 3))
    out = np.full(cov.shape, 255, dtype=np.uint8)
    out[cov >= THRESH[0]] = LEVELS[1]; out[cov >= THRESH[1]] = LEVELS[2]; out[cov >= THRESH[2]] = LEVELS[3]
    return Image.fromarray(out, 'L')

def crop_joins(path, text, px=600, width=W):
    font = ImageFont.truetype(path, px); asc, desc = font.getmetrics()
    w = int(font.getlength(text)) + 40
    im = Image.new('L', (w, asc + desc), 255); ImageDraw.Draw(im).text((20, asc), text, font=font, fill=0, anchor='ls')
    # split into 750-wide strips at native pixels
    strips = []
    for x in range(0, w, width): strips.append(im.crop((x, 0, min(w, x + width), asc + desc)))
    return strips

def page(new, before, out):
    P = round19.PARAGRAPHS
    imgs = []
    def img(im, cap): imgs.append(f'<figure><img src="{b64(im)}" width="{im.size[0]}" height="{im.size[1]}"><figcaption>{html.escape(cap)}</figcaption></figure>')
    def h2(t): imgs.append(f'<h2>{html.escape(t)}</h2>')
    def p(t): imgs.append(f'<p>{t}</p>')
    h2('The whole set, 230 px em (the rebuild)')
    for txt in ("ABCD EFGH IJKL MNOP QRST UVWX YZ", "abcde fghij klmno pqrst uvwxy z", "01234 56789", ".,:;! ?'\"‘’ “”-–— ()[]", "/\\*+= &%#@ _…"):
        img(block(new, txt, 230, line=1.25, rules=True), txt.replace(' ', ''))
    h2('Running text, 13 pt on the 2x reader, the four-level pipeline')
    p('Each paragraph twice: the REBUILD, then the round-51 font it replaces. 54 px em, 8x supersampled, quantized at 0.108 / 0.42 / 0.812 to 255 / 200 / 96 / 0.')
    for i, t in enumerate(P[:3]):
        img(eink(new, t), f'rebuild, paragraph {i + 1}'); img(eink(before, t), f'round 51, paragraph {i + 1}')
    h2('Words at 54 px, rebuild over round 51')
    for txt in ("egg ffi QU Kirk 3.5% Jade Qu Ty Va ry rn", "the of and to in a is that for it as was with be by on not he",
                "Hamburgefonstiv quick fjord zephyrs", "minimum nunnery mummer hurry"):
        img(block(new, txt, 54, line=1.3, rules=True), 'rebuild: ' + txt); img(block(before, txt, 54, line=1.3, rules=True), 'round 51: ' + txt)
    h2('Joins at 600 px (crops at native pixels)')
    for txt in ("nag", "beg", "BRK", "&Qy"):
        for s in crop_joins(new, txt): img(s, txt)
    # overlays
    table, counts, per, names = O.compare(new); tb, cb, pb, _ = O.compare(before)
    h2('Every glyph over the four references')
    p('Fjord black at 72%; EB Garamond 400 red, Van den Keere purple, Dante green, Edgar ochre at 26%; x-heights matched, left ink edges aligned. Flags fire at width ±20%, height ±15%, mean stroke ±25%, top/bottom ±0.12 xh.')
    rows = ''.join(f'<tr><td>{html.escape(n)}</td><td>{cb[n]}</td><td>{counts[n]}</td></tr>' for n in names)
    p(f'<table><tr><th>reference</th><th>round 51 flagged</th><th>rebuild flagged</th></tr>{rows}</table> (of {len(table)} glyphs; the mean-stroke figure of the round-51 font was understated by its overlapping contours -- its perimeter counted every stroke polygon -- so its stroke flags are not comparable)')
    fams = [('arches n m h u r', 'nmhur'), ('rounds o c e', 'oce'), ('bowls b d p q, a, s', 'bdpqas'), ('i j l f t', 'ijlft'), ('diagonals v w x y z k', 'vwxyzk'), ('g', 'g'),
            ('capitals', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), ('figures', '0123456789'), ('marks', ''.join(ch for ch in table if not ch.isalnum()))]
    for name, chars in fams:
        sub = {ch: table[ch] for ch in chars if ch in table}
        imgs.append(f'<h3>{html.escape(name)}</h3><div class="grid">{O.cells_html(sub, names)}</div>')
    body = ''.join(imgs)
    doc = f'''<title>Fjord Rebuild</title>
<style>:root{{--paper:#F9F3E9;--ink:#5C332B;--soft:#8A6A62;--rule:#E4D8C8}}@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{--paper:#171B1B;--ink:#CFD4CC;--soft:#93A09B;--rule:#2B3331}}}}:root[data-theme="dark"]{{--paper:#171B1B;--ink:#CFD4CC;--soft:#93A09B;--rule:#2B3331}}
body{{background:var(--paper);color:var(--ink);margin:0;padding:16px 10px 60px;font:15px/1.45 -apple-system,Arial,sans-serif}}main{{max-width:900px;margin:0 auto}}h1{{font-size:22px;margin:0 0 6px}}h2{{font-size:13px;letter-spacing:.04em;text-transform:uppercase;color:var(--soft);margin:26px 0 8px;border-top:1px solid var(--rule);padding-top:10px}}h3{{font-size:13px;color:var(--soft);margin:14px 0 4px}}
figure{{margin:0 0 10px}}figure img{{width:100%;max-width:375px;height:auto;image-rendering:pixelated;display:block;background:#fff}}figcaption{{font-size:11px;color:var(--soft);margin-top:2px}}
p{{max-width:64ch;color:var(--soft);font-size:13px}}table{{border-collapse:collapse;font-size:13px}}td,th{{padding:2px 8px;border-bottom:1px solid var(--rule);text-align:left}}
.grid{{display:flex;flex-wrap:wrap;gap:6px}}.cell{{background:#fff;border:1px solid var(--rule);padding:4px 6px;border-radius:4px;max-width:180px}}.ch{{font:600 13px Georgia;color:#6f6a60}}.flag{{display:inline-block;font-size:10px;border-left:3px solid;padding:0 4px;margin:2px 2px 0 0;background:#f7efe9;color:#333}}</style>
<main><h1>Fjord Rebuild</h1><p>All 93 glyphs redrawn as designed outlines (2026-09-13): stems with their wedges as one contour, bowls with drawn counters, real joins by outline union, the pen as the weight reference, the wedge family and every §3 ruling kept, the one-in-four linear cut applied last. Images are PNG at native pixels; 750 px blocks shown at 375 CSS px.</p>{body}</main>'''
    open(out, 'w').write(doc); print(out, len(doc) // 1024, 'KB')

if __name__ == '__main__':
    page(sys.argv[1], sys.argv[2], sys.argv[3])
