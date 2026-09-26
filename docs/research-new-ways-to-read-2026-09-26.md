# New ways to read — the evidence, what it costs here, and what to stop proposing

2026-09-26. Research only. No code, font or setting was changed to write it.
Surveyed against simulator `feedd4a` and firmware `4fb4cb648` the same day.

Owner, 2026-09-26, rejecting a shortlist of sensory spikes (haptic punctuation,
page-turn sounds, a candle timer, a pixel loupe):

> *"those all stink. i need new ways to read not gimmicks"*

**How sure each claim is.** Every study carries an evidence grade and a
verification tag, because the two are different things:

- **Evidence grade** is what the study IS: **field RCT** (randomized, real
  reading over weeks), **lab RCT** (randomized, one or a few sessions),
  **lab** (within-subjects or eye-tracking, no randomization between people),
  **meta-analysis**, **field data** (uncontrolled, large n), **anecdote**,
  **none**.
- **Verification** is what I did this session: **VERIFIED** (the source's text
  was read or extracted here and the numbers quoted come from it),
  **SECONDARY** (an abstract, a database record or a citing summary; the paper
  itself was not opened), **TITLE ONLY**, **UNREAD** (paywalled or blocked).
  **[repo]** means read in this repo or the firmware repo with the file cited.

Two things this document is not. It is not the 2026-09-24 catalog
(`docs/research-novel-reading-interfaces-2026-09-24.md`), whose 54 items are all
surfaces, sounds, haptics and motion; none of them is re-proposed here and the
owner's rejection covers that framing entirely. And it is not a plan: nothing
below has been rendered, and per the visual gate nothing here can go to a
decision without a real rendering first.

---

## 0. The rejection, and what it rules out

The four rejected spikes were the top of the 2026-09-24 shortlist (F26 felt
punctuation, M16 page-turn sound, F11 candle, M22 loupe). What they share is
that **none changes the text, its order, its pace, or what the reader knows
when he meets it**. They change what the glass feels like. The owner's phrase
draws the line there.

**In scope, then:** changes to how text is laid out (line breaks, measure,
indentation, segmentation), paced (who sets the rate and in what unit),
sequenced (what comes before and after the page), or supported (what the
reader is given at the seams: resuming, footnotes, unfamiliar words), judged
on comprehension, attention, retention, speed or enjoyment of long-form
reading. Novels and nonfiction epubs, on the phone and on the X3 (792×528
logical, two front buttons plus a side rocker, no touch).

**Out of scope, by that ruling:** anything whose mechanism is a sensation
(sound, vibration, tilt, glow), anything that simulates a material, and any
chrome that decorates rather than informs. The standing rules still bind
everything below: the 7:1 contrast floor (`src/ContrastFloor.h`), four gray
levels on the page, no touch on the X3, the frozen page palette, and the
reading-experiments ruling that Phase 2 stays wired to nothing without a new
ruling (`docs/reading-experiments.md` §0).

**What already exists, so nothing here re-proposes it** [repo]:

| Already shipped | Where |
|---|---|
| **Focus Reading** — bold prefix on every body word, Bionic-style | firmware `docs/focus-reading.md`; the split is `ParsedText.cpp:633-697`, `wordIsFocusSuffix` |
| **Speed read (RSVP)** — one word at a time on the page's own pixels | `src/SpeedRead.h`, `docs/speed-read-rsvp-2026-09-25.md` |
| **Read-aloud with word highlight** — the read-while-listen case | `ios/CrossPointReadAloud.mm:123` (`willSpeakRangeOfSpeechString`), rects from `src/ReadAloudChannel.h` |
| **Knuth-Plass on justified blocks**, and the auto-justify threshold now 34 so the default X3 page justifies | `ParsedText.cpp:938`, `lib/Epub/Epub/KnuthPlassBreaker.h`; firmware commit `39520a216` |
| **Footnotes** — collected per page, jump-to-note, jump back | `EpubReaderActivity.h:79` (`currentPageFootnotes`), `EpubReaderFootnotesActivity` |
| **Chapter selection** (a table of contents) | `EpubReaderActivity.cpp:903` |
| **Ruby** — a small line of text over a word, sparse-serialized | `ParsedText.h` `setRubyForWordAt`, `blocks/RubySerialization.h` |
| **A Claude API client on the device**, over Wi-Fi | firmware `src/notes/ClaudeChat.cpp:307` |
| **The reading ledger** (rate, volume, run length, abandonment) | `src/ReadingLog.h`, `docs/reading-experiments.md` |
| **Orientation settings** for the EPUB reader | `CrossPointSettings.h:350` |
| **The zen reading goal and the speedrun timer** | `src/ReadingAllowance.h`, `src/Speedrun.h` |

---

## 1. What the ledger can and cannot measure, before any item is judged

Every "how it would be measured" line below points at
`docs/reading-experiments.md`. Its arithmetic (§6) is the constraint: a
**10% effect is reachable in four to five weeks** of ordinary reading, a 5%
effect in four months, a 3% effect never. Its four outcomes are rate
(chars/min), volume (minutes per day), run length and abandonment. **It
measures none of comprehension, retention or recall**, and most of the
evidence below is about exactly those. So two additions would be needed
before any comprehension claim could be tested on him, and both are cheap,
offline and in the ledger's own idiom:

- **A one-press self-rating at a resume or a chapter end** — "I remembered
  where I was: yes / roughly / no" — written as an `evt` line. It is a
  subjective measure and it is the only one available without a test.
- **The free-recall prompt's own timing** (item C3) — whether he answered,
  and how long the page was held before the first turn — which is a
  behavioral proxy for how much reconstruction the resume cost. Cane et al.
  (2012) measured the same thing with an eye tracker.

Neither is built. Both are `evt` kinds the report would ignore until told
otherwise, which is how the ledger was designed to grow (§4, "unknown keys
must be tolerated").

---

## 2. The catalog

Each item: what changes for the reader; the evidence, graded; what it costs
to build HERE, with the hook; how it would be measured; and a blunt line on
gimmick risk.

### C1. Sense-lined text (visual-syntactic / cascade formatting)

**What changes.** Instead of a filled measure, each sentence is broken into
short lines at phrase boundaries, and subordinate phrases are indented under
what they modify, so the shape of the line carries the shape of the clause.
Live Ink (Walker Reading Technologies) and Cascade Reading are the two
products; the research names are VSTF and LDTF.

**Evidence.**

- **Field RCT.** Tate et al. 2019, *Scientific Studies of Reading*
  (SECONDARY, ERIC EJ1220260): 7th–8th graders, within-teacher randomized,
  44 minutes a week for a year. State ELA scaled score **ES = 0.05
  (p < .05)**, writing **ES = 0.07 (p < .01)**. Real, small, and in children.
- **Lab, eye-tracking.** Dempsey, Christianson & Van Dyke, *Reading and
  Writing* 39:2525–2561 (2026) (VERIFIED, the Cascade-hosted PDF was
  extracted and Tables 3–4 read): 74 adult native-English university readers
  after exclusions, two groups of 37, three sessions. Comprehension
  **+2.69% for the cascade group** (model estimate .31, 89% CrI [.02, .60]);
  passage accuracy .82/.70 cascade against .77/.67 traditional across
  sessions. Less rereading and more skipping; **no effect on first-pass
  measures** (first fixation, gaze duration, go-past), which the authors say
  themselves. Texts were read one sentence at a time, which is not a page.
- **Lab, within-subjects.** Ozaki & Ueda 2020, *JALT CALL Journal*
  16(3):147–166 (VERIFIED, the ERIC PDF was extracted): 132 Japanese
  students reading English. Low-proficiency high-schoolers gained on speed,
  comprehension and retention; high-proficiency gained speed and retention
  but not comprehension; middle-schoolers showed no significant difference.
- **Lab.** Jandreau & Bever 1992, *J. Applied Psychology* 77:143–146
  (SECONDARY), and Bever's own chapter (VERIFIED, the Arizona PDF was
  extracted): phrase-spaced formats improved comprehension and speed by
  "roughly 15% each, even more for poor readers", and **the benefit held for
  college readers with verbal SAT under 550 and not above it**.
- **Vendor.** Walker et al. 2005 (SECONDARY): "more than a full standard
  deviation" over a year, from the company that sells it. Discounted.

**Verdict.** The best-evidenced layout change in this document, and the
evidence is consistent: a small comprehension gain, largest for weaker,
younger or second-language readers, and the one adult eye-tracking study puts
it at under 3% on comprehension with no speed gain. Nothing measures a skilled
adult reading a novel for pleasure.

**Cost here.** Firmware, large. The layout owns the break and has the hook —
`ParsedText::extractLine` (`ParsedText.cpp:1559`) already applies a per-line
x-offset, but only the first-line indent (`resolveFirstLineIndent`,
`:776`); a cascade needs a per-line indent AND a segmenter that says where
phrases start. Live Ink uses a full parser. The ESP32-C3 cannot run one; a
punctuation-plus-stoplist heuristic (break before coordinating conjunctions,
prepositions, relative pronouns, after commas) is what would ship, and it is
not what was tested. The phone has Apple's `NLTagger` for parts of speech, no
public constituency parser. **The page count roughly triples**, which on the
X3 is a page turn every two or three sentences. `SECTION_FILE_VERSION` bump
(`Section.cpp:244`, 61 today) and a re-pagination of every book.

**Measurement.** Ledger rate is chars/min, so the page-count inflation does
not bias it (§3 of the ledger doc chose characters for exactly this reason);
volume and run length say whether he keeps reading it. Comprehension needs
§1's additions. A **blind 2AFC of the same paragraph both ways** through the
E4 harness (`crosspoint-reader/tools/knuth_plass_blind.py`) is the cheap
first gate and needs no build on the device.

**Gimmick risk: medium.** It looks like a gimmick, it triples page turns, and
the measured adult gain is small. It earns a render because the evidence is
real, not because it will win.

### C2. Semantic line breaks inside the existing breaker

**What changes.** Nothing visible unless it works: when the rag (or the glue)
leaves a choice, the line ends at a clause boundary rather than mid-phrase.
The measure, the page count and the type are untouched. It is C1's mechanism
without C1's shape.

**Evidence: none directly.** It is an inference from the C1 family — if phrase
boundaries at line ends help, a breaker that prefers them should help a
little — and there is no study of it. Semantic line breaks exist as a
writing convention (one clause per source line), never as a tested reading
format. Grade **none / inferred**.

**Cost here.** Small. The shipped Knuth-Plass port carries a penalty per break
position (`KnuthPlassBreaker.h`, `detail::breakParagraphImpl` at :247), so a
clause-boundary bonus is one term. Two catches: the breaker runs only on
JUSTIFIED blocks (`ParsedText.cpp:938`); a ragged block takes the whole-words
DP, which minimizes squared slack and has no penalty vector, so a ragged
version needs the KP ragged mode from the prototype (`\raggedright` glue,
`knuth-plass-line-breaking-2026-09-25.md` §1a) turned on. And the boundary
detector is the same stoplist heuristic as C1. `SECTION_FILE_VERSION` bump.

**Measurement.** The E4 blind harness first (it exists and renders X3-exact
pairs); a ledger arm only if he prefers it blind. Any rate effect will be
under the ledger's floor.

**Gimmick risk: low**, because it cannot be seen — which is also why it may do
nothing.

### C3. Recall on resume — retrieval practice at the seam

**What changes.** When a book is reopened after a real gap (hours, not a
screen change), the page does not appear first. A one-screen prompt does:
*"Before you read on: what was happening?"* He recalls silently (or types
nothing — there is nothing to grade), presses once, and then sees the last
paragraph he read as the answer key, then the page. At a chapter end the
same prompt can ask for the chapter. No LLM is needed for any of it.

**Evidence.** This is the strongest transfer in the document, and it is a
transfer: nobody has run it on people resuming a novel.

- **Lab RCT.** Roediger & Karpicke 2006, *Psychological Science* 17:249–255
  (VERIFIED, the PDF was extracted): prose passages (TOEFL, ~250 words).
  After 5 minutes restudy beat testing (81% vs 75%); after 2 days testing won
  **68% vs 54%, d = 0.95**; after a week **56% vs 42%, d = 0.83**. Experiment
  2 at one week: STTT 61%, SSST 56%, SSSS 40%. Free recall of prose, no
  feedback, still won.
- **Meta-review.** Dunlosky et al. 2013, *PSPI* 14:4–58 (SECONDARY):
  practice testing and distributed practice are the two HIGH-utility
  techniques; rereading, highlighting and summarization are LOW.
- **Lab RCT.** Szpunar, Khan & Schacter 2013, *PNAS* (SECONDARY): interpolated
  tests during a 21-minute lecture halved mind-wandering and improved
  retention. Lectures, not books; the mechanism (a test coming keeps
  attention on the material) is the one a chapter-end prompt would use.
- **Lab, eye-tracking.** Cane, Cauchard & Weger 2012, *QJEP* 65:1397–1413
  (SECONDARY): interrupted readers spend the resumption re-reading
  pre-interruption text; **a visual cue marking the last word read shortened
  the resumption lag substantially**, and time to consolidate before the
  interruption did not help. This is the "show the last paragraph" half.
- **Caution.** Retrieval is for retention and attention. Whether it improves
  the *enjoyment* of a novel is unmeasured, and a novel is read for that.

**Cost here.** Phone: small. The host already knows the gap (the ledger's
`ts` on the last `page` line; `src/ReadingLog.h`) and already holds the last
displayed page's text (`ReadAloudChannel::peek`, `src/ReadAloudChannel.h:103`,
non-destructive since 2026-09-25), so the prompt and the reveal are an
overlay before the first post-resume present, in the pattern the speed-read
frame uses (`src/SurfaceSpeedRead.h`, drawn from `HalDisplay.cpp:4129`). The
firmware need not know. X3: medium — an interstitial activity on the resume
path (`EpubReaderActivity::onEnter` :106 / `restoreSavedPosition` :2045),
the last page re-rendered for the reveal, and the gap read from
`progress.bin`'s timestamp if it has one (not checked). Both sides: the
prompt must be one press to dismiss and must never fire on a sub-hour gap
or mid-chapter on the X3's frequent sleeps, or it is a nag.

**Measurement.** The ledger sees the resume directly: rate on the first
pages after a gap (a washout-shaped window), run length after a resume, and
abandonment — a reader who cannot remember where he was is a reader who
puts the book down. Plus §1's one-press self-rating. Arms: prompt on / off
by session, in the Phase 2 pattern, which needs a ruling.

**Gimmick risk: low if gated, high if not.** It is a test at the start of a
pleasure activity. It also changes nothing about the page, so it is cheap to
try and cheap to remove.

### C4. Structure first — a chapter skeleton before the chapter (nonfiction only)

**What changes.** Opening a chapter of a nonfiction book shows one page of
its headings (and optionally each section's first sentence) before the
text. One press through. Novels never get it.

**Evidence.**

- **Meta-analysis.** Luiten, Ames & Ackerson 1980, *AERJ* (SECONDARY): 135
  studies of advance organizers, mean **ES ≈ 0.21 immediate, 0.26
  retention**. Small, consistent, classroom material.
- **Lab.** Duggan & Payne 2009, *JEP: Applied* (SECONDARY): under time
  pressure, skimming captured the important ideas better than reading half
  the text — but only when the layout made navigation easy; no advantage over
  reading the first half of every paragraph. Gist, not detail.
- **Against questions, for outlines.** Prequestions help video learning
  (Carpenter & Toftness 2017, SECONDARY) but on **self-paced text** they
  narrowed attention to the pretested material and hurt the rest (Hausman &
  Rhodes 2018, VERIFIED from the UCSC PDF; the Pan & Carpenter 2023 review
  is UNREAD, paywalled). So the skeleton is headings, never quiz questions.
- **Against previews for fiction.** Leavitt & Christenfeld 2011 found
  spoilers improved enjoyment; Johnson & Rosenbaum 2015 and Levine et al.
  2016 found the opposite (all SECONDARY). Contested both ways, which is
  enough to keep it off novels.

**Cost here.** Firmware, medium. The parser already classifies heading blocks
(`BlockStyle.h` carries the CSS the headings resolve through; the exact
heading flag was not traced this session) and the chapter list already
exists (`openChapterSelection`, `EpubReaderActivity.cpp:903`); a skeleton
page is a second walk of the section's blocks at chapter open. Needs a
fiction/nonfiction switch, which the epub does not declare — a per-book
toggle, or a heuristic on heading density.

**Measurement.** Volume and run length by book on/off; the self-rating.
Effects this size will not show in rate.

**Gimmick risk: low.** It is a table of contents shown at the right moment.
The risk is the opposite: that it is too dull to notice.

### C5. A reading ruler on the phone — finger-driven, never dimming

**What changes.** A band or underline marks the current line and moves with a
resting finger (or the rocker on the X3). Nothing above or below is dimmed;
the page keeps its 7:1 everywhere.

**Evidence.**

- **Lab, within-subjects.** Niklaus, Cai, Bylinskii & Wallace, CHI 2023
  "Digital Reading Rulers" (SECONDARY, Adobe/Readability Matters summary;
  the ACM full text was blocked): 91 readers with dyslexia, 86 without; four
  designs (gray bar, lightbox, shade, underline). **All four raised reading
  speed for both groups**, most for dyslexic readers; no single design
  preferred. Magnitudes were not in what I could read.
- **Against overlays.** Colored overlays: no high-quality evidence of benefit
  (Suttle et al. 2018 overview of systematic reviews; the Edinburgh
  double-masked null; both SECONDARY). A ruler is not an overlay, but the
  neighborhood is full of nulls.
- **Against auto-advance.** A ruler that moves itself is a pacer. Rayner et
  al. 2016 (*PSPI* 17:4–34; read in full by this repo for the RSVP doc, and
  this session only via the ScienceDaily release, SECONDARY) finds a
  speed–accuracy trade-off and no technique that beats it; the "a pacer adds
  30–50 wpm" figure that turns up in searches comes from speed-reading
  vendors, not from the review, and I could not find it in any study.

**Cost here.** Phone: small. Line rects are already published per page
(`ReadAloudLines.h`, from the read-aloud capture) and the finger is already
tracked by `padWatch`; the band is an overlay in output space, darken-only
in the margins or an underline under the descenders. X3: needs a mode in
which the rocker steps the ruler instead of the page — that trades the
device's one navigation control, so probably phone-only.

**Measurement.** The ledger's rate, directly — the evidence claims speed, and
speed is what the ledger measures best. If it is under 10% it will not show,
and the CHI result is on short passages.

**Gimmick risk: medium.** M21 in the rejected catalog was a "reading-guide
card" *simulation* with dimming; this is the tool with a lab result and no
dimming, and it must be presented as that or it reads as the same thing.

### C6. The measure — reading at ~55 characters per line

**What changes.** The line gets longer. Today the X3 portrait page at 14 pt
sets **36–38 characters per line** (both faces, `knuth-plass-line-breaking
-2026-09-25.md` §2). Landscape at the same size sets roughly 55–57. The phone
at 2x is narrower still.

**Evidence.**

- **Lab.** Dyson & Haselgrove 2001, *Int. J. Human-Computer Studies*
  (SECONDARY): 55 characters per line gave better comprehension than 100 and
  faster reading than 25; a medium measure held at normal and fast speeds.
  Dyson's 2004 review (SECONDARY) is the survey.
- **Convention.** Bringhurst's 45–75 with 66 ideal, already the basis of the
  auto-justify threshold [repo, `docs/auto-justification.md`].
- **Caveat.** These are screen studies of expository passages; the ledger doc
  already lists measure among the levers "large enough to see" only as a
  hope, not a measurement.

**Cost here: CORRECTED 2026-09-26 -- NOT zero.** The orientation setting
was REMOVED by firmware commit `3b30b5316` (2026-08-01): `GfxRenderer.h:74`
is `static constexpr Orientation orientation = Portrait` and
`CrossPointSettings.h:350` is a comment with no field under it. The renderer
still draws landscape correctly when that constant is changed (a scratch build
rendered 14 lines of ~55 cpl for a 21-line portrait paragraph), so the cost is
restoring a runtime choice, not new layout. The ledger does record `pw`/`ph`
on every `cfg` line, so once restored every page would say which measure it
was.
Landscape on the X3 changes the grip and which way the rocker turns pages;
a stand helps.

**Measurement.** This is **the best-shaped Phase 2 arm the ledger has**: a
large contrast, one setting, chars/min immune to the page-count change,
rate and run length both meaningful. It needs the Phase 2 ruling like every
arm, but the two arms already exist as settings.

**Gimmick risk: low.** It is the oldest question in typography and the device
can already ask it.

### C7. Glosses in ruby — for the one Spanish book

**What changes.** Above a rare or foreign word, a small gloss in the ruby slot
(`setRubyForWordAt`), once per chapter per word, frequency-gated so common
words are never glossed. The corpus has one Spanish epub [repo, KP doc §2],
and that is the only book this is for.

**Evidence.** **Meta-analysis, L2 only.** Glossing has a reliable facilitative
effect on second-language incidental vocabulary learning (a 2026 *Frontiers
in Language Sciences* meta-analysis and Boers' 2022 *Language Teaching*
review, both SECONDARY); the effect varies with gloss type. **For a native
reader of English novels there is no evidence at all**, and Kindle's Word Wise
has none published. So this is an L2 aid or nothing.

**Cost here.** Firmware, medium: the ruby channel and its sparse serialization
exist; what does not is a dictionary on the card (a Spanish–English word list
with frequency ranks, a few MB) and the lookup at parse time. A glossed line
takes ruby's extra height. `SECTION_FILE_VERSION` bump.

**Measurement.** Not the ledger's outcomes — vocabulary. Skip measurement;
judge by whether he keeps reading the Spanish book.

**Gimmick risk: medium**, and irrelevant unless the Spanish book is read.

### C8. Footnotes at the foot — progressive disclosure without leaving the page

**What changes.** A note referenced on this page is shown at the bottom of
this page (or its first line is, with the rest a press away), instead of a
jump to a notes screen and back.

**Evidence.**

- **Review.** DeStefano & LeFevre 2007, *Computers in Human Behavior*
  (SECONDARY): hyperlinks add decision and navigation load; learning is
  better with fewer links per page; effects are larger for readers with lower
  working memory.
- **Lab.** Cane et al. 2012 (above): any interruption costs a resumption
  re-read; a jump to another screen is one.
- **Mixed.** A footnote-vs-hyperlink recall comparison found no difference in
  adolescent ELLs where earlier higher-education samples had favored
  footnotes (SECONDARY, ERIC EJ1176159). Thin.

**Cost here.** Firmware, medium. `currentPageFootnotes` already holds the
page's note hrefs (`EpubReaderActivity.h:79`); what is missing is reserving
page height for the note text at pagination, which touches the paginator.
Notes are a nonfiction feature; novels rarely carry them.

**Measurement.** Abandonment and run length in books with notes. Small
population.

**Gimmick risk: low.** It is what a printed book does.

### C9. Character and thread recap, spaced (the "story so far")

**What changes.** On resume after a long gap, a short recap of the threads
in play; for a series, of the previous book. Kindle shipped both in 2025
(Recaps in April, Story So Far in September, AI-generated, U.S. English
titles only; press coverage SECONDARY).

**Evidence: none.** No study of recaps on comprehension or enjoyment of
fiction was found. Worse, a recap is **re-exposure**, which Dunlosky rates
low-utility against retrieval, and Roediger & Karpicke's restudy arm is the
one that lost at a week. The defensible place for a recap is **as the
feedback after C3's recall attempt**, not instead of it.

**Cost here.** Needs a language model. The firmware has a Claude client over
Wi-Fi (`ClaudeChat.cpp:307`) — a network round trip per resume, with the
book's text leaving the device, which is a privacy change the ledger's own
design refuses (`reading-experiments.md` §8). The phone has Apple's
on-device Foundation Models framework in iOS 26 (about a 3B-parameter model,
iPhone 15 Pro and later; Apple newsroom and developer docs, SECONDARY), which
this app does not use anywhere (grep of `ios/` and `src/` for
`FoundationModels`/`LanguageModel`: nothing). Offline is possible on the phone
only.

**Measurement.** As C3's feedback arm: recall prompt with and without the
recap shown afterward.

**Gimmick risk: high as a feature, low as C3's answer key.** "AI summary of
your book" is the exact shape of thing that stinks.

### C10. Items considered and set aside in one line each

- **Interleaved read + listen.** Already built. The meta-analysis says
  extending it buys nothing (§3).
- **Phrase-chunked RSVP.** Segmentation unit is known to matter in RSVP
  (Thoth, arXiv 1908.01699, abstract only — no results read), but RSVP's
  comprehension cost stands regardless (§3). The built speed read stays as
  the owner asked for it; do not build a second one.
- **"Who is speaking" attribution in dialogue.** No reading study found;
  the NLP side is an LLM problem (arXiv 2408.09452). Evidence none, cost
  high. Dropped.
- **Dual coding.** Novels have no images to code; the epubs with figures
  already show them. Nothing to build.
- **Spaced re-reading nudges.** Distributed practice is high-utility
  (Dunlosky) but "come back in three days" is a notification, not a way to
  read.
- **Self-calibrated print size (MNREAD).** Font size is already the ledger's
  ranked first Phase 2 arm (`reading-experiments.md` §7) and MNREAD's method
  is already in the kerning plan (§1i there); nothing new.
- **Chapter-end summary prompt (write a summary).** Summarization is
  low-utility without training (Dunlosky). Free recall (C3) is the version
  with evidence.

---

## 3. Negative results — so they stop coming back

Recorded with the number that kills each, and the caveat where there is one.

| Idea | What the evidence says | Grade / verification |
|---|---|---|
| **Bionic / Focus Reading (bold word prefixes)** | Readwise 2022, n = 2,074 completing all four halves: **−2.6 wpm with Bionic, under 1%, no effect**. Beelders 2025, *J. Eye Movement Research*, n = 53, Tobii 600 Hz: **131.1 vs 130.8 wpm** (t(52) = 0.13, p = .9), no difference in fixation count or duration, and fixations landed mid-word in both conditions — the bolding did not move the eye. A 2024 *Acta Psychologica* paper titled "No, Bionic Reading does not work" (TITLE ONLY, paywalled). | field data + lab; VERIFIED (Beelders via PMC), SECONDARY (Readwise) |
| | *Consequence here:* the firmware ships Focus Reading (`docs/focus-reading.md`). It should stay for anyone who likes it, but no claim of speed or comprehension belongs beside it, and the ADHD engagement claim in that doc is anecdote. | |
| **RSVP as a way to read** | Benedetto et al. 2015: literal comprehension LOWER with Spritz, blinks sharply reduced. Schotter, Tran & Rayner 2014: blocking regressions hurts comprehension, not only on ambiguous sentences. Comprehension falls above ~350 wpm (a 2018 replication line, SECONDARY). Rayner et al. 2016: eye movements are ~10% of reading time, so removing them cannot buy much. | lab; VERIFIED by this repo in the RSVP doc |
| **Pacers (finger, hand, cursor, moving highlight) and subvocalization suppression** | No controlled evidence of a gain without a comprehension cost; the review's model (speed–accuracy trade-off) predicts none. The "+30–50 wpm from a pacer" figure is vendor copy. | none; SECONDARY (ScienceDaily on Rayner 2016) |
| **Read while listening, self-paced** | Clinton-Lisell 2023 meta-analysis, 30 studies, N = 1,945, 62 effects: overall **g = .18** (SE .07), but **self-paced g = 0.06, 95% CI [−0.07, 0.19], p = .34** — the benefit exists only where the experimenter paced the reading. | meta-analysis; VERIFIED (ERIC PDF extracted) |
| **Scrolling, leading, teleprompter** | Sanchez & Wiley 2009: scrolling reduced comprehension of complex text, most for low working memory. Öquist & Lundin 2007 (mobile eye-tracking): paging read faster than scrolling and RSVP at equal comprehension, with lower workload than leading and RSVP. Kills M6 from the earlier catalog for good. | lab; SECONDARY |
| **Colored overlays / tinted rulers** | Suttle et al. 2018 overview of systematic reviews: no high-quality evidence; double-masked Edinburgh trial: no immediate effect. | meta-review; SECONDARY |
| **Highlighting, rereading, summarizing as aids** | Dunlosky et al. 2013: all three LOW utility. A "highlight as you read" mode is not a reading aid. | meta-review; SECONDARY |
| **Prequestions on self-paced text** | Hausman & Rhodes 2018: pretests narrowed attention to the tested concepts and hurt learning of the rest. Questions before a chapter: no. | lab RCT; VERIFIED (UCSC PDF) |
| **Spoilers / plot previews for fiction** | Leavitt & Christenfeld 2011 (improved enjoyment) against Johnson & Rosenbaum 2015 and Levine et al. 2016 (reduced). Contested; do not preview fiction. | lab; SECONDARY |
| **Letter spacing wider than normal** | Chung 2002: speed peaks at standard spacing (already in `research-claude-for-kerning-and-layout-2026-09-24.md` §1i). | lab; SECONDARY there |
| **Sensory aids** (sound, haptics, glow, tilt, candles, loupes) | Owner, 2026-09-26. Not evidence — a ruling, and the one this document exists under. | ruling |

---

## 4. The shortlist, ranked

Ranked on evidence strength × fit to a skilled adult reading long-form for
pleasure × cost here × what the ledger could actually see.

**1. Recall on resume (C3).** The one idea whose mechanism has RCT-grade
evidence with large effects (d ≈ 0.8–1.2 on prose at a week), whose cost on
the phone is a single overlay fed by channels that already exist, and whose
outcome the ledger measures today (rate after a resume, run length,
abandonment) without a comprehension test. It is also the only item that
changes what the reader *knows* when he meets the page, which is the half of
"a new way to read" the layout items cannot touch. The gate is everything:
gap ≥ 12 h, one press to skip, never on the X3's routine sleeps. Run it as
a session-level on/off arm; the transfer from lab prose to a resumed novel
is exactly the thing unmeasured, and this is the cheapest way to measure it.

**2. The measure at 55 cpl (C6).** NOT zero build (corrected 2026-09-26:
the orientation setting was removed in `3b30b5316`; restoring the runtime
choice is firmware work). Once restored, every logged page says which it was, the
contrast is large, and chars/min is immune to the page-count change. It is
the Phase 2 arm the ledger doc should have ranked and did not, because it
was thinking in fonts. Needs the Phase 2 ruling and a way to hold the X3
sideways.

**3. Sense-lined text (C1), rendered first, built only if he prefers it
blind.** The best-evidenced layout intervention anywhere in the literature —
a field RCT, an adult eye-tracking study, a within-subjects L2 study, and
Bever's 15% — but every effect is small and the strongest ones are in weaker
readers. The right first step costs no firmware: render twenty paragraphs
both ways at X3 pixels through the E4 harness and run the blind page. If he
cannot tell or prefers the block, the item is closed for a few hours of
work; if he prefers the cascade, the firmware cost and the tripled page
count are then worth pricing.

**4. Chapter skeleton for nonfiction (C4).** Advance organizers are a 135-study
meta-analysis at ES 0.2, the mechanism (a frame to attach to) is the one
Duggan & Payne's skimming result supports, and it is buildable on the X3 from
structures the parser already has. Bounded by ruling to nonfiction, which is
at least half of the six-title corpus (three are plainly nonfiction, two are
the WBN novels, the atlas was not checked). Modest, and the least likely to be mistaken for a
gimmick, because it is a table of contents.

**5. A finger-driven reading ruler on the phone (C5).** The CHI 2023 result
(n = 177) is a speed gain for readers with and without dyslexia, and speed
is the ledger's native outcome — the one item on this list the existing
instrument could confirm without additions. Cheap on the phone (line rects
and the finger both exist). It has to be built without dimming and without
auto-advance, or it becomes M21 and a pacer respectively, both of which the
evidence rejects.

**6. Semantic breaks in the breaker (C2).** No evidence of its own, but it is
one penalty term in a breaker that shipped this week, invisible when it does
nothing, and testable on the E4 harness alongside item 3 at no extra owner
time. Worth carrying on item 3's coat-tails and not otherwise.

---

## 5. What was checked and found not to matter, and what was not verified

- **The firmware's own `docs/` was scanned for prior work on any of these**
  (headings list, 90 files): Focus Reading, the breakers, footnotes, ruby,
  the Claude client and orientation are the ones that overlap, and each is
  cited above. No prior work on resume prompts, skeletons, rulers or
  cascades exists in either repo.
- **Rayner et al. 2016 could not be re-opened this session** (the USF
  mirror's certificate does not match, Sage returns 403). Its verdicts above
  come from the ScienceDaily release and from this repo's own VERIFIED
  reading of it in the RSVP doc. The pacer verdict specifically is my
  inference from the review's model, marked as such.
- **Pan & Carpenter 2023** (the prequestioning review) is UNREAD; the
  self-paced-text caveat rests on Hausman & Rhodes 2018 alone.
- **The CHI 2023 ruler magnitudes** were not readable; "significant
  improvement for both groups" is all that was available.
- **The Cascade study reads one sentence at a time** on a screen, not pages;
  its skipping/rereading result may not survive a full page.
- **No item here has been rendered, costed on the ESP32, or shown to him.**
  Every cost is an estimate from the hooks named. Per the visual gate, items
  1, 3 and 5 each need a real rendering before a decision question.
- **Nothing in the owner's corpus was measured for this document.** The
  36–38 cpl figure is the KP doc's, the nonfiction share is a count of six
  titles.

## Sources

Verified this session (text read or extracted):
- Dempsey, Christianson & Van Dyke, *Reading and Writing* 39:2525–2561 (2026): https://cascadereading.com/wp-content/uploads/2025/05/Cascade-Reading-Eye-Tracking-Study.pdf · https://link.springer.com/article/10.1007/s11145-025-10716-x
- Ozaki & Ueda 2020, *JALT CALL Journal* 16(3): https://files.eric.ed.gov/fulltext/EJ1289801.pdf
- Bever, "Learning and Reading" chapter (phrase spacing): https://dingo.sbs.arizona.edu/~tgb/pdfs/beverpdf_33.pdf
- Roediger & Karpicke 2006, *Psychological Science*: https://learninglab.psych.purdue.edu/downloads/2006/2006_Roediger_Karpicke_PsychSci.pdf
- Clinton-Lisell, reading-while-listening meta-analysis: https://files.eric.ed.gov/fulltext/EJ1403866.pdf
- Beelders 2025, *J. Eye Movement Research* (Bionic Reading): https://pmc.ncbi.nlm.nih.gov/articles/PMC12565662/
- Hausman & Rhodes 2018: https://bpb-us-e1.wpmucdn.com/sites.ucsc.edu/dist/4/1518/files/2023/02/Hausman.Rhodes.2018b-When-Pretesting-Fails-to-Enhance-Learning.pdf

Secondary (abstract, database record or summary):
- Tate et al. 2019: https://eric.ed.gov/?id=EJ1220260 · https://escholarship.org/uc/item/4vw2g0m6
- Jandreau & Bever 1992: https://www.academia.edu/9325327/Phrase_spaced_formats_improve_comprehension_in_average_readers
- Walker et al. 2005 (vendor): http://www.liveink.com/VSTF_ReadingOnline_IRA_2005_Walker.pdf
- Readwise Bionic test: https://blog.readwise.io/bionic-reading-results/
- "No, Bionic Reading does not work", *Acta Psychologica* 2024 (title only): https://www.sciencedirect.com/science/article/pii/S0001691824001811
- Rayner et al. 2016: https://doi.org/10.1177/1529100615623267 · ScienceDaily: https://www.sciencedaily.com/releases/2016/01/160114163035.htm
- Benedetto et al. 2015: https://www.sciencedirect.com/science/article/abs/pii/S0747563214007663
- Schotter, Tran & Rayner 2014: https://journals.sagepub.com/doi/10.1177/0956797614531148
- Sanchez & Wiley 2009: https://doi.org/10.1177/0018720809352788
- Öquist & Lundin 2007: https://dl.acm.org/doi/10.1145/1329469.1329493
- Niklaus, Cai, Bylinskii & Wallace, CHI 2023: https://dl.acm.org/doi/10.1145/3544548.3581367 · https://readabilitymatters.org/articles/research-highlight-digital-reading-rulers
- Suttle et al. 2018 (overlays): https://onlinelibrary.wiley.com/doi/10.1111/cxo.12676
- Dyson & Haselgrove 2001: https://www.sciencedirect.com/science/article/abs/pii/S1071581901904586 · Dyson 2004 review: https://stu.westga.edu/~ssynan1/literacy/Dyson.pdf
- Luiten, Ames & Ackerson 1980: https://doi.org/10.2307/1162483
- Duggan & Payne 2009: https://pubmed.ncbi.nlm.nih.gov/19751073/
- Carpenter & Toftness 2017 / Pan & Carpenter 2023 (unread): https://link.springer.com/article/10.1007/s10648-023-09814-5
- Dunlosky et al. 2013: https://journals.sagepub.com/doi/abs/10.1177/1529100612453266
- Szpunar, Khan & Schacter 2013: https://www.pnas.org/doi/10.1073/pnas.1221764110
- Cane, Cauchard & Weger 2012: https://doi.org/10.1080/17470218.2012.656666 · https://pubmed.ncbi.nlm.nih.gov/22540847/
- DeStefano & LeFevre 2007: https://www.semanticscholar.org/paper/200304b3639d5ac8382419099efda8a22b822bd1
- Leavitt & Christenfeld 2011: https://journals.sagepub.com/doi/abs/10.1177/0956797611417007 · Johnson & Rosenbaum 2015 (via): https://www.sciencedirect.com/science/article/abs/pii/S1057740815000467
- Glossing meta-analysis (L2): https://www.frontiersin.org/journals/language-sciences/articles/10.3389/flang.2026.1815571/full
- Thoth (NLP RSVP), abstract only: https://arxiv.org/abs/1908.01699
- Quotation attribution in novels (LLM): https://arxiv.org/pdf/2408.09452
- Kindle Recaps / Story So Far (press): https://www.aboutamazon.com/news/books-and-authors/kindle-recaps-feature-ebook-series-refreshers · https://www.bgr.com/2192985/kindle-cool-new-feature-story-so-far-june/
- Apple Foundation Models framework: https://www.apple.com/newsroom/2025/09/apples-foundation-models-framework-unlocks-new-intelligent-app-experiences/

## Owner rulings, 2026-09-26

- **Cascade (C1): YES**, after seeing the renders. Built **epub side**: claude-tools emits a separate cascaded edition of each generated book, phrases split offline by a real parser; the firmware gets only the markup/spacing fix a cascaded paragraph needs. No reader-side segmenter.
- **Cascade editions ACCEPTED 2026-09-26** ("yes to cascade") after the proof page: firmware `12f1c852d` (cascade-join / cascade-line) ships in TestFlight build 223, and the 28 editions were published in claude-tools `library-latest` (2026-09-26T17:17:01Z, 58 books). Sentence starts stay flush left and verbs are not colored, as built.
