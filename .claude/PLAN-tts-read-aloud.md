# PLAN: Read-aloud TTS on the iOS harness (Apple speech)

Tracked as ST-003 in [TODO.md](../TODO.md). Written 2026-08-07 against `main`
@ `ebf2b54`; this revision is calibrated for a capable implementer — it fixes
the contracts, gates, and sharp edges, and trusts the rest to judgment.
**WP-1 below is implemented on this branch.**

The end state: on the phone, with a book open, the app reads the page aloud
in the voice the owner picked in Settings > Accessibility > Spoken Content >
Voices, turns the page itself at the bottom, highlights each word as spoken,
and starts from any tapped word. All behind a default-off toggle in
Settings > CrossPoint X3.

The owner's increments — spike it, turn the page, highlight, start at a
word — are delivery milestones. The *work* splits along toolchain seams, and
that is how it is packaged:

| Package | Where it runs / verifies | What it is |
|---|---|---|
| **WP-1** | this repo; builds and tests on Linux | The whole platform-neutral feature: HAL channel, complete `ReadAloudCore` state machine (speak → page-turn → highlight → tap), overlay geometry accessors, headless drain, host tests |
| **WP-2** | firmware fork (`natebunnyfield/crosspoint-reader` @ `x3-main`) + a desktop run | Page capture: FW-A text (gate G0), FW-B word rects |
| **WP-3** | Mac (Xcode / iOS Simulator / device) | The AVSpeech adapter, Settings toggle, highlight painter, tap plumbing in the shim |

Dependencies: WP-2 and WP-3 both build on WP-1's contracts. G0 (text
quality) gates *investing further in WP-2/3 polish*, not writing WP-3's
adapter — but do not ship any of it to TestFlight before G0 passes.
Milestone mapping: "spike" = WP-3's canned-utterance checkpoint + G0;
"page turn" / "highlight" / "tap" land as WP-2+WP-3 wire up the
already-tested core transitions.

## Decisions (condensed; relitigate only with new information)

- **D1 — text comes from the firmware's layout pass** over a HAL channel.
  Harness-side EPUB parsing duplicates pagination and drifts; OCR/Screen
  Recognition can't sync or control; `UIAccessibilityElement` + Speak Screen
  can't page-turn, highlight, or start-at-word — but is a cheap, genuine
  VoiceOver win once the channel exists: recorded as follow-on work, own
  TODO entry when Phase 4 ships.
- **D2 — `AVSpeechSynthesizer`, system default voice** (`voiceWithLanguage:nil`
  honours the owner's Spoken Content voice). Per-book language and a rate
  control are non-goals for v1.
- **D3 — page turns are real injected button presses** so the firmware owns
  pagination, progress, chapters, end-of-book. Via `queueButtonTap` (below),
  not raw `injectButtonDown` from the harness — see sharp edge E1.
- **D4 — the channel lives on `HalGPIO`**, keyboard-channel precedent:
  firmware-facing half gets inline no-ops in the firmware's `lib/hal/HalGPIO.h`
  in the same firmware PR that first calls it; simulator-only half gets no
  firmware counterpart. Full signature fixed once (rects `nullptr` until FW-B).
- **D5 — the toggle is phone state** (Settings.bundle, like Keep Screen
  Awake), not `settings.json`.
- **D6 — highlight is overlay chrome**, not a firmware re-render: per-word
  e-ink refreshes have no device analog. Cost: invisible to
  `CROSSPOINT_SIM_SCREENSHOTS` (pre-composite); verify on-glass.
- **D7 — decision logic is pure and clock-free** (`ios/ReadAloudCore`,
  PadCore's discipline) so every transition is host-testable on Linux; time
  and geometry enter only as inputs.

## Risks (owner in parentheses)

- **R1 (G0): the layout pass can't yield clean text** — hyphenated line
  fragments, soft hyphens, page furniture. THE feasibility risk; everything
  else is engineering. If neither capture strategy passes G0, stop and
  renegotiate scope (paragraph-granularity speech is the fallback).
- R2 (FW-B): rects drift from text → both must come from one capture pass.
- R3 (WP-3): `NSRange` is UTF-16 code units; channel offsets are UTF-8 bytes.
- R4 (G0): capture must track the *displayed* page, not a pre-render.
- R5 (FW-B): rect coords must be render-scale-independent (iOS core runs 2x).
- R6 (WP-3): silent-switch audio → `AVAudioSessionCategoryPlayback`; verify
  on a physical phone.
- R7 (WP-3): async `didCancel` after `stopSpeaking` must not kill the next
  utterance → utterance serial filter in the adapter.
- R8 (core, done): end-of-book leaves AwaitingNextPage → adapter counts ~5 s
  of frames and feeds `pageTimeout()`.
- R10 (accepted): wrong voice for non-English books.

## Contracts (fixed; both repos and all packages depend on them)

**Text.** The published UTF-8 string is the page's logical content text:
reading order, single spaces, `\n` between paragraphs; no layout-inserted
hyphens, soft hyphens (U+00AD) stripped, words split across lines appear
whole and once; no page furniture (headers, page numbers, progress). Two
capture strategies — slice the paginator's source range (preferred) or
accumulate draw calls with merging/stripping (fallback); G0 decides.

**Channel** (implemented, [src/ReadAloudChannel.h](../src/ReadAloudChannel.h)):
`ReadAloudWordRect{ uint16 x,y,w,h; uint32 byteOffset; uint16 byteLen }` in
logical portrait panel px (X3: 528×792, y down), offsets into the page's
UTF-8; a line-wrapped word publishes one rect per visual fragment, all
sharing the word's byteOffset/byteLen. On `HalGPIO`: firmware-facing
`readAloudCaptureWanted()` / `publishReadAloudPage(utf8, len, rects, count)`
(device: inline `false` / no-op; `publish(nullptr,0,nullptr,0)` means "no
page — reader exited", consumers stop); simulator-only
`setReadAloudCaptureWanted(bool)` / `consumeReadAloudPage(ReadAloudPage&)`.
One consumer per build: the env-gated desktop logger
(`CROSSPOINT_SIM_READALOUD_LOG=1`, `#if !CROSSPOINT_SIM_IOS` in
simulator_main.cpp) or the iOS adapter — never both.

**Highlight** carries a byte range, not a rect index; the painter fills
every rect with that range, so split words light on both lines for free.

**Geometry.** Presented-panel accessors on `SimulatorOverlay`
(`panelLeftPx/panelWidthPx`, stored beside the existing pair on the
manual-placement path): scale `S = panelWidthPx / HalDisplay::DISPLAY_HEIGHT`
(portrait width == landscape fb height), origin
`(panelLeftPx, panelBottomPx − panelHeightPx)`. Portrait only.

**Logs** all start `[READALOUD] ` — acceptance steps grep that.

## WP-1 — platform-neutral feature (this repo) — IMPLEMENTED

What landed, where:

- [src/ReadAloudChannel.h](../src/ReadAloudChannel.h) — channel + PODs.
- [src/HalGPIO.h](../src/HalGPIO.h)/.cpp — the four channel methods, plus
  **`queueButtonTap(button, holdMs)`** (simulator-only): schedules a
  down/up pair that fires *inside `update()`*, where the pad's own
  injections land. Exists because of E1 — a harness cannot press buttons
  from the per-frame hook.
- [src/SimulatorOverlay.h](../src/SimulatorOverlay.h) /
  [src/HalDisplay.cpp](../src/HalDisplay.cpp) — `panelLeftPx/panelWidthPx`.
- [src/simulator_main.cpp](../src/simulator_main.cpp) — env-gated drain/log.
- [ios/ReadAloudCore.h](../ios/ReadAloudCore.h)/.cpp — the complete state
  machine (Off / Speaking / AwaitingNextPage; enable, pageArrived incl.
  cleared, finished vs canceled, pageTimeout, willSpeakByte with resumable
  scan and per-word dedupe, tapAtLogical with 2-px inflation, taps ignored
  in AwaitingNextPage where rects are stale).
- tests/read_aloud_channel_test.cpp, tests/read_aloud_core_test.cpp,
  registered in tests/run_all.sh. Green on Linux.

Not verifiable in the authoring environment (no firmware checkout, no SDL3):
the desktop pio build over the HalGPIO/HalDisplay/simulator_main edits.
**First desktop build after pulling this branch is the canary for those.**

## WP-2 — firmware capture (fork, branch off `x3-main`)

Simulator symlinked (`simulator=symlink://../crosspoint-simulator`).

**FW-A (text):** add the `ReadAloudWordRect` POD and the two inline no-ops to
`lib/hal/HalGPIO.h` (next to the text-entry no-ops, field-identical). Find
the paginator via the reader activity (`EpubReaderActivity` →
page-render path); prefer Strategy 1 (source-range slice). Capture only when
`gpio.readAloudCaptureWanted()`; publish after the displayed page's render;
publish `nullptr` on reader exit. New TUs require the iOS source-set regen
(CLAUDE.md).

**Gate G0** — headless, three books (plain / hyphenation-heavy / curly
quotes):

```bash
CROSSPOINT_SIM_READALOUD_LOG=1 \
CROSSPOINT_SIM_INPUT_SCRIPT='2000:HOME;3000:BACK;8000:DOWN;10000:UP;15000:QUIT' \
SDL_VIDEODRIVER=dummy .pio/build/simulator/program 2>&1 | grep -E 'READALOUD|ACT'
```

Pass = captured text matches the visible page word-for-word in order; no
fragments, no U+00AD, no furniture; DOWN/UP produce gens tracking the
visible page; BACK logs `cleared=1`; zero `[READALOUD]` lines without the
env var. Fail after both strategies = stop, report, renegotiate.

**FW-B (rects):** same pass as the text (R2), logical portrait px — divide
by the firmware's render scale at capture (R5); one rect per fragment for
wrapped words. `words=` in the log becomes plausible against a screenshot;
`bytes=` unchanged from FW-A.

Verify page-forward is `BTN_DOWN` while in there (reader's next-page branch;
G0's `DOWN` already shows the republish) — the adapter assumes it.

## WP-3 — the adapter (Mac)

`ios/CrossPointReadAloud.{h,mm}` (+ CMake sources, `-fobjc-arc`,
`-framework AVFoundation`; toggle key `readAloudEnabled` in Root.plist +
`CrossPointPrefs_readAloudEnabled()` — the Prefs pattern derives
registerDefaults from the plist already). Shape:

- `begin()` from `CrossPointHarness_begin()` (idempotent across wakes),
  `perFrame()` from `CrossPointHarness_perFrame()`. Main thread only.
- Audio session: `Playback` + `SpokenAudio`, activated lazily on first
  speak (R6). First checkpoint = canned utterance behind the toggle —
  audible in the iOS Simulator and on a muted physical phone; that is the
  owner's "spike that it is possible", demoable before WP-2 exists.
- perFrame order: poll pref edge → `setEnabled` + `setReadAloudCaptureWanted`;
  drain channel (keep last page; hold its `utf8` for slicing); drain
  delegate-event queue, **dropping events whose utterance serial ≠ current**
  (R7; tag via `objc_setAssociatedObject`); feed core; apply actions.
- Apply: StartUtterance(off) → slice `utf8` from `off` (always a rect start,
  so a valid UTF-8 boundary), bump serial, remember base offset;
  StopUtterance → `stopSpeakingAtBoundary:Immediate`; TurnPageForward →
  `gpio.queueButtonTap(HalGPIO::BTN_DOWN, 60)` and arm a ~5000-frame
  timeout that feeds `pageTimeout()` unless a page arrives; Set/Clear
  highlight → main-thread state + `SimulatorOverlay::requestPresent()`.
- Delegate: enqueue only (callbacks arrive off-main). `willSpeakRange` →
  UTF-16→UTF-8 via
  `[[utt.speechString substringToIndex:range.location] lengthOfBytesUsingEncoding:NSUTF8StringEncoding]`,
  rebased by the utterance's base offset on drain (R3). `didFinish` vs
  `didCancel` stay distinct all the way down — cancel never turns a page.
- Painter: `paintPad` delegates to
  `CrossPointReadAloud_paintHighlight(r, outW, outH, g_dark)`; map rects with
  the geometry contract, inflate 2 device px,
  `SDL_BLENDMODE_BLEND`, fill 255,200,0 at alpha 80 (light) / 60 (dark).
- Tap: `padWatch` tracks a candidate (finger down on no pad slot; cancelled
  by motion > `12 * g_ptScale` px or the events the pad resets on; up →
  `CrossPointReadAloud_tapAtScreen(fx, fy)`); the adapter converts to
  logical panel coords (geometry lives in one place) and feeds
  `tapAtLogical`. No timers; PadCore untouched.

On-glass acceptance (iOS Simulator unless noted): page spoken; manual turn
re-speaks; BACK stops (cleared publish); toggle-off stops; hands-free across
3+ pages and progress persists across a relaunch (the injected press was
real); end-of-book times out once, cleanly; highlight sits on the spoken
word in both appearances, survives multibyte text, lights both lines of a
split word; tap starts/jumps with no double audio; margins/drags do
nothing; pad unchanged; muted physical phone still audible.

## Sharp edges (measured or already-burned; do not rediscover)

- **E1 — perFrame injections lose their edges.** `beginFrame()` clears the
  edge latches at the top of each frame; `CrossPointHarness_perFrame()` runs
  *after* `loop()`, so a press injected there is wiped before any
  `wasPressed()` can see it. The pad works because its event watch fires
  inside `update()` (inside `loop()`). Hence `queueButtonTap`, which
  processes inside `update()`. Never inject buttons from the per-frame hook.
- `SDL_PushEvent` cannot drive level reads (`SDL_GetKeyboardState` untouched
  by pushed events) — the existing injection APIs exist for a reason.
- `NSRange` is UTF-16 code units (R3); ASCII books mask the bug.
- Screenshots are pre-composite; the highlight never appears in them (D6).
- One overlay callback (`setDrawCallback` holds a single pointer) — the pad
  painter delegates.
- One channel consumer per build; the desktop logger is compiled out on iOS.
- Headless scripts: open with `2000:HOME`, believe `[ACT]` lines, and boot
  destination varies run-to-run (CLAUDE.md; four runs burned twice).
- `.mm` compiles only on a Mac; that is why WP-1/WP-3 split where they do.
- No new cross-cutting defines; anything shared goes on
  `crosspoint_core PUBLIC` (split-brain guard, CLAUDE.md).

## Non-goals (v1, deliberate)

No background audio or lock-screen controls; interruptions = cancel, no
auto-resume; system voice regardless of book language; portrait only; a
sentence split across pages gets the turn's pause; a same-page re-render
restarts its speech; CJK segmentation not attempted; enabling the toggle
mid-page takes effect at the next page render (capture publishes at render).

## Bookkeeping

CLAUDE.md gains the channel note + the two tests (done with WP-1). WP-3
completion: owner-facing behaviour table in ios/README.md, close ST-003,
file the accessibility follow-on (D1) as its own entry. Firmware PRs name
the simulator commit they need; pin/source-set/`firmware_repo` stay in sync
if TUs are added.
