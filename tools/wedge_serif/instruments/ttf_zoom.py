"""ttf_zoom.py -- one glyph from a BUILT font, filled, every on-curve point dotted, at any zoom.

    python3 instruments/ttf_zoom.py out.png FONT.ttf GLYPH [x0,y0,x1,y1] [FONT2.ttf]
    env: SC (px per unit, default 1.2 whole glyph / 4 with a box), UNSHEAR (deg; 0 = as built)

GLYPH is a character or a glyph name. With a box (font units) only that region is drawn, larger.
With a second font the two outlines are drawn over each other (first filled gray, second as a red
line), which is the before/after at a join. The build's own view (glyph_zoom.py) draws from the
live builder and is hard-wired to the c; this one reads the shipped TTF, so it shows exactly what
the gates and the reader see. Written for the 2026-09-28 issue sweep.
"""
import sys, os, math
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen

out = sys.argv[1]; path = sys.argv[2]; gname = sys.argv[3]
box = [float(v) for v in sys.argv[4].split(',')] if len(sys.argv) > 4 and ',' in sys.argv[4] else None
path2 = sys.argv[5] if len(sys.argv) > 5 else (sys.argv[4] if len(sys.argv) > 4 and ',' not in sys.argv[4] else None)
UN = float(os.environ.get("UNSHEAR", "0")); T = math.tan(math.radians(UN))


class Flat(BasePen):
    def __init__(s, gs): super().__init__(gs); s.c = []; s.cur = []; s.on = []
    def _moveTo(s, p): s.cur = [p]; s.on.append(p)
    def _lineTo(s, p): s.cur.append(p); s.on.append(p)
    def _curveToOne(s, a, b, c):
        p0 = s.cur[-1]
        for i in range(1, 17):
            t = i / 16; m = 1 - t
            s.cur.append((m**3*p0[0] + 3*m*m*t*a[0] + 3*m*t*t*b[0] + t**3*c[0], m**3*p0[1] + 3*m*m*t*a[1] + 3*m*t*t*b[1] + t**3*c[1]))
        s.on.append(c)
    def _qCurveToOne(s, a, b):
        p0 = s.cur[-1]
        for i in range(1, 13):
            t = i / 12; m = 1 - t
            s.cur.append((m*m*p0[0] + 2*m*t*a[0] + t*t*b[0], m*m*p0[1] + 2*m*t*a[1] + t*t*b[1]))
        s.on.append(b)
    def _closePath(s):
        if s.cur: s.c.append(s.cur)
        s.cur = []
    _endPath = _closePath


def load(p):
    f = TTFont(p); gs = f.getGlyphSet(); cm = f.getBestCmap()
    name = cm.get(ord(gname)) if len(gname) == 1 else gname
    pen = Flat(gs); gs[name].draw(pen)
    un = lambda q: (q[0] - q[1] * T, q[1])
    return [[un(q) for q in c] for c in pen.c], [un(q) for q in pen.on]


C, ON = load(path)
C2, ON2 = load(path2) if path2 else ([], [])
xs = [x for c in C + C2 for x, _ in c]; ys = [y for c in C + C2 for _, y in c]
if box is None:
    box = [min(xs) - 20, min(ys) - 20, max(xs) + 20, max(ys) + 20]
SC = float(os.environ.get("SC", "4" if len(sys.argv) > 4 and ',' in sys.argv[4] else "1.2"))
x0, y0, x1, y1 = box
W, H = int((x1 - x0) * SC), int((y1 - y0) * SC)
im = Image.new("RGB", (W, H), (250, 249, 246)); d = ImageDraw.Draw(im)
P = lambda x, y: ((x - x0) * SC, (y1 - y) * SC)
# even-odd fill of the first font
mask = Image.new("L", (W, H), 0); md = ImageDraw.Draw(mask)
for c in C:
    tmp = Image.new("L", (W, H), 0); ImageDraw.Draw(tmp).polygon([P(*q) for q in c], fill=255)
    from PIL import ImageChops
    mask = ImageChops.logical_xor(mask.convert("1"), tmp.convert("1")).convert("L")
im.paste((70, 70, 70), (0, 0, W, H), mask)
for q in ON:
    if x0 <= q[0] <= x1 and y0 <= q[1] <= y1:
        a, b = P(*q); d.ellipse([a - 2.5, b - 2.5, a + 2.5, b + 2.5], fill=(0, 190, 255))
for c in C2:
    d.line([P(*q) for q in c] + [P(*c[0])], fill=(230, 30, 30), width=2)
F = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 14)
d.text((6, 6), f"{os.path.basename(path)} {gname} box {box} {SC} px/u" + (f"  red: {os.path.basename(os.path.dirname(path2))}/{os.path.basename(path2)}" if path2 else ""), fill=(200, 0, 0), font=F)
im.save(out); print(out, im.size, "box", [round(v) for v in box])
