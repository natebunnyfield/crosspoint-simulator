#!/usr/bin/env python3
"""ONE EDITOR PER POLARITY, and neither may write the other's fields.

The doctrine, 2026-08-22 (docs/light-ink-picker.md): light mode is paper and
ink and is edited by ios/CrossPointLightInkPicker.mm; dark mode is the CRT and
is edited by ios/CrossPointPaletteMixer.mm. The page-color chip branches on the
live appearance and opens one or the other.

They share ONE store: a preset integer plus four hex fields, two per
appearance. Nothing in that store expresses "this polarity is mine", so the
split is a convention -- and the convention was broken from the day it was
written. `applyGuns` kept writing `panelInkLight` / `panelPaperLight` from the
blend, so a gun moved in dark mode overwrote the light page's chosen ink. Owner
P1, 2026-08-23: "ink is not being picked up."

tests/panel_source_test.cpp pins the RULE, in bytes, through the shipped
decision functions. This file pins that the two editors still obey it, which
the C++ test cannot see: an editor that goes back to writing four fields
compiles, links, passes every other test here, and is only wrong on screen --
and only after the owner has used both halves of a feature.

Deliberately source-level, for the same reason chip_tint_source_test.py is: the
real check needs UIKit, a booted simulator and two appearance switches, and a
test that cannot run in this suite is a test nobody runs.
"""

import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
MIXER = REPO / "ios" / "CrossPointPaletteMixer.mm"
PICKER = REPO / "ios" / "CrossPointLightInkPicker.mm"
PREFS_H = REPO / "ios" / "PanelPrefs.h"
PREFS_MM = REPO / "ios" / "CrossPointPrefs.mm"
SHIM = REPO / "ios" / "CrossPointIOSShim.cpp"
SOURCE = REPO / "src" / "PanelSource.h"
PRESETS = REPO / "ios" / "CrossPointPresetList.mm"

failures = []


def check(ok, msg):
    if not ok:
        failures.append(msg)


def body_of(text, signature, where):
    """The source between `signature` and the first line-start `}`.

    A missing signature is a FAILURE, not a traceback: it means the function
    this test is about has been renamed or deleted, which is precisely when the
    guard must speak up rather than crash and be dismissed as a broken test.
    """
    start = text.find(signature)
    if start < 0:
        failures.append(f"{where} has no `{signature.strip()}` to check")
        return ""
    end = text.find("\n}\n", start)
    return text[start:end] if end > 0 else text[start:]


mixer = MIXER.read_text()
picker = PICKER.read_text()

# 1. THE REPORTED BUG. The dark editor must not name, let alone write, either
#    light hex key. Checked on the whole file rather than on applyGuns, because
#    a helper called from applyGuns would be just as wrong and far less visible.
for key in ("panelInkLight", "panelPaperLight"):
    check(
        key not in mixer,
        f"{MIXER.name} names '{key}'. It is DARK mode's editor (2026-08-22 "
        "doctrine); writing the light pair from it is the owner's P1 of "
        "2026-08-23, where one gun move replaced a chosen Payne's Gray with a "
        "red. The single legal exception -- freezing the light page once, when "
        "this editor claims the shared Custom slot -- goes through "
        "CrossPointPrefs_claimCustomFor.",
    )

# 2. ...and the light editor must not write either dark hex key. Its old
#    inline "dark snapshot" did, and froze only the tones: the dark page kept a
#    named phosphor's colors and lost its trail. Both halves live in the shared
#    claim now.
picker_writes = re.findall(r"forKey:(kInkDark|kPaperDark)\b", picker)
check(
    not picker_writes,
    f"{PICKER.name} writes {sorted(set(picker_writes))} directly. It is LIGHT "
    "mode's editor; the one-time freeze of the dark pair belongs to "
    "CrossPointPrefs_claimCustomFor, which also freezes the dark page's "
    "phosphor -- the half this file used to drop.",
)

# 3. Both editors must actually take the shared claim, and take it BEFORE they
#    write their own fields: it resolves the other polarity's live pair, which
#    is unreachable once the preset has moved to Custom.
for path, text, want_dark in ((MIXER, mixer, "1"), (PICKER, picker, "0")):
    check(
        "CrossPointPrefs_claimCustomFor" in text,
        f"{path.name} never calls CrossPointPrefs_claimCustomFor, so it either "
        "clobbers the other polarity or leaves it resolving from stale hex",
    )
    check(
        "CrossPointPrefs_setPanelPalettePreset" not in text,
        f"{path.name} points the preset at Custom itself instead of through "
        "CrossPointPrefs_claimCustomFor -- which is exactly how the freeze gets "
        "skipped",
    )
    check(
        f"claimCustomFor(/*editingDark=*/{want_dark})" in text,
        f"{path.name} does not claim the slot for the polarity it owns "
        f"(expected editingDark={want_dark})",
    )

# 4. The claim must freeze the other polarity BEFORE the preset moves. Both
#    orderings compile; only one is correct, and the wrong one silently freezes
#    the default hex instead of what was on screen.
claim = body_of(PREFS_MM.read_text(),
                 "void CrossPointPrefs_claimCustomFor(", PREFS_MM.name)
check(
    "panelForPrefs" in claim
    and "setPanelPalettePreset" in claim
    and claim.index("panelForPrefs") < claim.index("setPanelPalettePreset"),
    "CrossPointPrefs_claimCustomFor moves the preset before it resolves the "
    "other polarity; by then the named preset's pair is unreachable",
)
check(
    "panelsource::claimCustom" in claim,
    "CrossPointPrefs_claimCustomFor decides for itself instead of asking "
    "src/PanelSource.h, so the rule has two definitions again",
)

# 5. The glow must not read the raw preset. A Custom slot frozen from a named
#    phosphor IS that phosphor; reading the integer lost it, which is how a
#    light-mode ink pick killed a 283 ms dark-mode trail.
glow = body_of(SHIM.read_text(), "void pollPanelGlow()", SHIM.name)
check(
    "CrossPointPrefs_panelPalettePreset" not in glow,
    "pollPanelGlow reads the stored preset directly again. It must ask "
    "crosspoint::glowPresetForPrefs, or a page frozen from a phosphor stops "
    "glowing.",
)
check(
    "glowPresetForPrefs" in glow,
    "pollPanelGlow does not resolve through crosspoint::glowPresetForPrefs",
)

# 6. One decision point. The adapter fetches; src/PanelSource.h decides.
prefs_h = PREFS_H.read_text()
check(SOURCE.exists(), "src/PanelSource.h is missing")
check(
    "panelsource::panelFor" in prefs_h and "panelsource::glowPreset" in prefs_h,
    "ios/PanelPrefs.h no longer resolves through panelsource:: -- the decision "
    "has moved back into a file no host test can compile",
)
panel_for = body_of(prefs_h, "inline panelpalette::Palette panelForPrefs(bool dark)",
                     PREFS_H.name)
check(
    "panelpalette::resolve" not in panel_for,
    "panelForPrefs resolves the palette itself instead of delegating, so the "
    "iOS answer and the tested answer can drift",
)

# 7. The pad's Accessible pin, at BOTH resolution points. It lived at one of
#    them until 2026-08-23, so the SDL pad drew -4/-5 while the UIKit hide chip
#    drew the stored Current levels.
shim = SHIM.read_text()
levels = body_of(shim, "padpalette::Levels currentLevels(bool dark)", SHIM.name)
check(
    "resolveLevels" not in levels,
    "CrossPointIOSShim.cpp::currentLevels resolves the pad's levels itself "
    "again; it must use crosspoint::padLevelsForPrefs so the UIKit hide chip "
    "cannot get a different answer",
)
check(
    "padLevelsForPrefs" in prefs_h and "shippedLevels" in prefs_h,
    "ios/PanelPrefs.h does not resolve the pad through "
    "padpalette::shippedLevels",
)
pad_pal = body_of(prefs_h, "inline padpalette::Palette padPaletteForPrefs(bool dark)",
                   PREFS_H.name)
check(
    "CrossPointPrefs_padOutlineContrast" not in pad_pal,
    "padPaletteForPrefs hands the raw stored contrasts to makePaletteOn again "
    "-- that is the divergence itself",
)

# 8. THE ROAD BACK OUT OF CUSTOM has exactly one writer too. The two editors
#    can only point the shared integer AT Custom; the Presets list is the only
#    thing that points it back at a name (owner ruling 2026-08-23, "add a
#    Presets row back to the pickers"). It must not do that by hand.
check(PRESETS.exists(), "ios/CrossPointPresetList.mm is missing")
presets = PRESETS.read_text() if PRESETS.exists() else ""
check(
    "CrossPointPrefs_selectPanelPreset" in presets,
    f"{PRESETS.name} does not select through CrossPointPrefs_selectPanelPreset, "
    "so the release has two definitions the way the claim once did",
)
check(
    "CrossPointPrefs_setPanelPalettePreset" not in presets,
    f"{PRESETS.name} writes the preset integer directly, which skips the two "
    "Custom-only keys that have to be cleared with it",
)
for key in ("phosphorMixActive", "panelDarkSnapshotPreset", "panelInkLight",
            "panelPaperLight", "panelInkDark", "panelPaperDark"):
    check(
        key not in presets,
        f"{PRESETS.name} names '{key}'. It is neither polarity's editor and it "
        "does not own the store: everything it changes goes through "
        "CrossPointPrefs_selectPanelPreset.",
    )

# 9. ...and that function must ask src/PanelSource.h and write BOTH Custom-only
#    keys. Clearing only one is the failure the C++ test's naive arm models: a
#    stale mix outranks the frozen phosphor at the next claim, so the dark page
#    decays at the rate of a blend no control can reach.
select = body_of(PREFS_MM.read_text(),
                 "void CrossPointPrefs_selectPanelPreset(", PREFS_MM.name)
check(
    "panelsource::releaseCustom" in select,
    "CrossPointPrefs_selectPanelPreset decides for itself instead of asking "
    "src/PanelSource.h, so the rule has two definitions again",
)
for key in ("kPhosphorMixActive", "kPanelDarkSnapshotPreset"):
    check(
        key in select,
        f"CrossPointPrefs_selectPanelPreset leaves {key} behind. It speaks only "
        "while the slot is Custom, so a stale one is silent until the next "
        "claim and then contradicts the preset the owner just chose.",
    )
check(
    "CrossPointPrefs_setPanelPalettePreset" in select,
    "CrossPointPrefs_selectPanelPreset never moves the preset integer",
)

# 10. ONE LIST, BOTH DRAWERS, each previewing the appearance it renders. Two
#     lists would be two answers to "what does choosing Green CRT do", which is
#     the shape src/PanelSource.h exists to prevent.
for path, text, want_dark in ((MIXER, mixer, "YES"), (PICKER, picker, "NO")):
    check(
        "CrossPointPresetList_make" in text,
        f"{path.name} does not open the shared preset list, so either the "
        "presets are unreachable from it or it grew a list of its own",
    )
    check(
        f"CrossPointPresetList_make(/*dark=*/{want_dark}" in text,
        f"{path.name} previews the preset rows in the wrong appearance "
        f"(expected dark={want_dark}); it renders the other one",
    )
    check(
        "CrossPointPrefs_selectPanelPreset" not in text,
        f"{path.name} selects a preset itself rather than through the shared "
        "list -- one writer, for the same reason there is one claim",
    )

if failures:
    for f in failures:
        print(f"FAIL {f}", file=sys.stderr)
    sys.exit(1)
print("panel source: one editor per polarity, one decision point")
