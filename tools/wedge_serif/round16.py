"""Round 16: V23a-73c5 with the HAIRLINE-THROUGHS addressed six ways, and
the e's bar connected. Owner 2026-09-12: 'address the gaps and
hairline-throughs. inktraps like the H crossbar are good but the crossbar
of the e needs to connect more. make six versions of how to address this.
we are making a text font here, not a display face.'

The mechanism: a stroke is one polygon (left side out, right side back).
Where a curve is tight, or after the scissors jitter a vertex, the two sides
fold over each other and the polygon crosses itself; under TrueType's
nonzero rule the folded part winds the other way and cancels: a white
hairline through the stroke. Cures, in six flavors: (a) cut the CENTERLINE
instead of the outline, then stroke it and emit overlapping quads, which
cannot cancel; (b) leave curves uncut; (c) grow; (d) pools of ink at the
joins. The e's bar now runs into both strokes in every version."""
import os, random, sys, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import round12, round14, round15, alphabet2 as A
from round12 import V, Multi, quadify, jitter, offset_naive, signed_area, chaikin
from fontTools.ttLib import TTFont

G = dict(round15.GARAMOND)
ORIG = round12.ORIG

def pen_centerline_cut(seed, every=4, amp=3.0, curves=True):
    """The scissors cut the DRAWING, not the ink: decimate and jitter the
    centerline, stroke it with the pen, emit overlapping quads. No polygon
    can cross itself, so no hairline can appear."""
    counter = [0]
    def outline(pts, pen, profile=None, cut0=None, cut1=None):
        rng = random.Random(seed * 7919 + counter[0]); counter[0] += 1
        xs = [x for x, y in pts]; ys = [y for x, y in pts]
        straight = (max(xs) - min(xs)) < 2 or (max(ys) - min(ys)) < 2
        if len(pts) >= 12 and (curves or straight):
            phase = rng.randrange(every)
            keep = [p for i, p in enumerate(pts) if (i + phase) % every == 0 or i == len(pts) - 1]
            if keep[0] != pts[0]: keep.insert(0, pts[0])
            cut_pts = [(x + rng.uniform(-amp, amp), y + rng.uniform(-amp, amp)) for x, y in keep]
            # the profile is indexed by t over the original count; resample it
            n0 = len(pts) - 1; n1 = len(cut_pts) - 1
            prof = (lambda t, profile=profile: profile(t)) if profile else None
            poly = ORIG(cut_pts, pen, prof, cut0, cut1)
        else:
            poly = ORIG(pts, pen, profile, cut0, cut1)
        n = len(poly) // 2; L, R = poly[:n], poly[n:][::-1]; quads = Multi()
        for i in range(n - 1):
            j = min(n - 1, i + 2); q = [L[i], L[i + 1], L[j], R[j], R[i + 1], R[i]]
            if abs(signed_area(q)) > 1e-3: quads.append(q)
        return quads
    return outline

class SerifsOnly(round15.CleanCut):
    """Post op for the centerline-cut fonts: only the small polygons (the
    serifs, ears, dots) get the light treatment; quads pass through."""
    def __call__(self, polys, c):
        rng = random.Random(self.font_seed * 1000 + self.n); self.n += 1
        out = []
        for p in polys:
            if len(p) < 20 and len(p) != 6:
                q = offset_naive(chaikin(jitter(p, self.amp * 0.3, rng.randrange(1 << 30)), 1), self.grow * 0.6)
            else:
                q = offset_naive(p, self.grow * 0.5) if self.grow else p
            if abs(signed_area(q)) >= self.stray: out.append(q)
        return out

E = dict(e_bar_overlap=0.45)
BANK = [
 V("V23a-73c5-h1", "Quads, no cut on the ink", "the outline can not cross itself; the cut moves to the serifs only", pen=quadify(ORIG), post=SerifsOnly(73, 4, 3.0, 2.0, hand=False), over=dict(G, **E)),
 V("V23a-73c5-h2", "Cut the drawing, stroke it", "the centerline is decimated one in four and jittered 3, then stroked and quadded", pen=pen_centerline_cut(73, 4, 3.0), post=SerifsOnly(73, 4, 3.0, 2.0, hand=False), over=dict(G, **E)),
 V("V23a-73c5-h3", "Cut the drawing, gently", "one in six, jitter 2", pen=pen_centerline_cut(73, 6, 2.0), post=SerifsOnly(73, 4, 3.0, 2.0, hand=False), over=dict(G, **E)),
 V("V23a-73c5-h4", "Cut the drawing, stems only", "curves left smooth; only straight strokes are cut", pen=pen_centerline_cut(73, 4, 3.0, curves=False), post=SerifsOnly(73, 4, 3.0, 2.0, hand=False), over=dict(G, **E)),
 V("V23a-73c5-h5", "Cut the drawing, ink pools in the e", "as h2, with a pool of ink at each join of the e's bar and the bar 0.5 into the strokes", pen=pen_centerline_cut(73, 4, 3.0), post=SerifsOnly(73, 4, 3.0, 2.0, hand=False), over=dict(G, e_bar_overlap=0.5, e_join_fill=True)),
 V("V23a-73c5-h6", "Cut the drawing, spine carried", "as h2, and the s's spine forced toward stem weight, as a humanist s carries it (a proposal, not asked for)", pen=pen_centerline_cut(73, 4, 3.0), post=SerifsOnly(73, 4, 3.0, 2.0, hand=False), over=dict(G, s_spine=0.85, **E)),
]

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
    os.makedirs(out, exist_ok=True)
    paths = [round12.build(v, out) for v in BANK]
    for pth in paths: TTFont(pth)
    round12.BANK = BANK
    html = round12.page(paths).replace("<title>Fjord Font Files</title>", "<title>Seed 73, No Hairlines</title>").replace("<h1>Fjord Font Files</h1>", "<h1>Seed 73, No Hairlines</h1>")
    html = html.replace("Round 12. Twenty-six TrueType files from the B5.9 design, one per technique, all vector: pen models and outline operations, no raster.",
                        "Round 16. V23a-73c5 with the hairline-throughs addressed six ways and the e's bar run into its bowl. A hairline is a stroke's outline folding over itself and cancelling under the nonzero fill; the cures cut the drawing rather than the ink, leave curves uncut, or add ink at the joins. The H's ink traps are kept. Six TrueType files.")
    open(os.path.join(out, "fjord-hairlines.html"), "w").write(html)
    with zipfile.ZipFile(os.path.join(out, "fjord-hairlines.zip"), "w", zipfile.ZIP_DEFLATED) as z:
        for pth in paths: z.write(pth, os.path.basename(pth))
    print("ok", len(paths))
