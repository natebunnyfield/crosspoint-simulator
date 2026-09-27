"""Axes (a)-(e) of the fit metric, measured on one face.

Everything is FreeType, NO HINTING (round 401: the reader loads Albo with
FT_LOAD_NO_HINTING), so the audit sees the pixels the reader draws:

  (a) COLOUR AS RENDERED: the converter's 2-bit levels (8-bit coverage, top
      nibble, >=12/8/4 -> 3/2/1) at the reader's sizes -- 8, 10, 12, 14, 16,
      18 pt at 150 dpi (16.7-37.5 ppem) and the phone's 2x tier -- ink summed
      in the READING BAND (baseline to x-height, or cap height for a capital)
      over (linear advance x band height). A hairline that the 2-bit cut drops
      at 16.7 ppem is gone from this number, which is the point.
  (b) STROKE: the chamfer-ridge method of cmp_weight_survey.py (no percentile
      threshold on the ridge), on an exact Euclidean transform of an
      UNSHEARED raster at 1200 ppem: thin = p10, stroke = p50, cut = p90/p10.
  (c) PROPORTION: ink width / reference height (unsheared), open white =
      1 - ink / convex hull (aperture and open counters), closed counter area
      / reference height^2.
  (d) VERTICAL: ink top and bottom against the line the glyph belongs to
      (x-height / ascender / cap / figure-ascender; baseline / descender),
      class decided from the outline, in reference heights.
  (e) SIDEBEARINGS: the white between the advance's edges and the ink, row by
      row across the reading band AS SET (italics sheared, as read), each row
      clipped at 0.6 of the band; balance = (L - R)/(L + R), looseness =
      (L + R) / band.

    python3 geom.py FONT[:index] [--out f.json]
"""
import json, math, sys
import numpy as np
import freetype
from scipy import ndimage
from scipy.spatial import ConvexHull

sys.path.insert(0, __import__("os").path.dirname(__file__))
from common import Font, CHARS, UC, FIG, LC  # noqa: E402

READER_PT = [8, 10, 12, 14, 16, 18]
HI_PPEM = 1200


def quantize(a8):
    n = a8 >> 4
    return np.where(n >= 12, 3, np.where(n >= 8, 2, np.where(n >= 4, 1, 0)))


def render(F, ch, size64, dpi, shear=0.0):
    """(8-bit coverage array, bitmap_left, bitmap_top, linear advance px)."""
    f = freetype.Face(F.path, F.index)
    f.set_char_size(size64, size64, dpi, dpi)
    if shear:
        t = math.tan(math.radians(shear))
        m = freetype.Matrix(0x10000, int(-t * 0x10000), 0, 0x10000)
        f.set_transform(m, freetype.Vector(0, 0))
    f.load_glyph(F.gid[F.glyph(ch)], freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING)
    b = f.glyph.bitmap
    if b.rows == 0:
        return None
    a8 = np.frombuffer(bytes(b.buffer), dtype=np.uint8).reshape(b.rows, b.pitch)[:, :b.width]
    return a8, f.glyph.bitmap_left, f.glyph.bitmap_top, f.glyph.linearHoriAdvance / 65536.0


def colour(F, ch, tier):
    h = F.ref_height(ch)
    vals = []
    for pt in READER_PT:
        size = pt * tier
        r = render(F, ch, size * 64, 150)
        if r is None:
            return float("nan")
        a8, left, top, adv = r
        lv = quantize(a8) / 3.0
        ppem = size * 150 / 72.0
        hpx = h * ppem / F.upm
        yc = top - np.arange(lv.shape[0]) - 0.5          # row centres, px above baseline
        rows = (yc >= 0) & (yc <= hpx)
        vals.append(lv[rows].sum() / (adv * hpx))
    return float(np.mean(vals))


def hi_mask(F, ch, shear):
    r = render(F, ch, HI_PPEM * 64, 72, shear)
    a8, left, top, adv = r
    m = np.pad(a8 >= 128, 8)
    return m, left - 8, top + 8, adv


def stroke(mask, u):
    d = ndimage.distance_transform_edt(mask)
    p = np.pad(d, 1)
    c = p[1:-1, 1:-1]
    keep = (mask & (d >= 1.5) & (c >= p[1:-1, :-2]) & (c >= p[1:-1, 2:])
            & (c >= p[:-2, 1:-1]) & (c >= p[2:, 1:-1]))
    t = 2.0 * d[keep] * u
    if not len(t):
        return dict(thin=np.nan, stroke=np.nan, thick=np.nan, cut=np.nan)
    thin, med, thick = np.percentile(t, [10, 50, 90])
    return dict(thin=float(thin), stroke=float(med), thick=float(thick), cut=float(thick / thin))


def proportion(mask, u, h):
    ys, xs = np.nonzero(mask)
    width = (xs.max() - xs.min() + 1) * u / h
    ink = mask.sum()
    pts = np.c_[xs, ys].astype(float)
    try:
        hull = ConvexHull(pts).volume
    except Exception:
        hull = ink
    filled = ndimage.binary_fill_holes(mask).sum()
    return dict(width=float(width), open=float(1 - ink / max(hull, 1)),
                closed=float((filled - ink) * u * u / (h * h)))


def lines(F):
    """The face's own reference lines, font units."""
    xh, cap = F.xh, F.cap
    asc = [F.bbox(c)[3] for c in "bdhkl"]
    desc = [F.bbox(c)[1] for c in "pq"]
    ftop = [F.bbox(c)[3] for c in FIG if F.bbox(c)[3] > 1.2 * xh]
    fbot = [F.bbox(c)[1] for c in FIG if F.bbox(c)[1] < -0.25 * xh]
    return dict(xh=xh, cap=cap, asc=float(np.median(asc)), desc=float(np.median(desc)),
                fasc=float(np.median(ftop)) if ftop else cap,
                fdesc=float(np.median(fbot)) if fbot else float(np.median(desc)))


def vertical(F, ch, L):
    x0, y0, x1, y1 = F.bbox(ch)
    h = F.ref_height(ch)
    top = bot = float("nan")
    tcls = bcls = None
    if ch in UC:
        tcls = "cap"; top = (y1 - L["cap"]) / h
        if y0 > -0.12 * h:
            bcls = "base"; bot = y0 / h
    else:
        asc = y1 > 1.2 * L["xh"]
        if ch not in "ijt":
            tcls = ("fasc" if ch in FIG else "asc") if asc else "xh"
            top = (y1 - L[tcls]) / h
        desc = y0 < -0.25 * L["xh"]
        bcls = ("fdesc" if ch in FIG else "desc") if desc else "base"
        bot = (y0 - (L[bcls] if desc else 0.0)) / h
    return dict(top=top, bot=bot, tcls=tcls, bcls=bcls)


def bearings(F, ch):
    """Row-wise white as set, reading band only."""
    m, left, top, adv = hi_mask(F, ch, 0.0)
    h = F.ref_height(ch)
    u = F.upm / HI_PPEM
    hpx = h / u
    clip = 0.6 * hpx
    Ls, Rs = [], []
    for r in range(m.shape[0]):
        yc = top - r - 0.5
        if yc < 0 or yc > hpx:
            continue
        xs = np.nonzero(m[r])[0]
        if not len(xs):
            Ls.append(clip); Rs.append(clip); continue
        Ls.append(min(clip, max(0.0, left + xs.min())))
        Rs.append(min(clip, max(0.0, adv - (left + xs.max() + 1))))
    Lm, Rm = float(np.mean(Ls)), float(np.mean(Rs))
    return dict(balance=(Lm - Rm) / max(Lm + Rm, 1e-6), loose=(Lm + Rm) / hpx)


def measure_font(path, index=0, chars=CHARS):
    F = Font(path, index)
    L = lines(F)
    out = {}
    for ch in chars:
        if F.glyph(ch) is None:
            continue
        h = F.ref_height(ch)
        m, left, top, adv = hi_mask(F, ch, F.slant)
        u = F.upm / HI_PPEM
        row = {}
        row.update(stroke(m, u))
        row.update(proportion(m, u, h))
        row.update(vertical(F, ch, L))
        row.update(bearings(F, ch))
        row["col1x"] = colour(F, ch, 1)
        row["col2x"] = colour(F, ch, 2)
        out[ch] = row
    return dict(path=path, index=index, slant=F.slant, lines=L, glyphs=out)


if __name__ == "__main__":
    a = sys.argv[1:]
    p = a[0]
    idx = 0
    if ":" in p and not p.endswith(".ttf"):
        p, idx = p.rsplit(":", 1); idx = int(idx)
    res = measure_font(p, idx)
    if "--out" in a:
        json.dump(res, open(a[a.index("--out") + 1], "w"), indent=1)
    else:
        for ch, r in res["glyphs"].items():
            print(ch, {k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()})
