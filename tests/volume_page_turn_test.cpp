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
using volumepage::gestureFor;
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
  // WHICH ROW, not which button. Since 2026-09-06 the rocker fires the
  // gestureVolumeUp / gestureVolumeDown bindings; what those do is the
  // owner's, and "flipped" is assigning them the other way round rather than
  // a setting this header knows about.
  check(gestureFor(Verdict::Next) == gesturebind::Gesture::VolumeUp,
        "a Next verdict is the Volume Up row");
  check(gestureFor(Verdict::Prev) == gesturebind::Gesture::VolumeDown,
        "a Prev verdict is the Volume Down row");
  check(gestureFor(Verdict::None) == gesturebind::Gesture::Count,
        "None is no row at all");
  check(gestureFor(Verdict::Echo) == gesturebind::Gesture::Count,
        "an Echo is the restore being read back and must fire nothing");

  // THE SESSION IS HELD ONLY WHILE A ROW IS BOUND. Taking the rocker over
  // unasked is the thing App Store review has rejected apps for.
  auto none = [](gesturebind::Gesture) { return gesturebind::Action::Nothing; };
  check(!volumepage::needsVolumeSession(none),
        "both rows Nothing: no audio session, rocker left alone");
  auto up = [](gesturebind::Gesture g) {
    return g == gesturebind::Gesture::VolumeUp ? gesturebind::Action::Right
                                               : gesturebind::Action::Nothing;
  };
  check(volumepage::needsVolumeSession(up), "one bound row arms the session");
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

  // THE TWO OLD ROWS MUST BE GONE. They were retired 2026-09-06 when the
  // rocker became two ordinary gesture rows; a leftover row would offer a
  // switch that no longer reaches anything, which is worse than no switch.
  for (const char *dead : {"volumeButtonsTurnPages", "volumeButtonsFlipped"}) {
    check(plist.find(std::string("<string>") + dead + "</string>") == std::string::npos,
          std::string("Root.plist no longer carries ") + dead);
    check(prefs.find(std::string("@\"") + dead + "\"") == std::string::npos,
          std::string("CrossPointPrefs.mm no longer registers ") + dead);
  }
  check(prefsH.find("int CrossPointPrefs_volumeButtonsTurnPages(void);") == std::string::npos &&
            prefsH.find("int CrossPointPrefs_volumeButtonsFlipped(void);") == std::string::npos,
        "CrossPointPrefs.h no longer declares either retired accessor");

  // AND THE TWO NEW ROWS MUST EXIST, generated from the header like every
  // other gesture row.
  for (const char *row : {"gestureVolumeUp", "gestureVolumeDown"}) {
    check(plist.find(std::string("<string>") + row + "</string>") != std::string::npos,
          std::string("Root.plist carries the ") + row + " row");
  }

  // The adapter routes a press through the gesture dispatch rather than
  // injecting a hardcoded front-rocker button behind the zen gate.
  check(adapter.find("CrossPointZenRecognizers_fireGesture") != std::string::npos,
        "the adapter fires the bound row, not a button");
  check(adapter.find("volumepage::gestureFor(v)") != std::string::npos,
        "the adapter asks volumepage which row a verdict is");
  check(adapter.find("CrossPointPrefs_volumeButtons") == std::string::npos,
        "the adapter reads neither retired pref");

}

}  // namespace

int main(int argc, char **argv) {
  testDirection();
  testRestingLevel();
  testShippedSources(argc > 1 ? argv[1] : "ios");
  if (testcheck::g_failures) {
    std::printf("volume_page_turn_test: %d FAILED\n", testcheck::g_failures);
    return 1;
  }
  std::puts("volume_page_turn_test: all checks passed");
  return 0;
}
