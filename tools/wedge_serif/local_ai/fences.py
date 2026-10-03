#!/usr/bin/env python3
"""Fences sit symmetrically about every letter -- measured per cut, no hand step.

Owner 2026-09-28: *"improve letter spacing with parentheses and all brackets.
currently not symmetrical"*. The fences ( ) [ ] { } take symmetric bearings on
their own ink (build.fit, PUNCT_FENCES), but the letter INSIDE brings its own
two sides: `(n` sees n's left, `n)` sees n's right, and Albo's letters carry
different left and right bearings, so the white inside an open fence and inside
its close differed -- measured on round 426, Regular lowercase, 22-24 units
looser inside the close on the mean.

This measures, on a built cut WITHOUT this block (ALBO_FENCES=0), for every
fence pair and every letter and figure x, the visible gap inside the open fence
(`(x`) and inside the close (`x)`), each as the average of the closest
approach across the letter's band (instruments/fence_gap.py). NOT the mean
white: it counts a letter's own open white as gap (c reads 399 on its open
right against 218 on its left, E and L worse) -- the spacing method's rule,
a letter's own open white belongs to the letter. Then
it splits the difference: the open pair takes +d/2 and the close pair -d/2
(d = close - open), so `(x` equals `x)` and the letter's own looseness -- its
fitted spacing -- is kept. Kerns under MIN_KERN are dropped. Written into the
table file's "fences" block, keyed by cut; kern.py applies it before clearance.

    $VENV/bin/python fences.py BUILD_DIR     # BUILD_DIR built with ALBO_FENCES=0
    $VENV/bin/python fences.py BUILD_DIR --cuts Italic,BoldItalic --pairs "("
        re-measures ONLY those cuts and fence pairs (named by their opening
        character) and leaves every other entry of the block as it stands --
        for an arm that moves one fence (2026-10-02, the italic parens' height).
        BUILD_DIR then needs only the named cuts.
"""
import json, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); WS = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(WS, "instruments")); sys.path.insert(0, HERE)
from fence_gap import G  # noqa: E402
import b2_fit  # noqa: E402

CUTS = ("Regular", "Italic", "Bold", "BoldItalic")
FENCES = (("(", ")", "parenleft", "parenright"), ("[", "]", "bracketleft", "bracketright"),
          ("{", "}", "braceleft", "braceright"))
LETTERS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
MIN_KERN = 4
XH, CAP = 429, 674


OUTLIER = 80   # |close - open| past this is a deliberate special kern (Q's tail +500, J), not asymmetry
MAX_K = 40


def gapv(g, text, band):
    lo, mean = g.gap(text, *band)
    return lo


def _opt(name):
    if name in sys.argv:
        i = sys.argv.index(name); return sys.argv[i + 1]
    return None


def main():
    build = sys.argv[1]
    data = json.load(open(b2_fit.OUT))
    cuts = _opt("--cuts").split(",") if _opt("--cuts") else CUTS
    pairs = [f for f in FENCES if f[0] in _opt("--pairs")] if _opt("--pairs") else FENCES
    partial = cuts != CUTS or pairs != FENCES
    if partial:
        fen = data.setdefault("fences", {})
    else:
        fen = data["fences"] = {}
    for cut in cuts:
        g = G(os.path.join(build, f"Albo-{cut}.ttf"))
        if partial:
            names = {n for f in pairs for n in f[2:]}
            rows = fen[cut] = {k: v for k, v in fen.get(cut, {}).items() if not (set(k.split(" ")) & names)}
        else:
            rows = fen[cut] = {}
        for o, c, on, cn in pairs:
            for x in LETTERS:
                if not g.has(x):
                    continue
                band = (0, CAP) if (x.isupper()) else (0, XH)
                go, gc = gapv(g, o + x, band), gapv(g, x + c, band)
                if go is None or gc is None:
                    continue
                d = gc - go
                if abs(d) > OUTLIER:
                    continue
                k = max(-MAX_K, min(MAX_K, int(round(d / 2))))
                if abs(k) >= MIN_KERN:
                    xn = g.tt.getBestCmap()[ord(x)]
                    rows[f"{on} {xn}"] = k
                    rows[f"{xn} {cn}"] = -k
        print(f"  {cut}: {len(rows)} fence kerns, max |k| {max((abs(v) for v in rows.values()), default=0)}")
    json.dump(data, open(b2_fit.OUT, "w"), indent=1, ensure_ascii=False, sort_keys=True)
    print("wrote", b2_fit.OUT)


if __name__ == "__main__":
    main()
