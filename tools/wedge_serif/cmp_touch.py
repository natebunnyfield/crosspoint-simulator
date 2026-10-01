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
    # ROUND 348 -- KERNED, AND THIS GATE CANNOT SEE IT. Owner 2026-09-21,
    # "kern Q". These thirteen are no longer touching: measured as a 2-D
    # distance between rasterised outlines, every one now clears 0.012 em
    # (Q4 0.0146, Qg 0.0195, Q3 0.0135 ...), where ten of them INTERSECTED
    # before. The row-wise measure below cannot report that, because it
    # compares the second glyph's left edge with the FIRST GLYPH'S RIGHTMOST
    # INK ON THE SAME ROW, and the Q's tail reaches x=1312 on a 777-unit
    # advance -- so the number stays at -0.25 to -0.49 em whatever the kern
    # does, short of pushing the pair clean past the tail's end. They stay
    # exempt for that reason and NOT round 225's: it is the instrument that
    # cannot follow a thin stroke past a later glyph, not the drawing that is
    # wrong. Kern values and the sweep that sized them: outlines/kern.py.
    ('Q', 'J'): "round 348: kerned +500; this row-wise gate cannot see a thin tail",
    ('Q', 'g'): "round 348: kerned +480; this row-wise gate cannot see a thin tail",
    ('Q', 'j'): "round 348: kerned +500, as Qg", ('Q', 'p'): "round 348: kerned +460, as Qg",
    ('Q', 'q'): "round 348: kerned +140, as Qg", ('Q', 'y'): "round 348: kerned +360, as Qg",
    ('Q', '3'): "round 348: kerned +520, as Qg", ('Q', '4'): "round 348: kerned -60, as Qg",
    ('Q', '5'): "round 348: kerned +500, as Qg",
    ('Q', '7'): "round 348: NOT kerned -- it already clears by 0.0125 em on ink",
    ('Q', '9'): "round 348: kerned +60, as Qg",
    ('Q', '('): "round 348: kerned +440, as Qg", ('Q', ')'): "round 348: kerned +440, as Qg",
    # ROUND 360 -- the two that only ever surfaced at the BOLD weight, and
    # neither is touching: measured 2-D, Q, clears by 0.0613 em on the Bold
    # and 0.1360 on the Regular, Q; by 0.0632 and 0.1259. Same row-wise blind
    # spot as the thirteen above -- the tail reaches past the mark on rows the
    # mark also occupies, without ever meeting it. They take no kern.
    ('Q', ','): "round 360: not touching -- clears 0.061 em on the Bold, measured 2-D",
    ('Q', ';'): "round 360: not touching -- clears 0.063 em on the Bold, measured 2-D",
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


def ligating_pairs(ttf, index=0):
    """The two-glyph sequences the font's own `liga` feature replaces.

    WHY THE GATE NEEDS THIS. `ff` and `fi` were reported TOUCHING on the Bold
    at -0.034 and -0.023 em, and they are neither touching nor a sequence the
    font ever draws: both ligate. Measured on the Bold, `ff` shapes to 618
    units against 772 for two separate f's. The row-wise measure below places
    the second glyph at `getlength(xy) - getlength(y)` -- the LIGATURE's
    advance applied to two loose glyphs -- so it overlaps them by construction
    and then reports the overlap.

    Read from GSUB rather than kept as a hand list, because the roman carries
    ff fi fl ffi ffl and the italic carries none (owner 2026-09-21), so a
    hand list would be wrong for one of the two styles the moment it was
    written.
    """
    from fontTools.ttLib import TTFont as _TT
    f = _TT(ttf, fontNumber=index) if ttf.lower().endswith(".ttc") else _TT(ttf)
    if "GSUB" not in f:
        return set()
    rev = {}
    for ch, g in f.getBestCmap().items():
        rev.setdefault(g, chr(ch))
    out = set()
    gsub = f["GSUB"].table
    liga_idx = set()
    for fr in gsub.FeatureList.FeatureRecord:
        if fr.FeatureTag == "liga":
            liga_idx.update(fr.Feature.LookupListIndex)
    for i in liga_idx:
        lk = gsub.LookupList.Lookup[i]
        for st in lk.SubTable:
            for first, ligs in getattr(st, "ligatures", {}).items():
                for lg in ligs:
                    if len(lg.Component) != 1:      # only 2-glyph sequences
                        continue
                    a, b = rev.get(first), rev.get(lg.Component[0])
                    if a and b:
                        out.add((a, b))
    return out


def composite_chars(ttf):
    """{accented character: its base character} over the font's own cmap: an
    encoded character whose NFD starts with a DIFFERENT letter the font also
    encodes. The same rule kern.py's `_composite_family` uses (round 449)."""
    import unicodedata
    cmap = TTFont(ttf).getBestCmap(); out = {}
    for cp in sorted(cmap):
        ch = chr(cp); b = unicodedata.normalize("NFD", ch)[0]
        if b != ch and b.isalpha() and ord(b) in cmap and cmap[ord(b)] != cmap[cp]:
            out[ch] = b
    return out


def composite_sweep(a):
    """ROUND 449 -- THE ACCENTED PAIRS, which the default sweep never saw.

    Owner 2026-09-30, "fix all accented": every accented letter now takes its
    base letter's kerning, and an accent kerned as tight as its base can meet
    its neighbor (Tä, Yë, Ïl). This sweeps every pair with an accented letter on
    either side, measured exactly as the default sweep measures, and reports a
    pair only where the ACCENT is the fault: the pair is under the floor and
    either its base pair clears it, or its base pair is itself under the floor
    (an exempt pair, a script the default sweep does not cover) and the accent
    makes it worse by more than 0.002 em. A base pair the font LIGATES does not
    excuse its accented form: fí does not ligate, so it is measured as drawn.
    Every fault is printed, not the top N, because clearance.py reads the
    printed lines and writes one kern per line."""
    import unicodedata
    comp = composite_chars(a.ttf)
    # A mark BELOW the baseline meets the roman Q's long tail, which by ruling
    # pairs only with capitals and u (round 225: "leave the Q tail on roman
    # long"; the exempt Qg Qj Qp above are the same contact). Skipped, not
    # fixed: Qç Qļ Qą occur in no language.
    BELOW = set("\u0323\u0324\u0325\u0326\u0327\u0328\u032d\u032e\u0330\u0331")
    def q_tail(x, y):
        return x == "Q" and any(m in BELOW for m in unicodedata.normalize("NFD", y))
    # A pair across two scripts (Greek eta then an Esperanto j-circumflex) does
    # not occur in text either: letters of different scripts are not paired.
    def script(ch):
        o = ord(ch)
        if not ch.isalpha(): return None
        if 0x370 <= o <= 0x3FF or 0x1F00 <= o <= 0x1FFF: return "grek"
        if 0x400 <= o <= 0x52F: return "cyrl"
        return "latn"
    U = [chr(c) for c in range(ord('A'), ord('Z') + 1)]
    L = [chr(c) for c in range(ord('a'), ord('z') + 1)]
    # the curly quotes, guillemets, ellipsis and dashes too: an accented letter
    # is quoted as often as a plain one, and the first review of this sweep found
    # a Bold Italic o-dieresis touching its closing curly quote that the ASCII
    # quote beside it in the list did not show
    base_set = U + L + list("0123456789") + list(".,;:!?'\"()-") + list("\u2018\u2019\u201c\u201d\u00ab\u00bb\u2026\u2013\u2014")
    # and the neighbours the second review found untried: * and the letters with
    # no decomposition (round 451: italic i-circumflex before * touched unseen)
    base_set += list("*\u0111\u00f8\u0142\u00df\u00e6\u0153\u00fe\u00f0\u00bf\u00a1\u0110\u00d8\u0141\u00c6\u0152")
    # and the third review's: the rest of the encoded Latin letters with no decomposition
    # -- Turkish dotless i (which meets c-cedilla, s-cedilla and g-breve in real words), the
    # dotless j, Dutch ij, Maltese h-bar, Sami t-bar and eng, the long s. Round 452 had left
    # 15 contacts under the floor among them unseen (italic c-caron before h-bar 1.5 units)
    base_set += list("\u0131\u0237\u0133\u0132\u0127\u0126\u0167\u0166\u014b\u014a\u017f")
    base_set += [b for b in sorted(set(comp.values())) if b not in base_set]
    chars = base_set + sorted(comp)
    prof, fnt, size = profiles(a.ttf, chars, a.xh)
    have = [c for c in chars if c in prof]
    liga = ligating_pairs(a.ttf)
    lenb = {}
    # THE 2-D CLOSEST APPROACH as well as the row-wise white. A mark meets a
    # neighbour diagonally -- the dieresis by the shoulder of a W or a Y -- and
    # the row-wise measure, which compares only ink on the SAME row, cannot see
    # it (the review found Bold Italic Wa-dieresis at 7 units apart while its
    # row-wise white read exactly the floor). kern.py's Q and q kerns were sized
    # on this 2-D distance for the same reason (rounds 348, 357). Computed only
    # where the row-wise white is already under 0.05 em, from each glyph's edge
    # pixels, rendered exactly as the profiles are.
    W = H = size * 3; ox, oy = size, int(size * 2.1); edges = {}
    def edge(ch):
        if ch not in edges:
            im = Image.new("L", (W, H), 255)
            ImageDraw.Draw(im).text((ox, oy), ch, font=fnt, fill=0, anchor="ls")
            m = np.asarray(im) < 128
            e = m & ~(np.roll(m, 1, 0) & np.roll(m, -1, 0) & np.roll(m, 1, 1) & np.roll(m, -1, 1))
            ys, xs = np.nonzero(e); edges[ch] = (ys.astype(np.float32), (xs - ox).astype(np.float32))
        return edges[ch]

    masks = {}
    def mask(ch):
        if ch not in masks:
            im = Image.new("L", (W, H), 255)
            ImageDraw.Draw(im).text((ox, oy), ch, font=fnt, fill=0, anchor="ls")
            masks[ch] = np.asarray(im) < 128
        return masks[ch]
    def overlap(x, y, off):
        a, b = mask(x), mask(y); k = int(round(off))
        if k >= W: return False
        if k >= 0: return bool((a[:, k:] & b[:, :W - k]).any())
        return bool((a[:, :W + k] & b[:, -k:]).any())

    def gap2d(x, y, off):
        y1, x1 = edge(x); y2, x2 = edge(y); x2 = x2 + off
        if not len(x1) or not len(x2): return None
        if overlap(x, y, off): return 0.0
        mg = 0.05 * size
        k1 = x1 > x2.min() - mg; k2 = x2 < x1.max() + mg
        a1 = np.stack([y1[k1], x1[k1]], 1); a2 = np.stack([y2[k2], x2[k2]], 1)
        if not len(a1) or not len(a2): return None
        best = np.inf
        for i in range(0, len(a1), 512):
            d = ((a1[i:i + 512, None, :] - a2[None, :, :]) ** 2).sum(-1)
            best = min(best, float(d.min()))
        return float(np.sqrt(best)) / size

    def gap(x, y):
        rx, _ = prof[x]; _, ly = prof[y]
        if y not in lenb: lenb[y] = fnt.getlength(y)
        off = fnt.getlength(x + y) - lenb[y]
        both = ~np.isnan(rx) & ~np.isnan(ly)
        if not both.any(): return None
        g = float(np.min((off + ly[both]) - rx[both]) / size)
        if g < 0.05:
            # round 451 (the review): a NEGATIVE row-wise white is not always a
            # collision -- the italic j's tail passes UNDER an ogonek, so the two
            # share rows with the j's ink left of the ogonek's, and the row-wise
            # measure read -0.038 em where the true closest approach was +0.026.
            # Clearance then pushed the j 70 units through real contact. The 2-D
            # approach decides whenever it can be taken; overlapping ink is 0.
            d = gap2d(x, y, off)
            if d is not None: g = d if g <= 0 else min(g, d)
        return g

    base_gap = {}
    rows = []; n = 0
    for x in have:
        for y in have:
            if x not in comp and y not in comp:
                continue
            sx, sy = script(x), script(y)
            if (sx and sy and sx != sy) or q_tail(x, y):
                continue
            g = gap(x, y)
            if g is None:
                continue
            n += 1
            if g >= a.floor:
                continue
            bx, by = comp.get(x, x), comp.get(y, y)
            if (bx, by) in liga:
                rows.append((g, x, y)); continue
            if (bx, by) not in base_gap:
                base_gap[(bx, by)] = gap(bx, by) if (bx in prof and by in prof) else None
            gb = base_gap[(bx, by)]
            if gb is None or ((bx, by) not in EXEMPT and gb >= a.floor) or g < gb - 0.002:
                rows.append((g, x, y))
    rows.sort()
    print(f"\n{n} accented pairs swept at a {a.xh} px x-height; floor {a.floor:.3f} em\n")
    print(f"  {'pair':6}{'white, em':>12}")
    # The pair's own kern, in em, from the same shaper: clearance.py opens a
    # pair no further than its UNKERNED position, so an accent that meets its
    # neighbor with no kern at all (the bold's dieresis wider than its i) is a
    # drawing fault, reported here as "unkerned" and left to the drawing.
    unk = 0
    for g, x, y in rows:
        k = (fnt.getlength(x + y) - fnt.getlength(x) - fnt.getlength(y)) / size
        u = "  unkerned" if g - k < a.floor else ""
        unk += bool(u)
        print(f"  {x+y:6}{g:12.4f}   <-- {'TOUCHING' if g <= 0 else 'under the floor'}   kern_em {k:.4f}{u}")
    print()
    touching = [r for r in rows if r[0] <= 0]
    print(f"  {len(touching)} pair(s) TOUCHING, {len(rows)} below the {a.floor:.3f} em floor"
          f" ({unk} of them under it even unkerned).")
    return 1 if rows else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ttf")
    ap.add_argument("--floor", type=float, default=0.012, help="em of white below which a pair is a fault")
    ap.add_argument("--top", type=int, default=30)
    ap.add_argument("--xh", type=int, default=300)
    ap.add_argument("--composites", action="store_true",
                    help="sweep the pairs with an accented letter instead (round 449); reports only where the accent is the fault")
    a = ap.parse_args()
    if a.composites:
        return composite_sweep(a)

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

    # A PAIR THE FONT LIGATES IS NOT A PAIR. Dropped before the verdict rather
    # than exempted, because it is read from the font's own GSUB and is
    # therefore right for each style without anyone maintaining a list.
    liga = ligating_pairs(a.ttf)
    rows = [r for r in rows if (r[1], r[2]) not in liga]
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
