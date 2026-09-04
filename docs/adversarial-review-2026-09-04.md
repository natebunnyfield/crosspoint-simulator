# Adversarial review — simulator, 2026-09-04

Read-only refuting pass over the code commits since 2026-08-30 (`c25448b` …
`6d2ca67`), per the `adversarial-review` skill: an agent that did not write
the code, told to disprove each candidate before reporting, and to list what
it found CLEAN. Five findings survived. 1–3 are fixed in the commit that adds
this file, 4 with it; 5 is the firmware's and was fixed
there (`crosspoint-reader/docs/adversarial-review-2026-09-04.md`, finding 2).

## Findings, ranked

### 1. A light→dark flip deposited the LIGHT page's glass into the phosphor accumulator — would-ship — FIXED

`d4c59bb` withheld the BEAM on a polarity reconvert (`reconvertOnly`), but
the trail DEPOSIT sixty lines later still keyed on `contentChanged` alone. A
reconvert bumps `pixelBufSeq`, so the previous glass — the light page,
captured at its ABSOLUTE intensity because the light polarity keeps it — went
into `accumTexture` at near-full white; the reconverted page is a dark ground,
so `accumLive` went true and the whole glass composited bright and decayed
over the trail. Both halves are live on the phone: the frozen guns carry a
1095 ms trail in BOTH appearances, so the light page is captured and every
appearance flip (system, or the in-app Dark Mode row) deposits it. Inside the
owner's 2026-08-30 "do not flash for any reason, period" (S-031).

Reproduced headlessly on `simulator_x3` (glow 1095, beam 55, `darkMode` 0→1
written to the card at 8.6 s, dummy driver):

| capture | pre-fix mean luma | post-fix |
|---|---|---|
| light page, settled (7.0 s) | 242.7 | 237.9 |
| first present after the flip (9.1 s) | **54.2** (`[accum] … live=1`) | **35.5** |
| +300 ms | 44.3 | 35.5 |
| +900 ms | 33.6 | 35.5 |
| settled dark (13 s) | 30.8 | 35.5 |

Pre-fix the flip frame was +23 luma against the settled page on 100% of
pixels, followed by 14 self-driven trail presents; post-fix the flip frame IS
the settled page and no trail present fires. (The two columns were sampled by
different scripts, so compare within a column.)

**Fix:** `reconvertOnly` is decided once under the lock and consumed by BOTH
the beam arm and the deposit, through `glasscapture::shouldArmBeam` /
`shouldDeposit` (`src/GlassCapture.h`, pinned in `tests/glass_capture_test.cpp`).
No new picture came in, so none left the glass either.

### 2. `reconvertSeq` was re-read under a second lock — latent — FIXED

`reconvertLastFrame()` bumped the sequence inside the writer's lock, released
it, and `presentIfNeeded` re-locked to copy `pixelBufSeq` into `reconvertSeq`.
A render-task page landing in the gap would have been taken for the
reconvert: its sweep withheld, its trail still deposited. Both writers now
return the sequence they produced from under their own lock, and the
reconvert records that.

### 3. A flip mid-sweep finished the sweep with the new palette over the old glass — latent — FIXED

The reconvert exception prevented a NEW arm but did not cancel a sweep in
flight, and the texture is re-uploaded with the reconverted pixels, so the
remaining frames of a 55 ms sweep were exactly S-031's split-palette frame.
`beamStartedAt = 0` beside the arm decision.

### 4. `ReaderInsetsChannel` clamps a negative top inset to 0 — latent — FIXED

The firmware publishes `paintTop = orientedMarginTop − getCapInkTrim(font)`;
at `screenMargin` 0 with a large face the trim can exceed the 9 px viewable
margin and the value goes negative. The four-atomic channel passed it
through; the packed one (`4cd50c4`) stores 16-bit unsigned fields and clamps.
Effect: the zen shift moves by up to trim × device scale on that one
configuration. `getCapInkTrim` is the ink top of 'H' in the line box, so a
negative is legitimate wherever the face's blank above the cap exceeds the
9 px viewable margin plus `screenMargin`. The fields are now stored
offset-by-32768 (signed), and the test round-trips a −7. Not measured on a
device; the four-atomic channel's behavior is restored, no more.

### 5. A stale `OpenActionMenu` request across a pushed child — firmware — FIXED there

`FileManagerActivity::onEnter` drains the channel but a pop back from the text
viewer does not re-enter. Fixed in the firmware's result handlers.

## CLEAN — checked, nothing found

- `ios/GestureBindings.h` stored-integer stability: `Action` 0–13 append-only;
  every `Root.plist` row's values match the enum, defaults match `kRows`, the
  dropped `gestureSwipeDownAbove` is absent and its orphaned NSUserDefaults key
  is inert; bindings are keyed by row STRING, so the enum re-sort moves nothing.
- `rowOf()` / `kNoRow` / `shipsInert` against the 13 installed recognizers;
  `shipsInert(Count)` false after `2726010`.
- `CrossPointZenRecognizers.mm` dispatch after `f841eaa`: no double-fire path;
  a tap with a field open is not swallowed off the chip; the shake's yield
  cannot outlive the field (`SDL_EVENT_SCREEN_KEYBOARD_HIDDEN` re-claims on
  every keyboard-down, the field's close included).
- `GlassCapture` sequences: first present of a session, screenshot-due
  override, gen-driven recapture with no pixel change, AA page written twice
  inside the sweep, size change mid-sweep, beam-without-trail and
  trail-without-beam — each deposits once and captures once.
- `ReaderInsetsChannel` packing above zero: 16-bit fields, max value 1056 at
  2x, acquire/release pairing correct.
- `de8b2fa` keyboard chip in zen: the rect exists on both device paths; the
  chip branch precedes the gesture branch; a chip tap cannot also page or
  toggle zen.
- `a8dea75` / `c25448b`: no state where zen is off and a shift applies, or zen
  on and the band skipped after the first layout.
- `tests/test_manage_files_and_wifi_nav.sh`: every press ≥ 900 ms apart, each
  arm discriminates.
- `ios/testflight.sh` `6d2ca67`: `$?` after `fi` is the taken branch's last
  command in both arms; heredoc terminator valid.
- `ca41866` / `958eea9` channels: a burst coalesces to the last direction by
  contract; the menu channel is drained on Manage Files entry.
- `4951b62`: the reading-experiment gate writes nothing unless the pref is on.

## Sanitizers, same day — CLEAN

Every `c++`-compiled entry in `tests/run_all.sh` (59 pure host tests)
rebuilt with `-fsanitize=address,undefined` and run with no arguments:
59/59 passed, no AddressSanitizer report, no UBSan `runtime error`. The
shell tests and the plist-argument tests were not part of this sweep. A
negative result, recorded so it is not paid for twice; the runner has no
sanitizer switch, so this was a one-off script over its compile lines.
