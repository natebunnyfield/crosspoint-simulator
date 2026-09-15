"""THE ITALIC SKELETONS (round 105, 2026-09-14).

Owner: *"research what italic is because you're just doing an oblique"*, then
*"do a redraw at 13 degree tilt but with actual italic characters."*

`docs/italic-vs-oblique.md` is why this file exists. The short version: an
oblique is the roman slanted, a true italic is a different set of skeletons,
and the test is to shear a family's own roman by its italic's angle and see
what is left to explain. Real italics score 0.31 and 0.43 on that; Albo's
round-103 "italic" scored **0.852** — it was the roman, sheared, with three
letters redrawn. `outlines/cmp/oblique.py` runs the test.

So this module draws the letters that measurement says a real italic actually
changes — the arch letters, the ascenders, the diagonals — from a CURSIVE
skeleton rather than the roman's. Everything here registers only when
`pen.ITALIC`, so the roman is untouched and one source tree still builds both.

**The one idea the whole file is built on.** A roman arch springs off a
shoulder near the TOP of its stem and lands on the next stem: two stems and a
bridge. An italic arch *branches out of the stem LOW* — it leaves around
two fifths of the x-height as a thinning stroke, climbs, arcs over, and comes
down into the next stem, which is one continuous movement of a pen that never
lifts. Every one of n, m, h, r and (inverted) u follows from that, which is
why `italic_arch` is the first thing here and most of the rest is arithmetic
around it.

What is deliberately KEPT from the roman, because it is what makes this Albo's
italic rather than a second typeface: the pen, the contrast, the x-height and
the cap height, the wedge family where a serif survives at all, and the
figures, capitals and marks (real italics change those far less, and Albo's
capitals are its most settled work).
"""
import math
from . import glyph, GLYPHS
from .. import geom, pen
from ..geom import cubic, line, catmull
from ..primitives import stem, stroke, pen_widths, widths, ring, dot, stem_edge_x, bar
from .. import primitives as PR
from ..pen import S, XH, ASC, DESC, OVER, TH_V, TH_H, HAIR, CUT, BOWL_K, ENT
from .stems import DOT_R, dot_y
from .rounds import o_ring, O_RX

# ---------------------------------------------------------------- the levers
BRANCH_Y = 0.40      # where the arch LEAVES the left stem, x the x-height. The
                     # roman's shoulder is 0.52 and reads as a bridge; a written
                     # hand leaves lower, and this is the single number that
                     # separates the two constructions.
BRANCH_W = 0.30      # the stroke's width where it leaves, x the pen there: the
                     # branch is a hairline that swells as the pen turns over.
ARCH_TOP = 1.0       # the arch's peak, x (xh + the rounds' overshoot)
ENTRY_L = 0.42       # the entry stroke into an ascender or a stem, x the stem
EXIT_L = 0.55        # the exit leaving a foot, x the stem

def italic_arch(x0, x1, xh, branch=BRANCH_Y, top=ARCH_TOP, end_y=0.56, taper=BRANCH_W):
    """THE BRANCHING ARCH. Leaves the left stem's right edge at `branch` of
    the x-height as a thin stroke, climbs, arcs over at `top`, and comes down
    into the right stem at `end_y`. The pen's own widths along it, floored so
    it cannot vanish, and tapered hard over the first third so the branch
    reads as a stroke leaving a stem rather than a second stroke butted on."""
    over_c = pen.ARCH_OVER - TH_H / 2
    xl = stem_edge_x(x0, TH_V, ENT, branch * xh, 0, xh, +1)
    peak = (xh + over_c) * top
    # Round 106 (owner: "you have multiple errors"): the arch used to END at the
    # second stem's CENTRE at 0.56 xh -- it plunged into the stem from above and
    # left the stem's top standing exposed above it, wearing an entry thorn. An
    # italic arch comes over and BECOMES the second stem: it arrives at the
    # stem's top-left, vertical, and the stem continues it down. So the curve
    # ends at (x1, xh) with a vertical tangent, and the stem it lands on takes
    # no entry of its own (`it_entry=False` in _arch_letter).
    center = cubic((xl - S * 0.10, branch * xh),
                   (xl + (x1 - xl) * 0.12, peak * 0.90),
                   (x1 - S * 0.02, peak * 1.02),
                   (x1, xh * 0.94))
    base = pen_widths(center)
    floor = S * 0.30
    def w(t):
        u = min(1.0, t / 0.34)
        return max(base(t) * (taper + (1 - taper) * (3 * u * u - 2 * u ** 3)), floor)
    return stroke(center, w)

def italic_arch_down(x0, x1, xh, branch=0.62, bot=0.06, end_y=0.50):
    """The u's arch, and it is NOT the n's turned over. In a roman the u is
    the n rotated; in a written hand the pen comes DOWN the first stem, turns
    along the baseline and climbs the second, so the thin part is at the
    bottom-left turn and the stroke ends climbing. Drawn as its own curve for
    that reason."""
    xl = stem_edge_x(x0, TH_V, ENT, branch * xh, 0, xh, +1)
    # ends CLIMBING into the second stem's left side at 0.40 xh: a written u
    # turns along the baseline and rises. Landing at the foot (the previous
    # cut) tied a knot at the bottom-right.
    xr = stem_edge_x(x1, TH_V, ENT, 0.40 * xh, 0, xh, -1)
    center = cubic((xl - S * 0.06, branch * xh),
                   (xl + (x1 - xl) * 0.08, bot * xh - OVER * 0.6),
                   (xr - (x1 - x0) * 0.10, bot * xh - OVER * 0.4),
                   (xr + S * 0.12, 0.40 * xh))
    base = pen_widths(center)
    def w(t):
        u = min(1.0, t / 0.30)
        return max(base(t) * (0.42 + 0.58 * (3 * u * u - 2 * u ** 3)), S * 0.30)
    return stroke(center, w)

def istem(x, y0, y1, entry=True, exit_=True, **kw):
    """A stem with the italic's entry and exit instead of wedges. The
    suppression of the wedges lives in `primitives.stem` (a written letter has
    an entry OR a top serif, never both); this just names the intent."""
    return stem(x, y0, y1, top=None if entry else kw.pop('top', None),
                foot=None if exit_ else kw.pop('foot', None), **kw)

def _exit_stroke(x, y=0.0, L=None, w_at=None):
    """The curved exit leaving a foot toward the next letter."""
    L = L or S * EXIT_L; w0 = w_at or TH_V
    p = cubic((x - w0 * 0.34, y + S * 0.16), (x + L * 0.22, y + S * 0.02),
              (x + L * 0.66, y + L * 0.26), (x + L * 1.02, y + L * 0.82))
    return stroke(p, widths([(0.0, w0 * 0.92), (0.45, S * 0.34), (1.0, S * 0.10)]), cut0=None)

# ---------------------------------------------------------------- the arches
def _arch_letter(c, n_arches=1, first_top=None, tail=False):
    """n, m, h: a first stem (ascending for h) and one or two branching arches."""
    xh = c["xh"]; nw = pen.NW
    x0 = S / 2
    parts = [stem(x0, 0, first_top or xh, top=None, foot=None, ent_span=(0, first_top or xh))]
    x = x0
    for i in range(n_arches):
        x1 = x + nw
        parts.append(italic_arch(x, x1, xh))
        last = (i == n_arches - 1)
        # the arch IS this stem's entry; only the LAST stem carries the exit
        parts.append(stem(x1, 0, xh, top=None, foot=None, it_entry=False, it_exit=(None if last else False)))
        x = x1
    return geom.ink(parts)

if pen.ITALIC:

    @glyph('n')
    def g_n_it(c): return _arch_letter(c, 1)

    @glyph('m')
    def g_m_it(c): return _arch_letter(c, 2)

    @glyph('h')
    def g_h_it(c): return _arch_letter(c, 1, first_top=c["asc"])

    @glyph('u')
    def g_u_it(c):
        """Two strokes and nothing else (owner, round 107: "u has extra strokes
        on its left"). The first comes down, turns along the baseline and
        climbs into the second; the second comes down and flicks out. No entry
        at the top-left -- the round-106 u carried one AND a separate arch
        start, which read as two spurs."""
        xh = c["xh"]; x0 = S / 2; x1 = x0 + pen.NW
        xr = stem_edge_x(x1, TH_V, ENT, 0.42 * xh, 0, xh, -1)
        first = catmull([(x0, xh), (x0, xh * 0.30), (x0 + (x1 - x0) * 0.16, -OVER * 0.6),
                         (x0 + (x1 - x0) * 0.62, -OVER * 0.8), (xr + S * 0.10, xh * 0.42)], tension=0.5)
        fw = pen_widths(first)
        return geom.ink([stroke(first, lambda t: max(fw(t) * (1.0 - 0.34 * max(0.0, (t - 0.55) / 0.45)), S * 0.30), cut0=CUT, cut1=None),
                         stem(x1, 0, xh, top=None, foot=None, it_entry=False)])

    @glyph('r')
    def g_r_it(c):
        """The italic r: the branch leaves the stem and stops -- the same
        movement as the n's, cut short. The roman r's arm turns off a
        shoulder near the top; this one climbs out of the stem."""
        xh = c["xh"]
        x0 = S / 2
        xl = stem_edge_x(x0, TH_V, ENT, BRANCH_Y * xh, 0, xh, +1)
        reach = S * 2.15   # the r's arm
        center = cubic((xl - S * 0.10, BRANCH_Y * xh), (xl + reach * 0.22, xh * 0.94),
                       (xl + reach * 0.52, xh + pen.ARCH_OVER - TH_H / 2), (xl + reach, xh * 0.82))
        base = pen_widths(center)
        def w(t):
            u = min(1.0, t / 0.34)
            return max(base(t) * (BRANCH_W + (1 - BRANCH_W) * (3 * u * u - 2 * u ** 3)), S * 0.30)
        return geom.ink([stem(x0, 0, xh, top=None, foot=None), stroke(center, w, cut1=CUT)])

    # ------------------------------------------------------------ ascenders
    @glyph('l')
    def g_l_it(c): return stem(S / 2, 0, c["asc"], top=None, foot=None)

    @glyph('i')
    def g_i_it(c):
        xh = c["xh"]; x = S / 2
        return geom.ink([stem(x, 0, xh, top=None, foot=None), dot(x, dot_y(xh), DOT_R * 0.92)])

    @glyph('j')
    def g_j_it(c):
        xh = c["xh"]; desc = c["desc"]; x = S * 0.62; r = 96 * c["wf"]
        B = -desc * 0.80; y0 = B + r
        st = stem(x, y0 - 24, xh, top=None, foot=None, ent_span=(y0 - 240, xh))
        a0, a1 = 0.0, math.radians(-108)
        tail = [(x - r + r * math.cos(a0 + (a1 - a0) * i / 48), y0 + r * math.sin(a0 + (a1 - a0) * i / 48)) for i in range(49)]
        wfn = widths([(0.0, TH_V * 0.92), (0.45, S * 0.70), (1.0, S * 0.09)])
        return geom.ink([st, stroke(tail, wfn), dot(x, dot_y(xh), DOT_R * 0.92)])

    # ------------------------------------------------------------ the bowls
    # b d p q keep the ROMAN's bowl construction (`stems.bowl_stem`): the o's
    # ring at the b's radius, clipped to the stem, with the crotch traps. A
    # from-scratch italic bowl was tried first and came out at two thirds the
    # size -- advances of 372 and 376 against the roman's 564 and 570 -- which
    # is what happens when a proven construction is replaced rather than
    # parameterised. The italic difference in these four letters comes from
    # IT_OVAL narrowing the ring and from the entry and exit on their stems,
    # and the arch letters are where the skeleton actually changes.

    # ------------------------------------------------------------ diagonals
    @glyph('k')
    def g_k_it(c):
        """The italic k LOOPS (owner, round 107: "k needs a loop"): the arm
        leaves the stem, curls up and round, and comes BACK to the stem,
        closing a small bowl; the leg then leaves from the bottom of that bowl
        and flicks at the baseline. Both models do exactly this; the round-106
        k was two strokes off a stem, which is a roman k's construction."""
        xh = c["xh"]; asc = c["asc"]; x0 = S / 2
        st = stem(x0, 0, asc, top=None, foot=None, it_exit=False)
        xl = stem_edge_x(x0, TH_V, ENT, xh * 0.50, 0, xh, +1)
        loop = catmull([(xl - S * 0.12, xh * 0.44), (xl + S * 0.70, xh * 0.80), (xl + S * 1.55, xh * 1.00),
                        (xl + S * 1.95, xh * 0.80), (xl + S * 1.35, xh * 0.52), (xl + S * 0.20, xh * 0.40)], tension=0.55)
        lw = pen_widths(loop)
        loop_w = lambda t: max(lw(t) * (0.42 + 0.58 * min(1.0, t / 0.30)) * (1.0 - 0.30 * max(0.0, (t - 0.72) / 0.28)), S * 0.26)
        leg = catmull([(xl + S * 0.16, xh * 0.44), (xl + S * 1.20, xh * 0.26), (xl + S * 2.20, xh * 0.06),
                       (xl + S * 2.75, -OVER * 0.3), (xl + S * 3.15, OVER * 0.6)], tension=0.5)
        gw = pen_widths(leg)
        leg_w = lambda t: max(gw(t) * (0.55 + 0.45 * min(1.0, t / 0.25)) * (1.0 - 0.55 * max(0.0, (t - 0.80) / 0.20)), S * 0.14)
        return geom.ink([st, stroke(loop, loop_w), stroke(leg, leg_w, cut1=None)])

    @glyph('z')
    def g_z_it(c):
        """The italic z: an entry curl into the top bar, the diagonal, and a
        tail that sweeps under the letter and curls back. The round-106 z had
        a straight bar and a thin tail -- the shape without the flourish."""
        xh = c["xh"]; w = XH * 0.95 * c["wf"]
        top = catmull([(w * 0.06, xh * 0.78), (w * 0.02, xh * 0.94), (w * 0.22, xh * 1.00), (w * 0.98, xh * 0.98)], tension=0.5)
        tw_ = pen_widths(top)
        diag = line((w * 0.94, xh * 0.94), (w * 0.10, TH_H * 0.9))
        dw = pen_widths(diag)
        tail = catmull([(w * 0.18, TH_H * 1.0), (w * 0.55, -XH * 0.02), (w * 0.98, -XH * 0.16),
                        (w * 1.10, -XH * 0.30), (w * 0.94, -XH * 0.38)], tension=0.5)
        tl = pen_widths(tail)
        return geom.ink([stroke(top, lambda t: max(tw_(t) * (0.5 + 0.5 * min(1.0, t / 0.25)), S * 0.22)),
                         stroke(diag, lambda t: max(dw(t), S * 0.36)),
                         stroke(tail, lambda t: max(tl(t) * (1.0 - 0.55 * max(0.0, (t - 0.55) / 0.45)), S * 0.14), cut0=None)])

    def _curl_up(x, y, w, xh):
        """The thin stroke arriving at the top-right and curling back in over
        itself: the terminal both models put on the v, the w and the x."""
        return catmull([(x - w * 0.02, y - xh * 0.30), (x + w * 0.05, y - xh * 0.06), (x + w * 0.02, y + xh * 0.05),
                        (x - w * 0.10, y + xh * 0.04), (x - w * 0.14, y - xh * 0.04)], tension=0.5)

    @glyph('v')
    def g_v_it(c):
        xh = c["xh"]; w = XH * 0.86 * c["wf"]
        left = cubic((0, xh), (w * 0.16, xh * 0.52), (w * 0.34, xh * 0.20), (w * 0.52, 0))
        right = cubic((w * 0.52, 0), (w * 0.70, xh * 0.34), (w * 0.86, xh * 0.62), (w * 0.94, xh * 0.72))
        curl = _curl_up(w * 0.94, xh * 0.98, w * 0.5, xh)
        lw = pen_widths(left); rw = pen_widths(right); cw = pen_widths(curl)
        return geom.ink([stroke(left, lambda t: max(lw(t), S * 0.36), cut0=CUT, cut1=None),
                         stroke(right, lambda t: max(rw(t) * (1.0 - 0.28 * t), S * 0.20), cut0=None, cut1=None),
                         stroke(curl, lambda t: max(cw(t) * (0.9 - 0.5 * t), S * 0.12), cut0=None)])

    @glyph('w')
    def g_w_it(c):
        xh = c["xh"]; w = XH * 1.30 * c["wf"]
        parts = []
        for k in (0, 1):
            ox = k * w * 0.50; last = (k == 1)
            left = cubic((ox, xh), (ox + w * 0.08, xh * 0.52), (ox + w * 0.17, xh * 0.20), (ox + w * 0.26, 0))
            rt = (ox + w * 0.47, xh * 0.72) if last else (ox + w * 0.50, xh)
            right = cubic((ox + w * 0.26, 0), (ox + w * 0.35, xh * 0.34), (ox + w * 0.43, xh * 0.62), rt)
            lw = pen_widths(left); rw = pen_widths(right)
            parts.append(stroke(left, lambda t, f=lw: max(f(t), S * 0.34), cut0=CUT, cut1=None))
            parts.append(stroke(right, lambda t, f=rw: max(f(t) * (1.0 - 0.22 * t), S * 0.20), cut0=None, cut1=(None if last else CUT)))
            if last:
                curl = _curl_up(ox + w * 0.47, xh * 0.98, w * 0.30, xh); cw = pen_widths(curl)
                parts.append(stroke(curl, lambda t, f=cw: max(f(t) * (0.9 - 0.5 * t), S * 0.12), cut0=None))
        return geom.ink(parts)

    @glyph('x')
    def g_x_it(c):
        """The thick stroke is an elongated reverse S: a curl opening up-left
        at its start, the diagonal, a curl opening down-right at its end.
        The thin stroke crosses it as a hairline. Both models draw the x this
        way; round 106's was two plain curves with square cuts."""
        xh = c["xh"]; w = XH * 0.90 * c["wf"]
        thick = catmull([(w * 0.30, xh * 1.06), (w * 0.08, xh * 0.96), (w * 0.14, xh * 0.78),
                         (w * 0.50, xh * 0.50), (w * 0.86, xh * 0.20), (w * 0.94, xh * 0.02), (w * 0.70, -OVER * 0.9)], tension=0.5)
        thin = cubic((w * 1.02, xh * 0.98), (w * 0.64, xh * 0.62), (w * 0.34, xh * 0.34), (w * 0.02, -OVER * 0.2))
        tw = pen_widths(thick); nw_ = pen_widths(thin)
        thick_w = lambda t: max(tw(t) * (0.55 + 0.45 * min(1.0, t / 0.22)) * (1.0 - 0.45 * max(0.0, (t - 0.82) / 0.18)), S * 0.18)
        return geom.ink([stroke(thick, thick_w, cut0=None, cut1=None),
                         stroke(thin, lambda t: max(nw_(t) * 0.55, S * 0.20), cut0=CUT, cut1=CUT)])

    @glyph('y')
    def g_y_it(c):
        """The v's two strokes, the right one continuing down into a tail
        that curves back under the letter -- one movement, as a written y is."""
        xh = c["xh"]; desc = c["desc"]; w = XH * 0.84 * c["wf"]
        left = cubic((0, xh), (w * 0.16, xh * 0.52), (w * 0.34, xh * 0.20), (w * 0.52, 0))
        right = cubic((w * 0.98, xh), (w * 0.86, xh * 0.50), (w * 0.72, xh * 0.02), (w * 0.60, -desc * 0.36))
        tail = cubic((w * 0.60, -desc * 0.36), (w * 0.50, -desc * 0.78), (w * 0.24, -desc * 0.92), (w * 0.02, -desc * 0.72))
        lw = pen_widths(left); rw = pen_widths(right); tw = pen_widths(tail)
        return geom.ink([stroke(left, lambda t: max(lw(t), S * 0.36), cut0=CUT, cut1=None),
                         stroke(right, lambda t: max(rw(t) * (1.0 - 0.16 * t), S * 0.30), cut0=CUT, cut1=None),
                         stroke(tail, lambda t: max(tw(t) * (0.9 - 0.62 * t), S * 0.10), cut0=None)])
