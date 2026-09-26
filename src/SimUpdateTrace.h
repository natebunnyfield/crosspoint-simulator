#pragma once

// UPDATE TRACE: the flight recorder for Update Fonts / Update Library on a
// host build (the iOS app above all), written so the NEXT report of "the
// screen froze" arrives with the answer in diagnostics/firmware.log.
//
// Why it exists (2026-09-26). The owner reported the two update screens
// freezing on the phone; a fix verified on the desktop simulator shipped as
// TestFlight builds 226/227 and the owner reported it again. Re-traced on the
// iOS Simulator the same day -- Debug and Release, light and dark, a mock
// release and the real GitHub release, a fresh card, a card seeded exactly as
// CrossPointFsPrep seeds a phone, an already-synced card, the experimental
// toggles on, in-app instruments on and off with the glass sampled from
// outside -- and the longest gap between presents was ~1.1 s in every run.
// Whatever stops the glass on the phone is not on any path the simulator
// exercises, and the project rule for a second device failure is an
// instrument, not another plausible patch. This is that instrument.
//
// What it records while an update screen is up (and only then):
//   * every present, with the gap since the previous one;
//   * every time presentIfNeeded had a present OWED and declined it, and why
//     (backgrounded, the sleep veto, the coalescing hold) -- the three early
//     returns that can hold the glass while everything else is healthy;
//   * the firmware's own steps (the activity calls mark()), and every host
//     fetch with its duration and size;
//   * a STALL line from a watchdog thread whenever the main loop, or the
//     glass, has not moved for kStallMs -- naming the stage the main loop is
//     parked in and the last step the firmware marked. A thread of its own,
//     because a stalled main thread cannot report on itself.
//
// With no update screen up, every call is a relaxed atomic load (frameWritten
// also stores the generation). Nothing here changes behavior. Lines are only
// emitted at all while the diagnostics log is armed -- the host's sink checks.
// firmware.log only exists while Settings.app > Diagnostics Log is on (or
// CROSSPOINT_SIM_DIAGNOSTICS=1); lines written before that are dropped by the
// sink, not buffered.
//
// HEADER-ONLY on purpose: cmake/CrossPointSources.cmake is generated from the
// firmware's compile database, so a new .cpp here would go stale the moment
// anyone regenerated it (same reason as FirmwareLogFile.h). The firmware
// includes it under #ifdef SIMULATOR only.

#include <atomic>
#include <cstdarg>
#include <cstdint>
#include <cstdio>
#include <cstring>

namespace sim_update_trace {

// A main loop or a glass that has not moved for this long is reported. The
// update screens' own heartbeat repaints once a second, so anything past 1.5 s
// is already a missed beat.
inline constexpr uint64_t kStallMs = 1500;
inline constexpr uint64_t kWorkingFreshMs = 300;

// Where a line goes. The host installs this (simulator_main: SDL_Log, which
// the firmware-log tee copies into diagnostics/firmware.log); unset -- a host
// test, or before startup -- lines are dropped.
using Sink = void (*)(const char *line);
inline std::atomic<Sink> g_sink{nullptr};
// Milliseconds on the firmware's millis() clock, supplied by the host so this
// header needs neither Arduino.h nor SDL.
using Clock = uint64_t (*)();
inline std::atomic<Clock> g_clock{nullptr};

inline std::atomic<bool> g_active{false};
inline std::atomic<const char *> g_what{""};

// Breadcrumbs. STATIC STRINGS ONLY -- the pointer is stored, not the text.
inline std::atomic<const char *> g_mark{""};  // last firmware/host step
inline std::atomic<uint64_t> g_markMs{0};
inline std::atomic<const char *> g_mainStage{"idle"};  // main-loop stage
inline std::atomic<uint64_t> g_mainStageMs{0};
inline std::atomic<uint64_t> g_mainTickMs{0};   // last main-loop iteration
inline std::atomic<uint64_t> g_presentMs{0};    // last present of a NEW frame
inline std::atomic<uint32_t> g_presents{0};     // NEW-frame presents since begin()
inline std::atomic<uint32_t> g_repeats{0};      // same-frame presents since begin()
// The host's framebuffer generation (HalDisplay's pixelBufSeq): bumped where a
// firmware frame is written for presenting, and the generation last presented.
// A present only counts as the glass MOVING when it carries a newer frame -- the
// phosphor trail and the beam sweep re-present the SAME picture every display
// frame on a dark page, and counting those hid exactly the freeze this hunts
// (adversarial review, 2026-09-26).
inline std::atomic<uint64_t> g_frameSeq{0};
inline std::atomic<uint64_t> g_frameMs{0};
inline std::atomic<uint64_t> g_presentedSeq{0};
inline std::atomic<uint64_t> g_renderMs{0};     // last firmware render
inline std::atomic<uint64_t> g_requestMs{0};    // last repaint request
inline std::atomic<uint64_t> g_workingMs{0};    // last loop tick mid-run
inline std::atomic<const char *> g_declined{""}; // last owed-but-declined why
inline std::atomic<uint64_t> g_declinedMs{0};
inline std::atomic<uint32_t> g_declines{0};

inline bool active() { return g_active.load(std::memory_order_relaxed); }

inline uint64_t now() {
  const Clock c = g_clock.load(std::memory_order_relaxed);
  return c ? c() : 0;
}

inline void logf(const char *fmt, ...) {
  const Sink s = g_sink.load(std::memory_order_relaxed);
  if (!s) return;
  char body[256];
  va_list ap;
  va_start(ap, fmt);
  vsnprintf(body, sizeof(body), fmt, ap);
  va_end(ap);
  char line[300];
  snprintf(line, sizeof(line), "[updtrace] %llu ms %s",
           static_cast<unsigned long long>(now()), body);
  s(line);
}

// The firmware's update screen opened / closed.
inline void begin(const char *what) {
  const uint64_t t = now();
  g_what.store(what);
  g_presents.store(0);
  g_repeats.store(0);
  g_declines.store(0);
  g_declined.store("");
  g_frameMs.store(0);
  g_presentedSeq.store(g_frameSeq.load());
  g_presentMs.store(t);
  g_mainTickMs.store(t);
  g_renderMs.store(0);
  g_requestMs.store(t);
  g_workingMs.store(0);
  g_mark.store("begin");
  g_markMs.store(t);
  g_active.store(true);
  logf("BEGIN %s", what);
}
inline void end() {
  if (!g_active.exchange(false)) return;
  logf("END %s: %u new-frame presents, %u repeats, %u runs of declines",
       g_what.load(), g_presents.load(), g_repeats.load(), g_declines.load());
}

// A step boundary. `what` must be a string literal; `detail` is copied into
// the line and may be anything (a family name, a byte count).
inline void mark(const char *what, const char *detail = nullptr) {
  if (!active()) return;
  g_mark.store(what);
  g_markMs.store(now());
  if (detail)
    logf("mark %s (%s)", what, detail);
  else
    logf("mark %s", what);
}

// The firmware drew a frame (its render() ran) / asked for one / ran a loop
// tick while the run is still working (CHECKING or SYNCING). These three are
// what let the watchdog tell "the glass is not showing frames the firmware
// drew" from "the firmware stopped drawing" -- and stay quiet on a finished
// run's summary screen, which legitimately never repaints.
inline void rendered() {
  if (!active()) return;
  g_renderMs.store(now(), std::memory_order_relaxed);
  g_mark.store("render");
  g_markMs.store(now());
}
inline void requested() {
  if (!active()) return;
  g_requestMs.store(now(), std::memory_order_relaxed);
}
inline void working() {
  if (!active()) return;
  g_workingMs.store(now(), std::memory_order_relaxed);
}

// Main loop: where it is. Cheap enough to call every iteration.
inline void mainStage(const char *stage) {
  if (!active()) return;
  const uint64_t t = now();
  g_mainStage.store(stage, std::memory_order_relaxed);
  g_mainStageMs.store(t, std::memory_order_relaxed);
  g_mainTickMs.store(t, std::memory_order_relaxed);
}

// The host wrote framebuffer generation `seq` for presenting.
inline void frameWritten(uint64_t seq) {
  g_frameSeq.store(seq, std::memory_order_relaxed);
  if (!active()) return;
  g_frameMs.store(now(), std::memory_order_relaxed);
}

// presentIfNeeded reached the GPU. Logged one line per NEW frame (a handful a
// second at most on these screens); a present of the same frame -- a trail or
// beam step -- is only counted, or a dark page would log at display rate.
// `onGlass` is the generation the presented texture actually holds (the
// host's uploadedSeq), which is not always the newest written: E-Ink Mode
// holds its own flash frame, for one.
inline void presented(uint64_t onGlass) {
  if (!active()) return;
  const uint64_t seq = onGlass;
  if (g_presentedSeq.exchange(seq) == seq) {
    g_repeats.fetch_add(1, std::memory_order_relaxed);
    return;
  }
  const uint64_t t = now();
  const uint64_t gap = t - g_presentMs.exchange(t);
  const uint32_t n = g_presents.fetch_add(1) + 1;
  g_declined.store("");  // a later decline is a new run of them: log it again
  logf("present #%u frame %llu gap %llu ms (%u repeats so far)", n,
       static_cast<unsigned long long>(seq), static_cast<unsigned long long>(gap),
       g_repeats.load());
}

// presentIfNeeded had a present owed and returned without it. Logged and
// counted once per RUN of declines for one reason (the hold alone declines
// ~30 main-loop passes per frame); a new-frame present ends the run.
inline void declined(const char *why) {
  if (!active()) return;
  if (g_declined.exchange(why) != why) {
    g_declines.fetch_add(1, std::memory_order_relaxed);
    // The coalescing hold declines ~30 ms on EVERY antialiased frame by design;
    // a line per frame is noise. It is still recorded, and a STALL line names
    // it when it is the last thing that held the glass.
    if (std::strcmp(why, "coalescing hold") != 0) logf("present declined: %s", why);
  }
  g_declinedMs.store(now(), std::memory_order_relaxed);
}

// What the watchdog should say at `t`, if anything. Pure over the state above
// so a host test can drive it; `reported*` carry "already said it for this
// stall" between calls so one stall is one line, not four a second.
struct Verdict {
  bool mainStalled = false;   // the main loop has not iterated
  bool glassStalled = false;  // a drawn frame, or a working run, not on glass
  bool quiet = false;         // a working run that asks for no repaint
  uint64_t mainMs = 0;
  uint64_t glassMs = 0;
  uint64_t quietMs = 0;
};
struct Inputs {
  uint64_t t = 0, mainTick = 0, presentAt = 0, renderAt = 0, workingAt = 0,
           requestAt = 0;
  // A frame written for presenting (its time) and whether it is still not on
  // the glass (its generation is newer than the last one presented).
  uint64_t frameAt = 0;
  bool frameUnpresented = false;
};
struct Reported {
  bool main = false, glass = false, quiet = false;
};
inline uint64_t since(uint64_t t, uint64_t at) { return t > at ? t - at : 0; }
inline Verdict evaluate(const Inputs &in, Reported &r) {
  Verdict v;
  v.mainMs = since(in.t, in.mainTick);
  v.glassMs = since(in.t, in.presentAt);
  v.quietMs = since(in.t, in.requestAt);
  // Working = a CHECKING/SYNCING loop tick within kWorkingFreshMs. A working
  // run ticks every few ms, so this is tight on purpose: a window as wide as
  // kStallMs read a run that had JUST finished as still working and reported
  // its (legitimately still) summary screen as a stall -- measured on the iOS
  // Simulator, 1.3 s after "font sync done".
  const bool working = in.workingAt != 0 && since(in.t, in.workingAt) < kWorkingFreshMs;
  // A frame the host WROTE for presenting that has not reached the glass --
  // keyed on the framebuffer generation, not on render start or on any
  // present, so a trail re-presenting the old picture cannot hide it.
  const bool frameOwed = in.frameUnpresented && in.frameAt != 0 && since(in.t, in.frameAt) >= kStallMs;
  auto edge = [](bool cond, bool &said) {
    if (!cond) {
      said = false;
      return false;
    }
    if (said) return false;
    return said = true;
  };
  v.mainStalled = edge(v.mainMs >= kStallMs, r.main);
  v.glassStalled = edge(frameOwed || (working && v.glassMs >= kStallMs), r.glass);
  v.quiet = edge(working && v.quietMs >= kStallMs, r.quiet);
  return v;
}

// One watchdog pass (the host calls this from its own thread every ~250 ms).
inline void watch() {
  static Reported reported;
  if (!active()) {
    reported = Reported{};
    return;
  }
  Inputs in;
  in.t = now();
  in.mainTick = g_mainTickMs.load();
  in.presentAt = g_presentMs.load();
  in.renderAt = g_renderMs.load();
  in.workingAt = g_workingMs.load();
  in.requestAt = g_requestMs.load();
  in.frameAt = g_frameMs.load();
  in.frameUnpresented = g_frameSeq.load() != g_presentedSeq.load();
  const Verdict v = evaluate(in, reported);
  if (v.mainStalled)
    logf("STALL main loop silent %llu ms, parked in '%s' since %llu ms; "
         "last step '%s' at %llu ms",
         static_cast<unsigned long long>(v.mainMs), g_mainStage.load(),
         static_cast<unsigned long long>(g_mainStageMs.load()), g_mark.load(),
         static_cast<unsigned long long>(g_markMs.load()));
  if (v.glassStalled)
    logf("STALL no new frame on the glass for %llu ms (frame %llu written at "
         "%llu ms %s; last render %llu ms; %u repeats); main loop last ran %llu "
         "ms ago in '%s'; last decline '%s' at %llu ms; last step '%s' at %llu ms",
         static_cast<unsigned long long>(v.glassMs),
         static_cast<unsigned long long>(g_frameSeq.load()),
         static_cast<unsigned long long>(in.frameAt),
         in.frameUnpresented ? "and NOT presented" : "and presented",
         static_cast<unsigned long long>(in.renderAt), g_repeats.load(),
         static_cast<unsigned long long>(v.mainMs), g_mainStage.load(),
         g_declined.load(),
         static_cast<unsigned long long>(g_declinedMs.load()), g_mark.load(),
         static_cast<unsigned long long>(g_markMs.load()));
  if (v.quiet)
    logf("STALL the run is working but asked for no repaint in %llu ms; last "
         "step '%s' at %llu ms",
         static_cast<unsigned long long>(v.quietMs), g_mark.load(),
         static_cast<unsigned long long>(g_markMs.load()));
}

}  // namespace sim_update_trace
