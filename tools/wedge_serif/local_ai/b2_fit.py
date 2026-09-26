#!/usr/bin/env python3
"""Write the B2 spacing arm: glyph-identity + shape-feature ridge, as tables.

WHAT B2 IS. docs/local-ai-spacing-options-2026-09-26.md §2a: one ridge per
style over (a) each glyph's two bearings and (b) 38 shape features of the pair,
measured on the bench's own fonts. Held out on bench_fit's folds it scores
10.73 against the shipped pipeline's 11.66. This script fits it on ALL 370
non-g judgments (--extra: plus every later answer) and turns it into what the
builder ships. Since ROUND 396 it is Albo's DEFAULT spacing;
ALBO_SPACING_FIT=bench builds round 395's bench-fit tables instead.

HOW A PREDICTION BECOMES A FONT. The prediction for a pair is
    t(a, b) = rsb_id[a] + lsb_id[b] + w . x(a, b) + c
  * LOWERCASE and MARK bearings = the identity coefficients, rounded, NO
    reading floor (the 4-reading / 4-unit floors are part of what B2 beat).
    They REPLACE ROM_LC_ADJ / ALD_LC_ADJ / *_PUNCT_FIT one for one, the same
    semantics bench_fit.py's tables have. The g is held at round 340's value
    (owner 2026-09-21), and the fi/ffi ligatures ride the i's right side as
    they do today.
  * CAPITALS never become bearings (round 308's ruling stands); their identity
    term goes into kerns.
  * KERNS = round(t - what the new bearings already give), for every pair in
    SCOPE whose remainder is at least 4 units (the shipped letter floor).
    They REPLACE _BENCH_PAIRS_ROM / _BENCH_PAIRS_ITA and are added to what
    the pair already carries, exactly as those were.
  * SCOPE: every non-g bench pair, plus every census pair (pair_census.py, his
    books) seen >= 200 times (>= 10 when it carries a mark) whose right glyph is lowercase or a mark and whose
    left is a letter or a mark -- the classes the bench trained on. No g, no
    cap+cap, no mark+mark, no pair a ligature swallows (fi fl ff).
  * HOLDS: the pairs he set EXPLICITLY after the bench (rounds 384, 388, 389,
    390 in kern.py) keep round 395's white. `--holds A.ttf B.ttf` measures, on
    a first B2 build, how far each moved and writes the compensating kern.

    $VENV/bin/python b2_fit.py --census bigrams.json          # pass 1
    (build with ALBO_SPACING_FIT=b2)
    $VENV/bin/python b2_fit.py --census bigrams.json --holds BASE_DIR B2_DIR
"""
import argparse, json, os, sys
import numpy as np
from sklearn.preprocessing import StandardScaler

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, WS)
import bench_fit  # noqa: E402
import features as FT  # noqa: E402

OUT = os.path.join(WS, "outlines", "spacing_b2.json")
MARKS = set("'.,:;\"-!?")
ALPHA_ID, ALPHA_F = 1.0, 30.0
MIN_KERN = 4
CENSUS_MIN = 200
CENSUS_MIN_MARK = 10       # a mark's bearing reaches every letter beside it, so
                           # its rarer pairs must be in scope too (first build:
                           # h' m' c' opened ~30 units while e' n' t' were kerned)
AGL = {'.': 'period', ',': 'comma', ':': 'colon', ';': 'semicolon', "'": 'quotesingle',
       '"': 'quotedbl', '-': 'hyphen', '!': 'exclam', '?': 'question'}

# The pairs set by hand after the bench, per style (kern.py rounds 384-390).
HOLD = {
    "roman": ["fT", "'s", "'t", "or", "rd", "gr", "Vo", "Yo", "oc", "Jo", "Th", "Qu", "ba", "t.",
              "ed", "pa", "En", "ry", "Ka", "of", "ty", "wo", "ki", "ec", "rh", "hy", "th", "hm"],
    "italic": ["q'", "q\"", "Fi", "Fo", "Ye", "Yo", "Pa", "Po", "Pr", "Wa", "Wh", "Wi", "Am", "An",
               "Av", "or", "es", "r,", "fi", "gs", "y.", "El", "um", "rg", "ki", "ta", "Jo", "n'",
               "ru", "qu", "tr", "cy", "rh", "hy", "hm"],
}


def gnames(ch):
    """Glyph names a character's kern must be written on."""
    if ch == "'":
        return ["quotesingle", "quoteright"]      # round 388 precedent
    return [AGL.get(ch, ch)]


def in_scope(p):
    a, b = p
    if "g" in p or p in ("fi", "fl", "ff"):
        return False
    if a in MARKS and b in MARKS:
        return False
    return (a.isalpha() or a in MARKS) and (b.islower() or b in MARKS)


def fit(style, J, feats, W=None):
    """W: optional {pair: weight} (weighted ridge); missing pairs weigh 1."""
    pairs = sorted(J)
    glyphs = sorted({c for p in pairs for c in p})
    gi = {c: i for i, c in enumerate(glyphs)}
    G = len(glyphs)
    names = sorted(feats[pairs[0]])
    Xf = np.array([[feats[p][n] for n in names] for p in pairs])
    sc = StandardScaler().fit(Xf)
    A = np.zeros((len(pairs), 2 * G))
    for r, p in enumerate(pairs):
        A[r, 2 * gi[p[0]] + 1] = 1; A[r, 2 * gi[p[1]]] = 1
    Z = np.hstack([A, sc.transform(Xf), np.ones((len(pairs), 1))])
    pen = np.r_[np.full(2 * G, ALPHA_ID), np.full(len(names), ALPHA_F), 0.0]
    y = np.array([J[p] for p in pairs])
    sw = np.array([(W or {}).get(p, 1.0) for p in pairs])
    w = np.linalg.solve(Z.T @ (Z * sw[:, None]) + np.diag(pen), Z.T @ (sw * y))
    lsb = {c: w[2 * gi[c]] for c in glyphs}
    rsb = {c: w[2 * gi[c] + 1] for c in glyphs}
    wf, c0 = w[2 * G:-1], w[-1]

    def feat_term(p):
        x = sc.transform(np.array([[feats[p][n] for n in names]]))[0]
        return float(x @ wf + c0)

    def predict(p):
        return lsb.get(p[1], 0.0) + rsb.get(p[0], 0.0) + feat_term(p)
    ins = float(np.mean(np.abs(Z @ w - y)))
    return lsb, rsb, predict, ins


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--census", required=True)
    ap.add_argument("--holds", nargs=2, metavar=("BASE_DIR", "B2_DIR"))
    ap.add_argument("--skip-weight", type=float, default=1.0,
                    help="weight of a SKIPPED active-bench row (verdict skipped-ok, delta 0); "
                         "default 1 = a skip counts as a full judgment (owner 2026-09-26)")
    ap.add_argument("--consolidate", action="store_true",
                    help="move a glyph side's CONSISTENT kern remainder into its bearing (option, "
                         "2026-09-26; identical white on every in-scope pair up to rounding)")
    ap.add_argument("--extra", action="store_true",
                    help="also fold in bench/answers/extra-judgments.json (active_ingest.py): "
                         "each pair's judgment becomes the mean of every reading on the fit's zero")
    args = ap.parse_args()
    census = {p: n for p, n in json.load(open(args.census))["pairs"]}
    fonts = {s: FT.Font(p) for s, p in FT.FONTS.items()}
    out = json.load(open(OUT)) if (args.holds and os.path.exists(OUT)) else {}
    for style in ("roman", "italic"):
        J, W = with_extra(style, skip_w=args.skip_weight) if args.extra else (bench_fit.judgments(style), None)
        scope = sorted({p for p in J if in_scope(p)} |
                       {p for p, n in census.items() if in_scope(p) and
                        (n >= CENSUS_MIN or (n >= CENSUS_MIN_MARK and any(c in MARKS for c in p)))})
        feats = {}
        for p in scope:
            feats[p] = FT.pair_features(fonts[style], p[0], p[1], style == "italic")[0]
        lsb, rsb, predict, ins = fit(style, {p: J[p] for p in J if p in feats}, feats, W)
        letters, marks = {}, {}
        for c in sorted(set(lsb) | set(rsb)):
            L, R = int(round(lsb.get(c, 0))), int(round(rsb.get(c, 0)))
            if c.islower() and (L or R):
                letters[c] = [L, R]
            elif c in MARKS and (L or R):
                marks[c] = [L, R]
        side = {**{c: v for c, v in letters.items()}, **{c: v for c, v in marks.items()}}
        if args.consolidate:
            consolidate(side, letters, marks, scope, predict, style)
        kerns = {}
        for p in scope:
            give = side.get(p[0], [0, 0])[1] + side.get(p[1], [0, 0])[0]
            k = int(round(predict(p) - give))
            if abs(k) >= MIN_KERN and p not in HOLD[style]:
                kerns[p] = k
        st = out.setdefault(style, {})
        if not args.holds:
            st.update(letters=letters, marks=marks, kerns=kerns, holds={},
                      scope=len(scope), in_sample=round(ins, 2))
        print(f"{style}: {len(J)} judgments, in-sample {ins:.2f}; {len(letters)} letters, "
              f"{len(marks)} marks, {len(st['kerns'])} kerns over {len(scope)} pairs in scope")
        if args.holds:
            st["holds"] = measure_holds(style, *args.holds)
    json.dump(out, open(OUT, "w"), indent=1, ensure_ascii=False, sort_keys=True)
    print("wrote", OUT)


def consolidate(side, letters, marks, scope, predict, style, min_n=4, min_v=4):
    """B2 splits a glyph's own preference between its identity term and the
    shape features, so a side that wants +28 everywhere (the roman j's left,
    session 2) can ship as a +8 bearing plus six +24..+32 kerns. This moves the
    MEDIAN remainder of each lowercase/mark side (>= min_n in-scope pairs,
    |median| >= min_v) into the bearing; the kerns are then recomputed as
    usual, so every in-scope pair keeps its predicted white (to rounding) and
    the side's rarer, out-of-scope pairs now carry it too. Capitals are never
    bearings (round 308's ruling); the g stays held."""
    moved = []
    for pos, idx in ((1, 0), (0, 1)):         # glyph on the RIGHT -> its lsb; on the LEFT -> its rsb
        glyphs = sorted({p[pos] for p in scope})
        for c in glyphs:
            if c == "g" or not (c.islower() or c in MARKS):
                continue
            rem = [predict(p) - side.get(p[0], [0, 0])[1] - side.get(p[1], [0, 0])[0]
                   for p in scope if p[pos] == c]
            m = int(round(float(np.median(rem)))) if len(rem) >= min_n else 0
            if abs(m) >= min_v:
                tbl = letters if c.islower() else marks
                v = list(tbl.get(c, [0, 0])); v[idx] += m; tbl[c] = v; side[c] = v
                moved.append((c, "lsb" if idx == 0 else "rsb", m, len(rem)))
    print(f"  {style}: consolidated {len(moved)} sides: " +
          ", ".join(f"{c} {s} {m:+d} (n{n})" for c, s, m, n in moved))


def readings(style, drop=("g",)):
    """{pair: [(d on the 09-20 zero, weight class)]}: the bench (class "bench")
    plus every ingested row (active_ingest.py), class "skip" for a skipped
    active row (verdict skipped-ok), "extra" otherwise. g stays out, as in
    bench_fit (owner 2026-09-21)."""
    reads = {p: [(d, "bench")] for p, d in bench_fit.judgments(style, drop).items()}
    ex = os.path.join(WS, "bench", "answers", "extra-judgments.json")
    if os.path.exists(ex):
        for r in json.load(open(ex))["rows"]:
            if r["style"] == style and not any(c in drop for c in r["pair"]):
                cls = "skip" if r.get("verdict") == "skipped-ok" else "extra"
                reads.setdefault(r["pair"], []).append((r["d0920"], cls))
    return reads


def combine(reads, skip_w=1.0):
    """Each pair: the weighted MEAN of its readings (skip weight skip_w, all
    others 1) and, as the pair's weight in the fit, its largest reading weight
    -- a pair he only skipped weighs skip_w, one he touched weighs 1."""
    J, W = {}, {}
    for p, rs in reads.items():
        w = np.array([skip_w if c == "skip" else 1.0 for _, c in rs])
        J[p] = float(np.average([d for d, _ in rs], weights=w)) if w.sum() else 0.0
        W[p] = float(w.max())
    return J, W


def with_extra(style, drop=("g",), skip_w=1.0):
    return combine(readings(style, drop), skip_w)


def white_fn(path):
    """white(a, b) = rsb(a) + kern + lsb(b), kern by HarfBuzz, glyphs by char."""
    F = FT.Font(path)

    def white(a, b):
        names, adv, kern = F.shape(a, b)
        g = F.tt["glyf"][names[0]]; h = F.tt["glyf"][names[1]]
        rsb = adv - (g.xMax if g.numberOfContours else 0)
        lsb = h.xMin if h.numberOfContours else 0
        return rsb + kern + lsb
    return white


def measure_holds(style, base_dir, b2_dir):
    fn = "Albo-Regular.ttf" if style == "roman" else "Albo-Italic.ttf"
    wb, w2 = white_fn(os.path.join(base_dir, fn)), white_fn(os.path.join(b2_dir, fn))
    holds = {}
    for p in HOLD[style]:
        chars = [("'" if c == "'" else c) for c in p]
        for a in (["'", "’"] if chars[0] == "'" else [chars[0]]):
            for b in (["'", "’"] if chars[1] == "'" else [chars[1]]):
                d = wb(a, b) - w2(a, b)
                if d:
                    holds[a + b] = int(d)
    print(f"  {style}: {len(holds)} held pairs compensated: {holds}")
    return holds


if __name__ == "__main__":
    main()
