#!/usr/bin/env python3
"""The ITALIC straight quote ' against the italic references (2026-09-26):
its profile down its own length -- width near the top, middle and foot, as a
fraction of the face's stem -- its lean from vertical, its height, and its
ink over an n. Owner: "make it [the straight italic apostrophe] match the
style better". Unhinted, 1000 ppem, via apos_measure's raster.

    python3 instruments/apos_italic_straight.py ALBO_ITALIC.ttf [...]
"""
import math, os, sys
import numpy as np, freetype
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import apos_measure as AM


def profile(name, path, idx=0):
    f = freetype.Face(path, index=idx); f.set_pixel_sizes(0, AM.PPEM)
    R = AM.measure(name, path, idx); xh, stem = R["xh"], R["stem_xh"] * R["xh"]
    m, top = AM.raster(f, "'")
    ys = np.nonzero(m.any(1))[0]; y0, y1 = ys[0], ys[-1]; H = y1 - y0 + 1
    def at(fr):
        y = int(y0 + fr * (H - 1)); xs = np.nonzero(m[y])[0]
        return (xs.max() - xs.min() + 1) / stem, (xs.max() + xs.min()) / 2
    w10, c10 = at(0.10); w50, c50 = at(0.50); w90, c90 = at(0.90)
    lean = math.degrees(math.atan2(c10 - c90, 0.8 * H))
    return dict(font=name, h=H / xh, top=w10, mid=w50, foot=w90, taper=w90 / w10 if w10 else 0,
                lean=lean, ink_n=R["straight_over_n"], cur_head=R["apos"]["head"])


def main():
    rows = [profile(f"Albo {os.path.basename(os.path.dirname(p)) or p}", p) for p in sys.argv[1:]]
    rows += [profile(*r) for r in AM.REFS_ITALIC if os.path.exists(r[1])]
    print("| font | height /xh | width @10% /stem | @50% | @90% | foot/top | lean deg | ink / n | (’ head /stem) |")
    print("|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        print(f"| {r['font']} | {r['h']:.3f} | {r['top']:.2f} | {r['mid']:.2f} | {r['foot']:.2f} | {r['taper']:.2f} | {r['lean']:.1f} | {r['ink_n']:.3f} | {r['cur_head']:.2f} |")


if __name__ == "__main__":
    main()
