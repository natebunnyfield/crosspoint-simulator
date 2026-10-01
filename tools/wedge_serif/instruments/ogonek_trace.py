"""ogonek_trace.py -- TRACE the reference ogoneks: centerline and width, root to tip, in x-heights
and stems. Round 452 (2026-09-30), owner: *"ogonek needs to be traced and redone entirely"*.

    venv/bin/python instruments/ogonek_trace.py            # print the traces and the tables
    venv/bin/python instruments/ogonek_trace.py --write    # also regenerate outlines/glyphs/ogonek_traced.py
    venv/bin/python instruments/ogonek_trace.py --diag OUT.png   # each trace drawn over its reference

Not a bezier copy: what comes out is the STROKE -- where the pen's center went and how wide it was
there -- which Albo's own `stroke()` then draws (the method of trace_g.py, round 2026-09-17).

METHOD, per reference font:
  * rasterize the a-ogonek and the a at XHPX px x-height, unhinted; unshear an italic by its
    MEASURED slant (refs_registry.measure_slant -- Georgia Italic 13.0, Times Italic 16.1,
    Pagella Bold Italic 12.5; never post.italicAngle);
  * the ogonek is the a-ogonek's ink minus the a's (dilated 2 px), below 0.10 x-height, largest piece;
  * centerline: Zhang-Suen thinning, the longest geodesic path, smoothed; ROOT = the end nearer the
    baseline. The skeleton forks where the ogonek meets the a, so the samples within one half-width
    of the a's ink are dropped and the path is re-extended along its own tangent to the baseline:
    every trace starts at y = 0, where the visible mark leaves the letter;
  * width: through the body, the INSCRIBED CIRCLE's diameter (2 x the distance transform on
    the skeleton, which is the circles' centers); past the skeleton's natural end, where that
    falls to zero at any end, blunt or pointed, the CHORD across the normal (never more than
    the width where the skeleton ended); in the root zone, where the circle is cut by the
    junction with the a, the first clear width is held back to the root;
  * fitted, not interpolated: least-squares cubic splines through x(s), y(s) and w(s);
  * units: x and y in x-heights from the root, y up; width in the font's own lowercase stem
    (the l, mid-height), so the mark keeps its letter's colour at Albo's lighter stem.

Fonts: the roman from Pagella / Georgia / Times (Regular and Bold), the italic from Pagella /
Georgia / Times Italic (and Bold Italic). Flanker's ogonek is a different construction (a ball
terminal hung from the bowl) and Coelacanth's runs 0.63 x-height deep, so both are traced and
printed but kept out of the tables. TABLES: 'pagella' (Pagella alone; GUST Font License, which
permits a derivative under another name) and 'mean' (the three fonts averaged at equal arc length).
"""
import sys, os, math, json, argparse
import numpy as np, freetype
from scipy import ndimage as ndi
from collections import deque

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
XHPX = 600
N = 49
F = os.path.expanduser('~/Library/Fonts/'); SUP = '/System/Library/Fonts/Supplemental/'; REF = os.path.join(ROOT, 'refs') + '/'

FONTS = {   # key -> (label, path, measured slant)
    'pag_r': ('Pagella', F + 'texgyrepagella-regular.otf', 0.0),
    'geo_r': ('Georgia', SUP + 'Georgia.ttf', 0.0),
    'tim_r': ('Times', SUP + 'Times New Roman.ttf', 0.0),
    'pag_b': ('Pagella B', F + 'texgyrepagella-bold.otf', 0.0),
    'geo_b': ('Georgia B', SUP + 'Georgia Bold.ttf', 0.0),
    'tim_b': ('Times B', SUP + 'Times New Roman Bold.ttf', 0.0),
    'pag_i': ('Pagella I', REF + 'texgyrepagella-italic.otf', 11.7),
    'geo_i': ('Georgia I', SUP + 'Georgia Italic.ttf', 13.0),
    'tim_i': ('Times I', SUP + 'Times New Roman Italic.ttf', 16.1),
    'pag_z': ('Pagella Z', F + 'texgyrepagella-bolditalic.otf', 12.5),
    'geo_z': ('Georgia Z', SUP + 'Georgia Bold Italic.ttf', 13.0),
    'tim_z': ('Times Z', SUP + 'Times New Roman Bold Italic.ttf', 16.1),
    'coe_i': ('Coelacanth', REF + 'coelacanth-italic.otf', 14.5),
}
TABLES = {
    'pagella': {'R400': ['pag_r'], 'R700': ['pag_b'], 'I400': ['pag_i'], 'I700': ['pag_z']},
    'mean': {'R400': ['pag_r', 'geo_r', 'tim_r'], 'R700': ['pag_b', 'geo_b', 'tim_b'],
             'I400': ['pag_i', 'geo_i', 'tim_i'], 'I700': ['pag_z', 'geo_z', 'tim_z']},
}


def face(path):
    f = freetype.Face(path); f.set_pixel_sizes(0, 400)
    f.load_char('x', freetype.FT_LOAD_NO_HINTING); xh = f.glyph.metrics.height / 64
    f.set_pixel_sizes(0, int(round(400 * XHPX / xh)))
    return f


def raster(f, ch):
    f.load_char(ch, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING)
    b = f.glyph.bitmap
    return np.array(b.buffer, np.uint8).reshape(b.rows, b.pitch)[:, :b.width], f.glyph.bitmap_left, f.glyph.bitmap_top


def canvas(parts):
    L, R, T, B = -int(1.5 * XHPX), int(3.0 * XHPX), int(1.8 * XHPX), -int(1.4 * XHPX)
    out = []
    for a, l, t in parts:
        c = np.zeros((T - B, R - L), np.uint8); c[T - t:T - t + a.shape[0], l - L:l - L + a.shape[1]] = a; out.append(c)
    return out, L, T


def unshear(img, T, slant):
    if abs(slant) < 0.05: return img
    k = math.tan(math.radians(slant)); H, W = img.shape
    rows = np.arange(H)[:, None]; cols = np.arange(W)[None, :]
    return ndi.map_coordinates(img.astype(np.float32), [np.broadcast_to(rows, (H, W)), cols + k * (T - rows)], order=1, cval=0)


def zhang_suen(m):
    m = m.copy().astype(np.uint8); changed = True
    while changed:
        changed = False
        for step in (0, 1):
            P = np.pad(m, 1)
            p2, p3, p4, p5 = P[:-2, 1:-1], P[:-2, 2:], P[1:-1, 2:], P[2:, 2:]
            p6, p7, p8, p9 = P[2:, 1:-1], P[2:, :-2], P[1:-1, :-2], P[:-2, :-2]
            nb = [p2, p3, p4, p5, p6, p7, p8, p9]
            B = sum(x.astype(np.int32) for x in nb); seq = nb + [p2]
            A = sum(((seq[i] == 0) & (seq[i + 1] == 1)).astype(np.int32) for i in range(8))
            c1 = (p2 * p4 * p6) == 0 if step == 0 else (p2 * p4 * p8) == 0
            c2 = (p4 * p6 * p8) == 0 if step == 0 else (p2 * p6 * p8) == 0
            rem = (m == 1) & (B >= 2) & (B <= 6) & (A == 1) & c1 & c2
            if rem.any(): m[rem] = 0; changed = True
    return m.astype(bool)


def longest_path(sk):
    pts = set(zip(*np.nonzero(sk)))
    def nbrs(p):
        y, x = p
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if (dy or dx) and (y + dy, x + dx) in pts: yield (y + dy, x + dx)
    def bfs(s):
        prev = {s: None}; q = deque([s]); last = s
        while q:
            p = q.popleft(); last = p
            for n in nbrs(p):
                if n not in prev: prev[n] = p; q.append(n)
        return last, prev
    a, _ = bfs(next(iter(pts))); b, prev = bfs(a)
    path = []; p = b
    while p is not None: path.append(p); p = prev[p]
    return np.array(path, float)


def smooth(P, k):
    if len(P) < k: return P
    pad = k // 2
    Q = np.vstack([np.repeat(P[:1], pad, 0), P, np.repeat(P[-1:], pad, 0)]); ker = np.ones(k) / k
    return np.stack([np.convolve(Q[:, 0], ker, 'valid'), np.convolve(Q[:, 1], ker, 'valid')], 1)


def resample(P, n):
    d = np.r_[0, np.cumsum(np.hypot(*np.diff(P, axis=0).T))]; t = np.linspace(0, d[-1], n)
    return np.stack([np.interp(t, d, P[:, 0]), np.interp(t, d, P[:, 1])], 1)


def tangents(P):
    g = np.gradient(P, axis=0); return g / (np.hypot(g[:, 0], g[:, 1])[:, None] + 1e-12)


def chord(mask, other, p, nrm, lim=400):
    """distances to the mask's edge along +nrm and -nrm, and whether each side ends in OTHER ink"""
    out = []
    for s in (1, -1):
        d = 0.0; hit = False
        iy, ix = int(round(p[0])), int(round(p[1]))
        if not mask[iy, ix]: return 0.0, 0.0, True, True
        while d < lim:
            d += 0.25; y, x = p[0] + s * nrm[0] * d, p[1] + s * nrm[1] * d
            iy, ix = int(round(y)), int(round(x))
            if not mask[iy, ix]:
                hit = bool(other[iy, ix]); break
        out += [d, hit]
    return out[0], out[2], out[1], out[3]


def trace(key):
    lab, path, slant = FONTS[key]
    f = face(path)
    (ca, cb), L, T = canvas([raster(f, c) for c in ('ą', 'a')])
    ca = unshear(ca, T, slant) >= 128; cb = unshear(cb, T, slant) >= 128
    adil = ndi.binary_dilation(cb, iterations=2)
    og = ca & ~adil; og[: T - int(0.10 * XHPX), :] = False
    lb, n = ndi.label(og); sizes = ndi.sum(og, lb, range(1, n + 1)); og = lb == (1 + int(np.argmax(sizes)))
    ys_, xs_ = np.nonzero(og); y0_, x0_ = ys_.min() - 4, xs_.min() - 4
    P = longest_path(zhang_suen(og[y0_:ys_.max() + 5, x0_:xs_.max() + 5])) + np.array([y0_, x0_], float)
    if P[0, 0] > P[-1, 0]: P = P[::-1]                 # root (higher, smaller row) first
    P = smooth(P, 15)
    # drop the fork at the root: samples nearer the a's ink than a half-width
    da = ndi.distance_transform_edt(~adil); edt = ndi.distance_transform_edt(og)
    keep = 0
    while keep < len(P) - 10:
        y, x = P[keep]
        if da[int(round(y)), int(round(x))] > 1.2 * edt[int(round(y)), int(round(x))]: break
        keep += 1
    P = P[keep:]
    # the visible mark starts at the baseline: an italic's diff runs up into the exit stroke
    above = np.nonzero(P[:, 0] < T)[0]
    if above.size and above[0] == 0:
        P = P[int(np.argmax(P[:, 0] >= T)):]
    P = resample(P, 400)
    L0 = float(np.sum(np.hypot(*np.diff(P, axis=0).T)))
    # re-extend the root along its tangent up to the baseline (row T), the tip until it leaves the ink
    tn = tangents(P)
    v = -tn[0]; ext = []; cur = P[0].copy()
    while cur[0] > T and len(ext) < 4000:
        cur = cur + v * 0.5; ext.append(cur.copy())
    Lr = 0.5 * len(ext)
    if ext: P = np.vstack([np.array(ext[::-1]), P])
    v = tn[-1]; ext = []; cur = P[-1].copy()
    while len(ext) < 4000:
        nxt = cur + v * 0.5
        if not og[int(round(nxt[0])), int(round(nxt[1]))]: break
        cur = nxt; ext.append(cur.copy())
    Lt = 0.5 * len(ext)
    if ext: P = np.vstack([P, np.array(ext)])
    P = resample(P, 400); Ltot = Lr + L0 + Lt
    s_ = np.linspace(0, Ltot, len(P))
    # WIDTH. Through the body: the inscribed circle's diameter, 2 x EDT on the skeleton -- the
    # skeleton IS the inscribed circles' centers, so this is the stroke's width wherever its
    # sides are not ends. In the TIP zone (the extension past the skeleton's natural end) the
    # EDT falls to zero at any end, blunt or pointed, so the width there is the CHORD along the
    # normal, never more than the width where the skeleton ended. In the ROOT zone the stroke
    # runs into the a, so the width at the first trimmed skeleton sample is held back to the root.
    W = 2 * ndi.map_coordinates(edt, [P[:, 0], P[:, 1]], order=1)
    tn = tangents(P)
    i_r = int(np.searchsorted(s_, Lr)); i_t = int(np.searchsorted(s_, Lr + L0)) - 1
    # ...from the first sample whose inscribed circle is clear of the a: the a's ink at least
    # twice the circle's radius away (nearer than that the circle is cut by the junction)
    dP = ndi.map_coordinates(da, [P[:, 0], P[:, 1]], order=1); eP = ndi.map_coordinates(edt, [P[:, 0], P[:, 1]], order=1)
    clear = np.nonzero((dP >= 2.0 * eP) & (s_ >= 0.04 * Ltot))[0]
    i_r = min(max(i_r, int(clear[0]) if clear.size else i_r), len(P) // 3)
    W[:i_r] = W[i_r]
    for i in range(i_t + 1, len(P)):
        t = tn[i]; nrm = np.array([t[1], -t[0]]); dp, dm, hp, hm = chord(og, adil, P[i], nrm)
        W[i] = min(dp + dm, W[i - 1])
    W = smooth(np.stack([W, W], 1), 7)[:, 0]
    first = i_r
    # FIT, NOT INTERPOLATE: a least-squares cubic spline through x(s), y(s) and w(s) with a few
    # knots. The raw skeleton carries pixel noise; a curve drawn THROUGH every sample turned that
    # noise into wobbles on the stroke's inner edge, where an offset amplifies any wander in the
    # centerline's direction by the half-width. The fit error is printed (fit_err, x-heights).
    from scipy.interpolate import LSQUnivariateSpline
    sN = s_ / s_[-1]
    def fit(v, nk):
        kn = np.linspace(0, 1, nk + 2)[1:-1]
        return LSQUnivariateSpline(sN, v, kn, k=3)(sN)
    Pf = np.stack([fit(P[:, 0], 9), fit(P[:, 1], 9)], 1)
    fit_err = float(np.max(np.hypot(*(Pf - P).T))) / XHPX
    P = resample(Pf, len(P)); W = fit(W, 7)
    # the font's stem: the l at mid-height (horizontal run, corrected for the slant)
    a, l, t = raster(f, 'l'); m = a >= 128
    ys = np.nonzero(m.any(1))[0]; mid = (ys.min() + ys.max()) // 2
    run = float(np.median([np.ptp(np.nonzero(m[r])[0]) + 1 for r in range(mid - 20, mid + 20) if m[r].any()]))
    stem = run      # a SHEARED stem keeps its horizontal width (a cos(slant) here understated the
                    # italic stem and overstated every italic width by ~2%; round 452's review)
    # the a's foot: its rightmost ink at the baseline band
    band = cb[T - int(0.05 * XHPX):T + int(0.02 * XHPX), :]
    a_right = (np.nonzero(band.any(0))[0].max() + L) / XHPX
    idx = np.linspace(0, len(P) - 1, N).round().astype(int)
    X = (P[idx, 1] + L) / XHPX; Y = (T - P[idx, 0]) / XHPX
    return dict(label=lab, x=(X - X[0]).tolist(), y=(Y - Y[0]).tolist(), w=(W[idx] / stem).tolist(),
                stem=stem / XHPX, root_in=a_right - X[0], first_clean=first / (len(P) - 1), fit_err=fit_err,
                length=float(np.sum(np.hypot(*np.diff(P, axis=0).T))) / XHPX,
                _P=P, _W=W, _L=L, _T=T, _ca=ca, _og=og)


def table(traces, keys):
    xs = np.mean([traces[k]['x'] for k in keys], 0); ys = np.mean([traces[k]['y'] for k in keys], 0)
    ws = np.mean([traces[k]['w'] for k in keys], 0)
    return [(round(float(x), 4), round(float(y), 4), round(float(w), 3)) for x, y, w in zip(xs, ys, ws)]


def write_module(tabs, traces):
    lines = ['"""GENERATED by instruments/ogonek_trace.py --write -- do not edit by hand.',
             '', 'The reference ogoneks traced: (x, y, width) per sample, root to tip at equal arc length.',
             'x and y in x-heights from the root (the point where the mark leaves the letter, on the',
             'baseline), y up; width in the reference\'s own lowercase stem. Round 452, 2026-09-30.',
             '', 'Sources and root offsets (the root, x-heights inside the a\'s rightmost foot ink):']
    for k, t in traces.items():
        lines.append(f'    {t["label"]:11s} length {t["length"]:.3f}  root in {t["root_in"]:+.3f}  stem {t["stem"]:.3f}')
    lines += ['"""', '', 'TABLES = {']
    for name, d in tabs.items():
        lines.append(f'    {name!r}: {{')
        for cut, rows in d.items():
            lines.append(f'        {cut!r}: [')
            for r in rows: lines.append(f'            {r},')
            lines.append('        ],')
        lines.append('    },')
    lines.append('}')
    roots = {name: {cut: round(float(np.mean([traces[k]['root_in'] for k in keys])), 4) for cut, keys in d.items()} for name, d in TABLES.items()}
    lines += ['', '# the root, x-heights inside the a\'s rightmost foot ink, per table and cut', f'ROOT_IN = {roots!r}', '']
    out = os.path.join(ROOT, 'outlines', 'glyphs', 'ogonek_traced.py')
    open(out, 'w').write('\n'.join(lines)); print('wrote', out)


def diag(traces, out):
    from PIL import Image, ImageDraw
    ims = []
    for k, t in traces.items():
        ca, og, P, W, T = t['_ca'], t['_og'], t['_P'], t['_W'], t['_T']
        img = np.where(ca, 0, 255).astype(np.uint8); img = np.stack([img] * 3, -1)
        img[og] = (img[og] * 0.4 + np.array([255, 160, 140]) * 0.6).astype(np.uint8)
        im = Image.fromarray(img); d = ImageDraw.Draw(im); tn = tangents(P)
        for i in range(0, len(P), 16):
            nrm = np.array([tn[i][1], -tn[i][0]]); a = P[i] + nrm * W[i] / 2; b = P[i] - nrm * W[i] / 2
            d.line([(a[1], a[0]), (b[1], b[0])], fill=(30, 110, 230), width=2)
        d.line([(p[1], p[0]) for p in P], fill=(220, 20, 20), width=3)
        d.line([(0, T), (im.width, T)], fill=(150, 150, 150))
        cx = int(np.mean(P[:, 1])); im = im.crop((cx - int(0.55 * XHPX), T - int(0.25 * XHPX), cx + int(0.5 * XHPX), T + int(0.72 * XHPX)))
        try:
            from PIL import ImageFont
            fnt = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 34)
        except Exception:
            fnt = None
        dd = ImageDraw.Draw(im); dd.rectangle([0, 0, 260, 50], fill=(255, 255, 255)); dd.text((10, 8), t['label'], fill=(0, 0, 0), font=fnt)
        ims.append(im)
    W_ = sum(i.width for i in ims); o = Image.new('RGB', (W_, ims[0].height), 'white'); x = 0
    for i in ims: o.paste(i, (x, 0)); x += i.width
    o.save(out); print(out, o.size)      # native pixels: a proof figure is never resampled


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--write', action='store_true'); ap.add_argument('--diag')
    ap.add_argument('--keys', help='comma-separated FONTS keys to trace (default all; --write needs all)')
    a = ap.parse_args()
    keys = a.keys.split(',') if a.keys else list(FONTS)
    if a.write and a.keys: sys.exit('--write regenerates every table: run it without --keys')
    traces = {k: trace(k) for k in keys}
    for k, t in traces.items():
        i = [0, 6, 12, 18, 24, 30, 36, 42, 48]
        print(f"{t['label']:11s} len {t['length']:.3f}  root in {t['root_in']:+.3f}  fit {t['fit_err']:.4f}  clean from t {t['first_clean']:.2f}  "
              f"w/stem " + ' '.join(f"{t['w'][j]:.2f}" for j in i) + f"   tip ({t['x'][-1]:+.2f},{t['y'][-1]:+.2f}) min y {min(t['y']):+.2f}")
    if a.write:
        tabs = {name: {cut: table(traces, ks) for cut, ks in d.items()} for name, d in TABLES.items()}
        write_module(tabs, traces)
    if a.diag: diag(traces, a.diag)
