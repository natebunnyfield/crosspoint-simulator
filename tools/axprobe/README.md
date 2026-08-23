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
the app on the simulator first (`xcrun simctl install`).

**Turn real Speak Screen on before the run.** The pane is named *Speak Screen*;
the preference behind it is `SpeakThisEnabled` (Speak Screen shipped as "Speak
This" internally), and `SpeakScreenEnabled` — the obvious guess — is accepted
by `defaults` and read by nothing:

```bash
xcrun simctl spawn <udid> defaults write com.apple.Accessibility SpeakThisEnabled -bool true
```

Without it `testRealSpeakScreenFlagReachesThePageView` SKIPS (it does not fail:
with Speak Screen off the app correctly builds no page view, and blaming the
app for that would be a lie). The other Speak Screen test uses
`CROSSPOINT_SIM_FORCE_SPEAKSCREEN=1` and runs either way.

**Every test pages past the cover first — except the one that is about the
cover.** A book opens on `wrap0000.xhtml`, a cover wrapper with an `<img>` and
no prose: the reader renders a blank panel and the firmware correctly captures
an empty page. A probe that stops there by accident measures nothing and reads
as a failure of the exposure. `QTAP:BACK` opens the book from Home, each
`QTAP:RIGHT` is one page forward.

`testCoverPageSpeaksTheBookInstead` stops on it deliberately (owner ruling
2026-08-23): a textless page must vend the book's name and the fact that the
page has no text, rather than nothing at all. It opens with
`200:QTAP:BACK:2500` — a HELD Back across the boot routing check, which forces
the Home boot and makes the rest of the script mean the same thing every run —
then opens the book and pages `QTAP:LEFT` back to the front of it, because the
app resumes where the last run left it and the other tests each advance it a
few pages. If it ever starts so deep that ten taps cannot reach the cover,
reset the reading position by deleting the book's cache directory in the app's
container:

```bash
D=<udid>; C=$(xcrun simctl get_app_container $D com.natebunnyfield.crosspoint.x3 data)
rm -rf "$C/Documents/.crosspoint/epub_"*
```

That clears pagination and progress only — `recent.json` and `state.json` stay,
and they are what names the book (see `src/SpokenPageText.h`).

The generated `AXProbe.xcodeproj` is gitignored — run `xcodegen generate`.

Full chain, instrument and measurement:
[../../docs/speak-screen-chain.md](../../docs/speak-screen-chain.md).

Known artifact: on some section-start pages the firmware's capture emits glued
words with zero-height rects (tracked separately); run against a normal body
page when label content matters.
