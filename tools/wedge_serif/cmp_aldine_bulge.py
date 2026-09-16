"""Does a stroke BULGE? -- its width along its length, letter by letter.

Round 134, owner: "there is a pervasive issue of bulging with a and H and
other letters. identify it and fix it based on scans." A stem in the 1501
metal is one width from top to foot (Flanker holds 70 units at every height;
the macro's i reads 6-8 px the whole way down); a bowl's flank is thickest at
the lower left and thins steadily toward the top -- the pen's stress, not a
belly. Bulging is a stroke that is widest in its MIDDLE.

For every letter this unshears the glyph, walks each ink run at 21 heights,
tracks runs into columns (a run is the same stroke as the run above it when
their centres are within a stroke width), and reports per column the width at
the ends and in the middle: BULGE = middle / ends. 1.00 is a straight stem;
Flanker's alphabet sits at 0.95-1.05; a bowed cstem_i reads 1.3+.

    python3 cmp_aldine_bulge.py <ttf> [letters] [--slant 13] [--ref]
"""
import os, sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
PX = 600


def mask(ttf, ch, slant):
    f = ImageFont.truetype(ttf, PX)
    im = Image.new('L', (PX * 3, PX * 3), 255)
    ImageDraw.Draw(im).text((PX, int(PX * 2.0)), ch, font=f, fill=0, anchor='ls')
    base = int(PX * 2.0)
    # unshear about the baseline
    im = im.transform(im.size, Image.AFFINE, (1, math.tan(math.radians(slant)), -math.tan(math.radians(slant)) * base, 0, 1, 0), Image.BILINEAR, fillcolor=255)
    return np.asarray(im) < 128


def columns(ink, n=21):
    iy, ix = np.where(ink)
    if not len(iy): return []
    y0, y1 = iy.min(), iy.max()
    rows = []
    for k in range(n):
        y = int(round(y1 - (k / (n - 1)) * (y1 - y0)))
        r = ink[y]; runs = []; x = 0
        while x < len(r):
            if r[x]:
                j = x
                while j < len(r) and r[j]: j += 1
                runs.append((x, j)); x = j
            else: x += 1
        rows.append((k / (n - 1), runs))
    # track runs into columns
    cols = []
    for f, runs in rows:
        for a, b in runs:
            c = (a + b) / 2; w = b - a
            best = None
            for col in cols:
                pf, pa, pb = col[-1]
                pc = (pa + pb) / 2; pw = pb - pa
                # the same stroke: centre within a width, AND width continuous.
                # A crossbar merging into a stem doubles the run in one row;
                # that is a junction and starts a new column, not a bulge.
                if abs(f - pf) < 0.06 and abs(c - pc) < max(w, pw) * 0.9 and abs(w - pw) < 0.30 * max(w, pw):
                    if best is None or abs(c - pc) < best[0]: best = (abs(c - pc), col)
            if best: best[1].append((f, a, b))
            else: cols.append([(f, a, b)])
    return [c for c in cols if len(c) >= 7]


def bow(col):
    """How far a stroke's CENTRE leaves the straight line between its ends,
    in units of its own width. A bowed stem (cstem_i's CAP_BOW) keeps one
    width the whole way and still reads as a belly, because it is the EDGE the
    eye follows and both edges curve. 0 is straight; Flanker's stems sit under
    0.10; a -0.45 x S bow reads 0.4."""
    pts = [((a + b) / 2, f, b - a) for f, a, b in col]
    (c0, f0, w0), (c1, f1, w1) = pts[0], pts[-1]
    if f1 == f0: return None
    dev = 0.0
    for c, f, w in pts:
        t = (f - f0) / (f1 - f0); line = c0 + (c1 - c0) * t
        dev = max(dev, abs(c - line))
    return dev / max(1.0, (w0 + w1) / 2), f1 - f0


def bulge(col):
    ws = [(f, b - a) for f, a, b in col]
    f0, f1 = ws[0][0], ws[-1][0]; span = f1 - f0
    ends = [w for f, w in ws if f < f0 + span * 0.25 or f > f1 - span * 0.25]
    mid = [w for f, w in ws if f0 + span * 0.35 <= f <= f1 - span * 0.35]
    if not ends or not mid: return None
    mid.sort(); m = mid[len(mid) // 2]          # the median, not the max: one row is not a bulge
    return m / (sum(ends) / len(ends)), span


def report(ttf, letters, slant):
    out = {}
    for ch in letters:
        cols = columns(mask(ttf, ch, slant))
        worst = None; wbow = None
        for col in cols:
            r = bulge(col); b = bow(col)
            if r and r[1] >= 0.35:             # only strokes that run at least 35% of the letter's height
                if worst is None or r[0] > worst: worst = r[0]
            if b and b[1] >= 0.35:
                if wbow is None or b[0] > wbow: wbow = b[0]
        out[ch] = (worst, wbow)
    return out


def main():
    argv = [a for a in sys.argv[1:]]
    slant = 13.0
    if '--slant' in argv: i = argv.index('--slant'); slant = float(argv[i + 1]); del argv[i:i + 2]
    ttf = argv[0]; letters = argv[1] if len(argv) > 1 else 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
    ours = report(ttf, letters, slant)
    ref = report(os.path.join(HERE, 'refs', 'flanker-griffo-italic.otf'), letters, 12.0)
    print('bulge = widest in the middle / mean at the ends;  bow = the centre leaving the chord, x the width')
    print(' ch   bulge albo/flanker   bow albo/flanker')
    flagged = []
    fmt = lambda v: '%.2f' % v if v is not None else ' -- '
    for ch in letters:
        (a, ab), (r, rb) = ours.get(ch, (None, None)), ref.get(ch, (None, None))
        flag = ''
        if a and r and a > max(1.12, r * 1.10): flag += '  BULGES'
        if ab is not None and ab > max(0.15, (rb or 0) * 1.5): flag += '  BOWS'
        if flag: flagged.append(ch)
        print(' %s     %s / %s          %s / %s%s' % (ch, fmt(a), fmt(r), fmt(ab), fmt(rb), flag))
    print('\n%d letter(s) past the reference: %s' % (len(flagged), ''.join(flagged)))


if __name__ == '__main__':
    main()
