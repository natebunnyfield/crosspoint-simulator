#pragma once

// PHASE 2: WHICH ARM THIS CHAPTER IS IN. Designed, tested, and NOT WIRED.
//
// Owner's ask, 2026-08-25: *"we can even do this as randomized session
// variables, so that I don't have to pick what works. It's derived, and
// there's a range that works, and we can figure out which one, given enough
// data, works the best."*
//
// Nothing calls this yet, on purpose. Switching it on changes what the reader
// sees, and two things have to happen first: an explicit setting that ships
// OFF, and — for the page palette specifically — an owner decision to lift the
// freeze in src/FrozenPage.h. Both are open questions in
// docs/reading-experiments.md §7. The function is written and tested now
// because its failure modes are silent and because the design of the
// randomization is the part worth arguing about before any code depends on it.
//
// THE UNIT IS A CHAPTER, NOT A SESSION, and that is the whole design.
//
// A session-level randomization aligns the arms with everything that varies by
// session: time of day, fatigue, how long he has, whether he is on a train.
// Those swamp typography by a wide margin, and randomization only averages them
// out over many sessions — hundreds, at the rates in §6. A chapter-level
// randomization compares arms INSIDE one book, usually inside one sitting, over
// prose of nearly the same difficulty. That removes the book effect entirely
// (which is the largest one) and most of the drift.
//
// IT IS BLOCKED, NOT INDEPENDENT. Consecutive chapters are grouped into blocks
// of `armCount` and each block gets a random PERMUTATION of the arms, so every
// complete block contains every arm exactly once. Independent coin flips would
// let a run of six chapters land on one arm, and a book abandoned at chapter
// seven would then contribute a lopsided comparison; blocking makes every
// prefix balanced to within one block. This is a randomized complete block
// design, and the block is the thing time-varying confounds are trapped inside.
//
// IT IS A PURE FUNCTION OF THE SEED, NOT A DRAW. Two consequences, both
// load-bearing:
//
//   1. Turning back to chapter 4 renders it the way chapter 4 was rendered
//      before. A drawn assignment would re-roll it, which is both jarring and a
//      correlated-measurement bug — the re-read would be scored as a fresh
//      observation of whichever arm it happened to land on this time.
//   2. THE WHOLE ASSIGNMENT IS RE-DERIVABLE FROM THE LOG. The seed is written
//      into every `cfg` line (`armseed`), so an analysis can recompute every
//      arm from scratch and check that the recorded ones match, instead of
//      trusting the device. An experiment whose assignment cannot be audited is
//      an experiment whose results cannot be defended.
//
// Pure and host-tested (tests/reading_arm_test.cpp) for the reason everything
// in this family is: an assignment that is subtly unbalanced, or that silently
// depends on something it should not, produces a clean-looking dataset and a
// wrong conclusion. No compiler sees it and no rendered page announces it.

#include <cstdint>

namespace readingarm {

// The mixer every seed in this repo uses, spelled out here so this header
// compiles standalone in a host test. Same three-input avalanche as
// phosphorgrain::hash3; not shared with it only because pulling in the grain
// would drag the surface model into a file about statistics.
inline uint32_t mix(uint64_t a, uint64_t b, uint64_t c) {
  uint64_t h = 1469598103934665603ull;
  const uint64_t vals[3] = {a, b, c};
  for (const uint64_t v : vals) {
    for (int i = 0; i < 8; i++) {
      h ^= (v >> (i * 8)) & 0xFFu;
      h *= 1099511628211ull;
    }
  }
  h ^= h >> 33;
  h *= 0xff51afd7ed558ccdull;
  h ^= h >> 33;
  return static_cast<uint32_t>(h);
}

// Which block a chapter falls in, and its position inside it.
inline int blockOf(int spineIndex, int armCount) {
  if (armCount < 1) return 0;
  const int s = spineIndex < 0 ? 0 : spineIndex;
  return s / armCount;
}

inline int positionOf(int spineIndex, int armCount) {
  if (armCount < 1) return 0;
  const int s = spineIndex < 0 ? 0 : spineIndex;
  return s % armCount;
}

// THE ASSIGNMENT. Returns 0..armCount-1.
//
// A Fisher-Yates shuffle of [0, armCount) driven by a counter-based PRNG seeded
// from (seed, bookKey, block) — counter-based rather than stateful so the
// permutation depends on nothing but its three inputs, and so it is trivially
// reimplementable in the Python that audits it.
//
// armCount <= 1 always answers 0: an experiment with one arm is not an
// experiment, and the safe reading of that is "leave the settings alone".
inline int armIndex(uint64_t seed, uint64_t bookKey, int spineIndex, int armCount) {
  if (armCount <= 1) return 0;
  if (armCount > 16) armCount = 16;  // see kMaxArms
  const int block = blockOf(spineIndex, armCount);
  int perm[16];
  for (int i = 0; i < armCount; i++) perm[i] = i;
  for (int i = armCount - 1; i > 0; i--) {
    const uint32_t r = mix(seed ^ bookKey, static_cast<uint64_t>(block), static_cast<uint64_t>(i));
    const int j = static_cast<int>(r % static_cast<uint32_t>(i + 1));
    const int t = perm[i];
    perm[i] = perm[j];
    perm[j] = t;
  }
  return perm[positionOf(spineIndex, armCount)];
}

// The hard ceiling, and it is a STATISTICAL limit rather than a buffer size.
// Two arms reach significance at this data rate; eight never will (§6). The
// array is sized for it, but the number is chosen because an experiment that
// cannot finish is worse than no experiment.
inline constexpr int kMaxArms = 16;

// WASHOUT. Does this page count toward the outcome, or is it still adaptation?
//
// A reader meeting a changed face at the top of a chapter is slower for a while
// for reasons that have nothing to do with which face is better — and the
// switch happens at exactly the block boundary, so that transient is perfectly
// confounded with the arm unless it is excluded. Dropping the first few pages
// of every chapter costs data and buys an unbiased estimate; the alternative
// buys a bias that always points the same way (against whichever arm is
// unfamiliar).
//
// It is applied in the REPORT, not on the device: the pages are logged either
// way, so the washout length can be varied afterward and the answer checked for
// sensitivity to it. tools/reading_report.py owns the default.
inline bool countsTowardOutcome(int pageInSpine, int washoutPages) {
  if (washoutPages <= 0) return true;
  return pageInSpine >= washoutPages;
}

}  // namespace readingarm
