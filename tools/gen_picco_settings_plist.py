#!/usr/bin/env python3
"""Derive the Picco app's Settings.bundle Root.plist from the X3 app's.

The Picco app (ios/CMakeLists.txt, CROSSPOINT_IOS_DEVICE=PICCO) does not run
the X3 harness's gesture-to-button layer: its panel touches go to the
firmware's own touch model and gesture decoder, as on the device. So every row
that only configures that layer is dropped, and everything else is kept
byte-for-byte, so the two pages cannot drift apart.

Dropped, by group title:
  Zen                     -- zen mode is the X3 harness's gesture surface
  Gestures -- *           -- gesture -> X3 button bindings
  Above/Below the Paper, The Left Margin -- zone overrides of those bindings
  Zen Reading Goal        -- counted only in zen

usage: gen_picco_settings_plist.py <x3 Root.plist> <out Root.plist>
"""

import plistlib
import sys

DROP_EXACT = {
    "Zen",
    "Above the Paper",
    "Below the Paper",
    "The Left Margin",
    "Zen Reading Goal",
}
DROP_PREFIX = ("Gestures",)


def dropped(title):
    title = title or ""
    return title in DROP_EXACT or title.startswith(DROP_PREFIX)


def derive(src):
    out = dict(src)
    kept = []
    skipping = False
    for spec in src["PreferenceSpecifiers"]:
        if spec.get("Type") == "PSGroupSpecifier":
            skipping = dropped(spec.get("Title"))
        if not skipping:
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
    # Every dropped group must exist in the source: a renamed group would
    # otherwise survive silently onto the Picco page.
    titles = {s.get("Title") for s in src["PreferenceSpecifiers"]
              if s.get("Type") == "PSGroupSpecifier"}
    missing = sorted(DROP_EXACT - titles)
    if missing:
        print(f"gen_picco_settings_plist: no group titled {missing} in {argv[1]}",
              file=sys.stderr)
        return 1
    if any(k.startswith("gesture") or k == "zenModeEnabled"
           for k in (s.get("Key") or "" for s in out["PreferenceSpecifiers"])):
        print("gen_picco_settings_plist: a gesture/zen row survived", file=sys.stderr)
        return 1
    with open(argv[2], "wb") as f:
        plistlib.dump(out, f)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
