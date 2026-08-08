// Unit tests for ReadAloudChannel: the mutex'd page hand-off between the
// firmware's capture (publish) and the host speech consumer (consume). The
// contract under test: one consume per publish, latest publish wins,
// generations strictly increase, and publish(nullptr) is the "no page" clear
// that tells a consumer to stop.
//
// Build + run (no framework, no SDL):
//   c++ -std=c++20 -Isrc tests/read_aloud_channel_test.cpp -o /tmp/read_aloud_channel_test && /tmp/read_aloud_channel_test

#include "ReadAloudChannel.h"

#include <cstdio>
#include <cstring>

static int failures = 0;
#define CHECK(cond)                                                        \
  do {                                                                     \
    if (!(cond)) {                                                         \
      std::printf("FAIL %s:%d: %s\n", __FILE__, __LINE__, #cond);          \
      failures++;                                                          \
    }                                                                      \
  } while (0)

int main() {
  // --- empty channel: nothing to consume ------------------------------------
  {
    ReadAloudChannel ch;
    ReadAloudPage page;
    CHECK(!ch.consume(page));
  }

  // --- wanted flag round-trips, defaults off --------------------------------
  {
    ReadAloudChannel ch;
    CHECK(!ch.wanted());
    ch.setWanted(true);
    CHECK(ch.wanted());
    ch.setWanted(false);
    CHECK(!ch.wanted());
  }

  // --- publish -> consume once, then dry ------------------------------------
  {
    ReadAloudChannel ch;
    const char *text = "Hello page";
    const ReadAloudWordRect rects[] = {
        {10, 20, 40, 12, 0, 5},
        {60, 20, 40, 12, 6, 4},
    };
    ch.publish(text, std::strlen(text), rects, 2);
    ReadAloudPage page;
    CHECK(ch.consume(page));
    CHECK(page.utf8 == "Hello page");
    CHECK(page.rects.size() == 2);
    CHECK(page.rects[1].byteOffset == 6);
    CHECK(page.rects[1].w == 40);
    CHECK(!page.cleared);
    CHECK(page.generation == 1);
    CHECK(!ch.consume(page)); // one consume per publish
  }

  // --- two publishes before a consume: the second wins, generation counts both
  {
    ReadAloudChannel ch;
    ch.publish("first", 5, nullptr, 0);
    ch.publish("second", 6, nullptr, 0);
    ReadAloudPage page;
    CHECK(ch.consume(page));
    CHECK(page.utf8 == "second");
    CHECK(page.generation == 2);
    CHECK(!ch.consume(page));
  }

  // --- generations strictly increase across consumes ------------------------
  {
    ReadAloudChannel ch;
    ReadAloudPage page;
    ch.publish("a", 1, nullptr, 0);
    CHECK(ch.consume(page) && page.generation == 1);
    ch.publish("b", 1, nullptr, 0);
    CHECK(ch.consume(page) && page.generation == 2);
  }

  // --- publish(nullptr) is the clear: empty text, cleared flag, no rects ----
  {
    ReadAloudChannel ch;
    const ReadAloudWordRect rect = {1, 2, 3, 4, 0, 3};
    ch.publish("abc", 3, &rect, 1);
    ReadAloudPage page;
    CHECK(ch.consume(page) && !page.cleared);
    ch.publish(nullptr, 0, nullptr, 0);
    CHECK(ch.consume(page));
    CHECK(page.cleared);
    CHECK(page.utf8.empty());
    CHECK(page.rects.empty());
    CHECK(page.generation == 2);
  }

  // --- a clear never carries rects, even if a caller passes some ------------
  {
    ReadAloudChannel ch;
    const ReadAloudWordRect rect = {1, 2, 3, 4, 0, 3};
    ch.publish(nullptr, 0, &rect, 1);
    ReadAloudPage page;
    CHECK(ch.consume(page));
    CHECK(page.cleared && page.rects.empty());
  }

  // --- text without rects is legal (FW-A era firmware) ----------------------
  {
    ReadAloudChannel ch;
    ch.publish("no rects yet", 12, nullptr, 0);
    ReadAloudPage page;
    CHECK(ch.consume(page));
    CHECK(page.utf8 == "no rects yet" && page.rects.empty() && !page.cleared);
  }

  if (failures) {
    std::printf("%d failure(s)\n", failures);
    return 1;
  }
  std::printf("read_aloud_channel_test: all passed\n");
  return 0;
}
