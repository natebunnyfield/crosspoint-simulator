# PLAN: Read-aloud TTS on the iOS harness (Apple speech)

**Status: planned, not started.** Tracked as ST-003 in [TODO.md](../TODO.md).
Written 2026-08-07 against `main` @ `ebf2b54`; revised the same day to lead
with decisions and risks rather than mechanics.

The end state: on the phone, with a book open, the app reads the page aloud in
the system voice the owner picked in Settings > Accessibility > Spoken Content
> Voices, turns the page by itself when it reaches the bottom, highlights each
word as it is spoken, and starts reading from any word the owner taps. All of
it lives behind a default-off toggle in Settings > CrossPoint X3.

The owner's four increments map onto the phases like this:

| Asked for | Phase(s) here |
|---|---|
| "spike that it is possible" | 0A (speech plumbing) + 0B (text capture) + 1 (the two joined) |
| "make it turn the page" | 2 |
| "highlighting as it reads" | 3 |
| "start at a given selected word" | 4 |

The split of the spike into 0A/0B is deliberate and is the main thing this
revision changes: *"can the phone speak?"* is not the risk — AVSpeech is a
mature API and 0A is an afternoon. The risk that can sink the whole feature is
*"can the firmware produce clean, speakable page text?"* (R1 below), and it is
provable headlessly on Linux with no Mac and no audio. So it gets its own
spike and an explicit go/no-go gate before any composite work starts.

Rules of engagement for the implementer (unchanged, and they matter):

- **Do the phases in order**; each is a separate PR per repo and must pass its
  full acceptance checklist — and its gate, where one exists — before the
  next phase starts.
- **Never skip a Traps section**; every entry is either a bug this repo
  already had once or an API behaviour that was checked.
- **When reality contradicts a step**, stop and re-read the phase's Traps and
  the Contracts section rather than improvising.
- **The desktop PlatformIO build is the canary.** After every simulator-repo
  change: desktop build green, `tests/run_all.sh` green.

Two repos are involved:

| Repo | Role |
|---|---|
| `crosspoint-simulator` (this repo) | The channel (HAL surface), the pure state machine, the AVSpeech adapter, the highlight overlay, the tap hit-test |
| `natebunnyfield/crosspoint-reader` @ `x3-main` (the firmware fork) | Capturing page text + word rects during page render, publishing them, clearing on reader exit, inline no-ops so the device build still links |

Simulator-side changes land first in every phase pair (the firmware compiles
against this repo's HAL surface). The device build never breaks: every
firmware-facing method gets an inline no-op in the firmware's
`lib/hal/HalGPIO.h` in the same firmware PR that starts calling it — the
exact precedent is `setTextEntryActive` / `consumeTypedText` (2026-08-06).

---

## Decisions

Each records the alternatives actually weighed, so nobody relitigates them
mid-implementation — and so a wrong call is at least a *visible* wrong call.

**D1 — Page text comes from the firmware's own layout pass, over a new HAL
channel.** Alternatives considered:
- *Harness parses the EPUB itself* (it can read the file). Rejected: the
  harness cannot know which text is on the current page — pagination depends
  on font, size, margins, and the firmware's layouter, and re-implementing
  that is a second pagination engine that drifts from the first on every
  firmware change. The firmware already knows; ask it.
- *VoiceOver Screen Recognition (on-device OCR).* Rejected as the mechanism:
  zero-code but no page-turn integration, no reliable reading order, no word
  callbacks for highlighting, unlabeled pad buttons. Worth a five-minute
  manual experiment for curiosity, not a foundation.
- *Expose page text as a `UIAccessibilityElement` and let Speak Screen read
  it.* Rejected as the driver: Speak Screen reads one screenful and stops (no
  auto page-turn), provides no word-level callbacks (no highlight), and no
  start-at-word. But once the channel exists this is nearly free and is a
  genuine accessibility win for VoiceOver users — recorded as optional
  Phase 5, out of scope for the four asked-for increments.

**D2 — Speech engine is `AVSpeechSynthesizer` with the system default voice**
(`voiceWithLanguage:nil`), which honours the voice the owner picked under
Spoken Content — same voices, same engine as Apple's built-in screen reading.
Per-book language voices (EPUB `dc:language`) and a rate control are deferred
(Non-goals).

**D3 — Page turns are a real injected button press**
(`HalGPIO::injectButtonDown/Up`), not a call into reader internals. The
firmware's own handler then does pagination, progress persistence, chapter
boundaries, and end-of-book behaviour. Injection is the same API the
on-screen pad uses, so edge AND level reads work (`src/HalGPIO.h:71-93`).

**D4 — The channel lives on `HalGPIO`,** mirroring the host-keyboard channel
precedent (firmware-facing half + simulator-only half), and its full
four-argument signature is fixed in Phase 0B even though rects arrive only in
Phase 3 — the firmware-facing surface gets touched exactly once.

**D5 — The toggle is phone state** (Settings.bundle, like Keep Screen Awake),
not `settings.json`: device hardware has no speaker, so the setting means
nothing off the phone.

**D6 — The highlight is drawn by the simulator overlay,** not by the firmware
re-rendering the word inverted. A per-word e-ink refresh has no analog on
hardware and would push presentation-rate rendering into a firmware built
around rare refreshes; the overlay already paints over the presented panel on
the main thread. Accepted cost: `CROSSPOINT_SIM_SCREENSHOTS` captures
pre-composite, so the highlight is verifiable only on-glass.

**D7 — All decision logic is a pure, clock-free class**
(`ios/ReadAloudCore`), PadCore's discipline: AVSpeech-free, SDL-free, time
only as explicit inputs. That is what makes phases 2–4 testable on Linux in
`tests/run_all.sh` even though the adapter itself only compiles on a Mac.

---

## Risk register

Ordered by expected damage × discovery lateness. "Owner" is the phase whose
acceptance proves the risk retired.

| # | Risk | Owner | De-risk / kill criterion |
|---|---|---|---|
| R1 | The layout pass cannot yield clean reading-order text: hyphenated line-break fragments ("consid-"/"eration"), justified-text word splitting, headers/footers/page numbers interleaved, soft hyphens (U+00AD) spoken aloud | **0B** | Gate G0's word-for-word audit on three books. Two capture strategies specified; if NEITHER yields clean text, STOP — the feature as designed is not viable and the plan returns to the drawing board rather than shipping garbled speech |
| R2 | Word rects drift from the published text (offsets computed in a different pass than the string) | 3 | Contract requires text and offsets built in one pass; multibyte core test + on-glass drift check |
| R3 | `NSRange` is UTF-16 code units, channel offsets are UTF-8 bytes; ASCII books pass, curly quotes drift | 3 | Conversion snippet specified; multibyte unit test; curly-quote book on-glass |
| R4 | Capture fires for a page that is not the displayed one (pre-rendering, cache warms) | 0B | Gate G0: page back/forward, generation count must track the visible page exactly |
| R5 | Rect coordinates arrive in render-scaled pixels (iOS runs 2x) and the highlight lands at half size | 3 | Contract: logical portrait px, firmware divides by its own scale; acceptance step names the symptom |
| R6 | Speech inaudible on muted phones (audio session category) | 0A | `AVAudioSessionCategoryPlayback` in the spike; physical-device check |
| R7 | Async `didCancel` from a stop kills the *next* utterance | 1 | Utterance serial filter, specified; test row |
| R8 | End of book leaves the state machine hung waiting for a page | 2 | Adapter timeout input (core stays clock-free); test row |
| R9 | Per-word `requestPresent` breaks the presents-rarely model | 3 | Event-driven presents only on highlight *change*; word rate is a few Hz — measure in 3's acceptance, cap to sentence granularity if it matters |
| R10 | Non-English books spoken in the wrong voice | — | Accepted for v1 (Non-goals); revisit with `dc:language` |

---

## Invariants this feature must not break

Restated from CLAUDE.md because every one is load-bearing here:

1. **The HAL public surface mirrors the firmware's.** Firmware-facing methods
   added to `src/HalGPIO.h` get identical-signature inline no-ops in the
   firmware's `lib/hal/HalGPIO.h`. Simulator-only methods must NOT gain
   firmware counterparts.
2. **SDL render calls happen only on the main thread**, inside the
   `presentIfNeeded()` path — the highlight paints from the existing
   `SimulatorOverlay` draw callback and nowhere else.
3. **`HalGPIO::update()` owns the SDL event pump.** The tap detector observes
   through the already-installed `padWatch` event watch; no new pump, no poll.
4. **PadCore stays pure passthrough** — no gestures, timers, or word logic
   added to it. New logic goes in `ios/ReadAloudCore.*`, likewise clock-free.
5. **No new cross-cutting compile definitions.** This feature adds none; if
   one ever becomes necessary it goes on `crosspoint_core PUBLIC`, never the
   app target (split-brain guard).
6. **Presents are event-driven** via `SimulatorOverlay::requestPresent()`,
   never per-frame.
7. **Firmware settings vs phone settings** — see D5.

---

## Architecture

```
  firmware (fork x3-main)                 simulator repo
  ─────────────────────────              ──────────────────────────────────────
  EpubReader page render ──captures──▶  HalGPIO::publishReadAloudPage()
    (only when                             │  (ReadAloudChannel, mutex'd)
     readAloudCaptureWanted())             ▼
  reader exit ──publishes nullptr──▶   consumeReadAloudPage()   [simulator-only]
                                           │ drained on the main thread,
                                           │ once per frame, by ONE consumer
                                           ▼
              desktop: env-gated logger in simulator_main.cpp  (Phase 0B proof)
              iOS:     ios/CrossPointReadAloud.mm  (AVSpeech adapter, ObjC++)
                            │ owns AVSpeechSynthesizer + AVAudioSession
                            │ delegate events → locked queue → perFrame drain
                            ▼
                          ios/ReadAloudCore.{h,cpp}   (pure, clock-free, tested)
                            │ inputs: pageArrived / willSpeakByte / finished /
                            │         canceled / pageTimeout / tapAtLogical /
                            │         setEnabled
                            │ actions: StartUtterance / StopUtterance /
                            │          TurnPageForward / SetHighlight /
                            │          ClearHighlight
                            ▼
        adapter applies actions:
          speak/stop        → AVSpeechSynthesizer
          TurnPageForward   → gpio.injectButtonDown/Up(page-forward button)
          highlight state   → painted by the SimulatorOverlay callback,
                              SimulatorOverlay::requestPresent() on change
```

---

## Contracts (fixed in Phase 0B, stable through Phase 4)

### The published text — what "page text" means

This is the contract R1 lives or dies by. The UTF-8 string published for a
page is the **logical text of the page's content region**, meaning:

- Reading order, single ASCII spaces between words, `\n` between paragraphs.
- **No layout artifacts**: hyphens inserted by line breaking do not appear;
  soft hyphens (U+00AD) are stripped; a word split across lines appears once,
  whole.
- **No page furniture**: chapter header, page number, progress indicator,
  battery/status chrome are excluded — only the book content the owner would
  read aloud themselves.
- Images contribute nothing (their captions are content text if the reader
  renders them as text).

Two capture strategies can satisfy this; Phase 0B picks at Gate G0:

- **Strategy 1 (preferred): slice the source.** A rendered page *is* a range
  of the underlying chapter text — the paginator computed that range to lay
  the page out. If the reader exposes "page N covers source range [a,b)",
  publish that slice (markup removed). Clean by construction: line-break
  hyphens never existed in the source.
- **Strategy 2 (fallback): accumulate the draw calls,** merging fragments and
  stripping U+00AD and layout hyphens, skipping draw calls that originate
  from furniture. More code, more ways to drift; only if the paginator's
  ranges are not recoverable.

### The channel surface on `HalGPIO`

Firmware-facing pair — identical field-for-field and signature-identical in
BOTH repos (`src/HalGPIO.h` here with real bodies; `lib/hal/HalGPIO.h` in the
firmware as inline no-ops):

```cpp
// POD, identical in both repos. Coordinates are LOGICAL PORTRAIT panel pixels
// (X3: 528 wide, 792 tall; x right, y down), independent of render scale —
// the firmware divides by its own render scale at capture time.
//
// A word the layout wrapped across lines publishes ONE RECT PER VISUAL
// FRAGMENT, all sharing the word's byteOffset/byteLen — the highlight paints
// every rect carrying the spoken range, so a hyphen-split word lights up on
// both lines.
struct ReadAloudWordRect {
  uint16_t x, y, w, h;
  uint32_t byteOffset;  // into the page's UTF-8 text; always a word start
  uint16_t byteLen;
};

// Device inline bodies (firmware repo):
bool readAloudCaptureWanted() const { return false; }
void publishReadAloudPage(const char * /*utf8*/, size_t /*utf8Len*/,
                          const ReadAloudWordRect * /*rects*/,
                          size_t /*rectCount*/) {}
```

The four-argument signature is fixed from Phase 0B; the firmware passes
`nullptr, 0` for rects until Phase 3. Text and rect offsets must be built in
**the same capture pass** (R2) — never recomputed from each other.

`publishReadAloudPage(nullptr, 0, nullptr, 0)` means **"there is no page"**:
the reader exited or the book closed. Consumers stop speech and clear the
highlight.

Simulator-only half (no firmware counterpart, like `injectButtonDown`):

```cpp
void setReadAloudCaptureWanted(bool wanted);
bool consumeReadAloudPage(ReadAloudPage &out);  // true once per publish
```

### `src/ReadAloudChannel.h` (new, pure, SDL-free)

Header-only state holder owned by `HalGPIO`, testable with a bare
`c++ -Isrc` compile exactly like `GrayscalePreview.h`:

```cpp
#pragma once
#include <atomic>
#include <cstdint>
#include <mutex>
#include <string>
#include <vector>

struct ReadAloudWordRect { /* as above */ };

struct ReadAloudPage {
  std::string utf8;                       // empty when cleared == true
  std::vector<ReadAloudWordRect> rects;   // empty until Phase 3 firmware
  uint32_t generation = 0;                // bumps on every publish, incl. clear
  bool cleared = false;                   // publish(nullptr) => true
};

class ReadAloudChannel {
public:
  void setWanted(bool w) { wanted_.store(w); }
  bool wanted() const { return wanted_.load(); }
  void publish(const char *utf8, size_t len,
               const ReadAloudWordRect *rects, size_t rectCount);
  bool consume(ReadAloudPage &out);       // true once per publish
private:
  std::atomic<bool> wanted_{false};
  std::mutex mutex_;
  ReadAloudPage page_;
  bool hasNew_ = false;
  uint32_t nextGeneration_ = 1;
};
```

`publish` copies under the mutex, bumps `generation`, sets `cleared` when
`utf8 == nullptr`, sets `hasNew_`. `consume` moves the page out and clears
`hasNew_`. Publisher is the firmware task; consumer is the main thread; the
mutex is the whole thread story. **Exactly one consumer per build** — the
env-gated desktop logger or the iOS adapter, never both (the logger sits in
`#if !CROSSPOINT_SIM_IOS`).

### Highlight semantics

`SetHighlight` carries a **byte range** `{byteOffset, byteLen}` — the spoken
word's range — not a rect index. The painter fills every rect whose
`byteOffset/byteLen` equal that range (the hyphenation contract above), so
split words highlight correctly with no special cases anywhere else. The core
dedupes: consecutive `willSpeakByte` inputs inside the same word emit nothing
new.

### Coordinate mapping (Phase 3)

Rects are logical portrait panel pixels; the presented panel rect in device
pixels comes from `SimulatorOverlay` (two accessors added in Phase 3 next to
the existing pair, stored at the same site in `src/HalDisplay.cpp:704-706`):

```cpp
// Main thread, inside the overlay draw callback:
const float S  = SimulatorOverlay::panelWidthPx()
               / static_cast<float>(HalDisplay::DISPLAY_HEIGHT); // portrait width == landscape fb height (X3: 528)
const float x0 = SimulatorOverlay::panelLeftPx();
const float y0 = SimulatorOverlay::panelBottomPx() - SimulatorOverlay::panelHeightPx();
SDL_FRect hl = { x0 + r.x * S, y0 + r.y * S, r.w * S, r.h * S };
```

Landscape reading is out of scope for all phases (the phone harness presents
portrait only).

### Log discipline

Every log line this feature emits starts with `[READALOUD] ` — that prefix is
what every acceptance step greps.

---

## Phase 0A — Spike: Apple speech inside this app  *(size S; Mac required)*

Retires R6 and proves the delegate→queue→main-thread pattern every later
phase scales up. No firmware involvement, no channel: with a new default-off
Settings toggle on, the app speaks one canned sentence at launch.

### Files

| File | Change |
|---|---|
| `ios/CrossPointReadAloud.h` | new — C-linkage API |
| `ios/CrossPointReadAloud.mm` | new — AVSpeech adapter (spike form) |
| `ios/CrossPointPrefs.h` / `.mm` | add `CrossPointPrefs_readAloudEnabled()` |
| `ios/Settings.bundle/Root.plist` | default-off toggle `read_aloud_enabled`, title "Read Aloud (experimental)" |
| `ios/CrossPointIOSShim.cpp` | call `CrossPointReadAloud_begin()` from `CrossPointHarness_begin()`, `CrossPointReadAloud_perFrame()` from `CrossPointHarness_perFrame()` |
| `ios/CMakeLists.txt` | add the `.mm` to the app target sources (next to `CrossPointAppearance.mm`); link `AVFoundation` mirroring how `NetworkExtension` is linked |

### Steps

1. `ios/CrossPointReadAloud.h`, mirroring `CrossPointHarness.h`'s style:

   ```cpp
   #pragma once
   // Read-aloud TTS: Apple speech (AVSpeechSynthesizer) speaking the page.
   // See .claude/PLAN-tts-read-aloud.md. All entry points main thread only.
   #ifdef __cplusplus
   extern "C" {
   #endif
   void CrossPointReadAloud_begin(void);     // idempotent across wakes
   void CrossPointReadAloud_perFrame(void);  // drain delegate events; cheap when idle
   #ifdef __cplusplus
   }
   #endif
   ```

2. `ios/CrossPointReadAloud.mm` spike body: statics for the synthesizer, a
   delegate object, a `std::mutex` + event vector, `bool s_spikeDone`.
   `begin()` creates synthesizer + delegate once (static-bool guard, the
   `s_watchesInstalled` idiom). `perFrame()`: if `!s_spikeDone` and
   `CrossPointPrefs_readAloudEnabled()`:

   ```objc
   AVAudioSession *session = [AVAudioSession sharedInstance];
   [session setCategory:AVAudioSessionCategoryPlayback
                   mode:AVAudioSessionModeSpokenAudio
                options:0 error:nil];
   [session setActive:YES error:nil];
   AVSpeechUtterance *utt = [AVSpeechUtterance speechUtteranceWithString:
       @"CrossPoint read aloud is working on this device."];
   utt.voice = [AVSpeechSynthesisVoice voiceWithLanguage:nil]; // owner's Spoken Content voice
   [s_synth speakUtterance:utt];
   SDL_Log("[READALOUD] spike utterance started");
   ```

   Delegate implements `didFinishSpeechUtterance` and
   `didCancelSpeechUtterance`; both only enqueue. `perFrame` drains and logs
   `[READALOUD] spike utterance finished` / `canceled`.

3. Prefs accessor copies the `CrossPointPrefs_wantsScreenAwake` shape
   (registerDefaults + `boolForKey:`), key `read_aloud_enabled`, default NO;
   Root.plist gets a `PSToggleSwitchSpecifier` mirroring an existing toggle.

### Acceptance

- [ ] iOS project configures (no identity-guard failure — no new defines).
- [ ] iOS Simulator, toggle ON: sentence audible; `started` then `finished`
      logged. Toggle OFF: silent, neither log line, session never activated.
- [ ] **Physical iPhone with the ring/silent switch on silent**: sentence
      still audible (this is the R6 check; the Simulator cannot make it).
- [ ] `tests/run_all.sh` passes (no desktop source touched).

### Traps

- **Everything main thread**; delegate callbacks arrive on a private queue
  and must only enqueue.
- **`.mm` cannot compile off-Mac** — that is why this phase is this small.

---

## Phase 0B — Spike: clean page text out of the firmware  *(size M; no Mac needed)*

The real feasibility spike (R1, R4). Deliverable: the channel exists in the
HAL, the firmware captures page text (Strategy 1 or 2), and a headless
desktop run proves the captured text is speakable — before any speech code
depends on it.

### Simulator repo

| File | Change |
|---|---|
| `src/ReadAloudChannel.h` | new — as in Contracts |
| `src/HalGPIO.h` | include it; add the four methods (documented like the text-entry block at lines 95–131, stating which half is firmware-facing); private `ReadAloudChannel readAloud;` |
| `src/HalGPIO.cpp` | four one-line delegating bodies |
| `src/simulator_main.cpp` | env-gated headless drain (below) |
| `tests/read_aloud_channel_test.cpp` | new |
| `tests/run_all.sh` | register it (below) |

Headless drain, inside the main loop after `loop()`, guarded
`#if !CROSSPOINT_SIM_IOS`:

```cpp
// Headless proof of the read-aloud capture (see .claude/PLAN-tts-read-aloud.md):
// CROSSPOINT_SIM_READALOUD_LOG=1 asks the firmware to capture page text and
// logs every publish. Desktop has no speech consumer; iOS must not compile
// this — its harness is the consumer and this drain would steal its pages.
static const bool readAloudLog = [] {
  const char *v = SDL_getenv("CROSSPOINT_SIM_READALOUD_LOG");
  if (v && *v == '1') gpio.setReadAloudCaptureWanted(true);
  return v && *v == '1';
}();
if (readAloudLog) {
  ReadAloudPage page;
  while (gpio.consumeReadAloudPage(page)) {
    SDL_Log("[READALOUD] page gen=%u cleared=%d bytes=%zu words=%zu | %.200s",
            page.generation, page.cleared ? 1 : 0, page.utf8.size(),
            page.rects.size(), page.utf8.c_str());
  }
}
```

`tests/read_aloud_channel_test.cpp` (compile: `c++ -std=c++20 -Isrc`, no
other TU): consume-empty false; publish→consume returns text and rects,
second consume false; publish twice → consume sees the second, generation
strictly increasing; `publish(nullptr,0,nullptr,0)` → `cleared`, empty text;
wanted flag round-trips. Register after the `task_registry` block:

```bash
run read_aloud_channel \
  c++ -std=c++20 -Isrc -o "$OUT/read_aloud_channel" tests/read_aloud_channel_test.cpp
```

### Firmware repo (work package FW-A)

On a branch off `x3-main`, simulator symlinked
(`simulator=symlink://../crosspoint-simulator`):

1. **HAL no-ops**: in `lib/hal/HalGPIO.h`, next to the text-entry no-ops, add
   `ReadAloudWordRect` and the two firmware-facing inline no-ops,
   byte-identical layout.
2. **Investigate Strategy 1 first**: find the paginator — how does the reader
   know where page N starts and ends? (`grep -rn "EpubReaderActivity" src/ |
   head`, then follow the page-render path; look for the structure that maps
   pages to positions in the chapter text.) If a source range per page is
   recoverable, capture = slice that range, strip markup and soft hyphens.
3. **Else Strategy 2**: accumulate the content-region draw calls in reading
   order, merge line-break fragments, strip U+00AD, skip furniture draws.
4. Either way: when `gpio.readAloudCaptureWanted()` is true during a page
   render, build the string; after the render completes,
   `gpio.publishReadAloudPage(text.c_str(), text.size(), nullptr, 0)`. When
   false, do nothing (the device build folds the branch away entirely).
5. **Clear on exit**: reader activity's exit path publishes
   `(nullptr, 0, nullptr, 0)`.
6. New translation units need the iOS source-set regen per CLAUDE.md; prefer
   hooking existing TUs.

### Gate G0 — go/no-go (run on desktop, headless)

Script pattern (per CLAUDE.md: open with `HOME`, believe `[ACT]` lines):

```bash
CROSSPOINT_SIM_READALOUD_LOG=1 \
CROSSPOINT_SIM_INPUT_SCRIPT='2000:HOME;3000:BACK;8000:DOWN;10000:UP;15000:QUIT' \
SDL_VIDEODRIVER=dummy .pio/build/simulator/program 2>&1 | grep -E 'READALOUD|ACT'
```

All of the following, against THREE books — one plain, one hyphenation-heavy
(justified text, long words), one with curly quotes/accents:

- [ ] Page 1's captured text matches the visible page **word for word, in
      order** (screenshot the page, compare by eye — this is the R1 audit).
- [ ] No hyphenated fragments, no U+00AD bytes (`grep -c $'\xc2\xad'` on the
      captured text = 0), words split across lines appear whole, once.
- [ ] No page furniture: chapter header / page number / progress text absent.
- [ ] `DOWN` then `UP` produce gen=2 and gen=3 whose text matches the pages
      actually displayed (R4: capture tracks the *visible* page).
- [ ] BACK to Home logs a `cleared=1` publish.
- [ ] Without the env var: zero `[READALOUD]` lines.
- [ ] `tests/run_all.sh` green; desktop pio build green.

**If neither strategy passes the audit, stop here and report.** Phases 1–4
all speak this text; shipping them on garbled capture is worse than not
shipping. The fallback scope to negotiate at that point is
paragraph-granularity capture (speak paragraphs, highlight paragraphs),
which loses per-word highlight but survives a messy layouter.

### Traps

- **Do not "clean up" text in the simulator.** Stripping and merging is the
  firmware capture's job (it has the layout knowledge); the channel is a dumb
  pipe. A simulator-side cleanup pass would mask capture bugs from the audit
  that exists to catch them.
- **Boot-destination variance**: scripts open `2000:HOME`; believe
  `[ACT] Entering activity:` lines, not screenshots (four runs were burned on
  this once already — CLAUDE.md).
- `rm -rf ./fs_/.crosspoint/` must NOT be needed for any of this; if capture
  behaviour depends on cache state, something is wrong.

---

## Phase 1 — Join them: the phone speaks the real page  *(size M)*

Deliverable: toggle on + book open → the page is spoken. Manual page turns
re-speak the new page; leaving the reader stops speech. Introduces the pure
core (D7) and the serial filter (R7).

### Files

| File | Change |
|---|---|
| `ios/ReadAloudCore.h` / `.cpp` | new — pure core, Phase-1 transitions |
| `ios/CrossPointReadAloud.mm` | replace spike with the real adapter |
| `ios/CMakeLists.txt` | add `ReadAloudCore.cpp` to app target sources |
| `tests/read_aloud_core_test.cpp` | new |
| `tests/run_all.sh` | register it |

**`ios/ReadAloudCore.h`** — modeled on PadCore's header discipline; ships the
full Action vocabulary now, later phases add transitions but never signature
changes:

```cpp
#pragma once
#include <cstdint>
#include <vector>
#include "../src/ReadAloudChannel.h"  // ReadAloudWordRect, ReadAloudPage

// The pure decision logic behind read-aloud. Deliberately AVSpeech-free,
// SDL-free and CLOCK-FREE: time enters only as explicit inputs (pageTimeout),
// counted by the adapter. Tested by tests/read_aloud_core_test.cpp.
class ReadAloudCore {
public:
  struct Action {
    enum Type {
      StartUtterance,   // speak page text from utteranceByteOffset
      StopUtterance,    // stop current speech immediately
      TurnPageForward,  // inject a page-forward button press   (Phase 2)
      SetHighlight,     // highlight rects covering the byte range (Phase 3)
      ClearHighlight,   //                                         (Phase 3)
    };
    Type type;
    uint32_t utteranceByteOffset = 0;
    uint32_t highlightByteOffset = 0;   // SetHighlight only
    uint32_t highlightByteLen = 0;      //
  };
  enum class State { Off, Speaking, AwaitingNextPage };

  std::vector<Action> setEnabled(bool enabled);
  std::vector<Action> pageArrived(const ReadAloudPage &page);
  std::vector<Action> utteranceFinished();   // natural end only
  std::vector<Action> utteranceCanceled();   // stop/interruption: never turns the page
  std::vector<Action> pageTimeout();         // adapter counted too long awaiting a page
  std::vector<Action> willSpeakByte(uint32_t absoluteByteOffset);  // Phase 3
  std::vector<Action> tapAtLogical(int x, int y);                  // Phase 4
  State state() const { return state_; }

private:
  State state_ = State::Off;
  bool enabled_ = false;
  std::vector<ReadAloudWordRect> rects_;
  uint32_t textBytes_ = 0;
  int lastHighlightRect_ = -1;   // resumable scan cursor (Phase 3)
};
```

Phase-1 transition table (implement exactly; everything else returns `{}`):

| State | Input | Actions | Next |
|---|---|---|---|
| any | `setEnabled(false)` | StopUtterance (if Speaking) | Off |
| Off | `setEnabled(true)` | — (waits for a page) | Off |
| any, enabled | `pageArrived(cleared)` | StopUtterance (if Speaking) | Off |
| any, enabled | `pageArrived(text)` | StopUtterance (if Speaking), StartUtterance(0) | Speaking |
| Speaking | `utteranceFinished` | — (Phase 2 changes this) | Off |
| Speaking | `utteranceCanceled` | — | Off |

**Adapter, real form.** Statics: synthesizer + delegate from 0A, a
`ReadAloudCore s_core`, current page `std::string s_pageUtf8`,
`uint32_t s_utteranceBaseByte`, `uint32_t s_serial`. Per frame, in order:

1. Poll the pref; on change, `s_core.setEnabled(...)` and
   `gpio.setReadAloudCaptureWanted(...)`; apply actions.
2. `while (gpio.consumeReadAloudPage(page))` — keep only the LAST page
   drained this frame; store `utf8` in `s_pageUtf8`; feed
   `s_core.pageArrived(page)`; apply actions.
3. Drain the delegate queue; **drop events whose serial != `s_serial`**; feed
   survivors; apply actions.

Applying `StartUtterance(off)`:

```objc
s_serial++;
s_utteranceBaseByte = off;
NSString *text = [[NSString alloc]
    initWithBytes:s_pageUtf8.data() + off
           length:s_pageUtf8.size() - off
         encoding:NSUTF8StringEncoding];  // off is always a word start => valid UTF-8 boundary
AVSpeechUtterance *utt = [AVSpeechUtterance speechUtteranceWithString:text];
utt.voice = [AVSpeechSynthesisVoice voiceWithLanguage:nil];
objc_setAssociatedObject(utt, kReadAloudSerialKey, @(s_serial),
                         OBJC_ASSOCIATION_RETAIN_NONATOMIC);
[s_synth speakUtterance:utt];
SDL_Log("[READALOUD] utterance start serial=%u byteOff=%u", s_serial, off);
```

Applying `StopUtterance`:
`[s_synth stopSpeakingAtBoundary:AVSpeechBoundaryImmediate];` — the async
`didCancel` carries the old serial and is dropped by the filter; that is the
filter's whole reason to exist (R7). Delegate callbacks read the serial back
with `objc_getAssociatedObject` and enqueue `{kind, serial, byteOffset}`.

**Tests** (`c++ -std=c++17 -Iios` + `ios/ReadAloudCore.cpp`, mirroring
pad_core; also add the `run` block to run_all.sh): every Phase-1 table row;
pageArrived while disabled → no actions; canceled does NOT re-speak.
Assert action sequences exactly and in order, as `pad_core_test` does.

### Acceptance

- [ ] `tests/run_all.sh` green (both new tests PASS).
- [ ] Phone/iOS Simulator, toggle on, open a book: page spoken.
- [ ] Manual page-forward mid-speech: speech stops, new page spoken from its
      start, exactly one voice at a time (R7 visible here).
- [ ] BACK to Home mid-speech: speech stops (the cleared publish).
- [ ] Toggle off mid-speech: speech stops on the next frame.

### Traps

- **One consumer per build** (0B trap, restated because this phase adds the
  second consumer): the iOS adapter now drains; the desktop logger must
  remain `#if !CROSSPOINT_SIM_IOS`.
- **Do not implement `willSpeakRange` yet** — its UTF-16 trap belongs to
  Phase 3 where the rects exist to verify against.
- **Only channel-derived byte offsets** ever reach `StartUtterance` (0, or
  later a rect's byteOffset); never compute one.

---

## Phase 2 — Auto page-turn  *(size S)*

Deliverable: speech reaching the end of the page turns it via a real
injected button press — the firmware paginates, persists progress, and
re-publishes exactly as if the owner pressed it — and speech continues.
Retires R8.

### Step 0 — verify the page-forward button FIRST

Working assumption: `HalGPIO::BTN_DOWN` (`src/HalGPIO.h:194`; desktop key map
↓ = "page forward"). Verify both ways before writing code:

1. Firmware: grep the reader activity (path known from 0B) for which
   `BTN_*` its next-page branch tests.
2. Desktop: Gate G0's script already proves `DOWN` produces the next page's
   publish. If it is not BTN_DOWN, use what the grep found and say so in the
   core test's comments.

### Changes

**Core** — new rows (+ tests):

| State | Input | Actions | Next |
|---|---|---|---|
| Speaking | `utteranceFinished` | TurnPageForward | AwaitingNextPage |
| AwaitingNextPage | `pageArrived(text)` | StartUtterance(0) | Speaking |
| AwaitingNextPage | `pageArrived(cleared)` | — | Off |
| AwaitingNextPage | `pageTimeout` | — | Off |

`utteranceCanceled` in Speaking still goes to Off with **no** page turn —
that is the difference between "the phone stopped us" and "we finished the
page", and why didFinish and didCancel stay separate all the way down.

**Adapter**:

- `TurnPageForward` → `gpio.injectButtonDown(<verified button>)`, then a
  2-count frame counter; on reaching 0 in a later `perFrame`,
  `gpio.injectButtonUp(...)`. Two frames is a clean edge for `wasPressed`
  and far below any long-press threshold (the reader's font-family hold is
  hundreds of ms).
- Entering AwaitingNextPage arms a timeout of **5000 perFrame ticks** (the
  main loop runs ~1 kHz via `SDL_Delay(1)`, ≈5 s); expiry feeds
  `s_core.pageTimeout()` and logs `[READALOUD] page timeout — end of book?`.
  Any `pageArrived` disarms it. The counter lives in the adapter because the
  core is clock-free (D7).

**Test rows**: finished→TurnPageForward exactly once; the full loop
(page → finished → turn → page → StartUtterance); canceled → no
TurnPageForward; timeout → Off, and a later pageArrived while enabled starts
speech again (owner turned the page by hand after the book ended); cleared
during AwaitingNextPage → Off.

### Acceptance

- [ ] `tests/run_all.sh` green.
- [ ] A short chapter reads across ≥3 consecutive pages hands-free; the
      visible page follows the speech.
- [ ] **The turn is real**: after listening across a page boundary, kill and
      relaunch the app — it resumes on the page speech reached (firmware
      progress saw the button).
- [ ] Last page: speech ends, `page timeout` logged once, no further turns,
      no stuck state (another book then reads fine).
- [ ] Toggle off mid-read: speech stops AND no page turn fires afterwards.

### Traps

- **The injected button IS the feature** (D3) — never call reader internals
  or pagination APIs directly.
- **Page turns firing on cancel** mean the serial filter or delegate wiring
  is broken; fix that, never add compensating state.
- **Do not shorten the hold below 2 frames** — a down and up inside one frame
  risks the no-level-to-poll problem the deep-sleep edge-latch exists for.

---

## Phase 3 — Highlight the spoken word  *(size L)*

Deliverable: a translucent wash on the word being spoken, both appearances,
tracking word by word — including hyphen-split words on two lines. This
phase carries the feature's two hardest correctness details (R2, R3, R5) and
the presents-rarely measurement (R9).

### 3a. Simulator repo

**`SimulatorOverlay` accessors**: declare `int panelLeftPx();` and
`int panelWidthPx();` in `src/SimulatorOverlay.h` next to `panelBottomPx()`;
add the atomics next to the existing pair (`src/HalDisplay.cpp:417-420`) and
store them at the manual-placement site (lines 704–706):
`panelLeft = (int)(cx - logW * scale / 2.0f)`,
`panelWidth = (int)(logW * scale)`. The desktop letterbox path leaves them 0,
same as the existing pair — only manual placement paints highlights.

**Core**: keep `rects_` from `pageArrived`; new behaviour:

| State | Input | Actions | Next |
|---|---|---|---|
| Speaking | `willSpeakByte(b)` | SetHighlight(rects_[i].byteOffset, .byteLen) for the rect whose range contains `b`; nothing if none contains it or the word is unchanged | Speaking |
| Speaking → any stop/finish/cancel/clear | (append) ClearHighlight | — |

Find the rect by a **resumable scan** from `lastHighlightRect_` (speech only
moves forward within an utterance; rects are in reading order). Reset the
cursor on `pageArrived` and on any `StartUtterance` (Phase 4's backwards
jumps depend on that reset — test row).

**Adapter**:

- Delegate gains `willSpeakRangeOfSpeechString:utterance:` — the R3 trap in
  full:

  ```objc
  - (void)speechSynthesizer:(AVSpeechSynthesizer *)syn
      willSpeakRangeOfSpeechString:(NSRange)range
                        utterance:(AVSpeechUtterance *)utt {
    // range.location is UTF-16 CODE UNITS into utt.speechString. The channel
    // text and every rect offset are UTF-8 BYTES. Convert by measuring the
    // UTF-8 length of the prefix; the adapter adds s_utteranceBaseByte on
    // drain because this utterance may have started mid-page (Phase 4).
    NSUInteger b = [[utt.speechString substringToIndex:range.location]
                      lengthOfBytesUsingEncoding:NSUTF8StringEncoding];
    [self enqueueKind:kEvWillSpeak serial:serialOf(utt) byteOffset:(uint32_t)b];
  }
  ```

- `SetHighlight` / `ClearHighlight` → main-thread-owned highlight state (the
  range + a copy of the page rects) + `SimulatorOverlay::requestPresent()`.
  Event-driven and only on change — word-rate, a few Hz.
- Painting: `paintPad` (the single overlay callback) first calls a new
  `CrossPointReadAloud_paintHighlight(SDL_Renderer*, int outW, int outH)`:
  no-op without an active range; else, for EVERY rect matching the range, map
  with the Contracts formula, inflate by 2 device px, and:

  ```cpp
  SDL_SetRenderDrawBlendMode(r, SDL_BLENDMODE_BLEND);
  if (dark) SDL_SetRenderDrawColor(r, 255, 200, 0, 60);  // over 121212 paper
  else      SDL_SetRenderDrawColor(r, 255, 200, 0, 80);  // over FBFBF9 paper
  SDL_RenderFillRect(r, &hl);
  ```

  `dark` is `g_dark`, already maintained in that file. Painting over the
  panel from the overlay callback is legitimate: it runs after the panel
  texture, logical presentation disabled, device pixels.

**Test rows**: page text
`"\xE2\x80\x9CHello\xE2\x80\x9D caf\xC3\xA9 world"` with rects at true byte
offsets — bytes inside word 0 highlight word 0's range; entering word 1 emits
SetHighlight once, not per byte; inter-word bytes emit nothing; a
hyphen-split word (two rects, same range) — highlight action emitted once for
the range; finish/cancel/stop/disable each emit ClearHighlight; a fresh page
resets the scan cursor.

### 3b. Firmware repo (work package FW-B)

Extend the 0B capture: record each word's rect(s) in the same pass that
builds the text (R2). Coordinates: logical portrait pixels, y down —
**divide by the render scale at capture time** (R5; the iOS core runs
`CROSSPOINT_RENDER_SCALE=2`). A word wrapped across lines records one rect
per fragment sharing the word's byteOffset/byteLen. Pass the vector to
`publishReadAloudPage(...)`.

Headless verification: Gate G0's script now shows `words=N`; N must be
plausible against a screenshot's visible word count, and `bytes=` must be
unchanged from 0B for the same book/page (rects must not perturb text).

### Acceptance

- [ ] `tests/run_all.sh` green.
- [ ] Desktop headless: `words=` plausible, `bytes=` unchanged from 0B.
- [ ] iOS Simulator, light mode: the wash sits ON the spoken word — right
      word, right line, within a couple of px — across two pages including an
      auto turn (clears during the turn, resumes on the new page).
- [ ] Dark mode: same, dimmer wash, inverted panel.
- [ ] A hyphenation-heavy book: a split word lights on BOTH lines.
- [ ] A curly-quote book: no drift after multibyte characters (R3 on-glass).
- [ ] R9 measured: reading feels smooth; if per-word presents visibly cost,
      drop to sentence-granularity highlight and note it here.
- [ ] Desktop pio build green (HalDisplay/SimulatorOverlay were touched —
      desktop is their canary).

### Traps

- **NSRange is UTF-16 code units** — the `substringToIndex` +
  `lengthOfBytesUsingEncoding` conversion is the entire fix. Anything
  treating `range.location` as bytes or code points passes ASCII books and
  drifts at the first curly quote; the multibyte test and the on-glass check
  both exist for exactly this.
- **Screenshots cannot verify the highlight** (D6): BMP capture is
  pre-composite. On-glass eyes or a screen recording only.
- **Highlight at half/double size or offset** = firmware published scaled
  coordinates; fix the division at the capture site, never fudge `S` in the
  simulator.
- **One overlay callback** — `setDrawCallback` holds a single pointer; the
  pad's painter delegates to the highlight painter.

---

## Phase 4 — Start reading from a tapped word  *(size S)*

Deliverable: tapping a word starts (or jumps) reading from it, highlight
included; whitespace/margins do nothing; the pad is untouched.

### Changes (simulator repo only — the channel already carries everything)

**Core**:

| State | Input | Actions | Next |
|---|---|---|---|
| any, enabled, rects present | `tapAtLogical(x,y)` inside rects_[i] (each rect inflated 2 logical px for fat fingers) | StopUtterance (if Speaking), StartUtterance(rects_[i].byteOffset), SetHighlight(that word's range) | Speaking |
| any | `tapAtLogical` hitting nothing | — | unchanged |

**Shim.** Tap detection lives in `padWatch` (`ios/CrossPointIOSShim.cpp`),
which already sees every finger event and never consumes them (invariant 3).
Three fields of candidate state in the file's anonymous namespace:

- `FINGER_DOWN` hitting NO pad slot, inside the presented panel rect
  (`panelLeftPx/panelWidthPx/panelBottomPx/panelHeightPx`) → record
  `{fingerID, x, y}`.
- `FINGER_MOTION` beyond `12.0f * g_ptScale` device px from the down point →
  cancel (a drag must not start speech).
- `FINGER_UP` on a live candidate → logical coords
  (`lx = (fx - panelLeft) / S`, `ly = (fy - panelTop) / S`) →
  `CrossPointReadAloud_tapAtPanel(lx, ly)` → `s_core.tapAtLogical`, apply
  actions. `FINGER_CANCELED` / `WILL_ENTER_BACKGROUND` / `FOCUS_LOST` clear
  the candidate (the same events the pad resets on).
- No duration threshold — down-up without movement is a tap regardless of
  hold. No timers, matching the pad's design.

**Test rows**: tap inside word 2 while Off → Start(word 2's offset) +
SetHighlight(word 2's range); tap while Speaking word 0 → Stop, Start(word 2),
SetHighlight; tap a gap → nothing; tap with no rects (0B-era firmware) →
nothing; a tap 1 logical px outside a rect edge still hits (inflation); tap
an EARLIER word while speaking a later one → correct highlight afterwards
(the scan-cursor reset).

### Acceptance

- [ ] `tests/run_all.sh` green.
- [ ] Phone: tap a word with speech off → reading starts there, highlighted;
      the subsequent auto page-turn still fires (genuinely in Speaking).
- [ ] Tap another word while speaking → jump; no double audio, no spurious
      page turn (R7 again).
- [ ] Margins/whitespace taps → nothing; every pad button behaves exactly as
      before (pad slots are checked first, as today); a drag across the page
      → nothing.
- [ ] `[READALOUD] utterance start … byteOff=` equals the tapped rect's
      byteOffset.

### Traps

- **Do not touch PadCore** — candidate state is three fields in the shim, not
  a gesture bolted into the pad's pure core.
- **Taps only ever start at rect byteOffsets** (word starts by FW-B
  construction) — never "round" a tap to an arbitrary byte.

---

## Phase 5 (recorded, out of scope) — real screen-reader support

Once the channel exists, exposing the page text as a `UIAccessibilityElement`
over the panel view (plus labels on the seven pad buttons) makes VoiceOver
and Speak Screen genuinely work — Apple's screen reading, the owner's
gestures, no speech code of ours in the loop. It does not replace phases 1–4
(no auto page-turn, no word callbacks, no tap-to-start) but it serves
VoiceOver users the phases do not. Do not start it until Phase 4 ships; file
it as its own TODO entry then.

---

## Verification matrix — who can check what

| Environment | Can verify |
|---|---|
| Linux cloud session, this repo only | `tests/run_all.sh` (channel + all core state-machine rows), header-compile checks |
| Desktop with firmware checkout (Mac or Linux) | Everything above, plus Gate G0's full text-quality audit, FW-A/FW-B end-to-end (`words=`, `bytes=`, clear-on-exit, page-turn republish), pio canary |
| Mac with Xcode, iOS Simulator | All audible/visual acceptance: speech, auto turn, highlight placement, taps, both appearances |
| Physical iPhone (TestFlight via `ios/testflight.sh`) | Silent-switch (R6), real downloaded voices, Bluetooth audio, feel/performance (R9) |

## Non-goals and accepted simplifications (v1)

Do not "fix" these inside phases 0–4; each is a deliberate cut:

- No background audio / lock-screen controls — reading stops on backgrounding.
- Audio-session interruptions (calls) are treated as cancel; no auto-resume.
- System default voice regardless of book language (R10); no rate control UI.
- Landscape reading unsupported (the phone harness presents portrait only).
- A sentence split across a page boundary is spoken with the turn's pause in
  the middle.
- A firmware re-render of the same page (e.g. an AA toggle) restarts its
  speech.
- CJK and other unspaced scripts highlight whatever the capture emits as a
  "word" (likely a layout run); correctness of speech is Apple's, of
  segmentation is not attempted.

## Documentation & bookkeeping (part of each phase's PR)

- Phase 0B: add the channel to CLAUDE.md's HAL-surface notes (a short
  paragraph next to the keyboard-channel one) and the new test to its table
  and command list; Phase 1 adds the core test likewise.
- Phase 4 (feature complete): ios/README.md gains the owner-facing behaviour
  table (toggle, tap, what stops reading); close ST-003 in TODO.md; file
  Phase 5 as its own entry if still wanted.
- Each firmware PR names the simulator commit it needs; the firmware
  pin / source-set / `firmware_repo` triple stays in sync per
  CONTEXT-sim-notes.md if TUs were added.
