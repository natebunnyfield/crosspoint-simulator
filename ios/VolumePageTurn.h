#pragma once

#include <cstdint>

#include "GestureBindings.h"

// THE VOLUME ROCKER AS A PAGE ROCKER -- the whole decision, in one pure header.
//
// Owner, 2026-09-05, verbatim: *"add ios app setting for hardware volume
// buttons and any volume changes to control back and forward pages (front
// button rocker switch) default to off"*, followed the same day by *"add
// ios app setting ... option to flip volume buttons (default to off)"* --
// the second Settings.bundle row, kFlippedPrefKey below.
//
// iOS has no public volume-button API. The standard technique, and the one
// ios/CrossPointVolumeButtons.mm implements: hold an audio session, observe
// AVAudioSession.outputVolume by KVO, read the DIRECTION off the change,
// inject the press, then put the volume back where it was through a hidden
// MPVolumeView slider so the next press has somewhere to go. Everything that
// can be decided without UIKit is decided here, because every way it can be
// wrong is silent on a device -- a press that turns the wrong way, a restore
// read back as a press and turning the page straight back, a rocker that goes
// dead at one end of the range -- and none of AVAudioSession, KVO or
// MPVolumeView exists on a host to prove it against. Same discipline as
// GestureBindings.h and ZenPrefSync.h; tests/volume_page_turn_test.cpp.
namespace volumepage {

// SUPERSEDED 2026-09-06: THIS IS NO LONGER A FEATURE WITH ITS OWN SWITCHES.
//
// It shipped 2026-09-05 as two bespoke Settings rows -- volumeButtonsTurnPages
// (arm it) and volumeButtonsFlipped (reverse it) -- wired straight to a front-
// rocker page turn. The owner then ruled, 2026-09-06: *"make volume up and
// down an assignable setting like all other gestures."* Both rows are gone and
// the rocker is two ordinary bindings, gestureVolumeUp and gestureVolumeDown,
// in ios/GestureBindings.h.
//
// NOTHING WAS LOST IN THE TRADE, which is the half worth stating because
// removing two shipped switches looks like a regression:
//   * "off"      is both rows bound to Nothing. NOTE that this is no longer
//                the DEFAULT: on 2026-09-06 the owner bound the pair to the
//                page turn the retired switch performed, so the rocker turns
//                pages out of the box and Nothing is the opt-OUT.
//   * "flipped"  is assigning the two rows the other way round.
//   * what is    the rocker can now reach any action the other gestures can,
//     GAINED     not just a page turn.
//
// THE OPT-IN BECAME AN OPT-OUT, and the risk it was hedging is unchanged:
// App Store review has rejected apps for taking the volume rocker over, and
// the audio session is now held out of the box rather than on request. That is
// the owner's call, made knowing it; setting both rows to Nothing restores the
// old behaviour exactly.
//
// EVERYTHING BELOW THIS LINE IS UNCHANGED and is still the whole mechanism:
// the KVO arithmetic, the echo suppression, the resting level and the ends of
// the range. Only the last step -- what a press DOES -- moved out to the
// bindings table. Same discipline as before: every way this can be wrong is
// silent on a device, and none of AVAudioSession, KVO or MPVolumeView exists
// on a host to prove it against.

// The FRONT pair, which is the firmware's page rocker: in the reader Left and
// Right are previous and next page (ReaderUtils::detectPageTurn), in lists
// they are NavPrevious and NavNext. NOT the side pair (Up/Down) -- on this
// fork a side-button tap steps text size (ios/README.md, Controls). The values
// are HalGPIO's BTN_LEFT / BTN_RIGHT, static_asserted against the real
// constants in CrossPointVolumeButtons.mm exactly as gesturebind::kBtnLeft is.
constexpr uint8_t kBtnLeft = 2;
constexpr uint8_t kBtnRight = 3;
constexpr uint8_t kNoButton = 0xFF;

// How long the injected press is held: the same 60 ms the read-aloud page
// turn and the accessibility scroll hand to gpio.queueButtonTap.
constexpr unsigned long kTapHoldMs = 60;

// One rocker press moves outputVolume by 1/16 on an iPhone; the test sweeps
// the range in this step. The adapter does not use it -- direction is read off
// the SIGN of the change, not its size, so a route with a finer step (some
// Bluetooth headsets) still turns pages.
constexpr float kStep = 1.0f / 16.0f;

// A change smaller than this is float noise, not a press. Well under a step.
constexpr float kEpsilon = 0.005f;

// THE ENDS OF THE RANGE. At exactly 0.0 or 1.0 a press further in that
// direction changes nothing, so KVO fires nothing and the rocker goes dead one
// way. The working level is therefore kept off the ends: a level at (or within
// float slop of) either end when the feature arms is moved to the middle, and
// THAT becomes the resting level. The middle rather than one notch in from the
// end, because a slider set to 15/16 has to land there exactly for the next
// press to register and whether MPVolumeView rounds a sub-step value cannot be
// measured from here; 0.5 is unambiguous. kEndMargin sits below one step
// (0.0625) so a level one notch from the end is left where the owner put it.
constexpr float kEndMargin = 0.03f;
constexpr float kMidLevel = 0.5f;

constexpr bool atEnd(float level) {
  return level <= kEndMargin || level >= 1.0f - kEndMargin;
}

// The level to rest at, given what the session reports when the feature arms.
constexpr float restingLevel(float observed) {
  return atEnd(observed) ? kMidLevel : observed;
}

// What one outputVolume change means.
enum class Verdict {
  None,  // no measurable change (float noise, or the same value again)
  Next,  // the level went UP: volume-up = page forward = the front RIGHT button
  Prev,  // the level went DOWN: volume-down = page back = the front LEFT button
  Echo,  // the level landed on the resting value while a restore was pending:
         // our own slider write coming back, not a press
};

// `previous` is the last level the observer saw (the resting level once a
// restore has echoed); `current` is the level KVO just delivered;
// `restorePending` is true from the moment the slider was written until its
// echo has been seen; `resting` is the level that write set.
//
// Echo is judged FIRST. A restore write always produces one KVO event carrying
// the resting level, and read as a press it would turn the page back the way
// it just came -- every press would net to nothing. The one thing this cannot
// tell apart is a REAL press that lands exactly on the resting level while a
// restore is still in flight (a down press racing the restore of an up press);
// that press is read as the echo and lost. Accepted: it takes two presses
// inside the restore's round trip, and the adapter times a stale expectation
// out so it can never swallow a press that comes later.
constexpr Verdict judge(float previous, float current, bool restorePending,
                        float resting) {
  const float dr = current - resting;
  if (restorePending && dr > -kEpsilon && dr < kEpsilon) return Verdict::Echo;
  const float d = current - previous;
  if (d > kEpsilon) return Verdict::Next;
  if (d < -kEpsilon) return Verdict::Prev;
  return Verdict::None;
}

// WHICH GESTURE ROW A VERDICT IS. The direction is read off the sign of the
// level change (judge() above) and nothing else; what that direction then DOES
// is the binding's business, not this header's. That is the whole of the
// 2026-09-06 change: `buttonFor(Verdict, flipped)` returned a hardcoded front-
// rocker button and took the flip setting; this returns a row, and flipping is
// now the owner assigning the two rows the other way round.
//
// Returns Gesture::Count for None and Echo -- there is no row for "nothing
// happened", and an Echo is the restore being read back, which must never fire
// anything or the page turns straight back.
constexpr gesturebind::Gesture gestureFor(Verdict v) {
  switch (v) {
    case Verdict::Next:
      return gesturebind::Gesture::VolumeUp;
    case Verdict::Prev:
      return gesturebind::Gesture::VolumeDown;
    case Verdict::None:
    case Verdict::Echo:
      break;
  }
  return gesturebind::Gesture::Count;
}

// WHETHER TO HOLD THE AUDIO SESSION AT ALL. Taking the rocker over means
// holding an AVAudioSession and putting the level back after every press, and
// doing that while both rows are bound to Nothing would change what the
// phone's own buttons do for no gain -- which is the thing App Store review
// has rejected apps for. So the adapter arms only when at least one row is
// bound, and this is the predicate. `live` answers the CURRENT binding of a
// row, so the caller can pass the same lookup the recognizers use.
template <typename LiveAction>
constexpr bool needsVolumeSession(LiveAction live) {
  return live(gesturebind::Gesture::VolumeUp) != gesturebind::Action::Nothing ||
         live(gesturebind::Gesture::VolumeDown) != gesturebind::Action::Nothing;
}

}  // namespace volumepage
