#!/usr/bin/env python3
"""Rewrite the GESTURE half of ios/Settings.bundle/Root.plist from the header.

WHY THIS IS GENERATED AND THE REST OF THE PLIST IS NOT.

There are 29 gesture rows (17 global + 12 zone overrides) and each one is a
~34-line ``PSMultiValueSpecifier`` carrying the same eleven or twelve annotated
action labels.  That is close to a thousand lines of XML whose every value is
already stated, exactly once, in ``ios/GestureBindings.h`` -- the key, the
title, the group, the default.  A hand-maintained second copy of that table was
tried at 22 rows and drifted inside a day; ``tests/gesture_bindings_test.cpp``
catches the drift, but catching it after the fact is not as good as not having
two copies.

So the HEADER IS THE SOURCE and this script is the projection.  What lives here
and nowhere else is PRESENTATION prose: the annotated action labels ("Right --
page forward - next item") and each group's FooterText.  Those are owner-facing
English with no meaning to the code, and putting them in a pure C++ header would
be putting the Settings.app copy deck in the decision layer.

    python3 tools/gen_gesture_plist.py           # rewrite Root.plist in place
    python3 tools/gen_gesture_plist.py --check   # exit 1 if it would change

Only the span between the Zen Mode switch and the Screen group is touched;
every other row in Root.plist is left byte for byte alone.
"""

import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HEADER = os.path.join(HERE, "ios", "GestureBindings.h")
PLIST = os.path.join(HERE, "ios", "Settings.bundle", "Root.plist")

NL = "\n"

# The annotated action labels, in the canonical order of kGlobalActions.  These
# are the strings the owner reads; the firmware-button meanings in them were
# verified against the firmware (a side-button tap steps font SIZE on this fork,
# it does not page; a side-button HOLD cycles the reading font) and must not
# drift back into guesses.
ACTION_TITLE = {
    "Nothing": "Nothing",
    "Back": "Back — leave the book · close the screen",
    "Confirm": "Confirm — select · activate the row",
    "Left": "Left — page back · previous item",
    "Right": "Right — page forward · next item",
    "Up": "Up — smaller text in a book · scroll up",
    "Down": "Down — bigger text in a book · scroll down",
    "Power": "Power — sleep, or the reader's short-press setting",
    "ToggleZen": "Toggle Zen Mode",
    "FontFamilyStep": "Next Reading Font",
    "Inherit": "Use the Gestures setting",
    # Offered so a gesture CAN be pointed at it (appended 2026-08-29), but
    # nothing ships bound to it and it is not fully wired -- see the
    # FontFamilyStepBack case in CrossPointZenRecognizers.mm's
    # performGestureAction for what is missing and why.
    "FontFamilyStepBack": "Previous Reading Font",
}

FOOTER = {
    "Gestures — One Finger": (
        "What each gesture does, anywhere on the screen. The two groups at the "
        "bottom of this list can override the one-finger gestures for the strip "
        "above the sheet and the band below it; everywhere else — the page "
        "itself included — these apply." + NL + NL +
        "Two gestures may hold the same action, and any gesture may be set to "
        "Nothing." + NL + NL +
        "The side rocker (Up / Down) steps text size inside a book on this "
        "build — holding a side button changes the reading font — and "
        "scrolls a screenful elsewhere."
    ),
    "Gestures — Two Fingers": (
        "Pinch and rotation are two-finger gestures, so they live here. Each "
        "fires once when the fingers lift rather than continuously, because the "
        "reader repaginates on every step." + NL + NL +
        "Pinch and rotation can both fire from one two-finger gesture while "
        "rotation is set to Nothing — that is deliberate, and it is what keeps "
        "a slightly twisted pinch from being read as a rotation and doing "
        "nothing. Bind rotation and a twist that also squeezes will do both."
    ),
    "Gestures — The Device": (
        "Shake is not a touch: iOS delivers it as a motion event, so it works "
        "with the screen full of anything at all."
    ),
    "Above the Paper": (
        "The strip of screen above the sheet — the bezel and the notch. "
        "Leave a row on “Use the Gestures setting” and it does whatever the "
        "Gestures groups say; choose anything else and it wins here only. "
        "Choosing Nothing switches the gesture off in this strip while it keeps "
        "working everywhere else." + NL + NL +
        "Only one-finger gestures can be overridden by region. A two-finger "
        "gesture is the same gesture wherever it lands."
    ),
    "Below the Paper": (
        "The band below the sheet, where the button pad sits outside zen mode. "
        "Same rule as above: blank inherits, anything else wins here only."
    ),
}


def parse_header(text):
    """(action name -> int, [rows in enum order], [global actions], [zone actions])."""
    actions = {}
    body = re.search(r"enum class Action : int \{(.*?)\};", text, re.S).group(1)
    for name, value in re.findall(r"(\w+)\s*=\s*(\d+)", body):
        actions[name] = int(value)

    def action_list(sym):
        block = re.search(
            r"constexpr Action %s\[\] = \{(.*?)\};" % sym, text, re.S
        ).group(1)
        return re.findall(r"Action::(\w+)", block)

    rows = []
    table = re.search(r"constexpr Row kRows\[\] = \{(.*?)\n\};", text, re.S).group(1)
    pattern = re.compile(
        r"\{Gesture::(\w+), Family::(\w+), (-?\d+), Dir::(\w+), "
        r"OneFinger::(\w+), Zone::(\w+), \"([^\"]*)\", \"([^\"]*)\", \"([^\"]*)\", "
        r"Action::(\w+)\}"
    )
    for m in pattern.finditer(table):
        rows.append(
            dict(
                gesture=m.group(1),
                family=m.group(2),
                fingers=int(m.group(3)),
                dir=m.group(4),
                kind=m.group(5),
                zone=m.group(6),
                key=m.group(7),
                name=m.group(8),
                title=m.group(9),
                default=m.group(10),
            )
        )
    return actions, rows, action_list("kGlobalActions"), action_list("kZoneActions")


def group_of(row):
    """The C++ groupOf(), in Python. Same three questions, same order."""
    if row["zone"] == "AbovePaper":
        return "Above the Paper"
    if row["zone"] == "BelowPaper":
        return "Below the Paper"
    if row["family"] == "Shake":
        return "Gestures — The Device"
    return ("Gestures — One Finger" if row["fingers"] <= 1
            else "Gestures — Two Fingers")


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render(actions, rows, global_actions, zone_actions):
    out = []
    T = "\t"

    def group(title):
        out.append(T * 2 + "<dict>")
        out.append(T * 3 + "<key>FooterText</key>")
        out.append(T * 3 + "<string>%s</string>" % esc(FOOTER[title]))
        out.append(T * 3 + "<key>Title</key>")
        out.append(T * 3 + "<string>%s</string>" % esc(title))
        out.append(T * 3 + "<key>Type</key>")
        out.append(T * 3 + "<string>PSGroupSpecifier</string>")
        out.append(T * 2 + "</dict>")

    def specifier(row, offered):
        out.append(T * 2 + "<dict>")
        out.append(T * 3 + "<key>DefaultValue</key>")
        out.append(T * 3 + "<integer>%d</integer>" % actions[row["default"]])
        out.append(T * 3 + "<key>Key</key>")
        out.append(T * 3 + "<string>%s</string>" % row["key"])
        out.append(T * 3 + "<key>Title</key>")
        out.append(T * 3 + "<string>%s</string>" % esc(row["title"]))
        out.append(T * 3 + "<key>Titles</key>")
        out.append(T * 3 + "<array>")
        for a in offered:
            out.append(T * 4 + "<string>%s</string>" % esc(ACTION_TITLE[a]))
        out.append(T * 3 + "</array>")
        out.append(T * 3 + "<key>Type</key>")
        out.append(T * 3 + "<string>PSMultiValueSpecifier</string>")
        out.append(T * 3 + "<key>Values</key>")
        out.append(T * 3 + "<array>")
        for a in offered:
            out.append(T * 4 + "<integer>%d</integer>" % actions[a])
        out.append(T * 3 + "</array>")
        out.append(T * 2 + "</dict>")

    current = None
    for row in rows:
        g = group_of(row)
        if g != current:
            group(g)
            current = g
        zone = row["zone"] != "Neither"
        specifier(row, zone_actions if zone else global_actions)
    return NL.join(out)


def indent_before(xml, at):
    """The whitespace the Screen group's <dict> sits on, preserved verbatim."""
    line_start = xml.rindex(NL, 0, at) + 1
    return xml[line_start:at]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="exit 1 if Root.plist is not what the header implies")
    args = ap.parse_args()

    header = open(HEADER, encoding="utf-8").read()
    actions, rows, global_actions, zone_actions = parse_header(header)
    block = render(actions, rows, global_actions, zone_actions)

    xml = open(PLIST, encoding="utf-8").read()
    # The span to replace: everything after the Zen Mode switch's own </dict>
    # and before the <dict> that opens the Screen group. Anchored on those two
    # because both are hand-written rows this script must never touch.
    zen = xml.index("<string>zenModeEnabled</string>")
    start = xml.index("</dict>", zen) + len("</dict>")
    screen = xml.index("<string>Screen</string>")
    end = xml.rindex("<dict>", 0, screen)
    updated = xml[:start] + NL + block + NL + indent_before(xml, end) + xml[end:]

    if args.check:
        if updated != xml:
            sys.stderr.write(
                "Root.plist does not match ios/GestureBindings.h; run "
                "tools/gen_gesture_plist.py\n")
            return 1
        print("Root.plist agrees with ios/GestureBindings.h (%d rows)" % len(rows))
        return 0

    open(PLIST, "w", encoding="utf-8").write(updated)
    print("wrote %d gesture rows to %s" % (len(rows), PLIST))
    return 0


if __name__ == "__main__":
    sys.exit(main())
