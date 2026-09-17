"""A proof made of the words and letter-pairs the owner's books actually contain.

Owner 2026-09-17: *"give me a proof for the top words together that show all the
top combinations"*.

A pangram proves a font has 26 letters. It proves nothing about a TEXT FACE,
because what a reader meets is not letters but PAIRS -- the join, the space
between, the rhythm of one letter's exit against the next one's entry. So this
proof is built from the corpus rather than composed:

  * the top WORDS, straight off the frequency list, set as running text;
  * a COVERING SET -- the shortest list of common words that between them
    contain every one of the top N letter pairs, chosen greedily and biased
    toward frequent words, so nothing in the proof is a word nobody reads;
  * a CO-OCCURRENCE row -- words that carry several top pairs at once, which is
    where a fault compounds.

The corpus is the same one `outlines/cmp/corpus.py` uses for coverage: every
epub under ~/src/claude-tools, which the global CLAUDE.md names as the reader's
real-world corpus. 512,344 word tokens, 1,910,349 letter pairs.

WHY BIGRAMS AND NOT TRIGRAMS. The top 40 bigrams are 48% of every adjacent pair
a reader meets. Trigrams scatter: the top 40 are under 20%, so a trigram proof
spends most of its page on rare shapes.

    PYTHON_GIL=0 python3 proof_words.py <font.ttf> --out proof.png
    PYTHON_GIL=0 python3 proof_words.py <ttf> --pairs 60 --report
"""
import argparse, collections, glob, json, os, re, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("ALBO_CORPUS", os.path.expanduser("~/src/claude-tools"))
TEXTY = (".xhtml", ".html", ".htm")
TAG = re.compile(r"<[^>]+>")
CACHE = os.path.join(HERE, ".corpus_words.json")


def corpus(rebuild=False):
    """word -> count over every epub under ROOT. Cached: the scan is ~30 s."""
    if not rebuild and os.path.exists(CACHE):
        return collections.Counter(json.load(open(CACHE)))
    words = collections.Counter()
    for b in sorted(glob.glob(os.path.join(ROOT, "*", "epub", "*.epub"))):
        try: z = zipfile.ZipFile(b)
        except Exception: continue
        for n in z.namelist():
            if not n.lower().endswith(TEXTY): continue
            try: t = z.read(n).decode("utf-8", "ignore")
            except Exception: continue
            for w in re.findall(r"[a-zA-Z]+", TAG.sub(" ", t)):
                words[w.lower()] += 1
    json.dump(words, open(CACHE, "w"))
    return words


def bigrams(words):
    b = collections.Counter()
    for w, c in words.items():
        for i in range(len(w) - 1):
            b[w[i:i + 2]] += c
    return b


ENGLISH = "/usr/share/dict/words"


def english():
    """The system word list, lowercased. The corpus is the owner's whole epub
    library and that library includes a SPANISH project, so an unfiltered
    greedy cover reaches for `nosotros` and `toma` -- real words, genuinely in
    his books, and wrong for a proof whose standing brief is English word
    images. Absent the list, nothing is filtered and the proof says so."""
    try:
        return {w.strip().lower() for w in open(ENGLISH) if w.strip().isalpha()}
    except Exception:
        return None


def cover(words, pairs, pool=3000, maxlen=9):
    """The shortest list of COMMON words containing every pair in `pairs`.

    Greedy set cover, and the greed is deliberately biased: among words that
    cover the same number of remaining pairs it takes the most FREQUENT one, so
    the proof reads as English rather than as a word-list. A pair no common word
    carries is reported rather than dropped -- a proof that silently omits what
    it claims to cover is worse than a short one.
    """
    en = english()
    common = [w for w, _ in words.most_common(pool)
              if 2 <= len(w) <= maxlen and (en is None or w in en)]
    rank = {w: i for i, (w, _) in enumerate(words.most_common(pool))}
    need = set(pairs); out = []
    while need:
        best, gain = None, 0
        for w in common:
            g = len({w[i:i + 2] for i in range(len(w) - 1)} & need)
            if g > gain or (g == gain and g and rank.get(w, 1e9) < rank.get(best, 1e9)):
                best, gain = w, g
        if not best or not gain:
            break
        out.append(best)
        need -= {best[i:i + 2] for i in range(len(best) - 1)}
    return out, need


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ttf")
    ap.add_argument("--out", default="proof_words.png")
    ap.add_argument("--pairs", type=int, default=60)
    ap.add_argument("--words", type=int, default=48)
    ap.add_argument("--rebuild", action="store_true")
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()

    W = corpus(a.rebuild); B = bigrams(W)
    bt = sum(B.values()); wt = sum(W.values())
    top = [p for p, _ in B.most_common(a.pairs)]
    share = 100.0 * sum(B[p] for p in top) / bt
    cov, missed = cover(W, top)
    _en = english()
    topw = [w for w, _ in W.most_common(a.words * 3)
            if _en is None or w in _en][:a.words]

    # words carrying the most top pairs at once -- where a fault compounds
    en = english()
    dense = sorted(((len({w[i:i+2] for i in range(len(w)-1)} & set(top)), W[w], w)
                    for w, _ in W.most_common(2500)
                    if 4 <= len(w) <= 10 and (en is None or w in en)),
                   reverse=True)[:14]

    print(f"\n  corpus: {wt:,} word tokens, {bt:,} letter pairs, {len(W):,} types")
    print(f"  the top {a.pairs} pairs are {share:.1f}% of every adjacent pair a reader meets")
    print(f"  english filter: {'ON' if english() else 'OFF (no word list)'}")
    print(f"  {len(cov)} common words cover {len(top)-len(missed)} of them"
          + (f"; NOT covered by any common word: {' '.join(sorted(missed))}" if missed else ""))
    if a.report:
        print("\n  top pairs :", " ".join(top))
        print("  cover     :", " ".join(cov))
        print("  densest   :", " ".join(f"{w}({n})" for n, _, w in dense))

    from proof import Proof
    from PIL import ImageFont
    PAGE = 2000

    def rows(pr, text, px, gap=6):
        """Add `text` at `px`, WRAPPED to the page. `proof.Proof` has no
        wrapping -- every other proof in this project is one short line per row
        -- and an unwrapped row is silently CLIPPED at the page edge, which on
        a proof whose whole claim is 'every one of the top 60 pairs is here'
        would be a lie told by the renderer."""
        f = ImageFont.truetype(a.ttf, px)
        words_, line = text.split(), ""
        for w in words_:
            t = (line + " " + w).strip()
            if f.getlength(t) > PAGE - 2 * 30 and line:
                pr.row(line, px); pr.gap(gap); line = w
            else:
                line = t
        if line: pr.row(line, px); pr.gap(gap)

    pr = Proof(a.ttf, width=PAGE, pad=30)
    pr.label("THE TOP WORDS  —  the %d commonest in the corpus, in order" % a.words)
    for px, n in ((54, 16), (34, 32), (22, a.words)):
        rows(pr, " ".join(topw[:n]), px)
    pr.gap(16)
    pr.label("EVERY ONE OF THE TOP %d LETTER PAIRS  —  %.0f%% of all pairs, in %d common words"
             % (a.pairs, share, len(cov)))
    for px in (54, 34, 22):
        rows(pr, " ".join(cov), px)
    pr.gap(16)
    pr.label("THE DENSEST WORDS  —  most top-pairs in one word, where a fault compounds")
    rows(pr, " ".join(w for _, _, w in dense), 44)
    rows(pr, " ".join(w for _, _, w in dense), 26)
    pr.gap(16)
    pr.label("RUNNING TEXT  —  the top words as continuous prose")
    body = " ".join(topw[:a.words] + cov)
    for px in (28, 20, 15):
        rows(pr, body, px)
    pr.save(a.out)
    print("  wrote", a.out, "\n")


if __name__ == "__main__":
    main()
