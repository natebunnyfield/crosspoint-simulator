"""In-word balance: how dark each letter reads INSIDE common English words,
through the reader's four-level pipeline at 13 pt (54 px em), against a
reference face rendered the same way.

    python3 -m outlines.cmp.balance <font.ttf> [--ref <ref.ttf>] [--words w1,w2,...] [--json out]

Owner 2026-09-14 ("Beyond", "Tuesday": "the 'y' is too dark in a word
currently ... we need to find the balance for this letter and all letters
within a word image. use vision and math and a small corpus of english
words"). The isolated-letter measure (`word_weight.py`) averages a letter's
ink over its whole box, ascender to descender, and calls the y ordinary;
the eye reads the LINE: ink in the x-height band, and the darkest knot a
letter makes. So, per letter occurrence in a word:

  band   mean darkness of the letter's columns over the x-height band
         (baseline to x-height, +1 px each way for overshoot) -- the color
         the letter contributes to the line of text
  peak   the darkest PEAK x PEAK px window (6 px = 0.11 em) whose center
         lies in the letter's columns, any row -- the knot
  full   mean darkness over the letter's columns, ascender to descender
         (word_weight's figure, for continuity)

Columns are attributed to letters by pen position (no kerning in this
font). Each figure is averaged over the letter's occurrences in the corpus
(word_weight's 147 most common words), then given relative to the
frequency-weighted lowercase mean of the same figure; with --ref, the
reference face's same relative figure is divided out (a y has a descender
in every face), so `vs ref` is what THIS design adds to the letter.
"""
import argparse, json, statistics, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont
sys.path.insert(0, __file__.rsplit('/outlines/', 1)[0])
from word_weight import WORDS
from .proof import LEVELS, THRESH

PX = 54; SS = 8; PEAK = 6
LETTERS = "abcdefghijklmnopqrstuvwxyz"

_XH = {}
def xheight_px(path, px=PX):
    """The x-height in px: OS/2 sxHeight when the font has one (Albertus
    Medium's OS/2 is version 1, no sxHeight), else the ink height of an x."""
    if (path, px) in _XH: return _XH[(path, px)]
    tt = TTFont(path); os2 = tt['OS/2']
    if getattr(os2, 'sxHeight', 0):
        v = os2.sxHeight * px / tt['head'].unitsPerEm
    else:
        big = ImageFont.truetype(path, px * 10); asc, desc = big.getmetrics()
        im = Image.new('L', (px * 12, asc + desc), 255)
        ImageDraw.Draw(im).text((px, asc), 'x', font=big, fill=0, anchor='ls')
        bb = im.point(lambda q: 255 - q).getbbox(); v = (bb[3] - bb[1]) / 10.0
    _XH[(path, px)] = v; return v

def render_levels(path, text, px=PX, ss=SS):
    """The four-level raster of `text` (0 = white .. 1 = black, float), the
    baseline row and the x-height in px, and each letter's column span."""
    big = ImageFont.truetype(path, px * ss); small = ImageFont.truetype(path, px)
    xh = xheight_px(path, px)
    asc, desc = small.getmetrics(); pad = 4
    W = int(small.getlength(text)) + 2 * pad; H = asc + desc + 2 * pad
    im = Image.new('L', (W * ss, H * ss), 255)
    ImageDraw.Draw(im).text((pad * ss, (pad + asc) * ss), text, font=big, fill=0, anchor='ls')
    a = np.asarray(im, dtype=np.float32) / 255.0
    cov = 1.0 - a.reshape(H, ss, W, ss).mean(axis=(1, 3))
    lv = np.zeros(cov.shape, dtype=np.float32)
    for t, L in zip(THRESH, LEVELS[1:]): lv[cov >= t] = 1.0 - L / 255.0
    spans = []
    for i in range(len(text)):
        x0 = pad + small.getlength(text[:i]); x1 = pad + small.getlength(text[:i + 1])
        spans.append((int(round(x0)), int(round(x1))))
    return lv, pad + asc, xh, spans

def measure(path, words):
    occ = {ch: dict(band=[], peak=[], full=[]) for ch in LETTERS}
    per_word = {}
    for w in words:
        lv, base, xh, spans = render_levels(path, w)
        H, W = lv.shape
        b0 = max(0, int(round(base - xh)) - 1); b1 = min(H, base + 1)
        # box-filter for the peak
        k = PEAK; cs = np.cumsum(np.cumsum(np.pad(lv, ((1, 0), (1, 0))), axis=0), axis=1)
        win = (cs[k:, k:] - cs[:-k, k:] - cs[k:, :-k] + cs[:-k, :-k]) / (k * k)   # (H-k+1, W-k+1), window top-left at (r, c)
        per_word[w] = []
        for ch, (x0, x1) in zip(w, spans):
            if ch not in occ or x1 <= x0: continue
            band = float(lv[b0:b1, x0:x1].mean())
            full = float(lv[:, x0:x1].mean())
            c0 = max(0, x0 - k // 2); c1 = max(c0 + 1, min(win.shape[1], x1 - k // 2))
            peak = float(win[:, c0:c1].max())
            occ[ch]['band'].append(band); occ[ch]['peak'].append(peak); occ[ch]['full'].append(full)
            per_word[w].append((ch, band, peak))
    out = {}
    for ch in LETTERS:
        o = occ[ch]
        if o['band']:
            out[ch] = dict(n=len(o['band']), band=statistics.mean(o['band']), peak=statistics.mean(o['peak']), full=statistics.mean(o['full']))
    # frequency-weighted lowercase means
    for key in ('band', 'peak', 'full'):
        tot = sum(out[ch][key] * out[ch]['n'] for ch in out); n = sum(out[ch]['n'] for ch in out)
        mean = tot / n
        for ch in out: out[ch][key + '_rel'] = out[ch][key] / mean
    return out, per_word

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('font'); ap.add_argument('--ref'); ap.add_argument('--ref2')
    ap.add_argument('--words', help='comma-separated extra words (reported per word, not in the stats)')
    ap.add_argument('--json'); ap.add_argument('--letters', default=None, help='only these letters in the table')
    a = ap.parse_args()
    ours, pw_ = measure(a.font, WORDS)
    refs = []
    for r in (a.ref, a.ref2):
        if r: refs.append((r, measure(r, WORDS)[0]))
    rows = []
    for ch in sorted(ours, key=lambda c: -ours[c]['band_rel']):
        o = ours[ch]; row = dict(ch=ch, **o)
        for i, (r, ro) in enumerate(refs):
            if ch in ro:
                row[f'vs_ref{i}_band'] = (o['band_rel'] / ro[ch]['band_rel'] - 1) * 100
                row[f'vs_ref{i}_peak'] = (o['peak_rel'] / ro[ch]['peak_rel'] - 1) * 100
        rows.append(row)
    if a.json: json.dump(dict(font=a.font, refs=[r for r, _ in refs], letters=rows), open(a.json, 'w'), indent=1)
    hdr = 'letter   n   band  band_rel   peak  peak_rel   full_rel' + ''.join(f'   vs_ref{i}:band  peak' for i in range(len(refs)))
    print(f'font {a.font}\n{hdr}')
    for row in rows:
        if a.letters and row['ch'] not in a.letters: continue
        extra = ''.join(f"   {row.get(f'vs_ref{i}_band', float('nan')):+8.1f}% {row.get(f'vs_ref{i}_peak', float('nan')):+6.1f}%" for i in range(len(refs)))
        print(f"  {row['ch']}    {row['n']:4d}  {row['band']:.3f}   {row['band_rel']:5.2f}    {row['peak']:.3f}   {row['peak_rel']:5.2f}     {row['full_rel']:5.2f}{extra}")
    if a.words:
        print('\nper word (letter band / peak):')
        for w in a.words.split(','):
            lv, base, xh, spans = render_levels(a.font, w)
            _, pwd = measure(a.font, [w])
            print('  ' + w + ':  ' + '  '.join(f'{ch}:{b:.2f}/{p:.2f}' for ch, b, p in pwd[w]))

if __name__ == '__main__':
    main()
