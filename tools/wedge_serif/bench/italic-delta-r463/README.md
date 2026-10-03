# The italic re-basing pair, refreshed 2026-10-02 (round 463)

Owner ruling 2026-10-02: *"Refresh and refit now"* (docs/local-ai-spacing-options-2026-09-26.md §14c).

- `Albo-Italic-old.ttf`: unchanged from `../italic-delta-r409/` -- round 408's outline on round 405's
  tables, the outline his bench zero (09-20) was read against.
- `Albo-Italic-new.ttf`: TODAY's outline (commit ae11c1d, rounds 461-462) on the SAME round-405 tables
  (`git show 0bb48e5:tools/wedge_serif/outlines/spacing_b2.json`), built with the three code-level
  bearing corrections added since round 409 switched OFF, so the pair differs in OUTLINE only:

      env "${ALBO_ITA_ENV[@]}" ALBO_SPACING_TABLES=_r405_tables.json ALBO_ALD_A_RSB=0 \
          ALBO_ALD_R_DRSB=0 ALBO_ALD_R_DRSB_700=0 ALBO_ALD_X_DLSB=0 ALBO_ALD_X_DRSB=0 \
          PYTHON_GIL=0 python3 -m outlines.build OUT --style Italic

  (`_r405_tables.json` is that round-405 table file copied beside spacing_b2.json for the build.)

Checked: against `../italic-delta-r409/Albo-Italic-new.ttf` (round 409's outline, same tables), every
letter not redrawn since 409 measures exactly 0 kern-free band-white change as either member of a pair
with n, o, u (b d f g h i k l m n p q s t u w z). The redrawn ones: c right -44 (its drawn top, rounds
432-435), x right -20 / left -6 (round 461's cup), a +10 / -10 (round 419), r +4, e +5 / -2, j -2 / +3.

## The page builds (rows read on post-409 outlines)

`page-r430.ttf` and `page-r453.ttf`: the italic outline of round 430 (1ba6349, the family bench's
zero) and of round 453 (843de78, the words bench's zero), each built in a worktree on the same
round-405 tables with the code bearing corrections of its day off (`ALBO_ALD_A_RSB=0`, and at 453
`ALBO_ALD_R_DRSB=0 ALBO_ALD_R_DRSB_700=0`). `b2_fit.page_correction` re-bases each tables-converted
row from those benches by its own page's outline: measured, family ry -18 (round 430's r), words aq
+10, ex +5, le -2, se -2 (the a and e redrawn after 409), every other row 0.
