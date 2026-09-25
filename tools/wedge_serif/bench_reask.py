#!/usr/bin/env python3
"""The blind re-ask bench: how repeatable is the owner's own spacing judgment,
and is the fitted model already inside that noise?

WHY THIS FILE EXISTS.  `bench_fit.py` fits his 370 non-g bench judgments to a
mean error of about 8.3 units IN-SAMPLE (11.7 held-out, `bench_fit.py --cv`),
and nobody knows whether that is above or below his own repeatability, because
no bench row had ever been asked twice.  If the model already predicts his next
answer as well as his last answer does, more pair-fitting cannot pay; the next
gain would have to come from a better model or from nowhere.  Owner ruling
2026-09-25: *"Yes, build the re-ask bench"*.  Account and outcomes:
`docs/albo-kerning-noise-floor-2026-09-25.md`.

TWO SUBCOMMANDS.

  select   Chooses ~40 already-answered rows, stratified, and writes
           bench/reask-2026-09-25.html (the page he answers) and
           bench/reask-2026-09-25.key.json (his previous answers, the stratum,
           and the model's held-out prediction for each row).  Deterministic:
           the seed is fixed, so re-running reproduces both files byte for
           byte from the same bench_values.json.  The PAGE carries no previous
           answer anywhere, not even in its source -- the key file does.

  analyze  Reads his new answers and reports, per row, |new - previous|, his
           repeatability, the implied per-judgment noise, the model's error
           on the same rows, and the verdict.  Accepts either the JSON block
           the page's "Copy answers" button produces, or a directory written
           by `ArtifactData list --out_dir` over the page's `reask` collection.

WHY THE PAGE LOOKS LIKE THE OLD ONE.  A retest is only a retest if the
instrument is the same.  The page is the original bench's card, slider
(-60..60 thousandths of an em, zero = what shipped), the "shipped" reset and
the three verdict chips, rendered with the SAME two font files the original
page served (bench/fonts-2026-09-20/, head.modified 2026-09-20 22:23 UTC; every
stored answer is later) and the same per-row GPOS offset (`kr`/`ki`).  So a new
answer and an old one are measured from the same zero.  Two things differ, both
deliberately: rows of both styles are mixed in one shuffled list (each row
names its style), and the card does not show the other style's saved value,
because that would be his old answer.
"""
import argparse, base64, glob, json, math, os, re, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bench_fit  # noqa: E402

BENCH_DIR = os.path.join(HERE, "bench")
TAG = "reask-2026-09-25"
ITEMS = os.path.join(BENCH_DIR, "bench-items-2026-09-20.json")
FONTS = os.path.join(BENCH_DIR, "fonts-2026-09-20")
PAGE = os.path.join(BENCH_DIR, TAG + ".html")
KEY = os.path.join(BENCH_DIR, TAG + ".key.json")
SEED = 20260925

# Per style: the rows the model gets MOST wrong (held-out), then a random draw
# per class.  Outliers are where a retest is most informative -- a big residual
# is either his noise or the model's miss, and the retest says which -- but they
# are reported apart from the typical draw, because they would inflate any
# estimate of his noise taken over the whole set.
N_OUTLIERS = 5
DRAW = {"lower": 9, "cap": 3, "mark": 3}


def load_items():
    return {it["id"]: it for it in json.load(open(ITEMS))["items"]}


def held_out_predictions(J):
    """Mean held-out (shipped-integer) prediction per pair, over bench_fit's
    deterministic CV shuffles -- a prediction from fits that never saw it."""
    cv = bench_fit.cross_validate(J)
    acc = {}
    for p, v in zip(cv["pairs"], cv["pred"]):
        acc.setdefault(p, []).append(v)
    return {p: float(np.mean(v)) for p, v in acc.items()}


def select(db_path=None):
    items = load_items()
    by_pair = {it["pair"].replace(" ", ""): it for it in items.values()}
    db = json.load(open(db_path)) if db_path else {}
    rng = np.random.default_rng(SEED)
    rows, taken = [], set()
    for style in ("roman", "italic"):
        J = bench_fit.judgments(style)
        fit = bench_fit.fit_style(style)
        pred = held_out_predictions(J)
        free = [p for p in sorted(J) if p not in taken]
        resid = sorted(free, key=lambda p: (-abs(J[p] - pred[p]), p))
        chosen = [(p, "outlier") for p in resid[:N_OUTLIERS]]
        rest = [p for p in free if p not in dict(chosen)]
        for cls, n in DRAW.items():
            pool = [p for p in rest if bench_fit.pair_class(p) == cls]
            pick = rng.choice(len(pool), size=min(n, len(pool)), replace=False)
            chosen += [(pool[i], "typical") for i in sorted(pick)]
        for p, stratum in chosen:
            it = by_pair[p]
            prev = db.get(f"{style}_{it['id']}", {})
            if prev and prev.get("delta") != J[p]:
                sys.exit(f"bench_values.json and the db disagree on {style} {p}")
            rows.append(dict(style=style, id=it["id"], pair=p, word=it["word"],
                             cls=bench_fit.pair_class(p), stratum=stratum,
                             previous=J[p], previous_at=prev.get("at"),
                             held_out=round(pred[p], 2),
                             in_sample=fit["predict"](p)))
            taken.add(p)
    order = rng.permutation(len(rows))
    rows = [rows[i] for i in order]

    json.dump({"bench": TAG, "seed": SEED,
               "note": "PREVIOUS ANSWERS -- never show these on the page.",
               "rows": rows}, open(KEY, "w"), indent=1)
    page_items = []
    for r in rows:
        it = items[r["id"]]
        page_items.append(dict(id=it["id"], style=r["style"], word=it["word"],
                               i=it["i"], pair=it["pair"], g=it["g"], n=it["n"],
                               k=it["kr"] if r["style"] == "roman" else it["ki"]))
    write_page(page_items)
    counts = {}
    for r in rows:
        counts[(r["style"], r["stratum"], r["cls"])] = counts.get((r["style"], r["stratum"], r["cls"]), 0) + 1
    print(f"{len(rows)} rows -> {os.path.relpath(PAGE, HERE)} and {os.path.relpath(KEY, HERE)}")
    for k in sorted(counts):
        print(f"  {k[0]:6s} {k[1]:8s} {k[2]:5s} {counts[k]}")


def write_page(page_items):
    fonts = {}
    for name in ("Albo-Regular.ttf", "Albo-Italic.ttf"):
        fonts[name] = base64.b64encode(open(os.path.join(FONTS, name), "rb").read()).decode()
    html = PAGE_TEMPLATE
    html = html.replace("__REGULAR__", fonts["Albo-Regular.ttf"])
    html = html.replace("__ITALIC__", fonts["Albo-Italic.ttf"])
    html = html.replace("__ITEMS__", json.dumps(page_items, separators=(",", ":")))
    html = html.replace("__TAG__", TAG)
    open(PAGE, "w").write(html)


# ---------------------------------------------------------------- analysis

def read_answers(src):
    """{(style, id): {"delta", "verdict", "at"}} from the page's JSON block or
    from an ArtifactData out_dir of the `reask` collection."""
    out = {}
    if os.path.isdir(src):
        for f in glob.glob(os.path.join(src, "**", "*.json"), recursive=True):
            m = re.match(r"(roman|italic)_(.+)$", os.path.basename(f)[:-5])
            if not m:
                continue
            d = json.load(open(f))
            if d.get("touched"):
                out[(m[1], m[2])] = d
        return out
    text = open(src).read()
    blob = json.loads(text[text.index("{"):text.rindex("}") + 1])
    if blob.get("bench") != TAG:
        sys.exit(f"{src} is not an answer set for {TAG}")
    for a in blob["answers"]:
        out[(a["style"], a["id"])] = a
    return out


def analyze(src):
    key = json.load(open(KEY))
    ans = read_answers(src)
    rows = []
    for r in key["rows"]:
        a = ans.get((r["style"], r["id"]))
        if a is None:
            continue
        new = int(a["delta"])
        rows.append(dict(r, new=new, d=new - r["previous"],
                         model_err=abs(r["held_out"] - new)))
    if not rows:
        sys.exit("no answered rows")
    print(f"{len(rows)} of {len(key['rows'])} re-asked rows answered\n")
    print(f"  {'style':6s} {'pair':5s} {'word':14s} {'stratum':8s} {'prev':>5s} {'new':>5s}"
          f" {'|d|':>4s} {'model':>6s} {'|m-new|':>7s}")
    for r in sorted(rows, key=lambda r: (r["stratum"], r["style"], r["pair"])):
        print(f"  {r['style']:6s} {r['pair']:5s} {r['word'][:14]:14s} {r['stratum']:8s}"
              f" {r['previous']:+5d} {r['new']:+5d} {abs(r['d']):4d} {r['held_out']:+6.1f}"
              f" {r['model_err']:7.1f}")

    # Two independent judgments of one quantity, each with noise sd s: their
    # difference has sd s*sqrt(2), and its mean absolute value is 2s/sqrt(pi).
    # So s = mean|d| * sqrt(pi)/2.  The best any model can do against ONE of
    # his judgments is mean |noise| = s*sqrt(2/pi) = mean|d|/sqrt(2).
    def summary(sub, label):
        if not sub:
            return None
        m = float(np.mean([abs(r["d"]) for r in sub]))
        sd_d = float(np.std([r["d"] for r in sub], ddof=1)) if len(sub) > 1 else float("nan")
        s = m * math.sqrt(math.pi) / 2
        mod = float(np.mean([r["model_err"] for r in sub]))
        closer = sum(r["model_err"] < abs(r["d"]) for r in sub)
        tie = sum(r["model_err"] == abs(r["d"]) for r in sub)
        bias = float(np.mean([r["d"] for r in sub]))
        # A 40-row retest is small: say how small, with a fixed-seed bootstrap.
        rng = np.random.default_rng(SEED)
        ad = np.array([abs(r["d"]) for r in sub])
        boots = [float(np.mean(rng.choice(ad, len(ad)))) for _ in range(2000)]
        lo, hi = np.percentile(boots, [2.5, 97.5])
        print(f"\n{label} (n={len(sub)}):")
        print(f"  his repeatability, mean |new - previous|  {m:6.2f} units"
              f"   (95% bootstrap {lo:.2f}..{hi:.2f}; mean drift {bias:+.2f},"
              f" sd of the difference {sd_d:.2f})")
        print(f"  implied noise per judgment, sd            {s:6.2f}"
              f"   (from sd of difference: {sd_d / math.sqrt(2):.2f})")
        print(f"  floor for ANY model against one judgment  {m / math.sqrt(2):6.2f}")
        print(f"  model held-out error vs his NEW answer     {mod:6.2f}"
              f"   (model closer than his previous answer on {closer}/{len(sub)}, {tie} ties)")
        return m

    typ = summary([r for r in rows if r["stratum"] == "typical"], "TYPICAL rows")
    summary([r for r in rows if r["stratum"] == "outlier"], "OUTLIER rows (largest model residuals)")
    summary(rows, "ALL re-asked rows")
    for cls in ("lower", "cap", "mark"):
        summary([r for r in rows if r["cls"] == cls and r["stratum"] == "typical"],
                f"typical, class {cls}")

    # The bench-wide held-out error, recomputed now rather than quoted.
    tot, n = 0.0, 0
    for style in ("roman", "italic"):
        J = bench_fit.judgments(style)
        cv = bench_fit.cross_validate(J)
        tot += float(np.mean(cv["shipped"])) * len(J)
        n += len(J)
    cv_all = tot / n
    rep = typ if typ is not None else float(np.mean([abs(r["d"]) for r in rows]))
    print(f"\nbench-wide held-out error (bench_fit --cv, {n} judgments): {cv_all:.2f}")
    print(f"his repeatability on typical rows:                       {rep:.2f}")
    print(f"noise floor for any model (repeatability / sqrt 2):      {rep / math.sqrt(2):.2f}")
    print()
    if cv_all <= rep:
        print("VERDICT: held-out error <= his repeatability.  The model predicts his next")
        print("answer at least as well as his own previous answer does.  STOP fitting pairs:")
        print("more rows buy nothing he could see again.  Spend the bench on things it has")
        print("never asked (new glyphs, new styles), not on refining the pairs it has.")
    elif cv_all <= 1.25 * rep:
        print("VERDICT: held-out error is within 25% of his repeatability.  Pair-fitting is")
        print("near the end of what it can buy; a better MODEL (class priors, shape features,")
        print("research doc §3b) is the only lever left worth pulling, and only if it closes")
        print("the gap on held-out rows.")
    else:
        print("VERDICT: held-out error is well above his repeatability.  The model, not his")
        print("eye, is the bottleneck: add structure (research doc §3b) before adding rows,")
        print("and score every change on bench_fit --cv, never on the in-sample number.")


PAGE_TEMPLATE = r"""<title>Albo Re-ask Bench</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
  @font-face{font-family:"Albo";src:url("data:font/ttf;base64,__REGULAR__") format("truetype");font-weight:400;font-style:normal;font-display:block}
  @font-face{font-family:"Albo";src:url("data:font/ttf;base64,__ITALIC__") format("truetype");font-weight:400;font-style:italic;font-display:block}
  :root{--paper:#F6F6F4;--ink:#17181C;--soft:#4A4D55;--rule:#D9D9D4;--card:#FFF;
    --accent:#2F5872;--accent-soft:#E7EDF2;--good:#2D6A4A;--good-soft:#E3EFE8;
    --warn:#8A6A1F;--warn-soft:#F4EDDC;
    --sans:"IBM Plex Sans",system-ui,-apple-system,Arial,sans-serif;
    --mono:"IBM Plex Mono",ui-monospace,Menlo,monospace;
    --albo:"Albo",Georgia,"Times New Roman",serif}
  @media (prefers-color-scheme:dark){:root:not([data-theme="light"]){color-scheme:dark;
    --paper:#131418;--ink:#E9E9E5;--soft:#A3A7AF;--rule:#2C2E35;--card:#1B1D22;
    --accent:#8FB6D1;--accent-soft:#1E2A33;--good:#7FC3A0;--good-soft:#17251E;
    --warn:#D9B45E;--warn-soft:#2A2517}}
  :root[data-theme="dark"]{color-scheme:dark;--paper:#131418;--ink:#E9E9E5;--soft:#A3A7AF;--rule:#2C2E35;--card:#1B1D22;
    --accent:#8FB6D1;--accent-soft:#1E2A33;--good:#7FC3A0;--good-soft:#17251E;
    --warn:#D9B45E;--warn-soft:#2A2517}
  *{box-sizing:border-box}
  body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--sans);font-size:16px;line-height:1.5}
  .wrap{max-width:880px;margin:0 auto;padding:0 18px;padding-block:32px 90px;display:flex;flex-direction:column;gap:18px}
  h1{margin:0;font-size:clamp(25px,4.5vw,33px);line-height:1.12;letter-spacing:-.01em;text-wrap:balance}
  .lede{margin:0;color:var(--soft);max-width:62ch}
  .bar{position:sticky;top:env(safe-area-inset-top,0px);z-index:5;background:var(--paper);
       border-bottom:1px solid var(--rule);padding:9px 0;display:flex;gap:9px;flex-wrap:wrap;align-items:center}
  .seg{display:flex;border:1px solid var(--rule);border-radius:5px;overflow:hidden}
  .seg button{font:inherit;font-size:13.5px;padding:6px 11px;background:transparent;color:var(--ink);border:0;cursor:pointer}
  .seg button[aria-pressed="true"]{background:var(--accent);color:#fff}
  .status{font-family:var(--mono);font-size:12px;color:var(--soft);margin-left:auto;text-align:right}
  .card{background:var(--card);border:1px solid var(--rule);border-radius:6px;padding:13px 15px;
        display:flex;flex-direction:column;gap:9px}
  .card.done{border-color:var(--good)}
  .cardhead{display:flex;gap:9px;align-items:baseline;flex-wrap:wrap}
  .pair{font-family:var(--mono);font-size:12px;letter-spacing:.1em;text-transform:uppercase;
        color:var(--accent);background:var(--accent-soft);padding:3px 8px;border-radius:3px}
  .freq{font-family:var(--mono);font-size:11.5px;color:var(--soft)}
  .other{font-family:var(--mono);font-size:11.5px;color:var(--soft);margin-left:auto}
  .spec{font-family:var(--albo);line-height:1.22;overflow-x:auto}
  .spec .big{font-size:clamp(34px,7vw,54px);display:block;white-space:nowrap}
  .spec .run{display:block;color:var(--soft);margin-top:4px;white-space:nowrap}
  .ctl{display:flex;gap:11px;align-items:center;flex-wrap:wrap}
  input[type=range]{flex:1 1 200px;min-width:160px;accent-color:var(--accent)}
  .val{font-family:var(--mono);font-size:12.5px;min-width:7ch;text-align:right;font-variant-numeric:tabular-nums}
  .chips{display:flex;gap:5px;flex-wrap:wrap}
  .chip{font:inherit;font-size:12.5px;padding:4px 10px;border-radius:4px;border:1px solid var(--rule);
        background:transparent;color:var(--ink);cursor:pointer}
  .chip[aria-pressed="true"]{background:var(--good-soft);border-color:var(--good);color:var(--good);font-weight:500}
  .chip.warnish[aria-pressed="true"]{background:var(--warn-soft);border-color:var(--warn);color:var(--warn)}
  .reset{margin-left:auto;font-size:12px;background:none;border:0;color:var(--soft);cursor:pointer;text-decoration:underline;padding:3px}
  .more{font:inherit;font-size:14px;padding:9px 16px;border-radius:5px;border:1px solid var(--rule);
        background:var(--card);color:var(--ink);cursor:pointer}
  footer{border-top:1px solid var(--rule);padding-top:16px;color:var(--soft);font-size:13.5px;display:flex;flex-direction:column;gap:10px}
  textarea{width:100%;min-height:120px;font-family:var(--mono);font-size:11.5px;background:var(--card);color:var(--ink);
           border:1px solid var(--rule);border-radius:5px;padding:8px}
  button:focus-visible,input:focus-visible,textarea:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
  code{font-family:var(--mono);font-size:.9em}
  @media (max-width:520px){.wrap{padding-block:24px 70px}}
</style>
<div class="wrap">
  <header style="display:flex;flex-direction:column;gap:8px">
    <h1>Where should the letters sit?</h1>
    <p class="lede">Forty pairs from your own books, set exactly as on the spacing bench, roman and italic mixed. Zero is what ships; a number you leave is a correction in thousandths of an em. Judge each one fresh.</p>
  </header>
  <div class="bar">
    <div class="seg" id="size"><button data-v="13" aria-pressed="false">13</button><button data-v="17" aria-pressed="true">17</button><button data-v="22" aria-pressed="false">22</button></div>
    <span class="status" id="status">local only</span>
  </div>
  <div id="list" style="display:flex;flex-direction:column;gap:11px"></div>
  <footer>
    <div>Kerning for the opened pair is supplied by the page from that style's own GPOS value, so zero renders what the spacing bench rendered. Every other pair in the word keeps the font's kerning.</div>
    <div style="display:flex;gap:9px;align-items:center;flex-wrap:wrap">
      <button class="more" id="copy">Copy answers</button>
      <span id="copied" class="freq"></span>
    </div>
    <textarea id="export" readonly aria-label="answers as JSON"></textarea>
  </footer>
</div>
<script>
const BENCH = "__TAG__";
const ITEMS = __ITEMS__;
const state = {size:17, v:{}};
const $ = s => document.querySelector(s);
let db = null;
const key = it => it.style + "_" + it.id;
const cell = it => (state.v[key(it)] ||= {d:0, verdict:""});
const isSet = it => { const c = state.v[key(it)]; return !!(c && c.touched); };
const fmt = n => n.toLocaleString();
const LS = "albo-" + BENCH;

function exportJSON(){
  const answers = ITEMS.filter(isSet).map(it => { const c = cell(it);
    return {style:it.style, id:it.id, pair:it.pair.replace(" ",""), delta:c.d, verdict:c.verdict, at:c.at||null}; });
  return JSON.stringify({bench:BENCH, answers}, null, 0);
}
function setStatus(extra){
  const n = ITEMS.filter(isSet).length;
  $("#status").textContent = (extra ? extra + " · " : "") + n + "/" + ITEMS.length + " answered";
  $("#export").value = exportJSON();
}
function card(it){
  const st = it.style, kern = it.k;
  const cur = cell(it);
  const card = document.createElement("div");
  card.className = "card" + (isSet(it) ? " done" : "");
  const head = document.createElement("div"); head.className = "cardhead";
  const pair = document.createElement("span"); pair.className = "pair"; pair.textContent = it.pair;
  const freq = document.createElement("span"); freq.className = "freq";
  freq.textContent = fmt(it.n) + " in your books";
  const oinfo = document.createElement("span"); oinfo.className = "other";
  const label = () => oinfo.textContent = st + "   ·   " + (isSet(it) ? "saved" : "not saved");
  label();
  head.append(pair, freq, oinfo);
  const spec = document.createElement("div"); spec.className = "spec";
  spec.style.fontStyle = st === "italic" ? "italic" : "normal";
  const big = document.createElement("span"); big.className = "big";
  const run = document.createElement("span"); run.className = "run"; run.style.fontSize = state.size + "px";
  for (const host of [big, run]){
    host.appendChild(document.createTextNode(it.word.slice(0, it.i + 1)));
    const tail = document.createElement("span");
    tail.textContent = it.word.slice(it.i + 1);
    tail.style.marginLeft = ((kern + cur.d) / 1000) + "em";
    host.appendChild(tail);
  }
  spec.append(big, run);
  const ctl = document.createElement("div"); ctl.className = "ctl";
  const range = document.createElement("input");
  range.type = "range"; range.min = "-60"; range.max = "60"; range.step = "1"; range.value = cur.d;
  range.id = "r_" + key(it);
  range.setAttribute("aria-label", "spacing for " + it.pair + ", " + st);
  const val = document.createElement("span"); val.className = "val";
  const show = () => val.textContent = (cur.d > 0 ? "+" : "") + cur.d;
  const paint = () => { for (const h of [big, run]) h.lastChild.style.marginLeft = ((kern + cur.d) / 1000) + "em"; };
  const commit = () => { cur.touched = true; cur.at = new Date().toISOString(); card.classList.toggle("done", isSet(it)); label(); setStatus(); save(it); };
  show();
  range.addEventListener("input", () => { cur.d = parseInt(range.value,10); show(); paint(); });
  range.addEventListener("change", commit);
  const reset = document.createElement("button");
  reset.className = "reset"; reset.textContent = "shipped";
  reset.addEventListener("click", () => { cur.d = 0; range.value = 0; show(); paint(); commit(); });
  ctl.append(range, val, reset);
  const chips = document.createElement("div"); chips.className = "chips";
  for (const [k,lab] of [["tight","too tight"],["ok","right"],["loose","too loose"]]){
    const b = document.createElement("button");
    b.className = "chip" + (k === "ok" ? "" : " warnish");
    b.textContent = lab;
    b.setAttribute("aria-pressed", cur.verdict === k ? "true" : "false");
    b.addEventListener("click", () => {
      cur.verdict = cur.verdict === k ? "" : k;
      for (const s of chips.children) s.setAttribute("aria-pressed","false");
      b.setAttribute("aria-pressed", cur.verdict === k ? "true" : "false");
      commit();
    });
    chips.appendChild(b);
  }
  card.append(head, spec, ctl, chips);
  return card;
}
function render(){
  const list = $("#list"); list.innerHTML = "";
  for (const it of ITEMS) list.appendChild(card(it));
  setStatus();
}
function keepLocal(){ try { localStorage.setItem(LS, JSON.stringify(state.v)); } catch(e){} }
let pending = new Set(), timer = null;
function save(it){
  keepLocal();
  if (!db) return;
  pending.add(key(it));
  clearTimeout(timer);
  timer = setTimeout(async () => {
    const keys = [...pending]; pending.clear();
    for (const k of keys){
      const v = state.v[k]; const st = k.split("_")[0];
      try {
        await db.doc("reask/" + k).set({delta:v.d, verdict:v.verdict, touched:true, style:st, bench:BENCH, at:v.at || new Date().toISOString()});
        setStatus("saved");
      } catch(e){ setStatus("not saved (" + ((e&&e.code)||"error") + ")"); }
    }
  }, 350);
}
$("#size").addEventListener("click", e => {
  const b = e.target.closest("button"); if (!b) return;
  state.size = parseInt(b.dataset.v,10);
  for (const x of $("#size").children) x.setAttribute("aria-pressed", String(x === b));
  render();
});
$("#copy").addEventListener("click", async () => {
  const t = $("#export"); t.value = exportJSON();
  try { await navigator.clipboard.writeText(t.value); $("#copied").textContent = "copied"; }
  catch(e){ t.focus(); t.select(); $("#copied").textContent = "selected, copy it by hand"; }
});
try { const s = JSON.parse(localStorage.getItem(LS) || "null"); if (s) state.v = s; } catch(e){}
render();
(async () => {
  db = await (window.claude?.use?.("db") ?? Promise.resolve(null));
  if (!db){ setStatus("local only, use Copy answers"); return; }
  try {
    const snap = await db.collection("reask").get();
    for (const d of snap.docs){
      const b = d.data() || {};
      if (!ITEMS.some(it => key(it) === d.id)) continue;
      state.v[d.id] = {d: b.delta || 0, verdict: b.verdict || "", touched: true, at: b.at};
    }
  } catch(e){}
  render();
})();
</script>
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("select", help="choose the rows; write the page and the key")
    s.add_argument("--db", help="a JSON dump of the bench's `spacing` collection "
                                "({doc_id: doc}); adds each previous answer's timestamp "
                                "and fails if it disagrees with bench_values.json")
    a = sub.add_parser("analyze", help="score his answers against the key")
    a.add_argument("answers", help="the page's copied JSON (a file), or an ArtifactData "
                                   "out_dir of the page's `reask` collection")
    args = ap.parse_args()
    if args.cmd == "select":
        select(args.db)
    else:
        analyze(args.answers)


if __name__ == "__main__":
    main()
