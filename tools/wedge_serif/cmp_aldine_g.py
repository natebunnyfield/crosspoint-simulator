"""The binocular g's ANATOMY, measured the same way on a font and on a scan.

Owner 2026-09-16: *"do a better job connecting the ear of g, refer to scans and
reference fonts"*, then *"redo g based on flanker, pagella and the scan
detail"*.

WHY A RASTER AND NOT THE OUTLINE. The other Albo instruments measure outlines,
which is right when the reference is a font. Here one of the three references
is a photograph of a printed page, and a number that comes off a Bezier is not
comparable with one that comes off ink on paper unless both are measured by the
same procedure. So everything below is measured on a BITMAP at a fixed
x-height, whatever it was drawn from -- a font is rendered to one, a scan crop
is thresholded into one -- and the two then answer the same questions.

WHAT IT MEASURES, and why each survives:

  bowl / loop boxes     the two counters, found as the two largest enclosed
                        white regions. A binocular g IS its two counters; the
                        ink around them is what the pen did on the way.
  crown, foot           the letter's top and the loop's bottom
  neck                  the horizontal ink run at the height midway between
                        the bowl's counter floor and the loop's counter
                        ceiling -- the waist, where the two bowls are joined
                        by one stroke and nothing else is in the way
  ear reach / depth     ink to the RIGHT of the bowl's counter, which is the
                        only part of the ear that is not also the bowl
  ear angle             the slope of the ear's own centre line over its reach

    PYTHON_GIL=0 python3 cmp_aldine_g.py                 # every reference + Albo
    PYTHON_GIL=0 python3 cmp_aldine_g.py --ttf X.ttf     # one font
    PYTHON_GIL=0 python3 cmp_aldine_g.py --png out.png   # contact sheet
"""
import argparse, math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
REFS = os.path.join(HERE, "refs")
MACRO = os.path.expanduser("~/Downloads/griffo-macro.png")
# The g of "rodigium", located by eye on the macro's fourth line -- the same
# line aldine_autofit.SOURCES takes its i from, so the x-height is that line's
# 56 px.
#
# THE CROP STOPS AT x 271 AND THAT COSTS THE EAR. In the printed word the g's
# ear runs right out of the bowl's top and TOUCHES THE FOLLOWING i, which
# descends from the x-line to the baseline right where the ear is going. On the
# page they are one blob of ink. A crop wide enough to hold the whole ear holds
# most of an i with it -- measured that way the g came out 756 units wide with
# a 304-unit "ear", which is an i. So the scan is asked only what it can answer
# alone: the two counters, the neck, and the four stroke weights. The EAR's
# reach, depth and angle come from Flanker and Pagella, which are outlines and
# have no neighbour touching them. That is a limit of this evidence, not a
# judgment about the ear.
SCAN_G = (MACRO, (220, 486, 271, 600), 56.0, 'macro, "rodigium"')
XH = 429.0                      # every number below is in Albo's design units


def _otsu(a):
    hist = np.bincount(a.ravel(), minlength=256).astype(float)
    tot = hist.sum(); w = np.cumsum(hist); m = np.cumsum(hist * np.arange(256))
    with np.errstate(invalid="ignore", divide="ignore"):
        b = (m[-1] * w / tot - m) ** 2 / (w * (tot - w))
    b[~np.isfinite(b)] = -1
    return int(np.argmax(b))


def _components(mask):
    """4-connected components of a boolean mask, largest first. Iterative --
    a flood over a 900-px letter recurses into the tens of thousands."""
    seen = np.zeros(mask.shape, bool); out = []
    H, W = mask.shape
    for sy in range(H):
        for sx in range(W):
            if not mask[sy, sx] or seen[sy, sx]:
                continue
            st = [(sy, sx)]; seen[sy, sx] = True; pix = []
            while st:
                y, x = st.pop(); pix.append((y, x))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < H and 0 <= nx < W and mask[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True; st.append((ny, nx))
            out.append(pix)
    out.sort(key=len, reverse=True)
    return out


def ink_from_font(ttf, xh_px=900):
    """Render g so its x-height is xh_px, UNSHEARED, and return an ink mask
    plus the baseline and x-line rows."""
    from fontTools.ttLib import TTFont
    f = TTFont(ttf)
    upm = f["head"].unitsPerEm
    try: sx = f["OS/2"].sxHeight or upm * 0.5
    except Exception: sx = upm * 0.5
    ang = -getattr(f["post"], "italicAngle", 0.0)
    size = int(round(xh_px * upm / sx))
    fnt = ImageFont.truetype(ttf, size)
    W = H = size * 3
    im = Image.new("L", (W, H), 255)
    ImageDraw.Draw(im).text((W * 0.35, H * 0.62), "g", font=fnt, fill=0, anchor="ls")
    base = H * 0.62
    if abs(ang) > 0.05:        # unshear about the baseline
        k = math.tan(math.radians(ang))
        im = im.transform((W, H), Image.AFFINE, (1, k, -k * base, 0, 1, 0),
                          resample=Image.BICUBIC, fillcolor=255)
    a = np.asarray(im)
    return a < 128, base, base - xh_px, xh_px


def ink_from_scan(path, box, xh_px_src, xh_px=900):
    im = Image.open(path).convert("L").crop(box)
    sc = xh_px / xh_px_src
    im = im.resize((int(im.width * sc), int(im.height * sc)), Image.LANCZOS)
    a = np.asarray(im)
    mask = a < _otsu(a)
    # the crop is hand-located, so the x-line and baseline are found from the
    # BOWL: its counter's ceiling is the x-line less the bowl's own top stroke,
    # which is not knowable here -- so the scan reports every figure that does
    # not need them, and NaN for the two that do.
    return mask, None, None, xh_px


def anatomy(mask, base, xline, xh_px):
    """Every number in Albo design units (xh 429)."""
    u = XH / xh_px
    ys, xs = np.nonzero(mask)
    if not len(ys): return None
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    sub = mask[y0:y1 + 1, x0:x1 + 1]
    H, W = sub.shape
    # counters: enclosed white. Flood the background in from the border, and
    # whatever white is left is enclosed.
    white = ~sub
    bg = np.zeros_like(white); st = []
    for x in range(W):
        for y in (0, H - 1):
            if white[y, x] and not bg[y, x]: bg[y, x] = True; st.append((y, x))
    for y in range(H):
        for x in (0, W - 1):
            if white[y, x] and not bg[y, x]: bg[y, x] = True; st.append((y, x))
    while st:
        y, x = st.pop()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < H and 0 <= nx < W and white[ny, nx] and not bg[ny, nx]:
                bg[ny, nx] = True; st.append((ny, nx))
    holes = _components(white & ~bg)
    holes = [h for h in holes if len(h) > (xh_px * 0.02) ** 2]
    if len(holes) < 2: return None
    boxes = []
    for h in holes[:2]:
        hy = np.array([p[0] for p in h]); hx = np.array([p[1] for p in h])
        boxes.append((hy.min(), hy.max(), hx.min(), hx.max(), len(h)))
    boxes.sort(key=lambda b: b[0])          # topmost first: the bowl
    bowl, loop = boxes[0], boxes[1]
    R = {}
    R["h"] = (y1 - y0 + 1) * u
    R["w"] = (x1 - x0 + 1) * u
    R["bowl_ctr_w"] = (bowl[3] - bowl[2]) * u
    R["bowl_ctr_h"] = (bowl[1] - bowl[0]) * u
    R["loop_ctr_w"] = (loop[3] - loop[2]) * u
    R["loop_ctr_h"] = (loop[1] - loop[0]) * u
    R["ctr_ratio"] = (loop[3] - loop[2]) / max(1, (bowl[3] - bowl[2]))
    R["loop_over_bowl_h"] = (loop[1] - loop[0]) / max(1, (bowl[1] - bowl[0]))
    # the WAIST: the ink run on the row midway between the two counters
    wy = int((bowl[1] + loop[0]) / 2)
    row = np.nonzero(sub[wy])[0]
    if len(row):
        runs = np.split(row, np.where(np.diff(row) > 1)[0] + 1)
        R["waist_ink"] = max(len(r) for r in runs) * u
        R["waist_runs"] = len(runs)
    # the BOWL's stroke, left and right, on its counter's mid row
    by = int((bowl[0] + bowl[1]) / 2)
    row = np.nonzero(sub[by])[0]
    runs = np.split(row, np.where(np.diff(row) > 1)[0] + 1) if len(row) else []
    if len(runs) >= 2:
        R["bowl_left"] = len(runs[0]) * u
        R["bowl_right"] = len(runs[1]) * u
    # the LOOP's stroke the same way
    ly = int((loop[0] + loop[1]) / 2)
    row = np.nonzero(sub[ly])[0]
    runs = np.split(row, np.where(np.diff(row) > 1)[0] + 1) if len(row) else []
    if len(runs) >= 2:
        R["loop_left"] = len(runs[0]) * u
        R["loop_right"] = len(runs[-1]) * u
    # the EAR, anchored on the CROWN. The ear is not separable from the bowl
    # by any x threshold -- the bowl's own right flank lives to the right of
    # its counter, and on a face whose ear reaches far the ear IS the letter's
    # rightmost ink. So it is measured off the TOP PROFILE: the crown is where
    # the letter is highest, and everything right of the crown is ear. That is
    # also how it is read.
    top = np.full(W, -1)
    for c in range(W):
        r = np.nonzero(sub[:, c])[0]
        if len(r): top[c] = r.min()
    lit = np.nonzero(top >= 0)[0]
    crown_x = int(lit[np.argmin(top[lit])])
    R["crown_x_frac"] = crown_x / W
    # the ear runs from the crown to the last column that still has ink above
    # the bowl counter's floor
    ex = crown_x
    for c in range(crown_x, W):
        r = np.nonzero(sub[:bowl[1], c])[0]
        if not len(r):
            break
        ex = c
    R["ear_reach"] = (ex - crown_x) * u
    R["ear_drop"] = (top[ex] - top[crown_x]) * u if ex > crown_x else 0.0
    if ex > crown_x:
        R["ear_angle"] = -math.degrees(math.atan2(top[ex] - top[crown_x], ex - crown_x))
        deps = []
        for c in range(crown_x, ex + 1):
            r = np.nonzero(sub[:bowl[1], c])[0]
            if len(r): deps.append((r.max() - r.min() + 1) * u)
        if deps:
            R["ear_depth_mid"] = deps[len(deps) // 2]
            R["ear_depth_tip"] = deps[-1]
    R["_boxes"] = (bowl, loop, (y0, y1, x0, x1))
    return R


ROWS = [("h", "overall height"), ("w", "overall width"),
        ("bowl_ctr_w", "bowl counter w"), ("bowl_ctr_h", "bowl counter h"),
        ("loop_ctr_w", "loop counter w"), ("loop_ctr_h", "loop counter h"),
        ("ctr_ratio", "loop/bowl counter w"), ("loop_over_bowl_h", "loop/bowl counter h"),
        ("bowl_left", "bowl stroke L"), ("bowl_right", "bowl stroke R"),
        ("loop_left", "loop stroke L"), ("loop_right", "loop stroke R"),
        ("waist_ink", "neck ink at the waist"), ("waist_runs", "runs at the waist"),
        ("crown_x_frac", "crown x, frac of width"),
        ("ear_reach", "ear reach past the crown"),
        ("ear_drop", "ear drop below the crown"),
        ("ear_depth_mid", "ear depth, mid"), ("ear_depth_tip", "ear depth at its tip"),
        ("ear_angle", "ear top slope, deg (-ve = down)")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ttf", action="append", default=[])
    ap.add_argument("--png")
    ap.add_argument("--xh", type=int, default=900)
    a = ap.parse_args()
    subjects = []
    m, b, xl, xp = ink_from_scan(SCAN_G[0], SCAN_G[1], SCAN_G[2], xh_px=a.xh)
    subjects.append(("the scan (Griffo)", anatomy(m, b, xl, xp), m))
    fonts = a.ttf or [os.path.join(REFS, "flanker-griffo-italic.otf"),
                      os.path.join(REFS, "texgyrepagella-italic.otf"),
                      os.path.join(REFS, "cancelleresca-bastarda-beta12.otf")]
    labels = {"flanker-griffo-italic.otf": "Flanker Griffo",
              "texgyrepagella-italic.otf": "Pagella",
              "cancelleresca-bastarda-beta12.otf": "Cancelleresca"}
    for t in fonts:
        m, b, xl, xp = ink_from_font(t, a.xh)
        subjects.append((labels.get(os.path.basename(t), os.path.basename(t)),
                         anatomy(m, b, xl, xp), m))
    hdr = "  %-28s" % "" + "".join("%16s" % s[0] for s in subjects)
    print("\nthe binocular g, measured on a %d px x-height raster, in Albo units (xh %d)\n" % (a.xh, XH))
    print(hdr); print("  " + "-" * (28 + 16 * len(subjects)))
    for k, lab in ROWS:
        line = "  %-28s" % lab
        for _, r, _ in subjects:
            v = (r or {}).get(k)
            line += "%16s" % ("--" if v is None else ("%.2f" % v if abs(v) < 10 else "%.0f" % v))
        print(line)
    print()
    if a.png:
        tiles = []
        for lab, r, m in subjects:
            ys, xs = np.nonzero(m)
            im = Image.fromarray((~m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]).astype(np.uint8) * 255)
            im = im.resize((int(im.width * 380 / im.height), 380), Image.LANCZOS)
            tiles.append((im, lab))
        W = sum(t[0].width + 50 for t in tiles) + 50
        out = Image.new("L", (W, 460), 255); d = ImageDraw.Draw(out)
        uf = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 18)
        x = 40
        for im, lab in tiles:
            out.paste(im, (x, 20)); d.text((x, 425), lab, font=uf, fill=110); x += im.width + 50
        out.save(a.png); print("  wrote", a.png)


if __name__ == "__main__":
    main()
