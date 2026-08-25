// PHASE 2'S ARM ASSIGNMENT. src/ReadingArm.h.
//
// Nothing calls this yet (see that header). It is tested now because its
// failure modes produce a clean-looking dataset and a wrong conclusion, and
// because the properties below ARE the design — a reviewer arguing with the
// randomization should argue with these assertions, not with the prose.
//
// Four silent failures, one section each:
//
//   1. NOT DETERMINISTIC. A chapter re-read gets a different face, which is
//      jarring AND scores the re-read as a fresh observation of whichever arm
//      it landed on this time. Correlated measurements counted as independent
//      is the classic way to manufacture significance out of nothing.
//   2. NOT BALANCED. Independent coin flips let six chapters in a row land on
//      one arm; a book abandoned at chapter seven then contributes a lopsided
//      comparison, and abandonment is itself an outcome, so the imbalance is
//      not random with respect to what is being measured.
//   3. NOT RE-DERIVABLE. If the arm depended on anything not written into the
//      log, an analysis could not audit the assignment and would have to trust
//      the device. The whole seed protocol exists for this.
//   4. DEGENERATE AT THE EDGES. One arm, zero arms, a negative spine index
//      from a corrupt progress file. None of these may index out of bounds or
//      silently produce a lopsided design.

#include "../src/ReadingArm.h"

#include <cstdio>
#include <map>
#include <set>
#include <string>
#include <vector>

#include "TestCheck.h"

namespace {

constexpr uint64_t kSeed = 0x9E3779B97F4A7C15ull;
constexpr uint64_t kBook = 0xc74f943fd94b9751ull;

// --- 1. deterministic ------------------------------------------------------

void testDeterministic() {
  for (int spine = 0; spine < 64; spine++) {
    const int a = readingarm::armIndex(kSeed, kBook, spine, 2);
    const int b = readingarm::armIndex(kSeed, kBook, spine, 2);
    testcheck::check(a == b, "the same chapter always gets the same arm");
  }
  // The property that matters on a re-read: turning back to chapter 4 after
  // fifty chapters must still be chapter 4's arm. It is a pure function, so
  // this is trivially true -- and it is asserted anyway, because the obvious
  // "improvement" of drawing an assignment and caching it would break it in a
  // way nothing else here would catch.
  const int fourth = readingarm::armIndex(kSeed, kBook, 4, 2);
  for (int spine = 0; spine < 200; spine++) (void)readingarm::armIndex(kSeed, kBook, spine, 2);
  testcheck::check(readingarm::armIndex(kSeed, kBook, 4, 2) == fourth,
                   "an arm is not consumed by having been asked for");
}

// --- 2. balanced within every block ---------------------------------------

void testBlockBalance() {
  for (int armCount = 2; armCount <= 4; armCount++) {
    for (int book = 0; book < 8; book++) {
      const uint64_t bk = kBook + static_cast<uint64_t>(book) * 0x1000003ull;
      for (int block = 0; block < 12; block++) {
        std::set<int> seen;
        for (int pos = 0; pos < armCount; pos++) {
          const int spine = block * armCount + pos;
          const int arm = readingarm::armIndex(kSeed, bk, spine, armCount);
          testcheck::check(arm >= 0 && arm < armCount, "an arm index is in range");
          seen.insert(arm);
        }
        testcheck::check(static_cast<int>(seen.size()) == armCount,
                         "every complete block contains every arm exactly once");
      }
    }
  }
}

// A block design that always emitted the SAME permutation would be balanced and
// worthless -- chapter parity would decide the arm, and any effect that tracks
// chapter parity (a book whose odd chapters are dialogue) would be read as the
// treatment. So the permutation has to actually vary across blocks and books.
void testPermutationVaries() {
  std::set<std::string> shapes;
  for (int block = 0; block < 40; block++) {
    std::string s;
    for (int pos = 0; pos < 3; pos++) s += static_cast<char>('0' + readingarm::armIndex(kSeed, kBook, block * 3 + pos, 3));
    shapes.insert(s);
  }
  testcheck::check(shapes.size() >= 4, "the permutation is not the same in every block");

  std::set<int> firstArms;
  for (int book = 0; book < 40; book++) {
    firstArms.insert(readingarm::armIndex(kSeed, kBook + static_cast<uint64_t>(book), 0, 2));
  }
  testcheck::check(firstArms.size() == 2, "chapter 0 does not always land on the same arm across books");
}

// Over many blocks each arm must appear about equally often at each POSITION,
// or position and arm are correlated and the design is a fixed alternation
// wearing a costume.
void testPositionIsNotCorrelatedWithArm() {
  const int armCount = 2;
  const int blocks = 4000;
  std::map<int, int> armAtPos0;
  for (int block = 0; block < blocks; block++) {
    armAtPos0[readingarm::armIndex(kSeed, kBook, block * armCount, armCount)]++;
  }
  const double share = armAtPos0[0] / static_cast<double>(blocks);
  // A fair coin over 4000 blocks: sd is 0.0079, so 0.45..0.55 is ~6 sd wide and
  // will not flake, while a fixed alternation would score 1.0 or 0.0.
  testcheck::check(share > 0.45 && share < 0.55,
                   "the first slot of a block is not biased toward one arm");
}

// --- 3. re-derivable -------------------------------------------------------

// The seed is the only hidden input, and it is written into every cfg line. A
// different seed must give a different sequence, or recording it would be
// pointless; the SAME seed must reproduce it exactly, or auditing would be
// impossible. Both halves, because only having one is how a "seed" ends up
// being decorative.
void testSeedIsTheWholeSecret() {
  std::string a, b;
  for (int spine = 0; spine < 40; spine++) {
    a += static_cast<char>('0' + readingarm::armIndex(kSeed, kBook, spine, 2));
    b += static_cast<char>('0' + readingarm::armIndex(kSeed + 1, kBook, spine, 2));
  }
  testcheck::check(a != b, "a different seed gives a different assignment");

  std::string again;
  for (int spine = 0; spine < 40; spine++)
    again += static_cast<char>('0' + readingarm::armIndex(kSeed, kBook, spine, 2));
  testcheck::check(a == again, "the same seed reproduces the assignment exactly");
}

// --- 4. the edges ----------------------------------------------------------

void testDegenerateInputs() {
  testcheck::check(readingarm::armIndex(kSeed, kBook, 5, 1) == 0, "one arm is always arm 0");
  testcheck::check(readingarm::armIndex(kSeed, kBook, 5, 0) == 0, "zero arms answers 0 rather than dividing by it");
  testcheck::check(readingarm::armIndex(kSeed, kBook, 5, -3) == 0, "a negative arm count answers 0");
  // A corrupt progress.bin can hand back a negative spine. It must be clamped,
  // not used as an array index.
  const int neg = readingarm::armIndex(kSeed, kBook, -7, 2);
  testcheck::check(neg >= 0 && neg < 2, "a negative chapter index is clamped, not indexed with");
  testcheck::check(neg == readingarm::armIndex(kSeed, kBook, 0, 2), "and it reads as chapter 0");
  // Above the ceiling the count is clamped rather than overrunning perm[16].
  const int big = readingarm::armIndex(kSeed, kBook, 3, 999);
  testcheck::check(big >= 0 && big < readingarm::kMaxArms, "an absurd arm count is clamped to kMaxArms");
}

void testBlockAndPositionHelpers() {
  testcheck::check(readingarm::blockOf(0, 2) == 0 && readingarm::positionOf(0, 2) == 0, "chapter 0 is block 0 slot 0");
  testcheck::check(readingarm::blockOf(3, 2) == 1 && readingarm::positionOf(3, 2) == 1, "chapter 3 is block 1 slot 1");
  testcheck::check(readingarm::blockOf(-4, 2) == 0, "a negative chapter is block 0");
  testcheck::check(readingarm::blockOf(5, 0) == 0, "a zero arm count does not divide by zero");
}

// --- the washout -----------------------------------------------------------

// The transient at a block boundary is perfectly confounded with the arm --
// that is what makes it dangerous rather than merely noisy. Dropping the first
// pages of a chapter is the correction, and it must be applied at the START of
// a chapter (where the switch happens) and nowhere else.
void testWashout() {
  testcheck::check(readingarm::countsTowardOutcome(0, 0), "a washout of zero keeps everything");
  testcheck::check(!readingarm::countsTowardOutcome(0, 3), "the first page of a chapter is adaptation");
  testcheck::check(!readingarm::countsTowardOutcome(2, 3), "and so is the third");
  testcheck::check(readingarm::countsTowardOutcome(3, 3), "the fourth page counts");
  testcheck::check(readingarm::countsTowardOutcome(400, 3), "deep in a chapter counts");
  testcheck::check(readingarm::countsTowardOutcome(0, -1), "a negative washout is treated as none");
}

}  // namespace

int main() {
  testDeterministic();
  testBlockBalance();
  testPermutationVaries();
  testPositionIsNotCorrelatedWithArm();
  testSeedIsTheWholeSecret();
  testDegenerateInputs();
  testBlockAndPositionHelpers();
  testWashout();
  if (testcheck::g_failures) {
    std::printf("%d FAILURES\n", testcheck::g_failures);
    return 1;
  }
  std::printf("reading_arm_test: all checks passed\n");
  return 0;
}
