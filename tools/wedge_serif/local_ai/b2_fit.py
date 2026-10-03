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
import argparse, re, json, os, sys
import numpy as np
from sklearn.preprocessing import StandardScaler

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, WS)
import bench_fit  # noqa: E402
import features as FT  # noqa: E402

OUT = os.path.join(WS, "outlines", os.environ.get("ALBO_SPACING_TABLES", "spacing_b2.json"))
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
    # 2026-10-01: roman ed and italic qu left -- he read both again on the words bench (ed a
    # repeat, -8; qu in "aquí?", +1), so B2 fits them from his readings (round 431's rule)
    "roman": ["fT", "'s", "'t", "or", "gr", "Vo", "Yo", "oc", "Jo", "Th", "Qu", "ba", "t.",
              "pa", "En", "ry", "Ka", "of", "ty", "wo", "ki", "ec", "rh", "hy", "th", "hm"],
    "italic": ["q'", "q\"", "Fi", "Fo", "Ye", "Yo", "Pa", "Po", "Pr", "Wa", "Wh", "Wi", "Am", "An",
               "Av", "or", "es", "r,", "fi", "gs", "y.", "El", "um", "rg", "ki", "ta", "Jo", "n'",
               "ru", "tr", "cy", "rh", "hy", "hm"],
}


# ROUND 409 -- THE ITALIC WAS RE-DRAWN UNDER HIS READINGS (arm m: x-height
# 1.015, set width 1.15, nib 0.92; docs/albo-italic-size-nib-2026-09-26.md).
# Every italic reading is a delta on the 09-20 zero, i.e. an ABSOLUTE target
# white  T = white0920 + d.  A new outline moves the white the fit rule gives
# a pair before any table touches it, by
#     delta(p) = white(new outline, same tables) - white(old outline, same tables)
# (ALBO_B2_ITALIC_NEW / _OLD: two Italic builds identical in every table, kern,
# hold, clearance and tracking, differing only in the outline -- so all of those
# cancel). "White" for delta is the gap between the two glyphs' INK EXTREMES
# INSIDE THE X-HEIGHT BAND (the band the fit rule spaces on), at 1 unit per
# pixel; the bbox white (rsb + kern + lsb) is used only where either glyph has
# no x-band ink (quotes). The bbox white reads a stretched ascender's or tail's
# lean as spacing: d-e, d-o, d-comma read +19..+21 on the bbox and 0 in the
# band (measured 2026-09-26, 188 bench pairs: medians +2 bbox, +4 band). The pair's zero on the new outline is white0920 + delta, the fit's
# target there is  d - delta = T - (white0920 + delta),  and the shape features
# are measured on the NEW glyphs placed at that zero white (ZeroFont). The
# `kern` feature keeps the 09-20 font's own kern, which is what it always meant.
# FROM ROUND 409 THIS IS THE DEFAULT: the two builds live in
# bench/italic-delta-r409/ (-old: round 408's outline, -new: round 409's, both
# on round 405's tables), so every later refit and every active bench keeps the
# italic on its new zero. ALBO_B2_ITALIC_NEW=off gives the pre-409 behaviour
# (how the "before" column of the round-409 CV was produced); the env vars can
# also name other builds. The roman never takes this path.
#
# INGEST NEEDS NOTHING NEW. active_ingest.py's d0920 = page white + delta -
# white0920 - tracking, on whatever glyphs the page served. For a page served
# on the round-409 italic that is  T - white0920  measured on the NEW glyphs,
# and the new zero's white on the new glyphs is white0920 + delta(p) (ZeroFont
# places them there), so  d0920 - delta(p)  is right for those rows too.
#
# ROUND 463 -- THE PAIR REFRESHED TO TODAY'S OUTLINE (owner 2026-10-02, "Refresh
# and refit now"). The -new build in italic-delta-r409/ is round 409's outline,
# so every italic letter redrawn since -- the c's drawn top (432-435), the a
# (419), the r (438-442), the x (461) -- was re-based against its OLD outline
# and each needed a hand bearing to keep its whites (A_RSB, R_DRSB, X_DLSB, all
# retired with this round). bench/italic-delta-r463/ keeps the same -old and
# builds -new from today's outline on the same round-405 tables with those
# corrections off (its README has the command and the check: every letter not
# redrawn since 409 moves exactly 0). ALBO_B2_DELTA=r409 selects the old pair.
# AND THE DELTA IS NOW KERN-FREE: each build's band gap minus that pair's own
# kern, so a hand kern that changed in kern.py between the two builds (round
# 455 released the italic qu's -16) cannot read as outline. On the r409 pair,
# whose two builds carry identical kerns, this changes nothing (checked: the
# refit reproduces the shipped tables exactly with ALBO_B2_DELTA=r409).
_D409 = os.path.join(WS, "bench", "italic-delta-r409")
_D463 = os.path.join(WS, "bench", "italic-delta-r463")
_DDIR = _D409 if os.environ.get("ALBO_B2_DELTA", "r463") == "r409" else _D463
_IT_NEW = os.environ.get("ALBO_B2_ITALIC_NEW", os.path.join(_DDIR, "Albo-Italic-new.ttf"))
_IT_OLD = os.environ.get("ALBO_B2_ITALIC_OLD", os.path.join(_DDIR, "Albo-Italic-old.ttf"))
if (_IT_NEW or "").lower() in ("off", "0", "none", ""):
    _IT_NEW = _IT_OLD = None
_DELTA = {}


def xband_gap(F, a, b):
    """Ink-extreme gap inside the x band (0..XH), units, rasterized at 1 unit
    per pixel; None when either glyph has no ink there."""
    saved = FT.U
    FT.U = 1.0
    try:
        names, adv, kern = F.shape(a, b)
        W = int(FT.X0 + adv + kern + 1400); H = int(FT.BASE + 1000)
        A = F.mask(names[0], 0, W, H); B = F.mask(names[1], adv + kern, W, H)
        _, RA = FT.edges(A); LB, _ = FT.edges(B)
    finally:
        FT.U = saved
    yv = (H - np.arange(H)) - FT.BASE
    xs = (yv >= 0) & (yv < FT.XH)
    if not (np.any(xs & ~np.isnan(RA)) and np.any(xs & ~np.isnan(LB))):
        return None
    return float(np.nanmin(np.where(xs, LB, np.nan)) - np.nanmax(np.where(xs, RA, np.nan)) - 1.0)


# ALBO_B2_REBASE_SKIP="c": letters whose re-basing stays on the r409 pair (their
# post-409 redraw is NOT re-based): an arm for a letter whose outline change is a
# terminal the band-extreme white over-reads (round 463's c, its drawn top).
_SKIP = set(os.environ.get("ALBO_B2_REBASE_SKIP", ""))
_R409_PAIR = {}


def _delta_r409(p):
    if not _R409_PAIR:
        _R409_PAIR["n"], _R409_PAIR["o"] = FT.Font(os.path.join(_D409, "Albo-Italic-new.ttf")), FT.Font(os.path.join(_D409, "Albo-Italic-old.ttf"))
    N, O = _R409_PAIR["n"], _R409_PAIR["o"]
    xn, xo = xband_gap(N, p[0], p[1]), xband_gap(O, p[0], p[1])
    if xn is None or xo is None:
        return None
    return (xn - N.shape(p[0], p[1])[2]) - (xo - O.shape(p[0], p[1])[2])


def italic_delta(p):
    if not (_IT_NEW and _IT_OLD):
        return 0.0
    if _SKIP and (p[0] in _SKIP or p[1] in _SKIP) and _DDIR != _D409:
        # the skipped letter's side keeps r409's delta; the other letter's side moves
        d409 = _delta_r409(p)
        if d409 is not None:
            key = ("skip", p)
            if key not in _DELTA:
                full = _italic_delta_full(p)
                # replace the skipped glyph's own share (measured as its change against r409 with a neutral partner)
                share = 0.0
                for side, g in ((0, p[0]), (1, p[1])):
                    if g in _SKIP:
                        partner = "n"
                        q = (g + partner) if side == 0 else (partner + g)
                        share += _italic_delta_full(q) - (_delta_r409(q) or 0.0)
                _DELTA[key] = full - share
            return _DELTA[key]
    return _italic_delta_full(p)


def _italic_delta_full(p):
    if not (_IT_NEW and _IT_OLD):
        return 0.0
    if not _DELTA:
        _DELTA["_new"], _DELTA["_old"] = FT.Font(_IT_NEW), FT.Font(_IT_OLD)
        _DELTA["_wn"], _DELTA["_wo"] = white_fn(_IT_NEW), white_fn(_IT_OLD)
    if p not in _DELTA:
        xn, xo = xband_gap(_DELTA["_new"], p[0], p[1]), xband_gap(_DELTA["_old"], p[0], p[1])
        kn, ko = _DELTA["_new"].shape(p[0], p[1])[2], _DELTA["_old"].shape(p[0], p[1])[2]   # round 463: kern-free
        _DELTA[p] = ((xn - kn) - (xo - ko)) if (xn is not None and xo is not None) else \
            float((_DELTA["_wn"](p[0], p[1]) - kn) - (_DELTA["_wo"](p[0], p[1]) - ko))
    return _DELTA[p]


# ROUND 463 -- A READING TAKEN ON A POST-409 OUTLINE. A row ingested through the
# page's own tables (conv "tables", 2026-09-28 on) stores  table + delta +
# italic_delta(pair)  with italic_delta from the pair in force AT INGEST -- the
# r409 pair for every row so far -- so it stood for the page's outline only if
# that page showed round 409's glyphs. Two benches did not: the family bench
# (zero round 430: the r 18 units tighter on its right, the a and j redrawn) and
# the words bench (zero round 453: the a, c, e and r redrawn since 409). Each
# such row is re-based by its OWN page's outline instead:
#     d0920 - italic_delta(pair) + (gap(page) - gap(r409 new))
# both gaps kern-free, the page build being that round's outline on the same
# round-405 tables (bench/italic-delta-r463/page-r430.ttf, page-r453.ttf; the
# README). Bbox rows already stand on their page's own glyphs and are untouched.
# A row ingested from now on records the pair it was converted with
# ("delta_pair"), and a page outline not listed here adds nothing.
_PAGES = {"family-2026-09-28": "page-r430.ttf", "words-2026-10-01": "page-r453.ttf"}
_PAGE_F, _R409_F = {}, {}


def page_correction(row, pair):
    if row.get("conv") != "tables" or row.get("delta_pair", "r409") != "r409" or _DDIR == _D409:
        return 0.0
    fn = _PAGES.get(row.get("bench"))
    if not fn:
        return 0.0
    if fn not in _PAGE_F:
        _PAGE_F[fn] = FT.Font(os.path.join(_D463, fn))
    if not _R409_F:
        _R409_F["f"] = FT.Font(os.path.join(_D409, "Albo-Italic-new.ttf"))
    P, R = _PAGE_F[fn], _R409_F["f"]
    gp, gr = xband_gap(P, pair[0], pair[1]), xband_gap(R, pair[0], pair[1])
    if gp is None or gr is None:
        return 0.0
    return (gp - P.shape(pair[0], pair[1])[2]) - (gr - R.shape(pair[0], pair[1])[2])


class ZeroFont(FT.Font):
    """The NEW italic's glyphs, each pair placed at its zero white
    (white0920 + delta); the 09-20 font supplies the reference white and kern."""

    def __init__(self, new_path, old0920_path):
        super().__init__(new_path)
        self.z = FT.Font(old0920_path)
        self.wz, self.wn = white_fn(old0920_path), white_fn(new_path)

    def shape(self, a, b):
        names, adv, kern = super().shape(a, b)
        want = self.wz(a, b) + italic_delta(a + b)
        return names, adv, kern + (want - self.wn(a, b))


def feature_fonts():
    fonts = {s: FT.Font(p) for s, p in FT.FONTS.items()}
    if _IT_NEW and _IT_OLD:
        fonts["italic"] = ZeroFont(_IT_NEW, FT.FONTS["italic"])
    return fonts


def pair_feats(fonts, style, p):
    f = FT.pair_features(fonts[style], p[0], p[1], style == "italic")[0]
    if isinstance(fonts[style], ZeroFont):
        f["kern"] = float(fonts[style].z.shape(p[0], p[1])[2])
    return f


def judgments0(style, drop=("g",)):
    """bench_fit.judgments on the fit's zero -- shifted onto the new italic's."""
    return {p: d - (italic_delta(p) if style == "italic" else 0.0)
            for p, d in bench_fit.judgments(style, drop).items()}


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


# 2026-09-28, SHIPPED (round 431, owner chose arm B): ALBO_B2_CLASSES=<alpha> adds SIDE-CLASS
# terms -- one per (left glyph, right glyph's left-side class) and one per (left
# glyph's right-side class, right glyph), ridge-penalised at alpha. The family
# bench showed the r's right side wanting -15..-30 before a round letter and
# +10..+27 before a stem (rh rt rb rk), which one rsb cannot say and the shape
# features did not learn at any alpha. Held-out (10-fold) 8.82 -> 8.65 at 3.
# The terms land in KERNS (they are pair-level), never in bearings.
CLASSES = float(os.environ.get("ALBO_B2_CLASSES", "3") or 0)   # owner 2026-09-28: "B recency + classes" ships; 0 = off
CLASS_STYLES = os.environ.get("ALBO_B2_CLASS_STYLES", "roman").split(",")   # italic held-out 8.81 -> 9.06 with them
LCLS = {**{c: "round" for c in "ocedqasg"}, **{c: "stem" for c in "hbklnmripuj"},
        **{c: "diag" for c in "vwyx"}, "t": "t", "f": "f", "z": "z"}      # a glyph's LEFT side
RCLS = {**{c: "round" for c in "ocbpes"}, **{c: "stem" for c in "hdlnmiauqj"},
        **{c: "diag" for c in "vwyx"}, "r": "r", "t": "t", "f": "f", "k": "k", "z": "z"}  # its RIGHT side


def lcls(c):
    return LCLS.get(c, "cap" if c.isupper() else "mark")


def rcls(c):
    return RCLS.get(c, "cap" if c.isupper() else "mark")


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
    on = CLASSES and style in CLASS_STYLES
    k1 = sorted({(p[0], lcls(p[1])) for p in pairs}) if on else []
    k2 = sorted({(rcls(p[0]), p[1]) for p in pairs}) if on else []
    i1 = {k: i for i, k in enumerate(k1)}; i2 = {k: i for i, k in enumerate(k2)}
    C = np.zeros((len(pairs), len(k1) + len(k2)))
    for r, p in enumerate(pairs):
        if on:
            C[r, i1[(p[0], lcls(p[1]))]] = 1; C[r, len(k1) + i2[(rcls(p[0]), p[1])]] = 1
    Z = np.hstack([A, C, sc.transform(Xf), np.ones((len(pairs), 1))])
    pen = np.r_[np.full(2 * G, ALPHA_ID), np.full(len(k1) + len(k2), CLASSES or 1.0), np.full(len(names), ALPHA_F), 0.0]
    y = np.array([J[p] for p in pairs])
    sw = np.array([(W or {}).get(p, 1.0) for p in pairs])
    w = np.linalg.solve(Z.T @ (Z * sw[:, None]) + np.diag(pen), Z.T @ (sw * y))
    lsb = {c: w[2 * gi[c]] for c in glyphs}
    rsb = {c: w[2 * gi[c] + 1] for c in glyphs}
    wc = w[2 * G:2 * G + len(k1) + len(k2)]
    wf, c0 = w[2 * G + len(k1) + len(k2):-1], w[-1]

    def feat_term(p):
        x = sc.transform(np.array([[feats[p][n] for n in names]]))[0]
        t = float(x @ wf + c0)
        if on:
            j1, j2 = i1.get((p[0], lcls(p[1]))), i2.get((rcls(p[0]), p[1]))
            t += (wc[j1] if j1 is not None else 0.0) + (wc[len(k1) + j2] if j2 is not None else 0.0)
        return t

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
    fonts = feature_fonts()
    out = json.load(open(OUT)) if (args.holds and os.path.exists(OUT)) else {}
    for style in ("roman", "italic"):
        J, W = with_extra(style, skip_w=args.skip_weight) if args.extra else (judgments0(style), None)
        scope = sorted({p for p in J if in_scope(p)} |
                       {p for p, n in census.items() if in_scope(p) and
                        (n >= CENSUS_MIN or (n >= CENSUS_MIN_MARK and any(c in MARKS for c in p)))})
        feats = {}
        for p in scope:
            feats[p] = pair_feats(fonts, style, p)
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


def _when(r):
    """A reading's time in days (UTC). Rows carry `at`; an older row without one
    takes its bench's date at noon."""
    import datetime as _dt
    t = r.get("at")
    if not t:
        m = re.search(r"(\d{4}-\d{2}-\d{2})", r.get("bench", "")) or re.search(r"(\d{4}-\d{2}-\d{2})", BENCH_DATE)
        t = m.group(1) + "T12:00:00Z"
    return _dt.datetime.fromisoformat(t.replace("Z", "+00:00")).timestamp() / 86400.0


BENCH_DATE = "2026-09-20"


def readings(style, drop=("g",)):
    """{pair: [(d on the 09-20 zero, weight class, days)]}: the bench (class
    "bench", 2026-09-20) plus every ingested row (active_ingest.py), class
    "skip" for a skipped active row (verdict skipped-ok), "extra" otherwise.
    g stays out, as in bench_fit (owner 2026-09-21)."""
    t0 = _when({"bench": BENCH_DATE})
    reads = {p: [(d, "bench", t0)] for p, d in judgments0(style, drop).items()}
    ex = os.path.join(WS, "bench", "answers", "extra-judgments.json")
    if os.path.exists(ex):
        for r in json.load(open(ex))["rows"]:
            # an ACCENTED pair counts as its base pair's reading only where active_ingest set
            # fit_pair (its mark far from the neighbour); fit_pair None = the mark was judged,
            # and B2, which fits plain letters, must not see it (2026-10-01)
            pair = r.get("fit_pair", r["pair"])
            if pair is None or any(c.isalpha() and not c.isascii() for c in pair):
                continue
            if r["style"] == style and not any(c in drop for c in pair):
                cls = "skip" if r.get("verdict") == "skipped-ok" else "extra"
                sh = (italic_delta(pair) - page_correction(r, pair)) if style == "italic" else 0.0
                reads.setdefault(pair, []).append((r["d0920"] - sh, cls, _when(r)))
    return reads


# RECENCY (owner 2026-09-28, on the family bench: *"weight more recent
# measurements much heavier"*). Why: the family bench read ra -15 / na -12 /
# un -14 where his 09-20 bench read +17 / +29 / +14, and an equal-weight mean
# left the model where neither reading is. Each reading weighs
# 0.5 ** (age / HALF_LIFE days), age counted from his NEWEST reading, so a
# pair's judgment follows what he says now (the 09-20 bench, ~8.5 days older
# than the family bench, weighs ~0.003 of it where the pair was read again).
# A pair's weight in the fit is 1 + BOOST * its newest reading's recency, so a
# pair read today pulls the shared bearings and classes 1 + BOOST times as
# hard as one read only on 09-20 -- which still counts: it is most of the data.
# Still training data: the fit ships its prediction, not his number.
# ALBO_B2_RECENCY=0 = the equal-weight mean shipped through round 430.
RECENCY = os.environ.get("ALBO_B2_RECENCY", "1") != "0"
HALF_LIFE = float(os.environ.get("ALBO_B2_HALF_LIFE", "1.0"))
BOOST = float(os.environ.get("ALBO_B2_BOOST", "3.0"))


def combine(reads, skip_w=1.0):
    """Each pair: the weighted MEAN of its readings (skip weight skip_w, all
    others 1; times recency when RECENCY) and its weight in the fit (the
    largest reading weight; 1 + BOOST * newest recency when RECENCY)."""
    tn = max(t for rs in reads.values() for _, _, t in rs)
    J, W = {}, {}
    for p, rs in reads.items():
        base = np.array([skip_w if c == "skip" else 1.0 for _, c, _ in rs])
        rec = np.array([0.5 ** ((tn - t) / HALF_LIFE) for _, _, t in rs]) if RECENCY else np.ones(len(rs))
        w = base * rec
        J[p] = float(np.average([d for d, _, _ in rs], weights=w)) if w.sum() else 0.0
        W[p] = float(base.max()) * ((1.0 + BOOST * rec.max()) if RECENCY else 1.0)
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
