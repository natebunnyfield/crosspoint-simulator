# PLAN: Read-aloud TTS on the iOS harness (Apple speech)

Tracked as ST-003 in [TODO.md](../TODO.md). Written 2026-08-07 against `main`
@ `ebf2b54`; this revision is calibrated for a capable implementer — it fixes
the contracts, gates, and sharp edges, and trusts the rest to judgment.
**Status 2026-08-08: WP-1 and WP-2 are implemented and verified headlessly —
gate G0 PASSED (evidence in the WP-2 section). Remaining: WP-3's Mac compile
and on-glass acceptance.** The firmware side lives on the fork's
`read-aloud-capture` branch. Note: the firmware branch situation changed —
`x3-main` no longer exists; the fork's `main` IS the working branch, and this
fork's reader pages with the RIGHT front button, opens chapter selection on
CONFIRM, and auto-opens the sole book on a fresh card (all verified, all
diverging from older notes).

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
- `QTAP:<BUTTON>[:<holdMs>]` input-script action driving `queueButtonTap`,
  `CROSSPOINT_SIM_READALOUD_LOG=2` (full text + rect dump, the G0 audit
  format), and tests/test_read_aloud_capture.sh — an end-to-end shell test
  against a GENERATED two-chapter EPUB fixture (the seed book's mono-file
  chapter paginates for tens of seconds; the fixture is instant and
  deterministic).

The desktop pio build has since been run and is green (SDL3 built from
source on Linux; firmware fork cloned; symlink dev flow per CLAUDE.md).

## WP-2 — firmware capture — DONE, gate G0 PASSED (2026-08-08)

Landed on the fork's `read-aloud-capture` branch (off `main` @ `4ded8fc`;
`x3-main` no longer exists):

- `lib/hal/HalGPIO.h`: the `ReadAloudWordRect` POD at NAMESPACE scope
  (matching the simulator, so the capture code references it unqualified in
  both builds) plus the two inline no-ops.
- `EpubReaderActivity.cpp`: `captureReadAloudPage()` walks the display list
  in `renderContents()` — the one site that renders the DISPLAYED page. Not
  in `Page::render`, which the idle prewarm also runs against the NEXT page
  ("scan only, no pixels") and which would capture the wrong text (R4).
  What the walk does: per `PageLine`, per word, builds glue runs (tokens
  with no visible pixel gap — punctuation slices, CJK segments — captured
  as one word), strips soft hyphens, and reunites hyphen-split words across
  lines (the layout stores `"consid-"` + `"eration"` as separate tokens with
  the visible hyphen IN the prefix; a line-final `-` joins to the next
  line's first run, hyphen dropped, fragments sharing the word's byte
  range). Rects come from `wordXpos` + `getTextAdvanceX`, top =
  baseline − ascender, height = line height, in logical portrait px (layout
  runs at 1x regardless of render scale, so no division needed). Text and
  offsets are built in the same walk (R2). `onExit()` publishes the clear.
- Neither strategy from the original framing was needed as written: the
  display list already carries per-word text and positions; only the
  hyphen/glue reconstruction was real work.

**G0 evidence** (fork `main`, X3 profile, headless Linux): a justified,
hyphenation-on page of English Fairy Tales captured word-for-word against
its screenshot — "folk-/tale", "nurs-/ery", "extraordi-/nary" all reunited
correctly, em-dash and curly quotes intact; 484 rects across the run, zero
U+00AD bytes; page-forward then page-back republished byte-identical text
for the returned-to page; reader exit published `cleared=1`; zero publishes
without the env var. The RIGHT front button is page-forward
(`ReaderUtils::detectPageTurn`) — the adapter was corrected from the
BTN_DOWN assumption. `tests/test_read_aloud_capture.sh` pins all of this
permanently, including the `queueButtonTap` page-turn path end-to-end.

Known accepted imperfection: a paragraph-final real hyphen would be joined
to the next paragraph's first word (rare; the audit found zero instances).

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
  `gpio.queueButtonTap(HalGPIO::BTN_RIGHT, 60)` (RIGHT, verified against
  `ReaderUtils::detectPageTurn` — nav-swap inverts it, accepted) and arm a
  ~5000-frame timeout that feeds `pageTimeout()` unless a page arrives;
  Set/Clear highlight → main-thread state +
  `SimulatorOverlay::requestPresent()`.
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
- **E1b — the capture flag races the first render.** A fast book renders its
  first page inside the FIRST `loop()` iteration; any consumer that sets
  `setReadAloudCaptureWanted` lazily (main-loop lambda, perFrame edge
  detector) misses that page. Both consumers seed the flag before the loop:
  the desktop logger before `setup()`, the adapter in
  `CrossPointReadAloud_begin()`. Found live when the fixture book published
  chapter two's page but never chapter one's.
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
