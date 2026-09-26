#!/usr/bin/env python3
"""Score ANY spaced font against his answers: the door for tools that cannot run here.

A tool that only runs inside an app or as a service (FontLab 8's auto metrics
and auto kerning, Glyphs + KernOn, iKern, a designer by hand) hands back a
font. Give this the roman and the italic it returned; it measures every
answered pair's white in them (rsb + kern + lsb, HarfBuzz, b2_fit.white_fn --
kerning INCLUDED) and scores that white exactly as score.py scores a tool that
runs here. The tool must have been run on the 2026-09-20 bench fonts
(bench/fonts-2026-09-20/), the zero his answers are on, with outlines untouched.

    $VENV/bin/python score_font.py NAME ROMAN.ttf ITALIC.ttf
    $VENV/bin/python score.py NAME

Controls (all measured 2026-09-26): the 09-20 fonts themselves must score the
do-nothing line exactly; round 397 is B2 fitted on these very answers, so it
scores in-sample, far under any held-out number.
"""
import argparse, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402
import b2_fit  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name")
    ap.add_argument("roman")
    ap.add_argument("italic")
    a = ap.parse_args()
    T = C.Truth()
    white = {}
    for s, path in (("roman", a.roman), ("italic", a.italic)):
        wf = b2_fit.white_fn(path)
        white[s] = {p: float(wf(p[0], p[1])) for p in T.P[s]}
    print(C.save_preds(a.name, "0920", white, {"roman": a.roman, "italic": a.italic}))


if __name__ == "__main__":
    main()
