"""Round 379: the italic references' Greek capitals, unsheared ink width italic over roman
(decided symbols2._cw, the italic Greek capitals' 0.953). Run from this directory."""
import statistics as stt, sys
sys.argv = [sys.argv[0]]
from greek376_italic_widths import PAIRS, slant, width
UC = "ΓΔΘΛΞΠΣΦΨΩHOE"
allr = []
for name, R, I in PAIRS:
    kr = slant(*R); ki = slant(*I)
    rs = [width(*I, ch, ki)[0] / width(*R, ch, kr)[0] for ch in UC]
    allr.append(rs)
    print(name, " ".join(f"{ch}{r:.2f}" for ch, r in zip(UC, rs)))
print("median per letter", " ".join(f"{ch}{stt.median(r[i] for r in allr):.2f}" for i, ch in enumerate(UC)))
print("median all Greek", stt.median(r[i] for r in allr for i in range(10)))
