"""stem_axis_marks.py -- where an italic mark sits against its letter's STEMS, continued up on their
own axis. Round 453 (2026-09-30), owner: *"the macron or other marks are likely not centered
properly for italic. imagine stems continuing up on their axis and center optically based off
of that"*.

    venv/bin/python instruments/stem_axis_marks.py FONT ...          # per mark, per letter
    venv/bin/python instruments/stem_axis_marks.py --letters FONT ... # per base letter (symmetric marks)
    venv/bin/python instruments/stem_axis_marks.py --write            # regenerate outlines/glyphs/mark_axis_it.py

THE AXIS (`axis_line`). The base letter is rasterized at 1000 px per em. Over 0.15-0.85 of its
height every row's ink runs are found, the DOMINANT run count (the mode over the rows) is taken,
and only rows with that count are used -- a row where a serif, a join or a bar splits or merges
a stem would otherwise pull its line over. One run: the stem's centre line, fitted (x on y, least
squares). Two or more: a line through the leftmost run's centres and one through the
rightmost's; the axis is their average. Each line is a stem continued up on ITS OWN slope.
Letters with no stems (c C s S z Z G E F) take the box centre at mid-height, carried along the
font's own stem slope (its dotless i's).

THE OPTICAL OFFSET. Measured against that axis, the italic references agree letter by letter --
the a's marks sit a little left of it (-0.03), the e's right (+0.08, its terminal), the R's left
(-0.14, its leg) -- and those medians ARE the optical correction a stem cannot give. `--write`
stores them (B: per base letter, over the symmetric marks; M: the acute's, grave's and double
acute's own lean, net of B) for build.py to add to the axis.

Each figure: (mark ink centroid - axis at the centroid's height) / x-height, + = right.

A NEGATIVE RESULT kept for the record: an axis through the midpoints of the letter's OUTER EDGES
(`axis_edges`, `--edges`) puts the references' symmetric marks near 0 on a o u i n and their
capitals, but reads the e's terminal, the E's arms and the c's opening as body and biases those
letters by 0.2-0.4 in every font -- worse than the stem axis it was meant to improve on.
"""
import os, sys, math, statistics, freetype, numpy as np, unicodedata
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__)); WS = os.path.dirname(HERE)
SUP = '/System/Library/Fonts/Supplemental/'
REFS = [os.path.join(WS, 'refs', 'texgyrepagella-italic.otf'), os.path.join(WS, 'refs', 'coelacanth-italic.otf'),
        SUP + 'Georgia Italic.ttf', SUP + 'Times New Roman Italic.ttf', os.path.join(WS, 'refs', 'flanker-griffo-italic.otf')]
MARKS = {
    'acute': 'áéíóúýÁÉÍÓÚÝ', 'grave': 'àèìòùÀÈÌÒÙ', 'circumflex': 'âêîôûÂÊÎÔÛ',
    'dieresis': 'äëïöüÄËÏÖÜ', 'tilde': 'ãñõÃÑÕ', 'caron': 'čšžěřČŠŽĚŘ', 'macron': 'āēīōūĀĒĪŌŪ',
    'breve': 'ăğŭĂĞŬ', 'ring': 'åůÅŮ', 'dot': 'ċėżĊĖŻ', 'dblacute': 'őűŐŰ',
}
SYM = ['circumflex', 'dieresis', 'macron', 'tilde', 'breve', 'ring', 'dot', 'caron']
LEAN = ['acute', 'grave', 'dblacute']
BOX = set('cCsSzZGEF')
EDGES = False
V3 = True             # the round-453 axis family; --stems restores the first, line-per-side axis
V4 = True             # the top-band centre (axis_v4); --body uses the whole body's (axis_v3)
V5 = True             # stems by their arrival under the mark, the stemless by their body (axis_v5)


def raster(f, ch):
    f.load_char(ch, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING)
    b = f.glyph.bitmap
    return np.array(b.buffer, np.uint8).reshape(b.rows, b.pitch)[:, :b.width] >= 128, f.glyph.bitmap_left, f.glyph.bitmap_top


def place(parts, pad=60):
    L = min(l for a, l, t in parts) - pad; R = max(l + a.shape[1] for a, l, t in parts) + pad
    T = max(t for a, l, t in parts) + pad; B = min(t - a.shape[0] for a, l, t in parts) - pad
    out = []
    for a, l, t in parts:
        c = np.zeros((T - B, R - L), bool); c[T - t:T - t + a.shape[0], l - L:l - L + a.shape[1]] = a; out.append(c)
    return out


def place2(parts, pad=60):
    """place(), also returning the baseline's row."""
    L = min(l for a, l, t in parts) - pad; R = max(l + a.shape[1] for a, l, t in parts) + pad
    T = max(t for a, l, t in parts) + pad; B = min(t - a.shape[0] for a, l, t in parts) - pad
    out = []
    for a, l, t in parts:
        c = np.zeros((T - B, R - L), bool); c[T - t:T - t + a.shape[0], l - L:l - L + a.shape[1]] = a; out.append(c)
    return out, T


def _rows(mb, lo, hi):
    ys = np.nonzero(mb.any(1))[0]; top, bot = ys.min(), ys.max(); h = bot - top
    out = []
    for r in range(int(bot - hi * h), int(bot - lo * h)):
        xs = np.nonzero(mb[r])[0]
        if xs.size == 0: continue
        runs = np.split(xs, np.nonzero(np.diff(xs) > 1)[0] + 1)
        out.append((r, [(rr[0], rr[-1]) for rr in runs]))
    return out, top, bot


def _fit(pts):
    y = np.array([p[0] for p in pts], float); x = np.array([p[1] for p in pts], float)
    return np.polyfit(y, x, 1)


def axis_line(mb, base_ch, kfont=None):
    """(k, c, ndom): axis x = k * row + c, raster coordinates (rows run down)."""
    rows, top, bot = _rows(mb, 0.15, 0.85)
    counts = [len(rs) for _, rs in rows]
    ndom = max(set(counts), key=counts.count)
    use = [(r, rs) for r, rs in rows if len(rs) == ndom]
    kl, cl = _fit([(r, (rs[0][0] + rs[0][1]) / 2) for r, rs in use])
    if ndom == 1:
        k, c = kl, cl
    else:
        kr, cr = _fit([(r, (rs[-1][0] + rs[-1][1]) / 2) for r, rs in use])
        k, c = (kl + kr) / 2, (cl + cr) / 2
    if base_ch in BOX:
        k = kfont if kfont is not None else k
        xs = np.nonzero(mb.any(0))[0]; c = (xs.min() + xs.max()) / 2 - k * (top + bot) / 2
    return k, c, ndom


def axis_edges(mb, base_ch, kfont=None, lo=0.25, hi=0.75):
    rows, top, bot = _rows(mb, lo, hi)
    k, c = _fit([(r, (rs[0][0] + rs[-1][1]) / 2) for r, rs in rows])
    return k, c, 0


def _fitres(pts):
    y = np.array([p[0] for p in pts], float); x = np.array([p[1] for p in pts], float)
    k, c = np.polyfit(y, x, 1); return k, c, float(np.sqrt(np.mean((x - (k * y + c)) ** 2)))


def axis_v3(mb, base_ch, kfont, base_row, href):
    """(k, c): THE AXIS (round 453, after the owner's "your axis calculation is off for many
    letters"). The slope is the letter's own STRAIGHT stem(s) -- a side whose run centres fit a line
    within 1.5% of the x-height and lean within 14 degrees of the font's stems -- else the font's
    stem slope (a curve's fitted line is its average lean, not the letter's slant: the o's sides
    read 7 degrees, the e's 0). The centre is the middle of the UNSLANTED body over 0.15-0.85 of the
    x-height (cap height for a capital) above the baseline; the axis is that centre up the slope."""
    rlo, rhi = int(base_row - 0.85 * href), int(base_row - 0.15 * href)
    rows = []
    for r in range(rlo, rhi):
        xs = np.nonzero(mb[r])[0]
        if xs.size == 0: continue
        runs = np.split(xs, np.nonzero(np.diff(xs) > 1)[0] + 1)
        rows.append((r, xs, [(rr[0], rr[-1]) for rr in runs]))
    counts = [len(rs) for _, _, rs in rows]; nd = max(set(counts), key=counts.count)
    use = [(r, rs) for r, _, rs in rows if len(rs) == nd]
    ks = []
    for side in ((0,) if nd == 1 else (0, -1)):
        k, c, res = _fitres([(r, (rs[side][0] + rs[side][1]) / 2) for r, rs in use])
        if res < 0.015 * href and abs(k - kfont) < 0.25: ks.append(k)
    k = sum(ks) / len(ks) if ks else kfont
    ymid = base_row - 0.5 * href
    lo = min((xs - k * (r - ymid)).min() for r, xs, _ in rows); hi = max((xs - k * (r - ymid)).max() for r, xs, _ in rows)
    return k, (lo + hi) / 2 - k * ymid, len(ks)


def axis_v4(mb, base_ch, kfont, base_row, href, t0=0.15, t1=0.45):
    """(k, c): the slope as axis_v3 (the letter's straight stems, else the font's); the centre is the
    middle of the UNSLANTED ink in the letter's TOP band -- t0..t1 of the x-height (cap height)
    below the letter's own top, skipping the serif tips above it -- because a mark sits over where
    the stems ARRIVE: the L's and the h's stem, the A's apex, between the n's stem tops."""
    k, _, nst = axis_v3(mb, base_ch, kfont, base_row, href)
    top = np.nonzero(mb.any(1))[0].min()
    ymid = base_row - 0.5 * href; lo, hi = [], []
    for r in range(int(top + t0 * href), int(top + t1 * href)):
        xs = np.nonzero(mb[r])[0]
        if xs.size == 0: continue
        u = xs - k * (r - ymid); lo.append(u.min()); hi.append(u.max())
    return k, (min(lo) + max(hi)) / 2 - k * ymid, nst


def axis_v5(mb, base_ch, kfont, base_row, href):
    """(k, c): THE AXIS (round 453, third pass). Slope: the font's stem slope.
    Centre: for a STEM letter, the unslanted ink between 0.25 and 0.55 of the x-height (cap height)
    below its own top -- where its stems arrive under the mark, under the entry serifs of i u n and
    the r's arm; for a letter with NO stems (c C s S z Z G E F), the unslanted whole body
    (axis_v3), because a top band sees only the c's back or the E's top arm."""
    # THE SLOPE IS THE FONT'S (the dotless i's; the I's for a capital), for every letter: a
    # per-letter "straight stem" test tipped differently in the build and here on the Bold
    # Italic's calligraphic stems (the n's sides read 7.8 and 2.9 degrees, the a's 18, all near
    # the threshold), and the two disagreed by 0.15 of the x-height on the same letter
    if base_ch in BOX:
        rows, top, bot = _rows(mb, 0.0, 1.0)
        ymid = base_row - 0.5 * href; lo, hi = [], []
        for r in range(int(base_row - 0.85 * href), int(base_row - 0.15 * href)):
            xs = np.nonzero(mb[r])[0]
            if xs.size: u = xs - kfont * (r - ymid); lo.append(u.min()); hi.append(u.max())
        return kfont, (min(lo) + max(hi)) / 2 - kfont * ymid, 0
    top = np.nonzero(mb.any(1))[0].min()
    ymid = base_row - 0.5 * href; lo, hi = [], []
    for r in range(int(top + 0.25 * href), int(top + 0.55 * href)):
        xs = np.nonzero(mb[r])[0]
        if xs.size: u = xs - kfont * (r - ymid); lo.append(u.min()); hi.append(u.max())
    return kfont, (min(lo) + max(hi)) / 2 - kfont * ymid, 0


def font_slope(f):
    a, l, t = raster(f, 'ı')
    k, c, _ = axis_line(np.pad(a, 60), 'ı')
    return k


def font_slopes(f):
    """(lowercase, capital) stem slopes: the dotless i's and the I's centre lines."""
    out = []
    for ch in ('ı', 'I'):
        a, l, t = raster(f, ch); mb = np.pad(a, 60)
        rows, top, bot = _rows(mb, 0.15, 0.85)
        out.append(_fit([(r, (rs[0][0] + rs[0][1]) / 2) for r, rs in rows if len(rs) == 1])[0])
    return out


def measure(path):
    f = freetype.Face(path); f.set_pixel_sizes(0, 1000)
    f.load_char('x', freetype.FT_LOAD_NO_HINTING); xh = f.glyph.metrics.horiBearingY / 64
    f.load_char('H', freetype.FT_LOAD_NO_HINTING); caph = f.glyph.metrics.horiBearingY / 64
    kfont = font_slope(f); klc, kuc = font_slopes(f)
    res = {}
    for mk, chars in MARKS.items():
        for ch in chars:
            b = unicodedata.normalize('NFD', ch)[0]; b = 'ı' if b == 'i' else b
            try:
                (ca, cb), T = place2([raster(f, ch), raster(f, b)])
            except Exception:
                continue
            if V3:
                k, c, nd = (axis_v5 if V5 else (axis_v4 if V4 else axis_v3))(cb, b, kuc if b.isupper() else klc, T, caph if b.isupper() else xh)
            else:
                k, c, nd = (axis_edges if EDGES else axis_line)(cb, b, kfont)
            ys = np.nonzero(cb.any(1))[0]
            m = ca & ~ndi.binary_dilation(cb, iterations=2); m[ys.min() - 1:, :] = False
            if m.sum() < 30: continue
            my, mx = np.nonzero(m); mcx, mcy = mx.mean(), my.mean()
            res.setdefault(mk, []).append((ch, (mcx - (k * mcy + c)) / xh))
    return res


def per_base(res):
    d = {}
    for mk in SYM:
        for ch, v in res.get(mk, []):
            d.setdefault(unicodedata.normalize('NFD', ch)[0], []).append(v)
    return {b: statistics.median(vs) for b, vs in d.items()}


def tables():
    """B[letter]: the references' median symmetric-mark offset; M[mark]: the lean marks' own offset net of B."""
    per_font = [measure(p) for p in REFS]
    bf = [per_base(r) for r in per_font]
    letters = sorted(set().union(*[set(b) for b in bf]))
    B = {}
    for L in letters:
        if L in 'sSzZ' and not V3: continue   # (the first axis had no usable line for these)
        vs = [b[L] for b in bf if L in b]
        if len(vs) >= 3: B[L] = round(float(statistics.median(vs)), 3)
    M = {}
    for mk in LEAN:
        for case in ('lc', 'uc'):
            nets = []
            for r, b in zip(per_font, bf):
                for ch, v in r.get(mk, []):
                    if (ch.islower()) != (case == 'lc'): continue
                    base = unicodedata.normalize('NFD', ch)[0]
                    if base in b: nets.append(v - b[base])
            if nets: M[f"{mk}.{case}"] = round(float(statistics.median(nets)), 3)
    return B, M


def write():
    B, M = tables()
    out = os.path.join(WS, 'outlines', 'glyphs', 'mark_axis_it.py')
    lines = ['"""GENERATED by instruments/stem_axis_marks.py --write -- do not edit by hand.', '',
             "Round 453 (2026-09-30). The italic references' optical offsets against the stem axis",
             '(each letter\'s stems continued up on their own slope), in x-heights, + = right:',
             'B per base letter (median over the symmetric marks, then over the fonts); M the acute\'s,',
             'grave\'s and double acute\'s own lean, net of B, by case. References: ' +
             ', '.join(os.path.basename(p) for p in REFS) + '.', '"""', '',
             f'B = {B!r}', '', f'M = {M!r}', '']
    open(out, 'w').write('\n'.join(lines)); print('wrote', out); print('B', B); print('M', M)


def main():
    global EDGES
    args = sys.argv[1:]
    if '--write' in args:
        write(); return
    letters = '--letters' in args
    global V3
    if '--edges' in args: EDGES = True; V3 = False
    if '--stems' in args: V3 = False
    global V4
    if '--body' in args: V4 = False
    for p in [a for a in args if not a.startswith('--')]:
        r = measure(p); print(os.path.basename(p))
        if letters:
            for b, v in sorted(per_base(r).items(), key=lambda t: (t[0].isupper(), t[0])):
                print(f'  {b} {v:+.3f}')
            continue
        for mk, vals in r.items():
            lc = [v for ch, v in vals if ch.islower()]; uc = [v for ch, v in vals if ch.isupper()]
            print(f"  {mk:10s} lc {statistics.median(lc) if lc else float('nan'):+.3f}  uc {statistics.median(uc) if uc else float('nan'):+.3f}   "
                  + " ".join(f"{ch}{v:+.2f}" for ch, v in vals))


if __name__ == '__main__':
    main()
