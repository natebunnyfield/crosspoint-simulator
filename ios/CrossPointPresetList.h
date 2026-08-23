#pragma once

// THE NAMED-PRESET LIST, shared by both page-color editors.
//
// Owner ruling 2026-08-23: "add a Presets row back to the pickers." Every named
// preset became unreachable AS A PRESET on 2026-08-22, when the Settings.app
// palette row left with the other page rows: from then on the only writer of
// the shared preset integer was CrossPointPrefs_claimCustomFor, which can only
// ever point it AT Custom. One ink pick or one gun move and the fifty-odd names
// were gone until the store was edited by hand.
//
// ONE list for both editors, not one each, for the reason src/PanelSource.h
// exists: the two drawers already share a store, and a second implementation of
// "what does choosing Green CRT do" is how the two answers drift. The list is
// PUSHED onto the drawer's own navigation controller -- both are already
// UINavigationControllers, for their Done button -- so neither sheet's detents
// move. That matters for the mixer, which is pinned to the medium detent with
// no grabber by an owner ruling of 2026-08-21 ("the color tray is very
// slideable").
//
// The rows are previewed in the appearance THAT editor renders: light pairs in
// the historical-ink picker, dark pairs in the gun mixer. Same rows, same
// order, both lists complete -- a preset defines both appearances, so hiding
// any of them in either drawer would remove a choice that used to be reachable
// from Settings.app.

#ifdef __OBJC__
#import <UIKit/UIKit.h>

// A pushable list of every named preset, previewed in `dark`'s appearance.
// `onSelect` runs on the main thread after a selection has been applied, so the
// presenting editor can refresh readouts that now describe a page it no longer
// owns.
UIViewController *CrossPointPresetList_make(BOOL dark, void (^onSelect)(void));

// CROSSPOINT_SIM_OPEN_PRESETS=1: push the list as soon as either editor opens.
// The same family as CROSSPOINT_SIM_OPEN_MIXER / _OPEN_INKPICKER, and for the
// same reason -- simctl cannot synthesize a tap, so a screenshot of this screen
// has to be asked for from inside.
BOOL CrossPointPresetList_autoOpen(void);
#endif

#ifdef __cplusplus
extern "C" {
#endif

// Headless: select a preset through the EXACT path a tap takes, including the
// firmware re-render. Driven by CROSSPOINT_SIM_SELECT_PRESET=<int> in the shim,
// the same family as CrossPointInkPicker_applyForTest and
// CrossPointMixer_applyGunsForTest.
void CrossPointPresetList_selectForTest(int preset);

#ifdef __cplusplus
}
#endif
