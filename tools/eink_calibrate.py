#!/usr/bin/env python3
"""Measure an e-paper panel's GHOST from photographs, for src/EinkPanel.h.

E-ink mode's ghost plane is phenomenological and its three constants were
TUNED, NOT MEASURED (docs/eink-mode-spike-2026-09-25.md, section 1.4):

    kResidueToWhite  (residueToWhite())  ink a pixel keeps when it turns paper
    kResidueToBlack                      paper a pixel keeps when it turns ink
    kKeep                                how much ghost survives each partial

This tool reads them off photographs of a real panel. The full procedure --
what to photograph, in what order, and how -- is section 7 of that doc. In
short, three pages A, B, C, every photo taken from a tripod with the same
framing and locked exposure:

    prev     page A, just after a FULL/HALF refresh (clean)
    clean    page B, just after a FULL/HALF refresh (clean)
    ghosted  page B, reached from A by exactly ONE partial (page turn)
    later    (optional) page B again, after M more partials that went away
             from B and came back (B -> C -> B ... ), with --later-partials M

    tools/eink_calibrate.py PREV CLEAN GHOSTED [--later IMG --later-partials M]
                            [--crop x,y,w,h] [--third C_CLEAN]

It prints the three constants to paste. The masks are built from the CLEAN
photos, eroded so a one- or two-pixel misregistration cannot put a glyph edge
into the measurement, and every image is normalized to its OWN paper and ink
(measured on pixels those pages agree on), so a small exposure drift between
shots does not read as ghost.

    tools/eink_calibrate.py --selftest   # synthetic panel with known residues
"""

import argparse
import sys

import numpy as np
from PIL import Image

EROSION = 2  # px each way the masks are shrunk
MIN_PIXELS = 200


def load(path, crop, size=None):
    im = Image.open(path).convert("L")
    if crop:
        x, y, w, h = crop
        im = im.crop((x, y, x + w, y + h))
    if size and im.size != size:
        im = im.resize(size, Image.BILINEAR)
    return np.asarray(im, dtype=np.float64) / 255.0


def erode(mask, r=EROSION):
    out = mask.copy()
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            out &= np.roll(np.roll(mask, dy, 0), dx, 1)
    # np.roll wraps; the border is never trustworthy anyway
    out[:r, :] = out[-r:, :] = False
    out[:, :r] = out[:, -r:] = False
    return out


def ink_mask(img):
    """Ink = darker than the midpoint between this page's paper and ink."""
    lo, hi = np.percentile(img, 2), np.percentile(img, 98)
    return img < (lo + hi) / 2


def normalize(img, paper_px, ink_px):
    """Map this image so its paper reads 1 and its ink 0, from reference pixels
    whose state is known (paper in every page / ink in the photographed page)."""
    p = np.median(img[paper_px])
    k = np.median(img[ink_px])
    if p - k < 0.05:
        raise SystemExit("paper and ink are within 5% -- exposure or crop is wrong")
    return (img - k) / (p - k)


def measure(prev, clean, ghosted, later=None, later_partials=0, third=None):
    a_ink = ink_mask(prev)
    b_ink = ink_mask(clean)
    paper_all = erode(~a_ink & ~b_ink)
    b_ink_core = erode(b_ink)
    # ghost-to-white: ink on A, paper on B (and on C, when given)
    to_white = erode(a_ink) & erode(~b_ink)
    if third is not None:
        c_ink = ink_mask(third)
        to_white &= erode(~c_ink)
        paper_all &= erode(~c_ink)
    to_black = erode(~a_ink) & b_ink_core
    # The ink REFERENCE must be ink on BOTH pages: pixels that turned ink carry
    # the to-black residue, and normalizing by them would divide it away (the
    # selftest read 0.018 for a true 0.025 until this was split out).
    ink_ref = erode(a_ink & b_ink)
    for name, m in (("paper-in-every-page", paper_all), ("ink-on-A-and-B", ink_ref),
                    ("A-ink/B-paper", to_white),
                    ("A-paper/B-ink", to_black)):
        if m.sum() < MIN_PIXELS:
            raise SystemExit(f"only {int(m.sum())} {name} pixels; pick pages "
                             "with more text, or a larger crop")
    c = normalize(clean, paper_all, ink_ref)
    g = normalize(ghosted, paper_all, ink_ref)
    # A ghost on paper is DARKER than the clean page there; on ink, LIGHTER.
    r_white = float(np.mean(c[to_white] - g[to_white]))
    r_black = float(np.mean(g[to_black] - c[to_black]))
    out = {"residue_to_white": r_white, "residue_to_black": r_black,
           "n_white": int(to_white.sum()), "n_black": int(to_black.sum())}
    if later is not None and later_partials > 0:
        lt = normalize(later, paper_all, ink_ref)
        r_later = float(np.mean(c[to_white] - lt[to_white]))
        out["residue_later"] = r_later
        # EinkPanel.h: g <- g*kKeep on every partial that does not re-drive the
        # pixel, so M partials later the ghost is r * kKeep^M.
        out["keep"] = (max(r_later, 1e-9) / max(r_white, 1e-9)) ** (1.0 / later_partials)
    return out


def report(res, file=sys.stdout):
    p = lambda *a: print(*a, file=file)
    p(f"ghost to white (A ink -> B paper, {res['n_white']} px): "
      f"{res['residue_to_white']:.4f} of a full swing "
      f"= {res['residue_to_white'] * 255:.1f} levels")
    p(f"ghost to black (A paper -> B ink, {res['n_black']} px): "
      f"{res['residue_to_black']:.4f} = {res['residue_to_black'] * 255:.1f} levels")
    if "keep" in res:
        p(f"after the later partials the ghost is {res['residue_later']:.4f}; "
          f"per-partial keep {res['keep']:.4f}")
    p("")
    p("paste into src/EinkPanel.h (currently 0.030 / 0.015 / 0.92, tuned):")
    p(f"  inline double residueToWhite() {{ return {max(res['residue_to_white'], 0):.3f}; }}")
    p(f"  constexpr double kResidueToBlack = {max(res['residue_to_black'], 0):.3f};")
    if "keep" in res:
        p(f"  constexpr double kKeep = {min(max(res['keep'], 0), 1):.3f};")
    else:
        p("  kKeep: not measured (pass --later and --later-partials)")
    if res["residue_to_white"] < 0 or res["residue_to_black"] < 0:
        p("WARNING: a NEGATIVE residue means the ghosted photo is cleaner than "
          "the clean one -- check the photo order and the exposure lock.")


def selftest():
    """A synthetic panel with KNOWN residues, photographed with exposure drift,
    sensor noise and a 1 px misregistration; the tool must recover them."""
    rng = np.random.default_rng(7)
    H, W = 240, 320

    def text(seed):
        r = np.random.default_rng(seed)
        m = np.zeros((H, W), bool)
        for y in range(10, H - 20, 24):
            x = 8
            while x < W - 30:
                w = int(r.integers(8, 28))
                m[y:y + 12, x:x + w] = True  # a word as a solid bar: real strokes are several photo px wide
                x += w + int(r.integers(6, 14))
        return m

    A, B, C = text(1), text(2), text(3)
    rw, rb, keep, M = 0.06, 0.025, 0.85, 4
    paper, ink = 0.82, 0.12

    def photo(state, gain, shift=(0, 0)):
        img = ink + (paper - ink) * state
        img = img * gain + rng.normal(0, 0.006, img.shape)
        img = np.roll(np.roll(img, shift[0], 0), shift[1], 1)
        return np.clip(img, 0, 1)

    base = lambda m: np.where(m, 0.0, 1.0)
    ghost1 = base(B) - rw * (A & ~B) + rb * (~A & B)
    ghostM = base(B) - rw * keep ** M * (A & ~B & ~C) + rb * keep ** M * (~A & B)
    res = measure(photo(base(A), 1.00), photo(base(B), 1.03),
                  photo(ghost1, 0.97, (1, 0)), photo(ghostM, 1.01, (0, 1)), M,
                  third=photo(base(C), 0.99))
    ok = (abs(res["residue_to_white"] - rw) < 0.006 and
          abs(res["residue_to_black"] - rb) < 0.006 and
          abs(res["keep"] - keep) < 0.03)
    report(res)
    print(f"selftest: truth {rw} / {rb} / {keep}: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("prev", nargs="?", help="page A, clean")
    ap.add_argument("clean", nargs="?", help="page B, clean")
    ap.add_argument("ghosted", nargs="?", help="page B after ONE partial from A")
    ap.add_argument("--later", help="page B after --later-partials more partials")
    ap.add_argument("--later-partials", type=int, default=0)
    ap.add_argument("--third", help="page C (the away page), clean")
    ap.add_argument("--crop", help="x,y,w,h applied to every photo")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not (a.prev and a.clean and a.ghosted):
        ap.error("PREV CLEAN GHOSTED are required (or --selftest)")
    crop = tuple(int(v) for v in a.crop.split(",")) if a.crop else None
    clean = load(a.clean, crop)
    size = (clean.shape[1], clean.shape[0])
    res = measure(load(a.prev, crop, size), clean, load(a.ghosted, crop, size),
                  load(a.later, crop, size) if a.later else None,
                  a.later_partials,
                  load(a.third, crop, size) if a.third else None)
    report(res)
    return 0


if __name__ == "__main__":
    sys.exit(main())
