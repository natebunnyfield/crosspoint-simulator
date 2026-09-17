// sim_host_battery: the resolution order, the three-state answers, and the
// plug/unplug edge.
//
// Why this is worth a test. Every failure mode here is a WRONG PICTURE that
// still renders: a phone that shows 100 % forever, a charging bolt that never
// goes out, a desktop screenshot whose battery quietly stops matching the one
// it was captured with. None of them fails a build and none of them throws.
// The iOS backend itself cannot be compiled anywhere but a Mac and needs a
// real device to answer at all, so the part that can be pinned is the decision
// -- which reading wins, and what "unknown" does.
//
// The env-var arms matter as much as the published ones: the desktop canary and
// every headless capture in this repo go down that path, and the contract is
// that a build which never publishes behaves exactly as it did before the
// channel existed.

#include "SimHostBattery.h"

#include <cstdio>
#include <cstdlib>
#include <string>

static int failures = 0;

static void check(bool ok, const std::string &what) {
  if (!ok) {
    std::printf("FAIL: %s\n", what.c_str());
    ++failures;
  }
}

static void checkEq(int got, int want, const std::string &what) {
  if (got != want) {
    std::printf("FAIL: %s -- got %d, want %d\n", what.c_str(), got, want);
    ++failures;
  }
}

// Nothing published: back to the pre-channel behaviour.
static void clearPublished() { sim_host_battery::publish(-1, -1); sim_host_battery::consumeUsbEdge(); }

int main() {
  // ---------------------------------------------------------------- defaults
  unsetenv(sim_host_battery::kPercentEnvVar);
  unsetenv(sim_host_battery::kUsbEnvVar);
  clearPublished();
  checkEq(sim_host_battery::percent(), -1, "no publish means no host reading");
  checkEq(sim_host_battery::charging(), -1, "no publish means no host charging state");
  checkEq(sim_host_battery::resolvedPercent(), 100, "bare default is the historical 100");
  check(sim_host_battery::resolvedUsbConnected(), "bare default is the historical connected");

  // ------------------------------------------------------------- the env vars
  setenv(sim_host_battery::kPercentEnvVar, "37", 1);
  checkEq(sim_host_battery::resolvedPercent(), 37, "CROSSPOINT_SIM_BATTERY is honoured");
  setenv(sim_host_battery::kPercentEnvVar, "-5", 1);
  checkEq(sim_host_battery::resolvedPercent(), 0, "a negative env value clamps to 0");
  setenv(sim_host_battery::kPercentEnvVar, "250", 1);
  checkEq(sim_host_battery::resolvedPercent(), 100, "an over-100 env value clamps to 100");
  // Read every call, not latched. The old code cached this in a function-local
  // static, which was invisible on the desktop and froze the first reading on
  // a phone -- exactly the bug this channel exists to fix.
  setenv(sim_host_battery::kPercentEnvVar, "12", 1);
  checkEq(sim_host_battery::resolvedPercent(), 12, "the env var is re-read, not latched");

  setenv(sim_host_battery::kUsbEnvVar, "0", 1);
  check(!sim_host_battery::resolvedUsbConnected(), "CROSSPOINT_SIM_USB=0 is unplugged");
  setenv(sim_host_battery::kUsbEnvVar, "1", 1);
  check(sim_host_battery::resolvedUsbConnected(), "any other value is connected");
  setenv(sim_host_battery::kUsbEnvVar, "00", 1);
  check(sim_host_battery::resolvedUsbConnected(), "only the exact string \"0\" unplugs");

  // -------------------------------------------------- a host reading wins
  sim_host_battery::publish(63, 0);
  checkEq(sim_host_battery::resolvedPercent(), 63, "a published level beats the env var");
  check(!sim_host_battery::resolvedUsbConnected(), "a published state beats the env var");

  // 0 % is a REAL level, and the one most likely to be confused with "unknown".
  sim_host_battery::publish(0, 0);
  checkEq(sim_host_battery::resolvedPercent(), 0, "0 % publishes as 0, not as unknown");
  sim_host_battery::publish(100, 1);
  checkEq(sim_host_battery::resolvedPercent(), 100, "100 % publishes as 100");

  // Out of range is unknown, and unknown falls back rather than rendering a lie.
  // This is the iOS Simulator's own answer: batteryLevel -1, state Unknown.
  sim_host_battery::publish(-1, -1);
  checkEq(sim_host_battery::resolvedPercent(), 12, "an unknown level falls back to the env var");
  check(sim_host_battery::resolvedUsbConnected(), "an unknown state falls back to the env var");
  sim_host_battery::publish(101, 1);
  checkEq(sim_host_battery::resolvedPercent(), 12, "an over-range level is unknown, not clamped");

  // ------------------------------------------------------------- the USB edge
  clearPublished();
  check(!sim_host_battery::consumeUsbEdge(), "no edge before anything is published");
  // The FIRST reading is not an edge: -1 -> 1 at launch is the adapter starting
  // up, not a cable going in, and raising it there would repaint every boot.
  sim_host_battery::publish(50, 1);
  check(!sim_host_battery::consumeUsbEdge(), "the first reading raises no edge");
  // A level change with the same state is not an edge either.
  sim_host_battery::publish(49, 1);
  check(!sim_host_battery::consumeUsbEdge(), "a level change alone raises no edge");
  // Unplugged.
  sim_host_battery::publish(49, 0);
  check(sim_host_battery::consumeUsbEdge(), "unplugging raises an edge");
  check(!sim_host_battery::consumeUsbEdge(), "the edge is consumed, not sticky");
  // Plugged back in.
  sim_host_battery::publish(49, 1);
  check(sim_host_battery::consumeUsbEdge(), "plugging in raises an edge");
  // Going UNKNOWN is not an edge: the app backgrounding and the reading going
  // stale must not queue a repaint.
  sim_host_battery::publish(49, -1);
  check(!sim_host_battery::consumeUsbEdge(), "losing the reading raises no edge");
  sim_host_battery::publish(49, 1);
  check(!sim_host_battery::consumeUsbEdge(), "regaining the reading raises no edge");

  if (failures == 0) std::printf("host_battery: all checks pass\n");
  return failures == 0 ? 0 : 1;
}
