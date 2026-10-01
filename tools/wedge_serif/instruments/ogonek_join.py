"""ogonek_join.py -- does every ogonek touch its letter, and does any of it poke out beside it?
Round 452 (2026-09-30), from the traced ogonek's root (docs/albo-round-452-2026-09-30.md).

    python3 instruments/ogonek_join.py BUILD_DIR [CHARS]            # the table
    python3 instruments/ogonek_join.py BUILD_DIR [CHARS] --zoom OUT.png   # each join drawn

Per composite, base and mark as placed:
  gap   the distance between the letter's ink and the mark's (must be 0: a floating mark);
  poke  the mark's ink ABOVE the baseline that the letter's ink does not cover, in square units.
        A mark raised to meet a foot that sits above the line (the Italic a's stem bottoms out
        6 units up) shows here as poke under that foot, which is not a defect -- read --zoom.
Exit 1 on any gap > 0.5 unit.
"""
import sys
from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen
import shapely.geometry as sg

CUTS = ["Regular", "Italic", "Bold", "BoldItalic"]


class _Pen(BasePen):
    def __init__(self, gs): super().__init__(gs); self.cs = []; self.cur = []
    def _moveTo(self, p): self.cur = [p]
    def _lineTo(self, p): self.cur.append(p)
    def _qCurveToOne(self, p1, p2):
        p0 = self.cur[-1]
        for i in range(1, 9):
            t = i / 8; self.cur.append(((1-t)**2*p0[0]+2*(1-t)*t*p1[0]+t*t*p2[0], (1-t)**2*p0[1]+2*(1-t)*t*p1[1]+t*t*p2[1]))
    def _curveToOne(self, p1, p2, p3):
        p0 = self.cur[-1]
        for i in range(1, 9):
            t = i / 8; mt = 1 - t
            self.cur.append((mt**3*p0[0]+3*mt*mt*t*p1[0]+3*mt*t*t*p2[0]+t**3*p3[0], mt**3*p0[1]+3*mt*mt*t*p1[1]+3*mt*t*t*p2[1]+t**3*p3[1]))
    def _closePath(self): self.cs.append(self.cur); self.cur = []


def geom(gs, name, dx=0, dy=0):
    p = _Pen(gs); gs[name].draw(p)
    g = None
    for c in p.cs:
        if len(c) < 3: continue
        q = sg.Polygon([(x + dx, y + dy) for x, y in c]).buffer(0)
        g = q if g is None else g.symmetric_difference(q)      # even-odd: counters come out
    return g


def joins(D, chars):
    import os
    for st in CUTS:
        if not os.path.exists(f"{D}/Albo-{st}.ttf"): continue      # gates.sh builds two cuts
        f = TTFont(f"{D}/Albo-{st}.ttf"); gs = f.getGlyphSet(); cm = f.getBestCmap(); glyf = f['glyf']
        for ch in chars:
            g = glyf[cm[ord(ch)]]
            if not g.isComposite(): yield st, ch, None, None, None, None; continue
            (b, bx, by), (m, mx, my) = [(c.glyphName, c.x, c.y) for c in g.components][:2]
            gb = geom(gs, b, bx, by); gm = geom(gs, m, mx, my)
            up = gm.intersection(sg.box(-1e4, 0.5, 1e4, 1e4)).difference(gb.buffer(0.5))
            yield st, ch, gb.distance(gm), up, gb, gm


def zoom(D, chars, out):
    from PIL import Image, ImageDraw
    SC = 1.6; rows = {}
    for st, ch, gap, up, gb, gm in joins(D, chars):
        if gb is None: continue
        x0, y0, x1, y1 = gm.bounds; cx = (x0 + x1) / 2; win = (cx - 160, -250, cx + 160, 90)
        im = Image.new('RGB', (int(320 * SC), int(340 * SC)), 'white'); d = ImageDraw.Draw(im)
        def Q(x, y): return ((x - win[0]) * SC, (win[3] - y) * SC)
        def fill(geo, col):
            for p in getattr(geo, 'geoms', [geo]):
                if p.is_empty or p.geom_type != 'Polygon': continue
                d.polygon([Q(*q) for q in p.exterior.coords], fill=col)
                for h in p.interiors: d.polygon([Q(*q) for q in h.coords], fill='white')
        fill(gb, (170, 170, 170)); fill(gm.difference(gb), (40, 40, 40)); fill(up, (230, 30, 30))
        d.line([Q(win[0], 0), Q(win[2], 0)], fill=(60, 140, 230))
        d.text((4, 4), f"{st} {ch} gap {gap:.0f} poke {up.area:.0f}", fill=(0, 0, 0))
        rows.setdefault(st, []).append(im)
    strips = []
    for st in CUTS:
        r = rows.get(st, [])
        if not r: continue
        s = Image.new('RGB', (sum(i.width for i in r), r[0].height), 'white'); x = 0
        for i in r: s.paste(i, (x, 0)); x += i.width
        strips.append(s)
    o = Image.new('RGB', (max(s.width for s in strips), sum(s.height for s in strips)), 'white'); y = 0
    for s in strips: o.paste(s, (0, y)); y += s.height
    o.save(out); print(out, o.size)


if __name__ == '__main__':
    args = [a for a in sys.argv[1:]]
    out = None
    if '--zoom' in args:
        i = args.index('--zoom'); out = args[i + 1]; del args[i:i + 2]
    D = args[0]; chars = args[1] if len(args) > 1 else "ąęįųĄĘĮŲ"
    bad = 0; line = {}
    for st, ch, gap, up, gb, gm in joins(D, chars):
        if gb is None: line.setdefault(st, []).append(f"{ch} drawn"); continue
        if gap > 0.5: bad += 1
        line.setdefault(st, []).append(f"{ch} gap {gap:.0f} poke {up.area:.0f}")
    for st in CUTS:
        if st in line: print(f"{st:10s} " + " | ".join(line[st]))
    if out: zoom(D, chars, out)
    sys.exit(1 if bad else 0)
