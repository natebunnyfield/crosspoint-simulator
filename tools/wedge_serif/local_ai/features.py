#!/usr/bin/env python3
"""Shape features of every bench pair, measured on the fonts he judged.

PROBE for docs/local-ai-spacing-options-2026-09-26.md (owner 2026-09-26: "an ai
i can run on my mac mini ... that is able to adjust letters and kerning well
based on word image legibility").  Not a shipping tool.

WHAT IS MEASURED.  Every row of the 396-row bench, both styles, on the SAME two
font files the bench served (bench/fonts-2026-09-20/, which predate every
answer), shaped with HarfBuzz so the pair's own kern is in it -- the kern this
reads is checked against the bench's recorded `kr`/`ki` offsets and must agree
on all 396 rows, or the script refuses.  All numbers are in design units
(UPM 1000), rasterized with FreeType at 4 units per pixel.

    h_gap      rsb(A) + kern + lsb(B), the bbox white (gap_measure.py's measure)
    d2         closest approach in two dimensions (cmp_space_2d.py's measure 4)
    band_*     per-band row gaps: mean / min over rows where BOTH glyphs have
               ink, in the descender, x-height and ascender bands
    area_x     HT-Letterspacer-style white area: mean row gap over the WHOLE
               x band, each row's gap capped at 150 units (a row where one
               glyph is absent reads the cap) -- depth-limited white
    prof_*     each facing side's depth profile at 8 heights (distance from the
               glyph's own x-band extreme to its ink, capped at 200)
    inner_*    each glyph's own enclosed white (mean width of white runs that
               lie between ink, x band) -- "the space between letters is judged
               against the space inside them" (albo-spacing-method.md)
    blur_*     optical darkness: the pair blurred at sigma 40 units (about half
               the 84-unit stem), mean blurred ink in the gap strip vs over the
               pair's x band -- a YinYangFit-lite reading
    flags      capL, markL, markR, italic

Writes features-2026-09-20.json beside this file.

    $VENV/bin/python features.py      (venv: see requirements.txt)
"""
import json, os, sys
import numpy as np
import uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.pens.freetypePen import FreeTypePen
from fontTools.pens.transformPen import TransformPen
from scipy.ndimage import gaussian_filter

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.dirname(HERE)
BENCH = os.path.join(WS, "bench")
ITEMS = os.path.join(BENCH, "bench-items-2026-09-20.json")
FONTS = {"roman": os.path.join(BENCH, "fonts-2026-09-20", "Albo-Regular.ttf"),
         "italic": os.path.join(BENCH, "fonts-2026-09-20", "Albo-Italic.ttf")}
OUT = os.path.join(HERE, "features-2026-09-20.json")
MARKS = set("'.,:;\"-!?’“”")

U = 4.0                      # design units per pixel
X0, BASE = 400, 350          # canvas origin offsets, units
XH, ASC, DESC = 429, 770, -280
HEIGHTS = np.linspace(-200, 700, 8)


class Font:
    def __init__(self, path):
        self.tt = TTFont(path)
        self.gs = self.tt.getGlyphSet()
        self.cmap = self.tt.getBestCmap()
        self.hb = hb.Font(hb.Face(hb.Blob.from_file_path(path)))
        self.order = self.tt.getGlyphOrder()

    def shape(self, a, b):
        buf = hb.Buffer(); buf.add_str(a + b); buf.guess_segment_properties()
        hb.shape(self.hb, buf, {"liga": False, "clig": False, "dlig": False})
        inf, pos = buf.glyph_infos, buf.glyph_positions
        if len(inf) != 2:
            raise SystemExit(f"{a}{b}: shaped to {len(inf)} glyphs")
        natural = self.hb.get_glyph_h_advance(inf[0].codepoint)
        kern = pos[0].x_advance - natural + pos[1].x_offset
        return [self.order[i.codepoint] for i in inf], natural, kern

    def mask(self, name, dx, W, H):
        pen = FreeTypePen(self.gs)
        self.gs[name].draw(TransformPen(pen, (1, 0, 0, 1, dx, 0)))
        return pen.array(width=W, height=H, transform=(1 / U, 0, 0, 1 / U, X0 / U, BASE / U)) > 0.5


def row_of(y_units, H):
    return int(round(H - (y_units + BASE) / U))


def edges(M):
    """per row: (leftmost ink x, rightmost ink x) in units, NaN where empty."""
    has = M.any(1)
    L = np.full(M.shape[0], np.nan); R = np.full(M.shape[0], np.nan)
    idx = np.nonzero(has)[0]
    for y in idx:
        xs = np.nonzero(M[y])[0]
        L[y], R[y] = xs[0], xs[-1]
    return L * U - X0, R * U - X0


def inner_white(M, r0, r1):
    runs = []
    for y in range(r0, r1):
        xs = np.nonzero(M[y])[0]
        if len(xs) < 2:
            continue
        gaps = np.diff(xs) - 1
        runs.extend(g for g in gaps if g > 0)
    return float(np.mean(runs) * U) if runs else 0.0


def pair_features(F, a, b, italic):
    names, adv, kern = F.shape(a, b)
    W = int((X0 + adv + kern + 1400) / U); H = int((BASE + 1000) / U)
    A = F.mask(names[0], 0, W, H)
    B = F.mask(names[1], adv + kern, W, H)
    LA, RA = edges(A); LB, RB = edges(B)
    rows = np.arange(H); yv = (H - rows) * U - BASE        # row -> y units
    both = ~np.isnan(RA) & ~np.isnan(LB)
    g = LB - RA - U                                         # white per row, units

    f = {}
    ha, hb_ = F.tt["hmtx"][names[0]], F.tt["hmtx"][names[1]]
    ga, gb = F.tt["glyf"][names[0]], F.tt["glyf"][names[1]]
    rsb = ha[0] - ha[1] - ((ga.xMax - ga.xMin) if ga.numberOfContours else 0)
    f["h_gap"] = float(rsb + kern + hb_[1])
    f["kern"] = float(kern)
    # d2: nearest boundary points
    PA = np.array([(RA[y], yv[y]) for y in rows if not np.isnan(RA[y])])
    PB = np.array([(LB[y], yv[y]) for y in rows if not np.isnan(LB[y])])
    d = np.sqrt((PA[:, None, 0] - PB[None, :, 0]) ** 2 + (PA[:, None, 1] - PB[None, :, 1]) ** 2)
    f["d2"] = float(d.min())
    for band, lo, hi in (("desc", DESC, 0), ("x", 0, XH), ("asc", XH, ASC)):
        sel = both & (yv >= lo) & (yv < hi)
        f[f"band_{band}_mean"] = float(np.mean(g[sel])) if sel.any() else 300.0
        f[f"band_{band}_min"] = float(np.min(g[sel])) if sel.any() else 300.0
        f[f"band_{band}_frac"] = float(sel.sum() / max(1, ((yv >= lo) & (yv < hi)).sum()))
    xs = (yv >= 0) & (yv < XH)
    # depth-limited white: measured from each glyph's own x-band extreme
    ra_ext = np.nanmax(np.where(xs, RA, np.nan)) if np.any(xs & ~np.isnan(RA)) else np.nanmax(RA)
    lb_ext = np.nanmin(np.where(xs, LB, np.nan)) if np.any(xs & ~np.isnan(LB)) else np.nanmin(LB)
    depA = np.clip(ra_ext - np.where(np.isnan(RA), -1e9, RA), 0, 150)
    depB = np.clip(np.where(np.isnan(LB), 1e9, LB) - lb_ext, 0, 150)
    f["area_x"] = float(np.mean((lb_ext - ra_ext) + depA[xs] + depB[xs]))
    for i, h in enumerate(HEIGHTS):
        r = row_of(h, H)
        f[f"profA_{i}"] = float(min(200, ra_ext - RA[r])) if not np.isnan(RA[r]) else 200.0
        f[f"profB_{i}"] = float(min(200, LB[r] - lb_ext)) if not np.isnan(LB[r]) else 200.0
    r0, r1 = row_of(XH, H), row_of(0, H)
    f["innerA"] = inner_white(A, r0, r1)
    f["innerB"] = inner_white(B, r0, r1)
    # optical darkness
    img = gaussian_filter((A | B).astype(float), 40 / U)
    band = img[r0:r1]
    cA = int((ra_ext + X0) / U); cB = int((lb_ext + X0) / U)
    lo_c, hi_c = min(cA, cB), max(cA, cB) + 1
    f["blur_gap"] = float(band[:, lo_c:hi_c].mean())
    cols = np.nonzero((A | B)[r0:r1].any(0))[0]
    f["blur_pair"] = float(band[:, cols[0]:cols[-1] + 1].mean()) if len(cols) else 0.0
    f["blur_ratio"] = f["blur_gap"] / max(1e-6, f["blur_pair"])
    f["capL"] = float(a.isupper()); f["markL"] = float(a in MARKS); f["markR"] = float(b in MARKS)
    f["italic"] = float(italic)
    return f, kern


def main():
    items = json.load(open(ITEMS))["items"]
    out = {}
    for style, path in FONTS.items():
        F = Font(path)
        rows = {}
        for it in items:
            a, b = it["pair"].split(" ")
            feats, kern = pair_features(F, a, b, style == "italic")
            want = it["kr" if style == "roman" else "ki"]
            if kern != want:
                sys.exit(f"{style} {a}{b}: kern {kern} but the bench served {want}")
            rows[a + b] = dict(word=it["word"], i=it["i"], n=it["n"], g=it["g"], f=feats)
        out[style] = rows
        print(f"{style}: {len(rows)} pairs measured")
    json.dump(out, open(OUT, "w"), indent=0)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
