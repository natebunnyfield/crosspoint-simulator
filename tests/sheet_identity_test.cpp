// WHICH SHEET A SCREEN IS PRINTED ON -- src/SheetIdentity.h.
//
// Every failure mode here is a wrong PICTURE that compiles and logs nothing,
// which is the standing argument for a pure header with a host test (see
// PanelPalette.h, PhosphorGrain.h, FieldSelection.h). The three specific to
// this one:
//
//   * A seed of 0 reads to the latch as "nothing published yet", so a screen
//     whose hash happened to fold to 0 would silently restore the per-launch
//     sheet this replaces -- on that one screen, forever, with no symptom but
//     "Settings looks different today".
//   * A screen seed colliding with a page seed prints a menu on a leaf of the
//     open book. Nothing anywhere would say so.
//   * The FNV-1a that turns a name into a key has TWO copies, and they cannot
//     share a header: the firmware's is in src/activities/Activity.cpp and the
//     simulator is not linked on device. A drift between them changes which
//     sheet every system screen gets, without changing anything else. That one
//     is checked against the firmware's source text where a checkout is
//     present, and against pinned literals always.

#include "SheetIdentity.h"

#include <cstdio>
#include <cstring>
#include <fstream>
#include <set>
#include <sstream>
#include <string>

static int failures = 0;

static void check(bool ok, const char *what) {
  if (!ok) {
    std::printf("FAIL: %s\n", what);
    failures++;
  }
}

// The activity names the firmware actually enters, as of 2026-08-24. Used for
// the distinctness and collision sweeps rather than invented strings, so the
// properties are proven over the set that ships.
static const char *const kScreens[] = {
    "Boot",        "Home",         "Settings",      "FontSelection",
    "EditorFont",  "FileBrowser",  "FileManager",   "RecentBooks",
    "Reader",      "EpubReader",   "LibraryUpdate", "Colophon",
    "ClearCache",  "ClockOffset",  "NoteEditor",    "CrossPointWebServer",
    "Sleep",       "Crash",        "ClaudeChat",    "EpubReaderChapterSelection",
};
static constexpr int kScreenCount =
    static_cast<int>(sizeof(kScreens) / sizeof(kScreens[0]));

// --------------------------------------------------------------------------
static void testNeverZero() {
  // 0 is the latch's sentinel. Neither producer may return it, and the fold
  // that guarantees it has to be reachable rather than decorative -- so this
  // also asserts the fold's own value is not 0.
  check(sheetid::kNeverZero != 0u, "kNeverZero is itself a usable seed");
  for (int i = 0; i < kScreenCount; i++)
    check(sheetid::forScreen(sheetid::screenKey(kScreens[i])) != 0u,
          "a screen seed is never 0");
  for (int page = 0; page < 2000; page++)
    check(sheetid::forPage(0x0123456789ABCDEFull, page % 17, page) != 0u,
          "a page seed is never 0");
  // The empty name is a legal activity name as far as this code is concerned.
  check(sheetid::forScreen(sheetid::screenKey("")) != 0u,
        "the empty screen name still yields a seed");
  check(sheetid::forScreen(sheetid::screenKey(nullptr)) != 0u,
        "a null screen name still yields a seed");
}

// --------------------------------------------------------------------------
static void testDeterminism() {
  // THE WHOLE POINT. Same screen, same sheet -- across calls here, and across
  // launches and machines because nothing in the path reads a clock, an
  // address or an entropy source.
  for (int i = 0; i < kScreenCount; i++) {
    const uint32_t a = sheetid::forScreen(sheetid::screenKey(kScreens[i]));
    const uint32_t b = sheetid::forScreen(sheetid::screenKey(kScreens[i]));
    check(a == b, "a screen's seed is stable within a run");
  }
  check(sheetid::forPage(7, 2, 40) == sheetid::forPage(7, 2, 40),
        "a page's seed is stable within a run");
}

// --------------------------------------------------------------------------
static void testDistinctness() {
  // Two screens must be two leaves, or the show-through under a menu is the
  // menu itself and the paper never changes as you navigate. Not a hash-quality
  // claim: it is asserted over the names that ship.
  std::set<uint32_t> seen;
  for (int i = 0; i < kScreenCount; i++)
    seen.insert(sheetid::forScreen(sheetid::screenKey(kScreens[i])));
  check(static_cast<int>(seen.size()) == kScreenCount,
        "every shipped screen name gets its own sheet");

  // And a page is per page, which is the property paper_defects_test proves
  // for the field; pinned here too because forPage moved into this header.
  std::set<uint32_t> pages;
  for (int p = 0; p < 500; p++) pages.insert(sheetid::forPage(99, 0, p));
  check(pages.size() == 500, "500 consecutive pages are 500 sheets");
  check(sheetid::forPage(99, 0, 3) != sheetid::forPage(100, 0, 3),
        "the same page of two books is two sheets");
  check(sheetid::forPage(99, 0, 3) != sheetid::forPage(99, 1, 3),
        "the same page of two sections is two sheets");
}

// --------------------------------------------------------------------------
static void testNoCrossLaneCollision() {
  // A screen must never land on a page. The lane constant is what buys this,
  // so sweep a realistic page space against the shipped screen set rather than
  // asserting the constant is present.
  std::set<uint32_t> screens;
  for (int i = 0; i < kScreenCount; i++)
    screens.insert(sheetid::forScreen(sheetid::screenKey(kScreens[i])));
  int collisions = 0;
  for (uint64_t book = 1; book <= 40; book++)
    for (int spine = 0; spine < 30; spine++)
      for (int page = 0; page < 60; page++)
        if (screens.count(sheetid::forPage(book * 0x9E3779B97F4A7C15ull, spine,
                                           page)))
          collisions++;
  check(collisions == 0,
        "no screen sheet collides with any of 72,000 book pages");
}

// --------------------------------------------------------------------------
static void testFnvIsFnv() {
  // Pinned literals for the canonical FNV-1a 32-bit vectors, so a "harmless"
  // rewrite of the loop (signed char, the wrong prime, hashing the length)
  // fails here rather than silently re-papering every system screen.
  check(sheetid::screenKey("") == 2166136261u, "FNV-1a of the empty string");
  check(sheetid::screenKey("a") == 0xE40C292Cu, "FNV-1a of \"a\"");
  check(sheetid::screenKey("foobar") == 0xBF9CF968u, "FNV-1a of \"foobar\"");
  // High-bit bytes must be hashed UNSIGNED. A signed char here changes the key
  // for any name with a non-ASCII byte in it and nothing else.
  const char high[] = {static_cast<char>(0xFF), '\0'};
  uint32_t want = 2166136261u;
  want ^= 0xFFu;
  want *= 16777619u;
  check(sheetid::screenKey(high) == want, "FNV-1a hashes bytes unsigned");
}

// --------------------------------------------------------------------------
// The firmware's copy of that hash, read as text. Same technique as
// dial_table_test and panel_source_test.py: the two definitions cannot share a
// header, so the check is that the source still says the same thing.
//
// A missing firmware checkout is a missing precondition, not a failure -- but
// it says so loudly, because a silent skip is how this kind of check stops
// being run at all.
static void testFirmwareCopyMatches(const char *path) {
  std::ifstream in(path);
  if (!in) {
    std::printf("NOT CHECKED: firmware Activity.cpp not at %s -- pass its path "
                "as argv[1] to cross-check the FNV-1a constants\n",
                path);
    return;
  }
  std::stringstream ss;
  ss << in.rdbuf();
  const std::string src = ss.str();
  check(src.find("2166136261u") != std::string::npos,
        "firmware Activity.cpp still uses the FNV-1a offset basis");
  check(src.find("16777619u") != std::string::npos,
        "firmware Activity.cpp still uses the FNV-1a prime");
  // The unsigned-byte loop and the reader skip are the two halves that decide
  // WHICH sheet and WHETHER a book page keeps its own.
  check(src.find("const unsigned char c : name") != std::string::npos,
        "firmware Activity.cpp still hashes name bytes unsigned");
  check(src.find("if (!isReaderActivity()) gpio.publishScreenIdentity") !=
            std::string::npos,
        "firmware Activity::onEnter still publishes for non-readers only");
}

int main(int argc, char **argv) {
  testNeverZero();
  testDeterminism();
  testDistinctness();
  testNoCrossLaneCollision();
  testFnvIsFnv();
  testFirmwareCopyMatches(argc > 1
                              ? argv[1]
                              : "../crosspoint-reader/src/activities/Activity.cpp");
  if (failures) {
    std::printf("%d failure(s)\n", failures);
    return 1;
  }
  std::printf("sheet_identity_test: all checks passed\n");
  return 0;
}
