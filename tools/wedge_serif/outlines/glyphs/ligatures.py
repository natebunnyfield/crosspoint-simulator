"""fi fl ff ffi ffl (round 96, owner 2026-09-14: "proceed with ligatures").
Measured first: no f-pair collides in Albo (min row gap fi 162, fl 150, ff
152 against n+n 102), so these are the stylistic ligatures a text face
carries, not collision fixes. Construction, each on the f's own parts
(`stems.f_ink`): the hook re-aimed so it ENDS as the i's dot over the i's
stem (the dot is dropped); into the l's top-left wedge; the first f of ff
buried in the second f's stem with one continuous bar. The reader reaches
them by cmap (U+FB00-FB04) and a `liga` feature (`outlines/kern.py`)."""
import shapely.affinity as aff
from . import glyph
from .. import geom
from ..primitives import stem, dot
from ..pen import S, XH, ASC, TH_H, adj
from .stems import f_ink, f_geometry, dot_y, DOT_R, DOT_R_ADJ

FI_PUSH = 0.35    # the i's stem centre sits this many stems RIGHT of the hook's free end (first cut at -0.15 piled the hook into the stem top)
FL_PUSH = 0.40
FF_STEP = 1.38    # the second f's stem centre, in hook radii past the first (the natural pair is ~1.47; 1.02 was cramped)

def _i_stem(x, c):
    return stem(x, 0, c["xh"], top='left', foot='both')
def _l_stem(x, c):
    if adj('l'): return stem(x, 0, c["asc"], top='left', foot='both', top_len=1.05, foot_len=0.92)
    return stem(x, 0, c["asc"], top='left', foot='both')

def fi_parts(c, x_f_shift=0.0):
    """f + i fused: the hook comes over and flows INTO the i's dot, arriving
    on a diagonal (a vertical arrival takes the pen's full stem weight and
    read as the stem climbing into a knot -- the first cut)."""
    x, r, _ = f_geometry(c); x += x_f_shift
    dr = DOT_R_ADJ if adj('i') else DOT_R
    ix = x + r * 1.25 + S * FI_PUSH
    dy = dot_y(c["xh"])
    end = (ix - dr * 0.55, dy + dr * 0.55)                     # the dot's upper-left shoulder
    c2 = (x + r * 1.25, c["asc"] - r * 0.15)                   # over the crown, then down at ~50 degrees
    prof = [(0.0, 1.0), (0.6, 1.0), (1.0, 0.9)]
    f = f_ink(c, hook_end=end, hook_c2=c2, hook_profile=prof, parts=True, hook_cut=False)
    return f + [_i_stem(ix, c), dot(ix, dy, dr)]

def fl_parts(c, x_f_shift=0.0):
    """f + l: the hook rises into the l's top-left wedge."""
    x, r, _ = f_geometry(c); x += x_f_shift
    lx = x + r * 1.25 + S * FL_PUSH
    end = (lx - S * 0.45, c["asc"] - 8)                        # inside the wedge's bracket
    c2 = (x + r * 1.1, c["asc"] + 8)
    prof = [(0.0, 1.0), (0.7, 1.0), (1.0, 1.05)]
    f = f_ink(c, hook_end=end, hook_c2=c2, hook_profile=prof, parts=True, hook_cut=False)
    return f + [_l_stem(lx, c)]

def ff_first(c):
    """The first f of ff: its hook shortened into the second f's stem; its
    bar reaches the second bar so the two read as one."""
    x, r, bar_r = f_geometry(c); x2 = x + r * FF_STEP
    end = (x2 + S * 0.2, c["asc"] - r * 0.40)
    c2 = (x + r * 1.0, c["asc"] + 8)
    f = f_ink(c, hook_end=end, hook_c2=c2, hook_profile=[(0.0, 1.0), (1.0, 1.0)], parts=True, hook_cut=False)
    return f, x2 - x

# ROUND 266 -- THE BARS MUST MEET AT ANY WEIGHT. The f-ligatures read as one
# letter because the first f's bar overlaps the second's; that overlap was
# tuned at stem 84 and is sized in S, while the stems are placed on the
# x-height grid, which is not. So at the 400's stem of 66.9 the bars part and
# the ffi shipped as THREE ink islands (measured: 44-409, 290-658, 528-702
# where at 84 it is one, 44-748). `_bridge` closes any gap the weight opens,
# in the bars' own y band and at their own thickness, and does nothing at all
# when they already touch -- so the drawing at 84 is untouched.
def _bridge(bar_a, bar_b):
    """The connector between two f-bars, or None when they already touch. The
    bars are the same band of y, so the join is a rectangle across the x gap
    at their own shared height -- nothing is widened and nothing moves."""
    import shapely.geometry as _sg
    if bar_a.is_empty or bar_b.is_empty or bar_a.intersects(bar_b):
        return None
    ax0, ay0, ax1, ay1 = bar_a.bounds; bx0, by0, bx1, by1 = bar_b.bounds
    if bx0 <= ax1:
        return None
    lo, hi = max(ay0, by0), min(ay1, by1)
    if hi <= lo:
        return None
    return _sg.box(ax1 - 0.5, lo, bx0 + 0.5, hi)


@glyph('\ufb01')
def g_fi(c): return geom.ink(fi_parts(c))
@glyph('\ufb02')
def g_fl(c): return geom.ink(fl_parts(c))
@glyph('\ufb00')
def g_ff(c):
    first, dx = ff_first(c); second = [aff.translate(g, dx, 0) for g in f_ink(c, parts=True)]
    j = _bridge(first[2], second[2])
    return geom.ink(first + second + ([j] if j is not None else []))
@glyph('\ufb03')
def g_ffi(c):
    first, dx = ff_first(c); rest = [aff.translate(g, dx, 0) for g in fi_parts(c)]
    j = _bridge(first[2], rest[2])
    return geom.ink(first + rest + ([j] if j is not None else []))
@glyph('\ufb04')
def g_ffl(c):
    first, dx = ff_first(c); rest = [aff.translate(g, dx, 0) for g in fl_parts(c)]
    j = _bridge(first[2], rest[2])
    return geom.ink(first + rest + ([j] if j is not None else []))
