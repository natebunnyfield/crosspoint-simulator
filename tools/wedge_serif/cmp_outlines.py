#!/usr/bin/env python3
"""Diff two fonts by their glyph OUTLINES, not by their bytes.

A TTF's md5 never compares across builds: fontTools stamps `head.modified`
with the build time, so two byte-identical drawings hash differently and a
"byte-identical" claim made that way is worthless. Round 321 proved the new
default inert by hashing the file and got a false difference; the honest check
is per-glyph, and eight commit bodies on 2026-09-21 cite "0 of 493 glyph
outlines differ" from a snippet re-typed by hand each time. This is it.

    python3 cmp_outlines.py A.ttf B.ttf [--verbose]

Exit 0 when every shared glyph draws identically and neither font adds or
removes one; exit 1 otherwise, listing what moved.
"""
import sys, hashlib, argparse
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen


def outlines(path):
    f = TTFont(path)
    gs = f.getGlyphSet()
    out = {}
    for n in f.getGlyphOrder():
        p = RecordingPen()
        gs[n].draw(p)
        out[n] = hashlib.md5(repr(p.value).encode()).hexdigest()
    return out, f


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("a"); ap.add_argument("b")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--advances", action="store_true",
                    help="also compare advance widths, which spacing changes move")
    args = ap.parse_args()
    A, fa = outlines(args.a)
    B, fb = outlines(args.b)
    only_a = sorted(set(A) - set(B))
    only_b = sorted(set(B) - set(A))
    shared = sorted(set(A) & set(B))
    moved = [n for n in shared if A[n] != B[n]]
    if args.advances:
        ha, hb = fa["hmtx"], fb["hmtx"]
        adv = [n for n in shared if ha[n][0] != hb[n][0]]
    else:
        adv = []
    print(f"{len(moved)} of {len(shared)} shared glyph outlines differ")
    if only_a: print(f"  only in {args.a}: {only_a[:12]}")
    if only_b: print(f"  only in {args.b}: {only_b[:12]}")
    if adv:    print(f"  {len(adv)} advance(s) differ: {adv[:12]}")
    if moved and args.verbose: print("  moved:", moved)
    elif moved: print("  moved:", moved[:20], "..." if len(moved) > 20 else "")
    bad = bool(moved or only_a or only_b or adv)
    print("DIFFERENT" if bad else "IDENTICAL")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
