# The poor-characters render + gate harness (2026-09-26)

docs/albo-poor-characters-2026-09-26.md. Build an arm from `git archive HEAD`
plus the working copies of the glyph files, score it with the fit audit, gate it.

    export POOR_WORK=/some/scratch  POOR_PY=/python/with/scipy+freetype+uharfbuzz
    export VISIONOCR=<kept-legibility-index>/ocr/visionocr
    # POOR_WORK needs geom.json/legib.json carrying the reference faces
    # (fit_audit/run_all.sh writes them) and spacing.json (fit_audit/spacing.py)
    RESYNC=1 MINE_FILES="" ./arm.sh base "Regular Italic Bold BoldItalic" ""   # today
    ./score.sh base "Regular Italic Bold BoldItalic" y t          # F per cut
    ./redo.sh "Regular Bold" y y_geo=ALBO_ROM_Y_TAIL=geo           # build + score arms
    BASE=base ../poor_gates.sh $POOR_WORK/fonts/base $POOR_WORK/fonts/y_geo "Regular Bold"
    $POOR_PY thinmap.py FONT.ttf y out.png    # where the fit audit's p10 lives
    $POOR_PY ridgemap.py FONT.ttf F out.png   # the ridge by band about its p50

TAGS ARE DIRECTORY NAMES AND macOS IS CASE-INSENSITIVE: `t_pal` and `T_pal`
are one directory (it cost a clobbered arm here). Name capitals `Tcap_*`.
Run loops over word lists in bash, not zsh (zsh does not split `$L`).
