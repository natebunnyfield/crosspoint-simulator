"""Trace the K's upper arm and its top-right terminal in the bold reference
faces into Albo's units (2026-10-04; docs/albo-bold-k-2026-10-04.md, fourth
pass).

Owner 2026-10-04, after three passes on the Bold K's top-right serif (V, T, U):
*"getting worse"*, then *"let's trace references and see what is possible"*.

TRACING IS MEASUREMENT, NOT COPYING (fig27_trace.py's rule). Every face is
rendered UNHINTED and scaled so ITS H's top lands on Albo's (676 units), at
PX px per unit -- the K is a capital, so the faces share a cap height rather
than an x-height. What comes out is a description of the arm's end in Albo's
units and in the face's OWN H stem (`_s`); no outline point of a reference is
used. The same function reads an Albo build, so arm and reference go through
one instrument.

    python3 instruments/k_arm_trace.py [--albo LABEL=FONT ...] [--sheet OUT.png] [--zoom OUT.png] [--json OUT]

What each number is (Albo units, cap 676):
  stem     the face's H stem, horizontal run at a quarter of the cap height
  ang      the arm's angle from horizontal, from straight-line fits to both of
           its edges over 0.66-0.84 of the cap height (where it is arm only)
  arm      the arm's perpendicular thickness there; arm_s = arm / stem
  top      the highest ink of the arm's end (676 = on the cap line)
  flat     the width of the end's ink within 8 units of its own top: a serif
           sitting flat on the cap line reads long, a pointed end reads short
  reach_l  how far the end's ink runs LEFT of the arm's upper edge, extended:
           the serif or flare on the arm's upper side
  reach_r  how far it runs RIGHT of the arm's lower edge, extended: the serif
           or flare on the lower side, under the end
  drop_l, drop_r   how far below the top each reach is still more than 4
           units: the depth of that side's serif or flare
  end_x    the end's rightmost ink over the stem's left edge, over the cap
           height (the arm's horizontal span, the letter's top width)
  H serif  the face's own stem-top serif, out (left of the H's left stem) and
           in (right of it), the most over the top 40 units: the yardstick for
           the arm's
  leg      the leg's perpendicular thickness over 0.15-0.40 C (under the crotch,
           over the foot), over the stem and over the arm, and its angle
"""
import argparse, json, math, os, sys
import numpy as np
import freetype

SUP = "/System/Library/Fonts/Supplemental/"
DL = os.path.expanduser("~/Downloads/")
CAP_ALBO = 676.0
PX = 2.0

REFS = [
    ("Albertus", DL + "Albertus Medium Regular.ttf", 0),
    ("Trajan Bold", DL + "trajan-pro/TrajanPro-Bold.otf", 0),
    ("Berkeley Bold", DL + "ITC Berkeley Oldstyle/ITC Berkeley Oldstyle Bold/ITC Berkeley Oldstyle Bold.otf", 0),
    ("Georgia Bold", SUP + "Georgia Bold.ttf", 0),
    ("Charter Bold", SUP + "Charter.ttc", 3),
    ("Times Bold", SUP + "Times New Roman Bold.ttf", 0),
    ("Baskerville Bold", SUP + "Baskerville.ttc", 1),
    ("Hoefler Black", SUP + "Hoefler Text.ttc", 1),
    ("Palatino Bold", "/System/Library/Fonts/Palatino.ttc", 2),
    ("Iowan Bold", SUP + "Iowan Old Style.ttc", 1),
    ("Athelas Bold", SUP + "Athelas.ttc", 3),
    ("Cochin Bold", SUP + "Cochin.ttc", 1),
    ("Optima Bold", "/System/Library/Fonts/Optima.ttc", 1),
]


def render(path, idx, ch, px_per_unit=PX):
    """ch with the face's H top at CAP_ALBO units; returns (alpha array, origin
    x in px, baseline row in px, px per unit)."""
    f = freetype.Face(path, idx)
    f.set_char_size(2048 * 64, 0, 72, 72)
    f.load_char("H", freetype.FT_LOAD_NO_HINTING)
    cap_px = f.glyph.metrics.horiBearingY / 64.0
    size = 2048.0 * (CAP_ALBO * px_per_unit) / cap_px
    f.set_char_size(int(round(size * 64)), 0, 72, 72)
    f.load_char(ch, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING)
    b = f.glyph.bitmap
    a = np.array(b.buffer, np.uint8).reshape(b.rows, b.pitch)[:, :b.width]
    return a, f.glyph.bitmap_left, f.glyph.bitmap_top


def runs(row):
    m = np.concatenate([[0], (row > 127).astype(np.int8), [0]])
    d = np.diff(m); s = np.nonzero(d == 1)[0]; e = np.nonzero(d == -1)[0]
    return list(zip(s, e))


def stem_width(path, idx):
    a, l, t = render(path, idx, "H")
    y = int(t - CAP_ALBO * PX * 0.25)          # under the bar
    r = runs(a[y])
    return (r[0][1] - r[0][0]) / PX


def h_serif(path, idx):
    """The face's OWN stem-top serif: how far the H's left stem's top reaches
    left (outer) and right (inner) of the stem's edges, the MOST over the top
    40 units -- the yardstick an arm serif is read against, so a face whose
    serifs are all long does not read as having a long arm serif. The most,
    not one row: Albo's wedge top slopes down 17 units to its tip, so any one
    row near the cap line reads it short (6 units under the top read 26 of its
    52)."""
    a, l, t = render(path, idx, "H")
    r0 = runs(a[int(t - CAP_ALBO * PX * 0.25)])[0]
    top = None
    for y in range(a.shape[0]):
        if (a[y] > 127).any(): top = y; break
    out = inn = 0.0
    for y in range(top, top + int(40 * PX)):
        rt = runs(a[y])[0]
        out = max(out, (r0[0] - rt[0]) / PX); inn = max(inn, (rt[1] - r0[1]) / PX)
    return out, inn


def measure(path, idx):
    a, l, t = render(path, idx, "K")
    H, W = a.shape
    U = lambda px: px / PX
    def row_at(yu):                     # Albo units above baseline -> raster row
        return int(round(t - yu * PX))
    # the stem: the first run at a quarter of the height, under the arm's root and
    # left of the leg; its right edge, with a margin
    rs = runs(a[row_at(CAP_ALBO * 0.25)])
    stem_l, stem_r = rs[0]
    # the arm's run in a row: the WIDEST run whose left edge clears the stem. Not
    # the rightmost: round 479's under-side wedge hangs its tip into this band as
    # a separate 9-unit sliver right of the arm, and taking it read the arm at
    # 36 degrees where its edges run at 44.5
    def arm_run(yu):
        y = row_at(yu)
        if y < 0 or y >= H: return None
        cand = [r for r in runs(a[y]) if r[0] > stem_r + 2]
        return max(cand, key=lambda r: r[1] - r[0]) if cand else None
    ys, xl, xr = [], [], []
    for yu in np.arange(CAP_ALBO * 0.66, CAP_ALBO * 0.84, 2.0):
        r = arm_run(yu)
        if r: ys.append(yu); xl.append(U(r[0])); xr.append(U(r[1]))
    ys = np.array(ys); bl = np.polyfit(ys, xl, 1); br = np.polyfit(ys, xr, 1)
    slope = (bl[0] + br[0]) / 2.0                       # dx/dy
    ang = math.degrees(math.atan2(1.0, slope))
    run_w = np.median(np.array(xr) - np.array(xl))
    arm = run_w * math.sin(math.radians(ang))
    # the end: every row from the top of the ink down to 0.84 C, right of the stem
    rows = []
    yu = CAP_ALBO + 60.0
    while yu > CAP_ALBO * 0.84:
        y = row_at(yu)
        if 0 <= y < H:
            # the RIGHTMOST run only: a concave top splits the cap-line row into
            # slivers, and the stem's own top corner then reads as a run past the
            # stem (Optima's did, and its flat read 360 units for a 120-unit end)
            cand = [r for r in runs(a[y]) if r[0] > stem_r + 2]
            if cand:
                rows.append((yu, U(cand[-1][0]), U(cand[-1][1])))
        yu -= 1.0
    top = max(r[0] for r in rows)
    flat_rows = [r for r in rows if r[0] >= top - 8.0]
    flat = max(r[2] for r in flat_rows) - min(r[1] for r in flat_rows)
    lineL = lambda y: bl[0] * y + bl[1]; lineR = lambda y: br[0] * y + br[1]
    rl = [(lineL(y) - x0, y) for y, x0, x1 in rows]; rr = [(x1 - lineR(y), y) for y, x0, x1 in rows]
    reach_l = max(v for v, _ in rl); reach_r = max(v for v, _ in rr)
    drop_l = top - min([y for v, y in rl if v > 4.0], default=top)
    drop_r = top - min([y for v, y in rr if v > 4.0], default=top)
    end_x = (max(r[2] for r in rows) - U(stem_l)) / CAP_ALBO
    # the LEG: the widest run right of the stem over 0.15-0.40 C, where only the
    # leg is (under the crotch, over the foot's bracket); edges fitted as the arm's
    ys2, ll, lr = [], [], []
    for yu in np.arange(CAP_ALBO * 0.15, CAP_ALBO * 0.40, 2.0):
        r = arm_run(yu)
        if r: ys2.append(yu); ll.append(U(r[0])); lr.append(U(r[1]))
    ys2 = np.array(ys2); gl = np.polyfit(ys2, ll, 1); gr = np.polyfit(ys2, lr, 1)
    lslope = (gl[0] + gr[0]) / 2.0
    lang = math.degrees(math.atan2(1.0, -lslope))          # the leg falls to the right: angle from horizontal
    leg = np.median(np.array(lr) - np.array(ll)) * math.sin(math.radians(lang))
    return dict(ang=ang, arm=arm, top=top, flat=flat, reach_l=reach_l, reach_r=reach_r,
                drop_l=drop_l, drop_r=drop_r, end_x=end_x, leg=leg, leg_ang=lang)


def sheet(items, out, cap_px=260, zoom=None):
    from PIL import Image, ImageDraw, ImageFont
    LAB = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)
    cells = []
    for lab, path, idx in items:
        ppu = cap_px / CAP_ALBO
        a, l, t = render(path, idx, "K", ppu)
        if zoom:                            # the upper right: the arm's end and its serif
            cw, chh = int(cap_px * 0.62), int(cap_px * 0.42)
            base = t + 60                   # room above the cap line, or the crop runs off the image
            im = Image.new("L", (a.shape[1] + 60, base + 20), 250)
            im.paste(Image.fromarray(255 - a), (30, base - t), Image.fromarray(a))
            capy = base - cap_px
            ink = np.nonzero((np.array(im) < 128).any(0))[0]
            x1 = ink[-1] + 24
            crop = im.crop((x1 - cw, capy - 40, x1, capy - 40 + chh))
            d = ImageDraw.Draw(crop); d.line([(0, 40), (cw, 40)], fill=190)
            d.rectangle([0, 0, 12 * len(lab) + 14, 26], fill=250); d.text((6, 3), lab, fill=0, font=LAB)
            cells.append(crop)
        else:
            w = int(cap_px * 1.5); h = int(cap_px * 1.42); base = int(cap_px * 1.25)   # 1.5: Hoefler's and Georgia's K run past 1.2 caps
            im = Image.new("L", (w, h), 250); d = ImageDraw.Draw(im)
            d.line([(0, base - cap_px), (w, base - cap_px)], fill=205); d.line([(0, base), (w, base)], fill=205)
            im.paste(Image.fromarray(255 - a), (int(cap_px * 0.1) + l, base - t), Image.fromarray(a))
            d.text((6, 4), lab, fill=0, font=LAB); cells.append(im)
    cols = 5 if not zoom else 4
    cw, chh = cells[0].size
    rows_ = (len(cells) + cols - 1) // cols; g = 10
    out_im = Image.new("L", (cols * cw + (cols - 1) * g, rows_ * chh + (rows_ - 1) * g), 255)
    for i, c in enumerate(cells):
        out_im.paste(c, ((i % cols) * (cw + g), (i // cols) * (chh + g)))
    out_im.save(out)
    return out_im.size


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--albo", action="append", default=[], help="LABEL=FONT, read the same way, listed first")
    ap.add_argument("--sheet"); ap.add_argument("--zoom"); ap.add_argument("--json")
    ap.add_argument("--no-refs", action="store_true")
    a = ap.parse_args()
    items = [(s.split("=", 1)[0], s.split("=", 1)[1], 0) for s in a.albo] + ([] if a.no_refs else REFS)
    res = {}
    print(f"{'face':18s} {'stem':>5s} {'ang':>5s} {'arm':>5s} {'arm_s':>5s} {'top':>5s} {'flat':>5s} {'reach_l':>7s} {'drop_l':>6s} {'reach_r':>7s} {'drop_r':>6s} {'end_x':>5s}")
    for lab, path, idx in items:
        try:
            st = stem_width(path, idx); m = measure(path, idx)
        except Exception as e:
            print(f"{lab:18s} FAILED {e}"); continue
        m["stem"] = st; m["hser_l"], m["hser_r"] = h_serif(path, idx); res[lab] = m
        print(f"{lab:18s} {st:5.0f} {m['ang']:5.1f} {m['arm']:5.0f} {m['arm']/st:5.2f} {m['top']:5.0f} {m['flat']:5.0f} "
              f"{m['reach_l']:7.0f} {m['drop_l']:6.0f} {m['reach_r']:7.0f} {m['drop_r']:6.0f} {m['end_x']:5.2f}"
              f"   H serif out {m['hser_l']:4.0f} in {m['hser_r']:4.0f}   leg {m['leg']:4.0f} = {m['leg']/st:4.2f} stem, {m['leg']/m['arm']:4.2f} arm, at {m['leg_ang']:4.1f}")
    if a.json: json.dump(res, open(a.json, "w"), indent=1)
    if a.sheet: print("sheet", sheet(items, a.sheet))
    if a.zoom: print("zoom", sheet(items, a.zoom, cap_px=700, zoom=True))
