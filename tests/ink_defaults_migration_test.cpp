// The one-shot migration of a stored 0 to the 2026-09-12 Ink defaults. Every
// arm of the rule: a stored 0 moves (to 45 / 55), an unwritten key is left
// alone (the registered default already covers it), a non-zero stored value
// is the owner's and is kept, and once the marker is at the version nothing
// moves ever again -- including a 0 chosen after the migration ran.

#include "InkDefaultsMigration.h"

#include <cstdio>

#include "TestCheck.h"

#define CHECK(x) testcheck::check((x), #x)

int main() {
  using namespace inkmigration;

  // A 187/188 phone that opened the Ink group: both written 0, no marker.
  {
    const Result r = decide(0, 0, kUnwritten);
    CHECK(r.rounding == kRoundingDefault);
    CHECK(r.spread == kSpreadDefault);
    CHECK(r.marker == kVersion);
  }
  // A phone that never opened the group: nothing written, nothing to write.
  {
    const Result r = decide(kUnwritten, kUnwritten, kUnwritten);
    CHECK(r.rounding == kUnwritten);
    CHECK(r.spread == kUnwritten);
    CHECK(r.marker == kVersion);
  }
  // Owner-chosen values are kept; only a 0 moves, and each key independently.
  {
    const Result r = decide(120, 0, 0);
    CHECK(r.rounding == kUnwritten);
    CHECK(r.spread == kSpreadDefault);
    const Result s = decide(0, 30, 0);
    CHECK(s.rounding == kRoundingDefault);
    CHECK(s.spread == kUnwritten);
  }
  // Marker at version: a 0 chosen AFTER the migration stays 0, forever.
  {
    const Result r = decide(0, 0, kVersion);
    CHECK(r.rounding == kUnwritten);
    CHECK(r.spread == kUnwritten);
    CHECK(r.marker == kVersion);
    const Result s = decide(0, 0, kVersion + 5);
    CHECK(s.rounding == kUnwritten && s.marker == kVersion + 5);
  }

  if (testcheck::g_failures == 0)
    std::printf("ink_defaults_migration_test: all checks passed\n");
  return testcheck::g_failures ? 1 : 0;
}
