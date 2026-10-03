// src/SimulatorIdle.h: the main thread's sleeps pump presents.
//
// Every failure mode here is silent -- a pump that never runs leaves every
// animation at the firmware's 13 fps idle cadence with nothing in any log,
// a pump that runs on the render task touches SDL off the main thread, and
// a pump that recurses through its own delay() is a stack overflow on the
// first idle pass. So: the pump runs on the installing thread during a
// sleep, about once a millisecond; it never runs on another thread; a pump
// that itself sleeps does not recurse; the sleep still lasts its full time;
// and with nothing installed the sleep is the plain one.
#include <chrono>
#include <cstdio>
#include <thread>

#include "SimulatorIdle.h"

static int failures = 0;
static void check(bool ok, const char *what) {
  std::printf("%s: %s\n", ok ? "ok" : "FAIL", what);
  if (!ok) failures++;
}

static int g_pumps = 0;
static int g_nestedDepth = 0, g_maxDepth = 0;
static void countingPump() { g_pumps++; }
static void sleepingPump() {
  g_nestedDepth++;
  if (g_nestedDepth > g_maxDepth) g_maxDepth = g_nestedDepth;
  simidle::sleepMs(2);  // a pump that delays must not pump again
  g_nestedDepth--;
}

int main() {
  using clock = std::chrono::steady_clock;
  // Nothing installed: a plain sleep of the full length, no pump.
  {
    g_pumps = 0;
    const auto t0 = clock::now();
    simidle::sleepMs(20);
    const auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(clock::now() - t0).count();
    check(ms >= 20 && g_pumps == 0, "uninstalled: the plain sleep, full length, no pump");
  }
  simidle::install(countingPump);
  // Installed, on the installing thread: pumped about once a millisecond,
  // and the sleep still lasts its full time.
  {
    g_pumps = 0;
    const auto t0 = clock::now();
    simidle::sleepMs(30);
    const auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(clock::now() - t0).count();
    check(ms >= 30, "installed: delay(30) still returns no sooner than 30 ms later");
    check(g_pumps >= 10 && g_pumps <= 40, "installed: pumped about once a millisecond (10..40 in 30 ms)");
    check(simidle::lastPumpCount() == static_cast<unsigned long>(g_pumps), "installed: lastPumpCount reports the run");
  }
  // On another thread: never pumped (that thread may not touch SDL).
  {
    g_pumps = 0;
    std::thread t([] { simidle::sleepMs(15); });
    t.join();
    check(g_pumps == 0, "render task: a sleep on another thread pumps nothing");
  }
  // A pump that sleeps does not recurse into pumping.
  {
    simidle::install(sleepingPump);
    g_nestedDepth = g_maxDepth = 0;
    simidle::sleepMs(10);
    check(g_maxDepth == 1, "nested: a pump that delays falls through to the plain sleep");
    simidle::install(countingPump);
  }
  // delay(0) and delay(1): return promptly, pump at least once.
  {
    g_pumps = 0;
    const auto t0 = clock::now();
    simidle::sleepMs(0);
    simidle::sleepMs(1);
    const auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(clock::now() - t0).count();
    check(g_pumps >= 2 && ms < 50, "short delays: pump at least once each, return promptly");
  }
  simidle::uninstall();
  if (failures == 0) std::printf("simulator_idle: all passed\n");
  return failures == 0 ? 0 : 1;
}
