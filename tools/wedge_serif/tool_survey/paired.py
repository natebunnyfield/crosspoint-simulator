#!/usr/bin/env python3
"""Paired bootstrap for the survey's key comparisons (same held-out rows).

    $VENV/bin/python paired.py TOOL [TOOL ...]

For each tool: B2+tool (b2t) and the gain-calibrated tool (lin) against B2
alone and against doing nothing, bootstrap over held-out rows (4,000 draws).
Rows repeat across the 5 shuffles, so the interval is slightly narrow.
"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402


def ci(a, b, n=4000, seed=0):
    d = np.array(a) - np.array(b)
    rng = np.random.default_rng(seed)
    bs = [d[rng.integers(0, len(d), len(d))].mean() for _ in range(n)]
    return d.mean(), np.percentile(bs, 2.5), np.percentile(bs, 97.5)


T = C.Truth()
for name in sys.argv[1:]:
    white, _ = C.load_preds(name, "0920")
    td = T.tool_d(white)
    miss = sum(p not in td[s] for s in C.STYLES for p in T.J0[s])
    e = C.cv_scores(T, td, want=("nothing", "b2", "lin", "b2t"), raw=True)
    for k, ref in (("b2t", "b2"), ("lin", "nothing"), ("lin", "b2")):
        m, lo, hi = ci(e[k], e[ref])
        print(f"{name:20s} {k} - {ref}: {m:+.2f} (95% {lo:+.2f} .. {hi:+.2f}), n {len(e[k])}, missing {miss}")
