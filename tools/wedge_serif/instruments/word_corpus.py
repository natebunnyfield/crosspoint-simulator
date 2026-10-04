#!/usr/bin/env python3
"""word_corpus.py -- which WORD IMAGES the owner's books ask Albo for, in which cut, and which of
them have had the least attention (docs/albo-word-images-2026-10-04.md).

WHAT IT MEASURES

1. WORD FREQUENCY, per cut, over the owner's own epubs -- the corpus `pair_census.py` and
   `outlines.cmp.corpus` read (`ROOT/*/epub/*.epub`, ROOT = ~/src/claude-tools; `ALBO_CORPUS`
   moves it). The unit is the SURFACE FORM, case kept: "The" and "the" are two different word
   images, and only one of them starts with a capital T. Text extraction follows
   `instruments/stroke_colors.py` (content documents only, <head> <style> <script> dropped, entities
   decoded, a word is a run of letters that may hold an inner apostrophe), with one addition: each
   word carries the cut the reader sets it in, from the tags around it --
     R  plain text
     I  inside <em> <i> <cite> <dfn> <var>
     B  inside <strong> <b> <h1>..<h6> <th> <dt>
     Z  inside both.
   CSS-class styling (.deck, blockquote, .scenario ...) is NOT followed, only tags; that text is
   counted as R. Two corpora: ALL, the 41 files exactly as the existing tools read them, and
   UNIQUE, with the 19 cascade re-flows (same text, other line breaks) and the 3 superseded files
   dropped (SUPERSEDED below). Every count in the doc is ALL unless it says UNIQUE.

2. ATTENTION PER GLYPH: how many Albo commit subjects (git log over tools/wedge_serif and the Albo
   docs) and round headings in docs/wedge-serif-exploration.md name the glyph as the thing being
   worked on. A mention is "the [cut] X", "<cut> X", or a run of single letters
   ("h m n r u i l", "B P R", "i/j"). A quoted single letter is NOT a mention: in this repo it is
   almost always the owner's option pick ("d", "b wins"). A mention that follows a comparison word
   ("as thick as the o", "match the i's dot", "on the n shoulder") names a REFERENCE, not a
   target, and is not counted. A FAMILY round whose subject names no letters (the arches, the
   seventeen word-image adjustments, the thick/thin passes) credits the letters its record names
   (FAMILY_ROUNDS). Pooled over the four cuts; accented letters take their base letter's count.
   Every count of 8 or less was read by hand; the exceptions found are REF_WORDS, NOT_TARGET and
   EXTRA_TARGET below; `--show X` prints every subject counted for X.

3. ATTENTION PER PAIR: whether the owner judged the pair's spacing on any bench -- shown on the
   2026-09-20 bench (bench/bench-items-2026-09-20.json, all 396 rows) or read in any later session
   (bench/answers/extra-judgments.json, by style). Roman covers R and B, italic covers I and Z
   (the bolds were never benched; their spacing is the 400s' transferred).

4. THE NEGLECT INDEX of a word: the share of its letters whose glyph attention is in the bottom
   third of its case (lowercase or capitals), plus its letter pairs that were never benched, over
   (letters + pairs). A word whose every letter and pair was never looked at scores 1.0.

    $VENV instruments/word_corpus.py --out DIR            # writes DIR/corpus.json, prints the tables
    $VENV instruments/word_corpus.py --out DIR --show hnu # every commit subject counted for h, n, u
"""
import argparse, collections, glob, html, json, os, re, subprocess, sys, zipfile
from html.parser import HTMLParser

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.dirname(HERE)
REPO = os.path.dirname(os.path.dirname(WS))
sys.path.insert(0, WS)
from outlines.cmp.corpus import ROOT  # noqa: E402  (the census's corpus root)

WORD_RE = re.compile(r"[^\W\d_]+(?:['’][^\W\d_]+)*")
ITAL = {"em", "i", "cite", "dfn", "var"}
BOLD = {"strong", "b", "h1", "h2", "h3", "h4", "h5", "h6", "th", "dt"}
SKIP = {"head", "style", "script", "title"}
VOID = {"br", "img", "hr", "meta", "link", "input", "col", "area", "base", "wbr", "source", "track",
        "param", "embed"}
BLOCK = {"p", "div", "li", "ul", "ol", "h1", "h2", "h3", "h4", "h5", "h6", "br", "td", "th", "tr",
         "dt", "dd", "dl", "blockquote", "section", "article", "table", "pre", "hr", "header",
         "footer", "nav", "aside", "figure", "figcaption", "body", "html"}
CUTS = "RIBZ"
# Same text as a file kept: an older export of a book that has a newer one beside it.
SUPERSEDED = {"eighth-atlas-2026-09-15.epub",   # byte-identical in size to eighth-atlas.epub
              "tico-spanish-sealed-v1.epub",    # 2026-09-05; tico-spanish-sealed.epub is 09-12
              "trivia-aimed-v2.epub"}           # 2026-09-15; trivia-aimed.epub is 09-30


class _Text(HTMLParser):
    """Text of one content document with a cut code per character."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.parts, self.codes = [], [], []

    def _gap(self):
        self.parts.append(" "); self.codes.append("R")

    def handle_starttag(self, tag, attrs):
        if tag in BLOCK:
            self._gap()
        if tag not in VOID:
            self.stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        if tag in BLOCK:
            self._gap()

    def handle_endtag(self, tag):
        if tag in BLOCK:
            self._gap()
        if tag in self.stack:
            while self.stack and self.stack.pop() != tag:
                pass

    def handle_data(self, data):
        if any(t in SKIP for t in self.stack):
            return
        it = any(t in ITAL for t in self.stack)
        bd = any(t in BOLD for t in self.stack)
        c = "Z" if it and bd else "I" if it else "B" if bd else "R"
        self.parts.append(data); self.codes.append(c * len(data))


def doc_words(t):
    p = _Text()
    try:
        p.feed(t); p.close()
    except Exception:                       # a malformed file: fall back to the tag regex, all R
        t2 = html.unescape(re.sub(r"<[^>]+>", " ", re.sub(r"<(head|style|script)\b.*?</\1\s*>", " ", t, flags=re.S | re.I)))
        return [(w.replace("’", "'"), "R") for w in WORD_RE.findall(t2)]
    text = "".join(p.parts); codes = "".join(p.codes)
    return [(m.group(0).replace("’", "'"), codes[m.start()]) for m in WORD_RE.finditer(text)]


def harvest(root=ROOT):
    """{book: Counter((form, cut))} over every epub the census reads."""
    books = sorted(glob.glob(os.path.join(root, "*", "epub", "*.epub")))
    out = {}
    for b in books:
        cnt = collections.Counter()
        try:
            z = zipfile.ZipFile(b)
        except Exception:
            continue
        for n in z.namelist():
            if not n.lower().endswith((".xhtml", ".html", ".htm")):
                continue
            t = z.read(n).decode("utf-8", "ignore")
            for w, c in doc_words(t):
                cnt[(w, c)] += 1
        out[os.path.basename(b)] = cnt
    return out


def unique_books(names):
    return [n for n in names if "-cascade" not in n and n not in SUPERSEDED]


# ------------------------------------------------------------------ attention per glyph
CUTW = r"(?:Regular|Italic|Bold Italic|BoldItalic|Bold|roman|italic|bold italic|bold|upright|BI)"
P_THE = re.compile(r"\bthe\s+(?:(" + CUTW + r")\s+)?(?:(?:capital|lowercase|letter|glyph)\s+)?([A-Za-z])(?=['’]s\b|[\s,;:.)\]/]|$)")
P_CUT = re.compile(r"\b(" + CUTW + r")\s+([A-Za-z])(?=['’]s\b|[\s,;:.)\]/]|$)")
P_LIST = re.compile(r"(?<![\w'’])([A-Za-z])((?:\s*(?:,|/|\band\b|\s)\s*[A-Za-z](?![\w'’]))+)")
# a mention right after one of these names the letter something else is MEASURED AGAINST
REF_WORDS = re.compile(r"\b(?:as|like|than|to|onto|under|against|after|match(?:es|ed|ing)?|takes?|took|"
                       r"from|beside|vs\.?|into|via|at|by|shoulder of|on)\s+(?:(?:the|its|a|an|" + CUTW +
                       r")\s+){0,2}$", re.I)
# Hand-checked: (commit hash prefix, glyph) pairs the rules get wrong. NOT_TARGET drops a counted
# mention; EXTRA_TARGET adds one the rules drop. Each was read in full.
NOT_TARGET = {("b29c30b", "l"),                       # "the b stops short of the l"
              ("97d5a32", "b"), ("97d5a32", "h"),     # "f before b h k l +54" -- the f's spacing
              ("97d5a32", "k"), ("97d5a32", "l"),
              ("cf2643c", "d"), ("cf2643c", "h"),     # "the 6 as i (d's blunt cut on h's short tail)"
              ("d1ac018", "b"),                       # the ampersand "d's body under b's open top"
              ("5c18d36", "b"),                       # "the roman a ships as option b" -- a label
              ("2e12e80", "d"), ("4a444cc", "d"),     # the italic a takes "the d's tail"
              ("764eb75", "d"), ("322bf87", "d"),     # "the a is the d's bowl" / "a d with a short ascender"
              ("2b4e8ce", "i"),                       # fi ligature: "bar short of the i"
              ("2ea3ea7", "r"), ("2ea3ea7", "a"), ("2ea3ea7", "m"),   # a SPACING bench, not a drawing
              ("3c7a0b7", "O"),                       # "the italic S's and G's reach past the O"
              ("d881886", "A"),                       # "within 3% of the A's strokes"
              ("907eca1", "I")}                       # "the L's top is the I's two-sided top"
EXTRA_TARGET = {("cd34545", "y"),   # "owner rulings on the roman y"
                ("2e16c97", "p"),   # "six variations on the italic p"
                ("43b47a0", "e")}   # "one pass on the e"
# FAMILY ROUNDS whose subject names a family or the whole face, not letters. The letters each one
# moved are the ones its round record names (docs/wedge-serif-exploration.md rounds 27-30, 92, 93,
# 108; docs/albo-fit-audit-2026-09-26.md section 2b for 391 and 395, measured with cmp_outlines;
# docs/albo-poor-characters-2026-09-26.md section 1 for 409). Keyed by commit hash prefix or by the
# exploration log's heading.
FAMILY_ROUNDS = {
    "## Round 27 ": "nmh", "## Round 29 ": "nmh", "## Round 30 ": "nmh",      # the arches
    "## Round 92 ": "zrpnacoteklíubdwjf".replace("í", "i"),                     # the 17 word-image adjustments
    "## Round 93 ": "nmh",                                                       # n m h above the baseline
    "272874c": "bdpqce",        # round 108: bowls and open rounds sized to the o
    "80d8e74": "hmnrusty",      # round 391: italic arch hairline (h m n r u), roman floors (s t y)
    "95bf547": "bdpqasye",      # round 395: thick/thin picks (italic b d p q a s y, roman e)
    "f71dddf": "hmnruil",       # round 409: the italic resized, its stem family on a new nib
}


def subjects():
    log = subprocess.run(["git", "-C", REPO, "log", "--format=%h%x09%ad%x09%s", "--date=short", "--",
                          "tools/wedge_serif", "docs/albo-*.md", "docs/wedge-serif-exploration.md",
                          "docs/fjord-glyph-guide.md"], capture_output=True, text=True).stdout.splitlines()
    rows = [l.split("\t", 2) for l in log if l.count("\t") >= 2]
    heads = [("log", "", l.strip()) for l in open(os.path.join(REPO, "docs", "wedge-serif-exploration.md"))
             if l.startswith("## Round")]
    return rows + heads


def targets(s):
    """Glyphs a subject names as the thing worked on."""
    found = []
    for P in (P_THE, P_CUT):
        for m in P.finditer(s):
            pre = s[max(0, m.start() - 48):m.start()]
            if REF_WORDS.search(pre):
                continue
            found.append(m.group(2))
    for m in P_LIST.finditer(s):
        if REF_WORDS.search(s[max(0, m.start() - 48):m.start()]):
            continue
        toks = [m.group(1)] + re.findall(r"(?<![A-Za-z])[A-Za-z](?![A-Za-z])", m.group(2))
        if len(toks) >= 2:
            found += toks
    return list(dict.fromkeys(found))


def glyph_attention():
    att = collections.Counter(); where = collections.defaultdict(list)
    for h, d, s in subjects():
        ts = set(targets(s))
        ts |= {g for (hh, g) in EXTRA_TARGET if h.startswith(hh)}
        ts -= {g for (hh, g) in NOT_TARGET if h.startswith(hh)}
        for key, letters in FAMILY_ROUNDS.items():
            if (h != "log" and h.startswith(key)) or (h == "log" and s.startswith(key)):
                ts |= set(letters)
        for g in ts:
            att[g] += 1; where[g].append(f"{h} {d} {s}")
    return att, where


# ------------------------------------------------------------------ attention per pair
def pair_attention():
    """{style: {pair: n}} -- benched rows; roman = R, B; italic = I, Z."""
    att = {"roman": collections.Counter(), "italic": collections.Counter()}
    items = json.load(open(os.path.join(WS, "bench", "bench-items-2026-09-20.json")))["items"]
    for it in items:
        p = it["pair"].replace(" ", "")
        att["roman"][p] += 1; att["italic"][p] += 1
    for r in json.load(open(os.path.join(WS, "bench", "answers", "extra-judgments.json")))["rows"]:
        if r["style"] in att:
            att[r["style"]][r["pair"]] += 1
    return att


STYLE_OF = {"R": "roman", "B": "roman", "I": "italic", "Z": "italic"}


def base(s):
    """An accented letter as its base letter: é -> e (attention and pairs are the base's)."""
    import unicodedata
    return "".join(unicodedata.normalize("NFD", c)[0] for c in s)


def neglect(word, cut, gatt, low, patt):
    """(share, the neglected letters, the never-benched pairs)."""
    word = base(word)
    letters = [c for c in word if c.isalpha()]
    pairs = [word[i:i + 2] for i in range(len(word) - 1) if word[i].isalpha() and word[i + 1].isalpha()]
    nl = [c for c in letters if gatt.get(c, 0) <= low["uc" if c.isupper() else "lc"]]
    st = STYLE_OF[cut]
    npairs = [p for p in pairs if patt[st].get(p, 0) == 0]
    tot = len(letters) + len(pairs)
    return ((len(nl) + len(npairs)) / tot if tot else 0.0), nl, npairs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--top", type=int, default=500, help="words considered for the neglect list")
    ap.add_argument("--show", default="", help="print every subject counted for these glyphs")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    per_book = harvest()
    names = sorted(per_book)
    uniq = unique_books(names)
    ALL = collections.Counter(); UNI = collections.Counter()
    for n in names:
        ALL.update(per_book[n])
        if n in uniq:
            UNI.update(per_book[n])
    tot_all, tot_uni = sum(ALL.values()), sum(UNI.values())
    by_cut = {c: collections.Counter() for c in CUTS}
    for (w, c), k in ALL.items():
        by_cut[c][w] += k
    forms = collections.Counter()
    for (w, c), k in ALL.items():
        forms[w] += k
    funi = collections.Counter()
    for (w, c), k in UNI.items():
        funi[w] += k

    gatt, where = glyph_attention()
    lc = sorted("abcdefghijklmnopqrstuvwxyz", key=lambda g: gatt.get(g, 0))
    uc = sorted("ABCDEFGHIJKLMNOPQRSTUVWXYZ", key=lambda g: gatt.get(g, 0))
    # bottom third: the 9th-lowest count of 26 is the ceiling
    low = {"lc": gatt.get(lc[8], 0), "uc": gatt.get(uc[8], 0)}
    patt = pair_attention()

    cut_tot = {c: sum(by_cut[c].values()) for c in CUTS}
    top_forms = [w for w, _ in forms.most_common(a.top)]
    rows = []
    for w in top_forms:
        cuts = {c: by_cut[c][w] for c in CUTS if by_cut[c][w]}
        main_cut = max(cuts, key=cuts.get)
        share, nl, npr = neglect(w, main_cut, gatt, low, patt)
        rows.append(dict(word=w, count=forms[w], unique=funi[w], cuts=cuts, main_cut=main_cut,
                         neglect=round(share, 3), neglected_letters=nl, unbenched_pairs=npr,
                         score=round(forms[w] * share, 1)))
    neglected = sorted([r for r in rows if r["neglect"] > 0], key=lambda r: (-r["neglect"], -r["count"]))
    # rank stability, ALL vs UNIQUE, over the top 100
    ra = {w: i for i, (w, _) in enumerate(forms.most_common(100))}
    ru = {w: i for i, (w, _) in enumerate(funi.most_common(100))}
    both = set(ra) & set(ru)

    # REACH: for every letter, how many word tokens in each cut contain it (a letter counted once
    # per word however often it repeats), and the commonest words that carry it -- the "words it
    # hurts" a fault in that letter reaches.
    reach = {c: collections.Counter() for c in CUTS}
    carriers = {c: collections.defaultdict(collections.Counter) for c in CUTS}
    for (w, c), k in ALL.items():
        for ch in set(w):
            if ch.isalpha():
                reach[c][ch] += k
                carriers[c][ch][w] += k
    letter_reach = {c: dict(reach[c]) for c in CUTS}
    letter_words = {c: {ch: carriers[c][ch].most_common(12) for ch in carriers[c]} for c in CUTS}

    out = dict(
        letter_reach=letter_reach, letter_words=letter_words,
        books=len(names), books_unique=len(uniq), unique_files=uniq, tokens=tot_all, tokens_unique=tot_uni,
        distinct_forms=len(forms), cut_tokens=cut_tot,
        top_overlap_100=len(both),
        top=[dict(word=w, count=k, unique=funi[w], cuts={c: by_cut[c][w] for c in CUTS if by_cut[c][w]})
             for w, k in forms.most_common(400)],
        top_by_cut={c: by_cut[c].most_common(120) for c in CUTS},
        glyph_attention={g: gatt.get(g, 0) for g in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"},
        low_ceiling=low, lc_order=lc, uc_order=uc,
        pair_attention={st: dict(v) for st, v in patt.items()},
        words=rows, neglected=neglected[:80],
        mentions={g: where[g] for g in where},
    )
    json.dump(out, open(os.path.join(a.out, "corpus.json"), "w"), indent=1, ensure_ascii=False)

    print(f"{len(names)} files, {tot_all:,} words ({len(uniq)} unique files, {tot_uni:,}); "
          f"{len(forms):,} distinct surface forms")
    print("tokens by cut:", {c: f"{cut_tot[c]:,} ({cut_tot[c] / tot_all:.1%})" for c in CUTS})
    print(f"top-100 overlap ALL vs UNIQUE: {len(both)} of 100")
    print("\nglyph attention (lowercase, fewest first):", " ".join(f"{g}{gatt.get(g, 0)}" for g in lc))
    print("glyph attention (capitals, fewest first):", " ".join(f"{g}{gatt.get(g, 0)}" for g in uc))
    print("bottom-third ceilings:", low)
    print("\ntop 40 forms:", ", ".join(f"{w} {k}" for w, k in forms.most_common(40)))
    for c in "IBZ":
        print(f"top 20 in {c}:", ", ".join(f"{w} {k}" for w, k in by_cut[c].most_common(20)))
    print("\nmost neglected among the top", a.top)
    for r in neglected[:40]:
        print(f"  {r['word']:14s} {r['count']:6d} {r['main_cut']} neglect {r['neglect']:.2f}  "
              f"letters {''.join(r['neglected_letters'])}  pairs {' '.join(r['unbenched_pairs'])}")
    for g in a.show:
        print(f"\n== {g}: {gatt.get(g, 0)}")
        print("\n".join("   " + s for s in where[g]))


if __name__ == "__main__":
    main()
