#!/usr/bin/env python3
"""Which pairs the B2 arm moved, weighted by how often his books use them.

    $VENV/bin/python b2_moved.py BASE_DIR B2_DIR bigrams.json [--top 30] [--json OUT]

White = rsb + kern + lsb, kern by HarfBuzz (liga off), measured on every
census pair both fonts can set, roman and italic. Ranked by |dwhite| x count.
"""
import argparse, json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from b2_fit import white_fn  # noqa: E402

FILES = {"roman": "Albo-Regular.ttf", "italic": "Albo-Italic.ttf"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("base"); ap.add_argument("b2"); ap.add_argument("census")
    ap.add_argument("--top", type=int, default=30); ap.add_argument("--json")
    a = ap.parse_args()
    data = json.load(open(a.census))
    census, carriers = data["pairs"], data["carriers"]
    total = sum(n for _, n in census)
    rows, summary = [], {}
    for style, fn in FILES.items():
        wb, w2 = white_fn(os.path.join(a.base, fn)), white_fn(os.path.join(a.b2, fn))
        ds, ns = [], []
        for p, n in census:
            try:
                d = w2(p[0], p[1]) - wb(p[0], p[1])
            except SystemExit:
                continue
            ds.append(d); ns.append(n)
            if d:
                word = carriers.get(p, [[p, 0]])[0][0]
                rows.append(dict(style=style, pair=p, n=n, d=int(d), score=abs(d) * n, word=word,
                                 before=int(wb(p[0], p[1])), after=int(w2(p[0], p[1]))))
        ds, ns = np.array(ds), np.array(ns)
        summary[style] = dict(pairs=len(ds), moved=int((ds != 0).sum()), moved4=int((abs(ds) >= 4).sum()),
                              wmean=float((ds * ns).sum() / ns.sum()), wabs=float((abs(ds) * ns).sum() / ns.sum()),
                              maxabs=int(abs(ds).max()))
        s = summary[style]
        print(f"{style}: {s['pairs']} census pairs; moved {s['moved']} ({s['moved4']} by 4+ units); "
              f"frequency-weighted mean dwhite {s['wmean']:+.2f}, mean |dwhite| {s['wabs']:.2f}, max {s['maxabs']}")
    rows.sort(key=lambda r: -r["score"])
    print(f"\ntop {a.top} by |dwhite| x count (of {total:,} pair instances):")
    print(f"  {'style':6s} {'pair':4s} {'count':>7s} {'before':>6s} {'after':>6s} {'d':>4s}  word")
    for r in rows[: a.top]:
        print(f"  {r['style']:6s} {r['pair']:4s} {r['n']:7d} {r['before']:6d} {r['after']:6d} {r['d']:+4d}  {r['word']}")
    if a.json:
        json.dump(dict(summary=summary, top=rows[: a.top], all=rows), open(a.json, "w"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
