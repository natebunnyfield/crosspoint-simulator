"""Round 13: refinements of the three kept techniques, V23 Scissors, V15
Rotating nib, V19 Gravity. Six each, eighteen TrueType files."""
import math, os, sys, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import round11, round12, alphabet2 as A
from round12 import V, quadify, post_scissors, post_round, chaikin, decimate, jitter
from fontTools.ttLib import TTFont

def pen_rot_grav(sweep_deg, sag):
    """Rotating nib with gravity on top: the two kept pens in one hand."""
    rot = round11.pen_rotating(sweep_deg)
    def outline(pts, pen, profile=None, cut0=None, cut1=None):
        poly = rot(pts, pen, profile, cut0, cut1); n = len(poly) // 2
        L, R = poly[:n], poly[n:][::-1]; out_L = []; out_R = []
        for l, r in zip(L, R):
            cx, cy = (l[0] + r[0]) / 2, (l[1] + r[1]) / 2
            g = 1 + sag * max(0.0, 1 - cy / 480.0)
            out_L.append((cx + (l[0] - cx) * g, cy + (l[1] - cy) * g)); out_R.append((cx + (r[0] - cx) * g, cy + (r[1] - cy) * g))
        return out_L + out_R[::-1]
    return outline

def post_scissors_soft(every, amp, seed=2):
    return lambda polys, c: [chaikin(jitter(decimate(p, every), amp, seed + i), 1) for i, p in enumerate(polys)]

BANK = [
 # ---- V23 Scissors
 V("V23a", "Scissors, fine", "one vertex in four, jitter 4: many small snips", post=post_scissors(4, 4, 2)),
 V("V23b", "Scissors, medium", "one in six, jitter 6", post=post_scissors(6, 6, 2)),
 V("V23c", "Scissors, calm facets", "one in eight, jitter 3: flat cuts, steady hand", post=post_scissors(8, 3, 2)),
 V("V23d", "Scissors, rough", "one in five, jitter 9", post=post_scissors(5, 9, 4)),
 V("V23e", "Scissors, softened", "one in five, jitter 6, then one rounding pass: the cut edges eased", post=post_scissors_soft(5, 6, 2)),
 V("V23f", "Scissors on the brush", "the expert brush cut with scissors", pen=quadify(round11.pen_brush(0.45, 0.25)), post=post_scissors(5, 5, 3)),
 # ---- V15 Rotating nib
 V("V15a", "Rotating nib, 30°", "a gentler turn along each stroke", pen=quadify(round11.pen_rotating(30))),
 V("V15b", "Rotating nib, 70°", "a wider turn", pen=quadify(round11.pen_rotating(70))),
 V("V15c", "Rotating nib from 14°", "50° sweep starting flatter", pen=quadify(round11.pen_rotating(50)), over=dict(stress=14)),
 V("V15d", "Rotating nib from 34°", "50° sweep starting steeper", pen=quadify(round11.pen_rotating(50)), over=dict(stress=34)),
 V("V15e", "Rotating nib, lower contrast", "50° at contrast 0.45", pen=quadify(round11.pen_rotating(50)), over=dict(contrast=0.45)),
 V("V15f", "Rotating nib, letterpress", "50°, then grown 5 and rounded", pen=quadify(round11.pen_rotating(50)), post=round12.post_spread(5, 1)),
 # ---- V19 Gravity
 V("V19a", "Gravity, light sag", "0.3", pen=quadify(round11.pen_gravity(0.3))),
 V("V19b", "Gravity, heavy sag", "0.9", pen=quadify(round11.pen_gravity(0.9))),
 V("V19c", "Gravity, lower contrast", "0.6 at contrast 0.5", pen=quadify(round11.pen_gravity(0.6)), over=dict(contrast=0.5)),
 V("V19d", "Gravity, lighter cut", "0.6 on a 76 stem", pen=quadify(round11.pen_gravity(0.6)), over=dict(stem=76)),
 V("V19e", "Gravity, softened", "0.6, then two rounding passes", pen=quadify(round11.pen_gravity(0.6)), post=post_round(2)),
 V("V19f", "Gravity with the rotating nib", "50° sweep, 0.5 sag: the two kept pens in one hand", pen=quadify(pen_rot_grav(50, 0.5))),
]

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
    os.makedirs(out, exist_ok=True)
    paths = [round12.build(v, out) for v in BANK]
    for pth in paths: TTFont(pth)
    round12.BANK = BANK
    html = round12.page(paths).replace("<title>Fjord Font Files</title>", "<title>Fjord Refinements</title>").replace("<h1>Fjord Font Files</h1>", "<h1>Fjord Refinements</h1>")
    html = html.replace("Round 12. Twenty-six TrueType files from the B5.9 design, one per technique, all vector: pen models and outline operations, no raster.",
                        "Round 13. The three kept techniques refined six ways each: V23 Scissors, V15 Rotating nib, V19 Gravity. Eighteen TrueType files, all vector.")
    open(os.path.join(out, "fjord-refinements.html"), "w").write(html)
    with zipfile.ZipFile(os.path.join(out, "fjord-refinements.zip"), "w", zipfile.ZIP_DEFLATED) as z:
        for pth in paths: z.write(pth, os.path.basename(pth))
    print("ok", len(paths))
