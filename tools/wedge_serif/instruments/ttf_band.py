"""ttf_band.py -- a BUILT font's italic band bearings: for each glyph, the unsheared ink extent inside
the x-height band (as build.fit_aldine reads it) and the advance, so the final lsb/rsb the fit
produced can be compared across arms.

    python3 instruments/ttf_band.py FONT.ttf "ijr" [--slant 13] [--xh 429] [--over 14]

lsb_band = min(x - tan(slant) y) over band points; rsb_band = advance - max(...). Written 2026-09-28
for the issue sweep's j head and r arm (docs/albo-issue-sweep-2026-09-28.md).
"""
import sys, math
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import DecomposingRecordingPen
args = sys.argv[1:]
def opt(k, d):
    return float(args[args.index(k) + 1]) if k in args else d
path, chars = args[0], args[1]
sh = math.tan(math.radians(opt('--slant', 13.0))); XH = opt('--xh', 429.0); OV = opt('--over', 14.0)
f = TTFont(path); gs = f.getGlyphSet(); cm = f.getBestCmap(); hm = f['hmtx']
for ch in chars:
    n = cm[ord(ch)]; p = DecomposingRecordingPen(gs); gs[n].draw(p)
    pts = [q for op, a in p.value for q in a]
    band = [x - sh * y for x, y in pts if -OV <= round(y) <= XH + OV]
    adv = hm[n][0]
    print(f"{ch}: adv {adv:4d}  lsb_band {min(band):7.1f}  rsb_band {adv - max(band):7.1f}  band_w {max(band) - min(band):6.1f}")
