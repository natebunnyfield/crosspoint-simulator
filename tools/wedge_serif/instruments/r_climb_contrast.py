# the ARM's own hairline, not the letter's p10: ridge thickness (cmp_weight_survey's raster,
# chamfer, ridge; unsheared at the font's slant) on the climb out of the stem -- ridge points
# between 0.50 and 0.80 xh, right of the (left) stem's ink, left of 60% of the ink width --
# for the r and for the n, the letter whose shoulder the r's arm was solved to match
import sys, os, numpy as np
sys.path.insert(0, os.path.expanduser("~/src/crosspoint-simulator/tools/wedge_serif"))
import cmp_weight_survey as W
def climb(path, ch, sl):
    m, base = W.raster(path, ch, sl); d = W.chamfer(m)
    p = np.pad(d, 1); c = p[1:-1, 1:-1]
    keep = (m & (d >= 1.5) & (c >= p[1:-1, :-2]) & (c >= p[1:-1, 2:]) & (c >= p[:-2, 1:-1]) & (c >= p[2:, 1:-1]))
    H, Wd = m.shape; u = W.XH / 380; px = 380
    ys, xs = np.nonzero(keep); y = (base - ys) / px          # in x-heights above the baseline
    # the left stem: ink columns at mid x-height
    row = m[int(base - 0.3 * px)]; ink = np.nonzero(row)[0]; stemR = ink[np.argmax(np.diff(ink) > 1)] if (np.diff(ink) > 1).any() else ink.max()
    xmax = np.nonzero(m.any(0))[0].max(); xmin = np.nonzero(m.any(0))[0].min()
    sel = (y > 0.50) & (y < 0.80) & (xs > stemR + 4) & (xs < xmin + 0.6 * (xmax - xmin))
    t = 2 * d[ys[sel], xs[sel]] * u
    st = 2 * d[keep & (np.arange(H)[:, None] > base - 0.45 * px) & (np.arange(H)[:, None] < base - 0.1 * px)] * u
    return np.min(t), np.percentile(t, 25), np.median(st)
for path in sys.argv[1:]:
    for ch in "rn":
        mn, p25, st = climb(path, ch, 13.0)
        print(f"{path.split('/')[-2]:8s} {ch}: climb min {mn:5.1f} p25 {p25:5.1f} | stem {st:5.1f} | stem/climb {st/p25:.2f}")
