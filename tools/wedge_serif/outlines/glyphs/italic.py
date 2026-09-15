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
import math, os
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

    # ------------------------------------------------------------- the g
    # Round 109d. Written from a COMPLETE trace of Coelacanth's italic g
    # rather than from separate measurements of its parts, because the parts
    # were never the problem -- the structure was. Walking that letter's outer
    # contour all the way round says it is not a bowl plus a loop plus a
    # connector. It is a bowl, and then ONE continuous descending stroke that
    # leaves the bowl's bottom-left heading down and LEFT, swings out past the
    # bowl's own left edge, comes round the loop counter-clockwise through 343
    # degrees, and rises along the loop's top back to the SAME place on the
    # bowl's bottom. Both ends land within 17 degrees of each other there --
    # the ring is effectively cut by one radial face at 250 degrees, the
    # stroke leaving from that cut's inner corner and returning to its outer
    # corner. That is why every earlier cut of this letter read as two rings
    # with a wire between them, however the wire was drawn: a wire between two
    # closed rings is not what the pen does, and no amount of tangency fixes a
    # structure that is wrong.
    #
    # EVERY NUMBER BELOW IS UNSHEARED, and that correction is the round's
    # second lesson. The first pass read Coelacanth's boxes straight off the
    # shipped outlines -- which carry its own 13.57-degree slant, measured off
    # its l rather than taken from post.italicAngle, which is 0.0 and a lie --
    # and then used them as DESIGN offsets in Albo, where build.py shears
    # again at the end. The slant got counted twice. It inverted the two facts
    # that matter most here: sheared, the loop appears to sit 0.19 bowl-widths
    # LEFT of the bowl and the neck appears to bulge past the bowl's left
    # edge; unsheared, the loop sits 0.17 bowl-widths to the RIGHT and the
    # neck stays a tenth of an x-height INSIDE that edge. Round 102 recorded
    # that a wrong measurement is worse than no measurement because it carries
    # the authority of a number; this is the same trap with the slant in it.
    #
    # Coelacanth's g with its slant removed, at its 415 x-height:
    #
    #   bowl outer      308.4 x 411.0   centre (147.2,  210.5)
    #   bowl counter    175.2 x 293.0   side wall 66.6 = 0.160 xh
    #   loop outer      372.0 x 308.0   centre (199.5, -183.0)
    #   loop counter    283.1 x 180.0
    #   neck outer      x 33.6..126.2, y -80..53 -- leftmost 0.098 xh INSIDE
    #                   the bowl's own left edge, so there is no bulge at all
    #   ear             x 251.8..365.7, y 306..380, tip 0.145 xh past the
    #                   bowl's right edge at 0.819 xh, 0.81 -> 1.03 of the
    #                   bowl's own side wall in thickness
    #
    #   loop half-width / bowl half-width   1.206
    #   loop centre                         +0.170 bowl-widths (RIGHT)
    #   the stroke leaves and rejoins the bowl at 259 and 258.5 degrees
    #   it meets the loop at 124 and leaves it at 100
    #
    # THE DEPTH IS ALBO'S, NOT COELACANTH'S, and that is a measurement too.
    # Coelacanth's g bottoms at 0.812 of its x-height -- and so do its p
    # (0.810), q (0.839) and j (0.800). A deep g is that family's descender,
    # not a property of the letter. Albo's own p and q bottom at 0.643 and
    # 0.655, so the g takes 0.655 and the loop is fitted into that depth by
    # Coelacanth's own two proportions (centre at 0.543 of the depth, half-
    # height 0.457 of it). Copying 0.812 would have hung one letter a third of
    # a descender below every other.
    # ALBO'S DESCENDER CANNOT HOLD COELACANTH'S LOOP, and the letter is laid
    # out from that fact rather than against it. Coelacanth's bowl has a
    # bottom wall of 0.193 xh, so its ring's CENTRELINE bottom sits 0.108 xh
    # ABOVE the baseline and its loop's centreline top 0.147 xh below it --
    # 0.255 xh of neck between them, inside a 0.812 xh descender. Albo's
    # bottom wall is 0.093 xh (a higher-contrast pen), so its centreline
    # bottom is at 0.016 xh, and its descender is 0.655. Ask for Coelacanth's
    # loop proportions in that space and the loop's top lands ABOVE the
    # baseline, inside the bowl: the first cut of this drew the loop from the
    # depth down, the neck came out 0.11 xh long, and the two stub strokes'
    # square caps collided at the join and stood out as a barb.
    #
    # So the NECK is the fixed quantity and the loop is fitted under it: the
    # loop's centreline top is one neck-length below where the stroke leaves
    # the bowl, its centreline bottom is the descender less half the pen, and
    # its width follows from an aspect ratio rather than from the bowl. The
    # neck is shortened to 0.155 xh, which is what the space allows, and the
    # loop then runs flatter than Coelacanth's (1.50 against its 1.34) -- an
    # honest consequence of a shallower descender under a taller bowl, not a
    # taste decision. It cannot go flatter than that, and the limit is
    # mechanical rather than aesthetic: an ellipse's radius of curvature at its
    # ends is (half-height squared) over (half-width), and when that approaches
    # the pen's half-width the stroke's inner edge folds through itself. At
    # 1.62 the ratio was 1.96 and the loop's far left came to a pinched corner;
    # at 1.50 it is 2.36. Coelacanth can afford 1.34 at a ratio of 4.1 because
    # its loop is bigger relative to its pen, which is the same shallow-
    # descender constraint seen from the other side.
    G_DEPTH    = 0.655    # of the x-height -- Albo's own p/q descender
    G_NECK     = 0.155    # x the x-height: centreline distance from the bowl to the loop
    G_LOOP_RY  = 0.40     # the loop's half-height, x the descender depth
    G_LOOP_ASP = 1.50     # the loop's centreline width over its height
    G_LOOP_DX  = 0.060    # loop centre, this many bowl-widths right of the bowl's
    G_OUT_DEG  = 258.0    # where the stroke leaves the bowl
    G_IN_DEG   = 258.0    # and where it rejoins it -- the SAME point, which is
                          # what Coelacanth does (259.0 and 258.5). Separating
                          # them was an attempt to stop the two square end caps
                          # meeting point-to-point and standing out as a barb;
                          # that barb was really a symptom of the neck being a
                          # stub, and once the neck had its corner and its full
                          # length the separation only bought a white crack
                          # between the departure and the return -- 53 x 20
                          # units of it, its own contour in the built font.
    G_LOOP_OUT = 124.0    # where it meets the loop going out
    G_LOOP_IN  = 100.0    # and leaves the loop coming back
    G_NECK_CX  = 0.845    # THE CORNER. The neck is not one smooth curve: it is
    G_NECK_CY  = 0.036    # two strokes meeting at a sharp corner out to the
                          # LEFT, and leaving it out is what made Albo's neck
                          # read as a plain vertical connector. Owner, round
                          # 109d: "there is a corner, two stroke to the left
                          # that you need to be including." It is in
                          # Coelacanth's outline as two nearly straight edges:
                          # one from the bowl's bottom-left running down-left
                          # to a point, and one from that point running
                          # down-right into the loop. Reading the centreline
                          # back off it -- the contour runs counter-clockwise
                          # with the ink on its left, so the centreline is half
                          # a pen-width down-right of that edge -- puts the
                          # corner at 0.845 of the bowl's centreline half-width
                          # left of the bowl's centre, and 0.036 of the
                          # x-height BELOW the baseline. An earlier cut of this
                          # round measured only the neck's two ENDPOINTS, found
                          # them 16 units apart in x, and concluded the neck
                          # was near-vertical; the endpoints are near-vertical
                          # and the path between them is not.
    G_JOIN     = 0.55     # how far the return overshoots the bowl's ring
                          # centreline, x the flat pen -- see the junction note
    # Owner 2026-09-15: "the line connecting the two ovals needs to be thinner
    # at the connection with the lower oval in g. and generally there needs to
    # be some lightening and/or contrast." G_NECK_THIN is the descending
    # stroke's width where it MEETS THE LOOP, x its width leaving the bowl; it
    # eases back to full over G_NECK_BACK of the path once on the loop.
    # G_FLOOR is the width floor under the pen, which is what was holding the
    # whole stroke near-monoline -- lowering it is the "contrast" half.
    G_NECK_THIN = float(os.environ.get("ALBO_G_NECK_THIN", 1.00))
    G_NECK_BACK = float(os.environ.get("ALBO_G_NECK_BACK", 0.10))
    G_FLOOR     = float(os.environ.get("ALBO_G_FLOOR", 0.34))
    # Owner 2026-09-15, with a reference image: "for italic g, let's do an
    # italic swoopy loop like shown, but in albo style. FOLLOW THE BRUSH
    # STROKES AND CONTRAST OF THE EXAMPLE." The reference is a high-contrast
    # baroque italic g: its descender is not a flat oval sitting under the
    # bowl, it is a big TILTED loop that swings out and down, thick along its
    # lower-left where the pen pulls down, and a hairline where it comes back
    # up to the right. Three things make that shape and none of them existed
    # here: the loop had no tilt at all, it was too small to swing, and the
    # floor under the pen was high enough to keep the whole stroke near one
    # weight. G_LOOP_ROT tilts the loop's axis, G_LOOP_SWELL scales it about
    # its own centre, and G_FLOOR above is the contrast.
    G_LOOP_ROT   = float(os.environ.get("ALBO_G_LOOP_ROT", 0.0))
    G_LOOP_SWELL = float(os.environ.get("ALBO_G_LOOP_SWELL", 1.0))
    # Owner 2026-09-15, after the first swoop ladder: "you need to resize the
    # top loop and resize the bottom loop and try all over again. pay as much
    # attention to space between as stroke placement and angle. you have missed
    # most of the criteria so far." He is right and it is measurable. The
    # criterion I had not been measuring is the RELATION OF THE TWO COUNTERS:
    # on his reference the lower counter is 1.42x the upper one in AREA, and
    # Albo's is 0.46x -- the lower counter is a third of the size it should be
    # relative to the upper. The reference's bowl counter is also round (0.87
    # wide over tall) where Albo's is tall and narrow (0.63).
    #
    # So the bowl is no longer simply the o. G_BOWL_H shortens it with its TOP
    # PINNED at the x-height (a g's bowl still has to sit on that line, so the
    # room can only come off the bottom) and G_BOWL_W widens it. Both default
    # to 1.0, which reproduces the o-derived bowl exactly.
    G_BOWL_W = float(os.environ.get("ALBO_G_BOWL_W", 1.0))
    G_BOWL_H = float(os.environ.get("ALBO_G_BOWL_H", 1.0))
    # Owner again, 2026-09-15: "A is close but you've continued to ignore my ask
    # that you REDUCE the loops so that you can match the provided example." I
    # had been growing the lower one -- rung A's loop counter was 393 x 288
    # against the 244 x 171 it started at. Reducing BOTH ovals only opens their
    # counters if the WALLS come in with them, otherwise a smaller oval at the
    # same pen is just a thicker ring round a smaller hole. That is what these
    # two do, and it is the same "lightening and contrast" he asked for twice.
    G_BOWL_WALL = float(os.environ.get("ALBO_G_BOWL_WALL", 1.0))   # the bowl ring's pen, x normal
    G_LOOP_WALL = float(os.environ.get("ALBO_G_LOOP_WALL", 1.0))   # the descending stroke's pen, x normal
    G_EAR_DEG  = 33.0     # where the ear leaves the bowl
    G_EAR_OUT  = 0.145    # how far past the bowl's right edge its tip reaches (x xh)
    G_EAR_Y    = 0.819    # the height of that tip (x xh)

    # THE DUCTUS, owner 2026-09-15: "look at there are two strokes for the
    # example. match those. one on top left, the other from top right, down to
    # bottom left and looping to form bottom loop."
    #
    # That is the whole letter and it is not what was here. Every previous cut
    # built a CLOSED bowl (the o's ring) with a descender hung off it, which is
    # why the junction never came right however it was drawn: a closed ring has
    # no place for a second stroke to arrive. The reference is two pen
    # movements and the bowl is where they OVERLAP, not a thing either of them
    # draws alone.
    #
    #   STROKE ONE   lands to the right, sweeps LEFT over the bowl's top and
    #                down its left side to the bottom-left. The ear is this
    #                stroke's entry, not a separate flick -- which is what
    #                makes it two strokes and not three.
    #   STROKE TWO   starts at the bowl's top-right, comes DOWN the right side,
    #                round the bottom, out to the bottom-left, and on into the
    #                loop without lifting.
    #
    # The counter is enclosed by the pair. They overlap twice, at the top-right
    # where two starts sit together and at the bottom-left where one ends and
    # the other passes through, so there is no junction to patch.
    G_A0 = float(os.environ.get("ALBO_G_A0", 16.0))    # stroke one: where it meets the bowl, degrees
    G_A1 = float(os.environ.get("ALBO_G_A1", 262.0))   # ... and where it ends, sweeping left and down
    G_B0 = float(os.environ.get("ALBO_G_B0", 40.0))    # stroke two: where it starts, top-right
    # Owner 2026-09-15: "you're getting connector stroke direction wrong, it
    # crosses RIGHT TO LEFT." Stroke two was leaving the bowl at its bottom-LEFT
    # (196 degrees) and dropping straight into the loop, which makes the bowl a
    # near-complete ring and the connector a short link. It leaves at the
    # bottom-RIGHT and CROSSES the letter diagonally down-left, passing under
    # the bowl -- which is why the reference has a long diagonal through it, and
    # why that diagonal is what closes the bowl's bottom rather than the arc.
    G_B1 = float(os.environ.get("ALBO_G_B1", 298.0))   # ... and where it leaves the bowl to cross

    @glyph('g')
    def g_g_it(c):
        """Two strokes. The bowl is where they overlap."""
        xh = c["xh"]
        _wf = c["wf"] * pen.IT_OVAL
        brx = (O_RX * _wf + TH_V / 2) * G_BOWL_W
        bry = (xh / 2 + OVER) * G_BOWL_H
        bcx = brx; bcy = (xh + OVER) - bry
        crx = brx - TH_V / 2 * G_BOWL_WALL
        cry = bry - TH_H / 2 * G_BOWL_WALL

        def Bp(deg):
            a = math.radians(deg)
            return (bcx + crx * math.cos(a), bcy + cry * math.sin(a))

        def arc(d0, d1, n=150):
            return [Bp(d0 + (d1 - d0) * i / n) for i in range(n + 1)]

        # ---- the loop, sized and tilted as before -------------------------
        depth = xh * G_DEPTH
        # The loop is sized off the DESCENDER, not off the bowl's bottom. It was
        # the other way round for one build and the loop ballooned the moment
        # the bowl was shortened -- a shorter bowl raises its own bottom, which
        # made the gap it was measured from larger, which made the loop bigger,
        # which is backwards.
        bot = -(depth - TH_H / 2)
        mry = depth * G_LOOP_RY * G_LOOP_SWELL
        mrx = mry * G_LOOP_ASP
        lcy = bot + mry
        lcx = bcx + (brx * 2) * G_LOOP_DX
        _rot = math.radians(G_LOOP_ROT); _cr, _sr = math.cos(_rot), math.sin(_rot)

        def L(phi):
            x, y = mrx * math.cos(phi), mry * math.sin(phi)
            return (lcx + x * _cr - y * _sr, lcy + x * _sr + y * _cr)

        _low = min(L(i * math.pi / 180.0)[1] for i in range(360))
        lcy += bot - _low

        def bez(p0, c1, c2, p3, n=70):
            out_ = []
            for i in range(n + 1):
                t = i / n; u = 1 - t
                out_.append((u*u*u*p0[0] + 3*u*u*t*c1[0] + 3*u*t*t*c2[0] + t*t*t*p3[0],
                             u*u*u*p0[1] + 3*u*u*t*c1[1] + 3*u*t*t*c2[1] + t*t*t*p3[1]))
            return out_

        # ---- STROKE ONE: the ear, the top, and down the left --------------
        E1 = (bcx + brx + xh * G_EAR_OUT, xh * G_EAR_Y)
        A_on = Bp(G_A0)
        lead = bez(E1,
                   (E1[0] - (E1[0] - A_on[0]) * 0.45, E1[1]),
                   (A_on[0] + (E1[0] - A_on[0]) * 0.30, A_on[1] + (E1[1] - A_on[1]) * 0.55),
                   A_on, n=40)
        one = lead + arc(G_A0, G_A1)[1:]
        w1 = pen_widths(one, floor=S * G_FLOOR * G_BOWL_WALL)
        # thin at the ear's landing, full through the top and the left flank,
        # tapering again as it runs out at the bottom-left
        # stroke one runs PAST where stroke two leaves the bowl and stays near
        # full width to its end, because the two have to OVERLAP there or the
        # counter leaks out at the bottom-left -- both of them tapering into the
        # same place is what opened it.
        prof1 = widths([(0.0, 0.30), (0.10, 0.70), (0.20, 1.0), (0.86, 1.0), (1.0, 0.86)])
        s_one = stroke(one, lambda t: w1(t) * prof1(t) * G_BOWL_WALL, raw=True, pieces=True)

        # ---- STROKE TWO: top-right, down the right, out and round the loop --
        b_out = arc(G_B0, G_B1 - 360.0, n=170)      # clockwise: 40 -> -164
        Pa = L(math.radians(G_LOOP_OUT)); Ta = None
        dxp, dyp = -mrx * math.sin(math.radians(G_LOOP_OUT)), mry * math.cos(math.radians(G_LOOP_OUT))
        tx, ty = dxp * _cr - dyp * _sr, dxp * _sr + dyp * _cr
        tm = math.hypot(tx, ty) or 1.0; Ta = (tx / tm, ty / tm)
        P0 = b_out[-1]
        span_ = math.hypot(Pa[0] - P0[0], Pa[1] - P0[1])
        neck = bez(P0,
                   (P0[0] - span_ * 0.62, P0[1] - span_ * 0.16),
                   (Pa[0] - Ta[0] * span_ * 0.40, Pa[1] - Ta[1] * span_ * 0.40),
                   Pa, n=60)
        sweep = 2 * math.pi - (math.radians(G_LOOP_OUT) - math.radians(G_LOOP_IN))
        rnd = [L(math.radians(G_LOOP_OUT) + sweep * i / 300.0) for i in range(301)]
        two = b_out + neck[1:] + rnd[1:]
        w2 = pen_widths(two, floor=S * G_FLOOR * G_LOOP_WALL)
        nb = len(b_out) / len(two)
        def prof2(t):
            if t < nb * 0.12: return 0.42 + (t / (nb * 0.12)) * 0.58     # the entry at the top right
            if t < nb: return 1.0
            u = (t - nb) / max(1e-6, 1 - nb)
            if u < 0.22: return 1.0 - (1.0 - G_NECK_THIN) * (u / 0.22)   # thinning into the loop
            if u < 0.34: return G_NECK_THIN + (1.0 - G_NECK_THIN) * ((u - 0.22) / 0.12)
            return 1.0 - 0.30 * max(0.0, (u - 0.86) / 0.14)              # the loop runs out
        s_two = stroke(two, lambda t: w2(t) * prof2(t) * G_LOOP_WALL, raw=True, pieces=True)
        return geom.ink([s_one, s_two])
