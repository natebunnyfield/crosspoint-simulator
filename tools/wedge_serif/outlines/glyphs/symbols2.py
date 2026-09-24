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

def _u(c):
    """This build's o width over the Regular's 465 -- the traced skeletons'
    unit. Uses the ROMAN o's construction (`rounds.g_o`) in both styles: the
    italic's Greek is the roman Greek sheared, as it always was."""
    return 2 * (O_RX * O_RX_ADJ * c['wf'] + TH_V / 2 * O_W_ADJ) / 465.0

def _oring(cx, cy, rx, ry):
    """A closed bowl on the o's own weight (`rounds.g_o`: O_W_ADJ on the
    round pen, the hair floored at O_FLOOR_ADJ of the stem)."""
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
    center = _path(pts); wf = _rw(center, prof)
    if fin0: wf = finial_widths(wf, True); cut0 = finial_cut(center, True)
    if fin1: wf = finial_widths(wf, False); cut1 = finial_cut(center, False)
    return stroke(center, wf, cut0=cut0, cut1=cut1)

def _pen(pts, prof=None, cut0=None, cut1=None, fin0=False, fin1=False, center=None):
    """A straight or diagonal stroke through traced points, on the pen (the
    26-degree nib the Latin stems, arches and diagonals are drawn with)."""
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
    C = c["cap"]; w = 633; s = CS
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
    C = c["cap"]; w = 733; th = CAP_BAR
    b = bar(0, w, C, th, align='top', wedges=[('left', -1), ('right', -1)])
    return geom.ink([b, cstem(132, 0, C - th * 0.5, top=None, foot='both', ent_span=(0, C)),
                     cstem(600, 0, C - th * 0.5, top=None, foot='both', ent_span=(0, C))])

@glyph('Σ')      # Sigma
def g_Sigma(c):
    """The E's two outer bars (the top's right end hanging, the bottom's
    rising) and a mitred chevron between them: the thick stroke down to the
    right from the top bar's left end, the thin one back down to the left.
    Traced: 0.85 of the O wide (it was 0.67), the vertex at 0.54 of the width
    on the cap height's middle."""
    from .caps_straight import pw
    C = c["cap"]; w = 594; th = CAP_BAR
    top = bar(18, 560, C, th, align='top', wedges=[('right', -1)])
    bot = bar(0, 585, 0, th, align='bottom', wedges=[('right', 1)])
    a = (92, C - th * 0.5); v = (318, C * 0.50); b_ = (80, th * 0.5)
    chev = _mitre(a, v, b_, pw(a, v), pw(v, b_))
    return geom.ink([top, bot, chev])

@glyph('Φ')      # Phi
def g_Phi(c):
    """A capital stem with wedges at both ends, through a wide oval on the O's
    ring that stands between 0.14 and 0.86 of the cap height. Traced: 1.01 of
    the O wide (it was 0.66)."""
    from .caps_straight import cstem
    C = c["cap"]; rx = 353; ry = C * 0.36
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
    C = c["cap"]; cx = 365; cy = 385; rx = 265; ry = C + OVER - cy - 16
    def at(deg):
        a = math.radians(deg); cs, sn = math.cos(a), math.sin(a)
        return (cx + rx * math.copysign(abs(cs) ** (2 / BOWL_K), cs), cy + ry * math.copysign(abs(sn) ** (2 / BOWL_K), sn))
    pts = [(222, CAP_BAR * 0.45), (220, 40), (210, 95), (192, 150)] + [at(d) for d in range(220, -41, -10)] + [(538, 150), (520, 95), (510, 40), (508, CAP_BAR * 0.45)]   # the legs end INSIDE the feet: ended on the foot's top edge they grazed it (REVERSAL 169.5)
    center = catmull(pts)
    body = stroke(center, bowl_widths(center))
    return geom.ink([body, bar(8, 300, 0, CAP_BAR, align='bottom', wedges=[('left', 1)]),
                     bar(430, 722, 0, CAP_BAR, align='bottom', wedges=[('right', 1)])])

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
