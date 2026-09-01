#pragma once

#include <atomic>
#include <cstdint>

// The reader's published text-block insets (framebuffer px: top, right,
// bottom, left), on their way from the firmware's render task to the iOS zen
// layout, which places the panel from them. Owned by HalGPIO; kept as a free
// header with no SDL or HAL state so a plain host test can assert the
// contract -- the FontFamilyStepChannel.h pattern.
//
// PACKED INTO ONE ATOMIC. This replaces four independent `std::atomic<int>`
// fields (`publishReaderTextInsets`'s original shape, one `.store()` per
// field) plus a `readerInsetsValid` flag. `HalGPIO.h`'s own comment says why
// that split existed: "publish runs on the firmware task and the consumer is
// the main-thread relayout" -- a genuine cross-thread boundary with no lock.
// The old comment beside the four atomics argued the split was safe: "a torn
// read across two publishes of the SAME layout is harmless." True, and beside
// the point -- the case that actually matters is a torn read across two
// DIFFERENT layouts, and that is exactly what a font-size change or a page
// turn publishes (different top and bottom insets, because the reflowed text
// block ends somewhere else). A reader that samples the four fields
// separately can observe the NEW top from one publish paired with the OLD
// bottom from the one before it -- a combination that does not correspond to
// any real page.
//
// That combination is not inert. `ios/CrossPointIOSShim.cpp`'s zen-shift
// arithmetic reads top and bottom straight into
// `visTotal = slack + inkTopPx + inkBottomPx`, and the `want` shift it derives
// from a torn pair can land larger OR smaller than either the old or the new
// page's correct target -- a wrong-geometry frame that self-corrects on the
// very next poll once the tear has passed. That is a mechanism for "the page
// updates at full height then immediately becomes single-finger mode" (owner
// report, 2026-08-31, trigger: reactivation, then a font-size change, then a
// page turn) that no amount of pre-warming the LAYOUT CALL can fix, because
// the READ it warms from is what is unsound.
//
// One atomic makes the tear impossible: a `load()` always returns some value
// this class actually `store()`d, whole, never a mix of two stores.
class ReaderInsetsChannel {
 public:
  void publish(int topPx, int rightPx, int bottomPx, int leftPx) {
    packed_.store(pack(topPx, rightPx, bottomPx, leftPx),
                  std::memory_order_release);
    // Ordered after the geometry store (release above, acquire below in
    // read()) so a reader that observes valid_==true is guaranteed to load
    // the packed value this same publish wrote, never an older one.
    valid_.store(true, std::memory_order_release);
  }

  // false ("never published") lets the caller keep its own fallback constant,
  // distinct from a published zero -- same contract as the four-atomic
  // version this replaces.
  bool read(int &top, int &right, int &bottom, int &left) const {
    if (!valid_.load(std::memory_order_acquire)) return false;
    unpack(packed_.load(std::memory_order_acquire), top, right, bottom, left);
    return true;
  }

 private:
  // 16 bits per field, clamped. The largest framebuffer dimension this repo
  // publishes here is a tablet's landscape width in the low thousands of
  // pixels (BoardConfig's biggest panel today, at the top render-scale tier,
  // stays under 4000), so 65535 leaves headroom no real render reaches; a
  // value that somehow did gets clamped rather than bleeding into the
  // neighboring field the way a too-narrow pack would.
  static constexpr int kBits = 16;
  static constexpr uint64_t kMask = (1ull << kBits) - 1;

  static uint64_t clampField(int v) {
    if (v < 0) return 0;
    return static_cast<uint64_t>(v) > kMask ? kMask
                                             : static_cast<uint64_t>(v);
  }

  static uint64_t pack(int t, int r, int b, int l) {
    return (clampField(t) << (kBits * 3)) | (clampField(r) << (kBits * 2)) |
           (clampField(b) << kBits) | clampField(l);
  }

  static void unpack(uint64_t packed, int &t, int &r, int &b, int &l) {
    t = static_cast<int>((packed >> (kBits * 3)) & kMask);
    r = static_cast<int>((packed >> (kBits * 2)) & kMask);
    b = static_cast<int>((packed >> kBits) & kMask);
    l = static_cast<int>(packed & kMask);
  }

  std::atomic<uint64_t> packed_{0};
  std::atomic<bool> valid_{false};
};
