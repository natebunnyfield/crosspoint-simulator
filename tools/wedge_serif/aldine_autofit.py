#!/usr/bin/env python3
"""AUTOFIT: measure a letter's target, then solve its dials to hit it.

Owner 2026-09-15: *"be automated for the remaining letters based on the scans
and recent reference italics."*

Rounds 116-128 fitted five letters by hand, and every one of them went the same
way: measure the source, sweep a dial, re-measure, discover a second dial had
moved, sweep again. That loop is mechanical and this runs it.

    python3 aldine_autofit.py --letters aeiou        # measure + solve
    python3 aldine_autofit.py --letters n --dry      # just report the targets
    python3 aldine_autofit.py --letters a --apply    # write the solved defaults

WHERE A TARGET COMES FROM, in order:
  1. a SCAN CROP if one is listed in SOURCES -- the real evidence, hand-located
     because automatic letter-finding failed repeatedly (rounds 115-116) and a
     wrong crop is worse than no crop;
  2. otherwise a REFERENCE ITALIC from refs/ -- Pagella for proportion, and the
     letter is marked DERIVED in the ledger so nobody mistakes it for measured.

WHAT IS MEASURED, and why each survives:
  counter/ink   colour and counter in one number, measured identically on a
                scan and on a rendered glyph
  w/h           proportion, from the OUTLINE on our side -- never a raster
                bbox, which returns the canvas on a white ground (round 119)
  flank, stem   the two stroke widths, x the family stem S. Round 128: two
                ratios agreeing is not two measurements agreeing, and one
                ratio is satisfiable by infinitely many pairs of strokes.
"""
import argparse, math, os, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import ControlBoundsPen

HERE = os.path.dirname(os.path.abspath(__file__))
MACRO = os.path.expanduser('~/Downloads/griffo-macro.png')
VIRGIL = os.path.expanduser('~/Downloads/aldine.png')
TARGET_A = os.path.expanduser(
    '~/.claude/uploads/06bd1159-4703-424c-abda-64842a60926b/508b10cc-image.jpg')
REFS = os.path.join(HERE, 'refs')

# ch -> (image, crop, x-height in px, note).  Hand-located: automatic letter
# finding was tried and failed (template correlation matches every round bowl
# beside a stem), and a wrong crop silently poisons every number below it.
SOURCES = {
    'a': (TARGET_A, (25, 45, 185, 226), 114, "owner's target crop"),
    'e': (MACRO, (592, 342, 634, 406), 57, 'macro, "naues"'),
    'i': (MACRO, (183, 465, 213, 560), 56, 'macro, "rodigium"'),
    'o': (MACRO, (142, 57, 190, 118), 54, 'macro, "udos"'),
    # Located with --segment on the "naues / subitus" line (y 330-420), whose
    # x-height is 57 px off the e at box [8] -- the box the segmenter proposed
    # matches the hand crop that was found the slow way in round 117c, which is
    # what made the rest of this line trustworthy.
    'u': (MACRO, (526, 340, 584, 411), 57, 'macro, "naues"'),
    's': (MACRO, (640, 346, 679, 409), 57, 'macro, "naues,"'),
}
FALLBACK_REF = os.path.join(REFS, 'texgyrepagella-italic.otf')

# The flank/stem pair is only MEANINGFUL for a letter built as a bowl beside a
# stem. On a loop letter -- e o c s -- the left and right runs are two sides of
# the same curve, not two different strokes, and fitting to them drags the
# letter toward a shape it is not. The e solved at an error of 0.28 against a
# "stem" that does not exist before this flag was added.
HAS_STEM = set('abdghikmnpqrtu')

# ch -> [(env var, low, high)] -- the dials autofit is allowed to move.
DIALS = {
    'a': [('ALBO_ALD_A_FLANK', 0.6, 3.0), ('ALBO_ALD_A_STEMW', 1.5, 4.0),
          ('ALBO_ALD_A_BOWL', 0.8, 1.6)],
    'e': [('ALBO_ALD_E_THICK', 0.6, 2.0), ('ALBO_ALD_E_W', 0.5, 0.9)],
    'o': [('ALBO_ALD_O_THICK', 1.0, 2.6), ('ALBO_ALD_O_W', 0.6, 0.95)],
}
BUILD_ENV = dict(ALBO_ITALIC='aldine', FJORD_STEM='66.9', FJORD_CONTRAST='0.892',
                 FJORD_WIDTH='95', FJORD_SLANT='13')
S_OVER_XH = 0.196          # the family's stem as a fraction of the x-height


def _runs(px, W, y, thr):
    out = []; s = None
    for x in range(W):
        d = px[x, y] < thr
        if d and s is None: s = x
        if not d and s is not None: out.append((s, x - 1)); s = None
    if s is not None: out.append((s, W - 1))
    return out


def _counter_and_ink(img, thr):
    bw = img.point(lambda v: 0 if v < thr else 255)
    fl = bw.copy(); ImageDraw.floodfill(fl, (0, 0), 128)
    enc = sum(1 for p in fl.get_flattened_data() if p == 255)
    ink = sum(1 for p in bw.get_flattened_data() if p == 0)
    return enc, ink


def _strokes(img, thr, xh):
    """Median width of the LEFT and RIGHT runs over the rows where the counter
    has split the letter -- the bowl's flank and the stem, in units of S."""
    px = img.load(); W, H = img.size
    L, R = [], []
    for y in range(int(H * 0.22), int(H * 0.82)):
        rr = [r for r in _runs(px, W, y, thr) if r[1] - r[0] + 1 >= max(3, int(W * 0.04))]
        if len(rr) >= 2:
            L.append(rr[0][1] - rr[0][0] + 1); R.append(rr[-1][1] - rr[-1][0] + 1)
    if not L: return None, None
    L.sort(); R.sort()
    return L[len(L) // 2] / xh / S_OVER_XH, R[len(R) // 2] / xh / S_OVER_XH


def measure_source(ch):
    """The target metrics for one letter, from a scan crop or a reference."""
    if ch in SOURCES:
        path, box, xh, note = SOURCES[ch]
        img = Image.open(path).convert('L').crop(box)
        thr = 120
        enc, ink = _counter_and_ink(img, thr)
        flank, stem = _strokes(img, thr, xh) if ch in HAS_STEM else (None, None)
        bw = img.point(lambda v: 0 if v < thr else 255)
        bb = bw.point(lambda v: 255 - v).getbbox()
        return dict(source=f'SCAN {note}', derived=False,
                    counter=(enc / ink if ink else None),
                    wh=((bb[2] - bb[0]) / (bb[3] - bb[1])) if bb else None,
                    flank=flank, stem=stem)
    # no specimen: fall back to a reference italic, and SAY SO
    f = TTFont(FALLBACK_REF); gs = f.getGlyphSet()
    if ch not in gs: return None
    bp = ControlBoundsPen(gs); gs[ch].draw(bp)
    x0, y0, x1, y1 = bp.bounds
    ft = ImageFont.truetype(FALLBACK_REF, 700)
    w = int(ft.getlength(ch)) + 700; a, d = ft.getmetrics()
    im = Image.new('L', (w, a + d + 700), 255)
    ImageDraw.Draw(im).text((350, a + 350), ch, font=ft, fill=0, anchor='ls')
    enc, ink = _counter_and_ink(im, 128)
    return dict(source='REFERENCE Pagella Italic', derived=True,
                counter=(enc / ink if ink else None),
                wh=(x1 - x0) / (y1 - y0), flank=None, stem=None)


def measure_build(ttf, ch):
    f = TTFont(ttf); gs = f.getGlyphSet()
    bp = ControlBoundsPen(gs); gs[ch].draw(bp)
    x0, y0, x1, y1 = bp.bounds
    ft = ImageFont.truetype(ttf, 700); a, d = ft.getmetrics()
    w = int(ft.getlength('o')) + 700
    io = Image.new('L', (w, a + d + 700), 255)
    ImageDraw.Draw(io).text((350, a + 350), 'o', font=ft, fill=0, anchor='ls')
    ob = io.point(lambda v: 255 - v).getbbox(); xh = ob[3] - ob[1]
    w = int(ft.getlength(ch)) + 700
    im = Image.new('L', (w, a + d + 700), 255)
    ImageDraw.Draw(im).text((350, a + 350), ch, font=ft, fill=0, anchor='ls')
    enc, ink = _counter_and_ink(im, 128)
    bb = im.point(lambda v: 255 - v).getbbox()
    flank, stem = _strokes(im.crop(bb), 128, xh) if ch in HAS_STEM else (None, None)
    return dict(counter=(enc / ink if ink else 0), wh=(x1 - x0) / (y1 - y0),
                flank=flank, stem=stem)


def build(ch, overrides, out):
    env = dict(os.environ, **BUILD_ENV, **{k: f'{v:.4f}' for k, v in overrides.items()})
    subprocess.run([sys.executable, '-W', 'ignore', '-m', 'outlines.build', out,
                    '--style', 'Italic', '--only', ch + 'o'],
                   env=env, cwd=HERE, check=True, stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL)
    return os.path.join(out, 'Albo-Italic.ttf')


def err(got, want):
    """Relative error over the metrics the source actually provides."""
    parts = []
    for k in ('counter', 'wh', 'flank', 'stem'):
        if want.get(k) and got.get(k):
            parts.append(abs(got[k] - want[k]) / want[k])
    return sum(parts) / len(parts) if parts else 1e9


def solve(ch, target, rounds=3, samples=5, verbose=True):
    """Coordinate descent over the letter's dials. Each pass walks one dial at
    a time, because the dials INTERACT -- every hand-fitted letter in rounds
    121-128 needed a second dial re-solved after the first moved."""
    dials = DIALS.get(ch)
    if not dials:
        print(f"  {ch}: no dials registered -- nothing to solve"); return None
    cur = {}
    tmp = tempfile.mkdtemp(prefix=f'autofit-{ch}-')
    for name, lo, hi in dials: cur[name] = (lo + hi) / 2
    best = err(measure_build(build(ch, cur, os.path.join(tmp, 'x0')), ch), target)
    for r in range(rounds):
        for i, (name, lo, hi) in enumerate(dials):
            span = (hi - lo) / (2 ** r)
            c = cur[name]
            for k in range(samples):
                v = max(lo, min(hi, c - span / 2 + span * k / (samples - 1)))
                trial = dict(cur, **{name: v})
                e = err(measure_build(build(ch, trial, os.path.join(tmp, f'{r}{i}{k}')), ch), target)
                if e < best - 1e-6:
                    best, cur = e, trial
        if verbose:
            print(f"    pass {r+1}: err {best:.4f}  " +
                  " ".join(f"{n.split('_')[-1]}={cur[n]:.2f}" for n, _, _ in dials))
    return cur, best


def segment(path, y0, y1, thr=120, gap=2, minw=8):
    """Candidate letter boxes on one text line, by column ink profile.

    This exists because hand-hunting crops is what made the scans expensive to
    use: rounds 115-116 spent several passes locating a single `a` and got it
    wrong three times. It does NOT identify letters -- it proposes boxes in
    reading order for a human to label, which is the half a machine can do
    safely. Touching letters come back as one box; that is visible in the
    width and is the signal to split by hand rather than a failure to hide.
    """
    im = Image.open(path).convert('L')
    px = im.load(); W, H = im.size
    cols = [sum(1 for y in range(y0, y1) if px[x, y] < thr) for x in range(W)]
    boxes = []; s_ = None; run = 0
    for x, c in enumerate(cols):
        if c > 0:
            if s_ is None: s_ = x
            run = 0
        elif s_ is not None:
            run += 1
            if run >= gap:
                if x - run - s_ >= minw: boxes.append((s_, x - run))
                s_ = None; run = 0
    if s_ is not None and W - s_ >= minw: boxes.append((s_, W - 1))
    out = []
    for bx0, bx1 in boxes:
        ys = [y for y in range(y0, y1)
              if any(px[x, y] < thr for x in range(bx0, bx1 + 1))]
        if ys: out.append((bx0, min(ys), bx1 + 1, max(ys) + 1))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--letters', default='aeo')
    ap.add_argument('--dry', action='store_true', help='report targets, solve nothing')
    ap.add_argument('--rounds', type=int, default=3)
    ap.add_argument('--segment', help='IMAGE:Y0:Y1 -- propose letter boxes on one line')
    args = ap.parse_args()
    if args.segment:
        path, y0, y1 = args.segment.rsplit(':', 2)
        path = {'macro': MACRO, 'virgil': VIRGIL}.get(path, path)
        for i, b in enumerate(segment(path, int(y0), int(y1))):
            print(f"  [{i:2d}] {b}   w={b[2]-b[0]:3d} h={b[3]-b[1]:3d}")
        return 0
    for ch in args.letters:
        t = measure_source(ch)
        if not t:
            print(f"{ch}: no source and no reference glyph -- skipped"); continue
        mark = ' [DERIVED]' if t['derived'] else ''
        print(f"\n{ch}  <- {t['source']}{mark}")
        print("   target  " + "  ".join(
            f"{k} {t[k]:.3f}" for k in ('counter', 'wh', 'flank', 'stem') if t.get(k)))
        if args.dry: continue
        got = solve(ch, t, rounds=args.rounds)
        if not got: continue
        cur, e = got
        print(f"   solved  err {e:.4f}   " +
              "  ".join(f"{n}={v:.3f}" for n, v in cur.items()))


if __name__ == '__main__':
    sys.exit(main())
