import sys, json, math, html
sys.path.insert(0, '/Users/natebunnyfield/src/crosspoint-simulator/tools/wedge_serif')
from albo_bumps import GLYPHS
from regions import ROMAN, ITALIC, CUT
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from PIL import Image, ImageDraw
SP = '/private/tmp/claude-501/-Users-natebunnyfield-src-crosspoint-simulator/06bd1159-4703-424c-abda-64842a60926b/scratchpad'
F = 2.135; SC = 300 / 674.0
def cell(gi):
    cx0 = 20 + (gi % 6) * 705; cy0 = 60 + (gi // 6) * 615
    return cx0 + 105, cy0 + 435
def g2u(gi, dx, dy, cut):
    ox, base = cell(gi); sx, sy = dx * F, dy * F + cut
    return (sx - ox) / SC, (base - sy) / SC
def contours(gs, name):
    pen = RecordingPen(); gs[name].draw(pen); cs = []; cur = []
    for op, a in pen.value:
        if op == 'moveTo': cur = [a[0]]
        elif op == 'lineTo': cur.append(a[0])
        elif op in ('closePath', 'endPath'): cs.append(cur); cur = []
    if cur: cs.append(cur)
    return cs
out = {}
for style, ttf, regs, js in (('roman', f'{SP}/r232_rom/Albo-Medium.ttf', ROMAN, f'{SP}/bumps/bumps-roman.json'),
                             ('italic', f'{SP}/r231f_it/Albo-Italic.ttf', ITALIC, f'{SP}/bumps/bumps-italic.json')):
    f = TTFont(ttf); gs = f.getGlyphSet(); cmap = f.getBestCmap(); J = json.load(open(js))
    for rid, ch, half, (dx0, dy0, dx1, dy1), name, reading in regs:
        gi = GLYPHS.index(ch); cut = 0 if half == 'top' else CUT[style]
        ux0, uy1 = g2u(gi, dx0, dy0, cut); ux1, uy0 = g2u(gi, dx1, dy1, cut)
        cx, cy = (ux0 + ux1) / 2, (uy0 + uy1) / 2
        # my display-coordinate readings are +-20 px (+-100 units); a mark is always ON ink,
        # so a box holding no outline vertex is moved to the nearest vertex
        gn = cmap[ord(ch)]; cs = contours(gs, gn); allv = [q for c in cs for q in c]
        inside = [q for q in allv if ux0 <= q[0] <= ux1 and uy0 <= q[1] <= uy1]
        if not inside:
            q = min(allv, key=lambda q: (q[0]-cx)**2 + (q[1]-cy)**2)
            ddx, ddy = q[0]-cx, q[1]-cy; ux0 += ddx; ux1 += ddx; uy0 += ddy; uy1 += ddy; cx, cy = q
            snapped = True
        else: snapped = False
        half_w = max(125.0, (ux1 - ux0) / 2 + 70, (uy1 - uy0) / 2 + 70)
        Z = min(3.0, 900 / (2 * half_w))
        bx0, by0, bx1, by1 = cx - half_w, cy - half_w, cx + half_w, cy + half_w
        W = H = int(2 * half_w * Z)
        im = Image.new('RGB', (W, H), (255, 255, 255)); d = ImageDraw.Draw(im, 'RGBA')
        P = lambda x, y: ((x - bx0) * Z, (by1 - y) * Z)
        for c in cs: d.polygon([P(*p) for p in c], fill=(0, 0, 0, 45))
        for c in cs:
            pts = [P(*p) for p in c]; d.line(pts + [pts[0]], fill=(0, 0, 0, 255), width=1)
            for p in pts: d.ellipse([p[0]-1.6, p[1]-1.6, p[0]+1.6, p[1]+1.6], fill=(200, 0, 0, 255))
        for gy in (0, 429, 674):
            if by0 <= gy <= by1: d.line([P(bx0, gy), P(bx1, gy)], fill=(0, 0, 255, 70))
        d.rectangle([P(ux0, uy1), P(ux1, uy0)], fill=(255, 230, 0, 55), outline=(200, 170, 0, 255), width=2)
        for e in J:
            if e['glyph'] == ch and bx0 <= e['x'] <= bx1 and by0 <= e['y'] <= by1:
                p = P(e['x'], e['y']); r = 22 * Z / SC * 0.45
                d.ellipse([p[0]-r, p[1]-r, p[0]+r, p[1]+r], outline=(220, 0, 0, 255), width=2)
                d.text((p[0] + r + 2, p[1] - r), str(e['n']), fill=(220, 0, 0, 255))
        d.text((6, 4), f"{rid}  {style} {ch}  {name}   [{int(bx0)},{int(by0)} - {int(bx1)},{int(by1)}] units, {Z:.2f} px/unit", fill=(0, 0, 200, 255))
        fn = f"{rid}.png"; im.save(f"{SP}/ledger/{fn}")
        out[rid] = dict(style=style, glyph=ch, name=name, reading=reading, file=fn, box=[round(ux0), round(uy0), round(ux1), round(uy1)], size=[W, H], snapped=snapped)
json.dump(out, open(f'{SP}/ledger/index.json', 'w'), indent=1)
print(len(out), 'crops')
