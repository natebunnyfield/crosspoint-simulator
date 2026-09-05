#!/usr/bin/env bash
#
# One-shot, run ON THE MAC: put the licensed font sources where the hosted
# TestFlight iOS workflow can read them, without a single click in a browser.
#
#   ios/setup-local-fonts-repo.sh            create/update repo, key, secret
#   ios/setup-local-fonts-repo.sh --check    report what exists, change nothing
#
# What it does, in order:
#   1. Creates the PRIVATE repo $FONTS_REPO if it does not exist (gh).
#   2. Mirrors $FIRMWARE_DIR/lib/EpdFont/local_fonts/*.{ttf,otf} into it, flat,
#      plus the generated commercial editor-face headers (builtinFonts/
#      pragmatapro_*.h and nitti*.h, gitignored in the firmware) under
#      builtinFonts/, with a README that says what the folder is; commits and
#      pushes main.
#   3. Generates an ed25519 deploy key, adds the public half READ-ONLY to
#      $FONTS_REPO, stores the private half as the $SECRET_NAME secret on
#      $SIMULATOR_REPO AND on $FIRMWARE_REPO (its Compile Release workflow
#      reads the same mirror to pass the B-029 editor-face gate), and deletes
#      both halves from disk. A deploy key rather than a PAT because gh can do
#      every step of it; a fine-grained PAT is a web form. Re-running rotates
#      the key (the old one is removed by title).
#
# Why a repo at all: Edgar (Frere-Jones Type, licensed) is in the firmware's
# installed_families, ios/CMakeLists.txt refuses a bundle missing any installed
# family, and a hosted runner has no copy of the gitignored local_fonts/ --
# TestFlight iOS runs 15 and 16 (2026-09-05) died on exactly that. The repo is
# private and stays private: these are licensed files, mirrored for the
# licensee's own builds, never redistributed.
#
# Needs: gh (authenticated, `gh auth status`), ssh-keygen, git. Nothing else.

set -euo pipefail

FONTS_REPO="${CROSSPOINT_LOCAL_FONTS_REPO:-natebunnyfield/crosspoint-local-fonts}"
SIMULATOR_REPO="${CROSSPOINT_SIMULATOR_REPO:-natebunnyfield/crosspoint-simulator}"
FIRMWARE_REPO="${CROSSPOINT_FIRMWARE_REPO:-natebunnyfield/crosspoint-reader}"
FIRMWARE_DIR="${CROSSPOINT_FIRMWARE_DIR:-$HOME/src/crosspoint-reader}"
SECRET_NAME="LOCAL_FONTS_SSH_KEY"
KEY_TITLE="crosspoint-simulator TestFlight iOS (read-only)"
SRC="$FIRMWARE_DIR/lib/EpdFont/local_fonts"
HDR="$FIRMWARE_DIR/lib/EpdFont/builtinFonts"

CHECK=0
[[ "${1:-}" == "--check" ]] && CHECK=1

say() { printf '\n=== %s ===\n' "$1"; }
die() { printf '\nERROR: %s\n' "$1" >&2; exit 1; }

command -v gh >/dev/null || die "gh not found. brew install gh && gh auth login"
gh auth status >/dev/null 2>&1 || die "gh is not logged in: gh auth login"
command -v ssh-keygen >/dev/null || die "ssh-keygen not found"
[[ -d "$SRC" ]] || die "no $SRC -- this must run on the machine that holds the licensed sources"

say "Sources in $SRC"
shopt -s nullglob
SOURCES=("$SRC"/*.ttf "$SRC"/*.otf)
shopt -u nullglob
[[ ${#SOURCES[@]} -gt 0 ]] || die "$SRC holds no .ttf/.otf files"
for f in "${SOURCES[@]}"; do printf '  %s\n' "$(basename "$f")"; done
for need in Edgar-Regular.ttf Edgar-Bold.ttf Edgar-Italic.ttf Edgar-BoldItalic.ttf; do
  [[ -f "$SRC/$need" ]] || echo "  WARNING: $need is missing; the iOS seed-font gate will still refuse Edgar"
done

say "Generated editor-face headers in $HDR"
shopt -s nullglob
HEADERS=("$HDR"/pragmatapro_*.h "$HDR"/nitti*.h)
shopt -u nullglob
if [[ ${#HEADERS[@]} -eq 0 ]]; then
  echo "  none. The firmware's Compile Release on CI will still fail B-029 until they exist:"
  echo "    (cd $FIRMWARE_DIR/lib/EpdFont/scripts && ./convert-builtin-fonts.sh)   then re-run this script"
else
  echo "  ${#HEADERS[@]} headers (pragmatapro_*.h, nitti*.h)"
fi

say "Repository $FONTS_REPO"
if gh repo view "$FONTS_REPO" --json visibility --jq .visibility >/tmp/.fonts_repo_vis 2>/dev/null; then
  VIS=$(cat /tmp/.fonts_repo_vis)
  echo "  exists, visibility: $VIS"
  [[ "$VIS" == "PRIVATE" || "$VIS" == "private" ]] || die "$FONTS_REPO is $VIS. Licensed files must not sit in a public repo; make it private first: gh repo edit $FONTS_REPO --visibility private"
else
  echo "  does not exist"
  if [[ $CHECK -eq 0 ]]; then
    gh repo create "$FONTS_REPO" --private \
      --description "Licensed font sources for the CrossPoint firmware's gitignored lib/EpdFont/local_fonts/. Private; read by crosspoint-simulator's TestFlight iOS workflow through a read-only deploy key." \
      >/dev/null
    echo "  created (private)"
  fi
fi
rm -f /tmp/.fonts_repo_vis

say "Deploy key + secret on $SIMULATOR_REPO and $FIRMWARE_REPO"
for r in "$SIMULATOR_REPO" "$FIRMWARE_REPO"; do
  if gh secret list --repo "$r" 2>/dev/null | grep -q "^$SECRET_NAME"; then
    echo "  $r: secret $SECRET_NAME present (will be rotated)"
  else
    echo "  $r: secret $SECRET_NAME absent"
  fi
done

if [[ $CHECK -eq 1 ]]; then
  say "--check: nothing changed"
  exit 0
fi

say "Mirroring sources"
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
gh repo clone "$FONTS_REPO" "$WORK/repo" -- --quiet 2>/dev/null || {
  # A repo created seconds ago with no commits clones as empty; that is fine.
  git init -q "$WORK/repo"
  git -C "$WORK/repo" remote add origin "https://github.com/$FONTS_REPO.git"
}
cd "$WORK/repo"
git checkout -q -B main
# Mirror, do not merge: a file removed from local_fonts/ is removed here too,
# so the repo never carries a face the firmware no longer references.
find . -maxdepth 1 -type f \( -name '*.ttf' -o -name '*.otf' \) -delete
cp "${SOURCES[@]}" .
rm -rf builtinFonts
if [[ ${#HEADERS[@]} -gt 0 ]]; then
  mkdir -p builtinFonts
  cp "${HEADERS[@]}" builtinFonts/
fi
cat > README.md <<'README'
# crosspoint-local-fonts

A private mirror of the CrossPoint firmware's gitignored
`lib/EpdFont/local_fonts/` folder: the licensed font sources (Edgar by
Frere-Jones Type, and whatever else that folder holds on the licensee's Mac).

**Private, and it stays private.** These files are licensed to one person for
their own builds. Nothing here is redistributed; the simulator's TestFlight iOS
workflow checks this repo out into `firmware/lib/EpdFont/local_fonts/` on the
runner, builds the seed `.cpfont` tiers from it, and the runner is destroyed.

`builtinFonts/` holds the glyph tables `convert-builtin-fonts.sh` generates
from the commercial editor faces (PragmataPro, NittiTypewriter). The firmware
gitignores them for the same reason; its Compile Release workflow copies them
into `lib/EpdFont/builtinFonts/` so the B-029 gate sees a complete release.

Maintained by `crosspoint-simulator/ios/setup-local-fonts-repo.sh`, which
mirrors the folder flat (a file removed there is removed here), rotates the
read-only deploy key both workflows use, and stores it as the
`LOCAL_FONTS_SSH_KEY` secret on the simulator and firmware repos. Do not edit
by hand; run the script again.
README
git add -A
if git diff --cached --quiet; then
  echo "  repo already matches local_fonts/ ($(ls *.ttf *.otf 2>/dev/null | wc -l | tr -d ' ') files)"
else
  git -c user.name="$(git config --global user.name || echo local-fonts)" \
      -c user.email="$(git config --global user.email || echo local-fonts@localhost)" \
      commit -q -m "Mirror lib/EpdFont/local_fonts from $(hostname -s) on $(date -u +%Y-%m-%dT%H:%MZ)"
  git push -q -u origin main
  echo "  pushed $(ls *.ttf *.otf 2>/dev/null | wc -l | tr -d ' ') files"
fi
cd - >/dev/null

say "Rotating the deploy key"
ssh-keygen -q -t ed25519 -N '' -C "$KEY_TITLE" -f "$WORK/deploy_key"
# Remove any earlier key of the same title so rotation does not accumulate.
gh repo deploy-key list --repo "$FONTS_REPO" --json id,title --jq ".[] | select(.title==\"$KEY_TITLE\") | .id" 2>/dev/null \
  | while read -r id; do [[ -n "$id" ]] && gh repo deploy-key delete "$id" --repo "$FONTS_REPO" && echo "  removed old key $id"; done
gh repo deploy-key add "$WORK/deploy_key.pub" --repo "$FONTS_REPO" --title "$KEY_TITLE" >/dev/null
echo "  public half added to $FONTS_REPO (read-only)"
for r in "$SIMULATOR_REPO" "$FIRMWARE_REPO"; do
  gh secret set "$SECRET_NAME" --repo "$r" < "$WORK/deploy_key"
  echo "  private half stored as $SECRET_NAME on $r"
done
rm -f "$WORK/deploy_key" "$WORK/deploy_key.pub"

say "Done"
cat <<MSG
Dispatch a hosted build (the default seed list is every installed family):
  gh workflow run testflight-ios.yml --repo $SIMULATOR_REPO
The firmware's Compile Release (workflow_dispatch) now carries the editor
faces too:
  gh workflow run release.yml --repo $FIRMWARE_REPO
Re-run this script after adding or removing a file in local_fonts/ or after
regenerating the editor-face headers; it re-mirrors and rotates the key.
MSG
