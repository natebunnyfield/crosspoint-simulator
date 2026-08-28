// WHAT EVERY GESTURE DOES -- the truth table for ios/GestureBindings.h.
//
// Owner ruling 2026-08-28 (T-025), verbatim: *"if above and below the paper is
// blank, it should pass through to global configuration. if they are defined,
// they take precedence. there is no 'on the paper', it's just normal
// configuration."*
//
// So the model is LAYERED: a global layer holding every gesture, and two zone
// groups (above the paper, below it) that override it for the four
// single-finger gestures and are BLANK by default. There is no "on the paper"
// concept -- the paper is simply where nothing overrides.
//
// Every failure mode of that rule is SILENT on a device and none of them can be
// reproduced off-device at all, because UIKit's recognizers live above SDL where
// neither an input script nor simctl can synthesize a touch. So this is a truth
// table, and it pins:
//
//  1. EVERY DEFAULT IS BUILD 156'S BEHAVIOR. An install that never opens the
//     setting must behave identically to the build before it existed. Each
//     global default is asserted against the live mapping it replaces, by name,
//     and every zone row is blank -- except HoldAbove, which carries the zen
//     toggle and could not state it any other way.
//  2. THE FALL-THROUGH. A blank zone resolves to the global value; a set zone
//     beats it; an explicit Nothing in a zone beats a bound global. That last
//     one is the whole reason Inherit and Nothing are different values, and the
//     obvious wrong implementation collapses them.
//  3. AN UNBOUND GESTURE FIRES NOTHING -- and "nothing" must not fall back to
//     the default.
//  4. TWO GESTURES MAY SHARE ONE ACTION. No conflict detection, no moving.
//  5. CLEARING EVERY ZEN BINDING IS PERMITTED. No guard, by ruling.
//  6. THE ZONE BOUNDARIES are g_cardTopPx and the paper's bottom, and a landing
//     point between them has no override at all.
//  7. ZEN SCOPE IS A PROPERTY OF THE GESTURE AND ITS ZONE, NEVER OF THE ACTION
//     -- including the subtle half: an inherited action still takes the ZONE's
//     gate, so a hold above the paper set to Inherit still fires out of zen.
//
// Plus the two drift gates no static_assert can do: the stored integers (a
// binding persists as an integer, so re-pointing one silently changes what a
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

// The value an untouched row answers with: Settings.app registers every
// DefaultValue, so this is what the app actually reads on a clean install.
static int shipped(Gesture g) {
  return static_cast<int>(gesturebind::defaultAction(g));
}

// --- 1. THE DEFAULTS ARE TODAY'S BEHAVIOR ----------------------------------
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

  // EVERY ZONE ROW SHIPS BLANK -- except the one that carries the zen toggle.
  // Before this existed, a hold above the paper toggled zen while the same hold
  // anywhere else selected; those are two actions for one gesture, so no single
  // global binding can state both. A blank HoldAbove would inherit Confirm and
  // the zen toggle would silently vanish from the gesture that carries it.
  checkAction(gesturebind::defaultAction(Gesture::HoldAbove), Action::ToggleZen,
              "REGRESSION: the hold above the paper still toggles zen");
  const Gesture kBlank[] = {
      Gesture::TapAbove,   Gesture::SwipeLeftAbove, Gesture::SwipeRightAbove,
      Gesture::TapBelow,   Gesture::SwipeLeftBelow, Gesture::SwipeRightBelow,
      Gesture::HoldBelow};
  for (Gesture g : kBlank)
    checkAction(gesturebind::defaultAction(g), Action::Inherit,
                gesturebind::gestureName(g));

  // No GLOBAL row defaults to Nothing or Inherit. Every one of them DID
  // something before this setting existed; a default of Nothing would be a
  // capability removed by the act of making it configurable, and a global row
  // has nothing to inherit from.
  for (int i = 0; i < gesturebind::kGestureCount; ++i) {
    const Gesture g = static_cast<Gesture>(i);
    if (gesturebind::isZoneRow(g)) continue;
    check(gesturebind::defaultAction(g) != Action::Nothing,
          gesturebind::gestureName(g));
    check(gesturebind::defaultAction(g) != Action::Inherit,
          gesturebind::gestureName(g));
    check(gesturebind::defaultAction(g) != Action::Unset,
          gesturebind::gestureName(g));
  }

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
  // single-finger gesture answers what build 156 answered, in all three zones.
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
      // The swipes, likewise.
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
      // The hold: the 2026-08-27 position split, reproduced by the layers.
      {OneFinger::Hold, Zone::AbovePaper, false, Action::ToggleZen,
       "hold above, zen OFF -> toggle (the way IN)"},
      {OneFinger::Hold, Zone::AbovePaper, true, Action::ToggleZen,
       "hold above, zen ON -> toggle (the way OUT)"},
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
  // what makes the shipped behavior identical to build 156.
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
  std::set<int> seen;
  for (int k = 0; k <= 3; ++k) {
    for (Zone z : {Zone::AbovePaper, Zone::BelowPaper}) {
      const Gesture g =
          gesturebind::zoneGesture(static_cast<OneFinger>(k), z);
      check(g != Gesture::Count, "every one-finger gesture has both overrides");
      check(seen.insert(static_cast<int>(g)).second,
            "no two (gesture, zone) pairs share one row");
    }
  }
  check(seen.size() == 8, "eight override rows: four gestures, two zones");
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
  for (int k = 0; k <= 3; ++k)
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
  checkAction(gesturebind::actionFor(Gesture::FourFingerTap, true,
                                     stored(Action::Confirm)),
              Action::Confirm, "4-finger tap keeps CONFIRM too");
  // Including the zen toggle on several gestures at once, and across layers.
  checkAction(gesturebind::actionFor(Gesture::ThreeFingerTap, true,
                                     stored(Action::ToggleZen)),
              Action::ToggleZen, "3-finger tap toggles zen");
  checkAction(gesturebind::oneFingerAction(OneFinger::Hold, Zone::AbovePaper,
                                           true, stored(Action::ToggleZen), 0),
              Action::ToggleZen, "and so does the hold above the paper");
  checkAction(gesturebind::oneFingerAction(OneFinger::Tap, Zone::Neither, true,
                                           0, stored(Action::ToggleZen)),
              Action::ToggleZen, "and the global tap, if pointed at it");
}

// --- 5. CLEARING EVERY ZEN BINDING IS PERMITTED ----------------------------
static void testZenMayBeLeftUnbound() {
  // Owner ruling 2026-08-28: no guard, no refusal, no warning. If every
  // zen-toggle binding is cleared, zen is unreachable BY GESTURE and that is
  // allowed -- the configuration lives in Settings.app, outside the reader, so
  // it is always recoverable. This test exists so the "missing" guard reads as
  // a decision rather than an oversight, and so nobody adds one back.
  checkAction(gesturebind::actionFor(Gesture::ThreeFingerTap, false,
                                     stored(Action::Nothing)),
              Action::Nothing, "the 3-finger tap may be cleared");
  checkAction(gesturebind::oneFingerAction(OneFinger::Hold, Zone::AbovePaper,
                                           false, stored(Action::Nothing),
                                           stored(Action::Confirm)),
              Action::Nothing, "the hold above the paper may be cleared");
  // ...including by pointing the override at Inherit, so the hold above the
  // paper takes the global Hold and the toggle is gone that way too.
  checkAction(gesturebind::oneFingerAction(OneFinger::Hold, Zone::AbovePaper,
                                           false, stored(Action::Inherit),
                                           stored(Action::Confirm)),
              Action::Confirm,
              "an inherited hold above the paper takes the global action");
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
  // "You configure WHAT a gesture does, never WHEN." Exactly two rows fire
  // outside zen, and they are the two that can get you into it.
  int outside = 0;
  for (int i = 0; i < gesturebind::kGestureCount; ++i)
    if (gesturebind::firesOutsideZen(static_cast<Gesture>(i))) outside++;
  check(outside == 2, "exactly two rows fire outside zen");
  check(gesturebind::firesOutsideZen(Gesture::HoldAbove),
        "the hold above the paper fires outside zen (the way IN)");
  check(gesturebind::firesOutsideZen(Gesture::ThreeFingerTap),
        "the 3-finger tap fires outside zen (the way IN)");
  check(gesturebind::firesOutsideZen(OneFinger::Hold, Zone::AbovePaper),
        "...by landing point, which is how the recognizer asks");
  check(!gesturebind::firesOutsideZen(OneFinger::Hold, Zone::Neither),
        "a hold between the boundaries does not");
  check(!gesturebind::firesOutsideZen(OneFinger::Hold, Zone::BelowPaper),
        "nor one below the paper");
  check(!gesturebind::firesOutsideZen(OneFinger::Tap, Zone::AbovePaper),
        "nor a TAP above the paper -- only the hold gets in");

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
  // make four-finger taps live on every screen in the app.
  checkAction(gesturebind::actionFor(Gesture::FourFingerTap, false,
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
  checkAction(gesturebind::actionFor(Gesture::ThreeFingerTap, false,
                                     stored(Action::Power)),
              Action::Power, "...and so does the 3-finger tap");

  // Every other multi-finger gesture is silent while zen is off, whatever it
  // holds.
  for (int i = 0; i < gesturebind::kGestureCount; ++i) {
    const Gesture g = static_cast<Gesture>(i);
    if (gesturebind::isZoneRow(g) || gesturebind::firesOutsideZen(g)) continue;
    checkAction(gesturebind::actionFor(g, false, stored(Action::Right)),
                Action::Nothing, gesturebind::gestureName(g));
  }
}

// --- 8. THE STORED INTEGERS ------------------------------------------------
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
  check(gesturebind::kGestureCount == 22,
        "22 rows: 14 global, 4 above the paper, 4 below it");
  check(gesturebind::kGlobalActionCount == 10,
        "10 global actions: 7 buttons, Nothing, the zen toggle, the font step");
  check(gesturebind::kZoneActionCount == 11, "...and Inherit makes 11 in a zone");
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

  // The three groups the owner named, in layer order: the base first, then the
  // two overrides.
  const size_t global = xml.find("<string>Gestures</string>");
  const size_t above = xml.find("<string>Above the Paper</string>");
  const size_t below = xml.find("<string>Below the Paper</string>");
  check(global != std::string::npos, "the Gestures group is in Root.plist");
  check(above != std::string::npos, "the Above the Paper group is in Root.plist");
  check(below != std::string::npos, "the Below the Paper group is in Root.plist");
  check(global < above && above < below,
        "the groups read global, above the paper, below the paper");

  // THERE IS NO "ON THE PAPER". Owner ruling: it is not a concept, so it has no
  // row and no key. Asserted absent so a re-add is a conscious act, the same
  // discipline panel_palette_test.cpp applies to the removed page rows -- and
  // because an earlier shape of this feature DID have one.
  const char* onPaperKeys[] = {"gestureTapOnPaper",   "gestureSwipeLeftOnPaper",
                               "gestureSwipeRightOnPaper", "gestureHoldOnPaper",
                               "gestureTapPaper",     "gestureHoldPaper"};
  for (const char* k : onPaperKeys)
    check(xml.find(std::string("<string>") + k + "</string>") ==
              std::string::npos,
          "no row may configure a gesture ON the paper -- it is not a concept");

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
  }

  // The rows sit in the group their layer belongs to. Checked by POSITION
  // rather than by nesting, because a Settings.bundle has no nesting: a
  // PSGroupSpecifier owns every row between it and the next one, so a row that
  // drifts past a group header silently changes which heading it appears under
  // -- and here that would also change which LAYER it is, which is worse.
  for (int i = 0; i < gesturebind::kGestureCount; ++i) {
    const Gesture g = static_cast<Gesture>(i);
    const size_t at =
        xml.find("<string>" + std::string(gesturebind::key(g)) + "</string>");
    if (at == std::string::npos) continue;
    if (g < Gesture::TapAbove)
      check(at > global && at < above, gesturebind::gestureName(g));
    else if (g < Gesture::TapBelow)
      check(at > above && at < below, gesturebind::gestureName(g));
    else
      check(at > below, gesturebind::gestureName(g));
  }

  // The surviving sentinel from panel_palette_test.cpp: the Zen toggle stays at
  // the very top, ahead of everything added here.
  const size_t zenToggle = xml.find("<string>zenModeEnabled</string>");
  check(zenToggle != std::string::npos && zenToggle < global,
        "the Zen toggle still comes first");
}

int main(int argc, char** argv) {
  testDefaultsMatchToday();
  testLayering();
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
