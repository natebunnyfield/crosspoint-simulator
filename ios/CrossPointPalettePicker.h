#pragma once

#ifdef __cplusplus
extern "C" {
#endif

// The in-app page-colour picker: a modal list of every preset showing its name,
// its actual hex values, and a DAY and NIGHT preview of the real tones.
//
// WHY IT EXISTS RATHER THAN THE SETTINGS ROW. Settings.app can only render a
// row's title as text, so the palette picker there names fifteen colour schemes
// and shows none of them. The one thing that would help -- seeing the colour --
// is the one thing a Settings.bundle cannot do. Emoji squares were tried on
// 2026-08-17 and reverted: there are nine of them against fifteen mostly-pale
// palettes, so seven rows came out identical and three had to be overridden to
// stop the swatch contradicting the name of its own row. Owner: "emojis are
// worthless".
//
// UIKit rather than SDL, because the SDL side of this harness has no text
// rendering at all -- every label on screen is drawn by the FIRMWARE into the
// panel, and the pad draws only shapes. A list of names and hex values needs a
// font, and UIKit already has one, along with scrolling, Dynamic Type and
// VoiceOver for free.
//
// Settings.app keeps its own picker. This is not a second source of truth: both
// write the same NSUserDefaults key, and pollPanelPalette() in the shim notices
// on the next frame either way.
void CrossPointPalettePicker_present(void);

// True while the modal is on screen. The pad reads this so a touch that lands
// on the panel behind the sheet cannot also reach the firmware.
int CrossPointPalettePicker_isOpen(void);

// Called by the picker itself when it goes away, so a second tap can open it
// again. Not for other callers.
void CrossPointPalettePicker_noteDismissed(void);

#ifdef __cplusplus
}
#endif
