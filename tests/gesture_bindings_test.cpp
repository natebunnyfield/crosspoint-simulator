// WHAT EVERY GESTURE DOES -- the truth table for ios/GestureBindings.h.
//
// Owner ruling 2026-08-28 (T-025): the gestures became configurable from
// Settings.app, in three groups (above the paper, below the paper,
// multi-finger), with the paper itself fixed.
//
// Every failure mode of that rule is SILENT on a device and none of them can be
// reproduced off-device at all, because UIKit's recognizers live above SDL where
// neither an input script nor simctl can synthesize a touch. So this is a truth
// table, and it pins the five things the owner named plus the one that matters
// most:
//
//  1. EVERY DEFAULT IS BUILD 156'S BEHAVIOR. An install that never opens the
//     setting must behave identically to the build before it existed. Each
//     default is asserted against the live mapping it replaces, by name.
//  2. AN UNBOUND GESTURE FIRES NOTHING -- and "nothing" must not fall back to
//     the default, which is the obvious way to write this wrong.
//  3. TWO GESTURES MAY SHARE ONE ACTION. No conflict detection, no moving.
//  4. CLEARING EVERY ZEN BINDING IS PERMITTED. No guard, by ruling.
//  5. THE ZONE BOUNDARIES are g_cardTopPx and the paper's bottom, and the
//     on-paper behavior is untouched and unconfigurable.
//  6. ZEN SCOPE IS A PROPERTY OF THE GESTURE, NEVER OF THE ACTION.
//
// Plus the two drift gates no static_assert can do: the stored integers (a
// preset persists as an integer, so re-pointing one silently changes what a
// saved choice selects) and the shipped Root.plist, which the compiler never
// opens -- every row's key, its DefaultValue and the actions it offers.

#include <cassert>
#include <cstdio>
#include <fstream>
#include <set>
#include <sstream>
#include <string>
#include <vector>

#include "../ios/GestureBindings.h"

using gesturebind::Action;
using gesturebind::Gesture;
using gesturebind::OneFinger;
using gesturebind::Zone;

static int failures = 0;

static void check(bool ok, const char* what) {
  if (!ok) {
    std::printf("  FAIL: %s\n", what);
    failures++;
  }
}

static void checkAction(Action got, Action want, const char* what) {
  if (got != want) {
    std::printf("  FAIL: %s (got '%s', want '%s')\n", what,
                gesturebind::actionName(got), gesturebind::actionName(want));
    failures++;
  }
}

static int stored(Action a) { return static_cast<int>(a); }

// --- 1. THE DEFAULTS ARE TODAY'S BEHAVIOR ----------------------------------
//
// The right-hand column of each line is the live mapping this default replaces.
// If one of these ever has to change, it is because the app's behavior changed
// first, and the recognizer is the thing to read.
static void testDefaultsMatchToday() {
  // CrossPointZenRecognizers.mm swipe:, one finger. "reading on one finger"
  // (owner 2026-08-22): a swipe LEFT pages FORWARD, which is the front RIGHT
  // button. Neither the swipes nor the SDL deliberate tap was zone-aware, so
  // all three zones answered the same and the above/below pairs are identical.
  checkAction(gesturebind::defaultAction(Gesture::SwipeLeftAbove), Action::Right,
              "1-swipe left above the paper defaults to page forward");
  checkAction(gesturebind::defaultAction(Gesture::SwipeLeftBelow), Action::Right,
              "1-swipe left below the paper defaults to page forward");
  checkAction(gesturebind::defaultAction(Gesture::SwipeRightAbove), Action::Left,
              "1-swipe right above the paper defaults to page back");
  checkAction(gesturebind::defaultAction(Gesture::SwipeRightBelow), Action::Left,
              "1-swipe right below the paper defaults to page back");

  // CrossPointIOSShim.cpp padWatch, Verb::Down -> BTN_RIGHT.
  checkAction(gesturebind::defaultAction(Gesture::TapAbove), Action::Right,
              "the deliberate tap above the paper defaults to page forward");
  checkAction(gesturebind::defaultAction(Gesture::TapBelow), Action::Right,
              "the deliberate tap below the paper defaults to page forward");

  // ZenHoldRouting.h: above the paper -> Toggle, on it -> Select. The old rule
  // had only two zones, so everything at or below the paper's top edge selected
  // -- the strip below the paper included.
  checkAction(gesturebind::defaultAction(Gesture::HoldAbove), Action::ToggleZen,
              "the hold above the paper defaults to the zen toggle");
  checkAction(gesturebind::defaultAction(Gesture::HoldBelow), Action::Confirm,
              "the hold below the paper defaults to select");

  // swipe:, two fingers. "sizing on two": left is font +1 (BTN_DOWN), right is
  // font -1 (BTN_UP), up is back, down is select.
  checkAction(gesturebind::defaultAction(Gesture::TwoFingerSwipeLeft),
              Action::Down, "2-swipe left defaults to the side DOWN button");
  checkAction(gesturebind::defaultAction(Gesture::TwoFingerSwipeRight),
              Action::Up, "2-swipe right defaults to the side UP button");
  checkAction(gesturebind::defaultAction(Gesture::TwoFingerSwipeUp),
              Action::Back, "2-swipe up defaults to back");
  checkAction(gesturebind::defaultAction(Gesture::TwoFingerSwipeDown),
              Action::Confirm, "2-swipe down defaults to select");

  // twoTap:, threeTap:, fourTap:, pinch:, CPXShakeCatcher motionEnded:.
  checkAction(gesturebind::defaultAction(Gesture::TwoFingerTap), Action::Confirm,
              "2-finger tap defaults to select");
  checkAction(gesturebind::defaultAction(Gesture::ThreeFingerTap),
              Action::ToggleZen, "3-finger tap defaults to the zen toggle");
  checkAction(gesturebind::defaultAction(Gesture::FourFingerTap), Action::Power,
              "4-finger tap defaults to power");
  checkAction(gesturebind::defaultAction(Gesture::Pinch), Action::Up,
              "pinch defaults to the side UP button");
  checkAction(gesturebind::defaultAction(Gesture::Spread), Action::Down,
              "spread defaults to the side DOWN button");
  checkAction(gesturebind::defaultAction(Gesture::Shake),
              Action::FontFamilyStep, "shake defaults to the font family step");

  // ...and no gesture defaults to Nothing. Every one of them DID something
  // before this setting existed; a default of Nothing would be a capability
  // removed by the act of making it configurable.
  for (int i = 0; i < gesturebind::kGestureCount; ++i) {
    const Gesture g = static_cast<Gesture>(i);
    check(gesturebind::defaultAction(g) != Action::Nothing,
          gesturebind::gestureName(g));
    check(gesturebind::defaultAction(g) != Action::Unset,
          gesturebind::gestureName(g));
  }

  // AN UNTOUCHED STORE IS AN UNTOUCHED APP. -integerForKey: answers 0 for a key
  // nobody has written and for one whose registration domain never loaded; both
  // must render the app exactly as it shipped, which is the whole reason 0 is
  // Unset rather than Nothing.
  for (int i = 0; i < gesturebind::kGestureCount; ++i) {
    const Gesture g = static_cast<Gesture>(i);
    checkAction(gesturebind::resolve(g, 0), gesturebind::defaultAction(g),
                gesturebind::gestureName(g));
    // ...and so must junk: a restored backup, a hand-edited plist, a row a
    // later build removed.
    checkAction(gesturebind::resolve(g, -7), gesturebind::defaultAction(g),
                gesturebind::gestureName(g));
    checkAction(gesturebind::resolve(g, 9999), gesturebind::defaultAction(g),
                gesturebind::gestureName(g));
  }

  // The on-paper behavior is fixed and is the same behavior, stated where no
  // setting can reach it.
  checkAction(gesturebind::onPaperAction(OneFinger::Tap, true), Action::Right,
              "a tap ON the paper still pages forward");
  checkAction(gesturebind::onPaperAction(OneFinger::SwipeLeft, true),
              Action::Right, "a swipe left ON the paper still pages forward");
  checkAction(gesturebind::onPaperAction(OneFinger::SwipeRight, true),
              Action::Left, "a swipe right ON the paper still pages back");
  checkAction(gesturebind::onPaperAction(OneFinger::Hold, true), Action::Confirm,
              "a hold ON the paper still selects");
  // ...and none of it outside zen, exactly as before: no stray CONFIRM, no page
  // turn from a finger that belongs to the pad.
  for (int k = 0; k <= 3; ++k)
    checkAction(gesturebind::onPaperAction(static_cast<OneFinger>(k), false),
                Action::Nothing, "nothing ON the paper while zen is off");
}

// --- 2. AN UNBOUND GESTURE FIRES NOTHING -----------------------------------
static void testUnbound() {
  for (int i = 0; i < gesturebind::kGestureCount; ++i) {
    const Gesture g = static_cast<Gesture>(i);
    // REGRESSION GUARD: the obvious wrong implementation treats "Nothing" as
    // "no value stored" and hands back the default, so clearing a binding would
    // silently do nothing at all -- a setting that shows as set and is not.
    checkAction(gesturebind::resolve(g, stored(Action::Nothing)),
                Action::Nothing, gesturebind::gestureName(g));
    checkAction(gesturebind::actionFor(g, true, stored(Action::Nothing)),
                Action::Nothing, gesturebind::gestureName(g));
  }
  check(gesturebind::buttonFor(Action::Nothing) == gesturebind::kNoButton,
        "Nothing presses no button");
  check(gesturebind::buttonFor(Action::ToggleZen) == gesturebind::kNoButton,
        "the zen toggle presses no button");
  check(gesturebind::buttonFor(Action::FontFamilyStep) ==
            gesturebind::kNoButton,
        "the font family step presses no button");
}

// --- 3. TWO GESTURES MAY SHARE ONE ACTION ----------------------------------
static void testSharing() {
  // No conflict detection anywhere: each gesture resolves independently and
  // nothing here can see what another holds. Pointing the 2- and 4-finger taps
  // at the same button leaves BOTH holding it.
  checkAction(gesturebind::actionFor(Gesture::TwoFingerTap, true,
                                     stored(Action::Confirm)),
              Action::Confirm, "2-finger tap keeps CONFIRM");
  checkAction(gesturebind::actionFor(Gesture::FourFingerTap, true,
                                     stored(Action::Confirm)),
              Action::Confirm, "4-finger tap keeps CONFIRM too");
  // Including the zen toggle on several gestures at once.
  checkAction(gesturebind::actionFor(Gesture::ThreeFingerTap, true,
                                     stored(Action::ToggleZen)),
              Action::ToggleZen, "3-finger tap toggles zen");
  checkAction(
      gesturebind::actionFor(Gesture::HoldAbove, true, stored(Action::ToggleZen)),
      Action::ToggleZen, "and so does the hold above the paper");
}

// --- 4. CLEARING EVERY ZEN BINDING IS PERMITTED ----------------------------
static void testZenMayBeLeftUnbound() {
  // Owner ruling 2026-08-28: no guard, no refusal, no warning. If every
  // zen-toggle binding is cleared, zen is unreachable BY GESTURE and that is
  // allowed -- the configuration lives in Settings.app, outside the reader, so
  // it is always recoverable. This test exists so the "missing" guard reads as
  // a decision rather than an oversight, and so nobody adds one back.
  for (int i = 0; i < gesturebind::kGestureCount; ++i) {
    const Gesture g = static_cast<Gesture>(i);
    checkAction(gesturebind::actionFor(g, false, stored(Action::Nothing)),
                Action::Nothing, gesturebind::gestureName(g));
    checkAction(gesturebind::actionFor(g, true, stored(Action::Nothing)),
                Action::Nothing, gesturebind::gestureName(g));
  }
  // Not even the two always-on gestures are special-cased into keeping it.
  checkAction(gesturebind::actionFor(Gesture::ThreeFingerTap, false,
                                     stored(Action::Nothing)),
              Action::Nothing, "the 3-finger tap may be cleared");
  checkAction(gesturebind::actionFor(Gesture::HoldAbove, false,
                                     stored(Action::Nothing)),
              Action::Nothing, "the hold above the paper may be cleared");
}

// --- 5. THE ZONES ----------------------------------------------------------
static void testZones() {
  // An iPhone Air's measured geometry: the card top at 204 device px, the
  // rocker row (the paper's bottom edge in zen) at 852.
  const float top = 204.0f, bottom = 852.0f;
  check(gesturebind::zoneFor(0.0f, top, bottom) == Zone::AbovePaper,
        "y=0 is above the paper");
  check(gesturebind::zoneFor(203.9f, top, bottom) == Zone::AbovePaper,
        "one pixel above the card top is above the paper");
  check(gesturebind::zoneFor(204.0f, top, bottom) == Zone::OnPaper,
        "the card top itself is ON the paper (the boundary is exclusive above)");
  check(gesturebind::zoneFor(851.9f, top, bottom) == Zone::OnPaper,
        "one pixel above the paper's bottom edge is still on it");
  check(gesturebind::zoneFor(852.0f, top, bottom) == Zone::BelowPaper,
        "the paper's bottom edge itself is below the paper");
  check(gesturebind::zoneFor(2000.0f, top, bottom) == Zone::BelowPaper,
        "the bottom of the screen is below the paper");

  // A DEGENERATE BOTTOM EDGE COLLAPSES TO THE OLD TWO-ZONE RULE. Before the
  // first layout pass, and on the tablet path (which publishes no rocker row),
  // the paper's bottom is 0; a third zone must not be invented out of a zero,
  // or every gesture in the lower two thirds of the screen would silently
  // change meaning on the first frame after launch.
  check(gesturebind::zoneFor(1000.0f, top, 0.0f) == Zone::OnPaper,
        "with no measured bottom edge, below the top is ON the paper");
  check(gesturebind::zoneFor(100.0f, top, 0.0f) == Zone::AbovePaper,
        "...and above the top is still above it");
  check(gesturebind::zoneFor(1000.0f, top, top) == Zone::OnPaper,
        "a bottom edge equal to the top edge is not a zone");

  // THE OLD RULE, REPRODUCED. Before T-025 the hold split on g_cardTopPx alone:
  // above -> toggle in either mode, at or below -> select in zen only. With the
  // shipped defaults, both of the new lower zones still answer that.
  const int dTapA = stored(gesturebind::defaultAction(Gesture::HoldAbove));
  const int dTapB = stored(gesturebind::defaultAction(Gesture::HoldBelow));
  checkAction(gesturebind::oneFingerAction(OneFinger::Hold, Zone::AbovePaper,
                                           false, dTapA),
              Action::ToggleZen, "hold above, zen OFF -> toggle (the way IN)");
  checkAction(gesturebind::oneFingerAction(OneFinger::Hold, Zone::AbovePaper,
                                           true, dTapA),
              Action::ToggleZen, "hold above, zen ON -> toggle (the way OUT)");
  checkAction(
      gesturebind::oneFingerAction(OneFinger::Hold, Zone::OnPaper, true, 0),
      Action::Confirm, "hold on the paper, zen ON -> select");
  checkAction(
      gesturebind::oneFingerAction(OneFinger::Hold, Zone::OnPaper, false, 0),
      Action::Nothing, "hold on the paper, zen OFF -> nothing");
  checkAction(gesturebind::oneFingerAction(OneFinger::Hold, Zone::BelowPaper,
                                           true, dTapB),
              Action::Confirm, "hold below the paper, zen ON -> select");
  checkAction(gesturebind::oneFingerAction(OneFinger::Hold, Zone::BelowPaper,
                                           false, dTapB),
              Action::Nothing, "hold below the paper, zen OFF -> nothing");

  // ON THE PAPER IS NOT CONFIGURABLE, and the store cannot reach it: the same
  // call with a hostile stored value still answers the fixed action.
  checkAction(gesturebind::oneFingerAction(OneFinger::Tap, Zone::OnPaper, true,
                                           stored(Action::Power)),
              Action::Right, "a stored value cannot re-point the paper's tap");
  check(gesturebind::oneFingerGesture(OneFinger::Tap, Zone::OnPaper) ==
            Gesture::Count,
        "there is no settings row for a tap on the paper");
  check(gesturebind::oneFingerGesture(OneFinger::Hold, Zone::OnPaper) ==
            Gesture::Count,
        "there is no settings row for a hold on the paper");

  // Each configurable zone maps to its own row, and no row is shared.
  std::set<int> seen;
  for (int k = 0; k <= 3; ++k) {
    for (Zone z : {Zone::AbovePaper, Zone::BelowPaper}) {
      const Gesture g =
          gesturebind::oneFingerGesture(static_cast<OneFinger>(k), z);
      check(g != Gesture::Count, "every one-finger gesture has a row per zone");
      check(seen.insert(static_cast<int>(g)).second,
            "no two (gesture, zone) pairs share one row");
    }
  }
  check(seen.size() == 8, "eight single-finger rows: four gestures, two zones");
}

// --- 6. ZEN SCOPE IS A PROPERTY OF THE GESTURE -----------------------------
static void testZenScope() {
  // "You configure WHAT a gesture does, never WHEN." Exactly two gestures fire
  // outside zen, and they are the two that can get you into it today.
  int outside = 0;
  for (int i = 0; i < gesturebind::kGestureCount; ++i)
    if (gesturebind::firesOutsideZen(static_cast<Gesture>(i))) outside++;
  check(outside == 2, "exactly two gestures fire outside zen");
  check(gesturebind::firesOutsideZen(Gesture::HoldAbove),
        "the hold above the paper fires outside zen (the way IN)");
  check(gesturebind::firesOutsideZen(Gesture::ThreeFingerTap),
        "the 3-finger tap fires outside zen (the way IN)");

  // REGRESSION GUARD: the scope must not follow the ACTION. Binding a zen-only
  // gesture to the zen toggle must NOT promote it to always-on -- that would be
  // configuring WHEN, and it is the plausible-looking implementation that would
  // quietly make four-finger taps live on every screen in the app.
  checkAction(gesturebind::actionFor(Gesture::FourFingerTap, false,
                                     stored(Action::ToggleZen)),
              Action::Nothing,
              "a zen-only gesture bound to the toggle stays zen-only");
  // ...and the reverse: an always-on gesture bound to an ordinary button stays
  // always-on.
  checkAction(
      gesturebind::actionFor(Gesture::HoldAbove, false, stored(Action::Back)),
      Action::Back, "an always-on gesture bound to BACK still fires out of zen");
  checkAction(gesturebind::actionFor(Gesture::ThreeFingerTap, false,
                                     stored(Action::Power)),
              Action::Power, "...and so does the 3-finger tap");

  // Everything else is silent while zen is off, whatever it holds.
  for (int i = 0; i < gesturebind::kGestureCount; ++i) {
    const Gesture g = static_cast<Gesture>(i);
    if (gesturebind::firesOutsideZen(g)) continue;
    checkAction(gesturebind::actionFor(g, false, stored(Action::Right)),
                Action::Nothing, gesturebind::gestureName(g));
  }
}

// --- 7. THE STORED INTEGERS ------------------------------------------------
static void testStoredIntegers() {
  // A BINDING PERSISTS AS AN INTEGER, so this list APPENDS and never re-points:
  // changing what a number means silently changes what a saved choice selects,
  // and the owner would never see the moment it happened. Pinned by value.
  check(stored(Action::Unset) == 0, "Unset is 0 (an unwritten key)");
  check(stored(Action::Nothing) == 1, "Nothing is 1");
  check(stored(Action::Back) == 2, "Back is 2");
  check(stored(Action::Confirm) == 3, "Confirm is 3");
  check(stored(Action::Left) == 4, "Left is 4");
  check(stored(Action::Right) == 5, "Right is 5");
  check(stored(Action::Up) == 6, "Up is 6");
  check(stored(Action::Down) == 7, "Down is 7");
  check(stored(Action::Power) == 8, "Power is 8");
  check(stored(Action::ToggleZen) == 9, "ToggleZen is 9");
  check(stored(Action::FontFamilyStep) == 10, "FontFamilyStep is 10");

  // The button indices mirror HalGPIO::BTN_*. The recognizer static_asserts the
  // pair across the header boundary; this pins the values themselves.
  check(gesturebind::buttonFor(Action::Back) == 0, "BTN_BACK is 0");
  check(gesturebind::buttonFor(Action::Confirm) == 1, "BTN_CONFIRM is 1");
  check(gesturebind::buttonFor(Action::Left) == 2, "BTN_LEFT is 2");
  check(gesturebind::buttonFor(Action::Right) == 3, "BTN_RIGHT is 3");
  check(gesturebind::buttonFor(Action::Up) == 4, "BTN_UP is 4");
  check(gesturebind::buttonFor(Action::Down) == 5, "BTN_DOWN is 5");
  check(gesturebind::buttonFor(Action::Power) == 6, "BTN_POWER is 6");

  // Keys are unique and non-empty: two rows sharing a key is one setting
  // wearing two labels, and it looks exactly like a row that does not save.
  std::set<std::string> keys;
  for (int i = 0; i < gesturebind::kGestureCount; ++i) {
    const std::string k = gesturebind::key(static_cast<Gesture>(i));
    check(!k.empty(), "every gesture has a key");
    check(keys.insert(k).second, "no two gestures share a key");
  }
  check(gesturebind::kGestureCount == 18,
        "18 configurable gestures: 4 above, 4 below, 10 multi-finger");
  check(gesturebind::kOfferedActionCount == 10,
        "10 offered actions: 7 buttons, Nothing, the zen toggle, the font step");
  check(!gesturebind::isOffered(0),
        "Unset is never offered as a choice -- it is a read-time fallback");
}

// --- 8. THE SHIPPED Root.plist ---------------------------------------------
//
// The half no static_assert can do: Settings.app's rows live in a plist the
// compiler never opens. A row whose Key is misspelled writes a preference
// nothing reads; a row whose DefaultValue disagrees with defaultAction()
// DISPLAYS one thing and BEHAVES as another (CrossPointPrefs.mm derives its
// registration domain from these same DefaultValues, so the two halves have to
// agree or the switch and the app say different things); a row missing an
// action offers a choice the code supports and the owner cannot reach.

static std::string slurp(const char* path) {
  std::ifstream in(path);
  if (!in) return {};
  std::ostringstream ss;
  ss << in.rdbuf();
  return ss.str();
}

// The <dict>...</dict> of the specifier whose Key is `key`, or empty.
static std::string specifierFor(const std::string& xml, const std::string& key) {
  const std::string needle = "<string>" + key + "</string>";
  const size_t at = xml.find(needle);
  if (at == std::string::npos) return {};
  const size_t open = xml.rfind("<dict>", at);
  const size_t close = xml.find("</dict>", at);
  if (open == std::string::npos || close == std::string::npos) return {};
  return xml.substr(open, close - open);
}

// Scalar values inside the <array> that follows `arrayKey`.
static std::vector<std::string> arrayAfter(const std::string& xml,
                                           const char* arrayKey) {
  std::vector<std::string> out;
  const size_t k = xml.find(std::string("<key>") + arrayKey + "</key>");
  if (k == std::string::npos) return out;
  const size_t open = xml.find("<array>", k);
  const size_t close = xml.find("</array>", open);
  if (open == std::string::npos || close == std::string::npos) return out;
  size_t p = open;
  while (true) {
    const size_t s = xml.find('<', p + 1);
    if (s == std::string::npos || s >= close) break;
    const size_t e = xml.find('>', s);
    if (e == std::string::npos) break;
    const std::string tag = xml.substr(s + 1, e - s - 1);
    if (tag == "string" || tag == "integer") {
      const size_t vEnd = xml.find('<', e);
      out.push_back(xml.substr(e + 1, vEnd - e - 1));
      p = vEnd;
    } else {
      p = e;
    }
  }
  return out;
}

// The <integer> that follows `<key>DefaultValue</key>`, or INT_MIN.
static long defaultValueOf(const std::string& spec) {
  const size_t k = spec.find("<key>DefaultValue</key>");
  if (k == std::string::npos) return -999999;
  const size_t open = spec.find("<integer>", k);
  if (open == std::string::npos) return -999999;
  const size_t close = spec.find("</integer>", open);
  if (close == std::string::npos) return -999999;
  const std::string v = spec.substr(open + 9, close - open - 9);
  return std::stol(v);
}

static void testRootPlist(const char* path) {
  const std::string xml = slurp(path);
  if (xml.empty()) {
    std::printf("FAIL cannot read %s (run from the repo root)\n", path);
    failures++;
    return;
  }

  // The three group headers the owner named, in order.
  const size_t above = xml.find("<string>Above the Paper</string>");
  const size_t below = xml.find("<string>Below the Paper</string>");
  const size_t multi = xml.find("<string>Multi-Finger</string>");
  check(above != std::string::npos, "the Above the Paper group is in Root.plist");
  check(below != std::string::npos, "the Below the Paper group is in Root.plist");
  check(multi != std::string::npos, "the Multi-Finger group is in Root.plist");
  check(above < below && below < multi,
        "the groups read above the paper, below the paper, multi-finger");

  // THE PAPER ITSELF HAS NO ROWS. Owner ruling: on the paper is fixed and is
  // not in the settings at all. Asserted absent so a future re-add is a
  // conscious act rather than a merge accident, the same discipline
  // panel_palette_test.cpp applies to the removed page rows.
  const char* onPaperKeys[] = {"gestureTapOnPaper", "gestureSwipeLeftOnPaper",
                               "gestureSwipeRightOnPaper", "gestureHoldOnPaper",
                               "gestureTapPaper", "gestureHoldPaper"};
  for (const char* k : onPaperKeys)
    check(xml.find(std::string("<string>") + k + "</string>") ==
              std::string::npos,
          "no row may configure a gesture ON the paper");

  for (int i = 0; i < gesturebind::kGestureCount; ++i) {
    const Gesture g = static_cast<Gesture>(i);
    const std::string k = gesturebind::key(g);
    const std::string spec = specifierFor(xml, k);
    if (spec.empty()) {
      std::printf("  FAIL: %s (%s) has no row in Root.plist\n", k.c_str(),
                  gesturebind::gestureName(g));
      failures++;
      continue;
    }

    // DefaultValue must BE the default. Settings.app shows this for an
    // untouched key and CrossPointPrefs.mm registers it as what the app reads,
    // so a disagreement here is a switch that displays one action and performs
    // another.
    const long dv = defaultValueOf(spec);
    if (dv != static_cast<long>(gesturebind::defaultAction(g))) {
      std::printf(
          "  FAIL: %s DefaultValue is %ld, but defaultAction() is %d (%s)\n",
          k.c_str(), dv, static_cast<int>(gesturebind::defaultAction(g)),
          gesturebind::actionName(gesturebind::defaultAction(g)));
      failures++;
    }

    // Every row offers every action, in the one canonical order, and its
    // labels line up with them one for one.
    const std::vector<std::string> values = arrayAfter(spec, "Values");
    const std::vector<std::string> titles = arrayAfter(spec, "Titles");
    if (static_cast<int>(values.size()) != gesturebind::kOfferedActionCount) {
      std::printf("  FAIL: %s offers %zu actions, expected %d\n", k.c_str(),
                  values.size(), gesturebind::kOfferedActionCount);
      failures++;
      continue;
    }
    check(titles.size() == values.size(), k.c_str());
    for (int j = 0; j < gesturebind::kOfferedActionCount; ++j) {
      const long want = static_cast<long>(gesturebind::kOfferedActions[j]);
      if (std::stol(values[static_cast<size_t>(j)]) != want) {
        std::printf("  FAIL: %s value %d is %s, expected %ld (%s)\n", k.c_str(),
                    j, values[static_cast<size_t>(j)].c_str(), want,
                    gesturebind::actionName(gesturebind::kOfferedActions[j]));
        failures++;
      }
    }
  }

  // The rows sit in the group their gesture belongs to. Checked by POSITION
  // rather than by nesting, because a Settings.bundle has no nesting: a
  // PSGroupSpecifier owns every row between it and the next one, so a row that
  // drifts past a group header silently changes which heading it appears under.
  for (int i = 0; i < gesturebind::kGestureCount; ++i) {
    const Gesture g = static_cast<Gesture>(i);
    const size_t at =
        xml.find("<string>" + std::string(gesturebind::key(g)) + "</string>");
    if (at == std::string::npos) continue;
    const bool isAbove = i <= static_cast<int>(Gesture::HoldAbove);
    const bool isBelow = i > static_cast<int>(Gesture::HoldAbove) &&
                         i <= static_cast<int>(Gesture::HoldBelow);
    if (isAbove)
      check(at > above && at < below, gesturebind::gestureName(g));
    else if (isBelow)
      check(at > below && at < multi, gesturebind::gestureName(g));
    else
      check(at > multi, gesturebind::gestureName(g));
  }

  // The surviving sentinel from panel_palette_test.cpp: the Zen toggle stays at
  // the very top, ahead of everything added here.
  const size_t zenToggle = xml.find("<string>zenModeEnabled</string>");
  check(zenToggle != std::string::npos && zenToggle < above,
        "the Zen toggle still comes first");
}

int main(int argc, char** argv) {
  testDefaultsMatchToday();
  testUnbound();
  testSharing();
  testZenMayBeLeftUnbound();
  testZones();
  testZenScope();
  testStoredIntegers();
  testRootPlist(argc > 1 ? argv[1] : "ios/Settings.bundle/Root.plist");

  if (failures) {
    std::printf("gesture_bindings: %d FAILURES\n", failures);
    return 1;
  }
  std::printf("gesture_bindings: all checks passed\n");
  return 0;
}
