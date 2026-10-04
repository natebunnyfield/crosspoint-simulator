#!/usr/bin/env python3
"""word_parts.py -- the parts that explain each letter word_measure.py calls out, measured the same
way in Albo and in the reference faces (docs/albo-word-images-2026-10-04.md).

Every face is rendered UNHINTED at a 429-unit x-height (Albo's own; each reference scaled so its
x-height -- word_measure.measure_xh -- is 429), coverage >= 50% as ink, italics unsheared by their
measured slant (word_measure.measure_slant, off the face's own l) so a column means the same thing
in every face. All numbers are in these Albo-sized units unless a ratio.

  adv, lsb, rsb      the advance and the two sidebearings (ink box), units
  width              ink width, units
  band_ink           ink area between the baseline and the x-height, over the n's
  aperture           c e s a: the white gap, in units, between the upper and lower ink in the
                     column 80% across the ink box -- the mouth a reader sees
  mouth_rows         c e: rows of the right 25% of the ink box with NO ink, over the x-height --
                     the mouth's height
  term_top/term_bot  c: the rightmost ink in the top and the bottom 30% of the x-height, as a
                     fraction of the ink width -- how far each terminal reaches
  bowl_left          c e o: the left bowl's thickness at mid x-height, units
  hook_over          f: how far the hook's ink passes the advance (+ = overhangs), units
  bar_right          f t: the bar's right end against the advance (+ = past it), units
  stem_x             f t: the stem's left edge from the origin, units
  parts_top/mid/bot  u n: band ink in the top 25%, middle 50% and bottom 25% of the x-height,
                     each over the n's same slice
  join_L / join_R    n h m u b d p q a: the counter's top and bottom read 6 units inside the LEFT
                     (first) or RIGHT (last) stem at mid x-height, so an arch or a bowl is
                     measured where it LEAVES its stem. For n h m: arch_depth = x-height - the
                     counter's top at the left stem (how far below the x-line the arch lets go of
                     the stem). For u: bowl_rise = the counter's bottom at the right stem (how far
                     above the baseline the bowl reaches the stem). A u is an n turned over, so in
                     every reference the two agree within a few units; that is the test.

    $VENV instruments/word_parts.py --albo DIR [--letters cefuknh] [--json out.json]
"""
import argparse, json, math, os, sys
import numpy as np
import freetype

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import word_measure as WM  # noqa: E402

XH = 429.0


def mask(path, index, ch, italic):
    xh = WM.measure_xh(path, index)
    f = freetype.Face(path, index)
    ppem = XH / xh                                    # 1 px = 1 Albo unit at this size
    f.set_char_size(int(round(ppem * 64)), int(round(ppem * 64)), 72, 72)
    sl = WM.measure_slant(path, index) if italic else 0.0
    gid = f.get_char_index(ch)
    if not gid:
        return None
    a, left, top = WM._render(f, gid, shear=sl)
    adv = f.glyph.advance.x / 64.0
    if not a.size:
        return None
    m = a >= 128
    return m, left, top, adv


def rows_y(m, top):
    return top - np.arange(m.shape[0]) - 0.5          # row center, units above the baseline


def parts(path, index, ch, italic, n_ref=None):
    r = mask(path, index, ch, italic)
    if r is None:
        return None
    m, left, top, adv = r
    y = rows_y(m, top)
    cols = np.nonzero(m.any(0))[0]
    x0, x1 = cols[0], cols[-1] + 1
    out = dict(adv=float(adv), lsb=float(left + x0), rsb=float(adv - (left + x1)), width=float(x1 - x0))
    band = (y >= 0) & (y <= XH)
    out["band_px"] = float(m[band].sum())
    # aperture at 80% across the ink box
    cx = int(x0 + 0.80 * (x1 - x0))
    col = m[:, cx] & band
    ys = np.nonzero(col)[0]
    if len(ys) >= 2:
        gaps = np.diff(ys) - 1
        out["aperture"] = float(gaps.max())
    # the mouth: band rows with no ink in the right 25% of the box
    right = m[:, int(x0 + 0.75 * (x1 - x0)):x1]
    out["mouth_rows"] = float(((~right.any(1)) & band).sum()) / XH
    # terminals
    for name, lo, hi in (("term_top", 0.70, 1.0), ("term_bot", 0.0, 0.30)):
        sel = band & (y >= lo * XH) & (y <= hi * XH)
        cs = np.nonzero(m[sel].any(0))[0]
        out[name] = float((cs[-1] + 1 - x0) / (x1 - x0)) if len(cs) else float("nan")
    # left bowl at mid x-height
    rmid = int(np.argmin(np.abs(y - XH / 2)))
    xs = np.nonzero(m[rmid])[0]
    if len(xs):
        run_end = xs[0]
        while run_end + 1 < m.shape[1] and m[rmid, run_end + 1]:
            run_end += 1
        out["bowl_left"] = float(run_end - xs[0] + 1)
        out["stem_x"] = float(left + xs[0])
    # f, t: the hook's overhang and the bar's right end
    above = y > XH * 1.05
    ca = np.nonzero(m[above].any(0))[0] if above.any() else []
    if len(ca):
        out["hook_over"] = float(left + ca[-1] + 1 - adv)
    barrows = band & (y >= 0.80 * XH)
    cb = np.nonzero(m[barrows].any(0))[0]
    if len(cb):
        out["bar_right"] = float(left + cb[-1] + 1 - adv)
    # u / n slices
    for name, lo, hi in (("parts_top", 0.75, 1.0), ("parts_mid", 0.25, 0.75), ("parts_bot", 0.0, 0.25)):
        out[name + "_px"] = float(m[band & (y >= lo * XH) & (y < hi * XH)].sum())
    return out


def counter_at(path, index, ch, italic, side):
    """(top, bottom) of the counter, units above the baseline, read 6 units inside the stem on
    `side` ('L' = the first ink run at mid x-height, 'R' = the last). None without a counter."""
    r = mask(path, index, ch, italic)
    if r is None:
        return None
    m, left, top, adv = r
    y = rows_y(m, top)
    mid = int(np.argmin(np.abs(y - XH * 0.5)))
    xs = np.nonzero(m[mid])[0]
    runs, s = [], xs[0]
    for k in range(1, len(xs)):
        if xs[k] != xs[k - 1] + 1:
            runs.append((s, xs[k - 1])); s = xs[k]
    runs.append((s, xs[-1]))
    if len(runs) < 2:
        return None
    col = runs[0][1] + 6 if side == "L" else runs[-1][0] - 6
    up = mid
    while up > 0 and not m[up - 1, col]:
        up -= 1
    dn = mid
    while dn < m.shape[0] - 1 and not m[dn + 1, col]:
        dn += 1
    return float(y[up]), float(y[dn])


def joins(path, index, italic):
    out = {}
    for ch in "nhm":
        c = counter_at(path, index, ch, italic, "L")
        if c:
            out[ch + "_arch_depth"] = XH - c[0]
    c = counter_at(path, index, "u", italic, "R")
    if c:
        out["u_bowl_rise"] = c[1]
    for ch, side in (("b", "L"), ("p", "L"), ("d", "R"), ("q", "R")):
        c = counter_at(path, index, ch, italic, side)
        if c:
            out[ch + "_bowl_top"] = XH - c[0]; out[ch + "_bowl_bot"] = c[1]
    return out


def faces(albo):
    fs = []
    for c in WM.CUTS:
        fs.append(("Albo", c, os.path.join(albo, f"Albo-{c}.ttf"), 0))
    for r, cuts in WM.REFS.items():
        for c, (p, i) in cuts.items():
            fs.append((r, c, p, i))
    return fs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--albo", required=True)
    ap.add_argument("--letters", default="cefuknhoatidbpqsgwvyT")
    ap.add_argument("--json")
    a = ap.parse_args()
    R = {}
    for lab, cut, p, i in faces(a.albo):
        it = cut in ("Italic", "BoldItalic")
        n = parts(p, i, "n", it)
        row = {}
        for ch in a.letters:
            q = parts(p, i, ch, it)
            if q is None:
                continue
            q["band_ink_n"] = q["band_px"] / n["band_px"]
            for s in ("parts_top", "parts_mid", "parts_bot"):
                q[s] = q[s + "_px"] / max(n[s + "_px"], 1.0)
            row[ch] = q
        row["_joins"] = joins(p, i, it)
        R[f"{lab}/{cut}"] = row
    if a.json:
        json.dump(R, open(a.json, "w"), indent=1)
    keys = ("adv", "width", "lsb", "rsb", "band_ink_n", "aperture", "mouth_rows", "term_top", "term_bot",
            "bowl_left", "hook_over", "bar_right", "stem_x", "parts_top", "parts_mid", "parts_bot")
    print("the stem joins (units at a 429 x-height): n/h/m arch depth below the x-line, u bowl rise above the baseline")
    for f in R:
        J = R[f]["_joins"]
        print(f"  {f:22s} " + "  ".join(f"{k} {v:.0f}" for k, v in J.items()))
    for cut in WM.CUTS:
        print(f"\n== {cut}")
        for ch in a.letters:
            print(f"  {ch}")
            for k in keys:
                vals = {f.split("/")[0]: R[f][ch].get(k) for f in R if f.endswith("/" + cut) and ch in R[f]}
                if all(v is None or (isinstance(v, float) and math.isnan(v)) for v in vals.values()):
                    continue
                refs = [v for f, v in vals.items() if f != "Albo" and v is not None and not math.isnan(v)]
                med = float(np.median(refs)) if refs else float("nan")
                av = vals.get("Albo")
                print(f"    {k:11s} Albo {av if av is None else round(av, 3)!s:>8}  refs med {med:8.3f}  "
                      + "  ".join(f"{f[:4]} {v:.3f}" for f, v in vals.items() if f != "Albo" and v is not None))


if __name__ == "__main__":
    main()
