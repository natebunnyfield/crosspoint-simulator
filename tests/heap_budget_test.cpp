// S-001: the budgeted heap.
//
// ESP.getFreeHeap() reported a flat 1 MB, so every low-memory branch in the
// firmware — the background page build, the plane buffer, retaining a mini
// font, image decode, the JPEG path, the CSS parser — was unreachable in the
// only pre-device gate the project has.
//
// The config is read once per process from the environment, so each mode needs
// its own process: main() re-execs itself with the env set and one mode name.

#include "SimulatorHeap.h"

#include <cassert>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>

namespace {

constexpr uint32_t kFlat = 1024u * 1024u;

int runDefault() {
  // The whole point of opt-in: an existing headless run must see exactly what
  // it saw before.
  assert(!simheap::budgetEnabled());
  assert(simheap::freeBytes() == kFlat);
  assert(simheap::totalBytes() == kFlat);
  assert(simheap::maxAllocBytes() == kFlat);
  // Allocating must not move it, or every existing screenshot script starts
  // reporting a different heap than it used to.
  auto *waste = new std::vector<char>(200000, 'x');
  assert(simheap::freeBytes() == kFlat && "default mode must ignore allocations");
  delete waste;
  return 0;
}

int runPinned() {
  assert(simheap::budgetEnabled());
  assert(simheap::freeBytes() == 40000);
  assert(simheap::maxAllocBytes() == 40000);
  auto *waste = new std::vector<char>(200000, 'x');
  assert(simheap::freeBytes() == 40000 && "a pin does not move under allocation");
  delete waste;
  // A pinned value is what a test asserting "the CSS parser refuses below
  // 48 KB" would use: it is under the threshold and it stays there.
  assert(simheap::freeBytes() < 48u * 1024u);
  return 0;
}

int runBudget() {
  assert(simheap::budgetEnabled());
  assert(simheap::totalBytes() == 380000);
  const uint32_t before = simheap::freeBytes();
  assert(before > 0 && before <= 380000);

  // THE PROPERTY THAT MATTERS: it falls under pressure.
  auto *block = new std::vector<char>(120000, 'x');
  const uint32_t during = simheap::freeBytes();
  assert(during < before && "the budget must shrink as the firmware allocates");
  assert(before - during >= 100000 && "a 120 KB allocation should cost roughly that");

  delete block;

  // Give-back is asserted through the SIZED operator delete directly, not by
  // deleting the vector above. Only the sized form can know how much to return,
  // and which form the standard library reaches for is its business, not a
  // property this budget should depend on -- measured here, libc++ frees that
  // vector without going through it. So the budget falls reliably and recovers
  // only for allocations whose size is handed back. That asymmetry is the
  // honest behaviour and is documented in SimulatorHeap.cpp; a budget that only
  // ever falls is still a usable pressure signal, and pinning is the answer
  // when a test needs an exact number.
  const uint32_t beforeExplicit = simheap::freeBytes();
  void *raw = ::operator new(64000);
  const uint32_t withRaw = simheap::freeBytes();
  assert(withRaw < beforeExplicit && "an explicit new must cost the budget");
  ::operator delete(raw, 64000);
  const uint32_t after = simheap::freeBytes();
  assert(after > withRaw && "a sized delete must give the budget back");

  // The low-water mark remembers the worst moment, which is what a "did we ever
  // get close?" question is really asking.
  assert(simheap::minFreeBytes() <= during);

  // A reboot starts the budget over; the in-process reboot keeps every static,
  // so without the reset a rebooted run begins already spent.
  simheap::resetForReboot();
  assert(simheap::freeBytes() > after && "resetForReboot must return the whole budget");
  return 0;
}

}  // namespace

int main(int argc, char **argv) {
  if (argc > 1) {
    const std::string mode = argv[1];
    if (mode == "default") return runDefault();
    if (mode == "pinned") return runPinned();
    if (mode == "budget") return runBudget();
    std::fprintf(stderr, "unknown mode %s\n", mode.c_str());
    return 2;
  }

  const std::string self = argv[0];
  struct Case {
    const char *env;
    const char *mode;
  };
  const Case cases[] = {
      {"", "default"},
      {"CROSSPOINT_SIM_HEAP_FREE=40000", "pinned"},
      {"CROSSPOINT_SIM_HEAP=380000", "budget"},
  };
  for (const Case &c : cases) {
    const std::string cmd = std::string(c.env) + (c.env[0] ? " " : "") + self + " " + c.mode;
    if (std::system(cmd.c_str()) != 0) {
      std::fprintf(stderr, "heap_budget: %s mode FAILED\n", c.mode);
      return 1;
    }
  }
  std::puts("heap_budget: PASS");
  return 0;
}
