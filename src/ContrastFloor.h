#pragma once

// THE CONTRAST FLOOR, once.
//
// WCAG 2.x success criterion 1.4.6, Contrast (Enhanced), level AAA: body text
// must reach 7:1 against its background. It is the bar every surface treatment
// in this repo is swept against -- the grain's darkening budget, the
// letterpress paper budget, the scanline field, show-through, the ink and
// paper tables, and the named-preset duplicate check -- and it is why several
// of those dials clamp themselves per palette instead of shipping one global
// amplitude (the removed 10x grain dropped P11 Blue to 5.6:1 and P22R Red to
// about the same, which is exactly the failure this number exists to catch).
//
// It had three definitions on 2026-08-23 -- lightink:: as a double,
// letterpress:: and phosphorgrain:: as floats, each with a comment pointing at
// one of the others -- plus bare 7.0 literals in the tests. They agreed, which
// is the reason to fix it now rather than after they stop agreeing: an
// external standard's number has exactly one correct value, and a floor that
// is 7 in one pass and 6.5 in another is a page that measures legible and
// reads illegible.
//
// DOUBLE here; the two float namespaces narrow it at their own definitions.
// 7.0 is exactly representable in both, so the narrowing is lossless and no
// sweep result moves.

namespace wcag {

inline constexpr double kContrastFloorAAA = 7.0;

}  // namespace wcag
