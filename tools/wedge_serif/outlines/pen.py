"""The pen as the REFERENCE for weights (guide §0, §2): the shipping design
B5.9 -- stem 82, contrast 0.60 (hair 33), stress 26 deg, power 0.95 -- and
the fixed proportions. Every width written in the glyph code should be
readable against pen.th(); check() reports a drawn stroke against it."""
import os, math, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from alphabet2 import Pen as _Pen
import round19

DESIGN = dict(round19.DESIGN)
DESIGN["stem"] = 94                          # owner ruling, round 59 (2026-09-13): "94 wins" on the weight ladder; was 82
# Round 62 (owner, from the slider page): "set to new defaults" -- weight 84,
# contrast 0.80, ascender 770, descender 256, width 100, cut 115, x-height
# 429, serif 100. The caps stay at 1.625 x 415 = 674 (the XHGT axis moved
# the lowercase against fixed caps, and 429 was picked on that slider).
DESIGN["stem"] = 84; DESIGN["contrast"] = 0.80; DESIGN["asc"] = 770; DESIGN["desc"] = 256; DESIGN["xh"] = 429
DESIGN["cut"] = 115                          # the cut as an AMOUNT: 0 the dense outline, 100 the 1-in-4 projection, 200 the 1-in-8, linear between
# Round 61 (owner: "a variable axis font"): every design parameter an axis
# moves is read from an env override at import, so one master of the
# variable font is one subprocess of outlines.build. Unset, each is the
# shipping value; the static builder's defaults do not change.
_env = lambda k, d: float(os.environ.get(k, d))
BASE_XH = 415                                # the capitals stay at 1.625 x THIS whatever the x-height is
XH = _env("FJORD_XH", DESIGN["xh"]); ASC = _env("FJORD_ASC", DESIGN["asc"]); DESC = _env("FJORD_DESC", DESIGN["desc"])
DESIGN["xh"], DESIGN["asc"], DESIGN["desc"] = XH, ASC, DESC
S = _env("FJORD_STEM", DESIGN["stem"]); CAP_STEM = 1.137; CS = S * CAP_STEM   # FJORD_STEM: weight ladder override (round 58c); the wght axis
CONTRAST = _env("FJORD_CONTRAST", DESIGN["contrast"])                          # the CNTR axis: hair = stem x (1 - contrast)
WIDTH = _env("FJORD_WIDTH", 100.0) / 100.0                                     # the wdth axis: lc_width, the capitals' solved widths, the fitting, all x this
SERIF = _env("FJORD_SERIF", 100.0) / 100.0                                     # the SRIF axis: the wedge family's unit x this
CUT_AMOUNT = _env("FJORD_CUT", DESIGN["cut"])                                   # the CUTS axis: 0..200 (see cut.blend)
CAP = BASE_XH * 1.625
OVER = DESIGN["overshoot"]; ARCH_OVER = DESIGN["arch_over_edge"]
WF = DESIGN["lc_width"] * WIDTH
ENT = DESIGN["flare"]                       # entasis: stems swell 14% at their ends
WL = DESIGN["wedge_len"] * S * SERIF; WD = DESIGN["wedge_depth"] * S * SERIF   # 69.7 x 139.4 at stem 82: the wedge family's unit
DROP = DESIGN["serif_drop"] * S * SERIF; FILLET = DESIGN["fillet"]             # 23, 0.65
FOOT = DESIGN["foot_scale"]                  # feet are 0.85 of a top wedge's length
CUT = math.radians(DESIGN["cut_deg"])        # 20 deg pen cut
BOWL_K = DESIGN["bowl_k"]                    # 2.1: the family's superellipse
NW = DESIGN["n_width"] * WF + (S - 110) * 0.9   # the n's stem-to-stem distance
N_COUNTER = NW - S
N_COUNTER_FULL = DESIGN["n_width"] * WIDTH + (S - 110) * 0.9 - S   # the UNCONDENSED n counter the word space is 1.7 x of (round 20)
PEN = _Pen(S, CONTRAST, DESIGN["stress"], DESIGN["power"])
HAIR = PEN.hair

def th(deg):
    """Stroke width for a centerline running at `deg` (0 = right, 90 = up)."""
    a = math.radians(deg); return PEN.th((math.cos(a), math.sin(a)))
def th_t(tan): return PEN.th(tan)
TH_V = th(90); TH_H = th(0)                  # 77.3 and 55.4

def check(outer, inner, label=""):
    """Width of a drawn stroke (two edge curves, same direction) at each
    outer sample, against the pen's width at that tangent. Returns rows
    (t, width, pen, ratio); prints a summary."""
    import numpy as np
    from . import geom
    tans = geom.tangents(outer); inn = np.array(inner); rows = []
    for i, (p, tn) in enumerate(zip(outer, tans)):
        d = np.hypot(inn[:, 0] - p[0], inn[:, 1] - p[1]); w = float(d.min())
        e = PEN.th(tn); rows.append((i / max(1, len(outer) - 1), w, e, w / e))
    if label:
        rs = [r[3] for r in rows]
        print(f"[pen] {label}: width/pen min {min(rs):.2f} max {max(rs):.2f} mean {sum(rs)/len(rs):.2f}")
    return rows
