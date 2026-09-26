// src/SimUpdateTrace.h -- the update screens' flight recorder.
//
// It exists because Update Fonts / Update Library were reported frozen on the
// owner's phone twice and the second report could not be reproduced on the
// iOS Simulator (S-042). Its only job is to make the NEXT report carry the
// answer, so what this pins is that the lines it promises are actually
// written, and written once:
//   * a stall produces exactly ONE STALL line per stall, naming the main
//     loop's stage and the last step -- a stall that logged every 250 ms would
//     rotate the 256 KB log over its own beginning in minutes;
//   * a present logs its gap; an owed present that was declined logs WHY, once
//     per run of declines;
//   * the iOS HTTP branch (CROSSPOINT_SIM_HOST_HTTP=1, the phone's transport)
//     reports each fetch's start and duration -- compiled with that define so
//     the phone's branch is the one exercised, the same escape hatch as
//     http_dispatch_test;
//   * inactive, nothing is written at all.
//
//   c++ -std=c++20 -Isrc -DCROSSPOINT_SIM_HOST_HTTP=1 tests/update_trace_test.cpp

#include <cstdio>
#include <string>
#include <vector>

#include "SimHttpFetch.h"
#include "SimUpdateTrace.h"

#if !CROSSPOINT_SIM_HOST_HTTP
#error "build with -DCROSSPOINT_SIM_HOST_HTTP=1; see the header comment"
#endif

namespace {
std::vector<std::string> g_lines;
uint64_t g_now = 1000;
int g_failures = 0;
int g_hostFetches = 0;
uint64_t g_seq = 0;

void check(bool ok, const char *what) {
  if (!ok) {
    std::printf("FAIL: %s\n", what);
    for (const auto &l : g_lines) std::printf("    %s\n", l.c_str());
    g_failures++;
  }
}
int count(const char *needle) {
  int n = 0;
  for (const auto &l : g_lines)
    if (l.find(needle) != std::string::npos) n++;
  return n;
}
}  // namespace

// The phone's transport, substituted: takes 700 ms of fake time.
namespace sim_http_fetch {
bool hostFetch(const std::string &, const char *, const std::map<std::string, std::string> &,
               const std::string &, const char *, Response &out) {
  g_hostFetches++;
  g_now += 700;
  out.statusCode = 200;
  out.body = "12345";
  return true;
}
}  // namespace sim_http_fetch

int main() {
  namespace t = sim_update_trace;
  t::g_sink.store(+[](const char *line) { g_lines.emplace_back(line); });
  t::g_clock.store(+[]() -> uint64_t { return g_now; });

  // Inactive: silent, and the fetch still goes to the transport.
  t::mark("nothing");
  t::presented(g_seq);
  t::declined("backgrounded");
  t::mainStage("loop()");
  t::watch();
  sim_http_fetch::Response r;
  sim_http_fetch::fetch("https://example.invalid/a", "GET", {}, "", nullptr, r);
  check(g_lines.empty(), "an inactive trace writes nothing");
  check(g_hostFetches == 1, "an inactive trace still fetches");

  t::begin("FontUpdateActivity");
  check(count("BEGIN FontUpdateActivity") == 1, "begin is logged");

  // A healthy main loop and glass: no STALL line.
  for (int i = 0; i < 8; i++) {
    g_now += 250;
    t::mainStage("loop()");
    t::working();
    if (i % 3 == 0) {
      t::requested();
      t::rendered();
      t::frameWritten(++g_seq);
      t::presented(g_seq);
    }
    t::presented(g_seq);  // a trail re-present of the same frame: counted, not logged
    t::watch();
  }
  check(count("STALL") == 0, "a healthy loop reports no stall");
  check(count("present #") == 3, "each present is logged");

  // The iOS transport, while active: start (without the query) and duration.
  sim_http_fetch::fetch("https://api.github.com/x?token=SECRET", "GET", {}, "", nullptr, r);
  check(count("mark host fetch (https://api.github.com/x)") == 1, "fetch start names the URL");
  check(count("SECRET") == 0, "the query string never reaches the log");
  check(count("host fetch done in 700 ms: ok=1 status=200 curl=0 bytes=5") == 1,
        "fetch end carries duration, status and size");

  // The main loop parks in presentIfNeeded for 5 s: ONE main-loop STALL line
  // naming it, however many watchdog passes see it.
  t::mainStage("presentIfNeeded");
  t::frameWritten(++g_seq);
  t::presented(g_seq);
  g_now += 10;
  t::requested();
  t::rendered();
  t::frameWritten(++g_seq);  // written, never presented: the glass owes this frame
  for (int i = 0; i < 20; i++) {
    g_now += 250;
    t::watch();
  }
  check(count("STALL main loop silent") == 1, "one stall is one main-loop STALL line");
  check(count("parked in 'presentIfNeeded'") >= 1, "the stall names the main-loop stage");
  check(count("last step 'render'") >= 1, "the stall names the last step");
  check(count("STALL no new frame") == 1, "the glass stall is reported once too");

  // It recovers, then stalls again: a second line.
  t::mainStage("loop()");
  t::presented(g_seq);  // presents the owed frame
  t::watch();
  for (int i = 0; i < 8; i++) {
    g_now += 250;
    t::watch();
  }
  check(count("STALL main loop silent") == 2, "a second stall is a second line");

  // A FINISHED run: the loop ticks, nothing is working, nothing is drawn. The
  // summary screen legitimately never repaints, and must not read as a stall.
  const int glassBefore = count("STALL no new frame");
  for (int i = 0; i < 20; i++) {
    g_now += 250;
    t::mainStage("loop()");
    t::watch();
  }
  check(count("STALL no new frame") == glassBefore, "a finished run's still screen is not a stall");

  // A run that JUST finished: its last working tick 50 ms ago, its last
  // repaint request 1.4 s ago. The next watchdog pass must not call it quiet
  // (measured false positive on the iOS Simulator, 2026-09-26).
  g_now += 250;
  t::working();
  t::requested();
  g_now += 1400;
  t::working();
  g_now += 350;
  t::watch();
  check(count("asked for no repaint") == 0, "a run that just finished is not reported as quiet");

  // A WORKING run whose firmware stops asking for frames: its own line.
  for (int i = 0; i < 12; i++) {
    g_now += 250;
    t::mainStage("loop()");
    t::working();
    t::watch();
  }
  check(count("asked for no repaint") == 1, "a working run that stops repainting is reported once");

  // THE REVIEW'S CASE: a dark page's trail re-presents the OLD frame every
  // display frame while a NEW frame, written, never reaches the glass. Every
  // present below is a repeat; the glass must still be reported stalled.
  {
    const int before = count("STALL no new frame");
    t::frameWritten(++g_seq);
    for (int i = 0; i < 40; i++) {
      g_now += 50;
      t::mainStage("loop()");
      t::presented(g_seq - 1);  // the OLD frame, re-presented by the trail
      t::watch();
    }
    check(count("STALL no new frame") == before + 1,
          "a new frame hidden behind same-frame re-presents is reported");
    check(count("NOT presented") >= 1, "the stall says the written frame was not presented");
    t::presented(g_seq);
  }

  // Owed presents declined: the reason once per run of declines.
  const size_t before = g_lines.size();
  for (int i = 0; i < 50; i++) t::declined("backgrounded");
  check(g_lines.size() == before + 1, "a run of declines logs its reason once");
  t::frameWritten(++g_seq);
  t::presented(g_seq);
  t::declined("backgrounded");
  check(count("present declined: backgrounded") == 2, "a new-frame present ends the run: the next decline is logged");
  t::declined("coalescing hold");
  check(count("present declined: coalescing hold") == 1, "a new reason is logged");

  t::end();
  check(count("END FontUpdateActivity") == 1, "end is logged");
  const size_t atEnd = g_lines.size();
  t::end();
  g_now += 5000;
  t::watch();
  check(g_lines.size() == atEnd, "after end, nothing more is written");

  if (g_failures == 0) std::printf("update_trace: all checks passed\n");
  return g_failures == 0 ? 0 : 1;
}
