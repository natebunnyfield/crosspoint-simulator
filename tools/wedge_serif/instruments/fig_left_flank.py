"""The OUTER LEFT silhouette of a round figure, row by row, as rendered.

Owner 2026-09-23 on the italic 9: *"fix 9 awkward left outside curve and
counter"*. "Awkward" is a property of the SILHOUETTE -- the edge you read as an
outline -- so this measures the leftmost ink in each scanline over the bowl's
own rows and reports how far that edge departs from a smooth curve.

A pen-drawn bowl's left edge is CONVEX and monotone: it moves left as it
descends to the bowl's widest row and right again below it, with the turn
happening once. Two things make it awkward and both are measured here:
  REVERSALS -- the number of times the edge changes direction beyond noise.
    One is correct (the widest row). More than one is a wobble.
  RESIDUAL -- the largest departure, in design units, from a quadratic fitted
    through the same rows. A true arc leaves a parabola by a unit or two.
"""
import sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont


def rows(ttf, ch, px=600):
    f = TTFont(ttf); upm = f["head"].unitsPerEm
    sx = (f["OS/2"].sxHeight or upm * 0.5)
    size = int(round(px * upm / sx)); W = H = size * 3; base = int(H * 0.62)
    im = Image.new("L", (W, H), 255)
    ImageDraw.Draw(im).text((W * 0.35, base), ch, font=ImageFont.truetype(ttf, size), fill=0, anchor="ls")
    a = np.asarray(im) < 128
    ys, xs = np.nonzero(a)
    return a, sx / px, ys.min(), ys.max()


def counter_rows(a, y0, y1):
    """The row range of the glyph's largest enclosed white region -- the BOWL.

    THIS IS WHY THE FIRST CUT WAS WRONG. Measuring the leftmost ink over the
    9's whole height reads the TAIL, which descends to the left: every face
    then reports two reversals and a huge residual (Flanker 303 units), and the
    number says nothing about the bowl. The bowl is the part that has a
    counter, so the counter's own rows are the honest window."""
    H_, W_ = a.shape
    bg = ~a
    seen = np.zeros_like(bg); st = []
    for x in range(W_):
        if bg[0, x]: st.append((0, x))
        if bg[H_-1, x]: st.append((H_-1, x))
    for y in range(H_):
        if bg[y, 0]: st.append((y, 0))
        if bg[y, W_-1]: st.append((y, W_-1))
    for q in st: seen[q] = True
    while st:
        y, x = st.pop()
        for dy, dx in ((1,0),(-1,0),(0,1),(0,-1)):
            ny, nx = y+dy, x+dx
            if 0 <= ny < H_ and 0 <= nx < W_ and bg[ny,nx] and not seen[ny,nx]:
                seen[ny,nx] = True; st.append((ny,nx))
    inner = bg & ~seen
    lab = np.zeros(inner.shape, int); n = 0; best = None
    for y in range(H_):
        for x in range(W_):
            if inner[y,x] and not lab[y,x]:
                n += 1; st=[(y,x)]; lab[y,x]=n; cnt=0
                while st:
                    cy,cx = st.pop(); cnt += 1
                    for dy,dx in ((1,0),(-1,0),(0,1),(0,-1)):
                        ny,nx = cy+dy,cx+dx
                        if 0<=ny<H_ and 0<=nx<W_ and inner[ny,nx] and not lab[ny,nx]:
                            lab[ny,nx]=n; st.append((ny,nx))
                if best is None or cnt > best[1]: best = (n, cnt)
    if best is None: return y0, y1
    ys = np.nonzero(lab == best[0])[0]
    return ys.min(), ys.max()


def flank(ttf, ch, lo=0.05, hi=0.95, px=600):
    """(units-per-px, [(y_frac_of_bowl, left_x_units)]) over the BOWL's rows."""
    a, u, y0, y1 = rows(ttf, ch, px)
    b0, b1 = counter_rows(a, y0, y1)
    H = b1 - b0
    out = []
    for y in range(b0, b1 + 1):
        xs = np.nonzero(a[y])[0]
        if not len(xs): continue
        fr = (b1 - y) / H
        if lo <= fr <= hi: out.append((fr, xs.min() * u))
    return u, out


def report(label, ttf, ch, lo=0.10, hi=0.90):
    u, pts = flank(ttf, ch, lo, hi)
    if len(pts) < 20: print(f"  {label:26s} '{ch}'  too few rows"); return
    f = np.array([p[0] for p in pts]); x = np.array([p[1] for p in pts])
    xs = np.convolve(x, np.ones(9) / 9, mode="same")[4:-4]; fs = f[4:-4]
    d = np.diff(xs)
    sign = np.sign(np.where(np.abs(d) < 0.35, 0, d))
    sign = sign[sign != 0]
    rev = int(np.sum(sign[1:] != sign[:-1]))
    c = np.polyfit(fs, xs, 2); res = xs - np.polyval(c, fs)
    print(f"  {label:26s} '{ch}'  reversals {rev:2d}   max residual from a parabola {np.abs(res).max():6.1f} u"
          f"   rms {np.sqrt((res**2).mean()):5.1f}   widest row at {fs[int(np.argmin(xs))]:.2f} of the height")
    return rev, float(np.abs(res).max())


if __name__ == "__main__":
    args = sys.argv[1:]
    chars = "960o"
    for a in args:
        lab, p = a.split("=", 1)
        for ch in chars:
            report(lab, p, ch)
        print()
