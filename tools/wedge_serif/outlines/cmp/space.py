"""The space inside and between characters (owner's standing rule), measured
on a built TTF: the o's counter against the 1.036 ruling, the n counter at
mid x-height, the word space, the sidebearings of n o H O, and on the 54 px
four-level render the smallest enclosed counter (white pixels surviving)
and the narrowest aperture (the square dilation radius at which an open
counter seals).

    cd tools/wedge_serif && PYTHON_GIL=0 python3 -m outlines.cmp.space A.ttf [B.ttf]
"""
import sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from fontTools.ttLib import TTFont
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import round19
from .proof import eink

O_RULING = 1.036   # round 35: the o's counter, width over height

def contours_of(font, gn):
    g = font["glyf"][gn]; cs = []
    if g.numberOfContours <= 0: return cs
    co = list(g.coordinates); s = 0
    for e in g.endPtsOfContours: cs.append([(float(x), float(y)) for x, y in co[s:e + 1]]); s = e + 1
    return cs

def area(pts):
    return 0.5 * sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]))

def gname(font, ch):
    return font["cmap"].getBestCmap()[ord(ch)]

def o_counter(font):
    cs = contours_of(font, gname(font, "o"))
    hole = min(cs, key=lambda c: abs(area(c)))
    xs = [p[0] for p in hole]; ys = [p[1] for p in hole]
    return max(xs) - min(xs), max(ys) - min(ys)

def crossings(pts, y):
    """x of every crossing of the closed polyline with the horizontal line y."""
    out = []
    for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
        if (y0 <= y) != (y1 <= y): out.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
    return sorted(out)

def n_counter(font):
    xh = font["OS/2"].sxHeight; cs = contours_of(font, gname(font, "n"))
    outer = max(cs, key=lambda c: abs(area(c))); xs = crossings(outer, xh * 0.5)
    # even-odd: xs pairs off as ink spans; the counter is the widest paper gap
    # between them (the cut's notches add crossings a few units apart at the edges)
    gaps = [xs[i + 1] - xs[i] for i in range(1, len(xs) - 1, 2)]
    return max(gaps) if gaps else None

def bearings(font, ch):
    gn = gname(font, ch); adv, lsb = font["hmtx"][gn]; g = font["glyf"][gn]
    return adv, lsb, adv - g.xMax

def metrics(path):
    f = TTFont(path); w, h = o_counter(f)
    return dict(o_counter=(w, h, w / h), n_counter=n_counter(f), space=f["hmtx"]["space"][0],
                bearings={ch: bearings(f, ch) for ch in "noHO"}, xh=f["OS/2"].sxHeight)

# ---------------------------------------------------------------- at 54 px, four levels
INK = 96   # black and dark gray are ink; light gray and white are paper

def padded(im):
    p = Image.new("L", (im.size[0] + 4, im.size[1] + 4), 255); p.paste(im, (2, 2)); return p

def exterior(a):
    """Mask of paper pixels connected to the border (4-connected flood)."""
    im = Image.fromarray(np.where(a > INK, 255, 0).astype(np.uint8)).copy()   # fromarray is a read-only view: floodfill writes nothing into it
    ImageDraw.floodfill(im, (0, 0), 128)
    return np.array(im) == 128

def enclosed_components(a):
    """[(white255 count, paper count)] for every paper region not connected to the border."""
    paper = a > INK; ext = exterior(a); inside = paper & ~ext
    im = Image.fromarray(np.where(inside, 0, 255).astype(np.uint8)).copy(); out = []
    ys, xs = np.nonzero(np.array(im) == 0)
    while len(ys):
        ImageDraw.floodfill(im, (int(xs[0]), int(ys[0])), 128); m = np.array(im) == 128
        if not m.any(): raise RuntimeError("floodfill wrote nothing")
        out.append((int((a[m] == 255).sum()), int(m.sum()))); im2 = np.array(im); im2[m] = 200; im = Image.fromarray(im2).copy()
        ys, xs = np.nonzero(np.array(im) == 0)
    return out

def seal_radius(a, rmax=12):
    """Smallest square dilation radius r (px) of the ink at which some paper
    that was connected to the outside is sealed off (>= 3 px): the narrowest
    aperture is about 2r px. None if nothing seals by rmax."""
    ext0 = exterior(a); im = Image.fromarray(a).copy()
    for r in range(1, rmax + 1):
        d = np.array(im.filter(ImageFilter.MinFilter(2 * r + 1)))
        ext = exterior(d); sealed = ext0 & ~ext & (d > INK)
        if sealed.sum() >= 3: return r
    return None

def render_report(path, chars=None):
    chars = chars or [c for c in round19.CHARS if c.strip()]
    counters = []; apertures = []
    for ch in chars:
        a = np.array(padded(eink(path, ch, width=140)))
        for w255, n in enclosed_components(a): counters.append((w255, n, ch))
        r = seal_radius(a)
        if r is not None: apertures.append((r, ch))
    counters.sort(); apertures.sort()
    return counters, apertures

def describe(path, previous=None):
    m = metrics(path); lines = []
    w, h, r = m["o_counter"]; need = O_RULING * h - w
    lines.append(f"o counter {w:.0f} x {h:.0f} = {r:.3f} wide over tall (ruling {O_RULING}); " + (f"{need:+.0f} units of counter width would restore it ({need / TTFont(path)['hmtx'][gname(TTFont(path), 'o')][0] * 100:+.1f}% of the o's advance)" if abs(r - O_RULING) > 0.005 else "on the ruling"))
    lines.append(f"n counter at mid x-height {m['n_counter']:.0f}; word space {m['space']}; sidebearings (adv, lsb, rsb): " + ", ".join(f"{ch} {a} {l:.0f} {rr:.0f}" for ch, (a, l, rr) in m["bearings"].items()))
    if previous and os.path.exists(previous):
        p = metrics(previous); pw, ph, pr = p["o_counter"]
        lines.append(f"against {os.path.basename(previous)}: o counter {pw:.0f} x {ph:.0f} = {pr:.3f}; n counter {p['n_counter']:.0f}; word space {p['space']}; " + ", ".join(f"{ch} {a} {l:.0f} {rr:.0f}" for ch, (a, l, rr) in p["bearings"].items()))
    counters, apertures = render_report(path)
    lines.append("54 px four-level render, enclosed counters by white pixels surviving (white / any paper): " + ", ".join(f"{ch} {w}/{n}" for w, n, ch in counters[:8]) + f"; largest {counters[-1][2]} {counters[-1][0]}/{counters[-1][1]}")
    lines.append("narrowest apertures (square dilation radius that seals an open counter; gap about 2r px): " + ", ".join(f"{ch} r{r}" for r, ch in apertures[:10]))
    return lines, m, counters, apertures

if __name__ == "__main__":
    for l in describe(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)[0]: print(l)
