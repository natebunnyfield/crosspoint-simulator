#!/usr/bin/env python3
"""The outlier bench: the pairs most likely to be off, ranked, for the owner's eye,
and his answers turned into explicit kerns.

Owner 2026-09-25, after round 389: *"... then give me a page for more combos
that are outliers."*  Account: docs/albo-round-389-2026-09-25.md.

THREE SUBCOMMANDS.

  evidence BUILT_DIR   Measures every candidate pair in both styles and writes
                       bench/outliers-2026-09-25.evidence.json. Slow (renders the
                       reference faces); run once per build.
  select               Ranks the evidence, writes the page
                       (bench/outliers-2026-09-25.html) and its key
                       (bench/outliers-2026-09-25.key.json, evidence per row --
                       nothing of it is shown on the page).
  kerns ANSWERS --built DIR
                       Turns his answers into EXPLICIT KERNS, not a refit (pair
                       fitting stopped on 2026-09-25, docs/albo-kerning-noise-
                       floor-2026-09-25.md). For each answered pair:
                           target  = white in the page's fonts + his delta
                           add     = target - white in DIR's font
                       and prints a kern.py block in round 388/389's form
                       (`PAIRS[p] = _shipped(*p) + add`). Relative to the page's
                       fonts, not to "current + delta", so a glyph that moves
                       between the page and the kern round is not double-counted
                       -- which is exactly the fault round 388 found.
                       ANSWERS is the page's "Copy answers" JSON (a file) or an
                       ArtifactData out_dir of its `outliers` collection.

THE ZERO. The page embeds bench/fonts-2026-09-25/ (the round-389 build, commit
49deaff) and, like the re-ask page, splits each word after the judged pair's
left letter and puts the pair's own GPOS kern back as a margin, so zero renders
exactly what round 389 ships and a delta is a change to the pair's white in
font units (both fonts are 1000 upm).

HOW A PAIR IS RANKED.  score = E x log10(n), where n is the pair's count in his
books (pair_census.py) and E is how far off the pair looks, in units, from up to
four signed estimates (+ = looser than it should be):
  r     his own bench residual: white now - (white in the 09-20 bench font +
        his delta, the re-ask mean where there is one). Weight 2 -- it is his eye.
  d4    Measure 4 (cmp_space_2d, 2-D closest approach) as a PAIR INTERACTION:
        g(ab) - med_x g(ax) - med_x g(xb) + med_xy g(xy), x over a neutral
        lowercase set, Albo minus the references' median of the same number.
        What the pair does beyond its two letters' own sides.
  d5    the same on Measure 5 (cmp_word_white, clamp 1.5 counters -- at 1.0 the
        roman saturates: every pair read 134-137). Letters only.
  m     for an UNJUDGED pair that carries an explicit kern (kern.PAIRS) and
        whose ink moved or was redrawn since the 09-20 fonts (raster IoU at the
        pen origin < 0.97 -- a bearing change moves the ink too, and that is
        the point): how far its white moved since 09-20.
        A kern set against the old glyph and left on the new one pays twice.
E = |weighted mean| x (weight share agreeing with its sign). Estimates that
disagree cancel, and a pair supported by one measure alone scores at most half.
Excluded: pairs set in rounds 388/389, the roman's ligated pairs, and anything
under the count floors below.
"""
import argparse, glob, json, math, os, re, subprocess, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "instruments"))
import bench_reask  # noqa: E402  (the page template)

BENCH_DIR = os.path.join(HERE, "bench")
TAG = "outliers-2026-09-25"
FONTS = os.path.join(BENCH_DIR, "fonts-2026-09-25")
FONTS_0920 = os.path.join(BENCH_DIR, "fonts-2026-09-20")
EVID = os.path.join(BENCH_DIR, TAG + ".evidence.json")
PAGE = os.path.join(BENCH_DIR, TAG + ".html")
KEY = os.path.join(BENCH_DIR, TAG + ".key.json")
FILE = {"roman": "Albo-Regular.ttf", "italic": "Albo-Italic.ttf"}
REFSET = {"roman": "roman", "italic": "italic"}
NEU = "noeuimhac"
MARKS = set("'.,:;\"-!?")
# Count floors (22-book census, 2026-09-25): a pair seen this rarely is not
# worth a row of his time whatever it measures.
MIN_N = {"lower": 400, "cap": 120, "mark": 400}
DONE = {"roman": {"or", "rd", "'s", "'t"},
        "italic": {"or", "es", "Pa", "Po", "Pr", "Wa", "Wh", "Wi", "Am", "An", "Av",
                   "Fi", "Fo", "Ye", "Yo"}}
LIGATED = {"roman": {"fi", "fl", "ff"}, "italic": set()}
WORD = {"roman": ["rh", "hy", "yt", "th", "hm"], "italic": ["rh", "hy", "yt", "th", "hm"]}
N_RANKED = 40


def pclass(p):
    if any(c in MARKS for c in p): return "mark"
    if p[0].isupper(): return "cap"
    return "lower"


# ---------------------------------------------------------------- evidence

def census():
    from pair_census import harvest, pairs_from
    words, books = harvest()
    pair, carrier = pairs_from(words)
    return pair, carrier, len(books)


def interaction_table(face_gap, pairs):
    cache = {}
    def g(a, b):
        if (a, b) not in cache: cache[(a, b)] = face_gap(a, b)
        return cache[(a, b)]
    C = np.median([v for x in NEU for y in NEU if (v := g(x, y)) is not None])
    medA, medB, out = {}, {}, {}
    for p in pairs:
        a, b = p[0], p[1]
        if a not in medA:
            v = [w for x in NEU if (w := g(a, x)) is not None]; medA[a] = np.median(v) if v else None
        if b not in medB:
            v = [w for x in NEU if (w := g(x, b)) is not None]; medB[b] = np.median(v) if v else None
        ab = g(a, b)
        out[p] = None if (ab is None or medA[a] is None or medB[b] is None) else float(ab - medA[a] - medB[b] + C)
    return out


def glyph_changes(built, style):
    """Per character: did its ink change between the 09-20 bench font and `built`?
    (IoU of the two rasters at the pen origin, and the two bearings' moves.)"""
    from PIL import Image, ImageDraw, ImageFont
    from fontTools.ttLib import TTFont
    out = {}
    fa = ImageFont.truetype(os.path.join(FONTS_0920, FILE[style]), 200)
    fb = ImageFont.truetype(os.path.join(built, FILE[style]), 200)
    ca = TTFont(os.path.join(FONTS_0920, FILE[style])).getBestCmap()
    for ch in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'.,:;\"-!?":
        if ord(ch) not in ca: continue
        ims = []
        for f in (fa, fb):
            im = Image.new("L", (500, 500), 0)
            ImageDraw.Draw(im).text((150, 350), ch, font=f, fill=255, anchor="ls")
            ims.append(np.asarray(im) > 127)
        u = (ims[0] | ims[1]).sum(); i = (ims[0] & ims[1]).sum()
        out[ch] = round(float(i / u), 3) if u else 1.0
    return out


def evidence(built):
    from r389_bench_residuals import whites, residuals
    import refsets
    from cmp_space_2d import Face as F4
    from cmp_word_white import Face as F5
    pair, carrier, nbooks = census()
    R = residuals(built)
    items = {it["pair"].replace(" ", ""): it for it in
             json.load(open(os.path.join(BENCH_DIR, "bench-items-2026-09-20.json")))["items"]}
    out = {"built": built, "books": nbooks, "styles": {}}
    for style in ("roman", "italic"):
        path = os.path.join(built, FILE[style])
        pool = []
        for (a, b), n in pair.items():
            p = a + b
            if not (a.isalpha() or a in MARKS) or not (b.isalpha() or b in MARKS): continue
            if n < MIN_N[pclass(p)] or (a.isupper() and b.isupper()): continue
            if p in DONE[style] or p in LIGATED[style]: continue
            pool.append(p)
        for p in WORD[style]:
            if p not in pool: pool.append(p)
        w_now = whites(path, pool); w_old = whites(os.path.join(FONTS_0920, FILE[style]), pool)
        pool = [p for p in pool if p in w_now]
        faces4 = [F4(path)] + [F4(p, index=i) for _, p, i in refsets.entries(REFSET[style])]
        faces5 = [F5(path, clamp=1.5)]
        for _, p, i in refsets.entries(REFSET[style]):
            try: faces5.append(F5(p, index=i, clamp=1.5))
            except Exception: pass
        I4 = [interaction_table(f.gap, pool) for f in faces4]
        let = [p for p in pool if pclass(p) != "mark"]
        I5 = [interaction_table(f.white, let) for f in faces5]
        explicit = explicit_pairs(style)
        gch = glyph_changes(built, style)
        rows = {}
        for p in pool:
            def d(tabs):
                me = tabs[0].get(p); rv = [t[p] for t in tabs[1:] if t.get(p) is not None]
                return round((me - float(np.median(rv))) * 1000, 1) if (me is not None and rv) else None
            res = R[style].get(p)
            names = [bench_reask_name(c) for c in p]
            rows[p] = dict(
                n=pair[(p[0], p[1])], cls=pclass(p),
                words=carrier[(p[0], p[1])].most_common(8),
                bench_item=items.get(p, {}).get("id"),
                white=w_now[p][3], kern=w_now[p][1], white0920=w_old.get(p, [None] * 4)[3],
                r=round(res["resid"], 1) if res else None,
                his=res["delta_used"] if res else None,
                d4=d(I4), d5=d(I5) if pclass(p) != "mark" else None,
                explicit=tuple(names) in explicit,
                iou=[gch.get(p[0]), gch.get(p[1])])
        out["styles"][style] = rows
        print(f"{style}: {len(rows)} candidate pairs measured", file=sys.stderr)
    json.dump(out, open(EVID, "w"), indent=1)
    print(f"-> {os.path.relpath(EVID, HERE)}")


AGL = {"'": "quotesingle", '"': "quotedbl", ".": "period", ",": "comma", ":": "colon",
       ";": "semicolon", "-": "hyphen", "!": "exclam", "?": "question"}
def bench_reask_name(c): return c if c.isalpha() else AGL.get(c, c)


def explicit_pairs(style):
    """The pair-specific kerns (kern.PAIRS) the shipping build carries, by
    importing kern.py under that style's shipping environment."""
    env = dict(os.environ, FJORD_STEM="66.9", PYTHON_GIL="0")
    if style == "roman": env.update(FJORD_CONTRAST="0.892")
    else: env.update(ALBO_ITALIC="aldine", FJORD_CONTRAST="0.80", FJORD_WIDTH="95", FJORD_SLANT="13")
    out = subprocess.run([sys.executable, "-c",
                          "import json\nfrom outlines import kern\nprint(json.dumps([[l,r] for (l,r) in kern.PAIRS]))"],
                         cwd=HERE, env=env, capture_output=True, text=True, check=True).stdout
    return {tuple(x) for x in json.loads(out)}


# ---------------------------------------------------------------- ranking

def score(row):
    est = []
    if row["r"] is not None: est.append((row["r"], 2.0, "r"))
    if row["d4"] is not None: est.append((row["d4"], 1.0, "d4"))
    if row["d5"] is not None: est.append((row["d5"], 1.0, "d5"))
    changed = min(x for x in row["iou"] if x is not None) < 0.97 if any(row["iou"]) else False
    if row["r"] is None and row["explicit"] and changed and row["white0920"] is not None:
        est.append((row["white"] - row["white0920"], 1.0, "m"))
    if not est: return 0.0, 0.0, est
    wsum = sum(w for _, w, _ in est)
    mean = sum(v * w for v, w, _ in est) / wsum
    agree = sum(w for v, w, _ in est if v * mean > 0) / wsum
    E = abs(mean) * agree * (0.5 if len(est) == 1 else 1.0)   # one reading alone: half weight
    return E * math.log10(max(row["n"], 10)), mean, est


def pick_word(row, pair):
    """A real word carrying the pair: the bench's own row where there is one,
    else his books' commonest carrier that is plain enough to set."""
    for w, _ in row["words"]:
        w2 = w.replace("’", "'")
        i = w2.find(pair)
        if i < 0: continue
        if len(w2) > 14 or not re.fullmatch(r"[A-Za-z'.,;:!?\"-]+", w2): continue
        return w2, i
    return None, None


def select():
    ev = json.load(open(EVID))
    items = {it["id"]: it for it in
             json.load(open(os.path.join(BENCH_DIR, "bench-items-2026-09-20.json")))["items"]}
    ranked = []
    for style, rows in ev["styles"].items():
        for p, row in rows.items():
            s, mean, est = score(row)
            ranked.append((s, style, p, mean, est, row))
    ranked.sort(key=lambda t: (-t[0], t[1], t[2]))
    chosen, seen = [], set()
    for s, style, p, mean, est, row in ranked:
        if len([c for c in chosen if c["stratum"] == "ranked"]) >= N_RANKED: break
        if s <= 0: break
        chosen.append(dict(stratum="ranked", rank=len(chosen) + 1, style=style, pair=p, score=round(s, 2),
                           E_signed=round(mean, 1), estimates=[[k, v, w] for v, w, k in est], **row))
        seen.add((style, p))
    for style, ps in WORD.items():
        for p in ps:
            if (style, p) in seen: continue
            row = ev["styles"][style][p]; s, mean, est = score(row)
            chosen.append(dict(stratum="word", rank=None, style=style, pair=p, score=round(s, 2),
                               E_signed=round(mean, 1), estimates=[[k, v, w] for v, w, k in est], **row))
    page_items = []
    for c in chosen:
        if c["stratum"] == "word":             # he named the word: judge it there
            word, i = "rhythm", "rhythm".index(c["pair"])
        elif c["bench_item"]:
            it = items[c["bench_item"]]; word, i = it["word"], it["i"]
        else:
            word, i = pick_word(c, c["pair"])
        if word is None:
            print(f"  no settable word for {c['style']} {c['pair']}", file=sys.stderr); continue
        c["word"], c["i"] = word, i
        c["id"] = "o_" + c["pair"].encode().hex()
        page_items.append((c["stratum"], dict(id=c["id"], style=c["style"], word=word, i=i,
                               pair=c["pair"][0] + " " + c["pair"][1],
                               g=c["cls"], n=c["n"], k=c["kern"])))
    # The page's order: the three words' own pairs first (he asked about those),
    # then the ranked rows, strongest first. Nothing ranks visibly on the card.
    order = [x for st, x in page_items if st == "word"] + [x for st, x in page_items if st == "ranked"]
    json.dump({"bench": TAG, "fonts": os.path.relpath(FONTS, HERE), "books": ev["books"],
               "note": "Evidence per row. Never shown on the page.",
               "rows": chosen}, open(KEY, "w"), indent=1)
    write_page(order, sum(1 for st, _ in page_items if st == "word"))
    print(f"{len(order)} rows ({sum(c['stratum']=='ranked' for c in chosen)} ranked, "
          f"{sum(c['stratum']=='word' for c in chosen)} from the three words) -> {os.path.relpath(PAGE, HERE)}")
    for c in chosen:
        e = " ".join(f"{k}{v:+.0f}" for k, v, _ in c["estimates"])
        print(f"  {c['stratum']:6} {c['style']:6} {c['pair']:3} n={c['n']:6d} score {c['score']:5.1f}"
              f"  E {c['E_signed']:+6.1f}  [{e}]  {c.get('word')}")


def write_page(page_items, n_word):
    html = bench_reask.PAGE_TEMPLATE
    swaps = [
        ("<title>Albo Re-ask Bench</title>", "<title>Albo Outlier Bench</title>"),
        ("Forty pairs from your own books, set exactly as on the spacing bench, roman and italic mixed. "
         "Zero is what ships; a number you leave is a correction in thousandths of an em. Judge each one fresh.",
         f"{len(page_items)} pairs from your own books that measure as possibly off, set exactly as on the spacing "
         f"bench, roman and italic mixed. The first {n_word} are the rhythm pairs round 389 left alone. Zero is what ships "
         "after round 389; a number you leave is a correction in thousandths of an em."),
        ('db.collection("reask")', 'db.collection("outliers")'),
        ('db.doc("reask/" + k)', 'db.doc("outliers/" + k)'),
    ]
    for a, b in swaps:
        assert a in html, a[:40]
        html = html.replace(a, b)
    fonts = {n: __import__("base64").b64encode(open(os.path.join(FONTS, n), "rb").read()).decode()
             for n in FILE.values()}
    html = html.replace("__REGULAR__", fonts["Albo-Regular.ttf"]).replace("__ITALIC__", fonts["Albo-Italic.ttf"])
    html = html.replace("__ITEMS__", json.dumps(page_items, separators=(",", ":"))).replace("__TAG__", TAG)
    open(PAGE, "w").write(html)


# ---------------------------------------------------------------- answers -> kerns

def read_answers(src):
    out = {}
    if os.path.isdir(src):
        for f in glob.glob(os.path.join(src, "**", "*.json"), recursive=True):
            m = re.match(r"(roman|italic)_(.+)$", os.path.basename(f)[:-5])
            if not m: continue
            d = json.load(open(f))
            if d.get("touched"): out[(m[1], m[2])] = d
        return out
    text = open(src).read()
    blob = json.loads(text[text.index("{"):text.rindex("}") + 1])
    if blob.get("bench") != TAG: sys.exit(f"{src} is not an answer set for {TAG}")
    for a in blob["answers"]: out[(a["style"], a["id"])] = a
    return out


def kerns(src, built):
    from r389_bench_residuals import whites
    key = json.load(open(KEY)); ans = read_answers(src)
    blocks = {"roman": [], "italic": []}
    print(f"  {'style':6} {'pair':4} {'his':>4} {'page white':>10} {'target':>7} {'built':>6} {'add':>5}")
    for r in key["rows"]:
        a = ans.get((r["style"], r.get("id")))
        if a is None: continue
        d = int(a["delta"])
        if d == 0:
            print(f"  {r['style']:6} {r['pair']:4} {d:+4d}   (shipped is right: no kern)"); continue
        page = whites(os.path.join(FONTS, FILE[r["style"]]), [r["pair"]])[r["pair"]][3]
        now = whites(os.path.join(built, FILE[r["style"]]), [r["pair"]])[r["pair"]][3]
        add = page + d - now
        print(f"  {r['style']:6} {r['pair']:4} {d:+4d} {page:10d} {page + d:7d} {now:6d} {add:+5d}")
        if add: blocks[r["style"]].append(((bench_reask_name(r["pair"][0]), bench_reask_name(r["pair"][1])), add))
    print("\n# ---- paste into outlines/kern.py, above _apply_bench() ----")
    print("if _ALD is not None and _ALD.ON:")
    print("    for _p, _d in (" + ", ".join(f"({p!r}, {v})" for p, v in blocks["italic"]) + ",):" if blocks["italic"] else "    for _p, _d in ():")
    print("        PAIRS[_p] = _shipped(*_p) + _d")
    print("else:")
    print("    for _p, _d in (" + ", ".join(f"({p!r}, {v})" for p, v in blocks["roman"]) + ",):" if blocks["roman"] else "    for _p, _d in ():")
    print("        PAIRS[_p] = _shipped(*_p) + _d")
    print("# An apostrophe row was judged on U+0027; add quoteright too (round 388 precedent).")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("evidence"); e.add_argument("built")
    sub.add_parser("select")
    k = sub.add_parser("kerns"); k.add_argument("answers"); k.add_argument("--built", required=True)
    a = ap.parse_args()
    if a.cmd == "evidence": evidence(a.built)
    elif a.cmd == "select": select()
    else: kerns(a.answers, a.built)


if __name__ == "__main__":
    main()
