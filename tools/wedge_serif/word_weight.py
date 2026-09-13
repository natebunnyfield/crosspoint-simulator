#!/usr/bin/env python3
"""Visual weight of the most common English words (the owner's list of 147), set in a TTF at
reading size (13 pt on a 2x reader = 54 px em).

    python3 word_weight.py <font.ttf> [--px 54] [--json out.json] [--quiet]

Per WORD: darkness = ink coverage (antialiased gray, summed) over the box
advance width x (ascender..descender band), i.e. the mean ink fraction of
the rectangle the word occupies on the line. Per LETTER: the same for the
letter alone (its own advance), plus ink per advance (mean ink height in
px, a spacing-independent weight), count across the list, share of the
list's ink, and a "drive" score: the sum over the words it appears in of
(own darkness - lowercase median) x (its advance / the word's advance),
i.e. how much of the words' deviation from the median it is responsible
for. Stem and hairline widths are measured on a 1000 px raster: stems as
horizontal ink runs at mid x-height, hairlines as the vertical runs of a
bowl at its center column (top and bottom), reported in font units.
"""
import argparse, json, statistics, sys
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont

WORDS = ("the of and to in a is that for it as was with be by on not he i this are or his from at "
         "which but have an had they you were their one all we can her has there been if more when "
         "will would who so no she what up their its about into than them only other new some could "
         "time these two may then do first any my now such like our over man me even most made after "
         "also did many before must through back years where much your way well down should because "
         "each just those people mr how too little state good very make world still own see men work "
         "long get here between both life being under never day same another know while last might "
         "us great old year off come since against go came right used take three").split()
# the list as given by the owner is 148 tokens ("their" twice); deduplicated, order kept
WORDS = list(dict.fromkeys(WORDS))
LETTERS = "abcdefghijklmnopqrstuvwxyz"

def render(font, text, px):
    asc, desc = font.getmetrics()
    adv = font.getlength(text)
    W = max(1, int(round(adv))); H = asc + desc
    im = Image.new("L", (W + 8, H), 255)
    ImageDraw.Draw(im).text((0, asc), text, font=font, fill=0, anchor="ls")
    return im, adv, H

def ink(im):
    return sum(255 - v for v in im.getdata()) / 255.0

def measure_word(font, text, px):
    im, adv, H = render(font, text, px)
    k = ink(im)
    return dict(ink=k, adv=adv, band=H, dark=k / (adv * H) if adv > 0 else 0.0)

def runs(row, thresh=128):
    """(start, length) of ink runs in a 1-D sequence of gray values."""
    out, start = [], None
    for i, v in enumerate(row):
        if v < thresh and start is None: start = i
        elif v >= thresh and start is not None: out.append((start, i - start)); start = None
    if start is not None: out.append((start, len(row) - start))
    return out

def strokes(path, ch, big=1000):
    """Stem (widest horizontal run at 0.40 x-height) and, for bowl letters,
    the hairline (vertical run at the bowl's center column, top & bottom),
    in font units (upm 1000 == big px)."""
    tt = TTFont(path); upm = tt["head"].unitsPerEm; xh = tt["OS/2"].sxHeight
    font = ImageFont.truetype(path, big)
    asc, desc = font.getmetrics()
    im, adv, H = render(font, ch, big)
    W = im.size[0]
    y = asc - int(xh * 0.40 * big / upm)   # above the foot brackets (139 u), below the arch joins (0.52 xh) and the e bar
    row = [im.getpixel((x, y)) for x in range(W)]
    hr = runs(row)
    stem = max((L for _, L in hr), default=0) * upm / big
    thin = min((L for _, L in hr), default=0) * upm / big
    hair = None
    if ch in "obdpqceag":   # bowls: column through the bowl center
        # bowl center: middle of the widest horizontal ink extent at mid x-height, excluding the stem run
        if len(hr) >= 2:
            l = hr[0][0]; r = hr[-1][0] + hr[-1][1]
            cx = (l + r) // 2
            col = [im.getpixel((cx, yy)) for yy in range(H)]
            vr = [(s, L) for s, L in runs(col)]
            # keep runs inside the x-height band (+ overshoot)
            band = [(s, L) for s, L in vr if s < asc + 0.05 * big and s + L > asc - (xh + 40) * big / upm]
            if band:
                hair = dict(top=band[0][1] * upm / big, bottom=band[-1][1] * upm / big)
    return dict(stem=stem, thin=thin, hair=hair, runs=len(hr))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("font"); ap.add_argument("--px", type=int, default=54)
    ap.add_argument("--json"); ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--ref", help="a reference TTF (EB Garamond, Hoefler Text): each letter's darkness "
                    "relative to its own lowercase median, so the letter's INHERENT ink (an l has an "
                    "ascender, an r has an arm over air) is separated from what this design adds")
    ap.add_argument("--ref-index", type=int, default=0)
    a = ap.parse_args()
    font = ImageFont.truetype(a.font, a.px)
    words = {w: measure_word(font, w, a.px) for w in WORDS}
    letters = {ch: measure_word(font, ch, a.px) for ch in LETTERS}
    for ch in LETTERS:
        letters[ch]["ink_per_adv"] = letters[ch]["ink"] / letters[ch]["adv"]
        letters[ch]["count"] = sum(w.count(ch) for w in WORDS)
        letters[ch].update(strokes(a.font, ch))
    med = statistics.median(letters[ch]["dark"] for ch in LETTERS)
    total_ink = sum(letters[ch]["ink"] * letters[ch]["count"] for ch in LETTERS)
    for ch in LETTERS:
        L = letters[ch]; L["share"] = L["ink"] * L["count"] / total_ink
        L["drive"] = sum((L["dark"] - med) * (L["adv"] / words[w]["adv"]) for w in WORDS for _ in range(w.count(ch)))
        L["dev_pct"] = (L["dark"] / med - 1) * 100
    word_med = statistics.median(v["dark"] for v in words.values())
    if a.ref:
        rf = ImageFont.truetype(a.ref, a.px, index=a.ref_index)
        rl = {ch: measure_word(rf, ch, a.px) for ch in LETTERS}
        rmed = statistics.median(rl[ch]["dark"] for ch in LETTERS)
        rw = {w: measure_word(rf, w, a.px) for w in WORDS}
        rwmed = statistics.median(v["dark"] for v in rw.values())
        for ch in LETTERS:
            letters[ch]["ref_rel"] = rl[ch]["dark"] / rmed
            letters[ch]["vs_ref_pct"] = ((letters[ch]["dark"] / med) / (rl[ch]["dark"] / rmed) - 1) * 100
        for w in WORDS:
            words[w]["ref_rel"] = rw[w]["dark"] / rwmed
            words[w]["vs_ref_pct"] = ((words[w]["dark"] / word_med) / (rw[w]["dark"] / rwmed) - 1) * 100
    out = dict(font=a.font, px=a.px, lc_median=med, word_median=word_med, words=words, letters=letters)
    if a.json: json.dump(out, open(a.json, "w"), indent=1)
    if a.quiet: return
    order = sorted(WORDS, key=lambda w: words[w]["dark"])
    print(f"font {a.font}  em {a.px}px  lowercase median darkness {med:.4f}  word median {word_med:.4f}")
    print("\nDARKEST 10 words           dark    adv   ink")
    for w in order[::-1][:10]: v = words[w]; print(f"  {w:10s} {v['dark']:.4f}  {v['adv']:6.1f} {v['ink']:7.1f}")
    print("LIGHTEST 10 words          dark    adv   ink")
    for w in order[:10]: v = words[w]; print(f"  {w:10s} {v['dark']:.4f}  {v['adv']:6.1f} {v['ink']:7.1f}")
    print("\nLETTERS  dark   dev%  ink/adv  adv   n   share  drive   stem  thin  hair(top/bot)" + ("  refrel  vsref%" if a.ref else ""))
    for ch in sorted(LETTERS, key=lambda c: -letters[c]["dark"]):
        L = letters[ch]; h = L["hair"]
        hs = f"{h['top']:4.0f}/{h['bottom']:4.0f}" if h else "   -   "
        extra = f"   {L['ref_rel']:5.2f}  {L['vs_ref_pct']:+6.1f}" if a.ref else ""
        print(f"  {ch}   {L['dark']:.4f} {L['dev_pct']:+6.1f}  {L['ink_per_adv']:5.2f}  {L['adv']:5.1f} {L['count']:3d}  {L['share']*100:5.2f}  {L['drive']:+6.3f}  {L['stem']:4.0f}  {L['thin']:4.0f}  {hs}{extra}")
    if a.ref:
        print("\nWORDS most OVER the reference's relative darkness (this design darkens them)   and most UNDER")
        o = sorted(WORDS, key=lambda w: -words[w]["vs_ref_pct"])
        for w1, w2 in zip(o[:12], o[::-1][:12]):
            print(f"  {w1:10s} {words[w1]['vs_ref_pct']:+6.1f}%      {w2:10s} {words[w2]['vs_ref_pct']:+6.1f}%")

if __name__ == "__main__":
    main()
