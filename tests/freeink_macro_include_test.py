#!/usr/bin/env python3
"""A FREEINK_* MACRO TESTED WHERE BoardConfig.h IS NOT INCLUDED READS 0.

`#if FREEINK_DEVICE_X3` in a file that never includes src/BoardConfig.h is
not an error: the preprocessor reads an undefined identifier as 0, so the
branch silently goes the same way on every device. It shipped that way in
HalDisplay::supportsAbsoluteGrayscale, which answered YES on every X3 build and
hid the device's bilevel fallback (fixed 2026-09-25). This gate fails on any
simulator source that tests a FREEINK_* macro without including BoardConfig.h
itself -- a header that happens to include it is not trusted, since that is
exactly the kind of accident that goes away in a refactor. #ifdef/#ifndef on a
FREEINK_* macro are caught too (they are always defined, 0 or 1, so a test for
definedness is wrong everywhere), and a commented-out include does not count.
"""
import pathlib, re, sys

root = pathlib.Path(__file__).resolve().parent.parent
pat = re.compile(r'^\s*#\s*(?:if|elif|ifdef|ifndef)\b.*\bFREEINK_[A-Z0-9_]+', re.M)
inc = re.compile(r'^\s*#\s*include\s*[<"]BoardConfig\.h[>"]', re.M)
bad = []
for p in sorted(list((root / 'src').rglob('*.[ch]*')) + list((root / 'ios').rglob('*.[chm]*'))):
    if p.name == 'BoardConfig.h':
        continue
    text = p.read_text(errors='replace')
    if pat.search(text) and not inc.search(text):
        for m in pat.finditer(text):
            line = text.count('\n', 0, m.start()) + 1
            bad.append(f'{p.relative_to(root)}:{line}: {m.group(0).strip()}')
if bad:
    print('FAIL: FREEINK_* tested without including BoardConfig.h (it reads 0 here):')
    for b in bad:
        print('  ' + b)
    sys.exit(1)
print('freeink_macro_include: ok')
