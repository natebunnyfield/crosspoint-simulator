"""The rest of the epub set (round 99, second pass): the superscripts and
subscripts, the fractions, the Greek a technical book uses, the Latin
letters that are not composites, the chess pieces, the card suits and the
music signs.

The split from `symbols.py` is only the order they were drawn in -- that
module took the thirty-eight codepoints MEASURED in the owner's own 34
books, this one takes what he named ("unicode arrows, chess pieces, etc")
plus the eleven the first pass left.

Two constructions here are worth knowing about:

- **The superscripts, subscripts and fractions are the FIGURES**, scaled and
  moved by `_fig_at`, never redrawn -- so round 98's ruling on the 8 reaches
  the squared and the one-half for free, and nothing can drift.
- **The chess pieces are silhouettes, and the white piece is the black one's
  outline** (`_hollow`): that is how the pair is related in every typeface
  that carries them, and it means a change to a piece changes both.
"""
import math
import shapely.geometry as sg
import shapely.affinity as aff
from . import glyph, GLYPHS
from .. import geom, pen
from ..geom import cubic, line, superellipse
from ..primitives import stroke, pen_widths, widths, dot, ring, bar, stem
from ..pen import S, XH, CAP, ASC, DESC, OVER, TH_V, TH_H, HAIR, CUT, BOWL_K
from .stems import DOT_R
from .symbols import MATH, MID, _s

# ---------------------------------------------------------------- spaces
@glyph(' ')      # no-break space: the space's twin, and the corpus's 30 uses
def g_nbspace(c): return sg.Polygon()

# ------------------------------------------------- superscripts / subscripts
SUP_K = 0.62           # the figure's scale as a superior
SUP_Y = XH * 0.46      # its foot, for a superior
SUB_Y = -XH * 0.18     # ... and for an inferior

def _fig_at(c, ch, k, y, src=None):
    """A figure (or any glyph) scaled by k with its foot at y. The outline
    is the shipping one, so every ruling on the figures reaches these."""
    src = src or ch
    if src in '0123456789':   # the figures need their own old-style box in the context
        import latin
        from ..build import isfig  # noqa: F401  (documents the same ASCII-digit rule)
        top, bot = latin.FIG_BOX[src]; c = dict(c, figH=(top - bot) * c["cap"], ch=src)
    g = GLYPHS[src](c); x0, y0, x1, y1 = g.bounds
    g = aff.scale(g, k, k, origin=(x0, y0)); x0, y0, x1, y1 = g.bounds
    return aff.translate(g, -x0, y - y0)

for _i, _sup in enumerate("⁰¹²³⁴⁵⁶⁷⁸⁹"):
    glyph(_sup)((lambda d: (lambda c: _fig_at(c, d, SUP_K, SUP_Y)))(str(_i)))
for _i, _sub in enumerate("₀₁₂₃₄₅₆₇₈₉"):
    glyph(_sub)((lambda d: (lambda c: _fig_at(c, d, SUP_K, SUB_Y)))(str(_i)))
glyph('ⁿ')(lambda c: _fig_at(c, 'n', SUP_K, SUP_Y))       # superior n
glyph('ª')(lambda c: _fig_at(c, 'a', SUP_K, SUP_Y))       # feminine ordinal
glyph('º')(lambda c: _fig_at(c, 'o', SUP_K, SUP_Y))       # masculine ordinal

def _fraction(c, num, den):
    """A built fraction: the numerator superior, the solidus, the
    denominator inferior, each the font's own figure."""
    parts = []
    n = _fig_at(c, num, SUP_K, XH * 0.52); parts.append(n)
    x = n.bounds[2] - S * 0.12
    sl = _s(line((x, -XH * 0.12), (x + XH * 0.44, XH * 1.02)), w=MATH * 0.95)
    parts.append(sl)
    d = _fig_at(c, den, SUP_K, -XH * 0.10)
    parts.append(aff.translate(d, sl.bounds[2] - d.bounds[0] - S * 0.10, 0))
    return geom.ink(parts)

glyph('¼')(lambda c: _fraction(c, '1', '4'))
glyph('½')(lambda c: _fraction(c, '1', '2'))
glyph('¾')(lambda c: _fraction(c, '3', '4'))
glyph('⁄')(lambda c: _s(line((0, -XH * 0.12), (XH * 0.44, XH * 1.02)), w=MATH * 0.95))   # fraction slash

# ---------------------------------------------------------------- Greek
# The letters a technical or scientific book sets in running text. Drawn on
# the same pen as the Latin, at the same x-height, so a formula in a
# paragraph does not change typeface mid-sentence.
def _bowl(cx, cy, rx, ry, ws=1.0):
    solid, *_ = ring(cx, cy, rx, ry, w_scale=ws, floor=HAIR)
    return solid

@glyph('π')      # pi
def g_pi(c):
    w = XH * 0.96
    return geom.ink([bar(0, w, XH, TH_H * 0.92, align='top'),
                     _s(line((XH * 0.22, 0), (XH * 0.17, XH - TH_H * 0.5)), widths([(0.0, 0.92), (1.0, 0.80)])),
                     _s(line((w - XH * 0.22, 0), (w - XH * 0.18, XH - TH_H * 0.5)), widths([(0.0, 1.05), (1.0, 0.92)]))])
@glyph('φ')      # phi
def g_phi(c):
    r = XH * 0.36
    return geom.ink([_bowl(r, XH * 0.50, r, XH * 0.50, 0.84),
                     _s(line((r, -DESC * 0.62), (r, XH + XH * 0.30)), w=TH_V * 0.86)])
@glyph('α')      # alpha
def g_alpha(c):
    r = XH * 0.33
    bowl = _bowl(r, XH * 0.48, r, XH * 0.46, 0.92)
    tail = cubic((r * 1.86, XH * 0.94), (r * 2.02, XH * 0.42), (r * 1.90, XH * 0.16), (r * 2.22, 0))
    return geom.ink([bowl, _s(tail, widths([(0.0, 0.72), (1.0, 0.92)]), cut0=None)])
@glyph('β')      # beta
def g_beta(c):
    x = S * 0.5; h = ASC * 0.86
    return geom.ink([_s(line((x, -DESC * 0.62), (x, h * 0.92)), w=TH_V * 0.92),
                     _bowl(x + XH * 0.30, XH * 0.70, XH * 0.30, XH * 0.30, 0.86),
                     _bowl(x + XH * 0.33, XH * 0.22, XH * 0.33, XH * 0.26, 0.92)])
@glyph('γ')      # gamma
def g_gamma(c):
    return geom.ink([_s(line((0, XH), (XH * 0.42, -DESC * 0.30)), widths([(0.0, 0.66), (1.0, 1.0)])),
                     _s(line((XH * 0.78, XH), (XH * 0.34, XH * 0.30)), widths([(0.0, 0.62), (1.0, 0.92)]))])
@glyph('δ')      # delta
def g_delta(c):
    top = cubic((XH * 0.62, XH * 0.96), (XH * 0.24, XH * 1.06), (XH * 0.20, XH * 0.74), (XH * 0.44, XH * 0.58))
    return geom.ink([_bowl(XH * 0.34, XH * 0.32, XH * 0.34, XH * 0.32, 0.92),
                     _s(top, widths([(0.0, 0.62), (1.0, 0.86)]), cut1=None)])
@glyph('ε')      # epsilon
def g_epsilon(c):
    from .rounds import open_arc
    up = superellipse(XH * 0.30, XH * 0.70, XH * 0.30, XH * 0.30, math.radians(-40), math.radians(200), 2.05)
    lo = superellipse(XH * 0.30, XH * 0.26, XH * 0.30, XH * 0.26, math.radians(160), math.radians(-70), 2.05)
    pr = widths([(0.0, 0.62), (0.5, 1.0), (1.0, 0.68)])
    return geom.ink([_s(up, pr), _s(lo, pr)])
@glyph('θ')      # theta
def g_theta(c):
    r = XH * 0.32
    return geom.ink([_bowl(r, ASC * 0.42, r, ASC * 0.42, 0.86), bar(r * 0.30, r * 1.70, ASC * 0.42, MATH * 0.92)])
@glyph('λ')      # lambda
def g_lambda(c):
    return geom.ink([_s(line((0, 0), (XH * 0.52, ASC * 0.82)), widths([(0.0, 0.72), (1.0, 0.95)])),
                     _s(line((XH * 0.24, ASC * 0.40), (XH * 0.80, 0)), widths([(0.0, 0.72), (1.0, 0.95)]))])
@glyph('μ')      # mu
def g_mu(c):
    return geom.ink([_s(line((0, XH), (0, -DESC * 0.60)), w=TH_V * 0.92),
                     _s(cubic((0, XH * 0.20), (0, 0), (XH * 0.46, -XH * 0.04), (XH * 0.52, XH * 0.30)), widths([(0.0, 0.70), (1.0, 0.88)]), cut0=None),
                     _s(line((XH * 0.52, XH * 0.30), (XH * 0.52, XH)), w=TH_V * 0.86)])
@glyph('ρ')      # rho
def g_rho(c):
    return geom.ink([_s(line((0, XH * 0.50), (0, -DESC * 0.60)), w=TH_V * 0.92),
                     _bowl(XH * 0.32, XH * 0.50, XH * 0.32, XH * 0.50, 0.90)])
@glyph('σ')      # sigma
def g_sigma(c):
    return geom.ink([_bowl(XH * 0.34, XH * 0.34, XH * 0.34, XH * 0.34, 0.92),
                     bar(XH * 0.30, XH * 0.90, XH * 0.68, TH_H * 0.88, align='bottom')])
@glyph('τ')      # tau
def g_tau(c):
    return geom.ink([bar(0, XH * 0.74, XH, TH_H * 0.92, align='top'),
                     _s(line((XH * 0.40, 0), (XH * 0.38, XH - TH_H * 0.5)), widths([(0.0, 0.95), (1.0, 0.86)]))])
@glyph('ω')      # omega
def g_omega(c):
    a = _bowl(XH * 0.26, XH * 0.34, XH * 0.26, XH * 0.34, 0.86)
    b = _bowl(XH * 0.62, XH * 0.34, XH * 0.26, XH * 0.34, 0.86)
    box = sg.box(-XH, -XH, XH * 1.4, XH * 0.10)
    return geom.ink([a.difference(box).buffer(0), b.difference(box).buffer(0),
                     bar(0, XH * 0.20, XH * 0.06, TH_H * 0.86, align='bottom'),
                     bar(XH * 0.68, XH * 0.88, XH * 0.06, TH_H * 0.86, align='bottom')])
@glyph('Δ')      # Delta
def g_Delta(c):
    from ..pen import CS
    tri = sg.Polygon([(0, 0), (CAP * 0.62, CAP), (CAP * 1.24, 0)])
    return tri.difference(tri.buffer(-CS * 0.62))
@glyph('Ω')      # Omega
def g_Omega(c):
    r = CAP * 0.40
    a = _bowl(r, CAP * 0.46, r, CAP * 0.46, 1.0)
    box = sg.box(-CAP, -CAP, CAP * 2, CAP * 0.14)
    return geom.ink([a.difference(box).buffer(0),
                     bar(-r * 0.30, r * 0.52, 0, TH_H, align='bottom'),
                     bar(r * 1.48, r * 2.30, 0, TH_H, align='bottom')])
@glyph('Σ')      # Sigma
def g_Sigma(c):
    w = CAP * 0.66
    return geom.ink([bar(0, w, CAP, TH_H, align='top'), bar(0, w, 0, TH_H, align='bottom'),
                     _s(line((0, CAP - TH_H), (w * 0.52, CAP * 0.50)), widths([(0.0, 0.86), (1.0, 1.0)]), cut0=None),
                     _s(line((w * 0.52, CAP * 0.50), (0, TH_H)), widths([(0.0, 1.0), (1.0, 0.86)]), cut1=None)])
@glyph('Π')      # Pi
def g_Pi(c):
    from ..pen import CS
    w = CAP * 0.76
    return geom.ink([bar(0, w, CAP, TH_H, align='top'), stem(CS * 0.5, 0, CAP - TH_H * 0.5, w=CS, foot='both'),
                     stem(w - CS * 0.5, 0, CAP - TH_H * 0.5, w=CS, foot='both')])
@glyph('Φ')      # Phi
def g_Phi(c):
    from ..pen import CS
    r = CAP * 0.34
    return geom.ink([_bowl(r, CAP * 0.50, r, CAP * 0.34, 1.0), stem(r, 0, CAP, w=CS, top='left', foot='both')])
@glyph('∑')
def g_summation(c): return g_Sigma(c)
@glyph('∏')
def g_product(c): return g_Pi(c)

# ------------------------------------------------- the non-composite Latin
def _joined(c, a, b, overlap=0.18):
    """Two letters run together at their stems: the ligated vowels."""
    ga = GLYPHS[a](c); gb = GLYPHS[b](c)
    ax0, _, ax1, _ = ga.bounds; bx0, _, bx1, _ = gb.bounds
    return geom.ink([ga, aff.translate(gb, ax1 - bx0 - (bx1 - bx0) * overlap, 0)])

glyph('æ')(lambda c: _joined(c, 'a', 'e', 0.10))
glyph('Æ')(lambda c: _joined(c, 'A', 'E', 0.26))
glyph('œ')(lambda c: _joined(c, 'o', 'e', 0.10))
glyph('Œ')(lambda c: _joined(c, 'O', 'E', 0.22))
glyph('ĳ')(lambda c: _joined(c, 'i', 'j', -0.30))
glyph('Ĳ')(lambda c: _joined(c, 'I', 'J', -0.30))

def _slashed(c, ch, over=0.16):
    g = GLYPHS[ch](c); x0, y0, x1, y1 = g.bounds
    d = (x1 - x0) * over; e = (y1 - y0) * over
    sl = _s(line((x0 - d, y0 - e), (x1 + d, y1 + e)), w=max(MATH, HAIR))
    return geom.ink([g, sl])
glyph('ø')(lambda c: _slashed(c, 'o'))
glyph('Ø')(lambda c: _slashed(c, 'O'))

def _barred(c, ch, y=None, x_pad=0.20, w=None):
    """A letter with a crossbar: the Eth, the stroked d, h, l, t, L."""
    g = GLYPHS[ch](c); x0, y0, x1, y1 = g.bounds
    yy = y if y is not None else (y0 + y1) / 2
    d = (x1 - x0) * x_pad
    return geom.ink([g, bar(x0 - d, x1 + d, yy, w or MATH)])
glyph('ð')(lambda c: _crossed_eth(c))
glyph('Ð')(lambda c: _barred(c, 'D', y=CAP * 0.50, x_pad=0.06))
glyph('đ')(lambda c: _barred(c, 'd', y=ASC * 0.86, x_pad=0.10))
glyph('Đ')(lambda c: _barred(c, 'D', y=CAP * 0.50, x_pad=0.06))
glyph('ħ')(lambda c: _barred(c, 'h', y=ASC * 0.86, x_pad=0.10))
glyph('Ħ')(lambda c: _barred(c, 'H', y=CAP * 0.82, x_pad=0.02))
glyph('ŧ')(lambda c: _barred(c, 't', y=XH * 0.22, x_pad=0.16))
glyph('Ŧ')(lambda c: _barred(c, 'T', y=CAP * 0.40, x_pad=-0.18))

def _crossed_eth(c):
    """The eth: the o, with a back that LEAVES the bowl's top-left and rises
    to the ascender as one stroke, crossed near its top. The first cut
    started the back inside the bowl and read as an o with a curl."""
    g = GLYPHS['o'](c); x0, y0, x1, y1 = g.bounds
    top = ASC * 0.82
    back = cubic((x0 + (x1 - x0) * 0.16, y1 - (y1 - y0) * 0.30),
                 (x0 + (x1 - x0) * 0.30, y1 + (top - y1) * 0.46),
                 (x0 + (x1 - x0) * 0.66, y1 + (top - y1) * 0.72),
                 (x1 * 0.96, top))
    bar_y = y1 + (top - y1) * 0.58
    return geom.ink([g, _s(back, widths([(0.0, 0.92), (1.0, 0.58)]), cut0=None),
                     bar(x0 + (x1 - x0) * 0.20, x1 * 1.02, bar_y, MATH * 0.95)])

def _sloped_bar(c, ch, frac=0.42):
    """The Polish l: a bar across the stem at a slope."""
    g = GLYPHS[ch](c); x0, y0, x1, y1 = g.bounds
    yy = y0 + (y1 - y0) * frac; d = max((x1 - x0) * 0.62, S * 0.62)
    sl = _s(line(((x0 + x1) / 2 - d, yy - d * 0.42), ((x0 + x1) / 2 + d, yy + d * 0.42)), w=max(MATH * 0.95, HAIR))
    return geom.ink([g, sl])
glyph('ł')(lambda c: _sloped_bar(c, 'l', 0.52))
glyph('Ł')(lambda c: _sloped_bar(c, 'L', 0.34))

@glyph('þ')      # thorn
def g_thorn(c):
    from .stems import bowl_stem
    x = S / 2
    return geom.ink([stem(x, -c["desc"] * 0.86, c["asc"] * 0.92, top='left', foot='both'),
                     _bowl(x + XH * 0.30, XH * 0.50, XH * 0.32, XH * 0.50, 0.92)])
@glyph('Þ')      # Thorn
def g_Thorn(c):
    from ..pen import CS
    x = CS / 2
    return geom.ink([stem(x, 0, CAP, w=CS, top='left', foot='both'),
                     _bowl(x + CAP * 0.24, CAP * 0.62, CAP * 0.26, CAP * 0.24, 1.0)])
@glyph('ß')      # eszett
def g_germandbls(c):
    """The long s joined to the sharp s: a stem rising to the ascender with
    a shoulder, and a lower bowl that ends in the s's own terminal."""
    x = S * 0.5
    sh = cubic((x, ASC * 0.72), (x, ASC * 0.96), (x + XH * 0.50, ASC * 0.98), (x + XH * 0.48, ASC * 0.62))
    lower = cubic((x + XH * 0.48, ASC * 0.62), (x + XH * 0.44, XH * 0.62), (x + XH * 0.10, XH * 0.58), (x + XH * 0.16, XH * 0.40))
    tail = cubic((x + XH * 0.16, XH * 0.40), (x + XH * 0.62, XH * 0.30), (x + XH * 0.60, -XH * 0.02), (x + XH * 0.18, XH * 0.06))
    pr = widths([(0.0, 0.80), (0.5, 0.95), (1.0, 0.82)])
    return geom.ink([stem(x, 0, ASC * 0.74, top=None, foot='both'),
                     _s(sh, pr, cut0=None, cut1=None), _s(lower, pr, cut0=None, cut1=None),
                     _s(tail, widths([(0.0, 0.82), (0.6, 0.95), (1.0, 0.50)]), cut0=None)])
@glyph('ŋ')      # eng
def g_eng(c):
    g = GLYPHS['n'](c); x0, y0, x1, y1 = g.bounds
    tail = cubic((x1 - TH_V * 0.6, XH * 0.30), (x1 - TH_V * 0.6, -DESC * 0.30), (x1 - XH * 0.30, -DESC * 0.62), (x1 - XH * 0.52, -DESC * 0.46))
    return geom.ink([g, _s(tail, widths([(0.0, 0.92), (1.0, 0.42)]), cut0=None)])
@glyph('Ŋ')      # Eng
def g_Eng(c):
    g = GLYPHS['N'](c); x0, y0, x1, y1 = g.bounds
    tail = cubic((x1 - TH_V * 0.7, CAP * 0.20), (x1 - TH_V * 0.7, -DESC * 0.30), (x1 - CAP * 0.20, -DESC * 0.56), (x1 - CAP * 0.36, -DESC * 0.42))
    return geom.ink([g, _s(tail, widths([(0.0, 0.95), (1.0, 0.44)]), cut0=None)])
@glyph('ſ')      # long s
def g_longs(c):
    from .stems import f_ink
    parts = f_ink(c, parts=True)
    return geom.ink([parts[0], parts[1], bar(S * 0.10, S * 1.05, XH - TH_H * 0.4, TH_H * 0.8)])
@glyph('ĸ')      # kra
def g_kra(c):
    g = GLYPHS['k'](c); x0, y0, x1, y1 = g.bounds
    return aff.translate(g, 0, 0)

# the comma-below of Romanian s and t
@glyph('̦')
def g_commabelow(c):
    from .marks import comma_tail
    return geom.ink([dot(DOT_R * 0.92, -DOT_R * 1.2, DOT_R * 0.92), comma_tail(DOT_R * 0.92, -DOT_R * 1.2)])

# ---------------------------------------------------------------- chess
def _piece_body(top_h, neck_w, base_w, shoulder=0.30):
    """A piece's stem and base: the flared body every chessman shares."""
    return sg.Polygon([(-base_w, 0), (base_w, 0), (base_w, CAP * 0.08), (neck_w * 1.5, CAP * 0.16),
                       (neck_w, CAP * shoulder), (neck_w, top_h), (-neck_w, top_h),
                       (-neck_w, CAP * shoulder), (-neck_w * 1.5, CAP * 0.16), (-base_w, CAP * 0.08)])

def _hollow(g, w=None):
    """The white piece: the black one's outline. Same silhouette, so the
    pair can never disagree about what a rook is.

    The outline's width is a fraction of the CAP HEIGHT, not of the pen:
    round 100 found the white queen, bishop and spade losing counters at the
    SemiBold and Bold, because a pen-derived width thickens with the text
    weight while the piece stays the same size. A pictograph's outline is a
    property of the picture, not of the typeface's weight."""
    return g.difference(g.buffer(-(w or CAP * 0.042)))

def _chess(kind):
    B = CAP * 0.46          # half the base
    N = CAP * 0.13          # half the neck
    parts = []
    if kind == 'pawn':
        parts.append(_piece_body(CAP * 0.52, N * 0.92, B * 0.78))
        parts.append(sg.Point(0, CAP * 0.66).buffer(CAP * 0.17))
    elif kind == 'rook':
        parts.append(_piece_body(CAP * 0.62, N * 1.25, B * 0.86))
        top = sg.box(-B * 0.80, CAP * 0.62, B * 0.80, CAP * 0.90)
        for cx in (-B * 0.36, B * 0.36):   # the crenels
            top = top.difference(sg.box(cx - B * 0.14, CAP * 0.74, cx + B * 0.14, CAP * 0.92))
        parts.append(top)
    elif kind == 'bishop':
        parts.append(_piece_body(CAP * 0.50, N * 0.95, B * 0.80))
        mitre = sg.Polygon([(0, CAP * 1.00), (CAP * 0.24, CAP * 0.66), (CAP * 0.18, CAP * 0.46),
                            (-CAP * 0.18, CAP * 0.46), (-CAP * 0.24, CAP * 0.66)])
        parts.append(mitre.difference(sg.Polygon([(CAP * 0.02, CAP * 0.84), (CAP * 0.20, CAP * 0.62), (CAP * 0.06, CAP * 0.60)])))
        parts.append(sg.Point(0, CAP * 1.04).buffer(CAP * 0.075))
    elif kind == 'queen':
        parts.append(_piece_body(CAP * 0.56, N * 1.05, B * 0.86))
        crown = [(-B * 0.72, CAP * 0.56), (B * 0.72, CAP * 0.56)]
        pts = [(-B * 0.72, CAP * 0.92), (-B * 0.36, CAP * 0.66), (0, CAP * 0.98), (B * 0.36, CAP * 0.66), (B * 0.72, CAP * 0.92)]
        parts.append(sg.Polygon(crown[:1] + pts[::-1] + crown[1:]).buffer(0))
        for x, y in ((-B * 0.72, CAP * 0.96), (0, CAP * 1.02), (B * 0.72, CAP * 0.96)):
            parts.append(sg.Point(x, y).buffer(CAP * 0.075))
    elif kind == 'king':
        parts.append(_piece_body(CAP * 0.56, N * 1.05, B * 0.86))
        parts.append(sg.Polygon([(-B * 0.72, CAP * 0.56), (B * 0.72, CAP * 0.56), (B * 0.56, CAP * 0.86), (-B * 0.56, CAP * 0.86)]))
        parts.append(sg.box(-CAP * 0.055, CAP * 0.86, CAP * 0.055, CAP * 1.14))
        parts.append(sg.box(-CAP * 0.15, CAP * 0.96, CAP * 0.15, CAP * 1.05))
    else:   # knight: the head in profile
        parts.append(sg.Polygon([(-B, 0), (B, 0), (B, CAP * 0.10), (-B, CAP * 0.10)]))
        parts.append(sg.Polygon([
            (-B * 0.55, CAP * 0.10), (B * 0.62, CAP * 0.10), (B * 0.50, CAP * 0.40),
            (B * 0.66, CAP * 0.62), (B * 0.30, CAP * 0.86), (B * 0.10, CAP * 1.00),
            (-B * 0.16, CAP * 0.96), (-B * 0.10, CAP * 0.80), (-B * 0.52, CAP * 0.62),
            (-B * 0.66, CAP * 0.40), (-B * 0.40, CAP * 0.26)]))
    g = geom.ink(parts)
    return aff.translate(g, CAP * 0.50, 0)

_CHESS = [('♔', '♚', 'king'), ('♕', '♛', 'queen'), ('♖', '♜', 'rook'),
          ('♗', '♝', 'bishop'), ('♘', '♞', 'knight'), ('♙', '♟', 'pawn')]
for _white, _black, _kind in _CHESS:
    glyph(_black)((lambda k: (lambda c: _chess(k)))(_kind))
    glyph(_white)((lambda k: (lambda c: _hollow(_chess(k))))(_kind))

# ---------------------------------------------------------------- suits
def _heart(scale=1.0):
    r = CAP * 0.21 * scale
    a = sg.Point(-r * 0.92, CAP * 0.56).buffer(r); b = sg.Point(r * 0.92, CAP * 0.56).buffer(r)
    v = sg.Polygon([(-r * 1.92, CAP * 0.56), (r * 1.92, CAP * 0.56), (0, CAP * 0.02)])
    return geom.ink([a, b, v])
def _spade():
    r = CAP * 0.21
    a = sg.Point(-r * 0.92, CAP * 0.38).buffer(r); b = sg.Point(r * 0.92, CAP * 0.38).buffer(r)
    v = sg.Polygon([(-r * 1.92, CAP * 0.38), (r * 1.92, CAP * 0.38), (0, CAP * 0.92)])
    stem_ = sg.Polygon([(-r * 0.16, CAP * 0.10), (r * 0.16, CAP * 0.10), (r * 0.50, 0), (-r * 0.50, 0)])
    return geom.ink([a, b, v, stem_])
def _club():
    r = CAP * 0.19
    parts = [sg.Point(0, CAP * 0.72).buffer(r), sg.Point(-r * 1.10, CAP * 0.40).buffer(r), sg.Point(r * 1.10, CAP * 0.40).buffer(r),
             sg.Polygon([(-r * 0.16, CAP * 0.10), (r * 0.16, CAP * 0.10), (r * 0.55, 0), (-r * 0.55, 0)]),
             sg.box(-r * 0.16, CAP * 0.10, r * 0.16, CAP * 0.50)]
    return geom.ink(parts)
def _diamond():
    r = CAP * 0.30
    return sg.Polygon([(0, CAP * 0.02), (r * 0.82, CAP * 0.47), (0, CAP * 0.92), (-r * 0.82, CAP * 0.47)])
for _cp, _fn in (('♠', _spade), ('♥', _heart), ('♦', _diamond), ('♣', _club)):
    glyph(_cp)((lambda f: (lambda c: aff.translate(f(), CAP * 0.34, 0)))(_fn))
for _cp, _fn in (('♤', _spade), ('♡', _heart), ('♢', _diamond), ('♧', _club)):
    glyph(_cp)((lambda f: (lambda c: _hollow(aff.translate(f(), CAP * 0.34, 0))))(_fn))

# ---------------------------------------------------------------- music
def _note(beams=0, flag=False):
    r = CAP * 0.15
    head = aff.rotate(aff.scale(sg.Point(0, 0).buffer(1), r * 1.20, r * 0.86), 22)
    parts = [aff.translate(head, r * 1.1, r * 0.9)]
    x = r * 1.1 + r * 1.06
    parts.append(sg.box(x - MATH * 0.55, r * 0.9, x + MATH * 0.55, CAP * 0.94))
    if flag:
        parts.append(sg.Polygon([(x, CAP * 0.94), (x + r * 1.5, CAP * 0.72), (x + r * 1.3, CAP * 0.44), (x, CAP * 0.66)]))
    for i in range(beams):
        y = CAP * (0.94 - 0.16 * i)
        parts.append(sg.Polygon([(x, y), (x + r * 2.6, y - r * 0.30), (x + r * 2.6, y - r * 0.72), (x, y - r * 0.42)]))
    return geom.ink(parts)
glyph('♪')(lambda c: _note(flag=True))
glyph('♫')(lambda c: _twonotes(1))
glyph('♬')(lambda c: _twonotes(2))
def _twonotes(beams):
    r = CAP * 0.15
    a = _note(); b = aff.translate(_note(), r * 2.9, 0)
    beam = [sg.Polygon([(r * 2.16, CAP * (0.94 - 0.16 * i)), (r * 5.06, CAP * (0.94 - 0.16 * i)),
                        (r * 5.06, CAP * (0.94 - 0.16 * i) - r * 0.42), (r * 2.16, CAP * (0.94 - 0.16 * i) - r * 0.42)])
            for i in range(beams)]
    return geom.ink([a, b] + beam)
@glyph('♭')      # flat
def g_flat(c):
    x = S * 0.4
    return geom.ink([_s(line((x, -CAP * 0.06), (x, CAP * 1.02)), w=TH_V * 0.72),
                     _s(cubic((x, CAP * 0.40), (x + CAP * 0.30, CAP * 0.46), (x + CAP * 0.26, CAP * 0.06), (x, CAP * 0.14)),
                        widths([(0.0, 0.62), (0.5, 0.95), (1.0, 0.62)]), cut0=None, cut1=None)])
@glyph('♯')      # sharp
def g_sharp(c):
    w = CAP * 0.34
    parts = [_s(line((w * 0.30, -CAP * 0.06), (w * 0.30, CAP * 0.92)), w=TH_V * 0.55),
             _s(line((w * 0.78, -CAP * 0.02), (w * 0.78, CAP * 0.96)), w=TH_V * 0.55)]
    for y in (CAP * 0.30, CAP * 0.58):
        parts.append(_s(line((0, y), (w * 1.08, y + CAP * 0.10)), w=MATH * 1.15))
    return geom.ink(parts)
@glyph('♮')      # natural
def g_natural(c):
    w = CAP * 0.26
    return geom.ink([_s(line((0, CAP * 0.06), (0, CAP * 0.86)), w=TH_V * 0.55),
                     _s(line((w, CAP * 0.14), (w, CAP * 0.96)), w=TH_V * 0.55),
                     _s(line((0, CAP * 0.62), (w, CAP * 0.70)), w=MATH * 1.05),
                     _s(line((0, CAP * 0.30), (w, CAP * 0.38)), w=MATH * 1.05)])
