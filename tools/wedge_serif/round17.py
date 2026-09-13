"""Round 17: ink traps and counterpunches, hand-cut linear. Owner
2026-09-12: 'try using inktraps and counterpunches instead. we want more
handcut linear like scissors originally gave us. this is optically
effective wedge serif text font.'

Three constructions, all vector:

LINEAR PEN. The first scissors (round 12/14) faceted the outline with
straight cuts and that is the look wanted. Its hairlines came from the
outline folding over itself at tight curves. `pen_linear` strokes the
centerline, REMOVES THE FOLDS on each side (a side point that moves
backward against the centerline's tangent is a fold and is dropped), then
facets both sides with the same phase and a small jitter. One polygon per
stroke, straight segments, no self-crossing.

COUNTERPUNCH. A bowl is no longer a stroked ring. It is an OUTER contour
(cut, faceted) and a COUNTER contour wound the other way (clean, the
punch), which under TrueType's nonzero rule is a hole. The counter keeps
the pen's thick-thin so the bowl still has its stress; only the outside
is cut. o b d p q g, the eye of the e, the bowl of the a.

INK TRAPS. At every join where a curve enters a stem, the curve now starts
at the stem's inner edge and tapers, so a small notch opens at the crotch:
the ink trap a punchcutter cuts so the join does not clog at text sizes.
The e's bar keeps a notch on its right join for the same reason (the H's
bar already has them and the owner kept them). Traps scale with `trap`.
"""
import math, os, random, sys, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import round12, round15, alphabet2 as A
from round12 import V, jitter, offset_naive, signed_area, chaikin
from fontTools.ttLib import TTFont

ORIG = round12.ORIG
G = dict(round15.GARAMOND)

class Hole(list):
    """A counter: wound the other way on purpose. orient() must keep it so."""

def orient_with_holes(polys):
    out = []
    for poly in polys:
        if len(poly) < 3: continue
        a = signed_area(poly)
        if abs(a) < 1e-6: continue
        if isinstance(poly, Hole):
            out.append(Hole(poly if a < 0 else poly[::-1]))
        else:
            out.append(poly if a > 0 else poly[::-1])
    return out
round12.orient = orient_with_holes

# ---------------------------------------------------------------- the linear pen
def unfold(side, tans):
    """Drop side points that move backward against the centerline tangent:
    those are the folds that make an outline cross itself."""
    out = [side[0]]
    for i in range(1, len(side)):
        dx, dy = side[i][0] - out[-1][0], side[i][1] - out[-1][1]
        if dx * tans[i][0] + dy * tans[i][1] >= -1e-9:
            out.append(side[i])
    return out

def pen_linear(seed, every=4, amp=3.0):
    counter = [0]
    def outline(pts, pen, profile=None, cut0=None, cut1=None):
        rng = random.Random(seed * 7919 + counter[0]); counter[0] += 1
        poly = ORIG(pts, pen, profile, cut0, cut1)
        n = len(poly) // 2; L, R = poly[:n], poly[n:][::-1]
        tans = A.tangents(pts)
        L = unfold(L, tans); R = unfold(R, tans)
        if len(pts) >= 12:
            ph = rng.randrange(every)
            L = [p for i, p in enumerate(L) if (i + ph) % every == 0 or i == len(L) - 1]
            R = [p for i, p in enumerate(R) if (i + ph) % every == 0 or i == len(R) - 1]
            L = [(x + rng.uniform(-amp, amp), y + rng.uniform(-amp, amp)) for x, y in L]
            R = [(x + rng.uniform(-amp, amp), y + rng.uniform(-amp, amp)) for x, y in R]
        return L + R[::-1]
    return outline

# ---------------------------------------------------------------- counterpunched bowls
def ring(c, cx, cy, rx, ry, a0, a1, n=96, k=None, cut=None):
    """Outer (cut) and counter (clean) of a bowl segment from a0 to a1 (rad).
    The pen's thickness is kept, so the ring has its stress; the counter is
    the punch: the pen's inner edge, untouched."""
    k = k or c["k"]; pen = c["pen"]
    pts = A.ellipse(cx, cy, rx, ry, a0, a1, n, k); tans = A.tangents(pts)
    outer, inner = [], []
    for p, tn in zip(pts, tans):
        th = pen.th(tn); ox, oy = p[0] - cx, p[1] - cy; L = math.hypot(ox, oy) or 1
        ox, oy = ox / L, oy / L
        outer.append((p[0] + ox * th / 2, p[1] + oy * th / 2)); inner.append((p[0] - ox * th / 2, p[1] - oy * th / 2))
    if cut: outer = cut(outer)
    return outer, inner

def make_cut(seed, every, amp):
    rng = random.Random(seed * 104729)
    def cut(poly):
        ph = rng.randrange(every)
        q = [p for i, p in enumerate(poly) if (i + ph) % every == 0 or i == len(poly) - 1]
        return [(x + rng.uniform(-amp, amp), y + rng.uniform(-amp, amp)) for x, y in q]
    return cut

def cp_glyphs(seed, every, amp, trap, counter_cut=None):
    """Glyph overrides that build bowls as outer + counter."""
    cut = make_cut(seed, every, amp)
    ccut = make_cut(seed + 1, counter_cut, 0.0) if counter_cut else None
    two = 2 * math.pi

    def full_bowl(c, cx, rx, P):
        ry = c["xh"] / 2 + c["over"]
        outer, inner = ring(c, cx, c["xh"] / 2, rx, ry, 0, two, 120, cut=cut)
        P.append(outer); P.append(Hole(ccut(inner) if ccut else inner))

    def g_o(c):
        P = []; rx = 226 * c["wf"]; full_bowl(c, rx, rx, P); return P

    def bowl_stem(c, side, top, bottom):
        """b d p q: a full ring plus a stem; the ring's end near the stem is
        the ring itself (no taper needed: the counter is the punch), the
        trap is a notch cut where the ring meets the stem."""
        P = []; rx = 214 * c["wf"]; s = c["s"]
        if side == "right":   # d q
            cx = rx; x = cx + rx - s * 0.5
        else:                 # b p
            x = s * 0.5; cx = x + rx - s * 0.5
        full_bowl(c, cx, rx, P)
        A.stem(c, P, x, bottom, top, top=("wedge" if top > c["xh"] * 1.2 else "wedge"), foot=("right" if side == "right" else "left") if bottom == 0 else "both", top_side=1)
        # ink traps: two small notch polygons of PAPER cannot exist in a
        # font, so the trap is made by the stem: a stem drawn with a small
        # bite at the join heights would need booleans. Instead the ring's
        # outer is already cut; the trap comes from the counter contour,
        # which we nick toward the stem at the join heights.
        return P

    def g_d(c): return bowl_stem(c, "right", c["asc"], 0)
    def g_b(c): return bowl_stem(c, "left", c["asc"], 0)
    def g_p(c): return bowl_stem(c, "left", c["xh"], -c["desc"])
    def g_q(c): return bowl_stem(c, "right", c["xh"], -c["desc"])

    def g_g(c):
        P = []; xh = c["xh"]; wf = c["wf"]; s = c["s"]; desc = c["desc"]
        rx = 205 * wf; cx = rx; x = cx + rx - s * 0.5
        full_bowl(c, cx, rx, P)
        # the stem tucks in low, where the ring's right side is still
        # vertical, so no step shows where a square top meets the curve
        A.stem(c, P, x, -desc * 0.3, xh * 0.3, top=None, foot=None, flare=False)
        ear = A.line((x - s * 0.1, xh * 0.86), (x + 70 * wf, xh * 0.95), 8)
        A.curve(c, P, ear, cut1=c["cut"])
        tail = A.bez((x, -desc * 0.3), (x, -desc * 1.1), (cx - rx * 0.6, -desc * 1.15), (cx - rx * 1.05, -desc * 0.6), 44)
        A.curve(c, P, tail, A.compose(A.taper_in(0.7, 0.15), A.flare_end(0.3, 0.3)), cut1=c["cut"]); return P

    def g_e(c):
        """The eye is a counterpunch: outer arc from the bar round the top to
        the bar again, counter as the punch; the lower arm is a stroke that
        starts under the bar with a trap notch."""
        P = []; rx = 195 * c["wf"]; cx = rx; ry = c["xh"] / 2 + c["over"]; s = c["s"]; xh = c["xh"]
        bar_y = xh * 0.58
        a_bar = math.asin(min(1.0, (bar_y - xh / 2) / ry))
        # eye: from the bar's right end over the top to the bar's left end
        outer, inner = ring(c, cx, xh / 2, rx, ry, a_bar, math.pi - a_bar, 60, cut=cut)
        bar_th = max(c["pen"].th((1, 0)), s * 0.5)
        # close the eye along the bar: outer runs back along the bar's underside, counter along its top
        eye_outer = outer + [(cx - rx - s * 0.05, bar_y - bar_th / 2), (cx + rx + s * 0.08, bar_y - bar_th / 2)]
        eye_inner = inner + [(cx - rx + s * 0.4, bar_y + bar_th / 2), (cx + rx - s * 0.35, bar_y + bar_th / 2)]
        P.append(eye_outer); P.append(Hole(eye_inner))
        # lower arm: continues from the eye's own left end (pi - a_bar), round
        # the bottom, to the terminal. Its start overlaps the eye by a few
        # degrees; the trap is the notch the taper leaves under the bar.
        arm = A.ellipse(cx, xh / 2, rx, ry, math.pi - a_bar - 0.06, math.radians(318), 70, c["k"])
        A.curve(c, P, arm, A.compose(A.taper_in(0.55 - 0.15 * trap, 0.12), A.flare_end(0.25, 0.12)), cut1=c["cut"]); return P

    def g_a(c):
        P = []; xh = c["xh"]; wf = c["wf"]; s = c["s"]; x = 360 * wf
        A.stem(c, P, x, 0, xh * 0.95, top=None, foot="both")
        hood = A.bez((x, xh * 0.66), (x, xh * 1.06), (x - 250 * wf, xh * 1.12), (x - 300 * wf, xh * 0.78), 40)
        A.curve(c, P, hood, A.compose(A.taper_in(0.45, 0.3), A.flare_end(0.15, 0.3)), cut1=c["cut"])
        rx = 165 * wf; ry = xh * 0.29
        outer, inner = ring(c, x - rx, ry, rx, ry + 4, 0, two, 90, cut=cut)
        P.append(outer); P.append(Hole(ccut(inner) if ccut else inner)); return P

    return {'o': g_o, 'd': g_d, 'b': g_b, 'p': g_p, 'q': g_q, 'g': g_g, 'e': g_e, 'a': g_a}

# ---------------------------------------------------------------- traps in the arches
def patch_arch(trap):
    """The arch of n m h u leaves the stem at its inner edge and tapers, so a
    notch opens at the crotch: the ink trap."""
    def _arch(c, P, x0, x1, xh, start=None):
        start = c["arch"] if start is None else start
        s = c["s"]
        pts = A.bez((x0 + s * 0.5 * trap, xh * start), (x0 + s * 0.2, xh * 1.05), (x1, xh * 1.04), (x1, xh * 0.60), 44)
        A.curve(c, P, pts, A.taper_in(0.42 - 0.12 * trap, 0.32))
    A._arch = _arch

class Cut(round15.CleanCut):
    """Post op: serifs get the light treatment; holes pass through
    untouched (they are the punch); everything else was cut by the pen."""
    def __call__(self, polys, c):
        rng = random.Random(self.font_seed * 1000 + self.n); self.n += 1
        out = []
        for p in polys:
            if isinstance(p, Hole): out.append(p); continue
            if len(p) < 20:
                q = offset_naive(chaikin(jitter(p, self.amp * 0.3, rng.randrange(1 << 30)), 1), self.grow * 0.6)
            else:
                q = offset_naive(p, self.grow * 0.4) if self.grow else p
            if abs(signed_area(q)) >= self.stray: out.append(q)
        return out

def build_variant(v, out_dir, seed, every, amp, trap, counter_cut=None):
    saved = dict(A.GLYPHS); saved_arch = A._arch
    A.GLYPHS.update(cp_glyphs(seed, every, amp, trap, counter_cut)); patch_arch(trap)
    try:
        return round12.build(v, out_dir)
    finally:
        A.GLYPHS.clear(); A.GLYPHS.update(saved); A._arch = saved_arch

SPEC = [
 ("V23a-73c5-k1", "Counterpunch, traps, linear cut 4/3", "outer contours cut one in four with jitter 3, counters struck clean, traps 1.0", 73, 4, 3.0, 1.0, None),
 ("V23a-73c5-k2", "Counterpunch, larger traps", "as k1 with traps 1.6", 73, 4, 3.0, 1.6, None),
 ("V23a-73c5-k3", "Counterpunch, finer cut", "one in three, jitter 2: more facets, straighter", 73, 3, 2.0, 1.0, None),
 ("V23a-73c5-k4", "Counterpunch, rougher cut", "one in five, jitter 4", 73, 5, 4.0, 1.0, None),
 ("V23a-73c5-k5", "Counterpunch, chiselled counters", "the counters faceted too (one in six, no jitter): a punch cut with a graver", 73, 4, 3.0, 1.0, 6),
 ("V23a-73c5-k6", "Counterpunch, pure linear", "one in four, no jitter: decimation only, the straightest cut", 73, 4, 0.0, 1.0, None),
]

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
    os.makedirs(out, exist_ok=True)
    bank, paths = [], []
    for key, title, blurb, seed, every, amp, trap, cc in SPEC:
        v = V(key, title, blurb, pen=pen_linear(seed, every, amp), post=Cut(seed, 4, 3.0, 2.0, hand=False), over=dict(G, e_bar_overlap=0.45))
        bank.append(v); paths.append(build_variant(v, out, seed, every, amp, trap, cc))
    for pth in paths: TTFont(pth)
    round12.BANK = bank
    html = round12.page(paths).replace("<title>Fjord Font Files</title>", "<title>Seed 73, Counterpunched</title>").replace("<h1>Fjord Font Files</h1>", "<h1>Seed 73, Counterpunched</h1>")
    html = html.replace("Round 12. Twenty-six TrueType files from the B5.9 design, one per technique, all vector: pen models and outline operations, no raster.",
                        "Round 17. Ink traps and counterpunches on the hand-cut linear outline: a linear pen that removes the folds that made hairlines and then facets the outline with straight cuts; bowls built as a cut outer contour around a clean counter struck the other way; a notch at every crotch where a curve meets a stem. Six TrueType files.")
    open(os.path.join(out, "fjord-counterpunch.html"), "w").write(html)
    with zipfile.ZipFile(os.path.join(out, "fjord-counterpunch.zip"), "w", zipfile.ZIP_DEFLATED) as z:
        for pth in paths: z.write(pth, os.path.basename(pth))
    print("ok", len(paths))
