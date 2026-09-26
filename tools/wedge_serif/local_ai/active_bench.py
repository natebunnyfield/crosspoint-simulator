#!/usr/bin/env python3
"""The ACTIVE-LEARNING spacing bench: choose the next rows by what B2 is least
sure of, weighted by how often his books use the pair, and build the live page.

Owner ruling 2026-09-26 on decision 3 of docs/local-ai-spacing-options-
2026-09-26.md: *"Build it"*.

SELECTION (per session, deterministic from the seed):
  * CANDIDATES: every pair in B2's scope (b2_fit.in_scope; the bench pairs plus
    his books' pairs at 200+, or 10+ with a mark) that he has NEVER answered,
    in either bench, in that style.
  * UNCERTAINTY: the spread (sd) of the pair's predicted white across B2 fits
    on 200 bootstrap resamples of his 370 judgments. It is large where the
    glyphs were rarely judged or the pair's shape is unlike anything judged.
  * VISIBILITY: 0 when neither B2's proposed move from the zero font NOR its
    uncertainty reaches one phone kern quantum (1.16 units) -- such a pair
    cannot be seen to change on the phone. Sessions 1-2 had a round-395 zero,
    so the proposed move decided it; from round 397 the zero IS the model, the
    move is ~0 and the uncertainty (sd) decides it.
  * SCORE = sd x count x visibility. The top N go on the page.
  * REPEATS (~10%): pairs he already answered, drawn at random (seeded),
    so every session re-measures his noise and his drift.
  * THE ZERO is the SHIPPED font (ZERO_DIR below; round 395 for sessions 1-2,
    round 397 from session 3). Every row records its white there AND in the 09-20 bench fonts,
    so active_ingest.py can put the answer on the fit's zero.

THE PAGE is build_live.py's live bench (every letter a span placed by the
font's own kern plus his answer; a slider moves the pair everywhere on the
page), storing to the page's `db` capability, collection "active", one
document per row: {delta, verdict, touched, style, pair, bench, session, at}.
`session` is minted when the page opens (a sitting), `bench` names the page.
Without the db it keeps answers in localStorage and offers Copy answers.

    $VENV/bin/python active_bench.py --census bigrams.json --b2 B2_DIR --out DIR [--n 50] [--session s1]
"""
import argparse, base64, collections, json, os, random, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, WS)
import bench_fit  # noqa: E402
import features as FT  # noqa: E402
import b2_fit  # noqa: E402
from b2_fit import white_fn, in_scope  # noqa: E402

BENCH = os.path.join(WS, "bench")
# THE ZERO a new session is answered against: the SHIPPED font. Sessions 1-2
# were round 395 (fonts-2026-09-26); round 396 (B2 shipped) is
# fonts-2026-09-26-r396; session 3 is round 397 (fonts-2026-09-26-r397), session 4 on round 398 (fonts-2026-09-26-r398). Each key file records its own zero and every row's
# white there, so active_ingest.py converts each session from ITS zero.
ZERO_DIR = "fonts-2026-09-26-r399"   # session 5 was built on r398; session 6 on is r399
ZERO = {"roman": os.path.join(BENCH, ZERO_DIR, "Albo-Regular.ttf"),
        "italic": os.path.join(BENCH, ZERO_DIR, "Albo-Italic.ttf")}
B0920 = FT.FONTS
QUANTUM = 1.16
BOOT = 200
PARAGRAPH = ("It is a truth universally acknowledged, that a single man in possession "
             "of a good fortune, must be in want of a wife. The rhythm of the argument "
             "was wrongly named: You and John found every agreement in the software "
             "vocabulary, first things first, back past the true rule because the "
             "community had checked it. Verification took two numbers, and her, "
             "perfect latency, was kinked; the Witch of Kasov said Quiet, it is English.")
ENTITY = {"amp", "nbsp", "quot", "lt", "gt", "apos", "mdash", "ndash", "rsquo", "lsquo", "rdquo", "ldquo", "hellip"}
OK_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'.,;:!?")


def answered():
    """{style: set(pairs)} he has answered on ANY bench so far."""
    out = {s: set(json.load(open(bench_fit.BENCH))["literal"][s]) for s in ("roman", "italic")}
    k = json.load(open(os.path.join(BENCH, "outliers-2026-09-25.key.json")))["rows"]
    for r in k:
        out[r["style"]].add(r["pair"])
    ex = os.path.join(BENCH, "answers", "extra-judgments.json")
    if os.path.exists(ex):
        for r in json.load(open(ex))["rows"]:
            out[r["style"]].add(r["pair"])
    return out


def carriers_for(carriers, p, n=5):
    words = []
    for w, _ in carriers.get(p, []):
        if p[1] not in ".,;:!?'":
            w = w.rstrip(".,;:!?")
        if w.lower() in ENTITY or len(w) < 2 or len(w) > 14 or any(c not in OK_CHARS for c in w) or p not in w or w in words:
            continue
        words.append(w)
        if len(words) == n:
            break
    return words


def select(census, carriers, b2_dir, n, seed, repeat_frac=0.1):
    rng = np.random.default_rng(seed)
    done = answered()
    fonts = {s: FT.Font(p) for s, p in B0920.items()}
    rows = []
    for style in ("roman", "italic"):
        J, W = b2_fit.with_extra(style)          # bench + every ingested answer (skips = 0)
        cand = [p for p, c in census.items() if in_scope(p) and p not in done[style]
                and (c >= b2_fit.CENSUS_MIN or (c >= b2_fit.CENSUS_MIN_MARK and any(ch in b2_fit.MARKS for ch in p)))]
        pairs = sorted(p for p in set(J) | set(cand) if in_scope(p) or p in bench_fit.judgments(style))
        feats = {p: FT.pair_features(fonts[style], p[0], p[1], style == "italic")[0] for p in pairs}
        J = {p: v for p, v in J.items() if p in pairs}
        keys = sorted(J)
        boots = []
        for _ in range(BOOT):
            pick = rng.integers(0, len(keys), len(keys))
            Jb = {}
            for i in pick:                                   # duplicates: average is the same value
                Jb[keys[i]] = J[keys[i]]
            *_, predict, _ = b2_fit.fit(style, Jb, feats, W)
            boots.append([predict(p) for p in cand])
        sd = np.array(boots).std(0)
        wz = white_fn(ZERO[style]); w2 = white_fn(os.path.join(b2_dir, os.path.basename(ZERO[style])))
        w20 = white_fn(B0920[style])
        for p, s in zip(cand, sd):
            move = w2(p[0], p[1]) - wz(p[0], p[1])
            vis = 1.0 if max(abs(move), s) >= QUANTUM else 0.0
            rows.append(dict(style=style, pair=p, n=census[p], sd=float(s), move=int(move), visible=vis,
                             score=float(s * census[p] * vis), white0=int(wz(p[0], p[1])),
                             white0920=int(w20(p[0], p[1])), kind="active"))
    act = [r for r in rows if r["score"] > 0]
    act.sort(key=lambda r: -r["score"])
    n_rep = max(1, round(n * repeat_frac))
    chosen = act[: n - n_rep]
    # repeats: previously answered bench pairs, visible or not, one draw per style alternately
    pool = []
    for style in ("roman", "italic"):
        wz, w20 = white_fn(ZERO[style]), white_fn(B0920[style])
        for p, d in sorted(bench_fit.judgments(style).items()):
            if p in census and census[p] >= 200:
                pool.append(dict(style=style, pair=p, n=census[p], sd=None, move=None, visible=None, score=None,
                                 white0=int(wz(p[0], p[1])), white0920=int(w20(p[0], p[1])), kind="repeat",
                                 previous0920=d))
    reps = [pool[i] for i in rng.choice(len(pool), n_rep, replace=False)]
    out = chosen + reps
    for r in out:
        r["id"] = ("a_" if r["kind"] == "active" else "r_") + r["pair"].encode().hex()
        ws = carriers_for(carriers, r["pair"])
        r["word"] = ws[0] if ws else r["pair"]
        r["extra"] = ws[1:5]
        r["i"] = r["word"].index(r["pair"])
    order = list(range(len(out))); random.Random(seed).shuffle(order)
    return [out[i] for i in order], rows


def kern_map(font, texts):
    import uharfbuzz as hb
    F = hb.Font(hb.Face(hb.Blob.from_file_path(font)))
    def x(t, kern):
        b = hb.Buffer(); b.add_str(t); b.guess_segment_properties()
        hb.shape(F, b, {"kern": kern, "liga": False, "clig": False, "dlig": False})
        return [p.x_advance for p in b.glyph_positions]
    pairs = {t[i:i + 2] for t in texts for i in range(len(t) - 1) if " " not in t[i:i + 2]}
    m = {p: x(p, True)[0] - x(p, False)[0] for p in sorted(pairs)}
    return {p: v for p, v in m.items() if v}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--census", required=True); ap.add_argument("--b2", required=True)
    ap.add_argument("--out", required=True); ap.add_argument("--n", type=int, default=50)
    ap.add_argument("--session", default="s1"); ap.add_argument("--seed", type=int, default=20260926)
    a = ap.parse_args()
    data = json.load(open(a.census))
    census = {p: c for p, c in data["pairs"]}
    carriers = data["carriers"]
    tag = f"active-2026-09-26-{a.session}"
    items, allrows = select(census, carriers, a.b2, a.n, a.seed)
    sds = np.array([r["sd"] for r in allrows])
    vis = sum(r["visible"] for r in allrows)
    summary = dict(candidates=len(allrows), visible=int(vis), sd_min=float(sds.min()), sd_median=float(np.median(sds)),
                   sd_p90=float(np.percentile(sds, 90)), sd_max=float(sds.max()),
                   chosen_sd=[round(r["sd"], 2) for r in items if r["kind"] == "active"])
    key = dict(bench=tag, seed=a.seed, zero="bench/" + ZERO_DIR,
               note="Selection evidence and each row's white at both zeros. The page shows none of it.",
               summary=summary, rows=items)
    json.dump(key, open(os.path.join(BENCH, tag + ".key.json"), "w"), indent=1, ensure_ascii=False)
    texts = {"roman": {PARAGRAPH}, "italic": {PARAGRAPH}}
    for r in items:
        texts[r["style"]].update([r["word"]] + r["extra"])
    kerns = {s: kern_map(ZERO[s], t) for s, t in texts.items()}
    page_items = [dict(id=r["id"], style=r["style"], pair=r["pair"][0] + " " + r["pair"][1], word=r["word"],
                       i=r["i"], n=r["n"], extra=r["extra"]) for r in items]
    fonts64 = {s: base64.b64encode(open(f, "rb").read()).decode() for s, f in ZERO.items()}
    page = (open(os.path.join(HERE, "active_bench.html")).read()
            .replace("__BENCH__", tag).replace("__ITEMS__", json.dumps(page_items))
            .replace("__KERNS__", json.dumps(kerns)).replace("__PARA__", json.dumps(PARAGRAPH))
            .replace("__ROMAN__", fonts64["roman"]).replace("__ITALIC__", fonts64["italic"]))
    os.makedirs(a.out, exist_ok=True)
    open(os.path.join(a.out, "index.html"), "w").write(page)
    act = [r for r in items if r["kind"] == "active"]
    print(f"{tag}: {len(items)} rows ({len(act)} active, {len(items) - len(act)} repeats); "
          f"roman {sum(r['style'] == 'roman' for r in items)}, italic {sum(r['style'] == 'italic' for r in items)}")
    print(f"candidates {summary['candidates']}, visible {summary['visible']}; bootstrap sd over candidates: "
          f"min {summary['sd_min']:.2f}, median {summary['sd_median']:.2f}, p90 {summary['sd_p90']:.2f}, max {summary['sd_max']:.2f}")
    print(f"chosen active rows' sd: {min(summary['chosen_sd']):.2f}..{max(summary['chosen_sd']):.2f} "
          f"(median {np.median(summary['chosen_sd']):.2f})")
    for r in items:
        print(f"  {r['kind']:6s} {r['style']:6s} {r['pair']:3s} n={r['n']:6d} sd={r['sd'] if r['sd'] is None else round(r['sd'], 1)} "
              f"move={r['move']} word={r['word']}")
    print("wrote", os.path.join(a.out, "index.html"), "and", tag + ".key.json")


if __name__ == "__main__":
    main()
