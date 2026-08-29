// When the system's appearance may overwrite the owner's Dark Mode choice.
//
// Owner 2026-08-28: "when booted into system dark mode, be in dark mode."
//
// Two requirements pull against each other and BOTH have shipped as bugs:
//
//   * seeding from the system on every launch overwrote the in-app toggle, so
//     it did not survive a relaunch;
//   * seeding only on the first launch ever could not see a change made while
//     the app was CLOSED, so installing in light and reopening in dark came up
//     light.
//
// Neither answers from the current system alone. The missing question is "did
// the system change since we last looked", and that needs the previous answer
// remembered across launches. Every failure here is silent — a toggle that will
// not stick, or an app that ignores the phone — which is why this is a truth
// table and not a comment.
#include <cstdio>

#include "../ios/AppearanceSeed.h"

using appearanceseed::kNoneStored;
using appearanceseed::shouldSeedFromSystem;

static int failures = 0;

static void check(bool ok, const char *what) {
  if (!ok) {
    std::printf("  FAIL: %s\n", what);
    failures++;
  }
}

int main() {
  // ---- THE REPORTED BUG. Closed in light, phone switched to dark, reopened. ----
  check(shouldSeedFromSystem(false, 0, 1), "system went dark while closed -> follow it");
  check(shouldSeedFromSystem(false, 1, 0), "system went light while closed -> follow it");

  // ---- THE BUG THE FIRST-LAUNCH RULE EXISTS TO PREVENT. ----
  // System unchanged since we last looked, so whatever is stored is the
  // owner's own choice and must stand — including a toggle set AGAINST the
  // system appearance.
  check(!shouldSeedFromSystem(false, 1, 1), "system still dark -> the owner's setting stands");
  check(!shouldSeedFromSystem(false, 0, 0), "system still light -> the owner's setting stands");

  // ---- First ever launch: no setting to protect, so the system decides. ----
  check(shouldSeedFromSystem(true, kNoneStored, 1), "first launch, dark system");
  check(shouldSeedFromSystem(true, kNoneStored, 0), "first launch, light system");
  // Even with a remembered value, a first launch seeds: there is no settings
  // file, so there is no owner choice behind it.
  check(shouldSeedFromSystem(true, 1, 1), "first launch wins over a matching memory");

  // ---- Never recorded, but NOT a first launch: an install predating this. ----
  // Must NOT seed. The owner may have set the toggle deliberately, and
  // overwriting it on the upgrade launch is the exact bug the first-launch rule
  // was introduced to fix — reintroduced one release later.
  check(!shouldSeedFromSystem(false, kNoneStored, 1),
        "upgrade launch does not overwrite a stored choice");
  check(!shouldSeedFromSystem(false, kNoneStored, 0),
        "upgrade launch does not overwrite a stored choice (light)");

  // ---- And it must not stay stuck there. ----
  // The value is recorded on every launch, so the upgrade launch above leaves a
  // memory behind and the NEXT change is caught.
  check(appearanceseed::valueToRemember(1) == 1, "a dark system is remembered as dark");
  check(appearanceseed::valueToRemember(0) == 0, "a light system is remembered as light");
  check(shouldSeedFromSystem(false, appearanceseed::valueToRemember(0), 1),
        "the launch after an upgrade launch catches the change");

  if (failures == 0) {
    std::printf("appearance_seed_test: all checks passed\n");
    return 0;
  }
  std::printf("appearance_seed_test: %d FAILURES\n", failures);
  return 1;
}
