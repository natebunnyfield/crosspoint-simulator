// src/SimKeepAwake.h -- the Update Fonts / Update Library keep-awake lease.
//
// Owner ruling 2026-09-26 (S-042): hold the phone's idle timer off for the
// length of a run and give the owner's own value back on EVERY way out. What
// can go wrong is silent both ways -- a lease never released leaves the phone
// never locking (a battery drain nobody traces to an update screen), a lease
// released to the wrong value flips the owner's own setting -- so each exit
// path is driven here against both starting values of the idle timer.
//
// The host loop is modelled exactly as simulator_main applies it: the firmware
// only writes the wanted flag, one main-loop pass steps the lease with the
// idle timer's live value and writes what the lease says.
//
//   c++ -std=c++20 -Isrc tests/keep_awake_test.cpp

#include <cstdio>
#include <string>

#include "SimKeepAwake.h"

namespace {
int g_failures = 0;
void check(bool ok, const std::string &what) {
  if (!ok) {
    std::printf("FAIL: %s\n", what.c_str());
    g_failures++;
  }
}

// The phone: its idle timer and the host main loop that owns it.
struct Host {
  bool idleTimerDisabled = false;
  sim_keep_awake::Lease lease;
  int sets = 0, restores = 0, reasserts = 0;
  void pass() {
    switch (lease.step(sim_keep_awake::g_wanted.load(), sim_keep_awake::g_foreground.load(),
                       idleTimerDisabled)) {
      case sim_keep_awake::Action::Set:
        idleTimerDisabled = true;
        sets++;
        break;
      case sim_keep_awake::Action::Reassert:
        idleTimerDisabled = true;
        reasserts++;
        break;
      case sim_keep_awake::Action::Restore:
        idleTimerDisabled = lease.previous;
        restores++;
        break;
      case sim_keep_awake::Action::None:
        break;
    }
  }
};

// The firmware side, as the activities do it: true on entering CHECKING, then
// every loop tick "is the run working", false in onExit.
enum class Exit { Done, Failed, Stopped, Back, Sleep, HomeGesture, Reboot };
const char *name(Exit e) {
  switch (e) {
    case Exit::Done: return "done";
    case Exit::Failed: return "failed";
    case Exit::Stopped: return "stopped (Back between items)";
    case Exit::Back: return "Back mid-run / activity destroyed";
    case Exit::Sleep: return "power / sleep mid-run";
    case Exit::HomeGesture: return "home gesture";
    case Exit::Reboot: return "reboot mid-run (no onExit)";
  }
  return "?";
}

void runOne(Exit exit, bool ownerValue) {
  const std::string tag = std::string(name(exit)) + (ownerValue ? " [owner: disabled]" : " [owner: enabled]");
  sim_keep_awake::request(false);
  sim_keep_awake::setForeground(true);
  Host host;
  host.idleTimerDisabled = ownerValue;

  sim_keep_awake::request(true);  // onEnter
  for (int i = 0; i < 5; i++) {
    sim_keep_awake::request(true);  // loop(): working
    host.pass();
  }
  check(host.idleTimerDisabled, tag + ": held during the run");
  check(host.sets == 1, tag + ": set exactly once");

  switch (exit) {
    case Exit::Done:
    case Exit::Failed:
    case Exit::Stopped:
      // The summary screen: loop() keeps ticking with a terminal state.
      for (int i = 0; i < 3; i++) {
        sim_keep_awake::request(false);
        host.pass();
      }
      break;
    case Exit::Back:
    case Exit::Sleep:
    case Exit::HomeGesture:
      sim_keep_awake::request(false);  // onExit
      host.pass();
      break;
    case Exit::Reboot:
      sim_keep_awake::request(false);  // the reboot reset simulator_main registers
      host.pass();
      break;
  }
  check(host.idleTimerDisabled == ownerValue, tag + ": the owner's value is back");
  check(host.restores == 1, tag + ": restored exactly once");
  for (int i = 0; i < 5; i++) host.pass();
  check(host.idleTimerDisabled == ownerValue && host.restores == 1 && host.sets == 1,
        tag + ": nothing more happens after the run");
}
}  // namespace

int main() {
  for (Exit e : {Exit::Done, Exit::Failed, Exit::Stopped, Exit::Back, Exit::Sleep, Exit::HomeGesture,
                 Exit::Reboot})
    for (bool owner : {false, true}) runOne(e, owner);

  // Backgrounded mid-run: released while away, taken again on return, and the
  // owner's value still comes back at the end -- not the value the lease itself
  // wrote before the app went away.
  {
    sim_keep_awake::request(false);
    sim_keep_awake::setForeground(true);
    Host host;
    host.idleTimerDisabled = false;
    sim_keep_awake::request(true);
    host.pass();
    check(host.idleTimerDisabled, "background: held before");
    sim_keep_awake::setForeground(false);
    host.pass();
    check(!host.idleTimerDisabled, "background: released while away");
    sim_keep_awake::setForeground(true);
    host.pass();
    check(host.idleTimerDisabled, "background: taken again on return");
    sim_keep_awake::request(false);
    host.pass();
    check(!host.idleTimerDisabled, "background: the owner's value at the end");
    check(host.sets == 2 && host.restores == 2, "background: two leases, two restores");
  }

  // A second run straight after the first snapshots the owner's value again,
  // not the first run's.
  {
    sim_keep_awake::request(false);
    sim_keep_awake::setForeground(true);
    Host host;
    host.idleTimerDisabled = true;
    sim_keep_awake::request(true);
    host.pass();
    sim_keep_awake::request(false);
    host.pass();
    host.idleTimerDisabled = false;  // the owner changes his setting between runs
    sim_keep_awake::request(true);
    host.pass();
    sim_keep_awake::request(false);
    host.pass();
    check(!host.idleTimerDisabled, "second run: restores the value from before IT");
  }

  // Unplugged mid-run: the owner's charging preference turns the idle timer
  // back ON under the lease. The lease must take it back, or the phone locks
  // mid-run (adversarial review, 2026-09-26).
  {
    sim_keep_awake::request(false);
    sim_keep_awake::setForeground(true);
    Host host;
    host.idleTimerDisabled = true;  // plugged in, preference: stay awake
    sim_keep_awake::request(true);
    host.pass();
    host.idleTimerDisabled = false;  // unplugged: SDL_EnableScreenSaver
    host.pass();
    check(host.idleTimerDisabled && host.reasserts == 1, "unplugged mid-run: the lease reasserts");
    sim_keep_awake::request(false);
    host.pass();
    check(sim_keep_awake::g_reapplyPreference.exchange(false),
          "every restore asks the host preference to re-apply itself");
  }

  // Never wanted: nothing is ever written.
  {
    sim_keep_awake::request(false);
    Host host;
    host.idleTimerDisabled = true;
    for (int i = 0; i < 10; i++) host.pass();
    check(host.sets == 0 && host.restores == 0 && host.idleTimerDisabled, "idle: never touched");
  }

  if (g_failures == 0) std::printf("keep_awake: all checks passed\n");
  return g_failures == 0 ? 0 : 1;
}
