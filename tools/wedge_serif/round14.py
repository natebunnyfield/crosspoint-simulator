"""Round 14: V23a (Scissors, fine) cut from scratch six times. Owner
2026-09-12: 'remake the characters from scratch in v23a six times so I can
see what is possible. I need versions without identical defects.' Round 13
seeded the jitter by polygon index, so the same glyph got the same snips in
every file. Here every FONT has its own seed, every GLYPH its own stream,
the decimation starts at a random phase, and each glyph gets a hand's
variation (a little scale, a little tilt) so the six are six cuts."""
import math, os, random, sys, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import round12
from round12 import V, decimate, jitter
from fontTools.ttLib import TTFont

def decimate_phase(poly, every, phase):
    keep = [p for i, p in enumerate(poly) if (i + phase) % every == 0]
    return keep if len(keep) >= 3 else poly

def hand(polys, rng, scale=0.015, tilt_deg=0.6):
    s = 1 + rng.uniform(-scale, scale); a = math.radians(rng.uniform(-tilt_deg, tilt_deg))
    xs = [x for p in polys for (x, y) in p]; cx = (min(xs) + max(xs)) / 2
    ca, sa = math.cos(a), math.sin(a)
    out = []
    for p in polys:
        q = []
        for x, y in p:
            dx, dy = (x - cx) * s, y * s
            q.append((cx + dx * ca - dy * sa, dx * sa + dy * ca))
        out.append(q)
    return out

class Cut:
    """A post op with per-glyph independent randomness: the glyph index is
    taken from a counter the builder advances glyph by glyph."""
    def __init__(self, font_seed, every=4, amp=4.0):
        self.font_seed = font_seed; self.every = every; self.amp = amp; self.n = 0
    def __call__(self, polys, c):
        rng = random.Random(self.font_seed * 1000 + self.n); self.n += 1
        amp = self.amp * rng.uniform(0.7, 1.3)
        out = [jitter(decimate_phase(p, self.every, rng.randrange(self.every)), amp, rng.randrange(1 << 30)) for p in polys]
        return hand(out, rng)

BANK = [V(f"V23a-{i}", f"Scissors, cut {i}", f"font seed {seed}: its own snips, its own hand", post=Cut(seed))
        for i, seed in enumerate((11, 23, 37, 41, 59, 73), 1)]

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
    os.makedirs(out, exist_ok=True)
    paths = [round12.build(v, out) for v in BANK]
    for pth in paths: TTFont(pth)
    round12.BANK = BANK
    html = round12.page(paths).replace("<title>Fjord Font Files</title>", "<title>Six Cuts of V23a</title>").replace("<h1>Fjord Font Files</h1>", "<h1>Six Cuts of V23a</h1>")
    html = html.replace("Round 12. Twenty-six TrueType files from the B5.9 design, one per technique, all vector: pen models and outline operations, no raster.",
                        "Round 14. V23a (Scissors, fine) cut from scratch six times: each file has its own seed, each glyph its own stream and its own hand, so no two share a defect. Six TrueType files.")
    open(os.path.join(out, "fjord-sixcuts.html"), "w").write(html)
    with zipfile.ZipFile(os.path.join(out, "fjord-sixcuts.zip"), "w", zipfile.ZIP_DEFLATED) as z:
        for pth in paths: z.write(pth, os.path.basename(pth))
    # proof that the defects differ: compare glyph 'a' coordinates across files
    from fontTools.ttLib import TTFont as T
    sig = [tuple(T(p)["glyf"]["a"].coordinates) for p in paths]
    print("ok", len(paths), "distinct 'a' outlines:", len(set(sig)))
