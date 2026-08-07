# PLAN: Read-aloud TTS on the iOS harness (Apple speech)

**Status: planned, not started.** Tracked as ST-003 in [TODO.md](../TODO.md).
Written 2026-08-07 against `main` @ `ebf2b54`.

The end state: on the phone, with a book open, the app reads the page aloud in
the system voice the owner picked in Settings > Accessibility > Spoken Content
> Voices, turns the page by itself when it reaches the bottom, highlights each
word as it is spoken, and starts reading from any word the owner taps. All of
it lives behind a default-off toggle in Settings > CrossPoint X3.

This plan is written to be executed phase by phase by any implementer,
including a small model, without further design work. Rules of engagement:

- **Do the phases in order.** Each phase is a separate PR (per repo) and must
  pass its full acceptance checklist before the next phase starts.
- **Never skip a Traps section.** Every trap listed here is either a bug this
  repo has already had once, or an API behaviour that was checked.
- **When reality contradicts a step** (a symbol is missing, a grep finds
  nothing, a log line never appears), stop and re-read the phase's Traps and
  the Contracts section rather than improvising a workaround.
- **The desktop PlatformIO build is the canary.** After every simulator-repo
  change: the desktop build must stay green and `tests/run_all.sh` must pass.

Two repos are involved:

| Repo | Role in this feature |
|---|---|
| `crosspoint-simulator` (this repo) | The channel (HAL surface), the pure state machine, the AVSpeech adapter, the highlight overlay, the tap hit-test |
| `natebunnyfield/crosspoint-reader`, branch `x3-main` (the firmware fork) | Capturing page text + word rects during page render, publishing them, clearing on reader exit, inline no-ops so the device build still links |

Simulator-side changes land first in every phase pair: the firmware compiles
against this repo's HAL surface, so the surface must exist before the firmware
calls it. The device build never breaks because every firmware-facing method
gets an inline no-op in the firmware's own `lib/hal/HalGPIO.h` in the same
firmware PR that starts calling it (the exact precedent: `setTextEntryActive`
/ `consumeTypedText`, added there 2026-08-06).

---

## Invariants this feature must not break

Restated from CLAUDE.md because every one of them is load-bearing here:

1. **The HAL public surface mirrors the firmware's.** Firmware-facing methods
   added to `src/HalGPIO.h` must be added, same signature, as inline no-ops in
   the firmware's `lib/hal/HalGPIO.h`. Simulator-only methods (the harness's
   side of the channel) must NOT gain firmware counterparts.
2. **SDL render calls happen only on the main thread**, inside the
   `presentIfNeeded()` path. The highlight paints from the existing
   `SimulatorOverlay` draw callback and nowhere else.
3. **`HalGPIO::update()` owns the SDL event pump.** The tap detector observes
   events from the already-installed `padWatch` event watch in
   `ios/CrossPointIOSShim.cpp`; do not add another pump or poll.
4. **PadCore stays pure passthrough.** Do not add gestures, timers, or word
   logic to `ios/PadCore.*`. New decision logic goes in a new pure class,
   `ios/ReadAloudCore.*`, which is likewise **clock-free** — it never reads a
   clock; anything time-shaped arrives as an input from the adapter.
5. **No new cross-cutting compile definitions.** This feature adds none. If
   one ever becomes necessary it goes on `crosspoint_core PUBLIC` in
   [ios/CMakeLists.txt](../ios/CMakeLists.txt), never on the app target
   (split-brain guard, see CLAUDE.md "One device macro, one definition").
6. **The e-ink presentation model presents rarely.** Every repaint the
   feature needs goes through `SimulatorOverlay::requestPresent()`,
   event-driven, never per-frame.
7. **Firmware settings vs phone settings.** The read-aloud toggle is a
   property of the phone (device hardware has no speaker), so it lives in the
   iOS Settings.bundle like Keep Screen Awake, NOT in the firmware's
   `settings.json`.

---

## Architecture

```
  firmware (fork x3-main)                 simulator repo
  ─────────────────────────              ──────────────────────────────────────
  EpubReader page render ──captures──▶  HalGPIO::publishReadAloudPage()
    (only when                             │  (ReadAloudChannel, mutex'd)
     readAloudCaptureWanted())             ▼
  reader exit ──publishes nullptr──▶   consumeReadAloudPage()   [simulator-only]
                                           │ drained on main thread, once per
                                           │ frame, by the iOS adapter
                                           ▼
                          ios/CrossPointReadAloud.mm  (AVSpeech adapter, ObjC++)
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
          TurnPageForward   → gpio.injectButtonDown/Up(BTN_DOWN)
          highlight state   → painted by the SimulatorOverlay callback,
                              SimulatorOverlay::requestPresent() on change
```

Desktop builds compile the channel (it lives in `src/`) but have no adapter;
an env-gated logger in `simulator_main.cpp` makes the firmware half verifiable
headlessly on Linux with no Mac involved (Phase 1).

---

## Contracts (fixed in Phase 1, stable through Phase 4)

### The channel surface on `HalGPIO`

Firmware-facing pair — must exist field-for-field and signature-identical in
BOTH repos (`src/HalGPIO.h` here, real implementation; `lib/hal/HalGPIO.h` in
the firmware, inline no-ops):

```cpp
// POD, identical in both repos. Coordinates are LOGICAL PORTRAIT panel pixels
// (X3: 528 wide, 792 tall; x right, y down), independent of render scale —
// the firmware divides by its own render scale at capture time.
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

The full four-argument signature is fixed from Phase 1 even though rects only
matter in Phase 3 — the firmware passes `nullptr, 0` until then, so the
firmware-facing surface is touched exactly once.

`publishReadAloudPage(nullptr, 0, nullptr, 0)` means **"there is no page"**:
the reader exited (or the book closed). Consumers must stop speech and clear
the highlight.

Simulator-only half (no firmware counterpart, like `injectButtonDown`):

```cpp
void setReadAloudCaptureWanted(bool wanted);
bool consumeReadAloudPage(ReadAloudPage &out);  // true once per publish
```

### `src/ReadAloudChannel.h` (new, pure, SDL-free)

Header-only state holder owned by `HalGPIO`, testable with a bare `c++ -Isrc`
compile exactly like `GrayscalePreview.h`:

```cpp
#pragma once
#include <cstdint>
#include <mutex>
#include <string>
#include <vector>

struct ReadAloudWordRect { /* as above */ };

struct ReadAloudPage {
  std::string utf8;                       // empty when cleared == true
  std::vector<ReadAloudWordRect> rects;   // may be empty (Phase 1 firmware)
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
`utf8 == nullptr`, and sets `hasNew_`. `consume` moves the page out and clears
`hasNew_`. Publisher is the firmware task; consumer is the main thread — the
mutex is the whole thread story.

### Coordinate mapping (Phase 3)

Word rects are logical portrait panel pixels. The presented panel rect in
device pixels comes from `SimulatorOverlay` (two accessors added in Phase 3
next to the existing `panelBottomPx`/`panelHeightPx`):

```cpp
// Main thread, inside the overlay draw callback:
const float S  = SimulatorOverlay::panelWidthPx()
               / static_cast<float>(HalDisplay::DISPLAY_HEIGHT); // portrait width == landscape fb height (X3: 528)
const float x0 = SimulatorOverlay::panelLeftPx();
const float y0 = SimulatorOverlay::panelBottomPx() - SimulatorOverlay::panelHeightPx();
SDL_FRect hl = { x0 + r.x * S, y0 + r.y * S, r.w * S, r.h * S };
```

Landscape reading orientation is out of scope for all four phases (the phone
harness presents portrait only).

### Log discipline

Every log line this feature emits starts with `[READALOUD] `. That prefix is
what every acceptance step greps for.

---

## Phase 0 — Spike: prove Apple speech works inside this app

No firmware involvement, no channel. Deliverable: with a new Settings toggle
on, the app speaks one canned sentence at launch through
`AVSpeechSynthesizer`. This proves the audio session, the synthesizer, the
delegate callbacks, and the main-thread plumbing all work inside an SDL3/UIKit
app before any real machinery is built.

### Files

| File | Change |
|---|---|
| `ios/CrossPointReadAloud.h` | new — C-linkage API |
| `ios/CrossPointReadAloud.mm` | new — AVSpeech adapter (spike form) |
| `ios/CrossPointPrefs.h` / `.mm` | add `CrossPointPrefs_readAloudEnabled()` |
| `ios/Settings.bundle/Root.plist` | add default-off toggle `read_aloud_enabled`, title "Read Aloud (experimental)" |
| `ios/CrossPointIOSShim.cpp` | call `CrossPointReadAloud_begin()` from `CrossPointHarness_begin()`, `CrossPointReadAloud_perFrame()` from `CrossPointHarness_perFrame()` |
| `ios/CMakeLists.txt` | add `CrossPointReadAloud.mm` to the app target's source list (next to `CrossPointAppearance.mm`) and link `AVFoundation` where the other frameworks are linked (grep the file for `NetworkExtension` and mirror that pattern) |

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

2. `ios/CrossPointReadAloud.mm` spike body:
   - statics: `AVSpeechSynthesizer *s_synth`, a delegate object, a
     `std::mutex` + `std::vector<int>` event queue, `bool s_spikeDone`.
   - `CrossPointReadAloud_begin()`: create the synthesizer and delegate once
     (guard with a static bool, same idiom as `s_watchesInstalled` in
     `CrossPointHarness_begin`).
   - `CrossPointReadAloud_perFrame()`: if `!s_spikeDone` and
     `CrossPointPrefs_readAloudEnabled()`, set `s_spikeDone = true`, then:

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
   - Delegate implements `didFinishSpeechUtterance` and
     `didCancelSpeechUtterance`; both just push an int into the locked queue.
     `perFrame` drains the queue and logs
     `[READALOUD] spike utterance finished` / `canceled`. This exercises the
     exact delegate→queue→main-thread path every later phase relies on.

3. Prefs accessor: copy the `CrossPointPrefs_wantsScreenAwake` implementation
   shape in `CrossPointPrefs.mm` (registerDefaults + `boolForKey:`), key
   `read_aloud_enabled`, default `NO`. Root.plist gets a
   `PSToggleSwitchSpecifier` mirroring an existing toggle entry.

### Acceptance

- [ ] `cmake` configure of the iOS project succeeds (no identity-guard
      failure — this phase adds no defines).
- [ ] iOS Simulator (any iPhone model), toggle ON in Settings > CrossPoint X3:
      launch speaks the sentence; log shows `spike utterance started` then
      `finished`.
- [ ] Toggle OFF: silent launch, neither log line, and the audio session is
      never activated (no `setActive` call — it sits behind the pref check).
- [ ] Desktop build unaffected: `tests/run_all.sh` passes (no desktop source
      was touched).

### Traps

- **Everything main thread.** `begin` and `perFrame` are already called on the
  main thread by the harness. Never call AVSpeech from a delegate callback's
  own thread or from the firmware task.
- **Delegate callbacks arrive on a private queue**, not the main thread. They
  must only enqueue; all reactions happen in `perFrame`. This is the pattern
  Phases 1–4 scale up, so get it right here.
- **Silent switch**: `AVAudioSessionCategoryPlayback` is what makes speech
  audible with the ringer switch muted. Without it the spike "fails" on a
  muted phone while working in the Simulator — do not skip the session setup.
- **`.mm` files cannot compile off-Mac.** Nothing in this phase is
  host-testable; that is why the phase is kept this small.

---

## Phase 1 — Speak the real page (user phase "spike that it is possible")

Deliverable: with the toggle on and a book open, the phone speaks the actual
page text. Manual page turns re-speak the new page. Leaving the reader stops
speech. On desktop Linux, an env var proves the firmware capture end-to-end
with no Mac.

### 1a. Simulator repo

| File | Change |
|---|---|
| `src/ReadAloudChannel.h` | new — as specified in Contracts |
| `src/HalGPIO.h` | include it; add the four methods (documented like the text-entry block at lines 95–131, stating which half is firmware-facing); add `ReadAloudChannel readAloud;` private member |
| `src/HalGPIO.cpp` | four one-line delegating bodies |
| `src/simulator_main.cpp` | env-gated headless drain (below) |
| `ios/ReadAloudCore.h` / `.cpp` | new — pure core, initial state machine |
| `ios/CrossPointReadAloud.mm` | replace spike with the real adapter |
| `ios/CMakeLists.txt` | add `ReadAloudCore.cpp` to the app target sources |
| `tests/read_aloud_channel_test.cpp` | new |
| `tests/read_aloud_core_test.cpp` | new |
| `tests/run_all.sh` | register both (below) |

**Headless drain** in `simulator_main.cpp` — inside the main loop, after
`loop()`, guarded `#if !CROSSPOINT_SIM_IOS`:

```cpp
// Headless proof of the read-aloud capture (see .claude/PLAN-tts-read-aloud.md):
// CROSSPOINT_SIM_READALOUD_LOG=1 asks the firmware to capture page text and
// logs every publish. Desktop has no speech consumer; iOS must not compile
// this, its harness is the consumer and this drain would steal its pages.
static const bool readAloudLog = [] {
  const char *v = SDL_getenv("CROSSPOINT_SIM_READALOUD_LOG");
  if (v && *v == '1') gpio.setReadAloudCaptureWanted(true);
  return v && *v == '1';
}();
if (readAloudLog) {
  ReadAloudPage page;
  while (gpio.consumeReadAloudPage(page)) {
    SDL_Log("[READALOUD] page gen=%u cleared=%d bytes=%zu words=%zu | %.60s",
            page.generation, page.cleared ? 1 : 0, page.utf8.size(),
            page.rects.size(), page.utf8.c_str());
  }
}
```

**`ios/ReadAloudCore.h`** — pure, clock-free, SDL-free, modeled on PadCore's
header discipline. Phase 1 ships it with the full Action vocabulary but only
the Phase-1 transitions implemented; later phases add transitions plus tests,
never signature changes:

```cpp
#pragma once
#include <cstdint>
#include <vector>
#include "../src/ReadAloudChannel.h"  // ReadAloudWordRect

// The pure decision logic behind read-aloud. Deliberately AVSpeech-free,
// SDL-free and CLOCK-FREE: time only enters as explicit inputs (pageTimeout),
// counted by the adapter. Tested by tests/read_aloud_core_test.cpp.
class ReadAloudCore {
public:
  struct Action {
    enum Type {
      StartUtterance,   // speak page text from utteranceByteOffset
      StopUtterance,    // stop current speech immediately
      TurnPageForward,  // inject a page-forward button press   (Phase 2)
      SetHighlight,     // highlight rects[highlightIndex]      (Phase 3)
      ClearHighlight,   //                                      (Phase 3)
    };
    Type type;
    uint32_t utteranceByteOffset = 0;
    int highlightIndex = -1;
  };
  enum class State { Off, Speaking, AwaitingNextPage };

  std::vector<Action> setEnabled(bool enabled);
  std::vector<Action> pageArrived(const ReadAloudPage &page);
  std::vector<Action> utteranceFinished();   // natural end (Phase 2 grows this)
  std::vector<Action> utteranceCanceled();   // stop / interruption: never turns the page
  std::vector<Action> pageTimeout();         // adapter counted too long in AwaitingNextPage
  std::vector<Action> willSpeakByte(uint32_t absoluteByteOffset);  // Phase 3
  std::vector<Action> tapAtLogical(int x, int y);                  // Phase 4
  State state() const { return state_; }

private:
  State state_ = State::Off;
  bool enabled_ = false;
  std::vector<ReadAloudWordRect> rects_;  // current page (Phase 3/4)
  uint32_t textBytes_ = 0;
  int highlightIndex_ = -1;
};
```

Phase-1 transition table (implement exactly; everything else returns `{}`):

| State | Input | Actions | Next state |
|---|---|---|---|
| any | `setEnabled(false)` | StopUtterance (if Speaking) | Off |
| Off | `setEnabled(true)` | — (waits for a page) | Off |
| any, enabled | `pageArrived(cleared)` | StopUtterance (if Speaking) | Off |
| any, enabled | `pageArrived(text)` | StopUtterance (if Speaking), StartUtterance(0) | Speaking |
| Speaking | `utteranceFinished` | — (Phase 2 changes this) | Off |
| Speaking | `utteranceCanceled` | — | Off |

**Adapter (`CrossPointReadAloud.mm`), real form.** Statics: the synthesizer +
delegate from Phase 0, a `ReadAloudCore s_core`, the current page's
`std::string s_pageUtf8`, `uint32_t s_utteranceBaseByte`, and `uint32_t
s_serial` (utterance generation). Per frame, in this order:

1. Poll the pref; on change call `s_core.setEnabled(...)` and
   `gpio.setReadAloudCaptureWanted(...)`, apply actions.
2. `ReadAloudPage page; while (gpio.consumeReadAloudPage(page))` — keep only
   the LAST page drained this frame, store its `utf8` in `s_pageUtf8`, feed
   `s_core.pageArrived(page)`, apply actions.
3. Drain the delegate event queue; drop any event whose serial !=
   `s_serial`; feed survivors to the core; apply actions.

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

Applying `StopUtterance`: `[s_synth stopSpeakingAtBoundary:
AVSpeechBoundaryImmediate];` — the resulting `didCancel` event carries the old
serial and is dropped by the filter, which is exactly why the filter exists.
Delegate callbacks read the serial back with `objc_getAssociatedObject` on the
utterance they were handed and enqueue `{kind, serial, byteOffset}`.

**Tests.** `tests/read_aloud_channel_test.cpp` (compile: `c++ -std=c++20
-Isrc`, no other TU — the header is self-contained): consume-empty returns
false; publish→consume returns the text and rects, second consume false;
publish twice → consume sees the second, generation strictly increasing;
`publish(nullptr,0,nullptr,0)` → `cleared == true`, empty text; wanted flag
round-trips. `tests/read_aloud_core_test.cpp` (compile: `c++ -std=c++17 -Iios`
+ `ios/ReadAloudCore.cpp`, mirroring pad_core): every row of the Phase-1
transition table, plus: pageArrived while disabled produces no actions;
canceled does NOT re-speak or page-turn. Assert action sequences exactly, in
order, like `pad_core_test` does.

`tests/run_all.sh`, after the `task_registry` block:

```bash
run read_aloud_channel \
  c++ -std=c++20 -Isrc -o "$OUT/read_aloud_channel" tests/read_aloud_channel_test.cpp

run read_aloud_core \
  c++ -std=c++17 -Iios -o "$OUT/read_aloud_core" tests/read_aloud_core_test.cpp ios/ReadAloudCore.cpp
```

### 1b. Firmware repo (work package FW-A)

On branch off `x3-main`, with the simulator symlinked
(`simulator=symlink://../crosspoint-simulator` per CLAUDE.md):

1. **HAL no-ops**: in `lib/hal/HalGPIO.h`, next to the existing
   `setTextEntryActive` / `consumeTypedText` inline no-ops, add the
   `ReadAloudWordRect` struct and the two firmware-facing inline no-ops from
   the Contracts section, byte-identical field layout.
2. **Find the page-render completion site**: `grep -rn "EpubReaderActivity"
   src/ | head`, then inside that activity find where a page finishes
   rendering (the code path that runs once per displayed page — look for the
   render call the page-turn handler invokes). The capture hook wraps the
   text-layout pass that this render performs.
3. **Find the text source**: the renderer lays out parsed EPUB text
   word-by-word to draw it (`grep -rn "drawText\|drawString\|drawWord"
   src/renderer src/ | head-20` — adjust to what exists). Phase 1 needs only
   the concatenated plain text of the page in reading order, single spaces
   between words, `\n` between paragraphs.
4. **Hook**: when `gpio.readAloudCaptureWanted()` is true during a page
   render, accumulate that text into a `std::string`; after the render
   completes call `gpio.publishReadAloudPage(text.c_str(), text.size(),
   nullptr, 0)`. When it is false, do nothing — zero cost on device, where
   `readAloudCaptureWanted()` is inline `false` and the whole branch folds
   away.
5. **Clear on exit**: in the reader activity's exit path (`onExit` or
   equivalent — find where it tears down), call
   `gpio.publishReadAloudPage(nullptr, 0, nullptr, 0)`.
6. If any new translation unit was added (prefer not to — hook in existing
   TUs), regenerate the iOS source set per CLAUDE.md
   (`pio run -e simulator -t compiledb` + `tools/gen_cmake_sources.py`).

### Acceptance

Simulator repo alone (runnable in a Linux cloud session):
- [ ] `tests/run_all.sh` passes with the two new tests listed as PASS.

With the firmware checkout (desktop, headless — the firmware-side proof):
- [ ] ```bash
      CROSSPOINT_SIM_READALOUD_LOG=1 \
      CROSSPOINT_SIM_INPUT_SCRIPT='2000:HOME;3000:BACK;15000:QUIT' \
      SDL_VIDEODRIVER=dummy .pio/build/simulator/program 2>&1 | grep READALOUD
      ```
      (`HOME` normalises the boot state per CLAUDE.md; `BACK` from Home opens
      the most recent book.) Output shows at least one
      `[READALOUD] page gen=1 cleared=0 bytes=<nonzero> ...` whose text
      preview matches the book's first page.
- [ ] Without the env var: zero `[READALOUD]` lines (capture off by default).
- [ ] `rm -rf ./fs_/.crosspoint/` was NOT needed — the feature must not
      depend on cache state; if it appears to, something is wrong.

On the phone / iOS Simulator:
- [ ] Toggle on, open a book: the page is spoken.
- [ ] Press page-forward manually mid-speech: speech stops, new page is
      spoken from its start.
- [ ] BACK to Home mid-speech: speech stops (the cleared publish).
- [ ] Toggle off mid-speech (background the app, flip in Settings, return):
      speech stops on the next frame.

### Traps

- **The drain steals pages.** Exactly one consumer may drain
  `consumeReadAloudPage` per build: the env-gated logger on desktop, the
  adapter on iOS. That is why the logger sits in `#if !CROSSPOINT_SIM_IOS`.
- **NSRange is not needed yet** — do not implement `willSpeakRange` handling
  in this phase; its UTF-16 trap is Phase 3's headline and doing it early
  without the rects to check against invites an unverifiable half-feature.
- **The serial filter is not optional.** `stopSpeaking` produces an async
  `didCancel`; without the filter it arrives after the next `StartUtterance`
  and kills the new page's speech. The core must never receive stale events.
- **`byteOffset` slicing assumes word-start offsets.** Only ever pass offsets
  that came from the channel (0, or a rect's `byteOffset`); never compute
  arbitrary ones.
- **Boot-destination variance** (CLAUDE.md): scripts must open `2000:HOME`.
  Believe `[ACT] Entering activity:` lines, not the screenshot.

---

## Phase 2 — Auto page-turn (user phase "make it turn the page")

Deliverable: when speech reaches the end of the page, the firmware turns the
page (via a real injected button press, so the firmware paginates, persists
progress, and re-publishes exactly as if the owner pressed the button) and
speech continues on the new page. Reading stops cleanly at the end of the
book, on cancel, and on reader exit.

### Step 0 — verify the page-forward button (do this FIRST)

The working assumption is `HalGPIO::BTN_DOWN` (`src/HalGPIO.h:194`; the
desktop key map's ↓ = "page forward" per CONTEXT-sim-notes.md). Verify both
ways before writing code:

1. Firmware: `grep -rn "BTN_DOWN\|BTN_UP\|BTN_RIGHT" src/activities/*Reader*`
   (adjust path from what Phase 1 found) — confirm which index the reader's
   next-page branch tests.
2. Desktop: input script `2000:HOME;3000:BACK;8000:DOWN;15000:QUIT` with
   `CROSSPOINT_SIM_READALOUD_LOG=1` — the DOWN must produce a second
   `[READALOUD] page gen=2` line.

If it is not BTN_DOWN, use what the grep found and note it in the core test.

### Changes

**Core** (`ios/ReadAloudCore.cpp` + test rows):

| State | Input | Actions | Next state |
|---|---|---|---|
| Speaking | `utteranceFinished` | TurnPageForward | AwaitingNextPage |
| AwaitingNextPage | `pageArrived(text)` | StartUtterance(0) | Speaking |
| AwaitingNextPage | `pageArrived(cleared)` | — | Off |
| AwaitingNextPage | `pageTimeout` | — | Off |
| AwaitingNextPage | `utteranceCanceled` | — (stale, cannot happen post-filter; keep as no-op) | AwaitingNextPage |

`utteranceCanceled` in Speaking still goes to Off with no page turn — that is
the difference between "the phone stopped us" and "we finished the page", and
the reason the delegate distinguishes didFinish from didCancel.

**Adapter**:

- `TurnPageForward` → `gpio.injectButtonDown(HalGPIO::BTN_DOWN);` then start a
  2-count frame counter; when it hits 0 on a later `perFrame`, call
  `gpio.injectButtonUp(HalGPIO::BTN_DOWN);`. Two frames ≈ a few ms real hold:
  a clean edge for `wasPressed`, far below any long-press threshold (the
  reader's font-family hold is hundreds of ms). `injectButton*` is the same
  API the on-screen pad uses, so edge AND level reads work (see the header
  comment at `src/HalGPIO.h:71-93`).
- Entering AwaitingNextPage arms a timeout counter of **5000 perFrame ticks**
  (the main loop runs ~1 kHz via `SDL_Delay(1)`, so ≈5 s); on expiry, feed
  `s_core.pageTimeout()` and log `[READALOUD] page timeout — end of book?`.
  Any `pageArrived` disarms it. The counter lives in the adapter because the
  core is clock-free.

**Tests** (`read_aloud_core_test.cpp` additions): finished→TurnPageForward
exactly once; the full happy loop (page → finished → turn → page →
StartUtterance); canceled produces no TurnPageForward; timeout lands in Off
and a later pageArrived while enabled starts speech again (owner turned the
page by hand after the book ended); cleared during AwaitingNextPage → Off.

### Acceptance

- [ ] `tests/run_all.sh` passes.
- [ ] Phone/iOS Simulator: a short book chapter reads across at least three
      consecutive pages hands-free; the visible page follows the speech.
- [ ] The page turn is real: after listening across a page boundary, kill and
      relaunch the app — it resumes on the page speech had reached (firmware
      progress tracking saw the button).
- [ ] Last page of the book: speech ends, `page timeout` logged once, no
      further page turns, no stuck state (opening another book starts fresh).
- [ ] Toggle off mid-read: speech stops AND no page turn fires afterwards
      (the canceled path).
- [ ] Desktop `tests/run_all.sh` and desktop pio build stay green.

### Traps

- **Never call `rebootAsPowerWake()`-style shortcuts or firmware pagination
  APIs directly** — the injected button IS the feature: progress persistence,
  chapter boundaries, and end-of-book behaviour all come from the firmware's
  own handler.
- **didFinish fires for finished utterances only**; stopSpeaking produces
  didCancel. If page turns fire on cancel, the serial filter or the delegate
  wiring is wrong — fix that, do not add state to compensate.
- **Do not shorten the injected hold below 2 frames.** A down and up inside
  one frame risks the same no-level-to-poll problem the deep-sleep edge-latch
  exists for (`test_sleep_wake.sh` history).

---

## Phase 3 — Highlight the word being spoken (user phase "add highlighting")

Deliverable: the word currently being spoken carries a translucent highlight
on the panel, both appearances, tracking speech word by word. This phase has
the feature's two hardest correctness details: UTF-16→UTF-8 offset mapping
and rect coordinate mapping.

### 3a. Simulator repo

**`SimulatorOverlay` accessors.** In `src/SimulatorOverlay.h` declare
`int panelLeftPx();` and `int panelWidthPx();` next to `panelBottomPx()`. In
`src/HalDisplay.cpp`, next to the existing atomics at lines 417–420, add
`panelLeft`/`panelWidth` atomics, and store them at the manual-placement site
(lines 704–706): `panelLeft = (int)(cx - logW * scale / 2.0f)`,
`panelWidth = (int)(logW * scale)`. Desktop letterbox path never sets them
(stays 0), same as the existing pair — they are only meaningful under manual
placement, which is the only place the highlight paints.

**Core**: store `rects_` from `pageArrived`. New transitions:

| State | Input | Actions | Next |
|---|---|---|---|
| Speaking | `willSpeakByte(b)` | SetHighlight(i) where rects[i].byteOffset ≤ b < byteOffset+byteLen; no action if no rect matches or i unchanged | Speaking |
| Speaking → anything that stops or finishes speech | (append) ClearHighlight | — |

`rects_` is sorted by `byteOffset` (the firmware captures in reading order);
find by linear scan from the last index — pages have a few hundred words,
and the scan is resumable because speech only moves forward within an
utterance.

**Adapter**:

- Delegate gains `willSpeakRangeOfSpeechString:utterance:` — the UTF-16 trap:

  ```objc
  - (void)speechSynthesizer:(AVSpeechSynthesizer *)syn
      willSpeakRangeOfSpeechString:(NSRange)range
                        utterance:(AVSpeechUtterance *)utt {
    // range.location is UTF-16 CODE UNITS into utt.speechString. The channel
    // text and every rect offset are UTF-8 BYTES. Convert by measuring the
    // UTF-8 length of the prefix, then rebase onto the page: this utterance
    // may have started mid-page (Phase 4).
    NSUInteger b = [[utt.speechString substringToIndex:range.location]
                      lengthOfBytesUsingEncoding:NSUTF8StringEncoding];
    [self enqueueKind:kEvWillSpeak
               serial:serialOf(utt)
           byteOffset:(uint32_t)b];  // adapter adds s_utteranceBaseByte on drain
  }
  ```

  On drain, the adapter feeds
  `s_core.willSpeakByte(s_utteranceBaseByte + ev.byteOffset)`.
- `SetHighlight(i)` / `ClearHighlight` → store `int s_highlightIndex` (plus a
  copy of the page rects, main-thread-owned) and call
  `SimulatorOverlay::requestPresent()`. Event-driven, word-rate — this is the
  `requestPresent` contract working as designed, not a per-frame present.
- Painting: `paintPad` in `CrossPointIOSShim.cpp` is the single overlay
  callback; have it first call a new
  `CrossPointReadAloud_paintHighlight(SDL_Renderer*, int outW, int outH)`
  which no-ops when `s_highlightIndex < 0`, else maps the rect with the
  Contracts formula, inflates it by 2 device px, and fills it:

  ```cpp
  SDL_SetRenderDrawBlendMode(r, SDL_BLENDMODE_BLEND);
  // light: warm marker over FBFBF9 paper; dark: dimmer over 121212.
  if (dark) SDL_SetRenderDrawColor(r, 255, 200, 0, 60);
  else      SDL_SetRenderDrawColor(r, 255, 200, 0, 80);
  SDL_RenderFillRect(r, &hl);
  ```

  The dark flag is `g_dark`, already maintained in that file. Painting OVER
  the panel from the overlay callback is fine — the callback runs after the
  panel texture is rendered, with logical presentation disabled, in device
  pixels (see `src/SimulatorOverlay.h` header comment).

**Tests** (`read_aloud_core_test.cpp` additions): build a page whose text
contains multibyte content, e.g. `"\xE2\x80\x9CHello\xE2\x80\x9D caf\xC3\xA9 world"`
with three rects at the correct byte offsets, and assert: bytes inside word 0
highlight index 0; advancing into word 1 emits SetHighlight(1) exactly once
(no repeat for every byte); a byte in the inter-word gap emits nothing;
finish/cancel/stop each emit ClearHighlight; a fresh page resets the resumable
scan (byte 0 of the new page highlights index 0 again).

### 3b. Firmware repo (work package FW-B)

Extend the FW-A capture: at the point each word is placed (the same layout
pass that produced the text), also record its rect. Coordinates: the
renderer's logical portrait pixels, y down — **divide by the render scale at
capture time** if the draw site works in scaled pixels (on iOS the core runs
`CROSSPOINT_RENDER_SCALE=2`; the contract is scale-independent logical px).
`byteOffset`/`byteLen` must index the exact UTF-8 string being published —
build both in the same pass so they cannot drift. Pass the vector to
`publishReadAloudPage(text.c_str(), text.size(), rects.data(), rects.size())`.

Verification of the firmware half, headless on desktop: the Phase-1 log line
already prints `words=N`; extend the acceptance script and confirm `words=`
matches the visible word count of page 1 (count them on a screenshot).

### Acceptance

- [ ] `tests/run_all.sh` passes (new core rows green).
- [ ] Desktop headless: `words=` nonzero and plausible; `bytes=` unchanged
      from Phase 1 for the same book/page (rects must not perturb text).
- [ ] iOS Simulator, light mode: highlight sits ON the spoken word — right
      word, right line, within a couple of px — across at least two full
      pages including an auto page-turn (highlight clears during the turn,
      resumes on the new page's first word).
- [ ] Dark mode: same, with the dimmer wash, panel inverted.
- [ ] A book with curly quotes/accents: highlight does not drift after
      multibyte characters (this is the UTF-16/UTF-8 check on-glass).
- [ ] Desktop pio build green (SimulatorOverlay/HalDisplay were touched —
      desktop is the canary for those files).

### Traps

- **NSRange is UTF-16 code units.** The `substringToIndex` +
  `lengthOfBytesUsingEncoding` conversion is the entire fix; anything that
  treats `range.location` as bytes or as code points will pass ASCII books
  and drift on the first curly quote. The multibyte core test plus the
  on-glass check both exist to catch exactly this.
- **Screenshots cannot verify the highlight.** `CROSSPOINT_SIM_SCREENSHOTS`
  captures renderer output pre-composite (HalDisplay.cpp says so) and the
  overlay paints after; on-glass eyes or a screen recording are the only
  verification. Do not burn cycles wondering why the BMP shows no highlight.
- **If the highlight lands at half/double size or offset**, the firmware
  published scaled coordinates — fix the division at the capture site (FW-B),
  never by fudging `S` in the simulator, which would break the next device
  profile.
- **Do not add another overlay callback**; `setDrawCallback` holds one
  pointer. The pad's painter delegates to the highlight painter.

---

## Phase 4 — Start reading from a tapped word (user phase "start at a given selected word")

Deliverable: with the toggle on and a book open, tapping a word on the page
starts (or jumps) reading from that word, highlight included. Tapping
whitespace/margins does nothing. The pad keeps working unchanged.

### Changes (simulator repo only — the channel already carries everything)

**Core**:

| State | Input | Actions | Next |
|---|---|---|---|
| any, enabled, rects present | `tapAtLogical(x,y)` hitting rects[i] | StopUtterance (if Speaking), StartUtterance(rects[i].byteOffset), SetHighlight(i) | Speaking |
| any | `tapAtLogical` hitting nothing | — | unchanged |

Hit-test: point-in-rect over `rects_`, first match wins; inflate each rect by
2 logical px on all sides during the test (fat-finger margin; rects are
glyph-tight).

**Adapter / shim.** Tap detection lives in `padWatch`
(`ios/CrossPointIOSShim.cpp`), which already sees every finger event and
never consumes them (invariant 3):

- `SDL_EVENT_FINGER_DOWN` that hit-tests to NO pad slot and lands inside the
  presented panel rect (`panelLeftPx/panelWidthPx/panelBottomPx/panelHeightPx`)
  records `{fingerID, x, y}` as a tap candidate.
- `SDL_EVENT_FINGER_MOTION` moving more than `12.0f * g_ptScale` device px
  from the down point cancels the candidate (it is a swipe/scroll, and X3
  firmware ignores panel swipes anyway — but a drag must not start speech).
- `SDL_EVENT_FINGER_UP` on a live candidate converts to logical panel coords
  — `lx = (fx - panelLeft) / S`, `ly = (fy - panelTop) / S` with the Phase-3
  `S` — and calls `CrossPointReadAloud_tapAtPanel(lx, ly)`, which feeds
  `s_core.tapAtLogical` and applies actions. `FINGER_CANCELED`,
  `WILL_ENTER_BACKGROUND`, `FOCUS_LOST` clear the candidate (same events the
  pad resets on).
- No duration threshold: down-up without movement is a tap regardless of
  hold. No timers, matching the pad's own design.

**Tests** (`read_aloud_core_test.cpp` additions): tap inside word 2 while Off
→ Start(rects[2].byteOffset) + SetHighlight(2); tap while Speaking word 0 →
Stop, Start(word 2), SetHighlight(2); tap in a gap → no actions; tap with no
rects (Phase-1-era firmware) → no actions; the 2-px inflation catches a tap 1
logical px outside a rect edge.

### Acceptance

- [ ] `tests/run_all.sh` passes.
- [ ] Phone: tap a word mid-page with speech off → reading starts at that
      word, highlight on it; subsequent auto page-turn still works (state
      machine is genuinely in Speaking).
- [ ] Tap a different word while speaking → jump, no double audio, no
      spurious page turn (serial filter again).
- [ ] Tap margins/whitespace → nothing; tap every pad button → pad behaves
      exactly as before (candidate logic must not eat pad presses — pad slots
      are checked first, same as today).
- [ ] Drag across the page → no speech start.
- [ ] Utterance start byte equals the tapped rect's byteOffset in the log
      (`[READALOUD] utterance start serial=… byteOff=…`).

### Traps

- **Do not touch PadCore** — the candidate is three fields in the shim's
  anonymous namespace next to the other watch state, not a new gesture class
  bolted into the pad's pure core.
- **Word-start slicing**: `StartUtterance` offsets from taps are rect
  byteOffsets, which FW-B guarantees are word starts — the Phase-1 slicing
  precondition holds by construction. Never "round" a tap to an arbitrary
  byte.
- **Highlight resumable-scan reset**: jumping backwards (tapping an earlier
  word) must reset the Phase-3 scan index, or highlights stop tracking after
  a backwards jump. A core test row covers it.

---

## Verification matrix — who can check what

| Environment | Can verify |
|---|---|
| Linux cloud session, this repo only | `tests/run_all.sh` (channel + core tests, all phases' state machines), header-compile checks |
| Desktop with firmware checkout (Mac or Linux) | Everything above, plus FW-A/FW-B end-to-end via `CROSSPOINT_SIM_READALOUD_LOG=1` (text, `words=`, clear-on-exit, page-turn republish), pio canary build |
| Mac with Xcode, iOS Simulator | All audible/visual acceptance: speech, auto page-turn, highlight placement, taps, both appearances |
| Physical iPhone (TestFlight via `ios/testflight.sh`) | Silent-switch behaviour, real voices (downloaded enhanced/premium), Bluetooth audio, performance |

Known accepted simplifications (do not "fix" in these phases): audio stops on
backgrounding (no background-audio entitlement/Now Playing integration);
audio-session interruptions (calls) are treated as cancel — reading does not
auto-resume; landscape reading unsupported; sentences split across a page
boundary are spoken with a page-turn pause in the middle; a firmware
re-render of the same page (e.g. AA toggle) restarts its speech.

## Documentation & bookkeeping (part of each phase's PR)

- Phase 1: add the channel to CLAUDE.md's HAL-surface notes (one short
  paragraph next to the keyboard-channel one) and the two tests to the test
  table and command list.
- Phase 4 (feature complete): update ios/README.md with the owner-facing
  behaviour table (toggle, tap, what stops reading), and close ST-003 in
  TODO.md.
- Each firmware PR notes the simulator version/commit it needs, and the
  firmware pin/source-set/`firmware_repo` triple stays in sync per
  CONTEXT-sim-notes.md's invariant if TUs were added.
