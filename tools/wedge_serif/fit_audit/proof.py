"""The fit-audit proof page: each cut's worst-fitting glyphs in words, beside
their construction family, with the axis z-scores as a heat bar, and the
whole alphabet coloured by fit score.

Rendering is the reader's (legib.Renderer: FreeType NO HINTING, 2-bit levels,
HarfBuzz placement). Every image is a lossless PNG at native pixels; the 27 px
rows are magnified x2 NEAREST in the PNG itself, never by CSS, and no <img>
carries a width or height.

    python3 proof.py --fit fit.json --fonts DIR --out PROOFDIR [--top 12]
"""
import argparse, html, json, os, sys
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import CUTS, FAMILY, LC, UC, FIG  # noqa: E402
from legib import Renderer  # noqa: E402
from score import AXES  # noqa: E402

WORDS = {
    "a": "banana cataract", "b": "bubble absorb", "c": "accident cyclic", "d": "added dividend",
    "e": "eleven referee", "f": "affair fifteen", "g": "going baggage", "h": "health which",
    "i": "initial finish", "j": "jejune justify", "k": "knock kickback", "l": "little lullaby",
    "m": "minimum mammal", "n": "nonsense union", "o": "orthodox motto", "p": "puppet appear",
    "q": "quiet quaque", "r": "rarer mirror", "s": "sassiness stress", "t": "attitude tattoo",
    "u": "unusual tumult", "v": "revive velvet", "w": "wayward window", "x": "boxwax exotic",
    "y": "yearly everybody", "z": "puzzle zigzag",
    "A": "Anna Atlas", "B": "Bob Boston", "C": "Chicago Cecil", "D": "David Dodd",
    "E": "Egypt Edward", "F": "Friday Fifi", "G": "George Gaga", "H": "Hannah Hugh",
    "I": "India Isaiah", "J": "January Jojo", "K": "Kansas Kirk", "L": "London Lille",
    "M": "Miami Maxim", "N": "Nancy Noon", "O": "Ohio Otto", "P": "Paris Pepper",
    "Q": "Quebec Queen", "R": "Rome Rory", "S": "Sussex Sam", "T": "Texas Titus",
    "U": "Utah Ursula", "V": "Venice Viva", "W": "Wales Willow", "X": "Xerxes Xavier",
    "Y": "York Yolanda", "Z": "Zurich Zazu",
}
FIGWORDS = "1066 1789 2024 3690 4815 5678 6502 7389 8086 9021"
PAD = 10


def draw(R, text, hi=None):
    """Render one line; return an RGB array. Glyphs of the character `hi` are
    inked in the accent colour so the eye finds them in the word."""
    ppem = R.ppem
    W = int(ppem * 0.8 * len(text)) + 2 * PAD
    H = int(ppem * 1.65) + 2 * PAD
    base = PAD + int(ppem * 1.15)
    import uharfbuzz as hb
    buf = hb.Buffer(); buf.add_str(text); buf.guess_segment_properties()
    hb.shape(R.hbf, buf, {"kern": True, "liga": False})
    k = ppem / R.upm
    ink = np.zeros((H, W), np.uint8); acc = np.zeros((H, W), np.uint8)
    x = PAD; right = 0
    for inf, pos in zip(buf.glyph_infos, buf.glyph_positions):
        lv, left, top = R.glyph(inf.codepoint)
        gx = int(round(x + pos.x_offset * k)) + left; gy = base - top
        if lv.size:
            h, w = lv.shape
            tgt = acc if (hi is not None and text[inf.cluster] == hi) else ink
            sub = tgt[gy:gy + h, gx:gx + w]
            np.maximum(sub, lv[:sub.shape[0], :sub.shape[1]], out=sub)
            right = max(right, gx + w)
        x += pos.x_advance * k
    ink, acc = ink[:, :right + PAD], acc[:, :right + PAD]
    paper = np.array([250, 249, 246], float); black = np.array([20, 20, 20], float)
    red = np.array([196, 38, 32], float)
    t = (ink / 3.0)[..., None]; u = (acc / 3.0)[..., None]
    img = paper * (1 - t) + black * t
    img = img * (1 - u) + red * u
    return img.astype(np.uint8)


def stack(rows, gap=4):
    W = max(r.shape[1] for r in rows)
    out = []
    for r in rows:
        pad = np.full((r.shape[0], W - r.shape[1], 3), [250, 249, 246], np.uint8)
        out.append(np.concatenate([r, pad], 1))
        out.append(np.full((gap, W, 3), [250, 249, 246], np.uint8))
    return np.concatenate(out[:-1], 0)


def nearest(a, k):
    return np.repeat(np.repeat(a, k, 0), k, 1)


def family_text(ch, rows):
    """The glyph between each member of its own family in that cut."""
    fam = [c for c in (LC + UC + FIG) if FAMILY[c] == FAMILY[ch] and c != ch and c in rows
           and ((c in LC) == (ch in LC)) and ((c in FIG) == (ch in FIG))]
    fam = sorted(fam, key=lambda c: rows[c]["F"])[:7]   # the best-fitting members
    if ch in FIG:
        return " ".join(f"{c}{ch}{c}" for c in fam)
    n = "n" if ch in LC else "H"
    return f"{n}{ch}{n} " + " ".join(f"{c}{ch}{c}" for c in fam if c != n)


def ramp(F):
    """0 -> neutral grey-green, 2 (flag) -> amber, 4+ -> red."""
    t = min(F / 4.0, 1.0)
    stops = [(0.0, (74, 124, 89)), (0.5, (201, 150, 38)), (1.0, (196, 38, 32))]
    for (a, ca), (b, cb) in zip(stops, stops[1:]):
        if t <= b:
            f = (t - a) / (b - a)
            return tuple(int(ca[i] + (cb[i] - ca[i]) * f) for i in range(3))
    return stops[-1][1]


def alphabet(R, rows):
    """Every glyph, inked in its fit-score colour."""
    cells = []
    for ch in LC + UC + FIG:
        if ch not in rows:
            continue
        a = draw(R, ch)
        g = (250 - a.mean(2).astype(float)) / 230.0
        col = np.array(ramp(rows[ch]["F"]), float)
        paper = np.array([250, 249, 246], float)
        g = np.clip(g, 0, 1)[..., None]
        cells.append((paper * (1 - g) + col * g).astype(np.uint8))
    lines, cur, W = [], [], 0
    for c in cells:
        if W + c.shape[1] > 1100 and cur:
            lines.append(np.concatenate(cur, 1)); cur, W = [], 0
        cur.append(c); W += c.shape[1]
    if cur:
        lines.append(np.concatenate(cur, 1))
    return stack(lines, 0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fit", required=True)
    ap.add_argument("--fonts", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--top", type=int, default=12)
    ap.add_argument("--validation")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    F = json.load(open(a.fit))
    sections = []
    for cut in CUTS:
        rows = F[cut]
        path = os.path.join(a.fonts, f"Albo-{cut}.ttf")
        R27, R54 = Renderer(path, 0, 27), Renderer(path, 0, 54)
        al = alphabet(R54, rows)
        fn = f"alphabet-{cut}.png"; Image.fromarray(al).save(os.path.join(a.out, fn))
        order = sorted(rows, key=lambda c: -rows[c]["F"])[:a.top]
        cards = []
        for i, ch in enumerate(order):
            r = rows[ch]
            words = FIGWORDS if ch in FIG else WORDS[ch]
            fam = family_text(ch, rows)
            img27 = nearest(stack([draw(R27, words, ch), draw(R27, fam, ch)]), 2)
            img54 = stack([draw(R54, words, ch), draw(R54, fam, ch)])
            f27, f54 = f"{cut}-{i:02d}-27x2.png", f"{cut}-{i:02d}-54.png"
            Image.fromarray(img27).save(os.path.join(a.out, f27))
            Image.fromarray(img54).save(os.path.join(a.out, f54))
            heat = []
            for k, (name, subs, w) in AXES.items():
                if k in r["axes"]:
                    z = r["axes"][k]["z"]; by = r["axes"][k]["by"]
                    t = min(abs(z) / 4.0, 1.0)
                    cls = "pos" if z > 0 else "neg"
                    heat.append(f'<div class="cell {cls}" style="--t:{t:.2f}" title="{html.escape(name)}: {z:+.2f} ({by})">'
                                f'<span class="ax">{k} {html.escape(name)}</span><span class="z">{z:+.1f}</span></div>')
                else:
                    heat.append(f'<div class="cell na"><span class="ax">{k} {html.escape(name)}</span><span class="z">n/a</span></div>')
            reason = r["reason"]; rb = r["axes"][reason]["by"]
            cards.append(f'''
<article class="card">
  <header><span class="glyph">{html.escape(ch)}</span>
    <span class="meta">#{i + 1} &middot; F {r["F"]:.2f}{" &middot; <b>FLAGGED</b>" if r["flag"] else ""} &middot; {html.escape(FAMILY[ch])} family &middot; led by <b>{html.escape(AXES[reason][0])}</b> ({html.escape(rb)})</span></header>
  <div class="heat">{"".join(heat)}</div>
  <figure><img src="{f27}" alt="{html.escape(ch)} at 27 px, x2 nearest"><figcaption>27 px, magnified &times;2 nearest-neighbour. Top: words. Bottom: the glyph between members of its family (best-fitting first). Red = the glyph under audit.</figcaption></figure>
  <figure><img src="{f54}" alt="{html.escape(ch)} at 54 px"><figcaption>54 px, native.</figcaption></figure>
</article>''')
        nflag = sum(v["flag"] for v in rows.values())
        sections.append(f'''
<section>
  <h2>{cut} <small>{nflag} of {len(rows)} flagged (F &ge; 2.0)</small></h2>
  <figure class="alpha"><img src="{fn}" alt="{cut} alphabet coloured by fit score"><figcaption>Every lowercase, capital and figure at 54 px, inked by fit score: green fits, amber is the flag line (F 2), red is F 4 or worse.</figcaption></figure>
  {"".join(cards)}
</section>''')
    page = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Albo Fit Audit</title>
<style>
:root {{ --bg:#f6f5f1; --fg:#1c1c1a; --muted:#6b6a64; --card:#ffffff; --line:#dddbd3;
        --pos:196,38,32; --neg:38,92,170; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ --bg:#141413; --fg:#ecebe6; --muted:#a3a29b; --card:#1f1f1d; --line:#3a3935;
        --pos:236,98,88; --neg:112,160,235; }} }}
:root[data-theme="dark"] {{ --bg:#141413; --fg:#ecebe6; --muted:#a3a29b; --card:#1f1f1d; --line:#3a3935; --pos:236,98,88; --neg:112,160,235; }}
body {{ background:var(--bg); color:var(--fg); font:16px/1.5 -apple-system, system-ui, sans-serif; margin:0; padding:24px 16px; }}
main {{ max-width:1160px; margin:0 auto; }}
h1 {{ font-size:1.6rem; margin:0 0 .25rem; }} h2 {{ margin:2.2rem 0 .8rem; border-bottom:1px solid var(--line); padding-bottom:.3rem; }}
h2 small {{ color:var(--muted); font-weight:400; font-size:.9rem; }}
p.lede {{ color:var(--muted); max-width:70ch; }}
.card {{ background:var(--card); border:1px solid var(--line); border-radius:10px; padding:12px; margin:0 0 14px; }}
.card header {{ display:flex; gap:12px; align-items:baseline; flex-wrap:wrap; }}
.glyph {{ font-size:1.8rem; font-weight:600; min-width:1.4em; }}
.meta {{ color:var(--muted); font-size:.9rem; }}
.heat {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(96px, 1fr)); gap:4px; margin:10px 0; }}
.cell {{ border-radius:6px; padding:4px 6px; font-size:.78rem; display:flex; justify-content:space-between; gap:6px; border:1px solid var(--line); }}
.cell.pos {{ background:rgba(var(--pos), calc(var(--t) * .85)); }}
.cell.neg {{ background:rgba(var(--neg), calc(var(--t) * .85)); }}
.cell.na {{ opacity:.5; }}
.cell .z {{ font-variant-numeric:tabular-nums; font-weight:600; }}
figure {{ margin:8px 0; overflow-x:auto; }}
figure img {{ display:block; max-width:none; image-rendering:pixelated; }}
figcaption {{ color:var(--muted); font-size:.8rem; }}
</style></head><body><main>
<h1>Albo fit audit, round 402</h1>
<p class="lede">Each cut's worst-fitting letters by the fit score F (docs/albo-fit-audit-2026-09-26.md): deviation from the glyph's construction family, beyond what the same letter shows in six reference serifs, on eight axes. Heat cells: red = the glyph has MORE of that axis than it should, blue = LESS; opacity = |z| up to 4. Rendered as the reader renders: FreeType unhinted, 2-bit. Images are lossless PNG at native pixels; scroll sideways on a phone rather than letting anything be scaled.</p>
{"".join(sections)}
</main></body></html>'''
    open(os.path.join(a.out, "index.html"), "w").write(page)
    print("wrote", os.path.join(a.out, "index.html"))


if __name__ == "__main__":
    main()
