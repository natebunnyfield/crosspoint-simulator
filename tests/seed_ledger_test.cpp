// The seeded-family ledger's decision table.
//
// Why this is worth a test: every failure mode is silent and only shows up a
// launch later, on a device. Get it wrong one way and a font the owner deleted
// comes back (the bug this fixes, reported 2026-09-15). Get it wrong the other
// way and a family a new app version adds is never seeded at all, which looks
// like a broken build rather than a logic error.
//
// The real function does file I/O against the app's Documents directory and
// clones directories, none of which can run off-device. What is pinned here is
// the DECISION -- the three-way split on (bundled, present, in the ledger) --
// which is the part that was missing entirely and the part a future edit is
// most likely to get subtly wrong.

#include <cstdio>
#include <string>
#include <vector>

namespace {

// Mirrors ios/CrossPointFsPrep.cpp. Kept as a separate definition rather than
// #included because that file is iOS-only (clonefile.h, SDL, the bundle path)
// and cannot compile on a host -- the same escape hatch, and the same
// reservation, as the host-settings and host-battery tests.
bool ledgerHas(const std::vector<std::string> &names, const std::string &family) {
  for (const std::string &n : names) {
    if (n == family) return true;
  }
  return false;
}

enum class Action { Seed, LeaveDeleted };

Action decide(bool presentOnCard, bool inLedger) {
  if (!presentOnCard && inLedger) return Action::LeaveDeleted;
  return Action::Seed;
}

int failures = 0;

void check(bool ok, const char *what) {
  if (!ok) {
    std::printf("FAIL: %s\n", what);
    ++failures;
  }
}

}  // namespace

int main() {
  // ------------------------------------------------------------ the ledger
  std::vector<std::string> ledger;
  check(!ledgerHas(ledger, "Edgar"), "an empty ledger holds nothing");
  ledger.push_back("Edgar");
  ledger.push_back("TeXGyreHeros");
  check(ledgerHas(ledger, "Edgar"), "a listed family is found");
  check(ledgerHas(ledger, "TeXGyreHeros"), "the second entry is found too");
  check(!ledgerHas(ledger, "Almendra"), "an unlisted family is not found");
  // Exact match only. A prefix must not count, or "Heros" would suppress
  // "HerosTextCut" -- two real families in this tree whose names share a stem.
  check(!ledgerHas(ledger, "TeXGyreHeros2"), "a longer name is not a match");
  check(!ledgerHas(ledger, "TeXGyre"), "a prefix is not a match");

  // ----------------------------------------------------- the decision table
  //
  // FIRST INSTALL: nothing on the card, nothing in the ledger. Seed everything.
  check(decide(false, false) == Action::Seed, "a never-seeded absent family is seeded");

  // THE BUG THIS FIXES: we seeded it, the owner deleted it, it is gone. Before
  // the ledger this re-cloned on every launch.
  check(decide(false, true) == Action::LeaveDeleted, "a deleted family stays deleted");

  // PRESENT: seed/update as before, so a font fix in an app update still lands.
  // True whether or not the ledger knows about it -- a family the owner dropped
  // in by hand is present, unlisted, and must still be updated by the bundle.
  check(decide(true, false) == Action::Seed, "a present unlisted family is still updated");
  check(decide(true, true) == Action::Seed, "a present listed family is still updated");

  // A NEW FAMILY IN AN APP UPDATE is the same shape as a first install, and
  // this is the case a naive "never re-seed anything" fix would break: it is
  // absent and unlisted, so it seeds.
  check(decide(false, false) == Action::Seed, "a newly bundled family seeds on first sight");

  // THE RESTORE PATH. Removing the family's line (or the whole file) is how the
  // owner gets a deleted family back; the next launch then sees absent and
  // unlisted, which is the first-install case.
  std::vector<std::string> pruned;
  for (const std::string &n : ledger) {
    if (n != "TeXGyreHeros") pruned.push_back(n);
  }
  check(!ledgerHas(pruned, "TeXGyreHeros"), "removing the line clears the record");
  check(decide(false, ledgerHas(pruned, "TeXGyreHeros")) == Action::Seed,
        "and the family seeds again on the next launch");
  check(ledgerHas(pruned, "Edgar"), "pruning one line leaves the others");

  if (failures == 0) std::printf("seed_ledger: all checks pass\n");
  return failures == 0 ? 0 : 1;
}
