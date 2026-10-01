#!/usr/bin/env python3
"""Clearance kerns for a B2 refit, measured, per cut -- no hand step.

WHY. Three refits running (rounds 396-398, and 402), the italic q's right side
moved further in with his answers (-4, -9, -11) and a different set of q pairs
fell under cmp_touch's 0.012 em floor each time, which was then patched by a
hand-typed list in kern.py. This measures the built cuts with cmp_touch itself
(the gate, not a re-implementation of it), and for every pair under the floor
writes the kern that lifts it to TARGET em, into the table file's "clearance"
block, keyed by cut. kern.py applies that block under the B2 switch, after
everything else. Iterate: build, run this, rebuild, until it reports nothing.

    $VENV/bin/python clearance.py BUILD_DIR     # adds to the table named by ALBO_SPACING_TABLES
    $VENV/bin/python clearance.py BUILD_DIR --composites   # the accented pairs (round 449)
"""
import json, math, os, re, subprocess, sys
from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import b2_fit  # noqa: E402

CUTS = ("Regular", "Italic", "Bold", "BoldItalic")
TARGET = 0.015        # em; round 384's "floor plus a few units"


def under_floor(ttf, composites=False):
    args = ["--composites"] if composites else []
    out = subprocess.run(["python3", os.path.join(WS, "cmp_touch.py"), ttf] + args, capture_output=True, text=True,
                         env={**os.environ, "PYTHON_GIL": "0"}, cwd=WS).stdout
    rows = []
    for line in out.splitlines():
        m = re.match(r"^  (\S\S)\s+(-?[0-9.]+)\s+<-- (under the floor|TOUCHING)", line)
        if m:
            k = re.search(r"kern_em (-?[0-9.]+)", line)
            rows.append((m[1], float(m[2]), float(k[1]) if k else None))
    return rows


def main():
    # ROUND 449: --composites sweeps the pairs with an accented letter
    # (cmp_touch.py --composites) and writes the "clearance_composite" block.
    # kern.py applies that block AFTER every composite has inherited its base
    # pair's value (`_extend_composites`), so each kern here is a delta on the
    # inherited value. Written into "clearance" it would land before the
    # inheritance as a bare delta, and be kept as an explicit ruling.
    composites = "--composites" in sys.argv[1:]
    build = [x for x in sys.argv[1:] if not x.startswith("--")][0]
    data = json.load(open(b2_fit.OUT))
    clr = data.setdefault("clearance_composite" if composites else "clearance", {})
    added = 0
    for cut in CUTS:
        ttf = os.path.join(build, f"Albo-{cut}.ttf")
        f = TTFont(ttf); cmap = f.getBestCmap(); upm = f["head"].unitsPerEm
        for pair, gap, kern_em in under_floor(ttf, composites):
            names = [cmap.get(ord(c)) for c in pair]
            if None in names:
                continue
            k = math.ceil((TARGET - gap) * upm)
            if composites and "--cap" in sys.argv[1:]:
                # round 449's cap, now opt-in: never open an accented pair past
                # its unkerned position. It existed because the composites' left
                # sidebearings drew every mark-wide accented letter shifted right
                # (the bold i-dieresis by 113 units), so "unkerned" contacts were
                # the bug's, and kerns would have papered over it. Round 450 fixed
                # the sidebearings; an accent that meets its neighbour with no kern
                # is now the mark's own contact and gets the clearance a base pair
                # gets (italic i-acute before the ascender-high ?: "Aqui?").
                k = min(k, max(0, math.ceil(-(kern_em or 0.0) * upm)))
                if k <= 0:
                    print(f"  {cut:10s} {pair}  {gap:.4f} em  unkerned -- left to the drawing")
                    continue
            key = names[0] + " " + names[1]
            clr.setdefault(cut, {})[key] = clr.get(cut, {}).get(key, 0) + k
            added += 1
            print(f"  {cut:10s} {pair}  {gap:.4f} em  -> +{k}")
    json.dump(data, open(b2_fit.OUT, "w"), indent=1, ensure_ascii=False, sort_keys=True)
    print(f"{added} {'composite ' if composites else ''}clearance kern(s) added to {os.path.basename(b2_fit.OUT)}")


if __name__ == "__main__":
    main()
