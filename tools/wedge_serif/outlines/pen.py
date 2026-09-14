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
# Round 65 (owner): "set default to .95 contrast, update contrast range to
# full 0-100; set DESC default to 280." Then, same round: "new defaults:
# Weight 84, Contrast 0.95, Ascender 770, Descender 280, Width 100, Cut 87,
# x-height 429, Serif 92."
DESIGN["contrast"] = 0.95; DESIGN["desc"] = 280
DESIGN["cut"] = 87; DESIGN["serif"] = 92    # serif: the wedge family's unit (WL, WD, DROP) x 0.92
HAIR_FLOOR = 6.0   # the pen's hair never under this (0.32 px at 54 px em): at contrast 1.00 th() would be 0 on the stress angle
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
SERIF = _env("FJORD_SERIF", DESIGN["serif"]) / 100.0                                     # the SRIF axis: the wedge family's unit x this
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
class FlooredPen:
    """alphabet2.Pen with an absolute floor on its width: every consumer
    (th, th_t, pen_widths, bowl_th, check, the rings) reads PEN.th(), so
    the floor lives here and nowhere else. The ruled floors on particular
    strokes (K arm 0.47 stem, R leg 1.05 x pen, j tail, e bar 0.35 stem,
    r arm 0.78) sit above it and are untouched."""
    def __init__(self, inner, floor):
        self.inner = inner; self.floor = floor; self.stem = inner.stem; self.hair = max(inner.hair, floor)
        self.stress = inner.stress; self.power = inner.power
    def th(self, tan): return max(self.inner.th(tan), self.floor)
PEN = FlooredPen(_Pen(S, CONTRAST, DESIGN["stress"], DESIGN["power"]), HAIR_FLOOR)
HAIR = PEN.hair

def th(deg):
    """Stroke width for a centerline running at `deg` (0 = right, 90 = up)."""
    a = math.radians(deg); return PEN.th((math.cos(a), math.sin(a)))
def th_t(tan): return PEN.th(tan)
TH_V = th(90); TH_H = th(0)                  # 77.3 and 55.4
# Round 94 (owner 2026-09-14: "the crossbar for 'F' is too thin, take a pass
# at all capitals"): the capitals' bars were the pen's horizontal (55), 0.47
# of the cap stem after the cut, and dropped to gray at 13 pt while the stems
# held black; Albertus's bars measure 0.75 of its cap stem, Berkeley's 0.39.
# One unit for every capital bar, on the pen (so the CNTR axis moves it):
CAP_BAR_F = 1.18
CAP_BAR = TH_H * CAP_BAR_F                   # 65 at the default: 0.68 of the cap stem

# Round 92 (owner 2026-09-14: "make all adjustments and present each
# individually"): the lowercase adjustment list of round 91, each behind
# its letter so it can be built ALONE on the round-90 base and judged as one
# change. FJORD_ADJ is a string of letters, or "all". ADJ_DEFAULT is the set
# that ships once he rules; empty until then.
ADJ_DEFAULT = "zpnacotekiubwj"   # round 93, the owner's ruling on the round-92 page: yes to these; r l f stay as they were
ADJ = os.environ.get("FJORD_ADJ", ADJ_DEFAULT)
def adj(ch):
    """Is this letter's round-92 adjustment on? 'b' covers b and d; 'n'
    covers the arch of n h m; 'i' the dot of i (j has its own)."""
    return ADJ == "all" or ch in ADJ

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
