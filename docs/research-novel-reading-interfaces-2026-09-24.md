# Novel reading interfaces: a catalog of mundane and fantastical surfaces, with iOS channels and a shortlist

2026-09-24. This is research only. No code was changed to write it. It was
surveyed against simulator commit `901a6ae`.

The owner's ask, verbatim:

> *"come up with radically new ways to improve the reading experience through
> simulating previously untested interfaces (letterpress and crt are two tried
> ones, let's do fantastical ones and mundane ones), including using video, text
> to speech, audio, haptics in novel and unusual ways"*

**Evidence tags used below:**

- **[repo]**: read in this repo or the firmware repo, with the file named.
- **[src]**: checked this session against the linked source. That is usually
  documentation or a summary page, not a full reading.
- **[inf]**: my inference.

The effect estimates are all **[inf]**. None has been rendered or measured. The
catalog is a menu of proposals. Nothing in it is a finding.

---

## 0. The rules every idea below is held to

These come from this repo's standing rulings. An idea that breaks one is marked
**RULING NEEDED** rather than dropped.

1. **The 7:1 contrast floor is hard** [repo, `src/ContrastFloor.h`, WCAG 1.4.6
   AAA]. Every pass is darken-only or budgeted against it.
   `tests/composition_test.cpp` sweeps all the passes at once [repo]. A new pass
   must join that sweep. Text that is *meant to be read* may never drop below
   7:1, even transiently. The one deliberate exception is the reading goal's
   "spent" page [repo, `docs/reading-allowance.md`].
2. **Bloom and halation cost legibility.** Owner ruling 2026-08-18 [repo,
   CLAUDE.md]. Scanline bloom later shipped under the 2026-08-22
   dark-is-CRT doctrine, and the reading goal uses halation *deliberately* as
   its end signal. So: **any new glow around text needs a ruling.**
3. **The fiction goes around the text, not inside it.** Owner, "Keep 4 levels —
   fidelity is the point" [repo, `surface-roadmap.md` 2026-08-24]. The page
   stays device-exact. Surfaces composite over it.
4. **One sheet of glass.** Output-space effects cover the whole app surface,
   not a rectangle [repo, `whole-glass-crt.md`].
5. **No resampling warps.** A curvature or rotation pass reintroduces the ST-008
   beat on dithered type [repo, `surface-roadmap.md` §7].
6. **Frozen page palette.** The page's colors are frozen [repo,
   `src/FrozenPage.h`, 2026-08-24]. Any idea that moves the ink or paper color
   needs a ruling.
7. **Already decided against** [repo, `surface-roadmap.md` §1e, §1f, §4d, §7]:
   - the gutter shadow and page curl;
   - the page-stack edge;
   - dog-ears, marginalia and tape;
   - teletext and thermal-receipt *modes*;
   - CRT convergence, shadow mask, interlace and the degauss swirl;
   - the room reflection;
   - burn-in as a default.

   **Sound and haptics were NOT rejected.** They were deferred to "a motion
   review", and this document is that review.
8. **What the device can do.** The X3 has:
   - **no speaker** [repo, firmware `lib/hal/HalGPIO.h:254`: "this board has no
     speaker"];
   - no haptic actuator (none in the HAL) [repo];
   - no frontlight (the X4 Pro has one; the X3 does not) [repo, CLAUDE.md];
   - four gray levels;
   - e-ink refresh times of seconds. The X4's panel spec says a full refresh
     takes 3.5 s, a fast one 1.5 s and a partial one 0.42 s [repo,
     `crosspoint-reader/docs/grayscale-fast-refresh-spec-2026-09-14.md`].

   So **every audio, haptic, video and animated idea is phone-only.** Each
   entry says which side it can live on.

---

## 1. What the iPhone gives us: channel notes

### Haptics: Core Haptics

- `CHHapticEngine` plays `CHHapticPattern`s built from events [src,
  [Apple: AHAP files](https://developer.apple.com/documentation/corehaptics/representing-haptic-patterns-in-ahap-files),
  [Kodeco](https://www.kodeco.com/10608020-getting-started-with-core-haptics),
  [exyte](https://exyte.com/blog/creating-haptic-feedback-with-core-haptics)].
- There are two event types:
  - a **transient** is an impulse;
  - a **continuous** event is a sustained vibration, up to 30 s.
- Both take **intensity** and **sharpness** from 0 to 1, and both can follow
  parameter curves. An AHAP file is JSON and can carry synchronized audio.
- **Dynamic parameters** can be changed while a pattern plays. That is the
  mechanism a "paper grain under the finger" needs [inf].
- **State in the repo:** there is no haptic code anywhere today [repo, grep].
  SDL's own haptic subsystem is compiled out of the iOS build [repo,
  `ios-app-size.md:208`]. Haptics would therefore be a new `.mm` backend behind
  a pure header, following the house pattern (`ios/TiltGestures.h`).

### Speech: AVSpeechSynthesizer

- `speechSynthesizer:willSpeakRangeOfSpeechString:utterance:` reports each word
  range as it is spoken [src,
  [Apple](https://developer.apple.com/documentation/avfoundation/avspeechsynthesizerdelegate/1619681-speechsynthesizer),
  [Hacking with Swift](https://www.hackingwithswift.com/example-code/media/how-to-highlight-text-to-speech-words-being-read-using-avspeechsynthesizer)].
- iOS 16 added `AVSpeechUtterance(ssmlRepresentation:)` for prosody, and
  `AVSpeechSynthesisMarker` [src,
  [useyourloaf](https://useyourloaf.com/blog/synthesized-speech-from-text/),
  [mapbox issue](https://github.com/mapbox/mapbox-navigation-ios/issues/4057)].
- **Personal Voice** is usable by apps with permission [src,
  [Ben Dodson](https://bendodson.com/weblog/2024/04/03/using-your-personal-voice-in-an-ios-app/)].
- **A reported risk:** marker sync was lost on iOS 18 [src,
  [dev forum 769342](https://developer.apple.com/forums/thread/769342)].
  Anything timed to words must tolerate drift.
- **Already built** [repo, `ios/CrossPointReadAloud.mm:122`]: read-aloud
  already implements `willSpeakRange` and a highlight. The audio session is
  `Playback` / `SpokenAudio` (`:161`). The firmware publishes per-word rects
  (`ReadAloudChannel.h`, `ReadAloudGeometry.h`).

### Audio: AVAudioEngine and PHASE

- `AVAudioEnvironmentNode` offers HRTF spatialization and reverb presets [src,
  [Apple HRTF](https://developer.apple.com/documentation/avfaudio/avaudio3dmixingrenderingalgorithm/hrtf)].
- **PHASE** is geometry-aware spatial audio with early reflections and late
  reverb presets [src,
  [WWDC21 10079](https://developer.apple.com/videos/play/wwdc2021/10079/)].
- **Constraint:** SDL audio is compiled out [repo], so any audio goes through
  AVFoundation in a `.mm`. It must share the read-aloud's `AVAudioSession`, and
  the category choice decides whether it mixes with the user's music [inf].

### Gaze: ARKit face tracking

- `ARFaceAnchor.lookAtPoint` needs the TrueDepth camera [src,
  [Apple](https://developer.apple.com/documentation/arkit/arfaceanchor/lookatpoint?language=objc)].
- One writeup reports the per-eye gaze estimate is **too inaccurate to target a
  point on the phone's screen**, though it is fine for animating an avatar [src
  via search summary; not measured here].
- iOS's own Eye Tracking accessibility feature is a system feature, not an app
  API [inf].
- **Camera use requires `NSCameraUsageDescription` and a permission prompt.**
- **The repo has a gate that currently asserts the app has NO camera
  reference** [repo, `ios/verify-purpose-strings.sh:50`]. Any gaze idea changes
  that gate deliberately, and it changes the app's privacy story.

### Motion

- CoreMotion is already linked, and the tilt gestures already exist [repo,
  `ios/CMakeLists.txt:614`, `ios/TiltGestures.h`]. A gravity vector is
  available at no new cost.
- **AirPods head tracking** (`CMHeadphoneMotionManager`) exists in iOS 14 and
  later [inf, from memory; not re-checked this session].

### Video

- Frames can be decoded with `AVPlayerItemVideoOutput` and uploaded as an SDL
  texture [inf].
- **Prefer procedural over recorded video** everywhere. A procedural field is
  seedable, so the headless md5 gates keep working. A video is not
  deterministic [inf, from the repo's gate practice].

---

## 2. The catalog

**Format.** Each idea is a block with the following fields:

- **Sim**: what it simulates.
- **Ch**: the channels it uses. **V** is visual, **Vid** video, **TTS** text to
  speech, **A** audio, **H** haptics, **M** motion sensors.
- **Effect/risk**: the expected effect on legibility (L) or enjoyment (E), and
  the risks.
- **Build**: where it hooks into this simulator.
- **Cost**: S is a day or two, M about a week, L more than that.
- **Test**: how to test it.
- **Where**: whether it can exist on the e-ink device or only on the phone.

The test method: visual A/Bs follow `docs/perceptual-test-method.md`, with a
washout, catch trials and never a too-close pair. Audio and haptic ideas are
tested by block design: whole reading sessions with the feature on or off,
recorded in the reading ledger (`docs/reading-experiments.md`) with a one-tap
end-of-session rating. The ledger's power estimate says only effects of 10% or
more on reading rate will ever show. So **most of these are enjoyment features,
and they should be judged by preference and use, not by speed.**

### 2A. MUNDANE (26)

**M1. The library book's worn page.** Pages you have re-read (the ledger knows)
wear softer and grayer at the thumb corner and the lower margin, so the wear is
*your* history, not a fixed stamp.
- Sim: circulation wear.
- Ch: V.
- Effect/risk: E+. It avoids the fetishism list's objection that wear is
  "identical on every page", because the wear follows real re-reads. It never
  reaches the text block.
- Build: a new `paperdefects` class seeded by `readerPageIdentity`, with its
  amplitude driven by the ledger's per-page visit count; it joins the paper
  budget in `FieldSelection.h`.
- Cost: M.
- Test: 2AFC against the off state on re-read pages.
- Where: phone and desktop.

**M2. Carbon copy.** Blue-violet ink whose strokes are soft-edged, pressed
through tissue, with a faint impression from the key strike.
- Sim: a typewriter carbon.
- Ch: V.
- Effect/risk: E+ and L−. The soft edges eat hairlines. It must stay inside ink
  spread's existing limits (`docs/ink-rounding.md`: rounding alone starves
  hairlines by −12%), and the color needs a **RULING** on the palette freeze.
- Build: ink rounding/spread (`src/InkRounding.h`), letterpress deboss, and a
  palette.
- Cost: S.
- Test: 2AFC plus a 7:1 sweep.
- Where: phone and desktop.

**M3. Thermal receipt.** *Rejected already* [repo, `surface-roadmap.md` §4d]:
every property is a legibility deficit, and thermal fade opposes the 7:1 floor.
Recorded so it is not re-proposed. Its one good sub-idea, fading as a *time
signal*, already shipped as the reading goal.
- Where: none.

**M4. Green-bar tractor-feed paper.** Pale bands alternate every three text
lines, with sprocket holes in the margins and a perforation where the section
breaks.
- Sim: 1970s line-printer paper.
- Ch: V.
- Effect/risk: **L+ is plausible.** The bands are a line-tracking aid, a cousin
  of colored reading rulers. The bands darken paper and so spend budget. They
  **must be aligned to real baselines**, or they fight the text.
- Build: baselines come from the read-aloud word rects (`ReadAloudLines.h`)
  and reader insets (`ReaderInsetsChannel.h`). A band field goes in the light
  sheet stack (`SurfaceSheet.cpp`), output-space, with box integration against
  ST-008.
- Cost: M.
- Test: a ledger block on/off, plus a line-skip self-report.
- Where: phone and desktop. The device firmware *could* draw the bands as 1-bit
  dither [inf].

**M5. Microfiche reader.** A projected positive or negative, a lamp hot-spot
vignette, dust on the platen, and slight focus falloff at the corners.
- Sim: an archive reader, a third physics (projection).
- Ch: V, plus A for a fan hum.
- Effect/risk: E+. Focus falloff must be mean-preserving and outside the text
  block (the corner-defocus precedent). It is ranked second third-mode in
  `surface-roadmap.md` §4d [repo].
- Build: vignette (grain Vignette coverage), dust (the defects layer), an
  emissive palette.
- Cost: S–M.
- Test: 2AFC.
- Where: phone and desktop.

**M6. Teleprompter.** Continuous upward scroll at your measured characters per
minute (ledger), with a focus band at eye height.
- Sim: a prompter.
- Ch: V, M.
- Effect/risk: mixed L. Forced pacing removes regressions, which hurt
  comprehension in Schotter, Tran and Rayner 2014 [src,
  [Sage](https://journals.sagepub.com/doi/10.1177/0956797614531148)].
  Mitigation: tilt back to rewind, tilt to pause.
- Build: firmware pages still paginate, so it needs a two-page composite that
  scrolls in the panel texture. That is a new present mode.
- Cost: L.
- Test: comprehension questions per session, not speed.
- Where: phone only. E-ink cannot scroll smoothly.

**M7. Typewriter manuscript.** Per-word strike density from a fixed **table**
(never a jitter, per `docs/albo-imperfections.md` rule 1), and a ribbon that
fades down each page and re-inks at the chapter.
- Sim: a typescript.
- Ch: V, plus A and H for a carriage-return ding and a haptic at each line end
  during TTS.
- Effect/risk: E+. The lightest strike must clear 7:1. No baseline wobble,
  because wobble is a warp.
- Build: word rects from the read-aloud capture feed a darken-only modulation
  field. The ding uses `willSpeakRange` line transitions.
- Cost: M.
- Test: 2AFC plus a 7:1 sweep.
- Where: phone for A/H; the visual works on phone and desktop.

**M8. E-ink paper-white, with a real refresh waveform and ghosting.** A cool,
low-reflectance white; the black-white inversion flash; ghosting that
accumulates through partial refreshes and is cleared every N pages.
- Sim: **the actual device** (GC16 vs DU/A2 behavior [src,
  [Waveshare mode declaration](https://www.waveshare.com/w/upload/c/c4/E-paper-mode-declaration.pdf)]).
- Ch: V.
- Effect/risk: E+ as honesty. It is the top third-mode pick in
  `surface-roadmap.md` §4d [repo]. A ghost is a second image, so it **must be
  held under the floor's budget**. The flash is a flicker, which is a
  photosensitivity concern at one inversion per N pages.
- Build: the trail accumulator with **no decay** until a refresh
  (`glassPrevTexture`), `setPresentFlash`, and `setPanelEmissive(false)`.
- Cost: M.
- Test: 2AFC against a photograph of the X3.
- Where: phone and desktop. The device does this natively.

**M9. Newsprint.** Gray, low-brightness stock, heavy show-through, halftone
rosettes on images, and **ink rub-off**: a faint smudge along the path of your
own swipes.
- Sim: a daily paper.
- Ch: V, H (grit on swipe).
- Effect/risk: E+ and L−. Newsprint's real contrast is under 7:1, so the paper
  tone clamps at the floor, which makes this "newsprint-colored at legal
  contrast". The smudge must stay in the margins, or be ink-spread-budgeted.
- Build: a stock row, `ShowThrough.h`, and a swipe-path accumulator in output
  space.
- Cost: M.
- Test: 2AFC.
- Where: phone.

**M10. Overhead projector.** A bright pool with a warm edge, and the fan's hum.
- Sim: the classroom OHP.
- Ch: V, A.
- Effect/risk: E± (nostalgia). Keystone is a warp, so it is **forbidden**. Heat
  shimmer is motion on text, so it is **forbidden**.
- Build: a vignette plus an audio loop.
- Cost: S.
- Test: preference only.
- Where: phone. Low priority.

**M11. The acid paperback.** Browning that is strongest at the page edges and
weakest in the text block, deepening through the book.
- Sim: pulp aging.
- Ch: V.
- Effect/risk: E+. It darkens paper, so budget is shared with drift.
- Build: an edge-weighted ramp in the sheet field, keyed by spine position.
- Cost: S.
- Test: 2AFC.
- Where: phone and desktop.

**M12. Photocopy of a photocopy.** Toner speckle, and black bands at the page
edges.
- Sim: generation loss.
- Ch: V.
- Effect/risk: E± and L−. Speckle inside the text block is a distractor.
  Rotation is forbidden. Keep it to the margins.
- Build: the defects layer.
- Cost: S.
- Test: preference.
- Where: phone and desktop. Low priority.

**M13. The due-date stamp.** A rubber-stamped date appears in the margin when
you finish a chapter; its ink density reflects the time of day.
- Sim: a library slip.
- Ch: V, H (a thunk).
- Effect/risk: E+ as a progress ritual. It is chrome, not text.
- Build: an overlay in the margin on the chapter boundary, from the ledger's
  `sp` change.
- Cost: S.
- Test: preference.
- Where: phone. The device *could* draw it as firmware UI.

**M14. Silk ribbon bookmark.** A ribbon lies across the lower margin at your
last position. On opening, you feel it lift (haptic) and it slides away.
- Sim: a hardback ribbon.
- Ch: V, H.
- Effect/risk: E+. It must never cross text. Marginalia were rejected as
  content; this is navigation state.
- Build: an overlay, anchored with `panelBottomPx`.
- Cost: S.
- Test: preference.
- Where: phone.

**M15. Reading-room ambience.** A quiet HVAC hum, a distant page turn from
someone else, a far clock.
- Sim: a library reading room.
- Ch: A.
- Effect/risk: E±. Background sound helps some readers and distracts others.
  **Keep it off by default.**
- Build: an AVAudioEngine loop in a new `.mm`, mixed under TTS.
- Cost: S.
- Test: a ledger block, rate plus rating.
- Where: phone only.

**M16. Page-turn sound and feel, from the stock.** The sound and the haptic
follow the frozen paper: thin India crackles, laid paper thumps.
- Sim: a real leaf turning.
- Ch: A, H.
- Effect/risk: E+. It must fire only on a real page commit (the reader-page
  identity change), never on menus.
- Build: `HalGPIO::publishReaderPageIdentity` triggers an AHAP with an audio
  track, chosen per stock.
- Cost: S.
- Test: block on/off with a rating.
- Where: phone only.

**M17. Pencil tick at the stop.** When you leave a book, a small pencil tick
appears in the margin beside the line you were on, and it greets you next time.
- Sim: a reader's mark.
- Ch: V.
- Effect/risk: L+ as re-entry. It is margin-only.
- Build: a word rect from the last capture, stored per book key.
- Cost: S.
- Test: time to resume (ledger).
- Where: phone. The firmware could also do it.

**M18. Chalk on slate.** A dark world that is not CRT: chalk-dust texture and a
slightly gritty stroke edge.
- Sim: a blackboard.
- Ch: V, H (chalk grit on swipe).
- Effect/risk: E±. **RULING NEEDED**: the dark doctrine is "dark is CRT".
- Build: a third-world palette plus a grain variant.
- Cost: M.
- Test: 2AFC.
- Where: phone.

**M19. Split-flap page turn.** The new page arrives as a Solari board: flaps
clatter through, with a tick per flap.
- Sim: a departures board.
- Ch: V, A, H.
- Effect/risk: E+ for novelty, but it costs 300–600 ms per turn. Make it
  transition-only and skippable on any press.
- Build: a transition in `presentIfNeeded` that uses the old and new glass
  captures (`GlassCapture.h`).
- Cost: M.
- Test: preference plus a pages-per-session check.
- Where: phone.

**M20. The bouncing ball.** During read-aloud, a small ball hops word to word,
landing on each word's baseline.
- Sim: sing-along karaoke.
- Ch: V, TTS.
- Effect/risk: L+ for following along. It sits *above* the x-height and must
  not cover ink.
- Build: `willSpeakRange` plus `ReadAloudGeometry`, drawn as an overlay.
- Cost: S.
- Test: preference.
- Where: phone.

**M21. Reading-guide card.** A physical card slides under the current line and
dims the lines below it. Tilt moves it.
- Sim: the dyslexia reading-ruler card.
- Ch: V, M.
- Effect/risk: L± (evidence for rulers is mixed [inf]). **Dimmed text breaches
  7:1 by design → RULING NEEDED**. The alternative is an underlay band beneath
  the current line with no dimming.
- Build: line rects plus `TiltGestures.h`.
- Cost: S.
- Test: ledger block.
- Where: phone.

**M22. Jeweler's loupe.** A long-press shows a round loupe of the page at an
**integer ×4, nearest-neighbor, in X3 device pixels**.
- Sim: a loupe on a proof.
- Ch: V, H (a click when it snaps).
- Effect/risk: L+ as a *tool*. It lets the owner judge Albo's spacing at X3
  pixels on the phone (see `research-claude-for-kerning-and-layout-2026-09-24.md`).
- Build: an overlay that samples the panel texture; the long-press binding goes
  in `GestureBindings.h`.
- Cost: S.
- Test: none needed. It is a tool.
- Where: phone.

**M23. Cassette audiobook.** TTS with tape hiss, slight wow and flutter, and
the clunk of flipping to side B at the chapter end.
- Sim: books on tape.
- Ch: TTS, A.
- Effect/risk: E± (nostalgia). Wow and flutter on speech harms intelligibility
  if it exceeds about 0.5% [inf], so keep it subtle.
- Build: route AVSpeech into an AVAudioEngine with a varispeed node and a
  noise bed.
- Cost: M.
- Test: rating.
- Where: phone.

**M24. Train-window reading.** A soft periodic sway haptic and rail clack at
about 1 Hz, and a slow light band that passes over the glass.
- Sim: reading on a train.
- Ch: A, H, V.
- Effect/risk: E± (motion sickness risk). The light band must be darken-only
  and slow.
- Build: an AHAP loop plus an output-space band.
- Cost: S.
- Test: rating.
- Where: phone.

**M25. Slide-projector carousel.** A page turn is a clunk, a half-second dark
gap, and the next slide pops in, over a fan hum.
- Sim: a Kodak Carousel.
- Ch: V, A, H.
- Effect/risk: E±. The dark gap is exactly the perceptual washout the test
  method wants, which is an amusing side use.
- Build: a transition plus audio.
- Cost: S.
- Test: preference.
- Where: phone.

**M26. Index-card baselines.** Pale blue rules sit exactly under each baseline,
with a red margin rule.
- Sim: a ruled card.
- Ch: V.
- Effect/risk: L+ as a tracking aid, like M4. The rules must sit on true
  baselines, below the descender clearance.
- Build: M4's baseline data.
- Cost: S.
- Test: ledger block.
- Where: phone and desktop. The firmware could draw it.

### 2B. FANTASTICAL (28)

**F1. Text set in water.** Touching the page sends ripples out from your
finger. They displace nothing but the *light*: a darken-only caustic. The text
settles still within about 400 ms.
- Sim: a page under a still pool.
- Ch: V, H (a decaying continuous event).
- Effect/risk: E+. Motion over text costs legibility, so it is transient only
  and must never displace glyph pixels (no warp).
- Build: an output-space caustic field seeded at the touch point.
- Cost: M.
- Test: preference.
- Where: phone.

**F2. The manuscript that gilds as you read.** Lines you have finished get a
gold rule in the margin. Chapter initials burnish, and their sheen follows the
device's tilt.
- Sim: illumination as a record of reading.
- Ch: V, M.
- Effect/risk: E+. Gold ink on paper is often under 7:1, so **gild the
  margin and the drop initial only, never the body text.**
- Build: line rects from the capture, and CoreMotion gravity for the specular
  position.
- Cost: M.
- Test: preference plus use.
- Where: phone.

**F3. Bioluminescent ink.** On the dark page, glyphs brighten slightly where
disturbed (a touch, a page turn) and fade over 1–2 s, like dinoflagellates.
- Sim: a glowing sea.
- Ch: V, H.
- Effect/risk: E+. **Brightening the glyph itself, not a halo**, respects the
  bloom ruling. It must not exceed the paper-to-ink range.
- Build: the phosphor trail accumulator, used as an excitation map.
- Cost: M.
- Test: 2AFC.
- Where: phone.

**F4. The page is a window at dusk.** The paper warms and dims with your real
local sunset and hands over to the dark page at night.
- Sim: reading by a west window.
- Ch: V.
- Effect/risk: E+. **RULING NEEDED**: palette freeze. Each state must pass
  7:1. Location needs permission, or can be approximated from the time zone.
- Build: a scheduled blend between the two frozen pages.
- Cost: S.
- Test: preference over weeks.
- Where: phone.

**F5. The book that ages with you.** A book's paper yellows, foxes and softens
in proportion to *your* cumulative minutes in it (ledger). A finished book
looks loved, and a new one looks new.
- Sim: time-lapse wear.
- Ch: V.
- Effect/risk: E+. It shares budget with drift and defects.
- Build: per book key, ledger minutes drive the drift, defect density and edge
  browning (M11).
- Cost: M.
- Test: preference.
- Where: phone and desktop.

**F6. The whisper that follows your eyes.** A TTS whisper reads the line you
are looking at.
- Sim: a companion reading over your shoulder.
- Ch: TTS, camera (ARKit).
- Effect/risk: likely L−. On-screen gaze from ARKit is reported too inaccurate
  for targeting [src summary]. Adding a camera **breaks the no-camera gate and
  the privacy story** [repo]. A feasible variant: the whisper follows your
  *finger* resting under a line.
- Build: `willSpeakRange` plus a touch-to-line hit test.
- Cost: L for the camera version, S for the finger version.
- Test: measure gaze error first (§4, spike 8).
- Where: phone.

**F7. Paper grain under the fingertip.** As a finger drags across the page, a
continuous haptic's intensity and sharpness follow the tooth field under it.
Laid paper's chain lines come through as regular ticks, and a wax spot is slick.
- Sim: touching the sheet.
- Ch: H.
- Effect/risk: E+ and novel. There is no legibility cost at all.
- Build: sample `Letterpress.h` tooth and `LaidStructure.h` at the touch point,
  and feed it to a `CHHapticAdvancedPatternPlayer` with dynamic parameters.
- Cost: M.
- Test: blind stock identification by touch (can he tell India from Laid with
  his eyes closed?).
- Where: phone.

**F8. The metronome that paces reading.** A soft haptic pulse per line at his
own median rate, slowly nudging about 3% faster per week.
- Sim: a practice metronome.
- Ch: H, A (optional).
- Effect/risk: an L± experiment. Pacing may hurt comprehension (see M6). This is
  an *experiment*, not a feature.
- Build: the ledger rate plus line rects, and an AHAP transient.
- Cost: S.
- Test: a Phase-2-style randomized arm (**RULING NEEDED**,
  `reading-experiments.md` §0) with a comprehension spot-check.
- Where: phone.

**F9. Pages turning in a chosen room.** The page-turn sound (M16), and a very
quiet room tone, convolved with a room: a cathedral, a tiled bath, the Long
Room at Trinity, a cabin.
- Sim: acoustic place.
- Ch: A.
- Effect/risk: E+.
- Build: `AVAudioUnitReverb` presets, or PHASE [src].
- Cost: S–M.
- Test: rating.
- Where: phone.

**F10. Candlelight.** The light page is lit by a flame. A warm, slow luminance
flicker (under 2 Hz and under 3% amplitude) plays over the paper, with a faint
moving shadow of the flame at the top edge.
- Sim: reading by candle.
- Ch: V (procedural; video only if procedural fails), A (a flame crackle).
- Effect/risk: E+ and L−. Flicker is a comfort and photosensitivity risk. The
  darkest moment must still clear 7:1, so the flicker spends budget.
- Build: a darken-only multiply field in output space, driven by a seeded noise
  generator.
- Cost: S.
- Test: 2AFC plus a comfort rating after 10 minutes.
- Where: phone.

**F11. The goal as a candle burning down.** A candle in the pad band, or the
margin in zen, burns through the 5-minute zen goal. As it gutters, the page
behaves as the reading goal already does, and then it goes out.
- Sim: time as a candle.
- Ch: V, A (the snuff), H (a soft pulse when it goes out).
- Effect/risk: E+. It makes the goal *visible before* the decay minute, which
  the current design does not.
- Build: `SurfaceAllowance.h`'s clock drives an overlay sprite. The glyph page
  is untouched.
- Cost: S.
- Test: preference, plus whether goals are completed more often (ledger).
- Where: phone. A 1-bit candle icon on the device is possible [inf].

**F12. Wet ink that dries.** A freshly turned page glistens for a second, with
a tilt-responsive specular on the strokes, and then dries matte.
- Sim: just-printed.
- Ch: V, M.
- Effect/risk: E+. The specular must not lift ink toward paper below 7:1, so
  keep it on the paper side or darken the ink only.
- Build: letterpress rim pass, with a time-decayed gloss term.
- Cost: M.
- Test: 2AFC.
- Where: phone.

**F13. The compositor sets the page.** On a page turn, lines slide in from the
left one by one, like a stick of type being emptied into the chase, each with
a tick.
- Sim: hand composition.
- Ch: V, A, H.
- Effect/risk: E+ for novelty. Latency, so it must be skippable.
- Build: a transition using line rects.
- Cost: M.
- Test: preference.
- Where: phone.

**F14. The voice lives in the book.** With AirPods, the read-aloud voice is
spatialized to come *from the phone's position*, and it stays there as you turn
your head.
- Sim: someone reading to you from the book.
- Ch: TTS, A (spatial), M (head tracking).
- Effect/risk: E+ and uncanny. It needs headphones.
- Build: AVSpeech `write` into buffers, then AVAudioEnvironmentNode or PHASE,
  then head pose [inf].
- Cost: L.
- Test: rating.
- Where: phone.

**F15. The book performs itself.** Quoted dialogue is spoken in a second voice
and narration in the first. Distinct characters get distinct voices where
attribution is simple ("said X").
- Sim: a radio play.
- Ch: TTS.
- Effect/risk: E+. Misattribution is jarring, so fall back to two voices only
  (narration and quote).
- Build: split quote spans in the captured page text into utterances, using
  SSML [src].
- Cost: M.
- Test: rating.
- Where: phone.

**F16. Shake the snow globe.** In the e-ink mode (M8), shaking the phone *is*
the full refresh: the letters loosen, swirl as the ghosting clears, and settle.
- Sim: a snow globe as an e-ink GC16.
- Ch: V, H, M.
- Effect/risk: E+. It maps a real device ritual (the manual full refresh) to a
  gesture.
- Build: the shake is already a gesture [repo, `GestureBindings.h`], so this
  needs M8 plus a settle transition.
- Cost: S on top of M8.
- Test: preference.
- Where: phone.

**F17. Frost that thaws under the finger.** A cold morning: frost feathers over
the *margins*, and rests where a finger rested melt.
- Sim: a frosted window.
- Ch: V, H.
- Effect/risk: E+. **Frost over the text is forbidden**, so margins only.
- Build: a margin-only field with a touch-melt accumulator.
- Cost: M.
- Test: preference.
- Where: phone.

**F18. Constellation headings.** On the dark page, chapter titles only are drawn
as star fields that resolve into letters.
- Sim: a planetarium.
- Ch: V.
- Effect/risk: E±. Body text must never be affected.
- Build: heading detection requires firmware knowledge (the block type), which
  is not published.
- Cost: L.
- Test: preference.
- Where: phone. Low priority.

**F19. The breathing page.** The paper luminance rises and falls about 1% at 6
breaths a minute, with an optional matching haptic swell, as a calm-reading
mode.
- Sim: resonant breathing.
- Ch: V, H.
- Effect/risk: E±. Very low flicker frequency, but it is still modulation, so
  it must stay within budget.
- Build: a multiply field.
- Cost: S.
- Test: a comfort rating.
- Where: phone.

**F20. Heartbeat pacing.** The Apple Watch heart rate modulates a very slow
page-glow or pulse haptic.
- Sim: biofeedback.
- Ch: H, V.
- Effect/risk: E?. It needs HealthKit permission, and live heart rate is
  awkward on iOS without a watch app [inf].
- Cost: L.
- Test: rating.
- Where: phone. Low priority.

**F21. Weather at the window.** When it is raining where you are, the page dims
by a hair and rain sounds on the glass. Snow gives a hush.
- Sim: the outside, coming in.
- Ch: A, V.
- Effect/risk: E±. It needs WeatherKit and location.
- Cost: M.
- Test: rating.
- Where: phone.

**F22. Palimpsest.** The show-through source is the **last page of the previous
book you read**, scraped and faint under this one.
- Sim: a reused parchment.
- Ch: V.
- Effect/risk: E+ and poetic. It uses the existing show-through budget, so
  there is zero new legibility risk.
- Build: `ShowThrough.h` takes an alternate source, a stored mirrored capture
  per last book.
- Cost: S.
- Test: preference.
- Where: phone and desktop.

**F23. Invisible ink.** The next paragraph starts pale and darkens as the TTS
voice (or your pace) approaches it.
- Sim: lemon juice over a flame.
- Ch: V, TTS.
- Effect/risk: **L−. Text meant to be read below 7:1 → RULING NEEDED.**
  Recorded as the inverse of the reading goal, and probably not worth it.
- Cost: S.
- Test: ledger.
- Where: phone.

**F24. The pen that writes as it is read.** During read-aloud, a quill scratch
follows each word, and words that have not been spoken are drawn a hair
lighter.
- Sim: dictation to a scribe.
- Ch: TTS, A, V.
- Effect/risk: E+. The same 7:1 caveat as F23 applies to the "lighter"
  half, so drop that half and keep the sound.
- Build: `willSpeakRange` triggers a scratch sample per word.
- Cost: S.
- Test: rating.
- Where: phone.

**F25. Sundial progress.** A gnomon's shadow crosses the top margin as you move
through the book (or the chapter). Its length follows the real time of day.
- Sim: a sundial.
- Ch: V.
- Effect/risk: E+ and L-neutral. It is chrome.
- Build: an overlay from the ledger's `sp`/`pg`.
- Cost: S.
- Test: preference.
- Where: phone. Possibly the device, as a firmware header glyph.

**F26. Felt punctuation.** During read-aloud, the Taptic Engine marks prosody:
- a light tick at a comma;
- a firmer tap at a period;
- a double tap at a paragraph end;
- a long soft swell at a chapter end.

Details:
- Sim: a conductor's hand.
- Ch: TTS, H.
- Effect/risk: E+ and **L+ for listening comprehension is plausible [inf]**.
  It gives structure without the eyes (pocket listening), and it is novel.
- Build: `willSpeakRange` supplies the character offsets, and punctuation is
  looked up in the captured text. There are 4 AHAP transients.
- Cost: S.
- Test: a block design with a rating, plus a recall question per chapter.
- Where: phone.

**F27. Heavy words.** Rarer words, by frequency in his own 36-epub corpus,
thump harder under the finger or the voice.
- Sim: the weight of vocabulary.
- Ch: H, TTS.
- Effect/risk: E±. It is likely noise.
- Build: a word-frequency table from `pair_census.py`'s corpus pass.
- Cost: S.
- Test: rating.
- Where: phone. Low priority.

**F28. Raking light that follows your hand.** The letterpress deboss and the
paper tooth are lit from a direction set by **device tilt**. Tip the phone and
the relief of the impression moves, as it does under a real lamp.
- Sim: a printed sheet under a desk lamp.
- Ch: V, M.
- Effect/risk: E+, strongly. It makes an existing effect physical, and adds no
  new darkening, because the deboss is already budgeted. The light direction
  must not lift the deboss past its budget.
- Build: `Letterpress.h`'s deboss shadow offset becomes a vector from CoreMotion
  gravity (already linked), fed through `SurfaceSheet.cpp`. The cache key must
  gain the light direction, *quantized*, or every tilt rebuilds the field.
- Cost: M.
- Test: 2AFC tilted vs fixed, plus the owner's "does it feel like paper".
- Where: phone.

---

Total: **26 mundane + 28 fantastical = 54 ideas.** The 28 are F1–F28; F28 was
listed last because it is the strongest.

---

## 3. What cannot work on the e-ink device, and why

| Channel | Device (X3) | Phone |
|---|---|---|
| Audio of any kind (M5 hum, M9, M10, M15, M16, M23, M25, F9, F14, F15, F21, F24) | **No** — no speaker [repo] | Yes |
| Haptics (M7, M9, M13, M14, M19, M22, M24, F1, F3, F7, F8, F11, F16, F17, F19, F20, F26, F27) | **No** — no actuator [repo] | Yes (Taptic Engine) |
| Motion-driven (M6, M21, F2, F12, F14, F16, F28) | No usable sensor on the X3 [inf] | Yes (CoreMotion) |
| Animation, transitions, flicker (M6, M19, M25, F1, F3, F10, F12, F13, F19) | **No** — refresh is 0.4–3.5 s [repo] | Yes |
| Continuous-tone surfaces (most visual ideas) | **No** — the surface passes are simulator-only, over a 4-level page [repo] | Yes |
| Layout or chrome drawable as 1-bit firmware UI (M4, M13, M17, M26, F11 icon, F25) | **Possible**, as firmware work | Yes |
| The e-ink refresh itself (M8) | **Native** | Simulated |

---

## 4. The shortlist: the 8 most promising, each with a spike plan

The ranking weighs four things: novelty, expected enjoyment, legibility risk
(lower is better), and reuse of existing machinery.

**1. F28 — Raking light that follows your hand.**
- **Hypothesis:** the letterpress stops being a texture and becomes an object.
- **Spike (3 days).**
  1. Add a unit light vector to the letterpress model, defaulting to today's
     implied direction.
  2. Show that bit-exactness at the default holds, with an md5 gate against the
     current render.
  3. Feed the vector from CoreMotion's gravity, low-passed at about 0.3 s and
     quantized to 16 directions. That makes the field cache hit, and
     `CROSSPOINT_SIM_LOG_TIMING` measures the rebuild.
  4. Sweep all 16 directions through `composition_test` for 7:1.
  5. Desktop QA hatch: `CROSSPOINT_SIM_LIGHT_DIR=<deg>`.
- **Deliverable:** a PNG crop set at native pixels for 4 directions, and a
  TestFlight build.
- **Status:** SHIPPED — UNCONFIRMED on device until the owner has tilted it.

**2. M8 + F16 — E-ink paper-white with a real waveform, and shake-to-refresh.**
- **Hypothesis:** the one surface that is a picture of the *actual* device is
  the most satisfying one, and ghosting will be tolerable at a budget.
- **Spike (1 week).**
  1. A pure `EinkWaveform.h` model: frames for a GC16-style clear
     (black → white → image) and for DU partials.
  2. A ghost as a non-decaying copy of the previous glass, at alpha under the
     floor budget, reset every N turns and on shake.
  3. Reuse `glassPrevTexture` and `setPresentFlash`.
  4. Test: 2AFC against a phone photo of the X3 mid-refresh. Owner time: two
     5-minute sessions.
- **Risk:** the flash is a photosensitivity question. Keep one flash per N
  pages, default N ≥ 6.

**3. F26 — Felt punctuation during read-aloud.**
- **Hypothesis:** structure conveyed by touch improves listening, and it is
  pleasant.
- **Spike (2 days).**
  1. A pure `ProsodyHaptics.h` maps the punctuation class at a spoken range to
     an event, with a host test.
  2. A `.mm` backend with 4 prebuilt `CHHapticPattern`s, triggered from the
     existing `willSpeakRange` delegate. That runs on a private queue, so hop to
     main [repo, `CrossPointReadAloud.mm:28`].
  3. Guard against the iOS 18 marker drift: fire only on offsets that are
     strictly increasing.
  4. Test: a week with it on and a week off, with a rating plus one recall
     question per chapter.

**4. M16 + F9 — Page-turn sound and feel from the stock, in a chosen room.**
- **Spike (3 days).**
  1. Record or synthesize 3 turn samples: thin, medium and laid.
  2. Build AHAP files with an audio track and a haptic.
  3. Trigger only on a reader-page identity change, deduplicated the way the
     sheet identity is.
  4. An AVAudioEngine chain: a reverb unit with 4 room presets.
  5. Set the session category so it mixes with read-aloud and ducks under it.
  6. Test: a block design and a rating. Measure latency from commit to sound
     (under 30 ms is the target [inf]).

**5. F11 — The zen goal as a candle.**
- **Hypothesis:** a visible, calm countdown helps more than a surprise decay.
- **Spike (2 days).**
  1. A procedural candle sprite (flame, a wax height that follows
     `Session::used`) in the pad band, or in the left margin in zen.
  2. Snuff audio and a haptic at zero.
  3. The page is untouched until the existing decay minute.
  4. Test: whether goals are completed per zen start (the ledger's `evt` lines),
     2 weeks on and 2 weeks off.

**6. F7 — Paper grain under the fingertip.**
- **Spike (4 days).**
  1. A pure sampler over the tooth and laid fields at a touch point, giving
     intensity and sharpness, with a host test.
  2. `CHHapticAdvancedPatternPlayer` with a continuous event, updating its
     dynamic parameters at 60 Hz from `padWatch` finger-motion events. The pad
     and finger path already exist [repo, CLAUDE.md input section].
  3. Test: blind stock identification by touch, 20 trials, with India, Laid
     Antique and a vellum stock. Chance is 33%. Over 60% is a real signal.
- **Where:** phone only.

**7. M22 — The X3-pixel loupe.**
- **Hypothesis:** the owner judges Albo's spacing on the phone at a
  magnification that shows the X3's real pixels. This couples directly to the
  kerning plan (JND experiment E1).
- **Spike (1–2 days).**
  1. A long-press binding, via a new action in `GestureBindings.h` and its
     generator.
  2. An overlay that samples the panel texture in X3 device pixels at integer
     ×4, nearest-neighbor, in a round mask.
  3. A haptic click when the loupe snaps to a pixel boundary.
  4. No test needed, since it is a tool. Verify by comparing the loupe's pixels
     with a 1x headless capture, bytewise.

**8. F5 (+ M1) — The book that ages with you.**
- **Spike (4 days).**
  1. A pure mapping from ledger minutes per book key to drift, defect density
     and edge-browning amounts, capped by the existing budgets.
  2. Per-page re-read wear from page visit counts.
  3. Read the ledger at book open. It already exists and holds no titles [repo].
  4. Test: preference after a month. The effect is slow by design, so the
     test is the owner's reaction to a 50-hour-old book against a new one,
     rendered side by side.

**Runners-up:** M4 green-bar or M26 index-card baselines (possibly L+,
testable in the ledger), M5 microfiche, and F22 palimpsest (very cheap).

---

## 5. How to test any of these without repeating past mistakes

Every rule below comes from `docs/perceptual-test-method.md` [repo].

- **Washout between visual stimuli.** Use 900 ms between trials and 350 ms
  between the two cards of one trial.
- **Carry catch trials.** Repeat identical stimuli so the noise floor is
  measured.
- **Never ask a comparison he cannot make.** If two arms are too close, the
  answer carries no information.
- **Grep the stimulus for the thing being tested.** Before analyzing a
  time-varying effect, confirm the stimulus actually renders it. The phosphor
  run analyzed persistence on a page that never animated.
- **Pin the grain seed and restore the card between arms** [repo, CLAUDE.md].
- **Audio and haptics:** use blocks of days, not interleaved trials. Adaptation
  and novelty are strong. Record the setting in the ledger's `cfg` line, so
  every line written says which arm it was.
- **Name the outcome before the run:** enjoyment rating, completion, recall.
  Reading rate is only for levers expected at 10% or more (`reading-experiments.md`
  §6).
- **Every new visual pass joins `composition_test`** before it ships.
- **Do not run anything that teaches nothing new** (the global P0).

## 6. Not verified

- **ARKit gaze accuracy** comes from a search summary. It was not measured.
- **AirPods head tracking** is from memory, not re-checked.
- **The "L+" estimates** for line-tracking bands and felt punctuation are
  inferences. I cite no study that measured them.
- **All costs are estimates.**
- **No idea here has been rendered.** Per the owner's visual-gate rule, any of
  these that goes to a decision needs a real rendering published first, and no
  prose description.

## Sources

- Apple, AHAP files: https://developer.apple.com/documentation/corehaptics/representing-haptic-patterns-in-ahap-files
- Core Haptics guides: https://www.kodeco.com/10608020-getting-started-with-core-haptics · https://exyte.com/blog/creating-haptic-feedback-with-core-haptics
- AVSpeech willSpeakRange: https://developer.apple.com/documentation/avfoundation/avspeechsynthesizerdelegate/1619681-speechsynthesizer · https://www.hackingwithswift.com/example-code/media/how-to-highlight-text-to-speech-words-being-read-using-avspeechsynthesizer
- SSML utterances: https://useyourloaf.com/blog/synthesized-speech-from-text/ · https://github.com/mapbox/mapbox-navigation-ios/issues/4057
- Marker sync issue on iOS 18: https://developer.apple.com/forums/thread/769342
- Personal Voice in apps: https://bendodson.com/weblog/2024/04/03/using-your-personal-voice-in-an-ios-app/
- PHASE, WWDC21: https://developer.apple.com/videos/play/wwdc2021/10079/
- AVAudio HRTF: https://developer.apple.com/documentation/avfaudio/avaudio3dmixingrenderingalgorithm/hrtf
- ARKit lookAtPoint: https://developer.apple.com/documentation/arkit/arfaceanchor/lookatpoint?language=objc
- E-paper waveform modes: https://www.waveshare.com/w/upload/c/c4/E-paper-mode-declaration.pdf
- Schotter, Tran and Rayner 2014: https://journals.sagepub.com/doi/10.1177/0956797614531148
