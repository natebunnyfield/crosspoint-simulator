#!/bin/zsh
# Wrapper: run the CI signing setup from the repo root with fresh code,
# regardless of the invoking shell's cwd.
#
# Mirrors ios/deploy-from-repo.sh, and exists for the same two reasons:
# Terminal `do script` tabs open in $HOME, and inline `cd &&` kept getting
# stripped from osascript invocations (crds-ios, 2026-06-09).
# setup-ci-signing.applescript calls this; phones fire the AppleScript over SSH.
#
# DEFAULTS TO --yes, which is the whole point of firing it remotely. Bare
# setup-ci-signing.sh only LISTS the identities and changes nothing; run 31
# (2026-09-12) still logged "IOS_SIGNING_P12_B64 not set" after the script had
# reportedly been run, which is exactly what a list-only run leaves behind.
# Pass an explicit argument to override, e.g. `--check` for a dry listing.
#
#   ios/setup-ci-signing-from-repo.sh              # export + set the secrets
#   ios/setup-ci-signing-from-repo.sh --check      # list only, change nothing
#   ios/setup-ci-signing-from-repo.sh --and-build  # also dispatch TestFlight
#
# --and-build is opt-in on purpose: storing a signing identity and starting a
# twenty-minute Mac build are two different decisions, and a build should not
# be a side effect of the first.
cd "$HOME/src/crosspoint-simulator" || exit 1
echo "== branch: $(git branch --show-current)"
git pull --ff-only || { echo "git pull failed — resolve on the Mac"; exit 1; }

SIMULATOR_REPO="${CROSSPOINT_SIMULATOR_REPO:-natebunnyfield/crosspoint-simulator}"

# No array INDEXING below, only membership: zsh subscripts from 1 and bash
# from 0, so `args[1]` would mean different things depending on which shell
# a reader reaches for. The shebang says zsh; this way the block is correct
# either way, and testable under bash.
AND_BUILD=0
STORES=0
args=()
for a in "$@"; do
  if [[ "$a" == "--and-build" ]]; then AND_BUILD=1; else args+=("$a"); fi
done
if [[ ${#args[@]} -eq 0 ]]; then
  args=(--yes)
  STORES=1
fi
for a in "${args[@]}"; do
  [[ "$a" == "--yes" ]] && STORES=1
done

./ios/setup-ci-signing.sh "${args[@]}" || exit $?

if [[ $AND_BUILD -eq 1 ]]; then
  if [[ $STORES -eq 0 ]]; then
    echo "== --and-build ignored: signing secrets were not stored by this run"
    exit 0
  fi
  echo "== dispatching testflight-ios.yml on $SIMULATOR_REPO"
  gh workflow run testflight-ios.yml --repo "$SIMULATOR_REPO" \
    || { echo "dispatch failed — run it by hand"; exit 1; }
  echo "   watch: gh run list --workflow testflight-ios.yml --repo $SIMULATOR_REPO"
fi
