#!/usr/bin/env python3
"""Is B2's regularization chosen honestly, and does it overfit?

Owner 2026-09-26: *"we're trying to get a strong model not overfitting."*

    $VENV/bin/python probe_alpha.py

1. THE CURVE. Held-out error over a grid of the two ridge penalties -- ALPHA_ID
   (each glyph's two bearings) and ALPHA_F (the 38 standardized shape
   features) -- on bench_fit's own folds (10 x 5, seed 20260925), every
   ingested reading in training except a held-out pair's own, scored against
   his bench number (probe_extra.py's section A). The shipped values are
   ALPHA_ID 1, ALPHA_F 30, fixed on 2026-09-26 BEFORE any of this was run.
2. THE GAP. For each subset of his answers (bench, outliers, each active
   session, touched / skipped), in-sample error of the full fit against the
   held-out error of the same rows. A model that memorizes shows a large gap
   that grows with the data it memorized; the floor for the gap is his own
   noise (a fit that absorbs noise looks better in-sample by about that much).
"""
import json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, WS)
import bench_fit  # noqa: E402
import features as FT  # noqa: E402
import b2_fit  # noqa: E402
import probe_fit as PF  # noqa: E402

STYLES = ("roman", "italic")
A_ID = (0.1, 0.3, 1.0, 3.0, 10.0)
A_F = (3.0, 10.0, 30.0, 100.0, 300.0)


def main():
    fonts = {s: FT.Font(p) for s, p in FT.FONTS.items()}
    R = {s: b2_fit.readings(s) for s in STYLES}
    J0 = {s: bench_fit.judgments(s) for s in STYLES}
    feats = {s: {p: FT.pair_features(fonts[s], p[0], p[1], s == "italic")[0]
                 for p in R[s] if b2_fit.in_scope(p) or p in J0[s]} for s in STYLES}
    FO = PF.folds()

    def fit_on(s, reads):
        J, W = b2_fit.combine(reads, 1.0)
        J = {p: v for p, v in J.items() if p in feats[s]}
        return b2_fit.fit(s, J, feats[s], W)[2]

    def cv_bench(repeats=PF.REPEATS):
        errs = []
        for r in range(repeats):
            for i in range(PF.K):
                for s in STYLES:
                    held = FO[s][r * PF.K + i][2]
                    pred = fit_on(s, {p: v for p, v in R[s].items() if p not in held})
                    errs += [abs(pred(p) - J0[s][p]) for p in held]
        return float(np.mean(errs))

    print("1. held-out error on the 370 bench pairs (same folds, 2 shuffles for the grid)")
    grid = {}
    print("   ALPHA_ID \\ ALPHA_F " + "".join(f"{f:>8g}" for f in A_F))
    for a in A_ID:
        row = []
        for f in A_F:
            b2_fit.ALPHA_ID, b2_fit.ALPHA_F = a, f
            grid[(a, f)] = cv_bench(repeats=2)
            row.append(grid[(a, f)])
        print(f"   {a:>8g}           " + "".join(f"{v:8.2f}" for v in row))
    best = min(grid, key=grid.get)
    print(f"   best ({best[0]:g}, {best[1]:g}) {grid[best]:.2f}; shipped (1, 30) {grid[(1.0, 30.0)]:.2f}"
          f"  -- the gap is {grid[(1.0, 30.0)] - grid[best]:.2f} units, chosen on the SAME held-out rows, so optimistic")
    b2_fit.ALPHA_ID, b2_fit.ALPHA_F = 1.0, 30.0
    print(f"   shipped at the full 5 shuffles: {cv_bench():.2f}")

    print("\n2. in-sample vs held-out, by subset (shipped penalties)")
    ex = json.load(open(os.path.join(WS, "bench", "answers", "extra-judgments.json")))["rows"]
    lab = {}
    for s in STYLES:
        for p in J0[s]:
            lab[(s, p)] = "bench"
    for r in ex:
        k = (r["style"], r["pair"])
        if k in lab or r["pair"] not in feats[r["style"]]:
            continue
        lab[k] = ("outlier" if r["bench"].startswith("outliers") else r["bench"].rsplit("-", 1)[-1]
                  + ("-skipped" if r.get("verdict") == "skipped-ok" else "-touched"))
    keys = sorted(k for k in lab if k[1] in feats[k[0]])
    truth = {k: b2_fit.combine({k[1]: R[k[0]][k[1]]}, 1.0)[0][k[1]] for k in keys}
    full = {s: fit_on(s, R[s]) for s in STYLES}
    rng = np.random.default_rng(20260926)
    order = rng.permutation(len(keys)); folds = [order[i::10] for i in range(10)]
    cv = {}
    for fo in folds:
        held = {keys[i] for i in fo}
        preds = {s: fit_on(s, {p: v for p, v in R[s].items() if (s, p) not in held}) for s in STYLES}
        for k in held:
            cv[k] = preds[k[0]](k[1])
    print(f"   {'subset':12s} {'n':>4s} {'nothing':>8s} {'in-sample':>10s} {'held-out':>9s} {'gap':>6s}")
    for L in sorted(set(lab.values()), key=lambda x: (x != "bench", x)) + ["ALL"]:
        ks = [k for k in keys if L == "ALL" or lab[k] == L]
        ins = np.mean([abs(full[k[0]](k[1]) - truth[k]) for k in ks])
        ho = np.mean([abs(cv[k] - truth[k]) for k in ks])
        no = np.mean([abs(truth[k]) for k in ks])
        print(f"   {L:12s} {len(ks):4d} {no:8.2f} {ins:10.2f} {ho:9.2f} {ho - ins:6.2f}")
    json.dump({f"{a:g},{f:g}": v for (a, f), v in grid.items()},
              open(os.path.join(HERE, "probe_alpha-2026-09-26.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
