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

BOWL_BLEND = float(os.environ.get("ALBO_BOWL_BLEND", 0.0))   # round 343: close_corners radius on b d p q, units
DOT_R = 0.62 * S   # round 36: a dot 1.24 stems across reads as the stem's weight
DOT_R_ADJ = 0.58 * S   # round 92 (adj 'i', 'j'): the i a dot with a stalk (band -11%), the j's dot +27%
# ROUND 369 -- THE TITTLE. Owner 2026-09-23: *"scale up tittles to optically
# line up with characters."* Measured against six roman references at a common
# x-height (`cmp_marks.py`), Albo's tittle is 0.160 of the x-height where they
# run 0.221-0.261 -- but that comparison flatters them, because Albo's STEM is
# also the lightest of the seven (0.139 against 0.175-0.209). The measure that
# answers "lines up with the characters" is the tittle against the face's OWN
# stem, and there Albo reads 1.153 where the references run 1.148-1.444: at
# the very floor of the band rather than outside it. Both readings point the
# same way, which is why this dial only goes up.
# It carries the ACCENT dots too -- the dieresis's pair and the dot-above --
# because a tittle and a dot accent are the same optical object, a dot sitting
# over an x-height, and moving one without the other is how an i and an i-dot-
# accent stop matching. 1.0 is the shipped drawing exactly.
TITTLE = float(os.environ.get("ALBO_TITTLE", 1.20))   # round 369: tittle/stem 1.153 -> ~1.40, against the references' 1.148-1.444 (Georgia 1.378, Charter 1.368)
TIT_R = DOT_R * TITTLE
TIT_R_ADJ = DOT_R_ADJ * TITTLE
def dot_y(xh):
    """The tittle's CENTRE. It rises with the tittle, so scaling the dot does
    not close the white under it: the gap over the x-height was already 0.209
    where the references run 0.224-0.383 -- the tightest of the seven -- and
    growing the dot on a fixed centre took it to 0.179 at TITTLE 1.40, which
    is a bigger tittle that reads as a MERGED one at 13 px. At TITTLE 1.0 the
    added term is zero and the i is byte-identical."""
    return xh + 118 + S * 0.3 + (TIT_R - DOT_R)

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
    return geom.ink([stem(x, 0, xh, top='left', foot='both'), dot(x, dot_y(xh), TIT_R_ADJ if adj('i') else TIT_R)])

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
    return geom.ink([st, stroke(tail, wfn), dot(x, dot_y(xh), TIT_R_ADJ if adj('j') else TIT_R)])

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

# ROUND 285 -- THE s's FLOW AND THE SIZE OF ITS TOP, AS OPTIONS. Owner
# 2026-09-19: *"give me more options with an improved flow and smaller top."*
# Read off the drawing as it stands (option a): the two bowls are the SAME
# width (lower/upper 0.994, where a humanist s carries the lower wider), and
# the spine has a second inflection at t 0.03, right at the head, where the
# curve reverses for a thirtieth of its length before it turns the right way.
# Each option moves some of: `up` (how far the UPPER bowl reaches toward the
# letter's axis, 1.00 as drawn), the head's start, the arch's overshoot, the
# spine's tension, the two mid points, and S_FOOT_RATIO (the foot's end ink
# over the head's, which is what trims the top terminal).
S_OPTS = {
    'a': {},                                                                                     # the drawing before round 285
    'b': dict(up=0.88, ratio=1.30, waist=0.01),                                                  # SHIPPED, round 286: the owner's pick plus his amendment ("plus .01 wins")
    'c': dict(up=0.80, head=(0.90, 0.85), over=0.75, ratio=1.30),
    'd': dict(up=0.80, head=(0.88, 0.86), over=0.60, tens=0.62, ratio=1.30),
    'e': dict(up=0.74, head=(0.88, 0.87), over=0.55, tens=0.62, ratio=1.45, mid=(0.74, 0.80), midy=(0.44, 0.17)),
}
S_OPT = os.environ.get("ALBO_ROM_S_OPT", "b")   # round 286: b ships (owner: "b wins")
if S_OPT not in S_OPTS: S_OPT = "a"
_SO = S_OPTS[S_OPT]
S_UP    = float(os.environ.get("ALBO_ROM_S_UP",   _SO.get('up', 1.00)))
S_OVER  = float(os.environ.get("ALBO_ROM_S_OVER", _SO.get('over', 0.90)))
S_TENS  = float(os.environ.get("ALBO_ROM_S_TENS", _SO.get('tens', 0.55)))
S_MID   = _SO.get('mid', (0.78, 0.82))
S_MIDY  = _SO.get('midy', (0.42, 0.16))
S_WAIST = float(os.environ.get("ALBO_ROM_S_WAIST", _SO.get('waist', 0.0)))   # round 286: the waist raised by this x the x-height -- it shrinks the TOP space and grows the BOTTOM together
S_HEAD_X = float(os.environ.get("ALBO_ROM_S_HEAD_X", _SO.get("head", (0.93, 0.82))[0]))   # round 283: the head's reach, x the s's width -- 0.93 as drawn (owner, on the ladder: ".93/.82 wins"; round 282's per-weight reach is gone)
S_FOOT_X = float(os.environ.get("ALBO_ROM_S_FOOT_X", 0.11))   # round 283: the foot's reach, the head's mirrored about the apexes (0.42 - (0.93 - 0.62)); 0.06 before
S_FOOT_RATIO = float(os.environ.get("ALBO_S_FOOT_RATIO", _SO.get("ratio", 1.12)))   # round 284: the foot's end ink, x the head's -- "the bottom needs to be slightly bigger than the top"; both styles solve to this
S_HEAD_END = float(os.environ.get("ALBO_S_HEAD_END", 0.0))        # override: the head's end width x the foot's, fixed; 0 = solve for S_FOOT_RATIO
S_FOOT_RATIO_IT = float(os.environ.get("ALBO_S_FOOT_RATIO_IT", 1.30))   # round 286: the italic's own foot/head end ink. It rode the roman's option field until this line, so picking a roman option silently re-cut the italic's top; 1.30 is the value the owner's pick carries and it is stated here rather than inherited.
S_SMOOTH = float(os.environ.get("ALBO_ROM_S_SMOOTH", 0.6))   # round 283: the deburr -- the pen widths averaged over +/- this x the stem of path, above stem 84 (89 units at the 900); 0.35 leaves the nubs
S_HEAD_SPAN = float(os.environ.get("ALBO_S_HEAD_SPAN", PR.FINIAL_SPAN))   # round 284 ladder: the head's taper runs over this fraction of the path (the c's 0.13)
S_FOOT_SWELL = float(os.environ.get("ALBO_S_FOOT_SWELL", PR.FINIAL_SWELL))  # round 284 ladder: the foot's swell into its face (the c's 1.10)
S_HEAD_Y = float(os.environ.get("ALBO_ROM_S_HEAD_Y", _SO.get("head", (0.93, 0.82))[1]))   # round 282: the head's height, x the x-height (0.80 before)
@glyph('s')
def g_s(c):
    """One smooth spine on the pen's own widths (round 51's s: no spine
    boost -- that is the capital's rule).

    ROUND 282 -- BOTH ENDS ARE THE c's TOP FINIAL. Owner 2026-09-19: *"for
    round finial, c is fine but there needs to be parity with s in small
    scale rendering. right now it is too light and low on vertical grid."*
    Round 275 changed the roman's round finials out for the c's end and left
    this letter alone: its ends were the pen cut at 20 degrees with a 1.25
    flare over the last 12%, an oblique face that read light at 13 px and
    landed one pixel row under the c's. Now the family's finial on both ends
    (PR.finial_widths / PR.finial_cut, the head held to rounds.c_top_width()
    -- 60.8 at the 400, the c's own), the head's start raised 0.80 -> 0.82
    xh so its face tops out where the c's does (397 against 397).

    ROUND 285/286 -- THE FLOW, AND THE TWO SPACES. Owner 2026-09-19, on a
    page of five: *"b wins, but the space on the top loop needs to be reduced
    and the bottom space needs to increase."* Option b draws the UPPER bowl
    in toward the letter's axis (`S_UP` 0.88) so the lower bowl is the wider
    of the two -- the drawing before it had them equal at 0.994, which is
    what read stiff -- and trims the top terminal (S_FOOT_RATIO 1.30). His
    amendment is `S_WAIST`: the waist rides higher, which shrinks the top
    space and grows the bottom in one move, measured on the convex hull
    minus the ink. Laddered at +0.01 / +0.02 / +0.04 / +0.06 of the
    x-height, and his: *"plus .01 wins"* -- top over bottom 0.951 -> 0.90.
    The other options stay in S_OPTS as the record.

    ROUND 283 -- THE HEAD AS DRAWN, THE FOOT ITS EQUAL, AND NO BURRS. Owner,
    on a ladder of head starts: *".93/.82 wins"* -- the reach stays at 0.93
    (round 282 had stretched it to 1.04 and beyond, per weight, to keep the
    old width; that was the "top too heavy"), so the built s is 28 units
    narrower at the 400 than it was and the head tucks in over the bowl.
    *"the bottom needs to be optically equal to the top"*, then *"for all s,
    make the top equally or less visually heavy than the bottom"*, and in
    round 284 *"the bottom needs to be slightly bigger than the top"*: the
    foot's start is the head's mirrored about the two apexes (0.42 - 0.31 =
    0.11 of the width, from 0.06); the foot keeps the c's finial -- the 1.10
    swell, held to the c's end width -- and the head TAPERS into its face by
    however much `s_head_end` has to take off to leave the foot's end ink
    S_FOOT_RATIO (1.12) of the head's. Round 283's flat 0.85 made that ratio
    1.49 at the 400 and 1.55 at the 900, which is a difference rather than a
    slight one; the solve lands 0.98 / 0.96 at the light weights and takes
    nothing at all at the 700 and the 900, where the pen's own asymmetry
    already leaves the foot bigger. The italic s (aldine.a_s) solves the
    same way. *"deburr the 900 s"*: the
    Black's s stood a nub into each aperture. Not a fold (the tightest bend
    clears the half-width by 8 units) and not a sliver (an opening of radius
    10 took 18 square units off it): the pen's width climbs 54 -> 136 across
    the bend where the direction crosses the thin axis, and the inner offset
    of a width rising that fast on a bend that tight bulges. Above stem 84
    the pen widths are averaged over +/- S_SMOOTH x the stem of path
    (`_smooth_widths`, before the finials) -- 0.35 leaves the nubs, 0.6
    clears both; the 400 and the 200 keep the pen's own widths."""
    xh = c["xh"]; wf = c["wf"]; w = 370 * wf; o = OVER - TH_H / 2
    _ax = w * 0.50   # round 285: the upper bowl's two points reach toward this axis by S_UP
    _wq = S_WAIST * 0.35   # round 286: the two points either side of the waist move a third as far
    pts = [(w * S_HEAD_X, xh * S_HEAD_Y), (w * 0.62, xh + o * S_OVER),
           (_ax + (w * 0.20 - _ax) * S_UP, xh * (0.86 + _wq)), (_ax + (w * 0.22 - _ax) * S_UP, xh * (0.60 + S_WAIST)),
           (w * S_MID[0], xh * (S_MIDY[0] + S_WAIST)), (w * S_MID[1], xh * (S_MIDY[1] + _wq)), (w * 0.42, -o * 0.9), (w * S_FOOT_X, xh * 0.19)]
    spine = catmull(pts, tension=S_TENS)
    if PR.BOWL and PR.BOWL.get('widen'):
        prof = widen_terminal(widen_terminal(None, True), False)
        return geom.ink([stroke(spine, pen_widths(spine, prof), cut0=CUT, cut1=CUT)])
    from .rounds import c_top_width
    fl = c_top_width(); base = pen_widths(spine, None)
    if S > 84.0 and S_SMOOTH > 0.0: base = _smooth_widths(base, spine, S * S_SMOOTH)   # the deburr, see the docstring
    foot = PR.finial_widths(base, False, floor=fl, swell=S_FOOT_SWELL)   # the foot: the c's finial, held to the c's end width
    c0, c1 = PR.finial_cut(spine, True), PR.finial_cut(spine, False)
    def _mk(he):
        wf_ = PR.finial_widths(foot, True, floor=0.0, swell=he * foot(1.0) / foot(0.0), span=S_HEAD_SPAN)
        return stroke(spine, wf_, cut0=c0, cut1=c1), spine[0], spine[-1], wf_(0.0), wf_(1.0)
    return geom.ink([_mk(s_head_end(_mk))[0]])

def s_head_end(make, target=None, lo=0.80, hi=1.00, steps=9):
    """ROUND 284 -- how much smaller the s's HEAD is than its FOOT, solved
    rather than declared. Owner 2026-09-19: *"the bottom needs to be slightly
    bigger than the top."* Measured on the built stroke, the two ends are
    already unequal at equal END WIDTHS and not by a constant: the ink within
    a disc of the end's own width runs 3% more at the foot at the 200, 8% at
    the 400, 13% at the 700 and 16% at the 900, because the pen is wider
    where the foot leaves the bowl and the 28-degree face lies at a different
    angle across each. So a fixed multiplier (round 283's 0.85) made the foot
    half again the head's ink at the 400 and 55% more at the 900 -- a
    difference, not a slight one.

    `make(head_end)` returns (ink, head_point, foot_point, head_w, foot_w).
    This bisects head_end in [lo, hi] for foot_ink / head_ink == `target`,
    and the ceiling of 1.00 is load-bearing: where the pen's own asymmetry
    already exceeds the target (the 700 and the 900) the two ends take the
    same width and the foot is bigger by the pen alone."""
    from shapely.geometry import Point
    tgt = S_FOOT_RATIO if target is None else target
    if S_HEAD_END: return S_HEAD_END
    def ratio(he):
        ink, ph, pf, wh, wf_ = make(he)
        h = ink.intersection(Point(ph).buffer(wh * 0.8)).area
        f = ink.intersection(Point(pf).buffer(wf_ * 0.8)).area
        return (f / h) if h > 0 else tgt
    if ratio(hi) >= tgt: return hi          # the pen alone already does it
    a, b = lo, hi
    for _ in range(steps):
        m = (a + b) / 2
        if ratio(m) >= tgt: a = m
        else: b = m
    return (a + b) / 2

def _smooth_widths(f, center, win, N=600):
    """The width function `f(t)` box-averaged over +/- `win` units of the
    path (round 283's deburr for the s; the finials go on AFTER this so the
    ends keep their declared swells). At the 900 the pen runs 54 wide at
    t 0.2 and 136 at 0.4 -- the direction swings through the thin axis on
    the s's tightest bend -- and the inner offset of a width rising that fast
    on that bend bulges into the aperture; averaged over the stroke's own
    width of path it does not (69 / 131)."""
    from shapely.geometry import LineString
    L = LineString(geom.resample(center)).length; k = win / L
    ys = [f(i / N) for i in range(N + 1)]
    def g(t):
        lo = max(0, int((t - k) * N)); hi = min(N, int(math.ceil((t + k) * N)))
        return sum(ys[lo:hi + 1]) / (hi - lo + 1)
    return g

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
    #
    # ROUND 343 -- CLOSE THE CROTCH. Owner 2026-09-21, shown the four open gate
    # findings: *"yes to fixing, except y is supposed to have a gap"*. The b's
    # and p's are the same fault, a 6.4- and 4.5-unit spike of white where the
    # ring's outer meets the stem at a shallow angle -- `ink` adds the two
    # shapes and leaves a notch on one side, which is precisely what
    # `geom.close_corners` was written for (round 205, the g's joins).
    #
    # THE RADIUS IS BOUNDED BY THE y. A closing bridges any channel narrower
    # than 2r, and this face deliberately keeps a 7.2-7.9 unit hairline gap
    # (docs/albo-hairline-gap.md) -- so this is applied to the BOWL LETTERS
    # only, never globally, and r stays small.
    g_ = geom.ink([solid, st])
    return geom.close_corners(g_, BOWL_BLEND) if BOWL_BLEND else g_

@glyph('b')
def g_b(c): return bowl_stem(c, 'left', c["asc"], 0)
@glyph('d')
def g_d(c): return bowl_stem(c, 'right', c["asc"], 0)
@glyph('p')
def g_p(c): return bowl_stem(c, 'left', c["xh"], -c["desc"])
@glyph('q')
def g_q(c): return bowl_stem(c, 'right', c["xh"], -c["desc"])

# ===================== ROUND 324 -- THE BENT ROMAN g =======================
# Owner 2026-09-21: *"make a roman version of this, but reduce the lower loop
# top heaviness"*, `this` being the italic's cursive g restored in round 323.
#
# WHAT MAKES THAT LETTER what it is, measured rather than described. Its loop
# is WIDE AND SHALLOW where the roman's is a near-circle under a near-circle
# (loop/bowl counter 1.55 wide and 0.88 tall against the roman's 1.17/1.06),
# and its connector DIVES left out of the bowl and bends into the loop rather
# than running down the letter's left wall. Both are rebuilt here on the
# roman's own pen and proportions; nothing is ported from `aldine`.
#
# THE LOOP'S STRESS IS THE THIRD DIFFERENCE and it is the one the owner is
# pointing at. Wall thickness round the lower loop, ray-cast from its counter's
# centroid, 0 = east and 90 = TOP, in Albo units:
#
#              0    30    60    90   120   150   180   210   240   270   300   330
#   roman     69    54    37    33    38    53    68    54    38    34    39    53
#   italic    68    89    88    69    26    30    69    85    65    40    27    32
#   Flanker   48    69    71    82    27    48    35    61    35    24    21    27
#   Pagella   67    80    78   103    24    39    62    60    37    27    26    34
#
# The roman's ring is symmetric with its thicks due EAST and WEST -- a
# vertically stressed bowl, which is right for an o and wrong for this loop.
# The italic and both references put the weight through the UPPER LEFT, and
# the italic carries 89 and 88 at 30 and 60 degrees where the references carry
# 69-71 and 78-80. That upper-right shoulder, where the connector lands, is
# the heaviness; G_BENT_TOP_W cuts it, centred on G_BENT_TOP_AT and falling to
# nothing over G_BENT_TOP_ARC, so the rest of the ring is untouched.
# SHIPS. Owner 2026-09-21: *"need a roman bent g. please do what I keep
# asking."* Round 324 built this and left it behind the flag; that was the
# mistake. `plain` is the letter that shipped up to round 324.
# SHIPS OPEN. Owner 2026-09-21: *"ship open as default for roman, and closed
# for italic"*. The roman's g is the single-storey letter built as the q with
# a hooked foot (round 331), on the traced Futura tail (round 328) at
# TRACE_X 1.14; the ITALIC keeps the closed binocular one, which is a separate
# construction in `aldine` and is not touched by this. 'bent' is the
# two-storey roman of rounds 324-332, 'plain' the one before it.
G_STYLE = os.environ.get("ALBO_G_STYLE", "open").lower()       # open (ships) | bent | plain
G_BENT_LOOP_RX = float(os.environ.get("ALBO_G_BENT_LOOP_RX", 205.0))  # wf units, against the plain g's 190
G_BENT_LOOP_H = float(os.environ.get("ALBO_G_BENT_LOOP_H", 0.40))     # x the descender, against 0.50
G_BENT_LOOP_DX = float(os.environ.get("ALBO_G_BENT_LOOP_DX", -4.0))
# MEASURED AND LEFT AT ZERO. Rotating the tangent handed to `bowl_th` does
# NOT rotate the ring's stress: at phi 0, 14 and -14 the wall reads 67/50/37
# /33, 66/44/36/36 and 65/58/44/36 at 0/30/60/90 -- the thick stays due east
# and west whatever it is set to. The family's bowl profile is a function of
# how vertical the tangent is (round 58's switch), not of a nib angle, so
# this lever cannot do what its name suggests and the dial is kept only so
# the next person does not re-derive that.
G_BENT_PHI = float(os.environ.get("ALBO_G_BENT_PHI", 0.0))
# AND THE HEAVINESS IS AT 150, NOT 55. Aiming the cut at the upper RIGHT (55)
# was reading the reference italics' geometry onto a letter whose connector
# lands somewhere else: their neck comes down the middle into the loop's
# top, this one dives left and enters at G_BENT_TO. The mass is where the
# connector lands, so that is where the cut goes.
G_BENT_TOP_W = float(os.environ.get("ALBO_G_BENT_TOP_W", 0.65))   # x the ring's own width, at the shoulder; 79 -> 63 units at 150 deg
# Follows the entry: with the connector landing at 105 the mass sits at 120,
# not the 150 it sat at when the neck came in down the loop's left side.
G_BENT_TOP_AT = float(os.environ.get("ALBO_G_BENT_TOP_AT", 120.0))  # where that cut is centred, degrees
G_BENT_TOP_ARC = float(os.environ.get("ALBO_G_BENT_TOP_ARC", 85.0))  # and how far it reaches
G_BENT_FROM = float(os.environ.get("ALBO_G_BENT_FROM", 256.0))  # the neck leaves the bowl here
# ROUND 326 -- THE ENTRY ANGLE IS WHAT MAKES THE REVERSE BEND, and 163 could
# not. Traced by connectivity (the row under the bowl counter, then the
# overlapping run down), the connector's centre x against depth reads:
#   italic   leftmost -97 at t 0.49, back to -22   <- an S
#   Flanker  leftmost -117 at t 0.45, back to -35  <- an S
#   roman    leftmost -161 at t 0.94               <- a one-way diagonal
# Entering at 163 degrees IS the loop's far left, so the path can only keep
# going left and there is nothing to reverse. The reference letters enter near
# the loop's TOP, dive left halfway down and sweep back. At 105 with the dive
# at 0.60 the roman reads leftmost -84 at t 0.52.
G_BENT_TO = float(os.environ.get("ALBO_G_BENT_TO", 105.0))      # and enters the loop here
# 0.42 was the first value and it FAILS the contour gate: the diving neck
# grazes the loop's outer left edge and leaves a HAIR at (107, 9) -- a
# reversal past 150 degrees with a sub-8-unit arm, which the plain g does not
# have. 0.36 clears it, and so does entering the loop at 172 instead of 163;
# the dive is the cheaper of the two because the entry angle is what gives
# the elbow its shape.
G_BENT_DIVE = float(os.environ.get("ALBO_G_BENT_DIVE", 0.60))   # how far LEFT it dives, x the gap
G_BENT_DROP = float(os.environ.get("ALBO_G_BENT_DROP", 0.52))   # and how far down before it turns
G_BENT_WAIST_K = float(os.environ.get("ALBO_G_BENT_WAIST_K", 0.30))  # the vertical handle at the waist, x the gap
G_BENT_LEAD = float(os.environ.get("ALBO_G_BENT_LEAD", 0.16))   # how far left the stroke leans as it leaves the bowl
G_BENT_LAND = float(os.environ.get("ALBO_G_BENT_LAND", 0.10))   # and how it comes in to the loop
# ROUND 327 -- THE LOOP RESTS ON THE BASELINE. Owner: *"top rest on baseline
# not above"*. `G_LOOP_TOP` is TH_H for the plain g -- round 232's reading of
# "sit on the baseline" as the top stroke STANDING on the line, its underside
# touching. This is the other reading and it is the one he wants for this
# letter: the loop's topmost point AT the baseline. The plain g is untouched.
G_BENT_LOOP_TOP = float(os.environ.get("ALBO_G_BENT_LOOP_TOP", 0.0))


def _bent_loop(lcx, lcy, lrx, lry):
    """The lower loop as a ring whose width is the pen's, rotated to
    G_BENT_PHI, with the upper shoulder cut back by G_BENT_TOP_W."""
    outer = superellipse(lcx, lcy, lrx, lry, 0.0, 2 * math.pi, BOWL_K)[:-1]
    outer = geom.resample(outer + [outer[0]])[:-1]
    tans = geom.tangents(outer, closed=True)
    a = math.radians(G_BENT_PHI); ca, sa = math.cos(a), math.sin(a)
    ws = []
    for pt, tn in zip(outer, tans):
        w = PR.bowl_th((tn[0] * ca - tn[1] * sa, tn[0] * sa + tn[1] * ca))
        ang = math.degrees(math.atan2(pt[1] - lcy, pt[0] - lcx)) % 360.0
        d = abs((ang - G_BENT_TOP_AT + 180.0) % 360.0 - 180.0)
        if d < G_BENT_TOP_ARC:           # a raised cosine, so the cut has no edge
            f = 0.5 * (1.0 + math.cos(math.pi * d / G_BENT_TOP_ARC))
            w *= 1.0 - (1.0 - G_BENT_TOP_W) * f
        ws.append(w)
    n = len(ws)
    return ring_from(outer, widths_fn=lambda t: ws[min(n - 1, max(0, int(round(t * n))))])


def _g_bent(c):
    """The roman g with the italic's bent connector and wide shallow loop.
    The bowl and the ear are `g_g`'s, unchanged."""
    xh = c["xh"]; wf = c["wf"]; desc = c["desc"]
    rx = 172 * wf + TH_V / 2; ry = (xh * 0.66 + OVER * 2) / 2
    cy = xh + OVER - ry; cx = rx + S * 0.35
    bowl, bo, bi = ring(cx, cy, rx, ry)
    lrx = G_BENT_LOOP_RX * wf + TH_V / 2
    lry = desc * G_BENT_LOOP_H + TH_H / 2
    lcx = cx + G_BENT_LOOP_DX * wf; lcy = G_BENT_LOOP_TOP - lry
    loop, lo, li = _bent_loop(lcx, lcy, lrx, lry)
    crx, cry = rx - TH_V / 2, ry - TH_H / 2
    clrx, clry = lrx - TH_V / 2, lry - TH_H / 2
    def on(cx_, cy_, rx_, ry_, deg):
        a = math.radians(deg); return (cx_ + rx_ * math.cos(a), cy_ + ry_ * math.sin(a))
    p0 = on(cx, cy, crx, cry, G_BENT_FROM)
    p3 = on(lcx, lcy, clrx, clry, G_BENT_TO)
    gap = p0[1] - p3[1]
    # The BEND: out of the bowl, down and LEFT past the loop's own left edge,
    # then back right into the loop. A cubic through those two controls is the
    # elbow; catmull would round it away, and the elbow is the whole point.
    # ROUND 327 -- THE CONNECTOR IS TWO CUBICS THROUGH AN EXPLICIT WAIST.
    # Owner 2026-09-21, on his own dragged params: *"no kink in connector;
    # _DIVE is not going left enough"*. Both are the same fault. A single cubic
    # with one runaway handle does not move its curve left in proportion to the
    # handle -- past about 0.7 it FOLDS, and the traced leftmost point jumped
    # from t 0.52 back to t 0.92 while the letter grew a kink. So the dial
    # saturated and produced a defect at the same time.
    #
    # AT THE LEFTMOST POINT OF AN S THE TANGENT IS VERTICAL, because x is at a
    # minimum there. That is a constraint, not a preference, and it is what
    # makes this construction safe: the waist is placed directly, both cubics
    # meet it with a vertical tangent, so the join is C1 by construction and
    # cannot kink however far left the waist goes. G_BENT_DIVE is now a literal
    # distance -- the waist's offset left of the bowl exit, x the gap.
    wx = p0[0] - gap * G_BENT_DIVE
    wy = p0[1] - gap * G_BENT_DROP
    k = gap * G_BENT_WAIST_K
    seg1 = cubic(p0, (p0[0] - gap * G_BENT_LEAD, p0[1] - gap * 0.18),
                 (wx, wy + k), (wx, wy))
    seg2 = cubic((wx, wy), (wx, wy - k),
                 (p3[0] - gap * G_BENT_LAND, p3[1] + gap * 0.26), p3)
    neck = list(seg1) + list(seg2)[1:]
    nk = stroke(neck, PR.bowl_widths(neck, widths([(0.0, 0.30), (0.16, 0.9),
                                                   (0.45, G_NECK_MID),
                                                   (0.85, 0.9 * min(1.0, G_NECK_END / 0.30)),
                                                   (1.0, G_NECK_END)]),
                                     floor=S * G_NECK))
    ex, ey = on(cx, cy, crx, cry, 44); L = 96 * wf * g_ear_scale()
    ear_c = [(ex, ey), (ex + L, ey + L * math.tan(math.radians(8)))]
    ear = stroke(ear_c, PR.bowl_widths(ear_c, widths([(0.0, 0.4), (0.35, 1.0), (1.0, 1.05)]),
                                       floor=S * 0.72), cut1=CUT)
    return geom.ink([bowl, loop, nk, ear])


# ===================== ROUND 327 -- THE OPEN-LOOP ROMAN g ==================
# THIS IS WHAT SHIPS since round 335 (ALBO_G_STYLE defaults to `open`). The
# header below is from when it did not, and was wrong for six rounds:
# EXPLORATION ONLY, behind ALBO_G_STYLE=open. Nothing here ships: `bent` is
# still the default and an unset build is byte-identical (proved by comparing
# every glyph's RecordingPen output, never the TTF's md5 -- fontTools stamps
# head.modified, so md5 never compares across two builds).
#
# Owner 2026-09-21: *"make an open loop 'g' in roman based on other albo roman
# lowercase. take ten passes at giving me a variety of options."*
#
# WHAT AN OPEN-LOOP g IS, structurally, IN THIS FACE. It is the `q`'s skeleton
# with the stem's foot replaced by a hook: a FULL x-height bowl -- the o's
# ring, not the binocular g's 0.66-xh bowl -- whose right wall carries on past
# the baseline and curls. Every part below is one this face already owns:
#
#   the bowl    `ring()` at the o's centreline radius, its weight and its
#               hairline floor (rounds.O_RX x O_RX_ADJ, O_W_ADJ, O_FLOOR_ADJ)
#   the tail    a stroke on `PR.bowl_widths` -- the same profile the o's ring,
#               the a's hood and the e's arm are drawn on
#   its end     the j's run-out to a point; the c's lower terminal (0.70 of
#               the pen into the family's 20-degree cut); the c's TOP finial
#               with the y-tail's floor (PR.finial_widths / PR.finial_cut /
#               rounds.c_top_width); the v/y/x diagonal end wedge
#               (PR.end_wedge)
#   the ear     g_g's ear, unchanged, moved, or absent
#
# THE ONE RULE (docs/albo-method.md section 1) decides the root, and it is the
# only thing here that is not taste. The tail leaves the bowl ON THE RING'S
# OWN CENTRELINE, with the RING'S OWN CLOCKWISE TANGENT and the RING'S OWN
# WIDTH there (G_OPEN_W0 = 1.0 means `bowl_th` of that tangent). That is what
# makes the union tangent-continuous -- section 1b: a union ADDS, it does not
# blend, and two edges that arrive at an angle leave a notch on one side and a
# spur on the other that no width can tune away. Rooting the tail anywhere
# else, or at any other width, puts a step on the letter's right edge where
# the descender leaves. The negative results are in
# docs/albo-open-g-2026-09-21.md.


def _open_on(cx, cy, rx, ry, deg):
    a = math.radians(deg); return (cx + rx * math.cos(a), cy + ry * math.sin(a))


def _open_tan(rx, ry, deg):
    """The ring's CLOCKWISE tangent at `deg` -- the direction a stroke running
    DOWN the bowl's right wall is already travelling when it reaches there."""
    a = math.radians(deg)
    tx, ty = rx * math.sin(a), -ry * math.cos(a)
    L = math.hypot(tx, ty) or 1.0
    return (tx / L, ty / L)


def _open_arc(P0, T0, r, sweep_deg, n=72):
    """The j's tail: a circular arc leaving P0 along T0. A POSITIVE sweep turns
    the stroke clockwise on the page (down, then left -- the j's hook); a
    negative one turns it the other way (down, then right)."""
    s = 1.0 if sweep_deg >= 0 else -1.0
    ccx, ccy = P0[0] + s * T0[1] * r, P0[1] - s * T0[0] * r
    a0 = math.atan2(P0[1] - ccy, P0[0] - ccx)
    sw = s * math.radians(abs(sweep_deg))
    return [(ccx + r * math.cos(a0 - sw * i / n), ccy + r * math.sin(a0 - sw * i / n))
            for i in range(n + 1)]


# ---- the dials. Every one takes an ALBO_G_OPEN_* env override, and every one
# ---- of the ten options below is a row in this same table, so an option is a
# ---- set of dial values and never a separate code path.
#
#   rx      the bowl's centreline radius, x the o's own (rounds.O_RX x
#           O_RX_ADJ). 1.00 IS the o; the o is 1.036 wide over tall and a g
#           carrying a descender on its right wall reads wider than that.
#   frm     where the tail leaves the ring, degrees, 0 = due east (the bowl's
#           widest point, where the wall runs vertical and the departure is
#           straight down). NEGATIVE goes round the bottom-right.
#   kind    'arc' -- a straight run along the ring's tangent for `run`, then a
#           circular turn of radius `r` through `sweep` degrees: the j's own
#           construction. 'cubic' -- one curve to a tip declared by `reach`
#           (x, in ring-centreline radii from the bowl's centre), `depth` (y,
#           x the descender, positive = below the baseline) and `tipdeg` (the
#           direction of travel at the tip), with `c1`/`c2` the two handle
#           lengths as fractions of the chord: the y's and the e's.
#   prof    the tail's width, x `bowl_th` of its own tangent -- so `prof` is
#           taste and the DIRECTION carries the contrast (THE ONE RULE).
#   floor   the least width the tail may have, x the stem.
#   end     'point' | 'cut' | 'finial' | 'wedge' -- see the doc block above.
#   ear     'g' the binocular g's ear unchanged | 'none'.
#   ear_at  where it is rooted on the ring, degrees.
G_OPEN_OPTS = {
    # 1. THE j's TAIL. The face's own descender, transplanted: down the bowl's
    #    right wall, then the j's circular turn (its own radius, its own 118
    #    degrees of sweep), running out to a point. Rooted HIGH (-10) so the
    #    descender IS the bowl's right wall rather than a stroke hung off it.
    'j':     dict(rx=0.94, frm=-10.0, kind='arc', run=0.74, r=125.0, sweep=118.0,
                  prof=[(0.0, 1.00), (0.42, 0.94), (1.0, 0.18)], floor=0.0,
                  end='point', ear='g'),
    # 2. THE y's TAIL. One long cubic sweeping left across the whole letter and
    #    ending in the c's top finial on the y's own floor -- the roman y's
    #    tail, aimed at the g's root. The widest reach of the ten.
    # ROUND 328 -- THE TRACED TAILS. Each is one of the eight measured models,
    # run at the face's own descender with the face's own pen. The shape is not
    # mine and not a dial's: it is that font's descender centreline.
    'futura':    dict(rx=0.94, frm=-14.0, kind='trace', trace='futura',
                      prof=[(0.0, 1.00), (0.45, 0.90), (1.0, 0.72)],
                      floor=0.0, end='cut', ear='g'),
    'avenir':    dict(rx=0.94, frm=-14.0, kind='trace', trace='avenir',
                      prof=[(0.0, 1.00), (0.45, 0.90), (1.0, 0.72)],
                      floor=0.0, end='cut', ear='g'),
    'helvetica': dict(rx=0.94, frm=-14.0, kind='trace', trace='helvetica',
                      prof=[(0.0, 1.00), (0.45, 0.90), (1.0, 0.72)],
                      floor=0.0, end='cut', ear='g'),
    'verdana':   dict(rx=0.94, frm=-14.0, kind='trace', trace='verdana',
                      prof=[(0.0, 1.00), (0.45, 0.90), (1.0, 0.72)],
                      floor=0.0, end='cut', ear='g'),
    'din':       dict(rx=0.94, frm=-14.0, kind='trace', trace='din',
                      prof=[(0.0, 1.00), (0.45, 0.90), (1.0, 0.72)],
                      floor=0.0, end='cut', ear='g'),
    'y':     dict(rx=0.94, frm=-14.0, kind='cubic', reach=-0.92, depth=0.86, tipdeg=163.0,
                  c1=0.62, c2=0.52, prof=[(0.0, 1.00), (0.30, 0.92), (1.0, 0.86)],
                  floor=0.0, end='finial', ear='g'),
    # 3. THE c's LOWER TERMINAL, short and shallow. A stub hook that thins to
    #    0.70 of the pen and stops on the family's 20-degree cut, which is
    #    exactly how the c's bottom ends. The shallowest of the ten.
    'c':     dict(rx=0.94, frm=-16.0, kind='cubic', reach=-0.34, depth=0.60, tipdeg=188.0,
                  c1=0.58, c2=0.42, prof=[(0.0, 1.00), (0.45, 0.95), (1.0, 0.70)],
                  floor=0.0, end='cut', ear='g'),
    # 4. THE WEDGE. A medium hook stopped by a SERIF rather than by a taper:
    #    the v/y/x diagonal end wedge. Side -1 (the UPPER corner, an upturned
    #    flag) after a ladder: on the lower corner at 0.90 and 0.60 the wedge
    #    hangs off the tip as a droop, which reads as a fault rather than as
    #    a serif. The stroke also has to arrive near full width (prof ends at
    #    0.98) or there is nothing for the wedge to sit on.
    'wedge': dict(rx=0.94, frm=-12.0, kind='cubic', reach=-0.52, depth=0.74, tipdeg=170.0,
                  c1=0.66, c2=0.44, prof=[(0.0, 1.00), (0.40, 0.94), (1.0, 0.98)],
                  floor=0.0, end='wedge', wedge_side=-1, wedge_scale=0.75, ear='g'),
    # 5. DEEP. The full descender -- the p's own -281 -- taken in one near
    #    vertical drop with a late, tight turn. The depth axis at its maximum.
    'deep':  dict(rx=0.94, frm=-8.0, kind='cubic', reach=-0.28, depth=0.98, tipdeg=198.0,
                  c1=0.80, c2=0.30, prof=[(0.0, 1.00), (0.55, 0.92), (1.0, 0.44)],
                  floor=0.0, end='cut', ear='g'),
    # 6. PART-CLOSED. The hook curls left, turns, and comes back up so the
    #    letter reads as a loop that was never shut: measured mouth 66 units
    #    (the shortest white from the tip to the bowl or to the tail's own
    #    first 60%). A tip aimed further round than this FOLDS -- see the
    #    negative results at the foot of this block.
    'curl':  dict(rx=0.94, frm=-12.0, kind='cubic', reach=-0.56, depth=0.44, tipdeg=56.0,
                  c1=0.84, c2=0.54, prof=[(0.0, 1.00), (0.40, 0.92), (1.0, 0.52)],
                  floor=0.0, end='cut', ear='g'),
    # 7. HOOKS RIGHT. Down, then OUT to the right and up, ending in the c's
    #    finial -- the e's arm direction given to a descender. The only one of
    #    the ten whose tail leaves the bowl's own footprint on the right.
    'out':   dict(rx=0.94, frm=-20.0, kind='cubic', reach=1.30, depth=0.80, tipdeg=52.0,
                  c1=0.74, c2=0.54, prof=[(0.0, 1.00), (0.45, 0.88), (1.0, 0.74)],
                  floor=0.0, end='finial', ear='g'),
    # 8. THE o's BOWL, exactly (rx 1.00), with a restrained hook so the bowl is
    #    what the eye is asked about. The bowl axis.
    'o':     dict(rx=1.00, frm=-10.0, kind='cubic', reach=-0.44, depth=0.90, tipdeg=174.0,
                  c1=0.70, c2=0.46, prof=[(0.0, 1.00), (0.42, 0.92), (1.0, 0.62)],
                  floor=0.0, end='cut', ear='g'),
    # 9. THE HAIRLINE. The tail resolves the way a pen LIFTS: no floor and a
    #    profile that lets the run-out reach the bowl's own hair. The contrast
    #    axis -- and the one most at risk from the four-level pipeline at 13 px,
    #    which is the size he reads at (rounds.O_FLOOR_ADJ's ruling).
    'hair':  dict(rx=0.94, frm=-12.0, kind='cubic', reach=-0.66, depth=0.90, tipdeg=168.0,
                  c1=0.70, c2=0.50, prof=[(0.0, 1.00), (0.34, 0.86), (0.72, 0.52), (1.0, 0.30)],
                  floor=0.0, end='cut', ear='g'),
    # 10. NO EAR. The canonical single-storey g: the bowl and the tail and
    #     nothing else. The ear axis, and the arm that says what the ear is
    #     actually worth on a letter this shape.
    'bare':  dict(rx=0.94, frm=-12.0, kind='cubic', reach=-0.56, depth=0.90, tipdeg=168.0,
                  c1=0.70, c2=0.48, prof=[(0.0, 1.00), (0.40, 0.92), (1.0, 0.66)],
                  floor=0.0, end='finial', ear='none'),
}
# THE DEFAULT IS THE TRACED LETTER, not the first row of the table. `j` was
# the open-g exploration's own default and it is NOT what any ruling was made
# on: the counter (393 / 19 / 17, round 332) and the hook (TRACE_X 1.14,
# round 334) were both dialled and measured on `futura`. Round 335 shipped
# the roman without naming a row and therefore shipped `j` -- a letter with
# a different tail and terminal from every figure the owner approved.
G_OPEN = os.environ.get("ALBO_G_OPEN", "futura").lower()
if G_OPEN not in G_OPEN_OPTS: G_OPEN = "j"
_GO = dict(G_OPEN_OPTS[G_OPEN])
# ===================== ROUND 328 -- THE TAIL IS TRACED ====================
# Owner 2026-09-21: *"needs to hook back up like a 'g' typically does. you are
# making weird tails on an 'o' instead. stop and do much better based on traced
# models of other fonts."* Correct on every count, and the numbers say so.
#
# Eight single-storey sans g's had their DESCENDER CENTRELINE traced --
# skeletonised, the run at or below the baseline ordered from the bowl to the
# tip (`scratchpad/albo/tailtrace.py`). Every one has the same three-part
# shape, and none of the ten hand-dialled arms had it:
#
#                      deepest at x   tip x    tip y    RISE back up
#   the eight traced      -14..+17   -147..-190   -59..-147      17..113
#   the ten dialled       -49..+177   -53..-184  -207..-267       0..77
#
# The tail goes down the bowl's RIGHT, reaches its deepest point under the
# bowl's CENTRE, and then travels left and BACK UP. The dialled arms put their
# deepest point off to one side and ended within 20-60 units of the bottom --
# they descend and stop, which is why they read as a tail stuck on an o.
#
# The tables are the traces themselves, normalised so each model's own depth is
# 1.0 and x is in the same units, measured from the bowl's centre with +y up
# and the baseline at 0. They are a MEASUREMENT of eight faces, frozen here for
# the same reason the alt051 spine is frozen: re-deriving them per build would
# make the letter depend on which fonts this machine has installed.
G_OPEN_TAILS = {
    'futura': [(+0.873, +0.007), (+0.840, -0.372), (+0.750, -0.632), (+0.657, -0.766), (+0.579, -0.840), (+0.360, -0.955), (-0.012, -1.000), (-0.224, -0.974), (-0.361, -0.933), (-0.480, -0.870), (-0.610, -0.758), (-0.700, -0.628), (-0.748, -0.506)],
    'avenir': [(+0.977, +0.007), (+0.958, -0.220), (+0.922, -0.383), (+0.796, -0.643), (+0.601, -0.830), (+0.464, -0.906), (+0.323, -0.957), (-0.060, -1.000), (-0.316, -0.978), (-0.518, -0.924), (-0.710, -0.834), (-0.901, -0.690), (-0.897, -0.509)],
    'avenirnext': [(+1.084, +0.009), (+1.004, -0.371), (+0.920, -0.545), (+0.817, -0.681), (+0.709, -0.779), (+0.563, -0.869), (+0.422, -0.925), (+0.239, -0.967), (-0.075, -1.000), (-0.437, -0.972), (-0.728, -0.920), (-0.981, -0.831), (-1.000, -0.822), (-1.047, -0.671), (-1.108, -0.343)],
    'verdana': [(+1.098, +0.011), (+1.050, -0.303), (+0.947, -0.546), (+0.855, -0.670), (+0.763, -0.757), (+0.579, -0.870), (+0.368, -0.946), (-0.069, -1.000), (-0.491, -0.984), (-0.940, -0.897)],
    'trebuchet': [(+1.074, +0.010), (+1.131, -0.275), (+1.063, -0.565), (+1.001, -0.663), (+0.892, -0.767), (+0.633, -0.907), (+0.333, -0.979), (-0.030, -1.000), (-0.429, -0.943), (-0.621, -0.881), (-0.797, -0.798), (-0.983, -0.834)],
    'helvetica': [(+0.984, +0.009), (+0.925, -0.365), (+0.825, -0.607), (+0.751, -0.708), (+0.628, -0.822), (+0.487, -0.904), (+0.345, -0.954), (+0.012, -1.000), (-0.267, -0.986), (-0.431, -0.954), (-0.600, -0.886), (-0.710, -0.813), (-0.819, -0.685), (-0.879, -0.548)],
    'din': [(+0.941, +0.010), (+0.884, -0.380), (+0.785, -0.594), (+0.618, -0.776), (+0.384, -0.911), (+0.197, -0.964), (-0.095, -1.000), (-0.439, -0.948), (-0.710, -0.818), (-1.038, -0.807)],
    'sfrounded': [(+1.207, +0.011), (+1.163, -0.287), (+1.075, -0.497), (+1.003, -0.602), (+0.887, -0.724), (+0.776, -0.807), (+0.611, -0.895), (+0.417, -0.956), (-0.047, -1.000), (-0.400, -0.950), (-0.533, -0.906), (-0.782, -0.762), (-0.986, -0.575), (-1.069, -0.470)],
}

G_OPEN_TRACE     = os.environ.get("ALBO_G_OPEN_TRACE", _GO.get('trace', "futura"))
G_OPEN_TRACE_DEP = float(os.environ.get("ALBO_G_OPEN_TRACE_DEP", 1.0))  # x the face's own descender
# SHIPS AT 1.14. Owner 2026-09-21, after the round-334 ladder: *"ship 1.14"*.
# The hook reaches 191 units left of the counter's centre where the counter
# itself reaches 149, so the hook now carries past the bowl's own reach --
# which is the point: an OPEN curve reads smaller than a closed ring at the
# same span, and he is matching what the two look like rather than what they
# measure. 1.0 rebuilds the traced models untouched.
G_OPEN_TRACE_X   = float(os.environ.get("ALBO_G_OPEN_TRACE_X", 1.14))   # widen or narrow the tail's sweep


def _traced_tail(root, dep, wf, cx):
    """The chosen model, scaled to `dep` and hung off `root` (the point where
    the tail leaves the ring). Uniform in y so the model's own proportions
    survive; G_OPEN_TRACE_X is the one liberty, and it defaults to none."""
    tab = G_OPEN_TAILS.get(G_OPEN_TRACE) or G_OPEN_TAILS['futura']
    p0x, p0y = tab[0]
    # The model's own start sits ON the baseline; Albo's root is wherever the
    # ring is at G_OPEN_FROM, which is well ABOVE it. Anchoring the first point
    # and scaling by the descender therefore hung the whole tail high -- the
    # built letters measured 118 units deep against a 280 target and their tips
    # came back up to the baseline. The scale is taken from the root DOWN to
    # the descender line instead, so the model's deepest point lands on it.
    span = p0y - min(y for _, y in tab)
    ky = (root[1] + dep) / span if span > 1e-6 else dep
    # X IS NOT ON THE SAME SCALE AS Y. The model's x is in units of its own
    # depth but it MEANS bowl-relative position -- its first point is the
    # bowl's right edge. Scaling x by the vertical factor made the model's
    # +-1.0 into +-441 units and the tails ran to x -715 against a -190 target.
    # The start is matched to Albo's own ring instead.
    kx = (root[0] - cx) / p0x if abs(p0x) > 1e-6 else ky
    pts = [(root[0] + (x - p0x) * kx * G_OPEN_TRACE_X,
            root[1] + (y - p0y) * ky) for x, y in tab]
    return catmull(pts, tension=0.5)


_gof = lambda k, d: float(os.environ.get("ALBO_G_OPEN_" + k.upper(), _GO.get(k, d)))
G_OPEN_RX      = _gof('rx', 0.94)
G_OPEN_FROM    = _gof('frm', -12.0)
G_OPEN_KIND    = os.environ.get("ALBO_G_OPEN_KIND", _GO.get('kind', 'cubic'))
G_OPEN_RUN     = _gof('run', 0.74)       # 'arc': the straight run, x the drop from the root to the descender line
G_OPEN_R       = _gof('r', 125.0)        # 'arc': the turn's radius, wf units (the j's own)
G_OPEN_SWEEP   = _gof('sweep', 118.0)    # 'arc': degrees of turn (the j's own)
G_OPEN_REACH   = _gof('reach', -0.52)    # 'cubic': the tip's x, in ring-centreline radii from the bowl's centre
G_OPEN_DEPTH   = _gof('depth', 0.76)     # 'cubic': the tip's y, x the descender, BELOW the baseline
G_OPEN_TIPDEG  = _gof('tipdeg', 166.0)   # 'cubic': the direction of travel at the tip
G_OPEN_C1      = _gof('c1', 0.70)        # 'cubic': the handle along the ring's tangent, x the chord
G_OPEN_C2      = _gof('c2', 0.48)        # 'cubic': the handle back from the tip, x the chord
G_OPEN_W0      = _gof('w0', 1.00)        # the tail's width AT THE ROOT, x the ring's own width there. 1.0 is THE ONE RULE; anything else steps.
G_OPEN_FLOOR   = _gof('floor', 0.0)      # the tail's least width, x the stem
G_OPEN_END     = os.environ.get("ALBO_G_OPEN_END", _GO.get('end', 'cut'))
G_OPEN_WSIDE   = _gof('wedge_side', -1.0)    # 'wedge': which corner of the tail's end the serif sits on (-1 = upper, the one that works)
G_OPEN_WSCALE  = _gof('wedge_scale', 0.75)   # ... and its size, x the family's diagonal end wedge
# THE SHOULDER CUT, and the fault it exists for. Rooting the tail on the
# ring's centreline makes the departure tangent-continuous (above), but BELOW
# the root the two run side by side: the ring's centreline turns left toward
# the bowl's floor while the tail carries on down, so the union spans from the
# ring's inner edge to the tail's outer one. Measured PERPENDICULAR (a chamfer
# ridge on a ray from the counter's centroid -- the row-wise measure inflates
# on a slanted stroke, which is the trap docs/albo-g-anatomy.md round 323
# records for the g's waist), first cut against the o's own ring:
#
#     deg        0    45   285   300   315   330   345
#     the o     71    57    40    48    57    68    72
#     first g   73    67    41    49    93    80    75      <- +63% at 315
#
# The cure is the p's, not a new one: `bowl_stem` eases the ring's stroke to
# NEAR_STEM_W within 90 units of the stem's edge so the crotches clear, and
# the a's bowl does the same thing at its own stem. Here the ring's width is
# cut on a raised cosine centred on G_OPEN_CUT_AT -- the same shape round 324
# gave the bent g's loop shoulder -- so the tail carries the weight through
# the sector it shares with the ring and the rest of the ring is untouched.
# At 1.0 the bowl is the o's ring exactly.
G_OPEN_CUT_W   = _gof('cut_w', 0.55)     # the ring's width through the shared sector, x its own
G_OPEN_CUT_AT  = _gof('cut_at', 310.0)   # where the cut is centred, degrees (0 = due east)
G_OPEN_CUT_ARC = _gof('cut_arc', 36.0)   # and how far it reaches either side
G_OPEN_EAR     = os.environ.get("ALBO_G_OPEN_EAR", _GO.get('ear', 'g'))
# WHERE THE EAR SITS. g_g roots its ear at 44 degrees, on a bowl only 0.66
# of the x-height tall; on a FULL x-height bowl the same 44 degrees is a
# different place on the letter, and at 30 / 44 / 58 / 70 the ear reads as a
# nub on the right wall / a spur / an ear on the shoulder / a flag off the
# crown. 52 is where it sits on the shoulder, which is where the binocular
# g's own ear sits relative to ITS bowl (0.61 of the way up from the bowl's
# centre; 44 degrees here is 0.64, 52 is 0.79 -- so the angle that matches
# the PLACE is not the angle that matches the number).
G_OPEN_EAR_AT  = _gof('ear_at', 52.0)
G_OPEN_SER_AT    = _gof('ser_at', 38.0)     # where the bpqd serif stands on the ring, degrees
G_OPEN_SER_LEN   = _gof('ser_len', 1.05)    # the stub's height, x the stem
G_OPEN_SER_SCALE = _gof('ser_scale', 1.0)   # the wedge's size, x the family's
G_OPEN_SER_OVER  = _gof('ser_over', 1.0)
G_OPEN_SER_ALIGN = os.environ.get('ALBO_G_OPEN_SER_ALIGN', 'clip')   # ring | x | clip    # how much of the overshoot the stub's top takes    # where the ear is rooted on the ring, degrees (g_g's own number is 44)
# The profile is overridable too, as "t:w,t:w,..." -- so an option is never
# the only way to reach a shape.
def _open_prof():
    e = os.environ.get("ALBO_G_OPEN_PROF")
    if not e: return _GO.get('prof', [(0.0, 1.00), (0.40, 0.92), (1.0, 0.66)])
    return [tuple(float(x) for x in kv.split(':')) for kv in e.split(',')]
G_OPEN_PROF    = _open_prof()

# ---- WHAT WAS TRIED AND DID NOT WORK, with its numbers. -------------------
#
# 1. ROOTING THE TAIL LOW, on the bowl's underside (frm -45 to -60), so the
#    ring and the tail never run side by side and no shoulder cut is needed.
#    The ring's clockwise tangent at -45 is 42 degrees off vertical and at
#    -60 it is 55, so a stroke leaving TANGENT there heads down-LEFT and a
#    deep descender then needs an S-bend to straighten. Abandoned on the
#    geometry rather than on a picture: the alternative to the S is to leave
#    NOT tangent, which is the notch rule again (section 1b).
#
# 2. THE SHOULDER CUT OVER A WIDE ARC. At 320 degrees / 62 degrees the cut
#    reaches the bowl's widest point and its floor: g/o walls read 0.87 at
#    0 degrees and 0.85 at 345 where the four reference open g's (Futura,
#    Verdana, Trebuchet, Skia) hold 0.94-1.00. 310/36 touches neither.
#
# 3. A TAIL THAT FOLDS BACK ON ITSELF to close the loop properly (tip at
#    reach +0.12 to +0.42 with the tip pointing up-RIGHT). The centreline
#    then crosses itself and `stroke()`'s offset edges cross with it, which
#    leaves white slivers INSIDE the stroke -- three built and all three
#    broken. `stroke(..., pieces=True)` is the face's own cure for a
#    self-crossing centreline (the ampersand, the at-sign) and would be the
#    way in if this is ever wanted; the shape it makes is not this letter.
#
# 4. THE RIGHT-HOOKING TAIL (option 7) IS NOT A g. Measured as ink overlap
#    against this face's own q, both rasterised at one x-height and aligned
#    on their counters' centroids: the binocular g scores 0.137, the o
#    against the q 0.599 (the yardstick -- a q IS an o with a stem), and
#    option 7 scores 0.651, the worst of the ten. At 13 px "a foggy gauge"
#    reads "a foqqy qauqe". It ships as an option because the owner asked
#    for the axis, not because it works.


def _open_bowl(cx, cy, rx, ry, w_scale, floor):
    """The o's ring, with its width cut back through the sector the tail
    shares with it (G_OPEN_CUT_*). At G_OPEN_CUT_W 1.0 this IS the o's ring."""
    outer = superellipse(cx, cy, rx, ry, 0.0, 2 * math.pi, BOWL_K)[:-1]
    outer = geom.resample(outer + [outer[0]])[:-1]
    tans = geom.tangents(outer, closed=True)
    ws = []
    for pt, tn in zip(outer, tans):
        w = max(PR.bowl_th(tn) * w_scale, floor)
        ang = math.degrees(math.atan2(pt[1] - cy, pt[0] - cx)) % 360.0
        d = abs((ang - G_OPEN_CUT_AT + 180.0) % 360.0 - 180.0)
        if d < G_OPEN_CUT_ARC:                  # a raised cosine, so the cut has no edge
            f = 0.5 * (1.0 + math.cos(math.pi * d / G_OPEN_CUT_ARC))
            w *= 1.0 - (1.0 - G_OPEN_CUT_W) * f
        ws.append(w)
    n = len(ws)
    return ring_from(outer, widths_fn=lambda t: ws[min(n - 1, max(0, int(round(t * n))))])


# ===================== ROUND 331 -- THE LETTER, NOT ITS PARTS =============
# Owner 2026-09-21: *"you are adjusting one part when you need rebuild the
# whole letter"*. Right, and it explains every fix that came before it.
#
# `_g_open` was the o's ring with things ATTACHED to it -- a tail rooted on the
# ring at a tangent, a serif stub standing on the ring, a clip that turned out
# to cut nothing. Each round moved one attachment. The open-g report even
# described the letter as "the q's skeleton with the stem's foot replaced by a
# hook", which is the right description of the wrong code: nothing in it was
# built on a stem.
#
# b d p q ARE a stem with a bowl clipped to it -- `bowl_stem` places the stem
# first, by rule, and the ring is intersected with the stem's inner edge. A
# single-storey g is the SAME letter as the q, with one difference: the stem's
# FOOT is a hook instead of a serif. So it is built that way here, and three
# things that had to be dialled before now fall out for free:
#
#   * the serif is `stem(top='left')` on a true vertical -- round 330's
#     alignment is not a setting, it is what the construction does;
#   * the counter's right edge is the stem's inner edge, because the ring is
#     clipped to it exactly as the q's is;
#   * the tail leaves a STEM going down, not a ring going sideways -- which is
#     why rooting it on the ring needed an S-bend to reach the descender at
#     all (the open-g work recorded that as a negative result; it was a symptom
#     of building the letter out of the wrong part).
G_OPEN_BUILD = os.environ.get("ALBO_G_OPEN_BUILD", "qstem")   # qstem (round 331) | ring (rounds 326-330)
# ROUND 333 -- THE RIGHT STROKE'S WIDTH. Owner: *"thin out right stoke to
# optically match the rest of the word image. might just be 98% reduction but
# justify it."* It is NOT physically wider than the rest: at half the
# x-height the g's stem measures 64 units, and so do the u's, the d's and the
# n's. What is heavier is the ink AROUND it -- see the ladder in
# docs/albo-sans-g-research-2026-09-21.md round 333.
G_QS_STEM_W = _gof('qs_stem_w', 1.0)     # the right stroke, x the family's vertical
G_QS_TOP_SCALE = _gof('qs_top_scale', 1.0)  # the top serif's size, x the family's     # the right stroke, x the family's vertical
G_QS_CTR_TOP = _gof('qs_ctr_top', 2.0)   # units the counter's TOP rises, by thinning the wall there
G_QS_CTR_BOT = _gof('qs_ctr_bot', 0.0)   # and its bottom
G_QS_CTR_ARC = _gof('qs_ctr_arc', 70.0)  # how far round the thinning reaches, degrees
G_QS_STEM_Y = _gof('qs_stem_y', 0.0)     # where the stem stops and the hook starts, x the descender
G_QS_TOP    = os.environ.get("ALBO_G_QS_TOP", "left")   # the serif: bowl_stem's own 'left'


def _g_qstem(c):
    """The q, with the stem's foot replaced by the traced hook."""
    from shapely.geometry import box as _box
    xh = c["xh"]; wf = c["wf"]; desc = c["desc"]
    # --- bowl and stem, placed by `bowl_stem`'s own rule, in its own order
    rx_c = 214 * wf * (pen.IT_OVAL if pen.ITALIC else 1.0)
    rx = rx_c + TH_V / 2; ry = xh / 2 + OVER
    cx = rx; xs = cx + rx_c - S * 0.5; edge = xs - TH_V / 2
    # ROUND 332 -- THE COUNTER, TO THE OWNER'S OWN NUMBERS. He dialled it on
    # the bench (`scratchpad/albo/counter.html`): *"counter size 100.5%, below
    # x-height 17"*, with the baseline gap left at 19. As built the counter was
    # 391 tall, 19 above the baseline and 19 below the x-height; his figures are
    # 393 / 19 / 17, and 19 + 393 + 17 is the x-height exactly.
    #
    # The bench holds the OUTER still and moves only the counter, so that is
    # what happens here: the ring's wall is thinned at the TOP by the 2 units
    # the counter grows, on a raised cosine so there is no step, and the bottom
    # is untouched. The alternative -- a taller ring -- would raise the outer
    # too and change the overshoot, which is not what he was looking at.
    if G_QS_CTR_TOP or G_QS_CTR_BOT:
        outer0 = superellipse(cx, xh / 2, rx, ry, 0, 2 * math.pi, BOWL_K)[:-1]
        outer0 = geom.resample(outer0 + [outer0[0]])[:-1]
        tans0 = geom.tangents(outer0, closed=True)
        ws = []
        for pt, tn in zip(outer0, tans0):
            w = PR.bowl_th(tn)
            ang = math.degrees(math.atan2(pt[1] - xh / 2, pt[0] - cx)) % 360.0
            for centre, cut in ((90.0, G_QS_CTR_TOP), (270.0, G_QS_CTR_BOT)):
                d = abs((ang - centre + 180.0) % 360.0 - 180.0)
                if cut and d < G_QS_CTR_ARC:
                    w -= cut * 0.5 * (1.0 + math.cos(math.pi * d / G_QS_CTR_ARC))
            ws.append(max(w, S * 0.30))
        n_ = len(ws)
        solid, outer, inner = ring_from(outer0,
            widths_fn=lambda t: ws[min(n_ - 1, max(0, int(round(t * n_))))])
    else:
        solid, outer, inner = ring(cx, xh / 2, rx, ry)
    solid = solid.intersection(_box(-2000, -1000, edge + 5, 2000))
    y_bot = -desc * G_QS_STEM_Y
    st = stem(xs, y_bot, xh, w=TH_V * G_QS_STEM_W,
              top=(None if G_QS_TOP == 'none' else G_QS_TOP),
              foot=None, ent_span=(y_bot, xh), top_scale=G_QS_TOP_SCALE)
    # --- the hook IS the foot: the traced model hung off the stem's bottom
    root = (xs, y_bot)
    path = _traced_tail(root, desc * G_OPEN_TRACE_DEP, wf, cx)
    prof = widths([(t, (w * G_OPEN_W0) if t == 0.0 else w) for t, w in G_OPEN_PROF])
    base = PR.bowl_widths(path, prof, floor=S * G_OPEN_FLOOR)
    parts = [solid, st]
    if G_OPEN_END == 'finial':
        from .rounds import c_top_width
        parts.append(stroke(path, PR.finial_widths(base, False, floor=c_top_width()),
                            cut1=PR.finial_cut(path, False)))
    else:
        parts.append(stroke(path, base, cut1=CUT))
    return geom.ink(parts)


def _g_open(c):
    """The open-loop roman g -- a full x-height bowl whose right wall carries
    on past the baseline and curls, instead of closing into a second bowl."""
    from .rounds import O_RX, O_RX_ADJ, O_W_ADJ, O_FLOOR_ADJ, c_top_width
    xh = c["xh"]; wf = c["wf"]; desc = c["desc"]
    # --- the bowl IS the o's ring (its radius, its weight scale and its
    # --- hairline floor), narrowed by G_OPEN_RX. Nothing about it is new.
    rx = O_RX * O_RX_ADJ * G_OPEN_RX * wf + TH_V / 2 * O_W_ADJ
    ry = xh / 2 + OVER
    cx, cy = rx, xh / 2
    bowl, bo, bi = _open_bowl(cx, cy, rx, ry, O_W_ADJ, S * O_FLOOR_ADJ)
    crx, cry = rx - TH_V / 2, ry - TH_H / 2        # the ring's centreline, g_g's own idiom
    # --- the tail, rooted on that centreline with that tangent (THE ONE RULE)
    P0 = _open_on(cx, cy, crx, cry, G_OPEN_FROM)
    T0 = _open_tan(crx, cry, G_OPEN_FROM)
    if G_OPEN_KIND == 'trace':
        path = _traced_tail(P0, desc * G_OPEN_TRACE_DEP, wf, cx)
    elif G_OPEN_KIND == 'arc':
        drop = (P0[1] + desc) * G_OPEN_RUN
        run_len = drop / max(1e-6, abs(T0[1]))
        P1 = (P0[0] + T0[0] * run_len, P0[1] + T0[1] * run_len)
        path = geom.line(P0, P1)[:-1] + _open_arc(P1, T0, G_OPEN_R * wf, G_OPEN_SWEEP)
    else:
        P3 = (cx + G_OPEN_REACH * crx, -desc * G_OPEN_DEPTH)
        a3 = math.radians(G_OPEN_TIPDEG); T3 = (math.cos(a3), math.sin(a3))
        chord = math.hypot(P3[0] - P0[0], P3[1] - P0[1])
        C1 = (P0[0] + T0[0] * chord * G_OPEN_C1, P0[1] + T0[1] * chord * G_OPEN_C1)
        C2 = (P3[0] - T3[0] * chord * G_OPEN_C2, P3[1] - T3[1] * chord * G_OPEN_C2)
        path = cubic(P0, C1, C2, P3)
    prof = widths([(t, (w * G_OPEN_W0) if t == 0.0 else w) for t, w in G_OPEN_PROF])
    base = PR.bowl_widths(path, prof, floor=S * G_OPEN_FLOOR)
    parts = [bowl]
    if G_OPEN_END == 'finial':
        # the c's top, with the y-tail's floor: a tail running out on the pen's
        # THIN would otherwise swell to 1.10 of nearly nothing (PR.finial_widths)
        wfn = PR.finial_widths(base, False, floor=c_top_width())
        parts.append(stroke(path, wfn, cut1=PR.finial_cut(path, False)))
    elif G_OPEN_END == 'wedge':
        parts.append(stroke(path, base, cut1=CUT))
        parts.append(PR.end_wedge(path, base(1.0), False, int(G_OPEN_WSIDE), scale=G_OPEN_WSCALE))
    elif G_OPEN_END == 'point':
        parts.append(stroke(path, base))
    else:                                  # 'cut': the c's lower terminal
        parts.append(stroke(path, base, cut1=CUT))
    # --- ROUND 329 -- A bpqd SERIF INSTEAD OF AN EAR.
    # Owner 2026-09-21: *"make some bpqd style serifs to choose from, not the
    # ear"*. b d p q are all `bowl_stem`, and every one of them finishes its
    # stem with `stem(..., top='left')` -- one wedge, on the bowl side of the
    # stem's top. That is the serif being asked for, so it is taken from the
    # same call rather than drawn again: a short stem stub stands on the ring
    # at G_OPEN_SER_AT and carries the family's own top, and the ring is the
    # wall it stands on. `foot=None` always -- this end is a join, not a foot.
    if G_OPEN_EAR in ('dtop', 'btop', 'both', 'plus', 'flat'):
        # ROUND 330 -- ALIGNED THE WAY b d p q ALIGN. Owner: *"take multiple
        # passes at aligning the vertical stem with the serif in the same way
        # bdqp all do"*. Round 329 stood the stub on the ring at 38 degrees,
        # which is not what those letters do at all. `bowl_stem` places a TRUE
        # VERTICAL by rule -- its centre half a stem INSIDE the ring's far
        # centreline -- and then CLIPS the ring to that stem's inner edge, so
        # the stem's inner edge IS the counter's edge and nothing pokes past
        # it. Measured here: the x was out by only 6.7 units (0.10 stems), but
        # the counter's right edge was the RING's at 378.4 where bpqd would put
        # a straight wall at 344.9. The join was the misalignment, not the x.
        kind = {'dtop': 'left', 'btop': 'right', 'both': 'both',
                'plus': 'left+', 'flat': None}[G_OPEN_EAR]
        top_y = xh + OVER * G_OPEN_SER_OVER
        if G_OPEN_SER_ALIGN == 'ring':          # round 329, kept for the record
            xs, ry0 = _open_on(cx, cy, crx, cry, G_OPEN_SER_AT)
            y0 = min(top_y - S * G_OPEN_SER_LEN, ry0)
        else:
            xs = cx + crx - S * 0.5             # bowl_stem's own rule
            y0 = top_y - S * G_OPEN_SER_LEN
        if G_OPEN_SER_ALIGN == 'clip':
            from shapely.geometry import box as _box
            edge = xs - TH_V / 2                # the stem's INNER edge
            keep = _box(-2000, -2000, edge + 5, 4000).union(_box(-2000, -2000, 4000, y0))
            parts[0] = parts[0].intersection(keep)
        parts.append(stem(xs, y0, top_y, top=kind, foot=None,
                          ent_span=(0.0, top_y), top_scale=G_OPEN_SER_SCALE))
    elif G_OPEN_EAR != 'none':
        ex, ey = _open_on(cx, cy, crx, cry, G_OPEN_EAR_AT); L = 96 * wf * g_ear_scale()
        ear_c = [(ex, ey), (ex + L, ey + L * math.tan(math.radians(8)))]
        parts.append(stroke(ear_c, PR.bowl_widths(ear_c, widths([(0.0, 0.4), (0.35, 1.0), (1.0, 1.05)]),
                                                  floor=S * 0.72), cut1=CUT))
    return geom.ink(parts)


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
    if G_STYLE == 'open':
        return _g_qstem(c) if G_OPEN_BUILD == 'qstem' else _g_open(c)        # round 327, exploration only -- see the block above
    if G_STYLE == 'bent':
        return _g_bent(c)
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
