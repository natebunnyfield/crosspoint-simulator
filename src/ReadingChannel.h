#pragma once

// THE READING-USAGE CHANNEL'S POD, mirrored from the firmware's
// lib/hal/HalGPIO.h.
//
// Same arrangement as ReadAloudChannel.h beside it, and for the same reason:
// the firmware defines this struct at namespace scope in its own HalGPIO.h,
// this repo's src/HalGPIO.h SHADOWS that header on a simulator build, and the
// reader's code names the type unqualified. So the two definitions must stay
// field-identical, and the shared guard macro keeps any translation unit that
// somehow sees both from redefining it.
//
// tests/reading_log_test.cpp cross-checks this against the firmware's copy as
// text where a sibling checkout exists -- the same technique
// sheet_identity_test.cpp uses for the FNV-1a constants, and for the same
// reason: a silently divergent field order here would not fail to compile, it
// would write plausible wrong numbers into a log that is supposed to settle an
// argument.
//
// Design, schema and statistics: docs/reading-experiments.md.

#include <cstdint>

#ifndef CROSSPOINT_READING_PAGE_SAMPLE
#define CROSSPOINT_READING_PAGE_SAMPLE
struct ReadingPageSample {
  // WHICH PAGE. Same tuple publishReaderPageIdentity carries, and it must be
  // computed the same way -- readerBookKey(), never std::hash.
  uint64_t bookKey = 0;
  int32_t spineIndex = 0;
  int32_t pageInSpine = 0;
  // "epub" / "txt" / "xtc". A literal with static lifetime, never owned.
  const char* format = "";

  // HOW MUCH TEXT WAS ON IT. words counts non-blank tokens, chars their UTF-8
  // bytes, lines the PageLine elements that carried any. A reader that cannot
  // count (TXT, XTC -- no laid-out Page to walk) publishes 0/0/0, which the
  // analysis reads as "no denominator" and excludes from every rate rather
  // than treating as an empty page.
  uint32_t words = 0;
  uint32_t chars = 0;
  uint32_t lines = 0;

  // WHAT IT WAS SET TO. Typography only: the host owns its own dials (palette,
  // render scale, polarity) and adds them on its side, so nothing display-side
  // is plumbed through here.
  const char* fontFamily = "";   // SETTINGS.sdFontFamilyName, or "" for built-in
  uint8_t fontPointSize = 0;     // resolved pt for the active family + slot
  uint8_t fontSizeSlot = 0;      // S/M/L/XL, the persisted truth
  uint8_t lineSpacing = 0;       // TIGHT / NORMAL / WIDE
  uint8_t lineGridEnabled = 0;
  uint8_t justifyThresholdChars = 0;
  uint8_t ligaturesEnabled = 0;
  const char* ligaturesOff = "";  // the comma-separated per-pair spec
  uint8_t lineBreakMode = 0;      // SETTINGS.hyphenationEnabled
  uint8_t screenMargin = 0;
};
#endif
