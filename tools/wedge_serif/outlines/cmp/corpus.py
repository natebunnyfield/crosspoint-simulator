"""What the owner's own books actually ask a font for (round 99, 2026-09-14).

The demand list for coverage is MEASURED here rather than guessed from a
Unicode block: every epub in `~/src/claude-tools/*/epub/` is unzipped, the
markup stripped, and the characters counted; the result is diffed against a
font's cmap and printed in frequency order. Those books are the reader's
real-world corpus (the global CLAUDE.md says so), which is why the firmware
repo's `docs/font-unicode-coverage.md` uses the same source.

Anything a font lacks is supplied by NOTO at .cpfont build time, so a missing
codepoint is not a hole on the page -- it is one character of a different
typeface inside a word, which is invisible in a test that only asks "did it
render".

    cd tools/wedge_serif && PYTHON_GIL=0 python3 -m outlines.cmp.corpus <font.ttf>
    ALBO_CORPUS=/some/other/dir python3 -m outlines.cmp.corpus <font.ttf>
"""
import os, re, sys, glob, zipfile, collections, unicodedata
from fontTools.ttLib import TTFont

ROOT = os.environ.get('ALBO_CORPUS', os.path.expanduser('~/src/claude-tools'))
TEXTY = ('.xhtml', '.html', '.htm', '.ncx', '.opf')

def count(root=ROOT):
    """Character counts over every epub under `root`. Markup is stripped with
    a tag regex rather than parsed: an entity or an attribute value counted by
    accident moves nothing at this scale (2.5M characters), and a parser that
    rejects one malformed file would silently drop a whole book."""
    cnt = collections.Counter(); books = sorted(glob.glob(os.path.join(root, '*', 'epub', '*.epub')))
    for b in books:
        try: z = zipfile.ZipFile(b)
        except Exception: continue
        for n in z.namelist():
            if not n.lower().endswith(TEXTY): continue
            try: t = z.read(n).decode('utf-8', 'ignore')
            except Exception: continue
            cnt.update(re.sub(r'<[^>]+>', ' ', t))
    return cnt, books

def report(font_path, root=ROOT, limit=200):
    cnt, books = count(root)
    have = set(TTFont(font_path).getBestCmap())
    miss = [(ord(c), c) for c in cnt if ord(c) not in have and ord(c) >= 0x20
            and not unicodedata.category(c).startswith('C')]
    miss.sort(key=lambda t: -cnt[t[1]])
    print(f"{len(books)} books, {sum(cnt.values()):,} characters, {len(cnt)} distinct codepoints")
    print(f"{os.path.basename(font_path)}: {len(have)} in cmap; {len(miss)} corpus codepoints MISSING")
    for cp, c in miss[:limit]:
        print(f"  U+{cp:04X} {c!r:>6} {cnt[c]:>7}  {unicodedata.name(c, '?')[:48]}")
    return miss

if __name__ == '__main__':
    miss = report(sys.argv[1] if len(sys.argv) > 1 else '../../build/fjord-fonts/Albo-Regular.ttf')
    sys.exit(1 if miss else 0)
