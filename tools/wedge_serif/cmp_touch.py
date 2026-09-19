"""Every pair in the font, swept for letters that TOUCH or nearly touch.

Owner 2026-09-16: *"fix LA and any other touching letter combinations"*. The
second half is the point -- LA was found by eye, and anything found by eye has
siblings nobody happened to type.

WHY IT IS NOT cmp_cap_space.py's LOOP. That script renders a pair to measure
one gap, which is fine for the two dozen pairs an owner names and hopeless for
the ~10,000 a full sweep needs. Here each GLYPH is rendered once and reduced to
two profiles -- for every scanline, the rightmost and leftmost ink -- and a
pair's white is then arithmetic on two profiles plus the pair's shaped advance.
One render per glyph instead of two per pair.

The shaped advance is `getlength(a+b) - getlength(b)`, so the GPOS kern table is
in every number. Measuring bearings alone is the bug that let two touching
capitals through the round-177 re-space; see docs/albo-capital-spacing.md.

WHAT COUNTS AS A FAULT. Zero white is a collision and is always a fault. A
floor above zero is a judgment, so it is stated rather than assumed: --floor is
in em and defaults to 0.012, about a third of the thinnest hairline this face
draws, which is the point where two letters stop reading as two letters at 13
pt. Pairs that are SUPPOSED to interlock -- an f and a following ascender, a
quote tucked under a T -- are listed in EXEMPT with their reason.

    PYTHON_GIL=0 python3 cmp_touch.py <built>/Albo-Italic.ttf
    PYTHON_GIL=0 python3 cmp_touch.py <ttf> --floor 0.02 --top 40
"""
import argparse, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont

# Pairs whose ink is MEANT to meet or nearly meet. Each needs its reason.
EXEMPT = {
    ('f', 'b'): "the f's hook is drawn to land on an ascender's top-left wedge (round 96b)",
    # ROUND 225 -- the ROMAN Q's tail, by ruling. Owner 2026-09-18: "leave the
    # Q tail on roman long, it only needs to pair with other capitals and 'u'."
    # Qu and every capital but J clear on the long tail (QQ is kerned); the
    # lowercase, figure and fence pairs below are accepted as touching, and QJ
    # because no English word contains it. In the ITALIC these same pairs are
    # clean (its tail is the shortened one) and are not exempt there.
    ('Q', 'J'): "round 225: the J's hook runs half an em back under the tail; QJ occurs in no English word",
    ('Q', 'g'): "round 225: the roman Q pairs only with capitals and u, by ruling",
    ('Q', 'j'): "round 225: as Qg", ('Q', 'p'): "round 225: as Qg", ('Q', 'q'): "round 225: as Qg", ('Q', 'y'): "round 225: as Qg",
    ('Q', '3'): "round 225: as Qg", ('Q', '4'): "round 225: as Qg", ('Q', '5'): "round 225: as Qg", ('Q', '7'): "round 225: as Qg", ('Q', '9'): "round 225: as Qg",
    ('Q', '('): "round 225: as Qg", ('Q', ')'): "round 225: as Qg",
    ('f', 'h'): "as f+b",
    ('f', 'k'): "as f+b",
    ('f', 'l'): "as f+b",
}


def profiles(ttf, chars, xh_px=300, index=0, xh_src="declared"):
    """For each char: (right[y], left[y]) in px at the pen origin, and the row
    span it occupies. None where the row has no ink.

    `index` picks a face out of a .ttc -- the reference bolds live in
    Baskerville.ttc, Charter.ttc, Palatino.ttc and Hoefler Text.ttc (refsets.py).

    `xh_src` stays **declared** here on purpose, even though `OS/2.sxHeight` is
    absent in Charter and Iowan, zero in New York and wrong by 34% in Poetica
    (refsets.py's header). It only sizes the raster -- every number out of this
    file is per-em -- and this function feeds the TOUCH GATE, whose tightest
    passing pair is `"W` at 0.0124 em against a 0.012 floor. Re-sizing the
    raster moves a number that close to its floor by more than the margin, so a
    tidy-up here could flag or hide a collision. `measured` is for instruments
    that compare against Poetica and the .ttc bolds (cmp_word_white.py)."""
    if xh_src == "measured":
        import refsets
        size = int(round(xh_px / refsets.measure_xh(ttf, index)))
    else:
        f = TTFont(ttf, fontNumber=index) if ttf.lower().endswith(".ttc") else TTFont(ttf)
        upm = f["head"].unitsPerEm
        try: sx = f["OS/2"].sxHeight or upm * 0.5
        except Exception: sx = upm * 0.5
        size = int(round(xh_px * upm / sx))
    fnt = ImageFont.truetype(ttf, size, index=index)
    W = H = size * 3
    ox, oy = size, int(size * 2.1)
    out = {}
    for ch in chars:
        im = Image.new("L", (W, H), 255)
        ImageDraw.Draw(im).text((ox, oy), ch, font=fnt, fill=0, anchor="ls")
        a = np.asarray(im) < 128
        if not a.any():
            continue
        rows = np.nonzero(a.any(1))[0]
        r = np.full(H, np.nan); l = np.full(H, np.nan)
        for y in rows:
            xs = np.nonzero(a[y])[0]
            r[y] = xs.max() - ox; l[y] = xs.min() - ox
        out[ch] = (r, l)
    return out, fnt, size


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ttf")
    ap.add_argument("--floor", type=float, default=0.012, help="em of white below which a pair is a fault")
    ap.add_argument("--top", type=int, default=30)
    ap.add_argument("--xh", type=int, default=300)
    a = ap.parse_args()

    U = [chr(c) for c in range(ord('A'), ord('Z') + 1)]
    L = [chr(c) for c in range(ord('a'), ord('z') + 1)]
    D = list("0123456789")
    P = list(".,;:!?'\"()-")
    chars = U + L + D + P
    prof, fnt, size = profiles(a.ttf, chars, a.xh)
    have = [c for c in chars if c in prof]

    rows = []
    for x in have:
        rx, _ = prof[x]
        lenb = {}
        for y in have:
            _, ly = prof[y]
            # the pair's SHAPED advance -- the kern is in it
            key = y
            if key not in lenb: lenb[key] = fnt.getlength(y)
            off = fnt.getlength(x + y) - lenb[key]
            both = ~np.isnan(rx) & ~np.isnan(ly)
            if not both.any():
                continue
            g = np.min((off + ly[both]) - rx[both]) / size
            rows.append((g, x, y))
    rows.sort()

    bad = [r for r in rows if r[0] < a.floor and (r[1], r[2]) not in EXEMPT]
    exm = [r for r in rows if r[0] < a.floor and (r[1], r[2]) in EXEMPT]
    print(f"\n{len(rows)} pairs swept at a {a.xh} px x-height; floor {a.floor:.3f} em\n")
    print(f"  {'pair':6}{'white, em':>12}")
    for g, x, y in rows[:a.top]:
        tag = ""
        if (x, y) in EXEMPT: tag = f"   <-- exempt: {EXEMPT[(x, y)]}"
        elif g <= 0: tag = "   <-- TOUCHING"
        elif g < a.floor: tag = "   <-- under the floor"
        print(f"  {x+y:6}{g:12.4f}{tag}")
    print()
    touching = [r for r in bad if r[0] <= 0]
    print(f"  {len(touching)} pair(s) TOUCHING, {len(bad)} below the {a.floor:.3f} em floor"
          f"{f', {len(exm)} exempt' if exm else ''}.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
