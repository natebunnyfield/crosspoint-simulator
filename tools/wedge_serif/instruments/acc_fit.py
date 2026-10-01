"""acc_fit.py -- every accent AS IT SITS ON ITS LETTER, in any font: size, weight, gap and centring,
all per the font's own x-height (weights per its own stem), so Albo and the references compare
directly. Round 450 (2026-09-30), owner: "resize accents to fit rest and center the marks".

    venv/bin/python instruments/acc_fit.py [--bases lc|uc] FONT[@slant] ...

The mark is read off the ACCENTED glyph's raster minus its base's raster (same origin, unhinted,
1 px per unit), keeping only ink above the base's top (above marks) or below its bottom (below
marks). That is what the reader sees, whatever the font does with separate capital accents,
composites or drawn glyphs; the spacing mark (U+00B4 ...) is never read.

Columns, each a median over the bases that carry the mark:
  w, h      the mark's ink box / x-height
  wt        its mean stroke width (2 x area / edge length) / the font's l stem
  gap       mark bottom minus base top (above) or base bottom minus mark top (below) / x-height
  box       mark centre minus the base's ink-box centre / x-height          (+ = right)
  top       mark centre minus the centroid of the base's ink in its top half / x-height
  stem      for stem letters (i, l, j), mark centre minus the stem's own centre at 0.5 x-height
In an italic every centre is carried along the slant to the mark's own height, as the eye reads it.
"""
import sys, math, statistics, freetype, numpy as np
from scipy import ndimage as ndi
from fontTools.ttLib import TTFont

MARKS = {
    'acute':      ('áéíóúý', 'ÁÉÍÓÚÝ', 'above'),
    'grave':      ('àèìòù', 'ÀÈÌÒÙ', 'above'),
    'circumflex': ('âêîôû', 'ÂÊÎÔÛ', 'above'),
    'caron':      ('čšžěřň', 'ČŠŽĚŘŇ', 'above'),
    'tilde':      ('ãñõ', 'ÃÑÕ', 'above'),
    'macron':     ('āēīōū', 'ĀĒĪŌŪ', 'above'),
    'breve':      ('ăğŭ', 'ĂĞŬ', 'above'),
    'dieresis':   ('äëïöüÿ', 'ÄËÏÖÜŸ', 'above'),
    'dot':        ('ċėżġ', 'ĊĖŻĠ', 'above'),
    'ring':       ('åů', 'ÅŮ', 'above'),
    'dblacute':   ('őű', 'ŐŰ', 'above'),
    'cedilla':    ('çş', 'ÇŞ', 'below'),
    'ogonek':     ('ąęįų', 'ĄĘĮŲ', 'below'),
}
STEMS = set('ilıIL')

def base_of(ch):
    import unicodedata
    b = unicodedata.normalize('NFD', ch)[0]
    return 'ı' if b == 'i' else ('ȷ' if b == 'j' else b)

class Font:
    def __init__(self, arg):
        p, deg = (arg.split('@') + [None])[:2]
        self.name = p.split('/')[-1]
        self.t = TTFont(p)
        if deg is None:
            try: deg = abs(self.t['post'].italicAngle)
            except Exception: deg = 0.0
        self.k = math.tan(math.radians(float(deg)))
        self.f = freetype.Face(p); self.upm = self.f.units_per_EM; self.f.set_pixel_sizes(0, self.upm)
        self.cmap = self.t.getBestCmap()
        sx = self.t['OS/2'].sxHeight if self.name.startswith('Albo') else 0
        if sx and sx > 0:
            self.xh = float(sx)
        else:
            self.f.load_char('x', freetype.FT_LOAD_NO_HINTING); self.xh = self.f.glyph.metrics.horiBearingY / 64
        a, l, top = self.raster('l')
        row = int(top - 0.5 * self.xh); xs = np.nonzero(a[row])[0]
        self.stem = (xs.max() - xs.min() + 1) / math.sqrt(1 + self.k ** 2)
    def has(self, ch): return ord(ch) in self.cmap
    def raster(self, ch):
        self.f.load_char(ch, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING)
        b = self.f.glyph.bitmap
        a = np.array(b.buffer, np.uint8).reshape(b.rows, b.pitch)[:, :b.width] >= 128
        return a, self.f.glyph.bitmap_left, self.f.glyph.bitmap_top

def canvas(parts, pad=40):
    L = min(l for a, l, t in parts) - pad; R = max(l + a.shape[1] for a, l, t in parts) + pad
    T = max(t for a, l, t in parts) + pad; B = min(t - a.shape[0] for a, l, t in parts) - pad
    out = []
    for a, l, t in parts:
        c = np.zeros((T - B, R - L), bool); c[T - t:T - t + a.shape[0], l - L:l - L + a.shape[1]] = a; out.append(c)
    return out, L, T

def measure(F, acc, kind):
    base = base_of(acc)
    if not (F.has(acc) and F.has(base)): return None
    (cb, ca), L, T = canvas([F.raster(base), F.raster(acc)])
    ys = np.nonzero(cb.any(1))[0]; btop_r, bbot_r = ys.min(), ys.max()
    m = ca & ~ndi.binary_dilation(cb, iterations=2)
    rows = np.arange(m.shape[0])[:, None]
    m &= (rows < btop_r - 1) if kind == 'above' else (rows > bbot_r + 1)
    if m.sum() < 20: return None
    my, mx = np.nonzero(m)
    Y = lambda r: T - r
    X = lambda c: c + L
    mcx = (X(mx.min()) + X(mx.max())) / 2; mcy = (Y(my.min()) + Y(my.max())) / 2
    w = (mx.max() - mx.min() + 1); h = (my.max() - my.min() + 1)
    edge = (m & ~ndi.binary_erosion(m)).sum(); wt = 2.0 * m.sum() / max(edge, 1)
    gap = (Y(my.max()) - Y(btop_r)) if kind == 'above' else (Y(bbot_r) - Y(my.min()))   # mark BOTTOM over base top; below: base bottom over mark top (negative = attached)
    by, bx = np.nonzero(cb)
    bcx = (X(bx.min()) + X(bx.max())) / 2; bcy = (Y(by.min()) + Y(by.max())) / 2
    box = mcx - (bcx + F.k * (mcy - bcy))
    half = Y(by) >= (Y(by.min()) + Y(by.max())) / 2
    tcx = X(bx[half]).mean(); tcy = Y(by[half]).mean()
    top = mcx - (tcx + F.k * (mcy - tcy))
    stem = None
    if base in STEMS:
        r = int(T - 0.5 * F.xh); xs = np.nonzero(cb[r])[0]
        if xs.size:
            scx = X((xs.min() + xs.max()) / 2); stem = mcx - (scx + F.k * (mcy - 0.5 * F.xh))
    xh = F.xh
    return dict(w=w / xh, h=h / xh, wt=wt / F.stem, gap=gap / xh, box=box / xh, top=top / xh,
                stem=None if stem is None else stem / xh, base=base)

def main():
    args = sys.argv[1:]; which = 'lc'
    if args and args[0] == '--bases': which = args[1]; args = args[2:]
    fonts = [Font(a) for a in args]
    cols = ['w', 'h', 'wt', 'gap', 'box', 'top']
    for mk, (lc, uc, kind) in MARKS.items():
        chars = lc if which == 'lc' else uc
        print(f"\n{mk:10s} ({kind}, {'lowercase' if which == 'lc' else 'capitals'} {chars})")
        print(f"  {'font':34s}" + ''.join(f"{c:>8s}" for c in cols) + f"{'stem':>8s}   per letter: box")
        for F in fonts:
            rs = [(a, measure(F, a, kind)) for a in chars]
            rs = [(a, r) for a, r in rs if r]
            if not rs: print(f"  {F.name:34s}  n/a"); continue
            med = {c: statistics.median(r[c] for _, r in rs) for c in cols}
            st = [r['stem'] for _, r in rs if r['stem'] is not None]
            per = ' '.join(f"{a}{r['box']:+.3f}" for a, r in rs)
            print(f"  {F.name:34s}" + ''.join(f"{med[c]:8.3f}" for c in cols)
                  + (f"{statistics.median(st):8.3f}" if st else f"{'':>8s}") + f"   {per}")

if __name__ == '__main__':
    main()
