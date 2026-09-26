#!/usr/bin/env python3
"""Round 391: thick and thin, per letter, grouped by CONSTRUCTION FAMILY.

Reads `cmp_weight_survey.py --json` output (one file holding a roman and an
italic survey) and regroups it by the four-family map of
docs/albo-misfit-audit-2026-09-18.md, then reports for every letter:

    thin    p10 of the chamfer ridge's thickness (units)
    stroke  median
    thick   p90
    cut     thick / thin (the letter's own contrast)
    colour  ink in the reading band / (advance x reference height)
    dThin, dCut, dCol   the letter against its family's median, as a ratio - 1
    px27    the thin stroke in pixels at a 27 px em (the 1x app reading size)

A letter is listed as an OUTLIER when its thin is more than 25% under its
family's, its cut more than 30% over, or its colour more than 15% off.

    python3 instruments/r391_thick_thin.py WS.json [WS_after.json]
With two files, prints before -> after for every letter that moved.
"""
import json, sys
import numpy as np

FAM = {"round": set("acegosCGOQS"), "diag": set("vwxyzAVWXYZ"), "figure": set("0123456789")}
def fam(ch):
    for k, s in FAM.items():
        if ch in s: return k
    return "stem"

def load(path):
    d = json.load(open(path)); out = {}
    for style, groups in d.items():
        rows = [r for g in groups.values() for r in g]
        out[style] = {r["ch"]: r for r in rows}
    return out

def table(data):
    res = {}
    for style, rows in data.items():
        fams = {}
        for ch, r in rows.items(): fams.setdefault(fam(ch), []).append(r)
        med = {f: dict(thin=np.median([r["thin"] for r in rs]),
                       cut=np.median([r["thick"] / r["thin"] for r in rs]),
                       colour=np.median([r["colour"] for r in rs]),
                       stroke=np.median([r["stroke"] for r in rs])) for f, rs in fams.items()}
        res[style] = (med, {ch: dict(r, fam=fam(ch), cut=r["thick"] / r["thin"],
                                     dThin=r["thin"] / med[fam(ch)]["thin"] - 1,
                                     dCut=(r["thick"] / r["thin"]) / med[fam(ch)]["cut"] - 1,
                                     dCol=r["colour"] / med[fam(ch)]["colour"] - 1,
                                     px27=r["thin"] * 27 / 1000.0)
                            for ch, r in rows.items()})
    return res

def main():
    A = table(load(sys.argv[1]))
    B = table(load(sys.argv[2])) if len(sys.argv) > 2 else None
    for style, (med, rows) in A.items():
        print(f"\n=== {style} ===")
        for f, m in med.items():
            print(f"  family {f:6s} thin {m['thin']:5.1f}  stroke {m['stroke']:5.1f}  cut {m['cut']:4.2f}  colour {m['colour']:.3f}")
        print(f"  {'ch':2s} {'fam':6s} {'thin':>5s} {'strk':>5s} {'thick':>5s} {'cut':>5s} {'col':>6s} {'dThin':>6s} {'dCut':>6s} {'dCol':>6s} {'px27':>5s}")
        for ch, r in sorted(rows.items(), key=lambda kv: (kv[1]["fam"], kv[0])):
            flag = []
            if r["dThin"] < -0.25: flag.append("THIN")
            if r["dCut"] > 0.30: flag.append("CUT")
            if abs(r["dCol"]) > 0.15: flag.append("COL")
            line = (f"  {ch:2s} {r['fam']:6s} {r['thin']:5.1f} {r['stroke']:5.1f} {r['thick']:5.1f} {r['cut']:5.2f} "
                    f"{r['colour']:6.3f} {r['dThin']:+6.0%} {r['dCut']:+6.0%} {r['dCol']:+6.0%} {r['px27']:5.2f} {' '.join(flag)}")
            if B:
                b = B[1 - 1 if False else 0] if False else B[style][1].get(ch)
                if b and (abs(b["thin"] - r["thin"]) > 0.05 or abs(b["colour"] - r["colour"]) > 0.0005):
                    line += (f"  -> thin {b['thin']:5.1f} strk {b['stroke']:5.1f} thick {b['thick']:5.1f} "
                             f"cut {b['cut']:4.2f} col {b['colour']:.3f} dThin {b['dThin']:+.0%} dCut {b['dCut']:+.0%} dCol {b['dCol']:+.0%}")
                elif not B: pass
            print(line)

if __name__ == "__main__":
    main()
