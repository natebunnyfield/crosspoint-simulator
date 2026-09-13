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
            # keep BOTH end faces (round 26): dropping the first sample ate up
            # to four steps of every stroke's start, which is where a stem
            # hands over to its curve -- the j's tail broke there.
            L = [p for i, p in enumerate(L) if (i + ph) % every == 0 or i == len(L) - 1 or i == 0]
            R = [p for i, p in enumerate(R) if (i + ph) % every == 0 or i == len(R) - 1 or i == 0]
            L = [(x + rng.uniform(-amp, amp), y + rng.uniform(-amp, amp)) for x, y in L]
            R = [(x + rng.uniform(-amp, amp), y + rng.uniform(-amp, amp)) for x, y in R]
        return L + R[::-1]
    return outline

# ---------------------------------------------------------------- clips and bites
def clip_line(poly, p0, nrm):
    """Sutherland-Hodgman: keep the side where dot(p - p0, nrm) >= 0."""
    def inside(p): return (p[0] - p0[0]) * nrm[0] + (p[1] - p0[1]) * nrm[1] >= 0
    out = []
    for cur, nxt in zip(poly, poly[1:] + poly[:1]):
        ci, ni = inside(cur), inside(nxt)
        if ci: out.append(cur)
        if ci != ni:
            dc = (cur[0] - p0[0]) * nrm[0] + (cur[1] - p0[1]) * nrm[1]
            dn = (nxt[0] - p0[0]) * nrm[0] + (nxt[1] - p0[1]) * nrm[1]
            t = dc / (dc - dn) if dc != dn else 0
            out.append((cur[0] + (nxt[0] - cur[0]) * t, cur[1] + (nxt[1] - cur[1]) * t))
    return out if len(out) >= 3 else None

def bite(polys, apex, direction, half_angle, keep_hole=True, reach=None):
    """An INK TRAP: a V-shaped wedge with its apex at `apex`, opening along
    `direction` (unit), removed from every contour that covers it. Without
    booleans, polygon minus a convex wedge is the union of the polygon
    clipped to each of the wedge's two outer half-planes -- two polygons
    whose union is exactly the polygon with the notch."""
    dx, dy = direction; ca, sa = math.cos(half_angle), math.sin(half_angle)
    # the wedge's two edges, as outward normals of the half-planes to KEEP
    e1 = (dx * ca - dy * sa, dx * sa + dy * ca); e2 = (dx * ca + dy * sa, -dx * sa + dy * ca)
    n1 = (-e1[1], e1[0]); n2 = (e2[1], -e2[0])
    out = []
    for poly in polys:
        if isinstance(poly, Hole) and keep_hole: out.append(poly); continue
        # PARTITION, never union: pieces that overlap wind twice, and a
        # counter cancels only one layer (the bowls filled solid, 2026-09-12).
        # piece1 = poly & H1; rest = poly & ~H1; piece2 = rest & H2;
        # rest2 = rest & ~H2; piece3 = rest2 & beyond-the-cap.
        pieces = []
        p1 = clip_line(list(poly), apex, n1); rest = clip_line(list(poly), apex, (-n1[0], -n1[1]))
        if p1: pieces.append(p1)
        if rest:
            p2 = clip_line(rest, apex, n2); rest2 = clip_line(rest, apex, (-n2[0], -n2[1]))
            if p2: pieces.append(p2)
            if rest2 and reach is not None:
                cap = (apex[0] + dx * reach, apex[1] + dy * reach)
                p3 = clip_line(rest2, cap, (dx, dy))
                if p3: pieces.append(p3)
        if not pieces: continue
        total = sum(abs(signed_area(q)) for q in pieces)
        if abs(total - abs(signed_area(poly))) < 1e-3:
            out.append(poly)   # the wedge missed this polygon
        else:
            out.extend(pieces)
    return out

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
        """b d p q: a full ring plus a stem, the ring KEPT TO THE STEM (owner
        2026-09-12): its outer contour is clipped a hair inside the stem's
        inner edge (0.06 stem of overlap, so no shared edge seams), its
        counter at the stem's inner edge. The INK TRAPS are cut the way a
        punchcutter cuts them: a tooth on the counterpunch at each crotch,
        and a matching notch on the stem's own edge. Two simple polygons,
        no clipping, no partition seams (both were tried and both failed
        under FreeType's nonzero fill)."""
        P = []; rx = 214 * c["wf"]; s = c["s"]; xh = c["xh"]
        if side == "right":   # d q
            cx = rx; x = cx + rx - s * 0.5; into = -1
        else:                 # b p
            x = s * 0.5; cx = x + rx - s * 0.5; into = 1
        ry = xh / 2 + c["over"]
        outer, inner = ring(c, cx, xh / 2, rx, ry, 0, two, 120, cut=cut)
        edge = x - into * s * 0.5           # the stem's inner edge, toward the bowl
        outer = clip_line(outer, (edge - into * s * 0.06, 0), (into, 0))
        inner = clip_line(inner, (edge, 0), (into, 0))
        depth = c.get("trap_depth", 0.55) * s; half = s * 0.55
        # crotch heights: where the counter meets the stem's inner edge
        ys = [y for (xx, y) in inner if abs(xx - edge) < 0.5]
        y_top, y_bot = (max(ys), min(ys)) if ys else (xh * 0.82, xh * 0.18)
        # the tooth: the counter's corner vertex is pulled INTO the ink along
        # the crotch's bisector (up-and-into at the top, down-and-into below)
        tooth = []
        for i, (xx, y) in enumerate(inner):
            if abs(xx - edge) < 0.5 and (abs(y - y_top) < 1 or abs(y - y_bot) < 1):
                sgn = 1 if abs(y - y_top) < 1 else -1
                tooth.append((i, (xx - into * depth * 0.7, y + sgn * depth * 0.7)))
        for i, pt in sorted(tooth, reverse=True):
            inner.insert(i + (0 if pt[1] > xh / 2 else 1), pt)
        P.append(outer); P.append(Hole(ccut(inner) if ccut else inner))
        A.stem(c, P, x, bottom, top, top="wedge", foot=("right" if side == "right" else "left") if bottom == 0 else "both", top_side=1)
        # the notch on the stem's inner edge, matching the tooth
        stem_poly = P[2]
        notched = []
        for (xx, y) in stem_poly:
            if abs(xx - edge) < 0.5:
                for yc in (y_top, y_bot):
                    d = abs(y - yc)
                    if d < half:
                        xx = xx - into * 0.0 + (-into) * depth * 0.6 * (1 - d / half)
                        break
            notched.append((xx, y))
        P[2] = notched
        return P

    def g_d(c): return bowl_stem(c, "right", c["asc"], 0)
    def g_b(c): return bowl_stem(c, "left", c["asc"], 0)
    def g_p(c): return bowl_stem(c, "left", c["xh"], -c["desc"])
    def g_q(c): return bowl_stem(c, "right", c["xh"], -c["desc"])

    def g_g(c):
        """Looptail (double-storey) g, owner 2026-09-12, in the counterpunched
        construction the font uses: upper bowl and lower loop are each an
        outer contour around a struck counter; the link is a tapered stroke;
        the ear starts at the bowl's outer edge and never crosses it."""
        P = []; xh = c["xh"]; wf = c["wf"]; s = c["s"]; desc = c["desc"]
        rx = 160 * wf; ry = xh * 0.31; cx = rx + 10; cy = xh - ry
        outer, inner = ring(c, cx, cy, rx, ry, 0, two, 100, cut=cut)
        P.append(outer); P.append(Hole(ccut(inner) if ccut else inner))
        ex = cx + rx * 0.92; ey = cy + ry * 0.55
        A.curve(c, P, A.line((ex, ey), (ex + 85 * wf, ey + 28), 8), lambda t: 0.8, cut1=c["cut"])
        lcx, lcy = cx + 4, -desc * 0.55; lrx, lry = 200 * wf, desc * 0.56
        outer2, inner2 = ring(c, lcx, lcy, lrx, lry, 0, two, 110, cut=cut)
        P.append(outer2); P.append(Hole(ccut(inner2) if ccut else inner2))
        # the link: from the bowl's lower right down into the loop's upper right
        p0 = (cx + rx * 0.62, cy - ry * 0.82)
        p3 = (lcx + lrx * 0.66, lcy + lry * 0.78)
        link = A.bez(p0, (p0[0] + 26, p0[1] - 70), (p3[0] + 60, p3[1] + 70), p3, 30)
        A.curve(c, P, link, A.compose(A.taper_in(0.65, 0.2), A.taper_out(0.75, 0.2)))
        return P

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
        # round 27: hood peaks at the rounds' edge (was 0.07 xh over), bowl
        # bottom at -over like the o (was 0.07 xh under)
        yc = (8 * (xh + c["over"]) - xh * 0.66 - xh * 0.78) / 6
        hood = A.bez((x, xh * 0.66), (x, yc), (x - 250 * wf, yc), (x - 300 * wf, xh * 0.78), 40)
        A.curve(c, P, hood, A.compose(A.taper_in(0.45, 0.3), A.flare_end(0.15, 0.3)), cut1=c["cut"])
        rx = 165 * wf; ry = xh * 0.29
        outer, inner = ring(c, x - rx, ry - c["over"], rx, ry, 0, two, 90, cut=cut)   # centerline bottom at -over, as the o
        P.append(outer); P.append(Hole(ccut(inner) if ccut else inner)); return P

    return {'o': g_o, 'd': g_d, 'b': g_b, 'p': g_p, 'q': g_q, 'g': g_g, 'e': g_e, 'a': g_a}

# ---------------------------------------------------------------- traps in the arches
def patch_arch(trap):
    """The arch of n m h u leaves the stem at its inner edge and tapers, so a
    notch opens at the crotch: the ink trap."""
    def _arch(c, P, x0, x1, xh, start=None):
        start = c["arch"] if start is None else start
        s = c["s"]
        yc = (8 * (xh + c["over"]) - xh * start - xh * 0.60) / 6   # peak's centerline at the rounds' (round 27)
        pts = A.bez((x0 + s * 0.5 * trap, xh * start), (x0 + s * 0.2, yc + xh * 0.005), (x1, yc - xh * 0.005), (x1, xh * 0.60), 44)
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
 ("V23a-73c5-k6-t1", "k6, traps 0.4 stem", "pure decimation one in four, no jitter; bowls kept to their stems; ink traps bitten 0.4 stem deep at the crotches", 73, 4, 0.0, 1.0, None, 0.4),
 ("V23a-73c5-k6-t2", "k6, traps 0.6 stem", "as t1 with the bite 0.6 stem deep", 73, 4, 0.0, 1.0, None, 0.6),
 ("V23a-73c5-k6-t3", "k6, traps 0.85 stem", "as t1 with the bite 0.85 stem deep, the Bell Centennial depth", 73, 4, 0.0, 1.0, None, 0.85),
]

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
    os.makedirs(out, exist_ok=True)
    bank, paths = [], []
    for key, title, blurb, seed, every, amp, trap, cc, tdepth in SPEC:
        v = V(key, title, blurb, pen=pen_linear(seed, every, amp), post=Cut(seed, 4, 3.0, 2.0, hand=False), over=dict(G, e_bar_overlap=0.45, trap_depth=tdepth))
        bank.append(v); paths.append(build_variant(v, out, seed, every, amp, trap, cc))
    for pth in paths: TTFont(pth)
    round12.BANK = bank
    html = round12.page(paths).replace("<title>Fjord Font Files</title>", "<title>k6, Traps</title>").replace("<h1>Fjord Font Files</h1>", "<h1>k6, Traps</h1>")
    html = html.replace("Round 12. Twenty-six TrueType files from the B5.9 design, one per technique, all vector: pen models and outline operations, no raster.",
                        "Round 18. k6 with three bugs fixed: the fractures across j and f (a stem ending exactly where its curve begins seams in FreeType; stems now run into their curves), bowls kept to their stems (clipped at the stem's edges), and ink traps bitten into the crotches where bowl meets stem, at three depths. Three TrueType files.")
    open(os.path.join(out, "fjord-k6.html"), "w").write(html)
    with zipfile.ZipFile(os.path.join(out, "fjord-k6.zip"), "w", zipfile.ZIP_DEFLATED) as z:
        for pth in paths: z.write(pth, os.path.basename(pth))
    print("ok", len(paths))
