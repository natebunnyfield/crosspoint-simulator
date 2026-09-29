#!/usr/bin/env python3
"""parts_check.py -- parts_audit.py's PARTS and COUNTERS checks for a few characters, as a TABLE.

    $VENV/bin/python instruments/parts_check.py "ij:;!?" FONT.ttf [FONT.ttf ...]

For each character and reader size (8..18 pt at 1x and 2x, 150 dpi, unhinted, 2-bit levels -- the
reader's converter, exactly as parts_audit.py renders) it prints the dark pixel count (level >= 2)
of the SMALLEST separate part in its own footprint, and '*' where parts_audit would flag it (< 4 dark
px); with COUNTERS=1 it prints the enclosed-counter count instead (master / reader). parts_audit
reports only the failures over every glyph; this is the before/after instrument for one fix.
Written 2026-09-28 for the italic tittle and the small-size dots (docs/albo-issue-sweep-2026-09-28.md).
"""
import sys, os
import numpy as np
from scipy import ndimage as ndi
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parts_audit import render, levels, holes, READER_PT, TIERS, DPI, MASTER
import freetype
from fontTools.ttLib import TTFont

chars = sys.argv[1]; fonts = sys.argv[2:]
COUNTERS = os.environ.get("COUNTERS") == "1"
FAINT = os.environ.get("FAINT") == "1"   # the faint-stroke share (ridge on level <= 1), x100; * above 25
sizes = [(pt, t) for t in TIERS for pt in READER_PT]
print(f"{'font':28s} ch  " + " ".join(f"{pt}{'' if t == 1 else '@2x'}".rjust(7) for pt, t in sizes))
for path in fonts:
    face = freetype.Face(path); cmap = TTFont(path).getBestCmap()
    for ch in chars:
        gid = face.get_char_index(ord(ch))
        a8h, lh, th = render(face, gid, MASTER * 64, 72); ink = a8h >= 128
        lab, np_ = ndi.label(np.pad(ink, 1), structure=np.ones((3, 3))); lab = lab[1:-1, 1:-1]
        sz = ndi.sum(ink, lab, range(1, np_ + 1)) if np_ else []
        parts = [i + 1 for i, s in enumerate(sz) if s >= 0.0004 * MASTER * MASTER]
        hh = holes(np.pad(ink, 1), min_area=0.0015 * MASTER * MASTER)
        # PADDED: parts_audit.py takes the EDT of the tight bitmap, so a flat bar that fills its bitmap's
        # height has no background above or below it inside the array and its 'ridge' lands on the top
        # row -- it reported the Italic hyphen 100% faint at 9 sizes while the reader draws it level 2-3
        d_ = ndi.distance_transform_edt(np.pad(ink, 1))[1:-1, 1:-1]; ridge = (d_ == ndi.maximum_filter(d_, 3)) & (d_ > 1.5); ry, rx = np.nonzero(ridge)
        cells = []
        for pt, t in sizes:
            ppem = pt * t * DPI / 72.0; s = ppem / MASTER
            a8, l, tp = render(face, gid, (pt * t) << 6, DPI); lv = levels(a8); H, W = lv.shape
            if COUNTERS:
                hl = holes(np.pad(lv >= 2, 1)); cells.append(f"{hh}/{hl}{'*' if hl < hh else ' '}".rjust(7)); continue
            def to_low(yy, xx):
                X = (xx + lh + 0.5) * s; Y = (th - yy - 0.5) * s
                return np.clip((tp - Y).astype(int), 0, H - 1), np.clip((X - l).astype(int), 0, W - 1)
            if FAINT:
                ly_, lx_ = to_low(ry, rx); fr = float(np.mean(lv[ly_, lx_] <= 1)) if len(ry) else 0.0
                cells.append(f"{fr * 100:.0f}{'*' if fr > 0.25 else ' '}".rjust(7)); continue
            worst = None
            for pi in parts:
                yy, xx = np.nonzero(lab == pi); ly, lx = to_low(yy, xx)
                fp = np.zeros((H, W), bool); fp[ly, lx] = True
                for pj in parts:
                    if pj != pi:
                        y2, x2 = np.nonzero(lab == pj); oy, ox = to_low(y2, x2); fp[oy, ox] = False
                dark = int((lv[fp] >= 2).sum())
                worst = dark if worst is None else min(worst, dark)
            flag = '*' if (len(parts) > 1 and worst < 4) else ' '
            cells.append(f"{worst}{flag}".rjust(7))
        print(f"{os.path.basename(os.path.dirname(path))[-14:] + '/' + os.path.basename(path)[5:-4]:28s} {ch}   " + " ".join(cells))
