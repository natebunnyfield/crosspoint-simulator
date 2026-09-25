"""THE ITALIC'S GREEK, as a cursive (round 379).

Owner 2026-09-24, "yes to all", to round 374's open item (c): the italic's
Greek was the roman Greek sheared by 13 degrees -- an oblique -- while every
italic reference redraws its Greek. This module draws it in the ALDINE
ITALIC'S OWN CONSTRUCTION (`aldine.py`), and is live only where that module is
(`ALBO_ITALIC=aldine`, the shipping italic). The roman, and a build with the
classic italic, never import a line of it into a glyph.

WHAT THE REFERENCES DO (Iowan, Georgia, Times and Palatino italics, measured
unsheared by each face's own slant off its `l`; the scripts are in
`instruments/greek376_*.py`, the tables in docs/albo-greek-2026-09-23.md,
round 379):

  * A Greek letter keeps its proportion to its LATIN ANALOGUE across the
    roman/italic change -- eta/n 0.87 italic against 0.90 roman, mu/u 0.91 /
    0.95, kappa/k 1.03 / 1.01, sigma/o 1.08 / 1.12, omicron/o 1.00 / 1.00. It
    does NOT keep its width against the o in general: Iowan's italic o is 0.78
    of its roman o while its italic alpha is 0.96 of its roman alpha, because
    Iowan's italic a is not narrower either.
  * So the italic Greek is drawn from the italic Latin's parts wherever a
    Greek letter IS a Latin shape with something added -- the eta is the
    Aldine n with its right stem run down, the mu the Aldine u with its left
    stem run down, the nu the Aldine v's movement, the iota the Aldine i's
    stem and exit without the head or the dot -- and from the traced roman
    skeleton, re-drawn in the italic's hand and scaled by the ratio of the
    italic's Latin analogue to the roman's, wherever the letter has no Latin
    shape (beta, zeta, theta, xi, phi, omega ...).

THE HAND (`symbols2.hand`). The roman Greek functions call five helpers --
the skeleton unit, the o's ring, a round stroke, a pen stroke and a lowercase
stem. Drawn inside `with S2.hand(ItalicHand(...))`, those same functions run
through the italic's versions instead:

  unit     the roman skeleton unit x (italic Latin analogue / roman), live
  ring     the Aldine o's own ring: a superellipse at O_K on the 35-degree
           nib, thick/thin re-spread to CON_O (`aldine.a_o`)
  round    the same nib along an open path; free ends take the italic's
           finial at `aldine.fin_floor()` (round 276's rule for every end)
  pen      the chancery nib at 50 degrees (`aldine.nib`), its thick sized so
           a vertical downstroke is the Aldine stem (HM_STEMW)
  stem     `aldine.hm_stem` (swayed, waisted), with `hm_head` where the roman
           stem had its top wedge

Everything is drawn UNSHEARED; build.draw shears it like every italic glyph.
"""
import math
from . import glyph, GLYPHS
from . import aldine as ALD
from . import symbols2 as S2
from .. import geom, pen
from .. import primitives as PR
from ..geom import catmull, line, superellipse, resample, tangents
from ..primitives import stroke, widths
from ..pen import S, XH, ASC, DESC, OVER, CUT

ON = ALD.ON


def _width(g):
    x0, _, x1, _ = g.bounds
    return x1 - x0


_K = {}

def analogue_ratio(c, latin):
    """How much narrower this build's ITALIC draws a Latin letter than its
    ROMAN does, measured live on the two drawings: the italic's glyph against
    the roman module's own function (which the italic build still defines,
    only no longer registers). o 0.70, x 0.88, y 0.77, k 0.74 at the shipping
    Italic (measured on the built fonts, round 379)."""
    key = (latin, round(c["wf"], 5), S)
    if key not in _K:
        from . import rounds, diagonals
        roman = {'o': rounds.g_o, 'x': diagonals.g_x, 'y': diagonals.g_y, 'k': diagonals.g_k}[latin]
        _K[key] = _width(GLYPHS[latin](dict(c, ch=latin))) / _width(roman(dict(c, ch=latin)))
    return _K[key]


def _pair():
    """The Aldine o's (thick, thin), in units (`aldine.a_o`)."""
    thick, thin = (ALD.con([ALD.O_THIN, ALD.O_THICK], ALD.CON_O)[::-1] if ALD.CON_O else (ALD.O_THICK, ALD.O_THIN))
    So = math.sqrt(84.0 * S) if (S > 84.0 and ALD.O_S_UP) else S
    return So * thick, So * thin


PEN_PHI = 50.0     # the chancery nib's angle (`aldine.nib`'s measured 50 degrees)
PEN_THIN = 0.32    # its thin, x its thick (the Aldine v's thin 24-32 over its thick 66-74)


class ItalicHand:
    """The italic's versions of symbols2's five helpers (see the header)."""
    hbar = 0.62   # the zeta's and xi's cap stroke, x the nib: see symbols2._top_hook

    def __init__(self, c, latin='o'):
        self.c = c; self.latin = latin

    def u(self, c):
        return S2._u_roman(c) * analogue_ratio(c, self.latin)

    def oring(self, cx, cy, rx, ry):
        outer = superellipse(cx, cy, rx, ry, 0.0, 2 * math.pi, ALD.O_K)[:-1]
        T, H = _pair(); phi = math.radians(ALD.O_PEN)
        return PR.ring_from(outer, widths_fn=lambda t: H + (T - H) * abs(math.cos(t * 2 * math.pi - phi)), smooth_w=3)

    def _stroke(self, center, T, H, phi, prof, cut0, cut1, fin0, fin1):
        center = resample(center); n = len(center) - 1; tans = tangents(center)
        ws = [H + (T - H) * abs(math.sin(math.atan2(ty, tx) - phi)) for tx, ty in tans]
        k = 4
        ws = [sum(ws[max(0, i - k):i + k + 1]) / len(ws[max(0, i - k):i + k + 1]) for i in range(len(ws))]
        base = (lambda t: ws[min(n, int(round(t * n)))] * (prof(t) if prof else 1.0))
        wf = base
        if fin0: wf = PR.finial_widths(wf, True, floor=ALD.fin_floor()); cut0 = PR.finial_cut(center, True)
        if fin1: wf = PR.finial_widths(wf, False, floor=ALD.fin_floor()); cut1 = PR.finial_cut(center, False)
        return stroke(center, wf, cut0=cut0, cut1=cut1, raw=True)

    def round(self, pts, prof=None, cut0=None, cut1=None, fin0=False, fin1=False):
        T, H = _pair()
        return self._stroke(S2._path(pts), T, H, math.radians(ALD.O_PEN), prof, cut0, cut1, fin0, fin1)

    def pen(self, pts, prof=None, cut0=None, cut1=None, fin0=False, fin1=False, center=None):
        T = pen_thick(self.c)
        return self._stroke(center or S2._path(pts), T, T * PEN_THIN, math.radians(PEN_PHI), prof, cut0, cut1, fin0, fin1)

    def ent(self):
        """ROUND 385: the stem's width over this hand's round pen at the
        vertical (`S2._ent`)."""
        T, H = _pair(); phi = math.radians(ALD.O_PEN)
        return (ALD.HM_STEMW * ALD.hm_u(self.c)) / (H + (T - H) * abs(math.cos(phi)))

    def lc_stem(self, x, y0, y1, top=None):
        c = self.c
        if top:
            return geom.ink([ALD.hm_stem(c, x, y0, y1), ALD.hm_head(c, x, y1)])
        return ALD.hm_stem(c, x, y0, y1, cut=False)


def pen_thick(c):
    """The chancery nib's full width: a vertical downstroke on it (|sin(-90 -
    50)| = 0.64 of the way from thin to thick) comes out the Aldine stem."""
    sw = ALD.HM_STEMW * ALD.hm_u(c)
    return sw / (PEN_THIN + (1 - PEN_THIN) * abs(math.sin(math.radians(-90.0 - PEN_PHI))))


def _close3(g):
    """A 3-unit mitre close at EVERY weight: the italic's thinner round pen
    leaves the epsilon's and xi's waists (two arcs ending on one tongue) as a
    grazing crotch that `cmp_contour_hairs` reads as a HAIR at the 400 too,
    where the roman needs `_close` only above stem 84. Moves nothing wider
    than 6 units."""
    return g.buffer(3.0, join_style=2).buffer(-3.0, join_style=2)


POST = {'ε': _close3, 'ξ': _close3, 'δ': S2._heavy, 'θ': S2._heavy}


def _in_hand(fn, latin, post=None):
    def draw(c):
        with S2.hand(ItalicHand(c, latin)):
            g = fn(c)
        return post(g) if post else g
    return draw


if ON:
    # ------------------------------------------------ the traced skeletons, re-drawn in the italic hand
    # letter -> the Latin analogue whose italic/roman ratio scales its skeleton
    VIA_ROMAN = {'β': 'o', 'γ': 'y', 'δ': 'o', 'ε': 'o', 'ζ': 'o', 'θ': 'o', 'λ': 'k', 'ξ': 'o',
                 'ς': 'o', 'φ': 'o', 'χ': 'x', 'ω': 'o'}
    for _ch, _lat in VIA_ROMAN.items():
        glyph(_ch)(_in_hand(GLYPHS[_ch].__wrapped__ if hasattr(GLYPHS[_ch], '__wrapped__') else GLYPHS[_ch], _lat,
                            POST.get(_ch)))

    def _it(c, latin='o'):
        return ItalicHand(c, latin)

    # ------------------------------------------------ the letters that ARE a Latin shape
    @glyph('α')
    def it_alpha(c):
        """The italic o's ring with a stroke standing on its right side that
        rises a little over the x-height and leaves the baseline in the
        Aldine a's own exit (`hm_exit(.., 'a')`) -- the a's stem and exit
        with the head left off, which is what the italic references' alpha
        is. Traced on the roman skeleton (the stroke at 0.80 of the o) and
        scaled to the italic o."""
        H = _it(c); u = H.u(c); sw = ALD.HM_STEMW * ALD.hm_u(c)
        xs = 370 * u
        rx = (xs + sw / 2 - 4) / 2
        ring_, *_ = H.oring(rx, XH / 2, rx, XH / 2 + OVER)
        st = stroke(line((xs + 10 * u, XH + 12), (xs, XH * 0.30)), sw, cut0=CUT)
        return S2._heavy(geom.ink([ring_, st, ALD.hm_exit(c, xs, 'a')]))

    @glyph('ρ')
    def it_rho(c):
        """The italic o's ring, 0.96 of the o, and the Aldine stem from the
        middle of the bowl to the descender line, its left edge 3 units
        OUTSIDE the ring's (the roman sets it 2 inside: on the italic's
        thinner ring that left a 2-unit sliver where the two outer edges
        cross, a 165-degree REVERSAL). Traced on the roman skeleton."""
        H = _it(c); u = H.u(c); sw = ALD.HM_STEMW * ALD.hm_u(c); rx = 223 * u
        bowl_, *_ = H.oring(rx, XH / 2, rx, XH / 2 + OVER)
        g = geom.ink([bowl_, ALD.hm_stem(c, sw / 2 - 3, -DESC, XH * 0.5, cut=False)])
        # ROUND 385: the 3 units outside leave a STEP where the stem's flat top
        # stops on the ring's side (3.7 units at the 400, 4.7 at the 700,
        # `cmp_jogs.py`). The outer side of the join is made its own hull over a
        # short band, so the stem's edge eases onto the ring's in a slope; the
        # band stops at the stem's middle, so the counter is not touched.
        import shapely.geometry as _sg
        band = g.intersection(_sg.box(-9e3, XH * 0.5 - sw * 0.9, sw * 0.45, XH * 0.5 + sw * 1.2))
        return S2._heavy(g.union(band.convex_hull))

    @glyph('η')
    def it_eta(c):
        """The Aldine n (`aldine.a_n`: stem, head, the arch that branches
        low) with its right stem carried down to the descender and no exit --
        exactly the n of every italic reference, with the descender."""
        xh = c["xh"]; x0 = S * 1.0; x1 = x0 + ALD.HM_PITCH * xh
        return geom.ink([ALD.hm_stem(c, x0, 0, xh), ALD.hm_head(c, x0, xh), ALD.hm_arch(c, x0, x1),
                         ALD.hm_stem(c, x1, -DESC, ALD.hm_arch_end(c), cut=False)])

    @glyph('ι')
    def it_iota(c):
        """The Aldine i's stem and exit (`aldine.a_i`) with neither head nor
        dot: the italic references' iota has a plain top, which is what keeps
        it from reading as a dotless i. The top is cut on the family's pen
        angle and the stem swells into it as the i's does not."""
        xh = c["xh"]; x = S * 1.0; sw = ALD.HM_STEMW * ALD.hm_u(c)
        st = stroke(line((x, xh * 0.22), (x + 3, xh + 8)), widths([(0.0, sw), (0.85, sw), (1.0, sw * 0.92)]), cut1=CUT)
        return geom.ink([st, ALD.hm_exit(c, x, 'i')])

    @glyph('κ')
    def it_kappa(c):
        """The Aldine stem with its head, an arm that leaves it at 0.40 of the
        x-height and rises in a curve to the x-height in the italic's finial,
        and a leg from the arm down to the baseline and out in the exit's
        upturn. Traced on the italic references (the arm's top at 0.63 of the
        width, the leg's foot at 0.78); 1.03 of the Aldine k's width, as the
        references' kappa is of their k."""
        xh = c["xh"]; x = S * 1.0; H = _it(c, 'k')
        st = geom.ink([ALD.hm_stem(c, x, 0, xh), ALD.hm_head(c, x, xh)])
        arm = H.pen([(x + 10, xh * 0.36), (x + 70, xh * 0.47), (x + 140, xh * 0.66), (x + 196, xh * 0.84),
                     (x + 236, xh * 0.96)], widths([(0.0, 0.70), (0.25, 1.0)]), fin1=True)
        leg = H.pen([(x + 62, xh * 0.52), (x + 104, xh * 0.34), (x + 146, xh * 0.16), (x + 182, xh * 0.03),
                     (x + 222, xh * 0.01), (x + 256, xh * 0.10), (x + 272, xh * 0.24)],
                    widths([(0.0, 0.80), (0.20, 1.0), (0.70, 0.85), (1.0, 0.40)]), cut1=CUT)
        return geom.ink([st, arm, leg])

    @glyph('μ')
    def it_mu(c):
        """The Aldine u (`aldine.a_u`: the one movement down, round and up,
        the right stem and its exit) with its left stem carried down to the
        descender line -- the mu of every italic reference."""
        xh = c["xh"]; x0 = S * 1.0
        return geom.ink([ALD.a_u(c), ALD.hm_stem(c, x0, -DESC, xh * 0.50, cut=False)])

    @glyph('ν')
    def it_nu(c):
        """The Aldine v's movement (`aldine.a_v`: the entry sweeping up into
        the thick downstroke, the vertex on the baseline) with the thin stroke
        rising further and more upright, to the full x-height, into the
        italic's finial -- where the v's turns back at 0.89. Drawn on the v's
        own frame, points and width table."""
        P, u = ALD.d_frame(c, ALD.V_W); X = ALD.V_VX
        thick = ALD.d_pen([P(5, ALD.entry_y('v')), P(32, 0.90), P(76, 0.95), P(106, 0.75),
                           P(132, 0.50), P(152, 0.25), P(X - 4, 0.07), P(X, -0.018)],
                          [(0.00, 22), (0.10, 48), (0.24, 68), (0.70, 66), (0.90, 52), (1.00, 30)], u, tw=ALD.V_TW)
        thin = ALD.d_pen([P(X, -0.018), P(210, 0.12), P(242, 0.30), P(270, 0.52), P(290, 0.72),
                          P(300, 0.88), P(298, 0.99)],
                         [(0.00, 30), (0.15, 26), (0.55, 30), (0.80, 40), (1.00, 46)], u, tw=ALD.V_TW, fin1=True)
        g_ = geom.ink([thick, thin])
        return ALD._solid(g_) if ALD.ALD_WF_UP > 1.0 else g_

    def _droop_bar(c, x0, x1, H):
        """The pi's and tau's bar in the italic: a stroke on the nib whose
        LEFT end hooks down (all four italic references turn it down there
        where the roman hangs a wedge), running out level to the right."""
        xh = c["xh"]
        return H.pen([(x0, xh - 62), (x0 + 10, xh - 26), (x0 + 42, xh - 6), (x0 + 110, xh - 4),
                      (x1, xh + 2)], widths([(0.0, 0.55), (0.18, 0.70), (0.70, 0.62), (1.0, 0.52)]), cut0=CUT, cut1=CUT)

    @glyph('π')
    def it_pi(c):
        """The drooping bar, a left leg that curves down and to the left into
        the italic's finial, and a right leg that is the Aldine stem with the
        n's exit. 0.98 of the Aldine n's width, as the references' pi is of
        their n."""
        xh = c["xh"]; H = _it(c); sw = ALD.HM_STEMW * ALD.hm_u(c)
        x2 = 300.0
        b = _droop_bar(c, 0.0, x2 + 70, H)
        left = H.pen([(118, xh - 20), (116, xh * 0.66), (106, xh * 0.38), (84, xh * 0.14), (52, 8)], fin1=True)
        right = geom.ink([ALD.hm_stem(c, x2, 0, xh - 10, cut=False), ALD.hm_exit(c, x2, 'n')])
        return geom.ink([b, left, right])

    @glyph('τ')
    def it_tau(c):
        """The drooping bar and one Aldine stem a little left of its middle,
        leaving the baseline in the t's exit (the longest the italic has,
        `HM_EXIT_BY['t']`). 1.30 of the Aldine t's width, as the references'
        tau is of their t."""
        xh = c["xh"]; H = _it(c)
        xs = 132.0
        return geom.ink([_droop_bar(c, 0.0, 262.0, H),
                         ALD.hm_stem(c, xs, 0, xh - 10, cut=False), ALD.hm_exit(c, xs, 't')])

    @glyph('σ')
    def it_sigma(c):
        """The italic o's ring on a flat top, and a bar from the crown out to
        the right on the nib, thinning as it goes -- the italic references'
        sigma bar is a hairline, where the roman's is the ring's top wall.
        Traced (roman skeleton): the bowl = o, the bar to 1.11 o."""
        H = _it(c); u = H.u(c); rx = 232 * u; top = XH + 8
        bowl_, *_ = H.oring(rx, (top - OVER) / 2, rx, (top + OVER) / 2)
        T, Hn = _pair()
        th = Hn * 1.6
        b = stroke(line((rx - 20 * u, top - th / 2), (518 * u, top - th / 2)),
                   widths([(0.0, th), (0.35, th * 1.15), (1.0, th * 0.85)]), cut1=CUT)
        return S2._heavy(geom.ink([bowl_, b]))

    def _u_path(c, x0, P, top_frac):
        """The Aldine u's movement -- down the swayed stem from the head --
        but round at the bottom and carried up the right side to `top_frac`
        of the x-height, where it turns in. P is the letter's inner width."""
        xh = c["xh"]; u = ALD.hm_u(c)
        return catmull(ALD.ent_sway([(x0, xh * 0.95), (x0, xh * 0.58), (x0, xh * 0.32)], ALD.ENT_SWAY * u) +
                       [(x0 + P * 0.10, xh * 0.10), (x0 + P * 0.36, -OVER * 0.3), (x0 + P * 0.66, xh * 0.03),
                        (x0 + P * 0.90, xh * 0.22), (x0 + P * 1.00, xh * 0.50), (x0 + P * 0.99, xh * top_frac * 0.80),
                        (x0 + P * 0.92, xh * top_frac)], tension=0.5)

    def _headed(c, x0, g):
        """The u's head on a stroke that starts at the stem's top, with the
        stroke clipped under the head's face exactly as `aldine.a_u` does."""
        xh = c["xh"]; sw = ALD.HM_STEMW * ALD.hm_u(c)
        _ytr, _ang = ALD.hm_follow_cut(c, x0, xh, sw)
        _xr = x0 + sw / 2; _xl = x0 - sw - 10.0; _xrr = _xr + 10.0
        _line = lambda x: _ytr + (x - _xr) * math.tan(_ang)
        above = geom.poly([(_xl, _line(_xl)), (_xrr, _line(_xrr)), (_xrr, xh * 2), (_xl, xh * 2)])
        return geom.ink([g.difference(above), ALD.hm_head(c, x0, xh, wtop=sw)])

    def _u_prof(c):
        """The u's widths on the down-round-up, with the rise held heavier
        than the u's hairline: in the upsilon and psi the rise is a whole
        side of the letter, not a connector into a second stem."""
        u = ALD.hm_u(c); sw = ALD.HM_STEMW * u
        return widths([(0.00, sw), (0.34, sw), (0.46, sw * 0.90), (0.58, sw * 0.62), (0.70, sw * 0.62),
                       (0.84, sw * 0.80), (1.00, sw * 0.70)])

    UPS_W = 1.30   # the upsilon's inner width, x the Aldine pitch: 0.85 of the u's advance, as the references' upsilon is of their u
    PSI_W = 1.10   # each half of the psi's cup, x the pitch

    @glyph('υ')
    def it_upsilon(c):
        """The Aldine u's one movement -- the head, down, round, up -- without
        the u's right stem: the rise goes on to the x-height and turns in, into
        the italic's finial. 0.85 of the Aldine u's width, as the references'
        upsilon is of their u."""
        xh = c["xh"]; x0 = S * 1.0; P = ALD.HM_PITCH * xh * UPS_W
        path = _u_path(c, x0, P, 0.99)
        wf = PR.finial_widths(_u_prof(c), False, floor=ALD.fin_floor())
        g = stroke(path, wf, cut0=-math.radians(ALD.HM_TOPCUT), cut1=PR.finial_cut(path, False))
        return _headed(c, x0, g)

    @glyph('ψ')
    def it_psi(c):
        """The upsilon's cup made symmetric -- the left arm with its head, the
        right arm starting in the italic's finial -- the two meeting just over
        the baseline on a straight stem that runs from the ascender to the
        descender (Iowan's and Palatino's italic run it to the ascender, as the
        roman psi here does)."""
        xh = c["xh"]; u = ALD.hm_u(c); sw = ALD.HM_STEMW * u; x0 = S * 1.0
        P = ALD.HM_PITCH * xh * PSI_W; xs = x0 + P * 0.92
        left = catmull(ALD.ent_sway([(x0, xh * 0.95), (x0, xh * 0.58), (x0, xh * 0.26)], ALD.ENT_SWAY * u) +
                       [(x0 + P * 0.10, sw * 0.5 + 26 * u), (x0 + P * 0.42, sw * 0.5 - 4 * u), (xs, sw * 0.5 + 2 * u)],
                       tension=0.5)
        gl = stroke(left, widths([(0.0, sw), (0.45, sw), (0.75, sw * 0.80), (1.0, sw * 0.70)]),
                    cut0=-math.radians(ALD.HM_TOPCUT))
        xr = xs + P * 0.95
        right = catmull([(xr, xh * 0.97), (xr + 6 * u, xh * 0.74), (xr - 2 * u, xh * 0.44), (xr - P * 0.22, xh * 0.14),
                         (xs + P * 0.30, sw * 0.5 + 2 * u), (xs, sw * 0.5 + 2 * u)], tension=0.5)
        gr = stroke(right, PR.finial_widths(widths([(0.0, sw * 0.80), (0.40, sw * 0.86), (1.0, sw * 0.70)]), True,
                                            floor=ALD.fin_floor()), cut0=PR.finial_cut(right, True))
        st = stroke(line((xs, -DESC), (xs, ASC)), widths([(0.0, sw * 0.92), (0.5, sw), (1.0, sw * 0.92)]), cut0=CUT, cut1=CUT)
        return geom.ink([_headed(c, x0, gl), gr, st])
