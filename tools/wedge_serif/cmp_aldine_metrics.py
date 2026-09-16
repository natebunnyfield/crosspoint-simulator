#!/usr/bin/env python3
"""THE ALDINE LEDGER: every letter's measured target, and what it builds at.

Owner 2026-09-15: *"keep track of metrics that work for different letters
including line width."* The reason this is a SCRIPT and not a table in a doc:
the numbers drift the moment any shared dial moves, and a table in prose does
not notice. Contrast arm D moved the o from 0.624 to 0.823 against a target of
0.617 and nothing said so for a round.

    python3 cmp_aldine_metrics.py            # build and check every letter
    python3 cmp_aldine_metrics.py --only ae  # just these

Each row is a measurement off a Griffo scan, with the source named. A letter
with no measured target (no specimen on any page we have) is listed as DERIVED
and checked only for self-consistency.
"""
import argparse, math, os, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import ControlBoundsPen

# ch: (counter/ink, w/h, contrast arm, line width x S, source)
TARGETS = {
    # The a's w/h target is RETIRED, not failed. The 0.891 measured on the
    # owner's crop includes a full-length exit, and he then halved the tail
    # ("trim up a tail to be half as long"), which legitimately narrows the
    # letter to ~0.69. Keeping the old number would print a permanent false
    # failure -- which is how a ledger stops being read.
    # ROUND 132: the a's counter target moves to the REFERENCE VECTOR. The
    # 0.344 came off the owner's crop -- a 160 x 181 px photograph whose ink
    # spread closes the counter, and which aldine_targets.py marks SUSPECT
    # (1.55 xh of ink, 26 components; docs/albo-aldine-targets.md section 6).
    # Flanker Griffo's a measures 0.844 by this same flood fill, Pagella's
    # 0.672, Poetica's 0.598; the Petrarch page's a's are open like Flanker's.
    # Owner 2026-09-15: match the referenced vector or bitmap -- so Flanker.
    # ROUND 133: the a is a d WITH A SHORT ASCENDER (owner 2026-09-16, from
    # the scan) -- its stem now clears the x-line by 96 units under the same
    # head the b d p wear. Flanker's a has NO ascender, so its 0.844 counter
    # and 0.945 w/h stopped describing this letter the moment that ruling
    # landed: both numbers are taken over the whole glyph, and this glyph is
    # taller than the one they were measured on. Retargeted to the ruled
    # drawing. The ladder behind the ruling is in the round 133 log: at 150
    # units the a and the d are the same letter at 27 px, which is the wall.
    # ROUND 137: the owner drew this a himself in the editor, and it is a
    # wider letter -- his head reaches 210 units left where the old one
    # reached 76, so the ink box grows with it. Fourth retarget of this row,
    # same rule as the other three: a target describes a drawing.
    # ROUND 151: RETARGETED TO THE REFERENCE, and this one is the LAST of the
    # retargets rather than another of them -- the row stops describing a
    # drawing and starts describing a font we still have.
    #
    # 0.330 / 0.839 described round 146's teardrop-counter a, and the owner
    # withdrew that letter the day after it was measured (*"forget about the
    # tear drop counter"*). It then stood as the target through round 147's
    # traced a and failed it at +60% / -30%, which is the row working; but it
    # was never a number any reference holds. Measured with THIS SCRIPT'S OWN
    # `measure()` on the three reference faces, 2026-09-16:
    #
    #             counter/ink   w/h
    #   Flanker      0.844      0.945     <- the target, below
    #   Pagella      0.672      0.815
    #   Poetica      0.598      0.739
    #   round 146 target 0.330  0.839     <- 2.6x off the nearest reference
    #
    # The a is drawn against Flanker now (the d's bowl, the family's stem, no
    # construction of its own -- outlines/glyphs/aldine.py, round 151), so it
    # takes Flanker's own numbers, which is the SAME rule the o's row already
    # states one line down. It builds at 0.828 / 0.973: -1.9% and +3.0%.
    'a': (0.844, 0.945, 'ref',    0.83, "Flanker's own a, measured by this script (round 146's 0.330 described a withdrawn drawing)"),
    'e': (0.203, None,  'C 5.00', 1.12, 'griffo-macro.png, "naues", 54px xh'),
    'i': (None,  None,  'B 5.00', 0.64, 'griffo-macro.png, "rodigium"'),
    # ROUND 132 RULING: the o's counter target follows its weight to the
    # reference (owner 2026-09-16). 0.617 is what the PRINTED page measures --
    # ink spread closing the counter -- and holding it made the o's ring 104
    # units against the reference's 66-71. The o now measures 0.91 of the n's
    # mean ink width, where Flanker measures 0.90. The w/h is unchanged: the
    # scan's proportion was never the disputed number.
    'o': (1.034, 0.759, 'ref',    1.08, "Flanker's ring weight (the scan's 0.617 is the page's ink spread)"),
    'u': (None,  None,  'B 5.00', 0.64, 'pitch 0.52 xh from three stem pairs'),
    'y': (None,  None,  'B 5.00', 0.64, 'DERIVED - no y in any scan we hold'),
}
TOL = 0.10   # a letter is off when it misses its target by more than this


def measure(path, ch, size=700):
    f = TTFont(path); gs = f.getGlyphSet()
    bp = ControlBoundsPen(gs); gs[ch].draw(bp)
    x0, y0, x1, y1 = bp.bounds
    ft = ImageFont.truetype(path, size)
    w = int(ft.getlength(ch)) + size; a, d = ft.getmetrics()
    im = Image.new('L', (w, a + d + size), 255)
    ImageDraw.Draw(im).text((size // 2, a + size // 2), ch, font=ft, fill=0, anchor='ls')
    bw = im.point(lambda v: 0 if v < 128 else 255)
    fl = bw.copy(); ImageDraw.floodfill(fl, (0, 0), 128)
    enc = sum(1 for p in fl.get_flattened_data() if p == 255)
    ink = sum(1 for p in bw.get_flattened_data() if p == 0)
    return (enc / ink if ink else 0), (x1 - x0) / (y1 - y0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', default=''.join(TARGETS))
    args = ap.parse_args()
    out = tempfile.mkdtemp(prefix='aldine-metrics-')
    env = dict(os.environ, ALBO_ITALIC='aldine', FJORD_STEM='66.9',
               FJORD_CONTRAST='0.80', FJORD_WIDTH='95', FJORD_SLANT='13')
    subprocess.run([sys.executable, '-W', 'ignore', '-m', 'outlines.build', out,
                    '--style', 'Italic'], env=env, check=True,
                   stdout=subprocess.DEVNULL)
    ttf = os.path.join(out, 'Albo-Italic.ttf')
    print(f"{'ch':>2} {'arm':>8} {'line w':>7} {'counter/ink':>22} {'w/h':>18}   source")
    bad = 0
    for ch in args.only:
        if ch not in TARGETS: continue
        tc, tw, arm, lw, src = TARGETS[ch]
        r, wh = measure(ttf, ch)
        def cell(got, want):
            if want is None: return f"{got:8.3f}  (—)      "
            off = (got - want) / want
            flag = '  OFF' if abs(off) > TOL else ''
            return f"{got:8.3f}  ({want:.3f}, {off:+.0%}){flag}"
        c1, c2 = cell(r, tc), cell(wh, tw)
        if 'OFF' in c1 + c2: bad += 1
        print(f"{ch:>2} {arm:>8} {lw:7.2f} {c1:>22} {c2:>18}   {src}")
    print(f"\n{bad} letter(s) outside {TOL:.0%} of a measured target.")
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
