#!/usr/bin/env bash
# Build the roman Regular (and optionally the Italic) of Albo at a HISTORICAL
# commit, from a `git archive` snapshot -- never from the live tree, which
# another agent may be editing. Recipe = build_env.sh's ALBO_ROM_ENV, copied
# here as that file does for gates.sh (a builder that sources the tree under
# test is not a fixed recipe).
#
#   snap_build.sh COMMIT OUTDIR [EXTRA_ENV...]
#
# EXTRA_ENV are KEY=VALUE dials layered on top of the shipping env (used for
# the within-round dial toggles and the option arms).
# Environment: ETRACE_SCRATCH (snapshot root; default $TMPDIR/etrace),
#              ETRACE_ITALIC=1 also builds the Italic,
#              ETRACE_PATCH=file.patch applies a patch (-p1, repo-relative
#              paths) to a SEPARATE snapshot -- e_arms.patch adds the option
#              dials, defaults = today.
set -euo pipefail
commit="${1:?commit}"; out="${2:?outdir}"; shift 2
repo="$(cd "$(dirname "$0")/../../.." && pwd)"
root="${ETRACE_SCRATCH:-${TMPDIR:-/tmp}/etrace}/src"
sha="$(git -C "$repo" rev-parse --short "$commit")"
src="$root/$sha"
patch_file="${ETRACE_PATCH:-}"
if [ -n "$patch_file" ]; then
  patch_file="$(cd "$(dirname "$patch_file")" && pwd)/$(basename "$patch_file")"
  src="$root/$sha-$(basename "$patch_file" .patch)"
fi
if [ ! -f "$src/tools/wedge_serif/outlines/build.py" ]; then
  mkdir -p "$src"
  git -C "$repo" archive "$sha" tools/wedge_serif | tar -x -C "$src"
  if [ -n "$patch_file" ]; then ( cd "$src" && patch -p1 -s < "$patch_file" ); fi
fi
mkdir -p "$out"
out="$(cd "$out" && pwd)"
ROM=(FJORD_STEM=66.9 FJORD_CONTRAST=0.892)
ITA=(ALBO_ITALIC=aldine FJORD_STEM=66.9 FJORD_CONTRAST=0.80 FJORD_WIDTH=95 FJORD_SLANT=13)
( cd "$src/tools/wedge_serif" && env "${ROM[@]}" "$@" PYTHON_GIL=0 python3 -m outlines.build "$out" --style Regular >"$out/build-Regular.log" 2>&1 )
if [ "${ETRACE_ITALIC:-0}" = 1 ]; then
  ( cd "$src/tools/wedge_serif" && env "${ITA[@]}" "$@" PYTHON_GIL=0 python3 -m outlines.build "$out" --style Italic >"$out/build-Italic.log" 2>&1 )
fi
ls "$out"/*.ttf
