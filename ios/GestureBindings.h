#pragma once

#include <cstdint>

// WHAT EVERY GESTURE DOES -- the whole rule, in one pure header.
//
// Owner ruling, 2026-08-28 (T-025): the gestures become configurable from
// Settings.app, in THREE groups.
//
//   1. Above the paper   every single-finger gesture, assignable
//   2. Below the paper   every single-finger gesture, assignable
//   3. Multi-finger      no position split, assignable
//
// ON THE PAPER IS FIXED and is not in Settings.app at all. A single-finger
// gesture on the page keeps exactly the behavior it had before this header
// existed -- the tap and the two swipes turn pages, the hold selects. There is
// deliberately no row for it, no key for it, and no "prepared" hook for it.
//
// THE RULES THE OWNER SET, and the ones he set are the only ones here:
//
//  * ZEN MAY BE LEFT UNBOUND. There is no guard, no refusal and no warning
//    anywhere in this file, and the missing guard is not an oversight: if every
//    zen-toggle binding is cleared, zen is unreachable BY GESTURE and that is
//    allowed, because the configuration lives in iOS Settings.app -- outside
//    the reader, on a screen no gesture can lock you out of -- so it is always
//    recoverable.
//  * TWO GESTURES MAY SHARE ONE ACTION. No conflict detection, no moving, no
//    refusal. Each gesture independently resolves its own action and nothing
//    here needs to know what any other gesture holds.
//  * A GESTURE MAY BE BOUND TO NOTHING (Action::Nothing).
//  * ZEN SCOPE IS UNCHANGED. `firesOutsideZen` is a property of the GESTURE and
//    never of the action bound to it: you configure WHAT a gesture does, never
//    WHEN it does it. Exactly two gestures fire outside zen today (the
//    one-finger hold above the paper, and the three-finger tap), exactly as
//    before, whatever they are pointed at.
//
// WHY THIS IS A HEADER AND NOT AN IF-LADDER IN THE RECOGNIZERS. Every way it
// can be wrong is SILENT on a device, and none of them can be driven off-device
// at all -- UIKit recognizers live above SDL, where no input script and no
// simctl can synthesize a touch. A gesture that stops firing reads as the phone
// not delivering it; a gesture that fires the WRONG button reads as the reader
// misbehaving; a binding lost across an update reads as a setting that never
// saved. So the rule is pure, clock-free, free of SDL and UIKit types, and
// truth-tabled in tests/gesture_bindings_test.cpp. Same reason as
// ios/ZenHoldRouting.h beside it, src/HostKeyboardState.h and src/PanelSource.h.
namespace gesturebind {

// WHAT A GESTURE CAN BE POINTED AT.
//
// The vocabulary is the FIRMWARE'S BUTTONS -- the owner was explicit that this
// is the right vocabulary -- plus Nothing, plus the two host actions that have
// no button at all and that a gesture already performs today. Those two are
// here because the shipped defaults have to reproduce today's behavior exactly
// and today's three-finger tap toggles zen while today's shake steps the font
// family; neither is expressible as a button press, so without them no default
// could state what the app already does.
//
// STORED AS AN INTEGER in NSUserDefaults, so this list APPENDS and never
// inserts or re-points: changing what a number means silently changes what a
// saved choice selects. The display ORDER in Root.plist is independent of the
// integer, which is what lets the rows be grouped and sorted freely.
//
// UNSET IS 0, AND THAT IS LOAD-BEARING -- for the packaging fault, not for the
// ordinary untouched key. `-integerForKey:` searches the REGISTRATION domain as
// well as the persistent one, and CrossPointPrefs.mm builds that domain out of
// Root.plist's own DefaultValues, so an untouched gesture normally answers with
// its shipped action rather than with 0. What answers 0 is a store with no
// registration domain at all: an unreadable `Settings.bundle`, which is a real
// packaging fault with its own branch in `ensureDefaults()`. If 0 meant Nothing,
// that fault would disable EVERY GESTURE IN THE APP, silently, including both
// ways into zen. It means "use this gesture's built-in default" instead, so the
// worst a lost store can do is render the app exactly as it shipped.
//
// The corollary matters for diagnostics and is easy to get wrong: the VALUE
// cannot tell you whether the owner set a binding, because the shipped default
// and a deliberate choice of the same action are the same integer. Ask
// `CrossPointPrefs_gestureBindingIsExplicit`, which reads the persistent domain.
enum class Action : int {
  Unset = 0,  // never stored deliberately; resolves to the gesture's default
  Nothing = 1,
  Back = 2,
  Confirm = 3,
  Left = 4,
  Right = 5,
  Up = 6,
  Down = 7,
  Power = 8,
  ToggleZen = 9,
  FontFamilyStep = 10,
};

// The firmware button indices, mirrored from HalGPIO::BTN_* so this header can
// stay free of the HAL. The recognizer that consumes them static_asserts the
// pair, so a renumbering on either side fails the build rather than pressing
// the wrong key.
constexpr int kNoButton = -1;
constexpr int kBtnBack = 0;
constexpr int kBtnConfirm = 1;
constexpr int kBtnLeft = 2;
constexpr int kBtnRight = 3;
constexpr int kBtnUp = 4;
constexpr int kBtnDown = 5;
constexpr int kBtnPower = 6;

// Which button an action presses, or kNoButton for the three that press none.
constexpr int buttonFor(Action a) {
  switch (a) {
    case Action::Back: return kBtnBack;
    case Action::Confirm: return kBtnConfirm;
    case Action::Left: return kBtnLeft;
    case Action::Right: return kBtnRight;
    case Action::Up: return kBtnUp;
    case Action::Down: return kBtnDown;
    case Action::Power: return kBtnPower;
    default: return kNoButton;
  }
}

constexpr const char* actionName(Action a) {
  switch (a) {
    case Action::Unset: return "unset";
    case Action::Nothing: return "nothing";
    case Action::Back: return "back";
    case Action::Confirm: return "confirm";
    case Action::Left: return "left";
    case Action::Right: return "right";
    case Action::Up: return "up";
    case Action::Down: return "down";
    case Action::Power: return "power";
    case Action::ToggleZen: return "toggle zen";
    case Action::FontFamilyStep: return "font family step";
  }
  return "?";
}

// Every action a Settings row may offer, in the order the rows list them.
// Unset is deliberately absent: it is a read-time fallback, not a choice.
constexpr Action kOfferedActions[] = {
    Action::Nothing, Action::Back,  Action::Confirm,   Action::Left,
    Action::Right,   Action::Up,    Action::Down,      Action::Power,
    Action::ToggleZen, Action::FontFamilyStep,
};
constexpr int kOfferedActionCount =
    static_cast<int>(sizeof(kOfferedActions) / sizeof(kOfferedActions[0]));

constexpr bool isOffered(int stored) {
  for (int i = 0; i < kOfferedActionCount; ++i)
    if (static_cast<int>(kOfferedActions[i]) == stored) return true;
  return false;
}

// EVERY CONFIGURABLE GESTURE.
//
// The single-finger set is the set that EXISTS: the deliberate tap, the two
// horizontal swipes, and the hold. There is no one-finger up or down swipe in
// this app and none was added -- the multi-finger list the owner enumerated is
// exactly the multi-finger set the app already had, which is what says his
// "every single-finger gesture" means the same thing.
//
// Each single-finger gesture appears TWICE, once per configurable zone. The
// third zone -- on the paper -- has no entry here at all, because it is fixed;
// see onPaperAction below.
enum class Gesture : int {
  // Group 1: single finger, ABOVE the paper.
  TapAbove,
  SwipeLeftAbove,
  SwipeRightAbove,
  HoldAbove,
  // Group 2: single finger, BELOW the paper.
  TapBelow,
  SwipeLeftBelow,
  SwipeRightBelow,
  HoldBelow,
  // Group 3: multi-finger, wherever it lands.
  TwoFingerTap,
  TwoFingerSwipeLeft,
  TwoFingerSwipeRight,
  TwoFingerSwipeUp,
  TwoFingerSwipeDown,
  ThreeFingerTap,
  FourFingerTap,
  Pinch,
  Spread,
  Shake,
  Count,
};

constexpr int kGestureCount = static_cast<int>(Gesture::Count);

// The NSUserDefaults key, which is also the Root.plist row's Key. One list, so
// a typo cannot make the app read a key Settings.app does not write -- the
// silent failure CrossPointPrefs.mm's checkKnown() exists to catch, made
// impossible here instead.
constexpr const char* key(Gesture g) {
  switch (g) {
    case Gesture::TapAbove: return "gestureTapAbove";
    case Gesture::SwipeLeftAbove: return "gestureSwipeLeftAbove";
    case Gesture::SwipeRightAbove: return "gestureSwipeRightAbove";
    case Gesture::HoldAbove: return "gestureHoldAbove";
    case Gesture::TapBelow: return "gestureTapBelow";
    case Gesture::SwipeLeftBelow: return "gestureSwipeLeftBelow";
    case Gesture::SwipeRightBelow: return "gestureSwipeRightBelow";
    case Gesture::HoldBelow: return "gestureHoldBelow";
    case Gesture::TwoFingerTap: return "gestureTwoFingerTap";
    case Gesture::TwoFingerSwipeLeft: return "gestureTwoFingerSwipeLeft";
    case Gesture::TwoFingerSwipeRight: return "gestureTwoFingerSwipeRight";
    case Gesture::TwoFingerSwipeUp: return "gestureTwoFingerSwipeUp";
    case Gesture::TwoFingerSwipeDown: return "gestureTwoFingerSwipeDown";
    case Gesture::ThreeFingerTap: return "gestureThreeFingerTap";
    case Gesture::FourFingerTap: return "gestureFourFingerTap";
    case Gesture::Pinch: return "gesturePinch";
    case Gesture::Spread: return "gestureSpread";
    case Gesture::Shake: return "gestureShake";
    case Gesture::Count: break;
  }
  return "";
}

constexpr const char* gestureName(Gesture g) {
  switch (g) {
    case Gesture::TapAbove: return "tap above the paper";
    case Gesture::SwipeLeftAbove: return "swipe left above the paper";
    case Gesture::SwipeRightAbove: return "swipe right above the paper";
    case Gesture::HoldAbove: return "hold above the paper";
    case Gesture::TapBelow: return "tap below the paper";
    case Gesture::SwipeLeftBelow: return "swipe left below the paper";
    case Gesture::SwipeRightBelow: return "swipe right below the paper";
    case Gesture::HoldBelow: return "hold below the paper";
    case Gesture::TwoFingerTap: return "2-finger tap";
    case Gesture::TwoFingerSwipeLeft: return "2-finger swipe left";
    case Gesture::TwoFingerSwipeRight: return "2-finger swipe right";
    case Gesture::TwoFingerSwipeUp: return "2-finger swipe up";
    case Gesture::TwoFingerSwipeDown: return "2-finger swipe down";
    case Gesture::ThreeFingerTap: return "3-finger tap";
    case Gesture::FourFingerTap: return "4-finger tap";
    case Gesture::Pinch: return "pinch";
    case Gesture::Spread: return "spread";
    case Gesture::Shake: return "shake";
    case Gesture::Count: break;
  }
  return "?";
}

// THE DEFAULTS ARE BUILD 156'S BEHAVIOR, GESTURE BY GESTURE.
//
// This is the single most important correctness property of the whole feature:
// an install that never opens Settings.app must behave IDENTICALLY to the build
// before the setting existed. Each row below is the live mapping it replaces,
// and tests/gesture_bindings_test.cpp asserts every one of them by name.
//
//   tap / swipe left  -> Right    CrossPointZenRecognizers.mm swipe:, and the
//   swipe right       -> Left     SDL deliberate tap in CrossPointIOSShim.cpp
//                                 (Verb::Down -> BTN_RIGHT). Neither was
//                                 zone-aware, so above, on and below the paper
//                                 all got the same answer -- which is why all
//                                 six single-finger defaults come in pairs.
//   hold above        -> ToggleZen   ZenHoldRouting.h Action::Toggle
//   hold below        -> Confirm     ZenHoldRouting.h Action::Select. The old
//                                 rule had TWO zones and everything at or below
//                                 the paper's top edge was one of them, so the
//                                 strip below the paper selected, exactly as
//                                 the paper itself did.
//   2-swipe left/right -> Down/Up    the font-size pair (swipe:)
//   2-swipe up/down    -> Back/Confirm
//   2-finger tap       -> Confirm    twoTap:
//   3-finger tap       -> ToggleZen  threeTap:
//   4-finger tap       -> Power      fourTap:
//   pinch / spread     -> Up/Down    pinch:
//   shake              -> FontFamilyStep   CPXShakeCatcher motionEnded:
constexpr Action defaultAction(Gesture g) {
  switch (g) {
    case Gesture::TapAbove: return Action::Right;
    case Gesture::SwipeLeftAbove: return Action::Right;
    case Gesture::SwipeRightAbove: return Action::Left;
    case Gesture::HoldAbove: return Action::ToggleZen;
    case Gesture::TapBelow: return Action::Right;
    case Gesture::SwipeLeftBelow: return Action::Right;
    case Gesture::SwipeRightBelow: return Action::Left;
    case Gesture::HoldBelow: return Action::Confirm;
    case Gesture::TwoFingerTap: return Action::Confirm;
    case Gesture::TwoFingerSwipeLeft: return Action::Down;
    case Gesture::TwoFingerSwipeRight: return Action::Up;
    case Gesture::TwoFingerSwipeUp: return Action::Back;
    case Gesture::TwoFingerSwipeDown: return Action::Confirm;
    case Gesture::ThreeFingerTap: return Action::ToggleZen;
    case Gesture::FourFingerTap: return Action::Power;
    case Gesture::Pinch: return Action::Up;
    case Gesture::Spread: return Action::Down;
    case Gesture::Shake: return Action::FontFamilyStep;
    case Gesture::Count: break;
  }
  return Action::Nothing;
}

// A STORED INTEGER, RESOLVED. Anything that is not an offered action -- 0 from
// an unwritten key, a value from a restored backup, a hand-edited plist, a row
// this build does not have -- falls back to the gesture's default. That is the
// safe direction, and it is the same one panelpalette::resolve takes for an
// unknown preset: an unreadable store renders the app as it shipped rather than
// as a device with no gestures.
constexpr Action resolve(Gesture g, int stored) {
  if (!isOffered(stored)) return defaultAction(g);
  return static_cast<Action>(stored);
}

// DOES THIS GESTURE FIRE WHILE ZEN IS OFF?
//
// A property of the GESTURE, fixed at today's answer, and never of the action
// bound to it -- "you configure WHAT a gesture does, never WHEN" (owner,
// 2026-08-28). Exactly two are true, and they are the two that can get you INTO
// zen today: the three-finger tap, and the one-finger hold above the paper.
// Both are always-enabled recognizers for that reason; everything else lives on
// the zen-only verb set, on the shake catcher's own g_zenOn check, or on the
// SDL classifier's `zenBefore` gate.
//
// A consequence the owner accepted explicitly: bind a zen-only gesture to
// ToggleZen and it only gets you OUT. Nothing here refuses that.
constexpr bool firesOutsideZen(Gesture g) {
  return g == Gesture::HoldAbove || g == Gesture::ThreeFingerTap;
}

// THE ONE ENTRY POINT for a configurable gesture. Returns what to do right now,
// given the stored integer for this gesture and whether zen is on.
constexpr Action actionFor(Gesture g, bool zenOn, int stored) {
  if (!zenOn && !firesOutsideZen(g)) return Action::Nothing;
  return resolve(g, stored);
}

// ---------------------------------------------------------------------------
// ZONES, and the fixed middle one.
// ---------------------------------------------------------------------------

// Where a single finger landed, relative to the paper.
//
// The boundaries are the geometry the layout already publishes, in device
// pixels, and no new rect was invented for this:
//
//   paperTopPx      g_cardTopPx -- where black ends and paper begins. Published
//                   on every layout pass in BOTH modes, so the question has an
//                   answer on the launch before zen has ever been entered. This
//                   is the SAME boundary the one-finger hold already split on.
//   paperBottomPx   the bottom edge of g_zenPaper (the page plus the strip down
//                   to the rocker row) -- g_zenRowTopPx, also published by
//                   layoutPad in both modes.
enum class Zone {
  AbovePaper,
  OnPaper,
  BelowPaper,
};

constexpr const char* zoneName(Zone z) {
  return z == Zone::AbovePaper  ? "above"
         : z == Zone::BelowPaper ? "below"
                                 : "on";
}

// A DEGENERATE BOTTOM EDGE COLLAPSES TO THE OLD TWO-ZONE RULE, deliberately.
// If paperBottomPx is not below paperTopPx -- which is what both boundaries read
// before the first layout pass -- there is no below-the-paper zone and
// everything from the paper's top edge down is OnPaper, which is exactly what
// shipped before this header. A geometry that has not been measured yet must not
// invent a third zone out of a zero.
//
// NOTE THIS IS THE PRE-FIRST-PASS CASE ONLY, and not the tablet. The shim's
// `zenPaperBottomPx()` falls back to the PANEL's bottom edge when no rocker row
// has been published -- the same fallback the zen painter itself uses -- so on
// the tablet path, which publishes neither `g_cardTopPx` nor `g_zenRowTopPx`,
// the first present leaves paperTop at 0 and paperBottom at the page's bottom:
// a below-the-paper zone that is real and is measured against the page rather
// than a rocker row. With the shipped defaults nothing follows from it, since
// every Below binding resolves to what OnPaper does, but it is not "no third
// zone" and an editor relying on that would be wrong.
constexpr Zone zoneFor(float yPx, float paperTopPx, float paperBottomPx) {
  if (yPx < paperTopPx) return Zone::AbovePaper;
  if (paperBottomPx > paperTopPx && yPx >= paperBottomPx)
    return Zone::BelowPaper;
  return Zone::OnPaper;
}

// The four single-finger gestures. Each exists in all three zones; two of those
// zones are rows in Settings.app and the third is fixed.
enum class OneFinger {
  Tap,
  SwipeLeft,
  SwipeRight,
  Hold,
};

constexpr const char* oneFingerName(OneFinger k) {
  switch (k) {
    case OneFinger::Tap: return "tap";
    case OneFinger::SwipeLeft: return "swipe left";
    case OneFinger::SwipeRight: return "swipe right";
    case OneFinger::Hold: return "hold";
  }
  return "?";
}

// Which configurable gesture a one-finger gesture in this zone IS.
// Gesture::Count for OnPaper: there is no row, by ruling.
constexpr Gesture oneFingerGesture(OneFinger k, Zone z) {
  if (z == Zone::AbovePaper) {
    switch (k) {
      case OneFinger::Tap: return Gesture::TapAbove;
      case OneFinger::SwipeLeft: return Gesture::SwipeLeftAbove;
      case OneFinger::SwipeRight: return Gesture::SwipeRightAbove;
      case OneFinger::Hold: return Gesture::HoldAbove;
    }
  }
  if (z == Zone::BelowPaper) {
    switch (k) {
      case OneFinger::Tap: return Gesture::TapBelow;
      case OneFinger::SwipeLeft: return Gesture::SwipeLeftBelow;
      case OneFinger::SwipeRight: return Gesture::SwipeRightBelow;
      case OneFinger::Hold: return Gesture::HoldBelow;
    }
  }
  return Gesture::Count;
}

// ON THE PAPER, FIXED FOREVER -- reading gestures on the page stay reading
// gestures on the page. No key, no row, and nothing in Settings.app reaches
// this function. It is the behavior build 156 shipped, written out once.
//
// Zen-gated for the same reason the rest is: the one-finger swipes live on the
// zen-only verb recognizers, the deliberate tap is gated on `zenBefore`, and
// the on-paper hold was already gated on g_zenOn rather than on its recognizer
// (the recognizer is always enabled, because ABOVE the paper it must fire in
// both modes). Outside zen, a one-finger gesture on the page is the pad's or
// nobody's.
constexpr Action onPaperAction(OneFinger k, bool zenOn) {
  if (!zenOn) return Action::Nothing;
  switch (k) {
    case OneFinger::Tap: return Action::Right;        // page forward
    case OneFinger::SwipeLeft: return Action::Right;  // page forward
    case OneFinger::SwipeRight: return Action::Left;  // page back
    case OneFinger::Hold: return Action::Confirm;     // select
  }
  return Action::Nothing;
}

// THE WHOLE ONE-FINGER RULE, in one call. `stored` is the value read for
// oneFingerGesture(k, z) and is ignored on the paper, where nothing is stored.
constexpr Action oneFingerAction(OneFinger k, Zone z, bool zenOn, int stored) {
  const Gesture g = oneFingerGesture(k, z);
  if (g == Gesture::Count) return onPaperAction(k, zenOn);
  return actionFor(g, zenOn, stored);
}

}  // namespace gesturebind
