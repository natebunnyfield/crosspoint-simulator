#pragma once

// WHEN THE SYSTEM'S APPEARANCE MAY OVERWRITE THE OWNER'S CHOICE.
//
// Owner 2026-08-28: "when booted into system dark mode, be in dark mode."
//
// Two requirements pull against each other, and each has already been shipped
// as a bug in its own right:
//
//  * **The in-app Dark Mode toggle must stick.** Seeding `SETTINGS.darkMode`
//    from the system on every launch overwrote it, so the control did not
//    survive a relaunch. That was fixed by seeding only on the FIRST EVER
//    launch.
//  * **Launching while the phone is dark must come up dark.** The first-launch
//    rule cannot see a change made while the app was CLOSED: the running-app
//    poll initialises its "last system" from the system itself, so on the first
//    tick nothing has changed and the stored setting wins. Install in light,
//    switch the phone to dark, reopen: the app comes up light. That is the
//    report.
//
// Neither "always seed" nor "seed once" satisfies both, because both answer
// from the CURRENT system alone. The question they cannot answer is *did the
// system change since we last looked* — and that needs the previous answer
// remembered across launches, separately from the owner's setting.
//
// So: remember the system appearance we last acted on. On launch, if it differs
// from the system now, the phone changed while we were away and the app follows
// it. If it matches, nothing changed and the owner's setting stands, however it
// got there.
//
// Pure and storage-free: the caller supplies what it read and persists what it
// is told. Both failure modes are silent — a toggle that will not stick, and an
// app that ignores the phone — so the rule is a truth table rather than an
// if-ladder in the middle of applyTheme().
namespace appearanceseed {

// The remembered value when nothing has ever been stored.
inline constexpr int kNoneStored = -1;

// Should the system appearance be written into SETTINGS.darkMode right now?
//
// `firstEverLaunch` is the existing signal: no settings file, so there is no
// owner choice to protect and the system is the only sensible source.
// `storedSystemDark` is what we last acted on (kNoneStored if never).
// `currentSystemDark` is what the system says now.
constexpr bool shouldSeedFromSystem(bool firstEverLaunch, int storedSystemDark, int currentSystemDark) {
  if (firstEverLaunch) return true;
  // Never recorded — an install that predates this rule. Do NOT seed: the owner
  // may have set the toggle deliberately, and overwriting it on the upgrade
  // launch is precisely the bug the first-launch rule was introduced to fix.
  // The value is recorded on this launch, so the NEXT change is caught.
  if (storedSystemDark == kNoneStored) return false;
  return storedSystemDark != currentSystemDark;
}

// The system appearance is recorded on EVERY launch, whether or not it seeded.
// Recording only when seeding would leave the "never recorded" case above stuck
// forever, and a system change after a decline would then be invisible too.
constexpr int valueToRemember(int currentSystemDark) { return currentSystemDark; }

}  // namespace appearanceseed
