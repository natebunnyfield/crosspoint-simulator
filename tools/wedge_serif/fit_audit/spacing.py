"""Axis (f): how hard the SPACING has to fight a glyph.

Two kinds of evidence, both his:

  B2 (outlines/spacing_b2.json, read from a git revision so a concurrent refit
  cannot move the ruler mid-audit): the ridge fitted on every answer he gave.
    b2_bearing  |lsb| + |rsb| of the glyph's identity coefficients (lowercase;
                capitals never become bearings, round 308) -- how far the
                rule-built fitting was from what he wanted, in units.
    b2_kern     mean |kern| over the B2 kerns the glyph is in -- what the
                bearings could not absorb and a per-pair patch had to.
  THE BENCH (bench_values.json literal + bench/answers/extra-judgments.json,
  exactly the readings b2_fit.py uses): his delta on every pair he judged.
    bench_push  per side of the glyph (its right side = pairs where it is
                left, its left side = pairs where it is right), a t-like
                consistency |mean d| * sqrt(n) / (sd + 4), max of the two
                sides. A glyph he pushes the SAME way pair after pair is a
                glyph whose own sidebearing is wrong; noise cancels.

Figures have no answers (NaN). The bolds were never benched (NaN).

    python3 spacing.py --rev HEAD --out spacing.json
"""
import argparse, json, os, subprocess, sys
from collections import defaultdict
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import WS, REPO, LC, UC  # noqa: E402

STYLE_CUT = {"roman": "Regular", "italic": "Italic"}


def git_json(rev, rel):
    out = subprocess.run(["git", "-C", REPO, "show", f"{rev}:{rel}"], capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def readings(style, rev):
    """{pair: [d, ...]} -- b2_fit.readings(), from the revision."""
    lit = git_json(rev, "tools/wedge_serif/bench_values.json")["literal"][style]
    R = defaultdict(list)
    for p, d in lit.items():
        if d and "g" not in p:
            R[p].append(float(d))
    ex = git_json(rev, "tools/wedge_serif/bench/answers/extra-judgments.json")["rows"]
    for r in ex:
        if r["style"] == style and "g" not in r["pair"]:
            R[r["pair"]].append(float(r["d0920"]))
    return R


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rev", default="HEAD")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    b2 = git_json(a.rev, "tools/wedge_serif/outlines/spacing_b2.json")
    res = {"rev": subprocess.run(["git", "-C", REPO, "rev-parse", "--short", a.rev],
                                 capture_output=True, text=True).stdout.strip()}
    for style, cut in STYLE_CUT.items():
        T = b2[style]
        letters, kerns = T["letters"], T["kerns"]
        R = readings(style, a.rev)
        out = {}
        for ch in LC + UC:
            row = {}
            if ch in letters:
                l, r = letters[ch]
                row["b2_lsb"], row["b2_rsb"] = l, r
                row["b2_bearing"] = abs(l) + abs(r)
            ks = [abs(v) for p, v in kerns.items() if len(p) == 2 and ch in p and p[0].isalpha() and p[1].isalpha()]
            row["b2_kern"] = float(np.mean(ks)) if ks else 0.0
            row["b2_nkern"] = len(ks)
            sides = {}
            for side, idx in (("right", 0), ("left", 1)):
                ds = [np.mean(v) for p, v in R.items() if len(p) == 2 and p[idx] == ch]
                if len(ds) >= 3:
                    m, sd = float(np.mean(ds)), float(np.std(ds))
                    sides[side] = dict(n=len(ds), mean=m, sd=sd, t=abs(m) * np.sqrt(len(ds)) / (sd + 4.0))
            row["bench"] = sides
            row["bench_push"] = max([s["t"] for s in sides.values()], default=float("nan"))
            out[ch] = row
        res[cut] = out
    json.dump(res, open(a.out, "w"), indent=1)
    for cut in STYLE_CUT.values():
        top = sorted(((v["bench_push"] if v["bench_push"] == v["bench_push"] else 0, k) for k, v in res[cut].items()), reverse=True)[:8]
        print(cut, "bench_push top:", " ".join(f"{k}:{t:.1f}" for t, k in top))


if __name__ == "__main__":
    main()
