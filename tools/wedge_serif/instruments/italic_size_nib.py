#!/usr/bin/env python3
"""ITALIC vs ROMAN, same size (2026-09-26, owner: "check italic and roman are
using the same nib. italic seems too small").

For every roman/italic pair it measures, in 1/1000 em, from an UNHINTED
FreeType raster at 1000 ppem (so 1 px = 1/1000 em):

  xh    the x's top            cap   the H's top
  asc   the l/d/b/h top (max)  desc  the p/q bottom (min)
  stem  median horizontal ink run through i l n m u at mid x-height
  hair  the o's thinnest crossing at top and bottom (vertical run)
  wid   shaped advance per character of TEXT (HarfBuzz, kern on)
  ink   ink area per character of TEXT (em^2 x 1e3, 100 ppem unhinted)
  col   ink / (advance x xh): the colour of the x-height band
  app   xh x wid: the apparent size of a line

and prints each italic/roman ratio, then the references' median and range.

    uv run --python 3.13 --with uharfbuzz --with freetype-py --with fonttools \\
        --with numpy python instruments/italic_size_nib.py ROMAN.ttf ITALIC.ttf [label]
With no arguments it runs the reference pairs only; with --json OUT it writes
the table.
"""
import sys, os, json, statistics as st
import numpy as np
import freetype, uharfbuzz as hb

TEXT = ("It is a truth universally acknowledged, that a single man in possession of a good "
        "fortune, must be in want of a wife. However little known the feelings or views of "
        "such a man may be on his first entering a neighbourhood, this truth is so well fixed "
        "in the minds of the surrounding families, that he is considered the rightful property "
        "of some one or other of their daughters.")

SUP = "/System/Library/Fonts/Supplemental/"
DL = os.path.expanduser("~/Downloads/")
LF = os.path.expanduser("~/Library/Fonts/")
EPD = os.path.expanduser("~/src/crosspoint-reader/lib/EpdFont/scripts/downloaded_fonts/")
REFS = [
    ("Palatino", ("/System/Library/Fonts/Palatino.ttc", 0), ("/System/Library/Fonts/Palatino.ttc", 1)),
    ("Pagella", (LF + "texgyrepagella-regular.otf", 0), (LF + "texgyrepagella-italic.otf", 0)),
    ("Charter", (SUP + "Charter.ttc", 0), (SUP + "Charter.ttc", 1)),
    ("Georgia", (SUP + "Georgia.ttf", 0), (SUP + "Georgia Italic.ttf", 0)),
    ("Baskerville", (SUP + "Baskerville.ttc", 0), (SUP + "Baskerville.ttc", 2)),
    ("Hoefler Text", (SUP + "Hoefler Text.ttc", 0), (SUP + "Hoefler Text.ttc", 2)),
    ("Iowan", (SUP + "Iowan Old Style.ttc", 0), (SUP + "Iowan Old Style.ttc", 2)),
    ("Times", ("/System/Library/Fonts/Times.ttc", 0), ("/System/Library/Fonts/Times.ttc", 2)),
    ("Flanker Griffo", (LF + "flanker-griffo.regular.otf", 0), (LF + "flanker-griffo.italic.otf", 0)),
    ("Coelacanth", (EPD + "Coelacanth/Coelacanth.otf", 0), (EPD + "Coelacanth/CoelacanthItalic.otf", 0)),
    ("ITC Berkeley", (LF + "ITC Berkeley Oldstyle Medium.otf", 0), (LF + "ITC Berkeley Oldstyle Medium Italic.otf", 0)),
]


class F:
    def __init__(self, spec):
        path, idx = spec
        self.face = freetype.Face(path, index=idx)
        self.upem = self.face.units_per_EM
        blob = hb.Blob(open(path, "rb").read())
        self.hbf = hb.Font(hb.Face(blob, idx)); self.hbf.scale = (self.upem, self.upem)

    def raster(self, ch, ppem=1000):
        self.face.set_pixel_sizes(0, ppem)
        self.face.load_char(ch, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING)
        b = self.face.glyph.bitmap
        a = (np.frombuffer(bytes(b.buffer), np.uint8).reshape(b.rows, abs(b.pitch))[:, :b.width].astype(float) / 255
             if b.rows and b.width else np.zeros((0, 0)))
        return a, self.face.glyph.bitmap_left, self.face.glyph.bitmap_top

    def top(self, ch):
        a, l, t = self.raster(ch); return t

    def bottom(self, ch):
        a, l, t = self.raster(ch); return t - a.shape[0]

    def runs_at(self, ch, y):
        """horizontal ink runs (length) on the row at height y (1/1000 em)."""
        a, l, t = self.raster(ch); r = t - int(round(y))
        if r < 0 or r >= a.shape[0]: return []
        row = a[r] > 0.5; out = []; n = 0
        for v in list(row) + [False]:
            if v: n += 1
            elif n: out.append(n); n = 0
        return out

    def hair_o(self):
        a, l, t = self.raster("o"); ink = a > 0.5; H, W = ink.shape; best = []
        cols = [c for c in range(W) if ink[:, c].any()]
        for which in ("top", "bot"):
            vals = []
            for c in cols:
                col = ink[:, c]; idx = np.nonzero(col)[0]
                if which == "top":
                    i = idx[0]; n = 0
                    while i + n < H and col[i + n]: n += 1
                else:
                    i = idx[-1]; n = 0
                    while i - n >= 0 and col[i - n]: n += 1
                # only a crossing that has a counter behind it
                if n < H * 0.45: vals.append(n)
            best.append(min(vals) if vals else float("nan"))
        return min(best)

    def shape_len(self, text):
        buf = hb.Buffer(); buf.add_str(text); buf.guess_segment_properties()
        hb.shape(self.hbf, buf, {"kern": True, "liga": True})
        return sum(p.x_advance for p in buf.glyph_positions) / self.upem * 1000

    def ink(self, text, ppem=100):
        self.face.set_pixel_sizes(0, ppem); tot = 0.0
        for ch in text:
            if ch == " ": continue
            self.face.load_char(ch, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING)
            b = self.face.glyph.bitmap
            if b.rows: tot += np.frombuffer(bytes(b.buffer), np.uint8).reshape(b.rows, abs(b.pitch))[:, :b.width].sum() / 255
        return tot / (ppem * ppem) * 1e6 / len(text)   # (1/1000 em)^2 per char


def measure(spec):
    f = F(spec)
    xh = f.top("x"); cap = f.top("H")
    asc = max(f.top(c) for c in "bdhl"); desc = min(f.bottom(c) for c in "pq")
    stems = []
    for ch, fy in (("i", 0.45), ("l", 0.5), ("n", 0.35), ("m", 0.35), ("u", 0.55)):
        rr = f.runs_at(ch, xh * fy)
        if rr: stems.append(rr[0] if ch in "nmu" else max(rr))
    stem = st.median(stems)
    hair = f.hair_o()
    wid = f.shape_len(TEXT) / len(TEXT)
    ink = f.ink(TEXT)
    return dict(xh=xh, cap=cap, asc=asc, desc=-desc, stem=stem, hair=hair, wid=wid, ink=ink,
                col=ink / (wid * xh), app=xh * wid, stem_xh=stem / xh)


KEYS = ["xh", "cap", "asc", "desc", "stem", "hair", "wid", "ink", "col", "app", "stem_xh"]


def pair(name, r, i):
    R, I = measure(r), measure(i)
    return name, R, I, {k: I[k] / R[k] for k in KEYS}


def fmt_row(name, R, I, q):
    return (f"{name:15s} " + " ".join(f"{q[k]:6.3f}" for k in KEYS)
            + f"   | R xh {R['xh']:.0f} stem {R['stem']:.0f} hair {R['hair']:.0f}  I xh {I['xh']:.0f} stem {I['stem']:.0f} hair {I['hair']:.0f}")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    js = sys.argv[sys.argv.index("--json") + 1] if "--json" in sys.argv else None
    if js in args: args.remove(js)
    rows = []
    print(f"{'I/R ratio':15s} " + " ".join(f"{k:>6s}" for k in KEYS))
    for n, r, i in REFS:
        try:
            rows.append(pair(n, r, i)); print(fmt_row(*rows[-1]))
        except Exception as e:
            print(f"{n:15s} skipped: {e}")
    med = {k: st.median(q[k] for _, _, _, q in rows) for k in KEYS}
    lo = {k: min(q[k] for _, _, _, q in rows) for k in KEYS}
    hi = {k: max(q[k] for _, _, _, q in rows) for k in KEYS}
    print(f"{'REF MEDIAN':15s} " + " ".join(f"{med[k]:6.3f}" for k in KEYS))
    print(f"{'REF MIN':15s} " + " ".join(f"{lo[k]:6.3f}" for k in KEYS))
    print(f"{'REF MAX':15s} " + " ".join(f"{hi[k]:6.3f}" for k in KEYS))
    albo = []
    while len(args) >= 2:
        r, i = args[0], args[1]; lab = "Albo"
        args = args[2:]
        if args and not args[0].endswith((".ttf", ".otf")): lab = args.pop(0)
        albo.append(pair(lab, (r, 0), (i, 0))); print(fmt_row(*albo[-1]))
    if js:
        json.dump(dict(refs=[(n, R, I, q) for n, R, I, q in rows], median=med, min=lo, max=hi,
                       albo=[(n, R, I, q) for n, R, I, q in albo]), open(js, "w"), indent=1)


if __name__ == "__main__":
    main()
