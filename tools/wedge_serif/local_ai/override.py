#!/usr/bin/env python3
"""The OVERRIDE arm: every pair he has TOUCHED ships at his own value.

Owner 2026-09-26, asked whether a pair he touched should ship at his exact
value instead of the ridge's blend: *"show me"*. Behind
ALBO_SPACING_OVERRIDE=touched (default off: round 398 unchanged).

WHAT COUNTS AS TOUCHED. Every reading where he moved the slider: the 370 bench
judgments (a bench 0 is not stored, so every bench row is a moved slider), the
40 re-ask answers, the 50 outlier-bench answers, and the active sessions' rows
EXCEPT the skipped ones (verdict skipped-ok) -- a skip says "fine", it is not
his value for the pair. The g stays out, as everywhere in the fit (owner
2026-09-21). Several readings of a pair: their MEAN.

HOW IT SHIPS. Everything is on the fit's zero (the 2026-09-20 bench fonts, no
tracking): target white = white(pair, 09-20 font) + mean reading + tracking c
(which the build adds on top of every table). The override kern is
target white - white(pair, the B2 build), measured with HarfBuzz, and is ADDED
to what the pair carries in kern.py under the flag. So the arm = round 398
with his touched pairs moved to exactly his number; B2 sets everything else.

    $VENV/bin/python override.py write B2_DIR      # measure and write overrides into spacing_b2.json
    $VENV/bin/python override.py check             # first answer vs second, against the model
"""
import json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, WS)
import bench_fit  # noqa: E402
import b2_fit  # noqa: E402
from b2_fit import white_fn  # noqa: E402
from active_ingest import track_c  # noqa: E402

BENCH = os.path.join(WS, "bench")
OUT = b2_fit.OUT
FN = {"roman": "Albo-Regular.ttf", "italic": "Albo-Italic.ttf"}
STYLES = ("roman", "italic")
# The middle arm ("consistent"): his value only where he answered the pair 2+
# times and every reading lies within this spread (max - min), units. 11 is
# his measured repeatability, rounded (re-ask 10.83; sessions 1-4 mean 10.7).
CONSIST = 11


def touched(style, drop=("g",)):
    """{pair: [(d on the 09-20 zero, when, source)]}, chronological."""
    out = {}
    stamp = {}
    for p, d in bench_fit.judgments(style, drop).items():
        out.setdefault(p, []).append((float(d), "2026-09-21", "bench"))
    key = {(r["style"], r["id"]): r for r in json.load(open(os.path.join(BENCH, "reask-2026-09-25.key.json")))["rows"]}
    for a in json.load(open(os.path.join(BENCH, "answers", "reask-2026-09-25-answers.json")))["answers"]:
        r = key[(a["style"], a["id"])]
        if a["style"] == style and not any(c in drop for c in r["pair"]):
            out.setdefault(r["pair"], []).append((float(a["delta"]), a["at"], "reask"))
    for r in json.load(open(os.path.join(BENCH, "answers", "extra-judgments.json")))["rows"]:
        if r["style"] != style or any(c in drop for c in r["pair"]) or r.get("verdict") == "skipped-ok":
            continue
        out.setdefault(r["pair"], []).append((float(r["d0920"]), r.get("at") or r["bench"], r["bench"]))
    for p in out:
        out[p].sort(key=lambda t: t[1])
    return out


def write(b2_dir):
    data = json.load(open(OUT))
    for style in STYLES:
        T = touched(style)
        w20 = white_fn(os.path.join(BENCH, "fonts-2026-09-20", FN[style]))
        wb2 = white_fn(os.path.join(b2_dir, FN[style]))
        ov, ovc = {}, {}
        for p, rs in sorted(T.items()):
            # his readings are on the fit's zero, which has no tracking; the
            # build adds tracking c on top, so the target in today's font does too
            target = w20(p[0], p[1]) + np.mean([d for d, _, _ in rs]) + track_c(p)
            k = int(round(target - wb2(p[0], p[1])))
            if k:
                ov[p] = k
                ds = [d for d, _, _ in rs]
                if len(ds) >= 2 and max(ds) - min(ds) <= CONSIST:
                    ovc[p] = k
        data[style]["overrides"] = ov
        data[style]["overrides_consistent"] = ovc
        v = np.array(list(ov.values())); vc = np.array(list(ovc.values()) or [0])
        n2 = sum(1 for rs in T.values() if len(rs) >= 2)
        print(f"{style}: {len(T)} touched pairs, {len(ov)} move; mean |k| {np.abs(v).mean():.2f}, max {np.abs(v).max()}"
              f" | consistent: {n2} answered 2+ times, {len(ovc)} agree within {CONSIST} and move; "
              f"mean |k| {np.abs(vc).mean():.2f}, max {np.abs(vc).max()}")
    json.dump(data, open(OUT, "w"), indent=1, ensure_ascii=False, sort_keys=True)
    print("wrote overrides into", OUT)


def check():
    """For every pair he answered twice or more: does his FIRST reading predict
    his SECOND better than B2 does? B2 is refit per pair on every reading
    except that pair's second and later ones (so it has seen the first, as it
    had when the ship decision is made). Scored on the 09-20 zero."""
    import features as FT
    fonts = {s: FT.Font(p) for s, p in FT.FONTS.items()}
    rows = []
    for style in STYLES:
        T = touched(style)
        R = b2_fit.readings(style)            # the fit's own readings (skips included, as shipped)
        pairs = [p for p, rs in T.items() if len(rs) >= 2 and b2_fit.in_scope(p)]
        feats = {p: FT.pair_features(fonts[style], p[0], p[1], style == "italic")[0]
                 for p in R if b2_fit.in_scope(p) or p in bench_fit.judgments(style)}
        for p in pairs:
            first, second = T[p][0], T[p][1]
            reads = {q: v for q, v in R.items() if q != p}
            reads[p] = [(first[0], "bench")]
            J, W = b2_fit.combine(reads, 1.0)
            J = {q: v for q, v in J.items() if q in feats}
            pred = b2_fit.fit(style, J, feats, W)[2](p)
            rows.append(dict(style=style, pair=p, first=first[0], second=second[0], src=second[2],
                             model=pred, e_first=abs(first[0] - second[0]), e_model=abs(pred - second[0])))
    ef = np.array([r["e_first"] for r in rows]); em = np.array([r["e_model"] for r in rows])
    print(f"pairs answered twice: {len(rows)}")
    print(f"  his first answer vs his second: mean |error| {ef.mean():.2f}")
    print(f"  B2 (fit with his first, not his second): {em.mean():.2f}")
    print(f"  first closer on {int((ef < em).sum())}, model closer on {int((em < ef).sum())}, ties {int((ef == em).sum())}")
    by = {}
    for r in rows:
        k = r["src"] if r["src"] in ("reask",) else ("outliers" if r["src"].startswith("outliers")
                                                      else "active " + r["src"].rsplit("-", 1)[-1])
        by.setdefault(k, []).append(r)
    for k, v in sorted(by.items()):
        print(f"  second reading from {k:10s} n={len(v):3d}  first {np.mean([r['e_first'] for r in v]):5.2f}  model {np.mean([r['e_model'] for r in v]):5.2f}")
    json.dump(rows, open(os.path.join(HERE, "override-check-2026-09-26.json"), "w"), indent=1)
    return rows


if __name__ == "__main__":
    if sys.argv[1] == "write":
        write(sys.argv[2])
    else:
        check()
