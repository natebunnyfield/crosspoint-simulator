"""THE ALDINE LOWERCASE'S FITTING, re-solved from the reference's own white.

This is the record for `glyphs.aldine.BEARINGS` (round 133, owner 2026-09-16:
"fit the whole lowercase in one pass"). The table in that module is this
script's output; re-run it after ANY outline change there, the way
`BEARING_ADJ` in build.py names the solve that produced it.

    cd tools/wedge_serif
    ALBO_ITALIC=aldine FJORD_STEM=66.9 FJORD_CONTRAST=0.892 FJORD_WIDTH=95 \
      FJORD_SLANT=13 PYTHON_GIL=0 python3 -m outlines.build /tmp/B --style Italic
    PYTHON_GIL=0 python3 -m outlines.cmp.aldine_space /tmp/B/Albo-Italic.ttf
    PYTHON_GIL=0 python3 -m outlines.cmp.aldine_space /tmp/B/Albo-Italic.ttf --gaps
    PYTHON_GIL=0 python3 -m outlines.cmp.aldine_space /tmp/B/Albo-Italic.ttf --ratio

NOTE the solve reads the font it is solving FOR. Run it against a build made
with the CURRENT table and it reports the residual (which should be ~0 and is
the check that the table is still the answer); to re-solve from scratch after
an outline change, build once, run this, paste the table, build again.

WHY WHITE AND NOT THE REFERENCE'S BEARING NUMBERS
-------------------------------------------------
A sidebearing is only meaningful against the edge it is measured from.
Flanker's `r` carries a right bearing of 64 units because its arm reaches 387
units across; Albo's r reaches 285, so the same 64 leaves a visibly larger
hole. Copying the number transfers the reference's bookkeeping and not its
page. `docs/albo-aldine-targets.md` prints those numbers per letter and they
are the right thing to DRAW against; they are not the right thing to fit
against, and the difference is this script.

WHAT IS COMPARABLE BETWEEN TWO ITALICS OF DIFFERENT SLANT
----------------------------------------------------------
The white between two letters at a height y is a horizontal distance at a
fixed y, and a shear leaves every one of those alone. So a pair's gap profile
is the SAME sheared or unsheared and Flanker's compares with Albo's directly,
with no unshearing and no correction for the 1.2 degrees between them.

THE ALGEBRA
-----------
Write glyph X's band ink from its own left extreme: left(y) = lsb + pL(y),
right(y) = lsb + pR(y), advance = lsb + W + rsb. Then for the ordered pair A B

    gap(y) = (adv_A + lsb_B + pL_B(y)) - (lsb_A + pR_A(y))
           = rsb_A + lsb_B + [W_A - pR_A(y)] + pL_B(y)

-- lsb_A cancels, and the white is an affine function of rsb_A + lsb_B over a
pure-shape term. All 676 ordered pairs therefore give a linear least squares
in 52 unknowns, hugely overdetermined, with exactly ONE gauge freedom: adding
c to every lsb and taking c off every rsb changes no pair at all. It is pinned
by splitting the mean shift evenly between the two sides, because the
capitals, figures and punctuation still come from the round-20 fitter and a
one-sided gauge would silently re-space every lowercase-beside-capital pair.

THE CLIP
--------
White is the mean over band rows of min(gap, counter): no gap between two
letters counts as more white than the white INSIDE the letter. Without it the
c's open mouth and the r's shoulder spend their whole depth as inter-letter
space and both letters are fitted far too tight -- which is round 97b's
complaint ("crosses seems way too spaced out") arriving from the other side.
Being the face's OWN counter makes the whole measure scale-free, which is what
lets a narrow face and a wide one be compared at all.

THE SCALE -- the one judgment in the round
-------------------------------------------
Even color means the white BETWEEN letters tracks the white INSIDE them, so
what transfers from a reference is a RATIO, not a number of units. `--ratio`
prints it for every face we hold:

    Flanker Griffo Italic   0.74        Albo Medium, the roman      0.75
    Pagella Italic          0.82        Albo Italic, classic        0.87
    Poetica                 0.86        Albo Italic, aldine BEFORE  0.96
    Cancelleresca           0.92

0.74 is the target -- the face round 132 drew against -- and Albo's own roman
lands on 0.75 from an unrelated direction. The aldine italic stood at 0.96.

NEGATIVE RESULTS, so they are not re-proposed
----------------------------------------------
* COPYING THE DOC'S lsb/rsb RAW was tried first and is wrong for the reason
  above: Albo's band widths run 0.66 to 1.08 of Flanker's letter by letter
  (c 0.66, s 0.69, e 0.70 against l 1.08, d 1.06, a 1.02), so a copied bearing
  lands a different amount of white on nearly every pair.
* KEEPING THE MACHINERY and re-solving `SIDE_FRACTION` / `BEARING_ADJ` was the
  other option in the brief. It cannot express this: those terms fit a letter
  from its side CATEGORY times a capital's bearing, and the four categories
  cannot separate an Albo c (0.66 of the reference) from an Albo o (0.86) --
  they are both `round`. It would also have put the roman's numbers at risk
  for no gain, since the same table is read by every style.
* A FIXED CLIP DEPTH (0.5 x-height for both faces) gives Flanker 0.72 and Albo
  0.96; the self-scaled clip gives 0.74 / 0.96. The ordering is not an artifact
  of the clip, and the roman's 0.75 agrees under the self-scaled one.
* THE n COUNTER ALONE, read at HALF the x-height, is 25 units narrow on every
  arched letter -- that is where the arch springs from the stem. It is read at
  the median of 0.30/0.35/0.40/0.45 instead, and n and o are averaged, or the
  scale swings 0.62 to 0.78 depending on which letter is asked.
* A ZERO MINIMUM-GAP FLOOR -- no two letters touching anywhere in the band --
  was priced and REJECTED (`--floor 0`). It costs 9 units of mean white
  against the relief's 2, puts the fit at 0.80 x counter where the reference
  is 0.74, and opens 23 of the 26 letters, several by more than 20 units. It
  is chasing a criterion the reference does not meet either: Flanker touches
  on 7 band pairs of its own. The floor stays at Flanker's own worst, -22.
* A LOOSER SCALE was laddered (`--scale`). At k = 0.827 (ratio 0.90) the clip
  saturates on most pairs and the solve can only reach the target by pushing
  the few letters that are not saturated -- x lsb +45, y lsb +75, r rsb 177 --
  which is the solver reporting that the target is above what these shapes can
  deliver evenly, not a wider fit. 0.74 is where the residual is clean.
"""
import argparse, math, os, sys

import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, HERE)
import aldine_targets as T                                   # noqa: E402
from fontTools.ttLib import TTFont                           # noqa: E402

XH = 429.0
OVER = 14.0            # outlines.pen.OVER -- the band outlines.build.fit() uses
STEP = 4.0
LC = 'abcdefghijklmnopqrstuvwxyz'
ROWS = [(-OVER + i * STEP) for i in range(int((XH + 2 * OVER) / STEP) + 1)]


class Face(T.Ref):
    """A font in ALBO'S design space. A reference is scaled so its drawn `x`
    top lands on 429 (the doc's own rule); an Albo build is already in those
    units, so it is taken as-is -- scaling it by its own x top would divide the
    whole font by 1.03 for the overshoot and make nothing comparable."""
    def __init__(self, path, slant=None, own_units=False):
        self.path = path; self.label = os.path.basename(path)
        self.font = TTFont(path); self.gs = self.font.getGlyphSet()
        self.cmap = self.font.getBestCmap(); self.upm = self.font['head'].unitsPerEm
        self.angle = -slant if slant is not None else self.font['post'].italicAngle
        if own_units:
            self.k = 1.0
        else:
            self.k = XH / T.bbox(T.flatten(self.gs, self.cmap[ord('x')]))[3]
        self.shear = math.tan(math.radians(-self.angle))
        self.hmtx = self.font['hmtx']


def profile(ref, ch):
    """Band extremes from the contour POINTS -- exactly what
    `outlines.build.fit_aldine` measures, so a table this solves lands where it
    was put -- and the per-row edges from exact cuts, for the white."""
    conts, name = ref.glyph(ch)
    pts = [(x, y) for c in conts for x, y in c if -OVER <= y <= XH + OVER] \
        or [(x, y) for c in conts for x, y in c]
    bl = min(p[0] for p in pts); br = max(p[0] for p in pts)
    L, R = {}, {}
    for y in ROWS:
        r = T.runs_at_y(conts, y)
        if r: L[y] = r[0][0]; R[y] = r[-1][1]
    xs = [x for c in conts for x, y in c]
    adv = ref.advance(name)
    return dict(adv=adv, bl=bl, br=br, W=br - bl, lsb=bl, rsb=adv - br,
                pL={y: L[y] - bl for y in L}, pR={y: R[y] - bl for y in R},
                full=(min(xs), max(xs)))


def counter(ref, ch, fracs=(0.30, 0.35, 0.40, 0.45)):
    """The letter's widest interior gap, median over four mid-band heights.
    NOT 0.50: on every arched letter that is where the arch springs from the
    stem, and it reads the counter ~25 units narrow."""
    conts, _ = ref.glyph(ch); vals = []
    for f in fracs:
        r = T.runs_at_y(conts, XH * f)
        g = [r[i + 1][0] - r[i][1] for i in range(len(r) - 1)]
        if g: vals.append(max(g))
    return float(np.median(vals)) if vals else None


def mean_counter(ref):
    return (counter(ref, 'n') + counter(ref, 'o')) / 2


def shape_terms(P):
    """base[(A,B)][row] -- the part of the gap that is pure shape."""
    out = {}
    for A in LC:
        a = P[A]
        for B in LC:
            b = P[B]
            ys = [y for y in ROWS if y in a['pR'] and y in b['pL']]
            out[(A, B)] = np.array([(a['W'] - a['pR'][y]) + b['pL'][y] for y in ys])
    return out


def whites(P, base, depth, bear=None):
    out = {}
    for A in LC:
        for B in LC:
            l_, r_ = (bear[A][1], bear[B][0]) if bear else (P[A]['rsb'], P[B]['lsb'])
            g = l_ + r_ + base[(A, B)]
            out[(A, B)] = float(np.mean(np.minimum(g, depth))) if g.size else None
    return out


def min_gaps(P, base, bear=None):
    out = {}
    for A in LC:
        for B in LC:
            l_, r_ = (bear[A][1], bear[B][0]) if bear else (P[A]['rsb'], P[B]['lsb'])
            g = l_ + r_ + base[(A, B)]
            out[(A, B)] = float(g.min()) if g.size else None
    return out


def solve(base, target, seed, depth, lam=0.004, iters=60):
    idx = {c: i for i, c in enumerate(LC)}; n = len(LC)
    s0 = np.array([seed[c][1] for c in LC] + [seed[c][0] for c in LC], float)
    x = s0.copy()
    for _ in range(iters):
        rows, rhs = [], []
        for A in LC:
            for B in LC:
                bb = base[(A, B)]
                if bb.size == 0: continue
                s = x[idx[A]] + x[n + idx[B]]
                g = s + bb
                live = g < depth                    # rows the clip is not holding
                if not live.any(): continue
                slope = live.mean()                 # d(white)/d(s)
                cur = float(np.mean(np.minimum(g, depth)))
                r = np.zeros(2 * n); r[idx[A]] = slope; r[n + idx[B]] = slope
                rows.append(r); rhs.append(target[(A, B)] - cur + slope * s)
        M = np.array(rows); y = np.array(rhs)
        R = np.eye(2 * n) * lam * len(rows) ** 0.5
        xn, *_ = np.linalg.lstsq(np.vstack([M, R]), np.concatenate([y, R @ s0]), rcond=None)
        step = np.max(np.abs(xn - x)); x = 0.6 * xn + 0.4 * x
        if step < 0.05: break
    dL = np.mean([x[n + idx[c]] - seed[c][0] for c in LC])   # the gauge, split evenly
    dR = np.mean([x[idx[c]] - seed[c][1] for c in LC])
    c0 = (dR - dL) / 2.0
    for i in range(n):
        x[n + i] += c0; x[i] -= c0
    return {c: (x[n + idx[c]], x[idx[c]]) for c in LC}


def relieve(sol, base, floor, iters=400):
    """OPEN ANY PAIR WHOSE INK ACTUALLY TOUCHES, and only those.

    The least squares above fits the MEAN white and is blind to the minimum: a
    pair can average correctly while an exit stroke and an entry stroke cross
    at one height. Measured on the first solved table by rasterizing each glyph
    of a pair separately and intersecting the ink, 81 of 676 pairs shared ink
    INSIDE the x-height band against Flanker's 7 -- ks, vp, wp, wv, zp, vv, zs.
    Small (about 1.2 px at the 27 px reading size) but a touch is a touch, and
    the lowercase is deliberately unkerned, so nothing downstream will open it:
    `outlines/kern.py`, round 95 -- "The lowercase is NOT kerned."

    The floor is the REFERENCE'S OWN worst band minimum, -22 units, which
    Flanker spends on `rp`; an italic is allowed to interlock, it is not
    allowed to interlock worse than the face it is drawn against. Each
    violation is shared between the two letters, taken as a MAX per letter
    rather than a sum so one bad pair cannot push a letter out twice, and
    iterated. It only ever LOOSENS, so the mean can drift up a little -- which
    is the right trade against a collision, and is reported."""
    b = {c: list(sol[c]) for c in LC}
    for _ in range(iters):
        push = {c: [0.0, 0.0] for c in LC}
        worst = 0.0
        for A in LC:
            for B in LC:
                bb = base[(A, B)]
                if bb.size == 0: continue
                m = float((b[A][1] + b[B][0] + bb).min())
                if m < floor:
                    d = floor - m
                    push[A][1] = max(push[A][1], d / 2); push[B][0] = max(push[B][0], d / 2)
                    worst = max(worst, d)
        if worst < 0.5: break
        for c in LC:
            b[c][0] += push[c][0]; b[c][1] += push[c][1]
    return {c: (b[c][0], b[c][1]) for c in LC}


REF_FILES = [('Flanker Griffo Italic', 'flanker-griffo-italic.otf', None),
             ('Pagella Italic', 'texgyrepagella-italic.otf', None),
             ('Poetica', 'poetica-std-regular.otf', None),
             ('Cancelleresca', 'cancelleresca-bastarda-beta12.otf', None)]


def ratio_of(ref):
    P = {c: profile(ref, c) for c in LC}
    base = shape_terms(P); mc = mean_counter(ref)
    w = np.mean([v for v in whites(P, base, mc).values() if v is not None])
    return mc, float(w), float(w) / mc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('ttf', nargs='?', help='an Albo Italic built with ALBO_ITALIC=aldine')
    ap.add_argument('--slant', type=float, default=13.0)
    ap.add_argument('--lam', type=float, default=0.004)
    ap.add_argument('--scale', type=float, default=None, help='override k (default: counter ratio)')
    ap.add_argument('--floor', type=float, default=None,
                    help="minimum band gap allowed (default: the reference's own worst)")
    ap.add_argument('--gaps', action='store_true', help='the tightest pairs, as a MINIMUM not a mean')
    ap.add_argument('--ratio', action='store_true', help='white / own counter, every face we hold')
    a = ap.parse_args()

    if a.ratio:
        for label, fn, sl in REF_FILES:
            mc, w, r = ratio_of(Face(os.path.join(T.REFS, fn), sl))
            print(f"{label:28} counter {mc:5.0f}  white {w:5.0f}  ratio {r:.2f}")
        if a.ttf:
            mc, w, r = ratio_of(Face(a.ttf, a.slant, own_units=True))
            print(f"{os.path.basename(a.ttf):28} counter {mc:5.0f}  white {w:5.0f}  ratio {r:.2f}")
        return 0
    if not a.ttf:
        ap.error('a TTF is required unless --ratio')

    F = Face(T.PRIMARY); A = Face(a.ttf, a.slant, own_units=True)
    PF = {c: profile(F, c) for c in LC}; PA = {c: profile(A, c) for c in LC}
    bF = shape_terms(PF); bA = shape_terms(PA)
    mcF, mcA = mean_counter(F), mean_counter(A)
    k = a.scale if a.scale else mcA / mcF

    if a.gaps:
        g = min_gaps(PA, bA)
        gf = min_gaps(PF, bF)
        worst = sorted((v, p) for p, v in g.items() if v is not None)[:14]
        wf = sorted((v, p) for p, v in gf.items() if v is not None)[:14]
        print("tightest pairs by MINIMUM gap (a mean cannot see a collision)")
        print("  albo    " + "  ".join(f"{p[0]}{p[1]} {v:.0f}" for v, p in worst))
        print("  flanker " + "  ".join(f"{p[0]}{p[1]} {v:.0f}" for v, p in wf))
        return 0

    wF = whites(PF, bF, mcF)
    target = {p: k * v for p, v in wF.items() if v is not None}
    seed = {c: (PA[c]['lsb'], PA[c]['rsb']) for c in LC}
    w0 = whites(PA, bA, mcA)
    raw = solve(bA, target, seed, mcA, lam=a.lam)
    floor = a.floor if a.floor is not None else \
        min(v for v in min_gaps(PF, bF).values() if v is not None)
    sol = relieve(raw, bA, floor)
    moved = {c: (sol[c][0] - raw[c][0], sol[c][1] - raw[c][1]) for c in LC}
    moved = {c: v for c, v in moved.items() if abs(v[0]) > 0.5 or abs(v[1]) > 0.5}
    w1 = whites(PA, bA, mcA, bear=sol)

    def stat(w):
        e = [w[p] - target[p] for p in target]
        return np.mean([w[p] for p in target]), np.mean(np.abs(e)), np.max(np.abs(e))
    m0, e0, x0 = stat(w0); m1, e1, x1 = stat(w1)
    print(f"mean counter   Flanker {mcF:.0f}   Albo {mcA:.0f}   k = {k:.3f}   (clip = each face's own counter)")
    print(f"mean white     now {m0:6.1f} ({m0/mcA:.2f} x counter)   solved {m1:6.1f} ({m1/mcA:.2f} x counter)"
          f"   Flanker {np.mean(list(wF.values())):.1f} ({np.mean(list(wF.values()))/mcF:.2f} x counter)")
    print(f"mean|err|      now {e0:6.1f}   solved {e1:6.1f}      worst  now {x0:6.1f}   solved {x1:6.1f}")
    g1 = min_gaps(PA, bA, bear=sol)
    print(f"min gap floor  {floor:.0f} (Flanker's own worst band minimum)   "
          f"solved worst {min(v for v in g1.values() if v is not None):.0f}   "
          f"letters opened by the relief: " +
          (', '.join(f"{c} {v[0]:+.0f}/{v[1]:+.0f}" for c, v in sorted(moved.items())) or 'none'))
    print()
    print(f"{'ch':>2} | {'lsb':>5} {'rsb':>5} {'adv':>5} -> {'lsb':>5} {'rsb':>5} {'adv':>5} | "
          f"{'dAdv':>5} | {'ink L':>6} {'ink R':>6} | flanker l/r/adv")
    tbl = {}
    for c in LC:
        l1, r1 = round(sol[c][0]), round(sol[c][1])
        tbl[c] = (l1, r1)
        adv1 = l1 + PA[c]['W'] + r1
        dx = l1 - PA[c]['bl']
        fl, fr = PA[c]['full'][0] + dx, adv1 - (PA[c]['full'][1] + dx)
        print(f"{c:>2} | {PA[c]['lsb']:5.0f} {PA[c]['rsb']:5.0f} {PA[c]['adv']:5.0f} -> "
              f"{l1:5.0f} {r1:5.0f} {adv1:5.0f} | {adv1-PA[c]['adv']:5.0f} | {fl:6.0f} {fr:6.0f} | "
              f"{PF[c]['lsb']:5.0f} {PF[c]['rsb']:5.0f} {PF[c]['adv']:5.0f}")
    print('\nBEARINGS = ' + repr(tbl))
    return 0


if __name__ == '__main__':
    sys.exit(main())
