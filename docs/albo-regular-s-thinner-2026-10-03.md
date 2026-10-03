# Albo: a thinner Regular S, as options (2026-10-03)

Owner, after round 469 widened the Regular S to the Bold's proportion
(`docs/albo-round-469-2026-10-03.md`): *"give me regular S options that are
thinner."*

**Status: SHIPPED, N2** (owner *"N2"*), as round 471
(`docs/albo-round-471-2026-10-03.md`). Before the ruling: options. "Thinner"
was read both ways, and the proof showed both:

| arm | dials | S / H | S / E | S / O height | reads |
|---|---|---|---|---|---|
| today (round 469) | `ALBO_ROM_S_W` 1.20 | 0.643 | 0.879 | 1.001 | |
| **N1** | `ALBO_ROM_S_W` 1.10 | 0.591 | 0.808 | 1.001 | narrower: the narrowest regular references (Baskerville 0.594, Palatino 0.599) |
| **N2** | `ALBO_ROM_S_W` 1.15 | 0.618 | 0.844 | 1.000 | narrower: about the references' median (0.625) |
| **L1** | `ALBO_ROM_S_WT` 0.90 | 0.645 | 0.881 | 0.991 | lighter: every stroke width 10% thinner at today's width |
| **L2** | `ALBO_ROM_S_W` 1.15, `ALBO_ROM_S_WT` 0.90 | 0.615 | 0.841 | 0.996 | both |

- Measured by `instruments/bold_s_proof.py --measure`; `PROOF_CUT=Regular`
  now compares against six REGULAR references (Georgia, Charter, Palatino,
  Pagella, Times, Baskerville; S/H 0.59–0.66).
- `ALBO_ROM_S_WT` is new (`outlines/glyphs/caps_straight.py`, `S_WT_400`).
  It scales every width along the S's stroke, beak included, for stems 84 and
  under. The width solver holds the S's ink width, so S/H stays put. The top
  edge comes down with the stroke: S/O height 1.001 → 0.991.
- Only the Regular S moves. As in rounds 465 and 469, Ś Š Ş Ŝ Ș $ § follow it.

**Gates, each arm against round 470** (POOR GATES, Regular): no delta. Touch
0 / 0, no new hairs, census unchanged. A control build at the defaults is
identical to round 470.

Proof page: https://claude.ai/artifact/VqqeiCAHCopAZaHTtgjLDK
