#!/usr/bin/env python3
"""ALDINE PROOF -- every image the owner's proof page needs, from one command.

    python3 aldine_proof.py <Albo-Italic.ttf> <out_dir> [--text FILE]

Writes, into <out_dir>:

    para27.png, para40.png   two paragraphs of running English, each set in the
                             candidate font and in Flanker Griffo Italic, 1:1,
                             on the same measure
    lc_a.png .. lc_z.png     per-letter rows: the scan crop where one is
    uc_A.png .. uc_Z.png     hand-located, then Albo | Flanker Griffo | Pagella
                             | Poetica | Cancelleresca, every cell scaled to one
                             x-height (capitals to one cap height)
    index.html               the page itself, written beside the images

WHY IT EXISTS: each design pass was republishing that page out of two throwaway
scripts, and a throwaway script is exactly where a standing rule gets dropped.
The rules live in the code now:

  * PNG at native pixels, never JPEG. Every font cell is a VECTOR render made
    at the size it is judged at -- nothing is resampled after it is drawn. Only
    the scan crop is resampled, because it is a photograph, and its factor is
    printed in its own label so a soft edge is never read as a drawn one.
  * No image gets a fixed width or height in the page's CSS: width:100%,
    height:auto, image-rendering:pixelated. A fixed dimension beside a max-
    scales the two axes differently, which has been asked about five times.
  * Labels drawn by PIL are ASCII. Pillow's default font has no en-dash and no
    em-dash -- measured, both come back as the same 8x11 tofu box -- and one
    shipped that way once. Hyphens only, in anything PIL draws.
  * Paragraphs of meaningful English sentences, not pangrams and not letter
    strings, and two registers (a novel's opening, a page of exposition),
    because what is being judged is the word image.

The scan crops come from aldine_autofit.SOURCES -- hand-located, because
automatic letter-finding was tried and was 78% right, which silently poisons
everything underneath it. They live outside the repo (~/Downloads, the upload
folder); a letter whose source image is missing simply loses its scan cell and
says so in the caption, rather than failing the run.
"""
import argparse, os, sys
from datetime import date
from string import Template

from PIL import Image, ImageDraw, ImageFont, ImageOps
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import aldine_autofit as AF          # SOURCES (the scan crops) and REFS

XH = 120                             # every lowercase cell, scaled to this x-height
CAP = XH * 1.4                       # every capital cell, scaled to this cap height
PAD = 18                             # white around each cell
MEASURE = 1100                       # the paragraph measure, px
SIZES = (27, 40)                     # reading size, and one to read the joins at
LC = 'abcdefghijklmnopqrstuvwxyz'
UC = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

GRIFFO = os.path.join(AF.REFS, 'flanker-griffo-italic.otf')
REF_FONTS = [                        # the comparison row, in this order
    ('Flanker Griffo', GRIFFO),
    ('Pagella', os.path.join(AF.REFS, 'texgyrepagella-italic.otf')),
    ('Poetica', os.path.join(AF.REFS, 'poetica-std-regular.otf')),
    ('Cancell.', os.path.join(AF.REFS, 'cancelleresca-bastarda-beta12.otf')),
]

# Two registers. Austen for the word image of ordinary narrative, Darwin for
# long expository sentences with subordinate clauses and semicolons -- the
# shapes a running italic actually has to hold together.
PARAGRAPHS = [
    ("Austen, Pride and Prejudice",
     "It is a truth universally acknowledged, that a single man in possession of a good "
     "fortune, must be in want of a wife. However little known the feelings or views of "
     "such a man may be on his first entering a neighbourhood, this truth is so well fixed "
     "in the minds of the surrounding families, that he is considered the rightful property "
     "of some one or other of their daughters. My dear Mr. Bennet, said his lady to him one "
     "day, have you heard that Netherfield Park is let at last? Mr. Bennet replied that he "
     "had not. But it is, returned she; for Mrs. Long has just been here, and she told me "
     "all about it."),
    ("Darwin, On the Origin of Species",
     "It is interesting to contemplate an entangled bank, clothed with many plants of many "
     "kinds, with birds singing on the bushes, with various insects flitting about, and with "
     "worms crawling through the damp earth, and to reflect that these elaborately "
     "constructed forms, so different from each other, and dependent upon each other in so "
     "complex a manner, have all been produced by laws acting around us. These laws, taken "
     "in the largest sense, being Growth with Reproduction; Inheritance which is almost "
     "implied by reproduction; Variability from the indirect and direct action of the "
     "conditions of life, and from use and disuse; and a Ratio of Increase so high as to "
     "lead to a Struggle for Life, and as a consequence to Natural Selection. Thus, from "
     "the war of nature, from famine and death, the most exalted object which we are "
     "capable of conceiving, namely, the production of the higher animals, directly "
     "follows."),
]

_ttf = {}
def ttf(path):
    if path not in _ttf:
        _ttf[path] = TTFont(path, lazy=True)
    return _ttf[path]

def has(path, ch):
    return ord(ch) in ttf(path).getBestCmap()

def top_of(path, ch):
    """Height of `ch`'s outline over the em -- x-height off the x, cap height off
    the H. Measured on the OUTLINE, never a raster bbox: a raster bbox on a white
    ground returns the canvas (round 119)."""
    f = ttf(path)
    gs = f.getGlyphSet()
    bp = BoundsPen(gs)
    gs[f.getBestCmap()[ord(ch)]].draw(bp)
    return bp.bounds[3] / f['head'].unitsPerEm

def face_name(path):
    """Full name from the name table, so a renamed family relabels itself."""
    try:
        for rec in ttf(path)['name'].names:
            if rec.nameID == 4:
                return str(rec.toUnicode())
    except Exception:
        pass
    return os.path.splitext(os.path.basename(path))[0]

# --------------------------------------------------------------- paragraphs

def wrap(font, text, width):
    lines, cur = [], ''
    for w in text.split():
        t = (cur + ' ' + w).strip()
        if cur and font.getlength(t) > width:
            lines.append(cur); cur = w
        else:
            cur = t
    lines.append(cur)
    return lines

def block(path, px, text, width=MEASURE):
    f = ImageFont.truetype(path, px)
    lines = wrap(f, text, width - 40)
    lh = int(px * 1.32)
    im = Image.new('L', (width, lh * len(lines) + 40), 255)
    d = ImageDraw.Draw(im)
    for i, line in enumerate(lines):
        d.text((20, 10 + i * lh), line, font=f, fill=0)
    return im

def caption(text, width=MEASURE):
    im = Image.new('L', (width, 26), 255)
    ImageDraw.Draw(im).text((20, 4), text, font=ImageFont.load_default(16), fill=120)
    return im

def para_sheet(candidate, cand_name, px, paragraphs):
    """One sheet per size: each paragraph set in the candidate, then in Griffo."""
    rows = []
    for i, (title, text) in enumerate(paragraphs):
        if i:
            rows.append(Image.new('L', (MEASURE, 22), 255))   # air between texts
        for name, path in ((cand_name, candidate), ('Flanker Griffo Italic', GRIFFO)):
            rows.append(block(path, px, text))
            rows.append(caption('%s - %d px - 1:1 - %s' % (name, px, title)))
    h = sum(r.height for r in rows) + 10 * len(rows)
    out = Image.new('L', (MEASURE, h), 255)
    y = 0
    for r in rows:
        out.paste(r, (0, y)); y += r.height + 10
    return out

# ------------------------------------------------------------- letter rows

def cell_font(path, ch, size_px, name):
    size = max(8, int(round(size_px)))
    f = ImageFont.truetype(path, size)
    canvas = int(size * 4)
    im = Image.new('L', (canvas, canvas), 255)
    ImageDraw.Draw(im).text((size, size), ch, font=f, fill=0)
    bb = ImageOps.invert(im).getbbox()
    if bb is None:
        return None                                   # cmap hit, empty outline
    if bb[0] <= 0 or bb[1] <= 0 or bb[2] >= canvas or bb[3] >= canvas:
        raise RuntimeError('%s %r clipped its canvas -- a silent crop is worse '
                           'than a crash' % (os.path.basename(path), ch))
    box = (max(0, bb[0] - PAD), max(0, bb[1] - PAD),
           min(canvas, bb[2] + PAD), min(canvas, bb[3] + PAD))
    return im.crop(box), name

def cell_scan(ch):
    """The photograph, resampled to the sheet's x-height. The ONLY resampled
    cell on the page, and its factor rides in its label."""
    src = AF.SOURCES.get(ch)
    if not src:
        return None
    path, box, xh, _note = src
    path = os.path.expanduser(path)
    if not os.path.exists(path):
        return None                                   # source lives outside the repo
    im = Image.open(path).convert('L').crop(box)
    k = XH / xh
    im = im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))),
                   Image.LANCZOS)
    return (ImageOps.expand(im, PAD, 255), 'scan x%.1f' % k), k

def row(candidate, cand_label, ch, caps):
    """One letter across every face that has it. Returns (image, scan factor)."""
    cells, factor = [], None
    if not caps:
        sc = cell_scan(ch)
        if sc:
            cells.append(sc[0]); factor = sc[1]
    for name, path in [(cand_label, candidate)] + REF_FONTS:
        if not os.path.exists(path) or not has(path, ch):
            continue                                  # Cancelleresca has no capitals
        h = top_of(path, 'H' if caps else 'x')
        c = cell_font(path, ch, (CAP if caps else XH) / h, name)
        if c:
            cells.append(c)
    if not cells:
        return None, None
    lab = ImageFont.load_default(15)
    H = max(c[0].height for c in cells) + 24
    W = sum(c[0].width for c in cells) + 10 * (len(cells) - 1) + 60
    out = Image.new('L', (W, H), 255)
    d = ImageDraw.Draw(out)
    d.text((8, 4), ch, font=ImageFont.load_default(28), fill=0)
    x = 60
    for im, name in cells:
        out.paste(im, (x, H - 24 - im.height))        # bottom-aligned, as the sheet reads
        d.text((x, H - 20), name, font=lab, fill=120)
        x += im.width + 10
    return out, factor

# ------------------------------------------------------------------- page

PAGE = Template("""<title>$title</title>
<style>
  :root{ --ink:#221d17; --ink-soft:#5d554a; --rule:#ddd5c6; --ground:#f6f2e9; --panel:#fffdf8; --accent:#8c3a1e; }
  @media (prefers-color-scheme: dark){ :root:not([data-theme="light"]){ --ink:#ece5d8; --ink-soft:#a79c8b; --rule:#3a352d; --ground:#17150f; --panel:#201d16; --accent:#d9825e; } }
  :root[data-theme="dark"]{ --ink:#ece5d8; --ink-soft:#a79c8b; --rule:#3a352d; --ground:#17150f; --panel:#201d16; --accent:#d9825e; }
  body{background:var(--ground);color:var(--ink);font-family:"Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif;line-height:1.55;padding-inline:20px;padding-block:44px 72px;}
  main{max-width:900px;margin:0 auto;display:flex;flex-direction:column;gap:34px;}
  h1{font-size:clamp(1.7rem,5vw,2.3rem);margin:0;letter-spacing:-.01em;text-wrap:balance;}
  .sub{color:var(--ink-soft);margin:6px 0 0;font-size:.98rem;}
  h2{font-size:1.06rem;margin:0 0 14px;letter-spacing:.07em;text-transform:uppercase;font-family:ui-sans-serif,system-ui,sans-serif;color:var(--ink-soft);}
  p{margin:0 0 12px;}
  figcaption{font-family:ui-sans-serif,system-ui,sans-serif;font-size:.78rem;letter-spacing:.04em;color:var(--ink-soft);}
  figure{margin:0;display:flex;flex-direction:column;gap:6px;}
  .fig img{display:block;width:100%;height:auto;image-rendering:pixelated;background:#fff;border:1px solid var(--rule);}
  .rows{display:flex;flex-direction:column;gap:16px;}
  .note{background:var(--panel);border-left:3px solid var(--accent);padding:14px 18px;}
</style>
<main>
  <header>
    <h1>$title</h1>
    <p class="sub">$sub</p>
  </header>
  <div class="note"><p style="margin:0">Cells are vector renders at native pixels; only the scan crop is resampled, and its factor is in its label. Columns are bottom-aligned, so a descender hangs and a cap sits &mdash; read shape, weight and stress, not vertical position.</p></div>

  <section><h2>In sentences, at reading size</h2>
    <div class="rows">
$paras    </div>
  </section>
  <section><h2>Lowercase</h2><div class="rows">
$lc  </div></section>
  <section><h2>Capitals</h2><div class="rows">
$uc  </div></section>
</main>
""")

def fig(src, alt, cap):
    return ('      <figure class="fig"><img src="%s" alt="%s">'
            '<figcaption>%s</figcaption></figure>\n' % (src, alt, cap))

def write_page(out_dir, cand_label, font_path, paragraphs, lc_facts, uc_facts):
    title = '%s, letter by letter' % cand_label
    texts = ', '.join(t for t, _ in paragraphs)
    sub = ('%s in running English beside Flanker Griffo Italic, then every letter '
           'beside the Griffo scan where one is cropped and beside Flanker Griffo, '
           'Pagella Italic, Poetica and Cancelleresca Bastarda &mdash; all at one '
           'x-height (capitals at one cap height). Paragraphs: %s. Built %s from '
           '<code>%s</code>; republished as letters change.'
           % (cand_label, texts, date.today().isoformat(), os.path.basename(font_path)))
    paras = ''
    for px in SIZES:
        paras += fig('para%d.png' % px, 'two paragraphs at %d px' % px,
                     '<strong>%d px, 1:1</strong> &middot; each paragraph in %s above '
                     'and Flanker Griffo Italic below, on one %d px measure'
                     % (px, cand_label, MEASURE))
    def letters(facts, prefix):
        s = ''
        for ch, factor in facts:
            if factor:
                cap = ('<strong>%s</strong> &middot; scan on the left, resampled '
                       '&times;%.1f to the sheet&rsquo;s x-height' % (ch, factor))
            else:
                cap = '<strong>%s</strong> &middot; no scan crop &mdash; references only' % ch
            s += fig('%s_%s.png' % (prefix, ch), ch, cap)
        return s
    page = PAGE.substitute(title=title, sub=sub, paras=paras,
                           lc=letters(lc_facts, 'lc'), uc=letters(uc_facts, 'uc'))
    path = os.path.join(out_dir, 'index.html')
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write(page)
    return path

# ------------------------------------------------------------------- main

def read_text(path):
    """Blank-line separated paragraphs; a paragraph may open with a `Title:`
    line, otherwise it is numbered."""
    chunks = [c.strip() for c in open(path, encoding='utf-8').read().split('\n\n')]
    out = []
    for i, c in enumerate(x for x in chunks if x):
        head, _, rest = c.partition('\n')
        if head.rstrip().endswith(':') and rest.strip():
            out.append((head.rstrip().rstrip(':'), ' '.join(rest.split())))
        else:
            out.append(('text %d' % (i + 1), ' '.join(c.split())))
    if not out:
        sys.exit('%s: no paragraphs found' % path)
    return out

def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('font', help='the candidate italic (TTF or OTF)')
    ap.add_argument('out_dir')
    ap.add_argument('--text', metavar='FILE',
                    help='replace the two default paragraphs; blank-line separated')
    a = ap.parse_args()
    if not os.path.exists(a.font):
        sys.exit('no such font: %s' % a.font)
    for _, p in REF_FONTS:
        if not os.path.exists(p):
            print('missing reference, its column is dropped: %s' % p)
    paragraphs = read_text(a.text) if a.text else PARAGRAPHS
    os.makedirs(a.out_dir, exist_ok=True)
    label = face_name(a.font)
    short = label.split()[0] if label else 'Candidate'

    written = []
    for px in SIZES:
        p = os.path.join(a.out_dir, 'para%d.png' % px)
        para_sheet(a.font, label, px, paragraphs).save(p)
        written.append(p)

    facts = {}
    for name, chars, caps in (('lc', LC, False), ('uc', UC, True)):
        facts[name] = []
        for ch in chars:
            im, factor = row(a.font, short, ch, caps)
            if im is None:
                print('%s: no face has it -- skipped' % ch); continue
            p = os.path.join(a.out_dir, '%s_%s.png' % (name, ch))
            im.save(p); written.append(p)
            facts[name].append((ch, factor))

    page = write_page(a.out_dir, label, a.font, paragraphs, facts['lc'], facts['uc'])
    written.append(page)
    scans = sum(1 for _, f in facts['lc'] if f)
    print('%d files -> %s' % (len(written), a.out_dir))
    print('  %d paragraph sheets, %d lowercase (%d with a scan crop), %d capitals'
          % (len(SIZES), len(facts['lc']), scans, len(facts['uc'])))
    return 0

if __name__ == '__main__':
    sys.exit(main())
