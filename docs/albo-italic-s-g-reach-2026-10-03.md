# Albo: the italic S's and G's reach past the O (2026-10-03)

The owner was asked (one question at a time, "1 of 3"):
- The italic S's beak terminals reach well past the other round capitals.
- The Bold Italic S runs −57..724 and the G −56..731, where its O spans
  −15..690.
- Reference italic S's stay within 1% of their O's height.

He answered *"Show me options."*

**Status: RULED -- LEAVE** (owner 2026-10-03, *"leave, next"*): the italic S and G keep
their reach past the O, as intended. The dials stay in the code at 1.0 (today) as the
record; nothing ships. Before the ruling: options H1 / H2. The dials are `ALBO_ALD_S_REACH` and
`ALBO_ALD_G_REACH` (`outlines/glyphs/aldine.py`). Each is the fraction of the
ink's excess over the O that is kept. 1.0 (the default) is round 472 byte for
byte (control build).

## Why it reached

- **The S.** The spine's crown control point sits ON the cap line, and its
  bottom half an overshoot under the baseline. So the ink stands out by half
  the stroke there, and the stroke grows with the weight. The roman `g_S`
  places its crown at `C + o*0.9 - S_CROWN`, which compensates; the italic did
  not.
- **The G.** The bowl's radius `C/2 + 0.4*OVER` is its centerline, with the
  same result.
- **The O** is a ring whose outer edge is at `C/2 + OVER`.

**A trap found on the way (recorded so it is not re-learned).** Aldine's own
`glyph()` wrapper DILATES every italic capital after its builder returns, by
`S * 0.16 * (weight - 1)` for the capital's FIT weight (S 1.218, G 1.175).
That is 4.0 units for the Bold Italic S and 2.3 for the Italic. A target
measured inside the builder therefore lands short by exactly that. The first
two versions of the correction stopped 4 units high for this reason, and
iterating more did nothing. The dials now subtract the dilation.

**How the dial works.** The crown and bottom points (the S) or the radius (the
G) are corrected on the drawn ink until it lands within 0.3 units. The life
counter is restored between draws, so the serifs' jitter is the single draw's.

## The arms

| | Italic O | Italic S | Italic G | Bold Italic O | Bold Italic S | Bold Italic G |
|---|---|---|---|---|---|---|
| today | −15..689 | −34..701 | −35..709 | −15..690 | −57..724 | −56..731 |
| **H1** (`*_REACH` 0.5) | | −22..694 | −25..699 | | −36..707 | −36..710 |
| **H2** (`*_REACH` 0) | | −14..690 | −15..689 | | −15..690 | −15..690 |

**Moved:** S, G, their accented forms (Ś Š Ş Ŝ Ș Ğ Ĝ Ġ Ģ), and $ and §,
which are drawn from the S.

**Gates, each arm against round 472** (Italic and Bold Italic):
- POOR GATES: no delta. Touch 0 / 0, no new hairs, glitch 9 → 9 on the moved
  glyphs, contour census unchanged, approved letters unchanged.
- **The 2-D mark clearance re-tunes a few rare pairs**, which the ship's
  clearance loop would add:
  - H1: Bold Italic S + ï 16 → 20; Italic G + ĵ +1, ſ + Ŝ 17 → 24, ſ + Ĝ +3.
  - H2: Bold Italic S + ï 16 → 23, ſ + Ŝ +5; Italic G + ĵ +2, ſ + Ŝ 17 → 29,
    ſ + Ĝ +13.

Proof page: https://claude.ai/artifact/Y8zG3MEc17KXiYRetkymhM
