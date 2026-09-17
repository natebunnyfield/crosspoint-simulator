"""TRACE Coelacanth's g -- centreline and width, ring by ring, in Albo's units.

Owner 2026-09-17: *"trace g with an approved result."*

Not a bezier copy: what comes out is the STROKE -- where the pen's centre went
and how wide it was there -- which is the thing a width table was standing in
for. Coelacanth is OFL with the reserved name "Coelacanth"; a derivative under a
different name is permitted, and Albo is a different name.

METHOD. Rasterise the g unsheared at a known x-height. Distance-transform the
ink; the ridge is the pen's centreline and twice the distance is its width
there. Split the ridge by which counter it belongs to -- the letter's two
counters ARE its two rings -- and order each ring's samples by angle about its
own counter's centroid. That gives, for every 5 degrees: the centreline's radius
and the stroke's width. Scale into Albo's design units by x-height.

    PYTHON_GIL=0 python3 trace_g.py            # prints the traced tables
"""
import math, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
XH = 429.0


def raster(ttf, slant, px=600):
    from PIL import Image, ImageDraw, ImageFont
    from fontTools.ttLib import TTFont
    f = TTFont(ttf); upm = f["head"].unitsPerEm
    sx = f["OS/2"].sxHeight or upm * 0.5
    size = int(round(px * upm / sx)); W = H = size * 3; base = int(H * 0.62)
    im = Image.new("L", (W, H), 255)
    ImageDraw.Draw(im).text((W * 0.35, base), "g",
                            font=ImageFont.truetype(ttf, size), fill=0, anchor="ls")
    if abs(slant) > 0.05:
        k = math.tan(math.radians(slant))
        im = im.transform((W, H), Image.AFFINE, (1, k, -k * base, 0, 1, 0),
                          resample=Image.BICUBIC, fillcolor=255)
    a = np.asarray(im) < 128
    return a, base, px


def dist(mask):
    d = np.where(mask, 1e9, 0.0); H, W = d.shape
    for y in range(H):
        r = d[y].copy()
        if y: 
            up = d[y-1]; r = np.minimum(r, up + 1.0)
            r[1:] = np.minimum(r[1:], up[:-1] + 1.414); r[:-1] = np.minimum(r[:-1], up[1:] + 1.414)
        for x in range(1, W):
            if r[x] > r[x-1] + 1.0: r[x] = r[x-1] + 1.0
        for x in range(W-2, -1, -1):
            if r[x] > r[x+1] + 1.0: r[x] = r[x+1] + 1.0
        d[y] = r
    for y in range(H-2, -1, -1):
        r = d[y].copy(); dn = d[y+1]; r = np.minimum(r, dn + 1.0)
        r[1:] = np.minimum(r[1:], dn[:-1] + 1.414); r[:-1] = np.minimum(r[:-1], dn[1:] + 1.414)
        for x in range(1, W):
            if r[x] > r[x-1] + 1.0: r[x] = r[x-1] + 1.0
        for x in range(W-2, -1, -1):
            if r[x] > r[x+1] + 1.0: r[x] = r[x+1] + 1.0
        d[y] = r
    return d


def counters(mask):
    """The enclosed white regions, largest first, as (cy, cx, pixels)."""
    H, W = mask.shape; white = ~mask
    bg = np.zeros_like(white); st = []
    for x in range(W):
        for y in (0, H-1):
            if white[y, x] and not bg[y, x]: bg[y, x] = True; st.append((y, x))
    for y in range(H):
        for x in (0, W-1):
            if white[y, x] and not bg[y, x]: bg[y, x] = True; st.append((y, x))
    while st:
        y, x = st.pop()
        for dy, dx in ((1,0),(-1,0),(0,1),(0,-1)):
            ny, nx = y+dy, x+dx
            if 0 <= ny < H and 0 <= nx < W and white[ny, nx] and not bg[ny, nx]:
                bg[ny, nx] = True; st.append((ny, nx))
    hole = white & ~bg
    seen = np.zeros_like(hole); out = []
    ys, xs = np.nonzero(hole)
    for sy, sx in zip(ys, xs):
        if seen[sy, sx]: continue
        st = [(sy, sx)]; seen[sy, sx] = True; g = []
        while st:
            y, x = st.pop(); g.append((y, x))
            for dy, dx in ((1,0),(-1,0),(0,1),(0,-1)):
                ny, nx = y+dy, x+dx
                if 0 <= ny < H and 0 <= nx < W and hole[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True; st.append((ny, nx))
        if len(g) > 200: out.append(g)
    out.sort(key=len, reverse=True)
    return out


def ridge(mask, d, floor=1.5):
    H, W = d.shape; out = []
    for y in range(1, H-1):
        for x in range(1, W-1):
            if not mask[y, x] or d[y, x] < floor: continue
            v = d[y, x]
            if v >= d[y, x-1] and v >= d[y, x+1] and v >= d[y-1, x] and v >= d[y+1, x]:
                out.append((y, x, v))
    return out


def trace(ttf, slant, px=600, step=10):
    mask, base, px = raster(ttf, slant, px)
    d = dist(mask)
    rg = ridge(mask, d)
    cs = counters(mask)
    if len(cs) < 2: return None
    info = []
    for g in cs[:2]:
        gy = np.array([p[0] for p in g]); gx = np.array([p[1] for p in g])
        info.append((gy.mean(), gx.mean(), gy.min(), gy.max(), gx.min(), gx.max()))
    info.sort()                       # topmost first = the bowl
    u = XH / px                       # px -> Albo design units
    out = {}
    for name, (cy, cx, y0, y1, x0, x1) in zip(("bowl", "loop"), info):
        # a ridge sample belongs to this ring if it is nearer this counter's
        # centroid than the other's, in units of that counter's own radius
        rad = ((y1 - y0) + (x1 - x0)) / 4.0
        oth = info[1] if name == "bowl" else info[0]
        orad = ((oth[3] - oth[2]) + (oth[5] - oth[4])) / 4.0
        bins = {}
        for y, x, v in rg:
            dm = math.hypot(y - cy, x - cx) / rad
            do = math.hypot(y - oth[0], x - oth[1]) / orad
            if dm > do or dm > 2.2: continue
            a = math.degrees(math.atan2(-(y - cy), x - cx)) % 360
            b = int(a // step) * step
            bins.setdefault(b, []).append((math.hypot(y - cy, x - cx), 2 * v))
        prof = {}
        for b, vs in sorted(bins.items()):
            r = float(np.median([p[0] for p in vs]))
            w = float(np.median([p[1] for p in vs]))
            prof[b] = (r * u, w * u)
        out[name] = dict(cx=(cx) * u, cy=(base - cy) * u,
                         rx=(x1 - x0) / 2 * u, ry=(y1 - y0) / 2 * u, prof=prof)
    return out


if __name__ == "__main__":
    import refs_registry as RR
    t = trace(RR.path("Coelacanth"), RR.slant("Coelacanth"))
    for name in ("bowl", "loop"):
        r = t[name]
        print(f"\n  COELACANTH {name.upper()}   counter {2*r['rx']:.0f} x {2*r['ry']:.0f} units,"
              f" centre {r['cy']:.0f} above the baseline")
        print("    deg " + " ".join(f"{b:>5}" for b in r["prof"]))
        print("    rad " + " ".join(f"{v[0]:5.0f}" for v in r["prof"].values()))
        print("    wid " + " ".join(f"{v[1]:5.0f}" for v in r["prof"].values()))
