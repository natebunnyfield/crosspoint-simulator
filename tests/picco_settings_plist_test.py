#!/usr/bin/env python3
"""THE PICCO APP'S SETTINGS PAGE IS WHAT GestureBindings.h SAYS IT OFFERS.

tools/gen_picco_settings_plist.py derives the Picco page from the X3's at
configure time (ios/CMakeLists.txt), so nothing else ever opens the result.
Until 2026-11-27 the page had no zen or gesture rows at all; since then
(owner: "add ios app settings for volume and all other possible gestures from
crosspoint x3; put zen mode in") it carries every gesture row except the six
one-finger GLOBAL rows, whose touches are the firmware's on the Picco. This
pins, against the header rather than against a list typed here:

  * every gesture row the header OFFERS on the Picco is on the page, with the
    X3's key, default, values and group, and the six one-finger globals are not
    (gesturebind::offeredOn is the C++ statement of the same rule, pinned in
    tests/gesture_bindings_test.cpp);
  * the Zen switch is present and ships OFF, and Zen Reading Goal is present;
  * no row still offers the X3's "Use the Gestures setting" wording;
  * every non-gesture row of the X3 page survives byte for byte, and the X3
    page itself is not modified by the generator.
"""
import hashlib
import os
import plistlib
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import gen_gesture_plist  # noqa: E402

X3 = os.path.join(ROOT, "ios", "Settings.bundle", "Root.plist")
GEN = os.path.join(ROOT, "tools", "gen_picco_settings_plist.py")

failures = []


def check(ok, what):
    if not ok:
        failures.append(what)


def offered_on_picco(row):
    # Zone rows and every row that is not a one-finger kind.
    return row["zone"] != "Neither" or row["kind"] == "Count"


x3_before = hashlib.sha256(open(X3, "rb").read()).hexdigest()
with tempfile.TemporaryDirectory() as d:
    out = os.path.join(d, "Root.plist")
    rc = subprocess.run([sys.executable, GEN, X3, out]).returncode
    check(rc == 0, "generator exit %d" % rc)
    picco = plistlib.load(open(out, "rb")) if rc == 0 else {"PreferenceSpecifiers": []}
check(hashlib.sha256(open(X3, "rb").read()).hexdigest() == x3_before,
      "the generator modified the X3 page")

x3 = plistlib.load(open(X3, "rb"))
_, rows, _, _ = gen_gesture_plist.parse_header(
    open(gen_gesture_plist.HEADER, encoding="utf-8").read())


def by_key(plist):
    return {s["Key"]: s for s in plist["PreferenceSpecifiers"] if s.get("Key")}


def group_of_key(plist):
    group, out = None, {}
    for s in plist["PreferenceSpecifiers"]:
        if s.get("Type") == "PSGroupSpecifier":
            group = s.get("Title")
        elif s.get("Key"):
            out[s["Key"]] = group
    return out


pk, xk = by_key(picco), by_key(x3)
pg = group_of_key(picco)
gesture_keys = set()
dropped = 0
for r in rows:
    gesture_keys.add(r["key"])
    if offered_on_picco(r):
        check(r["key"] in pk, "%s offered on the Picco but missing" % r["key"])
        if r["key"] in pk:
            p, x = pk[r["key"]], xk[r["key"]]
            check(p["DefaultValue"] == x["DefaultValue"], "%s default differs" % r["key"])
            check(p["Values"] == x["Values"], "%s values differ" % r["key"])
            check(pg[r["key"]] == gen_gesture_plist.group_of(r), "%s group" % r["key"])
    else:
        dropped += 1
        check(r["key"] not in pk, "%s is a one-finger global row but is on the page" % r["key"])
check(dropped == 6, "expected the six one-finger global rows dropped, got %d" % dropped)

check("zenModeEnabled" in pk, "the Zen switch is missing")
check(pk.get("zenModeEnabled", {}).get("DefaultValue") is False, "Zen must ship OFF on the Picco")
check("readingAllowanceMinutes" in pk, "Zen Reading Goal is missing")
for k, s in pk.items():
    check("Use the Gestures setting" not in (s.get("Titles") or []),
          "%s still says 'Use the Gestures setting'" % k)
# Everything that is not a gesture row or the zen switch is the X3's, unchanged.
for k, s in xk.items():
    if k in gesture_keys or k == "zenModeEnabled":
        continue
    check(pk.get(k) == s, "%s differs from the X3 page" % k)

if failures:
    for f in failures:
        print("FAIL:", f)
    sys.exit(1)
print("picco_settings_plist: %d rows offered, 6 dropped, zen off by default" %
      (len(rows) - 6))
