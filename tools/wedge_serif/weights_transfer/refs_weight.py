#!/usr/bin/env python3
"""What do real serif families do to the WHITE between letters as the weight
goes up?  The evidence arm (b) and arm (c) of the weight-transfer study are
judged against (docs/albo-weights-transfer-2026-09-26.md §3).

For each family on this Mac with a regular and a heavier cut, per cut:
    stem      the n's left stem at mid x-height
    counter   the n's inner white at mid x-height (Tracy's control: half of it
              is the n's starting sidebearing)
    nsb       the n's mean sidebearing
    white     the census-weighted mean white (rsb + kern + lsb) over the 120
              most common lowercase pairs in the owner's own books
Each number is divided by the cut's own x-height, so families compare.
Then the heavy/regular RATIOS -- how the white moved against how the stem and
the counter moved.  Albo's six buildable cuts are measured the same way.

    $VENV/bin/python refs_weight.py [ALBO_FONT_DIR] > refs_weight.txt
"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import Font, census

SUP = "/System/Library/Fonts/Supplemental/"
FAM = [  # (family, [(label, path, index)]) -- regular first
    ("Palatino", [("Regular", "/System/Library/Fonts/Palatino.ttc", 0), ("Bold", "/System/Library/Fonts/Palatino.ttc", 2)]),
    ("Palatino It", [("Italic", "/System/Library/Fonts/Palatino.ttc", 1), ("Bold Italic", "/System/Library/Fonts/Palatino.ttc", 3)]),
    ("Baskerville", [("Regular", SUP + "Baskerville.ttc", 0), ("SemiBold", SUP + "Baskerville.ttc", 4), ("Bold", SUP + "Baskerville.ttc", 1)]),
    ("Baskerville It", [("Italic", SUP + "Baskerville.ttc", 2), ("Bold Italic", SUP + "Baskerville.ttc", 3)]),
    ("Charter", [("Regular", SUP + "Charter.ttc", 0), ("Bold", SUP + "Charter.ttc", 3), ("Black", SUP + "Charter.ttc", 5)]),
    ("Charter It", [("Italic", SUP + "Charter.ttc", 1), ("Bold Italic", SUP + "Charter.ttc", 2)]),
    ("Iowan", [("Regular", SUP + "Iowan Old Style.ttc", 0), ("Bold", SUP + "Iowan Old Style.ttc", 1), ("Black", SUP + "Iowan Old Style.ttc", 4)]),
    ("Iowan It", [("Italic", SUP + "Iowan Old Style.ttc", 2), ("Bold Italic", SUP + "Iowan Old Style.ttc", 3)]),
    ("Georgia", [("Regular", SUP + "Georgia.ttf", 0), ("Bold", SUP + "Georgia Bold.ttf", 0)]),
    ("Georgia It", [("Italic", SUP + "Georgia Italic.ttf", 0), ("Bold Italic", SUP + "Georgia Bold Italic.ttf", 0)]),
    ("Times", [("Regular", "/System/Library/Fonts/Times.ttc", 0), ("Bold", "/System/Library/Fonts/Times.ttc", 1)]),
    ("Cochin", [("Regular", SUP + "Cochin.ttc", 0), ("Bold", SUP + "Cochin.ttc", 1)]),
    ("Hoefler Text", [("Regular", SUP + "Hoefler Text.ttc", 0), ("Black", SUP + "Hoefler Text.ttc", 1)]),
    ("Superclarendon", [("Regular", SUP + "SuperClarendon.ttc", 0), ("Light", SUP + "SuperClarendon.ttc", 3), ("Bold", SUP + "SuperClarendon.ttc", 5), ("Black", SUP + "SuperClarendon.ttc", 7)]),
    ("Pagella", [("Regular", os.path.expanduser("~/Library/Fonts/texgyrepagella-regular.otf"), 0), ("Bold", os.path.expanduser("~/Library/Fonts/texgyrepagella-bold.otf"), 0)]),
    ("Pagella It", [("Italic", os.path.expanduser("~/Library/Fonts/texgyrepagella-italic.otf"), 0), ("Bold Italic", os.path.expanduser("~/Library/Fonts/texgyrepagella-bolditalic.otf"), 0)]),
]


def lc_pairs(k=120):
    out = [(p, n) for p, n in census() if p[0].islower() and p[1].islower()]
    return out[:k]


def measure(F, pairs):
    a = F.n_anatomy()
    xh = a["xh"]
    ws, wt = [], []
    for p, n in pairs:
        w = F.white(p[0], p[1])
        if w is not None:
            ws.append(w); wt.append(n)
    white = float(np.average(ws, weights=wt))
    return dict(stem=a["stem"] / xh, counter=a["counter"] / xh, nsb=(a["lsb"] + a["rsb"]) / 2 / xh,
                white=white / xh)


def main():
    pairs = lc_pairs()
    fams = list(FAM)
    if len(sys.argv) > 1:
        d = sys.argv[1]
        fams.append(("ALBO", [(s, os.path.join(d, f"Albo-{s}.ttf"), 0) for s in ("Regular", "ExtraLight", "Bold", "Black")]))
        fams.append(("ALBO It", [(s, os.path.join(d, f"Albo-{s}.ttf"), 0) for s in ("Italic", "BoldItalic")]))
    print("per x-height; ratios are this cut / the family's first cut")
    print(f"{'family':15s} {'cut':12s} {'stem':>6s} {'cntr':>6s} {'nsb':>6s} {'white':>6s} | "
          f"{'r_stem':>6s} {'r_cntr':>6s} {'r_nsb':>6s} {'r_white':>7s}  white-per-stem slope")
    slopes = {}
    for fam, cuts in fams:
        base = None
        for label, path, idx in cuts:
            if not os.path.exists(path):
                print(f"{fam:15s} {label:12s} MISSING {path}"); continue
            m = measure(Font(path, idx), pairs)
            if base is None:
                base = m; tail = ""
            else:
                ds = m["stem"] - base["stem"]
                sl = (m["white"] - base["white"]) / ds if abs(ds) > 1e-6 else float("nan")
                tail = f"  {sl:+.3f}"
                slopes.setdefault("italic" if "It" in fam else "roman", []).append((fam, label, sl,
                    m["white"] / base["white"], m["stem"] / base["stem"], m["counter"] / base["counter"]))
            r = {k: m[k] / base[k] for k in m}
            print(f"{fam:15s} {label:12s} {m['stem']:6.3f} {m['counter']:6.3f} {m['nsb']:6.3f} {m['white']:6.3f} | "
                  f"{r['stem']:6.2f} {r['counter']:6.2f} {r['nsb']:6.2f} {r['white']:7.2f}{tail}")
    print()
    print("SUMMARY over references (heavier cut vs the family's first cut), ALBO excluded:")
    for st, rows in slopes.items():
        rr = [r for r in rows if not r[0].startswith("ALBO")]
        if not rr:
            continue
        sl = np.array([r[2] for r in rr]); rw = np.array([r[3] for r in rr])
        rs = np.array([r[4] for r in rr]); rc = np.array([r[5] for r in rr])
        # how much of the stem ratio the white follows: (r_white-1)/(r_stem-1)
        follow = (rw - 1) / (rs - 1)
        print(f"  {st}: n={len(rr)}  white slope per unit stem median {np.median(sl):+.3f} "
              f"(range {sl.min():+.3f}..{sl.max():+.3f});  r_white median {np.median(rw):.2f}, "
              f"r_stem median {np.median(rs):.2f}, r_counter median {np.median(rc):.2f};  "
              f"white follows the stem ratio by a fraction median {np.median(follow):.2f} "
              f"(range {follow.min():.2f}..{follow.max():.2f})")


if __name__ == "__main__":
    main()
