#pragma once

#include <cstdint>

// THE VOLUME ROCKER AS A PAGE ROCKER -- the whole decision, in one pure header.
//
// Owner, 2026-09-05, verbatim: *"add ios app setting for hardware volume
// buttons and any volume changes to control back and forward pages (front
// button rocker switch) default to off"*.
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

// The Settings.bundle row (ios/Settings.bundle/Root.plist) and what an
// untouched install answers. OFF: taking over the volume rocker is something
// App Store review has rejected apps for, and a reader that changes what the
// phone's own buttons do without being asked is a surprise -- so it is opt-in.
// The test pins the plist's DefaultValue to this constant, since
// CrossPointPrefs.mm builds its registration domain from that plist and the
// switch and the app must not disagree.
constexpr const char *kPrefKey = "volumeButtonsTurnPages";
constexpr bool kDefaultEnabled = false;

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

// The button a verdict presses, or kNoButton.
constexpr uint8_t buttonFor(Verdict v) {
  switch (v) {
    case Verdict::Next:
      return kBtnRight;
    case Verdict::Prev:
      return kBtnLeft;
    case Verdict::None:
    case Verdict::Echo:
      break;
  }
  return kNoButton;
}

}  // namespace volumepage
