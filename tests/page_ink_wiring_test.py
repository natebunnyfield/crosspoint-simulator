#!/usr/bin/env python3
"""SOURCE GATE for the zen paper's ink-rows WIRING (docs/zen-page-margins.md §7, S-044).

tests/page_ink_rows_test.cpp pins the pure header (src/PageInkRows.h). This
file pins the places that header is plugged in, which no behavioral host test
reaches (the writers run under SDL on the render task, the consumer is the iOS
shim). Same shape as tests/font_resize_wiring_test.py, for the same reason:
delete any one of the sites below and every other test stays green.

Each assertion fails when:
- either pixel writer (renderBwPixels, composeGrayscalePreview in
  src/HalDisplay.cpp) stops measuring the rows after the level loop and
  before writePixelsFromLevels (ink rounding has moved the edges by then), or
  stops committing them AFTER its hold store (review finding 2: a commit the
  poll could see before the hold was armed relaid out a dark page twice);
- the call leaves its `!reconvertingFrame && pixelBufIsBookPage` gate (a
  reconvert of an old picture, or a system screen, would be measured);
- the HalGPIO commit stops asking StagedReaderInsets::pageDrawing() (an
  "Indexing" popup over the old page would be measured as the new one);
- the shim's zen placement stops reading readerPageInkRowsPx, or reads it into
  the panel's placement instead of the paper's edges only (review finding 1:
  `paperHArm`/`topWant` must stay on inkTopPx/inkBottomPx, the published pair);
- the poll stops deferring a rows edge while the present is held (review
  finding 2), or edges on the rows with the ink arm off (finding 4).
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
fails = []


def check(cond, msg):
    if not cond:
        fails.append(msg)


def body(src, signature):
    """The brace-balanced body following the first match of `signature`."""
    i = src.find(signature)
    if i < 0:
        return ""
    j = src.find("{", i)
    depth = 0
    for k in range(j, len(src)):
        if src[k] == "{":
            depth += 1
        elif src[k] == "}":
            depth -= 1
            if depth == 0:
                return src[j:k + 1]
    return src[j:]


disp = (ROOT / "src/HalDisplay.cpp").read_text()
for sig in ("uint64_t renderBwPixels(", "uint64_t composeGrayscalePreview()"):
    b = body(disp, sig)
    check(b, f"{sig} not found in src/HalDisplay.cpp")
    gate = "const bool measureInk = !reconvertingFrame && pixelBufIsBookPage;"
    i_ins = b.find("SimulatorOverlay::commitReaderTextInsets()")
    i_gate = b.find(gate)
    i_meas = b.find("pageink::inkRowsPortrait(levelBuf")
    i_write = b.find("writePixelsFromLevels(ramp")
    i_hold = b.rfind("presentHoldUntil.store(")
    i_commit = b.find("if (measureInk) SimulatorOverlay::commitReaderPageInkRows(inkRows);")
    i_dirty = b.find("requestDirtyPresent();", i_write if i_write >= 0 else 0)
    check(i_ins >= 0, f"{sig}: no commitReaderTextInsets")
    check(i_gate >= 0, f"{sig}: no !reconvertingFrame && pixelBufIsBookPage gate for the measure")
    check(i_meas >= 0 and i_gate < i_meas and i_meas - i_gate < 200,
          f"{sig}: the ink measure is not directly under its gate")
    check(i_ins < i_meas, f"{sig}: ink rows measured before the insets commit / the level loop")
    check(0 <= i_meas < i_write, f"{sig}: ink rows measured after writePixelsFromLevels (ink rounding has run)")
    loop = b[i_ins:i_meas] if i_ins >= 0 and i_meas >= 0 else ""
    check("levelBuf[y * HalDisplay::activeWidth() + x]" in loop,
          f"{sig}: the level loop is not between the insets commit and the ink measure")
    # review finding 2: the commit comes AFTER the writer's last hold store and
    # before the dirty present, so the poll sees the rows only with the hold settled
    check(i_commit >= 0, f"{sig}: no gated commitReaderPageInkRows(inkRows)")
    check(i_hold >= 0 and i_hold < i_commit, f"{sig}: the ink commit precedes the writer's hold store")
    check(i_dirty >= 0 and i_commit < i_dirty, f"{sig}: the ink commit is not before requestDirtyPresent")

gpio = (ROOT / "src/HalGPIO.cpp").read_text()
cb = body(gpio, "void commitReaderPageInkRows(const pageink::Rows &rows)")
check(cb, "HalGPIO.cpp: commitReaderPageInkRows not found")
check("readerInsetsChannel.pageDrawing()" in cb and cb.find("pageDrawing()") < cb.find("publish("),
      "HalGPIO.cpp: commitReaderPageInkRows does not gate on StagedReaderInsets::pageDrawing() before publishing")
check("pageInkRowsChannel.publish(rows)" in cb, "HalGPIO.cpp: commitReaderPageInkRows does not publish the writer's rows")

shim = (ROOT / "ios/CrossPointIOSShim.cpp").read_text()
i_read = shim.find("SimulatorOverlay::readerPageInkRowsPx(f, lastRow)")
check(i_read >= 0, "shim: the zen placement does not read readerPageInkRowsPx")
# finding 1: the rows feed edgeTopPx/edgeBottomPx only; want's inputs stay published
after = shim[i_read:i_read + 900]
check("edgeTopPx = f * toDevice" in after and "edgeBottomPx = (fbPortraitH - 1.0f - lastRow) * toDevice" in after,
      "shim: the ink rows do not set the paper's edges (edgeTopPx/edgeBottomPx)")
check("inkTopPx = f * toDevice" not in after and "inkBottomPx = (fbPortraitH" not in after,
      "shim: the ink rows are written into inkTopPx/inkBottomPx, which the panel's placement reads (review finding 1)")
check("const float paperHArm = panelHPx - inkTopPx - inkBottomPx + 3.0f * cPx;" in shim,
      "shim: paperHArm (the shift's input) no longer uses the published pair")
check("? (H * S - paperHArm) / 3.0f + cPx - inkTopPx" in shim,
      "shim: topWant no longer uses the published inkTopPx")
check("g_zenPaperTopArmPx = SDL_max(0.0f, base + want + edgeTopPx - cPx);" in shim,
      "shim: the paper's top is not struck from edgeTopPx")
check("g_zenPaperBotArmPx = SDL_min(H * S, base + want + panelHPx - edgeBottomPx + 2.0f * cPx);" in shim,
      "shim: the paper's bottom is not struck from edgeBottomPx")
# findings 2 and 4 in the poll
pb = body(shim, "void pollReaderInsets()")
check(pb, "shim: pollReaderInsets not found")
check("if (zenInkArm())" in pb and pb.find("if (zenInkArm())") < pb.find("readerPageInkRowsPx"),
      "shim: pollReaderInsets reads the ink rows with the ink arm off (review finding 4)")
check("SimulatorOverlay::presentHeldNow()" in pb,
      "shim: pollReaderInsets does not defer a rows edge while the present is held (review finding 2)")
check("bool presentHeldNow()" in disp and "presentHoldUntil.load()" in body(disp, "bool presentHeldNow()"),
      "HalDisplay.cpp: presentHeldNow does not read presentHoldUntil")

if fails:
    for f in fails:
        print("FAIL:", f)
    sys.exit(1)
print("page_ink_wiring: ok")
