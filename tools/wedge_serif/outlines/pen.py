"""The pen as the REFERENCE for weights (guide §0, §2): the shipping design
B5.9 -- stem 82, contrast 0.60 (hair 33), stress 26 deg, power 0.95 -- and
the fixed proportions. Every width written in the glyph code should be
readable against pen.th(); check() reports a drawn stroke against it."""
import os, math, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from alphabet2 import Pen as _Pen
import round19

DESIGN = dict(round19.DESIGN)
XH = DESIGN["xh"]; ASC = DESIGN["asc"]; DESC = DESIGN["desc"]
DESIGN["stem"] = 94                          # owner ruling, round 59 (2026-09-13): "94 wins" on the weight ladder; was 82
S = float(os.environ.get("FJORD_STEM", DESIGN["stem"])); CAP_STEM = 1.137; CS = S * CAP_STEM   # FJORD_STEM: weight ladder override (round 58c)
CAP = XH * 1.625
OVER = DESIGN["overshoot"]; ARCH_OVER = DESIGN["arch_over_edge"]
WF = DESIGN["lc_width"]
ENT = DESIGN["flare"]                       # entasis: stems swell 14% at their ends
WL = DESIGN["wedge_len"] * S; WD = DESIGN["wedge_depth"] * S   # 69.7 x 139.4: the wedge family's unit
DROP = DESIGN["serif_drop"] * S; FILLET = DESIGN["fillet"]     # 23, 0.65
FOOT = DESIGN["foot_scale"]                  # feet are 0.85 of a top wedge's length
CUT = math.radians(DESIGN["cut_deg"])        # 20 deg pen cut
BOWL_K = DESIGN["bowl_k"]                    # 2.1: the family's superellipse
NW = DESIGN["n_width"] * WF + (S - 110) * 0.9   # the n's stem-to-stem distance, 331
N_COUNTER = NW - S
PEN = _Pen(S, DESIGN["contrast"], DESIGN["stress"], DESIGN["power"])
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
