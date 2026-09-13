"""The hand-cut linear outline (round 17/18, kept by ruling): one vertex in
four on every contour, seed 73, no jitter -- applied LAST, to the finished
designed outline. Every CORNER is kept (a turn sharper than CORNER_DEG:
wedge apexes, end faces, the junction points a union makes), so the cut
facets curves and never chamfers a corner. Contours are cut in glyph order
with one running phase counter, as pen_linear did."""
import math, random
CORNER_DEG = 20.0

def corners(pts, deg=CORNER_DEG):
    n = len(pts); out = set(); c = math.cos(math.radians(deg))
    for i in range(n):
        a, b, d = pts[i - 1], pts[i], pts[(i + 1) % n]
        ux, uy = b[0] - a[0], b[1] - a[1]; vx, vy = d[0] - b[0], d[1] - b[1]
        lu = math.hypot(ux, uy) or 1; lv = math.hypot(vx, vy) or 1
        if (ux * vx + uy * vy) / (lu * lv) < c: out.add(i)
    return out

class Cutter:
    def __init__(self, seed=73, every=4):
        self.seed = seed; self.every = every; self.n = 0
    def __call__(self, pts):
        rng = random.Random(self.seed * 7919 + self.n); self.n += 1
        ph = rng.randrange(self.every); keep = corners(pts)
        out = [p for i, p in enumerate(pts) if (i + ph) % self.every == 0 or i in keep]
        return out if len(out) >= 3 else list(pts)
