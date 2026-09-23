"""Every bump and glitch the instruments can find, circled in thin red on a
hi-res sheet, one per style, for the owner to confirm by marking up.

Owner 2026-09-18: *"make a hires image with thin red circles around all of the
bumps and glitches you can identify in each character. I will confirm they
need fixes by highlighting them in another color. I will also highlight things
that need fixing that you did not find and circle."*

WHAT IS CIRCLED. The outline is flattened and walked; at each vertex the turn
angle and its change against the neighbours are taken. A vertex is a BUMP when
the edge's direction jolts by more than KINK degrees between one segment and
the next inside a run that is otherwise gentle (a corner -- a turn over
CORNER -- is a designed feature and is not marked), or when the curvature
changes sign twice within a few vertices by more than WAVE degrees (a
zig-zag). Adjacent hits are merged into one circle. Each circle is numbered;
the index file lists style, glyph, number, position in design units and what
was measured, so a confirmation ("roman n 3") maps to a place in the outline.

    PYTHON_GIL=0 python3 albo_bumps.py --roman R.ttf --italic I.ttf --out DIR
"""
import argparse, json, math, os, string
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen

GLYPHS = list(string.ascii_uppercase) + list(string.ascii_lowercase) + list("0123456789") + list(".,;:!?'\"-&@()")
KINK, CORNER, WAVE, MERGE = 9.0, 38.0, 7.0, 30.0     # MERGE: units between two circles


def contours(ttf, ch, f=None):
    f = f or TTFont(ttf); cmap = f.getBestCmap(); gs = f.getGlyphSet()
    if ord(ch) not in cmap: return []
    r = RecordingPen(); gs[cmap[ord(ch)]].draw(r)
    polys, cur = [], []
    def q(p0, p1, p2, n=10):
        return [((1-t)**2*p0[0]+2*(1-t)*t*p1[0]+t*t*p2[0], (1-t)**2*p0[1]+2*(1-t)*t*p1[1]+t*t*p2[1]) for t in [i/n for i in range(1, n+1)]]
    for op, a in r.value:
        if op == 'moveTo': cur = [a[0]]
        elif op == 'lineTo': cur.append(a[0])
        elif op == 'qCurveTo':
            pts = list(a)
            if pts[-1] is None: pts = pts[:-1] + [cur[0]]
            for i in range(len(pts) - 1):
                mid = ((pts[i][0]+pts[i+1][0])/2, (pts[i][1]+pts[i+1][1])/2) if i < len(pts)-2 else pts[-1]
                cur += q(cur[-1], pts[i], mid)
        elif op in ('closePath', 'endPath'):
            if len(cur) > 3: polys.append(cur)
            cur = []
    return polys


def bumps(polys, r=12.0, min_area=70.0, max_extent=80.0):
    """[(x, y, kind, value)] in design units.

    RECALIBRATED 2026-09-18, on the owner's W. Three detectors circled the
    edges' sub-unit waviness -- facets, then bowls, then diagonals (563 on the
    roman, 40 of them on the W's flanks) -- and he called it a complete miss:
    *"each end of the W strokes have errors ... I'm looking for big optical
    glitches."* Those are FEATURES of the ink, not deviations of an edge: a
    notch at a junction, a tab or spur standing off a terminal, a step where
    two pieces of a stroke did not meet. They are all things smaller than the
    pen. So the ink is compared with itself at the pen's scale: a CLOSING
    (dilate r, erode r) fills every concavity narrower than 2r -- what it
    adds is a NOTCH; an OPENING (erode r, dilate r) removes every protrusion
    thinner than 2r -- what it removes is a SPUR. A region is reported when
    it is bigger than a sliver (min_area) and smaller than a feature of the
    letter (max_extent): the crotch of a V fills a sliver and a hairline
    stroke is longer than max_extent, and neither is circled."""
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    rings = [Polygon(P) for P in polys if len(P) > 3]
    rings = [g.buffer(0) for g in rings if g.is_valid or True]
    if not rings: return []
    # even-odd: the glyph is the symmetric difference of its rings
    shape = rings[0]
    for g in rings[1:]: shape = shape.symmetric_difference(g)
    shape = shape.buffer(0)
    if shape.is_empty: return []
    closing = shape.buffer(r, join_style=1).buffer(-r, join_style=1)
    opening = shape.buffer(-r, join_style=1).buffer(r, join_style=1)
    hits = []
    for diff, kind in ((closing.difference(shape), 'notch'), (shape.difference(opening), 'spur')):
        parts = list(diff.geoms) if hasattr(diff, 'geoms') else [diff]
        for g in parts:
            if g.is_empty or g.area < min_area: continue
            x0, y0, x1, y1 = g.bounds
            if max(x1 - x0, y1 - y0) > max_extent: continue
            c = g.centroid
            hits.append((float(c.x), float(c.y), kind, float(g.area)))
    hits.sort(key=lambda h: -h[3]); out = []
    for h in hits:
        if all(math.hypot(h[0]-o[0], h[1]-o[1]) > MERGE for o in out): out.append(h)
    return out


def sheet(ttf, out_png, out_index, label, per_row=6, cap_px=300, chars=None):
    """`chars` sweeps a set other than GLYPHS -- round 368, because the Greek
    is not in the Latin list above and the owner asked for it by name
    ("address awful glitches and hairs in greek letters"). Omitted, the sheet
    is exactly the one this instrument has always drawn."""
    GLYPHS = chars or globals()['GLYPHS']
    f = TTFont(ttf); upm = f['head'].unitsPerEm
    cap = 674.0; scale = cap_px / cap
    fnt = ImageFont.truetype(ttf, int(round(upm * scale)))
    cell_w, cell_h = int(cap_px * 2.35), int(cap_px * 2.05)   # the W is 1.52 cap wide and the italic leans
    rows = (len(GLYPHS) + per_row - 1) // per_row
    W, H = cell_w * per_row + 40, cell_h * rows + 80
    im = Image.new("RGB", (W, H), (255, 255, 255)); d = ImageDraw.Draw(im)
    try: lab = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 22)
    except Exception: lab = ImageFont.load_default()
    d.text((20, 18), f"{label} -- every bump the instrument finds, circled and numbered; mark the ones that need a fix in another colour, and circle what I missed", fill=(60, 60, 60), font=lab)
    index = []; k = 0
    for gi, ch in enumerate(GLYPHS):
        cx0 = 20 + (gi % per_row) * cell_w; cy0 = 60 + (gi // per_row) * cell_h
        base = cy0 + int(cap_px * 1.45); ox = cx0 + int(cap_px * 0.35)
        d.text((cx0 + 8, cy0 + 4), ch, fill=(150, 150, 150), font=lab)
        d.text((ox, base), ch, fill=(0, 0, 0), font=fnt, anchor="ls")
        polys = contours(ttf, ch, f)
        if not polys: continue
        # glyph origin at (ox, base) in the image; design units scale by `scale` (y up)
        lsb = f['hmtx'][f.getBestCmap()[ord(ch)]][1]
        xs = [x for P in polys for x, y in P]; xmin = min(xs)
        for (x, y, kind, val) in bumps(polys):
            k += 1
            px = ox + (x - xmin + lsb) * scale; py = base - y * scale
            r = 22
            d.ellipse([px - r, py - r, px + r, py + r], outline=(220, 30, 30), width=2)
            d.text((px + r + 2, py - r - 4), str(k), fill=(220, 30, 30), font=lab)
            index.append(dict(style=label, glyph=ch, n=k, x=round(x), y=round(y), kind=kind, degrees=round(val, 1)))
    im.save(out_png)
    with open(out_index, "w") as fh: json.dump(index, fh, indent=1)
    return k, im.size


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--roman", required=True); ap.add_argument("--italic", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--chars", default=None, help="sweep these characters instead of the Latin set (e.g. the Greek)")
    ap.add_argument("--tag", default="", help="suffix for the output filenames, so a narrowed sweep does not overwrite the full one")
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    chars = list(a.chars) if a.chars else None
    for sty, p in (("roman", a.roman), ("italic", a.italic)):
        n, size = sheet(p, os.path.join(a.out, f"bumps-{sty}{a.tag}.png"), os.path.join(a.out, f"bumps-{sty}{a.tag}.json"), f"Albo {sty}", chars=chars)
        print(f"{sty}: {n} circles, {size}")


if __name__ == "__main__":
    main()
