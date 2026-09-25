"""The '&''s top-right terminal: how far right past the body, and how high -- round 383.

Owner 2026-09-24, on round 381's italic ampersand: *"the top right stroke of
italic ampersand is too long and tall."* This measures that stroke, and the
equivalent terminal on the reference italics, the same way on each.

Every glyph is rasterised at one x-height (the face's own 'x' ink) and
unsheared by its face's slant, so a lean is not read as reach. Then, in
x-heights from the baseline and from the ink's left edge:

  rtop    the top of the ink in the RIGHT HALF of the letter -- the terminal's
          height (for an Et, the t-stroke / curl; for a garalde &, the arm)
  rtop/c  the same over the face's cap height ('H' ink)
  ltop    the top of the LEFT half -- the E's head or the loop; `rtop - ltop`
          is how far the terminal stands above the rest of the letter
  ttop    the top of the ink strictly RIGHT of `body` -- the terminal's own
          height, with no E head in it (`ttop/c` over the cap)
  body    the rightmost ink below 0.5 xh -- the lower bowl's right side
  reach   the rightmost ink anywhere, minus `body`: how far the letter runs
          right past its bowl
  wid     the whole ink width

    PYTHON_GIL=0 python3 instruments/amp_reach.py [--refs] [FONT.ttf@slant ...]

Poetica's `ampersand.alt051` -- the ruled form's source -- is drawn from the
glyph by name (it has no codepoint), unsheared by Poetica's measured 9.2.
"""
import argparse, math, os, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from amp_measure import _ink, _box, size_for_xh, SYSTEM, _slant_l
import refs_registry as RR

PX = 300


def _metrics(mask_amp, base, xh, cap):
    x0, x1, y0, y1 = _box(mask_amp)
    mid = (x0 + x1) / 2.0
    cols = np.arange(mask_amp.shape[1])
    right = mask_amp & (cols[None, :] >= mid)
    left = mask_amp & (cols[None, :] < mid)
    top = lambda m: base - np.nonzero(m.any(1))[0].min()
    lowrows = np.arange(mask_amp.shape[0]) > base - 0.5 * xh
    low = mask_amp & lowrows[:, None]
    body = np.nonzero(low.any(0))[0].max()
    # THE TERMINAL ITSELF: ink strictly right of the lower bowl. The right HALF
    # also catches an E's head that crosses the midline (Flanker reads 1.36 on
    # it), so the terminal's own height is taken here.
    term = mask_amp & (cols[None, :] > body)
    ttop = top(term) if term.any() else float("nan")
    return dict(rtop=top(right) / xh, rtopc=top(right) / cap, ltop=top(left) / xh,
                ttop=ttop / xh, ttopc=ttop / cap,
                body=(body - x0) / xh, reach=(x1 - 1 - body) / xh, wid=(x1 - x0) / xh)


def measure_font(path, idx, slant):
    size, _ = size_for_xh(path, idx, PX)
    xa, base = _ink(path, idx, "x", size, slant); _, _, a, b = _box(xa); xh = b - a
    ha, _ = _ink(path, idx, "H", size, slant); _, _, a, b = _box(ha); cap = b - a
    m, base = _ink(path, idx, "&", size, slant)
    return _metrics(m, base, xh, cap)


def measure_alt051():
    from fontTools.ttLib import TTFont
    from fontTools.pens.basePen import BasePen
    p = RR.path("Poetica"); f = TTFont(p); gs = f.getGlyphSet()
    size, _ = size_for_xh(p, 0, PX)
    sc = size / f["head"].unitsPerEm
    xa, base = _ink(p, 0, "x", size, RR.slant("Poetica")); _, _, a, b = _box(xa); xh = b - a
    ha, _ = _ink(p, 0, "H", size, RR.slant("Poetica")); _, _, a, b = _box(ha); cap = b - a

    class P(BasePen):
        def __init__(s, g): super().__init__(g); s.polys = []; s.cur = []
        def _moveTo(s, q): s.cur = [q]
        def _lineTo(s, q): s.cur.append(q)
        def _curveToOne(s, c1, c2, e):
            q0 = s.cur[-1]
            for i in range(1, 17):
                t = i / 16; u = 1 - t
                s.cur.append(tuple(u**3*q0[j] + 3*u*u*t*c1[j] + 3*u*t*t*c2[j] + t**3*e[j] for j in (0, 1)))
        def _closePath(s): s.polys.append(s.cur); s.cur = []
    pen = P(gs); gs["ampersand.alt051"].draw(pen)
    sh = math.tan(math.radians(RR.slant("Poetica")))
    W = H = int(size * 3.2); b0 = int(H * 0.66)
    acc = np.zeros((H, W), bool)
    for poly in pen.polys:
        im = Image.new("1", (W, H), 0)
        ImageDraw.Draw(im).polygon([(W * 0.3 + (x - sh * y) * sc, b0 - y * sc) for x, y in poly], fill=1)
        acc ^= np.asarray(im, bool)
    return _metrics(acc, b0, xh, cap)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("fonts", nargs="*"); ap.add_argument("--refs", action="store_true")
    a = ap.parse_args()
    rows = []
    for spec in a.fonts:
        sl = 13.0
        if "@" in spec: spec, sl = spec.rsplit("@", 1); sl = float(sl)
        rows.append((os.path.basename(os.path.dirname(spec)) + "/" + os.path.basename(spec), measure_font(spec, 0, sl)))
    if a.refs:
        for n in ("Flanker Griffo", "Pagella", "Poetica", "Coelacanth"):
            rows.append((n, measure_font(RR.path(n), 0, RR.slant(n))))
        rows.append(("Poetica alt051", measure_alt051()))
        for n, p, i in SYSTEM:
            rows.append((n, measure_font(p, i, _slant_l(p, i))))
    print(f"{'face':34s} {'rtop':>5s} {'rtop/c':>6s} {'ltop':>5s} {'r-l':>5s} {'ttop':>5s} {'ttop/c':>6s} {'body':>5s} {'reach':>5s} {'wid':>5s}")
    for n, r in rows:
        print(f"{n[-34:]:34s} {r['rtop']:5.2f} {r['rtopc']:6.2f} {r['ltop']:5.2f} "
              f"{r['rtop']-r['ltop']:+5.2f} {r['ttop']:5.2f} {r['ttopc']:6.2f} "
              f"{r['body']:5.2f} {r['reach']:5.2f} {r['wid']:5.2f}", flush=True)


if __name__ == "__main__":
    main()
