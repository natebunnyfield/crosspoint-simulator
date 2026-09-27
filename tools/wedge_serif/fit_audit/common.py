"""Shared definitions for the fit audit (docs/albo-fit-audit-2026-09-26.md).

Fonts, the four cuts, the reference panel, the construction families, and
the glyph lookup (with the reference faces' old-style figures reached through
their own `onum` substitution, because Albo's figures are old-style and a
lining 3 is a different construction from an old-style one).
"""
import os
import numpy as np
import freetype
from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.dirname(HERE)
REPO = os.path.dirname(os.path.dirname(WS))

LC = "abcdefghijklmnopqrstuvwxyz"
UC = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
FIG = "0123456789"
CHARS = LC + UC + FIG
CUTS = ["Regular", "Italic", "Bold", "BoldItalic"]
PARTNER = {"Regular": "Bold", "Bold": "Regular", "Italic": "BoldItalic", "BoldItalic": "Italic"}

# CONSTRUCTION FAMILIES -- the map docs/albo-misfit-audit-2026-09-18.md used,
# kept so this ledger and that one are comparable. A glyph is judged against
# the letters built the same way, never against the alphabet: grouped by case,
# 47 of 124 glyphs "misfit", which measures the alphabet, not the drawing.
FAMILY = {}
for c in "acegos" + "CGOQS":
    FAMILY[c] = "round"
for c in "vwxyz" + "AVWXYZ":
    FAMILY[c] = "diag"
for c in FIG:
    FAMILY[c] = "figure"
for c in LC + UC:
    FAMILY.setdefault(c, "stem")

SYS = "/System/Library/Fonts"
SUP = SYS + "/Supplemental"
# (label, {cut: (path, face index)})
REFS = {
    "Georgia": {"Regular": (SUP + "/Georgia.ttf", 0), "Italic": (SUP + "/Georgia Italic.ttf", 0),
                "Bold": (SUP + "/Georgia Bold.ttf", 0), "BoldItalic": (SUP + "/Georgia Bold Italic.ttf", 0)},
    "Charter": {"Regular": (SUP + "/Charter.ttc", 0), "Italic": (SUP + "/Charter.ttc", 1),
                "Bold": (SUP + "/Charter.ttc", 3), "BoldItalic": (SUP + "/Charter.ttc", 2)},
    "Times": {"Regular": (SUP + "/Times New Roman.ttf", 0), "Italic": (SUP + "/Times New Roman Italic.ttf", 0),
              "Bold": (SUP + "/Times New Roman Bold.ttf", 0), "BoldItalic": (SUP + "/Times New Roman Bold Italic.ttf", 0)},
    "Baskerville": {"Regular": (SUP + "/Baskerville.ttc", 0), "Italic": (SUP + "/Baskerville.ttc", 2),
                    "Bold": (SUP + "/Baskerville.ttc", 1), "BoldItalic": (SUP + "/Baskerville.ttc", 3)},
    "Hoefler": {"Regular": (SUP + "/Hoefler Text.ttc", 0), "Italic": (SUP + "/Hoefler Text.ttc", 2),
                "Bold": (SUP + "/Hoefler Text.ttc", 1), "BoldItalic": (SUP + "/Hoefler Text.ttc", 3)},
    "Palatino": {"Regular": (SYS + "/Palatino.ttc", 0), "Italic": (SYS + "/Palatino.ttc", 1),
                 "Bold": (SYS + "/Palatino.ttc", 2), "BoldItalic": (SYS + "/Palatino.ttc", 3)},
}


def albo(fonts_dir, cut):
    return (os.path.join(fonts_dir, f"Albo-{cut}.ttf"), 0)


class Font:
    """One face: fontTools for metrics and GSUB, FreeType for pixels."""

    def __init__(self, path, index=0):
        self.path, self.index = path, index
        self.tt = TTFont(path, fontNumber=index, lazy=True)
        self.upm = self.tt["head"].unitsPerEm
        self.cmap = self.tt.getBestCmap()
        self.order = self.tt.getGlyphOrder()
        self.gid = {n: i for i, n in enumerate(self.order)}
        self.slant = -float(self.tt["post"].italicAngle)   # degrees, + leans right
        self.onum = self._onum()
        self.hmtx = self.tt["hmtx"]
        self._bbox = {}
        os2 = self.tt["OS/2"]
        self.xh = getattr(os2, "sxHeight", 0) or self._bbox_top("x")
        self.cap = getattr(os2, "sCapHeight", 0) or self._bbox_top("H")

    def _onum(self):
        m = {}
        if "GSUB" not in self.tt:
            return m
        g = self.tt["GSUB"].table
        if not g.FeatureList:
            return m
        for fr in g.FeatureList.FeatureRecord:
            if fr.FeatureTag != "onum":
                continue
            for li in fr.Feature.LookupListIndex:
                lk = g.LookupList.Lookup[li]
                for st in lk.SubTable:
                    if lk.LookupType == 7:
                        st = st.ExtSubTable
                    if hasattr(st, "mapping"):
                        m.update(st.mapping)
        return m

    def glyph(self, ch):
        """Glyph name; old-style figure where the face has an onum form."""
        n = self.cmap.get(ord(ch))
        if n is None:
            return None
        if ch in FIG:
            n = self.onum.get(n, n)
        return n

    def adv(self, ch):
        return self.hmtx[self.glyph(ch)][0]

    def bbox(self, ch):
        """(xMin, yMin, xMax, yMax) of the outline, font units, via FreeType at upm."""
        if ch in self._bbox:
            return self._bbox[ch]
        f = freetype.Face(self.path, self.index)
        f.set_char_size(self.upm * 64, self.upm * 64, 72, 72)
        f.load_glyph(self.gid[self.glyph(ch)], freetype.FT_LOAD_NO_HINTING | freetype.FT_LOAD_NO_SCALE)
        pts = np.array(f.glyph.outline.points, dtype=float)
        b = (pts[:, 0].min(), pts[:, 1].min(), pts[:, 0].max(), pts[:, 1].max()) if len(pts) else (0, 0, 0, 0)
        self._bbox[ch] = b
        return b

    def _bbox_top(self, ch):
        return self.bbox(ch)[3]

    def ref_height(self, ch):
        return self.cap if ch in UC else self.xh


def robust_z(vals, groups, pooled_k=6.0, floor=0.0):
    """Robust z of each value against its group: (v - group median) / scale.
    Scale = 1.4826 x MAD, SHRUNK toward the pooled MAD of all residuals with
    weight pooled_k, because a family of five diagonals has a MAD that is
    mostly noise (albo-method.md 1f: a yardstick over six letters is a
    sample, not a yardstick). `floor` is the smallest scale allowed: a family
    whose members are IDENTICAL on an axis (every flat letter sits on the
    baseline at exactly 0) has MAD 0, and without a floor one unit of
    difference reads as a million sigma."""
    vals = np.asarray(vals, float)
    out = np.full(len(vals), np.nan)
    ok = ~np.isnan(vals)
    groups = np.asarray(groups)
    res = np.full(len(vals), np.nan)
    meds = {}
    for g in set(groups[ok]):
        m = ok & (groups == g)
        meds[g] = np.median(vals[m])
        res[m] = vals[m] - meds[g]
    pooled = 1.4826 * np.median(np.abs(res[ok])) if ok.sum() else np.nan
    for g in meds:
        m = ok & (groups == g)
        n = m.sum()
        mad = 1.4826 * np.median(np.abs(res[m]))
        s = np.sqrt((n * mad ** 2 + pooled_k * pooled ** 2) / (n + pooled_k))
        out[m] = res[m] / max(s, floor, 1e-9)
    return out
