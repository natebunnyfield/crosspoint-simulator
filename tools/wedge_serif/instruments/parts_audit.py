#!/usr/bin/env python3
"""Which glyphs LOSE A VITAL PART at the reader's sizes (owner 2026-09-28:
"find all instances where vital parts of a letter go missing like the tittle
of i here" -- a phone screenshot of the italic with the i's dot gone and e's
reading as c; and "crossbars like f might not be thick enough at small scale").

Every encoded glyph, rendered as the reader's converter renders it
(set_char_size(pt*64, pt*64, 150, 150), FT_LOAD_RENDER | NO_HINTING, 8-bit cut
to 2 bits: top nibble >=12/8/4 -> 3/2/1; etrace/e_hint_gate.py), at every Albo
slot (8..18 pt, 1x and the phone's 2x tier), against a 400 px master:

  PARTS    each connected ink part of the master (8-connected, >= 0.5) -- the
           tittle, an accent, a colon's dots -- must reach level >= 2 somewhere
           in its footprint at the reader size. FAINT = only level 1 there,
           GONE = level 0.
  COUNTERS each enclosed counter of the master must still be enclosed by
           level >= 2 ink (an e whose bar dropped opens its eye; a filled bowl
           closes it). LOST = the count at the reader size is lower.
  FAINT STROKE  the fraction of the master's ridge (distance-transform local
           maxima, the stroke's centre line) that lands on level <= 1: a
           crossbar or hairline drawn in faint grey only.

    $VENV/bin/python parts_audit.py FONT.ttf [FONT.ttf ...] [--json OUT]
"""
import sys, json
import numpy as np, freetype
from scipy import ndimage as ndi
from fontTools.ttLib import TTFont

READER_PT = [8, 10, 12, 14, 16, 18]; TIERS = [1, 2]; DPI = 150; MASTER = 400


def render(face, gid, size64, dpi):
    face.set_char_size(size64, size64, dpi, dpi)
    face.load_glyph(gid, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING)
    b = face.glyph.bitmap
    if not b.rows or not b.width:
        return None
    a8 = np.frombuffer(bytes(b.buffer), dtype=np.uint8).reshape(b.rows, b.pitch)[:, :b.width]
    return a8, face.glyph.bitmap_left, face.glyph.bitmap_top


def levels(a8):
    n = a8 >> 4
    return np.where(n >= 12, 3, np.where(n >= 8, 2, np.where(n >= 4, 1, 0)))


def holes(mask):
    bg = ~mask
    lab, n = ndi.label(bg, structure=np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]]))
    edge = set(np.unique(np.r_[lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
    return sum(1 for i in range(1, n + 1) if i not in edge)


def audit(path):
    tt = TTFont(path); cmap = tt.getBestCmap()
    face = freetype.Face(path)
    out = []
    for cp, name in sorted(cmap.items()):
        ch = chr(cp)
        if ch.isspace() or cp < 33:
            continue
        gid = face.get_name_index(name.encode()) or face.get_char_index(cp)
        m = render(face, gid, MASTER * 64, 72)
        if m is None:
            continue
        a8h, lh, th = m; ink = a8h >= 128
        lab, nparts = ndi.label(np.pad(ink, 1), structure=np.ones((3, 3)))
        lab = lab[1:-1, 1:-1]
        sizes = ndi.sum(ink, lab, range(1, nparts + 1)) if nparts else []
        parts = [i + 1 for i, s in enumerate(sizes) if s >= 0.0004 * MASTER * MASTER]   # ignore specks
        hh = holes(np.pad(ink, 1))
        d = ndi.distance_transform_edt(ink); ridge = (d == ndi.maximum_filter(d, 3)) & (d > 1.5)
        ry, rx = np.nonzero(ridge)
        for t in TIERS:
            for pt in READER_PT:
                size64 = (pt * t) << 6; ppem = pt * t * DPI / 72.0; s = ppem / MASTER
                r = render(face, gid, size64, DPI)
                if r is None:
                    continue
                a8, l, tp = r; lv = levels(a8); H, W = lv.shape
                def to_low(yy, xx):
                    # master pixel -> reader pixel, through font space
                    X = (xx + lh + 0.5) * s; Y = (th - yy - 0.5) * s
                    return np.clip((tp - Y).astype(int), 0, H - 1), np.clip((X - l).astype(int), 0, W - 1)
                bad_parts = []
                # each part's OWN footprint only (no margin: a tittle sitting a
                # pixel above its stem would borrow the stem's ink -- the first
                # version of this audit passed every i that way). A part counts
                # as SMALL when its dark (level >= 2) area is under 4 px, i.e.
                # a dot of about 2 x 2 or less.
                own = np.zeros((H, W), bool)
                for pi in parts:
                    yy, xx = np.nonzero(lab == pi)
                    ly, lx = to_low(yy, xx)
                    fp = np.zeros((H, W), bool); fp[ly, lx] = True
                    if len(parts) > 1:
                        for pj in parts:
                            if pj != pi:
                                y2, x2 = np.nonzero(lab == pj); oy, ox = to_low(y2, x2); fp[oy, ox] = False
                    mx = int(lv[fp].max()) if fp.any() else 0
                    dark = int((lv[fp] >= 2).sum())
                    if len(parts) > 1 and (mx < 2 or dark < 4):
                        bad_parts.append(("GONE" if mx == 0 else ("FAINT" if mx < 2 else "SMALL"), dark, int(len(yy))))
                hl = holes(np.pad(lv >= 2, 1))
                ly, lx = to_low(ry, rx)
                faint = float(np.mean(lv[ly, lx] <= 1)) if len(ry) else 0.0
                key = f"{pt}pt" + ("" if t == 1 else "@2x")
                if bad_parts or hl < hh or faint > 0.25:
                    out.append(dict(glyph=name, char=ch, size=key, ppem=round(ppem, 1),
                                    parts=bad_parts, holes=(hh, hl), faint=round(faint, 3)))
    return out


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    jo = sys.argv[sys.argv.index("--json") + 1] if "--json" in sys.argv else None
    if jo: args = [a for a in args if a != jo]
    res = {}
    for p in args:
        r = audit(p); res[p] = r
        print(p, len(r), "findings")
    if jo: json.dump(res, open(jo, "w"), indent=1, ensure_ascii=False)
