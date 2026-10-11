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
  // 16 bits per field, SIGNED by an offset of 32768 and clamped. The largest
  // framebuffer dimension this repo publishes here is a tablet's landscape
  // width in the low thousands of pixels (BoardConfig's biggest panel today,
  // at the top render-scale tier, stays under 4000), so +-32767 leaves headroom
  // no real render reaches; a value that somehow did gets clamped rather than
  // bleeding into the neighboring field the way a too-narrow pack would.
  //
  // Signed, since 2026-09-04: the firmware publishes its top inset as the
  // margin MINUS the cap-ink trim of the reading face (the blank above 'H' in
  // the line box), and at screenMargin 0 with a large face that goes a few
  // pixels NEGATIVE. The four-atomic channel this replaced passed that
  // through and the zen shift consumed it; the first packed version clamped
  // it to 0 (adversarial review 2026-09-04, finding 4).
  static constexpr int kBits = 16;
  static constexpr uint64_t kMask = (1ull << kBits) - 1;
  static constexpr int kOffset = 1 << (kBits - 1);

  static uint64_t clampField(int v) {
    const long long shifted = static_cast<long long>(v) + kOffset;
    if (shifted < 0) return 0;
    return shifted > static_cast<long long>(kMask) ? kMask
                                                   : static_cast<uint64_t>(shifted);
  }

  static uint64_t pack(int t, int r, int b, int l) {
    return (clampField(t) << (kBits * 3)) | (clampField(r) << (kBits * 2)) |
           (clampField(b) << kBits) | clampField(l);
  }

  static int field(uint64_t packed, int shift) {
    return static_cast<int>((packed >> shift) & kMask) - kOffset;
  }

  static void unpack(uint64_t packed, int &t, int &r, int &b, int &l) {
    t = field(packed, kBits * 3);
    r = field(packed, kBits * 2);
    b = field(packed, kBits);
    l = field(packed, 0);
  }

  std::atomic<uint64_t> packed_{0};
  std::atomic<bool> valid_{false};
};

// THE INSETS REACH THE HOST WITH THE PAGE THEY DESCRIBE, NOT BEFORE IT
// (2026-10-11, owner: "not flash display and jitter layout on font resize";
// docs/font-resize-flash-jitter-2026-10-11.md).
//
// EpubReaderActivity::render() publishes its insets at the TOP of the render,
// before the section is rebuilt and before a pixel of the new page is drawn.
// On a page turn they rarely move, but a font-size step changes the cap-ink
// trim and therefore the top inset, and the iOS zen layout re-places the page
// from it within a frame (pollReaderInsets -> relayout -> requestPresent). So
// the host re-laid the glass and presented while the render task was still
// building the reflowed chapter: the OLD page at the NEW placement (the
// jitter), and that present, already past the coalescing hold, then waited
// for pixelBufMutex while the 1-bit pass wrote and uploaded the 1-bit frame
// (the flash). Measured on the iOS Simulator: present #9 "frame from B" 63 ms
// after the relayout, on a font step and on no page turn.
//
// The turned-page channel had the same shape and was fixed the same way in
// the firmware (publish after the page's first displayBuffer, adversarial
// review 2026-10-04, finding 5). This one is fixed host-side, without a
// firmware change: the publish is STAGED, and the display's pixel writers
// COMMIT it when they write the page -- the first instant the new insets and
// the picture they belong to exist together. From there the coalescing hold
// that suppresses the 1-bit frame also holds the relayout's present, so the
// new placement and the composed new page land on one present.
class StagedReaderInsets {
 public:
  // Render task, at the top of a reader render.
  void publish(int topPx, int rightPx, int bottomPx, int leftPx) {
    staged_.publish(topPx, rightPx, bottomPx, leftPx);
    pending_.store(true, std::memory_order_release);
  }

  // The pixel writer, when it writes a NEW picture (never a reconvert of an
  // old one). Returns true when a staged publish was promoted. A publish that
  // lands between the exchange and the read is promoted now and promoted again
  // (identically) by the next commit -- harmless, and never a mix: each side
  // is a ReaderInsetsChannel, which cannot tear.
  bool commit() {
    if (!pending_.exchange(false, std::memory_order_acq_rel)) return false;
    int t = 0, r = 0, b = 0, l = 0;
    if (!staged_.read(t, r, b, l)) return false;
    live_.publish(t, r, b, l);
    return true;
  }

  // The host. Only committed insets: false until the first page that carried
  // a publish has been written.
  bool read(int &top, int &right, int &bottom, int &left) const {
    return live_.read(top, right, bottom, left);
  }

 private:
  ReaderInsetsChannel staged_;
  ReaderInsetsChannel live_;
  std::atomic<bool> pending_{false};
};
