#!/usr/bin/env python3
"""GATE: does FreeType's autohinter shut the roman e's mouth at small sizes?

Albo ships with no hinting bytecode, so every FreeType consumer that asks for
default loading (the firmware's converter, the Kept Legibility Index, most of
the desktop) gets the AUTOHINTER. On 2026-09-26 one exact e outline -- the
round-395 bar floor 0.45, while 0.445 and 0.455 were clean -- made the
autohinter pull the e's bar and upper bowl DOWN a quarter to a third of a
pixel at 8-12 ppem, filling the only clear row of the mouth; Apple Vision
then read e as o 131 times in the index where every neighbor scored 0-6.
The trigger is a knife edge in outline coordinates, so no dial can be
trusted to stay clear of it and a paragraph cannot guard it: this gate can.

For every ppem from 8 to 12 in quarter pixels it renders the e as the
index does (FT_LOAD_RENDER, 8-bit) and measures e_mechanism.mouth_block:
the lightest pixel row, inside the drawn mouth band, measured as the darkest
pixel a path must cross from the glyph's center out past its right-most ink.
Clean builds of the roman read 0.00-0.12 there; the failing build 0.21-0.24.

    python3 e_hint_gate.py FONT.ttf [FONT.ttf ...] [--limit 0.15]

Exit 1 when any size exceeds the limit. Prints the worst size per font.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from e_mechanism import design, mouth_block  # noqa: E402

SIZES = [8.0 + 0.25 * k for k in range(17)]   # 8.0 .. 12.0 (at 7.5 every build, 09-20 included, reads ~0.2: the mouth band is under a pixel there)


def check(path, limit):
    geo, _ = design(path)
    vals = [(s, mouth_block(path, s, geo)) for s in SIZES]
    bad = [(s, v) for s, v in vals if v > limit]
    worst = max(vals, key=lambda sv: sv[1])
    return bad, worst, vals


def main():
    args = sys.argv[1:]
    limit = 0.15
    if "--limit" in args:
        i = args.index("--limit"); limit = float(args[i + 1]); del args[i:i + 2]
    fail = False
    for p in args:
        bad, worst, _ = check(p, limit)
        tag = "FAIL" if bad else "ok"
        print(f"{tag:4s} worst mouth_block {worst[1]:.3f} at {worst[0]} ppem"
              + (f"; over {limit} at {[s for s, _ in bad]}" if bad else "") + f"  {p}")
        fail |= bool(bad)
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
