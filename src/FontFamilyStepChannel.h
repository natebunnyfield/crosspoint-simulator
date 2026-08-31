#pragma once

#include <atomic>

// The font-family step channel: a host gesture (the iOS shake, in zen mode
// and outside it since 2026-08-29, or SHAKE in CROSSPOINT_SIM_INPUT_SCRIPT)
// on its way to the reader's family cycle. Owned by HalGPIO; kept as a free
// header with no SDL or HAL state so a plain host test can assert the
// contract (the ReadAloudChannel.h pattern).
//
// Same consume discipline as ReadAloudChannel: exactly one consume per
// inject, and a burst of injects between polls collapses to ONE step -- the
// reader re-paginates per step, so a queue here would turn one enthusiastic
// shake into a storm of SD loads. A burst that changes DIRECTION between
// polls keeps whichever direction was injected LAST: this is a level, like
// pending_, not an edge queue, and there is no principled "right" answer for
// a mid-burst reversal that cannot come from one physical shake anyway.
//
// DIRECTION, added 2026-08-29 for Action::FontFamilyStepBack
// (ios/GestureBindings.h) -- owner: "allow previous font to be an assignable
// gesture action." +1 steps to the next family, -1 to the previous, matching
// the sign EpubReaderActivity::cycleReaderFontFamily(int delta) already
// accepts (crosspoint-reader/src/activities/reader/EpubReaderActivity.cpp:818)
// -- a held side button already calls it with held.next ? +1 : -1
// (EpubReaderActivity.cpp:601), so backward stepping is not a new reader
// capability, only a value this channel did not used to carry. Chose a plain
// signed delta over an enum because that is the shape the consumer already
// takes and already uses this exact idiom for the same button today.
//
// BACKWARD COMPATIBLE ON PURPOSE. inject() and consume() keep their original
// zero-argument shapes and behavior, because crosspoint-simulator's own
// src/HalGPIO.cpp calls them exactly that way today
// (`fontFamilyStepChannel.inject();`, `return fontFamilyStepChannel.consume();`)
// and this change does not touch that file. inject() with no argument still
// means "step forward", byte-for-byte the same as before. direction() is new
// and purely additive.
class FontFamilyStepChannel {
public:
  // Host side (simulator-only, like injectButton*). delta: +1 = next family,
  // -1 = previous; any negative value folds to -1 and everything else to +1,
  // so a caller cannot inject a delta that skips more than one family.
  // Defaulted so the existing no-argument call (the shake) keeps compiling
  // and keeps meaning "forward".
  void inject(int delta = +1) {
    direction_.store(delta < 0 ? -1 : +1);
    pending_.store(true);
  }

  // Firmware side: true once per inject. Unchanged contract -- a caller that
  // only checks the return value (EpubReaderActivity.cpp today) sees no
  // difference from before this change.
  bool consume() { return pending_.exchange(false); }

  // The direction of the step consume() just reported. Only meaningful in
  // the same poll, immediately after consume() returns true -- read it
  // before another inject() can retarget it. A caller that ignores it (every
  // caller today) costs nothing: it is a peek, not a second consume.
  int direction() const { return direction_.load(); }

  // The in-process (iOS) reboot boundary: a step injected in the run being
  // abandoned must not land on the next boot's reader.
  void resetForReboot() { pending_.store(false); }

private:
  std::atomic<bool> pending_{false};
  std::atomic<int> direction_{+1};
};

// --- What this file does NOT close ------------------------------------------
//
// The channel can carry a direction now, but nothing reads direction() yet.
// "Previous font" cannot fire end to end until three more matched edits land,
// none of them in this file's scope:
//
//  1. crosspoint-simulator/src/HalGPIO.h + .cpp: injectFontFamilyStep() needs
//     a `delta` argument (default +1, so the shake's existing call keeps
//     compiling unchanged), and consumeFontFamilyStep() needs a way to hand
//     back direction() to firmware -- e.g. an added
//     `bool consumeFontFamilyStep(int& delta)` overload that reads
//     fontFamilyStepChannel.direction() right after a true consume().
//  2. crosspoint-reader/lib/hal/HalGPIO.h's inline no-op (line 276 as of
//     2026-08-29) needs the matching new signature, returning false and
//     leaving delta untouched, so on-device firmware still compiles to
//     nothing extra.
//  3. crosspoint-reader's EpubReaderActivity.cpp (around lines 412-414)
//     needs to read that delta and call cycleReaderFontFamily(delta) instead
//     of the hardcoded cycleReaderFontFamily(+1).
//  4. ios/CrossPointZenRecognizers.mm's FontFamilyStepBack case needs to call
//     the new injectFontFamilyStep(-1) instead of only logging that it is
//     offered but not wired.
//
// (1)-(3) are one matched HAL-method change under this project's HAL stub
// rule: firmware calls a method that must exist, with the SAME signature, on
// both the device's inline no-op and the simulator's real HalGPIO -- and the
// desktop canary (`pio run -e simulator`, built from the crosspoint-reader
// repo) links against crosspoint-simulator's HalGPIO.cpp. Landing only one
// side breaks a build the other side needs green, so (1), (2) and (3) have
// to ship together. (4) is independent and can follow once (1) exists.
