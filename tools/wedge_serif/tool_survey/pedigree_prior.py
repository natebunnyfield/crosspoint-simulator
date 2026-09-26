#!/usr/bin/env python3
"""A pedigree-font spacing prior, built the cheap way, scored like any tool.

THE QUESTION (owner 2026-09-26): is it worth training a spacing prior on
pedigreed fonts? The cheapest honest version: learn "white from shape" on
well-spaced text faces, apply it to Albo's shapes, and see whether that
predicts HIS answers -- alone, calibrated, and as a feature inside B2.

TRAINING FONTS: the text serifs macOS ships (Palatino, Hoefler Text, Iowan
Old Style, Baskerville, Charter, Georgia, Times New Roman, roman and italic)
plus, for the italic, the repo's own references (Flanker Griffo, Coelacanth,
Pagella). Each is scaled to Albo's x-height (429) before anything is measured,
so "white" means the same thing in every font.

FEATURES are spacing-INVARIANT shape measures (a prior must not see the
spacing it is predicting): each facing side's depth profile at 8 heights
(from its own bbox edge, capped 200), the pair's closest recess sum and mean
recess per band (descender / x / ascender), each glyph's inner white, and class
flags. Target: the pair's white, rsb + kern + lsb, HarfBuzz, kerning included.
One ridge per style (alpha 30, standardized), with a per-font intercept so a
face's overall tracking is not mistaken for shape; Albo gets the mean.

    $VENV/bin/python pedigree_prior.py
"""
import os, sys, time
import numpy as np
import uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.freetypePen import FreeTypePen
from fontTools.pens.transformPen import TransformPen
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C  # noqa: E402

SUP = "/System/Library/Fonts/Supplemental"
REFS = os.path.join(C.WS, "refs")
TRAIN = {
    "roman": [("Palatino", "/System/Library/Fonts/Palatino.ttc", 0), ("Hoefler Text", f"{SUP}/Hoefler Text.ttc", 0),
              ("Iowan", f"{SUP}/Iowan Old Style.ttc", 0), ("Baskerville", f"{SUP}/Baskerville.ttc", 0),
              ("Charter", f"{SUP}/Charter.ttc", 0), ("Georgia", f"{SUP}/Georgia.ttf", None),
              ("Times", f"{SUP}/Times New Roman.ttf", None)],
    "italic": [("Palatino It", "/System/Library/Fonts/Palatino.ttc", 1), ("Hoefler It", f"{SUP}/Hoefler Text.ttc", 2),
               ("Iowan It", f"{SUP}/Iowan Old Style.ttc", 2), ("Baskerville It", f"{SUP}/Baskerville.ttc", 2),
               ("Charter It", f"{SUP}/Charter.ttc", 1), ("Georgia It", f"{SUP}/Georgia Italic.ttf", None),
               ("Times It", f"{SUP}/Times New Roman Italic.ttf", None),
               ("Flanker Griffo", f"{REFS}/flanker-griffo-italic.otf", None),
               ("Coelacanth It", f"{REFS}/coelacanth-italic.otf", None),
               ("Pagella It", f"{REFS}/texgyrepagella-italic.otf", None)],
}
U = 4.0
XH = 429.0
HEIGHTS = np.linspace(-200, 700, 8)
MARKS = set("'.,:;\"-!?")


class Face:
    def __init__(self, path, index=None):
        self.tt = TTFont(path, fontNumber=index if index is not None else -1)
        self.gs = self.tt.getGlyphSet(); self.cmap = self.tt.getBestCmap(); self.order = self.tt.getGlyphOrder()
        self.hb = hb.Font(hb.Face(hb.Blob.from_file_path(path), index or 0))
        # x-height: OS/2 sxHeight where the table has one (Albo's own is 429, so
        # Albo is measured at scale 1), else the top of the x's outline.
        xh = getattr(self.tt["OS/2"], "sxHeight", 0) or 0
        if not xh:
            bp = BoundsPen(self.gs); self.gs[self.cmap[ord("x")]].draw(bp); xh = bp.bounds[3]
        self.s = XH / xh
        self._g = {}

    def has(self, p):
        return all(ord(c) in self.cmap for c in p)

    def glyph(self, ch):
        if ch in self._g:
            return self._g[ch]
        n = self.cmap[ord(ch)]
        bp = BoundsPen(self.gs); self.gs[n].draw(bp)
        x0, y0, x1, y1 = bp.bounds
        s = self.s
        W = int((x1 - x0) * s / U) + 4; H = int(1300 / U)
        pen = FreeTypePen(self.gs)
        self.gs[n].draw(TransformPen(pen, (1, 0, 0, 1, -x0, 0)))
        M = pen.array(width=W, height=H, transform=(s / U, 0, 0, s / U, 2, 400 / U)) > 0.5
        rows_y = (H - np.arange(H)) * U - 400          # row -> y (Albo units)
        L = np.full(H, np.nan); R = np.full(H, np.nan)
        for r in np.nonzero(M.any(1))[0]:
            xs = np.nonzero(M[r])[0]; L[r] = (xs[0] - 2) * U; R[r] = (xs[-1] - 2) * U
        wid = (x1 - x0) * s
        xs_ = (rows_y >= 0) & (rows_y < XH)
        runs = []
        for r in np.nonzero(xs_)[0]:
            xs = np.nonzero(M[r])[0]
            if len(xs) > 1:
                g = np.diff(xs) - 1; runs += list(g[g > 0])
        g = dict(L=L, R=R, y=rows_y, w=wid, inner=float(np.mean(runs) * U) if runs else 0.0,
                 x0=x0 * s, x1=x1 * s)
        self._g[ch] = g
        return g

    def white(self, a, b):
        buf = hb.Buffer(); buf.add_str(a + b); buf.guess_segment_properties()
        hb.shape(self.hb, buf, {"liga": False, "clig": False, "dlig": False})
        inf, pos = buf.glyph_infos, buf.glyph_positions
        adv = self.hb.get_glyph_h_advance(inf[0].codepoint)
        kern = pos[0].x_advance - adv + pos[1].x_offset
        ga, gb = self.glyph(a), self.glyph(b)
        return (adv * self.s - ga["x1"]) + kern * self.s + gb["x0"]


def feats(F, a, b):
    ga, gb = F.glyph(a), F.glyph(b)
    y = ga["y"]
    dA = ga["w"] - ga["R"]          # depth of A's right side from its bbox edge
    dB = gb["L"]                    # depth of B's left side from its bbox edge
    f = {}
    for i, h in enumerate(HEIGHTS):
        r = int(np.argmin(np.abs(y - h)))
        f[f"pA{i}"] = float(min(200, dA[r])) if not np.isnan(dA[r]) else 200.0
        f[f"pB{i}"] = float(min(200, dB[r])) if not np.isnan(dB[r]) else 200.0
    both = ~np.isnan(dA) & ~np.isnan(dB)
    for band, lo, hi in (("d", -280, 0), ("x", 0, XH), ("a", XH, 770)):
        sel = both & (y >= lo) & (y < hi)
        s = dA[sel] + dB[sel]
        f[f"rmin_{band}"] = float(s.min()) if sel.any() else 300.0
        f[f"rmean_{band}"] = float(np.mean(np.minimum(dA[sel], 150) + np.minimum(dB[sel], 150))) if sel.any() else 300.0
        f[f"frac_{band}"] = float(sel.mean())
    f["innerA"], f["innerB"] = ga["inner"], gb["inner"]
    f["capL"], f["capR"] = float(a.isupper()), float(b.isupper())
    f["markL"], f["markR"] = float(a in MARKS), float(b in MARKS)
    return f


def main():
    t0 = time.time()
    T = C.Truth()
    white, meta = {}, {}
    for s in C.STYLES:
        pairs = T.P[s]
        rows, y, fid = [], [], []
        names = [n for n, *_ in TRAIN[s]]
        per_font = {}
        for k, (name, path, idx) in enumerate(TRAIN[s]):
            F = Face(path, idx)
            got = 0
            for p in pairs:
                if not F.has(p):
                    continue
                rows.append(feats(F, *p)); y.append(F.white(*p)); fid.append(k); got += 1
            per_font[name] = got
        keys = sorted(rows[0])
        X = np.array([[r[k] for k in keys] for r in rows]); y = np.array(y); fid = np.array(fid)
        onehot = np.eye(len(names))[fid]
        sc = StandardScaler().fit(X)
        Z = np.hstack([sc.transform(X), onehot * 10.0])     # x10 so the ridge barely shrinks the intercepts
        mdl = Ridge(alpha=30.0).fit(Z, y)
        # leave-one-font-out: how well does shape predict an UNSEEN face's own white?
        lofo = {}
        for k, name in enumerate(names):
            m = fid != k
            sc2 = StandardScaler().fit(X[m])
            Z2 = np.hstack([sc2.transform(X[m]), onehot[m][:, [j for j in range(len(names)) if j != k]] * 10.0])
            md2 = Ridge(alpha=30.0).fit(Z2, y[m])
            Zt = np.hstack([sc2.transform(X[~m]), np.full((int((~m).sum()), len(names) - 1), 10.0 / (len(names) - 1))])
            pr = md2.predict(Zt)
            # a face's own tracking is one constant: score after removing it
            lofo[name] = dict(mae=float(np.mean(np.abs(pr - y[~m]))),
                              mae_tracked=float(np.mean(np.abs(pr - np.mean(pr - y[~m]) - y[~m]))),
                              r=float(np.corrcoef(pr, y[~m])[0, 1]))
        A = C.FONTSETS["0920"][s]
        FA = Face(A)
        XA = np.array([[feats(FA, *p)[k] for k in keys] for p in pairs])
        ZA = np.hstack([sc.transform(XA), np.full((len(pairs), len(names)), 10.0 / len(names))])
        white[s] = dict(zip(pairs, map(float, mdl.predict(ZA))))
        # sanity: Albo's own white measured by the same code must equal the bench zero
        chk = max(abs(FA.white(*p) - T.white0920[s][p]) for p in pairs)
        meta[s] = dict(fonts=per_font, rows=len(y), lofo=lofo, albo_white_check_max_abs=round(chk, 3))
        print(f"{s}: {len(y)} training rows from {len(names)} faces; Albo white check max |diff| {chk:.3f}")
        for n, v in lofo.items():
            print(f"   leave-one-face-out {n:16s} MAE {v['mae']:6.1f}  after its tracking {v['mae_tracked']:6.1f}  r {v['r']:+.2f}")
    meta["seconds"] = round(time.time() - t0, 1)
    print(C.save_preds("pedigree-prior", "0920", white, meta))


if __name__ == "__main__":
    main()
