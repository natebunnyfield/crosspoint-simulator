#pragma once

#include <chrono>

// The Arduino clock's epoch -- the instant millis()/micros() count from.
//
// On hardware a reset zeroes the tick counter, and the firmware is written
// against that: every `millis() - startedAt` comparison assumes startedAt was
// taken this boot. The desktop simulator matches for free (its reboot is
// execvp, a fresh process re-runs the static initializer), but the iOS reboot
// is a longjmp in the SAME process, where a function-local `static const auto
// start` survives -- so millis() kept counting across the wake and every
// *_AFTER_WAKE schedule (screenshots, input scripts) compared its offsets
// against a clock that was already hours in. The schedules fired instantly,
// silently defeating the re-parse registrars that were added to fix exactly
// that (S-002).
//
// So the epoch is a named, re-basable value: SimulatorLifecycle registers a
// simreset callback that re-bases it at the in-process reboot boundary, and
// millis() restarts near 0 exactly as a chip reset would. steady_clock, not
// system_clock, deliberately (see Arduino.h): wall-clock changes must not
// perturb timing.
//
// Header-only and chrono-only so a plain host test (tests/reboot_resets_test)
// can pin the re-base without dragging SDL or the HAL in.
namespace simclock {

inline std::chrono::steady_clock::time_point &epoch() {
  static auto start = std::chrono::steady_clock::now();
  return start;
}

// The reboot boundary. Only ever called from the simreset registry, which only
// runs on the in-process (iOS) reboot path -- the desktop's execvp reboot
// never calls it, so the desktop canary is bit-identical with this present.
inline void rebaseForReboot() {
  epoch() = std::chrono::steady_clock::now();
}

inline unsigned long millisSinceEpoch() {
  using namespace std::chrono;
  return duration_cast<milliseconds>(steady_clock::now() - epoch()).count();
}

inline unsigned long microsSinceEpoch() {
  using namespace std::chrono;
  return duration_cast<microseconds>(steady_clock::now() - epoch()).count();
}

}  // namespace simclock
