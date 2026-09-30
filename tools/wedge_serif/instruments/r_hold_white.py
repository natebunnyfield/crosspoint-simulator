# hold the white after the r when its end changes, per pair, against a reference build:
#   the closest approach (instruments/pair_gap2d.py's measure; rounds 438-442) where the nearest
#   points face each other horizontally; the smallest HORIZONTAL gap over the rows both glyphs ink
#   where they are stacked vertically (the r's end crest over a T's bar, the hanging end over a
#   baseline period: a vertical distance a kern barely answers); closest approach when the two
#   share no row. The reference build decides the measure for the pair.
# Excludes the fence closes (fences.py's symmetry rule) and r t (back at round 437's).
# MODE=report prints deltas only; otherwise merges kerns into the rsnip block.
import sys, os, json, numpy as np, freetype, uharfbuzz as hb
from scipy import ndimage as ndi
from fontTools.ttLib import TTFont
REF, NEW = sys.argv[1], sys.argv[2]; TOL = 2.5; MODE = os.environ.get("MODE", "apply")
EXCL = set(")]}t")
chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.,:;?!'\"-\u2019\u201d\u2014\u2013\u2026"
def canvases(path, pair):
    face = freetype.Face(path); face.set_pixel_sizes(0, 1000)
    blob = hb.Blob.from_file_path(path); hf = hb.Face(blob); font = hb.Font(hf); s = 1000 / hf.upem
    buf = hb.Buffer(); buf.add_str(pair); buf.guess_segment_properties(); hb.shape(font, buf, {"kern": True})
    x = 0; masks = []
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        face.load_glyph(info.codepoint, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING); b = face.glyph.bitmap
        a = np.array(b.buffer, np.uint8).reshape(b.rows, b.pitch)[:, :b.width] > 127
        masks.append((a, int(round(x + pos.x_offset * s)) + face.glyph.bitmap_left, face.glyph.bitmap_top)); x += pos.x_advance * s
    Wc = int(x) + 800; top = 1100; H = 1700; cv = []
    for a, l, t in masks:
        c = np.zeros((H, Wc), bool); c[top - t:top - t + a.shape[0], l + 300:l + 300 + a.shape[1]] |= a; cv.append(c)
    return cv
def closest(cv):
    return float(ndi.distance_transform_edt(~cv[1])[cv[0]].min())
def closest_vec(cv):
    """the closest approach and whether it runs more vertical than horizontal"""
    d, (iy, ix) = ndi.distance_transform_edt(~cv[1], return_indices=True)
    ys, xs = np.nonzero(cv[0]); k = np.argmin(d[ys, xs]); y, x = ys[k], xs[k]
    return float(d[y, x]), abs(iy[y, x] - y) > abs(ix[y, x] - x)
def rowgap(cv):
    r0 = cv[0].any(1) & cv[1].any(1)
    if not r0.any(): return None
    g = []
    for yy in np.nonzero(r0)[0]:
        g.append(np.nonzero(cv[1][yy])[0].min() - np.nonzero(cv[0][yy])[0].max())
    return float(min(g))
OVERHANG = set("fTXZ7")     # letters and figures whose top reaches OVER the r's end
def measure(path, c, left="r"):
    # round 442, second review. Letters and figures: the closest approach -- the measure
    # rounds 438-441 set the owner's r + letter targets in -- EXCEPT the ones whose top
    # reaches over the r's end (f's hook, the bars of T Z 7, X's arm): there the nearest
    # point is above the end, a vertical distance a kern barely moves, and holding it by
    # closest approach dragged the T 21-26 units sideways. Those, and every punctuation
    # mark (a baseline period is below the end: holding its closest approach pushed it 26
    # units away), hold the smallest HORIZONTAL gap over the rows both glyphs ink; closest
    # approach when no row is shared. A row gap is NOT used on a letter in general: its
    # minimum jumps to whichever row the new end reaches (r d read -18 and r 1 -65 by
    # rows where the closest approach moved +4 and +3).
    cv = canvases(path, left + c)
    if c.isalnum() and c not in OVERHANG: return closest(cv), "ca"
    rg = rowgap(cv)
    return (rg, "row") if rg is not None else (closest(cv), "ca")
q = os.environ.get('TABLE', 'outlines/spacing_b2.json'); d = json.loads(open(q).read())
for st in ("Italic", "BoldItalic"):
    fa, fb = f"{REF}/Albo-{st}.ttf", f"{NEW}/Albo-{st}.ttf"
    cm = TTFont(fb).getBestCmap(); blk = d["rsnip"].setdefault(st, {}); moved = []
    for c in chars:
        if c in EXCL or ord(c) not in cm: continue
        (ga, m1), (gb, m2) = measure(fa, c), measure(fb, c)
        if m1 != m2:     # judge both builds by the reference's measure
            cvb = canvases(fb, "r" + c)
            gb = closest(cvb) if m1 == "ca" else (rowgap(cvb) if rowgap(cvb) is not None else gb)
        dl = gb - ga
        if abs(dl) > TOL:
            key = "r " + cm[ord(c)]
            if MODE != "report": blk[key] = int(round(blk.get(key, 0) - dl))
            moved.append((c, m1, round(ga, 1), round(gb, 1), round(dl, 1)))
    d["rsnip"][st] = {k: v for k, v in blk.items() if v != 0}
    print(st, moved)
if MODE != "report": open(q, 'w').write(json.dumps(d, indent=1, ensure_ascii=False, sort_keys=True))
