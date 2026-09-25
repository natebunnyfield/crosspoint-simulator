#pragma once

// THE READING SPEEDRUN -- a spike. Owner 2026-09-24: "spike a speed running
// demo". Read as a speedrunner's timer laid over reading: the run is your time
// in this book this session, each PAGE is a split, and every split is compared
// with your best-ever time on that same page (the "gold split"), so the HUD
// says whether you are ahead of or behind yourself, page by page and in total
// -- LiveSplit's vocabulary applied to a book.
//
// A SPIKE: desktop-only switch (CROSSPOINT_SIM_SPEEDRUN=1), drawn with SDL3's
// built-in debug font, bests kept in a small text file. Everything that decides
// a number is here, pure, so tests/speedrun_test.cpp can drive it; the drawing
// is a few lines in src/HalDisplay.cpp. docs/speedrun-spike.md is the account.

#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <map>
#include <sstream>
#include <string>
#include <tuple>

namespace speedrun {

// A page shorter than this was flipped past, not read, and would set an
// unbeatable "best" -- so it neither counts as a split nor as a record.
inline constexpr double kMinSplitSeconds = 1.0;
// One pass may add at most this much (a stall or a suspension is not reading).
inline constexpr double kMaxStepSeconds = 1.0;

struct PageKey {
  uint64_t book = 0;
  int spine = 0;
  int page = 0;
  bool operator<(const PageKey &o) const {
    return std::tie(book, spine, page) < std::tie(o.book, o.spine, o.page);
  }
  bool operator==(const PageKey &o) const {
    return book == o.book && spine == o.spine && page == o.page;
  }
};

struct Run {
  std::map<PageKey, double> best;  // gold splits, persisted
  bool active = false;             // a page is being timed
  PageKey page;
  double pageSecs = 0.0;           // time on the current page
  double runSecs = 0.0;            // time in this book this session
  double runDelta = 0.0;           // sum over completed splits of (time - best)
  int splits = 0;                  // completed splits this run
  int golds = 0;                   // splits that set a new best this run
  bool bestsChanged = false;       // the caller should persist

  // One main-loop pass. `onPage` says a book page is up (with its key);
  // `reading` says this moment counts.
  void step(bool onPage, const PageKey &key, bool reading, double dt) {
    if (!(dt > 0.0)) dt = 0.0;
    if (dt > kMaxStepSeconds) dt = kMaxStepSeconds;
    if (!onPage) return;  // a menu pauses the run; it does not end it
    if (!active || !(key == page)) {
      if (active) finishSplit();
      if (!active || key.book != page.book) {  // a new book is a new run
        runSecs = 0.0; runDelta = 0.0; splits = 0; golds = 0;
      }
      page = key; pageSecs = 0.0; active = true;
    }
    if (reading) { pageSecs += dt; runSecs += dt; }
  }

  void finishSplit() {
    if (pageSecs < kMinSplitSeconds) return;
    const auto it = best.find(page);
    if (it != best.end()) runDelta += pageSecs - it->second;
    if (it == best.end() || pageSecs < it->second) {
      if (it != best.end()) golds++;
      best[page] = pageSecs;
      bestsChanged = true;
    }
    splits++;
  }

  // The live comparison for the page on screen, if it has a best: negative is
  // ahead. NAN when there is nothing to compare against.
  double pageDelta() const {
    const auto it = best.find(page);
    return it == best.end() ? NAN : pageSecs - it->second;
  }

  std::string serialize() const {
    std::ostringstream o;
    char line[96];
    for (const auto &kv : best) {
      std::snprintf(line, sizeof line, "%016llx %d %d %.2f\n",
                    static_cast<unsigned long long>(kv.first.book), kv.first.spine,
                    kv.first.page, kv.second);
      o << line;
    }
    return o.str();
  }
  void parse(const std::string &text) {
    std::istringstream in(text);
    std::string l;
    while (std::getline(in, l)) {
      unsigned long long b = 0; int s = 0, p = 0; double t = 0;
      if (std::sscanf(l.c_str(), "%llx %d %d %lf", &b, &s, &p, &t) == 4 && t >= kMinSplitSeconds)
        best[{static_cast<uint64_t>(b), s, p}] = t;
    }
  }
};

// "MM:SS" for a run, "SS.s" for a split, "+1.2" / "-0.4" for a delta.
inline std::string clock(double s) {
  if (!(s >= 0)) s = 0;
  const int t = static_cast<int>(s);
  char b[16];
  std::snprintf(b, sizeof b, "%02d:%02d", t / 60, t % 60);
  return b;
}
inline std::string delta(double d) {
  if (std::isnan(d)) return "";
  d = std::round(d * 10.0) / 10.0;
  if (d == 0.0) d = 0.0;  // no "-0.0": a tie is a tie
  char b[16];
  std::snprintf(b, sizeof b, "%+.1f", d);
  return b;
}

}  // namespace speedrun
