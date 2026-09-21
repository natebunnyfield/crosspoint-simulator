#!/usr/bin/env python3
"""Fit Albo's bearings and capital kerns from the owner's own spacing bench.

WHY THIS FILE EXISTS.  Rounds 303-308 solved this by hand, in a session, and
committed only the ANSWER -- `ROM_LC_ADJ`, `ALD_LC_ADJ`, the two punctuation
tables and `_BENCH_PAIRS_*` in `outlines/build.py` and `outlines/kern.py`.  The
input was never written back: `bench_values.json` stayed at round 302's 189
judgments while round 308's comment says it fitted 329, so the shipped numbers
could not be re-derived from anything in the repo.  When the bench grew again
on 2026-09-21 (384 judgments) there was no way to refit except to reconstruct
the method from the prose.  This script IS that reconstruction, checked against
round 308's shipped tables before it was trusted (see `--check`).

THE MODEL.  A pair's white is the LEFT glyph's right bearing plus the RIGHT
glyph's left bearing, so each judgment "the white in THIS pair should change by
d" is one equation

    rsb[left] + lsb[right] = d

in two unknowns per glyph, and the whole bench is ONE linear system.  Fitting
the letters and the marks separately is what made the marks worse as the letter
table got richer -- each half absorbed the other's error.

  * LETTERS come from the joint ridge fit at lambda 1 (a letter judged twice
    must not be trusted like one judged eleven times).  A glyph SIDE ships only
    when he judged it at least 4 times AND the fit asks for at least 4 units.
  * MARKS are NOT taken from the joint fit.  The ridge shrinks a mark he judged
    five times toward zero, and a mark's own readings are the strongest
    evidence in the bench -- so each mark is solved DIRECTLY: his mean for that
    mark, minus what the letters now contribute on the other side.  Floor is 3
    readings and no magnitude floor; a mark's whole job is a small number.
  * CAPITALS are never bearings here.  Round 308 ruled the italic's capitals
    not generalisable (mean +2, sd 20, range -41..+57) and the roman's six were
    one reading each, so every capital pair becomes a KERN, carrying his raw
    judgment MINUS what the following letter's new left bearing contributes.

THE g IS EXCLUDED, owner 2026-09-21: *"ignore new 'g' values because it was
with old g."*  Both letters were redrawn in rounds 331-342 and refitted in
round 340 against the current drawing with the 2-D closest approach; every g
row in the bench was judged against the superseded letter.  `--drop g` (the
default) removes all 14 of them, which also withdraws the old-g evidence that
rounds 303-308 folded into the `n` and the marks.

SOURCE OF TRUTH.  The bench itself is the published Artifact page; this repo
keeps a checkout of its database in `bench_values.json` under "literal".
Refresh it with the Artifact tool (read_db, collection `spacing`) before
refitting, or you are fitting last week's answers.
"""
import argparse, json, os, re, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
BENCH = os.path.join(HERE, "bench_values.json")
MARKS = set("'.,:;\"-!?")
LAM = 1.0
LETTER_MIN_N, LETTER_MIN_V = 4, 4
MARK_MIN_N = 3


def judgments(style, drop=("g",)):
    """{pair: delta} for one style, with every pair touching `drop` removed."""
    table = json.load(open(BENCH))["literal"][style]
    return {p: d for p, d in table.items()
            if d and not any(c in drop for c in p)}


def joint_fit(J, lam=LAM):
    """Ridge-solve every glyph's two bearings at once.  Returns (lsb, rsb, err)."""
    glyphs = sorted({c for p in J for c in p})
    iL = {c: 2 * i for i, c in enumerate(glyphs)}
    iR = {c: 2 * i + 1 for i, c in enumerate(glyphs)}
    pairs = sorted(J)
    A = np.zeros((len(pairs), 2 * len(glyphs)))
    b = np.zeros(len(pairs))
    for i, p in enumerate(pairs):
        A[i, iR[p[0]]] = 1.0
        A[i, iL[p[1]]] = 1.0
        b[i] = J[p]
    x = np.linalg.solve(A.T @ A + lam * np.eye(A.shape[1]), A.T @ b)
    lsb = {c: x[iL[c]] for c in glyphs}
    rsb = {c: x[iR[c]] for c in glyphs}
    return lsb, rsb, float(np.mean(np.abs(A @ x - b)))


def fit_style(style, drop=("g",)):
    J = judgments(style, drop)
    lsb, rsb, ridge_err = joint_fit(J)
    pairs = sorted(J)
    nL = {c: sum(1 for p in pairs if p[1] == c) for c in lsb}
    nR = {c: sum(1 for p in pairs if p[0] == c) for c in rsb}

    letters = {}
    for c in sorted(lsb):
        if not (c.isalpha() and c.islower()):
            continue                      # capitals are kerns, marks are direct
        L = int(round(lsb[c])) if nL[c] >= LETTER_MIN_N and abs(lsb[c]) >= LETTER_MIN_V else 0
        R = int(round(rsb[c])) if nR[c] >= LETTER_MIN_N and abs(rsb[c]) >= LETTER_MIN_V else 0
        if L or R:
            letters[c] = (L, R)

    # The marks, solved directly against what the letters now contribute.
    marks = {}
    for m in sorted(MARKS):
        left = [p for p in pairs if p[1] == m]        # mark on the right -> its LSB
        right = [p for p in pairs if p[0] == m]       # mark on the left  -> its RSB
        L = R = 0
        if len(left) >= MARK_MIN_N:
            L = int(round(np.mean([J[p] - rsb.get(p[0], 0.0) for p in left])))
        if len(right) >= MARK_MIN_N:
            R = int(round(np.mean([J[p] - lsb.get(p[1], 0.0) for p in right])))
        if L or R:
            marks[m] = (L, R)

    # Every capital pair becomes a kern: his raw number, minus what the
    # following letter's new left bearing already gives back.
    kerns = {}
    for p in pairs:
        if not p[0].isupper():
            continue
        give = letters.get(p[1], (0, 0))[0]
        d = int(round(J[p] - give))
        if d:
            kerns[p] = d

    # How well the SHIPPED integers do against his own numbers, which is the
    # only honest score -- the ridge residual is the continuous fit's.
    def predict(p):
        l, r = p
        a = letters.get(l, (0, 0))[1] or marks.get(l, (0, 0))[1]
        b = letters.get(r, (0, 0))[0] or marks.get(r, (0, 0))[0]
        return a + b + kerns.get(p, 0)
    shipped_err = float(np.mean([abs(predict(p) - J[p]) for p in pairs]))
    nothing_err = float(np.mean([abs(J[p]) for p in pairs]))
    return dict(n=len(pairs), letters=letters, marks=marks, kerns=kerns,
                ridge_err=ridge_err, shipped_err=shipped_err,
                nothing_err=nothing_err, nL=nL, nR=nR, lsb=lsb, rsb=rsb)


def _fmt_pairs(d):
    return "{" + ", ".join(f"{k!r}: ({v[0]:+d}, {v[1]:+d})" for k, v in d.items()) + "}"


def live_tables():
    """The tables `outlines/build.py` actually ships, read as text."""
    src = open(os.path.join(HERE, "outlines", "build.py")).read()
    out = {}
    for name in ("ROM_LC_ADJ", "ALD_LC_ADJ", "ROM_PUNCT_FIT", "ALD_PUNCT_FIT"):
        m = re.search(rf"^{name} = (\{{.*?\}})", src, re.S | re.M)
        out[name] = eval(m.group(1)) if m else None
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--drop", default="g",
                    help="glyphs whose pairs are excluded (default g, owner 2026-09-21)")
    ap.add_argument("--check", action="store_true",
                    help="compare the fit with what build.py ships; non-zero on a difference")
    args = ap.parse_args()
    drop = tuple(args.drop) if args.drop else ()

    res = {s: fit_style(s, drop) for s in ("roman", "italic")}
    for style in ("roman", "italic"):
        r = res[style]
        print(f"--- {style}: {r['n']} judgments"
              f"{' (dropped: ' + ' '.join(drop) + ')' if drop else ''}")
        print(f"    mean |error| vs his numbers: do nothing {r['nothing_err']:.2f}"
              f"  ->  shipped integers {r['shipped_err']:.2f}"
              f"   (continuous ridge {r['ridge_err']:.2f})")
        key = "ROM" if style == "roman" else "ALD"
        print(f"    {key}_LC_ADJ = " + _fmt_pairs(r["letters"]))
        print(f"    {key}_PUNCT_FIT = " + _fmt_pairs(r["marks"]))
        pairs = ", ".join(f"(({p[0]!r},{p[1]!r}), {d})" for p, d in sorted(r["kerns"].items()))
        print(f"    _BENCH_PAIRS_{'ROM' if style=='roman' else 'ITA'} = ({pairs})")
        print()

    if not args.check:
        return 0
    live = live_tables()
    bad = 0
    for style, lc, pf in (("roman", "ROM_LC_ADJ", "ROM_PUNCT_FIT"),
                          ("italic", "ALD_LC_ADJ", "ALD_PUNCT_FIT")):
        for name, got in ((lc, res[style]["letters"]), (pf, res[style]["marks"])):
            # The ligature riders track a letter rather than coming from the
            # fit, and the g is held at round 340's value by ruling.
            skip = set("\ufb00\ufb01\ufb02\ufb03\ufb04") | set(drop)
            want = {k: v for k, v in (live[name] or {}).items() if k not in skip}
            if want != got:
                bad = 1
                miss = {k: (want.get(k), got.get(k)) for k in set(want) | set(got)
                        if want.get(k) != got.get(k)}
                print(f"DIFFERS {name}: {miss}")
    print("build.py matches the bench" if not bad else "build.py does NOT match the bench")
    return bad


if __name__ == "__main__":
    sys.exit(main())
