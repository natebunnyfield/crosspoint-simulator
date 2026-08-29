#pragma once

#include <cstdint>

// WHAT EVERY GESTURE DOES -- the whole rule, in one pure header.
//
// Owner ruling, 2026-08-28 (T-025), verbatim: *"if above and below the paper is
// blank, it should pass through to global configuration. if they are defined,
// they take precedence. there is no 'on the paper', it's just normal
// configuration."*
//
// THE SET, ruled the same day after two rounds. The first shipped only the
// fourteen gestures that happened to be wired; the owner asked for every
// gesture the surface can express; and he then TRIMMED that back to the ones
// worth having on a phone held one-handed:
//
//   Tap (single only)  1 finger, 2 fingers                     2
//   Swipe              1 and 2 fingers x up/down/left/right    8
//   Long press         1 finger, 2 fingers                     2
//   Pinch              in, out                                 2
//   Rotation           clockwise, counter-clockwise            2
//   Shake              --                                      1
//                                                             ---
//                                                              17
//
// WHAT THE TRIM DELIBERATELY LEAVES OUT, so nobody re-adds it as an oversight:
//
//   * NO DOUBLE OR TRIPLE TAPS. This is the one omission with a mechanical
//     consequence worth stating: a double-tap recognizer makes every SINGLE tap
//     wait for it to fail -- about 300 ms -- because until the double-tap
//     window closes a tap cannot know it is single. With no multi-tap in the
//     set, nothing delays the page turn and no recognizer needs a failure
//     requirement. That is why there is no conditional-installation machinery
//     in ios/CrossPointZenRecognizers.mm: there is nothing to disambiguate.
//   * NO 3, 4 OR 5-FINGER GESTURES.
//   * NO SCREEN-EDGE PANS. iOS owns the left edge (the system back swipe), the
//     bottom (the home indicator) and the top (Notification Center); only the
//     right is reliably free, and one edge is not worth a family.
//
// **TWO GESTURES THAT WORKED BEFORE THIS ARE GONE, and that is the ruling, not
// a regression.** The 3-FINGER TAP (toggled zen) and the 4-FINGER TAP (power)
// were removed with the finger counts that carried them; the owner was shown
// that exact consequence and chose it. Power is therefore no longer any
// gesture's default and lives on the pad alone -- it stays in the offered
// ACTIONS, because he may bind it to something, but nothing ships pointing at
// it. tests/gesture_bindings_test.cpp names both removals so the change stays
// pinned rather than incidental.
//
// SO THE MODEL IS LAYERED, NOT THREE PARALLEL ZONES.
//
//   1. GESTURES (global)   the base. All 17, and this is what happens anywhere
//                          on screen unless a zone overrides it.
//   2. ABOVE THE PAPER     the six SINGLE-FINGER gestures (tap, four swipes,
//                          the hold), defaulting to INHERIT (blank).
//   3. BELOW THE PAPER     the same six, the same default.
//
// **THERE IS NO "ON THE PAPER".** The paper is simply where nothing overrides,
// so the global binding applies -- there is no concept, no row, no key and no
// branch for it anywhere. An earlier shape of this header hardcoded the paper's
// behavior as a fixed third case; that was wrong and is gone.
//
// MULTI-FINGER HAS NO ZONE OVERRIDE, by ruling: a two-finger tap is the same
// gesture wherever it lands. Neither does the shake, which has no landing point
// at all. 17 global rows + 12 zone rows = 29.
//
// BLANK AND "NOTHING" ARE DIFFERENT VALUES, and this is the part most likely to
// be got wrong:
//
//   Inherit   fall through to the global binding. The DEFAULT for every zone
//             row, and the only reason the shipped defaults reproduce what the
//             app already did.
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
//  * A GESTURE MAY BE BOUND TO NOTHING, including every gesture at once. There
//    is no guard anywhere in this file and none is wanted.
//  * TWO GESTURES MAY SHARE ONE ACTION. No conflict detection, no moving, no
//    refusal. Each gesture independently resolves its own action and nothing
//    here needs to know what any other gesture holds.
//  * THE ZEN ACTIONS ARE ORDINARY BINDINGS (owner 2026-08-28: *"zen is
//    toggleable in settings. drop this concern."*). Zen has its own switch in
//    Settings.app, so nothing about it is special-cased, protected or warned
//    about here.
//  * ZEN SCOPE IS UNCHANGED. Whether a gesture fires while zen is off is a
//    property of the GESTURE AND THE ZONE IT LANDED IN, and never of the action
//    bound to it: you configure WHAT a gesture does, never WHEN it does it. One
//    case fires outside zen -- the one-finger hold ABOVE the paper. (It was two
//    until the trim took the three-finger tap with it.) Note the GATE is the
//    zone's even when the ACTION came from the global layer: a hold above the
//    paper set to Inherit still fires out of zen, doing whatever the global
//    Hold says.
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
// and today's hold above the paper toggles zen while today's shake steps the
// font family; neither is expressible as a button press, so without them no
// default could state what the app already does. Inherit is the eleventh and
// belongs only to a zone row.
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
// that fault would disable EVERY GESTURE IN THE APP, silently. It means "use
// this row's built-in default" instead, so the worst a lost store can do is
// render the app exactly as it shipped.
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
//
// POWER IS STILL OFFERED even though nothing defaults to it any more: the trim
// took the four-finger tap that carried it, and removing the ACTION as well
// would be removing a capability the owner never asked to lose.
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
// to it -- which is exactly the mistake the owner corrected. It doubles as the
// table's marker for a row that is not a zone override at all.
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

// THE SIX SINGLE-FINGER GESTURES -- the only ones a zone may override.
//
// It was four before 2026-08-28 (tap, the two horizontal swipes, the hold); the
// two VERTICAL swipes joined them, so the count per zone went 4 -> 6 and the
// zone rows 8 -> 12.
enum class OneFinger {
  Tap,
  SwipeLeft,
  SwipeRight,
  SwipeUp,
  SwipeDown,
  Hold,
  Count,
};

constexpr const char* oneFingerName(OneFinger k) {
  switch (k) {
    case OneFinger::Tap: return "tap";
    case OneFinger::SwipeLeft: return "swipe left";
    case OneFinger::SwipeRight: return "swipe right";
    case OneFinger::SwipeUp: return "swipe up";
    case OneFinger::SwipeDown: return "swipe down";
    case OneFinger::Hold: return "hold";
    case OneFinger::Count: break;
  }
  return "?";
}

// WHICH UIKIT RECOGNIZER CLASS A ROW NEEDS. The recognizer file installs one
// object per (family, fingers, parameter) and this is how it knows which.
enum class Family : int {
  Tap,        // UITapGestureRecognizer, one tap
  Swipe,      // UISwipeGestureRecognizer, one direction each
  LongPress,  // UILongPressGestureRecognizer
  Pinch,      // UIPinchGestureRecognizer -- ONE object serves two rows, and
              // WHICH of the two is decided from the measured scale at firing
              // time, not from a field here: the table would then hold a second
              // copy of a fact only UIKit can answer.
  Rotate,     // UIRotationGestureRecognizer -- likewise, from the rotation's
              // sign
  Shake,      // not a recognizer at all: a UIResponder motion event
};

// A swipe's direction.
enum class Dir : int { None, Left, Right, Up, Down };

constexpr const char* dirName(Dir d) {
  switch (d) {
    case Dir::Left: return "left";
    case Dir::Right: return "right";
    case Dir::Up: return "up";
    case Dir::Down: return "down";
    case Dir::None: break;
  }
  return "none";
}

// WHICH SETTINGS.APP GROUP A ROW APPEARS IN.
//
// 29 rows in one flat list is a long scroll with no landmarks, so the global
// layer is sub-grouped BY FINGER COUNT -- the one partition a hand can feel,
// and the one that lets every row inside a group drop its "Two-Finger" prefix
// and read as a short verb. Pinch and rotation sit in Two Fingers because that
// is what they are; the shake has a group of its own because it is not a touch.
enum class Group : int {
  OneFinger,
  TwoFingers,
  Device,
  AbovePaper,
  BelowPaper,
  Count,
};

constexpr int kGroupCount = static_cast<int>(Group::Count);

constexpr const char* groupTitle(Group g) {
  switch (g) {
    case Group::OneFinger: return "Gestures — One Finger";
    case Group::TwoFingers: return "Gestures — Two Fingers";
    case Group::Device: return "Gestures — The Device";
    case Group::AbovePaper: return "Above the Paper";
    case Group::BelowPaper: return "Below the Paper";
    case Group::Count: break;
  }
  return "?";
}

// EVERY CONFIGURABLE ROW.
//
// Ordered exactly as Settings.app lists them, which is what lets the plist
// generator and the positional test walk one sequence rather than two. The
// order is NOT persisted -- a binding is stored under the row's string KEY, and
// the ACTION integers are the only numbers that must never move -- so this
// enum may be re-sorted freely, and was, when the set was re-cut on 2026-08-28.
enum class Gesture : int {
  // ONE FINGER -- the only rows a zone may override.
  TapGlobal,
  SwipeLeftGlobal,
  SwipeRightGlobal,
  SwipeUpGlobal,
  SwipeDownGlobal,
  HoldGlobal,
  // TWO FINGERS -- pinch and rotation ride here; both are two-finger gestures.
  TwoFingerTap,
  TwoFingerSwipeLeft,
  TwoFingerSwipeRight,
  TwoFingerSwipeUp,
  TwoFingerSwipeDown,
  TwoFingerHold,
  Pinch,
  Spread,
  RotateClockwise,
  RotateCounterClockwise,
  // THE DEVICE ITSELF.
  Shake,
  // ABOVE THE PAPER -- overrides, blank by default.
  TapAbove,
  SwipeLeftAbove,
  SwipeRightAbove,
  SwipeUpAbove,
  SwipeDownAbove,
  HoldAbove,
  // BELOW THE PAPER -- overrides, blank by default.
  TapBelow,
  SwipeLeftBelow,
  SwipeRightBelow,
  SwipeUpBelow,
  SwipeDownBelow,
  HoldBelow,
  Count,
};

constexpr int kGestureCount = static_cast<int>(Gesture::Count);

// ONE ROW, ONE PLACE -- key, log name, Settings.app title, recognizer shape,
// zone, and the default. The three parallel switch statements this replaced
// drifted within a day of being written, which is the same argument
// src/SimulatorDials.h makes for the surface dials.
struct Row {
  Gesture gesture;
  Family family;
  int fingers;     // 0 for the shake, which has none
  Dir dir;         // a swipe's direction. None elsewhere.
  OneFinger kind;  // the single-finger kind this row configures, or Count
  Zone zone;       // Neither for a global row
  const char* key;    // the NSUserDefaults key AND the Root.plist row's Key
  const char* name;   // what the [zen] log calls it
  const char* title;  // what Settings.app calls it, inside its group
  Action def;
};

constexpr Row kRows[] = {
  // ONE FINGER -- the only rows a zone may override.
    {Gesture::TapGlobal, Family::Tap, 1, Dir::None, OneFinger::Tap, Zone::Neither, "gestureTap", "tap", "Tap", Action::Right},
    {Gesture::SwipeLeftGlobal, Family::Swipe, 1, Dir::Left, OneFinger::SwipeLeft, Zone::Neither, "gestureSwipeLeft", "swipe left", "Swipe Left", Action::Right},
    {Gesture::SwipeRightGlobal, Family::Swipe, 1, Dir::Right, OneFinger::SwipeRight, Zone::Neither, "gestureSwipeRight", "swipe right", "Swipe Right", Action::Left},
    {Gesture::SwipeUpGlobal, Family::Swipe, 1, Dir::Up, OneFinger::SwipeUp, Zone::Neither, "gestureSwipeUp", "swipe up", "Swipe Up", Action::Nothing},
    {Gesture::SwipeDownGlobal, Family::Swipe, 1, Dir::Down, OneFinger::SwipeDown, Zone::Neither, "gestureSwipeDown", "swipe down", "Swipe Down", Action::Nothing},
    {Gesture::HoldGlobal, Family::LongPress, 1, Dir::None, OneFinger::Hold, Zone::Neither, "gestureHold", "hold", "Hold", Action::Confirm},
  // TWO FINGERS -- pinch and rotation ride here; both are two-finger gestures.
    {Gesture::TwoFingerTap, Family::Tap, 2, Dir::None, OneFinger::Count, Zone::Neither, "gestureTwoFingerTap", "2-finger tap", "Tap", Action::Confirm},
    {Gesture::TwoFingerSwipeLeft, Family::Swipe, 2, Dir::Left, OneFinger::Count, Zone::Neither, "gestureTwoFingerSwipeLeft", "2-finger swipe left", "Swipe Left", Action::Down},
    {Gesture::TwoFingerSwipeRight, Family::Swipe, 2, Dir::Right, OneFinger::Count, Zone::Neither, "gestureTwoFingerSwipeRight", "2-finger swipe right", "Swipe Right", Action::Up},
    {Gesture::TwoFingerSwipeUp, Family::Swipe, 2, Dir::Up, OneFinger::Count, Zone::Neither, "gestureTwoFingerSwipeUp", "2-finger swipe up", "Swipe Up", Action::Back},
    {Gesture::TwoFingerSwipeDown, Family::Swipe, 2, Dir::Down, OneFinger::Count, Zone::Neither, "gestureTwoFingerSwipeDown", "2-finger swipe down", "Swipe Down", Action::Confirm},
    {Gesture::TwoFingerHold, Family::LongPress, 2, Dir::None, OneFinger::Count, Zone::Neither, "gestureTwoFingerHold", "2-finger hold", "Hold", Action::Nothing},
    {Gesture::Pinch, Family::Pinch, 2, Dir::None, OneFinger::Count, Zone::Neither, "gesturePinch", "pinch", "Pinch", Action::Up},
    {Gesture::Spread, Family::Pinch, 2, Dir::None, OneFinger::Count, Zone::Neither, "gestureSpread", "spread", "Spread", Action::Down},
    {Gesture::RotateClockwise, Family::Rotate, 2, Dir::None, OneFinger::Count, Zone::Neither, "gestureRotateClockwise", "rotate clockwise", "Rotate Clockwise", Action::Nothing},
    {Gesture::RotateCounterClockwise, Family::Rotate, 2, Dir::None, OneFinger::Count, Zone::Neither, "gestureRotateCounterClockwise", "rotate counter-clockwise", "Rotate Counter-Clockwise", Action::Nothing},
  // THE DEVICE ITSELF.
    {Gesture::Shake, Family::Shake, 0, Dir::None, OneFinger::Count, Zone::Neither, "gestureShake", "shake", "Shake", Action::FontFamilyStep},
  // ABOVE THE PAPER -- overrides, blank by default.
    {Gesture::TapAbove, Family::Tap, 1, Dir::None, OneFinger::Tap, Zone::AbovePaper, "gestureTapAbove", "tap above the paper", "Tap", Action::Inherit},
    {Gesture::SwipeLeftAbove, Family::Swipe, 1, Dir::Left, OneFinger::SwipeLeft, Zone::AbovePaper, "gestureSwipeLeftAbove", "swipe left above the paper", "Swipe Left", Action::Inherit},
    {Gesture::SwipeRightAbove, Family::Swipe, 1, Dir::Right, OneFinger::SwipeRight, Zone::AbovePaper, "gestureSwipeRightAbove", "swipe right above the paper", "Swipe Right", Action::Inherit},
    {Gesture::SwipeUpAbove, Family::Swipe, 1, Dir::Up, OneFinger::SwipeUp, Zone::AbovePaper, "gestureSwipeUpAbove", "swipe up above the paper", "Swipe Up", Action::Inherit},
    {Gesture::SwipeDownAbove, Family::Swipe, 1, Dir::Down, OneFinger::SwipeDown, Zone::AbovePaper, "gestureSwipeDownAbove", "swipe down above the paper", "Swipe Down", Action::Inherit},
    {Gesture::HoldAbove, Family::LongPress, 1, Dir::None, OneFinger::Hold, Zone::AbovePaper, "gestureHoldAbove", "hold above the paper", "Hold", Action::ToggleZen},
  // BELOW THE PAPER -- overrides, blank by default.
    {Gesture::TapBelow, Family::Tap, 1, Dir::None, OneFinger::Tap, Zone::BelowPaper, "gestureTapBelow", "tap below the paper", "Tap", Action::Inherit},
    {Gesture::SwipeLeftBelow, Family::Swipe, 1, Dir::Left, OneFinger::SwipeLeft, Zone::BelowPaper, "gestureSwipeLeftBelow", "swipe left below the paper", "Swipe Left", Action::Inherit},
    {Gesture::SwipeRightBelow, Family::Swipe, 1, Dir::Right, OneFinger::SwipeRight, Zone::BelowPaper, "gestureSwipeRightBelow", "swipe right below the paper", "Swipe Right", Action::Inherit},
    {Gesture::SwipeUpBelow, Family::Swipe, 1, Dir::Up, OneFinger::SwipeUp, Zone::BelowPaper, "gestureSwipeUpBelow", "swipe up below the paper", "Swipe Up", Action::Inherit},
    {Gesture::SwipeDownBelow, Family::Swipe, 1, Dir::Down, OneFinger::SwipeDown, Zone::BelowPaper, "gestureSwipeDownBelow", "swipe down below the paper", "Swipe Down", Action::Inherit},
    {Gesture::HoldBelow, Family::LongPress, 1, Dir::None, OneFinger::Hold, Zone::BelowPaper, "gestureHoldBelow", "hold below the paper", "Hold", Action::Inherit},
};

static_assert(sizeof(kRows) / sizeof(kRows[0]) == kGestureCount,
              "every Gesture needs exactly one row");

// The table is INDEXED BY THE ENUM, so a row that drifts out of order would
// hand every lookup the wrong answer -- silently, and on a phone. Checked at
// compile time rather than trusted.
constexpr bool rowsAreInEnumOrder() {
  for (int i = 0; i < kGestureCount; ++i)
    if (static_cast<int>(kRows[i].gesture) != i) return false;
  return true;
}
static_assert(rowsAreInEnumOrder(), "kRows must be indexed by Gesture");

// A row that cannot exist, so every accessor has something safe to return for
// Gesture::Count and for an integer from outside the enum.
constexpr Row kNoRow = {Gesture::Count, Family::Shake, 0,  Dir::None, OneFinger::Count,
                        Zone::Neither,  "",            "?", "?",       Action::Nothing};

constexpr const Row& row(Gesture g) {
  return (static_cast<int>(g) >= 0 && static_cast<int>(g) < kGestureCount)
             ? kRows[static_cast<int>(g)]
             : kNoRow;
}

// Is this a ZONE row (an override that may be blank), or a GLOBAL one?
constexpr bool isZoneRow(Gesture g) { return row(g).zone != Zone::Neither; }

constexpr const char* key(Gesture g) { return row(g).key; }
constexpr const char* gestureName(Gesture g) { return row(g).name; }
constexpr const char* rowTitle(Gesture g) { return row(g).title; }

// WHICH GROUP A ROW IS IN, derived rather than stored: the group is entirely a
// function of the zone, the family and the finger count, and a stored copy is
// one more thing that can disagree with the row beside it.
constexpr Group groupOf(Gesture g) {
  const Row& r = row(g);
  if (r.zone == Zone::AbovePaper) return Group::AbovePaper;
  if (r.zone == Zone::BelowPaper) return Group::BelowPaper;
  if (r.family == Family::Shake) return Group::Device;
  return r.fingers <= 1 ? Group::OneFinger : Group::TwoFingers;
}

// THE DEFAULTS REPRODUCE THE PREVIOUS BUILD, MINUS WHAT THE TRIM REMOVED.
//
// An install that never opens Settings.app must behave as build 157 did, with
// exactly two intended exceptions: the 3-finger tap and the 4-finger tap no
// longer exist, so they no longer fire. Twelve global rows carry the live
// mapping they replaced; the five gestures the re-cut ADDED (the two
// one-finger vertical swipes, the two-finger hold, both rotations) are Nothing,
// and every zone row is blank:
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
//   pinch / spread     -> Up/Down    pinch:
//   shake              -> FontFamilyStep   CPXShakeCatcher motionEnded:
//
// **HoldAbove IS THE ONE ZONE ROW THAT IS NOT BLANK.** The reason is only the
// one that applies to every other default here: a one-finger hold ABOVE the
// paper toggles zen today, while the same hold anywhere else selects, and those
// are two actions for one gesture -- no single global binding can state both.
// Left blank it would inherit Confirm, and the hold above the paper would stop
// doing what it does now. It is an ordinary row: point it anywhere, or at
// Nothing, and nothing here objects.
constexpr Action defaultAction(Gesture g) { return row(g).def; }

// DOES THIS GLOBAL ROW SHIP INERT?
//
// Exactly the five gestures the 2026-08-28 re-cut ADDED: the two one-finger
// vertical swipes, the two-finger hold, and both rotations. Asked as a question
// about the DEFAULT rather than about the live binding, so the answer is a
// constant of the build and nothing has to be rebuilt when a binding changes.
//
// WHAT IT IS FOR, and it is not decoration. A recognizer that is installed can
// PREVENT another from recognizing -- UIGestureRecognizer's
// -canPreventGestureRecognizer: defaults to YES -- and pinch and rotation are
// both continuous two-finger gestures, so a real pinch (which always carries a
// few degrees of twist) can be arbitrated to rotation instead. With rotation
// shipping inert that would silently cost the owner the pinch binding he
// already has, on a gesture he has reported as not working once before. The
// same holds for a slow two-finger swipe that pauses long enough to begin the
// new two-finger hold.
//
// So the recognizer file grants simultaneity to any pair where either side
// ships inert: **a gesture that ships doing nothing may never prevent one that
// ships doing something.** Between two rows that both ship bound the answer is
// NO, which is exactly what UIKit does with no delegate at all -- so arbitration
// among the gestures that existed before the re-cut is untouched, which is what
// makes the parity claim above true of the RECOGNIZERS and not only of the
// table.
//
// The road not taken, priced: installing a recognizer only for a BOUND row
// would also fix it, and it is what an earlier draft did -- but a conditional
// set has to be rebuilt when the bindings move, Settings.app edits arrive while
// the app is backgrounded with no notification to hang a rebuild on, and the
// whole apparatus was removed on 2026-08-28 once the double-tap it existed for
// left the set. This is the version that needs no rebuild.
constexpr bool shipsInert(Gesture g) {
  return !isZoneRow(g) && defaultAction(g) == Action::Nothing;
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

// The GLOBAL row for a single-finger gesture. Always exists for a real kind.
//
// The `Count` guard is not decoration. Without it the scan matches the first row
// whose `kind` is Count -- the two-finger tap -- so `globalGesture(Count)`
// answered `TwoFingerTap` and `oneFingerAction(Count, ...)` answered `confirm`.
// No caller passes Count today (all three were checked), but this is a header
// whose whole reason for existing is that every wrong answer in it is silent on
// a phone, and its sibling zoneGesture() has carried the same guard all along.
constexpr Gesture globalGesture(OneFinger k) {
  if (k == OneFinger::Count) return Gesture::Count;
  for (int i = 0; i < kGestureCount; ++i)
    if (kRows[i].kind == k && kRows[i].zone == Zone::Neither)
      return kRows[i].gesture;
  return Gesture::Count;
}

// The ZONE OVERRIDE row, or Gesture::Count where there is none -- which is
// every gesture in Zone::Neither, and every two-finger row and the shake
// everywhere.
constexpr Gesture zoneGesture(OneFinger k, Zone z) {
  if (z == Zone::Neither || k == OneFinger::Count) return Gesture::Count;
  for (int i = 0; i < kGestureCount; ++i)
    if (kRows[i].kind == k && kRows[i].zone == z) return kRows[i].gesture;
  return Gesture::Count;
}

// The zone override for a GLOBAL row, by the row rather than by the kind.
constexpr Gesture zoneRowFor(Gesture globalRow, Zone z) {
  return zoneGesture(row(globalRow).kind, z);
}

// DOES THIS GESTURE FIRE WHILE ZEN IS OFF?
//
// Fixed at today's answer, and never a function of the action bound to it.
// Exactly ONE row is true: the one-finger hold ABOVE the paper. It was two
// until the 2026-08-28 trim removed the three-finger tap. Everything else lives
// on the zen-only recognizer set, on the shake catcher's own g_zenOn check, or
// on the SDL classifier's `zenBefore` gate.
//
// It is keyed on the ZONE ROW rather than on the global one, which is the whole
// subtlety: a hold above the paper set to Inherit takes its ACTION from the
// global layer and its GATE from here, so it still fires out of zen. The gate
// travels with the landing point, not with the binding.
constexpr bool firesOutsideZen(Gesture g) { return g == Gesture::HoldAbove; }

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
