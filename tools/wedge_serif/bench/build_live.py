#!/usr/bin/env python3
"""Build the LIVE outlier bench: every answer re-sets every text at once.

Owner 2026-09-25, on the outlier bench: *"change bench to affect other examples
dynamically as i go, not one pair at a time but all connected live as is
best."* The first page moved only the opened pair inside its own card. This
one sets EVERY letter of EVERY text on the page itself: each letter is a span
placed at the font's own kern for the pair it closes (read from the font with
HarfBuzz, below) plus his current answer for that pair. So a slider moved on
`hy` re-sets `hy` in its card, in the other cards' words, in the extra words
under each card, and in a reading paragraph for each style -- live, as he
drags. Nothing else in the fonts' behavior is simulated: ligatures are OFF in
the page (a span boundary breaks them), which the footer says.

Carries his answers over: the same database collection ("outliers") and the
same keys (style + "_" + id) as outliers-2026-09-25.html.

Run:  PYTHON_GIL=0 python3 bench/build_live.py   (from tools/wedge_serif)
"""
import base64, collections, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import pair_census  # noqa: E402

FONTS = {"roman": os.path.join(HERE, "fonts-2026-09-25", "Albo-Regular.ttf"),
         "italic": os.path.join(HERE, "fonts-2026-09-25", "Albo-Italic.ttf")}
SRC = os.path.join(HERE, "outliers-2026-09-25.html")
OUT = os.path.join(HERE, "outliers-live-2026-09-25.html")

PARAGRAPH = ("It is a truth universally acknowledged, that a single man in possession "
             "of a good fortune, must be in want of a wife. The rhythm of the argument "
             "was wrongly named: You and John found every agreement in the software "
             "vocabulary, first things first, back past the true rule because the "
             "community had checked it. Verification took two numbers, and her, "
             "perfect latency, was kinked; the Witch of Kasov said Quiet, it is English.")


def shape_x(font, text, kern):
    """x offsets of each character's glyph in `text`, shaped by HarfBuzz."""
    feats = "kern" if kern else "-kern"
    out = subprocess.run(["hb-shape", font, text, f"--features={feats},-liga,-clig,-dlig",
                          "--output-format=json", "--no-glyph-names"],
                         capture_output=True, text=True, check=True).stdout
    return [g["ax"] for g in json.loads(out)]


def pair_kern(font, a, b):
    """The kern HarfBuzz applies between a and b, in font units."""
    with_k = shape_x(font, a + b, True)
    without = shape_x(font, a + b, False)
    return with_k[0] - without[0]


def main():
    html = open(SRC).read()
    items = json.loads(re.search(r"const ITEMS = (\[.*?\]);", html).group(1))
    words, _ = pair_census.harvest()
    _, carrier = pair_census.pairs_from(words)
    # Extra real words per card: the most common words in his books carrying
    # the pair, excluding the card's own word and anything ungainly.
    for it in items:
        a, b = it["pair"].split(" ")
        cands = carrier.get((a, b), collections.Counter())
        extra = []
        for w, n in cands.most_common(200):
            w = w.rstrip(".,;:!?") if not b in ".,;:!?" else w
            if w == it["word"] or len(w) < 3 or len(w) > 12 or w in extra: continue
            if any(ch not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'.,;:!?" for ch in w): continue
            extra.append(w)
            if len(extra) == 4: break
        it["extra"] = extra
    # THE HUNDRED LONG WORDS (owner 2026-09-25: "give me a hundred long words
    # in 2x so I can give kerning feedback"): the most common words of 10+
    # letters in his own books, lowercase, one per stem-ish (no plural twins).
    longw, seen = [], set()
    for w, n in words.most_common():
        w = w.rstrip(".,;:!?")
        if len(w) < 10 or not w.isalpha() or not w.islower(): continue
        stem = w[:8]
        if stem in seen: continue
        seen.add(stem); longw.append(w)
        if len(longw) == 100: break
    # Every adjacent pair in every text the page shows, per style.
    texts = {"roman": set(longw), "italic": set(longw)}
    for it in items:
        for w in [it["word"]] + it["extra"]:
            texts[it["style"]].add(w)
    for st in texts: texts[st].add(PARAGRAPH)
    kerns = {}
    for st, ts in texts.items():
        pairs = set()
        for t in ts:
            for i in range(len(t) - 1):
                if t[i] != " " and t[i + 1] != " ": pairs.add(t[i:i + 2])
        kerns[st] = {p: pair_kern(FONTS[st], p[0], p[1]) for p in sorted(pairs)}
        kerns[st] = {p: v for p, v in kerns[st].items() if v != 0}
        print(st, len(pairs), "pairs,", len(kerns[st]), "kerned")
    # The same hundred words drawn from the fonts at the phone's 2x reading
    # size (54 px = 13 pt on the 2x app), native pixels, kerning and ligatures
    # ON as the app renders them -- ten words to an image, roman then italic.
    from PIL import Image, ImageDraw, ImageFont
    os.makedirs(os.path.join(HERE, "live-2x"), exist_ok=True)
    fr = ImageFont.truetype(FONTS["roman"], 54, layout_engine=ImageFont.Layout.RAQM)
    fi = ImageFont.truetype(FONTS["italic"], 54, layout_engine=ImageFont.Layout.RAQM)
    lab = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 13)
    for k in range(10):
        chunk = longw[k * 10:(k + 1) * 10]
        im = Image.new("L", (700, 150 * len(chunk)), 255); d = ImageDraw.Draw(im)
        for j, w in enumerate(chunk):
            y = j * 150
            d.text((4, y + 2), f"{k * 10 + j + 1}", font=lab, fill=120)
            d.text((34, y + 6), w, font=fr, fill=0)
            d.text((34, y + 76), w, font=fi, fill=0)
            d.line([(0, y + 149), (700, y + 149)], fill=215)
        im.save(os.path.join(HERE, "live-2x", f"long-{k + 1:02d}.png"))
    fonts64 = {st: base64.b64encode(open(f, "rb").read()).decode() for st, f in FONTS.items()}
    page = TEMPLATE.replace("__ITEMS__", json.dumps(items)) \
                   .replace("__KERNS__", json.dumps(kerns)) \
                   .replace("__PARA__", json.dumps(PARAGRAPH)) \
                   .replace("__LONG__", json.dumps(longw)) \
                   .replace("__ROMAN__", fonts64["roman"]).replace("__ITALIC__", fonts64["italic"])
    open(OUT, "w").write(page)
    print("wrote", OUT, len(page))


TEMPLATE = r"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Albo Live Bench</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
  @font-face{font-family:"AlboR";src:url("data:font/ttf;base64,__ROMAN__") format("truetype");font-display:block}
  @font-face{font-family:"AlboI";src:url("data:font/ttf;base64,__ITALIC__") format("truetype");font-display:block}
  :root{--paper:#F6F6F4;--ink:#17181C;--soft:#4A4D55;--rule:#D9D9D4;--card:#FFF;--accent:#2F5872;--accent-soft:#E7EDF2;
    --good:#2D6A4A;--good-soft:#E3EFE8;--hot:#9A3B1C;--sans:"IBM Plex Sans",system-ui,-apple-system,Arial,sans-serif;--mono:"IBM Plex Mono",ui-monospace,Menlo,monospace}
  @media (prefers-color-scheme:dark){:root:not([data-theme="light"]){color-scheme:dark;--paper:#131418;--ink:#E9E9E5;--soft:#A3A7AF;--rule:#2C2E35;--card:#1B1D22;--accent:#8FB6D1;--accent-soft:#1E2A33;--good:#7FC3A0;--good-soft:#17251E;--hot:#E08B66}}
  :root[data-theme="dark"]{color-scheme:dark;--paper:#131418;--ink:#E9E9E5;--soft:#A3A7AF;--rule:#2C2E35;--card:#1B1D22;--accent:#8FB6D1;--accent-soft:#1E2A33;--good:#7FC3A0;--good-soft:#17251E;--hot:#E08B66}
  *{box-sizing:border-box} body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--sans);font-size:16px;line-height:1.5}
  .wrap{max-width:880px;margin:0 auto;padding:0 16px;padding-block:28px 90px;display:flex;flex-direction:column;gap:16px}
  h1{margin:0;font-size:clamp(25px,4.5vw,33px);line-height:1.12} .lede{margin:0;color:var(--soft);max-width:64ch}
  .live{position:sticky;top:0;z-index:5;background:var(--paper);border-bottom:1px solid var(--rule);padding:10px 0;display:flex;flex-direction:column;gap:6px}
  .live .t{font-size:var(--psize);line-height:1.45;font-kerning:none;font-variant-ligatures:none;white-space:normal}
  .roman{font-family:"AlboR",Georgia,serif}.italic{font-family:"AlboI",Georgia,serif}
  .bar{display:flex;gap:9px;flex-wrap:wrap;align-items:center;font-size:13px;color:var(--soft)}
  .seg{display:flex;border:1px solid var(--rule);border-radius:5px;overflow:hidden}
  .seg button{font:inherit;font-size:13px;padding:5px 10px;background:transparent;color:var(--ink);border:0;cursor:pointer}
  .seg button[aria-pressed="true"]{background:var(--accent);color:#fff}
  .status{font-family:var(--mono);font-size:12px;margin-left:auto}
  .card{background:var(--card);border:1px solid var(--rule);border-radius:6px;padding:12px 14px;display:flex;flex-direction:column;gap:8px}
  .card.done{border-color:var(--good)}
  .cardhead{display:flex;gap:9px;align-items:baseline;flex-wrap:wrap}
  .pair{font-family:var(--mono);font-size:12px;letter-spacing:.1em;color:var(--accent);background:var(--accent-soft);padding:3px 8px;border-radius:3px}
  .freq,.other{font-family:var(--mono);font-size:11.5px;color:var(--soft)} .other{margin-left:auto}
  .big{font-size:clamp(34px,7vw,54px);line-height:1.2;white-space:nowrap;overflow-x:auto;font-kerning:none;font-variant-ligatures:none;display:block}
  .extra{font-size:var(--psize);color:var(--soft);font-kerning:none;font-variant-ligatures:none;display:flex;gap:1.1em;flex-wrap:wrap}
  .extra .w{color:var(--ink)}
  .ctl{display:flex;gap:11px;align-items:center;flex-wrap:wrap}
  input[type=range]{flex:1 1 200px;min-width:160px;accent-color:var(--accent)}
  .val{font-family:var(--mono);font-size:12.5px;min-width:6ch;text-align:right}
  .reset{margin-left:auto;font-size:12px;background:none;border:0;color:var(--soft);cursor:pointer;text-decoration:underline}
  .hl{box-shadow:inset 0 -2px 0 var(--hot)}
  footer{border-top:1px solid var(--rule);padding-top:14px;color:var(--soft);font-size:13.5px;display:flex;flex-direction:column;gap:10px}
  textarea{width:100%;min-height:110px;font-family:var(--mono);font-size:11.5px;background:var(--card);color:var(--ink);border:1px solid var(--rule);border-radius:5px;padding:8px}
  .more{font:inherit;font-size:14px;padding:8px 14px;border-radius:5px;border:1px solid var(--rule);background:var(--card);color:var(--ink);cursor:pointer}
</style></head><body>
<div class="wrap">
  <header style="display:flex;flex-direction:column;gap:8px">
    <h1>Where should the letters sit? — live</h1>
    <p class="lede">Every text here is set letter by letter from the font's own kerning plus your answers. So moving one pair's slider re-sets that pair everywhere, in the paragraphs, in every card's word and in the extra words under each card, as you drag. The pair you're moving is underlined wherever it appears. Answers from the first page are carried over.</p>
  </header>
  <div class="live">
    <div class="bar"><span>paragraphs</span>
      <div class="seg" id="size"><button data-v="15">15</button><button data-v="19" aria-pressed="true">19</button><button data-v="24">24</button></div>
      <span class="status" id="status">local only</span></div>
    <div class="t roman" id="pr"></div>
    <div class="t italic" id="pi"></div>
  </div>
  <div id="list" style="display:flex;flex-direction:column;gap:10px"></div>
  <section style="display:flex;flex-direction:column;gap:10px">
    <h2 style="margin:10px 0 0;font-size:22px">A hundred long words</h2>
    <p class="lede">These are the most common long words in your books, each in roman and then italic. They are set live, so your sliders above move them too. <b>Tap between two letters</b> to flag that gap: once for <span style="color:var(--hot)">too tight</span>, twice for <span style="color:var(--accent)">too loose</span>, three times to clear.</p>
    <div id="long" style="display:flex;flex-direction:column;gap:6px"></div>
    <h2 style="margin:14px 0 0;font-size:22px">The same words as the phone draws them (2×)</h2>
    <p class="lede">These are rendered from the real font files at the phone's 2× reading size (54 px), native pixels, with the app's own kerning and ligatures on. They don't move with the sliders.</p>
    <div id="raster" style="display:flex;flex-direction:column;gap:8px"></div>
  </section>
  <footer>
    <div>Ligatures are off on this page, because each letter is placed separately. A number you leave is a correction to the shipped white, in thousandths of an em.</div>
    <div style="display:flex;gap:9px;align-items:center"><button class="more" id="copy">Copy answers</button><span id="copied" class="freq"></span></div>
    <textarea id="export" readonly aria-label="answers as JSON"></textarea>
  </footer>
</div>
<script>
const BENCH = "outliers-2026-09-25";
const ITEMS = __ITEMS__;
const KERN = __KERNS__;
const PARA = __PARA__;
const LONG = __LONG__;
const gaps = {};   // "style|word|i" -> "tight" | "loose"
const LS = "albo-" + BENCH;
const state = {v:{}, size:19, hot:null};
const $ = s => document.querySelector(s);
const key = it => it.style + "_" + it.id;
const pairOf = it => it.pair.replace(" ", "");
const cell = it => (state.v[key(it)] ||= {d:0, verdict:""});
const isSet = it => !!(state.v[key(it)] && state.v[key(it)].touched);
let db = null;
// adj[style][pair] -> his current delta (live, including an unsaved drag)
function adj(style){ const m = {}; for (const it of ITEMS) if (it.style === style){ const c = state.v[key(it)]; if (c && (c.touched || c.live)) m[pairOf(it)] = c.d; } return m; }
// Set `text` into `el`, one span per letter, each letter placed by the kern
// for the pair it closes plus his delta for that pair.
function setText(el, text, style, gapKeyBase){
  const k = KERN[style] || {}, a = adj(style); el.textContent = "";
  for (let i = 0; i < text.length; i++){
    const s = document.createElement("span"); s.textContent = text[i];
    if (i > 0 && text[i] !== " " && text[i-1] !== " "){
      const p = text[i-1] + text[i];
      const u = (k[p] || 0) + (a[p] || 0);
      if (u) s.style.marginLeft = (u / 1000) + "em";
      if (state.hot && state.hot.style === style && state.hot.pair === p){ s.classList.add("hl"); if (el.lastChild) el.lastChild.classList.add("hl"); }
      if (gapKeyBase){
        const gk = gapKeyBase + "|" + i, g = gaps[gk];
        if (g) s.style.boxShadow = "inset 2px 0 0 " + (g === "tight" ? "var(--hot)" : "var(--accent)");
        s.dataset.gap = gk; s.style.cursor = "pointer";
      }
    }
    el.appendChild(s);
  }
}
const texts = [];  // {el, text, style}
function reflow(style){ for (const t of texts) if (!style || t.style === style) setText(t.el, t.text, t.style, t.gap); }
function exportJSON(){
  return JSON.stringify({bench:BENCH, answers: ITEMS.filter(isSet).map(it => { const c = cell(it);
    return {style:it.style, id:it.id, pair:pairOf(it), delta:c.d, verdict:c.verdict||"", at:c.at||null}; }),
    gaps: Object.entries(gaps).map(([k, v]) => { const [style, word, i] = k.split("|");
      return {style, word, pair: word[i-1] + word[i], i: +i, verdict: v}; })});
}
function setStatus(extra){
  $("#status").textContent = (extra ? extra + " · " : "") + ITEMS.filter(isSet).length + "/" + ITEMS.length + " answered";
  $("#export").value = exportJSON();
}
function card(it){
  const cur = cell(it);
  const c = document.createElement("div"); c.className = "card" + (isSet(it) ? " done" : "");
  const head = document.createElement("div"); head.className = "cardhead";
  const pair = document.createElement("span"); pair.className = "pair"; pair.textContent = it.pair;
  const freq = document.createElement("span"); freq.className = "freq"; freq.textContent = it.n.toLocaleString() + " in your books";
  const other = document.createElement("span"); other.className = "other";
  const label = () => other.textContent = it.style + " · " + (isSet(it) ? "saved" : "not saved"); label();
  head.append(pair, freq, other);
  const big = document.createElement("span"); big.className = "big " + it.style;
  texts.push({el: big, text: it.word, style: it.style});
  const ex = document.createElement("div"); ex.className = "extra " + it.style;
  for (const w of it.extra || []){ const s = document.createElement("span"); s.className = "w"; ex.appendChild(s); texts.push({el: s, text: w, style: it.style}); }
  const ctl = document.createElement("div"); ctl.className = "ctl";
  const range = document.createElement("input"); range.type = "range"; range.min = "-60"; range.max = "60"; range.step = "1"; range.value = cur.d;
  range.setAttribute("aria-label", "spacing for " + it.pair + ", " + it.style);
  const val = document.createElement("span"); val.className = "val";
  const show = () => val.textContent = (cur.d > 0 ? "+" : "") + cur.d; show();
  const commit = () => { cur.touched = true; cur.live = false; cur.at = new Date().toISOString(); c.classList.add("done"); label(); setStatus(); save(it); };
  range.addEventListener("pointerdown", () => { state.hot = {style: it.style, pair: pairOf(it)}; reflow(it.style); });
  range.addEventListener("focus", () => { state.hot = {style: it.style, pair: pairOf(it)}; reflow(it.style); });
  range.addEventListener("input", () => { cur.d = parseInt(range.value, 10); cur.live = true; show(); reflow(it.style); });
  range.addEventListener("change", commit);
  const reset = document.createElement("button"); reset.className = "reset"; reset.textContent = "shipped";
  reset.addEventListener("click", () => { cur.d = 0; range.value = 0; show(); commit(); reflow(it.style); });
  ctl.append(range, val, reset);
  c.append(head, big, ex, ctl);
  return c;
}
function render(){
  texts.length = 0;
  texts.push({el: $("#pr"), text: PARA, style: "roman"}, {el: $("#pi"), text: PARA, style: "italic"});
  const list = $("#list"); list.innerHTML = "";
  for (const it of ITEMS) list.appendChild(card(it));
  const L = $("#long"); L.innerHTML = "";
  LONG.forEach((w, n) => {
    const row = document.createElement("div"); row.style.cssText = "display:flex;gap:10px;align-items:baseline;flex-wrap:wrap";
    const num = document.createElement("span"); num.className = "freq"; num.textContent = n + 1; num.style.minWidth = "2.2em";
    row.appendChild(num);
    for (const st of ["roman", "italic"]){
      const s = document.createElement("span"); s.className = "big " + st; s.style.fontSize = "clamp(26px,5vw,40px)";
      row.appendChild(s); texts.push({el: s, text: w, style: st, gap: st + "|" + w});
    }
    L.appendChild(row);
  });
  const R = $("#raster"); if (!R.childElementCount) for (let k = 1; k <= 10; k++){
    const img = document.createElement("img"); img.src = "live-2x/long-" + String(k).padStart(2, "0") + ".png";
    img.alt = "long words " + ((k-1)*10+1) + "-" + (k*10) + ", 2x"; img.style.cssText = "display:block;width:100%;height:auto;max-width:700px;border:1px solid var(--rule);background:#fff";
    R.appendChild(img);
  }
  document.documentElement.style.setProperty("--psize", state.size + "px");
  reflow(); setStatus();
}
function keepLocal(){ try { localStorage.setItem(LS, JSON.stringify(state.v)); } catch(e){} }
let pending = new Set(), timer = null;
function save(it){
  keepLocal(); if (!db) return;
  pending.add(key(it)); clearTimeout(timer);
  timer = setTimeout(async () => {
    for (const k of [...pending]){ pending.delete(k); const v = state.v[k];
      try { await db.doc("outliers/" + k).set({delta:v.d, verdict:v.verdict||"", touched:true, style:k.split("_")[0], bench:BENCH, at:v.at||new Date().toISOString()}); setStatus("saved"); }
      catch(e){ setStatus("not saved (" + ((e && e.code) || "error") + ")"); } }
  }, 350);
}
$("#size").addEventListener("click", e => { const b = e.target.closest("button"); if (!b) return;
  state.size = parseInt(b.dataset.v, 10); for (const x of $("#size").children) x.setAttribute("aria-pressed", String(x === b));
  document.documentElement.style.setProperty("--psize", state.size + "px"); });
$("#copy").addEventListener("click", async () => { const t = $("#export"); t.value = exportJSON();
  try { await navigator.clipboard.writeText(t.value); $("#copied").textContent = "copied"; } catch(e){ t.select(); $("#copied").textContent = "selected, copy it by hand"; } });
try { const s = JSON.parse(localStorage.getItem(LS) || "null"); if (s) state.v = s; } catch(e){}
try { Object.assign(gaps, JSON.parse(localStorage.getItem(LS + "-gaps") || "{}")); } catch(e){}
document.addEventListener("click", e => {
  const s = e.target.closest("[data-gap]"); if (!s) return;
  const gk = s.dataset.gap, next = {undefined: "tight", tight: "loose", loose: undefined}[gaps[gk]];
  if (next) gaps[gk] = next; else delete gaps[gk];
  try { localStorage.setItem(LS + "-gaps", JSON.stringify(gaps)); } catch(err){}
  const style = gk.split("|")[0]; reflow(style); setStatus();
  if (db){ const id = gk.replace(/\|/g, "_");
    (next ? db.doc("gaps/" + id).set({key: gk, verdict: next, at: new Date().toISOString()}) : db.doc("gaps/" + id).delete())
      .then(() => setStatus("saved")).catch(err => setStatus("not saved (" + ((err && err.code) || "error") + ")")); }
});
render();
(async () => {
  db = await (window.claude?.use?.("db") ?? Promise.resolve(null));
  if (!db){ setStatus("local only, use Copy answers"); return; }
  try { const snap = await db.collection("outliers").get();
    for (const d of snap.docs){ const b = d.data() || {}; if (!ITEMS.some(it => key(it) === d.id)) continue;
      state.v[d.id] = {d: b.delta || 0, verdict: b.verdict || "", touched: true, at: b.at}; } } catch(e){}
  try { const g = await db.collection("gaps").get();
    for (const d of g.docs){ const b = d.data() || {}; if (b.key && b.verdict) gaps[b.key] = b.verdict; } } catch(e){}
  render();
})();
</script></body></html>
"""

if __name__ == "__main__":
    main()
