#!/usr/bin/env python3
"""GATE: is the roman e's mouth open AS THE READER RENDERS IT?

History. Albo ships with no hinting bytecode, so FreeType's default load hands
it to the AUTOHINTER. On 2026-09-26 one exact e outline -- round 395's bar
floor 0.45, while 0.445 and 0.455 were clean -- made the autohinter pull the
bar DOWN a quarter to a third of a pixel at 8-12 ppem and fill the only clear
row of the mouth; Apple Vision read e as o 131 times in the Kept Legibility
Index. Round 400 raised the bar 2 units and wired this gate on the autohinted
render (docs/albo-e-legibility-2026-09-26.md).

Round 401 (owner ruling 2026-09-26, "no hinting wins") changed the READER:
the firmware's converter now loads Albo with FT_LOAD_NO_HINTING
(sd-fonts.yaml `hinting: none`, docs/albo-hinting-options-2026-09-26.md).
There is no hinter left to create a knife edge, so this gate now renders the
e exactly as the converter does -- NO hinting, 8-bit coverage cut to the
converter's 2 bits -- and checks two things:

  1. READER SIZES (hard): every Albo slot the reader ships, 8..18 pt at
     150 dpi (16.7-37.5 ppem) and the 2x tier the phone draws (16..36 pt,
     33.3-75 ppem). mouth_block on the 8-bit coverage AND on the 2-bit levels
     must be <= --limit (0.15). Round 400 reads 0.00 at all twelve.
  2. EARLY WARNING (hard): 9..12 ppem in quarter pixels, unhinted, 8-bit,
     <= --small-limit (0.20). Round 400 reads 0.15 at worst (at 9.0) and
     Vision reads 0 e>o there (size sweep, 9-13 px). 8-8.75 ppem is REPORTED
     but not gated: unhinted, the mouth band is ~1.1 px tall there and lands
     grey across two rows in every build (r399 and r400 both read 0.18-0.26,
     Vision 13-14 e>o at 8 px for both) and in the reference serifs too
     (Georgia/Times/Charter/Palatino/Hoefler unhinted read 0.20-0.38 worst
     over 8-12 ppem). It is a property of an unhinted 8 px e, not of this
     drawing, and 8 px is half the reader's smallest size.

mouth_block: inside the drawn mouth band (terminal top .. bar underside,
measured unhinted at 1000 ppem), the lightest pixel row, taken as the darkest
pixel a path must cross from the glyph's center out past its right-most ink.
0 = one row runs clear, 1 = sealed.

    python3 e_hint_gate.py FONT.ttf [FONT.ttf ...] [--limit 0.15] [--small-limit 0.20]
    python3 e_hint_gate.py --autohint FONT.ttf   # the round-400 check (8-12 ppem,
                                                 # autohinted: the INDEX's renderer)

Exit 1 when any gated size exceeds its limit.
"""
import sys
import numpy as np
import freetype

# Self-contained (numpy + freetype only) so gates.sh can run it on the system
# python3, which has no scipy. The band and the block are the same measures as
# e_mechanism.py's design()/mouth_block().

READER_PT = [8, 10, 12, 14, 16, 18]   # sd-fonts.yaml Albo `sizes:`
TIERS = [1, 2]                        # 1x (X3) and the 2x tier (phone)
SMALL = [9.0 + 0.25 * k for k in range(13)]   # 9.0 .. 12.0, gated
TINY = [8.0, 8.25, 8.5, 8.75]                 # reported only
AUTO = [8.0 + 0.25 * k for k in range(17)]    # --autohint: the round-400 sweep


def _render(path, size64, dpi, flags, pad=3):
    """The converter's call: set_char_size(size64, size64, dpi, dpi), then
    FT_LOAD_RENDER | flags. Returns (8-bit coverage 0..1, 2-bit level/3, top)."""
    f = freetype.Face(path)
    f.set_char_size(size64, size64, dpi, dpi)
    f.load_char("e", freetype.FT_LOAD_RENDER | flags)
    b = f.glyph.bitmap
    a8 = np.frombuffer(bytes(b.buffer), dtype=np.uint8).reshape(b.rows, b.pitch)[:, :b.width]
    n = a8 >> 4   # fontconvert_sdcard.py: top nibble, then >=12/8/4 -> 3/2/1
    lv = np.where(n >= 12, 3, np.where(n >= 8, 2, np.where(n >= 4, 1, 0)))
    return np.pad(a8 / 255.0, pad), np.pad(lv / 3.0, pad), f.glyph.bitmap_top + pad


def band(path):
    """The drawn mouth band in font units (upem 1000 assumed, as Albo is):
    (terminal top, bar underside). Unhinted at 1000 ppem; the bar underside is
    the bottom of the SECOND ink run down the glyph's middle column (bowl top,
    bar, bowl bottom), the terminal top the highest ink below that at the
    right-most ink column under the bar."""
    cov, _, top = _render(path, 1000 * 64, 72, freetype.FT_LOAD_NO_HINTING)
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


def _block(cov, top, ppem, terminal_top, bar_underside):
    s = ppem / 1000.0
    lo, hi = terminal_top * s, bar_underside * s
    inkcols = np.nonzero((cov > 0.05).any(0))[0]
    c0 = (inkcols.min() + inkcols.max()) // 2; c1 = inkcols.max()
    best = 1.0
    for r in range(cov.shape[0]):
        if lo <= top - r - 0.5 <= hi:
            best = min(best, float(cov[r, c0:c1 + 1].max()))
    return round(best, 3)


def mouth(path, size64, dpi, flags, bnd):
    """(8-bit block, 2-bit block) at this size."""
    a8, lv, top = _render(path, size64, dpi, flags)
    ppem = size64 / 64.0 * dpi / 72.0
    return _block(a8, top, ppem, *bnd), _block(lv, top, ppem, *bnd)


def check(path, limit, small_limit):
    bnd = band(path)
    nh = freetype.FT_LOAD_NO_HINTING
    lines, bad = [], []
    reader = []
    for t in TIERS:
        for pt in READER_PT:
            b8, b2 = mouth(path, (pt * t) << 6, 150, nh, bnd)
            key = f"{pt}pt" + ("" if t == 1 else f"@{t}x")
            reader.append((key, b8, b2))
            if max(b8, b2) > limit:
                bad.append(f"reader {key} {max(b8, b2):.3f}")
    small = [(p, mouth(path, int(p * 64), 72, nh, bnd)[0]) for p in SMALL]
    bad += [f"{p} ppem {v:.3f}" for p, v in small if v > small_limit]
    tiny = [(p, mouth(path, int(p * 64), 72, nh, bnd)[0]) for p in TINY]
    wr = max(reader, key=lambda r: max(r[1], r[2]))
    ws = max(small, key=lambda r: r[1])
    lines.append(f"reader sizes (1x+2x, 8-bit/2-bit) worst {max(wr[1], wr[2]):.3f} at {wr[0]}")
    lines.append(f"9-12 ppem worst {ws[1]:.3f} at {ws[0]}")
    lines.append("8-8.75 ppem (reported, not gated) " + " ".join(f"{p}:{v:.2f}" for p, v in tiny))
    return bad, lines


def check_autohint(path, limit):
    bnd = band(path)
    vals = [(p, mouth(path, int(p * 64), 72, 0, bnd)[0]) for p in AUTO]
    bad = [f"{p} ppem {v:.3f}" for p, v in vals if v > limit]
    w = max(vals, key=lambda sv: sv[1])
    return bad, [f"AUTOHINTED 8-12 ppem worst {w[1]:.3f} at {w[0]}"]


def main():
    args = sys.argv[1:]
    limit, small_limit, auto = 0.15, 0.20, False
    if "--limit" in args:
        i = args.index("--limit"); limit = float(args[i + 1]); del args[i:i + 2]
    if "--small-limit" in args:
        i = args.index("--small-limit"); small_limit = float(args[i + 1]); del args[i:i + 2]
    if "--autohint" in args:
        args.remove("--autohint"); auto = True
    fail = False
    for p in args:
        bad, lines = check_autohint(p, limit) if auto else check(p, limit, small_limit)
        tag = "FAIL" if bad else "ok"
        print(f"{tag:4s} {'; '.join(lines)}" + (f"; OVER: {', '.join(bad)}" if bad else "") + f"  {p}")
        fail |= bool(bad)
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
