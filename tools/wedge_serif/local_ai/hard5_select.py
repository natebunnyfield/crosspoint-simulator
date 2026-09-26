#!/usr/bin/env python3
"""Pick the five HARDEST pairs, by a criterion computed from his answers.

    $VENV/bin/python hard5_select.py      -> $HARD5_DIR/selection.json

A pair is a candidate when he has answered it MORE THAN ONCE (bench + re-ask
+ outlier bench + active session 1, all on the 2026-09-20 zero), so his
answer is a mean of repeated judgments rather than one noisy slider.

    his      mean of his readings
    spread   max - min of his readings
    CONFIDENT  every reading has the sign of the mean, |his| >= 20, and
               spread <= max(15, 0.5 |his|)  -- large and repeatable
    B2 held  the shipped B2 (bench + extras, skip weight 1) REFIT WITHOUT any
             reading of that pair, predicting it
    miss     |B2 held - his|

Hardness = miss, among CONFIDENT pairs; the top five are the set. Every
candidate row is printed so the cut can be audited.
"""
import json, os
import numpy as np
import features as FT
import b2_fit
from hard5_common import STYLES, SCRATCH, all_readings


def b2_heldout(style, fonts, pairs_to_hold):
    R = b2_fit.readings(style)
    feats = {}
    need = {p for p in R if b2_fit.in_scope(p) or len(R[p]) and R[p][0][1] == "bench"} | set(pairs_to_hold)
    for p in need:
        feats[p] = FT.pair_features(fonts[style], p[0], p[1], style == "italic")[0]
    out = {}
    for p in pairs_to_hold:
        J, W = b2_fit.combine({q: v for q, v in R.items() if q != p}, 1.0)
        J = {q: v for q, v in J.items() if q in feats}
        out[p] = b2_fit.fit(style, J, feats, W)[2](p)
    return out


def main():
    fonts = {s: FT.Font(p) for s, p in FT.FONTS.items()}
    rows = []
    for s in STYLES:
        A = all_readings(s)
        multi = {p: r for p, r in A.items() if len(r) >= 2}
        held = b2_heldout(s, fonts, sorted(multi))
        for p, r in multi.items():
            d = np.array([x for x, _ in r])
            m = float(d.mean()); spread = float(d.max() - d.min())
            conf = bool(abs(m) >= 20 and np.all(np.sign(d) == np.sign(m))
                        and spread <= max(15.0, 0.5 * abs(m)))
            rows.append(dict(style=s, pair=p, readings=[[x, src] for x, src in r], his=round(m, 1),
                             spread=spread, confident=conf, b2_held=round(held[p], 1),
                             miss=round(abs(held[p] - m), 1)))
    rows.sort(key=lambda x: (-x["confident"], -x["miss"]))
    print(f"{len(rows)} pairs answered more than once")
    print(f"{'style':6s} {'pair':4s} {'n':>2s} {'his':>6s} {'spread':>6s} {'conf':>4s} {'B2held':>7s} {'miss':>5s}  readings")
    for x in rows:
        print(f"{x['style']:6s} {x['pair']:4s} {len(x['readings']):2d} {x['his']:+6.1f} {x['spread']:6.0f} "
              f"{'Y' if x['confident'] else '.':>4s} {x['b2_held']:+7.1f} {x['miss']:5.1f}  "
              + " ".join(f"{v:+.0f}({src})" for v, src in x["readings"]))
    top = [x for x in rows if x["confident"]][:5]
    os.makedirs(SCRATCH, exist_ok=True)
    json.dump(dict(criterion=__doc__, top5=top, all=rows),
              open(os.path.join(SCRATCH, "selection.json"), "w"), indent=1)
    print("\nTOP 5:", [(x["style"], x["pair"], x["his"], x["miss"]) for x in top])


if __name__ == "__main__":
    main()
