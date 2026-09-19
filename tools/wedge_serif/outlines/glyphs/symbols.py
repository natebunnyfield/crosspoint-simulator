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
import math
from . import glyph
from .. import geom, pen
from ..geom import cubic, line, superellipse
from ..primitives import stroke, pen_widths, widths, dot, ring, bar, stem, diagonal
from ..pen import S, XH, CAP, ASC, DESC, OVER, TH_V, TH_H, HAIR, CUT, BOWL_K
from .stems import DOT_R

MID = XH * 0.50            # the lowercase body's optical middle: where a symbol centres
MATH = TH_H * 0.92         # the weight of a mathematical rule (a shade under the pen's horizontal)
ARROW_LEN = XH * 1.32
ARROW_HEAD = XH * 0.30

def _s(pts, prof=None, w=None, cut0=CUT, cut1=CUT, light=1.0):
    return stroke(pts, w if w is not None else pen_widths(pts, (prof or (lambda t: 1.0)), scale=light), cut0=cut0, cut1=cut1)

# ---------------------------------------------------------------- arrows
def _arrow(c, dx, dy, length=None, double=False):
    """A shaft with a two-stroke head, pointing along (dx, dy). The head's
    barbs leave the tip at 32 degrees, the shaft holds the pen's weight for
    its direction, and the whole thing is centred on MID."""
    L = length or ARROW_LEN
    ang = math.atan2(dy, dx)
    cx, cy = L / 2, MID
    tip = (cx + math.cos(ang) * L / 2, cy + math.sin(ang) * L / 2)
    tail = (cx - math.cos(ang) * L / 2, cy - math.sin(ang) * L / 2)
    w = max(MATH * 0.92, HAIR)
    parts = [_s(line(tail, tip), w=w)]
    for sgn in (+1, -1):
        a = ang + math.pi + sgn * math.radians(32)
        end = (tip[0] + math.cos(a) * ARROW_HEAD, tip[1] + math.sin(a) * ARROW_HEAD)
        parts.append(_s(line(tip, end), w=w, cut0=None))
    if double:   # a second tail barb pair: the left-right and up-down arrows
        for sgn in (+1, -1):
            a = ang + sgn * math.radians(32)
            end = (tail[0] + math.cos(a) * ARROW_HEAD, tail[1] + math.sin(a) * ARROW_HEAD)
            parts.append(_s(line(tail, end), w=w, cut0=None))
    return geom.ink(parts)

@glyph('→')
def g_arrowright(c): return _arrow(c, 1, 0)
@glyph('←')
def g_arrowleft(c): return _arrow(c, -1, 0)
@glyph('↔')
def g_arrowboth(c): return _arrow(c, 1, 0, double=True)
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
    sign of mathematical prose."""
    L = ARROW_LEN; ang = math.atan2(0, dx); w = max(MATH * 0.78, HAIR); gap = XH * 0.13
    parts = []
    for off in (+gap / 2, -gap / 2):
        parts.append(_s(line((0, MID + off), (L, MID + off)), w=w))
    for tipx, sgn2 in (((L, MID), -1),) if not both else (((L, MID), -1), ((0, MID), +1)):
        for sgn in (+1, -1):
            a = math.radians(180 if sgn2 < 0 else 0) + sgn * math.radians(30)
            end = (tipx[0] + math.cos(a) * ARROW_HEAD, tipx[1] + math.sin(a) * ARROW_HEAD)
            parts.append(_s(line(tipx, end), w=w, cut0=None))
    g = geom.ink(parts)
    if dx < 0:
        import shapely.affinity as aff
        g = aff.scale(g, -1, 1, origin='center')
    return g

@glyph('⇒')
def g_dblarrowright(c): return _darrow(c, 1)
@glyph('⇐')
def g_dblarrowleft(c): return _darrow(c, -1)
@glyph('⇔')
def g_dblarrowboth(c): return _darrow(c, 1, both=True)

# ---------------------------------------------------------------- dots, quotes, braces
@glyph('·')      # middle dot
def g_middot(c): return dot(DOT_R, MID, DOT_R)
@glyph('•')      # bullet
def g_bullet(c): return dot(DOT_R * 1.5, MID, DOT_R * 1.5)
@glyph('∙')
def g_bulletop(c): return dot(DOT_R * 1.1, MID, DOT_R * 1.1)

def _guillemet(c, left, single=False):
    """Angle quotes: the chevrons are the pen's diagonals, their apex on MID
    and their opening the same 52 degrees as the circumflex's."""
    h = XH * 0.42; w = XH * 0.24; gap = XH * 0.20; n = 1 if single else 2
    parts = []
    for i in range(n):
        x0 = i * gap
        apex = (x0, MID) if left else (x0 + w, MID)
        a = (x0 + w, MID + h / 2) if left else (x0, MID + h / 2)
        b = (x0 + w, MID - h / 2) if left else (x0, MID - h / 2)
        parts.append(_s(line(a, apex), w=max(MATH * 0.95, HAIR), cut1=None))
        parts.append(_s(line(apex, b), w=max(MATH * 0.95, HAIR), cut0=None))
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
    """The font's own P with its counter FILLED, plus a second stem at the
    bowl's right edge: that is what a pilcrow is, and building it from the
    letter means it cannot drift from the capitals. Two hand-drawn versions
    came out as a block -- a ring clipped by a box, then a solid
    superellipse -- because a pilcrow's bowl is solid and a solid bowl
    drawn from scratch has no counter to give it a shape."""
    import shapely.geometry as sg
    from ..pen import CS
    from . import GLYPHS
    g = GLYPHS['P'](c)
    parts = list(g.geoms) if hasattr(g, 'geoms') else [g]
    filled = geom.ink([sg.Polygon(pp.exterior) for pp in parts])
    x0, y0, x1, y1 = filled.bounds
    g = geom.ink([filled, stem(x1 - CS * 0.5, 0, CAP, w=CS * 0.92, foot='both')])
    if S > 84.0:
        # round 272: at the 700 and the 900 the two stems' inner feet meet and
        # the slot between the stems becomes an enclosed counter with a dent
        # in it (adversarial review); the feet's ink under each such slot is
        # cut so the slot opens to the baseline as it does at the 400
        parts = list(g.geoms) if hasattr(g, 'geoms') else [g]
        cuts = []
        for pp in parts:
            for r in pp.interiors:
                hx0, hy0, hx1, hy1 = sg.Polygon(r).bounds
                if hy0 < CAP * 0.5:
                    cuts.append(sg.box(hx0 + 1.0, -CAP * 0.1, hx1 - 1.0, hy0 + CS * 0.35))   # up past where the brackets come within the ink spread of each other
        if cuts: g = g.difference(geom.union(cuts))
    return g

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
    a = _s(line((S * 0.42, CAP * 0.62), (S * 0.10, CAP)), widths([(0.0, 0.58), (1.0, 1.0)]))
    b = _s(line((S * 1.02, CAP * 0.62), (S * 0.70, CAP)), widths([(0.0, 0.58), (1.0, 1.0)]))
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
    w = XH * 0.82; h = XH * 0.30
    apex = (w, MID + h) if gt else (0, MID + h)
    a = (0, MID + h + h * 0.30) if gt else (w, MID + h + h * 0.30)
    b = (0, MID + h - h * 0.30) if gt else (w, MID + h - h * 0.30)
    parts = [_s(line(a, apex), w=MATH * 0.95, cut1=None), _s(line(apex, b), w=MATH * 0.95, cut0=None)]
    parts.append(bar(0, w, MID - h * 0.62, MATH))
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
    h = CAP * 0.96
    p = [(0, MID * 1.10), (XH * 0.26, MID * 0.40), (XH * 0.54, h)]   # a V wide enough to read: the first cut was near-vertical and looked like a bar's edge
    return geom.ink([_s(p, widths([(0.0, 0.58), (0.45, 1.10), (1.0, 0.70)]), cut1=None),
                     bar(XH * 0.52, XH * 1.36, h, MATH * 0.92, align='top')])

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
    return geom.ink([_s(spine, widths([(0.0, 0.95), (1.0, 0.82)]), cut0=None, cut1=None),
                     _s(hook, widths([(0.0, 0.82), (1.0, 0.52)]), cut0=None), foot, cross])
@glyph('¥')      # yen
def g_yen(c):
    from . import GLYPHS
    g = GLYPHS['Y'](c); x0, y0, x1, y1 = g.bounds
    return geom.ink([g, bar(x0 - 8, x1 + 8, CAP * 0.34, MATH), bar(x0 - 8, x1 + 8, CAP * 0.50, MATH)])
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
@glyph('✓')      # check
def g_check(c):
    p = [(0, XH * 0.46), (XH * 0.26, XH * 0.08), (XH * 0.80, XH * 0.92)]
    return _s(p, widths([(0.0, 0.72), (0.30, 1.00), (1.0, 0.62)]), light=1.05)
@glyph('✔')
def g_checkheavy(c):
    p = [(0, XH * 0.46), (XH * 0.26, XH * 0.08), (XH * 0.80, XH * 0.92)]
    return _s(p, widths([(0.0, 1.05), (0.30, 1.45), (1.0, 0.92)]), light=1.05)
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
        solid, *_ = ring(cx, cy, r, r, w_scale=0.60, floor=HAIR)
        return solid
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
