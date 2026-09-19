"""i l j f t a s and the bowl-and-stem letters b d p q, and the g."""
import math, os
import shapely.affinity as aff
from . import glyph
from .. import geom, pen
from ..geom import cubic, line, join, superellipse, catmull
from ..primitives import stem, stem_edge_x, ring, ring_from, stroke, pen_widths, widths, dot, wedge, trap, diagonal, beak, widen_terminal
from .. import primitives as PR
from ..pen import S, XH, ASC, DESC, OVER, TH_V, TH_H, HAIR, CUT, BOWL_K, ENT, WL, WD, DROP, adj
from .rounds import o_ring, open_arc
from .arches import smooth_widths   # R23's sawtooth fix, shared by the f's hook and the a's hood

DOT_R = 0.62 * S   # round 36: a dot 1.24 stems across reads as the stem's weight
DOT_R_ADJ = 0.58 * S   # round 92 (adj 'i', 'j'): the i a dot with a stalk (band -11%), the j's dot +27%
def dot_y(xh): return xh + 118 + S * 0.3

# owner, 2026-09-13: "slightly extend the top right serif of g" -- the ear's
# LENGTH only (the wedge family's L, WL, scaled), its DEPTH (the stroke's own
# cross-section) unchanged. Built at +15% and +30% for the page; +15% ships
# here by default. ALBO_G_EAR_EXTEND overrides for the page's other variant.
G_EAR_EXTEND = 0.15
# Owner 2026-09-15, and SETTLED the same day at 'slight' (0.34/0.60/0.21,
# against the previous 0.42/0.72/0.30).
# Owner 2026-09-15: "the line connecting the two ovals needs to be thinner at
# the connection with the lower oval in 'g'. and generally there needs to be
# some lightening and/or contrast." Three dials, all on the neck:
#   G_NECK      its FLOOR, x the stem -- the lightening
#   G_NECK_MID  its middle, x the bowl profile -- the contrast, since the ends
#               are already pinched and it is the middle that reads heavy
#   G_NECK_END  its width where it MEETS THE LOOP, x the profile. The bowl end
#               stays at 0.30: he named the lower oval specifically, and the two
#               ends are not symmetrical in a g -- the pen arrives at the loop
#               and leaves at the bowl.
G_NECK = float(os.environ.get("ALBO_G_NECK", 0.34))          # the neck's floor, x the stem (0.55 before; owner: thin the connector)
G_NECK_MID = float(os.environ.get("ALBO_G_NECK_MID", 0.60))  # the neck's middle, x its profile
G_NECK_END = float(os.environ.get("ALBO_G_NECK_END", 0.21))  # and where it meets the LOWER oval
# ROUND 230 -- THE LOOP'S TOP STROKE SITS ON THE BASELINE. Owner 2026-09-18:
# *"the top stroke of the bottom loop of the roman 'g' needs to sit on the
# baseline."* The loop was anchored with its outer top at +TH_H/2 -- the top
# stroke straddling the line, half a pen above it. G_LOOP_TOP is where the
# loop's top ink edge sits, in units above the baseline. Round 230 read the
# ruling as the edge ON the line (0); the owner corrected it the same day --
# *"sit on the baseline, meaning above the baseline"* -- so the top stroke
# STANDS on the line: its underside at 0, its top edge at TH_H. TH_H/2 (24)
# was the old drawing, straddling the line. The loop keeps its size and
# moves down, so the descender deepens by the same amount -- the same move
# the owner ruled for the italic in round 197, in the other direction.
G_LOOP_TOP = float(os.environ.get("ALBO_G_LOOP_TOP", TH_H))   # round 232: "sit on the baseline, meaning ABOVE the baseline" -- the top stroke's underside on the line, the stroke standing on it
def g_ear_scale(): return 1.0 + float(os.environ.get('ALBO_G_EAR_EXTEND', G_EAR_EXTEND))

# owner, 2026-09-13: "make a version of 't' that is a triangle on the right
# side, but keep it optically even to what is there now." Default True so
# both the old and new t ship; the page shows both.
T_RIGHT_TRIANGLE = os.environ.get('ALBO_T_TRIANGLE', '1') != '0'
T_TRI_SCALE = 0.55   # tunes the triangle's apex height so its ink area matches the old bar's within 2% (measured: old 53927 sq units at 1000 upm, triangle at 1.0 overshot to 56690 (+5.1%), 0.55 lands at 54552 (+1.2%))

@glyph('i')
def g_i(c):
    xh = c["xh"]; x = S / 2
    return geom.ink([stem(x, 0, xh, top='left', foot='both'), dot(x, dot_y(xh), DOT_R_ADJ if adj('i') else DOT_R)])

@glyph('l')
def g_l(c):
    # round 92 (adj 'l'): reads a size smaller than b d h -- the ascender family's top wedge (audit R2, 1.05), feet 0.92
    if adj('l'): return geom.ink([stem(S / 2, 0, c["asc"], top='left', foot='both', top_len=1.05, foot_len=0.92)])
    return geom.ink([stem(S / 2, 0, c["asc"], top='left', foot='both')])

@glyph('j')
def g_j(c):
    """No top flag; the tail one round arc holding the stem's weight through
    the turn and thinning to a point past the bottom (rounds 22, 25)."""
    xh = c["xh"]; wf = c["wf"]; desc = c["desc"]; r = 125 * wf; x = 120 * wf + S / 2
    B = -desc * 0.97; y0 = B + r
    # R26, owner 2026-09-18: "remove corner from bottom right (outside of
    # what you highlighted, but within what I highlighted)." The tail begins
    # at y0 on the stem's centerline with a vertical tangent, so the two
    # could meet flush; they did not, for two reasons measured on the built
    # outline. The stem ran 30 units PAST the tail's start (to y0 - 30), by
    # which height the tail's centerline had swung 4.4 units left, and the
    # tail was drawn 69.8 wide (TH_V x round 92's 0.9) against a stem of 77.7
    # at y0 -- so the stem's bottom-right corner stood 8.3 units proud of the
    # tail's inner edge at y -188, a step where the tail begins. Now the stem
    # ends 2 units into the tail (the overlap the union needs and no more)
    # and the tail starts at the stem's own width, easing to the round-92
    # profile by its 0.45 key -- the tail is a few units heavier over its
    # first 100 units and the same thereafter; the dot is not touched.
    # Gated on the style: the italic's own j lives in aldine.py, but
    # accents.py builds the dotless j and the j-circumflex of BOTH styles by
    # calling this function directly, so an ungated change here moves the
    # italic's uni0237 and jcircumflex (it did, on the first build).
    lo = y0 - 260
    st = stem(x, y0 - (30 if pen.ITALIC else 2), xh, top=None, foot=None, ent_span=(lo, xh))
    w_st = PR.stem_width(TH_V, ENT, (y0 - lo) / (xh - lo))   # the stem's width where the tail takes over
    a0, a1 = 0.0, math.radians(-118)
    tail = [(x - r + r * math.cos(a0 + (a1 - a0) * i / 48), y0 + r * math.sin(a0 + (a1 - a0) * i / 48)) for i in range(49)]
    jt = 0.9 if adj('j') else 1.0   # round 92 (adj 'j'): the heaviest letter by band (+27%) -- the tail 0.9, the dot as the i's
    wfn = widths([(0.0, TH_V * jt if pen.ITALIC else w_st), (0.45, S * jt), (1.0, S * 0.10)])
    return geom.ink([st, stroke(tail, wfn), dot(x, dot_y(xh), DOT_R_ADJ if adj('j') else DOT_R)])

# ALBO_ROM_F_BAR -- R21 / R22, owner 2026-09-18, on the f's bar ends: "give me
# options for slightly calligraphic treatments." Today's bar is a plain
# rectangle 0.8 of the pen's horizontal, square at both ends, its top on the
# x-height, 45 wf left of the stem and 120 wf right. Every option keeps the
# top on the x-height and the reach.
#   a  today
#   b  the pen's own ends: both faces sheared by the family's 20-degree cut,
#      as a broad nib leaves a horizontal (a parallelogram)
#   c  modulated: the bar thins to 0.70 at both ends the way bar(prof=) does
#      for the 7, the top edge held straight, the faces cut as b
#   d  b with small wedge ends -- hanging from the left end, rising from the
#      right, at half the bar-end wedge's size
F_BAR = os.environ.get("ALBO_ROM_F_BAR", "a")
F_BAR_CUT_DEG = float(os.environ.get("ALBO_ROM_F_BAR_CUT", 8.0))   # round 246: the bar's end faces lean this much, bottom-left to top-right; 0 is round 235
def f_bar(x, xh, wf, th, opt):
    x0, x1 = x - S * 0.5 - 45 * wf, x + S * 0.5 + 120 * wf
    if opt == 'b':
        return stroke([(x0, xh - th / 2), (x1, xh - th / 2)], th, cut0=CUT, cut1=CUT)
    if opt == 'c':
        return PR.bar(x0, x1, xh, th, align='top', cut0=CUT, cut1=CUT, prof=widths([(0.0, 0.70), (0.30, 1.0), (0.70, 1.0), (1.0, 0.70)]))
    if opt == 'd':
        b = stroke([(x0, xh - th / 2), (x1, xh - th / 2)], th, cut0=CUT, cut1=CUT)
        sh = math.tan(CUT) * th / 2   # the cut moves the bottom-left and the top-right corner outward by this (bar()'s own seating)
        k = 0.5
        wl = wedge((x0 - sh, xh - th), (-1, 0), (0, -1), WL * 0.85 * k, WD * 0.9 * k, 0.0)
        wr = wedge((x1 - sh, xh), (1, 0), (0, 1), WL * 0.85 * k, WD * 0.9 * k, 0.0)
        return geom.union([b, wl, wr])
    # ROUND 246. Owner 2026-09-18: "for f: a wins but make very slight pen
    # cuts from bottom left top to top right instead of vertical". Both end
    # faces lean the same way, F_BAR_CUT_DEG off the vertical (8; b's was the
    # family's full 20), the bottom corner left of the top corner at each end.
    if F_BAR_CUT_DEG > 0 and not pen.ITALIC:   # round 248: roman only -- round 246 had leaked into the italic ligatures' bars
        a_ = math.radians(F_BAR_CUT_DEG)
        return stroke([(x0, xh - th / 2), (x1, xh - th / 2)], th, cut0=a_, cut1=-a_)
    return stroke([(x0, xh - th / 2), (x1, xh - th / 2)], th)

def f_ink(c, hook_end=None, hook_c2=None, hook_profile=None, parts=False, hook_cut=True, flush=False):
    """The f's three solids (round 42 construction). The ligatures (round 96,
    `glyphs/ligatures.py`) re-aim the hook: `hook_end` replaces the cubic's
    end point, `hook_c2` its second control, `hook_profile` the width keys;
    `parts=True` returns [stem, hook, bar] unfused.

    `flush` (the standalone roman f only, R20): the hook leaves the stem with
    both edges continuous. Off, this is round 42's drawing byte for byte --
    the ligatures and the & keep it, since they are not in the round."""
    xh = c["xh"]; asc = c["asc"]; wf = c["wf"]; r = 200 * wf; x = 110 * wf + S / 2
    # R20, owner 2026-09-18: "remove corners on both sides." Measured on the
    # built f: the stem ran 30 units past the hook's start (to asc - r + 30),
    # by which height the hook's centerline had already swung right, so the
    # hook's outer edge began 4.9 units INSIDE the stem's left edge at y 623
    # -- the stem's top-left corner stood out as a step -- and the hook was
    # the pen's 77.5 against a stem of 79.1 there, a 2.1-unit jog on the
    # right. Now the stem ends 2 units into the hook (the overlap the union
    # needs, over which the centerline moves 0.01), and the hook begins at
    # the stem's own width, easing to the pen's by a quarter of its length.
    st_top = asc - r + (2 if flush else 30)
    st = stem(x, 0, st_top, top=None, foot=('left' if adj('f') else 'both'), ent_span=(0, asc))   # round 92 (adj 'f'): the double foot wide under the hook's reach -- left foot only
    end = hook_end or (x + r * 1.25, asc - r * 0.55); c2 = hook_c2 or (x + r * 0.9, asc + 8)
    hook = cubic((x, asc - r), (x, asc + 8), c2, end)
    prof = hook_profile or [(0.0, 1.0), (0.7, 1.0), (1.0, 1.2)]
    hook_cut1 = CUT if hook_cut else None
    # ROUND 275 -- THE HOOK'S END IS THE c's TOP FINIAL. Owner 2026-09-19:
    # "change out round finials (like c top serif)." The hook flared to 1.2 of
    # the pen over its last 30% into the family's 20-degree cut, a face lying
    # across a stroke heading down-right -- measured 79.9 wide at the 400 and
    # 138.6 at the 700, against the c's top of 60.8 and 103.4, and it read as
    # a teardrop. Now the family's finial (PR.finial_widths / PR.finial_cut):
    # the swell to 1.10 over the last 13%, the face sheared 28 degrees toward
    # the vertical (73.3 and 127.1 wide). The standalone roman f only, with
    # the flush hook: the ligatures re-aim the hook and pass their own
    # profile with no cut, and keep round 42's drawing.
    _finial = flush and hook_profile is None and hook_cut
    if _finial:
        # The face is sheared 28 degrees against the cut's 20, so its forward
        # (inner, lower) corner would reach tan(28) x 1.10 / 2 - tan(20) x 1.2
        # / 2 = 0.074 of the pen further down-right than round 42's did --
        # 4.9 units at the 400, 8.6 at the 700 -- into the f-capital pairs
        # that already sit at the touch floor: measured, fW touched at the 200
        # (-0.0024 em) and fT fell under the floor at the 700 (0.0086). The
        # hook's end retreats along its own tangent by that amount, so the
        # forward corner lands where it always has and the pairs measure as
        # they did; the hook is 0.074 of a pen shorter on its centerline.
        F_FINIAL_RETREAT = (math.tan(math.radians(PR.FINIAL_CUT_DEG)) * PR.FINIAL_SWELL - math.tan(CUT) * 1.2) / 2
        _ux, _uy = end[0] - c2[0], end[1] - c2[1]; _L = math.hypot(_ux, _uy) or 1.0
        _pe = pen.PEN.th((_ux / _L, _uy / _L)) * F_FINIAL_RETREAT
        end = (end[0] - _ux / _L * _pe, end[1] - _uy / _L * _pe)
        hook = cubic((x, asc - r), (x, asc + 8), c2, end)
    if flush:
        f0 = PR.stem_width(TH_V, ENT, st_top / asc) / TH_V   # the hook's start tangent is vertical, so the pen there IS TH_V
        prof = [(0.0, f0), (0.25, 1.0)] + [k for k in prof if k[0] > 0.25]
        if _finial: prof = [k for k in prof if k[0] < 1.0] + [(1.0, 1.0)]
    # flush also takes the arch's sawtooth fix (arches.smooth_widths, R23): the hook's edges carried the same 1-2 unit steps
    hw = smooth_widths(hook, pen.PEN.th, widths(prof)) if flush else pen_widths(hook, widths(prof))
    if _finial:
        hw = PR.finial_widths(hw, False); hook_cut1 = PR.finial_cut(hook, False)
    hk = stroke(hook, hw, cut1=hook_cut1)
    th = TH_H * 0.8
    b = f_bar(x, xh, wf, th, F_BAR if flush else 'a')
    return [st, hk, b] if parts else geom.ink([st, hk, b])

def f_geometry(c):
    """The f's stem centre x, hook radius r, and the bar's right end."""
    wf = c["wf"]; r = 200 * wf; x = 110 * wf + S / 2
    return x, r, x + S * 0.5 + 120 * wf

# Round 103 (owner: "fix a being squished"). The italic a's bowl is now a
# factor on the O's OWN centerline radius, not an independent fraction of the
# x-height: at 0.36 xh it came out 0.68 wide over tall against the o's 0.842 --
# 20% narrower than the letter it is supposed to be a sibling of, which is
# exactly what "squished" looks like. Derived from the o, it tracks IT_OVAL and
# every later ruling on the o for free. 0.96 because an a's bowl sits a touch
# narrower than an o, not a fifth narrower.
ITALIC_A_BOWL = 0.96      # the single-storey a's bowl, x the o's centerline radius
def g_a_italic(c):
    """The italic a: ONE storey -- a bowl and a stem, the o's own ring with
    the stem on its right. A sloped two-storey a is the commonest tell of a
    sloped roman pretending to be an italic, so this is the first form the
    italic switches (guide: an italic is not a slope)."""
    from .rounds import o_ring, O_RX
    xh = c["xh"]
    # THE O'S OWN RING, at 0.96 of its radius -- so the a cannot drift from the
    # o, and IT_OVAL reaches it. (Two earlier cuts sized this bowl by hand: the
    # first at 0.34 xh came out 0.6 of the x-height and read as a small cap,
    # the second at 0.36 xh was the right height and a fifth too narrow.)
    bowl, outer, inner = o_ring(c, O_RX * ITALIC_A_BOWL)
    x0, y0, x1, y1 = bowl.bounds
    st = stem(x1 - S * 0.5 + S * 0.08, 0, xh, top=None, foot='right', ent_span=(0, xh))
    return geom.ink([bowl, st])

def g_f_italic(c):
    """The italic f: it DESCENDS, the one letter whose italic form changes
    its own vertical extent. The hook above is the roman's; below the
    baseline the stem turns left and thins to a point, as the j's tail does."""
    xh = c["xh"]; asc = c["asc"]; desc = c["desc"]; wf = c["wf"]
    r = 200 * wf; x = 110 * wf + S / 2
    st = stem(x, -desc * pen.IT_FTAIL, asc - r + 30, top=None, foot=None, ent_span=(0, asc))
    hook = cubic((x, asc - r), (x, asc + 8), (x + r * 0.9, asc + 8), (x + r * 1.25, asc - r * 0.55))
    hk = stroke(hook, pen_widths(hook, widths([(0.0, 1.0), (0.7, 1.0), (1.0, 1.2)])), cut1=CUT)
    # The tail follows IT_FTAIL by SCALING the original coefficients, not by
    # being rewritten around a new depth: the first cut put the tail's start
    # at -desc*0.80 while the stem stopped at -desc*0.30, so the tail floated
    # free of the letter in every option. k is 1.0 at the shipped 0.30.
    _k = pen.IT_FTAIL / 0.30
    tail = cubic((x, -desc * 0.24 * _k), (x, -desc * 0.78 * _k),
                 (x - r * 0.46, -desc * 0.96 * _k), (x - r * 0.86, -desc * 0.72 * _k))
    tl = stroke(tail, widths([(0.0, TH_V * 0.95), (0.55, S * 0.72), (1.0, S * 0.10)]), cut0=None)
    th_ = TH_H * 0.8
    b = stroke([(x - S * 0.5 - 45 * wf, xh - th_ / 2), (x + S * 0.5 + 120 * wf, xh - th_ / 2)], th_)
    return geom.ink([st, hk, b, tl])

@glyph('f')
def g_f(c):
    """VdK's f (round 42): hook radius 200, reaching 0.65 xh past the stem,
    flaring into the pen cut; the bar 0.8 of the pen with its top on the
    x-height, 45 left / 120 right."""
    if pen.ITALIC: return g_f_italic(c)   # round 100: an italic f descends
    if pen.ITALIC: return g_f_italic(c)
    return f_ink(c, flush=True)

@glyph('t')
def g_t(c):
    """Round 51's t, restored (owner 2026-09-13: "revert 't' before the
    triangle"): the stem sheared at the top by the pen cut, a plain bar,
    the hooked tail."""
    xh = c["xh"]; wf = c["wf"]; r = 135 * wf; x = 100 * wf + S / 2
    # round 92 (adj 't'): the lightest letter in a word (band -16% Albertus) -- the top +20, the bar 1.15 of the pen's horizontal
    t_top = xh + (115 if adj('t') else 95); t_bar = TH_H * (1.15 if adj('t') else 1.0)
    st = stem(x, r * 0.85 - 10, t_top, top=None, foot=None, ent_span=(0, t_top), cut_top=CUT)
    tail = cubic((x, r * 0.85), (x, -OVER * 0.5), (x + r * 0.8, -OVER * 0.5), (x + r * 1.45, r * 0.6))
    tl = stroke(tail, pen_widths(tail, widths([(0.0, 1.0), (0.65, 1.0), (1.0, 1.3)])), cut1=CUT)
    b = stroke([(x - 100 * wf, xh - t_bar / 2), (x + 150 * wf, xh - t_bar / 2)], t_bar)
    return geom.ink([st, tl, b])

T_TOP_RISE = 96
T_TOP_SHEAR_DEG = 46

# owner 2026-09-14: "make five versions for me to pick from that gives a curve
# instead of a corner in the upper right of 'a'": (stem top x xh, hood
# start x xh, lean right in wf units, the lean's height x xh)
# owner 2026-09-14 on 0-4: "the 'a' curve needs to be closer to the vertical
# corner that was there before, you maximize gap space under the stroke":
# 5-9 keep the stem high (round 83's went to 0.95 xh with the hood bending
# over the top) and start the hood low and at the floor width, so the hollow
# under it stays open; the curve is only at the corner. The hood's path
# starts FLUSH with the stem's right edge (A_HOOD_FLUSH), or the stem's flat
# top pokes 0.25 S past the thinner hood -- a step, seen in the first build
# of 6-9. (The hood's start width is the 0.5 S floor at this contrast
# whatever the profile asks, so no width column.)
A_CURVES = [(0.66, 0.54, 22, 0.93),   # 0: round 84's
            (0.62, 0.50, 34, 0.94),   # 1: a little rounder
            (0.58, 0.46, 46, 0.95),   # 2: rounder still
            (0.54, 0.42, 60, 0.96),   # 3: a full shoulder
            (0.70, 0.58, 14, 0.90),   # 4: barely a curve, the stem nearly to the top
            (0.92, 0.60, 8, 1.04),    # 5: round 83's corner with the least rounding
            (0.88, 0.60, 10, 1.02),   # 6
            (0.84, 0.60, 12, 1.00),   # 7
            (0.80, 0.60, 0, 0.98),    # 8: RULED (owner 2026-09-14: "A curve 8 wins, but can you smooth
                                      # off the top right so there is no corner protuberance?") -- lean
                                      # 14 -> 0, so the hood leaves the stem vertical, no kink
            (0.76, 0.58, 16, 0.95)]   # 9: the roundest of the tight ladder
A_HOOD_FLUSH = True
A_HOOD_W = 0.92   # round 94: the hood's stroke x this (both its outer run-then-arc and the underside cubic)
A_UNDER_LEAN = 14   # round 86's curve 8 lean, for the underside cubic
A_CURVE = int(__import__('os').environ.get('FJORD_A_CURVE', 8))
# ALBO_ROM_A_OPT -- R17, owner 2026-09-18: "remove corner on shoulder, also
# give me an option that reduces visual imbalance in bottom right and options
# for a top left serif where the corner was." The shoulder is a FIX (below,
# in g_a); these are the options:
#   a  today, with the shoulder fixed
#   b  the bottom right lightened: the stem's right foot at 0.75 of the
#      family's length and depth (the one serif the a wears -- its left foot
#      is buried in the bowl -- and the mass the bowl's bottom joins at)
#   c  a small wedge serif at the hood's terminal, up-left, where the old
#      hood's flag was (the corner the 2026-09-13 redraw took away):
#      0.45 of the family's diagonal end
#   d  the same at 0.70
A_OPT = os.environ.get("ALBO_ROM_A_OPT", "b")   # round 244: b ships -- owner 2026-09-18, "for a: a and b" (the fix and the rebalanced right foot)
A_FOOT_B = 0.75
A_TERM_WEDGE = {'c': 0.45, 'd': 0.70}

@glyph('a')
def g_a(c):
    """Stem, hood and bowl -- redrawn 2026-09-13 (owner: the first cleanup
    "sucks"). What was wrong: the hood and the bowl's upper edge were PEN
    strokes, and at contrast 0.95 the pen's thin is the 6-unit floor, so the
    hood read as a bar with a flag and the bowl as a shallow lens. Now the
    hood and the bowl are on the BOWL profile (hair 0.525 S at this
    contrast), the bowl is taller -- it leaves the stem at 0.60 xh with a
    round upper-left shoulder instead of a straight diagonal -- and the
    hood curls: it climbs from the stem, crosses the top at the rounds'
    overshoot and comes DOWN to its terminal, which swells and ends in the
    pen cut, a teardrop not a flag. Counter and aperture are the whites
    the standing rule watches: reported on the page."""
    if pen.ITALIC: return g_a_italic(c)   # round 100: an italic a is one storey
    xh = c["xh"]; wf = c["wf"]; x = 360 * wf
    # owner 2026-09-13: "the top right of 'a' needs to be more of a curve
    # than a rectangular corner" -- the stem stops at A_STEM_TOP x xh and the
    # hood takes over from lower on the stem, leaning out to the right as it
    # climbs, so the outer contour at the top right is the hood's own curve
    top_f, start_f, lean, up = A_CURVES[A_CURVE]
    # ROUND 272 -- THE COUNTER'S LOWER RIGHT is the stem's INSIDE FOOT. Owner
    # 2026-09-19: *"roman 700 and 900 'a' is too thick especially lower right
    # within counter."* The left foot sits inside the bowl, under the bottom
    # stroke at the 400, but its bracket grows with the weight and at the
    # heavy ends it climbs into the counter as a chamfer: at the 900 from
    # (191, 61) on the counter's bottom to the stem's inner edge at y 160,
    # so the counter covered 35% of its own lower-right 60 x 60 against 67%
    # at the 400 and 88% at its own lower left. Above 84 the stem carries
    # its right foot only; at and under 84 both feet, and the 400 is
    # byte-identical.
    _feet_in = S <= 84.0
    if A_OPT == 'b':   # option b: the right foot smaller; the left foot is inside the bowl either way
        st = geom.union(([stem(x, 0, xh * top_f, top=None, foot='left', ent_span=(0, xh))] if _feet_in else []) +
                        [stem(x, 0, xh * top_f, top=None, foot='right', ent_span=(0, xh), foot_len=PR.FOOT * A_FOOT_B, foot_depth=A_FOOT_B)])   # stem()'s foot_len default is FOOT, so the factor multiplies it
    else:
        st = stem(x, 0, xh * top_f, top=None, foot='both' if _feet_in else 'right', ent_span=(0, xh))
    peak = xh + OVER - PR.bowl_hair() / 2
    if A_HOOD_FLUSH:
        # owner 2026-09-14, "smooth off the top right so there is no corner
        # protuberance": the hood is a straight run up the stem's centerline
        # at EXACTLY the stem's width (the stem flares 14% at its ends, ENT,
        # so that width is stem_width at top_f), and the curve begins at the
        # stem's top with a vertical tangent. Below top_f the hood's two
        # edges are the stem's two edges; the stem's flat top lies inside
        # the hood; nothing steps. (Measured before this: the cubic from
        # start_f bent left at once, and at the stem's top its outer edge was
        # 21 units inside the stem's -- the stem's corner was the bump.)
        # R17, owner 2026-09-18: "remove corner on shoulder." The comment
        # above was true at round 86 and false from round 94: A_HOOD_W
        # multiplies the WHOLE profile, f0 included, so the hood left the
        # stem at 0.92 of the stem's width -- 3.2 units inside its right edge
        # (measured on the built a: the hood's outer edge at 357.5 against
        # the stem's at 361.5, an 87-degree turn at the corner). f0 is now
        # divided by A_HOOD_W, so after the round-94 factor the hood IS the
        # stem's width where the stem's flat top lies inside it, and the
        # arc, whose first control point is straight above (lean 0, curve
        # 8), leaves the stem's edge vertical. The 0.92 still applies from
        # the turn on, which is what round 94 asked for.
        w_st = PR.stem_width(TH_V, PR.ENT, top_f); f0 = w_st / S / A_HOOD_W
        run = line((x, xh * start_f), (x, xh * top_f))
        arc = cubic((x, xh * top_f), (x + lean * wf, xh * up), (x - 236 * wf, peak + 44), (x - 286 * wf, xh * 0.72))
        hood = join(run, arc)
        tot = sum(math.hypot(hood[i + 1][0] - hood[i][0], hood[i + 1][1] - hood[i][1]) for i in range(len(hood) - 1))
        tv = xh * (top_f - start_f) / tot   # the run's share of the arc length
        under = cubic((x, xh * start_f), (x + A_UNDER_LEAN * wf, xh * up), (x - 236 * wf, peak + 44), (x - 286 * wf, xh * 0.72))
        under0 = widths([(0.0, 0.85), (0.35, 0.92), (0.75, 1.0), (1.0, 1.0)]) if adj('a') else widths([(0.0, 0.85), (0.22, 1.0), (0.75, 1.0), (1.0, 1.0)])   # round 275: the 1.12 at the end is the finial's swell now (below)
    else:
        hood = cubic((x, xh * start_f), (x + lean * wf, xh * up), (x - 236 * wf, peak + 44), (x - 286 * wf, xh * 0.72))
        prof = widths([(0.0, 0.85), (0.22, 1.0), (0.75, 1.0), (1.0, 1.12)])
    # ROUND 272 -- THE a ABOVE STEM 84. Owner 2026-09-19: *"roman 700 and 900
    # 'a' is too thick especially lower right within counter"* and *"fix the
    # overlap mismatch glitches on the right of 'a'."* The hood's profile is
    # 0.85-1.12 of the pen, which at a 148 stem is a 125-165 unit hood over a
    # counter 115 wide; above 84 it is scaled by sqrt(84/S) -- 0.85 at the
    # 700, 0.75 at the 900 -- RAMPED IN past the run, so the hood leaves the
    # stem at the stem's own width and thins along the arc (a flat factor put
    # a 10-unit step where the arc starts). At and under 84 the factor is 1
    # and every line below is today's code path, so the 400 is byte-identical.
    _hf = (84.0 / S) ** 0.5 if S > 84.0 else 1.0
    _t0 = (min(0.6, tv + 0.12) if A_HOOD_FLUSH else 0.30); _t1 = min(0.95, _t0 + 0.25)
    def _ramp(t):
        if _hf == 1.0: return 1.0
        return 1.0 if t <= _t0 else (_hf if t >= _t1 else 1.0 + (_hf - 1.0) * (t - _t0) / (_t1 - _t0))
    def _build(f0):
        if A_HOOD_FLUSH:
            prof0 = widths([(0.0, f0), (min(0.6, tv + 0.12), f0), (0.75, 1.0), (1.0, 1.0)])   # the stem's width held through the turn
            prof_ = lambda t: prof0(t) * A_HOOD_W * _ramp(t)   # round 94 (owner: "slightly reduce the top stroke of 'a'")
            under_prof = lambda t: under0(t) * A_HOOD_W * _ramp(t)   # round 92 (adj 'a'): the heaviest common letter (band +19% Albertus) -- the underside held light longer
            # ROUND 275 -- THE HOOD'S TERMINAL IS THE c's TOP FINIAL (owner:
            # "change out round finials (like c top serif)"). It swelled to
            # 1.12 over its last 25% into the 20-degree cut, "a teardrop not a
            # flag" -- 66.4 wide at the 400, 97.3 at the 700, the cut leaving
            # the OUTER (up-left) corner as the drop's point. Now the family's
            # finial on both strokes that share this end (the hood and its
            # underside end on one point at one width, so both must take it):
            # the swell to 1.10 over the last 13% and the face sheared 28
            # degrees toward the vertical, which on a stroke heading down-left
            # leaves the inner corner forward, as the c's top does. 65.2 and
            # 95.6 wide; no floor at the 700, where round 272 thinned this hood
            # on purpose. PR.finial_widths / PR.finial_cut.
            hood_w_ = PR.finial_widths(smooth_widths(hood, PR.bowl_th, prof_, floor=S * 0.5 * _hf), False)
            hd_ = stroke(hood, hood_w_, cut1=PR.finial_cut(hood, False))
            hd_ = geom.union([hd_, stroke(under, PR.finial_widths(smooth_widths(under, PR.bowl_th, under_prof, floor=S * 0.5 * _hf), False), cut1=PR.finial_cut(under, False))])
        else:
            prof_ = lambda t: prof(t) * _ramp(t)
            hood_w_ = PR.bowl_widths(hood, prof_, floor=S * 0.5 * _hf)
            hd_ = stroke(hood, hood_w_, cut1=CUT)
        return prof_, hood_w_, hd_
    prof, hood_w, hd = _build(f0 if A_HOOD_FLUSH else None)
    if S > 84.0 and A_HOOD_FLUSH:
        # THE JUNCTION, FLUSH BY MEASUREMENT. The hood's start width is the
        # stem's width at top_f as `stem_width` predicts it, and the hood as
        # drawn is narrower than the stem as drawn -- the arc's first tangent
        # leans, the bowl profile hands it a smaller width, the widths are
        # smoothed -- by 1.5 units at the 700 and 2-3 at the 900: a step on the
        # letter's right edge where the hood leaves the stem. So the hood is
        # built, its edge just above the stem's top is READ against the stem's
        # edge just below it, and it is built again with the start width scaled
        # by the miss. Then the run is trimmed to the stem's own footprint, the
        # outer edge is held at the stem's edge for 30 units above the top (the
        # smoothed widths overshoot there), and the stem's chamfered top corner
        # is filled under the hood's edge.
        from shapely.geometry import LineString as _LS, box as _box
        _xr = st.intersection(_LS([(x, xh * top_f - 0.75), (x + 3 * S, xh * top_f - 0.75)])).bounds[2]
        _hr = hd.intersection(_LS([(x, xh * top_f + 0.5), (x + 3 * S, xh * top_f + 0.5)])).bounds[2]
        if abs(_hr - _xr) > 0.15 and _hr > x:
            prof, hood_w, hd = _build(f0 * (_xr - x) / (_hr - x))
        _band = _box(x, xh * start_f - 2.0, x + 3 * S, xh * top_f)
        hd = hd.difference(_band.difference(st))
        hd = hd.difference(_box(_xr, xh * top_f - 2.0, x + 3 * S, xh * top_f + 30.0))
        hd = geom.union([hd, _box(x, xh * top_f - 6.0, _xr, xh * top_f + 1.0)])
    if A_OPT in A_TERM_WEDGE:
        # options c / d: a wedge serif on the hood's terminal, on its outer
        # (up-left) side, seated on the corner the pen cut leaves there. The
        # terminal travels down-left; left of that travel is the inner side,
        # so the outer corner is the stroke's R end, which cut1 moves
        # FORWARD by tan(CUT) x w/2 -- the wedge sits on the moved corner, as
        # bar() seats its wedges on the sheared corner, or its flat top would
        # overrun the face.
        tn = geom.tangents(hood); d = tn[-1]; w_end = hood_w(1.0)
        sd = (d[1], -d[0])                     # right of travel = up-left here
        P = hood[-1]; fwd = math.tan(PR.finial_cut(hood, False) if A_HOOD_FLUSH else CUT) * w_end / 2   # round 275: the flush hood's face is the finial's cut, and the wedge seats on the corner that cut leaves
        A = (P[0] + sd[0] * w_end / 2 + d[0] * fwd, P[1] + sd[1] * w_end / 2 + d[1] * fwd)
        hd = geom.union([hd, PR.diag_wedge(A, d, sd, A_TERM_WEDGE[A_OPT])])
    # the bowl's OUTER path (ccw): from inside the stem at 0.60 xh, a round
    # shoulder out to the left extreme at 0.30 xh, a round bottom, back
    # into the stem near the foot
    L = (x - 335 * wf, xh * 0.30); B = (x - 150 * wf, -OVER)
    xin = x + TH_V / 2 - TH_V * 0.35
    top = (xin, xh * 0.60)
    outer = join(cubic(top, (top[0] - 70 * wf, top[1] + 62), (L[0] + 6 * wf, L[1] + 150), L),
                 cubic(L, (L[0], L[1] - 120), (B[0] - 105 * wf, B[1]), B),
                 cubic(B, (B[0] + 85 * wf, B[1]), (xin, 15), (xin, 60)))
    outer_closed = geom.resample(outer + [outer[0]])[:-1]
    tans_o = geom.tangents(outer_closed, closed=True); n_o = len(outer_closed)
    NEAR_STEM_W = 40.0
    A_BOWL_ADJ = 0.92   # round 92 (adj 'a'): the bowl's stroke x this; 0.85 -> 0.92 (owner, round 93: "don't thin out 'a' as much")
    def wfn2(t):
        i = min(n_o - 1, int(round(t * n_o))); p = outer_closed[i]
        w = max(PR.bowl_th(tans_o[i]) * (A_BOWL_ADJ if adj('a') else 1.0), S * 0.5)
        u = max(0.0, min(1.0, (p[0] - (xin - 90.0)) / 90.0)); u = u * u * (3 - 2 * u)
        return w * (1 - u) + NEAR_STEM_W * u
    solid, o, i = ring_from(outer, widths_fn=wfn2, counter_smooth=3, smooth_w=6)
    return geom.ink([st, hd, solid])

@glyph('s')
def g_s(c):
    """One smooth spine on the pen's own widths (round 51's s: no spine
    boost -- that is the capital's rule), flaring 1.25 into a 20-degree pen
    cut at both ends."""
    xh = c["xh"]; wf = c["wf"]; w = 370 * wf; o = OVER - TH_H / 2
    pts = [(w * 0.93, xh * 0.80), (w * 0.62, xh + o * 0.9), (w * 0.20, xh * 0.86), (w * 0.22, xh * 0.60),
           (w * 0.78, xh * 0.42), (w * 0.82, xh * 0.16), (w * 0.42, -o * 0.9), (w * 0.06, xh * 0.19)]
    spine = catmull(pts, tension=0.55)
    prof = widths([(0.0, 1.25), (0.12, 1.0), (0.88, 1.0), (1.0, 1.25)])
    if PR.BOWL and PR.BOWL.get('widen'): prof = widen_terminal(widen_terminal(None, True), False)
    wfn = pen_widths(spine, prof)
    return geom.ink([stroke(spine, wfn, cut0=CUT, cut1=CUT)])

def bowl_stem(c, side, top, bottom):
    """b d p q: the o's ring at the b's radius, KEPT TO THE STEM (ruling,
    round 18): the ring's far stroke is centred half a stem outside the
    stem's centre, as the record placed it, and the ring is clipped a hair
    inside the stem's inner edge -- the union with the stem is the join,
    the counter's edge is the stem's inner edge, nothing pokes past the
    stem. A trap notch at each crotch."""
    from shapely.geometry import box
    xh = c["xh"]; wf = c["wf"]
    rx_c = 214 * wf * (pen.IT_OVAL if pen.ITALIC else 1.0); rx = rx_c + TH_V / 2; ry = xh / 2 + OVER   # round 108: the italic's bowls narrow with its o (they were 20% wider than it)
    if side == 'right':   # d q: stem on the right
        cx = rx; x = cx + rx_c - S * 0.5; into = -1   # the record: the stem's centre half a stem INSIDE the ring's far centerline
    else:                 # b p
        x = S / 2; cx = x - S * 0.5 + rx_c; into = 1
    ch = c.get('ch', '')
    if ch == 'p' and adj('p'):
        # round 92 (adj 'p'): the bowl/stem join read as a dark corner at 13
        # pt -- the ring's stroke eases to NEAR_STEM_W within 90 units of the
        # stem's edge (the a's construction), so the crotches clear
        outer0 = superellipse(cx, xh / 2, rx, ry, 0, 2 * math.pi, BOWL_K)[:-1]
        edge0 = x + into * TH_V / 2
        def wfn(t):
            i = min(len(outer0) - 1, int(round(t * len(outer0)))); p = outer0[i]
            w = max(PR.bowl_th(geom.tangents(outer0, closed=True)[i]), S * 0.5)
            u = max(0.0, min(1.0, (90.0 - abs(p[0] - edge0)) / 90.0)); u = u * u * (3 - 2 * u)
            return w * (1 - u) + 40.0 * u
        solid, outer, inner = ring_from(outer0, widths_fn=wfn, counter_smooth=3, smooth_w=6)
    else:
        solid, outer, inner = ring(cx, xh / 2, rx, ry, w_scale=(0.92 if ch in 'bd' and adj('b') else 1.0))   # round 92 (adj 'b'): b d bowls a shade heavy (b +12% Garamond), 0.92
    edge = x + into * TH_V / 2
    clip = box(edge - 5, -1000, 3000, 2000) if into == 1 else box(-2000, -1000, edge + 5, 2000)
    solid = solid.intersection(clip)
    foot = ('right' if side == 'right' else 'left') if bottom == 0 else 'both'   # round 92 tried a one-sided foot on the p; owner, round 93: "keep the serif as it was" -- and "do not make half serif" on any letter
    st = stem(x, bottom, top, top='left', foot=foot, ent_span=(bottom, top))
    # no trap cutouts here: the first version's pointed INTO the strokes
    # (a nick on the outside at each crotch, seen at 500 px); no ruling asks
    # for traps on the bowl letters
    return geom.ink([solid, st])

@glyph('b')
def g_b(c): return bowl_stem(c, 'left', c["asc"], 0)
@glyph('d')
def g_d(c): return bowl_stem(c, 'right', c["asc"], 0)
@glyph('p')
def g_p(c): return bowl_stem(c, 'left', c["xh"], -c["desc"])
@glyph('q')
def g_q(c): return bowl_stem(c, 'right', c["xh"], -c["desc"])

@glyph('g')
def g_g(c):
    """G3 (rulings, rounds 40/42) -- redrawn 2026-09-13 (owner: the first
    cleanup "sucks"). What was wrong: the neck and the ear were PEN strokes,
    sticks at contrast 0.95; the loop was a flat ellipse much wider than the
    bowl; the ear a long thin bar. Now: the bowl a little smaller and
    rounder (rx 172 wf, 0.66 xh tall); the loop less flat (rx 200 wf, half
    height 0.50 desc) and closer under the bowl; the neck on the bowl
    profile with a 0.55 S floor, leaving the bowl at 240 deg and entering
    the loop at 150 deg; the ear a short heavy stroke off the shoulder at
    the bowl profile, floored at 0.72 S, rising 8 deg, ending in the pen
    cut -- the top-right serif of the round-30 ruling, with weight."""
    xh = c["xh"]; wf = c["wf"]; desc = c["desc"]
    rx = 172 * wf + TH_V / 2; ry = (xh * 0.66 + OVER * 2) / 2; cy = xh + OVER - ry; cx = rx + S * 0.35
    bowl, bo, bi = ring(cx, cy, rx, ry)
    lrx = 190 * wf + TH_V / 2; lry = desc * 0.50 + TH_H / 2; lcx = cx + 18 * wf; lcy = G_LOOP_TOP - lry   # round 230: the loop's top edge at G_LOOP_TOP
    loop, lo, li = ring(lcx, lcy, lrx, lry)
    crx, cry = rx - TH_V / 2, ry - TH_H / 2; clrx, clry = lrx - TH_V / 2, lry - TH_H / 2
    def on(cx_, cy_, rx_, ry_, deg):
        a = math.radians(deg); return (cx_ + rx_ * math.cos(a), cy_ + ry_ * math.sin(a))
    p0 = on(cx, cy, crx, cry, 240); a1 = math.radians(150); p3 = on(lcx, lcy, clrx, clry, 150)
    tl = (-math.sin(a1), math.cos(a1)); gap = p0[1] - p3[1]
    # owner 2026-09-14: "clear out the inside counter of 'g' so it is an
    # uninterrupted oval" -- the neck and the ear used to START inside the
    # ring's centerline (22 up, 25 in), and their square start faces landed
    # in the counter. Both now begin ON the ring's centerline and taper in,
    # so nothing reaches the counter. And: "thin out the connector stroke
    # between ovals in g to match the calligraphic style" -- the neck on the
    # bowl profile with a G_NECK floor and a light middle.
    neck = cubic(p0, (p0[0] - gap * 0.05, p0[1] - gap * 0.58), (p3[0] - tl[0] * gap * 0.55, p3[1] - tl[1] * gap * 0.55), p3)
    nk = stroke(neck, PR.bowl_widths(neck, widths([(0.0, 0.30), (0.16, 0.9), (0.45, G_NECK_MID), (0.85, 0.9 * min(1.0, G_NECK_END / 0.30)), (1.0, G_NECK_END)]), floor=S * G_NECK))
    ex, ey = on(cx, cy, crx, cry, 44); L = 96 * wf * g_ear_scale()
    ear_c = [(ex, ey), (ex + L, ey + L * math.tan(math.radians(8)))]
    ear = stroke(ear_c, PR.bowl_widths(ear_c, widths([(0.0, 0.4), (0.35, 1.0), (1.0, 1.05)]), floor=S * 0.72), cut1=CUT)
    return geom.ink([bowl, loop, nk, ear])
