#!/usr/bin/env python3
"""WHAT A WEIGHT AXIS ACTUALLY CHANGES, regular -> bold, on Albo and on every
reference family: thickness, thinness, contrast, WIDTH and the cap stem, each
as a scale-free ratio and then as the bold-over-regular factor.

Written 2026-09-19 for the owner's question: *"so bold just increases the
stroke widths without increasing the width as much, give me the numbers for
regular (skip medium 500) and bold changes to width, thickness, thinness,
contrast, etc in albo and other reference fonts."* The premise is TRUE of the
references and FALSE of Albo, which is the finding -- see
docs/albo-family-2026-09-19.md section 9.

Measures are `cmp_bold_stem`'s, imported rather than re-implemented, so this
file introduces no second instrument: the stem is the l's median single run
over its middle 40%, the hairline the o's thinnest bowl, the x-height the
minimum ink over x z v w (the x alone overshoots in Albo), and an italic's
run is multiplied by cos(its MEASURED slant).

    ALBO_DIR=<dir with Albo-Regular.ttf> BOLD_DIR=... PYTHON_GIL=0 \
      python3 cmp_weight_axis.py
"""
import sys, os
import cmp_bold_stem as B

SP = os.environ.get("ALBO_BUILDS", "")
ALBO = [('Albo 66.9 -> 107', (SP+'/w/reg/Albo-Regular.ttf', 0), (SP+'/w/b107/Albo-Bold.ttf', 0)),
        ('Albo 66.9 -> 116', (SP+'/w/reg/Albo-Regular.ttf', 0), (SP+'/w/b116/Albo-Bold.ttf', 0))]
ALBO_IT = [('Albo it 66.9 -> 116', (SP+'/w/regit/Albo-Italic.ttf', 0), (SP+'/w/bi116/Albo-BoldItalic.ttf', 0))]


def rows(pairs, label):
    print('\n' + '=' * 108)
    print(label)
    print('=' * 108)
    hdr = f"{'family':20s} {'thick/xh':>9s} {'thin/xh':>9s} {'contrast':>9s} {'n adv/xh':>9s} {'cap/capH':>9s}"
    print(hdr + '   <- regular, then BOLD, then the bold/reg RATIO')
    out = []
    for name, reg, bold in pairs:
        try:
            r = B.measure(*reg); b = B.measure(*bold)
        except Exception as e:
            print(f'{name:20s}  SKIP {e}'); continue
        rc = r['stem'] / r['hair']; bc = b['stem'] / b['hair']
        print(f"{name:20s} {r['stem_xh']:9.4f} {r['hair']/r['xh']:9.4f} {rc:9.2f} "
              f"{r['n_adv']:9.4f} {r['cap_ratio']:9.4f}")
        print(f"{'':20s} {b['stem_xh']:9.4f} {b['hair']/b['xh']:9.4f} {bc:9.2f} "
              f"{b['n_adv']:9.4f} {b['cap_ratio']:9.4f}")
        ratios = (b['stem_xh']/r['stem_xh'], (b['hair']/b['xh'])/(r['hair']/r['xh']),
                  bc/rc, b['n_adv']/r['n_adv'], b['cap_ratio']/r['cap_ratio'])
        print(f"{'':20s} {ratios[0]:8.2f}x {ratios[1]:8.2f}x {ratios[2]:8.2f}x {ratios[3]:8.2f}x {ratios[4]:8.2f}x")
        out.append((name, ratios))
    return out


def summary(out, label):
    if not out: return
    import statistics as st
    print(f'\n-- {label}: bold/regular ratio, median of {len(out)} families --')
    names = ['thickness', 'thinness', 'contrast', 'WIDTH (n adv)', 'cap stem']
    for i, n in enumerate(names):
        vals = sorted(x[1][i] for x in out)
        print(f'   {n:16s} median {st.median(vals):5.2f}x    range {vals[0]:.2f}-{vals[-1]:.2f}x')


ro = rows(B.ROMAN, 'UPRIGHT REFERENCE FAMILIES, regular -> bold')
summary(ro, 'uprights')
io = rows(B.ITALIC, 'ITALIC REFERENCE FAMILIES, italic -> bold italic')
summary(io, 'italics')
rows(ALBO, 'ALBO, Regular 400 -> Bold')
rows(ALBO_IT, 'ALBO ITALIC, Regular 400 -> Bold Italic')
