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
| `CrossPointAccessibility.mm` / `CrossPointPageTextInput.mm` compiled into the app | yes — `ios/CMakeLists.txt` :49/:53 and :78/:80, and the AX runtime serves the view |
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
