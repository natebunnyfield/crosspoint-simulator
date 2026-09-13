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
def ring(c, cx, cy, rx, ry, a0, a1, n=96, k=None, cut=None, th_fn=None):
    """Outer (cut) and counter (clean) of a bowl segment from a0 to a1 (rad).
    The pen's thickness is kept, so the ring has its stress; the counter is
    the punch: the pen's inner edge, untouched. `th_fn(tangent)` replaces
    the pen's thickness (the g variant with a loop at full stem weight)."""
    k = k or c["k"]; pen = c["pen"]
    pts = A.ellipse(cx, cy, rx, ry, a0, a1, n, k); tans = A.tangents(pts)
    outer, inner = [], []
    for p, tn in zip(pts, tans):
        th = th_fn(tn) if th_fn else pen.th(tn); ox, oy = p[0] - cx, p[1] - cy; L = math.hypot(ox, oy) or 1
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

E_BAR_DEG = 5.0     # the e's bar rises left to right by this (owner 2026-09-12); 0 = level, as before
# Round 38: ten e variants "in between before and after; stronger counter
# inside, different crossbar, different noses". deg = bar tilt; bar = bar
# height over xh (lower = bigger eye); th = bar thickness over the pen's at
# that angle; end = where the lower arm stops (degrees on the bowl, 318 =
# as now, less = shorter, more = closes further); nose = the terminal:
# 'cut' (pen cut + flare, as now), 'flare' (big flare, square end), 'taper'
# (thins to a point), 'beak' (the C's wedge), 'blunt' (square, no flare).
E_VARIANTS = [
 dict(deg=5.0, bar=0.62, th=0.62, end=330, nose='blunt'),  # 0: owner 2026-09-12, from the e dials page (was the round-36 e: 5.0 / 0.58 / 1.0 / 318 / cut)
 dict(deg=0.0, bar=0.55, th=0.8, end=318, nose='cut'),    # 1: level bar, thinner, bigger eye
 dict(deg=2.5, bar=0.58, th=1.0, end=318, nose='cut'),    # 2: halfway tilt
 dict(deg=5.0, bar=0.62, th=1.0, end=318, nose='flare'),  # 3: high bar, small eye, flared nose
 dict(deg=3.0, bar=0.55, th=0.75, end=318, nose='taper'), # 4: low thin bar, pointed nose
 dict(deg=0.0, bar=0.58, th=1.2, end=318, nose='beak'),   # 5: level heavy bar, beaked nose
 dict(deg=5.0, bar=0.56, th=1.0, end=330, nose='blunt'),  # 6: long arm closing further, blunt nose
 dict(deg=8.0, bar=0.58, th=1.0, end=305, nose='cut'),    # 7: steep Jenson tilt, short arm
 dict(deg=3.0, bar=0.62, th=0.6, end=318, nose='flare'),  # 8: high hairline bar, big flare
 dict(deg=0.0, bar=0.58, th=0.85, end=330, nose='beak'),  # 9: level, long arm, beak
 dict(deg=4.0, bar=0.54, th=0.9, end=312, nose='taper'),  # 10: lowest bar (biggest eye), pointed
]
G_EAR_DEG = 35.0    # where on the g's bowl the ear wedge sits (deg from the bowl's right extreme)

# The g set, owner 2026-09-12: "make multiple improved 'g's for me to choose
# from". Selected by the design key `g_variant` (round20.build(over=
# {"g_variant": n}); 0 is the round-28 g, byte-for-byte). bowl_rx / loop_rx in
# units x wf; bowl_h a fraction of the x-height; loop_ry and loop_cy fractions
# of the descender; loop_cx the loop center's offset from the bowl's; angles
# in degrees on the superellipse (neck_from on the bowl, loop_entry on the
# loop, both measured as ellipse() does, 0 = right, 90 = up).
# Owner 2026-09-12: "g3 wins but it needs to match the underlying
# calligraphic brush strokes." Variant 0 is G3 (bowl near the o's width,
# round loop, short neck) re-cut on the nib, with Van den Keere as the shape
# reference (owner, same day: "better match the strokes of van den keere"):
#   - bowl and loop are rings on the pen (they carry the o's stress: thick
#     at the lower left and upper right, thin at the top and bottom -- the
#     same ring() the o uses);
#   - the neck takes NO weight floor. VdK's leaves the bowl's bottom-left
#     and falls down-left at ~65 degrees into the loop's far upper left; at
#     that angle the nib is broad on its own (58-66 units; the old floor
#     forced a 0.6 stem). Its path drops near-vertically first (an 8-degree
#     lean), then turns (ear="pen", neck="nib");
#   - the loop's join into the neck is one stroke: the neck ends ON the
#     loop's centerline with the loop's own tangent (loop_entry 140), so the
#     two widths are the pen's at the same angle and the join is continuous
#     (150: VdK's neck enters the loop's far upper left; at 140 the loop's
#     top hairline turned the corner into the neck and read as a kink);
#   - the ear is a pen stroke: it leaves the bowl's shoulder (48 degrees on
#     the ring) nearly level (a 5-degree rise), which the nib makes 50 wide
#     (a 15-degree rise would be a 40 hairline), pen-cut at the end. VdK's
#     is a level flick, 50 wide.
#   - loop 1.16 x the bowl's width (VdK 1.58; G3 was 1.03), its center 30
#     units right of the bowl's (VdK +33), 0.47 desc down.
# The other variants stand as they were; G3 itself (entry 3) is unchanged
# for reference.
G_VARIANTS = {
    0: dict(name="G3 on the nib, after Van den Keere", bowl_rx=185, bowl_h=0.70, ear="pen", loop_rx=215, loop_ry=0.45, loop_cx=30, loop_cy=0.47, neck_from=242, loop_entry=150, neck="nib"),
    1: dict(name="G1 ear as a top-right wedge serif", bowl_rx=152, bowl_h=0.64, ear="wedge", loop_rx=190, loop_ry=0.42, loop_cx=30, loop_cy=0.47, neck_from=262, loop_entry=118),
    2: dict(name="G2 garalde: smaller bowl, long neck, wide flat loop, flat ear", bowl_rx=136, bowl_h=0.56, ear="flat", loop_rx=205, loop_ry=0.37, loop_cx=42, loop_cy=0.54, neck_from=262, loop_entry=120),
    3: dict(name="G3 Jenson/Doves: bowl near the o's width, round loop, short neck, tick ear", bowl_rx=200, bowl_h=0.72, ear="tick", loop_rx=205, loop_ry=0.46, loop_cx=8, loop_cy=0.44, neck_from=258, loop_entry=116),
    4: dict(name="G4 narrow and tall: bowl narrower than the o, loop narrower than the bowl and deep, neck near vertical", bowl_rx=122, bowl_h=0.64, ear="flick", loop_rx=112, loop_ry=0.47, loop_cx=6, loop_cy=0.47, neck_from=268, loop_entry=100, neck_bend=0.0),
    5: dict(name="G5 open loop: the tail returns toward the neck and stops short, hairline", bowl_rx=152, bowl_h=0.64, ear="flick", loop_rx=190, loop_ry=0.42, loop_cx=30, loop_cy=0.47, neck_from=262, loop_entry=118, loop="open", loop_sweep=300),
    6: dict(name="G6 heavy loop: loop at full stem weight all round, wedge ear", bowl_rx=152, bowl_h=0.64, ear="wedge", loop_rx=190, loop_ry=0.42, loop_cx=30, loop_cy=0.47, neck_from=262, loop_entry=118, loop_w="stem"),
    7: dict(name="round 28 g (the old default)", bowl_rx=152, bowl_h=0.64, ear="flick", loop_rx=190, loop_ry=0.42, loop_cx=30, loop_cy=0.47, neck_from=262, loop_entry=118),
}

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
        """Double-storey g, round 28 (owner: "connector stem on the left side
        instead; make the two ovals better match the rest of the lowercase
        strokes and visual rhythm"), and 2026-09-12 (owner: "make multiple
        improved 'g's for me to choose from") a SET selected by the design
        key `g_variant` (0 = the round-28 g, unchanged; see G_VARIANTS).
        Every variant: an upper bowl and a lower loop as counterpunched rings
        on the pen (so they carry the o's stress), the neck on the LEFT with
        a weight floor of 0.6 stem, the ear off the bowl's upper right and
        never over the bowl, the loop the g's widest part (it sets the
        sides, round 28)."""
        V = G_VARIANTS[c.get("g_variant", 0)]
        P = []; xh = c["xh"]; wf = c["wf"]; s = c["s"]; desc = c["desc"]; over = c["over"]
        rx = V["bowl_rx"] * wf; ry = (xh * V["bowl_h"] + over) / 2; cy = xh + over - ry; cx = rx + s * 0.35
        outer, inner = ring(c, cx, cy, rx, ry, 0, two, 100, cut=cut)
        P.append(outer); P.append(Hole(ccut(inner) if ccut else inner))
        def on_bowl(deg):   # plain-ellipse point, as round 28 placed the ear and the neck
            a = math.radians(deg); return (cx + rx * math.cos(a), cy + ry * math.sin(a))
        ear = V["ear"]
        if ear == "flick":      # round 28: off the upper right, out and a little up, cut at the pen angle
            ex, ey = on_bowl(28)
            A.curve(c, P, A.line((ex - s * 0.15, ey - 6), (ex + 92 * wf, ey + 22), 8), lambda t: 0.75, cut1=c["cut"])
        elif ear == "wedge":    # owner: "make the spur on 'g' a serif like other top right serifs" -- the stem-top
            # bracket wedge (wl, wd, fillet, drop) set on the bowl's right side as if it were a stem ending at
            # G_EAR_DEG, pointing RIGHT. Its inner edge is a vertical line at the ring's centerline x, wd down
            # from the point; up to ~40 deg that x stays outside the counter (cx + rx - th/2) all the way down,
            # so the counter is never crossed (measured: counter area unchanged to 3 sq units). Proof
            # scratchpad wedge/g-e-proof.png, 2026-09-12.
            ex, ey = on_bowl(G_EAR_DEG); a = math.radians(G_EAR_DEG)
            ear_th = c["pen"].th((-math.sin(a), math.cos(a)))
            P.append(A.bracket_wedge((ex, ey), (0, 1), (-1, 0), ear_th, c["wl"], c["wd"], -1, drop=c["drop"], fillet=c["fillet"]))
        elif ear == "flat":     # Garamond: a level flick straight out to the right
            ex, ey = on_bowl(22)
            A.curve(c, P, A.line((ex - s * 0.2, ey), (ex + 115 * wf, ey + 6), 8), lambda t: 0.7, cut1=c["cut"])
        elif ear == "tick":     # Jenson/Doves: a short near-vertical tick rising off the shoulder
            ex, ey = on_bowl(48)
            A.curve(c, P, A.line((ex - 4, ey - s * 0.25), (ex + 14, ey + 62), 8), lambda t: 0.8, cut1=c["cut"])
        elif ear == "pen":      # the nib's own stroke: out of the bowl's shoulder, rising 15 degrees, no profile, pen cut
            # level, as VdK's: a horizontal is 52 under this nib, a 15-degree rise only 40
            ex, ey = on_bowl(48); L = 92 * wf
            A.curve(c, P, A.line((ex - s * 0.15, ey - 4), (ex + L, ey + L * math.tan(math.radians(5))), 12), None, cut1=c["cut"])
        # lower loop
        lrx = V["loop_rx"] * wf; lry = desc * V["loop_ry"]; lcx = cx + V["loop_cx"] * wf; lcy = -desc * V["loop_cy"]
        th_fn = (lambda tn: s) if V.get("loop_w") == "stem" else None   # 6: full stem weight all round
        a1 = math.radians(V["loop_entry"])          # where the neck enters the loop
        if V.get("loop") == "open":
            # 5: the loop is a STROKE from the neck's entry round the bottom and up the right, its tail
            # returning across the top toward the neck and stopping short of it, thinned to a hairline.
            arc = A.ellipse(lcx, lcy, lrx, lry, a1 - 0.14, a1 + math.radians(V["loop_sweep"]), 110, c["k"])
            A.curve(c, P, arc, A.taper_out(0.45, 0.3), cut1=c["cut"])
        else:
            outer2, inner2 = ring(c, lcx, lcy, lrx, lry, 0, two, 110, cut=cut, th_fn=th_fn)
            P.append(outer2); P.append(Hole(ccut(inner2) if ccut else inner2))
        # the neck, on the LEFT: drops from the bowl's bottom, then swings into the loop's upper left,
        # so neck and loop's left side read as one stroke. Pen weight with a floor of 0.6 stem.
        p0 = on_bowl(V["neck_from"])
        p3 = (lcx + lrx * math.cos(a1), lcy + lry * math.sin(a1))
        gap = p0[1] - p3[1]; bend = V.get("neck_bend", 1.0)
        if V.get("neck") == "nib":
            # the nib's neck: a vertical drop out of the bowl, then a turn that
            # arrives on the loop's centerline ALONG the loop's tangent there
            # (the ring runs counterclockwise, so at a1 it heads (-sin, cos)),
            # ending buried a hair inside the loop's stroke. No weight floor:
            # the pen's own thickness along this path stays broad.
            tl = (-math.sin(a1), math.cos(a1))
            link = A.bez(p0, (p0[0] - gap * 0.12, p0[1] - gap * 0.45), (p3[0] - tl[0] * gap * 0.38, p3[1] - tl[1] * gap * 0.38), p3, 40)
            A.curve(c, P, link, A.taper_out(0.85, 0.08))
            return P
        link = A.bez(p0, (p0[0] + 2 * wf * bend, p0[1] - gap * 0.62), (p3[0] + 6 * wf * bend, p3[1] + gap * 0.42), p3, 32)
        tn = A.tangents(link); n = len(link) - 1
        def prof(t):
            i = min(n, int(round(t * n))); th = c["pen"].th(tn[i])
            return max(th, s * 0.6) / th
        A.curve(c, P, link, prof)
        return P

    def g_e(c):
        """The eye is a counterpunch: outer arc from the bar round the top to
        the bar again, counter as the punch; the lower arm is a stroke that
        starts under the bar with a trap notch."""
        P = []; rx = 195 * c["wf"]; cx = rx; ry = c["xh"] / 2 + c["over"]; s = c["s"]; xh = c["xh"]
        # Owner 2026-09-12: "thin out the crossbar of 'e' by putting it at an
        # angle". The bar RISES left to right by E_BAR_DEG about its own
        # middle (still 0.58 xh there); the pen gives it its thickness at
        # that angle (a rising bar runs nearer the nib's thin direction, 26
        # deg), nothing is forced. Both ends stay buried in the bowl as
        # before; the eye's counter closes along the bar's TOP edge, which
        # now slopes with it, and the outer arc meets the bar at each end's
        # own height. Level bar = E_BAR_DEG 0, byte-identical to before.
        V = E_VARIANTS[c.get("e_variant", 0)]
        bar_y = xh * V["bar"]
        tilt = math.radians(V["deg"]); slope = math.tan(tilt)
        # the bar IS the strip between the eye's two closing edges (no separate
        # stroke): its ends are the eye contour's, cx - rx - 0.05 s to cx + rx + 0.08 s
        bar_at = lambda x: bar_y + (x - cx) * slope
        # floor 0.35 stem (was 0.42, which at 5 degrees is ~34 and would have
        # swallowed the chosen 0.62 x ~50 = ~31; the chosen value is the value)
        bar_th = max(c["pen"].th((math.cos(tilt), math.sin(tilt))) * V["th"], s * 0.35)
        yR = bar_at(cx + rx); yL = bar_at(cx - rx)
        a_r = math.asin(max(-1.0, min(1.0, (yR - xh / 2) / ry)))            # where the arc meets the bar, right
        a_l = math.pi - math.asin(max(-1.0, min(1.0, (yL - xh / 2) / ry)))  # ...and left
        # eye: from the bar's right end over the top to the bar's left end
        outer, inner = ring(c, cx, xh / 2, rx, ry, a_r, a_l, 60, cut=cut)
        # close the eye along the bar: outer runs back along the bar's underside, counter along its top
        eye_outer = outer + [(cx - rx - s * 0.05, bar_at(cx - rx - s * 0.05) - bar_th / 2), (cx + rx + s * 0.08, bar_at(cx + rx + s * 0.08) - bar_th / 2)]
        eye_inner = inner + [(cx - rx + s * 0.4, bar_at(cx - rx + s * 0.4) + bar_th / 2), (cx + rx - s * 0.35, bar_at(cx + rx - s * 0.35) + bar_th / 2)]
        P.append(eye_outer); P.append(Hole(eye_inner))
        # lower arm: continues from the eye's own left end (a_l), round
        # the bottom, to the terminal. Its start overlaps the eye by a few
        # degrees; the trap is the notch the taper leaves under the bar.
        arm = A.ellipse(cx, xh / 2, rx, ry, a_l - 0.06, math.radians(V["end"]), 70, c["k"])
        tin = A.taper_in(0.55 - 0.15 * trap, 0.12); nose = V["nose"]
        if nose == 'cut':     A.curve(c, P, arm, A.compose(tin, A.flare_end(0.25, 0.12)), cut1=c["cut"])
        elif nose == 'flare': A.curve(c, P, arm, A.compose(tin, A.flare_end(0.5, 0.2)))
        elif nose == 'taper': A.curve(c, P, arm, A.compose(tin, A.taper_out(0.7, 0.3)))
        elif nose == 'blunt': A.curve(c, P, arm, tin)
        elif nose == 'beak':
            A.curve(c, P, arm, tin)
            tn = A.tangents(arm)[-1]; d = tn; nrm = (-d[1], d[0])
            P.append(A.bracket_wedge(arm[-1], d, nrm, c["pen"].th(tn) * 1.1, c["wl"] * 0.85, c["wd"] * 0.85, -1, drop=0, fillet=c["fillet"]))
        return P

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
        yc = (8 * (xh + c["arch_over"]) - xh * start - xh * 0.60) / 6   # peak's centerline at the arch overshoot (rounds 27, 29)
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
