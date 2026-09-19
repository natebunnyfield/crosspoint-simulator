"""Measure 5: the white between two letters, CLAMPED at the letter's own counter.

WHY A FIFTH MEASURE, when docs/albo-spacing-method.md is a record of three that
were wrong. Because the four that exist cannot both be right at once, and two
owner observations prove it:

  2026-09-17, on `Vi`: *"you need to have more optical space between Vi."* The
      MEAN gap across the band had just tightened it, counting the V's splay as
      spacing. So far white does NOT count in full. (Measure 2's failure.)

  2026-09-19, on a rendered paragraph: *"about"* reads as *"a bout"*,
      *"capitals"* as *"capita ls"*, *"the"* as *"t he"*, *"between"* as
      *"bet ween"* -- at 13 px AND at 40 px, so it is fitting. The MINIMUM white
      and the 2-D closest approach both call `ab` and `nb` the same pair,
      because the a's right stem and the n's right stem stand in the same place
      and the difference is the open white ABOVE the a's bowl. So near white
      DOES count. (Measure 1 and Measure 4's blind spot.)

One measure satisfies both: the white in each row, CLAMPED, averaged over the
x-height band. Near white counts in full; white beyond the clamp counts as the
clamp and no more. A V's splay runs far past it and is discounted; an a's open
shoulder is inside it and is not.

THE CLAMP IS NOT A TUNED DIAL -- it is the face's own `n` COUNTER. That is
round 3's ruling used as a distance (*"the distance between characters should
be the same as within"*): white wider than the letter's own interior white has
stopped being rhythm and become a hole, and a hole's exact depth does not
change how the word reads. It is measured off the built font (`refsets.basis`),
so it follows a change of weight or width without being re-entered. `--clamp`
scales it for a sweep; the sweep is in docs/albo-spacing-method.md and it does
not change any verdict between 0.7 and 1.5 counters.

DO NOT USE IT ON MARKS. It averages the rows two glyphs SHARE in the x-height
band, so an apostrophe against an s has no rows and returns n/a -- which is
exactly the hole `cmp_space_2d.py` (measure 4) was written for. Letters here,
marks there.

    PYTHON_GIL=0 python3 cmp_word_white.py <ttf>                   # validation + per-letter sides
    PYTHON_GIL=0 python3 cmp_word_white.py <ttf> --refs            # against its own reference set
    PYTHON_GIL=0 python3 cmp_word_white.py <ttf> --pairs "ab nb th nh"
    PYTHON_GIL=0 python3 cmp_word_white.py <ttf> --sweep           # the clamp sweep
"""
import argparse, os, sys
import numpy as np
from cmp_touch import profiles
import refsets

LOWER = "abcdefghijklmnopqrstuvwxyz"
# The pairs every arm of this instrument is validated on. Each has a known
# answer from the record, so a run that disagrees is the instrument's fault.
VALID = [
    ("nn", "the rhythm: two stems, the pair every fitting rule is set from"),
    ("no", "the rhythm: stem into round"),
    ("on", "the rhythm: round into stem"),
    ("oo", "round 211: fitted to the references' 0.067-0.081 em on min white"),
    ("ab", "2026-09-19: 'about' reads as 'a bout' -- must read LOOSER than nb"),
    ("nb", "its control"),
    ("al", "2026-09-19: 'capitals' reads as 'capita ls' -- looser than nl"),
    ("nl", "its control"),
    ("th", "2026-09-19: 'the' reads as 't he' -- looser than nh"),
    ("nh", "its control"),
    ("tw", "2026-09-19: 'between' reads as 'bet ween' -- looser than nw"),
    ("nw", "its control"),
    ("Vi", "2026-09-17, the owner: Vi wants MORE space, so it must NOT read wildly loose"),
    ("Vu", "its sibling, which he set by hand at -126"),
    ("um", "round 199: he called it too tight; opened to the rhythm"),
]


class Face:
    def __init__(self, path, index=0, xh=300, chars=None, clamp=1.0):
        self.path, self.index = path, index
        chars = chars or (LOWER + LOWER.upper() + "0123456789.,;:!?'\"()-")
        self.prof, self.fnt, self.size = profiles(path, chars, xh, index=index, xh_src="measured")
        self.xh_px = xh
        b = refsets.basis(path, index)
        self.ctr_px = (b["ctr"] or 0.4) * xh          # the n's counter, in these px
        self.clamp_px = self.ctr_px * clamp
        self._len = {}

    def has(self, ch): return ch in self.prof

    def _adv(self, a, b):
        if b not in self._len: self._len[b] = self.fnt.getlength(b)
        return self.fnt.getlength(a + b) - self._len[b]

    def white(self, a, b):
        """Mean clamped white over the x-height rows the two glyphs share, in em."""
        if a not in self.prof or b not in self.prof: return None
        ra, _ = self.prof[a]; _, lb = self.prof[b]
        off = self._adv(a, b)
        # the x-height band, in raster rows: profiles() puts the baseline at
        # oy = size*2.1 and y grows downward.
        oy = int(self.size * 2.1)
        lo, hi = oy - self.xh_px, oy            # top of x-height .. baseline
        rows = np.arange(max(lo, 0), hi)
        r = ra[rows]; l = lb[rows] + off
        ok = ~np.isnan(r) & ~np.isnan(l)
        if ok.sum() < 3: return None
        w = np.clip(l[ok] - r[ok], 0.0, self.clamp_px)
        return float(w.mean() / self.size)

    def word_ratio(self, partners=LOWER):
        """WORD against LETTER, the measure rounds 100 and 133 set the space on:
        mean white across the x-height band, UNCLAMPED -- a word space is a hole
        by design and the clamp exists to discount holes, so clamping here would
        saturate both terms and the ratio would mean nothing. Median over the
        lowercase pairs, and the same pairs with a space between them."""
        keep = self.clamp_px
        self.clamp_px = 1e9
        try:
            L = [w for a in partners for b in partners if (w := self.white(a, b)) is not None]
            W = [w for a in partners for b in partners if (w := self.white_sp(a, b)) is not None]
        finally:
            self.clamp_px = keep
        if not L or not W: return None
        l, w = float(np.median(L)), float(np.median(W))
        return dict(letter=l, word=w, ratio=w / l)

    def white_sp(self, a, b):
        """The same mean white with a SPACE between the two letters."""
        if a not in self.prof or b not in self.prof: return None
        ra, _ = self.prof[a]; _, lb = self.prof[b]
        off = self.fnt.getlength(a + " " + b) - self.fnt.getlength(b)
        oy = int(self.size * 2.1)
        rows = np.arange(max(oy - self.xh_px, 0), oy)
        r = ra[rows]; l = lb[rows] + off
        ok = ~np.isnan(r) & ~np.isnan(l)
        if ok.sum() < 3: return None
        return float(np.clip(l[ok] - r[ok], 0.0, self.clamp_px).mean() / self.size)

    def sides(self, chars=LOWER, partners=LOWER):
        """Each letter's own two sides: the median clamped white with the whole
        lowercase on its right, and on its left."""
        out = {}
        for ch in chars:
            R = [w for b in partners if (w := self.white(ch, b)) is not None]
            L = [w for x in partners if (w := self.white(x, ch)) is not None]
            if R and L: out[ch] = (float(np.median(R)), float(np.median(L)))
        return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ttf")
    ap.add_argument("--refs", action="store_true")
    ap.add_argument("--set", dest="rset", default="auto",
                    choices=["auto", "roman", "italic", "bold", "bolditalic"])
    ap.add_argument("--pairs")
    ap.add_argument("--clamp", type=float, default=1.0, help="x the n counter")
    ap.add_argument("--sweep", action="store_true")
    ap.add_argument("--xh", type=int, default=300)
    ap.add_argument("--sides", action="store_true")
    ap.add_argument("--word", action="store_true", help="the word space against the letter white")
    a = ap.parse_args()

    rset = refsets.pick(a.ttf) if a.rset == "auto" else a.rset
    me = Face(a.ttf, clamp=a.clamp, xh=a.xh)
    print("\n%s -- mean clamped white, em, clamp %.2f x the n counter (%.0f px of %d)  [refs: %s]"
          % (os.path.basename(a.ttf), a.clamp, me.clamp_px, a.xh, rset))

    refs = []
    if a.refs or a.sweep:
        for label, p, i in refsets.entries(rset):
            try: refs.append((label, Face(p, i, clamp=a.clamp, xh=a.xh)))
            except Exception as e: print("  (%s: %s)" % (label, type(e).__name__))

    if a.sweep:
        print("\n  THE CLAMP SWEEP -- does the verdict move? (ab-nb and th-nh are the 2026-09-19")
        print("  faults; Vi/rhythm is the 2026-09-17 one. A clamp that works calls the first two")
        print("  POSITIVE and keeps the third from reading as a big multiple.)")
        print("    %-7s%9s%9s%9s%9s%9s" % ("clamp", "ab-nb", "al-nl", "th-nh", "tw-nw", "Vi/nn"))
        for c in (0.3, 0.5, 0.7, 1.0, 1.3, 1.5, 3.0, 99.0):
            f = Face(a.ttf, clamp=c, xh=a.xh)
            g = lambda s: f.white(s[0], s[1])
            print("    %-7.2f%9.4f%9.4f%9.4f%9.4f%9.2f" % (
                c, g("ab") - g("nb"), g("al") - g("nl"), g("th") - g("nh"),
                g("tw") - g("nw"), g("Vi") / g("nn")))
        print()

    print("\n  VALIDATION -- each pair has a known answer in the record")
    print("    %-5s%9s%9s   %s" % ("pair", "Albo", "ref med", "why it is here"))
    for p, why in VALID:
        v = me.white(p[0], p[1])
        rv = [w for _, f in refs if (w := f.white(p[0], p[1])) is not None]
        print("    %-5s%9s%9s   %s" % (
            p, "n/a" if v is None else "%.4f" % v,
            "%.4f" % np.median(rv) if rv else "--", why))

    if a.pairs:
        prs = a.pairs.split()
        print("\n    %-20s" % "face" + "".join("%8s" % p for p in prs))
        print("    %-20s" % "Albo" + "".join(
            ("%8.4f" % w if (w := me.white(p[0], p[1])) is not None else "     n/a") for p in prs))
        for label, f in refs:
            print("    %-20s" % label + "".join(
                ("%8.4f" % w if (w := f.white(p[0], p[1])) is not None else "     n/a") for p in prs))
        if refs:
            print("    %-20s" % "ref median" + "".join(
                ("%8.4f" % np.median(v) if (v := [w for _, f in refs if (w := f.white(p[0], p[1])) is not None]) else "     n/a")
                for p in prs))

    if a.word:
        print("\n  THE WORD SPACE AGAINST THE LETTERS -- mean unclamped white, em (rounds 100, 133)")
        print("    %-20s%10s%10s%9s%10s" % ("face", "letter", "word", "ratio", "space/em"))
        rows = [("Albo " + os.path.basename(a.ttf).split("-")[-1][:-4], me)] + refs
        for label, f in rows:
            w = f.word_ratio()
            if not w: continue
            sp = f.fnt.getlength(" ") / f.size
            print("    %-20s%10.4f%10.4f%9.2f%10.4f" % (label, w["letter"], w["word"], w["ratio"], sp))
        rr = [f.word_ratio()["ratio"] for _, f in refs if f.word_ratio()]
        if rr:
            print("    ref ratio: median %.2f, band %.2f-%.2f" % (np.median(rr), min(rr), max(rr)))

    if a.sides:
        s = me.sides()
        rs = [f.sides() for _, f in refs]
        print("\n  EACH LETTER'S OWN TWO SIDES -- median clamped white against the whole lowercase")
        print("    %-6s%9s%9s%9s%9s%8s%8s" % ("letter", "its R", "its L", "ref R", "ref L", "dR", "dL"))
        for ch in LOWER:
            if ch not in s: continue
            R, L = s[ch]
            rr = [d[ch][0] for d in rs if ch in d]; rl = [d[ch][1] for d in rs if ch in d]
            if rr:
                mr, ml = float(np.median(rr)), float(np.median(rl))
                print("    %-6s%9.4f%9.4f%9.4f%9.4f%+8.4f%+8.4f" % (ch, R, L, mr, ml, R - mr, L - ml))
            else:
                print("    %-6s%9.4f%9.4f" % (ch, R, L))
        allR = [v[0] for v in s.values()]; allL = [v[1] for v in s.values()]
        print("    median R %.4f (%.4f-%.4f, %.2fx)   median L %.4f (%.4f-%.4f, %.2fx)"
              % (np.median(allR), min(allR), max(allR), max(allR) / min(allR),
                 np.median(allL), min(allL), max(allL), max(allL) / min(allL)))
    print()


if __name__ == "__main__":
    sys.exit(main())
