"""angled_box.py -- each italic mark against an ANGLED BOX built from its letter's stems and the
font's axis. Round 454 (2026-10-01), owner: *"italic needs more centering, especially E and A.
make a angled box using stems and axis for reference during placement"*.

    venv/bin/python instruments/angled_box.py FONT ...                 # per base letter, symmetric marks
    venv/bin/python instruments/angled_box.py --sheet OUT.png "ĒĀÉÁ..." [LABEL::]FONT ...

THE BOX. Sides parallel to the font's own stem axis (the centre line of its I for a capital, of
its dotless i for a lowercase, fitted over 0.15-0.85 of the height); the left side touches the
leftmost ink and the right side the rightmost ink of the letter's STEM BAND, 0.15-0.85 of the
cap height (x-height) above the baseline -- the stems, bowls and diagonals, not the serif tips
and arms at the very top and bottom that reach past them. The box's centre line is where a mark
is centred: each figure is (mark ink centroid - centre line at the centroid's height) / x-height,
+ = right. `--band LO,HI` moves the band; `--full` takes all the ink.
"""
import os, sys, statistics, unicodedata, freetype, numpy as np
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__)); WS = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from stem_axis_marks import raster, place2, font_slopes, MARKS, SYM, LEAN, REFS  # noqa: E402

BAND = (0.15, 0.85)


def box(mb, k, base_row, href, band=None):
    """(umin, umax, rowmid): the angled box over the band, u = x - k * (row - rowmid), rows down."""
    lo, hi = band or BAND
    rowmid = base_row - 0.5 * href
    us_lo, us_hi = [], []
    for r in range(int(base_row - hi * href), int(base_row - lo * href) + 1):
        xs = np.nonzero(mb[r])[0]
        if xs.size: u = xs - k * (r - rowmid); us_lo.append(u.min()); us_hi.append(u.max())
    return min(us_lo), max(us_hi), rowmid


def face(path):
    f = freetype.Face(path); f.set_pixel_sizes(0, 1000)
    f.load_char('x', freetype.FT_LOAD_NO_HINTING); xh = f.glyph.metrics.horiBearingY / 64
    f.load_char('H', freetype.FT_LOAD_NO_HINTING); caph = f.glyph.metrics.horiBearingY / 64
    klc, kuc = font_slopes(f)
    return f, xh, caph, klc, kuc


def one(F, ch, band=None):
    """(offset / xh, parts for drawing) for accented `ch`, or None."""
    f, xh, caph, klc, kuc = F
    b = unicodedata.normalize('NFD', ch)[0]; b = 'ı' if b == 'i' else ('ȷ' if b == 'j' else b)
    try:
        (ca, cb), T = place2([raster(f, ch), raster(f, b)])
    except Exception:
        return None
    cap = b.isupper(); k = kuc if cap else klc; href = caph if cap else xh
    umin, umax, rowmid = box(cb, k, T, href, band)
    ys = np.nonzero(cb.any(1))[0]
    m = ca & ~ndi.binary_dilation(cb, iterations=2); m[ys.min() - 1:, :] = False
    if m.sum() < 30: return None
    my, mx = np.nonzero(m); mcx, mcy = mx.mean(), my.mean()
    centre = k * (mcy - rowmid) + (umin + umax) / 2
    return (mcx - centre) / xh, dict(ca=ca, cb=cb, m=m, k=k, umin=umin, umax=umax, rowmid=rowmid, T=T, href=href, mc=(mcx, mcy))


def measure(path, band=None):
    F = face(path); res = {}
    for mk, chars in MARKS.items():
        for ch in chars:
            r = one(F, ch, band)
            if r is not None: res.setdefault(mk, []).append((ch, r[0]))
    return res


def per_base(res):
    d = {}
    for mk in SYM:
        for ch, v in res.get(mk, []):
            d.setdefault(unicodedata.normalize('NFD', ch)[0], []).append(v)
    return {b: statistics.median(vs) for b, vs in d.items()}


def sheet(out, chars, specs, band=None):
    from PIL import Image, ImageDraw, ImageFont
    lab = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 18)
    SC = 0.30; rows = []
    for spec in specs:
        label, path = spec.split("::", 1) if "::" in spec else (os.path.basename(path), spec)
        F = face(path); cells = []
        for ch in chars:
            r = one(F, ch, band)
            if r is None: continue
            v, p = r
            ca, cb, m = p['ca'], p['cb'], p['m']
            H, W = ca.shape
            img = np.full((H, W, 3), 250, np.uint8)
            img[cb] = (40, 40, 40); img[m] = (200, 40, 30)
            im = Image.fromarray(img); d = ImageDraw.Draw(im)
            k, rowmid = p['k'], p['rowmid']
            def X(u, row): return k * (row - rowmid) + u
            r0, r1 = p['T'] - p['href'] * 1.55, p['T'] + 10
            blo, bhi = (band or BAND)
            # the box over the band, and its sides and centre line carried up past the mark
            rb0, rb1 = p['T'] - bhi * p['href'], p['T'] - blo * p['href']
            for u in (p['umin'], p['umax']):
                d.line([(X(u, r0), r0), (X(u, r1), r1)], fill=(120, 160, 230), width=3)
            d.polygon([(X(p['umin'], rb0), rb0), (X(p['umax'], rb0), rb0), (X(p['umax'], rb1), rb1), (X(p['umin'], rb1), rb1)], outline=(30, 90, 220))
            uc = (p['umin'] + p['umax']) / 2
            d.line([(X(uc, r0), r0), (X(uc, r1), r1)], fill=(30, 160, 60), width=4)
            mcx, mcy = p['mc']; d.ellipse([mcx - 12, mcy - 12, mcx + 12, mcy + 12], outline=(255, 200, 0), width=5)
            im = im.resize((max(1, int(W * SC)), max(1, int(H * SC))), Image.LANCZOS)
            c = Image.new("RGB", (im.width, im.height + 26), (250, 250, 250)); c.paste(im, (0, 26))
            ImageDraw.Draw(c).text((4, 2), f"{ch} {v:+.3f}", fill=(30, 30, 30), font=lab)
            cells.append(c)
        h = max(c.height for c in cells)
        strip = Image.new("RGB", (sum(c.width for c in cells) + 120, h), (250, 250, 250))
        ImageDraw.Draw(strip).text((6, h // 2), label, fill=(30, 30, 30), font=lab)
        x = 120
        for c in cells: strip.paste(c, (x, h - c.height)); x += c.width
        rows.append(strip)
    o = Image.new("RGB", (max(r.width for r in rows), sum(r.height for r in rows)), (250, 250, 250)); y = 0
    for r in rows: o.paste(r, (0, y)); y += r.height
    o.save(out); print(out, o.size)


def main():
    global BAND
    args = sys.argv[1:]; band = None
    if '--band' in args:
        i = args.index('--band'); BAND = tuple(float(v) for v in args[i + 1].split(',')); del args[i:i + 2]
    if '--full' in args:
        args.remove('--full'); BAND = (-0.05, 1.6)
    if '--sheet' in args:
        i = args.index('--sheet'); out, chars = args[i + 1], args[i + 2]; del args[i:i + 3]
        return sheet(out, chars, args)
    if '--refs' in args:
        args.remove('--refs'); args += REFS
    tabs = []
    for p in args:
        pb = per_base(measure(p)); tabs.append((os.path.basename(p), pb))
    letters = sorted(set().union(*[set(t) for _, t in tabs]), key=lambda c: (c.isupper(), c))
    print("letter " + " ".join(f"{n[:12]:>12s}" for n, _ in tabs))
    for L in letters:
        print(f"  {L}    " + " ".join(f"{t[L]:+12.3f}" if L in t else f"{'':>12s}" for _, t in tabs))


if __name__ == '__main__':
    main()
