// The host settings channel: the wire that carries a GitHub token from a
// surface the owner can reach to the fetch that needs it.
//
// It exists because Update Library was UNCONFIGURABLE on iOS. The token lives
// in SETTINGS.githubToken, which is set by hand-editing /.crosspoint/
// settings.json on the card, and a phone cannot open that file -- so the
// feature's own "no token" screen printed instructions nobody could follow.
//
// Two arms, because CROSSPOINT_SIM_HOST_SETTINGS is a compile-time switch and
// each arm is a different implementation:
//
//   -DCROSSPOINT_SIM_HOST_SETTINGS=1  the phone's branch. The real backend
//                                     (ios/CrossPointHostSettings.mm) is
//                                     iOS-only and there is no paired device,
//                                     so without the override it would ship
//                                     with no coverage at all -- the same
//                                     escape hatch, for the same reason, as
//                                     CROSSPOINT_SIM_HOST_WIFI. This file
//                                     supplies a scripted backend in its place.
//
//   (no override)                     the desktop's branch: the inline
//                                     environment-variable hatch in the header,
//                                     plus the two text gates below, which
//                                     need no platform at all.
//
// WHAT IT CANNOT COVER: whether iOS returns what we think it returns. That the
// Settings.app row is reachable, that -stringForKey: sees a value typed into a
// PSTextFieldSpecifier, and that IsSecure masks it are device-verify items.
//
//   c++ -std=c++20 -Isrc [-DCROSSPOINT_SIM_HOST_SETTINGS=1] \
//       tests/host_settings_test.cpp -o /tmp/host_settings && /tmp/host_settings

#include "SimHostSettings.h"

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <sstream>
#include <string>

#if CROSSPOINT_SIM_HOST_SETTINGS

// Stand-in backend. The real one reads NSUserDefaults; this is the same shape
// with the STORE -- and only the store -- replaced by a variable a test can
// set. The copy and its truncation are `copyToken` from the header, which is
// the code the phone actually runs.
namespace sim_host_settings {
namespace {
std::string g_scripted;
}  // namespace

size_t githubToken(char *out, size_t cap) {
  // Calls the SHIPPED copy, not a fourth transcription of it. That is the whole
  // point of the arm: ios/CrossPointHostSettings.mm reduces to
  // "fetch the NSString, hand it to copyToken", so testing copyToken through
  // this stand-in tests the phone's bytes. The stand-in replaces only the STORE
  // -- NSUserDefaults, which cannot exist here.
  return copyToken(g_scripted.empty() ? nullptr : g_scripted.c_str(), out, cap);
}

bool hasSettingsSurface() { return true; }

void testSetToken(const std::string &value) { g_scripted = value; }
}  // namespace sim_host_settings

#endif

#include "TestCheck.h"
using testcheck::check;
using testcheck::checkEq;

namespace {

// The firmware field this ends up in: CrossPointSettings.h's
// `char githubToken[104]`. Written out rather than included, because the host
// tests deliberately do not need a firmware checkout -- the four that do are
// shell scripts kept out of run_all.sh for exactly that reason. Sized for a
// fine-grained PAT ("github_pat_" + 82 chars); a classic 40-char token fits
// several times over.
constexpr size_t kFirmwareFieldSize = 104;

// A caller-side buffer with poison either side of it. Truncation is the failure
// mode that matters here: the destination is fixed-size and a token pasted with
// a stray character is exactly what arrives, so "copies one byte too many" has
// to be a test failure rather than a corrupted neighbour nobody notices.
//
// Every arm drives `sim_host_settings::copyToken` -- the ONE copy both backends
// call -- so these guards sit under the shipped bytes and not under a
// transcription of them.
struct GuardedBuffer {
  static constexpr size_t kGuard = 8;
  char raw[kGuard + kFirmwareFieldSize + kGuard];

  GuardedBuffer() { std::memset(raw, '\xA5', sizeof(raw)); }
  char *data() { return raw + kGuard; }
  std::string value() const { return std::string(raw + kGuard); }

  bool guardsIntact() const {
    for (size_t i = 0; i < kGuard; ++i) {
      if (raw[i] != '\xA5') return false;
      if (raw[kGuard + kFirmwareFieldSize + i] != '\xA5') return false;
    }
    return true;
  }
};

std::string slurp(const std::string &path) {
  std::ifstream in(path, std::ios::binary);
  if (!in) return {};
  std::ostringstream ss;
  ss << in.rdbuf();
  return ss.str();
}

// ------------------------------------------------------------------ arms ---

#if CROSSPOINT_SIM_HOST_SETTINGS

// A configured phone. The whole point: the token arrives, and it is the one the
// owner typed rather than the empty string that produced the NO_TOKEN screen.
void testHostTokenArrives() {
  sim_host_settings::testSetToken("github_pat_EXAMPLE_NOT_A_REAL_TOKEN");
  GuardedBuffer buf;
  const size_t length =
      sim_host_settings::githubToken(buf.data(), kFirmwareFieldSize);
  checkEq(static_cast<int>(length), 35, "host token length");
  checkEq(buf.value(), "github_pat_EXAMPLE_NOT_A_REAL_TOKEN",
          "host token bytes");
  check(buf.guardsIntact(), "host token did not write outside the field");
}

// An empty field is "not configured", not "a token that is the empty string".
// LibraryUpdater branches on this to raise NO_TOKEN rather than sending
// "Authorization: Bearer " and getting a 401 it would have to explain.
void testEmptyHostTokenReadsAsUnset() {
  sim_host_settings::testSetToken("");
  GuardedBuffer buf;
  checkEq(static_cast<int>(
              sim_host_settings::githubToken(buf.data(), kFirmwareFieldSize)),
          0, "empty host token reports zero length");
  checkEq(buf.value(), "", "empty host token leaves the buffer empty");
}

// Longer than the field. It TRUNCATES rather than overflowing -- the
// destination is a fixed char[104] in the firmware and the alternative to a
// short token is a smashed stack -- and it returns the FULL length, so the one
// call site can say "truncated, and it will not authenticate" without ever
// holding the untruncated value.
void testOversizeTokenTruncatesAndReportsIt() {
  const std::string oversize(kFirmwareFieldSize + 40, 'x');
  sim_host_settings::testSetToken(oversize);
  GuardedBuffer buf;
  const size_t length =
      sim_host_settings::githubToken(buf.data(), kFirmwareFieldSize);
  checkEq(static_cast<int>(length), static_cast<int>(oversize.size()),
          "oversize token reports its real length");
  checkEq(static_cast<int>(buf.value().size()),
          static_cast<int>(kFirmwareFieldSize - 1),
          "oversize token is cut to the field, less the terminator");
  check(length > kFirmwareFieldSize - 1,
        "the return value is what tells the caller it was truncated");
  check(buf.guardsIntact(), "oversize token did not write outside the field");
}

// Exactly the field's capacity, less the terminator: the last size that is NOT
// a truncation. Off-by-one either way is a token that silently loses its final
// character, which authenticates as nothing and says so nowhere.
void testExactFitIsNotTruncated() {
  const std::string exact(kFirmwareFieldSize - 1, 'y');
  sim_host_settings::testSetToken(exact);
  GuardedBuffer buf;
  const size_t length =
      sim_host_settings::githubToken(buf.data(), kFirmwareFieldSize);
  checkEq(static_cast<int>(length), static_cast<int>(kFirmwareFieldSize - 1),
          "exact-fit token length");
  checkEq(buf.value(), exact, "exact-fit token is copied whole");
  check(!(length > kFirmwareFieldSize - 1),
        "an exact fit must not read as truncated");
  check(buf.guardsIntact(), "exact-fit token did not write outside the field");
}

// A degenerate destination. Nothing calls it this way today, but the signature
// permits it and a crash inside a credential path is the worst place to find
// out.
void testDegenerateBufferIsSafe() {
  sim_host_settings::testSetToken("something");
  checkEq(static_cast<int>(sim_host_settings::githubToken(nullptr, 0)), 9,
          "null buffer still reports the length");
  char one[1] = {'Z'};
  checkEq(static_cast<int>(sim_host_settings::githubToken(one, 1)), 9,
          "one-byte buffer still reports the length");
  checkEq(std::string(one), "", "one-byte buffer holds only the terminator");
}

// The phone HAS a place to type it, so the "no token" screen must say so. This
// is the half that is not about the value at all: a build with a surface and an
// empty field needs a different sentence from a build with no surface, and
// getting it wrong is what shipped -- "Set githubToken in settings.json" on a
// device with no way to open settings.json.
void testHostAdvertisesItsSurface() {
  check(sim_host_settings::hasSettingsSurface(),
        "a host backend must advertise its settings surface");
}

#else

// The desktop's inline arm. Unset -- which is the only state the canary and
// every existing headless capture ever see -- every call folds to 0 and nothing
// about the existing behavior moves.
void testDesktopIsUnsetByDefault() {
  unsetenv(sim_host_settings::kGithubTokenEnvVar);
  GuardedBuffer buf;
  checkEq(static_cast<int>(
              sim_host_settings::githubToken(buf.data(), kFirmwareFieldSize)),
          0, "no env var means no token");
  checkEq(buf.value(), "", "no env var leaves the buffer empty");
  check(!sim_host_settings::hasSettingsSurface(),
        "the desktop has no settings surface to send the owner to");
}

// The QA hatch. It is what lets the authenticated path be driven headlessly
// without writing a credential into the simulated card, and it is deliberately
// NOT a settings surface: the sentence the no-token screen prints has to name
// somewhere the owner can go, and on the desktop that is settings.json.
void testDesktopEnvHatchCarriesAValue() {
  setenv(sim_host_settings::kGithubTokenEnvVar, "fake-token-for-the-test", 1);
  GuardedBuffer buf;
  checkEq(static_cast<int>(
              sim_host_settings::githubToken(buf.data(), kFirmwareFieldSize)),
          23, "env token length");
  checkEq(buf.value(), "fake-token-for-the-test", "env token bytes");
  check(!sim_host_settings::hasSettingsSurface(),
        "the env hatch must not claim to be a settings surface");
  check(buf.guardsIntact(), "env token did not write outside the field");

  // An empty variable is not a token. getenv() returns "" for `FOO=`, and
  // treating that as configured would send "Authorization: Bearer " and get a
  // 401 in place of the NO_TOKEN screen.
  setenv(sim_host_settings::kGithubTokenEnvVar, "", 1);
  checkEq(static_cast<int>(
              sim_host_settings::githubToken(buf.data(), kFirmwareFieldSize)),
          0, "an empty env var is not a token");

  unsetenv(sim_host_settings::kGithubTokenEnvVar);
}

void testDesktopEnvHatchTruncates() {
  const std::string oversize(kFirmwareFieldSize + 17, 'q');
  setenv(sim_host_settings::kGithubTokenEnvVar, oversize.c_str(), 1);
  GuardedBuffer buf;
  const size_t length =
      sim_host_settings::githubToken(buf.data(), kFirmwareFieldSize);
  checkEq(static_cast<int>(length), static_cast<int>(oversize.size()),
          "oversize env token reports its real length");
  checkEq(static_cast<int>(buf.value().size()),
          static_cast<int>(kFirmwareFieldSize - 1),
          "oversize env token is cut to the field");
  check(buf.guardsIntact(),
        "oversize env token did not write outside the field");
  unsetenv(sim_host_settings::kGithubTokenEnvVar);
}

// ----------------------------------------------------------- text gates ---
//
// The two halves that no compiler can see, and both failure modes are silent.

// The NSUserDefaults key in ios/CrossPointHostSettings.mm has to be the Key of
// the PSTextFieldSpecifier in Root.plist. A typo is invisible:
// -stringForKey: answers nil, the owner sees "not configured" having just typed
// a token, and nothing in any log says why.
void testPlistKeyMatchesTheBackend(const std::string &iosDir) {
  const std::string backend = slurp(iosDir + "/CrossPointHostSettings.mm");
  const std::string plist = slurp(iosDir + "/Settings.bundle/Root.plist");
  if (backend.empty() || plist.empty()) {
    std::printf("FAIL: pass the ios/ directory as argv[1], or run from the "
                "repo root\n");
    testcheck::g_failures++;
    return;
  }

  check(backend.find("@\"githubToken\"") != std::string::npos,
        "ios/CrossPointHostSettings.mm reads the key @\"githubToken\"");
  check(plist.find("<string>githubToken</string>") != std::string::npos,
        "Root.plist carries a row whose Key is githubToken");
  check(plist.find("<string>PSTextFieldSpecifier</string>") !=
            std::string::npos,
        "the token row is a text field -- nothing else in a Settings.bundle "
        "can take a typed string");

  // IsSecure, so iOS masks it while it is typed and keeps it out of QuickType.
  // Checked as a pair on the same row rather than anywhere in the file, since
  // this is the only secure field in the bundle.
  const size_t keyAt = plist.find("<string>githubToken</string>");
  const size_t rowStart = plist.rfind("<dict>", keyAt);
  const size_t rowEnd = plist.find("</dict>", keyAt);
  const bool bounded = rowStart != std::string::npos &&
                       rowEnd != std::string::npos && rowStart < rowEnd;
  check(bounded, "the token row is a well-formed dict");
  if (bounded) {
    const std::string row = plist.substr(rowStart, rowEnd - rowStart);
    check(row.find("<key>IsSecure</key>\n\t\t\t<true/>") != std::string::npos,
          "the token row is IsSecure, so iOS masks what is typed into it");
  }
}

// NOBODY MAY LOG THE TOKEN. The value passes through two files in this repo and
// one in the firmware; a printf of it in any of them would put a credential in
// a log the owner might paste into a bug report. Checked as text because there
// is no compiler diagnostic for "this string happens to be a secret".
void testNothingLogsTheToken(const std::string &iosDir) {
  const std::string backend = slurp(iosDir + "/CrossPointHostSettings.mm");
  if (backend.empty()) return;  // reported by the gate above
  const char *loggers[] = {"NSLog", "printf", "fprintf", "SDL_Log", "LOG_"};
  for (const char *fn : loggers) {
    check(backend.find(fn) == std::string::npos,
          std::string("ios/CrossPointHostSettings.mm must not call ") + fn +
              " -- it holds the raw token");
  }
}

#endif

}  // namespace

int main(int argc, char **argv) {
#if CROSSPOINT_SIM_HOST_SETTINGS
  (void)argc;
  (void)argv;
  testHostTokenArrives();
  testEmptyHostTokenReadsAsUnset();
  testOversizeTokenTruncatesAndReportsIt();
  testExactFitIsNotTruncated();
  testDegenerateBufferIsSafe();
  testHostAdvertisesItsSurface();
#else
  const std::string iosDir = argc > 1 ? argv[1] : "ios";
  testDesktopIsUnsetByDefault();
  testDesktopEnvHatchCarriesAValue();
  testDesktopEnvHatchTruncates();
  testPlistKeyMatchesTheBackend(iosDir);
  testNothingLogsTheToken(iosDir);
#endif

  if (testcheck::g_failures != 0) {
    std::printf("host_settings: %d failure(s)\n", testcheck::g_failures);
    return 1;
  }
  std::printf("host_settings: all checks passed\n");
  return 0;
}
