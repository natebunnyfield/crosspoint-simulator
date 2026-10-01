"""mark_crowd.py -- how close does each MARK come to the letters and marks beside it, in 2-D?
Round 453 (2026-10-01), owner: *"reduce umlaut and other marks to not be so close to other
letters and marks"*.

    venv/bin/python instruments/mark_crowd.py FONT ... [--pairs "Wö Tö Të ěš"] [--top 25]
    venv/bin/python instruments/mark_crowd.py --clear BUILD_DIR [--k 0.95] [--cuts Italic,BoldItalic] [--dry]
    venv/bin/python instruments/mark_crowd.py --zoom OUT.png "Të Tö í?" [LABEL::]FONT ...

WHY IT EXISTS. The touch gate (cmp_touch.py) and the composite clearance it drives
(local_ai/clearance.py --composites) measure white ROW BY ROW: on each scanline, the second
glyph's leftmost ink minus the first glyph's rightmost. A dieresis tucked UNDER a T's arm shares
no scanline with the arm, so that measure sees no contact at all, and the Italic's Tö kept To's
full kern with the dots a few units under the arm. This measures the true 2-D distance.

For every pair in the owner's books with an accented letter on either side (NFC, counted from
the epubs exactly as r448d's acc_corpus.py counted them) plus --pairs, shaped by HarfBuzz with
the font's own kerning:
  near    the distance from each accented letter's MARK to the whole ink of its neighbor
          (the neighbor's own mark included), / the font's x-height
  what    whether that nearest ink is the neighbor's mark ("mark") or its letter ("letter")
The mark is the accented glyph's raster minus its base letter's (dilated 2 px, same origin,
unhinted, 1 px per unit), so a reference whose accented letters are drawn rather than composed
measures the same way. Bases: NFD's first letter, dotless for i and j.

Summary per font, weighted by how often each pair occurs in the books: the share of mark
occurrences whose nearest neighbor ink is under 0.10 / 0.15 / 0.20 / 0.25 x-height, and the
median. Then the closest pairs, each with its count.
"""
import sys, os, re, glob, zipfile, collections, unicodedata, html, math, functools
import numpy as np, freetype, uharfbuzz as hb
from scipy import ndimage as ndi
from scipy.spatial import cKDTree
from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

DISPLAY = "Wö Vö Tö Yö Fö Pö Tê Të Tè Tě Tó Tú Wä Vä Wü Yü Fä Tä Tü fö fé fí ří ěš ší öü üö ëï äö " \
          "ió ië tê êt tô ôt lé él dé íl ïl kë ñó ó? í? é! ö, ã, ê. Kö Lö Rö Kä"


def base_of(ch):
    b = unicodedata.normalize('NFD', ch)[0]
    return 'ı' if b == 'i' else ('ȷ' if b == 'j' else b)


def accented(ch):
    d = unicodedata.normalize('NFD', ch)
    return len(d) > 1 and d[0].isalpha() and ch.isalpha()


@functools.lru_cache(maxsize=1)
def corpus_pairs():
    """{two-character string: count} for every adjacent non-space pair in the owner's books
    with a character above ASCII on either side."""
    from outlines.cmp.corpus import ROOT, TEXTY
    big = collections.Counter()
    for b in sorted(glob.glob(f"{ROOT}/*/epub/*.epub")):
        try: z = zipfile.ZipFile(b)
        except Exception: continue
        for n in z.namelist():
            if not n.lower().endswith(TEXTY): continue
            t = z.read(n).decode("utf-8", "ignore"); t = re.sub(r"<[^>]+>", " ", t)
            t = unicodedata.normalize("NFC", html.unescape(t))
            for a, c in zip(t, t[1:]):
                if a.isspace() or c.isspace(): continue
                if ord(a) > 127 or ord(c) > 127: big[a + c] += 1
    return big


class Font:
    def __init__(self, path):
        self.path = path; self.name = os.path.basename(path)
        self.t = TTFont(path); self.cmap = self.t.getBestCmap(); self.upm = self.t['head'].unitsPerEm
        self.f = freetype.Face(path); self.f.set_pixel_sizes(0, self.upm)
        self.hbf = hb.Font(hb.Face(hb.Blob.from_file_path(path)))
        sx = self.t['OS/2'].sxHeight if self.name.startswith('Albo') else 0
        if sx and sx > 0: self.xh = float(sx)
        else:
            self.f.load_char('x', freetype.FT_LOAD_NO_HINTING); self.xh = self.f.glyph.metrics.horiBearingY / 64
        self._g = {}; self._m = {}; self._t = {}

    def has(self, s): return all(ord(c) in self.cmap for c in s)

    def gid(self, ch): return self.t.getGlyphID(self.cmap[ord(ch)])

    def glyph(self, gid):
        """(ink bool array, left, top) at 1 px per unit, unhinted."""
        if gid not in self._g:
            self.f.load_glyph(gid, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING)
            b = self.f.glyph.bitmap
            a = np.array(b.buffer, np.uint8).reshape(b.rows, b.pitch)[:, :b.width] >= 128 if b.rows else np.zeros((0, 0), bool)
            self._g[gid] = (a, self.f.glyph.bitmap_left, self.f.glyph.bitmap_top)
        return self._g[gid]

    def mark(self, ch):
        """The mark's ink of accented `ch` as glyph-local points (x right, y up), or None."""
        if ch in self._m: return self._m[ch]
        out = None
        b = base_of(ch)
        if accented(ch) and self.has(ch) and self.has(b):
            A, al, at = self.glyph(self.gid(ch)); B, bl, bt = self.glyph(self.gid(b))
            if A.size and B.size:
                L = min(al, bl); T = max(at, bt)
                R = max(al + A.shape[1], bl + B.shape[1]); Bo = min(at - A.shape[0], bt - B.shape[0])
                ca = np.zeros((T - Bo, R - L), bool); cb = ca.copy()
                ca[T - at:T - at + A.shape[0], al - L:al - L + A.shape[1]] = A
                cb[T - bt:T - bt + B.shape[0], bl - L:bl - L + B.shape[1]] = B
                m = ca & ~ndi.binary_dilation(cb, iterations=2)
                m = ndi.binary_opening(m)                         # anti-aliasing slivers off the base's edge
                lab, n = ndi.label(m)
                if n:
                    sizes = ndi.sum(m, lab, range(1, n + 1)); keep = np.isin(lab, 1 + np.nonzero(sizes >= 0.02 * sizes.max())[0])
                    m = keep
                if m.sum() >= 20:
                    r, c = np.nonzero(m)
                    out = np.stack([c + L, T - r], 1).astype(float)
        self._m[ch] = out
        return out

    def own(self, ch):
        """The mark's own gap: its 2-D distance to its base letter's ink, in font units."""
        if ('own', ch) in self._m: return self._m[('own', ch)]
        m = self.mark(ch); out = None
        if m is not None:
            B, bl, bt = self.glyph(self.gid(base_of(ch)))
            r, c = np.nonzero(B & ~ndi.binary_erosion(B))
            out = float(cKDTree(np.stack([c + bl, bt - r], 1)).query(_edge(m), k=1)[0].min())
        self._m[('own', ch)] = out
        return out

    def mark_edge(self, ch):
        if ('edge', ch) not in self._m:
            m = self.mark(ch); self._m[('edge', ch)] = None if m is None else _edge(m)
        return self._m[('edge', ch)]

    def above(self, ch):
        """The mark sits over its letter (its ink's mean height above the base's middle)."""
        m = self.mark(ch)
        if m is None: return False
        B, bl, bt = self.glyph(self.gid(base_of(ch)))
        return float(m[:, 1].mean()) > bt - B.shape[0] / 2

    def tree(self, gid):
        if gid not in self._t:
            nb = self.ink(gid)
            self._t[gid] = None if nb is None else (cKDTree(nb[0]), nb[1])
        return self._t[gid]

    def ink(self, gid):
        """Glyph-local edge points and a membership test for the whole ink."""
        a, l, t = self.glyph(gid)
        if not a.size: return None
        e = a & ~ndi.binary_erosion(a)
        r, c = np.nonzero(e)
        return np.stack([c + l, t - r], 1).astype(float), (a, l, t)

    def shape(self, s):
        buf = hb.Buffer(); buf.add_str(s); buf.guess_segment_properties()
        hb.shape(self.hbf, buf, {"kern": True, "liga": False})
        x = 0; out = []
        for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
            out.append((info.codepoint, x + pos.x_offset, pos.y_offset)); x += pos.x_advance
        return out


def _edge(pts):
    """Edge points of a point cloud on the integer grid."""
    x0, y0 = pts.min(0).astype(int); x1, y1 = pts.max(0).astype(int)
    g = np.zeros((y1 - y0 + 3, x1 - x0 + 3), bool)
    g[(pts[:, 1] - y0 + 1).astype(int), (pts[:, 0] - x0 + 1).astype(int)] = True
    e = g & ~ndi.binary_erosion(g)
    r, c = np.nonzero(e)
    return np.stack([c + x0 - 1, r + y0 - 1], 1).astype(float)


def nearest(F, pair, which, dx=0.0, sh=None, what=True):
    """Distance from the mark of pair[which] to the whole ink of the other glyph, in font units,
    with the second glyph moved `dx` further right. (distance, 'mark'|'letter') or None."""
    if len(pair) != 2 or not F.has(pair): return None
    sh = sh or F.shape(pair)
    if len(sh) != 2: return None
    ch = pair[which]; me = F.mark_edge(ch)
    if me is None: return None
    (g0, x0, y0), (g1, x1, y1) = sh
    x1 = x1 + dx
    mx, my = (x0, y0) if which == 0 else (x1, y1)
    og, ox, oy = (g1, x1, y1) if which == 0 else (g0, x0, y0)
    tr = F.tree(og)
    if tr is None: return None
    tree, (a, l, t) = tr
    rel = me + [mx - ox, my - oy]                       # the mark's edge in the neighbor's own frame
    # inside test: any mark point that falls on the neighbor's ink
    m = F.mark(ch)
    cx = np.round(m[:, 0] + mx - ox - l).astype(int); cy = np.round(t - (m[:, 1] + my - oy)).astype(int)
    ok = (cx >= 0) & (cx < a.shape[1]) & (cy >= 0) & (cy < a.shape[0])
    d = 0.0 if (ok.any() and a[cy[ok], cx[ok]].any()) else float(tree.query(rel, k=1)[0].min())
    if not what: return d, None
    # what the nearest point belongs to: the neighbor's mark, if it has one and the point is on it
    kind = "letter"
    oe = F.mark_edge(pair[1 - which])
    if oe is not None:
        dm = float(cKDTree(oe).query(rel, k=1)[0].min())
        if dm <= d + 1.0: kind = "mark"
    return d, kind


def survey(F, pairs, counts):
    """[(near/xh, what, pair, count, which)] for every mark in every pair."""
    rows = []
    for p in pairs:
        for w in (0, 1):
            if not accented(p[w]): continue
            r = nearest(F, p, w)
            if r is None: continue
            g = F.own(p[w])
            rows.append((r[0] / F.xh, r[1], p, counts.get(p, 0), w, (r[0] / g) if g and g > 4 else None))
    return rows


def opening(F, pair, which, floor, sh):
    """The extra kern (font units, >= 0) that takes the mark of pair[which] to `floor` from its
    neighbor: 0 when it is already there. Bisection on the second glyph's shift; the distance
    does not fall as two neighbors move apart."""
    r = nearest(F, pair, which, 0.0, sh, what=False)
    if r is None or r[0] >= floor: return 0
    lo, hi = 0.0, 64.0
    while nearest(F, pair, which, hi, sh, what=False)[0] < floor:
        lo, hi = hi, hi * 2
        if hi > 2048: return None
    while hi - lo > 0.5:
        mid = (lo + hi) / 2
        if nearest(F, pair, which, mid, sh, what=False)[0] < floor: lo = mid
        else: hi = mid
    return int(math.ceil(hi))


def clear(build, K, cuts, dry=False):
    """THE 2-D MARK CLEARANCE (round 453). For every pair the composite sweep covers (an
    accented letter with a mark ABOVE beside any of cmp_touch.composite_neighbors), where the
    mark comes nearer its neighbor than K x its own gap to its own letter, add the kern that
    takes it to exactly that, into ALBO_SPACING_TABLES' "clearance_composite" block -- the same
    block local_ai/clearance.py --composites writes, applied by kern.py after the inheritance.
    Iterate with a rebuild, alongside clearance.py, until both add nothing.

    K = 0.95 by default, since round 456 (owner 2026-10-01, on the italic í? he had opened +9 on
    the words bench, which read 0.95 of the acute's gap: "B is fine" -- the rule raised for every
    mark rather than the one pair pinned). Round 453 shipped 0.8: beside a T, V, W, Y or F,
    Pagella and Coelacanth bring no mark closer than 0.83 and 0.78 of its own gap (Times 0.92;
    Georgia 0.47, Flanker 0.16 at its T). 1.0 was built first and rejected: in the Bold Italic it
    pushed Wö and Fö to POSITIVE kerns (+19, +14). docs/albo-round-453-2026-09-30.md has the
    measurements; docs/albo-round-456-2026-10-01.md the raise.

    WATCH THE READER'S KERN CLASSES. fontconvert_sdcard.py folds the pairs into classes by
    identical rows and columns, and over 255 either way it DROPS THE STYLE'S KERNING ENTIRELY
    (a warning, no error). Each explicit pair here can split a class: K=0.8 took the Italic
    from 86/106 to 106/150, K=1.0 to 119/169."""
    import json
    sys.path.insert(0, os.path.join(os.path.dirname(HERE), "local_ai"))
    import b2_fit, cmp_touch
    data = json.load(open(b2_fit.OUT)); clr = data.setdefault("clearance_composite", {})
    added = 0
    for cut in cuts:
        path = os.path.join(build, f"Albo-{cut}.ttf"); F = Font(path)
        comp = cmp_touch.composite_chars(path)
        acc = {c for c in comp if F.above(c) and F.own(c)}
        nbs = [c for c in dict.fromkeys(cmp_touch.composite_neighbors(comp) + sorted(comp)) if F.has(c)]
        seen = set(); n = 0; rows = []
        for x in sorted(acc):
            for y in nbs:
                for pair in (x + y, y + x):
                    if pair in seen: continue
                    seen.add(pair)
                    sx, sy = cmp_touch.script(pair[0]), cmp_touch.script(pair[1])
                    if sx and sy and sx != sy: continue
                    sh = F.shape(pair)
                    if len(sh) != 2: continue
                    need = 0
                    for w in (0, 1):
                        if pair[w] not in acc: continue
                        k = opening(F, pair, w, K * F.own(pair[w]) + 1.0, sh)
                        if k is None: print(f"  {cut:10s} {pair}  no opening clears it under 2048 units"); continue
                        need = max(need, k)
                    n += 1
                    if need > 0:
                        cm = F.t.getBestCmap(); key = cm[ord(pair[0])] + " " + cm[ord(pair[1])]
                        rows.append((need, pair, key))
        for need, pair, key in sorted(rows, reverse=True):
            print(f"  {cut:10s} {pair}  +{need}")
            if not dry: clr.setdefault(cut, {})[key] = clr.get(cut, {}).get(key, 0) + need
        added += len(rows)
        print(f"  {cut}: {n} pairs swept, {len(rows)} under K={K} of the mark's own gap")
    if not dry:
        json.dump(data, open(b2_fit.OUT, "w"), indent=1, ensure_ascii=False, sort_keys=True)
    print(f"{added} 2-D mark clearance kern(s) {'needed' if dry else 'added to ' + os.path.basename(b2_fit.OUT)}")


def zoom(out, pairs, paths, scale=0.5):
    """Each pair in each font, the mark in red, the nearest approach drawn as a blue segment,
    one row per font: a picture of what the numbers measure."""
    from PIL import Image, ImageDraw, ImageFont
    lab = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)
    rows = []
    for spec in paths:
        label, path = spec.split("::", 1) if "::" in spec else (None, spec)
        F = Font(path); cells = []
        for p in pairs:
            sh = F.shape(p) if F.has(p) else []
            if len(sh) != 2: continue
            k = 429.0 / F.xh * scale          # every font at Albo's x-height, `scale` px per Albo unit
            g1, x1, _ = sh[1]; a1, l1, _t = F.glyph(g1)
            span = (x1 + l1 + a1.shape[1]) * 429.0 / F.xh       # the pair's ink, in Albo units
            Wc, Hc = int((span + 240) * scale), int(1150 * scale); base = int(880 * scale); x00 = int(120 * scale)
            im = Image.new("RGB", (Wc, Hc), (250, 249, 245)); d = ImageDraw.Draw(im)
            best = None
            for i, (g, x, y) in enumerate(sh):
                a, l, t = F.glyph(g)
                if not a.size: continue
                ink = F.ink(g)[0] if True else None
                rr, cc = np.nonzero(a)
                X = (cc + l + x) * k + x00; Y = base - (t - rr + y) * k
                ch = p[i]; m = F.mark(ch)
                col = np.array([30, 30, 30])
                arr = np.array(im)
                xi = np.clip(X.astype(int), 0, Wc - 1); yi = np.clip(Y.astype(int), 0, Hc - 1)
                arr[yi, xi] = col
                if m is not None:
                    mx = np.clip(((m[:, 0] + x) * k + x00).astype(int), 0, Wc - 1); my = np.clip((base - (m[:, 1] + y) * k).astype(int), 0, Hc - 1)
                    arr[my, mx] = [200, 40, 30]
                im = Image.fromarray(arr); d = ImageDraw.Draw(im)
            for w in (0, 1):
                if not accented(p[w]) or F.mark_edge(p[w]) is None: continue
                (g0, x0, y0), (g1, x1, y1) = sh
                mxy = (x0, y0) if w == 0 else (x1, y1); og, ox, oy = (g1, x1, y1) if w == 0 else (g0, x0, y0)
                tree, _ = F.tree(og); me = F.mark_edge(p[w]) + [mxy[0] - ox, mxy[1] - oy]
                dd, ii = tree.query(me, k=1); j = int(np.argmin(dd))
                q = tree.data[ii[j]]
                P1 = ((me[j, 0] + ox) * k + x00, base - (me[j, 1] + oy) * k); P2 = ((q[0] + ox) * k + x00, base - (q[1] + oy) * k)
                d.line([P1, P2], fill=(30, 90, 220), width=3)
                v = float(dd[j]); g = F.own(p[w])
                txt = f"{v / F.xh:.3f} xh" + (f" = {v / g:.2f} x own gap" if g else "")
                d.text((6, 6 + 24 * w), txt, fill=(30, 90, 220), font=lab)
            cells.append(im)
        if not cells: continue
        strip = Image.new("RGB", (sum(c.width for c in cells) + 160, cells[0].height), (250, 249, 245))
        ImageDraw.Draw(strip).text((8, strip.height // 2 - 10), label or F.name.replace(".ttf", "").replace(".otf", "")[:16], fill=(30, 30, 30), font=lab)
        x = 160
        for c in cells: strip.paste(c, (x, 0)); x += c.width
        rows.append(strip)
    o = Image.new("RGB", (max(r.width for r in rows), sum(r.height for r in rows)), (250, 249, 245)); y = 0
    for r in rows: o.paste(r, (0, y)); y += r.height
    o.save(out); print(out, o.size)


def main():
    args = sys.argv[1:]; extra = DISPLAY; top = 25; only = False
    if '--zoom' in args:
        i = args.index('--zoom'); out = args[i + 1]; pairs = args[i + 2].split(); del args[i:i + 3]
        return zoom(out, pairs, args)
    if '--clear' in args:
        i = args.index('--clear'); build = args[i + 1]
        K = float(args[args.index('--k') + 1]) if '--k' in args else 0.95
        cuts = args[args.index('--cuts') + 1].split(',') if '--cuts' in args else ["Italic", "BoldItalic"]
        return clear(build, K, cuts, dry='--dry' in args)
    if '--pairs' in args:
        i = args.index('--pairs'); extra = args[i + 1]; del args[i:i + 2]; only = True
    if '--top' in args:
        i = args.index('--top'); top = int(args[i + 1]); del args[i:i + 2]
    disp = extra.split()
    cnt = corpus_pairs()
    corpus = [p for p in cnt if any(accented(c) for c in p)]
    for path in args:
        F = Font(path)
        print(f"\n{F.name}  (x-height {F.xh:.0f}/{F.upm})")
        d = {(p, w): (v, wh, q) for v, wh, p, n, w, q in survey(F, disp, cnt)}
        line = []
        for p in disp:
            vs = [d[(p, w)] for w in (0, 1) if (p, w) in d]
            if vs:
                v, wh, q = min(vs, key=lambda t: t[0])
                line.append(f"{p} {v:.3f}{'m' if wh == 'mark' else ''}" + (f"/{q:.2f}" if q is not None else ""))
        print("  display (x-height; m = nearest is the neighbor's mark; /r = that distance over the mark's own gap to its letter):")
        for i in range(0, len(line), 8): print("    " + "   ".join(line[i:i + 8]))
        if only: continue
        rows = survey(F, corpus, cnt)
        tot = sum(r[3] for r in rows)
        if not tot: continue
        vs = np.array([r[0] for r in rows]); ns = np.array([r[3] for r in rows], float)
        qs = np.array([np.nan if r[5] is None else r[5] for r in rows])
        o = np.argsort(vs); cum = np.cumsum(ns[o]) / ns.sum(); med = vs[o][np.searchsorted(cum, 0.5)]
        share = lambda t: ns[vs < t].sum() / tot * 100
        print(f"  corpus: {len(rows)} marks in {len(corpus)} pairs, {int(tot)} occurrences;"
              f" under 0.10 {share(0.10):.1f}%  0.15 {share(0.15):.1f}%  0.20 {share(0.20):.1f}%  0.25 {share(0.25):.1f}%;  median {med:.3f}")
        qshare = lambda t: ns[np.nan_to_num(qs, nan=9) < t].sum() / tot * 100
        print(f"  nearer the neighbor than {'':0s}its own letter, x its own gap: under 1.0 {qshare(1.0):.1f}%  0.75 {qshare(0.75):.1f}%  0.5 {qshare(0.5):.1f}%")
        close = sorted([r for r in rows if r[3] >= 3], key=lambda r: r[0])[:top]
        print("  closest (pairs occurring 3+ times): " + "  ".join(f"{p}{'¹' if w == 0 else '²'} {v:.3f}{'m' if wh == 'mark' else ''} ({n})" for v, wh, p, n, w, q in close))


if __name__ == '__main__':
    main()
