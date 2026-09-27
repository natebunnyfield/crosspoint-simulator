"""The white a redrawn glyph leaves on its commonest pairs, arm against today
(the poor-characters pass, 2026-09-26; docs/albo-poor-characters-2026-09-26.md).

B2 spacing was fitted on today's shapes, so an arm that changes a letter's ink
changes the white on every pair it is in -- through its new sidebearings (the
bearing rule re-derives them from the new ink) and through the ink itself.
This reports, per pair, the white as SET (HarfBuzz advance + GPOS kern, the
arm's own tables), two ways, both in font units:

  min   the closest horizontal approach of the two inks, row by row over the
        whole height (a hook tucking under the letter before it shows here)
  band  the mean horizontal white over the rows where BOTH glyphs have ink
        inside the x-height band (baseline to x-height), clipped at 0.6 of the
        band as the fit audit's bearings axis is -- the white the eye reads

  box   the gap between the two inks' whole extents (negative = one reaches
        past the other: a j's hook under the a before it)

and the change arm - today. It deliberately does NOT refit anything.

    python3 instruments/poor_pairs.py TODAY.ttf ARM.ttf --pairs "aj ej oj ju"
    python3 instruments/poor_pairs.py TODAY.ttf ARM.ttf --char j --top 8   # corpus pairs
"""
import argparse, collections, json, os, sys
import numpy as np
import freetype
import uharfbuzz as hb

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.dirname(HERE)


class Ink:
    def __init__(self, path):
        self.face = freetype.Face(path)
        self.upm = self.face.units_per_EM
        self.face.set_char_size(self.upm * 64, 0, 72, 72)      # 1 px = 1 unit
        self.hbf = hb.Font(hb.Face(hb.Blob.from_file_path(path)))
        self.cache = {}

    def rows(self, gid):
        """{y: (xmin, xmax)} of the glyph's ink, glyph origin at 0."""
        if gid not in self.cache:
            self.face.load_glyph(gid, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING)
            b = self.face.glyph.bitmap
            r = {}
            if b.rows:
                a = np.frombuffer(bytes(b.buffer), np.uint8).reshape(b.rows, b.pitch)[:, :b.width] >= 128
                left, top = self.face.glyph.bitmap_left, self.face.glyph.bitmap_top
                for i in range(a.shape[0]):
                    xs = np.nonzero(a[i])[0]
                    if len(xs): r[top - i] = (left + xs[0], left + xs[-1] + 1)
            self.cache[gid] = r
        return self.cache[gid]

    def pair(self, s, xh=429):
        buf = hb.Buffer(); buf.add_str(s); buf.guess_segment_properties()
        hb.shape(self.hbf, buf, {"kern": True, "liga": False})
        (g0, g1), (p0, p1) = [i.codepoint for i in buf.glyph_infos], buf.glyph_positions
        off = p0.x_advance + p1.x_offset - p0.x_offset
        A, B = self.rows(g0), self.rows(g1)
        common = [y for y in A if y in B]
        box = (min(v[0] for v in B.values()) + off) - max(v[1] for v in A.values())
        if not common: return float("nan"), float("nan"), float(box)
        gaps = {y: (B[y][0] + off) - A[y][1] for y in common}
        mn = min(gaps.values())
        band = [min(g, 0.6 * xh) for y, g in gaps.items() if 0 <= y <= xh]
        return float(mn), float(np.mean(band)) if band else float("nan"), float(box)


def corpus_pairs(ch, top):
    words = json.load(open(os.path.join(WS, ".corpus_words.json")))
    c = collections.Counter()
    up = ch.isupper()
    for w, n in words.items():
        if up:                                    # a capital: the word's first letter, then the next
            if w and w[0] == ch.lower() and len(w) > 1: c[ch + w[1]] += n
            continue
        for i in range(len(w) - 1):
            if ch in w[i:i + 2]: c[w[i:i + 2]] += n
    return [p for p, _ in c.most_common(top)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("today"); ap.add_argument("arm")
    ap.add_argument("--pairs", default="")
    ap.add_argument("--char")
    ap.add_argument("--top", type=int, default=8)
    ap.add_argument("--json")
    a = ap.parse_args()
    pairs = a.pairs.split() or corpus_pairs(a.char, a.top)
    T, R = Ink(a.today), Ink(a.arm)
    out = {}
    for p in pairs:
        (m0, b0, x0), (m1, b1, x1) = T.pair(p), R.pair(p)
        out[p] = dict(min0=m0, min1=m1, band0=b0, band1=b1, box0=x0, box1=x1)
        print(f"  {p}: min {m0:6.1f} -> {m1:6.1f} ({m1 - m0:+5.1f})   band {b0:6.1f} -> {b1:6.1f} ({b1 - b0:+5.1f})"
              f"   box {x0:6.1f} -> {x1:6.1f} ({x1 - x0:+5.1f})")
    if a.json: json.dump(out, open(a.json, "w"), indent=1)


if __name__ == "__main__":
    main()
