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
    'a': (0.844, 0.945, 'ref',    0.83, "Flanker Griffo Italic a (the crop's 0.344 is an ink-spread artifact)"),
    'e': (0.203, None,  'C 5.00', 1.12, 'griffo-macro.png, "naues", 54px xh'),
    'i': (None,  None,  'D 9.26', 0.64, 'griffo-macro.png, "rodigium"'),
    'o': (0.617, 0.759, 'D 9.26', 1.63, 'griffo-macro.png, "udos", 54px xh'),
    'u': (None,  None,  'D 9.26', 0.64, 'pitch 0.52 xh from three stem pairs'),
    'y': (None,  None,  'D 9.26', 0.64, 'DERIVED - no y in any scan we hold'),
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
               FJORD_CONTRAST='0.892', FJORD_WIDTH='95', FJORD_SLANT='13')
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
