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
from ..geom import cubic, line
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
    center = cubic((xl - S * 0.10, branch * xh),
                   (xl + (x1 - xl) * 0.10, peak * 0.86),
                   (x0 + (x1 - x0) * 0.62, peak),
                   (x1, end_y * xh))
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
    center = cubic((xl - S * 0.06, branch * xh),
                   (xl + (x1 - xl) * 0.06, bot * xh - OVER * 0.5),
                   (x0 + (x1 - x0) * 0.60, bot * xh - OVER),
                   (x1, end_y * xh))
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
        parts.append(stem(x1, 0, xh, top=None, foot=None))
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
        xh = c["xh"]; x0 = S / 2; x1 = x0 + pen.NW
        return geom.ink([stem(x0, 0, xh, top=None, foot=None),
                         italic_arch_down(x0, x1, xh),
                         stem(x1, 0, xh, top=None, foot=None)])

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
        xh = c["xh"]; desc = c["desc"]; x = S * 0.62; r = 118 * c["wf"]
        B = -desc * 0.92; y0 = B + r
        st = stem(x, y0 - 24, xh, top=None, foot=None, ent_span=(y0 - 240, xh))
        a0, a1 = 0.0, math.radians(-124)
        tail = [(x - r + r * math.cos(a0 + (a1 - a0) * i / 48), y0 + r * math.sin(a0 + (a1 - a0) * i / 48)) for i in range(49)]
        wfn = widths([(0.0, TH_V * 0.92), (0.45, S * 0.86), (1.0, S * 0.09)])
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
        """The italic k's leg CURVES -- both references change the k more than
        almost any other letter. The arm comes off the stem as a branch and the
        leg swings out of the join and curls to the baseline."""
        xh = c["xh"]; asc = c["asc"]; x0 = S / 2
        st = stem(x0, 0, asc, top=None, foot=None)
        xl = stem_edge_x(x0, TH_V, ENT, xh * 0.46, 0, xh, +1)
        arm = cubic((xl - S * 0.08, xh * 0.46), (xl + S * 0.9, xh * 0.72),
                    (xl + S * 2.2, xh * 0.96), (xl + S * 3.05, xh * 1.02))
        aw = pen_widths(arm)
        arm_w = lambda t: max(aw(t) * (0.34 + 0.66 * min(1.0, t / 0.36)), S * 0.30)
        leg = cubic((xl + S * 0.34, xh * 0.60), (xl + S * 1.55, xh * 0.34),
                    (xl + S * 2.05, xh * 0.10), (xl + S * 3.30, -OVER * 0.4))
        lw = pen_widths(leg)
        leg_w = lambda t: max(lw(t) * (0.42 + 0.58 * min(1.0, t / 0.30)), S * 0.32)
        return geom.ink([st, stroke(arm, arm_w, cut1=CUT), stroke(leg, leg_w, cut1=CUT)])

    @glyph('z')
    def g_z_it(c):
        """The italic z: the bottom bar leaves the diagonal and CURVES below
        the baseline into a tail. The roman z is three straight strokes; both
        references redraw this letter more than they redraw the o."""
        xh = c["xh"]; w = XH * 0.95 * c["wf"]
        top = bar(0, w, xh, TH_H * 0.95, align='top')
        diag = line((w - TH_H * 0.3, xh - TH_H * 0.7), (TH_H * 0.5, TH_H * 0.8))
        dw = pen_widths(diag)
        tail = cubic((0, TH_H * 0.9), (w * 0.52, TH_H * 0.2),
                     (w * 0.92, -XH * 0.10), (w * 1.12, -XH * 0.22))
        tw = pen_widths(tail)
        return geom.ink([top, stroke(diag, lambda t: max(dw(t), S * 0.34)),
                         stroke(tail, lambda t: max(tw(t) * (1.0 - 0.45 * t), S * 0.16), cut1=CUT)])

    @glyph('v')
    def g_v_it(c):
        xh = c["xh"]; w = XH * 0.86 * c["wf"]
        left = cubic((0, xh), (w * 0.16, xh * 0.52), (w * 0.34, xh * 0.20), (w * 0.52, 0))
        right = cubic((w * 0.52, 0), (w * 0.70, xh * 0.34), (w * 0.86, xh * 0.72), (w, xh))
        lw = pen_widths(left); rw = pen_widths(right)
        return geom.ink([stroke(left, lambda t: max(lw(t), S * 0.36), cut0=CUT, cut1=None),
                         stroke(right, lambda t: max(rw(t) * (1.0 - 0.28 * t), S * 0.20), cut0=None, cut1=CUT)])

    @glyph('w')
    def g_w_it(c):
        xh = c["xh"]; w = XH * 1.30 * c["wf"]
        parts = []
        for k in (0, 1):
            ox = k * w * 0.50
            left = cubic((ox, xh), (ox + w * 0.08, xh * 0.52), (ox + w * 0.17, xh * 0.20), (ox + w * 0.26, 0))
            right = cubic((ox + w * 0.26, 0), (ox + w * 0.35, xh * 0.34), (ox + w * 0.43, xh * 0.72), (ox + w * 0.50, xh))
            lw = pen_widths(left); rw = pen_widths(right)
            parts.append(stroke(left, lambda t, f=lw: max(f(t), S * 0.34), cut0=CUT, cut1=None))
            parts.append(stroke(right, lambda t, f=rw: max(f(t) * (1.0 - 0.22 * t), S * 0.20), cut0=None, cut1=CUT))
        return geom.ink(parts)
