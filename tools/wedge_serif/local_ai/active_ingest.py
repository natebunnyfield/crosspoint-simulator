#!/usr/bin/env python3
"""Fold his answers from any post-bench page into the spacing fit, on ONE zero.

Every bench page has its own zero -- the font it served. The fit (bench_fit.py,
b2_fit.py, probe_fit.py) lives on the 2026-09-20 bench fonts' zero, so an
answer only counts once it is moved there:

    target white = white(pair, page's font) + his delta
    d on the fit's zero = target white - white(pair, bench/fonts-2026-09-20)
                          - tracking c, when the page's font carried it (see TRACKED_ZEROS)

White = rsb + kern + lsb (HarfBuzz), the measure every page's key file uses.
The conversion is exact for spacing. It is NOT exact where an outline changed
between the two fonts (rounds 391-395 re-cut some thick/thin strokes). There
the same bbox white can look different, and that residue is his to see, not
ours to correct.

Writes bench/answers/extra-judgments.json, one row per answer with its source,
session, raw delta and converted delta; `b2_fit.py --extra` folds them in.
Re-running replaces the rows of the same bench, so a later export supersedes an
earlier one.

    # the 50 outlier-bench answers (fonts-2026-09-25), once:
    $VENV/bin/python active_ingest.py --outliers
    # an active-bench session, from the page's Copy answers block or from an
    # ArtifactData dump of its "active" collection:
    $VENV/bin/python active_ingest.py answers.json      # or a directory
"""
import argparse, glob, json, os, re, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from b2_fit import white_fn  # noqa: E402

BENCH = os.path.join(WS, "bench")
EXTRA = os.path.join(BENCH, "answers", "extra-judgments.json")
FN = {"roman": "Albo-Regular.ttf", "italic": "Albo-Italic.ttf"}
Z0920 = {s: white_fn(os.path.join(BENCH, "fonts-2026-09-20", f)) for s, f in FN.items()}
# the shipped zeros (round 395; round 396 = B2), recorded beside the fit's so a row can be read
# against what he sees today
Z395 = {s: white_fn(os.path.join(BENCH, "fonts-2026-09-26", f)) for s, f in FN.items()}
Z396 = {s: white_fn(os.path.join(BENCH, "fonts-2026-09-26-r396", f)) for s, f in FN.items()}
Z397 = {s: white_fn(os.path.join(BENCH, "fonts-2026-09-26-r397", f)) for s, f in FN.items()}
Z398 = {s: white_fn(os.path.join(BENCH, "fonts-2026-09-26-r398", f)) for s, f in FN.items()}
Z399 = {s: white_fn(os.path.join(BENCH, "fonts-2026-09-26-r399", f)) for s, f in FN.items()}
Z402 = {s: white_fn(os.path.join(BENCH, "fonts-2026-09-26-r402", f)) for s, f in FN.items()}
Z405 = {s: white_fn(os.path.join(BENCH, "fonts-2026-09-26-r405", f)) for s, f in FN.items()}
Z409 = {s: white_fn(os.path.join(BENCH, "fonts-2026-09-26-r409", f)) for s, f in FN.items()}


# TRACKING c (round 393, owner "c . +6 (caps +3)") is applied by build.py ON TOP
# of the spacing tables, so the fit's zero must NOT contain it. Every page
# served from round 395 on (these zero dirs) DID contain it, so a reading taken
# there carries it and must give it back, or the build adds it twice. Tracking
# c is +3 on each side of every lowercase letter and every mark, 0 on a
# capital: verified against a round-395 build at ALBO_TRACK=a on all 1,486
# census pairs in both styles, 0 mismatches (2026-09-26). Found building the
# override arm: before this, sessions 1-3 were fitted 6 units loose (3 on
# capital pairs) -- round 397 and 398 carry that.
TRACKED_ZEROS = {"fonts-2026-09-26", "fonts-2026-09-26-r396", "fonts-2026-09-26-r397",
                 "fonts-2026-09-26-r398", "fonts-2026-09-26-r399", "fonts-2026-09-26-r402", "fonts-2026-09-26-r405",
                 "fonts-2026-09-26-r409", "fonts-2026-09-28-r430",
                 "fonts-2026-10-01-r453"}   # round 453 (build 279): the "sextile" / "aquí?" bench, 2026-10-01


def track_c(pair):
    return sum(3 for c in pair if c.islower() or c in "'.,:;\"-!?")


def zero_dir(zero):
    """'bench/fonts-2026-09-26 (round 395, 12b75e9)' -> 'fonts-2026-09-26'."""
    return (zero or "").split("/")[-1].split(" ")[0]


def load_extra():
    return json.load(open(EXTRA)) if os.path.exists(EXTRA) else {"note": __doc__.split("\n\n")[1], "rows": []}


def save_extra(ex, bench, rows):
    ex["rows"] = [r for r in ex["rows"] if r["bench"] != bench] + rows
    json.dump(ex, open(EXTRA, "w"), indent=1, ensure_ascii=False)
    print(f"{bench}: {len(rows)} rows written to {os.path.relpath(EXTRA, WS)} ({len(ex['rows'])} in all)")


def outliers():
    key = {(r["style"], r["id"]): r for r in json.load(open(os.path.join(BENCH, "outliers-2026-09-25.key.json")))["rows"]}
    ans = json.load(open(os.path.join(BENCH, "answers", "outliers-2026-09-25-answers.json")))["answers"]
    z = {s: white_fn(os.path.join(BENCH, "fonts-2026-09-25", f)) for s, f in FN.items()}
    rows, agree = [], 0
    for a in ans:
        r = key[(a["style"], a["id"])]
        p = r["pair"]
        w0 = z[a["style"]](p[0], p[1]); w20 = Z0920[a["style"]](p[0], p[1])
        agree += (w0 == r["white"])
        rows.append(dict(bench="outliers-2026-09-25", style=a["style"], pair=p, id=a["id"], delta=a["delta"],
                         white_zero=int(w0), white0920=int(w20), d0920=int(w0 + a["delta"] - w20),
                         d_r395=int(w0 + a["delta"] - Z395[a["style"]](p[0], p[1])),
                         d_r396=int(w0 + a["delta"] - Z396[a["style"]](p[0], p[1])),
                         d_r397=int(w0 + a["delta"] - Z397[a["style"]](p[0], p[1])),
                         d_r398=int(w0 + a["delta"] - Z398[a["style"]](p[0], p[1])),
                         d_r399=int(w0 + a["delta"] - Z399[a["style"]](p[0], p[1])),
                         d_r402=int(w0 + a["delta"] - Z402[a["style"]](p[0], p[1])),
                         d_r405=int(w0 + a["delta"] - Z405[a["style"]](p[0], p[1])),
                         session="2026-09-25/26", at=a.get("at"), kind="outlier"))
    print(f"outlier answers: {len(rows)}; page-font white matches the key's on {agree}/{len(rows)}")
    shift = [r["d0920"] - r["delta"] for r in rows]
    print(f"  zero shift 09-25 -> 09-20: median {np.median(shift):+.0f}, range {min(shift):+d}..{max(shift):+d} units")
    return "outliers-2026-09-25", rows


def read_answers(src):
    if os.path.isdir(src):
        out = []
        for f in glob.glob(os.path.join(src, "**", "*.json"), recursive=True):
            m = re.match(r"(roman|italic)_(.+)$", os.path.basename(f)[:-5])
            if not m:
                continue
            d = json.load(open(f))
            if d.get("touched"):
                out.append(dict(style=m[1], id=m[2], delta=d["delta"], at=d.get("at"),
                                session=d.get("session"), bench=d.get("bench"), verdict=d.get("verdict", "")))
        return (out[0]["bench"] if out else None), out
    text = open(src).read()
    blob = json.loads(text[text.index("{"):text.rindex("}") + 1])
    return blob["bench"], blob["answers"]


# THROUGH THE TABLES (2026-09-28). The bbox conversion above reads an outline
# change as a spacing change wherever a glyph was redrawn after the fit's zero:
# the family bench's italic `ry` came out +99 on the fit's zero where he moved
# it -1, because the italic y's tail travelled 106 units in round 409's resize.
# His slider moves a pair from the white the FIT shipped on that page, so where
# the page's own spacing tables are kept beside its fonts (bench/<zero>/
# spacing_b2.json) the target on the fit's zero is exactly
#     table value (rsb + lsb + kern, the fit's frame) + his delta
# -- no outline enters. The italic row stores + italic_delta, which b2_fit
# subtracts again. Held pairs (their white carries a hold) and pairs outside
# the fit's scope keep the bbox conversion. Rows say which: conv="tables"/"bbox".
def table_white(tables, style, p):
    import b2_fit
    T = tables[style]
    if p in HELD_AT_ZERO.get(style, ()) or not b2_fit.in_scope(p):
        return None
    if any(c.isalpha() and not c.isascii() for c in p):
        return None      # an accented letter is in no B2 table: its pair was never in a fit's scope (2026-10-01)
    side = {**T["letters"], **T["marks"]}
    return side.get(p[0], [0, 0])[1] + side.get(p[1], [0, 0])[0] + T["kerns"].get(p, 0)


# b2_fit.HOLD as it stood when those tables were built (round 430 held the roman rd)
HELD_AT_ZERO = {"roman": {"fT", "'s", "'t", "or", "rd", "gr", "Vo", "Yo", "oc", "Jo", "Th", "Qu", "ba", "t.",
                          "ed", "pa", "En", "ry", "Ka", "of", "ty", "wo", "ki", "ec", "rh", "hy", "th", "hm"},
                "italic": {"q'", "q\"", "Fi", "Fo", "Ye", "Yo", "Pa", "Po", "Pr", "Wa", "Wh", "Wi", "Am", "An",
                           "Av", "or", "es", "r,", "fi", "gs", "y.", "El", "um", "rg", "ki", "ta", "Jo", "n'",
                           "ru", "qu", "tr", "cy", "rh", "hy", "hm"}}


# ACCENTED PAIRS (2026-10-01, the "sextile" / "aquí?" bench, the first to ask one). B2 fits plain
# letters only; an accented letter takes its BASE letter's kerning in the build (kern.py
# _extend_composites) plus the mark clearances on top. So an answer on an accented pair is
# fitted as a reading of its BASE pair when the mark is FAR from the neighbour -- its 2-D
# nearest approach at the page's zero at least FAR x its own gap to its own letter (then the
# white he judged is the letters', as in "uí", acute 3.5x its gap from the u) and the two pairs
# kerned alike at that zero. Otherwise the mark is what he judged (the italic "í?", acute 0.82x
# its gap from the ?): the row is kept with fit_pair None and no fit sees it -- the clearance
# rule owns that white, and how his answer should move it is his ruling, not the fit's.
FAR = 2.0


def composite_base(p):
    """'uí' -> 'ui', 'í?' -> 'i?'; None when no letter is accented."""
    import unicodedata
    out, hit = [], False
    for c in p:
        if c.isalpha() and not c.isascii():
            c = unicodedata.normalize("NFD", c)[0]; hit = True
        out.append(c)
    return "".join(out) if hit else None


def far_mark(zero_font, p):
    """(ratio, same_kern): the accented letter's mark, nearest approach / own gap, at the zero."""
    sys.path.insert(0, os.path.join(WS, "instruments"))
    from mark_crowd import Font, nearest
    F = Font(zero_font); b = composite_base(p)
    w = next(i for i, c in enumerate(p) if c.isalpha() and not c.isascii())
    d = nearest(F, p, w, 0.0, what=False); g = F.own(p[w])
    def kern(q):
        sh = F.shape(q); cm = F.t.getBestCmap()
        return sh[1][1] - F.t["hmtx"][cm[ord(q[0])]][0]
    return (d[0] / g if d and g else 0.0), kern(p) == kern(b)


def b2_fit_delta_is_r409():
    import b2_fit
    return b2_fit._DDIR == b2_fit._D409


def active(src):
    bench, ans = read_answers(src)
    key = json.load(open(os.path.join(BENCH, bench + ".key.json")))
    rows_k = {(r["style"], r["id"]): r for r in key["rows"]}
    tpath = os.path.join(BENCH, zero_dir(key.get("zero")) or "", "spacing_b2.json")
    tables = json.load(open(tpath)) if key.get("zero") and os.path.exists(tpath) else None
    rows = []
    for a in ans:
        r = rows_k[(a["style"], a["id"])]
        fit_pair, mark_ratio = r["pair"], None
        base = composite_base(r["pair"])
        if base is not None:
            zf = os.path.join(BENCH, zero_dir(key.get("zero")), FN[a["style"]])
            mark_ratio, same = far_mark(zf, r["pair"])
            fit_pair = base if (mark_ratio >= FAR and same) else None
        tw = table_white(tables, a["style"], fit_pair or r["pair"]) if tables else None
        if tw is not None:
            import b2_fit
            d_t = tw + a["delta"] + (b2_fit.italic_delta(fit_pair or r["pair"]) if a["style"] == "italic" else 0.0)
        rows.append(dict(bench=bench, style=a["style"], pair=r["pair"], id=a["id"], delta=a["delta"],
                         white_zero=r["white0"], white0920=r["white0920"],
                         d0920=(int(round(d_t)) if tw is not None else
                                int(r["white0"] + a["delta"] - r["white0920"]
                                    - (track_c(r["pair"]) if zero_dir(key.get("zero")) in TRACKED_ZEROS else 0))),
                         d0920_bbox=int(r["white0"] + a["delta"] - r["white0920"]
                                        - (track_c(r["pair"]) if zero_dir(key.get("zero")) in TRACKED_ZEROS else 0)),
                         conv=("tables" if tw is not None else "bbox"),
                         delta_pair=("r409" if b2_fit_delta_is_r409() else "r463"),   # round 463: which re-basing pair the +italic_delta used
                         track_removed=(track_c(r["pair"]) if zero_dir(key.get("zero")) in TRACKED_ZEROS else 0),
                         d_r395=int(r["white0"] + a["delta"] - Z395[a["style"]](*r["pair"])),
                         d_r396=int(r["white0"] + a["delta"] - Z396[a["style"]](*r["pair"])),
                         d_r397=int(r["white0"] + a["delta"] - Z397[a["style"]](*r["pair"])),
                         d_r398=int(r["white0"] + a["delta"] - Z398[a["style"]](*r["pair"])),
                         d_r399=int(r["white0"] + a["delta"] - Z399[a["style"]](*r["pair"])),
                         d_r402=int(r["white0"] + a["delta"] - Z402[a["style"]](*r["pair"])),
                         d_r405=int(r["white0"] + a["delta"] - Z405[a["style"]](*r["pair"])),
                         d_r409=int(r["white0"] + a["delta"] - Z409[a["style"]](*r["pair"])),
                         zero=key.get("zero"),
                         **({"fit_pair": fit_pair, "mark_ratio": round(mark_ratio, 2)} if base is not None else {}),
                         session=a.get("session"), at=a.get("at"), kind=r["kind"],
                         verdict=a.get("verdict", "") or "",
                         previous0920=r.get("previous0920")))
    reps = [r for r in rows if r["kind"] == "repeat"]
    if reps:
        d = np.array([r["d0920"] - r["previous0920"] for r in reps])
        print(f"repeats: n={len(d)}, mean |new - previous| {np.abs(d).mean():.2f}, drift {d.mean():+.2f} "
              f"(his re-ask of 2026-09-25: 10.83, drift +5.4)")
    sess = sorted({r["session"] for r in rows if r["session"]})
    print(f"{bench}: {len(rows)} answers over {len(sess)} sitting(s): {', '.join(sess)}")
    return bench, rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src", nargs="?")
    ap.add_argument("--outliers", action="store_true")
    a = ap.parse_args()
    ex = load_extra()
    if a.outliers:
        save_extra(ex, *outliers())
    if a.src:
        save_extra(ex, *active(a.src))
    if not (a.outliers or a.src):
        ap.error("give an answers file/dir, or --outliers")
    print("next: b2_fit.py --census ... --extra   (refit B2 with every reading, then build ALBO_SPACING_FIT=b2)")


if __name__ == "__main__":
    main()
