#pragma once
//
// ONE ASSERTION HARNESS for the host tests.
//
// There were eight hand-copied `check()` functions and thirteen `#define CHECK`
// macros in this directory, in dialects that did not agree: CHECK(cond),
// CHECK(cond, "message"), CHECKM(cond, "message"), check(bool, const char *),
// check(bool, const std::string &), checkEq, checkNear, expect. Moving an
// assertion from one file to another was a compile error, which is a tax on
// exactly the thing a test suite should make cheap.
//
// Everything here reproduces its dialect's output BYTE FOR BYTE -- the failure
// text carries the reason, and rewording one would lose the argument it makes.
// Nothing was unified that could not be reproduced exactly; the files whose
// dialect differs in its printed form keep their own printer and share only the
// counter (bind a reference to testcheck::g_failures and the local printer's
// `failures++` keeps working unchanged).
//
// THE DIALECTS
//
//   check(ok, what)              "FAIL: %s\n", counts
//   checkEq(got, want, what)     as above, with both values printed
//   checkNear(got, want, tol, w) as above, with the tolerance printed
//   CHECK(cond)                  "FAIL %s:%d: %s\n" with __FILE__/__LINE__/text
//   CHECKM(cond, ...)            as above, printf-formatted reason
//   expect(cond, what)           "FAIL: %s\n" to STDERR, then exit(1)
//
// Two opt-ins, both declared BEFORE the include:
//
//   TESTCHECK_FATAL_DIALECT       CHECK aborts on the first failure (stderr +
//                                 exit(1)) and counts checks rather than
//                                 failures. device_truth and sha256 shipped
//                                 that way; so do the five tests converted off
//                                 bare assert(), which aborted too -- and which
//                                 compiled to NOTHING under -DNDEBUG.
//   TESTCHECK_CHECK_TAKES_MESSAGE CHECK is spelled with a message, i.e. it is
//                                 CHECKM under the other name. light_ink does.
//
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <string>

namespace testcheck {

// Shared counters. Inline variables, so a test binds a reference to one in
// place of its own `static int failures = 0;` and every existing read of that
// name -- including the pass/fail tail -- goes on working untouched.
inline int g_failures = 0;
inline int g_checks = 0;

inline void check(bool ok, const char *what) {
  if (!ok) {
    std::printf("FAIL: %s\n", what);
    g_failures++;
  }
}

inline void check(bool ok, const std::string &what) {
  if (!ok) {
    std::printf("FAIL: %s\n", what.c_str());
    g_failures++;
  }
}

inline void checkEq(int got, int want, const std::string &what) {
  if (got == want) return;
  std::printf("FAIL: %s -- got %d, want %d\n", what.c_str(), got, want);
  g_failures++;
}

inline void checkEq(const std::string &got, const std::string &want,
                    const char *what) {
  if (got != want) {
    std::printf("FAIL: %s\n  got  \"%s\"\n  want \"%s\"\n", what, got.c_str(),
                want.c_str());
    g_failures++;
  }
}

// The comparison is written as !(|d| <= tol) rather than |d| > tol on purpose:
// a NaN fails the first and passes the second, and a NaN is exactly the answer
// this is here to catch.
inline void checkNear(double got, double want, double tol, const char *what) {
  if (!(std::fabs(got - want) <= tol)) {
    std::printf("FAIL: %s (got %.6f, want %.6f +/- %.6f)\n", what, got, want,
                tol);
    g_failures++;
  }
}

// The fail-fast dialect. Stops at the first failure because the tests using it
// set up process-wide state (env vars, a mock HTTP root, a live radio shim) and
// a later assertion measured after an earlier one failed reports noise.
inline void expect(bool cond, const char *what) {
  if (!cond) {
    std::fprintf(stderr, "FAIL: %s\n", what);
    std::exit(1);
  }
}

}  // namespace testcheck

// The macros stringify the condition, so they are variadic: a condition
// containing a comma at top level -- xQueuePeek(sem, nullptr, 0) == pdFALSE --
// is several macro arguments, and a fixed-arity macro rejects it outright.
#ifdef TESTCHECK_FATAL_DIALECT
#define CHECK(...)                                                            \
  do {                                                                        \
    testcheck::g_checks++;                                                    \
    if (!(__VA_ARGS__)) {                                                     \
      std::fprintf(stderr, "FAIL %s:%d: %s\n", __FILE__, __LINE__,            \
                   #__VA_ARGS__);                                             \
      std::exit(1);                                                           \
    }                                                                         \
  } while (0)
#elif defined(TESTCHECK_CHECK_TAKES_MESSAGE)
#define CHECK(cond, ...) CHECKM(cond, __VA_ARGS__)
#else
#define CHECK(...)                                                            \
  do {                                                                        \
    if (!(__VA_ARGS__)) {                                                     \
      std::printf("FAIL %s:%d: %s\n", __FILE__, __LINE__, #__VA_ARGS__);      \
      testcheck::g_failures++;                                                \
    }                                                                         \
  } while (0)
#endif

#define CHECKM(cond, ...)                                                     \
  do {                                                                        \
    if (!(cond)) {                                                            \
      std::printf("FAIL %s:%d: ", __FILE__, __LINE__);                        \
      std::printf(__VA_ARGS__);                                               \
      std::printf("\n");                                                      \
      testcheck::g_failures++;                                                \
    }                                                                         \
  } while (0)
