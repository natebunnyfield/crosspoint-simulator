"""The ampersand against its own face and against reference italics, round 377.

Owner 2026-09-24, "yes to all" -- including the long-open item that the italic
ampersand is an outlier wanting a new drawing, not a dial. This is the ruler
that says what "outlier" means, in numbers, for Albo and for every reference,
measured the SAME way on each.

Per font, on the '&':

  thirds    ink mass in the left / middle / right third of the ink box, in %.
            Two readings: `sh` as the glyph is rendered (sheared), `un` with
            the face's own slant taken out. Round 349 reported the sheared
            roman at 30.3 / 57.1 / 12.6 without saying which; both are printed
            so the known answer can be reproduced (ALBO_IT_AMP=a).
  top, bot  ink top and bottom, x the face's own x-height (measured off 'x'
            ink, never sxHeight -- two references carry a wrong one).
  capr      ink height over the face's cap height ('H' ink).
  wid       unsheared ink width, x the x-height.
  adv/o     the '&' advance over the 'o' advance.
  wt        stroke median (chamfer ridge, no percentile threshold --
            cmp_weight_survey's rule) over the median of the same measure on
            o e n c s a d g u, the body letters round 316 compared against.
  cut       the '&''s own thick/thin (90th/10th percentile along the ridge),
            and `bcut` the body letters' median cut beside it.
  col       ink area of the '&' over (ink width x ink height) -- how full its
            own box is; the body letters' median beside it as `bcol`.
  vhi       share of ink above the ink box's vertical middle, in %.

    PYTHON_GIL=0 python3 instruments/amp_measure.py FONT.ttf[:index][@slant] ...
    PYTHON_GIL=0 python3 instruments/amp_measure.py --refs --albo DIR

A slant given as @deg overrides; otherwise Albo italics take 13, the five
repo references take refs_registry's MEASURED slants, and any other italic is
measured off its 'l' with refs_registry.measure_slant (never post.italicAngle).
"""
import argparse, math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from cmp_weight_survey import chamfer, ridge_vals   # the survey's own ridge
import refs_registry as RR

PX = 300            # the x-height in pixels
BODY = "oencsadgu"

SYSTEM = [
    ("Georgia Italic", "/System/Library/Fonts/Supplemental/Georgia Italic.ttf", 0),
    ("Times New Roman Italic", "/System/Library/Fonts/Supplemental/Times New Roman Italic.ttf", 0),
    ("Palatino Italic", "/System/Library/Fonts/Palatino.ttc", 1),
    ("Hoefler Text Italic", "/System/Library/Fonts/Supplemental/Hoefler Text.ttc", 2),
    ("Baskerville Italic", "/System/Library/Fonts/Supplemental/Baskerville.ttc", 2),
]


def _font(path, idx, size):
    return ImageFont.truetype(path, size, index=idx)


def _ink(path, idx, ch, size, slant=0.0):
    f = _font(path, idx, size)
    W = H = int(size * 3.2); base = int(H * 0.66)
    im = Image.new("L", (W, H), 255)
    ImageDraw.Draw(im).text((W * 0.30, base), ch, font=f, fill=0, anchor="ls")
    if abs(slant) > 0.05:           # x_in = x + k*(y - base): k<0 removes a rightward lean
        k = -math.tan(math.radians(slant))
        im = im.transform((W, H), Image.AFFINE, (1, k, -k * base, 0, 1, 0),
                          resample=Image.BICUBIC, fillcolor=255)
    return np.asarray(im) < 128, base


def _box(a):
    ys, xs = np.nonzero(a)
    return xs.min(), xs.max() + 1, ys.min(), ys.max() + 1


def _thirds(a):
    x0, x1, _, _ = _box(a); w = x1 - x0
    col = a.sum(0)[x0:x1].astype(float); tot = col.sum()
    e = [0, w / 3, 2 * w / 3, w]
    out = []
    for i in range(3):
        lo, hi = e[i], e[i + 1]
        s = 0.0
        for j in range(int(math.floor(lo)), int(math.ceil(hi))):
            if j >= w: break
            ov = min(hi, j + 1) - max(lo, j)
            if ov > 0: s += col[j] * ov
        out.append(100.0 * s / tot)
    return out


def _ridge(a):
    PAD = 40
    x0, x1, y0, y1 = _box(a)
    m = a[max(0, y0 - PAD):y1 + PAD, max(0, x0 - PAD):x1 + PAD]
    d = chamfer(m); v = ridge_vals(m, d)
    return 2.0 * v


def size_for_xh(path, idx, px=PX):
    """Point size at which this face's 'x' ink is `px` tall."""
    a, _ = _ink(path, idx, "x", 400)
    _, _, y0, y1 = _box(a)
    return int(round(400 * px / (y1 - y0))), (y1 - y0) / 400.0


def measure(path, idx=0, slant=0.0, ch="&"):
    size, _ = size_for_xh(path, idx)
    u = 429.0 / PX                                  # report in Albo design units
    xa, base = _ink(path, idx, "x", size); _, _, xy0, xy1 = _box(xa)
    xh = xy1 - xy0
    ha, _ = _ink(path, idx, "H", size); _, _, hy0, hy1 = _box(ha)
    cap = hy1 - hy0
    sh, _ = _ink(path, idx, ch, size)
    un, base = _ink(path, idx, ch, size, slant)
    x0, x1, y0, y1 = _box(un)
    t = _ridge(un) * u
    body = []
    for b in BODY:
        ba, _ = _ink(path, idx, b, size, slant)
        tb = _ridge(ba) * u
        bx0, bx1, by0, by1 = _box(ba)
        body.append((float(np.median(tb)),
                     float(np.percentile(tb, 90) / np.percentile(tb, 10)),
                     float(ba.sum()) / ((bx1 - bx0) * (by1 - by0))))
    f = _font(path, idx, size)
    adv = f.getlength(ch) / max(1e-9, f.getlength("o"))
    mid = (y0 + y1) / 2.0
    vhi = 100.0 * un[:int(mid)].sum() / un.sum()
    return dict(
        thirds_sh=_thirds(sh), thirds_un=_thirds(un),
        top=(base - y0) / xh, bot=(base - y1) / xh, capr=(y1 - y0) / cap,
        wid=(x1 - x0) / xh, adv=adv,
        stroke=float(np.median(t)),
        wt=float(np.median(t)) / float(np.median([b[0] for b in body])),
        cut=float(np.percentile(t, 90) / np.percentile(t, 10)),
        bcut=float(np.median([b[1] for b in body])),
        col=float(un.sum()) / ((x1 - x0) * (y1 - y0)),
        bcol=float(np.median([b[2] for b in body])),
        vhi=vhi)


HDR = (f"{'face':34s} {'sheared thirds':>17s} {'unsheared thirds':>17s} "
       f"{'top':>5s} {'bot':>6s} {'capr':>5s} {'wid':>5s} {'adv/o':>5s} "
       f"{'wt':>5s} {'cut':>5s} {'bcut':>5s} {'col':>5s} {'bcol':>5s} {'vhi':>5s}")


def row(name, r):
    s = "/".join(f"{v:4.1f}" for v in r["thirds_sh"])
    u = "/".join(f"{v:4.1f}" for v in r["thirds_un"])
    return (f"{name:34s} {s:>17s} {u:>17s} {r['top']:5.2f} {r['bot']:6.2f} "
            f"{r['capr']:5.2f} {r['wid']:5.2f} {r['adv']:5.2f} {r['wt']:5.2f} "
            f"{r['cut']:5.2f} {r['bcut']:5.2f} {r['col']:5.2f} {r['bcol']:5.2f} "
            f"{r['vhi']:5.1f}")


def refs():
    out = []
    for name in ("Flanker Griffo", "Pagella", "Poetica", "Coelacanth"):
        out.append((name, RR.path(name), 0, RR.slant(name)))
    for name, p, i in SYSTEM:
        # measure_slant takes a path; a TTC's first face is not the italic, so
        # measure it here on the right index with the same rule ('l', 30/70%).
        out.append((name, p, i, _slant_l(p, i)))
    return out


def _slant_l(p, i):
    a, _ = _ink(p, i, "l", 900)
    ys = np.nonzero(a.any(1))[0]; y0, y1 = ys.min(), ys.max(); span = y1 - y0
    cs = []
    for fr in (0.30, 0.70):
        y = int(y0 + span * fr); r = np.nonzero(a[y])[0]
        cs.append(((r.min() + r.max()) / 2.0, y))
    return math.degrees(math.atan2(cs[0][0] - cs[1][0], cs[1][1] - cs[0][1]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("fonts", nargs="*")
    ap.add_argument("--refs", action="store_true")
    ap.add_argument("--albo", help="a build dir: Regular, Italic, Bold, BoldItalic")
    a = ap.parse_args()
    jobs = []
    if a.albo:
        for st, sl in (("Regular", 0), ("Italic", 13), ("Bold", 0), ("BoldItalic", 13)):
            p = os.path.join(a.albo, f"Albo-{st}.ttf")
            if os.path.exists(p): jobs.append((f"Albo {st}", p, 0, sl))
    for spec in a.fonts:
        sl = 0.0
        if "@" in spec: spec, sl = spec.rsplit("@", 1); sl = float(sl)
        idx = 0
        if ":" in spec: spec, idx = spec.rsplit(":", 1); idx = int(idx)
        jobs.append((os.path.basename(spec), spec, idx, sl))
    if a.refs: jobs += refs()
    print(HDR)
    for name, p, i, sl in jobs:
        print(row(f"{name} ({sl:.1f})", measure(p, i, sl)), flush=True)


if __name__ == "__main__":
    main()
