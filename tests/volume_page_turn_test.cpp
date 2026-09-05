// volumepage:: -- the hardware volume rocker as the firmware's page rocker
// (ios/VolumePageTurn.h), and the Settings.bundle row that switches it on.
//
// WHY THIS IS A HOST TEST
//
// The mechanism on the phone is AVAudioSession.outputVolume observed by KVO,
// with the level put back through a hidden MPVolumeView slider after every
// press. None of that exists on a host, and none of it can be driven from the
// iOS Simulator either (simctl cannot press a volume button). What CAN be
// driven is the decision every one of those events is fed into: which way did
// the level move, is this our own restore coming back, and where should the
// level rest so the next press still registers. Every failure mode is silent
// on a device -- a page turned the wrong way, a page turned and immediately
// turned back, a rocker that quietly stops working at full volume -- so the
// rule is pinned here.
//
// It also reads the shipped Root.plist and the two .mm files as TEXT: the row's
// DefaultValue must be the header's kDefaultEnabled (CrossPointPrefs.mm builds
// its registration domain from that plist, so a disagreement is a switch that
// displays one thing and behaves as another), the key the backend reads must
// be the key the row writes (a typo is a preference nothing reads), and the
// adapter must inject through gpio.queueButtonTap -- the one route an edge
// raised outside HalGPIO::update() is visible to the firmware.
//
// Build:
//   c++ -std=c++17 -Iios -o /tmp/vpt tests/volume_page_turn_test.cpp && /tmp/vpt

#include "VolumePageTurn.h"

#include <cstdio>
#include <fstream>
#include <sstream>
#include <string>

#include "TestCheck.h"

using testcheck::check;
using volumepage::buttonFor;
using volumepage::judge;
using volumepage::restingLevel;
using volumepage::Verdict;

namespace {

std::string slurp(const std::string &path) {
  std::ifstream in(path);
  if (!in) return {};
  std::ostringstream ss;
  ss << in.rdbuf();
  return ss.str();
}

// The <dict>...</dict> of the specifier whose Key is `key`, or empty. Same
// shape as gesture_bindings_test.cpp's reader.
std::string specifierFor(const std::string &xml, const std::string &key) {
  const std::string needle = "<string>" + key + "</string>";
  const size_t at = xml.find(needle);
  if (at == std::string::npos) return {};
  const size_t open = xml.rfind("<dict>", at);
  const size_t close = xml.find("</dict>", at);
  if (open == std::string::npos || close == std::string::npos) return {};
  return xml.substr(open, close - open);
}

void testDirection() {
  const float rest = 0.5f;
  // --- one press each way, nothing pending ---
  check(judge(rest, rest + volumepage::kStep, false, rest) == Verdict::Next,
        "volume up is page forward (Next)");
  check(judge(rest, rest - volumepage::kStep, false, rest) == Verdict::Prev,
        "volume down is page back (Prev)");
  check(judge(rest, rest, false, rest) == Verdict::None,
        "the same level again is nothing");
  check(judge(rest, rest + 0.001f, false, rest) == Verdict::None,
        "float noise below kEpsilon is nothing");

  // --- the restore's echo ---
  // After an up press the adapter writes `rest` back to the slider; the KVO
  // event that write produces carries `rest` and must NOT be read as a down
  // press, or every page turn would be followed by a turn back.
  check(judge(rest + volumepage::kStep, rest, true, rest) == Verdict::Echo,
        "the restore write's own KVO event is an Echo, not Prev");
  check(judge(rest - volumepage::kStep, rest, true, rest) == Verdict::Echo,
        "...in the other direction too, not Next");
  // With no restore pending, the same arrival IS a press: the owner pressed
  // down from a step above the resting level and landed on it.
  check(judge(rest + volumepage::kStep, rest, false, rest) == Verdict::Prev,
        "landing on the resting level with nothing pending is a real press");
  // A press that arrives while a restore is pending but does NOT land on the
  // resting level is a press (the second of two quick presses).
  check(judge(rest + volumepage::kStep, rest + 2 * volumepage::kStep, true,
              rest) == Verdict::Next,
        "a second quick up press is still Next while the restore is pending");

  // --- a finer step than the phone's (a headset route) still reads ---
  check(judge(rest, rest + 0.02f, false, rest) == Verdict::Next,
        "a step finer than 1/16 but above kEpsilon is still a press");

  // --- the mapping the owner asked for, against HalGPIO's numbering ---
  check(buttonFor(Verdict::Next) == volumepage::kBtnRight,
        "Next presses the front RIGHT button (3)");
  check(buttonFor(Verdict::Prev) == volumepage::kBtnLeft,
        "Prev presses the front LEFT button (2)");
  check(buttonFor(Verdict::None) == volumepage::kNoButton, "None presses nothing");
  check(buttonFor(Verdict::Echo) == volumepage::kNoButton, "Echo presses nothing");
  check(volumepage::kBtnLeft == 2 && volumepage::kBtnRight == 3,
        "the button indices are HalGPIO's BTN_LEFT=2 / BTN_RIGHT=3 (the .mm "
        "static_asserts the same)");

  // --- the default (unflipped) call shape must keep compiling unchanged ---
  // buttonFor's second parameter defaults to false, so every call above --
  // written before Flip Volume Buttons existed -- still means "unflipped".
  check(buttonFor(Verdict::Next) == buttonFor(Verdict::Next, false),
        "the one-argument call is the same as passing flipped=false");
}

// The Flip Volume Buttons truth table: flipping swaps which PHYSICAL button a
// verdict fires, and nothing else -- judge() above never sees the flip, so a
// direction is still read off the sign of the level change exactly as before.
// Only the OUTPUT side of buttonFor() is under test here.
void testFlipped() {
  check(buttonFor(Verdict::Next, false) == volumepage::kBtnRight,
        "unflipped: Next is still the front RIGHT button");
  check(buttonFor(Verdict::Prev, false) == volumepage::kBtnLeft,
        "unflipped: Prev is still the front LEFT button");
  check(buttonFor(Verdict::Next, true) == volumepage::kBtnLeft,
        "flipped: Next (volume up) becomes the front LEFT button (previous "
        "page)");
  check(buttonFor(Verdict::Prev, true) == volumepage::kBtnRight,
        "flipped: Prev (volume down) becomes the front RIGHT button (next "
        "page)");
  check(buttonFor(Verdict::None, true) == volumepage::kNoButton,
        "flipped: None still presses nothing");
  check(buttonFor(Verdict::Echo, true) == volumepage::kNoButton,
        "flipped: Echo still presses nothing");
  // Flipping is never a no-op button-for-button -- the whole point is that it
  // swaps the two real presses.
  check(buttonFor(Verdict::Next, true) != buttonFor(Verdict::Next, false),
        "flipping actually changes Next's button");
  check(buttonFor(Verdict::Prev, true) != buttonFor(Verdict::Prev, false),
        "flipping actually changes Prev's button");
}

void testRestingLevel() {
  // The ends are dead ends: a press further in that direction changes nothing
  // and produces no event. Arming there moves the level to the middle.
  check(restingLevel(0.0f) == volumepage::kMidLevel, "0.0 rests at the middle");
  check(restingLevel(1.0f) == volumepage::kMidLevel, "1.0 rests at the middle");
  check(restingLevel(0.999f) == volumepage::kMidLevel,
        "float slop under 1.0 is still the end");
  check(restingLevel(0.001f) == volumepage::kMidLevel,
        "float slop over 0.0 is still the end");
  // Anything with a step of room on both sides is left where the owner had it.
  check(restingLevel(0.5f) == 0.5f, "the middle stays put");
  check(restingLevel(volumepage::kStep) == volumepage::kStep,
        "one notch above silent stays put (a down press still changes it)");
  check(restingLevel(1.0f - volumepage::kStep) == 1.0f - volumepage::kStep,
        "one notch below full stays put (an up press still changes it)");
  check(volumepage::kEndMargin < volumepage::kStep,
        "kEndMargin is under one step, so no legal non-end level is clamped");

  // THE SWEEP: from every resting level the clamp can produce, a press in
  // EITHER direction produces a level that judge() reads as that press. This
  // is the property the whole feature stands on -- a resting level from which
  // one direction is silent is a rocker with one working button.
  for (int i = 0; i <= 16; ++i) {
    const float observed = i * volumepage::kStep;
    const float rest = restingLevel(observed);
    float up = rest + volumepage::kStep;
    float down = rest - volumepage::kStep;
    if (up > 1.0f) up = 1.0f;
    if (down < 0.0f) down = 0.0f;
    char what[96];
    std::snprintf(what, sizeof what, "from %d/16 (rests at %.4f) up reads Next",
                  i, rest);
    check(judge(rest, up, false, rest) == Verdict::Next, what);
    std::snprintf(what, sizeof what, "from %d/16 (rests at %.4f) down reads Prev",
                  i, rest);
    check(judge(rest, down, false, rest) == Verdict::Prev, what);
  }
}

// The shipped Root.plist row, and the two files that read and act on it.
void testShippedSources(const std::string &iosDir) {
  const std::string plist = slurp(iosDir + "/Settings.bundle/Root.plist");
  const std::string prefs = slurp(iosDir + "/CrossPointPrefs.mm");
  const std::string prefsH = slurp(iosDir + "/CrossPointPrefs.h");
  const std::string adapter = slurp(iosDir + "/CrossPointVolumeButtons.mm");
  const std::string cmake = slurp(iosDir + "/CMakeLists.txt");
  if (plist.empty() || prefs.empty() || prefsH.empty() || adapter.empty() ||
      cmake.empty()) {
    std::printf("FAIL: pass the ios/ directory as argv[1], or run from the "
                "repo root\n");
    testcheck::g_failures++;
    return;
  }

  const std::string key = volumepage::kPrefKey;
  const std::string spec = specifierFor(plist, key);
  check(!spec.empty(), "Root.plist carries a row whose Key is " + key);
  if (!spec.empty()) {
    check(spec.find("<string>PSToggleSwitchSpecifier</string>") !=
              std::string::npos,
          "the row is a toggle");
    // DefaultValue must BE kDefaultEnabled: Settings.app shows it for an
    // untouched key and CrossPointPrefs.mm registers it as what the app reads.
    const char *want = volumepage::kDefaultEnabled ? "<true/>" : "<false/>";
    const size_t dv = spec.find("<key>DefaultValue</key>");
    check(dv != std::string::npos && spec.find(want, dv) != std::string::npos,
          std::string("the row's DefaultValue is ") + want +
              " (volumepage::kDefaultEnabled)");
  }
  // OUTSIDE the generated gesture span: tools/gen_gesture_plist.py rewrites
  // everything between the Zen Mode switch and the Screen group, so a row
  // placed there would be deleted by its next run.
  const size_t screenAt = plist.find("<string>Screen</string>");
  const size_t rowAt = plist.find("<string>" + key + "</string>");
  check(screenAt != std::string::npos && rowAt != std::string::npos &&
            rowAt > screenAt,
        "the row sits after the Screen group, outside the generated span");

  // The backend reads the same key the row writes.
  check(prefs.find("@\"" + key + "\"") != std::string::npos,
        "ios/CrossPointPrefs.mm names the key @\"" + key + "\"");
  check(prefsH.find("int CrossPointPrefs_volumeButtonsTurnPages(void);") !=
            std::string::npos,
        "CrossPointPrefs.h declares CrossPointPrefs_volumeButtonsTurnPages");
  check(adapter.find("CrossPointPrefs_volumeButtonsTurnPages()") !=
            std::string::npos,
        "the adapter reads the setting through CrossPointPrefs");

  // Flip Volume Buttons: the same row, same group, same pinning as the toggle
  // above, for tools/gen_gesture_plist.py's span and for the key match between
  // the plist and the backend.
  const std::string flipKey = volumepage::kFlippedPrefKey;
  const std::string flipSpec = specifierFor(plist, flipKey);
  check(!flipSpec.empty(), "Root.plist carries a row whose Key is " + flipKey);
  if (!flipSpec.empty()) {
    check(flipSpec.find("<string>PSToggleSwitchSpecifier</string>") !=
              std::string::npos,
          "the flip row is a toggle");
    const char *flipWant = volumepage::kDefaultFlipped ? "<true/>" : "<false/>";
    const size_t flipDv = flipSpec.find("<key>DefaultValue</key>");
    check(flipDv != std::string::npos &&
              flipSpec.find(flipWant, flipDv) != std::string::npos,
          std::string("the flip row's DefaultValue is ") + flipWant +
              " (volumepage::kDefaultFlipped)");
  }
  const size_t flipRowAt = plist.find("<string>" + flipKey + "</string>");
  check(screenAt != std::string::npos && flipRowAt != std::string::npos &&
            flipRowAt > screenAt,
        "the flip row also sits after the Screen group, outside the "
        "generated span");
  // Same group as the enable toggle: no OTHER PSGroupSpecifier's Title sits
  // between the two rows.
  check(rowAt != std::string::npos && flipRowAt != std::string::npos &&
            plist.find("PSGroupSpecifier", rowAt) > flipRowAt,
        "the flip row sits in the same group as volumeButtonsTurnPages (no "
        "group boundary between them)");

  check(prefs.find("@\"" + flipKey + "\"") != std::string::npos,
        "ios/CrossPointPrefs.mm names the key @\"" + flipKey + "\"");
  check(prefsH.find("int CrossPointPrefs_volumeButtonsFlipped(void);") !=
            std::string::npos,
        "CrossPointPrefs.h declares CrossPointPrefs_volumeButtonsFlipped");
  check(adapter.find("CrossPointPrefs_volumeButtonsFlipped()") !=
            std::string::npos,
        "the adapter reads the flip setting through CrossPointPrefs");
  check(adapter.find("volumepage::buttonFor(v, flipped)") != std::string::npos,
        "the adapter passes the live flip setting into buttonFor()");

  // The injection route. queueButtonTap is the ONE way an edge raised outside
  // HalGPIO::update() reaches the firmware (HalGPIO.h says why: beginFrame()
  // wipes the latches, and a per-frame hook runs after loop()). A direct
  // injectButtonDown from the KVO path would compile, log a press, and turn
  // no page.
  check(adapter.find("gpio.queueButtonTap(") != std::string::npos,
        "the adapter injects through gpio.queueButtonTap");
  check(adapter.find("injectButtonDown") == std::string::npos,
        "the adapter never calls injectButtonDown directly");
  check(adapter.find("volumepage::kBtnLeft == HalGPIO::BTN_LEFT") !=
                std::string::npos &&
            adapter.find("volumepage::kBtnRight == HalGPIO::BTN_RIGHT") !=
                std::string::npos,
        "the adapter static_asserts the header's indices against HalGPIO");

  // The two frameworks the adapter imports have to be linked by name, the
  // same way AVFoundation is for read-aloud; a missing MediaPlayer is a link
  // error nobody sees until the Mac builds it.
  check(adapter.find("#import <MediaPlayer/MediaPlayer.h>") != std::string::npos,
        "the adapter imports MediaPlayer (MPVolumeView)");
  check(adapter.find("#import <AVFoundation/AVFoundation.h>") !=
            std::string::npos,
        "the adapter imports AVFoundation (AVAudioSession)");
  check(cmake.find("\"-framework MediaPlayer\"") != std::string::npos,
        "ios/CMakeLists.txt links MediaPlayer");
  check(cmake.find("CrossPointVolumeButtons.mm") != std::string::npos,
        "ios/CMakeLists.txt compiles the adapter");
}

}  // namespace

int main(int argc, char **argv) {
  testDirection();
  testFlipped();
  testRestingLevel();
  testShippedSources(argc > 1 ? argv[1] : "ios");
  if (testcheck::g_failures) {
    std::printf("volume_page_turn_test: %d FAILED\n", testcheck::g_failures);
    return 1;
  }
  std::puts("volume_page_turn_test: all checks passed");
  return 0;
}
