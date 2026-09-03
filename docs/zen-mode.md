# Zen mode

A **one-finger hold of 0.75 s above the paper** toggles it, either way in or out.
The pad's chrome goes away and what is left is a sheet of paper on black. (The
three-finger tap did this too until the 2026-08-28 gesture re-cut removed every
three-finger gesture; see "The set was re-cut" below. Zen also has its own switch
at the top of the app's Settings.app screen.)

(The hold's history is worth a line: the owner asked for it on 2026-08-27 as
*"holding down one finger longer than three seconds toggles zen and single finger
modes"* — "single finger mode" is his own term for NOT-zen, disambiguated on
2026-08-22, *"remove the color button from single finger (not zen) mode ui"* —
and then replaced the duration split with a POSITION split the same day.)

**The two sections marked SUPERSEDED are a DATED RECORD of shapes that are gone,
not a description of the code.** They name `holdSelect:`, `holdToggle:`,
`release()`, `onToggleDeadline()`, `toggled_` and `g_holdSelfManaged`, and none
of those exists any more; the log lines they quote cannot be emitted. They are
kept because each records a real cost that was paid to learn something. The live
rule is "The gestures", "The bindings are Settings.app rows" and "The hold splits
by POSITION" above them, plus
[ios/GestureBindings.h](../ios/GestureBindings.h).

## The gestures

Every one of these is a native UIKit recognizer
([ios/CrossPointZenRecognizers.mm](../ios/CrossPointZenRecognizers.mm)) except
the one-finger deliberate tap, which is the SDL classifier
([ios/ZenVerbs.h](../ios/ZenVerbs.h)) — owner 2026-08-22, *"let's use apple for
swiping instead"* / *"please use apple for this so everything works as
expected."*

**WHAT EACH ONE DOES IS CONFIGURABLE from Settings.app** since T-025 (owner
2026-08-28) — see the next section for the layered model. The table is the
shipped GLOBAL layer with every zone override blank.

| Gesture | Live in | Default action |
|---|---|---|
| **1-finger hold, 0.75 s, ABOVE the paper** | **zen AND not-zen** | **toggles zen, under the finger** (the one non-blank zone row) |
| 1-finger deliberate tap (≤28 px, ≤400 ms) | zen only | page forward (`BTN_RIGHT`) |
| 1-finger hold, 0.75 s, anywhere else | zen only | Select (`BTN_CONFIRM`) |
| 1-finger swipe left / right | zen only | page forward / back |
| 1-finger swipe up / down | zen only | Nothing (added 2026-08-28, ships inert) |
| 2-finger tap | zen only | Select |
| 2-finger swipe left / right | zen only | `BTN_DOWN` / `BTN_UP` |
| 2-finger swipe down / up | zen only | Select / Back |
| 2-finger hold, 0.75 s | zen only | Nothing (added 2026-08-28, ships inert) |
| pinch / spread (on the lift) | zen only | `BTN_UP` / `BTN_DOWN` |
| rotate clockwise / counter-clockwise (on the lift) | zen only | Nothing (added 2026-08-28, ships inert) |
| shake | **zen AND not-zen** (since 2026-08-29) | font family step |

Two rows are now always-on. The hold above the paper toggles **both ways**, so
it has to fire while zen is off; the shake was made always-on the same way,
2026-08-29 (owner: *"making shake gesture work in single-finger mode"* — his
own term for not-zen, from the 2026-08-27 quote at the top of this doc).
Everything else is enabled only while zen is on
(`CrossPointZenRecognizers_setEnabled`), or gated on the zen flag where the
gesture has no recognizer of its own (the SDL tap, and every hold that did not
land above the paper).

**"Above the paper" is the whole band above the card top, on every device
(ruling 2026-09-02).** On an iPad in portrait that band is ~194 pt, a fifth of
the glass, and the hold toggles zen anywhere in it; the 2026-09-02 audit
(finding 3) offered to cap the tablet's hold zone at the phone's ~68 pt strip
and the owner ruled to leave it. Not a defect; do not re-propose the cap.

**Rotation fires ONCE, on the lift**, exactly as pinch does and for the same
reason: both are continuous recognizers, and a slow rotate reported continuously
would queue a storm of font steps.

**A gesture that ships INERT may never prevent one that ships BOUND.** Five of
the seventeen default to Nothing, and three of them overlap gestures the app
already had — rotation over pinch above all, since a real pinch carries a few
degrees of twist and UIKit's default is that whichever recognizer fires first
stops the others. An inert rotation would therefore have been arbitrated the
gesture and done nothing, silently costing pinches the owner has today. The
recognizer file's delegate grants simultaneity iff either side's DEFAULT is
Nothing (`gesturebind::shipsInert`); between two rows that both ship bound the
answer is NO, which is what UIKit does with no delegate at all, so nothing about
the pre-re-cut arbitration moves. Bind rotation and a twist that also squeezes
will do both things — the cost of having asked for both. **Found by adversarial
review on 2026-08-28**, after the first cut of the re-cut shipped all five inert
recognizers unconditionally.

### Shake fires outside zen, and "previous font" is now assignable (2026-08-29)

**Owner asks: *"making shake gesture work in single-finger mode"* and *"allow
previous font to be an assignable gesture action."***

#### The shake was zen-only in TWO independent places, not one

Tracing from the shake reaching UIKit to the action firing (per this repo's
"repeated report → trace from zero" discipline — though this was a fresh ask,
not a repeat, the same tracing standard applies before touching scope rules):

1. **`gesturebind::firesOutsideZen(Gesture)`**
   (`ios/GestureBindings.h`) answered `true` for exactly `Gesture::HoldAbove`.
   `actionFor()` (the function every dispatch path funnels through, including
   the shake catcher's `liveAction`) reads: `if (!zenOn &&
   !firesOutsideZen(g)) return Action::Nothing;` — so with zen off and
   `firesOutsideZen(Shake)` false, the shake resolved to `Nothing`
   **regardless of what it was bound to**. This was documented as intentional
   in the recognizer file's own comment at the time: *"Zen-only, and the gate
   is the GESTURE's, not this method's."*
2. **`CrossPointZenRecognizers_setEnabled`** (`ios/CrossPointZenRecognizers.mm`)
   only called `[g_shake becomeFirstResponder]` inside `if (on)`; the `else`
   branch called `[g_shake resignFirstResponder]`. Motion events reach the
   FIRST RESPONDER only (`CPXShakeCatcher.canBecomeFirstResponder`; SDL's own
   view controller never claims it — verified in `SDL_uikitviewcontroller.m`).
   So even had gate 1 been open, a shake landing while zen was off had **no
   first responder to deliver the motion event to at all** — this app is
   called on every zen toggle AND at first boot poll
   (`CrossPointIOSShim.cpp:1591`, with whatever `g_zen` seeds to), so an app
   that launches into single-finger mode never gave the catcher first-responder
   status in the first place.

Both gates had to move together — fixing only #1 would have shipped a change
that compiles, passes the header's own truth table, and still does nothing on
a device, because the motion event never reaches the handler. Neither gate is
observable off-device (UIKit motion events are not injectable by
`CROSSPOINT_SIM_INPUT_SCRIPT` or `simctl`), which is exactly why this needed
tracing rather than a single obvious diff.

**The fix**: `firesOutsideZen(Gesture)` now also returns true for
`Gesture::Shake`, and `CrossPointZenRecognizers_setEnabled` calls
`becomeFirstResponder` unconditionally on every invocation rather than only
when `on`. The shake's action still resolves through the SAME
`gesturebind::actionFor` layered rule as every other gesture — this is a scope
change (which gestures are always-on), not a rule change (zen scope is still a
property of the gesture, never of the action bound to it, per the T-025
ruling above).

**No ruling in this file restricted the shake to zen-only** — the table above
recorded the shipped default, not a standing prohibition. The original ask
(2026-08-22, *"change reader font on shake in zen mode"*) named zen because
that was the only mode the gesture set existed in at the time; nothing said it
must never work outside it.

Status: **SHIPPED — UNCONFIRMED on device.** Same reasoning as every other row
in this table: UIKit recognizers and motion events live above SDL, so no
headless script can drive or observe them. Watch for `[zen] shake catcher ...
first responder` at every `CrossPointZenRecognizers_setEnabled` call (should
now log on the very first boot poll, zen or not) and `[zen] shake -> font
family step` on an actual device shake outside zen.

#### "Previous font" is offered, but not wired end to end

`Action::FontFamilyStepBack = 12` was appended to `gesturebind::Action` (after
`Inherit = 11`, never inserted — the append-only rule cares about the integer
being unused, not about declaration order) and to both `kGlobalActions` and
`kZoneActions`, so any gesture can now be pointed at "Previous Reading Font" in
Settings.app. Nothing ships bound to it (checked: `defaultAction(g) !=
FontFamilyStepBack` for every row, pinned in `tests/gesture_bindings_test.cpp`).

**It cannot be fully wired from this repo alone, and that is a finding, not a
shortcut.** Traced (not assumed) via `grep` over both repos:

- The firmware's `EpubReaderActivity::cycleReaderFontFamily(int delta)`
  **already accepts a negative delta** — a held side button uses
  `cycleReaderFontFamily(held.next ? +1 : -1)`
  (`crosspoint-reader/src/activities/reader/EpubReaderActivity.cpp:601`), so
  backward stepping is not a firmware capability gap.
- What carries no direction is the HOST channel the shake already uses:
  `src/FontFamilyStepChannel.h` (this repo) is a bare `std::atomic<bool>` —
  consume-once, no payload — and its one firmware call site
  (`EpubReaderActivity.cpp:412-414`) is hardcoded:
  `if (gpio.consumeFontFamilyStep()) { cycleReaderFontFamily(+1); }`. The
  device-side inline no-op (`crosspoint-reader/lib/hal/HalGPIO.h:276`,
  `bool consumeFontFamilyStep() { return false; }`) likewise carries no
  direction.

Completing the wire needs a firmware-repo change (a directional channel or a
second consume method, plus the `EpubReaderActivity.cpp` call site and the
device's inline no-op) — out of reach this session (`crosspoint-reader` was
explicitly off-limits). Per the standing instruction not to fake a missing
capability with N-1 forward steps, `performGestureAction` in
`ios/CrossPointZenRecognizers.mm` logs a distinct, explicit line
(`"font family step BACK (offered, not wired -- no direction on the
firmware's host channel)"`) and does nothing, rather than either silently
no-op'ing (indistinguishable in the log from an unbound gesture) or stepping
forward N-1 times (would corrupt the family index on any family list whose
length changes, and lies about what the gesture does).

**This is an architectural choice for the owner, not a default to guess at**:
whether the channel becomes a signed delta, a second boolean channel, or a
small enum, and whether a burst of opposite-direction gestures between polls
should collapse (current same-direction bursts already do, by design) are all
firmware-repo decisions nobody asked this session to make.

### The set was re-cut, 2026-08-28

Owner, after the first shipping version configured only the fourteen gestures
that happened to be wired: *"you did a subset of gestures, when I say all
possible do all possible"*. He was then shown the full expressible set and
trimmed it to seventeen: single taps on 1 and 2 fingers, swipes on 1 and 2
fingers in four directions, long presses on 1 and 2 fingers, pinch in and out,
rotation both ways, shake.

**Out, by ruling, with the reasons:**

- **No double or triple taps.** This is the omission with a mechanical
  consequence. A double-tap recognizer makes every SINGLE tap wait ~300 ms for
  it to fail, because until the double-tap window closes a tap cannot know it is
  single — and the single tap is the page turn. With no multi-tap in the set,
  nothing delays it, no recognizer needs `requireGestureRecognizerToFail:`, and
  the recognizer set is static.
- **No 3-, 4- or 5-finger gestures.**
- **No screen-edge pans.** iOS owns the left edge (system back), the bottom (the
  home indicator) and the top (Notification Center). Only the right is reliably
  free, and one edge is not worth a family.

**Two gestures that worked before are gone, and that is the ruling.** The
**3-finger tap** (toggled zen) and the **4-finger tap** (Power) went with the
finger counts; the owner was shown that consequence and chose it. Their
recognizers are REMOVED, not left installed-but-unbound — an installed
recognizer still consumes touches and can still fail a competing gesture. Power
is now pad-only and is nobody's default, though it stays in the offered actions
because it may still be bound. Both keys are asserted ABSENT from `Root.plist`
by `tests/gesture_bindings_test.cpp`, so a re-add has to be deliberate.

**On `BTN_UP` / `BTN_DOWN` in that table:** this fork sets
`longPressButtonBehavior = FONT_SIZE_STEP`
(`../crosspoint-reader/src/CrossPointSettings.h:477`), which makes the side pair
the FONT controls inside a book —
`EpubReaderActivity.cpp:604` steps font SIZE on the release of a side button
that never crossed the hold threshold, and returns before `detectPageTurn` is
ever reached. So a gesture bound to Down makes text bigger in a book and scrolls
a screenful everywhere else; it turns pages only where the reader's long-press
setting is Off. That is what the Settings.app labels say, and it is why they do
not say "page forward".

## The bindings are Settings.app rows, and the model is LAYERED (T-025, 2026-08-28)

Owner: *"make gestures configureable in ios app settings. list all possible
gestures and give a well ordered, logically list of what they can be assigned
to."* Then, correcting a first attempt that had built three parallel zones with a
hardcoded paper:

> *"if above and below the paper is blank, it should pass through to global
> configuration. if they are defined, they take precedence. there is no 'on the
> paper', it's just normal configuration."*

**Five groups, 29 rows, in two layers.** The rule is
[ios/GestureBindings.h](../ios/GestureBindings.h) — pure, clock-free, free of SDL
and UIKit types, truth-tabled in `tests/gesture_bindings_test.cpp` for the usual
reason: every way it can be wrong is silent on a device and none of it can be
driven off-device, because UIKit's recognizers live above SDL where no input
script and no `simctl` can synthesize a touch.

| Group | Layer | Rows | Ships |
|---|---|---|---|
| **Gestures — One Finger** | base | Tap · Swipe Left / Right / Up / Down · Hold | the mapping above |
| **Gestures — Two Fingers** | base | Tap · Swipe Left / Right / Up / Down · Hold · Pinch · Spread · Rotate Clockwise · Rotate Counter-Clockwise | ditto |
| **Gestures — The Device** | base | Shake | font family step |
| **Above the Paper** | override | Tap · Swipe Left / Right / Up / Down · Hold | blank, except Hold |
| **Below the Paper** | override | the same six | blank |

29 rows in one flat list is a scroll with no landmarks, so the global layer is
sub-grouped BY FINGER COUNT — the one partition a hand can feel, and the one
that lets every row inside a group drop its "Two-Finger" prefix and read as a
short verb. Pinch and rotation sit in Two Fingers because that is what they are.

**The gesture half of `Root.plist` is GENERATED** from the header's table by
[tools/gen_gesture_plist.py](../tools/gen_gesture_plist.py) — 29 rows of
`PSMultiValueSpecifier`, each carrying the same ten or eleven annotated action
labels, is not a table to hand-maintain beside one that already states every
value. Only the span between the Zen Mode switch and the Screen group is
touched. `tests/run_all.sh` runs the generator with `--check`, so a header
edited without re-running it fails the suite rather than shipping a stale
screen.

```
action(gesture, landingY):
    if gesture is not single-finger:          return global[gesture]
    zone = zoneFor(landingY)                  # above / below / neither
    if zone has a row and it is not blank:    return zoneBinding[zone][gesture]
    return global[gesture]
```

**THERE IS NO "ON THE PAPER."** It is not a zone with a fixed behavior, it is not
a row, and it is not a key. A landing point between the two boundaries simply has
no override, so the global binding applies — the same as a multi-finger gesture
anywhere, and the same as any gesture whose zone row is blank. The first shape of
this feature hardcoded the paper's behavior as a third case; that was wrong, and
the branch is gone rather than disabled.

**TWO-FINGER GESTURES HAVE NO ZONE OVERRIDE**, by ruling: a two-finger tap is
the same gesture wherever it lands. Neither does the shake, which has no landing
point to judge. The six overridable gestures are the one-finger tap, the four
one-finger swipes and the one-finger hold.

**BLANK AND "NOTHING" ARE DIFFERENT VALUES, and this is the part most likely to
be got wrong.**

| Zone row holds | Means |
|---|---|
| *Use the Gestures setting* (blank, `Inherit`) | fall through to the global binding. **The default for every zone row.** |
| **Nothing** | an EXPLICIT override: do nothing **in this region**, while the gesture keeps working everywhere else. |

The second is a real use, not a theoretical one: the owner has twice reported
gestures firing accidentally, and the margins are where that happens. An
implementation that collapses the two — treating "no action" as "no override" —
compiles, passes a casual read, and silently makes that row do the global thing
instead of nothing at all. `tests/gesture_bindings_test.cpp` fails it.

The global group has no blank. There is nothing above it to inherit from, so its
rows offer the ten actions and that is all; `Inherit` stored against a global row
(a hand-edited plist, a restored backup) falls back to that row's default rather
than escaping into the recognizers, where it would be dispatched as an unknown
action and swallow the gesture.

**What a row can be assigned to** is the firmware's button vocabulary, annotated
in the row label with what each does in a book and elsewhere: Back, Confirm,
Left, Right, Up, Down, Power — plus **Nothing**, plus the host actions that
have no button. Twelve global actions total as of 2026-09-01 (pinned in
`tests/gesture_bindings_test.cpp`), appended in this order and never
re-pointed (a binding persists as the integer, so changing what a number means
would silently change what a saved choice selects):

- **Toggle Zen Mode** and **Next Reading Font** — a gesture already performed
  both before this table existed; without them the shipped defaults could not
  have stated what the app already did.
- **Previous Reading Font** (`FontFamilyStepBack`, appended 2026-08-29) —
  offered so a gesture CAN be pointed at it, but nothing ships bound to it and
  it needed a firmware-repo change to finish wiring; see "'Previous font' is
  offered, but not wired end to end" above for the state as of that date.
- **Open Action Menu** (`OpenActionMenu`, appended 2026-09-01, T-027) — opens
  Manage Files' per-item action menu, today reachable on a device only by held
  Confirm (~1000 ms). Offered, no default binding (the owner picks the
  gesture). Fully wired end to end: `performGestureAction` in
  `ios/CrossPointZenRecognizers.mm` dispatches it to
  `HalGPIO::injectOpenActionMenu()`, and `FileManagerActivity::loop()` in the
  firmware repo polls the matching consume every frame and calls
  `openActionMenu()`, exactly as held Confirm does — see
  `crosspoint-simulator/src/OpenActionMenuChannel.h` for the channel contract.
  **Screen-scoped, unlike every other action in this table**: the channel is
  polled only in that one activity, so a gesture bound to it fires as a
  logged, diagnosable no-op anywhere else (`[zen] ... -> open action menu
  (fires only in Manage Files)`) rather than doing nothing silently.
  `FileManagerActivity::onEnter()` also drains (consumes and discards) any
  request still pending when the screen is entered, so a gesture fired
  minutes earlier on a different screen cannot surface the menu the instant
  Manage Files happens to open.

**The owner's four rulings, implemented exactly:**

- **Any binding may be cleared, the zen ones included.** No guard, no refusal,
  no warning, and **nothing special about the zen actions** — owner 2026-08-28,
  *"zen is toggleable in settings. drop this concern."* Zen has its own switch at
  the top of the same Settings.app screen, so a cleared Toggle Zen Mode binding is
  an ordinary cleared binding and no row is protected on its account. The missing
  guard is a decision; `tests/gesture_bindings_test.cpp` pins it so nobody adds
  one back.
- **Two gestures may share one action.** No conflict detection, no moving, no UI
  refusal. Each gesture resolves independently and nothing knows what the others
  hold.
- **A gesture may be bound to Nothing.**
- **Zen scope is unchanged**, and it is a property of the GESTURE AND ITS ZONE
  rather than of the action bound to it: you configure WHAT a gesture does, never
  WHEN. The one always-on case stays always-on whatever it holds, and binding a
  zen-only gesture to the toggle gets you only OUT of zen. **The subtle half: the
  gate travels with the landing point, not with the binding.** A hold above the
  paper left blank takes its ACTION from the global row — whose own row is not
  always-on — and its GATE from the zone, so it still fires while zen is off.
  Getting that backwards would lose a way into zen for anyone who blanked the
  row, silently.

**`HoldAbove` is the one zone row that does not ship blank**, for the same
reason every other default is what it is. Before T-025 a one-finger hold ABOVE
the paper toggled zen while the same hold anywhere else selected — the
2026-08-27 position split, below — and those are two different actions for one
gesture, so no single global binding can state both. Left blank it would inherit
Confirm and that hold would stop doing what it does now. It is an ordinary row:
point it anywhere, or at Nothing, and nothing objects.

**The defaults reproduce the previous build gesture by gesture, with exactly two
intended exceptions** (the 3- and 4-finger taps, which no longer exist) — the
property that matters most, since there is no way to notice it has broken except
by using the app and feeling that something is wrong. A stored 0 (an unwritten
key, or a registration domain that never loaded because
`Settings.bundle/Root.plist` was unreadable) resolves to the row's default rather
than to Nothing, so the worst a lost store can do is render the app as it shipped
rather than kill every gesture in it.

**A binding persists as an INTEGER**, so the action list APPENDS and never
inserts or re-points — the same discipline the palette presets follow, for the
same reason. `Inherit` is 11 rather than 0 because it arrived after the other
ten.

## The hold splits by POSITION, not duration (2026-08-27, final shape)

Owner: *"change long tap to only swap zen/singlefinger modes if tap held for
.75 sec above paper, if held below top of paper in zen mode, make it a select
after .75 before lift."*

| a 0.75 s one-finger hold landing... | zen off | zen on |
|---|---|---|
| **above the paper** (bezel / safe-area strip) | toggle INTO zen | toggle OUT of zen |
| **anywhere else** | nothing | Select (`BTN_CONFIRM`) |

Both fire at 0.75 s **with the finger still down**. Nothing happens on the lift.

**T-025 (2026-08-28) made this configurable rather than fixed**, and the table
above is what the shipped values still produce: the Above-the-Paper Hold row
carries Toggle Zen Mode, and everything else falls through to the global Hold,
which is Select. It did NOT add a second threshold, and must not.

"Above the paper" is the card's top edge — where black ends and paper begins
(`g_cardTopPx`), not the top of the text. "Below the paper" is past the sheet's
bottom edge (`g_zenRowTopPx`, the old top-rocker line — the same `line` the zen
painter cuts the sheet at, so the boundary the finger is judged against is the
edge the eye sees). Both are published by the layout pass in BOTH modes, which
is what makes the question answerable on a launch where zen has never been
entered.

Before the first layout the card top reads 0, and a 0 answers "everything is on
the paper" — the conservative direction, since a stray toggle is worse than a
missed one. The bottom edge has the same property before the first pass: a
bottom that is not BELOW the top makes `gesturebind::zoneFor` collapse to the
two-zone rule this section describes, so an unmeasured geometry cannot invent a
third zone out of a zero.

**The tablet is NOT that case, and an earlier draft of this paragraph said it
was.** `layoutPadTablet` publishes neither boundary, but `zenPaperBottomPx()`
falls back to the PANEL's bottom edge — the same fallback the zen painter uses —
so an iPad does get a below-the-paper zone from its first present, measured
against the page rather than a rocker row. Nothing follows from it at the shipped
defaults, since every Below row is blank and inherits.

### Why this shape, after two others in one day

1. A **5 s** hold toggled anywhere; a **0.75 s** hold selected in zen. A hold on
   its way to 5 s crosses 0.75 s, so one gesture wanted to fire two things.
2. The select moved to the **lift** so a long hold could suppress it. Correct,
   but it cost the stock iOS long-press feel the owner had asked for on
   2026-08-22 — the action no longer happened under the finger.
3. **Splitting by position removes the collision at its root.** The two actions
   can share a threshold because they can never both apply: a touch is either
   above the paper or it is not. So the select goes back to firing while held,
   and the 5 s wait is gone as well.

### What that deleted

- **One recognizer instead of two.** `g_lpHold`, always enabled.
- **The simultaneity delegate.** It existed only because UIKit's
  `-canPreventGestureRecognizer:` defaults to YES, so the shorter press stopped
  the longer one ever recognizing. With one hold recognizer there is no pair to
  exempt.
- **All the lift bookkeeping** — no release action, no elapsed-time arithmetic,
  no boot-tick underflow to fail closed against.

### The one thing carried forward deliberately

The select is gated on `g_zenOn` **in the action**, not by disabling the
recognizer. That is the fix for the defect shipped earlier the same day: the
select used to live on a zen-only recognizer which also owned the shared
tracker's lifecycle, so out of zen the tracker went stale and the toggle died in
one mode. Gating the ACTION rather than the RECOGNIZER makes that class of bug
unavailable.

## SUPERSEDED — the collision on one hold, and how it was ruled (2026-08-27)

**Nothing below this line describes the current code.** The symbols it names are
gone; see the banner at the top of this file.

The three-second hold and the zen long-press select are the **same physical
gesture** with two thresholds. A hold on its way to three seconds crosses 0.75 s,
so in zen one hold wanted to fire two things: a Select and then a toggle.

**Owner ruling, 2026-08-27: the select fires on the LIFT, not while held.**

| Total hold | Fires |
|---|---|
| < 0.75 s | nothing here (that is the deliberate tap's window, ≤400 ms) |
| 0.75 s .. < 3 s | **Select**, on the lift |
| ≥ 3 s | **zen toggle**, at the 3 s mark under the finger; the lift is silent |

Exactly one action per hold, never both. What a reader feels: hold past five
seconds and zen flips under the finger, and letting go does nothing more.

**This reverses a device-feel ruling knowingly.** On 2026-08-22 the select was
put on `.began` precisely because that is the stock iOS long-press feel
(*"please use apple for this so everything works as expected"*). It cannot
survive beside a longer hold on the same finger, and the owner accepted the cost
when it was presented. The superseded note is kept beside its replacement in
`CrossPointZenRecognizers.mm` rather than deleted.

**The 0.75 s threshold did not move.** It was itself set from the device
(2026-08-22: *"long tap select is too fast. make at least 1.5x longer"*). Only
*when* it fires changed.

## SUPERSEDED — the hold was dead in single-finger mode, and why (2026-08-27)

Owner, from the device: *"currently it does not work in single finger mode."*
Reported hours after it shipped in build 147, and correct.

**The mechanism.** `zenhold::Hold` is one tracker shared by both hold
recognizers, but only `holdSelect:` ever drove its lifecycle — and that
recognizer is **zen-only**. Out of zen nothing called `begin()` and nothing
called `release()`, so the tracker kept whatever the last zen hold left in it.
`onToggleDeadline()` answers `None` when either `poisoned_` or `toggled_` is
set, and out of zen neither could ever be cleared. Two ordinary sequences latch
it permanently:

- exit zen with the **3-finger tap** — no finger ever lifts through the select
  recognizer, so `release()` never runs and `toggled_` stays true;
- let any zen hold get a **second finger** on it — `poisoned_` stays true.

From that moment the hold worked in zen and did nothing at all out of it, which
is exactly the shape of the report.

**What makes it interesting** is that the code had already reasoned about this
and stopped one step short. `release()` carries a comment saying an idle tracker
must never carry a previous hold's poison, *because the toggle deadline is asked
on holds this tracker never saw begin*. That is the right analysis. What it
missed is that out of zen `release()` is never reached either, so the cleaning
it describes never runs. The adversarial pass also cleared this specific claim —
its clean-item 2 asserted the toggle still fires out of zen — so two independent
readers accepted a false statement about the one mode neither could exercise.

**The fix.** When zen is off, `holdToggle:` owns the whole lifecycle: `begin()`
on `.began`, `release()` on the lift. `g_holdSelfManaged` latches that ownership
**at `.began` and is not re-read**, because toggling flips `g_zenOn` under the
gesture and the `.ended` that follows must go to whoever took the `.began`. In
zen the branch does nothing and `holdSelect:` keeps the tracker as before.

**What is provable off-device** is the property the fix leans on — that
`begin()` scrubs an inherited poison and an inherited toggle latch — and
`tests/zen_hold_test.cpp` pins both, verified by mutation: deleting either
scrub from `begin()` fails exactly one named check. The recognizer wiring itself
is UIKit and reaches no host test, so the fix is device-confirm only. Watch for
`[zen] hold-toggle fired (tracker self-managed, zen off)`.

## Where the hold is live: everywhere, pad included (2026-08-27)

The hold is not hit-tested. It fires wherever the finger lands — the page, the
surround, and the **button pad**.

Out of zen the pad carries holds of its own: hold-to-sleep on POWER, page-turn
autorepeat on the rocker. So a pad hold that lands above the paper and runs past
0.75 s does its pad job *and* toggles zen. (The threshold was three seconds when
this was ruled; the ruling is about the absence of a gate, and it survived the
retune and the position split unchanged.) This was put to the owner as a choice — a page-only
gate, hit-testing the landing point against the already-published `g_zenPanel` /
`g_zenPaper` rects, would have left both pad holds exactly as they were. He was
asked, and asked again on the same day, and chose the ungated rule both times.

So the overlap is **ruled, not overlooked**, and it should not be re-filed as a
defect. The ask was *"holding down one finger"* with no location named, and the
recognizer is live with no location — what the landing point decides is WHICH
BINDING answers, not whether the gesture exists. Should a pad hold ever need
protecting, the whole fix is one hit-test in `ios/GestureBindings.h`; nothing
else moves, because the rule already takes the landing point. (Since T-025 there
is also a milder answer that needs no code: set the Above-the-Paper Hold row to
Nothing — the explicit override, not blank, which would inherit the global Hold
instead.)

**Cancelled and multi-finger holds fire neither.** A touch iOS takes for its own
gesture, or a second finger landing mid-hold, poisons the whole hold — the same
discipline `ZenVerbs.h` applies to a hand rolling across the glass.

The rule is pure and lives in
[ios/ZenHoldRouting.h](../ios/ZenHoldRouting.h), truth-tabled in
`tests/zen_hold_test.cpp` (in `run_all.sh`). It is a header rather than an `if`
in the recognizer action because **both inversions are silent**: a select that
stops firing reads as a gesture the phone did not deliver, and a select that
fires alongside the toggle reads as the toggle misfiring. Same precedent as
`src/TextEntryKeyRouting.h`, which exists because both inversions of the
Return-key rule shipped as bugs.

**There is NO simultaneity delegate, and its absence is the point.** Two hold
recognizers of the same touch count used to need one:
`UIGestureRecognizer`'s default `-canPreventGestureRecognizer:` is `YES`, so the
0.75 s recognizer reaching `.began` would have prevented the longer one from ever
recognizing — in zen the toggle would simply have been dead, silently. Splitting
the rule by POSITION instead of by DURATION removed the pair. The two long
presses that exist now (one finger and two, since 2026-08-28) differ in TOUCH
COUNT, which makes them mutually exclusive by construction.

**Movement allowance is Apple's default (10 pt)**, and that is the first thing to
suspect if a device report says the hold does not fire: `allowableMovement`
applies only *until* a long press is recognized, so a finger that drifts past
10 pt inside the 0.75 s fails the recognizer. It was left at the default because
10 pt on the phone's display scale is 30 device px, which is the 28 px slop
`ZenVerbs.h` already calls a deliberate touch — the repo's own answer to the same
question — and because inventing a number here would be inventing device feel.

### Status: SHIPPED — UNCONFIRMED on device

UIKit recognizers live above SDL, so no `CROSSPOINT_SIM_INPUT_SCRIPT` run and no
`simctl` can drive them. What is proven off-device is the routing (the truth
table) and that the wiring compiles and attaches. **What to watch in the log:**

```
[zen] recognizers attached: 13 objects for 29 configurable rows (17 gestures, 12
      zone overrides); hold 0.75 s; * = fires outside zen; the 1-finger tap stays
      on the SDL classifier [swipe left, ..., hold*, 2-finger tap, ..., pinch,
      rotate clockwise]
[zen] hold at y=118 px (paper 204..852) above the paper, zen off -> toggle zen
[zen] toggle -> on (hold above the paper)     <- the way IN worked
[zen] hold at y=560 px (paper 204..852) in no override zone, zen on -> confirm
[zen] hold in no override zone -> confirm (button 1)   <- a hold on the page selects
```

A hold that produces **no** `[zen]` line at all means the recognizer never
recognized — drift past `allowableMovement` is the leading suspect. A `[zen]
toggle` line and a `-> confirm` line for the SAME hold would mean the routing
broke, which is what the truth table exists to prevent. The attach line is built
from the installed array rather than written out by hand, so it cannot describe a
set the code does not have.

## The layout, and why each edge is where it is

Measured on an iPhone Air (1260x2736, 8 pt grid = 24 device px), home screen,
`CROSSPOINT_SIM_ZEN=1`:

```
paper   y 204 .. 1967      (bottom edge on grid cell 82)
ink     y 288 .. 1827
TOP     ink->paper   84 px = 3.50 cells
BOTTOM  ink->paper  141 px = 5.88 cells
```

**The page is never resized** (owner ruling 2026-08-19, *"do not resize with
zen"*). Zen changes only what is PAINTED around the page: the fit is a
fractional minification of the 3x framebuffer, so re-fitting the panel would
quietly change how every pixel of the text was resampled — measured 0.6212 ->
0.6818 the one time it was tried.

**Below the paper is black** (ruling 2026-08-19). Not decoration: the pad's
field is the same tone as the page's paper by design — measured 215,233,211
against 215,233,211 on an iPhone Air — so without the black there is no visible
edge anywhere on the screen and the sheet has nothing to have corners on. On an
OLED it is also the darkest a night page can be.

**The sheet BLEEDS TO THE GLASS.** It is not a card floating on black. Owner
ruling 2026-08-20, picked off a side-by-side of two live renders rather than a
description: the bounded version spent 204 px of the 1260 on margin and read as
a smaller object sitting on a screen, where the full-bleed one reads as the
screen being paper. The page itself is 1056 px wide either way — the page is
never resized in zen — so this is purely what the 204 px either side is painted
with, and it is paper. Black is for below the line only.

**The paper runs FOUR CELLS PAST the old top-rocker line** (ruling 2026-08-20).
The first version stopped at that line, which left 84 px of paper above the
first ink against 45 px below the last: bottom-heavy the wrong way, and the
sheet read as sliding off the bottom of the screen. The bottom band cannot be
fixed by moving that edge up, because up is where the ink is. Four CELLS rather
than 96 px so the rule holds on any device — the grid is in points, so it is 32
pt everywhere and lands on the grid by construction. Clamped so it never runs
under the home indicator.

## The corners, which took three attempts

The bottom pair has to be rounded or a raised sheet reads as a slab with two
sharp corners under two soft ones. Same curve as the top pair — `kCornerExponent
2.8`, off Apple's display mask — because the two pairs sit on one rectangle and
any difference is visible precisely there.

**Same RADIUS too, 8 pt, `kPaperCornerPt`** (owner ruling 2026-08-20: *"use the
bottom corner radius on the top of the paper too"*). The top pair used to ask
UIKit for the display's own radius — ~55 pt — so the card's corners ran with the
glass. On one rectangle that is a 165 px curve at the top against a 24 px curve
at the bottom, which reads as two different objects rather than as a sheet.
`CrossPointAppearance_displayCornerRadius` stays available; nothing calls it
today.

**Then the radius stopped being a constant** (owner 2026-08-22: *"use the circle
that determines the height gap between paper and text to make the corner radius
of the paper"*). `layoutPad` publishes the visual paper→ink gap as
`g_paperGapPx` and the corner is struck with the same circle: radius = half the
gap. On an iPhone Air that is 105.8 px against the 24 px constant it replaced.
The 8 pt constant survives only as the pre-first-placement fallback, which is
one boot pass — the `[bezel]` line logs which of the two is live.

**And it is not gated on zen** (owner 2026-08-23: *"paper bug: make top corners
of not zen mode match top corner radius of zen mode"*). It was: `paintTopBezel`
read the module only when `g_zen` was set, so the same card was struck with a
106 px curve in zen and a 24 px one out of it. The module is mode-independent by
construction — it is derived from the card top, the panel height and the
firmware's published ink insets, and zen changes none of them (the no-resize
ruling) — so the gate was suppressing a number that was already correct and
already being computed. Measured on an iPhone Air, top-left inset at the card's
first row, before and after:

| | non-zen | zen |
|---|---|---|
| before | 24 px | 106 px |
| after | 106 px | 106 px |

Light and dark alike, and the full 120-row inset profile is identical between
the two modes rather than merely equal at row 0. The panel's fit is untouched:
`[panel] out 1260x2736 px, scale 1.0000, panel 1056x1584 at 102,256` either
side of the change.

**The BOTTOM pair is zen-only, and stays that way.** `paintBottomFillets` is
called from the zen branch alone. Out of zen there is no bottom edge to round:
the pad's field is the paper tone and runs to the bottom of the glass, where the
display's own mask is the only curve. Measured in zen, the bottom pair's profile
is the top pair's, to the pixel.

Verified both pairs on an iPhone Air, insets from each side by row (at the 8 pt
constant, i.e. the fallback the table was measured at):

| row from edge | top pair | bottom pair |
|---|---|---|
| 0 | 24 | 24 |
| 1 | 13 | 13 |
| 2 | 10 | 10 |
| 3 | 8 | 8 |
| 4 | 7 | 7 |
| 5 | 6 | 6 |

Two ways to get this wrong, both shipped and both caught in a screenshot:

* **Cutting them out of the page's rect.** The page is 1056 px wide on a 1260 px
  screen. Because field and paper are the same tone, what the eye reads as one
  sheet runs edge to edge — so cutting at the page's edges put two 24 px notches
  at x=102 and x=1158, mid-field, eight pixels of nothing in the middle of the
  paper. **The corners that exist are the SCREEN's.**
* **Cutting them at the panel's bottom while the paper CONTRACTS.** With the
  line above the page's own bottom edge, the fillets landed inside the black
  band where nothing could see them, and what read as the paper's edge was the
  band's straight top. `g_zenPaper.h` must follow the line in BOTH directions,
  not just when paper is added.

Both are a superellipse, symmetric to the pixel on both sides.

## Two owner bug reports, both fixed 2026-08-29: the toggle flickers, and Settings.app goes stale

Owner, verbatim: *"less flickering of layout when zen mode is enabled/disabled"*
and *"keep zen mode ios app setting reflective of active value."* Both taken
at face value and traced from the present pipeline and `CrossPointPrefs.mm`
respectively, not re-derived from guesswork.

### The flicker: layoutPad computed the fix a present too late, twice over

**Mechanism 1 — the shift consumer ran before the shift was fresh.**
`layoutPad`'s phone path (`ios/CrossPointIOSShim.cpp`) used to read
`g_zenPanelShiftPx` into `g_zenShiftThisPass` (which `setBottomInset` and the
top-inset addition both consume) BEFORE the `want` block below it had a
chance to recompute that same variable for THIS pass. `want`'s own
computation is deliberately independent of the band/shift it feeds (its
comment: *"computed absolutely... reading it would feed the loop its own
output"*), so nothing stopped moving the consumer to run AFTER `want`
updates `g_zenPanelShiftPx` — which is the whole fix for this half: the shift
trio (`g_zenShiftThisPass`, `shiftPt`, `setBottomInset`) now sits right
before the closing `[zen] %s band=...` log line, after the `want` block, not
before it. This alone makes ONE call to `layoutPad` self-consistent: the
band and top inset it publishes always match the shift it just computed, in
the SAME call.

**Mechanism 2 — the self-consistent call still ran too late to help the
CURRENT present.** `layoutPad` runs from `paintPad`, which is
`HalDisplay::presentIfNeeded`'s overlay draw callback — and that present has
ALREADY fit the panel (`SimulatorOverlay::panelBottomPx/panelHeightPx`) from
whatever `bottomInset`/`topInset` were published on the PREVIOUS call, before
the draw callback ever runs. So even a perfectly self-consistent `layoutPad`
call publishes its corrected geometry one present too late for the present
it runs inside — that present's CHROME (rows, bezel, keyboard chip) is drawn
from the just-computed zen-target numbers while the PANEL (the actual page
image) is still sitting at the fit from before the toggle: a visibly
mismatched frame, corrected a moment later by the present the call just
requested. That mismatch, not the two-pass shift math by itself, is the
flicker — "a two-pass convergence that PRESENTS between the passes is a
flicker by construction."

**The fix**: `zenPreWarmLayout()` (`ios/CrossPointIOSShim.cpp`, defined next
to `windowPixelSize`, forward-declared at the top of the anonymous
namespace) calls `layoutPad(outW, outH)` SYNCHRONOUSLY from the three sites
that change zen state, BEFORE they call `SimulatorOverlay::requestPresent()`:
the toggle handler (`CrossPointZen_toggleFromRecognizer`), `pollZenMode()`'s
`ApplyToLive` branch (Settings.app changed the row), and `pollReaderInsets()`
(the ink-inset refinement shortly after the first real page renders). Calling
`layoutPad` outside a draw callback is safe — it does no SDL drawing of its
own (no `SDL_Renderer*` parameter at all), only geometry math and state
publishing — so publishing `bottomInset`/`topInset` a step earlier than the
draw callback ever could means the VERY NEXT `presentIfNeeded()` call fits
the panel from numbers that already match what the chrome is about to draw.
Both fixes are needed together: pre-warming alone would just publish the
STALE (mechanism-1) value one call earlier, and reordering alone leaves the
correct value one present late (mechanism 2).

**Evidence.** The currently-booted iPad Pro 13 simulator
(`0E5288ED-A466-4750-9FDC-BEA83FE9531A`) does NOT exercise this code path at
all — `layoutPad`'s phone branch returns immediately into `layoutPadTablet`
for `s_isPad`, which has its own, separate placement math with no
`g_zenPanelShiftPx` in it (grepped: zero matches). A `defaults write
zenModeEnabled` toggle there produced no `[zen] shift` line, confirming the
iPad path is unaffected by (and untested by) this fix, not that the fix does
nothing. Switched to a booted iPhone simulator (`iPhone Air CP`,
`3E367B66-99CC-476D-94D2-C73B4FA49A00`) instead, which exercises the phone
branch and is closer to the shipped app besides.

`log stream --predicate 'process == "CrossPointX3"'` captured only
`CFPrefsSource` chatter on this device -- not a single app `SDL_Log` line in
over 11,000 captured lines across ~15 s, despite the same predicate working
cleanly on the iPad session minutes earlier. `xcrun simctl launch --console
<udid> <bundle-id>` (stdout/stderr captured directly, bypassing the unified
log subsystem) worked immediately and is the more reliable capture method for
this repo's `SDL_Log` output; recorded here since the next investigation
would otherwise re-lose the same half hour.

Boot, fresh install, registered default `zenModeEnabled=1` (Settings.app's
shipped "on by default," 2026-08-22):

```
[zen] seed: pref=1 env=unset -> on
[zen] on  band=194.0pt topRowY=726.0pt paperTo=2328px panelH=0px panelW=0px
[panel] out 1260x2736 px, scale 1.0000, panel 1056x1584 at 102,256, filter nearest
[zen] shift 0.0 -> 115.7px (panelH=1584 slack=540 ink=60.0/35.0 fallback want=115.7)
[zen] on  band=256.3pt topRowY=629.3pt paperTo=2328px panelH=1584px panelW=1056px
[zen] on  band=256.3pt topRowY=667.7pt paperTo=2328px panelH=1584px panelW=1056px
```

The `panelH=0px` line is the very first-ever `layoutPad` call, before the
panel has been fit even once -- inherent bootstrapping (there is nothing to
converge FROM), not something this fix could remove. The line that matters is
the one after `[panel] out...`: `[zen] shift 0.0 -> 115.7px` is immediately
followed, IN THE SAME CALL, by `band=256.3pt` -- mechanism 1's fix working:
the band already reflects the shift that was just computed, not the shift
from a call two lines ago.

Toggling OFF via `defaults write com.natebunnyfield.crosspoint.x3
zenModeEnabled -bool false` (simulating a Settings.app edit) on the already-
running, already-converged app:

```
[zen] off (setting)
[zen] ink insets (fallback): top=60.0px bottom=35.0px
[zen] off band=256.3pt topRowY=667.7pt paperTo=2328px panelH=1584px panelW=1056px
[zen] ink insets (fallback): top=60.0px bottom=35.0px
[zen] off band=256.3pt topRowY=629.3pt paperTo=2328px panelH=1584px panelW=1056px
[zen] panel 1056x1584 at 102,256
```

Two `layoutPad` calls per toggle, as expected: the pre-warm call (before the
present) and the ordinary in-present call (`paintPad`'s own gate still fires
since nothing here sets `g_padLaidOut = true` after pre-warming). `band`
matches exactly across both (256.3pt) -- no shift line at all, because
turning OFF sets `g_zenShiftThisPass` to 0 unconditionally regardless of the
stored `g_zenPanelShiftPx`, so there is nothing to converge. `topRowY`
(`upperY`, the pad row Y) DOES differ between the two calls (667.7 then
629.3) -- checked, not waved away: `upperY` is the one quantity in this
function that legitimately depends on `panelBottomPx()`, the panel's
CURRENT fit, which genuinely does lag the pre-warm call by one present (the
fit for THIS present already ran, using last present's inset, before the
pre-warm call's publish could reach it). The pre-warm call's `upperY` is
therefore stale by construction -- but `paintPad` only draws `g_pad[]`
AFTER calling `layoutPad` from ITS OWN gate, which runs a second time on the
very next present (using the now-fresh `panelBottomPx()` the pre-warm call's
publish produced) and overwrites `g_pad[]` before anything is drawn. Checked
by reading `paintPad`: the stale `upperY` computed by `zenPreWarmLayout()`
is never drawn to the glass. The one narrow, pre-existing-shaped residual
this does NOT close: a real touch landing in the sub-frame window between the
pre-warm call and the in-present redraw could hit-test against the stale pad
rects. Not fixed here -- it is the same shape of risk the original
`want`-block convergence already carried, is bounded to the instant of a zen
toggle (a rare event, not a steady-state hazard), and fixing it would mean
gating input processing on layout convergence, which is a larger change than
either bug report asked for.

Toggling back ON reproduced the pair symmetrically (`[zen] panel 1056x1584 at
102,371` -- 371 - 256 = 115, matching the 115.7px shift to the pixel) and a
screenshot bracketing each toggle shows the unlabelled 7-button `g_pad[]`
grid present when off and absent when on, confirming the render followed the
log. (The "Resume / Select / Up / Down" text-labelled bar visible in every
capture is an always-on accessibility affordance, unrelated to `g_zen` --
confirmed by it appearing identically in both states; it is not the pad this
doc otherwise describes as unlabelled.)

**Status: SHIPPED, verified on an iPhone simulator (device-CONFIRMED for the
Settings.app-driven direction).** The gesture-driven toggle (the hold above
the paper) exercises the identical `zenPreWarmLayout()` call but could not be
independently re-verified this way -- UIKit recognizers live above SDL and
no `simctl` API injects a real touch-and-hold, the same limitation every
other gesture in this file already carries.

### Settings.app never wrote back: `CrossPointPrefs_zenModeEnabled()` had no setter

**Reproduced from the report, not assumed.** Grepped
`CrossPointPrefs_setZenModeEnabled` across the repo before this fix: zero
matches. `CrossPointPrefs_zenModeEnabled()` was READ-ONLY, and the only
writer of the `zenModeEnabled` key was Settings.app itself (a system
process, via the plist). `CrossPointZen_toggleFromRecognizer` (the hold
above the paper) flips `g_zen` directly and always has; nothing told the
store. So a gesture toggle left the row showing the WRONG value from that
moment on, and the next visit to Settings.app could silently revert a
toggle the reader had made minutes earlier -- exactly the report.

**The fix, and why it is not a direct write from the gesture handler.**
`ios/ZenPrefSync.h` is a pure, UIKit-free header (`zensync::decide`, in the
`HostKeyboardState.h`/`GestureBindings.h` tradition, host-tested by
`tests/zen_pref_sync_test.cpp`) answering one question every poll:
given the stored pref, the live `g_zen`, and `synced` -- the value both
sides were last made to agree on -- which one changed, and what should
happen: `None`, `ApplyToLive` (the store moved; make live match), or
`WriteToStore` (live moved; make the store match). `pollZenMode()`
(`ios/CrossPointIOSShim.cpp`, already run every frame) is the ONLY caller,
in both directions. `CrossPointZen_toggleFromRecognizer` writes nothing to
NSUserDefaults itself -- it flips `g_zen` and lets the very next
`pollZenMode()` poll (a frame later, not a present later) notice the
divergence and call the new `CrossPointPrefs_setZenModeEnabled()`
(`ios/CrossPointPrefs.h`/`.mm`).

**Why a shared tracker rather than a direct write.** A direct
`CrossPointPrefs_setZenModeEnabled(g_zen)` call from the toggle handler
would change what `pollZenMode()`'s NEXT poll reads from the store --
indistinguishable, with nothing else to go on, from an external
Settings.app edit, and it would re-run `ApplyToLive` (harmless only because
it would reapply the SAME value, which is luck: `ApplyToLive` already
carries a relayout and a present request, so an echoed write would cost a
wasted `zenPreWarmLayout()` + present on every single gesture toggle). Full
reasoning, including why a boolean `synced` makes the answer total rather
than a guess, is the comment above `zensync::decide` in the header.

**Confirmed no feedback loop, on device**: toggling `zenModeEnabled` via
`defaults write` (above) produced exactly ONE `[zen] off (setting)` /
`[zen] on  (setting)` line per toggle, with nothing further logged before
the next real change -- if `ApplyToLive` and `WriteToStore` were echoing
each other, this would show as a SECOND, spurious "(setting)" or
"(gesture -> settings)" line immediately after the first, or a `[zen]`
line every frame thereafter. Neither appeared.

**What happens if Settings.app is already open when the gesture writes the
store.** NSUserDefaults is the SAME in-memory-then-flushed store either
direction writes to, so a gesture's write is visible to Settings.app on
the SAME schedule an external Settings.app edit is visible to THIS app:
whenever Settings.app's own UI next re-reads it (typically on its next
`viewWillAppear`), not synchronously while it sits in the background. This
is standard `Settings.bundle` behavior for every app on the system, not
something specific to this key, and there is no API for one app to push a
live update into another app's already-drawn UI. Documented at the setter
in `CrossPointPrefs.mm` rather than worked around, because there is nothing
here to work around.

**Verification split, honestly.** The READ direction (Settings.app -> live,
`ApplyToLive`) is device-CONFIRMED above, by construction of the same
`defaults write` experiment used for the flicker fix -- every `[zen] ...
(setting)` line in this section's log excerpts IS that direction firing.
The WRITE direction (a gesture -> the store, `WriteToStore`) is
**SHIPPED -- UNCONFIRMED on device**: no `simctl` API injects the 0.75 s
hold above the paper, the same limitation every other gesture in this file
already carries, so it is verified only by the host truth table in
`tests/zen_pref_sync_test.cpp`. What that table pins, beyond the individual
cases: after a `WriteToStore` is acted on and `synced` updated, the very
next poll -- even with the store now reading what was just written --
answers `None`, not another `ApplyToLive` echoing the write back. Watch for
`[zen] on  (gesture -> settings)` / `[zen] off (gesture -> settings)` on a
real device to close this out; a repeated line on every frame after a
gesture toggle would mean the loop guard failed where the host test could
not see it.

## 2026-08-30: re-reported ("disabled, reenabled jump") -- H1 and H2 both CLEAN on iPad, a THIRD mechanism found and reproduced

Owner, verbatim: *"Be sure not to flash from Zen mode to out of Zen mode for
any reason, period. Right now, switching from dark mode to light mode,
changing pages, things like that are causing, uh, Zen mode, disabled,
reenabled jump."* Taken at face value, tested on the booted iPad Pro 13
simulator (`0E5288ED-A466-4750-9FDC-BEA83FE9531A`, `com.natebunnyfield.crosspoint.x3`,
`build/ios-app/ios/Debug-iphonesimulator/CrossPointX3.app`, zen on in the
store), against the two hypotheses named going in.

**Method.** `xcrun simctl io <udid> recordVideo` bracketing the two named
triggers (`xcrun simctl ui <udid> appearance dark|light`; page turns via
`SIMCTL_CHILD_CROSSPOINT_SIM_INPUT_SCRIPT='...;QTAP:CONFIRM;...;QTAP:RIGHT'`
-- `QTAP` schedules a real firmware button edge through
`HalGPIO::queueButtonTap`, which works even though zen hides the on-screen
pad, because page-forward is a firmware button (`Button::PageForward`, the
RIGHT front button on this firmware) and has nothing to do with the iOS
overlay chrome zen suppresses). Two independent runs, 80 and 279 frames,
extracted with `ffmpeg -vsync 0` and inspected pixel-by-pixel with Pillow
(`xcrun simctl io <udid> screenshot` alone is too coarse -- ~300 ms between
shots -- to catch a sub-frame present). `xcrun simctl spawn <udid> log show
--predicate 'processImagePath CONTAINS "CrossPointX3"'` ran throughout for
the `[zen]` lines.

**H1 (a real `pollZenMode()` toggle) -- CLEAN.** Across both runs (one
appearance-only, one appearance + four page turns), the `[zen]` log shows
exactly ONE line per process launch: `[zen] seed: pref=1 env=unset -> on`.
Zero `[zen] on (setting)` / `[zen] off (setting)` / `[zen] ... (gesture ->
settings)` lines ever appeared, including in the seconds bracketing both
`appearance dark` and `appearance light` calls. `zensync::decide()` was
never asked to reconcile a disagreement during either test -- `g_zen` never
moved.

**H2 (the `layoutPad` shift-guard race, `ios/CrossPointIOSShim.cpp:997`,
fixed for phone in `c25448b`/[S-020]) -- CONFIRMED N/A ON IPAD, not just
untested.** Read, not assumed: `layoutPad` (`ios/CrossPointIOSShim.cpp:646`)
returns after calling `layoutPadTablet` at line 654 (`if (s_isPad) {
layoutPadTablet(W, H, S); return; }`) -- every line after that, including
the `g_zenRowTopPx` assignment (:938) and the entire `g_zen &&
panelHPx > 0 && g_zenRowTopPx > ...` shift block (:997-1037) that [S-020]
patched, is PHONE-ONLY dead code on this device. `layoutPadTablet`
(:428-628) has no `g_zenPanelShiftPx`, no `g_zenRowTopPx` read, no shift
concept at all -- it derives `cardTopPx` once from `(outHpx - panelHpx) /
3` and the panel's own fit, values that do not move on a page turn (the
"zen does not resize the page" ruling holds independent of ink insets on
this path). Empirically: across 279 combined frames spanning four page
turns and two appearance toggles, the sampled bottom band (`y=0.90h..0.97h`)
and the outer top margin (`y=0.02h..0.10h`) -- both must be pure black
`(0,0,0)` in zen, and would show non-black the instant the on-screen pad
chrome reappeared -- stayed exactly `(0,0,0)` in every single frame once the
app finished loading. No geometry flash, no pad reappearance, on this
device, for either named trigger.

**A third mechanism, not named in either hypothesis, DOES reproduce --
twice, independently.** `applyTheme()` (`ios/CrossPointIOSShim.cpp:1403`)
calls `SimulatorOverlay::setPanelDark(g_dark)` (:1455) on every appearance
change, which reaches `HalDisplay::setPanelDark` (`src/HalDisplay.cpp:1086`)
and `HalDisplay::setInverted` (:1956), which sets `pendingReconvert` and
returns -- the actual repaint happens later, on the main thread, inside
`presentIfNeeded`. There (:2704-2708) `reconvertLastFrame()` (:965) runs
FIRST, rewriting the cached BW/grayscale planes to the NEW palette and
bumping `pixelBufSeq` exactly as a genuine new firmware render would
(documented in place at :2856-2858: "a polarity reconvert ... is a change
like any other"). A few hundred lines later in the SAME function, the CRT
beam-paint trigger (:2812-2821) reads that same `pixelBufSeq` bump as
`contentChanged` and does `beamStartedAt = SDL_GetTicks()` -- **starting a
fresh beam sweep**, with no exception for a reconvert that changed no page
content at all. The sweep (`beamProgress`, :3250-3261) then composites the
OLD, fully-old-palette composed glass (`glassPrevTexture`, captured before
the flip) under the NEW, fully-new-palette one, revealed top-down over the
sweep duration (55 ms, the app's shipped `CROSSPOINT_SIM_AS_SHIPPED` beam
value) -- so for a handful of frames mid-sweep, the top portion of the
panel renders in the NEW palette while everything below it is still the
OLD palette, in the same frame.

**This is not a description from reasoning -- it was captured.** Frame
33/80 of the first (appearance-only) run and frame 275/279 of the second
(appearance + page-turn) run both show it, at the SAME kind of moment (one
present after `appearance light`), independently:

```
y=390   (229,225,217)   <- cardTop; NEW (light) palette starts here
y=420   (232,226,219)
y=495   (241,235,228)
y=500   ( 22, 25, 26)   <- hard cut, still OLD (dark, 171B1B-ish) below
y=600   ( 20, 25, 26)
```

Frame 275 shows it on real book text, not just background: the first
rendered line of a paragraph ("Three properties of that function will")
sits on a cream ground in dark serif-weight text, struck through by the
antialiasing of what is now a light-mode glyph rendered where a dark-mode
row used to be, and every line below it is light-on-dark -- one visible
text block, two polarities, one frame. The zen sheet's own geometry (card
bounds, corner radius, the black margins above and below) is IDENTICAL in
this frame to the one before and after it -- confirmed by the same
bottom-band/top-margin sampling above reading pure black throughout -- so
this is not H2's geometry collapsing and not H1's `g_zen` moving. It is a
legitimate CRT beam sweep, the one built for page turns, firing over a
pure palette flip that carries no new page content, and it is exactly
the kind of jarring, screen-wide, self-correcting-a-moment-later
discontinuity a reader would describe as "disabled, reenabled" without
meaning `g_zen` literally toggled.

**Not yet fixed.** The natural repair is to stop a reconvert-only
`pixelBufSeq` bump from arming the beam (skip straight to `beamProgress =
1.0` / `beamStartedAt = 0` for that bump), but `presentIfNeeded` is the
file this repo's own docs warn cost "two build races and one report that
arrived truncated" from concurrent edits, and every CRT pass downstream of
the beam (`glassPrevTexture`, the accumulator capture, S-016's saturating
blend) reads `beamStartedAt`/`beamProgress` too -- changing when the sweep
arms needs the same nine-render, byte-identical-md5 discipline the
2026-08-25 refactor used, not a one-line patch under time pressure. Left
as a NEXT-STEP finding rather than shipped: reproduced twice, root-caused
to file:line, not yet patched.

**Page turns, tested separately and found CLEAN of this specific
mechanism**: a genuine page turn also bumps `pixelBufSeq` and also arms the
beam sweep, by the same code path -- but old and new page share the SAME
palette (no appearance change involved), so the sweep composites two
frames of one polarity and does not produce the split-palette flash. Four
`QTAP:RIGHT` page turns in the second recording produced no split-palette
frame and no non-black bottom/top margin sample. The owner's "changing
pages" trigger was not reproduced by a page turn ALONE on this device in
this session; it may require a page turn landing inside an in-flight beam
sweep from something else (untested), or it may describe the same
mechanism above under a different name from having seen it during reading
rather than during a deliberate appearance toggle. Recorded as unreproduced
for this specific trigger, not as ruled out.

## Checking it without a device

`CROSSPOINT_SIM_ZEN=1` forces zen at launch. It exists because the gesture
cannot be injected off-device: `CROSSPOINT_SIM_INPUT_SCRIPT`'s TAP feeds the
FIRMWARE's touch state, not SDL finger events, and `simctl` cannot inject
multi-touch either.

```bash
cmake -B build-simsdk -G Xcode -DCMAKE_SYSTEM_NAME=iOS \
  -DCMAKE_OSX_ARCHITECTURES=arm64 -DCMAKE_OSX_SYSROOT=iphonesimulator \
  -DCROSSPOINT_FIRMWARE_DIR="$HOME/src/crosspoint-reader" \
  -DCROSSPOINT_BUILD_FIRMWARE=ON \
  -DCROSSPOINT_IOS_SEED_FONTS_DIR="$PWD/ios/seedfonts"
xcodebuild -project build-simsdk/crosspoint_simulator.xcodeproj \
  -scheme CrossPointX3 -configuration Release -sdk iphonesimulator \
  -destination 'platform=iOS Simulator,name=iPhone Air (zen)' build
xcrun simctl install "iPhone Air (zen)" build-simsdk/ios/Release-iphonesimulator/CrossPointX3.app
SIMCTL_CHILD_CROSSPOINT_SIM_ZEN=1 xcrun simctl launch "iPhone Air (zen)" com.natebunnyfield.crosspoint.x3
xcrun simctl io "iPhone Air (zen)" screenshot zen.png
```

The `[zen]` log line reports the geometry every layout:
`[zen] on band=256.3pt topRowY=629.3pt paperTo=1968px panelH=1584px panelW=1056px`.

## 2026-08-31: "full height then immediately single-finger mode" — a FOURTH mechanism, and it is a data race, not a timing race

Owner: *"there is a persistent issue after ios app reactivation then font size
change and page turn, where the page updates at full height then immediately
becomes single-finger mode."* Full account, the fix, and the proof:
[BUGS.md `S-034`](../BUGS.md). Short version, because the other three entries
in this file (2026-08-29's flicker, and 2026-08-30's re-report above) are all
*timing* bugs — a present reaching the glass one step ahead of a `layoutPad()`
call that would have corrected it, fixed each time by moving the relayout
earlier. This one is different in kind: `HalGPIO::publishReaderTextInsets`
stored its four fields (top/right/bottom/left) as four independent atomics,
written on the firmware's render task and read on the main thread with
nothing coupling the four stores to the four loads as one unit. A font-size
change or a page turn publishes a genuinely different top/bottom pair than
the page before it, so a reader mid-tear can observe the NEW top paired with
the OLD bottom — a combination `ios/CrossPointIOSShim.cpp`'s zen-shift
arithmetic (`visTotal = slack + inkTopPx + inkBottomPx`, the same block
this file's 2026-08-29 section already describes) turns into a `want` shift
that matches no real page: one wrong-geometry frame, corrected a poll later
once the tear has passed. No amount of pre-warming the *call* to `layoutPad()`
fixes a torn *read* feeding it — the fix is `src/ReaderInsetsChannel.h`,
packing the four fields into one atomic so a load can only ever return a
value that was actually stored, whole.

**Render status: UNCONFIRMED, honestly.** This session drove the owner's exact
recipe (reactivate, font-size step, page turn) headlessly and confirmed via
log timestamps that it produces the intended sequence of real relayouts in
the intended order — but could not obtain a pixel capture of the reported bad
frame itself, because `simctl io recordVideo` wedged into a stuck "Host
recording is already in progress" state this session could not clear without
a simulator reboot, and a screenshot-burst workaround was congested by the
same daemon badly enough that forty consecutive captures came back
byte-identical. The mechanism is proven by code and by a concurrency test
measuring roughly a 50% torn-read rate against the pre-fix shape (BUGS.md has
the numbers); it is not proven by render. Close that on a future session with
a working `recordVideo`, or a device confirmation.

## 2026-09-01: mechanism #8 — the beam sweep can go stale mid-`presentIfNeeded`, not mid-layout

Owner, verbatim: *"bug after shaking for going to zen mode then selecting next
book on home screen does the buggy tall redraw flash still"*, corrected the
same session to *"not opening a book on home, selecting the next one"* — HOME
stays HOME the whole time; the sequence is shake-to-zen-on, then an ordinary
selection move, never a reader.

**The other seven mechanisms in this file are all layout races: a present
reaching the glass carrying a `layoutPad()`/`zenPreWarmLayout()` shift, band,
or inset that had not finished converging.** This one is not — verified by
grep before writing a line of speculation: `pollReaderInsets()`
(`ios/CrossPointIOSShim.cpp:1608`) returns on its first line every time on
Home, so it never even reaches the code the first seven mechanisms are about.
No `[pad]`/`[zen] panel...`/`[bezel]` relayout log follows the reported
trigger in any capture taken this session, and a real zen OFF→ON toggle
leaves the panel rect byte-identical on the tablet path (`layoutPadTablet`,
`ios/CrossPointIOSShim.cpp:429`, reads no reader-insets and no shift
concept at all). The zen/pad layout system is provably not where this one
lives.

**Where it does live: the shared present pipeline, `src/HalDisplay.cpp`'s
`presentIfNeeded`, one layer BELOW where every other mechanism in this file
sits.** The CRT beam-sweep progress (`beamProgress`, computed once from
`SDL_GetTicks() - beamStartedAt` against the shipped 55 ms beam) is sampled
early in the function and then used, unchanged, to build a sweep clip AFTER an
expensive synchronous field rebuild — `simsheet::ensureLetterpressField()`,
240-265 ms on a cache miss, i.e. the FIRST time the letterpress field is
needed this session, which a Home screen that has never shown a page reaches
exactly on its first real content change. By the time the stale
`beamProgress` (measured 7.3%) is drawn with, 305 ms have passed against a
55 ms budget — the clip built from it (`sweep.h * beamProgress`, full OUTPUT
height on the manual/iPad path) lands well above the panel's own top offset,
so the panel and its letterpress pass draw NOTHING, and only the zen top
bezel band (drawn separately, above the panel) falls inside it — the
horizontal cream sliver every repro screenshot shows.

**FIXED, same day.** The premise that held (arm the sweep's clock AFTER the
expensive rebuild rather than before it) worked once the ARM POINT moved
instead of adding a second sample: `beamStartedAt`'s write moved from the
early `contentChanged` block (still decides WHETHER to arm, under the pixel
lock, unchanged) to immediately after `ensureLetterpressField()`'s prewarm and
immediately before `beamProgress` is first computed — one write, one read,
same as before the investigation, just relocated past the rebuild. The
reverted first attempt failed by adding a SECOND read of `SDL_GetTicks()`
after the rebuild while leaving the panel's clip already set from the FIRST
(stale) `beamSweeping=true`, which desynced the clip's set/clear pairing; this
fix has no second read to desync anything with.

Reproduced pre-fix and absent post-fix in the same session, same `simctl io
screenshot` recipe: 6 of 10 pre-fix runs showed the sliver, 0 of 20 post-fix
runs (two batches) did. A `log stream` capture on a clean post-fix run caught
the RIGHT press paying the exact cost this mechanism is about (`panel BUILD
243.21` inside a 290 ms present) and still rendering correctly — the fix works
because of the reorder, not because the rebuild happened not to fire. The
sweep still sweeps: that same present is followed by several fast (0.7-8 ms)
cache-hit continuations before the deferred glass capture fires, i.e. the
55 ms reveal completing over multiple frames as designed, not a sweep quietly
disabled to make the symptom disappear. The settled frame (no beam, and beam
on with `[ACT]`-verified matching navigation) is byte-identical pre/post fix
on the desktop canary, per the 2026-08-25 discipline.

The other half — why the un-swept region rendered black instead of the
previous frame — was found 2026-09-01, and it is a zen mechanism in its own
right: the first present of a session runs the zen painter before the pad is
laid out, `g_zenPanel` is `0x0 at 0,0` and `g_zenRowTopPx` is 0, so the
"everything below the line is black" fill starts at `line = 0` and covers the
whole glass; the glass capture read that frame back, and the real frame one
present later carried the same page seq, so the seq-only capture gate kept the
black one for the first sweep to reveal. The capture is gated on a request
generation now (`src/GlassCapture.h`), so any overlay-driven present — the
first layout, a keyboard, a zen toggle — re-reads the glass. The black first
frame itself was ruled out the next day (owner 2026-09-02): the zen painter
draws nothing while the panel has no geometry, so the first present is paper.

Full account, including the reverted first attempt and the mechanics of the
working fix: [BUGS.md `S-035`](../BUGS.md).

**Status: root-caused, reproduced, and FIXED** (external `simctl io
screenshot` for both the pre-fix reproduction and the post-fix absence, so
neither depends on trusting the app's own capture path). A zen-off control and
a zen-on-no-press control of the identical sequence both rendered correctly
every time pre-fix testing was done, isolating the original trigger to zen
plus a genuine Home content change plus an unbuilt letterpress field — not to
zen or Home alone; the fix addresses the shared present-pipeline mechanism
directly rather than anything zen-specific, since [S-035] proved zen was never
implicated beyond the bezel band happening to be the only thing visible inside
the too-small clip.
