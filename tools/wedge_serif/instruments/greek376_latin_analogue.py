"""Italic references: each Greek letter's unsheared ink width over its Latin
analogue's, and the same in the roman -- does the italic Greek follow the
italic LATIN, or the roman Greek?"""
import statistics as stt, sys
sys.argv = [sys.argv[0]]
from greek376_italic_widths import PAIRS, slant, width
AN = [('η', 'n'), ('μ', 'u'), ('ν', 'v'), ('υ', 'u'), ('ι', 'ı'), ('α', 'a'), ('τ', 't'), ('κ', 'k'),
      ('ο', 'o'), ('ρ', 'p'), ('σ', 'o'), ('ω', 'w'), ('π', 'n'), ('χ', 'x'), ('λ', 'k'), ('γ', 'y')]
rows = {k: [] for k in AN}
for name, R, I in PAIRS:
    kr = slant(*R); ki = slant(*I)
    out = []
    for g, l in AN:
        try:
            ri = width(*I, g, ki)[0] / width(*I, l, ki)[0]
            rr = width(*R, g, kr)[0] / width(*R, l, kr)[0]
        except Exception:
            continue
        rows[(g, l)].append((ri, rr)); out.append(f"{g}/{l} {ri:.2f}({rr:.2f})")
    print(name, " ".join(out))
print("median italic (roman):", " ".join(f"{g}/{l} {stt.median(a for a, b in v):.2f}({stt.median(b for a, b in v):.2f})" for (g, l), v in rows.items() if v))
