"""The designed parts every glyph is built from. Each returns a shapely
geometry (already a valid solid) or, for the edge helpers, point lists; a
glyph composes them with geom.ink(solids, cutouts), whose union IS the
join -- one outline per solid, counters as holes, nothing buried.

Widths are DECLARED here and in the glyph code, read against pen.th()
(the reference), not generated from it: `widths(keys)` interpolates the
designer's keypoints along a stroke."""
import os, math
from . import geom, pen
from .geom import cubic, quad, line, superellipse, join, resample, tangents, smooth
from .pen import S, CS, XH, WL, WD, DROP, FILLET, FOOT, ENT, TH_V, TH_H, HAIR, CUT

# ---------------------------------------------------------------- life
# Owner 2026-09-13, on the variety audit (129 of 144 serifs byte-identical
# twins): "alter anything identical very slightly so they render the same
# at small scale, but are full of life at large scale." Every wedge and
# every ring takes a small deterministic perturbation keyed on the glyph
# being drawn and the order of the call within it -- never on geometry, so
# the variable font's masters get the same perturbation and stay
# compatible. LIFE is the amplitude: 0.06 = +-6% on a wedge's length and
# depth, +-10% on its drop and fillet, +-0.06 on a ring's superellipse
# exponent and +-0.6 deg of rotation. At 54 px a wedge is 3.5 x 7 px, so
# 6% is a fifth of a pixel: the four-level render does not move; at 400 px
# it is 4 units, a visible difference of hand. FJORD_LIFE=0 switches it off.
# ROUND 225 -- MOST OF THE WOBBLE COMES OUT. Owner 2026-09-18: *"reduce most
# of the wobble effect on letters."* ALBO_HAND_SCALE is one number over every
# deliberate irregularity in the face (docs/albo-imperfections.md): the LIFE
# jitter here, and in aldine.py the A's droop, the g's and Q's hand tables, the
# R's, the Z's and the X's. 1.0 is round 224 byte for byte; 0.3 ships.
HAND_SCALE = float(os.environ.get("ALBO_HAND_SCALE", 0.0))   # round 231: "remove all awful wavy lines for now"
LIFE = float(os.environ.get("FJORD_LIFE", 0.06)) * HAND_SCALE

# GLITCH SWEEP 2026-09-16: how deep below a stem's top face the italic ENTRY
# stroke's own end is buried, x S. Its square end face is 0.88 x the stem wide
# and nearly vertical, so a shallow burial leaves the face's upper corner
# standing past the stem as a pointed tab. The full account and the sweep are
# beside the entry itself, in `stem`. 0.18 is what shipped before this.
IT_END_BURY = float(os.environ.get("ALBO_IT_END_BURY", 0.45))
# ... and how high above the baseline the italic EXIT stroke starts, x S, for
# the mirror reason at the other end of the letter. Its own account is beside
# the exit in `stem`. 0.16 is what shipped before this.
IT_START_BURY = float(os.environ.get("ALBO_IT_START_BURY", 0.45))
_life = {"glyph": None, "n": 0}
def begin_glyph(name):
    """build.draw calls this before drawing a glyph; resets the call count."""
    _life["glyph"] = name; _life["n"] = 0
def life(k=3):
    """k deterministic values in [-1, 1] for the next serif/counter of the
    current glyph (a small LCG over a hash of (glyph, index))."""
    if not LIFE or _life["glyph"] is None: return [0.0] * k
    _life["n"] += 1
    x = 0
    for ch in "%s#%d" % (_life["glyph"], _life["n"]): x = (x * 131 + ord(ch)) & 0xFFFFFFFF
    out = []
    for _ in range(k):
        x = (x * 1103515245 + 12345) & 0x7FFFFFFF
        out.append((x >> 8) / float(1 << 23) * 2 - 1)
    return out

# ---------------------------------------------------------------- widths
def widths(keys):
    """keys: [(t, width), ...] with t in 0..1 ascending. Smoothstep between
    keys, held flat outside. Returns f(t)."""
    keys = sorted(keys)
    def f(t):
        if t <= keys[0][0]: return keys[0][1]
        if t >= keys[-1][0]: return keys[-1][1]
        for (t0, w0), (t1, w1) in zip(keys, keys[1:]):
            if t0 <= t <= t1:
                u = (t - t0) / (t1 - t0) if t1 > t0 else 1.0
                return w0 + (w1 - w0) * (3 * u * u - 2 * u * u * u)
        return keys[-1][1]
    return f

def pen_widths(center, profile=None, floor=0.0, scale=1.0):
    """The pen's own width along a centerline, as a width function of t --
    the reference, for reading off what to declare (and for the strokes
    that simply ARE the pen: dots, bars)."""
    tans = tangents(center); n = len(center) - 1
    def f(t):
        i = min(n, int(round(t * n))); w = pen.PEN.th(tans[i]) * scale
        if profile: w *= profile(t)
        return max(w, floor)
    return f

# ---------------------------------------------------------------- strokes
def _unfold(side, tans):
    out = [side[0]]
    for i in range(1, len(side)):
        dx, dy = side[i][0] - out[-1][0], side[i][1] - out[-1][1]
        if dx * tans[i][0] + dy * tans[i][1] >= -1e-9: out.append(side[i])
    return out

def stroke(center, width, cut0=None, cut1=None, raw=False, pieces=False, sides=False):
    """A stroke along a centerline: `width` a number or f(t). Ends are
    square faces, or sheared by cut0/cut1 (radians; the family's pen cut is
    pen.CUT). Returns a shapely solid."""
    pts = resample(center) if not raw else list(center)
    tans = tangents(pts); n = len(pts) - 1; L, R = [], []
    wf = width if callable(width) else (lambda t: width)
    for i, (p, tn) in enumerate(zip(pts, tans)):
        w = wf(i / n); nx, ny = -tn[1], tn[0]
        L.append((p[0] + nx * w / 2, p[1] + ny * w / 2)); R.append((p[0] - nx * w / 2, p[1] - ny * w / 2))
    for cut, idx, sgn in ((cut0, 0, 1), (cut1, -1, -1)):
        if cut is None: continue
        tn = tans[idx]; w = wf(0.0 if idx == 0 else 1.0); d = math.tan(cut) * w / 2 * sgn
        L[idx] = (L[idx][0] + tn[0] * d, L[idx][1] + tn[1] * d); R[idx] = (R[idx][0] - tn[0] * d, R[idx][1] - tn[1] * d)
    L = _unfold(L, tans); R = _unfold(R, tans)
    if pieces:
        # a centerline that CROSSES ITSELF (the &, the @'s ring): one polygon
        # would make holes of its crossings, so the stroke is the union of
        # short overlapping pieces, each a simple polygon
        parts = []; step = 6; n2 = min(len(L), len(R))
        for i in range(0, n2 - 1, step):
            j = min(n2, i + step + 2)
            q = L[i:j] + R[i:j][::-1]
            if len(q) >= 3: parts.append(geom.poly(q))
        return geom.union(parts)
    solid = geom.poly(L + R[::-1])
    return (solid, L, R) if sides else solid

def edge_stroke(outer, width, side=1, cut0=None, cut1=None):
    """A stroke drawn from its OUTER edge (the silhouette the designer
    draws) and a declared width toward `side` (+1 = left of travel, -1 =
    right). Returns (solid, inner_edge_points)."""
    pts = resample(outer); tans = tangents(pts); n = len(pts) - 1; inner = []
    wf = width if callable(width) else (lambda t: width)
    for i, (p, tn) in enumerate(zip(pts, tans)):
        w = wf(i / n); nx, ny = -tn[1] * side, tn[0] * side
        inner.append((p[0] + nx * w, p[1] + ny * w))
    inner = _unfold(inner, tans)
    return geom.poly(pts + inner[::-1]), inner

def offset(pts, width, side=1, closed=False):
    """Offset a curve by `width` (number or f(t)) toward `side`."""
    tans = tangents(pts, closed); n = max(1, len(pts) - 1); out = []
    wf = width if callable(width) else (lambda t: width)
    for i, (p, tn) in enumerate(zip(pts, tans)):
        w = wf(i / n); out.append((p[0] - tn[1] * side * w, p[1] + tn[0] * side * w))
    return out

# ---------------------------------------------------------------- serifs
def wedge(A, d, sd, length, depth, drop, edge_at=None, into=None, fillet=FILLET):
    """The family's bracketed wedge, as one polygon that overlaps its stem.
    A: the stem's corner at the end; d: unit direction OUT of the stem's
    end; sd: unit normal pointing out of the stem on the wedge's side.
    The apex sits `length` out along sd and `drop` back along d; the
    bracket is a concave quadratic from the apex to the stem's edge
    `depth` back, tangent to the edge there (control 0.65 of the way up
    the edge). edge_at(dist) gives the stem edge's real point `dist` back
    from A (entasis); default straight."""
    if edge_at is None: edge_at = lambda t: (A[0] - d[0] * t, A[1] - d[1] * t)
    u1, u2, u3, u4 = life(4)
    length *= 1 + LIFE * u1; depth *= 1 + LIFE * u2; drop *= 1 + 1.7 * LIFE * u3; fillet *= 1 + 1.7 * LIFE * u4
    B = (A[0] + sd[0] * length - d[0] * drop, A[1] + sd[1] * length - d[1] * drop)
    C = edge_at(depth)
    ctrl = (A[0] * fillet + C[0] * (1 - fillet), A[1] * fillet + C[1] * (1 - fillet))
    fil = quad(C, ctrl, B)
    # the polygon: down the stem's edge from A to C (real edge), then the
    # bracket out to the apex, the top edge back to A, and a strip inside
    # the stem so the union has no seam.
    inset = into if into is not None else 6.0
    edge = [edge_at(depth * i / 12) for i in range(13)]            # A .. C along the real edge
    inner = [(p[0] - sd[0] * inset, p[1] - sd[1] * inset) for p in edge]
    outline = inner + fil[1:] + [B, A]   # A'..C' inside the stem, C .. bracket .. B, the top edge back to A
    return geom.poly(outline)

# ---------------------------------------------------------------- stems
def stem_width(w0, ent, t):
    """Entasis: the ends swell by `ent` (14%), the waist stays straight --
    a quartic, so the middle 60% of the stem is within 1% of w0 and the
    swell lives in the last fifth at each end, where the brackets are. (The
    record's quadratic waisted the whole stem, visibly at 300 px.)"""
    return w0 * (1.0 + ent * (2 * t - 1) ** 4)

def stem(x, y0, y1, w=None, top=None, foot=None, ent=ENT, ent_span=None, cap=False,   # round 103: `cap` also gates the italic entry/exit
         top_len=1.0, top_depth=1.0, foot_len=FOOT, foot_depth=1.0, top_drop=1.0, foot_drop=0.6,
         top_scale=1.0, cut_top=None, it_entry=None, it_exit=None, it_exit_len=1.0):   # round 106: None = the italic's default, False = never (an arch IS its second stem's entry)
    """A vertical stem from y0 to y1 with entasis, its wedges as part of the
    same solid. w: mid width (default the pen's vertical, x1.137 for cap).
    top: None | 'left' | 'right' | 'both' | 'left+' | 'right+' ('+' adds the
    small 0.4 x 0.6 wedge the other way: the I, the U's right stem).
    foot: None | 'both' | 'left' | 'right'. ent_span: (ylo, yhi) the entasis
    is computed over when the drawn stem is a piece of a longer one (the
    n's right stem ends inside its arch). cut_top: shear the top face by
    this angle (radians) instead of a square end."""
    if w is None: w = TH_V * (pen.CAP_STEM if cap else 1.0)
    lo, hi = ent_span or (y0, y1)
    def wid(y): return stem_width(w, ent, (y - lo) / (hi - lo) if hi > lo else 0.5)
    ys = [y0 + (y1 - y0) * i / geom._n(abs(y1 - y0), geom.SPACING) for i in range(geom._n(abs(y1 - y0), geom.SPACING) + 1)]
    left = [(x - wid(y) / 2, y) for y in ys]; right = [(x + wid(y) / 2, y) for y in ys]
    if cut_top is not None:
        d = math.tan(cut_top) * wid(y1) / 2
        left[-1] = (left[-1][0], y1 + d); right[-1] = (right[-1][0], y1 - d)
    body = geom.poly(left + right[::-1])
    parts = [body]
    wl = WL * (pen.CAP_STEM if False else 1.0)   # the family's wedge is one size in both cases (round 22)
    wd = WD
    def edge_fn(side, at_top):
        # the real stem edge, `dist` back from the end on `side` (-1 left, +1 right)
        def f(dist):
            y = y1 - dist if at_top else y0 + dist
            return (x + side * wid(y) / 2, y)
        return f
    if top:
        main = -1 if top in ("left", "left+", "both") else +1
        sides = [main] + ([-main] if top in ("both", "left+", "right+") else [])
        if pen.ITALIC and pen.IT_ENTRY and it_entry is not False and not cap and y1 > 0 and abs(y0) < 1.0:
            sides = [sd for sd in sides if sd > 0]   # the entry replaces the LEFT top wedge, as the exit replaces the right foot
        for i, sd in enumerate(sides):
            small = (top in ("left+", "right+")) and i == 1
            L_ = wl * (0.4 if small else top_len) * top_scale; D_ = wd * (0.6 if small else top_depth); dr = DROP * (0.4 if small else top_drop)
            A = (x + sd * wid(y1) / 2, y1)
            parts.append(wedge(A, (0, 1), (sd, 0), L_, D_, dr, edge_at=edge_fn(sd, True)))
    if foot:
        sides = {"both": (-1, 1), "left": (-1,), "right": (1,)}[foot]
        # round 103: a calligraphic exit REPLACES the right foot, it does not
        # stand beside it. The first cut kept both and the feet grew barbs --
        # a spur down-right off every m, n, i and u, which reads as thorns and
        # is the opposite of flowing.
        if pen.ITALIC and pen.IT_EXIT and it_exit is not False and not cap and abs(y0) < 1.0:
            sides = tuple(sd for sd in sides if sd < 0)
        for sd in sides:
            A = (x + sd * wid(y0) / 2, y0)
            parts.append(wedge(A, (0, -1), (sd, 0), wl * foot_len, wd * foot_depth, DROP * foot_drop, edge_at=edge_fn(sd, False)))
    # ---------------------------------------------------------------- round 103
    # THE CALLIGRAPHIC ENTRY AND EXIT (owner: "much more calligraphic flowing
    # strokes"). A written italic does not start and stop: the pen arrives into
    # a stem from the previous letter and leaves it toward the next, and those
    # two flicks are most of what makes a page of italic look written rather
    # than sheared. They are added HERE, on the stem, rather than per letter,
    # so every lowercase stem that stands on the baseline gets them and none
    # of the capitals or figures do (`cap` gates that).
    if pen.ITALIC and not cap and abs(y0) < 1.0:
        if pen.IT_EXIT and it_exit is not False:
            # round 218: it_exit_len scales THIS stem's flick only. pen.IT_EXIT
            # is the family's and drives every lowercase foot; the 1 needed a
            # shorter one and nothing else did.
            L = S * pen.IT_EXIT * it_exit_len
            xe = x + wid(y0) / 2
            # GLITCH SWEEP 2026-09-16 -- THE SAME UNBURIED FACE AT THE FOOT.
            # Round 103 cured one barb here by dropping the right foot wedge
            # ("the feet grew barbs ... reads as thorns"); the other half was
            # still standing. The exit's start face is 0.92 x the stem wide
            # across a run that leaves almost horizontally, so the face is
            # nearly VERTICAL and its LOWER corner hung 26.0 units under the
            # baseline as a downward point, with a re-entrant step where the
            # stem's flat bottom met it. Swept: S*0.16 (what shipped) reaches
            # -26.0, S*0.25 -17.1, S*0.35 -7.7 and S*0.45 +1.5 -- the first
            # value that puts the whole face inside the stem's own ink.
            # IT_START_BURY is that start height, x S. It costs the flick its
            # root below the baseline (the ink outside the stem falls 1866 ->
            # 1216 units^2 and stops reaching left of the stem's right edge),
            # which is the barb and the wrap around the foot's corner going
            # together: the flick now leaves the stem at its edge, which is
            # what the round-103 comment says it is for.
            path = cubic((xe - wid(y0) * 0.34, y0 + S * IT_START_BURY), (xe + L * 0.22, y0 + S * 0.02),
                         (xe + L * 0.66, y0 + L * 0.26), (xe + L * 1.02, y0 + L * 0.82))
            parts.append(stroke(path, widths([(0.0, wid(y0) * 0.92), (0.45, max(S * 0.34, S * pen.IT_TIP)), (1.0, S * pen.IT_TIP)]), cut0=None))
        if pen.IT_ENTRY and it_entry is not False and (top or y1 > 0):
            L = S * pen.IT_ENTRY
            xs_ = x - wid(y1) / 2
            # The entry arrives TANGENTIALLY, running nearly along the stem's
            # own direction as it lands. The first cut came in steeply and every
            # stem top in "minimum" grew a thorn -- the exit's own mistake, at
            # the other end of the letter.
            #
            # GLITCH SWEEP 2026-09-16 -- AND IT STILL GREW ONE, at the OTHER
            # end of the same stroke. The entry's far end is a SQUARE face
            # (`cut1=None`) across a stroke 0.88 x the stem wide, and the face
            # is perpendicular to a nearly-horizontal run, so its upper corner
            # stood 20.5 units ABOVE the stem's flat top over a 52-unit span --
            # 329 units^2 of pointed tab past the ink it was meant to be buried
            # in, the same defect and the same measurement as the 1's flag in
            # round 75 (`figures.ONE_FLAG_BURY`). Visible on the 1 and the 4 at
            # 500 px as a second, taller peak to the right of the entry flag
            # with a valley between them.
            #
            # IT_END_BURY is how far below the stem's top the end CENTRE sits,
            # in stem widths of S. Swept: S*0.18 (the old value) leaves 329
            # units^2 above the top, S*0.30 leaves 54, S*0.35 leaves 0.7, and
            # S*0.45 clears it by 1.9 units -- enough that the cut's facets,
            # which shave ~0.4 (see `figures.FOUR_OPEN_GAP`), cannot put the
            # corner back over the line. The flag LEFT of the stem is what the
            # reader sees and it is unchanged in shape: its bbox stays at the
            # stem's own left edge, and it only loses the 150 units^2 the tab
            # was adding on the far side.
            path = cubic((xs_ - L * 0.95, y1 - L * 0.40), (xs_ - L * 0.55, y1 - L * 0.14),
                         (xs_ - L * 0.18, y1 - S * 0.02), (xs_ + wid(y1) * 0.26, y1 - S * IT_END_BURY))
            parts.append(stroke(path, widths([(0.0, S * pen.IT_TIP), (0.62, max(S * 0.28, S * pen.IT_TIP)), (1.0, wid(y1) * 0.88)]), cut1=None))
    return geom.union(parts)

def stem_edge_x(x, w, ent, y, lo, hi, side):
    """x of a stem's edge at height y (entasis over lo..hi)."""
    return x + side * stem_width(w, ent, (y - lo) / (hi - lo)) / 2

def diag_wedge(p_end, d_out, sd, scale=0.9, drop=DROP):
    """The wedge at a diagonal's end (A V W X Y K k v w x y): 0.9 x 0.9 of
    the family's, on the outer side. p_end is the stroke's end CORNER on
    that side, d_out the unit direction out of the stroke's end."""
    return wedge(p_end, d_out, sd, WL * scale, WD * scale, drop)

def end_wedge(pts, w, at_start, side, scale=0.9):
    """The diagonal wedge at one end of a stroke: side +1/-1 is taken on
    the normal of the direction OUT of that end (the record's convention:
    +1 on a diagonal's top-left end points up-left)."""
    tn = tangents(pts)
    d = (-tn[0][0], -tn[0][1]) if at_start else tn[-1]
    nrm = (-d[1], d[0]); sd = (nrm[0] * side, nrm[1] * side)
    P = pts[0] if at_start else pts[-1]
    A = (P[0] + sd[0] * w / 2, P[1] + sd[1] * w / 2)
    return diag_wedge(A, d, sd, scale)

def diagonal(p0, p1, w, serif0=None, serif1=None, cut0=None, cut1=None):
    """A straight stroke p0 -> p1 of width w (number or f(t)); serif0/serif1:
    +1/-1 = a diagonal wedge at that end, on the side named as end_wedge does."""
    pts = line(p0, p1)
    wf = w if callable(w) else (lambda t: w)
    parts = [stroke(pts, wf, cut0=cut0, cut1=cut1)]
    if serif0: parts.append(end_wedge(pts, wf(0.0), True, serif0))
    if serif1: parts.append(end_wedge(pts, wf(1.0), False, serif1))
    return geom.union(parts)

def bar(x0, x1, y, w, align="center", cut0=None, cut1=None, wedges=(), prof=None):
    """A horizontal bar. align: 'center' | 'top' | 'bottom' (which edge sits
    on y). wedges: [(end, side)] with end 'left'|'right' and side +1 (rising)
    or -1 (hanging) -- the bar-end wedge, 0.85 x 0.9 of the family.

    prof: round 219. A width profile in t, so a bar can MODULATE the way every
    other stroke in the face does -- `w` stays the width at the end the wedge
    hangs from, and the named edge stays straight while the other one moves.
    None is the flat bar, byte for byte."""
    if prof is not None:
        sgn = -1.0 if align == "top" else (1.0 if align == "bottom" else 0.0)
        n = max(8, geom._n(abs(x1 - x0), geom.SPACING))
        wf = lambda t: w * prof(t)
        pts = [(x0 + (x1 - x0) * i / n, y + sgn * wf(i / n) / 2) for i in range(n + 1)]
        parts = [stroke(pts, wf, cut0=cut0, cut1=cut1)]
        yc = y + sgn * w / 2          # the wedge hangs off the END, where w is w
        for end, side in wedges:
            if end == 'left':
                sh = math.tan(cut0) * w / 2 if cut0 is not None else 0.0
                A = (x0 + side * sh, yc + side * w / 2); d = (-1, 0)
            else:
                sh = math.tan(cut1) * w / 2 if cut1 is not None else 0.0
                A = (x1 - side * sh, yc + side * w / 2); d = (1, 0)
            parts.append(wedge(A, d, (0, side), WL * 0.85, WD * 0.9, 0.0))
        return geom.union(parts)
    yc = y - w / 2 if align == "top" else (y + w / 2 if align == "bottom" else y)
    pts = line((x0, yc), (x1, yc)); parts = [stroke(pts, w, cut0=cut0, cut1=cut1)]
    for end, side in wedges:
        # the bar's end face is sheared by cut0/cut1 (stroke() moves the
        # top corner back and the bottom corner forward by tan(cut) x w/2),
        # so the wedge must start at the SHEARED corner -- at the plain
        # corner its flat top overran the face and left a notch (owner,
        # 2026-09-13, "fix these weird glitches", on the variety audit's
        # bar-end blocks of E F L Z 2).
        if end == 'left':
            sh = math.tan(cut0) * w / 2 if cut0 is not None else 0.0
            A = (x0 + side * sh, yc + side * w / 2); d = (-1, 0)
        else:
            sh = math.tan(cut1) * w / 2 if cut1 is not None else 0.0
            A = (x1 - side * sh, yc + side * w / 2); d = (1, 0)
        parts.append(wedge(A, d, (0, side), WL * 0.85, WD * 0.9, 0.0))
    return geom.union(parts)

# ---------------------------------------------------------------- rounds

# ROUND 270 -- NO INDENTATIONS IN THE COUNTERS AT THE 700 AND THE 900. Owner
# 2026-09-19, verbatim: "for 700 and 900, counters should not have
# indentations in their counters." A ring's counter is the outer offset
# inward by the pen's width at each tangent, and the width swings with the
# stress: at the 400 the swing is small and the counter stays convex; at
# 116 and 148 the thick sides push in 7-18 units further than the thin top
# and bottom and the counter of an 8, g, o, 6, a, q or @ becomes an
# hourglass, dented at 3 and 9 o'clock (`cmp_counter_dents.py` measures it;
# the 400s read 0 dents, the 700 nine, the 900 seventeen). The cure is the
# ruling stated as geometry: above stem 84 the counter is its own convex
# hull, one Chaikin pass to round the chord ends, and nothing else moves --
# the outer is untouched, so the ink that filled the dent is the only ink
# that goes, and the wall at the dent thins by the dent's depth. At and
# under 84 the counter is exactly the offset it always was, so the 200 and
# the 400s are byte-identical. ALBO_COUNTER_CONVEX=0 turns it off.
COUNTER_CONVEX = float(os.environ.get('ALBO_COUNTER_CONVEX', 1.0))

def convex_counter(inner):
    """The counter's convex hull, resampled and lightly smoothed, in the
    input's winding."""
    from shapely.geometry import Polygon as _P
    hull = list(_P(inner).convex_hull.exterior.coords)[:-1]
    if geom.signed_area(hull) * geom.signed_area(inner) < 0: hull = hull[::-1]
    # start the hull at the point nearest the input's first point, so the
    # caller's t = 0 stays where it was
    i0 = min(range(len(hull)), key=lambda i: math.dist(hull[i], inner[0]))
    hull = hull[i0:] + hull[:i0]
    hull = smooth(hull, 1, closed=True)
    return resample(hull + [hull[0]])[:-1]

def convex_holes(g):
    """Every enclosed counter of a finished glyph made its own convex hull
    (round 272) -- for the counters that are strokes and not rings, where
    `convex_counter` cannot reach. Ink inside a counter's hull is removed;
    nothing else moves."""
    from shapely.geometry import Polygon as _P
    polys = list(g.geoms) if g.geom_type == 'MultiPolygon' else [g]
    out = []
    for poly in polys:
        holes = [list(_P(r).convex_hull.exterior.coords)[:-1] for r in poly.interiors]
        holes = [smooth(h, 1, closed=True) for h in holes]
        out.append(geom.poly(list(poly.exterior.coords), holes))
    return geom.union(out)

def ring(cx, cy, rx, ry, k=pen.BOWL_K, w_scale=1.0, floor=0.0, rot=0.0, counter_smooth=2, a0=0.0, a1=2 * math.pi, con=1.0, stress=0.0, oval=0.0, nib=None):
    """A full bowl: the OUTER is the designed superellipse (k = squareness);
    the COUNTER is its inward offset by the pen's width at each tangent
    (x w_scale, never under `floor`), smoothed so it reads as a drawn
    curve. Carries the pen's stress: sides at the vertical width, top and
    bottom at the horizontal, thinnest at 11 and 5 o'clock. Returns
    (solid, outer_pts, inner_pts)."""
    u1, u2 = life(2)
    k = k * (1 + LIFE * u1); rot = rot + math.radians(10 * LIFE * u2)
    outer = superellipse(cx, cy, rx, ry, a0, a1, k, rot=rot)[:-1]
    tans = tangents(outer, closed=True)
    # `con` RE-SPREADS THE RING'S OWN WIDTHS about their geometric mean before
    # the floor is applied: w' = mean * (w/mean) ** con. 1.0 is the family's
    # bowl profile untouched and every existing caller gets exactly that; above
    # 1 the thicks thicken and the thins thin, in proportion, WITHOUT moving the
    # family's BOWL_HAIR / BOWL_MAX -- which is the point, since those are
    # shared with every bowl in both faces and a letter that needs more contrast
    # than its family is a letter, not a new family.
    # `stress` ROTATES THE NIB, not the ring. `rot` turns the superellipse and
    # its tangents together, so the stress travels with the shape and the axis
    # does not move -- the same trap the g's G_SKEW turned out to be in round
    # 203. Rotating the TANGENT before the width lookup is the real lever: the
    # ring keeps its shape and the thick moves round it.
    if stress:
        _c, _s = math.cos(stress), math.sin(stress)
        _t = [(t[0] * _c - t[1] * _s, t[0] * _s + t[1] * _c) for t in tans]
    else:
        _t = tans
    if nib is None:
        ws = [bowl_th(tn) * w_scale for tn in _t]
    else:
        # ROUND 305 -- THE RING ON A TRUE NIB. `bowl_th` is already a function
        # of the tangent, so the family's bowl IS a pen -- but one whose hair
        # is 0.70 of its max (profile B, the owner's round-58 ruling), which
        # caps a ring at about 1.4:1 however it is cut. A nib states its own
        # thin and its own ANGLE: width = thin + (thick - thin) * |sin(dir -
        # phi)|, the same law `glyphs/aldine.nib` uses, which is what round 182
        # put the g's rings on and what round 195 said the 8's rings want.
        #
        # It is NOT `con`: con re-spreads the widths a profile already produced,
        # about their geometric mean, so the thin stays where the profile put it
        # and only gets thinner -- which is why it dents a counter. A nib moves
        # WHERE the thin falls, with the stroke's direction.
        _thick, _thin, _phi = nib
        ws = []
        for tn in _t:
            _d = math.degrees(math.atan2(tn[1], tn[0]))
            ws.append(S * w_scale * (_thin + (_thick - _thin)
                                     * abs(math.sin(math.radians(_d - _phi)))))
    if con != 1.0 and ws:
        import math as _m
        gm = _m.exp(sum(_m.log(max(w, 1e-6)) for w in ws) / len(ws))
        ws = [gm * (w / gm) ** con for w in ws]
    inner = []
    for p, tn, w in zip(outer, tans, ws):
        w = max(w, floor)
        inner.append((p[0] - tn[1] * w, p[1] + tn[0] * w))   # inward: the LEFT normal of a ccw outer
    inner = _unfold(inner, tans)
    inner = smooth(inner, counter_smooth, closed=True)
    inner = resample(inner + [inner[0]])[:-1]
    if S > 84.0 and COUNTER_CONVEX:      # round 270, see convex_counter
        inner = convex_counter(inner)
    # `oval` PULLS THE COUNTER ONTO ITS OWN ELLIPSE -- round 204's cure for the
    # g's bowl, and the one thing that lets a ring carry real contrast. The
    # counter is the outer offset inward by the width, so a width that swings
    # twice as far swings the counter with it and it dents; the 8's own note
    # records that smoothing does NOT fix that, and it does not.
    if oval:
        inner = ovalise(inner, outer, oval, 0.0)
    solid = geom.poly(outer, [inner[::-1]])
    return solid, outer, inner

def _fit_ellipse(pts):
    """Least-squares conic through a near-elliptical closed contour.
    Returns (cx, cy, Q) where Q is the 2x2 form with (p-c)Q(p-c) = 1."""
    import numpy as np
    P = np.asarray(pts, float)
    c0 = P.mean(axis=0)
    x, y = (P[:, 0] - c0[0]), (P[:, 1] - c0[1])
    # a x^2 + b xy + c y^2 + d x + e y = 1
    D = np.column_stack([x * x, x * y, y * y, x, y])
    sol, *_ = np.linalg.lstsq(D, np.ones_like(x), rcond=None)
    a, b, c, d, e = sol
    M = np.array([[a, b / 2.0], [b / 2.0, c]])
    if np.linalg.det(M) <= 1e-12:          # not an ellipse -- leave it alone
        return None
    # centre of the conic, then renormalise so the form is exactly 1 on it
    ctr = np.linalg.solve(2 * M, -np.array([d, e]))
    k = 1.0 + float(ctr @ M @ ctr + np.array([d, e]) @ ctr)
    if k <= 1e-9:
        return None
    return (c0[0] + ctr[0], c0[1] + ctr[1], M / k)


def ovalise(inner, outer, amount=1.0, wall_min=0.0, hand=None, counter_smooth=2):
    """ROUND 204 -- PULL A COUNTER ONTO ITS OWN BEST-FIT ELLIPSE.

    `ring_from` builds the counter by offsetting the outer inward by the
    stroke's width at each point. That is the right construction for the WALL
    and the wrong one for the WHITE: every kink in the width table, every hand
    press and every fast turn lands in the counter as a facet or a corner, and
    at a high contrast the counter stops being a shape and becomes the residue
    of one. Owner 2026-09-17: *"smooth out counters to be even oval"*.

    So the counter is fitted with an ellipse and each point is pulled onto it.
    `amount` 1.0 is the ellipse exactly, 0.0 the offset contour untouched.
    The outer does not move, so ALL of the contrast now lives in the wall,
    which is what a pen actually does -- the white it leaves is even and the
    black around it is not.

    `wall_min` is the guard: a point is never pulled so far that the wall
    thins past it (measured to the outer, in the same units). `hand` is a
    (degrees, dr) table pressed into the finished oval, because an ellipse
    drawn by a machine is not what this face is.
    """
    import numpy as np
    fit = _fit_ellipse(inner)
    if not fit:
        return inner
    cx, cy, Q = fit
    out = np.asarray(outer, float)
    res = []
    for px, py in inner:
        ux, uy = px - cx, py - cy
        u = np.array([ux, uy])
        q = float(u @ Q @ u)
        if q <= 1e-12:
            res.append((px, py)); continue
        t = 1.0 / math.sqrt(q)              # the ellipse along this point's own ray
        ex, ey = cx + ux * t, cy + uy * t
        a = amount
        if wall_min > 0.0:
            # back the blend off until the wall holds
            for _ in range(6):
                bx, by = px + (ex - px) * a, py + (ey - py) * a
                d = float(np.min(np.hypot(out[:, 0] - bx, out[:, 1] - by)))
                if d >= wall_min or a <= 0.0:
                    break
                a *= 0.5
        res.append((px + (ex - px) * a, py + (ey - py) * a))
    if hand:
        pressed = []
        for px, py in res:
            ang = math.degrees(math.atan2(py - cy, px - cx)) % 360.0
            dr = _table_at(hand, ang)
            L = math.hypot(px - cx, py - cy) or 1.0
            pressed.append((px + (px - cx) / L * dr, py + (py - cy) / L * dr))
        res = pressed
    res = smooth(res, counter_smooth, closed=True)
    return resample(res + [res[0]])[:-1]


def _table_at(table, ang):
    """(degrees, value) read periodically, cosine-interpolated."""
    ks = sorted((float(d) % 360.0, float(v)) for d, v in table)
    ang %= 360.0
    for i in range(len(ks)):
        a0, v0 = ks[i]
        a1, v1 = (ks[0][0] + 360.0, ks[0][1]) if i == len(ks) - 1 else ks[i + 1]
        if a0 <= ang <= a1:
            f = (ang - a0) / (a1 - a0) if a1 > a0 else 0.0
            f = 0.5 - 0.5 * math.cos(math.pi * f)
            return v0 + (v1 - v0) * f
    return ks[0][1]


def ring_from(outer, w_scale=1.0, floor=0.0, widths_fn=None, counter_smooth=2, post_inner=None, smooth_w=0):
    """A bowl from a DESIGNED closed outer path (ccw): the counter is the
    inward offset by the pen's width at each tangent (or widths_fn(t)),
    smoothed. Returns (solid, outer, inner)."""
    outer = resample(outer + [outer[0]])[:-1]
    tans = tangents(outer, closed=True); n = len(outer); inner = []
    ws = [widths_fn(i / n) if widths_fn else max(pen.PEN.th(tn) * w_scale, floor) for i, tn in enumerate(tans)]
    if smooth_w:   # the pen's width sequence, moving-averaged over +-smooth_w samples (a tight turn steps it)
        ws = [sum(ws[(i + k) % n] for k in range(-smooth_w, smooth_w + 1)) / (2 * smooth_w + 1) for i in range(n)]
    for i, (p, tn) in enumerate(zip(outer, tans)):
        w = ws[i]
        inner.append((p[0] - tn[1] * w, p[1] + tn[0] * w))
    inner = _unfold(inner, tans)
    if post_inner: inner = [post_inner(p) for p in inner]
    inner = smooth(inner, counter_smooth, closed=True)
    inner = resample(inner + [inner[0]])[:-1]
    if S > 84.0 and COUNTER_CONVEX:      # round 270, see convex_counter
        inner = convex_counter(inner)
    return geom.poly(outer, [inner[::-1]]), outer, inner

BOWL_HAIR, BOWL_MAX, BOWL_POW = 0.42, 1.18, 1.7    # round 57's D-family profile, fitted to Van den Keere's rays (kept for the record; the shipping font)
# Round 58 (owner: "a wedge serif like Albertus, but more readable" -- not
# Van den Keere): the bowl profile is a SWITCH. None = the pen (the 26-degree
# nib, round 56's bowls); a dict = a vertically stressed profile applied to
# EVERY bowl (D B P R, O Q C G, o c e b d p q g): hair and max over the stem,
# the exponent, the taper of a bowl's ends into its stem (x the hair), the
# round end's superellipse exponent, and for variant C the free terminals'
# widening (fraction, span) into the family's cut.
DEFAULT_BOWL = 'B'   # owner's pick, round 58 (2026-09-13): 'Albertus-like firm'; the family is Albo from this round
BOWL_OPTIONS = {
    'A': dict(name='Albertus-like moderate', hair=0.62, max=1.02, pow=1.4, taper=0.75, k=2.0, widen=None),
    'B': dict(name='Albertus-like firm', hair=0.70, max=1.00, pow=1.6, taper=0.85, k=1.9, widen=None),
    'C': dict(name='Glyphic near-monoline', hair=0.78, max=0.98, pow=2.0, taper=0.90, k=2.0, widen=(0.15, 0.12)),
    'D': dict(name='Albertus-measured', hair=0.75, max=1.05, pow=1.5, taper=0.85, k=2.0, widen=None, stress=20.0, arch_floor=1.0),
    'VDK': dict(name='round 57, Van den Keere fit', hair=0.42, max=1.18, pow=1.7, taper=0.7, k=2.0, widen=None),
}
# 'stress': degrees the profile's maximum sits above 3 o'clock (Albertus's O
# peaks at +20); 'arch_floor': the n m h u arches never thin below this x stem.

def bowl_hair():
    """The current bowl profile's thin, in units (the waist bar of the B)."""
    return S * (BOWL['hair'] if BOWL else BOWL_HAIR)
def set_bowl(key):
    """None = the ruled default (B); 'pen' = the 26-degree nib at each tangent (round 56)."""
    global BOWL
    BOWL = None if key == 'pen' else dict(BOWL_OPTIONS[DEFAULT_BOWL if key is None else key])
BOWL = dict(BOWL_OPTIONS[DEFAULT_BOWL])
if os.environ.get('FJORD_ARCH_FLOOR'): BOWL['arch_floor'] = float(os.environ['FJORD_ARCH_FLOOR'])   # round 60 ladder override: the n m h u arches never thin below this x stem
# The bowl hair follows the contrast (round 61's rule, applied at the
# default too since round 63): hair fraction 1 - 0.5 c -- B's own 0.70 at
# the 0.60 it was picked at, 0.60 at 0.80, 0.525 at 0.95, 0.50 at 1.00; the
# max unchanged.
BOWL['hair'] = 1.0 - 0.5 * pen.CONTRAST
# ROUND 264 -- THE CONTRAST DIAL CANNOT REACH A REAL CONTRAST, and the line
# above is why. Owner 2026-09-19 asked for Albo's contrast to be redrawn
# toward the reference faces. Measured first, on a ladder of FJORD_CONTRAST at
# the 400: the dial from 0.80 to 0.98 moves the built thick:thin only 1.32 to
# 1.50, because `1 - 0.5c` bottoms out at 0.50 of the stem even at c = 1.0 --
# a 2:1 bowl at the absolute end of the axis, and about 1.5:1 as the letters
# actually measure. The reference regulars run 1.49 to 3.00 with a median of
# 2.34 (docs/albo-family-2026-09-19.md section 9), so the architecture, not
# the setting, is what holds Albo flat.
# ALBO_BOWL_HAIR sets the fraction DIRECTLY, bypassing the mapping. Unset, the
# line above stands and every build is byte-identical.
# ROUND 265 -- THE RULING. Owner 2026-09-19, on the twenty-build dialling
# page: *"around 1.7 wins"*. That is step 2 of the grid, bowl hair 0.46 with
# the o's floor at 0.50, which measures 1.70 / 1.71 / 1.68 / 1.69 at the 200 /
# 400 / 700 / 900 -- inside the reference regulars' 1.49-3.00 where the face
# used to sit under all of them at 1.32. The `1 - 0.5c` line above is kept as
# the history of how the dial used to be derived; it no longer decides.
BOWL['hair'] = float(os.environ.get('ALBO_BOWL_HAIR', 0.46))

def bowl_th(tn):
    """Width of a bowl stroke at tangent tn: the switched profile, or the pen."""
    if BOWL is None: return pen.PEN.th(tn)
    phi = math.atan2(tn[1], tn[0]) - math.radians(BOWL.get('stress', 0.0))
    return S * (BOWL['hair'] + (BOWL['max'] - BOWL['hair']) * abs(math.sin(phi)) ** BOWL['pow'])

def bowl_widths(center, profile=None, floor=0.0, stress=0.0, con=1.0):
    """Like pen_widths, on the bowl profile (the pen when none is set).

    `stress` rotates the NIB the width is read from (radians) and `con`
    re-spreads the resulting widths about their geometric mean, the same two
    levers `ring` carries -- so an open stroke can be given a letter's axis and
    cut without redrawing its path."""
    tans = tangents(center); n = len(center) - 1
    if stress:
        _c, _s = math.cos(stress), math.sin(stress)
        tans = [(t[0] * _c - t[1] * _s, t[0] * _s + t[1] * _c) for t in tans]
    _gm = None
    if con != 1.0:
        _w = [bowl_th(t) for t in tans]
        _gm = math.exp(sum(math.log(max(w, 1e-6)) for w in _w) / max(len(_w), 1))
    def f(t):
        i = min(n, int(round(t * n))); w = bowl_th(tans[i])
        if _gm is not None: w = _gm * (w / _gm) ** con
        if profile: w *= profile(t)
        return max(w, floor)
    return f

def widen_terminal(profile_fn, at_start=False):
    """Variant C: a free terminal widens 15% over its last 12% (first 12% if
    at_start) into the family's cut. Returns the composed profile."""
    if BOWL is None or not BOWL.get('widen'): return profile_fn
    amt, span = BOWL['widen']
    def f(t):
        u = (t if not at_start else 1 - t)
        w = profile_fn(t) if profile_fn else 1.0
        if u > 1 - span: v = (u - (1 - span)) / span; w *= 1 + amt * (3 * v * v - 2 * v ** 3)
        return w
    return f
BOWL_ARC = 1.0     # the round end's x radius over the bowl's half height (a semicircle); a 12-cell grid over 0.65-1.0 x exponent 1.28-2.2 against VdK's D P R rays put 1.0 / 1.7 best (sum |delta| 141 of 27 cells)
BOWL_ARC_K = 2.0   # the end is a true round; the "squared shoulders" are the flat runs

def bowl_profile(tan):
    """Stroke width of a D-family bowl by its TANGENT: measured on Van den
    Keere's D P B (ray-cast at 1000 px from the bowl's centre), the bowl is
    VERTICALLY stressed -- the maximum where the stroke runs vertical (3
    o'clock), symmetric above and below, heavier than the stem (97 against
    82), falling steeply to a true thin wherever it runs horizontal (34,
    0.42 of the stem -- the whole top and bottom, from the stem to the
    shoulder): w = hair + (max - hair) |sin phi|^1.28, phi the tangent's
    angle. Not the 26-degree nib's profile, which peaks at 2 o'clock and
    only falls to ~60. (A first version took the angle from the half
    superellipse's own centre, which sits at the stem, so the top stroke
    thickened from the stem outward and the rays read ~100 everywhere.)"""
    if BOWL is not None: return bowl_th(tan)
    phi = math.atan2(tan[1], tan[0])
    return S * (BOWL_HAIR + (BOWL_MAX - BOWL_HAIR) * abs(math.sin(phi)) ** BOWL_POW)

def half_bowl(edge, y_top, y_bot, rx, k=pen.BOWL_K * 1.12, open_bottom=0.0, w_scale=1.0, into=22.0, taper=0.7, taper_span=0.08):
    """The D's bowl (rulings, rounds 36/47) on the measured profile (owner,
    2026-09-13, "take another pass at B and related characters"): the
    CENTERLINE is the designed half superellipse from the stem's inner
    edge -- squared shoulders (k x 1.12), outer edges ON y_top and y_bot --
    and the width at every point is bowl_profile(angle from the bowl's
    centre): a hairline leaving the stem at the top, the maximum at 3
    o'clock, a hairline returning at the bottom. Both ends run `into` the
    stem and ease to `taper` of the hairline there, so the end faces lie
    inside the stem's ink. The opened bottom (ruling) is a modest
    asymmetry now: the counter's lower half lifted by open_bottom x the
    horizontal stroke (Van den Keere's own bottom is 38 against a top of
    46). Returns (solid, cx, cy, rx_c, ry_c, L, R)."""
    hair = S * (BOWL['hair'] if BOWL else BOWL_HAIR); mx = S * (BOWL['max'] if BOWL else BOWL_MAX)
    if BOWL: taper = BOWL['taper']
    ry_c = (y_top - y_bot) / 2 - hair / 2; rx_c = rx - mx / 2
    cy = (y_top + y_bot) / 2; cx = edge + rx * 0.05
    # Van den Keere's bowl, measured (2026-09-13): a FLAT run from the stem
    # along the top, a round end, a flat run back along the bottom -- so the
    # thin holds all the way to the shoulder and the weight sits on the
    # belly. The arc's x radius is the bowl's half height (a round end),
    # the flat runs take up the rest of the fixed width.
    arc_rx = min(rx_c, ry_c * BOWL_ARC); flat = rx_c - arc_rx; ax = cx + flat
    arc = superellipse(ax, cy, arc_rx, ry_c, -math.pi / 2, math.pi / 2, BOWL['k'] if BOWL else BOWL_ARC_K)
    center = [(edge - into, cy - ry_c)] + arc + [(edge - into, cy + ry_c)]
    center = resample(center)
    n = len(center) - 1
    if open_bottom:
        def win(t): return max(0.0, math.sin(math.pi * (t - 0.04) / 0.46)) if 0.04 <= t <= 0.50 else 0.0
        center = [(px, py + 0.5 * open_bottom * TH_H * win(i / n)) for i, (px, py) in enumerate(center)]
    tans = tangents(center)
    def wfn(t):
        i = min(n, int(round(t * n)))
        w = bowl_profile(tans[i]) * w_scale
        if open_bottom: w += open_bottom * TH_H * win(t)
        if t < taper_span: u = t / taper_span; w *= taper + (1 - taper) * (3 * u * u - 2 * u ** 3)
        elif t > 1 - taper_span: u = (1 - t) / taper_span; w *= taper + (1 - taper) * (3 * u * u - 2 * u ** 3)
        return w
    solid, L, R = stroke(center, wfn, raw=True, sides=True)
    return solid, cx, cy, rx_c, ry_c, L, R

def beak(pts, w, at_start=True, cut_deg=-28.0, lip=(0.4, 0.7)):
    """The C/G/S beak (round 42, Van den Keere): the terminal's face is
    sheared toward the vertical and a SHORT lip hangs from the face's inner
    corner into the aperture -- a bracket wedge at 0.4 x 0.7 of the family.
    Returns the lip polygon; the caller shears the face with the same cut."""
    tn = tangents(pts)
    d = (-tn[0][0], -tn[0][1]) if at_start else tn[-1]
    nrm = (-d[1], d[0]); P = pts[0] if at_start else pts[-1]
    dd = math.tan(math.radians(cut_deg)) * w / 2
    # the face's inner corner after the cut (stroke() moves L forward, R back at the start)
    P0 = (P[0] - d[0] * dd, P[1] - d[1] * dd)
    A = (P0[0] - nrm[0] * w / 2, P0[1] - nrm[1] * w / 2)
    return wedge(A, d, (-nrm[0], -nrm[1]), WL * lip[0], WD * lip[1], 0.0)

# ---------------------------------------------------------------- the c's top finial
# ROUND 275 -- THE ROUND FINIALS TAKE THE c's TOP. Owner 2026-09-19: *"change
# out round finials (like c top serif)"*, and on round 273's ladder of five
# ends for that top: *"a works but my ask was about the round finials"* -- so
# the c's top AS DRAWN is the model, and the ball and teardrop ends elsewhere
# in the roman become it. That top (rounds.g_c, despurred in R18) is two
# numbers and a face: the stroke SWELLS to 1.10 of the pen over its first 13%
# and ends on a face sheared 28 degrees toward the vertical, no lip. What the
# converted ends had been, measured on the built 400 and 700 before this: a
# flare of 1.15-1.3 of the pen over the last 25-45% of the stroke into the
# family's 20-degree pen cut (f r y a J), or a 1.1-1.25 flare into the same
# cut (2 3 5) -- a long flare into a face lying ACROSS the stroke, which is
# what read as a ball. These three are the ONE definition; a glyph composes
# them and declares no swell, span or face of its own, so a later change is
# one place. The c itself draws its top through them (rounds.g_c) and is
# byte-identical to before.
FINIAL_SWELL = 1.10   # the end's width, x the stroke's own width there
FINIAL_SPAN = 0.13    # the swell rises over this fraction of the stroke's length
FINIAL_CUT_DEG = 28.0 # the face, sheared this far toward the vertical
def finial_widths(base, at_start, profile=None, floor=0.0, swell=FINIAL_SWELL, span=FINIAL_SPAN):
    """The c's swell on one end of a width function: f(t) = base(t) *
    profile(t), rising to `swell` x that over the end's `span` of the stroke
    (the same smoothstep `widths()` interpolates with, so a profile declared
    as [(0, 1.10), (0.13, 1.0), ...] and this compose to the same numbers).
    `floor` is the least width the swelled end may have: a terminal on a
    hairline (the y's tail runs out on the pen's thin) would otherwise swell
    to 1.10 of nearly nothing, so it takes the swell that lands it on the
    floor instead -- rounds.c_top_width() is the c's own end, the reference."""
    bf = base if callable(base) else (lambda t: base)
    pf = profile if callable(profile) else (lambda t: 1.0)
    te = 0.0 if at_start else 1.0
    w_end = bf(te) * pf(te)
    sw = max(swell, floor / w_end) if (floor and w_end > 0) else swell
    def f(t):
        w = bf(t) * pf(t)
        u = t if at_start else 1.0 - t
        if u < span:
            v = u / span
            w = w * (sw + (1.0 - sw) * (3 * v * v - 2 * v * v * v))
        return w
    return f
def finial_cut(pts, at_start, deg=FINIAL_CUT_DEG):
    """The c's face on one end of a centerline: the signed cut, in stroke()'s
    convention, that shears the end face `deg` toward the vertical. stroke()
    shears by moving the left-of-travel corner forward and the right one back
    (at the start; the reverse at the end), so the face after the cut runs
    along n + tn tan(cut) at a start and n - tn tan(cut) at an end; the sign
    is the one that leaves that face nearer the vertical. On the c's top,
    which leaves its start heading up-left, this is -28 degrees, the number
    g_c always carried. A stroke ending exactly horizontal has a face already
    vertical and takes the negative shear (the c's) -- neither is nearer."""
    tn = tangents(pts)[0 if at_start else -1]
    n = (-tn[1], tn[0]); s = 1.0 if at_start else -1.0
    best = None
    for sign in (-1.0, 1.0):
        tg = math.tan(math.radians(sign * deg))
        fx, fy = n[0] + s * tn[0] * tg, n[1] + s * tn[1] * tg
        off = abs(math.degrees(math.atan2(fy, fx)) % 180.0 - 90.0)
        if best is None or off < best[0] - 1e-9: best = (off, sign)
    return math.radians(best[1] * deg)

DOT_STYLE = int(os.environ.get("FJORD_DOT_STYLE", 1))   # owner 2026-09-14: "dot style 1 wins"
# ROUND 233 -- THE PUNCHED DOT. Owner 2026-09-18, on the bump markup, one line
# for every dot in the roman (R24 i, R25 j, R44 . R45 , R46 : R47 ; R48 ! R50 ?):
# *"replace lines with more metal punch inspired treatment."* What style 1 drew
# was an ELEVEN-SIDED POLYGON (12 - style sides, superellipse exponent 1.94,
# radial jitter x LIFE -- and LIFE is 0 since round 231, so the jitter was
# already gone and the only thing the style still did was show its eleven
# facets). Those facets are the "lines". A dot cut by a punch is a full round,
# its outline dense enough to read as a curve at any size; the style NUMBER is
# kept (the 2026-09-14 ruling chose 1 off a ladder of ten and everything reads
# it) and what it draws is replaced. ALBO_DOT_PUNCH picks the punch:
#   a  a full round -- a true circle at DOT_PUNCH_N vertices (the default)
#   b  a superellipse at exponent 2.3 -- squared a touch, the shoulders of a
#      punch that was filed flat on four sides
#   c  a round with a slight TEARDROP lean toward the writing direction: the
#      radius swells DOT_PUNCH_LEAN toward DOT_PUNCH_LEAN_DEG (right and a
#      little down) and shrinks by the same on the far side; the geometric
#      centre and the width do not move, the ink's weight does
# Styles 2-9 keep the ladder's polygons; 0 keeps the round superellipse.
DOT_PUNCH = os.environ.get("ALBO_DOT_PUNCH", "a")
DOT_PUNCH_N = 40           # vertices: 8.2 units apart on the i's dot, under the family's 11-unit SPACING
# The punch is drawn at 0.98 r, not r, and that number is the old polygon's SIZE
# and not a taste: an 11-gon on circumradius r is 1.9595 r wide (vertex to the
# opposite flat) and 0.9575 pi r^2 in area, and a circle at 0.98 r is 1.96 r wide
# and 0.9604 pi r^2 -- the same width to 0.03 unit on the i's dot and the same
# ink to half a percent. The 2026-09-14 ruling chose the dot at that size, and
# the marks were fitted on that extent in rounds 220-222: a circle at the full r
# is 2 units wider, and the build's bearing rule then moves every stop's and
# curly quote's advance by those 2 units (measured: period 260 -> 262). At
# 0.98 r the advances are byte-identical to the ship's.
DOT_PUNCH_SCALE = 0.98
DOT_PUNCH_K = 2.3          # option b's exponent
DOT_PUNCH_LEAN = 0.08      # option c: the radius swells 8% toward the lean and shrinks 8% away from it
DOT_PUNCH_LEAN_DEG = -20.0 # option c: the lean's direction, degrees from 3 o'clock (negative = below it)
def _punch_dot(cx, cy, r, opt):
    n = DOT_PUNCH_N; pts = []; r = r * DOT_PUNCH_SCALE
    lean = math.radians(DOT_PUNCH_LEAN_DEG)
    for i in range(n):
        a = 2 * math.pi * i / n; ca, sa = math.cos(a), math.sin(a)
        if opt == "b":
            kk = DOT_PUNCH_K
            x = math.copysign(abs(ca) ** (2 / kk), ca); y = math.copysign(abs(sa) ** (2 / kk), sa)
        else:
            x, y = ca, sa
        rr = r * (1 + DOT_PUNCH_LEAN * math.cos(a - lean)) if opt == "c" else r
        pts.append((cx + rr * x, cy + rr * y))
    return geom.poly(pts)
def dot(cx, cy, r, k=2.0):
    """The dot of i j and the marks. DOT_STYLE 0-9 (owner 2026-09-14: "make
    ten increasingly handcut versions of dots"): 0 the round superellipse;
    1 the PUNCHED dot (round 233, `_punch_dot`, `ALBO_DOT_PUNCH`); from 2
    the exponent falls toward a squarer form, the outline becomes a polygon
    of fewer sides, and each vertex takes a deterministic radial jitter
    from life() -- 9 is a rough-cut five-sided lump."""
    st = DOT_STYLE
    if st <= 0:
        return geom.poly(superellipse(cx, cy, r, r, 0, 2 * math.pi, k)[:-1])
    if st == 1:
        return _punch_dot(cx, cy, r, DOT_PUNCH)
    n = max(5, 12 - st)
    jit = 0.035 * st
    ks = k - 0.06 * st
    js = life(n + 1)
    rot = js[0] * math.pi / n
    pts = []
    for i in range(n):
        a = rot + 2 * math.pi * i / n
        rr = r * (1 + jit * js[i + 1])
        # a superellipse radius at this angle, so the squaring shows in the polygon too
        ca, sa = math.cos(a), math.sin(a)
        se = 1.0 / ((abs(ca) ** ks + abs(sa) ** ks) ** (1.0 / ks)) if ks > 0.5 else 1.0
        pts.append((cx + rr * se * ca, cy + rr * se * sa))
    return geom.poly(pts)

# ---------------------------------------------------------------- traps
def trap(apex, direction, half_deg, depth):
    """An ink trap: a V cut into the ink with its apex at `apex`, opening
    along `direction` (unit, pointing OUT of the ink into the crotch's
    air), `depth` deep. Subtract it (geom.ink cutouts)."""
    dx, dy = direction; a = math.radians(half_deg)
    tip = (apex[0] - dx * depth, apex[1] - dy * depth)
    far = depth * 2.2 / math.cos(a)   # the V reaches only a little past the apex into the air
    e1 = (dx * math.cos(a) - dy * math.sin(a), dx * math.sin(a) + dy * math.cos(a))
    e2 = (dx * math.cos(a) + dy * math.sin(a), -dx * math.sin(a) + dy * math.cos(a))
    return geom.poly([tip, (tip[0] + e1[0] * far, tip[1] + e1[1] * far), (tip[0] + e2[0] * far, tip[1] + e2[1] * far)])
