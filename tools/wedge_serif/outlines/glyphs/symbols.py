"""The symbols an epub actually uses (round 99, 2026-09-14).

Owner: "create all letters needed for my epub reading (unicode arrows, chess
pieces, etc)." The demand list is MEASURED, not guessed: all 34 books in
`~/src/claude-tools/*/epub/` were scanned (2,516,541 characters, 158 distinct
codepoints) and diffed against Albo's cmap -- `outlines/cmp/corpus.py`
re-runs it. Thirty-eight were missing, and the frequency order is the order
they were drawn in: the rightwards arrow (2,583 uses), the middle dot
(1,879), the guillemets (1,623 each), the ballot X (812), the braces (785),
the inverted question mark (662), the check (443), then a long tail.

Everything Albo does not draw is supplied by NOTO at .cpfont build time, so
an un-drawn symbol is not a hole on the page -- it is a symbol from another
typeface in the middle of a sentence, which is the thing worth fixing.

Sets beyond the corpus are here because the owner named them (arrows in
every direction, the chess pieces) or because the reader's `reading`
interval asks for them and a book of that kind would otherwise mix faces:
the card suits, the music signs, the geometric shapes, the superscripts and
subscripts, the currency and the mathematics.

Construction rules, so a later round can extend the set without a survey:
- everything is built from the same primitives the letters use (`stroke` on
  a centerline with `pen_widths`, `ring`, `bar`, `dot`, `diagonal`), so the
  stress and the weight are the pen's;
- a symbol's vertical centre is the LOWERCASE BODY's optical centre, the
  same ruling round 98 applied to the parens -- MID below;
- a symbol that stands in text at x-height scale (the arrows, the math
  relations) reads at the figures' weight, not the capitals';
- nothing here is fitted by hand: `round19.SIDES` gives every one of them
  the 'punct' side, and round 97b's mark bearings apply.
"""
import math, os
from . import glyph
from .. import geom, pen
from ..geom import cubic, line, superellipse
from ..primitives import stroke, pen_widths, widths, dot, ring, bar, stem, diagonal
from ..pen import S, XH, CAP, ASC, DESC, OVER, TH_V, TH_H, HAIR, CUT, BOWL_K
from .stems import DOT_R

MID = XH * 0.50            # the lowercase body's optical middle: where a symbol centres
MATH = TH_H * 0.92         # the weight of a mathematical rule (a shade under the pen's horizontal)
ARROW_LEN = XH * 1.32
# ROUND 385: the HORIZONTAL arrows' length. At 1.32 x-heights (0.57 em) the
# arrow and the implication sign set at 20 px read as a dash and an equals
# sign: Times New Roman's and STIX Two's run 0.9-1.0 em. 1.75 x-heights is
# 0.75 em -- long enough for the head to register, still a word's sign rather
# than a rule. The vertical and diagonal arrows keep ARROW_LEN: longer, they
# would drop through the baseline.
ARROW_LEN_H = XH * 1.75
ARROW_HEAD = XH * 0.30

def _fill_cracks(g, width=16.0):
    """ROUND 384: fill every hole whose mean width (2 x area / perimeter) is
    under `width` -- the glitch gate's CRACK and SPECK, left where two strokes
    of a symbol meet at an angle. 16, not the gate's 12, because this runs
    BEFORE the ink spread, which shrinks a hole on its way to the file: the
    700's radical measured 13 here and 11 in the font. A designed counter is
    far wider than this; the chess pieces' small crown windows are not passed
    through here."""
    import shapely.geometry as sg
    def fix(poly):
        keep = [r for r in poly.interiors
                if 2.0 * sg.Polygon(r).area / max(sg.Polygon(r).length, 1e-9) >= width]
        return sg.Polygon(poly.exterior, keep)
    if g.geom_type == 'Polygon': return fix(g)
    if g.geom_type == 'MultiPolygon': return sg.MultiPolygon([fix(p) for p in g.geoms])
    return g

def _upright(g):
    """ROUND 385: a PICTOGRAPH STANDS UPRIGHT IN THE ITALIC. Owner 2026-09-24,
    *"improve the chess, card and other symbols. they are distractingly weird
    currently."* `build.draw` shears every glyph about the baseline, so a
    square came out a parallelogram and a chess piece leaned as if it were
    falling over. Measured rather than assumed: Times New Roman, Arial and
    Courier New Italic keep the suits, the notes, the squares, circles and
    triangles and the arrows UPRIGHT (Georgia and Verdana Italic, the note),
    while they slant the pilcrow and the section -- a picture is not a letter.
    The inverse shear is applied here, BEFORE draw()'s own shear, so the pair
    cancels and the glyph reaches the file upright."""
    if not pen.SHEAR: return g
    import shapely.affinity as aff
    return aff.affine_transform(g, (1, -pen.SHEAR, 0, 1, 0, 0))

def _s(pts, prof=None, w=None, cut0=CUT, cut1=CUT, light=1.0):
    return stroke(pts, w if w is not None else pen_widths(pts, (prof or (lambda t: 1.0)), scale=light), cut0=cut0, cut1=cut1)

def _chevron(ax, ay, opens, D, H, apex, end_u, end_l):
    """ROUND 385: a TAPERED chevron as one polygon -- its outer point at
    (ax, ay), opening toward +x when `opens` is +1 (the < of a left
    guillemet), its arms reaching D across and H up and down. `apex` is the
    ink's horizontal depth on the axis, `end_u` / `end_l` the horizontal width
    of the upper / lower arm where it is cut level at +-H: an arm heavy at the
    point that thins toward its end, which is how Times New Roman Bold and
    Georgia Bold draw a guillemet. Built from pen strokes instead, two arms
    overlap at the point as two round or cut ends -- what made the 700's
    guillemets read blunt."""
    import shapely.geometry as sg
    pts = [(D, H), (0.0, 0.0), (D, -H), (D + end_l, -H), (apex, 0.0), (D + end_u, H)]
    return sg.Polygon([(ax + opens * x, ay + y) for x, y in pts]).buffer(0)

def _arrowhead(tx, ty, points, D, H, k, te):
    """ROUND 385: a double arrow's head -- two CURVED barbs sweeping back from
    a sharp point at (tx, ty) and tapering to a fine level-cut end, the white
    between them running in to an inner corner k behind the point. `points`
    is +1 for a head pointing toward +x. The shape of the double arrow's head
    in STIX Two Math and Apple Symbols (measured beside it in
    docs/albo-symbols-2026-09-24.md): the barbs bow toward the shafts."""
    import shapely.geometry as sg
    from ..geom import quad
    up_out = quad((0.0, 0.0), (-D * 0.52, H * 0.40), (-D, H))
    up_in = quad((-D + te, H), (-k - (D - te - k) * 0.52, H * 0.34), (-k, 0.0))
    upper = up_out + up_in[1:]
    lower = [(x, -y) for x, y in reversed(upper)]
    ring = upper[:-1] + lower[:-1]
    return sg.Polygon([(tx + points * x, ty + y) for x, y in ring]).buffer(0)

# ---------------------------------------------------------------- arrows
def _arrow(c, dx, dy, length=None, double=False):
    """A shaft with a head, pointing along (dx, dy), centered on MID.

    ROUND 385: the head is `_arrowhead`, the double arrows' own -- two curved
    barbs tapering to fine ends from a sharp point -- and the shaft a plain
    rule. It was a pen stroke with two more pen strokes butted on at the
    point at 32 degrees, which at the 700 piled up into the same knot the
    double arrow's head made (owner 2026-09-24: "address the weirdness ... in
    symbols"), and the shaft's tail carried the pen's slanted cut, a letter's
    terminal on a sign. One head for all eleven arrows now, so the arrow and
    the implication sign are visibly the same family. Built pointing right,
    then turned."""
    import shapely.affinity as aff
    L = length or ARROW_LEN
    w = max(MATH * 0.92, HAIR)
    H = XH * 0.32 + w * 0.5                              # big enough to read as a head at 20 px, not a dash
    D = H * 1.12
    k = w * 2.7                                          # the barbs ~1.8 strokes thick at the point, so they survive at 20 px
    te = w * 0.50
    parts = [_arrowhead(L, MID, +1, D, H, k, te), bar(k * 0.8 if double else 0.0, L - k * 0.8, MID, w)]
    if double:   # the left-right and up-down arrows
        parts.append(_arrowhead(0.0, MID, -1, D, H, k, te))
    g = geom.ink(parts)
    ang = math.degrees(math.atan2(dy, dx))
    return aff.rotate(g, ang, origin=(L / 2, MID)) if ang else g

@glyph('→')
def g_arrowright(c): return _arrow(c, 1, 0, length=ARROW_LEN_H)
@glyph('←')
def g_arrowleft(c): return _arrow(c, -1, 0, length=ARROW_LEN_H)
@glyph('↔')
def g_arrowboth(c): return _arrow(c, 1, 0, length=ARROW_LEN_H, double=True)
@glyph('↑')
def g_arrowup(c): return _arrow(c, 0, 1, length=ARROW_LEN * 0.92)
@glyph('↓')
def g_arrowdown(c): return _arrow(c, 0, -1, length=ARROW_LEN * 0.92)
@glyph('↕')
def g_arrowupdn(c): return _arrow(c, 0, 1, length=ARROW_LEN * 0.92, double=True)
@glyph('↗')
def g_arrowne(c): return _arrow(c, 1, 1)
@glyph('↘')
def g_arrowse(c): return _arrow(c, 1, -1)
@glyph('↖')
def g_arrownw(c): return _arrow(c, -1, 1)
@glyph('↙')
def g_arrowsw(c): return _arrow(c, -1, -1)

def _darrow(c, dx, both=False):
    """A double (hollow) arrow: two shafts and a barb pair, the implication
    sign of mathematical prose.

    ROUND 385 -- THE HEAD IS ONE CHEVRON, THE SHAFTS RUN INTO IT. Owner
    2026-09-24, from the round-384 proof: the bold double arrow *"reads as a
    lumpy hexagon with barbs"*. Round 384 had already stopped the shafts at
    the barbs, but the head was still two pen strokes butted at the tip, so at
    the 700 their round-cut ends piled up into a knot and the barbs' ends
    stood out as two more lumps. The head is now a mitered chevron
    (`_chevron`): a sharp point, barbs of the shafts' own weight cut square,
    reaching 1.3 shaft-gaps past the outer shaft and never less than 0.40 of the x-height off the axis (the proportion of the
    double arrow in Times New Roman and STIX Two, measured in
    docs/albo-symbols-2026-09-24.md); each shaft ends inside the chevron's arm
    so the two are one shape, and the white between the shafts runs on into
    the head to the chevron's inner corner. Round 384's gap rule is kept: a
    stroke of white between the shafts at every weight."""
    L = ARROW_LEN_H; w = max(MATH * 0.78, HAIR)
    gap = max(XH * 0.13, w * 2.0)                       # shaft center to shaft center
    H = max(gap / 2 + w / 2 + gap * 1.30, XH * 0.40)     # the barb's reach off the axis: smaller, the 400's arrow read as an equals sign at 20 px
    D = H * 1.10                                         # ... and back from the point
    k = w * 2.7                                          # the head's depth on the axis: barbs ~1.8 strokes thick at the point
    te = w * 0.50                                        # a barb's end, cut level
    heads = [(L, +1)] + ([(0.0, -1)] if both else [])
    parts = [_arrowhead(x, MID, p_, D, H, k, te) for x, p_ in heads]
    # each shaft ends in the MIDDLE of the barb it runs into -- measured on the
    # head itself, along the shaft's centerline -- so the two are one shape and
    # no square end can stand out past the barb's outer curve
    import shapely.geometry as sg
    def _end(head, y, toward):
        seg = head.intersection(sg.LineString([(-L, y), (2 * L, y)]))
        segs = list(seg.geoms) if hasattr(seg, 'geoms') else [seg]
        xs = [((q.coords[0][0] + q.coords[-1][0]) / 2) for q in segs if not q.is_empty]
        return max(xs) if toward > 0 else min(xs)
    for off in (+gap / 2, -gap / 2):
        x1 = _end(parts[0], MID + off, -1)
        x0 = _end(parts[1], MID + off, +1) if both else 0.0
        parts.append(bar(x0, x1, MID + off, w))
    g = geom.ink(parts)
    if dx < 0:
        import shapely.affinity as aff
        g = aff.scale(g, -1, 1, origin=(L / 2, MID))
    return g

@glyph('⇒')
def g_dblarrowright(c): return _darrow(c, 1)
@glyph('⇐')
def g_dblarrowleft(c): return _darrow(c, -1)
@glyph('⇔')
def g_dblarrowboth(c): return _darrow(c, 1, both=True)

# ---------------------------------------------------------------- dots, quotes, braces
# ROUND 363 -- THE MIDDLE DOT IS A TRAJAN TRIANGLE. Owner 2026-09-23: *"make
# the middot a trajan style triangle."*
#
# It is worth doing carefully: the middle dot is the SECOND most-used symbol
# in his own books (1,879 uses across the 34 epubs, after the rightwards
# arrow) -- see this file's header.
#
# The inscriptional interpunct is chisel-cut, so its sides are not quite
# straight: a V-gouge leaves edges that fall slightly INTO the shape. `CONC`
# bows each side inward by that fraction of the triangle's height; 0 is a
# plain triangle. `DIR` is which way the apex points -- the Trajan column
# carries both an apex-up point and a rightward wedge, so it is a dial rather
# than an assumption.
MIDDOT_TRI = float(os.environ.get("ALBO_MIDDOT_TRI", 1.0))   # 0 = the round dot, 1 = the triangle
MIDDOT_SIZE = float(os.environ.get("ALBO_MIDDOT_SIZE", 1.55))  # x the marks' dot DIAMETER, across the base
MIDDOT_APEX = float(os.environ.get("ALBO_MIDDOT_APEX", 180.0))   # where the point goes, degrees from 3 o'clock. 180 = to the LEFT, as the column cuts it
MIDDOT_TILT = float(os.environ.get("ALBO_MIDDOT_TILT", -12.0))   # the whole wedge rotated, degrees
MIDDOT_ASPECT = float(os.environ.get("ALBO_MIDDOT_ASPECT", 0.72))# the base's spread, x the wedge's length
MIDDOT_Y = float(os.environ.get("ALBO_MIDDOT_Y", 0.46))          # its centre, x the CAP height
MIDDOT_CONC = float(os.environ.get("ALBO_MIDDOT_CONC", 0.03))  # the chisel's hollow: the SAGITTA of each side, x the height. 0.10 is a shuriken; the useful range is 0 to about 0.05

def _tri(cx, cy, w, h, apex, tilt, conc):
    """The inscriptional interpunct: a chisel-cut WEDGE, not an equilateral
    triangle.

    ROUND 368, from the owner's own photograph of the column: the mark is a
    scalene wedge with its POINT TO THE LEFT and its mass to the right -- a
    short base on the right, a long edge running back to the point. Round
    363 built an equilateral triangle standing apex-up, which is the shape
    the phrase "Trajan triangle" suggests and is not what is cut in the
    stone. Corrected against the photograph rather than against the phrase.

    `apex` is where the point goes, degrees from 3 o'clock; `tilt` rotates
    the whole mark; `w`/`h` are its extents before that rotation; `conc` is
    the chisel's hollow on each edge.
    """
    # local: point at (-w/2, 0), base on the right, its two corners spread by h
    pts = [(-w / 2.0, 0.0), (w / 2.0, h / 2.0), (w / 2.0, -h / 2.0)]
    rot = math.radians(apex - 180.0 + tilt)
    ca, sa = math.cos(rot), math.sin(rot)
    pts = [(x * ca - y * sa, x * sa + y * ca) for x, y in pts]
    gx = sum(p[0] for p in pts) / 3.0; gy = sum(p[1] for p in pts) / 3.0
    pts = [(x - gx, y - gy) for x, y in pts]
    out = []
    for i in range(3):
        p0 = pts[i]; p1 = pts[(i + 1) % 3]
        mx, my = (p0[0] + p1[0]) / 2.0, (p0[1] + p1[1]) / 2.0
        nx, ny = -mx, -my
        L = math.hypot(nx, ny) or 1.0
        ctrl = (mx + nx / L * h * conc, my + ny / L * h * conc)
        # the hollow is the sagitta of each side and no more -- see round 363:
        # handles that overran the control turned this into a shuriken.
        out += geom.cubic(p0, ctrl, ctrl, p1)
    return [(cx + x, cy + y) for x, y in out]

@glyph('·')      # middle dot
def g_middot(c):
    if not MIDDOT_TRI:
        return dot(DOT_R, MID, DOT_R)
    # AND IT SITS AT MID-CAP, not mid-x-height. On the column the points
    # divide CAPITALS and are centred on them; MID is XH * 0.5, which on a
    # face with capitals is a good deal lower than the photograph shows.
    _w = DOT_R * 2.0 * MIDDOT_SIZE
    _cy = CAP * MIDDOT_Y
    return geom.poly(_tri(DOT_R, _cy, _w, _w * MIDDOT_ASPECT, MIDDOT_APEX,
                          MIDDOT_TILT, MIDDOT_CONC))
@glyph('•')      # bullet
def g_bullet(c): return dot(DOT_R * 1.5, MID, DOT_R * 1.5)
@glyph('∙')
def g_bulletop(c): return dot(DOT_R * 1.1, MID, DOT_R * 1.1)

GUIL_WHITE = 0.70   # the least white between the chevrons, as a fraction of their stroke: the italic 400's own (0.71; the roman's is 0.88)
def _guillemet(c, left, single=False):
    """Angle quotes: the chevrons are the pen's diagonals, their apex on MID
    and their opening the same 52 degrees as the circumflex's."""
    h = XH * 0.42; w = XH * 0.24; n = 1 if single else 2
    sw = max(MATH * 0.95, HAIR)
    # ROUND 384 -- THE GAP GROWS WITH THE STROKE. It was a fixed XH * 0.20,
    # which at the 400 leaves 26 units of white between the two chevrons
    # (0.87 of the stroke) and at the 700 leaves MINUS one: the chevrons ran
    # into each other and trapped a 760-unit hole, the glitch gate's SPECK on
    # both bolds. The white between two parallel diagonals is the horizontal
    # gap times the sine of their angle, so the gap is solved for the 400's
    # own white-to-stroke ratio; at the 400 the old constant is the larger and
    # still wins, so the 400s are unchanged.
    sin_a = math.sin(math.atan2(h / 2, w))
    gap = max(XH * 0.20, sw * (1.0 + GUIL_WHITE) / sin_a)
    if S > GUIL_PEN_ABOVE:
        return _guillemet_heavy(left, n, sw)
    parts = []
    for i in range(n):
        x0 = i * gap
        apex = (x0, MID) if left else (x0 + w, MID)
        a = (x0 + w, MID + h / 2) if left else (x0, MID + h / 2)
        b = (x0 + w, MID - h / 2) if left else (x0, MID - h / 2)
        parts.append(_s(line(a, apex), w=sw, cut1=None))
        parts.append(_s(line(apex, b), w=sw, cut0=None))
    return geom.ink(parts)

GUIL_PEN_ABOVE = 84.0   # the 400s (stem 66.9) keep the construction above, byte for byte

def _guillemet_heavy(left, n, sw):
    """ROUND 385 -- THE HEAVY GUILLEMETS, DRAWN AS THE PEN WOULD. Owner
    2026-09-24, from the round-384 proof: at the 700 the guillemets *"read as
    chunky blunt chevrons"*. They were the 400's chevron -- 180 units tall,
    monoline -- with its stroke nearly doubled (32 -> 57), so a chevron was a
    third stroke and two butted round ends at the point. What Times New Roman
    Bold and Georgia Bold do, measured beside them: the chevron grows a
    little with the weight, it has a PEN's contrast -- the stroke that falls
    to the right (\\) is the heavy one, the one that rises to the right (/)
    about half of it -- its point is sharp, and its ends are cut level. So
    here: 0.52 of the x-height tall against the 400's 0.42, the heavy arm the
    400's rule scaled by 0.95, the light arm 0.52 of it, one mitered polygon
    (`_chevron`) with a sharp point, and the gap solved for round 384's white
    against the HEAVY arm, which is the one that faces its neighbor across the
    gap on the lower half. The 400s are not touched."""
    h = XH * 0.56; D = XH * 0.25
    heavy = sw * 0.95
    sin_t = math.sin(math.atan2(h / 2, D))
    apex = heavy * 1.15 / sin_t                          # the point carries the most ink
    e_heavy, e_light = heavy * 0.62 / sin_t, heavy * 0.34 / sin_t
    gap = apex + heavy * GUIL_WHITE / sin_t              # round 384's white, at the point
    parts = []
    for i in range(n):
        x0 = i * gap
        if left:    # <: the upper arm rises to the right (light), the lower falls (heavy)
            parts.append(_chevron(x0, MID, +1, D, h / 2, apex, e_light, e_heavy))
        else:       # >: the upper arm falls to the right (heavy), the lower rises (light)
            parts.append(_chevron(x0 + D + e_heavy * 0.0, MID, -1, D, h / 2, apex, e_heavy, e_light))
    return geom.ink(parts)

@glyph('«')
def g_guillemotleft(c): return _guillemet(c, True)
@glyph('»')
def g_guillemotright(c): return _guillemet(c, False)
@glyph('‹')
def g_guilsinglleft(c): return _guillemet(c, True, single=True)
@glyph('›')
def g_guilsinglright(c): return _guillemet(c, False, single=True)

def _brace(c, left):
    """A brace on the parens' span (round 98's raised fences), its waist a
    cusp at MID and its two arms the pen's turning stroke."""
    from .marks import FENCE_RAISE
    top = CAP + FENCE_RAISE; bot = -DESC + FENCE_RAISE; mid = (top + bot) / 2
    w = XH * 0.30; xw = w * 0.22          # the waist's x
    prof = widths([(0.0, 0.52), (0.35, 0.92), (0.62, 0.92), (1.0, 0.52)])
    up = cubic((w, top), (xw, top - (top - mid) * 0.34), (w * 0.62, mid + (top - mid) * 0.42), (xw, mid))
    dn = cubic((xw, mid), (w * 0.62, mid - (mid - bot) * 0.42), (xw, bot + (mid - bot) * 0.34), (w, bot))
    g = geom.ink([_s(up, prof, cut1=None), _s(dn, prof, cut0=None)])
    if not left:
        import shapely.affinity as aff
        g = aff.scale(g, -1, 1, origin='center')
    return g

@glyph('{')
def g_braceleft(c): return _brace(c, True)
@glyph('}')
def g_braceright(c): return _brace(c, False)
@glyph('|')
def g_bar(c):
    from .marks import FENCE_RAISE
    return _s(line((TH_V * 0.4, -DESC + FENCE_RAISE), (TH_V * 0.4, CAP + FENCE_RAISE)), w=TH_V * 0.62)
@glyph('¦')
def g_brokenbar(c):
    from .marks import FENCE_RAISE
    x = TH_V * 0.4; top = CAP + FENCE_RAISE; bot = -DESC + FENCE_RAISE; g = (top - bot) * 0.14
    return geom.ink([_s(line((x, bot), (x, MID - g)), w=TH_V * 0.62), _s(line((x, MID + g), (x, top)), w=TH_V * 0.62)])

# ---------------------------------------------------------------- inverted Spanish
@glyph('¿')
def g_questiondown(c):
    import shapely.affinity as aff
    from .marks import g_question
    g = g_question(c)
    x0, y0, x1, y1 = g.bounds
    g = aff.rotate(g, 180, origin='center')
    return aff.translate(g, 0, -DESC * 0.62 - y0 + (y0 - g.bounds[1]))
@glyph('¡')
def g_exclamdown(c):
    import shapely.affinity as aff
    from .marks import g_exclam
    g = g_exclam(c); g = aff.rotate(g, 180, origin='center')
    return aff.translate(g, 0, -DESC * 0.62 - g.bounds[1])

# ---------------------------------------------------------------- marks
@glyph('\u00a7')      # section
def g_section(c):
    """The doubled S, and literally so: the font's own S at 0.60 with the
    same S turned 180 degrees under it, overlapping by a stroke. The first
    cut drew the curves by hand and came out an epsilon; the letter it is
    made of cannot."""
    import shapely.affinity as aff
    from . import GLYPHS
    g = GLYPHS['S'](c); x0, y0, x1, y1 = g.bounds
    k = 0.60; g = aff.scale(g, k, k, origin=(x0, y0)); x0, y0, x1, y1 = g.bounds
    up = aff.translate(g, -x0, CAP * 1.02 - y1)
    lo = aff.translate(aff.rotate(g, 180, origin='center'), -x0, CAP * 1.02 - y1 - (y1 - y0) * 0.50)   # the two S's INTERLOCK and share a spine: at 0.84 they read as two letters stacked, at 0.62 still two
    return geom.ink([up, lo])

@glyph('\u00b6')      # pilcrow
def g_paragraph(c):
    """ROUND 385 -- THE BOWL HANGS TO THE LEFT OF THE STEMS. Owner 2026-09-24,
    *"improve the chess, card and other symbols. they are distractingly weird
    currently."* Rounds 100-272 built this from the font's own P with its
    counter filled and a second stem at the bowl's right edge -- which put the
    solid bowl BETWEEN the two stems: a block at the 400 and, sheared, a
    capital A in the italic. In the pilcrow of every text face measured beside
    it (Times New Roman, Georgia, STIX Two, DejaVu, Apple Symbols) the two
    stems stand side by side and the solid bowl -- a reversed D -- hangs off the
    LEFT one from the cap line to a little under half the cap height; a flat
    top joins the stems. The stems are light (0.62 of the cap stem) and the
    bowl carries the weight, which is what makes it read as a mark rather
    than as a letter. The stems have no foot wedges: round 272's two inner
    feet met under the slot at the 700 and closed it into a counter, and with
    no feet there is nothing to meet."""
    import shapely.geometry as sg
    from ..pen import CS
    w = CS * 0.55
    rx, ry = CAP * 0.26, CAP * 0.29
    x1 = rx + w * 0.5
    x2 = x1 + w * 2.1                               # a stem and a tenth of white between the stems
    bowl = geom.poly(superellipse(x1, CAP - ry, rx, ry, math.pi / 2, math.pi * 1.5, 2.2), [])
    top = sg.box(x1 - 1.0, CAP - TH_H * 1.1, x2 + w / 2, CAP)
    return geom.ink([bowl, top, stem(x1, 0, CAP, w=w, ent=0.0, it_entry=False, it_exit=False), stem(x2, 0, CAP, w=w, ent=0.0, it_entry=False, it_exit=False)])

@glyph('†')      # dagger
def g_dagger(c):
    x = S * 0.9
    return geom.ink([_s(line((x, -DESC * 0.42), (x, CAP)), w=TH_V * 0.72),
                     bar(0, x * 2, CAP * 0.70, TH_H * 0.82)])
@glyph('‡')      # double dagger
def g_daggerdbl(c):
    x = S * 0.9
    return geom.ink([_s(line((x, -DESC * 0.42), (x, CAP)), w=TH_V * 0.72),
                     bar(0, x * 2, CAP * 0.74, TH_H * 0.82), bar(0, x * 2, CAP * 0.12, TH_H * 0.82)])
@glyph('′')      # prime
def g_prime(c): return _s(line((S * 0.42, CAP * 0.62), (S * 0.10, CAP)), widths([(0.0, 0.58), (1.0, 1.0)]))
@glyph('″')      # double prime
def g_dblprime(c):
    # ROUND 384 -- THE TWO PRIMES NO LONGER RUN TOGETHER. The second was set a
    # fixed 0.60 S to the right, but a prime is 0.91 S wide across its top
    # (measured at the 400 and the 700 alike), so the two tops overlapped in
    # every cut and the union left a slit between them -- the `second` finding
    # `cmp_contour_hairs.py` has listed since the gate existed. The offset is
    # now the prime's own top width plus 0.45 of it in white.
    import shapely.geometry as sg
    a = _s(line((S * 0.42, CAP * 0.62), (S * 0.10, CAP)), widths([(0.0, 0.58), (1.0, 1.0)]))
    x0, _, x1, _ = a.intersection(sg.box(-1e4, CAP * 0.90, 1e4, CAP * 0.92)).bounds
    dx = (x1 - x0) * 1.45
    b = _s(line((S * 0.42 + dx, CAP * 0.62), (S * 0.10 + dx, CAP)), widths([(0.0, 0.58), (1.0, 1.0)]))
    return geom.ink([a, b])
@glyph('‰')      # per mille
def g_perthousand(c):
    from .marks import g_percent
    import shapely.affinity as aff
    g = g_percent(c); x0, y0, x1, y1 = g.bounds
    r = (x1 - x0) * 0.16
    o1, *_ = ring(x1 + r * 1.5, r * 1.15, r, r * 1.06, w_scale=0.72)
    o2, *_ = ring(x1 + r * 4.0, r * 1.15, r, r * 1.06, w_scale=0.72)
    return geom.ink([g, o1, o2])

# ---------------------------------------------------------------- mathematics
@glyph('−')      # minus
def g_minus(c): return bar(0, XH * 0.86, MID, MATH)
@glyph('×')      # multiply
def g_multiply(c):
    h = XH * 0.52
    return geom.ink([_s(line((0, MID - h / 2), (h, MID + h / 2)), w=MATH * 0.95),
                     _s(line((0, MID + h / 2), (h, MID - h / 2)), w=MATH * 0.95)])
@glyph('÷')      # divide
def g_divide(c):
    r = DOT_R * 0.86; w = XH * 0.86
    return geom.ink([bar(0, w, MID, MATH), dot(w / 2, MID + XH * 0.26, r), dot(w / 2, MID - XH * 0.26, r)])
@glyph('±')      # plus-minus
def g_plusminus(c):
    w = XH * 0.80; y = MID + XH * 0.12
    return geom.ink([bar(0, w, y, MATH), _s(line((w / 2, y - w * 0.40), (w / 2, y + w * 0.40)), w=MATH),
                     bar(0, w, MID - XH * 0.40, MATH)])
@glyph('≈')      # almost equal
def g_approx(c):
    w = XH * 0.86
    def wave(y):
        p = cubic((0, y), (w * 0.28, y + XH * 0.13), (w * 0.62, y - XH * 0.13), (w, y + XH * 0.01))
        return _s(p, widths([(0.0, 0.78), (0.5, 1.0), (1.0, 0.78)]), light=0.92)
    return geom.ink([wave(MID + XH * 0.14), wave(MID - XH * 0.16)])
@glyph('≠')      # not equal
def g_notequal(c):
    from .marks import g_equal
    g = g_equal(c); x0, y0, x1, y1 = g.bounds
    sl = _s(line(((x0 + x1) / 2 - XH * 0.16, MID - XH * 0.40), ((x0 + x1) / 2 + XH * 0.16, MID + XH * 0.40)), w=MATH)
    return geom.ink([g, sl])
def _rel(c, eq_below=True, gt=False):
    # ROUND 384 -- THE CHEVRON IS THE `<`'s. It rose only 0.09 x-height over a
    # 0.82 x-height run -- a 12-degree wedge beside the `<`'s 49 -- so `≤` read
    # as a flattened arrowhead rather than as "less than", and its inside
    # corner was a REVERSAL to `cmp_contour_hairs.py` (167 degrees on 200-unit
    # arms). Now the `<`'s own width and nearly its slope (0.36 of the run
    # against 0.46, so it sits over the bar), lifted clear of the bar.
    w = XH * 0.74; h = w * 0.36; cy = MID + XH * 0.13
    apex = (w, cy) if gt else (0, cy)
    a = (0, cy + h) if gt else (w, cy + h)
    b = (0, cy - h) if gt else (w, cy - h)
    parts = [_s(line(a, apex), w=MATH * 0.95, cut1=None), _s(line(apex, b), w=MATH * 0.95, cut0=None)]
    parts.append(bar(0, w, MID - XH * 0.36, MATH))
    return geom.ink(parts)
@glyph('≤')
def g_lessequal(c): return _rel(c, gt=False)
@glyph('≥')
def g_greaterequal(c): return _rel(c, gt=True)
@glyph('<')
def g_less(c):
    w = XH * 0.74; h = XH * 0.34
    return geom.ink([_s(line((w, MID + h), (0, MID)), w=MATH * 0.95, cut1=None),
                     _s(line((0, MID), (w, MID - h)), w=MATH * 0.95, cut0=None)])
@glyph('>')
def g_greater(c):
    w = XH * 0.74; h = XH * 0.34
    return geom.ink([_s(line((0, MID + h), (w, MID)), w=MATH * 0.95, cut1=None),
                     _s(line((w, MID), (0, MID - h)), w=MATH * 0.95, cut0=None)])
@glyph('~')
def g_asciitilde(c):
    w = XH * 0.86
    p = cubic((0, MID), (w * 0.28, MID + XH * 0.17), (w * 0.62, MID - XH * 0.17), (w, MID + XH * 0.02))
    return _s(p, widths([(0.0, 0.78), (0.5, 1.05), (1.0, 0.78)]), light=0.95)
@glyph('^')
def g_asciicircum(c):
    w = XH * 0.62; y0 = XH * 0.42
    return geom.ink([_s(line((0, y0), (w / 2, y0 + XH * 0.46)), w=MATH * 0.95, cut1=None),
                     _s(line((w / 2, y0 + XH * 0.46), (w, y0)), w=MATH * 0.95, cut0=None)])
@glyph('∞')      # infinity
def g_infinity(c):
    r = XH * 0.24
    a, *_ = ring(r, MID, r, r * 0.86, w_scale=0.74, floor=HAIR)
    b, *_ = ring(r * 2.7, MID, r, r * 0.86, w_scale=0.74, floor=HAIR)
    return geom.ink([a, b])
@glyph('√')      # radical
def g_radical(c):
    """ROUND 385 -- ONE MITERED PATH. It was a pen stroke through three points
    with a swelling width profile, folded at the V and crack-filled (round
    384), plus a separate bar: at the 700 the long leg carried a 9-unit STEP
    two-thirds of the way up (`cmp_jogs.py`, docs/albo-symbols-2026-09-24.md) and
    the whole sign read lumpy. The radical is now what Albo's other
    mathematical signs are: a monoline rule, here one path -- the short
    down-stroke, the long up-stroke, the vinculum -- with a sharp point at the
    V and a square corner where the bar leaves the leg."""
    import shapely.geometry as sg
    w = max(MATH * 1.05, HAIR)
    h = CAP * 0.96 - w / 2                                # the bar's centerline: its top on CAP * 0.96
    path = [(0, MID * 1.10), (XH * 0.26, MID * 0.40 + w * 0.5), (XH * 0.54, h), (XH * 1.36, h)]
    return sg.LineString(path).buffer(w / 2, cap_style=2, join_style=2, mitre_limit=8.0)

# ---------------------------------------------------------------- signs
@glyph('°')      # degree
def g_degree(c):
    r = XH * 0.20
    # round 272: the same ring as the ring accent, and the same collapse -- at
    # the 900 a 92-unit wall on an 86-unit radius left a solid dot
    # (adversarial review); the wall scales by min(1, 84/S) as the accent's
    # has since round 268
    solid, *_ = ring(r, CAP - r, r, r, w_scale=0.62 * min(1.0, 84.0 / S), floor=HAIR * 0.9)
    return solid
@glyph('©')      # copyright
def _enclosed_letter_c(c): return _enclosed(c, 'C')
@glyph('®')
def _enclosed_letter_r(c): return _enclosed(c, 'R')
def _enclosed(c, letter):
    """A capital inside a ring, both on the pen. The letter is the font's
    own, scaled to the ring's counter, so the mark cannot drift from the
    capitals."""
    import shapely.affinity as aff
    from . import GLYPHS
    g = GLYPHS[letter](c); x0, y0, x1, y1 = g.bounds
    R = CAP * 0.42
    k = (R * 1.16) / max(x1 - x0, y1 - y0)
    g = aff.scale(g, k, k, origin=(x0, y0)); x0, y0, x1, y1 = g.bounds
    g = aff.translate(g, R - (x0 + x1) / 2, MID + CAP * 0.12 - (y0 + y1) / 2)
    solid, *_ = ring(R, MID + CAP * 0.12, R, R, w_scale=0.52, floor=HAIR * 0.9)
    return geom.ink([solid, g])
@glyph('™')      # trade mark
def g_trademark(c):
    import shapely.affinity as aff
    from . import GLYPHS
    parts = []; x = 0
    for L in 'TM':
        g = GLYPHS[L](c); x0, y0, x1, y1 = g.bounds
        k = 0.50; g = aff.scale(g, k, k, origin=(x0, y0)); x0, y0, x1, y1 = g.bounds
        g = aff.translate(g, x - x0, CAP - (y1 - y0) - y0)
        parts.append(g); x += (x1 - x0) + S * 0.22
    return geom.ink(parts)

def _currency_bar(g, n=1, vertical=True, span=1.22, counter=False):
    """The stroke that makes a letter a currency sign: through the ink, the
    pen's own weight, over-reaching the letter by the usual sixth.
    counter (round 272): the bar is centred on the letter's COUNTER -- from
    the inner edge of the first ink run at mid-height to the letter's right
    extreme -- not on its bounds. The cent's c is open on the right and
    thick on the left, so its bounds' centre falls inside the left wall
    once the wall carries the bold's weight: round 269 put the bold
    italic's c on the axis (wall 69 -> 96) and the cent's bar sank into it
    (adversarial review, 2026-09-19: the daylight between bar and wall,
    3,094 units^2, gone). Above stem 84 first; at every weight since the
    owner's ruling of 2026-09-19 on the cent page ("center it at the 400s too")."""
    x0, y0, x1, y1 = g.bounds; parts = [g]
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    if counter:   # round 276: at every weight -- owner 2026-09-19, on the cent page: "center it at the 400s too"
        from shapely.geometry import LineString as _LS
        _row = g.intersection(_LS([(x0 - 10, cy), (x1 + 10, cy)]))
        _segs = list(_row.geoms) if _row.geom_type == 'MultiLineString' else ([_row] if not _row.is_empty else [])
        if _segs:
            _first = min(_segs, key=lambda q: q.bounds[0])
            cx = (_first.bounds[2] + x1) / 2
    for i in range(n):
        off = ((i - (n - 1) / 2) * XH * 0.17)
        if vertical: parts.append(_s(line((cx + off, y0 - (y1 - y0) * (span - 1) / 2), (cx + off, y1 + (y1 - y0) * (span - 1) / 2)), w=MATH))
        else: parts.append(bar(x0 - (x1 - x0) * 0.10, x1 + (x1 - x0) * 0.10, cy + off, MATH))
    return geom.ink(parts)

@glyph('$')
def g_dollar(c):
    from . import GLYPHS
    return _currency_bar(GLYPHS['S'](c))
@glyph('¢')      # cent
def g_cent(c):
    import shapely.affinity as aff
    from . import GLYPHS
    g = GLYPHS['c'](c)
    return _currency_bar(g, counter=True)
@glyph('£')      # sterling
def g_sterling(c):
    """An italic L crossed, with a foot: the capital's own bowl gesture."""
    h = CAP
    spine = cubic((XH * 0.62, 0), (XH * 0.30, h * 0.30), (XH * 0.22, h * 0.52), (XH * 0.30, h * 0.80))
    hook = cubic((XH * 0.30, h * 0.80), (XH * 0.40, h * 1.04), (XH * 0.74, h * 1.02), (XH * 0.78, h * 0.80))
    foot = bar(XH * 0.10, XH * 0.92, 0, TH_H, align='bottom')
    cross = bar(XH * 0.08, XH * 0.66, h * 0.40, MATH)
    g = geom.ink([_s(spine, widths([(0.0, 0.95), (1.0, 0.82)]), cut0=None, cut1=None),
                  _s(hook, widths([(0.0, 0.82), (1.0, 0.52)]), cut0=None), foot, cross])
    # ROUND 392 -- THE SPINE RUNS INTO THE HOOK IN ONE LINE. The two cubics
    # meet at (0.30 xh, 0.80 cap) with different tangents (the spine arrives
    # at 16 degrees off vertical, the hook leaves at 23), so both square end
    # faces stand at the join and the inner edge carries a V-nick: 3.2 units
    # at the BoldItalic (311, 533), 2.0 at the Regular (181, 537),
    # `cmp_jogs.py` -- round 385's small list. Eased over a band a little
    # more than a stroke wide either side of the join; the hook's counter
    # starts well above it.
    jx, jy = XH * 0.30, h * 0.80
    return geom.ease_step(g, jx - S * 0.7, jx + S * 0.7, jy - S * 0.35, jy + S * 0.35)
@glyph('¥')      # yen
def g_yen(c):
    from . import GLYPHS
    # ROUND 387: `yen=True` -- the Y's arm root as round 386 ruled the yen on;
    # at the 700 the Y's own root now stands further off its spine
    # (aldine.py, Y_GAP_BOLD). Ignored by every other Y.
    g = GLYPHS['Y'](dict(c, yen=True)); x0, y0, x1, y1 = g.bounds
    opt = yen_gap_opt()
    if opt != 'a':
        return _yen_gapped(g, opt)
    if not pen.ITALIC:
        # ROUND 392 -- THE TRUNK BETWEEN THE BARS IS THE STEM'S OWN COLUMN.
        # The roman Y's thick left arm meets its stem 28 units LOWER than the
        # thin right arm does (Regular (380, 292); Bold (338, 295)), so under
        # the upper bar the arm's outer edge stood out of the trunk's left
        # side as a slanted ledge -- the notch round 385 reported on the
        # Regular ¥ ("on the stem's left just under the bars") -- and the
        # right side met the stem square. Between the two bars' centrelines
        # the Y is cut back to the stem's column, read off the trunk just
        # under the arm's join (0.40 cap; read at 0.25, below the lower bar,
        # the column is a unit narrower and left a 1-unit slant above that
        # bar); the bars cover both cut lines, so nothing else moves.
        import shapely.geometry as sg
        row = g.intersection(sg.LineString([(x0 - 10, CAP * 0.40), (x1 + 10, CAP * 0.40)]))
        tx0, _, tx1, _ = row.bounds
        g = g.difference(sg.box(x0 - 50, CAP * 0.34, tx0, CAP * 0.50)).difference(
            sg.box(tx1, CAP * 0.34, x1 + 50, CAP * 0.50))
    return _fill_cracks(geom.ink([g, bar(x0 - 8, x1 + 8, CAP * 0.34, MATH), bar(x0 - 8, x1 + 8, CAP * 0.50, MATH)]))
# 2026-09-24 -- OPTIONS: THE YEN CARRIES THE Y's HAIRLINE GAP. Owner: *"give me
# clever options for the Italic and bold italic yen characters to have a visible
# gap like the Y branch and trunk has."* The italic Y's arm stops 16.8 units
# (drawing; 13.0 in the built 400) short of its spine -- docs/albo-hairline-gap.md.
# Today's two full bars run straight over that join and bury it. ALBO_YEN_GAP
# picks; `a` is today's drawing, byte for byte, and is the default:
#   b  CHANNEL   -- the gap carried DOWN the trunk's right edge through both bars:
#                   each bar fuses to the trunk on the left and stands one gap
#                   off it on the right, as the arm does
#   c  FREE TRUNK -- the same white on BOTH sides: the bars never touch the trunk
#   d  ONE BAR   -- a single bar at the height of the arm's end, split by the gap:
#                   its right half grows out of the arm, its left out of the trunk
#   e  ABOVE     -- both bars lifted over the join to cross the branches, so the
#                   gap stands clear beneath them
# The white is a DESIGNED width, not the cut's own Y gap: the BoldItalic Y's arm
# stands 3.4 units off its spine (1.3 built), which no reader can see, so every
# cut takes the italic 400's 16.8. The options apply to the italics only; the
# roman Y has no gap to echo. ALBO_YEN_GAP_ROMAN=1 applies them upright too,
# for comparison. Read at CALL time: build.py re-draws `a` to hold the cut phase.
def yen_gap_opt():
    # RULED 2026-09-24 (owner): *"for yen, b for italics only"* -- the italics
    # ship the channel (option b); the romans, whose Y has no gap, stay a.
    opt = os.environ.get("ALBO_YEN_GAP", "b" if pen.ITALIC else "a")
    if opt != 'a' and not pen.ITALIC and os.environ.get("ALBO_YEN_GAP_ROMAN", "0") != "1":
        return 'a'
    return opt
def _yen_gapped(g, opt):
    import shapely.geometry as sg
    from shapely.ops import nearest_points
    G = float(os.environ.get("ALBO_YEN_GAP_W", 16.8))
    x0, y0, x1, y1 = g.bounds
    parts = sorted(list(g.geoms) if g.geom_type == 'MultiPolygon' else [g], key=lambda p: -p.area)
    if len(parts) > 1:
        # the italic: the trunk is the long spine, the branch the free arm
        trunk, arm = parts[0], parts[1]
        pa, pb = nearest_points(trunk, arm); gy = (pa.y + pb.y) / 2
    else:
        # the roman: one contour; the trunk is the stem's column below the fork
        row = g.intersection(sg.LineString([(x0 - 10, CAP * 0.25), (x1 + 10, CAP * 0.25)]))
        tx0, _, tx1, _ = row.bounds
        trunk, arm = sg.box(tx0, -50, tx1, CAP * 0.60), None; gy = CAP * 0.42
    # the trunk's centreline, row by row, and everything to its right
    cl = []
    for k in range(0, 61):
        y = -40 + (CAP * 0.75 + 40) * k / 60
        r = trunk.intersection(sg.LineString([(x0 - 50, y), (x1 + 50, y)]))
        if not r.is_empty: cl.append(((r.bounds[0] + r.bounds[2]) / 2, y))
    right = sg.Polygon(cl + [(x1 + 400, cl[-1][1]), (x1 + 400, cl[0][1])])
    halo = trunk.buffer(G, join_style=2).difference(trunk)
    collar = halo.intersection(right) if opt in ('b', 'd') else halo
    L, R = x0 - 8, x1 + 8
    if opt == 'e':
        bars = [bar(L, R, gy + CAP * float(os.environ.get("ALBO_YEN_E_LO", 0.11)), MATH),
                bar(L, R, gy + CAP * float(os.environ.get("ALBO_YEN_E_HI", 0.25)), MATH)]
    elif opt == 'd':
        bars = [bar(L, R, gy + CAP * float(os.environ.get("ALBO_YEN_D_Y", 0.03)), MATH * 1.15)]
    else:
        bars = [bar(L, R, CAP * 0.34, MATH), bar(L, R, CAP * 0.50, MATH)]
    if opt != 'e':
        bars = [b.difference(collar) for b in bars]
    if arm is not None:
        # the arm's own root opened to the same white: a no-op on the Italic
        # (its arm already stands 16.8 off), 13 units off the BoldItalic's
        arm = arm.difference(halo.intersection(right))
        # where the arm's tip lands a few units short of a bar piece (the
        # Italic's lower bar: 7 units, 5 in the font) the two are CLOSED into
        # one, locally -- a slit that narrow is the crack round 384 filled, not
        # the gap. The weld is the HULL of the two within 14 units of their
        # nearest approach (a morphological closing cannot bridge a corner to
        # an edge: the dilated neck is narrower than the erosion that follows).
        fills = []
        for b in bars:
            for p in (list(b.geoms) if b.geom_type == 'MultiPolygon' else [b]):
                d = arm.distance(p)
                if 0 < d < 10:
                    qa, qb = nearest_points(arm, p)
                    near = sg.Point((qa.x + qb.x) / 2, (qa.y + qb.y) / 2).buffer(14)
                    u = arm.union(p)
                    fills.append(u.intersection(near).convex_hull.difference(u).difference(halo))
        # ROUND 392 -- AND WHERE A BAR's UNDERSIDE CROSSES THE ARM's UPPER
        # EDGE A FEW UNITS SHORT OF THE CHANNEL, the white left between them
        # is a nick, not a designed space: at the BoldItalic the arm rides
        # higher and the Italic's 50 x 34-unit triangle under the upper bar
        # closes to a 7 x 6 notch in the channel's right edge (TTF (375, 306),
        # `cmp_jogs.py` 6.7; the ledge the option doc saw at 6x and left).
        # Filled by the hull of the ink in a small box there, kept out of the
        # halo so the channel's width does not move. Where the arm crosses
        # the bar's underside more than 14 units off the channel (the
        # Italic's triangle) nothing is done.
        for b in bars:
            for p in (list(b.geoms) if b.geom_type == 'MultiPolygon' else [b]):
                if not arm.intersects(p) or p.bounds[0] < trunk.bounds[0]:
                    continue
                yb = p.bounds[1] - 0.5
                row = sg.LineString([(x0 - 50, yb), (x1 + 400, yb)])
                ra = arm.intersection(row); rh = trunk.buffer(G, join_style=2).intersection(row)
                if ra.is_empty or rh.is_empty:
                    continue
                xa, xh = ra.bounds[0], rh.bounds[2]
                if 0.0 < xa - xh < 14.0:
                    u = geom.ink([arm, p])
                    box = sg.box(xh - 2.0, yb - 16.0, xa + 6.0, p.bounds[1] + 2.0)
                    fills.append(u.intersection(box).convex_hull.difference(u).difference(halo))
        g = geom.ink([trunk, arm] + fills)
    return _fill_cracks(geom.ink([g] + bars))
@glyph('€')      # euro
def g_euro(c):
    from . import GLYPHS
    g = GLYPHS['C'](c); x0, y0, x1, y1 = g.bounds
    return geom.ink([g, bar(x0 - XH * 0.10, x0 + (x1 - x0) * 0.72, CAP * 0.30, MATH),
                        bar(x0 - XH * 0.10, x0 + (x1 - x0) * 0.72, CAP * 0.46, MATH)])
@glyph('¤')      # generic currency
def g_currency(c):
    r = XH * 0.36
    solid, *_ = ring(r, MID, r, r, w_scale=0.62, floor=HAIR * 0.9)
    parts = [solid]
    for sx, sy in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
        p0 = (r + sx * r * 0.72, MID + sy * r * 0.72); p1 = (r + sx * r * 1.15, MID + sy * r * 1.15)
        parts.append(_s(line(p0, p1), w=MATH * 0.85))
    return geom.ink(parts)
@glyph('¬')      # not sign
def g_logicalnot(c):
    w = XH * 0.80
    return geom.ink([bar(0, w, MID + XH * 0.16, MATH), _s(line((w - MATH / 2, MID + XH * 0.16), (w - MATH / 2, MID - XH * 0.08)), w=MATH)])

# ---------------------------------------------------------------- dingbats
# ROUND 384 -- A CHECK IS TWO STROKES, not one polyline stroke. Offsetting one
# stroke around a 90-degree vertex folds its inner edge over itself: the check
# carried a crack at the vertex in every cut, and the HEAVY check at the bolds
# came out as a slab beside a reversed sliver (glitch CRACK, contour REVERSAL).
# Each leg is now its own stroke, meeting at the vertex in a hull joint, and
# whatever tiny hole the union still leaves is filled.
def _check(w0, w1, w2):
    a, v, b = (0, XH * 0.46), (XH * 0.26, XH * 0.08), (XH * 0.80, XH * 0.92)
    import shapely.geometry as sg
    leg1 = _s(line(a, v), widths([(0.0, w0), (1.0, w1)]), cut1=None, light=1.05)
    leg2 = _s(line(v, b), widths([(0.0, w1), (1.0, w2)]), cut0=None, light=1.05)
    # THE JOINT: the hull of the two legs' ends near the vertex, less the
    # inside angle -- so the outer corner closes cleanly and the crotch stays
    # sharp. Extending each leg past the vertex instead (the first cut) left a
    # stepped foot where the two butt ends crossed.
    R = TH_V * w1 * 1.4
    disk = sg.Point(v).buffer(R)
    hull = sg.MultiPolygon([p for g in (leg1.intersection(disk), leg2.intersection(disk))
                            for p in (g.geoms if g.geom_type == 'MultiPolygon' else [g])]).convex_hull
    def toward(p, k):
        L = math.hypot(p[0] - v[0], p[1] - v[1])
        return (v[0] + (p[0] - v[0]) / L * k, v[1] + (p[1] - v[1]) / L * k)
    inside = sg.Polygon([v, toward(a, R * 3), toward(b, R * 3)])
    return _fill_cracks(geom.ink([leg1, leg2, hull.difference(inside)]))
@glyph('✓')      # check
def g_check(c): return _check(0.72, 1.00, 0.62)
@glyph('✔')
def g_checkheavy(c):
    # The heavy check is the check made heavier with a MITRE dilation, not a
    # second drawing at 1.45x widths: drawn separately, its two thick legs at
    # the 700 met as two blocks with a step between them. One outline, grown.
    return _check(0.72, 1.00, 0.62).buffer(TH_V * 0.16, join_style=2)
@glyph('✗')      # ballot X
def g_ballotx(c):
    h = XH * 0.82
    return geom.ink([_s(line((0, XH * 0.06), (h, XH * 0.06 + h)), w=MATH * 1.05),
                     _s(line((0, XH * 0.06 + h), (h, XH * 0.06)), w=MATH * 1.05)])
@glyph('✘')
def g_ballotxheavy(c):
    h = XH * 0.82
    return geom.ink([_s(line((0, XH * 0.06), (h, XH * 0.06 + h)), w=MATH * 1.55),
                     _s(line((0, XH * 0.06 + h), (h, XH * 0.06)), w=MATH * 1.55)])

# ---------------------------------------------------------------- geometric
def _shape(c, kind, filled, size=None):
    # ROUND 385: upright in the italic -- see `_upright`. A sheared square is a
    # parallelogram, which is a different sign.
    return _upright(_shape_drawn(c, kind, filled, size))

def _shape_drawn(c, kind, filled, size=None):
    import shapely.geometry as sg
    r = (size or XH * 0.34)
    cx, cy = r, MID
    if kind == 'square': pts = [(cx - r, cy - r), (cx + r, cy - r), (cx + r, cy + r), (cx - r, cy + r)]
    elif kind == 'diamond': pts = [(cx, cy - r * 1.18), (cx + r * 0.92, cy), (cx, cy + r * 1.18), (cx - r * 0.92, cy)]
    elif kind == 'up': pts = [(cx - r, cy - r * 0.84), (cx + r, cy - r * 0.84), (cx, cy + r * 1.05)]
    elif kind == 'down': pts = [(cx - r, cy + r * 0.84), (cx + r, cy + r * 0.84), (cx, cy - r * 1.05)]
    elif kind == 'right': pts = [(cx - r * 0.84, cy - r), (cx - r * 0.84, cy + r), (cx + r * 1.05, cy)]
    elif kind == 'left': pts = [(cx + r * 0.84, cy - r), (cx + r * 0.84, cy + r), (cx - r * 1.05, cy)]
    else: pts = None
    if kind == 'circle':
        if filled:
            return geom.poly(superellipse(cx, cy, r, r, 0, 2 * math.pi, 2.0)[:-1], [])
        # ROUND 385: MONOLINE, as the white square and triangle are. It was
        # the pen's ring -- thick at the sides, thin at top and bottom -- which
        # is the letter o's stress, and at the 700 the white circle set beside
        # a word read as an o.
        disc = geom.poly(superellipse(cx, cy, r, r, 0, 2 * math.pi, 2.0)[:-1], [])
        return disc.difference(disc.buffer(-max(MATH * 0.95, HAIR)))
    outer = sg.Polygon(pts)
    if filled: return outer
    return outer.difference(outer.buffer(-max(MATH * 0.95, HAIR)))

@glyph('■')
def g_blacksquare(c): return _shape(c, 'square', True)
@glyph('□')
def g_whitesquare(c): return _shape(c, 'square', False)
@glyph('▪')
def g_blacksmallsquare(c): return _shape(c, 'square', True, XH * 0.21)
@glyph('▫')
def g_whitesmallsquare(c): return _shape(c, 'square', False, XH * 0.21)
@glyph('●')
def g_blackcircle(c): return _shape(c, 'circle', True)
@glyph('○')
def g_whitecircle(c): return _shape(c, 'circle', False)
@glyph('◆')
def g_blackdiamond(c): return _shape(c, 'diamond', True)
@glyph('◇')
def g_whitediamond(c): return _shape(c, 'diamond', False)
@glyph('▲')
def g_blackup(c): return _shape(c, 'up', True)
@glyph('△')
def g_whiteup(c): return _shape(c, 'up', False)
@glyph('▼')
def g_blackdown(c): return _shape(c, 'down', True)
@glyph('▽')
def g_whitedown(c): return _shape(c, 'down', False)
@glyph('▶')
def g_blackright(c): return _shape(c, 'right', True)
@glyph('◀')
def g_blackleft(c): return _shape(c, 'left', True)
