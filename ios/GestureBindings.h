#pragma once

#include <cstdint>

// WHAT EVERY GESTURE DOES -- the whole rule, in one pure header.
//
// Owner ruling, 2026-08-28 (T-025), verbatim: *"if above and below the paper is
// blank, it should pass through to global configuration. if they are defined,
// they take precedence. there is no 'on the paper', it's just normal
// configuration."*
//
// SO THE MODEL IS LAYERED, NOT THREE PARALLEL ZONES.
//
//   1. GESTURES (global)   the base. Every gesture -- the four single-finger
//                          ones and all ten multi-finger ones -- and this is
//                          what happens anywhere on screen unless a zone
//                          overrides it.
//   2. ABOVE THE PAPER     the four single-finger gestures, defaulting to
//                          INHERIT (blank).
//   3. BELOW THE PAPER     the same four, the same default.
//
// **THERE IS NO "ON THE PAPER".** The paper is simply where nothing overrides,
// so the global binding applies -- there is no concept, no row, no key and no
// branch for it anywhere. An earlier shape of this header hardcoded the paper's
// behavior as a fixed third case; that was wrong and is gone.
//
// MULTI-FINGER HAS NO ZONE OVERRIDE, by ruling: a three-finger tap is the same
// gesture wherever it lands.
//
// BLANK AND "NOTHING" ARE DIFFERENT VALUES, and this is the part most likely to
// be got wrong:
//
//   Inherit   fall through to the global binding. The DEFAULT for every zone
//             row, and the only reason the shipped defaults still reproduce
//             build 156.
//   Nothing   an EXPLICIT override meaning "do nothing in this zone", which is
//             how a gesture is disabled in one region while it keeps working
//             everywhere else. A real use: the owner has twice reported
//             gestures firing accidentally, and the margins are where that
//             happens.
//
// The global group has no Inherit -- there is nothing to inherit from -- so its
// rows offer the actions plus Nothing.
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
//  * A GESTURE MAY BE BOUND TO NOTHING.
//  * ZEN SCOPE IS UNCHANGED. Whether a gesture fires while zen is off is a
//    property of the GESTURE AND THE ZONE IT LANDED IN, and never of the action
//    bound to it: you configure WHAT a gesture does, never WHEN it does it.
//    Exactly two cases fire outside zen today, and they are the two that can get
//    you INTO zen: the three-finger tap, and the one-finger hold above the
//    paper. Note the GATE is the zone's even when the ACTION came from the
//    global layer -- a hold above the paper set to Inherit still fires out of
//    zen, doing whatever the global Hold says.
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
// could state what the app already does. Inherit is the eleventh and belongs
// only to a zone row.
//
// STORED AS AN INTEGER in NSUserDefaults, so this list APPENDS and never
// inserts or re-points: changing what a number means silently changes what a
// saved choice selects. The display ORDER in Root.plist is independent of the
// integer, which is what lets the rows be grouped and sorted freely. Inherit is
// 11 rather than 0 for exactly that reason -- it arrived after the other ten.
//
// UNSET IS 0, AND THAT IS LOAD-BEARING -- for the packaging fault, not for the
// ordinary untouched key. `-integerForKey:` searches the REGISTRATION domain as
// well as the persistent one, and CrossPointPrefs.mm builds that domain out of
// Root.plist's own DefaultValues, so an untouched row normally answers with its
// shipped value rather than with 0. What answers 0 is a store with no
// registration domain at all: an unreadable `Settings.bundle`, which is a real
// packaging fault with its own branch in `ensureDefaults()`. If 0 meant Nothing,
// that fault would disable EVERY GESTURE IN THE APP, silently, including both
// ways into zen. It means "use this row's built-in default" instead, so the
// worst a lost store can do is render the app exactly as it shipped.
//
// The corollary matters for diagnostics and is easy to get wrong: the VALUE
// cannot tell you whether the owner set a binding, because the shipped default
// and a deliberate choice of the same action are the same integer. Ask
// `CrossPointPrefs_gestureBindingIsExplicit`, which reads the persistent domain.
enum class Action : int {
  Unset = 0,  // never stored deliberately; resolves to the row's default
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
  Inherit = 11,  // zone rows only: fall through to the global binding
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

// Which button an action presses, or kNoButton for the four that press none.
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
    case Action::Inherit: return "inherit";
  }
  return "?";
}

// Every action a GLOBAL row offers, in the order the rows list them. Unset is
// deliberately absent (a read-time fallback, not a choice) and so is Inherit
// (there is nothing above the global layer to inherit from).
constexpr Action kGlobalActions[] = {
    Action::Nothing,   Action::Back,  Action::Confirm, Action::Left,
    Action::Right,     Action::Up,    Action::Down,    Action::Power,
    Action::ToggleZen, Action::FontFamilyStep,
};
constexpr int kGlobalActionCount =
    static_cast<int>(sizeof(kGlobalActions) / sizeof(kGlobalActions[0]));

// Every action a ZONE row offers: Inherit FIRST, because it is the default and
// the row's resting state, then the same ten.
constexpr Action kZoneActions[] = {
    Action::Inherit,   Action::Nothing, Action::Back,  Action::Confirm,
    Action::Left,      Action::Right,   Action::Up,    Action::Down,
    Action::Power,     Action::ToggleZen, Action::FontFamilyStep,
};
constexpr int kZoneActionCount =
    static_cast<int>(sizeof(kZoneActions) / sizeof(kZoneActions[0]));

// EVERY CONFIGURABLE ROW.
//
// The single-finger set is the set that EXISTS: the deliberate tap, the two
// horizontal swipes, and the hold. There is no one-finger up or down swipe in
// this app and none was added -- the multi-finger list the owner enumerated is
// exactly the multi-finger set the app already had, which is what says his
// "every single-finger gesture" means the same thing.
//
// Each single-finger gesture appears THREE times: once globally, and once per
// overridable zone. Multi-finger appears once, globally, by ruling.
enum class Gesture : int {
  // Group 1: GESTURES -- the global layer, and the only one multi-finger has.
  TapGlobal,
  SwipeLeftGlobal,
  SwipeRightGlobal,
  HoldGlobal,
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
  // Group 2: ABOVE THE PAPER -- overrides, blank by default.
  TapAbove,
  SwipeLeftAbove,
  SwipeRightAbove,
  HoldAbove,
  // Group 3: BELOW THE PAPER -- overrides, blank by default.
  TapBelow,
  SwipeLeftBelow,
  SwipeRightBelow,
  HoldBelow,
  Count,
};

constexpr int kGestureCount = static_cast<int>(Gesture::Count);

// Is this a ZONE row (an override that may be blank), or a GLOBAL one?
constexpr bool isZoneRow(Gesture g) {
  return g >= Gesture::TapAbove && g < Gesture::Count;
}

// The NSUserDefaults key, which is also the Root.plist row's Key. One list, so
// a typo cannot make the app read a key Settings.app does not write -- the
// silent failure CrossPointPrefs.mm's checkKnown() exists to catch, made
// impossible here instead.
constexpr const char* key(Gesture g) {
  switch (g) {
    case Gesture::TapGlobal: return "gestureTap";
    case Gesture::SwipeLeftGlobal: return "gestureSwipeLeft";
    case Gesture::SwipeRightGlobal: return "gestureSwipeRight";
    case Gesture::HoldGlobal: return "gestureHold";
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
    case Gesture::TapAbove: return "gestureTapAbove";
    case Gesture::SwipeLeftAbove: return "gestureSwipeLeftAbove";
    case Gesture::SwipeRightAbove: return "gestureSwipeRightAbove";
    case Gesture::HoldAbove: return "gestureHoldAbove";
    case Gesture::TapBelow: return "gestureTapBelow";
    case Gesture::SwipeLeftBelow: return "gestureSwipeLeftBelow";
    case Gesture::SwipeRightBelow: return "gestureSwipeRightBelow";
    case Gesture::HoldBelow: return "gestureHoldBelow";
    case Gesture::Count: break;
  }
  return "";
}

constexpr const char* gestureName(Gesture g) {
  switch (g) {
    case Gesture::TapGlobal: return "tap";
    case Gesture::SwipeLeftGlobal: return "swipe left";
    case Gesture::SwipeRightGlobal: return "swipe right";
    case Gesture::HoldGlobal: return "hold";
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
    case Gesture::TapAbove: return "tap above the paper";
    case Gesture::SwipeLeftAbove: return "swipe left above the paper";
    case Gesture::SwipeRightAbove: return "swipe right above the paper";
    case Gesture::HoldAbove: return "hold above the paper";
    case Gesture::TapBelow: return "tap below the paper";
    case Gesture::SwipeLeftBelow: return "swipe left below the paper";
    case Gesture::SwipeRightBelow: return "swipe right below the paper";
    case Gesture::HoldBelow: return "hold below the paper";
    case Gesture::Count: break;
  }
  return "?";
}

// THE DEFAULTS ARE BUILD 156'S BEHAVIOR.
//
// This is the single most important correctness property of the whole feature:
// an install that never opens Settings.app must behave IDENTICALLY to the build
// before the setting existed. Every zone row is therefore blank, and the global
// layer holds the live mapping each row replaces:
//
//   tap / swipe left  -> Right    CrossPointZenRecognizers.mm swipe:, and the
//   swipe right       -> Left     SDL deliberate tap in CrossPointIOSShim.cpp
//                                 (Verb::Down -> BTN_RIGHT). Neither was
//                                 position-aware, so one global binding is the
//                                 whole of what they did.
//   hold              -> Confirm  the zen long-press select.
//   2-swipe left/right -> Down/Up    the font-size pair (swipe:)
//   2-swipe up/down    -> Back/Confirm
//   2-finger tap       -> Confirm    twoTap:
//   3-finger tap       -> ToggleZen  threeTap:
//   4-finger tap       -> Power      fourTap:
//   pinch / spread     -> Up/Down    pinch:
//   shake              -> FontFamilyStep   CPXShakeCatcher motionEnded:
//
// **HoldAbove IS THE ONE ZONE ROW THAT IS NOT BLANK, and it has to be.** Before
// this existed, a one-finger hold ABOVE the paper toggled zen while the same
// hold anywhere else selected -- that is the 2026-08-27 position split. Those
// are two different actions for one gesture, so one global binding cannot state
// both: with HoldAbove blank the hold above the paper would inherit Confirm and
// **the zen toggle would silently disappear from the gesture that carries it**,
// leaving only the three-finger tap as a way in. Build-156 parity is the stated
// overriding property, so the override ships pre-filled. Pointing it at Inherit
// is a perfectly good thing for the owner to do; it is just not the default.
constexpr Action defaultAction(Gesture g) {
  switch (g) {
    // The global layer: today's mapping.
    case Gesture::TapGlobal: return Action::Right;
    case Gesture::SwipeLeftGlobal: return Action::Right;
    case Gesture::SwipeRightGlobal: return Action::Left;
    case Gesture::HoldGlobal: return Action::Confirm;
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
    // The zones: blank, except the one that carries the zen toggle.
    case Gesture::HoldAbove: return Action::ToggleZen;
    case Gesture::TapAbove:
    case Gesture::SwipeLeftAbove:
    case Gesture::SwipeRightAbove:
    case Gesture::TapBelow:
    case Gesture::SwipeLeftBelow:
    case Gesture::SwipeRightBelow:
    case Gesture::HoldBelow:
      return Action::Inherit;
    case Gesture::Count: break;
  }
  return Action::Nothing;
}

// Is this integer one of the actions the row offers?
constexpr bool isOffered(Gesture g, int stored) {
  if (stored == static_cast<int>(Action::Inherit)) return isZoneRow(g);
  for (int i = 0; i < kGlobalActionCount; ++i)
    if (static_cast<int>(kGlobalActions[i]) == stored) return true;
  return false;
}

// A STORED INTEGER, RESOLVED TO WHAT THE ROW HOLDS. Anything the row does not
// offer -- 0 from an unwritten key, a value from a restored backup, a
// hand-edited plist, a row this build does not have, and Inherit stored against
// a GLOBAL row where it would mean nothing -- falls back to that row's default.
// That is the safe direction, and it is the same one panelpalette::resolve takes
// for an unknown preset: an unreadable store renders the app as it shipped
// rather than as a device with no gestures.
//
// Note this may return Action::Inherit. That is not an action; it is the
// answer "this zone does not override", and only the layered resolution below
// may consume it.
constexpr Action resolve(Gesture g, int stored) {
  if (!isOffered(g, stored)) return defaultAction(g);
  return static_cast<Action>(stored);
}

// ---------------------------------------------------------------------------
// ZONES
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
//   paperBottomPx   the bottom edge of the paper (g_zenRowTopPx, the old rocker
//                   row's top), also published by layoutPad in both modes.
//
// `Neither` is geometrically the paper, and that is all it is: a landing point
// no override covers, so the global binding applies. It is deliberately NOT
// named for the paper, because naming it would invite a behavior to be attached
// to it -- which is exactly the mistake the owner corrected.
enum class Zone {
  AbovePaper,
  Neither,
  BelowPaper,
};

// Whole phrases, not adjectives: these go straight into the `[zen]` log lines,
// and "tap neither the paper" is what an adjective produced.
constexpr const char* zoneName(Zone z) {
  return z == Zone::AbovePaper  ? "above the paper"
         : z == Zone::BelowPaper ? "below the paper"
                                 : "in no override zone";
}

// A DEGENERATE BOTTOM EDGE LEAVES ONLY THE TOP BOUNDARY, deliberately. If
// paperBottomPx is not below paperTopPx -- which is what both boundaries read
// before the first layout pass -- there is no below-the-paper zone at all and
// everything from the top boundary down is Neither. A geometry that has not
// been measured yet must not invent a zone out of a zero.
//
// NOTE THIS IS THE PRE-FIRST-PASS CASE ONLY, and not the tablet. The shim's
// `zenPaperBottomPx()` falls back to the PANEL's bottom edge when no rocker row
// has been published -- the same fallback the zen painter itself uses -- so on
// the tablet path, which publishes neither `g_cardTopPx` nor `g_zenRowTopPx`,
// the first present leaves paperTop at 0 and paperBottom at the page's bottom:
// a below-the-paper zone that is real and is measured against the page rather
// than a rocker row. With the shipped defaults nothing follows from it, since
// every Below row is blank and inherits, but it is not "no such zone" and an
// editor relying on that would be wrong.
constexpr Zone zoneFor(float yPx, float paperTopPx, float paperBottomPx) {
  if (yPx < paperTopPx) return Zone::AbovePaper;
  if (paperBottomPx > paperTopPx && yPx >= paperBottomPx)
    return Zone::BelowPaper;
  return Zone::Neither;
}

// The four single-finger gestures.
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

// The GLOBAL row for a single-finger gesture. Always exists.
constexpr Gesture globalGesture(OneFinger k) {
  switch (k) {
    case OneFinger::Tap: return Gesture::TapGlobal;
    case OneFinger::SwipeLeft: return Gesture::SwipeLeftGlobal;
    case OneFinger::SwipeRight: return Gesture::SwipeRightGlobal;
    case OneFinger::Hold: return Gesture::HoldGlobal;
  }
  return Gesture::Count;
}

// The ZONE OVERRIDE row, or Gesture::Count where there is none -- which is
// every gesture in Zone::Neither, and every multi-finger gesture everywhere.
constexpr Gesture zoneGesture(OneFinger k, Zone z) {
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

// DOES THIS GESTURE FIRE WHILE ZEN IS OFF?
//
// Fixed at today's answer, and never a function of the action bound to it.
// Exactly two rows are true, and they are the two that can get you INTO zen:
// the three-finger tap, and the one-finger hold ABOVE the paper. Both are
// always-enabled recognizers for that reason; everything else lives on the
// zen-only verb set, on the shake catcher's own g_zenOn check, or on the SDL
// classifier's `zenBefore` gate.
//
// It is keyed on the ZONE ROW rather than on the global one, which is the whole
// subtlety: a hold above the paper set to Inherit takes its ACTION from the
// global layer and its GATE from here, so it still fires out of zen. The gate
// travels with the landing point, not with the binding.
constexpr bool firesOutsideZen(Gesture g) {
  return g == Gesture::HoldAbove || g == Gesture::ThreeFingerTap;
}

constexpr bool firesOutsideZen(OneFinger k, Zone z) {
  const Gesture zg = zoneGesture(k, z);
  return zg != Gesture::Count && firesOutsideZen(zg);
}

// A MULTI-FINGER GESTURE. One layer, no zone, one stored integer.
constexpr Action actionFor(Gesture g, bool zenOn, int stored) {
  if (!zenOn && !firesOutsideZen(g)) return Action::Nothing;
  const Action a = resolve(g, stored);
  // Inherit can only reach here from a hand-edited plist against a global row,
  // and resolve() has already rejected that -- but a zone row passed to this
  // overload would be a caller bug, and answering "inherit" as if it were an
  // action is the one way it could go unnoticed.
  return a == Action::Inherit ? Action::Nothing : a;
}

// A SINGLE-FINGER GESTURE. THE WHOLE LAYERED RULE.
//
//   if the zone has an override row and that row is not blank -> the override
//   otherwise                                                 -> the global
//
// `zoneStored` is the value read for zoneGesture(k, z) and is ignored where
// there is no such row; `globalStored` is the value read for globalGesture(k).
// Both are fetched by the caller because only the caller can touch
// NSUserDefaults -- this file decides, it does not read.
constexpr Action oneFingerAction(OneFinger k, Zone z, bool zenOn,
                                 int zoneStored, int globalStored) {
  if (!zenOn && !firesOutsideZen(k, z)) return Action::Nothing;
  const Gesture zg = zoneGesture(k, z);
  if (zg != Gesture::Count) {
    const Action za = resolve(zg, zoneStored);
    if (za != Action::Inherit) return za;
  }
  const Action ga = resolve(globalGesture(k), globalStored);
  // The global layer can never itself say Inherit (isOffered rejects it for a
  // global row), so this is belt and braces against a future edit that makes it
  // possible: an Inherit escaping into the recognizers would be dispatched as
  // an unknown action and swallowed.
  return ga == Action::Inherit ? Action::Nothing : ga;
}

}  // namespace gesturebind
