#!/usr/bin/env python3
"""mid_punct_grid.py -- what a vertical shift does to a THIN mark on the X3's pixel grid
(docs/albo-mid-punctuation-2026-10-04.md, owner todo 2026-10-04: *"raise middot and other mid
punctuation to be optically vertically centered"*).

    $VENV/bin/python instruments/mid_punct_grid.py DIR [--cuts Regular,Italic] [--dash 0:31:1] [--math 40:81:1] [--dot 0:46:1]

WHY. The reader renders Albo unhinted at 2-bit levels (round 401), so a bar 34-40 units thick --
the 400s' dashes and minus -- is under one pixel tall at the X3's 8-12 pt (150 dpi: 1 px = 60, 48,
40 units). Where it lands on the grid decides whether it draws as one dark row or as two pale ones:
a whole-unit raise that is right for the eye can turn the 10 pt em dash gray. Measured on the arms
first (parts_check.py FAINT=1); this scans every shift without building a font.

HOW. Each glyph of DIR's round-480-style font is loaded with FT_Set_Transform's delta = the shift,
so the outline itself is moved before it is rasterized -- the same raster a build carrying that
shift gives, to the unit the build rounds to -- at the reader sizes parts_audit.py uses (8-18 pt at
150 dpi, 1x and 2x), and reduced to the reader's levels (parts_audit.levels). Per glyph and size:
  faint   parts_check.py's FAINT number: the share of the stroke's ridge (taken on a 400 px master
          shifted the same way) that lands on level <= 1, x100. Over 25 is flagged
  merged  for = only: its two bars are not SEEN -- the middle columns' row profile (the
          darkest level in each row) has no valley a level lighter than a bar on each side
For the math class the + and = are scanned as ALBO_MID_MATH_ONE_AXIS draws them: their r480 outline
shifted by (shift - 0.05 XH), since that switch drops them 0.05 x-height onto the other signs' axis.
The dot reports its darkest level and its dark-pixel count (level >= 2) instead -- a wedge that
small is always partly pale, and what matters is that it does not vanish.
"""
import os, sys
import numpy as np, freetype
from scipy import ndimage as ndi
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parts_audit import levels, READER_PT, TIERS, DPI, MASTER

XH_UNITS = 429.0          # pen.XH: the one-axis drop is 0.05 of it (marks.g_plus / g_equal)
ONE_AXIS_DROP = 0.05 * XH_UNITS
CLASSES = {"dash": "-\u2013\u2014", "math": "\u2212+=\u00d7\u00f7", "dot": "\u00b7"}


def render(face, gid, size64, dpi, dy_px):
    """parts_audit.render with the outline moved up dy_px pixels before rasterizing."""
    face.set_char_size(size64, size64, dpi, dpi)
    face.set_transform(freetype.Matrix(0x10000, 0, 0, 0x10000), freetype.Vector(0, int(round(dy_px * 64))))
    face.load_glyph(gid, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING)
    face.set_transform(freetype.Matrix(0x10000, 0, 0, 0x10000), freetype.Vector(0, 0))
    b = face.glyph.bitmap
    if not b.rows or not b.width: return None
    a8 = np.frombuffer(bytes(b.buffer), dtype=np.uint8).reshape(b.rows, b.pitch)[:, :b.width]
    return a8, face.glyph.bitmap_left, face.glyph.bitmap_top


def faint(face, ch, dy_units, pt, tier):
    """parts_check.py's FAINT share for `ch` shifted dy_units, and (for =) whether the bars merged."""
    upm = face.units_per_EM; gid = face.get_char_index(ord(ch))
    a8h, lh, th = render(face, gid, MASTER * 64, 72, dy_units * MASTER / upm); ink = a8h >= 128
    d_ = ndi.distance_transform_edt(np.pad(ink, 1))[1:-1, 1:-1]
    ridge = (d_ == ndi.maximum_filter(d_, 3)) & (d_ > 1.5); ry, rx = np.nonzero(ridge)
    ppem = pt * tier * DPI / 72.0; s = ppem / MASTER
    a8, l, tp = render(face, gid, (pt * tier) << 6, DPI, dy_units * ppem / upm); lv = levels(a8); H, W = lv.shape
    X = (rx + lh + 0.5) * s; Y = (th - ry - 0.5) * s
    ly = np.clip((tp - Y).astype(int), 0, H - 1); lx = np.clip((X - l).astype(int), 0, W - 1)
    fr = float(np.mean(lv[ly, lx] <= 1)) if len(ry) else 0.0
    merged = None
    if ch == "=":
        # the two bars are SEEN when the middle columns' row profile (darkest level per row)
        # has a valley at least one level lighter than a bar on either side of it -- black,
        # light gray, black reads as "="; black, dark gray, black and an even gray slab do not
        p = lv[:, W // 3: 2 * W // 3 + 1].max(1)
        merged = not any(p[j] < min(p[:j].max(), p[j + 1:].max()) for j in range(1, len(p) - 1))
    return fr * 100, merged, int((lv >= 2).sum()), int(lv.max())


def scan(path, cls, lo, hi, step):
    face = freetype.Face(path); out = {}
    for dy in range(lo, hi, step):
        row = {}
        for ch in CLASSES[cls]:
            d = dy - ONE_AXIS_DROP if (cls == "math" and ch in "+=") else dy
            row[ch] = {(pt, t): faint(face, ch, d, pt, t) for t in TIERS for pt in READER_PT}
        out[dy] = row
    return out


def show(path, cls, lo, hi, step, sizes):
    res = scan(path, cls, lo, hi, step)
    hdr = " ".join(f"{pt}{'' if t == 1 else '@2x'}".rjust(6) for pt, t in sizes)
    print(f"\n{os.path.basename(path)}  class {cls}  (faint % per size; * over 25; M = the = merged; dot: max level/dark px)")
    for ch in CLASSES[cls]:
        print(f"  U+{ord(ch):04X}   shift  {hdr}   worst@1x(8-12)")
        for dy, row in res.items():
            cells = []; worst = 0.0
            for (pt, t) in sizes:
                f, m, dark, mx = row[ch][(pt, t)]
                if cls == "dot": cells.append(f"{mx}/{dark}".rjust(6)); continue
                if t == 1 and pt <= 12: worst = max(worst, f)
                cells.append((f"{f:.0f}" + ("*" if f > 25 else "") + ("M" if m else "")).rjust(6))
            print(f"          {dy:+4d}  " + " ".join(cells) + ("" if cls == "dot" else f"   {worst:.0f}"))


if __name__ == "__main__":
    a = sys.argv[1:]; d = a[0]
    cuts = a[a.index("--cuts") + 1].split(",") if "--cuts" in a else ["Regular", "Italic"]
    rng = {"dash": (0, 31, 1), "math": (40, 81, 1), "dot": (0, 46, 1)}
    for k in list(rng):
        if f"--{k}" in a: rng[k] = tuple(int(x) for x in a[a.index(f"--{k}") + 1].split(":"))
    only = [k for k in rng if f"--{k}" in a] or list(rng)
    sizes = [(pt, t) for t in TIERS for pt in READER_PT]
    for cut in cuts:
        for cls in only:
            show(os.path.join(d, f"Albo-{cut}.ttf"), cls, *rng[cls], sizes)
