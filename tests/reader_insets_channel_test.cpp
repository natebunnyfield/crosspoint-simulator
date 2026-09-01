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

  // --- negative and oversized fields clamp, and stay in their own field --
  {
    ReaderInsetsChannel ch;
    ch.publish(-5, 70000, 35, 16);
    int t = -99, r = -99, b = -99, l = -99;
    CHECK(ch.read(t, r, b, l));
    CHECK(t == 0);       // clamped up from negative
    CHECK(r == 65535);   // clamped down to the 16-bit field's max
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

  if (failures == 0) {
    std::printf("reader_insets_channel_test: all tests passed\n");
    return 0;
  }
  std::printf("reader_insets_channel_test: %d failure(s)\n", failures);
  return 1;
}
