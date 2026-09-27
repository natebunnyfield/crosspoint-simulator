#!/usr/bin/env python3
"""The APOSTROPHE against the word image it sits in (2026-09-26).

Owner 2026-09-26: *"reduce apostrophe to match rest of word image"*.

Every font -- Albo and the references alike -- is rasterized UNHINTED
(FreeType, FT_LOAD_NO_HINTING, as the reader renders Albo since round 401)
at a large ppem and read back the same way. Every figure is normalized to
that font's own x-height (from its 'x') or its own lowercase stem (the 'l'
at half the x-height), so a reference is compared "scaled to Albo's
x-height" without rescaling anything.

Horizontal runs, heights and areas are all invariant under a horizontal
shear, so the italics need no unshearing for any column except bbox width.

    python3 instruments/apos_measure.py [--albo DIR] [--json OUT]
"""
import argparse, json, os, sys
import numpy as np
import freetype

PPEM = 1000
HOME = os.path.expanduser("~/Library/Fonts")
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

REFS_ROMAN = [
    ("Palatino", "/System/Library/Fonts/Palatino.ttc", 0),
    ("Charter", "/System/Library/Fonts/Supplemental/Charter.ttc", 0),
    ("Georgia", "/System/Library/Fonts/Supplemental/Georgia.ttf", 0),
    ("Baskerville", "/System/Library/Fonts/Supplemental/Baskerville.ttc", 0),
    ("Times", "/System/Library/Fonts/Supplemental/Times New Roman.ttf", 0),
    ("Pagella", f"{HOME}/texgyrepagella-regular.otf", 0),
]
REFS_ITALIC = [
    ("Palatino It", "/System/Library/Fonts/Palatino.ttc", 1),
    ("Charter It", "/System/Library/Fonts/Supplemental/Charter.ttc", 1),
    ("Georgia It", "/System/Library/Fonts/Supplemental/Georgia Italic.ttf", 0),
    ("Flanker Griffo It", f"{HERE}/refs/flanker-griffo-italic.otf", 0),
    ("Pagella It", f"{HERE}/refs/texgyrepagella-italic.otf", 0),
    ("Poetica", f"{HERE}/refs/poetica-std-regular.otf", 0),
]


def raster(face, ch):
    """(mask, baseline row, left x) of one glyph, unhinted, 1 px = 1/PPEM em."""
    gi = face.get_char_index(ord(ch))
    if not gi:
        return None
    face.load_glyph(gi, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING)
    b = face.glyph.bitmap
    if not (b.rows and b.width):
        return None
    a = np.frombuffer(bytes(b.buffer), np.uint8).reshape(b.rows, abs(b.pitch))[:, :b.width]
    return a >= 128, face.glyph.bitmap_top


def max_run(m, rows=None):
    best = 0
    for r in (m if rows is None else m[rows]):
        d = np.diff(np.concatenate([[0], r.astype(np.int8), [0]]))
        s, e = np.nonzero(d == 1)[0], np.nonzero(d == -1)[0]
        if len(s):
            best = max(best, int((e - s).max()))
    return best


def measure(name, path, idx):
    face = freetype.Face(path, index=idx)
    face.set_pixel_sizes(0, PPEM)
    xm, xt = raster(face, "x"); xh = xm.shape[0]    # x-height in px (overshoot of an x is ~0)
    lm, lt = raster(face, "l")
    row = lt - int(xh * 0.5)                          # half the x-height above the baseline
    stem = max_run(lm, slice(row - 3, row + 4))
    R = {"font": name, "xh": xh, "stem_xh": stem / xh}

    def mark(ch):
        r = raster(face, ch)
        if r is None:
            return None
        m, top = r
        ys, xs = np.nonzero(m)
        h = ys.max() - ys.min() + 1; w = xs.max() - xs.min() + 1
        return dict(area=m.sum() / xh ** 2, h=h / xh, w=w / xh, head=max_run(m) / stem,
                    top=top / xh, bot=(top - m.shape[0]) / xh, px=m.sum())

    for ch, tag in (("’", "apos"), ("'", "straight"), (".", "period"), (",", "comma")):
        R[tag] = mark(ch)
    # the i's tittle: the component above the first all-white row over the stem
    im, it = raster(face, "i")
    rows = im.any(1); first = int(np.argmax(rows))
    empty = [y for y in range(first, len(rows)) if not rows[y]]
    if empty:
        cut = empty[0]
        tm = im[:cut]
        R["tittle"] = dict(area=tm.sum() / xh ** 2, head=max_run(tm) / stem, px=int(tm.sum()))
    nm, _ = raster(face, "n"); om, _ = raster(face, "o")
    R["n_area"] = nm.sum() / xh ** 2; R["o_area"] = om.sum() / xh ** 2
    a = R["apos"]
    if a:
        R["apos_over_period"] = a["px"] / R["period"]["px"]
        R["apos_over_comma"] = a["px"] / R["comma"]["px"]
        R["apos_over_n"] = a["area"] / R["n_area"]
        if R["straight"]:
            R["straight_over_n"] = R["straight"]["area"] / R["n_area"]
        if "tittle" in R:
            R["apos_over_tittle"] = a["px"] / R["tittle"]["px"]
    return R


COLS = [
    ("apos.h", "’ height /xh"), ("apos.w", "’ width /xh"), ("apos.area", "’ ink /xh²"),
    ("apos.head", "’ head /stem"), ("apos.top", "’ top /xh"), ("apos.bot", "’ foot /xh"),
    ("apos_over_n", "’ ink /n"), ("apos_over_period", "’ ink /."), ("apos_over_comma", "’ ink /,"),
    ("apos_over_tittle", "’ ink /tittle"),
    ("straight.h", "' height /xh"), ("straight_over_n", "' ink /n"), ("straight.area", "' ink /xh²"), ("straight.head", "' head /stem"),
    ("period.head", ". dia /stem"), ("comma.h", ", height /xh"), ("stem_xh", "stem /xh"),
]


def get(R, k):
    v = R
    for p in k.split("."):
        v = v.get(p) if isinstance(v, dict) else None
        if v is None:
            return None
    return v


def table(rows, title):
    out = [f"\n{title}", "| font | " + " | ".join(c[1] for c in COLS) + " |",
           "|---|" + "---|" * len(COLS)]
    for R in rows:
        out.append(f"| {R['font']} | " + " | ".join(
            "—" if get(R, k) is None else f"{get(R, k):.3f}" for k, _ in COLS) + " |")
    return "\n".join(out)


def median_row(rows, name):
    M = {"font": name}
    for k, _ in COLS:
        vs = [get(R, k) for R in rows if get(R, k) is not None]
        if vs:
            d = M
            ps = k.split(".")
            for p in ps[:-1]:
                d = d.setdefault(p, {})
            d[ps[-1]] = float(np.median(vs))
    return M


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--albo", action="append", default=[], help="DIR[:label] holding Albo-*.ttf; repeatable")
    ap.add_argument("--json")
    a = ap.parse_args()
    res = {}
    for style, refs, cuts in (("roman", REFS_ROMAN, ("Regular",)), ("italic", REFS_ITALIC, ("Italic",))):
        rows = []
        for spec in a.albo:
            d, _, lab = spec.partition(":")
            for c in cuts:
                rows.append(measure(f"Albo {c} {lab}".strip(), os.path.join(d, f"Albo-{c}.ttf"), 0))
        refrows = [measure(*r) for r in refs if os.path.exists(r[1])]
        rows += refrows + [median_row(refrows, "reference median")]
        res[style] = rows
        print(table(rows, style.upper()))
    if a.json:
        json.dump(res, open(a.json, "w"), indent=1, default=float)


if __name__ == "__main__":
    main()
