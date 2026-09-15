"""THE ALDINE LOWERCASE, drawn again from nothing (round 115).

Owner, three times, the last plainly: *"remake lowercase italic from scratch to
match the scan. I cannot be clearer, stop ignoring this instruction."* Rounds
114 and 114b answered by turning dials on the existing italic -- width,
contrast, serif size, the flick's tip, where the arch branches -- and a dial
cannot change what a letter IS. This module draws the lowercase from Griffo's
1501 shapes instead of adjusting a sheared roman toward them.

Registered ONLY under ALBO_ALDINE=1, so the shipping italic is untouched while
this is judged, and both can be built for the same page.

WHAT THE SCAN SHOWS, and what each of these is built from:

  THE HEAD    an ascender does not end in a flick. It ends in a flat angled
              head that sits ACROSS the stem, entered from the left. That one
              shape is most of the page's texture, because b d h k l are
              everywhere in Latin.
  THE ARCH    branches LOW -- around a third of the way up the stem -- climbs,
              and arches over. It is one movement, not a shoulder turned near
              the top.
  THE FOOT    a short blunt outstroke to the right, with weight in it.
  THE BOWLS   small, round and sitting LOW in the x-height band, not filling
              it. The a is single-storey with its bowl low against a nearly
              straight stem.
  THE e       a small eye under a bar that slants up hard.

Everything is drawn on the pen, so the contrast is the pen's own; no widths
are declared except where a stroke has to thin against its neighbour.
"""
import math, os
from . import glyph
from .. import geom, pen
from ..geom import cubic, line, catmull, superellipse
from ..primitives import stroke, pen_widths, widths, ring
from .. import primitives as PR
from ..pen import S, XH, ASC, DESC, OVER, TH_V, TH_H, CUT, BOWL_K

ON = os.environ.get("ALBO_ALDINE") == "1"

HEAD_DEG = float(os.environ.get("ALBO_ALD_HEAD_DEG", 24.0))   # the head's slant
HEAD_LEN = float(os.environ.get("ALBO_ALD_HEAD_LEN", 1.15))   # its length, x the stem
HEAD_W = float(os.environ.get("ALBO_ALD_HEAD_W", 0.58))       # its weight, x the stem
FOOT_LEN = float(os.environ.get("ALBO_ALD_FOOT", 0.80))       # the foot's outstroke
BRANCH = float(os.environ.get("ALBO_ALD_BRANCH", 0.34))       # where an arch leaves the stem, x xh
BOWL_TOP = float(os.environ.get("ALBO_ALD_BOWL_TOP", 0.98))   # a bowl's top, x xh -- they sit LOW
FLOOR = float(os.environ.get("ALBO_ALD_FLOOR", 0.30))         # the pen's floor, x the stem


def _w(c):
    return c["wf"]


def st(x, y0, y1, head=False, foot=True, w=1.0):
    """A stem. `head` puts the Aldine angled head across its top; `foot` the
    blunt outstroke to the right at the baseline."""
    parts = [stroke([(x, y0), (x, y1)], S * w)]
    if head:
        a = math.radians(HEAD_DEG); L = S * HEAD_LEN
        dx, dy = math.cos(a) * L, math.sin(a) * L
        p0 = (x - dx * 0.74, y1 - dy * 0.74 - S * 0.06)
        p1 = (x + dx * 0.36, y1 + dy * 0.36 - S * 0.02)
        parts.append(stroke([p0, p1], S * HEAD_W, cut0=CUT))
    if foot:
        L = S * FOOT_LEN
        parts.append(stroke(cubic((x - S * w * 0.42, y0 + S * 0.30),
                                  (x - S * w * 0.10, y0 + S * 0.02),
                                  (x + L * 0.42, y0 + S * 0.02),
                                  (x + L, y0 + L * 0.46)),
                            widths([(0.0, S * w * 0.92), (0.5, S * 0.42), (1.0, S * 0.30)])))
    return parts


def arch(c, x0, x1, land=0.74):
    """Branches low off the left stem, climbs, arches over, lands on the right
    one. ONE movement -- the thing a sheared roman cannot do."""
    xh = c["xh"]; ov = pen.ARCH_OVER
    p = cubic((x0, xh * BRANCH),
              (x0 + (x1 - x0) * 0.06, xh * 0.88),
              (x0 + (x1 - x0) * 0.52, xh + ov),
              (x1, xh * land))
    wf = pen_widths(p, floor=S * FLOOR)
    return stroke(p, lambda t: wf(t) * (0.62 + 0.38 * min(1.0, t / 0.34)))


def bowl(c, cx, rx, top=None, ry=None):
    """A small round bowl sitting LOW in the x-height band."""
    xh = c["xh"]; top = (top if top is not None else BOWL_TOP) * xh
    ry = ry if ry is not None else top / 2
    return ring(cx, top - ry, rx, ry + OVER * 0.5, floor=S * FLOOR)[0]


if ON:
    @glyph('i')
    def a_i(c):
        x = S * 1.0
        return geom.ink(st(x, 0, c["xh"], head=True) + [PR.dot(x + S * 0.30, c["xh"] + S * 1.35, S * 0.52)])

    @glyph('l')
    def a_l(c):
        return geom.ink(st(S * 1.0, 0, c["asc"], head=True))

    @glyph('n')
    def a_n(c):
        xh = c["xh"]; x0 = S * 1.0; x1 = x0 + 268 * _w(c)
        return geom.ink(st(x0, 0, xh, head=False) + [arch(c, x0, x1)] + st(x1, 0, xh * 0.74, foot=True))

    @glyph('m')
    def a_m(c):
        xh = c["xh"]; x0 = S * 1.0; d = 250 * _w(c); x1 = x0 + d; x2 = x1 + d
        return geom.ink(st(x0, 0, xh, head=False) + [arch(c, x0, x1), arch(c, x1, x2)]
                        + st(x1, 0, xh * 0.74, foot=False) + st(x2, 0, xh * 0.74))

    @glyph('h')
    def a_h(c):
        xh = c["xh"]; x0 = S * 1.0; x1 = x0 + 268 * _w(c)
        return geom.ink(st(x0, 0, c["asc"], head=True) + [arch(c, x0, x1)] + st(x1, 0, xh * 0.74))

    @glyph('u')
    def a_u(c):
        """The arch inverted: it branches low off the RIGHT stem going back."""
        xh = c["xh"]; ov = pen.ARCH_OVER; x0 = S * 1.0; x1 = x0 + 268 * _w(c)
        p = cubic((x1, xh * (1 - BRANCH)), (x1 - (x1 - x0) * 0.06, xh * 0.12),
                  (x0 + (x1 - x0) * 0.48, -ov), (x0, xh * 0.26))
        wf = pen_widths(p, floor=S * FLOOR)
        return geom.ink(st(x0, xh * 0.26, xh, head=False, foot=False)
                        + [stroke(p, lambda t: wf(t) * (0.66 + 0.34 * min(1.0, t / 0.3)))]
                        + st(x1, 0, xh, head=False))

    @glyph('r')
    def a_r(c):
        xh = c["xh"]; x0 = S * 1.0
        p = cubic((x0, xh * BRANCH), (x0 + 26 * _w(c), xh * 0.90),
                  (x0 + 96 * _w(c), xh + pen.ARCH_OVER), (x0 + 182 * _w(c), xh * 0.86))
        wf = pen_widths(p, floor=S * FLOOR)
        return geom.ink(st(x0, 0, xh, head=False)
                        + [stroke(p, lambda t: wf(t) * (0.60 + 0.40 * min(1.0, t / 0.35)), cut1=CUT)])

    @glyph('o')
    def a_o(c):
        return geom.ink([bowl(c, S * 0.6 + 145 * _w(c), 145 * _w(c), top=1.0)])

    @glyph('c')
    def a_c(c):
        xh = c["xh"]; rx = 140 * _w(c); cx = S * 0.6 + rx
        p = superellipse(cx, xh / 2, rx, xh / 2 + OVER * 0.5, math.radians(38), math.radians(322), BOWL_K)
        wf = pen_widths(p, floor=S * FLOOR)
        return geom.ink([stroke(p, wf, cut0=CUT, cut1=CUT)])

    @glyph('e')
    def a_e(c):
        """A small eye under a bar that slants up hard."""
        xh = c["xh"]; rx = 142 * _w(c); cx = S * 0.6 + rx
        p = superellipse(cx, xh / 2, rx, xh / 2 + OVER * 0.5, math.radians(30), math.radians(318), BOWL_K)
        wf = pen_widths(p, floor=S * FLOOR)
        ring_ = stroke(p, wf, cut0=CUT, cut1=CUT)
        sl = math.tan(math.radians(17.0))
        y = xh * 0.56
        bar = stroke([(cx - rx * 0.92, y - rx * 0.92 * sl), (cx + rx * 0.86, y + rx * 0.86 * sl)], TH_H * 0.92)
        return geom.ink([ring_, bar])

    # MEASURED off aldine.png, the 'a' of "Formoſam" at x 222-238, y 28-47,
    # after the owner named the shape: "look for characters that are like 'd'
    # with a short ascender". That is exactly what it is, and it is NOT what
    # this module drew first. Griffo's a is a SMALL bowl sitting LOW in the
    # x-height with the stem CARRYING ON ABOVE IT -- a d whose ascender has
    # been cut short. The first cut here filled the whole x-height with the
    # bowl and stopped the stem at the x-height line, which is a different
    # letter.
    A_BW = float(os.environ.get("ALBO_ALD_A_BW", 0.62))    # the bowl's width, x xh
    A_BH = float(os.environ.get("ALBO_ALD_A_BH", 0.84))    # its height, x xh -- it sits LOW
    A_RISE = float(os.environ.get("ALBO_ALD_A_RISE", 0.22))# how far the stem rises above the bowl, x xh
    A_HEAD = float(os.environ.get("ALBO_ALD_A_HEAD", 0.72))# the little head on that short ascender

    @glyph('a')
    def a_a(c):
        """A d with a short ascender: a small low bowl, and a stem that carries
        on above it."""
        xh = c["xh"]
        bw = A_BW * xh; bh = A_BH * xh
        rx = bw / 2; ry = bh / 2
        cx = S * 0.60 + rx; cy = ry - OVER * 0.3       # the bowl sits on the baseline
        x1 = cx + rx - TH_V * 0.10                      # the stem, on the bowl's right
        top = bh + A_RISE * xh                          # and it rises ABOVE the bowl
        bowl_ = ring(cx, cy, rx, ry + OVER * 0.4, floor=S * FLOOR)[0]
        parts = [bowl_] + st(x1, 0, top, head=False, foot=True)
        if A_HEAD:
            L = S * A_HEAD; a = math.radians(HEAD_DEG)
            dx, dy = math.cos(a) * L, math.sin(a) * L
            parts.append(stroke([(x1 - dx * 0.70, top - dy * 0.70 - S * 0.05),
                                 (x1 + dx * 0.34, top + dy * 0.34)], S * HEAD_W * 0.92, cut0=CUT))
        return geom.ink(parts)

    @glyph('b')
    def a_b(c):
        xh = c["xh"]; x0 = S * 1.0; rx = 142 * _w(c)
        return geom.ink(st(x0, 0, c["asc"], head=True, foot=False)
                        + [bowl(c, x0 + rx * 0.86, rx, top=BOWL_TOP)])

    @glyph('d')
    def a_d(c):
        xh = c["xh"]; rx = 142 * _w(c); x1 = S * 0.6 + rx * 1.78
        return geom.ink([bowl(c, S * 0.6 + rx, rx, top=BOWL_TOP)] + st(x1, 0, c["asc"], head=True))

    @glyph('p')
    def a_p(c):
        x0 = S * 1.0; rx = 142 * _w(c)
        return geom.ink(st(x0, -c["desc"], c["xh"], head=False, foot=False)
                        + [bowl(c, x0 + rx * 0.86, rx, top=BOWL_TOP)])

    @glyph('q')
    def a_q(c):
        rx = 142 * _w(c); x1 = S * 0.6 + rx * 1.78
        return geom.ink([bowl(c, S * 0.6 + rx, rx, top=BOWL_TOP)]
                        + st(x1, -c["desc"], c["xh"], head=False))

    @glyph('f')
    def a_f(c):
        """Tall, hooked head, and it descends -- as it does on the page."""
        xh = c["xh"]; asc = c["asc"]; x = S * 1.4
        p = cubic((x - S * 0.10, -c["desc"] * 0.52), (x - S * 0.02, xh * 0.5),
                  (x + S * 0.06, asc * 0.94), (x + S * 1.15, asc * 1.02))
        wf = pen_widths(p, floor=S * FLOOR)
        bar = stroke([(x - S * 0.95, xh * 0.94), (x + S * 1.00, xh * 0.94)], TH_H * 0.90)
        return geom.ink([stroke(p, lambda t: wf(t) * (1.0 - 0.42 * max(0.0, (t - 0.72) / 0.28)), cut1=CUT), bar])

    @glyph('t')
    def a_t(c):
        xh = c["xh"]; x = S * 1.0
        p = cubic((x, xh * 1.30), (x, xh * 0.34), (x + S * 0.30, S * 0.08), (x + S * 1.20, S * 0.62))
        wf = pen_widths(p, floor=S * FLOOR)
        bar = stroke([(x - S * 0.80, xh * 0.92), (x + S * 0.86, xh * 0.92)], TH_H * 0.88)
        return geom.ink([stroke(p, wf, cut1=CUT), bar])

    @glyph('j')
    def a_j(c):
        x = S * 1.0
        p = cubic((x, c["xh"]), (x, -c["desc"] * 0.36), (x - S * 0.55, -c["desc"] * 0.92), (x - S * 1.50, -c["desc"] * 0.70))
        wf = pen_widths(p, floor=S * FLOOR)
        return geom.ink([stroke(p, lambda t: wf(t) * (1.0 - 0.45 * max(0.0, (t - 0.6) / 0.4)), cut1=CUT),
                         PR.dot(x + S * 0.30, c["xh"] + S * 1.35, S * 0.52)])

    @glyph('s')
    def a_s(c):
        xh = c["xh"]; x = S * 0.7; w = 182 * _w(c)
        p = catmull([(x + w * 0.92, xh * 0.86), (x + w * 0.20, xh * 0.98), (x + w * 0.10, xh * 0.62),
                     (x + w * 0.86, xh * 0.40), (x + w * 0.94, xh * 0.08), (x + w * 0.16, xh * 0.14)], tension=0.5)
        wf = pen_widths(p, floor=S * FLOOR)
        return geom.ink([stroke(p, wf, cut0=CUT, cut1=CUT)])

    @glyph('g')
    def a_g(c):
        """Two storeys, both small -- the page's g is a quiet letter."""
        xh = c["xh"]; rx = 138 * _w(c); cx = S * 0.6 + rx
        up = bowl(c, cx, rx, top=BOWL_TOP)
        lo = ring(cx - rx * 0.16, -c["desc"] * 0.48, rx * 0.96, c["desc"] * 0.40, floor=S * FLOOR)[0]
        nk = stroke(cubic((cx + rx * 0.78, xh * 0.20), (cx + rx * 0.58, -c["desc"] * 0.04),
                          (cx + rx * 0.30, -c["desc"] * 0.10), (cx + rx * 0.72, -c["desc"] * 0.08)),
                    widths([(0.0, S * 0.66), (0.5, S * 0.34), (1.0, S * 0.60)]))
        return geom.ink([up, lo, nk])

    def _diag(p0, p1, w0, w1):
        return stroke([p0, p1], widths([(0.0, S * w0), (1.0, S * w1)]), cut0=CUT, cut1=CUT)

    @glyph('v')
    def a_v(c):
        xh = c["xh"]; x = S * 0.7; w = 200 * _w(c)
        return geom.ink([_diag((x, xh), (x + w * 0.52, 0), 0.96, 0.34),
                         _diag((x + w * 0.52, 0), (x + w, xh), 0.34, 0.52)])

    @glyph('w')
    def a_w(c):
        xh = c["xh"]; x = S * 0.7; w = 182 * _w(c)
        P = []
        for k in (0, 1):
            o = x + k * w * 1.06
            P += [_diag((o, xh), (o + w * 0.52, 0), 0.94, 0.34),
                  _diag((o + w * 0.52, 0), (o + w * 1.04, xh), 0.34, 0.50)]
        return geom.ink(P)

    @glyph('x')
    def a_x(c):
        xh = c["xh"]; x = S * 0.7; w = 190 * _w(c)
        return geom.ink([_diag((x, xh), (x + w, 0), 0.92, 0.40),
                         _diag((x, 0), (x + w, xh), 0.40, 0.40)])

    @glyph('y')
    def a_y(c):
        xh = c["xh"]; x = S * 0.7; w = 190 * _w(c)
        tail = cubic((x + w, xh), (x + w * 0.52, -c["desc"] * 0.42),
                     (x + w * 0.10, -c["desc"] * 0.86), (x - S * 0.70, -c["desc"] * 0.62))
        wf = pen_widths(tail, floor=S * FLOOR)
        return geom.ink([_diag((x, xh), (x + w * 0.54, 0), 0.94, 0.36),
                         stroke(tail, lambda t: wf(t) * (0.9 - 0.45 * max(0.0, (t - 0.55) / 0.45)), cut1=CUT)])

    @glyph('z')
    def a_z(c):
        xh = c["xh"]; x = S * 0.7; w = 182 * _w(c)
        return geom.ink([stroke([(x, xh * 0.94), (x + w, xh * 0.94)], TH_H * 0.95, cut0=CUT, cut1=CUT),
                         _diag((x + w * 0.94, xh * 0.94), (x + S * 0.10, TH_H * 0.5), 0.86, 0.86),
                         stroke([(x, 0), (x + w, 0)], TH_H * 0.95, cut0=CUT, cut1=CUT)])

    @glyph('k')
    def a_k(c):
        xh = c["xh"]; x0 = S * 1.0; r = 182 * _w(c)
        arm = _diag((x0 + r, xh), (x0 + S * 0.16, xh * 0.42), 0.40, 0.64)
        leg = _diag((x0 + S * 0.22, xh * 0.46), (x0 + r * 0.98, 0), 0.62, 0.86)
        return geom.ink(st(x0, 0, c["asc"], head=True) + [arm, leg])
