#pragma once

// What a finger on the glass means while the FIRMWARE IS ASLEEP.
//
// Owner, 2026-09-06: "can the ios app in zen mode wake up when x3 sim is
// powered down? that's what I keep trying to fix."
//
// A real X3 asleep wakes on its power button and on nothing else. Out of zen
// the phone has one too: the POWER capsule on the pad, which padWatch presses
// through injectButtonDown and the sleep loop takes as a wake. In zen the pad
// does not exist -- padWatch hit-tests nothing (`if (g_zen) break;`) -- so
// the only route into the sleeping firmware was an ACCIDENT of the bindings:
// a gesture whose action happens to resolve to a button (the deliberate tap's
// default Right, a swipe's Left/Right, the hold on the paper) reaches
// gpio.queueButtonTap, and the sleep loop turns a queued tap into a wake
// edge. Everything else did nothing, silently: the four-finger tap the owner
// remembers as Power (its recognizer went with the 2026-08-28 trim, so no
// code sees four fingers at all), a pinch or a shake (a font-family step, a
// channel nobody drains while asleep), any gesture bound to Nothing -- and
// the hold ABOVE the paper did worse than nothing, toggling zen on a glass
// that could not show it, so the eventual wake came up in the other mode.
//
// THE RULE. While the firmware is asleep and the app is in zen, the whole
// glass is the power button: the first finger to land wakes the device, and
// that touch does nothing else (the reboot cancels the recognizers before
// the jump, and the classifier is reset on the way up). A dark, powered-down
// glass offers no affordance, so the one thing a hand can do to it has to be
// the one thing that works. Out of zen nothing changes: the pad's POWER
// capsule stays the wake, as on the device, and a touch on the page while
// asleep is ignored as it always was.
//
// And while asleep, a resolved gesture action that is not a button press is
// SWALLOWED rather than performed: a press is a wake (the sleep loop's
// contract), but toggling zen or stepping a channel on a device that is not
// running is state the wake then inherits with nothing on the glass to
// explain it.
//
// Pure, for the reason every header beside it is: the wrong answer here is
// silent on a device (a tap that does nothing, a wake in the wrong mode), and
// neither the sleep loop nor a UIKit touch can be driven from a host.
namespace sleeptouch {

// A finger has landed. True: press POWER -- queued, because the sleep loop
// consumes a queued tap as a wake and never fires it -- and feed this touch
// to nothing else. False: the ordinary path (the classifier, the pad).
constexpr bool fingerDownWakes(const bool zen, const bool firmwareAsleep) {
  return zen && firmwareAsleep;
}

// A gesture has resolved to an action. True: perform it. False: swallow it,
// because the firmware is asleep and only a button press can reach it.
constexpr bool actionAllowedWhileAsleep(const bool firmwareAsleep,
                                        const bool actionIsButtonPress) {
  return !firmwareAsleep || actionIsButtonPress;
}

}  // namespace sleeptouch
