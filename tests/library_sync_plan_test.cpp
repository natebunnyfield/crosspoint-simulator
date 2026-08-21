// The Update Library compare logic (firmware src/network/LibrarySyncPlan.h).
//
// Pure on purpose, and tested here because every wrong verdict is silent on
// device: a book that should update gets skipped, an unchanged book gets
// re-downloaded on every run, or a hostile manifest filename escapes /books/.
// None of that renders as an error — the summary line still says "done".
//
// Needs the firmware include set (same guarded pattern as build_identity in
// run_all.sh): the header under test lives in the firmware repo, because the
// firmware is what runs it.

#include <cstdio>

#include "network/LibrarySyncPlan.h"

static int failures = 0;

static void expect(bool ok, const char* what) {
  if (!ok) {
    std::printf("FAIL: %s\n", what);
    ++failures;
  }
}

int main() {
  using namespace librarysync;

  // --- sizeVerdict -----------------------------------------------------------
  expect(sizeVerdict(false, 0, 100) == SizeVerdict::DOWNLOAD, "missing file downloads");
  expect(sizeVerdict(true, 99, 100) == SizeVerdict::DOWNLOAD, "size mismatch downloads without hashing");
  expect(sizeVerdict(true, 100, 100) == SizeVerdict::CHECK_SHA, "same size defers to the digest");
  // Zero-byte agreement still goes to the digest rather than assuming: an
  // empty file on the card and an empty manifest entry are equal only if the
  // digests agree (and a 0-byte manifest entry is a publisher bug this code
  // must not paper over by skipping).
  expect(sizeVerdict(true, 0, 0) == SizeVerdict::CHECK_SHA, "zero-size pair still checks the digest");

  // --- shaMatches ------------------------------------------------------------
  const char* shaLower = "01ab4e46334be596f14055644b82963504e2e8a74e91f23fc276215c739584a6";
  const char* shaUpper = "01AB4E46334BE596F14055644B82963504E2E8A74E91F23FC276215C739584A6";
  const char* shaOther = "01ab4e46334be596f14055644b82963504e2e8a74e91f23fc276215c739584a7";
  expect(shaMatches(shaLower, shaLower), "identical digests match");
  expect(shaMatches(shaLower, shaUpper), "case difference is not a difference");
  expect(!shaMatches(shaLower, shaOther), "one nibble apart is a difference");
  // The empty-and-short cases are the load-bearing ones: a failed hash read
  // produces an empty string, and empty==empty must NOT read as "unchanged" —
  // that would silently skip every book the card cannot hash.
  expect(!shaMatches("", ""), "two empty digests do not match");
  expect(!shaMatches(shaLower, ""), "empty right side does not match");
  expect(!shaMatches("01ab", "01ab"), "a 4-char prefix pair is not a sha256");
  expect(!shaMatches(nullptr, shaLower), "null is not a digest");

  // --- isSafeFileName --------------------------------------------------------
  expect(isSafeFileName("WBN-Solari.epub"), "plain name is safe");
  expect(isSafeFileName("tico-spanish-sealed.epub"), "hyphenated name is safe");
  expect(!isSafeFileName("../../.crosspoint/settings.json"), "traversal is rejected");
  expect(!isSafeFileName("sub/dir.epub"), "separator is rejected");
  expect(!isSafeFileName("sub\\dir.epub"), "backslash separator is rejected");
  expect(!isSafeFileName(".hidden.epub"), "dot-leading name is rejected");
  expect(!isSafeFileName(""), "empty name is rejected");
  expect(!isSafeFileName(nullptr), "null name is rejected");

  if (failures == 0) {
    std::printf("library_sync_plan: all assertions passed\n");
    return 0;
  }
  std::printf("library_sync_plan: %d FAILURES\n", failures);
  return 1;
}
