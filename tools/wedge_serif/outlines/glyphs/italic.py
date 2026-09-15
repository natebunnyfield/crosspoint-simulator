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
        """From the models: a SHORT arm that branches low, rises, and ends in a
        small curled ball -- not a long swoop with a cut end."""
        xh = c["xh"]; x0 = S / 2
        st = stem(x0, 0, xh, top=None, foot=None)
        xl = stem_edge_x(x0, TH_V, ENT, xh * 0.40, 0, xh, +1)
        arm = catmull([(xl - S * 0.12, xh * 0.42), (xl + S * 0.45, xh * 0.82), (xl + S * 1.20, xh * 1.02),
                       (xl + S * 1.62, xh * 0.94), (xl + S * 1.55, xh * 0.80)], tension=0.5)
        aw = pen_widths(arm)
        # the ball sits ON the arm's last point, not beside it: a dot placed
        # clear of the stroke reads as a detached blob
        return geom.ink([st, stroke(arm, lambda t: max(aw(t) * (0.32 + 0.68 * min(1.0, t / 0.35)), S * 0.24), cut1=CUT)])


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
        """ONE loop (owner, round 108b: "extra loops on k"). The arm comes off
        the stem, swings right and curves BACK toward it -- that returning
        curve IS the loop -- and the leg leaves the same junction and runs to
        the baseline. Round 108's k had a closed bowl AND a hooked arm AND a
        leg: three gestures, which read as two loops. The models have one."""
        xh = c["xh"]; asc = c["asc"]; x0 = S / 2
        st = stem(x0, 0, asc, top=None, foot=None, it_exit=False)
        xl = stem_edge_x(x0, TH_V, ENT, xh * 0.50, 0, xh, +1)
        arm = catmull([(xl + S * 1.95, xh * 1.00), (xl + S * 1.55, xh * 0.74),
                       (xl + S * 0.75, xh * 0.52), (xl - S * 0.15, xh * 0.44)], tension=0.5)
        aw = pen_widths(arm)
        leg = catmull([(xl + S * 0.10, xh * 0.46), (xl + S * 1.15, xh * 0.26),
                       (xl + S * 2.15, xh * 0.06), (xl + S * 2.70, OVER * 0.2), (xl + S * 3.05, xh * 0.10)], tension=0.5)
        gw = pen_widths(leg)
        return geom.ink([st,
                         stroke(arm, lambda t: max(aw(t) * (0.45 + 0.55 * min(1.0, t / 0.35)), S * 0.20), cut0=CUT),
                         stroke(leg, lambda t: max(gw(t) * (0.95 - 0.5 * max(0.0, (t - 0.72) / 0.28)), S * 0.14), cut0=None)])

    @glyph('z')
    def g_z_it(c):
        """From the models: a hooked entry into the top bar, the diagonal, and
        a bottom sweep that runs right and curls DOWN into a descending hook.
        Round 107's entry was a spike and its tail a stub."""
        xh = c["xh"]; w = XH * 0.96 * c["wf"]
        top = catmull([(w * 0.10, xh * 0.70), (w * 0.00, xh * 0.86), (w * 0.10, xh * 0.98), (w * 0.60, xh * 1.00), (w * 1.00, xh * 0.96)], tension=0.5)
        tw_ = pen_widths(top)
        diag = line((w * 0.96, xh * 0.92), (w * 0.14, TH_H * 1.1))
        dw = pen_widths(diag)
        tail = catmull([(w * 0.10, TH_H * 1.2), (w * 0.46, -XH * 0.02), (w * 0.82, -XH * 0.12),
                        (w * 0.96, -XH * 0.26)], tension=0.5)
        tl = pen_widths(tail)
        return geom.ink([stroke(top, lambda t: max(tw_(t) * (0.35 + 0.65 * min(1.0, t / 0.3)), S * 0.16), cut0=None),
                         stroke(diag, lambda t: max(dw(t), S * 0.36)),
                         stroke(tail, lambda t: max(tl(t) * (1.0 - 0.6 * max(0.0, (t - 0.6) / 0.4)), S * 0.12), cut0=None)])


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
        """Two curved strokes crossing at the letter's centre, the thick one
        falling and the thin one rising, each with ONE light turn at its
        lower end. Round 108's had a hook at every end and read as a knot."""
        xh = c["xh"]; w = XH * 0.90 * c["wf"]
        thick = catmull([(w * 0.16, xh * 1.00), (w * 0.30, xh * 0.78), (w * 0.50, xh * 0.50),
                         (w * 0.74, xh * 0.20), (w * 0.86, -OVER * 0.5)], tension=0.5)
        thin = catmull([(w * 0.96, xh * 1.00), (w * 0.74, xh * 0.76), (w * 0.50, xh * 0.50),
                        (w * 0.22, xh * 0.20), (w * 0.04, -OVER * 0.5)], tension=0.5)
        tw = pen_widths(thick); nw_ = pen_widths(thin)
        return geom.ink([stroke(thick, lambda t: max(tw(t), S * 0.36), cut0=CUT, cut1=CUT),
                         stroke(thin, lambda t: max(nw_(t) * 0.52, S * 0.20), cut0=CUT, cut1=CUT)])

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

    @glyph('f')
    def g_f_it2(c):
        """From the models: the italic f is a tall S. The top hook sweeps wide
        and high; the stem runs through the baseline and curves LEFT into a
        tail that mirrors the hook; the bar sits on the x-height."""
        xh = c["xh"]; asc = c["asc"]; desc = c["desc"]; x = S * 1.6
        top = catmull([(x + S * 2.10, asc * 0.94), (x + S * 1.50, asc * 1.02), (x + S * 0.70, asc * 0.96),
                       (x + S * 0.10, asc * 0.72), (x, asc * 0.45)], tension=0.5)
        st = stem(x, -desc * 0.30, asc * 0.50, top=None, foot=None, it_entry=False, it_exit=False)
        bot = catmull([(x, -desc * 0.22), (x - S * 0.10, -desc * 0.58), (x - S * 0.70, -desc * 0.86),
                       (x - S * 1.50, -desc * 0.92), (x - S * 2.05, -desc * 0.80)], tension=0.5)
        tw_ = pen_widths(top); bw = pen_widths(bot)
        th = TH_H * 0.8
        bar = stroke([(x - S * 0.9, xh - th / 2), (x + S * 1.7, xh - th / 2)], th)
        return geom.ink([stroke(top, lambda t: max(tw_(t) * (0.5 + 0.5 * min(1.0, t / 0.3)), S * 0.16), cut0=None, cut1=None),
                         st, stroke(bot, lambda t: max(bw(t) * (1.0 - 0.6 * max(0.0, (t - 0.6) / 0.4)), S * 0.14), cut0=None, cut1=None), bar])

    @glyph('g')
    def g_g_it(c):
        """From the models: the upper bowl the o's oval, the lower loop WIDER
        and more open, the neck a thin diagonal between them, and the ear a
        sweep to the right off the bowl's shoulder rather than a stub."""
        xh = c["xh"]; desc = c["desc"]
        bowl, bo, bi = o_ring(c, O_RX * 0.88, ry_center=xh * 0.34, cy=xh * 0.66)
        bx0, by0, bx1, by1 = bowl.bounds
        lcx = (bx0 + bx1) / 2 - S * 0.25; lcy = -desc * 0.52
        loop, lo, li = ring(lcx, lcy, (bx1 - bx0) * 0.62, desc * 0.44, w_scale=0.92)
        # the neck STARTS INSIDE the bowl's ink and ENDS INSIDE the loop's, or
        # the three pieces do not union and the g comes apart (round 108's
        # first cut: bowl, loop and a floating diagonal between them)
        neck = cubic((bx1 - TH_V * 0.9, xh * 0.52), (bx1 - TH_V * 0.5, xh * 0.14),
                     (lcx + (bx1 - bx0) * 0.44, -desc * 0.04), (lcx + (bx1 - bx0) * 0.50, -desc * 0.30))
        nw_ = pen_widths(neck)
        ear = catmull([(bx1 - TH_V * 1.1, xh * 0.84), (bx1 + S * 0.30, xh * 1.00), (bx1 + S * 0.95, xh * 1.02), (bx1 + S * 1.20, xh * 0.92)], tension=0.5)
        ew = pen_widths(ear)
        return geom.ink([bowl, loop, stroke(neck, lambda t: max(nw_(t) * 0.75, S * 0.32), cut0=None, cut1=None),
                         stroke(ear, lambda t: max(ew(t) * (0.9 - 0.4 * t), S * 0.14), cut0=None)])

