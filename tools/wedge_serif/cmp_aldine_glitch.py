#!/usr/bin/env python3
"""THE GLITCH GATE -- every glyph's outline swept for the union artifacts this
font has actually shipped, not for anything a designer might dislike.

Owner 2026-09-16: *"subagent to cleanup every letter of small errant glitches."*

WHY A GATE AND NOT A PARAGRAPH. Every defect in the list below was found by eye
at 500 px, after it had shipped, and each one is invisible at reading size --
which is exactly the shape of mistake a comment cannot prevent. The letters are
unions of strokes and rings under shapely; a union artifact is a geometric fact
about the output, so it can be measured, and anything measurable that can go
silent belongs in `tests/run_all.sh`'s sense of a gate rather than in prose.

THE DEFECT CLASSES, and the measure each one answers to:

  CRACK     two pieces that should merge leave a 1-3 unit white line inside the
            ink. That is a HOLE whose mean width (2 x area / perimeter) is far
            under a hairline. The K's arm carried one for three rounds.
  SPECK     a stray hole of a few hundred square units where the drawing asks
            for none -- the `a` lost a round to `PR.ring_from()`, which returns
            a solid that ALREADY HAS ITS COUNTER, being given a second one.
  NEEDLE    a contour a few units wide and tens of units long, where two
            nearly-parallel edges cross. Same mean-width measure, on an
            EXTERIOR.
  CRUMB     an exterior contour too small to be a piece of a letter.
            `geom.contours` already drops anything under 40 units^2; this
            catches the 40..CRUMB_AREA band it lets through.
  PINCH     two points far apart ALONG a contour but close together in the
            plane: a crack that has not opened yet, a fracture where two
            strokes butt rather than overlap, or the neck of a spur. Measured
            as the minimum distance between contour points at least
            PINCH_GAP apart in index.
  SPLIT     the glyph's ink falls into more pieces than the drawing has. An
            exterior count over the expected one is a fracture that has already
            separated, or a fragment left behind by a stroke that missed.
  INVALID   shapely could not make a valid polygon of it; a self-touching ring
            renders as a pinch or a filled counter.

WHERE THE THRESHOLDS COME FROM. The pen at the shipping dials (FJORD_CONTRAST
0.80, ALBO_ALD_CON 5.00) has a stem of ~84 units and a hairline of ~17-20
(stem / 5, plus the 1.2-unit ink spread on each side). So:

  HAIR_W = 12    a real stroke is never thinner than this. Measured over the
                 whole font at the shipping dials the thinnest legitimate
                 feature is the o's hairline at ~19 and a wedge serif's tip
                 run, which is a CORNER and not a run, so it does not enter a
                 mean-width average. 12 sits below every real stroke and above
                 every crack found by eye (1-3 units).
  CRUMB_AREA  = 900   30x30 units, a fifth of a wedge serif's area. Nothing a
                 letter is made of is smaller.
  SPECK_AREA  = 1200  the smallest real counter in the font is the e's eye;
                 measure it before lowering this (see --census).
  PINCH_D     = 3.0   a white line thinner than this does not survive
                 rasterisation at reading size, so it is not worth a round; one
                 wider than this is what the eye caught on the K.
  PINCH_GAP   = 8     points closer than 8 apart in index are neighbours on the
                 same edge, whose distance is ~11 units by construction
                 (geom.SPACING) and says nothing.

USAGE

    PYTHON_GIL=0 python3 cmp_aldine_glitch.py            # the gate: non-zero on a finding
    PYTHON_GIL=0 python3 cmp_aldine_glitch.py --census   # every contour, for calibration
    PYTHON_GIL=0 python3 cmp_aldine_glitch.py --chars abcK
    PYTHON_GIL=0 python3 cmp_aldine_glitch.py --ttf out/Albo-Italic.ttf   # post-CUT

The default reads the DESIGNED outlines (pre-cut, exact floats), because that
is where the cause of a union artifact lives. `--ttf` reads a built file
instead, which is the shipped configuration: the cutter is itself a plausible
source of glitches and a defect that exists only after cutting is exactly the
kind this font has shipped before.

THE DEFAULT SCOPE IS THE LETTERS AND THE FIGURES, and it is GREEN at
2026-09-16. `--all` also sweeps the punctuation, the symbols and the dingbats,
and it is NOT green -- these are the ten it reports, all of them looked at and
none of them fixed, so the next pass does not re-find them:

  ¡ …  ¨ ˝    SPLIT, and correct: a mark made of two or three separate pieces.
              They are not in MULTI because a punctuation mark's piece count is
              its drawing's business and pinning it here would be a second copy
              of that drawing.
  ¥ ♣ ♧ ♕     CRACK, 6.6 to 10.8 units wide, where two bars or two outline
              strokes cross. Same class as the beta's, fixable the same way,
              left because none of them is a letter.
  √           CRACK 7.5 -- the tick's corner against its bar.
  ♤           CRACK 5.6 -- the spade's foot against its body.
  ✔           CRACK 2.0, the worst in the font: the heavy tick is ONE stroke
              with a 100-degree corner, and a stroke that wide folds its inner
              edge through itself there. `stroke(pieces=True)` is the
              documented cure (see primitives.stroke) and would fix every one
              of these; it is not applied here because it changes the outline
              of every glyph drawn with `_s`.
  U+00A0      INVALID empty geometry -- a no-break SPACE, which is correct.

Also found and deliberately NOT fixed, because they are not union artifacts:
the W's crown reaches past the arms as a thin point (owner ruling 2026-09-13,
"lower and reduce the protuberance"), the N's diagonal leaves a ~9-unit beard
where it enters the right stem, and the shared ascender HEAD leaves a 3-unit
nick in its top edge on b d h i j k l and a step on its right. Measurements are
in the commit messages.
"""
import argparse, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))

# ---------------------------------------------------------------- thresholds
HAIR_W = 12.0        # units: below this, a run of ink is not a stroke
CRUMB_AREA = 900.0   # units^2: an exterior smaller than this is not a letter part
SPECK_AREA = 1200.0  # units^2: a hole smaller than this is not a counter
PINCH_D = 3.0        # units: a white line narrower than this is not worth a round
PINCH_GAP = 8        # contour indices: nearer than this is the same edge

# Glyphs whose drawing legitimately produces more than one ink island. EVERY
# row here was looked at at 300-600 px before it was written down, because the
# whole value of the SPLIT check is that a row added on a guess silences
# exactly the defect it is for -- the long s shipped a loose dash in its left
# sidebearing and the Omega two loose feet, and both were found by this check
# being noisy rather than by anyone looking.
MULTI = {
    'i': 2, 'j': 2,                     # the dot rides free
    ':': 2, ';': 2, '!': 2, '?': 2, '=': 2, '"': 2, '%': 3,
    'i̇': 2,
    'Ĳ': 2, 'ĳ': 4,           # IJ, ij -- two letters, and ij's two dots
    'ﬁ': 2, 'ﬃ': 2,           # fi, ffi -- the i's dot
    '¦': 2, '«': 2, '»': 2, '±': 2, '¿': 2,
    '©': 2, '®': 2,           # the ring and the letter inside it
    '¼': 3, '½': 3, '¾': 3, '÷': 3, '‰': 5,
    '™': 2, '≈': 2, '≤': 2, '≥': 2,
    # ROUND 385: the pieces and suits were redrawn as one silhouette each, so
    # the old allowances (the spade's foot, the queen's arms and finial) are
    # gone -- an allowance left above the drawing's count would hide a real
    # fracture. The white knight's eye is a dot inside its outline.
    '♘': 2,
    'Ω': 1,                        # NOT 3 -- see g_Omega, its feet were adrift
    # round 379: the Theta's bar floats inside the O (all four reference
    # Greeks draw it so -- traced, the bar's run at mid-height stands clear of
    # both walls), and the Xi is three bars with no stem. Looked at at 180 px.
    'Θ': 2, 'Ξ': 3,
}


def mean_width(area, perim):
    """2 x area / perimeter -- the mean width of the band a closed curve
    encloses. Exact for a long rectangle, and that is the shape every one of
    these defects has."""
    return 2.0 * area / perim if perim > 1e-9 else 0.0


def pinch(pts, gap=PINCH_GAP, dmin=PINCH_D):
    """The closest approach between two points of one contour that are at
    least `gap` apart along it. O(n^2) on point lists of a few hundred, which
    is nothing beside the build."""
    n = len(pts)
    best = (1e9, -1, -1)
    for i in range(n):
        xi, yi = pts[i]
        for j in range(i + gap, n - (gap if i < gap else 0)):
            dx = pts[j][0] - xi; dy = pts[j][1] - yi
            d = dx * dx + dy * dy
            if d < best[0]:
                best = (d, i, j)
    return (math.sqrt(best[0]), best[1], best[2]) if best[1] >= 0 else (1e9, -1, -1)


def contour_stats(pts):
    a = 0.0; p = 0.0
    n = len(pts)
    for i in range(n):
        x0, y0 = pts[i]; x1, y1 = pts[(i + 1) % n]
        a += x0 * y1 - x1 * y0
        p += math.hypot(x1 - x0, y1 - y0)
    return abs(a) / 2.0, p


def check(ch, conts, census=False):
    """conts: [(points, is_hole)]. Returns a list of finding strings."""
    out = []
    ext = [c for c in conts if not c[1]]
    holes = [c for c in conts if c[1]]
    want = MULTI.get(ch, 1)
    if len(ext) > want:
        areas = sorted((contour_stats(p)[0] for p, _ in ext), reverse=True)
        out.append(f"SPLIT   {len(ext)} ink islands, expected {want}; areas {['%.0f' % a for a in areas]}")
    for pts, hole in conts:
        area, perim = contour_stats(pts)
        mw = mean_width(area, perim)
        kind = 'hole' if hole else 'ext'
        if census:
            out.append(f"  census {kind:4s} area {area:9.0f}  perim {perim:8.0f}  meanw {mw:7.2f}  n {len(pts):4d}")
            continue
        if hole:
            if mw < HAIR_W:
                out.append(f"CRACK   hole mean width {mw:.2f} < {HAIR_W} (area {area:.0f}, perim {perim:.0f})")
            elif area < SPECK_AREA:
                out.append(f"SPECK   hole area {area:.0f} < {SPECK_AREA} (mean width {mw:.2f})")
        else:
            if area < CRUMB_AREA:
                out.append(f"CRUMB   ink island area {area:.0f} < {CRUMB_AREA} (mean width {mw:.2f})")
            elif mw < HAIR_W:
                out.append(f"NEEDLE  ink mean width {mw:.2f} < {HAIR_W} (area {area:.0f}, perim {perim:.0f})")
        d, i, j = pinch(pts)
        if d < PINCH_D and not census:
            out.append(f"PINCH   {kind} closes to {d:.2f} units between pts {i} and {j} "
                       f"at ({pts[i][0]:.0f},{pts[i][1]:.0f})")
    return out


# ---------------------------------------------------------------- sources
def from_design(chars):
    """The designed shapely geometry, before the cut. yields (ch, conts)."""
    import outlines.build as B
    from outlines import geom
    W = B.solve_widths()
    for ch in chars:
        if ch not in B.GLYPHS: continue
        g = B.draw(ch, W)
        if g.is_empty:
            yield ch, None, "INVALID empty geometry"
            continue
        note = None if g.is_valid else "INVALID shapely: " + str(g.is_valid_reason() if hasattr(g, 'is_valid_reason') else '')
        yield ch, geom.contours(g), note


def from_ttf(path, chars):
    """The SHIPPED outline: quadratic contours flattened back to points."""
    from fontTools.ttLib import TTFont
    from fontTools.pens.recordingPen import DecomposingRecordingPen
    from outlines import geom
    f = TTFont(path)
    cmap = f.getBestCmap(); gs = f.getGlyphSet()
    for ch in chars:
        gn = cmap.get(ord(ch))
        if gn is None: continue
        rp = DecomposingRecordingPen(gs)
        gs[gn].draw(rp)
        conts = []; cur = []
        for op, args in rp.value:
            if op == 'moveTo': cur = [args[0]]
            elif op == 'lineTo': cur.append(args[0])
            elif op == 'qCurveTo':
                pts = list(args)
                on = pts[-1]; offs = pts[:-1]
                p0 = cur[-1]
                # TrueType's implied on-curve points
                exp = []
                for k, c in enumerate(offs):
                    if k + 1 < len(offs):
                        nx = offs[k + 1]
                        exp.append((c, ((c[0] + nx[0]) / 2, (c[1] + nx[1]) / 2)))
                    else:
                        exp.append((c, on))
                for c, e in exp:
                    cur.extend(geom.quad(p0, c, e, spacing=6.0)[1:]); p0 = e
            elif op == 'curveTo':
                p0 = cur[-1]
                cur.extend(geom.cubic(p0, args[0], args[1], args[2], spacing=6.0)[1:])
            elif op == 'closePath' or op == 'endPath':
                if len(cur) >= 3:
                    if math.dist(cur[0], cur[-1]) < 1e-6: cur = cur[:-1]
                    conts.append((cur, geom.signed_area(cur) < 0))
                cur = []
        yield ch, conts, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--chars', default=None, help='restrict to these characters')
    ap.add_argument('--ttf', default=None, help='sweep a built font instead of the design')
    ap.add_argument('--census', action='store_true', help='print every contour, no pass/fail')
    ap.add_argument('--all', action='store_true', help='sweep every glyph, not just the letters and figures')
    a = ap.parse_args()

    import outlines.build as B
    letters = [c for c in B.CHARS if c.isalpha() or c in '0123456789']
    chars = list(a.chars) if a.chars else (list(B.CHARS) if a.all else letters)

    src = from_ttf(a.ttf, chars) if a.ttf else from_design(chars)
    bad = 0; seen = 0
    for ch, conts, note in src:
        seen += 1
        rows = []
        if note: rows.append(note)
        if conts: rows += check(ch, conts, census=a.census)
        if rows:
            name = ch if ch.isprintable() and not ch.isspace() else repr(ch)
            print(f"{name}  U+{ord(ch):04X}")
            for r in rows: print("   ", r)
            if not a.census: bad += 1
    print(f"\n{seen} glyphs swept, {bad} with findings"
          f"{' (census mode: nothing is a failure)' if a.census else ''}")
    return 1 if (bad and not a.census) else 0


if __name__ == '__main__':
    sys.exit(main())
