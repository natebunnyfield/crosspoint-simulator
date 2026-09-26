#!/usr/bin/env python3
"""Measure every arm x cut: the touch gate, how far the arm moves each cut
against today, and the white of the pairs he corrected most.

    $VENV/bin/python measure.py FONTS_DIR SNAPSHOT_WEDGE_SERIF > measure.txt

FONTS_DIR holds today/ b-stem/ c-rhythm/ d-b2/ (transfer.py); cmp_touch.py is
run from SNAPSHOT_WEDGE_SERIF (a HEAD snapshot) under the system python3, the
way gates.sh runs it.
"""
import json, os, re, subprocess, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import Font, census, MARKS  # noqa: E402
from transfer import CUTS, his_readings  # noqa: E402

ARMS = ["today", "b-stem", "c-rhythm", "d-b2"]
NAMED = ["um", "ks", "sw", "bj", "aj", "ej", "he", "sp"]


def touch(ttf, wedge):
    r = subprocess.run(["python3", "cmp_touch.py", ttf, "--top", "80"], cwd=wedge,
                       env=dict(os.environ, PYTHON_GIL="0"), capture_output=True, text=True)
    m = re.search(r"(\d+) pair\(s\) TOUCHING, (\d+) below", r.stdout)
    faults = []
    for line in r.stdout.splitlines():
        mm = re.match(r"\s+(\S+)\s+(-?\d+\.\d+)\s*(.*)$", line)
        if mm and "exempt" not in mm.group(3) and float(mm.group(2)) < 0.012:
            faults.append(f"{mm.group(1)} {float(mm.group(2)):+.4f}")
    return (int(m.group(1)), int(m.group(2)), faults) if m else (None, None, [r.stdout[-300:]])


def grid_pairs(reads, style, k=10):
    sc = []
    for p, ds in reads[style].items():
        if len(p) == 2 and p[0].islower() and p[1].islower() and "g" not in p:
            sc.append((abs(np.mean(ds)) * np.sqrt(len(ds)), p))
    top = [p for _, p in sorted(sc, reverse=True)]
    out = list(NAMED)
    for p in top:
        if p not in out:
            out.append(p)
        if len(out) >= len(NAMED) + k:
            break
    return out


def main():
    fonts, wedge = sys.argv[1], sys.argv[2]
    reads = his_readings()
    cen = [(p, n) for p, n in census(50)]
    res = {"touch": {}, "move": {}, "white": {}, "grid": {}, "his": {}}
    for style, cuts in CUTS.items():
        gp = grid_pairs(reads, style)
        res["grid"][style] = gp
        res["his"][style] = {p: dict(n=len(reads[style].get(p, [])),
                                     mean=round(float(np.mean(reads[style][p])), 1) if reads[style].get(p) else None)
                             for p in gp}
        for cut, wt in cuts:
            F0 = Font(os.path.join(fonts, "today", f"Albo-{cut}.ttf"))
            w0 = {}
            for p, n in cen:
                w = F0.white(p[0], p[1]) if all(ord(c) in F0.cmap for c in p) else None
                if w is not None:
                    w0[p] = (w, n)
            for arm in ARMS:
                path = os.path.join(fonts, arm, f"Albo-{cut}.ttf")
                F = Font(path)
                t = touch(path, wedge)
                res["touch"].setdefault(arm, {})[cut] = t
                d, wts = [], []
                for p, (w, n) in w0.items():
                    d.append(F.white(p[0], p[1]) - w); wts.append(n)
                d = np.array(d); wts = np.array(wts)
                res["move"].setdefault(arm, {})[cut] = dict(
                    mean_abs=round(float(np.average(np.abs(d), weights=wts)), 2),
                    mean=round(float(np.average(d, weights=wts)), 2),
                    max_abs=round(float(np.abs(d).max()), 1),
                    moved_ge4_pct=round(float(100 * wts[np.abs(d) >= 4].sum() / wts.sum()), 1))
                res["white"].setdefault(arm, {})[cut] = {p: F.white(p[0], p[1]) for p in gp}
                print(f"{style:6s} {cut:11s} {arm:9s} touch {t[0]}/{t[1]} {t[2][:4]}  "
                      f"move mean|d| {res['move'][arm][cut]['mean_abs']:5.2f} mean {res['move'][arm][cut]['mean']:+6.2f} "
                      f"max {res['move'][arm][cut]['max_abs']:5.1f} >=4u {res['move'][arm][cut]['moved_ge4_pct']:5.1f}%",
                      flush=True)
    json.dump(res, open(os.path.join(fonts, "measure.json"), "w"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
