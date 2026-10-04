#!/usr/bin/env python3
"""word_measure.py -- each letter AS IT SITS IN THE OWNER'S FREQUENT WORDS, through the reader's
pipeline, against reference faces set the same way (docs/albo-word-images-2026-10-04.md).

THE PIPELINE is the reader's since round 401: FreeType with NO hinting, 8-bit coverage cut to the
converter's 2-bit levels (top nibble >= 12/8/4 -> 3/2/1; `fit_audit/legib.quantize`), glyphs
placed by HarfBuzz with the font's own `kern` and `liga` (the reader applies both; Albo's Regular
ligates only fl, its Bold ff fi fl ffi ffl, its italics nothing), each glyph at its rounded pixel.
Every face is set at ALBO'S X-HEIGHT IN PIXELS (each face's declared sxHeight, or its rendered x
where it declares none -- see measure_xh), so a reference with a
bigger x-height is not given more pixels to draw with.

THE SIZES: Albo's whole ramp on the X3 (8, 10, 12, 14, 16, 18 pt at 150 dpi = 16.7-37.5 ppem, an
x-height of 7.2-16.1 px) and the phone's 2x tier at 8, 10 and 12 pt (33.3-50 ppem). Nine sizes, so
no single pixel phase decides a letter; "band" is their mean, and every size is kept in the JSON.

WHAT IT MEASURES, per letter occurrence, then per letter (frequency-weighted over the word list):

  band   the letter's SLOT (its advance, kerning included, the columns its pen position covers)
         over the x-height band (rows whose centers lie between the baseline and the x-height):
         mean 2-bit darkness, divided by the WHOLE WORD's band darkness. 1.00 = exactly the word's
         own color; 1.10 = a tenth darker than the word around it. Italics: the slot is sheared
         with the face's measured slant (off its own l), about the band's middle, so a leaning
         letter is not charged its neighbor's ink. Averaged over the nine sizes.
  knot   the darkest 0.11-em square window whose center lies in the letter's slot (any row), at
         ph-10, over the face's mean knot. Round 88's instrument (`outlines/cmp/balance.py`)
         carried over to the reader's renderer. MEASURED TO BE STYLE, NOT FAULT, on round 480: it
         calls 15 of Albo's 26 lowercase letters in the Regular (references 0-4), because Albo's
         even-weight rounds have no dark spot at all; in the bolds it saturates. Kept in the JSON,
         not used to call a letter.
  gapL   the white between this letter and the one BEFORE it, gapR the one AFTER it: in each row
  gapR   of the x-height band both glyphs ink, the white between the left glyph's right edge and
         the right glyph's left edge, clamped at the face's own n counter, averaged (measure 5 of
         `cmp_word_white.py`), on an unhinted raster at a 200 px x-height, kerning included; then
         over the face's median gap. Spacing is B2's (the owner's bench); a letter that sits loose
         or tight against EVERY neighbor on one side is a shape or a bearing, not a pair.

  anatomy  per face, on a 200 px x-height coverage raster: each letter's ink in the band, whole
         ink, advance and ink width over the same face's n -- why a letter reads light or dark
         (thin strokes, or a wide slot).
  words    (--report --words) each word's UNEVENNESS: the spread of its letters' slot colors,
         mean of the nine sizes, against the same word in every reference, with the letter that
         departs furthest.

The reference panel: Georgia, Charter, Palatino and Times New Roman (system fonts), ITC Berkeley
Oldstyle (Medium as the Regular) in every cut, and Albertus Medium (Regular only -- the face Albo
is "like, but more readable"). A letter's EXCESS is (Albo - reference median) / the references'
spread, floored at 0.03 so five faces that happen to agree cannot make a 1% difference read as
many sigma (`albo-method.md` 1f). The CALL/WATCH rule that turns these into a ranked list is
word_callouts.py's.

    $VENV instruments/word_measure.py --albo DIR --corpus corpus.json --out measure.json
    $VENV instruments/word_measure.py --report measure.json        # the per-letter tables
    $VENV instruments/word_measure.py --report measure.json --words  # the word-evenness tables
"""
import argparse, json, math, os, sys
from concurrent.futures import ProcessPoolExecutor
import numpy as np
import freetype
import uharfbuzz as hb

HERE = os.path.dirname(os.path.abspath(__file__))
SYS = "/System/Library/Fonts"
SUP = SYS + "/Supplemental"
DL = os.path.expanduser("~/Downloads")
BERK = DL + "/ITC Berkeley Oldstyle"
CUTS = ["Regular", "Italic", "Bold", "BoldItalic"]
LABEL = {"Regular": "R", "Italic": "I", "Bold": "B", "BoldItalic": "Z"}
REFS = {
    "Georgia": {"Regular": (SUP + "/Georgia.ttf", 0), "Italic": (SUP + "/Georgia Italic.ttf", 0),
                "Bold": (SUP + "/Georgia Bold.ttf", 0), "BoldItalic": (SUP + "/Georgia Bold Italic.ttf", 0)},
    "Charter": {"Regular": (SUP + "/Charter.ttc", 0), "Italic": (SUP + "/Charter.ttc", 1),
                "Bold": (SUP + "/Charter.ttc", 3), "BoldItalic": (SUP + "/Charter.ttc", 2)},
    "Palatino": {"Regular": (SYS + "/Palatino.ttc", 0), "Italic": (SYS + "/Palatino.ttc", 1),
                 "Bold": (SYS + "/Palatino.ttc", 2), "BoldItalic": (SYS + "/Palatino.ttc", 3)},
    "Times": {"Regular": (SUP + "/Times New Roman.ttf", 0), "Italic": (SUP + "/Times New Roman Italic.ttf", 0),
              "Bold": (SUP + "/Times New Roman Bold.ttf", 0), "BoldItalic": (SUP + "/Times New Roman Bold Italic.ttf", 0)},
    "Berkeley": {"Regular": (BERK + "/ITC Berkeley Oldstyle Medium/ITC Berkeley Oldstyle Medium.otf", 0),
                 "Italic": (BERK + "/ITC Berkeley Oldstyle Medium Italic/ITC Berkeley Oldstyle Medium Italic.otf", 0),
                 "Bold": (BERK + "/ITC Berkeley Oldstyle Bold/ITC Berkeley Oldstyle Bold.otf", 0),
                 "BoldItalic": (BERK + "/ITC Berkeley Oldstyle Bold Italic/ITC Berkeley Oldstyle Bold Italic.otf", 0)},
    "Albertus": {"Regular": (DL + "/Albertus Medium Regular.ttf", 0)},
}
ALBO_XH = 429 / 1000.0
# Albo's whole ramp on the X3 (8-18 pt at 150 dpi) and the phone's 2x tier at 8, 10, 12 pt: nine
# sizes, so a stem that happens to land on a pixel boundary at one size cannot decide a letter.
SIZES = {f"x3-{pt}": 150 / 72 * pt * ALBO_XH for pt in (8, 10, 12, 14, 16, 18)}
SIZES.update({f"ph-{pt}": 150 / 72 * 2 * pt * ALBO_XH for pt in (8, 10, 12)})
KNOT_SIZE = "ph-10"
HI_XH = 200          # px, the raster the gaps are read on
FLOOR = 0.03


def quantize(a8):
    n = a8 >> 4
    return np.where(n >= 12, 3, np.where(n >= 8, 2, np.where(n >= 4, 1, 0))).astype(np.uint8)


def _render(face, gid, shear=0.0):
    if shear:
        t = math.tan(math.radians(shear))
        face.set_transform(freetype.Matrix(0x10000, int(-t * 0x10000), 0, 0x10000), freetype.Vector(0, 0))
    face.load_glyph(gid, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING)
    b = face.glyph.bitmap
    a = (np.frombuffer(bytes(b.buffer), dtype=np.uint8).reshape(b.rows, b.pitch)[:, :b.width].copy()
         if b.rows else np.zeros((0, 0), np.uint8))
    if shear:
        face.set_transform(freetype.Matrix(0x10000, 0, 0, 0x10000), freetype.Vector(0, 0))
    return a, face.glyph.bitmap_left, face.glyph.bitmap_top


def measure_xh(path, index=0):
    """The face's x-height in em: OS/2 sxHeight where the font declares one, else the rendered x's
    ink height (refsets.measure_xh's rule, on FreeType unhinted). Declared first because ALBO'S x
    IS NOT FLAT-TOPPED: its wedge serifs rise to 451 (Regular) / 470 (Bold Italic) over a 429
    x-height line that its z and u sit on exactly; measuring Albo's x would set it 5% small.
    Charter and Albertus declare nothing and take the measured x, whose top is flat in both."""
    from fontTools.ttLib import TTFont
    tt = TTFont(path, fontNumber=index, lazy=True)
    sx = getattr(tt["OS/2"], "sxHeight", 0) or 0
    if sx:
        return sx / tt["head"].unitsPerEm
    f = freetype.Face(path, index); f.set_char_size(1000 * 64, 1000 * 64, 72, 72)
    a, left, top = _render(f, f.get_char_index("x"))
    rows = np.nonzero((a >= 128).any(1))[0]
    return (top - rows.min()) / 1000.0 if len(rows) else 0.5


def measure_slant(path, index=0):
    """Degrees the face leans, off its l's stem between 30% and 70% of its height (refs_registry's
    rule: a bare stem only), on FreeType unhinted."""
    f = freetype.Face(path, index); f.set_char_size(900 * 64, 900 * 64, 72, 72)
    a, left, top = _render(f, f.get_char_index("l"))
    m = a >= 128
    ys = np.nonzero(m.any(1))[0]
    if not len(ys):
        return 0.0
    y0, y1 = ys.min(), ys.max(); span = y1 - y0; cs = []
    for fr in (0.30, 0.70):
        y = int(y0 + span * fr); r = np.nonzero(m[y])[0]
        cs.append(((r.min() + r.max()) / 2.0, y))
    return math.degrees(math.atan2(cs[0][0] - cs[1][0], cs[1][1] - cs[0][1]))


class Face:
    """One face at one x-height in pixels: 2-bit glyphs, HarfBuzz shaping."""

    def __init__(self, path, index, xh_px, italic=False, slant=None):
        self.path, self.index = path, index
        self.xh_em = measure_xh(path, index)
        self.ppem = xh_px / self.xh_em
        self.xh_px = xh_px
        self.ft = freetype.Face(path, index)
        self.ft.set_char_size(int(round(self.ppem * 64)), int(round(self.ppem * 64)), 72, 72)
        self.hbf = hb.Font(hb.Face(hb.Blob.from_file_path(path), index))
        self.upm = self.ft.units_per_EM
        self.k = self.ppem / self.upm
        self.cache = {}
        self.slant = (measure_slant(path, index) if slant is None else slant) if italic else 0.0

    def glyph(self, gid):
        if gid not in self.cache:
            a, l, t = _render(self.ft, gid)
            self.cache[gid] = (quantize(a), l, t)
        return self.cache[gid]

    def shape(self, text):
        buf = hb.Buffer(); buf.add_str(text); buf.guess_segment_properties()
        hb.shape(self.hbf, buf, {"kern": True, "liga": True})
        out, x = [], 0.0
        for inf, pos in zip(buf.glyph_infos, buf.glyph_positions):
            out.append((inf.codepoint, inf.cluster, x + pos.x_offset * self.k, pos.x_advance * self.k))
            x += pos.x_advance * self.k
        return out, x

    def raster(self, text, pad=None):
        """(levels canvas, baseline row, x origin, glyph list [(gid, cluster, x, adv)])."""
        g, width = self.shape(text)
        pad = pad if pad is not None else int(self.ppem) + 4
        H = int(self.ppem * 1.6) + 2 * 4
        base = int(self.ppem * 1.15) + 4
        W = int(width) + 2 * pad
        c = np.zeros((H, W), np.uint8)
        for gid, cl, x, adv in g:
            lv, left, top = self.glyph(gid)
            if not lv.size:
                continue
            gx = int(round(pad + x)) + left; gy = base - top
            y0, x0 = max(gy, 0), max(gx, 0)
            sub = c[y0:gy + lv.shape[0], x0:gx + lv.shape[1]]
            np.maximum(sub, lv[y0 - gy:y0 - gy + sub.shape[0], x0 - gx:x0 - gx + sub.shape[1]], out=sub)
        return c, base, pad, g


def single(g, text):
    """Indices of glyphs that stand for exactly ONE character; a ligature (fl in the Regular, the
    five f-ligatures in the Bold) covers two or three and belongs to no single letter."""
    keep = set()
    for i, (gid, cl, x, adv) in enumerate(g):
        nxt = g[i + 1][1] if i + 1 < len(g) else len(text)
        if nxt - cl == 1:
            keep.add(i)
    return keep


def slot_bands(face, text):
    """Per glyph: (cluster, band darkness) and the word's band darkness, at this face's size."""
    c, base, pad, g = face.raster(text)
    H, W = c.shape
    yc = base - np.arange(H) - 0.5                      # row center, px above the baseline
    band = (yc >= 0) & (yc <= face.xh_px)
    rows = np.nonzero(band)[0]
    t = math.tan(math.radians(face.slant))
    mid = face.xh_px / 2.0
    lv = c.astype(float) / 3.0
    out = []
    tot_ink = tot_area = 0.0
    one = single(g, text)
    for i, (gid, cl, x, adv) in enumerate(g):
        if adv <= 0:
            continue
        ink = area = 0.0
        for r in rows:
            sh = t * (yc[r] - mid)                      # the slot leans with the letter
            x0 = pad + x + sh; x1 = x0 + adv
            i0, i1 = int(math.floor(x0)), int(math.ceil(x1))
            seg = lv[r, max(i0, 0):min(i1, W)]
            if not seg.size:
                continue
            # fractional coverage of the first and last columns
            w = np.ones(seg.size)
            w[0] -= (x0 - i0); w[-1] -= (i1 - x1)
            w = np.clip(w, 0, 1)
            ink += float((seg * w).sum()); area += float(w.sum())
        if area > 0:
            if i in one:
                out.append((cl, ink / area))
            tot_ink += ink; tot_area += area
    return out, (tot_ink / tot_area if tot_area else float("nan"))


def slot_knots(face, text, win_em=0.11):
    c, base, pad, g = face.raster(text)
    k = max(2, int(round(win_em * face.ppem)))
    lv = c.astype(float) / 3.0
    cs = np.cumsum(np.cumsum(np.pad(lv, ((1, 0), (1, 0))), axis=0), axis=1)
    win = (cs[k:, k:] - cs[:-k, k:] - cs[k:, :-k] + cs[:-k, :-k]) / (k * k)
    out = []
    one = single(g, text)
    for i, (gid, cl, x, adv) in enumerate(g):
        if adv <= 0 or i not in one:
            continue
        c0 = int(round(pad + x)) - k // 2; c1 = int(round(pad + x + adv)) - k // 2
        c0 = max(c0, 0); c1 = max(c0 + 1, min(win.shape[1], c1))
        out.append((cl, float(win[:, c0:c1].max())))
    return out


class Profiles:
    """Per glyph, row by row across the x-height band, the leftmost and rightmost ink at a 200 px
    x-height (unhinted, 50% coverage), for the gap measure."""

    def __init__(self, path, index, italic=False):
        self.f = Face(path, index, HI_XH, italic=italic, slant=0.0)
        self.cache = {}
        self.ctr = self._n_counter()

    def prof(self, gid):
        if gid not in self.cache:
            a, left, top = _render(self.f.ft, gid)
            m = a >= 128
            L = np.full(HI_XH, np.nan); R = np.full(HI_XH, np.nan)
            for r in range(m.shape[0]):
                yc = top - r - 0.5
                yi = int(math.floor(yc))
                if 0 <= yi < HI_XH:
                    xs = np.nonzero(m[r])[0]
                    if len(xs):
                        L[yi] = left + xs.min(); R[yi] = left + xs.max() + 1
            self.cache[gid] = (L, R)
        return self.cache[gid]

    def _n_counter(self):
        """The n's counter: the widest white run strictly inside the letter's ink, on the rows at
        35%, 45% and 55% of the x-height (below the arch, above the feet), median of the three.
        The widest run, not the second run: an italic n's pen join can split a stem's row into two
        runs a few pixels apart, which read as a 3-5 px "counter" in Times and Palatino Italic."""
        gid = self.f.ft.get_char_index("n")
        a, left, top = _render(self.f.ft, gid)
        m = a >= 128
        widths = []
        for fr in (0.35, 0.45, 0.55):
            r = int(round(top - HI_XH * fr - 0.5))
            if not (0 <= r < m.shape[0]):
                continue
            xs = np.nonzero(m[r])[0]
            if len(xs) < 2:
                continue
            gaps = np.diff(xs) - 1
            widths.append(float(gaps.max()))
        return float(np.median(widths)) if widths else HI_XH * 0.4

    def gap(self, pair):
        g, _ = self.f.shape(pair)
        if len(g) != 2:
            return None                                  # a ligature swallowed the pair
        (ga, _, xa, _), (gb, _, xb, _) = g
        La, Ra = self.prof(ga); Lb, Rb = self.prof(gb)
        w = (xb + Lb) - (xa + Ra)
        ok = ~np.isnan(w)
        if ok.sum() < 3:
            return None
        return float(np.clip(w[ok], 0, self.ctr).mean() / self.ctr)


def anatomy(path, index, italic=False):
    """Per letter, on an unhinted coverage raster at a 200 px x-height: the INK in the x-height band
    (coverage summed over the rows whose centers lie in the band), the whole ink, the advance and the
    ink's width -- each divided by the same face's n. A letter's color in a word is roughly its band
    ink over its advance, so these two say WHY a letter reads light or dark: thin strokes, or a wide
    slot. Shear does not change an area or an advance, so italics need no unshearing here."""
    F = Face(path, index, HI_XH, italic=italic, slant=0.0)
    out = {}
    for ch in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ":
        gid = F.ft.get_char_index(ch)
        if not gid:
            continue
        a, left, top = _render(F.ft, gid)
        adv = F.ft.glyph.advance.x / 64.0
        if not a.size:
            continue
        cov = a.astype(float) / 255.0
        yc = top - np.arange(a.shape[0]) - 0.5
        band = (yc >= 0) & (yc <= HI_XH)
        cols = np.nonzero((a >= 128).any(0))[0]
        out[ch] = dict(band_ink=float(cov[band].sum()), ink=float(cov.sum()), adv=adv,
                       width=float(cols[-1] - cols[0] + 1) if len(cols) else 0.0)
    n = out["n"]
    for ch, r in out.items():
        r.update(band_ink_n=r["band_ink"] / n["band_ink"], ink_n=r["ink"] / n["ink"],
                 adv_n=r["adv"] / n["adv"], width_n=r["width"] / n["width"],
                 color_n=(r["band_ink"] / r["adv"]) / (n["band_ink"] / n["adv"]))
    return out


def word_list(corpus, n_lower=600, n_title=80):
    """Lowercase forms and Title-case forms from the corpus, with counts."""
    top = json.load(open(corpus))["top"]
    lower = [(r["word"], r["count"]) for r in top if r["word"].isascii() and r["word"].replace("'", "").isalpha()
             and r["word"].islower() and len(r["word"]) >= 2][:n_lower]
    title = [(r["word"], r["count"]) for r in top if r["word"].isascii() and r["word"][:1].isupper()
             and r["word"][1:].replace("'", "").islower() and len(r["word"]) >= 2][:n_title]
    return lower, title


def measure_face(job):
    label, cut, path, index, words = job
    italic = cut in ("Italic", "BoldItalic")
    res = {"label": label, "cut": cut, "path": path, "index": index}
    letters = {}
    per_word = {}
    for sz, xh in SIZES.items():
        F = Face(path, index, xh, italic=italic)
        res.setdefault("slant", F.slant); res.setdefault("xh_em", F.xh_em)
        for w, n in words:
            bands, wc = slot_bands(F, w)
            for cl, b in bands:
                ch = w[cl]
                d = letters.setdefault(ch, {"band": {}, "knot": [], "n": 0.0})
                d["band"].setdefault(sz, []).append((b / wc, n))
            per_word.setdefault(w, {})[sz] = [(cl, round(b / wc, 4)) for cl, b in bands]
            if sz == KNOT_SIZE:
                for cl, kv in slot_knots(F, w):
                    letters[w[cl]]["knot"].append((kv, n))
    # gaps
    P = Profiles(path, index, italic=italic)
    pairs = {}
    for w, n in words:
        for i in range(len(w) - 1):
            pairs[w[i:i + 2]] = pairs.get(w[i:i + 2], 0) + n
    gaps = {p: P.gap(p) for p in pairs}
    gv = [(g, pairs[p]) for p, g in gaps.items() if g is not None]
    med = weighted_median([g for g, _ in gv], [n for _, n in gv])
    out = {}
    allknots = [(kv, n) for d in letters.values() for kv, n in d["knot"]]
    kmean = sum(k * n for k, n in allknots) / sum(n for _, n in allknots)
    for ch, d in letters.items():
        row = {}
        bs = [wmean(d["band"][sz]) for sz in SIZES if sz in d["band"]]
        row["band"] = float(np.mean(bs)); row["band_sizes"] = {sz: wmean(d["band"][sz]) for sz in d["band"]}
        row["knot"] = wmean(d["knot"]) / kmean
        row["weight"] = float(sum(n for _, n in d["band"]["x3-10"]))
        L = [(gaps[p] / med, pairs[p]) for p in pairs if p[1] == ch and gaps.get(p) is not None]
        R = [(gaps[p] / med, pairs[p]) for p in pairs if p[0] == ch and gaps.get(p) is not None]
        row["gapL"] = wmean(L) if L else None
        row["gapR"] = wmean(R) if R else None
        out[ch] = row
    res["letters"] = out
    res["anatomy"] = anatomy(path, index, italic=italic)
    res["gap_median_ctr"] = med
    res["n_counter_px"] = P.ctr
    res["pairs"] = {p: (round(g / med, 3) if g is not None else None) for p, g in gaps.items()}
    res["per_word"] = per_word
    return res


def wmean(v):
    tot = sum(n for _, n in v)
    return float(sum(x * n for x, n in v) / tot) if tot else float("nan")


def weighted_median(x, w):
    o = np.argsort(x); x = np.asarray(x)[o]; w = np.asarray(w, float)[o]
    c = np.cumsum(w)
    return float(x[np.searchsorted(c, c[-1] / 2.0)])


def faces(albo_dir):
    fs = [("Albo", c, os.path.join(albo_dir, f"Albo-{c}.ttf"), 0) for c in CUTS]
    for r, cuts in REFS.items():
        for c, (p, i) in cuts.items():
            fs.append((r, c, p, i))
    return fs


def excess(albo, refs):
    refs = [r for r in refs if r is not None and not (isinstance(r, float) and math.isnan(r))]
    if albo is None or len(refs) < 3:
        return None, None, None
    med = float(np.median(refs))
    sp = 1.4826 * float(np.median(np.abs(np.array(refs) - med)))
    return (albo - med) / max(sp, FLOOR), med, sp


def report(M, cut, keys=("band", "knot", "gapL", "gapR"), letters=None):
    A = M["Albo/" + cut]["letters"]
    refs = [M[k]["letters"] for k in M if k.endswith("/" + cut) and not k.startswith("Albo/")]
    rows = []
    for ch in sorted(A, key=lambda c: -A[c]["weight"]):
        if letters and ch not in letters:
            continue
        row = {"ch": ch, "weight": A[ch]["weight"]}
        for key in keys:
            e, med, sp = excess(A[ch].get(key), [r[ch].get(key) for r in refs if ch in r])
            row[key] = (A[ch].get(key), med, sp, e)
        rows.append(row)
    return rows


def word_evenness(M, cut, words):
    """For each word: its UNEVENNESS -- the spread (standard deviation) of its letters' slot colors
    over the word's own color, averaged over the nine sizes -- in Albo and in each reference set
    the same way; and the letter that departs furthest from the references' same letter IN THAT
    WORD. A word whose letters all carry the same color reads as one image; a word with one dark
    or pale slot reads as two pieces and a blot. Returns rows sorted by (Albo - reference median)."""
    A = M["Albo/" + cut]["per_word"]
    refs = [k for k in M if k.endswith("/" + cut) and not k.startswith("Albo/") and "per_word" in M[k]]
    rows = []
    for w, n in words:
        if w not in A:
            continue
        def unev(pw):
            vals = [float(np.std([b for _, b in pw[sz]])) for sz in pw if len(pw[sz]) > 1]
            return float(np.mean(vals)) if vals else float("nan")
        ua = unev(A[w])
        ur = [unev(M[r]["per_word"][w]) for r in refs if w in M[r]["per_word"]]
        if not ur or math.isnan(ua):
            continue
        # the letter that departs most: Albo's mean slot color minus the references' median, per slot
        worst, wv = None, 0.0
        for idx, (cl, _) in enumerate(A[w]["x3-10"]):
            av = float(np.mean([A[w][sz][idx][1] for sz in A[w] if len(A[w][sz]) > idx]))
            rv = []
            for r in refs:
                pw = M[r]["per_word"].get(w)
                if pw and len(pw["x3-10"]) > idx:
                    rv.append(float(np.mean([pw[sz][idx][1] for sz in pw if len(pw[sz]) > idx])))
            if rv and abs(av - np.median(rv)) > abs(wv):
                worst, wv = w[cl], av - float(np.median(rv))
        rows.append(dict(word=w, count=n, albo=ua, refs=float(np.median(ur)), lo=min(ur), hi=max(ur),
                         excess=ua - float(np.median(ur)), worst=worst, worst_delta=wv))
    return sorted(rows, key=lambda r: -r["excess"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--albo")
    ap.add_argument("--corpus")
    ap.add_argument("--out")
    ap.add_argument("--report")
    ap.add_argument("--lower", type=int, default=600)
    ap.add_argument("--title", type=int, default=80)
    ap.add_argument("--words", action="store_true", help="with --report: the word-evenness table")
    a = ap.parse_args()
    if a.report and a.words:
        M = json.load(open(a.report))
        wl = M["_words"]["lower"] + M["_words"]["title"]
        for cut in CUTS:
            rows = word_evenness(M, cut, wl)
            top = sorted(wl, key=lambda x: -x[1])[:100]
            topset = {w for w, _ in top}
            r100 = [r for r in rows if r["word"] in topset]
            worse = sum(1 for r in r100 if r["albo"] > r["hi"])
            print(f"\n{cut} ({LABEL[cut]}): of the 100 commonest words, {worse} are less even in Albo than in "
                  f"every reference; median unevenness Albo {np.median([r['albo'] for r in r100]):.3f}, "
                  f"references {np.median([r['refs'] for r in r100]):.3f}")
            for r in rows[:25]:
                print(f"  {r['word']:12s} {r['count']:6d}  Albo {r['albo']:.3f}  refs {r['refs']:.3f} "
                      f"[{r['lo']:.3f}-{r['hi']:.3f}]  worst letter {r['worst']} {r['worst_delta']:+.3f}")
        return
    if a.report:
        M = json.load(open(a.report))
        for cut in CUTS:
            print(f"\n{cut} ({LABEL[cut]}): letter  weight | band Albo ref e | knot Albo ref e | gapL e | gapR e")
            for r in report(M, cut):
                def f(k):
                    v, med, sp, e = r[k]
                    return "   --   " if e is None else f"{v:5.3f} {med:5.3f} {e:+5.1f}"
                print(f"  {r['ch']}  {r['weight']:9.0f} | {f('band')} | {f('knot')} | {f('gapL')} | {f('gapR')}")
        return
    lower, title = word_list(a.corpus, a.lower, a.title)
    words = lower + title
    jobs = [(l, c, p, i, words) for l, c, p, i in faces(a.albo)]
    M = {}
    with ProcessPoolExecutor(max_workers=os.cpu_count()) as ex:
        for res in ex.map(measure_face, jobs):
            M[f"{res['label']}/{res['cut']}"] = res
            print(res["label"], res["cut"], "slant %.1f" % res["slant"], "xh %.3f" % res["xh_em"],
                  "n ctr %.0f px" % res["n_counter_px"], flush=True)
    M["_words"] = {"lower": lower, "title": title}
    json.dump(M, open(a.out, "w"))
    print("wrote", a.out)


if __name__ == "__main__":
    main()
