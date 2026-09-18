"""Legibility of the italic 7 at reading sizes.

RASTERISATION IS OURS, not PIL's text(). PIL floors a float xy, so a sub-pixel
offset passed to ImageDraw.text() moves nothing -- measured: the ink sum is
identical at ox 0.00 / 0.33 / 0.66. Every per-pixel measure here is sensitive
to which phase of the grid the stroke lands on, so the phase has to be real:
the outline is filled at 16x and box-downsampled, which is coverage AA -- what
the panel's 4-level path does -- and the offset is applied in the supersample
grid where it means something.

Five numbers, each naming a way the figure actually fails on a panel:
  leg_min   the darkest pixel in the WEAKEST row of the lower stroke, 0..1.
            Low = the leg greys out and the 7 loses its diagonal.
  leg_mass  mean ink per row down the lower stroke -- how much stroke is there.
  aperture  the whitest the notch under the bar gets. Low = the top-right
            corner clots and the 7 reads as a blob.
  d1        1 - normalised correlation against the '1' at the same size.
            Low = 7 and 1 converge.
  ink7/ink6 ink fraction against the 6, at a size where the grid cannot lie.
"""
import sys, numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from PIL import Image, ImageDraw

SS = 16                       # supersample factor
PHASES = [(dx / 4.0, dy / 4.0) for dx in range(4) for dy in range(4)]

def contours(path, ch):
    f = TTFont(path); cmap = f.getBestCmap(); gs = f.getGlyphSet()
    pen = RecordingPen(); gs[cmap[ord(ch)]].draw(pen)
    upm = f['head'].unitsPerEm
    polys, cur = [], []
    def quad(p0, p1, p2, n=8):
        return [((1-t)**2*p0[0] + 2*(1-t)*t*p1[0] + t*t*p2[0],
                 (1-t)**2*p0[1] + 2*(1-t)*t*p1[1] + t*t*p2[1])
                for t in [i/n for i in range(1, n+1)]]
    def cube(p0, p1, p2, p3, n=10):
        return [((1-t)**3*p0[0] + 3*(1-t)**2*t*p1[0] + 3*(1-t)*t*t*p2[0] + t**3*p3[0],
                 (1-t)**3*p0[1] + 3*(1-t)**2*t*p1[1] + 3*(1-t)*t*t*p2[1] + t**3*p3[1])
                for t in [i/n for i in range(1, n+1)]]
    for op, args in pen.value:
        if op == 'moveTo': cur = [args[0]]
        elif op == 'lineTo': cur.append(args[0])
        elif op == 'qCurveTo':
            pts = list(args); on = pts[-1]
            if on is None:                       # implied on-curve points
                pts = pts[:-1]
                for i in range(len(pts) - 1):
                    mid = ((pts[i][0]+pts[i+1][0])/2, (pts[i][1]+pts[i+1][1])/2)
                    cur += quad(cur[-1], pts[i], mid)
                cur += quad(cur[-1], pts[-1], cur[0])
            else:
                for i in range(len(pts) - 2):
                    mid = ((pts[i][0]+pts[i+1][0])/2, (pts[i][1]+pts[i+1][1])/2)
                    cur += quad(cur[-1], pts[i], mid)
                cur += quad(cur[-1], pts[-2], on)
        elif op == 'curveTo':
            pts = list(args)
            cur += cube(cur[-1], pts[0], pts[1], pts[2])
        elif op in ('closePath', 'endPath'):
            if len(cur) > 2: polys.append(cur)
            cur = []
    if len(cur) > 2: polys.append(cur)
    return polys, upm

def raster(path, ch, px, ox=0.0, oy=0.0, pad=3, _cache={}):
    key = (path, ch)
    if key not in _cache: _cache[key] = contours(path, ch)
    polys, upm = _cache[key]
    s = px * SS / upm
    xs = [p[0] for c in polys for p in c]; ys = [p[1] for c in polys for p in c]
    x0, y1 = min(xs), max(ys)
    W = int((max(xs) - x0) * s) + 2 * pad * SS + SS
    H = int((y1 - min(ys)) * s) + 2 * pad * SS + SS
    im = Image.new("L", (W, H), 0); d = ImageDraw.Draw(im)
    dx = pad * SS + ox * SS; dy = pad * SS + oy * SS
    # even-odd via XOR: fill each contour, xor into the accumulator
    acc = np.zeros((H, W), dtype=bool)
    for c in polys:
        im2 = Image.new("L", (W, H), 0)
        ImageDraw.Draw(im2).polygon([((p[0]-x0)*s + dx, (y1-p[1])*s + dy) for p in c], fill=255)
        acc ^= np.asarray(im2) > 127
    a = acc.astype(float)
    h = (H // SS) * SS; w = (W // SS) * SS
    return a[:h, :w].reshape(h//SS, SS, w//SS, SS).mean(axis=(1, 3))

def crop_ink(a, t=0.12):
    ys, xs = np.nonzero(a > t)
    return a[ys.min():ys.max()+1, xs.min():xs.max()+1]

def _one(path, px, ox, oy):
    a = crop_ink(raster(path, "7", px, ox, oy))
    H, W = a.shape
    lo = a[int(H * 0.35):, :]
    leg_min = float(lo.max(axis=1).min())
    leg_mass = float(lo.sum() / lo.shape[0])
    top = a[:max(2, int(H * 0.30)), :]
    ap = []
    for r in top:
        idx = np.nonzero(r > 0.12)[0]
        if len(idx) < 2: continue
        ap.append(1.0 - r[idx.min():idx.max()+1].min())
    aperture = float(max(ap)) if ap else 0.0
    b = crop_ink(raster(path, "1", px, ox, oy))
    h = max(a.shape[0], b.shape[0]); w = max(a.shape[1], b.shape[1])
    A = np.zeros((h, w)); A[:a.shape[0], :a.shape[1]] = a
    B = np.zeros((h, w)); B[:b.shape[0], :b.shape[1]] = b
    den = float(np.sqrt((A*A).sum() * (B*B).sum())) or 1.0
    return leg_min, leg_mass, aperture, 1.0 - float((A*B).sum()) / den

def measure(path, px):
    acc = np.zeros(4)
    for ox, oy in PHASES: acc += np.array(_one(path, px, ox, oy))
    return acc / len(PHASES)

def ink(path, ch, px=240):
    a = raster(path, ch, px)
    return float(a.sum())

if __name__ == "__main__":
    hdr = "  ".join(f"{p}px legmin  mass  aper    d1" for p in (13, 17))
    print(f"{'arm':4s} {'bar/diag':11s} {hdr}   ink7/ink6")
    for spec in sys.argv[1:]:
        name, path, label = spec.split("=", 2)
        cols = []
        for px in (13, 17):
            lm, mass, ap, d1 = measure(path, px)
            cols.append(f"{lm:6.3f} {mass:5.2f} {ap:5.2f} {d1:5.3f}")
        r = ink(path, "7") / ink(path, "6")
        print(f"{name:4s} {label:11s}  " + "   ".join(cols) + f"    {r:6.3f}")
