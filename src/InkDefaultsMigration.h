#pragma once

// ONE-SHOT MIGRATION of the two Ink sliders that changed their shipped default.
//
// Builds 187 and 188 shipped Corner Rounding and Ink Spread at 0; build 189
// ships them at 45 and 55. A phone that opened the Ink group on 187/188 has 0
// WRITTEN for both, and a written value beats a registered default forever,
// so it would keep the flat page. Owner ruling 2026-09-12: migrate a stored 0
// to the new default ONCE, then never again -- a 0 chosen after this build
// stays 0.
//
// Pure, so the rule can be host-tested: the phone hands in what is actually
// WRITTEN in its store (not the registered default; a key with nothing
// written arrives as kUnwritten) plus the marker, and gets back what to
// write. tests/ink_defaults_migration_test.cpp pins every arm.

namespace inkmigration {

// Marker key `inkDefaultsMigration`: the version of this rule that has run.
// 0 (or unwritten) means never. Append versions; never reuse one.
constexpr int kVersion = 1;
constexpr int kUnwritten = -1;

constexpr int kRoundingDefault = 45;
constexpr int kSpreadDefault = 55;

struct Result {
  int rounding;   // value to write, or kUnwritten to leave the key alone
  int spread;
  int marker;     // always kVersion after a run
};

inline Result decide(int writtenRounding, int writtenSpread, int writtenMarker) {
  Result r{kUnwritten, kUnwritten, kVersion};
  if (writtenMarker >= kVersion) {
    // Already ran: touch nothing, marker stays where it is.
    r.marker = writtenMarker;
    return r;
  }
  if (writtenRounding == 0) r.rounding = kRoundingDefault;
  if (writtenSpread == 0) r.spread = kSpreadDefault;
  return r;
}

}  // namespace inkmigration
