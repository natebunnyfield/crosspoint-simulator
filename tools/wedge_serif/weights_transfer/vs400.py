#!/usr/bin/env python3
"""Today's white at each cut against the 400 of its style, pair by pair, over
the census pairs of his books (n >= 50), census-weighted.  Answers "what does a
reader of the Bold see where he judged the Regular" before any arm moves.

    $VENV/bin/python vs400.py TODAY_DIR
"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import Font, census
from transfer import CUTS, BASE

d = sys.argv[1]
cen = census(50)
for style, cuts in CUTS.items():
    B = Font(os.path.join(d, f"Albo-{BASE[style]}.ttf"))
    for cut, wt in cuts:
        if cut == BASE[style]:
            continue
        F = Font(os.path.join(d, f"Albo-{cut}.ttf"))
        rows = []
        for p, n in cen:
            if not all(ord(c) in F.cmap for c in p):
                continue
            a, b = B.white(*p), F.white(*p)
            if a is not None and b is not None:
                rows.append((b - a, n, p))
        dd = np.array([r[0] for r in rows]); w = np.array([r[1] for r in rows])
        mu = np.average(dd, weights=w); sd = np.sqrt(np.average((dd - mu) ** 2, weights=w))
        worst = sorted(rows, key=lambda r: -abs(r[0]) * np.sqrt(r[1]))[:8]
        print(f"{style:6s} {cut:11s} vs {BASE[style]}: white diff mean {mu:+.1f} sd {sd:.1f} units, "
              f"|diff|>=10 on {100*w[np.abs(dd)>=10].sum()/w.sum():.1f}% of text pairs; "
              f"largest (census-weighted): " + ", ".join(f"{''.join(r[2])} {r[0]:+.0f}" for r in worst))

# ---- the same comparison on ink, not bbox: the 2-D closest approach (d2) and
# the mean x-band row gap, from local_ai/features.py.  The bbox white of a
# sheared italic counts overhangs (the q's foot, an ascender's lean) that no
# neighbor meets, so the italic is read here too.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "local_ai"))
import features as FT
lc = [(p, n) for p, n in census(300) if p[0].islower() and p[1].islower()]
for style, cuts in CUTS.items():
    B = FT.Font(os.path.join(d, f"Albo-{BASE[style]}.ttf"))
    for cut, wt in cuts:
        if cut == BASE[style]:
            continue
        F = FT.Font(os.path.join(d, f"Albo-{cut}.ttf"))
        out = {"d2": [], "band_x_mean": []}; w = []; ex = []
        for p, n in lc:
            fa = FT.pair_features(B, p[0], p[1], style == "italic")[0]
            fb = FT.pair_features(F, p[0], p[1], style == "italic")[0]
            for k in out:
                out[k].append(fb[k] - fa[k])
            w.append(n); ex.append((fb["band_x_mean"] - fa["band_x_mean"], n, p))
        w = np.array(w)
        s = "; ".join(f"{k} diff mean {np.average(v, weights=w):+.1f} sd "
                      f"{np.sqrt(np.average((np.array(v)-np.average(v, weights=w))**2, weights=w)):.1f}"
                      for k, v in out.items())
        worst = sorted(ex, key=lambda r: -abs(r[0]) * np.sqrt(r[1]))[:8]
        print(f"{style:6s} {cut:11s} ink vs {BASE[style]} ({len(lc)} lowercase pairs, n>=300): {s}; "
              f"largest x-band: " + ", ".join(f"{''.join(r[2])} {r[0]:+.0f}" for r in worst))
