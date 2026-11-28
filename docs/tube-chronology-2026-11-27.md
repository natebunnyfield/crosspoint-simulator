# The Tube picker, in order of invention (2026-11-27)

Owner, verbatim: *"change Tube modal to be sorted by chronological invention
(use md files for this)"*.

The repo's md files dated only one of the seven phosphors before this
(`docs/crt-phosphor-presets.md:223`, P3's registered application "early radar
(c. 1939)"). The rest come from the table that doc's own figures trace to,
*Cathode Ray Tube Phosphors Of Interest To The Experimenter* (the
crt_phosphor_research PDF, curtpalme.com and bunkerofdoom.com copies,
2009-03-15 and 2009-12-20; read with `pdftotext -layout`), and from the order
JEDEC/RMA P-numbers were issued in, which follows registration. Each date
below says which it is.

| Order | Tube | Phosphor (the chemistry the emulation uses) | When | Basis |
|---|---|---|---|---|
| 1 | Amber | P3, Zn8BeSi5O19:Mn | c. 1939 | table: "Early radar (c. 1939)" [read] |
| 2 | Blue | P11, ZnS:Ag | c. 1948 | table: "A*-ZnS:Ag (c. 1948)" [read]; the c. 1948 is the date of the listing the table quotes, so P11 is no later than that |
| 3 | Pale Blue | P22B, ZnS:Ag | 1954 | P22 is the color-TV set (table: "the designation for the set of phosphors used for color TV CRTs" [read]); the first shadow-mask color tubes shipped 1954 [background, earlytelevision.org 15GP22]; ZnS:Ag blue was the set's blue from the start [inferred: same chemistry as P11] |
| 4 | Green | P22G, ZnS:Cu,Al | 1954 (designation) | same set as P22B; the table lists today's sulfide green [read]. The 1954 green was not necessarily this chemistry [not checked], so this places it by its designation |
| 5 | Yellow | P28, (Zn,Cd)S:Cu,Cl | mid-1950s | NO date in any source read; placed by P-number, after P22 and before P31, which Tektronix's wiki has dominant by the late 1950s [inferred] |
| 6 | Red | P22R, Y2O2S:Eu | 1964 or later | a europium rare-earth red, the family introduced in color tubes in June 1964 (US 4,191,662's background [search summary, not read]); the oxysulfide itself may be a few years later [not checked]. The 1954 set's red was a different, non-rare-earth phosphor, so P22R as emulated is the 1960s one |
| 7 | Pale Red | P56, Y2O3:Eu | after P22R | Y2O3:Eu is one of the three first rare-earth reds (same patent background [search summary]); P56 is a much later number than P22, a projection-tube registration [inferred from the number; no date found] |
| 8 | Mixed | the frozen four-gun blend (P45, P20, P38, P22R) | 2026-08 | the owner's own mix (`src/FrozenPage.h`), so it is the newest tube and sorts last |

**Ties and calls made, not found.** P22B and P22G share a date; blue goes first
because the set is listed blue, green, red nowhere in particular, so this is
arbitrary. Mixed last is literal: it was invented in August 2026. It is still
the default (stored 0); only where the picker lists it moved.

**Storage untouched.** The Tube row persists its stored index, so the order is
`SettingInfo::withDisplayOrder` (crosspoint-reader `src/SettingsList.h`), the
mechanism that exists to reorder a picker without moving a saved value:
display order = stored {5, 1, 2, 3, 4, 6, 7, 0}.

**Not found, and worth a look if the order is ever questioned:** a registration
date for P28 and P56; when Y2O2S:Eu (as opposed to YVO4:Eu) entered production;
the chemistry of the 1954 P22 green.
