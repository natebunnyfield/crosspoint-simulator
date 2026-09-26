#!/usr/bin/env python3
"""Zero-shot: can the local vision model (LM Studio) see what HE sees in a pair?

PROBE for docs/local-ai-spacing-options-2026-09-26.md, option A.

THE TASK.  For each of the 40 re-asked bench rows (the only rows he has judged
twice, so the target is the mean of two judgments and carries less of his
noise), the bench word is rendered three times, differing ONLY in the white at
the bench pair: -30, 0 and +30 design units (about 2.9 px at the 96 px em used
here -- visible, and inside the bench slider's -60..60).  The arms are stacked
and labelled A/B/C in a seeded random order; the model is asked which has the
most even, natural spacing.  Every row is asked TWICE with the order reversed,
so position bias and self-consistency are measured rather than assumed.

The pick maps to an estimate d in {-30, 0, +30}.  Scored against his answers
beside the same scores for do-nothing and for the held-out ridge.

Rendering: FreeType coverage via fontTools' FreeTypePen on the bench's own
fonts, HarfBuzz positions (the pair's kern included), no hinting.

    lms server start; lms load qwen/qwen3.8-27b
    $VENV/bin/python probe_vlm.py [--rows N] [--model qwen/qwen3.8-27b]
"""
import argparse, base64, io, json, os, random, re, sys, time, urllib.request
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, WS)
import features as FT  # noqa: E402
from fontTools.pens.freetypePen import FreeTypePen
from fontTools.pens.transformPen import TransformPen

KEY = os.path.join(WS, "bench", "reask-2026-09-25.key.json")
ANS = os.path.join(WS, "bench", "answers", "reask-2026-09-25-answers.json")
ITEMS = json.load(open(FT.ITEMS))["items"]
ARMS = (-30, 0, 30)
EM = 96
API = "http://localhost:1234/v1/chat/completions"


def render_word(F, word, i, delta):
    buf = FT.hb.Buffer(); buf.add_str(word); buf.guess_segment_properties()
    FT.hb.shape(F.hb, buf, {"liga": False, "clig": False})
    s = EM / 1000
    x = 0; pos = []
    for k, (inf, p) in enumerate(zip(buf.glyph_infos, buf.glyph_positions)):
        pos.append((F.order[inf.codepoint], x + p.x_offset))
        x += p.x_advance + (delta if k == i else 0)
    W = int((x + 400) * s); H = int(1300 * s)
    img = np.zeros((H, W))
    for name, gx in pos:
        pen = FreeTypePen(F.gs)
        F.gs[name].draw(TransformPen(pen, (1, 0, 0, 1, gx + 200, 350)))
        img = np.maximum(img, pen.array(width=W, height=H, transform=(s, 0, 0, s, 0, 0)))
    return Image.fromarray((255 - img * 255).astype(np.uint8))


def sheet(F, word, i, order):
    ims = [render_word(F, word, i, ARMS[k]) for k in order]
    W = max(im.width for im in ims) + 60; H = sum(im.height for im in ims)
    out = Image.new("L", (W, H), 255); d = ImageDraw.Draw(out)
    try:
        lab = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 28)
    except OSError:
        lab = ImageFont.load_default()
    y = 0
    for n, im in enumerate(ims):
        d.text((8, y + im.height // 2 - 14), "ABC"[n], fill=0, font=lab)
        out.paste(im, (60, y)); y += im.height
        d.line([(0, y - 1), (W, y - 1)], fill=200)
    return out


def ask(model, png, word, a, b):
    b64 = base64.b64encode(png).decode()
    prompt = (f"The image shows the word \"{word}\" set three times, labelled A, B and C. "
              f"The three differ ONLY in the space between the letters \"{a}\" and \"{b}\". "
              "You are an expert type designer judging letter spacing for comfortable reading: "
              "the space between letters should look even with the spaces inside and between "
              "the other letters of the word. Which version, A, B or C, is best spaced at that "
              "pair? Answer with a single letter.")
    # Qwen3.8 thinks whatever the API says (enable_thinking=false and effort
    # "none" were both tried and ignored, measured 2026-09-26); "low" is the
    # shortest effort its chat template accepts.
    body = dict(model=model, temperature=0, max_tokens=2000, reasoning_effort="low",
                messages=[{"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": "data:image/png;base64," + b64}}]}])
    req = urllib.request.Request(API, json.dumps(body).encode(), {"Content-Type": "application/json"})
    t = time.time()
    r = json.load(urllib.request.urlopen(req, timeout=600))
    dt = time.time() - t
    msg = r["choices"][0]["message"]
    txt = (msg.get("content") or "").strip()
    m = re.findall(r"\b([ABC])\b", txt)
    return (m[-1] if m else None), dt, txt, r.get("usage", {})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", type=int, default=40)
    ap.add_argument("--model", default="qwen/qwen3.8-27b")
    ap.add_argument("--save", default=None, help="directory to save each sheet PNG")
    args = ap.parse_args()
    key = {(r["style"], r["id"]): r for r in json.load(open(KEY))["rows"]}
    ans = {(a["style"], a["id"]): a["delta"] for a in json.load(open(ANS))["answers"]}
    fonts = {s: FT.Font(p) for s, p in FT.FONTS.items()}
    items = {it["id"]: it for it in ITEMS}
    rows = sorted(key.values(), key=lambda r: (r["style"], r["id"]))
    random.Random(7).shuffle(rows)          # a mixed sample when --rows < 40
    rows = rows[: args.rows]
    rng = random.Random(20260926)
    log = []
    for r in rows:
        it = next(x for x in ITEMS if x["word"] == r["word"] and x["pair"].replace(" ", "") == r["pair"])
        order = [0, 1, 2]; rng.shuffle(order)
        picks = []
        for o in (order, order[::-1]):
            im = sheet(fonts[r["style"]], it["word"], it["i"], o)
            bio = io.BytesIO(); im.save(bio, "PNG")
            if args.save:
                os.makedirs(args.save, exist_ok=True)
                im.save(os.path.join(args.save, f"{r['style']}_{r['pair']}_{''.join(map(str, o))}.png"))
            a, b = r["pair"][0], r["pair"][1]
            lab, dt, txt, usage = ask(args.model, bio.getvalue(), it["word"], a, b)
            est = ARMS[o["ABC".index(lab)]] if lab else None
            picks.append(dict(order=o, label=lab, est=est, sec=round(dt, 1), raw=txt[-80:],
                              tokens=usage))
        his = (r["previous"] + ans[(r["style"], r["id"])]) / 2
        log.append(dict(style=r["style"], pair=r["pair"], word=it["word"], stratum=r["stratum"],
                        his_prev=r["previous"], his_new=ans[(r["style"], r["id"])], his_mean=his,
                        ridge_held_out=r["held_out"], picks=picks))
        print(f"{r['style']:6s} {r['pair']:3s} {it['word']:14s} his {his:+6.1f} ridge {r['held_out']:+6.1f}"
              f"  vlm {[p['est'] for p in picks]}  labels {[p['label'] for p in picks]}"
              f"  {[p['sec'] for p in picks]}s", flush=True)
        json.dump(log, open(logpath(args.model), "w"), indent=1)   # every row: a stopped run keeps its data
    score(log)


def logpath(model):
    return os.path.join(HERE, "probe_vlm-" + model.replace("/", "_") + ".json")


def score(log):
    ok = [x for x in log if all(p["est"] is not None for p in x["picks"])]
    est = np.array([np.mean([p["est"] for p in x["picks"]]) for x in ok])
    his = np.array([x["his_mean"] for x in ok]); rid = np.array([x["ridge_held_out"] for x in ok])
    same = np.mean([x["picks"][0]["est"] == x["picks"][1]["est"] for x in ok])
    pos = {L: sum(p["label"] == L for x in ok for p in x["picks"]) for L in "ABC"}
    big = [i for i, h in enumerate(his) if abs(h) >= 15]
    sign = np.mean([np.sign(est[i]) == np.sign(his[i]) for i in big]) if big else float("nan")
    rsign = np.mean([np.sign(rid[i]) == np.sign(his[i]) for i in big]) if big else float("nan")
    secs = [p["sec"] for x in log for p in x["picks"]]
    print(f"\nrows scored {len(ok)} of {len(log)}; calls {len(secs)}, median {np.median(secs):.1f}s per call")
    print(f"MAE vs the mean of his two answers: VLM {np.mean(np.abs(est-his)):.2f}  "
          f"ridge {np.mean(np.abs(rid-his)):.2f}  nothing {np.mean(np.abs(his)):.2f}")
    print(f"order-reversed self-agreement {same:.0%}; label counts {pos}")
    print(f"direction right where |his| >= 15 (n={len(big)}): VLM {sign:.0%}  ridge {rsign:.0%}")
    print(f"correlation with his mean: VLM {np.corrcoef(est, his)[0,1]:+.2f}  ridge {np.corrcoef(rid, his)[0,1]:+.2f}")


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--score":
        score(json.load(open(logpath(sys.argv[2]))))
    else:
        main()
