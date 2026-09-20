"""ROUND 291 -- THE HAIRS, THE FRACTURES AND THE STAIRCASES, AS A GATE.

Owner 2026-09-19, on large renders of common words: *"bold italic 700 has
errors and glitches and fractures and hairs."* He was right and
`cmp_aldine_glitch.py` could not see it -- that gate sweeps for islands,
cracks and splits at a RASTER, and on the BoldItalic it reported 23 findings
of which every one was a symbol or a punctuation mark. The letters came back
clean and the `s` and the `g` were not clean.

WHAT THIS MEASURES, which no other tool here does: the CONTOUR's own point
stream, before any raster. Three faults live there and each of them reads as
a hair or a fracture once the outline is rounded to the em grid and filled:

  REVERSAL -- a vertex where the outline doubles back on itself by more than
    `--turn` degrees. On a drawn letter the sharpest thing is a wedge serif's
    tip or a hairline terminal, and those measure 149-162 degrees on this
    face's own m n r; a reversal past that is the contour walking out and
    back along the same line, which fills as a one-unit spike.

  HAIR -- a reversal sharper than `--hair-turn` whose shorter arm is under
    `--hair-len` units. That is the fault's real signature: a drawn corner
    has two long arms, a spike has one arm a unit or two long. Reported
    apart from the plain reversal count because the two want different
    verdicts -- a sharp corner between two long arms is a decision, a sharp
    corner on a two-unit arm is an accident.

  DEGENERATE DENSITY -- the fraction of segments under `--short` units. This
    is the one that found round 291's bug. A contour built at this project's
    `geom.SPACING` of 11 units should carry almost none: the family's c e n o
    read 0-6%. The `s` read 66% and the `g` 63%, because `geom.close_corners`
    puts a 24-segment-per-quadrant round buffer fan on EVERY vertex of an
    already-dense polyline and the erosion brings the fan back as hundreds of
    sub-unit segments. Sub-unit segments are invisible in design space and
    become the stepped, faceted edges the owner saw as soon as the exporter
    rounds them to integers -- and they defeat `geom.fit_curves`, whose
    corner test reads noise on a 0.3-unit segment as a corner, so the letter
    exports as a raw polygon with no curves in it at all.

Coincident points are collapsed BEFORE the angles are taken. They must be:
a zero-length segment has no direction, so a spike sitting next to a
duplicate point reads as 90 degrees or as nothing at all depending on which
way the arithmetic falls, and both readings are wrong. The duplicates are
counted and reported in their own column instead, because a run of them is
itself a symptom.

    PYTHON_GIL=0 python3 cmp_contour_hairs.py FONT.ttf [FONT2.ttf ...]
    PYTHON_GIL=0 python3 cmp_contour_hairs.py F.ttf --glyphs s,g,m --verbose

Exit 1 on any REVERSAL past `--turn` (default 165 degrees), on any HAIR, or
on any glyph whose short-segment fraction exceeds `--max-short` (default
0.25). Exit 0 otherwise. `--turn 200` disables the reversal arm,
`--max-short 1.1` the density arm, for a one-off look at the other.
"""
import argparse, math, os, string, sys

from fontTools.ttLib import TTFont


def contour_points(font, name):
    """[[(x, y), ...], ...] -- one list per contour, in font units, with
    coincident neighbors collapsed and the closing duplicate dropped. Every
    point is taken, on-curve and off: a control point is part of the stream
    the exporter wrote and a spike in it is a spike in the filled shape."""
    glyf = font["glyf"]
    g = glyf[name]
    if g.numberOfContours in (0, None) or g.isComposite():
        return []
    coords, end_pts, _flags = g.getCoordinates(glyf)
    out = []
    start = 0
    for e in end_pts:
        raw = [(float(coords[i][0]), float(coords[i][1])) for i in range(start, e + 1)]
        start = e + 1
        pts = []
        for p in raw:
            if not pts or math.dist(pts[-1], p) > 1e-9:
                pts.append(p)
        while len(pts) > 1 and math.dist(pts[0], pts[-1]) < 1e-9:
            pts.pop()
        out.append((pts, len(raw) - len(pts)))
    return out


def turn(a, b, c):
    """Degrees the direction changes at b. 0 is straight on, 180 is a
    complete reversal."""
    v1 = (b[0] - a[0], b[1] - a[1])
    v2 = (c[0] - b[0], c[1] - b[1])
    l1 = math.hypot(*v1)
    l2 = math.hypot(*v2)
    if l1 < 1e-9 or l2 < 1e-9:
        return 0.0
    d = max(-1.0, min(1.0, (v1[0] * v2[0] + v1[1] * v2[1]) / (l1 * l2)))
    return math.degrees(math.acos(d))


def measure(font, name, short=2.0, rev_turn=165.0, hair_turn=150.0, hair_len=8.0):
    segs = dups = shorts = 0
    revs = []
    hairs = []
    worst = (0.0, None, 0.0, 0.0)
    for pts, nd in contour_points(font, name):
        dups += nd
        n = len(pts)
        if n < 3:
            continue
        lens = [math.dist(pts[i], pts[(i + 1) % n]) for i in range(n)]
        segs += n
        shorts += sum(1 for d in lens if d < short)
        for i in range(n):
            t = turn(pts[(i - 1) % n], pts[i], pts[(i + 1) % n])
            arm_in, arm_out = lens[(i - 1) % n], lens[i]
            if t > worst[0]:
                worst = (t, pts[i], arm_in, arm_out)
            if t > rev_turn:
                revs.append((t, pts[i], arm_in, arm_out))
            if t > hair_turn and min(arm_in, arm_out) < hair_len:
                hairs.append((t, pts[i], arm_in, arm_out))
    return dict(segs=segs, dups=dups, shorts=shorts, revs=revs, hairs=hairs, worst=worst,
                frac=(shorts / segs if segs else 0.0))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("fonts", nargs="+")
    ap.add_argument("--glyphs", default="", help="comma-separated glyph names; default every glyph")
    ap.add_argument("--letters", action="store_true",
                    help="sweep only the Latin letters -- the arm that is held green; the symbols and "
                         "marks carry findings of their own (the same territory cmp_aldine_glitch reports)")
    ap.add_argument("--short", type=float, default=2.0, help="a segment under this many units is degenerate")
    ap.add_argument("--turn", type=float, default=165.0, help="a reversal past this many degrees fails")
    ap.add_argument("--hair-turn", type=float, default=150.0)
    ap.add_argument("--hair-len", type=float, default=8.0, help="a reversal with an arm under this is a hair")
    ap.add_argument("--max-short", type=float, default=0.25, help="failing fraction of degenerate segments")
    ap.add_argument("--verbose", action="store_true", help="a row for every glyph, not only the faults")
    a = ap.parse_args()

    bad = 0
    for path in a.fonts:
        f = TTFont(path)
        upem = f["head"].unitsPerEm
        k = upem / 1000.0                      # thresholds are quoted per 1000-unit em
        if a.glyphs:
            names = a.glyphs.split(",")
        elif a.letters:
            names = [c for c in string.ascii_letters if c in f.getGlyphOrder()]
        else:
            names = f.getGlyphOrder()
        rows = []
        for name in names:
            if name not in f.getGlyphOrder():
                print("  no such glyph:", name)
                bad += 1
                continue
            m = measure(f, name, short=a.short * k, rev_turn=a.turn,
                        hair_turn=a.hair_turn, hair_len=a.hair_len * k)
            if not m["segs"]:
                continue
            rows.append((name, m))
        faults = [(n, m) for n, m in rows if m["revs"] or m["hairs"] or m["frac"] > a.max_short]
        print(f"== {os.path.basename(path)}  {len(rows)} glyphs swept, {len(faults)} with findings")
        show = rows if a.verbose else faults
        for name, m in sorted(show, key=lambda r: (-len(r[1]["hairs"]), -r[1]["frac"])):
            tags = []
            if m["hairs"]:
                tags.append(f"HAIR x{len(m['hairs'])}")
            if m["revs"]:
                tags.append(f"REVERSAL x{len(m['revs'])}")
            if m["frac"] > a.max_short:
                tags.append(f"DENSE {m['frac'] * 100:.0f}%")
            w = m["worst"]
            print(f"  {name:<12} segs {m['segs']:>5}  short<{a.short:g} {m['shorts']:>5}"
                  f" ({m['frac'] * 100:>3.0f}%)  dup {m['dups']:>4}"
                  f"  worst turn {w[0]:>5.1f} deg at {None if w[1] is None else (round(w[1][0]), round(w[1][1]))}"
                  f" arms {w[2]:.1f}/{w[3]:.1f}   {'  '.join(tags)}")
            for t, p, ai, ao in (m["hairs"] or m["revs"])[:6]:
                print(f"       -> {t:.1f} deg at ({p[0]:.0f}, {p[1]:.0f}) arms {ai:.2f} / {ao:.2f}")
        bad += len(faults)
    print("FAIL" if bad else "PASS")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
