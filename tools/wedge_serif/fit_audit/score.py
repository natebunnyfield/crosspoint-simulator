"""THE FIT METRIC: combine axes (a)-(h) into one score per glyph per cut.

Definition (docs/albo-fit-audit-2026-09-26.md section 1):

  1. For every SUB-AXIS s and every face X (an Albo cut, or a reference face's
     matching cut), z_X(ch) = robust z of the glyph against its CONSTRUCTION
     FAMILY in that face (common.FAMILY; median centre, 1.4826 x MAD scale,
     shrunk toward the pooled MAD because a family of five has a noisy MAD).
  2. EXCESS over the references: e(ch) = (z_Albo - median_r z_r) /
     sqrt(1 + s_r^2), s_r the robust spread of the references' z for that
     glyph. A 7 is light in EVERY face; the metric asks whether Albo's 7 is
     lighter than a 7 has to be. The misfit audit's lesson (2026-09-21: two
     of three findings dissolved on a reference) is built in, not bolted on.
     Figures are compared only with faces whose DEFAULT figures are old-style
     (Georgia, Hoefler), because Albo's are.
  3. An AXIS takes its sub-axis of largest |e| (named, so a flag says why).
  4. FIT SCORE  F = sqrt( sum_axes w * max(0, |e| - 1)^2 ).
     Inside one reference-adjusted sigma is ordinary variation and costs
     nothing; past it the cost is quadratic, so ONE axis at 3 sigma scores 2.0
     on its own (a letter flagged for a single reason stays visible), and
     several moderate axes add up.
     Weights: colour 1, stroke 1, legibility 1 (what the reader sees at
     reading size, and "legible" is in the brief); proportion 0.75 (visible,
     but references disagree most here); spacing fight 0.75 (his own
     evidence, but spacing already corrects it); vertical 0.5 (1 px is ~60
     units at 16.7 ppem, so a few units of overshoot are sub-pixel at 1x);
     bearings 0.5 (overlaps the spacing fight); cross-cut 0.5 (derived from
     a-c).
  FLAG: F >= 2.0.

    python3 score.py --geom g.json --legib l.json --spacing s.json --tag r402 --out fit.json
"""
import argparse, json, math, os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import CHARS, CUTS, FAMILY, FIG, LC, UC, REFS, PARTNER, robust_z  # noqa: E402

AXES = {
    "a": ("colour", ["col1x", "col2x"], 1.0),
    "b": ("stroke", ["stroke", "thin", "cut"], 1.0),
    "c": ("proportion", ["width", "open"], 0.75),
    "d": ("vertical", ["top", "bot"], 0.5),
    "e": ("bearings", ["balance", "loose"], 0.5),
    "f": ("spacing fight", ["b2_bearing", "b2_kern", "bench_push"], 0.75),
    "g": ("legibility", ["legib"], 1.0),
    "h": ("cross-cut", ["xcut"], 0.5),
}
FLAG = 2.0
# THE SMALLEST DIFFERENCE EACH SUB-AXIS COUNTS AS ONE SIGMA. Absolute where the
# unit is already normalised by the reference height (0.015 of an x-height is
# 6 Albo units, a tenth of a pixel at 16.7 ppem); RELATIVE (a fraction of the
# face's median) where it is in font units, because the panel's UPMs differ.
FLOORS = {"col1x": ("rel", 0.03), "col2x": ("rel", 0.03), "stroke": ("rel", 0.04),
          "thin": ("rel", 0.05), "cut": ("rel", 0.05), "width": ("abs", 0.02),
          "open": ("abs", 0.02), "top": ("abs", 0.015), "bot": ("abs", 0.015),
          "balance": ("abs", 0.03), "loose": ("abs", 0.02), "legib": ("abs", 0.25)}
OLDSTYLE_REFS = ["Georgia", "Hoefler"]
# Variant switches, for the sensitivity table in the doc (validate.py
# --variants). The shipped metric is REFNORM "full".
REFNORM = "full"      # "full" | "diff" (no reference-spread term) | "none" (family z only)


def legib_values(L):
    """Relative log-odds of error per glyph (glyph minus the face's median)
    and its standard error. None when the face was not read."""
    if L is None:
        return {}, {}
    lo, se = {}, {}
    for ch in CHARS:
        n = L["occ"].get(ch, 0)
        if not n:
            continue
        e = L["err"].get(ch, 0)
        p = (e + 0.5) / (n + 1.0)
        lo[ch] = math.log(p / (1 - p))
        se[ch] = math.sqrt(1 / (e + 0.5) + 1 / (n - e + 0.5))
    m = np.median(list(lo.values()))
    return {k: v - m for k, v in lo.items()}, se


def face_table(G, L):
    """{sub-axis: {ch: value}} for one face."""
    T = {}
    for s in ["col1x", "col2x", "stroke", "thin", "cut", "width", "open", "top", "bot", "balance", "loose"]:
        T[s] = {ch: (G["glyphs"][ch].get(s) if G["glyphs"][ch].get(s) is not None else float("nan"))
                for ch in G["glyphs"]}
    lv, se = legib_values(L)
    T["legib"] = lv
    T["_legib_se"] = se
    return T


def zmap(vals, s=None):
    chars = [c for c in CHARS if c in vals]
    v = [vals[c] for c in chars]
    fl = 0.0
    if s in FLOORS:
        kind, x = FLOORS[s]
        fl = x if kind == "abs" else x * float(np.nanmedian(np.abs(v)))
    z = robust_z(v, [FAMILY[c] for c in chars], floor=fl)
    return dict(zip(chars, z))


def score_cut(geom, legib, spacing, tag, cut):
    key = f"{tag}/{cut}"
    if key not in geom or "glyphs" not in geom[key]:
        return None
    A = face_table(geom[key], legib.get(key))
    refs = {r: face_table(geom[f"{r}/{cut}"], legib.get(f"{r}/{cut}")) for r in REFS}
    rows = {ch: {"sub": {}, "axes": {}} for ch in CHARS if ch in A["col1x"]}
    for s in AXES["a"][1] + AXES["b"][1] + AXES["c"][1] + AXES["d"][1] + AXES["e"][1] + ["legib"]:
        if not A[s]:
            continue
        za = zmap(A[s], s)
        zr = {r: zmap(t[s], s) for r, t in refs.items() if t[s]}
        # the legibility z also carries the glyph's own counting noise
        if s == "legib":
            scale = 1.4826 * np.median(np.abs([v for v in A["legib"].values()])) or 1.0
        for ch in rows:
            if ch not in za or np.isnan(za[ch]):
                continue
            use = OLDSTYLE_REFS if ch in FIG else list(zr)
            rz = [zr[r][ch] for r in use if r in zr and ch in zr[r] and not np.isnan(zr[r][ch])]
            if not rz:
                continue
            med = float(np.median(rz))
            sr = 1.4826 * float(np.median(np.abs(np.array(rz) - med))) if len(rz) >= 3 else 0.5
            den = 1.0 + sr ** 2
            if REFNORM == "diff":
                den = 1.0
            elif REFNORM == "none":
                med, den = 0.0, 1.0
            if s == "legib":
                den += (A["_legib_se"].get(ch, 0) / scale) ** 2
            rows[ch]["sub"][s] = (za[ch] - med) / math.sqrt(den)
    # (f) spacing fight: no reference exists for his answers, so it is a robust
    # z within the glyph's CASE (spacing is not a construction property).
    sp = spacing.get(cut) if spacing and tag == spacing.get("_tag") else None
    if sp:
        for s in AXES["f"][1]:
            chars = [c for c in rows if c in sp and sp[c].get(s) is not None
                     and not (isinstance(sp[c].get(s), float) and np.isnan(sp[c][s]))]
            if len(chars) < 5:
                continue
            v = np.array([sp[c][s] for c in chars], float)
            z = robust_z(v, ["lc" if c in LC else "uc" for c in chars])
            for c, zz in zip(chars, z):
                rows[c]["sub"][s] = max(0.0, zz)   # only MORE fight than usual counts
    # axes a-g
    for ch, r in rows.items():
        for ax, (name, subs, w) in AXES.items():
            if ax == "h":
                continue
            cand = [(abs(r["sub"][s]), r["sub"][s], s) for s in subs if s in r["sub"]]
            if cand:
                _, v, s = max(cand)
                r["axes"][ax] = {"z": v, "by": s}
    return rows


def add_crosscut(all_rows, tag):
    """(h): the part of a glyph's a-c misfit its weight partner does NOT share.
    A deliberate irregularity is drawn into every cut; an accident usually
    lands in one (docs/albo-imperfections.md: a TABLE, never a jitter)."""
    for cut in CUTS:
        R, P = all_rows.get(cut), all_rows.get(PARTNER[cut])
        if not R or not P:
            continue
        for ch, r in R.items():
            if ch not in P:
                continue
            best, by = 0.0, None
            for s in AXES["a"][1] + AXES["b"][1] + AXES["c"][1]:
                if s in r["sub"] and s in P[ch]["sub"]:
                    d = abs(r["sub"][s]) - abs(P[ch]["sub"][s])
                    if d > best:
                        best, by = d, s
            r["axes"]["h"] = {"z": best, "by": by}


def finish(all_rows):
    for cut, R in all_rows.items():
        for ch, r in R.items():
            F2 = 0.0
            for ax, (name, subs, w) in AXES.items():
                if ax in r["axes"]:
                    F2 += w * max(0.0, abs(r["axes"][ax]["z"]) - 1.0) ** 2
            r["F"] = math.sqrt(F2)
            top = max(r["axes"].items(), key=lambda kv: AXES[kv[0]][2] * max(0, abs(kv[1]["z"]) - 1) ** 2)
            r["reason"] = top[0]
            r["flag"] = r["F"] >= FLAG
            r["family"] = FAMILY[ch]
    return all_rows


def score_tag(geom, legib, spacing, tag, with_spacing=True):
    sp = dict(spacing, _tag=tag) if (spacing and with_spacing) else None
    rows = {}
    for cut in CUTS:
        r = score_cut(geom, legib, sp, tag, cut)
        if r:
            rows[cut] = r
    add_crosscut(rows, tag)
    return finish(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--geom", required=True)
    ap.add_argument("--legib", required=True)
    ap.add_argument("--spacing")
    ap.add_argument("--tag", default="r402")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    geom, legib = json.load(open(a.geom)), json.load(open(a.legib))
    spacing = json.load(open(a.spacing)) if a.spacing else None
    rows = score_tag(geom, legib, spacing, a.tag)
    json.dump(rows, open(a.out, "w"), indent=1, default=float)
    for cut, R in rows.items():
        top = sorted(R.items(), key=lambda kv: -kv[1]["F"])[:15]
        nflag = sum(r["flag"] for r in R.values())
        print(f"\n{cut}: {nflag} of {len(R)} flagged (F >= {FLAG})")
        for ch, r in top:
            ax = " ".join(f"{k}{r['axes'][k]['z']:+.1f}" for k in "abcdefgh" if k in r["axes"])
            print(f"  {ch}  F {r['F']:.2f}  [{r['reason']}:{r['axes'][r['reason']]['by']}]  {ax}")


if __name__ == "__main__":
    main()
