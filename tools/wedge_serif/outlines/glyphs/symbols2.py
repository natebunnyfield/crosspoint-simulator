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
from .symbols import _fill_cracks
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
# ROUND 260, owner 2026-09-19 ("all commonly needed ... characters"): the
# THIRDS and the EIGHTH, built the same way from the same figures, so every
# ruling on a digit reaches them too. A recipe book and a ruler both want them
# and Albo carried only the quarters and the half.
glyph('⅓')(lambda c: _fraction(c, '1', '3'))
glyph('⅔')(lambda c: _fraction(c, '2', '3'))
glyph('⅛')(lambda c: _fraction(c, '1', '8'))
glyph('⅜')(lambda c: _fraction(c, '3', '8'))
glyph('⅝')(lambda c: _fraction(c, '5', '8'))
glyph('⅞')(lambda c: _fraction(c, '7', '8'))
glyph('⁄')(lambda c: _s(line((0, -XH * 0.12), (XH * 0.44, XH * 1.02)), w=MATH * 0.95))   # fraction slash

# ---------------------------------------------------------------- Greek
# The letters a technical or scientific book sets in running text, drawn on
# the same pen as the Latin, at the same x-height, so a formula in a
# paragraph does not change typeface mid-sentence.
#
# ROUND 373 -- TRACED. Owner 2026-09-23, after seeing this set beside
# reference faces: *"for greek letters: they are mostly wrong, trace"*. They
# were: every lowercase ran at about two thirds of the width a reference gives
# it against its own o, the delta did not ascend at all, the beta, theta and
# lambda stopped 120-140 units under the ascender, the gamma, mu and rho
# descended 100-170 units short, the omega was a two-thirds-height subscript,
# the sigma stood 0.75 of the x-height, and the capital Delta was a third
# wider than any reference. Round 371 found the epsilon MIRRORED the same way,
# by looking; `cmp_greek.py` is that look as a script.
#
# THE METHOD. `cmp_greek.py runs` maps each reference INTO ALBO'S UNITS --
# vertically onto Albo's own x-height, ascender and descender, horizontally by
# the two faces' o widths -- and cuts it with scanlines, so every stroke's
# centre can be read at every height. The skeletons below are the MEDIAN of
# Iowan Old Style, Georgia and Times (Palatino where its letter has the same
# structure; its pi, rho and tau are cursive forms and are not in the median),
# in Regular units against an o 465 wide. Every x is scaled by `_u(c)`, this
# build's o over that o, so a letter keeps its proportion to the o at every
# weight and width. Measuring a reference is research; nothing here is a
# reference's outline -- the strokes are Albo's pen (`pen_widths` for the
# straight and diagonal strokes, the o's round pen for the curves), Albo's
# ring for the bowls, the c's finial for the free round ends, Albo's wedges
# and bars. The per-letter targets, the before/after IoU against each
# reference and the gates are docs/albo-greek-2026-09-23.md.
from .rounds import O_RX, O_RX_ADJ, O_W_ADJ, O_FLOOR_ADJ
from ..primitives import bowl_widths, finial_widths, finial_cut, wedge
from ..pen import WL, WD, CAP_BAR, CS
from ..geom import catmull, join


def _bowl(cx, cy, rx, ry, ws=1.0):
    """The pre-373 Greek bowl (hairline floor). Kept for the thorn."""
    solid, *_ = ring(cx, cy, rx, ry, w_scale=ws, floor=HAIR)
    return solid

def _u_roman(c):
    """This build's ROMAN o width over the Regular's 465 (`rounds.g_o`'s
    construction)."""
    return 2 * (O_RX * O_RX_ADJ * c['wf'] + TH_V / 2 * O_W_ADJ) / 465.0

def _u(c):
    """The traced skeletons' unit: this build's o width over the Regular's
    465. With no hand installed that is the ROMAN o (`_u_roman`), in both
    styles -- the sheared-roman italic Greek of rounds 373-375 used it. The
    cursive italic's hand (round 379) supplies its own: the ITALIC's Latin
    analogue over the roman's."""
    if _HAND is not None: return _HAND.u(c)
    return _u_roman(c)

# ROUND 379 -- THE HAND. The italic's cursive Greek (`glyphs/greek_italic.py`)
# draws the letters whose construction the italic references keep -- the
# skeleton traced here -- in the ITALIC's own parts: the italic o's ring and
# round pen, its stem, head and exit. It installs a hand object here for the
# duration of one draw (`hand()`), and the five helpers below hand their work
# to it. With no hand installed -- the roman, and every build before round 379
# -- each helper runs exactly the code it always ran.
_HAND = None

class hand:
    """`with hand(H): g = g_beta(c)` -- draw one letter in another hand."""
    def __init__(self, h): self.h = h
    def __enter__(self):
        global _HAND
        self.prev = _HAND; _HAND = self.h
    def __exit__(self, *a):
        global _HAND
        _HAND = self.prev

def _oring(cx, cy, rx, ry):
    """A closed bowl on the o's own weight (`rounds.g_o`: O_W_ADJ on the
    round pen, the hair floored at O_FLOOR_ADJ of the stem)."""
    if _HAND is not None: return _HAND.oring(cx, cy, rx, ry)
    return ring(cx, cy, rx, ry, w_scale=O_W_ADJ, floor=S * O_FLOOR_ADJ)

def _rw(center, prof=None):
    """Widths on the o's round pen along a centerline."""
    p = (lambda t: O_W_ADJ * prof(t)) if prof else (lambda t: O_W_ADJ)
    return bowl_widths(center, p, floor=S * O_FLOOR_ADJ)

def _path(pts):
    return catmull(pts) if len(pts) > 2 else line(pts[0], pts[1])

def _round(pts, prof=None, cut0=None, cut1=None, fin0=False, fin1=False):
    """A round stroke through traced points, on the o's pen; fin0/fin1 give
    that end the c's finial (its swell and its face)."""
    if _HAND is not None: return _HAND.round(pts, prof, cut0, cut1, fin0, fin1)
    center = _path(pts); wf = _rw(center, prof)
    if fin0: wf = finial_widths(wf, True); cut0 = finial_cut(center, True)
    if fin1: wf = finial_widths(wf, False); cut1 = finial_cut(center, False)
    return stroke(center, wf, cut0=cut0, cut1=cut1)

def _pen(pts, prof=None, cut0=None, cut1=None, fin0=False, fin1=False, center=None):
    """A straight or diagonal stroke through traced points, on the pen (the
    26-degree nib the Latin stems, arches and diagonals are drawn with)."""
    if _HAND is not None: return _HAND.pen(pts, prof, cut0, cut1, fin0, fin1, center)
    center = center or _path(pts); wf = pen_widths(center, prof)
    if fin0: wf = finial_widths(wf, True); cut0 = finial_cut(center, True)
    if fin1: wf = finial_widths(wf, False); cut1 = finial_cut(center, False)
    return stroke(center, wf, cut0=cut0, cut1=cut1)

def _tail(x, y0, dx, rise, u):
    """A stem's foot turned right into a rising tail: the t's own tail
    (`stems.g_t`), which is what the alpha, the pi's right leg and the tau
    end in, in every reference."""
    return join(line((x, y0), (x, 125)), cubic((x, 125), (x, -OVER * 0.5), (x + dx * 0.56 * u, -OVER * 0.5), (x + dx * u, rise)))

def _lc_stem(x, y0, y1, top=None):
    """A lowercase Greek stem: the Latin stem, but with cap=True so the
    italic's calligraphic entry and exit (`primitives.stem`) are not added --
    the italic Greek is the roman Greek sheared."""
    if _HAND is not None: return _HAND.lc_stem(x, y0, y1, top)
    return stem(x, y0, y1, w=TH_V, top=top, foot=None, cap=True, ent_span=(min(y0, 0.0), max(y1, XH)))

def _close(g):
    """Above stem 84, a 4-unit mitre CLOSE: fills a crotch that two heavy
    strokes leave as a grazing sliver (the bold gamma's V and epsilon's
    waist read HAIR in `cmp_contour_hairs`), and moves nothing wider than
    8 units -- the device `_barred` uses for the bold italic."""
    if S > 84.0:
        return g.buffer(4.0, join_style=2).buffer(-4.0, join_style=2)
    return g

SIGMA_BAR_SWELL = 1.30   # the bar's underside drops away from the crown, so it crosses the bowl's shoulder where the shoulder is steep

def _heavy(g):
    """Above stem 84 every counter drawn from STROKES (not a ring) is made its
    own convex hull -- the 2026-09-19 ruling, as `g_germandbls` applies it."""
    if S > 84.0:
        from .. import primitives as _PR
        return _PR.convex_holes(g)
    return g

@glyph('α')      # alpha
def g_alpha(c):
    """The o's ring with a stroke standing on its right side: the stroke
    runs from the x-height to the baseline and turns right into the t's
    tail, and the ring's upper and lower right corners curve away from it,
    which is the two crotches that make an alpha. Traced: the stroke's centre
    at 0.80 of the o's width, the tail's end 0.28 o past it at 45 units."""
    u = _u(c); xs = 370 * u
    rx = (xs + TH_V / 2 - 4) / 2
    ring_, *_ = _oring(rx, XH / 2, rx, XH / 2 + OVER)
    path = join(line((xs + 12 * u, XH + 10), (xs, 125)), cubic((xs, 125), (xs, -OVER * 0.5), (xs + 70 * u, -OVER * 0.5), (xs + 128 * u, 50)))
    st = _pen(None, widths([(0.0, 1.0), (0.80, 1.0), (1.0, 1.25)]), cut0=CUT, cut1=CUT, center=path)
    return geom.ink([ring_, st])

BETA_OPEN_GAP = 80.0   # the waist tip's centre, units (x u) right of the stem's edge, at and under stem 84

@glyph('β')      # beta
def g_beta(c):
    """The stem from the descender to 0.70 of the ascender, turning over the
    top into the upper bowl (right side 0.76 o), down to the WAIST at
    y 392, where the stroke turns out into the wider lower bowl (0.84 o) and
    comes back into the stem at the baseline. The references do not close
    the waist on the stem -- its tip stops about half a stem short, and the
    two counters are one. That is drawn at and under stem 84. Above 84 the
    tip runs into the stem: an open waist is a counter indented by design,
    and the 2026-09-19 ruling is that a 700's counters are not indented."""
    u = _u(c); x = 45 * u
    tip = (x + TH_V / 2 + BETA_OPEN_GAP * u, 392) if S <= 84.0 else (x, 394)
    ent = TH_V / (S * 1.0 * O_W_ADJ)      # the curve leaves the stem at the stem's own width
    up = _round([(x, 470), (x + 4 * u, 600), (x + 38 * u, 700), (x + 118 * u, 752), (x + 210 * u, 752),
                 (x + 286 * u, 712), (x + 310 * u, 625), (x + 305 * u, 540), (x + 282 * u, 468), (x + 238 * u, 420),
                 (x + 175 * u, 398), tip],
                widths([(0.0, ent), (0.10, 1.0), (0.86, 1.0), (1.0, 0.25)]))
    lo = _round([tip, (x + 180 * u, 388), (x + 262 * u, 362), (x + 322 * u, 298), (x + 342 * u, 212),
                 (x + 332 * u, 132), (x + 292 * u, 58), (x + 215 * u, 8), (x + 125 * u, 6), (x + 50 * u, 38),
                 (x + 6 * u, 100), (x, 160)],
                widths([(0.0, 0.25), (0.12, 1.0), (0.90, 1.0), (1.0, ent)]))
    st = _lc_stem(x, -DESC, 560)
    return _heavy(geom.ink([st, up, lo]))

@glyph('γ')      # gamma
def g_gamma(c):
    """Two arms from the x-height meeting in a V on the baseline, and a
    straight descender from the V. The left arm is the thick one (it runs
    down-right, so the pen makes it so) and starts in a curl at the top left;
    the right arm is the thin one and starts on the c's finial. Traced: the
    V at 0.53 o, the right arm's top at 0.95 o, the descender straight down
    to the descender line."""
    u = _u(c); jx = 248 * u
    left = _pen([(14 * u, 408), (55 * u, 432), (100 * u, 405), (137 * u, 340), (162 * u, 280), (187 * u, 215),
                 (212 * u, 150), (232 * u, 88), (jx, -15)], widths([(0.0, 1.0), (0.85, 1.0), (1.0, 0.80)]), fin0=True)
    right = _pen([(440 * u, 432), (408 * u, 388), (370 * u, 280), (320 * u, 150), (283 * u, 75), (jx + 2 * u, -15)],
                 widths([(0.0, 1.0), (0.85, 1.0), (1.0, 0.80)]), fin0=True)
    desc = _lc_stem(jx - 3 * u, -DESC, 60)
    return _close(geom.ink([left, right, desc]))

@glyph('δ')      # delta
def g_delta(c):
    """The o, and a neck that leaves the top of the bowl up and to the LEFT,
    rises to the ascender and hooks over to the right into the c's finial.
    Traced: the neck's back at 0.22 o at 0.75 of the ascender, the hook's
    top on the ascender line, its end at 0.81 o, 100 units down."""
    u = _u(c); rx = 226 * u
    bowl, *_ = _oring(rx, XH / 2, rx, XH / 2 + OVER)
    neck = _round([(268 * u, XH + OVER - 22), (225 * u, 452), (178 * u, 490), (122 * u, 562), (104 * u, 640),
                   (128 * u, 714), (210 * u, 756), (302 * u, 747), (362 * u, 708), (378 * u, 668)],
                  widths([(0.0, 0.55), (0.10, 1.0)]), fin1=True)
    return geom.ink([bowl, neck])

@glyph('ε')      # epsilon
def g_epsilon(c):
    """Two bowls opening RIGHT (round 371 found the old one mirrored): the
    upper narrower and set in, the lower wider, meeting on the left at a
    waist from which a short tongue runs right. Both free ends take the c's
    finial. The two arcs END at the waist rather than cross there (round 371
    recorded the old X-crossing's spurs), each thinned to about the tongue's
    weight so their end faces lie inside it."""
    u = _u(c); w = (112 * u, 222)
    up = _round([(330 * u, 372), (320 * u, 410), (272 * u, 433), (190 * u, 436), (112 * u, 416), (70 * u, 362),
                 (68 * u, 295), (90 * u, 244), w], widths([(0.0, 1.0), (0.84, 1.0), (1.0, 0.55)]), fin0=True)
    lo = _round([w, (70 * u, 196), (50 * u, 125), (68 * u, 48), (145 * u, 4), (250 * u, 2), (328 * u, 32), (370 * u, 92)],
                widths([(0.0, 0.55), (0.14, 1.0)]), fin1=True)
    tongue = _s(line((w[0] - 12 * u, 219), (262 * u, 216)), w=TH_H * 1.05, cut0=None, cut1=CUT)
    return _close(geom.ink([up, lo, tongue]))

@glyph('θ')      # theta
def g_theta(c):
    """A tall oval on the o's weight from the baseline to the ascender, 0.97
    of the o wide, crossed at 350 by a bar buried in both walls."""
    u = _u(c); rx = 225 * u; top = ASC + 2
    ring_, *_ = _oring(rx, (top - OVER) / 2, rx, (top + OVER) / 2)
    return geom.ink([ring_, bar(rx * 0.12, rx * 1.88, 350, TH_H * 1.05)])

@glyph('λ')      # lambda
def g_lambda(c):
    """The long stroke from the ascender, starting in a curl on the c's
    finial and running down to the right into a rising foot; the short leg
    leaves it at 0.92 of the x-height and runs down-left to a flat foot with
    the A's bracket (`caps_straight.g_A`) at 0.7 of its size. Traced: the
    long stroke's centre at 0.54 o at the x-height, the leg's foot at 0.13 o."""
    u = _u(c)
    long_ = _pen([(68 * u, 692), (112 * u, 748), (178 * u, 728), (208 * u, 645), (230 * u, 560), (250 * u, 470),
                  (272 * u, 380), (300 * u, 280), (322 * u, 215), (343 * u, 150), (366 * u, 90), (398 * u, 38),
                  (445 * u, 12), (488 * u, 32)], widths([(0.0, 1.0), (0.90, 1.0), (1.0, 1.2)]), fin0=True, cut1=CUT)
    p0, p1 = (62 * u, 0.0), (265 * u, 395)
    tn = geom.tangents(line(p0, p1))[0]
    lw = pen.th_t(tn)
    leg = stroke(line(p0, p1), lw, cut0=-math.atan2(tn[0], tn[1]))
    Apt = (p0[0] - lw / 2 / tn[1], 0.0)
    foot = wedge(Apt, (0, -1), (-1, 0), WL * 0.9 * 0.7, WD * 0.9 * 0.7, 0.0,
                 edge_at=lambda d: (Apt[0] + tn[0] * d, tn[1] * d))
    return geom.ink([long_, leg, foot])

@glyph('μ')      # mu
def g_mu(c):
    """The u (`arches.g_u`, round 51's, in the roman) with its left stem run
    down to the descender line -- which is what a mu is in every reference,
    so it is built from the u's own construction and weights."""
    xh = XH; x0 = S / 2; x1 = x0 + pen.NW
    over_c = OVER - TH_H / 2
    left = _lc_stem(x0, -DESC, xh, top='left')
    cy = (8 * (-over_c) - xh * 0.4 - xh * 0.42) / 6
    center = cubic((x0, xh * 0.4), (x0, cy), (x1, cy), (x1 + 4, xh * 0.42))
    base = pen_widths(center)
    from .. import primitives as _PR
    floor = S * _PR.BOWL['arch_floor'] if (_PR.BOWL and _PR.BOWL.get('arch_floor')) else 0.0
    u_end = 0.70
    wfn = lambda t: max(base(t) * (1.0 if t < 0.7 else (u_end + (1 - u_end) * (1 - (3 * ((t - 0.7) / 0.3) ** 2 - 2 * ((t - 0.7) / 0.3) ** 3)))), floor)
    bowl_ = stroke(center, wfn)
    right = stem(x1, 0, xh, w=TH_V, top='left', foot='right', top_len=0.85, cap=True)
    return geom.ink([left, right, bowl_])

@glyph('π')      # pi
def g_pi(c):
    """A bar on the x-height whose left end drops in the bar's hanging wedge
    (the references all turn it down there), a left leg that curves down to
    the left into the c's finial, and a straight right leg ending in the t's
    tail. Traced: 1.12 o wide, the legs at 0.40 and 0.83 o."""
    u = _u(c); w = 520 * u; th = TH_H * 1.15
    b = bar(0, w, XH, th, align='top', wedges=[('left', -1)])
    left = _pen([(185 * u, XH - th / 2), (184 * u, 300), (176 * u, 200), (158 * u, 105), (122 * u, 38), (78 * u, 8)],
                fin1=True)
    x = 385 * u
    right = _pen(None, widths([(0.0, 1.0), (0.80, 1.0), (1.0, 1.25)]), cut1=CUT, center=_tail(x, XH - th / 2, 128, 50, u))
    return geom.ink([b, left, right])

@glyph('ρ')      # rho
def g_rho(c):
    """The o, 0.96 of its width, with a straight stem standing on its left
    side from the middle of the bowl to the descender line, its outer edge on
    the bowl's -- the p's stem without the p's shoulder, which is the
    difference between the two letters."""
    u = _u(c); rx = 223 * u
    bowl, *_ = _oring(rx, XH / 2, rx, XH / 2 + OVER)
    st = _lc_stem(TH_V / 2 + 2, -DESC, XH * 0.5)
    return geom.ink([bowl, st])

@glyph('σ')      # sigma
def g_sigma(c):
    """The o, its top on a flat line 8 units over the x-height, and a bar that
    leaves the top of the bowl and runs out to the right to 1.11 o. The bar is
    exactly as thick as the ring's top wall and starts at the ring's crown, so
    its underside is the counter's own top there: no step on the outside and
    no ledge inside (round 371 found the old bar GRAZING the bowl, which is a
    hair; round 373 found a thicker bar would have dented the counter)."""
    u = _u(c); rx = 232 * u; top = XH + 8
    bowl, *_ = _oring(rx, (top - OVER) / 2, rx, (top + OVER) / 2)
    from .. import primitives as _PR
    th = max(_PR.bowl_th((1.0, 0.0)) * O_W_ADJ, S * O_FLOOR_ADJ)
    b = bar(rx, 518 * u, top, th, align='top', prof=widths([(0.0, 1.0), (0.55, SIGMA_BAR_SWELL)]))
    return geom.ink([bowl, b])

@glyph('τ')      # tau
def g_tau(c):
    """The pi's bar with its dropped left end, and one stem a little left of
    the middle ending in the t's tail. Traced: 0.88 o wide, the stem at
    0.41 o."""
    u = _u(c); w = 408 * u; th = TH_H * 1.15
    b = bar(0, w, XH, th, align='top', wedges=[('left', -1)])
    x = 190 * u
    st = _pen(None, widths([(0.0, 1.0), (0.80, 1.0), (1.0, 1.25)]), cut1=CUT, center=_tail(x, XH - th / 2, 150, 52, u))
    return geom.ink([b, st])

@glyph('φ')      # phi
def g_phi(c):
    """U+03C6 is the LOOPED phi -- Unicode's reference glyph since 3.0, and
    four of the five references (Palatino draws the stroked form, which is
    U+03D5). One stroke: it starts on the c's finial at the top left, runs
    down the left side, round the bottom, up the right side and over, and
    comes down into a straight stem that runs through the loop's bottom to
    the descender line. The loop is open between its start and the stem.
    Traced: 1.20 o wide, the stem at 0.60 o."""
    u = _u(c); xs = 278 * u
    ent = TH_V / (S * 1.0 * O_W_ADJ)
    loop = _round([(165 * u, 412), (100 * u, 365), (55 * u, 285), (45 * u, 200), (62 * u, 110), (112 * u, 38),
                   (200 * u, 3), (320 * u, 2), (425 * u, 30), (492 * u, 100), (518 * u, 200), (508 * u, 310),
                   (460 * u, 400), (385 * u, 437), (318 * u, 418), (287 * u, 360), (xs, 280)],
                  widths([(0.0, 1.0), (0.90, 1.0), (1.0, ent)]), fin0=True)
    st = _lc_stem(xs, -DESC, 300)
    return _heavy(geom.ink([loop, st]))

@glyph('ω')      # omega
def g_omega(c):
    """Two lobes on the full x-height, sitting on the baseline (round 371
    found the old one 0.68 of the x-height and 24.5 units up -- a
    subscript), each starting on the c's finial at the top and running down,
    round and up into a shared middle stroke that stops at 0.74 of the
    x-height. Traced: 1.36 o wide, the middle at 0.68 o."""
    u = _u(c); m = 315 * u
    ent = TH_V / (S * 1.0 * O_W_ADJ)
    pts = [(165 * u, 428), (108 * u, 392), (68 * u, 340), (48 * u, 280), (42 * u, 215), (50 * u, 150), (72 * u, 88),
           (108 * u, 38), (170 * u, 3), (238 * u, 25), (283 * u, 85), (306 * u, 160), (m, 235)]
    prof = widths([(0.0, 1.0), (0.90, 1.0), (1.0, ent)])
    left = _round(pts, prof, fin0=True)
    right = _round([(2 * m - x, y) for x, y in pts], prof, fin0=True)
    mid = _s(line((m, 150), (m, 318)), w=TH_V, cut0=None, cut1=CUT)
    return geom.ink([left, right, mid])

# ROUND 379 -- THE REST OF THE GREEK LOWERCASE, so a Greek word can be set.
# Owner 2026-09-24, "yes to all", to round 374's open item (a). Traced the
# same way as round 373 (`cmp_greek.py runs`, the median of Iowan, Georgia,
# Times and Palatino mapped into Albo's units against an o 465 wide, x from
# the letter's left ink edge) and drawn from Albo's own parts: the o's round
# pen for the curves, the pen for the straight and diagonal strokes, the c's
# finial on free round ends, the Latin stem with its wedge, the n's arch, the
# k's arm and leg, the t's tail. The traced targets are in
# docs/albo-greek-2026-09-23.md, round 379.
#
# THESE ARE APPENDED TO THE GLYPH ORDER (build.GREEK_APPEND), not sorted in
# among the Greek, so no glyph that already ships is re-cut by the decimation
# phase (cut.py's per-contour counter). The omicron and the Latin-identical
# capitals are not drawn at all: they are COMPOSITES of the Latin letter
# (build.GREEK_COPY), which is what the reference Greek fonts do.

def _top_hook(u, y=690):
    """The zeta's and xi's cap stroke: a curl rising at the top left into a
    stroke that runs right just under the ascender. On the pen, so the run is
    as heavy as a horizontal is in this face; the curl takes the c's finial.
    Traced: the curl's tip at (95, 752), the stroke at y 690 from 30 to 395."""
    # a hand may lighten it: the italic's 50-degree nib makes a HORIZONTAL its
    # thickest stroke, and the references' italic cap stroke is a light one
    prof = (lambda t: _HAND.hbar) if _HAND is not None else None
    return _pen([(98 * u, y + 62), (70 * u, y + 42), (74 * u, y + 16), (110 * u, y + 1), (180 * u, y - 2), (262 * u, y),
                 (340 * u, y + 4), (398 * u, y + 10)], prof, fin0=True, cut1=CUT)

def _hook_bottom(u, x0=0.0):
    """The zeta's, xi's and final sigma's bottom: round on the baseline, down
    the right side under it and hooked back to the LEFT into the c's finial.
    Traced: the bottom run at y 20, the right side at 0.76 o down to -90, the
    end at (245, -222)."""
    return [(x0 + 170 * u, 25), (x0 + 250 * u, 18), (x0 + 318 * u, 8), (x0 + 352 * u, -30), (x0 + 356 * u, -86),
            (x0 + 338 * u, -140), (x0 + 298 * u, -185), (x0 + 245 * u, -222)]

@glyph('ζ')      # zeta
def g_zeta(c):
    """The cap stroke under the ascender (`_top_hook`), and one round stroke
    hanging from its right part: down to the LEFT along a long diagonal, round
    the bottom on the baseline and hooked under it (`_hook_bottom`). Traced:
    0.87 of the o wide, from the ascender to 0.8 of the descender; the spine
    at x 330 at y 630, 205 at 500, 88 at 330, 45 at 200."""
    u = _u(c)
    spine = _round([(352 * u, 694), (316 * u, 636), (270 * u, 578), (220 * u, 520), (174 * u, 462), (132 * u, 405),
                    (98 * u, 348), (72 * u, 290), (54 * u, 230), (47 * u, 172), (54 * u, 120), (78 * u, 76),
                    (116 * u, 44)] + _hook_bottom(u), widths([(0.0, 0.70), (0.08, 1.0)]), fin1=True)
    return _close(geom.ink([_top_hook(u), spine]))

@glyph('η')      # eta
def g_eta(c):
    """Albo's own n (`arches.g_n`: the left stem with its top wedge, the arch,
    the right stem it lands on) with the right stem carried down to the
    descender line and neither stem footed -- three of the four references
    foot neither; the left stem ends square on the baseline and the right one
    on the descender line, the way the mu's does. Traced: the stems 0.64 o
    apart, the right one to -281."""
    from .arches import arch
    x0 = S / 2; x1 = x0 + pen.NW
    left = _lc_stem(x0, 0, XH, top='left')
    right = _lc_stem(x1, -DESC, 0.66 * XH)
    a, cuts = arch(x0, x1, XH)
    return geom.ink([left, right, a], cuts)

@glyph('ι')      # iota
def g_iota(c):
    """The undotted stem, with the i's top wedge, turning at its foot into the
    t's tail -- the references' iota is exactly that: no dot and no foot, the
    stem running round into a short rising tail. Traced: the tail's end 147 u
    right of the stem's centre, at y 85."""
    u = _u(c); x = S / 2
    st = _lc_stem(x, 180, XH, top='left')
    tl = _pen(None, widths([(0.0, 1.0), (0.80, 1.0), (1.0, 1.25)]), cut1=CUT, center=_tail(x, 240, 150, 86, u))
    return geom.ink([st, tl])

K_ARM_W = 1.30     # the kappa's arm, x the pen at its angle (the k's own ladder value, round 92's 1.30 at 0.78)

@glyph('κ')      # kappa
def g_kappa(c):
    """The k (`diagonals.g_k`) at the x-height: a stem with the top wedge and
    no foot, the arm leaving it at 0.40 of the x-height and rising to the
    x-height in the k's end wedge, the leg springing from the arm's lower edge
    at the k's 56 degrees and landing in the diagonal's foot wedge. Traced:
    1.10 of the o wide, the arm's top at 0.67 o right of the stem."""
    from ..primitives import diagonal, end_wedge
    from .diagonals import pw
    u = _u(c); x = S / 2
    st = _lc_stem(x, 0, XH, top='left')
    A0, B0 = (x + 318 * u, XH * 0.96), (x + S * 0.2, XH * 0.40)
    arm_w = pw(A0, B0, 0.78 * K_ARM_W)
    arm = geom.union([diagonal(A0, B0, arm_w), end_wedge([B0, A0], arm_w, False, 1, scale=1.15)])
    t = (130 * u - (B0[0] - x)) / (A0[0] - B0[0]); J = (B0[0] + (A0[0] - B0[0]) * t, B0[1] + (A0[1] - B0[1]) * t)
    ad = (A0[0] - B0[0], A0[1] - B0[1]); aL = math.hypot(*ad); ad = (ad[0] / aL, ad[1] / aL)
    an = (-ad[1], ad[0])
    if an[0] < 0: an = (-an[0], -an[1])
    J_edge = (J[0] + an[0] * arm_w / 2, J[1] + an[1] * arm_w / 2)
    foot = (J[0] + J[1] / math.tan(math.radians(56)), 0)
    d = (J[0] - foot[0], J[1] - foot[1]); L = math.hypot(*d); d = (d[0] / L, d[1] / L)
    lw = pw(foot, J) * 1.10
    tip = (J_edge[0] + d[0] * S * 0.20, J_edge[1] + d[1] * S * 0.20)
    leg = diagonal(foot, tip, widths([(0.0, lw), (0.55, lw), (1.0, lw * 0.35)]), serif0=1)
    return geom.ink([st, arm, leg])

@glyph('ν')      # nu
def g_nu(c):
    """The v's thick stroke (`diagonals.g_v`, its top wedge on the outside)
    run down steeply to the vertex, and a thin stroke that leaves the vertex
    and CURVES up to stand vertical at the x-height, ending in the c's finial
    -- the one thing that makes a nu and not a v. Traced: the vertex at 0.54 o,
    the thin stroke through (324, 120), (391, 240), (428, 360)."""
    from ..primitives import diagonal
    from .diagonals import pw
    u = _u(c)
    p0, p1 = (96 * u, XH), (252 * u, 0)
    left = diagonal(p0, p1, pw(p0, p1), serif0=1)
    right = _pen([(262 * u, 14), (300 * u, 70), (338 * u, 140), (378 * u, 222), (410 * u, 300), (426 * u, 360),
                  (430 * u, 412)], widths([(0.0, 0.80), (0.20, 1.0)]), fin1=True)
    return _close(geom.ink([left, right]))

@glyph('ξ')      # xi
def g_xi(c):
    """The zeta's cap stroke and bottom, with a small upper lobe between,
    built as the epsilon is: the upper lobe hangs from under the cap stroke,
    rounds to the left and ENDS at the waist on the left; the lower lobe --
    the zeta's bottom -- starts there; and a short tongue on the pen runs
    RIGHT from the waist to 0.71 of the o, which is the references' waist
    stroke. (Round 379's first cut ran the two lobes to a common tip on the
    right, the way a pen writes it, and the hairpin raised a 166-degree
    REVERSAL there.) Traced: the upper lobe's left side at 104 at y 470, the
    waist at y 345, the lower lobe's left side at 44 at y 165."""
    u = _u(c); w = (150 * u, 348)
    up = _round([(292 * u, 690), (220 * u, 650), (156 * u, 600), (118 * u, 545), (104 * u, 482), (112 * u, 425),
                 (126 * u, 382), w], widths([(0.0, 0.70), (0.10, 1.0), (0.86, 1.0), (1.0, 0.55)]))
    lo = _round([w, (104 * u, 318), (70 * u, 270), (50 * u, 210), (44 * u, 150), (56 * u, 98),
                 (92 * u, 56), (130 * u, 36)] + _hook_bottom(u), widths([(0.0, 0.55), (0.10, 1.0)]), fin1=True)
    tongue = _pen([(w[0] - 16 * u, w[1]), (330 * u, w[1] - 4)], widths([(0.0, 1.0), (1.0, 0.85)]), cut1=CUT)
    return _close(geom.ink([_top_hook(u), up, lo, tongue]))

@glyph('υ')      # upsilon
def g_upsilon(c):
    """The u's left stem with its top wedge (`arches.g_u`), running into ONE
    round stroke that turns on the baseline and climbs the right side, leaning
    back in at the top into the c's finial -- the u without its right stem.
    Traced: 1.06 o wide, the left stem at 133, the bottom at y 8, the right
    side's widest at 455 at y 240, the end at (400, 415)."""
    u = _u(c); x0 = S / 2
    X = lambda px: x0 + (px - 133) * u
    left = _lc_stem(x0, 0.40 * XH - 30, XH, top='left')
    bowl_ = _round([(x0, 0.44 * XH), (X(136), 130), (X(152), 66), (X(200), 22), (X(268), 8), (X(338), 26), (X(396), 76),
                    (X(434), 146), (X(454), 228), (X(452), 305), (X(432), 368), (X(400), 418)],
                   widths([(0.0, 1.0), (0.90, 1.0)]), fin1=True)
    return geom.ink([left, bowl_])

@glyph('χ')      # chi
def g_chi(c):
    """Two strokes crossing a little under the middle of the x-height and both
    running on to the descender: the down-RIGHT one heavy (it is on the pen's
    broad side, as the x's is), starting in the gamma's curl at the top left
    and ending in a turned-out finial; the down-LEFT one the pen's thin, from
    a finial at the top right to one at the bottom left. Traced: 1.05 o wide,
    the crossing at (262, 110), both ends at the descender line."""
    u = _u(c)
    thick = _pen([(14 * u, 404), (55 * u, 430), (100 * u, 408), (146 * u, 350), (196 * u, 276), (236 * u, 200),
                  (272 * u, 118), (306 * u, 34), (340 * u, -52), (376 * u, -136), (412 * u, -200), (458 * u, -236),
                  (500 * u, -232)], widths([(0.0, 1.0), (0.88, 1.0), (1.0, 0.85)]), fin0=True, fin1=True)
    thin = _pen([(446 * u, 426), (410 * u, 354), (330 * u, 230), (262 * u, 110), (190 * u, -20), (130 * u, -140),
                 (74 * u, -258)], fin0=True, fin1=True)
    return _close(geom.ink([thick, thin]))

@glyph('ψ')      # psi
def g_psi(c):
    """A straight stem from the ascender to the descender through a cup: the
    upsilon's left stem and turn on the left, its mirror on the right ending
    in the c's finial, the two meeting the stem just over the baseline. The
    stem rises to the ascender as Iowan's and Palatino's do (Georgia and
    Times stop it at the x-height; the humanist two are the closer kin).
    Traced: 1.35 o wide, the stem at 340, the arms at 130 and 565, the cup's
    bottom at y 20."""
    u = _u(c); x0 = S / 2
    X = lambda px: x0 + (px - 130) * u
    xs = X(340)
    stem_ = stem(xs, -DESC, ASC, w=TH_V, top=None, foot=None, cap=True, cut_top=CUT, ent_span=(-DESC, ASC))
    left = _lc_stem(x0, 0.40 * XH - 30, XH, top='left')
    ent = TH_V / (S * 1.0 * O_W_ADJ)
    cupl = _round([(x0, 0.44 * XH), (X(134), 128), (X(160), 64), (X(220), 28), (X(290), 16), (xs, 16)],
                  widths([(0.0, 1.0), (0.80, 1.0), (1.0, ent)]))
    cupr = _round([(X(566), 418), (X(572), 350), (X(570), 260), (X(552), 170), (X(516), 94), (X(460), 42),
                   (X(396), 18), (xs, 16)], widths([(0.0, 1.0), (0.80, 1.0), (1.0, ent)]), fin0=True)
    return _heavy(geom.ink([stem_, left, cupl, cupr]))

@glyph('ς')      # final sigma
def g_finalsigma(c):
    """The c's top (its finial dropping at the top right), round the left side
    on the o's pen, and on through the zeta's bottom (`_hook_bottom`): hooked
    under the baseline back to the left. Traced: 0.84 o wide, the top's finial
    at (352, 348), the left side at 38 at y 220."""
    u = _u(c)
    return geom.ink([_round([(354 * u, 350), (338 * u, 402), (286 * u, 434), (204 * u, 436), (120 * u, 410),
                             (64 * u, 348), (40 * u, 268), (38 * u, 190), (56 * u, 118), (96 * u, 64),
                             (130 * u, 38)] + _hook_bottom(u), fin0=True, fin1=True)])

def _cw(c):
    """ROUND 379 -- the ITALIC's Greek capitals are ~4% narrower, as its Latin
    ones are. Measured, unsheared by each face's slant off `l`, italic over
    roman ink width, Iowan / Georgia / Times / Palatino: Gamma through Omega
    median 0.965 (H 0.96, O 0.94, E 0.97 on the same faces). So they take the
    Latin capitals' own measured factor, `build.CAP_NARROW` (0.953), applied to
    POSITIONS -- the stems keep their weight, as the Latin ones do under the
    width solver. 1.0 in the roman, byte for byte, and 1.0 for the two MATH
    signs that borrow these drawings (the n-ary sum and product)."""
    import os
    ch = c.get("ch", "")
    if pen.SHEAR and "\u0391" <= ch <= "\u03a9":
        return float(os.environ.get("ALBO_IT_CAP_NARROW", 0.953))
    return 1.0

def _mitre(a, v, b, wa, wb):
    """Two straight strokes a->v->b joined in a MITRE at v -- the outer tip
    and the inner crotch are where the two strokes' edges cross, so the join
    is one vertex and one crotch, not two square faces meeting (the notch
    and spur of docs/albo-method.md section 1b)."""
    def unit(p, q):
        dx, dy = q[0] - p[0], q[1] - p[1]; L = math.hypot(dx, dy); return dx / L, dy / L
    d1 = unit(a, v); d2 = unit(v, b)
    n1 = (-d1[1], d1[0]); n2 = (-d2[1], d2[0])
    def cross(p, d, q, e):
        den = d[0] * e[1] - d[1] * e[0]
        t = ((q[0] - p[0]) * e[1] - (q[1] - p[1]) * e[0]) / den
        return (p[0] + d[0] * t, p[1] + d[1] * t)
    L1 = (a[0] + n1[0] * wa / 2, a[1] + n1[1] * wa / 2); R1 = (a[0] - n1[0] * wa / 2, a[1] - n1[1] * wa / 2)
    L2 = (b[0] + n2[0] * wb / 2, b[1] + n2[1] * wb / 2); R2 = (b[0] - n2[0] * wb / 2, b[1] - n2[1] * wb / 2)
    XL = cross(L1, d1, L2, d2); XR = cross(R1, d1, R2, d2)
    return sg.Polygon([L1, XL, L2, R2, XR, R1]).buffer(0)

def _flat_leg(p0, p1, lw):
    """A straight leg whose foot face is cut LEVEL on the baseline (the A's
    thin leg's cut), p0 on the baseline."""
    tn = geom.tangents(line(p0, p1))[0]
    return stroke(line(p0, p1), lw, cut0=-math.atan2(tn[0], tn[1])), tn

@glyph('Δ')      # Delta
def g_Delta(c):
    """The A without its bar, standing on a base bar: the thin left leg and
    the thick right leg meeting at the A's own apex, their feet cut level and
    run out to the base's ends. Traced: 0.90 of the O wide (it was 1.20)."""
    from .caps_straight import pw
    C = c["cap"]; w = 633 * _cw(c); s = CS
    p1 = (w / 2 - s * 0.06, C - s * 0.32); r1 = (w / 2 - s * 0.18, C)
    def foot_at(xb, top, mult, outer):
        # the leg's centre on the baseline that puts its OUTER corner at xb
        p0 = (xb, 0.0)
        for _ in range(4):
            lw = pw(p0, top, mult); tn = geom.tangents(line(p0, top))[0]
            p0 = (xb - outer * lw / 2 / tn[1], 0.0)
        return p0, lw
    p0, lw = foot_at(0.0, p1, 0.72, -1)
    r0, rw = foot_at(w, r1, 1.0, 1)
    left, _ = _flat_leg(p0, p1, lw)
    tn = geom.tangents(line(r0, r1))[0]
    right = stroke(line(r0, r1), rw, cut0=-math.atan2(tn[0], tn[1]), cut1=math.atan2(tn[0], tn[1]))   # both faces LEVEL: the foot on the baseline, the apex on the cap line
    base = bar(0, w, 0, CAP_BAR, align='bottom')
    return geom.ink([left, right, base])

@glyph('Π')      # Pi
def g_Pi(c):
    """The T's bar (`caps_straight.g_T`: both ends in the hanging wedge) over
    the full width, and two capital stems with both feet, set in under it.
    Traced: 1.05 of the O wide (it was 0.88), the stems at 0.18 and 0.82."""
    from .caps_straight import cstem
    C = c["cap"]; k = _cw(c); w = 733 * k; th = CAP_BAR
    b = bar(0, w, C, th, align='top', wedges=[('left', -1), ('right', -1)])
    return geom.ink([b, cstem(132 * k, 0, C - th * 0.5, top=None, foot='both', ent_span=(0, C)),
                     cstem(600 * k, 0, C - th * 0.5, top=None, foot='both', ent_span=(0, C))])

@glyph('Σ')      # Sigma
def g_Sigma(c):
    """The E's two outer bars (the top's right end hanging, the bottom's
    rising) and a mitred chevron between them: the thick stroke down to the
    right from the top bar's left end, the thin one back down to the left.
    Traced: 0.85 of the O wide (it was 0.67), the vertex at 0.54 of the width
    on the cap height's middle."""
    from .caps_straight import pw
    C = c["cap"]; k = _cw(c); w = 594 * k; th = CAP_BAR
    top = bar(18 * k, 560 * k, C, th, align='top', wedges=[('right', -1)])
    bot = bar(0, 585 * k, 0, th, align='bottom', wedges=[('right', 1)])
    a = (92 * k, C - th * 0.5); v = (318 * k, C * 0.50); b_ = (80 * k, th * 0.5)
    chev = _mitre(a, v, b_, pw(a, v), pw(v, b_))
    return geom.ink([top, bot, chev])

@glyph('Φ')      # Phi
def g_Phi(c):
    """A capital stem with wedges at both ends, through a wide oval on the O's
    ring that stands between 0.14 and 0.86 of the cap height. Traced: 1.01 of
    the O wide (it was 0.66)."""
    from .caps_straight import cstem
    C = c["cap"]; rx = 353 * _cw(c); ry = C * 0.36
    ring_, *_ = ring(rx, C / 2, rx, ry)
    return geom.ink([ring_, cstem(rx, 0, C, top='both', foot='both')])

@glyph('Ω')      # Omega
def g_Omega(c):
    """The O's round pen as ONE stroke: up from the left foot, over the top
    at the cap height's overshoot, down to the right foot -- an arc that
    turns inward as it comes down, landing on two feet that run out beyond
    it on both sides, the outer ends rising in the E's bottom wedge. Traced:
    1.04 of the O wide, 1.02 of the cap height (it was 0.92 -- a short O on
    two feet), the legs landing at 0.29 and 0.69 of the width."""
    C = c["cap"]; k = _cw(c); cx = 365 * k; cy = 385; rx = 265 * k; ry = C + OVER - cy - 16
    def at(deg):
        a = math.radians(deg); cs, sn = math.cos(a), math.sin(a)
        return (cx + rx * math.copysign(abs(cs) ** (2 / BOWL_K), cs), cy + ry * math.copysign(abs(sn) ** (2 / BOWL_K), sn))
    pts = [(222 * k, CAP_BAR * 0.45), (220 * k, 40), (210 * k, 95), (192 * k, 150)] + [at(d) for d in range(220, -41, -10)] + [(538 * k, 150), (520 * k, 95), (510 * k, 40), (508 * k, CAP_BAR * 0.45)]   # the legs end INSIDE the feet: ended on the foot's top edge they grazed it (REVERSAL 169.5)
    center = catmull(pts)
    body = stroke(center, bowl_widths(center))
    return geom.ink([body, bar(8 * k, 300 * k, 0, CAP_BAR, align='bottom', wedges=[('left', 1)]),
                     bar(430 * k, 722 * k, 0, CAP_BAR, align='bottom', wedges=[('right', 1)])])

# ROUND 379 -- THE GREEK CAPITALS ALBO LACKED. Fourteen of them are the Latin
# letter (A B E Z H I K M N O P T Y X): those are composites of Albo's own
# capital, built in outlines/build.py (GREEK_COPY), so a later round on the
# Latin letter reaches the Greek for free and the two can never disagree --
# what the reference Greek fonts do. The five genuinely Greek ones are drawn
# here from the Latin capitals' own parts.

@glyph('Γ')      # Gamma
def g_Gamma(c):
    """The F without its middle arm (`caps_straight.g_F`): the capital stem
    with its top-left wedge and both feet, and the F's top arm hanging its
    wedge at the right. Traced: 0.75 of the O wide (the F's own solved width
    is 0.60), the arm's wedge reaching down to 0.80 of the cap height."""
    from .caps_straight import cstem
    C = c["cap"]; x = CS / 2; w = 452 * _cw(c)
    return geom.ink([cstem(x, 0, C, top='left', foot='both'),
                     bar(x, x + w, C, CAP_BAR, align='top', wedges=[('right', -1)])])

def _ticked_bar(x0, x1, y, th, C):
    """A bar with a short upright TICK at each end, the Theta's and the Xi's
    middle bar in all four references: 0.20 of the cap height tip to tip
    (Iowan 0.20, Georgia 0.20, Times 0.20, Palatino 0.19) and a little over
    half the bar's weight (the references' 32-45 units against their 50-60
    bars). The ticks are cut level at both ends, as a stem is."""
    tw = th * 0.62; h = C * 0.10
    ticks = [stroke(line((x, y - h), (x, y + h)), tw) for x in (x0 + tw / 2, x1 - tw / 2)]
    return geom.ink([bar(x0, x1, y, th)] + ticks)

@glyph('Θ')      # Theta
def g_Theta(c):
    """Albo's O, crossed at the middle of the cap height by a bar whose ends
    carry the bar-end wedge both ways -- the vertical ticks all four
    references put there. Traced: the bar from 0.31 to 0.69 of the O's width,
    the ticks 0.20 of the cap height from tip to tip."""
    g = GLYPHS['O'](c); x0, _, x1, _ = g.bounds; C = c["cap"]; w = x1 - x0
    return geom.ink([g, _ticked_bar(x0 + w * 0.31, x0 + w * 0.69, C / 2, CAP_BAR * 0.80, C)])

@glyph('Λ')      # Lambda
def g_Lambda(c):
    """The A without its bar (`caps_straight.g_A`, round 232's): the thin left
    leg on its flat foot and bracket, the thick right leg with the outer
    wedge, the thin stroke ending inside the thick one under the apex. The
    width is the A's own solved width. Traced: 1.03 of the O wide."""
    from .caps_straight import pw, W_
    from ..primitives import diagonal
    # In the ITALIC the A is the Aldine module's redraw, whose solved width
    # multiplier means a different drawing: read through W it made the italic
    # Lambda 0.72 of the roman's, a slash (IoU 0.07 against the italic
    # references). There the width is the roman A's own solve -- W ~ 1.00 at
    # the 400s and the Bold, so 600 on the width axis -- narrowed as every
    # italic Greek capital is (`_cw`).
    C = c["cap"]; w = (600 * pen.WIDTH * _cw(c)) if pen.SHEAR else W_(c, 'A', 600); s = CS
    p0, p1 = (s * 0.3, 0), (w / 2 - s * 0.06, C - s * 0.32)
    tn = geom.tangents(line(p0, p1))[0]
    lw = pw(p0, p1, 0.72)
    left = stroke(line(p0, p1), lw, cut0=-math.atan2(tn[0], tn[1]))
    Apt = (p0[0] - lw / 2 / tn[1], 0.0)
    foot = wedge(Apt, (0, -1), (-1, 0), WL * 0.9, WD * 0.9, 0.0, edge_at=lambda d: (Apt[0] + tn[0] * d, tn[1] * d))
    r0, r1 = (w - s * 0.3, 0), (w / 2 - s * 0.18, C)
    right = diagonal(r0, r1, pw(r0, r1), serif0=1)
    return geom.ink([left, foot, right])

@glyph('Ξ')      # Xi
def g_Xi(c):
    """Three bars and no stem: the T's top bar (both ends hanging the bar-end
    wedge), the bottom bar with the wedge rising at both ends, and a shorter
    middle bar with the Theta's two-way ticks. Traced: 0.86 of the O wide,
    the middle bar from 0.23 to 0.76 of it."""
    C = c["cap"]; w = 605 * _cw(c); th = CAP_BAR
    return geom.ink([bar(0, w, C, th, align='top', wedges=[('left', -1), ('right', -1)]),
                     _ticked_bar(w * 0.23, w * 0.76, C * 0.5, th * 0.90, C),
                     bar(0, w, 0, th, align='bottom', wedges=[('left', 1), ('right', 1)])])

@glyph('Ψ')      # Psi
def g_Psi(c):
    """A capital stem, full height, wedged both ways at the top and footed on
    both sides, through a cup: each arm a capital stem from the cap line with
    the two-way top wedge, turning in on the O's round pen to meet the stem
    at 0.30 of the cap height. Traced: 1.14 of the O wide, the arms at 0.14
    and 0.86 of it, vertical down to 0.70 of the cap height."""
    from .caps_straight import cstem
    C = c["cap"]; k = _cw(c)
    xl = CS / 2 + 30 * k; xs = xl + 288 * k; xr = xs + 288 * k
    parts = [cstem(xs, 0, C, top='both', foot='both'),
             cstem(xl, C * 0.58, C, top='both', foot=None, ent_span=(0, C)),
             cstem(xr, C * 0.58, C, top='both', foot=None, ent_span=(0, C))]
    for sx in (-1, 1):
        xa = xs + sx * 288 * k
        pts = [(xa, C * 0.66), (xa - sx * 3 * k, C * 0.54), (xa - sx * 22 * k, C * 0.44), (xa - sx * 70 * k, C * 0.35),
               (xa - sx * 150 * k, C * 0.29), (xs, C * 0.27)]
        center = catmull(pts)
        parts.append(stroke(center, bowl_widths(center, widths([(0.0, 0.95), (0.35, 1.0), (1.0, 0.9)]))))
    return geom.ink(parts)

@glyph('∑')
def g_summation(c): return g_Sigma(c)
@glyph('∏')
def g_product(c): return g_Pi(c)

# ------------------------------------------------- the non-composite Latin
def _joined(c, a, b, overlap=0.18):
    """Two letters run together at their stems: the ligated vowels.

    ROUND 267 -- the overlap is a fraction of the SECOND letter's width, and
    at a 148 stem the E's serifs and bars widen its box faster than the O's
    flank reaches it, so the OE shipped as two islands (378394 and 200834
    units^2). If the pair does not touch at the declared overlap, the second
    letter slides left in 4-unit steps until it does -- the first placement
    that is one piece. A pair that already touches is placed exactly where it
    was, so nothing at the 400 moves."""
    ra = GLYPHS[a](c); rb = GLYPHS[b](c)
    ga = geom.ink([ra]); gb = geom.ink([rb])          # inked copies for COUNTING only
    def _n(g): return 1 if g.geom_type == 'Polygon' else len(g.geoms)
    # the pair must merge exactly ONE island: an ij is four pieces (two dots)
    # that become three, an ae one that stays one. The first cut of this loop
    # asked for a single piece and slid the ij 240 units into itself.
    want = _n(ga) + _n(gb) - 1
    ax0, _, ax1, _ = ga.bounds; bx0, _, bx1, _ = gb.bounds
    dx0 = ax1 - bx0 - (bx1 - bx0) * overlap; dx = dx0
    limit = (bx1 - bx0) * 0.25          # never slide more than a quarter of the second letter
    while dx0 - dx <= limit:
        if _n(geom.ink([ga, aff.translate(gb, dx, 0)])) <= want: break
        dx -= 4.0
    else:
        dx = dx0                          # could not join within the limit: keep the declared place
    # built from the RAW parts exactly as before, so a pair that needed no
    # slide is byte-identical to what shipped
    return geom.ink([ra, aff.translate(rb, dx, 0)])

# The a's round-155 rebuild pulled its right side in, and at the old 0.10
# the two letters no longer touched -- `cmp_aldine_glitch.py` read the ae
# as TWO ink islands (123043 and 103663 units^2). 0.18 is `_joined`'s own
# default and the first value that merges them; 0.14 still splits.
glyph('æ')(lambda c: _joined(c, 'a', 'e', 0.18))
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
    g2 = geom.ink([g, bar(x0 - d, x1 + d, yy, w or MATH)])
    # ROUND 268 -- at the bold italic's 116 stem the straight bar and the
    # italic h's head bracket enclose a sliver of paper, 49 units long and
    # 4 wide at its mouth, where the bar's top edge runs under the bracket
    # (CRACK: 209 units^2 in the drawn geometry, 90 after the build's 1.2-unit
    # ink spread narrows it). A 2-unit close did not seal it -- a close fills
    # only what is narrower than twice its radius, and the mouth is 4 -- so
    # it is the C's 4, which does. Gated above stem 84 AND to the italic: the
    # roman 700 and 900 barred letters had no finding and stay byte-identical
    # to round 267's builds.
    if S > 84.0 and pen.SHEAR:
        g2 = g2.buffer(4.0, join_style=2).buffer(-4.0, join_style=2)
    return g2
glyph('ð')(lambda c: _crossed_eth(c))
glyph('Ð')(lambda c: _barred(c, 'D', y=CAP * 0.50, x_pad=0.06))
glyph('đ')(lambda c: _barred(c, 'd', y=ASC * 0.86, x_pad=0.10))
glyph('Đ')(lambda c: _barred(c, 'D', y=CAP * 0.50, x_pad=0.06))
glyph('ħ')(lambda c: _barred(c, 'h', y=ASC * 0.86, x_pad=0.10))
glyph('Ħ')(lambda c: _barred(c, 'H', y=CAP * 0.82, x_pad=0.02))
# GLITCH SWEEP 2026-09-16: the bar was at XH*0.22, where it crosses the t's own
# exit flick as that flick curls up and away -- and the triangle of paper caught
# between the two is a COUNTER, 1,192 units^2 of it, in a letter that has none.
# Swept: XH*0.18 traps 465 units^2, 0.22 traps 1192, 0.26 2106, 0.30 3158, and
# the hole is gone at 0.14 and again at 0.34. 0.34 is the one that keeps the bar
# in the lower half of the x-height where a stroked t wants it (Ŧ's is CAP*0.40
# and Đ's CAP*0.50) instead of dropping it onto the foot.
glyph('ŧ')(lambda c: _barred(c, 't', y=XH * 0.34, x_pad=0.16))
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
    # ROUND 267 -- at a 148 stem the thorn showed two slits (CRACKs of 9.3 and
    # 9.4). First read as the bowl crossing the stem; see below.
    # CORRECTED the same round, as the rho: the slits are the counter itself
    # closing (wall 0.92 S = 136 against a radius of 137), not the join. The
    # wall scale falls with the stem above 84.
    ws = 0.92 * min(1.0, 84.0 / S)
    return geom.ink([stem(x, -c["desc"] * 0.86, c["asc"] * 0.92, top='left', foot='both'),
                     _bowl(x + XH * 0.30, XH * 0.50, XH * 0.32, XH * 0.50, ws)])
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
    # ROUND 267 -- at a 148 stem the shoulder and the lower stroke filled the
    # upper bowl to a slit (CRACK, mean width 9.6, area 823): the letter's
    # counter is small and its strokes are sized in S. Above 84 the three
    # curved strokes lighten by the square root of 84/S -- 0.75 at 148 -- so
    # the bowl keeps its room while the stem carries the weight. At and under
    # 84 the factor is 1 and the drawing is as it was.
    _lt = min(1.0, (84.0 / S) ** 0.5)
    pr = widths([(0.0, 0.80), (0.5, 0.95), (1.0, 0.82)])
    g = geom.ink([stem(x, 0, ASC * 0.74, top=None, foot='both'),
                  _s(sh, pr, cut0=None, cut1=None, light=_lt), _s(lower, pr, cut0=None, cut1=None, light=_lt),
                  _s(tail, widths([(0.0, 0.82), (0.6, 0.95), (1.0, 0.50)]), cut0=None, light=_lt)])
    if S > 84.0:
        # round 272: the ruling (no indentations in a counter at the 700 and
        # the 900) reaches the eszett's two counters, which are strokes and
        # not rings -- dents of 21-34 units at the heavy ends (adversarial
        # review); each counter is its own convex hull above 84
        from .. import primitives as _PR
        g = _PR.convex_holes(g)
    return g
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
    """The long s: the f's stem and hook, with the left-hand nub instead of a
    full crossbar.

    GLITCH SWEEP 2026-09-16 -- THE NUB WAS NOT TOUCHING THE LETTER. It ran
    S*0.10 .. S*1.05 (8.4 .. 88.2 units), and at its own height the stem's ink
    starts at 101.9: a 13.7-unit gap, so the glyph shipped as TWO ink islands
    and the nub rendered as a loose dash floating in the left sidebearing --
    3,321 units^2 of detached mark, which is what `cmp_aldine_glitch.py`'s
    SPLIT check now catches. The right end is measured off the stem at the bar
    height and taken to the middle of it, rather than nudged to another
    constant, so the nub cannot come adrift again when the f is redrawn."""
    from .stems import f_ink
    import shapely.geometry as _sg
    parts = f_ink(c, parts=True)
    y = XH - TH_H * 0.4
    band = geom.union([parts[0], parts[1]]).intersection(
        _sg.box(-9e3, y - TH_H * 0.4, 9e3, y + TH_H * 0.4))
    # the LEFTMOST run, not the band's overall bounds: a height that also
    # caught the hook would put the midpoint of the two in the air between them
    runs = [band] if band.geom_type == 'Polygon' else list(getattr(band, 'geoms', []))
    runs = [p for p in runs if p.geom_type == 'Polygon' and not p.is_empty]
    x_in = min((p.bounds for p in runs), key=lambda b: b[0]) if runs else None
    x_in = (x_in[0] + x_in[2]) / 2 if x_in else S * 1.05
    return geom.ink([parts[0], parts[1], bar(S * 0.10, x_in, y, TH_H * 0.8)])
@glyph('ĸ')      # kra
def g_kra(c):
    g = GLYPHS['k'](c); x0, y0, x1, y1 = g.bounds
    return aff.translate(g, 0, 0)

# the comma-below of Romanian s and t
@glyph('̦')
def g_commabelow(c):
    from .marks import comma_tail
    return geom.ink([dot(DOT_R * 0.92, -DOT_R * 1.2, DOT_R * 0.92), comma_tail(DOT_R * 0.92, -DOT_R * 1.2, k=1.0)])   # k=1.0: an accent, not punctuation -- see comma_tail

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
    # ROUND 384: the stem reaches up INTO the lobes. It stopped at CAP * 0.10
    # while the lobes bottom out at CAP * 0.17, so the foot floated free of the
    # spade -- visible in the outline spade as a separate trapezoid with a
    # crack inside it.
    stem_ = sg.Polygon([(-r * 0.16, CAP * 0.30), (r * 0.16, CAP * 0.30), (r * 0.16, CAP * 0.10),
                        (r * 0.50, 0), (-r * 0.50, 0), (-r * 0.16, CAP * 0.10)])
    return geom.ink([a, b, v, stem_])
def _club():
    r = CAP * 0.19
    parts = [sg.Point(0, CAP * 0.72).buffer(r), sg.Point(-r * 1.10, CAP * 0.40).buffer(r), sg.Point(r * 1.10, CAP * 0.40).buffer(r),
             sg.Polygon([(-r * 0.16, CAP * 0.10), (r * 0.16, CAP * 0.10), (r * 0.55, 0), (-r * 0.55, 0)]),
             sg.box(-r * 0.16, CAP * 0.10, r * 0.16, CAP * 0.50),
             # ROUND 384: THE HEART OF THE CLUB. The three lobes only kiss, so
             # they left white slivers between them (glitch CRACK on the solid
             # club) and the stem's top poked up into the notch; the outline
             # club came out as three loose rings around a square. One disc at
             # the junction makes the three lobes and the stem one shape.
             sg.Point(0, CAP * 0.46).buffer(r * 0.62)]
    # ...and the V-notches where two lobes meet are blunted to 12 units: in
    # the italic they close at 12 degrees, a needle of white driven into the
    # outline club (REVERSAL, pass 3). A mitre closing fills only what is
    # narrower than 2 x 6 units; the lobes' own curves are untouched.
    return geom.ink(parts).buffer(6.0, join_style=2).buffer(-6.0, join_style=2)
def _diamond():
    r = CAP * 0.30
    return sg.Polygon([(0, CAP * 0.02), (r * 0.82, CAP * 0.47), (0, CAP * 0.92), (-r * 0.82, CAP * 0.47)])
for _cp, _fn in (('♠', _spade), ('♥', _heart), ('♦', _diamond), ('♣', _club)):
    glyph(_cp)((lambda f: (lambda c: aff.translate(f(), CAP * 0.34, 0)))(_fn))
for _cp, _fn in (('♤', _spade), ('♡', _heart), ('♢', _diamond), ('♧', _club)):
    # ROUND 384: the outline's inset leaves a sliver of white inside the
    # spade's and the club's narrow foot (glitch CRACK); filled, so the foot
    # is solid as it is on every printed card.
    glyph(_cp)((lambda f: (lambda c: _fill_cracks(_hollow(aff.translate(f(), CAP * 0.34, 0)))))(_fn))

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
