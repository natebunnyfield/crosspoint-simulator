#pragma once

// The firmware's serial log, written where the OWNER can read it: on the phone.
//
// This harness compiles the firmware at LOG_LEVEL=2, so every LOG_DBG the
// reader emits is already being produced. On iOS all of it goes to stderr,
// which a TestFlight build discards -- the same blind spot CrossPointDiagLog.h
// was written for, and the reason two "chapter selection lands a page early"
// fixes shipped on reasoning about what the state must be instead of on a
// reading of what it was.
//
// The harness chdir()s into the app's Documents directory (the emulated SD
// card) and Info.plist exposes it in the Files app as On My iPhone ->
// CrossPoint X3, so a file written here is readable and share-able FROM THE
// PHONE: open Files, tap the file, long-press to share. No Mac, no cable, no
// Console.app -- which is what closes the loop on a report from someone who is
// reading in bed, not sitting at a desk.
//
// SEPARATE FROM diagnostics/a11y.log ON PURPOSE. That file is the
// accessibility instrument, and its header asks -- correctly -- that it not
// grow into a general logger: twenty lines that matter must not be buried
// under thousands that do not. This is the general logger, in its own file, so
// both stay legible.
//
// Off unless asked for: the Settings.app "Diagnostics Log" switch (the same
// one that arms the a11y log), or CROSSPOINT_SIM_DIAGNOSTICS=1 for a scripted
// run. A desktop build needs neither -- stderr is right there in the terminal.
//
// Rotated, never truncated, one generation back: "it did the wrong thing a few
// minutes ago" has to still be answerable after the reader has paged on.
//
// HEADER-ONLY BY NECESSITY, not by taste. cmake/CrossPointSources.cmake is
// generated from the firmware's compile database, so a new .cpp here goes
// stale the moment anyone regenerates it and the iOS build's staleness gate
// then refuses to configure. A header costs nothing there -- and it also lets
// tests/firmware_log_file_test.cpp compile this code without dragging in
// ESP.cpp's SDL and Bonjour dependencies.

#include <sys/stat.h>

#include <cstddef>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <ctime>
#include <mutex>

namespace firmwarelog {

// Where the log lands, relative to the card root. The rotated generation is
// this path plus ".1".
inline constexpr const char *kFirmwareLogPath = "diagnostics/firmware.log";

namespace detail {

// One generation back, at a quarter megabyte. A reader paging steadily emits a
// few hundred bytes a page, so this holds a long sitting -- and the question is
// almost always about something that happened minutes ago, not hours.
inline constexpr long kRotateBytes = 256 * 1024;

// How often the host's switch is re-read. Per line would put an NSUserDefaults
// lookup in the middle of every LOG_DBG; per second is indistinguishable to a
// person flipping a switch in Settings.app and walking back to the app.
inline constexpr double kProviderPollSeconds = 1.0;

// Flushing every line would fsync-storm a section build. A quarter second is
// well under the time it takes to leave the reader and open the Files app, so
// a log read after the fact is never missing its last lines.
inline constexpr double kFlushSeconds = 0.25;

struct State {
  std::mutex mutex;
  int (*provider)() = nullptr;
  FILE *file = nullptr;
  long bytes = 0;
  double lastFlush = 0.0;
  double lastPoll = 0.0;
  bool lastAnswer = false;
};

inline State &state() {
  static State s;
  return s;
}

inline double nowSeconds() {
  struct timespec ts {};
  clock_gettime(CLOCK_MONOTONIC, &ts);
  return (double)ts.tv_sec + (double)ts.tv_nsec / 1e9;
}

// The headless door, matching CrossPointPrefs_diagnosticsEnabled's: read once,
// and it can only ENABLE. A scripted run asks for the instrument; the owner's
// Off is never overridden by an environment variable behind their back.
inline bool forcedOn() {
  static const bool forced = [] {
    const char *v = std::getenv("CROSSPOINT_SIM_DIAGNOSTICS");
    return v != nullptr && v[0] == '1';
  }();
  return forced;
}

// A nested call must not reach the lock. The gate the host installs is
// arbitrary code -- today it reads NSUserDefaults and logs with NSLog, which
// is inert here, but anything reachable from it that calls SDL_Log would come
// straight back through hostLine() with the mutex already held and deadlock
// the app on a non-recursive std::mutex. An instrument must never be able to
// take the reader down with it, so a re-entrant call is dropped instead.
// Thread-local: two threads logging at once is the normal case and is what the
// mutex is for; one thread logging FROM inside its own log call is not.
inline bool &reentering() {
  static thread_local bool r = false;
  return r;
}

struct ReentryGuard {
  const bool taken;
  ReentryGuard() : taken(!reentering()) {
    if (taken) reentering() = true;
  }
  ~ReentryGuard() {
    if (taken) reentering() = false;
  }
  ReentryGuard(const ReentryGuard &) = delete;
  ReentryGuard &operator=(const ReentryGuard &) = delete;
};

inline void closeFileLocked(State &s) {
  if (!s.file) return;
  ::fclose(s.file);
  s.file = nullptr;
  s.bytes = 0;
}

inline bool armedLocked(State &s) {
  if (forcedOn()) return true;
  if (!s.provider) return false;
  const double now = nowSeconds();
  if (now - s.lastPoll >= kProviderPollSeconds) {
    s.lastPoll = now;
    s.lastAnswer = s.provider() != 0;
  }
  return s.lastAnswer;
}

inline void rotateLocked(State &s) {
  closeFileLocked(s);
  char prev[128];
  snprintf(prev, sizeof(prev), "%s.1", kFirmwareLogPath);
  ::remove(prev);
  ::rename(kFirmwareLogPath, prev);
}

// Relative paths, resolved against the cwd the harness set (the card root).
// Before that chdir the fopen simply fails and every call is a no-op, so early
// boot logging degrades to stderr rather than writing into the read-only
// bundle's directory.
inline bool openLocked(State &s) {
  if (s.file) return true;
  ::mkdir("diagnostics", 0755);  // idempotent; EEXIST is the normal case
  s.file = ::fopen(kFirmwareLogPath, "a");
  if (!s.file) return false;
  ::fseek(s.file, 0, SEEK_END);
  const long end = ::ftell(s.file);
  s.bytes = end > 0 ? end : 0;
  return true;
}

// The owner can delete this file from the Files app WHILE the app is running.
// Clearing an old log before reproducing something is the obvious thing to do,
// and it is the exact moment the log matters most -- but an open handle keeps
// appending into the deleted inode: no error, no file, and a report that the
// logging "stopped working". One stat per logged line reopens it instead.
inline void ensureLiveLocked(State &s) {
  if (!s.file) return;
  struct stat st {};
  if (::stat(kFirmwareLogPath, &st) != 0) closeFileLocked(s);
}

inline void appendLocked(State &s, const char *bytes, size_t count) {
  if (!openLocked(s)) return;
  ::fwrite(bytes, 1, count, s.file);
  s.bytes += (long)count;
  const double now = nowSeconds();
  if (now - s.lastFlush >= kFlushSeconds) {
    s.lastFlush = now;
    ::fflush(s.file);
  }
  if (s.bytes >= kRotateBytes) rotateLocked(s);
}

}  // namespace detail

// Installs the host's answer to "is the diagnostics log armed?". iOS passes
// CrossPointPrefs_diagnosticsEnabled, so the Settings.app switch arms and
// disarms this file without a rebuild. Polled rather than cached forever, and
// this call forces the next poll to happen immediately. Not installed => off.
inline void setEnabledProvider(int (*provider)()) {
  detail::State &s = detail::state();
  std::lock_guard<std::mutex> lock(s.mutex);
  s.provider = provider;
  s.lastPoll = 0.0;
}

// Appends raw serial bytes exactly as the firmware wrote them. They already
// carry logPrintf's own "[millis] [LVL] [ORIGIN] " prefix, so nothing is added
// here beyond the bytes themselves.
inline void write(const char *bytes, size_t count) {
  if (!bytes || count == 0) return;
  detail::ReentryGuard guard;
  if (!guard.taken) return;
  detail::State &s = detail::state();
  std::lock_guard<std::mutex> lock(s.mutex);
  if (!detail::armedLocked(s)) {
    detail::closeFileLocked(s);  // a switch turned off mid-session releases the handle
    return;
  }
  detail::ensureLiveLocked(s);
  detail::appendLocked(s, bytes, count);
}

// Appends one host-side line (SDL_Log's output), tagged so it cannot be
// mistaken for firmware output. The harness half of a story -- an injected
// button, a foreground return -- is what separates "the reader jumped wrong"
// from "the reader jumped right and then something turned the page".
inline void hostLine(const char *text) {
  if (!text) return;
  detail::ReentryGuard guard;
  if (!guard.taken) return;
  detail::State &s = detail::state();
  std::lock_guard<std::mutex> lock(s.mutex);
  if (!detail::armedLocked(s)) {
    detail::closeFileLocked(s);
    return;
  }
  detail::ensureLiveLocked(s);
  detail::appendLocked(s, "[host] ", 7);
  detail::appendLocked(s, text, strlen(text));
  detail::appendLocked(s, "\n", 1);
}

// Pushes buffered bytes to disk. Writes are otherwise flushed a few times a
// second, so call this before the app can be suspended or killed.
inline void flush() {
  detail::ReentryGuard guard;
  if (!guard.taken) return;
  detail::State &s = detail::state();
  std::lock_guard<std::mutex> lock(s.mutex);
  if (s.file) ::fflush(s.file);
}

}  // namespace firmwarelog
