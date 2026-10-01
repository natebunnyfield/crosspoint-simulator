#!/usr/bin/env python3
"""kern_classes.py -- the reader's kern CLASSES for each font, at every Albo size and tier, with
the firmware converter's own functions; exit 1 when any reaches the 255 it can store.

    $VENV/bin/python instruments/kern_classes.py FONT.ttf [FONT.ttf ...]

WHY IT IS A GATE (round 453, 2026-10-01). `fontconvert_sdcard.py` (firmware,
lib/EpdFont/scripts) does not ship GPOS pairs: it folds them into classes -- every left glyph
with an identical row of adjustments is one class, every right glyph with an identical column
another -- and stores class ids as uint8. Over 255 either way it prints a WARNING and DROPS THE
STYLE'S KERNING ENTIRELY; the build succeeds and every page sets unkerned. Every explicit pair
the composite clearance adds can split a class, and round 453's 2-D mark clearance
(mark_crowd.py --clear) took the Italic from 86/106 classes to 106/150 in one round.

Values are extracted exactly as the converter does (4.4 fixed-point pixels at
size * tier * 150 / 72 ppem over the font's cmap, U+2122 excluded as sd-fonts.yaml's `reading`
interval excludes it), so a class count here is the count on the device. CROSSPOINT_FIRMWARE_DIR
picks the firmware checkout (default ~/src/crosspoint-reader). WARN prints at 230.
"""
import contextlib, io, os, sys
from fontTools.ttLib import TTFont

FW = os.environ.get("CROSSPOINT_FIRMWARE_DIR", os.path.expanduser("~/src/crosspoint-reader"))
sys.path.insert(0, os.path.join(FW, "lib/EpdFont/scripts"))
import fontconvert_sdcard as fc  # noqa: E402

LIMIT, WARN = 255, 230
SIZES = [(pt, tier) for tier in (1, 2) for pt in (8, 10, 12, 14, 16, 18)]


def main():
    bad = 0
    for path in sys.argv[1:]:
        cps = {cp for cp in TTFont(path).getBestCmap() if cp != 0x2122}
        worst = (0, 0, None)
        for pt, tier in SIZES:
            with contextlib.redirect_stderr(io.StringIO()):
                km = fc.extract_kerning_fonttools(path, cps, pt * tier * 150.0 / 72.0)
                *_, lc, rc = fc.derive_kern_classes(km)
            if km and not lc:          # the converter returned nothing: it dropped the style's kerning
                lc = rc = LIMIT + 1
            if max(lc, rc) > max(worst[:2]):
                worst = (lc, rc, f"{pt}{'' if tier == 1 else '@2x'}")
        lc, rc, at = worst
        flag = "DROPPED" if max(lc, rc) > LIMIT else ("NEAR-LIMIT" if max(lc, rc) >= WARN else "ok")   # one token: gates.sh baselines it
        bad += max(lc, rc) > LIMIT
        print(f"{os.path.basename(path):24s} classes {lc} left / {rc} right (worst at {at})  {flag}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
