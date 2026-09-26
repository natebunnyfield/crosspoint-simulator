#!/usr/bin/env python3
"""Held-out accuracy of every non-VLM spacing model on HIS bench answers.

PROBE for docs/local-ai-spacing-options-2026-09-26.md.  The only question it
answers: on judgments the model never saw, how close does each approach get to
his own numbers -- against the do-nothing line (13.66), the shipped ridge
(11.66, bench_fit.py --cv), his own repeatability (10.83, the re-ask bench)
and the floor for any model against one noisy judgment (7.66)?

SAME FOLDS AS bench_fit.py --cv: per style, sorted pairs, 10 folds x 5
shuffles from default_rng(20260925).  Pooled models train on both styles'
training folds at the same fold index, so no held-out pair ever reaches a fit.
Hyperparameters are FIXED in this file (chosen once, stated below), not tuned
on the held-out score; the one sweep that is printed is labelled as a sweep.

Second score: each model's mean held-out prediction against his NEW answers
on the 40 re-asked rows (bench/answers/reask-2026-09-25-answers.json), where
the shipped ridge scored 13.14 on the 30 typical rows.

    $VENV/bin/python probe_fit.py            (needs features.py's output)
"""
import json, os, sys, time
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.dirname(HERE)
sys.path.insert(0, WS)
import bench_fit  # noqa: E402

FEAT = os.path.join(HERE, "features-2026-09-20.json")
REASK_KEY = os.path.join(WS, "bench", "reask-2026-09-25.key.json")
REASK_ANS = os.path.join(WS, "bench", "answers", "reask-2026-09-25-answers.json")
K, REPEATS, SEED = bench_fit.CV_K, bench_fit.CV_REPEATS, bench_fit.CV_SEED
STYLES = ("roman", "italic")

FEATS = json.load(open(FEAT))
NAMES = sorted(next(iter(FEATS["roman"].values()))["f"])
GEOM = [n for n in NAMES if n not in ("capL", "markL", "markR", "italic")]


def X_of(style, pairs, names=NAMES):
    return np.array([[FEATS[style][p]["f"][n] for n in names] for p in pairs])


def folds():
    """{style: [(repeat, fold, held_pairs)]} exactly as bench_fit.cross_validate."""
    out = {}
    for s in STYLES:
        J = bench_fit.judgments(s)
        pairs = sorted(J)
        rng = np.random.default_rng(SEED)
        lst = []
        for r in range(REPEATS):
            order = rng.permutation(len(pairs))
            for i in range(K):
                lst.append((r, i, {pairs[j] for j in order[i::K]}))
        out[s] = lst
    return out


# ---------------------------------------------------------------- the models
# Each takes train = {style: {pair: d}}, and returns predict(style, pair).

def m_nothing(train):
    return lambda s, p: 0.0


def m_mean(train):
    mu = {s: float(np.mean(list(train[s].values()))) for s in STYLES}
    return lambda s, p: mu[s]


def m_shipped(train):
    fits = {s: bench_fit.fit_judgments(train[s]) for s in STYLES}
    return lambda s, p: float(fits[s]["predict"](p))


def m_ridge_id(train):
    fits = {s: bench_fit.fit_judgments(train[s]) for s in STYLES}
    return lambda s, p: float(fits[s]["predict_ridge"](p))


def _pooled(train, names):
    rows = [(s, p, d) for s in STYLES for p, d in train[s].items()]
    X = np.vstack([X_of(s, [p], names) for s, p, _ in rows])
    y = np.array([d for *_, d in rows])
    return X, y


def m_feat_ridge(train, alpha=30.0, names=NAMES):
    X, y = _pooled(train, names)
    sc = StandardScaler().fit(X)
    mdl = Ridge(alpha=alpha).fit(sc.transform(X), y)
    return lambda s, p: float(mdl.predict(sc.transform(X_of(s, [p], names)))[0])


def m_feat_gbm(train, names=NAMES):
    X, y = _pooled(train, names)
    mdl = HistGradientBoostingRegressor(loss="absolute_error", max_depth=3, learning_rate=0.05,
                                        max_iter=200, min_samples_leaf=10, random_state=0).fit(X, y)
    return lambda s, p: float(mdl.predict(X_of(s, [p], names))[0])


def m_optical(train):
    """Classical, no ML: his desired 2-D gap and depth-limited area are a
    per-CLASS constant (Tracy / HT Letterspacer's premise), so d = target -
    current.  Two numbers per class and style, fitted as medians."""
    cls = lambda p: bench_fit.pair_class(p)
    tgt = {}
    for s in STYLES:
        for c in ("lower", "cap", "mark"):
            v = [(FEATS[s][p]["f"]["area_x"] + d, FEATS[s][p]["f"]["d2"] + d)
                 for p, d in train[s].items() if cls(p) == c]
            tgt[(s, c)] = np.median(np.array(v), axis=0) if v else (0, 0)

    def pred(s, p):
        f = FEATS[s][p]["f"]; ta, td = tgt[(s, cls(p))]
        return float(0.5 * (ta - f["area_x"]) + 0.5 * (td - f["d2"]))
    return pred


def m_hybrid(train, alpha_id=1.0, alpha_f=30.0):
    """Glyph identity (the shipped model's two bearings per glyph) AND shape
    features in one ridge, per style: identity says what he wants of THIS
    glyph, features carry it to glyphs and pairs he has not judged."""
    fits = {}
    for s in STYLES:
        J = train[s]
        pairs = sorted(J)
        glyphs = sorted({c for p in pairs for c in p})
        gi = {c: i for i, c in enumerate(glyphs)}
        G = len(glyphs)
        Xf = X_of(s, pairs)
        sc = StandardScaler().fit(Xf)
        Xf = sc.transform(Xf)
        A = np.zeros((len(pairs), 2 * G))
        for r, p in enumerate(pairs):
            A[r, 2 * gi[p[0]] + 1] = 1; A[r, 2 * gi[p[1]]] = 1
        Z = np.hstack([A, Xf, np.ones((len(pairs), 1))])
        pen = np.r_[np.full(2 * G, alpha_id), np.full(Xf.shape[1], alpha_f), 0.0]
        y = np.array([J[p] for p in pairs])
        w = np.linalg.solve(Z.T @ Z + np.diag(pen), Z.T @ y)
        fits[s] = (gi, G, sc, w)

    def pred(s, p):
        gi, G, sc, w = fits[s]
        z = np.zeros(2 * G)
        if p[0] in gi: z[2 * gi[p[0]] + 1] = 1
        if p[1] in gi: z[2 * gi[p[1]]] = 1
        xf = sc.transform(X_of(s, [p]))[0]
        return float(np.r_[z, xf, 1.0] @ w)
    return pred


def m_ensemble(train):
    a, b = m_ridge_id(train), m_feat_gbm(train)
    return lambda s, p: 0.5 * a(s, p) + 0.5 * b(s, p)


MODELS = [("do nothing", m_nothing), ("his training mean (tracking only)", m_mean),
          ("SHIPPED ridge pipeline (bench_fit)", m_shipped),
          ("identity ridge, continuous", m_ridge_id),
          ("C  optical: per-class target area + 2-D gap", m_optical),
          ("B  features -> ridge", m_feat_ridge),
          ("B  features -> gradient boosting", m_feat_gbm),
          ("B  hybrid: identity + features, one ridge", m_hybrid),
          ("B  ensemble: identity ridge + GBM", m_ensemble)]


def evaluate(make, FO):
    J = {s: bench_fit.judgments(s) for s in STYLES}
    errs = {s: [] for s in STYLES}
    preds = {s: {} for s in STYLES}
    per_rep = []
    for r in range(REPEATS):
        rep = []
        for i in range(K):
            held = {s: FO[s][r * K + i][2] for s in STYLES}
            train = {s: {p: d for p, d in J[s].items() if p not in held[s]} for s in STYLES}
            f = make(train)
            for s in STYLES:
                for p in held[s]:
                    v = f(s, p)
                    e = abs(v - J[s][p])
                    errs[s].append((p, e)); rep.append(e)
                    preds[s].setdefault(p, []).append(v)
        per_rep.append(np.mean(rep))
    return errs, {s: {p: float(np.mean(v)) for p, v in preds[s].items()} for s in STYLES}, per_rep


def reask_score(preds):
    key = {(r["style"], r["id"]): r for r in json.load(open(REASK_KEY))["rows"]}
    ans = json.load(open(REASK_ANS))["answers"]
    typ, out = [], []
    for a in ans:
        r = key[(a["style"], a["id"])]
        p = r["pair"]
        if p not in preds[r["style"]]:
            continue
        e = abs(preds[r["style"]][p] - a["delta"])
        (typ if r["stratum"] == "typical" else out).append(e)
    return np.mean(typ), np.mean(out), len(typ), len(out)


def main():
    FO = folds()
    J = {s: bench_fit.judgments(s) for s in STYLES}
    print(f"judgments: roman {len(J['roman'])}, italic {len(J['italic'])} (g dropped); "
          f"{len(NAMES)} features")
    print(f"{'model':46s} {'roman':>6s} {'italic':>6s} {'BOTH':>6s} {'shuffles':>13s}"
          f" {'lower':>6s} {'cap':>6s} {'mark':>6s} | {'reask typ':>9s} {'out':>6s}  sec")
    results = {}
    for name, make in MODELS:
        t = time.time()
        errs, preds, per = evaluate(make, FO)
        dt = time.time() - t
        er = np.mean([e for _, e in errs["roman"]]); ei = np.mean([e for _, e in errs["italic"]])
        allE = [e for s in STYLES for _, e in errs[s]]
        bycls = {c: np.mean([e for s in STYLES for p, e in errs[s] if bench_fit.pair_class(p) == c])
                 for c in ("lower", "cap", "mark")}
        rt, ro, nt, no = reask_score(preds)
        results[name] = dict(roman=er, italic=ei, both=float(np.mean(allE)), lo=min(per), hi=max(per),
                             reask_typ=rt, reask_out=ro, **bycls)
        print(f"{name:46s} {er:6.2f} {ei:6.2f} {np.mean(allE):6.2f} {min(per):6.2f}..{max(per):5.2f}"
              f" {bycls['lower']:6.2f} {bycls['cap']:6.2f} {bycls['mark']:6.2f} | {rt:9.2f} {ro:6.2f} {dt:5.1f}")
    print("\nreference lines: his repeatability 10.83 (typical, n=30); floor for any model 7.66;"
          " shipped ridge vs his NEW answer 13.14 (typical) / 31.94 (outlier)")
    print("\nsweep (LABELLED: chosen on held-out, so optimistic): feature-ridge alpha")
    for a in (3, 10, 30, 100, 300):
        errs, _, _ = evaluate(lambda tr, a=a: m_feat_ridge(tr, alpha=a), FO)
        print(f"   alpha {a:4d}: {np.mean([e for s in STYLES for _, e in errs[s]]):.2f}")
    print("\nablation: geometry only (no class flags) -> ridge / GBM")
    for nm, mk in (("ridge", lambda tr: m_feat_ridge(tr, names=GEOM)), ("gbm", lambda tr: m_feat_gbm(tr, names=GEOM))):
        errs, _, _ = evaluate(mk, FO)
        print(f"   {nm}: {np.mean([e for s in STYLES for _, e in errs[s]]):.2f}")
    json.dump(results, open(os.path.join(HERE, "probe_fit-results.json"), "w"), indent=1)


if __name__ == "__main__" and not {"--paired", "--curve"} & set(sys.argv):
    main()


def paired(a="SHIPPED ridge pipeline (bench_fit)", bs=("B  hybrid: identity + features, one ridge",
                                                       "B  features -> ridge")):
    """Paired comparison on identical held-out rows: mean error difference with
    a bootstrap interval over PAIRS (each pair's 5 repeats averaged first, so a
    pair is one unit), and how often each model is the closer one."""
    FO = folds()
    mk = dict(MODELS)
    def per_pair(name):
        errs, _, _ = evaluate(mk[name], FO)
        acc = {}
        for s in STYLES:
            for p, e in errs[s]:
                acc.setdefault((s, p), []).append(e)
        return {k: np.mean(v) for k, v in acc.items()}
    A = per_pair(a)
    rng = np.random.default_rng(1)
    for b in bs:
        B = per_pair(b)
        keys = sorted(A)
        d = np.array([A[k] - B[k] for k in keys])
        boots = [rng.choice(d, len(d)).mean() for _ in range(4000)]
        print(f"{b} vs {a}: gain {d.mean():+.2f} units (95% {np.percentile(boots, 2.5):+.2f}.."
              f"{np.percentile(boots, 97.5):+.2f}); closer on {np.mean(d > 0):.0%}, worse on {np.mean(d < 0):.0%}")


if __name__ == "__main__" and "--paired" in sys.argv:
    paired()


def curve(fracs=(0.4, 0.6, 0.8, 1.0)):
    """Learning curve: held-out error when each training fold is thinned to a
    fraction of itself (seeded).  A curve still falling at 1.0 says more rows
    of the SAME kind would pay; a flat one says they would not."""
    FO = folds()
    J = {s: bench_fit.judgments(s) for s in STYLES}
    for name in ("SHIPPED ridge pipeline (bench_fit)", "B  hybrid: identity + features, one ridge"):
        make = dict(MODELS)[name]
        row = []
        for fr in fracs:
            rng = np.random.default_rng(3)
            errs = []
            for r in range(2):
                for i in range(K):
                    held = {s: FO[s][r * K + i][2] for s in STYLES}
                    train = {}
                    for s in STYLES:
                        pool = sorted(p for p in J[s] if p not in held[s])
                        keep = rng.choice(len(pool), int(round(fr * len(pool))), replace=False)
                        train[s] = {pool[j]: J[s][pool[j]] for j in keep}
                    f = make(train)
                    errs += [abs(f(s, p) - J[s][p]) for s in STYLES for p in held[s]]
            row.append(f"{fr:.0%} ({int(fr*333)} rows): {np.mean(errs):.2f}")
        print(f"{name}:  " + "   ".join(row))


if __name__ == "__main__" and "--curve" in sys.argv:
    curve()
