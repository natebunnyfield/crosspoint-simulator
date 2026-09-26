#!/usr/bin/env python3
"""Did the post-bench answers help B2? Held out, on bench_fit's own folds.

    $VENV/bin/python probe_extra.py

A. THE 370 BENCH PAIRS, SAME FOLDS as bench_fit.py --cv / probe_fit.py
   (10 folds x 5 shuffles, seed 20260925). Each held-out bench pair is scored
   against his ORIGINAL bench number, so the column is comparable with
   10.73. Training adds every ingested reading (bench/answers/extra-judgments
   .json) EXCEPT readings of a held-out pair, so nothing leaks. Rows: bench
   only (reproduces 10.73), and + extras at skip weights 1 / 0.5 / 0.25 / 0.

B. THE NEW PAIRS THEMSELVES (answered only after the bench: session 1 and
   the outlier bench's pairs that were not bench rows).
   * BEFORE: the bench-only B2 predicting them -- held out by construction.
   * AFTER, held out: 10-fold over those pairs (seed 20260926), training on
     the whole bench + the other folds' extras.
   * AFTER, in-sample: the full refit, for reference only.
   Split: session-1 touched / session-1 skipped (delta 0) / outlier.
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
SKIPS = (1.0, 0.5, 0.25, 0.0)


def main():
    fonts = {s: FT.Font(p) for s, p in FT.FONTS.items()}
    R = {s: b2_fit.readings(s) for s in STYLES}
    J0 = {s: bench_fit.judgments(s) for s in STYLES}
    feats = {}
    for s in STYLES:
        feats[s] = {p: FT.pair_features(fonts[s], p[0], p[1], s == "italic")[0]
                    for p in R[s] if b2_fit.in_scope(p) or p in J0[s]}
    ex = json.load(open(os.path.join(WS, "bench", "answers", "extra-judgments.json")))["rows"]
    tag = {}                     # (style, pair) -> subset label of a post-bench-only pair
    for r in ex:
        if r["pair"] in J0[r["style"]] or r["pair"] not in feats[r["style"]]:
            continue
        lab = ("s1-skipped" if r.get("verdict") == "skipped-ok" else "s1-touched") \
            if r["bench"].startswith("active") else "outlier"
        tag[(r["style"], r["pair"])] = lab

    def fit_on(s, reads, skip_w):
        J, W = b2_fit.combine(reads, skip_w)
        J = {p: v for p, v in J.items() if p in feats[s]}
        return b2_fit.fit(s, J, feats[s], W)[2]

    # ---- A: the bench pairs, same folds
    FO = PF.folds()
    print("A. the 370 bench pairs, held out on bench_fit's folds, scored against his bench number")
    for label, skip in [("bench only (B2 as proofed)", None)] + [(f"+ extras, skip weight {w:g}", w) for w in SKIPS]:
        errs = []
        for r in range(PF.REPEATS):
            for i in range(PF.K):
                for s in STYLES:
                    held = FO[s][r * PF.K + i][2]
                    if skip is None:
                        reads = {p: [(d, "bench")] for p, d in J0[s].items() if p not in held}
                    else:
                        reads = {p: v for p, v in R[s].items() if p not in held}
                    pred = fit_on(s, reads, 1.0 if skip is None else skip)
                    errs += [abs(pred(p) - J0[s][p]) for p in held]
        print(f"   {label:32s} {np.mean(errs):6.2f}")

    # ---- B: the post-bench pairs themselves
    keys = sorted(tag)
    truth = {}
    for s, p in keys:
        J, _ = b2_fit.combine({p: R[s][p]}, 1.0)
        truth[(s, p)] = J[p]
    before = {s: fit_on(s, {p: [(d, "bench")] for p, d in J0[s].items()}, 1.0) for s in STYLES}
    rng = np.random.default_rng(20260926)
    order = rng.permutation(len(keys)); folds = [order[i::10] for i in range(10)]
    after_cv = {sk: {} for sk in SKIPS}
    for sk in SKIPS:
        for f in folds:
            held = {keys[i] for i in f}
            preds = {s: fit_on(s, {p: v for p, v in R[s].items() if (s, p) not in held}, sk) for s in STYLES}
            for k in held:
                after_cv[sk][k] = preds[k[0]](k[1])
    full = {s: fit_on(s, R[s], 1.0) for s in STYLES}
    print("\nB. the pairs first answered after the bench (mean |error| vs his answer, 09-20 zero)")
    print(f"   {'subset':12s} {'n':>3s} {'nothing':>8s} {'BEFORE':>7s} " +
          " ".join(f"{'CV sk' + format(w, 'g'):>8s}" for w in SKIPS) + f" {'in-samp':>8s}")
    for lab in ("s1-touched", "s1-skipped", "outlier", "ALL"):
        ks = [k for k in keys if lab == "ALL" or tag[k] == lab]
        if not ks:
            continue
        e = lambda pr: np.mean([abs(pr(k) - truth[k]) for k in ks])
        cols = [e(lambda k, w=w: after_cv[w][k]) for w in SKIPS]
        print(f"   {lab:12s} {len(ks):3d} {np.mean([abs(truth[k]) for k in ks]):8.2f} "
              f"{e(lambda k: before[k[0]](k[1])):7.2f} " + " ".join(f"{c:8.2f}" for c in cols) +
              f" {e(lambda k: full[k[0]](k[1])):8.2f}")


if __name__ == "__main__":
    main()
