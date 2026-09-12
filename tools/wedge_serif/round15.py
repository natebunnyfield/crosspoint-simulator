"""Round 15: seed 73, clean. Owner 2026-09-12: 'seed 73 and let's make
several versions that do not have any gaps or stray marks. let's resize o
and other letters to match garamond better. adjust g and any other
characters to have a less distracting overlap area (counterpunch inspired)'.

Gaps and strays had two mechanical causes: decimating a five-point serif
polygon to two or three points makes a spike or a sliver, and jitter moves a
serif off its stem. The clean cutter leaves small polygons undecimated and
lightly jittered, grows every polygon a few units after the cut so joins
re-close, and drops any polygon whose area is below a stray threshold.
Garamond widths: width 1.0 and n_width 380 on the B5.9 design (o ~450 wide
against an x-height of 415, the n's ink ~437), matching Adobe Garamond's
proportions. The drawing itself changed in alphabet2: bowls of b d p q end
inside their stems; the g's stem starts at 0.42 x-height with a short ear."""
import math, os, random, sys, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import round12, round14
from round12 import V, decimate, jitter, offset_naive, signed_area
from fontTools.ttLib import TTFont

GARAMOND = dict(width=1.0, n_width=380)

class CleanCut(round14.Cut):
    def __init__(self, font_seed, every=4, amp=3.0, grow=3.0, hand=True, small=20, stray=350.0):
        super().__init__(font_seed, every, amp); self.grow = grow; self.hand = hand; self.small = small; self.stray = stray
    def __call__(self, polys, c):
        rng = random.Random(self.font_seed * 1000 + self.n); self.n += 1
        amp = self.amp * rng.uniform(0.8, 1.2); out = []
        for p in polys:
            if len(p) < self.small:   # a serif, an ear, a dot: never decimated, barely moved,
                # one rounding pass so a jittered apex is a wedge tip, not a hair
                q = round12.chaikin(jitter(p, amp * 0.3, rng.randrange(1 << 30)), 1)
                q = offset_naive(q, self.grow * 0.6)
            else:
                q = jitter(round14.decimate_phase(p, self.every, rng.randrange(self.every)), amp, rng.randrange(1 << 30))
            q = offset_naive(q, self.grow)  # re-close the joins the cut opened
            if abs(signed_area(q)) >= self.stray: out.append(q)
        return round14.hand(out, rng) if self.hand else out

BANK = [
 V("V23a-73c1", "Seed 73, clean, fine", "one in four, jitter 3, grown 3", post=CleanCut(73, 4, 3.0, 3.0), over=GARAMOND),
 V("V23a-73c2", "Seed 73, clean, finer", "one in four, jitter 2, grown 2", post=CleanCut(73, 4, 2.0, 2.0), over=GARAMOND),
 V("V23a-73c3", "Seed 73, clean, medium", "one in five, jitter 4, grown 3", post=CleanCut(73, 5, 4.0, 3.0), over=GARAMOND),
 V("V23a-73c4", "Seed 73, clean, facets", "one in six, jitter 3, grown 4", post=CleanCut(73, 6, 3.0, 4.0), over=GARAMOND),
 V("V23a-73c5", "Seed 73, clean, steady hand", "one in four, jitter 3, grown 3, no scale or tilt per glyph", post=CleanCut(73, 4, 3.0, 3.0, hand=False), over=GARAMOND),
 V("V23a-73c6", "Seed 73, clean, heavier", "one in four, jitter 3, grown 3, stem 90", post=CleanCut(73, 4, 3.0, 3.0), over=dict(GARAMOND, stem=90)),
]

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
    os.makedirs(out, exist_ok=True)
    paths = [round12.build(v, out) for v in BANK]
    for pth in paths: TTFont(pth)
    round12.BANK = BANK
    html = round12.page(paths).replace("<title>Fjord Font Files</title>", "<title>Seed 73, Clean</title>").replace("<h1>Fjord Font Files</h1>", "<h1>Seed 73, Clean</h1>")
    html = html.replace("Round 12. Twenty-six TrueType files from the B5.9 design, one per technique, all vector: pen models and outline operations, no raster.",
                        "Round 15. Seed 73 cut six ways with no gaps or stray marks: serifs are never decimated, every polygon is grown a few units after the cut so joins re-close, slivers are dropped. Letters at Garamond widths (o about 450 on an x-height of 415), bowls ending inside their stems, a quieter g. Six TrueType files.")
    open(os.path.join(out, "fjord-seed73.html"), "w").write(html)
    with zipfile.ZipFile(os.path.join(out, "fjord-seed73.zip"), "w", zipfile.ZIP_DEFLATED) as z:
        for pth in paths: z.write(pth, os.path.basename(pth))
    print("ok", len(paths))
