#!/usr/bin/env python3
"""Score saved tool predictions (preds/<tool>-<fontset>.json) against his answers.

    $VENV/bin/python score.py htls kernagic-gap ...      (fontset 0920 unless --fontset)

Prints, per tool: raw370 / rawALL (untrained), and the held-out cal / res / b2t
columns (common.py explains each). Reference lines, same harness: do nothing
13.66, B2 as shipped in round 397 10.33, his repeatability 10.83.
"""
import argparse, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
import bench_fit  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tools", nargs="+")
    ap.add_argument("--fontset", default="0920")
    ap.add_argument("--json", help="append results to this json file")
    ap.add_argument("--letters", action="store_true",
                    help="score letter pairs only (no marks), with the baselines recomputed on that subset")
    a = ap.parse_args()
    T = C.Truth()
    res = {}
    keep = (lambda p: bench_fit.pair_class(p) != "mark") if a.letters else None
    if a.letters:
        base = C.cv_scores(T, None, want=("nothing", "b2"), keep=keep)
        print(f"letters only: nothing {base['nothing']:.2f}  B2(r397) {base['b2']:.2f}")
    for name in a.tools:
        white, meta = C.load_preds(name, a.fontset)
        td = T.tool_d(white)
        raw = C.raw_scores(T, td, keep)
        cv = C.cv_scores(T, td, want=("cal", "lin", "res", "b2t"), keep=keep)
        res[name] = dict(raw, **cv)
        print(f"{name:28s} raw370 {raw['raw370']:6.2f} (n{raw['n370']}, nothing {raw['nothing370']:.2f})  "
              f"rawALL {raw['rawALL']:6.2f} (n{raw['nALL']}, nothing {raw['nothingALL']:.2f})  "
              f"bias {raw['bias']:+6.1f}  r {raw['r']:+.2f}  dir15 {raw['dir15']:.0%}  |  "
              f"CV cal {cv['cal']:6.2f}  lin {cv['lin']:6.2f}  res {cv['res']:6.2f}  b2t {cv['b2t']:6.2f}\n{'':28s} rawALL by " +
              "  ".join(f"{k} {v:.2f}" for k, v in raw['by'].items()), flush=True)
    if a.json:
        old = json.load(open(a.json)) if os.path.exists(a.json) else {}
        old.update({f"{k}@{a.fontset}" + ("@letters" if a.letters else ""): v for k, v in res.items()})
        json.dump(old, open(a.json, "w"), indent=1)


if __name__ == "__main__":
    main()
