#!/usr/bin/env bash
#
# One-shot, run ON THE MAC from a GUI Terminal: store this Mac's Apple signing
# identities in the simulator repo's Actions secrets, so hosted TestFlight iOS
# runs sign with an EXISTING certificate instead of minting a new one per run.
#
#   ios/setup-ci-signing.sh          list the identities, change nothing
#   ios/setup-ci-signing.sh --yes    export them and set the two secrets
#
# Why: with only the ASC API key, xcodebuild -allowProvisioningUpdates creates
# a fresh Apple Development certificate on every runner (its keychain starts
# empty, and the previous run's private key died with its runner). Apple caps
# certificates per account; run 17 (2026-09-05) hit the cap -- "Choose a
# certificate to revoke" -- and stopped at Archive. An imported identity is
# found before any minting is attempted, so the cap never comes up again.
#
# What is exported: EVERY code-signing identity (certificate + private key)
# in the login keychain, as one password-protected PKCS#12. The list is
# printed first and --yes is required. macOS asks, per key, whether
# `security` may export it: click Allow. Needs gh (authenticated) and a
# login keychain that is unlocked, i.e. a GUI Terminal, the same constraint
# ios/testflight.sh has for codesign.

set -euo pipefail

SIMULATOR_REPO="${CROSSPOINT_SIMULATOR_REPO:-natebunnyfield/crosspoint-simulator}"
KEYCHAIN="${CROSSPOINT_LOGIN_KEYCHAIN:-$HOME/Library/Keychains/login.keychain-db}"

say() { printf '\n=== %s ===\n' "$1"; }
die() { printf '\nERROR: %s\n' "$1" >&2; exit 1; }

command -v gh >/dev/null || die "gh not found. brew install gh && gh auth login"
gh auth status >/dev/null 2>&1 || die "gh is not logged in: gh auth login"
[[ -f "$KEYCHAIN" ]] || die "no login keychain at $KEYCHAIN (set CROSSPOINT_LOGIN_KEYCHAIN)"

say "Code-signing identities in $KEYCHAIN"
security find-identity -v -p codesigning "$KEYCHAIN" | sed 's/^/  /'
security find-identity -v -p codesigning "$KEYCHAIN" | grep -q '"Apple Development' \
  || echo "  WARNING: no Apple Development identity here; Xcode on this Mac has never signed for a device"

if [[ "${1:-}" != "--yes" ]]; then
  say "Nothing changed"
  echo "Re-run with --yes to export ALL of the identities above into a"
  echo "password-protected .p12 and store it as IOS_SIGNING_P12_B64 and"
  echo "IOS_SIGNING_P12_PASSWORD on $SIMULATOR_REPO."
  exit 0
fi

WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
PASS=$(uuidgen)

say "Exporting"
security export -k "$KEYCHAIN" -t identities -f pkcs12 -P "$PASS" -o "$WORK/identities.p12"
[[ -s "$WORK/identities.p12" ]] || die "export produced nothing (was the keychain locked, or the prompt denied?)"
echo "  $(stat -f %z "$WORK/identities.p12") bytes"

say "Storing secrets on $SIMULATOR_REPO"
base64 -i "$WORK/identities.p12" | tr -d '\n' | gh secret set IOS_SIGNING_P12_B64 --repo "$SIMULATOR_REPO"
printf '%s' "$PASS" | gh secret set IOS_SIGNING_P12_PASSWORD --repo "$SIMULATOR_REPO"
echo "  IOS_SIGNING_P12_B64, IOS_SIGNING_P12_PASSWORD set"

say "Done"
cat <<MSG
Hosted runs now import these identities into a throwaway keychain before
Archive and mint nothing. Re-run this script after renewing a certificate.
  gh workflow run testflight-ios.yml --repo $SIMULATOR_REPO
MSG
