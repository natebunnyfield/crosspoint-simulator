#!/usr/bin/env python3
"""HOW HEAVY IS A BOLD -- the stem, the cap stem and the hairline of a text
face's BOLD against its own REGULAR, measured the same way on every face.

Written 2026-09-19 for the bold masters: `FJORD_STEM` is a number and the only
honest way to pick it is to measure what real bold text faces do, not to scale
the regular by a factor that sounded right. (The retired variable font's ladder
put Bold at stem 107 against a Regular of 66.9 -- a 1.60x jump -- and today's
Medium is 84, so that ladder cannot be followed blind.)

THE MEASURES, all scale-free ratios so the render size cannot enter them:

  stem/xh     the `l`'s stem over the `x`'s ink height. The stem is the MEDIAN
              of the single-run width over the middle 40% of the l's ink, which
              is pure stem in every serif face (the serifs are at the ends and
              the entasis is symmetric about the middle).
  cap/capH    the `H`'s stem over the H's own ink height. Rows with exactly two
              ink runs are stems; the crossbar's rows have one and drop out.
  hair/stem   the `o`'s thinnest bowl over that same stem -- the face's own
              contrast. Measured down COLUMNS in the central 30% of the o, where
              the bowl's top and bottom are two runs and the thinner is the
              hairline.
  bold/reg    the same measure on the two files, which is the number a weight
              axis actually has to choose.

THE ONE TRAP, and it is the one `refs_registry.py` records: an italic's stem is
wider along a scanline than it is across the stroke, by 1/cos(slant), and a
font's DECLARED italicAngle is not its slant (two of the five reference italics
declare zero). So the slant is MEASURED here, off the `l` and only the `l`, as
the regression of the stem's row-centre against the row -- and the horizontal
run is multiplied by cos(that) before it is called a stem. An unmeasured italic
reads 3-4% heavy, which is the size of the decision being made.

    PYTHON_GIL=0 python3 cmp_bold_stem.py                    # the reference table
    PYTHON_GIL=0 python3 cmp_bold_stem.py --ttf X.ttf        # one file
    PYTHON_GIL=0 python3 cmp_bold_stem.py --albo DIR ...     # Albo build dirs
"""
import argparse, math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

SUP = "/System/Library/Fonts/Supplemental"
LOC = os.path.expanduser("~/src/crosspoint-reader/lib/EpdFont/local_fonts")
REFS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "refs")

# (family, upright file/idx, bold file/idx) -- uprights first, then italics.
ROMAN = [
    ("Georgia",        (f"{SUP}/Georgia.ttf", 0),        (f"{SUP}/Georgia Bold.ttf", 0)),
    ("Times New Roman",(f"{SUP}/Times New Roman.ttf", 0),(f"{SUP}/Times New Roman Bold.ttf", 0)),
    ("Charter",        (f"{SUP}/Charter.ttc", 0),         (f"{SUP}/Charter.ttc", 3)),
    ("Baskerville",    (f"{SUP}/Baskerville.ttc", 0),     (f"{SUP}/Baskerville.ttc", 1)),
    ("Hoefler Text*",  (f"{SUP}/Hoefler Text.ttc", 0),    (f"{SUP}/Hoefler Text.ttc", 1)),
    ("Dante MT",       (f"{LOC}/DanteMT-Regular.ttf", 0), (f"{LOC}/DanteMT-Bold.ttf", 0)),
    ("DTL Fleischmann",(f"{LOC}/DTLFleischmann-Regular.ttf", 0), (f"{LOC}/DTLFleischmann-Bold.ttf", 0)),
    ("DTL Romulus",    (f"{LOC}/DTLRomulus-Regular.otf", 0), (f"{LOC}/DTLRomulus-Bold.otf", 0)),
    ("Edgar",          (f"{LOC}/Edgar-Regular.ttf", 0),   (f"{LOC}/Edgar-Bold.ttf", 0)),
    ("Van den Keere",  (f"{LOC}/VandenKeere-Regular.otf", 0), (f"{LOC}/VandenKeere-Bold.otf", 0)),
    ("Venetian 301",   (f"{LOC}/Venetian301-Regular.otf", 0), (f"{LOC}/Venetian301-Bold.otf", 0)),
    ("Warbler Text",   (f"{LOC}/WarblerText-Regular.otf", 0), (f"{LOC}/WarblerText-Bold.otf", 0)),
]
ITALIC = [
    ("Flanker Griffo", (f"{REFS}/flanker-griffo-italic.otf", 0), (f"{REFS}/flanker-griffo-bold-italic.otf", 0)),
    ("Georgia",        (f"{SUP}/Georgia Italic.ttf", 0),  (f"{SUP}/Georgia Bold Italic.ttf", 0)),
    ("Times New Roman",(f"{SUP}/Times New Roman Italic.ttf", 0), (f"{SUP}/Times New Roman Bold Italic.ttf", 0)),
    ("Charter",        (f"{SUP}/Charter.ttc", 1),          (f"{SUP}/Charter.ttc", 2)),
    ("Baskerville",    (f"{SUP}/Baskerville.ttc", 2),      (f"{SUP}/Baskerville.ttc", 3)),
    ("Dante MT",       (f"{LOC}/DanteMT-Italic.ttf", 0),  (f"{LOC}/DanteMT-BoldItalic.ttf", 0)),
    ("DTL Fleischmann",(f"{LOC}/DTLFleischmann-Italic.ttf", 0), (f"{LOC}/DTLFleischmann-BoldItalic.ttf", 0)),
    ("DTL Romulus",    (f"{LOC}/DTLRomulus-Italic.otf", 0), (f"{LOC}/DTLRomulus-BoldItalic.otf", 0)),
    ("Edgar",          (f"{LOC}/Edgar-Italic.ttf", 0),    (f"{LOC}/Edgar-BoldItalic.ttf", 0)),
    ("Venetian 301",   (f"{LOC}/Venetian301-Italic.otf", 0), (f"{LOC}/Venetian301-BoldItalic.otf", 0)),
    ("Warbler Text",   (f"{LOC}/WarblerText-Italic.otf", 0), (f"{LOC}/WarblerText-BoldItalic.otf", 0)),
]

PX = 900          # em size; every measure is a ratio, so this is precision only


def _mask(path, idx, ch):
    f = ImageFont.truetype(path, PX, index=idx)
    W = H = PX * 3
    im = Image.new("L", (W, H), 255)
    ImageDraw.Draw(im).text((W * 0.35, H * 0.7), ch, font=f, fill=0, anchor="ls")
    a = np.asarray(im) < 128
    ys, xs = np.nonzero(a)
    if not len(ys): return None
    return a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def _runs(line):
    """(start, length) of every True run in a 1-D bool array."""
    out = []; s = None
    for i, v in enumerate(line):
        if v and s is None: s = i
        elif not v and s is not None: out.append((s, i - s)); s = None
    if s is not None: out.append((s, len(line) - s))
    return out


def _slant_and_stem(m):
    """Slant in degrees and stem width, off a bare-stem raster (l or I)."""
    H = m.shape[0]
    lo, hi = int(H * 0.30), int(H * 0.70)
    ws, cs, ys = [], [], []
    for y in range(lo, hi):
        r = _runs(m[y])
        if len(r) != 1: continue
        ws.append(r[0][1]); cs.append(r[0][0] + r[0][1] / 2.0); ys.append(y)
    if len(ws) < 8: return 0.0, float("nan")
    # slant: regression of stem centre against row (y grows DOWNWARD in the
    # raster, so a positive forward slope needs the sign flipped)
    ys = np.array(ys, float); cs = np.array(cs, float)
    k = np.polyfit(ys, cs, 1)[0]
    deg = math.degrees(math.atan(-k))
    return deg, float(np.median(ws)) * math.cos(math.radians(deg))


def _cap_stem(m):
    out = []
    for y in range(m.shape[0]):
        r = _runs(m[y])
        if len(r) == 2: out.append(min(r[0][1], r[1][1]))
    return float(np.median(out)) if len(out) >= 8 else float("nan")


def _hair(m):
    """The o's thinnest bowl: shortest of the two vertical runs down the
    central columns."""
    W = m.shape[1]
    lo, hi = int(W * 0.35), int(W * 0.65)
    out = []
    for x in range(lo, hi):
        r = _runs(m[:, x])
        if len(r) == 2: out.append(min(r[0][1], r[1][1]))
    return float(np.median(out)) if out else float("nan")


def _adv(path, idx, s):
    return ImageFont.truetype(path, PX, index=idx).getlength(s)


def _band(path, idx, chars):
    """The x-height (or cap height) as the SMALLEST ink height among several
    letters that all sit on the same line.

    THE INSTRUMENT BUG THIS EXISTS FOR, found 2026-09-19 and it inverted the
    whole bold decision. The x-height was read off the `x` alone, and **Albo's
    x has flaring wedge serifs that overshoot its own x-height** -- ink 481
    units against a declared 429, and it GROWS with the stem (493 at 107, 506
    at 140), so the denominator moved with the thing being measured and every
    Albo stem/xh came back 12-15% light while every reference (whose x IS flat)
    came back right. Albo Medium read 0.1663 where it is 0.1865, which is the
    difference between "lighter than every regular measured" and "the median
    regular". The `z` is flat in Albo and overshoots in Van den Keere; the `x`
    is flat in Van den Keere and overshoots in Albo -- so no single letter is
    safe and the MINIMUM over several is. Declared OS/2 values are no fallback
    either: Dante MT declares sxHeight 403 on a 2048-upm body (it is a 1000-upm
    number left in the table), which is a plausible-looking 5x error."""
    hs = []
    for ch in chars:
        m = _mask(path, idx, ch)
        if m is not None: hs.append(m.shape[0])
    if not hs: raise RuntimeError("no ink for " + chars)
    return min(hs)


def measure(path, idx=0):
    ml = _mask(path, idx, "l")
    mH = _mask(path, idx, "H"); mo = _mask(path, idx, "o")
    if ml is None or mH is None: raise RuntimeError("no ink")
    slant, stem = _slant_and_stem(ml)
    cs = _cap_stem(mH)
    cap = _band(path, idx, "HIE")
    xh = _band(path, idx, "xzvw")
    hair = _hair(mo) if mo is not None else float("nan")
    return dict(slant=slant, stem=stem, cap_stem=cs, cap=cap, xh=xh, hair=hair,
                stem_xh=stem / xh, cap_ratio=cs / cap, contrast=hair / stem,
                cap_over_lc=cs / stem,
                # WIDTH: the n's advance over the x-height, and the o's ink
                # box. A bold that is only a fatter regular has the same n
                # advance; a real bold buys room for the heavier stems.
                n_adv=_adv(path, idx, "n") / xh,
                n_em=_adv(path, idx, "n") / PX,
                o_wh=(mo.shape[1] / mo.shape[0]) if mo is not None else float("nan"))


def row(name, m, ref=None):
    s = (f"{name:<22} slant {m['slant']:>5.1f}  stem/xh {m['stem_xh']:.4f}"
         f"  capstem/capH {m['cap_ratio']:.4f}  hair/stem {m['contrast']:.3f}"
         f"  capstem/stem {m['cap_over_lc']:.3f}  n_adv/xh {m['n_adv']:.3f}"
         f"  o w/h {m['o_wh']:.3f}  n/em {m['n_em']:.3f}")
    if ref:
        s += (f"  bold/reg stem {m['stem']/ref['stem']:.3f}"
              f" adv {m['n_adv']/ref['n_adv']:.3f}")
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ttf", action="append", default=[])
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    if a.ttf:
        for t in a.ttf:
            try: print(row(os.path.basename(t)[:22], measure(t)))
            except Exception as e: print(t, "ERR", e)
        return 0
    for label, table in (("UPRIGHT", ROMAN), ("ITALIC", ITALIC)):
        print(f"\n=== {label} ===")
        rs = []
        for fam, reg, bold in table:
            if a.only and a.only not in fam: continue
            try:
                r = measure(*reg); b = measure(*bold)
            except Exception as e:
                print(f"{fam:<22} ERR {e}"); continue
            print(row(fam + " reg", r))
            print(row(fam + " BOLD", b, r))
            rs.append((fam, r, b))
        if rs:
            print(f"  median bold stem/xh      {np.median([b['stem_xh'] for _, _, b in rs]):.4f}")
            print(f"  median bold capstem/capH {np.median([b['cap_ratio'] for _, _, b in rs]):.4f}")
            print(f"  median bold/reg stem     {np.median([b['stem']/r['stem'] for _, r, b in rs]):.3f}")
            print(f"  median bold hair/stem    {np.median([b['contrast'] for _, _, b in rs]):.3f}")
            print(f"  median reg  hair/stem    {np.median([r['contrast'] for _, r, _ in rs]):.3f}")
            print(f"  median bold/reg n adv    {np.median([b['n_adv']/r['n_adv'] for _, r, b in rs]):.3f}")
            # The garalde / humanist group Albo actually belongs with. The rest
            # of the table is transitional and Scotch, and its bolds are black.
            G = [x for x in rs if x[0] in
                 ("Dante MT", "Van den Keere", "Venetian 301", "Charter", "Flanker Griffo")]
            if G:
                print(f"  GARALDE group ({', '.join(g[0] for g in G)}):")
                print(f"    median bold stem/xh    {np.median([b['stem_xh'] for _, _, b in G]):.4f}")
                print(f"    median bold/reg stem   {np.median([b['stem']/r['stem'] for _, r, b in G]):.3f}")
                print(f"    median bold/reg n adv  {np.median([b['n_adv']/r['n_adv'] for _, r, b in G]):.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
