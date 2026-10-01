"""acc_center_it.py -- where an ITALIC accent sits over its letter, measured the way the eye reads it,
in any font. Round 452 (2026-09-30), owner: "italic marks are not centered".

    venv/bin/python instruments/acc_center_it.py [--caps] FONT ...

acc_offset.py (round 440) carried the base's WHOLE-ink centroid along the font's DECLARED slant,
and two things make that unfit to compare fonts: Coelacanth declares 0 degrees, Flanker 12 and
Berkeley 7, none of them its letters' slant; and an italic letter's middle is not what a mark sits
over -- the eye sets a mark over the letter's TOP. So here:
  * the slant is MEASURED, from the l's left edge between 0.2 and 0.8 of its height (least squares);
  * the letter's axis is the ink centroid of its TOP band (0.55 x-height to its top), carried
    along the measured slant from that band's own centroid height to the mark's;
  * the mark's position is its ink centroid (the mark = accented raster minus base raster).
Each figure is (mark centroid - axis) / x-height, + = right. Also printed: each mark's own lean,
the angle of its principal axis from the vertical (an acute steep or flat).
"""
import sys, math, statistics, freetype, numpy as np
from scipy import ndimage as ndi
from fontTools.ttLib import TTFont
import unicodedata

LETTERS_UC = {
    'acute': 'ÁÉÍÓÚÝ', 'grave': 'ÀÈÌÒÙ', 'circumflex': 'ÂÊÎÔÛ', 'dieresis': 'ÄËÏÖÜ',
    'tilde': 'ÃÑÕ', 'caron': 'ČŠŽĚŘ', 'macron': 'ĀĒĪŌŪ', 'breve': 'ĂĞŬ', 'ring': 'ÅŮ',
    'dot': 'ĊĖŻİ', 'dblacute': 'ŐŰ',
}
LETTERS = {
    'acute': 'áéíóúý', 'grave': 'àèìòù',
    'circumflex': 'âêîôû', 'dieresis': 'äëïöü',
    'tilde': 'ãñõ', 'caron': 'čšžěř', 'macron': 'āēīōū',
    'breve': 'ăğŭ', 'ring': 'åů', 'dot': 'ċėż', 'dblacute': 'őű',
}

def raster(f, ch):
    f.load_char(ch, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING)
    b = f.glyph.bitmap
    a = np.array(b.buffer, np.uint8).reshape(b.rows, b.pitch)[:, :b.width] >= 128
    return a, f.glyph.bitmap_left, f.glyph.bitmap_top

def place(parts, pad=40):
    L = min(l for a, l, t in parts) - pad; R = max(l + a.shape[1] for a, l, t in parts) + pad
    T = max(t for a, l, t in parts) + pad; B = min(t - a.shape[0] for a, l, t in parts) - pad
    out = []
    for a, l, t in parts:
        c = np.zeros((T - B, R - L), bool); c[T - t:T - t + a.shape[0], l - L:l - L + a.shape[1]] = a; out.append(c)
    return out, L, T

def measured_slant(f, xh):
    a, l, t = raster(f, 'l'); ys = np.nonzero(a.any(1))[0]; top, bot = ys.min(), ys.max(); h = bot - top
    pts = []
    for r in range(int(top + 0.2 * h), int(top + 0.8 * h)):
        xs = np.nonzero(a[r])[0]
        if xs.size: pts.append((t - r, l + xs.min()))
    Y = np.array([p[0] for p in pts], float); X = np.array([p[1] for p in pts], float)
    k = np.polyfit(Y, X, 1)[0]          # dx per dy
    return k

def main():
    # --caps: the capitals, with the top band at 0.55 of each letter's OWN height (cap height)
    # instead of 0.55 x-height -- round 452's capital figures come from this mode
    caps = '--caps' in sys.argv[1:]
    table = LETTERS_UC if caps else LETTERS
    for p in [a for a in sys.argv[1:] if not a.startswith('--')]:
        f = freetype.Face(p); upm = f.units_per_EM; f.set_pixel_sizes(0, upm)
        name = p.split('/')[-1]
        try:
            sx = TTFont(p)['OS/2'].sxHeight if name.startswith('Albo') else 0
        except Exception: sx = 0
        if sx: xh = float(sx)
        else:
            f.load_char('x', freetype.FT_LOAD_NO_HINTING); xh = f.glyph.metrics.horiBearingY / 64
        k = measured_slant(f, xh)
        rows = []
        allv = []
        for mk, chars in table.items():
            vals, leans = [], []
            for acc in chars:
                try:
                    b = unicodedata.normalize('NFD', acc)[0]
                    b = 'ı' if (b == 'i' and not caps) else b
                    (cb, ca), L, T = place([raster(f, b), raster(f, acc)])
                except Exception: continue
                ys, xs = np.nonzero(cb); btop = ys.min()
                m = ca & ~ndi.binary_dilation(cb, iterations=2); m[btop - 1:, :] = False
                if m.sum() < 20: continue
                my, mx = np.nonzero(m)
                mcx = (mx + L).mean(); mcy = (T - my).mean()
                Yb = T - ys; Xb = xs + L
                band = Yb >= 0.55 * (Yb.max() if caps else xh)
                tcx = Xb[band].mean(); tcy = Yb[band].mean()
                axis = tcx + k * (mcy - tcy)
                vals.append((acc, (mcx - axis) / xh))
                # the mark's lean: principal axis of its pixels, degrees from vertical
                cov = np.cov(np.stack([(mx + L).astype(float), (T - my).astype(float)]))
                w, v = np.linalg.eigh(cov); vx, vy = v[:, 1]
                leans.append(math.degrees(math.atan2(abs(vx), abs(vy))) * (1 if vx * vy > 0 else -1))
            if vals:
                med = statistics.median(v for _, v in vals)
                allv += [v for _, v in vals]
                rows.append(f"{mk[:5]} {med:+.3f}" + (f" lean {statistics.median(leans):+.0f}" if mk in ('acute', 'grave', 'circumflex', 'caron') else ""))
                if caps or mk in ('acute', 'dieresis', 'circumflex'):
                    rows[-1] += " [" + " ".join(f"{a}{v:+.2f}" for a, v in vals) + "]"
        print(f"{name:34s} slant {math.degrees(math.atan(k)):4.1f}  mean {statistics.mean(allv):+.3f}\n    " + "\n    ".join(rows))

if __name__ == '__main__':
    main()
