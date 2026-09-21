"""Every letter pair the owner's own books actually contain, counted, with the most
common real word carrying each one.

The corpus is `outlines.cmp.corpus`'s -- the epubs under ~/src/claude-tools,
the reader's real-world books -- so "common" is measured here and not guessed
from an English frequency table written for someone else's prose.
"""
import os, re, sys, glob, zipfile, collections, json
from outlines.cmp.corpus import ROOT, TEXTY

WORD = re.compile(r"[A-Za-z][A-Za-z'’]*[A-Za-z.,;:!?]?|[A-Za-z]")

def harvest():
    words = collections.Counter()
    books = sorted(glob.glob(f"{ROOT}/*/epub/*.epub"))
    for b in books:
        try: z = zipfile.ZipFile(b)
        except Exception: continue
        for n in z.namelist():
            if not n.lower().endswith(TEXTY): continue
            try: t = z.read(n).decode("utf-8", "ignore")
            except Exception: continue
            t = re.sub(r"<[^>]+>", " ", t)
            t = t.replace("&#8217;", "'").replace("&rsquo;", "'").replace("’", "'")
            for w in WORD.findall(t):
                words[w] += 1
    return words, books

def pairs_from(words):
    pair = collections.Counter()
    carrier = {}                      # pair -> {word: count}
    for w, n in words.items():
        for i in range(len(w) - 1):
            a, b = w[i], w[i+1]
            if not (a.isalpha() or a in ".,;:!?'") : continue
            key = (a, b)
            pair[key] += n
            carrier.setdefault(key, collections.Counter())[w] += n
    return pair, carrier

if __name__ == "__main__":
    words, books = harvest()
    pair, carrier = pairs_from(words)
    total = sum(pair.values())
    print(f"{len(books)} books, {sum(words.values()):,} words, {len(pair):,} distinct pairs, {total:,} pair instances")
    json.dump({"pairs": [[f"{a}{b}", n] for (a, b), n in pair.most_common()],
               "carriers": {f"{a}{b}": carrier[(a,b)].most_common(8) for (a,b) in pair}},
              open(os.environ.get("ALBO_PAIR_OUT", "bigrams.json"), "w"))
    for (a,b), n in pair.most_common(30):
        print(f"  {a}{b}  {n:>8,}   {carrier[(a,b)].most_common(1)[0][0]}")

# Measured 2026-09-20: 36 books, 508,518 words, 1,486 distinct pairs,
# 2,007,794 pair instances. The top 50 pairs are half of all of them and the
# top 250 are 91%; pairs carrying a CAPITAL are 3.9% of instances and pairs
# carrying a MARK 4.2%. That is the shape that decides how many rows a
# spacing bench is worth building: the lowercase is where the reading is.
