"""The brush strokes under a g: skeleton, direction, thickness -- on any font.

Owner 2026-09-17: *"copy off coelacanth for g until you understand how the brush
strokes underlie the form."*

`docs/italic-g-strokes.md` did this once, on 2026-09-14, for the ROMAN italic's
g, and it ends with the rule this instrument exists to apply:

    When a stroke comes out the wrong weight, check its DIRECTION before its
    width. In a pen model the width IS a function of where the stroke is going.

METHOD. The glyph is rasterised unsheared at a fixed x-height; a chamfer
distance transform is taken over the ink; the ridge of that transform is the
stroke's centreline, and the local thickness is twice the distance there. The
local DIRECTION comes from the principal axis of the neighbouring ridge points.
Binning thickness by direction gives the PEN'S OWN SIGNATURE -- the direction
that comes out thinnest is the angle the nib's edge is held at, and the ratio of
thickest to thinnest is its contrast.

WHAT IT IS FOR. A face drawn on a pen has ONE signature for the whole letter: a
run at 20 degrees is thin wherever in the letter it happens. A face whose widths
were DECLARED per-region does not -- its loop can be thick in a direction its
bowl is thin in, which is the fingerprint of a width table standing in for a
pen, and no amount of re-tuning that table will make the letter read as written.

    PYTHON_GIL=0 python3 cmp_g_strokes.py            # Coelacanth, Flanker, Albo
    PYTHON_GIL=0 python3 cmp_g_strokes.py --ttf X.ttf --slant 13 --part loop
"""
import argparse, math, os, sys
import numpy as np


def raster(ttf, ch, slant, px=520):
    from PIL import Image, ImageDraw, ImageFont
    from fontTools.ttLib import TTFont
    f = TTFont(ttf); upm = f["head"].unitsPerEm
    try: sx = f["OS/2"].sxHeight or upm * 0.5
    except Exception: sx = upm * 0.5
    size = int(round(px * upm / sx)); W = H = size * 3; base = int(H * 0.62)
    im = Image.new("L", (W, H), 255)
    ImageDraw.Draw(im).text((W * 0.35, base), ch,
                            font=ImageFont.truetype(ttf, size), fill=0, anchor="ls")
    if abs(slant) > 0.05:
        k = -math.tan(math.radians(slant))   # sign fixed 2026-09-18: +13 was doubling the shear (see cmp_weight_survey.raster)
        im = im.transform((W, H), Image.AFFINE, (1, k, -k * base, 0, 1, 0),
                          resample=Image.BICUBIC, fillcolor=255)
    a = np.asarray(im) < 128
    ys, xs = np.nonzero(a)
    return a[ys.min():ys.max() + 1, xs.min():xs.max() + 1], base - ys.min(), px


def dist(mask):
    """Chamfer distance to background. Row-sequential, column-vectorised."""
    INF = 1e9
    d = np.where(mask, INF, 0.0)
    H, W = d.shape
    for y in range(H):
        r = d[y].copy()
        if y > 0:
            up = d[y - 1]
            r = np.minimum(r, up + 1.0)
            r[1:] = np.minimum(r[1:], up[:-1] + 1.414)
            r[:-1] = np.minimum(r[:-1], up[1:] + 1.414)
        for x in range(1, W):
            if r[x] > r[x - 1] + 1.0: r[x] = r[x - 1] + 1.0
        for x in range(W - 2, -1, -1):
            if r[x] > r[x + 1] + 1.0: r[x] = r[x + 1] + 1.0
        d[y] = r
    for y in range(H - 2, -1, -1):
        r = d[y].copy(); dn = d[y + 1]
        r = np.minimum(r, dn + 1.0)
        r[1:] = np.minimum(r[1:], dn[:-1] + 1.414)
        r[:-1] = np.minimum(r[:-1], dn[1:] + 1.414)
        for x in range(1, W):
            if r[x] > r[x - 1] + 1.0: r[x] = r[x - 1] + 1.0
        for x in range(W - 2, -1, -1):
            if r[x] > r[x + 1] + 1.0: r[x] = r[x + 1] + 1.0
        d[y] = r
    return d


def ridge(mask, d, floor=1.5):
    """Centreline samples: ink whose distance is a local maximum along BOTH
    axes. `floor` drops only the 1-2 px fringe where the transform is noise.

    NO PERCENTILE THRESHOLD, and that is the whole point. A first cut kept only
    the ink in the top 38% of the distance range, which is not a mild filter --
    it DELETES EVERY THIN STROKE FROM THE SAMPLE, because a thin stroke's
    distance is small everywhere along it. Measured on Coelacanth, that cut
    reported the pen's contrast as 1.50:1 with its thin and thick 45 degrees
    apart; the letter's real figures are below and the 2026-09-14 pass on the
    roman italic got 2.3:1 at 90 degrees apart, which is what a broad nib must
    give. An instrument that samples only the thick parts of a letter cannot
    measure how thin the thin parts are."""
    H, W = d.shape
    out = []
    for y in range(1, H - 1):
        for x in range(1, W - 1):
            if not mask[y, x] or d[y, x] < floor: continue
            v = d[y, x]
            if v >= d[y, x - 1] and v >= d[y, x + 1] and v >= d[y - 1, x] and v >= d[y + 1, x]:
                out.append((y, x, v))
    return out


def directions(pts, r=7):
    """Local run direction at each ridge point, from the principal axis of its
    neighbours. Returned in degrees 0..180 (a stroke has no head or tail)."""
    P = np.array([(p[1], -p[0]) for p in pts], float)   # x, y-up
    out = []
    for i, p in enumerate(P):
        n = P[np.abs(P[:, 0] - p[0]) <= r]
        n = n[np.abs(n[:, 1] - p[1]) <= r]
        if len(n) < 4: out.append(None); continue
        c = n - n.mean(0)
        w, v = np.linalg.eigh(c.T @ c)
        ax = v[:, -1]
        out.append(math.degrees(math.atan2(ax[1], ax[0])) % 180.0)
    return out


def signature(ttf, slant, label, px=520, part=None, band=15):
    mask, base, px = raster(ttf, "g", slant, px)
    H, W = mask.shape
    sel = np.zeros_like(mask)
    if part == "loop":   sel[base:] = True
    elif part == "bowl": sel[:base] = True
    else:                sel[:] = True
    m = mask & sel
    if m.sum() < 200: return None
    d = dist(mask)                      # distance over the WHOLE glyph
    pts = [p for p in ridge(mask, d) if sel[p[0], p[1]]]
    dirs = directions(pts)
    bins = {}
    for (y, x, v), a in zip(pts, dirs):
        if a is None: continue
        bins.setdefault(int(a // band) * band, []).append(2 * v)
    prof = {b: float(np.median(v)) for b, v in sorted(bins.items()) if len(v) >= 4}
    if len(prof) < 4: return None
    thin = min(prof, key=prof.get); thick = max(prof, key=prof.get)
    print(f"\n  {label}{'  [' + part + ']' if part else ''}   {len(pts)} ridge samples")
    print("    dir " + " ".join(f"{b:>5}" for b in prof))
    print("    wid " + " ".join(f"{prof[b]:5.0f}" for b in prof))
    print(f"    thinnest at {thin:3d} deg, thickest at {thick:3d} deg"
          f"   -> pen edge ~{thin:d} deg, contrast {prof[thick]/prof[thin]:.2f}:1"
          f"   (thin and thick {min(abs(thick-thin), 180-abs(thick-thin)):d} deg apart)")
    return prof


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ttf", action="append", default=[])
    ap.add_argument("--slant", action="append", type=float, default=[])
    ap.add_argument("--px", type=int, default=520)
    a = ap.parse_args()
    HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
    subjects = []
    if a.ttf:
        for i, t in enumerate(a.ttf):
            subjects.append((t, a.slant[i] if i < len(a.slant) else 0.0, os.path.basename(t)))
    else:
        import refs_registry as RR
        for n in ("Coelacanth", "Flanker Griffo"):
            subjects.append((RR.path(n), RR.slant(n), n))
    print("\nTHE PEN'S SIGNATURE -- stroke thickness against the direction the stroke runs")
    print("(a face drawn on one pen has ONE signature for the whole letter)")
    for t, s, n in subjects:
        signature(t, s, n, a.px)
        signature(t, s, n, a.px, "bowl")
        signature(t, s, n, a.px, "loop")
    print()


if __name__ == "__main__":
    main()
