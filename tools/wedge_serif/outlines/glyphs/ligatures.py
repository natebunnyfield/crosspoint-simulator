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
from .stems import f_ink, f_geometry, dot_y, DOT_R, DOT_R_ADJ, TIT_R, TIT_R_ADJ

import os as _os
# ROUND 292 -- HOW TIGHT AN f-LIGATURE MAY SET. Owner 2026-09-20: *"update
# spacing, the fl ffl and fi ligatures are too close."* Measured on the built
# fonts as the ligature's advance against the same letters set apart, which is
# what "too close" means here: at the Regular the fl set 14.2% tighter, the fi
# 16.0, the ffl 18.6 and the ffi 19.7, and the Bold ran 16.8 / 18.5 / 23.8 /
# 24.9. The italic, which he did NOT complain about, sets 0 to 11.5% tighter,
# so the italic is the reference for how much a ligature here should save.
FI_PUSH = float(_os.environ.get("ALBO_FI_PUSH", 0.35))   # the i's stem centre, this many stems RIGHT of the hook's free end (first cut at -0.15 piled the hook into the stem top)
FL_PUSH = float(_os.environ.get("ALBO_FL_PUSH", 0.40))
FF_STEP = float(_os.environ.get("ALBO_FF_STEP", 1.38))   # the second f's stem centre, in hook radii past the first (the natural pair is ~1.47; 1.02 was cramped)

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
    dr = TIT_R_ADJ if adj('i') else TIT_R
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
    # ROUND 267 -- at the 200 the first hook's tip only kissed the second
    # hook's edge (PINCH, 2.2 units at 379, 712): its end is S x 0.2 past the
    # second stem, an overlap sized in the stem, and at 43.8 that is 8.8
    # units. Under the 400's stem the tip goes further in and higher, into
    # the second hook's body; at 66.9 and above the end is exactly as it was.
    if S < 66.0:
        end = (x2 + S * 0.45, c["asc"] - r * 0.30)
    else:
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


# ============================ ROUND 309 -- MORE, AND ROMAN ONLY ============
# Owner 2026-09-21: *"remove italic ligatures. take pass at adding other
# ligatures to roman"*. The italic's `liga` feature is gone (outlines/kern.py);
# what follows is drawn for the ROMAN and is inert in the italic, whose own
# module registers its own letters.
#
# The four f-ligatures below are the fl construction with a different second
# letter: the f's hook is re-aimed so it ENDS inside the next letter's
# top-left wedge, and the letter is then set where the l would have stood. The
# face already admits the clash they cure -- `kern.py` carries an f+ascender
# cell of +54 opened in round 96b precisely because the hook lands on b h k l.
# A ligature is the other answer to that, and it is the one a text face makes.
#
# The `st` is a different animal and it is the one worth judging hardest: it
# joins two letters that do not collide at all, purely because a garalde is
# expected to have one. Its arc runs from the s's top terminal to the t's
# ascender at the t's own bar height -- not over the top, which is the
# nineteenth-century version and reads as decoration in a reading face.
#
# Codepoints: the standard slots are full at FB00-FB04, so the f-family takes
# the PUA (E000-E003) and the st its own standard slot, U+FB06. The reader's
# .cpfont carries FB00-FB06 or PUA, so all six reach the device.
from . import GLYPHS as _G

def _place(ch, c, x_left):
    """The letter `ch` drawn by its own glyph function, moved so its leftmost
    ink sits at x_left. Composing from the registry rather than redrawing is
    what keeps a ligature's second half identical to the letter it replaces."""
    g = _G[ch](c)
    return aff.translate(g, x_left - geom.bbox(g)[0], 0)

def _f_into_ascender(c, ch, push=None):
    """f + an ascending letter: the hook ends inside that letter's top-left
    wedge, exactly as it does for the l."""
    x, r, _ = f_geometry(c)
    lx = x + r * 1.25 + S * (FL_PUSH if push is None else push)
    end = (lx - S * 0.45, c["asc"] - 8)
    c2 = (x + r * 1.1, c["asc"] + 8)
    f = f_ink(c, hook_end=end, hook_c2=c2, hook_profile=[(0.0, 1.0), (0.7, 1.0), (1.0, 1.05)],
              parts=True, hook_cut=False)
    # the l's stem would stand with its own left edge here; the letter follows it
    ref = geom.bbox(_l_stem(lx, c))[0]
    return f + [_place(ch, c, ref)]

@glyph('\ue000')
def g_fb(c): return geom.ink(_f_into_ascender(c, 'b'))
@glyph('\ue001')
def g_fh(c): return geom.ink(_f_into_ascender(c, 'h'))
@glyph('\ue003')
def g_fk(c): return geom.ink(_f_into_ascender(c, 'k'))

@glyph('\ue002')
def g_fj(c):
    """f + j: the j's dot is the one the hook flows into, as the i's is."""
    x, r, _ = f_geometry(c)
    jx = x + r * 1.25 + S * FI_PUSH
    dr = TIT_R_ADJ if adj('j') else TIT_R
    dy = dot_y(c["xh"])
    end = (jx - dr * 0.55, dy + dr * 0.55)
    c2 = (x + r * 1.25, c["asc"] - r * 0.15)
    f = f_ink(c, hook_end=end, hook_c2=c2, hook_profile=[(0.0, 1.0), (0.6, 1.0), (1.0, 0.9)],
              parts=True, hook_cut=False)
    j = _G['j'](c)
    # The j carries its own dot and the hook arrives as one, so the dot goes.
    # Pick it by POSITION and SIZE, not by area alone: the first cut took
    # `max(area)` and kept whichever island happened to be largest, which on
    # this j is the descender -- the ligature then set an f beside a shape
    # that read as a capital J.
    parts = list(getattr(j, 'geoms', [j]))
    def _is_dot(g):
        x0, y0, x1, y1 = geom.bbox(g)
        return y0 > c["xh"] * 0.80 and (x1 - x0) < S * 1.6
    body = [g for g in parts if not _is_dot(g)]
    if not body: body = parts
    import shapely.ops as _ops
    body = _ops.unary_union(body)
    body = aff.translate(body, jx - geom.bbox(body)[0] - S * 0.1, 0)
    return geom.ink(f + [body, dot(jx, dy, dr)])

ST_ARC_H = float(_os.environ.get("ALBO_ST_ARC", 0.92))   # the arc's height, x the x-height
ST_PUSH = float(_os.environ.get("ALBO_ST_PUSH", 0.10))   # the t's left edge, in stems past the s
ST_ARC_TOP = float(_os.environ.get("ALBO_ST_ARC_TOP", 1.06))  # the arc's crown, x the x-height
ST_ARC_W = float(_os.environ.get("ALBO_ST_ARC_W", 0.78))      # its weight, x the bar

@glyph('\ufb06')
def g_st(c):
    """s + t joined at the t's bar height. The arc leaves the s's top terminal
    and lands on the t's stem; it is drawn at the bar's own weight so the join
    reads as the t's bar continued leftward rather than as a swash."""
    import shapely.geometry as _sg
    s_ = _G['s'](c)
    sx0, sy0, sx1, sy1 = geom.bbox(s_)
    t_ = _place('t', c, sx1 + S * ST_PUSH)
    tx0, ty0, tx1, ty1 = geom.bbox(t_)
    # The join springs from the s's own top terminal and lands on the t's stem
    # just under its bar. The first cut ran it flat at the bar's height and it
    # read as a gap with a hair across it -- an arc has to RISE out of the s or
    # there is nothing to see at 13 px.
    y = c["xh"] * ST_ARC_H
    top = c["xh"] * ST_ARC_TOP
    w = TH_H * ST_ARC_W
    a = _sg.LineString([(sx1 - S * 0.20, y - S * 0.10),
                        (sx1 + S * 0.05, top),
                        ((sx1 + tx0) / 2 + S * 0.10, top),
                        (tx0 + S * 0.45, y - S * 0.05)])
    arc = a.buffer(w / 2, cap_style=2, join_style=1, resolution=16)
    return geom.ink([s_, t_, arc])


# ---- ROUND 309b: MEASURED, AND THE f-FAMILY DOES NOT EARN ITS PLACE --------
# Counted over the owner's own 36 epubs (`tools/wedge_serif/pair_census.py`,
# 2,007,794 letter pairs), which is the only honest way to choose a ligature
# set for a reading device:
#
#     st  23,470      Th   8,589      ct   8,305      sp  3,229
#     ffi    312      ffl     17      fk 6  fb 3  fh 3  fj 1
#
# So `st` alone is seventy-five times commoner than `ffi`, which the face has
# shipped since round 96 -- and the four f-ligatures drawn above it (fb fh fj
# fk) appear THIRTEEN TIMES in two million pairs, six of those in the name
# Kafka. They are drawn, they are behind their own codepoints, and they are
# NOT in the `liga` feature: a ligature nobody's books contain is a glyph to
# maintain forever for nothing.
#
# `ct` and `Th` are the two that follow `st` on the same evidence.
CT_PUSH = float(_os.environ.get("ALBO_CT_PUSH", 0.10))
TH_TUCK = float(_os.environ.get("ALBO_TH_TUCK", 0.34))   # the h, this many stems UNDER the T's arm

@glyph('\ue004')
def g_ct(c):
    """c + t, joined as the st is: the arc springs from the c's upper terminal
    and lands under the t's bar. The c's terminal already reaches to the right,
    so its arc is shorter and flatter than the s's."""
    import shapely.geometry as _sg
    c_ = _G['c'](c)
    cx0, cy0, cx1, cy1 = geom.bbox(c_)
    t_ = _place('t', c, cx1 + S * CT_PUSH)
    tx0, ty0, tx1, ty1 = geom.bbox(t_)
    y = c["xh"] * ST_ARC_H
    top = c["xh"] * (ST_ARC_TOP - 0.02)
    a = _sg.LineString([(cx1 - S * 0.10, y - S * 0.02),
                        (cx1 + S * 0.10, top),
                        ((cx1 + tx0) / 2 + S * 0.10, top),
                        (tx0 + S * 0.45, y - S * 0.05)])
    return geom.ink([c_, t_, a.buffer(TH_H * ST_ARC_W / 2, cap_style=2, join_style=1, resolution=16)])

@glyph('\ue005')
def g_Th(c):
    """T + h: no new stroke at all -- the h simply stands UNDER the T's right
    arm, which is what the pair wants and what a kern cannot give, because a
    kern moves the whole letter and this only wants the overhang used."""
    T_ = _G['T'](c)
    tx0, ty0, tx1, ty1 = geom.bbox(T_)
    h_ = _place('h', c, tx1 - S * TH_TUCK)
    return geom.ink([T_, h_])
