// Unit + concurrency tests for ReaderInsetsChannel: the reader's published
// text-block insets on their way from the firmware's render task to the iOS
// zen layout's main-thread relayout.
//
// The contract under test: nothing published reads as "unpublished" (distinct
// from a published zero), publish/read round-trips exactly, out-of-range
// fields clamp instead of corrupting a neighbor, and -- the reason this
// header exists at all (S-034, BUGS.md) -- a reader on one thread NEVER
// observes a torn mix of two different publishes made from another thread.
// That last property is what the four-separate-`std::atomic<int>` shape this
// header replaced did not have: this test's "torn reads" case is built to
// fail against that shape and pass against this one.
//
// Build + run (no framework, no SDL):
//   c++ -std=c++20 -Isrc tests/reader_insets_channel_test.cpp -o /tmp/reader_insets_channel_test && /tmp/reader_insets_channel_test

#include "ReaderInsetsChannel.h"

#include <atomic>
#include <cstdio>
#include <thread>

#include "TestCheck.h"

static int &failures = testcheck::g_failures;

int main() {
  // --- never published reads as unpublished -----------------------------
  {
    ReaderInsetsChannel ch;
    int t = -1, r = -1, b = -1, l = -1;
    CHECK(!ch.read(t, r, b, l));
  }

  // --- publish/read round-trips exactly ----------------------------------
  {
    ReaderInsetsChannel ch;
    ch.publish(60, 16, 35, 16);
    int t = 0, r = 0, b = 0, l = 0;
    CHECK(ch.read(t, r, b, l));
    CHECK(t == 60);
    CHECK(r == 16);
    CHECK(b == 35);
    CHECK(l == 16);
  }

  // --- a published zero reads as published, not as "never published" ----
  {
    ReaderInsetsChannel ch;
    ch.publish(0, 0, 0, 0);
    int t = -1, r = -1, b = -1, l = -1;
    CHECK(ch.read(t, r, b, l));
    CHECK(t == 0 && r == 0 && b == 0 && l == 0);
  }

  // --- a NEGATIVE top inset round-trips (2026-09-04) ----------------------
  // The firmware publishes margin minus the reading face's cap-ink trim; at
  // screenMargin 0 with a large face that is a few pixels below zero, and the
  // four-atomic channel this replaced passed it through. The first packed
  // version clamped it to 0 and moved the zen shift by the difference.
  {
    ReaderInsetsChannel ch;
    ch.publish(-7, 16, 35, 16);
    int t = 0, r = 0, b = 0, l = 0;
    CHECK(ch.read(t, r, b, l));
    CHECK(t == -7);
    CHECK(r == 16 && b == 35 && l == 16);
  }

  // --- a later publish replaces the earlier one, in full ------------------
  {
    ReaderInsetsChannel ch;
    ch.publish(60, 16, 35, 16);
    ch.publish(48, 12, 41, 12);  // e.g. a font-size step's new reflow
    int t = 0, r = 0, b = 0, l = 0;
    CHECK(ch.read(t, r, b, l));
    CHECK(t == 48);
    CHECK(r == 12);
    CHECK(b == 41);
    CHECK(l == 12);
  }

  // --- out-of-range fields clamp, and stay in their own field -------------
  // Signed since 2026-09-04: a small negative is a VALUE (the case above),
  // and the clamp is at the signed field's ends, +-32767 / -32768.
  {
    ReaderInsetsChannel ch;
    ch.publish(-70000, 70000, 35, 16);
    int t = -99, r = -99, b = -99, l = -99;
    CHECK(ch.read(t, r, b, l));
    CHECK(t == -32768);  // clamped up to the signed field's min
    CHECK(r == 32767);   // clamped down to the signed field's max
    CHECK(b == 35);      // neighbors untouched by the clamp
    CHECK(l == 16);
  }

  // --- concurrency: a reader on one thread never sees a torn publish -----
  //
  // Two layouts, chosen so every field differs between them and neither
  // shares a value with the other -- a torn mix of the two is detectable in
  // every field, not just one. The writer alternates between them as fast as
  // it can (no delay) for a large number of iterations, while the reader
  // polls concurrently; every successful read must match ONE of the two
  // layouts in ALL FOUR fields.
  {
    ReaderInsetsChannel ch;
    constexpr int kIterations = 2'000'000;
    std::atomic<bool> writerDone{false};
    std::atomic<int> tornReads{0};
    std::atomic<int> goodReads{0};

    std::thread writer([&] {
      for (int i = 0; i < kIterations; ++i) {
        if (i & 1) {
          ch.publish(60, 16, 35, 16);
        } else {
          ch.publish(1000, 2000, 3000, 4000);
        }
      }
      writerDone.store(true, std::memory_order_release);
    });

    std::thread reader([&] {
      while (!writerDone.load(std::memory_order_acquire)) {
        int t = 0, r = 0, b = 0, l = 0;
        if (!ch.read(t, r, b, l)) continue;
        const bool isLayoutA = (t == 60 && r == 16 && b == 35 && l == 16);
        const bool isLayoutB =
            (t == 1000 && r == 2000 && b == 3000 && l == 4000);
        if (isLayoutA || isLayoutB) {
          goodReads.fetch_add(1, std::memory_order_relaxed);
        } else {
          tornReads.fetch_add(1, std::memory_order_relaxed);
        }
      }
    });

    writer.join();
    reader.join();

    // The reader must have actually raced the writer -- a channel that
    // publishes so slowly (or a reader that never got scheduled) the two
    // never overlapped would pass this check by doing nothing.
    CHECK(goodReads.load() > 1000);
    if (tornReads.load() != 0) {
      std::printf(
          "reader_insets_channel_test: %d TORN read(s) out of %d -- a "
          "reader observed a mix of two different publishes\n",
          tornReads.load(), goodReads.load() + tornReads.load());
    }
    CHECK(tornReads.load() == 0);
  }

  // --- STAGED: a publish is invisible until the page that carries it is
  // written (2026-10-11, docs/font-resize-flash-jitter-2026-10-11.md). The
  // host relaid the zen page from insets the render task published BEFORE it
  // drew the reflowed page, presenting the old page at the new placement.
  {
    StagedReaderInsets ch;
    int t = -1, r = -1, b = -1, l = -1;
    CHECK(!ch.read(t, r, b, l));
    CHECK(!ch.commit());  // nothing staged: nothing to promote
    ch.publish(14, 16, 16, 16);
    CHECK(!ch.read(t, r, b, l));  // published, NOT yet on the glass
    CHECK(!ch.commit());  // a write before the page (a popup) promotes nothing
    ch.markPageDrawing();
    CHECK(ch.commit());
    CHECK(ch.read(t, r, b, l));
    CHECK(t == 14 && r == 16 && b == 16 && l == 16);
    CHECK(!ch.commit());  // a second write of the same page promotes nothing

    // The font step: the new top is staged while the old page is still up,
    // and the host keeps reading the OLD insets until the new page is written.
    ch.publish(12, 16, 16, 16);
    CHECK(ch.read(t, r, b, l));
    CHECK(t == 14);
    // A build past 2 s draws "Indexing" over the OLD page: that write must
    // leave the old insets live (review of 576ad65, finding 1).
    CHECK(!ch.commit());
    CHECK(ch.read(t, r, b, l));
    CHECK(t == 14);
    ch.markPageDrawing();  // renderContents: this page is the one displayed
    CHECK(ch.commit());
    CHECK(ch.read(t, r, b, l));
    CHECK(t == 12);

    // Two publishes before one write: the LATER one is what lands.
    ch.publish(20, 1, 2, 3);
    ch.publish(-7, 4, 5, 6);
    ch.markPageDrawing();
    CHECK(ch.commit());

    // A page identity from a PREVIOUS render does not arm a newer publish:
    // the publish disarms.
    ch.markPageDrawing();
    ch.publish(30, 1, 1, 1);
    CHECK(!ch.commit());
    CHECK(ch.read(t, r, b, l));
    CHECK(t == -7);
    CHECK(ch.read(t, r, b, l));
    CHECK(t == -7 && r == 4 && b == 5 && l == 6);
  }

  if (failures == 0) {
    std::printf("reader_insets_channel_test: all tests passed\n");
    return 0;
  }
  std::printf("reader_insets_channel_test: %d failure(s)\n", failures);
  return 1;
}
