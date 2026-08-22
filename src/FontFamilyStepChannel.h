#pragma once

#include <atomic>

// The font-family step channel: a host gesture (the iOS shake in zen mode, or
// SHAKE in CROSSPOINT_SIM_INPUT_SCRIPT) on its way to the reader's family
// cycle. Owned by HalGPIO; kept as a free header with no SDL or HAL state so a
// plain host test can assert the contract (the ReadAloudChannel.h pattern).
//
// Same consume discipline as ReadAloudChannel: exactly one consume per inject,
// and a burst of injects between polls collapses to ONE step -- the reader
// re-paginates per step, so a queue here would turn one enthusiastic shake
// into a storm of SD loads. Direction is fixed at +1 (next family, wrapping);
// the firmware half is the inline no-op consumeFontFamilyStep() in the
// device's lib/hal/HalGPIO.h, which returns false so the poll folds away.
class FontFamilyStepChannel {
public:
  // Host side (simulator-only, like injectButton*).
  void inject() { pending_.store(true); }

  // Firmware side: true once per inject.
  bool consume() { return pending_.exchange(false); }

  // The in-process (iOS) reboot boundary: a step injected in the run being
  // abandoned must not land on the next boot's reader.
  void resetForReboot() { pending_.store(false); }

private:
  std::atomic<bool> pending_{false};
};
