#pragma once

// THE TURNED-PAGE LATCH: whether the page on the glass is a wide-table page
// ([T-021]), as the firmware says it is (docs/turned-page-landscape-plan-2026-10-04.md).
//
// One atomic flag with three writers, each of which returns whether it CHANGED
// the answer, because a change is what asks the host for a present (the host
// lays out its answer -- rotate, or snap back -- inside one, and an e-ink
// firmware may not present again for minutes):
//   * publish     -- EpubReaderActivity, once per displayed page, false on
//                    every path off the page it controls;
//   * screenEntered -- every NON-reader screen's Activity::onEnter, through
//                    HalGPIO::publishScreenIdentity. A PUSHED screen (the
//                    chapter list on Select, Find) keeps the reader alive and
//                    never runs its onExit (ActivityManager.cpp), so without
//                    this the flag outlived the page and the list was presented
//                    turned (adversarial review 2026-10-04, finding 2). The
//                    reader publishes again when it redraws after the pop;
//   * reset       -- the iOS in-process reboot, which keeps statics: a reboot
//                    taken on a turned page must not wake into a landscape app.
//
// Header-only and SDL-free so the contract is host-tested
// (tests/turned_page_landscape_test.cpp) without linking HalGPIO.cpp.
#include <atomic>

namespace turnedpage {

class Channel {
 public:
  bool publish(bool turned) { return flag_.exchange(turned) != turned; }
  bool screenEntered() { return flag_.exchange(false); }
  void reset() { flag_.store(false); }
  bool showing() const { return flag_.load(); }

 private:
  std::atomic<bool> flag_{false};
};

}  // namespace turnedpage
