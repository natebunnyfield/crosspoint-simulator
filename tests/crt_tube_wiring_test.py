#!/usr/bin/env python3
"""THE TUBE REACHES EVERY HOST THAT PAINTS THE DARK PAGE.

Owner 2026-11-27 (docs/crt-gamut-plan-2026-11-27.md, option B): the firmware's
Tube row names the dark page's phosphor. The firmware hands it to the
simulator's HalFrontlight (setTube), which publishes it inside the same Light
the hosts already read, so the model (src/FrontlitPage.h, pinned by
frontlit_page) is what decides. This gate pins the plumbing between the two,
which no host test can run: the iOS shim compiles only for iOS, and the desktop
hook only into a Picco build.

A host that rebuilt a Light from its fields, or asked the model for anything
but simfrontlight::current() whole, would drop the tube silently: the page
would stay the Mixed tube on that one host and every other test would pass.
And the desktop hook used to push the tail only when there was one, which was
fine while every page had a tail and leaves the Mixed tube's amber on a single
phosphor's afterglow now.
"""

import pathlib
import re
import sys

# An argument names another copy of the tree, which is how this gate was shown
# to fail: against the four files as they stood before the Tube.
REPO = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path(__file__).resolve().parent.parent

failures = []


def check(ok, msg):
    if not ok:
        failures.append(msg)


def code_of(path):
    """The file with its // comments removed: the checks are about code."""
    text = (REPO / path).read_text()
    return "\n".join(line.split("//", 1)[0] for line in text.splitlines()) + "\n"


def body_of(text, signature, where):
    """The source between `signature` and the first line-start `}`."""
    start = text.find(signature)
    if start < 0:
        check(False, f"{where}: {signature!r} not found")
        return ""
    end = text.find("\n}", start)
    return text[start:end if end > 0 else len(text)]


# 1. The HAL publishes the tube with the light and the hosts read it back.
hal = code_of("src/HalFrontlight.cpp")
check("g_tube.exchange(tube)" in body_of(hal, "void publish(", "HalFrontlight.cpp"),
      "HalFrontlight publish: a tube change must count as a change (bump the generation)")
check("l.tube = g_tube.load()" in body_of(hal, "frontlitpage::Light current()", "HalFrontlight.cpp"),
      "simfrontlight::current() must carry the tube")
check("publish(" in body_of(hal, "void HalFrontlight::setTube(", "HalFrontlight.cpp"),
      "HalFrontlight::setTube must publish")
check(len(re.findall(r"publish\(lastBrightness, lastWarmth, lit, lastTube\)", hal)) >= 5,
      "every HalFrontlight setter must publish the tube with the light")

# 2. The desktop hook asks the model with the whole Light, and clears the tail.
disp = code_of("src/HalDisplay.cpp")
hook = body_of(disp, "static void applyFrontlitPage()", "HalDisplay.cpp")
check("simfrontlight::current()" in hook and "frontlitpage::darkPage(l)" in hook,
      "applyFrontlitPage must ask darkPage for simfrontlight::current()")
check(re.search(r"setPanelGlowTail\(\s*dark\.mix\.hasTail\s*\?[^;]*:\s*nullptr", hook) is not None,
      "applyFrontlitPage must clear the tail when the tube has none")

# 3. iOS: the palette, the glow, the scanlines and the sleep tick.
prefs = code_of("ios/PanelPrefs.h")
store = body_of(prefs, "inline panelsource::Store panelStoreFromPrefs()", "PanelPrefs.h")
check("simfrontlight::current()" in store and "frontlitpage::darkPair(lamp)" in store,
      "panelStoreFromPrefs must take the dark pair from darkPair(simfrontlight::current())")
shim = code_of("ios/CrossPointIOSShim.cpp")
glow = body_of(shim, "void pollPanelGlow()", "CrossPointIOSShim.cpp")
check("simfrontlight::generation()" in glow,
      "pollPanelGlow must re-ask on the light's generation (a tube change bumps it)")
check("simfrontlight::current()" in glow and "frontlitpage::darkPage(lamp)" in glow,
      "pollPanelGlow must take the decay from darkPage(simfrontlight::current())")
check("setPanelGlowTail(tail" in glow,
      "pollPanelGlow must push its tail, null included")
scan = body_of(shim, "void pollScanlines()", "CrossPointIOSShim.cpp")
check("frontlitpage::bloomPercent(" in scan and "simfrontlight::current()" in scan,
      "pollScanlines must take the bloom from bloomPercent(simfrontlight::current(), ...)")
tick = body_of(shim, "void sleepTick()", "CrossPointIOSShim.cpp")
for call in ("syncPanelPalette()", "pollPanelGlow()", "pollScanlines()"):
    check(call in tick, f"sleepTick must run {call}")

# 4. Nobody rebuilds a Light from parts (which would drop the tube).
for path in ("ios/CrossPointIOSShim.cpp", "ios/PanelPrefs.h", "src/HalDisplay.cpp"):
    check(re.search(r"frontlitpage::Light\s*\{", code_of(path)) is None,
          f"{path}: build no Light from fields; pass simfrontlight::current() whole")

if failures:
    for f in failures:
        print("FAIL:", f)
    print(f"{len(failures)} failure(s)")
    sys.exit(1)
print("crt tube wiring: the HAL publishes it; the desktop hook and the iOS "
      "palette, glow, scanline and sleep-tick reads all follow it")
