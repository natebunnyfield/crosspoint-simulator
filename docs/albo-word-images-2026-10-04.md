# Albo's word images in his own books: which letters to reshape (2026-10-04)

Owner, verbatim: *"opus subagent to update md files and take a pass at improving
most common and most neglected word images rendered in my epubs by calling out
which letters need reshaping"*.

**Status: a FINDING pass. Nothing was drawn, built or shipped.** Every letter
below is a question for the owner to rule on, not a decision.

- **Surveyed:** commit `2ad5c37` (round 480, the Bold K) and the four fonts
  built for it: **R** Regular, **I** Italic, **B** Bold, **Z** Bold Italic.
- **Corpus:** his 41 epubs under `~/src/claude-tools/*/epub/` (the files
  `pair_census.py` reads), 667,084 words. Section 1.
- **Pipeline:** the reader's (round 401 on): FreeType with no hinting, the
  converter's 2-bit levels, and HarfBuzz with `kern` and `liga`.
  - Every face is set at Albo's x-height in pixels, at nine reader sizes:
    the X3's 8–18 pt, and the phone's 2x tier at 8, 10 and 12 pt.
- **References:** Georgia, Charter, Palatino and Times New Roman (system
  fonts), and ITC Berkeley Oldstyle in all four cuts. Albertus Medium is
  added in the Regular only.
- **How sure each statement is:**
  - **[measured]**: a number one of the scripts in section 9 prints.
  - **[inferred]**: my reading of why.
  - **[visual]**: seen on the PNGs in section 8.
- **Not duplicated:** the open capitals todo,
  `docs/albo-capitals-audit-2026-10-04.md`. Capitals are cited against it
  (section 4.11). They are not re-proposed.

---

## 0. The answer

**Ranked by how many of his words each one hurts.** "Words hurt" means the
tokens in his books, in that cut, whose word contains the letter.

The Regular is 88.5% of everything he reads, so a fault there outranks the same
fault in another cut. "Ruled" means an owner ruling owns that property. Those
letters are listed so the cost is visible, not proposed.

| # | letter (cut) | words it hurts | what is wrong, measured | direction | sure |
|---|---|---|---|---|---|
| 1 | **a** (R) | 209,894 tokens (36% of the Regular): *and, a, that, what, are, an, have, can* | **+8.7%** darker than the word around it, against the references' a (all 9 sizes above every reference). Its closed counter is 0.24 xh² (references 0.13–0.15; Albertus 0.08) and its hairlines 0.57 of the stem (references 0.33–0.42). It is the darkest letter in *and*, *that*, *are*, *an*, *can* and *each*, all less even than in every reference (*have* sits at the top of the references' range) | **owner's call.** Its height and width were ruled "as is" (2026-09-27), its top stroke T2 (round 462). Its weight was last ruled in round 93 (*"don't thin out a as much"*), on a much older a. If revisited: a smaller counter and lighter hairlines. (The Bold's a is row 7, a width fault, not this one.) | measured |
| 2 | **o** (R) | 182,782 (31%) | **+7.5%** darker (9 of 9 sizes). It carries 11% more band ink than the median reference, and its contrast is 1.98 (references 2.15–2.83) | **ruled**: profile B bowls (round 58); *"the roman o at the owner's pick, 0.93 / 1.10"* (round 226). Listed, not proposed. (The Bold's o is row 7.) | measured |
| 3 | **u** (R, B) | 75,287 R + 6,604 B (13%): *you, about, out, but, your, would, because* | **The u is not the n turned over** (4.1). The n, h and m arches let go of their stem 188–198 units below the x-line. The u's bowl reaches its right stem only 86–92 units above the baseline. Every one of the 21 reference cuts keeps those two within 28 units; Albo keeps them 96–112 apart. In words: **−6.3%** in R (6 of 9 sizes below every reference; watch level) and **−6.7%** in B (8 of 9) | give the u's bowl the n's shoulder, mirrored: rising into the right stem to about 0.44 xh. Round 92 meant to do this (*"same for h m u by construction"*); `g_u` still draws round 51's cubic | measured (structure, color); inferred (fix) |
| 4 | **c** (R) | 77,570 (13%): *which, can, because, each, back, chapter* | **−11.1%** lighter (7 of 9 sizes below every reference). Its mouth is 335 units (references 212–326), the widest of seven faces; its right bearing is 56 (references 3–32). Pairs after the c are 11–13% loose (*ch ca co ce*) | close the mouth by about 50–60 units, with the terminals reaching toward each other; consider narrowing about 5%; then re-bench the c's right side | measured |
| 4i | **c** (I, Z) | 3,010 I (11%): *chain, because, back, country* | **+21.3%** darker (9 of 9): the darkest italic c in the panel. Its ink is 0.58 of its own n's width (references 0.64–0.76), under a heavy drawn top | widen it (`ALBO_ALD_C_W` 0.675 xh). The top is his (F2's top-heavy balance, round 433; the drawn top E1, round 436) and is not proposed. No ruling covers the 400's width | measured |
| 5 | **g** (R, B) | 51,962 R + 4,645 B: *going, things, might, right, English* | **Spacing, not shape.** Its right side is 31–40% tighter than the references' (*ge go gh*) and 22% tighter than its own o. In every reference the g sits 11–47% looser than its own o | bench rows for the g. It has been out of the bench since round 344, and its bearings were measured once (rounds 335 and 340). Its shape is ruled (the open g) | measured |
| 6 | **f** (R, B, I) | 43,802 R + 3,580 B + 2,080 I: *of, for, from, first, before, after* | **−13.4%** lighter in R (8 of 9). Its bar ends 61 units inside its advance, where every reference's ends within 17 units of it. Pairs after the f are 9–16% loose, and *of*, *for* and *from* are three of the least even common words. B: **−10.9%**. I: **−6.7%**: its advance is 374 units against 240–286, and its hook stops 73 units short of the advance (references −19 to +18) | carry the bar to the advance and let the hook overhang as the references' do, then refit the f's right side. Round 430's +16 on the lone f's bar did not close it | measured; visual |
| 7 | **the Bold's widths** (B) | the whole Bold, 48,966 tokens (7.3% of all): *the, The, and, a, in, it, is, English* | **b d p q a g do not widen from R to B** (advance +0.3% to +1.6%), and v w y narrow 4%. Meanwhile n h u m t widen 13% and i l 18%. The references widen every letter alike (medians n 1.05, b 1.09, d 1.04, a 1.07). In bold words, n i h l u read 5–10% light and a o s g w 5–10% dark | **an architectural choice, so options first**: widen the Bold's bowls, a, g, s, o and diagonals by about 8–12%. This is the lowercase twin of the capitals audit's item 2 | measured; inferred (cause) |
| 8 | **k** (R) | 19,182 (3%): *like, kept, work, takes, book, know* | **−7.3%** (8 of 9). Its top quarter, where the arm leaves the stem, holds 0.555 of the n's top-quarter ink (references 0.59–0.74). It has a +47 right bearing where the references' arm or leg overhangs (−5 to −22) | weight in the arm's upper part. That is round 93's own ask (*"the top right serif of 'k' needs more visual weight"*), and it is still the light part. Then a tighter right side | measured |
| 9 | **T** (R, B, I) | 11,438 R + 2,974 B + 907 I: *The* (8,328, the 7th commonest word image), *That, This, Then* | **−13.4%** lighter in R (7 of 9). Its ink is 658 units wide (references 481–556). In *The*, 62 units of white separate the bar's end from the h's stem (references 10–43) | already in the capitals audit (T wide). This pass adds the word evidence. The *Th* white is his own held setting, so the lever is the T | measured |
| 10 | **e** (I, Z) | 14,300 I (52% of italic tokens): *the, times, values, one, page* | **−6.9%** (8 of 9). Its advance is 0.85 of its n (references 0.70–0.89, median 0.77), its ink is 363 units wide (median 328), and its mouth is 232 units (references 176–251) | narrow it about 8% and close the mouth a little | measured |
| 11 | **C G O** (R) | 10,000 together | **−19% / −12% / −8%** (8–9 of 9). Thin: band ink 0.58 / 0.84 / 0.90 of the n (references 0.63–0.78 / 0.90–1.07 / 0.94–1.20) | in the capitals audit ("light rounds"). Cited | measured |
| 12 | **A** (R, I) | 7,347 R + 1,005 I: *A, And, After, As, At, An* | **−12.2%** in R (7 of 9) and **−6.2%** in I. **Not in the capitals audit** | look at it beside the audit's capitals. The mechanism is not isolated: its band ink and advance are each inside the references' range | measured; cause unknown |
| 13 | **I** (R; I, Z) | 5,594 R: *I, It, In, If, I'm* | **+11.3%** darker in R (9 of 9). Its advance is 0.46 of the n (references 0.57–0.67), and the gap after it is tight (*It In Is If*). In I and Z it is **−15% / −12%**: narrow and light | in the capitals audit (I narrow). Cited | measured |
| 14 | **h** (I, Z) | 4,881 I + 2 Z: *the, with, that, what, them* | **+4.3%** in I (6 of 9, watch level) and **+11.7%** in Z (9 of 9). The italic h's ink is 0.92 of its own n's (references 0.97–1.03) and its advance 0.87 (references 0.90–1.00): a squeezed n under an ascender | make the h as wide as the italic n | measured |
| 15 | **v, w** (I) | 1,757 + 1,832 I: *values, even, with, answer, wrong* | **+8.4% / +6.6%** (8 of 9). Heavier band ink: v 0.81 of the n (references 0.63–0.82), w 1.35 (references 1.04–1.29) | one look at the thick strokes. The w's thick strokes (0.86) were the owner's pick of 2026-09-16, made before round 409 moved the italic onto a new nib | measured |
| 16 | **F** (R, I) | 2,275 R + 386 I | **−11.2% / −11.5%**: thin, with band ink 0.62 of the n (references 0.65–0.73). The capitals audit lists the F only as narrow in the bolds | with the audit's capitals | measured |

**Watch, not proposed.** Each is 4–5% off the references and outside their
range at 6 or more of the 9 sizes:

- **d** (R): −4.5%, 97,645 tokens. Same root as the u (4.1).
- **italic s:** −5.2%. It is thin: band ink 0.58 of the n against 0.60–0.75.
- **q** (R): +6.0%.
- **M** (R): −4.0%.
- **y** (B): +4.8%.
- **italic x:** −4.1%.

**Two context facts every number above sits in** [measured]:
- **Albo's Regular is the lightest and the widest word image of the seven
  faces at equal x-height.** Over his 100 commonest words:
  - its words are 3.24 x-heights wide (references 2.47–2.96);
  - its word color is 0.283 (references 0.320–0.452).
- That comes from ruled globals, not from any one letter:
  - the stem: 66.9, round 266;
  - the small x-height against long extenders: cap/xh 1.571 against
    1.40–1.49, ascender 1.80 against 1.43–1.66;
  - the widths and tracking c (round 393).
- Every per-letter number in this doc is measured against Albo's own word
  color, so the light face does not inflate it.
- **By the count of outlier letters, the Regular is a normal text face.** The
  rule in section 3 calls 5 of Albo's 26 lowercase letters: a c f k o. Applied
  to the references against each other, it calls 0–5 (Times 5, Albertus 5).
- The Italic (10) and the Bold (11) are less even than any reference (at
  most 6 and 8).
- The neglected letters (section 2) are mostly fine in the Regular.

---

## 1. The corpus: the most common word images

`instruments/word_corpus.py` reads the files `pair_census.py` and
`outlines/cmp/corpus.py` read: `~/src/claude-tools/*/epub/*.epub`.

**Extraction** follows `stroke_colors.py`:
- content documents only;
- `<head>`, `<style>` and `<script>` dropped;
- entities decoded;
- a word is a run of letters that may hold an inner apostrophe.

**Two additions:**
- **The unit is the surface form.** *The* and *the* are different word
  images, and only one of them starts with a T.
- **Each word carries the cut the reader sets it in**, read from its tags:
  - `em i cite dfn var` → I;
  - `strong b h1–h6 th dt` → B;
  - both → Z.
- CSS-class styling (`.deck`, `blockquote`) is not followed.

**The totals** [measured]:
- 41 files, 667,084 words, 24,875 distinct surface forms.
- By cut: **R 590,338 (88.5%)**, **B 48,966 (7.3%)**, **I 27,629 (4.1%)**,
  **Z 151 (0.02%)**.
- The Bold is mostly headings and labels. The Bold Italic is effectively
  three words: *poly* 70, *kink* 44, *nd* 16.

**Robustness** [measured]:
- 19 cascade re-flows and 3 superseded exports duplicate text: the 2026-09-15
  atlas, sealed-v1 and trivia-v2.
- Dropping them leaves 19 files and 270,397 words. 96 of the top 100 forms are
  the same.
- The order matches `docs/albo-stroke-colors-2026-10-01.md`'s top twenty.

**The 40 commonest** (all cuts):
- the 37,045 · a 16,595 · and 15,898 · is 12,453 · of 8,550 · to 8,461
- The 8,328 · in 8,318 · it 6,979 · that 4,412 · not 4,164 · for 4,067
- with 3,912 · as 3,782 · on 3,590 · one 3,337 · you 3,234 · from 2,664
- no 2,499 · are 2,388 · by 2,334 · was 2,312 · at 2,269 · what 2,071
- an 1,996 · which 1,773 · I 1,738 · A 1,721 · this 1,621 · two 1,552
- its 1,507 · que 1,473 · than 1,471 · or 1,406 · me 1,337 · be 1,306
- her 1,293 · has 1,208 · de 1,194 · have 1,181

Spanish appears from the Spanish books: *que* is 32nd.

**In the Italic:** the 1,220 · a 547 · times 526 · The 450 · of 443 · and 416 ·
Underlying 357 · values 357 · is 344 · from 305.

**In the Bold:** the 2,204 · The 1,995 · and 934 · a 873 · of 603 · in 557 ·
it 540 · is 487 · to 449 · English 413.

**Letter reach in the Regular**, the share of word tokens that contain each
letter [measured]:

- e 48%, t 37%, a 36%, o 31%
- n 30%, s 29%, i 29%, r 28%
- h 21%, d 17%, l 16%, c 13%, u 13%
- m 11%, p 9%, g 9%, y 8%, f 7%, w 7%
- b 6%, v 6%, k 3%, T 2%

The full table is in `corpus.json`.

---

## 2. "Most neglected": the definition, and what it found

**The definition.** A word image is neglected in proportion to how much of
it nobody has worked on. Two records say who worked on what.

1. **Glyph attention.** This is the number of Albo commit subjects naming the
   glyph as the thing worked on, plus the round headings in
   `docs/wedge-serif-exploration.md`.
   - **The sources:** 914 commits touching `tools/wedge_serif` or the Albo
     docs, and 123 headings.
   - **What counts as a mention:** "the [cut] X", "Italic X", or a run of
     single letters such as "h m n r u i l".
   - **References are skipped.** A mention after a comparison word ("as thick
     as the o", "on the n shoulder", "match the i's dot") names a reference,
     not a target.
   - **Family rounds** that name no letters (the arches, rounds 27–30; the
     seventeen word-image adjustments, round 92; rounds 108, 391, 395, 409)
     credit the letters their records name.
   - **Hand-checked:** every count of 8 or less. The exceptions are listed in
     the script (`NOT_TARGET`, `EXTRA_TARGET`, `FAMILY_ROUNDS`), and `--show X`
     prints every subject counted for X.
2. **Pair attention:** whether the pair was ever on his spacing bench. That
   means the 2026-09-20 bench's 396 rows, or any later session's rows in
   `bench/answers/extra-judgments.json`. Roman covers R and B; italic covers
   I and Z.

**The neglect share** of a word is the share of its letters and letter pairs
that nobody worked on:

- its letters in the bottom third of their case by attention;
- plus its pairs that were never benched;
- divided by its letters plus its pairs.

Neglect score = word count × share.

**Glyph attention, lowercase** [measured, hand-checked]:

| letters | named in |
|---|---|
| **l** | **3** |
| **d p v w** | **5** |
| **i** | **6** |
| **q u** | **7** |
| **b h** | **8** |
| n o | 9 |
| f | 10 |
| m | 11 |
| t x z | 13 |
| s | 14 |
| k | 16 |
| c | 21 |
| j | 22 |
| y | 23 |
| r | 34 |
| e | 37 |
| g | 60 |
| a | 78 |

**The capitals:** C 0, O 2, V 3, E H U X 4, B F G I N Z 5; at the top,
R 20, Q 26, K 27.

- **a g e r take 47%** of the 442 lowercase mentions.
- **The ten neglected lowercase letters are b d h i l p q u v w** (8 or
  fewer mentions).
  - They take 13% of the attention.
  - They are 29% of the letters in his 400 commonest words.
  - 69% of the Regular tokens of those 400 words contain at least one of
    them.

**The most neglected word images**, by score [measured]. The tags summarize
the word-evenness check in section 3:

| word | count | neglected letters | evenness against the references |
|---|---|---|---|
| the | 37,045 | h | more even than every reference |
| is | 12,453 | i | more even |
| and | 15,898 | d | **less even**; the cause is the a, not the d |
| in | 8,318 | i | within the references' range |
| it | 6,979 | i | more even |
| I | 1,738 | I | n/a |
| with | 3,912 | w i h | more even |
| The | 8,328 | h | **less even**; the T reads −13% in words (the per-word departure lands on the e, because a pale T lifts its neighbors' relative color) [inferred] |
| which | 1,773 | w h i h | **less even**; the cause is the c |
| by | 2,334 | b | within the range |
| you | 3,234 | u | within the range |
| that | 4,412 | h | **less even**; the cause is the a |
| what | 2,071 | w h | within the range |
| que | 1,473 | q u | **less even**; the cause is the u |
| did | 915 | d i d | within the range |
| this | 1,621 | h i | more even |
| was | 2,312 | w | within the range |
| his, who | 1,141, 1,117 | | within the range |
| all | 1,116 | l l | **less even**; the l reads light beside the dark a, though the l itself is fine (−1.8%) [inferred] |
| be | 1,306 | | more even |
| up | 590 | u p | **less even**; the p departs most (+0.05 of the word's color) |
| but, he, will, would | | | within the range |

**What it found.**
- The least-worked letters are the plain workhorses of the face, and in the
  Regular they mostly hold.
- Every neglected lowercase letter is inside the references' range on color
  in the Regular **except the u**, which is the structural finding of 4.1,
  and the d and the q, at watch level.
- The neglected words that are uneven are uneven because of a letter that
  had plenty of attention: the a in *and* and *that*, the c in *which*, the T
  in *The*.
- The neglected letters' real faults are in the other cuts:
  - the Bold's widths, which leave i l u h n light (4.6);
  - the italic h, squeezed (4.9);
  - the italic v and w, heavy (4.10).

**What the index cannot see** [inferred]:
- Work a commit subject did not name.
- A family pass the record does not resolve to letters.
- The marks. Accented letters take their base letter's attention; the marks
  had rounds 449–455.

So it is an index of who was looked at, not of who is right. Section 3 asks
who is right.

---

## 3. How the words were measured

**`instruments/word_measure.py`** works on his 600 commonest lowercase forms and
80 Title-case forms (ASCII only), across 25 faces × 9 sizes. Each letter
occurrence is weighted by its word's count. It measures:

- **band** is the letter's color in its word:
  - take the letter's slot, its pen position to its advance, kerning
    included;
  - over the rows between the baseline and the x-height, take the slot's mean
    2-bit ink;
  - divide by the whole word's ink in the same rows.
  - 1.00 is exactly the word's own color.
  - Italics shear the slot by the face's measured slant, read off its own l.
  - Ligature glyphs are skipped: fl in R, the f-ligatures in B.
- **gapL / gapR** is measure 5 of `cmp_word_white.py`. In each row of the band
  that both glyphs ink, it takes the white between them, clamps it at the
  face's own n counter, averages, and divides by the face's median gap.
- **knot** is the darkest 0.11-em window in the slot. It turned out to be
  **style, not fault**: 15 of Albo's 26 letters sit 2σ or more from the
  references in R, where the references sit 0–4 from each other, because
  Albo's even-weight rounds have no dark spot to find. In the bolds it
  saturates. It is kept in the JSON and used for nothing.

**The rule** (`instruments/word_callouts.py`):
- **CALL:** at least 5% from the reference median and outside every
  reference's range at 7 or more of the 9 sizes.
- **WATCH:** at least 4% away and outside at 6 or more sizes.
- No single pixel phase can decide it. At the first, three-size pass, the
  `i` read −6%; at nine sizes it is −3.4% and inside the range. It is
  recorded in section 7.

**Validation, against cases whose answer is known** [measured]:
- **The references against each other:** each reference face, judged against
  the others by the same rule.
  - R: Georgia 0, Charter 0, Palatino 2, Berkeley 2, Times 5, Albertus 5.
  - I: 2–6.
  - B: 0–8.
  - Z: 1–8.
- **Albo:** R 5, I 10, B 11, Z 7.
- **The rule's levels agree with round 91's eye.** It found nothing in the
  letters it measured within 6% (h −4%, m +4%, s −6%, v 0%), and acted on
  letters reading 8–19% off.

**`instruments/word_parts.py`** explains the calls:
- each face is drawn unhinted at a 429-unit x-height, italics unsheared by
  their measured slant;
- it reads advances, bearings, ink width, band ink over the n's, the c and e
  mouths, the f and t bar ends against the advance, and the stem joins.

**The per-glyph fit audit was also re-run on round 480**
(`fit_audit/run_geom.py` + `score.py`), on the geometry axes only. Almost all
of its flags are already on that audit's own exclusion list
(`docs/albo-fit-audit-r422-2026-09-27.md` section 4): e, I, Q, the t and M
spacing, J, j, S, l, k, the figures, the italic F, the approved g's and the
ruled Bold Italic r, q, V and W. That is expected:
- it compares a letter with its own construction family;
- it cannot see a whole family that is off, which is its own doc's lesson
  (`albo-fit-audit-2026-09-26.md` 2e);
- the findings here are mostly that kind: the n family against the u, and the
  Bold's stems against its bowls.

**Not re-run: the OCR legibility axis.** The `visionocr` binary is not on this
machine (`find /` found none).

---

## 4. The letters

### 4.1 u (R, B): the n's mirror that was never mirrored [measured]

**The stem joins**, in units at a 429 x-height (`word_parts.py`, the "stem
joins" block). Each cell gives the n's arch depth below the x-line, then the
u's bowl rise above the baseline:

| cut | Albo | Georgia | Charter | Palatino | Times | Berkeley | Albertus |
|---|---|---|---|---|---|---|---|
| R | **188 / 92** | 98 / 92 | 78 / 74 | 128 / 122 | 100 / 100 | 90 / 90 | 96 / 90 |
| B | **198 / 86** | 106 / 96 | 80 / 80 | 118 / 120 | 98 / 98 | 88 / 92 | |
| I | 204 / 204 | 108 / 92 | 124 / 96 | 200 / 200 | 198 / 214 | 196 / 192 | |
| Z | 206 / 202 | 118 / 104 | 126 / 104 | 214 / 196 | 198 / 200 | 194 / 196 | |

- Albo's roman n, h and m have an italic-depth arch (188–192). That is round
  92's lowered shoulder, approved in round 93.
- Its roman u kept a roman-depth bowl.
- Albo's italic matches itself: 204 / 204.

**The consequences** in the Regular:
- The n carries extra ink in the middle of the band, where its arch's
  underside hugs the stem.
- Against the n's middle band, the u has 0.938 of the ink (references
  0.995–1.03), and the d, b, p and q have 0.93–0.97 (references 0.98–1.05).
  The d is the watch item, for the same reason.
- In words: u −6.3% in R and −6.7% in B. *you, about, out, but, would*
  [measured]. In *number*, *under* and *human*, the n and u read as two different
  constructions [visual, `letter-u-R.png`].

**Direction:**
- Mirror the n's shoulder into the u's right stem, so its bowl leaves the stem
  near 0.44 xh rather than 0.21 [inferred].
- `g_u` (`glyphs/arches.py`) still draws round 51's cubic, which ends at
  0.42 xh centerline and thins to `u_end`. Round 92's u switch (on since
  round 93, `pen.ADJ_DEFAULT`) changed only the bowl's weight into the stem
  (0.58 → 0.70) and the right top wedge (0.85). Its `n` switch lowered the
  arch of n, h and m, and round 92's own table said *"same for h m u by
  construction"*.
- The other lever, the n family's depth, is ruled.

### 4.2 c (R): the widest mouth of seven faces [measured]

- **In words:** −11.1%, 0.784 against a median of 0.882, below every
  reference at 7 of 9 sizes.
  - The closest references are Berkeley and Albertus, both near 0.81, the
    open-c faces.
- **Mouth:** 335 units (references 212–326, median 274).
- **Right bearing:** 56 units (references 3–32). It carries round 303's +11 for
  round letters and `BEARING_ADJ` c +15, each set for a closed round letter.
- **Ink width:** 0.82 of its n (references 0.68–0.90; Albertus is the widest,
  at 0.90).
- **Pairs after the c:** *ch* +11%, *ca* +13%, *co* +11%, *ce* +11% against
  the reference median.
- **What it costs:** the c is the letter that departs most in *which*, *cost*
  and *across*. *can*, *case*, *fact*, *call*, *back* and *each* are among the
  least even common words, because the dark a stands next to the pale c.

**Direction** [inferred]:
- Close the mouth toward the reference median, about 50–60 units, by letting
  both terminals reach.
- Then put the c's right side back on the bench: an open letter does not need
  a closed round letter's +26.

### 4.3 c (I, Z): narrow and heavy [measured]

- **In words:** +21.3% in I (9 of 9) and +10.3% in Z (7 of 9).
- **Ink width:** 285 units, 0.58 of its own n (references 0.64–0.76). Its
  advance is 0.68 of the n (references 0.71–0.89).
- **What owns what:**
  - The top is his. F2 (round 433) set the top-heavy, light-bottom balance,
    and the drawn top is E1 (round 436).
  - In round 434 the 700's D3 kept its old width by his pick.
  - The 400's width (`ALBO_ALD_C_W` 0.675 xh) was never a question put to
    him. That is the lever.

### 4.4 g (R, B): its spacing, not its shape [measured]

Pair gaps, over the face's median gap:

| | ge | go | gh | gs |
|---|---|---|---|---|
| Albo R | 0.63 | 0.67 | 0.74 | 0.82 |
| reference median | 1.05 | 1.06 | 1.07 | 1.00 |

- Inside each face:
  - Albo's *ge* is 0.63 against its own *oe* at 0.81: 22% tighter.
  - Every reference's *ge* (0.97–1.08) is looser than its own *oe*
    (0.73–0.89), by 11% (Albertus) to 47% (Palatino).
- At reading size the ear reaches the next letter [visual, x3-16 probe].
- Its in-word darkness partly follows from the narrow slot [inferred]. It is
  +10.7% in R (5 of 9 sizes outside every reference, so under the call rule)
  and +10.0% in B (9 of 9).
- **Why it is untouched:**
  - The g is excluded from B2. All its bench rows were judged on the old g,
    and the owner dropped them (2026-09-21).
  - Its bearings were measured once, against the o, in rounds 335 and 340.
- **Direction:** a handful of bench rows (*ge go gh gs gi ga*). Its shape is
  ruled.

### 4.5 f (R, B, I): the white after the f [measured]

| | R | I |
|---|---|---|
| In words | −13.4% (8 of 9) | −6.7% (9 of 9) |
| Advance, units | 359 (references 253–319) | 374 (references 240–286) |
| Bar ends, units inside the advance | 61 (every reference within 17) | 129 (references 44–105) |
| Hook, units past the advance | 30 (references 6–98, median 58) | −73: stops short (references −19 to +18) |

- **Pairs after the f (R):** *fo* +16%, *fe* +14%, *fr* +13%, *ft* +9%.
- **But *of* itself is 15% tight:** the o sits close and the white falls after
  the f.
- *of*, *for* and *from* are three of his 18 commonest words, and all three
  are less even than in every reference. *of* reads 0.110 against the
  references' 0.030.
- The Bold f is −10.9%.

**Direction** [inferred]:
- Extend the bar to the advance, let the hook overhang as the references' do,
  and then refit the f's right side.
- Round 430 already gave the lone f's bar +16 (`ALBO_ROM_F_BAR_R`), and the
  gap is still 61.
- `BEARING_ADJ` f +25 on the right predates B2. Re-measure whether it is still
  needed.

### 4.6 The Bold's widths (B): stems widen with weight, bowls do not [measured]

Advance, Bold over Regular, each at its own x-height:

| | n h u m t | i l | f | o e s c | k | a | b d p q | g | v w y |
|---|---|---|---|---|---|---|---|---|---|
| **Albo** | **1.12–1.13** | **1.18** | 1.13 | 1.04–1.06 | 1.06 | **1.02** | **1.00** | **1.00** | **0.96** |
| reference median | 1.04–1.06 | 1.08–1.09 | 1.09 | 1.01–1.06 | 1.09 | 1.07 | 1.04–1.09 | 1.01 | 1.02–1.03 |

- **In bold words, light:** n −5.0%, i −9.8%, l −8.7%, u −6.7%, h −4.9%.
- **In bold words, dark:** a +6.4%, o +6.0%, s +5.4%, g +10.0%, w +10.1%.
  Their advance relative to the n is 0.76 / 0.88 / 0.67 / 0.80 / 1.15
  (references 0.82–0.90 / 0.90–0.95 / 0.70–0.74 / 0.81–0.91 / 1.25–1.36).
- The Bold also has the face's lowest contrast. Its lowercase thin strokes
  run 0.31–0.82 of the n stem (most 0.45–0.60), against the references'
  0.12–0.45. The bold capitals' contrast is the capitals audit's item 1.
- **Inferred cause:** the stem letters widen because they are built from
  stems, while a ring or a diagonal of fixed span grows inward.
- **Direction:** this is the whole cut, so it goes to the owner as options
  before anything is built (global rule):
  - widen the bowls, a, g, s, o and the diagonals by about 8–12%; or
  - narrow the Bold's stem letters; or
  - accept it, since the Bold is 7% of the text and is mostly headings.

### 4.7 k (R) [measured]

- **In words:** −7.3% (8 of 9).
- **Band ink:** 0.88 of the n (references 0.90–0.94).
- **The top quarter**, the arm's root and serif: 0.555 of the n's slice
  (references 0.59–0.74).
- **Right bearing:** +47, where the references overhang (−5 to −22). Its
  advance is 0.98 of the n (references 0.90–1.00).
- **History:** round 91 found the k light (−14%). Round 92 thickened the arm
  (1.40) and the leg (1.10). Round 93 asked for more weight on the top-right
  serif (wedge 1.35). It is still the light part.

### 4.8 T and *The* (R, B, I) [measured]

- **The T:** ink width 658 units at a 429 x-height (references 481–556);
  advance 1.25 of the n (references 1.01–1.22).
- **In *The*:** 62 units of white between the bar's end and the h's stem
  (references 10–43; Georgia 10, Berkeley 10, Palatino 22, Times 30,
  Charter 31, Albertus 43).
  - That white is the owner's own: *Th* is held in B2 (its holds, rounds
    384–390).
  - The h cannot tuck under the bar the way an o does: *To* kerns −112.
  - So the lever is the T's width, which is the capitals audit's item 4.
- *The* is 8,328 tokens: the commonest capital word by far.
- Also measured in the Regular: cap/xh 1.571 (references 1.40–1.49). Against
  this panel, Albo's capitals stand taller over its lowercase than the
  audit's +1.5% suggests. The audit's panel has Baskerville and Hoefler in
  place of Berkeley and Albertus.

### 4.9 h (I, Z): a squeezed n [measured]

| | ink width / own n | advance / n | in words |
|---|---|---|---|
| Italic h | 0.92 (references 0.97–1.03) | 0.87 (references 0.90–1.00) | +4.3%, 6 of 9 sizes |
| Bold Italic h | | 0.89 (references 0.95–1.00) | +11.7%, 9 of 9 |

- *The*, *She*, *This*, *Three* and *he* are the least even italic words. Part
  of that is the light T [inferred: in a three-letter word, a light T raises
  its neighbors' relative color].

### 4.10 italic v and w; italic e [measured]

- **Italic v and w:** band ink 0.81 / 1.35 of the n (references 0.63–0.82 /
  1.04–1.29); in words +8.4% / +6.6%.
- **Italic e:** section 0, row 10.
  - The e is the commonest italic letter, so its −6.9% reaches 52% of italic
    tokens.
  - *be, de, keep, kept, does, people* are less even than in every
    reference, with the e the departing letter.

### 4.11 Capitals in his words (cited against the open audit)

| letter | in words | in the audit? | what this pass adds |
|---|---|---|---|
| T | −13% R, −16% I | yes, T wide | *The* (section 4.8) |
| I | +11% R; −15% I | yes, I narrow | *It*, *In*, *Is* and *If* are tight after the I: gap 1.01 against 1.18 |
| C, G, O | −19%, −12%, −8% R | yes, light rounds | |
| H | −5% R | yes, H wide | |
| E, W, B | dark in B | yes, bold contrast / widths | |
| **A** | −12% R, −6% I | **no** | **new** |
| **F** | −11% R, −12% I | only narrow in the bolds | **new** |
| **Y** | −20% in Z | | **new**; it reaches 0 of his tokens |

---

## 5. Spacing: measured here, owned by the bench

**None of this is reshaping.** B2 is his bench (`local_ai/b2_fit.py`), and
the bench, not this doc, is where these go. Listed so the next bench session
can force the rows. All are measured.

Pair gaps against the reference median:

| pair | gap | note |
|---|---|---|
| *is* (12,453 tokens) | **+12%** | the s's left |
| *of* | **−15%** | |
| *it* | −12% | the t's left |
| *at* | −13% | the t's left |
| *nt* | −14% | the t's left |
| *ht* | −16% | the t's left |
| *nd* | −7% | the n's right |
| *ne* | −8% | the n's right |
| *no* | −8% | the n's right |
| *ge go gh* | −31 to −40% | section 4.4 |
| *fo fe fr* | +13 to +16% | section 4.5 |
| *ch ca co ce* | +11 to +13% | section 4.2 |
| *es* | +10% | |
| *en* | +7% | |

- **The commonest pairs are in line**, within ±2% of the references:
  *th, he, in, an, on, ou, to*.
- The n's right side is his: B2 n −10, rsb −13 in the round-344 table.
- The t's left side is already +10 in B2 and still reads tight. Its bar's left
  arm sets the closest rows [inferred].

---

## 6. Measured, ruled: listed, not proposed

- **a (R):** +8.7%. Its height, width and top are ruled, and its weight
  (round 93) is old. See row 1. **It is the largest word-image unevenness in
  the face by reach.** It leads the least-even common words in the Regular:
  *and* (Albo 0.076 against the references' 0.024), *that*, *are*, *an*,
  *can*, *each*, *back*.
- **o (R):** +7.5%, his 1.10-heavier pick (round 226). Because a and o are
  dark, the t in *to* and *at* reads light, though the t itself is fine:
  −0.5%, 0 of 9 sizes.
- **Italic b, d, p, q:** +5%, +5%, +9%, +17%. Their band ink is 1.08 / 1.23 /
  1.25 / 1.24 of the n (references 0.89–1.03). This is round 395's
  thick/thin picks, a style direction (fit audit 2e). The q was also ruled
  "as is".
- **Italic and Bold Italic g:** +13% / +14%, approved.
- **Italic S:** −17%; its reach was ruled LEAVE (2026-10-03).
- **Roman g:** shape ruled. Its spacing is in section 4.4.

---

## 7. Checked and found fine (negative results)

These are the color in words: the change against the reference median, and
how many of the 9 sizes fall outside every reference [measured]. None needs
reshaping by this measure.

| cut | letters inside the references' range |
|---|---|
| **R** | e +1.1% (0) · t −0.5% (0) · n −2.1% (2) · s −0.9% (0) · **i −3.4% (2)** · r −2.5% (0) · h −1.1% (2) · l −1.8% (1) · m +0.8% (3) · p −0.3% (1) · y +1.3% (0) · w +2.0% (0) · b −2.5% (3) · v −3.2% (0) · x, j, z (rare, inside) |
| **R capitals** | S +1.8% · W −1.5% · E −4.3% (1) · L −5.2% (0 of 9) · U, Y, B |
| **I** | a +0.3% (0) · t −0.5% (0) · n −1.5% (2) · o +2.4% (0) · i −0.1% (0) · r +0.9% (1) · l −1.5% (5) · u +1.5% (0) · m −0.3% (0) · y (0 of 9; the range is wide) · k +5.8% (4) |
| **B** | e +4.4% (5) · t +0.4% (0) · r −5.4% (2) · c −5.5% (3) · d −3.5% (7) · b −2.8% (0) · p −1.4% (0) · v +3.0% (3) · k −3.4% (7) · m −0.3% (1) |

**Structure checked and found in line** [measured]:
- The roman bowls join their stems at 80–90 units, top and bottom (b d p q),
  inside the references' 38–142.
- The italic n and u mirror each other: 204 / 204.
- The roman a's eye height (round 462's T2) moved its band ink 0.946 → 0.939:
  the a's darkness predates T2.

**Words checked and found fine** (Regular evenness at or better than the
references): *the* (0.017 against 0.034), *is*, *it*, *with*, *this*, *on*,
*no*, *its*, *be*. Inside the range: *in, not, one, you, by, was, what, two,
his, who, did, but, he, will, would*.

**Instrument findings recorded so they are not re-learned** [measured]:
- **`instruments/word_rows.py` sets Albo unkerned.** It kerns with
  `FT_Get_Kerning`, which reads only a legacy `kern` table, and Albo has
  none: it carries GPOS. *To* is 726 units unkerned and 614 kerned. Corrected
  in `albo-method.md` section 3. Round 442's doc had already noticed.
- **Albo's x is not flat-topped.** Its wedge serifs reach 451 units (R) and
  470 (Z) over the 429 line, which its z and u sit on. Setting Albo by its
  measured x renders it 5% small, so `word_measure.measure_xh` reads the
  declared sxHeight first.
- **An italic n's counter is not the second ink run.** In Times and Palatino
  Italic the pen join splits a stem, and the second run is a 3–5 px sliver.
  The widest interior run is the counter.
- **The first, three-size pass called the i.** Nine sizes do not (section 3).

---

## 8. The pictures

All are PNG at native pixels. Reading-size rows are magnified by an integer
factor with NEAREST, and the factor is in each header. They were written to
the session scratchpad `wordimg/` for the main session to publish.

| file | what it shows |
|---|---|
| `top-R.png` | His 30 commonest word images: Albo R and the six references, 10 pt on the X3, 2-bit, 4x NEAREST |
| `top-R-phone.png` | The same words at 10 pt on the phone's 2x tier, 2x NEAREST |
| `top-IBZ.png` | The 20 commonest words in each other cut, set in that cut: I, B, Z, against the references' matching cuts; 10 pt X3, 4x |
| `neglected-R.png` | The 30 most neglected words (section 2's score), Albo R and the references, 10 pt X3, 4x |
| `mechanism-R.png` | Context, drawn large (120 px x-height, unhinted, no resampling). n and u with red ticks where the arch and the bowl leave their stems; c and f with blue advance lines. Albo, Georgia, Charter, Berkeley, Albertus |
| `mechanism-B.png` | The same for the Bold, with Georgia, Charter and Berkeley |
| `letter-u-R.png` | u: *you about out but would number under human*; R against Georgia, Charter, Berkeley; 10 pt X3 4x, then phone 2x |
| `letter-c-R.png` | c: *which can because each back such once since*; against Georgia, Berkeley, Albertus |
| `letter-f-R.png` | f: *of for from first form before after different* |
| `letter-k-R.png` | k: *like kept work takes book back know keep* |
| `letter-T-R.png` | T: *The That Two This Then They Three To* |
| `letter-AI-R.png` | A and I: *A And After As At I It In If I'm* |
| `letter-bold-B.png` | The Bold's widths: *and a in it is the English What answers call* |
| `letter-e-I.png` | italic e: *the times values one page next answer these* |
| `letter-c-I.png` | italic c: *which chain because back country became each once* |
| `letter-h-I.png` | italic h: *the with Chapter right chain that what them* |
| `letter-f-I.png` | italic f: *of from for four first before life after* |
| `letter-vw-I.png` | italic v and w: *values even every over with answer wrong two* |
| `letter-worst-R.png` | The ten least even of his common Regular words: *of can That case fact off far back each call* |
| `letter-worst-I.png` | The ten least even italic words: *The It In She This keep be he people does* |

---

## 9. Reproduce

Everything runs from `tools/wedge_serif` with the measurement venv (numpy,
scipy, freetype-py, uharfbuzz, Pillow, fontTools). `DIR` holds the four
`Albo-*.ttf`; `WORK` is any scratch directory.

```bash
VENV=.../venv/bin/python
$VENV instruments/word_corpus.py --out WORK                  # corpus, attention, neglect -> WORK/corpus.json
$VENV instruments/word_corpus.py --out WORK --show hnu       # every commit subject counted for h, n, u
$VENV instruments/word_measure.py --albo DIR --corpus WORK/corpus.json --out WORK/measure.json   # ~6 s, 25 faces x 9 sizes
$VENV instruments/word_measure.py --report WORK/measure.json           # band / knot / gaps per letter, per cut
$VENV instruments/word_measure.py --report WORK/measure.json --words   # the word-evenness table
$VENV instruments/word_parts.py --albo DIR --letters cfuknheTdbpq      # stem joins, mouths, bar ends, advances
$VENV instruments/word_callouts.py --work WORK --albo DIR              # the ranked table of section 0 + the global context
$VENV instruments/word_proof.py --albo DIR --corpus WORK/corpus.json --out OUT --callouts default   # the PNGs
```

`--callouts default` draws the per-letter figures of section 8 from the
`CALLOUTS` table inside `word_proof.py`. A JSON file of the same shape draws
others: `{id: {cut, letter, words, refs, per}}`.

The fit audit re-run is `fit_audit/run_geom.py --albo r480=DIR --out WORK/geom.json`,
then `fit_audit/score.py --geom WORK/geom.json --legib EMPTY.json --spacing
WORK/spacing.json --tag r480`, with `spacing.py --rev HEAD`.

---

## 10. What this pass did not do

- **It drew nothing.** Glyph drawing is not delegated (rulings of 2026-09-13
  and 2026-09-26). Every "direction" above is a pointer for the main session
  and the owner.
- **Legibility (OCR) was not re-measured.** The `visionocr` binary is absent.
- **Italic and bold set by CSS class are counted as R.** That covers the
  WBN `.deck`, `blockquote` and the like. The Italic's 4.1% and the Bold's
  7.3% are therefore floors [inferred].
- **The word list is ASCII.** The Spanish accented words (*qué, tú, había*)
  are counted in the corpus but not measured.
- **The A's mechanism is not isolated** (section 4.11), and neither is why
  the t's left side reads tight (section 5).
