#!/usr/bin/env python3
"""Local VLM judge (LM Studio) on the hard-five stimuli, plus the MIXED arm.

    lms server start; lms load qwen3-vl-8b-instruct-mlx
    $VENV/bin/python hard5_vlm.py [--model qwen3-vl-8b-instruct-mlx]
    lms unload --all; lms server stop

Reads only the stimuli the other judges get ($HARD5_DIR/stimuli/) and the key
to SCORE afterwards. Three tasks, every one asked in two presentation orders
so position bias is measured, not assumed:

  f-ladder  nine rung images of a ladder in one message, in letter order A..I
            and again reversed I..A; native (54 px) and x3 copies, word and
            phrase. The prompt is INSTRUCTIONS.md's question.
  f-2afc    the 30 two-line trials, native and x3 (each trial already exists
            in both top/bottom orders).
  g1 mixed  B2 (held out) proposes the three rungs nearest its prediction; the
            VLM picks among only those three (their own random letters),
            both orders, word and phrase, native.
"""
import argparse, base64, json, os, re, subprocess, time, urllib.request
import numpy as np
from hard5_common import SCRATCH

API = "http://localhost:1234/v1/chat/completions"
ST = os.path.join(SCRATCH, "stimuli")
Q_LADDER = ("Which image has the most even, natural spacing for reading at book size? "
            "Answer with the letter.")
Q_AFC = ("Which line has the more even, natural spacing for reading at book size? "
         "Answer 1 or 2.")


def lms_rss_mb():
    out = subprocess.run(["ps", "-axo", "rss,command"], capture_output=True, text=True).stdout
    v = [int(l.split()[0]) for l in out.splitlines()[1:] if "LM Studio" in l or "lmstudio" in l.lower()]
    return round(sum(v) / 1024)


def b64(path):
    return "data:image/png;base64," + base64.b64encode(open(path, "rb").read()).decode()


def ask(model, intro, images, question, valid):
    content = [{"type": "text", "text": intro}]
    for lab, path in images:
        content += [{"type": "text", "text": f"Image {lab}:"}, {"type": "image_url", "image_url": {"url": b64(path)}}]
    content.append({"type": "text", "text": question})
    body = dict(model=model, temperature=0, max_tokens=40, messages=[{"role": "user", "content": content}])
    req = urllib.request.Request(API, json.dumps(body).encode(), {"Content-Type": "application/json"})
    t = time.time()
    r = json.load(urllib.request.urlopen(req, timeout=900))
    txt = (r["choices"][0]["message"].get("content") or "").strip()
    m = re.findall(r"\b([%s])\b" % valid, txt)
    return (m[0] if m else None), round(time.time() - t, 2), txt[:60], r.get("usage", {})


INTRO = {
    "ladder": ("These images show the same {what} set in a book typeface at e-reader size. They are "
               "identical except for the space between one pair of adjacent letters: {pair} in \"{word}\". "
               "Each image has an identifying letter at its left edge; the letters are in random order "
               "and mean nothing."),
    "afc": ("This image shows the same text twice, labelled 1 (top) and 2 (bottom), set in a book "
            "typeface at e-reader size. The two lines differ at most in the space between the letters "
            "{pair} in \"{word}\"."),
}


def retry(model):
    """Second pass over calls that gave NO answer (the 8B wrote prose and ran
    out of its 40-token budget): the same message plus one sentence, "Reply
    with only the letter." / "Reply with only 1 or 2." Marked retry=True."""
    out = os.path.join(SCRATCH, "results_vlm-" + model.replace("/", "_") + ".json")
    log = json.load(open(out))
    key = json.load(open(os.path.join(SCRATCH, "key.json")))
    P = {p["n"]: p for p in key["pairs"]}
    for x in log["ladder"] + log["mixed"]:
        if x["label"] is not None:
            continue
        pk = P[x["n"]]; mp = pk["ladder"][x["variant"]]
        d = os.path.join(ST, f"pair{x['n']}", "x3" if x.get("scale") == "x3" else "")
        if "candidates_px" in x:
            labs = sorted(L for L, r in mp.items() if r["px"] in x["candidates_px"])
            labs = labs if x["order"] == "fwd" else labs[::-1]
        else:
            labs = sorted(mp) if x["order"] == "AtoI" else sorted(mp)[::-1]
        pr = f"\"{pk['pair'][0]}\" and \"{pk['pair'][1]}\""
        L, sec, raw, _ = ask(model, INTRO["ladder"].format(what=x["variant"], pair=pr, word=pk["word"]),
                             [(l, os.path.join(d, f"{x['variant']}_{l}.png")) for l in labs],
                             Q_LADDER + " Reply with only the letter.", "".join(labs))
        x.update(label=L, pos=(labs.index(L) if L else None), est=(mp[L]["units"] if L else None),
                 sec=sec, raw=raw, retry=True)
        print("retry", x["n"], x["variant"], x.get("scale"), x["order"], L, flush=True)
    A = {t["trial"]: t for t in key["afc"]}
    for x in log["afc"]:
        if x["answer"] is not None:
            continue
        t = A[x["trial"]]
        path = os.path.join(ST, "afc", "" if x["scale"] == "native" else "x3", f"trial{t['trial']:02d}.png")
        word = P[t["pair_n"]]["word"]
        L, sec, raw, _ = ask(model, INTRO["afc"].format(pair=f"\"{t['pair'][0]}\" and \"{t['pair'][1]}\"", word=word),
                             [("", path)], Q_AFC + " Reply with only 1 or 2.", "12")
        x.update(answer=L, chose=((t["top"] if L == "1" else t["bottom"]) if L else None), sec=sec, raw=raw, retry=True)
        print("retry afc", x["trial"], x["scale"], L, flush=True)
    json.dump(log, open(out, "w"), indent=1)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--model", default="qwen3-vl-8b-instruct-mlx")
    ap.add_argument("--retry", action="store_true")
    args = ap.parse_args()
    if args.retry:
        return retry(args.model)
    key = json.load(open(os.path.join(SCRATCH, "key.json")))
    sel = {(x["style"], x["pair"]): x for x in json.load(open(os.path.join(SCRATCH, "selection.json")))["top5"]}
    upp = key["units_per_px"]
    log = dict(model=args.model, ladder=[], afc=[], mixed=[], rss_mb=[])
    for pk in key["pairs"]:
        n, pr = pk["n"], f"\"{pk['pair'][0]}\" and \"{pk['pair'][1]}\""
        for v in ("word", "phrase"):
            mp = pk["ladder"][v]
            for scale in ("native", "x3"):
                d = os.path.join(ST, f"pair{n}", "" if scale == "native" else "x3")
                for order in ("AtoI", "ItoA"):
                    labs = sorted(mp) if order == "AtoI" else sorted(mp)[::-1]
                    imgs = [(L, os.path.join(d, f"{v}_{L}.png")) for L in labs]
                    intro = INTRO["ladder"].format(what=v, pair=pr, word=pk["word"])
                    L, sec, raw, use = ask(args.model, intro, imgs, Q_LADDER, "A-I")
                    est = mp[L]["units"] if L else None
                    log["ladder"].append(dict(n=n, style=pk["style"], pair=pk["pair"], variant=v, scale=scale,
                                              order=order, label=L, pos=(labs.index(L) if L else None),
                                              est=est, sec=sec, raw=raw))
                    print("ladder", n, pk["pair"], v, scale, order, L, est, sec, flush=True)
            # g1 mixed: B2's three nearest rungs
            b2px = int(round(sel[(pk["style"], pk["pair"])]["b2_held"] / upp))
            cand = [k for k in (b2px - 1, b2px, b2px + 1)]
            labs = sorted(L for L, r in mp.items() if r["px"] in cand)
            for order in ("fwd", "rev"):
                ls = labs if order == "fwd" else labs[::-1]
                imgs = [(L, os.path.join(ST, f"pair{n}", f"{v}_{L}.png")) for L in ls]
                intro = INTRO["ladder"].format(what=v, pair=pr, word=pk["word"])
                L, sec, raw, _ = ask(args.model, intro, imgs, Q_LADDER, "".join(labs))
                log["mixed"].append(dict(n=n, style=pk["style"], pair=pk["pair"], variant=v, order=order,
                                         candidates_px=cand, label=L, pos=(ls.index(L) if L else None),
                                         est=(mp[L]["units"] if L else None), sec=sec, raw=raw))
                print("mixed", n, pk["pair"], v, order, L, sec, flush=True)
        log["rss_mb"].append(lms_rss_mb())
    for t in key["afc"]:
        for scale in ("native", "x3"):
            path = os.path.join(ST, "afc", "" if scale == "native" else "x3", f"trial{t['trial']:02d}.png")
            word = next(p["word"] for p in key["pairs"] if p["n"] == t["pair_n"])
            intro = INTRO["afc"].format(pair=f"\"{t['pair'][0]}\" and \"{t['pair'][1]}\"", word=word)
            L, sec, raw, _ = ask(args.model, intro, [("", path)], Q_AFC, "12")
            chose = (t["top"] if L == "1" else t["bottom"]) if L else None
            log["afc"].append(dict(trial=t["trial"], pair=t["pair"], other=t["other"], scale=scale,
                                   identical=t["identical"], answer=L, chose=chose, sec=sec, raw=raw))
            print("afc", t["trial"], t["pair"], t["other"], scale, L, chose, sec, flush=True)
    log["rss_mb"].append(lms_rss_mb())
    out = os.path.join(SCRATCH, "results_vlm-" + args.model.replace("/", "_") + ".json")
    json.dump(log, open(out, "w"), indent=1)
    print("wrote", out)


if __name__ == "__main__":
    main()
