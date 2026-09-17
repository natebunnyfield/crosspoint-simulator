#!/usr/bin/env python3
"""Which glyphs are still their own mirror -- the ledger behind round 167's
hand cuts, as a script rather than as a paragraph.

    cd tools/wedge_serif && PYTHON_GIL=0 python3 cmp_hand_symmetry.py
    PYTHON_GIL=0 python3 cmp_hand_symmetry.py --chars EFT0123456789
    PYTHON_GIL=0 python3 cmp_hand_symmetry.py --hand 0      # the pre-press tree
    PYTHON_GIL=0 python3 cmp_hand_symmetry.py --parts       # the SUB-PART numbers
    PYTHON_GIL=0 python3 cmp_hand_symmetry.py --cuts        # THE GATE, below

WIDEN `--chars` BEFORE QUOTING A RANKING FROM IT. The default set is the
thirteen glyphs round 167 cut, and a "tightest in the alphabet" claim read off
THAT set is not a claim about the alphabet. It was made once and was wrong:
swept over A-Z plus the figures, the five tightest are T 1.22, D 1.51, 8 1.59,
0 1.70, I 1.76 -- the untouched D and I are interleaved with the cut ones, and
the H at 11.06 that an `EFT0-9`-plus-H run makes look like "the next one" is
nine points away and has five letters in front of it.

AND IT IS ALSO A GATE, under `--cuts`, which is the half that earns its keep.
`_press` SNAPS each cut onto the nearest point of the contour it is cutting and
DROPS it if that point is further away than the cut's own reach -- which is what
keeps a cut aimed at the 8's lower counter out of its upper one, and is also a
silent no-op waiting to happen. A mistyped fraction in a table then draws
nothing, raises nothing, and fails no other gate in this repo: the render simply
comes back a shade closer to the round-166 letter and nobody can see the
difference at 13 pt. `--cuts` walks all 42 rows, prints how far each snap moved
its nominal point, and exits non-zero if any row found no edge within reach.
Run it after editing any HAND table. Measured 2026-09-16 at the shipped tables:
42 cuts, 0 dropped, snaps moving 0.3 to 6.2 units against reaches of 32 to 50.

WHAT IT DOES NOT CATCH, and this is the honest half: a fraction mistyped by less
than a full reach still finds an edge, still fires at FULL depth, and lands on
whatever edge happened to be nearest -- a cut in the wrong place rather than no
cut, which no exit code can tell from a cut in the right one. Adversarial review
named that gap. The mitigation is the SNAP column: every shipped row moves 0.3
to 6.2 units against reaches of 32 to 50, so anything past half its reach is
flagged LOOSE here, because a row that had to travel that far was probably not
written for the edge it found.

WHY IT EXISTS. Owner 2026-09-16: *"make E F T X handcut"* and *"make italic
numerals handcut"*. The instruction is only worth obeying where there is a
symmetry to break, and "this letter looks symmetrical" is not a measurement --
so this is the measurement. For each glyph it reports the SYMMETRIC DIFFERENCE
between the drawn ink and its own mirror, about the vertical and the horizontal
axis of its own bounding box, as a percentage of its ink. A glyph that is its
own mirror to within a percent or two is a glyph a punchcutter never made.

It is a REPORT, not a gate: there is no pass mark, because plenty of letters
are legitimately near-symmetric (the roman O, the H, the X's own construction)
and a threshold would either fire on those or never fire at all. It prints, and
a round decides.

Taken on the UNSHEARED drawing, before `build.draw`'s ink spread and before the
13-degree shear, because that is the space the tables in `glyphs/aldine.py` are
written in. The builder's solved width multipliers ARE applied (`solve_widths`),
since a figure's horizontal multiplier is re-solved every build and the drawing
without it is not the drawing that ships.

What it said on the round-166 tree, which is the reason round 167 exists, and
what the press then did to each (`--hand 0` against the module default):

    whole glyph        T  0.22 -> 1.22     0  0.49 / 0.50 -> 1.70 / 1.71
                       8  0.59 -> 1.59
    sub-parts          T  the arm alone         0.43 -> 1.84
    (`--parts`)        9  the bowl alone        0.69 -> 1.75
                       6  the bowl alone        2.58 -> 3.68
                       E  top bar vs bottom     4.81 -> 5.84

-- and the residue in the T and in the rings before the press is
`primitives.life()`'s +-6% on the two wedges and nothing else.

FOUR OF THOSE ARE SUB-PART MEASUREMENTS and the whole-glyph pass cannot produce
them. They were taken by hand in a scratch harness first, and an adversarial
pass correctly pointed out that a ledger you cannot re-run is not a ledger.
`--parts` runs them now: each is a horizontal band of the glyph mirrored about
that band's own axis, except the E's, which flips the bottom band onto the top
one, registers the two by their bounding boxes and differences them.

A SUB-PART NUMBER IS ONLY AS FIXED AS ITS BAND, and `PARTS` below is the band.
The E's first went into the record as 5.77 from a scratch harness reading a
slightly taller top band than the one committed here, which reads 4.81. Neither
is wrong; the point of putting the bands in the file is that the next pass gets
the same number as this one. Quote what the script prints.

After round 167's press at its shipped depth: T 1.22, 0 1.70 / 1.71, 8 1.59.
A factor of three to five, and all three are STILL the tightest mirrors in the
alphabet -- the next is the H at 11.06. THAT IS NOT THE DIAL BEING TOO SHALLOW,
and the arithmetic says why: the symmetric difference of a pressed glyph runs
about 2 x mean edge offset x perimeter, so putting the T on the H's 11 would
need a mean offset of 1.83 units and a deepest cut near 22 -- a third of a
stem. A T, a 0 and an 8 are near-symmetric letters and an Aldine 0 is an oval;
the number this work is held to is the EDGE OFFSET against the Q's 6 units, the
R's 5.0 and the X's 4.5, which lives beside `_HAND` in `glyphs/aldine.py`.
"""
import math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.environ.setdefault("ALBO_ITALIC", "aldine")
os.environ.setdefault("FJORD_SLANT", "13")
os.environ.setdefault("FJORD_CONTRAST", "0.80")
os.environ.setdefault("FJORD_WIDTH", "95")
os.environ.setdefault("FJORD_CUT", "0")
if "--hand" in sys.argv:
    os.environ["ALBO_ALD_HAND"] = sys.argv[sys.argv.index("--hand") + 1]

import shapely.affinity as AF
from outlines import build as B, geom
from outlines import primitives as PR
from outlines.glyphs import GLYPHS

CHARS = "EFT0123456789"
if "--chars" in sys.argv:
    CHARS = sys.argv[sys.argv.index("--chars") + 1]


def drawn(ch, W):
    """The glyph as its own function returns it: unsheared, no ink spread."""
    c = B.ctx(ch, W)
    if B.isfig(ch):
        import latin
        top, bot = latin.FIG_BOX[ch]
        c["figH"] = (top - bot) * B.C
    PR.begin_glyph(ch)
    return GLYPHS[ch](c)


# The four sub-part measurements, as bands of the glyph in CAP fractions (the
# T, the E) or in absolute design units (the 6's and the 9's bowls, which sit
# in figure boxes rather than on the cap line). Each was hand-located once, on
# the round-166 drawing, and the bands are deliberately generous: they select
# the part, they do not trim it to a number.
PARTS = [
    ('T', 'the arm alone, about its own vertical axis',      'mirror_x', ('cap', 0.89, 1.02)),
    ('6', 'the bowl alone, about its own vertical axis',     'mirror_x', ('abs', -30.0, 330.0)),
    ('9', 'the bowl alone, about its own vertical axis',     'mirror_x', ('abs', 330.0, 700.0)),
    ('E', 'the top bar against the bottom bar, registered',  'bars',     ('cap', 0.89, 1.02)),
]
E_BOT_BAND = ('cap', -0.02, 0.11)   # the E's bottom bar, the half the 'bars' row flips


def _band(g, ch, spec, C):
    from shapely.geometry import box
    kind, lo, hi = spec
    if kind == 'cap':
        lo, hi = lo * C, hi * C
    return g.intersection(box(-4000.0, lo, 4000.0, hi))


def parts_ledger():
    """The four sub-part numbers this file's header quotes."""
    import shapely.affinity as AF
    W = B.solve_widths()
    C = B.C
    print("HAND = %s" % os.environ.get("ALBO_ALD_HAND", "1.0 (the module default)"))
    print()
    print(" glyph  part                                             sym-diff   of ink")
    for ch, what, how, spec in PARTS:
        g = drawn(ch, W)
        sub = _band(g, ch, spec, C)
        if sub.is_empty:
            print("   %s    %-46s   BAND EMPTY" % (ch, what)); continue
        if how == 'mirror_x':
            x0, _, x1, _ = sub.bounds
            m = AF.scale(sub, xfact=-1, yfact=1, origin=((x0 + x1) / 2, 0))
            d = sub.symmetric_difference(m).area
            ref = sub.area
        else:                                   # the E: flip the bottom onto the top
            bot = _band(g, ch, E_BOT_BAND, C)
            m = AF.scale(bot, xfact=1, yfact=-1, origin=(0, 0))
            tb, bb = sub.bounds, m.bounds
            m = AF.translate(m, tb[0] - bb[0], tb[1] - bb[1])
            d = sub.symmetric_difference(m).area
            ref = sub.area
        print("   %s    %-46s   %7.2f%%   %8.0f" % (ch, what, 100 * d / ref, ref))
    print()
    print("(the whole-glyph pass -- this script with no flag -- cannot produce these;")
    print(" it only ever mirrors a glyph about its own bounding box.)")


def cuts_gate():
    """Every row of every HAND table must find an edge inside its own reach.

    A row that does not is DROPPED by `_press` and draws nothing -- silently,
    which is the whole reason this is a gate and not a note. Exits non-zero on
    the first drop."""
    from shapely.geometry.polygon import orient
    from outlines.glyphs import aldine as AL
    if not AL.ON:
        sys.exit("--cuts needs the Aldine italic: ALBO_ITALIC=aldine (it is set "
                 "by default when this script is run directly)")
    tabs = {'E': AL.CAP_E_HAND, 'F': AL.CAP_F_HAND, 'T': AL.CAP_T_HAND}
    tabs.update(AL.FIG_HAND)
    W = B.solve_widths()
    from outlines.glyphs import caps_straight as CS, figures as FG
    FIG = {'0': 'g_zero', '1': 'g_one', '2': 'g_two', '3': 'g_three', '4': 'g_four',
           '5': 'g_five', '6': 'g_six', '7': 'g_seven', '8': 'g_eight', '9': 'g_nine'}
    dropped = total = 0
    loosest = []
    print(" glyph  cut (fx, fy, where)        depth   snap moves it   its reach")
    for ch, tab in sorted(tabs.items()):
        c = B.ctx(ch, W)
        if B.isfig(ch):
            import latin
            top, bot = latin.FIG_BOX[ch]; c["figH"] = (top - bot) * B.C
        PR.begin_glyph(ch)
        fn = {'E': CS.g_E, 'F': CS.g_F, 'T': CS.g_T}.get(ch) or getattr(FG, FIG[ch])
        g = fn(c)
        x0, y0, x1, y1 = geom.bbox(g); w, h = x1 - x0, y1 - y0
        polys = [g] if g.geom_type == 'Polygon' else list(g.geoms)
        for fx, fy, rS, d, where in tab:
            total += 1
            cx, cy = x0 + w * fx, y0 + h * fy; r = rS * AL.S
            best = float('inf')
            for p in polys:
                p = orient(p, 1.0)
                rings = ([p.exterior] if where in ('ext', 'both') else [])
                rings += (list(p.interiors) if where in ('int', 'both') else [])
                for rg in rings:
                    for q in rg.coords:
                        best = min(best, math.hypot(q[0] - cx, q[1] - cy))
            ok = best <= r
            dropped += not ok
            loose = ok and best > r / 2
            loosest.append((best / r, ch, fx, fy))
            note = "" if ok else "   <-- DROPPED, draws nothing"
            if loose:
                note = "   <-- LOOSE: snapped past half its reach"
            print("   %s    (%.3f, %.3f, %-4s)    %+5.1f   %11.1f   %9.1f%s" % (
                ch, fx, fy, where, d, best, r, note))
    loosest.sort(reverse=True)
    print("\n%d cuts, %d dropped. Loosest snap: %s (%.3f, %.3f) at %.0f%% of its "
          "reach." % (total, dropped, loosest[0][1], loosest[0][2], loosest[0][3],
                      100 * loosest[0][0]))
    if dropped:
        sys.exit("%d cut(s) found no edge within reach -- they draw NOTHING. "
                 "Fix the fraction or widen the reach." % dropped)


def main():
    if "--cuts" in sys.argv:
        cuts_gate(); return
    if "--parts" in sys.argv:
        parts_ledger(); return
    W = B.solve_widths()
    print("HAND = %s" % os.environ.get("ALBO_ALD_HAND", "1.0 (the module default)"))
    print()
    print(" ch     ink area   mirror about x   mirror about y   holes")
    worst = []
    for ch in CHARS:
        if ch not in GLYPHS:
            continue
        g = drawn(ch, W)
        x0, y0, x1, y1 = geom.bbox(g)
        mx = AF.scale(g, xfact=-1, yfact=1, origin=((x0 + x1) / 2, 0))
        my = AF.scale(g, xfact=1, yfact=-1, origin=(0, (y0 + y1) / 2))
        sx = 100 * g.symmetric_difference(mx).area / g.area
        sy = 100 * g.symmetric_difference(my).area / g.area
        nh = sum(len(p.interiors) for p in
                 ([g] if g.geom_type == 'Polygon' else list(g.geoms)))
        print("  %s   %9.0f       %7.2f%%        %7.2f%%      %d" % (ch, g.area, sx, sy, nh))
        worst.append((min(sx, sy), ch))
    worst.sort()
    print()
    # A THRESHOLD, not a top-5. `worst[:5]` printed whatever was least-worst in
    # whatever `--chars` happened to be, under a banner asserting a property --
    # so on the default set it announced the E at 20.87% and the 6 at 32.56% as
    # letters "a punchcutter made none of", which is the opposite of true. Five
    # per cent is the line: below it a glyph is its own mirror to within the
    # ink spread, above it the two halves are visibly different halves.
    tight = [(v, c) for v, c in worst if v < 5.0]
    print("under 5% -- its own mirror, which a punchcutter's is not: " +
          (", ".join("%s %.2f%%" % (c, v) for v, c in tight) if tight else "none"))
    if len(CHARS) < 20:
        print("NOTE: only %d glyphs swept. Do NOT read a ranking against 'the "
              "alphabet' off this -- widen --chars first." % len(CHARS))


if __name__ == "__main__":
    main()
