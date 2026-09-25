# ROUND 389 -- the pair interaction behind the word-pair decisions in docs/albo-round-389-2026-09-25.md.
# usage: PYTHON_GIL=0 python3 instruments/r389_pair_interaction.py FONT.ttf roman|italic "fo or rt ..." [OUT.json]
# RUN ONE STYLE PER PROCESS, TO A FILE: two backgrounded runs sharing a terminal print in COMPLETION order,
# and that swapped the roman and italic tables once in round 389 (the doc records it).
"""Pair interaction against the letter's OWN pairs: D(ab) = g(ab) - med_x g(ax) - med_x g(xb) + med_xy g(xy),
x over a neutral lowercase set. d = D_Albo - median D_ref, units. M4 and M5 (clamp 1.5)."""
import sys, numpy as np, json
import os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import refsets
from cmp_space_2d import Face as F4
from cmp_word_white import Face as F5
NEU = "noeuimhac"
font, rset = sys.argv[1], sys.argv[2]; pairs = sys.argv[3].split(); out = sys.argv[4] if len(sys.argv)>4 else None
faces = [(F4(font), F5(font, clamp=1.5))]
for _, p, i in refsets.entries(rset):
    try: faces.append((F4(p, index=i), F5(p, index=i, clamp=1.5)))
    except Exception: pass
def D(g, a, b):
    ab = g(a, b)
    if ab is None: return None
    A = [v for x in NEU if (v := g(a, x)) is not None]
    B = [v for x in NEU if (v := g(x, b)) is not None]
    C = [v for x in NEU for y in NEU if (v := g(x, y)) is not None]
    if not A or not B: return None
    return ab - np.median(A) - np.median(B) + np.median(C)
res = {}
print(f"{'pair':5}{'M4 D':>7}{'ref':>7}{'d4':>6}{'spread':>8}{'M5 D':>7}{'ref':>7}{'d5':>6}")
for pr in pairs:
    a, b = pr[0], pr[1]
    r = {}
    for k in (0, 1):
        vals = [D((f[0].gap if k == 0 else f[1].white), a, b) for f in faces]
        me, rv = vals[0], [v for v in vals[1:] if v is not None]
        r[k] = (me*1000 if me is not None else None, np.median(rv)*1000 if rv else None,
                (me - np.median(rv))*1000 if (me is not None and rv) else None,
                (np.percentile(rv,75)-np.percentile(rv,25))*1000 if len(rv)>2 else None)
    res[pr] = dict(m4=r[0], m5=r[1])
    f = lambda x, w=7: f"{x:{w}.0f}" if x is not None else " "*(w-3)+"n/a"
    print(f"{pr:5}{f(r[0][0])}{f(r[0][1])}{f(r[0][2],6)}{f(r[0][3],8)}{f(r[1][0])}{f(r[1][1])}{f(r[1][2],6)}")
if out: json.dump(res, open(out, "w"), indent=1, default=float)
