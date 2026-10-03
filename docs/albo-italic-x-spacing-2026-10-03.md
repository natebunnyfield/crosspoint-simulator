# Albo: is the italic x loose? (2026-10-03)

Owner, asked "4 of 4" of the queued questions (should round 461's x spacing be
checked, given round 463 found the band measure over-reads reaching stroke
ends): *"Show me options."*

**Status: OPTIONS. Nothing shipped.**

## The question

Round 461 redrew the italic x and held its spacing by adding white:
`X_DLSB` +20 on the left, and `X_DRSB` +6 (Italic) / +12 (Bold Italic) on the
right. That made the model's band white (the ink extremes inside the x band)
match build 282's. Round 463 then showed the same measure over-reads a letter
whose stroke ends reach out: it asked to push every c about 40 units away
(`docs/albo-round-463-2026-10-02.md`).

## Measured: the 2-D closest approach (`cmp_space_2d.py --pairs`)

Em at a 150 px x-height, against the seven reference italics. Albo's own
rhythm is looser than the references' everywhere, so each pair is read as a
ratio over the reference median. Measured on control pairs with no x in them
(an in on un na ni no nu nt), Albo's italic runs **about 1.2×**.

| pair | ref median | today | Y1 (half) | Y2 (none) |
|---|---|---|---|---|
| ex | 0.053 | 0.096 (1.8×) | 0.087 | 0.078 (1.5×) |
| ax | 0.036 | 0.070 (1.9×) | 0.059 | 0.050 (1.4×) |
| ix | 0.045 | 0.112 (2.5×) | 0.101 | 0.092 (2.0×) |
| nx | 0.053 | 0.093 (1.8×) | 0.085 | 0.076 (1.4×) |
| ux | 0.042 | 0.109 (2.6×) | 0.099 | 0.089 (2.1×) |
| xe | 0.078 | 0.114 (1.5×) | 0.113 | 0.109 (1.4×) |
| xa | 0.069 | 0.089 (1.3×) | 0.088 | 0.085 (1.2×) |
| xi | 0.067 | 0.115 (1.7×) | 0.111 | 0.109 (1.6×) |
| xu | 0.059 | 0.140 (2.4×) | 0.137 | 0.134 (2.3×) |
| xp | 0.041 | 0.114 (2.8×) | 0.111 | 0.108 (2.6×) |

**Around the x, Albo runs about 1.75× against 1.2× elsewhere:** the x reads
loose, mostly on its left. Removing the correction (Y2) brings the left-side
pairs to 1.4–2.1×. The right side barely moves, because its correction was
only 6 units. The Bold Italic reads the same way (today ex 0.098 / ax 0.067 /
ix 0.112 against a reference median of 0.052 / 0.031 / 0.037; Y2 0.083 /
0.048 / 0.093).

## The arms

| arm | Italic X_DLSB / X_DRSB | Bold Italic | added by the clearance loop |
|---|---|---|---|
| today | 20 / 6 | 20 / 12 | |
| **Y1** | 10 / 3 | 10 / 6 | `R x` +7 (Bold Italic) |
| **Y2** | 0 / 0 | 0 / 0 | `R x` +8 (Italic), +17 (Bold Italic): round 461's first-pass values |

- The R's leg is the one pair that closes when the x moves in. Without its
  kern it falls under the floor (Y1 Bold Italic, Y2 Italic) or touches (Y2
  Bold Italic).
- With it, both arms are touch 0 / 0, composite and 2-D mark clearance 0, and
  kern classes ok (124 / 159, 123 / 160).
- Only the x moves. λ and χ are compensated in `build.fit_greek` as before.

Reproduce: `env "${ALBO_ITA_ENV[@]}" ALBO_ALD_X_DLSB=0 ALBO_ALD_X_DRSB=0 ...`,
then the clearance loop on a candidate table (`ALBO_SPACING_TABLES`).

Proof page: https://claude.ai/artifact/MH9gPVMhEMGDgSZexi4UvM
