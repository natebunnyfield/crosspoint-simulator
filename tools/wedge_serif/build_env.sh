# THE SHIPPING ENVIRONMENT FOR BOTH STYLES, in one place.
#
# `python3 -m outlines.build DIR --style Italic` with no environment builds a
# DIFFERENT FONT -- not the aldine italic, at a different contrast, width and
# slant -- and it builds cleanly and looks like Albo, so the mistake is silent.
# It cost a wrong before/after reading on 2026-09-21: both arms of a spacing
# proof were built bare, the italic's new capital kerns were not in either, and
# the measured change came back at +9 units where the real one was -41.
#
#   source build_env.sh
#   albo_build OUTDIR          # both styles, shipping dials
#
# gates.sh keeps its own copy of these two lines deliberately -- a gate that
# sources a file the change under test could edit is not a gate.
ALBO_ROM_ENV=(FJORD_STEM=66.9 FJORD_CONTRAST=0.892)
ALBO_ITA_ENV=(ALBO_ITALIC=aldine FJORD_STEM=66.9 FJORD_CONTRAST=0.80 FJORD_WIDTH=95 FJORD_SLANT=13)

albo_build() {
  local out="${1:?usage: albo_build OUTDIR}"
  local here; here="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
  ( cd "$here" && env "${ALBO_ROM_ENV[@]}" PYTHON_GIL=0 python3 -m outlines.build "$out" --style Regular ) || return 1
  ( cd "$here" && env "${ALBO_ITA_ENV[@]}" PYTHON_GIL=0 python3 -m outlines.build "$out" --style Italic  ) || return 1
}
