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
index does (FT_LOAD_RENDER, 8-bit) and measures mouth_block (as e_mechanism.py):
the lightest pixel row, inside the drawn mouth band, measured as the darkest
pixel a path must cross from the glyph's center out past its right-most ink.
Clean builds of the roman read 0.00-0.12 there; the failing build 0.21-0.24.

    python3 e_hint_gate.py FONT.ttf [FONT.ttf ...] [--limit 0.15]

Exit 1 when any size exceeds the limit. Prints the worst size per font.
"""
import sys
import numpy as np
import freetype

# Self-contained (numpy + freetype only) so gates.sh can run it on the system
# python3, which has no scipy. The band and the block are the same measures as
# e_mechanism.py's design()/mouth_block(); on round 400 this version gave the
# same worst value and verdict as that one on all 16 builds of the e->o trace.


def _render(path, ppem, hinting=True, pad=3):
    f = freetype.Face(path)
    f.set_char_size(int(ppem * 64))
    f.load_char("e", freetype.FT_LOAD_RENDER | (0 if hinting else freetype.FT_LOAD_NO_HINTING))
    b = f.glyph.bitmap
    a = np.frombuffer(bytes(b.buffer), dtype=np.uint8).reshape(b.rows, b.pitch)[:, :b.width] / 255.0
    return np.pad(a, pad), f.glyph.bitmap_top + pad


def band(path):
    """The drawn mouth band in font units (upem 1000 assumed, as Albo is):
    (terminal top, bar underside). Unhinted at 1000 ppem; the bar underside is
    the bottom of the SECOND ink run down the glyph's middle column (bowl top,
    bar, bowl bottom), the terminal top the highest ink below that at the
    right-most ink column under the bar."""
    cov, top = _render(path, 1000, hinting=False)
    ink = cov >= 0.5
    cols = np.nonzero(ink.any(0))[0]
    mid = ink[:, (cols.min() + cols.max()) // 2]
    runs, r, H = [], 0, len(mid)
    while r < H:
        if mid[r]:
            s0 = r
            while r < H and mid[r]:
                r += 1
            runs.append((s0, r))
        r += 1
    if len(runs) < 3:
        raise SystemExit(f"{path}: the e's middle column is not bowl/bar/bowl ({len(runs)} ink runs)")
    under_row = runs[1][1]
    low = ink.copy(); low[:under_row + 1] = False
    tip_col = np.nonzero(low.any(0))[0].max() - 2
    tip_row = np.nonzero(low[:, tip_col])[0].min()
    return top - tip_row, top - under_row


def mouth_block(path, ppem, terminal_top, bar_underside):
    cov, top = _render(path, ppem)
    s = ppem / 1000.0
    lo, hi = terminal_top * s, bar_underside * s
    inkcols = np.nonzero((cov > 0.05).any(0))[0]
    c0 = (inkcols.min() + inkcols.max()) // 2; c1 = inkcols.max()
    best = 1.0
    for r in range(cov.shape[0]):
        if lo <= top - r - 0.5 <= hi:
            best = min(best, float(cov[r, c0:c1 + 1].max()))
    return round(best, 3)

SIZES = [8.0 + 0.25 * k for k in range(17)]   # 8.0 .. 12.0 (at 7.5 every build, 09-20 included, reads ~0.2: the mouth band is under a pixel there)


def check(path, limit):
    tt, bu = band(path)
    vals = [(s, mouth_block(path, s, tt, bu)) for s in SIZES]
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
