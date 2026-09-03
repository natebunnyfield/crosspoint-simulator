// WHAT EVERY GESTURE DOES -- the truth table for ios/GestureBindings.h.
//
// Owner ruling 2026-08-28 (T-025), verbatim: *"if above and below the paper is
// blank, it should pass through to global configuration. if they are defined,
// they take precedence. there is no 'on the paper', it's just normal
// configuration."*
//
// So the model is LAYERED: a global layer holding every gesture, and two zone
// groups (above the paper, below it) that override it for the six
// single-finger gestures and are BLANK by default. There is no "on the paper"
// concept -- the paper is simply where nothing overrides.
//
// THE SET WAS RE-CUT THE SAME DAY, twice. The first shipping shape configured
// only the fourteen gestures that happened to be wired; the owner asked for
// every gesture the surface can express; and he then trimmed that to the
// seventeen worth having on a phone: single taps only (1 and 2 fingers), swipes
// on 1 and 2 fingers in four directions, long presses on 1 and 2 fingers,
// pinch, rotation, shake. **The three-finger tap (zen) and the four-finger tap
// (power) went with the finger counts that carried them**, and both removals
// are asserted BY NAME below so the change stays pinned rather than incidental.
//
// Every failure mode of that rule is SILENT on a device and none of them can be
// reproduced off-device at all, because UIKit's recognizers live above SDL where
// neither an input script nor simctl can synthesize a touch. So this is a truth
// table, and it pins:
//
//  1. EVERY SURVIVING DEFAULT IS THE PREVIOUS BUILD'S BEHAVIOR, and the two
//     removals are the only differences. Each global default is asserted
//     against the live mapping it replaces, by name; every zone row is blank
//     except HoldAbove, which reproduces what a hold above the paper does now.
//  2. THE FALL-THROUGH. A blank zone resolves to the global value; a set zone
//     beats it; an explicit Nothing in a zone beats a bound global. That last
//     one is the whole reason Inherit and Nothing are different values, and the
//     obvious wrong implementation collapses them.
//  3. AN UNBOUND GESTURE FIRES NOTHING -- and "nothing" must not fall back to
//     the default.
//  4. TWO GESTURES MAY SHARE ONE ACTION. No conflict detection, no moving.
//  5. ANY BINDING MAY BE CLEARED, the zen ones included. They are ordinary
//     bindings (owner 2026-08-28: "zen is toggleable in settings. drop this
//     concern.") -- no guard, no special case, and this test is here so nobody
//     adds one.
//  6. THE ZONE BOUNDARIES are g_cardTopPx and the paper's bottom, and a landing
//     point between them has no override at all.
//  7. ZEN SCOPE IS A PROPERTY OF THE GESTURE AND ITS ZONE, NEVER OF THE ACTION
//     -- including the subtle half: an inherited action still takes the ZONE's
//     gate, so a hold above the paper set to Inherit still fires out of zen.
//
// Plus the two drift gates no static_assert can do: the stored integers (a
// binding persists as an integer, so re-pointing one silently changes what a
// saved choice selects) and the shipped Root.plist, which the compiler never
// opens -- every row's key, its DefaultValue, the actions it offers, the group
// it sits in and the ORDER, since that plist is a projection of the header made
// by tools/gen_gesture_plist.py and a stale projection is invisible.

#include <cassert>
#include <cstdio>
#include <fstream>
#include <set>
#include <sstream>
#include <string>
#include <vector>

#include "../ios/GestureBindings.h"

using gesturebind::Action;
using gesturebind::Family;
using gesturebind::Gesture;
using gesturebind::Group;
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

// The value an untouched row answers with: Settings.app registers every
// DefaultValue, so this is what the app actually reads on a clean install.
static int shipped(Gesture g) {
  return static_cast<int>(gesturebind::defaultAction(g));
}

// The six single-finger kinds, walked as a range in several tests.
static constexpr int kOneFingerCount = static_cast<int>(OneFinger::Count);

// --- 1. THE DEFAULTS ARE THE PREVIOUS BUILD'S BEHAVIOR ----------------------
//
// The right-hand column of each line is the live mapping this default replaces.
// If one of these ever has to change, it is because the app's behavior changed
// first, and the recognizer is the thing to read.
static void testDefaultsMatchToday() {
  // CrossPointZenRecognizers.mm swipe:, one finger. "reading on one finger"
  // (owner 2026-08-22): a swipe LEFT pages FORWARD, which is the front RIGHT
  // button. Neither the swipes nor the SDL deliberate tap was position-aware,
  // so ONE global binding is the whole of what each of them did.
  checkAction(gesturebind::defaultAction(Gesture::SwipeLeftGlobal),
              Action::Right, "1-swipe left defaults to page forward");
  checkAction(gesturebind::defaultAction(Gesture::SwipeRightGlobal),
              Action::Left, "1-swipe right defaults to page back");
  // CrossPointIOSShim.cpp padWatch, Verb::Down -> BTN_RIGHT.
  checkAction(gesturebind::defaultAction(Gesture::TapGlobal), Action::Right,
              "the deliberate tap defaults to page forward");
  // ZenHoldRouting.h's Action::Select -- what a hold did anywhere but above the
  // paper.
  checkAction(gesturebind::defaultAction(Gesture::HoldGlobal), Action::Confirm,
              "the hold defaults to select");

  // swipe:, two fingers. "sizing on two": left is BTN_DOWN, right is BTN_UP, up
  // is back, down is select.
  checkAction(gesturebind::defaultAction(Gesture::TwoFingerSwipeLeft),
              Action::Down, "2-swipe left defaults to the side DOWN button");
  checkAction(gesturebind::defaultAction(Gesture::TwoFingerSwipeRight),
              Action::Up, "2-swipe right defaults to the side UP button");
  checkAction(gesturebind::defaultAction(Gesture::TwoFingerSwipeUp),
              Action::Back, "2-swipe up defaults to back");
  checkAction(gesturebind::defaultAction(Gesture::TwoFingerSwipeDown),
              Action::Confirm, "2-swipe down defaults to select");

  // twoTap:, pinch:, CPXShakeCatcher motionEnded:.
  checkAction(gesturebind::defaultAction(Gesture::TwoFingerTap), Action::Confirm,
              "2-finger tap defaults to select");
  checkAction(gesturebind::defaultAction(Gesture::Pinch), Action::Up,
              "pinch defaults to the side UP button");
  checkAction(gesturebind::defaultAction(Gesture::Spread), Action::Down,
              "spread defaults to the side DOWN button");
  checkAction(gesturebind::defaultAction(Gesture::Shake),
              Action::FontFamilyStep, "shake defaults to the font family step");

  // THE FIVE GESTURES THE RE-CUT ADDED SHIP INERT. A new gesture that arrived
  // doing something would be a behavior change nobody asked for.
  const Gesture kNewAndInert[] = {
      Gesture::SwipeUpGlobal, Gesture::SwipeDownGlobal, Gesture::TwoFingerHold,
      Gesture::RotateClockwise, Gesture::RotateCounterClockwise};
  for (Gesture g : kNewAndInert)
    checkAction(gesturebind::defaultAction(g), Action::Nothing,
                gesturebind::gestureName(g));

  // ...and `shipsInert` names EXACTLY those five. It is not documentation: the
  // recognizer file's simultaneity delegate is keyed on it, and it is the whole
  // of why an inert rotation cannot prevent the pinch that ships bound to the
  // font step. Widen it by accident and a bound gesture stops being able to
  // prevent anything; narrow it and a shipped binding starts losing arbitration
  // — both silent, both device-only.
  int inert = 0;
  for (int i = 0; i < gesturebind::kGestureCount; ++i) {
    const Gesture g = static_cast<Gesture>(i);
    if (gesturebind::shipsInert(g)) inert++;
    check(gesturebind::shipsInert(g) ==
              (!gesturebind::isZoneRow(g) &&
               gesturebind::defaultAction(g) == Action::Nothing),
          gesturebind::gestureName(g));
  }
  check(inert == 5, "exactly five gestures ship inert");
  for (Gesture g : kNewAndInert)
    check(gesturebind::shipsInert(g), gesturebind::gestureName(g));
  // No ZONE row is ever inert in this sense — zone rows have no recognizer of
  // their own, so asking would be asking about an object that does not exist.
  check(!gesturebind::shipsInert(Gesture::TapAbove),
        "a zone row is never a ships-inert RECOGNIZER");
  check(!gesturebind::shipsInert(Gesture::Pinch),
        "pinch ships bound, so nothing inert may prevent it");
  check(!gesturebind::shipsInert(Gesture::Spread), "nor spread");
  check(!gesturebind::shipsInert(Gesture::TwoFingerSwipeLeft),
        "nor the 2-finger swipes the new 2-finger hold overlaps");

  // The guard globalGesture() was missing until the 2026-08-28 adversarial
  // pass: without it the scan matched the first row whose kind is Count — the
  // two-finger tap — so globalGesture(Count) answered TwoFingerTap and
  // oneFingerAction(Count, ...) answered `confirm`.
  check(gesturebind::globalGesture(OneFinger::Count) == Gesture::Count,
        "globalGesture(Count) is Count, not the first multi-finger row");
  checkAction(gesturebind::oneFingerAction(OneFinger::Count, Zone::Neither, true,
                                           0, 0),
              Action::Nothing, "...and it resolves to nothing, not to confirm");

  // EVERY ZONE ROW SHIPS BLANK -- except the one that reproduces what a hold
  // above the paper does today. A hold above the paper toggles zen while the
  // same hold anywhere else selects; those are two actions for one gesture, so
  // no single global binding can state both, and a blank HoldAbove would
  // inherit Confirm and change what that hold does.
  checkAction(gesturebind::defaultAction(Gesture::HoldAbove), Action::ToggleZen,
              "REGRESSION: the hold above the paper still toggles zen");
  for (int i = 0; i < gesturebind::kGestureCount; ++i) {
    const Gesture g = static_cast<Gesture>(i);
    if (!gesturebind::isZoneRow(g) || g == Gesture::HoldAbove) continue;
    checkAction(gesturebind::defaultAction(g), Action::Inherit,
                gesturebind::gestureName(g));
  }

  // THE TWO REMOVALS, BY NAME. The owner was shown that the trim costs the
  // three-finger zen toggle and the four-finger power tap and chose it, so
  // these are pinned: a re-add has to be a conscious act, and the plist half of
  // the same assertion is in testRootPlist below.
  for (int i = 0; i < gesturebind::kGestureCount; ++i) {
    const gesturebind::Row& r = gesturebind::kRows[i];
    check(r.fingers <= 2, "no row uses more than two fingers");
    const std::string k = r.key;
    check(k != "gestureThreeFingerTap",
          "the 3-finger tap is GONE (owner 2026-08-28)");
    check(k != "gestureFourFingerTap",
          "the 4-finger tap is GONE (owner 2026-08-28)");
  }
  // POWER IS NO LONGER ANY GESTURE'S DEFAULT -- the four-finger tap was its
  // only home, and it is pad-only now. The ACTION survives, because the owner
  // may still bind it.
  for (int i = 0; i < gesturebind::kGestureCount; ++i)
    check(gesturebind::defaultAction(static_cast<Gesture>(i)) != Action::Power,
          "nothing ships bound to POWER");
  bool powerOffered = false;
  for (int i = 0; i < gesturebind::kGlobalActionCount; ++i)
    if (gesturebind::kGlobalActions[i] == Action::Power) powerOffered = true;
  check(powerOffered, "...but POWER is still offered as a choice");
  // ...and the zen toggle now ships on exactly one row, the hold above the
  // paper, because the three-finger tap that also carried it is gone.
  int zenDefaults = 0;
  for (int i = 0; i < gesturebind::kGestureCount; ++i)
    if (gesturebind::defaultAction(static_cast<Gesture>(i)) == Action::ToggleZen)
      zenDefaults++;
  check(zenDefaults == 1, "exactly one row ships bound to the zen toggle");

  // No GLOBAL row defaults to Inherit or Unset. Inherit means "fall through"
  // and there is nothing above the global layer to fall through to.
  for (int i = 0; i < gesturebind::kGestureCount; ++i) {
    const Gesture g = static_cast<Gesture>(i);
    if (gesturebind::isZoneRow(g)) continue;
    check(gesturebind::defaultAction(g) != Action::Inherit,
          gesturebind::gestureName(g));
    check(gesturebind::defaultAction(g) != Action::Unset,
          gesturebind::gestureName(g));
  }
  // Twelve of the seventeen global rows do something on a clean install; the
  // other five are the additions above. Counted rather than trusted, because
  // this is the number a wrong default would move.
  int liveGlobals = 0;
  for (int i = 0; i < gesturebind::kGestureCount; ++i) {
    const Gesture g = static_cast<Gesture>(i);
    if (gesturebind::isZoneRow(g)) continue;
    if (gesturebind::defaultAction(g) != Action::Nothing) liveGlobals++;
  }
  check(liveGlobals == 12, "twelve global rows ship bound to something");

  // AN UNTOUCHED STORE IS AN UNTOUCHED APP. -integerForKey: answers 0 for a key
  // whose registration domain never loaded -- an unreadable Settings.bundle --
  // and that must render the app exactly as it shipped, which is why 0 is Unset
  // rather than Nothing.
  for (int i = 0; i < gesturebind::kGestureCount; ++i) {
    const Gesture g = static_cast<Gesture>(i);
    checkAction(gesturebind::resolve(g, 0), gesturebind::defaultAction(g),
                gesturebind::gestureName(g));
    checkAction(gesturebind::resolve(g, -7), gesturebind::defaultAction(g),
                gesturebind::gestureName(g));
    checkAction(gesturebind::resolve(g, 9999), gesturebind::defaultAction(g),
                gesturebind::gestureName(g));
  }

  // INHERIT IS A ZONE VALUE ONLY. Stored against a global row -- a hand-edited
  // plist, a restored backup -- it must fall back to that row's default and NOT
  // escape into the recognizers, where it would be dispatched as an unknown
  // action and swallow the gesture.
  for (int i = 0; i < gesturebind::kGestureCount; ++i) {
    const Gesture g = static_cast<Gesture>(i);
    if (gesturebind::isZoneRow(g)) {
      checkAction(gesturebind::resolve(g, stored(Action::Inherit)),
                  Action::Inherit, gesturebind::gestureName(g));
    } else {
      checkAction(gesturebind::resolve(g, stored(Action::Inherit)),
                  gesturebind::defaultAction(g), gesturebind::gestureName(g));
    }
  }

  // THE WHOLE POINT, END TO END: with the shipped values in the store, every
  // single-finger gesture answers what the previous build answered, in all
  // three zones.
  struct Case {
    OneFinger kind;
    Zone zone;
    bool zenOn;
    Action want;
    const char* what;
  };
  const Case kCases[] = {
      // The deliberate tap paged forward wherever it landed, in zen only.
      {OneFinger::Tap, Zone::AbovePaper, true, Action::Right, "tap above"},
      {OneFinger::Tap, Zone::Neither, true, Action::Right, "tap on the paper"},
      {OneFinger::Tap, Zone::BelowPaper, true, Action::Right, "tap below"},
      {OneFinger::Tap, Zone::Neither, false, Action::Nothing, "tap, zen off"},
      {OneFinger::Tap, Zone::AbovePaper, false, Action::Nothing,
       "tap above, zen off"},
      // The horizontal swipes, likewise.
      {OneFinger::SwipeLeft, Zone::AbovePaper, true, Action::Right,
       "swipe left above"},
      {OneFinger::SwipeLeft, Zone::Neither, true, Action::Right,
       "swipe left on the paper"},
      {OneFinger::SwipeLeft, Zone::BelowPaper, true, Action::Right,
       "swipe left below"},
      {OneFinger::SwipeRight, Zone::Neither, true, Action::Left,
       "swipe right on the paper"},
      {OneFinger::SwipeRight, Zone::BelowPaper, true, Action::Left,
       "swipe right below"},
      {OneFinger::SwipeLeft, Zone::Neither, false, Action::Nothing,
       "swipe left, zen off"},
      // The vertical swipes are new and do nothing anywhere.
      {OneFinger::SwipeUp, Zone::Neither, true, Action::Nothing,
       "swipe up on the paper does nothing"},
      {OneFinger::SwipeUp, Zone::AbovePaper, true, Action::Nothing,
       "...nor above it"},
      {OneFinger::SwipeDown, Zone::BelowPaper, true, Action::Nothing,
       "swipe down below the paper does nothing"},
      // The hold: the 2026-08-27 position split, reproduced by the layers.
      {OneFinger::Hold, Zone::AbovePaper, false, Action::ToggleZen,
       "hold above, zen OFF -> toggle"},
      {OneFinger::Hold, Zone::AbovePaper, true, Action::ToggleZen,
       "hold above, zen ON -> toggle"},
      {OneFinger::Hold, Zone::Neither, true, Action::Confirm,
       "hold on the paper, zen ON -> select"},
      {OneFinger::Hold, Zone::Neither, false, Action::Nothing,
       "hold on the paper, zen OFF -> nothing (no stray CONFIRM)"},
      {OneFinger::Hold, Zone::BelowPaper, true, Action::Confirm,
       "hold below, zen ON -> select"},
      {OneFinger::Hold, Zone::BelowPaper, false, Action::Nothing,
       "hold below, zen OFF -> nothing"},
  };
  for (const Case& c : kCases) {
    const Gesture zg = gesturebind::zoneGesture(c.kind, c.zone);
    const int zoneStored = zg == Gesture::Count ? 0 : shipped(zg);
    checkAction(gesturebind::oneFingerAction(
                    c.kind, c.zone, c.zenOn, zoneStored,
                    shipped(gesturebind::globalGesture(c.kind))),
                c.want, c.what);
  }
}

// --- 2. THE FALL-THROUGH ---------------------------------------------------
static void testLayering() {
  const int g_right = stored(Action::Right);

  // BLANK FALLS THROUGH. This is the default state of every zone row, and it is
  // what keeps the shipped behavior the previous build's.
  checkAction(
      gesturebind::oneFingerAction(OneFinger::Tap, Zone::AbovePaper, true,
                                   stored(Action::Inherit), g_right),
      Action::Right, "a blank zone row inherits the global binding");
  checkAction(
      gesturebind::oneFingerAction(OneFinger::Tap, Zone::BelowPaper, true,
                                   stored(Action::Inherit), stored(Action::Back)),
      Action::Back, "...whatever the global binding happens to be");
  // An UNWRITTEN zone key answers with its registered default, which for every
  // row but HoldAbove is Inherit -- so it falls through too.
  checkAction(gesturebind::oneFingerAction(OneFinger::SwipeLeft,
                                           Zone::AbovePaper, true,
                                           shipped(Gesture::SwipeLeftAbove),
                                           stored(Action::Power)),
              Action::Power, "an untouched zone row inherits");

  // A SET ZONE ROW WINS.
  checkAction(gesturebind::oneFingerAction(OneFinger::Tap, Zone::AbovePaper,
                                           true, stored(Action::Back), g_right),
              Action::Back, "a set zone row beats the global binding");
  checkAction(gesturebind::oneFingerAction(OneFinger::Hold, Zone::BelowPaper,
                                           true, stored(Action::Power),
                                           stored(Action::Confirm)),
              Action::Power, "...in the below zone as well");
  // ...including for a gesture whose global row is unbound. This is the case
  // that makes "is this gesture bound" a question about ALL THREE layers.
  checkAction(gesturebind::oneFingerAction(OneFinger::SwipeUp, Zone::AbovePaper,
                                           true, stored(Action::Back),
                                           shipped(Gesture::SwipeUpGlobal)),
              Action::Back,
              "a zone override can bind a gesture whose global row is Nothing");

  // AN EXPLICIT Nothing IN A ZONE BEATS A BOUND GLOBAL. The owner's stated use:
  // switch a gesture off in the margins while it keeps working on the page. The
  // obvious wrong implementation collapses Nothing into blank -- treating "no
  // action" as "no override" -- and then this row silently does the global
  // thing instead of nothing at all.
  checkAction(gesturebind::oneFingerAction(OneFinger::Tap, Zone::AbovePaper,
                                           true, stored(Action::Nothing),
                                           g_right),
              Action::Nothing,
              "REGRESSION: an explicit Nothing in a zone is an OVERRIDE, not a "
              "blank");
  checkAction(gesturebind::oneFingerAction(OneFinger::SwipeLeft,
                                           Zone::BelowPaper, true,
                                           stored(Action::Nothing), g_right),
              Action::Nothing, "...and the same below the paper");
  // ...while the same Nothing stored GLOBALLY switches the gesture off
  // everywhere no zone overrides.
  checkAction(gesturebind::oneFingerAction(OneFinger::Tap, Zone::Neither, true,
                                           0, stored(Action::Nothing)),
              Action::Nothing, "a global Nothing switches the gesture off");

  // THE PAPER HAS NO OVERRIDE ROW AT ALL, and no stored value can reach it.
  check(gesturebind::zoneGesture(OneFinger::Tap, Zone::Neither) ==
            Gesture::Count,
        "there is no settings row for a landing point between the boundaries");
  check(gesturebind::zoneGesture(OneFinger::Hold, Zone::Neither) ==
            Gesture::Count,
        "...for any single-finger gesture");
  checkAction(gesturebind::oneFingerAction(OneFinger::Tap, Zone::Neither, true,
                                           stored(Action::Power), g_right),
              Action::Right,
              "a zone value is ignored where there is no zone row");

  // Each override row is distinct: two (gesture, zone) pairs sharing one row
  // would be one setting wearing two labels.
  // Every one-finger gesture has both overrides EXCEPT Swipe Down above the
  // paper (owner 2026-09-02): a swipe is zoned where UIKit recognizes it, and
  // the 68 pt band above the paper is crossed before a downward swipe is one.
  // Its mirror below the paper stays -- that band is at least twice as tall --
  // so eleven rows, not ten: dropped on measurement, not on symmetry.
  std::set<int> seen;
  for (int k = 0; k < kOneFingerCount; ++k) {
    for (Zone z : {Zone::AbovePaper, Zone::BelowPaper}) {
      const Gesture g =
          gesturebind::zoneGesture(static_cast<OneFinger>(k), z);
      const bool dropped = static_cast<OneFinger>(k) == OneFinger::SwipeDown &&
                           z == Zone::AbovePaper;
      if (dropped) {
        check(g == Gesture::Count,
              "no Swipe Down row above the paper (owner 2026-09-02)");
        continue;
      }
      check(g != Gesture::Count,
            "every other one-finger gesture has both overrides");
      check(seen.insert(static_cast<int>(g)).second,
            "no two (gesture, zone) pairs share one row");
    }
  }
  check(seen.size() == 11, "eleven override rows: six gestures, two zones, "
                           "minus the one that could not fire");
  check(gesturebind::zoneGesture(OneFinger::SwipeUp, Zone::BelowPaper) !=
            Gesture::Count,
        "Swipe Up below the paper STAYS -- its band is tall enough to fire in");
  // A missing override row is not a special case: the global binding applies,
  // exactly as it does on the paper.
  checkAction(gesturebind::oneFingerAction(OneFinger::SwipeDown,
                                           Zone::AbovePaper, true,
                                           stored(Action::Power), g_right),
              Action::Right,
              "a swipe down above the paper resolves to the global binding, "
              "whatever a stale zone value says");

  // A TWO-FINGER GESTURE HAS NO ZONE OVERRIDE, by ruling: it is the same
  // gesture wherever it lands. Asked through zoneRowFor, which is the question
  // the recognizer file puts.
  for (Zone z : {Zone::AbovePaper, Zone::Neither, Zone::BelowPaper}) {
    check(gesturebind::zoneRowFor(Gesture::TwoFingerTap, z) == Gesture::Count,
          "the 2-finger tap has no zone override");
    check(gesturebind::zoneRowFor(Gesture::Pinch, z) == Gesture::Count,
          "nor pinch");
    check(gesturebind::zoneRowFor(Gesture::Shake, z) == Gesture::Count,
          "nor the shake, which has no landing point at all");
  }
  check(gesturebind::zoneRowFor(Gesture::HoldGlobal, Zone::AbovePaper) ==
            Gesture::HoldAbove,
        "...while a one-finger row finds its own override");
}

// --- 3. AN UNBOUND GESTURE FIRES NOTHING -----------------------------------
static void testUnbound() {
  for (int i = 0; i < gesturebind::kGestureCount; ++i) {
    const Gesture g = static_cast<Gesture>(i);
    // REGRESSION GUARD: the obvious wrong implementation treats "Nothing" as
    // "no value stored" and hands back the default, so clearing a binding would
    // silently do nothing at all -- a setting that shows as set and is not.
    checkAction(gesturebind::resolve(g, stored(Action::Nothing)),
                Action::Nothing, gesturebind::gestureName(g));
  }
  for (int i = 0; i < gesturebind::kGestureCount; ++i) {
    const Gesture g = static_cast<Gesture>(i);
    if (gesturebind::isZoneRow(g)) continue;
    checkAction(gesturebind::actionFor(g, true, stored(Action::Nothing)),
                Action::Nothing, gesturebind::gestureName(g));
  }
  check(gesturebind::buttonFor(Action::Nothing) == gesturebind::kNoButton,
        "Nothing presses no button");
  check(gesturebind::buttonFor(Action::Inherit) == gesturebind::kNoButton,
        "Inherit presses no button");
  check(gesturebind::buttonFor(Action::ToggleZen) == gesturebind::kNoButton,
        "the zen toggle presses no button");
  check(gesturebind::buttonFor(Action::FontFamilyStep) ==
            gesturebind::kNoButton,
        "the font family step presses no button");
  check(gesturebind::buttonFor(Action::FontFamilyStepBack) ==
            gesturebind::kNoButton,
        "the font family step back presses no button");

  // Inherit must never come back OUT of either dispatch entry point: it is an
  // answer to "does this zone override", not an action, and a recognizer handed
  // one would swallow the gesture with nothing in the log.
  for (int i = 0; i < gesturebind::kGestureCount; ++i) {
    const Gesture g = static_cast<Gesture>(i);
    if (gesturebind::isZoneRow(g)) continue;
    check(gesturebind::actionFor(g, true, stored(Action::Inherit)) !=
              Action::Inherit,
          gesturebind::gestureName(g));
  }
  for (int k = 0; k < kOneFingerCount; ++k)
    for (Zone z : {Zone::AbovePaper, Zone::Neither, Zone::BelowPaper})
      check(gesturebind::oneFingerAction(static_cast<OneFinger>(k), z, true,
                                         stored(Action::Inherit),
                                         stored(Action::Inherit)) !=
                Action::Inherit,
            "no dispatch path may answer 'inherit'");
}

// --- 4. TWO GESTURES MAY SHARE ONE ACTION ----------------------------------
static void testSharing() {
  // No conflict detection anywhere: each gesture resolves independently and
  // nothing here can see what another holds.
  checkAction(gesturebind::actionFor(Gesture::TwoFingerTap, true,
                                     stored(Action::Confirm)),
              Action::Confirm, "2-finger tap keeps CONFIRM");
  checkAction(gesturebind::actionFor(Gesture::TwoFingerHold, true,
                                     stored(Action::Confirm)),
              Action::Confirm, "2-finger hold may hold CONFIRM too");
  // Including the zen toggle on several gestures at once, and across layers.
  checkAction(gesturebind::actionFor(Gesture::RotateClockwise, true,
                                     stored(Action::ToggleZen)),
              Action::ToggleZen, "a rotation may toggle zen");
  checkAction(gesturebind::oneFingerAction(OneFinger::Hold, Zone::AbovePaper,
                                           true, stored(Action::ToggleZen), 0),
              Action::ToggleZen, "and so does the hold above the paper");
  checkAction(gesturebind::oneFingerAction(OneFinger::Tap, Zone::Neither, true,
                                           0, stored(Action::ToggleZen)),
              Action::ToggleZen, "and the global tap, if pointed at it");
}

// --- 5. ANY BINDING MAY BE CLEARED, INCLUDING THE ZEN ONES -----------------
static void testEveryBindingMayBeCleared() {
  // Owner ruling 2026-08-28: no guard, no refusal, no warning, and nothing
  // special about the zen actions -- *"zen is toggleable in settings. drop this
  // concern."* Zen has its own switch in Settings.app, so a cleared zen binding
  // is an ordinary cleared binding. This test exists so the "missing" guard
  // reads as a decision rather than an oversight, and so nobody adds one back.
  checkAction(gesturebind::oneFingerAction(OneFinger::Hold, Zone::AbovePaper,
                                           false, stored(Action::Nothing),
                                           stored(Action::Confirm)),
              Action::Nothing, "the hold above the paper may be cleared");
  // ...including by pointing the override at Inherit, so the hold above the
  // paper takes the global Hold instead.
  checkAction(gesturebind::oneFingerAction(OneFinger::Hold, Zone::AbovePaper,
                                           false, stored(Action::Inherit),
                                           stored(Action::Confirm)),
              Action::Confirm,
              "an inherited hold above the paper takes the global action");
  // Every row at once: an app with no gesture bound to anything is a legal
  // configuration and resolves cleanly.
  for (int i = 0; i < gesturebind::kGestureCount; ++i) {
    const Gesture g = static_cast<Gesture>(i);
    if (gesturebind::isZoneRow(g)) continue;
    checkAction(gesturebind::actionFor(g, true, stored(Action::Nothing)),
                Action::Nothing, gesturebind::gestureName(g));
  }
  for (int k = 0; k < kOneFingerCount; ++k)
    for (Zone z : {Zone::AbovePaper, Zone::Neither, Zone::BelowPaper})
      checkAction(gesturebind::oneFingerAction(static_cast<OneFinger>(k), z,
                                               true, stored(Action::Nothing),
                                               stored(Action::Nothing)),
                  Action::Nothing, "every layer cleared resolves to nothing");
}

// --- 6. THE ZONES ----------------------------------------------------------
static void testZones() {
  // An iPhone Air's measured geometry: the card top at 204 device px, the
  // rocker row (the paper's bottom edge in zen) at 852.
  const float top = 204.0f, bottom = 852.0f;
  check(gesturebind::zoneFor(0.0f, top, bottom) == Zone::AbovePaper,
        "y=0 is above the paper");
  check(gesturebind::zoneFor(203.9f, top, bottom) == Zone::AbovePaper,
        "one pixel above the card top is above the paper");
  check(gesturebind::zoneFor(204.0f, top, bottom) == Zone::Neither,
        "the card top itself is inside no override (the boundary is exclusive "
        "above)");
  check(gesturebind::zoneFor(851.9f, top, bottom) == Zone::Neither,
        "one pixel above the paper's bottom edge is still inside no override");
  check(gesturebind::zoneFor(852.0f, top, bottom) == Zone::BelowPaper,
        "the paper's bottom edge itself is below the paper");
  check(gesturebind::zoneFor(2000.0f, top, bottom) == Zone::BelowPaper,
        "the bottom of the screen is below the paper");

  // A DEGENERATE BOTTOM EDGE LEAVES ONLY THE TOP BOUNDARY. Before the first
  // layout pass both boundaries read 0; a zone must not be invented out of a
  // zero, or every gesture in the lower two thirds of the screen would silently
  // change which row answers on the first frame after launch.
  check(gesturebind::zoneFor(1000.0f, top, 0.0f) == Zone::Neither,
        "with no measured bottom edge, below the top has no override");
  check(gesturebind::zoneFor(100.0f, top, 0.0f) == Zone::AbovePaper,
        "...and above the top still does");
  check(gesturebind::zoneFor(1000.0f, top, top) == Zone::Neither,
        "a bottom edge equal to the top edge is not a zone");
}

// --- 7. ZEN SCOPE IS A PROPERTY OF THE GESTURE AND ITS ZONE ----------------
static void testZenScope() {
  // "You configure WHAT a gesture does, never WHEN." TWO rows fire outside
  // zen -- the hold above the paper, and the shake (added 2026-08-29, owner:
  // "making shake gesture work in single-finger mode"). It was one from
  // 2026-08-28 (when the trim removed the three-finger tap) until this.
  int outside = 0;
  for (int i = 0; i < gesturebind::kGestureCount; ++i)
    if (gesturebind::firesOutsideZen(static_cast<Gesture>(i))) outside++;
  check(outside == 2, "exactly two rows fire outside zen");
  check(gesturebind::firesOutsideZen(Gesture::HoldAbove),
        "the hold above the paper fires outside zen");
  check(gesturebind::firesOutsideZen(OneFinger::Hold, Zone::AbovePaper),
        "...by landing point, which is how the recognizer asks");
  check(!gesturebind::firesOutsideZen(OneFinger::Hold, Zone::Neither),
        "a hold between the boundaries does not");
  check(!gesturebind::firesOutsideZen(OneFinger::Hold, Zone::BelowPaper),
        "nor one below the paper");
  check(!gesturebind::firesOutsideZen(OneFinger::Tap, Zone::AbovePaper),
        "nor a TAP above the paper -- only the hold gets in");

  // THE SHAKE, the 2026-08-29 addition: fires outside zen with no zone at all
  // (it has no landing point), and RESOLVES to its bound action in both zen
  // states -- not just gates open, the actual dispatch must answer the same
  // thing either way for a gesture with no zen-only recognizer to fall back
  // on.
  check(gesturebind::firesOutsideZen(Gesture::Shake),
        "REGRESSION: the shake fires outside zen (single-finger mode)");
  checkAction(gesturebind::actionFor(Gesture::Shake, /*zenOn=*/true,
                                     shipped(Gesture::Shake)),
              Action::FontFamilyStep, "shake resolves its binding in zen");
  checkAction(gesturebind::actionFor(Gesture::Shake, /*zenOn=*/false,
                                     shipped(Gesture::Shake)),
              Action::FontFamilyStep,
              "REGRESSION: shake resolves its binding out of zen too "
              "(single-finger mode)");
  // A cleared shake stays cleared in both states -- the always-on gate must
  // never manufacture an action out of Nothing.
  checkAction(gesturebind::actionFor(Gesture::Shake, true,
                                     stored(Action::Nothing)),
              Action::Nothing, "a cleared shake fires nothing, zen on");
  checkAction(gesturebind::actionFor(Gesture::Shake, false,
                                     stored(Action::Nothing)),
              Action::Nothing, "...and zen off");

  // THE GATE TRAVELS WITH THE LANDING POINT, NOT WITH THE BINDING. This is the
  // half a layered model makes easy to get wrong: a hold above the paper set to
  // Inherit takes its ACTION from the global row, whose own row does not fire
  // outside zen -- and it must still fire, because the zone is what decides.
  checkAction(gesturebind::oneFingerAction(OneFinger::Hold, Zone::AbovePaper,
                                           false, stored(Action::Inherit),
                                           stored(Action::Back)),
              Action::Back,
              "REGRESSION: an inherited action keeps the ZONE's zen gate");
  check(!gesturebind::firesOutsideZen(Gesture::HoldGlobal),
        "...and the global hold row is not itself an always-on row");

  // REGRESSION GUARD: the scope must not follow the ACTION. Binding a zen-only
  // gesture to the zen toggle must NOT promote it to always-on -- that would be
  // configuring WHEN, and it is the plausible implementation that would quietly
  // make two-finger taps live on every screen in the app.
  checkAction(gesturebind::actionFor(Gesture::TwoFingerTap, false,
                                     stored(Action::ToggleZen)),
              Action::Nothing,
              "a zen-only gesture bound to the toggle stays zen-only");
  checkAction(gesturebind::oneFingerAction(OneFinger::Tap, Zone::AbovePaper,
                                           false, stored(Action::ToggleZen), 0),
              Action::Nothing, "...including a zone override");
  // ...and the reverse: an always-on row bound to an ordinary button stays
  // always-on.
  checkAction(gesturebind::oneFingerAction(OneFinger::Hold, Zone::AbovePaper,
                                           false, stored(Action::Back), 0),
              Action::Back, "an always-on row bound to BACK still fires");

  // Every other gesture is silent while zen is off, whatever it holds.
  for (int i = 0; i < gesturebind::kGestureCount; ++i) {
    const Gesture g = static_cast<Gesture>(i);
    if (gesturebind::isZoneRow(g) || gesturebind::firesOutsideZen(g)) continue;
    checkAction(gesturebind::actionFor(g, false, stored(Action::Right)),
                Action::Nothing, gesturebind::gestureName(g));
  }
}

// --- 8. THE TABLE AND THE STORED INTEGERS ----------------------------------
static void testStoredIntegers() {
  // A BINDING PERSISTS AS AN INTEGER, so this list APPENDS and never re-points:
  // changing what a number means silently changes what a saved choice selects,
  // and the owner would never see the moment it happened. Pinned by value.
  // Inherit is 11 rather than 0 because it arrived after the other ten.
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
  check(stored(Action::Inherit) == 11, "Inherit is 11");
  // APPENDED 2026-08-29 (task: "allow previous font to be an assignable
  // gesture action"), after Inherit rather than before it -- the append-only
  // rule cares only that 12 was unused, not where it sits among the earlier
  // eleven declarations.
  check(stored(Action::FontFamilyStepBack) == 12, "FontFamilyStepBack is 12");
  // APPENDED 2026-09-01 (T-027: a bindable route into Manage Files' action
  // menu). Same append-only rule -- 13 was unused, so it goes after
  // FontFamilyStepBack rather than anywhere that would re-point an existing
  // saved choice.
  check(stored(Action::OpenActionMenu) == 13, "OpenActionMenu is 13");

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
    check(!k.empty(), "every row has a key");
    check(keys.insert(k).second, "no two rows share a key");
  }
  check(gesturebind::kGestureCount == 28,
        "28 rows: 17 gestures, 5 above the paper, 6 below it");
  check(gesturebind::kGlobalActionCount == 12,
        "12 global actions: 7 buttons, Nothing, the zen toggle, the font "
        "step, the font step back, open action menu");
  check(gesturebind::kZoneActionCount == 13, "...and Inherit makes 13 in a zone");
  // FontFamilyStepBack is OFFERED (a gesture can be pointed at it) but ships
  // on no default -- the same shape as Power after the 2026-08-28 trim.
  bool fontBackOffered = false;
  for (int i = 0; i < gesturebind::kGlobalActionCount; ++i)
    if (gesturebind::kGlobalActions[i] == Action::FontFamilyStepBack)
      fontBackOffered = true;
  check(fontBackOffered, "font family step back is offered as a choice");
  for (int i = 0; i < gesturebind::kGestureCount; ++i)
    check(gesturebind::defaultAction(static_cast<Gesture>(i)) !=
              Action::FontFamilyStepBack,
          "nothing ships bound to font family step back");
  // OpenActionMenu (T-027): same shape again -- offered in BOTH lists (a
  // gesture in either the global layer or a zone override may be pointed at
  // it), ships on no row's default, and the channel it dispatches to is
  // screen-scoped rather than global -- see ios/GestureBindings.h's comment
  // on the enumerator for what that means off this table.
  bool menuOfferedGlobal = false;
  for (int i = 0; i < gesturebind::kGlobalActionCount; ++i)
    if (gesturebind::kGlobalActions[i] == Action::OpenActionMenu)
      menuOfferedGlobal = true;
  check(menuOfferedGlobal, "open action menu is offered globally");
  bool menuOfferedZone = false;
  for (int i = 0; i < gesturebind::kZoneActionCount; ++i)
    if (gesturebind::kZoneActions[i] == Action::OpenActionMenu)
      menuOfferedZone = true;
  check(menuOfferedZone, "open action menu is offered in a zone too");
  for (int i = 0; i < gesturebind::kGestureCount; ++i)
    check(gesturebind::defaultAction(static_cast<Gesture>(i)) !=
              Action::OpenActionMenu,
          "nothing ships bound to open action menu -- the owner picks it");
  check(gesturebind::isOffered(Gesture::TwoFingerHold,
                                stored(Action::OpenActionMenu)),
        "a global row (e.g. the 2-finger hold T-027 named) accepts it");
  check(gesturebind::isOffered(Gesture::TapAbove,
                                stored(Action::OpenActionMenu)),
        "a zone row accepts it too");
  // A stored 0 (an unwritten key, or a Root.plist that would not load) never
  // resolves to open action menu on any row -- it falls back to that row's
  // own default, same as the general stored-0 sweep above proves for every
  // action, restated here by name since this is the newest and the one most
  // likely to be miscoded as a fallback.
  for (int i = 0; i < gesturebind::kGestureCount; ++i) {
    const Gesture g = static_cast<Gesture>(i);
    check(gesturebind::resolve(g, 0) != Action::OpenActionMenu ||
              gesturebind::defaultAction(g) == Action::OpenActionMenu,
          "stored 0 resolves to the row's own default, not to open action menu");
  }
  check(!gesturebind::isOffered(Gesture::TapGlobal, 0),
        "Unset is never offered as a choice -- it is a read-time fallback");
  check(!gesturebind::isOffered(Gesture::TapGlobal, stored(Action::Inherit)),
        "a GLOBAL row does not offer Inherit -- there is nothing above it");
  check(gesturebind::isOffered(Gesture::TapAbove, stored(Action::Inherit)),
        "a zone row does");
  // The row-kind predicate, pinned at both edges: an off-by-one here would make
  // a global row accept Inherit or a zone row reject it.
  check(!gesturebind::isZoneRow(Gesture::Shake), "Shake is a global row");
  check(gesturebind::isZoneRow(Gesture::TapAbove),
        "TapAbove is the first zone row");
  check(gesturebind::isZoneRow(Gesture::HoldBelow),
        "HoldBelow is the last zone row");

  // THE SHAPE OF THE SET, counted from the table rather than trusted. These are
  // the numbers the owner named; a family that quietly grows or shrinks moves
  // one of them.
  int taps = 0, swipes = 0, holds = 0, pinches = 0, rotates = 0, shakes = 0;
  for (int i = 0; i < gesturebind::kGestureCount; ++i) {
    const gesturebind::Row& r = gesturebind::kRows[i];
    if (r.zone != Zone::Neither) continue;
    switch (r.family) {
      case Family::Tap: taps++; break;
      case Family::Swipe: swipes++; break;
      case Family::LongPress: holds++; break;
      case Family::Pinch: pinches++; break;
      case Family::Rotate: rotates++; break;
      case Family::Shake: shakes++; break;
    }
  }
  check(taps == 2, "two taps: one finger and two, single taps only");
  check(swipes == 8, "eight swipes: two finger counts by four directions");
  check(holds == 2, "two long presses: one finger and two");
  check(pinches == 2, "pinch in and out");
  check(rotates == 2, "rotation both ways");
  check(shakes == 1, "one shake");
  check(taps + swipes + holds + pinches + rotates + shakes == 17,
        "17 global gestures");

  // EVERY SINGLE-FINGER ROW IS OVERRIDABLE AND NOTHING ELSE IS. The `kind`
  // field is what makes a row zone-aware, and a two-finger row that acquired
  // one would get a zone override nobody could see in Settings.app.
  for (int i = 0; i < gesturebind::kGestureCount; ++i) {
    const gesturebind::Row& r = gesturebind::kRows[i];
    const bool overridable = r.kind != OneFinger::Count;
    check(overridable == (r.fingers == 1),
          "exactly the one-finger rows carry a single-finger kind");
  }
}

// --- 9. THE SHIPPED Root.plist ---------------------------------------------
//
// The half no static_assert can do: Settings.app's rows live in a plist the
// compiler never opens. A row whose Key is misspelled writes a preference
// nothing reads; a row whose DefaultValue disagrees with defaultAction()
// DISPLAYS one thing and BEHAVES as another (CrossPointPrefs.mm derives its
// registration domain from these same DefaultValues, so the two halves have to
// agree or the switch and the app say different things); a row missing an
// action offers a choice the code supports and the owner cannot reach.
//
// The plist is GENERATED from the header by tools/gen_gesture_plist.py, which
// makes a stale projection the likeliest failure here rather than a typo -- so
// this also pins the ORDER and the GROUPING, which is what a stale run would
// move.

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

// The <integer> that follows `<key>DefaultValue</key>`, or a sentinel.
static long defaultValueOf(const std::string& spec) {
  const size_t k = spec.find("<key>DefaultValue</key>");
  if (k == std::string::npos) return -999999;
  const size_t open = spec.find("<integer>", k);
  if (open == std::string::npos) return -999999;
  const size_t close = spec.find("</integer>", open);
  if (close == std::string::npos) return -999999;
  return std::stol(spec.substr(open + 9, close - open - 9));
}

static void testRootPlist(const char* path) {
  const std::string xml = slurp(path);
  if (xml.empty()) {
    std::printf("FAIL cannot read %s (run from the repo root)\n", path);
    failures++;
    return;
  }

  // THE GROUPS, in the order the header lists them. The global layer is
  // sub-grouped by finger count because 28 rows in one flat list is a scroll
  // with no landmarks; the two override groups come last, after everything they
  // can override.
  size_t groupAt[gesturebind::kGroupCount];
  for (int i = 0; i < gesturebind::kGroupCount; ++i) {
    const Group grp = static_cast<Group>(i);
    const std::string title = gesturebind::groupTitle(grp);
    groupAt[i] = xml.find("<string>" + title + "</string>");
    if (groupAt[i] == std::string::npos) {
      std::printf("  FAIL: group '%s' is missing from Root.plist\n",
                  title.c_str());
      failures++;
      return;
    }
    if (i > 0)
      check(groupAt[i] > groupAt[i - 1],
            "the groups appear in the header's order");
  }
  // The gesture section ends where the Screen group begins.
  const size_t afterGestures = xml.find("<string>Screen</string>");
  check(afterGestures != std::string::npos &&
            afterGestures > groupAt[gesturebind::kGroupCount - 1],
        "the Screen group still follows the gesture groups");

  // THERE IS NO "ON THE PAPER". Owner ruling: it is not a concept, so it has no
  // row and no key. Asserted absent so a re-add is a conscious act, the same
  // discipline panel_palette_test.cpp applies to the removed page rows -- and
  // because an earlier shape of this feature DID have one.
  //
  // The two REMOVED gestures are asserted the same way: the three-finger tap
  // and the four-finger tap went with the 2026-08-28 trim, and a row for either
  // reappearing would be a ruling reversed by accident.
  const char* absentKeys[] = {
      "gestureTapOnPaper",        "gestureSwipeLeftOnPaper",
      "gestureSwipeRightOnPaper", "gestureHoldOnPaper",
      "gestureTapPaper",          "gestureHoldPaper",
      "gestureThreeFingerTap",    "gestureFourFingerTap",
      "gestureFiveFingerTap",     "gestureDoubleTap",
      "gestureTripleTap",         "gestureEdgePanLeft",
      // Dropped 2026-09-02: a downward swipe cannot be recognized inside the
      // 68 pt band above the paper. Its mirror below the paper is NOT here.
      "gestureSwipeDownAbove"};
  for (const char* k : absentKeys) {
    if (xml.find(std::string("<string>") + k + "</string>") !=
        std::string::npos) {
      std::printf("  FAIL: Root.plist still has a row for '%s'\n", k);
      failures++;
    }
  }

  size_t previous = 0;
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
    // so a disagreement here is a row that displays one action and performs
    // another.
    const long dv = defaultValueOf(spec);
    if (dv != static_cast<long>(gesturebind::defaultAction(g))) {
      std::printf(
          "  FAIL: %s DefaultValue is %ld, but defaultAction() is %d (%s)\n",
          k.c_str(), dv, static_cast<int>(gesturebind::defaultAction(g)),
          gesturebind::actionName(gesturebind::defaultAction(g)));
      failures++;
    }

    // Every row offers exactly its layer's actions, in the one canonical order,
    // with labels lining up one for one. A global row offering Inherit would be
    // offering a fall-through to nothing.
    const bool zoneRow = gesturebind::isZoneRow(g);
    const gesturebind::Action* wantList =
        zoneRow ? gesturebind::kZoneActions : gesturebind::kGlobalActions;
    const int wantCount =
        zoneRow ? gesturebind::kZoneActionCount : gesturebind::kGlobalActionCount;
    const std::vector<std::string> values = arrayAfter(spec, "Values");
    const std::vector<std::string> titles = arrayAfter(spec, "Titles");
    if (static_cast<int>(values.size()) != wantCount) {
      std::printf("  FAIL: %s offers %zu actions, expected %d\n", k.c_str(),
                  values.size(), wantCount);
      failures++;
      continue;
    }
    check(titles.size() == values.size(), k.c_str());
    for (int j = 0; j < wantCount; ++j) {
      const long want = static_cast<long>(wantList[j]);
      if (std::stol(values[static_cast<size_t>(j)]) != want) {
        std::printf("  FAIL: %s value %d is %s, expected %ld (%s)\n", k.c_str(),
                    j, values[static_cast<size_t>(j)].c_str(), want,
                    gesturebind::actionName(wantList[j]));
        failures++;
      }
    }

    // The row's TITLE is the header's, so Settings.app cannot label a row as
    // something the log does not call it.
    check(spec.find("<string>" + std::string(gesturebind::rowTitle(g)) +
                    "</string>") != std::string::npos,
          k.c_str());

    // THE ROW SITS IN THE GROUP ITS LAYER BELONGS TO, and in the header's
    // ORDER. Checked by POSITION rather than by nesting, because a
    // Settings.bundle has no nesting: a PSGroupSpecifier owns every row between
    // it and the next one, so a row that drifts past a group header silently
    // changes which heading it appears under -- and here that would also change
    // which LAYER it is, which is worse.
    const size_t at = xml.find("<string>" + k + "</string>");
    const int grp = static_cast<int>(gesturebind::groupOf(g));
    const size_t groupEnds = (grp + 1 < gesturebind::kGroupCount)
                                 ? groupAt[grp + 1]
                                 : afterGestures;
    check(at > groupAt[grp] && at < groupEnds, gesturebind::gestureName(g));
    check(at > previous, "the rows appear in the header's order");
    previous = at;
  }

  // The surviving sentinel from panel_palette_test.cpp: the Zen toggle stays at
  // the very top, ahead of everything added here.
  const size_t zenToggle = xml.find("<string>zenModeEnabled</string>");
  check(zenToggle != std::string::npos && zenToggle < groupAt[0],
        "the Zen toggle still comes first");
}

int main(int argc, char** argv) {
  testDefaultsMatchToday();
  testLayering();
  testUnbound();
  testSharing();
  testEveryBindingMayBeCleared();
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
