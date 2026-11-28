#!/usr/bin/env python3
"""Derive the Picco app's Settings.bundle Root.plist from the X3 app's.

The Picco app (ios/CMakeLists.txt, CROSSPOINT_IOS_DEVICE=PICCO) hands every
one-finger touch that lands on the PAGE to the firmware's own touch model and
gesture decoder, as on the device. Everything else is the X3 harness's, since
2026-11-27 (owner: "add ios app settings for volume and all other possible
gestures from crosspoint x3; put zen mode in"): zen, the two-finger gestures,
the motion rows (shake, the volume rocker, the four tilts), the three zones
around the page, and Zen Reading Goal. docs/picco-touch-on-ios-2026-11-25.md,
section 2026-11-27.

So the page is the X3 one, byte for byte, except:

  Dropped   "Gestures -- One Finger", the six global one-finger rows: a
            one-finger touch on the page is the firmware's, and its decoder
            fires exactly what those rows default to (GestureBindings.h,
            Device). On the Picco that layer is fixed at its defaults.
  Changed   Zen Mode ships OFF (the X3's ships on), so the app opens on the
            pad, as it always has.
            "Use the Gestures setting" (a zone row's Inherit) reads "Same as
            on the page", which is what it does here.
            The FooterText of the groups whose prose describes the X3 (Zen,
            the two gesture groups, the three zones).

The X3 page is the input and is never written, so the X3 app cannot change
through this script.

usage: gen_picco_settings_plist.py <x3 Root.plist> <out Root.plist>
"""

import plistlib
import sys

DROP_GROUPS = {"Gestures — One Finger"}
# The six global one-finger rows (GestureBindings.h kRows, OneFinger kinds in
# Zone::Neither). tests/picco_settings_plist_test.py checks this set against
# the header, and tests/gesture_bindings_test.cpp checks offeredOn() against it.
DROPPED_KEYS = {
    "gestureTap", "gestureSwipeLeft", "gestureSwipeRight",
    "gestureSwipeUp", "gestureSwipeDown", "gestureHold",
}
X3_INHERIT = "Use the Gestures setting"
PICCO_INHERIT = "Same as on the page"

NL = "\n"
FOOTER = {
    "Zen": (
        "Just the page: the button pad disappears and the page fills the "
        "screen, with every control on a gesture. A touch that lands on the "
        "page still goes to the Picco's own touch screen, in and out of zen: "
        "tap for the next page or to pick a row, swipe to turn, swipe up for "
        "Back, hold to select. The gestures below are everything else. Shake "
        "the phone to turn zen on or off without leaving the book — or use "
        "the switch below."
    ),
    "Gestures — Two Fingers": (
        "Two-finger gestures work anywhere, the page included, and only in "
        "zen. Each fires once when the fingers lift rather than continuously, "
        "because the reader repaginates on every step. A second finger on the "
        "page ends the first finger's touch, so a two-finger gesture never "
        "also turns the page." + NL + NL +
        "Up and Down are the X3's side buttons: in a book a tap steps the "
        "text size, and elsewhere they move a screenful."
    ),
    "Gestures — Motion": (
        "Gestures that are not touches. The shake arrives as a motion event, "
        "so it works with the screen full of anything at all — and it is the "
        "way into Zen, which is why it is bound by default. The volume "
        "buttons are the Picco's rocker out of the box, in and out of zen: "
        "up is the upper end (next), down the lower end (previous); set both "
        "rows to Nothing and the app leaves the phone’s buttons alone "
        "entirely. The four tilts are measured from however you are holding "
        "the phone when they arm, not from flat, and each fires once per "
        "tilt — bind one and the accelerometer starts; leave them alone and "
        "it never runs."
    ),
    "Above the Paper": (
        "The strip of screen above the sheet — the bezel and the notch. Only "
        "one-finger gestures that START here are configured here; one that "
        "starts on the page belongs to the Picco's touch screen. “Same as on "
        "the page” does what that touch would do on the page; choose anything "
        "else and it wins here only, and Nothing switches it off here. Only "
        "in zen, except the hold, which works in either mode."
    ),
    "Below the Paper": (
        "The band below the sheet, where the button pad sits outside zen mode. "
        "Same rule as above: “Same as on the page” or anything else, in zen."
    ),
    "The Left Margin": (
        "The strip down the left of the screen, beside the page. Same rule "
        "again, in zen. Beside the page itself this strip belongs to the "
        "Picco's left-edge Back swipe, so a touch there goes to the touch "
        "screen as if it had landed on the page's edge; these rows answer "
        "only where the margin runs above or below the page."
    ),
}


def derive(src):
    out = dict(src)
    kept = []
    skipping = False
    for spec in src["PreferenceSpecifiers"]:
        spec = dict(spec)
        if spec.get("Type") == "PSGroupSpecifier":
            title = spec.get("Title") or ""
            skipping = title in DROP_GROUPS
            if title in FOOTER:
                spec["FooterText"] = FOOTER[title]
        if skipping:
            continue
        if spec.get("Key") == "zenModeEnabled":
            spec["DefaultValue"] = False
        if "Titles" in spec:
            spec["Titles"] = [PICCO_INHERIT if t == X3_INHERIT else t
                              for t in spec["Titles"]]
        kept.append(spec)
    out["PreferenceSpecifiers"] = kept
    return out


def main(argv):
    if len(argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    with open(argv[1], "rb") as f:
        src = plistlib.load(f)
    out = derive(src)
    # A renamed group or prose target would otherwise survive silently onto
    # the Picco page in its X3 form.
    titles = {s.get("Title") for s in src["PreferenceSpecifiers"]
              if s.get("Type") == "PSGroupSpecifier"}
    missing = sorted((DROP_GROUPS | set(FOOTER)) - titles)
    if missing:
        print(f"gen_picco_settings_plist: no group titled {missing} in {argv[1]}",
              file=sys.stderr)
        return 1
    keys = [s.get("Key") for s in out["PreferenceSpecifiers"] if s.get("Key")]
    survived = sorted(DROPPED_KEYS & set(keys))
    if survived:
        print(f"gen_picco_settings_plist: one-finger global rows survived: {survived}",
              file=sys.stderr)
        return 1
    if "zenModeEnabled" not in keys:
        print("gen_picco_settings_plist: the Zen switch is missing", file=sys.stderr)
        return 1
    if any(X3_INHERIT in (s.get("Titles") or []) for s in out["PreferenceSpecifiers"]):
        print("gen_picco_settings_plist: an X3 Inherit title survived", file=sys.stderr)
        return 1
    with open(argv[2], "wb") as f:
        plistlib.dump(out, f)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
