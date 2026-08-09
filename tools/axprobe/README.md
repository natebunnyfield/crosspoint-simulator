# AXProbe — query the app through Apple's real accessibility runtime

XCUITest queries travel the same out-of-process channel VoiceOver and Speak
Screen use, unlike the app's own `[A11Y-TREE]` dump, which walks in-process and
can only prove the container *answers*, never that anyone *asks*. This probe is
what established (2026-08-09) that the AX server serves the page correctly —
five line elements with labels and frames — while the device's Speak Screen
reported "no speakable content" without ever querying the app.

```bash
xcodegen generate           # once, or after editing project.yml
xcodebuild test -project AXProbe.xcodeproj -scheme AXProbe -destination "id=<booted-sim-udid>"
```

The tests target `com.natebunnyfield.crosspoint.x3` by bundle id, so install
the app on the simulator first (`xcrun simctl install`). The second test sets
`CROSSPOINT_SIM_FORCE_SPEAKSCREEN=1` to exercise the Speak Screen element set
(the `UIAccessibilityReadingContent` page element) off-device.

Known artifact: on some section-start pages the firmware's capture emits glued
words with zero-height rects (tracked separately); run against a normal body
page when label content matters.
