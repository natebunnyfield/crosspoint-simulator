# The Speak Screen chain, and how to measure it

Status: 2026-08-23. Written because "No speakable content could be found on the
screen" has now cost **two** investigations — the 2026-08-09 arc that burned
~12 TestFlight builds (v42–v54) and the 2026-08-23 one this document records.
The standing rule is that a second failure in the same area gets
instrumentation, not another plausible patch. This is the instrument, the
measurement it produced, and the list of links that were checked and found
**healthy** — which is the half a chat summary always drops and the half that
stops the same candidates being re-proposed forever.

---

## 1. The chain

| # | Link | Where | How to see it |
|---|---|---|---|
| 1 | The firmware captures the displayed page's text + per-word rects | `EpubReaderActivity::captureReadAloudPage`, firmware `src/activities/reader/` | `[A11Y-FILE] CHAIN ... page=<N>B rects=<N>` |
| 2 | The channel carries it | `src/ReadAloudChannel.h`, drained by `CrossPointReadAloud_perFrame` | same line |
| 3 | The adapter holds it | `ios/CrossPointReadAloud.mm` (`g_pageUtf8` / `g_rects`) | same line |
| 4 | Panel geometry maps logical px to screen points | `src/ReadAloudGeometry.h` (pure), called from `ios/CrossPointAccessibility.mm` | `geo=1(x0,y0 xSCALE)` |
| 5a | Per-**line** `UIAccessibilityElement`s — VoiceOver, Braille, Switch Control | `CPAccessibilityOverlay` | `elements=<N>` |
| 5b | The **`UITextInput`** page view — **the only thing Speak Screen consumes** | `ios/CrossPointPageTextInput.mm` (`CPPageTextInputView`) | `view=1 frame=(...) inWindow=1` |
| 6 | A page with **no text** still says something true | `src/SpokenPageText.h` (pure), fed by `CrossPointAccessibility_setFallbackPage` | `fb=43B` and `textless page -- speaking the book instead: "..."` |

Speak Screen reads **5b and nothing else**. That was established by measurement
in 2026-08-09 against six other exposure mechanisms (synthetic element
containers, the explicit container protocol, `UIAccessibilityReadingContent`,
elements vended from the window, a hidden real `UITextView`, and a sentinel
matrix whose fully visible `UILabel` went unread). VoiceOver read every one of
them; Speak Screen read none. The recipe that works is WWDC26 session 219,
"Enhance the accessibility of your reading app": the protocol adopted **in its
entirety** on the accessibility element itself.

---

## 2. The instrument

One line answers all five links at once. It is throttled to changes of its
*shape* plus one line per five seconds, so it costs nothing in an ordinary
session.

```
CHAIN wants=1 page=765B rects=142 fb=0B geo=1(34,124 x0.667) view=1 \
      frame=(34,124 352x528) inWindow=1 host=SDL_uikitmetalview elements=21
```

- `wants` — `wantsReadingPage()`: Speak Screen on, or the override.
- `page` / `rects` — what the adapter is holding, i.e. links 1–3.
- `fb` — the textless-page substitute (link 6, added 2026-08-23). `page=0B
  rects=0 fb=0B` is a page nothing can name; `page=0B rects=0 fb=43B` is a
  cover that speaks.
- `geo` — link 4; `0(0,0 x0.000)` means the panel has not presented yet, which
  is normal for the first ~600 ms and self-heals.
- `view` / `frame` / `inWindow` — link 5b.
- `elements` — link 5a.

It is written by `CrossPointAccessibility_logChain` and goes through
`CrossPointDiag_log`, so it lands in `diagnostics/a11y.log` on the card (Files
app → On My iPhone → CrossPoint X3 → diagnostics) and mirrors to `SDL_Log`.

**Diagnostics are OFF by default** (owner ruling 2026-08-09). Two doors:

- On a phone: **Settings.app → CrossPoint X3 → Diagnostics Log**.
- Headless: **`CROSSPOINT_SIM_DIAGNOSTICS=1`**. Added 2026-08-23 — a sandboxed
  app's `NSUserDefaults` live in its data container, so `simctl spawn defaults
  write <bundleid>` writes a store nothing reads (see `ios/README.md`), and
  before this there was no way to turn the instrument on for a scripted run.
  It can only ENABLE; the owner's Off is never overridden by anything but an
  explicit run.

---

## 3. **Speak Screen CAN be tested in the simulator.** It was never true that it could not.

`ios/README.md` recorded, and every session since believed, that
"Speak Screen cannot be tested in the simulator — its Spoken Content pane
offers only Speak Selection, so `UIAccessibilityIsSpeakScreenEnabled()` reads 0
there." That belief is a large part of why the 2026-08-09 arc had to be run on
TestFlight, twelve builds at a time.

The pane is named *Speak Screen*; the preference behind it is not. From
`libAccessibility.dylib`'s own strings the key is **`SpeakThisEnabled`**
(`_AXSSpeakThisEnabled`, `com.apple.accessibility.SpeakThisEnabled`) — Speak
Screen shipped as "Speak This" internally. Writing it to the **system** domain
(not the app's container — this one really is a system preference) makes the
API return true:

```bash
xcrun simctl spawn <udid> defaults write com.apple.Accessibility SpeakThisEnabled -bool true
```

Measured 2026-08-23, iPhone Air simulator, iOS 26.5:

```
[A11Y-FILE] assistive tech: speakScreen=1 voiceOver=0 switchControl=0
```

with the full chain following. `SpeakScreenEnabled` — the obvious guess — is
accepted by `defaults` and read by nothing.

What still cannot be done in a simulator is **invoking** Speak Screen (the
two-finger swipe down from the top edge) and hearing it speak. `simctl` cannot
synthesize a two-finger swipe and XCUITest has no public multi-finger swipe. So
the *exposure* is fully testable off-device; the *speech* is not.

---

## 4. What the 2026-08-23 measurement found

Instrumented build, iPhone Air simulator (`663B0B14`), X3, render scale 2, zen
mode on (the shipped default), English Fairy Tales.

### Healthy — every link, on a page with text

```
CHAIN wants=1 page=520B rects=94  geo=1(34,132 x0.667) view=1 frame=(34,132 352x528) inWindow=1 elements=16
CHAIN wants=1 page=765B rects=142 geo=1(34,124 x0.667) view=1 frame=(34,124 352x528) inWindow=1 elements=21
CHAIN wants=1 page=814B rects=139 geo=1(34,132 x0.667) view=1 frame=(34,132 352x528) inWindow=1 elements=22
```

Confirmed through **Apple's real out-of-process AX channel** (`tools/axprobe`,
XCUITest — the same channel Speak Screen uses, not the app's in-process dump):

```
AXPROBE staticTexts count: 22
AXPROBE [0] label="applies to the collection of the"    frame=(39.3, 136.7, 271.3, 23.3)
AXPROBE [1] label="Brothers Grimm and to all the other" frame=(39.3, 160.0, 316.7, 23.3)
AXPROBE page-textinput exists: true frame=(34.0, 132.0, 352.0, 528.0)
```

The frames were checked against the rendered screenshot: the element for
`"By Anonymous"` reported `(139,137 142x23) pt` and the glyphs measure
`(137..283, 141..153) pt` on the 1260×2736 capture. The mapping is right.

Also verified healthy, each of which had been proposed as a suspect:

| Checked | Result |
|---|---|
| `CrossPointAccessibility.mm` / `CrossPointPageTextInput.mm` compiled into the app | yes — `ios/CMakeLists.txt` :51/:54 and :81/:82 (corrected 2026-08-29 — was :49/:53 and :78/:80, drifted as the file grew), and the AX runtime serves the view |
| The render-scale change 3 → 2 (`f549b4c`) | **not implicated.** The scale is derived from the *presented* panel width, so it is render-scale independent by construction. Pinned by `tests/readaloud_geometry_test.cpp` |
| Zen placement / panel moved (`79b4fc8`, zen default on) | **not implicated.** Zen moves the panel, `panelBottomPx`/`panelLeftPx` follow, geometry tracks: `[zen] panel 1056x1584 at 102,396` → `geo=1(34,132 x0.667)` |
| The preset-list push (`525c768`) and the removed drawer sliders (`a7d256d`) | **not implicated.** Neither is in the hierarchy unless presented |
| Frozen getters / removed keys in `CrossPointPrefs.mm` | **not implicated.** `readAloudEnabled`, `readAloudRatePercent` and `diagnosticsEnabled` all still read `NSUserDefaults` and all three rows are still in `Settings.bundle/Root.plist` |
| `CPXShakeCatcher` (zen, 2026-08-22) burying the page view | no — the page view is added last to the host and `inWindow=1` throughout |
| Backgrounding and returning to the foreground | survives; `view=1` unchanged across the cycle |
| 24 consecutive page turns | every page published a non-empty capture (20–143 rects). **No hole in the firmware capture path** |
| `UIAccessibilityIsSpeakScreenEnabled()` | not deprecated in the iOS 26.5 SDK; returns true off `SpeakThisEnabled` (§3) |

### The one condition that reproduced the message

**The displayed page genuinely has no text.** The firmware then published an
empty capture, the adapter cleared, and the container was correctly empty:

```
[ERS] Loading file: OEBPS/wrap0000.xhtml, index: 0
CHAIN wants=1 page=0B rects=0 geo=1(34,124 x0.667) view=0 frame=(0,0 0x0) inWindow=0 elements=0
```

`wrap0000.xhtml` is the book's **cover wrapper** — an `<img>` and nothing else.
Two things follow, and both matter:

1. It renders as an **entirely blank panel**. Measured: the whole panel area is
   three adjacent code values, no ink at all. The cover image is dropped (one
   of the fourteen "book notes" the firmware now raises is *images dropped*).
   **This rendering bug is out of scope and stays logged** (owner, 2026-08-23).
2. It is **the page a book opens on**, and the page a reader resumed at
   `spine=0 page=0` lands on. So the very first thing an owner saw after
   opening a book was a blank page on which Speak Screen said, accurately, that
   there was nothing to speak.

Per the 2026-08-09 scope ruling ("only EPUB text is speakable; Home, menus and
`.txt`/`.xtc` publish nothing, and *no speakable content* there is correct
behavior") that was working as designed. From the owner's chair it was
indistinguishable from the bug that ruling was written after — which is exactly
why it did not stay that way.

### THE COVER NOW SPEAKS (owner ruling 2026-08-23)

> make the cover speak something

An empty capture no longer means an empty screen. `src/SpokenPageText.h` decides
what such a page is worth saying, and the rules are all honesty rules:

- **The words are true or there are none.** The cover *is* the book's title and
  author, so saying them describes the page rather than inventing prose. When
  the book cannot be named, the fallback is the empty string and iOS goes on
  reporting nothing — which is then the truth.
- **The closing sentence** — "This page has no text." — is what keeps it honest
  on a page that is *not* the cover. Nothing reachable at that moment says which
  page this is, so a blank interior page or a dropped illustration gets a true
  sentence instead of an implied cover.
- **Only on a genuinely empty page.** `spokenpage::forPage` returns the page
  whenever it holds anything but whitespace, so a page with one word on it
  speaks that word. The fallback is a substitute, never a supplement.
- **VoiceOver does not change.** The fallback rides the page view and the
  `wantsReadingPage()` gate, exactly as the page element does; no line element
  is added, because there are no words on the page to frame.

**Where the text comes from, and what was rejected.** The firmware already
writes both halves to the card in `EpubReaderActivity::onEnter`, before the
first render: `APP_STATE.saveToFile()` (`openEpubPath` →
`/.crosspoint/state.json`) at :183 and `RECENT_BOOKS.addBook()` (path, title,
author → `/.crosspoint/recent.json`, which `saveToFile()`s immediately) at :184.
So the simulator reads them with its own `HalStorage` and needs **no new HAL
channel** — which was the stop condition on this task, since a channel is a
firmware change. Rejected on the way:

| Considered | Why not |
|---|---|
| The firmware's live `Epub` object (`getTitle()`/`getAuthor()`) | Reachable only through a new HAL channel or by reaching into activity internals from the harness. Firmware change; out of scope |
| The FRONT entry of `recent.json` | It is the most recently *opened* book, so it is usually right — which is what makes it dangerous. `openEpubPath` must match exactly, or nothing is said. A wrong title spoken over the right cover is a silent lie |
| Speaking the previous page's text | Named in the ruling as exactly what dishonesty looks like here. A textless publish clears the held page first |
| Rendering the cover so it has text | The blank-cover rendering bug is deliberately out of scope |

Measured, iPhone Air simulator, `CROSSPOINT_SIM_FORCE_SPEAKSCREEN=1`:

```
[ERS] Loading file: OEBPS/wrap0000.xhtml, index: 0
[A11Y-FILE] UITextInput page view installed (WWDC26-219 pattern)
[A11Y-FILE] textless page -- speaking the book instead: "English Fairy Tales. This page has no text."
[A11Y-FILE] CHAIN wants=1 page=0B rects=0 fb=43B geo=1(34,124 x0.667) view=1 frame=(34,124 352x528) inWindow=1 elements=0
```

Note the shape of that line against the one above it: `page=0B rects=0` is
unchanged — the firmware is still right that there is no text — and `view=1`
with `fb=43B` is the difference. `elements=0` is deliberate: no line elements,
so VoiceOver's blank page is byte-identical to what it was.

And through **Apple's own out-of-process channel**, which is the one that
matters — `tools/axprobe`, on the same blank page:

```
AXPROBE cover page-textinput exists: true
AXPROBE cover page-textinput value: "English Fairy Tales. This page has no text."
AXPROBE cover page-textinput frame=(34.0, 132.0, 352.0, 528.0)
AXPROBE cover line elements over the panel: 0
```

The routing shows up in the same suite by accident, which is the best kind of
evidence: two front-matter pages carrying almost nothing — 19 and 26 characters
— vended `"ENGLISH FAIRY TALES"` and `"COLLECTED BY JOSEPH JACOBS"`, their own
text, not the book's name. A page with words on it speaks its words however few
they are.

**Device-unconfirmed:** that iOS *speaks* it. A simulator cannot be sent the
two-finger swipe that invokes Speak Screen (§3), so what is proven here is that
Apple's own out-of-process channel is served the words. Also unconfirmed: how
Speak Screen draws its reading highlight over an element with no selection
rects — a textless page has no word geometry to give it, and the expectation
(untested) is that it simply draws none.

### One minor defect found, NOT fixed (a proposal, not a change)

The page view's frame is set when `setPage` runs, and nothing re-frames it
afterwards. A zen relayout that moves the panel between publishes therefore
leaves the frame one step stale — measured at 8 pt on the run above:

```
CHAIN ... geo=1(34,132 x0.667) view=1 frame=(34,124 352x528) ...
```

It self-corrects on the next publish (the very next page turn logged
`frame=(34,132 ...)`), and 8 pt inside a 352x528 element cannot produce "no
speakable content". It is recorded rather than patched because the level-
triggered self-heal in `CrossPointAccessibility_modeChanged` watches the MODE
and the element count, not the geometry, and adding geometry to it is a change
to working code that no measurement here demands. If a device report ever
describes the reading highlight sitting slightly off the words after a layout
change, this is the first thing to look at.

### What is NOT explained

If the report was made on a **body page** — a page with visible prose — nothing
found here explains it. Every link was populated on every one of 24 such pages,
and Apple's own channel served both element sets. The remaining differences
between this measurement and an owner's phone are:

- **Invocation.** The two-finger swipe cannot be synthesized, so "iOS asked and
  got nothing" versus "iOS never asked" is still device-only.
- **Release codegen.** Measured in Debug; TestFlight ships Release. No
  mechanism is known by which `-O2` would change Objective-C accessibility
  behavior, and it was not measured — stated so the next session does not
  assume it was.

---

## 5. Running it

```bash
# Build (see ios/README.md for the first-configure recipe)
cmake --build build/ios-app --config Debug --target CrossPointX3

D=<udid>
xcrun simctl install $D build/ios-app/ios/Debug-iphonesimulator/CrossPointX3.app
xcrun simctl spawn $D defaults write com.apple.Accessibility SpeakThisEnabled -bool true

# The chain, live. The leading HELD Back (200:QTAP:BACK:2500) spans the boot
# routing check and forces a Home boot, so the rest of the script means the
# same thing every run -- without it the launch resumes the book on alternate
# runs and `BACK` then LEAVES the reader instead of entering it. The next BACK
# opens the book (on its cover); each QTAP:RIGHT is one page forward, so this
# walks cover -> body and prints both CHAIN shapes.
SIMCTL_CHILD_CROSSPOINT_SIM_DIAGNOSTICS=1 \
SIMCTL_CHILD_CROSSPOINT_SIM_INPUT_SCRIPT='200:QTAP:BACK:2500;5000:QTAP:BACK;10000:QTAP:RIGHT' \
  xcrun simctl launch --console-pty $D com.natebunnyfield.crosspoint.x3

# Apple's real AX channel
cd tools/axprobe && xcodegen generate
xcodebuild test -project AXProbe.xcodeproj -scheme AXProbe -destination "id=$D"

# The pure geometry and the textless-page words, on the host
tests/run_all.sh -k readaloud
tests/run_all.sh -k spoken
```

`CROSSPOINT_SIM_FORCE_SPEAKSCREEN=1` still forces `wantsReadingPage()` for runs
that do not want to touch the system preference. Prefer `SpeakThisEnabled`: it
exercises the branch a phone actually takes.

### Traps that cost time on 2026-08-23, in the order they were hit

1. **The build failed on a firmware TU the source set did not know about**
   (`XmlEncodingSupport.cpp`, added uncommitted by a concurrent session).
   `cmake/CrossPointSources.cmake` is generated and pinned to a firmware
   commit; regenerate it rather than believing the link error.
2. **`cmake --build` after a source-set change needs a second invocation.**
   The first regenerates the `.xcodeproj`; `xcodebuild` in that same run uses
   the project it was handed at the start, so it links against the old object
   set and fails with the same undefined symbol.
3. **The firmware's own log goes to stdout, not `os_log`.** `simctl spawn log
   show` shows the `SDL_Log` half and none of the `[ACT]`/`[ERS]`/`[SCT]`
   lines. Launch with `--console-pty` or the activity trail is invisible.
4. **The reader opens on a blank page** (above). Four consecutive runs read as
   "the chain is dead" when they were measuring a cover wrapper. Since the
   cover ruling that page reports `fb=43B view=1`, so it no longer *looks* like
   a dead chain — but `page=0B rects=0` still means you are not measuring the
   firmware's capture.
5. **The tree dump used to fire on the first publish**, which is always that
   same empty cover page — so every dump ever collected for this bug was of an
   empty container over a page with nothing in it. Fixed 2026-08-23: it fires
   on the first page that has text.

---

## 6. Tests that now hold this

| Test | Holds |
|---|---|
| `tests/readaloud_geometry_test.cpp` | `src/ReadAloudGeometry.h`: not answerable before the first present (the level-triggered self-heal depends on it), the iPhone Air's measured numbers, `panelBottom` as an EDGE not an origin, a scale-less screen meaning 1x rather than a NaN frame, a strictly positive scale, and that `DISPLAY_HEIGHT` in place of `LOGICAL_HEIGHT` produces a detectably wrong answer. Mutation-checked: three separate breakages of the header each fail it |
| `tools/axprobe` `testSpeakScreenIsServedThePageWithASaneFrame` | through Apple's real out-of-process channel: the `crosspoint.page-textinput` element exists, carries non-empty text, and is framed over the screen rather than collapsed or off it |
| `tools/axprobe` `testRealSpeakScreenFlagReachesThePageView` | the same on the SHIPPED branch (`SpeakThisEnabled`), not the override. Skips, rather than fails, on a simulator where the flag was not set |
| `tests/spoken_page_text_test.cpp` | `src/SpokenPageText.h`: that a one-word page speaks its word and not the book (the fallback substitutes, never supplements), that an unnamed book speaks nothing at all rather than the front recents entry's title, the exact-path match, the sentence's punctuation, and JSON that is not the shape a naive reader assumes -- braces, quotes and the text `"path"` inside a title, `\u` escapes including a surrogate pair, unknown fields of every type, and nine broken documents. Mutation-checked: guessing the front entry, appending the book to a real page, and breaking one escape each fail it |
| `tools/axprobe` `testCoverPageSpeaksTheBookInstead` | through Apple's real out-of-process channel: a page with NO text vends an element, carrying the fallback's own words, framed over the panel -- and no line elements over the panel, so VoiceOver's blank page is unchanged |

All three pass as of 2026-08-23 against the instrumented build:

```
AXPROBE page-textinput value: 715 chars -- "proceeded to climb over. Up came the dog and ran off with th"
AXPROBE page-textinput frame=(34.0, 132.0, 352.0, 528.0) screen=(0.0, 0.0, 420.0, 912.0)
AXPROBE real-flag page-textinput value: 705 chars
** TEST SUCCEEDED **
```

The middle line is the one that matters most: the SHIPPED branch — real
`SpeakThisEnabled`, no override — builds the page view and hands 705 characters
of the displayed page to Apple's own out-of-process channel.

The cover pair, re-measured after the 2026-08-23 ruling — the same run, one page
apart, and the whole change in two lines:

```
AXPROBE cover page-textinput value: "English Fairy Tales. This page has no text."
AXPROBE page-textinput value: 520 chars -- "The Project Gutenberg eBook of English Fairy Tales This eBoo"
** TEST SUCCEEDED **
```
| `tests/test_read_aloud_capture.sh` | links 1–2 end to end against a generated EPUB |
| `tests/read_aloud_channel_test.cpp`, `tests/read_aloud_core_test.cpp` | the channel's hand-off contract and every state transition |

None of these can see whether iOS *speaks*. That remains device-only.

---

## 7. "It seems to have an underlining" — build 132, 2026-08-23

Owner report, on the phone, on the build where Speak Screen first worked:
*"reading works. though it seems to have an underlining."*

**The underline is drawn by iOS, not by this app, and it is the Speak Screen
SENTENCE highlight whose shipped default style is Underline.** Everything below
is measured; the one thing that is not is his own phone's setting, which cannot
be read from here.

### The app's own read-aloud highlight is a BLOCK — excluded in pixels

`CrossPointReadAloud_paintHighlight` (`ios/CrossPointReadAloud.mm`) is a
`SDL_RenderFillRect` of the word rect inflated 2 px on every side, warm marker
at alpha 80 light / 60 dark. Reproduced on an iPhone Air simulator, same book,
same page, same restored `Documents/.crosspoint` per arm, `readAloudEnabled`
true vs false: the only difference in the band is a solid rectangle over the
spoken word, 1060x200 device px band at 21.5 % content coverage, effect mean
12.2 code values / max 42 / 33.2 % of pixels moved by more than 4. **No arm of
this app draws a line under anything.** So an underline on the glass is the
system's.

### The rects are the right shape — full line box, not ink extent

Measured on `/books/ai-engineering-from-zero.epub`, X3 at 2x, logical panel
pixels (`CROSSPOINT_SIM_READALOUD_LOG=2` against a screenshot of the same
frame):

| Quantity | Value |
|---|---|
| `ReadAloudWordRect.h`, every rect on the page | **51** |
| Line pitch (successive rect `y`: 255, 306, 357, 408, 459, 510, 561, 612, 663) | **51** |
| Ink top (cap height) within a band starting at `B` | `B + 12` |
| Baseline (measured on a descender-free line) | `B + 40` |
| Descender bottom | `B + 47` |
| Rect bottom edge | `B + 50` |

So `h` **is** the line box: the bands are contiguous, each rect's bottom is the
next rect's top. `selectionRectsForRange:` unions those per line, which is the
shape WWDC26-219 prescribes. A second book agrees through a different route:
`139 word rects -> 22 line elements; first ... 299x23 pts` at panel scale
0.667 pt/px, i.e. 34.5 logical px, again that font's line pitch.

An underline drawn at the bottom of such a rect therefore lands **11 logical px
below the baseline and 3 px below the descenders** — about 7.3 pt on the phone
against a 34 pt line. That is a normal-looking underline, not a detached rule,
and it is exactly where UIKit puts one for any full-line-fragment selection
rect. There is nothing to fix in the geometry.

### iOS's own default IS Underline — read off a clean simulator

`Settings > Accessibility > Spoken Content > Highlight Content`. The
preferences live in `com.apple.Accessibility` beside `SpeakThisEnabled`, and the
key names are not the obvious guesses:

| Setting | Key | Getter | Clean iOS 26.5 simulator |
|---|---|---|---|
| Highlight Content | `QuickSpeakHighlightTextEnabled` | `_AXSQuickSpeakHighlightTextEnabled()` | **NO** (off) |
| Words / Sentences / both | `QuickSpeakHighlightChoice` | `-[AXSettings quickSpeakHighlightOption]` | **3** = Words and Sentences |
| Sentence Highlight Style | `QuickSpeakUnderlineSentence` (bool) and the option below | `-[AXSettings quickSpeakSentenceHighlightOption]` | **1** |
| Word / Sentence color | `QuickSpeakWordHighlightColor`, `QuickSpeakSentenceHighlightColor` | — | 0 |

The enum's meaning comes from Apple's own settings plist, not from a guess —
`/System/Library/PreferenceBundles/AccessibilitySettings.bundle/HighlightContentSettings.plist`:

```
{ "_sentenceHighlightOption" => "1", "label" => "UNDERLINE" }
{ "_sentenceHighlightOption" => "2", "label" => "HIGHLIGHT" }
```

So the moment Highlight Content is switched on, iOS highlights the spoken WORD
with a background block and underlines the spoken SENTENCE. Nothing in this app
selects that; nothing in this app can override it.

Read them on any booted simulator with a throwaway iphonesimulator binary that
`dlopen`s the two private libraries and calls the getters — `defaults read`
shows only keys that have been WRITTEN, and every one of these is unset on a
clean device, which is precisely when the defaults are what matters.

Two traps in reading them, both hit on 2026-08-23. **Check the property type
before casting a getter's return** (`class_getProperty` +
`property_getAttributes`): `quickSpeakSentenceHighlightOption` and
`quickSpeakHighlightOption` are `Q` (NSUInteger) and read cleanly, but several
neighbours in `AXSettings` are `NSNumber *` properties and a `BOOL` cast of one
of those reads the low byte of a pointer. And **the enum is the trustworthy
half**: `quickSpeakUnderlineSentence` (a real `B`) read NO on the very first
call of a fresh boot and YES on every call after, with a byte-identical
`com.apple.Accessibility.plist` and the key persisted nowhere on the device —
it answers off a cache the accessibility daemon publishes, so a first read can
race it. `quickSpeakSentenceHighlightOption` returned 1 on every read including
that first one, and it is what Apple's own settings row binds to.

### What could NOT be measured, and why

**Speak Screen cannot be invoked in the Simulator.** Three routes were tried on
2026-08-23 and all three failed, so the next session does not pay for them
again:

1. The two-finger swipe from the top edge — XCUITest has no arbitrary
   multi-touch API. (Already recorded in §4.)
2. The **Speech Controller** (`ShowSpeechController` in the same domain, the
   floating play button). Set through `-[AXSettings setShowSpeechController:]`,
   confirmed by read-back, and it never appeared — not on a fresh launch and not
   after `launchctl stop com.apple.SpringBoard`.
3. `SpeakThisServices` — the real client API, in
   `/System/Library/PrivateFrameworks/SpeakThisServices.framework`:
   `+[SpeakThisServices sharedInstance]`, then
   `-speakThisWithOptions:errorHandler:` (also `…forAppWithBundleID:` and
   `…forSceneID:`). Called from inside the frontmost app through
   `SIMCTL_CHILD_DYLD_INSERT_LIBRARIES`. **The call is accepted — no error
   handler ever fires — and nothing happens:** no speech, zero changed pixels
   across ten screenshots, and not one `TEXTINPUT` line, so the protocol was
   never consumed. The UI server behind it does not run in the Simulator.

Therefore: **UNCONFIRMED on device** that the line he sees is this underline.
It is the only drawer left once the app's own highlight is excluded in pixels,
and its default is Underline — but nobody has photographed it.

### CLOSED 2026-08-23 — the underline is iOS's, and the owner is keeping it

Owner: *"consider it resolved."*

Recorded so it is not re-investigated. The reported underline under spoken text
is **iOS's own sentence-highlight style**, not anything this app draws. Our
selection rects were measured and are correct: full line-box height, contiguous
band to band, with the bottom edge where UIKit puts an underline for any line
fragment.

If it ever comes back as a report, the first thing to check is
**Accessibility > Spoken Content > Highlight Content > Sentence Highlight
Style** — not our geometry. The path from there to the enum values is in §7
above.

No code changed for this, and none should.

---

## 8. "It is happening again" — 2026-08-26, and the report is NOT about today

Owner, 2026-08-26: *"'no speakable content could be found on the screen' error
is happening again"*, and then, correcting the framing: **"it was broken before
today."** Build 132 (2026-08-23) is where he reported the opposite —
*"reading works. though it seems to have an underlining"* (§7) — so the window
is builds 133–143 and the report is a RECURRENCE, not a first failure.

**It was not reproduced.** Everything below is either a measurement or a defect
found by reading, and the two are labelled apart, because the standing rule
after 2026-08-09 is that a second failure gets instrumentation rather than
another plausible patch.

> **SUPERSEDED BY §9, 2026-08-26.** The cause was found and reproduced: the
> capture flag is re-seeded FALSE on every in-process reboot and the correcting
> edge never fires again (S-023). Nothing measured in this section was wrong —
> the chain really is healthy from a cold launch, which is exactly why none of
> it explained the report. **Every measurement here was taken from boot 1, and
> the condition needs a reboot.** The three self-heal holes below are real and
> their repairs stand; they were not the reported bug. Keep reading this section
> for what was checked and found CLEAN, not for the conclusion.

### Measured healthy on HEAD (`a8def02`), and none of it explains the report

| Checked | Result |
|---|---|
| `tests/run_all.sh` | 55/55 before the change, 56/56 after |
| `tests/test_read_aloud_capture.sh` against firmware `57bb08721` | PASS — links 1–2 end to end, 14 rects containing their word's ink |
| CHAIN on body pages, iPhone Air sim, iOS 26.5, real `SpeakThisEnabled` | healthy and identical in shape to §4: `page=520B rects=94 fb=0B geo=1(34,85 x0.667) view=1 frame=(34,85 352x528) inWindow=1 elements=16` |
| CHAIN on front matter and on the cover | `page=0B rects=0 fb=43B view=1` — the cover fallback still fires |
| `tools/axprobe`, all four tests | PASS, including the SHIPPED branch: 520 characters served to Apple's own out-of-process channel |
| A sleep entry from inside the reader | chain unchanged across it (`view=1 inWindow=1`) up to the deep-sleep loop |

**Today's commits are ruled out as the cause and the bisect was abandoned on the
owner's correction, not on evidence** — worth saying plainly so nobody reads the
list below as cleared. What WAS read and found unrelated to the chain:
`a8def02` (the trail upload skip and the two `CADisableMinimumFrameDuration`
keys), `e21e078` + firmware `b959132a4` (the reading ledger, which publishes
from `renderContents` beside `captureReadAloudPage` and does not disturb it),
the three Tier 2 refactors, and firmware `01fbab3e4`'s screen identity. The
a11y sources themselves have not changed since 2026-08-23.

Also checked and CLEAN, so it is not re-derived: `readaloud::buildCapture`
appends a rect on every append to `text`, so "text with no rects" — which
`setPage` would turn into a `clear()` with no fallback, because
`g_pageTextless` keys on empty TEXT — is unreachable. `readAloudEnabled`,
`readAloudRatePercent` and `diagnosticsEnabled` all still read `NSUserDefaults`
after the 2026-08-23 freeze pass (`2cace19` rewrote `CrossPointPrefs.mm` and
left all three live) and all three rows are still in `Root.plist`. There is no
`TARGET_OS_SIMULATOR` anywhere in `ios/` or `src/`, so device and simulator
compile the same code.

### Found by reading: THREE holes in the level-triggered self-heal

The self-heal is the thing that makes this chain survive at all. The firmware
publishes a page ONCE, when it renders it, and an e-ink reader can go minutes
without rendering another — so anything lost between two page turns is invisible
until the next one, and what the owner gets meanwhile is exactly the reported
sentence over a page that is on the glass. That is why the 2026-08-09 fix made
the check LEVEL-triggered. **It did not finish the job**, and all three
remainders are silent, are unreachable from a healthy launch, and therefore
passed every measurement in §4 and every one in the table above.

1. **A page published before the container existed is dropped and never
   retried.** Both push paths return early on `g_overlay == nil`, leaving
   `g_builtMode` at `-1`, and `modeChanged()` read `-1` as "nothing built,
   nothing stale" and returned false. The TEXT page survived it by accident,
   because its caller also retried on an empty container. The **cover** could
   not: a textless page publishes no line elements by design, so an empty
   container is its correct steady state and cannot be its retry condition.
   `modeChanged()` was its only retry. A cover whose first push was dropped
   vended nothing for the rest of the session — which is the precise symptom
   the cover fallback was written to end.
2. **`keepFront()` could not recover the one loss that is reachable.**
   `g_overlay` is `__weak` and its only strong reference is its superview, so
   "removed from the window" and "the pointer reads nil" are the same instant —
   which makes the `!overlay.superview` recovery branch **dead code** and made
   the `if (!overlay) return;` early exit the live path. Nothing else recreates
   the container; both push paths return early on a missing one. So a container
   lost once, or never installed because `resolveWindow()` was not answerable at
   `CrossPointHarness_begin()` time, stayed lost for the whole session.
3. **"Does a page view object exist" is not "can anything reach it."** A page
   view retained by a host that has itself been detached answers yes to the
   first and no to the second; assistive technology traversing from the window
   finds nothing while every log line says the view is there.

### The fix, and where the decision now lives

`src/ReadAloudExposure.h` — pure, host-tested by
`tests/readaloud_exposure_test.cpp`, for the same reason `SpokenPageText.h` and
`ReadAloudGeometry.h` beside it are: `ios/CrossPointAccessibility.mm` compiles
only on a Mac, cannot be single-stepped on a phone, and every way this
predicate can be wrong is a sentence spoken by iOS on somebody else's device.
`modeChanged()` is retired for `CrossPointAccessibility_exposureOutOfStep()`
and `_textPageOutOfStep()`, the second of which folds in the `hasElements()`
term its caller used to have to remember — a caller that had to OR it in is
exactly how the textless page ended up with a weaker heal than the text page.
`keepFront()` reinstalls when the container is nil.

Mutation-checked rather than trusted green: six of the test's assertions fail
against the boolean it replaces, and the three marked `REGRESSION` are the three
holes above.

**Evidence it still works** — the same run that proves the fix changes nothing
about the healthy path, through Apple's real out-of-process channel:

```
AXPROBE cover page-textinput value: "English Fairy Tales. This page has no text."
AXPROBE staticTexts count: 16
AXPROBE real-flag page-textinput value: 520 chars
AXPROBE page-textinput frame=(34.0, 85.3, 352.0, 528.0) screen=(0.0, 0.0, 420.0, 912.0)
** TEST SUCCEEDED **
```

and the live chain, with no rebuild storm (41 `[A11Y-FILE]` lines in a 40 s run,
ten of them CHAIN):

```
CHAIN wants=1 page=26B rects=4 fb=0B geo=1(34,85 x0.667) view=1 frame=(34,85 352x528) inWindow=1 elements=2
```

The storm was worth checking and is the risk this predicate carries: it is asked
every frame, and a rebuild re-adds a subview and posts
`UIAccessibilityScreenChangedNotification`. A false positive here is not a
wasted branch, it is a notification storm at the display rate aimed at the
assistive technology the chain exists to serve. The first assertion in the test
is that a healthy exposure is left alone.

### A TRAP THAT COST A RUN, and it is in axprobe's own README

The suite FAILED once mid-session with `staticTexts count: 0` and
`cover page-textinput exists: false` — a perfect picture of the reported bug,
produced entirely by **reading position**. Earlier scripted runs had walked the
book past the point the cover test's ten `QTAP:LEFT` can recover, so it was
measuring pages that legitimately have nothing on them. Reset before
concluding anything:

```bash
D=<udid>; C=$(xcrun simctl get_app_container $D com.natebunnyfield.crosspoint.x3 data)
rm -rf "$C/Documents/.crosspoint/epub_"*
```

This is the same class of mistake as §5's trap 4 and it now has a second entry
in this document because it fooled a session that had already read the first.

### WHAT TO ASK FOR FROM THE PHONE, and what each answer means

The instrument for this is already shipped and needs no new build: **Settings.app
→ CrossPoint X3 → Diagnostics Log**, then reproduce, then Files → On My iPhone →
CrossPoint X3 → diagnostics → `a11y.log`. Read the CHAIN line at the moment of
the failure; its shape names the link, and each of the three holes above has its
own signature:

| CHAIN at the moment of failure | What it means |
|---|---|
| `page=NNNB rects=NN ... view=0 ... elements=0` | hole 1 or 2 — the container was never installed or was lost, and nothing recreated it |
| `page=0B rects=0 fb=0B` on a book page | the firmware captured nothing, i.e. links 1–3, not the exposure |
| `page=0B rects=0 fb=0B` on a cover | the book could not be NAMED (`spokenpage::forPage` returned empty), so iOS reporting nothing is the truth; check `openEpubPath` against `recent.json` |
| `view=1 ... inWindow=0` | hole 3 — the page view exists and nothing can reach it |
| `wants=0` | Speak Screen is off as far as the app can tell; `UIAccessibilityIsSpeakScreenEnabled()` is the only input |
| every link populated, `inWindow=1`, and NO `TEXTINPUT` line after the failed invocation | iOS never asked. That is the 2026-08-09 signature and nothing in this app can fix it |

That last row is the one worth the trip: `CPPageTextInputView` logs
`TEXTINPUT ... the UITextInput protocol is being consumed` on the first queries
after each page change, so the log distinguishes "iOS asked and got nothing"
from "iOS never asked" — which is still the one difference between this
measurement and his phone that no simulator can settle (§3, §7).

**Device-unconfirmed.** Nothing here was seen on a phone. Three defects were
found and repaired; whether any of them is the one he hit is unknown, and the
honest status is SHIPPED — UNCONFIRMED on device.

---

## 9. FOUND, REPRODUCED AND FIXED — 2026-08-26 (S-023)

**§8's conclusion is superseded, not deleted.** Everything it measured was
true — the chain IS healthy on HEAD from a cold launch, and that is precisely
why nothing in it explained the report. The condition is not reachable from a
cold launch at all. It needs a **reboot** in the middle of the session, and
every measurement in §8 was taken from a first boot.

### The mechanism

One flag, two writers that had drifted apart, across a boundary that resets one
of them and not the other. Full account with the owner's log excerpt and both
measured arms: `BUGS.md` **S-023**. In brief:

* `CrossPointReadAloud_begin()` seeded the firmware's capture flag from
  `CrossPointPrefs_readAloudEnabled()` — correct before capture became
  unconditional on the phone (the build-42 fix for the *previous* incarnation of
  this same message), never updated with it. A Speak Screen user leaves the Read
  Aloud (Experimental) toggle OFF, so begin() seeded **false** on every boot.
* `CrossPointReadAloud_perFrame()` corrected it to true on the edge
  `g_lastCaptureWanted != 1`.
* The iOS reboot is a `longjmp` into `setup()` in the SAME process.
  `ReadAloudChannel::resetForReboot()` deliberately leaves `wanted_` alone
  ("the consumer re-seeds it"), begin() re-seeds it **false**, and
  `g_lastCaptureWanted` survives at 1 — so the correcting edge never fires
  again. `readAloudCaptureWanted()` is false for the rest of the process,
  `captureReadAloudPage` returns at its first line, and `page=0B` forever.
* `fb=0B` follows from the same root and needs no separate fix: the
  textless-page fallback is only computed inside the drain's `if (got)` block,
  so a channel that never delivers starves the substitute too.

Every file transfer, every font download and every sleep/wake crosses that
boundary. **This is exactly the trap `CLAUDE.md` documents** — a static that
caches state across the in-process reboot works on the desktop and is dead on
the phone — with the twist that the comment saying "the consumer re-seeds it"
was true of a consumer that had an edge guard in front of its re-seed.

### Running it, and why the §5 recipe cannot show this

The §5 script never reboots, so it can only ever measure boot 1. Add a
sleep/wake to cross the `longjmp`:

```bash
D=<udid>
SIMCTL_CHILD_CROSSPOINT_SIM_DIAGNOSTICS=1 \
SIMCTL_CHILD_CROSSPOINT_SIM_LOG_POWER=1 \
SIMCTL_CHILD_CROSSPOINT_SIM_INPUT_SCRIPT='200:QTAP:BACK:2500;5000:QTAP:BACK;10000:QTAP:RIGHT;13000:QTAP:RIGHT;22000:POWER:700;28000:POWER:1' \
SIMCTL_CHILD_CROSSPOINT_SIM_INPUT_SCRIPT_AFTER_WAKE='7000:QTAP:RIGHT;11000:QTAP:RIGHT;18000:QUIT' \
  xcrun simctl launch --console-pty $D com.natebunnyfield.crosspoint.x3
```

`22000:POWER:700` is the firmware's own sleep threshold and `28000:POWER:1` is
the wake; `[power] longjmp reboot (power wake)` in the output is the boundary
being crossed, and it is the line to grep for before believing any post-reboot
CHAIN. Measured on `crosspoint-x3-air`, iOS 26.5, 2026-08-26, same script both
arms:

| | before the reboot | after |
|---|---|---|
| pre-fix | `page=746B rects=151`, `790B/165`, `780B/156` | `page=0B rects=0 fb=0B` at +0 s, +5 s, +10 s, +15 s, across two page turns |
| fixed | `page=812B rects=158 elements=22` | `page=812B rects=158 elements=22`, then `746B/151` after a turn |

**The cheapest single tell** is `[READALOUD] page capture wanted (always, on
iOS)`: it prints once per boot when the chain is healthy, and exactly once for
the whole process when it is not.

### What holds it

`tests/readaloud_reboot_seed_test.py`, in `tests/run_all.sh`. It fails on all
three of its properties against the pre-fix file, and its third assertion is the
general one — every `int g_last* = -1;` edge cache in the adapter must be
re-armed in `begin()`. Source-level for the same reason
`chip_tint_source_test.py` is: the live check needs UIKit, a booted phone and a
reboot mid-run.

### The sibling audit, including what was CLEAN

Nine other edge-cached statics cross the same boundary
(`g_appliedDark`/`Outline`/`Fill`, `pollBeamPaint`, `pollPageFade`,
`pollPanelGlow`, `pollLetterpress`, `pollPaperTooth`, `pollScanlines`). **None
has this bug**, and the reason is structural rather than lucky:
`gDisplayRebootReset` does not touch the surface dials — they are atomics in
`HalDisplay` that survive the `longjmp` — so a stale poll edge is suppressing a
push of a value that is already applied. `applyTheme()` writes `g_appliedDark`
unconditionally on every `CrossPointHarness_begin()`, so that edge is re-armed
by construction. `fontFamilyStepChannel` has no wanted flag and no consumer-side
edge at all.

**A surviving edge cache is only a bug where something else RESETS what it
mirrors.** That is the pair to look for when auditing this class, not the static
by itself.
