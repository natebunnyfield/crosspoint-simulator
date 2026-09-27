"""Trace a letter in the reference serifs into Albo's units, for the
poor-characters pass (2026-09-26; docs/albo-poor-characters-2026-09-26.md).

Owner 2026-09-26: *"give me options for the most critically poor characters
(all faces). trace other reference fonts and come up original solutions too."*

TRACING IS MEASUREMENT, NOT COPYING -- the rule of fig27_trace.py, whose
`Face` this reuses: every glyph is rendered UNHINTED, UNSHEARED by its
measured slant, scaled so the face's x-height lands on Albo's 429, at 2 px per
unit. What comes out is a description in Albo's units -- ink extent, the
stroke thicknesses of named regions over the SAME face's n stem, and a few
per-letter skeleton numbers -- and the arms in outlines/glyphs are Albo's own
pen construction set to those numbers. No outline point of a reference is used.

The same function reads an Albo build, so arm and reference go through one
instrument.

    PYTHON_GIL=0 python3 instruments/poor_trace.py y --cut Regular [--albo DIR ...]
    PYTHON_GIL=0 python3 instruments/poor_trace.py y --cut Regular --sheet out.png

Numbers per letter (units Albo, xh 429; `_n` = over the face's n stem):
  w, top, bot      ink extent (unsheared)
  thin_n, med_n, thick_n   p10 / p50 / p90 of the chamfer ridge's thickness
  cut              p90 / p10, the fit audit's contrast axis
  rows             the letter's ink runs at named heights (see ROWS), as
                   (x0, x1) pairs from the ink's left edge -- the skeleton
  plus per-letter extras (EXTRAS)
"""
import argparse, json, math, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from fig27_trace import Face, SUP, PAL, RF, XH_ALBO, PX  # noqa: E402

ROMAN = [("Georgia", SUP + "Georgia.ttf", 0), ("Charter", SUP + "Charter.ttc", 0),
         ("Times", SUP + "Times New Roman.ttf", 0), ("Baskerville", SUP + "Baskerville.ttc", 0),
         ("Hoefler", SUP + "Hoefler Text.ttc", 0), ("Palatino", PAL, 0)]
BOLD = [("Georgia", SUP + "Georgia Bold.ttf", 0), ("Charter", SUP + "Charter.ttc", 3),
        ("Times", SUP + "Times New Roman Bold.ttf", 0), ("Baskerville", SUP + "Baskerville.ttc", 1),
        ("Hoefler", SUP + "Hoefler Text.ttc", 1), ("Palatino", PAL, 2)]
ITALIC = [("Georgia It", SUP + "Georgia Italic.ttf", 0), ("Charter It", SUP + "Charter.ttc", 1),
          ("Palatino It", PAL, 1), ("Flanker", RF + "flanker-griffo-italic.otf", 0),
          ("Poetica", RF + "poetica-std-regular.otf", 0), ("Pagella", RF + "texgyrepagella-italic.otf", 0)]
BOLDITALIC = [("Georgia BI", SUP + "Georgia Bold Italic.ttf", 0), ("Charter BI", SUP + "Charter.ttc", 2),
              ("Palatino BI", PAL, 3), ("Flanker B", RF + "flanker-griffo-bold-italic.otf", 0),
              ("Times BI", SUP + "Times New Roman Bold Italic.ttf", 0), ("Hoefler BI", SUP + "Hoefler Text.ttc", 3)]
PANEL = {"Regular": ROMAN, "Bold": BOLD, "Italic": ITALIC, "BoldItalic": BOLDITALIC}
SLANT_CH = {"Hoefler Text.ttc": "I"}   # fig27_trace: Hoefler Italic's l is not a bare stem


def face(path, idx, italic):
    ch = "I" if (italic and path.endswith("Hoefler Text.ttc")) else "l"
    return Face(path, idx, slant=None if italic else 0.0, slant_ch=ch)


def ridge_thickness(m):
    """Chamfer ridge thickness (2 x distance) at the ridge pixels, in units."""
    from scipy import ndimage
    d = ndimage.distance_transform_edt(m)
    mx = ndimage.maximum_filter(d, size=3)
    r = (d >= mx - 1e-6) & (d > 1.5)
    return 2 * d[r] / PX


def nstem(F):
    a, x0, yt, _ = F.mask("n")
    rows = a[int(a.shape[0] * 0.55)]
    runs = _runs(rows)
    return (runs[0][1] - runs[0][0]) / PX if runs else float("nan")


def _runs(row):
    r, on = [], None
    for i, v in enumerate(row):
        if v and on is None: on = i
        if not v and on is not None: r.append((on, i)); on = None
    if on is not None: r.append((on, len(row)))
    return r


def measure(F, ch, rows=(0.9, 0.7, 0.5, 0.3, 0.1, -0.1, -0.3, -0.5)):
    a, x0, yt, adv = F.mask(ch)
    H, W = a.shape
    ys, xs = np.nonzero(a)
    left = xs.min()
    th = ridge_thickness(a); n = nstem(F)
    out = {"w": (xs.max() - xs.min()) / PX, "top": yt, "bot": yt - H / PX, "adv": adv,
           "lsb": x0 + left / PX, "rsb": adv - (x0 + (xs.max() + 1) / PX), "nstem": n,
           "thin_n": np.percentile(th, 10) / n, "med_n": np.percentile(th, 50) / n,
           "thick_n": np.percentile(th, 90) / n, "cut": np.percentile(th, 90) / np.percentile(th, 10)}
    rr = {}
    for f in rows:                         # f = fraction of x-height (negative: descender)
        y = int(round((yt - f * XH_ALBO) * PX))
        if 0 <= y < H:
            rr[f"{f:+.1f}"] = [(round((s - left) / PX), round((e - left) / PX)) for s, e in _runs(a[y])]
    out["rows"] = rr
    return out


def sheet(entries, out, pad=12):
    """entries: [(label, Face, ch)]. One strip, letters at a shared x-height
    and a shared baseline, black on paper, label as a thin tick row under each
    (labels are printed in the doc, the strip is for the eye)."""
    from PIL import Image, ImageDraw
    ims = []
    for label, F, ch in entries:
        a, x0, yt, adv = F.mask(ch)
        img = Image.fromarray(((~a) * 255).astype(np.uint8))
        ims.append((label, img, yt))
    # shared baseline: align yt (units above baseline) at 2 px/unit
    top = max(yt for _, _, yt in ims)
    bot = max(im.height / PX - yt for _, im, yt in ims)
    Hh = int((top + bot) * PX) + 2 * pad + 40
    Ww = sum(im.width for _, im, _ in ims) + pad * (len(ims) + 1)
    canvas = Image.new("L", (Ww, Hh), 255); d = ImageDraw.Draw(canvas)
    x = pad
    for label, im, yt in ims:
        canvas.paste(im, (x, pad + int((top - yt) * PX)))
        d.text((x, Hh - 34), label[:14], fill=0)
        x += im.width + pad
    base = pad + int(top * PX)
    for yy in (base, base - int(XH_ALBO * PX)):
        for xx in range(0, Ww, 6): canvas.putpixel((xx, yy), 160)
    canvas.save(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ch")
    ap.add_argument("--cut", default="Regular")
    ap.add_argument("--albo", action="append", default=[], help="LABEL=DIR of an Albo build")
    ap.add_argument("--sheet")
    ap.add_argument("--json")
    a = ap.parse_args()
    italic = "Italic" in a.cut
    entries = []
    for spec in a.albo:
        lab, d = spec.split("=", 1)
        entries.append((lab, face(os.path.join(d, f"Albo-{a.cut}.ttf"), 0, italic), a.ch))
    for lab, p, i in PANEL[a.cut]:
        try:
            entries.append((lab, face(p, i, italic), a.ch))
        except Exception as e:
            print("skip", lab, e, file=sys.stderr)
    res = {}
    for lab, F, ch in entries:
        m = measure(F, ch); res[lab] = m
        print(f"{lab:13s} w {m['w']:5.0f} top {m['top']:5.0f} bot {m['bot']:5.0f} lsb {m['lsb']:4.0f} rsb {m['rsb']:4.0f} "
              f"n {m['nstem']:4.0f} thin {m['thin_n']:.2f} med {m['med_n']:.2f} thick {m['thick_n']:.2f} cut {m['cut']:.2f}  slant {F.slant:.1f}")
        for k, v in m["rows"].items():
            print(f"      {k}: {v}")
    if a.sheet: sheet(entries, a.sheet)
    if a.json: json.dump(res, open(a.json, "w"), indent=1, default=float)


if __name__ == "__main__":
    main()
