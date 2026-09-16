"""Measure a reference italic letter by letter, in ALBO'S UNSHEARED DESIGN
SPACE, so a letter can be drawn against numbers instead of a feeling.

WHAT IT DOES, in four steps (the same four the doc's method section names):

  1. flatten the reference glyph's outline (fontTools, cubics and quadratics
     both, implied on-curve points included);
  2. scale so the reference's own x-height -- the bbox top of its `x` -- lands
     on Albo's 429 units, so every number below is directly comparable with
     `pen.DESIGN` (stem S=84, cap 674, asc 770, desc 280);
  3. UNSHEAR about the baseline by the font's `post.italicAngle`, because Albo
     is drawn upright and sheared at build time -- a reference measured in its
     own sheared space describes a letter nobody here can draw;
  4. cut the outline with horizontal and vertical lines and report the INK RUNS.

WHY RUNS AND NOT A SHAPE DESCRIPTION.  A run is the one measurement that is
the same thing on a rendered outline and on a scan of a printed page, and it
is the measurement a designer can act on: "the stem is 70 units wide at half
the x-height" is a drawable instruction, "the bowl is rather firm" is not.

THE CUTS ARE EXACT, NOT RASTERED.  A horizontal run at height y is computed
from the edge/line intersections directly, so the numbers are not quantized to
a pixel grid and a 6-unit hairline is still 6 units and not 5 or 7.  The raster
exists only for `--png`.

STROKE THICKNESS IS DERIVED FROM BOTH CUTS.  A horizontal run across a
diagonal or a curve is wider than the stroke actually is.  For a straight band
of true (perpendicular) width t at angle 0 from vertical, a horizontal cut
gives w = t/cos 0 and a vertical cut gives h = t/sin 0, so

        1/w^2 + 1/h^2 = 1/t^2   ->   t = w*h / sqrt(w^2 + h^2)

which recovers the true width from the two cuts with no raster and no
skeleton.  It is exact on a straight band and close on a slow curve; it is
WRONG at a junction, where both cuts see two strokes at once.  So a value is
reported only when it passes BOTH of the filters in `_axis_samples`: it must
agree within 10% with the largest disc that fits at the run's midpoint (a
junction can inflate the cut formula and cannot inflate a disc), and the run
must be locally PARALLEL -- one overlapping run of the same width and the same
derived t 15 units either side.  Those two together are what "clearly a single
stroke" means here, and each was added after a wrong number shipped: the disc
check stopped the H reporting a 414-unit stem, the parallelism check stopped
the n reporting its arch's spring as its stem.

Both axes are scanned, because a horizontal cut cannot measure a horizontal
stroke.  And the SUMMARY to quote is the MEDIAN: `thickest` and `thinnest` name
a place on the letter, not the letter's stroke.

SCANS.  Where `aldine_autofit.SOURCES` has a hand-located crop of the real
printed page, that bitmap is the true target and the outline is only a
stand-in.  The crop is upscaled so its x-height is 429 px = 429 units and Otsu
binarizes it there.  **The shear cannot be removed from a bitmap reliably** --
the printed angle is not declared anywhere, it varies letter to letter in a
chancery hand, and at 54-75 px of x-height an estimate off a single stem is
worth about +/-2 degrees.  So the scan is measured SHEARED, which is honest
because of an accident of geometry worth knowing:

  * a horizontal run's WIDTH is shear-invariant (x' = x + y*tan leaves every
    horizontal distance at a fixed y alone), so scan stroke widths are real;
  * a run's x POSITION and the overall bbox WIDTH are not -- the bbox is
    inflated by roughly (ink height)*tan(angle);
  * the derived t is within ~2% for a near-vertical stroke (a sheared band's
    perpendicular width is t*cos 12 = 0.978 t) and exact for a horizontal one.

Run it (the doc `docs/albo-aldine-targets.md` is built from the first four):
    PYTHON_GIL=0 python3 aldine_targets.py --md abc --per 4 --group
    PYTHON_GIL=0 python3 aldine_targets.py --md ABC --per 5 --group --brief
    PYTHON_GIL=0 python3 aldine_targets.py --second     # Flanker vs Pagella
    PYTHON_GIL=0 python3 aldine_targets.py --scans      # the crops alone
    PYTHON_GIL=0 python3 aldine_targets.py --slant      # declared vs drawn
    PYTHON_GIL=0 python3 aldine_targets.py --chars abo --png DIR
    PYTHON_GIL=0 python3 aldine_targets.py             # the long text report
"""
import argparse, math, os

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import DecomposingRecordingPen

HERE = os.path.dirname(os.path.abspath(__file__))
REFS = os.path.join(HERE, 'refs')
PRIMARY = os.path.join(REFS, 'flanker-griffo-italic.otf')
SECOND = os.path.join(REFS, 'texgyrepagella-italic.otf')

# Albo's design grid -- `pen.DESIGN`, round 65.  Everything below is in these
# units so a number here can be typed straight into a glyph program.
XH = 429.0
STEM_S = 84.0
CAP = 674.0
ASC = 770.0
DESC = 280.0

LC = 'abcdefghijklmnopqrstuvwxyz'
UC = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

# Sample heights.  Lowercase in fractions of the x-height (negatives are the
# descender, over 1.0 the ascender); capitals in fractions of the cap height,
# plus two descender rows for J and Q.  Rows with no ink are dropped, so a
# letter prints only the rows it actually has.
LADDER_LC = [-0.55, -0.30, -0.12, 0.03, 0.10, 0.25, 0.50, 0.75, 0.90, 0.97,
             1.15, 1.40, 1.65]
LADDER_UC = [0.03, 0.15, 0.35, 0.50, 0.65, 0.85, 0.97]
LADDER_UC_DESC = [-0.30, -0.12]          # in x-height units, for J and Q
COLS = [0.10, 0.25, 0.50, 0.75, 0.90]    # fractions of the ink width


# --------------------------------------------------------------------------
# outline -> contours


def _bez(p0, pts, n):
    """de Casteljau over any degree, n segments, p0 excluded."""
    out = []
    ctrl = [p0] + list(pts)
    for i in range(1, n + 1):
        t = i / n
        q = ctrl
        while len(q) > 1:
            q = [(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
                 for a, b in zip(q, q[1:])]
        out.append(q[0])
    return out


def _quads(p0, pts, n):
    """TrueType qCurveTo with IMPLIED on-curve points between consecutive
    off-curve controls -- the half-way rule.  The `None` terminator (a contour
    made only of off-curve points, legal in TrueType) is handled by starting
    from the midpoint of the last and first control, which is where such a
    contour's implied start actually is; the prototype dropped the None and
    silently promoted a control point to an on-curve point."""
    out = []
    if pts and pts[-1] is None:
        ctrls = list(pts[:-1])
        if not ctrls:
            return out
        start = ((ctrls[-1][0] + ctrls[0][0]) / 2.0,
                 (ctrls[-1][1] + ctrls[0][1]) / 2.0)
        p0 = start
        end = start
    else:
        ctrls, end = list(pts[:-1]), pts[-1]
    for i, c in enumerate(ctrls):
        nxt = ctrls[i + 1] if i + 1 < len(ctrls) else end
        on = nxt if i + 1 >= len(ctrls) else ((c[0] + nxt[0]) / 2.0,
                                              (c[1] + nxt[1]) / 2.0)
        out += _bez(p0, [c, on], max(2, n // 2))
        p0 = on
    return out


def flatten(glyphset, name, n=48):
    """Every contour of a glyph as a closed polyline.  Components are
    decomposed, so this works on a composite as well as on CFF."""
    pen = DecomposingRecordingPen(glyphset)
    glyphset[name].draw(pen)
    contours, cur = [], []

    def close():
        if len(cur) >= 3:
            contours.append(list(cur))

    for op, args in pen.value:
        if op == 'moveTo':
            close(); cur = [args[0]]
        elif op == 'lineTo':
            cur.append(args[0])
        elif op == 'curveTo':
            cur += _bez(cur[-1], args, n)
        elif op == 'qCurveTo':
            cur += _quads(cur[-1] if cur else (0, 0), args, n)
            if not cur:
                cur = list(_quads((0, 0), args, n))
        elif op in ('closePath', 'endPath'):
            close(); cur = []
    close()
    return contours


def transform(contours, k, shear):
    """Scale to Albo units, then unshear about the baseline: x' = x - y*tan."""
    return [[((x * k) - (y * k) * shear, y * k) for x, y in c] for c in contours]


def bbox(contours):
    xs = [p[0] for c in contours for p in c]
    ys = [p[1] for c in contours for p in c]
    return min(xs), min(ys), max(xs), max(ys)


# --------------------------------------------------------------------------
# exact cuts


def _cut(contours, v, axis):
    """Even-odd ink intervals along the line (axis=0: horizontal cut at y=v,
    axis=1: vertical cut at x=v).  Exact: the crossings of the flattened edges
    with the line, sorted and paired.  A vertex exactly on the line is nudged
    off it rather than counted twice, which is the classic scanline bug."""
    a, b = (1, 0) if axis == 0 else (0, 1)
    xs = []
    for c in contours:
        pts = c + [c[0]]
        for p, q in zip(pts, pts[1:]):
            p0, p1 = p[a], q[a]
            if p0 == p1:
                continue
            lo, hi = (p0, p1) if p0 < p1 else (p1, p0)
            if not (lo <= v < hi):
                continue
            t = (v - p0) / (p1 - p0)
            xs.append(p[b] + t * (q[b] - p[b]))
    xs.sort()
    return [(xs[i], xs[i + 1]) for i in range(0, len(xs) - 1, 2)]


def runs_at_y(contours, y):
    return _cut(contours, y, 0)


def runs_at_x(contours, x):
    return _cut(contours, x, 1)


def perp_width(contours, y, run):
    """True (perpendicular) stroke width at a run, from the horizontal run's
    width and the vertical run through its midpoint -- see the module
    docstring.  Returns (t, w, h) or None when the midpoint finds no vertical
    run (a cusp, or a run so thin the midpoint falls outside the ink)."""
    x0, x1 = run
    w = x1 - x0
    xm = (x0 + x1) / 2.0
    vr = [r for r in runs_at_x(contours, xm) if r[0] - 1e-6 <= y <= r[1] + 1e-6]
    if not vr or w <= 0:
        return None
    h = max(r[1] - r[0] for r in vr)
    if h <= 0:
        return None
    return (w * h / math.hypot(w, h), w, h)


def segments(contours):
    """The flattened outline as four arrays, for point-to-outline distance."""
    ax, ay, bx, by = [], [], [], []
    for c in contours:
        pts = c + [c[0]]
        for p, q in zip(pts, pts[1:]):
            ax.append(p[0]); ay.append(p[1]); bx.append(q[0]); by.append(q[1])
    return (np.array(ax), np.array(ay), np.array(bx), np.array(by))


def inscribed(segs, px, py):
    """Distance from an interior point to the nearest point of the outline --
    i.e. the radius of the largest disc that fits there.  2*this is the
    stroke's width when the point is at the stroke's centre, and it is the one
    quantity that CANNOT be inflated by a junction: a disc at the middle of a
    crossbar-meets-stem is still only as wide as the narrower stroke."""
    ax, ay, bx, by = segs
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    L2 = np.where(L2 == 0, 1e-9, L2)
    t = np.clip(((px - ax) * dx + (py - ay) * dy) / L2, 0.0, 1.0)
    qx, qy = ax + t * dx, ay + t * dy
    return float(np.sqrt(np.min((px - qx) ** 2 + (py - qy) ** 2)))


def _perp(contours, v, run, axis):
    """Perpendicular width at a run on either axis; returns (t, a, b) where a
    is the run's own length and b the crossing run's."""
    a = run[1] - run[0]
    mid = (run[0] + run[1]) / 2.0
    cross = [r for r in _cut(contours, mid, 1 - axis)
             if r[0] - 1e-6 <= v <= r[1] + 1e-6]
    if not cross or a <= 0:
        return None
    b = max(r[1] - r[0] for r in cross)
    if b <= 0:
        return None
    return (a * b / math.hypot(a, b), a, b)


def _axis_samples(contours, segs, lo, hi, axis, step, tol, delta):
    out = []
    v = lo
    while v <= hi:
        for r in _cut(contours, v, axis):
            m = _perp(contours, v, r, axis)
            if not m:
                continue
            t, a, b = m
            mid = (r[0] + r[1]) / 2.0
            px, py = (mid, v) if axis == 0 else (v, mid)
            disc = 2.0 * inscribed(segs, px, py)
            # THE TWO MEASUREMENTS MUST AGREE.  The cut formula is exact on a
            # band and inflates at a junction; the disc cannot inflate but is
            # short wherever the run's midpoint is off the band's centre.  A
            # sample where they disagree is not a single stroke, and that one
            # test is what stopped the H reporting a 414-unit stem (a vertical
            # cut down the stem crossed with the crossbar's own run) and the t
            # reporting 233 at the bar.
            if abs(disc - t) > tol * max(disc, t, 1.0):
                continue
            ok = True
            for d in (-delta, delta):
                nb = [q for q in _cut(contours, v + d, axis)
                      if q[1] > r[0] and q[0] < r[1]]
                if len(nb) != 1:
                    ok = False; break
                m2 = _perp(contours, v + d, nb[0], axis)
                a2 = nb[0][1] - nb[0][0]
                if not m2 or abs(m2[0] - t) > tol * max(t, 1.0) \
                        or abs(a2 - a) > tol * max(a, 1.0):
                    ok = False; break
            if ok:
                out.append((disc, v, mid, a, b, axis))
        v += step
    return out


def stroke_samples(contours, segs, y0, y1, x0=None, x1=None,
                   step=6.0, tol=0.10, delta=15.0):
    """Every cut that is CLEARLY A SINGLE STROKE, as
    (t, cut position, run midpoint, own run, crossing run, axis).

    BOTH AXES ARE SCANNED, and that is not symmetry for its own sake: a
    horizontal cut cannot measure a horizontal stroke.  The o's bottom arc, the
    H's crossbar, the e's bar and every serif are near-horizontal, so a
    horizontal cut lands a run that is wide, short-lived and rejected by the
    parallelism test below -- the letter then reports a "thinnest stroke" that
    is simply the thinnest VERTICAL one it has.  Scanning columns as well finds
    them: axis 1 in the output is a vertical cut, i.e. a horizontal stroke.

    Two filters, and the second one is the whole difference between a stroke
    and a number that looks like one:

    * the band is inset 6% of the ink height at each end, so the terminals --
      where every stroke tapers to nothing -- cannot supply the minimum;
    * the run must be LOCALLY PARALLEL: its width, and the derived t, must
      agree within `tol` with the same run 15 units above AND below, and there
      must be exactly one overlapping run at each.  A junction (the n's
      shoulder into its stem, the a's bowl into its flank) is locally smooth
      but not locally parallel -- its width is climbing -- and a serif's flare
      is not parallel either.  At +/-6 units both survived and both were being
      reported as the letter's thickest stroke, which is how this function got
      its second filter.
    """
    iy = 0.06 * (y1 - y0)
    out = _axis_samples(contours, segs, y0 + iy, y1 - iy, 0, step, tol, delta)
    if x0 is not None:
        ix = 0.06 * (x1 - x0)
        out += _axis_samples(contours, segs, x0 + ix, x1 - ix, 1,
                             step, tol, delta)
    return out


# --------------------------------------------------------------------------
# raster (only for --png)


def raster(contours, x0, y0, w, h):
    """1 unit = 1 px even-odd fill, sampled at pixel centres."""
    a = np.zeros((h, w), bool)
    for row in range(h):
        y = y0 + (h - 1 - row) + 0.5
        for s, e in runs_at_y(contours, y):
            i0 = int(math.ceil(s - x0 - 0.5))
            i1 = int(math.floor(e - x0 - 0.5))
            if i1 >= i0:
                a[row, max(0, i0):min(w, i1 + 1)] = True
    return a


def write_png(contours, path, label, cap=False):
    x0, y0, x1, y1 = bbox(contours)
    padl, padb = 70, 70
    x0i, y0i = int(math.floor(x0)) - padl, int(math.floor(y0)) - padb
    W = int(math.ceil(x1)) + padl - x0i
    H = int(math.ceil(y1)) + padb - y0i
    a = raster(contours, x0i, y0i, W, H)
    im = Image.fromarray(np.where(a, 0, 255).astype('uint8'), 'L').convert('RGB')
    d = ImageDraw.Draw(im)
    try:
        lab = ImageFont.load_default(12)
    except TypeError:
        lab = ImageFont.load_default()

    def ry(u):                       # design y -> image row
        return H - 1 - int(round(u - y0i))

    grid = [('%.1f' % (k / 10.0), k * XH / 10.0, k in (0, 10))
            for k in range(-7, 20)]
    if cap:
        grid += [('CAP', CAP, True)]
    for name, u, strong in grid:
        r = ry(u)
        if not (0 <= r < H):
            continue
        col = (200, 60, 60) if strong else (190, 190, 210)
        for x in range(0, W, 3 if strong else 6):
            im.putpixel((x, r), col)
        d.text((2, r - 13), name, font=lab, fill=col)
    u = (x0i // 50) * 50
    while u <= x0i + W:
        c = int(round(u - x0i))
        if 0 <= c < W:
            col = (200, 60, 60) if u == 0 else (190, 190, 210)
            for yy in range(0, H, 3 if u == 0 else 6):
                im.putpixel((c, yy), col)
            d.text((c + 2, 2), str(int(u)), font=lab, fill=col)
        u += 50
    d.text((padl, H - 18), label, font=lab, fill=(30, 30, 30))
    im.save(path)


# --------------------------------------------------------------------------
# reference fonts


class Ref:
    def __init__(self, path, label):
        self.path, self.label = path, label
        self.font = TTFont(path)
        self.gs = self.font.getGlyphSet()
        self.cmap = self.font.getBestCmap()
        self.upm = self.font['head'].unitsPerEm
        self.angle = self.font['post'].italicAngle
        xb = bbox(flatten(self.gs, self.cmap[ord('x')]))
        self.xh_units = xb[3]
        self.k = XH / self.xh_units
        self.shear = math.tan(math.radians(-self.angle))
        self.hmtx = self.font['hmtx']

    def glyph(self, ch):
        name = self.cmap[ord(ch)]
        return transform(flatten(self.gs, name), self.k, self.shear), name

    def advance(self, name):
        return self.hmtx[name][0] * self.k

    def measured_slant(self, ch='l', lo=0.25, hi=1.4):
        """The slant actually drawn on a stem, as a check on the declared
        `post.italicAngle` -- because the declared angle is what step 3 removes,
        and if the drawn stem disagrees the "unsheared" space still leans.

        Measured on the SCALED but NOT unsheared outline: midpoints of the one
        horizontal run over a band, fitted.  Rows whose run is more than 15%
        off the median width are dropped -- they are the entry and exit serifs,
        whose midpoints sit to one side of the stem's and which dragged the
        first version of this to 14.8 degrees on an `i` whose stem draws 11."""
        name = self.cmap[ord(ch)]
        cs = transform(flatten(self.gs, name), self.k, 0.0)
        rec = []
        y = lo * XH
        while y <= hi * XH:
            r = runs_at_y(cs, y)
            if len(r) == 1:
                rec.append((y, (r[0][0] + r[0][1]) / 2.0, r[0][1] - r[0][0]))
            y += 5.0
        if len(rec) < 8:
            return None
        med = sorted(w for _, _, w in rec)[len(rec) // 2]
        rec = [r for r in rec if abs(r[2] - med) <= 0.15 * med]
        if len(rec) < 8:
            return None
        a = np.polyfit(np.array([r[0] for r in rec]),
                       np.array([r[1] for r in rec]), 1)[0]
        return math.degrees(math.atan(a))


# --------------------------------------------------------------------------
# scans


def _otsu(a):
    hist = np.bincount(a.ravel(), minlength=256).astype(float)
    tot = hist.sum()
    w = np.cumsum(hist); m = np.cumsum(hist * np.arange(256))
    mt = m[-1]
    with np.errstate(invalid='ignore', divide='ignore'):
        between = (mt * w / tot - m) ** 2 / (w * (tot - w))
    between[~np.isfinite(between)] = -1
    return int(np.argmax(between))


def _label(mask):
    """4-connected components as a list of (size, coords-mask), largest first.
    Iterative; the recursion depth of a flood over a 430-unit letter is in the
    tens of thousands."""
    seen = np.zeros_like(mask)
    hgt, wid = mask.shape
    out = []
    for sy in range(hgt):
        for sx in range(wid):
            if not mask[sy, sx] or seen[sy, sx]:
                continue
            comp = np.zeros_like(mask)
            stack = [(sy, sx)]; seen[sy, sx] = True; comp[sy, sx] = True
            while stack:
                y, x = stack.pop()
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < hgt and 0 <= nx < wid and mask[ny, nx] \
                            and not seen[ny, nx]:
                        seen[ny, nx] = True; comp[ny, nx] = True
                        stack.append((ny, nx))
            out.append((int(comp.sum()), comp))
    out.sort(key=lambda r: -r[0])
    return out


def despeckle(mask, frac=0.03):
    """Drop every component under `frac` of the largest.  A photographed page
    binarized by Otsu carries paper grain and JPEG ringing as dozens of
    one-pixel islands -- the owner's `a` crop came back as 26 components -- and
    a single stray pixel moves the ink bbox, which every position below is
    measured from.  Returns (clean mask, components before, components after).
    """
    comps = _label(mask)
    if not comps:
        return mask, 0, 0
    keep = [c for n, c in comps if n >= frac * comps[0][0]]
    out = np.zeros_like(mask)
    for c in keep:
        out |= c
    return out, len(comps), len(keep)


DESCENDERS = set('gjpqy')

# How tall a letter's ink should be, in x-heights, if the crop holds that
# letter and nothing else and the crop's declared x-height is right.  This is
# the scans' only self-check and it earns its place: the owner's `a` crop
# measures 1.55 xh, which is not an `a`.
EXPECT_H = dict.fromkeys('acemnorsuvwxz', (0.95, 1.15))
EXPECT_H.update(dict.fromkeys('bdfhkl', (1.45, 1.85)))
EXPECT_H.update(dict.fromkeys('gpqy', (1.45, 1.85)))
EXPECT_H.update(dict.fromkeys('i', (1.30, 1.60)))
EXPECT_H.update(dict.fromkeys('j', (1.85, 2.35)))
EXPECT_H.update(dict.fromkeys('t', (1.12, 1.38)))


def scan_mask(ch, src):
    """Binarize a hand-located crop into a 1 unit = 1 px mask in Albo's grid,
    with the baseline located.  Returns a dict, or None if the crop is empty."""
    path, box, xh_px, note = src
    img = Image.open(path).convert('L').crop(box)
    k = XH / xh_px
    up = img.resize((max(1, int(round(img.width * k))),
                     max(1, int(round(img.height * k)))), Image.LANCZOS)
    a = np.asarray(up)
    thr = _otsu(a)
    mask = a < thr
    if not mask.any():
        return None
    mask, parts_raw, parts = despeckle(mask)
    ys, xs = np.where(mask)
    mask = mask[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    # Baseline.  A descender letter's baseline is one x-height below the ink
    # top (its bowl reaches the x-height line); every other letter here stands
    # on the baseline, so the ink bottom IS it -- give or take the overshoot a
    # round letter has, which is why the round ones are marked in the doc.
    if ch in DESCENDERS:
        base_row = XH
        base_note = 'baseline = ink top + 1 xh (ESTIMATED)'
    else:
        base_row = mask.shape[0] - 1
        base_note = 'baseline = ink bottom'
    # The one number that says whether to believe the crop at all.  The crop's
    # declared x-height is what every unit below is scaled by, so if the ink
    # the crop actually holds is not the height that letter should be, the
    # scale is wrong and so is everything under it.
    want = EXPECT_H.get(ch, (0.95, 1.15))
    h_xh = mask.shape[0] / XH
    trust = 'OK' if want[0] <= h_xh <= want[1] else \
        'SUSPECT: ink is %.2f xh tall, expected %.2f-%.2f' % (h_xh, *want)
    return dict(mask=mask, k=k, note=note, thr=thr, xh_px=xh_px,
                base_row=base_row, base_note=base_note, h_xh=h_xh,
                parts=parts, parts_raw=parts_raw, trust=trust)


def scan_runs_at(m, y):
    """Ink runs at design height y on a scan mask.  x is the column index from
    the ink bbox's left edge -- comparable ROW TO ROW within this scan, and NOT
    comparable with an outline's, because the bitmap is still sheared.  The
    widths are comparable with everything, shear leaving horizontal distances
    at a fixed y alone."""
    row = int(round(m['base_row'] - y))
    if not (0 <= row < m['mask'].shape[0]):
        return None
    r = m['mask'][row]
    out, i, W = [], 0, len(r)
    while i < W:
        if r[i]:
            j = i
            while j < W and r[j]:
                j += 1
            out.append((float(i), float(j)))
            i = j
        else:
            i += 1
    return out


# --------------------------------------------------------------------------
# reporting (the long text report; `--md` below emits the doc's blocks)


def fmt_runs(runs, prec=0):
    return ' '.join('%.*f-%.*f(%.*f)' % (prec, a, prec, b, prec, b - a)
                    for a, b in runs)


def ladder_for(ch, y0, y1):
    """The sample heights this letter actually has ink at.  Rows within 2
    units of the ink's own extremes are dropped: a cut there returns a run one
    or two units long, which is the outline's corner and not a measurement."""
    if ch.isupper():
        ys = [f * CAP for f in LADDER_UC] + [f * XH for f in LADDER_UC_DESC]
    else:
        ys = [f * XH for f in LADDER_LC]
    return sorted(y for y in ys if y0 + 2 < y < y1 - 2)


def label_y(ch, y):
    if ch.isupper():
        return '%.2f cap' % (y / CAP) if y >= 0 else '%.2f xh' % (y / XH)
    return '%.2f xh' % (y / XH)


def report_glyph(ref, ch, out, md=False):
    cs, name = ref.glyph(ch)
    x0, y0, x1, y1 = bbox(cs)
    adv = ref.advance(name)
    w, h = x1 - x0, y1 - y0
    head = ('bbox x %.0f..%.0f  y %.0f..%.0f   w %.0f  h %.0f  w/h %.3f   '
            'adv %.0f  lsb %.0f  rsb %.0f' %
            (x0, x1, y0, y1, w, h, w / h, adv, x0, adv - x1))
    rows = []
    for y in ladder_for(ch, y0, y1):
        rr = runs_at_y(cs, y)
        if not rr:
            continue
        ts = ['%.0f' % m[0] if m else '-'
              for m in (perp_width(cs, y, r) for r in rr)]
        rows.append((label_y(ch, y), '%.0f' % y, fmt_runs(rr), ' '.join(ts)))
    cols = []
    for f in COLS:
        vr = runs_at_x(cs, x0 + f * w)
        if vr:
            cols.append(('%.2f w' % f, '%.0f' % (x0 + f * w), fmt_runs(vr)))
    samp = stroke_samples(cs, segments(cs), y0, y1, x0, x1)
    best = max(samp, key=lambda r: r[0]) if samp else None
    worst = min(samp, key=lambda r: r[0]) if samp else None
    st = []
    for axis, tag in ((0, 'vertical'), (1, 'horizontal')):
        v = sorted(r[0] for r in samp if r[5] == axis)
        if v:
            st.append('%s strokes: median %.0f (%.2f S), range %.0f-%.0f, n=%d'
                      % (tag, v[len(v) // 2], v[len(v) // 2] / STEM_S,
                         v[0], v[-1], len(v)))
    for tag, rec in (('thickest', best), ('thinnest', worst)):
        if not rec:
            continue
        t, v, mid, a, b, axis = rec
        where = ('y=%.0f (%s), x~%.0f, vertical stroke'
                 % (v, label_y(ch, v), mid)) if axis == 0 else \
                ('x=%.0f, y~%.0f (%s), horizontal stroke'
                 % (v, mid, label_y(ch, mid)))
        st.append('%s %.0f (%.2f S) at %s; cuts %.0f x %.0f'
                  % (tag, t, t / STEM_S, where, a, b))
    if not st:
        st.append('NO STABLE SINGLE-STROKE CUT -- every cut lands on a '
                  'junction or a taper; do not quote a stroke for this letter')
    out(head, rows, cols, st, (best, worst), (x0, y0, x1, y1, adv))
    return cs


def report_scan(ch, m, out):
    """A scan's rows are RUNS ONLY.  The disc cross-check the outline gets is
    not applied here: on a photographed letterpress page the edges are ragged,
    and one source pixel of notch becomes 6-8 units at this scale, so the disc
    reads up to 20% under a clean stem and would dispute every one of them.
    The run width is the honest measurement on a bitmap, and it is the one the
    shear leaves alone."""
    hgt, wid = m['mask'].shape
    rows = []
    for y in ladder_for(ch, m['base_row'] - (hgt - 1), m['base_row']):
        rr = scan_runs_at(m, y)
        if rr:
            rows.append((label_y(ch, y), '%.0f' % y, fmt_runs(rr), ''))
    left, right, n = report_band(m)
    out(rows, dict(w=wid, h=hgt, parts=m['parts'], parts_raw=m['parts_raw'],
                   left=left, right=right, nband=n, note=m['note'],
                   thr=m['thr'], xh_px=m['xh_px'], base=m['base_note'],
                   h_xh=m['h_xh'], trust=m['trust']))


# --------------------------------------------------------------------------
# markdown emitter -- the doc's per-letter blocks come from here, so the
# numbers in `docs/albo-aldine-targets.md` can be regenerated and diffed.
# Only the prose lines in that doc are hand-written.


def _short(y, ch):
    return ('%.2f' % (y / (CAP if ch.isupper() else XH))).lstrip('0')


def _pairs(tag, items, per):
    """Lay cells out `per` to a line; the tag labels the first line only."""
    out = []
    for i in range(0, len(items), per):
        out.append((tag if i == 0 else ' ' * len(tag))
                   + ' | '.join(items[i:i + per]))
    return out


def md_glyph(ref, ch, scans, per=2, brief=False):
    cs, name = ref.glyph(ch)
    x0, y0, x1, y1 = bbox(cs)
    segs = segments(cs)
    L = ['bbox  x %.0f..%.0f  y %.0f..%.0f  w %.0f  h %.0f  w/h %.3f  '
         'adv %.0f  lsb %.0f  rsb %.0f'
         % (x0, x1, y0, y1, x1 - x0, y1 - y0, (x1 - x0) / (y1 - y0),
            ref.advance(name), x0, ref.advance(name) - x1)]
    cells = []
    for y in ladder_for(ch, y0, y1):
        rr = runs_at_y(cs, y)
        if rr:
            cells.append('%s %s' % (_short(y, ch), fmt_runs(rr)))
    L += _pairs('rows  ', cells, per)
    cells = []
    for f in COLS:
        vr = runs_at_x(cs, x0 + f * (x1 - x0))
        if vr:
            cells.append('%s %s' % (('%.2f' % f).lstrip('0'), fmt_runs(vr)))
    L += _pairs('cols  ', cells, per + 1)
    samp = stroke_samples(cs, segs, y0, y1, x0, x1)
    if samp:
        parts = []
        for axis, tag in ((0, 'vert'), (1, 'horz')):
            v = sorted(r[0] for r in samp if r[5] == axis)
            if v:
                parts.append('%s med %.0f (%.2f S) rng %.0f-%.0f n%d'
                             % (tag, v[len(v) // 2], v[len(v) // 2] / STEM_S,
                                v[0], v[-1], len(v)))
        L.append('strk  ' + ' | '.join(parts))
        b = max(samp, key=lambda r: r[0]); w = min(samp, key=lambda r: r[0])
        # `brief` drops the extremes line.  The capitals use it: on a slab
        # serif face a capital's thinnest stable cut is almost always the top
        # serif's 23 units, which is 26 identical lines saying nothing.
        if not brief:
            L.append('      thickest %.0f (%.2f S) at %s %s | thinnest %.0f '
                     '(%.2f S) at %s %s'
                     % (b[0], b[0] / STEM_S,
                        _short(b[1] if b[5] == 0 else b[2], ch),
                        'vert' if b[5] == 0 else 'horz',
                        w[0], w[0] / STEM_S,
                        _short(w[1] if w[5] == 0 else w[2], ch),
                        'vert' if w[5] == 0 else 'horz'))
    else:
        L.append('strk  NO STABLE SINGLE-STROKE CUT -- see the negative '
                 'results section')
    m = scans.get(ch)
    if m:
        hgt = m['mask'].shape[0]
        rows = []
        for y in ladder_for(ch, m['base_row'] - (hgt - 1), m['base_row']):
            rr = scan_runs_at(m, y)
            if rr:
                rows.append('%s %s' % (_short(y, ch), fmt_runs(rr)))
        band = ''
        rep = report_band(m)
        if rep[0] is not None:
            band = ' | band .20-.80 left %.0f (%.2f S)' % (rep[0], rep[0] / STEM_S)
            if rep[1] is not None:
                band += ' right %.0f (%.2f S)' % (rep[1], rep[1] / STEM_S)
        L.append('scan  %s | xh %d px | ink %dx%d (%.2f xh) | %s%s'
                 % (m['note'], m['xh_px'], m['mask'].shape[1], hgt,
                    m['h_xh'], m['trust'], band))
        L += _pairs('      ', rows, per)
    return L


def report_band(m):
    """The robust scan number: the median width of the leftmost and rightmost
    run over the x-height band, which is what `aldine_autofit` has always used,
    plus how many cuts it is a median of.  Runs under 4% of the letter's width
    are dropped -- at 54-75 px of x-height a printed page leaves specks that
    survive Otsu and the despeckle, and one of them at the left edge would
    become the "flank"."""
    wid = m['mask'].shape[1]
    L, R = [], []
    y = 0.20 * XH
    while y <= 0.80 * XH:
        rr = [r for r in (scan_runs_at(m, y) or [])
              if r[1] - r[0] >= 0.04 * wid]
        if len(rr) >= 2:
            L.append(rr[0][1] - rr[0][0]); R.append(rr[-1][1] - rr[-1][0])
        elif len(rr) == 1:
            L.append(rr[0][1] - rr[0][0])
        y += 6.0
    md_ = lambda v: sorted(v)[len(v) // 2] if v else None
    return md_(L), md_(R), len(L)


def emit_md(ref, chars, scans, per=2, group=False, brief=False):
    """One fenced block per letter, or -- with `group` -- one fence for the
    whole set with the letter opening each block.  The grouped form costs one
    line per letter instead of three, which is why the capitals use it."""
    if group:
        print('```')
    for ch in chars:
        if not group:
            print('#### %s' % ch)
            print('```')
        L = md_glyph(ref, ch, scans, per, brief)
        if group:
            print(('' if ch == chars[0] else '\n') + '%s  %s' % (ch, L[0]))
            for line in L[1:]:
                print(line)
        else:
            for line in L:
                print(line)
        if not group:
            print('```')
    if group:
        print('```')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--font', default=PRIMARY)
    ap.add_argument('--chars', default=LC + UC)
    ap.add_argument('--png', metavar='DIR')
    ap.add_argument('--scans', action='store_true')
    ap.add_argument('--second', action='store_true',
                    help='the smaller Pagella table (lowercase only)')
    ap.add_argument('--slant', action='store_true',
                    help='declared vs drawn slant; read the l, '
                         'whose stem is the only clean one')
    ap.add_argument('--md', metavar='CHARS',
                    help='emit the doc blocks for these letters')
    ap.add_argument('--per', type=int, default=2,
                    help='row cells per line in --md output')
    ap.add_argument('--brief', action='store_true',
                    help='omit the thickest/thinnest line from --md')
    ap.add_argument('--group', action='store_true',
                    help='one fenced block for the whole --md set')
    args = ap.parse_args()

    ref = Ref(args.font, os.path.basename(args.font))
    if args.md:
        from aldine_autofit import SOURCES
        sc = {c: scan_mask(c, SOURCES[c]) for c in args.md if c in SOURCES}
        emit_md(ref, args.md, {k: v for k, v in sc.items() if v},
                args.per, args.group, args.brief)
        return
    if args.slant:
        for r in (Ref(PRIMARY, 'flanker'), Ref(SECOND, 'pagella')):
            print('%-34s declared %.1f  measured on l %s  i %s  H %s'
                  % (r.label, r.angle,
                     '%.1f' % r.measured_slant('l') if r.measured_slant('l') else '-',
                     '%.1f' % r.measured_slant('i', 0.15, 0.85) if r.measured_slant('i', 0.15, 0.85) else '-',
                     '%.1f' % r.measured_slant('H', 0.15, 1.45) if r.measured_slant('H', 0.15, 1.45) else '-'))
        return

    if args.second:
        # The SECOND OPINION table: Flanker beside Pagella, same measurement,
        # same units.  Medians rather than the extremes, because an extreme
        # names a place on the letter and a median names the letter's stroke.
        a = Ref(PRIMARY, 'flanker'); b = Ref(SECOND, 'pagella')

        def cell(r, ch):
            cs, name = r.glyph(ch)
            x0, y0, x1, y1 = bbox(cs)
            sm = stroke_samples(cs, segments(cs), y0, y1, x0, x1)
            v = sorted(q[0] for q in sm if q[5] == 0)
            h = sorted(q[0] for q in sm if q[5] == 1)
            f = lambda z: ('%.0f' % z[len(z) // 2]) if z else '-'
            g = lambda z: ('%.2f' % (z[len(z) // 2] / STEM_S)) if z else '-'
            return ('%.0f | %.3f | %.0f | %s | %s | %s'
                    % (x1 - x0, (x1 - x0) / (y1 - y0), r.advance(name),
                       f(v), g(v), f(h)))
        print('| ltr | F w | F w/h | F adv | F vert | xS | F horz '
              '| P w | P w/h | P adv | P vert | xS | P horz |')
        print('|' + '---|' * 13)
        for ch in LC:
            print('| %s | %s | %s |' % (ch, cell(a, ch), cell(b, ch)))
        return

    if args.scans:
        from aldine_autofit import SOURCES
        for ch in sorted(SOURCES):
            m = scan_mask(ch, SOURCES[ch])
            print('\n### scan %s' % ch)
            if not m:
                print('  EMPTY CROP'); continue

            def out(rows, meta):
                print('  %s | otsu %d | crop xh %d px | parts %d (%d before '
                      'despeckle) | ink %dx%d units, h %.2f xh | %s | %s'
                      % (meta['note'], meta['thr'], meta['xh_px'],
                         meta['parts'], meta['parts_raw'], meta['w'],
                         meta['h'], meta['h_xh'], meta['base'], meta['trust']))
                if meta['left'] is not None:
                    print('  band 0.20-0.80 xh (%d cuts): left run median %.0f '
                          '(%.2f S)%s' % (
                              meta['nband'], meta['left'],
                              meta['left'] / STEM_S,
                              ', right run median %.0f (%.2f S)' % (
                                  meta['right'], meta['right'] / STEM_S)
                              if meta['right'] is not None else ''))
                for lab, yy, rr, ts in rows:
                    print('   %-9s y=%-5s | %s' % (lab, yy, rr))
            report_scan(ch, m, out)
        return

    print('# %s  upm %d  italicAngle %.1f  x-height %.0f -> 429 (k %.4f)'
          % (ref.label, ref.upm, ref.angle, ref.xh_units, ref.k))
    for ch in args.chars:
        cs = None

        def out(head, rows, cols, st, _b, _g):
            print('\n### %s' % ch)
            print('  %s' % head)
            for lab, yy, rr, ts in rows:
                print('   %-9s y=%-5s | %s | t %s' % (lab, yy, rr, ts))
            for lab, xx, vr in cols:
                print('   col %-6s x=%-5s | %s' % (lab, xx, vr))
            for s in st:
                print('   %s' % s)
        cs = report_glyph(ref, ch, out)
        if args.png:
            os.makedirs(args.png, exist_ok=True)
            tag = ('uc_' if ch.isupper() else 'lc_') + ch
            write_png(cs, os.path.join(args.png, '%s.png' % tag),
                      '%s  %s  unsheared %.1f deg, xh=429'
                      % (ch, ref.label, -ref.angle), cap=ch.isupper())


if __name__ == '__main__':
    main()
