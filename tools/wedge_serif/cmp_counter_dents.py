#!/usr/bin/env python3
"""COUNTER DENTS -- ink bulging INTO an enclosed counter, every glyph, any weight.

Owner 2026-09-19: *"for 700 and 900, counters should not have indentations in
their counters."* This is the instrument that finds them. A counter that is
drawn as the OUTER offset inward by the pen's width (primitives.ring,
ring_from) dents where the width swings: the thick sides push in further
than the thin top and bottom, and above the 400 the difference is large
enough that the counter of an 8, g, o, 6, a, q or @ becomes an hourglass with
a dent at 3 and at 9 o'clock. The 400s have none of these; the 700 has dents
of 7-12 units and the 900 of 12-18 (measured 2026-09-19, round 270).

The measure: for each enclosed counter of a built font, the counter's convex
hull minus the counter itself. Every piece of that difference is ink inside
the hull; a piece is a DENT when its area is at least --min-area (60) and it
is at least --min-thick (6) units thick at its thickest, so a facet of a
polygonised curve (a sliver a fraction of a unit thick) is never counted.
Designed non-convex counters -- the ampersand's lower loop at the 400, the
italic 9's tail join -- show up too, and are read as what they are.

    PYTHON_GIL=0 python3 cmp_counter_dents.py A.ttf [B.ttf ...] [--chars ...] [--out DIR]

Prints one line per font (glyph:area/thickness, worst first) and, with --out,
writes a picture per font of the worst twelve glyphs at 0.5 px/unit with the
dents in red -- a vector render at that size, nothing resampled.
"""
import argparse, collections, os, string, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cmp_aldine_glitch as G
from shapely.geometry import Polygon
from shapely.ops import unary_union

DEFAULT_CHARS = string.ascii_letters + string.digits + '&@'


def thickness(pc):
    lo, hi = 0.0, 80.0
    for _ in range(14):
        mid = (lo + hi) / 2
        if pc.buffer(-mid).is_empty: hi = mid
        else: lo = mid
    return 2 * lo


def dents(path, chars, min_area=60.0, min_thick=6.0):
    """yields (ch, outers, holes, [dent polygons], [(area, thick)])"""
    for ch, conts, note in G.from_ttf(path, chars):
        outers = [Polygon(p).buffer(0) for p, h in conts if not h and len(p) > 2]
        holes = [Polygon(p).buffer(0) for p, h in conts if h and len(p) > 2]
        found, nums = [], []
        for hole in holes:
            if hole.is_empty or hole.area < 200: continue
            bul = hole.convex_hull.difference(hole)
            parts = list(bul.geoms) if bul.geom_type == 'MultiPolygon' else ([bul] if not bul.is_empty else [])
            for pc in parts:
                if pc.area < min_area: continue
                th = thickness(pc)
                if th < min_thick: continue
                found.append(pc); nums.append((pc.area, th))
        if found:
            yield ch, outers, holes, found, nums


def picture(items, label, path, scale=0.5):
    from PIL import Image, ImageDraw
    tiles = []
    for ch, outers, holes, found in items:
        g = unary_union(outers).difference(unary_union(holes)) if holes else unary_union(outers)
        x0, y0, x1, y1 = g.bounds; W = int((x1 - x0) * scale) + 12; H = int((y1 - y0) * scale) + 12
        im = Image.new('RGB', (W, H), (255, 255, 255)); d = ImageDraw.Draw(im)
        def T(p): return [((x - x0) * scale + 6, (y1 - y) * scale + 6) for x, y in p]
        def draw_poly(poly, fill):
            d.polygon(T(poly.exterior.coords), fill=fill)
            for r in poly.interiors: d.polygon(T(r.coords), fill=(255, 255, 255))
        for poly in (list(g.geoms) if g.geom_type == 'MultiPolygon' else [g]): draw_poly(poly, (0, 0, 0))
        for n in found:
            for poly in (list(n.geoms) if n.geom_type == 'MultiPolygon' else [n]): draw_poly(poly, (220, 30, 30))
        tiles.append(im)
    W = sum(t.width for t in tiles) + 16 * (len(tiles) + 1); H = max(t.height for t in tiles) + 36
    out = Image.new('RGB', (W, H), (255, 255, 255)); x = 16
    for t in tiles: out.paste(t, (x, 12)); x += t.width + 16
    ImageDraw.Draw(out).text((4, H - 14), f"{label}: {' '.join(c for c, *_ in items)} -- red = ink inside the counter's convex hull; {scale:g} px/unit, vector render", fill=(0, 0, 190))
    out.save(path); return out.size


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('fonts', nargs='+')
    ap.add_argument('--chars', default=DEFAULT_CHARS)
    ap.add_argument('--min-area', type=float, default=60.0)
    ap.add_argument('--min-thick', type=float, default=6.0)
    ap.add_argument('--out', default=None, help='write a picture per font here')
    ap.add_argument('--top', type=int, default=12)
    a = ap.parse_args()
    total = 0
    for path in a.fonts:
        label = os.path.basename(path).replace('.ttf', '')
        items = list(dents(path, a.chars, a.min_area, a.min_thick))
        rows = sorted(((ch, ar, th) for ch, *_, nums in items for ar, th in nums), key=lambda r: -r[2])
        total += len(rows)
        print(f"-- {label}: {len(rows)} dent(s) in {len(items)} glyph(s)")
        if rows: print('   ' + ' '.join(f"{c}:{ar:.0f}/{th:.1f}" for c, ar, th in rows[:30]))
        if a.out and items:
            os.makedirs(a.out, exist_ok=True)
            worst = sorted(items, key=lambda it: -max(t for _, t in it[4]))[:a.top]
            for part in range(0, len(worst), 6):
                chunk = [(ch, o, h, f) for ch, o, h, f, _ in worst[part:part + 6]]
                p = os.path.join(a.out, f"{label}-dents-{part // 6 + 1}.png")
                print('   wrote', p, picture(chunk, label, p))
    sys.exit(1 if total else 0)


if __name__ == '__main__':
    main()
