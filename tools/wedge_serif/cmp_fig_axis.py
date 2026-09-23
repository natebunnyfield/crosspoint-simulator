"""WHERE A ROUND FIGURE CARRIES ITS INK, by clock position round its own ring.

Owner 2026-09-23, on a picture of the roman 8: *"thinning out bottom left stroke
and top right stroke of 8"*.

`cmp_g_strokes.py` answers "what pen is this letter drawn with" -- thickness
binned by the DIRECTION the stroke runs. That is the right question for a pen
signature and the wrong one for "is the 8 heavy at 7 o'clock", because a ring
runs through every direction and two places on the same ring can share a
direction. This instrument keeps `cmp_g_strokes`'s measure EXACTLY -- it imports
`raster`, `dist`, `ridge` and `directions` from it rather than re-deriving them,
so the thickness here is the same number that doc's tables are -- and changes
only the BINNING: by clock angle about the ring's own counter centroid.

WHY THE THICKNESS IS PERPENDICULAR BY CONSTRUCTION. The chamfer distance at a
ridge point is the radius of the largest circle inscribed in the ink there, so
twice it is the stroke's width measured ACROSS the stroke, whatever direction the
stroke runs. A horizontal scan line across a diagonal reads wide by 1/cos(theta)
and is one of the five recorded instrument bugs (docs/albo-method.md section 4);
nothing here scans a row.

CLOCK CONVENTION. 12 o'clock is the top of the ring, 3 the right flank, 6 the
bottom, 9 the left. The two places the owner named are 7-8 o'clock of the LOWER
ring (bottom left) and 1-2 o'clock of the UPPER ring (top right).

VALIDATION CASE, which the method doc demands before any number is believed:
Albo's bowl profile is `bowl_th`, width proportional to |sin(tangent)|**1.6 with
BOWL['stress'] = 0 (primitives.py:653, BOWL_OPTIONS['B'] carries no 'stress'
key) -- so every bowl in the face is VERTICALLY stressed: thickest where the
stroke runs vertical (3 and 9 o'clock) and thinnest where it runs horizontal (12
and 6). If this instrument reports Albo's own `o` or `0` any other way, the
instrument is wrong and nothing below it may be used.

    PYTHON_GIL=0 python3 cmp_fig_axis.py --ttf FONT.ttf            # 8 0 6 9 o O
    PYTHON_GIL=0 python3 cmp_fig_axis.py --ttf FONT.ttf --chars 8 --json out.json
    PYTHON_GIL=0 python3 cmp_fig_axis.py --refs                    # the reference romans
"""
import argparse, json, math, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from cmp_g_strokes import raster, dist, ridge          # the SAME measure, not a new one

SUP = "/System/Library/Fonts/Supplemental"
HOME = os.path.expanduser("~/Library/Fonts")
REF_ROMANS = [
    ("Georgia",        f"{SUP}/Georgia.ttf"),
    ("Big Caslon",     f"{SUP}/BigCaslon.ttf"),
    ("Flanker Griffo", f"{HOME}/flanker-griffo.regular.otf"),
    ("Pagella",        f"{HOME}/texgyrepagella-regular.otf"),
    ("Poetica",        f"{HOME}/Poetica Std Regular.otf"),
]


def holes(mask):
    """Background components of `mask` that do not touch the border, as boolean
    arrays -- a ring's counters. Flood fill from the border with a stack; no
    scipy on this box."""
    H, W = mask.shape
    bg = ~mask
    seen = np.zeros_like(bg)
    st = []
    for x in range(W):
        if bg[0, x]: st.append((0, x))
        if bg[H - 1, x]: st.append((H - 1, x))
    for y in range(H):
        if bg[y, 0]: st.append((y, 0))
        if bg[y, W - 1]: st.append((y, W - 1))
    for p in st: seen[p] = True
    while st:
        y, x = st.pop()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < H and 0 <= nx < W and bg[ny, nx] and not seen[ny, nx]:
                seen[ny, nx] = True; st.append((ny, nx))
    inner = bg & ~seen
    out = []
    lab = np.zeros(inner.shape, int); n = 0
    for y in range(H):
        for x in range(W):
            if inner[y, x] and not lab[y, x]:
                n += 1; st = [(y, x)]; lab[y, x] = n
                while st:
                    cy, cx = st.pop()
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < H and 0 <= nx < W and inner[ny, nx] and not lab[ny, nx]:
                            lab[ny, nx] = n; st.append((ny, nx))
    for i in range(1, n + 1):
        m = lab == i
        if m.sum() >= 40: out.append(m)
    out.sort(key=lambda m: -m.sum())
    return out


def _clock(cy, cx, y, x):
    """Clock hour (0..12, float) of pixel (y, x) about centre (cy, cx).
    Rows grow downward, so 12 o'clock is a SMALLER y."""
    dy, dx = (cy - y), (x - cx)          # y-up
    a = math.degrees(math.atan2(dx, dy)) % 360.0   # 0 = up = 12 o'clock, cw
    return a / 30.0


def profile(ttf, ch, px=520, slant=0.0, rings=None, bins=24):
    """Median stroke width by clock position, per ring, in DESIGN UNITS.

    `rings` None = one ring about the largest counter; 2 = split at the waist
    (the 8). Returns [(label, centre, {clock_bin: width_units}, counter_box)].
    """
    from fontTools.ttLib import TTFont
    f = TTFont(ttf); upm = f["head"].unitsPerEm
    try: sx = f["OS/2"].sxHeight or upm * 0.5
    except Exception: sx = upm * 0.5
    u_per_px = sx / px                                  # raster() sizes so x-height == px px
    mask, base, _ = raster(ttf, ch, slant, px)
    d = dist(mask)
    pts = ridge(mask, d)
    hs = holes(mask)
    if not hs: return []
    if rings == 2:
        if len(hs) < 2: return []
        hs = sorted(hs[:2], key=lambda m: -np.nonzero(m)[0].mean())   # lower first (larger row index)
        labels = ["lower", "upper"]
        y_lo = np.nonzero(hs[0])[0].min()     # top row of the lower counter
        y_up = np.nonzero(hs[1])[0].max()     # bottom row of the upper counter
        waist = (y_lo + y_up) / 2.0
        sel = [lambda p: p[0] > waist, lambda p: p[0] <= waist]
    else:
        hs = hs[:1]; labels = ["ring"]; sel = [lambda p: True]
    out = []
    for m, lab, keep in zip(hs, labels, sel):
        ys, xs = np.nonzero(m)
        cy, cx = ys.mean(), xs.mean()
        box = (xs.min() * u_per_px, ys.min() * u_per_px, xs.max() * u_per_px, ys.max() * u_per_px)
        b = {}
        for (y, x, v) in pts:
            if not keep((y, x)): continue
            h = _clock(cy, cx, y, x)
            k = int(h * bins / 12.0) % bins
            b.setdefault(k, []).append(2 * v * u_per_px)
        prof = {k: float(np.median(vs)) for k, vs in sorted(b.items()) if len(vs) >= 3}
        out.append((lab, (cy, cx), prof, box))
    return out


def peak(prof, n=4):
    """A ROBUST maximum: the median of the `n` heaviest clock bins.

    NOT `max(prof.values())`, and this cost a wrong reading first. The ridge's
    thickness is twice the inscribed-circle radius, and at a SQUARED corner a
    much larger circle fits than the wall is thick -- so raising the ring's
    superellipse exponent inflates one bin and nothing else. Measured on the
    roman 8: k 2.1 (today) peaks at 69, k 2.9 at 79 in a single bin whose
    neighbours read 72 and 69, k 4.0 at 114 with neighbours 71 and 94. Any
    "fraction of the figure's own peak" taken against that max reports the
    squarer ring as lighter at the diagonal when the diagonal has not moved.
    The median of the top four bins is immune: a corner occupies one or two."""
    v = sorted(prof.values())[-n:]
    return float(np.median(v)) if v else float("nan")


def at(prof, hour, bins=24, half=0.75):
    """Median width over a window of +/- `half` hours about `hour`."""
    vals = []
    for k, v in prof.items():
        h = k * 12.0 / bins
        dh = min(abs(h - hour), 12 - abs(h - hour))
        if dh <= half: vals.append(v)
    return float(np.median(vals)) if vals else float("nan")


def show(name, rows, bins=24):
    for lab, c, prof, box in rows:
        if not prof: continue
        ks = sorted(prof)
        print(f"  {name:22s} {lab:6s}  counter {box[2]-box[0]:5.0f} x {box[3]-box[1]:5.0f} u")
        print("     clock " + " ".join(f"{k*12/bins:5.1f}" for k in ks))
        print("     width " + " ".join(f"{prof[k]:5.0f}" for k in ks))
        tn = min(prof, key=prof.get); tk = max(prof, key=prof.get)
        print(f"     thin at {tn*12/bins:4.1f} o'clock ({prof[tn]:.0f}u), "
              f"thick at {tk*12/bins:4.1f} ({prof[tk]:.0f}u), robust peak {peak(prof):.0f}u, "
              f"contrast {peak(prof)/prof[tn]:.2f}:1")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ttf", action="append", default=[])
    ap.add_argument("--label", action="append", default=[])
    ap.add_argument("--slant", type=float, default=0.0)
    ap.add_argument("--chars", default="80690oO")
    ap.add_argument("--px", type=int, default=520)
    ap.add_argument("--refs", action="store_true")
    ap.add_argument("--json", default=None)
    a = ap.parse_args()
    subs = [(a.label[i] if i < len(a.label) else os.path.basename(t), t, a.slant)
            for i, t in enumerate(a.ttf)]
    if a.refs: subs += [(n, p, 0.0) for n, p in REF_ROMANS if os.path.exists(p)]
    blob = {}
    for name, t, sl in subs:
        print(f"\n{name}   ({t})")
        for ch in a.chars:
            rows = profile(t, ch, a.px, sl, rings=2 if ch == "8" else None)
            show(f"'{ch}'", rows)
            for lab, c, prof, box in rows:
                blob.setdefault(name, {})[f"{ch}:{lab}"] = {
                    "prof": {str(k): v for k, v in prof.items()},
                    "counter_w": box[2] - box[0], "counter_h": box[3] - box[1]}
    if a.json:
        json.dump(blob, open(a.json, "w"), indent=1)
        print("\nwrote", a.json)


if __name__ == "__main__":
    main()
