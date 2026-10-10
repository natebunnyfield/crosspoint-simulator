#!/usr/bin/env python3
"""What drives the common words' unevenness -- the decomposition, from a word_measure.py JSON.

The objective (docs/albo-word-image-drivers-2026-10-09.md): a word reads as one image when its
letters carry one color. For each of the 100 commonest word images in his books this prints

  * the TOP-100 GAP: the token-weighted mean of (Albo's unevenness - the references' median
    unevenness), where a word's unevenness is the spread of its letters' slot darkness over the
    word's own (word_measure.word_evenness); lower is better, 0 = the references;
  * WORSE: how many of the 100 are less even in Albo than in EVERY reference, and the share of
    tokens those words carry;
  * per LETTER: Albo's slot darkness minus the references' median for the SAME slot of the SAME
    word, token-weighted over every slot the letter occupies in the top 100, and that letter's
    SHARE of the total absolute deviation. The share says which letters to draw; a letter under
    ~5% is not where the word image is.

Usage:  word_drivers.py MEASURE.json [--cut Regular] [--top 100] [--letters 12] [--md]
        word_drivers.py A.json B.json ... --compare   (one gap/worse row per file, both cuts)

The same arithmetic produced the 2026-10-09 tables by hand; this is the instrument so the next
decomposition is a command rather than a reconstruction.
"""
import argparse, json, os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from word_measure import word_evenness, CUTS, LABEL  # noqa: E402


def top_words(M, n):
    wl = M["_words"]["lower"] + M["_words"]["title"]
    return sorted(wl, key=lambda x: -x[1])[:n]


def gap(M, cut, top):
    rows = word_evenness(M, cut, top)
    tot = sum(r["count"] for r in rows)
    g = sum(r["excess"] * r["count"] for r in rows) / max(tot, 1)
    worse = [r for r in rows if r["albo"] > r["hi"]]
    return g, len(worse), sum(r["count"] for r in worse) / max(tot, 1), rows


def letters(M, cut, top):
    A = M["Albo/" + cut]["per_word"]
    refs = [k for k in M if k.endswith("/" + cut) and not k.startswith("Albo/") and "per_word" in M[k]]
    dev, tok = {}, {}
    for w, n in top:
        if w not in A:
            continue
        sizes = [sz for sz in A[w] if all(w in M[r]["per_word"] and sz in M[r]["per_word"][w] for r in refs)]
        for idx, (cl, _) in enumerate(A[w][sizes[0]]):
            ch = w[cl]
            av = np.mean([A[w][sz][idx][1] for sz in sizes if len(A[w][sz]) > idx])
            rv = [np.mean([M[r]["per_word"][w][sz][idx][1] for sz in sizes if len(M[r]["per_word"][w][sz]) > idx])
                  for r in refs if len(M[r]["per_word"][w][sizes[0]]) > idx]
            if not rv:
                continue
            d = float(av - np.median(rv))
            dev[ch] = dev.get(ch, 0.0) + d * n
            tok[ch] = tok.get(ch, 0) + n
    total = sum(abs(v) for v in dev.values())
    out = [(ch, dev[ch] / tok[ch], tok[ch], abs(dev[ch]) / total) for ch in dev]
    return sorted(out, key=lambda r: -r[3])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("json", nargs="+")
    ap.add_argument("--cut", default=None)
    ap.add_argument("--top", type=int, default=100)
    ap.add_argument("--letters", type=int, default=12)
    ap.add_argument("--md", action="store_true")
    ap.add_argument("--compare", action="store_true")
    a = ap.parse_args()
    cuts = [a.cut] if a.cut else ["Regular", "Bold"]
    if a.compare:
        print("| file | " + " | ".join(f"{LABEL[c]} gap | {LABEL[c]} worse (tokens) " for c in cuts) + "|")
        print("|---|" + "---|---|" * len(cuts))
        for p in a.json:
            M = json.load(open(p))
            cells = []
            for c in cuts:
                g, w, ws, _ = gap(M, c, top_words(M, a.top))
                cells.append(f"{g:+.4f} | {w} ({ws:.0%})")
            print(f"| {os.path.basename(p)} | " + " | ".join(cells) + " |")
        return
    for p in a.json:
        M = json.load(open(p))
        top = top_words(M, a.top)
        for c in cuts:
            g, w, ws, rows = gap(M, c, top)
            print(f"\n{os.path.basename(p)} {c} ({LABEL[c]}): top-{a.top} gap {g:+.4f}; {w} words less even than every "
                  f"reference ({ws:.0%} of tokens); median unevenness Albo "
                  f"{np.median([r['albo'] for r in rows]):.3f} refs {np.median([r['refs'] for r in rows]):.3f}")
            L = letters(M, c, top)[: a.letters]
            if a.md:
                print("\n| letter | vs references | tokens | share of the deviation |\n|---|---|---|---|")
                for ch, d, t, s in L:
                    print(f"| {ch} | {d:+.1%} | {t:,} | {s:.1%} |")
            else:
                for ch, d, t, s in L:
                    print(f"  {ch}  {d:+6.1%}  {t:7,}  share {s:5.1%}")


if __name__ == "__main__":
    main()
