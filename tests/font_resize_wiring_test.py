#!/usr/bin/env python3
"""SOURCE GATE for the font-resize fix's WIRING (docs/font-resize-flash-jitter-2026-10-11.md).

What this is, said plainly: a structural check on the source text, not a
behavioral test. The behavior lives across the render thread, the main thread
and SDL, and the race it closes did not reproduce on the desktop even before
the fix (render and present timing there never put a present in flight at the
1-bit write), so no headless desktop run fails without the fix. The pure
pieces are behavior-tested elsewhere: tests/present_hold_test.cpp (the
predicate) and tests/reader_insets_channel_test.cpp (StagedReaderInsets).
This file exists because the adversarial review of 576ad65 showed that
DELETING the wiring -- the second hold check under the pixel lock, a writer's
commit, the page-identity arm -- left every test green. Each assertion below
fails when one of those is removed or moved out of place.
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
        return None
    j = src.index("{", i)
    depth = 0
    for k in range(j, len(src)):
        if src[k] == "{":
            depth += 1
        elif src[k] == "}":
            depth -= 1
            if depth == 0:
                return src[j:k + 1]
    return None


hal = (ROOT / "src/HalDisplay.cpp").read_text()
gpio = (ROOT / "src/HalGPIO.cpp").read_text()

# 1. presentIfNeeded asks the hold TWICE, and the second asking is the first
#    statement after the pixel lock that guards the upload.
pin = body(hal, "void HalDisplay::presentIfNeeded()")
check(pin is not None, "presentIfNeeded body not found")
if pin:
    check(pin.count("presentheld::held(") >= 2,
          "presentIfNeeded must ask presentheld::held twice (before the work and under pixelBufMutex)")
    m = re.search(r"bool reconvertOnly = false;\s*\{\s*const std::lock_guard<std::mutex> lock\(pixelBufMutex\);\s*(.{0,1600})",
                  pin, re.S)
    check(m is not None, "the upload's pixel-lock block (after `bool reconvertOnly = false;`) not found")
    if m:
        head = m.group(1)
        k = head.find("presentheld::held(")
        check(k >= 0, "the hold is not re-asked at the top of the upload's pixel-lock block")
        if k >= 0:
            after = head[k:k + 900]
            check("pendingPresent.store(true)" in after and "return;" in after,
                  "a present caught by the second check must stay OWED (pendingPresent=true) and return")
            check("firmwarelog::armed()" in after,
                  "the decline line must also log while the Diagnostics Log is on (phone has no env var)")

# 2. Both pixel writers commit the staged insets, only on a non-reconvert write.
for sig in ("uint64_t renderBwPixels(", "uint64_t composeGrayscalePreview()"):
    b = body(hal, sig)
    check(b is not None, f"{sig} body not found")
    if b:
        check(re.search(r"if \(!reconvertingFrame\) \{[^}]*commitReaderTextInsets\(\);", b, re.S) is not None,
              f"{sig} must call SimulatorOverlay::commitReaderTextInsets() inside `if (!reconvertingFrame)`")

# 3. The page identity arms the commit; the publish stages.
pid = body(gpio, "void HalGPIO::publishReaderPageIdentity(")
check(pid is not None and "readerInsetsChannel.markPageDrawing();" in pid,
      "publishReaderPageIdentity must arm the staged insets (markPageDrawing)")
check("static StagedReaderInsets readerInsetsChannel;" in gpio,
      "the reader insets channel must be the STAGED one")

if fails:
    for f in fails:
        print("FAIL:", f)
    sys.exit(1)
print("font_resize_wiring_test: all checks passed")
