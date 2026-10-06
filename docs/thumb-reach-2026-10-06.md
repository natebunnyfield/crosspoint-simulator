# Can the thumbs reach the buttons? Measured, with options (2026-10-06)

Owner, 2026-10-06: *"take a pass at button layout so thumbs can easily and
always reach them"*.

**Status: SHIPPED as TestFlight build 307 (0.1.1, 2026-10-06), the recommended set: P-B, L-B and T-B.** The options were
published as mockups composed from the app's own captures
(https://claude.ai/artifact/G2mSTy26NSpjveuzEzkudB), and the owner answered
*"go"*. One detail differs from the T-B mockup: the front pairs stay exactly on
the ruled thumb row (2026-08-09) and the rocker row hangs under them, where the
mockup had nudged the whole block 24 pt up to center it.

**Verified on fresh Simulator captures** (iPhone Air, iPad Pro 13), positions
measured off the outlines, in pt:
- phone portrait: front row 629-693 (unchanged), rocker row 709-773 (was
  806-870), pairs at 48-177 and 243-372 (were 16-145 and 275-404);
- phone landscape: upper row 132-196, rocker 212-276 (was 336-400);
- iPad portrait: front pairs 898-958 (centered on the thumb row at 928),
  rocker 974-1006 (was about 1319-1351);
- iPad landscape: front pairs 554-614, rocker 630-662 (was 975-1007).

Host test `turned_page_landscape` pins the landscape half: the phone's blocks
are centered on the height, and the iPad's rocker hangs under the front pairs.
Both new checks fail on the old layout (checked). The portrait halves live in
the shim and are verified by capture only. Device feel is UNCONFIRMED. Sources
are named in the section below, and every number here is either measured from a
capture or quoted from one of them.

## The reach data

- **Kim et al., "Defining Thumb Reach Envelopes for Handheld Devices"** (Human
  Factors, 2013; numbers via the ergoweb summary,
  https://ergoweb.com/thumb-reach-distances-and-envelopes-for-handheld-devices/).
  One hand, device held upright, measured from the DEVICE's edges. The zones:

  | zone | share of people | above the bottom | in from the gripping side |
  |---|---|---|---|
  | comfortable | 90% | 45.6-49.4 mm | 25.4-35.5 mm |
  | extended | 70% | 34.2-56.1 mm | 15.2-45.6 mm |

  Mean maximum reach was 51.8-61.4 mm, depending on the group.
- **Le et al., "Fingers' Range and Comfortable Area for One-Handed Smartphone
  Interaction Beyond the Touchscreen"** (CHI 2018,
  https://sven-mayer.com/wp-content/uploads/2018/01/le2018fingers.pdf):
  - the thumb's comfortable area on the screen is about 36 cm² (33.6-41.9) and
    does not grow with the phone;
  - people hold larger phones higher;
  - the far top corner cannot be reached without changing grip;
  - their advice: "place input controls higher for larger devices".

**Limits of the data.** Kim measured a small device (an iPod Touch) and Le
measured phones up to 6 inches, all with right-handed participants. Since a
bigger phone is held higher, the band on an iPhone Air sits at least as high as
these numbers, never lower. No study here gives a two-handed LANDSCAPE band. The
iPad case rests on the maximum reach distance alone.

## Where the controls are today

Screen edges, converted at 460 ppi (iPhone Air) and 264 ppi (iPad Pro 13). Add
about 2.5 mm of bezel to compare against the device-edge zones above. Every
rect was measured off a capture, not taken from the code.

**iPhone Air, portrait (the pad under the page):**

| controls | above the screen's bottom | in from the side |
|---|---|---|
| front row: Back/Select left, Left/Right right | 36.3-46.8 mm | outer cell 2.7-13.4 mm, inner cell 13.4-24.1 mm |
| page rocker (Up/Down) | 7.0-17.6 mm | as the front pair |
| POWER (half height) | 7.0-12.2 mm | as the front pair |

**iPhone Air, the turned page's landscape:**

| controls | above the screen's bottom | in from the side |
|---|---|---|
| lower row (POWER, rocker) | 3.3-13.9 mm | 13.9-33.8 mm (the safe area takes 11.3 mm) |
| upper row (the front pairs) | 16.6-27.2 mm | 13.9-33.8 mm |

**iPad Pro 13:**
- the front pairs sit on the tablet thumb row, 448 pt (86 mm) above the bottom
  (owner ruling 2026-08-09);
- POWER and the rocker sit along the bottom edge, about 65 mm below that row.

## Findings

1. **The page rocker and POWER are below the thumbs, in every layout.**
   - On the phone in portrait they sit 9.5-20 mm above the device's bottom,
     against a reach band that starts at 34 mm.
   - On the iPad they are about 65 mm under the thumb row, beyond the measured
     MEAN MAXIMUM thumb reach of 52-61 mm. So reaching them takes a change of
     grip, every time.

   The rocker is a page-turn control, so this lands on the most-used action.
2. **On the phone, each pair's outer cell hugs the edge.** It sits 5-16 mm from
   the device's side, where the 70% zone starts at 15 mm. A thumb has to fold
   back on itself to press it.
3. **The front row is in the right band** in portrait (39-49 mm with the bezel)
   and need not move. It sits 11.6 mm under the page, on the chassis ruling.

## Options

They are composed from the captures. In the mockups each control carries a
translucent fill so its position reads at a small size; the app draws them as
outlines.

**Phone portrait:**

- **P-A, today.**
- **P-B: lift the rocker row, pull the pairs in.**
  - The rocker row and POWER sit 16 pt under the front row, as in landscape.
    The rocker moves from 9.5-20 mm to about 25.5-36 mm.
  - Both pairs come 32 pt (5.3 mm) in from the edges, so the outer cell starts
    about 10.5 mm from the device's side.
  - The front row stays on the chassis ruling.
- **P-C: one centered block.** The front four sit in one row at the center,
  with the rocker and POWER under them. That puts every control 24-45 mm from
  EITHER side, which is the extended zone for one-handed use with either hand.
  It gives up the left/right split and the hand each half belongs to.

**Phone landscape (the turned page):**

- **L-A, today:** both rows are anchored to the bottom.
- **L-B: each side's 2x2 block centered on the screen's height,** where the
  thumbs of a two-handed grip rest. The rocker rises from 3.3-13.9 mm to about
  23-33.5 mm.

**iPad (every layout, the turned page included):**

- **T-A, today.**
- **T-B: POWER and the rocker move up to sit 16 pt under the front pairs,** as
  one block centered on the ruled thumb row. Nothing is left at the bottom
  edge.

## Not checked

- **Left-handed grips.** Le et al. recruited right-handed people only. The
  phone portrait's split layout is symmetric, so P-A and P-B treat both hands
  alike.
- **The X4 Pro and Sticky profiles,** whose pads differ.
- **The volume-buttons-as-rocker setting,** which is physical and unaffected.
- **Device feel:** UNCONFIRMED, as always for a layout that has to be held.
