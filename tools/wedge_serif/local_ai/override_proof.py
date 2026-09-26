#!/usr/bin/env python3
"""Proof page for the override arm: round 398 over ALBO_SPACING_OVERRIDE=touched.

    $VENV/bin/python override_proof.py R398_DIR OVR_DIR moved.json OUT_DIR

(1) the pairs where the arm differs most from round 398 (|dwhite| x count in
his books), each in its commonest word at 108 px native, round 398 above and
the override below, labelled with his answer and the model's white;
(2) two paragraphs + long words, roman and italic, 27 px x2 nearest and 54 px
native, with the gray/blue/red difference view; (3) the numbers.
Rendered as the reader renders (b2_proof.Setter).
"""
import html, json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from b2_proof import Setter, to_png, diff_png, label, PARA, LONG, FILES, WIDTH54  # noqa: E402
import override  # noqa: E402

N_PAIRS = 12


def pair_strip(r398, ovr, rows, style, out):
    sA, sB = Setter(r398, 108, style == "roman"), Setter(ovr, 108, style == "roman")
    T = override.touched(style)
    cells = []
    for r in rows:
        a, b = sA.word(r["word"]), sB.word(r["word"])
        wd = max(a.shape[1], b.shape[1], 620)
        pad = lambda m: np.pad(m, ((0, 0), (0, wd - m.shape[1])))
        n = len(T.get(r["pair"], []))
        cells.append(np.vstack([
            label(f"{r['pair']}  ({r['word']})   {r['n']:,} in his books   his readings: {n}", wd),
            label(f"round 398 (model): white {r['before']}", wd, 22), pad(a),
            label(f"override (his answer): white {r['after']}   ({r['d']:+d})", wd, 22), pad(b),
            np.zeros((30, wd), np.uint8)]))
    W = max(c.shape[1] for c in cells)
    img = np.vstack([np.pad(c, ((0, 0), (0, W - c.shape[1]))) for c in cells])
    return to_png(img, os.path.join(out, f"pairs-{style}.png"))


def main():
    r398, ovr, moved_json, out = sys.argv[1:5]
    mc = json.load(open(sys.argv[5])) if len(sys.argv) > 5 else None     # the consistent arm's moves
    os.makedirs(out, exist_ok=True)
    moved = json.load(open(moved_json))
    check = json.load(open(os.path.join(HERE, "override-check-2026-09-26.json")))
    figs = {}
    for style, fn in FILES.items():
        A_, B_ = os.path.join(r398, fn), os.path.join(ovr, fn)
        liga = style == "roman"
        f = {}
        for px, width, scale in ((27, WIDTH54 // 2, 2), (54, WIDTH54, 1)):
            sa = Setter(A_, px, liga)
            A = sa.block(PARA + [LONG], width)
            B = Setter(B_, px, liga).block(PARA + [LONG], width + px * 2, rows=sa.rows)
            f[px] = (to_png(A, os.path.join(out, f"{style}-{px}-r398.png"), scale),
                     to_png(B, os.path.join(out, f"{style}-{px}-override.png"), scale))
            if px == 54:
                f["diff"] = diff_png(A, B, os.path.join(out, f"{style}-54-diff.png"))
        rows = [r for r in moved["all"] if r["style"] == style][:N_PAIRS]
        f["pairs"] = pair_strip(A_, B_, rows, style, out)
        figs[style] = f
    s = moved["summary"]
    ef = np.mean([r["e_first"] for r in check]); em = np.mean([r["e_model"] for r in check])
    nf = sum(r["e_first"] < r["e_model"] for r in check)
    by = {}
    for r in check:
        k = "re-ask" if r["src"] == "reask" else ("outlier bench" if r["src"].startswith("outliers") else "active repeat")
        by.setdefault(k, []).append(r)
    byrows = "".join(f"<tr><td>{k}</td><td>{len(v)}</td><td>{np.mean([r['e_first'] for r in v]):.2f}</td>"
                     f"<td>{np.mean([r['e_model'] for r in v]):.2f}</td></tr>" for k, v in sorted(by.items()))
    # his repeats, per session, on the fit's zero (tracking removed) and as the page showed them
    ex = json.load(open(os.path.join(os.path.dirname(HERE), "bench", "answers", "extra-judgments.json")))["rows"]
    reprows = "<tr><td>re-ask (09-25), 30 typical rows</td><td>30</td><td>10.83</td><td>+5.43</td><td>(no tracking on that page)</td></tr>"
    for b in sorted({x["bench"] for x in ex if x["kind"] == "repeat"}):
        v = [x for x in ex if x["bench"] == b and x["kind"] == "repeat"]
        d = np.array([x["d0920"] - x["previous0920"] for x in v]); du = d + np.array([x.get("track_removed", 0) for x in v])
        nt = sum(1 for x in v if x.get("verdict") != "skipped-ok")
        reprows += (f"<tr><td>active {b.rsplit('-', 1)[-1]} ({nt} touched, {len(v) - nt} skipped)</td><td>{len(v)}</td>"
                    f"<td>{np.abs(d).mean():.2f}</td><td>{d.mean():+.2f}</td><td>{np.abs(du).mean():.2f} / {du.mean():+.2f}</td></tr>")
    mid = ""
    if mc:
        cs = mc["summary"]
        mid = (f"<tr><td>middle arm (answered 2+ times, agreeing within 11): pairs that change</td>"
               f"<td>{cs['roman']['moved']} (max {cs['roman']['maxabs']})</td><td>{cs['italic']['moved']} (max {cs['italic']['maxabs']})</td></tr>")
    sec = ""
    for style in ("roman", "italic"):
        f = figs[style]; t = style.capitalize()
        sec += f"""
<h2>{t}</h2>
<p class="cap">The {N_PAIRS} {t.lower()} pairs the override moves most (|&Delta;white| &times; how often his books use them), each in its commonest word at 108 px, native. Upper: round 398 (the model). Lower: his answer.</p>
<div class="strip"><img src="{f['pairs']}" alt="{t} most-changed pairs"></div>
<p class="cap">27 px, enlarged 2&times; with nearest-neighbor. Top: round 398. Bottom: override. Same line breaks.</p>
<div class="strip"><img src="{f[27][0]}" alt="{t} round 398 at 27 px"></div>
<div class="strip"><img src="{f[27][1]}" alt="{t} override at 27 px"></div>
<p class="cap">54 px, native pixels. Top: round 398. Bottom: override.</p>
<div class="strip"><img src="{f[54][0]}" alt="{t} round 398 at 54 px"></div>
<div class="strip"><img src="{f[54][1]}" alt="{t} override at 54 px"></div>
<p class="cap">Difference at 54 px: <span class="k g">gray</span> both, <span class="k b">blue</span> round 398 only, <span class="k r">red</span> override only.</p>
<div class="strip"><img src="{f['diff']}" alt="{t} difference"></div>
"""
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Your Answers, Exactly</title>
<style>
:root {{ --bg:#fbfbf9; --fg:#1d1d1b; --mut:#6b6b66; --line:#dcdcd6; --panel:#ffffff; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ --bg:#161614; --fg:#e8e8e3; --mut:#a3a39c; --line:#3a3a36; }} }}
:root[data-theme="dark"] {{ --bg:#161614; --fg:#e8e8e3; --mut:#a3a39c; --line:#3a3a36; }}
body {{ background:var(--bg); color:var(--fg); font:16px/1.5 -apple-system, system-ui, sans-serif; margin:0; padding:16px; }}
main {{ max-width:1200px; margin:0 auto; }}
.cap {{ color:var(--mut); font-size:14px; margin:18px 0 6px; }}
.strip {{ display:block; overflow-x:auto; background:var(--panel); border:1px solid var(--line); margin:4px 0; }}
.strip img {{ display:block; image-rendering:pixelated; }}
table {{ border-collapse:collapse; font-size:14px; display:block; overflow-x:auto; }}
td, th {{ border-bottom:1px solid var(--line); padding:3px 10px; text-align:left; }}
.k {{ padding:0 4px; border-radius:3px; color:#fff; }} .g {{ background:#737373; }} .b {{ background:#0073ff; }} .r {{ background:#ff2626; }}
</style></head><body><main>
<h1>Your Answers, Exactly</h1>
<p>Round 398 as shipped (the model) over the override arm (<code>ALBO_SPACING_OVERRIDE=touched</code>): every pair you have
moved a slider on ships at exactly your number (the mean of your readings, with tracking c on top as always), and the model
sets everything else. Rendered as the reader renders.</p>
<h2>The numbers</h2>
<table>
<tr><th></th><th>roman</th><th>italic</th></tr>
<tr><td>pairs that change</td><td>{s['roman']['moved']} ({s['roman']['moved4']} by 4+ units)</td><td>{s['italic']['moved']} ({s['italic']['moved4']} by 4+)</td></tr>
<tr><td>mean |&Delta;white| over his books (weighted)</td><td>{s['roman']['wabs']:.2f}</td><td>{s['italic']['wabs']:.2f}</td></tr>
<tr><td>net &Delta;white (weighted)</td><td>{s['roman']['wmean']:+.2f}</td><td>{s['italic']['wmean']:+.2f}</td></tr>
<tr><td>largest |&Delta;white|</td><td>{s['roman']['maxabs']}</td><td>{s['italic']['maxabs']}</td></tr>
{mid}
</table>
<p class="cap">Units are thousandths of an em. One kern step on the phone is 1.16.</p>
<h2>Which predicts your next answer better?</h2>
<p>For the {len(check)} pairs you have answered twice: your first answer against your second, and the model (fitted
<em>with</em> your first answer, without your second) against your second. Mean |error|, units.</p>
<table><tr><th>second answer from</th><th>n</th><th>your first answer</th><th>the model</th></tr>{byrows}
<tr><td><b>all</b></td><td>{len(check)}</td><td><b>{ef:.2f}</b></td><td><b>{em:.2f}</b></td></tr></table>
<p class="cap">Your first answer was the closer on {nf} of {len(check)}; the model on {len(check) - nf}.</p>
<h2>Your repeatability, session by session</h2>
<p>Each session re-asks five pairs you had answered on the first bench. A skip counts as 0, so a skipped repeat is compared too.
The last column is the same thing as the page showed it, before removing tracking c, which the pages from round 395 on carried
and the fit must not.</p>
<table><tr><th>session</th><th>n</th><th>mean |new &minus; previous|</th><th>drift</th><th>as displayed: |&Delta;| / drift</th></tr>{reprows}</table>
<p class="cap">Across the four sessions the mean is about 10.7, the same as the re-ask's 10.83: no trend.</p>
{sec}
</main></body></html>"""
    open(os.path.join(out, "index.html"), "w").write(page)
    print("wrote", out)


if __name__ == "__main__":
    main()
