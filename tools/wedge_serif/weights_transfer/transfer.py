#!/usr/bin/env python3
"""Carry the owner's 400 spacing answers to every Albo weight: four arms.

Owner 2026-09-26: *"interpolated based on my answers what changes would be
applicable to all of albo fonts (thin, black, italic, bold italic, etc)"*.
Every answer he gave (the 396-row bench, the re-ask, the outlier bench, active
sessions 1-2) was judged on the 400 Regular or the 400 Italic. Today those
corrections reach the other cuts as the SAME DESIGN UNITS (build.py applies
ROM_LC_ADJ / ALD_LC_ADJ / the mark tables with no weight term; kern.py adds the
B2 kerns to every cut of a style). This script prices three alternatives.

THE CORRECTION. C400 is what his answers put on the 400, in units, as shipped
at HEAD (outlines/spacing_b2.json, read from git -- another agent owns the
working copy): each lowercase/mark SIDE (the B2 identity bearings) and each
KERN (B2 kerns, plus the holds and his own post-bench kerns of rounds 388-390
on the held pairs, transcribed below from kern.py).

THE ARMS, each applied to TODAY's built cut by post-processing the TTF (sides
move the outline and the advance, composites follow their base exactly as the
builder does; kern deltas go in one extra PairPos lookup under 'kern'):

  a  units   C_W = C400. Today. No file is written; `today` IS arm a.
  b  stem    C_W = C400 * stem_W / stem_400 -- white grows with the stem.
  c  rhythm  C_W = C400 * counter_W / counter_400, the n's counter (Tracy's
             control: the n's sidebearing starts at half its counter). His
             correction is read as a fraction of the space inside the letters.
  d  B2      the B2 model re-evaluated on each cut's OWN shape features: the
             identity terms (a glyph's own preference) stay in units, the 38
             shape features are re-measured on that cut, and each in-scope
             pair's kern is re-derived exactly as b2_fit.py derives it (same
             4-unit floor, same holds).

    $VENV/bin/python transfer.py TODAY_DIR OUT_DIR
"""
import collections, json, os, sys
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables import otTables
from fontTools.otlLib.builder import buildPairPosGlyphs

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from common import Font, WS, MARKS, AGL, head_json, census  # noqa: E402
sys.path.insert(0, os.path.join(WS, "local_ai")); sys.path.insert(0, WS)
import b2_fit  # noqa: E402
import features as FT  # noqa: E402

CUTS = {"roman": [("ExtraLight", 200), ("Regular", 400), ("Bold", 700), ("Black", 900)],
        "italic": [("Italic", 400), ("BoldItalic", 700)]}
BASE = {"roman": "Regular", "italic": "Italic"}

# His own post-bench kerns on the held pairs (kern.py rounds 388, 389, 390 at
# HEAD). Clearance kerns (fT, QQ, q' q" qj, the bold qu) are NOT his answers
# and are not scaled.
EXPLICIT = {
    "roman": {"'s": -43, "'t": -41, "or": -20, "rd": 20, "gr": -27, "Vo": -4, "Yo": 3, "oc": -18,
              "Jo": -6, "Th": 6, "Qu": 10, "ba": 6, "t.": -3, "ed": 25, "pa": -13, "En": -5, "ry": -3,
              "Ka": 24, "of": -14, "ty": -6, "wo": 3, "ki": 8, "ec": 36, "rh": 27, "hy": -35, "th": -11,
              "hm": -15},
    "italic": {"Fi": 44, "Fo": 45, "Ye": -40, "Yo": -47, "Pa": 28, "Po": 33, "Pr": 27, "Wa": -11,
               "Wh": -12, "Wi": -12, "Am": -6, "An": -6, "Av": -6, "or": -16, "es": 22, "r,": -3,
               "fi": 9, "gs": 6, "y.": 18, "El": 16, "um": -16, "rg": 4, "ki": -21, "ta": 4, "Jo": 8,
               "n'": -23, "ru": 8, "qu": -16, "tr": 17, "cy": 5, "rh": -16, "hy": -11, "hm": 14},
}
QUOTES = "'\"‘’“”"


def correction(style):
    b2 = head_json("tools/wedge_serif/outlines/spacing_b2.json")[style]
    sides = {c: tuple(v) for c, v in {**b2["letters"], **b2["marks"]}.items() if c != "g"}
    kerns = dict(b2["kerns"])
    for p, d in b2.get("holds", {}).items():
        p = p.replace("’", "'")
        kerns[p] = kerns.get(p, 0) + d
    for p, d in EXPLICIT[style].items():
        kerns[p] = kerns.get(p, 0) + d
    return sides, kerns, b2


def gnames(F, ch, style):
    if ch == "'":
        return ["quotesingle", "quoteright"]
    n = F.cmap.get(ord(ch))
    return [n] if n else []


# ---------------------------------------------------------------- post-process
def apply(src, dst, side_delta, kern_delta, style):
    """side_delta {char: (dl, dr)} float; kern_delta {(char, char): d}."""
    tt = TTFont(src)
    cmap = tt.getBestCmap(); glyf = tt["glyf"]; hmtx = tt["hmtx"]
    names = {}                           # glyph name -> (dl, dr)
    for ch, (dl, dr) in side_delta.items():
        dl, dr = int(round(dl)), int(round(dr))
        if not (dl or dr):
            continue
        targets = []
        if style == "roman" and ch == "'":
            targets = [cmap[ord(q)] for q in QUOTES if ord(q) in cmap and (q == "'" or q not in side_delta)]
        else:
            n = cmap.get(ord(ch))
            targets = [n] if n else []
        for n in targets:
            names[n] = (dl, dr)
        if style == "roman" and ch in "il" and dr:
            for lig in (("ﬁ", "ﬃ") if ch == "i" else ("ﬂ", "ﬄ")):
                if ord(lig) in cmap:
                    names[cmap[ord(lig)]] = (0, dr)
    # composites follow their BASE (first component), as the builder does
    for gn in tt.getGlyphOrder():
        g = glyf[gn]
        if g.isComposite() and g.components[0].glyphName in names and gn not in names:
            names[gn] = ("comp",) + names[g.components[0].glyphName]
    for gn, v in names.items():
        g = glyf[gn]
        adv, lsb = hmtx[gn]
        if v[0] == "comp":
            dl, dr = v[1], v[2]
            for c in g.components[1:]:     # the base shifted by dl inside; the marks must too
                c.x += dl
        else:
            dl, dr = v
            if g.numberOfContours > 0:
                g.coordinates.translate((dl, 0))
        g.recalcBounds(glyf)
        hmtx[gn] = (adv + dl + dr, g.xMin if g.numberOfContours else lsb + dl)
    # kerns: one extra PairPos lookup appended to every 'kern' feature
    pairs = {}
    for (a, b), d in kern_delta.items():
        d = int(round(d))
        if not d:
            continue
        ga = ["quotesingle", "quoteright"] if a == "'" else ([cmap[ord(a)]] if ord(a) in cmap else [])
        gb = ["quotesingle", "quoteright"] if b == "'" else ([cmap[ord(b)]] if ord(b) in cmap else [])
        for la in ga:
            for rb in gb:
                vr = otTables.ValueRecord(); vr.XAdvance = d
                pairs[(la, rb)] = (vr, None)
    if pairs:
        gpos = tt["GPOS"].table
        subs = buildPairPosGlyphs(pairs, tt.getReverseGlyphMap())
        lk = otTables.Lookup(); lk.LookupType = 2; lk.LookupFlag = 0
        lk.SubTable = subs; lk.SubTableCount = len(subs)
        gpos.LookupList.Lookup.append(lk); gpos.LookupList.LookupCount += 1
        idx = gpos.LookupList.LookupCount - 1
        for fr in gpos.FeatureList.FeatureRecord:
            if fr.FeatureTag == "kern":
                fr.Feature.LookupListIndex.append(idx); fr.Feature.LookupCount += 1
    tt.save(dst)
    return len(names), len(pairs)


# ---------------------------------------------------------------- the arms
def arm_scaled(sides, kerns, k):
    sd = {c: ((k - 1) * L, (k - 1) * R) for c, (L, R) in sides.items()}
    kd = {tuple(p): (k - 1) * d for p, d in kerns.items() if len(p) == 2}
    return sd, kd


class B2Model:
    """b2_fit.fit on every answer (--extra, skip weight 1), features on the
    bench's 09-20 fonts, as shipped. predict() reads feats[p] at CALL time, so
    swapping a pair's feature row re-evaluates the model on another cut."""

    def __init__(self, style):
        J, W = b2_fit.with_extra(style, skip_w=1.0)
        cen = {p: n for p, n in census()}
        self.scope = sorted({p for p in J if b2_fit.in_scope(p)} |
                            {p for p, n in cen.items() if b2_fit.in_scope(p) and
                             (n >= b2_fit.CENSUS_MIN or (n >= b2_fit.CENSUS_MIN_MARK and any(c in b2_fit.MARKS for c in p)))})
        F0 = FT.Font(FT.FONTS[style])
        self.italic = style == "italic"
        self.feats = {p: FT.pair_features(F0, p[0], p[1], self.italic)[0] for p in self.scope}
        self.lsb, self.rsb, self.predict, self.ins = b2_fit.fit(style, {p: J[p] for p in J if p in self.feats},
                                                                 self.feats, W)

    def feat_rows(self, path):
        F = FT.Font(path)
        out = {}
        for p in self.scope:
            try:
                out[p] = FT.pair_features(F, p[0], p[1], self.italic)[0]
            except SystemExit:
                pass
        return out

    def term(self, p, row):
        keep = self.feats[p]; self.feats[p] = row
        try:
            return self.predict(p)
        finally:
            self.feats[p] = keep


def arm_b2(model, style, rows_w, rows_400, b2json):
    """Kern deltas: the kern b2_fit would write on this cut minus today's."""
    side = {**b2json["letters"], **b2json["marks"]}
    kd = {}
    for p in model.scope:
        if p not in rows_w or p not in rows_400 or p in b2_fit.HOLD[style]:
            continue
        give = side.get(p[0], [0, 0])[1] + side.get(p[1], [0, 0])[0]
        shift = model.term(p, rows_w[p]) - model.term(p, rows_400[p])
        k_new = int(round(model.predict(p) + shift - give))
        k_new = k_new if abs(k_new) >= b2_fit.MIN_KERN else 0
        k_old = b2json["kerns"].get(p, 0)
        if k_new != k_old:
            kd[tuple(p)] = k_new - k_old
    return kd


# ---------------------------------------------------------------- readings
def his_readings():
    """{style: {pair: [d on the 09-20 zero]}} -- bench, re-ask, extra rows."""
    out = {}
    for st in ("roman", "italic"):
        r = collections.defaultdict(list)
        for p, d in b2_fit.bench_fit.judgments(st, drop=()).items():
            r[p].append(d)
        out[st] = r
    ra = json.load(open(os.path.join(WS, "bench", "answers", "reask-2026-09-25-answers.json")))["answers"]
    for a in ra:
        out[a["style"]][a["pair"]].append(a["delta"])
    ex = json.load(open(os.path.join(WS, "bench", "answers", "extra-judgments.json")))["rows"]
    for a in ex:
        out[a["style"]][a["pair"]].append(a["d0920"])
    return out


def main():
    today, out = sys.argv[1], sys.argv[2]
    res = {"cuts": {}, "arms": {}}
    for style, cuts in CUTS.items():
        sides, kerns, b2json = correction(style)
        base = Font(os.path.join(today, f"Albo-{BASE[style]}.ttf")).n_anatomy()
        model = B2Model(style)
        print(f"{style}: B2 refit in-sample {model.ins:.2f} on {len(model.scope)} scope pairs "
              f"(shipped json says {b2json['in_sample']})", flush=True)
        rows_400 = model.feat_rows(os.path.join(today, f"Albo-{BASE[style]}.ttf"))
        for cut, wt in cuts:
            src = os.path.join(today, f"Albo-{cut}.ttf")
            an = Font(src).n_anatomy()
            ks, kc = an["stem"] / base["stem"], an["counter"] / base["counter"]
            res["cuts"][cut] = dict(style=style, weight=wt, stem=an["stem"], counter=an["counter"],
                                    k_stem=round(ks, 3), k_counter=round(kc, 3))
            print(f"  {cut:11s} stem {an['stem']:.0f} counter {an['counter']:.0f}  k_stem {ks:.3f} k_counter {kc:.3f}", flush=True)
            for arm, (sd, kd) in (("b-stem", arm_scaled(sides, kerns, ks)),
                                  ("c-rhythm", arm_scaled(sides, kerns, kc))):
                d = os.path.join(out, arm); os.makedirs(d, exist_ok=True)
                ng, nk = apply(src, os.path.join(d, f"Albo-{cut}.ttf"), sd, kd, style)
                res["arms"].setdefault(arm, {})[cut] = dict(glyphs_moved=ng, kern_pairs=nk)
            if cut == BASE[style]:
                kd = {}
            else:
                kd = arm_b2(model, style, model.feat_rows(src), rows_400, b2json)
            d = os.path.join(out, "d-b2"); os.makedirs(d, exist_ok=True)
            ng, nk = apply(src, os.path.join(d, f"Albo-{cut}.ttf"), {}, kd, style)
            res["arms"].setdefault("d-b2", {})[cut] = dict(glyphs_moved=ng, kern_pairs=nk,
                                                           kern_delta_mean_abs=round(float(np.mean([abs(v) for v in kd.values()])), 2) if kd else 0)
            print(f"    d-b2: {nk} kern glyph pairs changed", flush=True)
    json.dump(res, open(os.path.join(out, "arms.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
