"""The diacritics, drawn on the pen (round 99, 2026-09-14).

Why they exist: the reader's `reading` interval asks for U+0020-024F, and
every codepoint Albo does not draw is supplied by Noto at build time -- so
"cafe" with an acute, "naive" with a dieresis and every German, French,
Spanish, Polish or Czech word in a book came out with one letter from
another typeface. This module draws the marks; `build.ACCENTED` composes
them onto the bases as TrueType composites, so an accented letter IS its
letter plus its mark, never a redrawn approximation that can drift.

Each mark is drawn with its own ink starting at x = 0 and, for an
ABOVE mark, its bottom on y = 0; a BELOW mark hangs from y = 0. The
composite places it: `build.place_accent` centres it on the base's ink and
lifts it to the x-height or the cap line. So nothing here knows about a
base, and the same mark serves the lowercase and the capitals.

Sizes are the pen's, not invented: the strokes take `pen.th()` at their own
angle exactly as a letter's do, the dots are the family's `DOT_R`, the
macron is the pen's horizontal, and the ring is a bowl.
"""
import math
from . import glyph
from .. import geom, pen
from ..geom import cubic, line
from ..primitives import stroke, pen_widths, widths, dot, ring, bar
from ..pen import S, XH, CAP, ASC, TH_V, TH_H, HAIR, CUT, BOWL_K
from .stems import DOT_R, dot_y

# The family's accent box. Width and height are the proportions a garalde
# gives an acute: about a third of the x-height tall and two fifths wide.
ACC_H = 0.26 * XH          # 112 at xh 429
ACC_W = 0.38 * XH          # 163
ACC_LIGHT = 0.86           # the marks' strokes, x the pen (a mark is lighter than a stem)

def _stroke(pts, prof=None, cut0=CUT, cut1=CUT, light=ACC_LIGHT):
    return stroke(pts, pen_widths(pts, (prof or (lambda t: 1.0)), scale=light), cut0=cut0, cut1=cut1)

@glyph('´')      # acute
def g_acute(c):
    return _stroke(line((0, 0), (ACC_W, ACC_H)))

@glyph('`')      # grave
def g_grave(c):
    return _stroke(line((0, ACC_H), (ACC_W, 0)))

@glyph('ˆ')      # circumflex
def g_circumflex(c):
    left = _stroke(line((0, 0), (ACC_W / 2, ACC_H)), cut1=None)
    right = _stroke(line((ACC_W / 2, ACC_H), (ACC_W, 0)), cut0=None)
    return geom.ink([left, right])

@glyph('ˇ')      # caron
def g_caron(c):
    left = _stroke(line((0, ACC_H), (ACC_W / 2, 0)), cut1=None)
    right = _stroke(line((ACC_W / 2, 0), (ACC_W, ACC_H)), cut0=None)
    return geom.ink([left, right])

@glyph('˜')      # tilde
def g_tilde(c):
    """A wave: up out of the left, over, down into the right. Thin at the
    ends as a pen stroke turning through the horizontal is."""
    p = cubic((0, ACC_H * 0.30), (ACC_W * 0.28, ACC_H * 1.15), (ACC_W * 0.60, -ACC_H * 0.18), (ACC_W, ACC_H * 0.72))
    return _stroke(p, widths([(0.0, 0.62), (0.5, 1.0), (1.0, 0.62)]))

@glyph('¯')      # macron
def g_macron(c):
    return bar(0, ACC_W * 1.04, TH_H * ACC_LIGHT / 2, TH_H * ACC_LIGHT)

@glyph('˘')      # breve
def g_breve(c):
    """A cup: heavier at the bottom of the turn, the two ends cut."""
    p = cubic((0, ACC_H), (ACC_W * 0.12, -ACC_H * 0.16), (ACC_W * 0.88, -ACC_H * 0.16), (ACC_W, ACC_H))
    return _stroke(p, widths([(0.0, 0.70), (0.5, 1.12), (1.0, 0.70)]))

@glyph('¨')      # dieresis
def g_dieresis(c):
    r = DOT_R * 0.92
    return geom.ink([dot(r, r, r), dot(ACC_W - r, r, r)])

@glyph('˙')      # dot above
def g_dotaccent(c):
    r = DOT_R * 0.92
    return dot(r, r, r)

@glyph('˚')      # ring above
def g_ring(c):
    """A small bowl, its counter open enough to survive 13 pt: the ring is
    the family's, at a radius that makes the mark ACC_H*1.25 tall."""
    ry = ACC_H * 0.62; rx = ry * 1.02
    solid, *_ = ring(rx, ry, rx, ry, k=BOWL_K, w_scale=0.62, floor=HAIR * 0.9)
    return solid

@glyph('˝')      # double acute
def g_hungarumlaut(c):
    a = _stroke(line((0, 0), (ACC_W * 0.58, ACC_H)))
    b = _stroke(line((ACC_W * 0.52, 0), (ACC_W * 1.10, ACC_H)))
    return geom.ink([a, b])

@glyph('¸')      # cedilla (hangs below; drawn from y = 0 down)
def g_cedilla(c):
    """A hook leaving the letter's foot, turning left and closing. Its top
    overlaps into the base by a hair so the two read as one stroke."""
    d = 0.30 * XH
    p = cubic((ACC_W * 0.46, 8), (ACC_W * 0.46, -d * 0.42), (ACC_W * 0.86, -d * 0.40), (ACC_W * 0.70, -d * 0.78))
    q = cubic((ACC_W * 0.70, -d * 0.78), (ACC_W * 0.52, -d * 1.10), (ACC_W * 0.16, -d * 0.86), (ACC_W * 0.10, -d * 0.60))
    return geom.ink([_stroke(p, widths([(0.0, 0.92), (1.0, 0.72)]), cut0=None, cut1=None),
                     _stroke(q, widths([(0.0, 0.72), (1.0, 0.46)]), cut0=None)])

@glyph('˛')      # ogonek (hangs below)
def g_ogonek(c):
    d = 0.28 * XH
    p = cubic((ACC_W * 0.30, 8), (ACC_W * 0.30, -d * 0.55), (ACC_W * 0.86, -d * 0.55), (ACC_W * 0.78, -d * 1.02))
    return _stroke(p, widths([(0.0, 0.88), (1.0, 0.44)]), cut0=None)

# The caron of d t l and L: Czech and Slovak set it as an apostrophe at the
# letter's right shoulder, not as a wedge over the ascender. Drawn as its
# own mark so the composite table can name it.
@glyph('ʹ')      # (spacing modifier prime, borrowed as the caron.alt slot)
def g_caronalt(c):
    w = S * 0.34
    p = line((w / 2, 0), (w / 2 - S * 0.10, ACC_H * 1.22))
    return _stroke(p, widths([(0.0, 0.60), (1.0, 1.05)]), cut0=CUT)

# Dotless bases: í ì î ï and every accented i are the i WITHOUT its dot.
@glyph('ı')      # dotless i
def g_dotlessi(c):
    from ..primitives import stem
    return stem(S / 2, 0, c["xh"], top='left', foot='both')

@glyph('ȷ')      # dotless j
def g_dotlessj(c):
    from .stems import g_j
    from .. import geom as _g
    import shapely.geometry as _sg
    full = g_j(c)
    # the dot is the small disjoint piece; keep everything else
    parts = list(full.geoms) if hasattr(full, 'geoms') else [full]
    if len(parts) > 1:
        parts = sorted(parts, key=lambda p: -p.area)[:-1]
        return _g.ink(parts)
    return full
