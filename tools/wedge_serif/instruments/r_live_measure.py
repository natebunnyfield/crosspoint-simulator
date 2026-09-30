# live_rm.py -- rmatch's glyph-only numbers from the LIVE builder (asdf python, no scipy):
# term / hang exactly as rmatch.term takes them (1 px per unit, the bitmap's own width, a 3-4
# chamfer standing in for the Euclidean transform), and cut as cmp_weight_survey takes it.
import sys, os, math
sys.path.insert(0, os.getcwd())
import numpy as np
from PIL import Image, ImageDraw
from outlines import build
import cmp_weight_survey as W
xg = build.draw('x'); xh = xg.bounds[3] - max(0, xg.bounds[1])
g = build.draw('r'); x0, y0, x1, y1 = g.bounds
polys = [g] if g.geom_type == 'Polygon' else list(g.geoms)
Wd = int(math.ceil(x1 - x0)) + 2; Ht = int(math.ceil(y1 - y0)) + 2
im = Image.new("L", (Wd, Ht), 0); d = ImageDraw.Draw(im)
def tx(p): return (p[0] - x0, y1 - p[1])
for P in polys:
    d.polygon([tx(p) for p in P.exterior.coords], fill=255)
    for h in P.interiors: d.polygon([tx(p) for p in h.coords], fill=0)
a = np.asarray(im) > 127
m = np.pad(a, 2); dt = W.chamfer(m)[2:-2, 2:-2]
Y = (y1 - np.arange(Ht))[:, None]; X = np.arange(Wd)[None, :]
inkw = x1 - x0
term = 2 * dt[(Y > 0.55 * xh) & (X > 0.55 * inkw) & a].max()
stem = 2 * dt[(Y < 0.45 * xh) & (Y > 0.1 * xh) & a].max()
rq = a & (X > 0.75 * inkw) & (Y > 0.4 * xh)
hang = Y[rq.any(1)].min() / xh
# cut, survey method (unsheared, sxHeight 429 -> 380 px)
k = math.tan(math.radians(13)); s = 380 / 429.0
Wd2 = int((x1 - x0 + 400) * s); Ht2 = int((y1 - y0 + 200) * s)
im2 = Image.new("L", (Wd2, Ht2), 0); d2 = ImageDraw.Draw(im2)
def tx2(p): return ((p[0] - p[1] * k - x0 + 200) * s, (y1 + 100 - p[1]) * s)
for P in polys:
    d2.polygon([tx2(p) for p in P.exterior.coords], fill=255)
    for h in P.interiors: d2.polygon([tx2(p) for p in h.coords], fill=0)
m2 = np.asarray(im2) > 127
ys, xs = np.nonzero(m2); m2 = m2[max(0, ys.min() - 48):ys.max() + 49, max(0, xs.min() - 48):xs.max() + 49]
v = W.ridge_vals(m2, W.chamfer(m2)); t = 2.0 * v * (W.XH / 380)
print(f"{os.environ.get('LBL',''):14s} f/s {term/stem:.2f} term {1000*term/xh:4.0f} hang {hang:.2f} cut {np.percentile(t,90)/np.percentile(t,10):.2f} top {y1:.0f} right {x1:.0f}")
