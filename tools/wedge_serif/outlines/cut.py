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
    def phase(self):
        """The next contour's decimation phase (consumes the running counter)."""
        rng = random.Random(self.seed * 7919 + self.n); self.n += 1
        return rng.randrange(self.every)
    def plan(self, pts, ph=None):
        """The kept indices for a contour: every `every`-th from the phase, plus its corners."""
        if ph is None: ph = self.phase()
        keep = corners(pts)
        return sorted(i for i in range(len(pts)) if (i + ph) % self.every == 0 or i in keep)
    def __call__(self, pts):
        keep = self.plan(pts)
        out = [pts[i] for i in keep]
        return out if len(out) >= 3 else list(pts)

def project(pts, keep):
    """The cut as a DISPLACEMENT: every point not kept is moved onto the
    chord between its neighbouring kept points, so the polygon renders as
    the decimated one while keeping every point -- the form a variable
    font's masters need (same point count at every cut)."""
    n = len(pts)
    if len(keep) < 3: return list(pts)
    out = list(pts); ks = sorted(keep)
    for a, b in zip(ks, ks[1:] + [ks[0] + n]):
        pa = pts[a % n]; pb = pts[b % n]; span = b - a
        for j in range(a + 1, b):
            t = (j - a) / span; out[j % n] = (pa[0] + (pb[0] - pa[0]) * t, pa[1] + (pb[1] - pa[1]) * t)
    return out


def blend(pts, ph, amount, every=4):
    """The cut as a continuous AMOUNT on the dense point set (round 62):
    0 = the dense outline untouched, 100 = every point projected onto its
    1-in-`every` chords (the shipping cut of rounds 17-61), 200 = the same
    seed's 1-in-(2 every) chords (facets twice as long), and any value
    between a linear blend of the two neighbouring projections point by
    point. Corners are always kept. Same point count at every amount --
    the form the static builder and the variable font now share."""
    a = amount / 100.0
    if a <= 0.0: return list(pts)
    n = len(pts); c = corners(pts)
    p4 = project(pts, sorted(set(i for i in range(n) if (i + ph) % every == 0) | c))
    if a <= 1.0:
        return [(p[0] + (q[0] - p[0]) * a, p[1] + (q[1] - p[1]) * a) for p, q in zip(pts, p4)]
    p8 = project(pts, sorted(set(i for i in range(n) if (i + ph) % (2 * every) == 0) | c))
    b = min(1.0, a - 1.0)
    return [(p[0] + (q[0] - p[0]) * b, p[1] + (q[1] - p[1]) * b) for p, q in zip(p4, p8)]
