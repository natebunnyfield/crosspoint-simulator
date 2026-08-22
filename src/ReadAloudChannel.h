#pragma once

#include <atomic>
#include <cstddef>
#include <cstdint>
#include <mutex>
#include <string>
#include <vector>

// The read-aloud page channel: the firmware's page text (and, once FW-B
// lands, per-word rects) on its way to a host speech consumer. Owned by
// HalGPIO; kept as a free header with no SDL or HAL state so a plain host
// test can assert the contract (the GrayscalePreview.h pattern). See
// .claude/PLAN-tts-read-aloud.md for the full contract.
//
// One word, wrapped across lines by the layout, publishes ONE RECT PER
// VISUAL FRAGMENT, all sharing the word's byteOffset/byteLen — a highlight
// keyed on the byte range then lights every fragment with no special cases.
//
// This POD is duplicated in the firmware's lib/hal/HalGPIO.h (where the
// channel methods are inline no-ops). The two definitions must stay
// field-identical.
struct ReadAloudWordRect {
  // Logical portrait panel pixels (X3: 528 wide, 792 tall; x right, y down),
  // independent of render scale — the firmware divides by its own scale at
  // capture time.
  uint16_t x, y, w, h;
  uint32_t byteOffset; // into the page's UTF-8 text; always a word start
  uint16_t byteLen;
};

struct ReadAloudPage {
  std::string utf8;                     // empty when cleared == true
  std::vector<ReadAloudWordRect> rects; // empty until the firmware ships FW-B
  uint32_t generation = 0;              // bumps on every publish, incl. clear
  bool cleared = false;                 // publish(nullptr) => reader exited
};

// Publisher is the firmware (page render); consumer is the host's main
// thread. The mutex is the entire thread story. Exactly ONE consumer may
// drain per build — the env-gated desktop logger or the iOS adapter.
class ReadAloudChannel {
public:
  void setWanted(bool w) { wanted_.store(w); }
  bool wanted() const { return wanted_.load(); }

  // utf8 == nullptr publishes the "no page" clear. Rects are optional and
  // only meaningful alongside text.
  void publish(const char *utf8, size_t utf8Len, const ReadAloudWordRect *rects,
               size_t rectCount) {
    std::lock_guard<std::mutex> lock(mutex_);
    page_.cleared = utf8 == nullptr;
    if (utf8 && utf8Len > 0)
      page_.utf8.assign(utf8, utf8Len);
    else
      page_.utf8.clear();
    if (!page_.cleared && rects && rectCount > 0)
      page_.rects.assign(rects, rects + rectCount);
    else
      page_.rects.clear();
    page_.generation = nextGeneration_++;
    hasNew_ = true;
  }

  // The in-process (iOS) reboot boundary. The run that published is being
  // abandoned, so a page still waiting here must not deliver into the next
  // boot's consumer -- stale text spoken over whatever the rebooted firmware
  // shows. wanted_ is left alone: each consumer re-seeds it on its own boot
  // path (the iOS adapter in CrossPointReadAloud_begin, the desktop logger
  // before the first loop()).
  void resetForReboot() {
    std::lock_guard<std::mutex> lock(mutex_);
    page_ = ReadAloudPage{};
    hasNew_ = false;
  }

  // True once per publish; `out` receives the page.
  bool consume(ReadAloudPage &out) {
    std::lock_guard<std::mutex> lock(mutex_);
    if (!hasNew_)
      return false;
    out = page_;
    hasNew_ = false;
    return true;
  }

private:
  std::atomic<bool> wanted_{false};
  std::mutex mutex_;
  ReadAloudPage page_;
  bool hasNew_ = false;
  uint32_t nextGeneration_ = 1;
};
