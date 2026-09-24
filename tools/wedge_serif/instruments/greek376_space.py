#!/usr/bin/env python3
"""Round 379: is each GREEK side spaced like its LATIN ANALOGUE, the way the
reference Greek fonts space it?

There is no owner bench for the Greek, so build.py's GREEK_SIDES gives every
Greek side the shipped bearing of the Latin letter whose side it is. This
checks that transfer against the references, with no assumption about
whether Albo is looser or tighter than they are overall: in EACH face it
measures a Greek side's white and its Latin analogue's white against the same
partners (`cmp_space_2d.Face.gap`: the closest approach in two dimensions on
the shaped pair, in em), and takes the DIFFERENCE. If Albo's Greek-minus-Latin
difference sits on the references' median difference, the Greek is spaced
relative to Albo's own Latin as the references space theirs.

    PYTHON_GIL=0 python3 instruments/greek376_space.py A.ttf [B.ttf ...] [--style roman|italic|bold] [--fit]

`--fit` prints, for the LAST font given, build.py's GREEK_SIDE_ADJ row for
that style: the table the font was built with plus the correction that puts
each side OUTSIDE the references' spread onto the nearer edge of it (a side
inside the spread is left where the analogue put it), clamped to +-CLAMP. A
side's correction is (band edge - Albo) x 1000 units: moving a glyph by d
units moves its closest approach to a partner by at most d, so one pass lands
short where the nearest point is diagonal, and a second pass is the check.

Partners: the lowercase 'aeinorstu' for the lowercase, 'HOEDN' for the
capitals. References: the four faces with Greek on this Mac (cmp_greek.REFS).
"""
import os, sys, argparse, statistics as st
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import cmp_space_2d as CS
import cmp_greek as CG

CLAMP = 30        # units: no side is moved further than this by one fit
LC_PART = "aeinorstu"
UC_PART = "HOEDN"


def sides(face, g, la, ra, part):
    """(its right side minus the right analogue's, its left minus the left
    analogue's) in em, or None."""
    def med(vals):
        v = [x for x in vals if x is not None]
        return st.median(v) if v else None
    Rg = med(face.gap(g, b) for b in part); Ra = med(face.gap(ra, b) for b in part)
    Lg = med(face.gap(x, g) for x in part); La = med(face.gap(x, la) for x in part)
    if None in (Rg, Ra, Lg, La): return None
    return Rg - Ra, Lg - La


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("fonts", nargs="+")
    ap.add_argument("--style", default="roman", choices=["roman", "italic", "bold"])
    ap.add_argument("--fit", action="store_true")
    a = ap.parse_args()
    from outlines.build import GREEK_SIDES
    refs = [(n, CS.Face(p, 150, index=i)) for n, p, i in CG.REFS[a.style]]
    albos = [(os.path.basename(os.path.dirname(os.path.abspath(f))) + "/" + os.path.basename(f), CS.Face(f, 150))
             for f in a.fonts]
    print(f"Greek side minus its Latin analogue's side, em (+ = the Greek side is LOOSER), refs: {a.style}")
    print(f"  {'':3}{'':8}" + "".join(f"{n[:14]:>16}" for n, _ in albos) + f"{'ref median':>16}{'ref lo..hi':>16}")
    dev = {n: [] for n, _ in albos}
    fit = {}
    for g, (la, ra) in GREEK_SIDES.items():
        part = UC_PART if g.isupper() else LC_PART
        rr = [s for _, f in refs if (s := sides(f, g, la, ra, part)) is not None]
        if not rr: continue
        for k, lab in ((0, "R"), (1, "L")):
            vals = [r[k] for r in rr]; md = st.median(vals)
            row = f"  {g} {lab} {(ra if k == 0 else la):>4} "
            for i, (n, f) in enumerate(albos):
                s = sides(f, g, la, ra, part)
                if s is None: row += f"{'n/a':>16}"; continue
                row += f"{s[k]:+16.3f}"; dev[n].append(abs(s[k] - md))
                if i == len(albos) - 1:
                    # INSIDE the references' spread a side is left alone; outside it, it is moved to the
                    # nearer edge of that spread (never to the median: four faces disagree by up to 0.07 em
                    # on one side, and a median of four is not a target worth 30 units). A side 0.010 em
                    # too TIGHT wants 10 more units of bearing; k 0 is the RIGHT side (rsb).
                    lo, hi = min(vals), max(vals)
                    tgt = lo if s[k] < lo else (hi if s[k] > hi else s[k])
                    fit.setdefault(g, [0, 0])[1 - k] = max(-CLAMP, min(CLAMP, round((tgt - s[k]) * 1000)))
            row += f"{md:+16.3f}{min(vals):+8.3f}..{max(vals):+.3f}"
            print(row)
    if a.fit:
        from outlines.build import GREEK_SIDE_ADJ
        key = {'italic': 'ald', 'bold': 'bold'}.get(a.style, 'rom')
        old = GREEK_SIDE_ADJ.get(key, {})
        print(f"\n  GREEK_SIDE_ADJ['{key}'] = (lsb, rsb) units: the table this font was built with plus the correction")
        items = []
        for g, (dl, dr) in fit.items():
            o = old.get(g, (0, 0)); items.append(f"'{g}': ({o[0] + dl}, {o[1] + dr})")
        print("  {" + ", ".join(items) + "}")
    print("\n  mean |Albo - ref median|, em:" + "".join(f"  {n}: {st.mean(v):.4f} (n={len(v)})" for n, v in dev.items() if v))


if __name__ == "__main__":
    sys.exit(main())
