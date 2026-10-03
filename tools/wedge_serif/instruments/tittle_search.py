#!/usr/bin/env python3
"""tittle_search.py -- how small can the i and j's dot get, and where must it sit, before any of the
reader's twelve rasters loses it? Owner todo 2026-10-02: *"reduce tittles slightly without losing
them at small scale"* (docs/albo-tittles-2026-10-02.md).

    $VENV/bin/python instruments/tittle_search.py FONT.ttf [--k 0.80:1.00:0.01] [--dy -12:12:1] [--dx 0:0:1]

The reader rasterizes each glyph ONCE per size (8..18 pt at 1x and 2x, 150 dpi, unhinted), so a
dot's pixel phase at every size is fixed by its outline coordinates. This takes the built dot
contour of 'i' and 'j' (the topmost contour), scales it about the centre of its FLOOR by k (so the
white under it is kept, as `stems.dot_y` and the aldine HM_DOT_KEEP_FLOOR both do), lifts it dy
units and moves it dx units sideways (0 unless asked: a dot off its stem's axis), and computes each pixel's exact area coverage (shapely) at each raster. Dark = coverage
>= 0.5, which is parts_audit's level >= 2 (a8 >= 128). Unhinted FreeType coverage is the exact area,
so this reproduces parts_check's dot count (checked against it at k 1, dy 0 for every cut).

A (k, dy) PASSES when no size falls below min(4, today's count): no raster may lose its dot past
parts_audit's floor, and a raster already under the floor may not lose a pixel more.
"""
import sys
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen, DecomposingRecordingPen
from fontTools.pens.basePen import BasePen
from shapely.geometry import Polygon, box
SIZES = [(pt, t) for t in (1, 2) for pt in (8, 10, 12, 14, 16, 18)]


class Flat(BasePen):
    def __init__(s, gs): super().__init__(gs); s.cs = []; s.cur = []
    def _moveTo(s, p): s.cur = [p]
    def _lineTo(s, p): s.cur.append(p)
    def _qCurveToOne(s, p1, p2):
        p0 = s.cur[-1]
        for t in np.linspace(0, 1, 9)[1:]:
            s.cur.append(((1-t)**2*p0[0]+2*(1-t)*t*p1[0]+t*t*p2[0], (1-t)**2*p0[1]+2*(1-t)*t*p1[1]+t*t*p2[1]))
    def _curveToOne(s, p1, p2, p3):
        p0 = s.cur[-1]
        for t in np.linspace(0, 1, 13)[1:]:
            a, b, c, d = (1-t)**3, 3*(1-t)**2*t, 3*(1-t)*t*t, t**3
            s.cur.append((a*p0[0]+b*p1[0]+c*p2[0]+d*p3[0], a*p0[1]+b*p1[1]+c*p2[1]+d*p3[1]))
    def _closePath(s): s.cs.append(s.cur); s.cur = []
    _endPath = _closePath


def dot_contour(tt, name):
    gs = tt.getGlyphSet(); p = Flat(gs); gs[name].draw(p)
    return Polygon(max(p.cs, key=lambda c: min(y for _, y in c)))


def dark(poly, upm, pt, t):
    s = 150 / 72 * pt * t / upm; x0, y0, x1, y1 = poly.bounds; n = 0
    P = Polygon([(x * s, y * s) for x, y in poly.exterior.coords])
    for i in range(int(np.floor(x0 * s)), int(np.ceil(x1 * s))):
        for j in range(int(np.floor(y0 * s)), int(np.ceil(y1 * s))):
            if P.intersection(box(i, j, i + 1, j + 1)).area >= 0.5: n += 1
    return n


def variant(poly, k, dy, dx=0):
    x0, y0, x1, y1 = poly.bounds; cx = (x0 + x1) / 2
    return Polygon([(cx + (x - cx) * k + dx, y0 + (y - y0) * k + dy) for x, y in poly.exterior.coords])


def rng(spec, default):
    a, b, st = (float(v) for v in (spec or default).split(":")); return np.round(np.arange(a, b + st / 2, st), 4)


if __name__ == "__main__":
    path = sys.argv[1]; arg = dict(zip(sys.argv[2::2], sys.argv[3::2]))
    tt = TTFont(path); upm = tt["head"].unitsPerEm
    ks, dys, dxs = rng(arg.get("--k"), "0.80:1.00:0.01"), rng(arg.get("--dy"), "-12:12:1"), rng(arg.get("--dx"), "0:0:1")
    dots = {g: dot_contour(tt, g) for g in ("i", "j")}
    today = {g: [dark(p, upm, *z) for z in SIZES] for g, p in dots.items()}
    print(path.split("/")[-1], "today", {g: v for g, v in today.items()})
    for k in ks:
        ok = []
        for dy in dys:
            for dx in dxs:
                cnt = {g: [dark(variant(p, k, dy, dx), upm, *z) for z in SIZES] for g, p in dots.items()}
                if all(c >= min(4, t0) for g in cnt for c, t0 in zip(cnt[g], today[g])):
                    ok.append(int(dy) if len(dxs) == 1 else (int(dy), int(dx)))
        print(f"  k {k:.2f}: passing {'dy' if len(dxs) == 1 else '(dy, dx)'} {ok if ok else '-'}")
