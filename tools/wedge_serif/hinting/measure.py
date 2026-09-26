#!/usr/bin/env python3
"""Hinting arms, measured on the bitmaps the converter would ship (2026-09-26).

For every arm (raster.ARMS), style (Regular, Italic) and size (9 px, the six
reader sizes at 1x and at the 2x tier) this rasterizes a-z exactly as
fontconvert_sdcard.py does (validate.py proves it) and reports:

  e gate     the e hint gate's mouth_block, on the 2-bit levels the device
             gets (and on the 8-bit coverage, which is what the gate and the
             Kept Legibility Index see). 0 = one row runs clear out of the
             mouth, 1 = sealed. The shipped gate fails > 0.15.
  stems      the lowercase vertical stem at mid x-height in b h i j k l m n
             p r u (left run) and d q (right run): ink width (sum of the
             2-bit levels / 3, px) per letter. `spread` = max - min across
             the letters, `shapes` = how many distinct level patterns the
             same stem is drawn with. One stem drawn one way = 0 spread,
             1 shape.
  align      tops of the letters whose OUTLINE top sits on the x-height
             (+-3 units), bottoms of those sitting on the baseline, and the
             same for the round (overshooting) ones: the rendered edge in px
             (sub-pixel, from each row's peak level), its spread across the
             group, and `crisp` = mean peak level of the outermost row
             (1 = the edge lands on a pixel boundary, 0.33 = a pale fringe).
  colour     rendered ink of a-z (sum of levels / 3) against the unhinted
             8-bit area of the same glyphs at the same ppem: 1.00 = the
             outline's own weight. `letter_sd` = the spread of that ratio
             across letters (does hinting darken some letters and not
             others).

    python3 measure.py --fonts DIR --out results.json
"""
import argparse, json, os, sys
import numpy as np
import freetype
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import raster  # noqa: E402

LC = [ord(c) for c in "abcdefghijklmnopqrstuvwxyz"]
STEM_LEFT = "bhijklmnpru"
STEM_RIGHT = "dq"


# ---- the e gate's measure (e_hint_gate.py, copied: that file is another
# agent's to edit; this copy takes a rendered glyph instead of rendering) ----

def e_band(path):
    """(terminal top, bar underside) in font units, unhinted at 1000 ppem."""
    g = raster.render_set(path, 1000, 72, raster.FT_LOAD_NO_HINTING, [ord("e")])[ord("e")]
    pad = 3
    cov = np.pad(g.a8 / 255.0, pad)
    top = g.top + pad
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
    under_row = runs[1][1]
    low = ink.copy(); low[:under_row + 1] = False
    tip_col = np.nonzero(low.any(0))[0].max() - 2
    tip_row = np.nonzero(low[:, tip_col])[0].min()
    return top - tip_row, top - under_row


def mouth_block(cov, top, ppem, band):
    pad = 3
    cov = np.pad(cov, pad); top = top + pad
    s = ppem / 1000.0
    lo, hi = band[0] * s, band[1] * s
    inkcols = np.nonzero((cov > 0.05).any(0))[0]
    c0 = (inkcols.min() + inkcols.max()) // 2; c1 = inkcols.max()
    best = 1.0
    for r in range(cov.shape[0]):
        if lo <= top - r - 0.5 <= hi:
            best = min(best, float(cov[r, c0:c1 + 1].max()))
    return round(best, 3)


# ---- geometry ------------------------------------------------------------

def design_edges(path):
    """{cp: (top, bottom)} in font units, from the unhinted 1000 ppem render."""
    gs = raster.render_set(path, 1000, 72, raster.FT_LOAD_NO_HINTING, LC)
    out = {}
    for cp, g in gs.items():
        rows = np.nonzero((g.a8 >= 128).any(1))[0]
        out[cp] = (g.top - rows.min(), g.top - rows.max() - 1)
    return out


def edges(g):
    """Rendered (top, bottom) edge in px above the baseline, sub-pixel."""
    c = g.lv / 3.0
    P = c.max(1)
    n = len(P)
    i = 0
    frac_top = 0.0
    while i < n and P[i] < 1.0:
        frac_top += 1.0 - P[i]; i += 1
    top = g.top - frac_top
    j = n - 1
    frac_bot = 0.0
    while j >= 0 and P[j] < 1.0:
        frac_bot += 1.0 - P[j]; j -= 1
    bot = g.top - n + frac_bot
    first = np.nonzero(P > 0)[0]
    return top, bot, float(P[first[0]]), float(P[first[-1]])


def stem(g, ppem, xh_units, right=False):
    """Ink width (px) and level pattern of the stem run at mid x-height."""
    y = xh_units * ppem / 1000.0 * 0.5
    r = int(round(g.top - y - 0.5))
    r = min(max(r, 0), g.lv.shape[0] - 1)
    row = g.lv[r]
    runs, x = [], 0
    while x < len(row):
        if row[x]:
            s0 = x
            while x < len(row) and row[x]:
                x += 1
            runs.append(row[s0:x])
        x += 1
    if not runs:
        return None
    run = runs[-1] if right else runs[0]
    return float(run.sum()) / 3.0, "".join(str(v) for v in run)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fonts", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--arms", default=",".join(raster.ARMS))
    a = ap.parse_args()
    from fontTools.ttLib import TTFont
    res = {}
    for style in ("Regular", "Italic"):
        base = raster.font_path(a.fonts, "today", style)
        xh = TTFont(base)["OS/2"].sxHeight
        de = design_edges(base)
        tops_flat = [cp for cp, (t, b) in de.items() if abs(t - xh) <= 3]
        tops_round = [cp for cp, (t, b) in de.items() if 3 < t - xh <= 25]
        bots_flat = [cp for cp, (t, b) in de.items() if abs(b) <= 3]
        bots_round = [cp for cp, (t, b) in de.items() if -25 <= b < -3]
        groups = dict(top_flat=tops_flat, top_round=tops_round,
                      bot_flat=bots_flat, bot_round=bots_round)
        res.setdefault("_groups", {})[style] = {k: "".join(map(chr, v)) for k, v in groups.items()}
        res.setdefault("_xh", {})[style] = xh
        for arm in a.arms.split(","):
            path = raster.font_path(a.fonts, arm, style)
            band = e_band(path) if style == "Regular" else None
            for key, sz, dpi, ppem, tier in raster.sizes():
                gs = raster.render_set(path, sz, dpi, raster.ARMS[arm][1], LC)
                ideal = raster.render_set(path, sz, dpi, raster.FT_LOAD_NO_HINTING, LC)
                r = dict(tier=tier, ppem=round(ppem, 2))
                # e gate
                if band:
                    e = gs[ord("e")]
                    r["e_block_2bit"] = mouth_block(e.lv / 3.0, e.top, ppem, band)
                    r["e_block_8bit"] = mouth_block(e.a8 / 255.0, e.top, ppem, band)
                # stems
                st = {}
                for ch in STEM_LEFT + STEM_RIGHT:
                    v = stem(gs[ord(ch)], ppem, xh, right=ch in STEM_RIGHT)
                    if v:
                        st[ch] = v
                w = [v[0] for v in st.values()]
                r["stem_w"] = {k: round(v[0], 2) for k, v in st.items()}
                r["stem_pat"] = {k: v[1] for k, v in st.items()}
                r["stem_spread"] = round(max(w) - min(w), 2)
                r["stem_shapes"] = len(set(v[1] for v in st.values()))
                r["stem_mean"] = round(float(np.mean(w)), 2)
                # alignment
                al = {}
                for gname, cps in groups.items():
                    vals, crisp, dev = [], [], []
                    for cp in cps:
                        t, b, pt_, pb = edges(gs[cp])
                        if gname.startswith("top"):
                            vals.append(t); crisp.append(pt_); dev.append(t - de[cp][0] * ppem / 1000)
                        else:
                            vals.append(b); crisp.append(pb); dev.append(b - de[cp][1] * ppem / 1000)
                    if vals:
                        al[gname] = dict(spread=round(max(vals) - min(vals), 2),
                                         crisp=round(float(np.mean(crisp)), 2),
                                         mean_shift=round(float(np.mean(dev)), 2),
                                         mean_edge=round(float(np.mean(vals)), 2))
                r["align"] = al
                # colour
                ratios = []
                tot_r = tot_i = 0.0
                for cp in LC:
                    ink = gs[cp].lv.sum() / 3.0
                    area = ideal[cp].a8.sum() / 255.0
                    tot_r += ink; tot_i += area
                    if area:
                        ratios.append(ink / area)
                r["colour"] = round(tot_r / tot_i, 3)
                r["colour_letter_sd"] = round(float(np.std(ratios)), 3)
                res.setdefault(arm, {}).setdefault(style, {})[key] = r
            print(f"{arm} {style} done", file=sys.stderr, flush=True)
    json.dump(res, open(a.out, "w"), indent=1)


if __name__ == "__main__":
    main()
