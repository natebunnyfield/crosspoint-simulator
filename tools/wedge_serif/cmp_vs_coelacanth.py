"""Every alphanumeric of Albo's Aldine italic against Coelacanth Italic, ranked.

Owner 2026-09-17: *"compare every alphanumeric of coelacanth italic with our
aldine italic and show me an informative table graphic of what could be
improved."*

WHY COELACANTH IS THE YARDSTICK. It is the face the g's brush-stroke analysis
was measured off (`docs/italic-g-strokes.md`) and the one whose x-height --
425/1000 against Albo's 429 -- is closest of any reference, so the two can be
set to a common x-height without one of them being scaled past recognition.
It is NOT a target to be copied: Albo is its own face, aimed at metal
letterpress, and it is deliberately narrower (FJORD_WIDTH=95) and
shorter-capped (cap/xh 1.571 against Coelacanth's 1.673).

    THE WHOLE DESIGN OF THIS INSTRUMENT IS THE SUBTRACTION OF THOSE DELIBERATE
    DIFFERENCES. Every proportion figure is a RESIDUAL against Albo's own
    face-wide median for that glyph's class -- so "Albo is 5% narrow" vanishes
    and "this one letter is 18% wide while the rest of its own alphabet is 5%
    narrow" survives. A raw ratio table would have every glyph red and would
    say nothing.

    AND EVERY SHAPE FIGURE CARRIES COELACANTH AS ITS CONTROL. The pen column is
    not Albo's deviation from its own nib, it is that deviation MINUS
    Coelacanth's on the same letter -- because some letters cannot state a nib
    angle at all (z is 46 degrees off on Coelacanth too; its diagonal is most of
    its ink) and an instrument with no control would file that as an Albo fault.

FOUR TRAPS, each of which produced a confidently wrong table first:

  1. **Shear is applied at BUILD time** (FJORD_SLANT=13), and Albo's glyph code
     is unsheared design space. Both faces are unsheared before anything is
     measured, or a width is a width-plus-slant and a stress axis is the slant's.
  2. **A font's declared italic angle is not its slant.** Coelacanth's `post`
     table says 0.0 and the face slants 14.5. `refs_registry` holds the MEASURED
     value and this asks it. Albo is unsheared by its known build angle, 13,
     which is exact -- its `l` measures 12.2 and that 0.8 is the wedge serifs
     pulling the stem-centre reading, not a different slant.
  3. **DO NOT take the pen's thin direction as the argmin over 15-degree bins.**
     `cmp_g_strokes.py` does, and on a single g that is fine; over 62 glyphs it
     is not. A bin holding four ridge samples off a serif tip wins the argmin,
     so the first run of this script reported Albo's Y at 22.15:1 contrast and
     its V at 15.29:1 (Coelacanth: 3.14 and 2.45), and quantised every angle to
     a multiple of 15 so that all 62 glyphs "deviated" from a median that fell
     between two bins. Here the profile is a sliding +/-22-degree window at
     2-degree steps, each window's thickness a MEDIAN over at least 25 samples,
     and CONTRAST is not read off it at all -- it is the 85th percentile of
     ridge thickness over the 15th, which has no argmin to be captured.
  4. **`top` and `depth` cannot be residualised by letter case.** The lowercase
     "class" holds x-height letters and ascenders together, so its median height
     is a number no letter has. Height is a log RATIO (Albo's cap is 94.8% of
     Coelacanth's on every cap, so the median removes it); depth is an absolute
     difference residualised within a band taken off COELACANTH's own value --
     flat letters with flat, descenders with descenders.

WHAT IS MEASURED, per glyph, on both faces at a common x-height: ink width and
advance; height above the baseline and depth below it; stem (85th percentile of
twice the chamfer distance along the ridge) and hairline (15th); the pen's nib
angle from the smoothed direction profile; and the concave-vertex count from
`cmp_joints`, as an EXCESS over Coelacanth -- raw counts are not a verdict,
Coelacanth has 60 notches to Albo's 35 and its eight largest are the inner
vertices of V W M N w, which are correct.

    PYTHON_GIL=0 python3 cmp_vs_coelacanth.py --albo <Albo-Italic.ttf> \\
        --png /tmp/albo_vs_coelacanth.png --json /tmp/t.json
"""
import argparse, json, math, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import refs_registry as RR
import cmp_joints

GLYPHS = ([chr(c) for c in range(ord('a'), ord('z') + 1)] +
          [chr(c) for c in range(ord('A'), ord('Z') + 1)] +
          list("0123456789"))
MATCH = 2.2          # below this the glyph is reported as matching
WORK = 4.0           # at or above this it is red


# ---------------------------------------------------------------- rasterising

def _face(ttf):
    from fontTools.ttLib import TTFont
    f = TTFont(ttf)
    upm = f["head"].unitsPerEm
    try:
        sx = f["OS/2"].sxHeight or upm * 0.5
    except Exception:
        sx = upm * 0.5
    return f, upm, float(sx)


def layer(ttf, ch, slant, px, pad=6):
    """Unsheared ink for one glyph at x-height `px`.

    Returns (mask, top, left, adv): `top` is the crop's top edge in pixels ABOVE
    the baseline, `left` its left edge right of the pen origin, `adv` the
    advance in the same pixels. Two faces set to the same `px` are then directly
    comparable in every one of those numbers.
    """
    from PIL import Image, ImageDraw, ImageFont
    f, upm, sx = _face(ttf)
    size = int(round(px * upm / sx))
    W = H = size * 3
    ox, base = int(W * 0.35), int(H * 0.62)
    im = Image.new("L", (W, H), 255)
    ImageDraw.Draw(im).text((ox, base), ch, font=ImageFont.truetype(ttf, size),
                            fill=0, anchor="ls")
    if abs(slant) > 0.05:
        k = math.tan(math.radians(slant))
        # shear about the BASELINE, so the baseline point stays where it is
        im = im.transform((W, H), Image.AFFINE, (1, k, -k * base, 0, 1, 0),
                          resample=Image.BICUBIC, fillcolor=255)
    a = np.asarray(im) < 128
    if not a.any():
        return None
    ys, xs = np.nonzero(a)
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    m = np.zeros((y1 - y0 + 1 + 2 * pad, x1 - x0 + 1 + 2 * pad), bool)
    m[pad:pad + y1 - y0 + 1, pad:pad + x1 - x0 + 1] = a[y0:y1 + 1, x0:x1 + 1]
    cmap = f.getBestCmap()
    adv = f["hmtx"][cmap[ord(ch)]][0] * px / sx if ord(ch) in cmap else 0.0
    return m, float(base - (y0 - pad)), float((x0 - pad) - ox), float(adv)


# ------------------------------------------------------- distance / centreline

def chamfer(mask):
    """Chamfer (1, 1.414) distance to background, vectorised.

    The same transform `cmp_g_strokes.dist` computes; the horizontal sweeps are
    cumulative minima instead of Python loops, because this runs it 124 times
    rather than six. `r[x] = min(r[x], r[x-1]+1)` over a whole row is exactly
    `x + running_min(r[x] - x)`.
    """
    INF = 1e9
    d = np.where(mask, INF, 0.0)
    H, W = d.shape
    ix = np.arange(W, dtype=float)

    def hsweep(r):
        r = np.minimum(r, np.minimum.accumulate(r - ix) + ix)
        return np.minimum(r, np.minimum.accumulate((r + ix)[::-1])[::-1] - ix)

    for y in range(H):
        r = d[y].copy()
        if y > 0:
            up = d[y - 1]
            r = np.minimum(r, up + 1.0)
            r[1:] = np.minimum(r[1:], up[:-1] + 1.414)
            r[:-1] = np.minimum(r[:-1], up[1:] + 1.414)
        d[y] = hsweep(r)
    for y in range(H - 2, -1, -1):
        r = d[y].copy()
        dn = d[y + 1]
        r = np.minimum(r, dn + 1.0)
        r[1:] = np.minimum(r[1:], dn[:-1] + 1.414)
        r[:-1] = np.minimum(r[:-1], dn[1:] + 1.414)
        d[y] = hsweep(r)
    return d


def ridge_map(mask, d, floor=1.5):
    """Centreline: ink whose distance is a local maximum along BOTH axes.

    NO PERCENTILE THRESHOLD, and `cmp_g_strokes.ridge` records why: keeping only
    the top of the distance range DELETES EVERY THIN STROKE from the sample,
    because a thin stroke's distance is small all along it. An instrument that
    samples only the thick parts of a letter cannot measure how thin the thin
    parts are; that cut put Coelacanth's contrast at 1.50:1 when it is 2.3:1.
    """
    R = mask & (d >= floor)
    R[:, 1:-1] &= (d[:, 1:-1] >= d[:, :-2]) & (d[:, 1:-1] >= d[:, 2:])
    R[1:-1, :] &= (d[1:-1, :] >= d[:-2, :]) & (d[1:-1, :] >= d[2:, :])
    R[0, :] = R[-1, :] = R[:, 0] = R[:, -1] = False
    return R


def _integral(A):
    return np.pad(A.astype(float).cumsum(0).cumsum(1), ((1, 0), (1, 0)))


def ridge_directions(R, r=7):
    """Run direction at every ridge point, 0..180, from the principal axis of
    its neighbours -- for every point at once, off integral images of the ridge
    map's moments, so the O(n^2) neighbour search in `cmp_g_strokes.directions`
    does not happen. A 2x2 symmetric covariance's major axis is closed-form,
    0.5*atan2(2b, a-c).
    """
    H, W = R.shape
    ys, xs = np.nonzero(R)
    if len(ys) < 8:
        return ys, xs, np.full(len(ys), np.nan)
    Y, X = np.mgrid[0:H, 0:W].astype(float)
    Yu = (H - 1) - Y                       # y-up, so an angle means what it says
    I = {k: _integral(A) for k, A in
         (("n", R), ("x", R * X), ("y", R * Yu),
          ("xx", R * X * X), ("yy", R * Yu * Yu), ("xy", R * X * Yu))}
    y0 = np.clip(ys - r, 0, H); y1 = np.clip(ys + r + 1, 0, H)
    x0 = np.clip(xs - r, 0, W); x1 = np.clip(xs + r + 1, 0, W)

    def box(k):
        J = I[k]
        return J[y1, x1] - J[y0, x1] - J[y1, x0] + J[y0, x0]

    n = box("n")
    ok = n >= 4
    n = np.where(ok, n, 1.0)
    mx, my = box("x") / n, box("y") / n
    a = box("xx") / n - mx * mx
    c = box("yy") / n - my * my
    b = box("xy") / n - mx * my
    ang = np.degrees(0.5 * np.arctan2(2 * b, a - c)) % 180.0
    return ys, xs, np.where(ok, ang, np.nan)


def nib_profile(ang, thick, half=22.0, step=2.0, min_n=25):
    """Thickness against stroke direction: a sliding circular window, median
    inside it, and a window under `min_n` samples simply not reported.

    This replaces the 15-degree argmin (trap 3 in the module docstring). The
    window is wide enough that no serif tip can own a direction on its own, and
    the step is fine enough that a nib angle is a number rather than a bin.
    """
    if len(ang) < min_n:
        return {}
    out = {}
    for t in np.arange(0.0, 180.0, step):
        dd = np.abs(ang - t) % 180.0
        dd = np.minimum(dd, 180.0 - dd)
        s = thick[dd <= half]
        if len(s) >= min_n:
            out[float(t)] = float(np.median(s))
    return out


def nib_angle(prof, min_cover=40, min_depth=1.40):
    """The direction the strokes come out THINNEST -- the angle the nib's edge
    is held at, or nan where the letter cannot state one.

    TWO GATES, and they fail for different reasons. `min_cover` is angular
    COVERAGE: fewer than 40 of the 90 windows measurable means the letter's ink
    does not run in enough directions to locate a minimum, which is i, l, J and
    r here. `min_depth` is the profile's own max/min: a FLAT profile has an
    argmin, and it is noise. The second gate fires on neither face in this pair
    (Albo's shallowest is the 7 at 1.48, Coelacanth's the F at 1.86), so it is
    a guard rather than a filter -- recorded because a gate that never fires
    looks removable until the day it is the only thing standing between a flat
    letter and a confident 74-degree verdict."""
    if len(prof) < min_cover:
        return float("nan")
    if max(prof.values()) / max(min(prof.values()), 1e-9) < min_depth:
        return float("nan")
    return float(min(prof, key=prof.get))


def circ180(a, b):
    if a != a or b != b:
        return float("nan")
    d = abs(a - b) % 180.0
    return min(d, 180.0 - d)


# ------------------------------------------------------------------- per glyph

def measure(ttf, ch, slant, px):
    L = layer(ttf, ch, slant, px)
    if L is None:
        return None
    mask, top, left, adv = L
    H, W = mask.shape
    d = chamfer(mask)
    R = ridge_map(mask, d)
    ys, xs, ang = ridge_directions(R)
    good = ~np.isnan(ang)
    th = 2.0 * d[ys, xs] / px
    m = dict(ch=ch, w=(W - 12) / px, adv=adv / px, top=top / px,
             depth=(H - 12 - top) / px, area=float(mask.sum()) / (px * px),
             n=int(good.sum()))
    if good.sum() < 25:
        m.update(stem=float("nan"), hair=float("nan"), contrast=float("nan"),
                 nib=float("nan"), cover=0, ang=None, th=None)
        return m
    a, t = ang[good], th[good]
    m["stem"] = float(np.percentile(t, 85))
    m["hair"] = float(np.percentile(t, 15))
    m["contrast"] = m["stem"] / max(m["hair"], 1e-6)
    p = nib_profile(a, t)
    m["cover"] = len(p)
    m["nib"] = nib_angle(p)
    m["ang"], m["th"] = a, t          # kept only to pool the face-wide nib
    return m


def face_nib(M):
    """The face's OWN nib, pooled over every glyph's ridge samples at once --
    far steadier than a median of 62 per-glyph estimates, and the number each
    glyph is then judged against."""
    A = np.concatenate([M[c]["ang"] for c in M if M[c] and M[c]["ang"] is not None])
    T = np.concatenate([M[c]["th"] for c in M if M[c] and M[c]["th"] is not None])
    p = nib_profile(A, T, min_n=400)
    if not p:
        return float("nan"), float("nan")
    return float(min(p, key=p.get)), max(p.values()) / min(p.values())


def notches(ttf, min_score=1200.0):
    """Concave-vertex count per glyph, via `cmp_joints`. Only ever used as an
    EXCESS over Coelacanth: the inner vertex of a V is a notch and is right."""
    out = {}
    for ch in GLYPHS:
        cs, _ = cmp_joints.contours(ttf, ch)
        out[ch] = 0 if not cs else sum(
            1 for sc, t, con, p in cmp_joints.corners(cs) if con and sc >= min_score)
    return out


# ---------------------------------------------------------------- the residual

def klass(ch):
    return "lower" if ch.islower() else ("upper" if ch.isupper() else "digit")


def residuals(A, C):
    """Per-glyph deltas with the face-wide systematic taken out.

    Width, stem, height and area are log RATIOS, so the letter's own intrinsic
    size cancels and a class median removes the deliberate offset (95% width,
    94.8% cap). Depth is an absolute difference and CANNOT be a ratio -- a flat
    letter's depth is ~0 -- so it is residualised inside a band read off
    COELACANTH's own value, flat with flat and descender with descender.
    """
    R = {}
    for ch in GLYPHS:
        a, c = A.get(ch), C.get(ch)
        if not a or not c:
            continue

        def lr(k):
            va, vc = a[k], c[k]
            if va != va or vc != vc or va <= 1e-6 or vc <= 1e-6:
                return float("nan")
            return math.log(va / vc)

        R[ch] = dict(lw=lr("w"), lt=lr("stem"), lh=lr("top"), la=lr("area"),
                     lc=lr("contrast"), ddep=a["depth"] - c["depth"],
                     band=klass(ch) + ("_d" if c["depth"] > 0.10 else "_f"))
    for key in ("lw", "lt", "lh", "la", "lc"):
        for k in ("lower", "upper", "digit"):
            v = [R[c][key] for c in R if klass(c) == k and R[c][key] == R[c][key]]
            med = float(np.median(v)) if v else 0.0
            for c in R:
                if klass(c) == k:
                    R[c][key + "_r"] = R[c][key] - med
    for b in set(R[c]["band"] for c in R):
        v = [R[c]["ddep"] for c in R if R[c]["band"] == b]
        med = float(np.median(v)) if v else 0.0
        for c in R:
            if R[c]["band"] == b:
                R[c]["ddep_r"] = R[c]["ddep"] - med
    return R


def robust(v):
    v = np.asarray([x for x in v if x == x], float)
    if len(v) < 4:
        return 1.0
    return max(1.4826 * float(np.median(np.abs(v - np.median(v)))), 1e-4)


# --------------------------------------------------------------------- verdict

WEIGHT = dict(pen=1.25, width=1.00, weight=1.00, contrast=0.85,
              notch=0.90, height=0.75, depth=0.55, colour=0.40)


def verdicts(res, A, C, nibA, nibC, nA, nC):
    """One line per fault, in the words a person can act on: the number, the
    direction, and what it is measured against."""
    sW, sT = robust([res[c]["lw_r"] for c in res]), robust([res[c]["lt_r"] for c in res])
    sH, sD = robust([res[c]["lh_r"] for c in res]), robust([res[c]["ddep_r"] for c in res])
    sC, sA = robust([res[c]["lc_r"] for c in res]), robust([res[c]["la_r"] for c in res])
    ex = {c: (circ180(A[c]["nib"], nibA) - circ180(C[c]["nib"], nibC))
          for c in res}
    sP = robust([abs(v) for v in ex.values()])
    out = {}
    for ch in res:
        r = res[ch]
        terms = []

        def add(key, z, txt):
            if z == z and z > 0:
                terms.append((WEIGHT[key] * z, key, txt))

        def pct(k):
            return 100 * (math.exp(r[k]) - 1)

        p = pct("lw_r")
        add("width", abs(r["lw_r"]) / sW,
            f"{abs(p):.0f}% {'wide' if p > 0 else 'narrow'} for its own alphabet")
        if r["lt_r"] == r["lt_r"]:
            p = pct("lt_r")
            add("weight", abs(r["lt_r"]) / sT,
                f"stem {abs(p):.0f}% {'heavy' if p > 0 else 'light'} for its own alphabet")
        e = ex.get(ch, float("nan"))
        if e == e and e > 0:
            add("pen", e / sP,
                f"thins at {A[ch]['nib']:.0f}° where the face's nib is "
                f"{nibA:.0f}° — {e:.0f}° further off than Coelacanth is here")
        if r["lc_r"] == r["lc_r"]:
            p = pct("lc_r")
            add("contrast", abs(r["lc_r"]) / sC,
                f"hairline {'too thin' if p > 0 else 'too fat'} — "
                f"{A[ch]['contrast']:.1f}:1 here, Coelacanth {C[ch]['contrast']:.1f}:1")
        add("height", abs(r["lh_r"]) / sH,
            f"{abs(pct('lh_r')):.0f}% {'tall' if r['lh_r'] > 0 else 'short'} "
            f"above the baseline for its class")
        add("depth", abs(r["ddep_r"]) / sD,
            f"descends {abs(r['ddep_r']):.2f} xh "
            f"{'deeper' if r['ddep_r'] > 0 else 'shallower'} than its class")
        if r["la_r"] == r["la_r"]:
            p = pct("la_r")
            add("colour", abs(r["la_r"]) / sA,
                f"sets {abs(p):.0f}% {'blacker' if p > 0 else 'lighter'} than its class")
        n = max(0, nA.get(ch, 0) - nC.get(ch, 0))
        if n:
            add("notch", min(n, 3) * 1.3,
                f"{n} concave notch{'es' if n > 1 else ''} where strokes union "
                f"— no stroke width tunes these out")
        terms.sort(reverse=True)
        # THE WORST TERM, plus a THIRD of the rest. A plain sum ranks the glyph
        # with six trivial complaints above the glyph with one real fault, and
        # the top of this table is meant to be the work queue -- the first cut
        # put Albo's u (11% narrow, one notch, 2% tall) two rows below its E,
        # whose arms are as heavy as its stem.
        out[ch] = dict(score=(terms[0][0] + 0.35 * sum(t[0] for t in terms[1:])
                              if terms else 0.0),
                       terms=terms, pen_excess=e)
    return out


# ---------------------------------------------------------------------- render

def _ui(sz, bold=False):
    from PIL import ImageFont
    return ImageFont.truetype(
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else
        "/System/Library/Fonts/Supplemental/Arial.ttf", sz)


def _mono(sz):
    from PIL import ImageFont
    try:
        return ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", sz)
    except Exception:
        return _ui(sz)


def render(path, order, A, C, res, V, nA, nC, nibA, nibC, conA, conC,
           albo_ttf, coel_ttf, coel_slant, albo_slant):
    from PIL import Image, ImageDraw
    GX, CELL, XHP, ROWH = 36, 112, 42, 126
    cols = [("#", 42), ("", 46), ("Coelacanth", CELL), ("Albo", CELL),
            ("overlaid", CELL), ("wid", 64), ("stem", 66), ("contrast", 96),
            ("pen", 60), ("ntch", 56)]
    xs, x = [], GX + 12
    for _, w in cols:
        xs.append(x); x += w
    VX = x + 18
    W, HEAD, FOOT = VX + 852 + GX, 246, 174
    H = HEAD + ROWH * len(order) + FOOT
    im = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(im)

    d.text((GX, 30), "Albo Aldine Italic against Coelacanth Italic",
           font=_ui(34, True), fill=(17, 17, 17))
    for j, s in enumerate([
        "All 62 alphanumerics, worst first. Both faces UNSHEARED before measuring "
        "(Albo by its 13° build shear; Coelacanth by 14.5° — MEASURED, its post "
        "table declares 0°) and set to a common x-height.",
        "wid and stem are RESIDUALS against Albo's own class median, so the "
        "deliberate 95% width and 94.8% cap are subtracted out and only the letter "
        "out of step with its own alphabet is left.",
        "pen is Albo's deviation from its own nib MINUS Coelacanth's from its own "
        "— Coelacanth is the control, because some letters (z) cannot state a nib "
        "angle on any face. – means the letter has too few directions to try.",
    ]):
        d.text((GX, 74 + j * 23), s, font=_ui(16), fill=(88, 88, 88))
    lx = GX
    d.text((lx, 154), "overlay:", font=_ui(16), fill=(88, 88, 88))
    for lab, col in (("Coelacanth only", (232, 126, 126)),
                     ("Albo only", (60, 60, 60)), ("both", (86, 32, 32))):
        lx += 64 if lab == "Coelacanth only" else 0
        d.rectangle([lx, 156, lx + 22, 168], fill=col)
        d.text((lx + 30, 154), lab, font=_ui(16), fill=(88, 88, 88))
        lx += 30 + d.textlength(lab, font=_ui(16)) + 26
    d.text((lx + 6, 154), "\u2014 the overlay is the RAW pair; the numbers beside it "
           "are residuals, so a letter can show pink and still read \u22120%.",
           font=_ui(16), fill=(120, 120, 120))
    d.text((GX, 182), f"Albo's nib sits at {nibA:.0f}° over the whole alphabet "
           f"and its contrast is {conA:.2f}:1.   Coelacanth's nib {nibC:.0f}°, "
           f"contrast {conC:.2f}:1.   Each specimen below is UNSHEARED, as measured.",
           font=_ui(16), fill=(88, 88, 88))

    for (name, _), cx in zip(cols, xs):
        if name:
            d.text((cx, HEAD - 26), name, font=_ui(15, True), fill=(55, 55, 55))
    d.text((VX, HEAD - 26), "what could be improved", font=_ui(15, True),
           fill=(55, 55, 55))
    d.line([(GX, HEAD - 6), (W - GX, HEAD - 6)], fill=(140, 140, 140), width=2)

    lay = {(f, ch): layer(t, ch, s, XHP)
           for f, t, s in (("A", albo_ttf, albo_slant), ("C", coel_ttf, coel_slant))
           for ch in order}
    mono, monob = _mono(17), _ui(16, True)

    def blit(px0, py0, m, colour, alpha):
        h, w = m.shape
        arr = np.asarray(im).copy()
        y0, x0 = max(0, py0), max(0, px0)
        y1, x1 = min(arr.shape[0], py0 + h), min(arr.shape[1], px0 + w)
        if y1 <= y0 or x1 <= x0:
            return
        sub = m[y0 - py0:y1 - py0, x0 - px0:x1 - px0]
        reg = arr[y0:y1, x0:x1].astype(float)
        reg[sub] = reg[sub] * (1 - alpha) + np.array(colour, float) * alpha
        arr[y0:y1, x0:x1] = reg.astype(np.uint8)
        im.paste(Image.fromarray(arr))

    for i, ch in enumerate(order):
        y = HEAD + i * ROWH
        base = y + int(ROWH * 0.68)
        sc = V[ch]["score"]
        if i % 2 == 0:
            d.rectangle([GX, y, W - GX, y + ROWH - 1], fill=(250, 250, 249))
        bar = ((120, 172, 118) if sc < MATCH else
               (196, 74, 58) if sc >= WORK else (223, 176, 84))
        d.rectangle([GX, y + 2, GX + 7, y + ROWH - 3], fill=bar)
        d.text((xs[0] + 8, base - 14), f"{i + 1}", font=_ui(16), fill=(150, 150, 150))
        d.text((xs[1] + 6, base - 24), ch, font=_ui(30, True), fill=(25, 25, 25))
        d.text((xs[1] + 4, base + 8), f"{sc:.1f}", font=_ui(12), fill=(165, 165, 165))

        LC, LA = lay[("C", ch)], lay[("A", ch)]
        for cx, L in ((xs[2], LC), (xs[3], LA)):
            if L:
                blit(int(cx + (CELL - L[0].shape[1]) / 2), int(base - L[1]),
                     L[0], (25, 25, 25), 1.0)
        rw = max(LC[0].shape[1] if LC else 0, LA[0].shape[1] if LA else 0)
        if LC:
            blit(int(xs[4] + (CELL - rw) / 2 + (rw - LC[0].shape[1]) / 2),
                 int(base - LC[1]), LC[0], (240, 138, 138), 1.0)
        if LA:
            m = LA[0]
            ox = int(xs[4] + (CELL - rw) / 2 + (rw - m.shape[1]) / 2)
            oy = int(base - LA[1])
            blit(ox, oy, m, (18, 18, 18), 0.46)
            # ...and Albo's own CONTOUR solid on top. A flat alpha blend alone
            # made the two letters one mud-coloured shape at 42 px x-height;
            # the eye needs one of the two edges to be a line it can follow.
            e = m.copy()
            e[1:-1, 1:-1] &= (m[:-2, 1:-1] & m[2:, 1:-1] &
                              m[1:-1, :-2] & m[1:-1, 2:])
            blit(ox, oy, m & ~e, (12, 12, 12), 1.0)

        r = res[ch]

        def cell(k, txt, bad, dx=4):
            d.text((xs[k] + dx, base - 11), txt, font=(monob if bad else mono),
                   fill=((158, 44, 32) if bad else (125, 125, 125)))

        pw = 100 * (math.exp(r["lw_r"]) - 1)
        cell(5, f"{pw:+.0f}%", abs(pw) >= 9)
        if r["lt_r"] == r["lt_r"]:
            pt = 100 * (math.exp(r["lt_r"]) - 1)
            cell(6, f"{pt:+.0f}%", abs(pt) >= 12)
        else:
            cell(6, "  –", False)
        ca, cc = A[ch]["contrast"], C[ch]["contrast"]
        cell(7, f"{ca:.1f}/{cc:.1f}" if ca == ca else "   –",
             ca == ca and cc == cc and abs(math.log(ca / cc)) >= 0.33)
        e = V[ch]["pen_excess"]
        cell(8, f"{e:+.0f}°" if e == e else "  –", e == e and e >= 14)
        n = max(0, nA.get(ch, 0) - nC.get(ch, 0))
        cell(9, f"{nA.get(ch,0)}/{nC.get(ch,0)}", n > 0, dx=8)

        if sc < MATCH:
            d.text((VX, base - 11), "matches — nothing to do",
                   font=_ui(18), fill=(72, 132, 70))
        else:
            ts = [t[2] for t in V[ch]["terms"] if t[0] >= 0.75][:3] or \
                 [V[ch]["terms"][0][2]]
            for j, t in enumerate(ts):
                d.text((VX, base - 30 + j * 22), "• " + t, font=_ui(17),
                       fill=(35, 35, 35) if j == 0 else (118, 118, 118))
        d.line([(GX, y + ROWH - 1), (W - GX, y + ROWH - 1)], fill=(233, 233, 231))

    fy = HEAD + ROWH * len(order) + 26
    d.line([(GX, fy - 12), (W - GX, fy - 12)], fill=(140, 140, 140), width=2)
    for j, s in enumerate([
        "contrast is Albo/Coelacanth, stem over hairline (85th percentile of ridge "
        "thickness over the 15th) — NOT read off the direction profile, where a "
        "serif tip holding one bin wins the argmin and reported Albo's Y at 22:1.",
        "ntch is the concave-vertex count on the designed outline, Albo/Coelacanth, "
        "and only an EXCESS is flagged: Coelacanth has 60 to Albo's 35 and its eight "
        "largest are the inner vertices of V W M N w, which are correct.",
        "Albo is not a Coelacanth clone — it is aimed at metal letterpress, and "
        "width, weight and proportion differences may be deliberate. A stroke that "
        "contradicts its own pen is not.",
        "This table is SHAPE only. Albo's ink is 10% narrower than Coelacanth's "
        "but its advances are only 3% narrower, so it is the more loosely fitted "
        "face \u2014 fitting is measured in the doc, not here.",
        "method, negative results and what this could not measure: "
        "docs/albo-vs-coelacanth.md   ·   tools/wedge_serif/cmp_vs_coelacanth.py"
        "   ·   2026-09-17",
    ]):
        d.text((GX, fy + j * 24), s, font=_ui(16),
               fill=(112, 112, 112) if j < 3 else (150, 150, 150))
    im.save(path)
    return path


# ------------------------------------------------------------------------ main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--albo", required=True)
    ap.add_argument("--px", type=int, default=420)
    ap.add_argument("--albo-slant", type=float, default=13.0,
                    help="the BUILD shear, not a measurement (default 13)")
    ap.add_argument("--png", default=None)
    ap.add_argument("--json", default=None)
    a = ap.parse_args()

    coel, cs = RR.path("Coelacanth"), RR.slant("Coelacanth")   # 14.5, post says 0
    A = {ch: measure(a.albo, ch, a.albo_slant, a.px) for ch in GLYPHS}
    C = {ch: measure(coel, ch, cs, a.px) for ch in GLYPHS}
    nibA, conA = face_nib(A)
    nibC, conC = face_nib(C)
    nA, nC = notches(a.albo), notches(coel)
    res = residuals(A, C)
    V = verdicts(res, A, C, nibA, nibC, nA, nC)
    order = sorted(res, key=lambda c: -V[c]["score"])

    print(f"\n  Albo nib {nibA:.0f}° contrast {conA:.2f}:1     "
          f"Coelacanth nib {nibC:.0f}° contrast {conC:.2f}:1")
    print(f"\n  {'ch':4}{'score':>7}{'wid':>7}{'stem':>7}{'contrast':>11}"
          f"{'pen':>7}{'ntch':>8}   verdict")
    for ch in order:
        r, e = res[ch], V[ch]["pen_excess"]
        pt = f"{100*(math.exp(r['lt_r'])-1):+.0f}%" if r["lt_r"] == r["lt_r"] else "-"
        ca, cc = A[ch]["contrast"], C[ch]["contrast"]
        t = ("matches" if V[ch]["score"] < MATCH else
             ("; ".join(x[2] for x in V[ch]["terms"] if x[0] >= 0.75)
              or V[ch]["terms"][0][2])[:110])
        print(f"  {ch:4}{V[ch]['score']:7.1f}"
              f"{100*(math.exp(r['lw_r'])-1):+6.0f}%{pt:>7}"
              f"{(f'{ca:.1f}/{cc:.1f}' if ca == ca else '-'):>11}"
              f"{(f'{e:+.0f}' if e == e else '-'):>7}"
              f"{nA[ch]:5d}/{nC[ch]:<2d}   {t}")
    nm = sum(1 for c in order if V[c]["score"] < MATCH)
    nw = sum(1 for c in order if V[c]["score"] >= WORK)
    print(f"\n  {nm} of {len(order)} match and need nothing; {nw} need real work.\n")

    if a.json:
        slim = {f: {c: {k: v for k, v in M[c].items() if k not in ("ang", "th")}
                    for c in M if M[c]} for f, M in (("albo", A), ("coel", C))}
        json.dump(dict(**slim, res=res, nA=nA, nC=nC, nibA=nibA, nibC=nibC,
                       conA=conA, conC=conC, order=order,
                       score={c: V[c]["score"] for c in V},
                       pen_excess={c: V[c]["pen_excess"] for c in V},
                       terms={c: [[t[1], t[2], t[0]] for t in V[c]["terms"]]
                              for c in V}),
                  open(a.json, "w"), indent=1, default=float)
    if a.png:
        render(a.png, order, A, C, res, V, nA, nC, nibA, nibC, conA, conC,
               a.albo, coel, cs, a.albo_slant)
        print(f"  wrote {a.png}\n")


if __name__ == "__main__":
    main()
