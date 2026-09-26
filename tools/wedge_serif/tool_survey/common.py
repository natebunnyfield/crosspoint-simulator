#!/usr/bin/env python3
"""Shared scoring for the spacing-tool survey (docs/spacing-tools-survey-2026-09-26.md).

THE QUESTION. Owner 2026-09-26: "it seems overdue to see what other existing
tools can offer". Every tool here is run on Albo, its output is turned into a
predicted WHITE for each pair he has answered, and that is scored against his
own numbers with the SAME held-out folds the B2 fit was scored on.

THE ZERO. Every answer is stored as d on the 2026-09-20 bench fonts (the fonts
he judged first): he wants white(p) = white0920(p) + d. A tool that proposes
spacing proposes an absolute white W(p); its prediction of his answer is
W(p) - white0920(p). White is rsb + kern + lsb (bbox), gap_measure.py's measure
and b2_fit.white_fn's.

THE SCORES (mean |error|, design units, lower is better):
  raw370   the tool as it comes, on the 370 bench pairs, against his bench
           number (comparable with do-nothing 13.66).
  rawALL   the tool as it comes, on every answered pair, against the mean of
           his readings of that pair (bench + the three later benches).
  cal370   the tool plus ONE constant per style (its tracking), fitted on the
           training folds only -- the one knob every tool expects a designer
           to set by eye.
  lin370   a * tool + b per style, training folds only (tracking plus a gain:
           a tool whose moves are right in direction but wrong in size).
  res370   "tool + his correction": identity ridge (alpha 1, the B2 identity
           prior) fitted on d - tool_d, training folds only.
  b2t370   B2 (identity + 38 shape features) with the tool's d as a 39th
           feature, training folds only.
  All *370 CV scores train on bench + extras (skip weight 1), exactly as
  local_ai/probe_extra.py section A, whose B2 row is round 397's 10.33.
"""
import json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.dirname(HERE)
LA = os.path.join(WS, "local_ai")
sys.path.insert(0, LA); sys.path.insert(0, WS)
import bench_fit  # noqa: E402
import features as FT  # noqa: E402
import b2_fit  # noqa: E402
import probe_fit as PF  # noqa: E402

STYLES = ("roman", "italic")
# THE ANSWERS ARE PINNED. Active-bench session 3 was ingested while this
# survey ran (commit 2a3a27a), which moves every CV number. Every score here
# reads bench/answers/extra-judgments.json AS OF round 397 (c25375b: outlier
# bench + sessions 1-2, 150 rows), the state whose B2 scores 10.33. Set
# TOOL_SURVEY_EXTRAS=live to read the working-tree file instead.
EXTRAS_AT = os.environ.get("TOOL_SURVEY_EXTRAS", "c25375b")


def _extra_rows():
    rel = "tools/wedge_serif/bench/answers/extra-judgments.json"
    if EXTRAS_AT == "live":
        return json.load(open(os.path.join(WS, "bench", "answers", "extra-judgments.json")))["rows"]
    import subprocess
    txt = subprocess.run(["git", "-C", WS, "show", f"{EXTRAS_AT}:{rel}"], check=True,
                         capture_output=True, text=True).stdout
    return json.loads(txt)["rows"]


def readings(style, drop=("g",)):
    """b2_fit.readings, over the pinned extras."""
    reads = {p: [(d, "bench")] for p, d in bench_fit.judgments(style, drop).items()}
    for r in _extra_rows():
        if r["style"] == style and not any(c in drop for c in r["pair"]):
            cls = "skip" if r.get("verdict") == "skipped-ok" else "extra"
            reads.setdefault(r["pair"], []).append((r["d0920"], cls))
    return reads


PRED_DIR = os.path.join(HERE, "preds")
FONTSETS = {
    "0920": {"roman": os.path.join(WS, "bench", "fonts-2026-09-20", "Albo-Regular.ttf"),
             "italic": os.path.join(WS, "bench", "fonts-2026-09-20", "Albo-Italic.ttf")},
    "r397": {"roman": os.path.join(WS, "bench", "fonts-2026-09-26-r397", "Albo-Regular.ttf"),
             "italic": os.path.join(WS, "bench", "fonts-2026-09-26-r397", "Albo-Italic.ttf")},
}


def answered_pairs():
    """{style: sorted pairs} -- every pair with a reading (bench or later), no g,
    and measurable by features.py (the set probe_extra.py scores)."""
    out = {}
    J0 = {s: bench_fit.judgments(s) for s in STYLES}
    for s in STYLES:
        R = readings(s)
        out[s] = sorted(p for p in R if b2_fit.in_scope(p) or p in J0[s])
    return out


def words():
    """{(style, pair): a real word containing the pair} from the bench and key files."""
    w = {}
    items = json.load(open(os.path.join(WS, "bench", "bench-items-2026-09-20.json")))["items"]
    for it in items:
        p = it["pair"].replace(" ", "")
        for s in STYLES:
            w[(s, p)] = (it["word"], it["i"])
    import glob
    for kf in sorted(glob.glob(os.path.join(WS, "bench", "*.key.json"))):
        k = json.load(open(kf))
        rows = k.get("rows") or k.get("items") or []
        for r in rows:
            if not isinstance(r, dict) or "pair" not in r or "word" not in r:
                continue
            p = r["pair"].replace(" ", "")
            st = [r["style"]] if r.get("style") in STYLES else list(STYLES)
            i = r.get("i", r["word"].find(p))
            for s in st:
                w.setdefault((s, p), (r["word"], i))
    return w


class Truth:
    """His answers, the fit's zero, and the folds."""

    def __init__(self):
        self.P = answered_pairs()
        self.J0 = {s: bench_fit.judgments(s) for s in STYLES}
        self.R = {s: readings(s) for s in STYLES}
        self.Jall = {s: b2_fit.combine(self.R[s], 1.0)[0] for s in STYLES}
        self.white0920 = {s: {} for s in STYLES}
        for s in STYLES:
            wf = b2_fit.white_fn(FONTSETS["0920"][s])
            for p in self.P[s]:
                self.white0920[s][p] = float(wf(p[0], p[1]))
        self.FO = PF.folds()
        self._feats = None

    def feats(self):
        if self._feats is None:
            fonts = {s: FT.Font(p) for s, p in FT.FONTS.items()}
            self._feats = {s: {p: FT.pair_features(fonts[s], p[0], p[1], s == "italic")[0]
                               for p in self.P[s]} for s in STYLES}
        return self._feats

    def tool_d(self, pred_white):
        """{style: {pair: W}} -> {style: {pair: W - white0920}} (missing pairs dropped)."""
        return {s: {p: pred_white[s][p] - self.white0920[s][p]
                    for p in self.P[s] if p in pred_white.get(s, {})} for s in STYLES}


def identity_ridge(J, W=None, alpha=1.0):
    """d(a, b) = rsb[a] + lsb[b] + c, ridge alpha on the identity terms: the
    identity half of B2 on its own."""
    pairs = sorted(J)
    glyphs = sorted({c for p in pairs for c in p})
    gi = {c: i for i, c in enumerate(glyphs)}
    A = np.zeros((len(pairs), 2 * len(glyphs) + 1))
    for r, p in enumerate(pairs):
        A[r, 2 * gi[p[0]] + 1] = 1; A[r, 2 * gi[p[1]]] = 1; A[r, -1] = 1
    y = np.array([J[p] for p in pairs])
    sw = np.array([(W or {}).get(p, 1.0) for p in pairs])
    pen = np.r_[np.full(2 * len(glyphs), alpha), 0.0]
    w = np.linalg.solve(A.T @ (A * sw[:, None]) + np.diag(pen), A.T @ (sw * y))

    def predict(p):
        v = w[-1]
        if p[0] in gi: v += w[2 * gi[p[0]] + 1]
        if p[1] in gi: v += w[2 * gi[p[1]]]
        return float(v)
    return predict


def cv_scores(T, td, want=("nothing", "b2", "cal", "res", "b2t"), extras=True, keep=None, raw=False):
    """Held-out mean |error| on the 370 bench pairs (probe_extra.py A's folds
    and training set). td = {style: {pair: tool d}} or None (baselines only)."""
    feats = T.feats() if ("b2" in want or "b2t" in want) else None
    errs = {k: [] for k in want}
    for r in range(PF.REPEATS):
        for i in range(PF.K):
            for s in STYLES:
                held = T.FO[s][r * PF.K + i][2]
                train_out = held
                held = {p for p in held if (keep is None or keep(p)) and (td is None or p in td[s])}
                if extras:
                    reads = {p: v for p, v in T.R[s].items() if p not in train_out}
                else:
                    reads = {p: [(d, "bench")] for p, d in T.J0[s].items() if p not in train_out}
                J, W = b2_fit.combine(reads, 1.0)
                J = {p: v for p, v in J.items() if p in T.white0920[s]}
                if td is not None:
                    J = {p: v for p, v in J.items() if p in td[s] and (keep is None or keep(p))}
                tr = sorted(J)
                if "nothing" in want:
                    errs["nothing"] += [abs(T.J0[s][p]) for p in held]
                if "b2" in want:
                    pred = b2_fit.fit(s, J, feats[s], W)[2]
                    errs["b2"] += [abs(pred(p) - T.J0[s][p]) for p in held]
                if td is None:
                    continue
                t = td[s]
                if "cal" in want:
                    c = float(np.average([J[p] - t[p] for p in tr], weights=[W[p] for p in tr]))
                    errs["cal"] += [abs(t[p] + c - T.J0[s][p]) for p in held]
                if "lin" in want:
                    x = np.array([t[p] for p in tr]); yv = np.array([J[p] for p in tr]); wv = np.array([W[p] for p in tr])
                    A = np.vstack([x, np.ones_like(x)]).T
                    ab = np.linalg.lstsq(A * np.sqrt(wv)[:, None], yv * np.sqrt(wv), rcond=None)[0]
                    errs["lin"] += [abs(ab[0] * t[p] + ab[1] - T.J0[s][p]) for p in held]
                if "res" in want:
                    pr = identity_ridge({p: J[p] - t[p] for p in tr}, W)
                    errs["res"] += [abs(t[p] + pr(p) - T.J0[s][p]) for p in held]
                if "b2t" in want:
                    f2 = {p: dict(feats[s][p], tool=t[p]) for p in list(tr) + list(held)}
                    pred = b2_fit.fit(s, J, f2, W)[2]   # predict() reads f2, so held rows need theirs
                    errs["b2t"] += [abs(pred(p) - T.J0[s][p]) for p in held]
    if raw:
        return errs          # per held-out row, in the same order for every model
    return {k: float(np.mean(v)) for k, v in errs.items()}


def raw_scores(T, td, keep=None):
    if keep is not None:
        td = {s: {p: v for p, v in td[s].items() if keep(p)} for s in STYLES}
    """Untrained scores: the 370 against his bench number, and every answered
    pair against the mean of his readings."""
    e370 = [abs(td[s][p] - T.J0[s][p]) for s in STYLES for p in T.J0[s] if p in td[s]]
    eall = [abs(td[s][p] - T.Jall[s][p]) for s in STYLES for p in T.P[s] if p in td[s]]
    n0 = [abs(T.J0[s][p]) for s in STYLES for p in T.J0[s] if p in td[s]]
    nall = [abs(T.Jall[s][p]) for s in STYLES for p in T.P[s] if p in td[s]]
    # direction agreement where his answer is at least 15 units
    dirs = [np.sign(td[s][p]) == np.sign(T.Jall[s][p]) for s in STYLES for p in T.P[s]
            if p in td[s] and abs(T.Jall[s][p]) >= 15]
    # correlation of the tool's d with his
    x = [td[s][p] for s in STYLES for p in T.P[s] if p in td[s]]
    y = [T.Jall[s][p] for s in STYLES for p in T.P[s] if p in td[s]]
    by = {}
    for s in STYLES:
        by[s] = float(np.mean([abs(td[s][p] - T.Jall[s][p]) for p in T.P[s] if p in td[s]]))
    for c in ("lower", "cap", "mark"):
        by[c] = float(np.mean([abs(td[s][p] - T.Jall[s][p]) for s in STYLES for p in T.P[s]
                               if p in td[s] and bench_fit.pair_class(p) == c]))
    return dict(by=by, raw370=float(np.mean(e370)), n370=len(e370), nothing370=float(np.mean(n0)),
                rawALL=float(np.mean(eall)), nALL=len(eall), nothingALL=float(np.mean(nall)),
                dir15=float(np.mean(dirs)) if dirs else float("nan"), n_dir=len(dirs),
                r=float(np.corrcoef(x, y)[0, 1]),
                bias=float(np.mean(np.array(x) - np.array(y))))


def sidebearing_white(font_path, sb):
    """sb = {char: (lsb, rsb)} in bbox terms -> white(a, b) = rsb[a] + lsb[b] (no kern)."""
    def white(a, b):
        return sb[a][1] + sb[b][0]
    return white


def save_preds(name, fontset, pred_white, meta):
    os.makedirs(PRED_DIR, exist_ok=True)
    path = os.path.join(PRED_DIR, f"{name}-{fontset}.json")
    json.dump({"tool": name, "fontset": fontset, "meta": meta,
               "white": {s: {p: round(float(v), 2) for p, v in pred_white[s].items()} for s in STYLES}},
              open(path, "w"), indent=0, ensure_ascii=False)
    return path


def load_preds(name, fontset):
    d = json.load(open(os.path.join(PRED_DIR, f"{name}-{fontset}.json")))
    return d["white"], d["meta"]
