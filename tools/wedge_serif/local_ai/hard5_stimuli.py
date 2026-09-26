#!/usr/bin/env python3
"""Judge-ready stimuli for the five hardest pairs (docs/hard-pairs-eval-2026-09-26.md).

    $VENV/bin/python hard5_stimuli.py        (needs hard5_select.py's selection.json)

RENDERING. As the reader renders (b2_proof.Setter: FreeType default load
flags, 2-bit coverage, linear advances, GPOS kern at 1/16 px, each bitmap at
the pen rounded to a whole pixel), 54 px em, on the fonts every one of his
readings is measured against: bench/fonts-2026-09-20/ (the ZERO). A rung adds
its offset to the pen after the pair's first glyph, and nowhere else.

THE LADDER IS IN WHOLE PIXELS: rung k = k px = k * 1000/54 = 18.52k units,
k = -4..+4, nine rungs A-I. Measured first (--step-check): a 10-unit ladder
(-40..+40) at 54 px is 0.54 px per rung, and the pen's rounding to a whole
pixel makes rungs PIXEL-IDENTICAL: nine rungs gave 5 (ed), 7 (Fo), 8 (it)
and 9 (Wa, n') distinct images -- and where two differ, the pair's own gap
still moves only in whole pixels while the later letters jitter by one as
each glyph's pen rounds on its own. A judge cannot choose between identical
pictures, so the step is the reader's own pixel. His answers (|his| 23..41)
land on rungs +-1 / +-2, never on an edge.

LABELS. Each rung is its own lossless PNG with a letter strip on the left.
The letter-to-rung map is shuffled per pair AND per variant (seeded); the map
lives in hard5/key.json, outside stimuli/. File names carry only pair number,
variant and letter.

2AFC. One image, two lines labelled 1 (top) and 2 (bottom). Three
comparisons per pair, each in BOTH orders, trial numbers shuffled so the two
orders are never adjacent:
    his  vs  zero      his mean answer vs the font he judged (offset 0)
    his  vs  B2-held   vs what B2 predicts WITHOUT any of his readings of it
    his  vs  r395      vs what round 395 ships (already carries his answer
                       within 1-9 units on these five: a near-identical
                       CATCH pair -- a judge should split ~50/50; anything
                       else is position bias measured directly)
2AFC offsets are rounded to whole pixels as the reader would place them.
"""
import argparse, hashlib, json, os, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import b2_proof
from hard5_common import WS, SCRATCH

PX = 54
UPP = 1000 / PX                       # units per pixel at 54 px
FONTS = {"roman": os.path.join(WS, "bench", "fonts-2026-09-20", "Albo-Regular.ttf"),
         "italic": os.path.join(WS, "bench", "fonts-2026-09-20", "Albo-Italic.ttf")}
R395 = {"roman": os.path.join(WS, "bench", "fonts-2026-09-26", "Albo-Regular.ttf"),
        "italic": os.path.join(WS, "bench", "fonts-2026-09-26", "Albo-Italic.ttf")}
CARRIER = {  # (style, pair): (word, index of the pair's first glyph in the word, phrase)
    ("italic", "Fo"): ("For", 0, "For a moment she said nothing"),
    ("roman", "Wa"): ("Wayward", 0, "Wayward was the road home"),
    ("italic", "n'"): ("don't", 2, "I don't know where they went"),
    ("roman", "ed"): ("named", 3, "the man named in the letter"),
    ("roman", "it"): ("with", 1, "she came with the others"),
}
LETTERS = "ABCDEFGHI"
RUNGS = list(range(-4, 5))            # whole pixels


class Offsetter(b2_proof.Setter):
    def line_off(self, text, at, extra_px):
        """line() with extra_px added to the pen after glyph `at`."""
        buf = b2_proof.hb.Buffer(); buf.add_str(text); buf.guess_segment_properties()
        b2_proof.hb.shape(self.hb, buf, self.feats)
        if len(buf.glyph_infos) != len(text):
            raise SystemExit(f"{text!r}: shaped to {len(buf.glyph_infos)} glyphs (a ligature?)")
        s = self.px / self.upm
        pen, out = 0.0, []
        for k, (inf, pos) in enumerate(zip(buf.glyph_infos, buf.glyph_positions)):
            a, l, t, lin = self.glyph(inf.codepoint)
            natural = self.hb.get_glyph_h_advance(inf.codepoint)
            kern = round((pos.x_advance - natural) * s * 16) / 16
            out.append((int(np.floor(pen + 0.5)) + l, t, a))
            pen += lin + kern + (extra_px if k == at else 0.0)
        return out

    def render(self, text, at, extra_px, width=None):
        gl = self.line_off(text, at, extra_px)
        W = width or int(max(x + a.shape[1] for x, _, a in gl) + 2 * PX)
        asc = int(round(PX * 1.0)); H = int(round(PX * 1.45))
        img = np.zeros((H, W), np.uint8)
        for x, t, a in gl:
            if a.size == 0:
                continue
            y = asc - t; x = x + PX // 2
            img[y:y + a.shape[0], x:x + a.shape[1]] = np.maximum(img[y:y + a.shape[0], x:x + a.shape[1]], a)
        return img


_LAB = None


def with_label(cov, text):
    global _LAB
    if _LAB is None:
        _LAB = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 26)
    strip = Image.new("L", (48, cov.shape[0]), 255)
    ImageDraw.Draw(strip).text((12, cov.shape[0] // 2 - 16), text, font=_LAB, fill=0)
    word = Image.fromarray(255 - cov)
    out = Image.new("L", (strip.width + word.width, cov.shape[0]), 255)
    out.paste(strip, (0, 0)); out.paste(word, (strip.width, 0))
    d = ImageDraw.Draw(out); d.line([(strip.width - 2, 0), (strip.width - 2, out.height)], fill=180)
    return out


def save(im, path, x3=True):
    im.save(path)
    if x3:
        d = os.path.join(os.path.dirname(path), "x3"); os.makedirs(d, exist_ok=True)
        im.resize((im.width * 3, im.height * 3), Image.NEAREST).save(os.path.join(d, os.path.basename(path)))


def step_check(sel):
    for x in sel:
        s, p = x["style"], x["pair"]
        w, i, _ = CARRIER[(s, p)]
        S = Offsetter(FONTS[s], PX, s == "roman")
        hs = {hashlib.md5(S.render(w, i, u / UPP, 400).tobytes()).hexdigest() for u in range(-40, 41, 10)}
        print(f"{s} {p}: 10-unit ladder -40..+40 -> {len(hs)} distinct images of 9")


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--step-check", action="store_true")
    args = ap.parse_args()
    sel = json.load(open(os.path.join(SCRATCH, "selection.json")))["top5"]
    if args.step_check:
        return step_check(sel)
    import b2_fit
    root = os.path.join(SCRATCH, "stimuli"); os.makedirs(root, exist_ok=True)
    rng = random.Random(20260926)
    key = dict(px=PX, units_per_px=UPP, rungs_px=RUNGS, pairs=[], afc=[])
    afc_trials = []
    for n, x in enumerate(sel, 1):
        s, p = x["style"], x["pair"]
        w, i, phrase = CARRIER[(s, p)]
        S = Offsetter(FONTS[s], PX, s == "roman")
        W = {v: S.render(t, 0, 0).shape[1] + 5 * PX for v, t in (("word", w), ("phrase", phrase))}
        at = {"word": i, "phrase": phrase.index(w) + i}
        pk = dict(n=n, style=s, pair=p, word=w, phrase=phrase, his=x["his"],
                  readings=x["readings"], ladder={})
        d = os.path.join(root, f"pair{n}"); os.makedirs(d, exist_ok=True)
        for v, text in (("word", w), ("phrase", phrase)):
            perm = RUNGS[:]; rng.shuffle(perm)
            mp, seen = {}, set()
            for L, k in zip(LETTERS, perm):
                cov = S.render(text, at[v], float(k), W[v])
                seen.add(hashlib.md5(cov.tobytes()).hexdigest())
                save(with_label(cov, L), os.path.join(d, f"{v}_{L}.png"))
                mp[L] = dict(px=k, units=round(k * UPP, 1))
            assert len(seen) == len(RUNGS), f"{s} {p} {v}: duplicate rungs"
            pk["ladder"][v] = mp
        # 2AFC arms (units on the 09-20 zero)
        w0, w5 = b2_fit.white_fn(FONTS[s]), b2_fit.white_fn(R395[s])
        arms = {"his": x["his"], "zero": 0.0, "B2-held": x["b2_held"],
                "r395": float(w5(p[0], p[1]) - w0(p[0], p[1]))}
        pk["afc_arms_units"] = arms
        pk["afc_arms_px"] = {a: int(round(u / UPP)) for a, u in arms.items()}
        for other in ("zero", "B2-held", "r395"):
            for top_is_his in (True, False):
                afc_trials.append(dict(pair_n=n, style=s, pair=p, text=phrase, at=at["phrase"],
                                       other=other, top="his" if top_is_his else other,
                                       bottom=other if top_is_his else "his",
                                       top_px=pk["afc_arms_px"]["his" if top_is_his else other],
                                       bottom_px=pk["afc_arms_px"][other if top_is_his else "his"]))
        key["pairs"].append(pk)
    rng.shuffle(afc_trials)
    d = os.path.join(root, "afc"); os.makedirs(d, exist_ok=True)
    for t_n, t in enumerate(afc_trials, 1):
        S = Offsetter(FONTS[t["style"]], PX, t["style"] == "roman")
        Wd = S.render(t["text"], 0, 0).shape[1] + 5 * PX
        a = with_label(S.render(t["text"], t["at"], float(t["top_px"]), Wd), "1")
        b = with_label(S.render(t["text"], t["at"], float(t["bottom_px"]), Wd), "2")
        im = Image.new("L", (a.width, a.height + b.height + 12), 255)
        im.paste(a, (0, 0)); im.paste(b, (0, a.height + 12))
        ImageDraw.Draw(im).line([(0, a.height + 6), (im.width, a.height + 6)], fill=200)
        save(im, os.path.join(d, f"trial{t_n:02d}.png"))
        t["trial"] = t_n
        t["identical"] = t["top_px"] == t["bottom_px"]
    key["afc"] = afc_trials
    json.dump(key, open(os.path.join(SCRATCH, "key.json"), "w"), indent=1)
    print(f"wrote {root}; key {os.path.join(SCRATCH, 'key.json')}")
    for pk in key["pairs"]:
        print(pk["n"], pk["style"], pk["pair"], "his", pk["his"], "arms px", pk["afc_arms_px"])


if __name__ == "__main__":
    main()
