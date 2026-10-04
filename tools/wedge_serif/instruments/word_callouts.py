#!/usr/bin/env python3
"""word_callouts.py -- the ranked list of letters that hurt the owner's frequent words, from the
numbers word_corpus.py, word_measure.py and word_parts.py write (docs/albo-word-images-2026-10-04.md).

THE RULE, stated once so it can be re-run rather than re-argued:

  A letter, in a cut, is CALLED OUT when its color in his words (word_measure.py's band: the
  letter's slot over its own word's color, mean of nine reader sizes) is at least 5% away from
  the reference median AND outside the range of every reference face at 7 or more of the 9 sizes
  (so one pixel phase cannot decide it). WATCH: at least 4% away and outside at 6 or more sizes.
  The reference panel is Georgia, Charter, Palatino, Times and ITC Berkeley Oldstyle in every cut,
  plus Albertus Medium in the Regular.

  "Words hurt" = the tokens in his books, in that cut, whose word contains the letter
  (word_corpus.py's letter_reach). The list is ranked by that number, across all four cuts, so a
  fault in the Regular (88.5% of what he reads) outranks the same fault in the Bold Italic (0.02%).

  RULED marks a letter whose measured property is an owner ruling; it is listed, not proposed.

  GLOBAL: each face's word width and word color over his 100 commonest words, at Albo's x-height,
  10 pt on the X3 -- the context every per-letter number sits in.

    $VENV instruments/word_callouts.py --work DIR [--albo DIR]   (DIR holds corpus.json, measure.json)
"""
import argparse, json, math, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import word_measure as WM  # noqa: E402

CL = {"Regular": "R", "Italic": "I", "Bold": "B", "BoldItalic": "Z"}
# (cut, letter) -> the ruling that owns the measured property. Each was read in its source.
RULED = {
    ("Regular", "a"): "roman a ruled 'as is' (owner, 2026-09-27, 72e31ee); top stroke on the o's line, T2 (round 462)",
    ("Regular", "o"): "bowls on profile B, 'Albertus-like firm' (round 58); 'the roman o at the owner's pick, 0.93 / 1.10' (round 226)",
    ("Italic", "b"): "italic bowls: the owner's thick/thin picks (round 395) -- 'a style direction, not a fit correction' (fit audit 2026-09-26, 2e)",
    ("Italic", "d"): "italic bowls: round 395 thick/thin picks",
    ("Italic", "p"): "italic bowls: round 395 thick/thin picks",
    ("Italic", "q"): "italic bowls: round 395; 'italic q ruled as is' (be9c380)",
    ("BoldItalic", "q"): "italic q ruled as is (be9c380)",
    ("Italic", "g"): "approved (approved.py); the cursive bent g (round 323)",
    ("BoldItalic", "g"): "approved (approved.py); the cursive bent g (round 323)",
    ("Regular", "g"): "the open g (rounds 331-341); its spacing is excluded from the bench since round 344",
    ("Bold", "g"): "the open g (rounds 331-341); spacing excluded from the bench",
    ("Italic", "S"): "italic S reach ruled LEAVE (owner, 2026-10-03)",
}
# Capitals already in the open owner todo, docs/albo-capitals-audit-2026-10-04.md, by the cuts that
# audit names them in (its sections 2-4): cited, not re-proposed. A capital flagged here in a cut the
# audit does not name is a NEW finding.
AUDIT = {}
for _c in "CGOQ":
    AUDIT[("Regular", _c)] = "light round (audit 4)"
AUDIT[("Regular", "Z")] = "light Z (audit 4)"
AUDIT[("Regular", "L")] = "heavy L (audit 4)"
for _c in "TWZHQ":
    AUDIT.setdefault(("Regular", _c), "wide (audit 3)")
for _cut in ("Regular", "Italic", "Bold", "BoldItalic"):
    AUDIT[(_cut, "I")] = "I narrow (audit 3)"
    AUDIT[(_cut, "N")] = "N short (audit 2)"
AUDIT[("Regular", "J")] = "J narrow (audit 3)"
for _cut in ("Bold", "BoldItalic"):
    for _c in "BEFPRLX":
        AUDIT[(_cut, _c)] = "narrow in the bolds (audit 3)"
    for _c in "ABCDEFGHJKLMOPQRSTUVWXYZ":
        AUDIT.setdefault((_cut, _c), "bold capitals' contrast (audit 1)")
for _c in "ELZ":
    AUDIT[("Bold", _c)] = "heavy in the Bold (audit 4)"


def classify(M, C, cut):
    A = M["Albo/" + cut]
    refs = [k for k in M if k.endswith("/" + cut) and not k.startswith("Albo/")]
    tot = C["cut_tokens"][CL[cut]]
    rows = []
    for ch, L in A["letters"].items():
        if not ch.isalpha():
            continue
        R = [M[r]["letters"][ch] for r in refs if ch in M[r]["letters"]]
        if len(R) < 3:
            continue
        med = float(np.median([r["band"] for r in R]))
        d = L["band"] / med - 1.0
        out = 0
        for sz in WM.SIZES:
            rv = [r["band_sizes"][sz] for r in R if sz in r["band_sizes"]]
            av = L["band_sizes"].get(sz)
            if av is None or not rv:
                continue
            out += (d < 0 and av < min(rv)) or (d > 0 and av > max(rv))
        level = ("CALL" if abs(d) >= 0.05 and out >= 7 else
                 "WATCH" if abs(d) >= 0.04 and out >= 6 else "fine")
        an = A["anatomy"].get(ch, {})
        ra = [M[r]["anatomy"][ch] for r in refs if ch in M[r]["anatomy"]]
        def rel(k):
            if k not in an or not ra:
                return None
            v = [x[k] for x in ra]
            return dict(albo=an[k], med=float(np.median(v)), lo=min(v), hi=max(v))
        reach = C["letter_reach"][CL[cut]].get(ch, 0)
        rows.append(dict(cut=cut, ch=ch, level=level, delta=d, sizes_out=out, band=L["band"], ref_med=med,
                         gapL=L.get("gapL"), gapR=L.get("gapR"), reach=reach, reach_share=reach / tot,
                         band_ink_n=rel("band_ink_n"), adv_n=rel("adv_n"), color_n=rel("color_n"),
                         ruled=RULED.get((cut, ch)), audit=AUDIT.get((cut, ch)) if ch.isupper() else None))
    return rows


def global_context(albo, corpus, n=100):
    """Word width (advance over x-height) and word color (band) over the n commonest words, each
    face at Albo's x-height, 10 pt on the X3, frequency-weighted."""
    C = json.load(open(corpus))
    words = [(r["word"], r["count"]) for r in C["top"] if r["word"].isascii()][:n]
    out = {}
    for lab, cut, p, i in WM.faces(albo):
        if cut != "Regular":
            continue
        F = WM.Face(p, i, WM.SIZES["x3-10"])
        wsum = csum = tw = 0.0
        for w, k in words:
            g, width = F.shape(w)
            _, wc = WM.slot_bands(F, w)
            wsum += k * width / F.xh_px; csum += k * wc; tw += k
        out[lab] = dict(width_per_xh=wsum / tw, color=csum / tw)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", required=True)
    ap.add_argument("--albo")
    a = ap.parse_args()
    M = json.load(open(os.path.join(a.work, "measure.json")))
    C = json.load(open(os.path.join(a.work, "corpus.json")))
    rows = []
    for cut in WM.CUTS:
        rows += classify(M, C, cut)
    flagged = sorted([r for r in rows if r["level"] != "fine"], key=lambda r: -r["reach"])
    res = dict(rows=rows, flagged=flagged)
    if a.albo:
        res["global"] = global_context(a.albo, os.path.join(a.work, "corpus.json"))
    json.dump(res, open(os.path.join(a.work, "callouts.json"), "w"), indent=1, default=float)
    print("| rank | letter | cut | words hurt (tokens, share of the cut) | color in his words vs references "
          "| sizes outside every reference | level | ink in the band / n | advance / n | owner ruling |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for k, r in enumerate(flagged, 1):
        bi, ad = r["band_ink_n"], r["adv_n"]
        own = r["ruled"] or (f"capitals audit: {r['audit']}" if r["audit"] else "")
        print(f"| {k} | {r['ch']} | {CL[r['cut']]} | {r['reach']:,} ({r['reach_share']:.1%}) | "
              f"{r['delta']:+.1%} ({r['band']:.3f} vs {r['ref_med']:.3f}) | {r['sizes_out']}/9 | {r['level']} | "
              + (f"{bi['albo']:.2f} [{bi['lo']:.2f}-{bi['hi']:.2f}]" if bi else "--") + " | "
              + (f"{ad['albo']:.2f} [{ad['lo']:.2f}-{ad['hi']:.2f}]" if ad else "--") + f" | {own} |")
    if "global" in res:
        print("\nGLOBAL (Regular, 100 commonest words, 10 pt X3, Albo's x-height):")
        for lab, g in res["global"].items():
            print(f"  {lab:9s} word width {g['width_per_xh']:.2f} x-heights   word color {g['color']:.3f}")


if __name__ == "__main__":
    main()
