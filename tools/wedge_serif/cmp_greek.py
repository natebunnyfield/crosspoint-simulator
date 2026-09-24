"""Is Albo's GREEK the shape of a real Greek, letter by letter?

Round 373. Owner 2026-09-23, after seeing the Greek set rendered beside
reference faces: *"for greek letters: they are mostly wrong, trace"*. Round 371
had found the epsilon MIRRORED (it read as a digit 3) only by setting the
letters beside Times, Georgia and Palatino -- no instrument here could see a
wrong letter that is geometrically clean. This is that check as a script.

Two modes.

    PYTHON_GIL=0 python3 cmp_greek.py iou  <Albo.ttf> [--style roman|bold|italic] [--out DIR]
    PYTHON_GIL=0 python3 cmp_greek.py runs <Albo.ttf> <letters> [--refs Iowan,Georgia,...]
    PYTHON_GIL=0 python3 cmp_greek.py box  <Albo.ttf>

`iou` -- each letter and each reference reduced to an ink mask at ONE x-height
(the lowercase) or ONE cap height (the capitals), aligned on the BASELINE and
the left ink edge, compared as intersection over union -- `cmp_aldine_shape`'s
`compare_xh`, pointed at the Greek. An ascender that is too short, a descender
that is missing, a letter a third too narrow: all of them count against it.
The x-height is the font's OS/2 sxHeight where it declares one and the 'x''s
ink top where it does not (Iowan declares none); Albo's 'x' is NOT used,
because its wedge tips stand 22 units over its 429.

`runs` -- the tracing instrument. Every reference is mapped INTO ALBO'S UNITS
before it is read: vertically piecewise (0..xh onto 0..429, xh..ascender onto
429..Albo's own l, 0..descender onto 0..Albo's own p), horizontally by the
ratio of the two faces' o widths, so a reference letter lands at the size and
width it would have if it had been cut for Albo's Latin. The glyph is then
cut by horizontal scanlines and every ink run printed, so a stroke's CENTRE
at each height can be read, reference by reference, and their median taken.
Measuring a reference is research; what ships is Albo's own strokes on Albo's
own pen, drawn through the consensus of several faces
(docs/albo-method.md section 1d).

`box` -- the same mapping, bounding boxes only: width, bottom and top of every
Greek letter in every reference, and their median.
"""
import os, sys, statistics as st
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen

# round 379: the whole basic alphabet (the omicron and fourteen capitals are
# composites of the Latin letter; they are measured all the same)
G_LC = "αβγδεζηθικλμνξοπρσςτυφχψω"
G_UC = "ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ"
G = G_LC + G_UC

SUP = "/System/Library/Fonts/Supplemental/"
REFS = {
    'roman': [("Palatino", "/System/Library/Fonts/Palatino.ttc", 0),
              ("Iowan", SUP + "Iowan Old Style.ttc", 0),
              ("Georgia", SUP + "Georgia.ttf", 0),
              ("Times", SUP + "Times New Roman.ttf", 0)],
    'bold': [("Palatino", "/System/Library/Fonts/Palatino.ttc", 2),
             ("Iowan", SUP + "Iowan Old Style.ttc", 1),
             ("Georgia", SUP + "Georgia Bold.ttf", 0),
             ("Times", SUP + "Times New Roman Bold.ttf", 0)],
    'italic': [("Palatino", "/System/Library/Fonts/Palatino.ttc", 1),
               ("Iowan", SUP + "Iowan Old Style.ttc", 2),
               ("Georgia", SUP + "Georgia Italic.ttf", 0),
               ("Times", SUP + "Times New Roman Italic.ttf", 0)],
}
XH_PX = 240       # lowercase: every face scaled so its x-height is this
CAP_PX = 360      # capitals: ... so its cap height is this
PAD = 16


class Face:
    def __init__(self, path, idx=0):
        self.path, self.idx = path, idx
        f = TTFont(path, fontNumber=idx, lazy=True)
        self.upm = f['head'].unitsPerEm; self.gs = f.getGlyphSet(); self.cm = f.getBestCmap()
        os2 = f['OS/2']
        sx = getattr(os2, 'sxHeight', 0) or 0
        self.xh = sx if sx > 0 else self.bb('x')[3]
        cap = getattr(os2, 'sCapHeight', 0) or 0
        self.cap = cap if cap > 0 else self.bb('H')[3]
        self.asc = self.bb('l')[3]; self.desc = self.bb('p')[1]
        o = self.bb('o'); self.ow = o[2] - o[0]
        O = self.bb('O'); self.Ow = O[2] - O[0]

    def bb(self, ch):
        bp = BoundsPen(self.gs); self.gs[self.cm[ord(ch)]].draw(bp); return bp.bounds

    def mask(self, ch, units_per_px):
        """Ink mask at `units_per_px`, baseline at a known row. Returns
        (mask, baseline_row, px_per_unit)."""
        px = int(round(self.upm / units_per_px))
        f = ImageFont.truetype(self.path, px, index=self.idx)
        W = px * 3; H = px * 3; base = int(px * 1.9)
        im = Image.new('L', (W, H), 255)
        ImageDraw.Draw(im).text((px // 2, base), ch, font=f, fill=0, anchor='ls')
        return np.asarray(im) < 128, base, px / self.upm


def mask_norm(face, ch):
    """Mask scaled so the x-height (lowercase) or cap height (capitals) is
    XH_PX / CAP_PX."""
    target = CAP_PX if ch.isupper() else XH_PX
    ref_h = face.cap if ch.isupper() else face.xh
    return face.mask(ch, ref_h / target)[:2]


def compare(ref, rb, cand, cb):
    ys, xs = np.where(ref); rl = xs.min()
    ys, xs = np.where(cand); cl = xs.min()
    dx = rl - cl; dy = rb - cb
    c = np.zeros_like(ref)
    ys, xs = np.where(cand); ys2 = ys + dy; xs2 = xs + dx
    ok = (ys2 >= 0) & (ys2 < c.shape[0]) & (xs2 >= 0) & (xs2 < c.shape[1])
    c[ys2[ok], xs2[ok]] = True
    inter = (ref & c).sum(); union = (ref | c).sum()
    iou = inter / union if union else 0.0
    ys, xs = np.where(ref | c)
    y0, y1, x0, x1 = ys.min() - PAD, ys.max() + PAD, xs.min() - PAD, xs.max() + PAD
    r2, c2 = ref[y0:y1, x0:x1], c[y0:y1, x0:x1]
    img = np.full(r2.shape, 255, np.uint8)
    img[r2 & ~c2] = 200; img[c2 & ~r2] = 110; img[r2 & c2] = 0
    return iou, Image.fromarray(img)


def iou_table(albo, style='roman', out=None, letters=G):
    A = Face(albo)
    refs = [(n, Face(p, i)) for n, p, i in REFS[style]]
    res = {}
    for ch in letters:
        am, ab = mask_norm(A, ch)
        row = {}
        for n, F in refs:
            if ord(ch) not in F.cm: continue
            rm, rbase = mask_norm(F, ch)
            iou, img = compare(rm, rbase, am, ab)
            row[n] = iou
            if out:
                os.makedirs(out, exist_ok=True)
                img.save(os.path.join(out, 'ov_%04X_%s.png' % (ord(ch), n)))
        res[ch] = row
    return res


# ---------------------------------------------------------------- tracing
def albo_map(A):
    """Albo's own anchors: design x-height, its l's top, its p's bottom, its
    o's and O's widths, its cap height."""
    return dict(xh=A.xh, asc=A.asc, desc=A.desc, ow=A.ow, Ow=A.Ow, cap=A.cap)


def map_y(F, M, y, cap=False):
    if cap: return y / F.cap * M['cap']
    if y >= F.xh: return M['xh'] + (y - F.xh) / (F.asc - F.xh) * (M['asc'] - M['xh'])
    if y >= 0: return y / F.xh * M['xh']
    return y / F.desc * M['desc']


def unmap_y(F, M, ya, cap=False):
    if cap: return ya / M['cap'] * F.cap
    if ya >= M['xh']: return F.xh + (ya - M['xh']) / (M['asc'] - M['xh']) * (F.asc - F.xh)
    if ya >= 0: return ya / M['xh'] * F.xh
    return ya / M['desc'] * F.desc


def runs_at(F, M, ch, heights, upp=2.0):
    """For each Albo-unit height, the ink runs of F's glyph as (x0, x1) in
    Albo units measured from the glyph's left ink edge."""
    m, base, ppu = F.mask(ch, upp)
    ys, xs = np.where(m); left = xs.min()
    kx = (M['Ow'] / F.Ow) if ch.isupper() else (M['ow'] / F.ow)
    out = {}
    for ya in heights:
        yr = unmap_y(F, M, ya, ch.isupper())
        row = int(round(base - yr * ppu))
        if row < 0 or row >= m.shape[0]: out[ya] = []; continue
        line = m[row]; rr = []; x = 0; n = len(line)
        while x < n:
            if line[x]:
                x0 = x
                while x < n and line[x]: x += 1
                rr.append(((x0 - left) / ppu * kx, (x - left) / ppu * kx))
            else: x += 1
        out[ya] = rr
    return out


def cols_at(F, M, ch, xs_frac, upp=2.0):
    """Vertical scanlines at fractions of the ink width: runs as (y0, y1) in
    Albo units."""
    m, base, ppu = F.mask(ch, upp)
    ys, xs = np.where(m); left, right = xs.min(), xs.max()
    out = {}
    for fr in xs_frac:
        col = int(round(left + (right - left) * fr)); line = m[:, col]; rr = []; y = 0; n = len(line)
        while y < n:
            if line[y]:
                y0 = y
                while y < n and line[y]: y += 1
                a = map_y(F, M, (base - (y - 1)) / ppu, ch.isupper()); b = map_y(F, M, (base - y0) / ppu, ch.isupper())
                rr.append((a, b))
            else: y += 1
        out[fr] = rr[::-1]
    return out


def main():
    args = sys.argv[1:]
    if not args: print(__doc__); return 2
    mode = args[0]; albo = args[1]
    style = 'roman'
    if '--style' in args: style = args[args.index('--style') + 1]
    if mode == 'iou':
        out = args[args.index('--out') + 1] if '--out' in args else None
        res = iou_table(albo, style, out)
        names = [n for n, _, _ in REFS[style]]
        print('letter ' + ' '.join('%8s' % n for n in names) + '    mean')
        for ch, row in res.items():
            vals = [row.get(n) for n in names]
            ok = [v for v in vals if v is not None]
            print('%s U+%04X ' % (ch, ord(ch)) + ' '.join('%8.3f' % v if v is not None else '       -' for v in vals)
                  + '   %6.3f' % (sum(ok) / len(ok)))
        return 0
    A = Face(albo); M = albo_map(A); M['xh'] = A.xh
    names = None
    if '--refs' in args: names = args[args.index('--refs') + 1].split(',')
    refs = [(n, Face(p, i)) for n, p, i in REFS[style] if names is None or n in names]
    if mode == 'box':
        print('Albo anchors', {k: round(v) for k, v in M.items()})
        for ch in G:
            rows = []
            for n, F in refs:
                x0, y0, x1, y1 = F.bb(ch)
                kx = (M['Ow'] / F.Ow) if ch.isupper() else (M['ow'] / F.ow)
                rows.append((n, (x1 - x0) * kx, map_y(F, M, y0, ch.isupper()), map_y(F, M, y1, ch.isupper())))
            ax0, ay0, ax1, ay1 = A.bb(ch)
            med = [st.median(r[k] for r in rows) for k in (1, 2, 3)]
            print('%s Albo w %4d  %5d..%4d | ' % (ch, ax1 - ax0, ay0, ay1) +
                  '  '.join('%s %4d %5d..%4d' % (n[:3], w, b, t) for n, w, b, t in rows) +
                  ' | MEDIAN w %4d  %5d..%4d' % tuple(med))
        return 0
    if mode == 'runs':
        letters = args[2]
        for ch in letters:
            if ch.isupper(): hs = [M['cap'] * f for f in (0.02, 0.1, 0.25, 0.4, 0.5, 0.6, 0.75, 0.9, 0.98)]
            else: hs = [-250, -150, -60, 10, 45, 90, 150, 215, 280, 340, 390, 420, 480, 560, 640, 720, 760]
            print('\n=== %s  (x from the glyph\'s left ink edge, Albo units)' % ch)
            srcs = [('ALBO', A)] + refs
            data = [(n, runs_at(F, M, ch, hs)) for n, F in srcs]
            for ya in hs:
                print('y=%5d  ' % ya + ' | '.join('%s %s' % (n[:4], ' '.join('%d-%d' % (a, b) for a, b in d[ya])) for n, d in data))
        return 0
    if mode == 'cols':
        letters = args[2]
        fr = [0.1, 0.25, 0.4, 0.5, 0.6, 0.75, 0.9]
        for ch in letters:
            print('\n=== %s columns (fraction of ink width): y runs, Albo units' % ch)
            srcs = [('ALBO', A)] + refs
            data = [(n, cols_at(F, M, ch, fr)) for n, F in srcs]
            for f in fr:
                print('x=%.2f  ' % f + ' | '.join('%s %s' % (n[:4], ' '.join('%d..%d' % (a, b) for a, b in d[f])) for n, d in data))
        return 0
    print(__doc__); return 2


if __name__ == '__main__':
    sys.exit(main())
