"""Every letter and figure, in both styles, measured the same way.

Owner 2026-09-17: *"do a full survey of all roman and italic letters and
numerals"*, asked in the same breath as making the g's lower loop match the
weight of its neighbours -- which is the question this answers for all 124
glyphs at once: is any letter lighter, heavier, wider or flatter than the face
it belongs to?

METHOD, and it is the one `cmp_g_strokes.py` established. The glyph is
rasterised UNSHEARED at a fixed x-height, a chamfer distance transform is taken
over the ink, and the ridge of that transform is the stroke's centreline; local
thickness is twice the distance there. No percentile threshold is applied to
the ridge -- that would delete every thin stroke from the sample and report a
face as far less contrasted than it is (the bug recorded in that file).

    thin    the 10th percentile of thickness along the centreline
    stroke  the median -- what the letter's weight actually reads as
    thick   the 90th percentile
    cut     thick / thin, the letter's own contrast
    colour  ink area over (advance x reference height), the letter's blackness

A letter is FLAGGED when its stroke median is more than `--tol` from the median
of its own group (lowercase, capitals, figures) in its own style, because a
face's groups legitimately differ from one another -- capitals carry more
weight than lowercase in every humanist face -- and comparing a G against an o
would flag half the alphabet for being itself.

    PYTHON_GIL=0 python3 cmp_weight_survey.py --roman R.ttf --italic I.ttf
    PYTHON_GIL=0 python3 cmp_weight_survey.py --json out.json --tol 0.18
"""
import argparse, json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont

XH = 429.0


def raster(ttf, ch, slant, px=380):
    f = TTFont(ttf); upm = f["head"].unitsPerEm
    sx = f["OS/2"].sxHeight or upm * 0.5
    size = int(round(px * upm / sx)); W = H = size * 3; base = int(H * 0.62)
    im = Image.new("L", (W, H), 255)
    ImageDraw.Draw(im).text((W * 0.33, base), ch,
                            font=ImageFont.truetype(ttf, size), fill=0, anchor="ls")
    if abs(slant) > 0.05:      # unshear, so a stroke's thickness is its own
        # TWO INSTRUMENT BUGS, found 2026-09-18 by the two glyph agents of the
        # misfit round and verified on the cases whose answers are known:
        # (1) THE SIGN. PIL's AFFINE maps output -> input, x_in = x + k*y, so a
        #     POSITIVE k here ADDED the shear instead of removing it: the italic
        #     l's stem, +12.2 deg at slant 0, read +24.0 deg at +13 and -0.8 deg
        #     at -13. Every italic number this script had produced -- the whole
        #     2026-09-17 ledger, rounds 208-219's matches, the audit's section
        #     (b) -- was measured at 26 degrees of shear. The sign is flipped so
        #     that `--slant 13` means what it says.
        k = -math.tan(math.radians(slant))
        im = im.transform((W, H), Image.AFFINE, (1, k, -k * base, 0, 1, 0),
                          resample=Image.BICUBIC, fillcolor=255)
    a = np.asarray(im) < 128
    ys, xs = np.nonzero(a)
    if not len(ys): return None, 0
    # (2) THE CROP EDGE. The mask was cropped to the ink's bounding box, so a
    #     stroke lying ON the box edge -- a bar, a stem's outer side, the top
    #     of a Z -- had no background beyond it and the chamfer read it at up
    #     to twice its thickness: the roman Z's 59-unit bars came back as 93
    #     and 117 and the letter as "+65%, the heaviest in the roman". It is
    #     not. The crop keeps a margin of background on every side now.
    PADX = 48
    y0, y1 = max(0, ys.min() - PADX), min(a.shape[0], ys.max() + 1 + PADX)
    x0, x1 = max(0, xs.min() - PADX), min(a.shape[1], xs.max() + 1 + PADX)
    return a[y0:y1, x0:x1], base - ys.min()


def chamfer(mask):
    """Two-pass 3-4 chamfer, scaled back to pixels."""
    INF = 1 << 20
    d = np.where(mask, INF, 0).astype(np.int32)
    H, W = d.shape
    for y in range(H):
        row = d[y]
        up = d[y - 1] if y else None
        for x in range(W):
            if not mask[y, x]: continue
            v = row[x]
            if x: v = min(v, row[x - 1] + 3)
            if up is not None:
                v = min(v, up[x] + 3)
                if x: v = min(v, up[x - 1] + 4)
                if x + 1 < W: v = min(v, up[x + 1] + 4)
            row[x] = v
    for y in range(H - 1, -1, -1):
        row = d[y]
        dn = d[y + 1] if y + 1 < H else None
        for x in range(W - 1, -1, -1):
            if not mask[y, x]: continue
            v = row[x]
            if x + 1 < W: v = min(v, row[x + 1] + 3)
            if dn is not None:
                v = min(v, dn[x] + 3)
                if x + 1 < W: v = min(v, dn[x + 1] + 4)
                if x: v = min(v, dn[x - 1] + 4)
            row[x] = v
    return d / 3.0


def ridge_vals(mask, d, floor=1.5):
    """Thickness along the centreline -- vectorised, same rule as
    cmp_g_strokes.ridge: ink whose distance is a local max on both axes."""
    p = np.pad(d, 1, mode="constant")
    c = p[1:-1, 1:-1]
    keep = (mask & (d >= floor)
            & (c >= p[1:-1, :-2]) & (c >= p[1:-1, 2:])
            & (c >= p[:-2, 1:-1]) & (c >= p[2:, 1:-1]))
    return d[keep]


def measure(ttf, ch, slant, px=380):
    mask, base = raster(ttf, ch, slant, px)
    if mask is None: return None
    d = chamfer(mask)
    v = ridge_vals(mask, d)
    if not len(v): return None
    u = XH / px
    t = 2.0 * v * u
    f = TTFont(ttf); upm = f["head"].unitsPerEm
    adv = f["hmtx"][f.getBestCmap()[ord(ch)]][0] / upm * 1000.0
    ref = XH if ch.islower() else (f["OS/2"].sCapHeight or 674)
    # COLOUR IS MEASURED IN THE READING BAND, not over the whole glyph. The
    # first cut divided the letter's whole ink by (advance x x-height), which
    # reads an f at 0.77 and an l at 0.57 against an o's 0.39 -- the ascender's
    # ink counted against a box that stops at the x-height. What sets a word's
    # colour is the band the word is read in, so the ink is taken from the
    # baseline up to the reference height and nothing above or below it counts.
    lo = max(0, int(round(base - ref / u)))
    band = mask[lo:base + 1, :] if base > lo else mask
    ink = band.sum() * u * u
    return dict(ch=ch, thin=float(np.percentile(t, 10)), stroke=float(np.median(t)),
                thick=float(np.percentile(t, 90)), n=int(len(t)),
                adv=float(adv), colour=float(ink / (adv * ref)))


GROUPS = [("lowercase", "abcdefghijklmnopqrstuvwxyz"),
          ("capitals", "ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
          ("figures", "0123456789")]


def survey(ttf, slant, px=380):
    out = {}
    for name, chars in GROUPS:
        rows = [measure(ttf, c, slant, px) for c in chars]
        out[name] = [r for r in rows if r]
    return out


def report(data, tol):
    flagged = []
    for style, groups in data.items():
        print(f"\n=== {style} ===")
        for name, rows in groups.items():
            med = float(np.median([r["stroke"] for r in rows]))
            cmed = float(np.median([r["colour"] for r in rows]))
            print(f"\n{name}  (stroke median {med:.1f} units, colour median {cmed:.3f})")
            print(f"  {'ch':3s} {'thin':>6s} {'stroke':>7s} {'thick':>6s} {'cut':>5s} "
                  f"{'colour':>7s} {'adv':>6s}  off")
            for r in sorted(rows, key=lambda r: r["stroke"]):
                off = r["stroke"] / med - 1.0
                mark = "  <<" if abs(off) > tol else ""
                if mark: flagged.append((style, name, r["ch"], off))
                print(f"  {r['ch']:3s} {r['thin']:6.1f} {r['stroke']:7.1f} {r['thick']:6.1f} "
                      f"{r['thick']/max(r['thin'],1e-6):5.2f} {r['colour']:7.3f} "
                      f"{r['adv']:6.0f}  {off:+5.0%}{mark}")
    return flagged


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--roman", default="fonts/rebuild/Albo-Medium.ttf")
    ap.add_argument("--italic", default="fonts/rebuild/Albo-Italic.ttf")
    ap.add_argument("--slant", type=float, default=13.0)
    ap.add_argument("--px", type=int, default=380)
    ap.add_argument("--tol", type=float, default=0.15)
    ap.add_argument("--json")
    a = ap.parse_args()
    data = {}
    if os.path.exists(a.roman): data["roman"] = survey(a.roman, 0.0, a.px)
    if os.path.exists(a.italic): data["italic"] = survey(a.italic, a.slant, a.px)
    if not data: sys.exit("no fonts found")
    flagged = report(data, a.tol)
    if a.json: json.dump(data, open(a.json, "w"))
    print(f"\n{sum(len(g) for s in data.values() for g in s.values())} glyphs measured, "
          f"{len(flagged)} outside {a.tol:.0%} of their group")


if __name__ == "__main__":
    main()
